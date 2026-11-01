# RCX / QRC discovery for gpdk045 (read only)

Date: 2026-11-01. Scope: find any parasitic-extraction technology files usable with Assura RCX or QRC.
Nothing was installed or changed.

## What was searched

| Where | How | Result |
|---|---|---|
| Host PDK copy `/home/parshu/vm/pdk/gpdk045_v_6_0` (same tree as guest `/home/buet/pdk/gpdk045_v_6_0`) | `ls`, `find` by name (`*qrc*`, `*.rcx*`, `*captbl*`, `*.rul`), read of `assura/`, `soce/`, `diva/`, `pvs/`, `gpdk045/tech_gpdk045.tf` | See below |
| Host `/home/parshu/vm/cadence` (Cadence install as VMDK images) | name search | Not searched: it is a set of `Cadence-sNNN.vmdk` disk images, not a file tree. Not mounted. |
| Guest `/home/buet/cadence`, `/home/buet/pdk`, `/opt` | `find` for `qrcTechFile`, `*.qrc`, `*.rcx`, `*.capTbl`, `qrc`/`assura` install dirs | **Not done.** The guest did not respond (see "VM status"). |

Assumption: the guest PDK matches the host copy. The earlier ASSURA_FLOW_NOTES.md (verified in the guest) also reports that `qrc/` is absent, which agrees.

## What exists

- `assura/techRuleSets` sets `RcxSetupDir "../qrc"` (and `../qrc/typical`, `../qrc/worst`, `../qrc/best`). These directories are the RCX technology location.
- `assura/.rcx_setup.tpl`: a QRC UI 9.1.1 form template (output formats Spectre, Spice, DSPF, SPEF; parasitic R/C/L components `presistor`, `pcapacitor`, `pinductor`; "rcxfs" and RLCK options). It holds options only. It does not point at a technology file.
- `assura/extract.rul` (79 KB): Assura LVS device extraction rules (header: "ASSURA(r) version 3.17 LVS file"). It is not an RCX rule set. It does define the device `g45rnsnp` for the poly resistor (`extractRES("g45rnsnp" _resnsnpoly poly_conn("PLUS" "MINUS") pwell("B") ...)`).
- `soce/gpdk045.ict`: Encounter interconnect technology (ICT) for the process stack (diffusion, polycide, METAL_1 ... with thickness, height, resistivity). This is the usable input for building an extraction technology file. It is not one itself.
- `soce/gpdk045.basic.CapTbl` and `gpdk045.extended.CapTbl`: Encounter capacitance tables generated from the ICT (README: basic about 6 min, extended up to 19.5 h). These are Encounter files, not QRC tech files.
- `gpdk045/tech_gpdk045.tf`: Virtuoso technology file (layers, `extractMOS` declarations). It is used by Virtuoso and not by RCX.
- `diva/divaEXT.rul`, `pvs/extview.rul`: Diva and PVS extraction rules. Not RCX rule sets.

## What is missing

1. The QRC or RCX technology file (`qrcTechFile` / `.tch` / `.tf` for QRC) for gpdk045.
2. The `qrc/` directory and its `typical`, `worst`, `best` sub-directories that `techRuleSets` expects.
3. Any QRC or RCX rule or setup file containing layer-to-process mapping, corner files, or the via and resistance tables.
4. Any QRC or RCX cap table in the QRC format (the two `.CapTbl` files are Encounter format).

## Next step to enable extraction

Both of these are needed; the first alone is not enough.

1. In the guest, search first (read only), then decide:
   `find /home/buet/cadence /home/buet/pdk /opt -maxdepth 6 \( -iname '*qrc*' -o -iname '*.rcx' -o -iname '*captbl*' -o -iname 'qrcTechFile*' \) 2>/dev/null`
   `which qrc rcx avRCX 2>/dev/null; ls /home/buet/cadence/tools*/ 2>/dev/null`
   If a QRC install exists, use its tech-import tool on `soce/gpdk045.ict` to build the tech file.
   If no QRC install exists, the RCX step cannot run with this PDK copy.
2. Create `/home/buet/pdk/gpdk045_v_6_0/qrc/{typical,worst,best}/` with the generated tech file. Only then does `RcxSetupDir` resolve.
3. LVS must be clean first. Right now it is not (see `results/gpdk045/assura_lvs_dlatch_baseline.txt`: the resistor `res` vs `g45rnsnp` mismatch, and the layout is placement only). RCX runs after a successful LVS in the same run directory (ASSURA_FLOW_NOTES.md).

## VM status

The VM was started headless on 2026-11-01 at about 09:49 IST. The VirtualBox log shows the guest boot and a 800x600 display mode at 00:00:25 and no later activity. The screen stayed black through about 15 minutes of waiting, a key press, a mouse event, and one hard reset. No guest command could be run, so the guest search above is still to do.
