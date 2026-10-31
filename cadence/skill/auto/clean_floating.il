;; =========================================================================
;; clean_floating.il - remove "Floating net" warnings from the wired
;; schematics of divider_lib (DLATCH, divider_core, tb_divider).
;;
;; Load:  load("/abs/path/cadence/skill/auto/clean_floating.il")
;; Run:   cfCleanCell("DLATCH" "dry")   ; in memory only, nothing saved
;;        cfCleanCell("DLATCH" "save")  ; apply and dbSave
;;
;; Why the warnings exist: wire_schematics.il drew wires between pin terminals.
;; The original build left a short stub at each pin: a 2-point wire from the
;; pin terminal to a net label, label at the free end. The routed wire ends at
;; the terminal, so the label at the free end of the stub is dangling and
;; schCheck reports "Floating net" there.
;;
;; Rule (geometry only, no per-net or per-coordinate data). A label L at point
;; P is a candidate when:
;;   1. L is the only label at P, and no other wire touches P,
;;   2. P is not an instance terminal point,
;;   3. exactly one wire W touches P, W has 2 points and length <= 1.0 (stub),
;;   4. the other end Q of W lies on another wire H (H is not W).
;; Action for each candidate: create a label with the same name as L on H at Q,
;; then delete the stub W and the label L. The new label is created before the
;; old one is deleted, so no net loses its name and no component is unnamed.
;;
;; Tags: [V] schCreateWireLabel 9-argument form, copied from
;; build_schematic_v2.il (worked in this VM). [D] other calls (IC6.1.5 SKILL).
;; SKILL pitfalls kept in mind: cond clauses as (test body), every local
;; prefixed "cf" (variables are dynamically scoped), no infix comparisons.
;; =========================================================================

defvar(cfLib  "divider_lib")
defvar(cfFont 0.25)              ; net label font height (as build_schematic_v2.il)
defvar(cfEps  0.001)

;; Point equality within cfEps. Points are list(x y).
procedure(cfEq(cfP cfQ)
  let((cfDx cfDy)
    cfDx = car(cfP) - car(cfQ)
    cfDy = cadr(cfP) - cadr(cfQ)
    and(lessp(abs(cfDx) cfEps) lessp(abs(cfDy) cfEps))))

;; True if point cfP lies on the axis-aligned segment cfA-cfB (bbox test).
procedure(cfOnSeg(cfP cfA cfB)
  let((cfXl cfXh cfYl cfYh)
    cfXl = min(car(cfA) car(cfB)) - cfEps
    cfXh = max(car(cfA) car(cfB)) + cfEps
    cfYl = min(cadr(cfA) cadr(cfB)) - cfEps
    cfYh = max(cadr(cfA) cadr(cfB)) + cfEps
    and(lessp(cfXl car(cfP)) lessp(car(cfP) cfXh)
        lessp(cfYl cadr(cfP)) lessp(cadr(cfP) cfYh))))

;; True if point cfP lies on any segment of wire cfW (endpoints included).
procedure(cfTouchW(cfP cfW)
  let((cfL cfHit)
    cfL = cfW~>points
    cfHit = nil
    while(cdr(cfL)
      when(cfOnSeg(cfP car(cfL) cadr(cfL)) cfHit = t)
      cfL = cdr(cfL))
    cfHit))

;; True if point cfP is an endpoint (not an interior point) of wire cfW.
procedure(cfEnd(cfP cfW)
  let((cfPts)
    cfPts = cfW~>points
    or(cfEq(car(cfPts) cfP) cfEq(car(last(cfPts)) cfP))))

;; Length of a 2-point wire, Manhattan.
procedure(cfStubLen(cfW)
  let((cfPts cfA cfB)
    cfPts = cfW~>points
    cfA = car(cfPts)
    cfB = cadr(cfPts)
    abs(car(cfA) - car(cfB)) + abs(cadr(cfA) - cadr(cfB))))

;; Terminal point of an instance terminal (R0 assumed, as in wire_schematics.il):
;; centre of the first figure of the first pin, plus the instance origin.
procedure(cfTermPt(cfI cfT)
  let((cfTm cfPn cfFg cfBb cfX cfY)
    cfTm = cfT~>term
    cfPn = car(cfTm~>pins)
    cfFg = car(cfPn~>figs)
    cfBb = cfFg~>bBox
    cfX = (car(car(cfBb)) + car(cadr(cfBb))) / 2.0 + car(cfI~>xy)
    cfY = (cadr(car(cfBb)) + cadr(cadr(cfBb))) / 2.0 + cadr(cfI~>xy)
    list(cfX cfY)))

procedure(cfTermPts(cfCv)
  let((cfOut cfR)
    cfOut = nil
    foreach(cfI cfCv~>instances
      foreach(cfT cfI~>instTerms
        cfR = car(errset(cfTermPt(cfI cfT) t))
        when(cfR cfOut = cons(cfR cfOut))))
    cfOut))

;; Candidate for label cfL: list(name P Q stub host label), or nil.
;; cfWs: all wires. Label L must be the only label at P, the only wire touching
;; P must be a 2-point stub W, and P must not be an instance terminal.
procedure(cfCandSub(cfL cfN cfP cfW cfWs)
  let((cfPts cfQ cfHs)
    cfPts = cfW~>points
    cond(
      (and(equal(length(cfPts) 2) lessp(cfStubLen(cfW) 1.0))
        cfQ = if(cfEq(car(cfPts) cfP) then cadr(cfPts) else car(cfPts))
        cfHs = setof(cfH cfWs and(not(eq(cfH cfW)) cfTouchW(cfQ cfH)))
        if(cfHs then list(cfN cfP cfQ cfW car(cfHs) cfL) else nil))
      (t nil))))

procedure(cfCandOf(cfL cfLbs cfWs cfTps)
  let((cfP cfN cfNl cfAt cfTt)
    cfP = car(errset(cfL~>xy t))
    cfN = cfL~>theLabel
    cfNl = setof(cfX cfLbs cfEq(car(errset(cfX~>xy t)) cfP))
    cfAt = setof(cfX cfWs cfTouchW(cfP cfX))
    cfTt = setof(cfX cfTps cfEq(cfX cfP))
    if(and(cfP equal(length(cfNl) 1) equal(length(cfAt) 1) null(cfTt)
           cfEnd(cfP car(cfAt)))
      then cfCandSub(cfL cfN cfP car(cfAt) cfWs)
      else nil)))

procedure(cfCands(cfLbs cfWs cfTps)
  let((cfOut cfC)
    cfOut = nil
    foreach(cfL cfLbs
      cfC = cfCandOf(cfL cfLbs cfWs cfTps)
      when(cfC cfOut = cons(cfC cfOut)))
    cfOut))

;; Centre points of the schCheck markers (msg "Floating net ..." with a bBox at the
;; label point). Only markers are read; the list is used to select candidates.
procedure(cfMarkPts(cfCv)
  let((cfOut cfBb cfX cfY)
    cfOut = nil
    foreach(cfM cfCv~>markers
      cfBb = car(errset(cfM~>bBox t))
      when(cfBb
        cfX = (car(car(cfBb)) + car(cadr(cfBb))) / 2.0
        cfY = (cadr(car(cfBb)) + cadr(cadr(cfBb))) / 2.0
        cfOut = cons(list(cfX cfY) cfOut)))
    cfOut))

;; True if a marker centre equals point cfP.
procedure(cfHasM(cfP cfMk)
  let((cfX)
    cfX = setof(cfM cfMk cfEq(cfM cfP))
    if(cfX then t else nil)))

;; Apply candidates: create the replacement label first, then delete stub and label.
;; Element order: 0 name, 1 P, 2 Q, 3 stub, 4 host wire, 5 label.
procedure(cfApply(cfCv cfC)
  let((cfK cfNew cfNOk)
    cfNOk = 0
    foreach(cfK cfC
      cfNew = errset(schCreateWireLabel(cfCv nth(4 cfK) nth(2 cfK) nth(0 cfK) "lowerLeft" "R0" "stick" cfFont nil) t)
      cond(
        (null(car(cfNew))
          printf("CF FAIL label %s at %L not replaced, stub kept\n" nth(0 cfK) nth(2 cfK)))
        (t
          dbDeleteObject(nth(5 cfK))
          dbDeleteObject(nth(3 cfK))
          cfNOk = cfNOk + 1
          printf("CF DONE %s: label at %L moved to %L on host wire\n" nth(0 cfK) nth(1 cfK) nth(2 cfK)))))
    cfNOk))

;; Entry point. cfMode "dry": nothing saved. "save": dbSave after the check.
procedure(cfCleanCell(cfCell cfMode)
  let((cfCv cfShapes cfLbs cfWs cfTps cfC cfAll cfMk cfN cfChk)
    cfCv = dbOpenCellViewByType(cfLib cfCell "schematic" "schematic" "a")
    cfChk = car(errset(schCheck(cfCv) t))
    printf("CF %s schCheck before: %L\n" cfCell cfChk)
    cfMk = cfMarkPts(cfCv)
    cfShapes = cfCv~>shapes
    cfLbs = setof(cfS cfShapes equal(car(errset(cfS~>objType t)) "label"))
    cfWs = setof(cfS cfShapes member(car(errset(cfS~>objType t)) list("line" "path")))
    cfTps = cfTermPts(cfCv)
    printf("CF %s before: %d labels, %d wires, %d terminals\n" cfCell length(cfLbs) length(cfWs) length(cfTps))
    cfAll = cfCands(cfLbs cfWs cfTps)
    cfC = setof(cfK cfAll cfHasM(nth(1 cfK) cfMk))
    printf("CF %s markers: %d, candidates: %d, selected by marker: %d\n" cfCell length(cfMk) length(cfAll) length(cfC))
    foreach(cfN cfC
      printf("CF CAND %s at %L stub to %L host wire\n" nth(0 cfN) nth(1 cfN) nth(2 cfN)))
    printf("CF %s applied: %d\n" cfCell cfApply(cfCv cfC))
    cfChk = car(errset(schCheck(cfCv) t))
    printf("CF %s schCheck (errors warnings): %L\n" cfCell cfChk)
    printf("CF %s after: %d labels, %d wires\n" cfCell
      length(setof(cfS cfCv~>shapes equal(car(errset(cfS~>objType t)) "label")))
      length(setof(cfS cfCv~>shapes member(car(errset(cfS~>objType t)) list("line" "path")))))
    when(equal(cfMode "save")
      dbSave(cfCv)
      printf("CF %s saved\n" cfCell))
    dbClose(cfCv)
    cfChk))
