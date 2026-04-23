# NIST ChatGPT Conversation Evaluation Starter

This is a minimal starter for the final project proposed in `LLM Final Proposal.pdf`.

The project goal is to compare:

- a prior manual codebook analysis of developer-ChatGPT conversations
- an automated LLM-based analysis of the same conversations
- agreement between the two approaches on NIST-inspired privacy and security criteria

## What is included

- a small Python package with a simple batch-analysis pipeline
- a NIST-inspired codebook you can edit for your real study
- a mock client so the project runs offline without API access
- sample CSV data so you can test the workflow immediately
- a basic test for loading, scoring, and agreement calculation

## Layout

- `config.py`: runtime configuration
- `criteria.py`: codebook criteria and labels
- `dataio.py`: CSV loading helpers
- `prompting.py`: prompt builder for an external LLM
- `client.py`: mock and pluggable LLM clients
- `pipeline.py`: batch analysis and manual-vs-automated comparison
- `main.py`: CLI entry point
- `data/sample_conversations.csv`: example input data
- `tests/test_pipeline.py`: smoke-level test

## Expected CSV columns

Input conversations:

- `conversation_id`
- `conversation`

Optional manual labels:

- `manual_label`

The label should be one of:

- `compliant`
- `needs_review`
- `non_compliant`

## Run locally

From the repository root:

```bash
cd decoding-gpt
python3 final_proj/nist_chatgpt_eval/main.py \
  --input final_proj/nist_chatgpt_eval/data/sample_conversations.csv \
  --output final_proj/nist_chatgpt_eval/data/sample_results.csv \
  --use-mock
```

To compare against manual labels:

```bash
cd decoding-gpt
python3 final_proj/nist_chatgpt_eval/main.py \
  --input final_proj/nist_chatgpt_eval/data/sample_conversations.csv \
  --output final_proj/nist_chatgpt_eval/data/sample_results.csv \
  --manual-labels final_proj/nist_chatgpt_eval/data/sample_conversations.csv \
  --use-mock
```

Run the test:

```bash
cd decoding-gpt
python3 -m pytest final_proj/nist_chatgpt_eval/tests/test_pipeline.py
```

## Adapting this for the real project

1. Replace `sample_conversations.csv` with the real conversation set.
2. Update the criteria in `criteria.py` so they match your class codebook and NIST mapping exactly.
3. Replace the mock client with a real LLM client in `client.py`.
4. Store the automated outputs and compare them to the 300 manually coded examples.
5. Extend the metrics beyond simple agreement if needed, such as per-label precision/recall or Cohen's kappa.
