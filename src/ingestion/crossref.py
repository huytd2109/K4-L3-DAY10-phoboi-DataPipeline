from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import date
from html import unescape
from pathlib import Path
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list response into normalized paper records."""

    def clean_markup(value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", unescape(value or ""))
        return normalize_whitespace(without_tags)

    def parse_date(value: object) -> str:
        if isinstance(value, dict):
            date_parts = value.get("date-parts") or []
            if date_parts and date_parts[0]:
                parts = list(date_parts[0])
                year = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 1
                day = int(parts[2]) if len(parts) > 2 else 1
                try:
                    return date(year, month, day).isoformat()
                except ValueError:
                    return ""
            date_time = value.get("date-time")
            if date_time:
                return str(date_time)[:10]
        return ""

    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = normalize_whitespace(str(item.get("DOI", ""))).lower()
        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            raw_title = raw_title[0] if raw_title else ""
        title = clean_markup(str(raw_title))
        if not paper_id or not title:
            continue

        authors: list[str] = []
        for author in item.get("author", []) or []:
            if not isinstance(author, dict):
                continue
            full_name = normalize_whitespace(
                " ".join(str(author.get(key, "")) for key in ("given", "family"))
            )
            if full_name:
                authors.append(full_name)

        categories = [
            normalize_whitespace(str(subject))
            for subject in (item.get("subject", []) or [])
            if normalize_whitespace(str(subject))
        ]
        published = parse_date(item.get("published") or item.get("published-print") or item.get("published-online"))
        updated = parse_date(item.get("indexed") or item.get("created")) or published
        abs_url = normalize_whitespace(str(item.get("URL", ""))) or f"https://doi.org/{paper_id}"

        pdf_url = ""
        for link in item.get("link", []) or []:
            if not isinstance(link, dict):
                continue
            content_type = str(link.get("content-type", "")).lower()
            if "pdf" in content_type:
                pdf_url = normalize_whitespace(str(link.get("URL", "")))
                break
        pdf_url = pdf_url or abs_url

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=clean_markup(str(item.get("abstract", ""))),
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "Uncategorized",
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref data, falling back to the bundled offline snapshot."""
    snapshot_path = settings.paths.raw_api_response
    payload: dict | None = None

    if settings.refresh_source:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        try:
            response = session.get(
                "https://api.crossref.org/works",
                params={
                    "query": settings.source_query,
                    "filter": settings.source_filter,
                    "rows": settings.max_results,
                },
                headers={"User-Agent": "day10-data-observability-lab/0.1"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            write_json(snapshot_path, payload)
        except (requests.RequestException, ValueError):
            payload = None

    if payload is None:
        if not snapshot_path.exists():
            raise RuntimeError(
                "Crossref is unavailable and the offline snapshot does not exist: "
                f"{snapshot_path}"
            )
        payload = read_json(snapshot_path)

    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("Crossref payload did not contain any valid paper records.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load the parsed raw snapshot and validate its record shape."""
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of raw records in {path}.")

    records: list[PaperRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        values = dict(item)
        values["authors"] = list(values.get("authors") or [])
        values["categories"] = list(values.get("categories") or [])
        records.append(PaperRecord(**values))
    return records
