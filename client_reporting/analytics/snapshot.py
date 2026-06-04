from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SnapshotHolding:
    name: str
    identifier: str
    asset_type: str
    weight: float
    market_value: float
    book_cost: float
    gain_loss: float
    gain_loss_pct: float
    ticker: str = ""
    isin: str = ""
    sedol: str = ""


@dataclass(frozen=True)
class SnapshotPortfolioMetrics:
    as_of_date: str
    holdings_count: int
    total_market_value: float
    total_book_cost: float
    total_gain_loss: float
    total_gain_loss_pct: float
    asset_allocation: dict[str, float]
    concentration_top10: float
    fund_weight: float
    direct_equity_weight: float
    mmf_weight: float
    property_fund_weight: float
    top_positions: list[SnapshotHolding]
    key_drivers: list[SnapshotHolding]
    winners: list[SnapshotHolding]
    losers: list[SnapshotHolding]
    holdings: list[SnapshotHolding]
    missing_identifier_count: int
    risk_flags: list[str]


class SnapshotAnalyticsError(ValueError):
    """Raised when snapshot analytics cannot be calculated."""


def compute_snapshot_metrics(frame: pd.DataFrame, as_of_date: str) -> SnapshotPortfolioMetrics:
    if frame.empty:
        raise SnapshotAnalyticsError("Portfolio snapshot is empty.")

    total_market_value = float(frame["market_value"].sum())
    if total_market_value <= 0:
        raise SnapshotAnalyticsError("Total market value must be greater than zero.")

    enriched = frame.copy()
    enriched["weight"] = enriched["market_value"] / total_market_value
    total_book_cost = float(enriched["book_cost"].sum())
    total_gain_loss = float(enriched["gain_loss"].sum())
    total_gain_loss_pct = total_gain_loss / total_book_cost if total_book_cost else 0.0

    holdings = [_row_to_holding(row) for _, row in enriched.iterrows()]
    top_positions = sorted(holdings, key=lambda holding: holding.weight, reverse=True)[:10]
    key_drivers = sorted(holdings, key=lambda holding: abs(holding.gain_loss), reverse=True)[:10]
    winners = sorted([holding for holding in holdings if holding.gain_loss > 0], key=lambda holding: holding.gain_loss, reverse=True)[:5]
    losers = sorted([holding for holding in holdings if holding.gain_loss < 0], key=lambda holding: holding.gain_loss)[:5]
    allocation = enriched.groupby("asset_type")["market_value"].sum().sort_values(ascending=False) / total_market_value

    metrics = SnapshotPortfolioMetrics(
        as_of_date=as_of_date,
        holdings_count=len(holdings),
        total_market_value=total_market_value,
        total_book_cost=total_book_cost,
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        asset_allocation={str(index): float(value) for index, value in allocation.items()},
        concentration_top10=float(sum(holding.weight for holding in top_positions)),
        fund_weight=_allocation_weight(allocation, ["Fund", "ETF", "Property Fund"]),
        direct_equity_weight=_allocation_weight(allocation, ["Direct Equity"]),
        mmf_weight=_allocation_weight(allocation, ["MMF"]),
        property_fund_weight=_allocation_weight(allocation, ["Property Fund"]),
        top_positions=top_positions,
        key_drivers=key_drivers,
        winners=winners,
        losers=losers,
        holdings=holdings,
        missing_identifier_count=_missing_identifier_count(enriched),
        risk_flags=[],
    )
    return metrics.__class__(**{**metrics.__dict__, "risk_flags": _risk_flags(metrics)})


def _row_to_holding(row: pd.Series) -> SnapshotHolding:
    return SnapshotHolding(
        name=str(row["name"]),
        identifier=str(row["identifier"]),
        asset_type=str(row["asset_type"]),
        weight=float(row["weight"]),
        market_value=float(row["market_value"]),
        book_cost=float(row["book_cost"]),
        gain_loss=float(row["gain_loss"]),
        gain_loss_pct=float(row["gain_loss_pct"]),
        ticker=str(row.get("ticker", "")),
        isin=str(row.get("isin", "")),
        sedol=str(row.get("sedol", "")),
    )


def _allocation_weight(allocation: pd.Series, labels: list[str]) -> float:
    return float(sum(allocation.get(label, 0.0) for label in labels))


def _missing_identifier_count(frame: pd.DataFrame) -> int:
    identifiers = frame[["isin", "sedol", "ticker"]].fillna("").astype(str)
    return int((identifiers.apply(lambda row: not any(value.strip() for value in row), axis=1)).sum())


def _risk_flags(metrics: SnapshotPortfolioMetrics) -> list[str]:
    flags: list[str] = []
    largest = metrics.top_positions[0] if metrics.top_positions else None
    if largest and largest.weight >= 0.1:
        flags.append(f"Largest holding is {largest.name} at {largest.weight:.1%}.")
    if metrics.concentration_top10 >= 0.6:
        flags.append(f"Top ten holdings represent {metrics.concentration_top10:.1%} of portfolio value.")
    if metrics.property_fund_weight >= 0.15:
        flags.append(f"Property fund exposure is {metrics.property_fund_weight:.1%}; liquidity terms should be reviewed.")
    if metrics.mmf_weight >= 0.2:
        flags.append(f"MMF/cash-like exposure is {metrics.mmf_weight:.1%}; yield and reinvestment drag should be monitored.")
    if metrics.missing_identifier_count:
        flags.append(f"{metrics.missing_identifier_count} holdings have no ISIN, SEDOL, or ticker identifier.")
    if not flags:
        flags.append("No snapshot-level concentration or identifier issue breached the review threshold.")
    return flags
