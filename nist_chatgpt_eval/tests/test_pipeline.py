from pathlib import Path

from nist_chatgpt_eval.client import MockLLMClient
from nist_chatgpt_eval.pipeline import compare_with_manual, run_batch


def test_run_batch_and_compare(tmp_path: Path) -> None:
    project_dir = Path(__file__).resolve().parent.parent
    input_csv = project_dir / "data" / "sample_conversations.csv"
    output_csv = tmp_path / "results.csv"

    predictions = run_batch(input_csv, output_csv, MockLLMClient())

    assert output_csv.exists()
    assert len(predictions) == 5

    summary = compare_with_manual(predictions, input_csv)
    assert summary["compared_examples"] == 5
    assert 0.0 <= summary["agreement"] <= 1.0
