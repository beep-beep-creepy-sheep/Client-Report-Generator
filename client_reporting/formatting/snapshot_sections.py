from __future__ import annotations

from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics
from client_reporting.formatting.numbers import pct


def money(value: float) -> str:
    return f"{value:,.0f}"


def snapshot_metrics_table(metrics: SnapshotPortfolioMetrics) -> str:
    rows = [
        ("As-of date", metrics.as_of_date),
        ("Holdings", str(metrics.holdings_count)),
        ("Market value", money(metrics.total_market_value)),
        ("Book cost", money(metrics.total_book_cost)),
        ("Unrealized gain/loss", money(metrics.total_gain_loss)),
        ("Gain/loss on cost", pct(metrics.total_gain_loss_pct)),
        ("Top-ten concentration", pct(metrics.concentration_top10)),
        ("Fund/ETF/property fund weight", pct(metrics.fund_weight)),
        ("Direct equity weight", pct(metrics.direct_equity_weight)),
        ("MMF/cash-like weight", pct(metrics.mmf_weight)),
    ]
    body = "\n".join(f"| {label} | {value} |" for label, value in rows)
    return f"| Metric | Value |\n|---|---:|\n{body}"


def allocation_table(metrics: SnapshotPortfolioMetrics) -> str:
    body = "\n".join(
        f"| {asset_type} | {pct(weight)} |"
        for asset_type, weight in sorted(metrics.asset_allocation.items(), key=lambda item: item[1], reverse=True)
    )
    return f"| Asset type | Weight |\n|---|---:|\n{body}"


def snapshot_holdings_table(metrics: SnapshotPortfolioMetrics, limit: int = 15) -> str:
    body = "\n".join(
        "| {name} | {identifier} | {asset_type} | {weight} | {value} | {gain_loss} | {gain_loss_pct} |".format(
            name=holding.name,
            identifier=holding.identifier,
            asset_type=holding.asset_type,
            weight=pct(holding.weight),
            value=money(holding.market_value),
            gain_loss=money(holding.gain_loss),
            gain_loss_pct=pct(holding.gain_loss_pct),
        )
        for holding in metrics.top_positions[:limit]
    )
    return (
        "| Holding | Identifier | Type | Weight | Market Value | Gain/Loss | Gain/Loss % |\n"
        "|---|---|---|---:|---:|---:|---:|\n"
        f"{body}"
    )
