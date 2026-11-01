# presentation/explainer_builder.py
"""
Builds presentation/explainer.html using template substitution.
"""
import os
import sys
import json
import html

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from presentation.styles import SHARED_CSS, SHARED_JS
from presentation.qna_data import QNA_CARDS
from presentation.backlog_data import BACKLOG_ITEMS

def prepare_output(output):
    """Convert referenced images and strip machine-specific absolute paths."""
    import re
    from pathlib import Path
    from PIL import Image
    asset_dir = Path("presentation/assets")
    refs = set(re.findall(r"assets/([\w.-]+\.png)", output))
    dimensions = {}
    for name in sorted(refs):
        source = asset_dir / name
        target = source.with_suffix(".webp")
        with Image.open(source) as im:
            if im.width > 1200:
                im.thumbnail((1200, 100000), Image.Resampling.LANCZOS)
            im.save(target, "WEBP", quality=82, method=6)
            dimensions[target.name] = im.size
        output = output.replace("assets/" + name, "assets/" + target.name)
    first = True
    def image_attributes(match):
        nonlocal first
        tag = match.group(0)
        src = re.search(r'src="assets/([^"]+\.webp)"', tag)
        if not src:
            return tag
        width, height = dimensions[src.group(1)]
        loading = "eager" if first else "lazy"
        first = False
        return tag[:-1] + f' width="{width}" height="{height}" loading="{loading}" decoding="async">'
    output = re.sub(r'<img\b[^>]*>', image_attributes, output)
    output = re.sub(r'/home/[^\s<`"\)]+', lambda m: m.group(0).split('/')[-1], output)
    return output

def build_explainer_html():
    # Load PVT JSON data
    pvt_path = os.path.join("presentation", "assets", "pvt_data.json")
    with open(pvt_path, "r", encoding="utf-8") as f:
        pvt_data = json.load(f)
    
    pvt_d = pvt_data["D"]
    pvt_b = pvt_data["B"]
    
    # Render PVT Matrix Cells (D_1p4)
    d_cells_html = []
    for item in pvt_d:
        status_cls = "pass" if item["divides"] else "fail"
        tag = item["tag"]
        corner = item["corner"]
        temp = item["temp"]
        vdd = item["vdd"]
        reason = item["reason"]
        
        d_cells_html.append(f"""
        <div class="pvt-cell {status_cls}" 
             data-corner="{corner}" data-temp="{temp}" data-vdd="{vdd}" data-tag="{tag}"
             title="{tag} ({status_cls.upper()}): {reason}"
             onclick="inspectCorner('D', '{tag}')">
          <span style="font-size:10px;opacity:0.85;">{corner}</span>
          <span>{temp}°</span>
          <span style="font-size:9.5px;font-family:var(--mono);">{vdd}V</span>
        </div>
        """)
    d_grid_str = "".join(d_cells_html)

    # Render PVT Matrix Cells (B_6g)
    b_cells_html = []
    for item in pvt_b:
        status_cls = "pass" if item["divides"] else "fail"
        tag = item["tag"]
        corner = item["corner"]
        temp = item["temp"]
        vdd = item["vdd"]
        reason = item["reason"]
        
        b_cells_html.append(f"""
        <div class="pvt-cell {status_cls}" 
             data-corner="{corner}" data-temp="{temp}" data-vdd="{vdd}" data-tag="{tag}"
             title="{tag} ({status_cls.upper()}): {reason}"
             onclick="inspectCorner('B', '{tag}')">
          <span style="font-size:10px;opacity:0.85;">{corner}</span>
          <span>{temp}°</span>
          <span style="font-size:9.5px;font-family:var(--mono);">{vdd}V</span>
        </div>
        """)
    b_grid_str = "".join(b_cells_html)

    # Render Q&A Cards (Section 9)
    qna_groups = {}
    for card in QNA_CARDS:
        grp = card["group"]
        if grp not in qna_groups:
            qna_groups[grp] = []
        qna_groups[grp].append(card)
        
    qna_html_parts = []
    q_index = 1
    for grp_name, cards in qna_groups.items():
        qna_html_parts.append(f'<h4 style="font-family:var(--serif);font-size:18px;margin:24px 0 12px;color:var(--terracotta);border-bottom:1px solid var(--line);padding-bottom:4px;">{html.escape(grp_name)}</h4>')
        qna_html_parts.append('<div class="qna-accordion-group">')
        for c in cards:
            q_id = c["id"]
            q_text = html.escape(c["question"])
            a_text = html.escape(c["answer"])
            n_text = html.escape(c["numbers"])
            qna_html_parts.append(f"""
            <details class="qna-card" id="{q_id}">
              <summary class="qna-summary">
                <div class="qna-question-wrap">
                  <span class="qna-badge">Q{q_index}</span>
                  <span>{q_text}</span>
                </div>
                <span class="qna-chevron">▼</span>
              </summary>
              <div class="qna-body">
                <p class="qna-answer">{a_text}</p>
                <div class="qna-quote-box">
                  <strong>Numbers to quote:</strong> {n_text}
                </div>
              </div>
            </details>
            """)
            q_index += 1
        qna_html_parts.append('</div>')
    qna_body_str = "".join(qna_html_parts)

    # Render Backlog Checklist (Section 10)
    backlog_html_parts = []
    for item in BACKLOG_ITEMS:
        item_id = item["id"]
        letter = item["letter"]
        title = html.escape(item["title"])
        priority = item["priority"]
        effort = html.escape(item["effort"])
        desc = html.escape(item["description"])
        rationale = html.escape(item["rationale"])
        
        prio_chip_cls = "fail" if priority == "High" else ("partial" if priority == "Medium" else "done")
        
        backlog_html_parts.append(f"""
        <div class="checklist-card" id="card-{item_id}">
          <input type="checkbox" class="checklist-cb" data-id="{item_id}" onchange="handleBacklogCheck(this)">
          <div class="checklist-content">
            <div class="checklist-header-line">
              <span class="checklist-title">({letter}) {title}</span>
              <div class="checklist-meta">
                <span class="status-chip {prio_chip_cls}" style="font-size:11px;">{priority} Priority</span>
                <span class="category-chip">{effort}</span>
              </div>
            </div>
            <p class="checklist-desc">{desc}</p>
            <p class="checklist-rationale"><strong>Rationale / Impact:</strong> {rationale}</p>
          </div>
        </div>
        """)
    backlog_body_str = "".join(backlog_html_parts)

    # Read template string from explainer_template.html
    template_path = os.path.join("presentation", "explainer_template.html")
    with open(template_path, "r", encoding="utf-8") as tf:
        template = tf.read()

    # Perform safe replacements
    pvt_json_str = json.dumps(pvt_data)
    
    output = template
    output = output.replace("/* [[SHARED_CSS]] */", SHARED_CSS)
    output = output.replace("/* [[SHARED_JS]] */", SHARED_JS)
    output = output.replace("<!-- [[D_GRID]] -->", d_grid_str)
    output = output.replace("<!-- [[B_GRID]] -->", b_grid_str)
    output = output.replace("<!-- [[QNA_BODY]] -->", qna_body_str)
    output = output.replace("<!-- [[BACKLOG_BODY]] -->", backlog_body_str)
    output = output.replace("/* [[PVT_DATA_JSON]] */", pvt_json_str)

    output = prepare_output(output)
    out_path = os.path.join("presentation", "explainer.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Built {out_path} ({len(output)} bytes)")

if __name__ == "__main__":
    build_explainer_html()
