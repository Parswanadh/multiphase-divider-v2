#!/usr/bin/env bash
# ==============================================================================
# run_swarm.sh: Anthropic Loop Engineering Driver for OpenCode Swarm
# ==============================================================================
# Implements Orchestrator-Workers + Evaluator-Optimizer feedback loop.
# Continuously executes, evaluates distance-to-goal, mutates tasks dynamically,
# and pushes progress to GitHub until all North Star targets are 100% achieved.
# ==============================================================================

set -u

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${WORKSPACE_DIR}"

LOGS_DIR="${WORKSPACE_DIR}/logs"
STATE_DIR="${WORKSPACE_DIR}/state"
mkdir -p "${LOGS_DIR}" "${STATE_DIR}" "${WORKSPACE_DIR}/.trash"

DRIVER_LOG="${LOGS_DIR}/swarm_watchdog.log"
OPENCODE_BIN="/home/parshu/.opencode/bin/opencode"

echo "=================================================================" | tee -a "${DRIVER_LOG}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Anthropic Loop Engineering Swarm Driver..." | tee -a "${DRIVER_LOG}"
echo "=================================================================" | tee -a "${DRIVER_LOG}"

# Verify prerequisite EDA tools
for tool in ngspice magic klayout python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[ERROR] Required tool '$tool' not found in PATH." | tee -a "${DRIVER_LOG}"
        exit 1
    fi
done

MAX_ITERATIONS=60
iteration=0

while [ ${iteration} -lt ${MAX_ITERATIONS} ]; do
    iteration=$((iteration + 1))
    
    # 1. EVALUATOR PHASE: Run loop engine to evaluate distance-to-goal & mutate tasks
    EVAL_OUTPUT=$(python3 "${WORKSPACE_DIR}/scripts/loop_engine.py" 2>&1)
    echo "${EVAL_OUTPUT}" | tee -a "${DRIVER_LOG}"
    
    GOAL_DISTANCE=$(echo "${EVAL_OUTPUT}" | grep '"goal_distance_score":' | awk -F': ' '{print $2}' | tr -d ',')
    ALL_ACHIEVED=$(echo "${EVAL_OUTPUT}" | grep '"all_goals_achieved":' | awk -F': ' '{print $2}' | tr -d ',')
    ACTIVE_TASKS=$(echo "${EVAL_OUTPUT}" | grep -A 10 '"active_task_ids":' | grep '"TASK-' | tr -d '", ' | paste -sd ', ' -)

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [Loop Iteration ${iteration}/${MAX_ITERATIONS}] Distance-to-Goal: ${GOAL_DISTANCE}% | Active Tasks: [${ACTIVE_TASKS}]" | tee -a "${DRIVER_LOG}"

    # Check terminal exit condition
    if [ "${ALL_ACHIEVED}" = "true" ] || [ "${GOAL_DISTANCE}" = "0.0" ]; then
        echo "=================================================================" | tee -a "${DRIVER_LOG}"
        echo "[SUCCESS] NORTH STAR GOALS ACHIEVED (Distance = 0.0%)!" | tee -a "${DRIVER_LOG}"
        echo "[SUCCESS] 55/55 ACADEMIC EVALUATION & V2 IEEE MANUSCRIPT VERIFIED." | tee -a "${DRIVER_LOG}"
        echo "=================================================================" | tee -a "${DRIVER_LOG}"
        git add -A
        git commit -m "chore(release): 100% goal achieved via loop engineering swarm" || true
        git push origin main || true
        exit 0
    fi

    # 2. ORCHESTRATOR PHASE: Synthesize dynamic execution brief
    INSTRUCTION="[ANTHROPIC EVALUATOR-OPTIMIZER LOOP ITERATION ${iteration}]
Current Distance-to-Goal: ${GOAL_DISTANCE}%.
Currently Active Dynamic Tasks requiring execution and audit sign-off: [${ACTIVE_TASKS}].
Examine state/loop_ledger.json. Dispatch your specialized subagents (Research Swarm, Implementation Swarm, Validation Swarm) in parallel to execute these tasks.
Demand signed audit logs (logs/audit_m*.log) from the auditor agents. Resolve all defects autonomously without pausing for human input. When done, update git and state."

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dispatching OpenCode agent swarm..." | tee -a "${DRIVER_LOG}"

    # 3. OPTIMIZER PHASE: Execute OpenCode agent session
    if [ ${iteration} -eq 1 ]; then
        "${OPENCODE_BIN}" run --auto --thinking --file "${WORKSPACE_DIR}/PROMPT.md" "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    else
        "${OPENCODE_BIN}" run --continue --auto --thinking "${INSTRUCTION}" 2>&1 | tee -a "${DRIVER_LOG}"
    fi

    # Checkpoint git state after iteration
    git add -A
    git commit -m "chore(loop): completed iteration ${iteration} (goal distance: ${GOAL_DISTANCE}%)" || true
    git push origin main || true

    sleep 3
done

echo "[WARNING] Reached maximum loop iterations (${MAX_ITERATIONS}). Inspect state/loop_ledger.json for remaining tasks." | tee -a "${DRIVER_LOG}"
