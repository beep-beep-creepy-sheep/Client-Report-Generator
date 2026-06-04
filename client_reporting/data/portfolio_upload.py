from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd


REQUIRED_NUMERIC_COLUMNS = {"market_value"}

COLUMN_ALIASES = {
    "name": {"name", "holding", "security", "security_name", "fund_name", "description"},
    "isin": {"isin", "isin_code"},
    "sedol": {"sedol", "sedol_code"},
    "ticker": {"ticker", "symbol", "yf_ticker", "yahoo_ticker"},
    "asset_type": {"asset_type", "asset class", "asset_class", "type", "instrument_type"},
    "market_value": {"market_value", "market value", "value", "valuation", "current_value", "mv"},
    "book_cost": {"book_cost", "book cost", "cost", "cost_basis", "base_cost", "purchase_cost"},
    "gain_loss": {"gain_loss", "gain/loss", "gain loss", "unrealised_gain_loss", "unrealized_gain_loss", "pnl"},
    "gain_loss_pct": {"gain_loss_pct", "gain/loss %", "gain loss %", "return", "holding_return"},
    "currency": {"currency", "ccy"},
}

ASSET_TYPE_ALIASES = {
    "direct equity": "Direct Equity",
    "equity": "Direct Equity",
    "stock": "Direct Equity",
    "direct": "Direct Equity",
    "etf": "ETF",
    "exchange traded fund": "ETF",
    "fund": "Fund",
    "mutual fund": "Fund",
    "oeic": "Fund",
    "unit trust": "Fund",
    "property fund": "Property Fund",
    "real estate fund": "Property Fund",
    "reit fund": "Property Fund",
    "mmf": "MMF",
    "money market": "MMF",
    "money market fund": "MMF",
    "cash": "MMF",
}


@dataclass(frozen=True)
class UploadedPortfolio:
    frame: pd.DataFrame
    source_name: str


class PortfolioUploadError(ValueError):
    """Raised when an uploaded portfolio file cannot be interpreted."""


def read_portfolio_upload(file: BinaryIO, filename: str) -> UploadedPortfolio:
    suffix = filename.lower().rsplit(".", maxsplit=1)[-1]
    if suffix in {"xlsx", "xls"}:
        raw = pd.read_excel(file)
    elif suffix == "csv":
        raw = pd.read_csv(file)
    else:
        raise PortfolioUploadError("Upload an .xlsx, .xls, or .csv portfolio file.")

    frame = normalize_portfolio_frame(raw)
    return UploadedPortfolio(frame=frame, source_name=filename)


def normalize_portfolio_frame(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        raise PortfolioUploadError("The uploaded portfolio file is empty.")

    frame = raw.copy()
    frame.columns = [_clean_column_name(column) for column in frame.columns]
    rename_map = _build_rename_map(frame.columns)
    frame = frame.rename(columns=rename_map)

    missing = sorted(REQUIRED_NUMERIC_COLUMNS - set(frame.columns))
    if missing:
        raise PortfolioUploadError(f"Missing required column(s): {', '.join(missing)}.")

    if "name" not in frame.columns:
        frame["name"] = "Unnamed holding"
    if "asset_type" not in frame.columns:
        frame["asset_type"] = "Fund"

    for column in ["market_value", "book_cost", "gain_loss", "gain_loss_pct"]:
        if column in frame.columns:
            frame[column] = frame[column].apply(_to_number)

    frame = frame[frame["market_value"].fillna(0) != 0].copy()
    if frame.empty:
        raise PortfolioUploadError("No holdings with non-zero market value were found.")

    if "gain_loss" not in frame.columns and "book_cost" in frame.columns:
        frame["gain_loss"] = frame["market_value"] - frame["book_cost"]
    if "gain_loss" not in frame.columns:
        frame["gain_loss"] = 0.0

    if "book_cost" not in frame.columns:
        frame["book_cost"] = frame["market_value"] - frame["gain_loss"]

    if "gain_loss_pct" not in frame.columns:
        frame["gain_loss_pct"] = frame.apply(_gain_loss_pct, axis=1)
    else:
        frame["gain_loss_pct"] = frame["gain_loss_pct"].fillna(frame.apply(_gain_loss_pct, axis=1))

    for column in ["isin", "sedol", "ticker", "currency"]:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    frame["name"] = frame["name"].fillna("Unnamed holding").astype(str).str.strip()
    frame["asset_type"] = frame["asset_type"].fillna("Fund").astype(str).map(normalize_asset_type)
    frame["identifier"] = frame.apply(_identifier, axis=1)
    return frame.reset_index(drop=True)


def normalize_asset_type(value: str) -> str:
    cleaned = value.strip().lower()
    return ASSET_TYPE_ALIASES.get(cleaned, value.strip().title() if value.strip() else "Fund")


def _build_rename_map(columns: list[str]) -> dict[str, str]:
    rename_map: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for column in columns:
            if column in aliases:
                rename_map[column] = canonical
    return rename_map


def _clean_column_name(column: object) -> str:
    return str(column).strip().lower().replace("-", "_")


def _to_number(value: object) -> float:
    if pd.isna(value):
        return float("nan")
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip()
        if cleaned.endswith("%"):
            return float(cleaned[:-1]) / 100
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = f"-{cleaned[1:-1]}"
        return float(cleaned) if cleaned else float("nan")
    return float(value)


def _gain_loss_pct(row: pd.Series) -> float:
    book_cost = float(row.get("book_cost") or 0)
    if book_cost == 0:
        return 0.0
    return float(row.get("gain_loss") or 0) / book_cost


def _identifier(row: pd.Series) -> str:
    for column in ["isin", "sedol", "ticker"]:
        value = str(row.get(column, "")).strip()
        if value:
            return value
    return str(row.get("name", "Unnamed holding")).strip()
