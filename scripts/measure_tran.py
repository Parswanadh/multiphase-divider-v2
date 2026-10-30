#!/usr/bin/env python3
"""Measure a divide-by-2 / 8-phase transient from an ngspice `wrdata` file (header row
with `set wr_vecnames`; columns time v(ck) v(q1)..v(q4) v(q1b)..v(q4b) i(vdd)). A Spectre/ADE
CSV export with the same column names also works. Every value is computed from the waveform.

Usage: measure_tran.py FILE [VDD] [settle_ns]     (prints a report; exit 1 if it does not divide)
"""
import sys
import numpy as np


def measure(path, vdd, settle_s):
    with open(path) as f:
        names = f.readline().split()
    d = np.loadtxt(path, skiprows=1)
    t = d[:, 0]
    col = {n.lower(): d[:, i + 1] for i, n in enumerate(names[1:])}
    late = t > settle_s

    def rising(name):
        """rising crossings (after settling) of the midpoint of that signal's own swing"""
        x = col[name]
        lo, hi = x[late].min(), x[late].max()
        mid = (lo + hi) / 2
        idx = np.where((x[:-1] < mid) & (x[1:] >= mid) & (t[:-1] > settle_s))[0]
        return t[idx] + (mid - x[idx]) * (t[idx + 1] - t[idx]) / (x[idx + 1] - x[idx]), (lo, hi)

    r = {"vdd_v": vdd}
    ck, _ = rising("v(ck)")
    if len(ck) < 4:
        r["divides"] = False
        r["reason"] = "clock not found"
        return r
    fin = 1 / np.mean(np.diff(ck))
    r["f_in_ghz"] = fin / 1e9
    outs = ["v(q1)", "v(q2)", "v(q3)", "v(q4)", "v(q1b)", "v(q2b)", "v(q3b)", "v(q4b)"]
    edges = {n: rising(n) for n in outs}
    r["swing_v"] = {n: [round(float(a), 3), round(float(b), 3)] for n, (_, (a, b)) in edges.items()}
    q1 = edges["v(q1)"][0]
    if len(q1) < 4:
        r["divides"] = False
        r["reason"] = "Q1 does not toggle (symmetric/stuck state)"
        return r
    fout = 1 / np.mean(np.diff(q1))
    r["f_out_mhz"] = fout / 1e6
    r["division_ratio"] = fin / fout
    r["divides"] = bool(abs(fin / fout - 2) < 0.01)
    if not r["divides"]:
        r["reason"] = f"output at {fout/1e6:.1f} MHz, ratio {fin/fout:.3f} (not 2)"
        return r
    Tout = 1 / fout
    ref = q1[2]
    ph = {}
    for n in outs:
        e = edges[n][0]
        ph[n] = float(((e[np.searchsorted(e, ref)] - ref) / Tout * 360) % 360)
    order = sorted(ph.items(), key=lambda kv: kv[1])
    vals = np.array([v for _, v in order])
    steps = np.diff(np.append(vals, vals[0] + 360))
    r["phase_deg"] = {k: round(v, 2) for k, v in order}
    r["phase_steps_deg"] = [round(float(s), 2) for s in steps]
    r["max_phase_step_error_deg"] = round(float(np.abs(steps - 45).max()), 2)
    # supply power over an integer number of output periods
    i = -col["i(vdd)"]
    n_per = int((t[-1] - ref) // Tout)
    t1 = ref + n_per * Tout
    m = (t >= ref) & (t <= t1)
    iavg = np.trapezoid(i[m], t[m]) / (t1 - ref)
    r["i_avg_ma"] = float(iavg * 1e3)
    r["power_mw"] = float(vdd * iavg * 1e3)
    r["periods_averaged"] = n_per
    # CK -> output delay: each CK rising edge to the next rising edge on ANY of the 8 outputs
    alle = np.sort(np.concatenate([edges[n][0] for n in outs]))
    dl = []
    for c in ck:
        j = np.searchsorted(alle, c)
        if j < len(alle):
            dl.append(alle[j] - c)
    r["ck_to_q_delay_ps"] = float(np.mean(dl) * 1e12)
    r["pdp_fj"] = r["power_mw"] * r["ck_to_q_delay_ps"]       # mW * ps = fJ
    return r


if __name__ == "__main__":
    path = sys.argv[1]
    vdd = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    settle = float(sys.argv[3]) * 1e-9 if len(sys.argv) > 3 else 10e-9
    r = measure(path, vdd, settle)
    for k, v in r.items():
        print(f"{k:28s} {v}")
    sys.exit(0 if r.get("divides") else 1)
