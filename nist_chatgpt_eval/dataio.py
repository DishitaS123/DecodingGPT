from __future__ import annotations

import csv
import html
import re
from pathlib import Path

from nist_chatgpt_eval.criteria import OVERALL_SCORE_ORDER, VALID_LABELS

csv.field_size_limit(1024 * 1024 * 1024)

ANNOTATION_FIELDNAMES = (
    "id",
    "overall score( very bad, bad, ok, good, very good)",
    "identified category",
    "followed subcategories",
    "violated subcategories",
)


def normalize_overall_score(value: str) -> str:
    normalized = value.strip().lower().replace("  ", " ")
    if normalized == "okay":
        return "ok"
    return normalized


def overall_score_to_label(score: str) -> str:
    normalized = normalize_overall_score(score)
    if normalized not in OVERALL_SCORE_ORDER:
        raise ValueError(f"Invalid overall score: {score}")
    if normalized in {"good", "very good"}:
        return "compliant"
    if normalized == "ok":
        return "partially_compliant"
    return "non_compliant"


def clean_transcript_text(text: str) -> str:
    cleaned = html.unescape(text)
    cleaned = cleaned.replace("\\n", "\n").replace("\\t", "\t")
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" '\"[],")


def split_transcript(raw_text: str) -> list[dict[str, str]]:
    role_pattern = re.compile(r"""['"](?:from|From)['"]\s*:\s*['"]([^'"]+)['"]""")
    value_pattern = re.compile(r"""['"](?:value|Value)['"]\s*:\s*""")
    matches = list(role_pattern.finditer(raw_text))
    if not matches:
        return [{"role": "unknown", "text": clean_transcript_text(raw_text)}]

    turns: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        role = match.group(1).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        chunk = raw_text[start:end]
        value_match = value_pattern.search(chunk)
        if value_match:
            chunk = chunk[value_match.end() :]
        turns.append({"role": role, "text": clean_transcript_text(chunk)})
    return turns


def summarize_transcript(raw_text: str) -> dict[str, str]:
    turns = split_transcript(raw_text)
    user_chunks: list[str] = []
    assistant_chunks: list[str] = []
    all_chunks: list[str] = []

    for turn in turns:
        text = turn["text"]
        if not text:
            continue
        all_chunks.append(text)
        role = turn["role"]
        if role in {"human", "user"}:
            user_chunks.append(text)
        elif role in {"gpt", "assistant", "chatgpt"}:
            assistant_chunks.append(text)

    full_text = " ".join(all_chunks).strip() or clean_transcript_text(raw_text)
    user_text = " ".join(user_chunks).strip()
    assistant_text = " ".join(assistant_chunks).strip()
    return {
        "conversation_text": full_text,
        "user_text": user_text,
        "assistant_text": assistant_text or full_text,
    }


def load_conversations(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "conversation_raw", "conversation_text", "assistant_text", "manual_label"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        for row in reader:
            rows.append({key: (row.get(key) or "").strip() for key in reader.fieldnames or []})
    return rows


def load_manual_labels(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in load_conversations(path):
        label = row["manual_label"]
        if label not in VALID_LABELS:
            raise ValueError(f"Invalid manual label for {row['id']}: {label}")
        labels[row["id"]] = label
    return labels


def load_annotations(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(ANNOTATION_FIELDNAMES).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required annotation columns: {sorted(missing)}")
        for row in reader:
            score = normalize_overall_score(row["overall score( very bad, bad, ok, good, very good)"])
            rows.append(
                {
                    "id": row["id"].strip(),
                    "overall_score": score,
                    "manual_label": overall_score_to_label(score),
                    "identified_category": (row["identified category"] or "").strip(),
                    "followed_subcategories": (row["followed subcategories"] or "").strip(),
                    "violated_subcategories": (row["violated subcategories"] or "").strip(),
                }
            )
    return rows


def build_annotated_dataset(
    conversations_csv: Path,
    annotations_csv: Path,
    output_csv: Path,
) -> dict[str, int]:
    annotations = load_annotations(annotations_csv)
    wanted_ids = {row["id"] for row in annotations}
    matched_conversations: dict[str, dict[str, str]] = {}

    with conversations_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"first_col", "vectorized_col_1"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required conversation columns: {sorted(missing)}")

        for row in reader:
            conversation_id = (row.get("first_col") or "").strip()
            if conversation_id not in wanted_ids:
                continue
            transcript = summarize_transcript((row.get("vectorized_col_1") or "").strip())
            matched_conversations[conversation_id] = {
                "id": conversation_id,
                "conversation_raw": (row.get("vectorized_col_1") or "").strip(),
                **transcript,
            }

    output_rows: list[dict[str, str]] = []
    missing_ids: list[str] = []
    for annotation in annotations:
        conversation = matched_conversations.get(annotation["id"])
        if conversation is None:
            missing_ids.append(annotation["id"])
            continue
        output_rows.append({**conversation, **annotation})

    write_prepared_dataset(output_csv, output_rows)
    return {
        "requested_annotations": len(annotations),
        "matched_conversations": len(output_rows),
        "missing_conversations": len(missing_ids),
    }


def write_prepared_dataset(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "id",
        "conversation_raw",
        "conversation_text",
        "user_text",
        "assistant_text",
        "overall_score",
        "manual_label",
        "identified_category",
        "followed_subcategories",
        "violated_subcategories",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_predictions(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "id",
        "predicted_overall_score",
        "predicted_label",
        "confidence",
        "risk_hits",
        "safe_hits",
        "rationale",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_predictions(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "predicted_overall_score", "predicted_label", "confidence"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required prediction columns: {sorted(missing)}")
        for row in reader:
            rows.append({key: (row.get(key) or "").strip() for key in reader.fieldnames or []})
    return rows
