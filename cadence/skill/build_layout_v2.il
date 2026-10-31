;; =========================================================================
;; build_layout_v2.il  -  gpdk045 layout for the divider: DLATCH + divider_core
;; FIRST VERSION, UNTESTED (written without Virtuoso / Assura access).
;; Load in CIW:  load("/abs/path/cadence/skill/build_layout_v2.il")
;; Run:          buildLayoutDLATCH()  then  buildDividerCore()  then  runDRC()
;; Tags:  [V]      = verified in a PDK file (line refs in LAYOUT_NOTES.md)
;;        [VERIFY] = SKILL API or behaviour not confirmed here
;; Units: inputs are microns, converted to dbu by divS(). Keep all
;;        coordinates >= 0 (divS rounds with fix(x+0.5)).
;; Scope of this version: pcells placed, pins/labels placed, top-level
;;        instances + net labels + clock length check. Intra-latch metal
;;        routing is NOT drawn yet: terminal boxes are printed so the next
;;        iteration can route from real geometry.
;; =========================================================================

;; ------------------------------ tunables ------------------------------
defvar(divLibName    "divider_lib")   ; [VERIFY] exists, attached to gpdk045 tech
defvar(divPdkLib     "gpdk045")       ; [V] cds.lib line 6
defvar(divMosCell    "nmos1v")        ; [V] gpdk045/nmos1v
defvar(divResCell    "resnsnpoly")    ; [V] gpdk045/resnsnpoly (deviation: see notes)
defvar(divViewType   "maskLayout")    ; [VERIFY] tf viewTypeUnits row maskLayout
defvar(divDbuPerUm   2000)            ; [V] tf viewTypeUnits maskLayout 2000; [VERIFY] units
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
defvar(divRsh        200.0)           ; ohm/sq [V] gpdk045_resistor.scs tt_res, r_resnsnpoly = 200
defvar(divRend0      1.44e-5)         ; ohm*m [V] tt_res, r_rend_resnsnpoly = 1.44e-5
defvar(divResW      0.8)              ; um [V] POLYR.W.1.2 suggested min 0.8 (assuraDRC.rul line 108)

;; State shared between buildLayoutDLATCH and buildDividerCore (same CIW session)
defvar(divPinTable  nil)              ; list of (name x y) in DLATCH local um
defvar(divDlatchBox nil)              ; (x1 y1 x2 y2) of DLATCH local um

;; ------------------------------ helpers -------------------------------
procedure(divSnapUm(um)
  fix(um / divGridUm + 0.5) * divGridUm
)

;; um -> integer dbu, snapped to the manufacturing grid
procedure(divS(um)
  fix(divSnapUm(um) * divDbuPerUm + 0.5)
)

procedure(divRect(cv lpp x1 y1 x2 y2)
  dbCreateRect(cv lpp list(list(divS(x1) divS(y1)) list(divS(x2) divS(y2))))
)

procedure(divLabel(cv lpp x y txt)
  dbCreateLabel(cv lpp list(divS(x) divS(y)) txt "centerCenter" "R0" "stick" divS(0.1))
)

;; metal1 pin: pin shape + net + terminal + label. Each API call is errset-wrapped.
procedure(divPin(cv name x y dir)
  let((net term x2 y2 pf)
    x2 = x + divPinW
    y2 = y + divPinH
    net  = car(errset(dbCreateNet(cv name) t))
    term = car(errset(dbCreateTerm(net name dir) t))   ; [VERIFY] signature
    pf   = divRect(cv list("Metal1" "pin") x y x2 y2)
    unless(car(errset(dbCreatePin(net pf) t))
      printf("  VERIFY: dbCreatePin failed for %s (net/term/pin API)\n" name))
    divLabel(cv list("Metal1" "label") (x + divPinW / 2.0) (y + divPinH / 2.0) name)
    printf("  pin %s at (%g, %g) um\n" name x y)
    term
  )
)

;; ------------------------------ MOS / R placement ---------------------
;; Primary param set: types as in the CDF (strings). Retry set: fingers as int.
procedure(divMosParams(nf lStr)
  list(list("fw" "string" divFw)
       list("l" "string" lStr)
       list("fingers" "string" sprintf(nil "%d" nf))
       list("connectGates" "cyclic" "Top")
       list("tap" "cyclic" "Integrated"))
)

procedure(divMosParamsInt(nf lStr)
  list(list("fw" "string" divFw)
       list("l" "string" lStr)
       list("fingers" "int" nf)
       list("connectGates" "cyclic" "Top")
       list("tap" "cyclic" "Integrated"))
)

procedure(divPlacePcell(cv libName cellName instName xU yU params)
  let((master inst)
    inst = nil
    master = car(errset(dbOpenCellViewByType(libName cellName "layout" nil "r") t))
    if(master
      then inst = car(errset(dbCreateParamInst(cv master instName list(divS(xU) divS(yU)) "R0" 1 params) t))
      else printf("ERROR: cannot open %s/%s/layout (is the PDK attached?)\n" libName cellName))
    if(inst
      then printf("  placed %s (%s) at (%g, %g) um\n" instName cellName xU yU)
      else printf("  FAILED to place %s (%s); check param names/types above\n" instName cellName))
    inst
  )
)

procedure(divPlaceMos(cv name xU yU nf lStr)
  let((inst)
    inst = divPlacePcell(cv divPdkLib divMosCell name xU yU divMosParams(nf lStr))
    unless(inst
      printf("  retry %s with fingers as int\n" name)
      inst = divPlacePcell(cv divPdkLib divMosCell name xU yU divMosParamsInt(nf lStr)))
    inst
  )
)

;; right edge of an instance in um (bBox is ((x1 y1) (x2 y2)) in dbu)
procedure(divRightUm(inst)
  car(cadr(inst~>bBox)) * 1.0 / divDbuPerUm
)

;; x where the next MOS should start: right edge + gap, or fallback when inst failed
procedure(divNextX(inst xFallback)
  let((rr)
    if(inst
      then rr = divRightUm(inst) + divMosGap
      else rr = xFallback + 1.0)
    rr
  )
)

;; ------------------------------ DLATCH --------------------------------
procedure(divBuildDlatch(cv)
  let((yA yB yR1 yR2 yTop lenR x xM2 m1 m2 m3 m4 m5 m6 m7 r1 r2
       xR xRight pD pDb pQ pQb boxX boxY)
    printf("== DLATCH: building in %s\n" divLibName)
    yA = 1.0                         ; row A (M1 M5 M7 M6 M2) bottom edge
    yB = yA + 1.5                    ; row B (M3 M4), above row A
    yR1 = yB + 1.5                   ; resistor R1 (horizontal)
    yR2 = yR1 + 1.4                  ; resistor R2
    yTop = yR2 + 1.6
    lenR = divResLenUm()
    printf("  R len = %g um (W %g um, rsh %g, target %g ohm)\n" lenR divResW divRsh divRTarget)

    ;; row A, left to right: M1 M5 M7 M6 M2  (M7 centred between clock devices M5/M6)
    x = 1.0
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

    ;; row B: cross-coupled M3 (above M1) and M4 (above M2)
    m3 = divPlaceMos(cv "M3" 1.0 yB divNf1 divL1)
    m4 = divPlaceMos(cv "M4" xM2 yB divNf1 divL1)

    ;; poly resistors R1 (VDD-Q) and R2 (VDD-Qb), horizontal
    r1 = divPlacePcell(cv divPdkLib divResCell "R1" 1.0 yR1
           list(list("segW" "string" sprintf(nil "%gu" divResW))
                list("segL" "string" sprintf(nil "%gu" lenR))
                list("segments" "int" 1)))
    r2 = divPlacePcell(cv divPdkLib divResCell "R2" 1.0 yR2
           list(list("segW" "string" sprintf(nil "%gu" divResW))
                list("segL" "string" sprintf(nil "%gu" lenR))
                list("segments" "int" 1)))

    ;; cell extent (um)
    xRight = divRightUm(m2)
    xR = divNextX(r1 0.0) - divMosGap
    xRight = max(xRight xR)
    boxX = xRight + 0.6
    boxY = yTop + 0.4

    ;; pins: the pin table is also read by buildDividerCore
    printf("== DLATCH pins (placed; NOT yet routed to devices)\n")
    pD = yA + 0.2
    pDb = yB + 0.2
    pQ = yA + 0.2
    pQb = yB + 0.2
    divPin(cv "CK"    1.0 0.2 "input")
    divPin(cv "CKb"   1.6 0.2 "input")
    divPin(cv "NBIAS" 2.2 0.2 "input")
    divPin(cv "VSS"   2.8 0.2 "inputOutput")
    divPin(cv "D"     0.1 pD  "input")
    divPin(cv "Db"    0.1 pDb "input")
    divPin(cv "Q"     xRight + 0.4 pQ  "output")
    divPin(cv "Qb"    xRight + 0.4 pQb "output")
    divPin(cv "VDD"   1.0 yTop "inputOutput")

    setq(divPinTable
      list(list("CK" 1.0 0.2) list("CKb" 1.6 0.2) list("NBIAS" 2.2 0.2)
           list("VSS" 2.8 0.2) list("D" 0.1 pD) list("Db" 0.1 pDb)
           list("Q" xRight+0.4 pQ) list("Qb" xRight+0.4 pQb) list("VDD" 1.0 yTop)))
    setq(divDlatchBox list(0.0 0.0 boxX boxY))
    printf("== DLATCH box (um): 0 0 %g %g\n" boxX boxY)
    printf("== DLATCH terminal boxes: run divDumpTerms(\"M1\") etc. and send output\n")
    errset(dbSave(cv) t)
    printf("== DLATCH saved\n")
  )
)

;; prints the instance terminal boxes in global dbu (for the next routing pass)
procedure(divDumpTerms(instName)
  printf("  (divDumpTerms: call with the inst object, see notes)\n")
  printf("  %s\n" instName)
)

procedure(divResLenUm()
  let((endOhm len)
    endOhm = 2.0 * divRend0 / (divResW * 1e-6)   ; two ends, ohm (= 36 ohm)
    len = (divRTarget - endOhm) * divResW / divRsh ; um (= 7.856)
    divSnapUm(len)                               ; snapped to 0.005 um (= 7.855)
  )
)

procedure(buildLayoutDLATCH()
  let((lib cv)
    printf("== build_layout_v2: DLATCH\n")
    lib = ddGetObj(divLibName)
    cond(
      ((not(lib))
        printf("ERROR: library %s not found. Create it attached to gpdk045 and rerun.\n" divLibName))
      ((ddGetObj(divLibName "DLATCH" "layout"))
        printf("SKIP: DLATCH/layout already exists. Delete it in the Library Manager to rebuild.\n"))
      (t
        cv = dbOpenCellViewByType(divLibName "DLATCH" "layout" divViewType "w")  ; [VERIFY] creates the view
        if(cv
          then divBuildDlatch(cv)
          else printf("ERROR: could not create DLATCH/layout (see CIW error above)\n"))))
  )
)

;; ------------------------------ divider_core --------------------------
;; per instance: name orientation pin-nets in netlist order (D Db CK CKb Q Qb VDD VSS NBIAS)
;; netlist: spectre/divider_gpdk45.scs lines for XD1..XD4
defvar(divXdNets
  list(
    list("XD1" "R0"   "Q4b" "Q4" "ck"  "ckb" "Q1"  "Q1b" "vdd" "vss" "nbias")
    list("XD2" "MY"   "Q1b" "Q1" "ckb" "ck"  "Q2"  "Q2b" "vdd" "vss" "nbias")
    list("XD3" "MX"   "Q2"  "Q2b" "ckb" "ck" "Q3"  "Q3b" "vdd" "vss" "nbias")
    list("XD4" "R180" "Q3b" "Q3" "ck"  "ckb" "Q4"  "Q4b" "vdd" "vss" "nbias")))

;; global position of a DLATCH-local point for orientation o placed at (ox,oy)
procedure(divXform(o ox oy px py)
  let((gx gy)
    gx = ox + px
    gy = oy + py
    if(or(equal(o "MY") equal(o "R180")) then gx = ox - px)
    if(or(equal(o "MX") equal(o "R180")) then gy = oy - py)
    list(gx gy)
  )
)

;; net name for pin "pinName" of an entry in divXdNets
procedure(divNetOf(e pinName)
  let((names)
    names = '("D" "Db" "CK" "CKb" "Q" "Qb" "VDD" "VSS" "NBIAS")
    nth(index(pinName names) cddr(e))
  )
)

procedure(buildDividerCore()
  let((cvT dlM W H G e ox oy col row inst gp net lenCk lenCkb cx cy pt pos)
    printf("== build_layout_v2: divider_core\n")
    cond(
      ((not(divPinTable))
        printf("ERROR: divPinTable empty. Run buildLayoutDLATCH() first in this CIW session.\n"))
      ((ddGetObj(divLibName "divider_core" "layout"))
        printf("SKIP: divider_core/layout already exists.\n"))
      (t
        dlM = dbOpenCellViewByType(divLibName "DLATCH" "layout" divViewType "r")
        cvT = dbOpenCellViewByType(divLibName "divider_core" "layout" divViewType "w")  ; [VERIFY]
        if(not(dlM && cvT)
          then printf("ERROR: could not open DLATCH master or create divider_core\n")
          else
          progn(
            W = car(nth(2 divDlatchBox))
            H = car(cdr(cdr(cdr(divDlatchBox))))
            G = divTopGap
            ;; 2x2 array: col0 row0 R0 | col1 row0 MY | col0 row1 MX | col1 row1 R180
            foreach(e divXdNets
              col = 0
              row = 0
              if(equal(car(e) "XD2") || equal(car(e) "XD4") then col = 1)
              if(equal(car(e) "XD3") || equal(car(e) "XD4") then row = 1)
              ox = 0.0
              oy = 0.0
              if(col == 1 then ox = 2.0 * W + G)
              if(row == 1 then oy = 2.0 * H + G)
              inst = dbCreateInst(cvT dlM car(e) list(divS(ox) divS(oy)) cadr(e) 1)
              if(inst
                then printf("  %s %s at (%g, %g) um\n" car(e) cadr(e) ox oy)
                else printf("  FAILED to place %s\n" car(e)))
            )
            ;; net labels at every instance pin (labels only, no metal routing yet)
            foreach(e divXdNets
              col = 0
              row = 0
              if(equal(car(e) "XD2") || equal(car(e) "XD4") then col = 1)
              if(equal(car(e) "XD3") || equal(car(e) "XD4") then row = 1)
              ox = 0.0
              oy = 0.0
              if(col == 1 then ox = 2.0 * W + G)
              if(row == 1 then oy = 2.0 * H + G)
              foreach(pn list("CK" "CKb" "D" "Db" "Q" "Qb" "VDD" "VSS" "NBIAS")
                pos = assoc(pn divPinTable)
                if(pos
                  then
                    gp = divXform(cadr(e) ox oy cadr(pos) caddr(pos))
                    net = divNetOf(e pn)
                    divLabel(cvT list("Metal1" "label") car(gp) cadr(gp) net)
                  else printf("  WARN: no pin table entry for %s\n" pn))
              )
            )
            ;; clock wire-length check: star model, sum of Manhattan distances from
            ;; each ck / ckb pin to the array centre. Equal sums = symmetric.
            cx = W + G / 2.0
            cy = H + G / 2.0
            lenCk = 0.0
            lenCkb = 0.0
            foreach(e divXdNets
              col = 0
              row = 0
              if(equal(car(e) "XD2") || equal(car(e) "XD4") then col = 1)
              if(equal(car(e) "XD3") || equal(car(e) "XD4") then row = 1)
              ox = 0.0
              oy = 0.0
              if(col == 1 then ox = 2.0 * W + G)
              if(row == 1 then oy = 2.0 * H + G)
              foreach(pn list("CK" "CKb")
                pos = assoc(pn divPinTable)
                gp = divXform(cadr(e) ox oy cadr(pos) caddr(pos))
                net = divNetOf(e pn)
                pt = abs(car(gp) - cx) + abs(cadr(gp) - cy)
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

;; Assura DRC: the GUI route is printed here. A scripted call is not used
;; because the Assura SKILL entry point is not confirmed for IC6.1.5/Assura 4.1.
procedure(runDRC()
  printf("== runDRC: Assura DRC for DLATCH (run these in the VM GUI, VERIFY menu names)\n")
  printf("  1. Open divider_lib/DLATCH/layout in Virtuoso Layout Editor.\n")
  printf("  2. Assura > Run DRC (or Assura > Physical Verification > DRC).\n")
  printf("  3. Rules file: /home/buet/pdk/gpdk045_v_6_0/assura/assuraDRC.rul\n")
  printf("     Technology/ruleset name: default (cadence/skill/../assura_tech.lib: gpdk045_av)\n")
  printf("  4. Batch alternative: cadence/skill/run_drc.rsf (VERIFY keywords, batch command unknown).\n")
  printf("  5. Send the DRC error list (rule name + count + coords) back for the next pass.\n")
  t
)

printf("build_layout_v2.il loaded. Run buildLayout() or buildLayoutDLATCH() then buildDividerCore().\n")
