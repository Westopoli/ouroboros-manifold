# Stage 7 / 7.5 / 8 — Design Questions

> **Active brainstorming document.** This is a transient working file tracking open design questions for the next three implementation stages. Answers get captured here during chat sessions, then promoted into the bible and/or stage spec before this file is deleted.
>
> **Read `design_rules.md` first** to understand how this document is used across chats.

---

## Session Handoff

**Last updated:** [update this each session]

**Last session accomplished:**
- Initial audit complete — identified all open questions across Stages 7, 7.5, and 8
- Stage 7 foundational decisions resolved (see "Resolved Decisions" below)
- Library hints deferred out of Stage 7 (Question L1)

**Next session should:**
- Continue with Stage 7 open questions in the order presented below (S7-2 next)
- Work through Stage 7.5 questions
- Work through Stage 8 questions
- Once all [ANSWERED], promote decisions into bible/specs and delete this file

**Current state summary:**
- Stage 7: 4 design questions remain [OPEN], numerous [ENGINEERING-DEFAULT] items flagged
- Stage 7.5: 2 design questions [OPEN]
- Stage 8: 3 design questions [OPEN]

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
- **Library hints (L1)** → Deferred. Stage 7 ships without hints. The base pipeline (8 layouts × canvas scaling × positional jitter × simulation flavoring) already produces sufficient variety. Hints can be added later as a content addition via the library builder.

---

## Open Design Questions

Questions are grouped by stage. Status markers: **[OPEN]** not yet presented, **[PRESENTED]** awaiting answer, **[ANSWERED]** answered but not yet captured, **[CAPTURED]** written into bible/spec and ready for removal.

Answered questions stay in this file (with the answer) until they are captured into the bible/spec. After capture, they move to "Resolved Decisions" above or are removed entirely.

---

### Stage 7 — Map Generation + Tactical Reinforcement

#### S7-2 — Layer Count Per Map [OPEN]

The bible specifies vertical layers (3–5 per the abstract spec, 2–3 may work best for space). Procedurally generated maps need to decide how many layers to generate per map.

Options to present: fixed per-era, variable per-archetype, variable per-canvas-size.

---

#### S7-3 — Moving Battlefields [OPEN]

The bible mentions drifting spine nodes and moving gradient sources as a design concept. Significant engineering complexity (navmesh regeneration). Several archetypes' map characters imply motion (Evacuation's collapsing perimeter, Interception's in-transit enemy, Containment's flowing enemy). Question: include in Stage 7 or defer?

---

#### S7-4 — Default Structure Count Per Canvas Size [OPEN]

The bible says structure count is derived from region military field value, clamped to the archetype's canvas size range. The Stage 5.5 spec already has placeholder values (small 2–4, medium 3–6, large 4–8). Question: are these the right ranges? Since "always ≥1 structure" was decided, the floor should be at least 1.

This might be pure tuning and not need a design decision. Flag for Westley to confirm.

---

#### S7-5 — Reinforcement Structure Ownership Distribution [OPEN]

When a map is generated, structures need initial ownership (player / enemy / neutral). Archetype-dependent? Defensive archetypes give the player more starting structures; offensive archetypes give the enemy more; contested archetypes start neutral. Question: is this rule per-archetype, or per-layout, or a general default with archetype overrides?

---

### Stage 7.5 — Enemy Macro Behavior Scripts

#### S75-1 — Behavior Script Data Format [OPEN]

The bible describes the abstract architecture (state machine with reactive hooks, 5 behaviors × 3 modifiers) but not the concrete representation. Options: JSON state machine definitions consumed by a shared Python runner, Python classes per script, hybrid. Affects how easy it is to author new scripts vs. run them efficiently.

---

#### S75-2 — Prototype Archetype Selection [OPEN]

We decided to author 3–4 prototype behavior scripts first. Which ones? Candidates: Defensive Stand (simplest single-force defense), Assault (simplest single-force offense), Multi-Front Defense (multi-force coordination / trigger bus), Counterinsurgency (ambush + scattered forces). Selection determines which behaviors and hooks get tested first.

---

### Stage 8 — Godot Renderer, Command Interface, Game State Persistence

#### S8-1 — Save Scope [OPEN]

The bible lists Stage 8 as "Game State Persistence" but doesn't specify what's persisted. Candidates: simulation state (between missions), tactical engine state (mid-mission), replay files, onboarding preferences. Question: what's in scope for Stage 8's persistence work? Note: simulation state journaling/rollback is an open bible question (#15) explicitly deferred "after Stage 8." So full snapshot-and-branch is out. Question is about minimal viable save/load.

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
