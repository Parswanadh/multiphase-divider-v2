;; lxl_flow.il -- Layout XL "Generate All From Source" flow for divider_lib/DLATCH
;; Companion notes: LXL_FLOW_NOTES.md (each call cites the IC615 6.1.5 doc heading)
;; STATUS: run in batch Virtuoso 6.1.5 (guest) on divider_lib/DLATCH and divider_core.
;;   DLATCH: lxGenFromSource -> layout_lxl OK (28 nmos1v = 7 x m4 split, 9 pins).
;;           R1, R2 NOT generated (no layout master for analogLib res). See results/gpdk045/lxl_dlatch_readback.txt
;;   divider_core: lxGenFromSource -> layout_lxl OK (4 DLATCH instances, 13 pins).
;;   Placement does NOT run in batch: lxHiMoveAutomatically and lxHiAutoPlace need a window;
;;   vcpfeRunCustomDigitalPlacer was not run with real cellviews (test called with nil args).
;;   Log excerpts: results/gpdk045/lxl_flow_log.txt
;;
;; Load in CIW (or in a startup file):
;;   load("/home/parshu/projects/multiphase-divider-v2/cadence/skill/auto/lxl_flow.il")
;;   lxlRunFlow()
;;
;; Batch: verified in this VM with "virtuoso -nograph -replay" via skill_run.sh (guest log).
;;   The IC615 docs do not mention the flags; the run is the evidence.
;;   Run as a replay file: load("<copy of lxl_flow.il>") then set lxlCell if needed, then lxlRunFlow().
;;
;; SKILL notes: defvar values are reassigned every time this file is loaded, so edit
;; the defvar lines below and reload. Variables are prefixed lxl; no x, y, t, i.
;; Names of core-SKILL helpers (errset, progn, printf, foreach, if, let, equal) are not
;; in the IC615 copies; they are standard SKILL. VERIFY the errset return shape.

;; ---------------------------------------------------------------- settings
defvar(lxlLib      "divider_lib")    ;; verified (library used in batch run)
defvar(lxlCell     "DLATCH")         ;; verified cell name (divider_lib/DLATCH); set lxlCell after load() for divider_core
defvar(lxlSchView  "schematic")      ;; source view (sklayoutref/chap2.html: 'lxGenFromSource', example)
defvar(lxlLayView  "layout_lxl")     ;; NEW view. Do NOT use "layout": Generate All From Source deletes
                                     ;; the existing components (vxlhelp/chap6.html: 'Generating All Components from Source')
defvar(lxlDoPas    nil)              ;; Place As In Schematic = lxHiMoveAutomatically(), a window command
                                     ;; (sklayoutref/chap2.html: 'lxHiMoveAutomatically'). GUI only.
defvar(lxlDoPlace  nil)              ;; vcpfeRunCustomDigitalPlacer, GXL token (vlsgxl/chap1.html: 'GXL Applications')
defvar(lxlDoMovePorts nil)           ;; lxMovePorts (sklayoutref/chap6.html: 'lxMovePorts')
defvar(lxlDoCompare nil)             ;; lxRunCmdInVXL comparison report (sklayoutref/chap2.html: 'lxRunCmdInVXL')
defvar(lxlIgnoreR   t)               ;; ignore schematic r on generation (vxlhelp/appA.html: 'paramsToIgnore')

defvar(lxlCtxFile "/home/buet/cadence/IC615/tools.lnx86/dfII/etc/context/lx.cxt")  ;; guest path; loadContext("lx") fails ("could not open file")

;; ---------------------------------------------------------------- helpers
;; errset returns a list holding the value, or nil on error. lxlGot returns the value.
procedure(lxlGot(lxlRes)
  if(lxlRes then car(lxlRes) else nil)
)

;; Print the marker line. lxlOk is any non-nil value for success.
procedure(lxlReport(lxlN lxlOk lxlWhat)
  if(lxlOk
     then printf("LXL step %d ok: %s\n" lxlN lxlWhat)
     else printf("LXL step %d failed: %s (read the CIW error above)\n" lxlN lxlWhat)
  )
)

procedure(lxlSkip(lxlN lxlWhy)
  printf("LXL step %d skipped: %s\n" lxlN lxlWhy)
)

;; ---------------------------------------------------------------- steps
;; Step 0: load the Layout XL SKILL context. Without it lxGenFromSource and the other lx*
;; functions are unbound (fboundp nil) in batch. Verified: loadContext with the full path returns (t).
procedure(lxlStep0LoadCtx()
  let((lxlR)
    lxlR = errset(loadContext(lxlCtxFile) t)
    lxlReport(0 lxlR "Layout XL context lx.cxt loaded")
  )
)

;; Step 1: options that control generation. Set before generating.
;; envSetVal form: vxlhelp/chap1.html: 'Setting Environment Variables in the CIW'
;; Variable names: vxlhelp/appA.html (lxEvalCDFCallbacks, lxGenerateInBoundary, mfactorSplit,
;; lxFingeringNames, paramsToIgnore).
procedure(lxlStep1SetEnv()
  let((lxlR)
    lxlR = errset(progn(
      envSetVal("layoutXL" "lxEvalCDFCallbacks" 'boolean t)       ;; needed for nmos1v width/fingers callbacks
      envSetVal("layoutXL" "lxGenerateInBoundary" 'boolean t)     ;; generate inside the PR boundary
      envSetVal("layoutXL" "mfactorSplit" 'boolean t)             ;; m=4 becomes instName.1..4
      envSetVal("layoutXL" "lxFingeringNames" 'string "fingers finger numFingers numFinger")
      envSetVal("layoutXL" "paramsToIgnore" 'string if(lxlIgnoreR then "r" else ""))  ;; VERIFY: r on res not in pcell
    ) t)
    lxlReport(1 lxlR "layoutXL env vars set")
  )
)

;; Step 2: open the schematic source by database ID.
;; dbOpenCellViewByType(lib cell view) is the 3-argument form in sklayoutref/chap2.html: 'lxGenFromSource' example.
procedure(lxlStep2OpenSource()
  let((lxlR lxlCv)
    lxlR = errset(dbOpenCellViewByType(lxlLib lxlCell lxlSchView))
    lxlCv = lxlGot(lxlR)
    lxlReport(2 lxlCv sprintf(nil "opened %s/%s/%s" lxlLib lxlCell lxlSchView))
    lxlCv
  )
)

;; Step 3: generate the layout from the schematic.
;; Argument names: sklayoutref/chap2.html: 'lxGenFromSource' (Arguments list).
;; Values marked VERIFY are choices, not doc-confirmed defaults.
procedure(lxlStep3Generate(lxlSchCv)
  let((lxlR lxlLay)
    lxlR = errset(lxGenFromSource(lxlSchCv
        ?layViewName lxlLayView          ;; new view, see defvar lxlLayView
        ?initCreateInstances t           ;; Generate tab: Instances (vxlhelp/chap6.html: 'Specifying the Components to be Generated')
        ?initCreatePins t                ;; I/O pins
        ?initCreateBoundary t            ;; PR boundary (vxlhelp/chap6.html: 'Specifying the Place and Route Boundary')
        ?initDoStacking nil              ;; chaining OFF. VERIFY: nmos chaining wanted or not
        ?initDoFolding nil               ;; folding OFF. VERIFY
        ?initPrBoundaryShape "Rectangle" ;; guest log (LX-2052): value must be 'Rectangle' or 'Polygon'
        ?initPrBoundaryOrigin list(0.0 0.0)  ;; must be floats (guest: "ilGetDouble: arg must be flonum - 0")
        ?lxGenerateInBoundary t          ;; (vxlhelp/appA.html: 'lxGenerateInBoundary')
        ?extractAfterGenerateAll t       ;; extract after generation
        ?extractSchematic t))            ;; allow schematic extraction if needed
    lxlLay = lxlGot(lxlR)
    lxlReport(3 lxlLay sprintf(nil "lxGenFromSource -> view %s" lxlLayView))
    lxlLay
  )
)

;; Step 4: explicit save. sklayoutref/chap2.html says: "You must perform an explicit dbSave"
;; after lxGenFromSource. dbSave signature NOT IN DOCS (example use only). VERIFY.
procedure(lxlStep4Save(lxlLay)
  let((lxlR)
    if(lxlLay
      then lxlR = errset(dbSave(lxlLay))
           lxlReport(4 lxlR "dbSave of generated layout")
      else lxlSkip(4 "no layout cellview from step 3")
    )
  )
)

;; Step 5: confirm the layout points at the schematic we generated from.
;; sklayoutref/chap2.html: 'lxGetLXInfo' example: lxGetLXInfo("srcView" cvId)
;; GUEST RESULT: lxGetLXInfo("srcView" layCv) returns nil on both DLATCH and divider_core, so this
;; check currently FAILS. Its meaning is unverified; the source is the schematic by construction.
procedure(lxlStep5CheckSource(lxlLay lxlSchCv)
  let((lxlR lxlSrc)
    if(lxlLay
      then lxlR = errset(lxGetLXInfo("srcView" lxlLay) t)
           lxlSrc = lxlGot(lxlR)
           printf("LXL step 5 lxGetLXInfo srcView -> %L\n" lxlSrc)
           lxlReport(5 and(lxlSrc equal(lxlSrc lxlSchCv)) "layout source == schematic")
      else lxlSkip(5 "no layout cellview")
    )
  )
)

;; Step 6: list the generated instances (name and master). Print for inspection.
;; GUEST RESULT: ~>instances, ~>name, ~>cellName work on layout instances (verified, DLATCH and core).
procedure(lxlStep6List(lxlLay)
  let((lxlR)
    if(lxlLay
      then lxlR = errset(
             foreach(lxlInst lxlLay~>instances
               printf("LXL inst %s master=%s\n" lxlInst~>name lxlInst~>master~>cellName)) t)
           lxlReport(6 lxlR "instance list printed")
      else lxlSkip(6 "no layout cellview")
    )
  )
)

;; Step 7 (optional, GUI window command): Place As In Schematic.
procedure(lxlStep7Pas()
  let((lxlR)
    if(lxlDoPas
      then lxlR = errset(lxHiMoveAutomatically())   ;; needs the current layout window
           lxlReport(7 lxlR "Place As In Schematic (lxHiMoveAutomatically)")
      else lxlSkip(7 "lxlDoPas is nil")
    )
  )
)

;; Step 8 (optional, GXL token): custom digital placer, no form.
;; Signature: sklayoutref/chap6.html: 'vcpfeRunCustomDigitalPlacer'. Only the two required
;; IDs are passed; every other argument falls back to its environment variable.
procedure(lxlStep8Place(lxlSchCv lxlLay)
  let((lxlR)
    if(and(lxlDoPlace lxlLay)
      then lxlR = errset(vcpfeRunCustomDigitalPlacer(lxlSchCv lxlLay ?globalPlacement t))  ;; VERIFY GXL license
           lxlReport(8 lxlR "custom digital placer (GXL)")
      else lxlSkip(8 "lxlDoPlace nil or no layout")
    )
  )
)

;; Step 9 (optional): move top-level ports over components. sklayoutref/chap6.html: 'lxMovePorts'.
procedure(lxlStep9Ports(lxlLay)
  let((lxlR)
    if(and(lxlDoMovePorts lxlLay)
      then lxlR = errset(lxMovePorts(lxlLay))
           lxlReport(9 lxlR "lxMovePorts")
      else lxlSkip(9 "lxlDoMovePorts nil or no layout")
    )
  )
)

;; Step 10 (optional, batch-callable comparison). The doc example is:
;;   lxRunCmdInVXL(lcv 'ciLxComparisonReport list(?layoutCV lcv ?showReport nil ?useViewNames t ?useTimeStamp t))
;; sklayoutref/chap2.html: 'lxRunCmdInVXL'. VERIFY the argument form.
procedure(lxlStep10Compare(lxlLay)
  let((lxlR)
    if(and(lxlDoCompare lxlLay)
      then lxlR = errset(lxRunCmdInVXL(lxlLay 'ciLxComparisonReport
                     list(?layoutCV lxlLay ?showReport nil ?useViewNames t ?useTimeStamp t)))  ;; VERIFY
           lxlReport(10 lxlR "lxRunCmdInVXL comparison")
      else lxlSkip(10 "lxlDoCompare nil or no layout")
    )
  )
)

;; Step 11: final save.
procedure(lxlStep11Save(lxlLay)
  let((lxlR)
    if(lxlLay
      then lxlR = errset(dbSave(lxlLay))
           lxlReport(11 lxlR "final dbSave")
      else lxlSkip(11 "no layout cellview")
    )
  )
)

;; ---------------------------------------------------------------- driver
procedure(lxlRunFlow()
  let((lxlSchCv lxlLay)
    lxlStep0LoadCtx()
    lxlStep1SetEnv()
    lxlSchCv = lxlStep2OpenSource()
    if(lxlSchCv
      then lxlLay = lxlStep3Generate(lxlSchCv)
           lxlStep4Save(lxlLay)
           lxlStep5CheckSource(lxlLay lxlSchCv)
           lxlStep6List(lxlLay)
           lxlStep7Pas()
           lxlStep8Place(lxlSchCv lxlLay)
           lxlStep9Ports(lxlLay)
           lxlStep10Compare(lxlLay)
           lxlStep11Save(lxlLay)
           printf("LXL flow finished. Layout view: %s/%s/%s\n" lxlLib lxlCell lxlLayView)
      else printf("LXL flow stopped: schematic could not be opened\n")
    )
  )
)
