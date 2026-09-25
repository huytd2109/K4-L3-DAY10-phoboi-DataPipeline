from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, read_json, write_json


@dataclass(frozen=True)
class TestSetBundle:
    samples: list[dict[str, Any]]


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a deterministic five-question benchmark from clean papers."""
    if len(df) < 5:
        raise ValueError("At least five clean papers are required to build the test set.")

    ordered = df.sort_values(["paper_id"]).reset_index(drop=True)
    selected = [ordered.iloc[index] for index in range(5)]

    def sample(
        sample_id: str,
        question_type: str,
        question: str,
        ground_truth: str,
        doc_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "id": sample_id,
            "type": question_type,
            "question_type": question_type,
            "question": question,
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": doc_ids,
        }

    summary_row, authors_row, date_row, category_row, multi_a = selected
    multi_b = ordered.iloc[5] if len(ordered) > 5 else selected[0]
    samples = [
        sample(
            "eval_001",
            "summary",
            f"What is the summary of the paper '{summary_row['title']}'?",
            first_sentence(str(summary_row["summary"])),
            [str(summary_row["paper_id"])],
        ),
        sample(
            "eval_002",
            "authors",
            f"Who authored the paper '{authors_row['title']}'?",
            str(authors_row["authors_joined"]),
            [str(authors_row["paper_id"])],
        ),
        sample(
            "eval_003",
            "date",
            f"When was the paper '{date_row['title']}' published?",
            str(date_row["published"]),
            [str(date_row["paper_id"])],
        ),
        sample(
            "eval_004",
            "category",
            f"What categories are assigned to the paper '{category_row['title']}'?",
            str(category_row["categories_joined"]),
            [str(category_row["paper_id"])],
        ),
        sample(
            "eval_005",
            "multi_hop",
            (
                "Compare the main findings of "
                f"'{multi_a['title']}' and '{multi_b['title']}'."
            ),
            (
                f"{multi_a['title']}: {first_sentence(str(multi_a['summary']))} "
                f"{multi_b['title']}: {first_sentence(str(multi_b['summary']))}"
            ),
            [str(multi_a["paper_id"]), str(multi_b["paper_id"])],
        ),
    ]
    write_json(Path(output_path), samples)
    return samples


def load_or_create_test_set(
    df: pd.DataFrame,
    output_path,
    refresh: bool = False,
) -> TestSetBundle:
    """Compatibility API for the checkpoint command."""
    path = Path(output_path)
    if path.exists() and not refresh:
        samples = read_json(path)
    else:
        samples = build_test_set(df, path)
    return TestSetBundle(samples=samples)
