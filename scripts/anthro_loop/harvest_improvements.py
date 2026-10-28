#!/usr/bin/env python3
"""
Harvest improvements from orchestrator state and apply to artifacts
"""

import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).resolve().parent.parent.parent
STATE_DIR = WORKSPACE / "state" / "anthro"

def harvest():
    latest = STATE_DIR / "latest.json"
    if not latest.exists():
        return
    with open(latest) as f:
        state = json.load(f)
    print(f"Harvesting cycle {state['cycle']} - score {state['evaluation']['score']}")
    
if __name__ == "__main__":
    harvest()
