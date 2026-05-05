import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot violated subcategories for the top 3 identified categories."
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
        help="Number of top categories to plot.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display plots interactively in addition to saving them.",
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

    top_categories = (
        pd.Series(flatten_categories(df["identified category"]))
        .value_counts()
        .head(args.top_n)
        .index
        .tolist()
    )

    out_dir = output_dir_for(csv_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Top categories for {csv_path.name}: {top_categories}")

    for category in top_categories:
        category_data = df[
            df["identified category"].notna()
            & df["identified category"].astype(str).str.contains(fr"\b{category}\b")
        ]

        flattened_list = []
        for sublist in category_data["violated subcategories"].dropna():
            for item in str(sublist).split(","):
                item = item.strip()
                if not item:
                    continue
                flattened_list.append(item)

        if not flattened_list:
            print(f"No violated subcategories found for category {category}; skipping.")
            continue

        category_counts = pd.Series(flattened_list).value_counts().sort_index()
        x_positions = np.arange(len(category_counts))

        plt.figure(figsize=(10, 6))
        plt.bar(x_positions, category_counts.values, color="#b0c4de", width=0.6)
        plt.title(f"Violated Best Practices - Subcategories (Category {category})")
        plt.xlabel("Violated Subcategories")
        plt.ylabel("Count")
        plt.xticks(
            x_positions,
            [str(subcat) for subcat in category_counts.index],
            rotation=45,
            ha="right",
        )
        plt.tight_layout()

        out_path = out_dir / f"violated_subcategories_category_{category}.png"
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        print(f"Saved {out_path}")

        if args.show:
            plt.show()
        plt.close()


if __name__ == "__main__":
    main()
