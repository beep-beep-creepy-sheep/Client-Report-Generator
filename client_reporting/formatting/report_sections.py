from __future__ import annotations

from client_reporting.analytics.portfolio import PortfolioMetrics
from client_reporting.formatting.numbers import pct, ratio


def metrics_snapshot(metrics: PortfolioMetrics) -> str:
    rows = [
        ("Period", f"{metrics.start_date} to {metrics.end_date}"),
        ("Total return", pct(metrics.total_return)),
        ("Annualized return", pct(metrics.annualized_return)),
        ("Annualized volatility", pct(metrics.annualized_volatility)),
        ("Maximum drawdown", pct(metrics.max_drawdown)),
        ("Sharpe ratio", ratio(metrics.sharpe_ratio)),
        ("Worst daily return", pct(metrics.worst_day)),
        ("Top-three concentration", pct(metrics.concentration_top3)),
    ]
    body = "\n".join(f"| {label} | {value} |" for label, value in rows)
    return f"| Metric | Value |\n|---|---:|\n{body}"


def holdings_table(metrics: PortfolioMetrics) -> str:
    rows = [
        (
            item.ticker,
            pct(item.weight),
            pct(item.total_return),
            pct(item.annualized_volatility),
            pct(item.contribution),
        )
        for item in sorted(metrics.positions, key=lambda pos: pos.weight, reverse=True)
    ]
    body = "\n".join(
        f"| {ticker} | {weight} | {total_return} | {volatility} | {contribution} |"
        for ticker, weight, total_return, volatility, contribution in rows
    )
    return (
        "| Holding | Weight | Return | Ann. Volatility | Return Contribution |\n"
        "|---|---:|---:|---:|---:|\n"
        f"{body}"
    )
