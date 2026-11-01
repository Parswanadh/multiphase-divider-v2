"""Run the calibrated baseline netlist in ngspice at a given VDD / temperature / synthetic corner,
then measure it. Shared by analyze_baseline.py and run_pvt_matrix.py.

NGSPICE env var overrides the ngspice binary (default: `ngspice` on PATH).
Synthetic corners shift the generic LEVEL=1 deck (FF: VTO-50mV, KP x1.15; SS: VTO+50mV, KP x0.85).
They are NOT foundry corners and must be reported as such.
"""
import os, re, shutil, subprocess, tempfile, pathlib
from measure_tran import measure

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORNERS = {"TT": (0.0, 1.0), "FF": (-0.05, 1.15), "SS": (+0.05, 0.85)}


def _model(corner):
    dvt, kpx = CORNERS[corner]
    out = []
    for line in (ROOT / "spice/models/cmos180.mod").read_text().splitlines():
        if line.startswith(".model"):
            sign = -1 if "PMOS" in line else 1
            line = re.sub(r"VTO=(-?[\d.]+)", lambda m: f"VTO={float(m.group(1)) + sign*dvt:.4f}", line)
            line = re.sub(r"KP=([\d.]+)u", lambda m: f"KP={float(m.group(1))*kpx:.3f}u", line)
        out.append(line)
    return "\n".join(out) + "\n"


def run_case(vdd=1.8, temp=27, corner="TT", netlist="spice/divider_baseline_cal.cir", keep=None):
    ng = os.environ.get("NGSPICE") or shutil.which("ngspice")
    if not ng:
        raise RuntimeError("ngspice not found (set NGSPICE=/path/to/ngspice)")
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / "model.mod").write_text(_model(corner))
        s = (ROOT / netlist).read_text()
        s = s.replace(".include spice/models/cmos180.mod", f".include {td/'model.mod'}")
        s = re.sub(r"\.param VDD=[\d.]+", f".param VDD={vdd}", s)
        s = re.sub(r"\.temp [\d.-]+", f".temp {temp}", s)
        s = re.sub(r"\.ic .*", ".ic " + " ".join(f"V({n})={vdd if hi else 0}" for n, hi in
                   [("Q1",1),("Q1b",0),("Q2",1),("Q2b",0),("Q3",0),("Q3b",1),("Q4",0),("Q4b",1)]), s)
        data = td / "out.txt"
        s = re.sub(r"wrdata \S+", f"wrdata {data}", s)
        (td / "run.cir").write_text(s)
        p = subprocess.run([ng, "-b", str(td / "run.cir")], cwd=ROOT, capture_output=True, text=True, timeout=300)
        if not data.exists() or data.stat().st_size == 0:
            raise RuntimeError("ngspice produced no output:\n" + p.stdout[-800:] + p.stderr[-400:])
        if keep:
            shutil.copy(data, keep)
        return measure(str(data), vdd, 10e-9)
