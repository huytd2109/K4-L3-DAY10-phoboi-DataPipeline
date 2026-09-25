from __future__ import annotations

from typing import Any

from core.utils import write_text


def _format_metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the baseline pipeline report from generated artifacts."""
    lines = [
        "# Phase 1 — Baseline Data Pipeline Report",
        "",
        "## Source and clean dataset",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {_format_metric(value)} |" for key, value in source_summary.items())
    lines.extend(
        [
            "",
            "## Baseline metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
    )
    for key in (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    ):
        lines.append(f"| `{key}` | {_format_metric(metrics.get(key, 'N/A'))} |")
    lines.extend(
        [
            "",
            "## Data quality and freshness",
            "",
            f"- Great Expectations success: **{quality.get('expectations_success', quality.get('success'))}**",
            f"- Overall quality gate success: **{quality.get('success')}**",
            f"- Successful expectations: **{quality.get('statistics', {}).get('successful_expectations', 0)} / {quality.get('statistics', {}).get('evaluated_expectations', 0)}**",
            f"- Freshness status: **{freshness.get('is_fresh')}**",
            f"- Stale rows: **{freshness.get('stale_rows')} / {freshness.get('total_rows')}**",
            f"- Stale ratio: **{_format_metric(freshness.get('stale_ratio', 0.0))}**",
            f"- Publication range: **{freshness.get('oldest_published')} → {freshness.get('latest_published')}**",
            "",
            "## Conclusion",
            "",
            "This report is generated from the pipeline artifacts; no metric was entered manually.",
        ]
    )
    write_text(report_path, "\n".join(lines) + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
) -> None:
    """Write a three-state baseline/corrupted/repaired comparison."""
    metric_names = (
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    baseline_quality = baseline_quality or {}
    baseline_freshness = baseline_freshness or {}
    lines = [
        "# Corruption and Idempotent Repair Report",
        "",
        "## Metric comparison",
        "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|---|---:|---:|---:|",
    ]
    for metric_name in metric_names:
        lines.append(
            "| `{}` | {} | {} | {} |".format(
                metric_name,
                _format_metric(baseline_metrics.get(metric_name, "N/A")),
                _format_metric(corrupted_metrics.get(metric_name, "N/A")),
                _format_metric(repaired_metrics.get(metric_name, "N/A")),
            )
        )
    lines.extend(
        [
            "",
            "## Quality and freshness comparison",
            "",
            "| Signal | Baseline | Corrupted | Repaired |",
            "|---|---:|---:|---:|",
            f"| Quality gate | {baseline_quality.get('success', 'N/A')} | {corrupted_quality.get('success')} | {repaired_quality.get('success')} |",
            f"| Freshness | {baseline_freshness.get('is_fresh', 'N/A')} | {corrupted_freshness.get('is_fresh')} | {repaired_freshness.get('is_fresh')} |",
            f"| Stale ratio | {_format_metric(baseline_freshness.get('stale_ratio', 'N/A'))} | {_format_metric(corrupted_freshness.get('stale_ratio', 0.0))} | {_format_metric(repaired_freshness.get('stale_ratio', 0.0))} |",
            "",
            "## Interpretation",
            "",
            "The corrupted state is produced by six controlled data failures. The repaired state is rebuilt from the immutable raw snapshot, so repeated repair runs are idempotent.",
            "",
            f"- Corruption changed retrieval hit rate by **{_format_metric(corrupted_metrics.get('retrieval_hit_rate', 0.0) - baseline_metrics.get('retrieval_hit_rate', 0.0))}**.",
            f"- Repair recovered retrieval hit rate to **{_format_metric(repaired_metrics.get('retrieval_hit_rate', 0.0))}**.",
            f"- Corrupted quality/freshness: **{corrupted_quality.get('success')} / {corrupted_freshness.get('is_fresh')}**; repaired quality/freshness: **{repaired_quality.get('success')} / {repaired_freshness.get('is_fresh')}**.",
        ]
    )
    write_text(report_path, "\n".join(lines) + "\n")
