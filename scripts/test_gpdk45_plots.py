#!/usr/bin/env python3
"""Tests for scripts/gpdk45_plots.py on synthetic inputs. Every file is written under a temp dir.

Run: python -I -B scripts/test_gpdk45_plots.py   (or python -I -B -m pytest scripts/test_gpdk45_plots.py)
"""
import os
import struct
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gpdk45_plots as gp  # noqa: E402
import spectre_raw  # noqa: E402

SCRIPT = os.path.join(HERE, "gpdk45_plots.py")
PY = sys.executable

FIN = 1e9          # clock 1 GHz
TOUT = 2e-9        # outputs 500 MHz
T_END = 40e-9
DT = 10e-12
VDD = 1.8
# Output phases (deg). Chosen so that the phase order differs from the name order.
PHASES = {"v(q1)": 0, "v(q3)": 45, "v(q2)": 90, "v(q4)": 135,
          "v(q1b)": 180, "v(q3b)": 225, "v(q2b)": 270, "v(q4b)": 315}
SPICE_ORDER = ["time", "v(q1)", "v(q1b)", "v(q2)", "v(q2b)", "v(q3)", "v(q3b)",
               "v(q4)", "v(q4b)", "v(ck)", "vdd:p"]


def waveforms(tout=TOUT):
    """Smooth divide-by-two waveforms with exact phases; supply current is negative (sourcing)."""
    t = np.arange(0.0, T_END, DT)
    cols = {"time": t,
            "v(ck)": 0.5 * VDD * (1 + np.tanh(np.sin(2 * np.pi * FIN * t) / 0.05))}
    for n, ph in PHASES.items():
        cols[n] = 0.5 * VDD * (1 + np.tanh(np.sin(2 * np.pi * t / tout - np.deg2rad(ph)) / 0.05))
    cols["i(vdd)"] = -(1e-3 + 2e-4 * np.sin(2 * np.pi * 2 * FIN * t))
    return cols


def write_raw(path, cols):
    """Nutascii raw in the real layout: a DC block, then a tran block whose first variable sits on
    the Variables: line; values are a token stream packed several per line."""
    src = dict(cols)
    src["vdd:p"] = cols["i(vdd)"]
    n = len(cols["time"])
    out = ["Title: synthetic divider", "Date: test", "Plotname: Operating Point",
           "Command: synthetic", "Flags: real", "No. Variables: 2", "No. Points: 1",
           "Variables:", "\t0\tv(ck)\tV", "\t1\tvdd:p\tA", "Values:", "0\t0.0", "\t1.0e-3"]
    out += ["Title: synthetic divider", "Date: test", "Plotname: Transient Response",
            "Command: synthetic", "Flags: real", f"No. Variables: {len(SPICE_ORDER)}",
            f"No. Points: {n}", "Variables:", f"\t0\ttime\ts"]
    for k, name in enumerate(SPICE_ORDER[1:], start=1):
        unit = "A" if name == "vdd:p" else "V"
        out.append(f"\t{k}\t{name}\t{unit}")
    out.append("Values:")
    toks = []
    for i in range(n):
        toks.append(str(i))
        toks.extend(f"{src[name][i]:.9e}" for name in SPICE_ORDER)
    for k in range(0, len(toks), 4):
        out.append("\t".join(toks[k:k + 4]))
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    return path


PVT_HEADER = "Corner,Temp_C,VDD_V,Divides,f_out_MHz,Delay_ps,Power_mW,PDP_fJ,MaxPhaseStepErr_deg_or_reason"
PVT_ROWS = [
    "TT,27,1.6,PASS,700.0,120.0,1.10,132.0,20.1",
    "TT,27,1.8,PASS,700.0,108.0,1.40,151.2,20.0",
    "TT,27,2.0,PASS,700.0,100.0,1.70,170.0,19.9",
    "TT,-40,1.62,PASS,700.0,111.0,1.29,143.2,20.2",
    "TT,-40,1.8,PASS,700.0,105.0,1.30,136.5,20.3",
    "FF,27,1.8,PASS,700.0,90.0,1.90,171.0,20.4",
    "SS,125,1.62,FAIL,1000.0,,,,FAIL: output at 1000.0 MHz, ratio 1.400 (not 2)",
    "FS,27,1.8,FAIL,,,,,FAIL: clock not found",
    "bad_27_1.0,,,FAIL,,,,,FAIL: bad tag bad_27_1.0",
]


def write_text(path, lines):
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def grid_rows(unit_scale):
    """Grid rows; unit_scale converts GHz to the unit used for fin (1 = GHz, 1000 = MHz)."""
    hdr = "tag,divides,fin,rl,vb,cl,mult,f_out_MHz,power_mW,delay_ps,pdp_fJ,max_phase_step_err_deg,swing_lo,swing_hi"
    rows = [hdr]
    spec = [  # tag, divides, fin GHz, rl, vb, mult, fout MHz, err
        ("a1", "True", 1.0, "1k", "0.6", "2", 500.0, 0.40),
        ("a2", "True", 1.4, "1k", "0.6", "2", 700.0, 0.90),
        ("a3", "True", 1.8, "1k", "0.6", "2", 900.0, 1.60),
        ("b1", "True", 1.0, "2k", "0.5", "4", 500.0, 0.70),
        ("b2", "True", 1.4, "2k", "0.5", "4", 700.0, 1.10),
        ("c1", "False", 1.6, "1k", "0.6", "2", 0.0, ""),
    ]
    for tag, div, fin, rl, vb, mult, fout, err in spec:
        rows.append(",".join([tag, div, f"{fin * unit_scale:g}", rl, vb, "10f", mult,
                              f"{fout:g}", "1.2", "110", "132", f"{err}", "0.8", "1.8"]))
    return rows


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


class PlotTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.raw = write_raw(os.path.join(self.tmp, "tran.raw"), waveforms())
        self.pvt = write_text(os.path.join(self.tmp, "pvt.csv"), [PVT_HEADER] + PVT_ROWS)
        self.grid = write_text(os.path.join(self.tmp, "grid.csv"), grid_rows(1.0))
        self.out = os.path.join(self.tmp, "figures")

    def tearDown(self):
        self._tmp.cleanup()

    def assert_png(self, path, min_w=1000):
        self.assertIsNotNone(path)
        self.assertTrue(os.path.isfile(path), path)
        w, h = png_size(path)
        self.assertGreaterEqual(w, min_w)
        self.assertGreater(h, 300)
        self.assertGreater(os.path.getsize(path), 10_000)

    def test_raw_layout_and_measurement(self):
        cols = spectre_raw.read_tran(self.raw)
        self.assertEqual(len(cols), 11)
        self.assertEqual(len(cols["time"]), len(waveforms()["time"]))
        m = gp.measure_phases(cols)
        self.assertAlmostEqual(m["tout"], TOUT, delta=TOUT * 0.002)
        self.assertAlmostEqual(m["fin"], FIN, delta=FIN * 0.002)
        for n, ph in PHASES.items():
            self.assertAlmostEqual(
                (m["phase"][n] - ph + 180) % 360 - 180, 0.0, delta=0.5, msg=n)
        _, steps = gp.adjacent_steps(m["phase"])
        self.assertEqual(len(steps), 8)
        self.assertTrue(np.all(np.abs(steps - 45.0) < 0.6), steps)

    def test_non_dividing_raw_is_rejected(self):
        cols = spectre_raw.read_tran(write_raw(os.path.join(self.tmp, "bad.raw"),
                                               waveforms(tout=4 * TOUT)))
        with self.assertRaises(ValueError):
            gp.measure_phases(cols)

    def test_transient_figures(self):
        self.assert_png(gp.fig_8phases(self.raw, self.out))
        self.assert_png(gp.fig_phase_steps(self.raw, self.out))
        self.assert_png(gp.fig_supply_current(self.raw, self.out))

    def test_pvt_figures_and_parsing(self):
        pts = gp.parse_pvt(gp.load_csv(self.pvt))
        self.assertEqual(sum(p["status"] == "PASS" for p in pts), 6)
        self.assertEqual(sum(p["status"] == "FAIL" for p in pts), 2)  # bad-tag row is unplaced
        self.assert_png(gp.fig_pvt_delay_power(self.pvt, self.out))
        self.assert_png(gp.fig_pvt_heatmap(self.pvt, self.out), min_w=600)

    def test_grid_figure_and_unit(self):
        pts = [p for p in gp.parse_grid(gp.load_csv(self.grid)) if p["divides"]]
        self.assertEqual(len(pts), 5)  # the False row is excluded
        self.assertEqual(gp.fin_unit(pts)[0], "GHz")
        self.assert_png(gp.fig_tuning_phase_error(self.grid, self.out))
        mhz = write_text(os.path.join(self.tmp, "grid_mhz.csv"), grid_rows(1000.0))
        pts_mhz = [p for p in gp.parse_grid(gp.load_csv(mhz)) if p["divides"]]
        self.assertEqual(gp.fin_unit(pts_mhz)[0], "MHz")

    def test_missing_inputs_are_skipped(self):
        missing = os.path.join(self.tmp, "nope")
        self.assertIsNone(gp.fig_8phases(missing, self.out))
        self.assertIsNone(gp.fig_pvt_heatmap(missing, self.out))
        self.assertIsNone(gp.fig_tuning_phase_error(missing, self.out))
        self.assertFalse(os.path.exists(self.out))

    def test_cli_all_figures(self):
        r = subprocess.run([PY, "-I", "-B", SCRIPT, "--raw", self.raw, "--pvt", self.pvt,
                            "--grid", self.grid, "--outdir", self.out],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for name in ["fig_8phases.png", "fig_phase_steps.png", "fig_pvt_delay_power.png",
                     "fig_pvt_heatmap.png", "fig_tuning_phase_error.png", "fig_supply_current.png"]:
            self.assert_png(os.path.join(self.out, name), min_w=600)

    def test_cli_missing_inputs_exit_zero(self):
        missing = os.path.join(self.tmp, "absent")
        r = subprocess.run([PY, "-I", "-B", SCRIPT, "--raw", missing, "--pvt", missing,
                            "--grid", missing, "--outdir", self.out],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SKIP", r.stdout)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
