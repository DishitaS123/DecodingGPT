from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    input_csv: Path
    output_csv: Path
    manual_labels_csv: Path | None = None
    model_name: str = "mock-heuristic"
    use_mock: bool = True
