from client_reporting.app.report_builder import ReportBuilder, SnapshotReportRequest
from client_reporting.analytics.snapshot import compute_snapshot_metrics
from client_reporting.data.portfolio_upload import normalize_portfolio_frame
from client_reporting.research.auto_sources import default_research_urls
from client_reporting.research.web_sources import ResearchItem, citations_table, extract_research_ideas, infer_research_category, references_section
from client_reporting.formatting.quality import validate_report

import pandas as pd


def test_infer_research_category_identifies_monetary_policy():
    category = infer_research_category("Federal Reserve interest rate inflation monetary policy")

    assert category == "Monetary Policy"


def test_citations_table_numbers_sources():
    items = [
        ResearchItem(
            title="Policy update",
            url="https://example.com/policy",
            source="example.com",
            published="2026-06-04",
            summary="Central bank policy summary.",
            category="Monetary Policy",
        )
    ]

    table = citations_table(items)

    assert "[1]" in table
    assert "Policy update" in table
    assert "https://example.com/policy" in table


def test_snapshot_report_includes_research_context_and_implications():
    frame = normalize_portfolio_frame(
        pd.DataFrame(
            [
                {"name": "Liquidity Fund", "asset_type": "MMF", "market_value": 250, "book_cost": 250, "gain_loss": 0},
                {"name": "Global Fund", "asset_type": "Fund", "market_value": 750, "book_cost": 700, "gain_loss": 50},
            ]
        )
    )
    research = (
        ResearchItem(
            title="Rate outlook",
            url="https://example.com/rates",
            source="example.com",
            published="2026-06-04",
            summary="Policy rates remain relevant for liquidity funds.",
            category="Monetary Policy",
        ),
    )

    result = ReportBuilder().build_snapshot(
        SnapshotReportRequest(
            portfolio_frame=frame,
            client_type="institutional",
            as_of_date="2026-06-04",
            use_ollama=False,
            research_items=research,
        )
    )

    assert "## Research Context" in result.report
    assert "## Methodology and Data Basis" in result.report
    assert "## Evidence Synthesis" in result.report
    assert "## Portfolio Implications" in result.report
    assert "## References" in result.report
    assert "## Appendix A: Portfolio Metrics" in result.report
    assert "[1]" in result.report


def test_references_section_uses_professional_endnotes_not_table():
    items = [
        ResearchItem(
            title="Policy update",
            url="https://example.com/policy",
            source="example.com",
            published="2026-06-04",
            summary="Central bank policy summary.",
            category="Monetary Policy",
        )
    ]

    references = references_section(items)

    assert references.startswith("1. example.com")
    assert "[Source](https://example.com/policy)" in references
    assert "| Ref |" not in references


def test_extract_research_ideas_scores_investment_relevant_sentences():
    content = (
        "The central bank said inflation remains above target and policy rates may stay restrictive. "
        "The cafeteria menu changed on Monday. "
        "Liquidity conditions and yields are important for money market fund allocation decisions."
    )

    ideas = extract_research_ideas(content, "Monetary Policy", max_ideas=2)

    assert len(ideas) == 2
    assert any("inflation" in idea.lower() for idea in ideas)
    assert any("money market fund" in idea.lower() or "liquidity" in idea.lower() for idea in ideas)


def test_default_research_urls_reflect_portfolio_exposures():
    frame = normalize_portfolio_frame(
        pd.DataFrame(
            [
                {"name": "Liquidity Fund", "asset_type": "MMF", "market_value": 250, "book_cost": 250, "gain_loss": 0},
                {"name": "Property Fund", "asset_type": "Property Fund", "market_value": 250, "book_cost": 250, "gain_loss": 0},
                {"name": "Global Fund", "asset_type": "Fund", "market_value": 500, "book_cost": 450, "gain_loss": 50},
            ]
        )
    )
    metrics = compute_snapshot_metrics(frame, "2026-06-04")

    urls = default_research_urls(metrics)

    assert any("federalreserve.gov" in url or "bankofengland.co.uk" in url for url in urls)
    assert any("ecb.europa.eu" in url or "imf.org" in url for url in urls)


def test_quality_control_allows_cited_metric_backed_conditional_language():
    class Metrics:
        total_gain_loss_pct = 0.05
        fund_weight = 0.75
        concentration_top10 = 0.6
        total_gain_loss = 50000

    report = """
## Performance Summary
The portfolio gain/loss on cost is 5.0%.
## Key Drivers
Fund exposure is 75.0%.
## Research Context
Policy rates may affect MMF liquidity positioning [1].
## Evidence Synthesis
The 60.0% top-ten concentration could increase portfolio sensitivity to extracted research evidence.
## Risk Overview
Risk is tied to allocation and liquidity.
## Portfolio Implications
The portfolio may require monitoring because fund exposure is 75.0%.
## Outlook Commentary
Future review should use the cited evidence.
"""

    assert "Report contains too many vague conditional statements." not in validate_report(report, Metrics())
