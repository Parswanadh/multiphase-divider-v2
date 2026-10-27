#!/usr/bin/env bash
# ==============================================================================
# run_swarm.sh: Anthropic Proactive Loop Driver for IEEE Q1 Research Campaign
# ==============================================================================
# Implements Anthropic's "Getting Started with Loops" architecture:
# - Goal-based loop with quantitative, verifiable stop conditions
# - Evaluator-Optimizer feedback loop between Implementers and Adversarial Auditors
# - Dynamic task adaptation across a 1-2 week research lifecycle
# - Continuous GitHub check-pointing after each verified milestone
# ==============================================================================

set -u

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${WORKSPACE_DIR}"

LOGS_DIR="${WORKSPACE_DIR}/logs"
STATE_DIR="${WORKSPACE_DIR}/state"
mkdir -p "${LOGS_DIR}" "${STATE_DIR}" "${WORKSPACE_DIR}/.trash"

DRIVER_LOG="${LOGS_DIR}/swarm_watchdog.log"
OPENCODE_BIN="/home/parshu/.opencode/bin/opencode"

echo "==============================================================================" | tee -a "${DRIVER_LOG}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Anthropic Q1 Research Swarm Loop Engine..." | tee -a "${DRIVER_LOG}"
echo "==============================================================================" | tee -a "${DRIVER_LOG}"

# Verify EDA prerequisites
for tool in ngspice magic klayout python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[ERROR] Required EDA tool '$tool' not found in PATH." | tee -a "${DRIVER_LOG}"
        exit 1
    fi
done

MAX_CYCLES=100
cycle=0

while [ ${cycle} -lt ${MAX_CYCLES} ]; do
    cycle=$((cycle + 1))
    
    # 1. EVALUATOR PHASE: Evaluate progress towards Q1 North Star and academic rubrics
    EVAL_OUTPUT=$(python3 "${WORKSPACE_DIR}/scripts/loop_engine.py" 2>&1)
    echo "${EVAL_OUTPUT}" | tee -a "${DRIVER_LOG}"
    
    CURRENT_STAGE=$(echo "${EVAL_OUTPUT}" | grep '"current_stage":' | awk -F': ' '{print $2}' | tr -d '",')
    READINESS=$(echo "${EVAL_OUTPUT}" | grep '"overall_q1_readiness_pct":' | awk -F': ' '{print $2}' | tr -d ',')
    ACADEMIC_MARKS=$(echo "${EVAL_OUTPUT}" | grep '"academic_marks":' | awk -F': ' '{print $2}' | tr -d '",')
    CAMPAIGN_COMPLETE=$(echo "${EVAL_OUTPUT}" | grep '"campaign_complete":' | awk -F': ' '{print $2}' | tr -d ',')

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Cycle ${cycle}/${MAX_CYCLES}] Stage: ${CURRENT_STAGE} | Q1 Readiness: ${READINESS}% | Academic Marks: ${ACADEMIC_MARKS}" | tee -a "${DRIVER_LOG}"

    # Terminal stop condition
    if [ "${CAMPAIGN_COMPLETE}" = "true" ] || [ "${READINESS}" = "100.0" ]; then
        echo "==============================================================================" | tee -a "${DRIVER_LOG}"
        echo "[SUCCESS] IEEE Q1 CAMPAIGN COMPLETE (100% Readiness, 55/55 Academic Marks)!" | tee -a "${DRIVER_LOG}"
        echo "==============================================================================" | tee -a "${DRIVER_LOG}"
        git add -A
        git commit -m "chore(release): IEEE Q1 manuscript and 55M academic deliverables complete" || true
        git push origin main || true
        exit 0
    fi

    # 2. ORCHESTRATOR PHASE: Synthesize dynamic execution brief for OpenCode
    INSTRUCTION="[ANTHROPIC LOOP ENGINEERING CYCLE ${cycle}]
Current Research Stage: ${CURRENT_STAGE} (Q1 Readiness: ${READINESS}%, Academic Marks: ${ACADEMIC_MARKS}).
Review state/q1_roadmap.json and PROMPT.md.
Execute the active deliverables for ${CURRENT_STAGE} using your parallel subagents:
- If Stage 1: Calibrate baseline 180nm SPICE netlist, extract 8-phase waveforms, and generate 23ECE302 Theory Report (15M).
- If Stage 2: Implement V2 cascode tail mirror, active PMOS loads, phase tuning, multi-corner PVT sweep, and 23ECE383 Lab Report (40M).
- If Stage 3: Run Monte Carlo statistical mismatch (Vth/L dispersion) and extract Magic post-layout PEX netlist.
- If Stage 4: Draft full IEEE Q1 manuscript (manuscript_v2.md) and Table I state-of-the-art benchmarks.
Demand signed audit logs (logs/audit_m*.log) from your adversarial validation agents.
Auto-resolve all engineering choices and commit/push to GitHub origin main."

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dispatching OpenCode agent session..." | tee -a "${DRIVER_LOG}"

    # 3. OPTIMIZER PHASE: Run OpenCode session
    if [ ${cycle} -eq 1 ]; then
        "${OPENCODE_BIN}" run --auto --thinking --file "${WORKSPACE_DIR}/PROMPT.md" "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    else
        "${OPENCODE_BIN}" run --continue --auto --thinking "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    fi

    # Commit progress to GitHub
    git add -A
    git commit -m "chore(q1-campaign): cycle ${cycle} progress in ${CURRENT_STAGE} (${READINESS}% ready)" || true
    git push origin main || true

    sleep 3
done

echo "[WARNING] Reached maximum supervisor cycles (${MAX_CYCLES}). Check logs and state/q1_roadmap.json." | tee -a "${DRIVER_LOG}"
