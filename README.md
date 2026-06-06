# AI Client Reporting Engine

Offline-first AI-assisted client reporting engine for wealth management teams. It combines portfolio analytics, fund-heavy holdings upload, public research ingestion, deterministic report generation, optional local Ollama support, quality checks, and exportable client-ready Markdown/PDF reports.

## Live Website

Live Website: TODO

This repository includes a static React/Vite portfolio website under `site/`. It is designed for a public GitHub About/Website URL and can be deployed to Vercel without running the Python backend.

The public website is a demo only. It does not perform live portfolio analysis and should not receive client data.

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
- Local Python-backed web app for client type selection, portfolio editing, report preview, and downloads
- Static React/Vite public website for portfolio presentation and live demo deployment
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

## Run Public React/Vite Website

```bash
cd site
npm install
npm run dev
```

Build for deployment:

```bash
cd site
npm run build
```

The React site uses static JSON files under `site/public/data/`. It does not call `/api/analyze` or require the Python server.

## Vercel Deployment

Use these settings:

```text
Framework preset: Vite
Root directory: site
Build command: npm run build
Output directory: dist
```

After deployment, paste the Vercel URL into the GitHub repository About/Website field.

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

web_app/           # local Python-backed app and API
site/              # static React/Vite public website
docs/              # architecture and deployment notes
```

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Live Demo Notes](docs/live_demo.md)

## Notes

- The app uses Yahoo Finance through `yfinance`; it does not use paid market data or paid LLM APIs.
- ISIN and SEDOL are used for identification, not paid fund data lookup. Fund-heavy reporting is driven by the uploaded daily valuation and gain/loss snapshot.
- Research sources must be public URLs or RSS/Atom feeds. The app cites fetched items in the report; it does not use paid research APIs.
- PDF export is optional and uses `markdown` plus `weasyprint` when installed. If those packages are unavailable, Markdown export still works.
- Demo only. Not financial advice. Use the local Python app for private portfolio data.
