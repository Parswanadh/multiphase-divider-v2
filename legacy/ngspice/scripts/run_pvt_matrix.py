#!/usr/bin/env python3
"""PVT sweep of the calibrated baseline: synthetic corners x temperature x VDD (27 runs).
Every row is a simulation; rows that fail to divide are recorded as FAIL, not dropped."""
import csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from divider_sim import run_case, ROOT

rows = []
for corner in ("TT", "FF", "SS"):
    for temp in (-40, 27, 125):
        for vdd in (1.62, 1.80, 1.98):
            try:
                r = run_case(vdd, temp, corner)
            except Exception as e:
                r = {"divides": False, "reason": str(e)[:80]}
            ok = r.get("divides")
            rows.append([corner, temp, vdd, "PASS" if ok else "FAIL",
                         round(r.get("f_out_mhz", 0), 1),
                         round(r["ck_to_q_delay_ps"], 1) if ok else "",
                         round(r["power_mw"], 3) if ok else "",
                         round(r["pdp_fj"], 1) if ok else "",
                         r.get("max_phase_step_error_deg", "") if ok else r.get("reason", "")])
            print(rows[-1], flush=True)
(ROOT / "results").mkdir(exist_ok=True)
with open(ROOT / "results/pvt_summary_table.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Corner(synthetic)", "Temp_C", "VDD_V", "Divides", "f_out_MHz", "Delay_ps", "Power_mW", "PDP_fJ", "MaxPhaseStepErr_deg_or_reason"])
    w.writerows(rows)
print("wrote results/pvt_summary_table.csv")
