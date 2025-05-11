
# Leads Finder – Clean Edition

Streamlit app to discover business websites and e‑mail addresses by keyword and location.

## Supported search engines
* **DuckDuckGo** – unlimited, no key required.
* **Bing Web Search API** – set `BING_API_KEY` in secrets for 1 000 free queries/month.

## Optional enrichment
* `HUNTER_API_KEY` – Hunter.io Domain Search for additional emails.

## Secrets example
```
BING_API_KEY   = "your-bing-key"
HUNTER_API_KEY = "optional-hunter-key"
```

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
