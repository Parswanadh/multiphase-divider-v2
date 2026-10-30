;;==============================================================================
;; build_divider.il
;;
;; Builds the schematics of the 8-phase divide-by-2 divider in Cadence Virtuoso:
;;   DLATCH        (one latch: 6 MOSFETs + 1 tail MOSFET + 2 resistors)
;;   divider_core  (4 DLATCH instances, interconnected)
;;   tb_divider    (testbench: core + sources + 10 fF output loads)
;;
;; UNTESTED: written without access to Cadence. The first run may need small
;; fixes. Every call marked VERIFY must be checked against your release's
;; "Schematic Editor SKILL Functions Reference" and the "Virtuoso SKILL
;; Reference" (both are PDFs under your Cadence install directory).
;;
;; HOW TO RUN (in the CIW):
;;   load("/absolute/path/to/cadence/skill/build_divider.il")
;;   buildDivider()         ; step 1: DLATCH; step 2: divider_core if the symbol exists
;;   buildTestbench()       ; tb_divider (needs the divider_core SYMBOL)
;;
;; The script does NOT create the library divider_lib. It must already exist and
;; be attached to the gpdk045 technology library.
;;
;; Source of truth for connectivity and sizes:
;;   spectre/divider_gpdk45.scs  (bulk = VSS, sizes 240n/45n, 480n/90n, 8k, 10f)
;; The SPICE deck spice/divider_baseline_cal.cir differs (bulk tied to the source
;; node, 0.9u/0.18u sizes, 5k, 30f). This script does NOT follow it.
;;==============================================================================


;;------------------------------------------------------------------------------
;; 1. TUNABLES. Change values here, not in the code below.
;;    Each "VERIFY" line must be checked in YOUR PDK install.
;;    NOTE: defvar may keep an old value if the variable is already set in this
;;    CIW session. If an edit seems ignored, set it directly in the CIW, for
;;    example: divW1 = "240n"
;;------------------------------------------------------------------------------

defvar(divLib       "divider_lib")   ; library to write cells into (must already exist)
defvar(divPdkLib    "gpdk045")       ; VERIFY: library that contains the nmos1v device
defvar(divNmosCell  "nmos1v")        ; VERIFY: 1.0 V thin-oxide NMOS cell name in your PDK
defvar(divNmosView  "symbol")        ; VERIFY: symbol view name of nmos1v
defvar(divAnaLib    "analogLib")     ; ideal analog parts (res, cap, vdc, vpulse, gnd)
defvar(divBasicLib  "basic")         ; VERIFY: library with ipin/opin/iopin pin masters

defvar(divResCell   "res")           ; analogLib resistor (CDF parameter "r")
defvar(divResR      "8k")            ; matches rl=8k in the Spectre file
defvar(divW1        "240n")          ; M1,M2,M3,M4,M5,M6 width  (Spectre file)
defvar(divL1        "45n")           ; M1,M2,M3,M4,M5,M6 length (Spectre file)
defvar(divW7        "480n")          ; M7 tail current source width
defvar(divL7        "90n")           ; M7 tail current source length (long channel)

defvar(divCapCell   "cap")           ; analogLib capacitor (CDF parameter "c")
defvar(divCapC      "10f")           ; load per output, as in the Spectre file (cl=10f)

defvar(divStub      0.25)            ; length of the wire stub at each terminal (schematic units)
defvar(divWireW     0.0625)          ; wire width used for the stubs
defvar(divLabelFont 0.0625)          ; net label font height

;; testbench tunables (tb_divider)
;; 1.8 V / 1.2 V / 714.285 ps are the 180 nm calibration values (spice/divider_baseline_cal.cir).
;; FOR gpdk045 (spectre file): set tbVdd = 1.0, tbVbias = 0.8, tbPeriod = 1e-9.
;; Defaults are now the gpdk045 values. Do NOT use 1.8 V on the 1.0 V nmos1v devices.
defvar(tbName       "tb_divider")
defvar(tbVdd        1.0)             ; supply voltage (gpdk045 nmos1v is a 1.0 V device)
defvar(tbVbias      0.8)             ; NBIAS voltage: starting value, tune it (tail current)
defvar(tbPeriod     1e-9)            ; clock period in seconds: start at 1 GHz, then raise the frequency
defvar(tbRise       20e-12)          ; clock rise and fall time (same as the Spectre file)
defvar(tbCload      "10f")           ; load on each of the 8 outputs


;;------------------------------------------------------------------------------
;; 2. LOW-LEVEL HELPERS
;;    Every call that is not well known sits here, so a fix needs one edit.
;;    SKILL note: write infix math with explicit parentheses inside argument
;;    lists, for example list((x + 1.0) y), never list(x + 1.0 y).
;;------------------------------------------------------------------------------

;; Returns t if divider_lib exists. Prints a clear message if it does not.
procedure(divLibOk()
  if(ddGetObj(divLib) then
    t
  else
    progn(
      printf("ERROR: library %s does not exist. Create it and attach gpdk045 first.\n" divLib)
      nil)))

;; Returns t if a view of the given cell exists in divLib.
procedure(divViewExists(cellName viewName)
  if(ddGetObj(divLib cellName viewName) then t else nil))

;; Maps a pin direction to the basic-library pin master name. VERIFY these cell names.
procedure(divPinMasterName(direction)
  cond(
    ((equal direction "input")       "ipin")
    ((equal direction "output")      "opin")
    ((equal direction "inputOutput") "iopin")
    (t "ipin")))

;; Returns the center of the first pin figure of a master's terminal, in the
;; master's local coordinates. Returns nil if the terminal cannot be found.
;; VERIFY: cv~>terminals, t~>name, t~>pins, p~>figs, f~>bBox
procedure(divTermLocal(master termName)
  let((tm pin1 pf bb res)
    tm = nil
    res = nil
    foreach(t master~>terminals
      when(equal(t~>name termName) tm = t))
    if(tm then
      errset(progn(
        pin1 = car(tm~>pins)
        pf = car(pin1~>figs)
        bb = pf~>bBox
        res = list(((car(car(bb)) + car(cadr(bb))) / 2.0)
                   ((cadr(car(bb)) + cadr(cadr(bb))) / 2.0))
      ) t))
    if(res then
      res
    else
      progn(
        printf("WARNING: terminal %s not found on %s. List the real names with: master~>terminals~>name\n"
               termName master~>cellName)
        nil))))

;; Returns the center of a master's bounding box, in local coordinates.
;; VERIFY: master~>bBox
procedure(divSymCenter(master)
  let((bb)
    bb = master~>bBox
    list(((car(car(bb)) + car(cadr(bb))) / 2.0)
         ((cadr(car(bb)) + cadr(cadr(bb))) / 2.0))))

;; Draws one wire from p1 to p2. Returns the first wire object, or nil.
;; VERIFY: schCreateWire(cv mode route points width height angle). It returns a LIST of wires.
procedure(divWire(cv p1 p2)
  let((r res)
    r = errset(schCreateWire(cv "draw" "full" list(p1 p2) divWireW divWireW 0.0) t)
    res = car(r)
    if(listp(res) then car(res) else res)))

;; Puts a net label named netName at point pt, attached to the given wire.
;; VERIFY: schCreateWireLabel(cv wire point text justify orient font height overbar visible)
procedure(divLabel(cv wire pt netName)
  let((r)
    r = errset(schCreateWireLabel(cv wire pt netName "lowerLeft" "R0" "stick" divLabelFont nil t) t)
    if(null(r) then
      printf("WARNING: label %s failed at %L. Check schCreateWireLabel arguments.\n" netName pt))))

;; Places a schematic pin named netName at point (x y), with a short wire and label.
;; Inputs get their stub to the left and outputs to the right, away from the device block.
;; VERIFY: schCreatePin(cv pinMaster name direction nil point orient)
procedure(divPinAt(cv x y netName direction)
  let((master r sx px wire)
    master = dbOpenCellViewByType(divBasicLib divPinMasterName(direction) "symbol" "symbol" "r")
    r = errset(schCreatePin(cv master netName direction nil list(x y) "R0") t)
    if(null(r) then
      printf("WARNING: pin %s not created. Check schCreatePin arguments.\n" netName))
    sx = if(equal(direction "output") then 0.5 else -0.5)
    px = x + sx
    wire = divWire(cv list(x y) list(px y))
    divLabel(cv wire list(px y) netName)))

;; Places an instance of master named instName at (x y), orientation R0.
;; VERIFY: schCreateInst(cv master name origin orient). It returns the instance or nil.
procedure(divInst(cv master instName x y)
  let((r)
    r = errset(schCreateInst(cv master instName list(x y) "R0") t)
    car(r)))

;; Sets one CDF parameter (for example "w" or "r") on an instance.
;; Prints a warning on failure so the user can set the value by hand.
;; VERIFY: cdfGetInstCDF, cdfFindParamByName, setting ->value.
;; NOTE: setting ->value does NOT run CDF callbacks. Check W and L in the Properties form.
procedure(divSetParam(inst pname pvalue)
  let((r)
    r = errset(
      let((cdf prm)
        cdf = cdfGetInstCDF(inst)
        prm = cdfFindParamByName(cdf pname)
        if(prm then
          prm->value = pvalue
          t
        else
          nil))
      t)
    if(null(car(r)) then
      printf("WARNING: could not set %s=%s on %s. Set it by hand in the Properties form (Q).\n"
             pname pvalue inst~>name))))

;; Connects one instance terminal to a net by name.
;; Method: a short wire stub from the terminal, pointing away from the symbol
;; center, with a net label at its end. Labels with the same name are one net.
;; Assumes orientation R0 for every instance.
procedure(divConnect(cv master inst termName netName)
  let((lp ctr dx dy len ux uy ix iy p0 p1 wire)
    lp = divTermLocal(master termName)
    if(lp then
      ctr = divSymCenter(master)
      dx = car(lp) - car(ctr)
      dy = cadr(lp) - cadr(ctr)
      len = sqrt(dx*dx + dy*dy)
      if(len == 0.0 then
        ux = 0.0
        uy = 1.0
      else
        ux = dx / len
        uy = dy / len)
      ix = car(inst~>xy)
      iy = cadr(inst~>xy)
      p0 = list((ix + car(lp)) (iy + cadr(lp)))
      p1 = list((car(p0) + divStub*ux) (cadr(p0) + divStub*uy))
      wire = divWire(cv p0 p1)
      divLabel(cv wire p1 netName))))

;; Returns the master cellview for a device kind.
;; Kinds: "nmos", "res", "cap", "vdc", "vpulse", "gnd", "latch", "core".
procedure(divMaster(kind)
  let((info)
    info = cond(
      ((equal kind "nmos")   list(divPdkLib divNmosCell))
      ((equal kind "res")    list(divAnaLib divResCell))
      ((equal kind "cap")    list(divAnaLib divCapCell))
      ((equal kind "vdc")    list(divAnaLib "vdc"))
      ((equal kind "vpulse") list(divAnaLib "vpulse"))
      ((equal kind "gnd")    list(divAnaLib "gnd"))
      ((equal kind "latch")  list(divLib "DLATCH"))
      ((equal kind "core")   list(divLib "divider_core"))
      (t list(nil nil)))
    if(car(info) then
      dbOpenCellViewByType(car(info) cadr(info) "symbol" "symbol" "r")
    else
      progn(printf("ERROR: unknown device kind %s\n" kind) nil))))

;; Places one device from a table row, then connects terminals and sets parameters.
;; Row format: list(instName kind x y connections params)
;;   connections: list of list(termName netName)
;;   params:      list of list(cdfParamName value)
procedure(divPlaceDevice(cv row)
  let((name kind x y conns params master inst)
    name   = nth(0 row)
    kind   = nth(1 row)
    x      = nth(2 row)
    y      = nth(3 row)
    conns  = nth(4 row)
    params = nth(5 row)
    master = divMaster(kind)
    inst   = if(master then divInst(cv master name x y) else nil)
    if(inst then
      foreach(c conns divConnect(cv master inst car(c) cadr(c)))
      foreach(p params divSetParam(inst car(p) cadr(p)))
      printf("  placed %s (%s)\n" name kind)
    else
      printf("ERROR: could not place %s\n" name))))

;; Opens a NEW schematic cellview for writing. Skips it if it already exists,
;; so a re-run never duplicates instances. Delete the old cell first to rebuild.
procedure(divOpenNewSchematic(cellName)
  let((cv)
    cv = nil
    if(divLibOk() then
      if(divViewExists(cellName "schematic") then
        printf("SKIP: %s/%s schematic already exists. Delete it in the Library Manager to rebuild.\n"
               divLib cellName)
      else
        cv = dbOpenCellViewByType(divLib cellName "schematic" "schematic" "w")))
    cv))

;; Runs schCheck, prints its return value, then saves and closes the cellview.
;; Read the CIW output for errors and warnings. schCheck does not simulate anything.
procedure(divFinish(cv cellName)
  let((r)
    r = errset(schCheck(cv) t)
    printf("schCheck %s/%s returned: %L\n" divLib cellName r)
    dbSave(cv)
    dbClose(cv)
    printf("Saved %s/%s/schematic\n" divLib cellName)))

;; Tries to create the symbol of a cell from its schematic pins.
;; VERIFY: schSchemToPinList and schPinListToSymbol are NOT confirmed for this script.
;; If this fails, do it in the GUI: Design > Create Cellview > From Cellview,
;; save the symbol, then re-run the stage that stopped.
procedure(divMakeSymbol(cellName)
  let((r)
    printf("Trying to create the symbol of %s from its schematic...\n" cellName)
    r = errset(
      schPinListToSymbol(divLib cellName "symbol"
                         schSchemToPinList(divLib cellName "schematic"))
      t)
    if(null(car(r)) then
      progn(
        printf("MANUAL STEP: symbol for %s could not be created by the script.\n" cellName)
        printf("  GUI: Design > Create Cellview > From Cellview (schematic -> symbol), then save.\n")))))

;; Returns t if the symbol view of cellName exists.
procedure(divSymbolExists(cellName)
  divViewExists(cellName "symbol"))


;;------------------------------------------------------------------------------
;; 3. TABLES: connectivity copied from spectre/divider_gpdk45.scs
;;    Terminal names: nmos1v uses D G S B. res, cap, vdc, vpulse use PLUS MINUS.
;;    VERIFY terminal names against the real symbols.
;;------------------------------------------------------------------------------

;; Latch devices, following the Spectre subckt DLATCH.
;; Port order: D Db CK CKb Q Qb VDD VSS NBIAS.
;; Tail current source M7: gate on NBIAS, source and bulk on VSS.
procedure(divLatchDevices()
  let((pm pm7)
    pm  = list(list("w" divW1) list("l" divL1))
    pm7 = list(list("w" divW7) list("l" divL7))
    list(
      list("R1" "res"   0.0  4.0 list(list("PLUS" "VDD") list("MINUS" "Q"))  list(list("r" divResR)))
      list("R2" "res"   4.0  4.0 list(list("PLUS" "VDD") list("MINUS" "Qb")) list(list("r" divResR)))
      list("M1" "nmos"  0.0  0.0 list(list("D" "Q")    list("G" "D")     list("S" "xs")   list("B" "VSS")) pm)
      list("M2" "nmos"  4.0  0.0 list(list("D" "Qb")   list("G" "Db")    list("S" "xs")   list("B" "VSS")) pm)
      list("M5" "nmos"  8.0  0.0 list(list("D" "xs")   list("G" "CK")    list("S" "tail") list("B" "VSS")) pm)
      list("M3" "nmos"  0.0 -4.0 list(list("D" "Q")    list("G" "Qb")    list("S" "xh")   list("B" "VSS")) pm)
      list("M4" "nmos"  4.0 -4.0 list(list("D" "Qb")   list("G" "Q")     list("S" "xh")   list("B" "VSS")) pm)
      list("M6" "nmos"  8.0 -4.0 list(list("D" "xh")   list("G" "CKb")   list("S" "tail") list("B" "VSS")) pm)
      list("M7" "nmos"  4.0 -8.0 list(list("D" "tail") list("G" "NBIAS") list("S" "VSS")  list("B" "VSS")) pm7))))

;; DLATCH pins: list(netName direction x y). Inputs on the left, outputs on the right.
procedure(divLatchPins()
  list(
    list("D"     "input"       -4.0   0.0)
    list("Db"    "input"       -4.0  -2.0)
    list("CK"    "input"       -4.0  -6.0)
    list("CKb"   "input"       -4.0 -10.0)
    list("NBIAS" "input"       -4.0 -12.0)
    list("VDD"   "inputOutput" -4.0   8.0)
    list("VSS"   "inputOutput" -4.0 -16.0)
    list("Q"     "output"      12.0   6.0)
    list("Qb"    "output"      12.0   2.0)))

;; divider_core: four DLATCH instances. Wiring copied from the Spectre file:
;;   XD1 (Q4b Q4 ck  ckb Q1 Q1b vdd 0 nbias)
;;   XD2 (Q1b Q1 ckb ck  Q2 Q2b vdd 0 nbias)   <- CK and CKb SWAPPED
;;   XD3 (Q2  Q2b ckb ck Q3 Q3b vdd 0 nbias)   <- CK and CKb SWAPPED
;;   XD4 (Q3b Q3 ck  ckb Q4 Q4b vdd 0 nbias)
;; Each row's connections are list(terminal net). Terminals: D Db CK CKb Q Qb VDD VSS NBIAS.
procedure(divCoreDevices()
  list(
    list("XD1" "latch"  0.0   0.0 list(list("D" "Q4b") list("Db" "Q4")  list("CK" "CK")  list("CKb" "CKb") list("Q" "Q1") list("Qb" "Q1b") list("VDD" "VDD") list("VSS" "VSS") list("NBIAS" "NBIAS")) nil)
    list("XD2" "latch"  8.0   0.0 list(list("D" "Q1b") list("Db" "Q1")  list("CK" "CKb") list("CKb" "CK")  list("Q" "Q2") list("Qb" "Q2b") list("VDD" "VDD") list("VSS" "VSS") list("NBIAS" "NBIAS")) nil)
    list("XD3" "latch"  0.0  -8.0 list(list("D" "Q2")  list("Db" "Q2b") list("CK" "CKb") list("CKb" "CK")  list("Q" "Q3") list("Qb" "Q3b") list("VDD" "VDD") list("VSS" "VSS") list("NBIAS" "NBIAS")) nil)
    list("XD4" "latch"  8.0  -8.0 list(list("D" "Q3b") list("Db" "Q3")  list("CK" "CK")  list("CKb" "CKb") list("Q" "Q4") list("Qb" "Q4b") list("VDD" "VDD") list("VSS" "VSS") list("NBIAS" "NBIAS")) nil)))

;; divider_core pins: list(netName direction x y).
procedure(divCorePins()
  list(
    list("CK"    "input"       -4.0   2.0)
    list("CKb"   "input"       -4.0  -1.0)
    list("NBIAS" "input"       -4.0  -4.0)
    list("VDD"   "inputOutput" -4.0  -7.0)
    list("VSS"   "inputOutput" -4.0 -10.0)
    list("Q1"    "output"      14.0   6.0)
    list("Q1b"   "output"      14.0   4.0)
    list("Q2"    "output"      14.0   2.0)
    list("Q2b"   "output"      14.0   0.0)
    list("Q3"    "output"      14.0  -2.0)
    list("Q3b"   "output"      14.0  -4.0)
    list("Q4"    "output"      14.0  -6.0)
    list("Q4b"   "output"      14.0  -8.0)))


;;------------------------------------------------------------------------------
;; 4. BUILDERS
;;------------------------------------------------------------------------------

;; Step 1: builds the DLATCH schematic.
procedure(divBuildDLatch()
  let((cv)
    printf("Building DLATCH...\n")
    cv = divOpenNewSchematic("DLATCH")
    if(cv then
      foreach(row divLatchDevices() divPlaceDevice(cv row))
      foreach(p divLatchPins() divPinAt(cv nth(2 p) nth(3 p) nth(0 p) nth(1 p)))
      divFinish(cv "DLATCH"))
    cv))

;; Step 2: builds divider_core. Needs the DLATCH symbol.
procedure(divBuildCore()
  let((cv)
    cv = nil
    if(divSymbolExists("DLATCH") then
      progn(
        printf("Building divider_core...\n")
        cv = divOpenNewSchematic("divider_core")
        if(cv then
          foreach(row divCoreDevices() divPlaceDevice(cv row))
          foreach(p divCorePins() divPinAt(cv nth(2 p) nth(3 p) nth(0 p) nth(1 p)))
          divFinish(cv "divider_core")))
      else
        printf("STOP: DLATCH symbol not found. Create it (Design > Create Cellview > From Cellview), then run buildDividerCore().\n"))
    cv))

;; Runs the whole pipeline: DLATCH, then divider_core if the DLATCH symbol exists.
procedure(buildDivider()
  printf("=== buildDivider: step 1 (DLATCH) ===\n")
  divBuildDLatch()
  if(null(divSymbolExists("DLATCH")) then
    divMakeSymbol("DLATCH"))
  if(divSymbolExists("DLATCH") then
    progn(
      printf("=== buildDivider: step 2 (divider_core) ===\n")
      divBuildCore())
    printf("STOP after step 1: create the DLATCH symbol (GUI), then run buildDividerCore().\n"))
  t)

;; Re-runs only step 2. Use it after you make the DLATCH symbol by hand.
procedure(buildDividerCore()
  divBuildCore()
  t)

;; Builds tb_divider. Needs the divider_core SYMBOL.
;; Sources: VDD and NBIAS as vdc; CK and CKb as vpulse (CKb delayed by half a period);
;; 10 fF on each of the 8 outputs; ground through the analogLib gnd symbol on net "0".
procedure(buildTestbench()
  let((cv halfT outs i pwS)
    cv = nil
    if(divSymbolExists("divider_core") then
      progn(
        printf("Building %s...\n" tbName)
        cv = divOpenNewSchematic(tbName)
        if(cv then
          halfT = tbPeriod / 2.0
          pwS = sprintf(nil "%g" (halfT - tbRise))
          ;; Values are strings, because CDF parameters store text such as "1.8" or "5e-11".
          ;; VERIFY: vpulse CDF names (v1 v2 td tr tf pw per). They may differ: check the form.
          divPlaceDevice(cv list("XDIV" "core" 0.0 0.0
                                 list(list("CK" "CK") list("CKb" "CKb") list("NBIAS" "NBIAS")
                                      list("VDD" "VDD") list("VSS" "0")
                                      list("Q1" "Q1") list("Q1b" "Q1b") list("Q2" "Q2") list("Q2b" "Q2b")
                                      list("Q3" "Q3") list("Q3b" "Q3b") list("Q4" "Q4") list("Q4b" "Q4b"))
                                 nil))
          ;; Supply: vdc. VERIFY: vdc parameter name.
          divPlaceDevice(cv list("VDD_SRC" "vdc" -12.0 6.0
                                 list(list("PLUS" "VDD") list("MINUS" "0"))
                                 list(list("vdc" sprintf(nil "%g" tbVdd)))))
          ;; NBIAS bias: vdc.
          divPlaceDevice(cv list("VB_SRC" "vdc" -12.0 -2.0
                                 list(list("PLUS" "NBIAS") list("MINUS" "0"))
                                 list(list("vdc" sprintf(nil "%g" tbVbias)))))
          ;; CK: vpulse starting at 0 s.
          divPlaceDevice(cv list("VCK" "vpulse" -12.0 -10.0
                                 list(list("PLUS" "CK") list("MINUS" "0"))
                                 list(list("v1" "0") list("v2" sprintf(nil "%g" tbVdd))
                                      list("td" "0")
                                      list("tr" sprintf(nil "%g" tbRise))
                                      list("tf" sprintf(nil "%g" tbRise))
                                      list("pw" pwS)
                                      list("per" sprintf(nil "%g" tbPeriod)))))
          ;; CKb: the same pulse, delayed by half a period.
          divPlaceDevice(cv list("VCKB" "vpulse" -12.0 -18.0
                                 list(list("PLUS" "CKb") list("MINUS" "0"))
                                 list(list("v1" "0") list("v2" sprintf(nil "%g" tbVdd))
                                      list("td" sprintf(nil "%g" halfT))
                                      list("tr" sprintf(nil "%g" tbRise))
                                      list("tf" sprintf(nil "%g" tbRise))
                                      list("pw" pwS)
                                      list("per" sprintf(nil "%g" tbPeriod)))))
          ;; Ground symbol. VERIFY: its terminal name "gnd". It puts net "0" on the schematic.
          divPlaceDevice(cv list("GND0" "gnd" -12.0 -26.0
                                 list(list("gnd" "0")) nil))
          ;; 10 fF load on each output, stacked at x = 18.
          outs = list("Q1" "Q1b" "Q2" "Q2b" "Q3" "Q3b" "Q4" "Q4b")
          i = 0
          foreach(n outs
            divPlaceDevice(cv list(strcat("CL_" n) "cap" 18.0 (8.0 - 4.0*i)
                                   list(list("PLUS" n) list("MINUS" "0"))
                                   list(list("c" tbCload))))
            i = i + 1)
          divFinish(cv tbName)))
      else
        printf("STOP: divider_core symbol not found. Create it first, then run buildTestbench().\n"))
    cv))

printf("build_divider.il loaded. Run buildDivider(), then buildTestbench().\n")
