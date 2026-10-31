#!/usr/bin/env python3
"""Build report/Local_Simulation_Report.docx and report/figures/*.png.

Re-runnable. Reads (never writes) the project sources:
  spice/divider_baseline_cal.cir, spice/divider_baseline.cir, spice/models/cmos180.mod,
  results/metrics_baseline.json, results/pvt_summary_table.csv, results/baseline_cal_tran.txt,
  results/plots/*.png (embedded as they are).
Schematic figures are drawn from the parsed netlist; the netlist connectivity is asserted
against the expected topology before anything is drawn.
Runs scripts/validate.py (read-only checks) and pastes its real output into the report.
Does NOT run ngspice and does NOT re-run the pipeline scripts.

Division-search values (Table 4) are constants below: they were supplied from local ngspice
runs and are not stored in any file under results/.

Usage (venv with python-docx, matplotlib, numpy):
    <venv>/bin/python scripts/build_local_report.py
"""
import csv
import json
import os
import pathlib
import platform
import subprocess
import sys
import textwrap
from importlib import metadata

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "report"
FIG_DIR = REPORT / "figures"
OUT_DOCX = REPORT / "Local_Simulation_Report.docx"
CAL_CIR = ROOT / "spice" / "divider_baseline_cal.cir"
ORIG_CIR = ROOT / "spice" / "divider_baseline.cir"
MODEL = ROOT / "spice" / "models" / "cmos180.mod"
METRICS = ROOT / "results" / "metrics_baseline.json"
PVT_CSV = ROOT / "results" / "pvt_summary_table.csv"
TRAN = ROOT / "results" / "baseline_cal_tran.txt"
PLOTS = ROOT / "results" / "plots"
VALIDATE = ROOT / "scripts" / "validate.py"
FIG_DIR.mkdir(parents=True, exist_ok=True)

INK = "#1f2933"
RED_NET = "#b42318"
BLUE = "#2b6cb0"
ORANGE = "#c05621"
GREEN = "#2f855a"
GREY = "#6b7280"
CK_FILL = "#dbeafe"
CKB_FILL = "#fde7d3"
FAIL_FILL = "F8D7DA"
HDR_FILL = "D9E2F3"
NOTE_FILL = "FFF4E5"

F_IN_MHZ = 1400.0

# Division search (Table 4). Values as supplied from the local ngspice runs.
DIVISION_SEARCH = [
    ("Original netlist as written (no .ic)", "1.5k", "0.9 V", "none",
     "No division: Q and Qb of every latch sit at the same voltage (1.64 to 1.81 V)"),
    ("Original + .ic", "1.5k", "0.9 V", "none", "No division (same)"),
    ("Bias sweep", "1.5k", "1.0, 1.2, 1.4, 1.6 V", "none", "No division at any bias"),
    ("R sweep", "3k, 5k, 8k", "0.9 / 1.2 V", "none",
     "8k at 0.9 V and 5k at 1.2 V: outputs toggle at 1426-1451 MHz (ratio 0.96-0.98, following "
     "the clock, not dividing); 3k: no toggling"),
    ("Calibrated, load 10 fF", "5k", "1.2 V", "10 fF", "f_out 1451.9 MHz, ratio 0.964: not dividing"),
    ("Calibrated, load 30 fF", "5k", "1.2 V", "30 fF",
     "f_out 700.0 MHz, ratio 2.000: DIVIDES (chosen operating point)"),
    ("Calibrated, load 40 fF", "5k", "1.2 V", "40 fF", "983.4 MHz, ratio 1.424: fails"),
    ("Calibrated, load 50 fF", "5k", "1.2 V", "50 fF", "452.1 MHz, ratio 3.097: fails"),
    ("Calibrated, load 60 fF", "5k", "1.2 V", "60 fF", "233.3 MHz, ratio 6.000: fails"),
    ("Calibrated, load 80 fF", "5k", "1.2 V", "80 fF", "337.1 MHz, ratio 4.153: fails"),
]
SWEEP = [  # (load fF, f_out MHz, ratio) from the calibrated rows of DIVISION_SEARCH
    (10, 1451.9, 0.964), (30, 700.0, 2.000), (40, 983.4, 1.424),
    (50, 452.1, 3.097), (60, 233.3, 6.000), (80, 337.1, 4.153),
]

EXP_MOS = {  # name: (drain, gate, source, bulk) from the brief, checked against the netlist
    "M1": ("Q", "D", "xs", "xs"), "M2": ("Qb", "Db", "xs", "xs"),
    "M5": ("xs", "CK", "tail", "tail"), "M3": ("Q", "Qb", "xh", "xh"),
    "M4": ("Qb", "Q", "xh", "xh"), "M6": ("xh", "CKb", "tail", "tail"),
    "M7": ("tail", "nbias", "0", "0"),
}
EXP_XD = {  # latch: (D, Db, CK, CKb, Q, Qb) nets
    "XD1": ("Q4b", "Q4", "CK", "CKb", "Q1", "Q1b"),
    "XD2": ("Q1b", "Q1", "CKb", "CK", "Q2", "Q2b"),
    "XD3": ("Q2", "Q2b", "CKb", "CK", "Q3", "Q3b"),
    "XD4": ("Q3b", "Q3", "CK", "CKb", "Q4", "Q4b"),
}
EXP_EDGES = {  # (source latch, source pin, dest latch, dest pin)
    ("XD1", "Qb", "XD2", "D"), ("XD1", "Q", "XD2", "Db"),
    ("XD2", "Q", "XD3", "D"), ("XD2", "Qb", "XD3", "Db"),
    ("XD3", "Qb", "XD4", "D"), ("XD3", "Q", "XD4", "Db"),
    ("XD4", "Qb", "XD1", "D"), ("XD4", "Q", "XD1", "Db"),
}

# Pin positions on each latch box: fraction along the side (0..1, left->right or bottom->top).
SIDE = {
    "XD1": dict(inp="bottom", out="right", clk="top"),
    "XD2": dict(inp="left", out="bottom", clk="top"),
    "XD3": dict(inp="top", out="left", clk="right"),
    "XD4": dict(inp="right", out="top", clk="bottom"),
}
PIN_FRAC = {
    "XD1": {"Q": 0.7, "Qb": 0.3, "D": 0.3, "Db": 0.7, "CK": 0.3, "CKb": 0.7},
    "XD2": {"Db": 0.7, "D": 0.3, "Q": 0.3, "Qb": 0.7, "CK": 0.3, "CKb": 0.7},
    "XD3": {"D": 0.3, "Db": 0.7, "Q": 0.7, "Qb": 0.3, "CK": 0.3, "CKb": 0.7},
    "XD4": {"Db": 0.7, "D": 0.3, "Qb": 0.3, "Q": 0.7, "CK": 0.3, "CKb": 0.7},
}


# ----------------------------------------------------------------------------- netlist parsing
def parse_netlist(path):
    """Parse the SPICE subset used by the divider decks. Comments and the .control block are skipped."""
    info = {"subckts": {}, "mos": {}, "res": {}, "instances": {}, "caps": {},
            "sources": {}, "directives": []}
    cur = None
    in_ctrl = False
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("*"):
            continue
        tok = s.split()
        k = tok[0].lower()
        if k == ".control":
            in_ctrl = True
            continue
        if k == ".endc":
            in_ctrl = False
            continue
        if in_ctrl:
            continue
        if k == ".subckt":
            cur = tok[1]
            info["subckts"][cur] = {"pins": tok[2:], "mos": {}, "res": {}}
            continue
        if k == ".ends":
            cur = None
            continue
        if k.startswith("."):
            info["directives"].append(" ".join(tok))
            continue
        if cur is not None:
            params = dict(x.split("=", 1) for x in tok if "=" in x)
            if tok[0][0] in "Mm":
                info["subckts"][cur]["mos"][tok[0]] = dict(
                    d=tok[1], g=tok[2], s=tok[3], b=tok[4], model=tok[5],
                    W=params["W"], L=params["L"])
            elif tok[0][0] in "Rr":
                info["subckts"][cur]["res"][tok[0]] = dict(n1=tok[1], n2=tok[2], value=tok[3])
            continue
        if tok[0][0] in "Xx":
            info["instances"][tok[0]] = (tok[-1], tok[1:-1])
        elif tok[0][:2].lower() == "cl":
            info["caps"][tok[0]] = dict(n1=tok[1], n2=tok[2], value=tok[3])
        elif tok[0][0] in "Vv":
            info["sources"][tok[0]] = dict(n1=tok[1], n2=tok[2], spec=" ".join(tok[3:]))
    return info


def check_netlist(cal, orig):
    """Assert the calibrated netlist has the expected topology before anything is drawn."""
    lat = cal["subckts"]["DLATCH"]
    assert lat["pins"] == ["D", "Db", "CK", "CKb", "Q", "Qb", "VDD"], lat["pins"]
    assert set(lat["mos"]) == set(EXP_MOS) and len(lat["mos"]) == 7
    for name, exp in EXP_MOS.items():
        m = lat["mos"][name]
        got = (m["d"], m["g"], m["s"], m["b"])
        assert got == exp, f"{name}: netlist {got} != expected {exp}"
        assert m["model"] == "nmos"
    for name in ("M1", "M2", "M3", "M4", "M5", "M6"):
        assert (lat["mos"][name]["W"], lat["mos"][name]["L"]) == ("0.9u", "0.18u")
    assert (lat["mos"]["M7"]["W"], lat["mos"]["M7"]["L"]) == ("1.8u", "0.36u")
    assert lat["res"]["R1"] == dict(n1="VDD", n2="Q", value="5k")
    assert lat["res"]["R2"] == dict(n1="VDD", n2="Qb", value="5k")
    assert set(cal["instances"]) == set(EXP_XD)
    for x, (sub, nodes) in cal["instances"].items():
        assert sub == "DLATCH" and len(nodes) == 7, (x, sub, nodes)
        assert tuple(nodes[:6]) == EXP_XD[x], (x, nodes)
        assert nodes[6] == "Vdd"
    # ring: every latch input that is another latch's output
    out_map = {}
    for x, (_, nodes) in cal["instances"].items():
        pins = dict(zip(lat["pins"], nodes))
        out_map[pins["Q"]] = (x, "Q")
        out_map[pins["Qb"]] = (x, "Qb")
    edges = set()
    for x, (_, nodes) in cal["instances"].items():
        pins = dict(zip(lat["pins"], nodes))
        for ip in ("D", "Db"):
            if pins[ip] in out_map:
                sx, sp = out_map[pins[ip]]
                edges.add((sx, sp, x, ip))
    assert edges == EXP_EDGES, edges ^ EXP_EDGES
    assert len(cal["caps"]) == 8 and all(c["value"] == "30f" and c["n2"] == "0" for c in cal["caps"].values())
    assert cal["sources"]["Vbias"]["spec"] == "1.2"
    assert orig["sources"]["Vbias"]["spec"] == "0.9"
    assert orig["subckts"]["DLATCH"]["res"]["R1"]["value"] == "1.5k"
    assert not orig["caps"] and len(cal["caps"]) == 8
    for m_name, m in orig["subckts"]["DLATCH"]["mos"].items():
        c = cal["subckts"]["DLATCH"]["mos"][m_name]
        assert (m["d"], m["g"], m["s"], m["b"], m["W"], m["L"]) == (c["d"], c["g"], c["s"], c["b"], c["W"], c["L"])


def ctype(cal, x):
    return "CK" if cal["instances"][x][1][2] == "CK" else "CKb"


# ----------------------------------------------------------------------------- figures
def net_color(n):
    if n.lower() == "vdd":
        return RED_NET
    if n in ("CK", "CKb"):
        return BLUE
    if n == "nbias":
        return GREEN
    return INK


def fig_latch(cal, path):
    lat = cal["subckts"]["DLATCH"]
    M = lat["mos"]
    R = lat["res"]
    fig, ax = plt.subplots(figsize=(13, 9.3), dpi=300)
    ax.set_xlim(0.0, 13.0)
    ax.set_ylim(-0.75, 8.5)
    ax.set_aspect("equal")
    ax.axis("off")

    def L(xs, ys, c=INK, lw=1.2):
        ax.plot(xs, ys, color=c, lw=lw, solid_capstyle="round", solid_joinstyle="round")

    def dot(x, y):
        ax.plot([x], [y], "o", color=INK, ms=3.5)

    def T(x, y, s, c=INK, ha="left", va="center", size=9, weight="normal"):
        ax.text(x, y, s, color=c, ha=ha, va=va, fontsize=size, fontweight=weight)

    def nmos(name, xc, yc, drain_end):
        m = M[name]
        gx = xc - 0.12
        L([gx, gx], [yc - 0.42, yc + 0.42])
        for y0, y1 in [(yc + 0.36, yc + 0.13), (yc + 0.08, yc - 0.08), (yc - 0.13, yc - 0.36)]:
            L([xc, xc], [y0, y1])
        L([gx, xc - 0.6], [yc, yc])
        L([xc, xc + 0.25, xc + 0.25], [yc + 0.36, yc + 0.36, drain_end])
        L([xc, xc + 0.25, xc + 0.25], [yc - 0.36, yc - 0.36, yc - 0.8])
        T(xc - 0.7, yc - 0.45, f"{name} NMOS\nW={m['W']}  L={m['L']}", ha="right", va="top", size=8)
        T(xc - 0.66, yc, m["g"], net_color(m["g"]), ha="right", size=9, weight="bold")
        return m

    VDD_Y, QB_Y = 7.7, 6.05
    # layout: name -> (x centre, y centre); drain-end y set by whether the drain is an output node
    LAYOUT = {"M1": (2.5, 5.0), "M3": (5.3, 5.0), "M4": (7.7, 5.0), "M2": (10.5, 5.0),
              "M5": (2.5, 2.6), "M6": (7.7, 2.6), "M7": (5.0, 0.6)}
    ends = {}
    for name, (xc, yc) in LAYOUT.items():
        drain = M[name]["d"]
        ends[name] = yc + 1.05 if drain in ("Q", "Qb") else yc + 0.8
        nmos(name, xc, yc, ends[name])
    # structural assertions: the drawn wires must join the nets the netlist names
    assert M["M1"]["d"] == M["M3"]["d"] == "Q" and M["M4"]["d"] == M["M2"]["d"] == "Qb"
    assert M["M1"]["s"] == M["M2"]["s"] == M["M5"]["d"] == "xs"
    assert M["M3"]["s"] == M["M4"]["s"] == M["M6"]["d"] == "xh"
    assert M["M5"]["s"] == M["M6"]["s"] == M["M7"]["d"] == "tail"
    assert M["M7"]["s"] == "0"

    # supply rail and load resistors (R1: VDD->Q, R2: VDD->Qb)
    L([2.75, 10.75], [VDD_Y, VDD_Y], RED_NET)
    T(2.6, VDD_Y + 0.12, "VDD", RED_NET, ha="right", weight="bold")
    for x, name, out_y in ((2.75, "R1", "Q"), (10.75, "R2", "Qb")):
        assert R[name]["n1"] == "VDD" and R[name]["n2"] == out_y
        L([x, x], [VDD_Y, 7.25])
        ax.add_patch(Rectangle((x - 0.15, 6.45), 0.3, 0.8, fill=False, ec=INK, lw=1.2))
        L([x, x], [6.45, QB_Y])
        T(x + 0.25, 6.85, f"{name} = {R[name]['value']}  (VDD to {out_y})", size=9)
        dot(x, QB_Y)
    # output nodes
    L([2.75, 5.55], [QB_Y, QB_Y]); dot(5.55, QB_Y)
    L([7.95, 10.75], [QB_Y, QB_Y]); dot(7.95, QB_Y)
    T(4.15, QB_Y + 0.14, "Q", ha="center", weight="bold")
    T(9.35, QB_Y + 0.14, "Qb", ha="center", weight="bold")
    # xs (sampling sources + M5 drain) and xh (hold sources + M6 drain)
    L([2.75, 2.75], [4.2, 3.4])
    T(2.9, 3.8, "xs", weight="bold")
    T(10.9, 4.2, "xs", weight="bold")
    L([7.95, 7.95], [4.2, 3.4])
    T(8.1, 3.8, "xh", weight="bold")
    T(5.45, 4.2, "xh", ha="right", weight="bold")
    # tail node: M5/M6 sources, M7 drain
    L([2.75, 2.75, 7.95, 7.95], [1.8, 1.4, 1.4, 1.8])
    L([5.25, 5.25], [1.4, 1.4]); dot(5.25, 1.4)
    T(3.4, 1.52, "tail", weight="bold")
    # ground for M7 source
    L([5.25, 5.25], [-0.2, -0.3])
    L([5.05, 5.45], [-0.3, -0.3]); L([5.13, 5.37], [-0.38, -0.38]); L([5.21, 5.29], [-0.46, -0.46])
    T(5.6, -0.4, "0 (GND)", weight="bold")

    T(0.2, 8.3, "One DLATCH subcircuit, transistor level (drawn from spice/divider_baseline_cal.cir)",
      size=10, weight="bold")
    T(0.2, -0.55,
      "Net-name labels: identical names are the same node. Bulk tied to source for M1-M6 and to 0 for M7 "
      "(as in the netlist).\nDevice sizes: W/L from the netlist; R values from the netlist (5k).",
      size=7.5, c=GREY, va="top")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_ring(cal, path):
    lat = cal["subckts"]["DLATCH"]
    W, H = 3.2, 2.4
    BOX = {"XD1": (0.0, 4.2), "XD2": (5.5, 4.2), "XD3": (5.5, 0.0), "XD4": (0.0, 0.0)}
    latch = {x: dict(zip(lat["pins"], nodes)) for x, (_, nodes) in cal["instances"].items()}

    def ppos(x, side, frac):
        bx, by = BOX[x]
        return {"top": (bx + frac * W, by + H), "bottom": (bx + frac * W, by),
                "left": (bx, by + frac * H), "right": (bx + W, by + frac * H)}[side]

    fig, ax = plt.subplots(figsize=(11.5, 8.9), dpi=300)
    ax.set_xlim(-1.1, 10.4)
    ax.set_ylim(-1.1, 7.7)
    ax.set_aspect("equal")
    ax.axis("off")

    for x in BOX:
        bx, by = BOX[x]
        kind = ctype(cal, x)
        ax.add_patch(Rectangle((bx, by), W, H, facecolor=CK_FILL if kind == "CK" else CKB_FILL,
                               edgecolor=BLUE if kind == "CK" else ORANGE, lw=1.6))
        ax.text(bx + W / 2, by + H / 2 + 0.1, f"{x}", ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(bx + W / 2, by + H / 2 - 0.25,
                f"DLATCH, CK pin on net {kind}\nR1 = R2 = {lat['res']['R1']['value']} to VDD\n"
                f"7 NMOS, W/L {lat['mos']['M1']['W']}/{lat['mos']['M1']['L']} (M7 {lat['mos']['M7']['W']}/{lat['mos']['M7']['L']})",
                ha="center", va="top", fontsize=7.5, color=INK)
        # pin names inside the box and their net names outside
        for pin in ("D", "Db", "Q", "Qb", "CK", "CKb"):
            side = SIDE[x]["inp"] if pin in ("D", "Db") else (SIDE[x]["out"] if pin in ("Q", "Qb") else SIDE[x]["clk"])
            px, py = ppos(x, side, PIN_FRAC[x][pin])
            ax.plot([px], [py], "o", color=INK, ms=3)
            inset = {"top": (px, py - 0.1, "center", "top"), "bottom": (px, py + 0.1, "center", "bottom"),
                     "left": (px + 0.1, py, "left", "center"), "right": (px - 0.1, py, "right", "center")}[side]
            ax.text(inset[0], inset[1], pin, ha=inset[2], va=inset[3], fontsize=8, fontweight="bold",
                    color=INK)

    # clock pins: stubs to the global clock nets
    for x in BOX:
        side = SIDE[x]["clk"]
        for pin in ("CK", "CKb"):
            net = latch[x][pin]
            assert net in ("CK", "CKb")
            px, py = ppos(x, side, PIN_FRAC[x][pin])
            dx, dy = {"top": (0, 0.45), "bottom": (0, -0.45), "right": (0.45, 0), "left": (-0.45, 0)}[side]
            ax.plot([px, px + dx], [py, py + dy], color=net_color(net), lw=1.4)
            tx, ty = px + dx * 1.1, py + dy * 1.1
            ha, va = ("center", "bottom") if side == "top" else (("center", "top") if side == "bottom" else ("left", "center"))
            ax.text(tx, ty, net, color=net_color(net), ha=ha, va=va, fontsize=9, fontweight="bold")

    # data links: each output drives the input that carries its net
    for (sx, sp, dx_, dp) in EXP_EDGES:
        assert latch[sx][sp] == latch[dx_][dp], (sx, sp, dx_, dp)
        s_side, d_side = SIDE[sx]["out"], SIDE[dx_]["inp"]
        ps = ppos(sx, s_side, PIN_FRAC[sx][sp])
        pd = ppos(dx_, d_side, PIN_FRAC[dx_][dp])
        if s_side in ("left", "right"):
            xm = (ps[0] + pd[0]) / 2
            pts = [ps, (xm, ps[1]), (xm, pd[1]), pd]
        else:
            ym = (ps[1] + pd[1]) / 2
            pts = [ps, (ps[0], ym), (pd[0], ym), pd]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=INK, lw=1.2)
        net = latch[sx][sp]
        lab = {"right": (ps[0] + 0.06, ps[1] + 0.07, "left", "bottom"),
               "left": (ps[0] - 0.06, ps[1] + 0.07, "right", "bottom"),
               "top": (ps[0], ps[1] + 0.08, "center", "bottom"),
               "bottom": (ps[0], ps[1] - 0.08, "center", "top")}[s_side]
        ax.text(lab[0], lab[1], net, ha=lab[2], va=lab[3], fontsize=9, fontweight="bold", color=RED_NET)

    ax.legend(handles=[
        Patch(facecolor=CK_FILL, edgecolor=BLUE, label="latch with CK pin on net CK"),
        Patch(facecolor=CKB_FILL, edgecolor=ORANGE, label="latch with CK pin on net CKb (clock swapped)"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=2, fontsize=8, frameon=False)
    ax.text(-1.0, 7.5, "Ring: XD1 -> XD2 -> XD3 -> XD4 -> XD1. Red labels = net driven by the source latch.",
            fontsize=8, color=GREY, va="top")
    ax.text(-1.0, -1.0, "Each output node (Q1, Q1b ... Q4b) also has a 30 fF capacitor to ground (Cl1 ... Cl4b, not drawn). "
            "VDD pins are on net Vdd.", fontsize=7.5, color=GREY)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def load_tran():
    names = open(TRAN).readline().split()
    d = np.loadtxt(TRAN, skiprows=1)
    t = d[:, 0] * 1e9
    cols = {n.lower(): d[:, i + 1] for i, n in enumerate(names[1:])}
    return t, cols


def rising_times(t, x, lo, hi, mid):
    idx = np.where((x[:-1] < mid) & (x[1:] >= mid) & (t[:-1] >= lo) & (t[1:] <= hi))[0]
    return t[idx] + (mid - x[idx]) * (t[idx + 1] - t[idx]) / (x[idx + 1] - x[idx])


def fig_waveform(metrics, path):
    t, c = load_tran()
    late = t > 10.0
    lo_t, hi_t = 14.0, 20.0
    sig = {}
    for n in ("v(ck)", "v(q1)", "v(q1b)"):
        x = c[n]
        mid = (x[late].min() + x[late].max()) / 2
        sig[n] = rising_times(t, x, lo_t, hi_t, mid)
    ck, q1 = sig["v(ck)"], sig["v(q1)"]
    T_in = float(np.mean(np.diff(ck)))           # ns
    T_out = float(np.mean(np.diff(q1)))          # ns
    f_in_meas = 1.0 / T_in                       # GHz
    f_out_meas = 1000.0 / T_out                  # MHz
    assert abs(f_in_meas - metrics["f_in_ghz"]) / metrics["f_in_ghz"] < 1e-3, (f_in_meas, metrics["f_in_ghz"])
    assert abs(f_out_meas - metrics["f_out_mhz"]) / metrics["f_out_mhz"] < 1e-3, (f_out_meas, metrics["f_out_mhz"])
    assert len(q1) >= 4 and len(ck) >= 6

    fig, axs = plt.subplots(3, 1, figsize=(9, 6.6), dpi=300, sharex=True)
    rows = [("v(ck)", "CK (V)", BLUE), ("v(q1)", "Q1 (V)", RED_NET), ("v(q1b)", "Q1b (V)", GREEN)]
    for ax, (n, lab, col) in zip(axs, rows):
        m = (t >= lo_t) & (t <= hi_t)
        ax.plot(t[m], c[n][m], color=col, lw=1.3)
        ax.set_ylim(-0.2, 2.3)
        ax.set_ylabel(lab)
        ax.grid(alpha=0.3)
        for e in q1:
            ax.axvline(e, color=GREY, ls=":", lw=0.9)
    yA = 2.0
    axs[0].annotate("", xy=(ck[1], yA), xytext=(ck[0], yA), arrowprops=dict(arrowstyle="<->", color=INK))
    axs[0].text((ck[0] + ck[1]) / 2, yA + 0.08, f"T_CK = {T_in * 1000:.1f} ps", ha="center", fontsize=8)
    axs[1].annotate("", xy=(q1[1], yA), xytext=(q1[0], yA), arrowprops=dict(arrowstyle="<->", color=INK))
    axs[1].text((q1[0] + q1[1]) / 2, yA + 0.08, f"T_out = {T_out * 1000:.1f} ps = 2 x T_CK", ha="center", fontsize=8)
    axs[2].set_xlabel("time (ns)")
    axs[2].set_xlim(lo_t, hi_t)
    fig.suptitle("Calibrated baseline, TT / 27 C / 1.8 V: CK, Q1 and Q1b, 14-20 ns (dotted: Q1 rising edges)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return T_in * 1000.0, T_out * 1000.0, f_in_meas, f_out_meas


def fig_division(path):
    for load, f, r in SWEEP:
        assert abs(f * r - F_IN_MHZ) < 2.0, (load, f, r)     # f_out * ratio must equal f_in
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=300)
    loads = [s[0] for s in SWEEP]
    fo = [s[1] for s in SWEEP]
    rat = [s[2] for s in SWEEP]
    cols = [GREEN if abs(r - 2.0) < 0.01 else "#9ca3af" for r in rat]
    xs = np.arange(len(loads))
    a1.bar(xs, fo, color=cols, edgecolor=INK, lw=0.6)
    for xi, f, r in zip(xs, fo, rat):
        a1.text(xi, f + 25, f"ratio\n{r:.3f}", ha="center", va="bottom", fontsize=7)
    a1.axhline(F_IN_MHZ, color=INK, ls="--", lw=0.9)
    a1.text(len(loads) - 0.5, F_IN_MHZ + 15, "f_in = 1400 MHz", ha="right", fontsize=7)
    a1.axhline(F_IN_MHZ / 2, color=GREEN, ls=":", lw=0.9)
    a1.text(len(loads) - 0.5, F_IN_MHZ / 2 + 15, "f_in / 2", ha="right", fontsize=7, color=GREEN)
    a1.set_xticks(xs)
    a1.set_xticklabels([f"{l} fF" for l in loads], fontsize=8)
    a1.set_ylabel("output frequency (MHz)")
    a1.set_ylim(0, 1700)
    a1.set_title("Output frequency vs load (5k, 1.2 V)", fontsize=9)
    a1.grid(axis="y", alpha=0.3)

    a2.plot(loads, rat, "o-", color=INK, ms=5, lw=1.1)
    a2.plot([30], [2.0], "o", color=GREEN, ms=9)
    a2.axhline(2.0, color=GREEN, ls="--", lw=0.9)
    a2.text(78, 2.12, "target ratio 2 (divides)", ha="right", fontsize=7, color=GREEN)
    a2.axhline(1.0, color=GREY, ls=":", lw=0.9)
    a2.text(78, 1.12, "ratio 1 (follows clock)", ha="right", fontsize=7, color=GREY)
    for lo_, r_ in zip(loads, rat):
        a2.annotate(f"{r_:.3f}", (lo_, r_), textcoords="offset points", xytext=(4, 4), fontsize=7)
    a2.set_xlabel("output load (fF)")
    a2.set_ylabel("ratio f_in / f_out")
    a2.set_title("Division ratio vs load (calibrated)", fontsize=9)
    a2.set_xlim(0, 90)
    a2.set_ylim(0, 7)
    a2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------------- docx helpers
def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_cell(cell, text, size=9, bold=False, fill=None, align=None, mono=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    if align:
        p.alignment = align
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.bold = bold
    if mono:
        run.font.name = "Courier New"
    if fill:
        shade(cell, fill)


def add_table(doc, header, rows, widths_cm, size=9, fills=None, num_cols=()):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for i, h in enumerate(header):
        set_cell(t.rows[0].cells[i], h, size=size, bold=True, fill=HDR_FILL)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        fill = fills[ri] if fills else None
        for i, v in enumerate(row):
            set_cell(cells[i], v, size=size, fill=fill,
                     align=WD_ALIGN_PARAGRAPH.RIGHT if i in num_cols else None)
    for row in t.rows:
        for i, w in enumerate(widths_cm):
            row.cells[i].width = Cm(w)
    return t


def add_field(par, instr):
    r = par.add_run()
    b = OxmlElement("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    s = OxmlElement("w:fldChar")
    s.set(qn("w:fldCharType"), "separate")
    tx = OxmlElement("w:t")
    tx.text = "1"
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    for el in (b, it, s, tx, e):
        r._r.append(el)


def mono_block(doc, text, size=7.2, width=112):
    """Monospace listing in a grey single-cell table; long lines are wrapped with an indent."""
    lines = []
    for ln in text.rstrip("\n").split("\n"):
        if len(ln) <= width:
            lines.append(ln)
        else:
            lines.extend(textwrap.wrap(ln, width=width, subsequent_indent="    ",
                                       break_long_words=False, break_on_hyphens=False))
    t = doc.add_table(rows=1, cols=1)
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Cm(17.0)
    shade(cell, "F3F4F6")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(2)
    run = p.add_run("\n".join(lines))
    run.font.name = "Courier New"
    run.font.size = Pt(size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def para(doc, text, bold_lead=None, size=None, after=6, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
        if size:
            r.font.size = Pt(size)
    r = p.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    return p


def bullets(doc, items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        if isinstance(it, tuple):
            r = p.add_run(it[0])
            r.bold = True
            p.add_run(it[1])
        else:
            p.add_run(it)


def numbered(doc, items):
    for it in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(2)
        p.add_run(it)


def callout(doc, title, lines, fill=NOTE_FILL):
    t = doc.add_table(rows=1, cols=1)
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.rows[0].cells[0]
    cell.width = Cm(17.0)
    shade(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(title)
    r.bold = True
    for ln in lines:
        q = cell.add_paragraph()
        q.paragraph_format.space_after = Pt(2)
        q.add_run("- " + ln)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


FIG_N = [0]
TAB_N = [0]


def figure(doc, path, caption, width_cm=16.0):
    FIG_N[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph(style="Caption")
    cap.paragraph_format.space_after = Pt(10)
    r = cap.add_run(f"Figure {FIG_N[0]}. ")
    r.bold = True
    cap.add_run(caption)
    return FIG_N[0]


def table_caption(doc, text):
    TAB_N[0] += 1
    cap = doc.add_paragraph(style="Caption")
    cap.paragraph_format.keep_with_next = True
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(3)
    r = cap.add_run(f"Table {TAB_N[0]}. ")
    r.bold = True
    cap.add_run(text)
    return TAB_N[0]


def fmt_ps(x):
    return f"{x:.1f}"


# ----------------------------------------------------------------------------- main
def main():
    cal = parse_netlist(CAL_CIR)
    orig = parse_netlist(ORIG_CIR)
    check_netlist(cal, orig)
    lat = cal["subckts"]["DLATCH"]
    metrics = json.loads(METRICS.read_text())
    pvt = list(csv.DictReader(open(PVT_CSV)))
    assert len(pvt) == 27

    # ---- figures
    fig_latch(cal, FIG_DIR / "fig_a_latch_schematic.png")
    fig_ring(cal, FIG_DIR / "fig_b_ring_diagram.png")
    t_ck_ps, t_out_ps, f_in_meas, f_out_meas = fig_waveform(metrics, FIG_DIR / "fig_c_waveform.png")
    fig_division(FIG_DIR / "fig_d_division_search.png")

    # ---- validate (real output, read-only script)
    vpy = "/home/parshu/miniconda3/bin/python"
    if not os.path.exists(vpy):
        vpy = sys.executable
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    vp = subprocess.run([vpy, "-I", str(VALIDATE)], cwd=str(ROOT), capture_output=True, text=True, env=env)
    val_text = (vp.stdout + vp.stderr).rstrip()
    val_rc = vp.returncode

    # ---- derived numbers for the text (all from the files)
    pass_rows = [r for r in pvt if r["Divides"] == "PASS"]
    fail_rows = [r for r in pvt if r["Divides"] == "FAIL"]
    delays = [(float(r["Delay_ps"]), r) for r in pass_rows]
    d_min = min(delays, key=lambda z: z[0])
    d_max = max(delays, key=lambda z: z[0])
    slow3 = sorted(delays, key=lambda z: -z[0])[:3]
    pwr = [float(r["Power_mW"]) for r in pass_rows]
    phe = [float(r["MaxPhaseStepErr_deg_or_reason"]) for r in pass_rows]
    groups = {}
    for r in pass_rows:
        groups.setdefault((r["Corner(synthetic)"], r["Temp_C"]), []).append((float(r["VDD_V"]), float(r["Power_mW"])))
    full = {k: sorted(v) for k, v in groups.items() if len(v) == 3}
    mono_ok = sum(1 for k, v in full.items() if all(v[i][1] < v[i + 1][1] for i in range(2)))
    fail_desc = "; ".join(f"{r['Corner(synthetic)']}, {r['Temp_C']} C, {r['VDD_V']} V ({r['MaxPhaseStepErr_deg_or_reason']})"
                          for r in fail_rows)
    slow_desc = ", ".join(f"{r['Corner(synthetic)']} {r['Temp_C']} C {r['VDD_V']} V ({d:.1f} ps)" for d, r in slow3)
    slow_all_125 = all(r["Temp_C"] == "125" for _, r in slow3)
    temp_spread = "; ".join(
        f"{t} C {min(float(r['Delay_ps']) for r in pass_rows if r['Temp_C'] == t):.1f} to "
        f"{max(float(r['Delay_ps']) for r in pass_rows if r['Temp_C'] == t):.1f} ps"
        for t in ("-40", "27", "125"))
    steps = metrics["phase_steps_deg"]
    ph = metrics["phase_deg"]

    # ---- document
    doc = Document()
    doc.core_properties.title = "Local Simulation Report: 8-Phase Divide-by-Two CMOS Frequency Divider"
    doc.core_properties.author = ""
    doc.core_properties.subject = "ngspice validation of the Kuo et al. (IEEE MWTL, May 2025) topology"
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    sec.different_first_page_header_footer = True
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = fp.add_run("Local Simulation Report  |  page ")
    fr.font.size = Pt(8.5)
    add_field(fp, "PAGE")
    for r in fp.runs:
        r.font.size = Pt(8.5)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Heading 1", 15), ("Heading 2", 12.5)):
        st = doc.styles[name]
        st.font.size = Pt(size)
        st.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        st.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
        st.paragraph_format.space_after = Pt(5)

    # ---- title page
    for _ in range(7):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run("Local Simulation Report:\n8-Phase Divide-by-Two CMOS Frequency Divider")
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run("ngspice validation of the Kuo et al. (IEEE MWTL, May 2025) topology")
    r.font.size = Pt(13)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("Date: 2026-10-30")
    r.font.size = Pt(11)
    for _ in range(3):
        doc.add_paragraph()
    callout(doc, "Scope of every number in this report", [
        "Simulations use a GENERIC LEVEL=1 180 nm model deck (spice/models/cmos180.mod). "
        "This is NOT a foundry model and NOT the Cadence gpdk045 PDK.",
        "The PVT corners are SYNTHETIC (VTO shifted by 50 mV, KP scaled by 15 percent). They are not foundry corners.",
        "The Cadence gpdk045 results will replace these numbers when that run is finished.",
    ])
    doc.add_page_break()

    # ---- 1 Purpose and scope
    doc.add_heading("2  Purpose and scope", level=1)
    para(doc, "This report documents the ngspice simulations that were run locally for the 8-phase divide-by-two "
              "CMOS frequency divider in this repository. The topology is the one in Kuo et al., \"A Compact Multiphase "
              "Divide-by-Two CMOS Frequency Divider\", IEEE MWTL, May 2025, which is the reference of the project reports.")
    para(doc, "The work had four goals:")
    bullets(doc, [
        "check whether the original repository netlist divides by two (it does not, Section 5);",
        "find a calibrated netlist that divides, and record which change made the difference (Section 5, Table 4);",
        "measure the calibrated baseline: frequency, the eight output phases, CK-to-output delay, supply power and "
        "power-delay product (Section 6);",
        "run a 27-point PVT sweep of the calibrated netlist and check every measurement with an automated script "
        "(Sections 7 and 8).",
    ])
    callout(doc, "Read this first", [
        "The simulations use a GENERIC LEVEL=1 180 nm model deck (spice/models/cmos180.mod). It is not a foundry model "
        "and it is not gpdk045.",
        "The corners are SYNTHETIC. FF shifts VTO by -50 mV and scales KP by 1.15; SS shifts VTO by +50 mV and scales KP "
        "by 0.85 (both device types). The temperature points are -40, 27 and 125 C.",
        "The Cadence gpdk045 results will replace these numbers. spectre/divider_gpdk45.scs is written but has not been "
        "run, and no Cadence result file exists under results/.",
        "The calibration (5 kOhm loads, 1.2 V bias, 30 fF load on every output) was chosen by the division search in "
        "Section 5. These values differ from the original repository netlist.",
    ])

    # ---- 2 Tools
    doc.add_heading("3  Tools and environment", level=1)
    para(doc, "Simulator: ngspice-41 (the conda-forge ngspice-41 package; the binary reports \"ngspice-41\"). It is not on "
              "PATH in this environment, so the scripts take the binary from the NGSPICE environment variable. "
              "Measurement and plotting use Python with numpy and matplotlib. The report itself was generated with "
              f"python-docx {metadata.version('python-docx')}, matplotlib {matplotlib.__version__}, numpy {np.__version__} "
              f"under Python {platform.python_version()}, in a separate virtual environment.")
    para(doc, "Project scripts used for the results in this report:", after=3)
    table_caption(doc, "Scripts and what each one does.")
    add_table(doc, ["Script", "Purpose"], [
        ["scripts/divider_sim.py", "Shared runner. Writes a temporary deck from spice/divider_baseline_cal.cir with the given "
                                   "VDD, temperature and synthetic corner, runs ngspice in batch mode and measures the output."],
        ["scripts/measure_tran.py", "Measurement. From the wrdata waveform: CK and output edges, frequency, division ratio, "
                                    "eight phases, supply power, CK-to-output delay and PDP."],
        ["scripts/analyze_baseline.py", "Runs the calibrated baseline at TT / 27 C / 1.8 V and writes results/metrics_baseline.json."],
        ["scripts/run_pvt_matrix.py", "27-run PVT sweep (3 synthetic corners x -40/27/125 C x 1.62/1.80/1.98 V). Writes "
                                      "results/pvt_summary_table.csv; failing runs are kept as FAIL rows."],
        ["scripts/make_plots.py", "Draws the three plots in results/plots/ from the measured waveform, JSON and CSV."],
        ["scripts/validate.py", "13 independent checks. Re-measures the raw waveform and compares it with the JSON and CSV (Section 8)."],
        ["scripts/build_local_report.py", "Builds this report: figures drawn from the netlist, the division-search chart, and the .docx."],
    ], [5.2, 11.8], size=8.5)
    doc.add_paragraph()

    # ---- 3 Circuit
    doc.add_heading("4  Circuit description", level=1)
    para(doc, "The divider is a ring of four DLATCH subcircuits (XD1 to XD4). Each latch has a sampling pair (M1, M2, "
              "inputs D and Db) and a cross-coupled hold pair (M3, M4). Clock switch M5 (gate CK) steers the tail current "
              "from M7 (gate nbias) into the sampling pair through node xs. Clock switch M6 (gate CKb) steers the same tail "
              "current into the hold pair through node xh. Each latch has two 5 kOhm pull-up resistors to VDD, at Q and Qb. "
              "In the calibrated netlist every one of the eight outputs has a 30 fF load to ground.")
    para(doc, "Figure 1 shows one latch at transistor level. Figure 2 shows the ring. Both were drawn by "
              "scripts/build_local_report.py from the parsed netlist, and the script asserts the connectivity before drawing.")
    figure(doc, FIG_DIR / "fig_a_latch_schematic.png",
           "Transistor-level schematic of one DLATCH, drawn programmatically from the simulated netlist "
           "(spice/divider_baseline_cal.cir); not a Cadence screenshot. Device names, drain/gate/source/bulk nets, W/L "
           "and the R values are read from the netlist. Nets with the same name are the same node.", width_cm=16.5)
    figure(doc, FIG_DIR / "fig_b_ring_diagram.png",
           "Top-level ring of four DLATCH instances, drawn programmatically from the simulated netlist; not a Cadence "
           "screenshot. Each latch takes both outputs of its predecessor (Q1b drives D2, Q1 drives Db2, and so on). "
           "Blue: latches whose CK pin is on net CK (XD1, XD4). Orange: latches whose CK pin is on net CKb (XD2, XD3), "
           "so the clock is swapped for these two.", width_cm=16.5)
    table_caption(doc, "Device sizes of one DLATCH, from the netlist. All four instances use the same subcircuit.")
    rows = []
    for name in ("M1", "M2", "M5", "M3", "M4", "M6", "M7"):
        m = lat["mos"][name]
        rows.append([name, "NMOS", m["d"], m["g"], m["s"], m["b"], m["W"], m["L"]])
    for name in ("R1", "R2"):
        r = lat["res"][name]
        rows.append([name, "resistor", r["n1"], "-", r["n2"], "-", "-", r["value"]])
    add_table(doc, ["Device", "Type", "Drain / n1", "Gate", "Source / n2", "Bulk", "W", "L / value"], rows,
              [1.6, 2.6, 2.4, 2.0, 2.4, 1.6, 2.1, 2.3], size=8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    para(doc, "Sources in the top level: Vdd = 1.8 V; CK and CKb are 1.4 GHz pulse clocks (CKb is delayed by half a period, "
              "as written in the netlist); nbias = 1.2 V in the calibrated netlist.", size=9.5)
    table_caption(doc, "Interconnect of the four latches, from the netlist (pin order D, Db, CK, CKb, Q, Qb).")
    rows = []
    for x in ("XD1", "XD2", "XD3", "XD4"):
        nodes = cal["instances"][x][1]
        rows.append([x, *nodes[:6], ctype(cal, x)])
    add_table(doc, ["Latch", "D", "Db", "CK", "CKb", "Q", "Qb", "CK pin is on"], rows,
              [1.8, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.9], size=9, num_cols=())
    para(doc, "Ring connections: Q1b -> D2 and Q1 -> Db2; Q2 -> D3 and Q2b -> Db3; Q3b -> D4 and Q3 -> Db4; "
              "Q4b -> D1 and Q4 -> Db1. Each latch receives both outputs of its predecessor, so the ring has eight "
              "data wires, not four.", size=9.5)

    # ---- 4 Finding
    doc.add_heading("5  Finding: the original netlist does not divide", level=1)
    para(doc, "The original repository netlist (spice/divider_baseline.cir) uses 1.5 kOhm loads, a 0.9 V bias, no output "
              "load and no .ic start-up. It was simulated as written and with an .ic start-up, and then swept in bias "
              "and load resistance. None of these settings divided. Table 4 lists the differences between the original "
              "and the calibrated netlist, derived by parsing both files. Table 5 gives the search results.")
    table_caption(doc, "Differences between the original repository netlist and the calibrated netlist (both parsed "
                       "from the files). Transistor sizes are identical in both.")
    orig_r = orig["subckts"]["DLATCH"]["res"]["R1"]["value"]
    cal_r = lat["res"]["R1"]["value"]
    add_table(doc, ["Item", "Original (divider_baseline.cir)", "Calibrated (divider_baseline_cal.cir)"], [
        ["Latch load resistors R1, R2", orig_r, cal_r],
        ["Bias voltage nbias", f"{orig['sources']['Vbias']['spec']} V", f"{cal['sources']['Vbias']['spec']} V"],
        ["Output load capacitors", f"{len(orig['caps'])} (none)", f"{len(cal['caps'])} x {cal['caps']['Cl1']['value']} to ground"],
        ["Initial conditions (.ic)", "no" if not any(".ic" in d.split()[0] for d in orig["directives"]) else "yes",
         "yes (V(Q1)=1.8 V, V(Q1b)=0, ...)" if any(".ic" in d.split()[0] for d in cal["directives"]) else "no"],
        [".tran with uic (use initial conditions)", "no" if not any("uic" in d for d in orig["directives"]) else "yes",
         "yes" if any("uic" in d for d in cal["directives"]) else "no"],
    ], [5.4, 5.6, 6.0], size=9)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    table_caption(doc, "Division search (local ngspice runs). Generic 180 nm LEVEL=1 deck, fin 1.4 GHz, VDD 1.8 V, "
                       "with .ic start-up where stated.")
    add_table(doc, ["Case", "Load R", "Vbias", "Output load", "Result"],
              [list(r) for r in DIVISION_SEARCH], [4.0, 1.9, 2.4, 1.8, 6.9], size=8.5, fills=[
                  "E2F0D9" if "DIVIDES" in r[4] else None for r in DIVISION_SEARCH])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    figure(doc, FIG_DIR / "fig_d_division_search.png",
           "Division search, calibrated load sweep (5k loads, 1.2 V bias). Left: output frequency per load with the "
           "1400 MHz input and 700 MHz half-rate references; the only divide-by-two point (30 fF) is green. Right: "
           "division ratio against load, with the target ratio of 2. Both panels use the values in Table 5 and the "
           "ratio is checked against f_in (f_out x ratio = 1400 MHz for every row).", width_cm=15.5)
    para(doc, "Why the original netlist fails and why the calibrated one works:", bold_lead=None, after=3)
    bullets(doc, [
        ("Hold pair gain. ", "The cross-coupled pair M3/M4 must have a small-signal loop gain gm x R greater than 1 to "
                             "regenerate and hold a state. With the original 1.5 kOhm loads, Q and Qb of every latch sit at the "
                             "same voltage (1.64 to 1.81 V), so there is no stored state to divide. The R sweep is consistent "
                             "with this: at 3k nothing toggled, while 5k at 1.2 V and 8k at 0.9 V did toggle."),
        ("Load capacitance sets the delay. ", "Without output load, the R sweep toggled at the clock rate "
                             "(1426-1451 MHz, ratio 0.96-0.98): each latch regenerates within every clock phase, so the ring "
                             "follows the clock instead of dividing. Adding 30 fF per output slows the latch enough for "
                             "the ring to divide (700.0 MHz, ratio 2.000); 10 fF still follows the clock (ratio 0.964)."),
        ("Too slow fails again. ", "With more load (40 to 80 fF) the latch cannot complete its update within a phase, "
                             "and the ratio moves away from 2 (1.424, 3.097, 6.000, 4.153). In this sweep only 30 fF divides."),
    ])

    # ---- 5 Calibrated baseline
    doc.add_heading("6  Calibrated baseline results", level=1)
    para(doc, "The calibrated netlist was simulated at TT / 27 C / 1.8 V. Table 6 gives the measured metrics from "
              "results/metrics_baseline.json. The power is averaged over 11 whole output periods after a 10 ns settling "
              "time. The delay is the mean time from each CK rising edge (50 percent point) to the next rising edge on any "
              "of the eight outputs, each measured at its own mid-swing level.")
    table_caption(doc, "Measured metrics of the calibrated baseline (TT / 27 C / 1.8 V), from results/metrics_baseline.json.")
    add_table(doc, ["Metric", "Value", "Note"], [
        ["Supply VDD", f"{metrics['vdd_v']} V", "netlist .param VDD"],
        ["Input clock f_in", f"{metrics['f_in_ghz']:.3f} GHz", "1.4 GHz pulse clock (period 714.3 ps)"],
        ["Output frequency f_out (Q1)", f"{metrics['f_out_mhz']:.1f} MHz", "mean of Q1 rising-edge periods"],
        ["Division ratio f_in / f_out", f"{metrics['division_ratio']:.3f}",
         "divides by two: " + ("yes" if metrics["divides"] else "no")],
        ["CK-to-output delay (mean)", f"{metrics['ck_to_q_delay_ps']:.1f} ps", "see definition above"],
        ["Average supply current", f"{metrics['i_avg_ma']:.3f} mA", "trapezoidal average of i(Vdd)"],
        ["Power P = VDD x I_avg", f"{metrics['power_mw']:.3f} mW", f"{metrics['periods_averaged']} whole output periods"],
        ["Power-delay product", f"{metrics['pdp_fj']:.1f} fJ", "P x delay (1 mW x 1 ps = 1 fJ)"],
        ["Max phase-step error", f"{metrics['max_phase_step_error_deg']:.1f} deg", "against the ideal 45 deg step"],
    ], [5.4, 3.4, 8.2], size=9, num_cols=(1,))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    table_caption(doc, "Measured phases of the eight outputs, relative to the Q1 rising edge, and the step to the next output.")
    order = list(ph.items())
    rows = []
    for i, (n, v) in enumerate(order):
        rows.append([n, f"{v:.2f}", f"{steps[i]:.2f}", f"{steps[i] - 45:+.2f}"])
    add_table(doc, ["Output", "Phase (deg)", "Step to next (deg)", "Error vs 45 deg"], rows,
              [3.6, 3.4, 4.2, 4.2], size=9, num_cols=(1, 2, 3))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    lo_v = min(a for a, _ in metrics["swing_v"].values())
    hi_v = max(b for _, b in metrics["swing_v"].values())
    para(doc, f"The eight phases are distinct and every output swings between {lo_v:.3f} V and {hi_v:.3f} V. "
              f"The phase steps alternate between about {steps[0]:.1f} and {steps[1]:.1f} degrees, so the outputs are not "
              f"evenly spaced at 45 degrees. The largest step error is {metrics['max_phase_step_error_deg']:.1f} degrees "
              "against the ideal 45 degrees. The reference paper reports phase error within 3.75 degrees on silicon. "
              "That accuracy is NOT reproduced by this simulation.")
    para(doc, "The search in Table 5 varied only the load resistance, the bias and the output load. Device sizes were "
              "not varied, and the output load was limited by the division window (40 fF and above no longer divide). "
              "Neither knob was tuned for phase balance in this report.")
    figure(doc, FIG_DIR / "fig_c_waveform.png",
           f"Waveform of the calibrated baseline (TT / 27 C / 1.8 V), from results/baseline_cal_tran.txt, 14 to 20 ns: "
           f"CK, Q1 and Q1b. The measured CK period is {t_ck_ps:.1f} ps and the measured Q1 period is {t_out_ps:.1f} ps, "
           "so Q1 has half the frequency of CK. Dotted lines mark the Q1 rising edges.", width_cm=15.5)
    figure(doc, PLOTS / "baseline_8phases.png",
           "Eight outputs of the calibrated baseline over three output periods after start-up, stacked and sorted by "
           "measured phase (results/plots/baseline_8phases.png, drawn by scripts/make_plots.py).", width_cm=15.5)
    figure(doc, PLOTS / "baseline_phase_error.png",
           "Measured phase of each output against the ideal 45-degree spacing (results/plots/baseline_phase_error.png).",
           width_cm=12.5)

    # ---- 6 PVT
    doc.add_heading("7  PVT results", level=1)
    para(doc, "Table 8 lists all 27 runs of results/pvt_summary_table.csv: three synthetic corners (TT, FF, SS), three "
              "temperatures (-40, 27, 125 C) and three supply voltages (1.62, 1.80, 1.98 V). Runs that did not divide by "
              "two are kept in the table as FAIL rows (shaded), with the measured output frequency and ratio. "
              "The corners are synthetic (Section 2), so they are not foundry corners.")
    table_caption(doc, "PVT sweep of the calibrated netlist, all 27 runs, from results/pvt_summary_table.csv. "
                       "Corners are synthetic. FAIL rows are shaded.")
    rows = []
    fills = []
    for r in pvt:
        rows.append([r["Corner(synthetic)"], r["Temp_C"], r["VDD_V"], r["Divides"], r["f_out_MHz"], r["Delay_ps"],
                     r["Power_mW"], r["PDP_fJ"], r["MaxPhaseStepErr_deg_or_reason"]])
        fills.append(FAIL_FILL if r["Divides"] == "FAIL" else None)
    add_table(doc, ["Corner", "Temp (C)", "VDD (V)", "Divides", "f_out (MHz)", "Delay (ps)", "Power (mW)",
                    "PDP (fJ)", "Max phase-step err (deg), or reason"], rows,
              [1.4, 1.5, 1.5, 1.6, 1.8, 1.7, 1.8, 1.6, 4.1], size=7.5, fills=fills, num_cols=(1, 2, 4, 5, 6, 7))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    figure(doc, PLOTS / "pvt_delay_power.png",
           "CK-to-output delay and supply power against VDD for each synthetic corner and temperature "
           "(results/plots/pvt_delay_power.png, drawn by scripts/make_plots.py). The FAIL points are annotated.",
           width_cm=16.5)
    para(doc, "Reading the sweep:", after=3)
    bullets(doc, [
        f"{len(pass_rows)} of {len(pvt)} runs divide by two. The {len(fail_rows)} failures are at {fail_desc}. "
        "Both are at the SS corner and 125 C, and both are on the slow side of the sweep.",
        f"Over the {len(pass_rows)} passing runs the CK-to-output delay spans {d_min[0]:.1f} to {d_max[0]:.1f} ps "
        f"(TT / 27 C / 1.8 V: {metrics['ck_to_q_delay_ps']:.1f} ps). The spread by temperature is {temp_spread}. "
        f"The three slowest runs are {slow_desc}"
        + (", all at 125 C." if slow_all_125 else "."),
        f"Power tracks the supply. In {mono_ok} of the {len(full)} corner and temperature groups where all three "
        f"supply points pass, power rises with VDD at every step. Across the passing runs it ranges from "
        f"{min(pwr):.3f} to {max(pwr):.3f} mW.",
        f"Phase accuracy is far from the paper's 3.75 degrees at every passing point. The max phase-step error over the "
        f"passing runs is {min(phe):.2f} to {max(phe):.2f} degrees.",
    ])

    # ---- 7 Validation
    doc.add_heading("7  Validation", level=1)
    para(doc, "scripts/validate.py performs the 13 checks below. It re-measures the raw waveform "
              "(results/baseline_cal_tran.txt) with scripts/measure_tran.py and compares the result with the JSON and CSV "
              "files, so a hand-typed or stale result file cannot pass. The output below is the real output of that "
              f"script, run for this report as {vpy} -I scripts/validate.py (exit code {val_rc}).")
    numbered(doc, [
        "baseline divides by 2 (re-measured ratio)",
        "f_out = 700 MHz within 0.1 percent",
        "JSON power matches the re-measurement",
        "JSON CK-to-output delay matches the re-measurement",
        "PDP units: mW x ps = fJ (PDP equals power x delay)",
        "Q and Qb in antiphase (phase of Q1b = 180 degrees)",
        "eight distinct output phases",
        "every output swings more than 0.3 V",
        "power is consistent with VDD x I_avg",
        "PVT table has 27 rows (3 corners x 3 temperatures x 3 VDD)",
        "PVT PDP equals power x delay on every PASS row",
        "PVT TT / 27 C / 1.8 V row equals the baseline JSON power",
        "failed corners are kept in the table (2 FAIL rows)",
    ])
    mono_block(doc, val_text, size=7.0, width=110)

    # ---- 9 Limitations
    doc.add_heading("9  Limitations and next steps", level=1)
    bullets(doc, [
        ("Generic model, not a PDK. ", "All numbers use the generic LEVEL=1 180 nm deck (spice/models/cmos180.mod). "
                                       "They are not foundry or gpdk045 numbers and must not be quoted as such."),
        ("Synthetic corners. ", "FF and SS are a 50 mV VTO shift and a 15 percent KP scaling of the generic deck. They do "
                                "not represent a process corner set."),
        ("No layout. ", "The netlist has no layout parasitics. The layout is being done in Cadence Virtuoso on gpdk045 "
                        "and is not part of these simulations."),
        ("Phase accuracy not reached. ", f"The max phase-step error is {metrics['max_phase_step_error_deg']:.1f} degrees "
                                         "against the paper's 3.75 degrees on silicon. The steps alternate between about "
                                         f"{steps[0]:.1f} and {steps[1]:.1f} degrees."),
        ("Version 2 enhancements out of scope. ", "The V2 enhancements (spice/divider_v2_enhanced.cir) were deliberately "
                                                  "left out of this report."),
        ("Cadence gpdk045 run pending. ", "spectre/divider_gpdk45.scs is written but has not been run against a PDK (its "
                                          "header states it is untested), and no Cadence result file exists under results/. "
                                          "When it runs, the tables in this report should be replaced by the gpdk045 results."),
    ])

    # ---- 10 Appendix
    doc.add_page_break()
    doc.add_heading("10  Appendix", level=1)
    doc.add_heading("10.1  Calibrated netlist listing", level=2)
    para(doc, "Listing of spice/divider_baseline_cal.cir, reproduced exactly as it is in the repository.", size=10)
    mono_block(doc, CAL_CIR.read_text(), size=6.8, width=112)
    doc.add_heading("10.2  Reproduction commands", level=2)
    para(doc, "Run from the project root. NGSPICE must point to the ngspice-41 binary. The first command rewrites "
              "results/metrics_baseline.json and the PVT and plot commands rewrite files under results/, so run them only "
              "when you intend to regenerate those results. These commands were not re-run for this report.")
    mono_block(doc, "NGSPICE=<path to ngspice> python3 scripts/analyze_baseline.py && python3 scripts/run_pvt_matrix.py "
                    "&& python3 scripts/make_plots.py && python3 scripts/validate.py && python3 scripts/build_reports.py",
               size=7.5, width=100)
    para(doc, "This report is rebuilt with the Python environment that has python-docx, matplotlib and numpy:")
    mono_block(doc, "<venv>/bin/python scripts/build_local_report.py", size=8.5)
    para(doc, "The PDF copy is produced with:")
    mono_block(doc, "libreoffice --headless --convert-to pdf --outdir report report/Local_Simulation_Report.docx", size=8.5)

    doc.save(str(OUT_DOCX))
    print(f"wrote {OUT_DOCX}")
    print(f"figures: {sorted(p.name for p in FIG_DIR.glob('*.png'))}")
    print(f"validate exit code: {val_rc}")
    return val_rc


if __name__ == "__main__":
    sys.exit(main())
