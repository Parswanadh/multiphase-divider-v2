#!/usr/bin/env python3
"""
loop_engine.py: Fast-Track Evaluator-Optimizer Engine for IEEE LMWT
Dynamically evaluates progress across the 7 fast-track milestones:
- M1: Baseline 180nm Circuit & 700MHz Division
- M2: 8-Phase Waveforms, Metrics JSON & 23ECE302 Theory Assignment (15M)
- M3: V2 Enhanced Circuit Design (Cascode Tail, Active Loads, Fmax > 3GHz)
- M4: Multi-Corner PVT Sweep & 23ECE383 Lab System Project (40M)
- M5: Physical Magic Layout & Zero DRC Violations
- M6: IEEE LMWT 4-Page Publication Manuscript & TechRxiv Brief
- M7: Submission Package Release & GitHub Tagging
"""

import os
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
LOGS_DIR = WORKSPACE / "logs"
STATE_DIR = WORKSPACE / "state"

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
    milestones = {m: check_audit(f"audit_m{m}") for m in range(1, 8)}
    
    # Check specific artifact deliverables
    m1_pass = milestones[1][0]
    
    assign_doc = WORKSPACE / "report" / "23ECE302_Theory_Assignment.md"
    m2_pass = milestones[2][0] and assign_doc.exists()
    
    v2_cir = WORKSPACE / "spice" / "divider_v2_enhanced.cir"
    m3_pass = milestones[3][0] and v2_cir.exists()
    
    lab_doc = WORKSPACE / "report" / "23ECE383_System_Design_Project_Report.md"
    pvt_csv = WORKSPACE / "results" / "pvt_summary_table.csv"
    m4_pass = milestones[4][0] and lab_doc.exists() and pvt_csv.exists()
    
    gds_file = WORKSPACE / "layout" / "divider_core.gds"
    m5_pass = milestones[5][0] and gds_file.exists()
    
    manuscript = WORKSPACE / "paper" / "manuscript_lmwt.md"
    m6_pass = milestones[6][0] and manuscript.exists()
    
    m7_pass = milestones[7][0]

    verified_checks = [m1_pass, m2_pass, m3_pass, m4_pass, m5_pass, m6_pass, m7_pass]
    passed_count = sum(1 for c in verified_checks if c)
    readiness_pct = round((passed_count / 7.0) * 100.0, 1)

    # Calculate academic marks (55 marks)
    academic_marks = 0
    if assign_doc.exists() and m2_pass:
        academic_marks += 15
    if m1_pass:
        academic_marks += 10
    if m4_pass:
        academic_marks += 25
    if m5_pass:
        academic_marks += 5
    academic_marks = min(55, academic_marks)

    # Determine current milestone target
    next_m = 1
    for i, p in enumerate(verified_checks, start=1):
        if not p:
            next_m = i
            break
    if passed_count == 7:
        next_m = 7

    result = {
        "verified_milestones": f"{passed_count}/7",
        "next_pending_milestone": f"M{next_m}",
        "readiness_percentage": readiness_pct,
        "academic_marks": f"{academic_marks}/55",
        "target_venue": "IEEE Microwave and Wireless Technology Letters (LMWT)",
        "all_goals_achieved": passed_count == 7
    }

    # Save to state
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_DIR / "loop_status.json", "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    evaluate_and_advance()
