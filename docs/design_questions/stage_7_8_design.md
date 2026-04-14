# Stage 7 / 7.5 / 8 — Design Questions

> **Active brainstorming document.** This is a transient working file tracking open design questions for the next three implementation stages. Answers get captured here during chat sessions, then promoted into the bible and/or stage spec before this file is deleted.
>
> **Read `design_rules.md` first** to understand how this document is used across chats.

---

## Session Handoff

**Last updated:** 2026-04-14 (this session)

**Last session accomplished:**
- Prior session: Stage 7 + 7.5 fully resolved (S7-1 through S75-2 — see "Resolved Decisions")
- This session: **S8-1 save scope resolved** — sim state + tactical mid-mission state + onboarding prefs; replays excluded; sim rewind-with-re-seed is in scope
- This session: **S8-1a sim snapshot cadence resolved** — boundary-only (every time jump + every mission start/end); periodic snapshots flagged as "maybe later"
- **Bible override flagged:** S8-1 partially overrides hub Open Question #15 (journaling/rollback deferral). Bible hub §15 needs update at capture time — awaiting Westley approval of exact wording.
- Surfaced the sub-questions that #15 had been bundling (S8-1a through S8-1d below) plus the tactical-state scope question (S8-1e)

**Next session should:**
- Work through remaining S8-1 sub-questions (S8-1b branching model next) before moving to S8-2
- Then S8-2 (onboarding UI) and S8-3 (mid-mission UI density)
- Once all [ANSWERED], promote decisions into bible/specs and delete this file. At capture time: update bible hub §15 to reflect that rollback-with-re-seed is Stage 8 scope (leave the rest — multi-branch trees, crash recovery, cloud saves — as deferred follow-ups unless answered here).

**Current state summary:**
- Stage 7: all design questions resolved, engineering defaults flagged for spec review
- Stage 7.5: all design questions resolved
- Stage 8: S8-1 resolved (with bible flag); 5 new sub-questions opened (S8-1a–e); S8-2 and S8-3 still [OPEN]

---

## Context for New Chats

Upload or read these files at session start:

1. `docs/bible/game_bible.md` (hub)
2. `docs/bible/bible_world.md` (map generation system)
3. `docs/bible/bible_combat.md` (enemy macro behavior, tactical reinforcement)
4. `docs/bible/bible_missions.md` (mission archetypes)
5. `docs/bible/bible_antagonist.md` (faction archetypes — referenced by behavior scripts)
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

### Stage 8

- **Save scope (S8-1)** → Three classes of state persist in Stage 8: **(1) simulation state** between missions and across time jumps, **(2) tactical engine state** mid-mission for quit-and-resume, and **(3) onboarding preferences** (weights + rare-marks + difficulty) as "permanent for the generational arc" per the bible. **Replay files are explicitly excluded** — the game does not support rewatching completed missions. The simulation-state persistence is **rewind-capable**: the player can roll the simulation back to a previous snapshot and the simulation continues forward from that point with fresh stochastic outcomes. This is **re-seeded re-simulation, not deterministic replay** — because the simulation is stochastic, the "second run" diverges from the first, with divergence growing as time progresses and more random rolls accumulate. **Bible conflict flagged:** this partially overrides hub Open Question #15 ("Simulation State Journaling and Rollback — OPEN"), which had explicitly deferred rollback/branching out of Stage 8. The bible hub §15 entry must be updated at capture time to reflect that rewind-with-re-seed is Stage 8 scope; the remaining #15 pieces that are NOT committed here (crash recovery, multi-branch trees, cloud saves, etc.) stay deferred unless resolved by S8-1a–e below. Tuning and shape details (cadence, retention, branching model, chronicle handling, tactical-state scope) are surfaced as S8-1a–e.

- **Sim snapshot cadence (S8-1a)** → Event-driven boundary-only. Snapshots are written at every time jump boundary + every mission start and end. No per-tick periodic snapshots, no manual player-triggered save points. Each snapshot lands on a semantically meaningful narrative boundary the rewind UI can label (chapter name + mission). Rationale: matches the bible's generational/chapter-based structure, keeps the rewind primitive aligned with "run this chapter again, differently," bounds storage predictably. **Post-Stage-8 follow-up noted:** adding periodic intermediate snapshots during inter-mission sim (Option B from S8-1a) is a candidate future enhancement if boundary-only rewind feels too coarse once the game is playable. Recorded as a "maybe later" — do not build in Stage 8.

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

#### S8-1b — Rewind Branching Model [OPEN]

When the player rewinds to a past snapshot and simulation diverges from there, what happens to the "original" timeline? Linear model: rewinding truncates — everything after the rewind point is discarded, replaced by the new divergent run. Tree model: the game tracks both branches and lets the player switch between them. Hybrid: linear by default but a manual "fork" action that preserves the old branch.

---

#### S8-1c — Chronicle Behavior On Rewind [OPEN]

The chronicle scroll is generated from simulation events. When the player rewinds, do chronicle entries from the discarded timeline disappear, persist as a parallel/alternate history the player can read, or get flagged as "erased" but remain in a debug/lore archive? Ties to S8-1b (the answer may depend on whether branches are tracked).

---

#### S8-1d — Snapshot Retention [OPEN]

How many sim-state snapshots are retained per save slot before pruning? Options: unlimited (disk allowing), last-N ring buffer, keep-all-major-boundaries + prune-intermediate, manual prune. Pure tuning in parts, but the policy shape (what gets preserved vs. evicted) is a design decision because it determines how far back a player can meaningfully rewind.

---

#### S8-1e — Tactical Mid-Mission State Scope [OPEN]

S8-1 includes tactical engine state. Is it a simple **single-slot quit-and-resume** (write on quit, load on resume, consume once — no rewind mid-mission), or does the rewind feature extend *into* an active mission (multiple tactical snapshots, rewind to earlier point in the same mission)? Within-mission rewind is significantly more complex (many invariants: unit nav state, ability cooldowns, fog memory, ongoing effects) and may not match the "divergence grows over time" framing since missions are short (~15–30 min).

---

#### S8-2 — Onboarding Preference Weight UI [OPEN]

The bible says the onboarding screen lets the player set weights across 10 mission archetypes and mark up to 2 as "rare." The interaction model isn't specified. Options: sliders per archetype, star ratings, checkbox for "like this" + checkbox for "rare," drag-to-rank. Affects how the player perceives the weight system and how much setup time the onboarding takes.

---

#### S8-3 — Mid-Mission UI Information Density [OPEN]

The bible specifies the ability bar shows cooldown state only (no contextual prompts, no "ability ready" notifications beyond the bar itself). But the broader mid-mission UI — minimap details, selection info panel, objective tracker, reinforcement structure status, enemy composition hints — isn't specified. This is a design question because it affects the player's information access, which affects strategic play.

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
