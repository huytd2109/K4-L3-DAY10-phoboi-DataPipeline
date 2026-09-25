from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
from great_expectations import expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the required Great Expectations 1.x checks on a dataframe."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "text_for_embedding",
        "age_days",
    }
    missing_columns = sorted(required_columns - set(df.columns))

    expectation_results: list[dict[str, Any]] = []
    if not missing_columns:
        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
        data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
        batch_definition = data_asset.add_batch_definition_whole_dataframe(
            f"papers_batch_{report_name}"
        )
        batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

        expectations = [
            gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
            gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
            gxe.ExpectColumnValuesToNotBeNull(column="title"),
            gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
            gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
            gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
        ]
        for expectation in expectations:
            result = batch.validate(expectation)
            expectation_results.append(result.to_json_dict())

    stale_rows = int((pd.to_numeric(df.get("age_days"), errors="coerce") > settings.freshness_threshold_days).sum()) if "age_days" in df else len(df)
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    is_fresh = stale_ratio <= 0.25
    expectations_success = not missing_columns and all(
        bool(item.get("success")) for item in expectation_results
    )
    payload = {
        "report_name": report_name,
        "success": bool(expectations_success and is_fresh),
        "expectations_success": bool(expectations_success),
        "missing_columns": missing_columns,
        "statistics": {
            "evaluated_expectations": len(expectation_results),
            "successful_expectations": sum(
                1 for item in expectation_results if item.get("success")
            ),
            "unsuccessful_expectations": sum(
                1 for item in expectation_results if not item.get("success")
            ),
            "success_percent": (
                100.0
                * sum(1 for item in expectation_results if item.get("success"))
                / len(expectation_results)
                if expectation_results
                else 0.0
            ),
        },
        "freshness": {
            "threshold_days": settings.freshness_threshold_days,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": stale_ratio,
            "maximum_allowed_stale_ratio": 0.25,
            "is_fresh": is_fresh,
        },
        "results": expectation_results,
    }

    report_path = _quality_report_path(settings, report_name)
    write_json(report_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist the freshness SLA report."""
    published = pd.to_datetime(df.get("published"), errors="coerce", utc=True)
    ages = pd.to_numeric(df.get("age_days"), errors="coerce")
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    valid_published = published.dropna() if published is not None else pd.Series(dtype="datetime64[ns, UTC]")

    payload = {
        "threshold_days": settings.freshness_threshold_days,
        "maximum_allowed_stale_ratio": 0.25,
        "latest_published": (
            valid_published.max().date().isoformat() if not valid_published.empty else None
        ),
        "oldest_published": (
            valid_published.min().date().isoformat() if not valid_published.empty else None
        ),
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "is_fresh": bool(stale_ratio <= 0.25),
    }
    write_json(Path(report_path), payload)
    return payload


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    normalized = report_name.strip().lower()
    if normalized == "baseline":
        return settings.paths.baseline_quality_report
    if normalized == "corrupted":
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / f"{normalized}_quality_report.json"
