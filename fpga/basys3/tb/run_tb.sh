#!/usr/bin/env bash
#===============================================================================
# run_tb.sh
#
# Compiles and executes the iverilog testbench for the 8-phase divide-by-2
# latch ring demonstrator.
#===============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

RTL_DIR="${BASE_DIR}/rtl"
TB_DIR="${BASE_DIR}/tb"
BUILD_DIR="${BASE_DIR}/build"

mkdir -p "${BUILD_DIR}"

SIM_BIN="${BUILD_DIR}/tb_ring.vvp"

echo "=== Compiling tb_ring with Icarus Verilog ==="
iverilog -g2012 -DSIMULATION \
    -o "${SIM_BIN}" \
    "${RTL_DIR}/latch_ring.v" \
    "${TB_DIR}/tb_ring.v"

echo "=== Executing Simulation ==="
vvp "${SIM_BIN}"
