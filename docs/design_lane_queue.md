# Design Lane — Active Workstream Queue

This file is the live state of the Design Lane. The playbook (`docs/design_lane.md`) defines how the lane operates; this file tracks what is in flight, what is done, and what is next. Update on every workstream status change.

## Active Session Plan

`/Users/westley/.claude/plans/fluffy-growing-kite.md`

## Workstream Status

| WS | Topic | Status | Notes |
|----|-------|--------|-------|
| WS0 | Document the Design Lane | done | Lane playbook + queue + CLAUDE.md cross-refs landed |
| WS1 | Bible context summary (`## Game Shape at a Glance` in hub) | done | Folded into the hub during 2026-05-30 bible cleanse |
| WS2 | Multiplayer session-model fork (bridge fork only) | research-only — not committed | Multiplayer (per-mission co-op + host-faction shared, depth-dilution resolution) is alive as a research direction. See `docs/priority_queue.md` "Research-only" section. If picked up, opens a fresh Design Lane fork — not a resurrection of the 2026-05-16 bible In Flux prose. |
| WS2.5 | Tactical-layer identity — Lieutenant System | research-only — not committed | Lieutenant System is alive as a research direction. Substrate at `docs/research/topics/lieutenant_pivot_niche_brief.md` + feeder briefs. See `docs/priority_queue.md` "Research-only" section. RTS-framing kill carries forward unchanged (Steam-page-facing language is "pause-and-command tactical"). If picked up, opens fresh Design Lane fork. |
| WS3 | Strategic depth / sim-dimensions expansion | research-only — not committed | The "Cheap-Wide" sim-dimensions package (Legitimacy + Cohesion + Ideology-faction + Diplomacy-deepen + Logistics-derived + Intel-Lite) is alive as research. See `docs/priority_queue.md` "Research-only" section. Coupled to WS2.5 — if Lieutenant System ever promotes, WS3 re-opens against the picked substrate. |
| WS4 | Multiplayer remaining forks | research-only — not committed | All multiplayer detail forks (eligibility, invitation model, mid-mission join/leave, DLC parity, chronicle attribution, mission outcome ownership, rewind behavior, disconnect handling) sit behind WS2 staying research-only. If WS2 promotes, this opens too. |
| WS5 | Progression design — UI, player goals, achievements, experience curve, era unlocking | paused | Substrate fork (Run Shape, options A–H) open, awaiting Westley pick. Competitor matrix + Foundation vocab scan + Blue Ocean lens delivered in prior session. Original substrate anchor was Lieutenant System + niche target — both now research-only. WS5 can resume against current bible substrate (commander-not-king, generational chapters, single-player) or wait for WS2.5/WS3 promotion. |

## Next Up

WS0 + WS1 are done. WS2 / WS2.5 / WS3 / WS4 are research-only — no Design Lane work picks them up until Westley promotes one out of research. WS5 is the only workstream that could open next, against current bible substrate.

## Notes

- A workstream marked **research-only** means: the design fork remains alive in `docs/research/`, but the Design Lane is not actively working it. Its bible In Flux content was deleted in the 2026-05-30 / 2026-06-02 cleanse passes. When Westley says "open WS<X>," the workstream restarts with a fresh fork-enumeration pass against current bible state, not against the deleted In Flux prose.
- When a workstream completes, mark its row as `done`, fill in the completion date, and update Next Up. When the entire session plan completes, archive this snapshot (move to `docs/random/deleted/` with a `CAPTURED <YYYY-MM-DD>` banner) and start a fresh queue file for the next session plan.
