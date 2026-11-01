# v2 Claims Audit (CLAIMS_AUDIT.md)

Scope: every quantitative or qualitative claim in paper/manuscript_lmwt.md,
paper/manuscript_lmwt.tex, and paper/techrxiv_submission_brief.md.
Verdicts: supported by evidence / unsupported / contradicted by v1 evidence.

## Manuscript claims

| # | Claim (mss) | Verdict | Evidence path / reason |
|---|---|---|---|
| C1 | Regulated cascode tail mirror eliminates M7 issue, Vds at least 180 mV | Unsupported | No cascode schematic or sim in repo; v1 M7 Vds 8-68 mV, Vdsat 358 mV (report_data.json, analysis.json) |
| C2 | Active PMOS loads extend range 100 MHz to 3.2 GHz | Unsupported | No PMOS-load runs; v1 range is D to 5.5 GHz and B to 6 GHz with resistors |
| C3 | 45 percent area reduction vs resistors | Unsupported | No PMOS layout; v1 layout is placement only with DRC errors |
| C4 | Dynamic phase interpolator locks phases 45.0 deg +- 0.5 deg | Unsupported | No interpolator circuit; v1 D 38.46 deg at 1.4 GHz, B 3.78 deg at 6 GHz |
| C5 | Dissipates 2.2 mW from 1.8 V supply | Contradicted | v1 supply 1.0 V nominal (report_data.json); D 0.5413 mW, B 0.4929 mW, U8k 0.1375 mW |
| C6 | 6.02 dB in-band phase-noise reduction | Unsupported | No pnoise run in repo |
| C7 | FoM_phi 282.0, best among eight dividers | Unsupported | FoM uses unmeasured power and area; benchmark table values not verified |
| C8 | Eight-design benchmark table (Cho, Jang, Herzel, Jiang, Ahmed, Kim, Dekate) | Unsupported | Numbers copied without retrieval evidence; needs source check |
| C9 | 180 nm CMOS (tex abstract) | Contradicted | Work is GPDK045 45 nm (report_data.json tool_technology, README.md) |
| C10 | M1-M6 0.9/0.18 um, tail 1.8/0.36 um | Contradicted | v1 uses 240 nm/45 nm and 480 nm/90 nm (report_data.json) |
| C11 | PVT TT/FF/SS at 1.62/1.80/1.98 V, delay 91-171 ps, power 1.98-2.72 mW | Contradicted | v1 PVT is 5 corners x temps x 0.9/1.0/1.1 V; D delay 23-31 ps, power 0.25-1.08 mW |
| C12 | Output swing above 800 mV | Contradicted | v1 Q1 swing: D 0.4344 V, B 0.1349 V, U8k 0.2289 V (analysis.json) |
| C13 | Core area 0.000415 mm2 | Unsupported | No measured clean layout area; DLATCH bbox only |
| C14 | Post-layout effects minimal, common-centroid | Unsupported | Layout placement only, LVS not clean, no extraction |
| C15 | Fixes Kuo 1.5k loads and 100 MHz-1.4 GHz framing | Contradicted in part | Kuo is 1.4 GHz point with its own sizing; v1 paper-rule test used 1.15k at 45 nm |
| C16 | Title: enhanced divider with cascode and active loads | Unsupported | Describes unbuilt circuit; retitle required |

## TechRxiv brief claims

100 MHz-3.2 GHz, 0.5 deg, 2.2 mW: all unsupported (same as C2/C4/C5). Preprint timeline
1-2 days: process claim, keep only if TechRxiv current docs confirm.

## What must be deleted or re-measured

Delete or rewrite: C1-C8, C13-C14, C16 until Spectre or Assura evidence exists.
Correct: C5, C9-C12, C15 to v1 values with evidence paths. Re-measure for v2:
actual fmax per sizing, phase error per point, power with stated netlist, PVT table,
DRC/LVS counts, and any new-device claim only after its own sweep.

## Claims Register Rule Set

1. No number enters the manuscript without an evidence file path and a rerun command.
2. Each figure caption names the evidence file and corner.
3. Power figures state netlist variant (standalone vs schematic params) and window.
4. Phase error states method (t_pair steps) and strict 8-output check.
5. PVT claims list all 45 corners with fail reasons; no corner hiding.
6. Layout claims state view name, DRC rule counts, and LVS .cls summary.
7. Benchmark rows need retrieved source values, not copied table entries.
8. v1-to-v2 deltas cite both old and new evidence files.
