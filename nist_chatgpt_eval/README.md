# DecodingGPT Evaluation Pipeline

This package implements the final-project experiment described in the writeup:

- prepare the manually annotated 338-conversation subset from the larger Hugging Face dump
- run an automated evaluator over the same conversations
- compare automated predictions against manual labels using report-ready metrics

## Commands

Prepare the annotated subset:

```bash
python3 nist_chatgpt_eval/main.py prepare \
  --conversations /path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --output data/annotated_conversations.csv
```

Run the offline baseline:

```bash
python3 nist_chatgpt_eval/main.py analyze \
  --input data/annotated_conversations.csv \
  --output data/heuristic_predictions.csv \
  --use-mock
```

Compute agreement metrics:

```bash
python3 nist_chatgpt_eval/main.py evaluate \
  --predictions data/heuristic_predictions.csv \
  --manual data/annotated_conversations.csv \
  --output data/evaluation_summary.json
```

Run the whole pipeline in one step:

```bash
python3 nist_chatgpt_eval/main.py full-run \
  --conversations /path/to/conversationDataSet.csv \
  --annotations data/manual_annotations.csv \
  --prepared-output data/annotated_conversations.csv \
  --predictions-output data/heuristic_predictions.csv \
  --summary-output data/evaluation_summary.json \
  --use-mock
```

## Metrics

The evaluator reports:

- exact accuracy on the 5-point human score
- collapsed compliance accuracy on `compliant` / `partially_compliant` / `non_compliant`
- precision, recall, and F1 for the `non_compliant` class
- false positive rate
- Pearson correlation between model confidence and correctness
- Cohen's kappa

## Notes

- The offline client is a heuristic baseline so the project remains runnable without API keys.
- `PromptOnlyClient` is left in place as the integration point for GPT-4, Gemini, or OpenRouter models. Openai-gpt-4-1-nano, deepseek-deepseek-v4-flash, and gemini-2.5-flash were used for the purposes of this study. 
