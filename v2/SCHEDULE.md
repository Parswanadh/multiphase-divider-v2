# v2 Schedule (SCHEDULE.md)

## Work Breakdown Structure

| ID | Task | Depends | Lane |
|---|---|---|---|
| W1 | Decisions D1-D6 signed | None | Host |
| W2 | Secret rotation + history cleanup (backlog k) | None | Host/human |
| W3 | Rerun nominal D/B/U8k + freeze scripts | W1 | VM |
| W4 | Verify Monte Carlo model sections in PDK | W1 | VM/host |
| W5 | E1 sweep (m/R/vb) + fmax map | W3 | VM |
| W6 | E6 vb-trim add-on | W5 | VM |
| W7 | Analysis plots + tables from sweep TSVs | W5,W6 | Host |
| W8 | Route DLATCH m=4 R=3k, DRC/LVS passes | W1 | VM |
| W9 | Pursue qrc/extraction files | W1 | Host/human |
| W10 | Manuscript rewrite to outline | W7,W8 | Host |
| W11 | Numbers audit + prose audit + visual review | W10 | Host |
| W12 | Venue package + human push decision | W11 | Human |

## Dependencies and Critical Path

Critical path: W1 -> W3 -> W5 -> W7 -> W10 -> W11 -> W12.
Layout (W8) and extraction pursuit (W9) run off critical path. W2 is independent, do first.
VM lane is serial (W3, W5, W6, W8 queue under flock); host lane (W4, W7, W10, W11) runs parallel.

## Effort Estimates (hours, uncertainty in parentheses)

| Task | Effort |
|---|---|
| W1 decisions | 1 (+1) |
| W2 secret cleanup | 1 (+2) |
| W3 re-baseline | 4 (+4) |
| W4 MC model check | 1 (+1) |
| W5 E1 sweep | 12 (+12) |
| W6 vb trim | 4 (+4) |
| W7 analysis | 6 (+4) |
| W8 layout route | 16 (+16) |
| W9 extraction pursuit | 2 (+6) |
| W10 manuscript | 8 (+6) |
| W11 audits | 4 (+4) |
| W12 package | 2 (+2) |
| Total | 61 (+62) |

VM share is about half; calendar time dominated by VM serial time and disk/tool faults.

## Milestones and Exit Gates

| Milestone | Gate |
|---|---|
| M1 Decisions (day 2) | DECISIONS.log signed |
| M2 Re-baseline (end week 1) | Nominal reruns match v1 within script tolerance |
| M3 Enhancement data (end week 2) | Sweep table + recommended sizing frozen |
| M4 Layout snapshot (end week 3) | New DRC/LVS logs committed |
| M5 Draft (week 3-4) | Zero unsupported claims per CLAIMS_AUDIT |
| M6 Submit-ready (week 4) | Human approves venue package |

## Weekly Calendar (4-week variant; compress to 2 by dropping W6, W8 polish, TechRxiv variant)

Week 1: W1, W2, W3, W4, start W5 and W8 and W9.
Week 2: finish W5, W6; W7; W8 continues.
Week 3: W8 snapshot; W10 draft; W11 audits begin.
Week 4: W11 finish; W12 package; human push decision.
