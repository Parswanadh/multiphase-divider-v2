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


def read_raw_header(name):
    head = (FINAL / name).read_text(encoding="utf-8", errors="replace").splitlines()[:6]
    plot = next((ln.split(":", 1)[1].strip() for ln in head if ln.startswith("Plotname:")), None)
    date = next((ln.split(":", 1)[1].strip() for ln in head if ln.startswith("Date:")), None)
    if plot is None or date is None:
        fail(f"{name}: raw header lines not found")
    return plot, date


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


def screen(name, caption):
    """A Cadence screenshot, or a path that the builder reports as NOT YET AVAILABLE."""
    return {"file": f"screens/{name}.png", "caption": caption}


def screen_or_none(name, caption):
    return screen(name, caption) if (SCREEN_DIR / f"{name}.png").is_file() else None


def read_schematic_section():
    """Subsection on the OCEAN simulation from the Virtuoso schematic (section_schematic_sim.md).

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
    raw_plot, raw_date = read_raw_header("D_1p4.raw")
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
    extra_keys = ["ring", "tran_paper", "tran_b", "phase", "tail_8", "tail_d", "tail_b", "supply",
                  "fsweep", "pvt_dp_d", "pvt_hm_b6", "pvt_dp_b6", "tb", "ciw", "layout_dlatch", "drc"]
    extra_no = {key: EXTRA_FIG_START + i for i, key in enumerate(extra_keys)}
    slot_no = {"circuit": 1, "core": 2, "tran_8": 3, "dlatch": 4, "tran_d": 5, "pvt_hm_d": 6, "layout_core": 7}

    schc = read_schcheck()
    sch_text = (f"schCheck errors/warnings: DLATCH {schc['DLATCH']}, divider_core {schc['divider_core']}, "
                f"tb_divider {schc['tb_divider']}; connectivity in the schematics is by net labels")
    vdsat_note = (f"Vdsat = {vds_info['vdsat_v']:.3f} V was extracted for design D at the t = 0 point (Vgs = "
                  f"{op_d['vg_v']:g} V)")
    extras = [
        ("ring", plotted("fig_circuit_ring",
                         f"Ring interconnection of the four DLATCH instances XD1 to XD4 (alternating cross-connections, "
                         f"CK and CKb swapped on XD2 and XD3), drawn by scripts/draw_gpdk45_circuits.py from "
                         f"spectre/divider_gpdk45.scs (topology and W, L); the m and R labels are those of design D "
                         f"(m = {m_d}, R = {r_d:g} kOhm). Generated drawing, not a Cadence screenshot.")),
        ("tran_paper", plotted("fig_tran_unsized",
                               f"Paper-rule circuit (m = {m_u}, R1 = R2 = {r_u:g} kOhm = Ron/2) at {tag_u['f_ghz']:g} GHz, "
                               f"plotted from Spectre output (not a simulator screenshot). It does not divide: Q1 "
                               f"follows the clock at {f_out_u_meas:.1f} MHz and swings only {sw_u_mv:.1f} mV "
                               f"({a_u['q1_min_v']:.3f} V to {a_u['q1_max_v']:.3f} V).")),
        ("tran_b", plotted("fig_tran_B_6g",
                           f"Transient waveforms of design B at {f_b:g} GHz (m = {m_b}, R1 = R2 = {r_b:g} kOhm), "
                           f"plotted from Spectre output. Output period-measured frequency "
                           f"{num(nom_b['f_out_MHz']):.1f} MHz.")),
        ("phase", plotted("fig_phase_steps",
                          f"Phase steps between the eight outputs for the baseline U8k ({f_8:g} GHz), design D "
                          f"({f_d:g} GHz) and design B ({f_b:g} GHz), plotted from the nominal Spectre results.")),
        ("tail_8", plotted("fig_tail_saturation_U8k",
                           f"Tail (M7) drain voltage of the baseline U8k compared with Vdsat = "
                           f"{vds_info['vdsat_v']:.3f} V, plotted from Spectre output. M7 has the same W, L and Vgs as "
                           f"in design D, and the multiplier only places devices in parallel, so the Vdsat extracted "
                           f"for D is used.")),
        ("tail_d", plotted("fig_tail_saturation_D_1p4",
                           f"Tail (M7) drain voltage of design D at {f_d:g} GHz compared with the M7 saturation "
                           f"voltage Vdsat = {vds_info['vdsat_v']:.3f} V, plotted from Spectre output.")),
        ("tail_b", plotted("fig_tail_saturation_B_6g",
                           f"Tail (M7) drain voltage of design B at {f_b:g} GHz compared with Vdsat = "
                           f"{vds_info['vdsat_v']:.3f} V (the value extracted for design D; B has the same M7 sizing "
                           f"and bias and the same t = 0 operating point), plotted from Spectre output.")),
        ("supply", plotted("fig_supply_current",
                           "Supply current drawn from VDD for U8k, D and B, plotted from Spectre output; the table "
                           "power is VDD times the mean over whole output periods.")),
        ("fsweep", plotted("fig_fsweep",
                           "Frequency sweep of designs B, D and E (fs_B.tsv, fs_D.tsv, fs_E.tsv): divided "
                           "output and maximum phase-step error against input frequency.")),
        ("pvt_dp_d", plotted("fig_pvt_delay_power_D_1p4",
                             "Delay and power over the PVT matrix of design D at 1.4 GHz, plotted from pvt_D.tsv. "
                             "Passing points are drawn as lines; a red cross at the foot of each plot marks the "
                             "failing points at that supply voltage, with their count.")),
        ("pvt_hm_b6", plotted("fig_pvt_heatmap_B_6g",
                              f"PVT pass/fail map of design B at {f_b:g} GHz, plotted from pvt_B6.tsv. "
                              f"{sum_b6['pass_count']} of {sum_b6['total']} points pass.")),
        ("pvt_dp_b6", plotted("fig_pvt_delay_power_B_6g",
                              f"Delay and power over the PVT matrix of design B at {f_b:g} GHz, plotted from "
                              f"pvt_B6.tsv. Passing points are drawn as lines; a red cross at the foot of each plot "
                              f"marks the failing points at that supply voltage, with their count.")),
        ("tb", crop("schematic_tb_crop",
                    f"Virtuoso schematic of the testbench tb_divider (Cadence GUI screenshot, cropped to the "
                    f"schematic window). {sch_text}.")),
        ("ciw", crop("virtuoso_ciw_crop",
                     "Virtuoso 6.1.5 session with the gpdk045 PDK loaded (CIW log, Cadence GUI screenshot).")),
        ("layout_dlatch", crop("layout_dlatch_crop",
                               f"Virtuoso layout of the DLATCH: {lay['n_mos']} unit-size (m = {m_8}) nmos1v pcells, "
                               f"{lay['n_res']} resnsnpoly poly resistors and pin markers (Virtuoso Layout Suite "
                               f"screenshot, cropped to the layout canvas; cell outlines only). Placement only; not "
                               f"routed.")),
        ("drc", screen("drc_result",
                       f"Assura 4.1 DRC tally for the DLATCH layout (divider_lib/DLATCH/layout, gpdk045 "
                       f"assuraDRC.rul): {drc_total} errors in {len(drc_rules)} rules (terminal capture).")),
    ]
    if [k for k, _ in extras] != extra_keys:
        fail("extra figure list and figure-number keys differ")

    figures = {
        "circuit_diagram": plotted("fig_circuit_latch",
                                   f"Circuit diagram of one differential DLATCH (M1 to M7, R1, R2), drawn by "
                                   f"scripts/draw_gpdk45_circuits.py. Topology and W, L are read from "
                                   f"spectre/divider_gpdk45.scs (M1 to M6 W = {nm(net['sizes']['M1'][0])}, "
                                   f"L = {nm(net['sizes']['M1'][1])}; M7 W = {nm(net['sizes']['M7'][0])}, "
                                   f"L = {nm(net['sizes']['M7'][1])}); the labels m = {m_d} and R1 = R2 = {r_d:g} kOhm "
                                   f"are those of design D, set per run (the baseline has m = {m_8}, R = {r_8:g} kOhm). "
                                   f"Generated drawing, not a Cadence screenshot."),
        "impl_screenshot": crop("schematic_core_crop",
                                f"Virtuoso schematic of the divider core (design D library): four DLATCH instances "
                                f"XD1 to XD4 with the ring connections (Cadence GUI screenshot). The top level is the "
                                f"same for every design; the baseline and design D differ only in m and R "
                                f"(Tables 1 and 2). No separate schematic of the baseline was captured. {sch_text}."),
        "waveform_without_sizing": plotted(
            "fig_tran_U8k",
            f"Transient waveforms of the baseline without sizing, U8k (m = {m_8}, R1 = R2 = {r_8:g} kOhm, "
            f"vb = {tag_8['vb']:g} V) at {f_8:g} GHz, plotted from Spectre output (not a simulator screenshot). "
            f"All eight outputs divide: {num_8('f_out_MHz'):.1f} MHz, Q1 between {a_8['q1_min_v']:.3f} V and "
            f"{a_8['q1_max_v']:.3f} V. The non-dividing paper-rule circuit is Figure {extra_no['tran_paper']}."),
        "sized_circuit_screenshot": crop(
            "schematic_dlatch_crop",
            f"Virtuoso schematic of the DLATCH of design D with sizing: m = {m_d}, R1 = R2 = {r_d:g} kOhm "
            f"(Cadence GUI screenshot, cropped). Device parameters read back from the Virtuoso database are "
            f"given in the Tool and Technology section and agree with Table 2. {sch_text}."),
        "waveform_with_sizing": plotted(
            "fig_tran_D_1p4",
            f"Transient waveforms of design D (m = {m_d}, R1 = R2 = {r_d:g} kOhm) at {f_d:g} GHz, plotted from "
            f"Spectre output (not a simulator screenshot). Q1 swings between {a_d['q1_min_v']:.3f} V and "
            f"{a_d['q1_max_v']:.3f} V; output {num_d('f_out_MHz'):.1f} MHz; the tail voltage V(XD1.tail) stays "
            f"between {a_d['xd1_tail_min_v'] * 1e3:.1f} mV and {a_d['xd1_tail_max_v'] * 1e3:.1f} mV (XD2 up to "
            f"{a_d['xd2_tail_max_v'] * 1e3:.1f} mV)."),
        "pvt_screenshot": plotted(
            "fig_pvt_heatmap_D_1p4",
            f"PVT pass/fail map of design D at {f_d:g} GHz ({len(pvt_corners)} corners x "
            f"{'/'.join(str(t) for t in pvt_temps)} C x {'/'.join(f'{v:g}' for v in pvt_vdds)} V), plotted "
            f"from pvt_D.tsv, not a Cadence screenshot. {sum_d['pass_count']} of {sum_d['total']} points pass."),
        "layout_screenshot": crop(
            "layout_core_crop",
            "Virtuoso layout of divider_core: four DLATCH instances (XD1 to XD4) placed in a 2x2 arrangement, "
            "placement only (Virtuoso Layout Suite screenshot, cropped to the layout canvas; cell outlines only). "
            "Routing is not drawn."),
        "layout_waveform": {
            "note": ("Post-layout simulation was not performed. The layout is placement only (not routed, not "
                     "extracted), so no post-layout waveform exists; every result in this report is a pre-layout "
                     "simulation.")},
        "extra_figures": [item for _, item in extras],
    }
    if figures["layout_waveform"] is None:
        fail("layout_waveform slot must be a note")

    # ---------------------------------------------------------- designs
    cmp_text = (
        f"Comparison with the baseline (Table 3): sizing cuts the CK-to-output delay from "
        f"{metrics_8['delay_ps']} ps (U8k) to {metrics_d['delay_ps']} ps (D), a factor "
        f"{metrics_8['delay_ps'] / metrics_d['delay_ps']:.2f}, but it raises the power from {metrics_8['power_mw']} mW "
        f"to {metrics_d['power_mw']} mW (factor {metrics_d['power_mw'] / metrics_8['power_mw']:.2f}) and the PDP from "
        f"{metrics_8['pdp_fj']} fJ to {metrics_d['pdp_fj']} fJ (factor {metrics_d['pdp_fj'] / metrics_8['pdp_fj']:.2f}). "
        f"The maximum phase-step error also grows, from {metrics_8['max_phase_step_err_deg']} deg to "
        f"{metrics_d['max_phase_step_err_deg']} deg, and the Q1 swing grows from {metrics_8['swing_v']} V to "
        f"{metrics_d['swing_v']} V. Sizing therefore buys speed and swing at the cost of power and PDP; "
        f"it does not improve the phase error at {f_d:g} GHz.")
    design_without = {
        "description": [
            (f"Baseline without sizing (U8k): unit devices (m = {m_8}), load R1 = R2 = {r_8:g} kOhm, tail bias "
             f"vb = {tag_8['vb']:g} V, input {f_8:g} GHz, tt corner, {net['temp_c']} C, VDD = {vdd_v:g} V, simulated in "
             f"Cadence Spectre (U8k.tsv, U8k.raw). W and L are read from spectre/divider_gpdk45.scs; m, R, vb and "
             f"f_in are per-run overrides recorded in the run tag ({nom_8['tag']}). All eight outputs divide "
             f"({num_8('f_out_MHz'):.1f} MHz, Q1 swing {a_8['q1_min_v']:.3f} to {a_8['q1_max_v']:.3f} V)."),
            (f"How R was chosen: the unit-size circuit was searched over R = {br1['r_lo']:g} to {br1['r_hi']:g} kOhm "
             f"at vb = 0.8 V and {tag_8['vb']:g} V ({n_search} runs, unsized_baseline.tsv). At vb = {tag_8['vb']:g} V "
             f"R up to {br1['fail_max']:g} kOhm fails and R from {br1['ok_min']:g} kOhm divides; at vb = 0.8 V "
             f"R up to {br08['fail_max']:g} kOhm fails and R from {br08['ok_min']:g} kOhm divides. {r_8:g} kOhm at "
             f"{tag_8['vb']:g} V is the smallest round value of the table that divides at both biases."),
            (f"Finding, paper-rule circuit: applying the paper's rule literally (m = {m_u}, R1 = R2 = Ron/2 = "
             f"{r_u:g} kOhm, Ron = {ron:g} kOhm from LEDGER.md) does not divide at {tag_u['f_ghz']:g} GHz. Q1 runs "
             f"at {f_out_u_meas:.1f} MHz ({ratio_u:.1f} x f_in) with a swing of only {sw_u_mv:.1f} mV (Figure "
             f"{extra_no['tran_paper']}), so these are not toggling logic outputs. Its supply power is {p_u_mw:.3f} mW "
             f"(VDD times the mean supply current in analysis.json), which is not comparable with a dividing "
             f"circuit; delay, PDP and phase error are not defined for it."),
            (f"Why: the output pull-down is a stack of three devices (M1, M5, M7), about 3 Ron = {stack(1):.2f} kOhm "
             f"for m = 1, and regeneration needs R1 of at least about 1.1 x 3 Ron = {thr_mid(1):.2f} kOhm. The "
             f"measured threshold is between {br1['fail_max']:g} and {br1['ok_min']:g} kOhm at vb = {tag_8['vb']:g} V "
             f"and between {br08['fail_max']:g} and {br08['ok_min']:g} kOhm at vb = 0.8 V, so "
             f"{br08['fail_max']:g} to {br08['ok_min']:g} kOhm is the working range of the threshold. The "
             f"margined rule is conservative at vb = {tag_8['vb']:g} V, where {br1['ok_min']:g} kOhm already divides."),
        ],
        "devices": device_rows(net, m_8, r_8, tag_8["vb"]),
        "metrics": metrics_8,
    }
    design_with = {
        "description": [
            (f"Same topology with the sizing concept: multiplier m = {m_d} scales every device in parallel, load "
             f"R1 = R2 = {r_d:g} kOhm, input {f_d:g} GHz (design D). Stack rule (section Theory): the pull-down "
             f"stack resistance is 3 Ron/m = {stack(m_d):.2f} kOhm, the regeneration threshold 1.1 times that is "
             f"{thr_mid(m_d):.2f} kOhm (band {thr_lo(m_d):.2f} to {thr_hi(m_d):.2f} kOhm for the Ron range), and the "
             f"load {r_d:g} kOhm is above the band. The sizing check at {f_d:g} GHz and the {f_b:g} GHz point (design "
             f"B, m = {m_b}, R1 = R2 = {r_b:g} kOhm, reported in the other information section) use the same rule. The "
             f"tail device M7 is in the triode region: in the transient its drain voltage stays below Vdsat (see the "
             f"other information section)."),
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
        f"Virtuoso database read-back of the DLATCH of design D (results/gpdk045/virtuoso_dlatch_params_designD.txt): "
        f"R1 and R2 = {rb_r:g} kOhm; M1 to M6 w = {rb_mos['M1']['w']}, l = {rb_mos['M1']['l']}, m = {rb_mos['M1']['m']}; "
        f"M7 w = {rb_m7['w']}, l = {rb_m7['l']}, m = {rb_m7['m']}. These agree with Table 2, and with the W and L of "
        f"Table 1 (the netlist W and L)."
    )

    # ---------------------------------------------------------- narrative
    d_fail = sum_d["failing"]
    d_fail_text = (
        f"All {len(d_fail)} PVT failures of design D are at 125 C and 0.9 V."
        if d_fail and all(f["temp_C"] == 125 and abs(f["vdd_V"] - 0.9) < 1e-9 for f in d_fail)
        else f"Design D has {len(d_fail)} PVT failures (listed in the PVT table).")
    b_steps = nom_b["phase_steps_deg"].split(",")
    d_steps = nom_d["phase_steps_deg"].split(",")
    s8_steps = nom_8["phase_steps_deg"].split(",")
    q1_first_b = a_b["ck_to_q1_first_edge_delay_ps"]
    half_fail_b = 1e3 / (2.0 * sw_b["f_fail"])
    p1, p2 = pair_d[0].capitalize(), pair_d[1].capitalize()
    theory = [
        ("Topology. The divider follows Kuo et al. (References): four cascaded differential D-latches with "
         "alternating cross-connections Q1b to D2, Q2 to D3, Q3b to D4 and Q4 to D1b. Latches 2 and 3 have CK "
         "and CKb swapped. Each latch has a sampling pair M1 and M2, a positive-controlled switch M5, a hold pair "
         "M3 and M4, a negative-controlled switch M6, a tail M7 and loads R1 and R2. While CK is high a latch "
         "samples; while CK is low the hold pair regenerates the stored value. The ring connections make the eight "
         "outputs toggle in pairs at half the input frequency, spread around one period."),
        (f"Elmore estimate. In the paper's model the latch delay is t_pdf = t_pdr = (8C)(R/2) = 4RC, where C is the "
         f"gate (equal to diffusion) capacitance of a unit nMOS, the Q node carries (6 + 2)C = 8C, the turn-on "
         f"resistance R is twice the load R1 (R/2 = R1), and node b is grounded because M7 is on. The paper requires "
         f"T_CK/2 > 2 Td. C is not known here, but the node capacitance 8C is at least the {cl_ff:g} fF output load "
         f"C_L, so Td >= (8C)(R/2) >= R1 C_L. This is a lower bound, because device parasitics are neglected: "
         f"{td_d:.0f} ps for design D (R1 = {r_d:g} kOhm) and {td_b:.0f} ps for design B (R1 = {r_b:g} kOhm). At "
         f"{f_d:g} GHz (design D), 2 Td >= {2 * td_d:.0f} ps against T_CK/2 = {half_d:.0f} ps, a clear margin, so the "
         f"bound is met. At {f_b:g} GHz (design B), 2 Td >= {2 * td_b:.0f} ps against T_CK/2 = {half_b:.0f} ps, so "
         f"the bound is also met. Design B sits at its measured frequency limit: it divides up to "
         f"{sw_b['f_max']:g} GHz and fails at {sw_b['f_fail']:g} GHz, where T_CK/2 = {half_fail_b:.1f} ps. Its "
         f"measured CK-to-Q1 delay of {q1_first_b:.2f} ps is {q1_first_b / td_b:.1f} times the lower bound and "
         f"{q1_first_b / half_b:.0%} of T_CK/2, so the lower-bound estimate is optimistic at {f_b:g} GHz; the "
         f"condition is necessary but is not what alone decides division. The estimate is not compared with the "
         f"table delay, which is a different quantity (the CK edge to the next edge of any of the eight outputs, "
         f"not the paper's D-to-Q latch delay)."),
        (f"Stack resistance and regeneration. The output pull-down path is a stack of three series devices (M1, M5, "
         f"M7), so its resistance is about 3 Ron/m. Regeneration of the hold pair needs gm R1 > 1; the margin used "
         f"here is R1 >= 1.1 x (3 Ron/m). With Ron = {ron:g} kOhm (LEDGER.md) the unit stack is {stack(1):.2f} kOhm "
         f"and the margined threshold {thr_mid(1):.2f} kOhm, far above the paper-rule load of {r_u:g} kOhm, which is "
         f"why that circuit does not divide. The measured threshold of the unit-size circuit lies between "
         f"{br1['fail_max']:g} and {br1['ok_min']:g} kOhm at vb = {tag_8['vb']:g} V and between "
         f"{br08['fail_max']:g} and {br08['ok_min']:g} kOhm at vb = 0.8 V (unsized_baseline.tsv), which brackets both "
         f"the unmargined stack value and the margined one. For m = {m_d} the threshold is {thr_mid(m_d):.2f} kOhm "
         f"(band {thr_lo(m_d):.2f} to {thr_hi(m_d):.2f} kOhm), so design D at {r_d:g} kOhm passes, while design B at "
         f"{r_b:g} kOhm lies inside the band and its margin depends on the Ron value used. The recorded division "
         f"results in LEDGER.md agree with the margined rule for {ok_pairs} of {len(numeric)} numeric (m, R) pairs; "
         f"the rule is a guide, not an exact boundary. The paper's unit nMOS is W = {LITERATURE['unit_w_um']:g} um, "
         f"L = {LITERATURE['unit_l_nm']} nm (W/L = {LITERATURE['unit_w_um'] * 1e3 / LITERATURE['unit_l_nm']:.2f}); "
         f"the unit device here is {nm(net['sizes']['M1'][0])} / {nm(net['sizes']['M1'][1])} (W/L = "
         f"{float(net['sizes']['M1'][0][:-1]) / float(net['sizes']['M1'][1][:-1]):.2f}), the same shape."),
        (f"Phase-step law. Outputs come in pairs. In output-period degrees the phase of an edge pair that is "
         f"t_pair apart is a = 360 t_pair f_out = 180 t_pair f_in, and the steps between neighbouring outputs "
         f"alternate between a and 90 - a degrees. t_pair is measured in the raw files as the mean gap between the "
         f"rising edge of {p1} and the next rising edge of {p2}. At {f_d:g} GHz (design D) the steps are "
         f"{d_steps[0]} and {d_steps[1]} deg and t_pair = {tp_d:.2f} ps, so a = 180 x {tp_d:.2f} ps x {f_d:g} GHz = "
         f"{a_calc(tp_d, f_d):.2f} deg. At {f_b:g} GHz (design B) the steps are {b_steps[0]} and {b_steps[1]} deg and "
         f"t_pair = {tp_b:.2f} ps, so a = {a_calc(tp_b, f_b):.2f} deg. For the baseline U8k at {f_8:g} GHz the steps "
         f"are {s8_steps[0]} and {s8_steps[1]} deg with t_pair = {tp_8:.2f} ps (a = {a_calc(tp_8, f_8):.2f} deg). "
         f"Equal 45 deg steps need T_out = 8 t_pair, that is T_CK = 4 t_pair: {4 * tp_d:.1f} ps for D "
         f"(f_in = {1e3 / (4 * tp_d):.2f} GHz) and {4 * tp_b:.1f} ps for B (f_in = {1e3 / (4 * tp_b):.2f} GHz), "
         f"indicative values because t_pair itself depends on f_in. The phase error is therefore a property of each "
         f"design at a given f_in; in the frequency sweeps it falls as f_in rises and is small only near each "
         f"design's frequency limit. The paper's {LITERATURE['phase_err_deg']} deg is reproduced in magnitude only "
         f"by design B at {f_b:g} GHz."),
        (f"Delay and power definitions. Delay is the mean over CK rising edges of the time to the next rising edge "
         f"on any of the eight outputs. This differs from the delay of the first CK edge to Q1 alone: "
         f"{a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps for D against the table value {metrics_d['delay_ps']} ps. "
         f"Power is VDD times the mean supply current over whole output periods. PDP is power times delay (mW times "
         f"ps gives fJ). A division is accepted only when all eight outputs run at f_in/2 within 0.1 percent and "
         f"each swings at least {SWING_MIN_V:g} V."),
    ]

    tool_technology = [
        "Simulator: Cadence Spectre 12.1.0 (MMSIM121), run on a 32-bit CentOS 6.5 virtual machine. Layout and "
        "DRC tools in the flow: Virtuoso IC615 and Assura 4.1.",
        f"Evidence of the simulator runs: each raw file written by Spectre carries a header, for example D_1p4.raw: "
        f"Plotname \"{raw_plot}\", written {raw_date}. No terminal screenshot of the Spectre run itself is included.",
        "Process: Cadence GPDK045 v6.0, a 45 nm generic PDK. Device g45n1svt (Virtuoso cell nmos1v), a 1.0 V "
        "thin-oxide standard-Vt NMOS modelled with BSIM4. Corners tt, ff, ss, fs and sf from models/spectre/gpdk045.scs.",
        f"Sizes: unit transistor W = {nm(net['sizes']['M1'][0])}, L = {nm(net['sizes']['M1'][1])} for M1 to M6; M7 "
        f"W = {nm(net['sizes']['M7'][0])}, L = {nm(net['sizes']['M7'][1])}; the multiplier m scales every device "
        f"in parallel. W and L are from the netlist spectre/divider_gpdk45.scs; m, R, vb and f_in are per-run "
        f"parameter overrides recorded in each TSV tag (g_<f_in>G_<R>k_<vb>_<C_L>f_m<m>), not the netlist defaults.",
        f"Stimulus and conditions: VDD = {vdd_v:g} V with PVT at {pvt_vdds[0]:g} and {pvt_vdds[-1]:g} V; temperature "
        f"{net['temp_c']} C nominal; CK rise and fall {to_ps(net['params']['tr'])}; CKb is CK delayed by half a "
        f"period; tail bias vb = {vb_d:g} V; {to_ff(net['params']['cl'])} load on each of the eight outputs.",
        rb_text,
        f"Plots are generated by scripts from the Spectre results; the waveform and PVT figures are plots, not Virtuoso "
        f"screenshots, and each caption says so. The two circuit drawings (Figure 1 and Figure "
        f"{extra_no['ring']}) are generated by scripts/draw_gpdk45_circuits.py from spectre/divider_gpdk45.scs.",
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
        f"Frequency sweeps (fs_B, fs_D, fs_E). Design B (m = {m_b}, R = {r_b:g} kOhm) was swept from "
        f"{sw_b['f_lo']:g} to {sw_b['f_hi']:g} GHz: it divides at {', '.join(f'{x:g}' for x in sw_b['ok_list'])} GHz "
        f"and fails at {', '.join(f'{x:g}' for x in sw_b['fail_list'])} GHz. Design D (m = {m_d}, R = {r_d:g} kOhm) "
        f"was swept from {sw_d['f_lo']:g} to {sw_d['f_hi']:g} GHz: it divides at "
        f"{', '.join(f'{x:g}' for x in sw_d['ok_list'])} GHz and fails at "
        f"{', '.join(f'{x:g}' for x in sw_d['fail_list'])} GHz; {f_d:g} GHz also divides (Table 3), and "
        f"{f_d:g} to {sw_d['f_lo']:g} GHz was not swept. Design E (m = {tag_e['m']}, R = {tag_e['r_kohm']:g} kOhm) was "
        f"swept from {sw_e['f_lo']:g} to {sw_e['f_hi']:g} GHz: it divides at "
        f"{', '.join(f'{x:g}' for x in sw_e['ok_list'])} GHz and fails at "
        f"{', '.join(f'{x:g}' for x in sw_e['fail_list'])} GHz; {f_d:g} GHz also divides "
        f"(pvt_E, tt, {net['temp_c']} C, 1.0 V). The maximum phase-step error at the top of each dividing range is "
        f"{sw_b['err_max_f']:.2f} deg (B), {sw_d['err_max_f']:.2f} deg (D) and {sw_e['err_max_f']:.2f} deg (E); at the "
        f"bottom of the swept range it is {sw_b['err_min_f']:.2f}, {sw_d['err_min_f']:.2f} and {sw_e['err_min_f']:.2f} "
        f"deg. The error falls with input frequency in all three sweeps (Figure {extra_no['fsweep']}).")
    f_parts = "; ".join(
        f"m = {g['m']}, R = {g['r']:g} kOhm divides up to {g['f_max']:g} GHz ({g['err']:.2f} deg phase-step error "
        f"there)" + (f" and fails at {g['f_fail']:g} GHz" if g["f_fail"] else "") for g in sw_f)
    n_f = sum(g["n"] for g in sw_f)
    sweep_f_text = (f"Exploratory sweep fs_F ({n_f} points, not used for the tables): {f_parts}. The runs are "
                    f"single nominal points around the frequency limit of design B and were not run over PVT.")

    other_info = [
        (f"Layout: what was done (placement only). The layout was generated by the SKILL script "
         f"cadence/skill/build_layout_v2.il in Virtuoso 6.1.5 (IC615). The transistors in the layout are unit size: "
         f"one nmos1v pcell per device ({lay['n_mos']} single placements in layout_build_log.txt, each "
         f"{lay['bbox']} um wide), no multiplier. M1 to M6 have {lay['nf1']} fingers of {lay['fw_nm']:g} nm "
         f"({lay['w1_nm']:g} nm, L = {lay['l1_nm']:g} nm) and M7 has {lay['nf7']} fingers of {lay['fw_nm']:g} nm "
         f"({lay['w7_nm']:g} nm, L = {lay['l7_nm']:g} nm). This is the m = {m_8} sizing of Table 1; design D "
         f"(Table 2) needs {width_factor} times the width (m = {m_d}). The two poly resistors R1 and R2 (resnsnpoly, "
         f"segW {lay['r_w']} um, segL {lay['r_len']} um, {lay['r_rsh']} ohm/sq) give about {lay['r_target']:g} ohm "
         f"and are a placeholder: the simulated baseline uses {r_8:g} kOhm and design D {r_d:g} kOhm. The layout "
         f"therefore matches neither simulated design (its transistors are those of the m = {m_8} baseline, its "
         f"resistors are not), and a layout at m = {m_d} with the {r_d:g} kOhm resistor was not produced. The DLATCH "
         f"box is {lay['box_w']} x {lay['box_h']} um. divider_core places "
         + ", ".join(f"{x} {o}" for x, o in lay["place"])
         + f" with a {lay['gap']} um gap. The clock-star lengths ({lay['ck']} um each) are a computed Manhattan "
         f"distance from each clock pin to the array centre (LAYOUT_NOTES.md, section 7); no clock wire is drawn. "
         f"Figure {slot_no['layout_core']} shows the divider_core layout and Figure {extra_no['layout_dlatch']} the "
         f"DLATCH layout."),
        (f"Layout: Assura DRC (real result). Assura 4.1 DRC was run on the DLATCH layout only (divider_lib/DLATCH/layout, "
         f"gpdk045 assuraDRC.rul); divider_core was not run. The result is {drc_total} errors in {len(drc_rules)} rules "
         f"(Figure {extra_no['drc']}). Rule 220 psubstrate_StampErrorMult ({drc_count[220]}) and Rule 221 "
         f"psubstrate_StampErrorConnect ({drc_count[221]}) give {drc_stamp} substrate-stamp connectivity errors, because "
         f"no tap or substrate connection is routed. Rule 595 METAL1.A.1, Metal1 area must be at least {area_min:g} um^2 "
         f"({drc_count[595]}), gives {drc_metal} Metal1 minimum-area errors. The DRC summary lists the first {len(m595)} of these "
         f"markers; each is {w595:g} x {h595:g} um ({w595 * h595:.4f} um^2) at x {x595[0]:g} to {x595[1]:g} um and "
         f"y {y595[0]:g} to {y595[1]:g} um, inside the transistor rows. The coordinates indicate that the "
         f"{drc_metal} errors are isolated Metal1 contact pads, not the pin shapes: the script's pins are {lay['pin_w']:g} x {lay['pin_h']:g} um = {pin_area:.2f} um^2, which is above "
         f"the minimum. The {drc_count[221]} Rule 221 markers repeat at a {pitch221:g} um pitch, which is the device "
         f"pitch of the layout, so the substrate-stamp errors point at the unconnected integrated taps of the "
         f"pcells. The DLATCH layout is therefore not DRC clean."),
        ("Layout: what was not done. The layout is placement only. Intra-latch metal routing, vias, clock trunks and "
         "substrate taps or connections are not drawn. The layout screenshots show cell outlines, not filled mask "
         "geometry. LVS, parasitic extraction and post-layout simulation were not run, so the simulated results in "
         "this report are pre-layout results and the layout is not complete."),
        (f"Virtuoso connectivity check (results/gpdk045/core_connectivity_virtuoso.txt): the top-level connections of "
         f"{n_inst} DLATCH instances (XD1 to XD4) were compared pin by pin with spectre/divider_gpdk45.scs, giving "
         f"{len(mism)} mismatch{'es' if len(mism) != 1 else ''}"
         f"{' (' + ', '.join(mism) + ')' if mism else ''}. Schematic checks (schCheck errors/warnings, LEDGER.md): "
         f"DLATCH {schc['DLATCH']}, divider_core {schc['divider_core']}, tb_divider {schc['tb_divider']}."),
        (f"Second operating point, design B at {f_b:g} GHz: m = {m_b}, R1 = R2 = {r_b:g} kOhm, output "
         f"{num(nom_b['f_out_MHz']):.1f} MHz, power {num(nom_b['power_mW']):.4f} mW, delay "
         f"{num(nom_b['delay_ps']):.2f} ps, PDP {num(nom_b['pdp_fJ']):.3f} fJ, maximum phase-step error "
         f"{num(nom_b['max_phase_step_err_deg']):.2f} deg (steps {b_steps[0]} and {b_steps[1]} deg). Q1 swing "
         f"{a_b['q1_min_v']:.3f} to {a_b['q1_max_v']:.3f} V ({swing_b:.3f} V against the {SWING_MIN_V:g} V "
         f"criterion). The M7 tail voltage reaches {a_b['xd1_tail_max_v'] * 1e3:.1f} mV at most. B has the same M7 "
         f"W, L, multiplier and Vgs as design D and the same t = 0 operating point, so Vdsat is the same, "
         f"{vds_info['vdsat_v'] * 1e3:.1f} mV, and B's M7 is also in triode (Figure {extra_no['tail_b']}). The "
         f"metrics of this point are given here, not in Table 3; its PVT matrix is listed in Table 4 under the rows "
         f"labelled B6."),
        (f"Initial-condition operating point (the point written by the operating-point extraction, at t = 0 with CK "
         f"and CKb both low, so M5 and M6 are off and there is no tail current; it is not a bias point of the running "
         f"circuit). Paper-rule circuit: M7 {op_u['region']}, Vds = {op_u['vds_v'] * 1e9:.1f} nV, Ids = "
         f"{op_u['ids_a'] * 1e12:.1f} pA. Design D: M7 {op_d['region']}, Vds = {op_d['vds_v'] * 1e9:.1f} nV, Ids = "
         f"{op_d['ids_a'] * 1e12:.1f} pA. Design B: M7 {op_b['region']}, Vds = {op_b['vds_v'] * 1e9:.1f} nV, Ids = "
         f"{op_b['ids_a'] * 1e12:.1f} pA (the same as design D, because both designs have m = {m_d} and "
         f"vb = {vb_d:g} V and no tail current flows at t = 0). Vgs = {op_d['vg_v']:g} V in all three. The "
         f"triode conclusion below does not rest on this point but on the transient."),
        (f"Tail device M7 (honest finding). Vdsat is set by Vgs = {op_d['vg_v']:g} V, which is the same in the "
         f"transient as at t = 0: Vdsat = {vds_info['vdsat_v'] * 1e3:.1f} mV (Vth = {vds_info['vth_v'] * 1e3:.1f} mV; at "
         f"the t = 0 point gm = {vds_info['gm_ps']:.1f} pS and gds = {vds_info['gds_ms']:.3f} mS, Vds about "
         f"{op_d['vds_v'] * 1e9:.0f} nV). In the transient, V(XD1.tail) of design D stays between "
         f"{a_d['xd1_tail_min_v'] * 1e3:.1f} mV and {a_d['xd1_tail_max_v'] * 1e3:.1f} mV (XD2 reaches "
         f"{a_d['xd2_tail_max_v'] * 1e3:.1f} mV), and that of the baseline U8k between "
         f"{a_8['xd1_tail_min_v'] * 1e3:.1f} and {a_8['xd1_tail_max_v'] * 1e3:.1f} mV. Vds never reaches Vdsat, so "
         f"M7 operates in the triode region. The paper's tail is a saturated current source; this circuit's tail is "
         f"not, and the report states this deviation openly (see Figures {extra_no['tail_8']} and "
         f"{extra_no['tail_d']})."),
        sweeps_text,
        sweep_f_text,
        (f"PVT results. Design D at {f_d:g} GHz: {fail_text(sum_d)}. Design B at 1.4 GHz: {fail_text(sum_b1)}. "
         f"Design E (m = {tag_e['m']}, R = {tag_e['r_kohm']:g} kOhm) at 1.4 GHz: {fail_text(sum_e)}. Design B at "
         f"{f_b:g} GHz: {fail_text(sum_b6)}. The passing range for design D is power "
         f"{sum_d['passing_metrics']['power_mW']['min']:.3f} to {sum_d['passing_metrics']['power_mW']['max']:.3f} mW "
         f"and delay {sum_d['passing_metrics']['delay_ps']['min']:.2f} to "
         f"{sum_d['passing_metrics']['delay_ps']['max']:.2f} ps. The PVT tables list design D ({f_d:g} GHz) first and "
         f"design B ({f_b:g} GHz) second, with the design in the corner column. In Table 4 the ratio is f_in/f_out "
         f"(a division needs 2); a ratio of 0.5 means the outputs run at 2 f_in."),
        (f"Delay cross-check. The single-edge CK-to-Q1 delay in analysis.json is "
         f"{a_8['ck_to_q1_first_edge_delay_ps']:.2f} ps for U8k, {a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps for design D "
         f"and {a_b['ck_to_q1_first_edge_delay_ps']:.2f} ps for design B. That is a different quantity (first edge of "
         f"one output), so it is a cross-check only. The table delay is the mean over CK edges of the time to the next "
         f"edge of any of the eight outputs, which agrees with analysis.json to within 0.01 ps "
         f"({a_d['ck_to_any_output_mean_delay_ps']:.2f} ps for D). Q1 rise and fall times (10 to 90 percent) for D are "
         f"{a_d['q1_rise_10_90_ps']:.1f} ps and {a_d['q1_fall_10_90_ps']:.1f} ps."),
        (f"Power cross-check. The mean supply current of design D from analysis.json is "
         f"{a_d['supply_avg_ma_steady']:.5f} mA, against {num(nom_d['i_avg_mA']):.6f} mA in the TSV, within "
         f"{abs(num(nom_d['power_mW']) - a_d['supply_avg_ma_steady']) / num(nom_d['power_mW']):.3%}. The peak supply current "
         f"in steady state is {a_d['supply_peak_ma_steady']:.3f} mA (Figure {extra_no['supply']})."),
        (f"Comparison with the paper. Literature values from Kuo et al. (not re-measured here): "
         f"{LITERATURE['process']}, {LITERATURE['vdd_v']} V, {LITERATURE['f_in_ghz']} GHz input, "
         f"{LITERATURE['power_mw']} mW, phase error within {LITERATURE['phase_err_deg']} deg, core "
         f"{LITERATURE['core_um']} um^2. In this generic 45 nm PDK, design D at {f_d:g} GHz draws "
         f"{num_d('power_mW'):.4f} mW but its phase-step error is {num_d('max_phase_step_err_deg'):.2f} deg; "
         f"design B reaches {num(nom_b['max_phase_step_err_deg']):.2f} deg only at {f_b:g} GHz. The core area is not "
         f"measured here and the processes differ, so this report makes no claim of beating the paper."),
        (f"Figure numbering. Figures 1 to {len(slot_no)} are the named slots; the post-layout waveform slot holds a "
         f"statement that the simulation was not performed and has no figure number. Figures {EXTRA_FIG_START} "
         f"onwards are additional figures: the ring diagram (Figure {extra_no['ring']}), the non-dividing "
         f"paper-rule waveforms (Figure {extra_no['tran_paper']}), the {f_b:g} GHz waveforms (Figure "
         f"{extra_no['tran_b']}), phase steps (Figure {extra_no['phase']}), tail voltage (Figures "
         f"{extra_no['tail_8']}, {extra_no['tail_d']} and {extra_no['tail_b']}), supply current (Figure "
         f"{extra_no['supply']}), the frequency sweep (Figure {extra_no['fsweep']}) and the PVT plots for design D "
         f"and B (Figures {extra_no['pvt_dp_d']}, {extra_no['pvt_hm_b6']} and {extra_no['pvt_dp_b6']}), the "
         f"testbench schematic (Figure {extra_no['tb']}), the Virtuoso session log (Figure {extra_no['ciw']}), the "
         f"DLATCH layout (Figure {extra_no['layout_dlatch']}) and the Assura DRC tally (Figure {extra_no['drc']})."),
    ]

    conclusion = [
        (f"Both operating points work with the same topology and the stack rule. Design D at {f_d:g} GHz "
         f"(m = {m_d}, R = {r_d:g} kOhm) divides with {metrics_d['power_mw']} mW, {metrics_d['delay_ps']} ps delay, "
         f"{metrics_d['pdp_fj']} fJ PDP and a {metrics_d['max_phase_step_err_deg']} deg phase-step error, and passes "
         f"{sum_d['pass_count']} of {sum_d['total']} PVT points. Design B at {f_b:g} GHz (m = {m_b}, R = {r_b:g} kOhm) "
         f"divides with {num(nom_b['power_mW']):.4f} mW, {num(nom_b['delay_ps']):.2f} ps delay, "
         f"{num(nom_b['pdp_fJ']):.3f} fJ PDP and a {num(nom_b['max_phase_step_err_deg']):.2f} deg phase-step error, "
         f"and passes {sum_b6['pass_count']} of {sum_b6['total']} PVT points. Design B is the weaker point: its Q1 "
         f"swing is {swing_b:.3f} V ({a_b['q1_min_v']:.3f} to {a_b['q1_max_v']:.3f} V) against the {SWING_MIN_V:g} V "
         f"criterion, its tt, {b6_tt27_09['temp']} C, {b6_tt27_09['vdd']:g} V corner fails, and it fails at "
         f"{sw_b['f_fail']:g} GHz."),
        (f"Sizing against the baseline. Sizing{cmp_text.split(': sizing', 1)[1]}"),
        (f"The paper-rule circuit (m = {m_u}, R1 = Ron/2 = {r_u:g} kOhm) does not divide at {tag_u['f_ghz']:g} GHz, "
         f"which is consistent with the stack-resistance rule (its load is far below the {thr_mid(1):.2f} kOhm "
         f"threshold), and the R search puts the measured threshold of the unit-size circuit between "
         f"{br08['fail_max']:g} and {br08['ok_min']:g} kOhm (vb = 0.8 V) and between {br1['fail_max']:g} and "
         f"{br1['ok_min']:g} kOhm (vb = {tag_8['vb']:g} V)."),
        (f"Limits. The tail M7 operates in triode, not saturation, so the paper's tail model is not reproduced. The "
         f"phase-step error at {f_d:g} GHz ({metrics_d['max_phase_step_err_deg']} deg) is far above the paper's "
         f"{LITERATURE['phase_err_deg']} deg, and only design B at {f_b:g} GHz comes close "
         f"({num(nom_b['max_phase_step_err_deg']):.2f} deg). {d_fail_text} Design B, whose load lies inside the "
         f"regeneration band, passes fewer PVT points ({sum_b6['pass_count']} of {sum_b6['total']} at {f_b:g} GHz and "
         f"{sum_b1['pass_count']} of {sum_b1['total']} at 1.4 GHz)."),
        (f"Layout status: placement only, and not clean or complete. The divider_core (2x2 DLATCH placement) and the "
         f"DLATCH are placed but not routed, not extracted, not LVS-checked and not simulated after layout. The "
         f"transistors in the layout are unit size (m = {m_8}) and the resistors are a {lay['r_target']:g} ohm "
         f"placeholder, so the layout matches neither simulated design; a layout at m = {m_d} with the {r_d:g} kOhm "
         f"resistor was not produced. The DLATCH Assura DRC gives {drc_total} errors in {len(drc_rules)} rules "
         f"({drc_stamp} substrate-stamp connectivity, {drc_metal} Metal1 minimum area). Post-layout simulation was "
         f"not performed."),
    ]

    problems_faced = [
        "Spectre aborted with ERROR (VACOMP-1008): Cannot compile ahdlcmi module library, and then a segmentation "
        "fault, for the gate-resistance Verilog-A style sub-model inside the gpdk045 device.",
        "Cause: the Cadence VM is 32-bit CentOS 6.5, but the bundled perl (cdsPerl) and gcc are 64-bit and could not "
        "run, and no gcc was installed.",
        "The guest disk had only about 100 MB free, so a sweep failed with No space left on device.",
        f"The unit-size circuit with R1 = Ron/2 does not divide at 1, 1.4 or 2 GHz; a dividing unit-size baseline "
        f"needed a search over R.",
        f"The first division check counted false passes: outputs at 2 x f_in ({f_out_u_meas / 1e3:.1f} GHz for a "
        f"{tag_u['f_ghz']:g} GHz input) with only {fp_lo:.0f} to {fp_hi:.0f} mV of swing.",
        "The Spectre ASCII raw layout (first variable on the Variables line, several values per line) broke the first parser.",
        "The 125 C corners failed for the marginal sizing.",
        "The VM had no guest tools, so files were moved by virtual CD images and a virtual serial port with MD5 checks.",
        f"The phase error at {f_d:g} GHz is large ({metrics_d['max_phase_step_err_deg']} deg for design D), far from "
        f"the paper's {LITERATURE['phase_err_deg']} deg.",
        f"Layout not completed. The layout is placement only: intra-latch routing, vias, clock trunks and substrate "
        f"taps are not drawn, and the transistors are unit size (m = {m_8}). The DLATCH DRC gives {drc_total} errors "
        f"({drc_stamp} substrate-stamp, {drc_metal} Metal1 minimum area), LVS and extraction were not run, and "
        f"post-layout simulation was not performed.",
    ]
    problems_resolved = [
        "Installed gcc 4.4.7 and glibc-devel from the CentOS 6.5 vault RPMs, replaced the bundled perl wrapper by the "
        "system perl, and pointed the bundled gcc and ld symlinks at /usr/bin.",
        "The measured values were stored as TSV and JSON files (nominal, sweep, PVT and analysis files), so each "
        "number in this report is read from one of those files.",
        f"A dividing unit-size baseline was found by searching R ({n_search} Spectre runs, unsized_baseline.tsv); "
        f"the sizing concept then set the load from the stack-resistance rule, giving design D "
        f"({sum_d['pass_count']} of {sum_d['total']} PVT points).",
        f"The division test was made strict: all eight outputs at f_in/2 within 0.1 percent, each swinging at least "
        f"{SWING_MIN_V:g} V.",
        "The parsers were fixed for the Spectre ASCII raw layout, and the PVT and sweep results were checked against "
        "their summary files.",
        f"Two operating points were chosen: 1.4 GHz, the paper's input frequency, and {f_b:g} GHz, the point with the "
        f"smallest phase-step error. Each has its own PVT matrix.",
        "Assura batch DRC now runs from a run file. The file needs avParameters with ?inputLayout (\"df2\" "
        "\"divider_lib\") ?cellName ?viewName ?rulesFile ?workingDirectory ?runName ?avrpt t, and is run as "
        "`assura file.rsf` (no avDRC call). This gave the DLATCH DRC tally in the Layout text.",
    ]

    other_comment = [
        "The waveform and PVT figures are plots generated from Spectre data. They are labelled as plots, and no "
        "Cadence GUI screenshot is substituted for them.",
        "The Ron value and the recorded division pairs are taken from LEDGER.md. The Ron value is not in a separate "
        "output file, so the report cites the ledger.",
        "The two circuit drawings are generated from the gpdk045 Spectre netlist with the design D labels, so they "
        "agree with Tables 1 and 2. The earlier baseline drawings in report/figures are not used in this report.",
        "The paper's constants are literature values, and the title-page register and name fields are left blank by design.",
    ]

    sch_heading, sch_paras, sch_evidence = read_schematic_section()
    schematic_sim = {
        "heading": sch_heading,
        "paragraphs": sch_paras,
        "figure": None,  # the testbench schematic is already shown as an extra figure
        "figure_ref": f"The testbench schematic that was simulated is shown in Figure {extra_no['tb']}.",
    }
    references = [
        f"{LITERATURE['authors']}, \"A Compact Multiphase Divide-by-Two CMOS Frequency Divider,\" IEEE Microw. "
        f"Wireless Technol. Lett., vol. {paper['volume']}, no. {paper['issue']}, pp. {paper['pages']}, "
        f"{paper['date']}, doi: {paper['doi']}.",
        "Cadence Design Systems, Cadence GPDK045 v6.0 documentation (45 nm generic process design kit).",
        "Cadence Design Systems, Spectre Circuit Simulator Reference, MMSIM 12.1.",
    ] + [f"Evidence file: {rel}" for rel in sch_evidence]

    # ---------------------------------------------------------- Table 3 proof column and notes
    fn = extra_no
    values_proof = {
        "power_mw": f"Fig. {fn['supply']} (supply current, both columns)",
        "delay_ps": "no figure: analysis.json (ck_to_any_output_mean_delay_ps), see note",
        "pdp_fj": "power x delay (rows above)",
        "f_in_ghz": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "f_out_mhz": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "max_phase_step_err_deg": f"Fig. {fn['phase']}",
        "swing_v": f"Fig. {slot_no['tran_8']} (without), Fig. {slot_no['tran_d']} (with)",
        "sat": f"Fig. {fn['tail_8']} (without), Fig. {fn['tail_d']} (with)",
    }
    values_notes = [
        (f"Notes. Without sizing = the dividing unit-size baseline U8k (m = {m_8}, R = {r_8:g} kOhm, vb = "
         f"{tag_8['vb']:g} V). The paper-rule circuit (m = {m_u}, R = {r_u:g} kOhm) does not divide: supply power "
         f"{p_u_mw:.3f} mW, delay, PDP and phase error not defined (Figure {fn['tran_paper']}). Delay = mean over CK "
         f"rising edges of the time to the next rising edge of any of the eight outputs; the CK-to-Q1 first-edge "
         f"delay is {a_8['ck_to_q1_first_edge_delay_ps']:.2f} ps (U8k) and {a_d['ck_to_q1_first_edge_delay_ps']:.2f} ps "
         f"(D). Vds = largest V(XD1.tail) in the transient; Vdsat is the value extracted for design D (same M7 W, L "
         f"and Vgs, used for both columns).")]

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
