# v2 Plan: GPDK045 Re-implementation Letter (PLAN.md)

## 1. Executive Summary (10 lines)

1. v1 finished: Kuo divider re-implemented in GPDK045 45 nm at 1.0 V, Spectre-verified.
2. Key v1 finding: paper rule R1 = Ron/2 fails at unit size; stack rule R >= 1.1 x 3Ron/m works.
3. Two measured points exist: Design D 1.4 GHz (41/45 PVT) and Design B 6 GHz (21/45 PVT).
4. M7 is in triode everywhere (Vds 8 to 67 mV vs Vdsat 358 mV); layout is placement only.
5. Early v2 manuscript numbers (cascode, PMOS loads, 0.5 deg, 2.2 mW, 3.2 GHz) have no evidence.
6. v2 goal: one honest, fully measured letter on the 45 nm re-implementation plus one low-risk enhancement.
7. Scope excludes tapeout, extraction (unless PDK files obtained), and unmeasured claims.
8. Single VM lane serializes all Spectre/layout work; host lane parallelizes analysis and writing.
9. First decisions: enhancement choice, venue (LMWT vs TechRxiv), extraction file pursuit.
10. Done means: every number traceable to a rerunnable Spectre or Assura artifact.

## 2. Stakeholders and Needs

| Stakeholder | Need |
|---|---|
| Student authors | Defensible course-to-paper story, no fabricated data |
| Faculty evaluator | Traceable methods, stated limits, clean report |
| LMWT reviewers | Novelty or useful correction, measured PVT, honest comparison |
| TechRxiv readers | Preprint with full data and rerun commands |
| Future maintainers | Rerunnable scripts, file map, known-blocked items |

## 3. Scope and Non-Goals

In scope: re-measurement of v1 corners, one enhancement branch, DRC/LVS progress, manuscript rewrite.
Non-goals: tapeout; post-layout simulation without extraction files; phase-noise claims without pnoise runs;
Monte Carlo claims without a verified mismatch model; any 1.8 V or 180 nm claim for the 45 nm circuit.

## 4. Baseline (v1 Facts With Evidence Paths)

| Fact | Evidence |
|---|---|
| U8k m=1 R=8k divides 1.4 GHz: 0.1375 mW, 62.21 ps, 8.557 fJ, 26.42 deg | results/gpdk045/final/analysis.json (U8k), report/gpdk045/report_data.json |
| Paper rule m=1 R=1.15k fails: 2799.8 MHz, 15.3 mV swing | results/gpdk045/final/analysis.json (unsized), report/gpdk045/LEDGER.md |
| Design D m=4 R=3k 1.4 GHz: 0.5413 mW, 25.99 ps, 38.46 deg; schematic run 0.4554 mW, 26.66 ps | results/gpdk045/final/analysis.json (D_1p4), results/gpdk045/power_gap_experiment.md |
| Design B m=4 R=2k 6 GHz: 0.4929 mW, 27.94 ps, 3.78 deg | results/gpdk045/final/analysis.json (B_6g) |
| M7 triode: Vds 8 to 67 mV vs Vdsat 357.8 mV | report/gpdk045/report_data.json (other_info), results/gpdk045/final/analysis.json |
| PVT D 41/45 at 1.4 GHz; B 21/45 at 6 GHz | report/gpdk045/report_data.json (pvt_rows) |
| Layout placement only; DRC 21 errors / 3 rules; routed 136/137 with 134 DRC / 17 rules; LVS not clean; no RCX | results/gpdk045/assura_drc_dlatch_summary.txt, results/gpdk045/route_dlatch_log.txt, results/gpdk045/assura_lvs_dlatch_baseline.txt, cadence/skill/verify/ASSURA_FLOW_NOTES.md |
| VM: single lane flock, serial channel, 32-bit tools, disk-full history | README.md, cadence/skill/verify/ASSURA_FLOW_NOTES.md |
| PDK copy lacks qrc dir; LVS res 2T vs 3T mismatch | README.md, results/gpdk045/assura_lvs_dlatch_baseline.txt |

## 5. System Context and Constraints

Single Cadence VM lane (CentOS 6.5, IC615 6.1.5, Spectre MMSIM12.1, Assura 4.1) with one keyboard channel;
all guest work serialized under flock /home/parshu/vm/vm.lock. PDK is GPDK045 v6.0 copy without
Assura RCX qrc dir, so no parasitic extraction. Available tools: Virtuoso, SKILL, OCEAN, Spectre, ViVA,
Layout XL, Chip Assembly Router, Assura DRC/LVS. Workers: agy and opencode and Haiku on host lane only.
Supply is 1.0 V nominal (1.1 V rated max), not 1.8 V. Public GitHub repo history may expose a secret in
PROMPT.md; rotation and cleanup required (see RISKS.md).

## 6. Stage Plan With Entry/Exit Gates and Go/No-Go

| Stage | Entry | Work | Exit gate | Go/No-go |
|---|---|---|---|---|
| S0 Decisions | This plan approved | Pick enhancement, venue, extraction pursuit | DECISIONS.log signed | No-go: proceed without decisions |
| S1 Re-baseline | S0 done | Rerun nominal + PVT for chosen branch; freeze metrics script | All SR numbers reproduced, VERIFICATION_MATRIX updated | No-go if division fails at target |
| S2 Enhancement | S1 pass | Build and sweep one enhancement (see TRADE_STUDY.md) | Sweep table + headroom check | No-go if no gain vs cost; fall back to sizing study |
| S3 Layout | S2 done | Route DLATCH m=4 R=3k, fix DRC, push LVS | DRC count down, LVS mismatch list shrinks | No-go on post-layout claims if no extraction |
| S4 Manuscript | S1-S3 evidence | Rewrite to outline; claims register enforced | CLAIMS_AUDIT all supported | No-go: any unsupported number blocks submit |
| S5 Submit | S4 pass | Venue package (LMWT or TechRxiv) | Human approves push | Human decides push |

## 7. Definition of Done

Every number has an evidence file path plus a rerun command. Strict 8-output division check
(f_in/2 within 0.1 percent, swing at least 0.1 V) applied to all runs. PVT matrix reported with
pass list. Layout status stated exactly (placement vs routed, DRC/LVS counts). No 1.8 V, no 180 nm
device sizes, and no unverified v2 numbers in the manuscript.

## 8. Decision Log (Decisions That Must Be Made First)

| ID | Decision | Options | Owner | Status |
|---|---|---|---|---|
| D1 | Enhancement path | Sizing exploration (recommended) vs cascode vs PMOS loads vs interpolator | Human | Open |
| D2 | Venue | LMWT letter (4 pp) vs TechRxiv preprint first, LMWT after | Human | Open |
| D3 | Extraction | Request full PDK qrc files vs accept no post-layout sim | Human | Open |
| D4 | Power reporting | Standalone default-param vs schematic-param (0.541 vs 0.455 mW) as primary | Human | Open |
| D5 | Monte Carlo | Run only if mismatch/statistical model section verified in PDK | Worker check, human ruling | Open |
| D6 | Secret cleanup | Rotate credential, scrub PROMPT.md history | Human | Open |
