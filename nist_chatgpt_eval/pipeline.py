from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

from nist_chatgpt_eval.client import AnalysisResult, BaseLLMClient
from nist_chatgpt_eval.criteria import OVERALL_SCORE_ORDER, VALID_LABELS
from nist_chatgpt_eval.dataio import load_conversations, load_predictions, write_predictions


def run_batch(input_csv: Path, output_csv: Path, client: BaseLLMClient) -> list[dict[str, str]]:
    rows = load_conversations(input_csv)
    results: list[dict[str, str]] = []

    for row in rows:
        analysis: AnalysisResult = client.analyze(
            row["conversation_text"],
            assistant_text=row.get("assistant_text") or row["conversation_text"],
        )
        results.append(
            {
                "id": row["id"],
                "predicted_overall_score": analysis.overall_score,
                "predicted_label": analysis.label,
                "confidence": f"{analysis.confidence:.4f}",
                "risk_hits": ",".join(analysis.risk_hits),
                "safe_hits": ",".join(analysis.safe_hits),
                "rationale": analysis.rationale,
            }
        )

    write_predictions(output_csv, results)
    return results


def compare_with_manual(
    predictions: list[dict[str, str]] | Path,
    manual_labels_csv: Path,
) -> dict[str, object]:
    prediction_rows = load_predictions(predictions) if isinstance(predictions, Path) else predictions
    manual_rows = {row["id"]: row for row in load_conversations(manual_labels_csv)}

    exact_pairs: list[tuple[str, str]] = []
    label_pairs: list[tuple[str, str]] = []
    confidence_pairs: list[tuple[float, float]] = []
    overall_confusion: Counter[tuple[str, str]] = Counter()
    label_confusion: Counter[tuple[str, str]] = Counter()

    for row in prediction_rows:
        manual = manual_rows.get(row["id"])
        if manual is None:
            continue
        predicted_overall = row["predicted_overall_score"]
        manual_overall = manual["overall_score"]
        predicted_label = row["predicted_label"]
        manual_label = manual["manual_label"]

        exact_pairs.append((manual_overall, predicted_overall))
        label_pairs.append((manual_label, predicted_label))
        overall_confusion[(manual_overall, predicted_overall)] += 1
        label_confusion[(manual_label, predicted_label)] += 1
        confidence_pairs.append((float(row["confidence"]), 1.0 if manual_label == predicted_label else 0.0))

    exact_accuracy = _accuracy(exact_pairs)
    label_accuracy = _accuracy(label_pairs)
    precision, recall, f1 = _binary_metrics(label_pairs, positive_label="non_compliant")
    false_positive_rate = _false_positive_rate(label_pairs, positive_label="non_compliant")
    confidence_correlation = _pearson(confidence_pairs)
    kappa = _cohen_kappa(label_pairs, VALID_LABELS)

    summary: dict[str, object] = {
        "compared_examples": len(label_pairs),
        "overall_score_accuracy": exact_accuracy,
        "compliance_accuracy": label_accuracy,
        "non_compliant_precision": precision,
        "non_compliant_recall": recall,
        "non_compliant_f1": f1,
        "false_positive_rate": false_positive_rate,
        "confidence_correctness_pearson": confidence_correlation,
        "cohen_kappa": kappa,
        "overall_score_confusion": _format_confusion(overall_confusion, OVERALL_SCORE_ORDER),
        "compliance_confusion": _format_confusion(label_confusion, VALID_LABELS),
    }
    return summary


def write_summary(path: Path, summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _accuracy(pairs: list[tuple[str, str]]) -> float:
    return sum(1 for expected, observed in pairs if expected == observed) / len(pairs) if pairs else 0.0


def _binary_metrics(
    pairs: list[tuple[str, str]],
    positive_label: str,
) -> tuple[float, float, float]:
    true_positive = sum(1 for expected, observed in pairs if expected == positive_label and observed == positive_label)
    false_positive = sum(1 for expected, observed in pairs if expected != positive_label and observed == positive_label)
    false_negative = sum(1 for expected, observed in pairs if expected == positive_label and observed != positive_label)

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def _false_positive_rate(pairs: list[tuple[str, str]], positive_label: str) -> float:
    negatives = sum(1 for expected, _ in pairs if expected != positive_label)
    false_positives = sum(1 for expected, observed in pairs if expected != positive_label and observed == positive_label)
    return false_positives / negatives if negatives else 0.0


def _pearson(confidence_pairs: list[tuple[float, float]]) -> float:
    if not confidence_pairs:
        return 0.0
    xs = [x for x, _ in confidence_pairs]
    ys = [y for _, y in confidence_pairs]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in confidence_pairs)
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    denominator = denom_x * denom_y
    return numerator / denominator if denominator else 0.0


def _cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> float:
    if not pairs:
        return 0.0
    n = len(pairs)
    observed = _accuracy(pairs)
    expected = 0.0
    expected_counts = Counter(expected for expected, _ in pairs)
    observed_counts = Counter(observed for _, observed in pairs)
    for label in labels:
        expected += (expected_counts[label] / n) * (observed_counts[label] / n)
    return (observed - expected) / (1 - expected) if expected != 1 else 0.0


def _format_confusion(counter: Counter[tuple[str, str]], order: tuple[str, ...]) -> dict[str, int]:
    formatted: dict[str, int] = {}
    for expected in order:
        for observed in order:
            value = counter.get((expected, observed), 0)
            if value:
                formatted[f"{expected} -> {observed}"] = value
    return formatted
