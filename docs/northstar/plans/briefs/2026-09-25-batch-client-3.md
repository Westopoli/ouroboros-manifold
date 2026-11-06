# Client lane batch 3 (M-client, cwd `~/Projects/om-push/m3`), 2026-09-25

Standing rules: `2026-09-24-manager-client.md` and `leaf-mechanics.md` (leaves are `subagent_type: sonnet46-doer`; red first; one leaf per file at a time; merge lines to `~/Projects/om-push/queue.txt`; rebuild by copy on conflict; leaves work in fresh worktrees from `origin/main`, never from the m3 clone, which sits dirty on push/look6). Report to M0 ONCE when every item is pushed or blocked. No progress messages. No Claude agent plays the game; the 30B loop does.

Start only when `origin/main` carries sim batch 3: `tests/transport/test_pipe_units_move.py`, `test_pipe_chronicle_fragments.py`, `test_pipe_jump_entry_ticks.py` and `om_mission_get_region_delta` in `csrc/ouroboros_sim.h`. Check with `git -C ~/Projects/om-push/m0 fetch origin && git -C ~/Projects/om-push/m0 ls-tree --name-only origin/main tests/transport/`. If they are absent, wait (inline sleep loop, 5 minutes between checks, up to 2 hours), then start.

Facts from the sim lane you build against:
- `command` now issues a group move (om_command_group_move); units move at the slowest member's pace. Until T1-7-2 lands, interior units of a packed spawn can stay stuck; do not work around it in the client.
- `command` units array was capped at 256; T1-7-3 raises it. Select-all with 276 units drops 20 until then; do not work around it.
- Chronicle frame entries carry `fragment_ids` (three ints) and `fragment` = `fragment_ids[0]`; -1 means no fragment (cluster with no text-pass entry); 0 is a real id.
- Debrief frame `region_delta` carries military, economy, tension, population as applied by the mission's consequence; most bands apply zeros today (the table has one populated row).
- Entries after a jump carry ticks inside the jump window.

Order:
1. **C3-6, fragment -1 handling (QA-003 close).** The chronicle panel resolves prose from `fragment_ids`; a -1 renders the entry's structural line (category, regions, tick range) with no fragment text and no placeholder token. Test: `tests/test_chronicle_scroll.gd` gains a frame with `[-1,-1,-1]` and one with real ids; `tests/qa/desktop/test_flow_spine.py` chronicle step asserts at least one entry rendered after a 250-tick run and a jump. Then update `docs/legacy/agora_era/qa_backlog.md` row QA-003 to fixed with the evidence path.
2. **C4-8, debrief deltas.** Debrief shows the four region_delta values with their sign; zeros render as "no change". Test in `tests/test_briefing_debrief.gd` and `tests/test_debrief_live_ctypes.py` with a frame fixture carrying nonzero values.
3. **C5-4, movement on screen.** The tactical view already draws the live frame; verify a move order issued through the client reaches the pipe as one `command` for the whole selection and that unit positions change across frames (`tests/qa/desktop/test_tactical_play.py`: select the edge units of the spawn block, order a move 200 wu away, step 60 base ticks, assert at least one selected unit moved more than 50 wu; edge units move today even before T1-7-2). Plant: `move-order-dropped` (client sends per-unit commands) must be caught.
4. **QA-backlog hygiene.** Rows QA-001, QA-002, QA-004, QA-005, QA-006 are fixed on main: set their status and evidence in `docs/legacy/agora_era/qa_backlog.md` on a branch `push/qa-backlog` created from origin/main; this branch is from now the single writer of that file (the two 30B session branches `push/qa-2026-09-25-1/-2` conflicted on it; copy their real rows, drop the QA-004 parse-JSON artifact rows, then queue `docs qa-backlog push/qa-backlog`).
5. **Sweep row.** `scripts/run_godot_tests.sh` over the touched Godot tests, `tests/qa/desktop` in one pytest invocation; report counts.
