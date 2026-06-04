from __future__ import annotations

import json
import sys
import uuid
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client_reporting.app.report_builder import ReportBuilder, SnapshotReportRequest
from client_reporting.data.portfolio_upload import normalize_portfolio_frame, read_portfolio_upload
from client_reporting.research.web_sources import fetch_research_sources

STATIC_DIR = ROOT / "web_app" / "static"
REPORT_CACHE: dict[str, str] = {}


class ClientReportingHandler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        path = self.path.split("?", maxsplit=1)[0]
        if path.startswith("/api/download/"):
            self._download_report(path.rsplit("/", maxsplit=1)[-1], head_only=True)
            return
        self.send_error(404)

    def do_GET(self) -> None:
        path = self.path.split("?", maxsplit=1)[0]
        if path in {"", "/"}:
            self._serve_file(STATIC_DIR / "index.html", "text/html")
            return
        if path == "/api/sample":
            self._json({"holdings": _sample_holdings()})
            return
        if path.startswith("/api/download/"):
            self._download_report(path.rsplit("/", maxsplit=1)[-1])
            return

        requested = (STATIC_DIR / path.lstrip("/")).resolve()
        if not str(requested).startswith(str(STATIC_DIR.resolve())) or not requested.exists():
            self.send_error(404)
            return
        self._serve_file(requested, _content_type(requested))

    def do_POST(self) -> None:
        if self.path == "/api/parse-upload":
            self._parse_upload()
            return
        if self.path == "/api/analyze":
            self._analyze()
            return
        self.send_error(404)

    def _parse_upload(self) -> None:
        try:
            filename, content = self._read_multipart_file()
            uploaded = read_portfolio_upload(BytesIO(content), filename)
            self._json({"holdings": _frame_to_records(uploaded.frame), "source": uploaded.source_name})
        except Exception as exc:
            self._json({"error": str(exc)}, status=400)

    def _analyze(self) -> None:
        try:
            payload = self._read_json()
            frame = normalize_portfolio_frame(pd.DataFrame(payload.get("holdings", [])))
            research_urls = tuple(str(url).strip() for url in payload.get("research_urls", []) if str(url).strip())
            research_items = tuple(fetch_research_sources(research_urls)) if research_urls else ()
            result = ReportBuilder().build_snapshot(
                SnapshotReportRequest(
                    portfolio_frame=frame,
                    client_type=str(payload.get("client_type", "retail")),
                    as_of_date=str(payload.get("as_of_date", "")),
                    use_ollama=bool(payload.get("use_ollama", False)),
                    research_items=research_items,
                    auto_research=bool(payload.get("auto_research", False)),
                )
            )
            report_id = uuid.uuid4().hex
            REPORT_CACHE[report_id] = result.report
            self._json(
                {
                    "report": result.report,
                    "markdown_download_url": f"/api/download/{report_id}",
                    "metrics": _to_jsonable(result.metrics),
                    "quality_issues": result.quality_issues,
                    "llm_source": result.llm_source,
                    "holdings": _frame_to_records(frame),
                    "research_items": _to_jsonable(list(result.research_items)),
                }
            )
        except Exception as exc:
            self._json({"error": str(exc)}, status=400)

    def _download_report(self, report_id: str, head_only: bool = False) -> None:
        report = REPORT_CACHE.get(report_id)
        if report is None:
            self.send_error(404)
            return
        body = report.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="client_report.md"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _read_multipart_file(self) -> tuple[str, bytes]:
        content_type = self.headers.get("Content-Type", "")
        marker = "boundary="
        if marker not in content_type:
            raise ValueError("Upload request is missing a multipart boundary.")

        boundary = content_type.split(marker, maxsplit=1)[1].strip().strip('"').encode("utf-8")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        for part in body.split(b"--" + boundary):
            if b"filename=" not in part:
                continue
            header_blob, _, file_blob = part.partition(b"\r\n\r\n")
            filename = _filename_from_headers(header_blob.decode("utf-8", errors="ignore"))
            return filename, file_blob.rstrip(b"\r\n-")
        raise ValueError("No file was found in the upload request.")

    def _serve_file(self, path: Path, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _content_type(path: Path) -> str:
    return {
        ".css": "text/css",
        ".js": "text/javascript",
        ".html": "text/html",
    }.get(path.suffix, "application/octet-stream")


def _filename_from_headers(headers: str) -> str:
    for segment in headers.split(";"):
        segment = segment.strip()
        if segment.startswith("filename="):
            return Path(segment.split("=", maxsplit=1)[1].strip('"')).name
    return "portfolio.csv"


def _frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [_clean_record(record) for record in frame.to_dict(orient="records")]


def _clean_record(record: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = ""
        else:
            cleaned[key] = value
    return cleaned


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def _sample_holdings() -> list[dict[str, Any]]:
    return [
        {
            "name": "Global Equity Fund",
            "isin": "IE00B4L5Y983",
            "sedol": "",
            "ticker": "",
            "asset_type": "Fund",
            "market_value": 420000,
            "book_cost": 390000,
            "gain_loss": 30000,
            "currency": "GBP",
        },
        {
            "name": "US Equity ETF",
            "isin": "IE00B3XXRP09",
            "sedol": "",
            "ticker": "VTI",
            "asset_type": "ETF",
            "market_value": 280000,
            "book_cost": 250000,
            "gain_loss": 30000,
            "currency": "GBP",
        },
        {
            "name": "Sterling Liquidity Fund",
            "isin": "",
            "sedol": "B1Y9TB3",
            "ticker": "",
            "asset_type": "MMF",
            "market_value": 175000,
            "book_cost": 175000,
            "gain_loss": 0,
            "currency": "GBP",
        },
        {
            "name": "UK Commercial Property Fund",
            "isin": "",
            "sedol": "B8FMRX8",
            "ticker": "",
            "asset_type": "Property Fund",
            "market_value": 125000,
            "book_cost": 140000,
            "gain_loss": -15000,
            "currency": "GBP",
        },
        {
            "name": "Microsoft Corp",
            "isin": "US5949181045",
            "sedol": "2588173",
            "ticker": "MSFT",
            "asset_type": "Direct Equity",
            "market_value": 90000,
            "book_cost": 72000,
            "gain_loss": 18000,
            "currency": "GBP",
        },
    ]


def run(host: str = "127.0.0.1", port: int = 8501) -> None:
    server = ThreadingHTTPServer((host, port), ClientReportingHandler)
    print(f"Client Reporting Web App: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
