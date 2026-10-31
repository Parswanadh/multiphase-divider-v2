# Independent review: System_Design_Project_Report_gpdk045.pdf

Reviewed file: `report/gpdk045/System_Design_Project_Report_gpdk045.pdf`, 28 pages, md5 `99e3c282b60b32b9b9935e8d9ecba853`, written 2026-10-31 19:21:49. Page numbers below are this PDF's footers.

Note: `/home/parshu/vm/report_text.txt` was extracted 6 s before this PDF was written. It differs in one paragraph, the figure-numbering paragraph on p.16. All citations here come from a fresh `pdftotext` of the PDF.

Ground truth used:
- `results/gpdk045/final/*`, plus the Assura, Virtuoso and connectivity files and `layout_build_log.txt`
- `spectre/divider_gpdk45.scs` and `cadence/skill/build_layout_v2.il`
- `LEDGER.md`
- the paper PDF in the repo root
- my own edge timing from `D_1p4.raw` and `B_6g.raw`

## Verdict

The numbers match the Cadence Spectre data, and the main caveats are stated honestly. It is not ready to submit, for four reasons:
- the layout's transistors are m = 1, and the report does not say so
- the Elmore section contradicts itself and draws the wrong conclusion from it
- two red NOT YET AVAILABLE markers have no valid reason to be there
- several theory and presentation errors remain

Counts: 4 Critical, 11 Important, 13 Minor.

## Critical

**C1. The layout transistors are unit size (m = 1), not design D (m = 4), and the report does not say so.**
- Where: p.14 "Layout: what was done"; p.25 Fig 21 caption; p.26 Conclusion "Layout status".
- Evidence:
  - `cadence/skill/build_layout_v2.il` lines 29-34 set `divFw "120n"`, `divNf1 2` and `divNf7 4`.
  - `divMosSets` (lines 116-131) passes only fw, l, fingers, connectGates and tap. It never passes `m`.
  - `results/gpdk045/layout_build_log.txt` lines 4-10 show 7 single placements, each with an MOS bBox 0.595 um wide.
  - So M1-M6 are 2 x 120 nm = 240 nm and M7 is 480 nm, which is the m = 1 sizing.
  - Design D (Table 2, `virtuoso_dlatch_params_designD.txt`) is m = 4.
  - The report discloses only the resistor mismatch (2 kOhm laid out against 3 kOhm simulated). A reader therefore takes the transistors to be correct.
- Fix:
  - Add to "Layout: what was done": "The transistors in the layout are unit size: one nmos1v pcell per device, M1 to M6 with 2 x 120 nm fingers (240 nm) and M7 with 4 x 120 nm (480 nm), no multiplier. This is the m = 1 sizing; design D needs four times the width (m = 4). With the 2 kOhm placeholder resistors, the layout matches neither simulated design."
  - Change the Fig 21 caption to "7 unit-size (m = 1) nmos1v pcells ...".
  - Better: rebuild with 4x fingers, or with m = 4 on the pcells, and re-run DRC.

**C2. The Elmore estimate contradicts its own definition of C.**
- Where: pp.3-4, Theory, "Elmore estimate".
- What the report says:
  - It defines C as "the node capacitance".
  - It then computes Td = 4RC with C = 10 fF, giving 240 ps for D and 160 ps for B.
- Why that is wrong:
  - In the paper (eqs. 1-2) the Q-node capacitance is (6 + 2)C = 8C and the resistance is R/2.
  - Plugging the 10 fF load in as C puts 8C = 80 fF on the node. That contradicts both the report's definition and the 10 fF load.
  - The "(bound not met)" verdicts at both points rest on this 8x inflation.
  - This paragraph supports the sizing concept, which carries 8 marks.
- Fix: rewrite the paragraph as follows.
  - **Correct estimate.** Take the node capacitance 8C as at least C_L = 10 fF. Then Td is at least (8C)(R/2) = R1 x C_L:
    - design D: 30 ps
    - design B: 20 ps
    - This is a lower bound, because device parasitics are neglected.
  - **1.4 GHz (design D).** 2Td of at least 60 ps against T_CK/2 = 357 ps leaves a clear margin.
  - **6 GHz (design B).** 2Td of at least 40 ps against T_CK/2 = 83 ps.
    - B is at its measured limit: it fails at 6.2 GHz, where T_CK/2 = 80.6 ps.
    - The measured CK-to-Q1 delay of 66.10 ps exceeds T_CK/2.
    - So the lower-bound estimate is optimistic at 6 GHz. Keep a qualified form of "this bound is not what decides division" for B.
  - **Delay comparison.** Do not compare Td with the 25.99 / 27.94 ps table delay. That metric is CK to the next edge of any output, not the paper's D-to-Q latch delay.

**C3. The red logo marker on the title page (p.1) is not justified.**
- The logo exists at `/home/parshu/vm/fmt/assets/amrita_logo.jpeg`. It is the 474x136 image on p.1 of the official `format.pdf`.
- `report_data.json` line 3 has `"logo": null`.
- Fix: point `logo` at that file (copy it into `report/gpdk045/`) and regenerate.

**C4. The red Figure 20 marker (p.24) is not justified, and the text cites a figure that does not exist.**
- The marker reads "additional figure 12 (file not found: screens/library_manager.png)". This exposes the generator's internal slot name.
- The figure-numbering paragraph on p.16 lists "the Library Manager (Figure 20)".
- The screenshot is optional and was never captured.
- Fix: either capture it, or drop the slot and renumber Fig 21 to 20 and Fig 22 to 21. If renumbering, also update:
  - "Figure 21 the DLATCH layout" on p.14
  - "(Figure 22)" in the DRC paragraph on p.15
  - the figure-numbering paragraph on p.16

## Important

**I1. The phase-step law is off by a factor of 2.**
- Where: p.4, "Phase-step law".
- The report says t_pair = 13.0 ps at 1.4 GHz and 19.1 ps at 6 GHz, and that "Equal 45 deg steps need T_CK = 8 t_pair".
- The phases are in output-period degrees (Q1b sits at 180 deg).
- From the raw files, the paired-edge gap Q2 to Q3b is 25.95 ps for D (357.13 - 331.18) and 38.17 ps for B (83.34 - 45.17).
- Fix: "a = 360 t_pair f_out = 180 t_pair f_in; a = 6.54 deg gives t_pair = 25.95 ps (1.4 GHz) and a = 41.22 deg gives 38.17 ps (6 GHz); equal 45 deg steps need T_out = 8 t_pair, i.e. T_CK = 4 t_pair."

**I2. The "DC operating point" is a zero-current point at t = 0, but the report presents it as a normal DC analysis.**
- Where:
  - p.7 Fig 3 caption
  - p.7 sizing text: "M7 is in the triode region in the DC analysis (Vds stays below Vdsat)"
  - p.15 DC-op paragraph and the "Tail device M7" paragraph: "gm = 200.9 pS, gds = 2.531 mS at the bias"
- Why: VCKB has `val0=0 delay=tck/2`, so at t = 0 both CK and CKb are low. M5 and M6 are then off, and Ids is only 35.6 pA (unsized) and 137 pA (D).
- `D_1p4.m7vdsat.txt` was taken at that same point.
- Fix:
  - Write "t = 0 initial-condition point, CK and CKb both low, no tail current".
  - State that the triode conclusion rests on the transient: V(tail) is 8.1 to 66.9 mV against Vdsat = 357.8 mV. Vdsat is set by Vgs = 1 V, which is the same in the transient.
  - Replace "at the bias" with "at the t = 0 point (Vds about 54 nV)".
  - In the sizing text, replace "in the DC analysis (Vds stays ...)" with "in the transient".

**I3. The "without sizing" column is all n/a, and this contradicts the LEDGER ruling.**
- Where: p.5 and p.10, Table 3.
- LEDGER says: "it does not divide, so its delay/PDP are n/a and only power is reported".
- The report says: "the power of a non-dividing circuit is not reported".
- The data does have the number: `analysis.json` unsized `supply_avg_ma_steady` = 0.16517 mA, which is 0.165 mW at 1.0 V.
- Fix: choose one.
  - Either put "0.165 mW (supply power of the non-dividing circuit; not comparable)" in Power/without and cite `analysis.json`.
  - Or change the LEDGER ruling.
- Recommended for the sizing marks: add a dividing m = 1 baseline.
  - The stack rule predicts R >= 1.1 x 3 x 2.3 kOhm = 7.6 kOhm.
  - This needs a new Spectre run. No gpdk045 data exists for it, so the old generic 8k numbers must not be reused.

**I4. The proof column of Table 3 is generic and partly wrong.**
- Where: p.10.
- Every row cites "Fig. 3 (without), Fig. 5 (with)", including rows whose value is n/a.
- Fix:
  - Power: Fig 13
  - Phase-step error: Fig 11
  - Tail check: Fig 12
  - Delay: there is no figure. Cite `analysis.json` (`ck_to_any_output_mean_delay_ps` = 25.985) and say so, or add a zoomed CK-to-output edge plot.
  - Cite Fig 3 only where a "without" value exists (f_in, swing).
  - Add a footnote: "delay = CK rising edge to next rising edge of any of the 8 outputs; CK to Q1 = 51.95 ps".

**I5. The DRC paragraph attributes the errors to the wrong shapes.**
- Where: p.15, "Layout: Assura DRC".
- The report says the 14 Metal1 area errors are "on the pin shapes".
- In `assura_drc_dlatch_summary.txt` the markers are 0.12 x 0.06 um (0.0072 um^2). They sit inside the MOS rows, at x 0.96 to 4.175 um and y 1.00 to 2.02 um.
- The script's pins are 0.20 x 0.15 um = 0.03 um^2, which is at least 0.02 um^2 (LAYOUT_NOTES section 6), so the pins pass.
- The Rule 221 markers repeat at a 0.755 um pitch, which is the device pitch. That points to the pcells' integrated taps being unconnected.
- Fix:
  - "Marker coordinates indicate that the 14 Metal1 area errors are isolated Metal1 contact pads in the transistor rows, and the 7 substrate-stamp errors are the unconnected integrated taps of the pcells."
  - Change "at least 0.02 um" to "0.02 um^2".

**I6. The schematic evidence is weak (rubric item: Implementation, 7 marks).**
- Where: pp.5-8, p.23.
- The "simulator based circuit implementation" slot is for the unsized circuit, but it shows Fig 2, the core of the design D library. No m = 1 / R = 1.15 kOhm schematic exists; LEDGER's ruling leaves it out.
- Figs 2, 4 and 18 have these problems:
  - they are mostly empty black canvas
  - the devices are tiny
  - no instance names and no w/l/m/r labels are shown
  - connectivity is by net-label stubs, not wires
  - the sizes in the Fig 4 caption cannot be seen in the image
- Fix:
  - Rebuild the DLATCH with resR = 1.15k and mult = 1 and capture it; LEDGER estimates about 5 min. Or say in the Fig 2 caption that the top level is common to both designs and that the unsized DLATCH differs only in m and R (Table 1).
  - Recapture zoomed to the devices, with instance and CDF parameter labels shown, and preferably a white background.
  - Add "connectivity by net labels; schCheck 0 errors" to the captions.

**I7. The layout screenshots show only cell outlines, no mask geometry.**
- Where: p.14 Fig 7, p.25 Fig 21.
- Fig 7 shows four boxes labelled "DLATCH". Fig 21 shows named pcell boxes. Both look like display depth 0.
- Fix: set the display levels to 0-32 (Shift+F) and recapture.
  - Fig 7: the whole core.
  - Fig 21: zoom on the transistor row so poly, diffusion and Metal1 are visible.

**I8. Figure 5 is on a different page from its caption.**
- The image is on p.9 and the caption is at the top of p.10.
- Fix: set keep-with-next on the figure paragraph, or reduce the image height so it fits with the heading.

**I9. The red Figure 8 marker (p.14) is a valid gap, but it reads as unfinished.**
- Fix:
  - Replace it with black body text: "Not performed: the layout is placement-only (not routed, not extracted), so no post-layout simulation exists; all results in this report are pre-layout."
  - Do not give the gap a figure number, and update "Figures 1 to 8 are the named slots" on p.16.

**I10. The netlist the report cites does not contain the sizes it claims, and one sentence contradicts Table 1.**
- Where:
  - p.3 Fig 1 caption: "from spectre/divider_gpdk45.scs ... m = 4; R1 = R2 = 3 kOhm"
  - p.5: "Device sizes are read from spectre/divider_gpdk45.scs"
  - p.4: "These agree with the Spectre netlist sizes and with Tables 1 and 2"
- The netlist (line 14) defaults are `rl=8k vb=0.8 mult=1 fin=1G`, left over from the old pre-check. The actual m, R, vb and f_in are per-run overrides recorded in the tag, for example `g_1.4G_3k_1.0_10f_m4`.
- The read-back (m = 4, R = 3K) contradicts Table 1 (m = 1, 1.15 kOhm).
- Fix:
  - "W and L are from the netlist; m, R, vb and f_in are per-run parameter overrides recorded in each TSV tag (g_<fin>_<R>_<vb>_<CL>_m<m>)."
  - "These agree with Table 2, and with the W and L of Table 1."
  - Optionally set the netlist defaults to design D.

**I11. The report has no screenshot of the simulator itself.**
- The rubric asks for "screenshots as proof". Every waveform, PVT and sweep figure is a matplotlib plot. The plots are labelled honestly.
- The only Cadence evidence of simulation is the CIW of Virtuoso (Fig 19, unreadable at page size), not Spectre.
- Fix: add at least one terminal capture of the Spectre run for D_1p4, showing the version banner and "spectre completes with 0 errors". If possible, also add a ViVA or AWD plot of one raw file. Cite it next to Fig 5.

## Minor

**M1. Sweep wording, p.15.**
- "Design D ... divides from 3 to 5.5 GHz" and "E ... from 3 to 7 GHz" read as if both fail below 3 GHz. In fact the `fs_D` and `fs_E` sweeps start at 3 GHz, and D and E also divide at 1.4 GHz (Table 3, `pvt_E` tt_27_1.0).
- Fix: "the 3 to 8 GHz sweep of D divides at 3 to 5.5 GHz and fails at 6, 6.5, 7 and 8 GHz; 1.4 GHz also divides; 1.4 to 3 GHz was not swept."

**M2. Clock-star length, p.14.** "The clock-star lengths are equal (98.62 um each)" is a computed Manhattan distance from the pins to the array centre (LAYOUT_NOTES). No clock wire is drawn. Say so.

**M3. "Both operating points work", p.25.**
- Qualify this for design B. Its Q1 swing is 0.135 V (0.818 to 0.953 V) against the 0.1 V criterion.
- Its tt 27 C 0.9 V corner fails, and it fails at 6.2 GHz.

**M4. Tail voltage range, p.10 Fig 5 caption and p.15.**
- "Tail voltage stays between 8.1 and 66.9 mV" is for XD1 only.
- XD2 reaches 68.2 mV (`analysis.json` `xd2_tail_max_v`).
- Fix: write "XD1; XD2 up to 68.2 mV". The conclusion does not change.

**M5. Design B saturation check, p.15.**
- "Vdsat of M7 was not extracted for this point, so its saturation check is n/a" is overly cautious.
- B's M7 has the same W, L, m and Vgs = 1 V as D's (the m7op files are identical), so Vdsat is about 358 mV against a tail maximum of 66.2 mV. B is also triode.
- `figures/fig_tail_saturation_B_6g.png` already exists.

**M6. False-pass description, p.26.**
- "Outputs at 2 or 2.8 times the expected frequency": the final data show the unsized Q1 at 2799.8 MHz. That is 2 x f_in, or 4x the expected f_in/2.
- Fix: "at 2 x f_in (2.8 GHz for 1.4 GHz input)".

**M7. Table 4 row split across pages.**
- The B6 fs 27 C 0.9 V row breaks across p.12/p.13: "ratio 0.5000" is on one page and "not 2" on the next.
- Fix: set rows to "cannot split".

**M8. Table 4 formatting.**
- Decimals are inconsistent, for example 23.5, 27.7, 0.891, 16.8, 23.0 and 28.3. Use fixed decimals: delay 2, power 4, PDP 2.
- The note "ratio 0.5000 not 2" is cryptic. Use "outputs follow CK at 2 f_in, swing 0.03 to 0.05 V < 0.1 V", and define ratio = f_in/f_out.

**M9. Fig 15 and Fig 17 captions, pp.22-23.**
- The captions say "passing points only", but the plots draw FAIL markers.
- The power axis in Fig 17 runs down to -0.4 mW.
- Fix: change the caption and clamp the y axis at 0.

**M10. `fs_F.tsv` is never mentioned.**
- It holds 16 points: m4/m5, 2.2k/2.5k, 5.5 to 6.25 GHz.
- m4 with 2.2k divides at 6.25 GHz with 5.57 deg error. Mention it in one line, or say that it is exploratory.

**M11. Font.**
- The PDF embeds Liberation Serif because LibreOffice substituted it. The docx asks for Times New Roman 12/14, and the format requires TNR.
- Fix: export with TNR installed, or export from Word.

**M12. Title page and page layout.**
- The format has four member rows (register number, name, signature); the report has one header and blank space. Fill them in before submission.
- p.28 holds a single orphaned reference line. Keep the references together.
- pp.19-20 are half empty.

**M13. Paper details, p.2.**
- List the full authors: Yue-Fang Kuo, Shih-Hung Lin, Bo-Yi Chen and Liang-Chen Liu.
- Optionally state the paper's unit size (W = 0.9 um, L = 0.18 um, W/L = 5) against 240/45 nm (5.33) in the sizing argument.

## Markers

| # | Page | Marker | Is it a valid gap? | Fix |
|---|---|---|---|---|
| 1 | p.1 | "NOT YET AVAILABLE: institution logo image" | No. `/home/parshu/vm/fmt/assets/amrita_logo.jpeg` exists. | Set `logo` in `report_data.json` (C3). |
| 2 | p.14 | "NOT YET AVAILABLE: Figure 8 - simulator waveform screenshot of the layout" | Yes. The layout is not routed or extracted. | Replace with a black "Not performed ..." sentence and drop the figure number (I9). |
| 3 | p.24 | "NOT YET AVAILABLE: Figure 20 - additional figure 12 (file not found: screens/library_manager.png)" | No. It is an optional screenshot that was never captured. | Delete the slot and renumber 21 to 20 and 22 to 21, or capture it (C4). |

The blank register and name fields on the title page are blank by design, but they must be filled in before submission.

## Rubric table

The title page and all 20 headed sections of the official format are present, in the official order. No section is missing.

| Rubric item (marks) | Status | Evidence | What is missing |
|---|---|---|---|
| Implementation, schematic (7) | Partial | Real Virtuoso captures: Fig 2 (p.6), Fig 4 (p.8), Fig 18 (p.23). DB read-back m = 4, R = 3K (p.4). Core connectivity 0 mismatches, which I checked against the netlist ring. | No unsized schematic. The figures are unreadable and show no parameters (I6). |
| Applying sizing concept (8) | Partial | Stack rule and 5/5 LEDGER pairs (p.4), Tables 1-2 (pp.5, 8), Table 3 (p.10) | Elmore error (C2), phase law off by 2x (I1), "without" column all n/a (I3) |
| Functionality, DC and/or transient (10) | Covered for transient, weak for DC | Figs 3, 5 and 10. Strict 8-output check (p.4). Unsized non-division explained (p.5). | DC is only the degenerate t = 0 point (I2). No simulator screenshot (I11). |
| Power (5) | Covered | 0.5413 mW (Table 3); cross-check 0.54144 mA, 0.018% (p.16); Fig 13 | Without-sizing value (I3); proof figure mapping (I4) |
| Delay (5) | Covered, with caveat | 25.99 ps, definition (p.4), CK to Q1 = 51.95 ps (p.16) | No proof figure; footnote in Table 3 (I4) |
| PDP (5) | Covered | 14.067 fJ (Table 3); per-corner PDP (Table 4) | Without-sizing comparison (I3) |
| PVT (5) | Covered | Table 4 (90 rows, all verified, FAIL rows kept), Figs 6 and 15-17, counts and fail lists for D, B, E and B6 (pp.15-16) | Cosmetic only (M7-M9) |
| Layout (5) | Partial | Placement of DLATCH and core (Figs 7 and 21); real Assura DRC, 21 errors in 3 rules (Fig 22); limits disclosed (pp.14-15, p.26) | Devices are m = 1 (C1); outline-only screenshots (I7); no routing, LVS, PEX or post-layout sim; error attribution (I5) |
| Report (5) | Partial | All format sections in order; honest captions; cross-checks | 3 red markers, figure/caption split (I8), unreadable captures, font (M11) |

## Number audit

**Verified, matches the data:**
- **Table 3:** P 0.5413 mW, delay 25.99 ps, PDP 14.067 fJ, f_out 700.0 MHz, phase error 38.46 deg, swing 0.0153 / 0.4344 V, Vds 0.0669 V, Vdsat 0.3578 V.
- **Unsized:** Q1 2799.8 MHz, 0.975 to 0.991 V.
- **DC points:** 56.3 nV / 35.6 pA; 54.4 nV / 137.4 pA; Vth 527.5 mV, gm 200.9 pS, gds 2.531 mS.
- **Table 4:** all 90 rows, PASS/FAIL and every value. The only difference is a half-unit rounding on one PDP.
- **PVT counts and fail lists:** D 41/45, B (1.4 GHz) 27/45, E 41/45, B6 21/45. The temperature breakdowns are correct.
- **D passing range:** 0.246 to 1.078 mW, 23.54 to 31.05 ps.
- **Sweeps:** limits correct; top-of-range errors 3.78 / 13.82 / 15.24 deg and bottom-of-range 38.68 / 30.89 / 34.32 deg.
- **B operating point:** 0.4929 mW, 27.94 ps, 13.768 fJ, 3.78 deg, 48.78 / 41.22 deg, swing 0.818 to 0.953 V, tail 66.2 mV.
- **Cross-checks:** delay 25.985 ps; current 0.54144 mA (0.018%); peak 0.560 mA; CK to Q1 51.95 / 66.10 ps; rise/fall 134.6 / 102.6 ps.
- **DRC:** 1 + 6 + 14 = 21.
- **Layout dimensions:** box 4.875 x 20.28 um; R 7.855 x 0.8 um, about 2.0 kOhm; star 98.62 um; placements R0 / MY / MX / R180 with 1 um gaps.
- **Stack rule:** 6.90k, 1.72k, 1.90k, band 1.88 to 2.25k, 5/5 pairs.
- **Clock period:** T_CK/2 = 357 / 83 ps.
- **Paper values** (checked against the paper PDF): vol. 35, no. 5, pp. 617-620, DOI, 180 nm, 1.8 V, 2.34 mW, 3.75 deg, 91.7 x 52.9 um^2.

**Mismatches or wrong derivations:**
- t_pair 13.0 / 19.1 ps should be 25.95 / 38.17 ps, and T_CK = 8 t_pair should be 4 t_pair (I1).
- Td 240 / 160 ps comes from plugging C_L in as C, which makes the node capacitance 8C = 80 fF. The calculation should use 8C = C_L, giving a lower bound of 30 / 20 ps (C2).
- Tail maximum 66.9 mV is XD1 only; XD2 reaches 68.2 mV (M4).
- "2 or 2.8 times the expected frequency" should be 4x (M6).
- "0.02 um" should be "0.02 um^2", and the "pin shapes" attribution is wrong (I5).

**Honesty checks with no problem found:**
- The layout is stated as not clean and not complete.
- M7 is stated as triode.
- There is no claim of matching the paper at 1.4 GHz.
- There is no claim of post-layout results.
- The plots are labelled as plots.
- There is no claim of power or delay for the unsized circuit.
- No 180 nm numbers appear as gpdk045, and no 8k / 5k / 1.5k values leak into the report text. 8k survives only in the netlist defaults (I10).
