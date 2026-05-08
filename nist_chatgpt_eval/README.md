# DecodingGPT Evaluation Pipeline

This package prepares the manually annotated subset, runs an evaluator, compares predictions against the manual labels, and now also generates cross-model comparison artifacts for the final 3 LLM runs.

## Install

From the repo root:

```bash
uv sync
```

Then run commands with `uv run`.

## Commands

Prepare the annotated subset:

```bash
uv run python -m nist_chatgpt_eval.main prepare \
  --conversations /path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --output data/annotated_conversations.csv
```

Run the offline baseline:

```bash
uv run python -m nist_chatgpt_eval.main analyze \
  --input data/annotated_conversations.csv \
  --output data/heuristic_predictions.csv \
  --use-mock
```

Compute agreement metrics for one model:

```bash
uv run python -m nist_chatgpt_eval.main evaluate \
  --predictions data/heuristic_predictions.csv \
  --manual data/annotated_conversations.csv \
  --output data/evaluation_summary.json
```

Run the whole baseline pipeline:

```bash
uv run python -m nist_chatgpt_eval.main full-run \
  --conversations /path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --prepared-output data/annotated_conversations.csv \
  --predictions-output data/heuristic_predictions.csv \
  --summary-output data/evaluation_summary.json \
  --use-mock
```

Generate the manual-vs-LLM comparison bundle from the saved `Output` results:

```bash
uv run python -m nist_chatgpt_eval.main compare-models \
  --manual data/annotated_conversations.csv \
  --discover-root Output \
  --output-dir Output/analysis/model_comparison
```

## Outputs From `compare-models`

- `pairwise_metrics.csv`: pairwise agreement, kappa, and score correlations for manual + each LLM
- `manual_vs_models_summary.csv`: the main manual-vs-model metrics table
- `basic_stats.csv`: mean score, score spread, and label counts for each source
- `score_correlation_matrix.csv`: 4x4 score correlation matrix
- `score_correlation_heatmap.png`: figure-ready heatmap
- `agreement_examples.md`: report-ready agreement/disagreement examples

## Models Used In The Final Comparison

- `deepseek/deepseek-v4-flash`
- `google/gemini-2.5-flash`
- `openai/gpt-4.1-nano`
