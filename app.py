
import streamlit as st, pandas as pd, io, asyncio, os
from scraper import search_and_scrape

st.set_page_config(page_title="Shop Finder Clean (Duck/Bing)", layout="wide")
st.title("🛍️ Shop Finder – DuckDuckGo / Bing Edition")

st.markdown("""Find shop / business websites and emails by keyword and location.

* **DuckDuckGo**: unlimited, no key.  
* **Bing Web Search API**: 1 000 free queries/month (Azure key required).  
* Optional Hunter.io enrichment fills missing e‑mails.
""")

col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("🔑 Shop keyword", placeholder="e.g. bakery")
with col2:
    locations_input = st.text_input("🌍 Locations (comma‑separated)", value="Cape Town, South Africa")

engine = st.selectbox("Search engine", ["DuckDuckGo (free)", "Bing (needs API key)"])
bing_key = ""
if engine.startswith("Bing"):
    bing_key = st.text_input("BING_API_KEY", type="password")

max_sites = st.slider("Results per location", 1, 10, 3)
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")

if st.button("🔍 Find shops"):
    if not keyword:
        st.error("Please enter a keyword")
        st.stop()

    locations = [l.strip() for l in locations_input.split(",") if l.strip()]
    progress, status = st.progress(0), st.empty()
    all_rows=[]

    async def runner():
        for i, loc in enumerate(locations):
            status.info(f"Searching {loc} …")
            rows = await search_and_scrape(keyword, loc, max_sites, hunter_key,
                                           engine="bing" if engine.startswith("Bing") else "ddg",
                                           bing_key=bing_key)
            all_rows.extend(rows)
            progress.progress((i+1)/len(locations))

    asyncio.new_event_loop().run_until_complete(runner())
    df=pd.DataFrame(all_rows)
    st.success(f"Found {len(df)} leads")
    st.dataframe(df, use_container_width=True)
    buf=io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w,index=False,sheet_name="Leads")
    st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="shop_leads.xlsx")
