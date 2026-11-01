#!/usr/bin/env python3
"""Independent checks on the committed results. Exit 1 on any failure. Re-derives numbers from raw waveforms
and compares them with the JSON/CSV, so a hand-typed or stale result file cannot pass."""
import csv, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from measure_tran import measure

R = pathlib.Path(__file__).resolve().parent.parent / "results"
fails = []
def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok: fails.append(name)

m = json.loads((R / "metrics_baseline.json").read_text())
re = measure(str(R / "baseline_cal_tran.txt"), 1.8, 10e-9)           # re-measure from the raw waveform
check("baseline divides by 2", re["divides"], f"ratio {re['division_ratio']:.4f}")
check("f_out = 700 MHz (+-0.1%)", abs(re["f_out_mhz"] - 700) < 0.7, f"{re['f_out_mhz']:.2f}")
check("JSON matches re-measurement (power)", abs(m["power_mw"] - re["power_mw"]) < 1e-6)
check("JSON matches re-measurement (delay)", abs(m["ck_to_q_delay_ps"] - re["ck_to_q_delay_ps"]) < 1e-6)
check("PDP units: mW*ps = fJ", abs(m["pdp_fj"] - m["power_mw"] * m["ck_to_q_delay_ps"]) < 1e-6, f"{m['pdp_fj']:.1f} fJ")
check("Q and Qb in antiphase (phase of Q1b = 180)", abs(m["phase_deg"]["v(q1b)"] - 180) < 0.5)
check("8 distinct phases", len(set(round(v) for v in m["phase_deg"].values())) == 8)
check("every output swings > 0.3 V", all(b - a > 0.3 for a, b in m["swing_v"].values()))
check("power consistent with VDD*Iavg", abs(m["power_mw"] - m["vdd_v"] * m["i_avg_ma"]) < 1e-6)

rows = list(csv.DictReader(open(R / "pvt_summary_table.csv")))
check("PVT has 27 rows (3 corners x 3 T x 3 VDD)", len(rows) == 27, str(len(rows)))
ok = [r for r in rows if r["Divides"] == "PASS"]
check("PVT PDP = power x delay on every PASS row", all(abs(float(r["PDP_fJ"]) - float(r["Power_mW"]) * float(r["Delay_ps"])) < 0.2 for r in ok))
tt = [r for r in rows if r["Corner(synthetic)"] == "TT" and r["Temp_C"] == "27" and r["VDD_V"] == "1.8"][0]
check("PVT TT/27C/1.8V row equals baseline JSON", abs(float(tt["Power_mW"]) - m["power_mw"]) < 0.001)
check("failed corners are kept in the table", any(r["Divides"] == "FAIL" for r in rows), f"{len(rows)-len(ok)} FAIL")
print(f"\nphase steps (deg): {m['phase_steps_deg']}  -> max step error {m['max_phase_step_error_deg']} deg (NOT within 0.5 or 3.75)")
sys.exit(1 if fails else 0)
