#!/usr/bin/env python3
"""Turn the guest-printed GPDK045 Spectre TSV into the results/ files the report builder reads.

Usage:
  gpdk45_from_tsv.py --pvt pvt.tsv --nominal nominal.tsv [--tuning tuning.tsv]
                     --operating-point "fin=.. rl=.. vb=.. cl=.. mult=.."
                     [--netlist spectre/divider_gpdk45.scs] [--outdir results]

Input TSV (tab separated, header first, as cadence/vm/measure_guest.py prints it):
  tag divides f_in_GHz f_out_MHz ratio power_mW delay_ps pdp_fJ max_phase_step_err_deg swing_lo swing_hi
  divides is 0/1 (true/false, yes/no, pass/fail also accepted). Unmeasurable fields are "nan".
  A failed run may be a row  tag<TAB>ERROR<TAB>message.
  Swing columns are measured on node q1 (measure_guest.py), so they map to swing_v["v(q1)"].

Outputs (in --outdir, default <repo>/results):
  gpdk045_pvt_summary.csv    columns required by build_gpdk45_reports.py; FAIL rows kept with a reason
  gpdk045_metrics_tt27.json  nominal point tt_27_1.0; a key the TSV cannot provide is omitted and
                             listed under "unavailable_from_tsv" (the builder then refuses cleanly)
  gpdk045_tuning_grid.csv    only with --tuning; fin, rl, vb, cl, mult parsed from the tag
  gpdk045_provenance.json    model file, section(s), device, netlist SHA-256, operating point, tags

All inputs are validated before anything is written. Exit 2 on bad or missing input.
Units: power in mW, delay in ps, PDP in fJ; mW * ps = fJ, and pdp_fJ is checked against
power_mW * delay_ps within 1 percent.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEVICE = "g45n1svt"
SOURCE = "Cadence Spectre 12.1 (MMSIM121) in CentOS VM"
NOMINAL = "tt_27_1.0"
TSV_HEADER = ["tag", "divides", "f_in_GHz", "f_out_MHz", "ratio", "power_mW", "delay_ps", "pdp_fJ",
              "max_phase_step_err_deg", "swing_lo", "swing_hi"]
NUM_FIELDS = TSV_HEADER[2:]
# Must equal PVT_COLS in build_gpdk45_reports.py.
PVT_COLS = ["Corner", "Temp_C", "VDD_V", "Divides", "f_out_MHz", "Delay_ps", "Power_mW", "PDP_fJ",
            "MaxPhaseStepErr_deg_or_reason"]
TUNE_COLS = ["tag", "fin", "rl", "vb", "cl", "mult", "status", "reason", "f_in_GHz", "f_out_MHz", "ratio",
             "power_mW", "delay_ps", "pdp_fJ", "max_phase_step_err_deg", "swing_lo", "swing_hi"]
# Must equal MET_KEYS in build_gpdk45_reports.py.
MET_KEYS = ["f_in_ghz", "f_out_mhz", "division_ratio", "phase_deg", "phase_steps_deg",
            "max_phase_step_error_deg", "swing_v", "i_avg_ma", "power_mw", "periods_averaged",
            "ck_to_q_delay_ps", "pdp_fj", "vdd_v"]
PVT_RE = re.compile(r"^(tt|ff|ss|fs|sf)_(-?\d+)_(\d+(?:\.\d+)?)$")
TUNE_RE = re.compile(r"^g_([^_]+)_([^_]+)_([^_]+)_([^_]+)_m([^_]+)$")
OP_KEYS = ["fin", "rl", "vb", "cl", "mult"]
TRUE = {"1", "true", "yes", "pass"}
FALSE = {"0", "false", "no", "fail"}
PDP_TOL = 0.01
CORNER_ORDER = ["tt", "ff", "ss", "fs", "sf"]


class BadInput(Exception):
    pass


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def num(txt, where):
    t = txt.strip()
    if t.lower() == "nan":
        return None
    try:
        v = float(t)
    except ValueError:
        raise BadInput(f"{where}: not a number: {txt!r}")
    if not math.isfinite(v):
        raise BadInput(f"{where}: not finite: {txt!r} (use nan for unmeasurable)")
    return v


def read_tsv(path):
    p = pathlib.Path(path)
    if not p.is_file():
        raise BadInput(f"{path} does not exist")
    lines = [l.rstrip("\r") for l in p.read_text().split("\n") if l.strip()]
    if not lines:
        raise BadInput(f"{path} is empty")
    head = lines[0].split("\t")
    if head != TSV_HEADER:
        raise BadInput(f"{path}: header is {head}, expected {TSV_HEADER}")
    rows, seen = [], set()
    for n, line in enumerate(lines[1:], start=2):
        where = f"{path}:{n}"
        f = line.split("\t")
        tag = f[0].strip()
        if not tag:
            raise BadInput(f"{where}: empty tag")
        if tag in seen:
            raise BadInput(f"{where}: duplicate tag {tag}")
        seen.add(tag)
        if len(f) >= 2 and f[1].strip() == "ERROR":
            msg = " ".join("\t".join(f[2:]).split()) or "ERROR (no message)"
            rows.append({"tag": tag, "error": msg, "divides": False})
            continue
        if len(f) != len(TSV_HEADER):
            raise BadInput(f"{where}: {len(f)} fields, expected {len(TSV_HEADER)}")
        d = f[1].strip().lower()
        if d in TRUE:
            divides = True
        elif d in FALSE:
            divides = False
        else:
            raise BadInput(f"{where}: divides must be 0 or 1, got {f[1]!r}")
        r = {"tag": tag, "error": None, "divides": divides}
        for name, txt in zip(NUM_FIELDS, f[2:]):
            r[name] = num(txt, f"{where} {name}")
        check_pdp(where, r)
        rows.append(r)
    return rows


def check_pdp(where, r):
    p, d, pdp = r["power_mW"], r["delay_ps"], r["pdp_fJ"]
    if p is None or d is None or pdp is None:
        return
    calc = p * d  # mW * ps = fJ
    if abs(calc - pdp) > PDP_TOL * max(abs(calc), abs(pdp)):
        raise BadInput(f"{where} {r['tag']}: pdp_fJ {pdp} does not match power_mW*delay_ps = {calc:.4g} "
                       f"(more than 1 percent)")


def fmt_nan(x, spec):
    return "nan" if x is None else format(x, spec)


def clean(msg):
    return " ".join(str(msg).split())


def pvt_line(tag, r):
    m = PVT_RE.match(tag)
    if not m:
        raise BadInput(f"PVT tag {tag!r} is not <corner>_<temp>_<vdd> with corner in {CORNER_ORDER}")
    head = [m.group(1).upper(), str(int(m.group(2))), str(float(m.group(3)))]
    if r["error"] is not None:
        return head + ["FAIL", "", "", "", "", "FAIL: " + clean(r["error"])]
    if not r["divides"]:
        ratio = "" if r["ratio"] is None else f" (ratio {r['ratio']:.3f})"
        return head + ["FAIL", "", "", "", "", f"FAIL: does not divide{ratio}"]
    return head + ["PASS", fmt_nan(r["f_out_MHz"], ".1f"), fmt_nan(r["delay_ps"], ".1f"),
                   fmt_nan(r["power_mW"], ".4f"), fmt_nan(r["pdp_fJ"], ".2f"),
                   fmt_nan(r["max_phase_step_err_deg"], ".2f")]


def pvt_csv(rows):
    out = [PVT_COLS]
    for r in rows:
        out.append(pvt_line(r["tag"], r))
    return out


def nominal_metrics(rows):
    matches = [r for r in rows if r["tag"] == NOMINAL]
    if not matches:
        raise BadInput(f"nominal TSV has no {NOMINAL} row")
    r = matches[0]
    m_tag = PVT_RE.match(NOMINAL)
    vdd = float(m_tag.group(3))
    m = {"tag": NOMINAL, "vdd_v": vdd, "divides": bool(r["divides"] and r["error"] is None),
         "source": SOURCE}
    if r["error"] is not None:
        m["status"], m["reason"] = "FAIL", "FAIL: " + clean(r["error"])
    elif not r["divides"]:
        ratio = "" if r["ratio"] is None else f" (ratio {r['ratio']:.3f})"
        m["status"], m["reason"] = "FAIL", f"does not divide{ratio}"
    else:
        m["status"] = "PASS"
    if r["error"] is None:
        pairs = [("f_in_ghz", r["f_in_GHz"]), ("f_out_mhz", r["f_out_MHz"]),
                 ("division_ratio", r["ratio"]), ("power_mw", r["power_mW"]),
                 ("ck_to_q_delay_ps", r["delay_ps"]), ("pdp_fj", r["pdp_fJ"]),
                 ("max_phase_step_error_deg", r["max_phase_step_err_deg"])]
        for k, v in pairs:
            if v is not None:
                m[k] = v
        if r["swing_lo"] is not None and r["swing_hi"] is not None:
            # measure_guest.py takes the swing on node q1 only.
            m["swing_v"] = {"v(q1)": [r["swing_lo"], r["swing_hi"]]}
        if r["power_mW"] is not None:
            m["i_avg_ma"] = r["power_mW"] / vdd  # P = VDD x I_avg, so mW / V = mA
    m["unavailable_from_tsv"] = [k for k in MET_KEYS if k not in m]
    return m


def tuning_csv(rows):
    out = [TUNE_COLS]
    for r in rows:
        t = TUNE_RE.match(r["tag"])
        if not t:
            raise BadInput(f"tuning tag {r['tag']!r} is not g_<fin>_<rl>_<vb>_<cl>_m<mult>")
        op = list(t.groups())
        if r["error"] is not None:
            status, reason = "FAIL", clean(r["error"])
        elif not r["divides"]:
            status, reason = "FAIL", "does not divide"
        else:
            status, reason = "PASS", ""

        def cell(k):
            return "" if r.get(k) is None else repr(r[k])
        out.append([r["tag"], *op, status, reason] + [cell(k) for k in NUM_FIELDS])
    return out


def parse_operating_point(s):
    kv = {}
    for tok in s.split():
        if "=" not in tok:
            raise BadInput(f"operating point token {tok!r} is not key=value")
        k, v = tok.split("=", 1)
        if k not in OP_KEYS or not v or k in kv:
            raise BadInput(f"operating point: bad or repeated key in {tok!r}; keys are {OP_KEYS}")
        kv[k] = v
    if sorted(kv) != sorted(OP_KEYS):
        raise BadInput(f"operating point must give all of {OP_KEYS}, got {sorted(kv)}")
    return " ".join(f"{k}={kv[k]}" for k in OP_KEYS)


def netlist_info(path):
    p = pathlib.Path(path)
    if not p.is_file():
        raise BadInput(f"netlist {path} does not exist")
    raw = p.read_bytes()
    lines = [l for l in raw.decode("utf-8", "replace").splitlines() if not l.lstrip().startswith("//")]
    inc = None
    for l in lines:
        m = re.match(r'\s*include\s+"([^"]+)"\s+section=(\w+)', l)
        if m:
            inc = m.groups()
            break
    if inc is None:
        raise BadInput(f"netlist {path}: no include \"...\" section=... line")
    if not any(re.search(r"\b" + DEVICE + r"\b", l) for l in lines):
        raise BadInput(f"netlist {path}: device {DEVICE} not found")
    try:
        rel = str(p.resolve().relative_to(ROOT))
    except ValueError:
        rel = str(p.resolve())
    return {"netlist": rel, "model_file": inc[0], "model_file_name": os.path.basename(inc[0]),
            "section": inc[1], "device": DEVICE, "netlist_sha256": hashlib.sha256(raw).hexdigest()}


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def build(args):
    pvt_rows = read_tsv(args.pvt)
    nom_rows = read_tsv(args.nominal)
    tune_rows = read_tsv(args.tuning) if args.tuning else None
    op = parse_operating_point(args.operating_point)
    netinfo = netlist_info(args.netlist)
    metrics = nominal_metrics(nom_rows)

    corners = {PVT_RE.match(r["tag"]).group(1) for r in pvt_rows if PVT_RE.match(r["tag"])}
    corners.add("tt")
    sections = [c for c in CORNER_ORDER if c in corners]
    if tune_rows is not None and netinfo["section"] not in sections:
        sections.append(netinfo["section"])

    tags, seen = [], set()
    for r in pvt_rows + nom_rows + (tune_rows or []):
        if r["tag"] not in seen:
            seen.add(r["tag"])
            tags.append(r["tag"])

    prov = {"source": SOURCE, "device": DEVICE, **netinfo,
            "sections_used": sections, "operating_point": op, "tags": tags,
            # Count of result rows; the builder prints it as "raw result files". The TSV names no raw files.
            "raw_files": tags,
            "input_sha256": {"pvt": sha256_file(args.pvt), "nominal": sha256_file(args.nominal),
                             "tuning": sha256_file(args.tuning) if args.tuning else None}}
    outputs = {
        "gpdk045_pvt_summary.csv": pvt_csv(pvt_rows),
        "gpdk045_metrics_tt27.json": metrics,
        "gpdk045_provenance.json": prov,
    }
    if tune_rows is not None:
        outputs["gpdk045_tuning_grid.csv"] = tuning_csv(tune_rows)
    return outputs


def write_outputs(outdir, outputs):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        path = out / name
        if name.endswith(".csv"):
            with open(path, "w", newline="") as f:
                csv.writer(f).writerows(content)
        else:
            with open(path, "w") as f:
                json.dump(content, f, indent=2, allow_nan=False)
                f.write("\n")
        print(f"wrote {path}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert gpdk045 Spectre TSV output to results/ files.")
    ap.add_argument("--pvt", required=True, help="PVT TSV (tags <corner>_<temp>_<vdd>)")
    ap.add_argument("--nominal", required=True, help="TSV containing the tt_27_1.0 row")
    ap.add_argument("--tuning", help="tuning TSV (tags g_<fin>_<rl>_<vb>_<cl>_m<mult>)")
    ap.add_argument("--operating-point", required=True, help='"fin=.. rl=.. vb=.. cl=.. mult=.."')
    ap.add_argument("--netlist", default=str(ROOT / "spectre" / "divider_gpdk45.scs"))
    ap.add_argument("--outdir", default=str(ROOT / "results"))
    args = ap.parse_args(argv)
    try:
        outputs = build(args)
    except BadInput as e:
        die(str(e))
    write_outputs(args.outdir, outputs)


if __name__ == "__main__":
    main()
