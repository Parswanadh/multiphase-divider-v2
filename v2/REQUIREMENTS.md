# v2 Requirements (REQUIREMENTS.md)

Rule: each requirement needs evidence file path; unknown means unknown.

| ID | Requirement | Rationale | Acceptance criterion | Verification | Evidence file | Priority |
|---|---|---|---|---|---|---|
| SR-01 | Correct divide by two at nominal | Core function | All 8 outputs at f_in/2 within 0.1 pct, swing at least 0.1 V | Test (Spectre tran) | results/gpdk045/final/analysis.json style rerun, v2 rerun log | Must |
| SR-02 | Stated frequency range with limits | v1 shows range depends on sizing | Sweep table lists divide/fail per point plus max phase err | Test (f sweep) | v2 sweep TSV + fig_fsweep successor | Must |
| SR-03 | Phase-step error reported honestly | v1 D 38.46 deg at 1.4 GHz, B 3.78 deg at 6 GHz | Max step error computed by same script for every point | Analysis script | results/gpdk045/final/analysis.json method | Must |
| SR-04 | Power and PDP with stated netlist | Standalone 0.541 mW vs schematic 0.455 mW gap | Report both or pick one with reason; window and periods stated | Test + analysis | results/gpdk045/power_gap_experiment.md successor | Must |
| SR-05 | PVT 45 corners (5 x 3 x 3) on final branch | v1 D 41/45, B 21/45 | Pass/fail table with fail reason per corner | Test (PVT matrix) | report/gpdk045/report_data.json pvt_rows successor | Must |
| SR-06 | Monte Carlo only if model supports it | No MC evidence in v1 | Check PDK spectre model for statistical/mismatch sections first; if absent, SR deferred with reason | Inspection | PDK models dir listing + finding note (unknown today) | Should |
| SR-07 | Layout DRC progress, LVS mismatch list | v1 placement 21/3 rules; routed 134/17; LVS not clean | New routed DLATCH at m=4 R=3k; DRC count and LVS .cls deltas reported | Inspection (Assura) | results/gpdk045/assura_* successor logs | Must |
| SR-08 | No post-layout sim without extraction | PDK copy lacks qrc dir | Post-layout claim allowed only with av_extracted view + sim log | Inspection | cadence/skill/verify/ASSURA_FLOW_NOTES.md + qrc dir listing | Must |
| SR-09 | Every number traceable, one-command rerun | Reproducibility | Each table cell maps to file + command in README/VERIFICATION_MATRIX | Inspection | v2 rerun script + claims register | Must |
| SR-10 | Manuscript within LMWT 4-page format; TechRxiv variant optional | Venue fit | Outline sections map to evidence; no unsupported claim | Inspection + prose audit | paper/ successor + v2/CLAIMS_AUDIT.md | Must |
| SR-11 | Supply and tech stated correctly | v1 is 1.0 V GPDK045, not 1.8 V | All docs say 1.0 V nominal, 0.9/1.1 corners, 45 nm | Inspection | report/gpdk045/report_data.json tool_technology | Must |
| SR-12 | Secret removed from history | PROMPT.md plaintext risk | Credential rotated; history scrubbed or file fixed | Inspection | Git log + backlog item k | Must |

Notes: priority Must means blocks submit; Should means do if VM budget allows.
Unknown today: exact VM minutes per run (estimate from logs only), Monte Carlo model availability,
whether qrc files can be obtained.
