
# Leads Finder

Streamlit app that builds a cumulative Excel database (`leads_database.xlsx`) of websites and email addresses for any keyword & location search.

## Engines
* **DuckDuckGo (randomized start page)** – no key needed.
* **Bing Web Search API** – add `BING_API_KEY` secret (1 000 free queries/month).

Optional Hunter.io enrichment with `HUNTER_API_KEY`.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
