# Built-in automatic routing for divider_lib/DLATCH (IC 6.1.5, gpdk045)

Status: **router is licensed and runs in batch, but DLATCH cannot be routed yet.**
The placement-only `layout` view has no net connectivity on device terminals, so the
router has 0 connections to make. `layout_routed` is NOT produced by a real route.
Script: `route_dlatch.il` (same dir). Log: `results/gpdk045/route_dlatch_log.txt`.

Citation keys: `sklayoutref` = `cdsdocs/ic615_doc/sklayoutref/`, `vxlhelp` = `cdsdocs/ic615_doc/vxlhelp/`,
`vlsgxl` = `cdsdocs/ic615_doc/vlsgxl/` (host). Guest-only books, under `~/cadence/IC615/doc/`:
`autouser/routedesign.html` (Space-based Router User Guide), `rderef/drouteT.html` (Routing IDE
AutoRouter command reference), `iccausr/*.html` (Chip Assembly Router user guide).

## 1. Routing entry points in IC615 6.1.5

| Function / command | What it does | Batch from SKILL? | Doc |
|---|---|---|---|
| `leStartRouter(?layoutLCV list(lib cell view) ?layoutRoutedLCV list(lib cell view) ?doFile f ?showGraphics nil ?quitAtFinish t ?statusFile f ...)=> t/nil` | Starts the Chip Assembly Router (`vcar`, `iccraft/bin/vcar`) on the source view, writes the routed result to the routed view, runs the do-file commands. | **Yes, tested.** Returns t, creates the routed view. | `sklayoutref/chap1.html` 'leStartRouter' (Example 1 and 2) |
| `lxSelectedRoute(b_useWAOverrides)`, `lxSelectedRouteNet(b_useWAOverrides)` | Routes the nets selected in the **layout window**. | No. Needs a selection in a open window. Not usable in `-nograph` batch. | `sklayoutref/chap2.html` |
| `leHiGuidedRouting([w])`, `leHiP2P([w])`, `leHiCreateWire` | Interactive wire commands. | No (window commands). | `sklayoutref/wire.html` |
| `rteDeleteRoutedNets`, `rteSearchAndRepair`, `rteOptimizeRoute`, `rteCheckRoutability`, `rteFixViolations` | Post-route clean-up / checks of an existing route. They do not route. | Yes (callable), but need an existing route. | `sklayoutref/chap7.html` (Virtuoso Space-based Router SKILL functions) |
| `leCreatePath(d_cv l_lpp l_points n_width [t_style] [n_offset] [t_just])=> d_pathId` | Manual path. Used by any hand fallback. | Yes (callable). | `sklayoutref/chap1.html` 'leCreatePath' |
| `dbCreateVia`, `lxGetValidViaDefs(d_obj [cg] [bottom] [top])`, `lxGetPinNets()` | Via creation, via-definition lookup, pin-net list. | Yes (callable). `lxGetValidViaDefs` in `sklayoutref/chap2.html`. | `sklayoutref/chap2.html` |
| `leGetValidLayerList`, `leGetEntryLayer`, `leGetValidPurposeList` | Layer / purpose lists from the tech file. | Yes (`leGetValidPurposeList` in `sklayoutref/chap1.html`). | `sklayoutref/chap1.html` |

NOT FOUND in the docs or the session: `leRouteNets`, `rteRoute*`, `rteAutoRoute`, `lxAutoRoute`,
`techGetLayerPurposePair` (not callable in this session). Use `leGetValidLayerList` and
`leGetEntryLayer` to read layers instead.

Router commands (Chip Assembly Router do-file, `iccausr/`; Routing IDE Tcl, `rderef/drouteT.html`):
- `check (type all)` [D: `iccausr/chap4` example text] - VERIFIED accepted by vcar.
- `groute` (global route), `troute` (track route; default = `troute (quick)` + `troute (refine)`) [D: `iccausr/chap6`]. VERIFIED accepted by vcar (no error).
- `droute` (detail route) [D: `iccausr/chap6`, example name "Detail routing" ; VERIFY that the exact name is accepted; the preflight run did not reach it].
- Routing IDE (`rderef`) names: `global_route`, `local_route`, `detail_route`, `search_and_repair`, `optimize_routes`. These are Tcl commands of the Routing IDE, NOT of vcar. vcar rejected Tcl `puts` ("Unrecognized command puts").

GUI-only automatic route: Route - Automatic Routing form (Selected Set, Global Route, Local Route, Detail Route, Refinement steps). [`autouser/routedesign.html`, guest path above]. Needs a window, not batch.

## 2. Licence evidence (this VM, batch)

- Licence file: `CDS_LIC_FILE=/home/buet/cadence/IC615/ic6151license.dat`. Its FEATURE list includes `Cadence_chip_assembly_router`, `Virtuoso_custom_router`, `Route`, `IC_autoroute`, `Virtuoso_Layout_Suite_XL`, `Virtuoso_Layout_Suite_GXL`. (names only, no secrets printed)
- `lmstat` cannot run in the guest (`bad ELF interpreter /lib/ld-lsb.so.3`). The licence was tested by running the tool.
- `vcar` (`iccraft/bin/vcar`) prints `Virtuoso Framework License (111) was checked out successfully` and runs the commands. Its log for the preflight shows `Nets 9 Connections 0`. No licence error for the router was printed.
- Warning seen: `(icLic-32) vcar: Could not establish MPS-connection to session 'virtuoso16187'`. This is harmless for the run.
- Conclusion: **the Chip Assembly Router is usable in batch; its licence is not the blocker.** The blocker is connectivity.

## 3. Why the placement-only DLATCH cannot be routed (measured)

- Layout `divider_lib/DLATCH/layout`: 9 instances (M1-M7 `gpdk045/nmos1v`, R1, R2 `gpdk045/resnsnpoly`), 18 shapes, 9 nets (the pin nets). vcar preflight: `Nets 9 Processed, Net Terminals 9, Signal Connections Created 0`, `Nets 9 Connections 0`.
- The router needs device terminals attached to nets. They are not in the placement-only view.
- Connectivity from the schematic, tested in batch (`lxSetConnRef` + `lxUpdateComponentsAndNets`, on a scratch copy):
  - `lxUpdateComponentsAndNets` returned t but **deleted all 9 placed instances** (LX-2004 "does not exist in the schematic") and created 28 new ones (`Instances created: 28`, `Instance connectivity updated: 0`). The hand placement is lost, so this path is rejected.
  - The schematic's instance names match the layout's names (M1-M7, R1, R2), so the mismatch is in the binder (`Schematic instances with corresponding layout instances: 0`). Cause not found. R1 and R2 also give `no layout master defined` (schematic `analogLib/res` vs layout `gpdk045/resnsnpoly`).
  - A later batch run in the same session ended with `SIGBUS` (crash report `/tmp/crashReport_103126_1648__buet_cadence.log`).
- So neither "route the placed view" nor the connectivity-driven hand fallback has the net data. A hand fallback would need device terminal nets assigned from the schematic first, which is a larger job.

## 4. Route to a routed DLATCH (next step, not done here)

1. Get a connected layout with the LXL worker's Generate-All-From-Source flow (`auto/lxl_flow.il`) into a NEW view (e.g. `layout_lxl`), not `layout`. That flow re-places the cell, so the routed result will not keep the hand placement. Record which placement is used.
2. Then run `route_dlatch.il` with `rdSrcView` set to that view. The preflight then sees connections and `leStartRouter` writes `rdRoutedView`.
3. Check the do-file: confirm `droute` accepted (VERIFY in the log).

## 5. Layer and spacing values (for the routing step, not used yet)

From `cadence/skill/PDK_FACTS.md`: Metal1 `Metal1` (7/0), Metal2 `Metal2` (9/0), Metal3 `Metal3` (11/0); DRC: `METAL1.W.1` width >= 0.06 um, `METAL1.SP.1.2` spacing >= 0.1 um, `VIA1.E.1` enclosure >= 0.005 um. The router uses the tech file rules through the constraint group `virtuosoDefaultSetup` (`leStartRouter` log: `virtuosoDefaultSetup is the effective constraint group`). The router log lists 35 signal layers. These values were NOT taken from routing output.

## 6. Assura DRC/LVS (not run here; owned by the verify worker)

Exact command for DLATCH after the routed view exists (from memory file `cadence-vm-gpdk045-workflow`, and `cadence/skill/run_drc.rsf`):
```
avParameters(?inputLayout ("df2" "divider_lib") ?cellName "DLATCH" ?viewName "layout_routed" ?rulesFile <assura rules> ?workingDirectory <dir> ?runName "DLATCH_routed" ?avrpt t)
```
then run `assura <file>.rsf`. The current `run_drc.rsf` is a template and is NOT verified. Use the verify worker's flow.

## 7. Batch invocation used

Replay file (guest `~/gpdk_run/skill/run_route.il`): `load("/home/buet/gpdk_run/skill/route_dlatch.il")` then `routeDlatchMain()`. Launched with `flock /home/parshu/vm/vm.lock skill_run.sh run_route.il route_dlatch.il`. Virtuoso writes the router log through its own path, so the log in results/ was built from the Virtuoso output and the preflight log.

## 8. Scratch artifacts left in divider_lib (for cleanup by the owner; nothing deleted)

- `DLATCH/layout_routed`: empty view created by an early `leStartRouter` probe. It is not a routed result. Delete it before using `layout_routed` for real.
- `DLATCH/layout_nets`, `DLATCH/layout_nets2`: copies made by the `lxUpdateComponentsAndNets` test. They hold the wrong 28-instance layout. Do not use them.
- The placement-only `DLATCH/layout` was not saved or changed by this work (shape and instance counts unchanged, 18 and 9).
