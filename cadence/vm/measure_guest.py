#!/usr/bin/env python
"""Measure a divide-by-2 / 8-phase transient from Spectre nutascii raw files.

Runs inside the CentOS 6.5 guest with Python 2.6.6, using the standard library only.
Definitions mirror scripts/measure_tran.py.

Usage: measure_guest.py <file.raw | dir> [vdd] [settle_ns]
  dir:  every *.raw in it -> one tab-separated row per file (header first), also written
        to ./measure_summary.tsv
  file: header + one row
  vdd defaults to the tag's last field (<corner>_<temp>_<vdd>, e.g. tt_27_1.0 or tt_27_0p9),
  else 1.0. A bad file prints "<tag>\\tERROR\\t<message>" and processing continues.

divides=1 only if all of these hold after settle_ns:
  - |f_in / f_out(Q1) - 2| < 0.001
  - every output (Q1..Q4, Q1b..Q4b) has a mean rising-edge period within 0.1% of 2/f_in
    (per-output period from its own rising crossings of its own mid-swing)
  - every output swings >= 0.1 V (max - min); feedthrough glitches alone do not count
  - every output's rising-edge count is within +-1 of the Q1 count
Otherwise divides=0 and the last column `reason` lists the failed checks; for divides=1 it is `ok`.
Columns after swing_hi: phases_deg (name:phase in sorted order, degrees relative to the 3rd Q1
rising edge), phase_steps_deg (8 adjacent steps, wrap-around included), periods_averaged (output
periods used for the power average), i_avg_mA (average VDD supply current), reason.
Non-dividing rows have nan in phases_deg, phase_steps_deg, periods_averaged and i_avg_mA.
"""
from __future__ import division, print_function

import bisect
import math
import os
import sys
from array import array

HEADER = ["tag", "divides", "f_in_GHz", "f_out_MHz", "ratio", "power_mW", "delay_ps",
          "pdp_fJ", "max_phase_step_err_deg", "swing_lo", "swing_hi",
          "phases_deg", "phase_steps_deg", "periods_averaged", "i_avg_mA", "reason"]
OUTS = ["q1", "q2", "q3", "q4", "q1b", "q2b", "q3b", "q4b"]
NAN = float("nan")
RATIO_TOL = 0.001      # |f_in / f_out - 2|
PERIOD_TOL = 0.001     # relative, per-output mean period vs 2 / f_in
MIN_SWING = 0.1        # volts, max - min after settling
EDGE_TOL = 1           # rising-edge count vs Q1


def _norm(name):
    n = name.strip().lower()
    if n.startswith("v(") and n.endswith(")"):
        n = n[2:-1]
    return n


def parse_plots(path):
    """Return the usable plots of a nutascii file: dicts with plotname, names, cols.

    cols[i] is an array('d') holding every value of variable names[i] (names[0] is time).
    """
    plots = []
    cur = None
    state = None
    tok_count = 0
    f = open(path, "r")
    try:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("Title:"):
                cur = {"plotname": "", "names": [], "cols": None}
                plots.append(cur)
                state = "header"
                tok_count = 0
                continue
            if cur is None:
                cur = {"plotname": "", "names": [], "cols": None}
                plots.append(cur)
                state = "header"
            if state == "values":
                # tokens come as: pointIndex, v0, v1 ... v(N-1), pointIndex, ...
                nv1 = len(cur["names"]) + 1
                cols = cur["cols"]
                for s in line.split():
                    pos = tok_count % nv1
                    tok_count += 1
                    if pos:
                        cols[pos - 1].append(float(s))
                continue
            if line.startswith("Values:"):
                cur["cols"] = [array("d") for _ in cur["names"]]
                state = "values"
            elif line.startswith("Variables:"):
                state = "vars"
                # Spectre puts the first variable (time) on the same line as "Variables:"
                parts = line[len("Variables:"):].split()
                if len(parts) >= 2 and parts[0].isdigit():
                    cur["names"].append(parts[1])
            elif line.startswith("Plotname:"):
                cur["plotname"] = line[len("Plotname:"):].strip()
            elif state == "vars":
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    cur["names"].append(parts[1])
    finally:
        f.close()

    usable = []
    for p in plots:
        cols = p["cols"]
        if not p["names"] or not cols:
            continue
        n = min(len(c) for c in cols)      # drop a partial trailing point
        for c in cols:
            if len(c) > n:
                del c[n:]
        usable.append(p)
    return usable


def pick_plot(plots):
    """First plot whose Plotname contains 'tran'; otherwise the only plot."""
    if not plots:
        raise ValueError("no nutascii Variables/Values data in file")
    for p in plots:
        if "tran" in p["plotname"].lower():
            return p
    if len(plots) == 1:
        return plots[0]
    raise ValueError("no transient plot among: %s"
                     % "; ".join([p["plotname"] for p in plots]))


def rising(t, x, start):
    """Rising crossings of the mid-level of x's own swing (samples from index start on).

    Returns (crossing times, lo, hi); crossings are linearly interpolated on the raw grid.
    """
    seg = x[start:]
    lo = min(seg)
    hi = max(seg)
    mid = 0.5 * (lo + hi)
    out = []
    for i in range(start, len(t) - 1):
        a = x[i]
        b = x[i + 1]
        if a < mid and b >= mid:
            out.append(t[i] + (mid - a) * (t[i + 1] - t[i]) / (b - a))
    return out, lo, hi


def measure(plot, vdd, settle_s):
    names = plot["names"]
    cols = plot["cols"]
    idx = {}
    for i, n in enumerate(names):
        k = _norm(n)
        if k not in idx:
            idx[k] = i

    def sig(k):
        if k not in idx:
            raise ValueError("signal %s not in plot" % k)
        return cols[idx[k]]

    t = cols[0]
    if len(t) < 8:
        raise ValueError("too few points (%d)" % len(t))
    start = bisect.bisect_right(t, settle_s)
    if start >= len(t) - 2:
        raise ValueError("no data after settle time")

    sup = None
    if "vdd:p" in idx:
        sup = idx["vdd:p"]
    else:
        cands = sorted([k for k in idx if k.startswith("vdd:")])
        if cands:
            sup = idx[cands[0]]

    r = {"divides": 0, "f_in_GHz": NAN, "f_out_MHz": NAN, "ratio": NAN, "power_mW": NAN,
         "delay_ps": NAN, "pdp_fJ": NAN, "max_phase_step_err_deg": NAN,
         "swing_lo": NAN, "swing_hi": NAN, "phases": None, "steps": None,
         "periods": NAN, "i_avg_mA": NAN, "reason": ""}

    ck_edges, _, _ = rising(t, sig("ck"), start)
    if len(ck_edges) < 4:
        r["reason"] = "clock not found"
        return r
    fin = (len(ck_edges) - 1) / (ck_edges[-1] - ck_edges[0])
    r["f_in_GHz"] = fin / 1e9
    t_target = 2.0 / fin                      # expected output period at f_in / 2

    edges = {}
    swing = {}
    for name in OUTS:
        e, lo, hi = rising(t, sig(name), start)
        edges[name] = e
        swing[name] = hi - lo
        if name == "q1":
            r["swing_lo"] = lo
            r["swing_hi"] = hi

    q1 = edges["q1"]
    if len(q1) < 4:
        r["reason"] = "Q1 does not toggle (symmetric/stuck state)"
        return r
    Tout = (q1[-1] - q1[0]) / (len(q1) - 1)
    fout = 1.0 / Tout
    ratio = fin / fout
    r["f_out_MHz"] = fout / 1e6
    r["ratio"] = ratio

    fails = []
    if abs(ratio - 2.0) >= RATIO_TOL:
        fails.append("ratio %.4f not 2 (Q1 %.3f MHz)" % (ratio, fout / 1e6))
    for name in OUTS:
        e = edges[name]
        if swing[name] < MIN_SWING:
            fails.append("%s swing %.3f V < %.1f V (not toggling)"
                         % (name, swing[name], MIN_SWING))
        if len(e) < 4:
            fails.append("%s has %d rising edges (not toggling)" % (name, len(e)))
            continue
        tmean = (e[-1] - e[0]) / (len(e) - 1)
        if abs(tmean - t_target) >= PERIOD_TOL * t_target:
            fails.append("%s period %.2f ps vs 2/f_in %.2f ps"
                         % (name, tmean * 1e12, t_target * 1e12))
        if abs(len(e) - len(q1)) > EDGE_TOL:
            fails.append("%s edge count %d vs Q1 %d" % (name, len(e), len(q1)))
    if fails:
        r["reason"] = "; ".join(fails)
        return r

    r["divides"] = 1
    r["reason"] = "ok"

    # phases of the 8 outputs relative to the 3rd Q1 rising edge
    ref = q1[2]
    phases = []
    for name in OUTS:
        e = edges[name]
        j = bisect.bisect_left(e, ref)
        if j >= len(e):
            raise ValueError("no %s edge after reference" % name)
        phases.append((((e[j] - ref) / Tout * 360.0) % 360.0, name))
    phases.sort()
    vals = [p for p, _ in phases]
    steps = [vals[i + 1] - vals[i] for i in range(7)]
    steps.append(vals[0] + 360.0 - vals[7])
    r["max_phase_step_err_deg"] = max([abs(s - 45.0) for s in steps])
    r["phases"] = ",".join(["%s:%.2f" % (n, p) for p, n in phases])
    r["steps"] = ",".join(["%.2f" % s for s in steps])

    # average supply power over an integer number of output periods (trapezoid on raw grid)
    if sup is None:
        raise ValueError("no VDD: supply current in plot")
    cur = cols[sup]
    n_per = int((t[-1] - ref) // Tout)
    if n_per < 1:
        raise ValueError("less than one output period after reference")
    t1 = ref + n_per * Tout
    i0 = bisect.bisect_left(t, ref)
    i1 = bisect.bisect_right(t, t1)
    s = 0.0
    for k in range(i0, i1 - 1):
        s += (t[k + 1] - t[k]) * (-cur[k] - cur[k + 1]) * 0.5
    iavg = s / (t1 - ref)
    r["power_mW"] = vdd * iavg * 1e3
    r["i_avg_mA"] = iavg * 1e3
    r["periods"] = n_per

    # CK rising edge -> next rising edge on any of the 8 outputs
    alle = []
    for name in OUTS:
        alle.extend(edges[name])
    alle.sort()
    tot = 0.0
    cnt = 0
    for c in ck_edges:
        j = bisect.bisect_left(alle, c)
        if j < len(alle):
            tot += alle[j] - c
            cnt += 1
    if cnt == 0:
        raise ValueError("no output edge after any clock edge")
    r["delay_ps"] = tot / cnt * 1e12
    r["pdp_fJ"] = r["power_mW"] * r["delay_ps"]          # mW * ps = fJ
    return r


def vdd_from_tag(tag):
    parts = tag.split("_")
    if len(parts) >= 3:
        s = parts[-1].lower().rstrip("v").replace("p", ".")
        try:
            return float(s)
        except ValueError:
            pass
    return 1.0


def fmt(v, spec):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "nan"
    return spec % v


def process(path, vdd_arg, settle_s):
    tag = os.path.splitext(os.path.basename(path))[0]
    if vdd_arg is not None:
        vdd = float(vdd_arg)
    else:
        vdd = vdd_from_tag(tag)
    plot = pick_plot(parse_plots(path))
    r = measure(plot, vdd, settle_s)
    if not r["divides"]:
        sys.stderr.write("%s: %s\n" % (tag, r["reason"]))
    reason = r["reason"].replace("\t", " ").replace("\n", " ")
    return [tag,
            "%d" % r["divides"],
            fmt(r["f_in_GHz"], "%.4f"),
            fmt(r["f_out_MHz"], "%.3f"),
            fmt(r["ratio"], "%.4f"),
            fmt(r["power_mW"], "%.6f"),
            fmt(r["delay_ps"], "%.2f"),
            fmt(r["pdp_fJ"], "%.3f"),
            fmt(r["max_phase_step_err_deg"], "%.3f"),
            fmt(r["swing_lo"], "%.4f"),
            fmt(r["swing_hi"], "%.4f"),
            r["phases"] or "nan",
            r["steps"] or "nan",
            fmt(r["periods"], "%d"),
            fmt(r["i_avg_mA"], "%.6f"),
            reason]


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: measure_guest.py <file.raw | dir> [vdd] [settle_ns]\n")
        return 2
    target = argv[1]
    vdd_arg = argv[2] if len(argv) > 2 and argv[2] else None
    settle_s = (float(argv[3]) if len(argv) > 3 else 10.0) * 1e-9

    if os.path.isdir(target):
        files = sorted([os.path.join(target, f) for f in os.listdir(target)
                        if f.lower().endswith(".raw")])
        if not files:
            sys.stderr.write("no *.raw files in %s\n" % target)
            return 1
    elif os.path.isfile(target):
        files = [target]
    else:
        sys.stderr.write("not a file or directory: %s\n" % target)
        return 1

    lines = ["\t".join(HEADER)]
    for path in files:
        tag = os.path.splitext(os.path.basename(path))[0]
        try:
            fields = process(path, vdd_arg, settle_s)
        except Exception as e:
            msg = str(e) or e.__class__.__name__
            fields = [tag, "ERROR", msg.replace("\n", " ").replace("\t", " ")]
        lines.append("\t".join(fields))

    for ln in lines:
        print(ln)
    if os.path.isdir(target):
        with open("measure_summary.tsv", "w") as f:
            f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
