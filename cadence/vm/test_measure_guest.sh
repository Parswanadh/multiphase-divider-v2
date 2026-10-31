#!/usr/bin/env bash
# Tests measure_guest.py on synthetic Spectre nutascii raw files (1.4 GHz clock, 8 phases
# at 45 deg, supply current -0.5 mA + ripple, VDD 1.0 V, non-uniform time grid):
#   tt_27_1.0      (a) clean divide-by-2                  -> divides=1, phases/steps filled
#   glitch_27_1.0  (b) Q3b only a 20 mV ripple            -> divides=0, reason: swing/toggling
#   approx_27_1.0  (c) f_out = 0.5 f_in * (1 +- 0.4%)      -> divides=0, reason: ratio
#   bad_27_1.0     corrupt file                            -> ERROR row
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

def write_raw(path, tout, q3b_ripple):
    # tout: output period; q3b_ripple: Q3b only wiggles by +-10 mV around 0.5 V (20 mV swing)
    def row(tt):
        vals = [tt, 0.5 + 0.5 * math.sin(2 * math.pi * tt / T)]
        for name, k in PH:
            amp = 0.010 if (q3b_ripple and name == "Q3b") else 0.5
            vals.append(0.5 + amp * math.sin(2 * math.pi * tt / tout - 2 * math.pi * k / 8.0))
        vals.append(-0.5e-3 + 0.1e-3 * math.sin(2 * math.pi * tt / T))   # VDD:p current
        return vals
    with open(path, "w") as f:
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

write_raw(os.path.join(raw_dir, "tt_27_1.0.raw"), TOUT, False)
write_raw(os.path.join(raw_dir, "glitch_27_1.0.raw"), TOUT, True)
write_raw(os.path.join(raw_dir, "approx_27_1.0.raw"), TOUT * 1.004, False)

# a corrupt file: must yield an ERROR row, not a crash
with open(os.path.join(raw_dir, "bad_27_1.0.raw"), "w") as f:
    f.write("this is not a raw file\n")
PYGEN

# ---- run and check ----
# field <row text> <tag> <col>: column <col> of the row for <tag> ("MISSING" if absent)
field() {
  printf '%s\n' "$1" | awk -F'\t' -v t="$2" -v c="$3" '$1==t {print $c; f=1} END {if (!f) print "MISSING"}'
}

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

  # (a) clean divide-by-2 with 45 deg steps: divides=1, phases/steps filled, reason ok
  local d_a ph_a st_a np_a i_a rs_a
  d_a=$(field "$out" tt_27_1.0 2)
  ph_a=$(field "$out" tt_27_1.0 12)
  st_a=$(field "$out" tt_27_1.0 13)
  np_a=$(field "$out" tt_27_1.0 14)
  i_a=$(field "$out" tt_27_1.0 15)
  rs_a=$(field "$out" tt_27_1.0 16)
  if [ "$d_a" = 1 ] && [ "$rs_a" = ok ] && [ "$np_a" -gt 0 ] 2>/dev/null && \
     awk -v p="$ph_a" -v s="$st_a" -v i="$i_a" 'BEGIN {
        np = split(p, pa, ","); ns = split(s, sa, ",")
        if (np != 8 || ns != 8) exit 1
        for (k = 1; k <= np; k++) if (pa[k] !~ /^q[1-4]b?:-?[0-9]+\.[0-9]+$/) exit 1
        for (k = 1; k <= ns; k++) { dd = sa[k] - 45; if (dd < 0) dd = -dd; if (dd >= 0.5) exit 1 }
        dd = i - 0.5; if (dd < 0) dd = -dd; if (dd >= 0.02) exit 1
        exit 0 }'; then
    pass "$label (a) clean: divides=1, 8 phases and 8 steps ~45 deg, periods=$np_a i_avg=${i_a} mA, reason ok"
  else
    bad "$label (a) clean case: divides=$d_a reason=$rs_a phases=$ph_a steps=$st_a periods=$np_a i_avg=$i_a"
  fi

  # extra fields are nan for non-dividing rows
  nan_extras() {
    local c
    for c in 12 13 14 15; do
      [ "$(field "$out" "$1" "$c")" = nan ] || return 1
    done
    return 0
  }

  # (b) Q3b with only a 20 mV swing: divides=0, reason names Q3b and swing/toggling
  local d_b rs_b
  d_b=$(field "$out" glitch_27_1.0 2)
  rs_b=$(field "$out" glitch_27_1.0 16)
  if [ "$d_b" = 0 ] && printf '%s' "$rs_b" | grep -qE 'q3b.*(swing|toggl)' \
     && nan_extras glitch_27_1.0; then
    pass "$label (b) Q3b glitch-only: divides=0, reason=\"$rs_b\""
  else
    bad "$label (b) Q3b glitch-only case: divides=$d_b reason=$rs_b"
  fi

  # (c) f_out = 0.5 f_in only to 0.4%: divides=0, reason names the ratio
  local d_c rs_c
  d_c=$(field "$out" approx_27_1.0 2)
  rs_c=$(field "$out" approx_27_1.0 16)
  if [ "$d_c" = 0 ] && printf '%s' "$rs_c" | grep -q 'ratio' \
     && nan_extras approx_27_1.0; then
    pass "$label (c) approx 0.5 ratio: divides=0, reason=\"$rs_c\""
  else
    bad "$label (c) approximate ratio case: divides=$d_c reason=$rs_c"
  fi
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
