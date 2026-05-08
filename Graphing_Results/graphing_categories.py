import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot the top identified categories from a predictions CSV."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="Best Practices Metrics - Final.csv",
        help="Path to predictions CSV.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Number of top categories to include in the plot.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively in addition to saving it.",
    )
    return parser.parse_args()


def flatten_categories(series):
    flattened = []
    for sublist in series.dropna():
        for item in str(sublist).split(","):
            item = item.strip()
            if not item:
                continue
            try:
                flattened.append(int(float(item)))
            except ValueError:
                print(f"Skipping invalid category value: {item}")
    return flattened


def output_dir_for(csv_path: Path) -> Path:
    if csv_path.name == "predictions.csv":
        return csv_path.parent / "graph_data"
    return csv_path.parent


def main():
    args = parse_args()
    csv_path = Path(args.csv_path).expanduser().resolve()
    df = pd.read_csv(csv_path)

    category_counts = pd.Series(flatten_categories(df["identified category"])).value_counts()
    top_categories = category_counts.head(args.top_n)

    out_dir = output_dir_for(csv_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.bar(top_categories.index.astype(str), top_categories.values, color="#1f77b4")
    plt.xlabel("Codebook Categories")
    plt.ylabel("Count")
    plt.title(f"Top {len(top_categories)} Codebook Categories")
    plt.tight_layout()

    out_path = out_dir / "category_counts_top3.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Top categories for {csv_path.name}: {top_categories.index.tolist()}")
    print(f"Saved {out_path}")

    if args.show:
        plt.show()
    plt.close()


if __name__ == "__main__":
    main()
