#!/usr/bin/env python3
"""Collect gpdk045 PVT Spectre results.

Usage: gpdk45_collect.py RAW_DIR

RAW_DIR holds one entry per corner/temp/vdd point named <tag>.raw (a nutascii file, or a
directory containing one), with tag = <corner>_<temp>_<vdd>, e.g. tt_27_1.0 or ff_-40_1.1.
Each raw is converted (spectre_raw.py) and measured (measure_tran.measure) at the VDD parsed
from its tag. Writes, relative to the repository root:
  results/gpdk045_pvt_summary.csv    one row per tag; failures are kept as FAIL rows
  results/gpdk045_metrics_tt27.json  full measurement for tag tt_27_1.0
  results/gpdk045_provenance.json    model file, section, device and raw file names
Exit 2 if RAW_DIR is missing or has no *.raw entries.
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # python -I does not put the script directory on sys.path
ROOT = os.path.dirname(HERE)
import spectre_raw  # noqa: E402
from measure_tran import measure  # noqa: E402

NETLIST = os.path.join(ROOT, "spectre", "divider_gpdk45.scs")
RESULTS = os.path.join(ROOT, "results")
SETTLE_S = 10e-9
TAG_RE = re.compile(r"^(tt|ff|ss|fs|sf)_(-?\d+)_(\d+(?:\.\d+)?)$")
HEADER = ["Corner", "Temp_C", "VDD_V", "Divides", "f_out_MHz", "Delay_ps", "Power_mW",
          "PDP_fJ", "MaxPhaseStepErr_deg_or_reason"]


def jsonable(x):
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if hasattr(x, "item"):
        return x.item()
    return x


def netlist_provenance():
    """Model file, section and device name, read from the netlist itself."""
    prov = {"netlist": os.path.relpath(NETLIST, ROOT), "model_file": None, "section": None,
            "device": None}
    with open(NETLIST) as f:
        lines = [l for l in f.read().splitlines() if not l.lstrip().startswith("//")]
    for l in lines:
        m = re.match(r'\s*include\s+"([^"]+)"\s+section=(\w+)', l)
        if m:
            prov["model_file"] = m.group(1)
            prov["model_file_name"] = os.path.basename(m.group(1))
            prov["section"] = m.group(2)
            break
    for l in lines:
        m = re.search(r"\b(g45\w+)\b", l)
        if m:
            prov["device"] = m.group(1)
            break
    with open(NETLIST, "rb") as f:
        prov["netlist_sha256"] = hashlib.sha256(f.read()).hexdigest()
    return prov


def collect(raw_dir):
    entries = sorted(e for e in glob.glob(os.path.join(raw_dir, "*.raw")))
    if not entries:
        print(f"ERROR: no <tag>.raw files in {raw_dir}", file=sys.stderr)
        sys.exit(2)
    os.makedirs(RESULTS, exist_ok=True)
    rows, metrics, raw_names = [], {}, []
    with tempfile.TemporaryDirectory() as td:
        for ent in entries:
            name = os.path.basename(ent)
            tag = name[: -len(".raw")]
            raw_names.append(name)
            m = TAG_RE.match(tag)
            if not m:
                rows.append([tag, "", "", "FAIL", "", "", "", "", f"FAIL: bad tag {tag}"])
                continue
            corner, temp, vdd = m.group(1), int(m.group(2)), float(m.group(3))
            table = os.path.join(td, f"{tag}.txt")
            try:
                spectre_raw.convert(ent, table)
                r = measure(table, vdd, SETTLE_S)
            except Exception as exc:  # keep the failure as a row
                reason = f"FAIL: {type(exc).__name__}: {exc}".replace("\n", " ")
                rows.append([corner.upper(), temp, vdd, "FAIL", "", "", "", "", reason])
                if tag == "tt_27_1.0":
                    metrics[tag] = {"tag": tag, "status": "FAIL", "reason": reason}
                continue
            if tag == "tt_27_1.0":
                metrics[tag] = {"tag": tag, "raw_file": name, **jsonable(r)}
            if r.get("divides"):
                rows.append([corner.upper(), temp, vdd, "PASS",
                             f"{r['f_out_mhz']:.1f}", f"{r['ck_to_q_delay_ps']:.1f}",
                             f"{r['power_mw']:.4f}", f"{r['pdp_fj']:.2f}",
                             f"{r['max_phase_step_error_deg']:.2f}"])
            else:
                rows.append([corner.upper(), temp, vdd, "FAIL", "", "", "", "",
                             "FAIL: " + r.get("reason", "does not divide")])

    csv_path = os.path.join(RESULTS, "gpdk045_pvt_summary.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)

    if "tt_27_1.0" not in metrics:
        metrics["tt_27_1.0"] = {"tag": "tt_27_1.0", "status": "FAIL",
                                "reason": "no tt_27_1.0.raw in input directory"}
    with open(os.path.join(RESULTS, "gpdk045_metrics_tt27.json"), "w") as f:
        json.dump(metrics["tt_27_1.0"], f, indent=2)

    prov = netlist_provenance()
    prov["raw_files"] = raw_names
    prov["raw_dir"] = os.path.basename(os.path.normpath(raw_dir))
    with open(os.path.join(RESULTS, "gpdk045_provenance.json"), "w") as f:
        json.dump(prov, f, indent=2)

    npass = sum(1 for r in rows if r[3] == "PASS")
    print(f"wrote {csv_path} ({len(rows)} rows, {npass} PASS, {len(rows)-npass} FAIL)")
    print(f"wrote {os.path.join(RESULTS, 'gpdk045_metrics_tt27.json')}")
    print(f"wrote {os.path.join(RESULTS, 'gpdk045_provenance.json')}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print("usage: gpdk45_collect.py RAW_DIR  (RAW_DIR must exist and contain <tag>.raw)",
              file=sys.stderr)
        sys.exit(2)
    collect(sys.argv[1])
