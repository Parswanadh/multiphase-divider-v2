#!/usr/bin/env python3
"""
loop_engine.py: Anthropic Loop Engineering Engine for IEEE Q1 Campaign
Implements Orchestrator-Workers + Evaluator-Optimizer dynamic loop patterns
derived from Anthropic's 'Getting Started with Loops' architecture.

Evaluates progress across a 1-2 week research lifecycle:
- Stage 1: Analytical Modeling & Academic Assignment (15M)
- Stage 2: Loophole Exploitation, V2 Architecture & Lab System Project (40M)
- Stage 3: Monte Carlo Statistical Mismatch & Post-Layout PEX Extraction
- Stage 4: Publication-Grade IEEE Q1 Manuscript & Benchmark Defense
"""

import os
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
ROADMAP_PATH = WORKSPACE / "state" / "q1_roadmap.json"
LOGS_DIR = WORKSPACE / "logs"

def load_roadmap():
    if not ROADMAP_PATH.exists():
        raise FileNotFoundError(f"Roadmap not found at {ROADMAP_PATH}")
    with open(ROADMAP_PATH, "r") as f:
        return json.load(f)

def save_roadmap(data):
    ROADMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ROADMAP_PATH, "w") as f:
        json.dump(data, f, indent=2)

def check_audit(audit_name):
    log_file = LOGS_DIR / f"{audit_name}.log"
    if not log_file.exists():
        return False, "Not started"
    content = log_file.read_text()
    if "AUDIT: PASS" in content:
        return True, "Verified PASS"
    elif "AUDIT: REJECTED" in content:
        return False, "Rejected with punchlist"
    return False, "Incomplete audit"

def evaluate_and_advance():
    roadmap = load_roadmap()
    
    # 1. Evaluate Stage 1: Analytical & Baseline
    s1_pass, s1_reason = check_audit("audit_m1")
    s2_pass, s2_reason = check_audit("audit_m2")
    assignment_doc = WORKSPACE / "report" / "23ECE302_Theory_Assignment.md"
    stage1_complete = s1_pass and assignment_doc.exists()

    # 2. Evaluate Stage 2: V2 Architecture & Lab Project
    s3_pass, s3_reason = check_audit("audit_m3")
    s5_pass, s5_reason = check_audit("audit_m5")
    s6_pass, s6_reason = check_audit("audit_m6")
    lab_doc = WORKSPACE / "report" / "23ECE383_System_Design_Project_Report.md"
    stage2_complete = s3_pass and s5_pass and s6_pass and lab_doc.exists()

    # 3. Evaluate Stage 3: Monte Carlo & Layout PEX
    s4_pass, s4_reason = check_audit("audit_m4")
    gds_file = WORKSPACE / "layout" / "divider_core.gds"
    mc_results = WORKSPACE / "results" / "monte_carlo_phase_error.csv"
    stage3_complete = s4_pass and gds_file.exists() and mc_results.exists()

    # 4. Evaluate Stage 4: IEEE Q1 Manuscript
    s7_pass, s7_reason = check_audit("audit_m7")
    manuscript = WORKSPACE / "paper" / "manuscript_v2.md"
    stage4_complete = s7_pass and manuscript.exists()

    # Update Stage statuses
    stages = roadmap["dynamic_stages"]
    if stage1_complete:
        stages[0]["status"] = "COMPLETED"
        if stages[1]["status"] == "QUEUED":
            stages[1]["status"] = "ACTIVE"
            roadmap["current_stage"] = "STAGE_2_V2_ARCHITECTURE_ENHANCEMENT"
            
    if stage2_complete:
        stages[1]["status"] = "COMPLETED"
        if stages[2]["status"] == "QUEUED":
            stages[2]["status"] = "ACTIVE"
            roadmap["current_stage"] = "STAGE_3_MONTE_CARLO_AND_LAYOUT_PEX"
            
    if stage3_complete:
        stages[2]["status"] = "COMPLETED"
        if stages[3]["status"] == "QUEUED":
            stages[3]["status"] = "ACTIVE"
            roadmap["current_stage"] = "STAGE_4_IEEE_Q1_MANUSCRIPT_AND_PEER_AUDIT"
            
    if stage4_complete:
        stages[3]["status"] = "COMPLETED"
        roadmap["current_stage"] = "ALL_STAGES_COMPLETED"

    # Compute Readiness Percentage (0 - 100%)
    weights = [0.25, 0.35, 0.20, 0.20]
    completion = [
        1.0 if stage1_complete else (0.5 if s1_pass else 0.1),
        1.0 if stage2_complete else (0.5 if s5_pass else 0.0),
        1.0 if stage3_complete else (0.5 if s4_pass else 0.0),
        1.0 if stage4_complete else (0.3 if manuscript.exists() else 0.0)
    ]
    readiness = sum(w * c for w, c in zip(weights, completion)) * 100.0
    roadmap["overall_q1_readiness_pct"] = round(readiness, 2)

    # Academic rubrics check (55 Marks)
    academic_marks = 0
    if assignment_doc.exists(): academic_marks += 15
    if s1_pass: academic_marks += 10
    if s2_pass: academic_marks += 15
    if s3_pass: academic_marks += 5
    if s4_pass: academic_marks += 5
    if s6_pass: academic_marks += 5
    roadmap["north_star_metrics"]["academic_rubric_marks"]["verified"] = min(55, academic_marks)

    save_roadmap(roadmap)

    # Return concise status for watchdog
    result = {
        "current_stage": roadmap["current_stage"],
        "overall_q1_readiness_pct": roadmap["overall_q1_readiness_pct"],
        "academic_marks": f"{roadmap['north_star_metrics']['academic_rubric_marks']['verified']}/55",
        "stage1_complete": stage1_complete,
        "stage2_complete": stage2_complete,
        "stage3_complete": stage3_complete,
        "stage4_complete": stage4_complete,
        "campaign_complete": stage4_complete and academic_marks >= 55
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate_and_advance()
