# Plan: from "every item landed" to a mission that plays (2026-10)

Approved by Westley 2026-09-30. The coordinating chat (any tier) runs Waves A to C from this file; Wave 0 was done by the Architect and its outputs are listed under "Wave 0 status" below. Companion: `docs/northstar/plans/archive/2026-09-30-work-list.md` (the reach-triage mapping, 89 rows, landed 0848ebb). Architect rulings on its flagged rows: `om_chronicle_generate_map_keyframes` stays with C5 (G-C3); the four R-061 commander-death symbols belong to B7; the R-126-04 force-sizing pair moves into B4; the event wrappers and breakaway creators under the C6 sweep go live through A1 and need no unit of their own.


## Context

Every MVP build item is ledgered as landed (bk-53), but the reach triage (`~/Projects/om-push/logs/reach_triage_2026-09-28.md`) and tonight's QA screenshots show the live game does not do what the bible says. Verified against `origin/main` today (no live caller for each): the event template library never loads, so no event fires in play and the chronicle stays empty (QA-003); the mission-selection score's conflict, chain, relevance and preference terms are never set; the briefing is never assembled; the enemy state machine never evaluates a transition; the commander, rivals, refusal, abilities and structures are unreachable; the chapter lifecycle after a jump (selector, collapse) never runs. On screen: a placeholder modal blocks Deploy, the briefing shows zeros, the tactical view shows one clipped unit and no HUD, the galaxy is a hairball.

Landed since the triage, so not in this plan: mission scoring and termination (B9-14), the mission clock (B9), the opening jump (T1-17), macro group orders advance/hold/rout (B13-8), the G1 SimBridge cut (partial), HDR4 accessors, gate lints. Today's relay queue (`docs/northstar/plans/briefs/2026-09-30-sonnet-relay/`) lands the 30 to 60 minute clock, four register answers, the QA gate and two visual checks; this plan starts after it.

Parked, not in this plan: multiplayer, the Haiku flagger, era-feel differentiation, paired economy.

Westley's decisions today (2026-09-30): Q-080-03 stays open (difficulty is a no-op in the MVP; the flag stays on E-10 S-080). Hold-zone required duration is a fixed 10 minutes (new rule, R-075-02). Execution is full tiers with **Sonnet 5.5 as the Doer** (the 4.6 doer retires). Tactical pieces are cut from the QA evidence, not from a first-look session.

## How the work runs

Architect (Fable) writes rules, contract shapes and briefs, and rules on reports. Engineer (`subagent_type: engineer`, Sonnet 5.5) writes every piece's tests first and does git and merge clerking. Doer (new `subagent_type: doer`, Sonnet 5.5) builds one unit per brief. All rules of the gap-fix plan hold: tests red first, one owner per file (`pieces.toml`), about one file and under 100 lines per unit, contract changes land first as docs-profile pieces, no stacked branches, clerk lands, builders push and stop, agents report once. Nothing is spawned in plan mode.

Order: Wave 0, then A, B, C in order; inside a wave the numbered items run in parallel where they own different files. Each item lists the rule it proves, the owner file, and the test. Piece ids follow the attached owner (`B9-N` mission.c, `T1-N` om_pipe.c, `B13-N` enemy_macro.c, `C2-N` galaxy, `C5-N` tactical_c, `C3-N` chronicle, `C6-N` briefing; new files get a `pieces.toml` row first).

## Wave 0 status (done 2026-09-30 unless marked)

1. Doer on 5.5: DONE, commit f005eaa (`.claude/agents/doer.md`, `sonnet46-doer.md` deleted, CLAUDE.md). Loads after a session restart.
2. Rules: DONE in this commit. R-075-02 hold-zone required = 10 minutes; Q-080-03 marked deferred (difficulty is a no-op in the MVP); R-030-01 says the launch library loads at `set_seed`. The other behaviours already have rules: R-055-04 and R-062-01 (selector and collapse after the jump), R-065-02 (consequence entry 1), R-067-01..03 (chains and categories), R-120-01..R-121-04 (patrol, ambush, transitions), R-126-01/02 (structures placed, units materialise), R-103-01 and R-104-01 (camera, HUD), R-078-05 (refuse), R-079-02 (briefing controls are Accept and Refuse only). No new Q rows were needed.
3. Reach triage work list: Engineer task, output `docs/northstar/plans/archive/2026-09-30-work-list.md`.
4. `pieces.toml` rows: part of the same Engineer task.

Lane merge (2026-09-30): every lane branch is landed or superseded except `push/HDR4-2` (conflicts in 10 files; its briefing node/radius/force tests and the `wt/HDR4-2-r` rebuild are the starting point for A4) and `push/W-1` (probably superseded by W-1a..f; decide before Wave B4).

## Wave 0: rails (as planned)

1. **Doer on 5.5.** New `.claude/agents/doer.md` (`model: claude-sonnet-5-5`, tools without Agent), `sonnet46-doer.md` deleted, CLAUDE.md Task-matching table and `DOER_BACKEND = sonnet55`. Memory `agent-model-pinning` updated. Needs a session restart to load.
2. **Rules before code (Architect, bible + register), one docs piece:**
   - E-10 R-075-02: hold-zone `required` = 10 minutes of battle (12,000 base ticks); completion = elapsed/required; the mission ends on completion (R-075-07 already says so).
   - E-10 S-080: Q-080-03 stays open; the rule text says difficulty is a no-op until it closes, and the merge gate does not require it.
   - E-04: state that the launch event library loads at world creation in play (today only tests load it). E-08: the chapter lifecycle (selector, collapse check, chapter advance) runs at the end of every jump. E-09: entry 1 of every chronicle is the player's consequence entry; chains and categories are computed at jump time. E-14: patrol and ambush issue real orders; the state machine evaluates transitions every macro interval. E-15: structures are placed at mission setup; a produced unit materialises. E-16: the briefing's "Review Chronicle" opens the chronicle scene (no placeholder modal); the tactical HUD shows the clock, the objective, and the selected group. E-10 S-078: the refuse verb exists on the briefing.
   - Each of these is a rewrite of existing rule text, not a new story; where the rule needs a value the bible lacks, a `Q-` row with candidates, and that item waits.
3. **Reach triage becomes the work list.** The Engineer re-runs `reach_lint.py` on main and diffs against the triage; every C item maps to one item below or gets a D (dead) ruling from the Architect, recorded in the triage file. The lint's baseline shrinks with every landing (regression mode already on).
4. **`pieces.toml` rows** for any file below with no owner (new client scenes for commander assignment and the refuse flow; `csrc/events.c` if unowned).

## Wave A: the game does something (sim and pipe; blockers)

A1. **Events load in play** (E-04, cluster 1). `handle_set_seed` in `csrc/pipe/om_pipe.c` calls `om_events_load_launch` and applies the launch feature set after `om_world_generate` and **before `om_campaign_start`** (the opening jump must see the templates; today it runs with none), exactly as `tests/csim/conftest.py`'s `world_factory` does (copy its order, do not invent one). Test: transport test that after `set_seed` + one `jump`, the chronicle frame carries at least one event-derived entry, and the E-04 isolation test's template count matches in play. Owner `T1-N`. Everything downstream depends on this.

A2. **Mission-selection context is real** (E-10 R-072-02, cluster 2, item 7). One `B9-N` unit adds `om_mission_refresh_context(w, region)` that computes the four setters' inputs from world state: recent attacks and attack budget from the event log (`csrc/events.c` accessors), adjacent lost regions from ownership history, revolt events, lineage context from `generational.c`, preference from the campaign settings. One `T1-N` unit calls it from `handle_mission_start` before scoring. Test: a seeded world where a telegraphed attack exists selects a Defensive Stand (the R-072 fixture), through the pipe, not the test seam. Removes the 2,000 to 5,000 unit fallback battles.

A3. **Q-072-01 fallback aligned.** Since 0682e05 `handle_mission_start` falls back through R-080-03 (a rare archetype may still be chosen) instead of a silent region-0/archetype-0 default; the answered Q-072-01 rule (retry up to 5 jumps of 20 ticks, then Defensive Stand on the weakest player region) is still unbuilt and sits in front of that fallback. `T1-N`. Test through the pipe with a world where nothing triggers.

A4. **Briefing is assembled and shipped** (E-10 S-079, item 8; gap-fix S2). `handle_mission_start` calls `om_mission_assemble_briefing`; the mission frame carries `node`, `radius`, `force[]` (HDR4 accessors exist), `position_name`, `parity`, `objective` text. Contract: the frame fields are already documented in `docs/architecture.md` (verify; if not, a docs piece first). `T1-N`, then `C6-N`: `mission_briefing.gd` renders them, the `mock_001` fallback leaves the live path, the zeros go. Test: transport worked example; a Godot test that the briefing shows a non-empty position and a roster.

A5. **Placeholder modal gone** (`C6-N`). R-079-02 says the briefing's only controls are Accept and Refuse, so the "Review Chronicle" button and its "after backend integration" modal are deleted outright (the chronicle is reached from the debrief and the galaxy). Refuse is wired in B3; until then the button is present and disabled with a tooltip, not a modal. Test: a desktop test that the briefing shows exactly Accept and Refuse and that Deploy is reachable in one click.

A6. **Tactical view, from the QA evidence** (`C5-N`, one unit each; E-16 rules from Wave 0):
   - Camera frames the player's force at mission start (today the unit sits at y=22, clipped); pan (edge and keys) and wheel zoom, the E-16 S-103 controls the rule already names.
   - HUD: mission clock (R-076 "HUD clock"), objective name and completion, selected group summary, End Mission. The debug overlay stays off (G4).
   - Attack-move key `A` and the order feedback the QA profile already assumes.
   - Enemy visible: with A2 composing real forces, confirm enemy units render; if the QA's empty field persists, that is a `qa_state`/render bug to bisect with the frozen/blank checks now in the harness.
   Tests: desktop tests with plants (`camera-unbounded` exists) and screenshot assertions (unit sprite inside the viewport, HUD labels present).

A7. **Pipe cost at 5,000 units.** Measure first (`~/Projects/om-push/logs/`): serialise time per `tactical_step` at 1,000 and 5,000 units. If serialisation dominates, a contract piece documents a delta tactical frame (`units_changed[]` plus a full frame every N steps) in `docs/architecture.md`, then `T1-N` and `C5-N` implement. If not, the fix is wherever the measurement points. Budget: one step under 50 ms at 5,000 units (Westley's number to confirm; the 20 ticks/s real-time rule needs it).

## Wave B: enemies and missions

B1. **Enemy state machine live** (E-14, cluster 6). `om_macro_tick` calls `om_macro_eval_transitions` per force each macro interval; patrol and ambush issue orders (patrol: waypoint loop around the force's anchor; ambush: hold in cover until a player group enters range, then attack-move), replacing the log-only branches. `B13-N`, two units. Tests: E-14 isolation tests for each transition already exist; add the integration test that a force enters ambush and fires on contact through `om_tactical_step`.

B2. **Hold-zone 10 minutes** (R-075-02). `om_mission_setup_hold_zone(w, 0, 12000)` instead of the time limit; test updated by the Engineer as a rule change with a ledger row. `B9-N`.

B3. **Rivals, refusal, abilities** (items 9, 14, 15). `om_mission_end` calls `om_mission_tag_rivals` (`B9-N`). Pipe verbs `mission_refuse` (R-078-05: band refusal, no deploy, tension +8% of deficit) and `activate_ability` (R-096-05) added to the command switch, documented in `docs/architecture.md` first (contract piece), then `T1-N` each; a Refuse button on the briefing (`C6-N`). Tests: transport tests per verb; Godot test for the button.

B4. **Structures exist** (E-15 R-126, items 12, 13). Mission setup places structures per archetype and calls `om_structure_assign_owners`; `om_support_tick` materialises produced units via `om_structure_pop_spawned_unit`. `B9-N` and `B14-N`. Test: integration test that a held structure produces a unit that appears in the tactical frame.

B5. **Chronicle tells stories** (E-09, cluster 4, items 10, 11). At jump end `gen_time_jump` adds the consequence entry (`om_chronicle_add_consequence_event` with the last mission's result), then runs categorisation and `om_chronicle_build_chain_clusters`; `om_chronicle_distill_candidates` (the one B→C row) feeds it. `B11-N`/`generational.c` owner. Test: after a mission and a jump, entry 1 is the consequence, and at least one chain tag exists in a seeded world. Q-068-02 (character on each entry) is a contract change to `om_chronicle_entry`: docs piece first, then the sim records it, then `chronicle_names.gd` renders it (`C3-N`).

B6. **Chapter lifecycle after a jump** (E-08, cluster 3). `handle_jump` runs, after `om_time_jump_run`: `om_player_faction_check_collapse` (chapter end reason), `om_character_selector_run` (rotation and nemesis pools), chapter advance. `T1-N` calling existing orchestrators; no new algorithm. Test: transport test that after a jump the snapshot's chapter number increments and the commander changes when the lineage has no living member (fixture from `test_E08_*`).

B7. **Commander assignment** (Q-077-02, gap-fix S1). Contract piece: pipe command `assign_commander {unit_id}` and the mission frame's `commander_unit`. Sim: `om_mission_spawn_force` keeps ids; `om_mission_end` evaluates fate from the assigned unit (`om_mission_eval_commander_fate`); reassignment allowed while the unit lives. Client: assignment on the briefing roster (default: the first unit) and a reassign action in the tactical selection panel. Debrief says "killed in action" when the unit died. `B9-N`, `T1-N`, `C6-N`, `C5-N`, `C4-N`. Test: transport test where the commander's unit dies and the debrief band carries `killed`.

## Wave C: gap-fix leftovers

C1. **Pipe chain S3 to S6.** S3 faction refs in the chronicle frame (no `[faction]` text after a jump); S4 save honesty (`format_version`, `chapter`, sorted `list_saves`); S5 stale STUB labels removed; S6 tactical `tier`/`state` filled or kept reserved. `T1-N` each, in order.

C2. **HDR5 region scale.** `OM_MAX_REGIONS` 128 to 512; `om_step_friction`'s n² edge scan becomes an adjacency walk (the measured hotspot); save version bump; E-03 tests to [250, 400] as a rule change; scale suite at 400; the Q-021-08 budget (150-tick jump under 2 s) is the acceptance test, with the loading-animation stub on the client (`C8-N`). Then G-G5 layout at scale and `DEFAULT_N_REGIONS`.

C3. **Client G2 to G6, G5b.** Error panels on pipe failure (bridge helper `C2-N`, then one unit per scene); main menu per the decision (`C1-N`); debug overlay gated off and off TacticalBridge; stored settings applied at boot; key rebinding (R-110-02); TacticalBridge autoload removed once G4 and E2 no longer read it.

C4. **E1 Era Library, E2 bug report, E3 legacy tactical deletion**, in that order, as the gap-fix plan specifies (E1 rules and register rows first; E2 rewrite off TacticalBridge, reachable from every screen; E3 deletes `scenes/tactical/` with the Engineer classifying each removed test). Then the SimBridge autoload leaves `project.godot` and the 52 files still naming SimBridge/TacticalBridge are swept (G-projectgodot-1).

C5. **Galaxy and chronicle migration.** G-G1 camera, G-G2 renderers with the new snapshot adapter, G-G3 labels and hover, G-G4 frame-time fallback (tier in `qa_state`, positive control), G-C1 composite layout, G-C2 mention click, G-C3 jump replay from the R-056-03 ownership snapshot (every 2 ticks, per the rule, not a change list; contract piece first). The hairball layout the QA shows is fixed by G-G2/G-G5, not patched before.

C6. **Reach triage sweep.** Every C item not covered above becomes a unit or a recorded D ruling until `reach_lint` reports no rule-backed behaviour tested but unwired. The 11 E questions become register rows in Wave 0 item 2.

## Critical files

- Sim: `csrc/pipe/om_pipe.c` (`handle_set_seed` ~1145, `handle_mission_start` ~1339, `handle_jump` ~1305, the command switch), `csrc/mission.c` (`om_mission_start` ~2180, `om_mission_end` ~1361, setters ~2036), `csrc/enemy_macro.c` (`om_macro_tick`, `om_macro_eval_transitions` 345), `csrc/generational.c` (`gen_time_jump`, `om_chapter_*` ~980), `csrc/events.c`, `csrc/tactical_support.c`, `csrc/chronicle.c`, `csrc/om_internal.h` (`OM_MAX_REGIONS`), `csrc/friction.c`.
- Contracts: `csrc/ouroboros_sim.h` + `signatures.toml`, `docs/architecture.md` (mission frame fields, new verbs, delta frame, chronicle entry character ref, ownership snapshot).
- Client: `scenes/mission_briefing/mission_briefing.gd`, `scenes/tactical_c/tactical_view.gd` and its HUD, `scenes/debrief/debrief.gd`, `scenes/galaxy/*`, `scenes/world/chronicle_*`, `autoload/c_bridge.gd`, `project.godot`.
- Rules: `docs/bible/epics/E-04, E-08, E-09, E-10, E-14, E-15, E-16`, `docs/northstar/ambiguity_register.md`, `docs/northstar/plans/push/pieces.toml`, `scripts/specfactory/reach_lint.py` baseline.

## Verification

- Per piece: tests red on main, green on the branch; `merge_gate.sh` clean (reach_lint regression mode, owner_lint, size_lint); determinism checksum unchanged unless the piece's ledger row says why.
- After Wave A: a fresh campaign through the pipe (transport test) yields a briefing with a named position and roster, a Defensive Stand when the fixture's attack exists, and a chronicle with event-derived entries after the first jump. A QA session's screenshots show the force inside the viewport, HUD labels, and enemy units; the blank-frame and frozen-screen detectors report nothing new on those screens.
- After Wave B: an integration test plays a seeded mission to the end through `om_tactical_step`: enemy transitions logged, a structure produces a unit, hold-zone completes at 12,000 held ticks, the commander's fate reaches the debrief, entry 1 of the next chronicle is the consequence.
- After Wave C: `reach_lint` reports zero rule-backed unwired symbols; the scale suite passes at 400 regions with the 2 s jump budget; `ps` shows no Python sim during QA; the 30B QA over a day files no new fingerprints on the fixed screens.
- End to end, Westley's eyes at the end of each wave: one full 30-minute mission from new campaign to the next chapter's briefing, with no placeholder in the way.
