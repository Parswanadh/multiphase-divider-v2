# build_layout_v2.il: layout notes (gpdk045 DLATCH and divider_core)

Status: first version, UNTESTED. Written without Virtuoso or Assura. Nothing here has been run.
Tags: [V] = read from a PDK file; [VERIFY] = SKILL API or behaviour not confirmed.
PDK root used for citations: `/home/parshu/vm/pdk/gpdk045_v_6_0` (VM path: `/home/buet/pdk/gpdk045_v_6_0`).

## 1. What the script does and does not do

| Item | State |
|---|---|
| Probe the layout API units (`divProbeScale`) | Done. Prints the mode it chose |
| Print CDF names, types, defaults of nmos1v and resnsnpoly (`divPrintCdf`) | Done (first-run check) |
| Place M1 M5 M7 M6 M2 in row A, M3 M4 in row B (from the real top of row A) | Done, [VERIFY] param types |
| Place R1, R2 (resnsnpoly), R2 stacked from the real bBox of R1 | Done, [VERIFY] pcell params |
| Pins CK CKb NBIAS VSS D Db Q Qb VDD (metal1 pin + label) | Done. Pins only, not connected to devices |
| Terminal figures printed per device in global um (`divDumpInst`) | Done, uses master terminals and dbTransformBBox [VERIFY] |
| Intra-latch metal routing (gates, S/D, body, VDD/VSS) | NOT drawn. Route from the printed boxes in the next pass |
| Via and contact instances | NOT drawn. Use the viadefs in section 4 |
| divider_core: 4 DLATCH instances in a 2x2 (R0, MY, MX, R180) | Done, [VERIFY] `dbCreateInst` signature |
| Net labels at all instance pins | Done |
| Clock trunks (CK, CKb metal2) | NOT drawn. Only the equal-length check is printed |
| DRC | Not run. `runDRC()` prints the GUI steps |

Expect the first DRC run to show missing-contact, implant/tap, and pin-spacing errors. Those are the next work item.

## 2. Parameters found (pcell names, types, options)

### nmos1v layout pcell [V]
- Layout PCell params (`gpdk045/nmos1v/layout/layout.oa`, `prog((_pcParameters ...)`):
  `fw l fingers connectGates connectSD switchSD diffCont dfm mtlCvg sdMtlWidth leftAbut rightAbut tap topTap bottomTap leftTap rightTap tapExtension tapCntRows`.
- CDF (`gpdk045/nmos1v/data.dm`): `w` total width (default 120n), `fw` finger width (default 120n), `fingers` (type "string", default 1), `l` (default 45n), `m`, `model` (default g45n1svt).
- Cyclic choices (CDF text): `connectGates` = None / Top / Bottom / Both (default None). `connectSD` = None / Source / Drain / Both. `tap` = None / Integrated / Detached (default None). `dfm` = Minimum / DFM.
- Used in the script: `fw="120n"`, `l`, `fingers`, `connectGates="Top"`, `tap="Integrated"`. Cyclic-choice params are passed as "string" (the script's fallback set drops them).
- Param types tried in order: `fingers` as "string", then "int", then a minimal set with only fw / l / fingers.
- UNKNOWN: whether `connectGates="Top"` and `tap="Integrated"` give the connections you want. Check after the first run.

### Poly resistor layout pcell (resnsnpoly) [V]
- Layout params (`gpdk045/resnsnpoly/layout/layout.oa`): `segW segL connection segments leftDummy rightDummy cntOnDummy cntRows topTap bottomTap leftTap rightTap tapExtension`.
- CDF names (`resnsnpoly/data.dm`): `model r rsh rend rcont segW segL segments connection`.
- Used: `segW="0.8u"`, `segL="7.855u"`, `segments` (int 1, then string, then omitted). `connection` left at default (values UNKNOWN).

### Via / contact pcells [V]
- The only via-type pcell directory is `gpdk045/M2_M1_LV` (layout dir only, no data.dm). Its params are UNKNOWN, so the script does not use it.
- Use the techfile viadefs instead (section 4). The script does not call them yet.

## 3. Resistor choice and sizing (deviation from the task)

The task named `ressnpoly` or `ressppoly`. Those are salicided, with sheet resistance 15 ohm/sq at tt (`gpdk045_resistor.scs` tt_res block, `r_ressnpoly = 15`). A 2 kOhm resistor would then need about 133 squares, about 107 um of 0.8 um poly. That is not practical in a 2x2 cell.

`resnsnpoly` (N+ poly, no salicide) is the practical choice:
- Sheet resistance: `r_resnsnpoly = 200` ohm/sq at tt (`gpdk045_resistor.scs` line 75, tt_res block).
- End resistance: `r_rend_resnsnpoly = 1.44e-5` (line 76). The model divides it by W per end: 18 ohm per end at W = 0.8 um, 36 ohm for two ends.
- dl and dw are 0 at tt (same block), so no width or length correction.
- Length: L = (R - 2*rend0/W) * W / rsh = (2000 - 36) * 0.8 / 200 = 7.856 um, snapped to 7.855 um. Expected R = 200 * 7.855 / 0.8 + 36 = 1999.75 ohm.
- Width 0.8 um is the POLYR.W.1.2 suggested minimum (`assuraDRC.rul` line 108).
- Caveat: the non-salicide poly needs the salicide-block layer in the real layout. The pcell is expected to add it. Verify this in the DRC run. POLYR.E.1 (salicide block enclosure, line 3639, 0.14 um) applies to the salicided version.

Resistor sizing is in `divResLenUm()` and the `defvar`s at the top of the .il file. Change `divResCell` back to `ressnpoly` to use the salicided cell, but then the length is about 107 um.

## 4. Layers, vias and DRC rules used

### Layers [V] (`gpdk045/gpdk045.layermap`)
Oxide (1/0, active), Poly (3/0), Nimp (4/0), Pimp (5/0), Cont (6/0), Metal1 (7/0, pin 7/1, label 7/3), Via1 (8/0), Metal2 (9/0), SiProt (72/0). The script uses layer names, not stream numbers.

### Via/contact definitions [V] (`gpdk045/tech_gpdk045.tf`, `viaDefs(standardViaDefs(...))`, lines 1662-1740)
- `M1_PO`: Poly to Metal1 via `Cont` 0.06x0.06. Enclosure: poly 0.02 / 0.03 (x/y), metal1 0.0 / 0.03.
- `M1_DIFF`: Oxide to Metal1 via `Cont` 0.06x0.06. Enclosure: oxide 0.03 / 0.03, metal1 0.0 / 0.03.
- `M1_PSUB`: as M1_DIFF, plus Pimp 0.01 and PWdummy 0.01. Body tie to psub.
- `M1_NIMP` / `M1_PIMP`: as M1_DIFF, plus Nimp or Pimp 0.07.
- `M2_M1`: Metal1 to Metal2 via `Via1` 0.07x0.07. Enclosure 0.005 / 0.03.
- Use `techFindViaDefByName(tf "M1_PO")` (or `M1_DIFF`, `M2_M1`) with `dbCreateVia`. [VERIFY] signature.

### DRC rule lines [V] (`assura/assuraDRC.rul`, errorLayer messages)
| Rule | Value | Line |
|---|---|---|
| OXIDE.W.1 | Active width >= 0.05 | 3289 |
| OXIDE.W.2.1.1 | 1.1V NMOS gate width >= 0.12 | 3295 |
| OXIDE.SP.1 | N+ active to N+ active >= 0.08 | 3320 |
| OXIDE.A.1 | Active area >= 0.035 | 3341 |
| OXIDE.X.1 | Oxide must be covered by Nimp or Nzvt or Salicide Block | 3356 |
| POLY.W.1 | 1.1V NMOS gate length >= 0.045 | 3531 |
| POLY.SP.2 | Gate space >= 0.06 | 3557 |
| POLY.SP.3 | Interconnect space >= 0.06 | 3560 |
| POLY.SP.1 | Poly resistor space >= 0.3 | 3554 |
| POLY.E.1 | NMOS gate extension beyond active >= 0.1 | 3570 |
| POLY.A.1 | Poly interconnect area >= 0.02 | 3629 |
| POLYR.W.1.1 | Poly resistor width >= 0.1 | 45 |
| POLYR.W.1.2 | Suggested poly resistor width >= 0.8 | 108 |
| POLYR.X.1 | Poly resistor needs N+ or P+ implant | 3681 |
| NIMP.SP.1 | N+ implant space >= 0.12 | 3687 |
| NIMP.E.1 | N+ implant to active enclosure >= 0.07 | 3692 |
| NIMP.E.3 | N+ implant to gate side enclosure >= 0.1 | 3718 |
| CONT.W.1 | Contact width/length = 0.06 | 3840 |
| CONT.SP.1 | Contact to contact space >= 0.06 | 3843 |
| CONT.E.1 | Active to contact enclosure >= 0.03 | 3889 |
| CONT.E.2 | Poly to contact enclosure >= 0.02 | 3896 |
| CONT.X.3 | Contact must be covered by oxide or poly | 3932 |
| METAL1.W.1 | Metal1 width >= 0.06 | 4095 |
| METAL1.E.2 | Metal1 enclosure of contact >= 0.03 (opposite sides) | 4092 |
| METAL1.SP.1.1 | Metal1 space >= 0.06 | 4188 |
| METAL1.SP.1.2 | Metal1 space >= 0.1 (wide metal) | 4228 |
| METAL1.A.1 | Metal1 area >= 0.02 | 4719 |
| METAL2.W.1 | Metal2 width >= 0.08 | 4098 |
| METAL2.SP.1.1 | Metal2 space >= 0.07 | 4191 |
| VIA1.W.1 | Via1 0.07x0.07 | 4837 |
| VIA1.SP.1 | Via1 space >= 0.07 | 4840 |
| VIA1.E.1 | Metal1 to Via1 enclosure >= 0.005 | 4897 |
| METAL1.W.2 | Metal1 width <= 6.0 um (pin max, passes at 0.2 um) | 4131 |

Line numbers are the line of the `errorLayer` message in `assuraDRC.rul`. Some messages wrap onto the next line; the first line is the one cited.

Not checked in this pass: the NMOS tap rule (the pcell `tap` option should handle it) and the Oxide-to-Nimp enclosure for hand-drawn oxide. Use the DRC report for these.

## 5. Grid and units

- Manufacturing grid 0.005 um [V] (`tech_gpdk045.tf` lines 157-159, `mfgGridResolution 0.005`).
- maskLayout: user unit micron, 2000 dbu per um [V] (`tech_gpdk045.tf` viewTypeUnits, maskLayout row, lines ~148-155).
- The SKILL layout API is expected to take user units (um), which is what the script assumes first. [VERIFY] at runtime: `divProbeScale` places one MOS at the origin, reads its raw bBox width and sets `divScale` to 1 (user units) or 2000 (dbu). The CIW prints `== units probe:` with the chosen mode. If the probe says dbu, every coordinate is scaled by 2000 and rectangles are the intended size.
- All coordinates are snapped to the 0.005 um grid by `divSnapUm`. Use the values printed by `divPrintCdf`/`divDumpInst` to double-check placement.

## 6. Pins

- Metal1 pin 0.20 x 0.15 um, area 0.03 um^2, above METAL1.A.1 (0.02).
- Pin labels on `Metal1 label` purpose. Pin shapes on `Metal1 pin`.
- The pin API calls are [VERIFY]: `dbCreateNet`, `dbCreateTerm(net name dir)`, `dbCreatePin(net fig)`. Each is wrapped in `errset` and prints `VERIFY` on failure.

## 7. Symmetry and clock routing (plan, partly done)

- Row A order M1 M5 M7 M6 M2 puts M7 between the clock devices M5 and M6 (paper rule). The row is not yet centred on M7 because widths are placed left to right. The next pass should centre M7 and mirror M1/M2 and M5/M6.
- Top level: XD1 R0 at (0,0), XD2 MY, XD3 MX, XD4 R180, gap 1.0 um. Latches 2 and 3 have CK and CKb swapped in the net labels (from the netlist).
- Clock length check: the star model sums Manhattan distance from each ck and ckb pin to the array centre. Equal sums mean equal wire lengths by construction. The check is printed; it is not the routed length.
- Clock trunks (metal2) and their vias are NOT drawn. Proposed approach for the next pass: metal1 stubs from each CK/CKb pin to a metal2 trunk, with a via1 at each trunk. Keep the two trunks at separate y values and keep stubs of the other net out of the trunk span.

## 8. Known risks and open items

1. Pcell param types (string, int, cyclic). The script passes "string" and falls back to "int" for fingers and to a minimal set. Check the `FAILED` lines.
2. `dbCreateInst` argument order (cv master name origin orient numInst) [VERIFY].
3. `dbOpenCellViewByType(lib cell view viewType "w")` creates the view in "w" mode [VERIFY].
4. Terminal names on nmos1v and resnsnpoly layout pcells are UNKNOWN. The `divDumpInst` output will show them.
5. Intra-latch routing and vias are not drawn. DRC will flag incomplete contacts and possibly pin spacing. Expected.
6. `runDRC()` is GUI steps only. The Assura entry point is not verified (`assuraRunDRC` is not used).
7. `run_drc.rsf` keywords are from memory of the Assura run-file format. VERIFY.
8. `divider_core` needs the pin table from `buildLayoutDLATCH()` in the same CIW session. A reload clears it.

## 9. Discrepancies with the repository

- The task asks for resistor "~2 kOhm". The netlist `spectre/divider_gpdk45.scs` (parameters line) uses `rl=8k`. This script follows the task (2 kOhm). Decide which is right before the Spectre run, or the layout and netlist will disagree.
- The task named `ressnpoly`/`ressppoly`. The script uses `resnsnpoly` (section 3).
- The task said create only two files. `run_drc.rsf` was also requested by name, so it was created. Delete it if it is not wanted.
- `cadence/skill/PDK_FACTS.md` section 0 says the NMOS is a 1.1 V device, while the netlist comment says 1.0 V. The layout is not affected.
- `spectre/divider_gpdk45.scs` line 11 include path is `/home/buet/pdk/...`. PDK_FACTS.md already flags this. Not changed here.

## 10. How to run

1. Create `divider_lib` if missing, attached to gpdk045 tech.
2. CIW: `load("/abs/path/cadence/skill/build_layout_v2.il")`
3. `buildLayoutDLATCH()`. Read the printf output. Send back: the `== units probe` line, the CDF dump lines, any `FAILED` or `VERIFY` lines, and the terminal lines (`divDumpInst`).
4. `buildDividerCore()` (same CIW session, so the pin table is set).
5. `runDRC()` for the GUI steps. Send back the DRC error list.
