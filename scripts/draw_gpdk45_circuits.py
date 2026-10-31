#!/usr/bin/env python3
"""Draw the gpdk045 divider circuits from the Spectre netlist.

Writes two figures for the gpdk045 report:
  report/gpdk045/figures/fig_circuit_latch.png   one DLATCH (M1 to M7, R1, R2)
  report/gpdk045/figures/fig_circuit_ring.png    the four latches in the ring

Sources:
  spectre/divider_gpdk45.scs          topology, device sizes, load and bias names
  results/gpdk045/virtuoso_dlatch_params_designD.txt
                                      Virtuoso read-back of design D (m and R used for labels)

The drawing code is a port of scripts/build_local_report.py (fig_latch, fig_ring), with the
baseline netlist replaced by the gpdk045 Spectre netlist. Labels show the gpdk045 sizes.
The script uses matplotlib, which is installed for /usr/bin/python3, not in the docx venv.

Usage (from any directory):
  /usr/bin/python3 scripts/draw_gpdk45_circuits.py
"""

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NETLIST = REPO / "spectre" / "divider_gpdk45.scs"
READBACK = REPO / "results" / "gpdk045" / "virtuoso_dlatch_params_designD.txt"
FIG_DIR = REPO / "report" / "gpdk045" / "figures"

INK = "#1f2933"
RED_NET = "#b42318"
BLUE = "#2b6cb0"
ORANGE = "#c05621"
GREEN = "#2f855a"
GREY = "#6b7280"
CK_FILL = "#dbeafe"
CKB_FILL = "#fde7d3"

# Spectre net names at the top level map to the report names used in the drawings.
NET_MAP = {"vdd": "VDD", "nbias": "NBIAS", "ck": "CK", "ckb": "CKb", "0": "VSS"}

# Expected topology (drain, gate, source, bulk) of each DLATCH device. The drawing is only
# produced if the netlist matches these, so the wires drawn join the nets the netlist names.
EXP_MOS = {
    "M1": ("Q", "D", "xs", "VSS"), "M2": ("Qb", "Db", "xs", "VSS"),
    "M5": ("xs", "CK", "tail", "VSS"), "M3": ("Q", "Qb", "xh", "VSS"),
    "M4": ("Qb", "Q", "xh", "VSS"), "M6": ("xh", "CKb", "tail", "VSS"),
    "M7": ("tail", "NBIAS", "VSS", "VSS"),
}
EXP_PINS = ["D", "Db", "CK", "CKb", "Q", "Qb", "VDD", "VSS", "NBIAS"]
EXP_XD = {  # (D, Db, CK, CKb, Q, Qb) of each latch instance at the top level
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

# Pin positions on each latch box: side and fraction along the side.
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


def fail(msg):
    raise SystemExit(f"draw_gpdk45_circuits: {msg}")


# ----------------------------------------------------------------------------- parsing
def parse_netlist(path):
    """Parse the Spectre subset used by spectre/divider_gpdk45.scs."""
    info = {"params": {}, "pins": None, "mos": {}, "res": {}, "inst": {}, "caps": {}}
    in_sub = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.split("//", 1)[0].strip()
        if not s:
            continue
        if s.startswith("parameters "):
            info["params"] = dict(t.split("=", 1) for t in s.split()[1:] if "=" in t)
            continue
        m = re.match(r"subckt\s+(\w+)\s*\(([^)]*)\)", s)
        if m:
            if m.group(1) == "DLATCH":
                info["pins"] = m.group(2).split()
                in_sub = True
            continue
        if s.startswith("ends"):
            in_sub = False
            continue
        m = re.match(r"^(\w+)\s*\(([^)]*)\)\s*(.*)$", s)
        if not m:
            continue
        name, nodes, rest = m.group(1), m.group(2).split(), m.group(3).split()
        kv = dict(t.split("=", 1) for t in rest if "=" in t)
        if in_sub and name[0] == "M":
            info["mos"][name] = dict(d=nodes[0], g=nodes[1], s=nodes[2], b=nodes[3], model=rest[0],
                                     W=kv["w"], L=kv["l"], multi=kv["multi"])
        elif in_sub and name[0] == "R":
            info["res"][name] = dict(n1=nodes[0], n2=nodes[1], value=kv["r"])
        elif not in_sub and name[0] == "X" and rest:
            info["inst"][name] = (rest[0], [NET_MAP.get(n, n) for n in nodes])
        elif not in_sub and name.startswith("CL"):
            info["caps"][name] = dict(n1=nodes[0], n2=nodes[1], value=kv["c"])
    return info


def parse_readback(path):
    """Virtuoso read-back of design D: resistor values (kOhm) and nMOS w, l, m per device."""
    res, mos = {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+)\s+(\S+)\s+(.*)$", line.strip())
        if not m:
            continue
        name, master, rest = m.groups()
        if master == "res":
            res[name] = re.search(r'r="([^"]*)"', rest).group(1)
        elif master == "nmos1v":
            mos[name] = {k: re.search(rf'{k}="([^"]*)"', rest).group(1) for k in ("w", "l", "m")}
    if not res or not mos:
        fail("could not read resistors or devices from the Virtuoso read-back")
    return res, mos


def length(text):
    """Netlist length such as '240n' becomes '240 nm'."""
    if not text.endswith("n"):
        fail(f"unexpected length {text}")
    return f"{float(text[:-1]):g} nm"


# ----------------------------------------------------------------------------- checks
def check(net, rb_res, rb_mos):
    pins = net["pins"]
    if pins != EXP_PINS:
        fail(f"DLATCH pins {pins} differ from {EXP_PINS}")
    mos = net["mos"]
    if set(mos) != set(EXP_MOS):
        fail(f"DLATCH devices {sorted(mos)} differ from {sorted(EXP_MOS)}")
    for name, exp in EXP_MOS.items():
        m = mos[name]
        if (m["d"], m["g"], m["s"], m["b"]) != exp:
            fail(f"{name}: netlist {(m['d'], m['g'], m['s'], m['b'])} != expected {exp}")
        if m["model"] != "g45n1svt":
            fail(f"{name}: unexpected model {m['model']}")
    if net["res"]["R1"] != dict(n1="VDD", n2="Q", value="rl") or \
       net["res"]["R2"] != dict(n1="VDD", n2="Qb", value="rl"):
        fail("R1/R2 are not VDD to Q and VDD to Qb with r=rl")
    if set(net["inst"]) != set(EXP_XD):
        fail(f"top-level latches {sorted(net['inst'])} differ from {sorted(EXP_XD)}")
    for x, (sub, nodes) in net["inst"].items():
        if sub != "DLATCH" or tuple(nodes[:6]) != EXP_XD[x] or nodes[6:] != ["VDD", "VSS", "NBIAS"]:
            fail(f"{x}: nodes {nodes} differ from the expected latch connections")
    if len(net["caps"]) != 8 or any(c["value"] != "cl" or c["n2"] != "0" for c in net["caps"].values()):
        fail("output load capacitors differ from 8 x (c=cl to ground)")
    # the Virtuoso read-back must give the same W, L and the multiplier for M1 to M7
    for name, m in mos.items():
        rb = rb_mos.get(name)
        if rb is None or (rb["w"], rb["l"]) != (m["W"], m["L"]):
            fail(f"{name}: Virtuoso read-back W/L {rb} differs from the netlist {m['W']}/{m['L']}")
    if {rb["m"] for rb in rb_mos.values()} != {rb_mos["M1"]["m"]}:
        fail("Virtuoso read-back multiplier differs between devices")
    if any(m["multi"] != "mult" for m in mos.values()):
        fail("netlist devices do not all use multi=mult")
    if set(rb_res) != {"R1", "R2"} or rb_res["R1"] != rb_res["R2"]:
        fail("Virtuoso read-back resistors R1 and R2 differ")
    rl = rb_res["R1"]
    if not rl.upper().endswith("K"):
        fail(f"unexpected resistor value {rl} in the read-back")
    return {"rl": rl[:-1].lower() + "k", "m": rb_mos["M1"]["m"], "w": rb_mos["M1"]["w"],
            "l": rb_mos["M1"]["l"], "w7": rb_mos["M7"]["w"], "l7": rb_mos["M7"]["l"],
            "cl": f"{float(net['params']['cl'][:-1]):g} fF"}


def ctype(latch_nodes):
    return "CK" if latch_nodes["CK"] == "CK" else "CKb"


def net_color(n):
    if n == "VDD":
        return RED_NET
    if n in ("CK", "CKb"):
        return BLUE
    if n == "NBIAS":
        return GREEN
    return INK


# ----------------------------------------------------------------------------- figures
def fig_latch(net, cfg, path):
    M = net["mos"]
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
        T(xc - 0.7, yc - 0.45, f"{name} nMOS  m = {cfg['m']}\nW = {length(m['W'])}  L = {length(m['L'])}",
          ha="right", va="top", size=8)
        T(xc - 0.66, yc, m["g"], net_color(m["g"]), ha="right", size=9, weight="bold")

    VDD_Y, QB_Y = 7.7, 6.05
    LAYOUT = {"M1": (2.5, 5.0), "M3": (5.3, 5.0), "M4": (7.7, 5.0), "M2": (10.5, 5.0),
              "M5": (2.5, 2.6), "M6": (7.7, 2.6), "M7": (5.0, 0.6)}
    for name, (xc, yc) in LAYOUT.items():
        drain = M[name]["d"]
        nmos(name, xc, yc, yc + 1.05 if drain in ("Q", "Qb") else yc + 0.8)
    # the drawn wires must join the nets the netlist names
    assert M["M1"]["d"] == M["M3"]["d"] == "Q" and M["M4"]["d"] == M["M2"]["d"] == "Qb"
    assert M["M1"]["s"] == M["M2"]["s"] == M["M5"]["d"] == "xs"
    assert M["M3"]["s"] == M["M4"]["s"] == M["M6"]["d"] == "xh"
    assert M["M5"]["s"] == M["M6"]["s"] == M["M7"]["d"] == "tail"
    assert M["M7"]["s"] == "VSS"

    # supply rail and load resistors (R1: VDD to Q, R2: VDD to Qb)
    L([2.75, 10.75], [VDD_Y, VDD_Y], RED_NET)
    T(2.6, VDD_Y + 0.12, "VDD", RED_NET, ha="right", weight="bold")
    for x, name, out_y in ((2.75, "R1", "Q"), (10.75, "R2", "Qb")):
        L([x, x], [VDD_Y, 7.25])
        ax.add_patch(Rectangle((x - 0.15, 6.45), 0.3, 0.8, fill=False, ec=INK, lw=1.2))
        L([x, x], [6.45, QB_Y])
        T(x + 0.25, 6.85, f"{name} = {cfg['rl']}  (VDD to {out_y})", size=9)
        dot(x, QB_Y)
    L([2.75, 5.55], [QB_Y, QB_Y]); dot(5.55, QB_Y)
    L([7.95, 10.75], [QB_Y, QB_Y]); dot(7.95, QB_Y)
    T(4.15, QB_Y + 0.14, "Q", ha="center", weight="bold")
    T(9.35, QB_Y + 0.14, "Qb", ha="center", weight="bold")
    # xs (sampling sources and M5 drain) and xh (hold sources and M6 drain)
    L([2.75, 2.75], [4.2, 3.4])
    T(2.9, 3.8, "xs", weight="bold")
    T(10.9, 4.2, "xs", weight="bold")
    L([7.95, 7.95], [4.2, 3.4])
    T(8.1, 3.3, "xh", weight="bold")
    T(5.45, 4.2, "xh", ha="right", weight="bold")
    # tail node: M5 and M6 sources, M7 drain
    L([2.75, 2.75, 7.95, 7.95], [1.8, 1.4, 1.4, 1.8])
    L([5.25, 5.25], [1.4, 1.4]); dot(5.25, 1.4)
    T(3.4, 1.52, "tail", weight="bold")
    # M7 source is the DLATCH VSS pin, tied to global ground at the top level
    L([5.25, 5.25], [-0.2, -0.3])
    L([5.05, 5.45], [-0.3, -0.3]); L([5.13, 5.37], [-0.38, -0.38]); L([5.21, 5.29], [-0.46, -0.46])
    T(5.6, -0.4, "VSS (0 V)", weight="bold")
    # gate of M7 is the NBIAS pin
    T(0.2, 8.3, "One DLATCH subcircuit, transistor level (drawn from spectre/divider_gpdk45.scs)",
      size=10, weight="bold")
    T(0.2, -0.55,
      f"Net-name labels: identical names are the same node. Bulk tied to VSS for all devices (as in the "
      f"netlist). Design D: m = {cfg['m']} (multi = mult), R1 = R2 = {cfg['rl']} (read back from Virtuoso).\n"
      f"Output load on each output node: {cfg['cl']} (eight capacitors, not drawn here).",
      size=7.5, c=GREY, va="top")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_ring(net, cfg, path):
    W, H = 3.2, 2.4
    BOX = {"XD1": (0.0, 4.2), "XD2": (5.5, 4.2), "XD3": (5.5, 0.0), "XD4": (0.0, 0.0)}
    latch = {x: dict(zip(EXP_PINS, nodes)) for x, (_, nodes) in net["inst"].items()}

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
        kind = ctype(latch[x])
        ax.add_patch(Rectangle((bx, by), W, H, facecolor=CK_FILL if kind == "CK" else CKB_FILL,
                               edgecolor=BLUE if kind == "CK" else ORANGE, lw=1.6))
        ax.text(bx + W / 2, by + H / 2 + 0.5, x, ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(bx + W / 2, by + H / 2 + 0.2,
                f"DLATCH, CK pin on net {kind}\nR1 = R2 = {cfg['rl']} to VDD\n"
                f"7 nMOS, m = {cfg['m']}\nW/L {length(cfg['w'])}/{length(cfg['l'])} "
                f"(M7 {length(cfg['w7'])}/{length(cfg['l7'])})",
                ha="center", va="top", fontsize=6.8, color=INK)
        for pin in ("D", "Db", "Q", "Qb", "CK", "CKb"):
            side = SIDE[x]["inp"] if pin in ("D", "Db") else (SIDE[x]["out"] if pin in ("Q", "Qb") else SIDE[x]["clk"])
            px, py = ppos(x, side, PIN_FRAC[x][pin])
            ax.plot([px], [py], "o", color=INK, ms=3)
            inset = {"top": (px, py - 0.1, "center", "top"), "bottom": (px, py + 0.1, "center", "bottom"),
                     "left": (px + 0.1, py, "left", "center"), "right": (px - 0.1, py, "right", "center")}[side]
            ax.text(inset[0], inset[1], pin, ha=inset[2], va=inset[3], fontsize=8, fontweight="bold", color=INK)

    # clock pins: stubs to the global clock nets
    for x in BOX:
        side = SIDE[x]["clk"]
        for pin in ("CK", "CKb"):
            net_name = latch[x][pin]
            assert net_name in ("CK", "CKb")
            px, py = ppos(x, side, PIN_FRAC[x][pin])
            dx, dy = {"top": (0, 0.45), "bottom": (0, -0.45), "right": (0.45, 0), "left": (-0.45, 0)}[side]
            ax.plot([px, px + dx], [py, py + dy], color=net_color(net_name), lw=1.4)
            tx, ty = px + dx * 1.1, py + dy * 1.1
            ha, va = ("center", "bottom") if side == "top" else (("center", "top") if side == "bottom" else ("left", "center"))
            ax.text(tx, ty, net_name, color=net_color(net_name), ha=ha, va=va, fontsize=9, fontweight="bold")

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
        net_name = latch[sx][sp]
        lab = {"right": (ps[0] + 0.06, ps[1] + 0.07, "left", "bottom"),
               "left": (ps[0] - 0.06, ps[1] + 0.07, "right", "bottom"),
               "top": (ps[0], ps[1] + 0.08, "center", "bottom"),
               "bottom": (ps[0], ps[1] - 0.08, "center", "top")}[s_side]
        ax.text(lab[0], lab[1], net_name, ha=lab[2], va=lab[3], fontsize=9, fontweight="bold", color=RED_NET)

    ax.legend(handles=[
        Patch(facecolor=CK_FILL, edgecolor=BLUE, label="latch with CK pin on net CK"),
        Patch(facecolor=CKB_FILL, edgecolor=ORANGE, label="latch with CK pin on net CKb (clock swapped)"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=2, fontsize=8, frameon=False)
    ax.text(-1.0, 7.5, "Ring: XD1 -> XD2 -> XD3 -> XD4 -> XD1. Red labels = net driven by the source latch.",
            fontsize=8, color=GREY, va="top")
    ax.text(-1.0, -1.0, f"Each output node also has a {cfg['cl']} capacitor to ground (CL1 ... CL4b, not drawn). "
            "VDD pins are on net VDD, VSS pins on the global ground.", fontsize=7.5, color=GREY)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    net = parse_netlist(NETLIST)
    rb_res, rb_mos = parse_readback(READBACK)
    cfg = check(net, rb_res, rb_mos)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    latch_png = FIG_DIR / "fig_circuit_latch.png"
    ring_png = FIG_DIR / "fig_circuit_ring.png"
    fig_latch(net, cfg, latch_png)
    fig_ring(net, cfg, ring_png)
    print(f"wrote {latch_png}")
    print(f"wrote {ring_png}")
    print(f"labels from read-back: R = {cfg['rl']}, m = {cfg['m']}, cl = {cfg['cl']}")


if __name__ == "__main__":
    sys.exit(main())
