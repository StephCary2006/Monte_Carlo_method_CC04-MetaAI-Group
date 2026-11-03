#!/usr/bin/env python3
"""tv2_analysis.py - phan tich Approach 2 va sinh ban nhap bao cao tieng Anh tu so lieu THAT.
Cach chay: python3 scripts/tv2_analysis.py results/tv2
Dau ra:   results/tv2/tv2_report_draft.md, results/tv2/tv2_numbers.csv, results/tv2/tv2_figures/*.png
"""
import os, re, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = sys.argv[1] if len(sys.argv) > 1 else "results/tv2"
FIG = os.path.join(D, "tv2_figures"); os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------- machine info
info = open(os.path.join(D, "machine_info.txt")).read()
C = int(re.search(r"cores=(\d+)", info).group(1))
def lscpu(key):
    m = re.search(rf"^{key}:\s*(.+)$", info, re.M)
    return m.group(1).strip() if m else None
model = lscpu("Model name") or "unknown CPU"
tpc = int(lscpu(r"Thread\(s\) per core") or 1)
hyp = lscpu("Hypervisor vendor")
phys = C // tpc if tpc > 1 else None

# ---------------------------------------------------------------- data
N = int(pd.read_csv(os.path.join(D, "raw", "single.csv"))["n_points"].iloc[0])
g = pd.read_csv(os.path.join(D, "summary.csv"))
Ts = float(g.loc[g.approach == "single", "mean"].iloc[0])
loc = g[g.approach == "local"].sort_values("threads").reset_index(drop=True)
loc["speedup"] = Ts / loc["mean"]
loc["efficiency"] = loc["speedup"] / loc["threads"]
loc["cv"] = loc["std"] / loc["mean"]
T_all = loc.threads.tolist()

def row(T):
    r = loc[loc.threads == T]
    return r.iloc[0] if len(r) else None

def nearest(T):
    return int(loc.iloc[(loc.threads - T).abs().idxmin()].threads)

def karp_flatt(S, T):
    return (1 / S - 1 / T) / (1 - 1 / T) if T > 1 else np.nan
loc["karp_flatt"] = [karp_flatt(s, t) for s, t in zip(loc.speedup, loc.threads)]

r1, rC = row(1), row(nearest(C))
Tc = int(rC.threads)
best = loc.loc[loc.speedup.idxmax()]
Smax, Tmax = float(best.speedup), int(best.threads)
Tsat = int(loc[loc.speedup >= 0.95 * Smax].threads.min())
rsat = row(Tsat)
Tbig = int(loc.threads.max()); rbig = row(Tbig)
T2 = nearest(2); r2 = row(T2)

# Amdahl fit tren vung T <= C
fit = loc[loc.threads <= C]
ps = np.linspace(0, 0.99999, 100000)
err = [(((1 / ((1 - p) + p / fit.threads)) - fit.speedup) ** 2).sum() for p in ps]
p_fit = float(ps[int(np.argmin(err))])
serial = 1 - p_fit
S_bound = 1 / serial

kf = loc[(loc.threads >= 2) & (loc.threads <= C)]
kf_trend = None
if len(kf) >= 3:
    slope = np.polyfit(kf.threads, kf.karp_flatt, 1)[0]
    span = kf.karp_flatt.iloc[-1] - kf.karp_flatt.iloc[0]
    kf_trend = "rising" if span > 0.02 and slope > 0 else ("flat" if abs(span) <= 0.02 else "falling")

# loi ich moi lan nhan doi so luong (trong vung <= C)
doubling = []
t = 1
while 2 * t <= C:
    a, b = row(t), row(2 * t)
    if a is not None and b is not None:
        doubling.append((t, 2 * t, 100 * (1 - b["mean"] / a["mean"])))
    t *= 2

overhead_T1 = 100 * (r1["mean"] / Ts - 1)
cv_mean = 100 * loc.cv.mean()
cv_bad = loc[loc.cv > 0.10].threads.tolist()

# ---------------------------------------------------------------- bang so lieu
show = sorted({x for x in [1, 2, 4, C // 2, C, 2 * C, 16, 32, 64, 128] if x in T_all})
tab = loc[loc.threads.isin(show)][["threads", "mean", "std", "speedup", "efficiency", "karp_flatt"]]
tab.to_csv(os.path.join(D, "tv2_numbers.csv"), index=False)

def md_table(df):
    lines = ["| Threads (T) | Mean time (s) | Std dev (s) | Speedup | Efficiency | Karp–Flatt e |",
             "|---:|---:|---:|---:|---:|---:|"]
    for r in df.itertuples():
        kfv = "–" if np.isnan(r.karp_flatt) else f"{r.karp_flatt:.3f}"
        lines.append(f"| {r.threads} | {r.mean:.4f} | {r.std:.4f} | {r.speedup:.2f} | {r.efficiency:.2f} | {kfv} |")
    return "\n".join(lines)

# ---------------------------------------------------------------- do thi
def xaxis(ax):
    ax.set_xscale("log", base=2); ax.set_xlabel("Number of threads (T)")
    ax.axvline(C, ls=":", c="gray", label=f"{C} logical CPUs"); ax.grid(alpha=.3)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(loc.threads, loc.speedup, "o-", label="Measured (Approach 2)")
ax.plot(loc.threads, [min(t, C) for t in loc.threads], "k--", alpha=.5, label="Ideal min(T, CPUs)")
tt = np.array(sorted(loc.threads))
ax.plot(tt, 1 / ((1 - p_fit) + p_fit / np.minimum(tt, C)), "-.", c="tab:red", label=f"Amdahl fit, p = {p_fit:.4f}")
xaxis(ax); ax.set_ylabel("Speedup = T_single / T_parallel")
ax.set_title("Approach 2: Speedup vs Number of Threads"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(FIG, "tv2_speedup.png"), dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(loc.threads, loc.efficiency, "o-", label="Measured efficiency")
ax.plot(loc.threads, [min(1, C / t) for t in loc.threads], "k--", alpha=.5, label="Upper bound min(1, CPUs / T)")
xaxis(ax); ax.set_ylabel("Efficiency = Speedup / T"); ax.set_ylim(0, 1.1)
ax.set_title("Approach 2: Parallel Efficiency vs Number of Threads"); ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(FIG, "tv2_efficiency.png"), dpi=150); plt.close(fig)

# false sharing
fs_path = os.path.join(D, "fs", "raw.csv")
fs = None
if os.path.exists(fs_path):
    f = pd.read_csv(fs_path)
    fs = f.groupby(["approach", "threads"])["time_sec"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    lab = {"local": "Local counter on stack (Approach 2)", "fs_padded": "Shared array, padded to 64 B",
           "fs_packed": "Shared array, packed (false sharing)"}
    for a in ["local", "fs_padded", "fs_packed"]:
        d = fs[fs.approach == a]
        ax.errorbar(d.threads, d["mean"], yerr=d["std"], marker="o", capsize=3, label=lab[a])
    xaxis(ax); ax.set_ylabel("Execution time (s)")
    ax.set_title("Effect of False Sharing on Local Accumulation"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "tv2_false_sharing.png"), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- van ban
vm = hyp is not None
machine = f"{C} logical CPUs ({model})" + (f", running as a {hyp} virtual machine" if vm else "")

design = f"""## Design of Approach 2: Local Accumulation with a Map–Reduce Structure

Approach 2 divides the {N:,} random samples into T contiguous chunks of N/T samples, one per POSIX thread; the last thread also takes the remainder N mod T, so the total number of samples is always exactly N. Each thread receives a private argument structure holding its sample count, its random seed and a slot for its result.

The computation follows a map–reduce pattern. In the map phase, every worker copies its seed into a local variable and counts the points that fall inside the unit circle in a counter allocated on its own stack. Nothing shared is read or written inside the sampling loop; the result is stored into the worker's structure exactly once, after the loop ends. In the reduce phase, the main thread calls `pthread_join` on each worker and adds the partial counts to obtain the total used in π ≈ 4 × hits / N.

```c
static void *worker(void *arg) {{
    task_t *t = (task_t *)arg;
    unsigned int seed = t->seed;        /* private RNG state  */
    long long local = 0;                /* private counter    */
    for (long long i = 0; i < t->n_points; i++)
        local += sample_hit(&seed);
    t->hits = local;                    /* single write       */
    return NULL;
}}
```

| Constraint from the specification | How the implementation satisfies it |
|---|---|
| No shared variable inside the main loop | The counter and the RNG state are local variables; the only write to memory visible to other threads happens once per thread, after the loop |
| Each thread uses an independent random generator | `rand_r()` with seed = base seed + thread index; `rand()` is avoided because the glibc version keeps a single global state protected by an internal lock, which would silently serialize the threads |
| Threads do not interfere during computation | Threads share no data and take no locks until they finish; partial results are combined only after `pthread_join` |

Execution time is measured with `clock_gettime(CLOCK_MONOTONIC)` from just before the first `pthread_create` to just after the last `pthread_join` and the final sum. Thread creation and joining are therefore included, because they are real costs of the parallel version, while argument parsing, memory allocation and printing are excluded. Correctness is verified automatically before every measurement: with one thread the estimate equals that of Approach 1 exactly, and for the same T and seed it equals the estimate of the mutex-based version digit for digit, because every thread draws the same sample sequence in both programs.
"""

dbl = ""
if len(doubling) >= 2:
    first, last = doubling[0], doubling[-1]
    dbl = (f" The return on each additional thread shrinks quickly: doubling from {first[0]} to {first[1]} threads cuts the execution time by "
           f"{first[2]:.0f}%, whereas doubling from {last[0]} to {last[1]} threads cuts it by only {last[2]:.0f}%.")

if kf_trend == "rising":
    kf_txt = ("The experimentally determined serial fraction (Karp–Flatt metric) rises with the number of threads, from "
              f"{kf.karp_flatt.iloc[0]:.3f} at T = {int(kf.threads.iloc[0])} to {kf.karp_flatt.iloc[-1]:.3f} at T = {int(kf.threads.iloc[-1])}. "
              "A fixed serial portion would keep this metric constant, so the growth indicates overhead that increases with the thread count "
              "rather than a constant piece of sequential code.")
elif kf_trend == "flat":
    kf_txt = ("The Karp–Flatt metric stays roughly constant across thread counts (about "
              f"{kf.karp_flatt.mean():.3f}), which is consistent with a fixed serial fraction rather than an overhead that grows with T.")
elif kf_trend == "falling":
    kf_txt = ("The Karp–Flatt metric decreases as threads are added, suggesting that part of the loss at low thread counts comes from "
              "start-up effects, such as CPU frequency ramp-up, that are amortized at higher parallelism.")
else:
    kf_txt = ""

smt_txt = ""
if phys:
    smt_txt = (f" The {C} logical CPUs correspond to only {phys} physical cores with {tpc} hardware threads each. Two hardware threads on the same core "
               "share its execution units, and this workload is dominated by arithmetic in `rand_r()` and the distance test, so the second thread on a core adds "
               f"far less than a full core of throughput; ideal scaling is therefore closer to {phys} than to {C}.")
elif vm:
    smt_txt = (f" The measurements were taken inside a {hyp} virtual machine. Each virtual CPU is a thread that the hypervisor schedules onto the host's logical "
               "processors, which may be two hardware threads of the same physical core, and the host operating system keeps running its own tasks, "
               "so the virtual CPUs are not dedicated cores.")

growth = (f"{r2.speedup:.2f} with {T2} threads and {rC.speedup:.2f} with {Tc} threads" if T2 != Tc
          else f"{rC.speedup:.2f} with {Tc} threads")
if len(fit) >= 3:
    amdahl_txt = (f"Fitting Amdahl's Law, S(T) = 1 / ((1 − p) + p / T), to the measurements up to {C} threads gives a parallel fraction p = {p_fit:.4f}, "
                  f"equivalent to a serial fraction of {100 * serial:.2f}% and an upper bound on speedup of {S_bound:.1f}. The sequential code in Approach 2 is, "
                  "however, very small: it consists only of creating the threads, joining them and adding T numbers. Amdahl's Law therefore captures the shape "
                  f"of the curve but not its cause. {kf_txt}")
else:
    amdahl_txt = ("Amdahl's Law, S(T) = 1 / ((1 − p) + p / T), limits speedup through the fraction of work that stays sequential. In Approach 2 that fraction is "
                  "very small, consisting only of creating the threads, joining them and adding T numbers, so Amdahl's Law alone cannot explain the losses.")
sat_txt = f", and speedup is already within 5% of that peak at {Tsat} threads" if Tsat < Tmax else ""
if overhead_T1 >= 1:
    ov_txt = f"already takes {overhead_T1:.1f}% longer than the single-threaded baseline"
else:
    ov_txt = f"takes almost exactly as long as the single-threaded baseline (difference {overhead_T1:+.1f}%)"

A = f"""## A. Why Speedup Does Not Scale Linearly with the Number of Threads

On the test machine with {machine}, speedup grows from 1.00 with one thread to {growth}, against an ideal value of {Tc}. The highest speedup, {Smax:.2f}, is reached at {Tmax} threads{sat_txt}.{dbl}

{amdahl_txt}

Several mechanisms account for the gap. Creating and joining threads has a fixed cost that does not shrink as work is divided; with one worker thread, Approach 2 {ov_txt}, and at {Tc} threads each thread processes only {N // Tc:,} samples in about {1000 * rC['mean']:.0f} ms, so that fixed cost becomes a larger share of the total. Modern processors also raise their clock frequency when few cores are busy and lower it when all cores are loaded, so the single-threaded baseline runs at a higher frequency than each thread of the parallel run, which lowers the measured speedup even for perfectly parallel work.{smt_txt} Finally, the operating system continues to schedule other processes and interrupts on the same CPUs, so the slowest thread determines the finishing time of the whole run, and any thread delayed by a context switch delays the join.

Memory bandwidth is not a significant limit for this program: each thread keeps its random state and counter in registers or the L1 cache and touches almost no shared memory. The losses therefore come from fixed thread-management costs, frequency scaling, shared execution resources and scheduling, which together produce the diminishing returns visible in the speedup curve.
"""

eff_T = []
for x in [1, 2, Tc, 2 * C, Tbig]:
    if row(x) is not None and x not in eff_T: eff_T.append(x)
eff_list = ", ".join(f"{float(row(t).efficiency):.2f} at T = {t}" for t in eff_T)
if Tsat > C and float(rC.speedup) >= 0.90 * Smax:
    T_rec, r_rec = Tc, rC
    rec_txt = (f"The best balance between speedup and resource use is at {Tc} threads, one per logical CPU: speedup there ({float(rC.speedup):.2f}) is within "
               f"{100 * (1 - float(rC.speedup) / Smax):.0f}% of the maximum, and the small extra gain at higher thread counts lies close to the run-to-run variation "
               f"while efficiency falls from {float(rC.efficiency):.2f} to {float(rsat.efficiency):.2f}.")
else:
    rec_txt = (f"The best balance between speedup and resource use is at about {Tsat} threads, where speedup ({float(rsat.speedup):.2f}) is within 5% of the "
               f"maximum and efficiency is still {float(rsat.efficiency):.2f}.")
E = f"""## E. Why Parallel Efficiency Declines as Threads Are Added

Parallel efficiency, E(T) = Speedup(T) / T, measures how much useful work each thread contributes relative to perfect scaling. The measured values are {eff_list}.

Below the number of logical CPUs, efficiency declines gradually because every added thread brings its own creation and joining cost, competes for shared execution resources and runs at a lower clock frequency than a single busy core, while its share of the work becomes smaller. Each thread therefore delivers somewhat less than one thread's worth of extra speed.

Beyond {C} threads, the decline becomes steep. The machine can execute at most {C} threads at the same instant, so speedup cannot exceed {C} however many threads are created, and efficiency is bounded by {C} / T. At {Tbig} threads the bound is {C / Tbig:.3f} and the measured efficiency is {float(rbig.efficiency):.3f}. Additional threads add no computing capacity; they only time-share the same CPUs, which adds context switches, scheduler work and thread start-up cost without increasing throughput.

{rec_txt} Creating more threads than this costs efficiency without a meaningful gain in execution time.
"""

table_txt = f"""## Measured Data for Approach 2

All configurations use N = {N:,} samples, seed 2024 and 5 runs each; T_single = {Ts:.4f} s. Mean coefficient of variation across configurations: {cv_mean:.1f}%.

{md_table(tab)}
"""
if cv_bad:
    table_txt += f"\nNote for the team: configurations with standard deviation above 10% of the mean: T = {', '.join(map(str, cv_bad))}. Consider re-running on a quieter system.\n"

FS = ""
if fs is not None:
    Tf = int(fs.threads.max())
    t_loc = float(fs[(fs.approach == "local") & (fs.threads == Tf)]["mean"].iloc[0])
    t_pad = float(fs[(fs.approach == "fs_padded") & (fs.threads == Tf)]["mean"].iloc[0])
    t_pak = float(fs[(fs.approach == "fs_packed") & (fs.threads == Tf)]["mean"].iloc[0])
    ratio = t_pak / t_pad
    rows_fs = ["| Threads | Local counter (s) | Padded array (s) | Packed array (s) | Packed / Padded |", "|---:|---:|---:|---:|---:|"]
    for T in sorted(fs.threads.unique()):
        v = {a: float(fs[(fs.approach == a) & (fs.threads == T)]["mean"].iloc[0]) for a in ["local", "fs_padded", "fs_packed"]}
        rows_fs.append(f"| {T} | {v['local']:.4f} | {v['fs_padded']:.4f} | {v['fs_packed']:.4f} | {v['fs_packed'] / v['fs_padded']:.2f} |")
    if ratio >= 1.10:
        fs_interp = (f"With {Tf} threads, the packed layout is {ratio:.2f} times slower than the padded one, although both perform exactly the same number of increments. "
                     "In the packed array, up to eight 8-byte counters fit in one 64-byte cache line; every increment by one thread invalidates that line in the caches of the other cores, "
                     "so the line moves back and forth between cores even though the threads never touch the same variable. This is false sharing.")
    else:
        fs_interp = (f"With {Tf} threads, the packed layout is only {ratio:.2f} times the time of the padded one, so no significant false-sharing penalty was observed on this machine. "
                     "Possible reasons are a small number of truly parallel cores or, in a virtual machine, vCPUs that the hypervisor places on hardware threads of the same physical core, which share one L1 cache.")
    FS = f"""## Supplementary Experiment: False Sharing in the Accumulation Step

To test why Approach 2 writes its result only once, two variants were measured that update a counter in a shared array on every hit: one with the counters packed next to each other (8 bytes each) and one with each counter padded to its own 64-byte cache line. Both variants declare the counters `volatile` so that every increment is really written to memory.

{chr(10).join(rows_fs)}

{fs_interp} The padded variant is still slower than the stack counter of Approach 2 ({t_pad:.4f} s versus {t_loc:.4f} s at {Tf} threads), because it stores to memory on every hit while the local counter stays in a register. The ranking register counter < private cache line < shared cache line supports the design choice of accumulating locally and publishing the result once.
"""

figs = """## Figures to Insert

- `tv2_figures/tv2_speedup.png` — Approach 2: Speedup vs Number of Threads, with the ideal line and the fitted Amdahl curve
- `tv2_figures/tv2_efficiency.png` — Approach 2: Parallel Efficiency vs Number of Threads, with the bound min(1, CPUs / T)
""" + ("- `tv2_figures/tv2_false_sharing.png` — Effect of False Sharing on Local Accumulation\n" if fs is not None else "")

out = os.path.join(D, "tv2_report_draft.md")
with open(out, "w") as fh:
    fh.write(f"# Approach 2 – Report Draft (generated from measurements on {machine})\n\n")
    fh.write("\n".join([design, A, E, table_txt, FS, figs]))
print(f"Ban nhap bao cao: {out}")
print(f"Do thi: {FIG}/")
print(f"Tom tat: C={C}, Smax={Smax:.2f} tai T={Tmax}, bao hoa T={Tsat}, Amdahl p={p_fit:.4f}, hieu suat T={Tc}: {float(rC.efficiency):.2f}")
