#!/usr/bin/env python3
"""compare.py - so sanh Approach 2 giua cac may (dung cho phan B, C, 6.2).
Cach chay: python3 scripts/compare.py      (doc moi results/*/summary.csv)
Moi may tu tinh speedup voi T_single CUA CHINH NO -> khong tron so lieu giua cac may.
"""
import glob, os, re
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows, fig, ax = [], *plt.subplots(figsize=(7.5, 4.8))
for f in sorted(glob.glob("results/*/summary.csv")):
    d0 = os.path.dirname(f); name = os.path.basename(d0)
    cores = int(re.search(r"cores=(\d+)", open(os.path.join(d0, "machine_info.txt")).read()).group(1))
    g = pd.read_csv(f); loc = g[g.approach == "local"].sort_values("threads")
    best = loc.loc[loc.speedup.idxmax()]
    # diem bao hoa: T nho nhat dat >= 95% speedup cao nhat
    sat = int(loc[loc.speedup >= 0.95 * best.speedup].threads.min())
    t128 = loc[loc.threads == loc.threads.max()].iloc[0]
    rows.append(dict(may=name, cores=cores, T_single=round(g[g.approach == "single"]["mean"].iloc[0], 4),
                     speedup_max=round(best.speedup, 2), T_tai_max=int(best.threads), diem_bao_hoa=sat,
                     speedup_T_max=round(t128.speedup, 2)))
    ax.plot(loc.threads, loc.speedup, marker=".", label=f"{name} ({cores} cores)")
ax.set_xscale("log", base=2); ax.set_xlabel("Number of threads"); ax.set_ylabel("Speedup (Approach 2)")
ax.set_title("Approach 2 speedup on different machines"); ax.grid(alpha=.3); ax.legend()
os.makedirs("results/compare", exist_ok=True)
fig.tight_layout(); fig.savefig("results/compare/speedup_all_machines.png", dpi=150)
t = pd.DataFrame(rows); t.to_csv("results/compare/machines.csv", index=False); print(t.to_string(index=False))
