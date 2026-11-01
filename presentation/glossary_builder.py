# presentation/glossary_builder.py
"""
Builds presentation/glossary.html
"""
import os
import sys
import json
import html

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from presentation.glossary_data import GLOSSARY_TERMS
from presentation.styles import SHARED_CSS, SHARED_JS

def build_glossary_html():
    # Sort terms alphabetically by term name (case-insensitive)
    sorted_terms = sorted(GLOSSARY_TERMS, key=lambda x: x["term"].lower())
    
    # Extract unique categories
    categories = sorted(list(set(t["category"] for t in sorted_terms)))
    
    # Extract letters present
    letters_present = sorted(list(set(t["term"][0].upper() for t in sorted_terms if t["term"][0].isalpha())))
    all_letters = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    
    # Build Letter Jump Bar
    jump_links_html = []
    for l in all_letters:
        if l in letters_present:
            jump_links_html.append(f'<a href="#letter-{l}" class="letter-jump-link">{l}</a>')
        else:
            jump_links_html.append(f'<span class="letter-jump-link disabled">{l}</span>')
    letter_bar_html = "".join(jump_links_html)
    
    # Build Category Filter Chips
    cat_chips_html = [
        '<button class="filter-chip-btn active" data-category="all" onclick="filterCategory(\'all\', this)">All ({0})</button>'.format(len(sorted_terms))
    ]
    for c in categories:
        count = sum(1 for t in sorted_terms if t["category"] == c)
        cat_chips_html.append(f'<button class="filter-chip-btn" data-category="{html.escape(c)}" onclick="filterCategory(\'{html.escape(c)}\', this)">{html.escape(c)} ({count})</button>')
    cat_chips_str = "".join(cat_chips_html)
    
    # Build Terms HTML
    current_letter = ""
    terms_html_parts = []
    
    for t in sorted_terms:
        term_clean = t["term"]
        first_letter = term_clean[0].upper() if term_clean[0].isalpha() else "#"
        
        # Check if we transitioned to a new letter
        if first_letter != current_letter and first_letter != "#":
            current_letter = first_letter
            terms_html_parts.append(f'<div class="letter-section-marker" id="letter-{current_letter}"><h3 style="font-family:var(--serif);font-size:24px;border-bottom:2px solid var(--line);padding-bottom:6px;margin:24px 0 16px;color:var(--terracotta);">{current_letter}</h3></div>')
            
        term_id = "term-" + "".join(c.lower() if c.isalnum() else "-" for c in term_clean).strip("-")
        cat_clean = t["category"]
        def_clean = html.escape(t["definition"])
        proj_clean = html.escape(t["project"])
        link_target = html.escape(t["link"])
        
        # Map link to section title
        section_name = link_target.split("#")[-1] if "#" in link_target else "explainer"
        section_display_name = {
            "start": "Section 0: Rubric & Start",
            "paper": "Section 1: The Paper (Kuo et al.)",
            "theory": "Section 2: Theory & Physics",
            "timeline": "Section 3: Project Timeline",
            "results": "Section 4: Results Dashboard",
            "power-gap": "Section 5: Schematic vs Standalone",
            "layout": "Section 6: Layout & Physical Verification",
            "tools": "Section 7: Cadence Tool Tour",
            "gallery": "Section 8: Screenshots Gallery",
            "qna": "Section 9: Defense Q&A",
            "backlog": "Section 10: Pending Backlog",
            "v2-plan": "Section 11: v2 Plan for the Paper",
            "cheatsheet": "Section 12: Defense Cheat Sheet"
        }.get(section_name, "Explainer Site")
        
        terms_html_parts.append(f"""
        <article class="glossary-entry-card" id="{term_id}" data-category="{html.escape(cat_clean)}" data-term="{html.escape(term_clean.lower())}">
          <div class="glossary-entry-header">
            <h3 class="glossary-term-name">{html.escape(term_clean)}</h3>
            <span class="category-chip">{html.escape(cat_clean)}</span>
          </div>
          <p class="glossary-def">{def_clean}</p>
          <div class="glossary-project-box">
            <strong>In this project:</strong> {proj_clean}
          </div>
          <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
            <a href="{link_target}" class="glossary-cross-link">→ View in {html.escape(section_display_name)}</a>
            <span style="font-family:var(--mono);font-size:11px;color:var(--ink-faint);">#{html.escape(term_id)}</span>
          </div>
        </article>
        """)
        
    terms_body_html = "".join(terms_html_parts)
    
    # Sidebar Navigation categories
    sidebar_cat_links = []
    for c in categories:
        count = sum(1 for t in sorted_terms if t["category"] == c)
        sidebar_cat_links.append(f'<a href="javascript:void(0)" onclick="filterCategory(\'{html.escape(c)}\')" class="nav-item"><span>{html.escape(c)}</span><span class="category-chip" style="font-size:10.5px;">{count}</span></a>')
    sidebar_cats_html = "".join(sidebar_cat_links)

    glossary_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VLSI Defense Glossary: Multiphase Divide-by-Two CMOS Frequency Divider</title>
  <style>
{SHARED_CSS}
  </style>
</head>
<body>

  <!-- Mobile Header -->
  <header class="mobile-header">
    <div class="mobile-brand">Multiphase Divider Defense</div>
    <div style="display:flex;gap:8px;">
      <a href="explainer.html" class="mobile-menu-btn" style="text-decoration:none;font-weight:600;">Explainer</a>
      <button class="mobile-menu-btn" onclick="toggleMobileMenu()">Categories ☰</button>
    </div>
  </header>

  <div class="app-container">
    <!-- Left Navigation Sidebar -->
    <nav id="sidebar" aria-label="Glossary Navigation">
      <div class="sidebar-header">
        <div class="brand-badge">
          <span class="brand-dot"></span>
          <span>Technical Reference</span>
        </div>
        <h2 class="sidebar-title">Defense Glossary</h2>
        <div class="sidebar-subtitle">{len(sorted_terms)} Verified VLSI &amp; Systems Terms</div>
      </div>

      <div class="nav-links-container">
        <div class="nav-group-label">Quick Links</div>
        <a href="explainer.html" class="nav-item">
          <span>← Back to Defense Explainer</span>
        </a>
        <a href="#search-anchor" class="nav-item" onclick="document.getElementById('glossary-search').focus()">
          <span>🔍 Live Search</span>
        </a>

        <div class="nav-group-label">Browse by Category</div>
        <a href="javascript:void(0)" onclick="filterCategory('all')" class="nav-item active" id="nav-cat-all">
          <span>All Terms</span>
          <span class="category-chip" style="font-size:10.5px;">{len(sorted_terms)}</span>
        </a>
        {sidebar_cats_html}
      </div>

      <div class="sidebar-footer">
        <button class="theme-toggle-btn" onclick="toggleTheme()" aria-label="Toggle Color Theme">
          <span>🌓</span>
          <span class="theme-toggle-text">Dark Theme</span>
        </button>
        <a href="explainer.html" class="page-switcher-btn">
          <span>Explore Main Explainer →</span>
        </a>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <div class="content-wrap">

        <header class="hero-header" id="search-anchor">
          <div class="hero-eyebrow">
            <span class="chip">Self-Contained Companion</span>
            <span>Comprehensive Terminology Guide</span>
          </div>
          <h1 class="hero-title">VLSI Defense & EDA Glossary</h1>
          <p class="hero-subtitle">
            An alphabetical encyclopedia of 122 circuit design, device physics, sizing theory, physical layout, Cadence tool flow, and verification terms grounded in the 45&nbsp;nm GPDK045 multiphase frequency divider implementation.
          </p>
          <div class="hero-meta-bar">
            <div class="hero-meta-item">Total Terms: <strong>{len(sorted_terms)}</strong></div>
            <div class="hero-meta-item">Categories: <strong>{len(categories)}</strong></div>
            <div class="hero-meta-item">Process Node: <strong>Cadence GPDK045 (45 nm)</strong></div>
            <div class="hero-meta-item">Status: <strong>Traceable to Repo Evidence Logs</strong></div>
          </div>
        </header>

        <!-- Sticky Controls Bar -->
        <div class="glossary-controls-bar">
          <div class="search-input-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="glossary-search" class="search-input" placeholder="Search across terms, definitions, values, and project notes (e.g., Elmore, triode, M7, Assura, DRC, Ron)..." oninput="handleSearch(this.value)">
          </div>

          <div class="category-filter-chips">
            {cat_chips_str}
          </div>

          <div class="letter-jump-bar">
            {letter_bar_html}
          </div>

          <div style="margin-top:10px;font-size:13px;color:var(--ink-muted);display:flex;justify-content:space-between;align-items:center;">
            <span id="terms-count-display">Showing {len(sorted_terms)} of {len(sorted_terms)} terms</span>
            <button onclick="resetFilters()" style="background:none;border:none;color:var(--terracotta);font-size:12.5px;cursor:pointer;text-decoration:underline;">Reset Filters</button>
          </div>
        </div>

        <!-- Terms Output Grid -->
        <div class="glossary-terms-grid" id="glossary-container">
          {terms_body_html}
        </div>

        <div id="no-results-msg" style="display:none;padding:60px 20px;text-align:center;color:var(--ink-muted);background:var(--bg-card);border:1px dashed var(--line);border-radius:var(--radius-md);margin-top:20px;">
          <h3 style="font-family:var(--serif);font-size:20px;margin-bottom:8px;color:var(--ink);">No Matching Terms Found</h3>
          <p style="font-size:14.5px;">Try searching for a different keyword or resetting the category filter.</p>
          <button onclick="resetFilters()" style="margin-top:14px;padding:8px 16px;background:var(--terracotta);color:#fff;border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:600;">Reset Filters</button>
        </div>

        <footer style="margin-top:80px;padding-top:24px;border-top:1px solid var(--line);text-align:center;color:var(--ink-muted);font-size:13.5px;">
          <p>Cadence GPDK045 Multiphase Frequency Divider Project Defense: Static &amp; Self-Contained</p>
          <p style="margin-top:6px;"><a href="explainer.html" class="text-link">Return to Main Defense Explainer</a></p>
        </footer>

      </div>
    </main>
  </div>

  <script>
{SHARED_JS}

// Glossary Client-Side Search and Filtering
let activeCategory = 'all';
let searchKeyword = '';

function filterCategory(cat, btnEl) {{
  activeCategory = cat;
  
  // Update button classes in control bar
  const buttons = document.querySelectorAll('.filter-chip-btn');
  buttons.forEach(b => {{
    if (b.getAttribute('data-category') === cat) {{
      b.classList.add('active');
    }} else {{
      b.classList.remove('active');
    }}
  }});
  
  // Update sidebar active link
  const navItems = document.querySelectorAll('#sidebar .nav-item');
  navItems.forEach(item => {{
    item.classList.remove('active');
  }});
  if (cat === 'all') {{
    const allLink = document.getElementById('nav-cat-all');
    if (allLink) allLink.classList.add('active');
  }}
  
  applyGlossaryFilter();
}}

function handleSearch(val) {{
  searchKeyword = val.trim().toLowerCase();
  applyGlossaryFilter();
}}

function applyGlossaryFilter() {{
  const cards = document.querySelectorAll('.glossary-entry-card');
  const letterMarkers = document.querySelectorAll('.letter-section-marker');
  let visibleCount = 0;
  
  cards.forEach(card => {{
    const cardCat = card.getAttribute('data-category');
    const cardTerm = card.getAttribute('data-term');
    const cardText = card.innerText.toLowerCase();
    
    const matchesCat = (activeCategory === 'all' || cardCat === activeCategory);
    const matchesSearch = (searchKeyword === '' || cardText.includes(searchKeyword));
    
    if (matchesCat && matchesSearch) {{
      card.style.display = '';
      visibleCount++;
    }} else {{
      card.style.display = 'none';
    }}
  }});
  
  // Hide letter headers if all cards under them are hidden
  letterMarkers.forEach(marker => {{
    if (searchKeyword !== '' || activeCategory !== 'all') {{
      marker.style.display = 'none';
    }} else {{
      marker.style.display = '';
    }}
  }});
  
  // Update count display
  const countEl = document.getElementById('terms-count-display');
  const totalCards = cards.length;
  if (countEl) {{
    countEl.textContent = `Showing ${{visibleCount}} of ${{totalCards}} terms`;
  }}
  
  // No results message
  const noRes = document.getElementById('no-results-msg');
  if (noRes) {{
    noRes.style.display = visibleCount === 0 ? 'block' : 'none';
  }}
}}

function resetFilters() {{
  const searchInput = document.getElementById('glossary-search');
  if (searchInput) searchInput.value = '';
  searchKeyword = '';
  filterCategory('all');
}}
  </script>
</body>
</html>
"""

    out_path = os.path.join("presentation", "glossary.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(glossary_page)
    print(f"Built {out_path} ({len(glossary_page)} bytes, {len(sorted_terms)} terms)")

if __name__ == "__main__":
    build_glossary_html()