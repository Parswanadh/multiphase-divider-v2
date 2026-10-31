;; =========================================================================
;; route_dlatch.il - automatic routing of divider_lib/DLATCH with the
;; built-in Virtuoso Chip Assembly Router (vcar).
;; Load in CIW:  load("/abs/path/cadence/skill/auto/route_dlatch.il")
;; Run:          routeDlatchMain()
;; Batch:        replay file calls routeDlatchMain() (see ROUTER_NOTES.md section 7)
;;
;; Tags: [V] verified by a run in this VM, [D] from the IC615 docs only,
;;       [VERIFY] not yet confirmed.
;; No per-wire coordinates anywhere. Only names are set below.
;;
;; Flow:
;;  0. Delete ONLY the named scratch views (literal names) and the old routed view.
;;  1. Overlap check on the source view (instance bBox pairs). Printed only.
;;  2. Preflight: vcar reads the source view (no save) and reports the
;;     net/connection count. If there are 0 connections, STOP.
;;  3. Standalone vcar run (system()) on the source view: groute, troute, route,
;;     check, then "save_oa as <rdRoutedView>" (IC615 docs: save_oa [export] [as <new_view>]).
;;     leStartRouter was NOT used: in batch its save back to Virtuoso timed out
;;     ("cdsServIpc: connection timeout"), so no routes were written.
;;  4. Reopen the routed view in SKILL and print its counts.
;; The source view is never saved by this script. "layout" is never touched.
;; =========================================================================

;; ------------------------------ parameters -----------------------------
defvar(rdLib        "divider_lib")       ; [V] library holding the DLATCH cell
defvar(rdCell       "DLATCH")            ; [V] cell to route
defvar(rdSrcView    "layout_lxl")        ; [V] connected source view (Layout XL generate-from-source, 13403a2)
defvar(rdRoutedView "layout_routed")     ; [V] output view written by save_oa
defvar(rdWorkDir    "/home/buet/gpdk_run/rt")         ; scratch dir in the guest
defvar(rdVcar       "/home/buet/cadence/IC615/tools/iccraft/bin/vcar")  ; [V] router binary
defvar(rdCmdFile    "/home/buet/gpdk_run/rt/route_dlatch.vcar")         ; router command file (written here)
defvar(rdPreFile    "/home/buet/gpdk_run/rt/preflight.vcar")            ; preflight command file (written here)
defvar(rdCdDir      "/home/buet/cds_work")  ; directory with cds.lib (vcar must run here)
;; [V] groute, troute, route, check accepted by vcar. "route" = detail pass (droute/detailroute/dr rejected).
;; [D] save_oa as <view> from iccausr save_oa description.
defvar(rdRouteCmds  list("groute" "troute" "route" "check (type all)" strcat("save_oa as " rdRoutedView)))

;; ------------------------------ helpers --------------------------------
procedure(rdWriteCmds(path lines)
  let((rdFh)
    rdFh = outfile(path "w")
    foreach(rdL lines fprintf(rdFh "%s\n" rdL))
    close(rdFh)
    t
  )
)

;; Delete one scratch view of rdLib/rdCell. The name is passed as a literal
;; by the caller; nothing else in divider_lib is touched.
procedure(rdDeleteScratch(rdV)
  let((rdObj)
    rdObj = ddGetObj(rdLib rdCell rdV)
    cond(
      (null(rdObj) printf("== view %s/%s/%s not present\n" rdLib rdCell rdV))
      (t
        ddDeleteObj(rdObj)
        printf("== deleted view %s/%s/%s\n" rdLib rdCell rdV)))
  )
)

;; bBox of an instance as list(x1 y1 x2 y2), user units (um)
procedure(rdBox(rdI)
  let((rdB)
    rdB = rdI~>bBox
    list(car(car(rdB)) cadr(car(rdB)) car(cadr(rdB)) cadr(cadr(rdB)))
  )
)

;; Overlap of two instance boxes with positive area
procedure(rdOverlap(rdP rdQ)
  let((rdA rdC)
    rdA = rdBox(rdP)
    rdC = rdBox(rdQ)
    and(nth(0 rdA) < nth(2 rdC) nth(0 rdC) < nth(2 rdA)
        nth(1 rdA) < nth(3 rdC) nth(1 rdC) < nth(3 rdA))
  )
)

;; Count overlapping instance pairs in the source view; print each pair.
procedure(rdOverlapReport(rdCv)
  let((rdList rdN rdA rdB rdCnt)
    rdList = rdCv~>instances
    rdN = length(rdList)
    rdCnt = 0
    for(rdA 0 rdN - 1
      for(rdB rdA + 1 rdN - 1
        when(rdOverlap(nth(rdA rdList) nth(rdB rdList))
          rdCnt = rdCnt + 1
          printf("== overlap: %s %s\n" nth(rdA rdList)~>name nth(rdB rdList)~>name))))
    printf("== overlap pairs in %s = %d (of %d instances)\n" rdSrcView rdCnt rdN)
    rdCnt
  )
)

;; Preflight: vcar on the source view without saving; t when the design has
;; at least one connection to route.
procedure(rdHasConnections()
  let((rdRc)
    rdWriteCmds(rdPreFile list("check (type all)" "groute"))
    rdRc = system(strcat("cd " rdCdDir " && timeout 150 " rdVcar
              " -lib " rdLib " -cell " rdCell " -view " rdSrcView
              " -do " rdPreFile " -nog -nocheck -quit -noinit -nodid > " rdWorkDir "/preflight.log 2>&1"))
    printf("== route_dlatch: preflight vcar exit=%L\n" rdRc)
    0 == system(strcat("grep -E 'Nets [0-9]+ Connections [1-9]' " rdWorkDir "/preflight.log > /dev/null"))
  )
)

;; Standalone router run. Writes rdWorkDir/route.log. Returns the vcar exit code.
procedure(rdRunRouter()
  let((rdRc)
    rdWriteCmds(rdCmdFile rdRouteCmds)
    rdRc = system(strcat("cd " rdCdDir " && timeout 240 " rdVcar
              " -lib " rdLib " -cell " rdCell " -view " rdSrcView
              " -do " rdCmdFile " -nog -nocheck -quit -noinit -nodid > " rdWorkDir "/route.log 2>&1"))
    printf("== route_dlatch: vcar exit=%L (log %s/route.log)\n" rdRc rdWorkDir)
    rdRc
  )
)

;; ------------------------------ main -----------------------------------
procedure(routeDlatchMain()
  let((rdSrcCv rdOv rdRouted rdRc)
    printf("== route_dlatch: %s/%s  %s -> %s\n" rdLib rdCell rdSrcView rdRoutedView)

    ;; step 0: scratch views from earlier tests, and the old routed view, by literal name
    rdDeleteScratch("layout_nets")
    rdDeleteScratch("layout_nets2")
    rdDeleteScratch("layout_routed")

    ;; step 1: overlap check on the source view
    rdSrcCv = dbOpenCellViewByType(rdLib rdCell rdSrcView nil "r")
    rdOv = rdOverlapReport(rdSrcCv)
    dbClose(rdSrcCv)

    ;; step 2 and 3
    cond(
      (null(rdHasConnections())
        printf("BLOCKED: router preflight found 0 connections in %s/%s/%s.\n" rdLib rdCell rdSrcView)
        nil)
      (t
        rdRc = rdRunRouter()
        ;; step 4: reopen the routed view and print its counts
        rdRouted = ddGetObj(rdLib rdCell rdRoutedView)
        cond(
          (null(rdRouted) printf("== route_dlatch: %s was NOT written\n" rdRoutedView) nil)
          (t
            rdRouted = dbOpenCellViewByType(rdLib rdCell rdRoutedView nil "r")
            printf("== route_dlatch: %s insts=%d shapes=%d\n" rdRoutedView length(rdRouted~>instances) length(rdRouted~>shapes))
            dbClose(rdRouted)
            rdRc))))
  )
)

printf("route_dlatch.il loaded. Run routeDlatchMain().\n")
