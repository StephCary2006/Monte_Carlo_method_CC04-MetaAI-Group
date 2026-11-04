#!/usr/bin/env bash
# test_all_tv2.sh - KIEM TRA TONG THE + DONG GOI phan viec cua TV2
# Cach dung:
#   ./scripts/test_all_tv2.sh            dung lai ket qua da co trong results/tv2 (neu co)
#   ./scripts/test_all_tv2.sh --fresh    xoa results/tv2 va do lai tu dau
#   ./scripts/test_all_tv2.sh --full     do pi voi N = 10^12 (5 chu so thap phan, ~10 phut)
cd "$(dirname "$0")/.."
ROOT=$(pwd); NAME=$(basename "$ROOT")
FRESH=0; FULL=0
for a in "$@"; do case $a in --fresh) FRESH=1;; --full) FULL=1;; esac; done
mkdir -p logs
exec > >(tee logs/test_all.log) 2>&1
PASS=(); FAIL=(); WARN=()
step() { echo; echo "=================== $1 ==================="; }
ok()   { PASS+=("$1"); echo "[PASS] $1"; }
bad()  { FAIL+=("$1"); echo "[FAIL] $1"; }
warn() { WARN+=("$1"); echo "[WARN] $1"; }

step "1. Thong tin may"
echo "nproc = $(nproc)"; lscpu | grep -E "Model name|Thread\(s\) per core|Hypervisor vendor" || true
echo "gcc   = $(gcc --version | head -1)"

step "2. Bien dich (-Wall -Wextra)"
make -s clean
if make all 2>logs/build_warnings.txt; then
  if [ -s logs/build_warnings.txt ]; then cat logs/build_warnings.txt; bad "Bien dich co canh bao"; else ok "Bien dich sach, khong canh bao"; fi
else cat logs/build_warnings.txt; bad "Bien dich loi"; fi

step "3. Kiem tra tinh dung (check.sh)"
./scripts/check.sh && ok "check.sh: Approach 1/2/3 cho pi dung va trung nhau" || bad "check.sh"

step "4. Approach 2: do hieu nang + false sharing + ban nhap bao cao"
[ $FRESH -eq 1 ] && rm -rf results/tv2 && echo "Da xoa results/tv2 (--fresh)"
if ./scripts/run_tv2.sh; then
  ok "run_tv2.sh hoan tat"
  if grep -q "Note for the team" results/tv2/tv2_report_draft.md; then
    warn "Mot so cau hinh co std > 10% - nen chay lai voi --fresh khi may ranh"
  else ok "So lieu on dinh (std <= 10%)"; fi
else bad "run_tv2.sh"; fi

step "5. Do chinh xac pi (pi_precise)"
N=1000000000; [ $FULL -eq 1 ] && N=1000000000000
./pi_precise $N $(nproc) 2024 | tee logs/pi_precise.txt
d=$(grep "correct decimals" logs/pi_precise.txt | awk '{print $NF}')
need=3; [ $FULL -eq 1 ] && need=5
[ "${d:-0}" -ge $need ] && ok "pi dung $d chu so thap phan (N = $N)" || bad "pi chi dung ${d:-0} chu so (N = $N, can >= $need)"

step "6. Dong goi ~/$NAME.zip"
make -s clean
cd .. && rm -f "$NAME.zip" && zip -qr "$NAME.zip" "$NAME" && ok "Da tao $(pwd)/$NAME.zip ($(du -h "$NAME.zip" | cut -f1))"

step "7. Copy ra thu muc Downloads cua Windows (VMware Shared Folders)"
DL=""
if ! ls /mnt/hgfs/* >/dev/null 2>&1 && command -v vmhgfs-fuse >/dev/null; then
  echo "Thu mount shared folder (co the hoi mat khau sudo)..."
  sudo mkdir -p /mnt/hgfs && sudo vmhgfs-fuse .host:/ /mnt/hgfs -o subtype=vmhgfs-fuse,allow_other 2>/dev/null || true
fi
DL=$(find /mnt/hgfs -maxdepth 1 -iname "*download*" 2>/dev/null | head -1)
if [ -n "$DL" ]; then
  cp -f "$NAME.zip" "$DL/" && ok "Da copy sang Windows: $DL/$NAME.zip"
else
  echo "Chua bat Shared Folder Downloads -> bo qua. Keo tha ~/$NAME.zip ra Windows, hoac xem README_TV2.md."
fi

step "TONG KET"
for p in "${PASS[@]}"; do echo "  [PASS] $p"; done
for w in "${WARN[@]}"; do echo "  [WARN] $w"; done
for f in "${FAIL[@]}"; do echo "  [FAIL] $f"; done
[ ${#FAIL[@]} -eq 0 ] && echo ">>> TAT CA DEU DAT$([ ${#WARN[@]} -gt 0 ] && echo " (co ${#WARN[@]} canh bao)")" || echo ">>> CO ${#FAIL[@]} MUC CHUA DAT (xem logs/test_all.log)"
