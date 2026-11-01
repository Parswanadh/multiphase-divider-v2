# presentation/styles.py
"""
Shared Claude-Style CSS and Interactive JS for Multiphase Divider Site.
"""

SHARED_CSS = """
:root {
  --bg: #FAF9F5;
  --bg-panel: #F2EFE8;
  --bg-card: #FFFFFF;
  --ink: #1F1E1D;
  --ink-muted: #6B6A63;
  --ink-faint: #8E8C84;
  --line: #E8E6DC;
  --line-subtle: #F0EDE4;
  --terracotta: #C96442;
  --terracotta-hover: #B55434;
  --terracotta-bg: #FDF5F2;
  --terracotta-border: #F3D3C7;
  --code-bg: #F5F3EC;
  --badge-done-bg: #E6F4EA;
  --badge-done-ink: #137333;
  --badge-partial-bg: #FEF7E0;
  --badge-partial-ink: #B06000;
  --badge-fail-bg: #FCE8E6;
  --badge-fail-ink: #C5221F;
  --serif: 'Iowan Old Style', 'Charter', 'Georgia', serif;
  --sans: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --mono: ui-monospace, 'SF Mono', Menlo, Consolas, Monaco, monospace;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.03);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.05);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.08);
}

[data-theme="dark"] {
  --bg: #1F1E1D;
  --bg-panel: #272523;
  --bg-card: #2B2927;
  --ink: #ECEAE4;
  --ink-muted: #A3A096;
  --ink-faint: #78756D;
  --line: #3D3A36;
  --line-subtle: #33312F;
  --terracotta: #D97757;
  --terracotta-hover: #E8896A;
  --terracotta-bg: #352622;
  --terracotta-border: #4D332B;
  --code-bg: #262422;
  --badge-done-bg: #1B3826;
  --badge-done-ink: #81C995;
  --badge-partial-bg: #3E3013;
  --badge-partial-ink: #FDD663;
  --badge-fail-bg: #3C1C1A;
  --badge-fail-ink: #F28B82;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.25);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.4);
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
  scroll-padding-top: 30px;
  font-size: 16px;
}

body {
  background-color: var(--bg);
  color: var(--ink);
  font-family: var(--sans);
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* Layout Architecture */
.app-container {
  display: flex;
  min-height: 100vh;
}

/* Left Sidebar Table of Contents */
#sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 310px;
  flex: none;
  background-color: var(--bg-panel);
  border-right: 1px solid var(--line);
  padding: 32px 20px 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 100;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--sans);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--terracotta);
  margin-bottom: 6px;
}

.brand-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--terracotta);
}

.sidebar-title {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 600;
  line-height: 1.25;
  color: var(--ink);
}

.sidebar-subtitle {
  font-size: 12.5px;
  color: var(--ink-muted);
  margin-top: 4px;
}

.nav-links-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-group-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin: 16px 10px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 13.5px;
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background-color: rgba(201, 100, 66, 0.08);
  color: var(--terracotta);
}

.nav-item.active {
  background-color: var(--bg-card);
  color: var(--terracotta);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
  border-left: 3px solid var(--terracotta);
}

.nav-num {
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--ink-muted);
  margin-right: 8px;
}

.nav-item.active .nav-num {
  color: var(--terracotta);
  font-weight: 700;
}

.sidebar-footer {
  padding-top: 16px;
  border-top: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease;
}

.theme-toggle-btn:hover {
  border-color: var(--terracotta);
  color: var(--terracotta);
}

.page-switcher-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  background: var(--terracotta);
  border: 1px solid var(--terracotta);
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.page-switcher-btn:hover {
  background-color: var(--terracotta-hover);
}

/* Mobile Header Bar */
.mobile-header {
  display: none;
  position: sticky;
  top: 0;
  background-color: var(--bg-panel);
  border-bottom: 1px solid var(--line);
  padding: 12px 20px;
  z-index: 90;
  align-items: center;
  justify-content: space-between;
}

.mobile-brand {
  font-family: var(--serif);
  font-weight: 600;
  font-size: 16px;
}

.mobile-menu-btn {
  background: var(--bg-card);
  border: 1px solid var(--line);
  color: var(--ink);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
}

/* Main Content Area */
main.main-content {
  flex: 1;
  min-width: 0;
  padding: 56px 64px 120px;
}

.content-wrap {
  max-width: 980px;
  margin: 0 auto;
}

/* Hero Header */
header.hero-header {
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--line);
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--terracotta);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.hero-eyebrow span.chip {
  background-color: var(--terracotta-bg);
  border: 1px solid var(--terracotta-border);
  padding: 2px 8px;
  border-radius: 6px;
}

h1.hero-title {
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1.18;
  font-weight: 500;
  letter-spacing: -0.015em;
  margin-bottom: 16px;
  color: var(--ink);
}

p.hero-subtitle {
  font-size: 18px;
  line-height: 1.6;
  color: var(--ink-muted);
}

.hero-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 28px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px dashed var(--line);
  font-size: 13.5px;
  color: var(--ink-muted);
}

.hero-meta-item strong {
  color: var(--ink);
  font-weight: 600;
}

/* Card Sections */
section.card-section {
  background-color: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 36px 40px;
  margin-bottom: 44px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

section.card-section:hover {
  box-shadow: var(--shadow-md);
}

.section-anchor-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}

h2.section-heading {
  font-family: var(--serif);
  font-size: 27px;
  font-weight: 500;
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-number {
  font-family: var(--mono);
  font-size: 16px;
  font-weight: 600;
  color: var(--terracotta);
  background-color: var(--terracotta-bg);
  border: 1px solid var(--terracotta-border);
  padding: 2px 10px;
  border-radius: 6px;
}

.permalink-icon {
  opacity: 0;
  font-size: 18px;
  color: var(--terracotta);
  text-decoration: none;
  transition: opacity 0.15s ease;
}

h2.section-heading:hover .permalink-icon {
  opacity: 1;
}

/* TL;DR Executive Callout */
.tldr-box {
  background-color: var(--terracotta-bg);
  border: 1px solid var(--terracotta-border);
  border-left: 4px solid var(--terracotta);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  margin-bottom: 26px;
}

.tldr-label {
  font-family: var(--sans);
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--terracotta);
  margin-bottom: 4px;
}

.tldr-text {
  font-size: 14.5px;
  line-height: 1.55;
  color: var(--ink);
}

/* Subheadings & Typography */
h3.subsection-heading {
  font-family: var(--serif);
  font-size: 20px;
  font-weight: 600;
  line-height: 1.35;
  margin: 32px 0 12px;
  color: var(--ink);
  border-bottom: 1px solid var(--line-subtle);
  padding-bottom: 6px;
}

p.body-text {
  font-size: 15.5px;
  line-height: 1.7;
  color: var(--ink);
  margin-bottom: 16px;
}

p.lead-text {
  font-size: 17px;
  line-height: 1.65;
  color: var(--ink);
  margin-bottom: 20px;
}

ul.bullet-list, ol.num-list {
  padding-left: 24px;
  margin-bottom: 20px;
}

ul.bullet-list li, ol.num-list li {
  font-size: 15px;
  line-height: 1.65;
  margin-bottom: 8px;
  color: var(--ink);
}

a.text-link {
  color: var(--terracotta);
  text-decoration: underline;
  text-underline-offset: 3px;
  transition: color 0.15s ease;
}

a.text-link:hover {
  color: var(--terracotta-hover);
}

/* Status Chips & Badges */
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.status-chip.done {
  background-color: var(--badge-done-bg);
  color: var(--badge-done-ink);
}

.status-chip.partial {
  background-color: var(--badge-partial-bg);
  color: var(--badge-partial-ink);
}

.status-chip.fail {
  background-color: var(--badge-fail-bg);
  color: var(--badge-fail-ink);
}

.category-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  background-color: var(--bg-panel);
  border: 1px solid var(--line);
  color: var(--ink-muted);
}

/* Responsive Tables */
.table-wrapper {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  margin: 20px 0 28px;
  box-shadow: var(--shadow-sm);
}

table.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  text-align: left;
}

table.data-table th, table.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}

table.data-table th {
  background-color: var(--bg-panel);
  font-weight: 600;
  font-size: 12.5px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--ink);
  white-space: nowrap;
}

table.data-table tr:last-child td {
  border-bottom: none;
}

table.data-table tr:hover td {
  background-color: rgba(201, 100, 66, 0.03);
}

table.data-table td.num {
  font-family: var(--mono);
  font-size: 13.5px;
  white-space: nowrap;
}

.source-tag {
  display: inline-block;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--ink-faint);
  background-color: var(--bg-panel);
  border: 1px solid var(--line);
  padding: 1px 6px;
  border-radius: 4px;
  margin-top: 4px;
}

/* Code Blocks with Copy Button */
.code-block-wrapper {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--code-bg);
  margin: 18px 0 26px;
  overflow: hidden;
}

.code-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background-color: var(--bg-panel);
  border-bottom: 1px solid var(--line);
  font-size: 12px;
  color: var(--ink-muted);
  font-family: var(--mono);
}

.copy-btn {
  background: var(--bg-card);
  border: 1px solid var(--line);
  color: var(--ink);
  font-family: var(--sans);
  font-size: 11.5px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.copy-btn:hover {
  border-color: var(--terracotta);
  color: var(--terracotta);
}

.copy-btn.copied {
  background-color: var(--badge-done-bg);
  border-color: var(--badge-done-ink);
  color: var(--badge-done-ink);
}

pre.code-content {
  padding: 16px 20px;
  overflow-x: auto;
  font-family: var(--mono);
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--ink);
}

code.inline-code {
  font-family: var(--mono);
  font-size: 13.5px;
  background-color: var(--code-bg);
  border: 1px solid var(--line);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--ink);
}

/* Figures & Gallery */
figure.content-figure {
  margin: 24px 0 32px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

figure.content-figure img {
  width: 100%;
  height: auto;
  display: block;
  cursor: zoom-in;
  transition: opacity 0.2s ease;
}

figure.content-figure img:hover {
  opacity: 0.95;
}

figcaption.figure-caption {
  padding: 12px 18px;
  font-size: 13.5px;
  color: var(--ink-muted);
  background-color: var(--bg-panel);
  border-top: 1px solid var(--line);
  line-height: 1.5;
}

figcaption.figure-caption strong {
  color: var(--ink);
}

/* Gallery Grid */
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 20px;
  margin: 24px 0;
}

.gallery-card {
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.gallery-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--terracotta);
}

.gallery-card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  display: block;
}

.gallery-info {
  padding: 12px 16px;
}

.gallery-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 4px;
}

.gallery-desc {
  font-size: 12.5px;
  color: var(--ink-muted);
  line-height: 1.4;
}

/* Lightbox Modal */
#lightbox-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(15, 14, 13, 0.92);
  z-index: 9999;
  justify-content: center;
  align-items: center;
  padding: 40px;
  backdrop-filter: blur(4px);
}

#lightbox-overlay.active {
  display: flex;
}

.lightbox-content-box {
  max-width: 92vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.lightbox-img-wrap {
  flex: 1;
  min-height: 0;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}

#lightbox-img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  display: block;
}

.lightbox-caption-bar {
  padding: 16px 24px;
  background: var(--bg-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  border-top: 1px solid var(--line);
}

#lightbox-caption {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.5;
}

.lightbox-close-btn {
  background: var(--bg-panel);
  border: 1px solid var(--line);
  color: var(--ink);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
}

/* Accordion / Q&A Cards */
.qna-accordion-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 20px 0 32px;
}

details.qna-card {
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

details.qna-card[open] {
  border-color: var(--terracotta);
  box-shadow: var(--shadow-sm);
}

summary.qna-summary {
  padding: 16px 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 15.5px;
  color: var(--ink);
  list-style: none;
  user-select: none;
}

summary.qna-summary::-webkit-details-marker {
  display: none;
}

.qna-question-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.qna-badge {
  font-family: var(--mono);
  font-size: 12px;
  background-color: var(--bg-panel);
  border: 1px solid var(--line);
  padding: 2px 7px;
  border-radius: 5px;
  color: var(--ink-muted);
}

.qna-chevron {
  font-size: 14px;
  color: var(--ink-faint);
  transition: transform 0.2s ease;
}

details.qna-card[open] .qna-chevron {
  transform: rotate(180deg);
  color: var(--terracotta);
}

.qna-body {
  padding: 16px 20px 20px;
  border-top: 1px solid var(--line-subtle);
  background-color: var(--bg);
}

.qna-answer {
  font-size: 15px;
  line-height: 1.65;
  color: var(--ink);
  margin-bottom: 12px;
}

.qna-quote-box {
  background-color: var(--terracotta-bg);
  border: 1px solid var(--terracotta-border);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--ink);
}

.qna-quote-box strong {
  color: var(--terracotta);
}

/* Checklist Cards (Section 10) */
.checklist-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0 32px;
}

.checklist-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background-color: var(--bg-card);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.checklist-card.completed {
  background-color: var(--bg-panel);
  border-color: var(--line-subtle);
  opacity: 0.85;
}

.checklist-card.completed .checklist-title {
  text-decoration: line-through;
  color: var(--ink-muted);
}

.checklist-cb {
  width: 19px;
  height: 19px;
  margin-top: 3px;
  accent-color: var(--terracotta);
  cursor: pointer;
}

.checklist-content {
  flex: 1;
}

.checklist-header-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.checklist-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

.checklist-meta {
  display: flex;
  gap: 8px;
}

.checklist-desc {
  font-size: 13.5px;
  color: var(--ink-muted);
  line-height: 1.5;
  margin-bottom: 6px;
}

.checklist-rationale {
  font-size: 12.5px;
  color: var(--terracotta);
  font-style: italic;
}

/* Progress bar for Backlog */
.progress-card {
  background: var(--bg-panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13.5px;
  font-weight: 600;
  margin-bottom: 8px;
}

.progress-bar-outer {
  width: 100%;
  height: 8px;
  background: var(--line);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-inner {
  height: 100%;
  background: var(--terracotta);
  width: 0%;
  transition: width 0.3s ease;
}

/* PVT Matrix Grid */
.pvt-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.pvt-grid-container {
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.pvt-cell {
  aspect-ratio: 1.3;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.pvt-cell:hover {
  transform: scale(1.08);
  box-shadow: var(--shadow-sm);
  z-index: 5;
}

.pvt-cell.pass {
  background-color: var(--badge-done-bg);
  color: var(--badge-done-ink);
  border-color: #B7E1CD;
}

.pvt-cell.fail {
  background-color: var(--badge-fail-bg);
  color: var(--badge-fail-ink);
  border-color: #F4C7C3;
}

.pvt-cell.selected {
  outline: 2px solid var(--ink);
  outline-offset: 1px;
}

.pvt-inspector-box {
  background-color: var(--bg-panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
  font-size: 13.5px;
  margin-top: 12px;
}

/* SVG Chart Wrappers */
.chart-box {
  background: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 20px 24px;
  margin: 18px 0;
}

.chart-title {
  font-size: 14.5px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--ink);
}

/* Glossary Page Specific Styles */
.glossary-controls-bar {
  position: sticky;
  top: 0;
  background-color: var(--bg);
  padding: 16px 0 20px;
  z-index: 50;
  border-bottom: 1px solid var(--line);
  margin-bottom: 30px;
}

.search-input-wrap {
  position: relative;
  margin-bottom: 14px;
}

.search-input {
  width: 100%;
  padding: 12px 18px 12px 42px;
  font-size: 15px;
  font-family: var(--sans);
  background-color: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
}

.search-input:focus {
  outline: 2px solid var(--terracotta);
  border-color: transparent;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-faint);
  font-size: 16px;
}

.category-filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.filter-chip-btn {
  background-color: var(--bg-card);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 12.5px;
  font-weight: 500;
  padding: 5px 12px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter-chip-btn:hover {
  border-color: var(--terracotta);
  color: var(--terracotta);
}

.filter-chip-btn.active {
  background-color: var(--terracotta);
  border-color: var(--terracotta);
  color: #FFFFFF;
  font-weight: 600;
}

.letter-jump-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px 0;
}

.letter-jump-link {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 26px;
  height: 26px;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.letter-jump-link:hover {
  background-color: var(--terracotta-bg);
  color: var(--terracotta);
}

.letter-jump-link.disabled {
  color: var(--ink-faint);
  pointer-events: none;
  opacity: 0.4;
}

.glossary-terms-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.glossary-entry-card {
  background-color: var(--bg-card);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 24px 28px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.glossary-entry-card:hover {
  border-color: var(--terracotta);
  box-shadow: var(--shadow-md);
}

.glossary-entry-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}

.glossary-term-name {
  font-family: var(--serif);
  font-size: 21px;
  font-weight: 600;
  color: var(--ink);
}

.glossary-def {
  font-size: 15px;
  line-height: 1.6;
  color: var(--ink);
  margin-bottom: 12px;
}

.glossary-project-box {
  background-color: var(--bg-panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  font-size: 13.5px;
  color: var(--ink);
  margin-bottom: 10px;
}

.glossary-project-box strong {
  color: var(--terracotta);
}

.glossary-cross-link {
  font-size: 13px;
  color: var(--terracotta);
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* Responsive Breakpoints */
@media (max-width: 1024px) {
  #sidebar {
    position: fixed;
    left: -320px;
    box-shadow: var(--shadow-lg);
  }

  #sidebar.open {
    transform: translateX(320px);
  }

  .mobile-header {
    display: flex;
  }

  main.main-content {
    padding: 32px 24px 80px;
  }

  section.card-section {
    padding: 24px 20px;
  }

  .pvt-grid-container {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 640px) {
  h1.hero-title {
    font-size: 30px;
  }

  h2.section-heading {
    font-size: 22px;
  }

  .pvt-grid-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Print Friendly Styles */
@media print {
  #sidebar, .mobile-header, .theme-toggle-btn, .page-switcher-btn, .copy-btn, #lightbox-overlay, .pvt-controls, .glossary-controls-bar {
    display: none !important;
  }

  body {
    background: #FFFFFF !important;
    color: #000000 !important;
    font-size: 12pt;
  }

  main.main-content {
    padding: 0 !important;
    width: 100% !important;
  }

  .content-wrap {
    max-width: 100% !important;
  }

  section.card-section {
    border: 1px solid #CCCCCC !important;
    box-shadow: none !important;
    padding: 16px !important;
    margin-bottom: 20px !important;
    page-break-inside: avoid;
  }

  a {
    color: #000000 !important;
    text-decoration: none !important;
  }
}
"""

SHARED_JS = """
// LocalStorage Theme Management
(function initTheme() {
  const savedTheme = localStorage.getItem('defense_site_theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
  }
})();

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('defense_site_theme', newTheme);
  updateThemeBtnText();
}

function updateThemeBtnText() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const btns = document.querySelectorAll('.theme-toggle-text');
  btns.forEach(b => {
    b.textContent = currentTheme === 'dark' ? 'Light Theme' : 'Dark Theme';
  });
}

// Mobile Sidebar Drawer
function toggleMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

// Copy Code Button Logic
function copyCode(btn, codeId) {
  const codeEl = document.getElementById(codeId);
  if (!codeEl) return;
  const text = codeEl.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span>✓</span> Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.classList.remove('copied');
    }, 2000);
  }).catch(err => {
    console.error('Copy failed:', err);
  });
}

// Lightbox Modal Logic
function openLightbox(imgSrc, captionText) {
  const overlay = document.getElementById('lightbox-overlay');
  const lbImg = document.getElementById('lightbox-img');
  const lbCaption = document.getElementById('lightbox-caption');
  if (overlay && lbImg) {
    lbImg.src = imgSrc;
    lbCaption.textContent = captionText || '';
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeLightbox() {
  const overlay = document.getElementById('lightbox-overlay');
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Global Keyboard Handler (Escape key)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeLightbox();
    const sidebar = document.getElementById('sidebar');
    if (sidebar && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
    }
  }
});

// Scrollspy for Sidebar
window.addEventListener('DOMContentLoaded', () => {
  updateThemeBtnText();
  
  const sections = document.querySelectorAll('section[id]');
  const navItems = document.querySelectorAll('.nav-item');
  
  if (sections.length > 0 && navItems.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          navItems.forEach(item => {
            if (item.getAttribute('href') === '#' + id) {
              item.classList.add('active');
            } else {
              item.classList.remove('active');
            }
          });
        }
      });
    }, {
      rootMargin: '-20% 0px -70% 0px'
    });
    
    sections.forEach(s => observer.observe(s));
  }
});
"""

print("Loaded shared styles and scripts.")