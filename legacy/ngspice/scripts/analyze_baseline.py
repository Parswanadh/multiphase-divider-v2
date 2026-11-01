#!/usr/bin/env python3
"""Simulate the calibrated baseline at TT/27C/1.8V and write results/metrics_baseline.json
from the MEASURED waveform (nothing is hardcoded)."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from divider_sim import run_case, ROOT

r = run_case(1.8, 27, "TT", keep=str(ROOT / "results/baseline_cal_tran.txt"))
r["source"] = "ngspice, spice/divider_baseline_cal.cir, generic LEVEL=1 deck (not a foundry model)"
(ROOT / "results").mkdir(exist_ok=True)
(ROOT / "results/metrics_baseline.json").write_text(json.dumps(r, indent=2))
print(json.dumps(r, indent=2))
sys.exit(0 if r.get("divides") else 1)
