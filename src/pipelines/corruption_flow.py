from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import main as run_phase1
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run controlled corruption, evaluation, idempotent repair, and comparison."""
    settings = load_settings()
    required_baseline = (
        settings.paths.clean_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
    )
    if any(not path.exists() for path in required_baseline):
        run_phase1()

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality = read_json(settings.paths.baseline_quality_report)
    baseline_freshness = read_json(settings.paths.freshness_report)
    clean_df = pd.read_json(settings.paths.clean_json)
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(
        settings.paths.corrupted_clean_json,
        corrupted_df.to_dict(orient="records"),
    )

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        corrupted_freshness_path,
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        settings.paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )

    repaired_df = build_clean_dataframe(
        load_raw_records(settings.paths.raw_records_json),
        datetime.now(UTC),
    )
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(
        settings.paths.repaired_clean_json,
        repaired_df.to_dict(orient="records"),
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        repaired_freshness_path,
    )
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        settings.paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )

    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    print("Corruption and repair pipeline complete.")
    print(
        "Retrieval hit rate — "
        f"baseline: {baseline_metrics['retrieval_hit_rate']:.3f}, "
        f"corrupted: {corrupted_evaluation.summary['retrieval_hit_rate']:.3f}, "
        f"repaired: {repaired_evaluation.summary['retrieval_hit_rate']:.3f}."
    )
