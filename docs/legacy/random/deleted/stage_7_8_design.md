# Stage 7 / 7.5 / 8 — Design Questions

> **Active brainstorming document.** This is a transient working file tracking open design questions for the next three implementation stages. Answers get captured here during chat sessions, then promoted into the bible and/or stage spec before this file is deleted.
>
> **Read `design_rules.md` first** to understand how this document is used across chats.

---

## Session Handoff

**Last updated:** 2026-04-15 (Stage 8 spec write-up session in progress)

**Last session accomplished:**
- Prior session: Stage 7 + 7.5 fully resolved (S7-1 through S75-2 — see "Resolved Decisions")
- Prior session: **S8-1 save scope resolved** — sim state + tactical mid-mission state + onboarding prefs; replays excluded; sim rewind-with-re-seed is in scope
- Prior session: **S8-1a sim snapshot cadence resolved** — boundary-only (every time jump + every mission start/end); periodic snapshots flagged as "maybe later"
- Prior session: **S8-1b rewind branching model resolved** — linear default + explicit "fork from here" action; forked slots appear in Stage 9 save-slot browser as sibling slots
- Prior session: **Stage 7 spec drafted and committed** to `docs/stage_specs/stage_7_spec.md` on main
- Prior session: **Stage 7 spec audit complete** — 9 items identified (1 formatting, 6 design gaps, 2 minor).
- This session: **Audit #0 applied** — closed the unclosed code fence in the Stage 7 spec (commit `e1023ca`).
- This session: **Audit — spec markdown restored** — `##`/`###` section headers, `**file**` label bolding, and missing `python` code fences around the `config.py` and I/O-shape snippets were stripped during original authoring; all restored (commit `b129472`).
- This session: **Audit #1 applied — S7-5 ownership rule spelled out** — linear centered mapping (Option A). Military drives the player↔enemy axis, tension drives the neutral share, economy/population do not participate. Stage 7 ships with uniform `33/33/33` baseline for all archetypes; 4 prototype baselines are added in Stage 7.5 per S75-2. New config constants `OWNERSHIP_MILITARY_COEFF` and `OWNERSHIP_TENSION_COEFF` both default to `0.15` (tuning).
- This session: **Bible hub captured** (v2.07 → v2.08) — Stage 7 roadmap split into 7 / 7.5 / 8; Stage 8 roadmap expanded with rewind-with-re-seed persistence; Open Questions #12 (structure placement), #13 (economy tuning in shape), and #15 (journaling, partially) resolved; "Beyond Stage 9" deferral list updated.

**Next session should:**
- **First:** apply the Stage 7 spec audit fixes. Order:
  - (0) ~~Fix the unclosed code fence~~ — DONE (commit `e1023ca`)
  - (1) ~~Add S7-5 ownership rule~~ — DONE (linear centered mapping, Option A; commit pending this turn)
  - (2) ~~Add `STRUCTURE_COUNT_RANGES` to the config block~~ — DONE (small 1–3, medium 2–5, large 3–7)
  - (3) ~~Add production time formula~~ — DONE (embedded in the `reinforcement.py` bullet list)
  - (4) ~~Define `RegionState` dataclass shape~~ — DONE (Option B: 6 numeric driver fields + `region_id` + `tier`; debug/label fields are not read by generation logic, only by output helpers)
  - (5) ~~Clarify spawn_point node usage~~ — DONE (added "Spawn Point vs Reinforcement Structure Placement" subsection)
  - (6) ~~Archetype-aware fairness~~ — DONE (Option B: per-archetype `FairnessTargetProfile` with `(target_ratio, tolerance)` per metric; direction-preserving ratios replace 0–1 symmetry scores; 4 prototype archetypes get authored profiles, other 6 use symmetric default; obsolete `FAIRNESS_ACCEPTABLE_SCORE` removed; Checkpoint H test plan updated)
  - (7) ~~Complications-deferred note~~ — DONE (added to "Not in scope" line)
  - (8) ~~Gradient property count reconciliation~~ — DONE (gradient_placer.py entry documents the 4 continuous + 1 layer-mask-with-5-channels decomposition matching the bible's 5)
  - (9) ~~I8 measurement mechanism~~ — DONE (navmesh exposes `generation_count` counter; Checkpoint L/M assert == 1)
- Several of these have implementation shapes worth confirming with Westley as mini-questions (especially 1, 4, 6). Present per `design_rules.md` format.
- Stage-8-write-up session (2026-04-15): **Q1 onboarding scope** resolved (Option A — onboarding ships in Stage 8); **Q2 player command count** resolved (4, not 5); **Q3 save scope / rewind deferral** resolved (rewind is a post-launch feature — Stage 8 ships saves only; sim state is a single current-state file per slot; S8-1e resolved as single-slot quit-and-resume; S8-1a / S8-1b / S8-1c / S8-1d all deferred to the post-launch rewind design session with the earlier captured decisions preserved under "Deferred to post-launch rewind feature"). Bible edits landed: hub §15 rewritten, hub Stage 8 roadmap paragraph rewritten, hub "Beyond Stage 9" bullet, docs/bible_history/bible_2_00_combat.md L235 and L456.
- **Next session should:** answer S8-2 (onboarding UI interaction model) and S8-3 (mid-mission UI density). Once answered and captured, finish the Stage 8 spec's remaining sections (Checkpoints, Invariants, Done Condition) and push.
- Once all [ANSWERED], promote decisions into bible/specs and delete this file.

**Current state summary:**
- Stage 7: all design questions resolved, spec drafted and committed, audit backlog identified (9 items)
- Stage 7.5: all design questions resolved
- Stage 8: S8-1 (updated), S8-1e, Q1, Q2, Q3 resolved. S8-1a / S8-1b / S8-1c / S8-1d deferred to post-launch rewind feature. S8-2 and S8-3 still [OPEN].

---

## Context for New Chats

Upload or read these files at session start:

1. `docs/bible/game_bible.md` (hub)
2. `docs/bible_history/bible_2_00_world.md` (map generation system)
3. `docs/bible_history/bible_2_00_combat.md` (enemy macro behavior, tactical reinforcement)
4. `docs/bible_history/bible_2_00_missions.md` (mission archetypes)
5. `docs/bible_history/bible_2_00_antagonist.md` (faction archetypes — referenced by behavior scripts)
6. `docs/design_rules.md` (process rules)
7. `docs/dev_rules.md` (for reference on how specs are structured)
8. `docs/stage_specs/stage_5_5_spec.md` and `stage_6_spec.md` (recent spec examples for format reference)
9. **This file** (`docs/design_questions/stage_7_8_design.md`)

**Relevant existing code** (read if question touches implementation):
- `simulation/tactical_engine.py`, `tactical_map.py` — current tactical engine
- `simulation/mission_contracts.py` — shared data structures
- `simulation/test_maps.py` — hand-authored test maps (Stage 6 baseline)

---

## Resolved Decisions (from prior sessions)

These have already been decided. Listed here for reference — do not re-ask.

### Stage 7

- **Reinforcement structure placement** → Structures are a new spine node type placed within the authored strategic layouts (resolves hub Open Question #12). Placement is per-layout, not per-archetype; archetype compatibility filters select which layouts apply.
- **Reinforcement economy tuning** → Power-rating-scaled production time. Each structure produces one unit at a time; more powerful units take longer to produce. No resource currency. (Partially resolves hub Open Question #13; specific values are tuning decisions.)
- **Baseline trickle** → No trickle. Zero structures held = zero production. The map generator guarantees at least one production structure per map so total zero is impossible.
- **Enemy AI composition reactivity** → The enemy target ratio system adjusts in response to extreme player composition skews (~70%+ in a single category). Mild skews (e.g., 50%) do not trigger adjustment. Specific threshold and magnitude are tuning values.
- **Behavior script authoring scope** → 3–4 prototype scripts first to validate the vocabulary, then author the remaining 7. (Corresponds to Stage 7.5.)
- **Strategic Layout Library size** → 8 authored layouts in the first pass.
- **Complications** → Deferred. Not part of Stage 7. Implement in a later stage after core missions are playable.
- **Stage split** → Three stages: Stage 7 (map gen + reinforcement), Stage 7.5 (behavior scripts), Stage 8 (Godot renderer + command interface + persistence).
- **Library hints (S7-1)** → Deferred. Stage 7 ships without hints. The base pipeline (8 layouts × canvas scaling × positional jitter × simulation flavoring) already produces sufficient variety. Hints can be added later as a content addition via the library builder.
- **Layer count per map (S7-2)** → Fixed at 5 layers at the engine level for all eras. This is required by the era-agnostic architecture (revenue principle): expansion packs must be content-only, not engine changes. The bible's examples (e.g., the 1980s era with submarines at layers 4–5, surface at layer 3, aircraft at layers 1–2) assume 5. The Settled Reach space era does not restrict units to specific layers — all spacecraft can occupy any layer — but the engine still supports 5. Visual presentation per era is a renderer concern (see hub Open Design Question #16), not an engine concern. Per-map variation in how the vertical dimension plays comes from the `layer_accessibility_mask` gradient, not from varying the layer count.
- **Moving battlefields (S7-3)** → Drifting spine nodes only. Stage 7 supports objective and capture-point spine nodes drifting along authored paths, but gradient sources remain static. Navmesh is computed once at mission initialization and never regenerates. Moving gradient sources (drifting nebulae, shifting debris fields) are deferred for a later addition once the renderer exists to visualize them and the base procedural map system is proven. For archetypes whose design calls for environmental motion (Evacuation's collapsing perimeter, Interception's in-transit enemy, Containment's flowing enemy), the motion is implemented through enemy force behavior against a static map — forces advancing through spine zones, wave-style spawns, behavior-script-driven territorial pressure — not through the map literally changing.
- **Reinforcement structure ownership distribution (S7-5)** → Hybrid: archetype-authored baseline + simulation-state delta, bounded. Each archetype authors a default ownership distribution (player / neutral / enemy percentages) reflecting its tactical intent. The mission region's simulation state then applies a bounded delta on top of the baseline — **military field** drives the player/enemy axis (high military shifts toward player-owned, low military shifts toward enemy-owned), and **tension field** drives the neutral share (high tension increases the neutral/contested share). Economy and population do not drive ownership. Specific delta magnitudes are tuning values. Baselines are authored only for the 3–4 prototype archetypes selected in Stage 7.5; the remaining archetypes use a neutral-leaning fallback (~33/33/33) until their behavior scripts are authored and their baselines can be designed alongside. This pattern (authored baseline + bounded simulation delta) intentionally mirrors the existing simulation flavoring approach in the map generation pipeline.

### Stage 7.5

- **Behavior script data format (S75-1)** → JSON state machine files consumed by a shared Python runner (`behavior_runner.py`). Each script is a `.json` file specifying forces, states (behavior + modifier + position), transitions (with conditions), and reactive hooks (with when-conditions and actions). Conditions use a small restricted expression language over trigger bus flags, tactical state predicates (e.g., `force_hp_fraction < 0.5`), and timers — not arbitrary Python. The runner loads JSON, validates against a schema (catches dead states, missing transitions, stale flag references before runtime), and executes the state machine against the tactical engine's command protocol. Adding a new archetype means creating a new JSON file, no engine code changes. The expression language vocabulary is authored alongside the runner and extended when a new class of condition is genuinely needed.
- **Prototype archetype selection (S75-2)** → Four prototype behavior scripts authored in Stage 7.5: **Defensive Stand**, **Assault**, **Multi-Front Defense**, and **Counterinsurgency**. These four cover all five base behaviors (`advance`, `defend`, `patrol`, `ambush`, `retreat`) and exercise the trigger bus / multi-force coordination (Multi-Front Defense) plus the hidden-enemy-in-sensor-interference pattern (Counterinsurgency). The remaining six archetype scripts (Siege Breaking, Reconquest, Suppression, Interception, Evacuation, Containment) are authored in a follow-up pass once the prototype set validates the vocabulary. The reinforcement structure ownership baselines (S7-5) are also authored only for these four prototypes in Stage 7.5; the remaining six use the neutral fallback until their scripts land.

- **Defensive Stand prototype (Stage-7.5-write-up session, DQ-A)** → Ownership ratio `{player: 0.50, neutral: 0.20, enemy: 0.30}`. Enemy composition (attacker profile): Vanguard 0.35, Raider 0.20, Bombard 0.20, Interceptor 0.15, Line 0.10, Bastion 0.00. Behavior script: Force A (main thrust on primary chokepoint, `advance_cautious` initial → `advance_aggressive` on T+180s timer or player chokepoint HP < 30%; retreats on own HP < 40%) + Force B (flanker on secondary approach, T+45s staggered start, same shape with `force_b_broken` flag on retreat). Reactive hook: `force_b_broken` causes Force A to commit hard. Maps with one approach vector collapse to Force A only.

- **Assault prototype (Stage-7.5-write-up session, DQ-B)** → Ownership ratio `{player: 0.30, neutral: 0.20, enemy: 0.50}` (symmetric mirror of Defensive Stand). Enemy composition (defender profile): Line 0.30, Bastion 0.20, Interceptor 0.20, Bombard 0.15, Vanguard 0.10, Raider 0.05. Behavior script: Force A (garrison, primary defensive line, `defend_aggressive` initial; transitions to `defend_cautious` on HP < 35% or to `defend_aggressive` on `inner_breach` / `reserve_committed` flags) + Force B (reserve at rear staging, `defend_cautious` initial; commits to `advance_aggressive` toward player on `inner_breach` OR Force A HP < 50% OR T+240s timer). Trigger-bus vocabulary: `inner_breach`, `reserve_committed`, `force_a_broken`, `objective_secured`.

- **Multi-Front Defense prototype (Stage-7.5-write-up session, DQ-C)** → Ownership ratio `{player: 0.50, neutral: 0.20, enemy: 0.30}` (same as Defensive Stand — still a defending mission; enemy share spread across multiple sides). Enemy composition: same total as Defensive Stand attacker mix, split across 2–3 forces (largest with Vanguard bias, smaller with Raider bias). Behavior script: 2–3 independent forces with staggered timer offsets (T+0, T+60s, T+120s), each running probe → commit → retreat-or-press. Cascading-aggression trigger bus: `force_*_broken` flags cause OTHER forces to escalate (the "enemy noticed I'm distracted" beat); `any_front_broke_through` causes all forces to commit. 2-force variant on canvases with 2 approach vectors; 3-force variant on Large canvases with 3+ vectors.

- **Counterinsurgency prototype (Stage-7.5-write-up session, DQ-D)** → Ownership ratio `{player: 0.30, neutral: 0.50, enemy: 0.20}` (neutral majority — civilian infrastructure of ambiguous loyalty). Enemy composition (insurgent profile, lower total power): Raider 0.55, Interceptor 0.25, Vanguard 0.15, Line 0.05, Bombard 0.00, Bastion 0.00. Behavior script: variable cell count via per-mission **fragmentation roll** (rolled once at mission start per noise philosophy) — Concentrated bucket (~25%, 3 cells = 2 ambush + 1 patrol), Dispersed bucket (~50%, 4 cells = 2 ambush + 1 patrol + 1 sleeper, the default), Fragmented bucket (~25%, 5–6 cells = 3 ambush + 1 patrol + 1–2 sleepers). Total enemy power constant across buckets — only granularity changes. Cell roles: ambush cells start hidden (sensor-interference / cover), trigger on player proximity to `advance_aggressive`, retreat on HP < 40%. Patrol cell starts visible, `patrol_cautious` waypoint cycle, retreats when detected after ~30s to draw player into ambush territory. Sleeper cells start hidden, trigger on bus state (other cells engaged-or-destroyed) — late-mission "the insurgency wasn't done" beat. Trigger-bus vocabulary: `cell_*_engaged`, `cell_*_activated`, `patrol_engaged`, `region_swept` (mission-end gate).

### Stage 8

- **Save scope (S8-1) [updated Stage-8-write-up session Q3]** → Three classes of state persist **at launch**: (1) **simulation state** — a single current-state file per slot, written so a playthrough survives across sessions (no boundary-snapshot history in Stage 8); (2) **tactical engine state** mid-mission for **single-slot quit-and-resume** (write on quit, load on resume, consume once); (3) **onboarding preferences** (weights + rare-marks + difficulty) as "permanent for the generational arc" per the bible. **Replay files are explicitly excluded.** **Rewind is deferred to a post-launch feature** — see "Deferred to post-launch rewind feature" below. Bible edits applied (v2.11): hub §15 rewritten; hub Stage 8 roadmap paragraph rewrites persistence language to "saves, not rewind."

- **Onboarding scope (Stage-8-write-up session, Q1)** → **Option A: onboarding ships in Stage 8.** The hub's Stage 8 roadmap paragraph already specifies the onboarding screen (difficulty + archetype weights + rare marks + opening time jump + abbreviated chronicle scroll); the conflicting "Beyond Stage 9" bullet was stale text. **Bible edit applied (v2.10):** the phrase "onboarding screen" was removed from the hub's "Beyond Stage 9" list, with a parenthetical note pointing to the Stage 8 entry as authoritative. Interaction-model design (slider vs star-rating vs like+rare-checkbox vs drag-to-rank) remains S8-2 below.

- **Command vocabulary count (Stage-8-write-up session, Q2)** → **Player command set is 4, not 5.** The "5-command" / "5 commands" references in `docs/bible_history/bible_2_00_combat.md` line 235 and line 456, and the "5-command vocabulary" phrase in the hub's Stage 8 roadmap entry, were bugs created by conflating the player command vocabulary with the **enemy macro behavior modifier system** (5 base behaviors × 3 modifiers = 15 flavors — `docs/bible_history/bible_2_00_combat.md` §Enemy Macro Behavior System, lines 401–418). **Bible edits applied (v2.10):** `docs/bible_history/bible_2_00_combat.md` L235 and L456 rewritten to "4-command protocol" / "same 4 commands the player does." Hub Stage 8 entry rewritten to "4-command vocabulary (`move`, `attack_move`, `attack_target`, `activate_ability`) plus the two layer commands from `docs/bible_history/bible_2_00_combat.md` §Layer Assignment Hotkey." No change to the Command Vocabulary section itself — it already correctly listed four commands. The Stage 8 WebSocket command packet shape uses these four combat commands plus a separate layer-command channel (two kinds: hard transfer, preference assignment).

- **Tactical mid-mission state scope (S8-1e) [resolved by Q3]** → **Single-slot quit-and-resume.** Since rewind is deferred post-launch, mid-mission rewind is out of scope for launch. The tactical engine serializes once on quit, loads once on resume, and the on-disk file is consumed (deleted) on successful resume. No multiple tactical snapshots, no mid-mission rollback.

#### Deferred to post-launch rewind feature

Rewind is a distinct post-launch feature. The following captured decisions move with it out of Stage 8 scope. They are preserved here so the post-launch rewind design session has the prior work to build from:

- **Sim snapshot cadence (S8-1a, deferred post-launch):** Boundary is **one per chapter, at the post-time-jump / pre-mission-selection point** (Q3 update). This replaces the earlier S8-1a framing of three-per-chapter (time-jump + mission start + mission end). One snapshot per chapter, taken before the mission generator runs, so rewinding re-invokes the generator and may produce a different mission.
- **Rewind gating (Q3):** Minimum rewind distance is **at least 5 missions back** (exact value tuning) — the player cannot rewind the mission they just finished. Anti-gaming mechanic; prevents the rewind feature from collapsing into a "try again until I win" loop.
- **Forward-sim behavior on rewind (Q3):** On rewind, the sim is restored to the pre-mission-selection boundary and the mission generator **re-runs**. The player may get a different mission archetype, region, and character. Not "same mission, new seed" — "new path from this world-state onward."
- **Branching model (S8-1b, deferred post-launch):** Linear default + explicit "fork from here." Rewinding a slot truncates by default; fork-from-here duplicates the slot at the rewind boundary into a sibling slot, preserving the pre-rewind timeline. The Stage 9 save-slot browser becomes the timeline browser.
- **Chronicle on rewind (S8-1c, deferred post-launch):** Chronicle entries from the discarded chapter window are **erased** on linear rewind. Fork-from-here is the preservation mechanism.
- **Snapshot retention policy (S8-1d, deferred post-launch):** Open. Not a Stage 8 concern since Stage 8 writes no history. The post-launch rewind feature designs its own retention policy alongside its history format.
- **History format (new, Q3):** Stage 8 does not write a boundary-snapshot history. The post-launch rewind feature designs its own history format from scratch. Players who save a slot before the rewind update installs will only be able to rewind to boundaries captured after the update — pre-update chapters are opaque to rewind. This was Option (ii) from Q3.

---

## Open Design Questions

Questions are grouped by stage. Status markers: **[OPEN]** not yet presented, **[PRESENTED]** awaiting answer, **[ANSWERED]** answered but not yet captured, **[CAPTURED]** written into bible/spec and ready for removal.

Answered questions stay in this file (with the answer) until they are captured into the bible/spec. After capture, they move to "Resolved Decisions" above or are removed entirely.

---

### Stage 7 — Map Generation + Tactical Reinforcement

#### S7-4 — Default Structure Count Per Canvas Size [RECLASSIFIED: TUNING]

Reclassified as a tuning value. The bible establishes the derivation (region military → total capacity, clamped to archetype canvas size range). The specific range per canvas size is a number that will be adjusted through playtesting. Initial proposed defaults (small 1–3, medium 2–5, large 3–7 — floor adjusted to 1 to honor the "always ≥1 structure" decision from S7 prior session) will ship in the stage spec as config values. No design input required.

---

### Stage 7.5 — Enemy Macro Behavior Scripts

### Stage 8 — Godot Renderer, Command Interface, Game State Persistence

#### S8-1c, S8-1d, S8-1e — RESOLVED / DEFERRED by Q3

S8-1c (chronicle on rewind) and S8-1d (snapshot retention) and the history-format decision are all deferred to the post-launch rewind feature — see "Deferred to post-launch rewind feature" under Resolved Decisions → Stage 8. S8-1e (tactical mid-mission state scope) is resolved as single-slot quit-and-resume by the same Q3 resolution.

---

#### S8-2 — Onboarding Preference Weight UI [CAPTURED]

**Answer (Q4, Stage-8-write-up session):** Binary rare-mark per archetype, any subset allowed except the full set. The player sees 10 archetype rows, each a single "mark as rare" checkbox (or equivalent toggle). No sliders, no ratings, no rankings — the weight is two-valued: unmarked = default preference weight, marked = rare down-weight (0.1 per `docs/bible_history/bible_2_00_missions.md:34`). The player can mark as many as they like, with one validation: at least one archetype must remain unmarked (the onboarding screen disables the "Confirm" button if all 10 are marked, with an inline message). Difficulty is a three-button Easy / Medium / Hard selector above the archetype list.

**Bible edits applied (v2.12):** `game_bible.md:155` and `docs/bible_history/bible_2_00_missions.md:301` rewritten: the "up to two" cap removed; constraint changed to "at least one archetype must remain unmarked"; the binary-per-archetype shape stated explicitly.

---

#### S8-3 — Mid-Mission UI Information Density [CAPTURED]

**Answer (Q5, Stage-8-write-up session):** Adapt the Immortal: Gates of Pyre HUD as the layout reference. Reference screenshots saved to `docs/design_questions/igop_hud_reference_alpha.png` and `igop_hud_reference_beta.png`. Ouroboros inherits IGoP's clustered-bottom-bar layout (portraits + minimap + command-adjacent grid + control-group tabs + commander portrait) and subtracts the economy / tech / build-grid surfaces that don't map to this game. Ouroboros-specific panels fill the freed space — reinforcement-structure production list where IGoP has TRAIN/TECH/BUILD/POWER, plus a new layer-selector strip above the commander portrait. Event ticker top-left. Objectives list top-left. Banner channel top-center reserved for significance moments. No enemy composition readout at launch (fog of war is a play element, not a summary). Right sidebar reserved — no content at launch, future features (chronicle intelligence feed, event-reaction prompts) fill it without a rework. Event-ticker content is hardcoded to the beat set at launch (capture / loss / rout / objective threshold); polished authored content deferred to a Beyond-Stage-9 HUD Personality pass.

**Bible edits applied (v2.13):**
- `docs/bible_history/bible_2_00_combat.md` — new section "Mid-Mission HUD Layout" inserted after "Camera and Player View," before "Moving Battlefields." Full layout captured, IGoP citation and reference-image paths included, launch-scope caveats noted.

**Open sub-items deferred to implementation / later:**
- Per-element visual spec (exact pixel layout, Terminal-Meets-Glass typography application to combat HUD, colorblind-safe layer color palette). These are rendering-layer choices that land during Stage 8 implementation or post-launch polish. They do not gate the spec.
- Chronicle intelligence feed (the right-sidebar future feature). A post-launch design question.

---

**All Stage 8 open questions are now [CAPTURED]. This file is ready to delete once the Stage 8 spec lands on main and Westley confirms no further Stage 8 brainstorming is pending.**

---

## Engineering Defaults Awaiting Review

These are not Westley-input-required, but should be flagged for his review once the spec draft exists. Claude will propose defaults with reasoning in the stage spec.

### Stage 7

- **Layout data format** — JSON dict with named zones, edges, chokepoint specs, compatibility tags. Similar in shape to how chronicle templates are structured.
- **Compatibility filter specification language** — Boolean requirements checklist per archetype (e.g., `requires: [chokepoint >= 2, flank_route >= 1, staging_zone_has_cover: true]`). Authored as config per archetype.
- **Per-archetype compatibility filter content** — Claude will draft filters for all 10 archetypes from the bible's map character prose. Westley reviews the drafts.
- **Gradient placement algorithm** — Deterministic rules tied to spine node types: obstacle_density sources cluster around chokepoints, cover_density around staging/defensible zones, sensor_interference around ambush zones, elevation around vantage nodes. Config-tunable intensities.
- **Simulation flavoring multipliers** — Default formulas proposed in spec. Tuned during playtesting.
- **Spine edge types** — Proposed: `path` (normal), `restricted` (narrow), `flank` (alternate long route). Matches layout authoring vocabulary.
- **Reinforcement capture zone radius** — Default proposal: 300 wu. Tuning value.
- **Reinforcement capture duration** — Default proposal: 10 sec. Tuning value.
- **Structure HP** — Default proposal: 3000 (roughly 2× Bastion). Tuning value.
- **Production time formula** — Default: `production_time_sec = BASE_PRODUCTION_TIME × (unit_power_rating / POWER_NORMALIZATION)`. Config constants tuning values.
- **Composition reactivity threshold/magnitude** — Default: 70% threshold in one category, AI shifts 15% of its ratio toward the counter category. Tuning values.

### Stage 7.5

- **Reactive hook condition language** — Simple expression language over trigger bus flags + tactical state queries (e.g., `force_hp_fraction < 0.4`, `bus.force_a_routed`).
- **Trigger bus vocabulary** — Per-archetype flag names. Claude drafts from bible examples; Westley reviews.
- **Script evaluation cadence** — Already specified in bible: ~every 2 seconds. Config value.

### Stage 8

- **WebSocket protocol format** — JSON for simplicity and debuggability. MessagePack if performance requires.
- **Snapshot vs. delta wire format** — Draft in spec. Full snapshot = all unit state; delta = changes since last tick.
- **Camera angle/zoom** — Fixed angle proposal: ~60° from horizontal (standard RTS). Zoom range: 0.5×–2.0×.
- **Control groups** — Standard 0–9 RTS binding (10 groups). All-army hotkey: tilde (`~`) or similar.
- **Ability hotkeys** — Proposal: Q/W/E/R/T for the 5 commands plus context keys.
- **Layer switching** — Proposal: Tab cycles active layer. Modifier key (e.g., Shift) + 1–5 for layer assignment.
- **Minimap** — Bottom-right, standard RTS. Shows friendly units (bright), visible enemies (dim), terrain (gradient contours), objectives (icons).
- **Performance targets** — Draft in spec: <16ms renderer frame budget, <5ms WebSocket round-trip, 400 units target before degradation.

---

## Dependencies and Blockers

Notes on question ordering — which decisions must precede others.

- **S7-2 (layer count)** should resolve before compatibility filter content is drafted — filters may reference layer accessibility requirements.
- **S7-3 (moving battlefields)** gates whether navmesh regeneration is in Stage 7 scope.
- **S75-2 (prototype archetype selection)** gates which compatibility filters need to be tested in Stage 7.5 — non-prototype archetypes can be stubbed.
- **S8-1 (save scope)** gates whether Stage 8 needs a serialization contract for the simulation state, tactical state, or both.

---

## Archive / Removed Questions

(Empty for now. Captured questions either move here or are deleted once they've been promoted into the bible/spec.)
