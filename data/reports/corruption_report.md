# Corruption and Idempotent Repair Report

## Metric comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | 1.0000 | 0.6000 | 1.0000 |
| `mean_token_f1` | 1.0000 | 0.8000 | 1.0000 |
| `judge_accuracy` | 1.0000 | 0.8000 | 1.0000 |
| `mean_judge_score` | 5 | 4.2000 | 5 |

## Quality and freshness comparison

| Signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Quality gate | True | False | True |
| Freshness | True | False | True |
| Stale ratio | 0.0417 | 0.2917 | 0.0417 |

## Interpretation

The corrupted state is produced by six controlled data failures. The repaired state is rebuilt from the immutable raw snapshot, so repeated repair runs are idempotent.

- Corruption changed retrieval hit rate by **-0.4000**.
- Repair recovered retrieval hit rate to **1.0000**.
- Corrupted quality/freshness: **False / False**; repaired quality/freshness: **True / True**.
