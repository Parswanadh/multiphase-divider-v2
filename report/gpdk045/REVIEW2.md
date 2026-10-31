# Independent Review 2: System Design Project Report (Frozen Audit)

Audit of frozen report text extracted from the final PDF at `/home/parshu/.claude/jobs/30217dfb/tmp/frozen/report_frozen.txt` (668 lines, 28 pages). Ground truth verified against simulation datasets, TSVs, logs, and verification summaries in `results/gpdk045/`.

---

## Number mismatches

Sorted by severity:

| Severity | Parameter & Stated Value | Line | Ground Truth Source File | Ground Truth Value | Analysis & Discrepancy Details |
|---|---|---|---|---|---|
| **High** | OCEAN Q1 voltage swing: `0.713–1.006 V` | 184 | `results/gpdk045/ocean_schematic_run.txt` | Not recorded in file | **Unverifiable number from results directory.** The log file `ocean_schematic_run.txt` records only edge crossing timestamps (`t1..t3`, `ck1..ck2`) and average current (`Iavg = -0.3896 mA`). The voltage swing is not captured in any file under `results/gpdk045/`. |
| **Medium** | Table 3 PDP with sizing: `14.067 fJ` | 251 | `results/gpdk045/final/D_1p4.tsv` & `analysis.json` | Recomputed: `14.068 fJ` | **Table arithmetic discrepancy (-0.001 fJ).** Multiplying displayed Table 3 values ($0.5413\text{ mW} \times 25.99\text{ ps}$) yields $14.0684\text{ fJ}$. The printed value $14.067\text{ fJ}$ was calculated before rounding from raw values ($0.541337\text{ mW} \times 25.985127\text{ ps} = 14.06678\text{ fJ}$). |
| **Medium** | Table 3 PDP without sizing: `8.557 fJ` | 251 | `results/gpdk045/final/U8k.tsv` & `analysis.json` | Recomputed: `8.554 fJ` | **Table arithmetic discrepancy (+0.003 fJ).** Multiplying displayed Table 3 values ($0.1375\text{ mW} \times 62.21\text{ ps}$) yields $8.5539\text{ fJ}$. The printed value $8.557\text{ fJ}$ comes from TSV calculation using unrounded power ($0.137549\text{ mW} \times 62.21\text{ ps} = 8.55692\text{ fJ}$). |
| **Medium** | Design B (6 GHz) PDP: `13.768 fJ` | 362, 526 | `results/gpdk045/final/B_6g.tsv` & `analysis.json` | Recomputed: `13.772 fJ` | **Arithmetic discrepancy (-0.004 fJ).** Multiplying stated Power ($0.4929\text{ mW}$) by Delay ($27.94\text{ ps}$) yields $13.7716\text{ fJ}$. Value $13.768\text{ fJ}$ derives from unrounded raw values ($0.492869\text{ mW} \times 27.93523\text{ ps} = 13.76849\text{ fJ}$). |
| **Low** | Table 6 PDP arithmetic: 9 corner rows | 612–656 | `results/gpdk045/final/pvt_D.tsv` | $\Delta = \pm 0.01\text{ fJ}$ vs displayed | **Displayed column product mismatch in 9 rows:** `tt_-40_1.0` ($24.01 \times 0.6892 = 16.55$ vs 16.54), `ff_-40_1.0` ($24.66 \times 0.8104 = 19.98$ vs 19.99), `ff_-40_1.1` ($25.20 \times 1.0784 = 27.18$ vs 27.17), `ff_27_1.0` ($25.97 \times 0.6467 = 16.79$ vs 16.80), `ff_125_0.9` ($31.05 \times 0.3074 = 9.54$ vs 9.55), `ss_27_1.1` ($25.27 \times 0.6476 = 16.36$ vs 16.37), `fs_-40_1.0` ($24.08 \times 0.7669 = 18.47$ vs 18.46), `fs_27_1.0` ($25.59 \times 0.6098 = 15.60$ vs 15.61), `sf_-40_1.1` ($24.03 \times 0.8837 = 21.24$ vs 21.23). Caused by copying `pdp_fJ` from TSV (unrounded power) rather than multiplying displayed rounded columns. |
| **Low** | Table 6 `tt_125_0.9` note swing: `0.034 V` | 618 | `results/gpdk045/final/pvt_D.tsv` | `0.035 V` (`reason` col) | In TSV `reason`, swing is $0.035\text{ V}$ ($0.8279 - 0.7934 = 0.0345\text{ V}$). Table 6 truncates $0.0345\text{ V}$ to $0.034\text{ V}$ instead of standard rounding to $0.035\text{ V}$. |

### Arithmetic and Counts Verification Summary
- **Table 3 Arithmetic Check:** Stated ratios hold exactly: delay reduction $62.21 / 25.99 = 2.3936\times \approx 2.39\times$; power increase $0.5413 / 0.1375 = 3.9367\times \approx 3.94\times$; PDP increase $14.067 / 8.557 = 1.6439\times \approx 1.64\times$.
- **PVT Summary Pass Counts:** 
  - Table 4 (Design D at 1.4 GHz): 41 PASS, 4 FAIL out of 45 corners ($91.1\%$ yield). Matches `results/gpdk045/final/pvt_D.tsv` and `pvt_summary_D_1p4.json` cell-by-cell (FAIL corners: `tt_125_0.9`, `ss_125_0.9`, `fs_125_0.9`, `sf_125_0.9`).
  - Table 5 (Design B at 6.0 GHz): 21 PASS, 24 FAIL out of 45 corners ($46.7\%$ yield). Matches `results/gpdk045/final/pvt_B6.tsv` and `pvt_summary_B_6g.json` cell-by-cell (-40 °C: 2 fail; 27 °C: 7 fail; 125 °C: 15 fail).
- **Physical Metrics Verification:**
  - $R_{\text{on}} = 2.3\text{ k}\Omega$; unit stack $= 6.90\text{ k}\Omega$; regeneration threshold $R_1 \ge 7.59\text{ k}\Omega$; m=4 stack $= 1.72\text{ k}\Omega$; threshold band $1.88\text{--}2.25\text{ k}\Omega$ (verified against `LEDGER.md` and `unsized_baseline.tsv`).
  - $V_{\text{dsat}} = 0.3578\text{ V}$ (extracted BSIM4 parameter in `D_1p4.m7op.txt`). Peak transient tail voltages: $66.9\text{ mV}$ (D), $67.1\text{ mV}$ (U8k), $66.2\text{ mV}$ (B); all confirmed in triode.
  - Assura DRC on DLATCH: exactly 21 real errors across 3 rules (Rule 220: 1; Rule 221: 6; Rule 595: 14; verified against `assura_drc_dlatch_summary.txt`).

---

## Inconsistencies

Sorted by severity:

| Severity | Issue | Lines | Description & Evidence |
|---|---|---|---|
| **High** | Erroneous Table Reference for Design B PVT | 364–365 | In "Design B operating point", text states: *"Peak tail voltage reaches 66.2 mV, below Vdsat = 357.8 mV (triode, Figure 14). PVT results appear in Table 4."* Table 4 is the summary for **Design D at 1.4 GHz**. The PVT results for Design B at 6 GHz are in **Table 5**. |
| **High** | Non-existent "ratio" Column Reference | 402–403 | In PVT analysis, text states: *"In Table 4, ratio is f_in/f_out (ratio 2 denotes correct division; 0.5 denotes outputs at 2 f_in)."* Table 4 contains only Process Corner, Temperature, and Supply Voltage with `PASS`/`FAIL` entries. There is no `ratio` column in Table 4. |
| **Medium** | Non-standard Section Heading Format | 176 | The section heading `Simulation driven directly from the Virtuoso schematic (OCEAN)` is in title-case without a colon, whereas all official template headings are uppercase ending with a colon (`SCREENSHOT OF ...:`). |
| **Medium** | Duplicate Text in Table Captions | 278–279, 301 | Table 4 title repeats the pass count: `... (41 of 45 pass; FAIL at 125 °C, 0.9 V for tt, ss, fs, sf) (41 of 45 corners pass)`. Table 5 title duplicates the count: `... (21 of 45 pass) (21 of 45 corners pass)`. |
| **Low** | Tool & Technology Cites Figure 8 instead of Figure 2 | 114–115 | Text cites `Figure 1 and Figure 8` for DLATCH and ring schematics. Figure 2 (page 5) is the primary Virtuoso divider core schematic, yet it is never cited in the body text; the text bypasses it and points directly to supplementary Figure 8 (page 16). |

*Note on Layout & Sizing Consistency:* The layout description is internally consistent across all sections (Lines 334, 339, 347, 514, 543, 562): it is consistently described as placement-only, unrouted, unit-size ($m=1$), with 21 DRC errors and no post-layout simulation.

---

## Writing

Sorted by severity:

| Severity | Line | Offender Quote | Category | One-Line Rewrite |
|---|---|---|---|---|
| **High** | 597–599 | `Evidence file: results/gpdk045/ocean_schematic_run.txt`<br>`Evidence file: cadence/ocean/run_schematic_tb.ocn`<br>`Evidence file: results/gpdk045/virtuoso_netlist_tb_divider.scs` | File names in References | Delete lines 597–599, or replace with: *Cadence Virtuoso Schematic and OCEAN Simulation Testbench, divider_lib, 2026.* |
| **High** | 120 | `... and input 1.4 GHz (tt, 27 C, VDD = 1 V, g_1.4G_8k_1.0_10f_m1). All eight outputs ...` | Leaked batch run tag | `... and 1.4 GHz input under nominal conditions (tt corner, 27 °C, VDD = 1.0 V). All eight outputs ...` |
| **High** | 109–110 | `Simulation dataset: "Transient Analysis `tran': time = (0 s -> 40 ns)" (12:25:58 PM, Sat Oct 31, 2026).` | Raw simulator log banner | `Simulations were conducted using 40 ns transient analysis runs in Cadence Spectre.` |
| **High** | 196–199, 532–535 | `sizing cuts delay from 62.21 ps (U8k) to 25.99 ps (D) (2.39x) and increases swing from 0.2289 V to 0.4344 V. Power rises from 0.1375 mW to 0.5413 mW (3.94x), PDP from 8.557 fJ to 14.067 fJ (1.64x), and phase-step error from 26.42 deg to 38.46 deg at 1.4 GHz.` | Verbatim repeated paragraph | For line 532–535: `Compared to the baseline, transistor sizing reduces delay by 2.39x and increases swing to 0.4344 V, trading off 3.94x higher power and 1.64x PDP.` |
| **High** | 339, 347–348 | `The layout is placement only: it is not routed, and LVS and post-layout simulation were not run.` | Verbatim repeated sentence | For line 347–348: `Interconnect routing, LVS matching, and post-layout extraction were not implemented for this placement study.` |
| **Medium** | 390–394, 397–401 | `... tt_27_0.9, tt_125_0.9, tt_125_1.0, tt_125_1.1, ff_125_0.9, ff_125_1.0, ff_125_1.1, ss_27_0.9, ss_125_0.9, ss_125_1.0, ss_125_1.1, fs_125_0.9, fs_125_1.0, fs_125_1.1, sf_27_0.9, sf_125_0.9, sf_125_1.0, sf_125_1.1 ...` | Raw simulation tags dump | `For Design B at 1.4 GHz, 18 corners fail (3 at 27 °C/0.9 V and all 15 at 125 °C), as enumerated in Table 5.` |
| **Medium** | 346–347 | `Cell divider_core places XD1 R0, XD2 MY, XD3 MX, XD4 R180 with a 1 um gap (clock-star length 98.62 um each).` | Tool transformation jargon | `Divider core places four DLATCH instances in a 2x2 mirrored quad layout with a 1.0 µm channel gap and matched clock lines.` |
| **Medium** | 413–418 | `Figure index. Primary figures 1 to 7 cover schematics, waveforms, and layout. Figures 8 onwards provide supplementary validation: ring architecture (Figure 8), paper sizing waveforms (Figure 9) ...` | Meta-document filler | Delete paragraph, or replace with: `Supplementary validation figures (Figures 8–23) provide extended sweeps, corner distributions, and layout diagnostics.` |
| **Medium** | 507–508 | `Figure 21: Virtuoso Command Interpreter Window (CIW) log confirming gpdk045 library initialization.` | Tool console log filler | `Figure 21: Cadence Virtuoso CIW startup transcript demonstrating GPDK045 library loading.` |
| **Medium** | 549–552, 570–571 | `Compilation failure in Spectre AHDL/CMI module compilation for the gpdk045 BSIM4 model. 32-bit simulation environment compatibility ...` | IT infrastructure log | `Configured host compiler toolchain and 32-bit runtime libraries to resolve Spectre BSIM4 model compilation.` |
| **Low** | 86, 119, 196, 266 | `Baseline U8k at 1.4 GHz gives 71.42 and 18.59 deg ...` | Unexplained abbreviation | `The unsized baseline divider (m = 1, R = 8 kΩ) at 1.4 GHz produces phase steps of 71.42° and 18.59°.` |
| **Low** | 343 | `(segW 0.8 um, segL 7.855 um, 200 ohm/sq, target 2000 ohm).` | PDK parameter names | `(segment width W = 0.8 µm, segment length L = 7.855 µm, sheet resistance 200 Ω/sq, target resistance 2000 Ω).` |
| **Low** | 156, 218, 359, 501 | `Schematic check: DLATCH 0/0, divider_core 0/0, tb_divider 0/1 errors/warnings.` | Cryptic check shorthand | `Schematic checks: 0 errors/0 warnings for DLATCH and divider_core; 0 errors/1 warning for tb_divider.` |
| **Low** | 83 | `... yielding phase step a = 180 t_pair f_in degrees, alternating with 90 - a degrees.` | Non-standard variable | `... yielding phase step Δϕ = 180 × t_pair × f_in degrees, alternating with (90° − Δϕ).` |
| **Low** | 185–188 | `Several caveats apply to this run: the testbench bias was set to 0.8 V rather than 1.0 V, only Q1 was checked in this script, and the verification remains a nominal single-corner check.` | Defensive log phrasing | `This initial OCEAN testbench checked nominal 1 GHz operation at vb = 0.8 V prior to comprehensive multi-corner verification.` |

---

## Verdict

The frozen report's core electrical numbers and PVT counts rigorously match the Cadence Virtuoso/Spectre dataset, but the report requires corrections for one unverifiable swing number, minor PDP display roundoff deltas, two incorrect table cross-references (Table 4 vs Table 5 and the phantom `ratio` column), and removal of leaked batch script tags, raw simulation failure dumps, and repository file paths from the references.
