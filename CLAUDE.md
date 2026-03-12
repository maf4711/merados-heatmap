# merados-heatmap

Interactive stock market heatmap and screener (Finviz-style), built with Streamlit.

## Tech Stack

- Python 3
- Streamlit (web UI)
- Plotly (interactive heatmaps and charts)
- yfinance, financedatabase, pandas-ta (market data)
- Multi-source: FMP, Finnhub, Alpha Vantage APIs
- SQLite cache for performance
- aiohttp for async API calls

## Key Files

- `app.py` -- main Streamlit application
- `data_providers.py` -- multi-source data fetcher with quality scoring
- `requirements.txt` -- Python dependencies

## Features

- Finviz-style interactive heatmap
- Multi-source data with quality scores
- News and sentiment analysis
- Stock screener
- DCF fair value calculation
- SQLite-backed caching layer

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Config

Set API keys as environment variables or in a `.env` file:
- `FMP_API_KEY`
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`

yfinance works without an API key as fallback.
