#!/usr/bin/env python3
"""Write the 45 nm (GPDK045) report files. Numbers come only from files; nothing is typed by hand.

Outputs (REPORT_DIR, default <repo>/report/gpdk045):
  23ECE302_Theory_Assignment_gpdk045.md             always written (no simulation data; the 45 nm
                                                     starting sizes are constants given in the task)
  23ECE383_System_Design_Project_Report_gpdk045.md  written only if the provenance gate passes

Inputs (RESULTS_DIR, default <repo>/results):
  gpdk045_provenance.json    gate: device must be g45n1svt and model_file must contain gpdk045
  gpdk045_metrics_tt27.json  nominal point (tt, 27 C, 1.0 V); if it did not divide the report says so
  gpdk045_pvt_summary.csv    one row per PVT point written by gpdk45_collect.py
  gpdk045_layout_drc.json    optional, keys drc_errors and lvs_clean; absent means layout NOT DONE
Netlist: spectre/divider_gpdk45.scs (device sizes and loads are read from it for the lab report; its
SHA-256 is compared with the one recorded in the provenance file).

Exit 2 when the lab report is refused (gate failure or missing/invalid input).
"""
import csv
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = pathlib.Path(os.environ.get("RESULTS_DIR", str(ROOT / "results")))
REPORT = pathlib.Path(os.environ.get("REPORT_DIR", str(ROOT / "report" / "gpdk045")))
NETLIST = ROOT / "spectre" / "divider_gpdk45.scs"
DEVICE = "g45n1svt"
PVT_FILE = "gpdk045_pvt_summary.csv"
PVT_COLS = ["Corner", "Temp_C", "VDD_V", "Divides", "f_out_MHz", "Delay_ps", "Power_mW", "PDP_fJ",
            "MaxPhaseStepErr_deg_or_reason"]
MET_KEYS = ["f_in_ghz", "f_out_mhz", "division_ratio", "phase_deg", "phase_steps_deg",
            "max_phase_step_error_deg", "swing_v", "i_avg_ma", "power_mw", "periods_averaged",
            "ck_to_q_delay_ps", "pdp_fj", "vdd_v"]
# Planned PVT matrix: PDK corners from models/spectre/gpdk045.scs, temperatures, and VDD = 1.0 V +/-10 %.
CORNERS = ["tt", "ff", "ss", "fs", "sf"]
TEMPS = [-40, 27, 125]
VDDS = [0.9, 1.0, 1.1]
# Kuo et al., IEEE MWTL 35(5), 2025. Literature values quoted for comparison only, not re-measured.
PAPER = {"process": "180 nm TSMC", "f_in_ghz": 1.4, "power_mw": 2.34, "phase_err_deg": 3.75,
         "core_um": "91.7 x 52.9"}
# 45 nm starting values for the theory assignment (given in the task; not read from the netlist).
THEORY_SIZES = [("M1, M2", "240 nm", "45 nm", "Sampling pair, unit device"),
                ("M3, M4", "240 nm", "45 nm", "Hold pair, unit device"),
                ("M5, M6", "240 nm", "45 nm", "Clock switches (CK, CKb), unit devices"),
                ("M7", "480 nm", "90 nm", "Long channel so it acts as a current source in saturation")]
THEORY_LOAD = "8 kOhm"
REASON = {"M1": "Sampling pair, unit device", "M2": "Sampling pair, unit device",
          "M3": "Hold pair, unit device", "M4": "Hold pair, unit device",
          "M5": "Clock switch (CK), unit device", "M6": "Clock switch (CKb), unit device",
          "M7": "Long channel so it acts as a current source in saturation"}


def refuse(msg):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(2)


def read_json(name):
    p = RESULTS / name
    return json.loads(p.read_text()) if p.exists() else None


def nm(v):   # "240n" -> "240 nm"
    return v[:-1] + " nm" if v.endswith("n") else v


def kohm(v):  # "8k" -> "8 kOhm"
    return v[:-1] + " kOhm" if v.endswith("k") else v


def netlist_design():
    """Device sizes, bias, supply and loads as written in the current netlist, plus its SHA-256."""
    txt = NETLIST.read_text()
    sha = hashlib.sha256(NETLIST.read_bytes()).hexdigest()
    sizes = {}
    for m in re.finditer(r"^\s*(M\d)\s*\([^)]*\)\s*" + DEVICE + r"\s+w=(\S+)\s+l=(\S+)", txt, re.M):
        sizes.setdefault(m.group(1), (m.group(2), m.group(3)))
    pline = next((l for l in txt.splitlines() if l.startswith("parameters")), "")
    params = dict(re.findall(r"(\w+)=(\S+)", pline))
    if sorted(sizes) != ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]:
        refuse(f"could not read M1-M7 sizes from {NETLIST}")
    for key in ("rl", "cl", "vb", "vdd"):
        if key not in params:
            refuse(f"parameter {key} not found in {NETLIST}")
    return sizes, params, sha


def gate(prov):
    """Return None if the provenance names the gpdk045 device and model, else the reason."""
    if prov is None:
        return "results/gpdk045_provenance.json does not exist"
    if prov.get("device") != DEVICE:
        return f"provenance device is {prov.get('device')!r}, expected {DEVICE}"
    mf = prov.get("model_file") or ""
    if "gpdk045" not in mf:
        return f"provenance model file {mf!r} does not contain gpdk045"
    return None


def theory_md():
    rows = "\n".join(f"| {d} | {w} | {l} | {why} | ___ |" for d, w, l, why in THEORY_SIZES)
    rows += f"\n| R1, R2 (load) | {THEORY_LOAD} | n/a | Load; the paper uses 1.5 kOhm (see below) | ___ |"
    return f"""# 23ECE302 Theory Assignment: Multiphase Divide-by-Two CMOS Frequency Divider (GPDK045, 45 nm)

Reference: Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," IEEE Microw. Wireless Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025. Section and figure numbers below refer to that paper. The process here is the Cadence GPDK045 (45 nm) kit. The device is `g45n1svt` (the 1.0 V standard-Vt NMOS, Virtuoso cell nmos1v).

## Section 1: Transistor schematic (7 marks)

The divider is four cascaded differential D-latches (paper Figs. 2 and 3). A single latch has:

| Device | Role | Connections (drain, gate, source) |
|---|---|---|
| M1, M2 | Sampling differential pair | Q / D / xs and Qb / Db / xs |
| M5 | Positive-controlled sampling switch | xs / CK / tail |
| M3, M4 | Hold cross-coupled pair | Q / Qb / xh and Qb / Q / xh |
| M6 | Negative-controlled hold switch | xh / CKb / tail |
| M7 | NMOS tail current source, saturation | tail / bias / ground |
| R1, R2 | Resistive loads | VDD to Q and VDD to Qb |

Latch 1 and latch 4 sample when CK is high; latch 2 and latch 3 sample when CKb is high (they receive CK and CKb swapped).
The alternating cross-connections between latches are

- Q1b to D2, Q2 to D3, Q3b to D4, Q4 to D1b (and the complementary signals to Db).

Operation: when CK is high, latch 1 samples and latch 2 holds; when CK falls the roles swap. A signal therefore needs two
input clock periods to travel the loop once, which gives divide-by-two. Because the signal passes through latches whose
delays add up, the outputs are separated by multiples of the latch delay Td, and f0, f45, ..., f315 are taken from the
eight output nodes. Draw the full schematic of Fig. 2 with every net labelled and mark which latch uses CK and which CKb.

## Section 2: Sizing concept and Elmore delay (8 marks)

**Sizing rules (paper Sec. II, applied to 45 nm starting values).**
- Each unit nMOS except M7 uses the 45 nm channel length (L = 45 nm) and W = 240 nm.
- M7 uses a longer channel (L = 90 nm, W = 480 nm) so that it behaves as a current source in saturation.
- The gate capacitance is assumed equal to one diffusion capacitance, called C.
- The nMOS turn-on resistance R is designed to be twice the load resistance R1 (so R1 = R/2) to obtain equal rise and
  fall times. M7 is always on, so node b is approximately grounded.

**Elmore delay (paper Eqs. 1 and 2, Fig. 5).** The Elmore delay of a path is the sum of the RC products along the
discharging (or charging) path.
1. Falling output (Fig. 5b): node a has already discharged to ground through capacitance 2C and resistance R/2. Node Q1 has
   capacitance (6 + 2)C = 8C and resistance R/2 to ground, so

   t_pdf = (8C)(R/2) = 4RC.
2. Rising output (Fig. 5c): the load is R1 = R/2 charging the same 8C, so

   t_pdr = (8C)(R1) = (8C)(R/2) = 4RC.
3. Hence t_pdr = t_pdf: equal rise and fall delays, which keeps the output symmetric.

**Speed limit.** Each latch has delay Td. Sampling and holding each take half a clock period, and a signal passes through two
latches (2 Td) in a half period, so the maximum input frequency is limited by 2 Td < T_CK / 2. Equally spaced 45 degree
phases need the delay step 2 Td to match T_CK / 4 (T_CK close to 8 Td).

**Sizing table (45 nm starting values; the tuned-value column is filled after the gpdk045 sweep).**

| Device | W | L or R | Reason | Tuned value |
|---|---|---|---|---|
{rows}

**Why the load is 8 kOhm and not the paper's 1.5 kOhm.** The paper uses R1 = R2 = 1.5 kOhm. A pre-check on a generic
LEVEL=1 180 nm model (not the gpdk045 model; not a gpdk045 result) showed that the latch with 1.5 kOhm did not divide: the
hold pair must have gm x R above 1 to regenerate the state, and at 1.5 kOhm it did not. The 45 nm starting value is therefore
8 kOhm. The required value depends on the device transconductance, which differs between the generic model and gpdk045, so
the load must be retuned on gpdk045 and the tuned-value column records the result.
"""


def span(vals, fmt):
    return "no passing points" if not vals else f"{fmt(min(vals))} to {fmt(max(vals))}"


def build_matrix(rows):
    """Planned 5 x 3 x 3 grid. Absent points become MISSING rows; extra rows (bad tags) are kept."""
    index, extra = {}, []
    for r in rows:
        try:
            key = (r["Corner"].lower(), int(r["Temp_C"]), round(float(r["VDD_V"]), 2))
        except ValueError:
            extra.append(r)
            continue
        index.setdefault(key, r)
    full = []
    for c in CORNERS:
        for t in TEMPS:
            for v in VDDS:
                r = index.get((c, t, round(v, 2)))
                if r is None:
                    r = {"Corner": c.upper(), "Temp_C": str(t), "VDD_V": f"{v:.1f}", "Divides": "MISSING",
                         "f_out_MHz": "", "Delay_ps": "", "Power_mW": "", "PDP_fJ": "",
                         "MaxPhaseStepErr_deg_or_reason": "MISSING: no raw file"}
                full.append(r)
    return full + extra, len(CORNERS) * len(TEMPS) * len(VDDS)


def lab_md(prov, m, rows, drc, sizes, params, nl_sha):
    planned_rows, n_planned = build_matrix(rows)
    ok = [r for r in planned_rows if r["Divides"] == "PASS"]
    bad = [r for r in planned_rows if r["Divides"] == "FAIL"]
    missing = [r for r in planned_rows if r["Divides"] == "MISSING"]
    n_present = n_planned - len(missing)
    dl = [float(r["Delay_ps"]) for r in ok]
    pw = [float(r["Power_mW"]) for r in ok]
    pd = [float(r["PDP_fJ"]) for r in ok]
    nom_ok = bool(m.get("divides"))
    vdd_nom = float(params["vdd"])
    fail_txt = "; ".join(
        (f"{r['Corner']} {r['Temp_C']} C {r['VDD_V']} V" if r["Temp_C"] else r["Corner"]) +
        f" ({r['MaxPhaseStepErr_deg_or_reason'].replace('FAIL: ', '')})" for r in bad) or "none"
    miss_txt = "; ".join(f"{r['Corner']} {r['Temp_C']} C {r['VDD_V']} V" for r in missing) or "none"
    corners_txt = ", ".join(c.upper() for c in CORNERS)
    temps_txt = ", ".join(str(t) for t in TEMPS)
    vdds_txt = ", ".join(f"{v:.1f}" for v in VDDS)

    def note(r):
        if r["Divides"] == "PASS":
            return f"{float(r['MaxPhaseStepErr_deg_or_reason']):.2f} deg"
        return r["MaxPhaseStepErr_deg_or_reason"]
    table = "\n".join(
        f"| {r['Corner']} | {r['Temp_C']} | {r['VDD_V']} | {r['Divides']} | {r['Delay_ps'] or '-'} | "
        f"{r['Power_mW'] or '-'} | {r['PDP_fJ'] or '-'} | {note(r)} |" for r in planned_rows)

    if drc is None:
        layout_txt = ("**NOT DONE.** No layout DRC/LVS result file (`results/gpdk045_layout_drc.json`) exists, so no DRC "
                      "or LVS result is reported here. No layout area is claimed.")
        layout_status = "Not done"
    else:
        clean = "yes" if drc["lvs_clean"] else "no"
        layout_txt = (f"DRC errors: {drc['drc_errors']}. LVS clean: {clean}. Source: results/gpdk045_layout_drc.json. "
                      "No layout area is claimed (the file holds no area value).")
        layout_status = f"DRC errors {drc['drc_errors']}, LVS clean: {clean}"

    if nl_sha == prov.get("netlist_sha256"):
        nl_note = ("The netlist hash matches the one recorded in the provenance file, so the netlist values below are the "
                   "ones that were simulated.")
        nl_warn = ""
    else:
        nl_note = ("**Warning:** the netlist in the repository is not the one that was simulated (SHA-256 differs from the "
                   "provenance record). The values in Section 1 are read from the current file and may not match the run.")
        nl_warn = "\n> " + nl_note
        print("WARNING: netlist SHA-256 differs from the provenance record", file=sys.stderr)

    status = f"""# 23ECE383 System Design Project Report: 8-Phase Divide-by-Two Frequency Divider (GPDK045, 45 nm)

> **Status of this document.** Every number below is generated by `scripts/build_gpdk45_reports.py` from
> `results/gpdk045_metrics_tt27.json`, `results/gpdk045_pvt_summary.csv` and `results/gpdk045_provenance.json`. These come
> from Spectre runs on the GPDK045 model file `{prov.get('model_file', '')}` (device `{prov.get('device')}`). The base
> netlist is `spectre/divider_gpdk45.scs` with section `{prov.get('section', '')}`; the run script substitutes each corner
> name into that line for the PVT points. The run recorded netlist SHA-256 `{prov.get('netlist_sha256', '')}` and
> {len(prov.get('raw_files', []))} raw result files. PVT corners are the PDK corners tt, ff, ss, fs and sf from
> `models/spectre/gpdk045.scs`. The generic 180 nm pre-check is pointed to in Section 9 only; none of its numbers appear in
> the tables below.{nl_warn}

"""

    s1 = f"""## 1. Design specification and topology
Reference design: Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider", IEEE MWTL 35(5), 2025.
Four cascaded differential D-latches, driven by CK / CKb, with alternating cross-connections
Q1b to D2, Q2 to D3, Q3b to D4, Q4 to D1b. Each latch: sample pair M1/M2, hold pair M3/M4, clock switches M5 (CK) and
M6 (CKb), tail M7, loads R1/R2. Devices are `{DEVICE}` (the 1.0 V standard-Vt NMOS, Virtuoso cell nmos1v).

| Item | Value (from the current netlist) |
|---|---|
| Supply (nominal) | {vdd_nom:.1f} V; PVT points use {vdds_txt} V |
| M1-M6 | W/L = {nm(sizes['M1'][0])} / {nm(sizes['M1'][1])} |
| M7 (tail) | W/L = {nm(sizes['M7'][0])} / {nm(sizes['M7'][1])}, gate bias {float(params['vb']):g} V |
| Loads R1 = R2 | {kohm(params['rl'])} |
| Output load | {params['cl']} on each of the 8 outputs |

The sizes and bias are the starting values carried over from the 180 nm design (see the netlist header). They were not
tuned for gpdk045 in this run. {nl_note}
"""

    if nom_ok:
        missing_keys = [k for k in MET_KEYS if k not in m]
        if missing_keys:
            refuse(f"lab report not written: metrics file lacks keys {missing_keys}")
        ph = m["phase_deg"]
        steps = m["phase_steps_deg"]
        sw = m["swing_v"]["v(q1)"]
        err = m["max_phase_step_error_deg"]
        paper_err = PAPER["phase_err_deg"]
        within = "within" if err <= paper_err else "not within"
        phase_rows = "\n".join(f"| {k.upper()} | {v:.2f} |" for k, v in ph.items())
        steps_txt = ", ".join(f"{s:.2f}" for s in steps)
        s2 = f"""## 2. Functionality and 8-phase transient analysis (10 marks)
Measured from the transient waveform on the nominal point (tt, 27 C, {m['vdd_v']:g} V), not assumed:

| Quantity | Result |
|---|---|
| Input frequency | {m['f_in_ghz']:.3f} GHz |
| Output frequency | {m['f_out_mhz']:.2f} MHz (division ratio {m['division_ratio']:.4f}) |
| Output swing, V(Q1) (single-ended) | {sw[0]:.2f} V to {sw[1]:.2f} V |

Phase of each output relative to the Q1 rising edge:

| Output | Phase (deg) |
|---|---|
{phase_rows}

Adjacent phase steps (deg): {steps_txt}. The ideal is 45 deg for every step, so the **maximum step error is {err:.2f} deg**.
The paper reports phase error within {paper_err} deg on silicon; this gpdk045 nominal point is {within} that bound
({err:.2f} deg against {paper_err} deg).
"""
        s345 = f"""## 3. Power calculation (5 marks)
P = VDD x I_avg, with I_avg the time-average of the supply current over {m['periods_averaged']} whole output periods
after start-up (trapezoidal integration of the supply current):
I_avg = {m['i_avg_ma']:.3f} mA, so **P = {m['power_mw']:.3f} mW** at {m['vdd_v']:g} V.

## 4. Delay calculation (5 marks)
Measured clock-to-output delay: for each rising CK edge (50 percent point), the time to the next rising edge on any of the
eight outputs (each at its own mid-swing level), averaged: **{m['ck_to_q_delay_ps']:.1f} ps**.
The Elmore expressions for this latch are derived in the 302 theory assignment; no separate Elmore number is given here.

## 5. Power-delay product (5 marks)
PDP = P x t_d = {m['power_mw']:.3f} mW x {m['ck_to_q_delay_ps']:.1f} ps = **{m['pdp_fj']:.2f} fJ**
(unit check: 1 mW x 1 ps = 1 fJ).
"""
        s8 = f"""## 8. Comparison with the paper (literature values)
Kuo et al. report, for their {PAPER['process']} design: {PAPER['f_in_ghz']} GHz operation, {PAPER['power_mw']} mW, phase error
within {paper_err} deg, and a core of {PAPER['core_um']} um including resistors. These are literature values and were not
re-measured here. Our gpdk045 nominal point gives an input of {m['f_in_ghz']:.3f} GHz, power {m['power_mw']:.3f} mW and a
maximum phase step error of {err:.2f} deg ({within} the {paper_err} deg bound). Layout area is not reported (layout status:
{layout_status}). The comparison is not like-for-like: the process is GPDK045 (45 nm) rather than {PAPER['process']}, the
sizes and load are unoptimised starting values (Section 1), and the supply is {vdd_nom:g} V. This report does not claim that
the design matches or beats the paper.
"""
        summary = f"""| Functionality | 10 | Measured on gpdk045, nominal point (tt, 27 C, {m['vdd_v']:g} V) divides by two |
| Power | 5 | {m['power_mw']:.3f} mW (nominal point) |
| Delay | 5 | {m['ck_to_q_delay_ps']:.1f} ps (nominal point) |
| PDP | 5 | {m['pdp_fj']:.2f} fJ (mW x ps = fJ) |"""
    else:
        reason = m.get("reason") or m.get("status") or "no reason recorded"
        s2 = f"""## 2. Functionality and 8-phase transient analysis (10 marks)
**The nominal point (tt, 27 C, {vdd_nom:g} V) does not divide by two.** Result: FAIL. Reason recorded by the collector:
{reason}. No phase measurement is reported, because the 8-phase analysis needs a divide-by-two waveform.
"""
        nm_txt = "not measured (nominal point does not divide)"
        s345 = f"""## 3. Power calculation (5 marks)
{nm_txt}.

## 4. Delay calculation (5 marks)
{nm_txt}.

## 5. Power-delay product (5 marks)
{nm_txt}.
"""
        s8 = f"""## 8. Comparison with the paper (literature values)
No comparison is made: the nominal point did not divide, so there are no gpdk045 frequency, power or phase figures to set
against Kuo et al. ({PAPER['process']}, {PAPER['f_in_ghz']} GHz, {PAPER['power_mw']} mW, phase error within
{PAPER['phase_err_deg']} deg, core {PAPER['core_um']} um). This report does not claim that the design matches or beats the
paper.
"""
        summary = f"""| Functionality | 10 | FAIL on gpdk045 nominal point: {reason} |
| Power | 5 | not measured |
| Delay | 5 | not measured |
| PDP | 5 | not measured |"""

    if ok:
        passing_txt = (f"Among passing points, delay spans {span(dl, lambda x: f'{x:.1f}')} ps, power "
                       f"{span(pw, lambda x: f'{x:.3f}')} mW and PDP {span(pd, lambda x: f'{x:.2f}')} fJ.")
    else:
        passing_txt = "No point passes, so no delay, power or PDP range is given."
    s6 = f"""## 6. PVT sensitivity analysis (5 marks)
Planned matrix: corners {corners_txt} (PDK corners from `models/spectre/gpdk045.scs`); temperatures {temps_txt} C; VDD
{vdds_txt} V (nominal {vdd_nom:g} V with +/-10 percent). **{n_present} of {n_planned} planned points were run;
{len(ok)} divide by two, {len(bad)} fail to divide, {len(missing)} missing (no raw file).**
Failed points: {fail_txt}. Missing points: {miss_txt}. Failures and missing points are kept in the table.

| Corner | Temp (C) | VDD (V) | Divides | Delay (ps) | Power (mW) | PDP (fJ) | Max phase step error / reason |
|---|---|---|---|---|---|---|---|
{table}

{passing_txt}
"""

    s7 = f"""## 7. Physical layout and DRC (5 marks)
{layout_txt}
"""
    s9 = """## 9. Reference: generic 180 nm pre-check
Pointer only. The generic LEVEL=1 180 nm pre-check (`results/metrics_baseline.json`, `results/pvt_summary_table.csv`,
`report/23ECE383_System_Design_Project_Report.md`) uses a different model and is not comparable to this report. Its
numbers are not used in any table above.
"""
    s10 = f"""## 10. Summary and rubric status
| Rubric item | Marks | Status |
|---|---|---|
{summary}
| PVT | 5 | {len(ok)} of {n_planned} planned points divide; {len(bad)} FAIL and {len(missing)} MISSING kept in Section 6 |
| Layout | 5 | {layout_status} |
| Report | 5 | This document |

Reproduce: `python -I scripts/gpdk45_collect.py <raw_dir>` then `python -I scripts/build_gpdk45_reports.py`.
"""
    return status + s1 + "\n" + s2 + "\n" + s345 + "\n" + s6 + "\n" + s7 + "\n" + s8 + "\n" + s9 + "\n" + s10


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    p302 = REPORT / "23ECE302_Theory_Assignment_gpdk045.md"
    p302.write_text(theory_md())
    print(f"wrote {p302}")

    prov = read_json("gpdk045_provenance.json")
    reason = gate(prov)
    if reason:
        refuse(f"lab report not written: {reason}. Run the Cadence Spectre PVT run and scripts/gpdk45_collect.py first.")
    m = read_json("gpdk045_metrics_tt27.json")
    if m is None:
        refuse("lab report not written: results/gpdk045_metrics_tt27.json does not exist")
    pvt = RESULTS / PVT_FILE
    if not pvt.exists():
        refuse(f"lab report not written: results/{PVT_FILE} does not exist")
    with open(pvt, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != PVT_COLS:
            refuse(f"lab report not written: {PVT_FILE} header is {reader.fieldnames}")
        rows = list(reader)
    drc = read_json("gpdk045_layout_drc.json")
    if drc is not None and not ("drc_errors" in drc and "lvs_clean" in drc):
        refuse("lab report not written: gpdk045_layout_drc.json lacks drc_errors or lvs_clean")
    sizes, params, nl_sha = netlist_design()

    p383 = REPORT / "23ECE383_System_Design_Project_Report_gpdk045.md"
    p383.write_text(lab_md(prov, m, rows, drc, sizes, params, nl_sha))
    print(f"wrote {p383}")


if __name__ == "__main__":
    main()
