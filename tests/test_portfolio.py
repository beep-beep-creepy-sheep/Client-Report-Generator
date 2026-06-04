import pandas as pd

from client_reporting.analytics.portfolio import compute_portfolio_metrics, normalize_weights


def test_normalize_weights_accepts_percentage_inputs():
    weights = normalize_weights(["AAPL", "MSFT"], [60, 40])

    assert weights == {"AAPL": 0.6, "MSFT": 0.4}


def test_compute_portfolio_metrics_uses_weighted_returns():
    dates = pd.date_range("2024-01-01", periods=40, freq="B")
    prices = pd.DataFrame(
        {
            "AAA": [100 + idx for idx in range(40)],
            "BBB": [100 + idx * 0.5 for idx in range(40)],
        },
        index=dates,
    )
    metrics = compute_portfolio_metrics(prices, {"AAA": 0.75, "BBB": 0.25})

    assert metrics.total_return > 0
    assert metrics.annualized_volatility >= 0
    assert metrics.key_drivers[0].ticker == "AAA"
