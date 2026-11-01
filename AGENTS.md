# Agent Instructions: multiphase-divider-v2

## Project and frozen baseline
This repository contains the verified v1 baseline for the Cadence GPDK045 (45 nm) implementation of the Kuo et al. 8-phase divide-by-two CMOS divider at 1.0 V supply.
The v1 work is complete, graded, and permanently tagged as v1.0-stable on branch stable/v1 at commit 336d17b with VM snapshot stable-v1.
Never alter the data or semantics of tag v1.0-stable, because this represents the finished, examined course project baseline.
Any ongoing maintenance commits on branch main require review and must not invalidate published findings.
All ongoing v2 paper drafting, expanded parameter exploration, and preprint development take place in `/home/parshu/projects/multiphase-divider-paper-v2`; consult its `PROGRESS.md` for active assignments.

## Report generation
Rebuild the 25-page v1 system design report (`report/gpdk045/System_Design_Project_Report_gpdk045.pdf`) using the two-stage pipeline:
`/usr/bin/python3 scripts/make_report_data.py`
This script dynamically aggregates raw simulation TSVs from `results/gpdk045/final/` into `report/gpdk045/report_data.json` and executes `scripts/build_academic_docx.py`.
Never hardcode metrics into reporting logic, because numbers must originate from authenticated simulation logs.

## Presentation site and deployment
- Build presentation site: Regenerate the mobile-optimized explainer, glossary, and image assets into `site/`:
  `/usr/bin/python3 scripts/build_site.py`
- Validate site: Execute verification checks on HTML and asset paths:
  `/usr/bin/python3 presentation/verify_site.py`
- Cloudflare Pages deployment: Follow `docs/DEPLOY.md` to deploy `site/` with Wrangler after verifying that privacy scans show no tokens or passwords.

## README assets
Generate SVG badges and animated division waveform assets:
`/usr/bin/python3 scripts/make_readme_assets.py --outdir docs/readme`
Maintain explicit provenance: distinguish Cadence Virtuoso screenshots, Spectre waveform exports, and script-rendered schematic drawings, because academic integrity forbids misrepresenting simulated plots as physical layout captures.

## Hard rules
- Evidence requirement: Never state a performance number without an associated evidence file in `results/gpdk045/`, because unmeasured claims damage academic credibility.
- No unmeasured claims: Do not cite numbers from `legacy/` (preliminary 180 nm ngspice work) as GPDK045 metrics, because only 45 nm Cadence and Spectre data are valid.
- Two power variants: Always distinguish standalone netlist power (0.5413 mW for Design D) from Virtuoso netlist power (0.4554 mW), because layout-dependent device parameters create a 16 percent difference.
- Placement-only layout: Characterize layout solely as placement-only (21 Assura DRC errors); never claim LVS or post-layout simulation, because the PDK lacks extraction tech files.
- Commits forbidden: Never run git commit, git push, or git tag, because committer rights are reserved for the repository owner.
- File preservation: Never delete files; move superseded materials to `no-rel/` or `legacy/` with notes in `no-rel/README.md`, because full project history must remain accessible.

## Models and engines
Follow the model policy in `PROGRESS.md`:
- Claude subagents: Do not launch Claude subagents, because Claude limits are preserved for the operator.
- Codex limits: Run at most 3 concurrent Codex workers (gpt-6-luna for mechanical work, gpt-6.1-terra for medium work, gpt-6.1-sol for high-stakes steps).
- agy for review: Use agy (gemini-3.8-flash-high) for text editing, reviews, and HTML validation.
- OpenCode limits: Allowed only on Go tier (opencode-go/deepseek-v4.1-flash and opencode-go/muse-spark-1.3-contributor); free, Zen, and Pro models are forbidden.

## Tooling facts and pitfalls
- Python environment: Run scripts with `/usr/bin/python3`, because default PATH interpreters lack matplotlib and Pillow.
- VM lock: Coordinate any VM actions with `flock -o /home/parshu/vm/vm.lock`, because concurrent console access corrupts execution.
- VM boot state: The Cadence VM is powered off at snapshot stable-v1 due to a kernel boot hang; do not start simulation jobs.
- Progress logging: Record maintenance actions in `PROGRESS.md`.
