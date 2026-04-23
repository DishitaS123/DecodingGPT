from __future__ import annotations

from collections import Counter
from pathlib import Path

from nist_chatgpt_eval.client import AnalysisResult, BaseLLMClient
from nist_chatgpt_eval.dataio import load_conversations, load_manual_labels, write_results


def run_batch(input_csv: Path, output_csv: Path, client: BaseLLMClient) -> list[dict[str, str]]:
    rows = load_conversations(input_csv)
    results: list[dict[str, str]] = []

    for row in rows:
        analysis: AnalysisResult = client.analyze(row["conversation"])
        results.append(
            {
                "conversation_id": row["conversation_id"],
                "predicted_label": analysis.label,
                "confidence": f"{analysis.confidence:.2f}",
                "rationale": analysis.rationale,
            }
        )

    write_results(output_csv, results)
    return results


def compare_with_manual(
    predictions: list[dict[str, str]],
    manual_labels_csv: Path,
) -> dict[str, float | int | dict[str, int]]:
    manual = load_manual_labels(manual_labels_csv)
    matched = 0
    compared = 0
    confusion: Counter[tuple[str, str]] = Counter()

    for row in predictions:
        conversation_id = row["conversation_id"]
        predicted = row["predicted_label"]
        manual_label = manual.get(conversation_id)
        if manual_label is None:
            continue
        compared += 1
        if predicted == manual_label:
            matched += 1
        confusion[(manual_label, predicted)] += 1

    agreement = matched / compared if compared else 0.0
    confusion_table = {
        f"{manual_label} -> {predicted_label}": count
        for (manual_label, predicted_label), count in sorted(confusion.items())
    }
    return {
        "compared_examples": compared,
        "matched_examples": matched,
        "agreement": agreement,
        "confusion": confusion_table,
    }
