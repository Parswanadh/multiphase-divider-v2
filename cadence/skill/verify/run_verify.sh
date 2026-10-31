#!/bin/bash
# Re-runnable Assura physical verification for the gpdk045 divider (host side).
# usage: run_verify.sh CELL drc|lvs|rcx
#   Fills templates/<stage>.rsf.in, ships the RSF to the Cadence VM on a virtual CD, and runs
#   Assura in batch (`assura <rsf>`, cds_work) in the guest. Every VM call runs under the shared lock.
# Guest outputs: /home/buet/verify/<CELL>_<STAGE>/ (run dir, recreated before each run) and the
# Assura console log ~/gpdk_run/verify/<CELL>_<STAGE>.out. Nothing is written into the repo.
# Examples: ./run_verify.sh DLATCH lvs ; EXTRA='layout( deleteCellPin("g45rnsnp" "B") )' RUNTAG=_pinB ./run_verify.sh DLATCH lvs
set -euo pipefail
if [ -z "${VERIFY_LOCKED:-}" ]; then
  exec env VERIFY_LOCKED=1 flock /home/parshu/vm/vm.lock "$0" "$@"
fi
CELL="${1:?usage: run_verify.sh CELL drc|lvs|rcx}"
STAGE="${2:?usage: run_verify.sh CELL drc|lvs|rcx}"
LIB=divider_lib                         # the only place the design library is named
case "$CELL" in *[!A-Za-z0-9_]*|"") echo "bad CELL: $CELL" >&2; exit 2;; esac
case "$STAGE" in drc|lvs|rcx) ;; *) echo "bad STAGE: $STAGE (drc|lvs|rcx)" >&2; exit 2;; esac
HERE=$(cd "$(dirname "$0")" && pwd)
D=/home/parshu/vm
# optional: EXTRA="<avCompareRule>" is inserted into the LVS RSF; RUNTAG names a variant run
EXTRA="${EXTRA:-}"
RUN="${CELL}_${STAGE}${RUNTAG:-}"
WORK="/home/buet/verify/$RUN"
# LVS: aveng needs the schematic VLDB file to exist; dfIIToVldb fills it from the RSF
# (same call the Assura GUI makes). An empty file is created first, which dfIIToVldb takes as output.
PRE=""; VLRCP=""
if [ "$STAGE" = lvs ]; then
  VLRCP="cp -f ~/gpdk_run/verify/$RUN.vlr $WORK/ && "
  PRE="dfIIToVldb -cdslib /home/buet/cds_work/cds.lib $WORK/$RUN.vlr ~/gpdk_run/verify/$RUN.rsf > ~/gpdk_run/verify/$RUN.vlr.out 2>&1; "
fi
ST=$(mktemp -d /tmp/verify_stage_XXXXXX)
fill() { sed -e "s|@LIB@|$LIB|g" -e "s|@CELL@|$CELL|g" -e "s|@WORK@|$WORK|g" -e "s|@RUN@|$RUN|g" -e "s|@EXTRA@|$EXTRA|g" "$1"; }
fill "$HERE/templates/$STAGE.rsf.in" > "$ST/$RUN.rsf"
if [ "$STAGE" = lvs ]; then fill "$HERE/templates/netlist.vlr.in" > "$ST/$RUN.vlr"; fi
N=$(date +%s); MED=$D/verify_$N; mkdir -p "$MED"; cp "$ST"/$RUN.* "$MED/"
xorriso -as mkisofs -quiet -r -J -V V$N -o $D/v_$N.iso "$MED" 2>/dev/null
VBoxManage storageattach CadenceVM --storagectl IDE --port 0 --device 0 --type dvddrive \
  --medium $D/v_$N.iso --forceunmount >/dev/null 2>&1; sleep 4
GUEST="sudo umount /mnt/r 2>/dev/null; sudo mount -t iso9660 -o ro /dev/sr0 /mnt/r && mkdir -p ~/gpdk_run/verify && cp -f /mnt/r/$RUN.* ~/gpdk_run/verify/ && rm -rf $WORK /dev/shm/$RUN && mkdir -p $WORK && ${VLRCP}cd ~/cds_work && ${PRE}env TMPDIR=/dev/shm timeout 900 assura ~/gpdk_run/verify/$RUN.rsf > ~/gpdk_run/verify/$RUN.out 2>&1; echo ASSURA_EXIT=\$?; ls $WORK | wc -l; df -h / | tail -1"
"$D/vmx.sh" "$GUEST" 1000
echo "--- guest log tail for $RUN (staged in $ST) ---"
"$D/vmx.sh" "tail -n ${TAILN:-40} ~/gpdk_run/verify/$RUN.out | tr -cd '\11\12\40-\176' | cut -c1-200" 60
