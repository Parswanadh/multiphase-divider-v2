#!/usr/bin/env python3
"""Synthetic check of spectre_raw.py + measure_tran.measure.

Builds a nutascii raw file for an ideal 8-phase divide-by-2 (ck 1.4 GHz, outputs 700 MHz,
phases 0..315 deg in 45 deg steps, VDD 1.0 V, supply current -1 mA), converts it, and checks
the measured division ratio and phase steps.
"""
import os
import sys
import tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # python -I does not put the script directory on sys.path
import spectre_raw  # noqa: E402
from measure_tran import measure  # noqa: E402

FIN = 1.4e9
FOUT = FIN / 2
VDD = 1.0
TD = 30e-12          # common output delay after ck
TSTOP = 40e-9
DT = 2e-12


def write_raw(path, t, sigs):
    names = ["time"] + list(sigs)
    n = len(t)
    with open(path, "w") as f:
        f.write("Title: synthetic divider\nDate: Sat Jan  1 00:00:00 2000\n")
        f.write("Plotname: Transient Analysis\nFlags: real\n")
        f.write(f"No. Variables: {len(names)}\nNo. Points: {n}\nVariables:\n")
        for k, nm in enumerate(names):
            kind = "time" if nm == "time" else "voltage"
            f.write(f"\t{k}\t{nm}\t{kind}\n")
        f.write("Values:\n")
        for p in range(n):
            f.write(f"{p}\t{t[p]:.12e}\n")
            for nm in names[1:]:
                f.write(f"\t{sigs[nm][p]:.12e}\n")


def make_signals(t):
    sigs = {"v(ck)": VDD * (0.5 + 0.5 * np.sin(2 * np.pi * FIN * t))}
    for k, ph in enumerate([0, 45, 90, 135]):
        s = VDD * (0.5 + 0.5 * np.sin(2 * np.pi * FOUT * (t - TD) - np.deg2rad(ph)))
        sigs[f"v(q{k+1})"] = s
        sigs[f"v(q{k+1}b)"] = VDD - s            # complementary output: +180 deg
    sigs["VDD:p"] = -1e-3 * np.ones_like(t)      # negative while the source delivers power
    return sigs


def main():
    t = np.arange(0, TSTOP, DT)
    sigs = make_signals(t)
    fails = []
    with tempfile.TemporaryDirectory() as td:
        raw = os.path.join(td, "tran.raw")
        write_raw(raw, t, sigs)
        out_by_dir = spectre_raw.convert(td, os.path.join(td, "tran_table.txt"))  # directory input
        assert out_by_dir.endswith("tran_table.txt")
        table = os.path.join(td, "table.txt")
        spectre_raw.convert(raw, table)
        with open(table) as f:
            header = f.readline().split()
        if header != spectre_raw.COLUMNS:
            fails.append(f"header mismatch: {header}")
        r = measure(table, VDD, 10e-9)
    for k, v in r.items():
        print(f"{k:28s} {v}")
    ratio = r.get("division_ratio", float("nan"))
    if not r.get("divides") or abs(ratio - 2) > 0.01:
        fails.append(f"division ratio {ratio} not ~2")
    if r.get("max_phase_step_error_deg", 999) > 1.0:
        fails.append(f"phase step error {r.get('max_phase_step_error_deg')} deg")
    if abs(r.get("power_mw", 0) - 1.0) > 0.01:
        fails.append(f"power {r.get('power_mw')} mW, expected 1.0")
    if fails:
        print("FAIL:", "; ".join(fails))
        sys.exit(1)
    print("PASS: spectre_raw conversion and measure_tran agree (ratio ~2)")


if __name__ == "__main__":
    main()
