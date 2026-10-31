#!/usr/bin/env python3
"""Re-draw the delay/power-versus-supply PVT figures with the y axis clamped at 0.

gpdk45_pvt_report.fig_delay_power puts the FAIL markers in a band below the data, which pushes
the power axis to negative values. This script draws the passing points as lines and shows the
failing points only as a red cross at the foot of the plot, with the count of failing points per
supply voltage (the individual failing corners are listed in the PVT table of the report).
Nothing in results/ is written; only report/gpdk045/figures/fig_pvt_delay_power_<label>.png.

Usage: gpdk45_pvt_replot.py [--finals DIR] [--outdir DIR]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gpdk45_pvt_report as pr  # noqa: E402

plt, Line2D = pr.plt, pr.Line2D

JOBS = [("pvt_D.tsv", "D_1p4"), ("pvt_B.tsv", "B_1p4"), ("pvt_E.tsv", "E_1p4"), ("pvt_B6.tsv", "B_6g")]


def fig_delay_power_clamped(recs, label, fin, outdir):
    fig, (axd, axp) = plt.subplots(1, 2, figsize=(8.4, 4.3), sharex=True)
    panels = [(axd, "delay_ps", "Propagation delay (ps)", "Delay"),
              (axp, "power_mW", "Power (mW)", "Power")]
    for ax, key, ylabel, title in panels:
        hi = max([r[key] for r in recs.values() if r["pass"]] or [1.0])
        for c in pr.CORNERS:
            for t in pr.TEMPS:
                xs = [v for v in pr.VDDS if recs[(c, t, v)]["pass"]]
                ys = [recs[(c, t, v)][key] for v in xs]
                if xs:
                    ax.plot(xs, ys, color=pr.CORNER_COLOR[c], ls=pr.TEMP_LS[t], lw=1.4,
                            marker="o", ms=3.5)
        top = hi * 1.12
        ax.set_ylim(0, top)
        for v in pr.VDDS:
            n_fail = sum(1 for c in pr.CORNERS for t in pr.TEMPS if not recs[(c, t, v)]["pass"])
            if n_fail:
                ax.scatter([v], [0.035 * top], marker="x", s=30, color=pr.FAIL_COLOR,
                           linewidths=1.4, zorder=5, clip_on=False)
                ax.annotate(f"{n_fail} FAIL", (v, 0.035 * top), xytext=(5, 0),
                            textcoords="offset points", fontsize=6.5, va="center",
                            color=pr.FAIL_COLOR)
        ax.set_xlim(0.85, 1.15)
        ax.set_xticks(pr.VDDS)
        ax.set_xlabel("VDD (V)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, color="0.9", lw=0.6)
        ax.set_axisbelow(True)
    handles = [Line2D([], [], color=pr.CORNER_COLOR[c], lw=1.6, label=c.upper()) for c in pr.CORNERS]
    handles += [Line2D([], [], color="0.2", ls=pr.TEMP_LS[t], lw=1.4, label=f"{t} °C") for t in pr.TEMPS]
    handles += [Line2D([], [], color=pr.FAIL_COLOR, marker="x", ls="", ms=6, mew=1.4,
                       label="count of failing points")]
    fig.legend(handles=handles, loc="lower center", ncol=9, frameon=False, fontsize=7.5,
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"Delay and power vs. supply voltage, design {label}, f_in = {fin:g} GHz "
                 f"(lines: passing points; red cross: failing points at that supply)", fontsize=10)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    path = os.path.join(outdir, f"fig_pvt_delay_power_{label}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--finals", default=pr.DEFAULT_CSVDIR)
    ap.add_argument("--outdir", default=pr.DEFAULT_OUTDIR)
    args = ap.parse_args(argv)
    for tsv, label in JOBS:
        path = os.path.join(args.finals, tsv)
        recs, _ = pr.load_tsv(path)
        print("wrote", fig_delay_power_clamped(recs, label, pr.fin_from_tsv(path), args.outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
