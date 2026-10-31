#!/usr/bin/env python3
"""PVT report for the gpdk045 multiphase divider (Spectre TSV -> CSV, JSON, figures).

Input is a guest-produced TSV with columns:
  tag,divides,f_in_GHz,f_out_MHz,ratio,power_mW,delay_ps,pdp_fJ,max_phase_step_err_deg,
  swing_lo,swing_hi,phases_deg,phase_steps_deg,periods_averaged,i_avg_mA,reason
where tag = <corner>_<temp>_<vdd>, corner in tt,ff,ss,fs,sf, temp in -40,27,125, vdd in 0.9,1.0,1.1.
A row passes when divides == 1, reason == "ok" and delay/power/PDP are finite. Everything else is FAIL
(kept in the CSV and drawn as failed). Grid cells with no row are reported as FAIL "missing row".

Usage:
  gpdk45_pvt_report.py --tsv FILE --label NAME [--fin-ghz X] [--outdir DIR] [--csvdir DIR]
  gpdk45_pvt_report.py --compare A.tsv B.tsv ...

Outputs (for --label NAME):
  <csvdir>/pvt_<NAME>.csv             full 45-row PVT table (FAIL rows kept)
  <csvdir>/pvt_summary_<NAME>.json    pass counts and min/max/typical over passing rows, failing corners
  <outdir>/fig_pvt_heatmap_<NAME>.png
  <outdir>/fig_pvt_delay_power_<NAME>.png
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from collections import OrderedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_OUTDIR = os.path.join(ROOT, "report", "gpdk045", "figures")
DEFAULT_CSVDIR = os.path.join(ROOT, "results", "gpdk045", "final")

CORNERS = ["tt", "ff", "ss", "fs", "sf"]
TEMPS = [-40, 27, 125]
VDDS = [0.9, 1.0, 1.1]
GRID = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]  # 45 points
TYPICAL = ("tt", 27, 1.0)
CORNER_COLOR = OrderedDict([
    ("tt", "#1f1f1f"),
    ("ff", "#2a6fb0"),
    ("ss", "#c0702a"),
    ("fs", "#4a9a4a"),
    ("sf", "#8a4fb0"),
])
TEMP_LS = {-40: "-", 27: "--", 125: ":"}
FAIL_COLOR = "#c81e1e"
PASS_CELL = "#9fd3a5"
FAIL_CELL = "#e3a09a"
REASON_MAX = 60

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 10,
    "savefig.dpi": 300,
})


# ----------------------------------------------------------------------------- parsing

def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def finite(x):
    return x is not None and math.isfinite(x)


def short_reason(reason, maxlen=REASON_MAX):
    """First clause of a Spectre reason, parenthetical notes removed, truncated."""
    r = (reason or "").strip()
    if not r:
        return "no reason given"
    if r == "ok":
        return "ok"
    first = r.split(";")[0]
    first = re.sub(r"\([^)]*\)", "", first)
    first = " ".join(first.split())
    if len(first) > maxlen:
        first = first[: maxlen - 3].rstrip() + "..."
    return first


def load_tsv(path):
    """Return (records keyed by grid point, list of unparsed tags).

    Records hold the grid point and metrics; a grid point with no row is filled as a missing FAIL.
    Rows whose tag is not a grid point are reported and ignored.
    """
    recs = {}
    unparsed = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tag = (row.get("tag") or "").strip()
            parts = tag.split("_")
            point = None
            if len(parts) == 3 and parts[0] in CORNERS:
                try:
                    point = (parts[0], int(parts[1]), float(parts[2]))
                except ValueError:
                    point = None
            if point not in GRID:
                unparsed.append(tag)
                continue
            if point in recs:
                raise ValueError(f"duplicate tag {tag} in {path}")
            try:
                divides = int(float(row.get("divides") or 0))
            except ValueError:
                divides = 0
            rec = {
                "corner": point[0], "temp": point[1], "vdd": point[2],
                "divides": divides,
                "f_out_MHz": fnum(row.get("f_out_MHz")),
                "delay_ps": fnum(row.get("delay_ps")),
                "power_mW": fnum(row.get("power_mW")),
                "pdp_fJ": fnum(row.get("pdp_fJ")),
                "phase_err_deg": fnum(row.get("max_phase_step_err_deg")),
                "reason_raw": (row.get("reason") or "").strip(),
            }
            metrics_ok = all(finite(rec[k]) for k in ("delay_ps", "power_mW", "pdp_fJ"))
            rec["pass"] = divides == 1 and rec["reason_raw"] == "ok" and metrics_ok
            if not rec["pass"]:
                if rec["reason_raw"] == "ok":
                    rec["reason_raw"] = "nan metrics"
                rec["reason"] = short_reason(rec["reason_raw"])
            else:
                rec["reason"] = "ok"
            recs[point] = rec
    for point in GRID:
        if point not in recs:
            recs[point] = {
                "corner": point[0], "temp": point[1], "vdd": point[2], "divides": 0,
                "f_out_MHz": float("nan"), "delay_ps": float("nan"), "power_mW": float("nan"),
                "pdp_fJ": float("nan"), "phase_err_deg": float("nan"),
                "reason_raw": "missing row", "reason": "missing row", "pass": False,
            }
    return recs, unparsed


def tag_of(point):
    c, t, v = point
    return f"{c}_{t}_{v:.1f}"


def fin_from_tsv(path):
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            x = fnum(row.get("f_in_GHz"))
            if finite(x):
                return x
    return float("nan")


# ----------------------------------------------------------------------------- summary

def count_by(recs, key, values):
    out = OrderedDict()
    for v in values:
        pts = [r for r in recs.values() if r[key] == v]
        out[str(v)] = {"pass": sum(1 for r in pts if r["pass"]), "total": len(pts)}
    return out


def metric_stats(recs, key):
    passing = [(r[key], p) for p, r in recs.items() if r["pass"]]
    if not passing:
        return {"min": None, "min_at": None, "max": None, "max_at": None, "typical": None}
    lo = min(passing, key=lambda x: x[0])
    hi = max(passing, key=lambda x: x[0])
    typ = recs.get(TYPICAL)
    return {
        "min": lo[0], "min_at": tag_of(lo[1]),
        "max": hi[0], "max_at": tag_of(hi[1]),
        "typical": typ[key] if typ and typ["pass"] else None,
    }


def build_summary(recs, label, fin, source, unparsed):
    n_pass = sum(1 for r in recs.values() if r["pass"])
    failing = [
        {"tag": tag_of(p), "corner": r["corner"], "temp_C": r["temp"], "vdd_V": r["vdd"],
         "reason": r["reason"]}
        for p, r in recs.items() if not r["pass"]
    ]
    typ = recs.get(TYPICAL)
    return OrderedDict([
        ("label", label),
        ("source_tsv", os.path.basename(source)),
        ("f_in_GHz", fin),
        ("pass_count", n_pass),
        ("total", len(GRID)),
        ("pass_by_temp_C", count_by(recs, "temp", TEMPS)),
        ("pass_by_vdd_V", count_by(recs, "vdd", VDDS)),
        ("pass_by_corner", count_by(recs, "corner", CORNERS)),
        ("passing_metrics", OrderedDict([
            ("power_mW", metric_stats(recs, "power_mW")),
            ("delay_ps", metric_stats(recs, "delay_ps")),
            ("pdp_fJ", metric_stats(recs, "pdp_fJ")),
        ])),
        ("typical_point", tag_of(TYPICAL)),
        ("typical_status", "pass" if typ and typ["pass"] else "fail or missing"),
        ("failing", failing),
        ("unparsed_tags", unparsed),
    ])


def write_csv(recs, path):
    header = ["Corner", "Temp_C", "VDD_V", "Divides", "f_out_MHz", "Delay_ps", "Power_mW", "PDP_fJ",
              "MaxPhaseStepErr_deg", "Reason"]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for p in GRID:
            r = recs[p]
            w.writerow([r["corner"], r["temp"], f"{r['vdd']:g}", r["divides"],
                        f"{r['f_out_MHz']:.3f}" if finite(r["f_out_MHz"]) else "nan",
                        f"{r['delay_ps']:.2f}" if finite(r["delay_ps"]) else "nan",
                        f"{r['power_mW']:.6f}" if finite(r["power_mW"]) else "nan",
                        f"{r['pdp_fJ']:.3f}" if finite(r["pdp_fJ"]) else "nan",
                        f"{r['phase_err_deg']:.3f}" if finite(r["phase_err_deg"]) else "nan",
                        r["reason"]])


# ----------------------------------------------------------------------------- figures

def fig_heatmap(recs, label, fin, outdir):
    cells = [(t, v) for t in TEMPS for v in VDDS]
    grid = np.zeros((len(CORNERS), len(cells)))
    for i, c in enumerate(CORNERS):
        for j, (t, v) in enumerate(cells):
            grid[i, j] = 1.0 if recs[(c, t, v)]["pass"] else 0.0
    n_pass = int(grid.sum())
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    ax.imshow(grid, cmap=ListedColormap([FAIL_CELL, PASS_CELL]), vmin=0, vmax=1, aspect="auto")
    for i, c in enumerate(CORNERS):
        for j, (t, v) in enumerate(cells):
            r = recs[(c, t, v)]
            if r["pass"]:
                txt = f"{r['delay_ps']:.1f} ps"
            else:
                txt = "FAIL"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="black" if r["pass"] else FAIL_COLOR,
                    fontweight="normal" if r["pass"] else "bold")
    for j in (2.5, 5.5):
        ax.axvline(j, color="white", lw=2.5)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels([f"{t} °C\n{v:.1f} V" for t, v in cells], fontsize=8)
    ax.set_yticks(range(len(CORNERS)))
    ax.set_yticklabels([c.upper() for c in CORNERS], fontsize=8)
    ax.set_ylabel("Process corner")
    ax.set_xlabel("Temperature and supply voltage")
    ax.set_title(f"PVT pass/fail map, design {label}, f_in = {fin:g} GHz ({n_pass}/{len(GRID)} pass)")
    fig.text(0.5, 0.01,
             "Green: pass, cell text is propagation delay. Red: FAIL (wrong divide ratio or output not toggling).",
             ha="center", fontsize=7, color="0.25")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    path = os.path.join(outdir, f"fig_pvt_heatmap_{label}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


def fig_delay_power(recs, label, fin, outdir):
    fig, (axd, axp) = plt.subplots(1, 2, figsize=(8.4, 4.3), sharex=True)
    panels = [(axd, "delay_ps", "Propagation delay (ps)", "Delay"),
              (axp, "power_mW", "Power (mW)", "Power")]
    for ax, key, ylabel, title in panels:
        pass_vals = [r[key] for r in recs.values() if r["pass"]]
        lo = min(pass_vals) if pass_vals else 0.0
        hi = max(pass_vals) if pass_vals else 1.0
        span = (hi - lo) if hi > lo else max(abs(hi), 1.0) * 0.2
        fail_by_vdd = {v: [] for v in VDDS}
        for c in CORNERS:
            for t in TEMPS:
                xs, ys = [], []
                for v in VDDS:
                    r = recs[(c, t, v)]
                    if r["pass"]:
                        xs.append(v)
                        ys.append(r[key])
                    else:
                        fail_by_vdd[v].append((c, t))
                if xs:
                    ax.plot(xs, ys, color=CORNER_COLOR[c], ls=TEMP_LS[t], lw=1.4, marker="o", ms=3.5)
        # Failed points sit in a band below the data, stacked per supply, labelled corner/temp.
        band_top = lo - 0.10 * span
        step = 0.09 * span
        max_k = 0
        for v, items in fail_by_vdd.items():
            for k, (c, t) in enumerate(items):
                y = band_top - k * step
                max_k = max(max_k, k)
                ax.scatter([v], [y], marker="x", s=30, color=FAIL_COLOR, linewidths=1.4, zorder=5)
                ax.annotate(f"{c}/{t}", (v, y), xytext=(4, 0), textcoords="offset points",
                            fontsize=6, va="center", color=FAIL_COLOR)
        bottom = band_top - (max_k + 1) * step - 0.05 * span
        ax.axhline(band_top + 0.45 * step, color="0.7", lw=0.6)
        ax.set_ylim(bottom, hi + 0.12 * span)
        ax.set_xlim(0.85, 1.15)
        ax.set_xticks(VDDS)
        ax.set_xlabel("VDD (V)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, color="0.9", lw=0.6)
        ax.set_axisbelow(True)

    handles = [Line2D([], [], color=CORNER_COLOR[c], lw=1.6, label=c.upper()) for c in CORNERS]
    handles += [Line2D([], [], color="0.2", ls=TEMP_LS[t], lw=1.4, label=f"{t} °C") for t in TEMPS]
    handles += [Line2D([], [], color=FAIL_COLOR, marker="x", ls="", ms=6, mew=1.4, label="FAIL")]
    fig.legend(handles=handles, loc="lower center", ncol=9, frameon=False, fontsize=7.5,
               bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"Delay and power vs. supply voltage, design {label}, f_in = {fin:g} GHz "
                 f"(passing points; FAIL marked below the data)", fontsize=10)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    path = os.path.join(outdir, f"fig_pvt_delay_power_{label}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------------- CLI

def run_one(tsv, label, fin_arg, outdir, csvdir):
    if not os.path.exists(tsv):
        print(f"NOTE: {tsv} not found; nothing written for label {label}.")
        return 0
    recs, unparsed = load_tsv(tsv)
    fin = fin_arg if fin_arg is not None else fin_from_tsv(tsv)
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(csvdir, exist_ok=True)

    csv_path = os.path.join(csvdir, f"pvt_{label}.csv")
    write_csv(recs, csv_path)
    summary = build_summary(recs, label, fin, tsv, unparsed)
    json_path = os.path.join(csvdir, f"pvt_summary_{label}.json")
    with open(json_path, "w") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    hm = fig_heatmap(recs, label, fin, outdir)
    dp = fig_delay_power(recs, label, fin, outdir)

    print(f"{label}: pass {summary['pass_count']}/{summary['total']} (f_in {fin:g} GHz)")
    for c in CORNERS:
        d = summary["pass_by_corner"][c]
        print(f"  corner {c}: {d['pass']}/{d['total']}")
    for f in summary["failing"]:
        print(f"  FAIL {f['tag']}: {f['reason']}")
    if unparsed:
        print(f"  WARNING: {len(unparsed)} row(s) with unrecognised tag ignored: {unparsed}")
    for p in (csv_path, json_path, hm, dp):
        print(f"  wrote {p}")
    return 0


def compare_table(paths):
    lines = ["| Design | Pass (of 45) | -40 °C | 27 °C | 125 °C | Failing tags |",
             "|---|---|---|---|---|---|"]
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        if not os.path.exists(p):
            lines.append(f"| {name} | not found | - | - | - | - |")
            continue
        recs, _ = load_tsv(p)
        n = sum(1 for r in recs.values() if r["pass"])
        per_t = [sum(1 for r in recs.values() if r["pass"] and r["temp"] == t) for t in TEMPS]
        fails = [tag_of(k) for k, r in recs.items() if not r["pass"]]
        fail_txt = ", ".join(fails) if fails else "none"
        lines.append(f"| {name} | {n} | {per_t[0]}/15 | {per_t[1]}/15 | {per_t[2]}/15 | {fail_txt} |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tsv", help="PVT TSV from the guest run")
    ap.add_argument("--label", help="design label, e.g. D_1p4")
    ap.add_argument("--fin-ghz", type=float, default=None,
                    help="input frequency in GHz for titles (default: f_in_GHz column)")
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR, help="figure directory")
    ap.add_argument("--csvdir", default=DEFAULT_CSVDIR, help="CSV/JSON directory")
    ap.add_argument("--compare", nargs="+", metavar="TSV",
                    help="print a markdown table of pass counts for several TSV files")
    args = ap.parse_args(argv)

    if args.compare:
        print(compare_table(args.compare))
        return 0
    if not args.tsv or not args.label:
        ap.error("--tsv and --label are required (or use --compare)")
    return run_one(args.tsv, args.label, args.fin_ghz, args.outdir, args.csvdir)


if __name__ == "__main__":
    sys.exit(main())
