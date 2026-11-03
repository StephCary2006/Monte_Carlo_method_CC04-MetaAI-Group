#!/usr/bin/env python3

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    output_dir = results_dir / "compare"
    figure_dir = root / "figures" / "compare"

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    frames = []

    for tv in ["tv1", "tv2", "tv3", "tv4", "tv5"]:
        file = results_dir / tv / "raw.csv"

        if not file.exists():
            print(f"[SKIP] {file} not found")
            continue

        df = pd.read_csv(file)
        df["tv"] = tv
        frames.append(df)

    if not frames:
        raise SystemExit("No raw.csv files found.")

    combined = pd.concat(frames, ignore_index=True)

    combined["execution_time"] = pd.to_numeric(
        combined["execution_time"], errors="coerce"
    )
    combined["threads"] = pd.to_numeric(
        combined["threads"], errors="coerce"
    )
    combined["batch_size"] = pd.to_numeric(
        combined["batch_size"], errors="coerce"
    )

    combined.to_csv(output_dir / "all_results.csv", index=False)

    summary = (
        combined.groupby(
            ["tv", "machine", "approach", "threads", "batch_size"],
            dropna=False,
        )["execution_time"]
        .agg(mean_time="mean", stddev="std", runs="count")
        .reset_index()
    )

    summary["stddev"] = summary["stddev"].fillna(0)
    summary.to_csv(output_dir / "summary.csv", index=False)

    # Compare local accumulation across machines
    local = summary[summary["approach"] == "local"]

    if not local.empty:
        plt.figure()

        for machine, group in local.groupby("machine"):
            group = group.sort_values("threads")
            plt.plot(
                group["threads"],
                group["mean_time"],
                marker="o",
                label=machine,
            )

        plt.xlabel("Number of threads")
        plt.ylabel("Mean execution time (seconds)")
        plt.title("Local accumulation: machine comparison")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(figure_dir / "machine_local_comparison.png", dpi=150)
        plt.close()

    # Compare mutex with k=1 across machines
    mutex = summary[
        (summary["approach"] == "mutex")
        & (summary["batch_size"] == 1)
    ]

    if not mutex.empty:
        plt.figure()

        for machine, group in mutex.groupby("machine"):
            group = group.sort_values("threads")
            plt.plot(
                group["threads"],
                group["mean_time"],
                marker="o",
                label=machine,
            )

        plt.xlabel("Number of threads")
        plt.ylabel("Mean execution time (seconds)")
        plt.title("Mutex (k=1): machine comparison")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(figure_dir / "machine_mutex_comparison.png", dpi=150)
        plt.close()

    print(f"Combined data: {output_dir / 'all_results.csv'}")
    print(f"Summary: {output_dir / 'summary.csv'}")
    print(f"Figures: {figure_dir}")


if __name__ == "__main__":
    main()
