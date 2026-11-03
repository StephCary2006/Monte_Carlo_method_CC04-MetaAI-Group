#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

N=1000000
SEED=12345
THREADS=4
TOLERANCE=0.03

fail() {
    echo "[FAIL] $1" >&2
    exit 1
}

pass() {
    echo "[PASS] $1"
}

check_pi() {
    local pi="$1"
    awk -v p="$pi" -v tol="$TOLERANCE" \
        'BEGIN {
            if (p > 3.141592653589793 - tol &&
                p < 3.141592653589793 + tol) exit 0;
            exit 1;
        }'
}

echo "======================================"
echo " Monte Carlo Pi - Correctness Tests"
echo "======================================"

# 1. Single-thread baseline
out="$(./pi_single "$N" "$SEED")"
pi="$(awk '/Pi estimate/ {print $NF}' <<< "$out")"
points="$(awk '/Points/ {print $NF}' <<< "$out")"

[[ "$points" == "$N" ]] || fail "pi_single point count"
check_pi "$pi" || fail "pi_single pi estimate"
pass "pi_single"

# 2. Local accumulation
out="$(./pi_local "$N" "$THREADS" "$SEED")"
IFS=',' read -r approach threads points k pi elapsed <<< "$out"

[[ "$points" == "$N" ]] || fail "pi_local point count"
[[ "$threads" == "$THREADS" ]] || fail "pi_local thread count"
check_pi "$pi" || fail "pi_local pi estimate"
pass "pi_local"

# 3. False sharing: packed and padded
for mode in packed padded; do
    out="$(./pi_false_sharing "$N" "$THREADS" "$SEED" "$mode")"
    IFS=',' read -r approach threads points k pi elapsed <<< "$out"

    [[ "$points" == "$N" ]] || fail "false sharing $mode point count"
    check_pi "$pi" || fail "false sharing $mode pi estimate"
    pass "pi_false_sharing ($mode)"
done

# 4. Mutex
out="$(./pi_mutex "$N" "$THREADS" 1 "$SEED")"
points="$(awk -F= '$1=="points" {print $2}' <<< "$out")"
threads="$(awk -F= '$1=="threads" {print $2}' <<< "$out")"
pi="$(awk -F= '$1=="pi" {print $2}' <<< "$out")"

[[ "$points" == "$N" ]] || fail "pi_mutex point count"
[[ "$threads" == "$THREADS" ]] || fail "pi_mutex thread count"
check_pi "$pi" || fail "pi_mutex pi estimate"
pass "pi_mutex"

echo "======================================"
echo " All correctness tests passed."
echo "======================================"
