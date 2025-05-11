
import os, re, asyncio, aiohttp, requests
from googleapiclient.discovery import build

API_KEY = os.getenv("GOOGLE_API_KEY")
CX_ID   = os.getenv("GOOGLE_CX")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NEGATIVE = {"directory", "yellowpages", "listing", "mapquest"}

def google_search(query: str, max_results: int):
    if not API_KEY or not CX_ID:
        return []
    srv = build("customsearch", "v1", developerKey=API_KEY, cache_discovery=False)
    try:
        res = srv.cse().list(q=query, cx=CX_ID, num=max_results).execute()
        urls = []
        for item in res.get("items", []):
            url = item["link"]
            dom = url.split("/")[2]
            if not any(n in dom for n in NEGATIVE):
                urls.append(url)
        return urls
    except Exception:
        return []

async def fetch_html(session, url, max_bytes=200_000):
    try:
        async with session.get(url, timeout=6) as r:
            return (await r.content.read(max_bytes)).decode("utf-8", errors="ignore")
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

async def search_and_scrape(keyword: str, location: str, max_sites: int, hunter_key: str):
    urls = google_search(f"{keyword} {location}", max_sites)
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        tasks = [scrape_site(session, u, hunter_key) for u in urls]
        leads = await asyncio.gather(*tasks)
    for lead in leads:
        lead["keyword"]  = keyword
        lead["location"] = location
    return leads
