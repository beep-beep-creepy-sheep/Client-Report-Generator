from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class MarketDataRequest:
    tickers: list[str]
    period: str = "1y"
    start: date | None = None
    end: date | None = None


class MarketDataError(RuntimeError):
    """Raised when market data is missing or unusable."""


def normalize_tickers(tickers: Iterable[str]) -> list[str]:
    normalized = [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    if not normalized:
        raise MarketDataError("At least one ticker is required.")
    return normalized


def fetch_adjusted_close(request: MarketDataRequest) -> pd.DataFrame:
    tickers = normalize_tickers(request.tickers)
    raw = _download(tickers, request)
    if raw.empty:
        raise MarketDataError("No price data was returned by yfinance.")

    prices = _extract_close(raw, tickers)
    prices = prices.dropna(how="all").ffill().dropna(axis=1, how="any")
    missing = sorted(set(tickers) - set(prices.columns))
    if missing:
        retry_prices = _retry_missing_tickers(missing, request)
        prices = pd.concat([prices, retry_prices], axis=1).ffill().dropna(axis=1, how="any")
        missing = sorted(set(tickers) - set(prices.columns))
    if missing:
        raise MarketDataError(f"Missing usable price data for: {', '.join(missing)}")
    if len(prices) < 30:
        raise MarketDataError("At least 30 daily observations are required for reporting.")
    return prices[tickers]


def _download(tickers: list[str], request: MarketDataRequest) -> pd.DataFrame:
    download_kwargs = {
        "tickers": tickers,
        "auto_adjust": True,
        "progress": False,
        "group_by": "column",
        "threads": len(tickers) > 1,
    }
    if request.start or request.end:
        download_kwargs["start"] = request.start
        download_kwargs["end"] = request.end
    else:
        download_kwargs["period"] = request.period
    return yf.download(**download_kwargs)


def _retry_missing_tickers(missing: list[str], request: MarketDataRequest) -> pd.DataFrame:
    recovered: list[pd.DataFrame] = []
    for ticker in missing:
        raw = _download([ticker], request)
        if raw.empty:
            continue
        try:
            recovered.append(_extract_close(raw, [ticker]))
        except MarketDataError:
            continue
    if not recovered:
        return pd.DataFrame()
    return pd.concat(recovered, axis=1)


def _extract_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        elif "Adj Close" in raw.columns.get_level_values(0):
            close = raw["Adj Close"]
        else:
            raise MarketDataError("Downloaded data does not contain close prices.")
    else:
        close = raw[["Close"]] if "Close" in raw.columns else raw[["Adj Close"]]

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0])
    if len(tickers) == 1 and list(close.columns) != tickers:
        close.columns = tickers
    return close
