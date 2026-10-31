# Layout XL "Generate From Source" flow for divider_lib (IC 6.1.5)

Sources: IC615 6.1.5 HTML copies in `/home/parshu/vm/cdsdocs/ic615_doc/`.
Citation keys: `vxlhelp` = Virtuoso Layout Suite XL User Guide, `sklayoutref` = Virtuoso Layout Suite SKILL Reference, `vlsgxl` = Virtuoso Layout Suite GXL Reference.
Citations use the file and heading as printed in the doc. "NOT IN DOCS" marks things the docs do not cover.

Companion script: `lxl_flow.il` (same directory). Every unverified argument there carries `;; VERIFY`.

---

## 0. Tiers and licenses (read first)

| Capability | Tier | Doc |
|---|---|---|
| Generate All From Source, Selected From Source, Place As In Schematic (PAS), Update Components And Nets, Check Against Source, Pin editing | Layout XL | `vxlhelp/chap6.html`, `vxlhelp/chap10.html`, `vxlhelp/chap9.html` |
| Layout XL is launched from a schematic (Launch - Layout XL). It checks out a Layout XL license if none is held | Layout XL | `vxlhelp/chap1.html`: 'Starting Layout XL with an Automatic Physical Configuration View'; `vxlhelp/chap4.html`: 'License Requirements' |
| Custom Digital Placer (Place - Custom Digital - Placer) | Listed in the XL menu reference, but the GXL guide lists it as a GXL application "accessed with token licenses" | `vxlhelp/appB.html`: 'Command Quick Reference' (Place Menu); `vlsgxl/chap1.html`: 'GXL Applications' |
| Analog Placer, Modgen, Floorplanner, Space-based Router | Layout GXL, token licenses | `vlsgxl/chap1.html`: 'GXL Applications'; `vxlhelp/chap6.html`: lines noting "Add Geometries or Transfer Constraints requires a Layout GXL license" |
| Layout GXL launch | GXL | `vlsgxl/chap1.html`: 'Launching GXL' (Launch - Layout GXL); SKILL `lxLaunchLayoutGXL` in `sklayoutref/chap2.html` |

Application names used by the docs: "Layout XL" (env prefix `layoutXL`), "Layout GXL", "Virtuoso Layout Suite XL" (window banner). The docs do not give a `geOpen`-style `?application` argument. The only documented way to open a layout in XL from SKILL is `lxLaunchLayoutXL` (needs a schematic window; see §1). `geOpen` and `hiOpenWindow` do not appear in any of the three docs. Layout XL also reads the `maskLayoutDefaultApp` variable, but `vxlhelp/chap1.html` says the Open-with setting in the Application group box cannot be changed from it. NOT IN DOCS: a SKILL call that opens a layout cellview in XL without a window.

---

## 1. Opening a layout bound to the schematic

### 1a. GUI (documented)
1. CIW: File - Open, library `divider_lib`, cell `DLATCH`, view `schematic`. [vxlhelp/chap1.html: 'Starting Layout XL with an Automatic Physical Configuration View', step 1-2]
2. In the schematic window: Launch - Layout XL. The Startup Option form appears. [same section, step 3]
3. Layout group: choose "create new layout" (name it, e.g. `layout_lxl`, default view name is `layout`) or "open existing". Configuration group: choose **Automatic**, then OK. [same section, steps 4-5]
4. The schematic is reopened in the context of an automatic physical configuration view (`physConfig` or `physConfig_<schName>`). [same section, notes after step 5]

Note: `vxlhelp/chap1.html` says Automatic mode is the right choice unless you need the Configure Physical Hierarchy features.

Alternative start points: layout window - Launch - Layout XL [vxlhelp/chap1.html: 'Starting Layout XL from a Layout View']; physConfig view - File - Open [vxlhelp/chap1.html: 'Starting Layout XL from a Physical Configuration View'].

### 1b. SKILL (documented)
- `lxLaunchLayoutXL([ w_windowID ])=> t`: "Launches Layout XL from a specified schematic window ... only if it is a schematic window." [sklayoutref/chap2.html: 'lxLaunchLayoutXL']. This needs a GUI schematic window.
- Batch / no-window route: `lxGenFromSource( d_schCellViewID ... )` takes a database ID, not a window. [sklayoutref/chap2.html: 'lxGenFromSource']. The example opens the schematic with `schCV=dbOpenCellViewByType( schLibName schCellName schViewName )` and then calls `lxGenFromSource( schCV ?layViewName "layoutNew")`, followed by an explicit `dbSave` [sklayoutref/chap2.html: 'lxGenFromSource', Examples]. The docs give no batch example that opens a window.
- `lxSetConnRef(t_layLib t_layCell t_layView t_sourceType { CELLVIEW | NONE }[ ?schLib ][ ?schCell ][ ?schView ])` sets the connectivity reference for a layout that does not have one. [sklayoutref/chap2.html: 'lxSetConnRef']

### 1c. Batch / replay
NOT IN DOCS: `virtuoso -nograph -replay`, `-log` and how they interact with Layout XL. The IC615 copies in `/home/parshu/vm/cdsdocs/ic615_doc/` contain no `-nograph` or `-replay` text (grep of all HTML). Treat the command line as UNVERIFIED. Run the script once from the CIW with `load("...lxl_flow.il")` first.

---

## 2. Generate All From Source: options and the call

### 2a. GUI
Connectivity - Generate - All From Source. [vxlhelp/chap6.html: 'Generating All Components from Source']
- Generate Layout form, Generate tab: Instances, I/O Pins, PR Boundary; Chaining; Folding; Chain Folds; Except Global Pins; Except Pad Pins; Snap Boundary; Preserve User-Defined Mappings; Extract Connectivity After Generation. [vxlhelp/chap6.html: 'Specifying the Components to be Generated']; form layout in [vxlhelp/appD.html: 'Generate Layout']
- I/O Pins tab: pin layer, height, width, multiplicity, Create checkbox, Create Label As. [vxlhelp/chap6.html: 'Specifying the I/O Pins to be Generated', 'Specifying Default Values for All Pins', 'Creating Pin Labels']
- PR Boundary tab: Rectangle (origin) or Polygon (points). [vxlhelp/chap6.html: 'Specifying the Place and Route Boundary']
- Floorplan tab: preserve floorplanning objects. [vxlhelp/chap6.html: 'Preserving Floorplanning Objects']
- Warning: Generate All From Source "deletes any existing components in the layout view and generates everything from scratch." [vxlhelp/chap6.html: 'Generating All Components from Source']. **So never point it at the existing `divider_lib/DLATCH/layout`. Use a new view name.**
- Result: instances and pins are placed below the PR boundary in the same relative positions as in the schematic, unless `lxGenerateInBoundary` is set. [vxlhelp/chap6.html: 'Generating All Components from Source']
- Generated layout instances are named `instName.n` for mfactor devices, `instName|...` for hierarchy. [vxlhelp/chap6.html: 'Mfactored Devices and Folded Devices']

### 2b. SKILL, one call (documented)
`lxGenFromSource(d_schCellViewID[ ?layLibName t ][ ?layCellName t ][ ?layViewName t ][ ?configLib t ][ ?configCell t ][ ?configView t ][ ?initCreateInstances {t|nil} ][ ?initDoStacking {t|nil} ][ ?initDoFolding {t|nil} ][ ?initCreatePins {t|nil} ][ ?initGlobalNetPins {t|nil} ][ ?initCreatePadPins {t|nil} ][ ?initCreateBoundary {t|nil} ][ ?initCreateSnapBoundary {t|nil} ][ ?lxPositionMinSep n ][ ?lxGenerateInBoundary {t|nil} ][ ?initCreateMTM {t|nil} ][ ?extractAfterGenerateAll {t|nil} ][ ?extractSchematic {t|nil} ][ ?ignoreSchematicCheck {t|nil} ][ ?initPrBoundaryShape t ][ ?initPrBoundaryOrigin l ][ ?initPrBoundaryPoints l ][ ?initAreaSource1 t ][ ?initAreaSource1Val n ][ ?initAreaSource2 t ][ ?initAreaSource2Val n ])=> dbCellViewID` [sklayoutref/chap2.html: 'lxGenFromSource']

Doc facts for these arguments:
- Omitted layout library/cell/view names: layout is created with the schematic's cell name. [sklayoutref/chap2.html: 'lxGenFromSource', Description]
- Omitted physConfig names: physConfig in the layout cell's library/cell, default configView `physConfig`. [same]. So a `physConfig` view is created in `divider_lib/DLATCH` (VERIFY: confirm the view name after the run).
- `?extractSchematic`: if the schematic must be extracted and this is not set, generation stops. [same]
- `?initPrBoundaryShape` valid values "rectangle" and "polygon"; `?initPrBoundaryOrigin` is required for rectangle. [same] (lxSetBoundaryOptions writes the value as "Rectangle" [sklayoutref/chap2.html: 'lxSetBoundaryOptions']; case is not important to the docs but use what the doc example uses. VERIFY.)
- `?initAreaSource*` defaults are Utilization 20 and AspectRatio 1. [same]
- The docs say "You must perform an explicit dbSave after you have generated the new layout cellview." [sklayoutref/chap2.html: 'lxGenFromSource', Examples]. `dbSave` itself is not documented in the three docs (example use only). VERIFY the signature.

### 2c. SKILL, step-by-step alternative (documented)
Sequence: `lxGenerateStart(d_schId d_layId [?extractSchematic t])` -> any of `lxSetGenerateOptions`, `lxSetBoundaryOptions`, `lxSetAreaEstimationOptions`, `lxSetNetPinSpecs`, `lxSetPreserveFloorplanningOptions` -> `lxGenerateFinish(d_schId d_layId [?extractSchematic t])`. [sklayoutref/chap2.html: 'lxGenerateStart', 'lxGenerateFinish', and the doc's list in vxlhelp/chap6.html: 'Generating a Layout from Source Using SKILL']
- `lxSetGenerateOptions([ ?instances ][ ?stacks ][ ?folds ][ ?chainFolds ][ ?pins ][ ?globalPins ][ ?padPins ][ ?boundary ][ ?snapBoundary ][ ?mtm ][ ?extract ][ ?posMinSep n ][ ?inBoundary ])=> t` [sklayoutref/chap2.html: 'lxSetGenerateOptions']. Note: the doc's printed signature has a stray bracket around `?pins`; use the argument names as printed.
- `lxSetBoundaryOptions([ ?shape t ][ ?origin g ][ ?points lg ])`; origin required for Rectangle. [sklayoutref/chap2.html: 'lxSetBoundaryOptions']
- `lxSetNetPinSpecs(?nets lt[ ?lpp lt ]?width n?height n[ ?numPins x][ ?create g])`. The pin layer-purpose is `list("layer" "purpose")`. [sklayoutref/chap2.html: 'lxSetNetPinSpecs']. Valid LPPs come from `lxGetAvailablePinLPPs()` and net names from `lxGetPinNets()`, both called between Start and Finish. [sklayoutref/chap2.html: 'lxGetAvailablePinLPPs', 'lxGetPinNets']
- `lxSetPreserveFloorplanningOptions([ ?preserve { all | none } ][ ?rows ][ ?blockages ][ ?areaBoundaries ][ ?trackPatterns ][ ?clusters ][ ?clusterBoundaries ])`. [sklayoutref/chap2.html: 'lxSetPreserveFloorplanningOptions']
- The docs say the SKILL path can be used "to run Generate All From Source", and list the functions above. [vxlhelp/chap6.html: 'Generating a Layout from Source Using SKILL']

### 2d. Environment variables that control generation (documented, layoutXL)
Set with `envSetVal("layoutXL" "<name>" '<type> <value>)`. [vxlhelp/chap1.html: 'Setting Environment Variables in the CIW', e.g. `envSetVal("layoutXL" "chainFolds" 'boolean t)`]
- `lxEvalCDFCallbacks` (boolean, default nil): evaluates CDF callbacks during Generate All From Source, Generate Selected From Source, Generate Folded Devices. [vxlhelp/appA.html: 'lxEvalCDFCallbacks']. **Needed for nmos1v** (see §3).
- `lxGenerateInBoundary` (boolean, default nil): generate inside the design boundary. [vxlhelp/appA.html: 'lxGenerateInBoundary']
- `lxPositionPinsOnBoundary` (boolean, default t): positions pins on the prBoundary for Generate All From Source with lxGenerateInBoundary = t, and for PAS. [vxlhelp/appA.html: 'lxPositionPinsOnBoundary']
- `mfactorSplit` (boolean, default t): place mfactored schematic devices as multiple layout devices. [vxlhelp/appA.html: 'mfactorSplit']
- `lxFingeringNames` (string, default "fingers finger numFingers numFinger"): names that define pcell gate fingering. [vxlhelp/appA.html: 'lxFingeringNames']
- `initIOPinLayer` (string "layer purpose"), `initPinWidth` (default 25.0), `initPinHeight`, `initPinMultiplicity`. [vxlhelp/appA.html: 'initIOPinLayer', 'initPinWidth']
- `createBoundaryLabel`: label of library, cell and view inside the top edge of the boundary. [vxlhelp/chap6.html: 'Specifying the Components to be Generated', step 5]
- `createImplicitBusTerminals`: needed before Generate All From Source for bus terminal/bit order. [vxlhelp/chap6.html: 'Generating All Components from Source']
- `lxSchematicDefaultApp`: whether the schematic opens in XL or L mode. [vxlhelp/chap1.html: 'Starting Layout XL from a Layout View']

---

## 3. Device mapping: schematic to layout

### 3a. How a schematic instance becomes a layout device (documented)
- Generate All From Source "copies all the schematic parameters to the new layout instance", with exceptions. The list includes "mfactor and sfactor" and `lxMFactorNum`, `lxParamsToIgnore`, `lxRounding`, etc. [vxlhelp/chap6.html: 'Generate All From Source and Schematic Parameters']
- Parameters can be ignored with `lxParamsToIgnore` or the Parameters tab of the Layout XL Options form. [same section, bullet 2]. The LAM file can do the same per cell with `<IGNORE><GEN>` and `<CHECK>`. [vxlhelp/appE.html: 'LAM File Mappings Section', statements `<IGNORE>`, `<GEN>`, `<CHECK>`]
- CDF callbacks run only with `lxEvalCDFCallbacks` = t, and the callback sees the complete parameter list including adjusted folding/sfactor/lxCombination values. [vxlhelp/chap6.html: 'Generate All From Source and Schematic Parameters'; vxlhelp/appA.html: 'lxEvalCDFCallbacks']
- Parameter name mapping: "Name mapping defines the mapping between parameter names in the schematic and layout cellviews; for example, `l L ; w W ;`". [vxlhelp/appD.html: 'Name mapping' (Parameters tab, Layout XL Options)]. LAM equivalent: `<MAP>l L ; w W ;</MAP>` under `<PARAMETERS>` [vxlhelp/appE.html: 'LAM File Mappings Section', `<MAP>` statement; example block]. Note the LAM statement is documented as "Name mapping (cell attributes only)".
- Rounding: `(w 0.05 round)` rounds a parameter value. [vxlhelp/appD.html: 'Rounding']; LAM `<ROUNDING>`. [vxlhelp/appE.html: example]

### 3b. nmos1v (schematic) to nmos1v (layout pcell)
Project facts (from `PDK_FACTS.md`, VERIFIED there from the PDK files, not from the IC615 docs):
- Schematic CDF: `w` (total width), `l`, `m`, `fingers`, `model`, plus the callback `gpdk045_mosCB( 'w )` and `gpdk045_mosCB( 'l )` that recomputes `fw`/`fingers`.
- Layout pcell params: `fw l fingers connectGates connectSD ...` (`fw` is finger width).

Mapping, as the docs support it:
1. **Width name.** Component type attribute "Width parameter" (default `w`) names the transistor width on the layout master; set it to `fw` for the layout cell. [vxlhelp/appD.html: 'Component Types Attributes', 'Width parameter']; LAM `<WIDTH>widthParamName</WIDTH>` [vxlhelp/appE.html: 'LAM File Component Type Section']. Alternatively map the name with `<MAP>w fw ;</MAP>` [vxlhelp/appE.html]. Pick one; do not do both without checking the result.
2. **Component class and terminals.** Component class NMOS, Active layer (ndiff), Folding threshold are required for chaining and folding. [vxlhelp/appD.html: 'Component Types Attributes'; vxlhelp/chap4.html: 'Component Types Mode'] Default terminal names D/G/S/B (drain/gate/source/bulk) apply. [vxlhelp/appD.html: 'Property/Value']
3. **Multiplier m.** Schematic param names for the parallel factor default to "m M". [vxlhelp/appD.html: 'Schematic Parameter Names', 'Parallel-connected factor']. Each m=4 device becomes instances `inst.1`..`inst.4` with `mfactorSplit` = t. [vxlhelp/chap6.html: 'Mfactored Devices and Folded Devices'; vxlhelp/appA.html: 'mfactorSplit']
   - **Width split is ambiguous in the docs.** `vxlhelp/appD.html` says the width "value must be split among the generated parallel-connected devices ... such that number of mfactored instances * mfactorSplit value = source parameter value". Whether each generated instance gets `w/4` or the full `w` is not stated clearly. The script does not print instance parameter values (no documented accessor for them in these copies); read `fw`/`fingers`/`l` of one generated instance in the GUI (Property Editor) and compare with the schematic before trusting the result. Do not assume.
4. **Fingers.** `fingers` is already a pcell fingering name by default (`lxFingeringNames`), so with `fingers=1` nothing needs mapping. [vxlhelp/appA.html: 'lxFingeringNames'] Folding/chaining is a separate option and is off in the script.
5. **CDF callbacks.** Required so that `w` and `fw`/`fingers` are computed the same way as in the PDK CDF. `lxEvalCDFCallbacks` = t. [vxlhelp/appA.html: 'lxEvalCDFCallbacks']

### 3c. analogLib `res` (schematic) to resnsnpoly (layout pcell)
What the docs give:
- Physical-cell override per cell in CPH: Configure Physical Hierarchy - Cells tab - double-click "Physical Cell" and "Physical View". Saved with File - Save. [vxlhelp/chap4.html: 'Specifying the Mapping for a Cell']
- Per instance override: CPH - Instances tab - "Physical Cell" column, with Occurrence mode if one occurrence only. [vxlhelp/chap4.html: 'Specifying the Mapping for an Instance or Occurrence']. This is the least intrusive route here because `analogLib/res` is outside `divider_lib`.
- Cell-level LAM: a physical cell maps to a logical cell with `<LOGICAL_CELL>` and `<VIEW NAME="symbol" />`, as in the LAM example. [vxlhelp/appE.html: 'LAM File Mappings Section', example]. Editing the LAM for the gpdk045 library is not something the docs suggest; a `library.lam` override is found through `setup.loc`. [vxlhelp/appE.html: 'LAM File Locations']
- Resistance parameter names: `r R` by default. [vxlhelp/appD.html: 'Schematic Parameter Names', 'Resistance'] The docs say the resistance value "must be split among generated series-connected devices" (this is for sfactor/lxCombination). [same]
- `lxCombination` builds series/parallel networks of the same device from a formula, and ignores `r` when set. [vxlhelp/appC.html: 'lxCombination']. It does **not** convert `r` into `segW`/`segL` of a poly pcell.

NOT IN DOCS: any rule that converts `r=3k` into `resnsnpoly` `segW`, `segL`, `segments`. Sizing must be done by setting the pcell parameters directly, or by the project's own sizing formula (`R = rsh*L/W + 2*rend0/W`, in `build_layout_v2.il` and `LAYOUT_NOTES.md`). Whether `r` is copied into the pcell at generation time and fails is not stated; the script ignores `r` through a `;; VERIFY` option, and prints the instance list.

Note: the `resnsnpoly` layout pcell params are `segW segL connection segments ...` (project `LAYOUT_NOTES.md`). The docs have no list for them.

### 3d. Device correspondence
- Generate All From Source with "Preserve User-Defined Mappings" (`?initCreateMTM`) keeps user-defined one-to-one, many-to-many, many-to-one and one-to-many device correspondence. It does not report missing devices. [vxlhelp/chap6.html: 'Specifying the Components to be Generated', step 3; sklayoutref/chap2.html: 'lxGenFromSource', ?initCreateMTM]
- Define Device Correspondence form: Connectivity - Define Device Correspondence. [vxlhelp/chap10.html: 'Updating Device Correspondence']
- SKILL: `lxHiDefineDeviceCorr()` (GUI) and `bndAddInstsBindingByName`, `bndSetInstsBindingByName`, `bndGetBoundObjects` and others. [vxlhelp/chap10.html: 'Define Device Correspondence SKILL API']; `lxHiDefineDeviceCorr` in [sklayoutref/chap2.html]. These binding functions are listed in the chap10 doc but are not fully documented in the three copies. NOT IN DOCS in full detail.

### 3e. Iterated instances and bus pins
Iterated instance `K<0:1>` can map to several layout instances; bus pins `SEL<0:1>` map to `SEL<0>`, `SEL<1>`. [vxlhelp/chap3.html: 'One-to-Many Mapping']. Not used for DLATCH.

---

## 4. Placement

### 4a. Place As In Schematic (PAS)
- GUI: Connectivity - Generate - Place As In Schematic. Moves generated components and pins inside the design boundary, keeping relative positions. Unbound instances/pins go below the boundary. Layout XL does not compact the layout; DRC is not guaranteed. Constraints are not honored; a message points to the Analog Auto Placer. [vxlhelp/chap7.html: 'Moving Generated Components into the Design Boundary']; [vxlhelp/chap6.html: 'Generating All Components from Source' is the other entry point]
- SKILL: `lxHiMoveAutomatically()=> t | nil` "Runs the Place As In Schematic command". [sklayoutref/chap2.html: 'lxHiMoveAutomatically']. This is a window command: it needs the current layout window. NOT usable from `-replay` batch as documented.

### 4b. Automatic placement (Custom Digital Placer)
- GUI: Place - Custom Digital - Placer, "Runs the automatic placer", opens the Auto Placer form. [vxlhelp/appB.html: 'Command Quick Reference', Place Menu]
- SKILL, form: `lxHiAutoPlace([ d_cellViewID ])=> t | nil` "Opens the Auto Placer form ... Virtuoso Custom Digital Placer". [sklayoutref/chap6.html: 'lxHiAutoPlace']
- SKILL, no form: `vcpfeRunCustomDigitalPlacer(d_schCvID d_layCvID [ ?globalPlacement {t|nil} ][ ?optimizePlacement {t|nil} ][ ?runTime {quick|moderate|optimized} ][ ?groupCMOSPairs ][ ?preserveChains ][ ?groupMFactors ][ ?allowRotation ][ ?minDisturbancePlacement ][ ?ecoMode ][ ?saveAs ][ ?saveAsLibName ][ ?saveAsCellName ][ ?saveAsViewName ][ ?overwrite ][ ?intraRowSpacer ][ ?interRowSpacer ][ ?adjustBdy ][ ?reserveTracksForRouting ][ ?vcpRulesConstraintGroup ][ ?minBoundaryOffset ][ ?maxPinsPerNet ][ ?mixedMode ][ ?placeCluster ][ ?componentEdge ])=> t` [sklayoutref/chap6.html: 'vcpfeRunCustomDigitalPlacer']. Each argument has an env-var default. `?globalPlacement t` is the doc's advice for the first placement of a design. [same]
- Placement planning (rows): Place - Custom Digital - Placement Planning. [vxlhelp/appB.html]; SKILL `lxEditPlacementStyle()=> t` [sklayoutref/chap6.html]. The `lxPlc*PlaceSetupField*` functions read/write fields of that form. [sklayoutref/chap6.html]
- Component class PMOS/NMOS/STDCELL and the Active layer drive row generation. [vxlhelp/appD.html: 'Component Types Attributes']
- Placer environment: `vcpCellBoundaryLPPs` has no argument but is honored. [sklayoutref/chap6.html: 'vcpfeRunCustomDigitalPlacer', Arguments]
- Placement status: `lxUpdatePlacementStatus()=> t | nil` [sklayoutref/chap2.html]; Place - Update Placement Status [vxlhelp/chap6.html].
- Locking: `lxSelectedLock`, `lxHiLockSelected`, `lxFreezeInst`, `lxUnfreezeInst` exist as SKILL; the locked constraint "cannot be moved during interactive or automatic placement" [vxlhelp/chap7.html: 'Locking and Unlocking Devices'; sklayoutref/chap2.html for names].

Status: the placer is documented in the XL menu reference, but the GXL guide lists it as a token-licensed application. Whether a plain Layout XL license is enough is NOT STATED in the docs. Test first.

### 4c. Analog placer and Modgen (GXL)
- Analog placer SKILL: `nclAnalogAutoPlaceCB([ d_cellViewID ][ g_effortLevel ][ g_updatePRBoundary ])`, `nclAnalogQuickPlace([ d_cellViewID ])`. [sklayoutref/anaplace.html]. GXL, token license. Not used in the script.
- Modgen SKILL: `mgGen(d_cellViewID d_constraintID)=> d_modgenID`, and `mgRoute*`, `mgAddDummy*`, `mgAbutCB`. [sklayoutref/modgen.html]. GXL. Modgen is the documented way to build interdigitated or common-centroid matched arrays; the constraint ID comes from the Constraint Manager. Modgen is not used in the script.
- Analog placement in the XL GUI: Place - Analog menu points to "Virtuoso Analog Placer User Guide", which is not in the copies. [vxlhelp/appB.html]

---

## 5. I/O pin placement

- Pins are generated on the boundary when `lxGenerateInBoundary` = t and `lxPositionPinsOnBoundary` = t. [vxlhelp/appA.html: 'lxPositionPinsOnBoundary'; vxlhelp/chap6.html: 'Generating All Components from Source']
- To move I/O pins to the edges of the boundary: Place - Pin Placement (points to the Placer guide). [vxlhelp/chap7.html: 'Moving Generated Components into the Design Boundary'; vxlhelp/appB.html: 'Pin Placement']
- SKILL: `lxEditPinPlacement([ g_fromLayoutGenFormP ])=> t` opens the Pin Placement form; it can constrain a pin to an edge, order and fix pins, set the pitch, and start pin placement. [sklayoutref/chap6.html: 'lxEditPinPlacement']
- SKILL, move ports: `lxMovePorts(d_cellViewID)=> t`: "Moves top-level ports over components based on their connectivity." [sklayoutref/chap6.html: 'lxMovePorts']. This is the only documented non-GUI pin move in XL.
- Pin side (Left/Right/Top/Bottom) constraint: documented in the soft-pin context ("Define the side constraints using ... Side drop-down ... creates an alignment (side) constraint") [vxlhelp/chap7.html: 'Creating a Soft Pin']. NOT IN DOCS for flat pins in this copy.
- Pin layer: `initIOPinLayer` env var, or `lxSetNetPinSpecs ?lpp list("M1" "pin")`. [vxlhelp/appA.html: 'initIOPinLayer'; sklayoutref/chap2.html: 'lxSetNetPinSpecs']. The valid pin LPPs come from `lxGetAvailablePinLPPs()`. The layer names for this technology are not known from the docs; read them from the tech file.
- Ignoring pins: `unusedPin` property and `propsUsedToIgnoreObjs` env var. [vxlhelp/chap6.html: 'Ignoring Mismatched Pins']

---

## 6. Constraints

Documented:
- Schematic constraints transfer to layout at startup, at Generate All From Source, and by Update Layout Constraints (`lxHiUpdateLayoutConstraints()=> t`). [vxlhelp/chap6.html: 'Constraint Transfer'; sklayoutref/chap2.html: 'lxHiUpdateLayoutConstraints']
- Transferred constraints are read-only in the layout; you can add layout constraints to override. [vxlhelp/chap6.html: 'Constraint Manager Assistant']
- Constraint types and how they map from schematic to layout (one-to-many): symmetry pair `symmetry(A,B)` -> `symmetry(A.<N>,B.<N>)`; matched orientation `relOrient(A,B,"orient")` -> `relOrient(A.1,B.1,"orient")`; layout structure; SlayoutStructure; allOther. [vxlhelp/chap6.html: 'Constraint Mapping in One-to-Many Relationships']
- Cluster: `ciCon(cluster)` in the schematic becomes `oaCluster` in the layout, one-way synchronized. [vxlhelp/chap6.html: 'Creation and Synchronization of Clusters']
- For the differential pair (DLATCH M1/M2 style): create the symmetry (differential pair) and matched-orientation constraints in the **schematic** Constraint Manager, so the transfer maps them. The Constraint Manager docs are in the Unified Custom Constraints guide, which is NOT in the copies. Constraint-creation SKILL is NOT IN DOCS in the three copies. No constraint-creation call is in the script.
- Constraint Manager entry: Windows - Assistants - Constraint Manager. [vxlhelp/chap8.html: 'Creating and Editing Net Constraints']; Net Class and Net Priority are created there.
- Constraints are honored by the Custom Digital Placer, and Modgen; PAS ignores them. [vxlhelp/chap7.html: 'Moving Generated Components...' notes]

---

## 7. Check Against Source and Update Components And Nets

- Check: Connectivity - Check - Against Source. Reports missing/mismatched cellview masters, devices, top-level pins and global nets, mismatched terminals, unbound nets, parameter mismatches, bus terminals. [vxlhelp/chap9.html: 'Check Against Source']. SKILL `lxHiVerifyDesign()=> t`. [sklayoutref/chap2.html: 'lxHiVerifyDesign'] (GUI).
- Batch-callable comparison: `lxRunCmdInVXL(d_layCV u_cmd g_cmdArgs [ d_schCV ])=> t | nil`, "Runs a user-supplied command in layout XL, with CPH and the Binder enabled, without opening the windows." [sklayoutref/chap2.html: 'lxRunCmdInVXL']. The doc example is `lxRunCmdInVXL(lcv 'ciLxComparisonReport list(?layoutCV lcv ?showReport nil ?useViewNames t ?useTimeStamp t))`. The arguments in the example use `?schCV` where the signature shows positional `d_schCV`. VERIFY. Also: "does not work with interactive editing, incremental binding, or incremental extraction."
- Update: Connectivity - Update - Components And Nets. [vxlhelp/chap10.html: 'Updating Components and Nets']. SKILL: `lxHiUpdateComponentsAndNets()=> t`, `lxUpdateComponentsAndNets(d_schCellViewID d_layCellViewID [...])` (the doc prints `lxUpdateComponentsAndNets(schCV layCV)` as an example), or the Start/Finish pair. [sklayoutref/chap2.html: 'lxUpdateComponentsAndNets', 'lxUpdateComponentsAndNetsStart']
- Update Layout Parameters (layout parameters to match schematic): Connectivity - Update - Layout Parameters; SKILL `lxHiUpdateLayoutParameters()=> t`. [vxlhelp/chap10.html: 'Updating Layout Parameters'; sklayoutref/chap2.html]. This is the documented way to re-sync parameters after a schematic change. The width-split rule (§3b) applies.
- Extract: Connectivity - Update - Extract Layout. [vxlhelp/chap8.html: 'Extracting a Top-Level Design']. `?extractAfterGenerateAll t` extracts after generation. [sklayoutref/chap2.html: 'lxGenFromSource']
- Layout connectivity source check: `lxGetLXInfo({ srcView | dstView | workingWinID }[ d_cellviewID ])`. [sklayoutref/chap2.html: 'lxGetLXInfo'] (example: `srcId=lxGetLXInfo("srcView" cvId)`). Used in the script to confirm the layout points at `divider_lib/DLATCH/schematic`.

---

## 8. Not available in IC615 6.1.5 docs, or GXL only

| Item | Status |
|---|---|
| `geOpen` / `hiOpenWindow` with `?application "Layout XL"` | NOT IN DOCS |
| Batch launch flags (`-nograph`, `-replay`) | NOT IN DOCS (no flag text in the copies) |
| Layout XL open of a layout without a window, as a documented SKILL call | NOT IN DOCS as such; `lxGenFromSource` takes a db ID and its example has no window |
| `dbOpenCellViewByType`, `dbSave`, `errset`, `progn`, `printf`, `foreach`, `car`, `~>` accessors | Core SKILL / DB API, not in the three copies. `dbOpenCellViewByType` appears in the examples. `dbSave` appears in one example only. `~>name` appears in examples. `~>instances` is not in the docs |
| Pin placement algorithm (Place - Pin Placement) | Documented only as the Placer guide (not in copies) |
| Automatic placement as a documented XL-only feature | Documented in the XL menu, but GXL lists the placer as token-licensed. Licensing NOT STATED |
| Analog placer, Modgen, Floorplanner | GXL (token), docs in SKILL refs (`anaplace.html`, `modgen.html`) only |
| Constraint creation SKILL and UI details | NOT IN DOCS (Unified Custom Constraints guide not copied) |
| Resistor `r` to `resnsnpoly` `segW`/`segL`/`segments` conversion | NOT IN DOCS |
| Width split for mfactored devices, exact rule | Ambiguous in `vxlhelp/appD.html` (Schematic Parameter Names, Transistor); verify by check |
| Pin side constraint for flat (non-soft) pins | Documented for soft pins only |
| Layer names for pins in this technology | NOT IN DOCS; read the tech file |

---

## 9. Run order and verification (what the script does)

1. Set env vars (`lxEvalCDFCallbacks`, `lxGenerateInBoundary`, `mfactorSplit`). §2d.
2. Open `divider_lib/DLATCH/schematic` with `dbOpenCellViewByType`. §1b.
3. `lxGenFromSource` into the NEW view `layout_lxl` (not `layout`). Boundary = rectangle origin (0 0); `lxGenerateInBoundary` t; extract after generation. §2b.
4. `dbSave` the new view. §2b.
5. Print the source check (`lxGetLXInfo`) and the instance names with master cell (step 6 prints names and masters only). §3b, §7.
6. Optional, flagged off by default: PAS (`lxHiMoveAutomatically`, GUI only), placer (`vcpfeRunCustomDigitalPlacer`, GXL), `lxMovePorts`. §4, §5.
7. Optional: `lxRunCmdInVXL` comparison report. §7.
8. Save, print the summary.

Each step prints `LXL step N ok: <what>` or `LXL step N failed: <what> (read the CIW error above)`. The failure line does not carry the error text itself: the script takes the `errset` result and does not capture the message. Read the CIW error printed just above it. Pass `t` as the second argument to `errset` to make the CIW print the error (VERIFY the `errset` flag and return shape against core SKILL; not in these docs).

Known things to inspect after a run:
- Instance count and names (`DLATCH` has M1..M7 nmos1v and R1, R2 analogLib res, per `NOTES_v2.md`). Expect `M1.1..M1.4` if `m` splits.
- R1 and R2: if the instance has no layout pcell mapping they are missing from the layout. Set the CPH per-instance mapping (§3c) before expecting them.
- `physConfig` view created in `divider_lib/DLATCH` (§2b).
- Check Against Source report in the CIW / Info window (GUI).
