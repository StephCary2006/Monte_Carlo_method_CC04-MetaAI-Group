#!/usr/bin/env bash
# run_all.sh - MOT LENH chay toan bo thi nghiem tren may hien tai.
# Cach dung:  ./scripts/run_all.sh <ten_may>      vi du: ./scripts/run_all.sh tv1
# Ket qua:    results/<ten_may>/raw/*.csv  +  results/<ten_may>/machine_info.txt
set -e
name=${1:?"Thieu ten may, vi du: ./scripts/run_all.sh tv1"}
dir=results/$name
if [ -d "$dir/raw" ] && [ -n "$(ls -A "$dir/raw" 2>/dev/null)" ]; then
  echo "$dir/raw da co du lieu. Xoa hoac doi ten truoc khi chay lai." >&2; exit 1
fi
mkdir -p "$dir/raw"

make -s all
./scripts/check.sh                       # code sai thi dung ngay, khong do

C=$(nproc)
# Approach 2: tung so nguyen 1..max(16,C), sau do thua dan den 128
max=$(( C > 16 ? C : 16 ))
T_LOCAL="$(seq -s ' ' 1 $max)"
for t in 24 32 48 64 96 128; do [ $t -gt $max ] && T_LOCAL="$T_LOCAL $t"; done
# Approach 3: luy thua cua 2 va C (Approach 3 cham nen chay it diem hon)
T_MUTEX=$(printf "%s\n" 1 2 4 8 16 32 64 128 $C | sort -n | uniq | tr '\n' ' ')

{ echo "cores=$C"; echo "date=$(date '+%F %T')"; echo "commit=$(git rev-parse --short HEAD 2>/dev/null || echo none)";
  echo "gcc=$(gcc --version | head -1)"; echo; lscpu; } > "$dir/machine_info.txt"

echo "May $name: $C core | Approach 2: T = $T_LOCAL | Approach 3: T = $T_MUTEX"
B=./scripts/run_bench.sh
$B single                       "$dir/raw/single.csv"
$B local   "$T_LOCAL"           "$dir/raw/local.csv"
$B mutex   "$T_MUTEX"           "$dir/raw/mutex.csv"
$B mutex_k $C "1 10 100 1000 10000" "$dir/raw/mutex_k.csv"
python3 scripts/plot.py "$dir"
echo "XONG. Gui nguyen thu muc $dir cho TV4."
