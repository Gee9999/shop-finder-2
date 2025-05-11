
import streamlit as st, pandas as pd, io, asyncio
from scraper import search_and_scrape

st.set_page_config(page_title="Leads Finder – Clean Edition", layout="wide")
st.title("📇 Leads Finder – Clean Edition")

st.markdown("""Generate lead lists by discovering business websites and e‑mail addresses for any keyword & location.

* Default engine: DuckDuckGo (unlimited, no key).  
* Optional engine: Bing Web Search API (1 000 queries/month free).  
* Hunter.io enrichment can fill missing emails.
""")

col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("🔑 Business keyword", placeholder="e.g. bakery")
with col2:
    locations_input = st.text_input("🌍 Locations (comma‑separated towns/countries)",
                                    value="Cape Town, South Africa")

engine = st.selectbox("Search engine", ["DuckDuckGo (free)", "Bing API"])
bing_key = ""
if engine.startswith("Bing"):
    bing_key = st.text_input("BING_API_KEY", type="password")

max_sites  = st.slider("Results per location", 1, 10, 3)
hunter_key = st.text_input("Hunter.io API key (optional)", type="password")

if st.button("🔍 Find leads"):
    if not keyword:
        st.error("Please enter a keyword")
        st.stop()

    locations = [l.strip() for l in locations_input.split(",") if l.strip()]
    progress, status = st.progress(0), st.empty()
    all_rows = []

    async def runner():
        for i, loc in enumerate(locations):
            status.info(f"Searching {loc} …")
            rows = await search_and_scrape(keyword, loc, max_sites, hunter_key,
                                           engine="bing" if engine.startswith("Bing") else "ddg",
                                           bing_key=bing_key)
            all_rows.extend(rows)
            progress.progress((i+1)/len(locations))

    asyncio.new_event_loop().run_until_complete(runner())
    df = pd.DataFrame(all_rows)
    st.success(f"Found {len(df)} leads")
    st.dataframe(df, use_container_width=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Leads")
    st.download_button("⬇️ Download Excel", buf.getvalue(), file_name="leads.xlsx")
