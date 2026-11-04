#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv", default="tv4",
                        help="Result folder, e.g. tv1 or tv4")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    result_dir = root / "results" / args.tv
    figure_dir = root / "figures" / args.tv

    raw_file = result_dir / "raw.csv"
    figure_dir.mkdir(parents=True, exist_ok=True)

    if not raw_file.exists():
        raise SystemExit(f"Missing file: {raw_file}")

    df = pd.read_csv(raw_file)

    df["execution_time"] = pd.to_numeric(df["execution_time"])
    df["threads"] = pd.to_numeric(df["threads"])
    df["batch_size"] = pd.to_numeric(df["batch_size"])

    # Summary statistics
    keys = ["machine", "approach", "threads", "batch_size"]

    summary = (
        df.groupby(keys, dropna=False)["execution_time"]
        .agg(mean_time="mean", stddev="std", runs="count")
        .reset_index()
    )

    summary["stddev"] = summary["stddev"].fillna(0)

    # Baseline = average single-thread time for each machine
    baseline = (
        summary[summary["approach"] == "single"]
        .groupby("machine")["mean_time"]
        .first()
    )

    summary["speedup"] = summary.apply(
        lambda row: (
            baseline.get(row["machine"], float("nan"))
            / row["mean_time"]
        ),
        axis=1,
    )

    summary["efficiency"] = summary["speedup"] / summary["threads"]

    summary_file = result_dir / "summary.csv"
    summary.to_csv(summary_file, index=False)

    print(f"Saved summary: {summary_file}")

    # 1. Execution time vs threads
    scaling = summary[
        summary["approach"].isin(["local", "mutex"])
    ]

    for approach in scaling["approach"].unique():
        subset = scaling[scaling["approach"] == approach]

        if subset.empty:
            continue

        plt.figure()
        for k, group in subset.groupby("batch_size"):
            label = f"k={int(k)}" if approach == "mutex" else approach
            group = group.sort_values("threads")
            plt.plot(
                group["threads"],
                group["mean_time"],
                marker="o",
                label=label,
            )

        plt.xlabel("Number of threads")
        plt.ylabel("Mean execution time (seconds)")
        plt.title(f"{approach}: Execution time vs threads")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(figure_dir / f"{approach}_time.png", dpi=150)
        plt.close()

    # 2. Speedup
    plt.figure()

    for approach in ["local", "mutex"]:
        subset = summary[summary["approach"] == approach]

        if approach == "mutex":
            subset = subset[subset["batch_size"] == 1]

        subset = subset.sort_values("threads")

        if not subset.empty:
            plt.plot(
                subset["threads"],
                subset["speedup"],
                marker="o",
                label=approach,
            )

    plt.xlabel("Number of threads")
    plt.ylabel("Speedup")
    plt.title("Speedup vs number of threads")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_dir / "speedup.png", dpi=150)
    plt.close()

    # 3. Parallel efficiency
    plt.figure()

    for approach in ["local", "mutex"]:
        subset = summary[summary["approach"] == approach]

        if approach == "mutex":
            subset = subset[subset["batch_size"] == 1]

        subset = subset.sort_values("threads")

        if not subset.empty:
            plt.plot(
                subset["threads"],
                subset["efficiency"],
                marker="o",
                label=approach,
            )

    plt.xlabel("Number of threads")
    plt.ylabel("Parallel efficiency")
    plt.title("Parallel efficiency vs number of threads")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_dir / "efficiency.png", dpi=150)
    plt.close()

    # 4. Mutex batch-size comparison
    mutex = summary[summary["approach"] == "mutex"]

    if not mutex.empty:
        plt.figure()

        for threads, group in mutex.groupby("threads"):
            group = group.sort_values("batch_size")
            plt.plot(
                group["batch_size"],
                group["mean_time"],
                marker="o",
                label=f"{int(threads)} threads",
            )

        plt.xscale("log")
        plt.xlabel("Batch size (k)")
        plt.ylabel("Mean execution time (seconds)")
        plt.title("Mutex performance vs batch size")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(figure_dir / "mutex_batch_size.png", dpi=150)
        plt.close()

    # 5. False sharing comparison
    fs = summary[
        summary["approach"].isin(["fs_packed", "fs_padded"])
    ]

    if not fs.empty:
        plt.figure()

        for approach in ["fs_packed", "fs_padded"]:
            subset = fs[fs["approach"] == approach].sort_values("threads")

            if not subset.empty:
                plt.plot(
                    subset["threads"],
                    subset["mean_time"],
                    marker="o",
                    label=approach,
                )

        plt.xlabel("Number of threads")
        plt.ylabel("Mean execution time (seconds)")
        plt.title("False sharing: packed vs padded")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(figure_dir / "false_sharing.png", dpi=150)
        plt.close()

    print(f"Figures saved in: {figure_dir}")


if __name__ == "__main__":
    main()
