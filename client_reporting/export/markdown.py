from __future__ import annotations

from pathlib import Path


def write_markdown(report: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report, encoding="utf-8")
    return destination
