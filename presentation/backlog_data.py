# presentation/backlog_data.py
"""
12 Backlog Items (a through l) for Multiphase Divider Defense.
"""

BACKLOG_ITEMS = [
    {
        "id": "item-a",
        "letter": "a",
        "title": "Hand-routed, DRC- and LVS-clean layout of DLATCH and divider_core",
        "priority": "High",
        "effort": "3–5 days",
        "status": "Pending",
        "description": "Currently, the layout exists as an unrouted placement of PCells with 21 DRC errors. The automated Chip Assembly Router attempt left 1 unrouted connection on net xs and created 134 DRC errors. Completing a clean manual routing on standard metal grids with proper substrate tap guard-rings is required for tapeout readiness.",
        "rationale": "Layout mark is currently marked 'Partial' (evaluated at 3/5 marks); an LVS-clean routed layout secures full 5/5 physical design marks."
    },
    {
        "id": "item-b",
        "letter": "b",
        "title": "Layout at m = 4 with 3 kΩ poly resistors (current layout is m = 1 with 2 kΩ)",
        "priority": "High",
        "effort": "1–2 days",
        "status": "Pending",
        "description": "The existing placement layout was generated with unit-sized devices (m = 1) and 2 kΩ resistors. To reflect the nominal Design D evaluated in simulation, the layout view must be updated to multiplier m = 4 (or 4 parallel fingers) and 3 kΩ g45rnsnp poly resistors with matched aspect ratios.",
        "rationale": "Ensures complete 1-to-1 fidelity between schematic CDF parameters and physical polygon dimensions."
    },
    {
        "id": "item-c",
        "letter": "c",
        "title": "Post-layout parasitic extraction and simulation (RCX / QRC)",
        "priority": "High",
        "effort": "1 day (after PDK fix)",
        "status": "Blocked",
        "description": "Currently blocked because the local GPDK045 copy lacks the Assura QRC technology files (directory `qrcSetupDir /home/buet/pdk/gpdk045_v_6_0/qrc` is absent). Resolving this requires copying the complete QRC rule directory from the university foundry package, then generating view `av_extracted`.",
        "rationale": "Extracts physical wiring capacitance and resistance to quantify real interconnect delay degradation and phase shifts."
    },
    {
        "id": "item-d",
        "letter": "d",
        "title": "Post-layout waveform capture for final report slot",
        "priority": "Medium",
        "effort": "2 hours",
        "status": "Pending",
        "description": "The formal academic report template contains a dedicated figure slot for post-layout transient simulation waveforms. Once extraction view `av_extracted` is simulated in Spectre, the resulting ViVA waveform strip must be captured and inserted into the report.",
        "rationale": "Fulfills the final placeholder requirement in the academic report rubrics."
    },
    {
        "id": "item-e",
        "letter": "e",
        "title": "ViVA screenshots for baseline, Design B, and PVT cases",
        "priority": "Medium",
        "effort": "4 hours",
        "status": "Pending",
        "description": "In the current report, only Design D at 1.4 GHz features a native Virtuoso ViVA viewer capture (`viva_tran_D_1p4GHz_full.png`). Transient waveform figures for the Unsized Baseline, Design B at 6.0 GHz, and PVT extreme corners are high-resolution Python plots generated from raw Spectre output data.",
        "rationale": "Replacing script plots with native Virtuoso GUI captures ensures uniform presentation visual aesthetics."
    },
    {
        "id": "item-f",
        "letter": "f",
        "title": "Optional: Re-run PVT sweeps on Virtuoso schematic netlist",
        "priority": "Low",
        "effort": "3 hours",
        "status": "Optional",
        "description": "All 45-corner PVT sweeps were executed on the standalone netlist with default foundry device parameters, yielding 0.541 mW typical power and 14.07 fJ PDP for Design D. Re-running the 45-corner matrix on the Virtuoso schematic netlist (which includes STI stress and well proximity parameters) would lower reported power to ~0.455 mW and PDP to ~12.14 fJ.",
        "rationale": "Presents more favorable power metrics while maintaining conservative standalone figures as worst-case baseline."
    },
    {
        "id": "item-g",
        "letter": "g",
        "title": "Testbench schematic cleanup and screenshot",
        "priority": "Low",
        "effort": "2 hours",
        "status": "Pending",
        "description": "Resolve the single remaining schCheck warning on `tb_divider` ('Instance name collides with signal name - VDD'), declutter dense interconnect routing in `divider_core` schematic, and insert a dedicated testbench schematic screenshot into the project documentation.",
        "rationale": "Achieves completely clean 0/0 schCheck across all views and documents stimulus setup."
    },
    {
        "id": "item-h",
        "letter": "h",
        "title": "Install Times New Roman font for PDF compilation",
        "priority": "Low",
        "effort": "30 mins",
        "status": "Pending",
        "description": "The report `.docx` document correctly specifies Times New Roman typography, but Linux LibreOffice headless PDF compilation substitutes Liberation Serif because Microsoft TrueType core fonts (`ttf-mscorefonts-installer`) are not installed on the host OS.",
        "rationale": "Ensures exact typographic matching between the Word master document and compiled PDF print deliverables."
    },
    {
        "id": "item-i",
        "letter": "i",
        "title": "Student administrative details (Names, Reg Nos, Signatures)",
        "priority": "High",
        "effort": "15 mins",
        "status": "Pending",
        "description": "The report title page and declaration section currently maintain placeholder student names, university register numbers, batch identifiers, and formal faculty evaluation signature lines.",
        "rationale": "Mandatory administrative requirement prior to final submission to the university evaluation committee."
    },
    {
        "id": "item-j",
        "letter": "j",
        "title": "Workspace hygiene and stray file cleanup",
        "priority": "Low",
        "effort": "1 hour",
        "status": "Pending",
        "description": "Remove temporary guest run directories, orphaned ISO staging files, intermediate log text dumps, and scratch netlists generated during router debugging to restore repository cleanliness.",
        "rationale": "Maintains an uncluttered repository structure and minimizes storage footprint."
    },
    {
        "id": "item-k",
        "letter": "k",
        "title": "Security remediation: Rotate and purge plaintext VM password",
        "priority": "High",
        "effort": "1 hour",
        "status": "Pending",
        "description": "A plaintext login password exists in the legacy task prompt file (`PROMPT.md`). The guest account password should be rotated, and git history scrubbed or the file updated to use environment variables or local credentials ignored by git.",
        "rationale": "Essential security best practice preventing credential leakage in public or academic git repositories."
    },
    {
        "id": "item-l",
        "letter": "l",
        "title": "Optional: Oral defense presentation slide deck",
        "priority": "Medium",
        "effort": "1 day",
        "status": "Optional",
        "description": "Translate the 12-section explainer and results dashboard into a 15-slide presentation deck (PPTX / Google Slides / Keynote) optimized for a 15-minute viva presentation and defense session.",
        "rationale": "Provides visual companion slides directly aligned with the cheat sheet and talk tracks."
    }
]

print(f"Total backlog items defined: {len(BACKLOG_ITEMS)}")
