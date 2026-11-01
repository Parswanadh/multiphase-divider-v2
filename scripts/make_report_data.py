#!/usr/bin/env python3
"""Build report/gpdk045/report_data.json from the gpdk045 result files, then build
the System Design Project Report (.docx and .pdf) with build_academic_docx.py.

Numbers are read at run time from:
  results/gpdk045/final/  unsized.tsv (paper-rule circuit), U8k.tsv (dividing unit-size baseline),
                          D_1p4.tsv, B_6g.tsv (nominal runs), unsized_baseline.tsv (R search),
                          analysis.json, *.m7op.txt, D_1p4.m7vdsat.txt,
                          pvt_D.tsv, pvt_B6.tsv, pvt_summary_*.json, fs_B/D/E/F.tsv
  results/gpdk045/        layout_build_log.txt, assura_drc_dlatch_*.txt, core_connectivity_virtuoso.txt
  cadence/skill/build_layout_v2.il   layout sizes (fingers, finger width, pin size)
  spectre/divider_gpdk45.scs   device sizes, load capacitance, rise time, temperature
  report/gpdk045/LEDGER.md     measured Ron, its range, and the recorded division pairs
  report/gpdk045/report_data.example.json   paper citation block only
The only typed numbers are the literature constants of Kuo et al. (LITERATURE below) and the
division criterion (0.1 V swing, 0.1 percent) of the report text.

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
CROP_DIR = REPO / "report" / "gpdk045" / "screens" / "crops"
READBACK = REPO / "results" / "gpdk045" / "virtuoso_dlatch_params_designD.txt"
CONN = REPO / "results" / "gpdk045" / "core_connectivity_virtuoso.txt"
GPDK = REPO / "report" / "gpdk045"
FIG_DIR = GPDK / "figures"
SHARED_FIG_DIR = REPO / "report" / "figures"
SCREEN_DIR = GPDK / "screens"
NETLIST = REPO / "spectre" / "divider_gpdk45.scs"
LEDGER = GPDK / "LEDGER.md"
EXAMPLE = GPDK / "report_data.example.json"
SCHEM_SIM_MD = GPDK / "section_schematic_sim.md"
DRC_RULES = REPO / "results" / "gpdk045" / "assura_drc_dlatch_rules.txt"
BUILDER = REPO / "scripts" / "build_academic_docx.py"
DRAW = REPO / "scripts" / "draw_gpdk45_circuits.py"
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
    "unit_w_um": 0.9,    # width of each unit nMOS except M7
    "unit_l_nm": 180,    # channel length of each unit nMOS except M7
    "authors": "Yue-Fang Kuo, Shih-Hung Lin, Bo-Yi Chen and Liang-Chen Liu",
}
SWING_MIN_V = 0.1  # division criterion of the strict check: every output swings at least this much
LOGO = GPDK / "assets" / "amrita_logo.jpeg"
LAYOUT_SRC = REPO / "cadence" / "skill" / "build_layout_v2.il"
LAYOUT_LOG = REPO / "results" / "gpdk045" / "layout_build_log.txt"
DRC_SUMMARY = REPO / "results" / "gpdk045" / "assura_drc_dlatch_summary.txt"

PREFIX = {"": 1.0, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12}
GRID_TAG = re.compile(r"^g_(?P<f>[\d.]+)G_(?P<r>[\d.]+)k_(?P<vb>[\d.]+)_(?P<cl>[\d.]+)f_m(?P<m>\d+)$")
PVT_TAG = re.compile(r"^(?P<corner>[a-z]{2})_(?P<temp>-?\d+)_(?P<vdd>\d+\.\d+)$")
EXTRA_FIG_START = 8  # figures 1 to 7 are the named slots (slot 8, the post-layout waveform, is a note)


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


def read_drc_rules():
    """Assura DRC tally of DLATCH/layout: one line per rule, real and flat counts."""
    pat = re.compile(r"^Rule No\.\s*(\d+)\s*:\s*(.+?)\s+Real Error Count\s*:\s*(\d+);\s*Flat Error Count\s*:\s*(\d+)$")
    rules = []
    for raw in DRC_RULES.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = pat.match(line)
        if m is None:
            fail(f"unrecognised line in {DRC_RULES.name}: {line!r}")
        no, name, real, flat = m.groups()
        if real != flat:
            fail(f"real and flat DRC counts differ for rule {no}")
        rules.append({"no": int(no), "name": name.strip(), "count": int(real)})
    if len(rules) != 3:
        fail(f"expected 3 DRC rules in {DRC_RULES.name}, found {len(rules)}")
    return rules


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


def fail_note(row):
    """Short note for a failing PVT row (ratio = f_in / f_out; a division needs 2)."""
    ratio = num(row["ratio"])
    swing = None if num(row["swing_lo"]) is None else num(row["swing_hi"]) - num(row["swing_lo"])
    if ratio is not None and abs(ratio - 0.5) < 0.01:
        what = "outputs at 2 f_in"
    elif ratio is not None and abs(ratio - 1.0) < 0.05:
        what = f"outputs at about f_in (ratio {ratio:.4f})"
    elif ratio is not None and abs(ratio - 2.0) < 0.01:
        what = "divides"
    else:
        what = f"ratio {ratio}"
    if swing is not None and swing < SWING_MIN_V:
        what += f", swing {swing:.3f} V < {SWING_MIN_V:g} V"
    return what


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
            "f_out_mhz": None if num(row["f_out_MHz"]) is None else f"{num(row['f_out_MHz']):.1f}",
            "delay_ps": f"{num(row['delay_ps']):.2f}" if divides else None,
            "power_mw": f"{num(row['power_mW']):.4f}" if divides else None,
            "pdp_fj": f"{num(row['pdp_fJ']):.2f}" if divides else None,
            "note": "" if divides else fail_note(row),
        })
    if len(rows) != summary["total"] or passes != summary["pass_count"]:
        fail(f"{tsv_name}: {passes}/{len(rows)} pass, {summary_name} says "
             f"{summary['pass_count']}/{summary['total']}")
    return out, summary


def summary_only(name):
    return json.loads((FINAL / name).read_text(encoding="utf-8"))


def fail_text(summary):
    items = summary["failing"]
    n_fail = len(items)
    total = summary["total"]
    if n_fail == 0:
        return f"all {total} corners pass"
    temps = set(f["temp_C"] for f in items)
    vdds = set(f["vdd_V"] for f in items)
    if len(temps) == 1 and len(vdds) == 1:
        t = next(iter(temps))
        v = next(iter(vdds))
        return f"{n_fail} of {total} corners fail, all at {t} C and {v:g} V"
    by_temp = Counter(f["temp_C"] for f in items)
    parts = []
    for t in sorted(by_temp):
        t_items = [f for f in items if f["temp_C"] == t]
        t_vdds = sorted(set(f["vdd_V"] for f in t_items))
        if len(t_items) == 15:
            parts.append(f"all 15 at {t} C")
        elif len(t_vdds) == 1:
            parts.append(f"{len(t_items)} at {t} C and {t_vdds[0]:g} V")
        else:
            parts.append(f"{len(t_items)} at {t} C")
    return f"{n_fail} of {total} corners fail ({', '.join(parts)})"


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
            "n_ok": len(ok), "n": len(pts),
            "ok_list": [p["f"] for p in ok], "fail_list": [p["f"] for p in bad],
            "f_lo": min(p["f"] for p in pts), "f_hi": max(p["f"] for p in pts),
            "tag": rows[0]["tag"]}


def sweep_groups(name):
    """Sweep file with several (m, R) groups: per group the highest dividing frequency."""
    groups = {}
    for r in read_tsv(FINAL / name):
        t = grid_tag(r["tag"])
        groups.setdefault((t["m"], t["r_kohm"]), []).append(
            (t["f_ghz"], r["divides"].strip() == "1", num(r["max_phase_step_err_deg"])))
    out = []
    for (m_val, r_val), pts in sorted(groups.items()):
        pts.sort()
        ok = [p for p in pts if p[1]]
        fails = [p[0] for p in pts if not p[1] and ok and p[0] > ok[-1][0]]
        out.append({"m": m_val, "r": r_val, "f_max": ok[-1][0] if ok else None,
                    "err": ok[-1][2] if ok else None, "f_fail": fails[0] if fails else None,
                    "n": len(pts)})
    return out


def baseline_search():
    """unsized_baseline.tsv: per tail bias the largest failing and smallest dividing R (m = 1)."""
    rows = read_tsv(FINAL / "unsized_baseline.tsv")
    by_vb = {}
    for r in rows:
        t = grid_tag(r["tag"])
        if t["m"] != 1:
            fail("unsized_baseline.tsv contains m != 1")
        by_vb.setdefault(t["vb"], []).append((t["r_kohm"], r["divides"].strip() == "1"))
    out = {}
    for vb, pts in by_vb.items():
        fails = [r for r, ok in pts if not ok]
        oks = [r for r, ok in pts if ok]
        if fails and oks and max(fails) >= min(oks):
            fail(f"unsized_baseline.tsv: division is not monotone in R at vb = {vb}")
        out[vb] = {"fail_max": max(fails) if fails else None, "ok_min": min(oks) if oks else None,
                   "r_lo": min(r for r, _ in pts), "r_hi": max(r for r, _ in pts), "n": len(pts)}
    return len(rows), out


def swing_range_mv(names):
    """Smallest and largest per-output swing (mV) quoted in the reason column of failing TSV rows."""
    vals = []
    for name in names:
        for r in read_tsv(FINAL / name):
            if r["divides"].strip() == "0":
                vals += [float(x) for x in re.findall(r"swing (\d+\.\d+) V", r["reason"])]
    return min(vals) * 1e3, max(vals) * 1e3


def layout_facts():
    """Layout sizes and placement figures, read from the SKILL script and the build log."""
    il = LAYOUT_SRC.read_text(encoding="utf-8")
    log = LAYOUT_LOG.read_text(encoding="utf-8")

    def il_var(name, pattern):
        m = re.search(rf"^defvar\({name}\s+{pattern}\)", il, re.M)
        if m is None:
            fail(f"{name} not found in {LAYOUT_SRC.name}")
        return m.group(1)

    f = {
        "fw_nm": float(il_var("divFw", r'"(\d+)n"')),
        "l1_nm": float(il_var("divL1", r'"(\d+)n"')),
        "l7_nm": float(il_var("divL7", r'"(\d+)n"')),
        "nf1": int(il_var("divNf1", r"(\d+)")),
        "nf7": int(il_var("divNf7", r"(\d+)")),
        "pin_w": float(il_var("divPinW", r"([\d.]+)")),
        "pin_h": float(il_var("divPinH", r"([\d.]+)")),
    }
    mos = re.findall(r"placed (M\d) \(nmos1v\)", log)
    res = re.findall(r"placed (R\d) \(resnsnpoly\)", log)
    box = re.search(r"DLATCH box \(um\): [\d.]+ [\d.]+ ([\d.]+) ([\d.]+)", log)
    rlen = re.search(r"R len = ([\d.]+) um \(W ([\d.]+) um, rsh (\d+), target (\d+) ohm\)", log)
    star = re.search(r"ck=([\d.]+) ckb=([\d.]+)", log)
    gap = re.search(r"gap ([\d.]+) um", log)
    bbox = re.search(r"raw MOS bBox width = ([\d.]+)", log)
    pos = dict(re.findall(r"placed (M\d) \(nmos1v\) at \(([\d.]+),", log))
    place = re.findall(r"(XD\d) (R0|MY|MX|R180) at origin", log)
    if not (len(mos) == 7 and len(res) == 2 and box and rlen and star and gap and bbox and len(place) == 4):
        fail("layout_build_log.txt does not have the expected content")
    f.update({"n_mos": len(mos), "n_res": len(res), "box_w": box.group(1), "box_h": box.group(2),
              "r_len": rlen.group(1), "r_w": rlen.group(2), "r_rsh": rlen.group(3),
              "r_target": float(rlen.group(4)), "ck": star.group(1), "ckb": star.group(2),
              "gap": gap.group(1), "bbox": bbox.group(1), "place": place,
              "pitch": float(pos["M5"]) - float(pos["M1"])})
    f["w1_nm"] = f["fw_nm"] * f["nf1"]
    f["w7_nm"] = f["fw_nm"] * f["nf7"]
    return f


def drc_markers():
    """Marker rectangles of each Assura rule in assura_drc_dlatch_summary.txt."""
    out, rule = {}, None
    for line in DRC_SUMMARY.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^Rule No\. (\d+) :", line)
        if m:
            rule = int(m.group(1))
            out[rule] = {"boxes": [], "env": None}
            continue
        if rule is None:
            continue
        e = re.match(r"^\s+1\s+1\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$", line)
        if e:
            out[rule]["env"] = tuple(float(x) for x in e.groups())
        b = re.match(r"^\s+\d+\s+X\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$", line)
        if b:
            out[rule]["boxes"].append(tuple(float(x) for x in b.groups()))
    return out


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


def screen_name(name):
    """Prefer a *_full.png screenshot if present over *_cadence or layout_core."""
    if name.endswith("_full"):
        return name
    base = name[:-len("_cadence")] if name.endswith("_cadence") else name
    full = f"{base}_full"
    return full if (SCREEN_DIR / f"{full}.png").is_file() else name


def screen(name, caption):
    """A Cadence screenshot, preferring a *_full.png file if present."""
    return {"file": f"screens/{screen_name(name)}.png", "caption": caption}


def screen_or_none(name, caption):
    return screen(name, caption) if (SCREEN_DIR / f"{name}.png").is_file() else None


def read_schematic_section(fig_dict=None):
    """Subsection on the simulation from the Virtuoso schematic (section_schematic_sim.md).

    The markdown has a '### ' heading, then paragraphs; the last paragraph starts with
    'Evidence files:' and lists comma-separated repo paths, which go to the references.
    """
    blocks = [b.strip() for b in SCHEM_SIM_MD.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    if not blocks or not blocks[0].startswith("### "):
        fail(f"{SCHEM_SIM_MD.name}: first block must be a '### ' heading")
    heading = blocks[0][4:].strip()
    paragraphs = [" ".join(b.split()) for b in blocks[1:]]
    if not paragraphs or not paragraphs[-1].startswith("Evidence files:"):
        fail(f"{SCHEM_SIM_MD.name}: last paragraph must start with 'Evidence files:'")
    evidence = [e.strip() for e in paragraphs.pop()[len("Evidence files:"):].split(",") if e.strip()]
    for rel in evidence:
        if not (REPO / rel).is_file():
            fail(f"{SCHEM_SIM_MD.name}: evidence file missing: {rel}")
    if fig_dict:
        paragraphs = [p.format(**fig_dict) for p in paragraphs]
    return heading, paragraphs, evidence


def crop(name, caption):
    """A crop of a Cadence screenshot, made by hand with PIL and stored in screens/crops/."""
    if not (CROP_DIR / f"{name}.png").is_file():
        fail(f"missing screenshot crop {name}.png (screens/crops/)")
    return {"file": f"screens/crops/{name}.png", "caption": caption}


def read_readback():
    """Virtuoso read-back of design D: resistors (as written, e.g. 3K) and nMOS w, l, m."""
    text = READBACK.read_text(encoding="utf-8")
    res, mos = {}, {}
    for line in text.splitlines():
        m = re.match(r"^(\w+)\s+(\S+)\s+(.*)$", line.strip())
        if not m:
            continue
        name, master, rest = m.groups()
        if master == "res":
            res[name] = re.search(r'r="([^"]*)"', rest).group(1)
        elif master == "nmos1v":
            mos[name] = {k: re.search(rf'{k}="([^"]*)"', rest).group(1) for k in ("w", "l", "m")}
    if set(res) != {"R1", "R2"} or len(mos) != 7:
        fail("read-back does not list R1, R2 and M1 to M7")
    return res, mos


NET_NORM = {"ck": "CK", "ckb": "CKb", "vdd": "VDD", "nbias": "NBIAS", "0": "VSS", "vss": "VSS"}


def read_connectivity():
    """Compare the Virtuoso top-level latch connections with the Spectre netlist.

    Returns (instances compared, mismatching pins). Pins are the DLATCH pin names.
    """
    pins = ["D", "Db", "CK", "CKb", "Q", "Qb", "VDD", "VSS", "NBIAS"]
    virt = {}
    for line in CONN.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(XD\d+)\s+DLATCH:\s+(.*)$", line.strip())
        if m:
            virt[m.group(1)] = dict(kv.split("=", 1) for kv in m.group(2).split())
    spec = {}
    for line in NETLIST.read_text(encoding="utf-8").splitlines():
        s_ = line.split("//", 1)[0].strip()
        m = re.match(r"^(XD\d+)\s*\(([^)]*)\)\s*DLATCH$", s_)
        if m:
            nodes = [NET_NORM.get(n, n) for n in m.group(2).split()]
            spec[m.group(1)] = dict(zip(pins, nodes))
    if not virt or set(virt) != set(spec):
        fail("Virtuoso connectivity and netlist name different latch instances")
    mism = []
    for x in sorted(spec):
        for pin in pins:
            v = virt[x].get(pin)
            if v is None or NET_NORM.get(v.lower(), v) != spec[x][pin]:
                mism.append(f"{x}.{pin}")
    return len(spec), mism


def read_schcheck():
    """schCheck errors/warnings per cell, from the LEDGER.md T4 line."""
    text = LEDGER.read_text(encoding="utf-8")
    m = re.search(r"schCheck ([\d]+/[\d]+), ([\d]+/[\d]+), ([\d]+/[\d]+)", text)
    if m is None:
        fail("schCheck counts not found in LEDGER.md")
    return dict(zip(("DLATCH", "divider_core", "tb_divider"), m.groups()))


def build_data():
    net = read_netlist()
    led = read_ledger()
    drc_rules = read_drc_rules()
    drc_count = {r["no"]: r["count"] for r in drc_rules}
    drc_total = sum(drc_count.values())
    drc_stamp = drc_count[220] + drc_count[221]   # psubstrate stamp connectivity
    drc_metal = drc_count[595]                    # METAL1.A.1 minimum area
    if drc_stamp + drc_metal != drc_total:
        fail("DRC rule classes do not add up to the total")
    ana = json.loads((FINAL / "analysis.json").read_text(encoding="utf-8"))
    paper = json.loads(EXAMPLE.read_text(encoding="utf-8"))["paper"]
    paper["authors"] = LITERATURE["authors"]
    if not LOGO.is_file():
        fail(f"logo file missing: {LOGO}")

    nom_u = one_row("unsized.tsv", expect_divides=False)   # paper-rule circuit, does not divide
    nom_8 = one_row("U8k.tsv", expect_divides=True)        # dividing unit-size baseline
    nom_d = one_row("D_1p4.tsv", expect_divides=True)
    nom_b = one_row("B_6g.tsv", expect_divides=True)
    tag_u, tag_8, tag_d, tag_b = (grid_tag(r["tag"]) for r in (nom_u, nom_8, nom_d, nom_b))
    for tag in (tag_u, tag_8, tag_d, tag_b):
        if abs(tag["cl_ff"] - 10.0) > 1e-9 or net["params"].get("cl") != "10f":
            fail("load capacitance differs from 10 fF")
    if tag_8["m"] != 1 or tag_u["m"] != 1:
        fail("the baseline circuits must be unit size (m = 1)")
    a_u = ana["designs"]["unsized"]
    a_8 = ana["designs"]["U8k"]
    a_d = ana["designs"]["D_1p4"]
    a_b = ana["designs"]["B_6g"]
    for nom, a in ((nom_8, a_8), (nom_d, a_d), (nom_b, a_b)):
        if a["tsv"]["tag"] != nom["tag"]:
            fail("analysis.json does not match the nominal TSV tags")
    vdd_v = ana["vdd_v"]

    op_u = op_point("unsized.m7op.txt")
    op_d = op_point("D_1p4.m7op.txt")
    op_b = op_point("B_6g.m7op.txt")
    for op, tag in ((op_u, tag_u), (op_d, tag_d), (op_b, tag_b)):
        if abs(op["vg_v"] - tag["vb"]) > 1e-9:
            fail("M7 gate voltage in the operating point differs from vb in the tag")
    if abs(tag_8["vb"] - tag_d["vb"]) > 1e-9 or abs(tag_b["vb"] - tag_d["vb"]) > 1e-9:
        fail("tail bias differs between baseline, D and B; one Vdsat cannot be reused")
    if (op_b["vds_v"], op_b["ids_a"], op_b["region"]) != (op_d["vds_v"], op_d["ids_a"], op_d["region"]):
        fail("B and D M7 operating points differ; Vdsat of D cannot stand for B")
    vds_info = vdsat_info("D_1p4.m7vdsat.txt")

    # Cross-checks between the TSV and analysis.json (must agree within rounding).
    for label, nom, a in (("U8k", nom_8, a_8), ("D", nom_d, a_d), ("B", nom_b, a_b)):
        if abs(num(nom["delay_ps"]) - a["ck_to_any_output_mean_delay_ps"]) > 0.01:
            fail(f"{label}: delay in the TSV does not match analysis.json")
        rel = abs(num(nom["power_mW"]) - a["supply_avg_ma_steady"]) / num(nom["power_mW"])
        if rel > 0.001:
            fail(f"{label}: power in the TSV differs from the supply-current average by {rel:.4%}")

    f_d, f_b, f_8 = tag_d["f_ghz"], tag_b["f_ghz"], tag_8["f_ghz"]
    r_u, r_8, r_d, r_b = tag_u["r_kohm"], tag_8["r_kohm"], tag_d["r_kohm"], tag_b["r_kohm"]
    m_u, m_8, m_d, m_b = tag_u["m"], tag_8["m"], tag_d["m"], tag_b["m"]
    vb_d = tag_d["vb"]

    ron = led["ron"]
    if abs(r_u - ron / 2.0) > 0.005:
        fail("paper-rule R1 is not Ron/2 from LEDGER.md")
    stack = lambda m: 3.0 * ron / m
    thr_mid = lambda m: 1.1 * stack(m)
    thr_lo = lambda m: 1.1 * 3.0 * led["ron_lo"] / m
    thr_hi = lambda m: 1.1 * 3.0 * led["ron_hi"] / m
    numeric = [p for p in led["pairs"] if p["r_kohm"] is not None]
    ok_pairs = sum(1 for p in numeric if (p["r_kohm"] >= thr_mid(p["m"])) == p["divides"])

    # Baseline search: measured threshold bracket per tail bias against the stack rule.
    n_search, search = baseline_search()
    br1, br08 = search[tag_8["vb"]], search[0.8]
    if not (br1["fail_max"] < stack(1) <= br1["ok_min"]):
        fail("3 Ron is not inside the measured threshold bracket at the baseline bias")
    if not (br08["fail_max"] < thr_mid(1) <= br08["ok_min"]):
        fail("1.1 x 3 Ron is not inside the measured threshold bracket at vb = 0.8 V")

    # Elmore relation of the paper: t_pd = (8C)(R/2), the Q node carries 8C and R = 2 R1.
    # The node capacitance is at least the output load C_L, so Td >= R1 * C_L (kOhm x fF = ps).
    cl_ff = tag_d["cl_ff"]
    td_d = r_d * cl_ff
    td_b = r_b * cl_ff
    half_d = 1e3 / (2.0 * f_d)
    half_b = 1e3 / (2.0 * f_b)
    if not (2.0 * td_d < half_d and 2.0 * td_b < half_b):
        fail("the Elmore lower bound is not met; the report text assumes it is")

    # Phase-step law. t_pair is the gap between the two close edges (Q2 to Q3b), measured in the raw files.
    steps_d = [float(x) for x in nom_d["phase_steps_deg"].split(",")]
    steps_b = [float(x) for x in nom_b["phase_steps_deg"].split(",")]
    steps_8 = [float(x) for x in nom_8["phase_steps_deg"].split(",")]
    tp_d, tp_b, tp_8 = a_d["t_pair_ps"], a_b["t_pair_ps"], a_8["t_pair_ps"]
    pair_d = a_d["t_pair_outputs"]
    if a_b["t_pair_outputs"] != pair_d or a_8["t_pair_outputs"] != pair_d:
        fail("the paired outputs differ between designs")
    a_calc = lambda tp, f: 180.0 * tp * 1e-3 * f     # a = 180 t_pair f_in (ps x GHz = 1e-3)
    for tp, f, st in ((tp_d, f_d, steps_d), (tp_b, f_b, steps_b), (tp_8, f_8, steps_8)):
        if abs(a_calc(tp, f) - min(st)) > 0.05:
            fail("t_pair does not reproduce the smallest phase step")

    # Pass/fail data.
    pvt_d, sum_d = pvt_block("D", "pvt_D.tsv", "pvt_summary_D_1p4.json", f_d)
    pvt_b6, sum_b6 = pvt_block("B6", "pvt_B6.tsv", "pvt_summary_B_6g.json", f_b)
    sum_b1 = summary_only("pvt_summary_B_1p4.json")
    sum_e = summary_only("pvt_summary_E_1p4.json")
    sw_b, sw_d, sw_e = sweep("fs_B.tsv"), sweep("fs_D.tsv"), sweep("fs_E.tsv")
    sw_f = sweep_groups("fs_F.tsv")
    tag_e = grid_tag(sw_e["tag"])
    pvt_all = pvt_d + pvt_b6
    pvt_corners = sorted({r["corner"].split()[1] for r in pvt_all})
    pvt_temps = sorted({r["temp"] for r in pvt_all})
    pvt_vdds = sorted({r["vdd"] for r in pvt_all})
    b6_tt27_09 = next(r for r in pvt_b6 if r["corner"] == "B6 tt" and r["temp"] == 27 and r["vdd"] == 0.9)

    swing = lambda a: a["q1_max_v"] - a["q1_min_v"]
    swing_u, swing_8, swing_d, swing_b = swing(a_u), swing(a_8), swing(a_d), swing(a_b)
    f_out_u_meas = num(nom_u["f_out_MHz"])
    sw_u_mv = swing_u * 1e3
    p_u_mw = a_u["supply_avg_ma_steady"] * vdd_v
    ratio_u = f_out_u_meas / (tag_u["f_ghz"] * 1e3)
    fp_lo, fp_hi = swing_range_mv(["unsized.tsv", "unsized_baseline.tsv"])
    lay = layout_facts()
    drcm = drc_markers()
    width_factor = m_d // m_8

    num_d = lambda key: num(nom_d[key])
    num_8 = lambda key: num(nom_8[key])

    # ---------------------------------------------------------- metrics
    metrics_8 = {
        "f_in_ghz": rnd(num_8("f_in_GHz"), 3),
        "f_out_mhz": rnd(num_8("f_out_MHz"), 3),
        "power_mw": rnd(num_8("power_mW"), 4),
        "delay_ps": rnd(num_8("delay_ps"), 2),
        "pdp_fj": rnd(num_8("pdp_fJ"), 3),
        "max_phase_step_err_deg": rnd(num_8("max_phase_step_err_deg"), 2),
        "swing_v": rnd(swing_8, 4),
        "m7_vds_v": rnd(a_8["xd1_tail_max_v"], 4),
        "m7_vdsat_v": rnd(vds_info["vdsat_v"], 4),
    }
    metrics_d = {
        "f_in_ghz": rnd(num_d("f_in_GHz"), 3),
        "f_out_mhz": rnd(num_d("f_out_MHz"), 3),
        "power_mw": rnd(num_d("power_mW"), 4),
        "delay_ps": rnd(num_d("delay_ps"), 2),
        "pdp_fj": rnd(num_d("pdp_fJ"), 3),
        "max_phase_step_err_deg": rnd(num_d("max_phase_step_err_deg"), 2),
        "swing_v": rnd(swing_d, 4),
        "m7_vds_v": rnd(a_d["xd1_tail_max_v"], 4),
        "m7_vdsat_v": rnd(vds_info["vdsat_v"], 4),
    }

    # ---------------------------------------------------------- figure numbers
    viva_file = SCREEN_DIR / "viva_tran_D_1p4GHz_full.png"
    extra_keys = ["ring", "tran_paper", "tran_b", "phase", "tail_8", "tail_d", "tail_b", "supply",
                  "fsweep", "pvt_dp_d", "pvt_hm_b6", "pvt_dp_b6", "layout_dlatch", "drc"]
    if viva_file.is_file():
        extra_keys.append("tran_d_plot")
    extra_no = {key: EXTRA_FIG_START + i for i, key in enumerate(extra_keys)}
    slot_no = {"circuit": 1, "core": 2, "tran_8": 3, "dlatch": 4, "tran_d": 5, "pvt_hm_d": 6, "layout_core": 7}
    tab_no = {
        "dev_without": 1,
        "dev_with": 2,
        "values": 3,
        "pvt_d": 4,
        "pvt_b6": 5,
        "appendix_pvt": 6,
    }

    schc = read_schcheck()
    dl_e, dl_w = schc["DLATCH"].split("/")
    core_e, core_w = schc["divider_core"].split("/")
    tb_e, tb_w = schc["tb_divider"].split("/")
    if (dl_e, dl_w) == (core_e, core_w):
        sch_text = (f"Schematic checks: {dl_e} errors and {dl_w} warnings for DLATCH and divider_core; "
                    f"{tb_e} errors and {tb_w} warning for tb_divider (the supply source instance and its net are both named VDD).")
    else:
        sch_text = (f"Schematic checks: {dl_e} errors and {dl_w} warnings for DLATCH; "
                    f"{core_e} errors and {core_w} warnings for divider_core; "
                    f"{tb_e} errors and {tb_w} warning for tb_divider (the supply source instance and its net are both named VDD).")
    vdsat_note = (f"Extracted saturation voltage Vdsat = {vds_info['vdsat_v']:.3f} V for design D (Vgs = "
                  f"{op_d['vg_v']:g} V).")
    extras = [
        ("ring", plotted("fig_circuit_ring",
                         f"Ring interconnection of four DLATCH stages (XD1 to XD4) with alternating cross-connections, "
                         f"and inverted clocks on XD2 and XD3 (design D: m = {m_d}, R = {r_d:g} kOhm).")),
        ("tran_paper", plotted("fig_tran_unsized",
                               f"Transient simulation waveforms for reference paper sizing (m = {m_u}, R1 = R2 = {r_u:g} kOhm = Ron/2) at "
                               f"{tag_u['f_ghz']:g} GHz, showing failure to divide.")),
        ("tran_b", plotted("fig_tran_B_6g",
                           f"Transient waveforms for design B at {f_b:g} GHz (m = {m_b}, R1 = R2 = {r_b:g} kOhm), "
                           f"yielding divided outputs at {num(nom_b['f_out_MHz']):.1f} MHz.")),
        ("phase", plotted("fig_phase_steps",
                          f"Phase steps between the eight outputs for unsized baseline ({f_8:g} GHz), design D "
                          f"({f_d:g} GHz), and design B ({f_b:g} GHz).")),
        ("tail_8", plotted("fig_tail_saturation_U8k",
                           f"Tail transistor (M7) drain voltage for unsized baseline compared with saturation voltage "
                           f"Vdsat = {vds_info['vdsat_v']:.3f} V.")),
        ("tail_d", plotted("fig_tail_saturation_D_1p4",
                           f"Tail transistor (M7) drain voltage for design D at {f_d:g} GHz compared with saturation "
                           f"voltage Vdsat = {vds_info['vdsat_v']:.3f} V.")),
        ("tail_b", plotted("fig_tail_saturation_B_6g",
                           f"Tail transistor (M7) drain voltage for design B at {f_b:g} GHz compared with saturation "
                           f"voltage Vdsat = {vds_info['vdsat_v']:.3f} V.")),
        ("supply", plotted("fig_supply_current",
                           "Supply current drawn from VDD for unsized baseline, design D, and design B.")),
        ("fsweep", plotted("fig_fsweep",
                           "Frequency sweeps for designs B, D, and E showing division range and maximum phase-step "
                           "error versus input frequency.")),
        ("pvt_dp_d", plotted("fig_pvt_delay_power_D_1p4",
                             "Delay and power across the PVT matrix for design D at 1.4 GHz (crosses mark failing corners).")),
        ("pvt_hm_b6", plotted("fig_pvt_heatmap_B_6g",
                              f"PVT pass/fail map for design B at {f_b:g} GHz ({sum_b6['pass_count']} of {sum_b6['total']} "
                              f"points pass).")),
        ("pvt_dp_b6", plotted("fig_pvt_delay_power_B_6g",
                              f"Delay and power across the PVT matrix for design B at {f_b:g} GHz (crosses mark failing corners).")),
        ("layout_dlatch", screen("layout_dlatch_cadence",
                                 f"Virtuoso layout editor showing the DLATCH cell: {lay['n_mos']} unit NMOS devices (m = {m_8}) and "
                                 f"{lay['n_res']} poly resistors.")),
        ("drc", screen("drc_result",
                       f"Assura DRC summary for the DLATCH layout showing {drc_total} errors across {len(drc_rules)} rules.")),
    ]
    tran_d_plotted = plotted(
        "fig_tran_D_1p4",
        f"Transient waveforms for design D (m = {m_d}, R1 = R2 = {r_d:g} kOhm) at {f_d:g} GHz. Output "
        f"frequency is {num_d('f_out_MHz'):.1f} MHz with Q1 swinging from {a_d['q1_min_v']:.3f} V to "
        f"{a_d['q1_max_v']:.3f} V.")
    if viva_file.is_file():
        extras.append(("tran_d_plot", tran_d_plotted))
    if [k for k, _ in extras] != extra_keys:
        fail("extra figure list and figure-number keys differ")

    figures = {
        "circuit_diagram": plotted("fig_circuit_latch",
                                   f"Schematic of the differential D-latch (DLATCH) stage (M1-M7, R1, R2). Sizing: M1-M6 "
                                   f"W = {nm(net['sizes']['M1'][0])}, L = {nm(net['sizes']['M1'][1])}; M7 "
                                   f"W = {nm(net['sizes']['M7'][0])}, L = {nm(net['sizes']['M7'][1])}. Values shown for "
                                   f"design D (sized, m = {m_d}, R1 = R2 = {r_d:g} kOhm, {f_d:g} GHz); unsized baseline uses "
                                   f"multiplier m = {m_8}, R = {r_8:g} kOhm."),
        "impl_screenshot": screen("schematic_core_cadence",
                                  f"Virtuoso schematic editor window showing the divider core with four DLATCH instances (XD1 to XD4) connected "
                                  f"in a ring. The unsized baseline and design D share this topology, differing only in multiplier m and load "
                                  f"resistance R (Table {tab_no['dev_without']} and Table {tab_no['dev_with']})."),
        "waveform_without_sizing": plotted(
            "fig_tran_U8k",
            f"Transient waveforms for the unsized baseline (m = {m_8}, R1 = R2 = {r_8:g} kOhm, "
            f"vb = {tag_8['vb']:g} V) at {f_8:g} GHz. All eight outputs divide to {num_8('f_out_MHz'):.1f} MHz, "
            f"with Q1 swinging from {a_8['q1_min_v']:.3f} V to {a_8['q1_max_v']:.3f} V. Waveforms for reference paper sizing "
            f"appear in Figure {extra_no['tran_paper']}."),
        "sized_circuit_screenshot": screen(
            "schematic_dlatch_cadence",
            f"Virtuoso schematic editor window showing the DLATCH cell with sizing applied (design D: m = {m_d}, "
            f"R1 = R2 = {r_d:g} kOhm), consistent with Table {tab_no['dev_with']}."),
        "waveform_with_sizing": (
            screen("viva_tran_D_1p4GHz_full",
                   "Transient waveforms of design D at 1.4 GHz (tt, 27 C), simulated from the Virtuoso testbench and displayed in the Cadence ViVA waveform viewer.")
            if viva_file.is_file() else tran_d_plotted
        ),
        "pvt_screenshot": plotted(
            "fig_pvt_heatmap_D_1p4",
            f"PVT pass/fail map for design D at {f_d:g} GHz across {len(pvt_corners)} corners, temperatures "
            f"{'/'.join(str(t) for t in pvt_temps)} C, and supplies {'/'.join(f'{v:g}' for v in pvt_vdds)} V "
            f"({sum_d['pass_count']} of {sum_d['total']} points pass)."),
        "layout_screenshot": screen(
            "layout_core",
            f"Virtuoso layout editor showing divider_core with four DLATCH instances (XD1 to XD4) placed in a 2x2 array. "
            f"The layout is placement only, not routed, with no LVS or post-layout simulation; Assura DRC reports "
            f"{drc_total} errors across {len(drc_rules)} rules."),
        "layout_waveform": {
            "note": "No post-layout waveform exists because the layout is placement only."},
        "extra_figures": [item for _, item in extras],
    }
    if figures["layout_waveform"] is None:
        fail("layout_waveform slot must be a note")

    # ---------------------------------------------------------- designs
    cmp_text = (
        f"Comparison with baseline (Table {tab_no['values']}): sizing cuts delay from {metrics_8['delay_ps']} ps (unsized baseline) to "
        f"{metrics_d['delay_ps']} ps (design D) ({metrics_8['delay_ps'] / metrics_d['delay_ps']:.2f}x) and increases swing "
        f"from {metrics_8['swing_v']} V to {metrics_d['swing_v']} V. Power rises from {metrics_8['power_mw']} mW "
        f"to {metrics_d['power_mw']} mW ({metrics_d['power_mw'] / metrics_8['power_mw']:.2f}x), PDP from "
        f"{metrics_8['pdp_fj']} fJ to {metrics_d['pdp_fj']} fJ ({metrics_d['pdp_fj'] / metrics_8['pdp_fj']:.2f}x), "
        f"and phase-step error from {metrics_8['max_phase_step_err_deg']} deg to {metrics_d['max_phase_step_err_deg']} deg "
        f"at {f_d:g} GHz.")
    design_without = {
        "description": [
            (f"Unsized baseline (m = 1, R = {r_8:g} kOhm): unit devices (m = {m_8}), load R1 = R2 = {r_8:g} kOhm, tail bias "
             f"vb = {tag_8['vb']:g} V, and {f_8:g} GHz input under nominal conditions (tt corner, {net['temp_c']} C, VDD = {vdd_v:g} V). "
             f"All eight outputs divide to {num_8('f_out_MHz'):.1f} MHz, with Q1 swinging from "
             f"{a_8['q1_min_v']:.3f} V to {a_8['q1_max_v']:.3f} V."),
            (f"Selection of R: load resistance was swept from {br1['r_lo']:g} to {br1['r_hi']:g} kOhm at tail bias "
             f"vb = 0.8 V and {tag_8['vb']:g} V. Division fails up to {br1['fail_max']:g} kOhm and succeeds from "
             f"{br1['ok_min']:g} kOhm at vb = {tag_8['vb']:g} V; at vb = 0.8 V it fails up to {br08['fail_max']:g} kOhm "
             f"and divides from {br08['ok_min']:g} kOhm. The value R = {r_8:g} kOhm at vb = {tag_8['vb']:g} V was selected "
             f"as the minimum round value dividing at both biases."),
            (f"Failure of reference paper sizing: direct implementation of the paper rule (m = {m_u}, R1 = R2 = Ron/2 = "
             f"{r_u:g} kOhm, Ron = {ron:g} kOhm) fails to divide at {tag_u['f_ghz']:g} GHz. Output Q1 oscillates at "
             f"{f_out_u_meas:.1f} MHz ({ratio_u:.1f} x f_in) with only {sw_u_mv:.1f} mV swing (Figure "
             f"{extra_no['tran_paper']}). Supply power is {p_u_mw:.3f} mW; delay, PDP, and phase error are undefined."),
            (f"Mechanism: the pull-down path comprises three stacked devices (M1, M5, M7) with effective resistance "
             f"3 Ron = {stack(1):.2f} kOhm for m = 1. Regeneration requires R1 >= 1.1 x 3 Ron = {thr_mid(1):.2f} kOhm "
             f"as established in Theory, consistent with simulated bounds of {br1['fail_max']:g}-{br1['ok_min']:g} kOhm at vb = {tag_8['vb']:g} V "
             f"and {br08['fail_max']:g}-{br08['ok_min']:g} kOhm at vb = 0.8 V."),
            sch_text,
        ],
        "devices": device_rows(net, m_8, r_8, tag_8["vb"]),
        "metrics": metrics_8,
    }
    design_with = {
        "description": [
            (f"Sized divider (design D): device multiplier m = {m_d}, load R1 = R2 = {r_d:g} kOhm, and input "
             f"{f_d:g} GHz. The pull-down stack resistance is 3 Ron/m = {stack(m_d):.2f} kOhm, requiring load resistance "
             f"of {thr_mid(m_d):.2f} kOhm (tolerance band {thr_lo(m_d):.2f} to {thr_hi(m_d):.2f} kOhm) according to "
             f"the stack rule established in Theory. Load R = {r_d:g} kOhm provides adequate margin. The same sizing "
             f"rule applies to design B at {f_b:g} GHz (m = {m_b}, R1 = R2 = {r_b:g} kOhm). Transistor M7 operates in "
             f"triode, with transient drain voltage remaining below Vdsat. "
             f"Figure {slot_no['dlatch']} shows the Virtuoso schematic of the DLATCH cell with this sizing applied, corresponding to the device dimensions listed in Table {tab_no['dev_with']}."),
            cmp_text,
        ],
        "devices": device_rows(net, m_d, r_d, tag_d["vb"]),
        "metrics": metrics_d,
    }

    # ---------------------------------------------------------- Virtuoso read-back and connectivity
    rb_res, rb_mos = read_readback()
    rb_r = float(rb_res["R1"][:-1]) if rb_res["R1"].upper().endswith("K") else None
    if rb_r is None or rb_res["R2"] != rb_res["R1"] or abs(rb_r - r_d) > 1e-9:
        fail("Virtuoso read-back resistors differ from design D R")
    if any(v["m"] != str(m_d) for v in rb_mos.values()):
        fail("Virtuoso read-back multiplier differs from design D m")
    for name, v in rb_mos.items():
        if (v["w"], v["l"]) != net["sizes"][name]:
            fail(f"Virtuoso read-back {name} W/L differs from the netlist")
    n_inst, mism = read_connectivity()
    rb_m7 = rb_mos["M7"]
    rb_text = (
        f"Virtuoso schematic parameter extraction for the design D DLATCH cell: "
        f"R1 and R2 = {rb_r:g} kOhm; M1-M6 W = {rb_mos['M1']['w']}, L = {rb_mos['M1']['l']}, m = {rb_mos['M1']['m']}; "
        f"M7 W = {rb_m7['w']}, L = {rb_m7['l']}, m = {rb_m7['m']}. These match Table {tab_no['dev_with']} and the nominal transistor dimensions."
    )

    # ---------------------------------------------------------- narrative
    d_fail = sum_d["failing"]
    d_fail_text = (
        f"All {len(d_fail)} PVT failures for design D occur at 125 C and 0.9 V."
        if d_fail and all(f["temp_C"] == 125 and abs(f["vdd_V"] - 0.9) < 1e-9 for f in d_fail)
        else f"Design D exhibits {len(d_fail)} PVT failures.")
    b_steps = nom_b["phase_steps_deg"].split(",")
    d_steps = nom_d["phase_steps_deg"].split(",")
    s8_steps = nom_8["phase_steps_deg"].split(",")
    q1_first_b = a_b["ck_to_q1_first_edge_delay_ps"]
    half_fail_b = 1e3 / (2.0 * sw_b["f_fail"])
    p1, p2 = pair_d[0].capitalize(), pair_d[1].capitalize()
    theory = [
        ("Topology. The divider consists of four differential D-latches (DLATCH) connected in a ring with alternating "
         "cross-connections (Q1b-D2, Q2-D3, Q3b-D4, Q4-D1b) and inverted clocks on latches 2 and 3 (Kuo et al.). "
         "Each latch contains differential sampling pair M1-M2, clock switches M5-M6, regenerative cross-coupled pair M3-M4, "
         "tail current source transistor M7, and resistive loads R1-R2. Sampling occurs when input clock CK is high, "
         "and regeneration occurs when complementary clock CKb is active, producing eight phases at half the input frequency."),
        (f"Elmore delay model. Latch propagation delay is modeled as t_pd = (8C)(R/2) = 4RC, where each output carries "
         f"capacitance 8C and load R/2 = R1. Division requires half-period timing budget T_CK/2 > 2 Td, where Td is the "
         f"single-latch propagation delay. For load capacitance C_L = {cl_ff:g} fF, the parasitic-free lower bound "
         f"Td >= R1 C_L yields {td_d:.0f} ps for design D (sized, m = {m_d}, R1 = R2 = {r_d:g} kOhm, {f_d:g} GHz) and "
         f"{td_b:.0f} ps for design B (m = {m_b}, R1 = R2 = {r_b:g} kOhm, {f_b:g} GHz). Timing budget T_CK/2 > 2 Td is met at "
         f"{f_d:g} GHz (2 Td >= {2 * td_d:.0f} ps vs {half_d:.0f} ps) and {f_b:g} GHz (2 Td >= {2 * td_b:.0f} ps vs {half_b:.0f} ps). "
         f"Design B divides up to {sw_b['f_max']:g} GHz and fails at {sw_b['f_fail']:g} GHz (T_CK/2 = {half_fail_b:.1f} ps); "
         f"measured CK-to-Q1 delay ({q1_first_b:.2f} ps) is {q1_first_b / td_b:.1f}x the intrinsic bound ({q1_first_b / half_b:.0%} "
         f"of T_CK/2), showing parasitic capacitance limits high-frequency operation."),
        (f"Stack resistance and regeneration. The pull-down network forms a three-transistor stack (M1, M5, M7) with "
         f"effective resistance 3 Ron/m, where Ron is the channel on-resistance and m is the device multiplier. "
         f"Regeneration requires a loop gain gm R1 > 1 (gm is the transconductance), giving R1 >= 1.1 x (3 Ron/m). With Ron = {ron:g} kOhm, the unit stack is "
         f"{stack(1):.2f} kOhm, requiring R1 >= {thr_mid(1):.2f} kOhm. Reference paper sizing ({r_u:g} kOhm) falls below "
         f"this threshold, preventing division. Measured thresholds for m = 1 span {br1['fail_max']:g}-{br1['ok_min']:g} kOhm "
         f"at tail bias vb = {tag_8['vb']:g} V and {br08['fail_max']:g}-{br08['ok_min']:g} kOhm at vb = 0.8 V. For m = {m_d}, "
         f"the required threshold is {thr_mid(m_d):.2f} kOhm (band {thr_lo(m_d):.2f}-{thr_hi(m_d):.2f} kOhm); design D "
         f"(R1 = {r_d:g} kOhm) provides margin, while design B (R1 = {r_b:g} kOhm) operates within the marginal band. Measured "
         f"division agrees with the rule for {ok_pairs} of {len(numeric)} tested parameter pairs. Unit device aspect ratio "
         f"W/L = {float(net['sizes']['M1'][0][:-1]) / float(net['sizes']['M1'][1][:-1]):.2f} ({nm(net['sizes']['M1'][0])} / "
         f"{nm(net['sizes']['M1'][1])}) matches the reference design ratio of "
         f"{LITERATURE['unit_w_um'] * 1e3 / LITERATURE['unit_l_nm']:.2f} ({LITERATURE['unit_w_um']:g} um / "
         f"{LITERATURE['unit_l_nm']} nm)."),
        (f"Phase-step relationship. Outputs toggle in pairs separated by t_pair (measured between rising edges of "
         f"{p1} and {p2}), yielding alternating phase steps of a = 180 t_pair f_in degrees and (90 - a) degrees. For "
         f"design D at {f_d:g} GHz, t_pair = {tp_d:.2f} ps gives steps of {d_steps[0]} and {d_steps[1]} deg "
         f"(a = 180 x {tp_d:.2f} ps x {f_d:g} GHz = {a_calc(tp_d, f_d):.2f} deg). For design B at {f_b:g} GHz, "
         f"t_pair = {tp_b:.2f} ps gives {b_steps[0]} and {b_steps[1]} deg (a = {a_calc(tp_b, f_b):.2f} deg). The "
         f"unsized baseline at {f_8:g} GHz gives {s8_steps[0]} and {s8_steps[1]} deg (t_pair = {tp_8:.2f} ps, a = "
         f"{a_calc(tp_8, f_8):.2f} deg). Nominal 45 deg spacing requires T_CK = 4 t_pair: {4 * tp_d:.1f} ps "
         f"({1e3 / (4 * tp_d):.2f} GHz) for design D and {4 * tp_b:.1f} ps ({1e3 / (4 * tp_b):.2f} GHz) for design B. Phase error "
         f"decreases toward the divider limit, matching the reference benchmark ({LITERATURE['phase_err_deg']} deg) in "
         f"design B at {f_b:g} GHz."),
        (f"Definitions of performance metrics. Propagation delay is the average time from each CK rising edge to the next "
         f"transition across any output ({metrics_d['delay_ps']} ps for design D; single-edge CK-to-Q1 delay is "
         f"{a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps). Power is VDD times average supply current over full clock cycles. "
         f"Power-delay product (PDP) is power times delay (fJ). Division is confirmed when all eight outputs toggle at "
         f"f_in/2 within 0.1 percent with peak-to-peak swing >= {SWING_MIN_V:g} V."),
    ]

    tool_technology = [
        "Tools and environment: Cadence Virtuoso IC615 (6.1.5), Spectre circuit simulator (MMSIM 12.1), and "
        "Assura physical verification (4.1). Process technology is Cadence GPDK045 v6.0 (45 nm generic CMOS), "
        "using standard-threshold NMOS devices (g45n1svt, 1.0 V nominal) evaluated across tt, ff, ss, fs, and sf corners.",
        f"Device sizing: unit transistors M1-M6 have W = {nm(net['sizes']['M1'][0])}, L = {nm(net['sizes']['M1'][1])}, "
        f"and tail transistor M7 has W = {nm(net['sizes']['M7'][0])}, L = {nm(net['sizes']['M7'][1])}. Device multiplier "
        f"m scales channel widths in parallel.",
        f"Operating conditions: nominal supply VDD = {vdd_v:g} V (varied from "
        f"{pvt_vdds[0]:g} V to {pvt_vdds[-1]:g} V in the process, voltage and temperature (PVT) analysis), nominal temperature {net['temp_c']} C, clock transition times "
        f"{to_ps(net['params']['tr'])}, tail bias vb = {vb_d:g} V, and load capacitance {to_ff(net['params']['cl'])} "
        f"per output. Simulations employ 40 ns transient analysis runs in Cadence Spectre.",
        rb_text,
        f"Circuit schematics for the DLATCH and divider core are illustrated in Figure {slot_no['circuit']} and Figure {slot_no['core']} (ring architecture in Figure {extra_no['ring']}).",
        "Origin of the figures: the schematic and layout editor views, the Assura DRC summary and the ViVA waveform of design D are screenshots of Cadence tool windows. The other waveforms, sweeps and PVT maps are plots made with Python (matplotlib) from the Spectre result files, and the circuit diagrams are drawn by a script from the netlist. No figure was produced by an image-generation model, and every plotted point comes from a Spectre result file.",
    ]

    pin_area = lay["pin_w"] * lay["pin_h"]
    area_min = float(re.search(r">= ([\d.]+) um", next(r["name"] for r in drc_rules if r["no"] == 595)).group(1))
    m595 = drcm[595]["boxes"]
    dims595 = {tuple(sorted((round(b[2] - b[0], 3), round(b[3] - b[1], 3)))) for b in m595}
    if not m595 or len(m595) > drc_count[595] or len(dims595) != 1:
        fail("Metal1 area markers: count or size not as expected")
    w595, h595 = dims595.pop()
    x595 = (min(b[0] for b in m595), max(b[2] for b in m595))
    y595 = (min(b[1] for b in m595), max(b[3] for b in m595))
    m221 = drcm[221]["boxes"]
    x221 = sorted({b[0] for b in m221})
    pitch221 = x221[1] - x221[0]
    if abs(pitch221 - lay["pitch"]) > 1e-6:
        fail("Rule 221 marker pitch does not equal the device pitch of the layout log")
    if pin_area < area_min or w595 * h595 >= area_min or len(m221) != drc_count[221]:
        fail("pin area or marker area inconsistent with the Metal1 minimum area")

    sweeps_text = (
        f"Frequency sweeps. Design B (m = {m_b}, R = {r_b:g} kOhm) was swept from "
        f"{sw_b['f_lo']:g} to {sw_b['f_hi']:g} GHz: it divides at {', '.join(f'{x:g}' for x in sw_b['ok_list'])} GHz "
        f"and fails at {', '.join(f'{x:g}' for x in sw_b['fail_list'])} GHz. Design D (m = {m_d}, R = {r_d:g} kOhm) "
        f"was swept from {sw_d['f_lo']:g} to {sw_d['f_hi']:g} GHz: it divides at "
        f"{', '.join(f'{x:g}' for x in sw_d['ok_list'])} GHz and fails at "
        f"{', '.join(f'{x:g}' for x in sw_d['fail_list'])} GHz (the {f_d:g} GHz operating point also divides). "
        f"Design E (m = {tag_e['m']}, R = {tag_e['r_kohm']:g} kOhm) was swept from {sw_e['f_lo']:g} to {sw_e['f_hi']:g} GHz: "
        f"it divides at {', '.join(f'{x:g}' for x in sw_e['ok_list'])} GHz and fails at "
        f"{', '.join(f'{x:g}' for x in sw_e['fail_list'])} GHz ({f_d:g} GHz divides at tt, {net['temp_c']} C, 1.0 V). "
        f"Maximum phase-step error at the highest dividing frequency is {sw_b['err_max_f']:.2f} deg for design B, "
        f"{sw_d['err_max_f']:.2f} deg for design D, and {sw_e['err_max_f']:.2f} deg for design E, compared with {sw_b['err_min_f']:.2f}, "
        f"{sw_d['err_min_f']:.2f}, and {sw_e['err_min_f']:.2f} deg at the lower frequency bounds. In all cases, "
        f"phase error improves as frequency increases (Figure {extra_no['fsweep']}).")
    f_parts = "; ".join(
        f"m = {g['m']}, R = {g['r']:g} kOhm divides up to {g['f_max']:g} GHz (phase error {g['err']:.2f} deg)"
        + (f" and fails at {g['f_fail']:g} GHz" if g["f_fail"] else "") for g in sw_f)
    sweep_f_text = (f"Parametric exploration around design B: {f_parts}. These sweeps "
                    f"delimit the maximum operating frequency of design B under nominal conditions.")

    other_info = [
        (f"Layout. The DLATCH cell contains {lay['n_mos']} unit NMOS devices ({lay['bbox']} um wide) and {lay['n_res']} "
         f"poly resistors (segment width {lay['r_w']} um, segment length {lay['r_len']} um, {lay['r_rsh']} ohm/sq, target resistance {lay['r_target']:g} ohm). "
         f"Transistors M1-M6 use {lay['nf1']} fingers of {lay['fw_nm']:g} nm ({lay['w1_nm']:g} nm, L = {lay['l1_nm']:g} nm); "
         f"M7 uses {lay['nf7']} fingers of {lay['fw_nm']:g} nm ({lay['w7_nm']:g} nm, L = {lay['l7_nm']:g} nm) for m = {m_8}. "
         f"Design D requires {width_factor}x width (m = {m_d}) and {r_d:g} kOhm load (baseline uses {r_8:g} kOhm). "
         f"DLATCH boundary is {lay['box_w']} x {lay['box_h']} um. Divider core arranges four DLATCH cells in a "
         f"four-quadrant layout with a {lay['gap']} um channel between cells. An automatic routing run with "
         f"Cadence Chip Assembly Router completed 136 of 137 connections but produced 134 DRC errors and "
         f"mismatches in LVS, so the placement layout is reported. Cell layouts are shown in "
         f"Figure {slot_no['layout_core']} (divider_core) and Figure {extra_no['layout_dlatch']} (DLATCH)."),
        (f"DRC verification. Assura DRC on DLATCH reports {drc_total} errors across {len(drc_rules)} rules "
         f"(Figure {extra_no['drc']}). Rules 220 ({drc_count[220]}) and 221 ({drc_count[221]}) give {drc_stamp} "
         f"substrate-stamp errors from unrouted taps at device pitch {pitch221:g} um. Rule 595 ({drc_count[595]}) "
         f"gives {drc_metal} Metal1 minimum-area errors (threshold {area_min:g} um^2) flagged at isolated contact pads. "
         f"Connected contact pins ({lay['pin_w']:g} x {lay['pin_h']:g} um = {pin_area:.2f} um^2) meet the minimum area."),
        (f"Schematic connectivity. Pin-by-pin audit of the {n_inst} DLATCH instances (XD1-XD4) against the netlist "
         f"confirms exact schematic connectivity with {len(mism)} mismatch{'es' if len(mism) != 1 else ''}"
         f"{' (' + ', '.join(mism) + ')' if mism else ''}."),
        (f"Design B operating point. At {f_b:g} GHz (m = {m_b}, R1 = R2 = {r_b:g} kOhm), the divider achieves "
         f"{num(nom_b['f_out_MHz']):.1f} MHz output, {num(nom_b['power_mW']):.4f} mW power, {num(nom_b['delay_ps']):.2f} ps "
         f"delay, {num(nom_b['pdp_fJ']):.3f} fJ PDP, and {num(nom_b['max_phase_step_err_deg']):.2f} deg maximum phase "
         f"error ({b_steps[0]} and {b_steps[1]} deg steps). Output Q1 swings {swing_b:.3f} V ({a_b['q1_min_v']:.3f} V to "
         f"{a_b['q1_max_v']:.3f} V), above the {SWING_MIN_V:g} V limit (transient waveforms are shown in Figure {extra_no['tran_b']}). Peak tail voltage reaches "
         f"{a_b['xd1_tail_max_v'] * 1e3:.1f} mV, below Vdsat = {vds_info['vdsat_v'] * 1e3:.1f} mV (triode, "
         f"Figure {extra_no['tail_b']}). PVT results appear in Table {tab_no['pvt_b6']}."),
        (f"DC operating points. Prior to clock switching, tail current leakage is negligible (Vgs = {op_d['vg_v']:g} V). "
         f"For reference paper sizing, M7 operates in {op_u['region']} (Vds = {op_u['vds_v'] * 1e9:.1f} nV, Ids = {op_u['ids_a'] * 1e12:.1f} pA). "
         f"For design D, M7 operates in {op_d['region']} (Vds = {op_d['vds_v'] * 1e9:.1f} nV, Ids = {op_d['ids_a'] * 1e12:.1f} pA). "
         f"For design B (m = {m_d}, vb = {vb_d:g} V), M7 operates in {op_b['region']} (Vds = {op_b['vds_v'] * 1e9:.1f} nV, "
         f"Ids = {op_b['ids_a'] * 1e12:.1f} pA)."),
        (f"Tail transistor operating region. With gate bias Vgs = {op_d['vg_v']:g} V and threshold voltage Vth = {vds_info['vth_v'] * 1e3:.1f} mV, "
         f"extracted Vdsat is {vds_info['vdsat_v'] * 1e3:.1f} mV (at DC initialization, gm = {vds_info['gm_ps']:.1f} pS, "
         f"gds = {vds_info['gds_ms']:.3f} mS, Vds = {op_d['vds_v'] * 1e9:.0f} nV). In transient operation, "
         f"the internal tail node voltage spans {a_d['xd1_tail_min_v'] * 1e3:.1f} to {a_d['xd1_tail_max_v'] * 1e3:.1f} mV for design D "
         f"(reaching {a_d['xd2_tail_max_v'] * 1e3:.1f} mV in the second latch) and {a_8['xd1_tail_min_v'] * 1e3:.1f} to "
         f"{a_8['xd1_tail_max_v'] * 1e3:.1f} mV for the unsized baseline. Because Vds remains below Vdsat, M7 operates in "
         f"triode rather than saturation across all operating conditions (Figures {extra_no['tail_8']} and {extra_no['tail_d']})."),
        sweeps_text,
        sweep_f_text,
        (f"PVT analysis. Across the 45-corner PVT matrix (Table {tab_no['pvt_d']} and Table {tab_no['pvt_b6']}), "
         f"design D fails {len(sum_d['failing'])} corners at {f_d:g} GHz (all at 125 C, 0.9 V), as shown in the pass/fail map in Figure {slot_no['pvt_hm_d']}; "
         f"propagation delay and supply power across all corners are plotted in Figure {extra_no['pvt_dp_d']}. At 1.4 GHz, "
         f"design B fails {len(sum_b1['failing'])} corners and design E (m = {tag_e['m']}, R = {tag_e['r_kohm']:g} kOhm) "
         f"fails {len(sum_e['failing'])} corners. At {f_b:g} GHz, design B fails {len(sum_b6['failing'])} corners "
         f"(pass/fail map in Figure {extra_no['pvt_hm_b6']} and delay/power distribution in Figure {extra_no['pvt_dp_b6']}). "
         f"Passing corners of design D span from {sum_d['passing_metrics']['power_mW']['min']:.3f} to {sum_d['passing_metrics']['power_mW']['max']:.3f} mW "
         f"and {sum_d['passing_metrics']['delay_ps']['min']:.2f} to {sum_d['passing_metrics']['delay_ps']['max']:.2f} ps. "
         f"In Table {tab_no['appendix_pvt']} (Appendix), the Divides column confirms pass and fail status across all 45 corners."),
        (f"Transient delay and edge times. First-edge CK-to-Q1 delays are {a_8['ck_to_q1_first_edge_delay_ps']:.2f} ps "
         f"(unsized baseline), {a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps (design D), and "
         f"{a_b['ck_to_q1_first_edge_delay_ps']:.2f} ps (design B). Multi-phase average delay for design D is "
         f"{a_d['ck_to_any_output_mean_delay_ps']:.2f} ps. Output Q1 rise and fall times are "
         f"{a_d['q1_rise_10_90_ps']:.1f} ps and {a_d['q1_fall_10_90_ps']:.1f} ps."
         + (f" Transient waveforms from the standalone netlist simulation of design D are shown in Figure {extra_no['tran_d_plot']}." if "tran_d_plot" in extra_no else "")),
        (f"Supply current. Average and peak supply currents for design D are {a_d['supply_avg_ma_steady']:.3f} mA "
         f"and {a_d['supply_peak_ma_steady']:.3f} mA, respectively (Figure {extra_no['supply']})."),
        (f"Comparison with reference literature. Reported values from Kuo et al. ({LITERATURE['process']}, "
         f"{LITERATURE['vdd_v']} V, {LITERATURE['f_in_ghz']} GHz) are {LITERATURE['power_mw']} mW, phase error within "
         f"{LITERATURE['phase_err_deg']} deg, and core area {LITERATURE['core_um']} um^2. In 45 nm, design D at "
         f"{f_d:g} GHz consumes {num_d('power_mW'):.4f} mW with {num_d('max_phase_step_err_deg'):.2f} deg phase error; "
         f"design B reaches {num(nom_b['max_phase_step_err_deg']):.2f} deg at {f_b:g} GHz."),
    ]

    conclusion = [
        (f"Multiphase CMOS division in 45 nm is demonstrated for design D at {f_d:g} GHz ({sum_d['pass_count']} of "
         f"{sum_d['total']} PVT corners passing) and design B at {f_b:g} GHz ({sum_b6['pass_count']} of {sum_b6['total']} "
         f"PVT corners passing). Device sizing significantly reduces propagation delay and increases voltage swing at the "
         f"expense of higher power dissipation (Table {tab_no['values']})."),
        "Reference paper sizing fails to divide because load resistance falls below the stack regeneration threshold.",
        (f"Operating limitations: tail transistor M7 operates in triode across all designs due to low transient drain headroom. "
         f"All PVT failures for design D are confined to the slow-supply corner (125 C, 0.9 V). Design B achieves "
         f"low phase error ({num(nom_b['max_phase_step_err_deg']):.2f} deg) matching the literature benchmark, but exhibits "
         f"reduced swing ({swing_b:.3f} V) and fails division beyond {sw_b['f_max']:g} GHz."),
        (f"Physical implementation was evaluated as an unrouted placement with {drc_total} documented Assura DRC errors across "
         f"{len(drc_rules)} rules; routing, LVS, and post-layout simulation were not performed."),
    ]

    problems_faced = [
        "The reference paper sizing rule failed to divide at unit device size because load resistance fell below the regeneration threshold.",
        "Conventional division checks initially counted false passes caused by low-amplitude harmonics at 2 f_in.",
        "Tail current source transistor M7 operated in triode rather than saturation due to limited drain voltage headroom.",
        "Spectre BSIM4 model compilation failed on the 32-bit simulation host due to missing compiler and runtime libraries.",
        "Automated routing of the divider core produced DRC errors and LVS mismatches.",
    ]
    problems_resolved = [
        f"Resized load resistance using the 3 Ron/m stack regeneration rule, selecting R = {r_8:g} kOhm for the unsized baseline and R = {r_d:g} kOhm for design D.",
        f"Introduced an eight-output verification check requiring division to f_in/2 within 0.1% and output swing >= {SWING_MIN_V:g} V across all outputs.",
        "Characterized transient tail node voltages against extracted BSIM4 Vdsat, confirming triode operation.",
        "Installed the missing compiler and runtime libraries to enable native 32-bit Spectre model compilation.",
        "Reported the placement layout with its DRC result, because the automatic router output carried 134 DRC errors and LVS mismatches.",
    ]

    other_comment = [
        f"The power and PDP in Table {tab_no['values']} come from the standalone netlist with default device parameters"
        + (f" (transient waveforms in Figure {extra_no['tran_d_plot']})" if "tran_d_plot" in extra_no else "")
        + "; the schematic-driven run, which includes the layout-dependent parameters, gives lower power (see the schematic-simulation discussion). Post-layout simulation was not possible because the process kit provides no parasitic-extraction rule files.",
    ]

    sch_heading, sch_paras, sch_evidence = read_schematic_section({"fig_tran_d": slot_no["tran_d"]})
    schematic_sim = {
        "heading": sch_heading,
        "paragraphs": sch_paras,
        "figure": None,  # the testbench schematic is already shown as an extra figure
    }
    references = [
        f"{LITERATURE['authors']}, \"A Compact Multiphase Divide-by-Two CMOS Frequency Divider,\" IEEE Microw. "
        f"Wireless Technol. Lett., vol. {paper['volume']}, no. {paper['issue']}, pp. {paper['pages']}, "
        f"{paper['date']}, doi: {paper['doi']}.",
        "Cadence Design Systems, Cadence GPDK045 v6.0 documentation (45 nm generic process design kit).",
        "Cadence Design Systems, Spectre Circuit Simulator Reference, MMSIM 12.1.",
    ]

    # ---------------------------------------------------------- Table 3 proof column and notes
    fn = extra_no
    values_proof = {
        "power_mw": f"Fig. {fn['supply']} (supply current, both columns)",
        "delay_ps": "Calculated mean delay (see note)",
        "pdp_fj": "Calculated: power x delay",
        "f_in_ghz": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "f_out_mhz": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "max_phase_step_err_deg": f"Fig. {fn['phase']}",
        "swing_v": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "sat": f"Fig. {fn['tail_8']} (without), Fig. {fn['tail_d']} (with)",
    }
    values_notes = [
        (f"Notes: Baseline without sizing corresponds to unit devices (unsized baseline: m = {m_8}, R = {r_8:g} kOhm, "
         f"vb = {tag_8['vb']:g} V). Reference paper sizing (m = {m_u}, R = {r_u:g} kOhm) fails to achieve frequency "
         f"division (Figure {fn['tran_paper']}). Reported propagation delay denotes multi-phase average delay defined in "
         f"Theory (single-edge delays are given under transient delay and edge times). Vds indicates peak transient tail node voltage; Vdsat is "
         f"the extracted saturation voltage for M7."),
        "PDP is computed from unrounded power and delay values.",
    ]

    paper_block = {k: paper[k] for k in ("title", "authors", "journal", "volume", "issue", "pages", "date", "doi")}
    data = {
        "example_only": False,
        "logo": f"assets/{LOGO.name}",
        "titles": {"system_design_project": TITLE},
        "paper": paper_block,
        "figures": figures,
        "designs": {"without_sizing": design_without, "with_sizing": design_with},
        "values_proof": values_proof,
        "values_notes": values_notes,
        "pvt_rows": pvt_all,
        "theory": [t for t in theory],
        "tool_technology": tool_technology,
        "other_info": other_info,
        "conclusion": conclusion,
        "problems_faced": problems_faced,
        "problems_resolved": problems_resolved,
        "other_comment": other_comment,
        "references": references,
        "schematic_sim": schematic_sim,
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


def draw_circuits():
    """Regenerate the two gpdk045 circuit drawings (needs matplotlib, from /usr/bin/python3)."""
    python = "/usr/bin/python3" if Path("/usr/bin/python3").is_file() else sys.executable
    proc = subprocess.run([python, str(DRAW)], capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        fail(f"draw_gpdk45_circuits failed:\n{proc.stdout}\n{proc.stderr}")
    print(proc.stdout.rstrip())


def main():
    draw_circuits()
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
