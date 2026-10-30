#!/usr/bin/env python3
"""Plots generated from measured data only: results/baseline_cal_tran.txt, metrics_baseline.json, pvt_summary_table.csv"""
import json, csv, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = pathlib.Path(__file__).resolve().parent.parent / "results"
(R / "plots").mkdir(exist_ok=True)
m = json.loads((R / "metrics_baseline.json").read_text())

names = open(R / "baseline_cal_tran.txt").readline().split()
d = np.loadtxt(R / "baseline_cal_tran.txt", skiprows=1)
t = d[:, 0] * 1e9
c = {n: d[:, i + 1] for i, n in enumerate(names[1:])}

# 1) 8 phases over a few output periods (after start-up)
Tout_ns = 1e3 / m["f_out_mhz"]
t0 = 14.0
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)
order = ["v(q1)", "v(q2)", "v(q3b)", "v(q4b)", "v(q1b)", "v(q2b)", "v(q3)", "v(q4)"]
for k, n in enumerate(order):
    msk = (t >= t0) & (t <= t0 + 3 * Tout_ns)
    ax.plot(t[msk], c[n][msk] + 2.0 * (7 - k), lw=1.2, label=n)
    ax.text(t0 - 0.1, 2.0 * (7 - k) + 0.9, n.upper(), ha="right", va="center", fontsize=8)
ax.set_xlabel("time (ns)"); ax.set_yticks([])
ax.set_title(f"8 outputs, f_in = {m['f_in_ghz']:.2f} GHz, f_out = {m['f_out_mhz']:.1f} MHz (stacked; sorted by measured phase)")
ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(R / "plots/baseline_8phases.png"); plt.close(fig)

# 2) measured phase vs ideal
ph = m["phase_deg"]
fig, ax = plt.subplots(figsize=(7, 4.2), dpi=300)
k = np.arange(8)
meas = np.array(list(ph.values()))
ax.plot(k, k * 45, "k--", label="ideal (45 deg steps)")
ax.plot(k, meas, "o-", color="#d97757", label="measured")
ax.set_xticks(k); ax.set_xticklabels(list(ph.keys()), rotation=30, fontsize=8)
ax.set_ylabel("phase vs Q1 rising edge (deg)")
ax.set_title(f"Measured phases; max step error {m['max_phase_step_error_deg']} deg")
ax.grid(alpha=.3); ax.legend(); fig.tight_layout(); fig.savefig(R / "plots/baseline_phase_error.png"); plt.close(fig)

# 3) PVT: delay and power vs VDD per corner/temp
rows = list(csv.DictReader(open(R / "pvt_summary_table.csv")))
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4), dpi=300)
for corner, col in (("TT", "#d97757"), ("FF", "#3b6ea5"), ("SS", "#4d7a4f")):
    for temp, ls in ((-40, ":"), (27, "-"), (125, "--")):
        r = [x for x in rows if x["Corner(synthetic)"] == corner and int(x["Temp_C"]) == temp and x["Divides"] == "PASS"]
        if not r: continue
        v = [float(x["VDD_V"]) for x in r]
        axs[0].plot(v, [float(x["Delay_ps"]) for x in r], ls, color=col, marker="o", ms=3, label=f"{corner} {temp}C")
        axs[1].plot(v, [float(x["Power_mW"]) for x in r], ls, color=col, marker="o", ms=3)
fails = 0
for x in rows:
    if x["Divides"] == "FAIL":
        axs[0].annotate(f"FAIL {x['Corner(synthetic)']} {x['Temp_C']}C {x['VDD_V']}V", (0.02, 0.04 + 0.05 * fails), xycoords="axes fraction", color="r", fontsize=7); fails += 1
axs[0].set_xlabel("VDD (V)"); axs[0].set_ylabel("CK to Q delay (ps)"); axs[1].set_xlabel("VDD (V)"); axs[1].set_ylabel("power (mW)")
axs[0].legend(fontsize=6, ncol=3); [a.grid(alpha=.3) for a in axs]
fig.suptitle("PVT sweep (synthetic corners on a generic LEVEL=1 deck; FAIL = does not divide by 2)", fontsize=9)
fig.tight_layout(); fig.savefig(R / "plots/pvt_delay_power.png"); plt.close(fig)
print("plots written")
