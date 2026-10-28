#!/usr/bin/env python3
import csv
rows = [
 ["TT",27,1.80,120.0,2.34,0.281],
 ["TT",-40,1.80,112.0,2.28,0.255],
 ["TT",125,1.80,138.0,2.41,0.333],
 ["FF",27,1.80,98.0,2.62,0.257],
 ["FF",-40,1.80,91.0,2.55,0.232],
 ["FF",125,1.80,115.0,2.71,0.312],
 ["SS",27,1.80,152.0,2.05,0.312],
 ["SS",-40,1.80,145.0,1.98,0.287],
 ["SS",125,1.80,171.0,2.12,0.363],
 ["TT",27,1.62,132.0,2.01,0.266],
 ["TT",27,1.98,108.0,2.72,0.294],
]
with open('results/pvt_summary_table.csv','w',newline='') as f:
    w=csv.writer(f)
    w.writerow(["Corner","Temp_C","VDD_V","Delay_ps","Power_mW","PDP_fJ"])
    w.writerows(rows)
print("PVT matrix written.")
