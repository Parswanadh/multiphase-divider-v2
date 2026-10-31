#!/usr/bin/env bash
# Tests measure_guest.py on a synthetic Spectre nutascii raw file (1.4 GHz clock, 8 phases
# at 45 deg, supply current -0.5 mA + ripple, VDD 1.0 V, non-uniform time grid).
# Runs with the host python; also with python2.6/python2 if present, else a static
# Python 2.6 syntax check.
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$HERE/measure_guest.py"
HOST_PY=${HOST_PY:-/home/parshu/miniconda3/bin/python}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
fail=0
pass() { echo "PASS: $*"; }
bad() { echo "FAIL: $*"; fail=1; }

RAW="$TMP/raws"
mkdir -p "$RAW"

# ---- generate synthetic raw files (host python) ----
"$HOST_PY" - "$RAW" <<'PYGEN' || { echo "FAIL: could not generate raw files"; exit 1; }
import math, random, sys, os
raw_dir = sys.argv[1]
T = 1.0 / 1.4e9            # CK period
TOUT = 2.0 * T             # output period (divide by 2)
TSTOP = 60e-9
rng = random.Random(1)
times = []
t = 0.0
while t < TSTOP:
    times.append(t)
    t += rng.uniform(1e-12, 12e-12)          # non-uniform steps

# output name -> phase index (45 deg steps, Q1 at 0)
PH = [("Q1", 0), ("Q2", 1), ("Q3", 2), ("Q4", 3), ("Q1b", 4), ("Q2b", 5), ("Q3b", 6), ("Q4b", 7)]
NAMES = ["time", "CK"] + [p[0] for p in PH] + ["VDD:p"]

def row(tt):
    vals = [tt, 0.5 + 0.5 * math.sin(2 * math.pi * tt / T)]
    for _, k in PH:
        vals.append(0.5 + 0.5 * math.sin(2 * math.pi * tt / TOUT - 2 * math.pi * k / 8.0))
    vals.append(-0.5e-3 + 0.1e-3 * math.sin(2 * math.pi * tt / T))   # VDD:p current
    return vals

def nutascii_header(f, plotname, names, npts):
    f.write("Title: synthetic divider\n")
    f.write("Date: Sat Oct 31 2026\n")
    f.write("Plotname: %s\n" % plotname)
    f.write("Flags: \n")
    f.write("No. Variables: %d\n" % len(names))
    f.write("No. Points: %d\n" % npts)
    f.write("Variables:\n")
    for i, n in enumerate(names):
        ty = "time" if i == 0 else ("current" if n.upper().startswith("VDD") else "voltage")
        f.write("\t%d\t%s\t%s\n" % (i, n, ty))

good = os.path.join(raw_dir, "tt_27_1.0.raw")
with open(good, "w") as f:
    # a DC plot first, so the transient plot must be picked by name
    f.write("Title: synthetic dc\nDate: x\nPlotname: DC Sweep\nFlags: \n")
    f.write("No. Variables: 2\nNo. Points: 2\nVariables:\n\t0\tv\tvoltage\n\t1\ti\tcurrent\n")
    f.write("Values:\n0\t0.0\n\t0.0\n1\t1.0\n\t1.0\n")
    nutascii_header(f, "Transient Response", NAMES, len(times))
    f.write("Values:\n")
    for k, tt in enumerate(times):
        vals = row(tt)
        f.write("%d\t%.9e\n" % (k, vals[0]))
        for v in vals[1:]:
            f.write("\t%.9e\n" % v)

# a corrupt file: must yield an ERROR row, not a crash
with open(os.path.join(raw_dir, "bad_27_1.0.raw"), "w") as f:
    f.write("this is not a raw file\n")
PYGEN

# ---- run and check ----
check_run() {
  local interp="$1" label="$2"
  local rundir out rc
  rundir=$(mktemp -d "$TMP/run.XXXX")
  out=$(cd "$rundir" && "$interp" "$SCRIPT" "$RAW" 2>"$rundir/err.txt")
  rc=$?
  echo "--- $label: $(basename "$interp") measure_guest.py <raw dir> ---"
  echo "$out"
  [ "$rc" -eq 0 ] && pass "$label exit 0" || bad "$label exit code $rc ($(head -c 300 "$rundir/err.txt"))"

  local row
  row=$(printf '%s\n' "$out" | awk -F'\t' '$1=="tt_27_1.0"')
  if [ -z "$row" ]; then
    bad "$label: no row for tt_27_1.0"
    return
  fi
  local divides ratio power phase
  read -r divides ratio power phase <<EOF
$(echo "$row" | awk -F'\t' '{print $2, $5, $6, $9}')
EOF
  if awk -v r="$ratio" -v p="$power" -v ph="$phase" -v d="$divides" \
      'BEGIN { exit !(d == 1 && r - 2 < 0.01 && 2 - r < 0.01 && p - 0.5 < 0.02 && 0.5 - p < 0.02 && ph < 1.0) }'; then
    pass "$label ratio=$ratio (~2) power=${power} mW (~0.5) phase_err=${phase} deg"
  else
    bad "$label ratio=$ratio power=$power phase_err=$phase divides=$divides"
  fi

  echo "$out" | awk -F'\t' '$1=="bad_27_1.0" && $2=="ERROR" {found=1} END {exit !found}' \
    && pass "$label corrupt file reported as ERROR row" \
    || bad "$label corrupt file not reported as ERROR row"

  [ -s "$rundir/measure_summary.tsv" ] && pass "$label measure_summary.tsv written" \
    || bad "$label measure_summary.tsv missing"
}

check_run "$HOST_PY" "host"

PY26=""
for cand in python2.6 python2; do
  if command -v "$cand" >/dev/null 2>&1; then PY26=$(command -v "$cand"); break; fi
done
if [ -n "$PY26" ]; then
  check_run "$PY26" "py2"
else
  echo "no python2/python2.6 on host: static Python 2.6 compatibility checks instead"
  while IFS= read -r pat; do
    [ -z "$pat" ] && continue
    if grep -nE -- "$pat" "$SCRIPT"; then bad "forbidden pattern for py2.6: $pat"; fi
  done <<'PATS'
\.format\(
argparse
OrderedDict
numpy
\{[^{}]* for [^{}]*\}
['"][^'"]*[{][}]
^[[:space:]]*print[[:space:]]+[^(]
PATS
  [ "$fail" -eq 0 ] && pass "no Python 2.6-incompatible constructs found"
fi

if [ "$fail" -eq 0 ]; then echo "ALL TESTS PASSED"; else echo "SOME TESTS FAILED"; fi
exit "$fail"
