from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import combinations
import math
from pathlib import Path
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MANUAL_SCORE_COLUMN = "overall_score"
MODEL_SCORE_COLUMN = "overall score( very bad, bad, ok, good, very good)"
MODEL_LABEL_COLUMN = "predicted_label"

SCORE_TO_INT = {
    "very bad": 1,
    "bad": 2,
    "ok": 3,
    "good": 4,
    "very good": 5,
}

LABEL_ORDER = ("compliant", "partially_compliant", "non_compliant")


@dataclass(frozen=True)
class SourceRecord:
    name: str
    scores: dict[str, str]
    labels: dict[str, str]


def generate_model_comparison_report(
    manual_csv: Path,
    prediction_paths: list[Path],
    output_dir: Path,
) -> dict[str, object]:
    manual_rows = _read_csv(manual_csv)
    manual_scores = {row["id"]: _normalize_score(row[MANUAL_SCORE_COLUMN]) for row in manual_rows}
    manual_labels = {row["id"]: _normalize_label(row["manual_label"]) for row in manual_rows}
    assistant_text = {row["id"]: (row.get("assistant_text") or "").strip() for row in manual_rows}
    conversation_text = {row["id"]: (row.get("conversation_text") or "").strip() for row in manual_rows}

    sources = [SourceRecord("Manual", manual_scores, manual_labels)]
    for path in prediction_paths:
        rows = _read_csv(path)
        if not rows:
            continue
        name = _display_model_name(rows[0], path)
        score_column = _prediction_score_column(rows[0])
        label_column = _prediction_label_column(rows[0])
        sources.append(
            SourceRecord(
                name=name,
                scores={row["id"]: _normalize_score(row[score_column]) for row in rows},
                labels={row["id"]: _normalize_label(row[label_column]) for row in rows},
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    pairwise_rows = _pairwise_rows(sources)
    _write_csv(
        output_dir / "pairwise_metrics.csv",
        [
            "source_a",
            "source_b",
            "shared_examples",
            "label_agreement",
            "cohen_kappa",
            "pearson_score_correlation",
            "spearman_score_correlation",
        ],
        pairwise_rows,
    )

    basic_stats_rows = _basic_stats_rows(sources)
    _write_csv(
        output_dir / "basic_stats.csv",
        [
            "source",
            "n_examples",
            "mean_score",
            "std_score",
            "compliant_count",
            "partially_compliant_count",
            "non_compliant_count",
        ],
        basic_stats_rows,
    )

    manual_summary_rows = _manual_summary_rows(sources)
    _write_csv(
        output_dir / "manual_vs_models_summary.csv",
        [
            "model",
            "shared_examples",
            "label_agreement",
            "cohen_kappa",
            "pearson_score_correlation",
            "spearman_score_correlation",
        ],
        manual_summary_rows,
    )

    correlation_matrix = _score_correlation_matrix(sources, method="pearson")
    _write_matrix_csv(output_dir / "score_correlation_matrix.csv", sources, correlation_matrix)
    _plot_heatmap(output_dir / "score_correlation_heatmap.png", sources, correlation_matrix)

    examples = _select_examples(sources, assistant_text, conversation_text)
    examples_path = output_dir / "agreement_examples.md"
    examples_path.write_text(_format_examples_markdown(examples), encoding="utf-8")

    return {
        "sources": [source.name for source in sources],
        "pairwise_metrics_csv": str(output_dir / "pairwise_metrics.csv"),
        "basic_stats_csv": str(output_dir / "basic_stats.csv"),
        "manual_vs_models_csv": str(output_dir / "manual_vs_models_summary.csv"),
        "score_correlation_csv": str(output_dir / "score_correlation_matrix.csv"),
        "score_correlation_heatmap": str(output_dir / "score_correlation_heatmap.png"),
        "examples_markdown": str(examples_path),
    }


def discover_prediction_csvs(output_root: Path) -> list[Path]:
    candidates = sorted(output_root.glob("*/*/predictions.csv"))
    filtered: list[Path] = []
    for path in candidates:
        lowered = str(path).lower()
        if "/manual/" in lowered or "/mock/" in lowered or "openrouter_free" in lowered:
            continue
        filtered.append(path)
    return filtered


def _pairwise_rows(sources: list[SourceRecord]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source_a, source_b in combinations(sources, 2):
        shared_ids = sorted(set(source_a.scores) & set(source_b.scores))
        score_pairs = [(source_a.scores[row_id], source_b.scores[row_id]) for row_id in shared_ids]
        label_pairs = [(source_a.labels[row_id], source_b.labels[row_id]) for row_id in shared_ids]
        score_int_pairs = [(SCORE_TO_INT[a], SCORE_TO_INT[b]) for a, b in score_pairs]
        rows.append(
            {
                "source_a": source_a.name,
                "source_b": source_b.name,
                "shared_examples": len(shared_ids),
                "label_agreement": _accuracy(label_pairs),
                "cohen_kappa": _cohen_kappa(label_pairs, LABEL_ORDER),
                "pearson_score_correlation": _pearson(score_int_pairs),
                "spearman_score_correlation": _spearman(score_int_pairs),
            }
        )
    return rows


def _basic_stats_rows(sources: list[SourceRecord]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in sources:
        values = [SCORE_TO_INT[score] for score in source.scores.values()]
        label_counts = {label: 0 for label in LABEL_ORDER}
        for label in source.labels.values():
            label_counts[label] += 1
        rows.append(
            {
                "source": source.name,
                "n_examples": len(values),
                "mean_score": round(statistics.mean(values), 4) if values else 0.0,
                "std_score": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
                "compliant_count": label_counts["compliant"],
                "partially_compliant_count": label_counts["partially_compliant"],
                "non_compliant_count": label_counts["non_compliant"],
            }
        )
    return rows


def _manual_summary_rows(sources: list[SourceRecord]) -> list[dict[str, object]]:
    manual = sources[0]
    rows: list[dict[str, object]] = []
    for source in sources[1:]:
        shared_ids = sorted(set(manual.scores) & set(source.scores))
        label_pairs = [(manual.labels[row_id], source.labels[row_id]) for row_id in shared_ids]
        score_pairs = [(SCORE_TO_INT[manual.scores[row_id]], SCORE_TO_INT[source.scores[row_id]]) for row_id in shared_ids]
        rows.append(
            {
                "model": source.name,
                "shared_examples": len(shared_ids),
                "label_agreement": _accuracy(label_pairs),
                "cohen_kappa": _cohen_kappa(label_pairs, LABEL_ORDER),
                "pearson_score_correlation": _pearson(score_pairs),
                "spearman_score_correlation": _spearman(score_pairs),
            }
        )
    return rows


def _score_correlation_matrix(sources: list[SourceRecord], method: str) -> list[list[float]]:
    matrix: list[list[float]] = []
    for source_a in sources:
        row: list[float] = []
        for source_b in sources:
            shared_ids = sorted(set(source_a.scores) & set(source_b.scores))
            pairs = [(SCORE_TO_INT[source_a.scores[row_id]], SCORE_TO_INT[source_b.scores[row_id]]) for row_id in shared_ids]
            if method == "pearson":
                row.append(_pearson(pairs))
            else:
                row.append(_spearman(pairs))
        matrix.append(row)
    return matrix


def _plot_heatmap(path: Path, sources: list[SourceRecord], matrix: list[list[float]]) -> None:
    labels = [source.name for source in sources]
    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(matrix, cmap="Blues", vmin=-1, vmax=1)
    ax.set_xticks(range(len(labels)), labels=labels, rotation=30, ha="right")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_title("Overall Score Correlation Heatmap")

    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="black")

    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _write_matrix_csv(path: Path, sources: list[SourceRecord], matrix: list[list[float]]) -> None:
    header = ["source"] + [source.name for source in sources]
    rows = []
    for source, values in zip(sources, matrix):
        row = {"source": source.name}
        for target, value in zip(sources, values):
            row[target.name] = round(value, 6)
        rows.append(row)
    _write_csv(path, header, rows)


def _select_examples(
    sources: list[SourceRecord],
    assistant_text: dict[str, str],
    conversation_text: dict[str, str],
) -> list[dict[str, object]]:
    manual = sources[0]
    models = sources[1:]
    shared_ids = sorted(set(manual.labels).intersection(*(set(model.labels) for model in models)))
    rows = []
    for row_id in shared_ids:
        labels = {source.name: source.labels[row_id] for source in sources}
        scores = {source.name: source.scores[row_id] for source in sources}
        model_matches = sum(1 for model in models if model.labels[row_id] == manual.labels[row_id])
        unique_labels = len({model.labels[row_id] for model in models})
        rows.append(
            {
                "id": row_id,
                "labels": labels,
                "scores": scores,
                "assistant_excerpt": _excerpt(assistant_text.get(row_id) or conversation_text.get(row_id) or ""),
                "model_matches_manual": model_matches,
                "all_agree": all(model.labels[row_id] == manual.labels[row_id] for model in models),
                "models_split_count": unique_labels,
            }
        )

    used_ids: set[str] = set()
    examples: list[dict[str, object]] = []
    examples.extend(
        _pick_by_condition(rows, lambda row: row["all_agree"] and row["labels"]["Manual"] == "compliant", 1, used_ids)
    )
    examples.extend(
        _pick_by_condition(rows, lambda row: row["all_agree"] and row["labels"]["Manual"] == "non_compliant", 1, used_ids)
    )
    examples.extend(
        _pick_by_condition(rows, lambda row: (not row["all_agree"]) and row["model_matches_manual"] == 2, 1, used_ids)
    )
    examples.extend(
        _pick_by_condition(rows, lambda row: (not row["all_agree"]) and row["model_matches_manual"] == 1, 1, used_ids)
    )
    examples.extend(
        _pick_by_condition(
            rows,
            lambda row: row["models_split_count"] >= 3 or row["model_matches_manual"] == 0,
            1,
            used_ids,
        )
    )
    return examples


def _pick_by_condition(
    rows: list[dict[str, object]],
    predicate,
    count: int,
    used_ids: set[str],
) -> list[dict[str, object]]:
    picked: list[dict[str, object]] = []
    for row in sorted(rows, key=_example_sort_key):
        if not predicate(row):
            continue
        if row["id"] in used_ids:
            continue
        picked.append(row)
        used_ids.add(row["id"])
        if len(picked) >= count:
            break
    return picked


def _format_examples_markdown(examples: list[dict[str, object]]) -> str:
    lines = ["# Agreement and Disagreement Examples", ""]
    for index, example in enumerate(examples, start=1):
        lines.append(f"## Example {index}: `{example['id']}`")
        lines.append("")
        lines.append(f"Assistant excerpt: {example['assistant_excerpt']}")
        lines.append("")
        lines.append("| Source | Overall score | Label |")
        lines.append("| --- | --- | --- |")
        for source in example["scores"]:
            lines.append(
                f"| {source} | {example['scores'][source]} | {example['labels'][source]} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _normalize_score(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "okay":
        return "ok"
    return normalized


def _normalize_label(value: str) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "needs_review":
        return "partially_compliant"
    return normalized


def _prediction_score_column(row: dict[str, str]) -> str:
    if MODEL_SCORE_COLUMN in row:
        return MODEL_SCORE_COLUMN
    for key in row:
        if key.strip().lower().startswith("overall score"):
            return key
    raise KeyError("Could not find prediction overall score column.")


def _prediction_label_column(row: dict[str, str]) -> str:
    if MODEL_LABEL_COLUMN in row:
        return MODEL_LABEL_COLUMN
    for key in row:
        if key.strip().lower() == "predicted_label":
            return key
    raise KeyError("Could not find prediction label column.")


def _display_model_name(row: dict[str, str], path: Path) -> str:
    model_name = (row.get("model_name") or "").strip()
    if model_name:
        if model_name == "openai/gpt-4.1-nano":
            return "GPT-4.1-nano"
        if model_name == "deepseek/deepseek-v4-flash":
            return "DeepSeek-V4-Flash"
        if model_name == "google/gemini-2.5-flash":
            return "Gemini-2.5-Flash"
        return model_name
    return path.parent.name


def _excerpt(text: str, limit: int = 320) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _example_sort_key(row: dict[str, object]) -> tuple[int, int, str]:
    excerpt = str(row["assistant_excerpt"]).lower()
    keywords = (
        "password",
        "hash",
        "salt",
        "ssl",
        "tls",
        "api key",
        "parameterized",
        "prepared statement",
        "encrypt",
        "secret",
    )
    keyword_score = sum(1 for keyword in keywords if keyword in excerpt)
    return (-keyword_score, len(excerpt), str(row["id"]))


def _accuracy(pairs: list[tuple[str, str]]) -> float:
    return sum(1 for left, right in pairs if left == right) / len(pairs) if pairs else 0.0


def _cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> float:
    if not pairs:
        return 0.0
    observed = _accuracy(pairs)
    total = len(pairs)
    expected = 0.0
    for label in labels:
        p_left = sum(1 for left, _ in pairs if left == label) / total
        p_right = sum(1 for _, right in pairs if right == label) / total
        expected += p_left * p_right
    return (observed - expected) / (1 - expected) if expected != 1 else 0.0


def _pearson(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    xs = [left for left, _ in pairs]
    ys = [right for _, right in pairs]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    denominator = denom_x * denom_y
    return numerator / denominator if denominator else 0.0


def _spearman(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    xs = [left for left, _ in pairs]
    ys = [right for _, right in pairs]
    ranked_x = _average_ranks(xs)
    ranked_y = _average_ranks(ys)
    return _pearson(list(zip(ranked_x, ranked_y)))


def _average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position
        while end < len(indexed) and indexed[end][1] == indexed[position][1]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for idx in range(position, end):
            original_index = indexed[idx][0]
            ranks[original_index] = average_rank
        position = end
    return ranks
