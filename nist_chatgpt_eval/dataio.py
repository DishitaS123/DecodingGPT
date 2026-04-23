from __future__ import annotations

import csv
from pathlib import Path

from nist_chatgpt_eval.criteria import VALID_LABELS


def load_conversations(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"conversation_id", "conversation"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for row in reader:
            rows.append(
                {
                    "conversation_id": row["conversation_id"].strip(),
                    "conversation": row["conversation"].strip(),
                    "manual_label": (row.get("manual_label") or "").strip(),
                }
            )
    return rows


def load_manual_labels(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in load_conversations(path):
        label = row["manual_label"]
        if not label:
            continue
        if label not in VALID_LABELS:
            raise ValueError(f"Invalid manual label for {row['conversation_id']}: {label}")
        labels[row["conversation_id"]] = label
    return labels


def write_results(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "conversation_id",
        "predicted_label",
        "confidence",
        "rationale",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
