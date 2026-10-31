# Assura LVS / RCX flow for gpdk045 (what was learned, what runs)

Sources: the gpdk045 PDK copy (guest /home/buet/pdk/gpdk045_v_6_0/assura: extract.rul, compare.rul,
LVSinclude.rsf, techRuleSets, .lvs_setup.tpl, .rcx_setup.tpl), the Assura 4.1 user and command
reference (guest /home/buet/cadence/ASSURA41/doc/assurauser, assuracommandref), and the Assura 4.1
sample runs in guest /home/buet/cds_work/mylib2/nand2 (run2.rsf = GUI-generated LVS, rcx.run2.rsf = RCX).

## PDK rule files
- `techRuleSets` ruleSet "default": DrcRules assuraDRC.rul, LvsExtractRules extract.rul,
  LvsCompareRules compare.rul, LvsInclude LVSinclude.rsf, RcxSetupDir ../qrc (absent in this PDK copy).
- `compare.rul` contains only comparison tolerances and parameter comparisons (MOS, RES, CAP, g45inda/g45inds).
- `LVSinclude.rsf`: bind(net "*[*]" "*<*>"), mergeSplitGate(sameOrder), autoPinSwap, expandOnError.
- `.lvs_setup.tpl` / `.rcx_setup.tpl` / `.avc_setup.tpl` / `.drc_setup.tpl` are GUI form defaults (Assura 3.2 style),
  not needed for batch runs.
- The PDK has NO qrc/ (RCX tech) directory. soce/ has only *.CapTbl files (Cadence QRC cap tables).

## Batch LVS (what works)
RSF: `avParameters(?inputLayout ("df2" LIB) ?cellName CELL ?viewName "layout" ?rulesFile extract.rul
?workingDirectory DIR ?runName RUN ?avrpt t ...)`, then `load(compare.rul)`, `load(LVSinclude.rsf)`,
`avCompareRules( schematic( netlist( dfII "DIR/RUN.vlr" ) ) )`, `avLVS()`. Run as `assura file.rsf`.
- The schematic side is netlisted by dfIIToVldb. Its native rules file is the file named in netlist(dfII ...):
  it must exist and contain avLibName, avCellName, avViewName, avSimName, avViewList, avStopList,
  avVldbFile (the VLDB output). The DLATCH rules are in verify/templates/netlist.vlr.in.
  Running `dfIIToVldb <rules.vlr> <rsf>` before `assura` produces the VLDB (run_verify.sh does this for stage lvs).
- Without groupModels( RES ) the run aborts with "Device unbound" (schematic res vs layout g45rnsnp), so the
  template has groupModels( RES ) in the general section.
- `?joinPins top` (unquoted). `"Top"` gives an AVRC-10548 warning.
- Output: runName.lrs (summary per cell), runName.cls (pin/net/device mismatch detail), runName.csm,
  runName.sum (echoed RSF and timing), runName.msg/.wrn (warnings).

## Batch RCX
The Assura sample: `avParameters(?workingDirectory ?runName ?inputLayout ?cellName ?viewName ?techLib)` +
`rcxParameters(?rcxSetupDir ... ?outputFormat "dfII" ?extractedView "av_extracted" ...)` + `avRCX()`.
RCX needs a successful LVS (avNX) in the same run dir and an RCX tech directory. Here the rcxSetupDir
(/home/buet/pdk/gpdk045_v_6_0/qrc) does not exist, so RCX stops at setup. Not runnable with this PDK copy.

## Guest environment limits found
- Guest / (sda1) is full (17-25 MB free). Assura writes runName.dat/.bcr/.tmp into the run dir and failed with
  "No space left on device". The LVS template therefore sets `?diskList (("/dev/shm/RUN" 1G))` (tmpfs, 2 GB).
- DRC still writes temporary files to /tmp (on /), so stage drc fails with "Can't write the temporary file in /tmp".
  It works only when the guest disk has space (the earlier DRC run was done before the disk filled).

## Wrapper
`run_verify.sh CELL drc|lvs|rcx` fills templates/<stage>.rsf.in (and netlist.vlr.in for lvs), ships the files on a
virtual CD, runs `assura` in the guest under the shared flock, and prints the tail of the Assura console log.
Variants: env EXTRA="<avCompareRule>" RUNTAG=_suffix (used for the diagnostic LVS run B).
Results are read from the guest run dir /home/buet/verify/<CELL>_<STAGE>[RUNTAG] (.lrs, .cls, .csm).
