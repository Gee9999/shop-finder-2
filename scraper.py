
import os, re, asyncio, aiohttp, requests, random
from duckduckgo_search import DDGS

BING_KEY = os.getenv("BING_API_KEY")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NEGATIVE = {"directory","yellowpages","listing","mapquest"}

def ddg_random_search(query, max_results):
    page = random.randint(1, 20)
    with DDGS() as ddgs:
        raw = ddgs.text(query, max_results=max_results, page=page)
        urls = [r["href"] for r in raw if r.get("href","").startswith("http")]
    return [u for u in urls if not any(n in u for n in NEGATIVE)]

def bing_search(query, max_results, api_key):
    if not api_key:
        return []
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params  = {"q": query, "count": max_results}
    try:
        r = requests.get("https://api.bing.microsoft.com/v7.0/search",
                         headers=headers, params=params, timeout=5)
        data = r.json()
        urls = [it["url"] for it in data.get("webPages", {}).get("value", [])]
        return [u for u in urls if not any(n in u for n in NEGATIVE)]
    except Exception:
        return []

async def fetch_html(session, url, max_bytes=200_000):
    try:
        async with session.get(url, timeout=6) as resp:
            return (await resp.content.read(max_bytes)).decode("utf-8", errors="ignore")
    except Exception:
        return ""

async def hunter(domain, key):
    try:
        r = requests.get("https://api.hunter.io/v2/domain-search",
                         params={"domain": domain, "api_key": key}, timeout=5)
        if r.status_code == 200:
            emails = [e["value"] for e in r.json().get("data", {}).get("emails", [])]
            return ", ".join(emails)
    except Exception:
        pass
    return ""

async def scrape_site(session, url, hunter_key):
    html   = await fetch_html(session, url)
    emails = EMAIL_RE.findall(html)
    if not emails and hunter_key:
        domain = url.split("/")[2]
        emails = await asyncio.get_event_loop().run_in_executor(None, hunter, domain, hunter_key)
        emails = emails.split(", ") if isinstance(emails, str) else emails
    return {"website": url, "emails_found": ", ".join(set(emails))}

async def search_and_scrape(keyword, location, max_sites, hunter_key, engine="ddg", bing_key=""):
    query = f"{keyword} {location}"
    urls  = ddg_random_search(query, max_sites) if engine=="ddg" else bing_search(query, max_sites, bing_key)
    async with aiohttp.ClientSession(headers={"User-Agent":"Mozilla/5.0"}) as session:
        tasks = [scrape_site(session, u, hunter_key) for u in urls]
        leads = await asyncio.gather(*tasks)
    for l in leads:
        l["keyword"]  = keyword
        l["location"] = location
        l["engine"]   = engine
    return leads
