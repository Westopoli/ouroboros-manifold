# Ouroboros Manifold — Game Bible

> **This is the single source of truth for the game's design.** This hub file contains the game's vision, principles, and short sections. Major systems are documented in spoke files (see Table of Contents). The hub + its spokes together form the complete bible. If something in any other doc conflicts with the bible (hub or spoke), the bible wins.
>
> **HUB-AND-SPOKE ARCHITECTURE:** This file is the hub. Each major system has its own spoke file in this directory. Claude Code sessions read the hub plus only the spokes relevant to their task, not the entire bible. Stage specs and task descriptions specify which spokes to read.
>
> **MODIFICATION RULE: This document and all spoke files are append-only unless Westley explicitly approves a deletion.** AI sessions may add new sections, expand existing sections, and resolve open questions by writing answers into the appropriate section. AI sessions may NOT delete, overwrite, or replace existing decided content. If new information conflicts with existing content, flag the conflict for Westley to resolve — do not silently overwrite. This rule exists because multiple AI sessions contribute to this document, and silent deletions have already caused loss of decided design work.
>
> **OPEN QUESTION GOVERNANCE:** The "Open Design Questions" section at the end of this document is a staging area, not a permanent home. When an open question is resolved through brainstorming, the answer must be written into its natural section in the relevant spoke file, and the question must be removed from the open list. If you are an AI session reading this document and you notice decided design content that still appears as an open question (or vice versa — an unresolved question living only inline with no entry in the open questions section), flag it for Westley.
>
> **Last updated:** May 9, 2026 (v2.16) — New spoke `bible_design_vision.md` added to the bible. Two-section structure: Foundational Principles (binding — skill ceiling as design target, game-theoretic depth, opt-in complexity, positional thinking over command shortcuts) and Endgame Targets (aspirational, non-binding — multi-perspective camera, intelligent opponent behavior). Hub Table of Contents and Design Experience Guide updated with spoke pointer + summary. `bible_combat.md` updated with all-army hotkey re-open flag per Foundational Principle 4 — flag does not change launch implementation; removal is deferred until a future stage explicitly addresses it. Previous: April 24, 2026 (v2.15) — World view 3D territory visualization design captured from `world_view_disclosure_design.md` (all questions Q1–Q4 resolved). `bible_world.md` "Galaxy View" section updated: supersession notes added to 2D metaball/Voronoi implementation paragraphs and snap-transition sentence; six new subsections added (Territory Visualization — Constellation and Shell Hybrid, Zoom Disclosure — Plateau-and-Edge Ladder, Player Camera Controls, Faction List and Data Panels, Hover and Focus Interactions, Time-Jump Animation Dynamics). File separation note added to Ambient Particle Field paragraph (main menu galaxy copied to frozen `main_menu_galaxy.gd/.tscn`, world view renderer modified independently). World View Major Modification roadmap entry added. See `world_view_major_modification_spec.md` for the implementation spec. Previous: (v2.14) — Four combat bible re-open flags written per v3.00 / Q-mon8.1 v2 branch system decision. (1) Tactical Reinforcement: rate, structure density, placement, cost, production time become per-era config. (2) Stat Philosophy / pacing targets: per-branch engagement duration targets (Branch 1 → 30–45s, Branch 2 → 1–2min, Branch 3 → 2min+). (3) Unit Stat Baselines: HP and damage become per-era tunable within branch signature; Settled Reach HP retcon flagged. (4) New "Information Warfare" section consolidating fog/sensor mechanics with per-branch parameterization (Branch 1 near-total awareness, Branch 2 partial asymmetry, Branch 3 heavy fog). All four flag implementation as deferred to post-Stage 13 — friends-ZIP ships single era with current values unchanged. Beyond Stage 13 updated with branch parameterization and Settled Reach retcon entries. Previous: (v2.13) — Combat visual polish session 2: ambient battle density resolved as two-layer hybrid (GPU particle haze base + battle-biased Bézier flyby ships accent), captured in `bible_combat.md` "Ambient Battle Density" subsection. Stage 12.5 scope finalized with three additional polish items: selection circle recolor (dimmer, faction-colored), HUD animation refinement (smooth transitions per Stage 9 aesthetic), player-configurable edge-scroll speed setting. Minimap polish and sound hooks deferred to post-Stage 13. All Stage 12.5 design questions now resolved — ready for spec authoring. Previous: (v2.12) — Combat visual polish design session captured seven decisions into `bible_combat.md`. Attack event protocol resolved as hybrid (renderer-inferred normal attacks, engine-emitted ability events). Unit facing resolved as target-priority rule with rotation speed cap. Four attack visual categories established (projectile, volley, beam, area pulse) with hybrid mesh-head + GPU-particle-trail projectile construction and LOD tiers. Ability visual treatment resolved as enhanced-parameter base attacks plus a shared overlay library (ring telegraph, unit glow, screen-space distortion). Impact feedback resolved as slow emission bloom + drifting impact particles in a cinematic register (Star Wars: Revenge of the Sith reference). Unit destruction resolved as bloom → damage particles → drift → darkening with wreckage LOD demotion ladder and camera-distance-based hybrid cull. All systems era-agnostic per Sacred Design Principle #3. Stage 12.5 roadmap entry added. Ambient battle density (cheap visual elements for massive-battle feel) remains open. Previous: (v2.11) — Stage 11 design brainstorming captured six decisions across `bible_chronicle.md` and `bible_world.md`. Galaxy view data flow resolved as keyframe snapshots (engineering decision, lives in stage spec). Chronicle scroll master-timeline model resolved: the galaxy animation is the master clock, entries are queued to keyframe tick ranges and carry a minimum display duration, `bible_chronicle.md` "Chronicle Scroll — Visual Presentation" expanded. Layout resolved as the expanding scroll: full-screen galaxy during pull-back and push-in, scroll panel slides in from the right during narration with galaxy resizing to ~60–65%, captured in the same section. Chronicle entry interaction resolved with three states (printing / printed / expanded) and a strict pause-everything rule on expansion, captured in the same section. `bible_world.md` "Seamless Transition" section rewritten to reflect the galaxy-as-master-clock model, the expanding scroll layout, and a new player-confirmed continuation step (the player presses Proceed when ready; no countdown) with a first-class Exit to Main Menu action at chapter boundaries. `bible_world.md` "Galaxy View — Faction territory" expanded with the influence-bubbles-plus-border-contours visualization model resolving the "colored regions with clearly defined borders" requirement. `bible_world.md` "Galaxy View — Military activity visualization" expanded to specify the event-driven flash source (attack / conquest / revolt events only) and the division of labor between sim (what happened and where) and renderer (how it looks). Follow-up captures: Stage 11 roadmap ZIP-cut sentence updated to reflect military activity flashes as required rather than optional. Word-fade-in treatment added to `bible_chronicle.md` "Chronicle Scroll — Visual Presentation" — each word fades from 0% to 100% opacity over a short tunable duration as it arrives, producing the "slowly materializing" streaming-generation feel rather than a hard character pop. Chronicle–keyframe co-occurrence guarantee captured in `bible_chronicle.md`: the distiller and keyframe selector share a single significance pipeline so every chronicle entry has a matching galaxy moment, with ownership-change keyframes added on top regardless of distiller output; preserves the dual-channel (spatial + narrative) promise. Exit transition treatment captured in `bible_world.md` "Seamless Transition": Exit fades the entire screen to black and loads the main menu with no choreography, deliberately asymmetric with Proceed's continuous motion — Proceed keeps the player inside the cycle so motion continuity is right, Exit leaves the experience so a clean cut is right. Previous: (v2.10) Sacred Design Principle #3 clarifying note added on config-driven per-era parameter variation. No principle change — explicit clarification that "minimal functional differences" permits per-era config variation (unit stats, sensor ranges, engagement targets, reinforcement rates, fog densities) consumed uniformly by a branch-blind era-blind engine. What remains forbidden is code-branched era logic. Prompted by Session 6 of visual identity design work resolving Q-mon8.1 v2 (Option E — multi-axis branch mechanical identity) and Q-mon8.2 v2 (2 launch branches + Roman standalone + Branch 3 post-launch). See `bible_monetization.md` new "Branch System" subsection and rewritten component 1 of the Progression Track Redesign. Previous: (v2.09) S8-1c (chronicle behavior on rewind) resolved: Option A, erase-on-rewind. Chronicle entries from a discarded timeline are deleted on linear rewind; the chronicle always reflects exactly the canonical timeline. S8-1b's "fork from here" is the explicit preservation mechanism for players who want to keep a pre-rewind chronicle. Open Question #15 updated accordingly — chronicle-on-rewind removed from the still-open sub-questions list. Previous: (v2.08) Stage 7 split into Stage 7 / 7.5 / 8. Stage 7 roadmap entry updated (map generation + tactical reinforcement only; behavior scripts moved to 7.5; renderer and persistence moved to 8). Stage 7.5 roadmap entry added (JSON state-machine enemy macro behavior scripts; four prototype archetypes — Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency — author first, remaining six follow; prototype reinforcement ownership baselines author here alongside the scripts). Stage 8 roadmap entry expanded to cover Game State Persistence: simulation-state rewind-with-re-seed (re-seeded re-simulation, not deterministic replay), boundary-only snapshot cadence (time jumps + mission start/end), linear-default plus explicit "fork from here" branching model, three classes of persisted state (sim, tactical mid-mission, onboarding prefs), replays excluded. Open Question #12 (Reinforcement Structure Placement Strategy) resolved — structures are a new spine node type placed within authored layouts; initial ownership = archetype baseline + bounded simulation-state delta (military drives player/enemy axis, tension drives neutral share; economy and population do not participate). Open Question #13 (Reinforcement Economy Tuning) resolved in shape — power-rating-scaled production time, no currency, no baseline trickle, single 70/15 composition-reactivity rule; specific numbers remain tuning. Open Question #15 (Simulation State Journaling and Rollback) partially resolved — Stage 8 ships rewind-with-re-seed as above; crash recovery, multi-branch tree UI, cloud saves, and sub-questions (chronicle behavior on rewind, snapshot retention policy, tactical mid-mission state scope) remain deferred. Previous: (v2.07) Tactical movement model replaced and Tier 2 stat rebalance resolved. The v2.06 ORCA/RVO local steering attempt was reverted — it did not produce stable formations at our unit counts and could not express the "immovable engaged unit" rule that the combat design requires. The new fine-layer steering is a custom directional-probe model paired with a deterministic hard-collision pass. Core behaviors now documented in the bible: units stop to fight when an `attack_move` brings an enemy into range (with an engagement leash that prevents chase drift); plain `move` is pure displacement, non-combat, suppressing auto-engage entirely; hard collision separates overlapping same-layer units each tick; stationary units (no move target, or held by engagement) absorb zero push — moving units deflect around them, which is what produces concave formations and the Strike speed advantage. Open Design Question #14 (engagement duration rebalance) resolved: HP and damage values adjusted to hit the updated pacing targets (minimum 45s brawl, ~2 min tactical, 50v50 mirror 150–200s). Rebalance is non-uniform across unit types by design; discrete stat values are implementation parameters in engine config, not in the bible. `bible_combat.md` Pathfinding section rewritten, Command Vocabulary reduced from 6 commands to 4 (`group_move` and `fast_move` removed — speed matching dropped; every movement command runs at each unit's native speed), Command Vocabulary clarified (move = non-combat, attack_move = stops-to-engage with leash), Unit Behavior AI decision loop updated to specify that `move` suppresses check 3, Stat Philosophy rebalance note marked resolved, Tier 2 numeric table removed (values live in config). Previous: (v2.06) Stage 6 Checkpoint J design revision: friendly line-of-fire blocking removed (ranged units fire through friendlies, matching SC2 model). Reactive push-apart collision system replaced with ORCA/RVO local steering (proactive velocity-based collision avoidance producing natural concave formations and speed-dependent positioning advantage). L4 behavioral claim revised from single win-rate threshold (">30% flank wins") to behavioral gradient test across four scenario tiers representing increasing defender disadvantage; pass criteria is monotonic gradient shape, not single number. `bible_combat.md` pathfinding section updated to "Hierarchical A* with RVO Local Steering." `stage_6_spec.md` movement.py description, config section, Checkpoint B/F/J descriptions, and L4 claim updated. `stage_6_checkpoint_j_continuation.md` status and resume sequence updated. Previous: (v2.05) Stage 9 (UI Shell) added to implementation roadmap: Main Menu, Era Library, Mission Briefing, New Game, Load Game, Key Redemption, Settings screens. Security architecture established: browser-redirect purchase flow, input sanitization, pre-authored error messages, IS_RELEASE_BUILD logging discipline. `animation_strategy.md` added as new spoke file defining the UI animation design language (two-layer shader+glyph hybrid, choreography principles, glyph vocabulary). "Beyond Stage 8" renamed to "Beyond Stage 9" and updated. Previous: (v2.04) Two new open design questions added: Simulation State Journaling and Rollback (crash recovery + timeline branching); Space Era Vertical Layer Visualization (three-tier system: mechanical baseline with layer indicator rings, light environmental dressing from gradient data, heavy environmental dressing for gradient-rich maps). Stage 8 design decisions recorded in brainstorming: WebSocket communication architecture, hybrid state synchronization (periodic snapshots + deltas), linear tick interpolation for 60fps rendering, fixed-angle top-down camera, Immortal-inspired selection model with all-army hotkey. Stage 8 roadmap description updated. Previous: (v2.03) Enemy Macro Behavior system added to bible_combat.md (shared behavior scripts with reactive hooks, compositional vocabulary, timer+threshold+noise transitions, independent forces with trigger bus coordination). Tactical Reinforcement system added to bible_combat.md (local reinforcement structures, in-mission production tied to region military state, enemy AI ratio-based production). Light Economy section in hub updated to reflect in-mission reinforcement design. Engagement duration targets updated (minimum 45 sec brawl, 2 min tactical). Rare authored external reinforcement events (1 in 10–20 missions) specified. Stage 7 roadmap description updated. Open design questions added for reinforcement structure placement, economy tuning, and engagement rebalance. Previous: (v2.02) Tactical simulation architecture, damage model, stat philosophy, Tier 2 baselines, command vocabulary, squad mechanics, pathfinding, power rating, canvas dimensions, cross-layer visibility, elevation, objective tracking. Previous: (v2.10) Sacred Design Principle #3 clarifying note added on config-driven per-era parameter variation. No principle change — explicit clarification that "minimal functional differences" permits per-era config variation (unit stats, sensor ranges, engagement targets, reinforcement rates, fog densities) consumed uniformly by a branch-blind era-blind engine. What remains forbidden is code-branched era logic. Prompted by Session 6 of visual identity design work resolving Q-mon8.1 v2 (Option E — multi-axis branch mechanical identity) and Q-mon8.2 v2 (2 launch branches + Roman standalone + Branch 3 post-launch). See `bible_monetization.md` new "Branch System" subsection and rewritten component 1 of the Progression Track Redesign. Previous: (v2.09) S8-1c (chronicle behavior on rewind) resolved: Option A, erase-on-rewind. Chronicle entries from a discarded timeline are deleted on linear rewind; the chronicle always reflects exactly the canonical timeline. S8-1b's "fork from here" is the explicit preservation mechanism for players who want to keep a pre-rewind chronicle. Open Question #15 updated accordingly — chronicle-on-rewind removed from the still-open sub-questions list. Previous: (v2.08) Stage 7 split into Stage 7 / 7.5 / 8. Stage 7 roadmap entry updated (map generation + tactical reinforcement only; behavior scripts moved to 7.5; renderer and persistence moved to 8). Stage 7.5 roadmap entry added (JSON state-machine enemy macro behavior scripts; four prototype archetypes — Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency — author first, remaining six follow; prototype reinforcement ownership baselines author here alongside the scripts). Stage 8 roadmap entry expanded to cover Game State Persistence: simulation-state rewind-with-re-seed (re-seeded re-simulation, not deterministic replay), boundary-only snapshot cadence (time jumps + mission start/end), linear-default plus explicit "fork from here" branching model, three classes of persisted state (sim, tactical mid-mission, onboarding prefs), replays excluded. Open Question #12 (Reinforcement Structure Placement Strategy) resolved — structures are a new spine node type placed within authored layouts; initial ownership = archetype baseline + bounded simulation-state delta (military drives player/enemy axis, tension drives neutral share; economy and population do not participate). Open Question #13 (Reinforcement Economy Tuning) resolved in shape — power-rating-scaled production time, no currency, no baseline trickle, single 70/15 composition-reactivity rule; specific numbers remain tuning. Open Question #15 (Simulation State Journaling and Rollback) partially resolved — Stage 8 ships rewind-with-re-seed as above; crash recovery, multi-branch tree UI, cloud saves, and sub-questions (chronicle behavior on rewind, snapshot retention policy, tactical mid-mission state scope) remain deferred. Previous: (v2.07) Tactical movement model replaced and Tier 2 stat rebalance resolved. The v2.06 ORCA/RVO local steering attempt was reverted — it did not produce stable formations at our unit counts and could not express the "immovable engaged unit" rule that the combat design requires. The new fine-layer steering is a custom directional-probe model paired with a deterministic hard-collision pass. Core behaviors now documented in the bible: units stop to fight when an `attack_move` brings an enemy into range (with an engagement leash that prevents chase drift); plain `move` is pure displacement, non-combat, suppressing auto-engage entirely; hard collision separates overlapping same-layer units each tick; stationary units (no move target, or held by engagement) absorb zero push — moving units deflect around them, which is what produces concave formations and the Strike speed advantage. Open Design Question #14 (engagement duration rebalance) resolved: HP and damage values adjusted to hit the updated pacing targets (minimum 45s brawl, ~2 min tactical, 50v50 mirror 150–200s). Rebalance is non-uniform across unit types by design; discrete stat values are implementation parameters in engine config, not in the bible. `bible_combat.md` Pathfinding section rewritten, Command Vocabulary reduced from 6 commands to 4 (`group_move` and `fast_move` removed — speed matching dropped; every movement command runs at each unit's native speed), Command Vocabulary clarified (move = non-combat, attack_move = stops-to-engage with leash), Unit Behavior AI decision loop updated to specify that `move` suppresses check 3, Stat Philosophy rebalance note marked resolved, Tier 2 numeric table removed (values live in config). Previous: (v2.06) Stage 6 Checkpoint J design revision: friendly line-of-fire blocking removed (ranged units fire through friendlies, matching SC2 model). Reactive push-apart collision system replaced with ORCA/RVO local steering (proactive velocity-based collision avoidance producing natural concave formations and speed-dependent positioning advantage). L4 behavioral claim revised from single win-rate threshold (">30% flank wins") to behavioral gradient test across four scenario tiers representing increasing defender disadvantage; pass criteria is monotonic gradient shape, not single number. `bible_combat.md` pathfinding section updated to "Hierarchical A* with RVO Local Steering." `stage_6_spec.md` movement.py description, config section, Checkpoint B/F/J descriptions, and L4 claim updated. `stage_6_checkpoint_j_continuation.md` status and resume sequence updated. Previous: (v2.05) Stage 9 (UI Shell) added to implementation roadmap: Main Menu, Era Library, Mission Briefing, New Game, Load Game, Key Redemption, Settings screens. Security architecture established: browser-redirect purchase flow, input sanitization, pre-authored error messages, IS_RELEASE_BUILD logging discipline. `animation_strategy.md` added as new spoke file defining the UI animation design language (two-layer shader+glyph hybrid, choreography principles, glyph vocabulary). "Beyond Stage 8" renamed to "Beyond Stage 9" and updated. Previous: (v2.04) Two new open design questions added: Simulation State Journaling and Rollback (crash recovery + timeline branching); Space Era Vertical Layer Visualization (three-tier system: mechanical baseline with layer indicator rings, light environmental dressing from gradient data, heavy environmental dressing for gradient-rich maps). Stage 8 design decisions recorded in brainstorming: WebSocket communication architecture, hybrid state synchronization (periodic snapshots + deltas), linear tick interpolation for 60fps rendering, fixed-angle top-down camera, Immortal-inspired selection model with all-army hotkey. Stage 8 roadmap description updated. Previous: (v2.03) Enemy Macro Behavior system added to bible_combat.md (shared behavior scripts with reactive hooks, compositional vocabulary, timer+threshold+noise transitions, independent forces with trigger bus coordination). Tactical Reinforcement system added to bible_combat.md (local reinforcement structures, in-mission production tied to region military state, enemy AI ratio-based production). Light Economy section in hub updated to reflect in-mission reinforcement design. Engagement duration targets updated (minimum 45 sec brawl, 2 min tactical). Rare authored external reinforcement events (1 in 10–20 missions) specified. Stage 7 roadmap description updated. Open design questions added for reinforcement structure placement, economy tuning, and engagement rebalance. Previous: (v2.02) Tactical simulation architecture, damage model, stat philosophy, Tier 2 baselines, command vocabulary, squad mechanics, pathfinding, power rating, canvas dimensions, cross-layer visibility, elevation, objective tracking.

---

## Table of Contents

### In This File (Hub)

1. [Vision and Identity](#vision-and-identity) — What the game is, what it feels like, what it's not
2. [Game Shape at a Glance](#game-shape-at-a-glance) — Two-layer structure, cycle, tempo, rewind, where to read more
3. [Sacred Design Principles](#sacred-design-principles) — Non-negotiable architectural constraints
4. [The Generational Structure](#the-generational-structure) — Chapters, cycles, character selection, what carries over
5. [The Player's Toolkit](#the-players-toolkit) — Assets, force composition, economy, commanding forces
6. [Tone and Feel](#tone-and-feel) — Elegiac, humorous, weighted by time
7. [What's Unique (Blue Ocean)](#whats-unique-blue-ocean) — The combination no other game offers
8. [Design Experience Guide](#design-experience-guide) — Quick-reference for design decisions: player identity, phase feelings, heuristics, litmus tests
9. [Transition from Previous Iteration](#transition-from-previous-iteration) — What survives, what's cut, what changes
10. [Open Design Questions](#open-design-questions) — Resolved design decisions
11. [Document Maintenance](#document-maintenance) — Rules, workflow, governance

### Spoke Files (Full References)

- [`bible_simulation.md`](bible_simulation.md) — Region state model, drift formulas, event chains, tick sequence, faction agents, diplomacy, technology, coherence ledger
- [`bible_missions.md`](bible_missions.md) — Mission generation, 10 mission archetypes, objectives, difficulty, briefings, complications, outcome band classification, outcome resolver
- [`bible_combat.md`](bible_combat.md) — Unit combat categories, 6-unit roster, abilities, unit behavior AI, force allocation, 2.5D layers, tactical variety
- [`bible_world.md`](bible_world.md) — Scale, world generation, topology, faction lifecycle, civilizational lifecycle, map generation, visual style, sci-fi era
- [`bible_chronicle.md`](bible_chronicle.md) — Chronicle scroll, distiller algorithm, template authoring framework, lineage entanglement
- [`bible_antagonist.md`](bible_antagonist.md) — External military archetypes, internal threats, spatial manifestation, threat progression
- [`bible_design_vision.md`](bible_design_vision.md) — Foundational design principles (binding) and endgame targets (aspirational, post-launch direction)
- [`bible_monetization.md`](bible_monetization.md) — Skeleton/skin model, time period expansions, distribution, pricing, multiplayer considerations
- [`bible_ai_pipeline.md`](bible_ai_pipeline.md) — Library pipeline, 3D asset pipeline, dynamic naming system
- [`animation_strategy.md`](animation_strategy.md) — UI animation design language, two-layer atmosphere+glyph architecture (shader atmospheres for celebrations, 3D particle galaxy for main menu), glyph vocabulary, animation primitives, choreography principles

---

## In Flux

This section holds emerging design that has been resolved but not yet promoted into the main spoke body. Entries here are authoritative — they supersede any conflicting content below. When an In Flux topic is fully locked and its dependent forks resolve, the entry promotes into the relevant section of the hub or a spoke.

### Tactical-layer identity — Lieutenant System + framing kill-zones (2026-05-16, committed)

**Resolved (substrate).** The tactical layer is restructured from "direct command of ~20–30 units" to **"command of 3–7 named lieutenants who each command sub-formations."** The player issues intent (objectives, priorities, timing); each lieutenant interprets that intent through their own traits, skill, and personality, then executes against the units assigned to them. The unit count per mission stays in the same range as previously planned; the *decision atom* changes from "unit/squad" to "lieutenant." Lieutenants are named, persistent, and carry traits that produce behavioral variance — not stat-stick modifiers, but actual differences in how the same order is executed (a bold lieutenant pushes when told to screen; a cautious one over-prepares; a glory-seeker breaks formation for a kill). This is the load-bearing system that the rest of the tactical and chronicle design hangs from.

**Resolved (framing).** Ouroboros is **not marketed, tagged, framed, or described as an RTS**. The Steam tag "RTS" / "Real-Time Strategy" is excluded from the storefront. The genre framing is **generational strategy simulation with operational tactical missions**. Tag direction: *Grand Strategy, Sci-fi, Simulation, Procedural Generation, Narrative, Story Rich, Generations, Strategy*. Tags actively avoided: *RTS, Real-Time, Competitive, Esports, MOBA*. Internally the missions remain real-time, but the genre-buyer signal is operational-strategy, not arcade-RTS. The Stormgate / Immortals: Gates of Pyre / ZeroSpace / Homeworld 3 graveyard is the empirical basis: every recent classic-RTS launch has collapsed, and SC2 owns the residual tribe.

**Rationale.** Market research this session converged on three findings: (1) the recent-RTS-launch market is a kill zone — every entrant (Stormgate, IGoP, ZeroSpace, Tempest Rising, Homeworld 3) has flopped commercially; (2) named-character continuity ("lieutenants who outlive your commander," dynasty-style succession) is the strongest under-served mechanic in the strategy space, with CK3, Wildermyth, and Battle Brothers as proof points; (3) the combination "operational commander with personality-driven AI subordinates inside a centuries-long generational sim" has zero direct commercial competition. The lieutenant system is the mechanic that makes all of this real at the tactical layer. The strongest commercial reference points (RimWorld $300M+, CK3 4M units, Battle Brothers ~$31M, Wildermyth, Songs of Syx, HighFleet, Sea Power) share a profile: small team, $25–35 price, 100k–500k passionate buyers, uncompromised authorial voice, no direct competitor in their exact corner.

**Niche target (primary).** The generational/legacy strategy intersection: CK3 + Wildermyth + Battle Brothers + Field of Glory: Empires audience. Reachable passionate buyers ~80k–200k. Discovery surfaces: r/CrusaderKings, r/wildermyth, r/grandstrategy, SsethTzeentach, Quill18, Many a True Nerd. Price tolerance $25–35. They buy for continuity, names that matter, world that lives, simulation depth over polish.

**Niche target (thematic differentiator).** Foundation / hard-SF literary tribe. Reachable ~20k–80k with halo from Apple TV Foundation viewership. Discovery: r/asimov, r/printSF, r/IsaacArthur. This tribe is not the conversion engine — the generational/legacy tribe is — but it is the thematic resonance that lets the project be authored rather than designed-by-committee.

**Niches actively avoided.** SC2 / classic-RTS PvP players (kill zone, every entrant flopped); Warhammer 40K space-opera audience (IP-locked); AAA 4X seats (Civ / Stellaris own them and cannot be displaced); multiplayer-ladder anything (requires CCU that this project will never reach).

**Open sub-fork — Q1: Tactical-layer redesign scope and cost.** The current implementation (Stage 6 tactical engine + Stage 7.5 behavior scripts + Stage 8 mission flow) was built assuming direct unit command. The lieutenant system is conceptually compatible — lieutenants resemble sub-factions inside the player faction, and the existing behavior-script infrastructure can plausibly back lieutenant interpretation — but the tactical UI, order-issuance surface, per-lieutenant trait model, and intent-vs-execution feedback loop are all new. Concrete cost estimate, what survives unchanged versus what gets reworked, and the path-of-least-disruption migration are downstream work and gate any tactical-layer implementation effort. Until this fork closes, no tactical-layer code work should adopt the lieutenant model — the Stage 6/7.5 work in place continues to serve the current solo loop.

**Open sub-fork — Q3: Chronicle and generational scope extension to lieutenants.** Lieutenants should plausibly outlive the player commander, retire, die, become legends, betray, found lineages, and have their grandchildren serve under future commanders. This requires extending the chronicle/naming/coherence systems (Stage 5 / Stage 11g) to track lieutenants as first-class named entities across generations, not just per-mission roster fixtures. **Feasibility under current design and cost are not yet known.** This fork is gated by Q1's cost assessment — if the tactical redesign is feasible, Q3 opens; if it is not, the lieutenant system itself reverts to consideration. Q3 resolution is deferred until Q1 returns concrete numbers.

**Resolved sub-fork — Q2: Kill RTS framing immediately.** RTS framing is killed across all current and future marketing surfaces effective immediately. Any Steam page draft, capsule copy, tag list, trailer voice-over, screenshot caption, or website copy that frames the game as "RTS" / "real-time strategy" / "real-time tactical combat as the lead identity" is non-compliant and must be reworked. This decision is independent of whether Q1 succeeds — even if the lieutenant redesign is rejected, the RTS-tag avoidance stands on the market research alone.

**Constraints this places on other forks.**
- **Multiplayer F1 (strategic-depth dilution).** Resolved. The depth-dilution fork in the multiplayer entry below has a strong candidate resolution under the lieutenant system: the decision atom is the lieutenant (not the unit), so per-player decision density stays high under co-op even when the unit pool is split — each player commands a subset of the lieutenants. Final wording in the multiplayer entry references this.
- **WS3 strategic depth.** Reshapes substantially. The lieutenant system becomes the tactical-layer substrate that WS3 designs against. The 11 WS3 forks (decision dimensions, cross-dimensional coupling, decision horizon, intelligence richness, etc.) all reinterpret around lieutenants as the agent of macro-to-tactical translation.
- **Chronicle / naming (Stage 5, Stage 11g).** Extension under Q3 — gated on Q1.
- **Game Shape at a Glance (hub).** Will retro-update to describe the lieutenant system, the operational-strategy framing, and the killed RTS framing once Q1 cost assessment lands.
- **Implementer lane.** No tactical-layer code work adopts the lieutenant model until Q1 cost assessment is delivered and approved. Existing tactical work (Stage 6, 7.5, 8) continues unchanged. Existing pre-Zip BLOCKER work (save/resume, mission objectives, tutorial, mission map speed, packaging, tactical mid-mission save, state-of-faction) is orthogonal to the lieutenant system and continues unchanged. The framing kill (Q2) applies immediately to any marketing surface, Steam-page draft, or capsule copy that lives inside BLOCKER 5 (Stage 13 packaging).

**Cross-refs.** Promotion target: a future `bible_lieutenants.md` spoke (or absorption into `bible_combat.md` + `bible_chronicle.md`, decided after Q1 closes). Multiplayer entry below now resolves its F1 depth-dilution fork via this entry. WS3 substrate work in `bible_simulation.md ## In Flux` will reference this entry as substrate.

---

### Multiplayer — session model (2026-05-16, revised after market validation)

**Resolved.** Multiplayer follows a **per-mission co-op** model. The macro simulation layer is single-player always — your campaign, your factions, your generational saga. Tactical missions can optionally become drop-in co-op for invited friends. When the mission ends, friends leave and the simulation resumes solo. Steam Datagram Relay carries the tactical session only; no shared simulation state, no lockstep, no dedicated server.

**Rationale.** Market-validation research (this session) showed the persistent-shared-world archetype sells via single-player + DLC with multiplayer as a minority feature carrying significant engineering tax (lockstep determinism constrains every simulation system added). The per-mission co-op archetype occupies the highest concurrent-player tier in the comparison matrix (Helldivers 2, Deep Rock Galactic, Vermintide) and places no constraint on the simulation layer. For Ouroboros, this preserves all single-player design freedom — including rewind, library generation, and the entire simulation layer — while still delivering the "fight alongside friends" headline. The earlier persistent-shared-world pick is superseded.

**Trade-off acknowledged.** The "two friends live the same generational saga" headline is gone. Each friend has their own campaign; co-op is a tactical visit. If the unique-experience goal later requires a shared generational saga, this pick must be revisited.

**Sub-fork F1 — Tactical co-op surface (resolved 2026-05-16).** All co-op players command units within the host's player faction (one shared army), under **strict permissions: a player can only issue orders to units assigned to them, not to other players' units**. The mechanism for partitioning the unit pool (pre-mission assignment, role-based, dynamic) is downstream detail. An alternative "temporary ally faction per player" surface was considered and rejected: it would inject a separate AI-equipped faction into the host's simulation, complicating chronicle attribution and breaking the "you and your friends are one army" framing.

**Load-bearing fork — Strategic-depth dilution under unit-splitting (resolution candidate: Lieutenant System).** Single-player tactical missions use a unit count tuned for the strategic-depth ceiling of one human. Splitting that pool across multiple humans under naive unit-allocation lowers per-player decision count below the strategic-depth threshold, reducing the skill ceiling. **Strategic depth is non-negotiable.** The Lieutenant System entry above is the candidate resolution: the decision atom is the lieutenant (not the unit), and each co-op player commands a subset of the host's lieutenant roster — so per-player decision density stays at solo levels (each player still issues intent, reads personality, adapts to interpretation outcomes) even as the unit pool is shared. This fork's full closure depends on the lieutenant tactical-layer redesign succeeding (gated on Q1 above). If Q1 returns "not feasible," this fork reopens and the multiplayer model itself may be scrapped (the candidate resolutions previously listed — scaling total unit pool, role specialization, larger co-op-only missions — are demoted to fallbacks behind the lieutenant approach).

**Constraints this places on other forks.**
- **WS3 strategic depth.** No simulation-layer multiplayer constraint. AI behavior, cross-dimensional decision coupling, and decision memory all design against a single-player sim. The "player-visible decision surface" fork is unidirectional (player sees and influences; no other humans in the simulation layer).
- **Rewind.** Survives unchanged. Rewind operates in the simulation layer, which is always single-player. Co-op missions do not rewind — they complete, and the host's solo simulation then resumes.
- **Save model.** Host owns the save file. Co-op sessions are ephemeral and leave no client-side state.
- **Monetization.** Base game + DLC model unchanged. DLC parity rules for co-op (client owns / client borrows host's content / mission disabled on mismatch) is a downstream WS4 sub-fork.
- **WS4 scope.** The multiplayer design surface contracts substantially under this pick. Open downstream sub-forks once the strategic-depth-dilution fork closes: F1 internal permission/role detail, F2 mission eligibility (which missions are co-op-able), F3 invitation model (friends / public lobby / both), F4 mid-mission join/leave, F5 DLC parity, F6 chronicle attribution of co-op participants, F7 mission outcome ownership (cross-campaign rewards), F8 rewind behavior in co-op, F9 disconnect handling.
- **`Game Shape at a Glance` scope note.** Will retro-update to describe the locked co-op shape (simulation is single-player; tactical is optional drop-in co-op) once WS4 sub-forks lock.

**Cross-refs.** Promotion target: a future `bible_multiplayer.md` spoke (created after WS4 forks lock). Related In Flux entries (when written): WS4 forks in this hub; WS3 substrate forks in `bible_simulation.md ## In Flux`. Hub section `Game Shape at a Glance` carries a forward-pointing scope note. The strategic-depth-dilution fork above gates all further multiplayer work.

---

## Vision and Identity

### What This Game Is

Ouroboros Manifold is a single-player sci-fi strategy game set in a living, stochastic world. The player is not a god, not a king, and not the leader of a civilization. The player is **a commander** — one person given an impossible task by a civilization that has its own plans, its own politics, and its own momentum. The world does not revolve around the player. It moves on its own. The player is a piece of the puzzle.

The game is structured as a **generational chain of missions**. Each mission is a chapter. Between chapters, time jumps forward — decades or centuries — and the world evolves through the simulation. The player then returns as a new character: a descendant, a successor, or someone shaped by the consequences of what came before. The player's career across generations IS the story.

### The Core Fantasy

You are a commander in a vast civilization. You are given a force, a mission, and a deadline. The mission is difficult — perhaps impossible. While you work, the world keeps turning. Factions rise and fall. Threats emerge. History happens around you, and your mission is one thread in a much larger tapestry.

When your mission ends — success, failure, or something in between — time jumps forward. The simulation runs. The world changes in ways shaped by what you did, but not controlled by it. And then you return as someone new, in a world that remembers what happened even if your new character doesn't fully understand it.

Over the course of many chapters, you experience the arc of a civilization — its rise, its crises, its potential extinction — not from above, but from inside. You are always one person with limited tools, trying to make a difference in a universe that is genuinely uncertain.

### The Feeling

The tragedy of understanding something you can't fully control. You can read the situation, make the right call, commit your forces — and it still might not be enough. Not because the game cheated, but because the world is too big and too alive for one hand to hold it all. That's the Foundation feeling. You're not Hari Seldon. You're Hober Mallow — inside the machine, reading the currents, doing what you can.

### Closest References (What It's NOT)

- **Not Stellaris** — you don't manage a whole empire's economy, diplomacy, and military. You command a task force on assignment.
- **Not Total War** — there's no separate campaign map / battle map split. It's one continuous world.
- **Not a god-game** — you don't hover above the world pressing buttons. You're in it.
- **Closest comparisons** — the strategic layer of FTL (limited resources, hard choices, things going wrong), the emergent narrative of Crusader Kings (stories that emerge from systems), the spatial command of Homeworld (forces in 3D space), the living world of Dwarf Fortress (simulation that doesn't care about you), the unit control philosophy of Halo Wars (heavy units individual, light units as squads), the combat design of Immortal: Gates of Pyre (RPS-with-exceptions, accessible depth). But none of these are quite right. The game is its own thing.

### Design Inspiration

**Isaac Asimov's Foundation series** is the primary narrative and thematic inspiration for the game. The feeling of vast civilizational arcs, the tension between individual action and historical momentum, the sense of reading currents in a world too large for any one person to control — this is the Foundation feeling translated into interactive form. The game is set thousands of years in the future, in a world of humans, and the player experiences the rise and fall of civilizations from inside, not above.

Immortal: Gates of Pyre is a key source of inspiration for the game's combat and accessibility philosophy — particularly its approach to low skill floor with high skill ceiling, and its RPS-with-exceptions unit design. See the Force and Combat sections for how these ideas are adapted.

---

## Game Shape at a Glance

This game is a real-time tactical RTS wrapped in a batch-processed generational simulation. It is not turn-based. There is no end-turn button, no 4X cadence, no waiting for the world to take its turn while the player thinks. If those phrases are forming a picture, the picture is wrong.

**Two layers.** Play alternates between two layers with distinct tempos:

- **Tactical layer — missions.** Real-time RTS. The player commands force groups on a procedurally laid-out map, fighting one engagement per mission. A mission runs 30–60 minutes of continuous gameplay. The simulation is stopped during missions — the player's attention is on the tactical problem.
- **Macro layer — the generational sim.** A batch-tick simulation of the world's factions, regions, and history. The sim does not play in real time; it runs forward in deterministic ticks between missions, producing a state snapshot and a chronicle of what happened.

**The cycle.** Each loop of play moves through:

1. **Mission** (real-time tactical, 30–60 minutes).
2. **Outcome resolver** (batch, instantaneous) — the mission's result is digested into a consequence bundle.
3. **Time jump** (batch ticks, animated as a chronicle scroll) — the sim runs forward, faction decisions resolve, events fire, the world evolves. The player watches a galaxy view animate and a 5–10 entry chronicle print itself across the scene.
4. **Character selector + mission generator** (batch) — the next chapter's protagonist and mission are selected from the new world state.
5. **Mission** (back to step 1, as a new character).

Steps 2–4 are the batch-processed window between real-time missions. Steps 1 and 5 are the player's real-time gameplay.

**Tempo controls.** Missions run in real time. The chronicle scroll between missions plays at a fixed pace; the player can click any entry to expand and read it (the world view holds its state while the player reads), and can skip to the next mission. Per-layer pause and speed behavior is part of the active multiplayer design scope and is not finalized in this summary.

**Rewind.** In single-player, the player can roll the world back to a prior mission or time-jump boundary. The simulation does not deterministically replay; it re-runs forward from the snapshot with fresh stochastic outcomes, so the post-rewind history diverges from the discarded one. Two intents are supported: a linear rewind, which truncates the discarded timeline, and a fork, which preserves the discarded timeline as a sibling save before rewinding the original. Rewind is a single-player tool. Its behavior under multiplayer is open.

**What the player is doing, by layer.**

- **In a mission:** selecting force groups, issuing move / attack-move / target / ability commands, reading the engagement, deciding when to commit or break off. The player commands forces; they do not control individual units.
- **Between missions:** watching the chronicle scroll, hovering and clicking regions in the galaxy view, reading what their last mission caused, anticipating the next.

**Where to read more.** Simulation backbone and faction decision model: `bible_simulation.md`. Mission generation, archetypes, and per-mission structure: `bible_missions.md`. Tactical engine, combat, force composition: `bible_combat.md`. Chronicle scroll, distillation, narrative entries: `bible_chronicle.md`. World view, galaxy map, between-mission visualization: `bible_world.md`.

**Scope note.** This summary describes the game as currently designed for single-player. Multiplayer is under active design; the multiplayer session model, pause-during-missions behavior, and rewind in multiplayer are open within that scope and will retro-update this section as they resolve.

---

## Sacred Design Principles

These are non-negotiable. Any feature that violates these is wrong.

1. **Genuine stochasticity.** Outcomes are truly uncertain. Multiple forces compete every tick — player effects, faction agent actions, and universe noise — and none fully controls the result. Never fake uncertainty.
2. **The simulation models civilizational state as a layered multi-dimensional space.** Granular per-region fields (military strength, economic output, factional tension, population) are the ground truth. Composite axes (stability, capacity) are derived from those fields and govern the simulation's big-picture decision-making. What is sacred is that the simulation tracks real, meaningful state at both granular and composite levels.
3. **Era-agnostic architecture — THE REVENUE PRINCIPLE.** This is not just an architectural guideline. It is the foundation of the game's entire commercial model. Every dollar the game makes after launch depends on this principle being maintained from day one. Violating it creates technical debt that blocks the expansion pack pipeline — the primary revenue engine.

   The simulation engine, mission generator, faction agents, event chains, combat system, and game loop operate on **abstract mechanical concepts only**. The sci-fi setting is a **theme pack** — a content layer that the AI library generates and the engine consumes. The engine never says "starship"; it says "heavy combat unit." The engine never says "star system"; it says "region." The engine never says "fleet"; it says "force group." The theme pack maps those abstractions to a battlecruiser in sci-fi, a trireme in a Greek theme, a Tiger tank in a WW2 theme, a dragon in a fantasy theme. The current and sole focus is the sci-fi theme — but the architecture must support any theme without engine changes.

   **What this means in practice for every AI session and every line of code:**
   - No simulation code, no event template schema, no faction agent logic, no drift formula, no config value name may reference a specific era, setting, or theme. "military_strength" is correct. "fleet_power" is wrong. "region" is correct. "star_system" is wrong. "heavy_combat_unit" is correct. "battleship" is wrong.
   - The theme pack is a separate content layer that maps abstract types to era-specific names, art, and prose. This layer does not exist yet and does not need to until visual work begins. But the simulation must never make it hard to add.
   - If you are an AI session writing code and you are tempted to use a sci-fi term because it's more readable — don't. Use the abstract term. Readability is solved with comments, not with era-specific vocabulary baked into the engine.
   - Future eras are cosmetic/superficial swaps with minimal functional differences — the same mechanics, same simulation, same event chains, different names, art, and prose.
   - **This principle applies to this document as well.** The game bible describes mechanics, not settings. Sections that describe the engine, the simulation, the combat system, the mission generator, and the game loop must use abstract vocabulary. Theme-specific terms (like "starship" or "galaxy") belong only in the Vision and Identity section (which describes the game's default sci-fi presentation to players) and in the Expansion Packs section (which discusses theme packs by name). Everywhere else, the bible speaks the engine's language.

   See "Expansion Packs and Monetization" for how this architecture becomes the revenue engine. The skeleton (engine) ships once. The skins (theme packs) ship forever. Every expansion pack is pure content — no engine changes required. That is only true if this principle is never violated.

   **Clarifying note on "minimal functional differences" (added April 15, 2026, Session 6 of visual identity design work).** The phrase "minimal functional differences" in this principle explicitly permits **config-driven per-era parameter variation**. It does not require every era to play mechanically identically. Different eras may have different unit stat values, different sensor ranges, different engagement duration targets, different reinforcement rates, different fog densities — as long as every such variation lives in per-era config files that the engine consumes uniformly.

   What remains forbidden is **code-branched era logic**: no `if branch == "scifi"`, no `if era == "settled_reach"`, no special-case engine paths keyed on era identity. The engine stays branch-blind and era-blind. It reads config and acts on config. Eras differ because their config differs, not because the engine contains era-aware logic.

   This clarification was prompted by the Session 6 decision to implement mechanically distinct branches in the era catalog — each branch expresses a signature stance across tempo, information warfare, and attrition axes. Implementing those branches without violating this principle requires the config-driven architecture described above. Branches themselves are a monetization and progression catalog concept, not an engine concept; see `bible_monetization.md` "Branch System" subsection.

   This is not a softening of Sacred Principle #3. It is the correct reading of "minimal functional differences" — the principle was always about engine architecture, not about forcing mechanical uniformity across eras. Config-level variation is how the engine *supports* diverse content without engine changes, which is the principle's actual goal.

---

## The Simulation Backbone

> **Full reference: [`bible_simulation.md`](bible_simulation.md)**

The simulation runs a system-dynamics model with stochastic event chains across a world of connected regions. Each region tracks four granular fields (military, economy, tension, population) and two composite axes (stability, capacity). Faction agents accumulate budget, evaluate targets, and take actions (attack, colonize, reinforce, accumulate) through a scored decision model with per-archetype weights. Events fire stochastically through threshold triggers with noise, and can spawn follow-up events with delays and conditions. The tick resolution sequence runs 7 steps per tick: natural drift, event processing, faction agent decisions with intent resolution, border friction, composite recalculation. See `bible_simulation.md` for all formulas, tick sequence, event architecture, agent model, diplomacy, technology, coherence ledger, and tuning observations.

---

## The Generational Structure

### Chapters

A single playthrough consists of multiple **chapters**. Each chapter is one mission played by one commander. Chapters last approximately 30–60 minutes of real play time.

### The Cycle

1. **Mission briefing** — the civilization presents the player with a mission: objectives, forces assigned, context about what's happening in the world.
2. **Recon phase** — free camera over the mission area with no time pressure. The player observes terrain, enemy positions hidden by fog of war, points of interest, and their own starting deployment. The commander studies the map before giving the order. The mission clock does not start until the player hits "Begin Mission."
3. **The mission** — the player commands their forces to accomplish the objective. The simulation is stopped during missions — the player is focused on their tactical problem, not monitoring a live world. Rare pre-computed complications may fire (roughly every third mission) based on the archetype's complication table, but these are determined at mission generation, not driven by live simulation ticks.
4. **Mission resolution** — success exists on a spectrum, not a binary. The tactical layer classifies the outcome into one of the archetype's outcome bands, and the mission outcome resolver translates that into region stat changes applied to the mission region, scaled proportionally to the region's current state. There is no separate world-wide momentum or vector nudge — the simulation propagates local consequences naturally through inter-region dependencies during the subsequent time jump. The resolution also determines the **commander's fate**: survived, wounded, or killed. Commander death can result from catastrophic mission failure or specific tactical outcomes (e.g., the command unit is destroyed). A killed commander is logged in the coherence ledger and becomes part of the lineage's narrative — "Commander Tanaka went down with the ISV Resolute during the defense of Terminus." Death forces an early lineage decision: the character selector either continues through another family member or rotates to a new lineage. Commander death is not a fail state for the player — it's a narrative event that the generational structure absorbs naturally.
5. **Time jump** — the simulation fast-forwards through a random duration between a configurable min and max (targeting 20–100 years). The duration is a simple random roll, decoupled from mission urgency or world state — the simulation's existing drama-generation systems (passive drift, event chains, faction agent actions) produce interesting events over any duration naturally. The player has no agency over the gap length. The player experiences the jump as a **chronicle scroll** — a text-based vertical timeline of 5–10 entries summarizing what happened between chapters, presented alongside an **animated map view** where the player watches faction territories shift, borders redraw, and new factions emerge in real time as the scroll advances. Three kinds of entries, presented in order: **consequence entries** (direct results of the player's last mission, shown first so the player sees their impact), **world entries** (things that happened on their own — faction shifts, tech changes, inter-faction conflicts), and **setup entries** (the last one or two entries teeing up the new chapter). The player can click any entry to expand it slightly for extra detail. No voice acting, no cutscenes — just good prose, clean typography, the weight of time, and a map that moves.
6. **New chapter** — the player returns as a character selected by the simulation. **Lineage persistence:** the simulation keeps the player within the same bloodline for 2–4 chapters before rotating to a different family. Within a lineage run, each chapter is a descendant — the player sees the family name return and watches consequences compound across a career arc. The simulation rotates to a new lineage when: the character selector's rotation logic triggers (regional delta scoring, crisis veto, hard cap — see Character Selector Algorithm), the bloodline has died out, or the world's pressure points have shifted to a region where a different lineage is more narratively charged. When the lineage rotates, the new character is selected from the weighted pool: most commonly a **descendant of a previous commander from a different lineage** the player has already played. Less commonly a **descendant of a previous commander's rival or nemesis** (instant dramatic tension). Rarely, an **unrelated person elevated by circumstance** (signals the world has changed dramatically). The 2–4 chapter range is a soft target — the simulation aims for it, not enforces it rigidly. If a bloodline dies out after one mission, that is a meaningful moment, not a bug. The civilization assigns a new mission based on the current state of the world.

### Character Selector Algorithm

The character selector runs after the time jump completes and the mission generator has already selected the next mission's region and archetype. It determines whether to continue the current lineage or rotate, and if rotating, picks the new lineage. The selector is coupled to the mission generator — the mission region is already decided, and the selector finds the best commander for that mission.

**Step 1: Rotation decision.** The ledger tracks a chapter counter for the current lineage. The rotation decision uses three mechanisms:

**Regional delta scoring** — after the time jump, the selector computes how much the lineage's home region (and adjacent regions) changed in field values during the jump. High total delta means the region is active and the family's story is in motion — stay with this lineage. Low total delta means things are quiet — natural exit point. The delta score maps to a rotation probability: low delta = high rotation chance, high delta = low rotation chance. The mapping curve and thresholds are config values.

**Crisis veto** — if the lineage's home region is in an active crisis (stability below a config threshold, or an active event chain in a critical stage), rotation is vetoed regardless of what the delta score or chapter counter say. The family stays because their story isn't done.

**Hard cap** — a maximum chapter count (config value, ~6) forces rotation regardless of delta score or crisis state. Even if the family is mid-crisis at the cap, the game cuts away. The chronicle frames this naturally — the family's story continues in the background, but the world's attention shifts. This prevents a single crisis-locked lineage from dominating the playthrough.

**Forced rotation** — if the bloodline has no living members, or the commander died and no immediate family successor exists, rotation is forced immediately regardless of counter, delta, or crisis.

The flow: check forced rotation conditions → if chapter counter is below the eligible range (2), stay → if at or above the hard cap, rotate → compute regional delta score → map to rotation probability → roll → if rotation triggers, check crisis veto → if vetoed, stay another chapter → otherwise, rotate.

**Step 2: Lineage selection (on rotation).** The selector runs after the mission generator has already chosen the mission region. It finds the best lineage for that region:

**Priority 1 — Previous lineage descendant (most common, ~70%).** Check all previous lineages the player has played. Does any have living descendants in or near the mission region? If multiple qualify, score by: recency penalty (don't immediately return to a lineage you just left), number of living descendants in the region, and how many chapters ago the player last played them (moderate gap preferred over very recent or very distant). Weighted random draw from scored candidates.

**Priority 2 — Nemesis/rival descendant (rarer, ~20%).** Check the coherence ledger for named characters who were rivals or antagonists to any previous commander. Do any have descendants in or near the mission region? If yes, select from this pool. Instant dramatic tension — the player commands the descendant of someone who opposed them.

**Priority 3 — Unrelated person (rarest, ~10%).** No previous lineage or nemesis connection to the mission region. Generate a new character from that region. This signals the world has changed dramatically — the old families aren't relevant here.

The pool weights (~70/20/10) are config values. The selector rolls against the weights to pick a pool, then selects within that pool. If the selected pool has no valid candidates (e.g., no nemesis descendants exist near the mission region), it falls through to the next pool.

**Step 3: Commander assignment.** The selected lineage member (or newly generated character) is registered in the coherence ledger as the new commander. Their rank is set to the appropriate military rank. The chapter counter for the new lineage (or continued lineage) is incremented. The selector returns a structured record tracking the selected character, lineage, faction, whether rotation occurred (and why), and which pool was used. See `bible_simulation.md` "Character Selector Data Contract" for the implementation-level data structure and nemesis tagging mechanism.

**Step 4: Lineage member generation during time jumps.** During each time jump, a **lineage generator module** (separate from the coherence ledger) runs a simple family tree update for the current lineage (and all tracked previous lineages). The update is minimal: N descendants produced (based on time jump length and a fertility config value), distributed across regions based on where the family currently lives. Each descendant gets a name (from the naming system), a region, and an age. No personality traits, no career simulation, no detailed life events. The generator hands the new character records to the coherence ledger for registration. The chronicle distiller and template system add narrative richness in prose — the ledger just tracks who exists and where. This keeps both systems lean while giving the character selector and distiller enough data to work with.

### Onboarding and First Chapter

**Single onboarding screen.** Before chapter 1, the player makes two permanent choices on one screen: **difficulty setting** (Easy/Medium/Hard) and **mission preference weights** (across the 10 mission archetypes, with up to two markable as "rare"). Both are permanent for the entire generational arc. The same onboarding screen fires at the start of each new cycle after Exodus or Extinction — the player can make different choices for the new civilization.

**Future difficulty option — Hard Mode.** A fourth difficulty tier beyond Easy/Medium/Hard, selected at the same onboarding screen. Hard Mode applies two changes on top of the existing constraint compression system: (1) mission objectives are tuned to be deliberately punishing — tighter time limits, more aggressive enemy compositions, higher outcome-band thresholds for success; (2) the all-army hotkey is disabled, requiring the player to manage multiple independent control groups with no single-button fallback. The combination demands genuine multi-front tactical skill — the player must split attention, prioritize engagements, and coordinate forces manually. This is a post-launch addition; the Easy/Medium/Hard system ships first and must be balanced before a fourth tier is layered on top.

**Opening time jump.** After the player confirms their choices, the game generates the starting world and immediately runs a time jump (configurable, targeting 20–50 years — same minimum as standard time jumps). The simulation's fast pacing means even this initial jump produces meaningful history: factions expand, borders form, and first military contacts may occur. The player sees an abbreviated opening chronicle scroll — 3–5 entries, all world entries (no consequence entries since there's no previous mission). This serves as the player's introduction to both the world and the chronicle scroll format — and immediately establishes that the world is dangerous and in motion. The mission generator then runs normally against the post-jump state, and the character selector draws from the "unrelated person" pool since no previous lineages exist. Subsequent cycles after Exodus or Extinction use the same opening time jump — in post-Extinction cycles, the chronicle scroll includes ruin references and the world contains remnants of the previous civilization.

### What Carries Over

- **The world remembers everything.** The simulation state carries forward completely. Every mission outcome, every faction shift, every tech advance or cultural collapse persists.
- **The player starts mechanically fresh each chapter.** New character, new forces, new mission. No persistent "player level" or unlocks.
- **But the civilization evolves.** As the simulation progresses, technology advances (or regresses). The tools available to the player in later chapters may be significantly different from early chapters — better units, new asset types, or conversely, degraded capabilities if the civilization is declining.
- **The Ouroboros.** The game can cycle. If the civilization reaches Extinction with Amnesia, it restarts — and the player's next character exists in a world that contains the ruins of everything that came before. The Memory Burden mechanic: the player remembers what their new character does not.

### Player Civilization Mortality

The player's civilization has no plot armor. It can be conquered, fragmented, or ground into extinction by the same simulation forces that affect every other faction. This is a core design commitment, not an edge case.

**When the player's faction collapses** (loses all regions, or is reduced below a viability threshold), the generational structure absorbs it:

1. **The chronicle frames the fall.** The collapse becomes a major chronicle scroll entry — potentially the most dramatic moment in the playthrough. The prose treats it with weight: "The last garrison of [faction name] surrendered at [region]. Seven hundred years of history ended not with a battle, but with a signature."

2. **The character selector reassigns the player to a surviving faction.** The selector evaluates all surviving factions and picks one using modified lineage selection logic: prefer factions that the player has narrative connections to (previous lineages with descendants in that faction's territory, nemesis connections, geographic proximity to the fallen civilization's former territory). If no narrative connection exists, select the faction whose territory overlaps most with the player's former civilization — the player experiences the world their people built, now under new management.

3. **The player continues as a commander in the new faction.** New mission, new forces, new political context. The player's institutional knowledge of the world carries forward even though their character is new. The chronicle connects the threads — "Three decades after the fall of [old faction], a young officer in [new faction] was given command of a force..."

**Cross-faction lineage rotation.** Even when the player's civilization survives, the lineage rotation system can move the player to a different faction for variety. After the hard cap on lineage chapters (config value, ~6), the character selector considers candidates across all factions, not just the player's current one. A player who has spent four chapters commanding forces for one faction might rotate to a breakaway faction born from a revolt in their former territory, or to a rival faction where a nemesis descendant now serves. This prevents the player from being locked into a single faction's perspective and creates dramatic moments of seeing the world from the other side.

### Terminal Conditions and the Cycle

The game is designed to run indefinitely. Terminal conditions are not endpoints — they are **transitions** that the generational structure absorbs naturally. With player civilization mortality, even the "death" of the player's faction is a transition, not a game over.

- **Exodus** — the civilization escapes to a new region of the world (or a new world entirely). The simulation resets to an early-era state: small foothold, limited technology, dark unexplored space. But the chronicle carries forward, the coherence ledger remembers, and the player's new commander may inherit fragments of the old civilization's knowledge. A new early era begins.
- **Extinction with Amnesia** — the civilization dies. Cold restart with relics. A new civilization emerges in the same world, surrounded by the ruins of everything that came before. The simulation resets to early-era state. The Memory Burden mechanic: the player remembers what their new character does not. The relics of the old civilization are physically present but unlabeled — waypoints exist, but inspect panels read "Unknown."
- **The Unbroken Line** — the civilization endures through the late era without collapsing. Eventually the simulation's internal pressures (external faction escalation, internal fractures, resource exhaustion, technological complexity) force a transition — either an Exodus, a collapse into Extinction, or a **civilizational contraction** where the civilization voluntarily or involuntarily retreats to a smaller footprint, effectively resetting to a mid or early era state with the scars of what came before.

The game loops through expansion → conflict → fragmentation → renewal, but this cycle operates at the faction level, not the global level. Multiple factions cycle independently. The player threads through these cycles via lineage rotation, experiencing the world from different vantage points. Each cycle feels different because the world remembers: ruins from collapsed factions, chronicle entries spanning centuries, lineages that connect across faction boundaries. The player experiences the Ouroboros — civilizations rising, falling, and rising again, with the player as the thread of continuity across the cycles.

---

## Missions

> **Full reference: [`bible_missions.md`](bible_missions.md)**

Missions are generated from simulation state using a curated library of 10 mission archetypes with variables filled by the current world context. Each archetype defines its own simulation trigger conditions, objective shape, asset profile, map character, success spectrum with consequence tables, and complication templates. The mission generator reads simulation state, identifies pressure points, and matches them to eligible archetypes. The mission outcome resolver translates tactical results into region stat changes proportional to current state. See `bible_missions.md` for the full generator algorithm, all 10 archetypes, objectives, difficulty/era scaling, briefings, complications, and outcome resolution.

---

## The Player's Toolkit

### What You Command

The player receives a **variable set of assets** for each mission. What you get depends on what the civilization can provide (shaped by simulation state, tech level, and mission type). Forces scale with the era — early chapters might feature basic units, late chapters might have advanced technology or, if the civilization is declining, desperate scraps.

Asset categories:

- **Forces** — combat units. Your hard power. Defend, attack, project force. The most expensive assets and the most painful to lose.
- **Science units** — extend knowledge. Explore, investigate anomalies, boost tech. Fragile but valuable for information advantage.
- **Trade/supply convoys** — economic backbone. Run supply to your forces and between regions. Disrupting enemy supply (or protecting yours) is a strategic lever.
- **Intelligence operatives** — eyes and saboteurs. Place them for better visibility or to disrupt enemy operations. Limited number, high value.
- **Cultural missions** — the long game. Slow, but they stabilize cultural memory in a region. The civilizational equivalent of planting a tree.

Not every mission includes every asset type. A defensive stand is mostly combat forces with some supply units. A counterinsurgency mission is a light mobile force. An evacuation includes non-combat supply convoys representing evacuation targets that must be protected.

Non-military assets sit **outside the combat RPS entirely**. They're not combat units — they're strategic tools. They have **no combat capability** and must be protected or evacuated when fighting starts.

### Commanding Forces

- **Top-down tactical view** — the player sees their forces from above and gives orders
- **Direct control** — click/select units, tell them where to go and what to do
- **Always real-time, no pause** — pacing is slow enough to think. Deliberate, not frantic. The skill is in reading the situation and making committed positioning decisions.

### Individual Units

Units feel real but are not deep characters. They have names. Losing one should sting — especially heavy Siege units — but the attachment is to the mission and the civilization, not to individual units. Think named tools you care about (like a favorite ship in FTL), not party members in an RPG.

### Light Economy

The player does not manage a civilization-level economy, set resource priorities, or build a base. The civilization allocates a **starting force** for each mission based on the mission type and its own state. The player's influence over force composition is **front-loaded into the mission preference weights** set at game start — by telling the civilization what kind of commander they are (military-focused, exploration-focused, etc.), the player shapes which mission types they receive, and the mission type determines the asset profile. See "Force Allocation Algorithm" in the Force and Combat Design section for how this translates into concrete forces.

This is the "commander, not king" principle applied to logistics. You don't choose your loadout — you're handed orders and equipment. The civilization tries to give you what the mission calls for, constrained by what it can actually produce. A thriving civilization gives you a well-equipped force. A declining civilization gives you scraps and a note about what they couldn't spare. The gap between what you need and what you get is where the drama lives.

**Local reinforcements during missions.** The starting force is roughly half of what the player will field over the course of a full mission. The other half comes from **local reinforcement structures** — military infrastructure already present in the mission region (garrison posts, militia stations, forward operating bases) that produce replacement units at a slow, steady rate. The player captures or holds these structures to receive reinforcements and chooses which unit type to produce. The enemy has access to the same system. The total reinforcement capacity of all structures on the map is derived from the mission region's military field value in the simulation — a high-military region has more productive infrastructure, a depleted region has less. This creates a direct, player-visible link between the simulation's strategic state and the tactical experience: commanding forces in a thriving region feels fundamentally different from scraping together militia in a dying one. The chronicle briefing communicates the expected reinforcement level to the player as part of the mission context — though in rare situations, intelligence may be incomplete. See `bible_combat.md` "Tactical Reinforcement System" for the full design.

---

## Force and Combat Design

> **Full reference: [`bible_combat.md`](bible_combat.md)**

Three combat categories (Strike / Line / Siege) on a soft RPS spectrum, with 6 base unit types (2 per category). Each unit has one ability. Force allocation is algorithmic — the mission type determines the asset profile, the civilization's state determines what it can produce, and the gap between need and availability creates tactical drama. Combat plays out on 2.5D vertical layers with moving battlefields and environmental hazards. The tactical engine uses a SC2-style sim/renderer split: a deterministic Python tick engine (20 ticks/sec) owns all gameplay state, Godot renders it. Damage uses multiplicative RPS multipliers (1.5×/0.75×/1.0×) with flat HP and cover density reduction. Engagement pacing is deliberate: minimum 45 seconds for a straight brawl, ~2 minutes with tactical play. Local reinforcement structures provide in-mission unit production tied to the region's military state. Enemy macro behavior uses a shared behavior script system with reactive hooks — 5 base behaviors with 3 modifiers, timer+threshold+noise transitions, and independent forces coordinated through a shared trigger bus. Combat visuals use four era-agnostic attack rendering categories (projectile, volley, beam, area pulse), hybrid mesh+particle projectile construction with LOD tiers, a shared ability overlay library, cinematic impact feedback, and drifting wreckage with LOD demotion. See `bible_combat.md` for the full unit roster, abilities, roles, damage model, stat baselines, command vocabulary, pathfinding, power rating, AI-generated variety, force allocation algorithm, map layers, tactical variety, enemy macro behavior, tactical reinforcement system, and combat visuals.

---

## The Antagonist System

> **Full reference: [`bible_antagonist.md`](bible_antagonist.md)**

All external antagonists are territorial military factions running the same agent framework as every other faction — same engine, different config weights. Five base archetypes, with more generated by the library builder post-launch. Internal antagonists (breakaway factions, coups, extremist movements) emerge from simulation mechanics and can be resolved, absorbed, or turned into allies. See `bible_antagonist.md` for archetype definitions, internal threat mechanics, spatial manifestation, and threat progression.

---

## The Chronicle

> **Full reference: [`bible_chronicle.md`](bible_chronicle.md)**

The chronicle is the player's window into the civilization's history — both as the narrative montage during time jumps and as the long memory across generations. The chronicle scroll distiller compresses hundreds of ticks into 5–10 entries using a three-pass algorithm (significance scoring, lineage-first clustering, keyed composable template selection). The template authoring framework provides AI-generated prose fragments assembled at runtime. See `bible_chronicle.md` for scroll presentation, distiller algorithm, template framework, and lineage entanglement.

---

## The World

> **Full reference: [`bible_world.md`](bible_world.md)**

The world is a variable-size network of regions connected by a typed adjacency graph. World generation uses tiered templates (from isolated single-faction to contested multi-faction). The map generation system uses a Spine + Gradient hybrid approach with a Strategic Layout Authoring Framework — hand-authored spatial blueprints filtered by archetype topology templates. Per-faction lifecycle stages (Growth → Peak → Decline → Collapse/Rebirth) and civilizational lifecycle mechanics drive macro arcs. See `bible_world.md` for scale, generation templates, topology, lifecycle mechanics, spatial navigation, map generation pipeline, visual style, and the sci-fi era ("The Settled Reach").

---

## Tone and Feel

### Elegiac, Not Grim

The game is about civilizations rising and falling over vast timescales. The tone is that of a real history being recorded. There is tragedy — the threat cannot be stopped, only delayed. But there is also humor, beauty, and unexpected moments of hope.

### The Humor

The game has a sense of humor. Easter eggs, dry observations, and unexpected moments of levity are intentional. The humor is in the writing, not in the events. Dry, earned, and occasionally absurd.

### The Weight of Time

The generational structure gives the game something almost no other game has: **the passage of centuries felt through play**. The player doesn't just read about time passing — they played the chapter that caused this. They remember the commander who failed, and now they're living with the consequences as someone new.

---

## What's Unique (Blue Ocean)

The combination that doesn't exist in any current game:

1. **Genuinely stochastic simulation** underneath a strategy game — you're not playing against scripted AI or deterministic systems. The world has its own probability space.
2. **Generational chapter structure** — you're not one persistent character or one persistent empire. You're a series of people inside a civilization that changes around you.
3. **Commander, not king** — you don't control everything. You control a task force on a mission, and the civilization has its own plans.
4. **AI-generated mission and narrative content** — every playthrough is contextually unique through library-built templates with simulation-driven variables.
5. **The tragedy of understanding** — you can read the system, master the patterns, and still face outcomes you can't prevent. Mastery means you understand WHY you lost, not that you always win.
6. **Cyclic civilizational arcs** — the game loops through early/mid/late eras, with each cycle carrying the scars and ruins of the last. The Ouroboros isn't a name — it's the structure.

---

## Design Experience Guide

> **This section is a quick-reference for design decisions.** When you're choosing between two approaches and the code doesn't make the answer obvious, check here first. These are the player experience commitments that every mechanical decision should serve.

### Core Player Identity

The player is **a commander** — one person with limited tools, given an impossible task by a civilization that has its own plans. The player influences the world but never dictates to it. They receive orders and equipment, not a kingdom and a treasury. The gap between what they need and what they get is where the drama lives. Every design decision should reinforce this: the player is *inside* the world, not *above* it.

### The Five Feelings

The game should produce these distinct player experiences depending on the faction's lifecycle state. These are the emotional targets — if a mechanic doesn't serve at least one of them, question whether it belongs.

1. **Pioneer survival** (young faction) — scrappy, resource-scarce, every mission matters because the faction can't absorb a loss. The feeling of building something fragile in a dangerous world.
2. **Strategic depth** (established faction) — real military, real logistics, real enemies. The player is a commander with actual resources making actual strategic choices about which fronts to prioritize.
3. **Imperial weight** (overextended faction) — too much territory, not enough resources. Every solution creates a new problem. The feeling of managing decline before it becomes collapse.
4. **Elegiac decline** (declining faction) — watching an institution die from the inside while trying to save what you can. Last stands, fighting former allies, protecting the last intact core regions.
5. **Survival and identity** (faction born from collapse) — a new faction finding its footing in a dangerous world, surrounded by the wreckage of what came before. The feeling of starting over with scars.

The player may experience all five across a single playthrough through lineage rotation — including experiencing the consequences of their own failures from the other side.

### Design Decision Heuristics

When facing a design fork, these resolve the ambiguity:

- **Uncertainty** — genuine, never faked. If the player can guarantee an outcome, the design is wrong. Multiple forces compete and none fully controls the result.
- **Control** — the player influences, never dictates. The civilization has its own plans. If a feature gives the player too much control over the world, pull it back.
- **Loss** — dramatic, never punishing. Losing a region is a chronicle moment, not a game over. The generational structure absorbs every loss. If the player can lose and the game becomes *more* interesting, the design is right.
- **Humor** — dry, earned, never forced. The game winks, it doesn't mug. Easter eggs and absurdity are welcome. Cringe is not.
- **Complexity** — accessible floor, deep ceiling. A new player can play without understanding every system. A skilled player plays differently because they read the situation better, not because they memorized more rules.
- **Pacing** — the world is always in motion. If the map is static for 100 ticks, the core fantasy fails. Static = broken.
- **Mastery** — mastery means understanding *why* you lost, not that you always win. The tragedy of understanding is the core emotional loop.

### The Litmus Tests

Quick yes/no checks for any feature or design decision:

1. **Commander or god?** Does this make the player feel like a commander inside a living world, or a god hovering above it? If god — redesign.
2. **Chronicle material?** Would this produce interesting chronicle entries? If a feature can't generate narrative material, it's mechanical overhead without payoff.
3. **Era-agnostic?** Does this work identically with a different theme pack? If it depends on sci-fi specifics, it violates the revenue principle.
4. **Loss is interesting?** Can the player lose and still want to keep playing? If failure makes the game less interesting instead of more, the stakes are wrong.
5. **The world doesn't care?** Does the world continue operating regardless of the player's actions? If a system pauses, waits, or adjusts itself for the player, it breaks the living-world contract.

### Long-Term Design Vision

> **Full reference: [`bible_design_vision.md`](bible_design_vision.md)**

A separate spoke documents the game's foundational design principles (binding on all current and future work — skill ceiling as design target, game-theoretic depth, opt-in complexity, positional thinking over command shortcuts) and endgame targets (aspirational, post-launch direction — multi-perspective camera, intelligent opponent behavior). The foundational principles are at the same authority level as the Sacred Design Principles above and constrain how mechanics are designed. The endgame targets are not currently scheduled and do not bind launch implementation. See `bible_design_vision.md` for the full content and the binding-status legend.

---

## Expansion Packs and Monetization

> **Full reference: [`bible_monetization.md`](bible_monetization.md)**

The game is a **skeleton** (era-neutral engine). Expansion packs are the **skin** (theme packs that reskin every surface). The skeleton ships once; the skins ship forever. This is the commercial engine enabled by Sacred Design Principle #3 (era-agnostic architecture). Distribution uses a hybrid Steam + direct model with platform-agnostic entitlements. See `bible_monetization.md` for time period packs, isolated chapters, rotational AI-generated expansions, monetization model, distribution infrastructure, and future considerations (multiplayer, unit skins, Steam Workshop).

---

## AI Integration Pillar

> **Full reference: [`bible_ai_pipeline.md`](bible_ai_pipeline.md)**

AI is a core differentiator. The library builder pipeline generates content offline (chronicle templates, mission archetypes, briefing content, complication templates, event narratives), stores it in JSON, and the game reads it at runtime with zero API calls during play. The 3D asset pipeline uses AI-assisted modeling with human cleanup. The dynamic naming system generates names across four categories (people, places, units, factions) with per-faction variable subsets and cultural drift. See `bible_ai_pipeline.md` for the full pipeline architecture, asset pipeline, and naming system design.

---

## Transition from Previous Iteration

The game was previously an elegiac god-game where the player observed as "The Unseen Hand" and applied abstract declarations through a particle-based fate space. The redesign changes the player's role to commander, the interaction model to missions, and the game loop to generational chapters. This section captures what survives, what's cut, and what changes.

### New Project

The redesign starts a new project. Code from the old project is selectively copied during Stage 0 (see dev_rules.md), not inherited wholesale. The old repo is preserved as reference.

### Simulation Backend — Survives with Modification

The simulation backbone is the most valuable existing asset. **The simulation redesign is now resolved — see "The Simulation Backbone" section for the full architecture.** The engine uses a System Dynamics model with stochastic event chains, a layered region state model (granular fields + composite axes), and a defined tick resolution sequence. The core *concepts* from the previous iteration (multi-dimensional civilizational state, stochastic event firing, emergent narrative through a coherence ledger) survive in the new architecture. The specific old implementation (3D vector space with Entropy/Continuity/Reach, the old tick resolution model) is replaced by the new SD-based system.

**Likely to survive in some form:** The concept of a multi-dimensional state space for civilizational health. The outcome mapper concept (proximity-based probability). The coherence ledger (named character tracking — becomes more central as it drives character selection, inheritance missions, and chronicle scroll content). The region model and world state concepts. The library reader and its fallback contract. The template assembler's text generation machinery. Config values as a starting reference.

**Likely to need new operating mode:** The antagonist agent — replaced by the multi-faction agent model. All factions (including the player's civilization) run autonomous agents during time jumps, making discrete attack/defend/accumulate decisions each tick. The event firing system — runs in batch during time jumps. The tick system — must support autonomous batch processing (hundreds of ticks, no player input).

**Replaced conceptually:** The declaration resolver's force math is repurposed as the engine for translating mission outcomes into simulation inputs. Instead of six small per-tick player nudges, one consequence bundle of region stat changes is injected per mission. The per-tick player declaration interface is gone.

### Simulation Backend — New Systems Needed

Four new backend systems are required to support the mission-based game loop:

**Mission generator** — reads simulation state, identifies pressure points, matches them to library archetypes, fills variable slots, produces a structured mission briefing. This is the bridge between the simulation and the player.

**Chronicle scroll distiller** — takes hundreds of ticks of accumulated events from a time jump and compresses them into 5–10 scroll entries. Uses a three-pass algorithm: significance scoring (template tier as floor, delta magnitude as boost, context multiplier), lineage-first clustering (lineage → chain → regional summary), and keyed composable template selection (category-matched fragment assembly with base/expanded forms). See "The Chronicle" section for full algorithm.

**Character selector** — runs after the mission generator selects a mission region. Decides whether to continue the current lineage (delta-driven rotation probability with crisis veto and hard cap) or rotate to a new one (mission-coupled selection from three weighted pools: previous lineage descendant, nemesis descendant, unrelated). Manages minimal lineage member generation during time jumps (count + location, no traits). See "The Generational Structure" section for full algorithm.

**Mission outcome resolver** — takes the tactical layer's outcome band classification and produces region stat changes for the mission region using per-archetype proportional lookup tables. No separate vector nudge or world-wide momentum — consequences are region-local and the simulation propagates them naturally. See "Missions" section for full algorithm.

### Frontend — Fresh Start

All Godot frontend code is rebuilt from scratch. No visual work carries forward. The previous iteration's visuals were designed for a god-game observer — the new game needs a commander's interface. Ideas from the old visual work may inform future design but are not copied or ported.

**Cut entirely:** The fate space (particle visualization, declaration HUD, projection cones, counter-currents). The declaration UI (six buttons, hint system, resonance meter). All declaration feedback systems (ripple, bloom, comparison view). The role selection screen. The manifold line chart. The chronicle compression columns. The Unseen Hand identity.

**Will be rebuilt purpose-built:** World view, system view, planet view. Mission briefing screen. Recon phase view. Tactical mission layer (the biggest new frontend system). Chronicle scroll UI for time jump montages. Chronicle as intelligence feed during missions. Mission preference and difficulty selection in onboarding.

### Library Pipeline — Expands

The library builder architecture (offline generation, JSON storage, caching contract, API dispatcher) is the right pattern. The existing builder scripts and generated content survive. New builder scripts are needed for: mission briefing prose, chronicle scroll entry templates, and complication templates per mission archetype. The 10 mission archetypes are fully specified in the bible (simulation triggers, objective shapes, asset profiles, map characters, success spectra with consequence tables). The existing 102 event templates still generate events during time jumps and feed the scroll distiller.

---

## Open Design Questions

> **Governance reminder:** This section is a staging area. When a question here gets resolved through brainstorming, write the answer into its natural section in the relevant spoke file and remove the question from this list. If you are an AI session and you see decided content that still appears here as open, or an unresolved question living only inline elsewhere, flag it for Westley.
>
> **As of v1.21, questions 1–11 are all resolved.** No open design questions remain from the original list. Future design questions (mission archetype templates, tactical layer implementation, chronicle scroll UI, etc.) will be added here as they enter active design work.

### 1. Simulation Engine — Multi-Faction Design (RESOLVED across v1.01–v1.11)
*Fully resolved. Core architecture, faction agents, attack/conquest mechanics, colonization, diplomacy, oscillation, and all tuning passes complete. See `bible_simulation.md`.*

### 2. Force and Asset Design (RESOLVED in v1.12)
*Fully resolved. 6-unit roster, one ability per unit, light economy, force allocation algorithm. See `bible_combat.md` and "The Player's Toolkit" section above.*

### 3. Combat and Tactical Layer (RESOLVED in v1.12, updated v2.02)
*Fully resolved. SC2-style sim/renderer architecture: deterministic Python tick engine (20 ticks/sec) as ground truth, Godot as pure renderer, replay via initial state + command stream. Damage model: multiplicative RPS multipliers (Strike→Siege 1.5×, Siege→Line 1.5×, Line→Strike 1.5×; reverse 0.75×; mirror 1.0×), flat HP, AoE circles with damage cap, cover density reduction. Stat philosophy: A+C hybrid (long engagements with category-specific rhythm — Strike 10–15 sec, Line 20–30 sec, Siege 30–45 sec; large battles >60 sec). Tier 2 stat baselines for all 6 units. Command vocabulary: 4 commands (move, attack_move, attack_target, activate_ability). All movement commands run at each unit's native speed — no speed matching, no group-move primitive; combined-arms cohesion is a player skill, not an engine guarantee (resolved v2.07). Squads visual-only (single entity in simulation). Pathfinding: hierarchical A* + steering. Power rating formula for force parity. Supply/non-combat units included. Continuous 2D coordinates with discrete vertical layers. Cross-layer visibility: passive cone (degraded range on adjacent layers) + active sensor pulse. Elevation in space era: sensor advantage only, config flag for land-era damage bonus. Unit Behavior AI: universal decision loop, player-activated abilities, identical for player and enemy. See `bible_combat.md`.*

### 4. Map Generation System (RESOLVED in v1.13, updated v2.02)
*Fully resolved. Five-gradient property vocabulary (sensor_interference, elevation, obstacle_density, cover_density, layer_accessibility_mask). Strategic Layout Authoring Framework: shared pool of 10–20 hand-authored spatial blueprints defining zone positions and spatial relationships as relative coordinates; archetype topology templates redefined as compatibility filters selecting from the shared layout pool. Fog of war via multiplicative sensor radius reduction. Cross-layer visibility: combined cone + pulse model (passive degraded detection on adjacent layers at 50%/20% range, active sensor pulse with cooldown for full-layer snapshot). Vantage nodes double cone factors and extend detection +1 layer. Recon phase: terrain visible, enemies hidden. Canvas sizing: small 8000², medium 16000², large 24000² world units, archetype base + bounded simulation modifier (±30%). Formation width reference: 200 world units. Simulation-to-gradient mappings: composite axes for baseline intensities, individual fields for bounded texture deltas. See `bible_world.md`.*

### 5. Dynamic Naming System (RESOLVED in v1.13)
*Fully resolved. Three variable categories (linguistic roots, phoneme patterns, cultural flavor tags — era markers excluded per era-agnostic principle). Per-faction variable subsets with Schism cultural drift inheritance. Levenshtein dedup at build time, no redraw. Era-split pools (50% agnostic / 50% era-specific). Library fully separated from game, zero runtime AI dependencies. Ledger pulls via thin interface. See `bible_ai_pipeline.md`.*

### 6. Diplomacy and Peace System (RESOLVED — v1.16/v1.17)

*Fully resolved.* Three diplomatic states (hostile/neutral/cooperative). Cooperative benefits: adjacency bonus sharing, border friction removal, best-partner-only technology convergence. Peace formation: event-driven through sustained non-aggression and stability thresholds. Betrayal mechanic: per-tick probability roll scaled by archetype, opportunity, and internal pressure. Betrayal consequences: surprise attack + flip to hostile, no reputation system. Mutual defense coordination noted as future consideration. See `bible_simulation.md`.

### 7. Technology System (RESOLVED — v1.16/v1.17)

*Fully resolved.* Single numeric tech_level (0–100) per faction. Archetype-interpreted multipliers with ~20% total budget asymmetrically distributed per archetype. Tech growth driven by economy with population floor. Best-partner-only convergence in cooperative peace. Breakaway inheritance. Technology loss through event chains. 3 tech tiers per era (uniform boundaries: 0–33, 34–66, 67–100) with discrete jump transitions. Tier regression possible through tech loss. See `bible_simulation.md`.

### 8. Sci-Fi Era Tier Sketch (RESOLVED — v1.19)

*Fully resolved.* Base era identity: "The Settled Reach" (20–30 solar systems, expandable). Three-tier visual progression: Frontier (boxy, seamed, matte), Establishment (smooth, integrated, polished), Zenith (flowing, luminous, abstract). All 6 unit types designed across tiers with cross-era silhouette archetypes established as hard constraints for future eras. Tactical map structures defined (points of interest tiered, obstacles/cover/hazards universal). Galaxy view designed as 3D star map with orbital camera, faction territory coloration with defined borders, military flash VFX, ambient particle field, and seamless zoom transitions. Era creation template established for future era packs. See `bible_world.md`.

### 9. Region Tier Promotion (RESOLVED — v1.21)

*Fully resolved.* Regions use a **discrete tier system** — home, frontier, and empty — each with a configured military capacity cap (home: 100, frontier: 60). As a region's military approaches its tier cap, reinforcement efficiency drops toward zero. Colonized empty regions become frontiers. The tier distinction creates natural asymmetry: home regions can sustain full military strength while frontiers cap out lower, making them structurally easier to attack. Home regions are still vulnerable — their military decays without economic support, and conquest resets entrenchment. No tier promotion mechanic exists (frontiers don't become home regions). See `bible_simulation.md`.

### 10. Revolt Probability Scaling with Faction Size (RESOLVED — v1.21)

*Fully resolved.* An **administrative revolt system** operates independently of tension-triggered revolts. Every tick, each region in every faction rolls against `admin_revolt_chance = base_rate + scaling_rate * max(0, territory_count - inflection_point)^2`. The base_rate is nonzero for all factions regardless of size (even small factions can experience secession). Quadratic scaling above the inflection point makes large empires hemorrhage territory aggressively. The roll is uniform across all regions. When fired, a non-interruptible variable-length event chain (3–8 ticks) produces a new independent breakaway faction. The chain cannot be suppressed by reinforcement or condition improvement — once ignited, it always completes. Archetype resistance to scaling is deferred as a future tuning option. See `bible_simulation.md`.

### 11. Home Region Vulnerability (RESOLVED — v1.21)

*Resolved emergently through Q9 + Q10 interaction — no additional mechanic needed.* Home regions have a high military cap (100) but are not invincible — their military decays without economic support, and the administrative revolt system (Q10) guarantees that large empires shed territory, which collapses the empire's budget, which eliminates reinforcement spending, which allows natural military decay, which makes the home region crackable by external attackers. Home regions don't need a special vulnerability mechanic — they have a special *dependency* on the empire around them. Kill the empire, the capital follows. Entrenchment (tenure-based defense bonus) provides additional defender advantage that resets on conquest.

### 12. Reinforcement Structure Placement Strategy (RESOLVED — v2.08)

*Resolved.* Reinforcement structures are a new spine node type placed within the authored strategic layouts. Placement is authored per-layout, not per-archetype — archetype compatibility filters select which layouts apply to which archetypes, so a Defensive Stand pulls layouts where structures fall behind the player's lines and an Assault pulls layouts where they sit in the enemy's territory, without a parallel per-archetype placement override system. Initial ownership comes from a two-part rule: each archetype authors a baseline distribution (player / neutral / enemy percentages) reflecting its tactical intent, and the mission region's simulation state applies a bounded delta on top — military drives the player↔enemy axis, tension drives the neutral share, economy and population do not participate. The generator guarantees at least one structure per map so "zero production" is impossible. Strategic decisions (push for the structure or focus on the objective) emerge from the placement + ownership mix without structures overtaking objectives in importance.

### 13. Reinforcement Economy Tuning (RESOLVED mechanically — v2.08; numeric values remain tuning)

*Resolved in shape; numbers remain tuning.* The reinforcement economy has no currency — each structure produces one unit at a time and production time scales with unit power rating (more powerful units take proportionally longer). The player cannot pick individual units against a budget; the game surfaces production choices through which structures are held, not a shopping list. There is no baseline trickle — zero structures held means zero production, and the generator guarantees at least one structure per map so total zero is impossible. The enemy AI composition reactivity uses a single rule rather than a ratio profile library: if the player's composition exceeds ~70% in any one category (Strike / Line / Siege), the enemy's target ratio shifts ~15% toward the counter category; mild skews do not trigger adjustment. Specific production times, capture durations, structure HP, total structure count per canvas size, and the ~70%/~15% thresholds are tuning values adjusted through playtesting, living in engine config rather than in the bible.

### 14. Engagement Duration Rebalance (RESOLVED — v2.07)

*Resolved.* Stats rebalanced to hit the updated pacing targets (minimum 45s brawl, ~2 min tactical engagement, 50v50 mirror 150–200s). The rebalance was applied as a hybrid — both HP increases and damage reductions — and is **non-uniform across unit types** by design, because uniform scaling produced degenerate matchups at the new durations. Discrete stat values are implementation parameters and live in engine config, not in the bible. The design contract the rebalance preserves: engagements hit the pacing targets, the soft RPS triangle still produces the expected winners, and positioning and abilities remain decisive within a matchup. See `bible_combat.md` → Stat Philosophy.

### 15. Simulation State Journaling and Rollback (PARTIALLY RESOLVED — v2.09)

*Partially resolved.* Rewind-with-re-seed is in Stage 8 scope: the player can roll the simulation back to a previous snapshot and the simulation continues forward from that point with fresh stochastic outcomes. Because the simulation is stochastic, the second run diverges from the first — this is re-seeded re-simulation, not deterministic replay, with divergence growing as time progresses. Three classes of state persist: simulation state between missions and across time jumps, tactical engine state mid-mission for quit-and-resume, and onboarding preferences as "permanent for the generational arc." Replays are excluded. Snapshot cadence is event-driven boundary-only — every time jump boundary plus every mission start and end — so snapshots land on semantically meaningful narrative boundaries the rewind UI can label (chapter + mission). No per-tick periodic snapshots in Stage 8; adding intermediate sim snapshots is a candidate future enhancement. Branching model is linear-default plus explicit fork: rewinding a save slot truncates by default (snapshots after the rewind point are discarded and replaced by the new divergent run), and a separate "fork from here" action duplicates the slot at the rewind point into a sibling slot before rewinding the original, preserving an alternate timeline without making tree navigation a first-class concept. The Stage 9 save-slot browser is reused as the timeline browser; forks are just named sibling slots. Chronicle behavior on rewind: chronicle entries from a discarded timeline are **erased** on linear rewind — the chronicle always reflects exactly the canonical timeline. Fork-from-here is the explicit preservation mechanism for players who want to keep a pre-rewind chronicle. Two clean tools, two intents: fork preserves, rewind resets. This matches the bible's "fragments of a real history" framing (one history at a time, not a tree) and the elegiac tone. **Still open (not resolved by Stage 8):** crash recovery, multi-branch tree UI, cloud saves, and several sub-questions — snapshot retention policy (unlimited / ring buffer / keep-major-prune-intermediate / manual), the precise scope of tactical mid-mission state (single-slot quit-resume vs mid-mission rewind), and whether rewind should warn the player that divergence is the point. These pieces remain deferred beyond Stage 8 unless future brainstorming answers them.

### 16. Space Era Vertical Layer Visualization (OPEN — v2.04)

How should vertical layers be visually presented in space-themed eras (the Settled Reach and future space eras) where there is no natural ground plane? Land-based eras have an obvious answer (ground level, underground, elevated terrain), but space lacks inherent "up" and "down." The baseline approach decided in brainstorming uses a three-tier system that scales with map context:

**Tier 1 — Mechanical baseline (all space maps).** Each discrete layer is rendered at a slightly different visual depth. Units carry a small circular **layer indicator ring** beneath them, color-coded by layer. The active layer (where selection focus is) renders at full brightness and interactivity. Other layers render slightly dimmed, with units showing their layer-color indicator but not responding to click selection. Layer switching via hotkey (Tab or mouse wheel with modifier). The minimap shows all layers simultaneously with color-coded dots. This tier handles the pure spatial communication — the player always knows which layer a unit is on and can switch focus quickly.

**Tier 2 — Light environmental dressing (maps with moderate gradient features).** Where the spine + gradient pipeline places sensor interference or obstacle density sources near layer boundaries, the renderer adds subtle environmental elements — sparse debris, faint energy fields, thin particle wisps — that visually mark where layers differ. These elements are generated from gradient data, not manually placed. They provide visual texture that also hints at tactical properties (denser visuals = more sensor interference).

**Tier 3 — Heavy environmental dressing (maps with strong gradient features).** Full nebula bands, dense asteroid fields, or radiation belts serve as layer boundaries. This is the richest visual treatment and only appears when the map's gradients call for it. The environmental dressing directly communicates gameplay effects — a thick nebula between layers means degraded cross-layer detection.

The tier system means space battles range from clean (open space, layers distinguished primarily by depth and indicators) to atmospheric (nebula-choked space, layers separated by visible phenomena), depending on the map's procedurally generated character. This avoids the "nebula in every battle" problem while still allowing dramatic environmental layer boundaries when the map warrants it. The active sensor pulse ability could temporarily render all layers at full detail regardless of tier, providing a momentary cross-layer awareness burst that matches the gameplay mechanic.

Open visual tuning questions (deferred to when the renderer is running): Is the depth/parallax separation between layers sufficient for readability at the fixed top-down camera angle? What is the exact color coding per layer (must be colorblind-accessible)? How does the layer indicator ring interact with unit selection highlighting? Should layer-dimming be a simple opacity reduction or a desaturation + opacity shift? How many layers should space eras support (the bible specifies 3–5 for the abstract system; space may work best with 2–3)?

---

## Document Maintenance

### Rules

1. **The bible (hub + spokes) is the single source of truth.** If something in another doc conflicts with any bible file, the bible wins. Other docs should reference bible files, not duplicate their content.
2. **Append-only unless Westley approves.** See the modification rule at the top of this document. AI sessions add and expand. They do not delete or replace. This applies to all spoke files equally.
3. **Conceptual only.** No implementation details (file paths, function signatures, JSON shapes, config values). Those belong in architecture and stage docs.
4. **Update, don't append.** When a design decision changes *with Westley's approval*, update the relevant section in place. Don't add a "revision note" at the bottom — the document should always read as current.
5. **Open questions move to resolved.** When a question from the "Open Design Questions" section gets answered through brainstorming, the answer gets written into the appropriate spoke file and the question gets removed from the open list.
6. **Hub-and-spoke structure.** The bible is split into a hub (this file) and spoke files for major systems. Design decisions go into the relevant spoke file first, then get a one-line note in the hub's summary paragraph if they change the system's scope. If a spoke file conflicts with the hub, flag it for Westley — do not silently resolve the conflict.
7. **Version numbering.** The hub version number increments whenever any spoke or the hub changes. Major structural changes (new spokes, significant redesigns) increment the whole number (2.xx → 3.00). Minor additions, resolved questions, and refinements increment the decimal. Previous monolithic versions are preserved in `docs/bible_history/`.
8. **Spoke reading discipline.** Claude Code sessions read the hub plus only the spokes specified by their stage spec or task description. Stage specs must include a "Bible References" section listing exactly which spoke files and sections to read.

### Workflow with AI

- **Brainstorming happens in Claude.ai conversations.** These are ephemeral — they're for exploration, not record.
- **Decisions get captured in the bible.** After a brainstorming session produces decisions, the relevant spoke file (or the hub) gets updated. The conversation can be discarded.
- **Claude Code reads the hub as its starting point.** When implementation begins, Claude Code sessions start by reading this hub to understand what the game is, then read spoke files as directed by their task.
- **If a brainstorming session is long and needs to be continued across conversations, produce a `continuation_context.md`** that captures the current state of the discussion. This is temporary scaffolding — the decisions from it should be merged into the bible before implementation begins.

### Implementation Stage Roadmap

The game is built in numbered stages, each with its own spec document (`stage_N_spec.md`). Each stage proves a specific set of mechanics through behavioral claims (testable invariants) and validation criteria. Stages build on each other — later stages assume earlier stages pass. The split between "design" (Claude.ai brainstorming) and "implementation" (Claude Code) is maintained at the stage boundary: design decisions are resolved in brainstorming and written to the bible *before* the spec is written, and the spec is written *before* implementation begins.

**Stage 1** — World Graph and Passive Drift. Regions, adjacency, field drift with oscillation, adjacency bonus. The spatial foundation.

**Stage 2** — Event Chain Architecture. Threshold triggers, chain spawns, pending queue, collision resolution, mutual exclusion. The event system.

**Stage 3** — Faction Agents and Territorial Conflict. Budget accumulation, attack/colonize/reinforce decisions, intent-resolution loop, conquest, border friction. Multi-faction competition.

**Stage 3.5** — Diplomacy and Technology. Three diplomatic states, peace formation, betrayal mechanic, tech_level 0–100, tech tiers, convergence. Inter-faction relationships.

**Stage 4** — Civilizational Lifecycle and Generational Structure. Administrative revolts, lifecycle phase classification, time jump controller, generational structure (lineage rotation, faction reassignment). The world becomes a living history.

**Stage 5** — Chronicle Pipeline, Coherence Ledger, Library Builder, and Naming System. The library builder tool (API + manual modes for chronicle fragment and naming pool generation), the coherence ledger (named character lifecycle, lineage tracking, event attachment), the chronicle scroll distiller (three-pass algorithm: significance scoring → lineage-first clustering → template assembly), and the dynamic naming system. Time jumps produce real narrative with real names. All generated content is production-quality and ships with the game.

**Stage 5.5** — Mission Generation Pipeline. Mission generator (candidate scoring, archetype selection, variable filling), mission outcome resolver (proportional lookup tables consuming outcome bands from the tactical engine), force allocation algorithm (power-rating-based force parity). The bridge between simulation state and playable missions.

**Stage 6** — Tactical Simulation Engine (Headless). The deterministic Python tick engine: unit movement on continuous 2D space with vertical layers, RPS damage model, abilities, fog of war (sensor interference, cross-layer cone + pulse), pathfinding (hierarchical A* + steering), objective tracking, outcome band classification, power rating, replay command protocol. SC2-style sim/renderer split. All combat validated headless — no visual dependencies. Hundreds of engagements per hour for balance testing.

**Stage 7** — Map Generation and Tactical Reinforcement. The spine + gradient procedural pipeline (Strategic Layout Authoring Framework, archetype compatibility filters, direction-preserving fairness evaluator with per-archetype target profiles, region-state simulation flavoring). Tactical reinforcement structures (a new spine node type placed within authored layouts, ownership seeded by an archetype baseline plus a bounded simulation-state delta, producing replacement units during missions with production time scaled by unit power rating). Drifting spine nodes (objectives and reinforcement structures can follow authored paths during a mission; navmesh is built once and never regenerated). Wires the tactical engine to procedurally generated maps. Mission complications are deferred to a later stage. Enemy macro behavior moved to Stage 7.5; Godot renderer and game state persistence moved to Stage 8.

**Stage 7.5** — Enemy Macro Behavior Scripts. JSON-authored state-machine scripts consumed by a shared runner. Each archetype's script specifies forces, states (behavior + modifier + position), transitions (with timer / threshold / noise conditions over trigger-bus flags and tactical-state predicates), and reactive hooks. Compositional behavior vocabulary (the base behaviors plus modifiers that compose with them). Independent multi-force coordination through a shared trigger bus. Four prototype scripts authored first — Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency — to validate the vocabulary and trigger-bus pattern; the remaining six archetype scripts (Siege Breaking, Reconquest, Suppression, Interception, Evacuation, Containment) are authored in a follow-up pass once the prototype set proves out. The four prototype reinforcement ownership baselines (per-archetype player/neutral/enemy distributions that feed the Stage 7 ownership resolver) are also authored in this stage; the remaining six archetypes use a neutral fallback until their scripts land.

**Stage 8** — Godot Renderer, Command Interface, and Game State Persistence. The visual layer that makes the game playable: Godot as a pure renderer reading tactical engine state over a WebSocket bridge (Python engine as standalone server, Godot as client). Hybrid state synchronization (full snapshot on mission start + periodic snapshots every N seconds, delta updates between). Linear interpolation between engine ticks (20/sec) for 60fps rendering. Fixed-angle top-down RTS camera. Command input system inspired by Immortal: Gates of Pyre — classic PC RTS selection (click-to-select, box-select, right-click-to-move, control groups) with a persistent all-army hotkey that auto-includes newly produced units. Ability hotkeys mapped to the 5-command vocabulary. Vertical layer rendering uses a three-tier system: mechanical baseline (layer indicator rings, active-layer focus, dimmed inactive layers), light environmental dressing (gradient-driven debris/particles at layer boundaries), and heavy environmental dressing (nebula/asteroid layer boundaries where gradients call for it). Space-era-specific layer visualization is an open design question (see #16). Game state persistence covers three classes of state: simulation state between missions and across time jumps, tactical engine state mid-mission for quit-and-resume, and onboarding preferences as permanent for the generational arc. Replays are explicitly excluded. The simulation-state persistence is **rewind-capable** — the player can roll the simulation back to a previous snapshot and the simulation continues forward from that point with fresh stochastic outcomes (re-seeded re-simulation, not deterministic replay). Because the simulation is stochastic, the second run diverges from the first, with divergence growing as time accumulates. Snapshots land on semantically meaningful narrative boundaries (every time jump + every mission start and end) rather than periodic ticks. Rewind is linear by default (snapshots after the rewind point are discarded and replaced by the new divergent run) with an explicit "fork from here" action that duplicates the save slot at the rewind point before rewinding, giving the player a safety valve to preserve an alternate timeline. Forked slots appear in the Stage 9 save-slot browser as sibling slots; tree UI is not a first-class concept. The game becomes playable for the first time. Recon phase: free camera over the mission area with no time pressure. Terrain visible, enemy positions hidden by fog of war. Mission clock starts when the player hits 'Begin Mission.' See 'The Cycle' step 2 for the full design. Onboarding screen: single screen with difficulty setting and mission preference weights (10 archetypes, up to 2 markable as rare). Permanent for the generational arc. Opening time jump after confirmation (20–50 years, abbreviated 3–5 entry chronicle scroll). See 'Onboarding and First Chapter' for the full design.

**Stage 8.5** — Era Theme Resolution and 3D Asset Integration. The era-agnostic rendering layer that makes Sacred Design Principle #3 real in the visual pipeline. `EraThemeResolver` autoload reads per-era JSON manifests mapping abstract engine types to 3D model paths, material configs, and display metadata. Tactical renderers retrofitted from Stage 8 placeholders to production 3D models. Faction colors applied at runtime to model face groups with per-tier treatment (matte/metallic/emissive). Squad rendering for Strike units. Settlement structure models (the single interactive tactical structure) produced and integrated. Environment object scatter from gradient sources. Proven era-agnostic by a test-era swap: changing one config string swaps the entire visual presentation with zero code changes.

**Stage 9** — UI Shell: Main Menu, Era Library, Mission Briefing, and Game Management. The non-combat UI screens that wrap around tactical gameplay: Main Menu, New Game (era + template selection, save slot creation), Load Game (save slot browser), Era Library (in-game storefront with era cards, tier progression, mastery display), Era Detail (per-era deep-dive with unit roster and purchase flow), Key Redemption (with celebration animations), Mission Briefing (the hinge screen — two-column layout matching the bible reference mockup), and Settings (client-side display/audio/keybinds). All screens consume mock data through a `UIDataBus` singleton — the seam for backend integration. Security architecture: browser-redirect purchase flow (game never touches payment data), input sanitization on all text fields, pre-authored error messages only, no internal state leakage, `IS_RELEASE_BUILD` flag gates all debug output. Celebration animations use a two-layer hybrid system: shader atmospheres (background mood) + Unicode glyph bloom with departure-board title resolve (foreground events). See `animation_strategy.md` for the full animation design language. The game looks and feels like a product for the first time.

**Stage 10** — Backend Integration. Replace Stage 9's `UIDataBus` mock layer with a live WebSocket bridge to the Python sim (reusing Stage 8's protocol). Every Stage 9 screen reads real simulation state. Adds connection lifecycle (sim launched as subprocess on game start), loading and error states for async data, and entitlement state hardcoded to "Settled Reach owned" for the friends-ZIP build. The seam is preserved — only the bus implementation changes.

**Stage 11** — World View, Chronicle Scroll, and Seamless Transition. The macro-loop visual structure per `bible_world.md` (Galaxy View, Seamless Transition) and `bible_chronicle.md` (Chronicle Scroll). Mission end → camera pulls back → world view emerges → time jump executes with chronicle text printing → camera pushes into next region → next mission begins. One continuous flow, no loading screens. The world view uses the component architecture from `amendment_world_view_architecture.md`: `WorldViewShell` orchestrator, `WorldViewData` shared data store, per-era swappable renderers and cameras instanced via `setup_era()`. The Settled Reach renderer provides the first era's world view visuals (region nodes, territory bubbles with contoured borders, connections, military flashes). The main menu's decorative particle galaxy is a separate standalone scene (`world_view_structure.tscn`). ZIP scope cuts: region tier visualization optional. Faction territory, connections, and military activity flashes all required.

**World View Major Modification** — World View 3D Territory Visualization. Replaces the 2D metaball territory plane with a 3D constellation + shell hybrid. Constellation: faction-colored luminous Bézier filament arcs between adjacent same-faction systems. Shell: translucent 3D metaball isosurface membranes wrapping each faction's territory volume, with rival-shell gap and border glow. Three-band zoom disclosure ladder (Overview shell-dominant / Regional constellation-dominant / Local click-to-focus spotlight) with plateau-and-edge blending. Player camera controls (left-drag pan, scroll zoom, right-drag orbit, click-to-focus). Faction list panel with hover-dim/click-isolate (cross-band). Faction data panel with whole-faction stats. Time-jump animation dynamics: smooth territory tween morphing (no snap transitions), chronicle-linked focus highlight, faction-colored scroll entry text, ambient conflict flashes. File separation: main menu galaxy copied to frozen `main_menu_galaxy.gd/.tscn`, world view renderer modified independently. See `bible_world.md` "Territory Visualization" subsections and `world_view_major_modification_spec.md`.

**Stage 12** — Loop Edges: Onboarding, Mission Debrief, Save Serialization, Bug Report Capture. Closes every open end of the game loop for the friends-ZIP build. Onboarding enhanced with archetype descriptions and expand/collapse accordion. Mission debrief inserted between tactical mission and pull-back — displays outcome band, objectives, force retention, 3D ribbon performance graphs, and simulation impact preview. Autosave wiring at three loop boundaries (post-debrief, post-narration, mid-mission quit) with single-slot, no-rewind semantics (open-ended runs, single autosave overwritten each time, restart is hard reset). Bug-report capture system with rolling 5-second tactical state buffer, command log, F12 hotkey, ZIP bundler, clipboard delivery for Discord. Tutorial fully omitted (deferred to commercial-launch scope).

**Stage 12.5** — Combat Visual Polish. Makes tactical combat visually alive for the friends-ZIP build. Unit facing (target-priority rotation with speed cap), attack visuals (four era-agnostic rendering categories — projectile, volley, beam, area pulse — with hybrid mesh-head + GPU-particle-trail projectile construction and LOD tiers for 200v200 performance), ability overlay effects (ring telegraph, unit glow, screen-space distortion composing on top of enhanced base attacks), impact feedback (slow emission bloom + drifting impact particles in a cinematic register), and unit destruction sequences (death bloom → damage particles → drift → darkening, with wreckage LOD demotion and camera-distance-based hybrid cull). Ambient battle density resolved as a two-layer system: GPU particle haze (always-on base) plus 10–20 low-poly flyby ships on battle-biased Bézier paths (accent layer, cut first under frame pressure). Engine-side: `facing_rad` update rule (target priority) and ability activation events in the delta stream. Renderer-side: all visual systems, wreckage lifecycle, ambient density layers, performance budgeting. Additional polish: selection circle recolor (dimmer, faction-colored), HUD animation refinement (smooth transitions on panel appear/disappear, cooldown sweep animations, consistent timing per Stage 9 aesthetic), player-configurable edge-scroll speed setting. Minimap polish and sound placeholder hooks deferred to post-Stage 13. Aesthetic reference: Star Wars Revenge of the Sith opening battle — slow, massive, everything conveys mass and scale. See `bible_combat.md` "Combat Visuals" section for the full combat visual design.

**Stage 13** — Friends-ZIP Build, Bundling, and Distribution Hygiene. Self-contained Windows ZIP a friend can extract and double-click. Python sim bundled as a subprocess via PyInstaller (or Nuitka/Cython if startup time demands it — decide in spec). `IS_RELEASE_BUILD = true`, debug output suppressed. First-launch privacy modal disclosing scope ("private playtest, no automatic data collection"). Optional crash log written next to executable for manual email return. Pre-distribution checklist: clean install on a second machine, full loop verification, no leaked dev paths. ZIP delivered to a small group of personally-known playtesters. **This is not a commercial release** — no Steam, no monetization, no webapp, no entitlement. The build is retired when public beta begins. See `friends_zip_plan.md` for the full integration plan.

**Beyond Stage 13** — Multi-stage tutorial across hallmark eras (`bible_monetization.md` v3.00 component 8), inspection mode for non-owned eras, Era Library multi-era support (Roman free tier, 1980s, additional eras), Steam integration (Steamworks SDK, depots, branches, achievements, public beta), webapp + entitlement server + Stripe (commercial monetization per `bible_monetization.md`), sound design, music, era pack tooling for skeleton/skin expansion model, mission complications, remaining simulation-state journaling pieces not covered by Stage 8's rewind-with-re-seed (crash recovery, multi-branch tree UI, cloud saves — see open question #15), UI layout customization (a settings mode where the player can reposition HUD elements such as minimap, hotkeys bar, etc., flip map orientation, and preview changes live within the settings screen), **branch combat parameterization** (move reinforcement rates, structure density, engagement duration targets, HP/damage values, fog density, sensor range, and cross-layer detection from global constants to per-era manifest config — see re-open flags in `bible_combat.md` sections: Tactical Reinforcement, Stat Philosophy, Unit Stat Baselines, Information Warfare), **Settled Reach combat retcon** (rebalance Settled Reach HP and engagement timings downward for Branch 1 fast-burst tempo — substantial Stage-6-scale tuning pass). Scoped as needed.

---

## Operational TODOs

Tasks blocked on host or environment availability, not design. Cleared once the blocker is resolved.

### Stage 13 Checkpoint A — Windows PyInstaller pass

**Logged:** 2026-05-08 18:33 EDT
**Commit at logging:** `a41eeb67234ddd6cf40110c7be8ad40476c317b2`
**Blocker:** macOS host cannot cross-compile a Windows `.exe` via PyInstaller; no Windows host available right now.

**State at handoff (validated on darwin/arm64):**
- `build/pyinstaller_spec.spec` builds cleanly. Bundle: 32 MB. Cold ready: 5.60 s. Warm ready: 0.25 s. Smoke test passes: 4 messages received, command roundtrip `ready_for_tactical` → `snapshot` works, `--root <tmpdir>/logs/` created (not inside the bundle), no leaked dev paths in the bundled files.
- `build/build_zip.py` updated to reference `pyinstaller_spec.spec` (was `.py` — PyInstaller treats `.py` as an entry script, not a spec; renamed).
- `hidden_imports` extended by 11 modules: `command_ingest`, `mission_contracts`, `map_gen_contracts`, `debrief_data`, `power_rating`, `unit`, `world`, `faction`, `events`, `time_jump`, `world_view`, `world_view.time_jump_emitter`.
- PyInstaller 6.20.0 installed into `simulation/.venv` (Python 3.14.3, alongside existing `numpy 2.4.4`).

**To do on a Windows host:**
1. `python -m pip install pyinstaller` in the project venv.
2. `python -m PyInstaller --noconfirm --clean --workpath build/_pyi_work --distpath build/_pyi_dist build/pyinstaller_spec.spec`
3. Smoke test: `build\_pyi_dist\ouroboros_sim\ouroboros_sim.exe --root C:\path\to\test_dir` — confirm length-prefixed JSON progress messages, ready under 15 s, no console window, `<test_dir>\logs\` created, command roundtrip via stdin works.
4. Iterate `hidden_imports` if any `ImportError` surfaces in stderr. (Numpy hooks usually picked up automatically by PyInstaller; Windows-specific quirks unlikely but possible.)
5. Update Track C Checkpoint A in `docs/ai_status.md` with the Windows results.

### Track B / B3 — Control groups exclusive membership (untested in-game)

**Logged:** 2026-05-08
**Blocker:** Code change landed and headless test suite (`tests/test_input_router_control_groups.tscn`) passes 12/12, but the manual in-game checklist has not yet been run by Westley.

**Change summary:**
- `scenes/tactical/input_router.gd`: removed digit-1..4 hijack in `_handle_digit` (was calling `_select_all_army`/`_select_by_category`, blocking recall for groups 1–4); `1..0` now uniformly recalls. `_bind_group` rewritten for exclusive membership — a uid bound into a new group is removed from any other group it was in. Orphaned `_select_by_category()` and `_CATEGORY_TYPES` deleted.
- New tests: `tests/test_input_router_control_groups.{gd,tscn}`.

**To do (manual confirm in a live tactical mission):**
1. Select 5 units → `Ctrl+1` → press `1` → those 5 should reselect (was previously hijacking to "select all army").
2. Select 3 of those 5 → `Ctrl+2`. Press `1` → only the *other 2* should recall (exclusive membership working).
3. Press `2` → those 3 should recall.
4. With nothing selected, press `Ctrl+3` → group 3 should not exist (no-op on empty selection).

**Heads-up for B4:** the `1..0` keys are now exclusively recall keys. B4's category selection feature will need a different keybind.
