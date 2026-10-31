;; =========================================================================
;; build_layout_v2.il  -  gpdk045 layout for the divider: DLATCH + divider_core
;; FIRST VERSION, UNTESTED (written without Virtuoso / Assura access).
;; Load in CIW:  load("/abs/path/cadence/skill/build_layout_v2.il")
;; Run:          buildLayoutDLATCH()  then  buildDividerCore()  then  runDRC()
;; Tags:  [V]      = verified in a PDK file (line refs in LAYOUT_NOTES.md)
;;        [VERIFY] = SKILL API or behaviour not confirmed here
;; Units: the script probes the layout API once (divProbeScale). If a placed
;;        MOS bBox is about 0.5 wide it uses user units (um); if it is about
;;        1000 wide it uses dbu (divDbuPerUm). The probe result is printed.
;; Scope: pcells placed, pins/labels placed, top-level instances + net labels,
;;        clock length check. Intra-latch metal routing and vias are NOT drawn.
;;        Terminal boxes are printed (divDumpInst) for the next routing pass.
;; =========================================================================

;; ------------------------------ tunables ------------------------------
defvar(divLibName    "divider_lib")   ; [VERIFY] exists, attached to gpdk045 tech
defvar(divPdkLib     "gpdk045")       ; [V] cds.lib line 6
defvar(divMosCell    "nmos1v")        ; [V] gpdk045/nmos1v
defvar(divResCell    "resnsnpoly")    ; [V] gpdk045/resnsnpoly (deviation: see notes)
defvar(divViewType   "maskLayout")    ; [VERIFY] tf viewTypeUnits row maskLayout
defvar(divDbuPerUm   2000.0)          ; [V] tf viewTypeUnits maskLayout 2000 (used only if probe says dbu)
defvar(divGridUm     0.005)           ; [V] tf mfgGridResolution 0.005
defvar(divMosGap     0.5)             ; um between MOS pcells in a row
defvar(divTopGap     1.0)             ; um between DLATCH instances in divider_core
defvar(divPinW       0.20)            ; um pin width  (0.20x0.15 = 0.03 um2 >= METAL1.A.1 0.02)
defvar(divPinH       0.15)

;; MOS sizing. Layout pcell params are fw (per finger), l, fingers [V] (nmos1v/layout/layout.oa)
defvar(divFw         "120n")          ; [V] CDF default finger width
defvar(divL1         "45n")           ; M1-M6 length
defvar(divL7         "90n")           ; M7 length
defvar(divNf1        2)               ; M1-M6: 2 fingers x 120n = W 240n
defvar(divNf7        4)               ; M7: 4 fingers x 120n = W 480n

;; Poly resistor sizing, resnsnpoly (no salicide). R = rsh*L/W + 2*rend0/W
defvar(divRTarget    2000.0)          ; ohm (user target; netlist uses 8k, see notes)
defvar(divRsh        200.0)           ; ohm/sq [V] gpdk045_resistor.scs tt_res r_resnsnpoly = 200
defvar(divRend0      1.44e-5)         ; ohm*m [V] tt_res r_rend_resnsnpoly = 1.44e-5
defvar(divResW      0.8)              ; um [V] POLYR.W.1.2 suggested min 0.8 (assuraDRC.rul line 108)

;; Session state (set by the builders; same CIW session needed for divider_core)
defvar(divScale     1.0)              ; API coordinate per um: 1.0 = user units, else dbu
defvar(divPinTable  nil)              ; list of (name x y), DLATCH-local um
defvar(divDlatchBox nil)              ; (0 0 x2 y2), DLATCH-local um

;; ------------------------------ units ---------------------------------
procedure(divSnapUm(um)
  fix(um / divGridUm + 0.5) * divGridUm
)

;; um -> coordinate for the layout API (float for user units, integer for dbu)
procedure(divC(um)
  if(divScale == 1.0
    then divSnapUm(um)
    else fix(divSnapUm(um) * divScale + 0.5))
)

;; API coordinate -> um
procedure(divToUm(v)
  v * 1.0 / divScale
)

;; Places one MOS at the origin, reads the raw bBox width, sets divScale.
;; width ~0.5 -> user units (1.0); width ~1000 -> dbu (divDbuPerUm). Deletes the probe.
procedure(divProbeScale(cv)
  let((tmp w)
    tmp = car(errset(dbCreateParamInst(cv
            car(errset(dbOpenCellViewByType(divPdkLib divMosCell "layout" nil "r") t))
            "TMPPROBE" list(0 0) "R0" 1
            car(divMosSets(divNf1 divL1))) t))
    if(tmp
      then
        w = car(cadr(tmp~>bBox)) - car(car(tmp~>bBox))
        if(w > 100
          then setq(divScale divDbuPerUm)
          else setq(divScale 1.0))
        printf("== units probe: raw MOS bBox width = %g -> divScale = %g (%s)\n"
          w divScale if(divScale == 1.0 then "user units, um" else "dbu"))
        errset(dbDeleteObject(tmp) t)
      else
        printf("== units probe FAILED (no MOS placed); divScale stays %g. Check the PDK attach.\n" divScale))
  )
)

;; ------------------------------ shapes --------------------------------
procedure(divRect(cv lpp x1 y1 x2 y2)
  dbCreateRect(cv lpp list(list(divC(x1) divC(y1)) list(divC(x2) divC(y2))))
)

procedure(divLabel(cv lpp x y txt)
  dbCreateLabel(cv lpp list(divC(x) divC(y)) txt "centerCenter" "R0" "stick" divC(0.1))
)

;; metal1 pin: pin shape + net + terminal + label. Each API call is errset-wrapped.
procedure(divPin(cv name x y dir)
  let((net term x2 y2 lx ly pf)
    x2 = x + divPinW
    y2 = y + divPinH
    lx = x + divPinW / 2.0
    ly = y + divPinH / 2.0
    net  = car(errset(dbCreateNet(cv name) t))
    term = car(errset(dbCreateTerm(net name dir) t))   ; [VERIFY] signature
    pf   = divRect(cv list("Metal1" "pin") x y x2 y2)
    unless(car(errset(dbCreatePin(net pf) t))
      printf("  VERIFY: dbCreatePin failed for %s (net/term/pin API)\n" name))
    divLabel(cv list("Metal1" "label") lx ly name)
    printf("  pin %s at (%g, %g) um\n" name x y)
    term
  )
)

;; ------------------------------ pcell placement -----------------------
;; Param sets, tried in order. Types are "string" first (CDF types), then int
;; for fingers, then a minimal set with only fw/l/fingers. Cyclic-type params are not used.
procedure(divMosSets(nf lStr)
  list(
    list(list("fw" "string" divFw)
         list("l" "string" lStr)
         list("fingers" "string" sprintf(nil "%d" nf))
         list("connectGates" "string" "Top")
         list("tap" "string" "Integrated"))
    list(list("fw" "string" divFw)
         list("l" "string" lStr)
         list("fingers" "int" nf)
         list("connectGates" "string" "Top")
         list("tap" "string" "Integrated"))
    list(list("fw" "string" divFw)
         list("l" "string" lStr)
         list("fingers" "string" sprintf(nil "%d" nf)))
  )
)

procedure(divResSets(lenU)
  list(
    list(list("segW" "string" sprintf(nil "%gu" divResW))
         list("segL" "string" sprintf(nil "%gu" lenU))
         list("segments" "int" 1))
    list(list("segW" "string" sprintf(nil "%gu" divResW))
         list("segL" "string" sprintf(nil "%gu" lenU))
         list("segments" "string" "1"))
    list(list("segW" "string" sprintf(nil "%gu" divResW))
         list("segL" "string" sprintf(nil "%gu" lenU)))
  )
)

procedure(divPlacePcell(cv libName cellName instName xU yU params)
  let((master inst)
    inst = nil
    master = car(errset(dbOpenCellViewByType(libName cellName "layout" nil "r") t))
    if(master
      then inst = car(errset(dbCreateParamInst(cv master instName list(divC(xU) divC(yU)) "R0" 1 params) t))
      else printf("ERROR: cannot open %s/%s/layout (is the PDK attached?)\n" libName cellName))
    if(inst
      then printf("  placed %s (%s) at (%g, %g) um\n" instName cellName xU yU)
      else printf("  FAILED %s (%s) with this param set\n" instName cellName))
    inst
  )
)

;; tries each param set until one places; returns the instance or nil
procedure(divPlaceTry(cv libName cellName instName xU yU paramSets)
  let((inst)
    inst = nil
    foreach(ps paramSets
      unless(inst
        inst = divPlacePcell(cv libName cellName instName xU yU ps)))
    inst
  )
)

procedure(divPlaceMos(cv name xU yU nf lStr)
  divPlaceTry(cv divPdkLib divMosCell name xU yU divMosSets(nf lStr))
)

;; right / top edge of an instance in um, with fallback when the instance is nil
procedure(divRightU(inst fallback)
  if(inst then divToUm(car(cadr(inst~>bBox))) else fallback)
)

procedure(divTopU(inst fallback)
  if(inst then divToUm(cadr(cadr(inst~>bBox))) else fallback)
)

;; max top edge over a list of instances (nil entries skipped)
procedure(divMaxTop(insts yDef)
  let((topv)
    topv = yDef
    foreach(i insts
      if(i then topv = max(topv divTopU(i yDef))))
    topv
  )
)

;; x where the next MOS starts: right edge + gap, or fallback when the instance is nil
procedure(divNextX(inst xFallback)
  let((rr)
    if(inst
      then rr = divRightU(inst 0.0) + divMosGap
      else rr = xFallback + 1.0)
    rr
  )
)

;; prints the terminal figures of an instance, in global um (x1 y1 x2 y2).
;; Uses the master's terminals, transformed by the instance transform.
procedure(divDumpInst(inst)
  when(inst
    printf("  terminals of %s (global um: x1 y1 x2 y2):\n" inst~>name)
    errset(
      foreach(t inst~>master~>terminals
        foreach(p t~>pins
          foreach(f p~>figs
            let((bb)
              bb = dbTransformBBox(f~>bBox inst~>transform)
              printf("    %s  %g %g %g %g\n" t~>name
                divToUm(car(car(bb))) divToUm(cadr(car(bb)))
                divToUm(car(cadr(bb))) divToUm(cadr(cadr(bb))))
            )
          )
        )
      )
    t)
  )
)

;; prints the CDF parameter names, types and defaults of a PDK cell (for the first run)
procedure(divPrintCdf(cellName)
  let((cdf)
    printf("== CDF of %s/%s (name type default):\n" divPdkLib cellName)
    cdf = car(errset(cdfGetBaseCellCDF(ddGetObj(divPdkLib cellName)) t))
    if(cdf
      then errset(
             foreach(p cdf~>parameters
               printf("   %L  %L  %L\n" p~>name p~>type p~>defValue))
             t)
      else printf("   (cdfGetBaseCellCDF returned nil; in CIW try: cdfGetBaseCellCDF(ddGetObj(\"%s\" \"%s\"))~>parameters)\n"
             divPdkLib cellName))
  )
)

;; poly resistor length (um) for the target R, snapped to the grid
procedure(divResLenUm()
  let((endOhm len)
    endOhm = 2.0 * divRend0 / (divResW * 1e-6)     ; two ends, ohm (= 36)
    len = (divRTarget - endOhm) * divResW / divRsh ; um (= 7.856)
    divSnapUm(len)                                 ; snapped (= 7.855)
  )
)

;; ------------------------------ DLATCH --------------------------------
procedure(divBuildDlatch(cv)
  let((yA topA yB topB yR1 topR1 yR2 topR2 yTop lenR x xM2 m1 m2 m3 m4 m5 m6 m7
       r1 r2 xR xR2 xRight xQ pD pDb boxX boxY)
    printf("== DLATCH: building\n")
    divProbeScale(cv)
    yA = 1.0                                  ; row A bottom (um)
    x = 1.0

    ;; row A, left to right: M1 M5 M7 M6 M2 (M7 between the clock devices M5/M6)
    m1 = divPlaceMos(cv "M1" x yA divNf1 divL1)
    x = divNextX(m1 x)
    m5 = divPlaceMos(cv "M5" x yA divNf1 divL1)
    x = divNextX(m5 x)
    m7 = divPlaceMos(cv "M7" x yA divNf7 divL7)
    x = divNextX(m7 x)
    m6 = divPlaceMos(cv "M6" x yA divNf1 divL1)
    x = divNextX(m6 x)
    xM2 = x
    m2 = divPlaceMos(cv "M2" xM2 yA divNf1 divL1)

    ;; row B above row A, placed from the real top of row A
    topA = divMaxTop(list(m1 m5 m7 m6 m2) yA)
    yB = topA + 0.5
    m3 = divPlaceMos(cv "M3" 1.0 yB divNf1 divL1)     ; above M1
    m4 = divPlaceMos(cv "M4" xM2 yB divNf1 divL1)     ; above M2

    ;; poly resistors, stacked from the real bBox of the previous one
    topB = divMaxTop(list(m3 m4) yB)
    yR1 = topB + 0.5
    lenR = divResLenUm()
    printf("  R len = %g um (W %g um, rsh %g, target %g ohm)\n" lenR divResW divRsh divRTarget)
    r1 = divPlaceTry(cv divPdkLib divResCell "R1" 1.0 yR1 divResSets(lenR))
    topR1 = divTopU(r1 yR1)
    yR2 = topR1 + 0.4
    r2 = divPlaceTry(cv divPdkLib divResCell "R2" 1.0 yR2 divResSets(lenR))
    topR2 = divTopU(r2 yR2)

    ;; cell extent from the placed shapes
    xRight = divRightU(m2 xM2)
    xR = divRightU(r1 0.0)
    xRight = max(xRight xR)
    xR2 = divRightU(r2 0.0)
    xRight = max(xRight xR2)
    xQ = xRight + 0.4
    yTop = topR2 + 0.4
    boxX = xRight + 0.6
    boxY = yTop + 0.4

    ;; terminal geometry for the routing pass (global um)
    printf("== DLATCH terminal figures (global um):\n")
    foreach(i list(m1 m5 m7 m6 m2 m3 m4 r1 r2) divDumpInst(i))

    ;; pins on the cell edges (not yet connected to devices)
    printf("== DLATCH pins (placed, NOT routed to devices yet)\n")
    pD = yA + 0.2
    pDb = yB + 0.2
    divPin(cv "CK"    1.0 0.2 "input")
    divPin(cv "CKb"   1.6 0.2 "input")
    divPin(cv "NBIAS" 2.2 0.2 "input")
    divPin(cv "VSS"   2.8 0.2 "inputOutput")
    divPin(cv "D"     0.1 pD  "input")
    divPin(cv "Db"    0.1 pDb "input")
    divPin(cv "Q"     xQ  pD  "output")
    divPin(cv "Qb"    xQ  pDb "output")
    divPin(cv "VDD"   1.0 yTop "inputOutput")

    setq(divPinTable
      list(list("CK" 1.0 0.2) list("CKb" 1.6 0.2) list("NBIAS" 2.2 0.2)
           list("VSS" 2.8 0.2) list("D" 0.1 pD) list("Db" 0.1 pDb)
           list("Q" xQ pD) list("Qb" xQ pDb) list("VDD" 1.0 yTop)))
    setq(divDlatchBox list(0.0 0.0 boxX boxY))
    printf("== DLATCH box (um): 0 0 %g %g\n" boxX boxY)
    errset(dbSave(cv) t)
    printf("== DLATCH saved\n")
  )
)

procedure(buildLayoutDLATCH()
  let((lib cv)
    printf("== build_layout_v2: DLATCH\n")
    divPrintCdf(divMosCell)
    divPrintCdf(divResCell)
    lib = ddGetObj(divLibName)
    cond(
      (not(lib)
        printf("ERROR: library %s not found. Create it attached to gpdk045 and rerun.\n" divLibName))
      (ddGetObj(divLibName "DLATCH" "layout")
        printf("SKIP: DLATCH/layout already exists. Delete it in the Library Manager to rebuild.\n"))
      (t
        cv = dbOpenCellViewByType(divLibName "DLATCH" "layout" divViewType "w")  ; [VERIFY] creates view
        if(cv
          then divBuildDlatch(cv)
          else printf("ERROR: could not create DLATCH/layout (see CIW error above)\n"))))
  )
)

;; ------------------------------ divider_core --------------------------
;; One entry per instance, in netlist order:
;;   name orient  D Db CK CKb Q Qb VDD VSS NBIAS   (spectre/divider_gpdk45.scs, XD1..XD4)
defvar(divXdNets
  list(
    list("XD1" "R0"   "Q4b" "Q4" "ck"  "ckb" "Q1"  "Q1b" "vdd" "vss" "nbias")
    list("XD2" "MY"   "Q1b" "Q1" "ckb" "ck"  "Q2"  "Q2b" "vdd" "vss" "nbias")
    list("XD3" "MX"   "Q2"  "Q2b" "ckb" "ck" "Q3"  "Q3b" "vdd" "vss" "nbias")
    list("XD4" "R180" "Q3b" "Q3" "ck"  "ckb" "Q4"  "Q4b" "vdd" "vss" "nbias")))

;; global point of a DLATCH-local point (px py) for orientation o placed at origin (ox oy)
procedure(divXform(o ox oy px py)
  let((gx gy)
    gx = ox + px
    gy = oy + py
    if(or(equal(o "MY") equal(o "R180")) then gx = ox - px)
    if(or(equal(o "MX") equal(o "R180")) then gy = oy - py)
    list(gx gy)
  )
)

;; net of pin pinName for an entry of divXdNets (entry = name orient nets...)
procedure(divNetOf(e pinName)
  let((pn nets)
    pn = list("D" "Db" "CK" "CKb" "Q" "Qb" "VDD" "VSS" "NBIAS")
    nets = cddr(e)
    cadr(assoc(pinName mapcar(lambda((p n) list(p n)) pn nets)))
  )
)

;; origin of a 2x2 slot: XD1 (0,0), XD2 (col 1), XD3 (row 1), XD4 (both)
procedure(divSlotOrigin(e W H G)
  let((col row ox oy)
    col = 0
    row = 0
    if(or(equal(car(e) "XD2") equal(car(e) "XD4")) then col = 1)
    if(or(equal(car(e) "XD3") equal(car(e) "XD4")) then row = 1)
    ox = 0.0
    oy = 0.0
    if(col == 1 then ox = 2.0 * W + G)
    if(row == 1 then oy = 2.0 * H + G)
    list(ox oy)
  )
)

procedure(buildDividerCore()
  let((cvT dlM bb W H G o ox oy inst gp net lenCk lenCkb cx cy pos dx dy pt)
    printf("== build_layout_v2: divider_core\n")
    cond(
      (not(divPinTable)
        printf("ERROR: divPinTable empty. Run buildLayoutDLATCH() first in this CIW session.\n"))
      (ddGetObj(divLibName "divider_core" "layout")
        printf("SKIP: divider_core/layout already exists.\n"))
      (t
        dlM = dbOpenCellViewByType(divLibName "DLATCH" "layout" divViewType "r")
        cvT = dbOpenCellViewByType(divLibName "divider_core" "layout" divViewType "w")  ; [VERIFY]
        if(not(and(dlM cvT))
          then printf("ERROR: could not open DLATCH master or create divider_core\n")
          else progn(
            divProbeScale(cvT)
            W = nth(2 divDlatchBox)
            H = nth(3 divDlatchBox)
            G = divTopGap
            printf("  DLATCH box %g x %g um, gap %g um, divScale %g\n" W H G divScale)

            ;; 2x2 array: XD1 R0 | XD2 MY / XD3 MX | XD4 R180
            foreach(e divXdNets
              o = divSlotOrigin(e W H G)
              ox = car(o)
              oy = cadr(o)
              inst = dbCreateInst(cvT dlM car(e) list(divC(ox) divC(oy)) cadr(e) 1)  ; [VERIFY]
              if(inst
                then printf("  %s %s at origin (%g, %g) um\n" car(e) cadr(e) ox oy)
                else printf("  FAILED to place %s\n" car(e)))
            )

            ;; net labels at every instance pin (labels only; no metal routing yet)
            foreach(e divXdNets
              o = divSlotOrigin(e W H G)
              ox = car(o)
              oy = cadr(o)
              foreach(pn list("CK" "CKb" "D" "Db" "Q" "Qb" "VDD" "VSS" "NBIAS")
                pos = assoc(pn divPinTable)
                if(pos
                  then
                    gp = divXform(cadr(e) ox oy cadr(pos) caddr(pos))
                    net = divNetOf(e pn)
                    divLabel(cvT list("Metal1" "label") car(gp) cadr(gp) net)
                  else printf("  WARN: no pin-table entry for %s\n" pn))
              )
            )

            ;; clock length check (star model): sum of Manhattan distances from each
            ;; ck / ckb pin to the array centre. Equal sums = symmetric by construction.
            cx = W + G / 2.0
            cy = H + G / 2.0
            lenCk = 0.0
            lenCkb = 0.0
            foreach(e divXdNets
              o = divSlotOrigin(e W H G)
              ox = car(o)
              oy = cadr(o)
              foreach(pn list("CK" "CKb")
                pos = assoc(pn divPinTable)
                gp = divXform(cadr(e) ox oy cadr(pos) caddr(pos))
                net = divNetOf(e pn)
                dx = car(gp) - cx
                dy = cadr(gp) - cy
                pt = abs(dx) + abs(dy)
                if(equal(net "ck")  then lenCk = lenCk + pt)
                if(equal(net "ckb") then lenCkb = lenCkb + pt)
              )
            )
            printf("== clock star length (um): ck=%g ckb=%g diff=%g\n" lenCk lenCkb abs(lenCk - lenCkb))
            printf("== clock TRUNKS NOT DRAWN in this version (see LAYOUT_NOTES.md)\n")
            errset(dbSave(cvT) t)
            printf("== divider_core saved\n")
          )
        )
      ))
  )
)

;; ------------------------------ entry points --------------------------
procedure(buildLayout()
  buildLayoutDLATCH()
  buildDividerCore()
)

;; Assura DRC: the GUI route is printed. A scripted call is not used because
;; the Assura SKILL entry point is not confirmed for this install.
procedure(runDRC()
  printf("== runDRC: Assura DRC for DLATCH (GUI steps, menu names VERIFY)\n")
  printf("  1. Open divider_lib/DLATCH/layout in the Virtuoso Layout Editor.\n")
  printf("  2. Assura > Run DRC (Physical Verification menu).\n")
  printf("  3. Technology: gpdk045_av (assura_tech.lib).  Rule set: default (assura/techRuleSets).\n")
  printf("  4. Rules file: /home/buet/pdk/gpdk045_v_6_0/assura/assuraDRC.rul\n")
  printf("  5. Batch alternative: cadence/skill/run_drc.rsf (keywords VERIFY, batch command UNKNOWN).\n")
  printf("  6. Send back the DRC error list (rule name, count, coordinates).\n")
  t
)

printf("build_layout_v2.il loaded. Run buildLayout(), or buildLayoutDLATCH() then buildDividerCore().\n")
