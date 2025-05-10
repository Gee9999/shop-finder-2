import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from io import BytesIO
from datetime import datetime
import re
import requests
from urllib.parse import urlparse

st.set_page_config(page_title="Shop Finder | Powered by Proto Trading", layout="centered")
st.markdown("<h1 style='color:#001f3f;'>Shop Finder</h1><h4>Powered by Proto Trading</h4>", unsafe_allow_html=True)
st.markdown("---")

blacklist_patterns = [
    "sentry", "bootstrap", "react@", "example.com", "your@email.com",
    "@2x.", "@3x.", ".jpg", ".jpeg", ".png", ".webp", ".svg", "favicon"
]

HUNTER_API_KEY = "9fe1766be5de1514e0e7b9e3d3eb1a338a47c4e0"

def is_valid_email(email):
    return all(p not in email.lower() for p in blacklist_patterns)

def prioritize_email(emails):
    priority = ["info@", "sales@", "support@", "admin@", "contact@", "hello@", "enquiries@"]
    business_first = sorted([e for e in emails if not any(free in e for free in ["gmail.com", "yahoo.com", "hotmail.com"])])
    all_sorted = sorted(business_first or emails, key=lambda x: (not any(p in x for p in priority), len(x)))
    return all_sorted[0] if all_sorted else ""

def extract_best_email(url):
    def fetch(url):
        try:
            headers = { "User-Agent": "Mozilla/5.0" }
            r = requests.get(url, headers=headers, timeout=5)
            return r.text if r.ok else ""
        except Exception:
            return ""

    html = fetch(url) + fetch(url.rstrip("/") + "/contact")
    emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html))
    filtered = [e for e in emails if is_valid_email(e)]
    return prioritize_email(filtered)

def extract_snippet_emails(snippet):
    found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", snippet)
    return [e for e in found if is_valid_email(e)]

def extract_domain(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")
    except:
        return ""

def fetch_hunter_email(domain):
    if not domain:
        return ""
    try:
        r = requests.get(
            f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
        )
        if r.ok:
            data = r.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                return emails[0].get("value")
    except:
        return ""
    return ""

# --- UI Inputs ---
categories_input = st.text_area("📦 Product Categories (one per line)", height=100)
country = st.selectbox("🌍 Country", sorted([
    "South Africa", "Kenya", "Nigeria", "Ghana", "Namibia", "Botswana", "Zimbabwe", "Uganda", "Tanzania",
    "Zambia", "Mozambique", "Egypt", "Ethiopia", "Morocco", "Rwanda"
]))
city = st.text_input("🏙️ City (optional)")
extra_keywords = st.text_input("➕ Extra Keywords (optional)")
num_results = st.slider("🔁 Max results per search", 1, 20, 10)

keyword_variants = ["supplier", "wholesaler", "distributor", "store", "shop"]
if extra_keywords:
    keyword_variants += [kw.strip() for kw in extra_keywords.split(",") if kw.strip()]

headers = {"User-Agent": "Mozilla/5.0"}

if st.button("🔍 Find Leads"):
    if not categories_input:
        st.warning("Please enter at least one product category.")
    else:
        categories = [line.strip() for line in categories_input.splitlines() if line.strip()]
        all_data = []
        seen_urls = set()
        location = f"{city}, {country}" if city else country

        with st.spinner("Running search with Hunter.io fallback..."):
            with DDGS(headers=headers) as ddgs:
                for cat in categories:
                    for variant in keyword_variants:
                        query = f"{cat} {variant} in {location}"
                        try:
                            results = ddgs.text(query, region='wt-wt', safesearch='Off', max_results=num_results)
                            for r in results:
                                url = r.get("href")
                                if url and url not in seen_urls:
                                    seen_urls.add(url)
                                    snippet = r.get("body") or ""
                                    domain = extract_domain(url)

                                    # Try main HTML/email extraction
                                    main_email = extract_best_email(url)
                                    if not main_email:
                                        # Fallback to snippet
                                        snippet_emails = extract_snippet_emails(snippet)
                                        main_email = prioritize_email(snippet_emails)
                                    if not main_email:
                                        # Fallback to Hunter.io
                                        main_email = fetch_hunter_email(domain)

                                    is_valid = "✅" if main_email else "❌"

                                    all_data.append({
                                        "name": r.get("title"),
                                        "url": url,
                                        "snippet": snippet,
                                        "email": main_email,
                                        "is_valid_email": is_valid,
                                        "source": domain,
                                        "category": cat,
                                        "location": location,
                                        "query": query
                                    })
                        except Exception as e:
                            st.error(f"❌ Error on query: {query}\n{str(e)}")

        if all_data:
            df = pd.DataFrame(all_data)
            st.success(f"✅ Found {len(df)} leads.")
            st.dataframe(df)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            filename = f"shop_finder_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            st.download_button("📥 Download Excel", buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("No results found. Try a broader category or fewer filters.")
