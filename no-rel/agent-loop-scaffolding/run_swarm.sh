#!/usr/bin/env bash
# ==============================================================================
# run_swarm.sh: Fast-Track Autonomous Swarm Runner for IEEE LMWT
# ==============================================================================
# Executes OpenCode continuously across the 7 milestones until all 7 audit
# gates pass and the complete IEEE LMWT submission package is pushed to GitHub.
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
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Fast-Track IEEE LMWT Swarm Loop Engine..." | tee -a "${DRIVER_LOG}"
echo "==============================================================================" | tee -a "${DRIVER_LOG}"

# Verify EDA tools
for tool in ngspice magic klayout python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[ERROR] Required tool '$tool' not found in PATH." | tee -a "${DRIVER_LOG}"
        exit 1
    fi
done

MAX_CYCLES=50
cycle=0

while [ ${cycle} -lt ${MAX_CYCLES} ]; do
    cycle=$((cycle + 1))
    
    # 1. EVALUATOR PHASE: Evaluate progress
    EVAL_OUTPUT=$(python3 "${WORKSPACE_DIR}/scripts/loop_engine.py" 2>&1)
    echo "${EVAL_OUTPUT}" | tee -a "${DRIVER_LOG}"
    
    PASSED_COUNT=$(echo "${EVAL_OUTPUT}" | grep '"verified_milestones":' | awk -F': ' '{print $2}' | tr -d '",')
    NEXT_M=$(echo "${EVAL_OUTPUT}" | grep '"next_pending_milestone":' | awk -F': ' '{print $2}' | tr -d '",')
    READINESS=$(echo "${EVAL_OUTPUT}" | grep '"readiness_percentage":' | awk -F': ' '{print $2}' | tr -d ',')
    ACADEMIC_MARKS=$(echo "${EVAL_OUTPUT}" | grep '"academic_marks":' | awk -F': ' '{print $2}' | tr -d '",')
    ALL_DONE=$(echo "${EVAL_OUTPUT}" | grep '"all_goals_achieved":' | awk -F': ' '{print $2}' | tr -d ',')

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Cycle ${cycle}/${MAX_CYCLES}] Verified: ${PASSED_COUNT} | Target: ${NEXT_M} | Readiness: ${READINESS}% | Academic: ${ACADEMIC_MARKS}" | tee -a "${DRIVER_LOG}"

    # Terminal stop condition
    if [ "${ALL_DONE}" = "true" ] || [ "${READINESS}" = "100.0" ]; then
        echo "==============================================================================" | tee -a "${DRIVER_LOG}"
        echo "[SUCCESS] IEEE LMWT SUBMISSION PACKAGE & 55M ACADEMIC DELIVERABLES COMPLETE!" | tee -a "${DRIVER_LOG}"
        echo "==============================================================================" | tee -a "${DRIVER_LOG}"
        git add -A
        git commit -m "chore(release): complete IEEE LMWT 4-page paper and 55M academic reports" || true
        git push origin main || true
        exit 0
    fi

    # 2. ORCHESTRATOR PHASE: Synthesize instruction for OpenCode
    INSTRUCTION="[FAST-TRACK EXECUTION CYCLE ${cycle}]
Current Status: ${PASSED_COUNT} milestones verified (Readiness: ${READINESS}%, Academic Marks: ${ACADEMIC_MARKS}).
Next Active Milestone to execute and verify: ${NEXT_M}.
Read PROMPT.md carefully. Dispatch your specialized subagents (circuit-engineer, pvt-metrics-runner, layout-engineer, academic-author, research-author) in parallel.
Demand signed audit logs (logs/audit_m*.log with AUDIT: PASS) from your validation auditors.
Execute immediately without pausing for human input, and push changes to GitHub origin main."

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dispatching OpenCode agent session..." | tee -a "${DRIVER_LOG}"

    # 3. OPTIMIZER PHASE: Run OpenCode session
    if [ ${cycle} -eq 1 ]; then
        "${OPENCODE_BIN}" run --auto --thinking --file "${WORKSPACE_DIR}/PROMPT.md" "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    else
        "${OPENCODE_BIN}" run --continue --auto --thinking "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    fi

    # Checkpoint git state after iteration
    git add -A
    git commit -m "chore(fast-track): completed cycle ${cycle} (active: ${NEXT_M}, readiness: ${READINESS}%)" || true
    git push origin main || true

    sleep 3
done

echo "[WARNING] Reached maximum supervisor cycles (${MAX_CYCLES}). Check logs." | tee -a "${DRIVER_LOG}"
