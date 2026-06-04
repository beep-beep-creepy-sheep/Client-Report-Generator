from __future__ import annotations

from client_reporting.analytics.portfolio import PortfolioMetrics
from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics
from client_reporting.formatting.numbers import pct, ratio
from client_reporting.formatting.report_sections import holdings_table, metrics_snapshot
from client_reporting.formatting.snapshot_sections import allocation_table, snapshot_holdings_table, snapshot_metrics_table
from client_reporting.research.web_sources import ResearchItem, format_research_context


def build_report_prompt(metrics: PortfolioMetrics, client_type: str) -> str:
    tone = _tone_instruction(client_type)
    drivers = "\n".join(
        f"- {item.ticker}: weight {pct(item.weight)}, return {pct(item.total_return)}, contribution {pct(item.contribution)}"
        for item in metrics.key_drivers
    )
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    return f"""
You are writing a professional wealth-management client report.

Client type: {client_type}
Tone requirements: {tone}

Strict quality rules:
- Use the exact section headings: Performance Summary, Key Drivers, Risk Overview, Outlook Commentary.
- Reference actual metrics from the data below.
- Do not use generic filler, disclaimers, or phrases such as "market conditions" or "various factors".
- Do not claim a forecast. Outlook should explain what to monitor based on the measured portfolio profile.
- Keep the report concise and client-ready.

Portfolio metrics:
- Period: {metrics.start_date} to {metrics.end_date}
- Total return: {pct(metrics.total_return)}
- Annualized return: {pct(metrics.annualized_return)}
- Annualized volatility: {pct(metrics.annualized_volatility)}
- Maximum drawdown: {pct(metrics.max_drawdown)}
- Sharpe ratio: {ratio(metrics.sharpe_ratio)}
- Best daily return: {pct(metrics.best_day)}
- Worst daily return: {pct(metrics.worst_day)}
- Top-three concentration: {pct(metrics.concentration_top3)}

Key drivers:
{drivers}

Risk flags:
{risks}

Metrics table:
{metrics_snapshot(metrics)}

Holdings table:
{holdings_table(metrics)}
""".strip()


def build_snapshot_report_prompt(
    metrics: SnapshotPortfolioMetrics,
    client_type: str,
    research_items: list[ResearchItem] | None = None,
) -> str:
    tone = _tone_instruction(client_type)
    drivers = "\n".join(
        f"- {item.name} ({item.asset_type}, {item.identifier}): weight {pct(item.weight)}, gain/loss {item.gain_loss:,.0f}, gain/loss on cost {pct(item.gain_loss_pct)}"
        for item in metrics.key_drivers[:6]
    )
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    return f"""
You are writing a professional wealth-management client report from an uploaded daily portfolio snapshot.

Client type: {client_type}
Tone requirements: {tone}

Strict quality rules:
- Use the exact section headings: Performance Summary, Key Drivers, Research Context, Evidence Synthesis, Risk Overview, Portfolio Implications, Outlook Commentary.
- Reference actual uploaded snapshot metrics.
- When using research, cite it with bracketed references such as [1] and do not invent sources.
- Treat extracted research ideas as evidence. Connect them explicitly to portfolio exposures, gain/loss, concentration, MMF/cash-like exposure, fund exposure, property fund exposure, and direct equity exposure where relevant.
- Do not imply that ISIN or SEDOL was used to fetch paid market data.
- Do not use generic filler, disclaimers, or phrases such as "market conditions" or "various factors".
- The portfolio is mainly funds, ETFs, property funds, MMFs, and some direct equity.
- Keep the report concise and client-ready.

Snapshot metrics:
- As-of date: {metrics.as_of_date}
- Holdings: {metrics.holdings_count}
- Market value: {metrics.total_market_value:,.0f}
- Book cost: {metrics.total_book_cost:,.0f}
- Unrealized gain/loss: {metrics.total_gain_loss:,.0f}
- Gain/loss on cost: {pct(metrics.total_gain_loss_pct)}
- Fund/ETF/property fund weight: {pct(metrics.fund_weight)}
- Direct equity weight: {pct(metrics.direct_equity_weight)}
- MMF/cash-like weight: {pct(metrics.mmf_weight)}
- Top-ten concentration: {pct(metrics.concentration_top10)}

Key drivers:
{drivers}

Risk flags:
{risks}

Public research context:
{format_research_context(research_items or [])}

Metrics table:
{snapshot_metrics_table(metrics)}

Allocation table:
{allocation_table(metrics)}

Top holdings table:
{snapshot_holdings_table(metrics, limit=10)}
""".strip()


def _tone_instruction(client_type: str) -> str:
    if client_type == "institutional":
        return "technical, metric-driven, concise, suitable for an investment committee."
    return "plain English, narrative, low jargon, suitable for an individual investor."
