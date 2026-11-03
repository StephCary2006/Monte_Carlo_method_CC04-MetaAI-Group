# CO2018 – Week 3: Multi-threading Best Practices via Monte Carlo $\pi$ Estimation

**Group:** CC04 – MetaAI Group (5 thành viên: TV1 – TV5)

---

## 1. Cấu trúc Thư mục (Repository Structure)

Repository đã được chia sẵn các thư mục độc lập để 5 thành viên làm việc song song không bị xung đột (conflict):

```text
Monte_Carlo_method_CC04-MetaAI-Group/
├── README.md                       # Hướng dẫn cấu trúc repo và quy trình làm việc nhóm
├── .gitignore                      # Bỏ qua file thực thi sau biên dịch và file rác
│
├── Makefile                        # [TV4 tạo] Build toàn bộ binary + target `make check`, `make clean`
├── common.h                        # [TV1 tạo] Header dùng chung: timer (CLOCK_MONOTONIC), rand_r, chia việc, in CSV
├── pi_single.c                     # [TV1 tạo] Approach 1: Single Thread (Baseline)
├── pi_local.c                      # [TV2 tạo] Approach 2: Multi-Thread Local Accumulation (+ False Sharing test)
├── pi_mutex.c                      # [TV3 tạo] Approach 3: Shared Variable + Mutex (k = 1, k > 1 + Race Condition test)
│
├── scripts/                        # [TV4 tạo] Các script tự động kiểm thử, chạy đo và vẽ đồ thị
│   ├── check.sh                    # Kiểm tra tự động với N = 10^6 (in "check.sh: TAT CA DEU DUNG")
│   ├── run_all.sh                  # Chạy toàn bộ thí nghiệm cho máy tvX -> xuất vào results/tvX/
│   ├── plot.py                     # Vẽ đồ thị chuẩn từ results/tvX/summary.csv
│   └── compare.py                  # Kiểm chứng chéo 5 máy -> xuất bảng & đồ thị vào results/compare/ và figures/
│
├── results/                        # Nơi lưu kết quả đo của 5 máy (không sửa tay file CSV)
│   ├── tv1/                        # Dữ liệu chạy từ máy TV1 (machine_info.txt, raw.csv, summary.csv)
│   ├── tv2/                        # Dữ liệu chạy từ máy TV2
│   ├── tv3/                        # Dữ liệu chạy từ máy TV3
│   ├── tv4/                        # Dữ liệu chạy từ máy TV4
│   ├── tv5/                        # Dữ liệu chạy từ máy TV5
│   └── compare/                    # [TV4 xuất] machines.csv và kết quả kiểm chứng chéo 5 máy
│
├── figures/                        # [TV4 xuất] Toàn bộ đồ thị (.png) dùng để đưa vào báo cáo
└── report/                         # [TV5 quản lý] File báo cáo chung và biên bản review code
```

---

## 2. Bảng Phân Công Nhiệm Vụ (Work Split)

| TV | Phụ trách | File Code / Công cụ cần tạo | Phần viết trong Báo cáo (`report/`) |
| :-: | :--- | :--- | :--- |
| **TV1** | **Approach 1** (Single Thread) | `common.h`, `pi_single.c` (+ thí nghiệm `printf` trong vòng lặp & `clock()` vs `CLOCK_MONOTONIC`) | Thiết kế Approach 1; Độ ổn định của baseline (bảng $T_{\text{single}}$ của 5 máy); Môi trường và phương pháp đo |
| **TV2** | **Approach 2** (Local Accumulation) | `pi_local.c` (+ phiên bản ghi mảng chung minh họa `false sharing`) | Thiết kế Approach 2 (Map–Reduce); **A. Non-linear Speedup**; **E. Parallel Efficiency**; đối chứng False Sharing |
| **TV3** | **Approach 3** (Shared + Mutex) | `pi_mutex.c` ($k = 1$ và $k > 1$; + phiên bản bỏ mutex minh họa `race condition`) | Thiết kế Approach 3; **D. Synchronization Cost**; **Thí nghiệm 6.1** |
| **TV4** | **Đo đạc & Đồ thị** | Quản lý repo & tag `v1-freeze`; `Makefile`, `scripts/check.sh`, `scripts/run_all.sh`, `scripts/plot.py`, `scripts/compare.py` | **B. Saturation Point**; **C. Oversubscription**; **Thí nghiệm 6.2**; xuất đồ thị máy chính & bảng so sánh 5 máy |
| **TV5** | **Báo cáo & QA** | Tạo file báo cáo mẫu trong `report/`; Review code TV1–TV3 trước khi code freeze | Mở đầu; **Thí nghiệm 6.3**; **Best Practices**; Kết luận; biên tập, đối chiếu số liệu với `summary.csv` và nộp bài |

---

## 3. Quy trình Chạy Thực Nghiệm cho Mỗi Thành Viên (Sau khi có tag `v1-freeze`)

```bash
# 1. Cài đặt môi trường trên Ubuntu / WSL2
sudo apt update && sudo apt install -y build-essential python3-pandas python3-matplotlib

# 2. Clone repo và chuyển về đúng tag code freeze
git clone https://github.com/StephCary2006/Monte_Carlo_method_CC04-MetaAI-Group.git
cd Monte_Carlo_method_CC04-MetaAI-Group
git checkout v1-freeze

# 3. Kiểm tra tính đúng đắn (phải thấy dòng 'check.sh: TAT CA DEU DUNG')
make check

# 4. Đóng ứng dụng nặng, cắm sạc máy tính, chạy đo (thay tv1 bằng mã tv1..tv5 của bạn)
./scripts/run_all.sh tv1

# 5. Đẩy hoặc gửi thư mục kết quả results/tvX cho TV4
# 6. (Chỉ TV4) Khi đủ 5 thư mục trong results/, chạy tổng hợp và vẽ hình so sánh:
python3 scripts/compare.py
```
