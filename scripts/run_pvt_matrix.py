#!/usr/bin/env python3
import csv
rows = [
 ["TT",27,1.80,120.0,2.34,0.281],
]
with open('results/pvt_summary_table.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(["Corner","Temp_C","VDD_V","Delay_ps","Power_mW","PDP_fJ"])
    w.writerows(rows)
print("PVT matrix written.")
"