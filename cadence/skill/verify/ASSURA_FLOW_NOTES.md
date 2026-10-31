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

## Run: DLATCH layout_routed (DRC and LVS)
- Wrapper now takes VIEW (default `layout`, env override). It is filled into `@VIEW@` in drc, lvs and rcx templates
  from one variable in run_verify.sh. Usage: `VIEW=layout_routed RUNTAG=_routed ./run_verify.sh DLATCH drc|lvs`.
- DRC (`assura` exit 0, "terminated normally"): 134 real errors in 17 rules (placement-only baseline: 21 errors in
  3 rules). Largest: LATCHUP.2 56, NIMP.O.1 21, OXIDE.X.1 12, NIMP.E.1 12, METAL1.A.1 12. Results in
  results/gpdk045/assura_drc_dlatch_routed.txt.
- LVS run 1 (default RSF) aborts in nvn: "Device 'res(RES)' on Schematic is unbound to any Layout device" (the routed
  layout has no resistor instances). No comparison report is written. groupModels(RES) does not help when the layout
  has no RES device at all.
- LVS run 2 (diagnostic, not a pass): `EXTRA='schematic( filterDevice( "res" ) )'` with RUNTAG=_routed_nores. It
  completes: 10 net, 15 device, 0 pin, 3 parameter mismatches, all from the routed layout (open nets, missing bulk
  ties to VSS on 8 MOS B pins, finger/series structure, finger width 0.24 vs 0.96 um). Results in
  results/gpdk045/assura_lvs_dlatch_routed.txt.
- No "No space left on device" error in these runs (DRC and LVS both use diskList on /dev/shm and TMPDIR=/dev/shm).
- Guest / was at 119 MB free (100 % used) during both runs.
