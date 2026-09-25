from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from html import unescape
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw records into the stable schema used by retrieval."""

    def clean_text(value: object) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", unescape(str(value or "")))
        return normalize_whitespace(without_tags)

    if run_date.tzinfo is None:
        run_timestamp = pd.Timestamp(run_date, tz="UTC")
    else:
        run_timestamp = pd.Timestamp(run_date).tz_convert("UTC")

    cleaned_rows: list[dict] = []
    for record in records:
        row = asdict(record) if isinstance(record, PaperRecord) else dict(record)
        paper_id = clean_text(row.get("paper_id")).lower()
        title = clean_text(row.get("title"))
        summary = clean_text(row.get("summary"))
        if not paper_id or not title or not summary:
            continue

        authors = [clean_text(item) for item in row.get("authors", []) if clean_text(item)]
        categories = [clean_text(item) for item in row.get("categories", []) if clean_text(item)]
        published = pd.to_datetime(row.get("published"), errors="coerce", utc=True)
        updated = pd.to_datetime(row.get("updated"), errors="coerce", utc=True)
        if pd.isna(published):
            continue
        if pd.isna(updated):
            updated = published

        published_iso = published.date().isoformat()
        updated_iso = updated.date().isoformat()
        authors_joined = compact_join(authors) or "Unknown"
        categories_joined = compact_join(categories) or "Uncategorized"
        age_days = int((run_timestamp.normalize() - published.normalize()).days)
        text_for_embedding = "\n".join(
            [
                f"Title: {title}",
                f"Authors: {authors_joined}",
                f"Published: {published_iso}",
                f"Categories: {categories_joined}",
                f"Summary: {summary}",
            ]
        )
        cleaned_rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": clean_text(row.get("primary_category"))
                or (categories[0] if categories else "Uncategorized"),
                "published": published_iso,
                "updated": updated_iso,
                "age_days": age_days,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "text_for_embedding": text_for_embedding,
                "abs_url": clean_text(row.get("abs_url")),
                "pdf_url": clean_text(row.get("pdf_url")),
                "comment": clean_text(row.get("comment")),
            }
        )

    columns = [
        "paper_id",
        "title",
        "summary",
        "authors",
        "categories",
        "primary_category",
        "published",
        "updated",
        "age_days",
        "authors_joined",
        "categories_joined",
        "summary_chars",
        "text_for_embedding",
        "abs_url",
        "pdf_url",
        "comment",
    ]
    df = pd.DataFrame(cleaned_rows, columns=columns)
    if df.empty:
        return df
    return (
        df.drop_duplicates(subset=["paper_id"], keep="first")
        .sort_values(["published", "paper_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
