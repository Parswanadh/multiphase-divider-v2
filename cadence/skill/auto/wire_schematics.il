;; =========================================================================
;; wire_schematics.il - draw wires between the terminals of every net in
;; divider_lib/{DLATCH, divider_core, tb_divider} (schematic views).
;;
;; Load:  load("/abs/path/cadence/skill/auto/wire_schematics.il")
;; Run:   wireSchematicsMain()
;;
;; What it does, per cell:
;;  1. Opens the schematic for edit ("a").
;;  2. Reads connectivity from the database: every instTerm -> net name,
;;     and the terminal point (instance origin + master pin figure centre).
;;  3. Groups the terminals by net name. Nets with fewer than 2 terminals are skipped.
;;  4. Per net: minimum spanning tree (Manhattan distance) over the terminal
;;     points; each tree edge is drawn with the built-in router
;;     schCreateWire(cv "route" "full" ...).
;;  5. schCheck, then dbSave and dbClose.
;;
;; Connectivity is NOT changed: the existing pin stubs and net labels are kept.
;; The new wires only join terminals that are already on the same net name.
;; Nothing is hard-coded per net or per coordinate. Only the cell list and the
;; tunables below are names/values.
;;
;; Tags: [V] verified in this VM by a run, [D] from IC615 docs, [VERIFY] not yet confirmed.
;;   schCreateWire(d_cvId t_entryMethod t_routeMethod l_points n_xSpacing n_ySpacing n_width)
;;   with entry "route" only the first two points are used [D: skcompref chap2].
;;
;; SKILL pitfalls kept in mind: cond clauses written as (null(x) ...),
;; all infix math inside let statements, every local name prefixed "ws"
;; (variables are dynamically scoped).
;; =========================================================================

;; ------------------------------ tunables -------------------------------
defvar(wsLib       "divider_lib")
defvar(wsCells     list("DLATCH" "divider_core" "tb_divider"))
defvar(wsWidth     0.0625)      ; wire width (same as the pin stubs)
defvar(wsSnap      0.0625)      ; snap spacing passed to schCreateWire
defvar(wsSkipNets  nil)         ; nets to leave as stubs only, e.g. list("gnd!")
defvar(wsSave      t)           ; t: dbSave each cell. nil: discard (dry run)
defvar(wsDrawn     nil)          ; segments drawn in the current cell: list(netName p1 p2)

;; ------------------------------ geometry -------------------------------

;; Centre of a bBox ((x1 y1) (x2 y2)) as list(x y).
procedure(wsBoxCtr(wsBb)
  let((wsX1 wsY1 wsX2 wsY2 wsCx wsCy)
    wsX1 = car(car(wsBb))
    wsY1 = cadr(car(wsBb))
    wsX2 = car(cadr(wsBb))
    wsY2 = cadr(cadr(wsBb))
    wsCx = (wsX1 + wsX2) / 2.0
    wsCy = (wsY1 + wsY2) / 2.0
    list(wsCx wsCy)))

;; Centre of the first figure of the first pin of a master terminal, master coordinates.
;; For nmos1v this is the centre of the small pin rect, which is the connection point.
procedure(wsCtr(wsTm)
  let((wsPn wsFg)
    wsPn = car(wsTm~>pins)
    wsFg = car(wsPn~>figs)
    wsBoxCtr(wsFg~>bBox)))

;; Terminal point of an instance terminal, in cellview coordinates.
;; Assumes R0 orientation for every instance, which build_schematic_v2.il uses.
procedure(wsPoint(wsI wsT)
  let((wsC wsXy wsX wsY)
    wsC = wsCtr(wsT~>term)
    wsXy = wsI~>xy
    wsX = car(wsXy) + car(wsC)
    wsY = cadr(wsXy) + cadr(wsC)
    list(wsX wsY)))

;; Manhattan distance between two points.
procedure(wsDist(wsP wsQ)
  let((wsDx wsDy)
    wsDx = car(wsP) - car(wsQ)
    wsDy = cadr(wsP) - cadr(wsQ)
    abs(wsDx) + abs(wsDy)))

;; ------------------------------ connectivity ---------------------------

;; One row per instance terminal that has a net:  list(netName point "inst.term")
procedure(wsRowsOf(wsCv)
  let((wsAcc wsNm wsPt)
    wsAcc = nil
    foreach(wsI wsCv~>instances
      foreach(wsT wsI~>instTerms
        wsNm = car(errset(wsT~>net~>name t))
        when(stringp(wsNm)
          wsPt = wsPoint(wsI wsT)
          wsAcc = cons(list(wsNm wsPt strcat(wsI~>name "." wsT~>name)) wsAcc))))
    reverse(wsAcc)))

;; Schematic pins (ipin/opin/iopin) are not instTerms. Each cell terminal has one pin object
;; whose figure sits next to the pin tip. The tip is the origin of the pin instance nearest to
;; that figure. Row: list(netName point "PIN.<terminal>").
procedure(wsPinRowsOf(wsCv)
  let((wsAcc wsNm wsFg wsPc wsBestD wsBestI wsDd)
    wsAcc = nil
    foreach(wsTm wsCv~>terminals
      wsNm = car(errset(wsTm~>net~>name t))
      when(stringp(wsNm)
        wsFg = car(car(wsTm~>pins)~>figs)
        wsPc = wsBoxCtr(wsFg~>bBox)
        wsBestD = nil
        wsBestI = nil
        foreach(wsI wsCv~>instances
          wsDd = wsDist(wsI~>xy wsPc)
          cond(
            (null(wsBestD) setq(wsBestD wsDd) setq(wsBestI wsI))
            (lessp(wsDd wsBestD) setq(wsBestD wsDd) setq(wsBestI wsI))))
        wsAcc = cons(list(wsNm wsBestI~>xy strcat("PIN." wsTm~>name)) wsAcc)))
    reverse(wsAcc)))

;; Distinct net names, in first-seen order.
procedure(wsNamesOf(wsRows)
  let((wsAcc)
    wsAcc = nil
    foreach(wsRowN wsRows
      unless(member(car(wsRowN) wsAcc)
        wsAcc = cons(car(wsRowN) wsAcc)))
    reverse(wsAcc)))

;; Rows that belong to one net name.
procedure(wsOfNet(wsRows wsNm)
  let((wsAcc)
    wsAcc = nil
    foreach(wsRowM wsRows
      when(equal(car(wsRowM) wsNm)
        wsAcc = cons(wsRowM wsAcc)))
    reverse(wsAcc)))

;; ------------------------------ spanning tree --------------------------

;; Prim minimum spanning tree over Manhattan distance.
;; wsPts: list of points. Returns a list of (i j) index pairs into wsPts.
procedure(wsMst(wsPts)
  let((wsN wsHi wsIn wsOut wsEd wsBest wsD wsK wsRowA wsIdxB)
    wsN = length(wsPts)
    wsHi = wsN - 1
    wsIn = list(0)
    wsOut = nil
    for(wsK 1 wsHi
      setq(wsOut append1(wsOut wsK)))
    wsEd = nil
    while(wsOut
      wsBest = nil
      foreach(wsRowA wsOut
        foreach(wsIdxB wsIn
          wsD = wsDist(nth(wsRowA wsPts) nth(wsIdxB wsPts))
          cond(
            (null(wsBest) wsBest = list(wsD wsRowA wsIdxB))
            (lessp(wsD car(wsBest)) wsBest = list(wsD wsRowA wsIdxB)))))
      wsEd = cons(cdr(wsBest) wsEd)
      wsIn = cons(cadr(wsBest) wsIn)
      wsOut = setof(wsX wsOut not(wsX == cadr(wsBest)))
    )
    reverse(wsEd)))

;; ------------------------------ drawing --------------------------------

;; True when a created object is a flight line. The router returns flight lines as objType "line"
;; (diagonal or axis aligned) and routed Manhattan wires as objType "path". A diagonal
;; two-point object is also counted as a flight.
procedure(wsIsFlight(wsO)
  let((wsPts wsA wsB wsDx wsDy wsTy)
    wsPts = car(errset(wsO~>points t))
    wsTy = car(errset(wsO~>objType t))
    cond(
      (equal(wsTy "line") t)
      (lessp(length(wsPts) 2) nil)
      (t
        wsA = car(wsPts)
        wsB = cadr(wsPts)
        wsDx = abs(car(wsA) - car(wsB))
        wsDy = abs(cadr(wsA) - cadr(wsB))
        and(wsDx > 1e-6 wsDy > 1e-6)))))

;; Axis-aligned box test: is point wsO inside the box spanned by A and B (tolerance 0.02)?
procedure(wsInBox(wsO wsA wsB)
  let((wsX0 wsX1 wsY0 wsY1 wsTol)
    wsTol = 0.02
    wsX0 = if(lessp(car(wsA) car(wsB)) then car(wsA) else car(wsB))
    wsX1 = if(lessp(car(wsA) car(wsB)) then car(wsB) else car(wsA))
    wsY0 = if(lessp(cadr(wsA) cadr(wsB)) then cadr(wsA) else cadr(wsB))
    wsY1 = if(lessp(cadr(wsA) cadr(wsB)) then cadr(wsB) else cadr(wsA))
    and(car(wsO) >= wsX0 - wsTol car(wsO) <= wsX1 + wsTol
        cadr(wsO) >= wsY0 - wsTol cadr(wsO) <= wsY1 + wsTol)))

;; Segments and vertices of the wires drawn so far in this cell.
;; Adds the consecutive segments of polyline wsPl to wsDrawn for net wsNm.
procedure(wsAddSegs(wsNm wsPl)
  let((wsRest)
    wsRest = wsPl
    while(cdr(wsRest)
      wsDrawn = cons(list(wsNm car(wsRest) cadr(wsRest)) wsDrawn)
      wsRest = cdr(wsRest))))

;; Segments (p1 p2) of the drawn wires of every net other than wsNm.
procedure(wsSegsOf(wsNm)
  let((wsAcc)
    wsAcc = nil
    foreach(wsE wsDrawn
      unless(equal(car(wsE) wsNm)
        wsAcc = cons(cdr(wsE) wsAcc)))
    wsAcc))

;; End points of a list of segments.
procedure(wsEndsOf(wsSegs)
  let((wsAcc)
    wsAcc = nil
    foreach(wsS wsSegs
      wsAcc = cons(car(wsS) wsAcc)
      wsAcc = cons(cadr(wsS) wsAcc))
    wsAcc))

;; t when the polyline wsPts touches an obstacle: an other-net point inside one of its segments,
;; one of its vertices inside an other-net segment, or the segment crossing an other-net point.
procedure(wsPathBlocked(wsPts wsObs wsSegs)
  let((wsHit wsRest)
    wsHit = nil
    wsRest = wsPts
    while(cdr(wsRest)
      foreach(wsO wsObs
        when(wsInBox(wsO car(wsRest) cadr(wsRest)) wsHit = t))
      foreach(wsS wsSegs
        when(or(wsInBox(car(wsRest) car(wsS) cadr(wsS)) wsInBox(cadr(wsRest) car(wsS) cadr(wsS)))
          wsHit = t))
      wsRest = cdr(wsRest))
    wsHit))

;; Detour candidates around the two points at offset wsK (left, right, above, below).
procedure(wsDetours(wsP wsQ wsK)
  let((wsX1 wsX2 wsY1 wsY2 wsXmin wsXmax wsYmin wsYmax wsXl wsXr wsYt wsYb)
    wsX1 = car(wsP)
    wsX2 = car(wsQ)
    wsY1 = cadr(wsP)
    wsY2 = cadr(wsQ)
    wsXmin = if(lessp(wsX1 wsX2) then wsX1 else wsX2)
    wsXmax = if(lessp(wsX1 wsX2) then wsX2 else wsX1)
    wsYmin = if(lessp(wsY1 wsY2) then wsY1 else wsY2)
    wsYmax = if(lessp(wsY1 wsY2) then wsY2 else wsY1)
    wsXl = wsXmin - wsK
    wsXr = wsXmax + wsK
    wsYt = wsYmax + wsK
    wsYb = wsYmin - wsK
    list(
      list(wsP list(wsXl wsY1) list(wsXl wsY2) wsQ)
      list(wsP list(wsXr wsY1) list(wsXr wsY2) wsQ)
      list(wsP list(wsX1 wsYt) list(wsX2 wsYt) wsQ)
      list(wsP list(wsX1 wsYb) list(wsX2 wsYb) wsQ))))

;; Chooses a Manhattan polyline p -> ... -> q that touches no other net. Candidates in order:
;; the two L paths, then detours at offsets 1, 2, 3, 4, 6 around the two points.
;; Returns the point list, or nil if every candidate is blocked.
procedure(wsPickPath(wsP wsQ wsObs wsSegs)
  let((wsX1 wsX2 wsY1 wsY2 wsCands wsFound)
    wsX1 = car(wsP)
    wsX2 = car(wsQ)
    wsY1 = cadr(wsP)
    wsY2 = cadr(wsQ)
    wsCands = list(
      list(wsP list(wsX2 wsY1) wsQ)
      list(wsP list(wsX1 wsY2) wsQ))
    foreach(wsK list(1.0 2.0 3.0 4.0 6.0)
      wsCands = append(wsCands wsDetours(wsP wsQ wsK)))
    wsFound = nil
    foreach(wsC wsCands
      when(and(null(wsFound) null(wsPathBlocked(wsC wsObs wsSegs)))
        wsFound = wsC))
    wsFound))

;; Points of other nets (terminal points, pin tips and label points) for net wsNm.
procedure(wsObsOf(wsAll wsNm)
  let((wsAcc)
    wsAcc = nil
    foreach(wsE wsAll
      unless(equal(car(wsE) wsNm)
        wsAcc = cons(cadr(wsE) wsAcc)))
    wsAcc))

;; Draws one wire from p to q. First the built-in router (route, full). Its result is
;; rejected when it is a flight line or when a segment touches another net (wsPathBlocked);
;; then the points are drawn as a Manhattan polyline that touches no other net (wsPickPath).
;; If no candidate is clear, nothing is drawn (the caller retries other far ends).
;; wsAll: list of list(netName point) for every terminal, pin and label in the cell.
;; Returns t when the connection was drawn, nil otherwise.
procedure(wsRoute(cv wsP wsQ wsNm wsAll)
  let((wsRr wsRw wsBad wsPath wsRes wsObs wsSegs wsPts)
    wsSegs = wsSegsOf(wsNm)
    wsObs = append(wsObsOf(wsAll wsNm) wsEndsOf(wsSegs))
    wsRr = errset(schCreateWire(cv "route" "full" list(wsP wsQ) wsSnap wsSnap wsWidth) t)
    wsRw = car(wsRr)
    wsBad = nil
    foreach(wsO wsRw
      wsPts = car(errset(wsO~>points t))
      when(or(wsIsFlight(wsO) wsPathBlocked(wsPts wsObs wsSegs))
        wsBad = t))
    cond(
      (null(wsRr) printf("  ERROR: schCreateWire failed %L -> %L\n" wsP wsQ) nil)
      (null(wsBad)
        foreach(wsO wsRw wsAddSegs(wsNm car(errset(wsO~>points t))))
        t)
      (t
        foreach(wsO wsRw dbDeleteObject(wsO))
        wsPath = wsPickPath(wsP wsQ wsObs wsSegs)
        cond(
          (null(wsPath) nil)
          (t
            printf("  fallback %s: route result rejected for %L -> %L; drawn Manhattan %L\n" wsNm wsP wsQ wsPath)
            wsRes = errset(schCreateWire(cv "draw" "full" wsPath wsSnap wsSnap wsWidth) t)
            wsAddSegs(wsNm wsPath)
            t))))))

;; Draws the spanning tree of one net.
procedure(wsNet(cv wsNm wsRows wsAll)
  let((wsPts wsEd wsP wsQ wsDd wsCnt wsRows2 wsOkE)
    wsPts = nil
    wsRows2 = wsOfNet(wsRows wsNm)
    foreach(wsRowP wsRows2
      wsPts = cons(cadr(wsRowP) wsPts))
    wsPts = reverse(wsPts)
    wsCnt = length(wsPts)
    cond(
      (lessp(wsCnt 2) printf("  net %s: single terminal, not wired\n" wsNm))
      (t
        wsEd = wsMst(wsPts)
        printf("  net %s: %d terminals, %d wire edges\n" wsNm wsCnt length(wsEd))
        foreach(wsE wsEd
          wsP = nth(car(wsE) wsPts)
          wsQ = nth(cadr(wsE) wsPts)
          wsDd = wsDist(wsP wsQ)
          when(wsDd > 0.0
            wsOkE = wsRoute(cv wsP wsQ wsNm wsAll)
            ;; edge not drawn: try the other terminals of this net as the far end
            foreach(wsX wsPts
              when(and(null(wsOkE) wsDist(wsP wsX) > 0.0)
                wsOkE = wsRoute(cv wsP wsX wsNm wsAll)))
            when(null(wsOkE)
              printf("  UNRESOLVED %s: %L has no clear path to any other %s terminal; left as labels only\n" wsNm wsP wsNm))))))))

;; Restores schematic from schematic_bak (stub-only original), so every run starts clean.
;; Returns t when the restore worked.
procedure(wsRestore(wsCellName)
  let((wsBakCv wsRestOk)
    wsBakCv = dbOpenCellViewByType(wsLib wsCellName "schematic_bak" "schematic" "r")
    cond(
      (null(wsBakCv) printf("ERROR: no %s/schematic_bak to restore from\n" wsCellName) nil)
      (t
        wsRestOk = dbCopyCellView(wsBakCv wsLib wsCellName "schematic" nil nil t)
        dbClose(wsBakCv)
        printf("  restored %s/schematic from schematic_bak: %s\n" wsCellName if(wsRestOk then "OK" else "FAILED"))
        wsRestOk))))

;; Wires one cell. Returns t on success.
procedure(wsCell(wsCellName)
  let((wsCv wsRows wsNms wsOk)
    wsOk = nil
    printf("\n== WIRE %s/%s/schematic\n" wsLib wsCellName)
    cond(
      (null(wsRestore(wsCellName)) nil)
      (t
        wsCv = dbOpenCellViewByType(wsLib wsCellName "schematic" "schematic" "a")
        wsOk = wsWireCv(wsCv wsCellName)))
    wsOk))

;; Label points of a cellview as list(netName point).
procedure(wsLabelsOf(wsCv)
  let((wsAcc wsLb)
    wsAcc = nil
    foreach(wsS wsCv~>shapes
      when(equal(car(errset(wsS~>objType t)) "label")
        wsLb = car(errset(wsS~>theLabel t))
        when(stringp(wsLb)
          wsAcc = cons(list(wsLb car(errset(wsS~>xy t))) wsAcc))))
    wsAcc))

;; Draws every net of an open cellview, checks it, saves it.
procedure(wsWireCv(wsCv wsCellName)
  let((wsRows wsNms wsOk wsAll wsRowQ)
    wsOk = nil
    wsDrawn = nil
    cond(
      (null(wsCv) printf("ERROR: cannot open %s/%s/schematic for edit\n" wsLib wsCellName) nil)
      (t
        wsRows = append(wsRowsOf(wsCv) wsPinRowsOf(wsCv))
        wsNms = wsNamesOf(wsRows)
        wsAll = nil
        foreach(wsRowQ wsRows
          wsAll = cons(list(car(wsRowQ) cadr(wsRowQ)) wsAll))
        wsAll = append(wsAll wsLabelsOf(wsCv))
        printf("  %d terminals on %d nets, %d label points\n" length(wsRows) length(wsNms) length(wsAll))
        foreach(wsNmX wsNms
          unless(member(wsNmX wsSkipNets)
            wsNet(wsCv wsNmX wsRows wsAll)))
        printf("  schCheck %s: %L\n" wsCellName car(errset(schCheck(wsCv) t)))
        when(wsSave
          dbSave(wsCv)
          printf("  saved %s/%s/schematic\n" wsLib wsCellName))
        dbClose(wsCv)
        wsOk = t))
    wsOk))

;; ------------------------------ entry point ----------------------------

procedure(wireSchematicsMain()
  let((wsDone)
    wsDone = t
    foreach(wsCellX wsCells
      unless(wsCell(wsCellX) wsDone = nil))
    printf("== WIRE SCHEMATICS %s\n" if(wsDone then "DONE" else "FINISHED WITH ERRORS"))
    wsDone))
