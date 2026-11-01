# no-rel: files that are not part of the deliverable but are kept

Nothing in this repository is deleted when it stops being relevant. It is moved here (or to `legacy/`) so the work stays available and can be restored.

| Folder | What it is | Why it is here |
|---|---|---|
| `agent-loop-scaffolding/` | Scripts, config, state and logs of the first automated agent loop (`run_swarm.sh`, `run_anthro_loop.sh`, `agent_dashboard`, `paper_review_ui`, `config/`, `state/`, `logs/`, `opencode.jsonc`) | Written in the first phase, before any Cadence run. Not used by the final results. |
| `../legacy/` | The early local ngspice study with a generic 180 nm model | Its numbers are not GPDK045 results and must not be quoted. |
| `../v2/legacy_draft/` | The early v2 manuscript draft and roadmap | Its numbers were never measured. See `v2/CLAIMS_AUDIT.md`. |

Not stored here: `PROMPT.md` of the first phase contains a plaintext password. Keeping it in a public repository would expose it again, so the file exists only in the local, git-ignored `reference/` folder. Rotate that password.

Restore a file with `git mv no-rel/<path> <destination>`.
