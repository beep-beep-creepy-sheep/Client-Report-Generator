from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class PositionMetric:
    ticker: str
    weight: float
    total_return: float
    annualized_volatility: float
    contribution: float


@dataclass(frozen=True)
class PortfolioMetrics:
    tickers: list[str]
    weights: dict[str, float]
    start_date: str
    end_date: str
    observations: int
    total_return: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    sharpe_ratio: float
    best_day: float
    worst_day: float
    concentration_top3: float
    positions: list[PositionMetric]
    key_drivers: list[PositionMetric]
    risk_flags: list[str]


class PortfolioInputError(ValueError):
    """Raised when portfolio inputs are invalid."""


def normalize_weights(tickers: Iterable[str], weights: Iterable[float]) -> dict[str, float]:
    ticker_list = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    weight_list = [float(weight) for weight in weights]
    if len(ticker_list) != len(weight_list):
        raise PortfolioInputError("Tickers and weights must have the same length.")
    if not ticker_list:
        raise PortfolioInputError("At least one position is required.")
    if any(weight < 0 for weight in weight_list):
        raise PortfolioInputError("Short positions are not supported in this report template.")
    total = sum(weight_list)
    if total <= 0:
        raise PortfolioInputError("Total weight must be greater than zero.")
    return {ticker: weight / total for ticker, weight in zip(ticker_list, weight_list)}


def compute_portfolio_metrics(prices: pd.DataFrame, weights: dict[str, float]) -> PortfolioMetrics:
    prices = prices[list(weights.keys())].dropna()
    returns = prices.pct_change().dropna()
    if returns.empty:
        raise PortfolioInputError("Not enough price observations to calculate returns.")

    weight_series = pd.Series(weights)
    portfolio_returns = returns.dot(weight_series)
    cumulative = (1 + portfolio_returns).cumprod()
    drawdown = cumulative / cumulative.cummax() - 1

    total_return = float(cumulative.iloc[-1] - 1)
    ann_return = float((1 + total_return) ** (TRADING_DAYS / len(returns)) - 1)
    ann_vol = float(portfolio_returns.std() * (TRADING_DAYS**0.5))
    sharpe = float(ann_return / ann_vol) if ann_vol else 0.0

    asset_returns = prices.iloc[-1] / prices.iloc[0] - 1
    asset_vols = returns.std() * (TRADING_DAYS**0.5)
    positions = [
        PositionMetric(
            ticker=ticker,
            weight=float(weight),
            total_return=float(asset_returns[ticker]),
            annualized_volatility=float(asset_vols[ticker]),
            contribution=float(weight * asset_returns[ticker]),
        )
        for ticker, weight in weights.items()
    ]
    key_drivers = sorted(positions, key=lambda item: abs(item.contribution), reverse=True)[:3]

    return PortfolioMetrics(
        tickers=list(weights.keys()),
        weights=weights,
        start_date=str(prices.index[0].date()),
        end_date=str(prices.index[-1].date()),
        observations=len(returns),
        total_return=total_return,
        annualized_return=ann_return,
        annualized_volatility=ann_vol,
        max_drawdown=float(drawdown.min()),
        sharpe_ratio=sharpe,
        best_day=float(portfolio_returns.max()),
        worst_day=float(portfolio_returns.min()),
        concentration_top3=float(sum(sorted(weights.values(), reverse=True)[:3])),
        positions=positions,
        key_drivers=key_drivers,
        risk_flags=_risk_flags(ann_vol, float(drawdown.min()), weights),
    )


def _risk_flags(volatility: float, max_drawdown: float, weights: dict[str, float]) -> list[str]:
    flags: list[str] = []
    largest_weight = max(weights.values())
    if largest_weight >= 0.4:
        flags.append(f"Single-position concentration is elevated at {largest_weight:.1%}.")
    if volatility >= 0.22:
        flags.append(f"Annualized volatility is high at {volatility:.1%}.")
    if max_drawdown <= -0.18:
        flags.append(f"Maximum drawdown is material at {max_drawdown:.1%}.")
    if not flags:
        flags.append("No single risk metric is outside the standard review threshold.")
    return flags
