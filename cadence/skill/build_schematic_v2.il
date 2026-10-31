;;==============================================================================
;; build_schematic_v2.il
;;
;; Builds, in library divider_lib (v2 rewrite; does NOT depend on build_divider.il):
;;   1. DLATCH        schematic + symbol  (M1..M7 nmos1v, R1 R2 analogLib res, 9 pins)
;;   2. divider_core  schematic + symbol  (XD1..XD4 = DLATCH symbol, 2x2 ring)
;;   3. tb_divider    schematic           (divider_core, vdc, vpulse CK/CKb, 8 caps, gnd)
;;
;; Connectivity is copied from spectre/divider_gpdk45.scs. Bulk of every NMOS = VSS.
;; Nets connect BY NAME: every terminal gets a short stub wire with a net label.
;; All procedures use the prefix v2 so they cannot clash with build_divider.il.
;;
;; UNTESTED: written without access to Cadence. APIs that are not certain are
;; called inside errset and print WARNING / MANUAL lines. See NOTES_v2.md.
;;
;; RUN (CIW):
;;   load("/absolute/path/to/cadence/skill/build_schematic_v2.il")
;;   buildAll()
;;   showSchematic("DLATCH")      ; read-only window for a screenshot
;;==============================================================================


;;------------------------------------------------------------------------------
;; 1. TUNABLES
;;    defvar keeps the old value if the symbol is already bound in this CIW
;;    session. To change one now, type e.g.  resR = "8k"  in the CIW.
;;------------------------------------------------------------------------------
defvar(v2Lib      "divider_lib")   ; target library (must exist, see v2LibOk)
defvar(v2Pdk     "gpdk045")        ; PDK library, provides nmos1v
defvar(v2Ana     "analogLib")      ; res, cap, vdc, vpulse, gnd
defvar(v2Basic   "basic")          ; ipin, opin, iopin
defvar(v2Nmos    "nmos1v")         ; 1.1 V thin-oxide NMOS, terminals D G S B
defvar(v2Overwrite t)              ; t: delete and rebuild existing views. nil: skip them
defvar(resR      "2k")             ; R1, R2 value. NOTE: netlist uses rl=8k (see NOTES_v2.md)
defvar(capC      "10f")            ; load per output (netlist cl=10f)
defvar(wMain     "240n")           ; M1..M6 width  (netlist)
defvar(lMain     "45n")            ; M1..M6 length (netlist)
defvar(wTail     "480n")           ; M7 width      (netlist)
defvar(lTail     "90n")            ; M7 length     (netlist)
defvar(mult      1)                ; CDF m on every nmos (netlist: multi=mult)
defvar(tbVdd     1.0)              ; VDD voltage
defvar(tbVbias   0.8)              ; NBIAS voltage (tail current, tune it)
defvar(tbPeriod  1e-9)             ; CK period, seconds
defvar(tbRise    20e-12)           ; CK rise and fall time, seconds
defvar(stubLen   0.25)             ; stub wire length from each terminal (schematic units)
defvar(wireW     0.0625)           ; wire width
defvar(labelFont 0.0625)           ; net label font height
defvar(v2LabelForm nil)            ; filled at run time: which schCreateWireLabel form worked


;;------------------------------------------------------------------------------
;; 2. SMALL HELPERS
;;    SKILL note: infix math is kept out of argument lists (use let statements).
;;    Procedures in this section are used by everything below.
;;------------------------------------------------------------------------------

;; Formats a number as a string for a CDF value. Works for integers and floats.
procedure(v2Num(x)
  let((v2y)
    v2y = x * 1.0
    sprintf(nil "%g" v2y)))

;; Rounds a coordinate to the 0.0625 grid (used for stub END points only).
procedure(v2Snap(x)
  let((n r res)
    n = x * 16.0
    r = errset(fix(n + 0.5) t)
    res = if(r then car(r) / 16.0 else x)
    res))

;; Returns t if divider_lib exists. Otherwise prints the Library Manager steps.
procedure(v2LibOk()
  cond(
    (ddGetObj(v2Lib) t)
    (t
      printf("ERROR: library %s does not exist.\n" v2Lib)
      printf("  Create it by hand (this script does not create libraries):\n")
      printf("    Library Manager > File > New > Library...\n")
      printf("    Name: %s\n" v2Lib)
      printf("    Choose: Attach to an existing technology library, then select gpdk045.\n")
      printf("  Then run buildAll() again.\n")
      nil)))

;; Technology attach is NOT done by this script (not certain of the API).
;; Prints a note only.
procedure(v2TechNote()
  printf("NOTE: no techfile is attached by this script. divider_lib must already be\n")
  printf("      attached to gpdk045 (Library Manager > right-click lib > Properties).\n"))

;; Checks that the PDK and analogLib/basic libraries are visible.
procedure(v2CheckPdk()
  let((ok)
    ok = t
    foreach(lb list(v2Pdk v2Ana v2Basic)
      cond(
        (ddGetObj(lb) printf("  OK      library %s\n" lb))
        (t
          printf("  MISSING library %s  (check cds.lib DEFINE and the CIW library path)\n" lb)
          setq(ok nil))))
    ok))

;; Prints the terminal names of one symbol, so a wrong name is easy to fix.
procedure(v2PrintTerms(label spec)
  let((m)
    m = car(errset(dbOpenCellViewByType(car(spec) cadr(spec) "symbol" "schematicSymbol" "r") t))
    cond(
      (m
        printf("  %s  %s/%s terminals:" label car(spec) cadr(spec))
        foreach(trm m~>terminals printf(" %s" trm~>name))
        printf("\n"))
      (t printf("  %s  %s/%s symbol NOT found\n" label car(spec) cadr(spec))))))

;; Prints terminal names of every master the build uses.
procedure(v2DiagTerms()
  printf("Terminal names of the masters (used by the connect step):\n")
  v2PrintTerms("nmos   " list(v2Pdk v2Nmos))
  v2PrintTerms("res    " list(v2Ana "res"))
  v2PrintTerms("cap    " list(v2Ana "cap"))
  v2PrintTerms("vdc    " list(v2Ana "vdc"))
  v2PrintTerms("vpulse " list(v2Ana "vpulse"))
  v2PrintTerms("gnd    " list(v2Ana "gnd"))
  v2PrintTerms("ipin   " list(v2Basic "ipin")))

;; Library and cell spec for a device kind.
procedure(v2Spec(kind)
  cond(
    ((equal kind "nmos")   list(v2Pdk v2Nmos))
    ((equal kind "res")    list(v2Ana "res"))
    ((equal kind "cap")    list(v2Ana "cap"))
    ((equal kind "vdc")    list(v2Ana "vdc"))
    ((equal kind "vpulse") list(v2Ana "vpulse"))
    ((equal kind "gnd")    list(v2Ana "gnd"))
    ((equal kind "latch")  list(v2Lib "DLATCH"))
    ((equal kind "core")   list(v2Lib "divider_core"))
    (t nil)))

;; Opens the symbol view of a device kind for reading. Returns nil on failure.
procedure(v2Master(kind)
  let((spec m)
    spec = v2Spec(kind)
    m = nil
    cond(
      (null(spec) printf("ERROR: unknown device kind %s\n" kind))
      (t
        setq(m car(errset(dbOpenCellViewByType(car(spec) cadr(spec) "symbol" "schematicSymbol" "r") t)))
        when(null(m) printf("ERROR: symbol %s/%s not found. Check the library is attached.\n" car(spec) cadr(spec)))))
    m))

;; Center of a bounding box ((x1 y1) (x2 y2)). Returns list(x y).
procedure(v2BoxCenter(bb)
  let((cx cy)
    cx = (car(car(bb)) + car(cadr(bb))) / 2.0
    cy = (cadr(car(bb)) + cadr(cadr(bb))) / 2.0
    list(cx cy)))

;; Center of a master's bounding box, in master coordinates.
procedure(v2MasterCenter(master)
  let((r)
    r = errset(v2BoxCenter(master~>bBox) t)
    if(r then car(r) else list(0.0 0.0))))

;; Center of the first figure of the first pin of a terminal.
procedure(v2TermBoxCenter(trm)
  let((pin1 fig bb)
    pin1 = car(trm~>pins)
    fig = car(pin1~>figs)
    bb = fig~>bBox
    v2BoxCenter(bb)))

;; Center of a named terminal, in master coordinates. nil if not found.
;; The name "@FIRST" means the first terminal of the master (used for analogLib gnd).
procedure(v2TermXY(master termName)
  let((found r tname)
    found = nil
    tname = if(equal(termName "@FIRST") then v2FirstTermName(master) else termName)
    foreach(trm master~>terminals
      when(equal(trm~>name tname) setq(found trm)))
    cond(
      (found
        setq(r errset(v2TermBoxCenter(found) t))
        if(r then car(r) else nil))
      (t
        printf("WARNING: terminal %s not found on %s. Real names are listed above (v2DiagTerms).\n"
               termName master~>cellName)
        nil))))

;; Name of the first terminal of a master, or nil.
procedure(v2FirstTermName(master)
  let((tl tt)
    tl = master~>terminals
    tt = car(tl)
    if(tt then tt~>name else nil)))

;; Wire from p1 to p2. Returns the wire object, or nil.
procedure(v2Wire(cv p1 p2)
  let((r w)
    r = errset(schCreateWire(cv "draw" "full" list(p1 p2) wireW wireW 0.0) t)
    w = car(r)
    if(listp(w) then car(w) else w)))

;; Net label on a wire end. Tries the 9-argument form first, then the 10-argument form.
;; RISK: the argument list is the one thing most likely to need a fix. The form that
;; worked is printed at the first success.
procedure(v2Label(cv wire pt netName)
  if(null(wire)
    then printf("WARNING: no wire to hang label %s on at %L\n" netName pt)
    else v2LabelTry(cv wire pt netName)))

;; Tries the 9-argument form, then the 10-argument form. Prints which one worked.
procedure(v2LabelTry(cv wire pt netName)
  let((r1 r2)
    setq(r1 errset(schCreateWireLabel(cv wire pt netName "lowerLeft" "R0" "stick" labelFont nil) t))
    if(car(r1)
      then v2LabelNote(9)
      else v2LabelTry10(cv wire pt netName))))

;; 10-argument form of schCreateWireLabel (fallback).
procedure(v2LabelTry10(cv wire pt netName)
  let((r2)
    setq(r2 errset(schCreateWireLabel(cv wire pt netName "lowerLeft" "R0" "stick" labelFont nil t) t))
    if(car(r2)
      then v2LabelNote(10)
      else printf("WARNING: label %s not created by the 9- or 10-arg form. RISK: schCreateWireLabel args.\n" netName))))

;; Prints the working label form once per session.
procedure(v2LabelNote(form)
  when(null(v2LabelForm)
    printf("  (schCreateWireLabel: the %d-argument form works here)\n" form)
    setq(v2LabelForm form)))

;; Pin symbol (ipin/opin/iopin) at (x y) with a stub wire and a net label.
;; dx, dy: direction of the stub, outward from the device block.
procedure(v2PinAt(cv x v2y netName direction dx dy)
  let((pm r wire x1 y1)
    pm = car(errset(dbOpenCellViewByType(v2Basic v2PinMaster(direction) "symbol" "schematicSymbol" "r") t))
    r = errset(schCreatePin(cv pm netName direction nil list(x v2y) "R0") t)
    if(null(car(r)) then
      printf("WARNING: pin %s not created. RISK: schCreatePin args, or basic/ipin symbol missing.\n" netName))
    x1 = x + dx
    y1 = v2y + dy
    wire = v2Wire(cv list(x v2y) list(x1 y1))
    v2Label(cv wire list(x1 y1) netName)))

;; Pin master name for a pin direction.
procedure(v2PinMaster(direction)
  cond(
    ((equal direction "input")  "ipin")
    ((equal direction "output") "opin")
    (t "iopin")))

;; Places an instance at (x y), orientation R0. Returns the instance or nil.
procedure(v2Inst(cv master instName x v2y)
  car(errset(schCreateInst(cv master instName list(x v2y) "R0") t)))

;; Sets one CDF parameter. If the parameter is type "int", the value is converted.
;; RISK: setting ->value does not run CDF callbacks. Check w/l/fingers in the
;; Properties form after the build.
procedure(v2SetParamRaw(inst pname pvalue)
  let((cdf prm ptype)
    cdf = cdfGetInstCDF(inst)
    prm = cdfFindParamByName(cdf pname)
    ptype = if(prm then car(errset(prm->type t)) else nil)
    if(prm then v2AssignParam(prm ptype pvalue))
    prm))

;; Writes the value into a CDF parameter, converting to integer for "int" params.
procedure(v2AssignParam(prm ptype pvalue)
  if(equal(ptype "int")
    then prm->value = atoi(pvalue)
    else prm->value = pvalue))

procedure(v2SetParam(inst pname pvalue)
  let((r)
    r = errset(v2SetParamRaw(inst pname pvalue) t)
    if(null(car(r)) then
      printf("WARNING: CDF %s not set on %s. Set it by hand in the Properties form (Q).\n"
             pname inst~>name))))

;; Connects one terminal of an instance to a net by name: stub wire + label.
;; The stub follows the dominant axis from the symbol center (Manhattan).
;; Only the stub END point is grid-snapped: snapping the attach point would detach the wire.
procedure(v2Connect(cv master inst termName netName)
  let((lp)
    lp = v2TermXY(master termName)
    if(lp
      then v2Stub(cv master inst lp netName)
      else printf("  (terminal %s not found: net %s NOT connected on %s)\n" termName netName inst~>name))))

;; Draws the stub and its label for one terminal (lp = terminal center in master coords).
procedure(v2Stub(cv master inst lp netName)
  let((ctr dx dy ix iy x0 y0 horiz negStub sgnX sgnY dxs dys x1 y1 wire)
    ctr = v2MasterCenter(master)
    dx = car(lp) - car(ctr)
    dy = cadr(lp) - cadr(ctr)
    ix = car(inst~>xy)
    iy = cadr(inst~>xy)
    x0 = ix + car(lp)
    y0 = iy + cadr(lp)
    horiz = abs(dx) > abs(dy)
    negStub = 0.0 - stubLen
    sgnX = if(dx > 0.0 then stubLen else negStub)
    sgnY = if(dy > 0.0 then stubLen else negStub)
    dxs = if(horiz then sgnX else 0.0)
    dys = if(horiz then 0.0 else sgnY)
    x1 = v2Snap(x0 + dxs)
    y1 = v2Snap(y0 + dys)
    wire = v2Wire(cv list(x0 y0) list(x1 y1))
    v2Label(cv wire list(x1 y1) netName)))

;; Places one instance from a row and connects its terminals and CDF parameters.
;; Row format: list(instName kind x y conns params)
;;   conns:  list(list(termName netName) ...)
;;   params: list(list(cdfName value) ...)
procedure(v2Place(cv row)
  let((name kind x v2y conns params master inst)
    name = nth(0 row)
    kind = nth(1 row)
    x = nth(2 row)
    v2y = nth(3 row)
    conns = nth(4 row)
    params = nth(5 row)
    master = v2Master(kind)
    inst = if(master then v2Inst(cv master name x v2y) else nil)
    if(inst then
      progn(
        ;; Parameters first: the PDK symbol is parametrized, so editing w/l rebuilds it. Wire afterwards,
        ;; using the instance's own (updated) master for the pin positions.
        foreach(p params v2SetParam(inst car(p) cadr(p)))
        setq(master if(inst~>master then inst~>master else master))
        foreach(c conns v2Connect(cv master inst car(c) cadr(c)))
        printf("  placed %s (%s) at %g %g\n" name kind x v2y))
      else printf("ERROR: could not place %s (%s)\n" name kind))))

;; Places every row of a list.
procedure(v2PlaceAll(cv rows)
  foreach(r rows v2Place(cv r)))

;; Places every pin of a list. Pin row: list(name direction x y dx dy)
procedure(v2PinAll(cv pins)
  foreach(p pins
    v2PinAt(cv nth(2 p) nth(3 p) car(p) cadr(p) nth(4 p) nth(5 p))))

;; Deletes an existing view (only when v2Overwrite is t). Returns t when the view
;; is free for writing, nil otherwise.
procedure(v2PrepareView(cellName viewName)
  let((obj)
    obj = ddGetObj(v2Lib cellName viewName)
    cond(
      (null(obj) t)
      (null(v2Overwrite)
        printf("SKIP: %s/%s/%s exists (v2Overwrite is nil).\n" v2Lib cellName viewName)
        nil)
      (t v2DeleteView(obj cellName viewName)))))

;; Deletes an existing view object. Returns t if the view is gone afterwards.
procedure(v2DeleteView(obj cellName viewName)
  let((r)
    setq(r errset(ddDeleteObj(obj) t))
    if(ddGetObj(v2Lib cellName viewName)
      then progn(
        printf("ERROR: could not delete %s/%s/%s. Close every window that shows it, then re-run.\n"
               v2Lib cellName viewName)
        nil)
      else t)))

;; Tests whether a view exists.
procedure(v2ViewExists(cellName viewName)
  if(ddGetObj(v2Lib cellName viewName) then t else nil))

;; Creates the symbol of a cell from its schematic, after the schematic is saved.
;; Attempt 1: schViewToView. Attempt 2: schSchemToPinList + schPinListToSymbol.
;; If both fail, prints the GUI step. RISK: argument order of both calls.
procedure(v2MakeSymbol(cellName)
  let((r)
    if(v2PrepareView(cellName "symbol")
      then v2MakeSymbolTry(cellName)
      else printf("  symbol %s/symbol kept (existing)\n" cellName))))

;; Two attempts at creating the symbol, then a check and a MANUAL line if both fail.
procedure(v2MakeSymbolTry(cellName)
  let((r)
    printf("  making symbol %s/symbol (attempt 1: schViewToView)\n" cellName)
    setq(r errset(schViewToView(v2Lib cellName v2Lib cellName "schematic" "symbol" "schSchemToPinList" "schPinListToSymbol") t))
    if(null(v2ViewExists(cellName "symbol"))
      then v2MakeSymbolAttempt2(cellName))
    if(v2ViewExists(cellName "symbol")
      then printf("  OK symbol %s/symbol\n" cellName)
      else printf("MANUAL: symbol of %s not created. GUI: open the schematic, Design > Create Cellview > From Cellview, then Save.\n" cellName))))

;; Attempt 2 of v2MakeSymbol: read the pin list, then build the symbol from it.
procedure(v2MakeSymbolAttempt2(cellName)
  let((cv pl r)
    printf("  making symbol %s/symbol (attempt 2: schPinListToSymbol)\n" cellName)
    cv = dbOpenCellViewByType(v2Lib cellName "schematic" "schematic" "r")
    setq(r errset(schSchemToPinList(cv) t))
    pl = car(r)
    if(pl
      then setq(r errset(schPinListToSymbol(v2Lib cellName "symbol" pl) t))
      else printf("  attempt 2: no pin list from %s\n" cellName)
    )
    dbClose(cv)))

;; Checks the schematic and saves it. The output is printed in the CIW.
procedure(v2Finish(cv cellName)
  let((r)
    r = errset(schCheck(cv) t)
    printf("schCheck %s: %L\n" cellName car(r))
    dbSave(cv)
    dbClose(cv)
    printf("Saved %s/%s/schematic\n" v2Lib cellName)))


;;------------------------------------------------------------------------------
;; 3. ROW TABLES (connectivity copied from spectre/divider_gpdk45.scs)
;;    nmos1v terminals: D G S B   (D = drain, G = gate, S = source, B = bulk)
;;    analogLib:        PLUS MINUS (res, cap, vdc, vpulse)
;;    gnd:              first terminal, resolved at run time ("@FIRST")
;;------------------------------------------------------------------------------

;; One NMOS. Netlist order: (drain gate source) ; bulk is always VSS.
procedure(v2NmosRow(name x v2y d g s w l)
  list(name "nmos" x v2y
       list(list("D" d) list("G" g) list("S" s) list("B" "VSS"))
       list(list("w" w) list("fw" w) list("fingers" "1") list("l" l) list("m" v2Num(mult)))))

;; One resistor (analogLib res): PLUS, MINUS, CDF r.
procedure(v2ResRow(name x v2y plusNet minusNet)
  list(name "res" x v2y
       list(list("PLUS" plusNet) list("MINUS" minusNet))
       list(list("r" resR))))

;; One capacitor (analogLib cap): PLUS, MINUS, CDF c.
procedure(v2CapRow(name x v2y net)
  list(name "cap" x v2y
       list(list("PLUS" net) list("MINUS" "gnd!"))
       list(list("c" capC))))

;; One DC source (analogLib vdc): PLUS, MINUS, CDF vdc.
procedure(v2DcRow(name x v2y net value)
  list(name "vdc" x v2y
       list(list("PLUS" net) list("MINUS" "gnd!"))
       list(list("vdc" v2Num(value)))))

;; One pulse source (analogLib vpulse). tdVal = delay (0 for CK, half period for CKb).
procedure(v2PulseRow(name x v2y net tdVal)
  let((pwVal)
    pwVal = tbPeriod / 2.0 - tbRise
    list(name "vpulse" x v2y
         list(list("PLUS" net) list("MINUS" "gnd!"))
         list(list("v1" "0")
              list("v2" v2Num(tbVdd))
              list("td" v2Num(tdVal))
              list("tr" v2Num(tbRise))
              list("tf" v2Num(tbRise))
              list("pw" v2Num(pwVal))
              list("per" v2Num(tbPeriod))))))

;; Ground symbol. Its terminal is resolved at run time (name "@FIRST").
procedure(v2GndRow(name x v2y)
  list(name "gnd" x v2y
       list(list("@FIRST" "gnd!"))
       nil))

;; One DLATCH instance in divider_core: pins D Db CK CKb Q Qb VDD VSS NBIAS.
procedure(v2CoreRow(name x v2y d db ck ckb q qb)
  list(name "latch" x v2y
       list(list("D" d) list("Db" db) list("CK" ck) list("CKb" ckb)
            list("Q" q) list("Qb" qb) list("VDD" "VDD") list("VSS" "VSS")
            list("NBIAS" "NBIAS"))
       nil))

;; DLATCH schematic instances. Sample pair top, M5 center, hold pair, M6, M7 at the bottom.
procedure(v2DlatchRows()
  list(
    v2ResRow("R1"  -2.5  7.0 "VDD" "Q")
    v2ResRow("R2"   2.5  7.0 "VDD" "Qb")
    v2NmosRow("M1" -2.5  4.0 "Q"   "D"    "xs"   wMain lMain)
    v2NmosRow("M2"  2.5  4.0 "Qb"  "Db"   "xs"   wMain lMain)
    v2NmosRow("M5"  0.0  1.0 "xs"  "CK"   "tail" wMain lMain)
    v2NmosRow("M3" -2.5 -1.5 "Q"   "Qb"   "xh"   wMain lMain)
    v2NmosRow("M4"  2.5 -1.5 "Qb"  "Q"    "xh"   wMain lMain)
    v2NmosRow("M6"  0.0 -3.5 "xh"  "CKb"  "tail" wMain lMain)
    v2NmosRow("M7"  0.0 -6.5 "tail" "NBIAS" "VSS" wTail lTail)))

;; DLATCH pins. Row: list(name direction x y dx dy). dx,dy = stub direction.
procedure(v2DlatchPins()
  list(
    list("D"     "input"       -6.0  4.0 -0.5  0.0)
    list("Db"    "input"       -6.0  3.0 -0.5  0.0)
    list("CK"    "input"       -6.0  1.0 -0.5  0.0)
    list("CKb"   "input"       -6.0 -3.5 -0.5  0.0)
    list("NBIAS" "input"       -6.0 -6.5 -0.5  0.0)
    list("Q"     "output"       6.0  5.0  0.5  0.0)
    list("Qb"    "output"       6.0  3.0  0.5  0.0)
    list("VDD"   "inputOutput"  0.0 10.0  0.0  0.5)
    list("VSS"   "inputOutput"  0.0 -10.0 0.0 -0.5)))

;; divider_core instances: ring floorplan. XD1 top-left, XD2 top-right,
;; XD3 bottom-right, XD4 bottom-left (clockwise). Connections from the netlist:
;;   XD1 (Q4b Q4 ck ckb Q1 Q1b)   XD2 (Q1b Q1 ckb ck Q2 Q2b)
;;   XD3 (Q2 Q2b ckb ck Q3 Q3b)   XD4 (Q3b Q3 ck ckb Q4 Q4b)
procedure(v2CoreRows()
  list(
    v2CoreRow("XD1" -6.0  6.0 "Q4b" "Q4"  "CK"  "CKb" "Q1" "Q1b")
    v2CoreRow("XD2"  6.0  6.0 "Q1b" "Q1"  "CKb" "CK"  "Q2" "Q2b")
    v2CoreRow("XD3"  6.0 -6.0 "Q2"  "Q2b" "CKb" "CK"  "Q3" "Q3b")
    v2CoreRow("XD4" -6.0 -6.0 "Q3b" "Q3"  "CK"  "CKb" "Q4" "Q4b")))

;; divider_core pins. Row: list(name direction x y dx dy)
procedure(v2CorePins()
  list(
    list("CK"    "input"       -16.0  2.0 -0.5  0.0)
    list("CKb"   "input"       -16.0  0.0 -0.5  0.0)
    list("NBIAS" "input"       -16.0 -2.0 -0.5  0.0)
    list("Q4"    "output"      -16.0  8.0 -0.5  0.0)
    list("Q4b"   "output"      -16.0  7.0 -0.5  0.0)
    list("Q3"    "output"      -16.0 -7.0 -0.5  0.0)
    list("Q3b"   "output"      -16.0 -8.0 -0.5  0.0)
    list("Q1"    "output"       16.0  8.0  0.5  0.0)
    list("Q1b"   "output"       16.0  7.0  0.5  0.0)
    list("Q2"    "output"       16.0 -7.0  0.5  0.0)
    list("Q2b"   "output"       16.0 -8.0  0.5  0.0)
    list("VDD"   "inputOutput"   0.0 16.0  0.0  0.5)
    list("VSS"   "inputOutput"   0.0 -16.0 0.0 -0.5)))

;; tb_divider: core connections. The core VSS goes to global ground "0".
procedure(v2TbCoreConns()
  list(list("CK" "CK") list("CKb" "CKb") list("NBIAS" "NBIAS")
       list("VDD" "VDD") list("VSS" "gnd!")
       list("Q1" "Q1") list("Q1b" "Q1b") list("Q2" "Q2") list("Q2b" "Q2b")
       list("Q3" "Q3") list("Q3b" "Q3b") list("Q4" "Q4") list("Q4b" "Q4b")))

;; tb_divider rows: sources, ground, core, 8 output loads.
procedure(v2TbRows()
  let((halfP)
    halfP = tbPeriod / 2.0
    list(
      v2DcRow("VDD"  -30.0 12.0 "VDD"   tbVdd)
      v2DcRow("VB"   -30.0  8.0 "NBIAS" tbVbias)
      v2PulseRow("VCK"  -30.0  4.0 "CK"  0.0)
      v2PulseRow("VCKB" -30.0 -4.0 "CKb" halfP)
      v2GndRow("GND" -30.0 -12.0)
      list("XCORE" "core" 0.0 0.0 v2TbCoreConns() nil)
      v2CapRow("CL1"   26.0 12.0 "Q1")
      v2CapRow("CL1b"  26.0  9.0 "Q1b")
      v2CapRow("CL2"   26.0  6.0 "Q2")
      v2CapRow("CL2b"  26.0  3.0 "Q2b")
      v2CapRow("CL3"   26.0  0.0 "Q3")
      v2CapRow("CL3b"  26.0 -3.0 "Q3b")
      v2CapRow("CL4"   26.0 -6.0 "Q4")
      v2CapRow("CL4b"  26.0 -9.0 "Q4b"))))


;;------------------------------------------------------------------------------
;; 4. CELL BUILDERS. Each returns t on success (or when skipped), nil on error.
;;------------------------------------------------------------------------------

;; [1/3] DLATCH schematic, then its symbol.
procedure(v2BuildDlatch()
  let((cv ok)
    ok = nil
    printf("\n[1/3] DLATCH schematic\n")
    if(v2PrepareView("DLATCH" "schematic") then
      progn(
        setq(cv dbOpenCellViewByType(v2Lib "DLATCH" "schematic" "schematic" "w"))
        when(cv
          v2PlaceAll(cv v2DlatchRows())
          v2PinAll(cv v2DlatchPins())
          v2Finish(cv "DLATCH")
          v2MakeSymbol("DLATCH")
          setq(ok t))
        when(null(cv) printf("ERROR: could not open DLATCH schematic for writing.\n"))))
    ok))

;; [2/3] divider_core schematic, then its symbol. Needs the DLATCH symbol.
procedure(v2BuildCore()
  let((cv ok)
    ok = nil
    printf("\n[2/3] divider_core schematic\n")
    cond(
      (null(v2ViewExists("DLATCH" "symbol"))
        printf("ERROR: DLATCH symbol is missing. Build DLATCH first (see NOTES_v2.md).\n"))
      (null(v2PrepareView("divider_core" "schematic")) nil)
      (t
        setq(cv dbOpenCellViewByType(v2Lib "divider_core" "schematic" "schematic" "w"))
        when(cv
          v2PlaceAll(cv v2CoreRows())
          v2PinAll(cv v2CorePins())
          v2Finish(cv "divider_core")
          v2MakeSymbol("divider_core")
          setq(ok t))
        when(null(cv) printf("ERROR: could not open divider_core schematic for writing.\n"))))
    ok))

;; [3/3] tb_divider schematic. Needs the divider_core symbol.
procedure(v2BuildTb()
  let((cv ok)
    ok = nil
    printf("\n[3/3] tb_divider schematic\n")
    cond(
      (null(v2ViewExists("divider_core" "symbol"))
        printf("ERROR: divider_core symbol is missing. Build divider_core first.\n"))
      (null(v2PrepareView("tb_divider" "schematic")) nil)
      (t
        setq(cv dbOpenCellViewByType(v2Lib "tb_divider" "schematic" "schematic" "w"))
        when(cv
          v2PlaceAll(cv v2TbRows())
          v2Finish(cv "tb_divider")
          setq(ok t))
        when(null(cv) printf("ERROR: could not open tb_divider schematic for writing.\n"))))
    ok))


;;------------------------------------------------------------------------------
;; 5. ENTRY POINTS
;;------------------------------------------------------------------------------

;; Runs all three builders in order. Read the CIW output: each step prints
;; OK / WARNING / ERROR / MANUAL lines.
procedure(buildAll()
  let((ok)
    printf("==== build_schematic_v2 ====\n")
    printf("Library %s | resR=%s | mult=%s | main W/L=%s/%s | tail W/L=%s/%s | overwrite=%L\n"
           v2Lib resR v2Num(mult) wMain lMain wTail lTail v2Overwrite)
    v2TechNote()
    ;; Warm up the PDK: its first use runs libInit.il, which assigns globals (it overwrote a variable named y).
    v2Master("nmos")
    printf("PDK / library check:\n")
    ok = if(v2LibOk() then v2CheckPdk() else nil)
    if(ok then v2DiagTerms())
    if(ok then setq(ok v2BuildDlatch()))
    if(ok then setq(ok v2BuildCore()))
    if(ok then setq(ok v2BuildTb()))
    if(ok
      then printf("==== DONE. Next: showSchematic(\"DLATCH\") (then divider_core, tb_divider) and screenshot.\n")
      else printf("==== STOPPED at the first ERROR above. Fix it, then re-run buildAll().\n"))
    ok))

;; Opens a cell's schematic read-only, for a screenshot.
procedure(showSchematic(cellName)
  let((w)
    w = car(errset(geOpen(?lib v2Lib ?cell cellName ?view "schematic" ?mode "r") t))
    if(w
      then printf("Opened %s/%s/schematic read-only. Press f (Fit) in the window, then screenshot.\n" v2Lib cellName)
      else printf("WARNING: geOpen failed for %s. Double-click it in the Library Manager instead.\n" cellName))))
