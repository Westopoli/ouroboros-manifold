# Look-judge rig: status 2026-11-24

Branch `s/look-judge-rig` (worktree `~/Projects/om-wt/look-judge-rig`), not merged to main, not pushed. Spec: `docs/northstar/plans/cascades/look-judge-rig/spec.md`. Decision: `DEC-look-judge-rig-2026-11-24`.

## Built and green (126 tests)
Core (cards, state checks, runner, page), backends (Ollama, `claude -p`, cache, calibration gate), render (sidecar, ID-colour render, pixel checks, wired into `fight_replay.gd`), ledger tool, trace comparison, daemon screenshot directory fix.

## Pilot results (state checks, `look_2026-11-19/`)
- A1: FAIL, units 82 and 120, 0.33 wu apart, last tick 1396 (matches the trace).
- A2: PASS. A3: FAIL (81 and 118, 123 ticks under one radius). A4: FAIL (two pairs).
- B1: trap `blue_wins` FAIL (red won); B2: FAIL (draw).
- Ledger `verify` on a backfilled row: PASS.

## Not done
- No vision model installed. Qwen3-VL needs a download (`ollama pull`), then the calibration gate over a render control set. The render-level control set (stacked pair, unit off position, frozen, blank PNGs with sidecars) is not built as files; only the synthetic ones inside the tests exist.
- Look cards are drafts. Westley approves them once: `scripts/look/cards/overlap.toml`, `trap.toml` (`trap.toml` carries R-097-05 as a placeholder id; the trap fights have no rule id).
- Walls: real fight files hold walls under `built_features`; the wall check returns UNSURE on them.
- Ledger holds 4 stage 3 rows. Stage 1 and 2 approvals are unrecoverable (see `2026-11-24-ledger-unrecovered.md`).
- `scripts/play.sh` has no `systemd-run` cap; runs here were wrapped by hand.
- Played-not-green landing step (open merged game with `scripts/play.sh`) not yet done.

## His to rule
Every `DRAFT-feel-*` in `scripts/look/tolerances.toml`; `DRAFT-look-false-pass-max` (0); frozen window, overlap radius (15 wu), position offset (2 px); pilot target.
