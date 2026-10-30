# Divider schematic builder (Cadence Virtuoso SKILL)

`build_divider.il` creates the divider schematics so you do not have to draw them by hand.

**UNTESTED: written without access to Cadence; first run may need small fixes.**

## What it creates

| Cell | View | Contents |
|---|---|---|
| `DLATCH` | `schematic` | M1-M6 (nmos1v, W=240n L=45n), M7 tail (nmos1v, W=480n L=90n), R1 R2 (analogLib `res`, 8k), pins D Db CK CKb NBIAS (input), Q Qb (output), VDD VSS (inputOutput) |
| `divider_core` | `schematic` | XD1..XD4 (DLATCH instances). Latches 2 and 3 have CK/CKb swapped. Pins CK CKb NBIAS VDD VSS, outputs Q1 Q1b Q2 Q2b Q3 Q3b Q4 Q4b |
| `tb_divider` | `schematic` | divider_core, vdc VDD and NBIAS, vpulse CK and CKb (CKb delayed half a period), 10 fF on each output, analogLib `gnd` |

Connectivity is copied from `spectre/divider_gpdk45.scs`. Bulk is VSS. The SPICE deck `spice/divider_baseline_cal.cir` differs: it ties bulk to the source node and uses different sizes and loads. This builder does not follow it.

## Prerequisites

1. Library `divider_lib` exists and is attached to the gpdk045 technology library. The script does not create it.
2. The gpdk045 PDK is loaded, so `nmos1v` is available.

## How to run (CIW)

```
load("/absolute/path/to/cadence/skill/build_divider.il")
buildDivider()          ; builds DLATCH, then divider_core if the DLATCH symbol exists
```

If buildDivider stops after DLATCH, it prints `STOP ...`. Then:

1. Make the DLATCH symbol: in the Library Manager, select `DLATCH` schematic, then Design > Create Cellview > From Cellview. Save it.
2. Run `buildDividerCore()`.
3. Make the divider_core symbol the same way (Create Cellview > From Cellview), or let the script try it.
4. Run `buildTestbench()`.

Re-running a builder skips a cell whose schematic already exists. To rebuild, delete the cell in the Library Manager first.

## Set the testbench values for your run

The defaults in the `tunables` block at the top of the file are now the gpdk045 starting values:

- `tbVdd 1.0`, `tbVbias 0.8`, `tbPeriod 1e-9`, `tbRise 20e-12` (gpdk045 starting values, tune them)

To change them, set these in the CIW before `buildTestbench()`:

```
tbVdd = 1.0
tbVbias = 0.8
tbPeriod = 1e-9
```

**Warning:** 1.8 V on 1.0 V nmos1v devices is an overstress. Do not run gpdk045 at 1.8 V.

## Simulation setup (not done by the script)

- **Initial conditions:** set them in ADE (Outputs/ICs or Initial Conditions). Use Q1=VDD, Q1b=0, Q2=VDD, Q2b=0, Q3=0, Q3b=VDD, Q4=0, Q4b=VDD. Without them the symmetric state may never resolve and the divider will not divide.
- **Transient:** stop time 40n (matches the Spectre file), and maximum step 5p.
- Confirm that the Spectre netlist contains the subckt and the gpdk045 model include.

## Debugging in the CIW

| You see | Likely cause | Fix |
|---|---|---|
| `Unbound variable: divLib` or similar | The file was not loaded | Re-run `load(...)` with the absolute path |
| `ERROR: library divider_lib does not exist` | Library missing | Create it and attach gpdk045 |
| `WARNING: terminal X not found on nmos1v` then the rest fails | Terminal names differ in your PDK | Run `dbOpenCellViewByType("gpdk045" "nmos1v" "symbol" "symbol" "r")~>terminals~>name` and update the names in the tables |
| `WARNING: could not set w=... on M1` | CDF parameter name differs | Set W/L by hand in the Properties form (Q), then check the names with `cdfGetInstCDF(inst)~>parameters` |
| `WARNING: label X failed` or `WARNING: pin X not created` | `schCreateWireLabel` or `schCreatePin` argument list differs | Check the call in the Schematic Editor SKILL reference; the wrappers `divLabel` and `divPinAt` are the only places to edit |
| `schCheck ... returned: ...` with floating pins, unconnected terminals, or dangling wires | Terminal location was guessed wrong (pin hotspot), so a stub missed its pin | Open the cell, move or redraw the flagged stub. The rest of the connectivity is still correct because nets are matched by name |
| `MANUAL STEP: symbol ... could not be created` | `schPinListToSymbol` path not confirmed | Use the GUI: Design > Create Cellview > From Cellview |
| `ERROR: could not place X` | `dbOpenCellViewByType` for the master failed | The master symbol does not exist or the library name is wrong (see `divMaster`) |

Errors are printed by `errset(..., t)`, so the real Cadence error text appears in the CIW above the script's own warning.

## VERIFY list (check these before the first run)

1. `divPdkLib`, `divNmosCell`, `divNmosView`: the nmos1v cell name, library, and symbol view in your gpdk045.
2. `divBasicLib` and the pin masters `ipin`, `opin`, `iopin`: their names and location (`basic` library).
3. Terminal names: nmos1v `D G S B`, and `PLUS MINUS` for res, cap, vdc, vpulse. The `gnd` terminal is named `gnd`.
4. CDF parameter names: `w`, `l`, `r`, `c`, `vdc`, and the vpulse names `v1 v2 td tr tf pw per`. Check them with `cdfGetInstCDF(inst)~>parameters`.
5. Signatures of `schCreateWire`, `schCreateWireLabel`, `schCreatePin`, `schCreateInst`, `schCheck`, and `dbOpenCellViewByType` (mode string `"r"` or `"w"`, not `'read`).
6. `schSchemToPinList` and `schPinListToSymbol` (symbol generation). These are not confirmed.
7. Terminal location: the script takes the centre of a pin figure's bounding box. If stubs land off the pins, adjust `divTermLocal`.
8. The instance orientation is always `R0`.
9. `defvar` values can persist in the CIW. If an edit has no effect, set the variable directly in the CIW.

## Known limits

- Connectivity is by net label name. Pins are placed on the left and right edges, not in any optimal layout.
- Instance positions are fixed grid values, so the schematics are readable but not tidy.
- The script does not set ADE initial conditions or the simulator options. See the simulation setup section.
- The script never runs a simulation.

## Files

- `build_divider.il`: the SKILL script.
- `README.md`: this file.
