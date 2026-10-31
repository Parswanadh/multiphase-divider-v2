# PDK_FACTS: gpdk045 v6.0 facts for cadence/skill/build_divider.il

PDK root: `/home/parshu/vm/pdk/gpdk045_v_6_0` (called `$PDK` below).
Method: read-only inspection of text files, `strings`/`grep -a` on OpenAccess binaries,
and the CDF text inside each cell's cell-level `data.dm`. No Cadence tool was run and the VM was not touched.

Status key: **VERIFIED** = found in a PDK file (cited). **UNKNOWN** = not determinable from the PDK.
**ASSUMED** = reasoning, not a file fact.

---

## 0. Important findings up front

1. The PDK calls the thin-oxide NMOS a **1.1 V** device, not 1.0 V. Sources: `$PDK/models/spectre/gpdk045_mos.scs` header lines 14, 23, 32, 42 ("1.1V Standard-Vt devices"); `$PDK/models/spectre/gpdk045_soa.scs` line 21 (`max_vdd_1v=1.1`). The 1.0 V value in the Spectre deck is still inside that limit.
2. The PDK has **no** cells named `rppoly`, `rppolyl`, `rpposab` or any `rp*` resistor (grep of the whole PDK returned nothing). Poly resistors are `ressnpoly`, `ressppoly`, `resnsnpoly`, `resnsppoly` (and `_2` variants).
3. The PDK has **no** `res`, `cap`, `vdc`, `vpulse`, `gnd`, `ipin`, `opin`, `iopin` cells. Those come from the Cadence tool libraries `analogLib` and `basic`, which the PDK's `cds.lib` only references in commented-out lines (see section 5).
4. **Bin check, W=240n L=45n (M1..M6): inside bin 30 of the nch model. Valid in tt/ff/ss/fs/sf.** Details in section 4.
5. **Bin check, W=480n L=90n (M7 tail): inside bin 23.** Also valid. Details in section 4.
6. `spectre/divider_gpdk45.scs` line 11 includes `/home/buet/pdk/gpdk045_v_6_0/models/spectre/gpdk045.scs`. That path does not exist on this machine (the PDK is under `/home/parshu/vm/pdk/`). Fix the include path before running Spectre. This is outside build_divider.il and was not edited.

---

## 1. Cell names, views, and CDF parameters

### 1a. MOS (1.1 V thin-oxide NMOS and PMOS)

| Item | Value | Status | Source |
|---|---|---|---|
| Library name | `gpdk045` | VERIFIED | `$PDK/cds.lib` line 6: `DEFINE gpdk045 ./gpdk045` |
| Library dir | `$PDK/gpdk045/` | VERIFIED | directory listing |
| 1.1 V thin-oxide NMOS cell | `nmos1v` | VERIFIED | dir `$PDK/gpdk045/nmos1v/`; `$PDK/gpdk045/mos.Cat` line 2; `$PDK/gpdk045/gpdk045_PDKRegistrations.il` line 8 |
| 1.1 V thin-oxide PMOS cell | `pmos1v` | VERIFIED | dir `$PDK/gpdk045/pmos1v/`; `mos.Cat` line 14; `PDKRegistrations.il` (`pfet` list) |
| Other NMOS/PMOS cells (not used) | `nmos1v_3`, `nmos1v_hvt`, `nmos1v_hvt_3`, `nmos1v_lvt`, `nmos1v_lvt_3`, `nmos1v_nat`, `nmos1v_nat_3`, `nmos2v`, `nmos2v_3`, `nmos2v_nat`, `nmos2v_nat_3`; PMOS: `pmos1v_3`, `pmos1v_hvt`, `pmos1v_hvt_3`, `pmos1v_lvt`, `pmos1v_lvt_3`, `pmos2v`, `pmos2v_3` | VERIFIED | `mos.Cat`; `PDKRegistrations.il` |
| `nmos1v` / `pmos1v` view dirs | `symbol`, `spectre`, `auCdl`, `auLvs`, `hspiceD`, `ivpcell`, `layout` | VERIFIED | directory listing of `$PDK/gpdk045/nmos1v/` |
| `nmos1v` has NO `schematic` view | - | VERIFIED | directory listing |
| Symbol view name | `symbol` | VERIFIED | `$PDK/gpdk045/nmos1v/symbol/symbol.oa` (OA binary, present) |
| Terminals | `D`, `G`, `S`, `B` | VERIFIED | `strings` on `nmos1v/symbol/symbol.oa`: `cdsTerm("D")`, `cdsTerm("G")`, `cdsTerm("S")`, `cdsTerm("B")`; `nmos1v/data.dm` CDF `termOrder (D G S B)` |
| Terminal of `nmos1v_3` (3-terminal) | `D G S bulkn` | VERIFIED | `nmos1v_3/data.dm` (not used) |
| Terminal mapping (ext. extraction) | G on poly, S/D on ndiff, B on psubstrate | VERIFIED | `$PDK/diva/divaEXT.rul` lines 902-903 (`extractDevice ... (poly_conn "G") (ndiff_conn "S" "D") (psubstrate "B") "nmos1v ivpcell"`) |
| Spectre netlist model for `nmos1v` | subckt `g45n1svt` (default of CDF `model`) | VERIFIED | `nmos1v/data.dm` CDF: `defValue "g45n1svt" ... name "model"`; `simInfo spectre ... otherParameters (model) termOrder (D G S B) termMapping (D :d G :g S :s B :b)` |
| PMOS model subckt | `g45p1svt` | VERIFIED | `pmos1v/data.dm` CDF `model` default `g45p1svt`; `gpdk045_mos.scs` line 4532 |
| Mapping of nmos1v CDF to Spectre instance params | `w`->`simW`, `nf` (from CDF `fingers`), `m`->`simM` | VERIFIED | `nmos1v/data.dm` `propMapping (nil m simM w simW nf fingers trise dtemp)` |
| Spectre instance parameter list | `w l nf as ad ps pd nrd nrs sa sb sd sca scb scc m trise region degradation geo isnoisy` | VERIFIED | `nmos1v/data.dm` `instParameters` |
| CDF name, MOS total width | `w` (prompt "Total Width", default `120n`) | VERIFIED | `nmos1v/data.dm`: `name "w" ... defValue "120n"` |
| CDF name, MOS length | `l` (prompt "Length", default `45n`) | VERIFIED | `nmos1v/data.dm`: `name "l" ... defValue "45n"` |
| CDF name, finger width | `fw` (prompt "Finger Width", default `120n`) | VERIFIED | `nmos1v/data.dm` |
| CDF name, finger count | `fingers` (default `1`; Spectre name `nf`) | VERIFIED | `nmos1v/data.dm` `name "fingers"`; `PDKRegistrations.il` `ciMapParam("fingerCount" ... '("fingers"))` |
| CDF name, multiplier | `m` (default `1`) | VERIFIED | `nmos1v/data.dm`; `PDKRegistrations.il` `ciMapParam("mFactor" ... '("m"))` |
| CDF name, model | `model` (default `g45n1svt`) | VERIFIED | `nmos1v/data.dm` |
| Full CDF name list (nmos1v) | `model m simM l fw w simW fingers AreaFormula threshold diffCont connectGates dfm sdMtlWidth connectSD switchSD mtlCvg leftAbut rightAbut tap leftTap rightTap bottomTap topTap tapExtension tapCntRows showSimParams editAreaPerim ad as pd ps nrd nrs sa ls sb Vds sd Vbs sca Vgs scb scc geo ld dtemp region degradation isnoisy off` | VERIFIED | `nmos1v/data.dm` (names extracted by regex) |
| Layout PCell params | `fw l fingers connectGates connectSD switchSD diffCont dfm mtlCvg sdMtlWidth leftAbut rightAbut tap topTap bottomTap leftTap rightTap tapExtension tapCntRows` | VERIFIED | `strings` on `nmos1v/layout/layout.oa` (`prog((_pcParameters fw l fingers ...`) |
| ADE CIW check for CDF names | `cdfGetInstCDF(inst)~>parameters` | UNKNOWN (SKILL API not in PDK) | - |

Note on the `.il` CDF field: `divSetParam` sets `prm->value` directly and runs no CDF callbacks (see the .il comment). The PDK CDF has `callback "gpdk045_mosCB( 'w )"` and `callback "gpdk045_mosCB( 'l )"`, so `w` and `l` may recompute `fw`/`fingers`. Set `fingers=1` and `fw=w` as well, or set `w` through the form so the callback runs. (ASSUMED: the callback behavior is inferred from the CDF text, not read from the callback source.)

### 1b. Resistors

Every `res*` cell in the PDK (from `$PDK/gpdk045/resistors.Cat`, `prim` list in `primitives.Cat`, and `PDKRegistrations.il` `resistor` list):

| Cell | What it is (from `models/spectre/gpdk045_resistor.scs` header comment, lines 16-54, and the cell CDF) | Terminals (CDF termOrder) | Spectre component | Status |
|---|---|---|---|---|
| `ressnpoly` | N+ poly resistor, salicided | PLUS MINUS B | `g45rsnp` | VERIFIED |
| `ressppoly` | P+ poly resistor, salicided | PLUS MINUS B | `g45rspp` | VERIFIED |
| `resnsnpoly` | N+ poly resistor, no salicide | PLUS MINUS B | `g45rnsnp` | VERIFIED |
| `resnsppoly` | P+ poly resistor, no salicide | PLUS MINUS B | `g45rnspp` (CDF componentName missing; modelName = g45rnspp) | VERIFIED |
| `ressnpoly_2`, `ressppoly_2`, `resnsnpoly_2`, `resnsppoly_2` | Same poly types, 2-terminal variant (no B terminal; CDF has `SUB` and `bulkn`) | PLUS MINUS | `g45rsnp` / `g45rspp` / `g45rnsnp` / `g45rnspp` | VERIFIED for terminals/component; meaning of "_2" suffix: UNKNOWN (not documented in PDK) |
| `ressndiff`, `resspdiff`, `resnsndiff`, `resnspdiff` (+ `_2`) | N+/P+ diffusion resistors (salicided / not) | PLUS MINUS B (+ `_2`: PLUS MINUS) | `g45rsnd`, `g45rspd`, `g45rnsnd`, `g45rnspd` | VERIFIED |
| `resnwsti`, `resnwoxide` (+ `_2`) | N-well resistor under STI / under oxide | PLUS MINUS B | `g45rnws`, `g45rnwo` | VERIFIED |
| `resm1` ... `resm11` | Metal 1 ... Metal 11 resistor | PLUS MINUS | `g45rm1` ... `g45rm11` | VERIFIED |
| `primRes2` | primitive 2-terminal resistor | PLUS MINUS | `pPar` model | VERIFIED (symbol) |
| `primRes3`, `primRes3_inh_n`, `primRes3_inh_p` | primitive 3-terminal resistors | PLUS MINUS B / bulkn / bulkp | - | VERIFIED (symbol) |

Resistor CDF parameter names: `model`, `r` (resistance), `l`, `w`, `effW`, `effL`, `segR`, `segW`, `segL`, `rsh`, `dw`, `dl`, `tc1`, `tc2` (from `ressnpoly/data.dm`, `resm1/data.dm`). VERIFIED.

Resistor symbol-internal strings: `res2` / `res3` appear in `resm1/symbol/symbol.oa` and `ressnpoly/symbol/symbol.oa`. These look like glyph/cell-type names, not confirmed masters. Treat as UNKNOWN.

Analog `res` (analogLib) does NOT exist in the PDK. Its CDF name `r` and terminals `PLUS`/`MINUS` are UNKNOWN from the PDK. (`PDKRegistrations.il` `ciMapParam("resValue" ... '("r"))` shows the PDK maps the generic resistance param to `r`.)

### 1c. Capacitors

| Cell | Terminals | CDF params | Spectre component | Status |
|---|---|---|---|---|
| `mimcap` | PLUS MINUS B | `model c w l m area perim ...` (`calcParam c w l m`) | `g45cmim` (`gpdk045_mimcap.scs` line 89: `inline subckt g45cmim (n1 n2 body)`) | VERIFIED |
| `nmoscap1v`, `pmoscap1v` | D G S B | `model m c l fw w fingers ...` | `g45ncap1` / `g45pcap1` | VERIFIED |
| `nmoscap2v`, `pmoscap2v` | D G S B | `model m c l fw w ...` | `g45ncap2` / `g45pcap2` | VERIFIED |

Note: `c` is the capacitance CDF name. The PDK maps the generic capacitance param to `c` (`PDKRegistrations.il` `ciMapParam("capValue" ... '("c"))`). Analog `cap` (analogLib) is UNKNOWN from the PDK.

Only `mimcap` is registered as a "capacitor" device (`PDKRegistrations.il`: `ciRegisterDevice("capacitor" ... '("gpdk045" "mimcap" nil))`).

### 1d. Other cells used or relevant

| Cell | Notes | Status |
|---|---|---|
| `ind_a`, `ind_s` | inductors (terminals PLUS MINUS B) | VERIFIED |
| `npn2`/`npn5`/`npn10`, `vpnp2`/`vpnp5`/`vpnp10` | BJTs (terminals C B E S) | VERIFIED |
| `ndio*`, `pdio*` | diodes (terminals PLUS MINUS) | VERIFIED |

### 1e. Views (summary)

- Views exist as directories of OpenAccess binaries (`symbol.oa`, `layout.oa`, ...). Files named `pdk.dat` are binary (`file` reports `data`); the CDF text is in each cell-level `data.dm`.
- `symbol` exists for every device cell checked. `schematic` exists for the `resm*` and `res*` cells, not for `nmos1v`/`pmos1v`/`mimcap`.
- Spectre-view symbol for `nmos1v` is `spectre/symbol.oa` (different bytes from `symbol/symbol.oa`, but the same terminal strings).

---

## 2. Spectre model (for the netlister)

### 2a. How `nmos1v` reaches the model subckt

- CDF `model` default = `g45n1svt` (`$PDK/gpdk045/nmos1v/data.dm`, VERIFIED).
- The Spectre `simInfo` block in the same file says the instance line is `<name> (D G S B) <model> w=... l=... nf=... m=...`, with `termOrder (D G S B)` and `termMapping (nil D :d G :g S :s B :b)`. So the netlister writes `(d g s b) g45n1svt` (VERIFIED from CDF text; the emitted netlist was NOT produced here).
- UNKNOWN / RISK: the subckt `g45n1svt` declares parameters `l w multi nf factor` (not `m`). The netlister also emits `m=` (from `instParameters ... m ...`). Whether Spectre accepts `m=` on the subckt instance has not been tested. The bundled Spectre deck avoids this by passing only `w=` and `l=`.

### 2b. First ~12 lines of `subckt g45n1svt`

Source: `$PDK/models/spectre/gpdk045_mos.scs` lines 979-990 (VERIFIED, copied verbatim):

```
inline subckt g45n1svt ( d g s b )
parameters
+l=1e-6 w=1e-6 multi=1 nf=1 factor=1
+dmcg=4E-8
+xw=0+dxw_n
+ad=2*dmcg/factor*(w/nf+xw/factor)
+as=2*dmcg/factor*(w/nf+xw/factor)
+pd=4*dmcg/factor+2*(w/nf+xw/factor)
+ps=4*dmcg/factor+2*(w/nf+xw/factor)
+nrd=dmcg/factor/(w/nf+xw/factor)
+nrs=dmcg/factor/(w/nf+xw/factor)
+sa=6.1E-7/factor
```

The inner device line is at line 1006 of the file: `g45n1svt ( d n1 s b ) nch w=w l=l ad=ad as=as pd=pd ps=ps nrd=nrd nrs=nrs m=multi`. The model block `model nch bsim4 {` starts at line 1011. `ends g45n1svt` is at line 4528. The PMOS subckt `g45p1svt` starts at 4532, its `ends` at 7972.

### 2c. Corner sections in `models/spectre/gpdk045.scs` (VERIFIED)

`section tt` (line 9), `ff` (35), `ss` (61), `fs` (87), `sf` (113), `mc` (139). Each includes `gpdk045_mos.scs` `section=<corner>` and the other device files (diode, bipolar, mimcap, moscap, resistor, inductor, soa). The `_hvt`, `_lvt`, `_na`, `_18`, `_na18` and `_mos_var` variants are included inside each corner, not as top-level sections.

`divider_gpdk45.scs` line 11 uses `section=tt` (correct name), but the path is wrong (see section 0).

---

## 3. Supply voltage and DRC/SOA limits

| Item | Value | Status | Source |
|---|---|---|---|
| Device class of `nmos1v` | 1.1 V standard-Vt ("1v") | VERIFIED | `gpdk045_mos.scs` header lines 14, 23, 32, 42 |
| Nominal supply to use | 1.1 V (PDK rating). 1.0 V (used in Spectre deck) is below it | VERIFIED | same |
| Max gate voltage, 1 V devices | 1.1 V (soft limit) | VERIFIED | `gpdk045_soa.scs` line 21 `max_vdd_1v=1.1` |
| Max gate voltage, 2 V (1.8 V) devices | 1.8 V (hard limit) | VERIFIED | `gpdk045_soa.scs` line 22 `max_vdd_2v=1.8` |
| 1.8 V devices | `nmos2v` / `pmos2v` (model `g45n2svt` / `g45p2svt`) | VERIFIED | `nmos2v/data.dm` `modelName g45n2svt` |

The `.il` default `tbVdd 1.0` is consistent with `divider_gpdk45.scs` (`vdd=1.0`). It is inside the 1.1 V rating, so no value change is needed. Only the comment should say 1.1 V.

---

## 4. Bin check for `g45n1svt` (nch model, 30 bins)

Source: `$PDK/models/spectre/gpdk045_mos.scs`. Bin header lines and geometry lines are cited. The corner offsets come from the `section` blocks in the same file.

Bin limits, each as written in the file (`lmin`, `lmax`, `wmin`, `wmax`; `dxl_n`, `dxw_n`, `dlmis_n`, `dwmis_n` are corner/mismatch offsets):

| Bin | Line (header) | lmin | lmax | wmin | wmax |
|---|---|---|---|---|---|
| 6 | 1597 | 4E-8 | 6.0E-8-(dxl_n+dlmis_n) | 2.0E-6-(dxw_n+dwmis_n) | 1.1E-5-(dxw_n+dwmis_n) |
| 12 | 2298 | 4E-8 | 6.0E-8-(...) | 1.0E-6-(...) | 2.0E-6-(...) |
| 18 | 3001 | 4E-8 | 6.0E-8-(...) | 5.0E-7-(...) | 1.0E-6-(...) |
| 23 | 3587 | 6.0E-8-(dxl_n+dlmis_n) | 1.0E-7-(dxl_n+dlmis_n) | 3.0E-7-(dxw_n+dwmis_n) | 5.0E-7-(dxw_n+dwmis_n) |
| 24 | 3703 | 4E-8 | 6.0E-8-(...) | 3.0E-7-(...) | 5.0E-7-(...) |
| 30 | 4408 | 4E-8 | 6.0E-8-(dxl_n+dlmis_n) | 1.2E-7 | 3.0E-7-(dxw_n+dwmis_n) |

Other bins (1-5, 7-11, 13-17, 19-22, 25-29) were checked too. Bins 25-29 have `wmin=1.2E-7` but L ranges that exclude 45n. Bins 19-22 have wmin 3E-7 but L ranges that exclude 45n or 90n.

**W=240n, L=45n (M1..M6):**
- L=45n (4.5e-8) is in [4e-8, 6e-8): bins 6, 12, 18, 24, 30 have this L range.
- Among the bins whose L range contains 45n (6, 12, 18, 24, 30), W=2.4e-7 is in range only for bin 30 ([1.2e-7, 3.0e-7]). Bins 6, 12 and 18 need W >= 5e-7 or more; bin 24 needs W >= 3e-7.
- **Result: exactly one bin, bin 30, contains W=240n L=45n.**
- Corner check (offsets from the `section` blocks):
  - tt (line 190/189): dxl_n=0, dxw_n=0. lmax=6.0e-8, wmax=3.0e-7.
  - ff (line 210/211): dxl_n=-4.4e-9, dxw_n=+9e-9. lmax=6.44e-8, wmax=2.91e-7.
  - ss (line 230/231): dxl_n=+4.4e-9, dxw_n=-9e-9. lmax=5.56e-8, wmax=3.09e-7.
  - fs (line 250/251) and sf (line 270/271): dxl_n=0, dxw_n=0.
  - Mismatch terms dlmis_n, dwmis_n depend on rn1/rn2 (line 66: `rn1=0 rn2=0`, which is the nominal value). They are 0 in nominal runs.
- **Conclusion: W=240n L=45n is valid in bin 30 for tt, ff, ss, fs, sf. Verified.**

**W=480n, L=90n (M7 tail):**
- W=4.8e-7 is in [3.0e-7, 5.0e-7] for bins 19-24 only (bin 23 is the one with L range containing 9e-8).
- L=9e-8 is in [6.0e-8, 1.0e-7) for bin 23 (line 3587: lmin 6.0E-8, lmax 1.0E-7, wmin 3.0E-7, wmax 5.0E-7). Bin 22 has lmin 1.0E-7, so it is excluded.
- **Result: W=480n L=90n is inside bin 23 (tt nominal). Verified.**

Minimum sizes allowed by the model (VERIFIED): smallest L in any bin is 4E-8 (40 nm, bin 6/12/18/24/30). Smallest W is 1.2E-7 (bins 25-30). Largest W is 1.1E-5.

Note on `pmos1v` (`g45p1svt`): the same bin structure is used (`gpdk045_mos.scs` line 4565 onward), with `pch` bins starting at line 4565 and its own offsets (`dxl_p`, `dxw_p`). Not checked bin-by-bin.

---

## 5. Library and pin masters

| Item | Status | Source / reason |
|---|---|---|
| `analogLib` cells (`res`, `cap`, `vdc`, `vpulse`, `gnd`) and their terminals and CDF params | UNKNOWN | Not in the PDK. `$PDK/cds.lib` lines 2-4 have `#DEFINE analogLib ...` commented out, pointing to the Cadence tool install (`$(compute:THIS_TOOL_INST_ROOT)/tools/dfII//etc/cdslib/artist/analogLib`). That install is not in this PDK. |
| `basic` library (`ipin`, `opin`, `iopin`) | UNKNOWN | `cds.lib` line 3: `#DEFINE basic ...` commented out. The PDK has no pin-master cells. |
| `sheets` library | UNKNOWN | `cds.lib` line 4 (commented). Not used by the script. |
| `gpdk045` library | VERIFIED | `cds.lib` line 6 (`DEFINE gpdk045 ./gpdk045`) |
| Layer used for IO pins | `Metal1 drawing` | VERIFIED: `$PDK/gpdk045/libInitCustomExit.il` line 20: `envSetValIfDefault("layoutXL" "initIOPinLayer" 'string "Metal1 drawing")` |

Consequence: `divBasicLib "basic"` and the pin masters `ipin`/`opin`/`iopin` cannot be confirmed from the PDK. Confirm them in the Virtuoso CIW with `ddGetObj("basic")` and `ddGetObj("basic" "ipin")`. These are not verified here.

---

## 6. Layout facts (for reference; the script does not draw layout)

### 6a. Layers (`$PDK/gpdk045/gpdk045.layermap`, VERIFIED)

| Role | Layer (drawing purpose, stream layer/datatype) |
|---|---|
| N-well | `Nwell` drawing (2/0) |
| Active / diffusion | `Oxide` drawing (1/0). There is no `Active` or `Diff` layer name. `tech_gpdk045.tf` lines 22-26 map `ndiff_layer`, `pdiff_layer`, `active_layer` to `"Oxide"`. |
| Thick oxide | `Oxide_thk` (24/0) |
| Poly (gate and interconnect) | `Poly` drawing (3/0). `tech_gpdk045.tf` line 31: `ipoly_layer "Poly"` |
| N+ implant | `Nimp` (4/0) |
| P+ implant | `Pimp` (5/0) |
| Contact (poly/active to metal1) | `Cont` (6/0). `tech_gpdk045.tf` line 34: `contact_layer "Cont"` |
| Metal1 | `Metal1` drawing (7/0); pin purpose (7/1) |
| Via1 | `Via1` (8/0) |
| Metal2 | `Metal2` (9/0) |
| Via2 | `Via2` (10/0) |
| Metal3 | `Metal3` (11/0) |
| Via3 | `Via3` (30/0) |
| Metal4 | `Metal4` (31/0) |
| Metal5 ... Metal11 | `Metal5` (33), `Metal6` (35), `Metal7` (38), `Metal8` (40), `Metal9` (42), `Metal10` (152), `Metal11` (162) |
| Via4 ... Via10 | `Via4` (32), `Via5` (34), `Via6` (37), `Via7` (39), `Via8` (41), `Via9` (151), `Via10` (161) |
| Well-related dummy / marker layers | `Resdum`, `Capdum`, `INDdummy`, `prBoundary` (99/0), etc. | 

### 6b. Layout width/spacing numbers (from `$PDK/assura/assuraDRC.rul`, quoted)

Only the lines below were found. Spacings for Oxide-to-Oxide and Metal1 enclosure of contacts were not searched exhaustively.

| Rule | Value (quoted rule text) | Line |
|---|---|---|
| `POLY.W.1` | `Minimum 1.1V N-channel gate length >= 0.045 um` | 3531 |
| `POLY.W.2` | `Minimum 1.1V P-channel gate length >= 0.045 um` | 3535 |
| `POLY.W.5` | `Minimum Poly interconnect width >= 0.045 um` | 3550 |
| `POLY.SP.2` | `Minimum Poly gate space >= 0.06 um` | 3557 |
| `POLY.SP.3` | `Minimum Poly interconnect space >= 0.06 um` | 3560 |
| `POLY.E.1` | `Minimum N-channel gate extension beyond Active Area >= 0.1 um` | 3570 |
| `OXIDE.W.1` | `Minimum Active Area width >= 0.05 um` | 3289 |
| `OXIDE.W.2.1.1` | `Minimum 1.1V N-channel gate width >= 0.12 um` | 3295 |
| `OXIDE.W.2.2.1` | `Minimum 1.1V P-channel gate width >= 0.12 um` | 3306 |
| `OXIDE.A.1` | `Minimum area for Active Area >= 0.035 um` | 3341 |
| `CONT.W.1` | `Maximum and minimum Contact width/length == 0.06 um` | 3840 |
| `CONT.SP.1` | `Minimum Contact to Contact spacing >= 0.06 um` | 3843 |
| `CONT.E.1` | `Minimum Active Area to Contact enclosure >= 0.03 um` | 3889 |
| `CONT.E.2` | `Minimum Poly to Contact enclosure >= 0.02 um` | 3896 |
| `NIMP.W.1` | `Minimum N+ Implant width >= 0.12 um` | 3684 |
| `PIMP.W.1` | `Minimum P+ Implant width >= 0.12 um` | 3765 |
| `METAL1.W.1` | `Metal1 width must be >= 0.06 um` | 4095 |
| `METAL1.SP.1.1` | `Metal1 to Metal1 spacing must be >= 0.06 um` | 4188 |
| `METAL1.SP.1.2` | `Metal1 to Metal1 spacing must be >= 0.1 um` | 4228 |
| `VIA1.W.1` | `Via1 shapes must be 0.07x0.07 rectangles` | 4837 |
| `VIA1.E.1` | `Metal1 to Via1 enclosure must be >= 0.005 um` | 4897 |
| `POLYR.W.1.1` | `Minimum Poly resistor width >= 0.1 um` | 45 |
| `POLYR.W.1.2` | `Minimum suggested Poly resistor width >= 0.8 um` | 108 |
| `POLY.SP.1` | `Minimum Poly resistor space >= 0.3 um` | 3554 |

The DRC deck `pvs/pvlDRC.rul` and `diva/divaDRC.rul` were not compared with these numbers.

---

## 7. Documentation

- `$PDK/soce/README`: explains the Encounter capacitance tables (`gpdk045.basic.CapTbl`, `gpdk045.extended.CapTbl`). Not related to the schematic flow. VERIFIED.
- No other README exists in the PDK (`find . -iname "*readme*"` returns only `soce/README`). VERIFIED.
- `gpdk045_PDKRegistrations.il` header: "essentially for the use of the Circuit Prospector assistant". VERIFIED.
- `gpdk045_ModelMgmt.il` header: "@ 2008 Cadence", procedures `gpdk045_AppendModelFile` and `gpdk045_GetExpModelFileList` (no cell names). VERIFIED.

---

## 8. Files read (list)

- Text: `$PDK/cds.lib`, `$PDK/assura_tech.lib`, `$PDK/pvtech.lib`, `$PDK/gpdk045/gpdk045.layermap`, `$PDK/gpdk045/gpdk045_PDKRegistrations.il`, `$PDK/gpdk045/gpdk045_ModelMgmt.il`, `$PDK/gpdk045/libInit.il`, `$PDK/gpdk045/libInitCustomExit.il`, `$PDK/gpdk045/gpdk045_customFilter.il`, `$PDK/gpdk045/tech_gpdk045.tf` (lines 1-80), `$PDK/gpdk045/*.Cat`, `$PDK/models/spectre/*.scs` (all 9 files), `$PDK/assura/assuraDRC.rul`, `$PDK/assura/techRuleSets`, `$PDK/diva/divaEXT.rul` (lines 620-905), `$PDK/soce/README`.
- Binary, read with `strings`/`grep -a`/regex: `$PDK/gpdk045/<cell>/data.dm` (CDF text), `$PDK/gpdk045/nmos1v/{symbol,layout,ivpcell,spectre}/*.oa`.
- Binary, not readable as text: `$PDK/gpdk045/<cell>/pdk.dat` (`file` reports `data`), `tech.db`, `.cadence/dfII/cph/lam/cph.lam` (XML-like; not used).

---

## 9. Concrete edits to build_divider.il

Each row is one `VERIFY` line or tunable in `cadence/skill/build_divider.il` (grep: `grep -n VERIFY build_divider.il`). "Edit" means the change to make. "Keep" means the current value is correct and only the VERIFY note should be removed.

| Line | Current | Action | Corrected value / text | Source |
|---|---|---|---|---|
| 37 | `defvar(divLib "divider_lib")` | Keep | - | Not a PDK item (user-created library) |
| 38 | `defvar(divPdkLib "gpdk045")  ; VERIFY` | Keep, drop VERIFY | `"gpdk045"` | `$PDK/cds.lib` line 6 |
| 39 | `defvar(divNmosCell "nmos1v")  ; VERIFY: 1.0 V ...` | Keep value; fix comment | `"nmos1v"`. Comment: `1.1 V thin-oxide NMOS` (not 1.0 V) | `$PDK/gpdk045/nmos1v/` dir; `mos.Cat` line 2; `gpdk045_mos.scs` header |
| 40 | `defvar(divNmosView "symbol")  ; VERIFY` | Keep, drop VERIFY | `"symbol"` | `$PDK/gpdk045/nmos1v/symbol/symbol.oa` |
| 41 | `defvar(divAnaLib "analogLib")` | Keep, mark UNKNOWN | `"analogLib"` (not in PDK) | `$PDK/cds.lib` line 2 (commented); section 5 |
| 42 | `defvar(divBasicLib "basic")  ; VERIFY` | Keep, still UNKNOWN | `"basic"` | `$PDK/cds.lib` line 3 (commented); section 5 |
| 44 | `defvar(divResCell "res")` | Keep, still UNKNOWN | `"res"` (analogLib). PDK alternative, if you must use a PDK resistor: `ressppoly` (PLUS MINUS B) or `resm1` (PLUS MINUS). The bundled Spectre deck uses an ideal resistor, so keep analogLib `res`. | Section 1b |
| 46 | `defvar(divW1 "240n")` | Keep | `"240n"`. Inside bin 30, valid in all corners | Section 4 (gpdk045_mos.scs line 4408) |
| 47 | `defvar(divL1 "45n")` | Keep | `"45n"`. Inside bin 30 (lmin 4E-8, lmax 6E-8) | Section 4; CDF default `l=45n` in `nmos1v/data.dm` |
| 48 | `defvar(divW7 "480n")` | Keep | `"480n"`. Inside bin 23 | Section 4 (gpdk045_mos.scs line 3587) |
| 49 | `defvar(divL7 "90n")` | Keep | `"90n"`. Inside bin 23 | Section 4 |
| 51 | `defvar(divCapCell "cap")` | Keep, still UNKNOWN | `"cap"` (analogLib). PDK alternative: `mimcap` (PLUS MINUS B; CDF `c`) | Section 1c |
| 52 | `defvar(divCapC "10f")` | Keep | `"10f"` | `bundled Spectre cl=10f` |
| 63 | `defvar(tbVdd 1.0)` | Keep value; fix comment | `1.0` is inside the PDK rating (1.1 V). Comment: "PDK nominal 1.1 V; 1.0 V matches divider_gpdk45.scs" | `gpdk045_soa.scs` line 21; section 3 |
| 90-96 | `divPinMasterName` returns `"ipin"`, `"opin"`, `"iopin"` | Keep, still UNKNOWN | - | Section 5 |
| 100, 124 | `cv~>terminals`, `master~>bBox` (SKILL API) | Keep, still UNKNOWN | Terminal names on the nmos symbol are `D G S B`, so the lookup works for them | Section 1a |
| 132, 140, 149, 162 | `schCreateWire`, `schCreateWireLabel`, `schCreatePin`, `schCreateInst` argument lists | Keep, still UNKNOWN | - | Not in PDK (Virtuoso SKILL reference) |
| 170 | `cdfGetInstCDF`, `cdfFindParamByName` | Keep, still UNKNOWN | Parameter names `w` and `l` confirmed (section 1a) | `nmos1v/data.dm` |
| 277 | `schSchemToPinList`, `schPinListToSymbol` | Keep, still UNKNOWN | - | Not in PDK |
| 300 | Terminal names for devices | Keep for nmos | nmos1v: `D G S B` (VERIFIED). res/cap/vdc/vpulse: `PLUS MINUS` (VERIFIED only for PDK cells; analogLib UNKNOWN) | Sections 1a-1c |
| 311-312 | R1/R2 terminals `PLUS` / `MINUS` (analogLib `res`) | Keep, still UNKNOWN | - | Section 1b |
| 313-319 | M1..M7 terminals `D G S B` | Keep | - | VERIFIED (`nmos1v/symbol/symbol.oa` cdsTerm; `data.dm` termOrder) |
| 428 | vpulse CDF names `v1 v2 td tr tf pw per` | Keep, still UNKNOWN | - | analogLib, not in PDK |
| 435-438 | vdc CDF name `vdc` | Keep, still UNKNOWN | - | analogLib, not in PDK |
| 461-463 | `gnd` terminal name | Keep, still UNKNOWN | - | analogLib, not in PDK |
| 468-470 | CL cap terminals `PLUS MINUS` and CDF `c` | Keep, still UNKNOWN for analogLib `cap` | If you switch to PDK `mimcap`: terminals `PLUS MINUS B` (tie B to 0), CDF `c` | Section 1c |

### 9a. Lines in the .il that are not VERIFY but should change

- Comments at lines 39 ("1.0 V thin-oxide NMOS") and 61 ("nmos1v devices" in the 1.0 V note) should say 1.1 V PDK rating. Only the text changes; the value 1.0 stays.
- `cadence/skill/README.md` line 67 mentions CDF names `w`, `l`. Those are confirmed; no change needed.

### 9b. Suggested fix for CDF W/L on `nmos1v` (not applied)

Set `w`, `fw`, and `fingers` together so the PCell and the netlist agree:

```
w = "240n"
fw = "240n"       ; Finger Width (CDF name fw), default 120n
fingers = "1"     ; CDF name fingers (Spectre nf)
l = "45n"
```

This is ASSUMED to match the PDK's own layout approach. It is not verified against a generated netlist.

---

## 10. Open items (UNKNOWN)

1. Whether `ipin`, `opin`, `iopin` exist in `basic` on this Cadence install.
2. Whether analogLib `res`, `cap`, `vdc`, `vpulse`, `gnd` exist with the names assumed in the script, and their CDF and terminal names.
3. Whether the Spectre netlister (with `m=` and `nf=`) is accepted by `g45n1svt` (section 2a risk).
4. The meaning of the `_2` suffix on `ressnpoly_2` and similar cells.
5. Whether `pmos1v` bins match the nch bins (not checked bin-by-bin).
