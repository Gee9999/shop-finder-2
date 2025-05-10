import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from io import BytesIO
from datetime import datetime
import re
import requests

st.set_page_config(page_title="Shop Finder | Powered by Proto Trading", layout="centered")
st.markdown("<h1 style='color:#001f3f;'>Shop Finder</h1><h4>Powered by Proto Trading</h4>", unsafe_allow_html=True)
st.markdown("---")

blacklist_patterns = [
    "sentry", "bootstrap", "react@", "example.com", "your@email.com",
    "@2x.", "@3x.", ".jpg", ".jpeg", ".png", ".webp", ".svg", "favicon"
]

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
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=5)
            return r.text if r.ok else ""
        except Exception:
            return ""

    combined_html = fetch(url) + fetch(url.rstrip("/") + "/contact")
    raw_emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", combined_html))
    filtered = [e for e in raw_emails if is_valid_email(e)]
    best_email = prioritize_email(filtered)
    return best_email

def extract_snippet_emails(snippet):
    found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", snippet)
    return [e for e in found if is_valid_email(e)]

# --- UI Inputs ---
categories_input = st.text_area("📦 Product Categories (one per line)", height=100, help="e.g. beads, handbags, electronics")
country = st.selectbox("🌍 Country", sorted([
    "South Africa", "Kenya", "Nigeria", "Ghana", "Namibia", "Botswana", "Zimbabwe", "Uganda", "Tanzania",
    "Zambia", "Mozambique", "Egypt", "Ethiopia", "Morocco", "Rwanda"
]), help="Select a country in Africa")

city = st.text_input("🏙️ City (optional)", help="Optional: Cape Town, Nairobi, etc.")
extra_keywords = st.text_input("➕ Extra Keywords (optional)", help="Add more like 'importer, manufacturer'")
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

        with st.spinner("Searching and auto-prioritizing email sources..."):
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
                                    snippet_emails = extract_snippet_emails(snippet)
                                    snippet_email_best = prioritize_email(snippet_emails)
                                    extracted_email = extract_best_email(url)

                                    # Use main method first, fallback to snippet email
                                    final_email = extracted_email or snippet_email_best
                                    is_valid = "✅" if final_email else "❌"

                                    all_data.append({
                                        "name": r.get("title"),
                                        "url": url,
                                        "snippet": snippet,
                                        "email": final_email,
                                        "is_valid_email": is_valid,
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
            st.info("No results found. Try other keywords or categories.")
