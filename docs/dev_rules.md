# Ouroboros Manifold — Development Rules

> **This document governs how the project is built.** The game bible (`game_bible.md`) says what to build. This document says how to build it, how to organize the work, and how to avoid the mistakes that killed the last iteration. Every Claude session — Code or chat — reads this file and follows these rules.
>
> **Last updated:** March 27, 2026

---

## Context

This is a solo developer project. Westley designs in Claude.ai (brainstorming, design decisions, documentation) and implements in Claude Code (writing and modifying code). The game bible is the single source of truth for design. This document is the single source of truth for process.

The previous iteration of this game suffered from:
- Code piling up without being proven, leading to 15+ orphaned files
- Systems growing tendrils into each other before they were validated, making removal surgical
- Design docs proliferating across many files with conflicting information
- Implementation racing ahead of design, requiring costly rework

These rules exist to prevent all of that.

---

## The Five Development Principles

### 1. Isolation First

Every new system starts as a standalone module with a clear API boundary. It reads inputs, produces outputs, and touches nothing else. If you delete the file, nothing breaks except the thing that calls it.

**In practice:**
- New systems live in their own file(s) with no imports from other in-progress systems
- Communication between systems happens through documented data structures (dicts, JSON schemas), not deep function calls into each other's internals
- A system should be testable in complete isolation — it should run with mock inputs and produce verifiable outputs without needing the rest of the project

### 2. Prove Before Integrating

Each system gets a "prove it" phase where it runs in isolation — a test script, console output, or minimal UI. Only after it's proven does it get wired into the larger system. Integration is a separate, deliberate step.

**In practice:**
- Every system has a standalone test or demo that proves it works before it touches anything else
- "Proven" means: Westley has seen it run, reviewed the output, and said "yes, this works"
- Integration happens in a dedicated step, not as a side effect of building the next thing
- If a system can't be proven in isolation, it's scoped wrong — break it down further

### 3. Thin Interfaces

Systems communicate through minimal, documented data structures. If System A needs something from System B, they share a data shape, not function calls deep into each other's internals.

**In practice:**
- Every system documents its input shape and output shape at the top of its primary file
- When two systems need to talk, define the interface contract first, then implement both sides
- If changing System A's internals would break System B, the interface is too thick — refactor
- Data structures should be plain dicts or simple dataclasses, not complex object graphs

### 4. Kill Switch Architecture

Every integrated system should be disableable with a single flag or config toggle. If you turn off the mission generator, the simulation still runs. If you turn off combat, missions still generate briefs. Nothing is load-bearing until Westley explicitly decides it is.

**In practice:**
- Every integration point has a bypass: `if config.ENABLE_MISSIONS: ...` else the system continues without it
- Default state for any new system is OFF until proven and explicitly enabled
- Disabling a system should never crash the project or produce errors — it should gracefully degrade to the behavior that existed before the system was added
- This means integration is always additive, never structural

### 5. Stage Gates

Each stage has a clear "done" condition. You don't move to the next stage until the current one is proven and Westley is happy with it. If he's NOT happy, the current stage's code can be killed cleanly because of principles 1–4.

**In practice:**
- Each stage spec defines a "Prove it" condition — a concrete, observable test that confirms the stage works
- Moving to the next stage requires explicit confirmation from Westley
- If a stage is abandoned, removing its code should take minutes, not hours
- No "partial stage" work that spans multiple stages — finish one, gate it, then start the next

---

## Stage Map

Each stage proves one thing before moving on. The simulation comes first, then narrative systems, then missions, then the player layer, then combat, then the full loop, then polish. Every stage is Python-only unless explicitly noted as Godot. Every stage is isolated and killable per the five principles.

The map is organized into groups. Within each group, stages are sequential — each builds on the one before it. Groups themselves are roughly sequential, but later groups may begin design work while earlier groups are finishing implementation.

---

### Group A — Simulation Foundation (Python only, console output)

#### Stage 0 — Region State and Passive Drift (Prove Fields Move) ✅ COMPLETE
Implement the four granular fields (military, economy, tension, population) and two composite axes (stability, capacity) for a single region. Implement the per-tick drift formulas from the bible. No events, no factions, no galaxy — one region updating in a loop.
**Prove:** Run 200 ticks on a single region with hand-set initial values. Print field values each tick. Confirm drift behaves as expected: military decays without economic support, tension rises under prosperity pressure and stress pressure, population grows logistically, composites reflect field state. Tuning values in config.

#### Stage 1 — Galaxy Generation and Multi-Region Drift (Prove Regions Interact)
Implement the galaxy as a graph of regions with typed adjacency edges (border, trade, both). Implement one starting template (isolated start). Run passive drift across all regions simultaneously. No events yet, no factions — just the SD model running across a connected galaxy.
**Prove:** Generate a galaxy from the isolated start template. Run 200 ticks. Print per-region summaries. Confirm regions drift differently based on their starting values and connections. Confirm edge types are stored (even if not yet used differently — untyped "both" is fine for this stage per the bible's implementation approach).

#### Stage 2 — Event Chain Architecture (Prove Events Fire and Chain)
Implement the event threshold trigger system (with per-region noise offsets), the pending event queue, chain spawns with delays and conditions, mutual exclusion tags, and simultaneous collision resolution. Use a small hand-authored set of test event templates (5–10) covering the key behaviors: threshold triggers, chain spawns, mutual exclusion, compounding collisions.
**Prove:** Run the simulation forward. Confirm events fire when fields cross thresholds (not before), chains propagate through follow-up events, mutually exclusive events resolve correctly, and simultaneous events on the same tick compound their deltas. Print an event log showing chain tags and causal links.

#### Stage 3 — Faction Agents (Prove the Galaxy Is a Free-for-All)
Implement the faction entity model (ID, archetype, owned regions, budget, budget growth, faction-level modifiers, diplomatic stance). Implement the three-decision agent model (accumulate, attack, reinforce). Implement attack event resolution with the resistance mechanic and conquest events. Implement the player's civilization autonomous defensive agent. Implement border friction. Start with one NPC faction (the Conqueror archetype) plus the player's civilization.
**Prove:** Generate a galaxy with two factions. Run 500+ ticks. Confirm the Conqueror accumulates budget, launches attacks based on attractiveness scoring, conquers regions when defenders are overwhelmed, and the player's civilization defends autonomously. Confirm border friction applies to contested borders. Print a faction summary showing territory changes over time.

#### Stage 4 — Coherence Ledger Core (Prove the World Remembers)
Implement the coherence ledger: named character tracking, faction arc tracking, cause-and-effect thread tracking via chain tags. The ledger reads the event log and tick history and maintains a structured record of who did what, where, and why. No chronicle generation yet — just the data layer.
**Prove:** Run a simulation with events and faction activity. Query the ledger for: named characters involved in events, causal chains that span multiple regions, faction arc summaries. Confirm the ledger can answer "what happened in Region X and who was involved" from structured data.

---

### Group B — Narrative and Chronicle (Python only, console output)

#### Stage 5 — Chronicle Scroll Distiller (Prove Time Jumps Tell Stories)
Implement the three-pass distiller algorithm: significance scoring (template tier as floor, delta magnitude as boost, context multiplier), lineage-first clustering (lineage → chain → regional summary), and cluster ranking to fill the 5–10 entry budget. No template assembly yet — output is structured data describing what each scroll entry would contain.
**Prove:** Run a simulation for 100+ ticks (a time jump). Feed the event log to the distiller. Confirm it produces 5–10 ranked clusters with lineage clusters guaranteed. Print the cluster summaries. Confirm the ordering makes narrative sense — the most dramatic events surface, minor noise is grouped into regional summaries, causal chains are kept intact.

#### Stage 6 — Chronicle Template Assembly (Prove the Scroll Reads Like History)
Implement the keyed composable template selection system: category matching, fragment pools (opening, detail, closing), variable slot filling from coherence ledger data, base form and expanded form generation. Author a starter set of templates (3–5 per major category). Wire the distiller's output into the template assembler.
**Prove:** Run a full time jump and distill. Feed the clusters to the template assembler. Print the resulting 5–10 scroll entries as prose. Confirm they read like fragments of real history — not data dumps, not repetitive, and the variable slots are filled with actual names and places from the ledger.

#### Stage 7 — Character Selector (Prove Lineages Persist)
Implement the character selector algorithm: rotation decision (regional delta scoring, crisis veto, hard cap, forced rotation), lineage selection on rotation (three weighted pools: previous lineage descendant, nemesis descendant, unrelated), and minimal lineage member generation during time jumps. Wire into the coherence ledger for lineage tracking.
**Prove:** Run a multi-chapter simulation (simulate → select character → simulate → select character, repeated 10+ times). Print the lineage history: which family was active each chapter, when rotations occurred and why, how descendants were distributed. Confirm lineages persist for 2–4 chapters on average, crisis veto works, hard cap forces rotation, and the three selection pools produce varied but coherent lineage arcs.

---

### Group C — Mission Systems (Python only, console output)

#### Stage 8 — Pressure Point Detection (Prove the World Has Needs)
Implement a module that reads simulation state (composite axes, active event chains, faction conflicts at borders) and identifies mission-worthy regions. Output is structured data: which regions need attention, what kind of pressure they're under, how urgent it is.
**Prove:** Run the simulation forward 100+ ticks with active factions. Feed the state to the pressure point detector. Confirm it identifies regions under military pressure, regions with high tension, regions with active faction conflicts. Print the pressure point list ranked by urgency. Confirm stable regions are excluded.

#### Stage 9 — Mission Generator (Prove the World Can Ask for Help)
Implement the mission generator algorithm: build candidate pool (region × archetype pairings), score each candidate (urgency, relevance, preference weights), weighted random draw from top candidates, variable slot filling. Author 3–5 starter mission archetypes (at least one military, one crisis response, one exploration). Wire into pressure point detection and coherence ledger.
**Prove:** After a time jump, run the mission generator. Print the produced mission brief: objective, context, forces implied, time constraint, named characters involved. Run it 10 times from the same state and confirm variety — the weighted random draw produces different missions, not the same one every time. Confirm preference weights shift the distribution.

#### Stage 10 — Mission Outcome Resolver (Prove Consequences Land)
Implement the outcome resolver: receive an outcome band classification, look up the per-archetype proportional consequence table, compute field deltas scaled to the region's current state, apply to the mission region. No tactical layer yet — outcome bands are manually selected for testing.
**Prove:** Set up a mission region in a known state. Feed each outcome band (total success through total failure) to the resolver. Print the resulting field deltas. Confirm proportional scaling works — saving a desperate region produces bigger absolute deltas than reinforcing a strong one. Confirm failure in a weak region is catastrophic.

#### Stage 11 — The Full Backend Loop (Prove Generations Work End-to-End)
Wire the existing systems into a single loop: galaxy generation → opening time jump → distill chronicle → select character → generate mission → (manually select outcome) → resolve outcome → time jump → distill → select character → generate mission → repeat. This is the complete backend game loop minus combat.
**Prove:** Run 5+ chapters in a single loop from console. Print the full output: chronicle scroll entries, character selections, mission briefs, outcome consequences, and the galaxy state evolving between chapters. Confirm the loop produces a coherent generational arc — missions respond to real galaxy pressure, outcomes change the world, chronicles tell the story, lineages persist and rotate meaningfully.

---

### Group D — Godot Frontend Shell (Godot + Python via WebSocket)

#### Stage 12 — WebSocket Bridge (Prove Godot Can Talk to Python)
Establish the Godot ↔ Python WebSocket connection. Define the message protocol for the operations the frontend needs: request galaxy state, request time jump, request mission brief, submit outcome. The Python backend is the proven Group A–C stack. Godot sends requests, Python responds with JSON.
**Prove:** Godot sends "generate galaxy" → Python responds with galaxy state JSON → Godot prints it. Round-trip works, protocol is clean, no state leaks.

#### Stage 13 — Galaxy View (Prove You Can See the World)
Implement a minimal galaxy view in Godot: regions as nodes, edges as connections, faction ownership as color. The view reads galaxy state JSON from the backend. No interaction beyond camera controls. Low-poly, Art of Rally aesthetic target — but functional first, beautiful later.
**Prove:** Generate a galaxy, display it. Run a time jump, update the display. Confirm regions change visually when ownership or state changes. The player can look at a galaxy and understand what's happening.

#### Stage 14 — Chronicle Scroll UI (Prove Time Jumps Feel Real)
Implement the chronicle scroll display: split-screen layout (galaxy view left, scroll text right), word-by-word text printing, click-to-expand for detail, synchronized pacing with galaxy view border changes. The scroll reads distiller output from the backend.
**Prove:** Run a time jump. Watch the scroll print while the galaxy view updates. Confirm the dual-channel experience works — the player sees borders shift while reading why. Click-to-expand shows additional detail. The time jump feels like watching history unfold.

#### Stage 15 — Mission Briefing and Outcome Selection (Prove the Chapter Loop Works Visually)
Implement the mission briefing screen (situation, objective, assets) and a manual outcome selection interface (dropdown: total success / strong success / partial success / partial failure / total failure). Wire into the backend loop. No combat — the player reads the brief, selects an outcome, sees the consequences, watches the next time jump.
**Prove:** Play through 3+ chapters end-to-end in Godot: onboarding screen → opening time jump → chronicle scroll → mission brief → outcome selection → consequence → time jump → next brief. The full visual loop works. This is the clickable prototype of the entire game minus combat.

#### Stage 16 — Onboarding Screen (Prove the Game Starts Clean)
Implement the single onboarding screen: difficulty selection (Easy/Medium/Hard) and mission preference weights (five categories, one markable as "rare"). Wire into the backend — preferences feed the mission generator, difficulty feeds the force parity system (when it exists) and constraint compression.
**Prove:** Start a new game. Make choices on the onboarding screen. Confirm they persist across the entire session — mission types reflect preferences, and the backend receives the difficulty setting. Same screen fires on cycle restart after Exodus or Extinction.

---

### Group E — Fleet and Tactical Foundation (Godot)

#### Stage 17 — Ship Entities and Movement (Prove Ships Exist)
Add ship entities to Godot. Three categories (Strike, Line, Siege) with placeholder art. Basic movement on a 2D plane — select ships, issue move orders, watch them go. Squad grouping for Strike (multiple ships move as a unit). Individual control for Line and Siege. No combat, no damage, no abilities.
**Prove:** Place a mixed fleet in a tactical view. Select and command ships. Confirm movement feels responsive, squads stay together, heavy ships feel heavy, the top-down view is readable. The unit control feels good.

#### Stage 18 — Damage Model and RPS Core (Prove Fighting Works)
Add the damage model and the soft-counter RPS system. Strike beats Siege, Siege beats Line, Line beats Strike — soft counters, not hard. Basic AI for enemy ships (approach and engage). Two fleets fight. No abilities, no traits, no layers, no environments.
**Prove:** Set up a balanced fight. Confirm the RPS creates real tactical decisions — flanking Siege with Strike matters, Line holding against Strike matters. Positioning determines outcomes, not just unit composition. The counter advantage is real but overcomeable.

#### Stage 19 — Unit Stats and Traits (Prove Ships Feel Different)
Add the stat system (speed, firepower, durability, range, sensor radius) and trait system (passive characteristics: hardened hull, long-range sensors, etc.). Ships within the same category now feel mechanically distinct based on their stat profile and traits.
**Prove:** Create two different Line ships with different stat profiles and traits. Put them in the same combat scenario. Confirm they play differently — one holds a position better, the other flanks more effectively. The stat and trait layer adds meaningful variety without breaking the RPS.

#### Stage 20 — Active Abilities (Prove Mastery Has a Ceiling)
Add active abilities: triggered by the player, cooldown-based. Barrage for Siege, afterburner for Strike, etc. One or two abilities per ship class to start. A new player can ignore abilities and still play. A skilled player uses them to create decisive moments.
**Prove:** Run the same battle twice — once using abilities tactically, once ignoring them. Confirm the ability-using player has a meaningful advantage. The skill ceiling is real.

---

### Group F — Combat Depth (Godot, each sub-stage isolated and toggleable)

#### Stage 21 — 2.5D Vertical Layers (Prove Space Has Depth)
Add 3–5 vertical layers. Ships exist on a layer and can transition between them. Sensor coverage determines layer visibility. Config flag toggleable — combat works with or without layers.
**Prove:** Set up a battle with enemies on a different layer. Confirm layer transitions work, sensor coverage creates real uncertainty (an ambush from an unseen layer is surprising), and layer positioning adds tactical decisions that didn't exist in 2D.

#### Stage 22 — Environmental Hazards (Prove the Battlefield Is Alive)
Add environmental features: asteroids (obstacle density), nebulae (sensor interference), gravity wells (movement distortion), radiation zones (damage over time). Features are placed via the gradient field system. Config flag toggleable.
**Prove:** Fight in a hazard-rich environment vs. an open field. Confirm hazards create terrain-like tactical decisions — using cover, avoiding danger zones, luring enemies into bad positions. The battlefield feels like a place, not an empty arena.

#### Stage 23 — Moving Battlefields (Prove Nothing Stays Still)
Implement battlefield drift: spine nodes shift position over time, gradient sources move. The tactical space changes during combat. Convoy escort missions move the engagement zone. Config flag toggleable.
**Prove:** Run a battle where the engagement zone shifts. Confirm players must continuously reposition. A plan that was good 30 seconds ago is no longer optimal. The moving battlefield creates the World of Warships feel — angle and position relative to a shifting environment is always the most important decision.

---

### Group G — Map Generation (Python + Godot)

#### Stage 24 — Spine Generator (Prove Maps Have Structure)
Implement the spine graph generator: per-archetype scripts that produce 10–30 nodes with type tags and edges. Start with one archetype script (military defense). Output is a data seed — positions, types, connections. No rendering yet.
**Prove:** Generate 10 spines from the same archetype. Print the topology. Confirm each has deliberate tactical structure: chokepoints, flanking routes, defensible positions, objective placement. Confirm variety — no two are identical but all are structurally sound.

#### Stage 25 — Gradient Fields (Prove Maps Have Texture)
Add gradient field generation on top of the spine. Field sources with position, property type, radius, intensity, falloff. The spine provides structure, gradients fill the space with navigational texture. Still data output — no rendering.
**Prove:** Generate a complete map seed (spine + gradients). Print the data budget (~350 bytes). Sample gradient values at various positions and confirm they produce sensible spatial properties — dense areas near obstacle sources, dangerous areas near hazard sources, open areas between.

#### Stage 26 — Map Renderer (Prove Maps Look Like Places)
Implement the Godot-side map renderer that interprets spine + gradient data into era-appropriate 3D geometry. Use the sci-fi theme pack mapping: obstacle density → asteroid fields, hazard intensity → radiation zones, etc. Low-poly Art of Rally aesthetic.
**Prove:** Generate a map seed and render it. Walk the camera through the space. Confirm it looks like a place — the spine creates readable tactical geography, the gradients create organic visual texture, the thematic mapping makes it feel like sci-fi space. Continuous movement, no loading screens.

---

### Group H — Integration and the Full Loop (Godot + Python)

#### Stage 27 — Mission-to-Tactical Bridge (Prove Missions Create Battlefields)
Wire mission generation into map generation. When the backend produces a mission brief, the map generator creates a tactical scenario from the mission parameters: archetype determines spine script, region state feeds gradient flavoring, faction context determines enemy force composition. Force parity system allocates the player's forces based on civilization capacity and difficulty.
**Prove:** Generate a mission from the live simulation. Confirm the resulting tactical scenario reflects the mission context — a defense mission produces a defensible map with enemies approaching, an exploration mission produces an open map with unknowns. Force parity gives the player a winnable fight.

#### Stage 28 — Tactical-to-Outcome Bridge (Prove Combat Feeds the Simulation)
Wire the tactical layer's results back into the mission outcome resolver. The tactical layer classifies the player's performance into an outcome band. The resolver translates it into region stat changes. The simulation absorbs the consequences during the next time jump.
**Prove:** Play a mission. Confirm the outcome band classification makes sense (decisive victory → total success, barely survived → partial success, got destroyed → total failure). Confirm the resulting field deltas are proportional and appropriate. Run the next time jump and confirm the galaxy reflects what happened.

#### Stage 29 — The Complete Chapter Loop (Prove the Game Loop Is Fun)
Wire everything into the complete loop: onboarding → opening time jump → chronicle scroll → mission brief → recon phase → tactical deployment → combat → outcome → consequence → time jump → next chapter. This is the full game loop with all systems live. No kill switches — everything is on.
**Prove:** Play 3–5 full chapters. The experience should be: read a brief that makes you care, study the map in recon, fight a battle where your decisions matter, see consequences that change the galaxy, read a chronicle that tells the story of what happened while you were gone, and feel the generational arc building. If this is satisfying, the game works. If it isn't, identify which system is the weakest link and iterate.

---

### Group I — Content, Polish, and Expansion Architecture

#### Stage 30 — AI Library Content Expansion (Prove Variety Holds Up)
Expand the AI library: 15–20 mission archetypes across all five categories, chronicle template variety (many fragments per category), naming system with diverse cultural flavor, ship stat profiles per civilization trait. This is content volume, not new systems.
**Prove:** Play 10+ chapters. Confirm missions don't repeat thematically, chronicle entries stay fresh, names feel authored not generated, and ship variety creates different tactical textures across chapters.

#### Stage 31 — Complication System (Prove Disruptions Are Memorable)
Implement the deferred complication system: per-archetype complication tables, pre-computed firing at mission generation, roughly every-third-mission frequency. Complications fire mid-mission as narrative and tactical disruptions.
**Prove:** Play 10+ missions. Confirm complications fire at roughly the target frequency, feel like memorable disruptions (not background noise), and create genuine tactical pivots. A faction collapsing mid-evacuation should be a story the player tells later.

#### Stage 32 — Theme Pack Interface (Prove the Skeleton Accepts Skins)
Formalize the era-agnostic theme pack interface: the boundary between the engine's abstract concepts (heavy combat unit, obstacle density, regional instability) and the theme's concrete content (battlecruiser, asteroid field, civil war). Build the interface contract that a theme pack must implement to plug into the engine. The sci-fi theme becomes the first theme pack — refactored from hard-coded content into the theme pack format.
**Prove:** The sci-fi theme pack is loaded through the theme interface, not hard-coded. A second test theme (minimal — placeholder names and art, but structurally complete) can be swapped in without changing engine code. The engine never says "starship" — it says "heavy combat unit" and the theme translates.

#### Stage 33 — Visual Polish, Sound, and Full Experience (Prove It's a Game)
Visual polish pass (Art of Rally aesthetic fully realized), sound design, UI refinement, chronicle typography, galaxy view beauty, time jump pacing, briefing screen feel. The full generational experience across multiple chapters and at least one full cycle (early → mid → late → terminal condition → restart).
**Prove:** A playthrough feels like a finished game, not a prototype. The elegiac tone lands. Time passing feels heavy. The chronicle reads like real history. Combat is satisfying. The galaxy feels alive. Someone who has never seen the project can pick it up and understand what they're playing.

---

**Note on stage ordering:** Groups A–C are backend-only and must complete before Group D begins. Groups E and F (fleet/combat) can begin design work during Group D but implementation starts after Stage 15. Group G (map generation) can proceed in parallel with Group E once Stage 11 is complete. Group H requires all prior groups. Group I is post-integration polish and expansion work.

---

## File and Project Organization

### Project Structure Philosophy

- **Flat over nested.** Don't create deep directory hierarchies speculatively. Start flat, add structure only when the number of files in a directory makes it unreadable.
- **One system, one file (to start).** A new system is one Python file or one GDScript file. Only split into multiple files when the single file becomes genuinely unmanageable (300+ lines with clearly separable concerns).
- **Tests live next to code.** Test files sit alongside the files they test, prefixed with `test_`. Not in a separate test directory.
- **Dead code gets deleted, not commented.** If something is no longer used, remove it. Git history preserves it if you ever need it back. Commented-out blocks are clutter that confuses future Claude sessions.

### Documentation Structure

```
docs/
├── game_bible.md          ← THE design document. Single source of truth.
├── dev_rules.md            ← THIS file. How the project is built.
├── stage_specs/            ← One spec per stage, created when that stage begins.
│   ├── stage_0_spec.md
│   ├── stage_1_spec.md
│   └── ...
└── continuation_context.md ← Temporary. For bridging brainstorming sessions.
```

- **game_bible.md** — what to build. Conceptual only. No code, no file paths, no implementation details.
- **dev_rules.md** — how to build it. Process, principles, stage map, organizational rules.
- **stage_specs/** — implementation details for each stage. Created one at a time, as each stage begins. Each spec is self-contained: what to build, input/output shapes, done condition, files to create.
- **continuation_context.md** — ephemeral. Exists only to bridge a brainstorming session across Claude.ai conversations. Gets deleted once its decisions are merged into the bible.

### Rules for Documentation

1. **Three docs maximum govern the project at any time:** the bible, this file, and the current stage spec. That's it.
2. **No other design docs.** If it's a design decision, it goes in the bible. If it's an implementation detail, it goes in the stage spec. If it's a process rule, it goes here. There is no fourth category.
3. **Stage specs are disposable.** Once a stage is complete and integrated, its spec is historical reference only. It should not be consulted for how the system works — the code is the source of truth for implementation, the bible is the source of truth for design.
4. **Never duplicate bible content in stage specs.** Stage specs reference the bible ("See game_bible.md, Missions section") rather than restating design decisions. This prevents conflicting information.

---

## Stage Spec Format

Every stage spec follows this structure:

```markdown
# Stage [N] — [Name]

## Goal
One sentence: what this stage proves.

## Context
What the player (Westley) should read in game_bible.md for design context.
What previous stages this builds on.

## What to Build
Concrete list of files to create, with purpose and scope for each.

## Input/Output Shapes
The data structures this stage's systems consume and produce.
Written as example dicts/JSON — not abstract descriptions.

## Integration Points
How this stage connects to previous stages (if at all).
What config flags enable/disable it.

## Done Condition
A concrete, observable test. "Run X, see Y, confirm Z."
Westley signs off on this before the next stage begins.

## Files Created
Filled in after implementation. Lists every file this stage produced.
Used for auditing — if a file isn't on this list, it shouldn't exist.
```

---

## Rules for Claude Code Sessions

### Starting a Session

1. **Read the game bible first.** Every Claude Code session begins by reading `game_bible.md` to understand what the game is.
2. **Read this file second.** Understand the development principles and where we are in the stage map.
3. **Read the current stage spec third.** This tells you what to build right now.
4. **Don't read old stage specs or old design docs.** They're historical. The bible and current spec are all you need.

### During a Session

1. **Build only what the current stage spec asks for.** Do not anticipate future stages. Do not add "hooks" for systems that don't exist yet. Do not build infrastructure "we'll need later." Build what's specified, prove it works, stop.
2. **One system at a time.** Implement, test, confirm. Don't start the next system until the current one is proven.
3. **Ask before integrating.** If a system needs to touch another system's code, stop and confirm with Westley. Integration is a deliberate decision, not a side effect.
4. **No dead code.** If you write something and it turns out not to be needed, delete it. Don't leave it commented out. Don't leave "utility functions" that nothing calls.
5. **Document interfaces, not internals.** Put docstrings on public functions describing what they take and return. Don't over-comment internal logic — the code should be readable on its own.
6. **Config values in one place.** All tuning parameters live in `config.py` (or equivalent). Never hardcode a value that Westley might want to adjust.
7. **Checkpoint output must be self-verifying.** Every data structure tested in a checkpoint must have its key properties printed in the output — not just asserted silently. If a checkpoint tests edge types, print edge types. If it tests field ranges, print the ranges alongside the values. Westley reviews checkpoints by reading terminal output, not by reading test code. If he can't verify a property from the printed output alone, the checkpoint is incomplete.
8. **Baby steps.** Each change should be small enough to verify independently. If a task feels like it needs 200+ lines of changes across multiple files, break it into smaller steps and confirm between each one.

### Mandatory Checkpoints — STOP AND WAIT

> **THIS IS THE MOST IMPORTANT RULE IN THIS DOCUMENT.** The entire development methodology depends on Westley seeing and approving output at every step. Claude Code cannot self-verify. Claude Code's judgment about whether output "looks right" is not reliable enough — it has been wrong. Only Westley's eyes count.

**After completing each step in the stage spec:**

1. **Run the prove-it test.** Execute the test script and capture the output.
2. **Show the output to Westley.** Print it, display it, make it visible. Do not summarize it — show the actual numbers.
3. **STOP. Do not continue to the next step.** Wait for Westley to review the output and say "yes, this works" or "no, this is wrong."
4. **Do not evaluate the output yourself and decide to proceed.** You are not the judge of whether the simulation's behavior is correct. Westley is. Your job is to build, test, and present. His job is to evaluate and approve.
5. **Do not batch multiple steps.** Each step gets its own checkpoint. Do not implement steps 2 and 3 and then show output for both — implement step 2, show output, wait for approval, then implement step 3.

**What counts as a step:** Every numbered step in the stage spec (A1, A2, B1, etc.) is a checkpoint. Every substep that produces testable output is a checkpoint. If you're unsure whether something needs a checkpoint, it does.

**What "STOP" means:** Stop generating code. Stop running tests. Stop planning the next step. Present the output and wait for input. The next message from Westley determines what happens next — proceed, adjust, or redo.

**Why this exists:** This is a solo developer project. The developer cannot review code and output if Claude Code has already moved three steps past the problem. The incremental build methodology only works if every increment is verified before the next one begins. Skipping checkpoints turns "small provable steps" into "a big pile of unverified changes" — which is exactly what the dev rules exist to prevent.

### When Something Doesn't Work

1. **Don't pile fixes on top of broken code.** If a system isn't working, understand why before adding more code. Adding code to work around a bug creates the exact tangle this process is designed to prevent.
2. **It's okay to delete and restart a system.** The isolation principles mean this is cheap. If a module isn't working after reasonable effort, delete it and rebuild with a clearer understanding. This is faster than debugging a tangled mess.
3. **Escalate design questions.** If implementation reveals a design problem — something the bible didn't account for, or two design decisions that conflict — stop implementing and flag it. Westley will take it to a Claude.ai brainstorming session. Don't make design decisions in implementation sessions.

---

## Rules for Claude.ai Brainstorming Sessions

### Purpose
Claude.ai sessions are for design exploration, decision-making, and documentation. They are NOT for writing code.

### Starting a Session
1. Upload `game_bible.md` and `continuation_context.md` (if continuing a prior session).
2. Upload this file if the session might touch process/organization questions.
3. Upload old design docs (architecture.md, etc.) ONLY if the session is about mapping existing systems to the new design.

### During a Session
1. **Decisions get captured in the bible.** At the end of a session (or when a major decision is made), update the bible. Don't leave decisions only in the conversation.
2. **Produce a continuation context if the session will span multiple conversations.** This is a temporary file that captures where the discussion is, what's been decided, and what's still open. It gets deleted once its contents are merged into the bible.
3. **Don't produce implementation docs.** Stage specs are produced by the session that begins a stage, not speculatively.

### Ending a Session
1. Update the bible with any decisions made.
2. If more brainstorming is needed, produce a continuation context.
3. If a stage is ready to begin, produce the stage spec for that stage.

---

## Repo Strategy

**New project.** The redesign is radical enough that starting fresh and selectively copying proven code is cleaner than stripping the old project. The old repo is preserved as reference but is not the working codebase.

**What gets copied (evaluated at Stage 0):**
- Simulation files that are still relevant: likely `vector_engine.py`, `region_model.py`, `world_state.py`, `config.py`, `antagonist_agent.py`, possibly `coherence_ledger.py` and `template_assembler.py`
- The library builder pipeline if the template format doesn't need fundamental changes
- Library content (JSON files) if the format is compatible

**What does NOT get copied:**
- All Godot frontend code (will be rebuilt from scratch starting Stage 4)
- The declaration system (`declaration_resolver.py`) — replaced by mission system
- The old WebSocket protocol — will be redesigned for the new architecture
- Any file not on the "copied" list — if it's not explicitly brought over, it doesn't exist

**The decision of exactly which files to copy happens during Stage 0**, when Claude Code is evaluating the existing simulation code against the new design requirements. This is not decided speculatively — it's decided with the code open.

---

## Communication Patterns

### Westley → Claude Code
- "Here's the stage spec, implement it"
- "This system doesn't feel right, let's debug"
- "Delete this, it's not working"
- "I want to adjust [specific thing], here's what I want instead"

### Westley → Claude.ai
- "I want to brainstorm [design area]"
- "This didn't work in practice, let's redesign"
- "Write up what we decided into the bible"
- "Produce a continuation context / stage spec"

### Claude Code → Westley
- "Here's what I built, here's how to test it"
- "This design decision doesn't work in implementation because [specific reason] — flag for brainstorming?"
- "Stage done. Here's the prove-it test. Ready for your sign-off."

### Claude.ai → Westley
- "Here's what I recommend and why"
- "Here are the tradeoffs between options"
- "Updated the bible with our decisions"
- "Here's the continuation context for next session"

---

## Summary: The One-Page Version

1. **Bible says what. Dev rules say how. Stage specs say what right now.**
2. **Isolate, prove, then integrate. Never the reverse.**
3. **If you can't delete it cleanly, it's wired in wrong.**
4. **Build only what the current stage asks for. No speculation.**
5. **Three docs govern the project. No more.**
6. **Dead code gets deleted, not commented.**
7. **Design questions go to brainstorming. Implementation questions go to Code. Never cross the streams.**
8. **Every stage has a gate. Westley opens it.**
9. **STOP after every step. Show output. Wait for Westley. Do not self-verify and continue.**
