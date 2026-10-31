#!/usr/bin/env python3
"""Build report/gpdk045/report_data.json from the gpdk045 result files, then build
the System Design Project Report (.docx and .pdf) with build_academic_docx.py.

Numbers are read at run time from:
  results/gpdk045/final/  unsized.tsv, D_1p4.tsv, B_6g.tsv (nominal runs),
                          analysis.json, *.m7op.txt, D_1p4.m7vdsat.txt,
                          pvt_D.tsv, pvt_B6.tsv, pvt_summary_*.json, fs_B/D/E.tsv
  spectre/divider_gpdk45.scs   device sizes, load capacitance, rise time, temperature
  report/gpdk045/LEDGER.md     measured Ron, its range, and the recorded division pairs
  report/gpdk045/report_data.example.json   paper citation block only
The only typed numbers are the literature constants of Kuo et al. (LITERATURE below).

Usage (from any directory):
  python3 -I scripts/make_report_data.py
"""

import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FINAL = REPO / "results" / "gpdk045" / "final"
GPDK = REPO / "report" / "gpdk045"
FIG_DIR = GPDK / "figures"
SHARED_FIG_DIR = REPO / "report" / "figures"
SCREEN_DIR = GPDK / "screens"
NETLIST = REPO / "spectre" / "divider_gpdk45.scs"
LEDGER = GPDK / "LEDGER.md"
EXAMPLE = GPDK / "report_data.example.json"
BUILDER = REPO / "scripts" / "build_academic_docx.py"
DATA_OUT = GPDK / "report_data.json"
VENV_PY = Path("/home/parshu/vm/rv/bin/python")
BUILT_STEM = "23ECE383_System_Design_Report"
FINAL_STEM = "System_Design_Project_Report_gpdk045"
TITLE = ("Implementation of a Compact Multiphase Divide-by-Two CMOS Frequency Divider "
         "in 45 nm CMOS (Cadence GPDK045)")

# Literature constants of Kuo et al., as stated in the paper. Not re-measured here.
LITERATURE = {
    "process": "TSMC 180 nm",
    "vdd_v": 1.8,
    "f_in_ghz": 1.4,
    "power_mw": 2.34,
    "phase_err_deg": 3.75,
    "core_um": "91.7 x 52.9",
}

PREFIX = {"": 1.0, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12}
GRID_TAG = re.compile(r"^g_(?P<f>[\d.]+)G_(?P<r>[\d.]+)k_(?P<vb>[\d.]+)_(?P<cl>[\d.]+)f_m(?P<m>\d+)$")
PVT_TAG = re.compile(r"^(?P<corner>[a-z]{2})_(?P<temp>-?\d+)_(?P<vdd>\d+\.\d+)$")
EXTRA_FIG_START = 9  # figures 1 to 8 are the named slots


def fail(msg):
    raise SystemExit(f"make_report_data: {msg}")


def num(text):
    if text is None:
        return None
    text = str(text).strip()
    if text in ("", "nan", "n/a", "None"):
        return None
    return float(text)


def rnd(value, digits=4):
    return None if value is None else round(value, digits)


def read_tsv(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def to_si(value, unit):
    """Convert text such as '54.39' + 'nV' to base SI units."""
    return float(value) * PREFIX[unit[:-1]]


def nm(size_text):
    """Netlist size such as '240n' becomes '240 nm'."""
    if not size_text.endswith("n"):
        fail(f"unexpected netlist size {size_text}")
    return f"{float(size_text[:-1]):g} nm"


def to_ps(time_text):
    """Netlist time such as '20p' becomes '20 ps'."""
    if not time_text.endswith("p"):
        fail(f"unexpected netlist time {time_text}")
    return f"{float(time_text[:-1]):g} ps"


def to_ff(cap_text):
    """Netlist capacitance such as '10f' becomes '10 fF'."""
    if not cap_text.endswith("f"):
        fail(f"unexpected netlist capacitance {cap_text}")
    return f"{float(cap_text[:-1]):g} fF"


# ----------------------------------------------------------------- file readers
def read_netlist():
    text = NETLIST.read_text(encoding="utf-8")
    sizes = {}
    for match in re.finditer(r"^\s*(M\d)\s+\(.*?\)\s+g45n1svt\s+w=(\S+)\s+l=(\S+)", text, re.M):
        sizes[match.group(1)] = (match.group(2), match.group(3))
    params_line = re.search(r"^parameters\s+(.*)$", text, re.M)
    temp = re.search(r"temp=(\d+)", text)
    if params_line is None or temp is None or not sizes:
        fail("could not read sizes, parameters or temperature from the netlist")
    params = dict(item.split("=", 1) for item in params_line.group(1).split() if "=" in item)
    return {"sizes": sizes, "params": params, "temp_c": int(temp.group(1))}


def read_ledger():
    text = LEDGER.read_text(encoding="utf-8")
    ron = re.search(r"Ron = ([\d.]+) kOhm", text)
    band = re.search(r"([\d.]+)\.\.([\d.]+) kOhm", text)
    line = next((ln for ln in text.splitlines() if "needs load R" in ln), None)
    if ron is None or band is None or line is None:
        fail("could not read Ron, its range or the division pairs from LEDGER.md")
    yes_text, rest = line.split("divide;", 1)
    no_text = rest.split(" do not", 1)[0]
    pairs = []
    for divides, chunk in ((True, yes_text), (False, no_text)):
        for m_val, r_text in re.findall(r"\(m(\d+),\s*([^)]+)\)", chunk):
            r_val = float(r_text[:-1]) if re.fullmatch(r"[\d.]+k", r_text) else None
            pairs.append({"m": int(m_val), "r_label": r_text, "r_kohm": r_val, "divides": divides})
    return {"ron": float(ron.group(1)), "ron_lo": float(band.group(1)),
            "ron_hi": float(band.group(2)), "pairs": pairs}


def grid_tag(tag):
    m = GRID_TAG.match(tag)
    if m is None:
        fail(f"tag not recognised: {tag}")
    return {"f_ghz": float(m["f"]), "r_kohm": float(m["r"]), "vb": float(m["vb"]),
            "cl_ff": float(m["cl"]), "m": int(m["m"])}


def one_row(name, expect_divides):
    rows = read_tsv(FINAL / name)
    if len(rows) != 1:
        fail(f"{name}: expected one row, found {len(rows)}")
    row = rows[0]
    if (row["divides"].strip() == "1") != expect_divides:
        fail(f"{name}: divides flag differs from the expected design state")
    return row


def op_point(name):
    text = (FINAL / name).read_text(encoding="utf-8")
    vds = re.search(r"d : V\([^)]*\) = ([-\d.eE+]+) (\w+)", text)
    gate = re.search(r"g : V\([^)]*\) = ([-\d.eE+]+) (\w+)", text)
    ids = re.search(r"ids = ([-\d.eE+]+) (\w+)", text)
    region = re.search(r"region = (\w+)", text)
    if not (vds and gate and ids and region):
        fail(f"cannot parse operating point {name}")
    return {"vds_v": to_si(vds.group(1), vds.group(2)),
            "vg_v": to_si(gate.group(1), gate.group(2)),
            "ids_a": to_si(ids.group(1), ids.group(2)),
            "region": region.group(1)}


def vdsat_info(name):
    text = (FINAL / name).read_text(encoding="utf-8")
    vals = {}
    for key, pattern in (("vdsat_v", r"vdsat = ([\d.eE+-]+) mV"),
                         ("vth_v", r"vth = ([\d.eE+-]+) mV")):
        m = re.search(pattern, text)
        if m is None:
            fail(f"cannot parse {key} in {name}")
        vals[key] = float(m.group(1)) / 1000.0
    gm = re.search(r"gm = ([\d.eE+-]+) pS", text)
    gds = re.search(r"gds = ([\d.eE+-]+) mS", text)
    vals["gm_ps"] = float(gm.group(1)) if gm else None
    vals["gds_ms"] = float(gds.group(1)) if gds else None
    return vals


def pvt_block(label, tsv_name, summary_name, f_in):
    rows = read_tsv(FINAL / tsv_name)
    summary = json.loads((FINAL / summary_name).read_text(encoding="utf-8"))
    if abs(summary["f_in_GHz"] - f_in) > 1e-9:
        fail(f"{summary_name}: f_in {summary['f_in_GHz']} differs from {f_in}")
    short_reason = {f["tag"]: f["reason"] for f in summary["failing"]}
    out, passes = [], 0
    for row in rows:
        m = PVT_TAG.match(row["tag"])
        if m is None:
            fail(f"{tsv_name}: tag not recognised: {row['tag']}")
        divides = row["divides"].strip() == "1"
        passes += int(divides)
        if not divides and row["tag"] not in short_reason:
            fail(f"{tsv_name}: failing point {row['tag']} missing from {summary_name}")
        out.append({
            "corner": f"{label} {m['corner']}",
            "temp": int(m["temp"]),
            "vdd": float(m["vdd"]),
            "divides": divides,
            "f_out_mhz": rnd(num(row["f_out_MHz"]), 3) if divides else None,
            "delay_ps": rnd(num(row["delay_ps"]), 2) if divides else None,
            "power_mw": rnd(num(row["power_mW"]), 4) if divides else None,
            "pdp_fj": rnd(num(row["pdp_fJ"]), 2) if divides else None,
            "note": "" if divides else short_reason[row["tag"]],
        })
    if len(rows) != summary["total"] or passes != summary["pass_count"]:
        fail(f"{tsv_name}: {passes}/{len(rows)} pass, {summary_name} says "
             f"{summary['pass_count']}/{summary['total']}")
    return out, summary


def summary_only(name):
    return json.loads((FINAL / name).read_text(encoding="utf-8"))


def fail_text(summary):
    items = summary["failing"]
    by_temp = Counter(f"{f['temp_C']} C" for f in items)
    parts = ", ".join(f"{k}: {v}" for k, v in sorted(by_temp.items(), key=lambda kv: int(kv[0].split()[0])))
    tags = ", ".join(f["tag"] for f in items)
    return f"{summary['pass_count']} of {summary['total']} pass; {len(items)} fail ({parts}): {tags}"


def sweep(name):
    rows = read_tsv(FINAL / name)
    pts = [{"f": num(r["f_in_GHz"]), "ok": r["divides"].strip() == "1",
            "err": num(r["max_phase_step_err_deg"]), "ratio": num(r["ratio"])} for r in rows]
    ok = sorted((p for p in pts if p["ok"]), key=lambda p: p["f"])
    bad = sorted((p for p in pts if not p["ok"]), key=lambda p: p["f"])
    if not ok:
        fail(f"{name}: no dividing point")
    f_max = ok[-1]["f"]
    above = [p for p in bad if p["f"] > f_max]
    return {"f_min": ok[0]["f"], "f_max": f_max,
            "f_fail": above[0]["f"] if above else None,
            "err_min_f": ok[0]["err"], "err_max_f": ok[-1]["err"],
            "n_ok": len(ok), "n": len(pts)}


def t_pair_ps(steps, f_ghz):
    a_deg = min(steps)
    return a_deg / 360.0 * 1e3 / f_ghz


# ----------------------------------------------------------------- report pieces
def device_rows(net, m, r_kohm, vb):
    s = net["sizes"]
    for pair in (("M1", "M2"), ("M3", "M4"), ("M5", "M6")):
        if s[pair[0]] != s[pair[1]]:
            fail(f"{pair} sizes differ in the netlist")
    if s["M1"] != s["M5"]:
        fail("M1 and M5 sizes differ in the netlist")
    return [
        {"device": "M1, M2", "w": nm(s["M1"][0]), "l": nm(s["M1"][1]), "multiplier": m,
         "role": "sampling pair (differential inputs)"},
        {"device": "M3, M4", "w": nm(s["M3"][0]), "l": nm(s["M3"][1]), "multiplier": m,
         "role": "hold pair (cross-coupled regenerative pair)"},
        {"device": "M5", "w": nm(s["M5"][0]), "l": nm(s["M5"][1]), "multiplier": m,
         "role": "switch controlled by CK"},
        {"device": "M6", "w": nm(s["M6"][0]), "l": nm(s["M6"][1]), "multiplier": m,
         "role": "switch controlled by CKb"},
        {"device": "M7", "w": nm(s["M7"][0]), "l": nm(s["M7"][1]), "multiplier": m,
         "role": f"tail current source, gate at vb = {vb:g} V"},
        {"device": "R1, R2", "w": None, "l": None, "multiplier": None,
         "role": f"load resistors, {r_kohm:g} kOhm each"},
    ]


def plotted(name, caption):
    if not (FIG_DIR / f"{name}.png").is_file():
        fail(f"missing plotted figure {name}.png")
    return {"file": f"figures/{name}.png", "caption": caption}


def shared(name, caption):
    if not (SHARED_FIG_DIR / f"{name}.png").is_file():
        fail(f"missing shared figure {name}.png")
    return {"file": f"../figures/{name}.png", "caption": caption}


def screen(name, caption):
    """A Cadence screenshot, or a path that the builder reports as NOT YET AVAILABLE."""
    return {"file": f"screens/{name}.png", "caption": caption}


def screen_or_none(name, caption):
    return screen(name, caption) if (SCREEN_DIR / f"{name}.png").is_file() else None


def verdict(ok):
    return "met" if ok else "not met"


def build_data():
    net = read_netlist()
    led = read_ledger()
    ana = json.loads((FINAL / "analysis.json").read_text(encoding="utf-8"))
    paper = json.loads(EXAMPLE.read_text(encoding="utf-8"))["paper"]

    nom_u = one_row("unsized.tsv", expect_divides=False)
    nom_d = one_row("D_1p4.tsv", expect_divides=True)
    nom_b = one_row("B_6g.tsv", expect_divides=True)
    tag_u, tag_d, tag_b = (grid_tag(r["tag"]) for r in (nom_u, nom_d, nom_b))
    for tag in (tag_u, tag_d, tag_b):
        if abs(tag["cl_ff"] - 10.0) > 1e-9 or net["params"].get("cl") != "10f":
            fail("load capacitance differs from 10 fF")
    a_u = ana["designs"]["unsized"]
    a_d = ana["designs"]["D_1p4"]
    a_b = ana["designs"]["B_6g"]
    if a_d["tsv"]["tag"] != nom_d["tag"] or a_b["tsv"]["tag"] != nom_b["tag"]:
        fail("analysis.json does not match the nominal TSV tags")

    op_u = op_point("unsized.m7op.txt")
    op_d = op_point("D_1p4.m7op.txt")
    op_b = op_point("B_6g.m7op.txt")
    for op, tag in ((op_u, tag_u), (op_d, tag_d), (op_b, tag_b)):
        if abs(op["vg_v"] - tag["vb"]) > 1e-9:
            fail("M7 gate voltage in the operating point differs from vb in the tag")
    vds_info = vdsat_info("D_1p4.m7vdsat.txt")

    # Cross-checks between the TSV and analysis.json (must agree within rounding).
    for label, nom, a in (("D", nom_d, a_d), ("B", nom_b, a_b)):
        if abs(num(nom["delay_ps"]) - a["ck_to_any_output_mean_delay_ps"]) > 0.01:
            fail(f"{label}: delay in the TSV does not match analysis.json")
        rel = abs(num(nom["power_mW"]) - a["supply_avg_ma_steady"]) / num(nom["power_mW"])
        if rel > 0.001:
            fail(f"{label}: power in the TSV differs from the supply-current average by {rel:.4%}")

    f_d, f_b = tag_d["f_ghz"], tag_b["f_ghz"]
    r_u, r_d, r_b = tag_u["r_kohm"], tag_d["r_kohm"], tag_b["r_kohm"]
    m_u, m_d, m_b = tag_u["m"], tag_d["m"], tag_b["m"]

    ron = led["ron"]
    if abs(r_u - ron / 2.0) > 0.005:
        fail("unsized R1 is not Ron/2 from LEDGER.md")
    stack = lambda m: 3.0 * ron / m
    thr_mid = lambda m: 1.1 * stack(m)
    thr_lo = lambda m: 1.1 * 3.0 * led["ron_lo"] / m
    thr_hi = lambda m: 1.1 * 3.0 * led["ron_hi"] / m
    numeric = [p for p in led["pairs"] if p["r_kohm"] is not None]
    ok_pairs = sum(1 for p in numeric if (p["r_kohm"] >= thr_mid(p["m"])) == p["divides"])

    # Elmore relation of the paper: t_pd = (8C)(R/2) = 4 R C with R = 2 R1.
    # kOhm times fF gives ps. T_CK/2 = 500 / f_GHz ps.
    cl_ff = tag_d["cl_ff"]
    td_d = 4.0 * (2.0 * r_d) * cl_ff
    td_b = 4.0 * (2.0 * r_b) * cl_ff
    half_d = 1e3 / (2.0 * f_d)
    half_b = 1e3 / (2.0 * f_b)
    bound_d_met = 2.0 * td_d < half_d
    bound_b_met = 2.0 * td_b < half_b

    # Phase-step law.
    steps_d = [float(x) for x in nom_d["phase_steps_deg"].split(",")]
    steps_b = [float(x) for x in nom_b["phase_steps_deg"].split(",")]
    tp_d = t_pair_ps(steps_d, f_d)
    tp_b = t_pair_ps(steps_b, f_b)

    # Pass/fail data.
    pvt_d, sum_d = pvt_block("D", "pvt_D.tsv", "pvt_summary_D_1p4.json", f_d)
    pvt_b6, sum_b6 = pvt_block("B6", "pvt_B6.tsv", "pvt_summary_B_6g.json", f_b)
    sum_b1 = summary_only("pvt_summary_B_1p4.json")
    sum_e = summary_only("pvt_summary_E_1p4.json")
    sw_b, sw_d, sw_e = sweep("fs_B.tsv"), sweep("fs_D.tsv"), sweep("fs_E.tsv")

    swing_u = a_u["q1_max_v"] - a_u["q1_min_v"]
    swing_d = a_d["q1_max_v"] - a_d["q1_min_v"]
    swing_b = a_b["q1_max_v"] - a_b["q1_min_v"]
    f_out_u_meas = num(nom_u["f_out_MHz"])
    sw_u_mv = swing_u * 1e3

    # ---------------------------------------------------------- metrics
    metrics_u = {
        "f_in_ghz": rnd(num(nom_u["f_in_GHz"]), 3),
        "f_out_mhz": None,
        "power_mw": None,
        "delay_ps": None,
        "pdp_fj": None,
        "max_phase_step_err_deg": None,
        "swing_v": rnd(swing_u, 4),
        "m7_vds_v": rnd(a_u["xd1_tail_max_v"], 4),
        "m7_vdsat_v": None,
    }
    metrics_d = {
        "f_in_ghz": rnd(num(nom_d["f_in_GHz"]), 3),
        "f_out_mhz": rnd(num(nom_d["f_out_MHz"]), 3),
        "power_mw": rnd(num(nom_d["power_mW"]), 4),
        "delay_ps": rnd(num(nom_d["delay_ps"]), 2),
        "pdp_fj": rnd(num(nom_d["pdp_fJ"]), 3),
        "max_phase_step_err_deg": rnd(num(nom_d["max_phase_step_err_deg"]), 2),
        "swing_v": rnd(swing_d, 4),
        "m7_vds_v": rnd(a_d["xd1_tail_max_v"], 4),
        "m7_vdsat_v": rnd(vds_info["vdsat_v"], 4),
    }

    # ---------------------------------------------------------- extras and slots
    extras = [
        ("ring", shared("fig_b_ring_diagram",
                        "Ring interconnection of the four latches (alternating cross-connections), drawn "
                        "programmatically by scripts/build_local_report.py from the baseline netlist "
                        "spice/divider_baseline_cal.cir. The labels are baseline values, not the gpdk045 sizes.")),
        ("tran_b", plotted("fig_tran_B_6g",
                           f"Transient waveforms of design B at {f_b:g} GHz (m = {m_b}, R1 = R2 = {r_b:g} kOhm), "
                           f"plotted from Spectre output. Output period-measured frequency "
                           f"{num(nom_b['f_out_MHz']):.1f} MHz.")),
        ("phase", plotted("fig_phase_steps",
                          "Phase steps between the eight outputs for designs D (1.4 GHz) and B (6 GHz), "
                          "plotted from the nominal Spectre results.")),
        ("tail_d", plotted("fig_tail_saturation_D_1p4",
                           f"Tail (M7) drain voltage of design D at 1.4 GHz compared with the M7 saturation "
                           f"voltage Vdsat = {vds_info['vdsat_v']:.3f} V, plotted from Spectre output.")),
        ("supply", plotted("fig_supply_current",
                           "Supply current drawn from VDD, plotted from Spectre output; the table power is "
                           "VDD times the mean over whole output periods.")),
        ("fsweep", plotted("fig_fsweep",
                           "Frequency sweep of designs B, D and E (fs_B.tsv, fs_D.tsv, fs_E.tsv): divided "
                           "output and maximum phase-step error against input frequency.")),
        ("pvt_dp_d", plotted("fig_pvt_delay_power_D_1p4",
                             "Delay and power over the PVT matrix of design D at 1.4 GHz, plotted from pvt_D.tsv "
                             "(passing points only).")),
        ("pvt_hm_b6", plotted("fig_pvt_heatmap_B_6g",
                              f"PVT pass/fail map of design B at {f_b:g} GHz, plotted from pvt_B6.tsv. "
                              f"{sum_b6['pass_count']} of {sum_b6['total']} points pass.")),
        ("pvt_dp_b6", plotted("fig_pvt_delay_power_B_6g",
                              f"Delay and power over the PVT matrix of design B at {f_b:g} GHz, plotted from "
                              f"pvt_B6.tsv (passing points only).")),
        ("dlatch", screen("schematic_dlatch",
                          "Virtuoso schematic of the D-latch (Cadence GUI screenshot).")),
        ("tb", screen("schematic_tb",
                      "Virtuoso schematic of the testbench (Cadence GUI screenshot).")),
        ("lib", screen("library_manager",
                       "Virtuoso Library Manager showing the cells (Cadence GUI screenshot).")),
        ("drc", screen("drc_result",
                       "Assura DRC result for the layout (Cadence GUI screenshot).")),
    ]
    extra_no = {key: EXTRA_FIG_START + i for i, (key, _) in enumerate(extras)}

    figures = {
        "circuit_diagram": shared("fig_a_latch_schematic",
                                  "Circuit diagram of one differential D-latch (M1 to M7, R1, R2), drawn "
                                  "programmatically by scripts/build_local_report.py from the baseline netlist "
                                  "spice/divider_baseline_cal.cir. The labels on the drawing are baseline values, "
                                  "not the gpdk045 sizes; Tables 1 and 2 give the gpdk045 sizes."),
        "impl_screenshot": screen_or_none("schematic_core",
                                          "Virtuoso schematic of the circuit without sizing (Cadence GUI screenshot)."),
        "waveform_without_sizing": plotted(
            "fig_tran_unsized",
            f"Transient waveforms of the circuit without sizing (m = {m_u}, R1 = R2 = {r_u:g} kOhm) at "
            f"{f_d:g} GHz, plotted from Spectre output (not a simulator screenshot). Q1 swings between "
            f"{a_u['q1_min_v']:.3f} V and {a_u['q1_max_v']:.3f} V ({sw_u_mv:.1f} mV), so the outputs do not divide. "
            f"DC operating point (analysis, t = 0, CK low): M7 region {op_u['region']}, Vds = "
            f"{op_u['vds_v'] * 1e9:.1f} nV, Ids = {op_u['ids_a'] * 1e12:.1f} pA, Vgs = {op_u['vg_v']:g} V."),
        "sized_circuit_screenshot": screen_or_none(
            "schematic_sized", "Virtuoso schematic of the circuit based on the sizing concept (Cadence GUI screenshot)."),
        "waveform_with_sizing": plotted(
            "fig_tran_D_1p4",
            f"Transient waveforms of design D (m = {m_d}, R1 = R2 = {r_d:g} kOhm) at {f_d:g} GHz, plotted from "
            f"Spectre output (not a simulator screenshot). Q1 swings between {a_d['q1_min_v']:.3f} V and "
            f"{a_d['q1_max_v']:.3f} V; output {num(nom_d['f_out_MHz']):.1f} MHz; tail voltage stays between "
            f"{a_d['xd1_tail_min_v'] * 1e3:.1f} mV and {a_d['xd1_tail_max_v'] * 1e3:.1f} mV."),
        "pvt_screenshot": plotted(
            "fig_pvt_heatmap_D_1p4",
            f"PVT pass/fail map of design D at {f_d:g} GHz (5 corners x -40/27/125 C x 0.9/1.0/1.1 V), plotted "
            f"from pvt_D.tsv, not a Cadence screenshot. {sum_d['pass_count']} of {sum_d['total']} points pass."),
        "layout_screenshot": screen_or_none("layout_core", "Virtuoso layout of the divider core (Cadence GUI screenshot)."),
        "layout_waveform": screen_or_none(
            "layout_waveform", "Simulator waveform of the extracted layout (Cadence GUI screenshot)."),
        "extra_figures": [item for _, item in extras],
    }

    # ---------------------------------------------------------- designs
    design_without = {
        "description": (
            f"Unit devices (m = 1) with the paper's rule applied literally: R1 = R2 = Ron/2 = {r_u:g} kOhm, where "
            f"Ron = {ron:g} kOhm is the measured on-resistance of the unit nMOS (LEDGER.md; the Vds sweep gives "
            f"{led['ron_lo']:g} to {led['ron_hi']:g} kOhm). Device sizes are read from spectre/divider_gpdk45.scs. "
            f"At {f_d:g} GHz the eight outputs follow the clock: the period-measured Q1 frequency is "
            f"{f_out_u_meas:.1f} MHz (about twice f_in) but the Q1 swing is only {sw_u_mv:.1f} mV, so these are not "
            f"toggling logic outputs and the circuit does not divide. Delay, PDP and phase error are therefore n/a, and "
            f"the power of a non-dividing circuit is not reported as a result."),
        "devices": device_rows(net, m_u, r_u, tag_u["vb"]),
        "metrics": metrics_u,
    }
    design_with = {
        "description": (
            f"Same topology with the sizing concept: multiplier m = {m_d} scales every device in parallel, load "
            f"R1 = R2 = {r_d:g} kOhm, input {f_d:g} GHz (design D). Stack rule (section Theory): the pull-down "
            f"stack resistance is 3 Ron/m = {stack(m_d):.2f} kOhm, the regeneration threshold 1.1 times that is "
            f"{thr_mid(m_d):.2f} kOhm (band {thr_lo(m_d):.2f} to {thr_hi(m_d):.2f} kOhm for the Ron range), and the "
            f"load {r_d:g} kOhm is above the band. The sizing check at 1.4 GHz and the 6 GHz point (design B, m = "
            f"{m_b}, R1 = R2 = {r_b:g} kOhm, reported in the other information section) use the same rule. The tail "
            f"device M7 is in the triode region in the DC analysis (Vds stays below Vdsat), see the other information "
            f"section."),
        "devices": device_rows(net, m_d, r_d, tag_d["vb"]),
        "metrics": metrics_d,
    }

    # ---------------------------------------------------------- narrative
    d_fail = sum_d["failing"]
    d_fail_text = (
        f"All {len(d_fail)} PVT failures of design D are at 125 C and 0.9 V."
        if d_fail and all(f["temp_C"] == 125 and abs(f["vdd_V"] - 0.9) < 1e-9 for f in d_fail)
        else f"Design D has {len(d_fail)} PVT failures (listed in the PVT table).")
    b_steps = nom_b["phase_steps_deg"].split(",")
    d_steps = nom_d["phase_steps_deg"].split(",")
    dc_b = op_b
    theory = [
        ("Topology. The divider follows Kuo et al. (References): four cascaded differential D-latches with "
         "alternating cross-connections Q1b to D2, Q2 to D3, Q3b to D4 and Q4 to D1b. Latches 2 and 3 have CK "
         "and CKb swapped. Each latch has a sampling pair M1 and M2, a positive-controlled switch M5, a hold pair "
         "M3 and M4, a negative-controlled switch M6, a tail M7 and loads R1 and R2. While CK is high a latch "
         "samples; while CK is low the hold pair regenerates the stored value. The ring connections make the eight "
         "outputs toggle in pairs at half the input frequency, spread around one period."),
        (f"Elmore estimate. In the paper's model the latch delay is t_pdf = t_pdr = (8C)(R/2) = 4RC with "
         f"R1 = R/2, so R = 2 R1, and C is the node capacitance; node b is grounded because M7 is on. The paper "
         f"requires T_CK/2 > 2 Td. With the {cl_ff:g} fF output load, Td = {td_d:.0f} ps for design D against "
         f"T_CK/2 = {half_d:.0f} ps at {f_d:g} GHz (bound {verdict(bound_d_met)}), and Td = {td_b:.0f} ps for "
         f"design B against T_CK/2 = {half_b:.0f} ps at {f_b:g} GHz (bound {verdict(bound_b_met)}). Both designs "
         f"divide in simulation, so this bound is not the limit that decides division here. The Elmore expression "
         f"is used only for the trend of the sizing, not as a sufficient design rule."),
        (f"Stack resistance and regeneration. The output pull-down path is a stack of three series devices (M1, M5, "
         f"M7), so its resistance is about 3 Ron/m. Regeneration of the hold pair needs gm R1 > 1; the margin used "
         f"here is R1 >= 1.1 x (3 Ron/m). With Ron = {ron:g} kOhm (LEDGER.md) the unit stack is {stack(1):.2f} kOhm, "
         f"far above the unsized load of {r_u:g} kOhm, which is why the unsized circuit does not divide. For m = {m_d} "
         f"the threshold is {thr_mid(m_d):.2f} kOhm (band {thr_lo(m_d):.2f} to {thr_hi(m_d):.2f} kOhm), so design D "
         f"at {r_d:g} kOhm passes, while design B at {r_b:g} kOhm lies inside the band and its margin depends on the "
         f"Ron value used. The recorded division results in LEDGER.md agree with this rule for {ok_pairs} of "
         f"{len(numeric)} numeric (m, R) pairs."),
        (f"Phase-step law. Outputs come in pairs. The steps between neighbouring outputs alternate between a and "
         f"90 - a degrees, with a = 360 t_pair f_in. At {f_d:g} GHz the measured steps are {d_steps[0]} and "
         f"{d_steps[1]} deg (a = {min(steps_d):.2f} deg, t_pair = {tp_d:.1f} ps); at {f_b:g} GHz the steps are "
         f"{b_steps[0]} and {b_steps[1]} deg (a = {min(steps_b):.2f} deg, t_pair = {tp_b:.1f} ps). Equal 45 deg "
         f"steps need T_CK = 8 t_pair. Because t_pair differs between the two designs, the phase error is a property "
         f"of each design at a given f_in; in the frequency sweeps it falls as f_in rises and is small only near "
         f"each design's frequency limit. The paper's 3.75 deg is reproduced in magnitude only by design B at 6 GHz."),
        ("Delay and power definitions. Delay is the mean over CK rising edges of the time to the next rising edge "
         "on any of the eight outputs. Power is VDD times the mean supply current over whole output periods. "
         "PDP is power times delay (mW times ps gives fJ). A division is accepted only when all eight outputs run at "
         "f_in/2 within 0.1 percent and each swings at least 0.1 V."),
    ]

    tool_technology = [
        "Simulator: Cadence Spectre 12.1.0 (MMSIM121), run on a 32-bit CentOS 6.5 virtual machine. Layout and "
        "DRC tools in the flow: Virtuoso IC615 and Assura 4.1.",
        "Process: Cadence GPDK045 v6.0, a 45 nm generic PDK. Device g45n1svt (Virtuoso cell nmos1v), a 1.0 V "
        "thin-oxide standard-Vt NMOS modelled with BSIM4. Corners tt, ff, ss, fs and sf from models/spectre/gpdk045.scs.",
        f"Sizes: unit transistor W = {nm(net['sizes']['M1'][0])}, L = {nm(net['sizes']['M1'][1])} for M1 to M6; M7 "
        f"W = {nm(net['sizes']['M7'][0])}, L = {nm(net['sizes']['M7'][1])}; the multiplier m scales every device "
        f"in parallel.",
        f"Stimulus and conditions: VDD = 1.0 V with PVT at 0.9 and 1.1 V; temperature {net['temp_c']} C nominal; "
        f"CK rise and fall {to_ps(net['params']['tr'])}; CKb is CK delayed by half a period; tail bias "
        f"vb = {tag_d['vb']:g} V; {to_ff(net['params']['cl'])} load on each of the eight outputs.",
        "Plots are generated by scripts from the Spectre results; the waveform and PVT figures are plots, not Virtuoso "
        "screenshots, and each caption says so. The two circuit drawings (Figures 1 and 9) are generated "
        "programmatically from the baseline netlist spice/divider_baseline_cal.cir, not from the gpdk045 netlist.",
    ]

    other_info = [
        (f"Second operating point, design B at {f_b:g} GHz: m = {m_b}, R1 = R2 = {r_b:g} kOhm, output "
         f"{num(nom_b['f_out_MHz']):.1f} MHz, power {num(nom_b['power_mW']):.4f} mW, delay "
         f"{num(nom_b['delay_ps']):.2f} ps, PDP {num(nom_b['pdp_fJ']):.3f} fJ, maximum phase-step error "
         f"{num(nom_b['max_phase_step_err_deg']):.2f} deg (steps {b_steps[0]} and {b_steps[1]} deg). Q1 swing "
         f"{a_b['q1_min_v']:.3f} to {a_b['q1_max_v']:.3f} V. The M7 tail voltage reaches {a_b['xd1_tail_max_v'] * 1e3:.1f} mV "
         f"at most. Vdsat of M7 was not extracted for this point, so its saturation check is n/a. The metrics of "
         f"this point are given here, not in Table 3; its PVT matrix is listed in Table 4 under the rows labelled B6."),
        (f"DC operating point (analysis at t = 0, CK low, no tail current). Unsized: M7 {op_u['region']}, "
         f"Vds = {op_u['vds_v'] * 1e9:.1f} nV, Ids = {op_u['ids_a'] * 1e12:.1f} pA. Design D: M7 {op_d['region']}, "
         f"Vds = {op_d['vds_v'] * 1e9:.1f} nV, Ids = {op_d['ids_a'] * 1e12:.1f} pA. Design B: M7 {dc_b['region']}, "
         f"Vds = {dc_b['vds_v'] * 1e9:.1f} nV, Ids = {dc_b['ids_a'] * 1e12:.1f} pA (the same as design D, because "
         f"both designs have m = {m_d} and vb = {tag_d['vb']:g} V and no tail current flows at t = 0). "
         f"Vgs = {op_d['vg_v']:g} V in all three."),
        (f"Tail device M7 (honest finding). In the transient, the tail voltage of design D stays between "
         f"{a_d['xd1_tail_min_v'] * 1e3:.1f} mV and {a_d['xd1_tail_max_v'] * 1e3:.1f} mV, while Vdsat = "
         f"{vds_info['vdsat_v'] * 1e3:.1f} mV (Vth = {vds_info['vth_v'] * 1e3:.1f} mV, gm = {vds_info['gm_ps']:.1f} pS, "
         f"gds = {vds_info['gds_ms']:.3f} mS at the bias). Vds never reaches Vdsat, so M7 operates in the triode "
         f"region. The paper's tail is a saturated current source; this circuit's tail is not, and the report states "
         f"this deviation openly (see Figure {extra_no['tail_d']})."),
        (f"Frequency sweeps (fs_B, fs_D, fs_E). Design B divides from {sw_b['f_min']:g} to {sw_b['f_max']:g} GHz and "
         f"fails at {sw_b['f_fail']:g} GHz, where the output ratio is not 2. Design D (m = {m_d}, R = {r_d:g} kOhm) "
         f"divides from {sw_d['f_min']:g} to {sw_d['f_max']:g} GHz and fails at {sw_d['f_fail']:g} GHz. Design E "
         f"(m = 6, R = 2 kOhm) divides from {sw_e['f_min']:g} to {sw_e['f_max']:g} GHz and fails at "
         f"{sw_e['f_fail']:g} GHz. The maximum phase-step error at the top of each dividing range is "
         f"{sw_b['err_max_f']:.2f} deg (B), {sw_d['err_max_f']:.2f} deg (D) and {sw_e['err_max_f']:.2f} deg (E); at the "
         f"bottom of the range it is {sw_b['err_min_f']:.2f}, {sw_d['err_min_f']:.2f} and {sw_e['err_min_f']:.2f} deg. "
         f"The error falls with input frequency in all three sweeps (Figure {extra_no['fsweep']})."),
        (f"PVT results. Design D at {f_d:g} GHz: {fail_text(sum_d)}. Design B at 1.4 GHz: {fail_text(sum_b1)}. "
         f"Design E (m = 6, R = 2 kOhm) at 1.4 GHz: {fail_text(sum_e)}. Design B at {f_b:g} GHz: {fail_text(sum_b6)}. "
         f"The passing range for design D is power {sum_d['passing_metrics']['power_mW']['min']:.3f} to "
         f"{sum_d['passing_metrics']['power_mW']['max']:.3f} mW and delay {sum_d['passing_metrics']['delay_ps']['min']:.2f} "
         f"to {sum_d['passing_metrics']['delay_ps']['max']:.2f} ps. The PVT tables list design D (1.4 GHz) first and "
         f"design B (6 GHz) second, with the design in the corner column."),
        (f"Delay cross-check. The single-edge CK-to-Q1 delay in analysis.json is "
         f"{a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps for design D and {a_b['ck_to_q1_first_edge_delay_ps']:.2f} ps "
         f"for design B. That is a different quantity (first edge of one output), so it is a cross-check only. The "
         f"table delay is the mean over all eight outputs, which agrees with analysis.json to within 0.01 ps "
         f"({a_d['ck_to_any_output_mean_delay_ps']:.2f} ps for D). Q1 rise and fall times (10 to 90 percent) for D are "
         f"{a_d['q1_rise_10_90_ps']:.1f} ps and {a_d['q1_fall_10_90_ps']:.1f} ps."),
        (f"Power cross-check. The mean supply current of design D from analysis.json is "
         f"{a_d['supply_avg_ma_steady']:.5f} mA, against {num(nom_d['i_avg_mA']):.6f} mA in the TSV, within "
         f"{abs(num(nom_d['power_mW']) - a_d['supply_avg_ma_steady']) / num(nom_d['power_mW']):.3%}. The peak supply current "
         f"in steady state is {a_d['supply_peak_ma_steady']:.3f} mA."),
        (f"Comparison with the paper. Literature values from Kuo et al. (not re-measured here): "
         f"{LITERATURE['process']}, {LITERATURE['vdd_v']} V, {LITERATURE['f_in_ghz']} GHz input, "
         f"{LITERATURE['power_mw']} mW, phase error within {LITERATURE['phase_err_deg']} deg, core "
         f"{LITERATURE['core_um']} um^2. In this generic 45 nm PDK, design D at 1.4 GHz draws "
         f"{num(nom_d['power_mW']):.4f} mW but its phase-step error is {num(nom_d['max_phase_step_err_deg']):.2f} deg; "
         f"design B reaches {num(nom_b['max_phase_step_err_deg']):.2f} deg only at 6 GHz. The core area is not measured "
         f"here and the processes differ, so this report makes no claim of beating the paper."),
        (f"Figure numbering. Figures 1 to 8 are the named slots. Figures {EXTRA_FIG_START} onwards are additional "
         f"figures: the ring diagram (Figure {extra_no['ring']}), the 6 GHz waveforms (Figure {extra_no['tran_b']}), "
         f"phase steps (Figure {extra_no['phase']}), tail voltage (Figure {extra_no['tail_d']}), supply current "
         f"(Figure {extra_no['supply']}), the frequency sweep (Figure {extra_no['fsweep']}) and the PVT plots for "
         f"design D and B (Figures {extra_no['pvt_dp_d']}, {extra_no['pvt_hm_b6']} and {extra_no['pvt_dp_b6']})."),
    ]

    conclusion = [
        (f"Both operating points work with the same topology and the stack rule. Design D at {f_d:g} GHz "
         f"(m = {m_d}, R = {r_d:g} kOhm) divides with {metrics_d['power_mw']} mW, {metrics_d['delay_ps']} ps delay, "
         f"{metrics_d['pdp_fj']} fJ PDP and a {metrics_d['max_phase_step_err_deg']} deg phase-step error, and passes "
         f"{sum_d['pass_count']} of {sum_d['total']} PVT points. Design B at {f_b:g} GHz (m = {m_b}, R = {r_b:g} kOhm) "
         f"divides with {num(nom_b['power_mW']):.4f} mW, {num(nom_b['delay_ps']):.2f} ps delay, "
         f"{num(nom_b['pdp_fJ']):.3f} fJ PDP and a {num(nom_b['max_phase_step_err_deg']):.2f} deg phase-step error, "
         f"and passes {sum_b6['pass_count']} of {sum_b6['total']} PVT points."),
        (f"The unsized circuit with R1 = Ron/2 does not divide at 1.4 GHz, which is consistent with the "
         f"stack-resistance rule (its load is far below the threshold)."),
        (f"Limits. The tail M7 operates in triode, not saturation, so the paper's tail model is not reproduced. The "
         f"phase-step error at 1.4 GHz ({metrics_d['max_phase_step_err_deg']} deg) is far above the paper's 3.75 deg, "
         f"and only design B at 6 GHz comes close ({num(nom_b['max_phase_step_err_deg']):.2f} deg). {d_fail_text} "
         f"Design B, whose load lies inside the regeneration band, passes fewer PVT points ({sum_b6['pass_count']} of "
         f"{sum_b6['total']} at 6 GHz and {sum_b1['pass_count']} of {sum_b1['total']} at 1.4 GHz)."),
        ("Still to be added: the Virtuoso schematic and layout screenshots, the layout simulation and the DRC result. "
         "These slots are shown in red in the figure list until they are provided."),
    ]

    problems_faced = [
        "Spectre aborted with ERROR (VACOMP-1008): Cannot compile ahdlcmi module library, and then a segmentation "
        "fault, for the gate-resistance Verilog-A style sub-model inside the gpdk045 device.",
        "Cause: the Cadence VM is 32-bit CentOS 6.5, but the bundled perl (cdsPerl) and gcc are 64-bit and could not "
        "run, and no gcc was installed.",
        "The guest disk had only about 100 MB free, so a sweep failed with No space left on device.",
        "The unit-size circuit with R1 = Ron/2 does not divide at 1, 1.4 or 2 GHz.",
        "The first division check counted false passes: outputs at 2 or 2.8 times the expected frequency with only "
        "15 to 20 mV of swing.",
        "The Spectre ASCII raw layout (first variable on the Variables line, several values per line) broke the first parser.",
        "The 125 C corners failed for the marginal sizing.",
        "The VM had no guest tools, so files were moved by virtual CD images and a virtual serial port with MD5 checks.",
        "The phase error at 1.4 GHz is large (38.46 deg for design D), far from the paper's 3.75 deg.",
    ]
    problems_resolved = [
        "Installed gcc 4.4.7 and glibc-devel from the CentOS 6.5 vault RPMs, replaced the bundled perl wrapper by the "
        "system perl, and pointed the bundled gcc and ld symlinks at /usr/bin.",
        "The measured values were stored as TSV and JSON files (nominal, sweep, PVT and analysis files), so each "
        "number in this report is read from one of those files.",
        "The unsized design was replaced by the sizing concept: the load was set from the stack-resistance rule, "
        "giving design D (41 of 45 PVT points).",
        "The division test was made strict: all eight outputs at f_in/2 within 0.1 percent, each swinging at least 0.1 V.",
        "The parsers were fixed for the Spectre ASCII raw layout, and the PVT and sweep results were checked against "
        "their summary files.",
        "Two operating points were chosen: 1.4 GHz, the paper's input frequency, and 6 GHz, the point with the "
        "smallest phase-step error. Each has its own PVT matrix.",
    ]

    other_comment = [
        "The waveform and PVT figures are plots generated from Spectre data. They are labelled as plots, and no "
        "Cadence GUI screenshot is substituted for them.",
        "The Ron value and the recorded division pairs are taken from LEDGER.md. The Ron value is not in a separate "
        "output file, so the report cites the ledger.",
        "The two circuit drawings were generated from the earlier baseline netlist (spice/divider_baseline_cal.cir), "
        "not from the gpdk045 netlist. Their device labels therefore differ from Tables 1 and 2.",
        "The paper's constants are literature values, and the title-page register and name fields are left blank by design.",
    ]

    references = [
        "Y.-F. Kuo et al., \"A Compact Multiphase Divide-by-Two CMOS Frequency Divider,\" IEEE Microw. Wireless "
        "Technol. Lett., vol. 35, no. 5, pp. 617-620, May 2025, doi: 10.1109/LMWT.2025.3528863.",
        "Cadence Design Systems, Cadence GPDK045 v6.0 documentation (45 nm generic process design kit).",
        "Cadence Design Systems, Spectre Circuit Simulator Reference, MMSIM 12.1.",
    ]

    paper_block = {k: paper[k] for k in ("title", "authors", "journal", "volume", "issue", "pages", "date", "doi")}
    data = {
        "example_only": False,
        "logo": None,
        "titles": {"system_design_project": TITLE},
        "paper": paper_block,
        "figures": figures,
        "designs": {"without_sizing": design_without, "with_sizing": design_with},
        "pvt_rows": pvt_d + pvt_b6,
        "theory": [t for t in theory],
        "tool_technology": tool_technology,
        "other_info": other_info,
        "conclusion": conclusion,
        "problems_faced": problems_faced,
        "problems_resolved": problems_resolved,
        "other_comment": other_comment,
        "references": references,
    }

    checks = {
        "ron": ron, "ron_band": (led["ron_lo"], led["ron_hi"]),
        "pairs_consistent": (ok_pairs, len(numeric)),
        "d_tail_vdsat": vds_info["vdsat_v"],
    }
    return data, checks


def run_builder(data):
    """Write report_data.json, then build docx and pdf into a temp dir and move them."""
    DATA_OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    python = str(VENV_PY) if VENV_PY.is_file() else sys.executable
    tmp = Path(tempfile.mkdtemp(prefix="gpdk045_report_"))
    try:
        proc = subprocess.run(
            [python, "-I", str(BUILDER), "--data", str(DATA_OUT), "--out", str(tmp)],
            capture_output=True, text=True, timeout=900,
        )
        if proc.returncode != 0:
            fail(f"builder failed:\n{proc.stdout}\n{proc.stderr}")
        print(proc.stdout.rstrip())
        built_docx = tmp / f"{BUILT_STEM}.docx"
        built_pdf = tmp / f"{BUILT_STEM}.pdf"
        if not (built_docx.is_file() and built_pdf.is_file()):
            fail("builder did not produce both the docx and the pdf")
        out_docx = GPDK / f"{FINAL_STEM}.docx"
        out_pdf = GPDK / f"{FINAL_STEM}.pdf"
        shutil.move(str(built_docx), str(out_docx))
        shutil.move(str(built_pdf), str(out_pdf))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    pages = subprocess.run(["pdfinfo", str(out_pdf)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", pages)
    return out_docx, out_pdf, (int(m.group(1)) if m else None)


def main():
    data, checks = build_data()
    docx, pdf, pages = run_builder(data)
    print(f"report_data.json: {DATA_OUT}")
    print(f"docx: {docx}")
    print(f"pdf:  {pdf}")
    print(f"pdf pages: {pages}")
    print(f"ron (LEDGER.md): {checks['ron']} kOhm, band {checks['ron_band']}")
    print(f"recorded (m,R) pairs consistent with the stack rule: {checks['pairs_consistent'][0]} "
          f"of {checks['pairs_consistent'][1]}")


if __name__ == "__main__":
    main()
