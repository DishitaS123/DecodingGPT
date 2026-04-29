# DecodingGPT

This repository contains the final project for evaluating ChatGPT code/security advice against a NIST-inspired rubric, then comparing automated assessments to prior human annotations.

## Where everything is

- Writeup source: [main.tex](/Users/dishita/Desktop/LLM/DecodingGPT/main.tex)
- Evaluation code: [nist_chatgpt_eval](/Users/dishita/Desktop/LLM/DecodingGPT/nist_chatgpt_eval)
- Manual annotations used for comparison: `data/manual_annotations.csv`
- Prepared 338-conversation evaluation set: `data/annotated_conversations.csv`
- Automated baseline predictions: `data/heuristic_predictions.csv`
- Metrics summary: `data/evaluation_summary.json`

## What the code does

The pipeline supports three steps:

1. Build the annotated evaluation set by joining the 338 manually labeled IDs with the original large conversation dump.
2. Run an automated evaluator. The repository currently includes an offline heuristic baseline and a prompt stub for plugging in GPT-4, Claude, or OpenRouter models.
3. Compare automated outputs against manual labels using accuracy, precision/recall/F1 for non-compliance, false positive rate, confidence/correctness correlation, and Cohen's kappa.

## Run it

From the repo root:

```bash
python3 -m pytest nist_chatgpt_eval/tests/test_pipeline.py
```

To rerun the full baseline experiment:

```bash
python3 nist_chatgpt_eval/main.py full-run \
  --conversations /absolute/path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --prepared-output data/annotated_conversations.csv \
  --predictions-output data/heuristic_predictions.csv \
  --summary-output data/evaluation_summary.json \
  --use-mock
```

## Data note

The original `conversationDataSet.csv` is about 728 MB, so it is not copied into this repo. The smaller 338-row prepared subset used in the writeup is included here so the evaluation can be rerun without the full raw dump.

One manual annotation ID, `ankfvn5z`, does not appear in the raw conversation dump, so the prepared dataset contains 338 matched conversations rather than 339 annotation rows.
