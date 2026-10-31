# build_schematic_v2.il: notes

UNTESTED. Written without Cadence. Run it, send the CIW output back.

## Run

```
load("/absolute/path/to/cadence/skill/build_schematic_v2.il")
buildAll()                  ; DLATCH -> symbol -> divider_core -> symbol -> tb_divider
showSchematic("DLATCH")     ; read-only window; press f to fit, then screenshot
```

Prerequisites (not done by the script):
- Library `divider_lib` exists and is attached to gpdk045. If not, Library Manager > File > New > Library, attach to gpdk045. The script only prints these steps.
- No techfile is attached by the script (not certain of the API).

## What gets built

| Cell | Contents |
|---|---|
| DLATCH | M1..M6 nmos1v (w=240n l=45n), M7 nmos1v (w=480n l=90n), R1 R2 analogLib `res`, pins D Db CK CKb NBIAS (in), Q Qb (out), VDD VSS (inout) |
| divider_core | XD1..XD4 = DLATCH symbol, connected per the netlist. Pins CK CKb NBIAS VDD VSS, Q1 Q1b Q2 Q2b Q3 Q3b Q4 Q4b |
| tb_divider | divider_core, vdc VDD and NBIAS, vpulse CK and CKb (CKb delayed half a period), cap 10f on 8 outputs, gnd |

Connectivity is copied from `spectre/divider_gpdk45.scs`. Every NMOS bulk is VSS.

## Decisions to check

1. **R1/R2 value: `resR = "2k"`, as requested. The netlist uses `rl=8k`.** Change `resR` if you want the netlist value.
2. **Overwrite is on by default** (`v2Overwrite t`). Existing views are deleted and rebuilt. Close any window that shows them first, or the delete fails with a message.
3. **nmos1v parameters:** `w`, `fw` (= w), `fingers` = 1, `l`, `m` = `mult` (= 1). Matches PDK_FACTS 9b.
4. **Layout** is a readable grid, not a copy of the paper. DLATCH: resistors top, sample pair M1/M2, M5 centred under them, hold pair M3/M4, M6 centred, M7 at the bottom. divider_core: a clockwise ring, XD1 top-left, XD2 top-right, XD3 bottom-right, XD4 bottom-left. **This is not checked against Fig. 2.**
5. **Wire stubs** run along the dominant axis. Only the stub end is grid-snapped. Snapping the attach point would detach the wire.
6. **Not done:** fit-to-window (I am not sure of the API; press f in the window), techfile attach, library creation, and ADE setup.

## Simulation setup (ADE, not in the script)

Initial conditions from the netlist `ic` line, to set in ADE:

`Q1=tbVdd Q1b=0 Q2=tbVdd Q2b=0 Q3=0 Q3b=tbVdd Q4=0 Q4b=tbVdd`

Without them the symmetric state may never resolve.

Also: tb defaults `tbVdd=1.0`, `tbVbias=0.8`, `tbPeriod=1e-9`, `tbRise=20e-12`. Do not use 1.8 V on these 1.1 V devices.

`defvar` keeps old values in a live CIW session. To change a value now, type e.g. `resR = "8k"` before `buildAll()`, or restart the CIW.

## Likely failure points (the CIW output names them)

- `schCreateWireLabel`: 9-argument form tried first, then 10-argument. The working form is printed once.
- `schCreatePin` argument order: a WARNING line appears if it fails.
- Symbol creation: `schViewToView` first, then `schSchemToPinList` + `schPinListToSymbol`. If both fail, a MANUAL line gives the GUI steps (Design > Create Cellview > From Cellview).
- CDF parameter names and types (`prm->type`, `atoi`). A WARNING names the parameter that could not be set.
- Terminal names: `v2DiagTerms` prints the real names for nmos1v, res, cap, vdc, vpulse, gnd and ipin. The gnd terminal is resolved at run time.
