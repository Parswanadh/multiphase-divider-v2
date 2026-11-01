# v2 Trade Study (TRADE_STUDY.md)

## Candidates

| # | Option | What changes | Why considered |
|---|---|---|---|
| E1 | Wider m/R design-space exploration | Sweep m 2-8, R 1-8k, vb 0.8/1.0 at 1.4 and 6 GHz | v1 already shows rule works 5/5; cheapest new data |
| E2 | Regulated cascode tail | Add cascode device(s) over M7 | Early mss claims saturation fix and 180 mV headroom |
| E3 | PMOS active loads | Replace R1/R2 with PMOS | Early mss claims peaking to 3.2 GHz and 45 pct area cut |
| E4 | Tail removal or resize | Drop M7 or change W/L/m | M7 triode everywhere suggests tail is a resistor |
| E5 | Phase interpolation / varactor trim | Extra tuning cells | Early mss claims 0.5 deg |
| E6 | Bias-tuned frequency range | vb or supply trim per band | Cheap range extension without new devices |
| E7 | Body or supply tuning | Back-gate or VDD trim | Listed for completeness |

## Feasibility in 45 nm at 1.0 V (from v1 data)

Headroom: M7 Vds measured 8 to 68 mV transient (report_data.json other_info; analysis.json
xd1_tail min/max), Vdsat 357.8 mV. Available headroom above the tail node is tens of mV.
A cascode stack needs roughly Vdsat x 2 plus margin (about 700 mV), which does not fit under
a 1.0 V supply with the existing 3-stack plus load drop. E2 is therefore high risk without
re-architecting bias and swing; it also adds capacitance at the common-source node.

Regeneration: division needs gm x R1 above 1 with R1 at least 1.1 x 3Ron/m (report_data.json
theory; LEDGER.md 5/5 rule). PMOS loads (E3) replace a well-characterized resistor with a
PVT-sensitive active load and change the loop gain condition; v1 has zero PMOS-load runs,
so E3 needs a new stability and swing characterization, not a drop-in.

Power and phase reasoning from v1: sizing m=1 to m=4 cut delay 62.21 to 25.99 ps but raised
power 0.1375 to 0.5413 mW and worsened phase error 26.42 to 38.46 deg at 1.4 GHz
(report_data.json designs). Phase error falls near each design's frequency limit
(B 3.78 deg at 6 GHz; D 13.8 deg at 5.5 GHz; E 15.2 deg at 7 GHz). This favors E1/E6:
pick the sizing whose limit sits at the target frequency instead of adding tuning cells.

## Scoring Matrix (weights in parentheses)

Scale 1 to 5 (5 best). Score = sum(weight x rating).

| Option | Evidence base (3) | VM cost (2) | Headroom fit (3) | PVT risk (2) | Novelty (1) | Total |
|---|---|---|---|---|---|---|
| E1 sizing exploration | 5 | 5 | 5 | 4 | 2 | 50 |
| E6 bias-tuned range | 4 | 5 | 5 | 3 | 2 | 45 |
| E4 tail resize | 3 | 4 | 4 | 3 | 3 | 38 |
| E3 PMOS loads | 1 | 2 | 2 | 2 | 5 | 22 |
| E2 cascode tail | 1 | 2 | 1 | 2 | 4 | 18 |
| E5 interpolator | 1 | 2 | 3 | 2 | 4 | 24 |
| E7 body/supply | 2 | 3 | 3 | 2 | 2 | 27 |

Weights favor what can actually be measured in the VM lane.

## Recommended Path and Fallback

Recommended: E1 primary (map m/R/vb vs fmax, swing, power, phase error; crown one D-successor
and one B-successor), plus E6 as a cheap add-on (vb trim per band). Fallback if E1 shows no
gain: publish the correction letter (paper rule fails at unit size; stack rule with limits)
with D and B as the two measured points and no new devices.

Explicitly not recommended as primary: E2, E3, E5 (all early-manuscript claims with zero
Spectre evidence and headroom or stability problems at 1.0 V).

## Deciding Experiments (each under VM flock)

| Exp | Question | Sweep | VM cost estimate from logs |
|---|---|---|---|
| X1 | Where is the R threshold per m | m 2,3,4,6 x R 1-8k at 1.4 GHz, vb 1.0 | Grid runs like cadence/vm/run_gpdk045.sh grid; 40 ns tran each; cost unknown in minutes, budget half day per sub-sweep |
| X2 | fmax per shortlist sizing | f 1.4-8 GHz per candidate | Same as v1 fsweep; B/E precedent exists |
| X3 | vb trim effect | vb 0.6-1.0 at fixed m/R | LEDGER.md shows vb 0.8 vs 1.0 shifts threshold 1k; cheap |
| X4 | Cascode probe (only if E2 chosen) | Add ideal cascode, check Vds stack and swing | New schematic + op point; high risk, budget full day |
| X5 | PMOS load probe (only if E3 chosen) | Diode PMOS vs R at same m | New schematic + PVT subset; budget days |
| X6 | Tail resize probe | M7 W/L/m variants, record Vds vs Vdsat | Op-point + tran; budget hours |

VM cost note: logs do not state minutes per run, so costs are relative. Measure and record
wall time for the first grid, then re-budget.
