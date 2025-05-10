import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from io import BytesIO
from datetime import datetime
import re
import requests

st.set_page_config(page_title="Shop Finder | Powered by Proto Trading", layout="centered")

# Header
st.markdown("<h1 style='color:#001f3f;'>Shop Finder</h1><h4>Powered by Proto Trading</h4>", unsafe_allow_html=True)
st.markdown("---")

# Blacklist patterns
blacklist_patterns = [
    "sentry.wixpress.com",
    "sentry.io",
    "wixpress.com",
    "lodash@", "react@", "polyfill@", "core-js",
    "@2x.", "@3x.", ".png", ".jpg", ".jpeg",
    "your@email.com", "example.com", "liputra.com"
]

def is_valid_email(email):
    for pattern in blacklist_patterns:
        if pattern.lower() in email.lower():
            return False
    return True

def extract_first_valid_email(url):
    def fetch(url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=5)
            if response.ok:
                return response.text
        except Exception:
            return ""
        return ""

    email_set = set()
    main_html = fetch(url)
    contact_html = fetch(url.rstrip('/') + "/contact")

    for html in [main_html, contact_html]:
        found = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)
        email_set.update([e for e in found if is_valid_email(e)])

    email_list = list(email_set)
    if email_list:
        return email_list[0], "✅"
    else:
        return "", "❌"

# --- Inputs ---
categories_input = st.text_area("📦 Product Categories (one per line)", height=100, help="e.g. beads, handbags, electronics")
country = st.selectbox("🌍 Country", sorted([
    "South Africa", "Kenya", "Nigeria", "Ghana", "Namibia", "Botswana", "Zimbabwe", "Uganda", "Tanzania", "Zambia", "Mozambique", "Egypt", "Ethiopia", "Morocco", "Rwanda"
]), help="Select a country in Africa")

city = st.text_input("🏙️ City (optional)", help="Optional: Cape Town, Nairobi, etc.")
extra_keywords = st.text_input("➕ Extra Keywords (optional)", help="Add more like 'importer, manufacturer'")
num_results = st.slider("🔁 Max results per search", 1, 20, 10)

keyword_variants = ["supplier", "wholesaler", "distributor", "store", "shop"]

if extra_keywords:
    keyword_variants += [kw.strip() for kw in extra_keywords.split(",") if kw.strip()]

headers = {
    "User-Agent": "Mozilla/5.0"
}

if st.button("🔍 Find Leads"):
    if not categories_input:
        st.warning("Please enter at least one product category.")
    else:
        categories = [line.strip() for line in categories_input.splitlines() if line.strip()]
        all_data = []
        seen_urls = set()

        location = f"{city}, {country}" if city else country

        with st.spinner("Searching and storing valid emails..."):
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
                                    email, is_valid = extract_first_valid_email(url)
                                    all_data.append({
                                        "name": r.get("title"),
                                        "url": url,
                                        "snippet": r.get("body"),
                                        "email": email,
                                        "is_valid_email": is_valid,
                                        "category": cat,
                                        "location": location,
                                        "query": query
                                    })
                        except Exception as e:
                            st.error(f"❌ Error on query: {query}\n{str(e)}")

        if all_data:
            df = pd.DataFrame(all_data)
            st.success(f"✅ Found {len(df)} unique leads.")
            st.dataframe(df)

            # Excel download
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            filename = f"shop_finder_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            st.download_button("📥 Download Excel", buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("No results found. Try other keywords or categories.")
