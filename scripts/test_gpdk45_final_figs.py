#!/usr/bin/env python3
"""End-to-end test of gpdk45_final_figs.py against the real final Spectre files.

Runs the script into a temporary outdir (and a temporary JSON path, so the real
analysis.json is not touched), then checks the figures exist with size > 20 kB, the
mean-supply-current check against the tsv i_avg_mA (within 1 %), and that two PNGs open
with PIL at 300 dpi.

Run: /home/parshu/miniconda3/bin/python -I scripts/test_gpdk45_final_figs.py
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIGS = os.path.join(HERE, "gpdk45_final_figs.py")
FINALS = os.path.join(ROOT, "results", "gpdk045", "final")

EXPECTED = [
    "fig_tran_D_1p4.png",
    "fig_tran_B_6g.png",
    "fig_tran_unsized.png",
    "fig_phase_steps.png",
    "fig_tail_saturation_D_1p4.png",
    "fig_tail_saturation_B_6g.png",
    "fig_supply_current.png",
]


def read_tsv_i_avg(name):
    with open(os.path.join(FINALS, name + ".tsv")) as f:
        row = next(csv.DictReader(f, delimiter="\t"))
    return float(row["i_avg_mA"])


class FinalFiguresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="gpdk45_figs_test_")
        cls.outdir = os.path.join(cls.tmp, "figures")
        cls.json_path = os.path.join(cls.tmp, "analysis.json")
        proc = subprocess.run(
            [sys.executable, "-I", FIGS, "--finals", FINALS, "--outdir", cls.outdir,
             "--json", cls.json_path],
            capture_output=True, text=True)
        cls.returncode = proc.returncode
        cls.stdout = proc.stdout
        cls.stderr = proc.stderr

    def test_script_exits_clean(self):
        self.assertEqual(self.returncode, 0, self.stderr[-2000:])

    def test_figures_exist_and_are_large(self):
        for fn in EXPECTED:
            path = os.path.join(self.outdir, fn)
            self.assertTrue(os.path.isfile(path), fn)
            self.assertGreater(os.path.getsize(path), 20 * 1024, fn)

    def test_mean_supply_current_matches_tsv(self):
        with open(self.json_path) as f:
            doc = json.load(f)
        for name in ["D_1p4", "B_6g"]:
            ref = read_tsv_i_avg(name)
            m = doc["designs"][name]
            for key in ["supply_avg_ma_steady", "supply_avg_ma_2_periods"]:
                rel = abs(m[key] - ref) / ref
                self.assertLessEqual(rel, 0.01, f"{name} {key}: {m[key]} vs tsv {ref}")

    def test_two_pngs_open_at_300_dpi(self):
        for fn in ["fig_tran_D_1p4.png", "fig_phase_steps.png"]:
            with Image.open(os.path.join(self.outdir, fn)) as im:
                w, h = im.size
                self.assertGreater(w, 500)
                self.assertGreater(h, 500)
                dpi = im.info.get("dpi", (0, 0))[0]
                self.assertAlmostEqual(dpi, 300, delta=1)


if __name__ == "__main__":
    unittest.main()
