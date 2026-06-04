# AI Client Reporting Engine

Offline-first client reporting system for wealth management teams. It transforms ticker and allocation inputs into client-ready portfolio commentary with metrics, tone control, and exportable Markdown/PDF output.

## Features

- Portfolio analytics from `yfinance` price history
- Daily portfolio snapshot upload for fund-heavy portfolios
- ISIN and SEDOL support as holding identifiers
- Public web/RSS research ingestion with numbered citations
- Return, volatility, drawdown, Sharpe ratio, beta, concentration, and driver attribution
- Uploaded market value, book cost, and gain/loss analytics
- Research-aware commentary for macro, monetary policy, industry, and fund sources
- Dynamic report tone for retail and institutional clients
- Local Ollama LLM integration with deterministic metric-aware fallback
- Streamlit UI for client type selection, preview, and downloads
- Markdown export and optional PDF export

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional local LLM:

```bash
ollama pull llama3.1
ollama serve
```

## Run React-Style Web App

```bash
python3 web_app/server.py
```

Open [http://localhost:8501](http://localhost:8501).

The legacy Streamlit entrypoint remains in `app/streamlit_app.py`, but the main experience is now the local web workspace in `web_app/`.

## Example Input

For fund-heavy portfolios, upload an `.xlsx`, `.xls`, or `.csv` file. Required column:

```text
market_value
```

Recommended columns:

```text
name, isin, sedol, ticker, asset_type, book_cost, gain_loss, gain_loss_pct, currency
```

Supported `asset_type` examples:

```text
Fund, ETF, Property Fund, MMF, Direct Equity
```

For direct equity or ETF-only portfolios, use comma-separated tickers and matching weights:

```text
AAPL, MSFT, VTI, BND
35, 25, 25, 15
```

## Project Structure

```text
client_reporting/
├── data/          # market data access
├── analytics/     # portfolio metrics and attribution
├── formatting/    # report formatting and validation
├── llm/           # Ollama client and prompts
├── app/           # report builder orchestration
└── export/        # markdown and PDF exporters
```

## Notes

- The app uses Yahoo Finance through `yfinance`; it does not use paid market data or paid LLM APIs.
- ISIN and SEDOL are used for identification, not paid fund data lookup. Fund-heavy reporting is driven by the uploaded daily valuation and gain/loss snapshot.
- Research sources must be public URLs or RSS/Atom feeds. The app cites fetched items in the report; it does not use paid research APIs.
- PDF export is optional and uses `markdown` plus `weasyprint` when installed. If those packages are unavailable, Markdown export still works.
