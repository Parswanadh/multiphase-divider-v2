# GitHub README Presentation Research

Web search was available and verified against current GitHub Flavored Markdown (GFM) rendering rules.

## 1. Techniques Found

* HTML Sanitization: GitHub strips `<script>`, `<style>`, `<iframe>`, `<video>`, `<embed>`, `<form>`, and attributes like `class` or `id`. Permitted elements include `<details>`, `<summary>`, `<picture>`, `<source>`, `<img>`, `<table>`, `<kbd>`, `<sup>`, `<sub>`, `<p>`, and attributes `align`, `width`, `height`.
* Theme Adaptation: `<picture>` containing `<source media="(prefers-color-scheme: dark)" srcset="...">` and `<img src="...">` enables dark and light mode asset switching. URL fragments like `#gh-dark-mode-only` are deprecated.
* Alerts: Standard syntax `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, and `> [!CAUTION]` renders styled callout containers.
* Diagrams and Math: Native client-side Mermaid via fenced code blocks (flowcharts, sequence diagrams, state diagrams). Math equations render through MathJax with `$inline$` and `$$block$$`.
* Animated Vector Graphics: SVG files rendered inside `<img>` support SMIL animations (`<animate>`, `<animateTransform>`) and internal CSS keyframes (`@keyframes`). JavaScript inside SVGs is disabled.
* Video Embeds: In-page playback of `.mp4` occurs solely for GitHub CDN URLs (`user-attachments/assets`). Repository-relative `.mp4` files trigger download prompts rather than in-page playback. Standard practice is an animated preview loop (GIF or animated SVG) linking to the video file.
* Badges: Third-party services (for example shields.io) introduce latency, privacy concerns, and availability dependencies. Local static SVG badges eliminate external requests.
* Loading Budget: Total README page asset weight should stay below 6 MB. Individual animated GIFs should remain under 2 MB to avoid mobile browser stutter and bandwidth waste.

## 2. Techniques Adopted

* Animated SVG Hero Banner: Vector-based header with circuit ring animation. Fast load, crisp resolution on high-DPI displays, zero external dependencies.
* Dark and Light Mode Waveforms: `<picture>` elements for static transient plots ensuring legibility across light and dark GitHub interfaces.
* Real Spectre Waveform GIF and MP4: Generated directly from transient simulation data (`results/gpdk045/final/D_1p4.raw`). Kept under 2 MB with an MP4 link for smooth playback.
* Native Alerts: Applied for technical caveats (placement-only status, lack of RCX files, schCheck warning).
* Local Static SVG Badges: Self-contained SVGs committed to `docs/readme/` for technology node, supply voltage, and status.
* Collapsible Details: `<details>` blocks for Virtuoso, OCEAN, and VM invocation steps to preserve document readability.
* Mermaid Diagrams: Native text-based flowcharts for the EDA tool execution sequence and repository architecture.
* Inline SVG Result Visuals: Mini horizontal bar graphs embedded in the results table for immediate visual comparison without external libraries.

## 3. Techniques Rejected and Rationale

* External Badge Services (shields.io, badgen.net): Rejected. External servers can fail, track users, or introduce network latency.
* Dynamic Profile/Repo Stats Widgets (github-readme-stats): Rejected. They rely on third-party Heroku/Vercel services and violate air-gapped reproducibility.
* Raw `<video>` and `<iframe>` Tags: Rejected. Stripped unconditionally by GitHub HTML sanitizers.
* Pure CSS in Markdown: Rejected. GitHub sanitizes raw `<style>` blocks in markdown body.
* Heavy Full-Duration Waveform GIFs: Rejected. A full 40 ns simulation capture produces multi-megabyte files; truncated to 2 steady-state cycles to honor the 2 MB limit.
