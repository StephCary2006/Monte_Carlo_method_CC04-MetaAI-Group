#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Configuration
N="${N:-10000000}"
RUNS="${RUNS:-5}"
SEED="${SEED:-12345}"
TV="${TV:-tv4}"
MACHINE="${MACHINE:-$(hostname -s)}"

CPU_THREADS="$(nproc)"
MAX_THREADS="${MAX_THREADS:-$((CPU_THREADS * 2))}"

OUT_DIR="results/$TV"
RAW="$OUT_DIR/raw.csv"

mkdir -p "$OUT_DIR"

# Build programs
make all

# Machine information
{
    echo "Machine: $MACHINE"
    echo "Date: $(date)"
    echo "OS: $(uname -srm)"
    echo "Logical CPUs: $CPU_THREADS"
    echo "Benchmark points: $N"
    echo "Runs per configuration: $RUNS"
    echo "Maximum threads: $MAX_THREADS"
    echo
    lscpu 2>/dev/null || true
} > "$OUT_DIR/machine_info.txt"

# CSV header
echo "machine,approach,threads,batch_size,run,points,inside,pi,execution_time,seed" > "$RAW"

record() {
    echo "$MACHINE,$1,$2,$3,$4,$5,$6,$7,$8,$9" >> "$RAW"
}

get_value() {
    local key="$1"
    awk -F= -v k="$key" '$1 == k {print $2; exit}'
}

echo "======================================"
echo " Monte Carlo Pi Benchmark"
echo " Machine: $MACHINE"
echo " N: $N | Runs: $RUNS"
echo " Threads: 1..$MAX_THREADS"
echo "======================================"

for run in $(seq 1 "$RUNS"); do
    current_seed=$((SEED + run - 1))

    echo
    echo "Run $run / $RUNS"

    # Single-thread baseline
    echo "  [single]"

    out="$(./pi_single "$N" "$current_seed")"

    pi="$(awk '/Pi estimate/ {print $NF}' <<< "$out")"
    inside="$(awk '/Inside/ {print $NF}' <<< "$out")"
    elapsed="$(awk '/^Time:/ {print $2}' <<< "$out")"

    record "single" 1 0 "$run" "$N" "$inside" "$pi" "$elapsed" "$current_seed"

    # Thread scaling
    for T in $(seq 1 "$MAX_THREADS"); do
        echo "  [local] threads=$T"

        out="$(./pi_local "$N" "$T" "$current_seed")"
        IFS=',' read -r approach threads points k pi elapsed <<< "$out"

        record "local" "$T" 0 "$run" "$points" "" "$pi" "$elapsed" "$current_seed"

        # False sharing experiment
        for mode in packed padded; do
            echo "  [false sharing: $mode] threads=$T"

            out="$(./pi_false_sharing "$N" "$T" "$current_seed" "$mode")"
            IFS=',' read -r approach threads points k pi elapsed <<< "$out"

            record "$approach" "$T" 0 "$run" "$points" "" "$pi" "$elapsed" "$current_seed"
        done

        # Mutex experiment with different batch sizes
        for K in 1 10 100 1000; do
            echo "  [mutex] threads=$T k=$K"

            out="$(./pi_mutex "$N" "$T" "$K" "$current_seed")"

            points="$(get_value points <<< "$out")"
            threads="$(get_value threads <<< "$out")"
            inside="$(get_value inside <<< "$out")"
            pi="$(get_value pi <<< "$out")"
            elapsed="$(get_value seconds <<< "$out")"

            record "mutex" "$threads" "$K" "$run" "$points" "$inside" "$pi" "$elapsed" "$current_seed"
        done
    done
done

echo
echo "======================================"
echo " Benchmark completed."
echo " Raw results: $RAW"
echo " Machine info: $OUT_DIR/machine_info.txt"
echo "======================================"
