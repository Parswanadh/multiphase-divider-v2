#!/usr/bin/env python3
"""
loop_engine.py: Anthropic Loop Engineering Engine
Implements Orchestrator-Workers + Evaluator-Optimizer feedback loop.
Dynamically inspects environmental artifacts, evaluates distance-to-goal,
and mutates tasks towards the advanced publication & academic deliverables.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).resolve().parent.parent
LEDGER_PATH = WORKSPACE / "state" / "loop_ledger.json"
LOGS_DIR = WORKSPACE / "logs"

def load_ledger():
    if not LEDGER_PATH.exists():
        raise FileNotFoundError(f"Ledger file not found at {LEDGER_PATH}")
    with open(LEDGER_PATH, "r") as f:
        return json.load(f)

def save_ledger(data):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2)

def check_audit_pass(milestone_num):
    log_file = LOGS_DIR / f"audit_m{milestone_num}.log"
    if not log_file.exists():
        return False, "File does not exist"
    content = log_file.read_text()
    if "AUDIT: PASS" in content:
        return True, "Signed off with AUDIT: PASS"
    elif "AUDIT: REJECTED" in content:
        return False, "Rejected by auditor"
    return False, "Audit log incomplete"

def evaluate_and_mutate():
    ledger = load_ledger()
    ledger["current_iteration"] += 1
    iteration = ledger["current_iteration"]
    
    # 1. Evaluate Milestone Audits & Progress
    milestone_checks = {m: check_audit_pass(m) for m in range(1, 8)}
    
    # Calculate rubric score
    rubrics = ledger["north_star_goal"]["academic_evaluation"]["rubrics"]
    if milestone_checks[1][0]:
        rubrics["theory_assignment_implementation"]["verified"] = 7
        rubrics["theory_assignment_sizing"]["verified"] = 8
        rubrics["system_project_functionality"]["verified"] = 10
    if milestone_checks[2][0]:
        rubrics["system_project_power"]["verified"] = 5
        rubrics["system_project_delay"]["verified"] = 5
        rubrics["system_project_pdp"]["verified"] = 5
    if milestone_checks[3][0]:
        rubrics["system_project_pvt"]["verified"] = 5
    if milestone_checks[4][0]:
        rubrics["system_project_layout"]["verified"] = 5
    if milestone_checks[6][0]:
        rubrics["system_project_report"]["verified"] = 5

    total_verified = sum(item["verified"] for item in rubrics.values())
    academic_complete = total_verified >= 55
    if academic_complete:
        ledger["north_star_goal"]["academic_evaluation"]["status"] = "COMPLETED"

    # Evaluate V2 Paper goals
    v2_status = ledger["north_star_goal"]["publication_v2_paper"]
    metrics_file = WORKSPACE / "results" / "metrics_baseline.json"
    v2_table = WORKSPACE / "results" / "v2_comparison_table.csv"
    manuscript = WORKSPACE / "paper" / "manuscript_v2.md"

    if milestone_checks[5][0] and v2_table.exists():
        v2_status["status"] = "VERIFIED_READY"

    # Calculate overall Goal Distance Score (0 to 100)
    passed_milestones = sum(1 for m, (passed, _) in milestone_checks.items() if passed)
    goal_distance = max(0.0, 100.0 - (passed_milestones / 7.0 * 80.0) - (20.0 if manuscript.exists() else 0.0))
    ledger["goal_distance_score"] = round(goal_distance, 2)

    # 2. Dynamic Task Mutation (Anthropic Evaluator-Optimizer Pattern)
    active_ids = {t["id"] for t in ledger["active_dynamic_tasks"]}
    completed_ids = {t["id"] for t in ledger["completed_dynamic_tasks"]}
    
    # Check if active tasks completed
    new_active = []
    for task in ledger["active_dynamic_tasks"]:
        task_id = task["id"]
        # Match milestone to task
        done = False
        if "BASELINE" in task_id and milestone_checks[1][0]:
            done = True
        elif "RESEARCH" in task_id and (WORKSPACE / "research" / "enhancement_strategy.md").exists():
            done = True
        elif "METRICS" in task_id and milestone_checks[2][0]:
            done = True
        elif "PVT" in task_id and milestone_checks[3][0]:
            done = True
        elif "LAYOUT" in task_id and milestone_checks[4][0]:
            done = True
        elif "V2-ENHANCED" in task_id and milestone_checks[5][0]:
            done = True
        elif "REPORTS" in task_id and milestone_checks[6][0]:
            done = True
        elif "MANUSCRIPT" in task_id and milestone_checks[7][0]:
            done = True
            
        if done:
            task["status"] = "COMPLETED"
            task["completed_iteration"] = iteration
            ledger["completed_dynamic_tasks"].append(task)
        else:
            new_active.append(task)
            
    ledger["active_dynamic_tasks"] = new_active
    active_ids = {t["id"] for t in ledger["active_dynamic_tasks"]}
    completed_ids = {t["id"] for t in ledger["completed_dynamic_tasks"]}

    # Dynamically inject next-tier tasks based on environmental feedback
    candidate_tasks = [
        {
            "id": "TASK-03-EXTRACT-METRICS",
            "category": "implementation",
            "title": "Compute 8-phase waveforms, power (2.34mW), delay, and PDP",
            "assigned_agent": "pvt-metrics-runner",
            "auditor_agent": "data-integrity-verifier",
            "status": "READY",
            "dependencies": ["TASK-01-BASELINE-NETLIST"]
        },
        {
            "id": "TASK-04-PVT-SWEEP",
            "category": "implementation",
            "title": "Automate multi-corner PVT sweep across TT/FF/SS, -40C to 125C, 1.8V±10%",
            "assigned_agent": "pvt-metrics-runner",
            "auditor_agent": "data-integrity-verifier",
            "status": "READY",
            "dependencies": ["TASK-03-EXTRACT-METRICS"]
        },
        {
            "id": "TASK-05-MAGIC-LAYOUT",
            "category": "implementation",
            "title": "Implement Magic VLSI common-centroid 2-finger layout with zero DRC errors",
            "assigned_agent": "layout-engineer",
            "auditor_agent": "circuit-auditor",
            "status": "READY",
            "dependencies": ["TASK-01-BASELINE-NETLIST"]
        },
        {
            "id": "TASK-06-V2-ENHANCED-DIVIDER",
            "category": "implementation",
            "title": "Implement V2 divider with cascode tail mirror, active PMOS loads, and phase alignment",
            "assigned_agent": "circuit-engineer",
            "auditor_agent": "circuit-auditor",
            "status": "READY",
            "dependencies": ["TASK-02-RESEARCH-ENHANCEMENT", "TASK-03-EXTRACT-METRICS"]
        },
        {
            "id": "TASK-07-ACADEMIC-REPORTS",
            "category": "academic",
            "title": "Compile 23ECE302 Theory (15M) & 23ECE383 Lab System Project (40M) reports",
            "assigned_agent": "academic-author",
            "auditor_agent": "rubric-compliance-officer",
            "status": "READY",
            "dependencies": ["TASK-03-EXTRACT-METRICS", "TASK-04-PVT-SWEEP", "TASK-05-MAGIC-LAYOUT"]
        },
        {
            "id": "TASK-08-IEEE-MANUSCRIPT",
            "category": "publication",
            "title": "Draft complete IEEE Letters manuscript with Table I comparative benchmarking",
            "assigned_agent": "research-author",
            "auditor_agent": "data-integrity-verifier",
            "status": "READY",
            "dependencies": ["TASK-06-V2-ENHANCED-DIVIDER", "TASK-07-ACADEMIC-REPORTS"]
        }
    ]

    for cand in candidate_tasks:
        c_id = cand["id"]
        if c_id not in active_ids and c_id not in completed_ids:
            # Check if dependencies are satisfied
            deps_met = all(dep in completed_ids for dep in cand["dependencies"])
            if deps_met:
                ledger["active_dynamic_tasks"].append(cand)
                ledger["dynamic_mutation_history"].append({
                    "iteration": iteration,
                    "action": "SPAWNED_TASK",
                    "task_id": c_id,
                    "reason": "Dependencies satisfied in closed loop"
                })

    save_ledger(ledger)
    
    print(json.dumps({
        "iteration": iteration,
        "goal_distance_score": ledger["goal_distance_score"],
        "academic_score_verified": f"{total_verified}/55",
        "active_tasks_count": len(ledger["active_dynamic_tasks"]),
        "completed_tasks_count": len(ledger["completed_dynamic_tasks"]),
        "active_task_ids": [t["id"] for t in ledger["active_dynamic_tasks"]],
        "all_goals_achieved": ledger["goal_distance_score"] == 0.0
    }, indent=2))

if __name__ == "__main__":
    evaluate_and_mutate()
