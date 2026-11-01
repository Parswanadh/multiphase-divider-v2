#!/usr/bin/env python3
"""Generate all README presentation assets for multiphase-divider-v2.

Outputs (in docs/readme/):
  - hero_banner.svg: Animated SVG banner with four-latch circuit topology and clock pulse animation.
  - badge_*.svg: Static SVG badges (Process, Supply, Status, Flow, Design metrics).
  - bar_*.svg: Mini SVG horizontal bar visuals for the results table.
  - waveform_D_1p4GHz_{light,dark}.png: Real Spectre transient waveform plots for Design D (1.4 GHz).
  - waveform_B_6GHz_{light,dark}.png: Real Spectre transient waveform plots for Design B (6.0 GHz).
  - division_action.gif: Animated GIF (under 2 MB) showing division in action.
  - division_action.mp4: H.264 video conversion via ffmpeg.
  - pvt_heatmap.png: Visual matrix of PVT pass/fail corners for Design D and Design B.

Usage:
  python3 scripts/make_readme_assets.py [--outdir docs/readme]
"""
import os
import sys
import subprocess

# Ensure required libraries are available; fallback to known python binaries if needed.
try:
    import matplotlib
    import PIL
    import numpy
except ImportError:
    for candidate in ["/usr/bin/python3", "/home/parshu/miniconda3/bin/python"]:
        if os.path.isfile(candidate) and candidate != sys.executable:
            os.execv(candidate, [candidate] + sys.argv)
    raise RuntimeError("matplotlib, PIL, or numpy not available in current environment")

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image
import csv
import io
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import spectre_raw as sr

DEFAULT_OUTDIR = os.path.join(ROOT, "docs", "readme")
RAW_D = os.path.join(ROOT, "results", "gpdk045", "final", "D_1p4.raw")
RAW_B = os.path.join(ROOT, "results", "gpdk045", "final", "B_6g.raw")
PVT_D = os.path.join(ROOT, "results", "gpdk045", "final", "pvt_D.tsv")
PVT_B = os.path.join(ROOT, "results", "gpdk045", "final", "pvt_B6.tsv")


def make_badge_svg(label, value, color_bg="#2ea043", label_bg="#21262d"):
    """Construct a clean, self-contained SVG badge."""
    char_w_lbl = 6.8
    char_w_val = 7.0
    w_lbl = int(len(label) * char_w_lbl + 16)
    w_val = int(len(value) * char_w_val + 16)
    total_w = w_lbl + w_val
    h = 22
    lbl_x = w_lbl / 2.0
    val_x = w_lbl + w_val / 2.0
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{h}" viewBox="0 0 {total_w} {h}" role="img" aria-label="{label}: {value}">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="m">
    <rect width="{total_w}" height="{h}" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#m)">
    <rect width="{w_lbl}" height="{h}" fill="{label_bg}"/>
    <rect x="{w_lbl}" width="{w_val}" height="{h}" fill="{color_bg}"/>
    <rect width="{total_w}" height="{h}" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11" font-weight="600">
    <text x="{lbl_x}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{lbl_x}" y="14">{label}</text>
    <text x="{val_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{val_x}" y="14">{value}</text>
  </g>
</svg>"""
    return svg


def make_bar_svg(ratio, color="#2ea043", bg="#21262d", width=60, height=10):
    """Construct an inline horizontal progress/bar SVG."""
    ratio = max(0.0, min(1.0, ratio))
    bar_w = int(ratio * (width - 2))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="progress bar">
  <rect width="{width}" height="{height}" rx="2" fill="{bg}"/>
  <rect x="1" y="1" width="{bar_w}" height="{height - 2}" rx="1" fill="{color}"/>
</svg>"""
    return svg


def make_hero_banner_svg(out_path):
    """Generate the animated SVG hero banner illustrating the 4-latch ring and clock phases."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 260" width="100%" height="260" style="background:#090d16; border-radius:6px; border:1px solid #30363d;">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090d16"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
    <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#58a6ff" stop-opacity="0.2"/>
      <stop offset="50%" stop-color="#388bfd" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#58a6ff" stop-opacity="0.2"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="960" height="260" fill="url(#bgGrad)" rx="6"/>

  <!-- Left: Metadata and Titles -->
  <g transform="translate(32, 34)">
    <rect x="0" y="0" width="280" height="20" rx="3" fill="#161b22" stroke="#30363d" stroke-width="1"/>
    <text x="8" y="14" fill="#58a6ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="10.5" font-weight="600" letter-spacing="0.5">CADENCE GPDK045 (45 nm CMOS) • SYSTEM DESIGN</text>

    <text x="0" y="52" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="22" font-weight="700">Multiphase Divide-by-Two Frequency Divider</text>
    <text x="0" y="76" fill="#8b949e" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="13" font-weight="400">Re-implementation and verification of the Kuo et al. (IEEE MWTL 2025) 8-phase architecture</text>

    <!-- Key metric chips -->
    <g transform="translate(0, 102)">
      <rect x="0" y="0" width="370" height="30" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
      <circle cx="16" cy="15" r="4" fill="#2ea043"/>
      <text x="28" y="19" fill="#c9d1d9" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11.5" font-weight="500">Design D: 1.4 GHz to 700 MHz | 0.54 mW | 41/45 PVT Pass</text>
    </g>

    <g transform="translate(0, 140)">
      <rect x="0" y="0" width="370" height="30" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
      <circle cx="16" cy="15" r="4" fill="#f0883e"/>
      <text x="28" y="19" fill="#c9d1d9" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11.5" font-weight="500">Design B: 6.0 GHz to 3.0 GHz | 3.78° Phase Error | 21/45 Pass</text>
    </g>

    <g transform="translate(0, 178)">
      <rect x="0" y="0" width="370" height="30" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
      <circle cx="16" cy="15" r="4" fill="#a371f7"/>
      <text x="28" y="19" fill="#c9d1d9" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11.5" font-weight="500">Complete Flow: SKILL Schematic, Spectre Sim, Assura Placement</text>
    </g>
  </g>

  <!-- Right: 4-Latch Ring Topology Circuit Diagram with SMIL Animation -->
  <g transform="translate(480, 20)">
    <!-- Circuit Panel Container -->
    <rect x="0" y="8" width="450" height="216" rx="6" fill="#111622" stroke="#21262d" stroke-width="1"/>
    <text x="16" y="28" fill="#8b949e" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="600">CIRCUIT RING TOPOLOGY (XD1 to XD4)</text>

    <!-- Interconnecting Bus Lines -->
    <!-- Top bus (XD1 to XD2) -->
    <path d="M 105 70 L 165 70" stroke="#30363d" stroke-width="2" fill="none"/>
    <path d="M 105 76 L 165 76" stroke="#30363d" stroke-width="2" fill="none"/>

    <!-- Right bus (XD2 to XD4) -->
    <path d="M 225 100 L 225 130 L 225 150" stroke="#30363d" stroke-width="2" fill="none"/>
    <path d="M 231 100 L 231 130 L 231 150" stroke="#30363d" stroke-width="2" fill="none"/>

    <!-- Bottom bus (XD4 to XD3) -->
    <path d="M 165 170 L 105 170" stroke="#30363d" stroke-width="2" fill="none"/>
    <path d="M 165 176 L 105 176" stroke="#30363d" stroke-width="2" fill="none"/>

    <!-- Left bus (XD3 back to XD1 with inversion/cross) -->
    <path d="M 75 140 L 75 125 L 85 115 L 85 100" stroke="#30363d" stroke-width="2" fill="none"/>
    <path d="M 85 140 L 85 125 L 75 115 L 75 100" stroke="#30363d" stroke-width="2" fill="none"/>

    <!-- Latch 1: XD1 (Top Left) -->
    <g id="latch1" transform="translate(45, 50)">
      <rect width="60" height="50" rx="4" fill="#161b22" stroke="#58a6ff" stroke-width="1.5"/>
      <text x="30" y="24" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="700" text-anchor="middle">XD1</text>
      <text x="30" y="38" fill="#58a6ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" text-anchor="middle">CK (0°)</text>
    </g>

    <!-- Latch 2: XD2 (Top Right) -->
    <g id="latch2" transform="translate(165, 50)">
      <rect width="60" height="50" rx="4" fill="#161b22" stroke="#3fb950" stroke-width="1.5"/>
      <text x="30" y="24" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="700" text-anchor="middle">XD2</text>
      <text x="30" y="38" fill="#3fb950" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" text-anchor="middle">CKb (90°)</text>
    </g>

    <!-- Latch 4: XD4 (Bottom Right) -->
    <g id="latch4" transform="translate(165, 140)">
      <rect width="60" height="50" rx="4" fill="#161b22" stroke="#f778ba" stroke-width="1.5"/>
      <text x="30" y="24" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="700" text-anchor="middle">XD4</text>
      <text x="30" y="38" fill="#f778ba" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" text-anchor="middle">CK (270°)</text>
    </g>

    <!-- Latch 3: XD3 (Bottom Left) -->
    <g id="latch3" transform="translate(45, 140)">
      <rect width="60" height="50" rx="4" fill="#161b22" stroke="#bc8cff" stroke-width="1.5"/>
      <text x="30" y="24" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="700" text-anchor="middle">XD3</text>
      <text x="30" y="38" fill="#bc8cff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="9" text-anchor="middle">CKb (180°)</text>
    </g>

    <!-- 8 Phase Output Pins and Arrows -->
    <!-- Q1, Q1b -->
    <path d="M 235 65 L 290 65" stroke="#58a6ff" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="295" y="69" fill="#58a6ff" font-family="-apple-system,sans-serif" font-size="10" font-weight="600">Q1, Q1b (0°, 180°)</text>

    <!-- Q2, Q2b -->
    <path d="M 235 85 L 290 85" stroke="#3fb950" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="295" y="89" fill="#3fb950" font-family="-apple-system,sans-serif" font-size="10" font-weight="600">Q2, Q2b (45°, 225°)</text>

    <!-- Q3, Q3b -->
    <path d="M 235 155 L 290 155" stroke="#bc8cff" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="295" y="159" fill="#bc8cff" font-family="-apple-system,sans-serif" font-size="10" font-weight="600">Q3, Q3b (90°, 270°)</text>

    <!-- Q4, Q4b -->
    <path d="M 235 175 L 290 175" stroke="#f778ba" stroke-width="1.5" stroke-dasharray="3 3"/>
    <text x="295" y="179" fill="#f778ba" font-family="-apple-system,sans-serif" font-size="10" font-weight="600">Q4, Q4b (135°, 315°)</text>

    <!-- Animated traveling pulse token circulating the ring -->
    <circle r="4" fill="#58a6ff">
      <animateMotion path="M 105 73 L 165 73 L 195 100 L 195 140 L 165 173 L 105 173 L 75 140 L 75 100 Z" dur="2.4s" repeatCount="indefinite"/>
      <animate attributeName="fill" values="#58a6ff;#3fb950;#bc8cff;#f778ba;#58a6ff" dur="2.4s" repeatCount="indefinite"/>
    </circle>
    <circle r="2" fill="#ffffff">
      <animateMotion path="M 105 73 L 165 73 L 195 100 L 195 140 L 165 173 L 105 173 L 75 140 L 75 100 Z" dur="2.4s" repeatCount="indefinite"/>
    </circle>

    <!-- Rotating phase ring in bottom right corner -->
    <g transform="translate(380, 150)">
      <circle cx="25" cy="25" r="22" fill="none" stroke="#21262d" stroke-width="1.5"/>
      <!-- 8 phase tick marks -->
      <line x1="25" y1="3" x2="25" y2="7" stroke="#58a6ff" stroke-width="2"/>
      <line x1="40" y1="9" x2="37" y2="12" stroke="#3fb950" stroke-width="2"/>
      <line x1="47" y1="25" x2="43" y2="25" stroke="#bc8cff" stroke-width="2"/>
      <line x1="40" y1="41" x2="37" y2="38" stroke="#f778ba" stroke-width="2"/>
      <line x1="25" y1="47" x2="25" y2="43" stroke="#58a6ff" stroke-width="2"/>
      <line x1="9" y1="41" x2="12" y2="38" stroke="#3fb950" stroke-width="2"/>
      <line x1="3" y1="25" x2="7" y2="25" stroke="#bc8cff" stroke-width="2"/>
      <line x1="9" y1="9" x2="12" y2="12" stroke="#f778ba" stroke-width="2"/>
      <!-- Rotating indicator arrow -->
      <line x1="25" y1="25" x2="25" y2="8" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round">
        <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="1.2s" repeatCount="indefinite"/>
      </line>
      <circle cx="25" cy="25" r="3" fill="#ffffff"/>
      <text x="25" y="60" fill="#8b949e" font-family="-apple-system,sans-serif" font-size="8.5" text-anchor="middle">8x PHASES</text>
    </g>
  </g>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    # Verify well-formedness
    xml.dom.minidom.parse(out_path)
    print(f"Generated and verified {out_path}")


def make_static_waveforms(raw_d_path, raw_b_path, outdir):
    """Plot static waveform PNG pairs (dark/light) for Design D (1.4 GHz) and Design B (6.0 GHz)."""
    # 1. Design D (1.4 GHz)
    d_data = sr.read_tran(raw_d_path)
    td = d_data["time"]
    t0_d = 15.0e-9
    T_out_d = 2.0 / 1.4e9
    t1_d = t0_d + 2.0 * T_out_d
    win_d = (td >= t0_d) & (td <= t1_d)
    tw_ps_d = (td[win_d] - t0_d) * 1e12

    # 2. Design B (6.0 GHz)
    b_data = sr.read_tran(raw_b_path)
    tb = b_data["time"]
    t0_b = 15.0e-9
    T_out_b = 2.0 / 6.0e9
    t1_b = t0_b + 3.0 * T_out_b
    win_b = (tb >= t0_b) & (tb <= t1_b)
    tw_ps_b = (tb[win_b] - t0_b) * 1e12

    configs = [
        ("D_1p4GHz", d_data, win_d, tw_ps_d, "Design D (1.4 GHz input to 700 MHz output, m=4, R=3 kΩ)", "2 Output Periods (1428.6 ps each)"),
        ("B_6GHz", b_data, win_b, tw_ps_b, "Design B (6.0 GHz input to 3.0 GHz output, m=4, R=2 kΩ)", "3 Output Periods (333.3 ps each)"),
    ]

    for mode in ["dark", "light"]:
        is_dark = (mode == "dark")
        bg_col = "#0d1117" if is_dark else "#ffffff"
        text_col = "#c9d1d9" if is_dark else "#24292f"
        spine_col = "#30363d" if is_dark else "#d0d7de"
        grid_col = "#30363d" if is_dark else "#eaeef2"
        tick_col = "#8b949e" if is_dark else "#57606a"

        ck_col = "#f0883e" if is_dark else "#d95f02"
        q1_col = "#58a6ff" if is_dark else "#0969da"
        q2_col = "#3fb950" if is_dark else "#1a7f37"
        q3_col = "#bc8cff" if is_dark else "#8250df"
        q4_col = "#f778ba" if is_dark else "#cf222e"

        signals = [
            ("CK", "v(ck)", ck_col),
            ("Q1", "v(q1)", q1_col),
            ("Q2", "v(q2)", q2_col),
            ("Q3", "v(q3)", q3_col),
            ("Q4", "v(q4)", q4_col),
        ]

        for tag, data, win, tw_ps, title, sub_x in configs:
            fig, axes = plt.subplots(5, 1, sharex=True, figsize=(8.0, 5.0), dpi=150)
            fig.patch.set_facecolor(bg_col)

            for ax, (lbl, key, col) in zip(axes, signals):
                ax.set_facecolor(bg_col)
                y = data[key][win]
                ax.plot(tw_ps, y, color=col, lw=1.4)
                ax.set_ylabel(f"{lbl}\n(V)", color=text_col, fontsize=8, rotation=0, ha="right", va="center")
                ax.tick_params(colors=tick_col, labelsize=7.5)
                for s in ax.spines.values():
                    s.set_color(spine_col)
                ax.grid(True, color=grid_col, linestyle="--", alpha=0.6)
                ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
                if key == "v(ck)":
                    ax.set_ylim(-0.1, 1.1)

            axes[-1].set_xlabel(f"Time (ps) — {sub_x}", color=text_col, fontsize=8.5)
            fig.suptitle(f"{title} — Spectre Transient", color=text_col, fontsize=9.5, y=0.98)
            fig.tight_layout()

            out_png = os.path.join(outdir, f"waveform_{tag}_{mode}.png")
            fig.savefig(out_png, facecolor=bg_col, edgecolor="none")
            plt.close(fig)
            print(f"Generated {out_png} ({os.path.getsize(out_png)//1024} KB)")


def make_waveform_animation(raw_d_path, outdir):
    """Generate animated GIF (<2 MB) and MP4 from real Design D Spectre transient simulation."""
    d_data = sr.read_tran(raw_d_path)
    t = d_data["time"]
    t0 = 15.0e-9
    T_out = 2.0 / 1.4e9
    t1 = t0 + 2.0 * T_out # 2 periods = 2857.14 ps
    win = (t >= t0) & (t <= t1)
    tw_ps = (t[win] - t0) * 1e12

    n_sweep_frames = 28
    n_hold_frames = 6
    total_frames = n_sweep_frames + n_hold_frames
    max_t = tw_ps[-1]

    signals = [
        ("CK (1.4 GHz)", "v(ck)", "#f0883e"),
        ("Q1 (700 MHz, 0°)", "v(q1)", "#58a6ff"),
        ("Q2 (700 MHz, 45°)", "v(q2)", "#3fb950"),
        ("Q3 (700 MHz, 90°)", "v(q3)", "#bc8cff"),
        ("Q4 (700 MHz, 135°)", "v(q4)", "#f778ba"),
    ]

    pil_frames = []

    for f_idx in range(total_frames):
        fig, axes = plt.subplots(5, 1, sharex=True, figsize=(6.6, 4.2), dpi=100)
        fig.patch.set_facecolor("#0d1117")

        if f_idx < n_sweep_frames:
            curr_t = (f_idx + 1) / n_sweep_frames * max_t
        else:
            curr_t = max_t

        f_win = tw_ps <= curr_t

        for ax, (lbl, key, col) in zip(axes, signals):
            ax.set_facecolor("#0d1117")
            y_all = d_data[key][win]
            y_sub = y_all[f_win]
            t_sub = tw_ps[f_win]

            ax.set_xlim(0, max_t)
            if key == "v(ck)":
                ax.set_ylim(-0.1, 1.1)
            else:
                ax.set_ylim(0.5, 1.1)

            # Faint background guide
            ax.plot(tw_ps, y_all, color=col, lw=0.7, alpha=0.15)
            # Active trace
            if len(t_sub) > 0:
                ax.plot(t_sub, y_sub, color=col, lw=1.6)
                # Tracking dot at edge
                ax.plot(t_sub[-1], y_sub[-1], marker="o", markersize=3.5, color="#ffffff")

            ax.set_ylabel(lbl, color="#c9d1d9", fontsize=6.8, rotation=0, ha="right", va="center")
            ax.tick_params(colors="#8b949e", labelsize=7)
            for spine in ax.spines.values():
                spine.set_color("#30363d")
            ax.grid(True, color="#30363d", linestyle="--", alpha=0.5)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=3))

        axes[-1].set_xlabel("Time (ps) — 2 Output Periods", color="#c9d1d9", fontsize=8)
        fig.suptitle("Spectre Transient: Design D 1.4 GHz Division in Action", color="#c9d1d9", fontsize=8.5, y=0.98)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor="#0d1117", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        pil_frames.append(img)

    # Save animated GIF
    gif_path = os.path.join(outdir, "division_action.gif")
    durations = [70] * n_sweep_frames + [140] * n_hold_frames
    pil_frames[0].save(
        gif_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    gif_kb = os.path.getsize(gif_path) // 1024
    print(f"Generated {gif_path} ({gif_kb} KB)")

    # Save MP4 video using ffmpeg
    mp4_path = os.path.join(outdir, "division_action.mp4")
    # Write frames to temp or use ffmpeg with image pipe
    ffmpeg_cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        "-r", "14",
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-movflags", "+faststart",
        mp4_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for frame in pil_frames:
        frame.save(proc.stdin, "JPEG")
    # Hold frames in video
    for _ in range(8):
        pil_frames[-1].save(proc.stdin, "JPEG")
    proc.stdin.close()
    proc.wait()
    mp4_kb = os.path.getsize(mp4_path) // 1024
    print(f"Generated {mp4_path} ({mp4_kb} KB)")


def make_pvt_heatmap(pvt_d_path, pvt_b_path, outdir):
    """Generate a combined PVT pass/fail matrix visualization for Design D and Design B."""
    def parse_pvt_tsv(path):
        grid = {} # corner -> { (temp, vdd): pass_bool }
        with open(path, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                parts = row["tag"].split("_")
                corner = parts[0]
                temp = parts[1]
                vdd = parts[2]
                divides = (int(row["divides"]) == 1)
                grid.setdefault(corner, {})[(temp, vdd)] = divides
        return grid

    d_grid = parse_pvt_tsv(pvt_d_path)
    b_grid = parse_pvt_tsv(pvt_b_path)

    corners = ["tt", "ff", "ss", "fs", "sf"]
    temps = ["-40", "27", "125"]
    vdds = ["0.9", "1.0", "1.1"]

    cols_x = []
    for t in temps:
        for v in vdds:
            cols_x.append((t, v))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 3.8), dpi=150)
    fig.patch.set_facecolor("#0d1117")

    for ax, grid, title, pass_info in [
        (ax1, d_grid, "Design D (1.4 GHz)", "41 / 45 Pass (91.1%)"),
        (ax2, b_grid, "Design B (6.0 GHz)", "21 / 45 Pass (46.7%)"),
    ]:
        ax.set_facecolor("#0d1117")
        matrix = np.zeros((len(corners), len(cols_x)))

        for i, c in enumerate(corners):
            for j, (t, v) in enumerate(cols_x):
                passed = grid.get(c, {}).get((t, v), False)
                matrix[i, j] = 1 if passed else 0

        # Draw matrix cells
        for i in range(len(corners)):
            for j in range(len(cols_x)):
                val = matrix[i, j]
                col = "#2ea043" if val == 1 else "#cf222e"
                rect = plt.Rectangle((j, i), 0.9, 0.9, facecolor=col, edgecolor="#30363d", lw=1)
                ax.add_patch(rect)
                text = "P" if val == 1 else "F"
                ax.text(j + 0.45, i + 0.45, text, color="#ffffff", ha="center", va="center", fontsize=8.5, fontweight="bold")

        ax.set_xlim(-0.1, len(cols_x))
        ax.set_ylim(-0.1, len(corners))
        ax.invert_yaxis()

        ax.set_xticks([j + 0.45 for j in range(len(cols_x))])
        x_labels = [f"{v}V\n{t}°C" if j % 3 == 1 else f"{v}V" for j, (t, v) in enumerate(cols_x)]
        ax.set_xticklabels(x_labels, color="#8b949e", fontsize=7.5)

        ax.set_yticks([i + 0.45 for i in range(len(corners))])
        ax.set_yticklabels([c.upper() for c in corners], color="#c9d1d9", fontsize=8.5, fontweight="bold")

        for spine in ax.spines.values():
            spine.set_color("#30363d")

        ax.set_title(f"{title}: {pass_info}", color="#c9d1d9", fontsize=10, fontweight="bold", pad=12)

    fig.suptitle("Spectre PVT Matrix: 5 Corners × 3 Temperatures × 3 Supply Voltages", color="#f0f6fc", fontsize=11, fontweight="bold", y=0.98)
    fig.tight_layout()

    out_png = os.path.join(outdir, "pvt_heatmap.png")
    fig.savefig(out_png, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Generated {out_png} ({os.path.getsize(out_png)//1024} KB)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate README assets")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Destination directory for assets")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    print(f"Generating assets in {args.outdir}...")

    # 1. Hero banner SVG
    make_hero_banner_svg(os.path.join(args.outdir, "hero_banner.svg"))

    # 2. Static SVG Badges
    badges = [
        ("badge_process.svg", "Process", "GPDK045 (45 nm)", "#2ea043"),
        ("badge_supply.svg", "Supply", "1.0 V nominal", "#1f6feb"),
        ("badge_status.svg", "Baseline", "v1.0-stable", "#238636"),
        ("badge_flow.svg", "EDA Flow", "Virtuoso / Spectre / Assura", "#8957e5"),
        ("badge_designd.svg", "Design D (1.4 GHz)", "41/45 Pass (91.1%)", "#2ea043"),
        ("badge_designb.svg", "Design B (6.0 GHz)", "3.78 deg phase error", "#f0883e"),
    ]
    for filename, lbl, val, col in badges:
        svg_content = make_badge_svg(lbl, val, col)
        path = os.path.join(args.outdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        xml.dom.minidom.parse(path)

    # 3. Mini bar SVGs for results table
    bars = [
        ("bar_pvt_91.svg", 41.0 / 45.0, "#2ea043"),
        ("bar_pvt_47.svg", 21.0 / 45.0, "#f0883e"),
        ("bar_pvt_0.svg", 0.0, "#cf222e"),
        ("bar_pvt_na.svg", 0.0, "#484f58"),
        # Power bars (relative to max 0.6 mW)
        ("bar_power_d.svg", 0.5413 / 0.60, "#58a6ff"),
        ("bar_power_b.svg", 0.4929 / 0.60, "#58a6ff"),
        ("bar_power_unsized.svg", 0.1375 / 0.60, "#58a6ff"),
        ("bar_power_paper.svg", 0.1652 / 0.60, "#cf222e"),
        # Delay bars (relative to 70 ps)
        ("bar_delay_d.svg", 25.99 / 70.0, "#3fb950"),
        ("bar_delay_b.svg", 27.94 / 70.0, "#3fb950"),
        ("bar_delay_unsized.svg", 62.21 / 70.0, "#f0883e"),
        # PDP bars (relative to 16 fJ)
        ("bar_pdp_d.svg", 14.067 / 16.0, "#a371f7"),
        ("bar_pdp_b.svg", 13.768 / 16.0, "#a371f7"),
        ("bar_pdp_unsized.svg", 8.557 / 16.0, "#a371f7"),
    ]
    for filename, ratio, col in bars:
        svg_content = make_bar_svg(ratio, col)
        path = os.path.join(args.outdir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        xml.dom.minidom.parse(path)

    # 4. Waveforms from real simulation data
    make_static_waveforms(RAW_D, RAW_B, args.outdir)

    # 5. Animated GIF and MP4
    make_waveform_animation(RAW_D, args.outdir)

    # 6. Combined PVT matrix heatmap
    make_pvt_heatmap(PVT_D, PVT_B, args.outdir)

    print("All README assets successfully generated.")


if __name__ == "__main__":
    main()
