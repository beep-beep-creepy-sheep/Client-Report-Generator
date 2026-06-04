from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from client_reporting.app.report_builder import ReportBuilder, ReportRequest, SnapshotReportRequest
from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics
from client_reporting.data.portfolio_upload import PortfolioUploadError, read_portfolio_upload
from client_reporting.export.pdf import PdfExportError, markdown_to_pdf_bytes


st.set_page_config(page_title="AI Client Reporting Engine", layout="wide")

st.title("AI Client Reporting Engine")

with st.sidebar:
    st.header("Report Settings")
    client_type = st.selectbox("Client type", ["retail", "institutional"])
    use_ollama = st.checkbox("Use local Ollama", value=True)


def parse_csv_values(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_weights(raw: str) -> list[float]:
    return [float(item.strip().rstrip("%")) for item in raw.split(",") if item.strip()]


def sample_portfolio_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": "Global Equity Fund",
                "isin": "IE00B4L5Y983",
                "sedol": "",
                "ticker": "",
                "asset_type": "Fund",
                "market_value": 420000,
                "book_cost": 390000,
                "gain_loss": 30000,
                "currency": "GBP",
            },
            {
                "name": "US Equity ETF",
                "isin": "IE00B3XXRP09",
                "sedol": "",
                "ticker": "VTI",
                "asset_type": "ETF",
                "market_value": 280000,
                "book_cost": 250000,
                "gain_loss": 30000,
                "currency": "GBP",
            },
            {
                "name": "Sterling Liquidity Fund",
                "isin": "",
                "sedol": "B1Y9TB3",
                "ticker": "",
                "asset_type": "MMF",
                "market_value": 175000,
                "book_cost": 175000,
                "gain_loss": 0,
                "currency": "GBP",
            },
            {
                "name": "UK Commercial Property Fund",
                "isin": "",
                "sedol": "B8FMRX8",
                "ticker": "",
                "asset_type": "Property Fund",
                "market_value": 125000,
                "book_cost": 140000,
                "gain_loss": -15000,
                "currency": "GBP",
            },
            {
                "name": "Microsoft Corp",
                "isin": "US5949181045",
                "sedol": "2588173",
                "ticker": "MSFT",
                "asset_type": "Direct Equity",
                "market_value": 90000,
                "book_cost": 72000,
                "gain_loss": 18000,
                "currency": "GBP",
            },
        ]
    )


upload_tab, ticker_tab = st.tabs(["Upload portfolio snapshot", "Ticker model"])

with upload_tab:
    st.subheader("Daily Portfolio Snapshot")
    st.caption("Use this for fund-heavy portfolios. ISIN and SEDOL identify holdings; uploaded value and gain/loss drive the report.")

    with st.expander("Expected columns"):
        st.write(
            "Required: `market_value`. Recommended: `name`, `isin`, `sedol`, `ticker`, "
            "`asset_type`, `book_cost`, `gain_loss`, `gain_loss_pct`, `currency`."
        )
        st.dataframe(sample_portfolio_frame(), use_container_width=True)

    uploaded_file = st.file_uploader("Upload Excel or CSV", type=["xlsx", "xls", "csv"])
    as_of_date = st.date_input("As-of date")
    parsed_upload = None
    if uploaded_file is not None:
        try:
            parsed_upload = read_portfolio_upload(uploaded_file, uploaded_file.name)
            st.dataframe(parsed_upload.frame.head(50), use_container_width=True)
            st.caption(f"Loaded {len(parsed_upload.frame)} holdings from {parsed_upload.source_name}.")
        except PortfolioUploadError as exc:
            st.error(f"Could not read portfolio file: {exc}")

    if st.button("Generate snapshot report", type="primary", disabled=parsed_upload is None):
        try:
            request = SnapshotReportRequest(
                portfolio_frame=parsed_upload.frame,
                client_type=client_type,
                as_of_date=str(as_of_date),
                use_ollama=use_ollama,
            )
            result = ReportBuilder().build_snapshot(request)
            st.session_state["report_result"] = result
        except Exception as exc:
            st.error(f"Could not generate report: {exc}")

with ticker_tab:
    st.subheader("Ticker-Based Portfolio")
    st.caption("Use this for direct equity or ETFs with Yahoo Finance tickers.")
    tickers_raw = st.text_input("Tickers", value="AAPL, MSFT, VTI, BND")
    weights_raw = st.text_input("Weights", value="35, 25, 25, 15")
    period = st.selectbox("Lookback period", ["6mo", "1y", "2y", "5y"], index=1)

    if st.button("Generate ticker report", type="primary"):
        try:
            request = ReportRequest(
                tickers=parse_csv_values(tickers_raw),
                weights=parse_weights(weights_raw),
                client_type=client_type,
                period=period,
                use_ollama=use_ollama,
            )
            result = ReportBuilder().build(request)
            st.session_state["report_result"] = result
        except Exception as exc:
            st.error(f"Could not generate report: {exc}")

result = st.session_state.get("report_result")
if result:
    left, right = st.columns([0.68, 0.32])
    with left:
        st.subheader("Preview")
        st.markdown(result.report)

    with right:
        st.subheader("Controls")
        st.metric("LLM source", result.llm_source)
        if isinstance(result.metrics, SnapshotPortfolioMetrics):
            st.metric("Market value", f"{result.metrics.total_market_value:,.0f}")
            st.metric("Gain/Loss", f"{result.metrics.total_gain_loss:,.0f}")
            st.metric("Gain/Loss %", f"{result.metrics.total_gain_loss_pct:.1%}")
        else:
            st.metric("Total return", f"{result.metrics.total_return:.1%}")
            st.metric("Annualized volatility", f"{result.metrics.annualized_volatility:.1%}")
            st.metric("Max drawdown", f"{result.metrics.max_drawdown:.1%}")

        st.download_button(
            "Download Markdown",
            data=result.report.encode("utf-8"),
            file_name="client_report.md",
            mime="text/markdown",
        )

        try:
            pdf_bytes = markdown_to_pdf_bytes(result.report)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name="client_report.pdf",
                mime="application/pdf",
            )
        except PdfExportError:
            st.caption("PDF export is available when WeasyPrint system dependencies are installed.")

        if result.quality_issues:
            st.warning("Quality-control review found issues:")
            for issue in result.quality_issues:
                st.write(f"- {issue}")
        else:
            st.success("Quality-control checks passed.")
else:
    st.info("Enter portfolio inputs in the sidebar and generate a report.")
