# Progress log (read this first after any context reset)

Updated: 2026-11-01 11:50 IST.

- v1 is finished, frozen and documented in STABLE.md (tag `v1.0-stable`, branch `stable/v1`, VM snapshot `stable-v1`). Do not modify the baseline.
- Active work on v2 of the paper is in the private repository https://github.com/Parswanadh/multiphase-divider-paper-v2 (local: /home/parshu/projects/multiphase-divider-paper-v2). Read its PROGRESS.md for status, rules, worker mapping and how to continue.
- In this repository, recent work: README with real-data waveform GIF and mp4, presentation site (explainer, glossary, 32 viva questions), a 20-slide defense deck (presentation/slides, one worker is fixing slide 7 and slide 14), repository cleanup (legacy/, v2/ plan copy).
- Preservation rule: never delete files. Move them to `no-rel/` (or `legacy/`) with a note in `no-rel/README.md`.
- Rules: workers never commit or push; models allowed are Codex (luna, terra, sol) and agy (Gemini); no Claude subagents; no number without an evidence file.
- Known problem: the Cadence guest does not boot after the laptop restart (powered off at `stable-v1`).
