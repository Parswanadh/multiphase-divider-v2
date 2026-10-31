# Built-in automatic routing for divider_lib/DLATCH (IC 6.1.5, gpdk045)

Status: **DLATCH is routed with the built-in Chip Assembly Router (vcar). Result view:
`divider_lib/DLATCH/layout_routed`. One connection is still open (net `xs`).**
Script: `route_dlatch.il` (same dir). Log: `results/gpdk045/route_dlatch_log.txt`.
Source view: `divider_lib/DLATCH/layout_lxl` (Layout XL generate-from-source, commit 13403a2).
Placement-only view `divider_lib/DLATCH/layout` is untouched (9 instances, 18 shapes, checked).

Citation keys: `sklayoutref` = `cdsdocs/ic615_doc/sklayoutref/`, `vxlhelp` = `cdsdocs/ic615_doc/vxlhelp/`
(host). Guest-only books under `~/cadence/IC615/doc/`: `iccausr/*.html` (Chip Assembly Router user
guide, incl. `save_oa`), `autouser/routedesign.html` (Space-based Router user guide), `rderef/drouteT.html`
(Routing IDE, Tcl commands; NOT the vcar command set).

## 1. Routing entry points

| Function / command | What it does | Batch? | Doc |
|---|---|---|---|
| `vcar` (`~/cadence/IC615/tools/iccraft/bin/vcar`), run standalone from `system()` with `-lib -cell -view -do <cmdfile> -nog -nocheck -quit -noinit -nodid` | Runs the Chip Assembly Router command file on a view. Writes results with `save_oa as <view>`. | **Yes. Used for the result.** | `iccausr` (`save_oa [export] [as <new_view>]`) |
| `leStartRouter(?layoutLCV ?layoutRoutedLCV ?doFile ?showGraphics nil ?quitAtFinish t ...)=> t/nil` | Starts the same router from SKILL. | Starts, but the save back to Virtuoso fails in batch (`cdsServIpc: connection timeout (local host)`). Routes not written. Avoided. | `sklayoutref/chap1.html` 'leStartRouter' |
| `lxSelectedRoute(b)`, `lxSelectedRouteNet(b)` | Routes selected nets in an open window. | No (needs a window). | `sklayoutref/chap2.html` |
| `leHiGuidedRouting`, `leHiP2P` | Interactive. | No. | `sklayoutref/wire.html` |
| `rteDeleteRoutedNets`, `rteSearchAndRepair`, `rteOptimizeRoute`, `rteCheckRoutability` | Clean-up and checks of an existing route. Not a router. | Callable; not used. | `sklayoutref/chap7.html` |
| `dbCopyCellView(src lib cell view "maskLayout")` | Copy a layout view (warns "version: maskLayout is ignored"). | Yes. | (used in tests only) |
| `lxSetConnRef`, `lxUpdateComponentsAndNets` | Attach schematic connectivity to a placed layout. | Yes, but **deletes placed instances that the binder does not match** (see section 3). Not used on the final flow. | `sklayoutref/chap2.html` |

## 2. vcar command set accepted (verified by runs)

- `check (type all)`: accepted. Reports clearance conflicts, re-entrant paths, weak connections.
- `groute`: accepted (global route). `troute` (track route; default quick + refine): accepted.
- `route`: accepted. This is the **detail route** pass (the Route - Autoroute - Detail Route pass, `iccausr`). `droute`, `detailroute`, `detail_route`, `dr`, `detail`, `dtroute`, `route (detail)`, `route (type all)` are NOT valid. `route` with options gives syntax errors.
- `save_oa as layout_routed`: writes the routed design to a new view (`iccausr`, save_oa). Verified: the saved view holds the routed shapes.
- Tcl `puts` is rejected (vcar is not Tcl).

## 3. Connectivity and placement facts (measured)

- Placement-only `layout`: 9 instances (M1-M7, R1, R2), 18 shapes, **no net connectivity on device terminals** (vcar: `Nets 9 Connections 0`). Not routable.
- `lxUpdateComponentsAndNets` on a placed copy deleted all 9 placed instances and created 28 unplaced ones. Rejected.
- Layout XL `layout_lxl` (commit 13403a2): 28 instances (M1..M6 and M7 split x4), 9 pins, connectivity present. vcar preflight: `Nets 12 Connections 137`. Routable. R1/R2 are NOT in this view (no layout master for analogLib `res`), so the routed netlist has no resistors.
- Overlap check (`rdOverlapReport` in the script): **0 overlapping instance pairs** among 28 instances. No placement step was needed.

## 4. Routing result (saved view `layout_routed`)

- Command sequence (`route_dlatch.il`): `groute`, `troute`, `route`, `check (type all)`, `save_oa as layout_routed`.
- After `groute`+`troute`: Percent Connected 99.27 (136 of 137 connections). After `route` and the final wiring statistics: `Unroutes 1`, Percent Connected 94.89. One open connection: `Net xs fromto |M5.4-D_right |M2.1-S_left failed` (groute.fail), unconnected length 0.115 um.
- Router `check`: Clear conflicts 8, re-entrant path violations 4, weak connection violations 2, stub violations 0, net order violations 0, wires thinner than min width 0.
- Vias: 37 total (router wiring statistics). Vias are not counted in the shape list below.
- Saved view counts: 28 instances, 217 top-level shapes:
  - Metal1 pathSeg 73, Metal1 rect 9 (pins), Metal2 pathSeg 17 (routing)
  - Poly pathSeg 76, Oxide pathSeg 13, PWdummy pathSeg 29. These are NOT metal. The router treats these layers as signal layers (tech-derived). They need review in DRC/LVS before use.

### Router layer parameters (from the vcar log, from the tech file, not literals)

| Layer | Width (um) | Clearance (um) |
|---|---|---|
| Metal1 | 0.060 | 0.060 |
| Metal2 .. Metal9 | 0.080 | 0.070 |
| Metal10, Metal11 | 0.220 | 0.200 |
| Poly | 0.045 | 0.060 |
| Via1..Via8 | 0.070 | 0.070 |
| Via9, Via10 | 0.180 | 0.180 |

Signal layers: 35. Constraint group: `virtuosoDefaultSetup`.
DRC rules from `PDK_FACTS.md`: `METAL1.W.1` >= 0.06, `METAL1.SP.1.2` >= 0.1 um (the router uses 0.06 clearance on Metal1, so **Metal1 spacing may be below the Assura rule of 0.1 um**; verify with Assura).

## 5. Next steps / caveats

- The one open connection (`xs`) and the 8 clearance conflicts must be fixed or accepted before the routed view is used for LVS/DRC.
- The 118 non-metal path segments (Poly, Oxide, PWdummy) need checking. They may be router-created signal wires on layers that should not carry routes.
- R1/R2 are missing from the layout (no layout master for analogLib `res`). LVS will not match the schematic until resistors are added.

## 6. Assura (not run here; owned by the verify worker)

Cell/view for the routed result: `divider_lib` / `DLATCH` / `layout_routed`. Placement-only: `divider_lib` / `DLATCH` / `layout`. Source for routing: `layout_lxl`.
Exact avParameters form (from the workflow memory file, not verified in this session):
```
avParameters(?inputLayout ("df2" "divider_lib") ?cellName "DLATCH" ?viewName "layout_routed" ?rulesFile <assura rules> ?workingDirectory <dir> ?runName "DLATCH_routed" ?avrpt t)
```
then `assura <file>.rsf`. `cadence/skill/run_drc.rsf` is an unverified template.

## 7. Batch invocation used

Replay file (`~/gpdk_run/rt/run_route.il`): `load("/home/buet/gpdk_run/skill/route_dlatch.il")` then `routeDlatchMain()`. Launched with
`flock /home/parshu/vm/vm.lock skill_run.sh run_route.il route_dlatch.il`. Router logs: guest `~/gpdk_run/rt/route.log` (run) and `preflight.log`.

## 8. Scratch views

- Deleted by the script (literal names, with `ddDeleteObj`): `DLATCH/layout_nets`, `DLATCH/layout_nets2`, `DLATCH/layout_routed` (old empty view). The first run deleted all three. `layout_nets` and `layout_nets2` were absent on later runs.
- Other views left in divider_lib by this work: none from the routing flow. `DLATCH/layout_routed` is now the routed result (not empty).
