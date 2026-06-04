from __future__ import annotations

from client_reporting.analytics.snapshot import SnapshotPortfolioMetrics


DEFAULT_RESEARCH_SOURCES = {
    "Monetary Policy": [
        "https://www.federalreserve.gov/monetarypolicy.htm",
        "https://www.ecb.europa.eu/rss/press.html",
        "https://www.bankofengland.co.uk/rss",
    ],
    "Macro": [
        "https://www.imf.org/en/news/rss",
        "https://www.oecd.org/en/topics/policy-issues/economic-outlook.html",
        "https://www.federalreserve.gov/default.htm",
    ],
    "Industry": [
        "https://www.bankofengland.co.uk/rss",
        "https://www.ecb.europa.eu/home/html/rss.en.html",
    ],
    "Fund Research": [
        "https://www.vanguard.co.uk/professional/insights-education",
        "https://www.ishares.com/uk/professional/en/insights",
    ],
}


def default_research_urls(metrics: SnapshotPortfolioMetrics, max_sources: int = 6) -> tuple[str, ...]:
    categories = ["Monetary Policy", "Macro"] if metrics.mmf_weight > 0 else ["Macro", "Monetary Policy"]
    if metrics.mmf_weight > 0:
        categories.append("Monetary Policy")
    if metrics.property_fund_weight > 0:
        categories.append("Industry")
    if metrics.fund_weight >= 0.35:
        categories.append("Fund Research")
    if metrics.direct_equity_weight > 0:
        categories.append("Industry")

    urls: list[str] = []
    for category in categories:
        for url in DEFAULT_RESEARCH_SOURCES.get(category, []):
            if url not in urls:
                urls.append(url)
            if len(urls) >= max_sources:
                return tuple(urls)
    return tuple(urls[:max_sources])
