# analogLib `res` vs PDK `g45rnsnp`: why LVS fails on the resistors, and a fix plan

Read-only analysis. No schematic or layout was changed. Source files: host copy of the PDK
(`/home/parshu/vm/pdk/gpdk045_v_6_0`), `models/spectre/gpdk045_resistor.scs`, `assura/extract.rul`,
`results/gpdk045/assura_lvs_dlatch_baseline.txt`, `cadence/skill/PDK_FACTS.md`.
The guest was not reachable, so nothing here was simulated or re-run in Virtuoso.

## Why LVS fails on the resistors

1. **Terminal count.** The schematic resistor is analogLib `res`, with two terminals (PLUS, MINUS).
   The layout device extracted from the poly resistor is `g45rnsnp`, with three terminals: PLUS, MINUS and bulk B.
   `extract.rul` shows the bulk tie: `extractRES("g45rnsnp" _resnsnpoly poly_conn("PLUS" "MINUS") pwell("B") ...)`.
   The baseline LVS report confirms it: `res(RES): 5 out of 5 pins were unmatched (schematic PLUS MINUS; layout PLUS MINUS B), further matching disabled.`
2. **Device class.** Run A matched the device types (`res(RES)` against `g45rnsnp(RES)`), but the pin mismatch stopped the top-level comparison.
3. **Run B** (layout bulk pin deleted with `deleteCellPin`) got past the pins. The comparison then ran to the end and reported `(res, g45rnsnp) RES 2 2 0 0`:
   the two resistors were not matched. Their nets `avC31..avC34` (poly to Q/Qb) had no connection in the placement-only layout.
   So the bulk pin is only one of the problems. The resistor routing is the other.
4. **Parameter values are not compared.** `extract.rul` says: "Known issue with resistor `r` parameter. Currently only using w,l." An `r` value on the schematic device is therefore not checked against the layout. Resistance equality must come from the layout geometry (w, l), not from the `r` property.

## What the PDK offers

| Cell | Terminals | Spectre subckt | Matches extract.rul? |
|---|---|---|---|
| `resnsnpoly` (N+ poly, no salicide) | PLUS MINUS B (PDK_FACTS, VERIFIED) | `subckt resnsnpoly (n1 n2)`, **2 ports** | yes: `cellView("resnsnpoly ivpcell gpdk045")` |
| `ressnpoly` (N+ poly, salicided) | PLUS MINUS B | `ressnpoly (n1 n2)` | layout `g45rsnp` (not in the extraction list checked) |
| `resnsnpoly_2` and other `_2` variants | PLUS MINUS (no B); CDF has SUB and bulkn | `g45rnsnp` family | not in `extract.rul` cellView list; the `_2` suffix is not documented |
| `primRes2` | PLUS MINUS | pPar model | not checked |

Key facts about `resnsnpoly`:

- Its Spectre model has two ports. Bulk `B` is **not** connected in the model. In simulation the B terminal is cosmetic, and it has to be tied in the schematic (to `gnd!`).
- The model (`gpdk045_resistor.scs`, lines 485–497) gives R = rsh·(L−dl)/(W−dw)·tfacp·(bias term) plus two end resistances rend0/(W)·tface.
- Section `tt_res` (lines 56–95): `r_resnsnpoly = 200` Ω/sq, `r_rend_resnsnpoly = 1.44e-5`, `dl = dw = 0`. The corner sections (`ss_res`, `ff_res`) scale both.
- Rough sizing, not verified: at tt, 27 C, R ≈ 200·(L/W) + 2·14.4 Ω for W = 1.0 µm. For R = 3 kΩ, L/W ≈ 14.9 squares, so W = 1.0 µm and L ≈ 14.9 µm. The bias term is about 1 % at 0.5 V, by hand.

## Would a `resnsnpoly` schematic simulate with the same resistance?

In principle, yes, if the schematic uses the same geometry (W, L) as the layout. Then the schematic has the same subckt as the simulator reads from the PDK. But it is not the same netlist as now:

- `res R=3k` (analogLib, ideal) becomes a 15 µm poly resistor with bias and temperature dependence. The power and delay of design D will move. Expect a few percent, which is enough to change the reported numbers.
- So the existing numbers (0.541337 mW standalone, 0.455 mW in the Virtuoso netlist, 41/45 corners) cannot be reused. The whole 45-corner PVT sweep would have to be run again.

## Concrete plan

1. In the guest (after the VM is up): ship a small Spectre deck with one `resnsnpoly` (W = 1.0 µm, L ≈ 14.9 µm, B tied to 0) and a DC sweep. Compare its resistance with 3 kΩ at tt. Do the same for ss and ff. Only if this matches within the target tolerance go on.
2. Read the layout geometry of the current `res`-based resistor cells (if any are drawn). Compare its W and L to step 1. If they differ, the layout must be redrawn to the chosen W and L. The LVS check only compares w and l, so these must agree exactly.
3. Build a schematic variant (not in `DLATCH` yet): swap `res` for `resnsnpoly` with the chosen w and l and B tied to `gnd!`. Schematic check, LVS on the cell.
4. Re-run design D at 1.4 GHz and compare with the existing run. Accept the new numbers only after a full 45-corner sweep.
5. Alternative with no schematic change: keep `res`, and delete the layout bulk pin in the compare rules (the same idiom PDK `compare.rul` uses for the `g45inds` CTAP). This is what Run B did as a diagnostic. It also needs the resistor routing fixed, and it is not a faithful LVS comparison, so it should be reported as such.

## Risks

- Using `resnsnpoly` changes the simulated circuit: the bias term and temperature term are real effects, so the results change (see above).
- The resistor is about 15 µm long at 1.0 µm width. The DLATCH and divider_core placement will grow, and poly spacing (POLY.SP.1 ≥ 0.3 µm) and the width rule (min 0.1 µm, suggested 0.8 µm) apply.
- The `_2` variants are not in the extraction cellView list. Using them could reproduce the current mismatch. Do not use them without checking the layout cell they map to.
- The layout resistor geometry is in the guest (not read here). Until it is read, the W and L in step 1 are a guess.
