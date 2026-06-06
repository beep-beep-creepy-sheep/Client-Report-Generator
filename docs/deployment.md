# Deployment

This repository has two web surfaces.

## Public Live Website

The public website is an interactive browser-only React/Vite app in `site/`. It is suitable for Vercel and for the GitHub repository About/Website field.

It supports sample loading, CSV upload, editable holdings, client-type selection, portfolio metrics, deterministic report generation, and Markdown download. It does not call the Python backend.

### Vercel Settings

```text
Framework preset: Vite
Root directory: site
Build command: npm run build
Output directory: dist
```

## Local Python App

The local app is the real interactive reporting workspace:

```bash
pip install -r requirements.txt
python3 web_app/server.py
```

Open `http://localhost:8501`.

Use local mode for private portfolio data, uploaded holdings files, public source fetching, optional Ollama, and Markdown/PDF export.

## Disclaimers

- Demo only.
- Not financial advice.
- The public browser-only site should not receive client data.
- Local mode is preferred for private portfolio data.
