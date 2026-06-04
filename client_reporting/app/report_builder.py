from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from client_reporting.analytics.portfolio import PortfolioMetrics, compute_portfolio_metrics, normalize_weights
from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics, compute_snapshot_metrics
from client_reporting.data.market_data import MarketDataRequest, fetch_adjusted_close
from client_reporting.formatting.quality import validate_report
from client_reporting.formatting.report_sections import holdings_table, metrics_snapshot
from client_reporting.formatting.snapshot_sections import allocation_table, snapshot_holdings_table, snapshot_metrics_table
from client_reporting.llm.fallback import build_deterministic_report
from client_reporting.llm.fallback import build_deterministic_snapshot_report
from client_reporting.llm.ollama import OllamaClient, OllamaConfig
from client_reporting.llm.prompts import build_report_prompt, build_snapshot_report_prompt
from client_reporting.research.auto_sources import default_research_urls
from client_reporting.research.web_sources import ResearchItem, citations_table, fetch_research_sources


@dataclass(frozen=True)
class ReportRequest:
    tickers: list[str]
    weights: list[float]
    client_type: str
    period: str = "1y"
    use_ollama: bool = True
    ollama_model: str = "llama3.1"


@dataclass(frozen=True)
class SnapshotReportRequest:
    portfolio_frame: pd.DataFrame
    client_type: str
    as_of_date: str
    use_ollama: bool = True
    ollama_model: str = "llama3.1"
    research_urls: tuple[str, ...] = ()
    research_items: tuple[ResearchItem, ...] = ()
    auto_research: bool = False


@dataclass(frozen=True)
class ReportResult:
    report: str
    metrics: PortfolioMetrics | SnapshotPortfolioMetrics
    quality_issues: list[str]
    llm_source: str
    report_mode: str = "ticker"
    research_items: tuple[ResearchItem, ...] = ()


class ReportBuilder:
    def build(self, request: ReportRequest) -> ReportResult:
        client_type = _normalize_client_type(request.client_type)
        weights = normalize_weights(request.tickers, request.weights)
        prices = fetch_adjusted_close(MarketDataRequest(tickers=list(weights.keys()), period=request.period))
        metrics = compute_portfolio_metrics(prices, weights)

        source = "deterministic"
        narrative = ""
        if request.use_ollama:
            try:
                client = OllamaClient(OllamaConfig(model=request.ollama_model))
                prompt = build_report_prompt(metrics, client_type)
                narrative = client.generate(prompt)
                source = "ollama"
            except Exception:
                narrative = build_deterministic_report(metrics, client_type)
        else:
            narrative = build_deterministic_report(metrics, client_type)

        report = _compose_report(narrative, metrics, client_type)
        issues = validate_report(report, metrics)
        return ReportResult(report=report, metrics=metrics, quality_issues=issues, llm_source=source)

    def build_snapshot(self, request: SnapshotReportRequest) -> ReportResult:
        client_type = _normalize_client_type(request.client_type)
        metrics = compute_snapshot_metrics(request.portfolio_frame, request.as_of_date)
        research_urls = _research_urls(metrics, request)
        research_items = request.research_items or tuple(fetch_research_sources(research_urls))

        source = "deterministic"
        if request.use_ollama:
            try:
                client = OllamaClient(OllamaConfig(model=request.ollama_model))
                prompt = build_snapshot_report_prompt(metrics, client_type, list(research_items))
                narrative = client.generate(prompt)
                source = "ollama"
            except Exception:
                narrative = build_deterministic_snapshot_report(metrics, client_type, list(research_items))
        else:
            narrative = build_deterministic_snapshot_report(metrics, client_type, list(research_items))

        report = _compose_snapshot_report(narrative, metrics, client_type, list(research_items))
        issues = validate_report(report, metrics)
        return ReportResult(
            report=report,
            metrics=metrics,
            quality_issues=issues,
            llm_source=source,
            report_mode="snapshot",
            research_items=research_items,
        )


def _research_urls(metrics: SnapshotPortfolioMetrics, request: SnapshotReportRequest) -> tuple[str, ...]:
    urls: list[str] = []
    if request.auto_research:
        urls.extend(default_research_urls(metrics))
    urls.extend(request.research_urls)
    deduped: list[str] = []
    for url in urls:
        if url and url not in deduped:
            deduped.append(url)
    return tuple(deduped)


def _normalize_client_type(client_type: str) -> str:
    normalized = client_type.strip().lower()
    if normalized not in {"retail", "institutional"}:
        raise ValueError("client_type must be either 'retail' or 'institutional'.")
    return normalized


def _compose_report(narrative: str, metrics: PortfolioMetrics, client_type: str) -> str:
    title = "Institutional Portfolio Report" if client_type == "institutional" else "Client Portfolio Report"
    return f"""
# {title}

{narrative.strip()}

## Portfolio Metrics
{metrics_snapshot(metrics)}

## Holdings Attribution
{holdings_table(metrics)}
""".strip()


def _compose_snapshot_report(
    narrative: str,
    metrics: SnapshotPortfolioMetrics,
    client_type: str,
    research_items: list[ResearchItem] | None = None,
) -> str:
    title = "Institutional Portfolio Snapshot Report" if client_type == "institutional" else "Client Portfolio Snapshot Report"
    citations = citations_table(research_items or [])
    citation_section = f"\n\n## Research Sources\n{citations}" if citations else ""
    return f"""
# {title}

{narrative.strip()}

## Portfolio Metrics
{snapshot_metrics_table(metrics)}

## Asset Allocation
{allocation_table(metrics)}

## Top Holdings
{snapshot_holdings_table(metrics)}
{citation_section}
""".strip()
