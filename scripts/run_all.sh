#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Usage:
#   ./scripts/run_all.sh tv4
#
# Optional environment variables:
#   N=10000000 RUNS=5 THREAD_COUNTS="1 2 4 8"
# ============================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MACHINE="${1:-tv4}"
N="${N:-10000000}"
RUNS="${RUNS:-5}"
SEED="${SEED:-12345}"

RESULT_DIR="results/$MACHINE"
mkdir -p "$RESULT_DIR"

RAW="$RESULT_DIR/raw.csv"
SUMMARY="$RESULT_DIR/summary.csv"

for program in pi_single pi_local pi_mutex; do
    if [ ! -x "./$program" ]; then
        echo "Error: ./$program not found. Run 'make' first."
        exit 1
    fi
done

if ! command -v lscpu >/dev/null 2>&1; then
    echo "Error: lscpu is required."
    exit 1
fi

LOGICAL_CORES="$(nproc)"
PHYSICAL_CORES="$(lscpu -p=CORE,SOCKET | grep -v '^#' | sort -u | wc -l)"

# Default thread counts: below, around, and above CPU capacity.
if [ -n "${THREAD_COUNTS:-}" ]; then
    read -r -a THREAD_LIST <<< "$THREAD_COUNTS"
else
    THREAD_LIST=(1 2 4 "$PHYSICAL_CORES" "$LOGICAL_CORES" "$((LOGICAL_CORES * 2))")
fi

# Remove duplicate thread counts and invalid values.
THREAD_LIST=($(printf '%s\n' "${THREAD_LIST[@]}" | awk '$1 > 0' | sort -nu))

echo "=========================================="
echo "Monte Carlo Pi Benchmark"
echo "Machine: $MACHINE"
echo "Points : $N"
echo "Runs   : $RUNS"
echo "Physical cores: $PHYSICAL_CORES"
echo "Logical cores : $LOGICAL_CORES"
echo "Threads: ${THREAD_LIST[*]}"
echo "=========================================="

# Save machine information.
{
    echo "Machine ID: $MACHINE"
    echo "Date: $(date --iso-8601=seconds)"
    echo
    echo "Operating system:"
    cat /etc/os-release
    echo
    echo "CPU information:"
    lscpu
    echo
    echo "Memory information:"
    free -h
} > "$RESULT_DIR/machine_info.txt"

# CSV header.
echo "machine,approach,threads,batch_size,run,points,inside,pi,execution_time" > "$RAW"

record_result() {
    local approach="$1"
    local threads="$2"
    local batch="$3"
    local run="$4"
    shift 4

    local output
    output=$("$@")

    local pi inside total elapsed
    IFS=',' read -r pi inside total elapsed <<< "$output"

    if [ "$total" != "$N" ]; then
        echo "Error: $approach processed $total points instead of $N."
        exit 1
    fi

    echo "$MACHINE,$approach,$threads,$batch,$run,$total,$inside,$pi,$elapsed" >> "$RAW"
}

for threads in "${THREAD_LIST[@]}"; do
    echo
    echo "Testing with $threads thread(s)"

    for run in $(seq 1 "$RUNS"); do
        current_seed=$((SEED + run))

        echo "  Run $run/$RUNS"

        # Approach 1: Single-thread baseline.
        record_result "single" 1 0 "$run" \
            ./pi_single "$N" "$current_seed"

        # Approach 2: Local accumulation.
        record_result "local" "$threads" 0 "$run" \
            ./pi_local "$N" "$threads" "$current_seed"

        # Approach 3: Shared variable + mutex, k = 1.
        record_result "mutex" "$threads" 1 "$run" \
            ./pi_mutex "$N" "$threads" 1 "$current_seed"

        # Approach 3: Shared variable + mutex, k = 100.
        record_result "mutex" "$threads" 100 "$run" \
            ./pi_mutex "$N" "$threads" 100 "$current_seed"
    done
done

# Generate summary statistics.
python3 - "$RAW" "$SUMMARY" <<'PY'
import csv
import sys
import statistics
from collections import defaultdict

raw_path, summary_path = sys.argv[1:]

groups = defaultdict(list)
baseline = defaultdict(list)

with open(raw_path, newline="") as f:
    for row in csv.DictReader(f):
        machine = row["machine"]
        approach = row["approach"]
        threads = int(row["threads"])
        batch = int(row["batch_size"])
        elapsed = float(row["execution_time"])

        key = (machine, approach, threads, batch)
        groups[key].append(elapsed)

        if approach == "single":
            baseline[machine].append(elapsed)

with open(summary_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "machine", "approach", "threads", "batch_size",
        "mean_time", "stddev", "speedup", "efficiency"
    ])

    for key, values in sorted(groups.items()):
        machine, approach, threads, batch = key

        mean_time = statistics.mean(values)
        stddev = statistics.stdev(values) if len(values) > 1 else 0.0

        base_values = baseline.get(machine, [])
        base_mean = statistics.mean(base_values) if base_values else 0.0

        speedup = base_mean / mean_time if mean_time > 0 else 0.0
        efficiency = speedup / threads if threads > 0 else 0.0

        writer.writerow([
            machine, approach, threads, batch,
            f"{mean_time:.9f}",
            f"{stddev:.9f}",
            f"{speedup:.6f}",
            f"{efficiency:.6f}"
        ])
PY

echo
echo "Benchmark completed."
echo "Raw data : $RAW"
echo "Summary  : $SUMMARY"

python3 scripts/plot.py "$MACHINE"

echo "Graphs saved in figures/."
