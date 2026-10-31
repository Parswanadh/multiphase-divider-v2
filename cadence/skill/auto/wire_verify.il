;; wire_dump.il : backup and connectivity dump helpers (used by phase files)
procedure(wbBackup(wbCell)
  let((wbObj wbCv wbR)
    wbObj = ddGetObj("divider_lib" wbCell "schematic_bak")
    cond(
      (wbObj printf("== BACKUP %s: schematic_bak already exists, not overwritten\n" wbCell))
      (t
        wbCv = dbOpenCellViewByType("divider_lib" wbCell "schematic" "schematic" "r")
        wbR = dbCopyCellView(wbCv "divider_lib" wbCell "schematic_bak" nil nil nil)
        dbClose(wbCv)
        printf("== BACKUP %s -> schematic_bak: %s\n" wbCell if(wbR then "OK" else "FAILED"))))
  )
)

procedure(wdNetOf(wdTm)
  let((wdNt)
    wdNt = car(errset(wdTm~>net~>name t))
    if(stringp(wdNt) then wdNt else "NONE")
  )
)

procedure(wdDumpCell(wdCell wdDir wdTag)
  let((wdCv wdFh wdShF wdCdf)
    wdCv = dbOpenCellViewByType("divider_lib" wdCell "schematic" "schematic" "r")
    wdFh = outfile(strcat(wdDir "/" wdTag "_" wdCell "_conn.txt") "w")
    wdShF = outfile(strcat(wdDir "/" wdTag "_" wdCell "_shapes.txt") "w")
    foreach(wdI wdCv~>instances
      fprintf(wdFh "INST %s %s/%s\n" wdI~>name car(errset(wdI~>libName t)) car(errset(wdI~>cellName t)))
      wdCdf = car(errset(cdfGetInstCDF(wdI) t))
      when(wdCdf
        foreach(wdP wdCdf->parameters
          fprintf(wdFh "PARAM %s %s=%L\n" wdI~>name wdP->name wdP->value)))
      foreach(wdT wdI~>instTerms
        fprintf(wdFh "CONN %s %s.%s\n" wdNetOf(wdT) wdI~>name wdT~>name)))
    foreach(wdS wdCv~>shapes
      fprintf(wdShF "%s\n" car(errset(wdS~>objType t))))
    close(wdFh)
    close(wdShF)
    dbClose(wdCv)
    printf("== DUMP %s (%s) written to %s\n" wdCell wdTag wdDir)
  )
)
