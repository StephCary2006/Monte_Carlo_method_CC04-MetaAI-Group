
#!/usr/bin/env python3

"""
Compare benchmark results from five machines.

Usage:
    python3 scripts/compare.py
"""

import csv
import re
import statistics
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
COMPARE = RESULTS / "compare"
FIGURES = ROOT / "figures"

COMPARE.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

MACHINES = [f"tv{i}" for i in range(1, 6)]

all_rows = []
machine_rows = []


def read_machine_info(path):
    info = {
        "cpu_model": "Unknown",
        "physical_cores": "",
        "logical_cores": "",
        "os": "Unknown",
    }

    if not path.exists():
        return info

    content = path.read_text(errors="replace")

    for line in content.splitlines():
        if line.startswith("Model name:"):
            info["cpu_model"] = line.split(":", 1)[1].strip()
        elif line.startswith("CPU(s):"):
            info["logical_cores"] = line.split(":", 1)[1].strip()
        elif line.startswith("Operating System:"):
            info["os"] = line.split(":", 1)[1].strip()

    # Use unique CORE,SOCKET pairs from lscpu output if available.
    match = re.search(
        r"^CPU\(s\):\s*(\d+)",
        content,
        re.MULTILINE,
    )

    if match and not info["logical_cores"]:
        info["logical_cores"] = match.group(1)

    # Count physical cores from Core(s) per socket * Socket(s).
    cores = re.search(r"^Core\(s\) per socket:\s*(\d+)", content, re.MULTILINE)
    sockets = re.search(r"^Socket\(s\):\s*(\d+)", content, re.MULTILINE)

    if cores and sockets:
        info["physical_cores"] = (
            int(cores.group(1)) * int(sockets.group(1))
        )

    pretty = re.search(r'^PRETTY_NAME="(.+)"$', content, re.MULTILINE)
    if pretty:
        info["os"] = pretty.group(1)

    return info


for machine in MACHINES:
    summary = RESULTS / machine / "summary.csv"
    info_path = RESULTS / machine / "machine_info.txt"

    if not summary.exists():
        print(f"Skipping {machine}: summary.csv not found.")
        continue

    info = read_machine_info(info_path)

    machine_rows.append({
        "machine": machine,
        **info,
    })

    with summary.open(newline="") as file:
        for row in csv.DictReader(file):
            row["threads"] = int(row["threads"])
            row["batch_size"] = int(row["batch_size"])
            row["mean_time"] = float(row["mean_time"])
            row["stddev"] = float(row["stddev"])
            row["speedup"] = float(row["speedup"])
            row["efficiency"] = float(row["efficiency"])
            all_rows.append(row)


if not all_rows:
    raise SystemExit("No summary.csv files found.")


# Export machine information.
with (COMPARE / "machines.csv").open("w", newline="") as file:
    fields = [
        "machine",
        "cpu_model",
        "physical_cores",
        "logical_cores",
        "os",
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(machine_rows)


# Export combined benchmark data.
with (COMPARE / "comparison.csv").open("w", newline="") as file:
    fields = [
        "machine",
        "approach",
        "threads",
        "batch_size",
        "mean_time",
        "stddev",
        "speedup",
        "efficiency",
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for row in all_rows:
        writer.writerow({key: row[key] for key in fields})


# Compare execution time at matching thread counts.
# Each approach and mutex batch size gets its own graph.
groups = {}

for row in all_rows:
    approach = row["approach"]
    batch = row["batch_size"]
    label = f"{approach}_k{batch}" if approach == "mutex" else approach

    groups.setdefault(label, []).append(row)


for label, rows in groups.items():
    plt.figure(figsize=(10, 6))

    machines = sorted({row["machine"] for row in rows})

    for machine in machines:
        machine_data = [
            row for row in rows
            if row["machine"] == machine
        ]

        machine_data.sort(key=lambda row: row["threads"])

        x = [row["threads"] for row in machine_data]
        y = [row["mean_time"] for row in machine_data]

        plt.plot(x, y, marker="o", label=machine)

    plt.xlabel("Number of Threads")
    plt.ylabel("Mean Execution Time (seconds)")
    plt.title(f"Machine Comparison - {label}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = FIGURES / f"machine_comparison_{label}.png"
    plt.savefig(output, dpi=300)
    plt.close()

    print(f"Created: {output}")


# Compare speedup across machines.
plt.figure(figsize=(10, 6))

for machine in sorted({row["machine"] for row in all_rows}):
    data = [
        row for row in all_rows
        if row["machine"] == machine
        and row["approach"] == "local"
    ]

    data.sort(key=lambda row: row["threads"])

    if data:
        plt.plot(
            [row["threads"] for row in data],
            [row["speedup"] for row in data],
            marker="o",
            label=machine,
        )

plt.xlabel("Number of Threads")
plt.ylabel("Speedup")
plt.title("Local Accumulation Speedup Across Machines")
plt.grid(True)
plt.legend()
plt.tight_layout()

output = FIGURES / "machine_comparison_speedup.png"
plt.savefig(output, dpi=300)
plt.close()

print(f"Created: {output}")

print("\nComparison completed.")
print(f"Machine information: {COMPARE / 'machines.csv'}")
print(f"Combined data: {COMPARE / 'comparison.csv'}")
