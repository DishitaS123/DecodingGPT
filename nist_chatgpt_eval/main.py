from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nist_chatgpt_eval.client import HeuristicSecurityClient, PromptOnlyClient
from nist_chatgpt_eval.dataio import build_annotated_dataset
from nist_chatgpt_eval.model_comparison import (
    discover_prediction_csvs,
    generate_model_comparison_report,
)
from nist_chatgpt_eval.pipeline import compare_with_manual, run_batch, write_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automated security assessment pipeline for developer-ChatGPT conversations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Build the 338-row annotated evaluation dataset.")
    prepare.add_argument("--conversations", required=True, type=Path, help="Raw conversation dump CSV.")
    prepare.add_argument("--annotations", required=True, type=Path, help="Manual annotation CSV.")
    prepare.add_argument("--output", required=True, type=Path, help="Prepared dataset output CSV.")

    analyze = subparsers.add_parser("analyze", help="Run the offline or API-backed evaluator.")
    analyze.add_argument("--input", required=True, type=Path, help="Prepared dataset CSV.")
    analyze.add_argument("--output", required=True, type=Path, help="Prediction CSV.")
    analyze.add_argument("--use-mock", action="store_true", help="Use the offline heuristic evaluator.")

    evaluate = subparsers.add_parser("evaluate", help="Compare predictions against manual labels.")
    evaluate.add_argument("--predictions", required=True, type=Path, help="Prediction CSV.")
    evaluate.add_argument("--manual", required=True, type=Path, help="Prepared dataset CSV.")
    evaluate.add_argument("--output", type=Path, default=None, help="Optional JSON summary output.")

    compare_models = subparsers.add_parser(
        "compare-models",
        help="Generate pairwise metrics, a correlation heatmap, and report-ready examples.",
    )
    compare_models.add_argument("--manual", required=True, type=Path, help="Prepared dataset CSV.")
    compare_models.add_argument(
        "--prediction",
        action="append",
        dest="predictions",
        type=Path,
        help="Prediction CSV to include. Repeat once per model.",
    )
    compare_models.add_argument(
        "--discover-root",
        type=Path,
        default=None,
        help="Optional Output root to auto-discover prediction CSVs when --prediction is omitted.",
    )
    compare_models.add_argument("--output-dir", required=True, type=Path, help="Directory for comparison outputs.")

    full_run = subparsers.add_parser("full-run", help="Prepare data, score it, and compute metrics.")
    full_run.add_argument("--conversations", required=True, type=Path, help="Raw conversation dump CSV.")
    full_run.add_argument("--annotations", required=True, type=Path, help="Manual annotation CSV.")
    full_run.add_argument("--prepared-output", required=True, type=Path, help="Prepared dataset CSV.")
    full_run.add_argument("--predictions-output", required=True, type=Path, help="Prediction CSV.")
    full_run.add_argument("--summary-output", required=True, type=Path, help="Summary JSON.")
    full_run.add_argument("--use-mock", action="store_true", help="Use the offline heuristic evaluator.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "prepare":
        summary = build_annotated_dataset(args.conversations, args.annotations, args.output)
        print(json.dumps(summary, indent=2))
        return

    if args.command == "analyze":
        client = HeuristicSecurityClient() if args.use_mock else PromptOnlyClient()
        predictions = run_batch(args.input, args.output, client)
        print(f"Wrote {len(predictions)} predictions to {args.output}")
        return

    if args.command == "evaluate":
        summary = compare_with_manual(args.predictions, args.manual)
        if args.output:
            write_summary(args.output, summary)
        print(json.dumps(summary, indent=2))
        return

    if args.command == "compare-models":
        prediction_paths = list(args.predictions or [])
        if not prediction_paths:
            if args.discover_root is None:
                raise ValueError("Pass at least one --prediction or provide --discover-root.")
            prediction_paths = discover_prediction_csvs(args.discover_root)
        summary = generate_model_comparison_report(args.manual, prediction_paths, args.output_dir)
        print(json.dumps(summary, indent=2))
        return

    if args.command == "full-run":
        prep_summary = build_annotated_dataset(args.conversations, args.annotations, args.prepared_output)
        client = HeuristicSecurityClient() if args.use_mock else PromptOnlyClient()
        predictions = run_batch(args.prepared_output, args.predictions_output, client)
        summary = compare_with_manual(predictions, args.prepared_output)
        write_summary(args.summary_output, summary)
        print(
            json.dumps(
                {
                    "prepare": prep_summary,
                    "predictions_written": len(predictions),
                    "summary_output": str(args.summary_output),
                    "metrics": summary,
                },
                indent=2,
            )
        )
        return

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
