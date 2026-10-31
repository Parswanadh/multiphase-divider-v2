#!/bin/bash
# Runs inside the Cadence VM (CentOS 6.5, python 2.6). Usage: run_gpdk045.sh <workdir> [one|pvt|grid]
# Needs divider_gpdk45.scs and measure_guest.py in <workdir>.
# Output: out/summary.tsv (one measured row per run), out/<tag>.log, out/tt_27_1.0.raw (kept for plots, mode one).
# Other raw waveforms are deleted right after being measured: the guest disk has only ~100 MB free.
# Operating point (override by environment): FIN RL VB CL ; grid mode sweeps FINS RLS VBS CLS.
cd "$1" || exit 1; MODE=${2:-one}; mkdir -p out
FIN=${FIN:-1G}; RL=${RL:-8k}; VB=${VB:-0.8}; CL=${CL:-10f}; MULT=${MULT:-1}
rm -f out/summary.tsv
runx() { # tag corner temp vdd fin rl vb cl mult
  tag=$1; c=$2; t=$3; v=$4; f=$5; r=$6; b=$7; l=$8; m=$9
  sed -e "s/section=tt/section=$c/" -e "s/temp=27 tnom=27/temp=$t tnom=27/" \
      -e "s/^parameters .*/parameters vdd=$v fin=$f tck=1\/fin tr=20p cl=$l rl=$r vb=$b mult=$m/" \
      -e "s/^ic .*/ic Q1=$v Q1b=0 Q2=$v Q2b=0 Q3=0 Q3b=$v Q4=0 Q4b=$v/" \
      divider_gpdk45.scs > out/$tag.scs
  spectre out/$tag.scs -format nutascii -raw out/$tag.raw +log out/$tag.log > /dev/null 2>&1
  rc=$?
  if [ -s out/$tag.raw ]; then
    [ -f out/summary.tsv ] || python measure_guest.py out/$tag.raw $v 2>/dev/null | head -1 > out/summary.tsv
    python measure_guest.py out/$tag.raw $v 2>/dev/null | tail -n +2 >> out/summary.tsv
  else
    printf "%s\tERROR\tno raw produced (spectre exit %s)\n" "$tag" "$rc" >> out/summary.tsv
  fi
  echo "$tag spectre_exit=$rc"
  [ "$tag" = "tt_27_1.0" ] || [ -n "$KEEP" ] || rm -f out/$tag.raw
  [ -n "$KEEP" ] && [ -f oppoint.txt ] && cp oppoint.txt out/$tag.oppoint
  rm -rf $tag.ahdlSimDB core*
}
case $MODE in
  one) runx tt_27_1.0 tt 27 1.0 $FIN $RL $VB $CL $MULT ;;
  pvt) for c in tt ff ss fs sf; do for t in -40 27 125; do for v in 0.9 1.0 1.1; do
         runx ${c}_${t}_${v} $c $t $v $FIN $RL $VB $CL $MULT; done; done; done ;;
  grid) for f in ${FINS:-$FIN}; do for r in ${RLS:-$RL}; do for b in ${VBS:-$VB}; do for l in ${CLS:-$CL}; do for m in ${MULTS:-$MULT}; do
         runx g_${f}_${r}_${b}_${l}_m${m} tt 27 1.0 $f $r $b $l $m; done; done; done; done; done ;;
esac
echo ALLDONE
