#!/usr/bin/env bash
set -euo pipefail

N=1000000
SEED=12345
TOLERANCE=0.01

passed=0
failed=0

check_output() {
    local name="$1"
    local output="$2"

    if ! python3 - "$name" "$output" "$N" "$TOLERANCE" <<'PY'
import sys
import math

name, output, expected_n, tolerance = sys.argv[1:]
expected_n = int(expected_n)
tolerance = float(tolerance)

try:
    fields = output.strip().split(",")

    if len(fields) != 4:
        raise ValueError("Expected 4 CSV fields")

    pi_value = float(fields[0])
    inside = int(fields[1])
    total = int(fields[2])
    elapsed = float(fields[3])

    if total != expected_n:
        raise ValueError(f"Expected {expected_n} points, got {total}")

    if not (0 <= inside <= total):
        raise ValueError("Invalid inside-point count")

    if not math.isfinite(pi_value) or abs(pi_value - 3.141592653589793) > tolerance:
        raise ValueError(f"Pi estimate outside tolerance: {pi_value}")

    if not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("Invalid execution time")

except Exception as exc:
    print(f"FAIL: {name}: {exc}")
    sys.exit(1)

print(f"PASS: {name}")
PY
    then
        return 1
    fi
}

run_test() {
    local name="$1"
    shift

    echo "Testing: $name"

    local output
    if ! output=$("$@" 2>/dev/null); then
        echo "FAIL: $name (program returned an error)"
        failed=$((failed + 1))
        return
    fi

    if check_output "$name" "$output"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi
}

# Approach 1: Single Thread
run_test "pi_single" ./pi_single "$N" "$SEED"

# Approach 2: Local Accumulation
run_test "pi_local (4 threads)" ./pi_local "$N" 4 "$SEED"

# Approach 3: Shared Variable + Mutex
run_test "pi_mutex (k=1)" ./pi_mutex "$N" 4 1 "$SEED"
run_test "pi_mutex (k=100)" ./pi_mutex "$N" 4 100 "$SEED"

echo
echo "=========================================="
echo "Tests passed: $passed"
echo "Tests failed: $failed"
echo "=========================================="

if [ "$failed" -eq 0 ]; then
    echo "check.sh: TAT CA DEU DUNG"
    exit 0
else
    echo "check.sh: CO LOI"
    exit 1
fi
