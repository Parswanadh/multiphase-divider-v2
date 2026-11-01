# Academic Submission Completeness & Rigorous Compliance Audit
**Institution:** Amrita School of Engineering, Bengaluru  
**Department:** Electronics and Communication Engineering (ECE / EAC)  
**Academic Year:** 2026–2027 (B.Tech. V Semester)  
**Evaluation Dates:** 27th October to 7th November 2026 (per Faculty Email / Notice)  
**Evaluator / Course Faculty:** Dr. Kaveri Hatti  
**Audited Directory:** `/home/parshu/projects/multiphase-divider-v2/report/gpdk045`  
**Date of Audit:** 2026-11-01  

---

## Executive Summary & Audit Baseline

This independent academic audit evaluates the completeness and submission-readiness of the two course deliverables:
1. **Deliverable A (40 Marks):** 23ECE383 VLSI Design Laboratory — System Design Project Report (`System_Design_Project_Report_gpdk045.pdf` and `.docx`).
2. **Deliverable B (15 Marks):** 23ECE302 VLSI Design (Theory) — Theory Assignment (`23ECE302_Theory_Assignment_gpdk045.md`).

### Governing Requirement Sources
1. **Official Format Document:** `/home/parshu/Downloads/System Design Project Report_format (1).doc` (converted and verified via LibreOffice to text, PDF, and DOCX). Prescribes the institutional header, title page structure, typography rules (Times New Roman 12 pt body, 14 pt headings), 20 numbered/specific sections in fixed order, values table with proof screenshots, and "Page X of Y" footer.
2. **Evaluation Rubric & Notice:** `reference/whatsapp_2026-10-28.jpeg` (official communication from Dr. Kaveri Hatti to `2024EAC` dated Thu 10/09/2026 18:42, containing the 40-mark lab distribution for CO4, 15-mark theory assignment distribution, and 100-mark course evaluation structure).
3. **Verified Simulation Evidence & Repository Context:** `report/gpdk045/report_data.json`, `results/gpdk045/final/*.tsv`, `results/gpdk045/assura_drc_dlatch_summary.txt`, `README.md`, `STABLE.md`, and `report/gpdk045/README_report.md`.

---

## Deliverable A: 23ECE383 VLSI Lab System Design Project (40 Marks)

Deliverable A is compiled as a 25-page academic report in both PDF (`System_Design_Project_Report_gpdk045.pdf`, 3,163,607 bytes) and DOCX (`System_Design_Project_Report_gpdk045.docx`, 4,853,871 bytes).

### Compliance & Rubric Evaluation Table

| Requirement / Item | Source (Format Doc / Rubric Line) | Status | Evidence (Page, Section, File) | Fix Needed / Action Required |
|---|---|---|---|---|
| **Institutional Title & Cover Block** | Format Doc, Page 1 | **Partly** | Page 1; Amrita logo, department, semester, course titles present. Student table (Table 0) has 4 empty rows; Batch Number and Faculty Signature lines are blank underscores. | **Student Action Required:** Fill student Register Numbers, Names, Signatures, Batch Number, and Evaluation Date. |
| **Typography: Font Family** | Format Doc: "(USE TIMES NEW ROMAN WITH FONT SIZE AS 12 EVERYWHERE EXCEPT HEADING...)" | **Partly** | `System_Design_Project_Report_gpdk045.docx` specifies `Times New Roman`. However, `pdffonts` reveals that `System_Design_Project_Report_gpdk045.pdf` embeds `LiberationSerif` because Microsoft core fonts are not installed on the Linux build host. | Install `msttcorefonts` on host or export PDF from Microsoft Word on Windows/macOS so genuine Times New Roman is embedded. |
| **Typography: Font Sizes** | Format Doc: "FONT SIZE AS 12 EVERYWHERE EXCEPT HEADING. HEADING FONT SIZE WITH 14" | **Met** | Entire DOCX verified via python-docx: all `Heading 1` paragraphs are 14.0 pt; all body text and table text are 12.0 pt. No other font sizes exist. | None. Fully compliant. |
| **Page Layout & Margins** | Format Doc: US Letter, Top/Bottom 1.0", Left/Right 1.25" | **Partly** | Pages 1–23: US Letter, Margins 0.9" on all 4 sides. Pages 24–25 (Appendix): Landscape, Margins 0.75" / 0.8". Format template had 1.0" top/bot and 1.25" left/right. | Minor margin deviation introduced by builder to fit 6.3" waveform figures without severe clipping. Acceptable, but differs from template defaults. |
| **Page Numbering Footer** | Format Doc: "Page X of Y" in footer | **Met** | Pages 1–25: Footer explicitly contains `Page X of 25` on every single page from Page 1 to Page 25. | None. Fully compliant. |
| **Double Page Border** | Format Doc visual styling / `README_report.md` | **Met** | Visually verified on rendered PNGs (`page-01.png` to `page-25.png`): all pages feature an outer double border. | None. Fully compliant. |
| **Front-Matter: Abstract** | Academic Standard / Student prompt check | **Missing (Not in Template)** | Format doc contains no Abstract slot; report contains no Abstract. Report proceeds directly from Title Page to `TITLE OF THE SYSTEM DESIGN PROJECT:`. | Template does not request an Abstract. If evaluator requests an abstract, add an unnumbered summary section before Section 1. |
| **Front-Matter: Certificate / Declaration / Acknowledgement** | Academic Standard / Student prompt check | **Missing (Not in Template)** | Format doc contains no Certificate, Declaration, or Acknowledgement; report omits them accordingly. | Template omits these. Retain as-is unless department issues a formal thesis/project monograph guideline. |
| **Front-Matter: Table of Contents (TOC)** | Academic Standard / Student prompt check | **Missing (Not in Template)** | Format doc contains no TOC; report omits TOC. | Omitted in format template. For a 25-page document, a Table of Contents is highly recommended ("NICE TO HAVE"). |
| **Front-Matter: List of Figures / Tables (LOF / LOT)** | Academic Standard / Student prompt check | **Missing (Not in Template)** | Format doc contains no LOF/LOT; report omits LOF/LOT. | Omitted in format template. Optional addition. |
| **Section Ordering: Sections 1–6 (Paper Details, Circuit, Theory, Tools)** | Format Doc, Page 2 | **Met** | Pages 2–4: `TITLE OF THE SYSTEM DESIGN PROJECT:`, `TITLE OF THE PAPER:`, `DETAILS OF THE PAPER:`, `CIRCUIT DIAGRAM:`, `THEORY AND WORKING PRINCIPLE:`, `TOOL & TECHNOLOGY USED:`. | None. Fully matches template order. |
| **Section Ordering: Section 7 (Circuit Implementation Screenshot)** | Format Doc, Page 2 | **Met** | Pages 4–6: Heading present; Table 1 (device parameters); Figure 2 (Virtuoso schematic editor core window). | None. |
| **Section Ordering: Section 8 (Unsized Waveform Screenshot)** | Format Doc, Page 2 | **Met** | Page 7: Heading present; Figure 3 (Transient waveforms for unsized baseline at 1.4 GHz). | Note: Waveform is a Python matplotlib Spectre plot rather than a Cadence ViVA screenshot. |
| **Section Ordering: Section 9 (Circuit with Sizing Screenshot)** | Format Doc, Page 2 | **Met** | Pages 8–9: Heading present; Figure 4 (Virtuoso DLATCH schematic); Table 2 (sized device list). | None. |
| **Section Ordering: Section 10 (Sized Waveform Screenshot)** | Format Doc, Page 2 | **Met** | Page 10: Heading present; Figure 5 (ViVA transient waveform screenshot of Design D at 1.4 GHz). | None. Genuine Cadence ViVA tool screenshot. |
| **Section Ordering: Section 11 (Values Table with Proof Figures)** | Format Doc, Pages 2–3 | **Met** | Pages 10–11: Table 3 lists Power (0.1375 vs 0.5413 mW), Delay (62.21 vs 25.99 ps), PDP (8.557 vs 14.067 fJ), Frequency, Swing, M7 Saturation check, with Proof Figure citations. | None. Fully compliant. |
| **Section Ordering: Section 12 (PVT Analysis Screenshot)** | Format Doc, Page 3 | **Partly** | Pages 11–12: Heading present; Table 4 (Design D summary), Table 5 (Design B summary), Figure 6 (Python matplotlib PVT heatmap). | No Cadence ADE XL / Virtuoso screenshot; headless Python heatmap provided instead. |
| **Section Ordering: Section 13 (Layout Screenshot)** | Format Doc, Page 3 | **Met** | Page 13: Heading present; Figure 7 (Virtuoso Layout XL placement view of `divider_core` 2x2 array). | None. Genuine Virtuoso layout editor screenshot. |
| **Section Ordering: Section 14 (Layout Simulator Waveform Screenshot)** | Format Doc, Page 3 | **Partly** | Page 13: Heading present; Text explicitly states: *"No post-layout waveform exists because the layout is placement only."* | Layout unrouted / no extraction. Heading is preserved, explanation given, but screenshot is missing. |
| **Section Ordering: Sections 15–20 (Other Info, Conclusion, Problems, Comments, References)** | Format Doc, Page 3 | **Met** | Pages 13–23: All sections present in exact sequence; 15 extra figures included in Section 15. | None. |
| **Appendix: Complete PVT Table** | Academic completeness | **Met** | Pages 24–25: `APPENDIX: COMPLETE PVT DATA`, Table 6 (complete 45-corner simulation results for Design D across tt/ff/ss/fs/sf, -40/27/125 °C, 0.9/1.0/1.1 V). | None. Added value. |
| **Rubric Line: Functionality (DC & Transient Analysis)** | Rubric: System Project (10 Marks) | **Met** | Pages 7, 10, 16, 22: Full transient division verified (Design D 1.4 GHz → 700 MHz, Design B 6.0 GHz → 3.0 GHz, ViVA screenshot in Fig. 5); DC operating points evaluated in prose (Page 14). | Optional: Add a static DC transfer curve / operating point sweep screenshot if evaluator demands explicit "DC" plot. |
| **Rubric Line: Power Calculation** | Rubric: System Project (5 Marks) | **Met** | Table 3 (Pages 10–11), Section 15 (Page 18, Fig. 15 supply current plot). Unsized: 0.1375 mW; Sized Design D: 0.5413 mW (standalone) / 0.4554 mW (Virtuoso); Design B: 0.4929 mW. | None. Fully evidenced. |
| **Rubric Line: Delay Calculation** | Rubric: System Project (5 Marks) | **Met** | Table 3 (Pages 10–11), Page 3 (Theory), Page 15 (Section 15). Unsized: 62.21 ps (multiphase avg) / 135.96 ps (first-edge); Sized Design D: 25.99 ps (avg) / 51.95 ps (first-edge). | None. Fully evidenced. |
| **Rubric Line: Power Delay Product (PDP)** | Rubric: System Project (5 Marks) | **Met** | Table 3 (Pages 10–11): Unsized: 8.557 fJ; Sized Design D: 14.067 fJ. Derived from unrounded simulation power and delay; footnote clarifies display arithmetic. | None. Fully evidenced. |
| **Rubric Line: PVT Analysis** | Rubric: System Project (5 Marks) | **Met** | Pages 11–12, 19–20, 24–25: 45-point matrix (5 corners × 3 temps × 3 voltages). Design D: 41/45 pass (91.1%); Design B: 21/45 pass (46.7%). Full Table 6 in Appendix. | None. Exceeds standard lab depth. |
| **Rubric Line: Layout** | Rubric: System Project (5 Marks) | **Partly** | Pages 13, 14, 21: Figures 7 & 20 show Virtuoso layout placement of `divider_core` and `DLATCH`. Figure 21 shows Assura DRC summary (21 errors across 3 rules). | Layout is placement-only (unrouted); no LVS-clean layout exists; no post-layout extraction or simulation was performed. 1–2 marks at risk under strict rubric interpretation. |
| **Rubric Line: Report** | Rubric: System Project (5 Marks) | **Partly** | 25 pages, rigorous data, zero template dummy text. However, student cover page metadata is blank, and 7 figures are never referenced in prose. | Fill student metadata; add in-text references to Figures 4, 6, 10, 17, 18, 19, 22. |

---

### PDF Rendering & Format Verification

Visual inspections were performed across all 25 pages rendered to 70 DPI PNG images (`pdftoppm -r 70` into `/tmp/pdf_pages/page-01.png` to `page-25.png`):

1. **Page Count & Section Allocation:**
   - **Total Pages:** 25 pages.
   - **Page 1:** Institutional Title / Cover Page with double border.
   - **Page 2:** Project Title, Paper Details, Circuit Diagram (Figure 1).
   - **Page 3:** Theory and Working Principle (Elmore delay, Stack regeneration, Phase-step equations).
   - **Page 4:** Tool & Technology Used; Simulator Based Circuit Implementation (start).
   - **Page 5:** Table 1 (Device list without sizing).
   - **Page 6:** Figure 2 (Virtuoso schematic editor core window).
   - **Page 7:** Output Waveform without Sizing (Figure 3); Virtuoso vs Standalone power explanation.
   - **Page 8:** Circuit Based on Sizing Concept (Figure 4); Sizing rationale.
   - **Page 9:** Table 2 (Device list with sizing). *(Note: Table 2 occupies top 2.5 inches; bottom 7.5 inches is blank due to page break before Section 10).*
   - **Page 10:** Output Waveform with Sizing (Figure 5 ViVA screenshot); Values Table (Table 3 start).
   - **Page 11:** Table 3 continuation and notes; PVT Analysis (Table 4 Design D summary).
   - **Page 12:** Table 5 (Design B summary); Figure 6 (PVT pass/fail heatmap for Design D).
   - **Page 13:** Layout Screenshot (Figure 7); Output Waveform for Layout note; Any Other Relevant Information (start).
   - **Pages 14–22:** Detailed engineering narrative and Extra Figures (Figures 8–22).
   - **Page 22 (lower half):** Conclusion.
   - **Page 23:** Problems Faced, Problems Resolved, Any Other Comment, References.
   - **Pages 24–25 (Landscape):** Appendix: Table 6 (Complete 45-corner PVT table for Design D).

2. **Captions and Cross-References Audit:**
   - **Tables (6 total):** All 6 tables have formal captions (`Table 1:` to `Table 6:`) above the table and are cross-referenced in the text.
   - **Figures (22 total):** All 22 figures have formal captions (`Figure 1:` to `Figure 22:`) below the image.
   - **Unreferenced Figures Defect:** An exhaustive search of the document text revealed that **7 figures are never cited in the body text or tables**:
     * **Figure 4 (Page 8):** Virtuoso DLATCH schematic editor window.
     * **Figure 6 (Page 12):** PVT pass/fail heatmap for Design D at 1.4 GHz.
     * **Figure 10 (Page 16):** Transient waveforms for Design B at 6 GHz.
     * **Figure 17 (Page 19):** Delay and power vs VDD for Design D.
     * **Figure 18 (Page 20):** PVT pass/fail heatmap for Design B at 6 GHz.
     * **Figure 19 (Page 20):** Delay and power vs VDD for Design B.
     * **Figure 22 (Page 22):** Transient waveforms for Design D standalone netlist.
     *(Fix needed: In `report_data.json` or narrative builder, add parenthetical citations such as "(Figure 4)", "(Figure 6)", etc., in their corresponding paragraphs).*

3. **Placeholders and Unfilled Student Information:**
   - **Cover Page Table 0 (Page 1):** The 4 student rows under `REGISTER NUMBER`, `NAME`, `SIGNATURE WITH DATE` contain empty strings `['', '', '']`.
   - **Batch Number (Page 1):** Literal string `BATCH NUMBER: ____________________________________`.
   - **Faculty Signature (Page 1):** Literal string `________________________________________________________` followed by `FACULTY EXAMINER SIGNATURE WITH EVALUATION DATE`.
   - **General Text:** Zero occurrences of `TODO`, `FIXME`, `XX`, `[...]`, or `NOT YET AVAILABLE`.
   - **Table Cells:** `n/a` appears 18 times (appropriately representing non-applicable resistor dimensions W/L in Tables 1 and 2, and undefined delay/power for failed PVT points in Table 6).

4. **Image Legibility & Provenance Assessment:**
   - **Figure 1 (Page 2):** Clear vector-rendered schematic drawing of DLATCH stage; text fully legible.
   - **Figure 2 (Page 6):** Virtuoso schematic editor window. The black background and dark canvas make net labels small, but the 4-cell block topology is identifiable.
   - **Figure 3 (Page 7):** Python matplotlib plot of 8-phase waveforms; crisp, high-resolution axes and labels.
   - **Figure 4 (Page 8):** Virtuoso DLATCH schematic; pin labels visible on high zoom.
   - **Figure 5 (Page 10):** Cadence ViVA waveform viewer screenshot; 8 color-coded traces clearly distinguishable.
   - **Figure 6 (Page 12):** Python matplotlib heatmap (green/red); text inside cells (delay/FAIL) legible.
   - **Figure 7 (Page 13):** Virtuoso Layout XL editor; shows 2x2 bounding boxes labeled `DLATCH`. Internal transistor geometries are not visible because cell view is at top-level placement zoom.
   - **Figures 8–19, 22:** High-resolution matplotlib plots with clear typography and legends.
   - **Figure 20 (Page 21):** Virtuoso DLATCH layout; poly resistors clearly visible; NMOS devices clustered at base.
   - **Figure 21 (Page 21):** Assura DRC terminal summary; white text on black background; error counts (Rule 220: 1, Rule 221: 6, Rule 595: 14) razor-sharp.

---

### Numerical Consistency Audit

Spot-check of 17 key numerical claims across Conclusion, Values Table, Narrative, and raw simulation logs (`results/gpdk045/final/`):

| Parameter / Claim | Stated in Report Text / Table | Value in `report_data.json` | Underlying Simulation Source | Discrepancy / Alignment |
|---|---|---|---|---|
| **Design D Input Frequency** | 1.4 GHz | `1.4` GHz | `results/gpdk045/final/D_1p4.tsv` col `f_in_GHz`: `1.4000` | Exact match |
| **Design D Output Frequency** | 700.0 MHz | `700.0` MHz | `results/gpdk045/final/D_1p4.tsv` col `f_out_MHz`: `700.000` | Exact match |
| **Design D Power (Standalone)** | 0.5413 mW | `0.5413` mW | `results/gpdk045/final/D_1p4.tsv` col `power_mW`: `0.541337` | Exact match (rounded to 4 decimal places) |
| **Design D Delay (Multiphase Avg)** | 25.99 ps | `25.99` ps | `results/gpdk045/final/D_1p4.tsv` col `delay_ps`: `25.99` | Exact match |
| **Design D Power Delay Product** | 14.067 fJ | `14.067` fJ | `results/gpdk045/final/D_1p4.tsv` col `pdp_fJ`: `14.067` | Exact match (computed from unrounded raw values) |
| **Design D Output Swing** | 0.4344 V | `0.4344` V | `D_1p4.tsv`: `swing_hi` (1.0172) - `swing_lo` (0.5827) = `0.4345 V` | Raw calculation yields 0.4344 V from transient sample arrays |
| **Design D Phase-Step Error** | 38.46 deg | `38.46` deg | `results/gpdk045/final/D_1p4.tsv` col `max_phase_step_err_deg`: `38.461` | Exact match (rounded to 2 decimal places) |
| **Design D PVT Corners Passing** | 41 of 45 corners | `41` pass, `4` fail | `results/gpdk045/final/pvt_summary_D_1p4.json`: `{"passed": 41, "failed": 4}` | Exact match |
| **Design D PVT Fail Condition** | 125 °C, 0.9 V (tt, ss, fs, sf) | 4 fail rows at 125 °C, 0.9 V | `results/gpdk045/final/pvt_D.tsv` | Exact match |
| **Design B Input Frequency** | 6.0 GHz (or 6 GHz) | `6.0` GHz | `results/gpdk045/final/B_6g.tsv` col `f_in_GHz`: `6.0000` | Exact match |
| **Design B Output Frequency** | 3000.0 MHz | `3000.0` MHz | `results/gpdk045/final/B_6g.tsv` col `f_out_MHz`: `3000.000` | Exact match |
| **Design B Power** | 0.4929 mW | `0.4929` mW | `results/gpdk045/final/B_6g.tsv` col `power_mW`: `0.492869` | Exact match |
| **Design B Delay** | 27.94 ps | `27.94` ps | `results/gpdk045/final/B_6g.tsv` col `delay_ps`: `27.94` | Exact match |
| **Design B PDP** | 13.768 fJ | `13.768` fJ | `results/gpdk045/final/B_6g.tsv` col `pdp_fJ`: `13.768` | Exact match |
| **Design B Phase-Step Error** | 3.78 deg | `3.78` deg | `results/gpdk045/final/B_6g.tsv` col `max_phase_step_err_deg`: `3.784` | Exact match |
| **Design B PVT Corners Passing** | 21 of 45 corners | `21` pass, `24` fail | `results/gpdk045/final/pvt_summary_B_6g.json`: `{"passed": 21, "failed": 24}` | Exact match |
| **Unsized Baseline Power** | 0.1375 mW | `0.1375` mW | `results/gpdk045/final/U8k.tsv` col `power_mW`: `0.137549` | Exact match |
| **Unsized Baseline Delay** | 62.21 ps | `62.21` ps | `results/gpdk045/final/U8k.tsv` col `delay_ps`: `62.21` | Exact match |
| **Unsized Baseline PDP** | 8.557 fJ | `8.557` fJ | `results/gpdk045/final/U8k.tsv` col `pdp_fJ`: `8.557` | Exact match |
| **M7 Saturation Voltage (Vdsat)** | 0.358 V (357.8 mV) | `0.3578` V | `results/gpdk045/final/D_1p4.m7vdsat.txt`: `357.8 mV` | Exact match |
| **Assura DRC Error Count** | 21 errors across 3 rules | `21` errors | `results/gpdk045/assura_drc_dlatch_summary.txt`: Rule 220 (1), Rule 221 (6), Rule 595 (14) | Exact match |

**Finding:** All 21 audited numerical values in the report abstract/conclusion/tables match the authenticated simulation data without a single discrepancy.

### Figure Provenance Verification
Report Section "TOOL & TECHNOLOGY USED" (Page 4) explicitly states:
> *"Origin of the figures: the schematic and layout editor views, the Assura DRC summary and the ViVA waveform of design D are screenshots of Cadence tool windows. The other waveforms, sweeps and PVT maps are plots made with Python (matplotlib) from the Spectre result files, and the circuit diagrams are drawn by a script from the netlist. No figure was produced by an image-generation model, and every plotted point comes from a Spectre result file."*

Audit of figure source files in `report/gpdk045/figures/` and `report/gpdk045/screens/`:
1. **Cadence Tool Screenshots (Virtuoso / ViVA / Assura):**
   - Figure 2: `screens/schematic_core_full.png` (Virtuoso Schematic Editor)
   - Figure 4: `screens/schematic_dlatch_full.png` (Virtuoso Schematic Editor)
   - Figure 5: `screens/viva_tran_D_1p4GHz_full.png` (Cadence ViVA Waveform Viewer)
   - Figure 7: `screens/layout_core_full.png` (Virtuoso Layout XL Editor)
   - Figure 20: `screens/layout_dlatch_full.png` (Virtuoso Layout XL Editor)
   - Figure 21: `screens/drc_result.png` (Assura DRC Terminal Log)
2. **Script-Drawn Schematics:**
   - Figure 1: `figures/fig_circuit_latch.png` (Generated by `scripts/draw_gpdk45_circuits.py`)
   - Figure 8: `figures/fig_circuit_ring.png` (Generated by `scripts/draw_gpdk45_circuits.py`)
3. **Spectre Data Plots (Python Matplotlib):**
   - Figures 3, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 22. All generated by `scripts/gpdk45_final_figs.py` and `scripts/gpdk45_pvt_replot.py` directly from raw simulation TSVs.

**Finding:** The provenance disclosure is 100% truthful and satisfies the strict academic integrity mandate of `AGENTS.md`.

---

## Deliverable B: 23ECE302 Theory Assignment (15 Marks)

Deliverable B corresponds to the theory component evaluated under the rubric:
- **Implementation (7 marks)**
- **Applying Sizing Concept (8 marks)**

### Current File Status
- **Existing File:** `report/gpdk045/23ECE302_Theory_Assignment_gpdk045.md` (Markdown text only, 66 lines).
- **Compiled Formats (.docx / .pdf):** **NONE EXISTS**. There is no `23ECE302_Theory_Assignment_gpdk045.docx` or `23ECE302_Theory_Assignment_gpdk045.pdf` anywhere in the repository.

### Compliance & Rubric Evaluation Table

| Requirement / Item | Source (Rubric Line / Format Doc) | Status | Evidence (Line / Section in Markdown) | Fix Needed / Action Required |
|---|---|---|---|---|
| **Submit-Ready PDF / DOCX Document** | Submission Requirement | **Missing** | Only Markdown exists in `report/gpdk045/`. No PDF or DOCX file has been generated. | Convert/compile the assignment into an official PDF document formatted with Amrita cover page. |
| **Institutional Front-Matter & Cover Block** | Format Doc, Page 1 | **Missing** | Missing all front-matter: no Amrita logo, student register number, name, batch number, or date. | Add official Amrita assignment cover page. |
| **Section 1: Transistor Schematic (7 Marks)** | Rubric: Implementation (7 Marks) | **Partly** | Section 1 (Lines 5–27) describes device connections, latch operation, and phase separation in text. | **Critical Defect (Line 26):** Contains unfilled prompt instruction: *"Draw the full schematic of Fig. 2 with every net labelled and mark which latch uses CK and which CKb."* No schematic drawing or image is embedded! |
| **Section 2: Elmore Delay Analysis** | Rubric: Applying Sizing Concept (8 Marks) | **Met** | Section 2 (Lines 37–50): Mathematical derivations for $t_{pdf} = (8C)(R/2) = 4RC$, $t_{pdr} = (8C)(R1) = 4RC$, rise/fall symmetry, and speed limit $2 T_d < T_{CK}/2$ are fully detailed. | None in text derivation. |
| **Section 2: Sizing Concept & Tuned Values Table (8 Marks)** | Rubric: Applying Sizing Concept (8 Marks) | **Partly** | Lines 54–61: Sizing table is present with device W/L starting values and rationales. | **Critical Defect (Lines 56–60):** The entire "Tuned value" column is composed of literal blank underlines: `\| ___ \|` for M1–M2, M3–M4, M5–M6, M7, and R1–R2! |
| **Section 2: Sizing Threshold Explanation** | Rubric: Applying Sizing Concept (8 Marks) | **Partly** | Lines 62–66: Explains why 1.5 kΩ fails and 8 kΩ was chosen. | Mentions pre-check on generic LEVEL=1 180 nm model; should explicitly cite the GPDK045 45 nm regenerative stack rule ($R \ge 1.1 \times 3 R_{on}/m = 7.59\text{ k}\Omega$). |

### Dual-Submission Context: Joint Report vs Separate Deliverable
- **Crucial Context:** Dr. Kaveri Hatti's official format document (`System Design Project Report_format (1).doc`) explicitly combines both course titles on Page 1:
  > *ASSIGNMENT FOR 23ECE302 VLSI DESIGN*  
  > *SYSTEM DESIGN FOR 23ECE383 VLSI DESIGN LABORATORY REPORT*
- **If the department accepts a SINGLE COMBINED REPORT:** The 25-page `System_Design_Project_Report_gpdk045.pdf` already contains Section 1 (Circuit Schematics, Figs. 1, 2, 8), Section 2 (Elmore Delay & Sizing Theory, Page 3), Sized Devices (Table 2, Page 9), and Sizing Performance Proofs (Table 3, Page 10). Under a joint submission, all 15 marks of Deliverable B are satisfied.
- **If the department requires a SEPARATE SUBMISSION for 23ECE302:** Deliverable B is currently **COMPLETELY UNREADY** (0/15 marks safe) because it is an incomplete Markdown file with empty blanks and missing schematics.

---

## Action Plan: Blockers & Nice-To-Have

### BLOCKERS Before Submission (Ordered by Marks at Risk)

1. **Deliverable B: Missing Compiled Deliverable (15 Marks at Risk)**
   - *Issue:* If 23ECE302 requires an independent submission, only an incomplete Markdown draft exists.
   - *Fix:* Create a standalone, submit-ready PDF for 23ECE302 with:
     * Official Amrita assignment cover page.
     * Transistor schematic diagram embedded (embed `figures/fig_circuit_ring.png` or `figures/fig_circuit_latch.png`).
     * Sizing table filled with tuned values: M1–M6: $W = 240\text{ nm}, L = 45\text{ nm}, m = 4$; M7: $W = 480\text{ nm}, L = 90\text{ nm}, m = 4$; R1, R2: $3\text{ k}\Omega$ (Design D) and $2\text{ k}\Omega$ (Design B).
     * Remove the placeholder text *"Draw the full schematic..."*.

2. **Deliverable A: Blank Student & Guide Metadata on Cover Page (5 Marks at Risk under Report Rubric)**
   - *Issue:* Table 0 (Page 1) student register numbers, names, signatures, batch number, and faculty signature line are completely blank.
   - *Fix (STUDENT ONLY):* The student must supply:
     * Student Register Number(s) (e.g., `BL.EN.U4ECE...`).
     * Student Name(s).
     * Physical or digital signatures with date.
     * Lab Batch Number (e.g., `Batch 1`, `Batch 2`, `EAC-A`).
     * Faculty evaluator name (`Dr. Kaveri Hatti`) and evaluation date.

3. **Deliverable A: 7 Unreferenced Figures in Report Prose (2 Marks at Risk under Academic Rigor)**
   - *Issue:* Figures 4, 6, 10, 17, 18, 19, and 22 are captioned but never cited anywhere in the report body text.
   - *Fix:* Insert explicit in-text citations in `report/gpdk045/report_data.json` so that every figure is introduced and discussed in prose prior to appearance.

4. **Deliverable A: Unrouted Placement Layout Limitation Disclosure (1–2 Marks at Risk under Layout Rubric)**
   - *Issue:* Rubric allocates 5 marks for Layout. The layout is placement-only (21 Assura DRC errors, unrouted, no LVS, no RC extraction).
   - *Fix:* Ensure the report's frank disclosure remains prominent: the PDK lacks Assura RCX extraction runset files, which prevents post-layout netlist generation. Academic integrity dictates submitting the DRC-documented placement rather than claiming unverified post-layout metrics.

---

### NICE TO HAVE (Quality & Polish Improvements)

1. **Font Substitution in PDF (`LiberationSerif` vs `Times New Roman`):**
   - Install `msttcorefonts` on the Linux host system (`sudo apt-get install ttf-mscorefonts-installer`) or open `System_Design_Project_Report_gpdk045.docx` in Microsoft Word and export to PDF.
2. **Table of Contents & List of Figures:**
   - Although omitted in the 3-page format template, adding an automated Table of Contents on Page 2 elevates the 25-page report to professional publication standard.
3. **Table 2 Page-Break Whitespace Reduction:**
   - Adjust spacing or figure scaling on Page 8/9 so that Table 2 and the Section 10 heading flow naturally without leaving a 7.5-inch blank white void on Page 9.
4. **ViVA / ADE XL PVT Screenshot:**
   - Replace or supplement the Python matplotlib heatmap (Figure 6) with a direct Cadence ADE XL / ViVA corner sweep plot if the Cadence VM is ever booted for post-v1 maintenance.

---

## Audit Summary Scorecard

| Deliverable | Total Marks | Met | Partly | Missing | Cannot Verify | Submission Readiness |
|---|---|:---:|:---:|:---:|:---:|---|
| **Deliverable A: 23ECE383 System Design Project Report** | 40 Marks | 18 | 7 | 4 | 0 | **Submission-Ready pending Student Metadata & Citations** |
| **Deliverable B: 23ECE302 Theory Assignment** | 15 Marks | 1 | 3 | 2 | 0 | **NOT Ready (Needs Compilation & Blank Fill-in)** |

*Note: For Deliverable A, the 4 items categorized as Missing (Abstract, Certificate/Declaration/Acknowledgement, Table of Contents, List of Figures/Tables) are standard academic monograph conventions that are absent from both the university's 3-page template and the report.*
