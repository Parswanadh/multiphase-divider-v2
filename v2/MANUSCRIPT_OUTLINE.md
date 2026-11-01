# v2 Manuscript Outline (MANUSCRIPT_OUTLINE.md)

Format: LMWT letter, 4 pages max. Optional TechRxiv version with appendix data.
Framing: 45 nm GPDK045 re-implementation with a sizing rule for load selection,
measured limits, and what the paper rule does and does not do. No overclaim.

## Title options (no overclaim)

1. A 45 nm Re-implementation of an Eight-Phase Divide-by-Two Divider With a Load-Sizing Rule
2. Load-Sizing Limits of a Compact Multiphase Divider in 45 nm CMOS
3. Measured PVT Limits of an Eight-Phase Divide-by-Two Divider in GPDK045

## Section plan

| Section | Claim | Figure/Table | Evidence file | Status |
|---|---|---|---|---|
| Abstract | 45 nm re-impl; stack rule; two measured points; limits | None | analysis.json, pvt_rows | To write |
| I. Intro | Kuo topology; what we test | Fig 1 latch + ring | report_data.json figures | To write |
| II. 45 nm sizing rule | R >= 1.1 x 3Ron/m; paper rule fails at unit size | Table R threshold | LEDGER.md, analysis.json unsized | To write |
| III. Measured nominal | D 1.4 GHz and B 6 GHz numbers with netlist variant | Tran figs, Table metrics | analysis.json D_1p4/B_6g, power_gap_experiment.md | To write |
| IV. Frequency and phase | fmax per sizing; error falls near limit | f sweep fig | report_data.json fsweep notes | To re-measure |
| V. PVT | 45-corner tables; fail modes at 125 C / 0.9 V | PVT heatmaps | report_data.json pvt_rows | To re-measure |
| VI. Headroom/limits | M7 triode 8-68 mV vs 358 mV; swing limits | Tail fig | analysis.json tail min/max | To write |
| VII. Layout status | Placement/routed state, DRC/LVS counts, no extraction | Layout shots | assura_drc/lvs logs, route_dlatch_log.txt | To re-measure |
| VIII. Conclusion | What holds, what fails, one enhancement result | None | v2 sweep TSV | To write |
| Refs | Kuo + tool refs only; benchmarks only if retrieved | None | Kuo 2025, Cadence docs | To write |

## Figures list

F1 latch schematic; F2 ring; F3 D 1.4 GHz tran; F4 B 6 GHz tran; F5 paper-rule fail;
F6 f sweep; F7 phase steps; F8 tail saturation; F9 supply current; F10 PVT maps;
F11 layout + DRC screenshot. Each caption names the evidence file and corner.
Post-layout waveform slot stays empty until extraction exists (backlog d).
