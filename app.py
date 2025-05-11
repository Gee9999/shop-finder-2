
import streamlit as st, pandas as pd, io, asyncio, os
from scraper import search_and_scrape

st.set_page_config(page_title="Leads Finder", layout="wide")
st.title("📇 Leads Finder")

st.markdown("Build and grow your own lead database. Each search adds new leads into a cumulative Excel file kept on the server.")

# --- inputs ---
col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("Business keyword", placeholder="e.g. bakery")
with col2:
    locations_input = st.text_input("Locations (comma‑separated)", value="Cape Town, South Africa")

engine = st.selectbox("Search engine", ["DuckDuckGo (randomized)", "Bing API"])
bing_key = st.text_input("BING_API_KEY", type="password") if engine.startswith("Bing") else ""

max_sites   = st.slider("Results per location", 1, 10, 3)
hunter_key  = st.text_input("Hunter.io API key (optional)", type="password")

DB_PATH = "leads_database.xlsx"

if st.button("🔍 Run & save leads"):
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
    new_df = pd.DataFrame(all_rows)

    if os.path.exists(DB_PATH):
        old = pd.read_excel(DB_PATH)
        combined = pd.concat([old, new_df], ignore_index=True).drop_duplicates(subset=["website","keyword","location"])
    else:
        combined = new_df

    combined.to_excel(DB_PATH, index=False)
    st.success(f"Database now has {len(combined)} leads.")
    st.dataframe(combined.tail(200), use_container_width=True)

    with open(DB_PATH, "rb") as f:
        st.download_button("⬇️ Download full database", f, file_name="leads_database.xlsx")
elif os.path.exists("leads_database.xlsx"):
    st.info("Existing database:")
    db = pd.read_excel("leads_database.xlsx")
    st.write(f"Rows: {len(db)}")
    st.dataframe(db.tail(200), use_container_width=True)
    with open("leads_database.xlsx", "rb") as f:
        st.download_button("⬇️ Download full database", f, file_name="leads_database.xlsx")
