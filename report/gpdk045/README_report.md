# System Design Project Report generator (23ECE383 / 23ECE302)

`scripts/build_academic_docx.py` builds the college report as `.docx` and then `.pdf`
(via `libreoffice --headless --convert-to pdf`). The layout follows the official format
file: title page, section order and capitalised headings. Times New Roman, 12 pt body,
14 pt headings, US Letter, 1 inch margins, double page border, "Page X of Y" footer.

Nothing is invented. Content comes only from a JSON data file.

## Run

```
/home/parshu/vm/rv/bin/python scripts/build_academic_docx.py \
    --data report/gpdk045/report_data.json \
    --out  /path/to/output_dir        # docx and pdf are written here
    [--no-pdf]                        # only the .docx
```

The venv is outside the repo: `python3 -m venv /home/parshu/vm/rv && /home/parshu/vm/rv/bin/pip install python-docx pillow`.
The output file is `23ECE383_System_Design_Report.docx` (and `.pdf`).

`report_data.json` is your real data file. Keep it out of version control if it holds results you
have not published. Start from `report_data.example.json`, which is example-only.

## Data file schema

Relative paths (figures, logo) are resolved against the directory of the data file.

| Key | Type | Used for |
|---|---|---|
| `example_only` | bool | `true` adds a red "EXAMPLE DATA - NOT A RESULT" line at the top. |
| `logo` | path or null | Institution logo on the title page (the Amrita logo image). |
| `titles.system_design_project` | string | Title page and "TITLE OF THE SYSTEM DESIGN PROJECT". |
| `paper` | object | "TITLE OF THE PAPER" (`paper.title`) and "DETAILS OF THE PAPER": `authors`, `journal`, `volume`, `issue`, `pages`, `date`, `doi`. |
| `figures` | object | Figure slots, listed below. |
| `designs.without_sizing` / `designs.with_sizing` | object | `description` (string), `devices` (list), `metrics` (object). |
| `pvt_rows` | list | PVT table rows (see below). |
| `theory`, `tool_technology`, `other_info`, `conclusion`, `problems_faced`, `problems_resolved`, `other_comment`, `references` | list of strings | One paragraph per item. |

### figures

Each slot is `{"file": "<png or jpg>", "caption": "<text>"}` or `null`. Slots appear in this
order and are numbered `Figure 1` to `Figure 8`:

1. `circuit_diagram`
2. `impl_screenshot`
3. `waveform_without_sizing`
4. `sized_circuit_screenshot`
5. `waveform_with_sizing`
6. `pvt_screenshot`
7. `layout_screenshot`
8. `layout_waveform`

`extra_figures` is a list of the same objects. It is numbered 9, 10, and so on and appears
under "ANY OTHER RELEVANT INFORMATION". A `null` entry renders a NOT YET AVAILABLE line.

### designs.*.metrics

Keys, with the unit added automatically:

| Key | Unit | Row in the values table |
|---|---|---|
| `power_mw` | mW | Power calculation |
| `delay_ps` | ps | Delay calculation |
| `pdp_fj` | fJ | Power Delay Product |
| `f_in_ghz` | GHz | Input frequency |
| `f_out_mhz` | MHz | Output frequency |
| `max_phase_step_err_deg` | deg | Max phase-step error |
| `swing_v` | V | Output swing |
| `m7_vds_v`, `m7_vdsat_v` | V | Tail-device saturation check (saturated when Vds >= Vdsat) |

Any metric may be `null`, which renders `n/a`. The number is shown as entered, with no rounding.

Each row of the values table has a "Proof (figure)" column that cites the waveform figures
(`waveform_without_sizing` and `waveform_with_sizing`).

### designs.*.devices

List of `{"device", "w", "l", "multiplier", "role"}`. Null fields render `n/a`.

### pvt_rows

List of `{"corner", "temp", "vdd", "divides", "f_out_mhz", "delay_ps", "power_mw", "pdp_fj", "note"}`.
`divides` is `true` (PASS), `false` (FAIL, shown in red) or `null` (n/a). FAIL rows are kept.

## Rules

- A figure slot that is `null`, missing, or points to a missing file renders a bold red line
  `NOT YET AVAILABLE: Figure n - <what is needed>`. No placeholder image or number is ever created.
- A narrative list that is empty or missing renders the same kind of line.
- A metric or field that is `null` renders `n/a`.
- Figure numbers are fixed by slot order, so a reference such as "Fig. 3" stays correct
  when a slot is filled later.
- Figures are scaled to at most 6 in wide and 7.5 in high, and captioned "Figure n:" below.
- Tables are captioned "Table n:" above. Table 1 and Table 2 are the device lists, Table 3 is
  the values table, and Table 4 is the PVT table.
- The script prints the count and list of NOT YET AVAILABLE items after each build. Use this
  as a to-do list.

## Student-filled items

The title-page register numbers, names, signatures, batch number and faculty signature lines
are left empty on purpose. Column headers are kept. Do not fill them from the data file.

## Test workflow (no repo output)

```
/home/parshu/vm/rv/bin/python scripts/build_academic_docx.py \
    --data report/gpdk045/report_data.example.json --out /home/parshu/vm/fmt/test_out
```

Check the PDF visually, and check the fonts and sizes with python-docx.
