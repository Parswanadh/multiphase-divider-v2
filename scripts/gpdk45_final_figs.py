#!/usr/bin/env python3
"""Figures and analysis.json for the final gpdk045 Spectre runs of the 8-phase divider.

Inputs (all measured by Spectre 12.1 inside the Cadence VM):
  FINALS/{unsized,D_1p4,B_6g}.raw   nutmeg ASCII transient (read with spectre_raw._parse_plot)
  FINALS/{unsized,D_1p4,B_6g}.tsv   one-row summary per design (the numbers quoted in the report)

Outputs (OUTDIR):
  fig_tran_D_1p4.png, fig_tran_B_6g.png     CK + 8 outputs, sorted by measured phase, 3 output periods
  fig_tran_unsized.png                      CK, Q1, Q1b of the non-dividing unsized design
  fig_phase_steps.png                       8 adjacent phase steps vs the ideal 45 deg
  fig_tail_saturation_D_1p4.png / _B_6g.png V(XD1.tail) over 3 output periods, optional Vdsat line
  fig_supply_current.png                    supply current drawn, 2 output periods per design
  JSON                                      FINALS/analysis.json (or --json)

Conventions:
  settle = 10 ns; plot window start = max(10 ns, 15 output periods); steady state = t >= 10 ns.
  Edges are found at the mid-swing of each signal's own steady-state levels (linear interpolation),
  as in measure_tran.py. Supply current is drawn = -V(VDD:p); means are time-weighted (trapezoid).
  Nothing is hard-coded from the measurements: every plotted or printed number comes from the data.

Usage: gpdk45_final_figs.py [--finals DIR] [--outdir DIR] [--vdsat V] [--json PATH]
"""
import argparse
import csv
import json
import math
import os
import re
import sys

# -I strips the script directory from sys.path; add it so spectre_raw can be imported.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

import spectre_raw as sr  # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_FINALS = os.path.join(ROOT, "results", "gpdk045", "final")
DEFAULT_OUTDIR = os.path.join(ROOT, "report", "gpdk045", "figures")

DESIGNS = ["unsized", "D_1p4", "B_6g"]
DIVIDERS = ["D_1p4", "B_6g"]
DESC = {
    "unsized": "unsized: unit devices m = 1, R = 1.15 kΩ, 1.4 GHz in",
    "D_1p4": "D_1p4: m = 4, R = 3 kΩ, vb = 1.0 V, 1.4 GHz in",
    "B_6g": "B_6g: m = 4, R = 2 kΩ, vb = 1.0 V, 6 GHz in",
}
OUT_NODES = ["q1", "q2", "q3", "q4", "q1b", "q2b", "q3b", "q4b"]
ORANGE, BLUE, GREEN = "#d97757", "#3b6ea5", "#4d7a4f"
SETTLE_S = 10e-9
START_PERIODS = 15
PLOT_PERIODS = 3
CURRENT_PERIODS = 2
VDD = 1.0
TOL = 0.01  # relative tolerance for the mean-current check


def pick_font():
    have = {f.name for f in font_manager.fontManager.ttflist}
    for cand in ["Times New Roman", "Liberation Serif", "DejaVu Serif"]:
        if cand in have:
            return cand
    return "DejaVu Serif"


def setup_style():
    fam = pick_font()
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": [fam, "Liberation Serif", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })
    return fam


# ----------------------------------------------------------------- input parsing
def raw_columns(path):
    """All variables of the transient plot in a nutascii raw file, keyed by lower-case name."""
    with open(path, errors="replace") as f:
        text = f.read().splitlines()
    starts = [k for k, l in enumerate(text) if l.startswith("Title:")]
    if not starts:
        raise ValueError(f"{path}: not a nutmeg raw file")
    starts.append(len(text))
    chosen = None
    for a, b in zip(starts[:-1], starts[1:]):
        blk = text[a:b]
        plot = next((l.split(":", 1)[1].strip() for l in blk if l.startswith("Plotname:")), "")
        if re.search("tran", plot, re.I):
            chosen = blk
            break
    if chosen is None:
        raise ValueError(f"{path}: no transient plot")
    _, names, data = sr._parse_plot(chosen)
    return {n.lower(): data[:, j] for j, n in enumerate(names)}


def _num(s):
    v = float(s)
    return v if math.isfinite(v) else None


def read_tsv(path):
    with open(path) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 1:
        raise ValueError(f"{path}: expected one row, found {len(rows)}")
    r = rows[0]
    out = {"tag": r["tag"], "divides": r["divides"].strip() == "1", "reason": r["reason"]}
    for k in ["f_in_GHz", "f_out_MHz", "ratio", "power_mW", "delay_ps", "pdp_fJ",
              "max_phase_step_err_deg", "swing_lo", "swing_hi", "i_avg_mA"]:
        out[k] = _num(r[k])
    out["periods_averaged"] = _num(r["periods_averaged"])
    out["phase_steps_deg"] = (None if r["phase_steps_deg"] == "nan"
                              else [float(x) for x in r["phase_steps_deg"].split(",")])
    if r["phases_deg"] == "nan":
        out["phases_deg"] = None
    else:
        out["phases_deg"] = [(p.split(":")[0].strip().lower(), float(p.split(":")[1]))
                             for p in r["phases_deg"].split(",")]
    return out


# ----------------------------------------------------------------- measurements
def crossings(t, x, level, rising):
    x0, x1 = x[:-1], x[1:]
    if rising:
        idx = np.nonzero((x0 < level) & (x1 >= level))[0]
    else:
        idx = np.nonzero((x0 > level) & (x1 <= level))[0]
    return t[idx] + (level - x0[idx]) * (t[idx + 1] - t[idx]) / (x1[idx] - x0[idx])


def window_mean(t, y, a, b):
    """Time-weighted mean of y over [a, b], with interpolated end points."""
    inner = (t > a) & (t < b)
    ta = np.concatenate([[a], t[inner], [b]])
    ya = np.interp(ta, t, y)
    return float(np.trapezoid(ya, ta) / (b - a))


def steady_edges(t, x, lo, hi, rising):
    mid = (lo + hi) / 2
    c = crossings(t, x, mid, rising)
    return c[c >= SETTLE_S]


def transition_times(t, x, lo, hi, tper, rise_edges, fall_edges):
    """Mean 10-90 % rise and fall times (s) over the steady-state edges."""
    sw = hi - lo
    l10, l90 = lo + 0.1 * sw, lo + 0.9 * sw
    r10 = crossings(t, x, l10, True)
    r90 = crossings(t, x, l90, True)
    f90 = crossings(t, x, l90, False)
    f10 = crossings(t, x, l10, False)
    rise, fall = [], []
    for tm in rise_edges:
        a = r10[(r10 < tm) & (r10 > tm - tper / 2)]
        b = r90[(r90 > tm) & (r90 < tm + tper / 2)]
        if len(a) and len(b):
            rise.append(b[0] - a[-1])
    for tf in fall_edges:
        a = f90[(f90 < tf) & (f90 > tf - tper / 2)]
        b = f10[(f10 > tf) & (f10 < tf + tper / 2)]
        if len(a) and len(b):
            fall.append(b[0] - a[-1])
    return rise, fall


def measure_design(name, finals):
    raw = os.path.join(finals, name + ".raw")
    tsv = read_tsv(os.path.join(finals, name + ".tsv"))
    cols = raw_columns(raw)
    t = cols["time"]
    st = t >= SETTLE_S
    lo_hi = {k: (cols[k][st].min(), cols[k][st].max()) for k in cols if k != "time"}
    mid = {k: (lo_hi[k][0] + lo_hi[k][1]) / 2 for k in lo_hi}

    q1r = steady_edges(t, cols["q1"], *lo_hi["q1"], True)
    q1f = steady_edges(t, cols["q1"], *lo_hi["q1"], False)
    ckr = steady_edges(t, cols["ck"], *lo_hi["ck"], True)
    if len(q1r) < 4 or len(ckr) < 4:
        raise RuntimeError(f"{name}: too few edges (Q1 {len(q1r)}, CK {len(ckr)})")
    tper = float(np.mean(np.diff(q1r)))
    t0 = max(SETTLE_S, START_PERIODS * tper)
    t1 = t0 + PLOT_PERIODS * tper
    if t1 > t[-1]:
        raise RuntimeError(f"{name}: plot window ends after simulation end")

    i_drawn = -cols["vdd:p"]
    xd1, xd2 = cols["xd1.tail"], cols["xd2.tail"]
    m = {
        "tag": tsv["tag"],
        "tsv": tsv,
        "window_start_ns": t0 * 1e9,
        "plot_window_ns": [t0 * 1e9, t1 * 1e9],
        "steady_state_window_ns": [SETTLE_S * 1e9, float(t[-1] * 1e9)],
        "q1_min_v": float(lo_hi["q1"][0]),
        "q1_max_v": float(lo_hi["q1"][1]),
        "xd1_tail_min_v": float(xd1[st].min()),
        "xd1_tail_max_v": float(xd1[st].max()),
        "xd2_tail_min_v": float(xd2[st].min()),
        "xd2_tail_max_v": float(xd2[st].max()),
        "supply_peak_ma_steady": float(i_drawn[st].max() * 1e3),
        "supply_peak_ma_all_time_incl_startup": float(i_drawn.max() * 1e3),
        "supply_avg_ma_steady": window_mean(t, i_drawn, SETTLE_S, t[-1]) * 1e3,
        "supply_avg_ma_2_periods": window_mean(t, i_drawn, t0, t0 + CURRENT_PERIODS * tper) * 1e3,
    }
    ctx = {"t": t, "cols": cols, "t0": t0, "t1": t1, "tper": tper, "tsv": tsv,
           "lo_hi": lo_hi, "i_drawn": i_drawn}

    # Divider-only metrics. The unsized design does not divide, so these are n/a for it.
    if name in DIVIDERS:
        if not tsv["divides"]:
            raise RuntimeError(f"{name}: tsv says it does not divide")
        f_meas = 1 / tper / 1e6
        if abs(f_meas - tsv["f_out_MHz"]) / tsv["f_out_MHz"] > 0.005:
            raise RuntimeError(f"{name}: measured f_out {f_meas} vs tsv {tsv['f_out_MHz']}")
        ref = q1r[2]
        phases = {}
        out_edges = []
        for n in OUT_NODES:
            e = steady_edges(t, cols[n], *lo_hi[n], True)
            out_edges.append(e)
            phases[n] = float(((e[np.searchsorted(e, ref)] - ref) / tper * 360) % 360)
        order = sorted(phases, key=phases.get)
        tsv_order = [p for p, _ in tsv["phases_deg"]]
        if order != tsv_order:
            raise RuntimeError(f"{name}: phase order {order} != tsv order {tsv_order}")
        dev = max(abs(phases[p] - v) for p, v in tsv["phases_deg"])
        if dev > 0.5:
            raise RuntimeError(f"{name}: computed phases deviate from tsv by {dev:.3f} deg")
        def ck_prev(e):
            return ckr[ckr <= e][-1]  # latest CK rising edge at or before e

        first = ck_prev(q1r[0])
        delay_first = float((q1r[0] - first) * 1e12)
        delay_mean = float(np.mean([e - ck_prev(e) for e in q1r]) * 1e12)
        # same definition as scripts/measure_tran.py (and so the tsv delay_ps): each CK rising
        # edge to the next rising edge on any of the 8 outputs, averaged over CK edges
        alle = np.sort(np.concatenate(out_edges))
        d_any = [alle[np.searchsorted(alle, c)] - c for c in ckr
                 if np.searchsorted(alle, c) < len(alle)]
        delay_any = float(np.mean(d_any) * 1e12)
        if tsv["delay_ps"] is not None and abs(delay_any - tsv["delay_ps"]) > 0.05:
            raise RuntimeError(f"{name}: CK->any-output delay {delay_any:.3f} ps vs tsv "
                               f"{tsv['delay_ps']:.3f} ps")
        rise, fall = transition_times(t, cols["q1"], *lo_hi["q1"], tper,
                                      q1r, q1f)
        m.update({
            "f_out_measured_mhz": f_meas,
            "phase_deg_measured": {p: round(phases[p], 3) for p in order},
            "phase_order_matches_tsv": True,
            "phase_max_dev_from_tsv_deg": float(dev),
            "ck_to_q1_first_edge_delay_ps": delay_first,
            "ck_to_q1_mean_delay_ps": delay_mean,
            "ck_to_any_output_mean_delay_ps": delay_any,
            "q1_rise_10_90_ps": float(np.mean(rise) * 1e12),
            "q1_fall_10_90_ps": float(np.mean(fall) * 1e12),
            "q1_rise_fall_edges": [len(rise), len(fall)],
        })
        ctx["phases"] = phases
        ctx["order"] = order
        ctx["q1r"] = q1r
    else:
        m.update({k: None for k in ["f_out_measured_mhz", "phase_deg_measured",
                                    "phase_order_matches_tsv", "phase_max_dev_from_tsv_deg",
                                    "ck_to_q1_first_edge_delay_ps", "ck_to_q1_mean_delay_ps",
                                    "ck_to_any_output_mean_delay_ps",
                                    "q1_rise_10_90_ps", "q1_fall_10_90_ps",
                                    "q1_rise_fall_edges"]})

    # Current checks against the tsv average (the tsv average is the authority for the report).
    if tsv["i_avg_mA"] is not None:
        ref_i = tsv["i_avg_mA"]
        for key in ["supply_avg_ma_steady", "supply_avg_ma_2_periods"]:
            rel = abs(m[key] - ref_i) / ref_i
            m[key.replace("_ma_", "_vs_tsv_rel_err_")] = float(rel)
            if rel > TOL:
                raise AssertionError(f"{name}: {key} {m[key]:.6f} mA differs from tsv "
                                     f"{ref_i:.6f} mA by {rel*100:.2f} % (> 1 %)")
    return m, ctx


# ----------------------------------------------------------------- figures
def save(fig, path):
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


def plot_tran_divider(name, m, ctx, outdir):
    cols, t, t0, t1, tper = ctx["cols"], ctx["t"], ctx["t0"], ctx["t1"], ctx["tper"]
    win = (t >= t0) & (t <= t1)
    tw = t[win]  # absolute time
    rows = [("CK", "ck", ORANGE, None)]
    for p in ctx["order"]:
        color = BLUE if not p.endswith("b") else GREEN
        rows.append((p.upper(), p, color, ctx["phases"][p]))
    fig, axes = plt.subplots(len(rows), 1, sharex=True, figsize=(7.2, 10.8))
    fig.subplots_adjust(left=0.14, right=0.86, top=0.925, bottom=0.06, hspace=0.12)
    # ideal 45 deg grid: edges at Q1 rising + k * T/8
    q1r = ctx["q1r"]
    ref = q1r[np.searchsorted(q1r, t0)]
    kmin = int(np.ceil((t0 - ref) / (tper / 8)))
    kmax = int(np.floor((t1 - ref) / (tper / 8)))
    grid = [(ref + k * tper / 8) * 1e9 for k in range(kmin, kmax + 1)]
    for ax, (label, key, color, ph) in zip(axes, rows):
        y = cols[key][win]
        ax.plot(tw * 1e9, y, color=color, lw=1.1)
        lo, hi = y.min(), y.max()
        pad = 0.12 * (hi - lo)
        ax.set_ylim(lo - pad, hi + pad)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.set_ylabel(f"{label}\n(V)", rotation=0, ha="right", va="center")
        ax.tick_params(labelsize=8)
        for g in grid:
            ax.axvline(g, color="#b5b5b5", lw=0.6, ls="--", zorder=0)
        if ph is not None:
            ax.text(1.015, 0.5, f"phase\n{ph:.2f}°", transform=ax.transAxes,
                    ha="left", va="center", fontsize=8)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
    axes[0].text(1.015, 0.5, f"f_in\n{m['tsv']['f_in_GHz']:.2f}\nGHz", transform=axes[0].transAxes,
                 ha="left", va="center", fontsize=8)
    axes[-1].set_xlabel("time (ns)")
    axes[-1].set_xlim(t0 * 1e9, t1 * 1e9)
    fig.suptitle(
        f"Transient of the gpdk045 8-phase divider, {DESC[name]}, VDD = {VDD:.1f} V.\n"
        f"Output {m['tsv']['f_out_MHz']:.1f} MHz; three output periods after settle "
        f"(start {t0*1e9:.2f} ns). Traces sorted by measured phase; dashed lines: ideal 45° grid.",
        fontsize=9, y=0.985)
    save(fig, os.path.join(outdir, f"fig_tran_{name}.png"))


def plot_tran_unsized(m, ctx, outdir):
    cols, t, t0, t1 = ctx["cols"], ctx["t"], ctx["t0"], ctx["t1"]
    win = (t >= t0) & (t <= t1)
    tw = t[win] * 1e9
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(7.2, 6.4))
    fig.subplots_adjust(left=0.15, right=0.97, top=0.9, bottom=0.10, hspace=0.18)
    spec = [("CK", "ck", ORANGE), ("Q1", "q1", BLUE), ("Q1b", "q1b", GREEN)]
    swing_mv = (ctx["lo_hi"]["q1"][1] - ctx["lo_hi"]["q1"][0]) * 1e3
    for ax, (label, key, color) in zip(axes, spec):
        y = cols[key][win]
        ax.plot(tw, y, color=color, lw=1.1)
        if key == "ck":
            lo, hi = y.min(), y.max()
            pad = 0.1 * (hi - lo)
            ax.set_ylim(lo - pad, hi + pad)
        else:
            lo, hi = ctx["lo_hi"][key]
            pad = 0.25 * (hi - lo)
            ax.set_ylim(lo - pad, hi + pad)
            ax.text(0.99, 0.92, f"steady swing {(hi - lo) * 1e3:.1f} mV",
                    transform=ax.transAxes, ha="right", va="top", fontsize=8,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.set_ylabel(f"{label}\n(V)", rotation=0, ha="right", va="center")
        ax.tick_params(labelsize=8)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
    axes[-1].set_xlabel("time (ns)")
    axes[-1].set_xlim(t0 * 1e9, t1 * 1e9)
    fig.suptitle(
        f"Unsized divider, {DESC['unsized']}, VDD = {VDD:.1f} V: the outputs do not divide.\n"
        f"Q1 follows the clock at {m['tsv']['f_out_MHz']:.1f} MHz with a steady swing of "
        f"{swing_mv:.1f} mV (Q1 zoomed; {PLOT_PERIODS} output periods shown).",
        fontsize=9, y=0.985)
    save(fig, os.path.join(outdir, "fig_tran_unsized.png"))


def plot_phase_steps(all_m, outdir):
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.31)
    x = np.arange(8)
    width = 0.38
    colors = {"D_1p4": BLUE, "B_6g": GREEN}
    labels = None
    for j, name in enumerate(DIVIDERS):
        tsv = all_m[name]["tsv"]
        steps = tsv["phase_steps_deg"]
        if len(steps) != 8:
            raise RuntimeError(f"{name}: expected 8 phase steps")
        order = [p for p, _ in tsv["phases_deg"]]
        if labels is None:
            labels = [f"{order[k].upper()}→{order[(k + 1) % 8].upper()}" for k in range(8)]
        xs = x + (j - 0.5) * width
        bars = ax.bar(xs, steps, width, color=colors[name], label=(
            f"{name} ({tsv['f_in_GHz']:.1f} GHz in, {tsv['f_out_MHz']:.0f} MHz out), "
            f"max error {tsv['max_phase_step_err_deg']:.2f}°"))
        for b, v in zip(bars, steps):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.2f}", ha="center",
                    va="bottom", fontsize=7)
    ax.axhline(45, color=ORANGE, lw=1.4, ls="--", label="ideal 45°")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_xlabel("adjacent output pair (measured phase order)")
    ax.set_ylabel("phase step (deg)")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30),
              ncol=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.suptitle("Adjacent phase steps of the 8 divider outputs, from the measured "
                 "phases (tsv), vs the ideal 45° step", fontsize=9, y=0.985)
    save(fig, os.path.join(outdir, "fig_phase_steps.png"))


def plot_tail(name, ctx, m, vdsat, outdir):
    t, cols, t0, t1 = ctx["t"], ctx["cols"], ctx["t0"], ctx["t1"]
    win = (t >= t0) & (t <= t1)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.14)
    ax.plot((t[win]) * 1e9, cols["xd1.tail"][win], color=BLUE, lw=1.2,
            label=f"V(XD1.tail), steady state min {m['xd1_tail_min_v']*1e3:.2f} mV, "
                  f"max {m['xd1_tail_max_v']*1e3:.2f} mV")
    if vdsat is not None:
        ax.axhline(vdsat, color=ORANGE, lw=1.3, ls="--", label=f"Vdsat = {vdsat:.3f} V")
        title_v = f"Vdsat = {vdsat:.3f} V (dashed line)"
    else:
        title_v = "Vdsat not provided"
    ax.set_xlim(t0 * 1e9, t1 * 1e9)
    ax.set_xlabel("time (ns)")
    ax.set_ylabel("V(XD1.tail) (V)")
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.suptitle(
        f"Tail node V(XD1.tail) of {DESC[name]}, three output periods after settle; {title_v}.",
        fontsize=9, y=0.975)
    save(fig, os.path.join(outdir, f"fig_tail_saturation_{name}.png"))


def plot_supply(all_m, all_ctx, outdir):
    fig, axes = plt.subplots(2, 1, sharex=True, sharey=True, figsize=(7.2, 6.0))
    fig.subplots_adjust(left=0.14, right=0.97, top=0.86, bottom=0.11, hspace=0.25)
    for ax, name, color in zip(axes, DIVIDERS, [BLUE, GREEN]):
        ctx = all_ctx[name]
        m = all_m[name]
        t, t0, tper = ctx["t"], ctx["t0"], ctx["tper"]
        t1 = t0 + CURRENT_PERIODS * tper
        win = (t >= t0) & (t <= t1)
        rel = (t[win] - t0) * 1e9
        y = ctx["i_drawn"][win]
        ax.plot(rel, y, color=color, lw=1.1)
        mean2 = m["supply_avg_ma_2_periods"] * 1e-3
        ax.axhline(mean2, color=ORANGE, lw=1.3, ls="--")
        ax.text(0.99, 0.95,
                f"mean {mean2*1e3:.4f} mA (tsv i_avg {m['tsv']['i_avg_mA']:.4f} mA), "
                f"peak {m['supply_peak_ma_steady']:.3f} mA",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))
        ax.set_ylabel(f"{name}\nI(VDD) (A)")
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, -3))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[-1].set_xlabel(f"time after window start (ns), {CURRENT_PERIODS} output periods")
    axes[-1].set_xlim(0, CURRENT_PERIODS * tper * 1e9)
    fig.suptitle("Supply current drawn from VDD (positive = drawn) after settle, "
                 f"D_1p4 vs B_6g, {CURRENT_PERIODS} output periods each; dashed: mean over window.",
                 fontsize=9, y=0.975)
    save(fig, os.path.join(outdir, "fig_supply_current.png"))


# ----------------------------------------------------------------- JSON
def jsonable(obj):
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return float(obj) if math.isfinite(float(obj)) else "n/a"
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if obj is None:
        return "n/a"
    return obj


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--finals", default=DEFAULT_FINALS)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--vdsat", type=float, default=None,
                    help="Vdsat in volts for the tail plots (default: none)")
    ap.add_argument("--json", default=None,
                    help="analysis JSON path (default: FINALS/analysis.json)")
    args = ap.parse_args(argv)
    json_path = args.json or os.path.join(args.finals, "analysis.json")
    os.makedirs(args.outdir, exist_ok=True)
    print(f"font: {setup_style()}")

    all_m, all_ctx = {}, {}
    for name in DESIGNS:
        all_m[name], all_ctx[name] = measure_design(name, args.finals)

    for name in DIVIDERS:
        plot_tran_divider(name, all_m[name], all_ctx[name], args.outdir)
        plot_tail(name, all_ctx[name], all_m[name], args.vdsat, args.outdir)
    plot_tran_unsized(all_m["unsized"], all_ctx["unsized"], args.outdir)
    plot_phase_steps(all_m, args.outdir)
    plot_supply(all_m, all_ctx, args.outdir)

    doc = {
        "settle_ns": SETTLE_S * 1e9,
        "vdd_v": VDD,
        "vdsat_v": args.vdsat,
        "current_sign": "drawn = -V(VDD:p); positive = current drawn from the supply",
        "plot_window_rule": "start = max(settle, 15 output periods); 3 output periods",
        "current_window_rule": "2 output periods starting at the plot window start",
        "designs": {n: all_m[n] for n in DESIGNS},
    }
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(jsonable(doc), f, indent=2, allow_nan=False)
        f.write("\n")
    print(f"wrote {json_path}")

    for n in DESIGNS:
        m = all_m[n]
        print(f"{n}: Q1 {m['q1_min_v']:.4f}..{m['q1_max_v']:.4f} V; "
              f"tail1 {m['xd1_tail_min_v']*1e3:.2f}..{m['xd1_tail_max_v']*1e3:.2f} mV; "
              f"I_avg steady {m['supply_avg_ma_steady']:.5f} mA (tsv {m['tsv']['i_avg_mA']}); "
              f"I_avg 2-period {m['supply_avg_ma_2_periods']:.5f} mA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
