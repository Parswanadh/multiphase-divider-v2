#!/usr/bin/env bash
# ==============================================================================
# run_swarm.sh: Autonomous Zero-Human-in-the-Loop Driver for OpenCode Swarm
# ==============================================================================
# This script continuously supervises OpenCode until ALL 7 milestones
# achieve verified AUDIT: PASS sign-offs and all artifacts are pushed to GitHub.
# ==============================================================================

set -u

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${WORKSPACE_DIR}"

LOGS_DIR="${WORKSPACE_DIR}/logs"
mkdir -p "${LOGS_DIR}" "${WORKSPACE_DIR}/.trash"

DRIVER_LOG="${LOGS_DIR}/swarm_watchdog.log"
OPENCODE_BIN="/home/parshu/.opencode/bin/opencode"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Autonomous Zero-Human Swarm Driver..." | tee -a "${DRIVER_LOG}"

# Check prerequisites
for tool in ngspice magic klayout; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[ERROR] Required tool '$tool' not found in PATH." | tee -a "${DRIVER_LOG}"
        exit 1
    fi
done

TOTAL_MILESTONES=7

check_progress() {
    local passed=0
    for m in $(seq 1 ${TOTAL_MILESTONES}); do
        local log_file="${LOGS_DIR}/audit_m${m}.log"
        if [ -f "${log_file}" ] && grep -q "AUDIT: PASS" "${log_file}"; then
            passed=$((passed + 1))
        fi
    done
    echo "${passed}"
}

MAX_ITERATIONS=50
iteration=0

while [ ${iteration} -lt ${MAX_ITERATIONS} ]; do
    iteration=$((iteration + 1))
    current_passed=$(check_progress)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iteration ${iteration}/${MAX_ITERATIONS} | Verified Milestones: ${current_passed}/${TOTAL_MILESTONES}" | tee -a "${DRIVER_LOG}"

    if [ "${current_passed}" -eq "${TOTAL_MILESTONES}" ]; then
        echo "=================================================================" | tee -a "${DRIVER_LOG}"
        echo "[SUCCESS] ALL 7 MILESTONES VERIFIED WITH AUDIT: PASS SIGN-OFFS!" | tee -a "${DRIVER_LOG}"
        echo "=================================================================" | tee -a "${DRIVER_LOG}"
        git add -A
        git commit -m "chore(release): all milestones verified and completed autonomously" || true
        git push origin main || true
        exit 0
    fi

    # Determine prompt instruction based on pending milestones
    INSTRUCTION="You are running in 100% autonomous zero-human-in-the-loop mode. Currently ${current_passed}/${TOTAL_MILESTONES} milestones have verified AUDIT: PASS sign-offs. Immediately execute the next pending milestone(s) using the Research, Implementation, and Validation swarms as specified in PROMPT.md. Demand audit sign-offs from the auditor agents, self-heal any defects, and push to GitHub origin main."

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launching OpenCode agent session..." | tee -a "${DRIVER_LOG}"

    # Execute opencode autonomously
    if [ ${iteration} -eq 1 ]; then
        "${OPENCODE_BIN}" run --auto --thinking --file "${WORKSPACE_DIR}/PROMPT.md" "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    else
        "${OPENCODE_BIN}" run --continue --auto --thinking "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    fi

    sleep 3
done

echo "[WARNING] Reached maximum supervisor iterations (${MAX_ITERATIONS}). Check ${DRIVER_LOG} for details." | tee -a "${DRIVER_LOG}"
