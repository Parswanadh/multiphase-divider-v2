#!/usr/bin/env python3
"""Concatenate guide/frag/*.html into guide/cadence_gpdk45_guide.html using guide/shell.html."""
import pathlib, sys
g = pathlib.Path(__file__).parent
order = ["A_overview_setup", "E_cadence101", "D_findings", "B_schematic_sim", "C_layout_report"]
body = "\n".join((g / "frag" / f"{n}.html").read_text() for n in order)
out = (g / "shell.html").read_text().replace("<!--CONTENT-->", body)
(g / "cadence_gpdk45_guide.html").write_text(out)
print("built", len(out.splitlines()), "lines")
