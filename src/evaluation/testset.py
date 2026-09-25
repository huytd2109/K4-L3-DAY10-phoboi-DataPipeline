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
    """Create the required deterministic ten-question benchmark."""
    if len(df) < 10:
        raise ValueError("At least ten clean papers are required to build the test set.")

    ordered = df.sort_values(["paper_id"]).reset_index(drop=True)
    selected = [ordered.iloc[index] for index in range(10)]

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

    question_types = (
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    )
    samples: list[dict[str, Any]] = []
    for index, (row, question_type) in enumerate(
        zip(selected, question_types, strict=True),
        start=1,
    ):
        title = str(row["title"])
        paper_id = str(row["paper_id"])
        if question_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))
        elif question_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = str(row["authors_joined"])
        elif question_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(row["published"])
        else:
            question = f"What categories are assigned to the paper '{title}'?"
            ground_truth = str(row["categories_joined"])
        samples.append(
            sample(
                f"eval_{index:03d}",
                question_type,
                question,
                ground_truth,
                [paper_id],
            )
        )
    write_json(Path(output_path), samples)
    return samples


def load_or_create_test_set(
    df: pd.DataFrame,
    output_path,
    refresh: bool = False,
) -> TestSetBundle:
    """Compatibility API for the checkpoint command."""
    path = Path(output_path)
    samples = read_json(path) if path.exists() and not refresh else None
    expected_types = {"summary", "authors", "date", "categories"}
    is_valid = (
        isinstance(samples, list)
        and len(samples) == 10
        and {item.get("question_type") for item in samples if isinstance(item, dict)}
        == expected_types
    )
    if not is_valid:
        samples = build_test_set(df, path)
    return TestSetBundle(samples=samples)
