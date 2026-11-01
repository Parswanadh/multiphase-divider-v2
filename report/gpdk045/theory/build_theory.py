#!/usr/bin/env python3
"""Build the 23ECE302 VLSI Design Theory Assignment as .docx and .pdf.

Official Amrita format: Times New Roman, 12 pt body, 14 pt headings, 0.9 in margins,
double page border, "Page X of Y" footer, cover block matching system design report.

Output:
  report/gpdk045/theory/23ECE302_Theory_Assignment.docx
  report/gpdk045/theory/23ECE302_Theory_Assignment.pdf
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import docx
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageChops

FONT = "Times New Roman"
BODY_PT = 11.0  # Precise academic body font
HEADING_PT = 12.5
BLACK = RGBColor(0x00, 0x00, 0x00)
TEXT_W_IN = 6.7  # 8.5 - 2*0.9 in


class TheoryReportBuilder:
    def __init__(self, root_dir: Path, out_dir: Path):
        self.root_dir = root_dir
        self.out_dir = out_dir
        self.report_dir = root_dir / "report" / "gpdk045"
        self.temp_dir = Path(tempfile.mkdtemp(prefix="theory_build_img_"))
        self.doc = Document()
        self.fig_count = 0
        self.table_count = 0
        self._setup_styles()
        self._page_setup()

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @staticmethod
    def _font(run, size=BODY_PT, bold=False, italic=False, color=BLACK):
        run.font.name = FONT
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:eastAsia"), FONT)
        rfonts.set(qn("w:cs"), FONT)
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        if color is not None:
            run.font.color.rgb = color

    def text(self, p, s, size=BODY_PT, bold=False, italic=False, color=BLACK):
        run = p.add_run(s)
        self._font(run, size, bold, italic, color)
        return run

    def para(self, s="", *, size=BODY_PT, bold=False, italic=False, color=BLACK,
              align=None, before=0, after=2.0, keep=False, keep_together=False, line_spacing=1.02):
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing = line_spacing
        pf.keep_with_next = keep
        pf.keep_together = keep_together
        pf.widow_control = True
        if align == "c":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "r":
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif align == "j":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if s:
            self.text(p, s, size, bold, italic, color)
        return p

    def heading(self, s, before=4.5, after=1.0):
        p = self.doc.add_paragraph(style="Heading 1")
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.keep_with_next = True
        pf.widow_control = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        self.text(p, s, HEADING_PT, bold=True, color=BLACK)
        return p

    def subheading(self, s, before=2.5, after=0.6):
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.keep_with_next = True
        pf.widow_control = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        self.text(p, s, size=BODY_PT, bold=True, color=BLACK)
        return p

    def page_break(self):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.add_run().add_break(WD_BREAK.PAGE)
        return p

    def _field(self, p, instr):
        def run_with(element=None, txt=None):
            run = p.add_run(txt) if txt is not None else p.add_run()
            self._font(run, size=10)
            if element is not None:
                run._element.append(element)
            return run

        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        run_with(begin)
        instr_el = OxmlElement("w:instrText")
        instr_el.set(qn("xml:space"), "preserve")
        instr_el.text = f" {instr} "
        run_with(instr_el)
        sep = OxmlElement("w:fldChar")
        sep.set(qn("w:fldCharType"), "separate")
        run_with(sep)
        run_with(txt="1")
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        run_with(end)

    def _cell(self, cell, s, bold=False, italic=False, color=BLACK, align="l", pad_v=0.8, size=8.0):
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(pad_v)
        p.paragraph_format.space_after = Pt(pad_v)
        p.paragraph_format.line_spacing = 1.0
        if align == "c":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "r":
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif align == "j":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        self.text(p, s, size=size, bold=bold, italic=italic, color=color)

    def table(self, header, rows, widths, caption, alignments=None, pad_v=0.8, font_size=8.0):
        widths = [w * 6.0 / sum(widths) for w in widths]  # fit the official 6.0 in text width
        self.table_count += 1
        cap = self.para(keep=True, before=2.0, after=0.6)
        cap.paragraph_format.keep_together = True
        cap.paragraph_format.keep_with_next = True
        self.text(cap, f"Table {self.table_count}: ", bold=True, size=9.0)
        self.text(cap, caption, size=9.0)

        if alignments is None:
            alignments = ["l"] + ["c"] * (len(header) - 1)

        t = self.doc.add_table(rows=1, cols=len(header))
        t.style = self.doc.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False

        tblPr = t._tbl.tblPr
        tblBorders = OxmlElement("w:tblBorders")
        for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b_el = OxmlElement(f"w:{border_name}")
            b_el.set(qn("w:val"), "single")
            b_el.set(qn("w:sz"), "4")
            b_el.set(qn("w:space"), "0")
            b_el.set(qn("w:color"), "000000")
            tblBorders.append(b_el)
        tblPr.append(tblBorders)

        trpr = t.rows[0]._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:tblHeader"))
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

        for i, h in enumerate(header):
            cell = t.rows[0].cells[i]
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), "E0E0E0")
            cell._tc.get_or_add_tcPr().append(shd)
            align = alignments[i] if i < len(alignments) else "c"
            self._cell(cell, h, bold=True, align=align, pad_v=pad_v, size=font_size)

        for row in rows:
            new_row = t.add_row()
            new_row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            cells = new_row.cells
            for i, val in enumerate(row):
                align = alignments[i] if i < len(alignments) else "c"
                bold = False
                italic = False
                color = BLACK
                if isinstance(val, tuple):
                    val_str = str(val[0])
                    if len(val) > 1 and val[1]:
                        bold = True
                    if len(val) > 2 and val[2]:
                        italic = True
                    if len(val) > 3 and val[3]:
                        color = val[3]
                else:
                    val_str = str(val)
                self._cell(cells[i], val_str, bold=bold, italic=italic, color=color, align=align, pad_v=pad_v, size=font_size)

        for i, w in enumerate(widths):
            t.columns[i].width = Inches(w)
            w_dxa = str(int(w * 1440))
            for row in t.rows:
                cell = row.cells[i]
                cell.width = Inches(w)
                tcW = cell._tc.get_or_add_tcPr().get_or_add_tcW()
                tcW.set(qn("w:type"), "dxa")
                tcW.set(qn("w:w"), w_dxa)

        self.para(after=1.5)
        return t

    def _trim_figure(self, path: Path) -> Path:
        if not path or not path.is_file():
            return path
        norm = str(path).replace("\\", "/")
        if "screens" in norm or "figures" not in norm:
            return path
        try:
            with Image.open(path) as im:
                if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    bg.paste(im, mask=im.convert("RGBA").split()[3])
                    im_rgb = bg
                else:
                    im_rgb = im.convert("RGB")
                bg = Image.new("RGB", im.size, (255, 255, 255))
                diff = ImageChops.difference(im_rgb, bg)
                bbox = diff.getbbox()
                if bbox:
                    w, h = im.size
                    pad = 2
                    bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                            min(w, bbox[2] + pad), min(h, bbox[3] + pad))
                    cropped = im.crop(bbox)
                    out_path = self.temp_dir / f"trimmed_{path.name}"
                    cropped.save(out_path)
                    return out_path
        except Exception:
            pass
        return path

    def figure(self, rel_path_str: str, caption: str, width_in: float = 4.2, max_h_in: float = 1.7):
        self.fig_count += 1
        path = self.report_dir / rel_path_str
        if not path.is_file():
            raise FileNotFoundError(f"Missing figure file: {path}")

        render_path = self._trim_figure(path)
        with Image.open(render_path) as im:
            w_px, h_px = im.size
        aspect = h_px / w_px

        w_in = width_in
        h_in = w_in * aspect
        if h_in > max_h_in:
            h_in = max_h_in
            w_in = h_in / aspect

        pic_p = self.para(align="c", keep=True, before=0.8, after=0.6)
        pic_p.paragraph_format.keep_together = True
        run = pic_p.add_run()
        self._font(run)
        run.add_picture(str(render_path), width=Inches(w_in), height=Inches(h_in))

        cap_p = self.para(align="c", before=0.2, after=1.5)
        cap_p.paragraph_format.keep_together = True
        self.text(cap_p, f"Figure {self.fig_count}: ", bold=True, size=8.5)
        self.text(cap_p, caption, size=8.5)

    def figure_pair(self, rel1: str, cap1: str, rel2: str, cap2: str, width_in: float = 3.2, max_h_in: float = 1.65):
        self.fig_count += 1
        n1 = self.fig_count
        self.fig_count += 1
        n2 = self.fig_count

        path1 = self.report_dir / rel1
        path2 = self.report_dir / rel2
        rend1 = self._trim_figure(path1)
        rend2 = self._trim_figure(path2)

        def get_wh(p):
            with Image.open(p) as im:
                w_px, h_px = im.size
            aspect = h_px / w_px
            w = width_in
            h = w * aspect
            if h > max_h_in:
                h = max_h_in
                w = h / aspect
            return w, h

        w1, h1 = get_wh(rend1)
        w2, h2 = get_wh(rend2)

        t = self.doc.add_table(rows=2, cols=2)
        t.style = self.doc.styles["Normal Table"] if "Normal Table" in self.doc.styles else self.doc.styles["Table Grid"]
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False

        tblPr = t._tbl.tblPr
        tblBorders = OxmlElement("w:tblBorders")
        for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b_el = OxmlElement(f"w:{border_name}")
            b_el.set(qn("w:val"), "none")
            tblBorders.append(b_el)
        tblPr.append(tblBorders)

        col_w = [3.35, 3.35]
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for i, w in enumerate(col_w):
                cell = row.cells[i]
                cell.width = Inches(w)
                tcW = cell._tc.get_or_add_tcPr().get_or_add_tcW()
                tcW.set(qn("w:type"), "dxa")
                tcW.set(qn("w:w"), str(int(w * 1440)))

        # Row 0: pictures
        p1 = t.rows[0].cells[0].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0.4)
        p1.paragraph_format.space_after = Pt(0.4)
        r1 = p1.add_run()
        self._font(r1)
        r1.add_picture(str(rend1), width=Inches(w1), height=Inches(h1))

        p2 = t.rows[0].cells[1].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_before = Pt(0.4)
        p2.paragraph_format.space_after = Pt(0.4)
        r2 = p2.add_run()
        self._font(r2)
        r2.add_picture(str(rend2), width=Inches(w2), height=Inches(h2))

        # Row 1: captions
        c1 = t.rows[1].cells[0].paragraphs[0]
        c1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c1.paragraph_format.space_before = Pt(0.2)
        c1.paragraph_format.space_after = Pt(1.5)
        self.text(c1, f"Figure {n1}: ", bold=True, size=8.0)
        self.text(c1, cap1, size=8.0)

        c2 = t.rows[1].cells[1].paragraphs[0]
        c2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c2.paragraph_format.space_before = Pt(0.2)
        c2.paragraph_format.space_after = Pt(1.5)
        self.text(c2, f"Figure {n2}: ", bold=True, size=8.0)
        self.text(c2, cap2, size=8.0)

        self.para(after=1.0)

    def _setup_styles(self):
        def fix_theme(style_el):
            rpr = style_el.get_or_add_rPr()
            rfonts = rpr.get_or_add_rFonts()
            for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rfonts.get(qn(attr)) is not None:
                    del rfonts.attrib[qn(attr)]
            rfonts.set(qn("w:eastAsia"), FONT)
            rfonts.set(qn("w:cs"), FONT)
            color = rpr.find(qn("w:color"))
            if color is not None:
                for attr in ("w:themeColor", "w:themeShade", "w:themeTint"):
                    if color.get(qn(attr)) is not None:
                        del color.attrib[qn(attr)]

        normal = self.doc.styles["Normal"]
        normal.font.name = FONT
        normal.font.size = Pt(BODY_PT)
        normal.font.color.rgb = BLACK
        fix_theme(normal.element)

        heading = self.doc.styles["Heading 1"]
        heading.font.name = FONT
        heading.font.size = Pt(HEADING_PT)
        heading.font.bold = True
        heading.font.italic = False
        heading.font.color.rgb = BLACK
        fix_theme(heading.element)

    def _page_setup(self):
        sec = self.doc.sections[0]
        sec.page_width = Inches(8.5)
        sec.page_height = Inches(11)
        for side, val in (("left_margin", 1.25), ("right_margin", 1.25), ("top_margin", 1.0), ("bottom_margin", 1.0)):
            setattr(sec, side, Inches(val))
        sec.footer_distance = Inches(0.45)

        # Double page border matching official format
        sect_pr = sec._sectPr
        borders = OxmlElement("w:pgBorders")
        borders.set(qn("w:offsetFrom"), "text")
        borders.set(qn("w:display"), "allPages")
        for side in ("top", "left", "bottom", "right"):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:val"), "double")
            el.set(qn("w:sz"), "4")
            el.set(qn("w:space"), "10")
            el.set(qn("w:color"), "000000")
            borders.append(el)
        sect_pr.find(qn("w:pgMar")).addnext(borders)

        footer_p = sec.footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = footer_p.add_run("Page ")
        self._font(run, size=10)
        self._field(footer_p, "PAGE")
        run = footer_p.add_run(" of ")
        self._font(run, size=10)
        self._field(footer_p, "NUMPAGES")

    # -------------------------------------------------------------------------
    # 7-PAGE EXACT BUDGET
    # -------------------------------------------------------------------------
    def build_page1_cover(self):
        """Page 1: Amrita official cover block with student blanks."""
        logo_path = self.report_dir / "assets" / "amrita_logo.jpeg"
        if logo_path.is_file():
            p_logo = self.para(align="c", before=4, after=8)
            with Image.open(logo_path) as im:
                w_px, h_px = im.size
                aspect = h_px / w_px
            w_in = 3.6
            run = p_logo.add_run()
            self._font(run)
            run.add_picture(str(logo_path), width=Inches(w_in), height=Inches(w_in * aspect))

        self.para("AMRITA SCHOOL OF ENGINEERING, BENGALURU", align="c", before=2, after=2)
        self.para("DEPARTMENT OF ELECTRONICS & COMMUNICATION ENGINEERING", align="c", before=0, after=8)
        self.para("B. TECH. V SEMESTER (ECE AND EAC) AY 2026-2027", bold=True, align="c", before=2, after=3)
        self.para("ASSIGNMENT FOR 23ECE302 VLSI DESIGN", bold=True, align="c", before=2, after=3)
        self.para("THEORY ASSIGNMENT REPORT", bold=True, align="c", before=2, after=3)
        self.para("JULY TO NOVEMBER 2026", bold=True, align="c", before=2, after=12)

        self.para("MULTIPHASE DIVIDE-BY-TWO CMOS FREQUENCY DIVIDER IN 45 NM CMOS (CADENCE GPDK045)",
                  bold=True, italic=True, align="c", size=13, before=6, after=4)
        self.para("Evaluation: Implementation / Transistor Schematic (7 Marks) & Applying Sizing Concept (8 Marks)",
                  italic=True, align="c", size=11, before=0, after=12)

        self.para("Submitted by", bold=True, align="c", before=4, after=4)
        sub = self.doc.add_table(rows=5, cols=3)
        sub.style = self.doc.styles["Table Grid"]
        sub.alignment = WD_TABLE_ALIGNMENT.CENTER
        sub.autofit = False

        tblPr = sub._tbl.tblPr
        tblBorders = OxmlElement("w:tblBorders")
        for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b_el = OxmlElement(f"w:{border_name}")
            b_el.set(qn("w:val"), "single")
            b_el.set(qn("w:sz"), "4")
            b_el.set(qn("w:space"), "0")
            b_el.set(qn("w:color"), "000000")
            tblBorders.append(b_el)
        tblPr.append(tblBorders)

        headers = ["REGISTER NUMBER", "NAME", "SIGNATURE WITH DATE"]
        for i, h in enumerate(headers):
            cell = sub.rows[0].cells[i]
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), "E0E0E0")
            cell._tc.get_or_add_tcPr().append(shd)
            self._cell(cell, h, bold=True, italic=True, align="c", pad_v=3.0, size=11)

        col_w = [2.2, 2.3, 2.2]
        for row_idx, row in enumerate(sub.rows):
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            if row_idx > 0:
                row.height = Pt(28)
                row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
            for i, w in enumerate(col_w):
                cell = row.cells[i]
                cell.width = Inches(w)
                tcW = cell._tc.get_or_add_tcPr().get_or_add_tcW()
                tcW.set(qn("w:type"), "dxa")
                tcW.set(qn("w:w"), str(int(w * 1440)))

        p_batch = self.para(before=16, after=10)
        self.text(p_batch, "BATCH NUMBER: ", bold=True)
        self.text(p_batch, "____________________________________", bold=False)

        self.para("________________________________________________________", before=28, after=3)
        self.para("FACULTY EXAMINER SIGNATURE WITH EVALUATION DATE", bold=True, before=0, after=0)
        self.page_break()

    def build_page2_paper_and_dlatch(self):
        """Page 2: Paper details, Tool & tech, Section 1 intro, DLATCH schematics (side-by-side)."""
        self.heading("TITLE OF THE ASSIGNMENT PROJECT:")
        self.para("Implementation of a Compact Multiphase Divide-by-Two CMOS Frequency Divider in 45 nm CMOS (Cadence GPDK045)", after=1.5)

        self.heading("DETAILS OF THE REFERENCE PAPER (SOURCE OF ARCHITECTURE):")
        fields = [
            ("Paper Title", 'Y.-F. Kuo et al., "A Compact Multiphase Divide-by-Two CMOS Frequency Divider"'),
            ("Authors", "Yue-Fang Kuo, Shih-Hung Lin, Bo-Yi Chen, and Liang-Chen Liu"),
            ("Journal", "IEEE Microwave and Wireless Technology Letters (vol. 35, no. 5, pp. 617-620, May 2025)"),
            ("Digital Object Identifier (DOI)", "10.1109/LMWT.2025.3528863"),
            ("Process Technology Comparison", "Reference: TSMC 180-nm CMOS (1.8 V supply); This work: Cadence GPDK045 (45 nm standard-Vt CMOS, 1.0 V supply)."),
        ]
        for lbl, val in fields:
            p = self.para(after=0.8)
            self.text(p, f"{lbl}: ", bold=True)
            self.text(p, val)

        self.heading("TOOL & PROCESS TECHNOLOGY USED:")
        self.para(
            "Circuit entry and simulations were executed in Cadence Virtuoso IC6.1.5 and Cadence Spectre MMSIM 12.1 using Cadence 45 nm "
            "Generic Process Design Kit (GPDK045, v6.0). Transistors are 1.0 V standard-Vt NMOS devices (model g45n1svt, cell nmos1v). "
            "Nominal power supply is VDD = 1.0 V (+/-10% range: 0.9 V to 1.1 V) at 27 deg C.",
            after=1.5, align="j"
        )

        self.heading("SECTION 1: TRANSISTOR SCHEMATIC IMPLEMENTATION (7 MARKS)")
        self.para(
            "The multiphase divider consists of four differential Current-Mode Logic (CML) D-latches (Latch 1 to Latch 4, instances XD1 to XD4) "
            "connected in a closed ring with alternating cross-connections and dual-clock phasing. Each latch provides differential inputs (D, Db) "
            "and outputs (Q, Qb), with eight discrete multiphase outputs (f0, f45, f90, f135, f180, f225, f270, and f315) tapped directly from the latch output nodes.",
            after=1.5, align="j"
        )

        self.subheading("1.1 Single Differential D-Latch (DLATCH) Transistor Topology")
        self.para(
            "As depicted in Figure 1 (schematic diagram) and Figure 2 (Virtuoso schematic editor screenshot), each DLATCH contains seven NMOS transistors "
            "(M1-M7) and two symmetric resistive pull-up loads (R1, R2 connected to VDD): differential sampling pair (M1, M2), sampling clock switch (M5), "
            "regenerative cross-coupled hold pair (M3, M4), hold clock switch (M6), and tail current sink (M7, L = 90 nm, gate vb = 1.0 V).",
            after=1.5, align="j"
        )

        # DLATCH figures side-by-side
        self.figure_pair(
            "figures/fig_circuit_latch.png",
            "Differential D-latch circuit diagram with M1-M7 and loads R1, R2.",
            "screens/schematic_dlatch_full.png",
            "Virtuoso DLATCH schematic editor window in Cadence GPDK045.",
            width_in=3.2, max_h_in=1.75
        )
        self.page_break()

    def build_page3_ring_and_tables(self):
        """Page 3: Four-latch ring architecture, clocking table, and device table."""
        self.subheading("1.2 Four-Latch Ring Divider Architecture & Alternating Clock Distribution")
        self.para(
            "The complete frequency divider (Figure 3 schematic diagram) interconnects four DLATCH stages in a ring. To achieve divide-by-two frequency "
            "division without race conditions, two fundamental topological rules are enforced:",
            after=1.0, align="j"
        )
        arch_rules = [
            ("Dual-Clock Phasing: ", "Latches 1 & 4 receive true clock CK at sampling switch M5 and inverted clock CKb at hold switch M6. Latches 2 & 3 receive inverted clocking: CKb at sampling switch M5 and CK at hold switch M6. When CK is HIGH, Latches 1 & 4 sample while Latches 2 & 3 hold; when CK falls LOW, Latches 2 & 3 sample while Latches 1 & 4 hold."),
            ("Alternating Cross-Connections: ", "Inter-stage connections alternate between inverted and direct couplings: Q1b connects to D2 and Q1 to D2b; Q2 connects to D3 and Q2b to D3b; Q3b connects to D4 and Q3 to D4b; and Q4 connects to D1b and Q4b to D1. This topology produces a single net loop inversion across the four-stage cascade.")
        ]
        for bld, body in arch_rules:
            p = self.para(before=0.3, after=0.6, align="j")
            self.text(p, "- ", bold=True)
            self.text(p, bld, bold=True)
            self.text(p, body)

        self.para(
            "Operating Principle: A signal transition requires two full input clock periods (2 * T_CK) to traverse the entire 4-latch loop and return in phase, "
            "yielding exact divide-by-two frequency division (f_out = f_in / 2). Each latch stage introduces propagation delay Td ~ T_CK / 8, providing eight "
            "equidistant output phases spaced by 45 degrees (pi / 4).",
            after=1.2, align="j"
        )

        self.figure("figures/fig_circuit_ring.png",
                    "Interconnection diagram of the four-latch ring divider (XD1 to XD4) showing alternating cross-connections and dual-phase clock distribution.",
                    width_in=4.2, max_h_in=1.70)

        # Table 1: Clocking and Phase Allocation Table
        t1_headers = ["Latch Stage", "Instance", "Sampling Clock (M5)", "Hold Clock (M6)", "Inputs (D, Db)", "Outputs (Q, Qb)", "Phase Taps", "Nominal Phase"]
        t1_rows = [
            ["Latch 1", "XD1", "CK (Active High)", "CKb (Active Low)", "D1 = Q4b, Db1 = Q4", "Q1, Q1b", "f0, f180", "0 deg, 180 deg"],
            ["Latch 2", "XD2", "CKb (Active Low)", "CK (Active High)", "D2 = Q1b, Db2 = Q1", "Q2, Q2b", "f45, f225", "45 deg, 225 deg"],
            ["Latch 3", "XD3", "CKb (Active Low)", "CK (Active High)", "D3 = Q2, Db3 = Q2b", "Q3, Q3b", "f90, f270", "90 deg, 270 deg"],
            ["Latch 4", "XD4", "CK (Active High)", "CKb (Active Low)", "D4 = Q3b, Db4 = Q3", "Q4, Q4b", "f135, f315", "135 deg, 315 deg"],
        ]
        t1_widths = [0.8, 0.95, 1.1, 1.0, 1.2, 0.7, 0.7, 0.85]
        self.table(t1_headers, t1_rows, t1_widths,
                   "Four-Latch Ring Clocking, Inter-Stage Connections, and Multiphase Output Allocation",
                   alignments=["l", "c", "c", "c", "l", "c", "c", "c"], font_size=8.0, pad_v=0.7)

        # Table 2: Device Table
        t2_headers = ["Device Name", "Circuit Function", "Drain", "Gate", "Source", "Bulk", "Baseline Dimensions (W / L)"]
        t2_rows = [
            ["M1, M2", "Differential sampling pair", "Q, Qb", "D, Db", "xs", "gnd!", "W = 240 nm, L = 45 nm (m = 1)"],
            ["M3, M4", "Regenerative cross-coupled hold pair", "Q, Qb", "Qb, Q", "xh", "gnd!", "W = 240 nm, L = 45 nm (m = 1)"],
            ["M5", "Sampling clock pass switch", "xs", "CK (or CKb)", "tail", "gnd!", "W = 240 nm, L = 45 nm (m = 1)"],
            ["M6", "Hold clock pass switch", "xh", "CKb (or CK)", "tail", "gnd!", "W = 240 nm, L = 45 nm (m = 1)"],
            ["M7", "Tail current sink", "tail", "vb (1.0 V)", "gnd!", "gnd!", "W = 480 nm, L = 90 nm (m = 1)"],
            ["R1, R2", "Symmetric pull-up resistive loads", "VDD", "n/a", "Q, Qb", "n/a", "R = 8 kOhm (unsized baseline)"],
        ]
        t2_widths = [1.0, 1.9, 0.7, 0.9, 0.7, 0.6, 1.9]
        self.table(t2_headers, t2_rows, t2_widths,
                   "DLATCH Transistor Device List, Terminal Interconnections, and Baseline Dimensions in Cadence GPDK045",
                   alignments=["l", "l", "c", "c", "c", "c", "l"], font_size=8.0, pad_v=0.7)
        pass  # flow (no forced break)

    def build_page4_sizing_physics(self):
        """Page 4: Section 2 Sizing concept, Elmore delay derivation, Edge balance vs regeneration, 45 nm findings (strictly budgeted to 1 page)."""
        self.heading("SECTION 2: TRANSISTOR SIZING CONCEPT & ELMORE DELAY (8 MARKS)")

        self.subheading("2.1 Kuo Elmore Delay Derivation & Edge-Balance Model (Paper Eqs. 1-2, Fig. 5)")
        self.para(
            "In Kuo et al. (IEEE LMWT 2025, Section II), latch propagation delay is analyzed using an Elmore RC delay model assuming tail transistor M7 "
            "is continuously ON with grounded drain (node-b ~ 0 V). Assuming unit gate capacitance equals diffusion capacitance (C = C_g = C_d), each "
            "differential output node Q1 carries lumped capacitance C_total = (6 + 2)C = 8C (drain junctions 2C, cross-coupled gate 1C, subsequent stage gate 1C, "
            "interconnect parasitics 4C). Internal node xs carries effective discharge capacitance ~2C.",
            after=1.0, align="j"
        )
        self.para("Falling Output Delay (t_pdf, Eq. 1): Discharging through M1 and M5 with active branch channel resistance R/2 yields:  t_pdf = (8C)*(R/2) = 4*R*C", bold=False, align="j", before=0.4, after=0.8)
        self.para("Rising Output Delay (t_pdr, Eq. 2): Charging node Q1 from VDD exclusively through load resistor R1 yields:  t_pdr = (8C)*R1", bold=False, align="j", before=0.4, after=1.0)

        self.subheading("2.2 Edge-Balance Interpretation vs. State Regeneration Condition")
        self.para(
            "Crucial Physical Distinction: Equating t_pdr = t_pdf yields R1 = R_on / 2. This is strictly an EDGE-BALANCE CONDITION designed to equalize "
            "rise and fall delays under Kuo's simplified grounded-tail model to ensure output symmetry; it is NOT a regeneration condition. In physical silicon, "
            "tail transistor M7 operates in the triode region with finite resistance. Cross-coupled pair M3-M4 requires small-signal loop gain A_loop = g_m * R1 > 1 "
            "to regenerate digital states against noise. If R1 is chosen too small (e.g., R1 = R_on / 2), the loop gain may fall below unity, which would explain a failure to regenerate (the loop gain was not measured directly; only the failure to divide was observed).",
            after=1.2, align="j"
        )

        self.subheading("2.3 GPDK045 45 nm Findings and the Stack-Regeneration Rule")
        self.para(
            "Direct transplantation of the reference sizing rule to Cadence GPDK045 exposes this limitation. In GPDK045, the measured NMOS channel on-resistance "
            "for a unit device (W = 240 nm, L = 45 nm, Vgs = 1.0 V) is R_on = 2.3 kOhm (range 2.28-2.73 kOhm). The paper's rule yields R1 = R_on / 2 = 1.15 kOhm.",
            after=0.8, align="j"
        )
        self.para(
            "45 nm Non-Dividing Finding: When simulated in Cadence Spectre at 1.4 GHz, the unit-size divider with R1 = 1.15 kOhm FAILS TO DIVIDE "
            "(results/gpdk045/final/unsized.tsv). Rather than dividing to 700 MHz, the output exhibits feedthrough at 2799.8 MHz (2 * f_in) with an "
            "unusable peak-to-peak swing of only 15.3 mV (< 0.1 V threshold), as shown in Figure 4. This is consistent with insufficient regenerative loop gain in the hold pair; the loop gain itself was not measured.",
            after=1.0, align="j"
        )
        self.para(
            "Stack-Regeneration Rule (Approximate Heuristic): To achieve regeneration and full swing, load resistor R1 must overcome the pull-down "
            "resistance of the three stacked NMOS transistors (M1 + M5 + M7 during sampling, M3 + M6 + M7 during hold). For device multiplier m, effective "
            "stack resistance is R_stack ~ 3 * R_on / m. Empirical sweeps in GPDK045 establish that reliable regeneration requires an approximate margin of ~1.1x:  "
            "R_load >= ~ 1.1 * (3 * R_on / m).",
            after=0.8, align="j"
        )
        self.para(
            "- Unit sizing (m = 1): Stack resistance is 3 * 2.3 kOhm = 6.90 kOhm. The heuristic predicts R_load >= 7.59 kOhm. Spectre sweeps confirm division "
            "fails for R <= 6 kOhm and succeeds for R >= 7 kOhm at vb = 1.0 V (R >= 8 kOhm at vb = 0.8 V). Thus, R = 8 kOhm is selected as the robust unsized baseline.",
            after=0.8, align="j"
        )
        self.para(
            "- Sized devices (m = 4): Quadrupling width reduces stack resistance to (3 * 2.3 kOhm) / 4 = 1.725 kOhm, giving a regeneration threshold of "
            "R_load >= 1.90 kOhm (band 1.88-2.25 kOhm). Sized Design D adopts R = 3 kOhm (58% margin above the 1.90 kOhm threshold; 41 of 45 PVT corners divide); Design B adopts R = 2 kOhm "
            "at 6 GHz, minimizing RC delay to achieve a superior 3.78-degree phase error.",
            after=1.0, align="j"
        )

        self.subheading("2.4 Divider Speed Limit")
        self.para(
            "Speed Limit: Correct division requires signal propagation through two latches (2 * Td) within half a clock period (T_CK / 2): "
            "2 * Td < T_CK / 2  ==>  f_in,max < 1 / (4 * Td). Equidistant 45-degree phases require 2 * Td ~ T_CK / 4 (T_CK ~ 8 * Td). "
            "Phase error drops toward zero near this limit (3.78 deg in Design B at 6 GHz).",
            after=1.5, align="j"
        )
        pass  # flow (no forced break)

    def build_page5_tables_and_gap(self):
        """Page 5: Sizing & Performance Tables, Power discrepancy analysis (strictly budgeted to 1 page)."""
        # Table 3: Tuned Values Table
        t3_headers = ["Device", "Baseline (Unsized)", "Tuned Design D (1.4 GHz)", "Tuned Design B (6.0 GHz)", "Role", "Sizing Rationale & Engineering Justification"]
        t3_rows = [
            ["M1, M2", "W = 240 nm, L = 45 nm, m = 1", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)",
             "Sampling pair", "Multiplier m = 4 quadruples gm and lowers channel Ron from 2.3 kOhm to 575 Ohm, accelerating input tracking."],
            ["M3, M4", "W = 240 nm, L = 45 nm, m = 1", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)",
             "Hold cross pair", "Multiplier m = 4 ensures gm * R1 > 1 with lower load R (2-3 kOhm), preventing state collapse and boosting speed."],
            ["M5", "W = 240 nm, L = 45 nm, m = 1", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)",
             "Clock switch (CK)", "Matched to differential pair (m = 4) to lower series resistance in the sampling pull-down stack below 600 Ohm."],
            ["M6", "W = 240 nm, L = 45 nm, m = 1", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)", "W = 240 nm, L = 45 nm, m = 4 (Weff = 960 nm)",
             "Clock switch (CKb)", "Matched to hold pair (m = 4) to enable rapid transition into regenerative latching on clock edge."],
            ["M7", "W = 480 nm, L = 90 nm, m = 1", "W = 480 nm, L = 90 nm, m = 4 (Weff = 1920 nm)", "W = 480 nm, L = 90 nm, m = 4 (Weff = 1920 nm)",
             "Tail current sink", "Channel length L = 90 nm raises rout. Width m = 4 sinks 4x current (0.54 mA vs 0.14 mA) with Vds ~ 67 mV in triode."],
            ["R1, R2", "R = 8 kOhm", "R = 3 kOhm", "R = 2 kOhm",
             "Pull-up loads", "Design D uses R = 3 kOhm for 0.434 V swing and division at 41 of 45 PVT corners (a deterministic corner count, not a yield estimate). Design B uses R = 2 kOhm to minimize RC delay at 6 GHz (3.78 deg error)."],
        ]
        t3_widths = [0.8, 1.1, 1.2, 1.2, 0.9, 1.5]
        self.table(t3_headers, t3_rows, t3_widths,
                   "Transistor Sizing and Tuned Parameter Values in Cadence GPDK045 (Unsized Baseline vs. Tuned Design D vs. Tuned Design B)",
                   alignments=["l", "l", "l", "l", "l", "j"], font_size=7.5, pad_v=0.5)

        # Table 4: Measured Performance Table
        t4_headers = [
            "Performance Metric",
            "Unsized Baseline (m = 1, R = 8 kOhm)",
            "Sized Design D (m = 4, R = 3 kOhm) [Standalone]",
            "Sized Design D (m = 4, R = 3 kOhm) [Virtuoso]",
            "Sized Design B (m = 4, R = 2 kOhm) [Standalone]",
            "Unit",
            "Sizing Impact & Rationale"
        ]
        t4_rows = [
            ["Input Clock Frequency (f_in)", "1.400", "1.400", "1.400", "6.000", "GHz", "Evaluated design operating points"],
            ["Output Frequency (f_out)", "700.0", "700.0", "700.0", "3000.0", "MHz", "Exact 2:1 division verified across all designs"],
            ["Division Status", "PASS (Ratio 2.0)", "PASS (Ratio 2.0)", "PASS (Ratio 2.0)", "PASS (Ratio 2.0)", "—", "All 8 phase outputs toggle symmetrically"],
            ["Average DC Supply Power", "0.1375", "0.5413", "0.4554", "0.4929", "mW", "Sizing increases current 3.94x; Virtuoso netlist is 15.9% lower due to layout effects"],
            ["Propagation Delay (t_pd)", "62.21", "25.99", "26.66", "27.94", "ps", "Sizing cuts delay by 2.39x (Design D); Design B maintains 27.94 ps at 6 GHz"],
            ["Power-Delay Product (PDP)", "8.557", "14.067", "12.142", "13.768", "fJ", "Energy-delay trade-off for 2.39x speed improvement"],
            ["Differential Output Swing", "0.2289 (0.749-0.978)", "0.4344 (0.583-1.017)", "0.434 (0.58-1.01)", "0.1349 (0.818-0.953)", "V", "Sizing increases output swing by 1.90x in Design D"],
            ["Maximum Phase-Step Error", "26.42", "38.46", "37.90", "3.78", "deg", "Design B reaches 3.78 deg, matching Kuo benchmark (3.75 deg)"],
            ["Tail M7 V_ds / V_dsat Check", "0.0671 / 0.3578", "0.0669 / 0.3578", "0.067 / 0.358", "0.0768 / 0.3578", "V", "M7 operates in triode region (Vds < Vdsat) across all designs"],
            ["PVT corners dividing (count, not yield)", "Not evaluated", "41 of 45 corners", "Consistent with standalone", "21 of 45 corners", "—", "5 corners x 3 temperatures x 3 supply voltages"],
        ]
        t4_widths = [1.2, 0.9, 1.0, 1.0, 0.9, 0.4, 1.3]
        self.table(t4_headers, t4_rows, t4_widths,
                   "Measured Electrical Performance Comparison across Unsized Baseline, Tuned Design D, and Tuned Design B in GPDK045",
                   alignments=["l", "c", "c", "c", "c", "c", "j"], font_size=7.5, pad_v=0.4)
        pass  # flow (no forced break)

    def build_page6_waveforms(self):
        """Page 6: Power Discrepancy Analysis & Verification Waveforms."""
        self.subheading("2.5 Power Discrepancy Analysis: Standalone Netlist vs. Virtuoso Schematic Netlist")
        self.para(
            "An authentic 15.9% difference is observed between standalone Spectre netlist power (0.5413 mW) and Virtuoso schematic netlist power "
            "(0.4554 mW) for Design D. Diagnostic simulations (results/gpdk045/power_gap_experiment.md) confirmed this difference originates entirely "
            "from layout-dependent effect parameters (stress terms sa, sb, sd, well-proximity terms sca, scb, scc, and parasitics as, ad, ps, pd) "
            "computed by the Virtuoso CDF netlister. Injecting these parameters into the standalone netlist yields 0.4554 mW and 26.66 ps, matching "
            "the Cadence OCEAN schematic simulation (results/gpdk045/ocean_schematic_run_1p4GHz_D.txt) to within 0.02%.",
            after=1.5, align="j"
        )

        self.heading("SECTION 3: SIMULATION WAVEFORM VERIFICATION EVIDENCE")
        self.para(
            "Transient division waveforms were verified in Cadence Spectre and Virtuoso ViVA across the evaluated operating points:",
            after=1.0, align="j"
        )

        # Pair 1: Unsized failure & Design D ViVA screenshot
        self.figure_pair(
            "figures/fig_tran_unsized.png",
            "Spectre transient waveform for paper sizing (1.15 kOhm) showing division failure (2.8 GHz, 15.3 mV swing).",
            "screens/viva_tran_D_1p4GHz_full.png",
            "ViVA viewer screenshot of sized Design D at 1.4 GHz confirming 2:1 division to 700 MHz (0.4344 V swing).",
            width_in=3.2, max_h_in=1.65
        )

        # Pair 2: Design B 6 GHz & Phase step distribution
        self.figure_pair(
            "figures/fig_tran_B_6g.png",
            "Spectre transient waveforms of Design B at 6.0 GHz showing 3000.0 MHz divided outputs.",
            "figures/fig_phase_steps.png",
            "Phase step distribution across eight outputs; Design B achieves 3.78 deg error at 6 GHz.",
            width_in=3.2, max_h_in=1.65
        )
        pass  # flow (no forced break)

    def build_page7_provenance_and_refs(self):
        """Page 7: Data sources table and references."""
        self.heading("DATA SOURCES AND REPRODUCIBILITY PROVENANCE")
        self.para(
            "In compliance with academic integrity guidelines, zero numeric values in this report are fabricated. Every reported metric corresponds to "
            "an authenticated simulation output file in results/gpdk045/final/ generated from Cadence Spectre 12.1 inside the CentOS VM:",
            after=1.2, align="j"
        )

        # Table 5: Data Sources Table
        t5_headers = ["Claimed Parameter / Result", "Reported Value", "Primary Evidence File", "Rerun & Verification Command"]
        t5_rows = [
            ["Unsized baseline metrics (1.4 GHz)", "0.1375 mW, 62.21 ps, 0.2289 V, 26.42 deg", "results/gpdk045/final/U8k.tsv", "spectre spectre/standalone/divider_U8k.scs"],
            ["Reference sizing failure (1.15 kOhm)", "Oscillates 2799.8 MHz, 15.3 mV swing", "results/gpdk045/final/unsized.tsv", "spectre spectre/standalone/divider_unsized.scs"],
            ["Design D standalone metrics (1.4 GHz)", "0.5413 mW, 25.99 ps, 0.4344 V, 38.46 deg", "results/gpdk045/final/D_1p4.tsv", "spectre spectre/standalone/divider_D_1p4.scs"],
            ["Design D Virtuoso schematic power & delay", "0.4554 mW, 26.66 ps (15.9% layout gap)", "results/gpdk045/ocean_schematic_run_1p4GHz_D.txt", "ocean -restore cadence/ocean/run_schematic_tb.ocn"],
            ["Layout-dependent effect verification", "0.5413 mW -> 0.4554 mW via stress terms", "results/gpdk045/power_gap_experiment.md", "python3 scripts/test_power_gap.py"],
            ["Design B standalone metrics (6.0 GHz)", "0.4929 mW, 27.94 ps, 0.1349 V, 3.78 deg", "results/gpdk045/final/B_6g.tsv", "spectre spectre/standalone/divider_B_6g.scs"],
            ["Tail M7 saturation check (Vdsat = 0.358 V)", "Vds = 0.0669 V (D), 0.0768 V (B) (triode)", "results/gpdk045/final/D_1p4.m7vdsat.txt", "grep m7 results/gpdk045/final/*.m7op.txt"],
            ["PVT corners dividing, Design D", "41 of 45 corners divide (deterministic count, not a yield estimate)", "results/gpdk045/final/pvt_summary_D_1p4.json", "python3 scripts/gpdk45_pvt_report.py --json"],
            ["PVT corners dividing, Design B", "21 of 45 corners divide (deterministic count, not a yield estimate)", "results/gpdk045/final/pvt_summary_B_6g.json", "python3 scripts/gpdk45_pvt_report.py --json"],
            ["NMOS channel on-resistance Ron", "2.3 kOhm (range 2.28 to 2.73 kOhm)", "report/gpdk045/LEDGER.md", "spectre cadence/tests/dc_sweep_nmos.scs"],
        ]
        t5_widths = [1.8, 1.4, 1.7, 1.8]
        self.table(t5_headers, t5_rows, t5_widths,
                   "Audit Traceability Table: Simulation Source Files and Execution Commands for Reported Metrics",
                   alignments=["l", "l", "l", "l"], font_size=8.0, pad_v=0.6)

        self.heading("REFERENCES")
        refs = [
            ('Y.-F. Kuo, S.-H. Lin, B.-Y. Chen, and L.-C. Liu, "A Compact Multiphase Divide-by-Two CMOS Frequency Divider," '
             'IEEE Microwave and Wireless Technology Letters, vol. 35, no. 5, pp. 617-620, May 2025, doi: 10.1109/LMWT.2025.3528863.'),
            ('Cadence Design Systems, "Cadence GPDK045 Generic Process Design Kit Documentation," version 6.0, Cadence Design Systems, San Jose, CA.'),
            ('Cadence Design Systems, "Spectre Circuit Simulator Reference Manual," MMSIM 12.1, Cadence Design Systems, San Jose, CA.')
        ]
        for i, ref in enumerate(refs, 1):
            p = self.para(before=1.0, after=1.2, align="j")
            self.text(p, f"[{i}] ", bold=True)
            self.text(p, ref)

    def save_docx(self, docx_path: Path):
        self.doc.save(str(docx_path))
        print(f"Saved DOCX: {docx_path}")

    def convert_to_pdf(self, docx_path: Path, pdf_path: Path):
        cmd = [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            str(docx_path),
            "--outdir", str(pdf_path.parent)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {res.stderr}")
        expected_pdf = docx_path.with_suffix(".pdf")
        if expected_pdf != pdf_path and expected_pdf.is_file():
            shutil.move(expected_pdf, pdf_path)
        print(f"Generated PDF: {pdf_path}")


def main():
    root_dir = Path("/home/parshu/projects/multiphase-divider-v2")
    out_dir = root_dir / "report" / "gpdk045" / "theory"
    out_dir.mkdir(parents=True, exist_ok=True)

    docx_path = out_dir / "23ECE302_Theory_Assignment.docx"
    pdf_path = out_dir / "23ECE302_Theory_Assignment.pdf"

    builder = TheoryReportBuilder(root_dir, out_dir)
    try:
        builder.build_page1_cover()
        builder.build_page2_paper_and_dlatch()
        builder.build_page3_ring_and_tables()
        builder.build_page4_sizing_physics()
        builder.build_page5_tables_and_gap()
        builder.build_page6_waveforms()
        builder.build_page7_provenance_and_refs()
        builder.save_docx(docx_path)
        builder.convert_to_pdf(docx_path, pdf_path)
    finally:
        builder.cleanup()

    print("Build complete successfully.")


if __name__ == "__main__":
    main()
