# v2 Verification Matrix (VERIFICATION_MATRIX.md)

Strict division check for every tran row: all 8 outputs at f_in/2 within 0.1 pct,
swing at least 0.1 V. Status is planned until rerun logs exist.

| Req | Test procedure | Tool | Evidence artifact | Automation command | Status |
|---|---|---|---|---|---|
| SR-01 | Nominal tran at 1.4 GHz (D) and 6 GHz (B); rerun U8k | Spectre, measure_guest.py | v2 rerun analysis.json + TSVs | bash cadence/vm/run_gpdk045.sh <dir> grid (FIN/RL/VB/CL/MULT set) | Planned |
| SR-02 | f sweep per sizing until fail; record fmax + phase err | Spectre grid | v2 sweep TSV + fsweep fig | Same grid, FIN list | Planned |
| SR-03 | Phase steps from t_pair method on each passing point | analysis script | v2 analysis.json phase_steps_deg | python3 scripts Jelpp (v2 freeze) | Planned |
| SR-04 | Power over same window; report both netlist variants | Spectre + measure | v2 power gap note successor | power_gap_experiment.md method | Planned |
| SR-05 | 45-corner PVT on final branch | Spectre pvt | v2 pvt TSV + pass table | bash cadence/vm/run_gpdk045.sh <dir> pvt | Planned |
| SR-06 | List PDK model sections; grep statistical/mismatch | Inspection | Finding note with dir listing | ls/grep on guest PDK models dir | Planned |
| SR-07 | Route DLATCH m=4; Assura DRC + LVS | Virtuoso, Assura 4.1 | v2 assura drc/lvs logs | cadence/skill/verify/run_verify.sh DLATCH drc/lvs | Planned |
| SR-08 | Check qrc dir presence; block post-layout claim if absent | Inspection | qrc listing + ASSURA_FLOW_NOTES successor | ls /home/buet/pdk/gpdk045_v_6_0/qrc | Planned |
| SR-09 | Claims register cross-check per table cell | Inspection | CLAIMS_AUDIT.md update | Manual audit | Planned |
| SR-10 | Page count + section-evidence map | Inspection | Draft + outline | Manual | Planned |
| SR-11 | Grep drafts for 1.8 V / 180 nm leakage | Inspection | Audit note | grep -rn prose | Planned |
| SR-12 | Confirm rotation + clean log | Inspection | Git log note | git log -- PROMPT.md | Planned |

Rerun rule: VM calls under flock /home/parshu/vm/vm.lock; record wall time per grid.
