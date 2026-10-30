#!/usr/bin/env bash
# run_spectre.sh: run the divider netlist in Spectre, export waveforms.txt, then measure.
# UNTESTED: written without Cadence access. Items marked VERIFY must be checked on your install.
#
# Usage (from your work directory, where a copy of the netlist lives):
#   ./run_spectre.sh [netlist.scs]          default netlist: divider_gpdk45.scs
# Override any setting by env var, e.g.:  FIN=2e9 WIN_STOP=40e-9 ./run_spectre.sh
#
# Outputs: rawdir/ (psfbin), run.log (spectre), export_ocean.log, waveforms.txt, measure_ocean.log
# Exit status: 0 only if spectre ran, the tran results exist, and waveforms.txt has the right header.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
NETLIST="${1:-divider_gpdk45.scs}"
RAW="${RAW:-rawdir}"
LOG="${LOG:-run.log}"
OUT="${OUT_FILE:-waveforms.txt}"

# settings shared with the .ocn scripts (keep FIN equal to the netlist's fin, VDD to its vdd)
export RESULTS_DIR="$RAW" OUT_FILE="$OUT"
export FIN="${FIN:-1e9}" VDD="${VDD:-1.0}"
export T_START="${T_START:-0}" T_STOP="${T_STOP:-40e-9}" DT="${DT:-5e-12}"
export WIN_START="${WIN_START:-10e-9}" WIN_STOP="${WIN_STOP:-40e-9}"
export OCEAN_BATCH=1

fail() { echo "run_spectre: FAILED: $*" >&2; exit 1; }

[[ -f "$NETLIST" ]] || { echo "run_spectre: no netlist '$NETLIST' in $(pwd)" >&2; exit 2; }
command -v spectre >/dev/null || { echo "run_spectre: spectre not on PATH (VERIFY: module load / cadence env)" >&2; exit 2; }
command -v ocean   >/dev/null || { echo "run_spectre: ocean not on PATH (VERIFY: cadence env)" >&2; exit 2; }

rm -rf "$RAW" "$LOG" "$OUT"

# VERIFY flags: -format psfbin (binary PSF), -raw DIR (result directory), +log FILE (log file)
spectre -format psfbin -raw "$RAW" "$NETLIST" +log "$LOG"

# spectre returns nonzero on hard errors (set -e above). Also look for the summary line.
# VERIFY the exact summary text on your version.
grep -qi "completed with 0 errors" "$LOG" || echo "run_spectre: WARNING: no '0 errors' summary in $LOG" >&2

# results must exist. VERIFY the tran file name: spectre writes <analysis>.<analysis>.<...>
compgen -G "$RAW/*tran*" >/dev/null || fail "no tran results in $RAW/"

# export: OCEAN reads the results and writes $OUT. Ocean's own exit status is not trusted;
# waveforms.txt is validated below.
ocean -nograph -restore "$HERE/export_waveforms.ocn" < /dev/null 2>&1 | tee export_ocean.log || true
[[ -s "$OUT" ]] || fail "$OUT was not written (see export_ocean.log)"

EXPECT="time v(ck) v(q1) v(q2) v(q3) v(q4) v(q1b) v(q2b) v(q3b) v(q4b) i(vdd)"
[[ "$(head -n 1 "$OUT")" == "$EXPECT" ]] || fail "header of $OUT does not match the required format"
grep -qi "nan" "$OUT" && fail "$OUT contains nan values (see export_ocean.log)"

# measurement printed to the CIW log and to measure_ocean.log
ocean -nograph -restore "$HERE/measure_divider.ocn" < /dev/null 2>&1 | tee measure_ocean.log || true
grep -q "division ratio" measure_ocean.log || fail "measurement did not complete (see measure_ocean.log)"

echo "run_spectre: done. Copy $OUT to the host and run:  python3 scripts/measure_tran.py $OUT 1.0 10"
