# v2 Risk Register (RISKS.md)

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Trigger |
|---|---|---|---|---|---|---|
| R1 | Fabricated-claim carryover: unverified mss numbers leak into v2 | High | High | Claims register + audit gate; prose audit before submit | Human | Any number without evidence file |
| R2 | Layout never clean: DRC/LVS block | High | Medium | Scope to DRC-count-down + mismatch list; manual route DLATCH m=4 (backlog a,b) | VM worker | DRC count stalls 2 sessions |
| R3 | Extraction unavailable (no qrc dir) | High | Medium | State as limit; pursue full PDK copy in parallel; no post-layout claims | Human | qrc dir still absent week 2 |
| R4 | VM single lane + one keyboard channel stalls queue | High | Medium | VM lock protocol; short grids; host lane for analysis/writing | VM owner | Queue wait above 1 day |
| R5 | Guest disk full / 32-bit tool fragility | Medium | High | Check df before runs; /dev/shm for Assura tmp; keep time for perl/gcc fixes | VM worker | Assura/Spectre tmp write fail |
| R6 | Tool licence limits (vcpfe placer, LXL auto) | Medium | Low | Hand placement fallback; record licence error as evidence | VM worker | Placer call fails |
| R7 | Worker stalls (VM or host agent idle) | Medium | Medium | Heartbeat in WORKFLOW.md; reassign lane on stall | Human | No update 24 h |
| R8 | Schedule slip: 2-4 week plan overruns | Medium | Medium | Weekly gates; fallback to correction letter (E1-lite) | Human | S1 exit missed |
| R9 | Public repo secret in PROMPT.md history | High | High | Rotate credential now; scrub history or switch file to env vars (backlog k); do not print secret | Human | Secret present in git log |
| R10 | Wrong supply/tech in prose (1.8 V, 180 nm) | Medium | High | SR-11 check; template header with 1.0 V / 45 nm | Manuscript owner | Draft mentions 1.8 V |
| R11 | Monte Carlo promised without model | Medium | Medium | SR-06: verify PDK statistical sections first; defer with reason if absent | Worker | No mismatch section found |
| R12 | Benchmark table errors | Medium | Medium | Retrieve each source value; drop unverified rows | Manuscript owner | Source not found |

Top note: R9 is a security task, not a paper task. Do it first and separately.
