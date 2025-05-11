
# Leads Finder

Keeps a cumulative `leads_database.xlsx` file on the server and merges new
searches into it each run.

## Engines
* DuckDuckGo (randomized start page) – no key.
* Bing Web Search API – set `BING_API_KEY`.

## Optional
* `HUNTER_API_KEY` for email enrichment.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
