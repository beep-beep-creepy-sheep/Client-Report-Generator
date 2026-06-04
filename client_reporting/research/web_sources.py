from __future__ import annotations

from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterable
from urllib.parse import urlparse
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ResearchItem:
    title: str
    url: str
    source: str
    published: str
    summary: str
    category: str
    ideas: tuple[str, ...] = ()
    excerpt: str = ""


class ResearchFetchError(RuntimeError):
    """Raised when a public source cannot be fetched or parsed."""


def fetch_research_sources(urls: Iterable[str], max_items: int = 8, timeout_seconds: int = 6) -> list[ResearchItem]:
    items: list[ResearchItem] = []
    for url in _clean_urls(urls):
        if len(items) >= max_items:
            break
        try:
            items.extend(_fetch_url(url, max_items - len(items), timeout_seconds))
        except Exception:
            continue
    return items[:max_items]


def format_research_context(items: list[ResearchItem]) -> str:
    if not items:
        return "No public research sources were supplied or successfully fetched."
    return "\n".join(
        f"[{index}] {item.title} — {item.source}, {item.published or 'date not found'} ({item.category}). "
        f"Summary: {item.summary} Ideas: {_ideas_text(item)} URL: {item.url}"
        for index, item in enumerate(items, start=1)
    )


def citations_table(items: list[ResearchItem]) -> str:
    if not items:
        return ""
    rows = "\n".join(
        f"| [{index}] | {item.title} | {item.source} | {item.published or 'N/A'} | {item.category} | {item.url} |"
        for index, item in enumerate(items, start=1)
    )
    return f"| Ref | Title | Source | Date | Category | URL |\n|---:|---|---|---|---|---|\n{rows}"


def _clean_urls(urls: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for value in urls:
        url = str(value).strip()
        if not url or url.startswith("#"):
            continue
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        cleaned.append(url)
    return cleaned


def _fetch_url(url: str, max_items: int, timeout_seconds: int) -> list[ResearchItem]:
    response = requests.get(
        url,
        timeout=timeout_seconds,
        headers={"User-Agent": "ClientReportGenerator/0.1 (+local research tool)"},
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    text = response.text
    if _looks_like_feed(text):
        return _parse_feed(text, url, max_items, timeout_seconds)
    return [_parse_page(text, url)]


def _looks_like_feed(text: str) -> bool:
    head = text.lstrip()[:500].lower()
    return "<rss" in head or "<feed" in head or "<rdf" in head


def _parse_feed(text: str, feed_url: str, max_items: int, timeout_seconds: int) -> list[ResearchItem]:
    root = ET.fromstring(text.encode("utf-8"))
    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    items: list[ResearchItem] = []
    for entry in entries[:max_items]:
        title = _xml_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"]) or "Untitled research item"
        link = _feed_link(entry) or feed_url
        published = _normalize_date(
            _xml_text(
                entry,
                [
                    "pubDate",
                    "published",
                    "updated",
                    "{http://www.w3.org/2005/Atom}published",
                    "{http://www.w3.org/2005/Atom}updated",
                ],
            )
        )
        summary = _clean_text(
            _xml_text(
                entry,
                ["description", "summary", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"],
            )
        )
        linked_content = _fetch_linked_page_text(link, timeout_seconds) if link and link != feed_url else ""
        items.append(
            _enrich_research_item(
                ResearchItem(
                    title=_clean_text(title),
                    url=link,
                    source=_source_name(link or feed_url),
                    published=published,
                    summary=_truncate(summary, 220),
                    category=infer_research_category(f"{title} {summary} {linked_content[:800]} {link}"),
                ),
                linked_content or summary,
            )
        )
    return items


def _fetch_linked_page_text(url: str, timeout_seconds: int) -> str:
    try:
        response = requests.get(
            url,
            timeout=min(timeout_seconds, 5),
            headers={"User-Agent": "ClientReportGenerator/0.1 (+local research tool)"},
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        return _page_body_text(BeautifulSoup(response.text, "html.parser"))
    except Exception:
        return ""


def _parse_page(text: str, url: str) -> ResearchItem:
    soup = BeautifulSoup(text, "html.parser")
    title = _meta_content(soup, "og:title") or (soup.title.string if soup.title else "") or "Untitled research page"
    body_text = _page_body_text(soup)
    summary = (
        _meta_content(soup, "og:description")
        or _meta_name_content(soup, "description")
        or _first_paragraph(soup)
        or _truncate(body_text, 220)
        or "No concise summary was found on the page."
    )
    published = (
        _meta_content(soup, "article:published_time")
        or _meta_name_content(soup, "date")
        or _meta_name_content(soup, "pubdate")
        or ""
    )
    return _enrich_research_item(
        ResearchItem(
            title=_clean_text(title),
            url=url,
            source=_source_name(url),
            published=_normalize_date(published),
            summary=_truncate(_clean_text(summary), 220),
            category=infer_research_category(f"{title} {summary} {body_text[:800]} {url}"),
        ),
        body_text or summary,
    )


def _enrich_research_item(item: ResearchItem, content: str) -> ResearchItem:
    cleaned = _clean_text(content)
    ideas = tuple(extract_research_ideas(cleaned, item.category, max_ideas=4))
    excerpt_source = " ".join(ideas) if ideas else cleaned
    return ResearchItem(
        title=item.title,
        url=item.url,
        source=item.source,
        published=item.published,
        summary=item.summary,
        category=item.category,
        ideas=ideas,
        excerpt=_truncate(excerpt_source, 520),
    )


def extract_research_ideas(content: str, category: str = "", max_ideas: int = 4) -> list[str]:
    sentences = _sentences(content)
    scored = sorted(
        ((score_research_sentence(sentence, category), sentence) for sentence in sentences),
        key=lambda item: item[0],
        reverse=True,
    )
    ideas: list[str] = []
    for score, sentence in scored:
        if score <= 0:
            continue
        if any(_too_similar(sentence, existing) for existing in ideas):
            continue
        ideas.append(_truncate(sentence, 240))
        if len(ideas) >= max_ideas:
            break
    return ideas


def score_research_sentence(sentence: str, category: str = "") -> int:
    lowered = sentence.lower()
    if _is_noise_sentence(lowered):
        return -5
    score = 0
    keyword_groups = {
        "macro": ["growth", "gdp", "economy", "recession", "labour", "labor", "employment", "demand"],
        "policy": ["rate", "inflation", "monetary", "central bank", "yield", "policy", "fomc", "ecb", "bank of england"],
        "industry": ["sector", "industry", "property", "real estate", "technology", "energy", "healthcare", "earnings"],
        "fund": ["fund", "etf", "portfolio", "allocation", "duration", "credit", "liquidity", "valuation"],
        "risk": ["risk", "volatility", "drawdown", "liquidity", "concentration", "uncertainty"],
    }
    for keywords in keyword_groups.values():
        score += sum(1 for keyword in keywords if keyword in lowered)
    if category and category.lower().split()[0] in lowered:
        score += 1
    if re.search(r"\d", sentence):
        score += 1
    if 80 <= len(sentence) <= 260:
        score += 1
    if len(sentence) < 45 or len(sentence) > 360:
        score -= 2
    return score


def _is_noise_sentence(lowered_sentence: str) -> bool:
    noise_terms = [
        "skip to main content",
        "toggle dropdown",
        "submit search",
        "please enable javascript",
        "pdf | html",
        "(pdf)",
        "transcripts and other historical materials",
        "communications policies",
        "fomc meeting",
        "back to top",
        "subscribe to",
        "follow us",
        "careers",
        "site map",
    ]
    return any(term in lowered_sentence for term in noise_terms)


def _sentences(content: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", content).strip()
    candidates = re.split(r"(?<=[.!?])\s+", cleaned)
    return [candidate.strip() for candidate in candidates if candidate.strip()]


def _too_similar(candidate: str, existing: str) -> bool:
    left = set(candidate.lower().split())
    right = set(existing.lower().split())
    if not left or not right:
        return False
    return len(left & right) / min(len(left), len(right)) > 0.72


def _ideas_text(item: ResearchItem) -> str:
    if not item.ideas:
        return item.excerpt or "No extractable idea found."
    return " ".join(f"- {idea}" for idea in item.ideas)


def _page_body_text(soup: BeautifulSoup) -> str:
    for unwanted in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        unwanted.decompose()
    candidates = soup.find_all(["article", "main"])
    if not candidates:
        candidates = [soup.body] if soup.body else [soup]
    text_blocks: list[str] = []
    for candidate in candidates:
        if candidate is None:
            continue
        paragraphs = [node.get_text(" ", strip=True) for node in candidate.find_all(["h1", "h2", "h3", "p", "li"])]
        text_blocks.extend(paragraph for paragraph in paragraphs if len(paragraph) > 35 and not _is_noise_sentence(paragraph.lower()))
    return _clean_text(" ".join(text_blocks))


def infer_research_category(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["central bank", "federal reserve", "ecb", "bank of england", "monetary", "interest rate", "inflation"]):
        return "Monetary Policy"
    if any(term in lowered for term in ["gdp", "macro", "economy", "labour market", "labor market", "imf", "oecd"]):
        return "Macro"
    if any(term in lowered for term in ["sector", "industry", "technology", "healthcare", "energy", "property", "real estate"]):
        return "Industry"
    if any(term in lowered for term in ["fund", "etf", "portfolio", "asset allocation", "factsheet", "outlook"]):
        return "Fund Research"
    return "General Research"


def _xml_text(entry: ET.Element, names: list[str]) -> str:
    for name in names:
        element = entry.find(name)
        if element is not None and element.text:
            return element.text
    return ""


def _feed_link(entry: ET.Element) -> str:
    link = _xml_text(entry, ["link"])
    if link:
        return link
    for element in entry.findall("{http://www.w3.org/2005/Atom}link"):
        href = element.attrib.get("href", "")
        if href:
            return href
    return ""


def _meta_content(soup: BeautifulSoup, property_name: str) -> str:
    element = soup.find("meta", attrs={"property": property_name})
    return str(element.get("content", "")) if element else ""


def _meta_name_content(soup: BeautifulSoup, name: str) -> str:
    element = soup.find("meta", attrs={"name": name})
    return str(element.get("content", "")) if element else ""


def _first_paragraph(soup: BeautifulSoup) -> str:
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if len(text) > 60:
            return text
    return ""


def _source_name(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host or "Unknown source"


def _normalize_date(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except Exception:
        match = re.search(r"\d{4}-\d{2}-\d{2}", value)
        return match.group(0) if match else value[:24]


def _clean_text(value: str) -> str:
    text = BeautifulSoup(unescape(value or ""), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
