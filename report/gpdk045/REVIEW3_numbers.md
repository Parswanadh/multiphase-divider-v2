# Independent Review 3: Quantitative and Structural Audit of Report Text

This audit evaluates the frozen 29-page report text (`/home/parshu/.claude/jobs/30217dfb/tmp/qa/report.txt`, 672 lines) against ground-truth simulation results, logs, and data files located in `results/gpdk045/` (`final/*.tsv`, `final/analysis.json`, `pvt_*.tsv`, `assura_drc_dlatch_*.txt`, `ocean_schematic_run_1p4GHz_D.txt`, `power_gap_experiment.md`, `wire_schematics_log.txt`, `route_dlatch_log.txt`) and `report/gpdk045/report_data.json`.

---

## 1. Table of Defects (Sorted by Severity)

| Severity | Defect / Issue | Location | Stated Value | Source / Ground Truth Value | Analysis & Discrepancy Description |
|---|---|---|---|---|---|
| **Medium** | Non-existent Table Column Reference | Page 14, Lines 6–7 | *"In Table 6 (Appendix), ratio is f_in/f_out (ratio 2 denotes correct division; 0.5 denotes outputs at 2 f_in)."* | Table 6 contains: `Corner`, `Temp (°C)`, `VDD (V)`, `Divides`, `f_out (MHz)`, `Delay (ps)`, `Power (mW)`, `PDP (fJ)`, `Note` | **Text references non-existent column.** Table 6 does not contain a `ratio` column. It presents `Divides` (`PASS`/`FAIL`) and `f_out (MHz)`. While `ratio` is a column in the underlying data file `results/gpdk045/final/pvt_D.tsv`, it was excluded from the rendered report table. |
| **Low** | Minor Swing Truncation vs. Rounding | Page 27, Table 6 row `tt_125_0.9` Note column | `swing 0.034 V < 0.1 V` | `results/gpdk045/final/pvt_D.tsv` `reason` col: `0.035 V` | **Truncation discrepancy.** Differential swing is $V_{\text{max}} - V_{\text{min}} = 0.8279\text{ V} - 0.7934\text{ V} = 0.0345\text{ V}$. Standard rounding yields $0.035\text{ V}$ (as recorded in the TSV reason string); the table note truncates to $0.034\text{ V}$. |
| **Low** | Displayed Table Arithmetic vs. Unrounded PDP | Page 9 (Table 3), Pages 2, 13, 24–25 (Design B text), Pages 27–28 (Table 6) | Table 3 With Sizing PDP: `14.067 fJ`; Table 3 Without Sizing PDP: `8.557 fJ`; Design B PDP: `13.768 fJ`; Table 6 (9 corner rows) | Recomputed from displayed rounded columns: Table 3 With Sizing: $0.5413 \times 25.99 = 14.068\text{ fJ}$; Without Sizing: $0.1375 \times 62.21 = 8.554\text{ fJ}$; Design B: $0.4929 \times 27.94 = 13.772\text{ fJ}$ | **Display rounding artifact.** Stated PDPs exactly match products of unrounded raw values: $0.541337\text{ mW} \times 25.985127\text{ ps} = 14.06678\text{ fJ} \approx 14.067\text{ fJ}$; $0.137549\text{ mW} \times 62.21\text{ ps} = 8.55692\text{ fJ} \approx 8.557\text{ fJ}$; $0.492869\text{ mW} \times 27.93523\text{ ps} = 13.76849\text{ fJ} \approx 13.768\text{ fJ}$. In Table 6, 9 rows differ by $\pm 0.01\text{ fJ}$ when multiplying rounded columns due to direct TSV copying. Note below Table 3 explicitly clarifies this. |
| **Low** | Proof Figure Mapping vs. Data Source | Page 9, Table 3 ($f_{\text{in}}$, $f_{\text{out}}$, Output swing) | `Fig. 5 (with)` cited as proof for Design D $f_{\text{in}}$, $f_{\text{out}}$, and swing ($0.4344\text{ V}$) | `Fig. 23` shows standalone transient waveforms from which $0.4344\text{ V}$ ($0.583\text{--}1.017\text{ V}$) was extracted | **Template slot vs. underlying data source.** Figure 5 is the Virtuoso ViVA screenshot from the schematic-driven OCEAN run (Page 8), whereas the $0.4344\text{ V}$ swing corresponds to the standalone Spectre simulation waveforms plotted in Figure 23 (Page 24). |

---

## 2. Captions and Cross-References Verification

### 2.1 Complete List of Captions with Numbers and Locations

All captions in the 29-page text were extracted and mapped to their page locations:

- **Table 1** (Page 4): *Table 1: Device list, circuit without the sizing concept*
- **Table 2** (Page 6): *Table 2: Device list, circuit based on the sizing concept*
- **Table 3** (Page 9): *Table 3: Performance values with and without the sizing concept, with the proof figures for each row*
- **Table 4** (Page 10): *Table 4: PVT summary for design D at 1.4 GHz (41 of 45 corners pass)*
- **Table 5** (Page 10): *Table 5: PVT summary for design B at 6.0 GHz (21 of 45 corners pass)*
- **Table 6** (Pages 27–28): *Table 6: Complete PVT analysis results for design D at 1.4 GHz (45 corners)*
- **Figure 1** (Page 1): *Figure 1: Schematic of the differential DLATCH stage (M1-M7, R1, R2). Sizing: M1-M6 W = 240 nm, L = 45 nm; M7 W = 480 nm, L = 90 nm. Values shown for design D (m = 4, R1 = R2 = 3 kOhm; baseline uses m = 1, R = 8 kOhm).*
- **Figure 2** (Page 4): *Figure 2: Virtuoso schematic editor window showing the divider core with four DLATCH instances (XD1 to XD4) connected in a ring. Baseline and design D share this topology, differing only in m and R (Table 1 and Table 2). Schematic checks: 0 errors and 23 warnings for DLATCH; 0 errors and 11 warnings for divider_core; 0 errors and 19 warnings for tb_divider. The warnings are floating-net notices at net-label stubs; the netlist is unchanged by the wiring.*
- **Figure 3** (Page 5): *Figure 3: Transient waveforms for the baseline divider without sizing (m = 1, R1 = R2 = 8 kOhm, vb = 1 V) at 1.4 GHz. All eight outputs divide to 700.0 MHz, with Q1 swinging from 0.749 V to 0.978 V. Waveforms for paper sizing appear in Figure 9.*
- **Figure 4** (Page 7): *Figure 4: Virtuoso schematic editor window showing the DLATCH cell with sizing applied (design D: m = 4, R1 = R2 = 3 kOhm), consistent with Table 2. Schematic checks: 0 errors and 23 warnings for DLATCH; 0 errors and 11 warnings for divider_core; 0 errors and 19 warnings for tb_divider. The warnings are floating-net notices at net-label stubs; the netlist is unchanged by the wiring.*
- **Figure 5** (Page 8): *Figure 5: ViVA transient waveforms of design D from the Virtuoso testbench via Spectre.*
- **Figure 6** (Page 11): *Figure 6: PVT pass/fail map for design D at 1.4 GHz across 5 corners, temperatures -40/27/125 C, and supplies 0.9/1/1.1 V (41 of 45 points pass).*
- **Figure 7** (Page 12): *Figure 7: Virtuoso layout editor showing divider_core with four DLATCH instances (XD1 to XD4) placed in a 2x2 array (placement only, unrouted).*
- **Figure 8** (Page 14): *Figure 8: Ring interconnection of four DLATCH stages (XD1 to XD4) with alternating cross-connections, and inverted clocks on XD2 and XD3 (design D: m = 4, R = 3 kOhm).*
- **Figure 9** (Page 15): *Figure 9: Transient simulation with paper sizing (m = 1, R1 = R2 = 1.15 kOhm = Ron/2) at 1.4 GHz. Division fails: Q1 oscillates at 2799.8 MHz with only 15.3 mV swing (0.975 V to 0.991 V).*
- **Figure 10** (Page 16): *Figure 10: Transient waveforms for design B at 6 GHz (m = 4, R1 = R2 = 2 kOhm), yielding divided outputs at 3000.0 MHz.*
- **Figure 11** (Page 17): *Figure 11: Phase steps between the eight outputs for unsized baseline (1.4 GHz), design D (1.4 GHz), and design B (6 GHz).*
- **Figure 12** (Page 17): *Figure 12: Tail transistor (M7) drain voltage for unsized baseline compared with saturation voltage Vdsat = 0.358 V.*
- **Figure 13** (Page 18): *Figure 13: Tail transistor (M7) drain voltage for design D at 1.4 GHz compared with saturation voltage Vdsat = 0.358 V.*
- **Figure 14** (Page 18): *Figure 14: Tail transistor (M7) drain voltage for design B at 6 GHz compared with saturation voltage Vdsat = 0.358 V.*
- **Figure 15** (Page 19): *Figure 15: Supply current drawn from VDD for unsized baseline, design D, and design B.*
- **Figure 16** (Page 19): *Figure 16: Frequency sweeps for designs B, D, and E showing division range and maximum phase-step error versus input frequency.*
- **Figure 17** (Page 20): *Figure 17: Delay and power across the PVT matrix for design D at 1.4 GHz (crosses mark failing corners).*
- **Figure 18** (Page 20): *Figure 18: PVT pass/fail map for design B at 6 GHz (21 of 45 points pass).*
- **Figure 19** (Page 21): *Figure 19: Delay and power across the PVT matrix for design B at 6 GHz (crosses mark failing corners).*
- **Figure 20** (Page 22): *Figure 20: Virtuoso Command Interpreter Window (CIW) log confirming gpdk045 library initialization.*
- **Figure 21** (Page 23): *Figure 21: Virtuoso layout editor showing the DLATCH cell: 7 unit nMOS devices (m = 1) and 2 poly resistors (placement only, unrouted).*
- **Figure 22** (Page 23): *Figure 22: Assura DRC summary for the DLATCH layout showing 21 errors across 3 rules.*
- **Figure 23** (Page 24): *Figure 23: Transient waveforms for design D (m = 4, R1 = R2 = 3 kOhm) at 1.4 GHz. Output frequency is 700.0 MHz with Q1 swinging from 0.583 V to 1.017 V. Tail voltage V(XD1.tail) remains between 8.1 mV and 66.9 mV (XD2 reaches 68.2 mV).*

---

### 2.2 Cross-Reference Integrity Check

Every reference in the body text and tables was checked against its target caption:

| Reference Location | Item Cited | Stated Context / Claim | Caption Verified? | Content Alignment Notes |
|---|---|---|---|---|
| Page 3, Line 13 | Table 2 | *"These match Table 2 and the nominal transistor dimensions."* | Yes (Page 6) | Table 2 lists $W=240\text{ nm}, L=45\text{ nm}, m=4$ for M1–M6; $W=480\text{ nm}, L=90\text{ nm}, m=4$ for M7. Matches. |
| Page 3, Line 15 | Figure 1, Figure 2 | *"Circuit schematics for the DLATCH and divider core are illustrated in Figure 1 and Figure 2"* | Yes (Pages 1, 4) | Figure 1 is DLATCH stage; Figure 2 is divider core ring. Matches. |
| Page 3, Line 16 | Figure 8 | *"(ring architecture in Figure 8)."* | Yes (Page 14) | Figure 8 shows ring interconnection of XD1–XD4. Matches. |
| Page 3, Line 29 | Figure 9 | *"Output Q1 oscillates at 2799.8 MHz ... with only 15.3 mV swing (Figure 9)."* | Yes (Page 15) | Figure 9 caption states oscillation at 2799.8 MHz with 15.3 mV swing. Matches. |
| Page 4, Line 20 | Table 1, Table 2 | *"...differing only in m and R (Table 1 and Table 2)."* | Yes (Pages 4, 6) | Table 1 gives $m=1, R=8\text{ k}\Omega$; Table 2 gives $m=4, R=3\text{ k}\Omega$. Matches. |
| Page 5, Line 10 | Figure 9 | *"Waveforms for paper sizing appear in Figure 9."* | Yes (Page 15) | Caption confirms paper sizing transient waveforms. Matches. |
| Page 6, Line 6 | Figure 5 | *"Figure 5 shows the corresponding ViVA waveforms."* | Yes (Page 8) | Caption confirms ViVA transient waveforms of design D. Matches. |
| Page 6, Line 22 | Table 3 | *"Comparison with baseline (Table 3): sizing cuts delay from 62.21 ps ... to 25.99 ps..."* | Yes (Page 9) | Table 3 contains performance values with and without sizing. Matches. |
| Page 7, Line 3 | Table 2 | *"...consistent with Table 2."* | Yes (Page 6) | Sizing $m=4, R_1=R_2=3\text{ k}\Omega$ matches Table 2. Matches. |
| Page 9, Table 3 | Fig. 15 | Proof for Power calculation (both columns) | Yes (Page 19) | Figure 15 plots supply current for baseline, Design D, and Design B. Matches. |
| Page 9, Table 3 | Fig. 3, Fig. 5 | Proof for $f_{\text{in}}$ (1.4 GHz), $f_{\text{out}}$ (700.0 MHz), Output swing | Yes (Pages 5, 8) | Fig. 3 shows baseline waveforms; Fig. 5 shows Design D waveforms. Matches. |
| Page 9, Table 3 | Fig. 11 | Proof for Max phase-step error | Yes (Page 17) | Figure 11 plots phase steps for baseline, Design D, and Design B. Matches. |
| Page 9, Table 3 | Fig. 12, Fig. 13 | Proof for Tail-device saturation check (without / with) | Yes (Pages 17, 18) | Fig. 12 shows baseline tail voltage; Fig. 13 shows Design D tail voltage. Matches. |
| Page 9, Table 3 Note | Figure 9 | *"...delay, PDP, and phase error undefined; Figure 9)."* | Yes (Page 15) | Caption confirms paper sizing division failure. Matches. |
| Page 12, Line 23 | Figure 7, Figure 21 | *"Cell layouts are shown in Figure 7 (divider_core) and Figure 21 (DLATCH)."* | Yes (Pages 12, 23) | Fig. 7 is divider_core layout; Fig. 21 is DLATCH layout. Matches. |
| Page 13, Line 2 | Figure 22 | *"Assura DRC on DLATCH reports 21 errors across 3 rules (Figure 22)."* | Yes (Page 23) | Figure 22 caption reports 21 errors across 3 rules. Matches. |
| Page 13, Line 15 | Figure 14 | *"...below Vdsat = 357.8 mV (triode, Figure 14)."* | Yes (Page 18) | Figure 14 plots Design B M7 tail voltage vs $V_{\text{dsat}}$. Matches. |
| Page 13, Line 16 | Table 5 | *"PVT results appear in Table 5."* | Yes (Page 10) | Table 5 is PVT summary for Design B at 6.0 GHz. Matches. |
| Page 13, Line 25 | Figures 12, 13 | *"...M7 operates in triode rather than saturation (Figures 12 and 13)."* | Yes (Pages 17, 18) | Figures 12 and 13 confirm triode operation for baseline and Design D. Matches. |
| Page 13, Line 33 | Figure 16 | *"...phase error improves as frequency increases (Figure 16)."* | Yes (Page 19) | Figure 16 plots frequency sweeps and phase-step error. Matches. |
| Page 14, Line 6 | Table 6 | *"In Table 6 (Appendix), ratio is f_in/f_out (ratio 2 denotes correct division; 0.5 denotes outputs at 2 f_in)."* | Partial (Pages 27–28) | Table 6 exists in Appendix, but **does not contain a `ratio` column** (contains `Divides` and `f_out`). Reported as Medium defect. |
| Page 14, Line 12 | Figure 15 | *"Peak current is 0.560 mA (Figure 15)."* | Yes (Page 19) | Figure 15 shows transient supply current waveforms. Matches. |

---

## 3. Arithmetic Verification

### 3.1 With/Without Sizing Table Arithmetic (Table 3)
- **Baseline (Without Sizing):**
  - Displayed values: $P = 0.1375\text{ mW}$, Delay $= 62.21\text{ ps}$, stated $\text{PDP} = 8.557\text{ fJ}$.
  - Product of displayed values: $0.1375\text{ mW} \times 62.21\text{ ps} = 8.553875\text{ fJ}$.
  - Product of unrounded raw values (`U8k.tsv` / `analysis.json`): $0.137549\text{ mW} \times 62.21\text{ ps} = 8.556923\text{ fJ} \approx \mathbf{8.557\text{ fJ}}$.
  - Discrepancy from unrounded calculation: $\mathbf{< 0.0001\text{ fJ}}$ (exact within rounding).
- **Design D (With Sizing):**
  - Displayed values: $P = 0.5413\text{ mW}$, Delay $= 25.99\text{ ps}$, stated $\text{PDP} = 14.067\text{ fJ}$.
  - Product of displayed values: $0.5413\text{ mW} \times 25.99\text{ ps} = 14.068387\text{ fJ}$.
  - Product of unrounded raw values (`D_1p4.tsv` / `analysis.json`): $0.541337\text{ mW} \times 25.985127\text{ ps} = 14.066711\text{ fJ} \approx \mathbf{14.067\text{ fJ}}$.
  - Discrepancy from unrounded calculation: $\mathbf{< 0.0003\text{ fJ}}$ (exact within rounding).
- **Design B (Body Text & Conclusions):**
  - Displayed values: $P = 0.4929\text{ mW}$, Delay $= 27.94\text{ ps}$, stated $\text{PDP} = 13.768\text{ fJ}$.
  - Product of displayed values: $0.4929\text{ mW} \times 27.94\text{ ps} = 13.771626\text{ fJ}$.
  - Product of unrounded raw values (`B_6g.tsv` / `analysis.json`): $0.492869\text{ mW} \times 27.93523\text{ ps} = 13.768409\text{ fJ} \approx \mathbf{13.768\text{ fJ}}$.
  - Discrepancy from unrounded calculation: $\mathbf{< 0.0004\text{ fJ}}$ (exact within rounding).
- **Stated Performance Ratios (Page 6):**
  - Delay reduction: $62.21\text{ ps} / 25.99\text{ ps} = 2.3936\times \rightarrow$ stated **$2.39\times$** (Exact).
  - Power increase: $0.5413\text{ mW} / 0.1375\text{ mW} = 3.9367\times \rightarrow$ stated **$3.94\times$** (Exact).
  - PDP increase: $14.067\text{ fJ} / 8.557\text{ fJ} = 1.6439\times \rightarrow$ stated **$1.64\times$** (Exact).
- **Table 6 PDP Column (Appendix):**
  - In 32 of 41 PASS rows, multiplying displayed rounded Delay by Power equals displayed rounded PDP.
  - In 9 rows (`tt_-40_1.0`, `ff_-40_1.0`, `ff_-40_1.1`, `ff_27_1.0`, `ff_125_0.9`, `ss_27_1.1`, `fs_-40_1.0`, `fs_27_1.0`, `sf_-40_1.1`), product differs by $\pm 0.01\text{ fJ}$ due to unrounded TSV copying.

---

## 4. PVT Pass Counts and Matrix Verification

- **Table 4 (Design D at 1.4 GHz, Page 10):**
  - Table grid: 5 corners $\times$ 3 temperatures $\times$ 3 voltages = 45 entries.
  - Count: **41 PASS**, **4 FAIL** (Total = 45).
  - Stated total: *"41 of 45 corners pass"*. (Matches).
  - Failing corners in table: `tt` at $125^\circ\text{C}, 0.9\text{ V}$; `ss` at $125^\circ\text{C}, 0.9\text{ V}$; `fs` at $125^\circ\text{C}, 0.9\text{ V}$; `sf` at $125^\circ\text{C}, 0.9\text{ V}$.
  - Ground truth source (`results/gpdk045/final/pvt_summary_D_1p4.json` & `pvt_D.tsv`): Identical cell-by-cell.
- **Table 5 (Design B at 6.0 GHz, Page 10):**
  - Table grid: 5 corners $\times$ 3 temperatures $\times$ 3 voltages = 45 entries.
  - Count: **21 PASS**, **24 FAIL** (Total = 45).
  - Stated total: *"21 of 45 corners pass"*. (Matches).
  - Temperature breakdown:
    - $-40^\circ\text{C}$: 13 PASS, 2 FAIL (`ss` and `sf` at $0.9\text{ V}$).
    - $27^\circ\text{C}$: 8 PASS, 7 FAIL (`tt`, `ff`, `ss`, `fs`, `sf` at $0.9\text{ V}$; `ss` and `sf` at $1.0\text{ V}$).
    - $125^\circ\text{C}$: 0 PASS, 15 FAIL (all corners and voltages).
  - Ground truth source (`results/gpdk045/final/pvt_summary_B_6g.json` & `pvt_B6.tsv`): Identical cell-by-cell.
- **Table 6 (Complete PVT Data for Design D, Pages 27–28):**
  - Total rows: 45.
  - Row tally: **41 PASS rows**, **4 FAIL rows**. (Matches).

---

## 5. Logs and Physical Verification Verification

- **Schematic Check Notices (`wire_schematics_log.txt`):**
  - Stated: *"0 errors and 23 warnings for DLATCH; 0 errors and 11 warnings for divider_core; 0 errors and 19 warnings for tb_divider."*
  - Source file `results/gpdk045/wire_schematics_log.txt` (Final run):
    - `DLATCH schCheck: 0 errors, 23 warnings`
    - `divider_core schCheck: 0 errors, 11 warnings`
    - `tb_divider schCheck: 0 errors, 19 warnings`
    - `"Warnings are extraction 'Floating net' notices at stub-end label points ... netlist unchanged."`
  - Verdict: **Exact match**.
- **Assura DRC (`assura_drc_dlatch_summary.txt` & `assura_drc_dlatch_rules.txt`):**
  - Stated: *"21 errors across 3 rules ... Rules 220 (1) and 221 (6) ... device pitch 0.755 um ... Rule 595 (14) flags isolated contact pads (0.06 x 0.12 um = 0.0072 um^2 < 0.02 um^2), while connected pads (0.12 x 0.25 um = 0.03 um^2) meet the minimum area."*
  - Source file `results/gpdk045/assura_drc_dlatch_summary.txt`:
    - Rule 220 (`psubstrate_StampErrorMult`): 1 error
    - Rule 221 (`psubstrate_StampErrorConnect`): 6 errors (marker coords step at $0.755\ \mu\text{m}$)
    - Rule 595 (`METAL1.A.1: Metal1 area >= 0.02 um`): 14 errors (markers measure $0.06 \times 0.12\ \mu\text{m} = 0.0072\ \mu\text{m}^2$)
    - Total: $1 + 6 + 14 = 21$ real errors across 3 rules.
  - Verdict: **Exact match**.
- **Automated Routing (`route_dlatch_log.txt` & `assura_drc_dlatch_routed.txt`):**
  - Stated: *"completed 136 of 137 connections but produced 134 DRC errors and mismatches in LVS"*.
  - Source file `results/gpdk045/route_dlatch_log.txt`:
    - Section 3: `Nets 12 Connections 137 Unroutes 1` ($137 - 1 = 136$ routed).
  - Source file `results/gpdk045/assura_drc_dlatch_routed.txt`:
    - `Total: 134 real errors (flat count = real count) in 17 rules.`
  - Verdict: **Exact match**.

---

## 6. Comprehensive Quantitative Claims Audit

Every other quantitative claim in the 29-page text was cross-checked against the repository data:

1. **Operating Points & Sizing Dimensions:**
   - Unit device: $W = 240\text{ nm}, L = 45\text{ nm}$ ($W/L = 5.333 \approx 5.33$). Tail: $W = 480\text{ nm}, L = 90\text{ nm}$. (Matches `virtuoso_netlist_tb_divider.scs`).
   - Reference paper: $W/L = 0.9\ \mu\text{m} / 180\text{ nm} = 5.00$. (Matches `report_data.json`).
   - Sizing multipliers: $m=1$ (baseline), $m=4$ (Design D, Design B), $m=6$ (Design E). (Matches TSVs).
   - Resistor values: $R = 8\text{ k}\Omega$ (baseline), $3\text{ k}\Omega$ (Design D), $2\text{ k}\Omega$ (Design B), $1.15\text{ k}\Omega$ (paper rule). (Matches TSVs).
2. **Device Physics & Operating Regimes:**
   - $R_{\text{on}} = 2.3\text{ k}\Omega$; unit 3-transistor stack $= 6.90\text{ k}\Omega$; regeneration threshold $R_1 \ge 1.1 \times 6.90 = 7.59\text{ k}\Omega$. (Matches `LEDGER.md`).
   - Empirical sweep boundaries: 6 to $7\text{ k}\Omega$ at $V_b = 1.0\text{ V}$; 7 to $8\text{ k}\Omega$ at $V_b = 0.8\text{ V}$. (Matches `unsized_baseline.tsv`).
   - $m=4$ stack $= 1.72\text{ k}\Omega$; threshold band $1.88\text{--}2.25\text{ k}\Omega$. (Matches `LEDGER.md`).
   - BSIM4 extracted operating parameters: $V_{\text{th}} = 527.5\text{ mV}$, $V_{\text{dsat}} = 357.8\text{ mV}$, $g_m = 200.9\text{ pS}$, $g_{\text{ds}} = 2.531\text{ mS}$. (Matches `D_1p4.m7vdsat.txt`).
   - DC $t=0$ tail conditions: Paper sizing $V_{\text{ds}} = 56.3\text{ nV}, I_{\text{ds}} = 35.6\text{ pA}$; Design D $V_{\text{ds}} = 54.4\text{ nV}, I_{\text{ds}} = 137.4\text{ pA}$; Design B $V_{\text{ds}} = 54.4\text{ nV}, I_{\text{ds}} = 137.4\text{ pA}$. (Matches `unsized.m7op.txt`, `D_1p4.m7op.txt`, `B_6g.m7op.txt`).
   - Transient peak tail voltage: Design D $= 66.9\text{ mV}$ (XD1), $68.2\text{ mV}$ (XD2); Baseline $= 67.1\text{ mV}$; Design B $= 66.2\text{ mV}$. All $< 357.8\text{ mV}$ (confirmed triode). (Matches `analysis.json`).
3. **Elmore Delay & Frequency Limits:**
   - Lower bound $T_d \ge R_1 C_L$: $30\text{ ps}$ for Design D ($3\text{ k}\Omega \times 10\text{ fF}$); $20\text{ ps}$ for Design B ($2\text{ k}\Omega \times 10\text{ fF}$). (Exact).
   - Clock half-periods: $T_{\text{CK}}/2 = 357\text{ ps}$ at $1.4\text{ GHz}$; $83\text{ ps}$ at $6.0\text{ GHz}$; $80.6\text{ ps}$ at $6.2\text{ GHz}$. (Exact).
   - Design B CK-to-Q1 delay: $66.10\text{ ps} = 3.305\times \approx 3.3\times$ intrinsic bound ($79.3\% \approx 79\%$ of $T_{\text{CK}}/2$). (Matches `analysis.json`).
4. **Phase-Step Calculations:**
   - $a = 180 \times t_{\text{pair}} \times f_{\text{in}}$:
     - Design D ($t_{\text{pair}} = 25.95\text{ ps}, 1.4\text{ GHz}$): $a = 6.54^\circ$, complementary $83.46^\circ$. (Matches).
     - Design B ($t_{\text{pair}} = 38.16\text{ ps}, 6.0\text{ GHz}$): $a = 41.22^\circ$, complementary $48.78^\circ$. (Matches).
     - Baseline ($t_{\text{pair}} = 73.75\text{ ps}, 1.4\text{ GHz}$): $a = 18.59^\circ$, complementary $71.42^\circ$. (Matches).
   - $45^\circ$ spacing required $T_{\text{CK}} = 4 t_{\text{pair}}$: Design D $= 103.8\text{ ps}$ ($9.63\text{ GHz}$); Design B $= 152.7\text{ ps}$ ($6.55\text{ GHz}$). (Matches).
5. **Transient Edge & Switching Characteristics:**
   - First-edge CK-to-Q1 delay: $135.96\text{ ps}$ (baseline), $51.95\text{ ps}$ (Design D), $66.10\text{ ps}$ (Design B). (Matches `analysis.json`).
   - Mean multi-phase delay: $62.21\text{ ps}$ (baseline), $25.99\text{ ps}$ (Design D), $27.94\text{ ps}$ (Design B). (Matches `analysis.json`).
   - Design D rise/fall times ($10\%\text{--}90\%$): $t_r = 134.6\text{ ps}, t_f = 102.6\text{ ps}$. (Matches `analysis.json`).
   - Supply current Design D: mean steady $= 0.54144\text{ mA}$, TSV integrated $= 0.541337\text{ mA}$ ($0.018\%$ difference); peak steady $= 0.560\text{ mA}$. (Matches `analysis.json`).
6. **Schematic vs. Standalone Power Gap:**
   - Virtuoso schematic simulation (OCEAN): $P = 0.455\text{ mW}$, delay $= 26.66\text{ ps}$, $\text{PDP} = 12.14\text{ fJ}$. (Matches `ocean_schematic_run_1p4GHz_D.txt`).
   - Standalone netlist: $P = 0.541\text{ mW}$, delay $= 25.99\text{ ps}$, $\text{PDP} = 14.07\text{ fJ}$. (Matches `power_gap_experiment.md`).
7. **Exploratory Frequency Sweeps (16 Points):**
   - Design B: divides $1.4\text{--}6.0\text{ GHz}$ (phase error $38.68^\circ \rightarrow 3.78^\circ$), fails at $6.2\text{ GHz}$. (Matches `fs_B.tsv`).
   - Design D: divides $3.0\text{--}5.5\text{ GHz}$ (phase error $30.89^\circ \rightarrow 13.82^\circ$), fails at $6.0\text{ GHz}$. (Matches `fs_D.tsv`).
   - Design E: divides $3.0\text{--}7.0\text{ GHz}$ (phase error $34.32^\circ \rightarrow 15.24^\circ$), fails at $8.0\text{ GHz}$. (Matches `fs_E.tsv`).
   - 16-point exploration (`fs_F.tsv`):
     - $m=4, R=2.2\text{ k}\Omega$: divides up to $6.25\text{ GHz}$ ($5.57^\circ$).
     - $m=4, R=2.5\text{ k}\Omega$: divides up to $6.0\text{ GHz}$ ($11.23^\circ$), fails at $6.25\text{ GHz}$.
     - $m=5, R=2.2\text{ k}\Omega$: divides up to $6.25\text{ GHz}$ ($16.56^\circ$).
     - $m=5, R=2.5\text{ k}\Omega$: divides up to $6.25\text{ GHz}$ ($14.36^\circ$).
     - All match `fs_F.tsv` exactly.
8. **Physical Layout Metrics:**
   - DLATCH cell: 7 unit nMOS pcells ($0.595\ \mu\text{m}$ width), 2 poly resistors ($W=0.8\ \mu\text{m}, L=7.855\ \mu\text{m}, 200\ \Omega/\Box, 2000\ \Omega$). Dimensions: $4.875 \times 20.28\ \mu\text{m}$. (Matches `layout_build_log.txt`).
   - divider_core: 4 instances (XD1 R0, XD2 MY, XD3 MX, XD4 R180, $1\ \mu\text{m}$ gap), clock-star branch length $98.62\ \mu\text{m}$. (Matches `layout_build_log.txt`).
9. **Literature Reference Values (Kuo et al.):**
   - TSMC $180\text{ nm}$, $1.8\text{ V}$, $1.4\text{ GHz}$, $2.34\text{ mW}$, phase error $\le 3.75^\circ$, core area $91.7 \times 52.9\ \mu\text{m}^2$. (Matches `report_data.json` & paper).

---

## 7. Audit Verdict

**Verdict:**
The report text is exceptionally rigorous and well-verified: all quantitative simulation metrics (power, delay, PDP, frequencies, phase-step errors, swings, DC/transient tail operating voltages, stack resistances, and device dimensions) match the Cadence MMSIM 12.1 / Virtuoso 6.1.5 simulation datasets and verification logs in `results/gpdk045/` without any numerical hallucinations or fabrications. All 23 figure captions and 6 table captions exist at their referenced locations with matching content. Only one structural reference defect was identified: the body text on Page 14 refers to a non-existent `ratio` column in Appendix Table 6 (a column that exists in `pvt_D.tsv` but was omitted from the rendered report table).
