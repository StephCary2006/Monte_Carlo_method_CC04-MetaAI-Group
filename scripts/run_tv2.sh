#!/usr/bin/env bash
# run_tv2.sh - MOT LENH lam tron phan Approach 2 cua TV2:
#   1) make check   2) run_all.sh tv2 (bo do chung cua nhom)
#   3) thi nghiem false sharing   4) phan tich + sinh ban nhap bao cao (tieng Anh)
# Cach dung: ./scripts/run_tv2.sh
set -e
cd "$(dirname "$0")/.."
D=results/tv2
make -s all
./scripts/check.sh

if [ -f "$D/summary.csv" ]; then
  echo ">> Da co $D/summary.csv, bo qua run_all.sh"
else
  ./scripts/run_all.sh tv2
fi

C=$(nproc)
FS=$D/fs/raw.csv
if [ -f "$FS" ]; then
  echo ">> Da co $FS, bo qua thi nghiem false sharing"
else
  mkdir -p $D/fs
  T_FS=$(printf "%s\n" 1 2 4 8 16 $C | awk -v c=$C '$1<=c' | sort -n | uniq | tr '\n' ' ')
  echo ">> False sharing: T = $T_FS"
  echo "approach,threads,n_points,k,pi_estimate,time_sec" > $FS
  for T in $T_FS; do
    for r in 1 2 3 4 5; do
      ./pi_local         10000000 $T 2024        >> $FS
      ./pi_false_sharing 10000000 $T 2024 padded >> $FS
      ./pi_false_sharing 10000000 $T 2024 packed >> $FS
    done
    echo "  T=$T xong"
  done
fi

python3 scripts/tv2_analysis.py $D
echo
echo "XONG. Gui cho nhom:"
echo "  - TV4: nen thu muc $D  (zip -r tv2.zip $D)"
echo "  - TV5: $D/tv2_report_draft.md va $D/tv2_figures/*.png"
