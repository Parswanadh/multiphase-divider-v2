# REVIEW3 visual QA, pages 11-20 of 29

Scope: read-only visual inspection of rendered PNGs p-11 to p-20. Every page has a heavy black rectangular frame inset from the page edge and a "Page N of 29" footer. This is consistent across all ten pages (low; confirm whether it is an intended page border).

| page | defect | severity |
|---|---|---|
| 11 | ok. Tables 4 and 5 are centred, columns evenly sized, FAIL cells red and legible, bottom blank area small. | - |
| 12 | Figure 6 (PVT pass/fail heatmap) occupies only the top ~45% of the page; the remaining ~55% below the caption (y ~ 330 to 720) is empty. Cell values (e.g. "24.6 ps") and axis tick labels are about 4 pt and barely legible; the sub-legend line ("Green: pass, cell text is propagation delay...") is unreadable. | high (blank area); medium (figure text) |
| 13 | "SCREENSHOT OF THE LAYOUT:" Figure 7 is a Virtuoso layout-editor screenshot. Menus, toolbar, layer panel, status bar and window title are unreadable at report size; only the "DLATCH" labels and the red/green routing outlines are discernible. Figure is also small (about half the text width). | high |
| 13 | Heading "SCREENSHOT OF THE OUTPUT WAVEFORM OBTAINED FROM THE SIMULATOR FOR THE LAYOUT:" is followed by no figure, only a paragraph saying the layout was not simulated. The heading promises an image that is not present. | medium |
| 14 | ok. Dense justified text, consistent body size, no overflow or stranded heading. | - |
| 15 | Figure 8 (ring interconnection schematic of XD1-XD4) is about 45% of the text width. Box labels (cell parameters), pin names and the italic note under the diagram are unreadable; only "XD1" to "XD4" and the legend colours are readable. | high |
| 15 | Bottom ~15% of page empty after Figure 8 caption. Within tolerance. | low |
| 16 | Figure 9 (transient, unsized, 1.4 GHz) sits at the top of the page; caption ends at y ~ 335, leaving roughly 55% of the page (y ~ 340 to 720) blank. | high |
| 16 | Figure 9 title line (two lines at the top of the image) and the axis tick labels and "CK / Q1 / QB1" y-labels are very small (about 4 pt); annotations such as "steady swing 15.3 mV" are barely legible. | medium |
| 17 | Figure 10 (nine stacked transient panels, design B) is legible only at the trace level. The per-panel "phase xx.xx deg" annotations, the y-axis tick labels (0.94 / 0.96) and the top title line are about 3-4 pt and effectively unreadable. Panels are tightly packed with no space between them. | medium |
| 18 | Figure 11 (grouped bar chart of adjacent phase steps): bar value labels (e.g. "71.4", "83.5") and the three-line legend under the axes are very small. The dashed "ideal 45 deg" line runs through the bar labels. | medium |
| 18 | Figure 12 (tail node V(XD1.tail), unsized): axes and caption are legible; the top sub-title and the legend text are small. | low |
| 19 | Figure 13 and Figure 14 are both full-width and legible at trace level. In Figure 14 the last x-axis tick label "11.0" appears clipped at the right edge of the plot area (reads as "11.(" ). Figure sub-titles and legend text are small. | low |
| 20 | Figure 15 (three stacked supply-current panels): the panels occupy about 40% of the text width; the panel sub-titles, y-axis scale annotations and the mean/peak text in each panel are illegible. | medium |
| 20 | Figure 16 (two side-by-side sweeps): plot area is adequate, but legend and tick labels are about 4 pt, Red "x" markers are clear. Blank area below caption ~27% of page, within tolerance. | medium |

Cadence screenshots on pages 11-20: only Figure 7 (Virtuoso layout editor, page 13) is a real tool screenshot. It is NOT legible at report size; the layout canvas content is discernible but all UI text is not. The output-waveform screenshot heading on page 13 has no image at all.

Verdict:
1. Two pages have large blank areas (p12 and p16, roughly 55% empty below the figure), and p13 has a heading promising a screenshot with no figure.
2. The Cadence layout screenshot (Figure 7, p13) and the ring schematic (Figure 8, p15) are not legible at report size; most multi-panel plots (p16, p17, p18, p20) use text too small to read.
3. Text pages (11, 14) are clean; the defects are concentrated in figure sizing, and the fix is to enlarge figures (or split multi-panel figures) and fill the blank space on p12 and p16.
