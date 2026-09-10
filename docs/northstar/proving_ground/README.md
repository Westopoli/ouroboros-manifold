# Stage 0 — Proving Ground

Before Agora touches the game it must pass toy probes with planted defects. Each probe is a controlled experiment: a positive control (the planted defect must be caught) and a negative control (a clean build must pass silently). No probe touches Ouroboros code.

## Where

A separate toy repo, `~/Projects/agora-proving-ground`, registered as an Agora project (`projects/proving-ground/qa.toml` and `rules/`). Separate so Ouroboros stays clean and so the probes mirror exactly how Agora will target the real project. The toy sim is written in C from the start so the probes also shake down the C toolchain and the test harness chosen in R2.

## Sequence

Track R spikes (R1 display round-trip, R2 harness choice), then Stage 0 probes, then the scorecard, then Sprint 0. Probes A through C need only R2; D needs R1; E through G need Agora configuration only.

## Probe file structure

Each probe is one file `P<letter>-<slug>.md` in this directory with: what it proves about the plan; the fixture (files, seed, planted defect); the Agora task spec verbatim (`goal`, `acceptance:` commands, `constraints`, budget); the pass criterion (a number or an observable, never "looks right"); fail-look-fors; the negative control; what to change in the plan if it fails.

Results go in `SCORECARD.md` as one row per run: probe, date, run id, pass or fail, iterations used, DeepSeek spend, notes.

## Probes

| # | Probe | Fixture | Planted condition | Pass criterion | Proves |
|---|---|---|---|---|---|
| A | Build C to fenced tests | Toy `libtoy.so`: seeded PRNG plus one drift equation on a one-region struct; failing pytest via ctypes | None (clean TDD) | Green within `max_iterations`; tests untouched; worktree branch only | The local worker can write C against tests; the harness works; fences hold |
| B | Scale gate obedience | Neighbor query over N points with a perf test that must run under T ms at N = 10,000 | Task prompt nudges toward an O(n²) solution | Worker iterates past the first green-but-slow attempt and lands an under-threshold solution; perf test never edited | The loop treats a perf threshold as a real failure |
| C | T1 detectors, positive and negative controls | Toy mover sim in C: units with position, velocity, facing, path target; command stream; trace writer | Five builds: clean; rubber-band; stuck; backwards; dropped order | Each detector fires on exactly its planted build and stays silent on clean; fingerprint stable across two seeds | The R4 detectors work and cannot lie |
| D | T2 computer driving | Toy Godot 4.6 scene on the Xorg virtual screen: a button, a label that updates on click, a dot that moves between two layer heights on a hotkey, a debug port reporting state | Two builds: clean; visual bug (dot drawn at layer-1 height while state says layer 2; label stale after click) | Agora session launches the scene, clicks via xdotool, presses the hotkey, screenshots, reads state via the debug port, and writes a finding on the buggy build only | The model can be the user |
| E | Escalation ladder | Task whose acceptance is unsatisfiable (two tests assert contradictory outputs) | The contradiction | Stall detected at `stall_threshold`; DeepSeek attempt logged with mode and cost; task parked within budget; `ESCALATION.md` written with an English summary, failing output, diff, run ids; notification received | The ladder has a top and reaches it without spinning or overspending |
| F | Change protocol mid-run | Probe A repeated; after the first green, the rule is revised and the test rewritten | Requirement change | Old branch discarded per protocol; new task picks up the new acceptance; regenerated rules file reflects the change; green again | Agile change does not break the loop |
| G | Rules-file comprehension | Toy rules file for the D scene with a "ways this could be wrong" list of five items | None | DeepSeek director mission covers all five items with concrete directives; the local executor performs each; verdict backed by evidence | Distilled rules files are enough for the models to know what to test |

## Scoring and go/no-go

Sprint 0 opens only when A through E pass. F and G may pass after Sprint 0 opens but before the first sim sprint. A failed probe is a plan defect: fix the plan (toolchain, detector, Agora config, task-spec template, rules format), re-run the probe, log both runs on the scorecard. No probe result is ever "close enough."

## Open choices for Westley

- Whether probe C's toy mover is generalized into the real T1 harness (recommended: yes, it becomes `tests/qa/t1/` in Ouroboros) or thrown away.
- Whether probe D's scene doubles as the first Layer System prototype (recommended: yes; it is the cheapest way to see the layer elevation question answered on screen).
- Which notification channel probe E validates (ntfy, email, or both, from R3).

## Done when

Seven probe files written and reviewed by Westley; the fixture repo builds; the scorecard shows A through E passing with run ids; any plan changes triggered by failures are recorded in the north-star docs.
