from __future__ import annotations

from pathlib import Path


class PdfExportError(RuntimeError):
    """Raised when optional PDF dependencies are unavailable."""


def markdown_to_pdf(report: str, destination: Path) -> Path:
    document = _render_html(report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _html_to_pdf(document, destination)
    return destination


def markdown_to_pdf_bytes(report: str) -> bytes:
    document = _render_html(report)
    return _html_to_pdf(document)


def _render_html(report: str) -> str:
    try:
        import markdown
    except Exception as exc:  # pragma: no cover - depends on optional system libs
        raise PdfExportError("Install markdown and weasyprint to enable PDF export.") from exc

    html = markdown.markdown(report, extensions=["tables"])
    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 42px; color: #17202a; }}
          h1, h2 {{ color: #102a43; }}
          table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
          th, td {{ border-bottom: 1px solid #d9e2ec; padding: 8px; text-align: right; }}
          th:first-child, td:first-child {{ text-align: left; }}
          p, li {{ font-size: 11pt; line-height: 1.5; }}
        </style>
      </head>
      <body>{html}</body>
    </html>
    """


def _html_to_pdf(document: str, destination: Path | None = None) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - depends on optional system libs
        raise PdfExportError("Install WeasyPrint to enable PDF export.") from exc

    if destination is not None:
        HTML(string=document).write_pdf(destination)
        return b""
    return bytes(HTML(string=document).write_pdf())
