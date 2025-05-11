
import streamlit as st, pandas as pd, io, asyncio
from scraper import search_and_scrape

st.set_page_config(page_title="Shop Finder Clean", layout="wide")
st.title("🛍️ Shop Finder – Clean Edition (Google API)")

st.markdown("""Find shop / business websites and e‑mail addresses by keyword and location.

* Uses Google Programmable Search (first 100 queries/day free).  
* Skips obvious directory domains.  
* Scrapes homepage for e‑mails; optional Hunter.io enrichment fills gaps.
""")

col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("🔑 Shop keyword", placeholder="e.g. bakery")
with col2:
    locations_input = st.text_input("🌍 Locations (comma-separated towns/countries)",
                                    value="Cape Town, South Africa")

max_sites  = st.slider("Google results per location", 1, 10, 3)
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")

if st.button("🔍 Find shops"):
    if not keyword:
        st.error("Please enter a keyword")
        st.stop()

    locations = [l.strip() for l in locations_input.split(",") if l.strip()]
    progress  = st.progress(0)
    status    = st.empty()
    leads_all = []

    async def runner():
        for i, loc in enumerate(locations):
            status.info(f"Searching {loc} …")
            leads = await search_and_scrape(keyword, loc, max_sites, hunter_key)
            leads_all.extend(leads)
            progress.progress((i + 1) / len(locations))

    asyncio.new_event_loop().run_until_complete(runner())
    df = pd.DataFrame(leads_all)
    st.success(f"Found {len(df)} leads")
    st.dataframe(df, use_container_width=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Leads")
    st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="shop_leads.xlsx")
