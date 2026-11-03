#!/usr/bin/env python3
"""plot.py - ve do thi cho MOT may.
Cach chay: python3 scripts/plot.py results/<ten_may>
Doc <dir>/raw/*.csv, ghi <dir>/summary.csv va <dir>/figures/*.png
"""
import glob, os, re, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d0 = sys.argv[1] if len(sys.argv) > 1 else "results"
info = os.path.join(d0, "machine_info.txt")
CORES = os.cpu_count()
if os.path.exists(info):
    m = re.search(r"cores=(\d+)", open(info).read())
    if m: CORES = int(m.group(1))
fig_dir = os.path.join(d0, "figures"); os.makedirs(fig_dir, exist_ok=True)

frames = []
for f in sorted(glob.glob(os.path.join(d0, "raw", "*.csv"))):
    d = pd.read_csv(f); d["source"] = os.path.basename(f); frames.append(d)
if not frames: sys.exit(f"Khong co file CSV trong {d0}/raw")
df = pd.concat(frames, ignore_index=True)
assert df["n_points"].nunique() == 1, "Cac file CSV dung N khac nhau -> khong duoc ghep!"

# Diem neo: cau hinh xuat hien o nhieu file phai co thoi gian gan nhau
per_file = df.groupby(["approach", "threads", "k", "source"])["time_sec"].mean().reset_index()
for key, d in per_file.groupby(["approach", "threads", "k"]):
    if len(d) > 1 and d.time_sec.max() / d.time_sec.min() >= 1.10:
        print(f"CANH BAO diem neo {key} lech > 10%: " + ", ".join(f"{r.source}={r.time_sec:.4f}s" for r in d.itertuples()))

g = df.groupby(["approach", "threads", "k"])["time_sec"].agg(["mean", "std", "count"]).reset_index()
t_single = g.loc[g.approach == "single", "mean"].iloc[0]
g["speedup"] = t_single / g["mean"]
g["efficiency"] = g["speedup"] / g["threads"]
g.to_csv(os.path.join(d0, "summary.csv"), index=False)

main = g[((g.approach == "local") & (g.k == 0)) | ((g.approach == "mutex") & (g.k == 1))]
LABEL = {"local": "Approach 2 - Local accumulation", "mutex": "Approach 3 - Shared + mutex"}
name = os.path.basename(os.path.normpath(d0))

def style(ax, ylabel, title):
    ax.set_xscale("log", base=2); ax.set_xlabel("Number of threads"); ax.set_ylabel(ylabel)
    ax.set_title(f"{title} ({name}, {CORES} cores)"); ax.axvline(CORES, ls=":", c="gray", label=f"{CORES} cores")
    ax.grid(alpha=.3); ax.legend()

def save(fig, f): fig.tight_layout(); fig.savefig(os.path.join(fig_dir, f), dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.5))
for a, d in main.groupby("approach"):
    ax.errorbar(d.threads, d["mean"], yerr=d["std"], marker="o", capsize=3, label=LABEL[a])
ax.axhline(t_single, ls="--", c="k", label="Approach 1 - Single thread")
style(ax, "Execution time (s)", "Execution Time vs Threads"); save(fig, "time_vs_threads.png")

fig, ax = plt.subplots(figsize=(7, 4.5))
for a, d in main.groupby("approach"):
    ax.plot(d.threads, d.speedup, marker="o", label=LABEL[a])
ts = sorted(main.threads.unique())
ax.plot(ts, [min(t, CORES) for t in ts], "k--", alpha=.5, label="Ideal min(T, cores)")
style(ax, "Speedup = T_single / T_parallel", "Speedup vs Threads"); save(fig, "speedup_vs_threads.png")

fig, ax = plt.subplots(figsize=(7, 4.5))
for a, d in main.groupby("approach"):
    ax.plot(d.threads, d.efficiency, marker="o", label=LABEL[a])
style(ax, "Efficiency = Speedup / T", "Parallel Efficiency vs Threads"); save(fig, "efficiency_vs_threads.png")

kd = g[g.approach == "mutex"]; kt = kd.groupby("threads")["k"].nunique()
if (kt > 1).any():
    T_k = kt.idxmax(); d = kd[kd.threads == T_k].sort_values("k")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(d.k, d["mean"], yerr=d["std"], marker="o", capsize=3, label=f"Approach 3, T = {T_k}")
    lt = main[(main.approach == "local") & (main.threads == T_k)]
    if len(lt): ax.axhline(lt["mean"].iloc[0], ls="--", c="g", label=f"Approach 2, T = {T_k}")
    ax.set_xscale("log"); ax.set_xlabel("k (iterations between shared updates)"); ax.set_ylabel("Execution time (s)")
    ax.set_title(f"Synchronization Frequency 6.1 ({name})"); ax.grid(alpha=.3); ax.legend(); save(fig, "sync_frequency.png")

print(f"{name}: T_single = {t_single:.4f}s, {CORES} cores -> {d0}/summary.csv, {fig_dir}/")
