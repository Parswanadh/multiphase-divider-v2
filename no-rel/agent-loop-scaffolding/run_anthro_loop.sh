#!/usr/bin/env bash
# Anthropic Loop Engineering Runner
# Orchestrator-Workers + Evaluator-Optimizer Continuous Pipeline

WORKSPACE="/home/parshu/vlsi-lab"
cd "$WORKSPACE"

LOGS_DIR="$WORKSPACE/logs/anthro"
mkdir -p "$LOGS_DIR"

LOG_FILE="$LOGS_DIR/anthro_orchestrator.log"

echo "==============================================================================" | tee -a "$LOG_FILE"
echo "[$(date)] Starting Anthropic Loop Engineering Pipeline" | tee -a "$LOG_FILE"
echo "Pattern: Orchestrator-Workers + Evaluator-Optimizer" | tee -a "$LOG_FILE"
echo "Model: opencode-go/iceman-contributor-free" | tee -a "$LOG_FILE"
echo "Mode: Continuous High-Throughput Autonomous Improvement" | tee -a "$LOG_FILE"
echo "==============================================================================" | tee -a "$LOG_FILE"

# Start orchestrator in background
python3 "$WORKSPACE/scripts/anthro_loop/orchestrator.py" >> "$LOG_FILE" 2>&1 &
ORCH_PID=$!
echo "[$(date)] Orchestrator started (PID: $ORCH_PID)" | tee -a "$LOG_FILE"

# Keep running
wait $ORCH_PID
