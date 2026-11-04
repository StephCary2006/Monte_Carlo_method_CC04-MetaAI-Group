#!/usr/bin/env bash
# run_bench.sh - chay benchmark va ghi ket qua ra file CSV
# Cach dung:
#   ./scripts/run_bench.sh single                        <file.csv>
#   ./scripts/run_bench.sh local  "<danh sach T>"        <file.csv>
#   ./scripts/run_bench.sh mutex  "<danh sach T>"        <file.csv>
#   ./scripts/run_bench.sh mutex_k <T> "<danh sach k>"   <file.csv>
# Vi du chia Approach 2 cho 2 nguoi, may 8 core (CUNG MOT MAY, chay lan luot):
#   TV2: ./scripts/run_bench.sh local "1 2 3 4 5 6 7 8" results/raw/local_part1.csv
#   TV3: ./scripts/run_bench.sh local "1 8 9 10 11 12 13 14 15 16 24 32 48 64 96 128" \
#        results/raw/local_part2.csv
set -e
mkdir -p "$(dirname "${@: -1}")"
N=10000000      # giu CO DINH khi so sanh
SEED=2024
RUNS=5          # moi cau hinh chay 5 lan

mode=$1
header="approach,threads,n_points,k,pi_estimate,time_sec"

case "$mode" in
  single)
    out=$2; [ -f "$out" ] || echo "$header" > "$out"
    for r in $(seq $RUNS); do ./pi_single $N $SEED >> "$out"; done ;;
  local|mutex)
    threads=$2; out=$3; [ -f "$out" ] || echo "$header" > "$out"
    for T in $threads; do
      for r in $(seq $RUNS); do ./pi_$mode $N $T $SEED >> "$out"; done
      echo "  $mode T=$T xong" >&2
    done ;;
  mutex_k)
    T=$2; ks=$3; out=$4; [ -f "$out" ] || echo "$header" > "$out"
    for k in $ks; do
      for r in $(seq $RUNS); do ./pi_mutex $N $T $SEED $k >> "$out"; done
      echo "  mutex T=$T k=$k xong" >&2
    done ;;
  *) echo "mode khong hop le: $mode" >&2; exit 1 ;;
esac
