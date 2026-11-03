#!/usr/bin/env bash
# check.sh - kiem tra tinh dung truoc khi do (chay nhanh voi N = 10^6)
set -e
N=1000000; S=2024; fail=0
pi() { "$@" | cut -d, -f5; }
ok()  { echo "  [OK]   $1"; }
bad() { echo "  [SAI]  $1"; fail=1; }

p1=$(pi ./pi_single $N $S)
awk -v p=$p1 'BEGIN{exit !(p>3.13 && p<3.15)}' && ok "Approach 1: pi = $p1" || bad "Approach 1: pi = $p1 ngoai khoang 3.14 +- 0.01"

l1=$(pi ./pi_local $N 1 $S)
[ "$l1" = "$p1" ] && ok "Approach 2 voi T=1 trung Approach 1" || bad "Approach 2 T=1 ($l1) khac Approach 1 ($p1)"

for T in 2 3 7 8 16; do                     # 3, 7: kiem tra chia phan du
  l=$(pi ./pi_local $N $T $S); m=$(pi ./pi_mutex $N $T $S); mk=$(pi ./pi_mutex $N $T $S 100)
  if [ "$l" = "$m" ] && [ "$l" = "$mk" ]; then ok "T=$T: Approach 2 = Approach 3 (k=1) = Approach 3 (k=100) = $l"
  else bad "T=$T: local=$l mutex=$m mutex_k100=$mk (phai giong het nhau)"; fi
done

[ $fail -eq 0 ] && echo "check.sh: TAT CA DEU DUNG" || { echo "check.sh: CO LOI, KHONG DUOC DO"; exit 1; }
