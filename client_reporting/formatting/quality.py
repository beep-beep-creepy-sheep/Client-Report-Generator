from __future__ import annotations

import re

GENERIC_PHRASES = (
    "market conditions",
    "it is important to note",
    "as an ai",
    "various factors",
    "could be impacted",
    "diversified portfolio may",
)


def validate_report(report: str, metrics: object) -> list[str]:
    issues: list[str] = []
    lower = report.lower()
    for phrase in GENERIC_PHRASES:
        if phrase in lower:
            issues.append(f"Generic phrase detected: '{phrase}'.")

    required_sections = [
        "Performance Summary",
        "Key Drivers",
        "Risk Overview",
        "Outlook Commentary",
    ]
    for section in required_sections:
        if section not in report:
            issues.append(f"Missing section: {section}.")

    metric_patterns = _metric_patterns(metrics)
    if not any(pattern in report for pattern in metric_patterns):
        issues.append("Report does not reference calculated portfolio metrics.")

    vague_sentences = [
        sentence
        for sentence in re.findall(r"[^.!?]*(?:may|could|might)[^.!?]*[.!?]", report, flags=re.I)
        if _is_unsupported_vague_sentence(sentence)
    ]
    if len(vague_sentences) > 3:
        issues.append("Report contains too many vague conditional statements.")
    return issues


def _is_unsupported_vague_sentence(sentence: str) -> bool:
    lowered = sentence.lower()
    if re.search(r"\[[0-9]+\]", sentence):
        return False
    if re.search(r"\d", sentence):
        return False
    supported_terms = (
        "portfolio",
        "allocation",
        "exposure",
        "holding",
        "research",
        "evidence",
        "metric",
        "gain/loss",
        "liquidity",
        "risk",
    )
    if any(term in lowered for term in supported_terms):
        return False
    return True


def _metric_patterns(metrics: object) -> list[str]:
    if hasattr(metrics, "total_return"):
        return [
            f"{getattr(metrics, 'total_return'):.1%}",
            f"{getattr(metrics, 'annualized_volatility'):.1%}",
            f"{getattr(metrics, 'max_drawdown'):.1%}",
        ]
    return [
        f"{getattr(metrics, 'total_gain_loss_pct'):.1%}",
        f"{getattr(metrics, 'fund_weight'):.1%}",
        f"{getattr(metrics, 'concentration_top10'):.1%}",
        f"{getattr(metrics, 'total_gain_loss'):,.0f}",
    ]
