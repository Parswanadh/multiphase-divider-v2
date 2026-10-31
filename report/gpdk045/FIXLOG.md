# Fix log for REVIEW.md

Rebuilt report: 35 pages, 0 NOT YET AVAILABLE markers. Rulings applied: the without-sizing column is the dividing unit-size baseline U8k (m = 1, R = 8 kOhm, vb = 1.0 V); the paper-rule circuit (m = 1, R = 1.15 kOhm) is kept as a non-dividing finding; no re-layout; no VM access. Figure numbering is now dynamic: the post-layout waveform slot is a plain sentence without a number, so named figures are 1 to 7 and additional figures 8 to 23. Scripts changed: make_report_data.py, build_academic_docx.py, gpdk45_final_figs.py (also regenerated results/gpdk045/final/analysis.json); new: scripts/gpdk45_pvt_replot.py, report/gpdk045/assets/amrita_logo.jpeg. README_report.md was not updated (its text about fixed figure numbers is now out of date).

## Critical
- C1: fixed. "Layout: what was done" and the Conclusion state that the transistors are unit size (m = 1; M1 to M6 2 x 120 nm, M7 4 x 120 nm, no multiplier), that design D needs 4 times the width, that the layout matches neither simulated design, and that an m = 4 / 3 kOhm layout was not produced (ruling 2, no re-layout). Fig 22 caption says unit-size (m = 1). All sizes are parsed from build_layout_v2.il and layout_build_log.txt.
- C2: fixed. Corrected Elmore lower bound Td >= R1 C_L (30 ps for D, 20 ps for B), bound met at both points, B at its measured frequency limit (fails at 6.2 GHz). The false "66.10 ps exceeds T_CK/2" wording was not used (66.10 ps is 79 percent of T_CK/2); the text says 3.3 times the lower bound. No "bound not met" text remains.
- C3: fixed. Logo copied to report/gpdk045/assets/ and set in the data; it renders on page 1.
- C4: fixed. Library Manager slot dropped, every reference renumbered (figure paragraph and all "Figure N" mentions checked in the re-extracted PDF text; all 23 captions exist and every reference resolves).

## Important
- I1: fixed. t_pair is measured by gpdk45_final_figs.py (paired-edge gap Q2 to Q3b) and stored in analysis.json: 25.95 ps (D), 38.16 ps (B), 73.75 ps (U8k). Law a = 360 t_pair f_out = 180 t_pair f_in and T_CK = 4 t_pair, each a reproduced from t_pair to within 0.05 deg.
- I2: fixed. Relabelled as the t = 0 initial-condition point (CK and CKb low, no tail current); the triode conclusion rests on V(tail) in the transient against Vdsat; "at the bias" replaced by Vds about 54 nV at t = 0.
- I3: fixed. Without-sizing column is the U8k row (0.1375 mW, 62.21 ps, 8.557 fJ, 26.42 deg, swing 0.2289 V, tail check from its raw). Paper-rule supply power 0.165 mW is stated as a finding (computed as supply_avg_ma_steady x VDD). Comparison states that sizing cuts delay but raises power, PDP, phase error and swing.
- I4: fixed. Per-row proof column (power Fig 15, phase error Fig 11, tail Figs 12 and 13, delay "no figure: analysis.json"), plus a note defining the delay metric and the CK-to-Q1 first-edge values.
- I5: fixed. DRC paragraph now attributes the 14 Metal1 errors to isolated contact pads in the transistor rows (0.06 x 0.12 um markers; the summary lists 4 of the 14), the 6 Rule 221 markers to the unconnected pcell taps (0.755 um pitch equals the device pitch, checked by the script), and "0.02 um^2".
- I6: not fixed: recapturing the schematics needs the Cadence VM, which was off limits. Partial: captions now say that the top level is common to the designs, that connectivity is by net labels and give the schCheck counts; no separate m = 1 schematic exists and the caption says so.
- I7: not fixed: layout screenshots with mask layers need the VM. The captions and the "what was not done" text now say they show cell outlines only.
- I8: fixed. Figure maximum height lowered to 7.0 in; Figure 5 now sits with its caption on page 11.
- I9: fixed. Black sentence, no figure number: "Post-layout simulation was not performed ...".
- I10: fixed in text. W and L come from the netlist; m, R, vb, f_in are per-run overrides recorded in the TSV tag; read-back "agrees with Table 2 and the W and L of Table 1". The netlist defaults were not changed (out of scope).
- I11: not fixed: no Spectre terminal log exists on disk and the VM was off limits. Partial: the raw-file header (Plotname, date) of D_1p4.raw is quoted in Tool and Technology and the text states that no terminal screenshot of the run is included.

## Minor
- M1: fixed. Sweep text lists the swept and failing frequencies from the files and states that 1.4 GHz also divides and 1.4 to 3 GHz was not swept.
- M2: fixed. States that the clock-star length is a computed Manhattan distance and no clock wire is drawn.
- M3: fixed. Conclusion qualifies design B (Q1 swing 0.135 V against 0.1 V, tt 27 C 0.9 V corner fails, fails at 6.2 GHz).
- M4: fixed. XD1 range with "XD2 up to 68.2 mV" in the Figure 5 caption and the tail text.
- M5: fixed. B's M7 is stated to be in triode with the same Vdsat (script checks the m7op files of B and D are identical); Figure 14 (fig_tail_saturation_B_6g) added.
- M6: fixed. "outputs at 2 x f_in (2.8 GHz for a 1.4 GHz input)", swing range read from the files.
- M7: fixed. Rows set to cannot split.
- M8: fixed. Fixed decimals (delay 2, power 4, PDP 2) and notes rewritten ("outputs at 2 f_in, swing ... < 0.1 V"); ratio = f_in / f_out defined in the table caption.
- M9: fixed. Captions corrected; new scripts/gpdk45_pvt_replot.py redraws the delay/power plots with the y axis clamped at 0 and failing points as a counted cross at the foot (gpdk45_pvt_report.py itself was not edited).
- M10: fixed. fs_F mentioned as an exploratory sweep with its per-(m, R) results read from the file.
- M11: not fixed: Times New Roman is not installed on this machine (only Liberation Serif), so the PDF embeds Liberation Serif; the docx still asks for Times New Roman and exports correctly from Word.
- M12: partly fixed. Title-page member table now has visible borders and the references are kept together. Not fixed: register numbers, names and signatures stay blank by design (student fills them); some pages are still part empty because large figures do not share pages.
- M13: fixed. Full author list added; the paper's unit nMOS (0.9 um / 180 nm, W/L = 5.00) is compared with 240 / 45 nm (5.33).

Counts: 23 fixed, 5 not fixed or only partly fixed (I6, I7, I11, M11, M12).
