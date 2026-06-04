import pandas as pd

from client_reporting.analytics.snapshot import compute_snapshot_metrics
from client_reporting.data.portfolio_upload import normalize_portfolio_frame


def test_normalize_portfolio_frame_accepts_fund_identifiers_and_gain_loss():
    raw = pd.DataFrame(
        [
            {
                "Security Name": "Global Fund",
                "ISIN": "IE00TEST1234",
                "SEDOL": "",
                "Asset Class": "Fund",
                "Market Value": "100,000",
                "Book Cost": "90,000",
                "Gain/Loss": "10,000",
            },
            {
                "Security Name": "Liquidity Fund",
                "SEDOL": "B123456",
                "Asset Class": "MMF",
                "Market Value": 50000,
                "Book Cost": 50000,
                "Gain/Loss": 0,
            },
        ]
    )

    frame = normalize_portfolio_frame(raw)

    assert list(frame["asset_type"]) == ["Fund", "MMF"]
    assert frame.loc[0, "identifier"] == "IE00TEST1234"
    assert frame.loc[1, "identifier"] == "B123456"
    assert frame["gain_loss"].sum() == 10000


def test_compute_snapshot_metrics_calculates_concentration_and_allocation():
    frame = normalize_portfolio_frame(
        pd.DataFrame(
            [
                {"name": "Fund A", "asset_type": "Fund", "market_value": 600, "book_cost": 500, "gain_loss": 100},
                {"name": "MMF A", "asset_type": "MMF", "market_value": 250, "book_cost": 250, "gain_loss": 0},
                {
                    "name": "Equity A",
                    "ticker": "MSFT",
                    "asset_type": "Direct Equity",
                    "market_value": 150,
                    "book_cost": 100,
                    "gain_loss": 50,
                },
            ]
        )
    )

    metrics = compute_snapshot_metrics(frame, "2026-06-04")

    assert metrics.total_market_value == 1000
    assert metrics.total_gain_loss == 150
    assert metrics.asset_allocation["Fund"] == 0.6
    assert metrics.mmf_weight == 0.25
    assert metrics.direct_equity_weight == 0.15
    assert metrics.top_positions[0].name == "Fund A"
