# DecodingGPT

This repository evaluates ChatGPT security/code advice against a NIST-inspired rubric, then compares automated LLM judgments with prior manual annotations for the same 338 conversations.

## Quick Start

Clone the repo, move into it, and install everything with `uv`:

```bash
git clone https://github.com/DishitaS123/DecodingGPT.git
cd DecodingGPT
uv sync
```

After that, use `uv run` for every command so the synced environment is used automatically.

## Repo Layout

- Writeup source: [main.tex](/Users/dishita/Desktop/LLM/DecodingGPT/main.tex)
- Evaluation package: [nist_chatgpt_eval](/Users/dishita/Desktop/LLM/DecodingGPT/nist_chatgpt_eval)
- Plotting helpers: [Graphing_Results](/Users/dishita/Desktop/LLM/DecodingGPT/Graphing_Results)
- Manual annotations: `data/manual_annotations.csv`
- Prepared 338-conversation dataset: `data/annotated_conversations.csv`
- Baseline heuristic outputs: `data/heuristic_predictions.csv`, `data/evaluation_summary.json`
- Final model outputs used in the report: `Output/DEEPSEEK_V4_FLASH`, `Output/GEMINI_2_5_FLASH`, `Output/GPT_4_1_NANO`
- Cross-model comparison outputs: `Output/analysis/model_comparison`

## Reproduce The Environment

Install dependencies once:

```bash
uv sync
```

Run tests:

```bash
uv run pytest nist_chatgpt_eval/tests/test_pipeline.py
```

## Main Pipeline

Prepare the annotated subset from the large conversation dump:

```bash
uv run python -m nist_chatgpt_eval.main prepare \
  --conversations /absolute/path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --output data/annotated_conversations.csv
```

Run the offline baseline evaluator:

```bash
uv run python -m nist_chatgpt_eval.main analyze \
  --input data/annotated_conversations.csv \
  --output data/heuristic_predictions.csv \
  --use-mock
```

Compute evaluation metrics for one prediction file against the manual labels:

```bash
uv run python -m nist_chatgpt_eval.main evaluate \
  --predictions data/heuristic_predictions.csv \
  --manual data/annotated_conversations.csv \
  --output data/evaluation_summary.json
```

Run the full baseline pipeline in one command:

```bash
uv run python -m nist_chatgpt_eval.main full-run \
  --conversations /absolute/path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --prepared-output data/annotated_conversations.csv \
  --predictions-output data/heuristic_predictions.csv \
  --summary-output data/evaluation_summary.json \
  --use-mock
```

## Compare Manual Results Against The 3 LLMs

All final model outputs are already in `Output`, so you can regenerate the comparison metrics, heatmap, and report examples directly from the saved CSVs:

```bash
uv run python -m nist_chatgpt_eval.main compare-models \
  --manual data/annotated_conversations.csv \
  --discover-root Output \
  --output-dir Output/analysis/model_comparison
```

This command writes:

- `Output/analysis/model_comparison/pairwise_metrics.csv`
- `Output/analysis/model_comparison/manual_vs_models_summary.csv`
- `Output/analysis/model_comparison/basic_stats.csv`
- `Output/analysis/model_comparison/score_correlation_matrix.csv`
- `Output/analysis/model_comparison/score_correlation_heatmap.png`
- `Output/analysis/model_comparison/agreement_examples.md`

## Regenerate Plots From The Generated CSVs

The graphing scripts use each model's saved `predictions.csv` and regenerate plots directly from those CSVs. All three graphing scripts now use only the top 3 categories by default instead of hard-coded category IDs.

From the repo root:

```bash
uv run python Graphing_Results/graphing_categories.py Output/DEEPSEEK_V4_FLASH/deepseek-deepseek-v4-flash/predictions.csv
uv run python Graphing_Results/graphing_sub_score_followed.py Output/DEEPSEEK_V4_FLASH/deepseek-deepseek-v4-flash/predictions.csv
uv run python Graphing_Results/graphing_sub_score_violated.py Output/DEEPSEEK_V4_FLASH/deepseek-deepseek-v4-flash/predictions.csv
uv run python Graphing_Results/graphing_categories.py Output/GPT_4_1_NANO/openai-gpt-4-1-nano/predictions.csv
uv run python Graphing_Results/graphing_sub_score_followed.py Output/GPT_4_1_NANO/openai-gpt-4-1-nano/predictions.csv
uv run python Graphing_Results/graphing_sub_score_violated.py Output/GPT_4_1_NANO/openai-gpt-4-1-nano/predictions.csv
uv run python Graphing_Results/graphing_categories.py Output/GEMINI_2_5_FLASH/google-gemini-2-5-flash/predictions.csv
uv run python Graphing_Results/graphing_sub_score_followed.py Output/GEMINI_2_5_FLASH/google-gemini-2-5-flash/predictions.csv
uv run python Graphing_Results/graphing_sub_score_violated.py Output/GEMINI_2_5_FLASH/google-gemini-2-5-flash/predictions.csv
```

These commands save the PNGs into each model's `graph_data` folder.

## Data Notes

- The raw source conversation dump is not checked into this repository because it is large.
- The prepared 338-row subset used for evaluation is included in `data/annotated_conversations.csv`.
- One manual annotation ID, `ankfvn5z`, does not appear in the raw conversation dump, so 339 annotation rows become 338 matched conversations.

The original larger dataset can be accessed here: https://drive.google.com/drive/folders/1J4k2E4dTOXjolCV2Oq4m_-rJj_--TU24?usp=sharing

## Report Notes

The current report source is in `main.tex`. The generated comparison artifacts most useful for the writeup are:

- `Output/analysis/model_comparison/manual_vs_models_summary.csv`
- `Output/analysis/model_comparison/score_correlation_heatmap.png`
- `Output/analysis/model_comparison/agreement_examples.md`
