# Progress log (read this first after any context reset)

Updated: 2026-11-01 12:20 IST.

- v1 is finished, frozen and documented in STABLE.md (tag `v1.0-stable`, branch `stable/v1`, VM snapshot `stable-v1`). Do not modify the baseline.
- Active work on v2 of the paper is in the private repository https://github.com/Parswanadh/multiphase-divider-paper-v2 (local: /home/parshu/projects/multiphase-divider-paper-v2). Read its PROGRESS.md for status, rules, worker mapping and how to continue.
- In this repository, recent work: README with real-data waveform GIF and mp4, presentation site (explainer, glossary, 32 viva questions), a 20-slide defense deck (presentation/slides, one worker is fixing slide 7 and slide 14), repository cleanup (legacy/, v2/ plan copy).
- Preservation rule: never delete files. Move them to `no-rel/` (or `legacy/`) with a note in `no-rel/README.md`.
- Rules: workers never commit or push; models allowed are Codex (luna, terra, sol) and agy (Gemini); no Claude subagents; no number without an evidence file.
- Known problem: the Cadence guest does not boot after the laptop restart (powered off at `stable-v1`).

## Model policy (authoritative; the human set these rules)
- OpenCode: only the Go plan (provider prefix `opencode-go/`) and only `opencode-go/deepseek-v4.1-flash` and `opencode-go/muse-spark-1.3-contributor`. Never use Zen models (prefix `opencode/`), never free models (names ending `-free`, for example `opencode-go/beam-free`, `opencode-go/iceman-contributor-free`, `opencode/big-pickle`), never Pro or other models (kimi, glm, qwen, deepseek-v4-pro). Every OpenCode call passes `--model` explicitly; the global default in ~/.config/opencode/opencode.json is `opencode-go/muse-spark-1.3-contributor` (Go).
- OpenCode's 5-hour plan limit was reached on 2026-11-01; re-probe with `scripts/engine_probe.sh` before using it.
- Codex: `gpt-6-luna` (mechanical), `gpt-6.1-terra` (medium), `gpt-6.1-sol` (high stakes only); at most 3 at once; falls back to agy on a usage limit.
- agy: `gemini-3.8-flash-high`, for formatting and review.
- No Claude subagents (the human wants Claude limits preserved). Haiku is not used.
- Figure provenance: Cadence screenshots, plots from Spectre output, and script-drawn circuit diagrams are stated as such in the report (Tool and Technology section).
