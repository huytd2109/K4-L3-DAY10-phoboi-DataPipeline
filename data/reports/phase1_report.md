# Phase 1 — Baseline Data Pipeline Report

## Source and clean dataset

| Field | Value |
|---|---:|
| `source` | Crossref REST API |
| `raw_records` | 24 |
| `clean_records` | 24 |
| `test_samples` | 5 |
| `embedding_model` | sentence-transformers/all-MiniLM-L6-v2 |
| `collection` | papers-baseline |

## Baseline metrics

| Metric | Value |
|---|---:|
| `samples` | 5 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |

## Data quality and freshness

- Great Expectations success: **True**
- Overall quality gate success: **True**
- Successful expectations: **6 / 6**
- Freshness status: **True**
- Stale rows: **1 / 24**
- Stale ratio: **0.0417**
- Publication range: **2026-03-28 → 2026-07-22**

## Conclusion

This report is generated from the pipeline artifacts; no metric was entered manually.
