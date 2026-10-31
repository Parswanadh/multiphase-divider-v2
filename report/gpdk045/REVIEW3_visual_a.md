# Visual QA, pages 1 to 10 (REVIEW3, reviewer a)

Read-only review of /home/parshu/.claude/jobs/30217dfb/tmp/qa/pages/p-01.png to p-10.png. Severity: high = blocks reading or looks broken, medium = noticeable, low = cosmetic.

| page | defect | severity |
|---|---|---|
| 1 | Title page is otherwise sound (AMRITA logo renders, footer "Page 1 of 29" present). Sign-off table (register number, name, signature) is empty, as intended for handwriting. "BATCH NUMBER:" and "FACULTY EXAMINER SIGNATURE WITH EVALUATION DATE" have no writing line after the label, so there is nowhere to write. | low |
| 2 | Figure 1 (DLATCH transistor schematic, centre of page) is too small to read at page size. Device labels (D, Q, Qb, M1 to M7, XD1 style net names), W/L annotations and the footnote line under the schematic are illegible. | high |
| 2 | Figure 1 caption is centred over three lines while the body text above is left/justified; minor alignment mismatch. | low |
| 3 | Text-only page, no figure issues. Run-in lead-in labels ("Topology.", "Elmore delay model.", "Stack resistance and regeneration.", "Phase-step relationship.", "Definitions of performance metrics.") appear as plain roman text, so they are not visually distinguished from the body. | low |
| 4 | ok (bottom about 12% blank, acceptable). | ok |
| 5 | Figure 2 (Virtuoso schematic editor, divider_core) is not legible at report size. Window title, menu bar, toolbar, instance names (XD1 to XD4) and net labels are unreadable; only the overall ring shape is visible. | high |
| 5 | Table 1: "Role" column wraps mid-phrase ("sampling pair (differential / inputs)"); acceptable but uneven row heights. | low |
| 6 | Figure 3 (transient waveforms, matplotlib plot filling about 70% of the page) has tick labels, the top title line, the "1.4 GHz" legend and the right-hand "phase" annotations set very small; they are hard to read at page size. The eight traces themselves are readable. | medium |
| 6 | Caption sits directly under the figure (no separation problem). Not a Cadence screenshot. | ok |
| 7 | Heading "Simulation driven directly from the Virtuoso schematic (OCEAN)" is in mixed-case bold, while every other section heading in the document is all-caps bold. | low |
| 7 | Table 2 is consistent with Table 1 in style (caption above, shaded header). No overflow. | ok |
| 8 | Figure 4 (Cadence DLATCH schematic, sizing applied) occupies the top half of the page; the caption and then roughly 40% of the page below are blank. | high |
| 8 | Figure 4 is not legible at report size (labels and net names unreadable, as with Figure 2). | high |
| 9 | Figure 5 (ViVA transient, design D) occupies the top half of the page; roughly 40% of the page below the single-line caption is blank. | high |
| 9 | Figure 5 traces are visible but signal names in the left legend, the y-axis tick values and the time-axis labels are too small to read; the Virtuoso/ViVA menus are illegible. | high |
| 9 | Section heading wraps to three lines ("SCREENSHOT OF THE OUTPUT WAVEFORM ... (DC AND TRANSIENT):"). Cosmetic. | low |
| 10 | Table 3 spans full width and renders cleanly; header row shaded, no overflow. | ok |
| 10 | In the "Tail-device saturation check" row, the bold values wrap to three lines with a colon at the end of the first line ("Vdsat = 0.3578 V:" / "NOT saturated"), which reads awkwardly. | low |
| 10 | "Proof (figure)" column entries wrap ("Fig. 15 (supply / current, both / columns)"). Acceptable but uneven. | low |
| 10 | Bottom about 20% blank below the notes paragraph; within the acceptable range. | ok |

Legibility of Cadence screenshots at report size: Figure 2 (page 5) not legible; Figure 4 (page 8) not legible; Figure 5 ViVA (page 9) partly legible (traces only, labels and axes not readable). Figure 1 (page 2) is a schematic rendered at very small size and is also not legible.

Verdict:
1. Pages 1 to 10 are structurally clean (no overflowing tables, no cut-off text, no stranded headings, captions stay with their figures), but the sign-off page is blank by design and pages 2, 5, 8 and 9 have figures too small to read.
2. Highest priority: enlarge or crop the Cadence screenshots (Figures 1, 2, 4, 5) so that labels are legible, and fill the roughly 40% blank space on pages 8 and 9 below Figures 4 and 5.
3. Lower priority: add writing lines for BATCH NUMBER and faculty signature on page 1, unify the heading case on page 7, and tidy table wrapping on pages 5 and 10.
