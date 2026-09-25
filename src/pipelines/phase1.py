from __future__ import annotations

from datetime import UTC, datetime

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import load_or_create_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the complete clean-data baseline pipeline."""
    settings = load_settings()
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    clean_df = build_clean_dataframe(records, datetime.now(UTC))
    if clean_df.empty:
        raise RuntimeError("Cleaning produced an empty dataframe.")
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(
        clean_df,
        settings,
        settings.paths.freshness_report,
    )
    if not quality["success"]:
        raise RuntimeError(
            "Baseline data failed the quality gate. Inspect "
            f"{settings.paths.baseline_quality_report}."
        )

    index = LocalEmbeddingIndex.build(
        clean_df,
        settings,
        settings.paths.embeddings_json,
    )
    test_set = load_or_create_test_set(
        clean_df,
        settings.paths.eval_testset,
        refresh=settings.refresh_test_set,
    )
    evaluation = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    source_summary = {
        "source": settings.source_api,
        "raw_records": len(records),
        "clean_records": len(clean_df),
        "test_samples": len(test_set.samples),
        "embedding_model": settings.embedding_model,
        "collection": settings.baseline_collection_name,
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        evaluation.summary,
        quality,
        freshness,
    )
    print(
        "Baseline pipeline complete: "
        f"{len(clean_df)} papers, {len(test_set.samples)} questions, "
        f"hit rate={evaluation.summary['retrieval_hit_rate']:.3f}, "
        f"token F1={evaluation.summary['mean_token_f1']:.3f}."
    )
