#!/usr/bin/env bash
#===============================================================================
# run_yosys_synth.sh
#
# Synthesizes the top module using Yosys synth_xilinx targeting Xilinx 7-series.
#===============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

YOSYS="/home/parshu/miniconda3/bin/yosys"
LOG_FILE="${BASE_DIR}/build/yosys_synth.log"

echo "=== Running Yosys Synthesis Check (top -> synth_xilinx) ==="
"${YOSYS}" -p "
    read_verilog ${BASE_DIR}/rtl/latch_ring.v ${BASE_DIR}/rtl/top.v
    synth_xilinx -top top
    stat
" > "${LOG_FILE}" 2>&1

echo "Yosys synthesis completed successfully. Log written to ${LOG_FILE}"
echo ""
echo "=== Tail of Synthesis Log ==="
tail -n 35 "${LOG_FILE}"
