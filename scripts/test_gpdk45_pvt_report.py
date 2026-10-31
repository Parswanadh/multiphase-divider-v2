#!/usr/bin/env python3
"""Synthetic tests for gpdk45_pvt_report.py (run: /home/parshu/miniconda3/bin/python -I scripts/test_gpdk45_pvt_report.py).

All outputs go to a temporary directory; nothing under results/ or report/ is touched.
Covers: all-pass, partial-fail (with a missing row), an ERROR/nan row, the --compare mode and the
absent-TSV note.
"""
import csv
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
PY = "/home/parshu/miniconda3/bin/python"
CLI = HERE / "gpdk45_pvt_report.py"

spec = importlib.util.spec_from_file_location("pvt", CLI)
pvt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pvt)

HEADER = ["tag", "divides", "f_in_GHz", "f_out_MHz", "ratio", "power_mW", "delay_ps", "pdp_fJ",
          "max_phase_step_err_deg", "swing_lo", "swing_hi", "phases_deg", "phase_steps_deg",
          "periods_averaged", "i_avg_mA", "reason"]
FAIL_REASON = ("ratio 0.5001 not 2 (Q1 2799.681 MHz); q1 swing 0.035 V < 0.1 V (not toggling); "
               "q1 period 357.18 ps vs 2/f_in 1428.57 ps")


def tag(point):
    c, t, v = point
    return f"{c}_{t}_{v:.1f}"


def ok_row(point, i):
    p = 1.0 + 0.01 * i
    return {"tag": tag(point), "divides": "1", "f_in_GHz": "1.4000", "f_out_MHz": "700.000",
            "ratio": "2.0000", "power_mW": f"{p:.6f}", "delay_ps": f"{20 + i * 0.1:.2f}",
            "pdp_fJ": f"{p * (20 + i * 0.1) / 1000:.3f}", "max_phase_step_err_deg": "39.0",
            "swing_lo": "0.5", "swing_hi": "0.9", "phases_deg": "", "phase_steps_deg": "",
            "periods_averaged": "18", "i_avg_mA": "0.5", "reason": "ok"}


def fail_row(point, reason=FAIL_REASON):
    r = ok_row(point, 0)
    r.update({"divides": "0", "f_out_MHz": "2799.681", "ratio": "0.5001", "power_mW": "nan",
              "delay_ps": "nan", "pdp_fJ": "nan", "max_phase_step_err_deg": "nan", "reason": reason})
    return r


def grid():
    return [(c, t, v) for c in pvt.CORNERS for t in pvt.TEMPS for v in pvt.VDDS]


def write_tsv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(HEADER)
        for r in rows:
            w.writerow([r[h] for h in HEADER])


def run_cli(args):
    return subprocess.run([PY, "-I", str(CLI)] + args, capture_output=True, text=True)


class PvtReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.figs = self.tmp / "figs"
        self.csvdir = self.tmp / "csv"

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, tsv, label):
        res = run_cli(["--tsv", str(tsv), "--label", label, "--fin-ghz", "1.4",
                       "--outdir", str(self.figs), "--csvdir", str(self.csvdir)])
        self.assertEqual(res.returncode, 0, res.stderr)
        return res

    def _csv_rows(self, label):
        with open(self.csvdir / f"pvt_{label}.csv", newline="") as fh:
            return list(csv.DictReader(fh))

    def _json(self, label):
        with open(self.csvdir / f"pvt_summary_{label}.json") as fh:
            return json.load(fh)

    def test_all_pass(self):
        rows = [ok_row(p, i) for i, p in enumerate(grid())]
        tsv = self.tmp / "allpass.tsv"
        write_tsv(tsv, rows)
        self._run(tsv, "allpass")
        s = self._json("allpass")
        self.assertEqual(s["pass_count"], 45)
        self.assertEqual(s["total"], 45)
        self.assertEqual(s["failing"], [])
        self.assertEqual(s["typical_status"], "pass")
        self.assertIsNotNone(s["passing_metrics"]["delay_ps"]["typical"])
        self.assertEqual(len(self._csv_rows("allpass")), 45)
        self.assertTrue((self.figs / "fig_pvt_heatmap_allpass.png").exists())
        self.assertTrue((self.figs / "fig_pvt_delay_power_allpass.png").exists())

    def test_partial_fail_and_missing(self):
        rows = []
        for i, p in enumerate(grid()):
            if p[0] == "tt" and p[1] == 125:
                rows.append(fail_row(p))
            elif p == ("ss", 27, 1.0):
                continue  # missing row
            else:
                rows.append(ok_row(p, i))
        tsv = self.tmp / "partial.tsv"
        write_tsv(tsv, rows)
        self._run(tsv, "partial")
        s = self._json("partial")
        self.assertEqual(s["pass_count"], 45 - 3 - 1)
        self.assertEqual(s["pass_by_temp_C"]["125"]["pass"], 15 - 3)
        self.assertEqual(s["pass_by_corner"]["tt"]["pass"], 9 - 3)
        self.assertEqual(s["pass_by_corner"]["ss"]["pass"], 8)
        self.assertEqual(s["typical_status"], "pass")
        tags = {f["tag"] for f in s["failing"]}
        self.assertIn("ss_27_1.0", tags)  # missing row reported as FAIL
        self.assertIn("tt_125_0.9", tags)
        for f in s["failing"]:
            self.assertNotIn("(", f["reason"])
            self.assertLessEqual(len(f["reason"]), pvt.REASON_MAX)
        ratio_fail = [f for f in s["failing"] if f["tag"] == "tt_125_0.9"][0]
        self.assertEqual(ratio_fail["reason"], "ratio 0.5001 not 2")
        csv_rows = self._csv_rows("partial")
        self.assertEqual(len(csv_rows), 45)  # FAIL rows kept
        fail_csv = [r for r in csv_rows if r["Corner"] == "tt" and r["Temp_C"] == "125"]
        self.assertEqual(len(fail_csv), 3)
        self.assertEqual(fail_csv[0]["Delay_ps"], "nan")

    def test_error_nan_row(self):
        rows = [ok_row(p, i) for i, p in enumerate(grid())]
        rows[10] = fail_row(grid()[10], reason="ERROR: spectre exited with status 1")
        rows[11] = dict(ok_row(grid()[11], 11), reason="ok", delay_ps="nan", pdp_fJ="nan")
        tsv = self.tmp / "error.tsv"
        write_tsv(tsv, rows)
        self._run(tsv, "error")
        s = self._json("error")
        self.assertEqual(s["pass_count"], 43)
        reasons = {f["tag"]: f["reason"] for f in s["failing"]}
        self.assertTrue(reasons[tag(grid()[10])].startswith("ERROR: spectre exited"))
        self.assertEqual(reasons[tag(grid()[11])], "nan metrics")
        self.assertIsNotNone(s["passing_metrics"]["power_mW"]["min"])
        csv_rows = self._csv_rows("error")
        self.assertEqual(len(csv_rows), 45)

    def test_unrecognised_tag_ignored(self):
        rows = [ok_row(p, i) for i, p in enumerate(grid())]
        rows.append(fail_row(("tt", 27, 1.0)))
        rows[-1]["tag"] = "ERROR_run"
        tsv = self.tmp / "badtag.tsv"
        write_tsv(tsv, rows)
        self._run(tsv, "badtag")
        s = self._json("badtag")
        self.assertEqual(s["pass_count"], 45)
        self.assertEqual(s["unparsed_tags"], ["ERROR_run"])

    def test_compare_mode(self):
        rows = [ok_row(p, i) for i, p in enumerate(grid())]
        a = self.tmp / "pvt_A.tsv"
        b = self.tmp / "pvt_B.tsv"
        rows_b = [fail_row(p) if p[1] == 125 else ok_row(p, i) for i, p in enumerate(grid())]
        write_tsv(a, rows)
        write_tsv(b, rows_b)
        res = run_cli(["--compare", str(a), str(b), str(self.tmp / "missing.tsv")])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("| pvt_A | 45 |", res.stdout)
        self.assertIn("| pvt_B | 30 |", res.stdout)
        self.assertIn("not found", res.stdout)

    def test_absent_tsv_note(self):
        res = run_cli(["--tsv", str(self.tmp / "pvt_B6.tsv"), "--label", "B_6g",
                       "--outdir", str(self.figs), "--csvdir", str(self.csvdir)])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("not found", res.stdout)
        self.assertFalse(self.csvdir.exists())


if __name__ == "__main__":
    unittest.main()
