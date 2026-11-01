;; parametrize_tb.il
;; Batch Virtuoso (run with skill_run.sh). Makes the tb_divider testbench sources read the
;; OCEAN design variables used by pvt_sweep.ocn: VDD, tbVbias (NBIAS), tbPeriod (CK period).
;; Before the edit the schematic held literal values (vdc=1, vdc=800m, per=1n, td=500p, pw=480p),
;; so desVar() had no effect on the netlist. Expressions are written into the CDF of each instance.
;; The DLATCH resistors (3K) and device multipliers (m=4) are left as literal values.
;; A backup of the cell is taken first: system("cp -r ...") in the guest.

procedure(pvtSetParam(cv nm pname val)
  let((i cdf p)
    i = car(setof(x cv~>instances equal(x~>name nm)))
    unless(i error("parametrize_tb: no instance %s" nm))
    cdf = cdfGetInstCDF(i)
    p = cdfFindParamByName(cdf pname)
    unless(p error("parametrize_tb: no CDF param %s on %s" pname nm))
    p~>value = val
    printf("SET %s.%s = %s\n" nm pname val)
    t))

system("rm -rf /home/buet/gpdk_run/ocean_pvt/bak_tb_divider")
system("cp -r /home/buet/cds_work/divider_lib/tb_divider /home/buet/gpdk_run/ocean_pvt/bak_tb_divider")
cvTb = dbOpenCellViewByType("divider_lib" "tb_divider" "schematic" "schematic" "a")
pvtSetParam(cvTb "VB" "vdc" "tbVbias")
pvtSetParam(cvTb "VDD" "vdc" "VDD")
pvtSetParam(cvTb "VCK" "per" "tbPeriod")
pvtSetParam(cvTb "VCK" "pw" "tbPeriod/2-20p")
pvtSetParam(cvTb "VCKB" "per" "tbPeriod")
pvtSetParam(cvTb "VCKB" "td" "tbPeriod/2")
pvtSetParam(cvTb "VCKB" "pw" "tbPeriod/2-20p")
dbSave(cvTb)
dbClose(cvTb)
printf("PARAMETRIZE_DONE\n")
