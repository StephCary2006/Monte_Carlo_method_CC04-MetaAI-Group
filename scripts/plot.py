#!/usr/bin/env python3

"""
Plot benchmark results for one machine.

Usage:
    python3 scripts/plot.py tv4
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
MACHINE = sys.argv[1] if len(sys.argv) > 1 else "tv4"

SUMMARY = ROOT / "results" / MACHINE / "summary.csv"
FIGURES = ROOT / "figures"

FIGURES.mkdir(parents=True, exist_ok=True)

if not SUMMARY.exists():
    raise SystemExit(f"Error: {SUMMARY} does not exist.")

with SUMMARY.open(newline="") as file:
    rows = list(csv.DictReader(file))

if not rows:
    raise SystemExit("Error: summary.csv is empty.")

# Group rows by approach and mutex batch size.
groups = {}

for row in rows:
    approach = row["approach"]
    batch = int(row["batch_size"])
    label = f"{approach}_k{batch}" if approach == "mutex" else approach

    groups.setdefault(label, []).append({
        "threads": int(row["threads"]),
        "time": float(row["mean_time"]),
        "speedup": float(row["speedup"]),
        "efficiency": float(row["efficiency"]),
    })

for values in groups.values():
    values.sort(key=lambda item: item["threads"])


def plot_metric(metric, ylabel, title, filename, ideal=False):
    plt.figure(figsize=(9, 6))

    for label, values in groups.items():
        x = [item["threads"] for item in values]
        y = [item[metric] for item in values]

        plt.plot(x, y, marker="o", label=label)

    if ideal:
        max_threads = max(
            item["threads"]
            for values in groups.values()
            for item in values
        )
        plt.plot(
            [1, max_threads],
            [1, max_threads],
            linestyle="--",
            label="Ideal speedup",
        )

    plt.xlabel("Number of Threads")
    plt.ylabel(ylabel)
    plt.title(f"{title} - {MACHINE}")
    plt.xticks(sorted({
        item["threads"]
        for values in groups.values()
        for item in values
    }))
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = FIGURES / filename
    plt.savefig(output, dpi=300)
    plt.close()

    print(f"Created: {output}")


plot_metric(
    "time",
    "Execution Time (seconds)",
    "Execution Time vs Threads",
    f"{MACHINE}_execution_time.png",
)

plot_metric(
    "speedup",
    "Speedup",
    "Speedup vs Threads",
    f"{MACHINE}_speedup.png",
    ideal=True,
)

plot_metric(
    "efficiency",
    "Parallel Efficiency",
    "Parallel Efficiency vs Threads",
    f"{MACHINE}_efficiency.png",
)

print("Plotting completed.")
