from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nist_chatgpt_eval.client import MockLLMClient, PromptOnlyClient
from nist_chatgpt_eval.pipeline import compare_with_manual, run_batch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal starter for manual vs automated NIST-style conversation analysis."
    )
    parser.add_argument("--input", required=True, type=Path, help="CSV of conversations.")
    parser.add_argument("--output", required=True, type=Path, help="Where to save predictions.")
    parser.add_argument(
        "--manual-labels",
        type=Path,
        default=None,
        help="Optional CSV with manual labels for agreement comparison.",
    )
    parser.add_argument(
        "--use-mock",
        action="store_true",
        help="Use the offline heuristic client instead of a real LLM API.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = MockLLMClient() if args.use_mock else PromptOnlyClient()
    predictions = run_batch(args.input, args.output, client)

    print(f"Wrote {len(predictions)} predictions to {args.output}")

    if args.manual_labels:
        summary = compare_with_manual(predictions, args.manual_labels)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
