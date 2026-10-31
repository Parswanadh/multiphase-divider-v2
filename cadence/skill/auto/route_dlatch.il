;; =========================================================================
;; route_dlatch.il - automatic routing of divider_lib/DLATCH with the
;; built-in Virtuoso Chip Assembly Router (vcar, launched by leStartRouter).
;; Load in CIW:  load("/abs/path/cadence/skill/auto/route_dlatch.il")
;; Run:          routeDlatchMain()
;; Batch:        skill_run.sh route_dlatch.il  (see ROUTER_NOTES.md)
;;
;; Tags: [V] verified by a run in this VM, [D] from the IC615 docs only,
;;       [VERIFY] not yet confirmed.
;; No per-wire coordinates anywhere. Only names are set below.
;;
;; Flow:
;;  1. Preflight: vcar reads the source view (no save) and reports the
;;     net/connection count. If there are 0 connections, the router has
;;     nothing to route and the script STOPS (no routed view is written).
;;  2. Otherwise writes a router command file (groute, troute, droute,
;;     check) and runs leStartRouter: source view -> routed view.
;;  The source view is never saved by this script.
;; =========================================================================

;; ------------------------------ parameters -----------------------------
defvar(rdLib        "divider_lib")       ; [V] library holding the DLATCH cell
defvar(rdCell       "DLATCH")            ; [V] cell to route
defvar(rdSrcView    "layout")            ; [V] placement-only view (not modified)
defvar(rdRoutedView "layout_routed")     ; [V] output view created by the router
defvar(rdWorkDir    "/home/buet/gpdk_run/rt")         ; scratch dir in the guest
defvar(rdVcar       "/home/buet/cadence/IC615/tools/iccraft/bin/vcar")  ; [V] router binary (leStartRouter runs it)
defvar(rdCmdFile    "/home/buet/gpdk_run/rt/route_dlatch.vcar")         ; router command file (written here)
defvar(rdPreFile    "/home/buet/gpdk_run/rt/preflight.vcar")            ; preflight command file (written here)
defvar(rdCdDir      "/home/buet/cds_work")  ; directory with cds.lib (vcar must run here)
defvar(rdRouteCmds  list("groute" "troute" "droute" "check (type all)"))  ; [D] iccausr/chap6 + rderef; droute name [VERIFY]

;; ------------------------------ helpers --------------------------------
procedure(rdWriteCmds(path lines)
  let((rdFh)
    rdFh = outfile(path "w")
    foreach(rdL lines fprintf(rdFh "%s\n" rdL))
    close(rdFh)
    t
  )
)

;; Preflight: runs vcar on the source view without saving and returns t
;; when the design has at least one connection to route.
procedure(rdHasConnections()
  let((rdRc)
    rdWriteCmds(rdPreFile list("check (type all)" "groute"))
    rdRc = system(strcat("cd " rdCdDir " && timeout 150 " rdVcar
              " -lib " rdLib " -cell " rdCell " -view " rdSrcView
              " -do " rdPreFile " -nog -quit -noinit -nodid > " rdWorkDir "/preflight.log 2>&1"))
    printf("== route_dlatch: preflight vcar exit=%L\n" rdRc)
    ;; grep for a Nets line with Connections >= 1
    0 == system(strcat("grep -E 'Nets [0-9]+ Connections [1-9]' " rdWorkDir "/preflight.log > /dev/null"))
  )
)

;; ------------------------------ main -----------------------------------
procedure(routeDlatchMain()
  let((rdFound rdRes)
    printf("== route_dlatch: %s/%s  %s -> %s\n" rdLib rdCell rdSrcView rdRoutedView)
    rdFound = isCallable('leStartRouter)
    printf("== route_dlatch: leStartRouter callable = %L\n" rdFound)
    cond(
      (null(rdFound)
        printf("BLOCKED: leStartRouter is not defined in this session.\n")
        nil)
      (null(rdHasConnections())
        printf("BLOCKED: router preflight found 0 connections in %s/%s/%s.\n" rdLib rdCell rdSrcView)
        printf("         The placement-only view has no net connectivity on device terminals,\n")
        printf("         so no routing is attempted and %s is not written.\n" rdRoutedView)
        nil)
      (t
        rdWriteCmds(rdCmdFile rdRouteCmds)
        rdRes = leStartRouter(
          ?layoutLCV list(rdLib rdCell rdSrcView)
          ?layoutRoutedLCV list(rdLib rdCell rdRoutedView)
          ?showGraphics nil
          ?quitAtFinish t
          ?createDidFile nil
          ?useStartupFiles nil
          ?checkAtStartup nil
          ?doFile rdCmdFile
          ?statusFile strcat(rdWorkDir "/route_status.txt"))
        printf("== route_dlatch: leStartRouter returned %L\n" rdRes)
        rdRes)
    )
  )
)

printf("route_dlatch.il loaded. Run routeDlatchMain().\n")
