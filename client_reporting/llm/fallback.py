from __future__ import annotations

from client_reporting.analytics.portfolio import PortfolioMetrics
from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics
from client_reporting.formatting.numbers import pct, ratio
from client_reporting.research.web_sources import ResearchItem


def build_deterministic_report(metrics: PortfolioMetrics, client_type: str) -> str:
    if client_type == "institutional":
        return _institutional_report(metrics)
    return _retail_report(metrics)


def build_deterministic_snapshot_report(
    metrics: SnapshotPortfolioMetrics,
    client_type: str,
    research_items: list[ResearchItem] | None = None,
) -> str:
    if client_type == "institutional":
        return _institutional_snapshot_report(metrics, research_items or [])
    return _retail_snapshot_report(metrics, research_items or [])


def _institutional_report(metrics: PortfolioMetrics) -> str:
    drivers = "\n".join(
        f"- {item.ticker}: {pct(item.weight)} weight, {pct(item.total_return)} holding return, {pct(item.contribution)} contribution."
        for item in metrics.key_drivers
    )
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    return f"""
## Performance Summary
The portfolio returned {pct(metrics.total_return)} over {metrics.start_date} to {metrics.end_date}, with annualized return of {pct(metrics.annualized_return)} and annualized volatility of {pct(metrics.annualized_volatility)}. The realized Sharpe ratio was {ratio(metrics.sharpe_ratio)}, and the maximum drawdown was {pct(metrics.max_drawdown)}.

## Key Drivers
{drivers}

## Risk Overview
Portfolio risk was defined by a worst daily return of {pct(metrics.worst_day)}, maximum drawdown of {pct(metrics.max_drawdown)}, and top-three concentration of {pct(metrics.concentration_top3)}.
{risks}

## Outlook Commentary
Near-term review should focus on whether the largest contributors continue to justify their allocation weights and whether volatility remains near {pct(metrics.annualized_volatility)}. A drawdown beyond {pct(metrics.max_drawdown)} would warrant a formal allocation review rather than a purely tactical rebalance.
""".strip()


def _retail_report(metrics: PortfolioMetrics) -> str:
    best_driver = metrics.key_drivers[0]
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    return f"""
## Performance Summary
Your portfolio gained {pct(metrics.total_return)} from {metrics.start_date} to {metrics.end_date}. Day-to-day movement was meaningful: annualized volatility was {pct(metrics.annualized_volatility)}, and the largest pullback during the period was {pct(metrics.max_drawdown)}.

## Key Drivers
The biggest measured driver was {best_driver.ticker}, which had a {pct(best_driver.weight)} portfolio weight and added {pct(best_driver.contribution)} to overall return. Across the main holdings, the report focuses on contribution, not just headline price movement, because position size determines the client impact.

## Risk Overview
The portfolio's worst single day was {pct(metrics.worst_day)}, while the best single day was {pct(metrics.best_day)}. The top three holdings represent {pct(metrics.concentration_top3)} of the portfolio, so those positions deserve the most attention in review meetings.
{risks}

## Outlook Commentary
The next review should compare expected comfort with the measured drawdown of {pct(metrics.max_drawdown)} and volatility of {pct(metrics.annualized_volatility)}. If those numbers feel too large for the client objective, the portfolio should be adjusted before performance pressure forces a rushed decision.
""".strip()


def _institutional_snapshot_report(metrics: SnapshotPortfolioMetrics, research_items: list[ResearchItem]) -> str:
    drivers = "\n".join(
        f"- {item.name}: {pct(item.weight)} weight, {item.gain_loss:,.0f} unrealized gain/loss, {pct(item.gain_loss_pct)} on cost."
        for item in metrics.key_drivers[:5]
    )
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    research = _research_context(research_items)
    evidence = _evidence_synthesis(metrics, research_items)
    implications = _portfolio_implications(metrics, research_items, "institutional")
    monitoring = _monitoring_agenda(metrics, research_items)
    return f"""
## Performance Summary
As of {metrics.as_of_date}, the portfolio market value was {metrics.total_market_value:,.0f} across {metrics.holdings_count} holdings. Total unrealized gain/loss was {metrics.total_gain_loss:,.0f}, equal to {pct(metrics.total_gain_loss_pct)} on book cost. The central conclusion is that client outcomes are being driven less by single-name equity risk and more by pooled-fund allocation, liquidity positioning, and concentration discipline.

## Methodology and Data Basis
This report uses the uploaded valuation snapshot as the primary portfolio record. Market value, book cost, unrealized gain/loss, asset type, and identifiers are treated as portfolio facts; public research sources are treated as contextual evidence and cited in brackets. ISIN and SEDOL are used for holding identification, not paid fund-data enrichment.

## Key Drivers
{drivers}

## Research Context
{research}

## Evidence Synthesis
{evidence}

## Risk Overview
Fund, ETF, and property fund exposure represented {pct(metrics.fund_weight)} of portfolio value, direct equity represented {pct(metrics.direct_equity_weight)}, and MMF/cash-like exposure represented {pct(metrics.mmf_weight)}. Top-ten concentration was {pct(metrics.concentration_top10)}.
{risks}

## Portfolio Implications
{implications}

## Monitoring Agenda
{monitoring}

## Outlook Commentary
The portfolio review should remain evidence-led: changes to allocation should be justified by the interaction between measured portfolio exposures and the cited research record, not by market narrative alone. Because this report is based on the uploaded snapshot, ISIN and SEDOL are used for identification rather than paid data enrichment.
""".strip()


def _retail_snapshot_report(metrics: SnapshotPortfolioMetrics, research_items: list[ResearchItem]) -> str:
    largest = metrics.top_positions[0]
    best = metrics.winners[0] if metrics.winners else None
    worst = metrics.losers[0] if metrics.losers else None
    best_text = f"The largest positive gain/loss contributor was {best.name}, at {best.gain_loss:,.0f}." if best else "No holding showed a positive unrealized gain/loss in the uploaded snapshot."
    worst_text = f"The largest negative gain/loss contributor was {worst.name}, at {worst.gain_loss:,.0f}." if worst else "No holding showed a negative unrealized gain/loss in the uploaded snapshot."
    risks = "\n".join(f"- {flag}" for flag in metrics.risk_flags)
    research = _research_context(research_items)
    evidence = _evidence_synthesis(metrics, research_items)
    implications = _portfolio_implications(metrics, research_items, "retail")
    monitoring = _monitoring_agenda(metrics, research_items)
    return f"""
## Performance Summary
On {metrics.as_of_date}, the portfolio was valued at {metrics.total_market_value:,.0f}. Compared with book cost, the uploaded holdings show total gain/loss of {metrics.total_gain_loss:,.0f}, or {pct(metrics.total_gain_loss_pct)}.

## Methodology and Data Basis
This report starts with the uploaded portfolio snapshot and then uses public research sources as supporting evidence. The analysis links the client's actual holding weights and gain/loss figures to the research evidence cited in brackets.

## Key Drivers
The largest holding is {largest.name}, representing {pct(largest.weight)} of the portfolio. {best_text} {worst_text}

## Research Context
{research}

## Evidence Synthesis
{evidence}

## Risk Overview
Most of the analysis comes from fund and cash-like holdings rather than only listed shares. Fund, ETF, and property fund exposure is {pct(metrics.fund_weight)}, direct equity is {pct(metrics.direct_equity_weight)}, and MMF/cash-like exposure is {pct(metrics.mmf_weight)}.
{risks}

## Portfolio Implications
{implications}

## Monitoring Agenda
{monitoring}

## Outlook Commentary
The next client discussion should start with the actual gain/loss figures in the uploaded file, then review whether the largest positions still match the client's liquidity needs and risk comfort. For funds without free daily price history, the report should rely on the platform valuation and holding-level gain/loss instead of paid data.
""".strip()


def _research_context(items: list[ResearchItem]) -> str:
    if not items:
        return "No external public research source was supplied, so this report relies on the uploaded portfolio snapshot only."
    rows: list[str] = []
    for index, item in enumerate(items, start=1):
        ideas = " ".join(item.ideas) if item.ideas else item.summary
        rows.append(f"- [{index}] {item.source} / {item.category}: {item.title}. Core evidence: {ideas}")
    return "\n".join(rows)


def _portfolio_implications(metrics: SnapshotPortfolioMetrics, items: list[ResearchItem], client_type: str) -> str:
    categories = {item.category for item in items}
    references = ", ".join(f"[{index}]" for index, _ in enumerate(items, start=1)) or "the uploaded snapshot"
    tone = "Committee focus" if client_type == "institutional" else "Client focus"
    points = [
        f"{tone}: the research evidence from {references} should be read against the portfolio's {pct(metrics.fund_weight)} fund/ETF/property allocation and {pct(metrics.concentration_top10)} top-ten concentration.",
        f"The {pct(metrics.mmf_weight)} MMF/cash-like allocation should be interpreted through extracted rate, inflation, and liquidity ideas rather than treated as a passive cash balance.",
        f"The {pct(metrics.direct_equity_weight)} direct-equity allocation should be linked to sector-specific ideas and holding-level gain/loss, not just broad market direction.",
    ]
    if "Monetary Policy" in categories and metrics.mmf_weight > 0:
        points.append("Monetary-policy sources are directly relevant because the portfolio contains cash-like/MMF exposure.")
    if "Industry" in categories and metrics.direct_equity_weight > 0:
        points.append("Industry research is relevant because direct equity exposure creates company and sector sensitivity.")
    if "Fund Research" in categories and metrics.fund_weight > 0.5:
        points.append("Fund research is relevant because most portfolio risk is expressed through pooled vehicles rather than individual securities.")
    return "\n".join(f"- {point}" for point in points)


def _evidence_synthesis(metrics: SnapshotPortfolioMetrics, items: list[ResearchItem]) -> str:
    if not items:
        return "The evidence base is limited to the uploaded valuation snapshot, so conclusions should focus on holding size, gain/loss, concentration, and liquidity profile."
    idea_refs = ", ".join(f"[{index}]" for index, item in enumerate(items, start=1) if item.ideas or item.summary)
    return (
        f"The extracted evidence {idea_refs} should be interpreted through the portfolio's measured exposures: "
        f"{pct(metrics.fund_weight)} in funds/ETFs/property funds, {pct(metrics.mmf_weight)} in MMF/cash-like holdings, "
        f"{pct(metrics.direct_equity_weight)} in direct equities, and {pct(metrics.concentration_top10)} in the top ten holdings. "
        f"That means macro and policy ideas primarily affect liquidity, yield, and fund allocation decisions, while sector or industry ideas mainly affect direct equity and specialist fund review."
    )


def _monitoring_agenda(metrics: SnapshotPortfolioMetrics, items: list[ResearchItem]) -> str:
    references = ", ".join(f"[{index}]" for index, _ in enumerate(items, start=1)) or "portfolio snapshot"
    agenda = [
        f"Reconcile the largest gain/loss contributors against the {pct(metrics.concentration_top10)} top-ten concentration before approving any rebalance.",
        f"Review MMF/cash-like exposure of {pct(metrics.mmf_weight)} against the policy and liquidity evidence in {references}.",
        f"Review property fund exposure of {pct(metrics.property_fund_weight)} for liquidity terms, dealing frequency, and valuation lag.",
        f"Document whether the {pct(metrics.fund_weight)} pooled-fund allocation remains aligned with the client's investment horizon and reporting objective.",
    ]
    return "\n".join(f"- {item}" for item in agenda)
