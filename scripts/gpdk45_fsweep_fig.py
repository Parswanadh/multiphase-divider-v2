#!/usr/bin/env python3
"""Phase-step error and power vs input frequency from the guest sweep TSVs (real Spectre runs)."""
import sys, re, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = pathlib.Path(__file__).resolve().parent.parent
F = R / "results/gpdk045/final"
series = [("fs_B.tsv", "B  m=4, R=2 kOhm", "#d97757"), ("fs_D.tsv", "D  m=4, R=3 kOhm", "#3b6ea5"), ("fs_E.tsv", "E  m=6, R=2 kOhm", "#4d7a4f")]
def rows(p):
    out = []
    for l in open(p):
        c = l.rstrip("\n").split("\t")
        if len(c) < 10 or c[0] == "tag" or c[0].startswith("__"):
            continue
        m = re.match(r"g_([\d.]+)G_", c[0])
        fin = float(m.group(1))
        out.append((fin, c[1] == "1", float(c[8]) if c[8] != "nan" else None, float(c[5]) if c[5] != "nan" else None))
    return sorted(out)
plt.rcParams["font.family"] = "serif"
fig, ax = plt.subplots(1, 2, figsize=(10, 4), dpi=300)
for f, lab, col in series:
    p = F / f
    if not p.exists():
        continue
    r = rows(p)
    ok = [x for x in r if x[1] and x[2] is not None]
    ax[0].plot([x[0] for x in ok], [x[2] for x in ok], "o-", color=col, label=lab)
    ax[1].plot([x[0] for x in ok], [x[3] for x in ok], "o-", color=col, label=lab)
    bad = [x for x in r if not x[1]]
    if bad:
        ax[0].plot([x[0] for x in bad], [0] * len(bad), "x", color="red", ms=8)
ax[0].set_xlabel("input frequency (GHz)"); ax[0].set_ylabel("max |phase step - 45 deg| (deg)")
ax[0].set_title("Phase-step error vs input frequency (red x: does not divide)", fontsize=9)
ax[1].set_xlabel("input frequency (GHz)"); ax[1].set_ylabel("average power (mW)")
ax[1].set_title("Power vs input frequency (tt, 27 C, 1.0 V)", fontsize=9)
for a in ax:
    a.grid(alpha=.3); a.legend(fontsize=7)
fig.tight_layout()
out = R / "report/gpdk045/figures/fig_fsweep.png"
fig.savefig(out); print("wrote", out)
