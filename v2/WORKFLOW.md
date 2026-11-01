# v2 Workflow (WORKFLOW.md)

## Agent Roles

| Role | Who | Does |
|---|---|---|
| VM lane owner | One worker at a time | All guest runs (Spectre, Virtuoso, Assura); holds flock |
| Host analyst | agy/opencode/Haiku | TSV analysis, plots, tables, no guest calls |
| Manuscript owner | Host worker | Draft + claims register; no new numbers without evidence |
| Auditor | Different worker than author | Numbers audit, prose audit, visual review |
| Human | Project lead | Decisions D1-D6, push approval, secret cleanup |

## File-Ownership Map

| Path | Owner | Rule |
|---|---|---|
| v2/PLAN.md, SCHEDULE.md, RISKS.md | Human + planner | Edits by proposal only |
| v2/REQUIREMENTS.md, VERIFICATION_MATRIX.md | Analyst | Update status only with evidence |
| v2/TRADE_STUDY.md, CLAIMS_AUDIT.md | Analyst/auditor | New data appends; no silent edits |
| v2/MANUSCRIPT_OUTLINE.md, paper/ | Manuscript owner | Claims register enforced |
| results/gpdk045/* | VM lane owner | Append-only logs; never rewrite old logs |
| cadence/*, spectre/*, scripts/* | VM/analyst by task | Small diffs; record command |
| PROMPT.md, secrets | Human only | Workers never read or print |

Workers own ONLY v2/ plus their assigned evidence outputs. Do not touch /home/parshu/vm.
Do not run git commit or push; the human decides pushes.

## VM Lock Protocol

All guest commands run under flock /home/parshu/vm/vm.lock. One guest job at a time.
Check guest disk (df) before Assura/Spectre batches; use /dev/shm for tmp per
ASSURA_FLOW_NOTES.md. Record wall time per grid in the run log.

## Review Gates

1. Numbers audit: every table cell has evidence path + rerun command.
2. Prose audit: grep for banned leakage (1.8 V, 180 nm sizes, 0.5 deg, 2.2 mW, 3.2 GHz, 45 pct, 6.02 dB, FoM 282) unless newly measured.
3. Visual review: figure vs caption vs evidence corner match; ViVA vs script-plot labeled.

## RACI

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Enhancement choice | Analyst | Human | Auditor | All |
| VM runs | VM owner | Human | Analyst | All |
| Layout | VM owner | Human | Analyst | All |
| Manuscript | Mss owner | Human | Auditor | All |
| Audits | Auditor | Human | Mss owner | All |
| Push | Human | Human | All | All |
