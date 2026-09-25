from __future__ import annotations

from math import ceil

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Apply six deterministic corruption scenarios and write an audit log."""
    if df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")

    corrupted = df.copy(deep=True).reset_index(drop=True)
    original_count = len(corrupted)
    drop_count = max(1, ceil(original_count * 0.20))
    published_order = pd.to_datetime(corrupted["published"], errors="coerce", utc=True)
    latest_indices = published_order.nlargest(drop_count).index.tolist()
    dropped_ids = corrupted.loc[latest_indices, "paper_id"].astype(str).tolist()
    corrupted = corrupted.drop(index=latest_indices).reset_index(drop=True)

    def positions(start: int, count: int) -> list[int]:
        if corrupted.empty:
            return []
        return [((start + offset) % len(corrupted)) for offset in range(count)]

    blank_indices = positions(0, min(4, len(corrupted)))
    noise_indices = positions(4, min(4, len(corrupted)))
    truncate_indices = positions(8, min(4, len(corrupted)))
    stale_indices = positions(12, min(7, len(corrupted)))

    blank_ids = corrupted.loc[blank_indices, "paper_id"].astype(str).tolist()
    corrupted.loc[blank_indices, "summary"] = ""

    noise_marker = " ###@@@ CORRUPTED-NOISE 0000 ??? ###@@@"
    noise_ids = corrupted.loc[noise_indices, "paper_id"].astype(str).tolist()
    corrupted.loc[noise_indices, "summary"] = (
        corrupted.loc[noise_indices, "summary"].astype(str) + noise_marker
    )

    truncate_ids = corrupted.loc[truncate_indices, "paper_id"].astype(str).tolist()
    corrupted.loc[truncate_indices, "title"] = corrupted.loc[
        truncate_indices, "title"
    ].astype(str).str.slice(0, 7)

    stale_ids = corrupted.loc[stale_indices, "paper_id"].astype(str).tolist()
    stale_dates = pd.to_datetime(
        corrupted.loc[stale_indices, "published"], errors="coerce"
    ) - pd.DateOffset(years=5)
    corrupted.loc[stale_indices, "published"] = stale_dates.dt.strftime("%Y-%m-%d")

    duplicate_count = min(drop_count, len(corrupted))
    duplicate_source = corrupted.iloc[:duplicate_count].copy(deep=True)
    duplicate_ids = duplicate_source["paper_id"].astype(str).tolist()
    corrupted = pd.concat([corrupted, duplicate_source], ignore_index=True)

    now = pd.Timestamp.now(tz="UTC").normalize()
    published = pd.to_datetime(corrupted["published"], errors="coerce", utc=True)
    corrupted["age_days"] = (now - published.dt.normalize()).dt.days.astype("Int64")
    corrupted["summary_chars"] = corrupted["summary"].fillna("").astype(str).str.len()
    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: "\n".join(
            [
                f"Title: {row['title']}",
                f"Authors: {row['authors_joined']}",
                f"Published: {row['published']}",
                f"Categories: {row['categories_joined']}",
                f"Summary: {row['summary']}",
            ]
        ),
        axis=1,
    )

    log = {
        "original_rows": original_count,
        "corrupted_rows": int(len(corrupted)),
        "scenarios": [
            {
                "name": "drop_latest_records",
                "affected_count": len(dropped_ids),
                "paper_ids": dropped_ids,
                "details": "Dropped the newest 20% of records.",
            },
            {
                "name": "blank_summary",
                "affected_count": len(blank_ids),
                "paper_ids": blank_ids,
                "details": "Replaced summaries with empty strings.",
            },
            {
                "name": "inject_text_noise",
                "affected_count": len(noise_ids),
                "paper_ids": noise_ids,
                "details": f"Appended marker: {noise_marker.strip()}",
            },
            {
                "name": "truncate_title",
                "affected_count": len(truncate_ids),
                "paper_ids": truncate_ids,
                "details": "Truncated titles to seven characters.",
            },
            {
                "name": "stale_date",
                "affected_count": len(stale_ids),
                "paper_ids": stale_ids,
                "details": "Moved publication dates five years into the past.",
            },
            {
                "name": "duplicate_rows",
                "affected_count": len(duplicate_ids),
                "paper_ids": duplicate_ids,
                "details": "Duplicated rows to restore the original row count.",
            },
        ],
    }
    write_json(output_log_path, log)
    return corrupted.reset_index(drop=True)
