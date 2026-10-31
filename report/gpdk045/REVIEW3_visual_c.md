# Visual QA review C: pages 21-29

Read-only review of rendered pages p-21.png to p-29.png. Judgments on small text are made from the downscaled page renders (about 600 px wide for portrait, 770 px for landscape), so treat "illegible" calls as approximate.

| page | defect | severity |
|---|---|---|
| 21 | Figure 18 (PVT pass/fail heatmap): the legend line under the x-axis ("Green: pass, cell text is propagation delay; Red: FAIL ...") and the x-axis tick labels are very small. | low |
| 21 | Figure 17 (top of page): axis tick labels, the "x FAIL" annotations and the legend are small. Figure is readable but tight. | low |
| 21 | Bottom of page is blank below the Figure 18 caption (about 20-25 % of page). Within the limit. | ok (no defect) |
| 22 | Only the Figure 19 block (plot, legend, caption) occupies the top ~45 % of the page. The lower ~60 % is blank before the footer. | medium |
| 22 | Figure 19 legend and the red "x n FAIL" annotations under the Delay and Power plots are small. | low |
| 23 | Figure 20 (Virtuoso CIW log screenshot): the full window is scaled to roughly half the text width. The log text cannot be read at report size, so the figure conveys only that a log exists. | high |
| 23 | Lower ~40 % of page blank below the Figure 20 caption. | medium |
| 24 | Figure 21 (Virtuoso layout editor, DLATCH cell): the canvas is almost entirely black and the device shapes are small. The layer panel and menu text are unreadable, and the device labels are legible only for the "resmpoly" resistor labels. Dark and low-contrast at report size. | high |
| 24 | Figure 22 (Assura DRC terminal summary): text is legible. Some lines in the screenshot itself wrap mid-phrase ("Flat Error / Count : 1", "Real Error Count / : 14"). | low |
| 25 | Figure 23 (transient waveform stack): the title block at the top, the y-axis labels (CK, Q1, ...), the tick labels and the right-hand "phase" annotations are very small. Fonts are sans-serif, unlike the serif body text. | medium |
| 25 | "CONCLUSION:" body paragraph runs to the bottom margin and continues on p-26 mid-sentence. Acceptable, not a stranded heading. | ok (no defect) |
| 26 | Text-only page. Headings, body and margins are consistent with neighbouring pages; no overflow or clipping seen. | ok |
| 27 | Text ends about 45 % of the way down the page; the lower ~55 % is blank before the landscape appendix starts on a new page. Likely an intentional section break, but it still reads as a large empty area. | medium |
| 28 | Appendix Table 6 (landscape): fits within the page width, the header row is shaded and the table body is legible at about 7-8 pt. The Note column wraps cleanly. | ok |
| 28 | Table 6 header is repeated correctly on the continuation page. | ok |
| 29 | In the Note column, "divides, swing 0.093 V < 0.1 V" wraps so that a lone "V" sits on the second line. Cosmetic. | low |
| 29 | Table 6 continuation ends about two-thirds down the page. Last page, so blank space is allowed. | ok |

Cadence screenshots at report size:
- Figure 20 (p-23, CIW log): not legible.
- Figure 21 (p-24, Virtuoso layout, DLATCH): not legible for device or layer detail; dark canvas.
- Figure 22 (p-24, Assura DRC summary): legible.

Verdict:
1. Pages 21-29 have no clipped, overlapping or stranded elements, and the landscape appendix Table 6 fits its page with a repeated header.
2. The main problems are the Cadence screenshots on p-23 (Figure 20) and p-24 (Figure 21), which are unreadable at report size, plus large blank areas on p-22, p-23 and p-27.
3. Smaller issues are the tiny text in the Figure 17-19 and Figure 23 plots, a lone "V" wrap on p-29, and sans-serif figure fonts against the serif body text.
