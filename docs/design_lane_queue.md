# Design Lane — Active Workstream Queue

This file is the live state of the Design Lane. The playbook (`docs/design_lane.md`) defines how the lane operates; this file tracks what is in flight, what is done, and what is next. Update on every workstream status change.

## Active Session Plan

`/Users/westley/.claude/plans/fluffy-growing-kite.md`

## Workstream Status

| WS | Topic | Status | Output Location | Date |
|----|-------|--------|-----------------|------|
| WS0 | Document the Design Lane | done | `docs/design_lane.md`, `docs/design_lane_queue.md`, `CLAUDE.md`, memory | 2026-05-16 |
| WS1 | Bible context summary (`## Game Shape at a Glance` in hub) | done | `docs/bible/game_bible.md` | 2026-05-16 |
| WS2 | Multiplayer session-model fork (bridge fork only) | done (per-mission co-op + F1 host-faction shared w/ strict permissions; depth-dilution resolved via Lieutenant System pivot) | `docs/bible/game_bible.md ## In Flux` | 2026-05-16 |
| WS2.5 | Tactical-layer identity pivot — Lieutenant System + RTS framing kill | done substrate; Q1 (redesign cost) + Q3 (chronicle extension cost) open | `docs/bible/game_bible.md ## In Flux` | 2026-05-16 |
| WS3 | Strategic depth — REFRAMED 2026-05-16 to lieutenant-intelligence-first (Fork-A) then sim-dims (Fork-B). Fork A1 (Personality model) options presented, awaiting user pick. | in-progress (paused at Fork A1 awaiting-pick) | `docs/bible/bible_combat.md ## In Flux` (primary, Fork-A) + `docs/bible/bible_simulation.md ## In Flux` (secondary, Fork-B) | 2026-05-16 paused |
| WS4 | Multiplayer remaining forks | pending | `docs/bible/game_bible.md ## In Flux`; promote to `docs/bible/bible_multiplayer.md` after all forks lock | — |
| WS5 | Progression design — UI, player goals, achievements, experience curve, era unlocking | in-flight (own session) — substrate Fork 1 (Run Shape) open, awaiting Westley pick on options A–H; competitor matrix + Foundation vocab scan + Blue Ocean lens delivered. See `gentle-rising-compass.md ## Session Pause — 2026-05-16` | `docs/bible/game_bible.md ## In Flux` initially; spoke TBD (likely new `bible_progression.md` after locks) | 2026-05-16 paused |

## Next Up

WS0 → WS1 → WS2 → WS3 → WS4. Hard sequential. Hand-off pauses between every workstream per the playbook.

**WS5 forks off the main queue** — own Design Lane chat, own session plan (`/Users/westley/.claude/plans/gentle-rising-compass.md`). Substrate anchor = Lieutenant System + niche target locked in `game_bible.md ## In Flux` (2026-05-16). Does not gate on WS3/WS4 closure; can run parallel after this chat closes.

## Notes

- Order rationale (WS2 before WS3): the multiplayer session model constrains strategic-depth design (AI behaves differently in per-mission co-op vs. persistent shared world vs. async). Locking the MP substrate first prevents WS3 rework.
- WS4 promotion target: a new `bible_multiplayer.md` spoke gets created only after WS4 forks all lock — premature spoke creation invites self-contradiction during fork churn.
- When a workstream completes, mark its row as `done`, fill in the completion date, and update Next Up. When the entire session plan completes, archive this snapshot (move to `docs/random/deleted/` with a `CAPTURED <YYYY-MM-DD>` banner) and start a fresh queue file for the next session plan.
