#!/usr/bin/env python3
"""Synthetic tests for gpdk45_from_tsv.py (run: /home/parshu/miniconda3/bin/python -I scripts/test_gpdk45_from_tsv.py).

Every CLI call writes to a temporary --outdir. The repo's results/ and report/gpdk045/ are snapshotted
before and after the run and must be unchanged. The real build_gpdk45_reports.py is run on the output with
RESULTS_DIR and REPORT_DIR pointed at temp dirs, so the builder-facing contract is checked directly.
"""
import csv
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PY = "/home/parshu/miniconda3/bin/python"
CLI = HERE / "gpdk45_from_tsv.py"
BUILDER = HERE / "build_gpdk45_reports.py"
REAL_NETLIST = ROOT / "spectre" / "divider_gpdk45.scs"
HEADER = "\t".join(["tag", "divides", "f_in_GHz", "f_out_MHz", "ratio", "power_mW", "delay_ps", "pdp_fJ",
                    "max_phase_step_err_deg", "swing_lo", "swing_hi"])
OP = "fin=1.4 rl=8k vb=0.8 cl=10f mult=1"
MODEL = "/home/buet/pdk/gpdk045_v_6_0/models/spectre/gpdk045.scs"

PVT_ROWS = [
    "tt_27_1.0\t1\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78",
    "ff_-40_1.1\t1\t1.5\t750\t2.0\t2.80\t14.0\t39.2\t0.80\t0.25\t0.75",
    "ss_125_0.9\t0\tnan\tnan\t1.250\tnan\tnan\tnan\tnan\tnan\tnan",
    "fs_27_1.0\tERROR\traw file corrupt: bad header",
    "sf_27_1.0\t1\t1.4\t700\t2.0\t2.5\tnan\tnan\t1.10\t0.2\t0.8",
]
NOMINAL_PASS = ["tt_27_1.0\t1\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78"]
NOMINAL_ERROR = ["tt_27_1.0\tERROR\tno raw produced (spectre exit 1)"]
TUNING_ROWS = [
    "g_1.4_8k_0.8_10f_m1\t1\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78",
    "g_1.4_6k_0.8_10f_m2\t0\tnan\tnan\tnan\tnan\tnan\tnan\tnan\tnan\tnan",
    "g_1.4_8k_0.9_10f_m1\tERROR\tspectre timeout",
]

RESULTS = ROOT / "results"
REPORT_GPDK = ROOT / "report" / "gpdk045"
OUTPUTS = ["gpdk045_pvt_summary.csv", "gpdk045_metrics_tt27.json", "gpdk045_tuning_grid.csv",
           "gpdk045_provenance.json"]

failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def tsv(lines):
    return "\n".join([HEADER] + lines) + "\n"


def write(path, text):
    path.write_text(text)
    return path


def run(args, env_extra=None):
    assert "--outdir" in args, "tests must always pass --outdir"
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run([PY, "-I", str(CLI)] + args, capture_output=True, text=True, env=env)


def snapshot():
    """Files under results/ and report/gpdk045/ with size and mtime, to prove the repo was not touched."""
    snap = {}
    for base in (RESULTS, REPORT_GPDK):
        if base.exists():
            for dp, _, fns in os.walk(base):
                for fn in fns:
                    p = pathlib.Path(dp) / fn
                    st = p.stat()
                    snap[str(p)] = (st.st_size, st.st_mtime_ns)
    return snap


def load_builder():
    spec = importlib.util.spec_from_file_location("build_gpdk45_reports", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_inputs(tmp, pvt=PVT_ROWS, nominal=NOMINAL_PASS, tuning=TUNING_ROWS, netlist_text=None):
    d = tmp / "in"
    d.mkdir(parents=True, exist_ok=True)
    net = write(d / "divider.scs", netlist_text or (
        "// test netlist\nsimulator lang=spectre\n"
        f'include "{MODEL}" section=tt\n'
        "parameters vdd=1.0 rl=8k vb=0.8 cl=10f\n"
        "M1 (a b c d) g45n1svt w=240n l=45n\n"))
    p = write(d / "pvt.tsv", tsv(pvt))
    n = write(d / "nominal.tsv", tsv(nominal))
    t = write(d / "tuning.tsv", tsv(tuning)) if tuning is not None else None
    return p, n, t, net


def cli_args(p, n, t, net, out, op=OP):
    a = ["--pvt", str(p), "--nominal", str(n), "--operating-point", op, "--netlist", str(net), "--outdir", str(out)]
    if t is not None:
        a += ["--tuning", str(t)]
    return a


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.reader(f))


def outdir_files(out):
    return sorted(p.name for p in out.iterdir()) if out.exists() else []


def main():
    before = snapshot()
    before_gpdk = [p for p in OUTPUTS if (RESULTS / p).exists()]
    B = load_builder()
    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix="gpdk45_tsv_test_"))

    # 1. happy path with tuning
    p, n, t, net = make_inputs(tmp_root / "ok")
    out = tmp_root / "ok" / "out"
    r = run(cli_args(p, n, t, net, out))
    check("happy path exits 0", r.returncode == 0, r.stderr)
    check("all four outputs written", outdir_files(out) == sorted(OUTPUTS), str(outdir_files(out)))
    if r.returncode != 0:
        print(r.stderr)

    # 2. PVT summary: header, PASS, FAIL with reason, ERROR as FAIL, nan in a PASS row
    rows = read_csv(out / "gpdk045_pvt_summary.csv")
    check("PVT header matches builder PVT_COLS", rows[0] == B.PVT_COLS, str(rows[0]))
    by = {r[0] + "_" + r[1] + "_" + r[2]: r for r in rows[1:]}
    check("PASS row formatted (tt 27 1.0)", by.get("TT_27_1.0") == [
        "TT", "27", "1.0", "PASS", "700.0", "16.1", "2.3400", "37.67", "1.25"], str(by.get("TT_27_1.0")))
    check("FAIL row keeps reason", by.get("SS_125_0.9", [""] * 9)[8] == "FAIL: does not divide (ratio 1.250)",
          str(by.get("SS_125_0.9")))
    check("ERROR row becomes FAIL with message", by.get("FS_27_1.0", [""] * 9)[8] ==
          "FAIL: raw file corrupt: bad header", str(by.get("FS_27_1.0")))
    check("nan in PASS row written as nan", by.get("SF_27_1.0", [""] * 9)[5] == "nan",
          str(by.get("SF_27_1.0")))
    check("PVT row count", len(rows) - 1 == len(PVT_ROWS), str(len(rows) - 1))
    m = B.build_matrix([dict(zip(rows[0], r)) for r in rows[1:]])[0]
    check("builder build_matrix gives 45 planned rows, none extra", len(m) == 45, str(len(m)))

    # 3. nominal metrics JSON
    met = json.loads((out / "gpdk045_metrics_tt27.json").read_text())
    check("nominal divides is real bool True", met.get("divides") is True, str(met.get("divides")))
    check("nominal swing is on q1", met.get("swing_v", {}).get("v(q1)") == [0.22, 0.78], str(met.get("swing_v")))
    check("nominal i_avg_ma = P / VDD", abs(met["i_avg_ma"] - 2.34) < 1e-9, str(met.get("i_avg_ma")))
    check("no null values in metrics JSON", None not in met.values())
    check("keys TSV cannot give are listed",
          sorted(met["unavailable_from_tsv"]) == ["periods_averaged", "phase_deg", "phase_steps_deg"],
          str(met["unavailable_from_tsv"]))
    builder_missing = sorted(k for k in B.MET_KEYS if k not in met)
    check("builder-missing keys equal unavailable list", builder_missing == sorted(met["unavailable_from_tsv"]),
          str(builder_missing))

    # 4. tuning grid
    tg = read_csv(out / "gpdk045_tuning_grid.csv")
    check("tuning tag parsed", tg[1][:6] == ["g_1.4_8k_0.8_10f_m1", "1.4", "8k", "0.8", "10f", "1"], str(tg[1]))
    check("tuning FAIL row reason", tg[2][6:8] == ["FAIL", "does not divide"], str(tg[2]))
    check("tuning ERROR row kept with message", tg[3][6:8] == ["FAIL", "spectre timeout"], str(tg[3]))

    # 5. provenance
    prov = json.loads((out / "gpdk045_provenance.json").read_text())
    check("provenance device", prov["device"] == "g45n1svt")
    check("provenance model file from include line", prov["model_file"] == MODEL, prov["model_file"])
    check("provenance section", prov["section"] == "tt")
    check("provenance sections used", prov["sections_used"] == ["tt", "ff", "ss", "fs", "sf"],
          str(prov["sections_used"]))
    check("provenance netlist sha256", prov["netlist_sha256"] == hashlib.sha256(net.read_bytes()).hexdigest())
    check("provenance operating point", prov["operating_point"] == OP)
    check("provenance tags", prov["tags"][0] == "tt_27_1.0" and len(prov["tags"]) == len(set(prov["tags"])) and
          "g_1.4_6k_0.8_10f_m2" in prov["tags"], str(prov["tags"]))
    check("provenance source", prov["source"] == "Cadence Spectre 12.1 (MMSIM121) in CentOS VM")
    gate = B.gate(prov)
    check("builder gate accepts provenance", gate is None, str(gate))

    # 6. real netlist (read only) and a second run with no tuning file
    out2 = tmp_root / "real" / "out"
    r2 = run(["--pvt", str(p), "--nominal", str(n), "--operating-point", OP, "--netlist", str(REAL_NETLIST),
              "--outdir", str(out2)])
    check("real netlist run exits 0", r2.returncode == 0, r2.stderr)
    if r2.returncode == 0:
        pr2 = json.loads((out2 / "gpdk045_provenance.json").read_text())
        check("real netlist sha256", pr2["netlist_sha256"] == hashlib.sha256(REAL_NETLIST.read_bytes()).hexdigest())
        check("no tuning csv without --tuning", "gpdk045_tuning_grid.csv" not in outdir_files(out2))

    # 7. builder run on our output, nominal PASS: must refuse cleanly with the missing keys
    rep_pass = tmp_root / "bpass"
    env = {"RESULTS_DIR": str(out), "REPORT_DIR": str(rep_pass)}
    rb = subprocess.run([PY, "-I", str(BUILDER)], capture_output=True, text=True,
                        env={**os.environ, **env})
    check("builder refuses PASS nominal with exit 2", rb.returncode == 2, rb.stderr)
    check("builder names the missing keys", "phase_deg" in rb.stderr and "periods_averaged" in rb.stderr,
          rb.stderr)

    # 8. builder run on our output, nominal FAIL: report written
    p2, n2, t2, net2 = make_inputs(tmp_root / "fail", nominal=NOMINAL_ERROR)
    out3 = tmp_root / "fail" / "out"
    r3 = run(cli_args(p2, n2, t2, net2, out3))
    check("nominal ERROR run exits 0", r3.returncode == 0, r3.stderr)
    rep_fail = tmp_root / "bfail"
    rb2 = subprocess.run([PY, "-I", str(BUILDER)], capture_output=True, text=True,
                         env={**os.environ, "RESULTS_DIR": str(out3), "REPORT_DIR": str(rep_fail)})
    check("builder accepts FAIL nominal (exit 0)", rb2.returncode == 0, rb2.stderr)
    check("builder writes lab report for FAIL nominal",
          (rep_fail / "23ECE383_System_Design_Project_Report_gpdk045.md").exists(), str(rb2.stdout))

    # 9. bad input: exit 2, nothing written
    def expect_bad(label, args_fn):
        d = tmp_root / ("bad_" + label)
        d.mkdir(parents=True)
        p_, n_, t_, net_ = make_inputs(d, **args_fn.get("inputs", {}))
        args = cli_args(p_, n_, t_, net_, d / "out", op=args_fn.get("op", OP))
        for rep in args_fn.get("replace", []):
            args[args.index(rep[0])] = rep[1]
        if args_fn.get("extra_path"):
            args[args.index(str(p_))] = args_fn["extra_path"]
        rr = run(args)
        ok = rr.returncode == 2 and "Traceback" not in rr.stderr and not outdir_files(d / "out")
        check(f"bad input exits 2: {label}", ok, f"rc={rr.returncode} {rr.stderr.strip()[:200]}")
        return rr

    expect_bad("missing pvt file", {"extra_path": str(tmp_root / "nope.tsv")})
    bad_hdr_dir = tmp_root / "badhdr"
    bad_hdr_dir.mkdir()
    bad_hdr = write(bad_hdr_dir / "pvt.tsv", "tag\tdivides\n" + "\n".join(PVT_ROWS) + "\n")
    _, n_, _, net_ = make_inputs(bad_hdr_dir)
    rr = run(cli_args(bad_hdr, n_, None, net_, bad_hdr_dir / "out"))
    check("bad header exits 2", rr.returncode == 2 and "header" in rr.stderr, rr.stderr.strip()[:200])
    expect_bad("no tt_27_1.0 in nominal", {"inputs": {"nominal": ["ff_27_1.0\t1\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78"]}})
    expect_bad("pdp mismatch", {"inputs": {"nominal": ["tt_27_1.0\t1\t1.4\t700\t2.0\t2.34\t16.1\t99.0\t1.25\t0.22\t0.78"]}})
    expect_bad("bad operating point", {"op": "fin=1.4 rl=8k vb=0.8 cl=10f"})
    expect_bad("divides not 0/1", {"inputs": {"pvt": ["tt_27_1.0\tmaybe\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78"]}})
    expect_bad("bad PVT tag", {"inputs": {"pvt": ["xx_27_1.0\t1\t1.4\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78"]}})
    expect_bad("netlist without include", {"inputs": {"netlist_text": "parameters vdd=1.0\n"}})
    expect_bad("non-numeric field",{"inputs": {"pvt": ["tt_27_1.0\t1\tabc\t700\t2.0\t2.34\t16.1\t37.67\t1.25\t0.22\t0.78"]}})

    # 10. repo untouched
    after = snapshot()
    check("repo results/ and report/gpdk045 unchanged", before == after,
          f"changed: {sorted(set(before) ^ set(after))[:3]}")
    check("no gpdk045 output appeared in repo results/",
          [p for p in OUTPUTS if (RESULTS / p).exists()] == before_gpdk)

    print()
    if failures:
        print(f"{len(failures)} FAILED: {failures}")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
