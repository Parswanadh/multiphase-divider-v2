#!/usr/bin/env python3
"""Figures for the gpdk045 report, drawn only from simulation outputs.

Inputs (each optional; a figure whose input is missing is skipped with a printed note):
  --raw     Spectre nutascii raw of the nominal transient (a file, or a directory holding one)
  --pvt     results/gpdk045_pvt_summary.csv from gpdk45_collect.py (FAIL rows are kept)
  --grid    results/gpdk045_tuning_grid.csv (tuning sweep rows)
  --outdir  output directory (default report/gpdk045/figures)

Figures (300 dpi PNG, white background):
  fig_8phases.png             CK and the eight outputs, 3 output periods after start-up, by phase
  fig_phase_steps.png         adjacent phase steps vs the ideal 45 deg
  fig_pvt_delay_power.png     delay and power vs VDD per corner and temperature; FAIL marked
  fig_pvt_heatmap.png         PASS/FAIL map, corner x (temperature, VDD)
  fig_tuning_phase_error.png  max phase-step error vs input frequency, divider-passing rows
  fig_supply_current.png      supply current vs time over two output periods

Measurement follows scripts/measure_tran.py: rising crossings of each signal's own mid-swing,
linearly interpolated. Start-up is taken as the first SETTLE_FRAC of the record. Tout is the
mean spacing of Q1 rising edges; the phase reference is the third Q1 rising edge. A raw whose
outputs do not divide by two raises ValueError, and the figure is then skipped with a note.
"""
import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

import spectre_raw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PVT = os.path.join(ROOT, "results", "gpdk045_pvt_summary.csv")
DEFAULT_GRID = os.path.join(ROOT, "results", "gpdk045_tuning_grid.csv")
DEFAULT_OUTDIR = os.path.join(ROOT, "report", "gpdk045", "figures")

DPI = 300
SETTLE_FRAC = 0.3
OUT_NODES = ["v(q1)", "v(q2)", "v(q3)", "v(q4)", "v(q1b)", "v(q2b)", "v(q3b)", "v(q4b)"]
NAMES = {n: n[2:-1].upper() for n in OUT_NODES}
CORNER_COLORS = {"tt": "#d97757", "ff": "#3b6ea5", "ss": "#4d7a4f", "fs": "#7b4fa0", "sf": "#8c5a2b"}
TEMP_STYLES = ["-", "--", ":", "-."]
TEMP_MARKERS = ["o", "s", "^", "D"]
PASS_FILL, FAIL_FILL, NA_FILL = "#9cc69b", "#e07a7a", "#e6e6e6"
TRUE_WORDS = {"1", "true", "yes", "y", "t", "pass"}


def skip(msg):
    print(f"SKIP: {msg}")


def save(fig, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")
    return path


def _num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------- transient measurements

def load_tran(raw):
    if not raw or not os.path.exists(raw):
        skip(f"no transient raw at {raw!r}; transient figures not drawn")
        return None
    try:
        path = spectre_raw.find_raw(raw)
    except FileNotFoundError as exc:
        skip(f"{exc}; transient figures not drawn")
        return None
    return spectre_raw.read_tran(path)


def rising_edges(t, x, settle):
    """Interpolated rising crossings of the mid-swing of x after settle, and its (lo, hi)."""
    late = t > settle
    lo, hi = float(x[late].min()), float(x[late].max())
    mid = 0.5 * (lo + hi)
    i = np.where((x[:-1] < mid) & (x[1:] >= mid) & (t[:-1] > settle))[0]
    tc = t[i] + (mid - x[i]) * (t[i + 1] - t[i]) / (x[i + 1] - x[i])
    return tc, (lo, hi)


def measure_phases(cols):
    """Phases of the eight outputs relative to the third Q1 rising edge (deg, mod 360)."""
    t = cols["time"]
    settle = t[0] + SETTLE_FRAC * (t[-1] - t[0])
    ck, _ = rising_edges(t, cols["v(ck)"], settle)
    if len(ck) < 4:
        raise ValueError("CK does not toggle after start-up")
    edges = {}
    for n in OUT_NODES:
        edges[n], _ = rising_edges(t, cols[n], settle)
    q1 = edges["v(q1)"]
    if len(q1) < 4:
        raise ValueError("Q1 does not toggle after start-up")
    tout = float(np.mean(np.diff(q1)))
    fin = 1.0 / float(np.mean(np.diff(ck)))
    ratio = fin * tout
    if abs(ratio - 2.0) > 0.02:
        raise ValueError(f"output does not divide by two (fin/fout = {ratio:.3f})")
    ref = float(q1[2])
    phase = {}
    for n in OUT_NODES:
        later = edges[n][edges[n] >= ref]
        if later.size == 0:
            raise ValueError(f"{n} has no rising edge after the reference")
        phase[n] = float(((later[0] - ref) / tout * 360.0) % 360.0)
    return {"t": t, "cols": cols, "ref": ref, "tout": tout, "fin": fin, "phase": phase}


def adjacent_steps(phase):
    """Outputs sorted by phase, and the wrap-around step between each adjacent pair."""
    order = sorted(phase.items(), key=lambda kv: kv[1])
    vals = np.array([v for _, v in order])
    steps = np.diff(np.append(vals, vals[0] + 360.0))
    return order, steps


def fig_8phases(raw, outdir):
    cols = load_tran(raw)
    if cols is None:
        return None
    m = measure_phases(cols)
    order, _ = adjacent_steps(m["phase"])
    t, ref, tout = m["t"], m["ref"], m["tout"]
    win = (t >= ref) & (t <= ref + 3 * tout)
    x = (t[win] - ref) * 1e9
    traces = [("v(ck)", "CK")] + [(n, f"{NAMES[n]}  {p:.1f} deg") for n, p in order]
    vdd = float(np.max(cols["v(ck)"][win]))
    spacing = 1.25 * vdd
    fig, ax = plt.subplots(figsize=(8, 9))
    ticks, labels = [], []
    for k, (n, lab) in enumerate(traces):
        base = (len(traces) - 1 - k) * spacing
        ax.plot(x, cols[n][win] + base, lw=1.0, color="#888888" if n == "v(ck)" else "#1f1f1f")
        ticks.append(base + vdd / 2)
        labels.append(lab)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, x[-1])
    ax.set_xlabel("Time from reference edge (ns)")
    ax.set_ylabel("Node voltage (V), traces stacked; label = measured phase")
    ax.set_title("CK and the eight divider outputs, ordered by measured phase,\n"
                 "3 output periods after start-up")
    return save(fig, outdir, "fig_8phases.png")


def fig_phase_steps(raw, outdir):
    cols = load_tran(raw)
    if cols is None:
        return None
    m = measure_phases(cols)
    order, steps = adjacent_steps(m["phase"])
    names = [k for k, _ in order]
    labels = [f"{NAMES[names[i]]} to {NAMES[names[(i + 1) % 8]]}" for i in range(8)]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(range(8), steps, width=0.6, color="#5b7083")
    ax.axhline(45.0, ls="--", lw=1.2, color="#c0392b", label="ideal 45 deg")
    for i, s in enumerate(steps):
        ax.text(i, s + 0.8, f"{s:.2f}", ha="center", fontsize=8)
    ax.set_xticks(range(8))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, max(55.0, float(steps.max()) + 6))
    ax.set_ylabel("Adjacent phase step (deg)")
    ax.set_xlabel("Adjacent pair in measured phase order")
    ax.set_title("Measured adjacent phase steps (rising mid-swing crossings) vs ideal 45 deg")
    ax.legend(loc="lower right", fontsize=8)
    return save(fig, outdir, "fig_phase_steps.png")


# ---------------------------------------------------------------- PVT summary

def load_csv(path):
    if not path or not os.path.exists(path):
        skip(f"no CSV at {path!r}; figure not drawn")
        return None
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def parse_pvt(rows):
    """Rows with a PASS/FAIL status and a numeric temperature and VDD; others are counted."""
    pts, unplaced = [], 0
    for r in rows:
        status = (r.get("Divides") or "").strip().upper()
        status = status if status in ("PASS", "FAIL") else None
        temp, vdd = _num(r.get("Temp_C")), _num(r.get("VDD_V"))
        corner = (r.get("Corner") or "").strip().lower()
        if status is None or temp is None or vdd is None or not corner:
            unplaced += 1
            continue
        pts.append({"corner": corner, "temp": temp, "vdd": vdd, "status": status,
                    "delay": _num(r.get("Delay_ps")), "power": _num(r.get("Power_mW"))})
    if unplaced:
        print(f"note: {unplaced} CSV row(s) lack a PASS/FAIL status or numeric Temp_C/VDD_V "
              "and are not placed")
    return pts


def fig_pvt_delay_power(pvt_path, outdir):
    rows = load_csv(pvt_path)
    if rows is None:
        return None
    pts = parse_pvt(rows)
    temps = sorted({p["temp"] for p in pts})
    series = {}
    for p in pts:
        if p["status"] == "PASS" and p["delay"] is not None and p["power"] is not None:
            series.setdefault((p["corner"], p["temp"]), []).append(p)
    fig, (ax_d, ax_p) = plt.subplots(1, 2, figsize=(11, 5))
    for (corner, temp), lst in sorted(series.items()):
        lst.sort(key=lambda p: p["vdd"])
        vx = [p["vdd"] for p in lst]
        ls = TEMP_STYLES[temps.index(temp) % len(TEMP_STYLES)]
        mk = TEMP_MARKERS[temps.index(temp) % len(TEMP_MARKERS)]
        col = CORNER_COLORS.get(corner, "#555555")
        lab = f"{corner.upper()} {temp:g} C"
        ax_d.plot(vx, [p["delay"] for p in lst], ls=ls, marker=mk, color=col, label=lab)
        ax_p.plot(vx, [p["power"] for p in lst], ls=ls, marker=mk, color=col, label=lab)
    blend = blended_transform_factory  # x in data, y in axes fraction
    fails = [p for p in pts if p["status"] == "FAIL"]
    fail_txt = "; ".join(f"{p['corner'].upper()} {p['temp']:g} C at {p['vdd']:g} V" for p in fails)
    for ax in (ax_d, ax_p):
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo - 0.2 * (hi - lo), hi)  # band below the data for FAIL markers
        tr = blend(ax.transData, ax.transAxes)  # x in data, y in axes fraction
        for p in fails:
            ax.plot([p["vdd"]], [0.07], ls="none", marker="x", ms=9, mew=2,
                    color="red", transform=tr, clip_on=False)
        if fails:
            ax.text(0.02, 0.98, "FAIL (red x, no delay/power): " + fail_txt,
                    transform=ax.transAxes, color="red", fontsize=7, va="top")
        ax.set_xlabel("Supply VDD (V)")
        ax.grid(alpha=0.3, lw=0.5)
    ax_d.set_ylabel("Delay (ps)")
    ax_p.set_ylabel("Power (mW)")
    ax_d.set_title("Delay vs VDD")
    ax_p.set_title("Power vs VDD")
    if series:
        ax_p.legend(fontsize=7, loc="best")
    else:
        skip("no PASS points with delay and power; only FAIL markers drawn")
    fig.suptitle("Delay and power vs VDD by corner and temperature (PASS points; FAIL marked with x)")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return save(fig, outdir, "fig_pvt_delay_power.png")


def fig_pvt_heatmap(pvt_path, outdir):
    rows = load_csv(pvt_path)
    if rows is None:
        return None
    pts = parse_pvt(rows)
    corners = sorted({p["corner"] for p in pts})
    keys = sorted({(p["temp"], p["vdd"]) for p in pts})
    grid = np.full((len(corners), len(keys)), np.nan)
    for p in pts:
        i, j = corners.index(p["corner"]), keys.index((p["temp"], p["vdd"]))
        if p["status"] == "FAIL":
            grid[i, j] = 0.0  # a FAIL in any duplicate row dominates
        elif np.isnan(grid[i, j]):
            grid[i, j] = 1.0
    cmap = ListedColormap([FAIL_FILL, PASS_FILL]).with_extremes(bad=NA_FILL)
    fig, ax = plt.subplots(figsize=(max(6, 1.1 * len(keys) + 2), max(3, 0.7 * len(corners) + 2)))
    ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(corners)):
        for j in range(len(keys)):
            v = grid[i, j]
            txt = "no data" if np.isnan(v) else ("PASS" if v == 1.0 else "FAIL")
            ax.text(j, i, txt, ha="center", va="center", fontsize=8)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([f"{t:g} C\n{v:g} V" for t, v in keys], fontsize=8)
    ax.set_yticks(range(len(corners)))
    ax.set_yticklabels([c.upper() for c in corners])
    ax.set_xlabel("Temperature (deg C) and supply VDD (V)")
    ax.set_ylabel("Process corner")
    ax.set_title("PVT pass/fail map: corner vs (temperature, VDD)")
    ax.legend(handles=[Patch(color=PASS_FILL, label="PASS"), Patch(color=FAIL_FILL, label="FAIL"),
                       Patch(color=NA_FILL, label="not in summary")],
              loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
    fig.tight_layout()
    return save(fig, outdir, "fig_pvt_heatmap.png")


# ---------------------------------------------------------------- tuning grid

def parse_grid(rows):
    pts = []
    for r in rows:
        pts.append({
            "divides": (r.get("divides") or "").strip().lower() in TRUE_WORDS,
            "fin": _num(r.get("fin")), "fout": _num(r.get("f_out_MHz")),
            "rl": (r.get("rl") or "").strip(), "vb": (r.get("vb") or "").strip(),
            "mult": (r.get("mult") or "").strip(),
            "err": _num(r.get("max_phase_step_err_deg")),
        })
    return pts


def fin_unit(pts):
    """Infer the unit of the fin column from divider rows, where fin = 2 * f_out (f_out in MHz).

    Returns (name, factor) such that fin * factor is in GHz, or None if it cannot be inferred.
    """
    ratios = [p["fin"] / (2.0 * p["fout"]) for p in pts
              if p["fin"] and p["fout"] and p["fout"] > 0]
    if not ratios:
        return None
    u = 1e-3 / float(np.median(ratios))
    cands = {"GHz": 1.0, "MHz": 1e-3, "Hz": 1e-9}
    name = min(cands, key=lambda k: abs(math.log10(u / cands[k])))
    if abs(math.log10(u / cands[name])) > 0.1:
        return None
    return name, cands[name]


def fig_tuning_phase_error(grid_path, outdir):
    rows = load_csv(grid_path)
    if rows is None:
        return None
    pts = [p for p in parse_grid(rows) if p["divides"] and p["fin"] is not None and p["err"] is not None]
    if not pts:
        skip("no divider-passing rows with a numeric phase error in the grid")
        return None
    unit = fin_unit(pts)
    if unit is None:
        skip("cannot infer the unit of the fin column from the grid rows")
        return None
    uname, u = unit
    print(f"note: grid fin treated as {uname}")
    groups = {}
    for p in pts:
        groups.setdefault((p["rl"], p["mult"], p["vb"]), []).append(p)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    cmap = plt.get_cmap("tab10")
    for i, key in enumerate(sorted(groups)):
        lst = sorted(groups[key], key=lambda p: p["fin"])
        ax.plot([p["fin"] * u for p in lst], [p["err"] for p in lst], marker="o", ms=4, lw=1.0,
                color=cmap(i % 10), label=f"rl={key[0]}, mult={key[1]}, vb={key[2]}")
    ax.set_xlabel("Input frequency fin (GHz)")
    ax.set_ylabel("Max phase-step error (deg)")
    ax.set_title("Maximum phase-step error vs input frequency (grid rows that divide by two)")
    ax.grid(alpha=0.3, lw=0.5)
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    return save(fig, outdir, "fig_tuning_phase_error.png")


# ---------------------------------------------------------------- supply current

def fig_supply_current(raw, outdir):
    cols = load_tran(raw)
    if cols is None:
        return None
    m = measure_phases(cols)
    t, ref, tout = m["t"], m["ref"], m["tout"]
    win = (t >= ref) & (t <= ref + 2 * tout)
    x = (t[win] - ref) * 1e9
    i_ma = -cols["i(vdd)"][win] * 1e3
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x, i_ma, color="#1f1f1f", lw=0.9)
    ax.axvline(tout * 1e9, ls=":", color="#888888", lw=1.0)
    ax.text(tout * 1e9, ax.get_ylim()[1], " one output period", fontsize=7, va="top", color="#555555")
    ax.set_xlim(0, x[-1])
    ax.set_xlabel("Time from reference edge (ns)")
    ax.set_ylabel("Current drawn from VDD (mA), = -i(vdd)")
    ax.set_title("Supply current vs time over two output periods (after start-up)")
    ax.grid(alpha=0.3, lw=0.5)
    return save(fig, outdir, "fig_supply_current.png")


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="Draw the gpdk045 report figures from simulation outputs.")
    ap.add_argument("--raw", default=None,
                    help="Spectre nutascii raw of the nominal transient (file or directory)")
    ap.add_argument("--pvt", default=DEFAULT_PVT, help="PVT summary CSV")
    ap.add_argument("--grid", default=DEFAULT_GRID, help="tuning grid CSV")
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR, help="output directory for the PNG files")
    a = ap.parse_args(argv)
    jobs = [
        ("fig_8phases", lambda: fig_8phases(a.raw, a.outdir)),
        ("fig_phase_steps", lambda: fig_phase_steps(a.raw, a.outdir)),
        ("fig_pvt_delay_power", lambda: fig_pvt_delay_power(a.pvt, a.outdir)),
        ("fig_pvt_heatmap", lambda: fig_pvt_heatmap(a.pvt, a.outdir)),
        ("fig_tuning_phase_error", lambda: fig_tuning_phase_error(a.grid, a.outdir)),
        ("fig_supply_current", lambda: fig_supply_current(a.raw, a.outdir)),
    ]
    for name, job in jobs:
        try:
            job()
        except ValueError as exc:
            skip(f"{name} not drawn: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
