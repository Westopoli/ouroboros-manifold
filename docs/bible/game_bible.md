# Ouroboros Manifold — Game Bible

This is the single source of truth for what this game is. If any other doc conflicts with this file, this file wins.

The bible is **rewrite-not-append.** Decisions that change replace prior text; they do not stack on top of it. The bible always describes what the game *is* right now. Historical snapshots live in `docs/bible_history/`.

---

## Table of Contents

- [Vision and Identity](#vision-and-identity)
- [Game Shape at a Glance](#game-shape-at-a-glance)
- [Sacred Design Principles](#sacred-design-principles)
- [The Simulation Backbone](#the-simulation-backbone)
- [The Generational Structure](#the-generational-structure)
- [Missions](#missions)
- [The Player's Toolkit](#the-players-toolkit)
- [Force and Combat Design](#force-and-combat-design)
- [The Antagonist System](#the-antagonist-system)
- [The Chronicle](#the-chronicle)
- [The World](#the-world)
- [Tone and Feel](#tone-and-feel)
- [What's Unique (Blue Ocean)](#whats-unique-blue-ocean)
- [Design Experience Guide](#design-experience-guide)
- [Monetization](#monetization)
- [AI Integration Pillar](#ai-integration-pillar)
- [Document Maintenance](#document-maintenance)
- [Implementation Stage Roadmap](#implementation-stage-roadmap)

Spoke files (full references for major systems) live alongside this hub at `docs/bible/bible_*.md`. A spoke exists only if a system is too long to fold into the hub cleanly. Read a spoke only when touching the system it owns.

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

**Isaac Asimov's Foundation series** is the primary narrative and thematic inspiration. The feeling of vast civilizational arcs, the tension between individual action and historical momentum, the sense of reading currents in a world too large for any one person to control — this is the Foundation feeling translated into interactive form. The game is set thousands of years in the future, in a world of humans, and the player experiences the rise and fall of civilizations from inside, not above.

Immortal: Gates of Pyre is a key source for the game's combat and accessibility philosophy — particularly its approach to low skill floor with high skill ceiling, and its RPS-with-exceptions unit design.

---

## Game Shape at a Glance

This game is a **pause-and-command tactical** wrapped in a batch-processed generational simulation. It is not turn-based. There is no end-turn button, no 4X cadence. It is also not an RTS in the marketing sense — pacing is deliberate, the player is encouraged to pause and read the field, and the engine never measures the player against the clock. Internally the tactical layer ticks at a fixed rate; externally the player experience is "stop, look, command, watch."

**Two layers.** Play alternates between two layers with distinct tempos:

- **Tactical layer — missions.** Pause-and-command tactical. The player commands force groups on a procedurally laid-out map, fighting one engagement per mission. A mission runs 30–60 minutes of continuous gameplay. The simulation is stopped during missions — the player's attention is on the tactical problem.
- **Macro layer — the generational sim.** A batch-tick simulation of the world's factions, regions, and history. The sim does not play in real time; it runs forward in deterministic ticks between missions, producing a state snapshot and a chronicle of what happened.

**The cycle.** Each loop of play moves through:

1. **Mission** (tactical, 30–60 minutes).
2. **Outcome resolver** (batch, instantaneous) — the mission's result is digested into a consequence bundle.
3. **Time jump** (batch ticks, animated as a chronicle scroll) — the sim runs forward, faction decisions resolve, events fire, the world evolves. The player watches a galaxy view animate and a 5–10 entry chronicle print itself across the scene.
4. **Character selector + mission generator** (batch) — the next chapter's protagonist and mission are selected from the new world state.
5. **Mission** (back to step 1, as a new character).

Steps 2–4 are the batch-processed window between missions. Steps 1 and 5 are the player's active gameplay.

**Tempo controls.** Missions run continuously but the player can pause at will to read the field and issue orders. The chronicle scroll between missions plays at a fixed pace; the player can click any entry to expand and read it, and can skip to the next mission.

**Rewind.** The player can roll the world back to a prior mission or time-jump boundary. The simulation does not deterministically replay; it re-runs forward from the snapshot with fresh stochastic outcomes, so the post-rewind history diverges from the discarded one. Two intents are supported: a linear rewind that truncates the discarded timeline, and a fork that preserves the discarded timeline as a sibling save before rewinding the original.

**What the player is doing, by layer.**

- **In a mission:** selecting force groups, issuing move / attack-move / target / ability commands, reading the engagement, deciding when to commit or break off. The player commands forces; they do not control individual units.
- **Between missions:** watching the chronicle scroll, hovering and clicking regions in the galaxy view, reading what their last mission caused, anticipating the next.

**Where to read more.** Simulation backbone and faction decision model: `bible_simulation.md`. Mission generation, archetypes, per-mission structure: `bible_missions.md`. Tactical engine, combat, force composition: `bible_combat.md`. Chronicle scroll, distillation, narrative entries: `bible_chronicle.md`. World view, galaxy map, between-mission visualization: `bible_world.md`.

---

## Sacred Design Principles

These are non-negotiable. Any feature that violates these is wrong.

1. **Genuine stochasticity.** Outcomes are truly uncertain. Multiple forces compete every tick — player effects, faction agent actions, and universe noise — and none fully controls the result. Never fake uncertainty.

2. **The simulation models civilizational state as a layered multi-dimensional space.** Granular per-region fields (military strength, economic output, factional tension, population) are the ground truth. Composite axes (stability, capacity) are derived from those fields and govern the simulation's big-picture decision-making. What is sacred is that the simulation tracks real, meaningful state at both granular and composite levels.

3. **Era-agnostic architecture.** The simulation engine, mission generator, faction agents, event chains, combat system, and game loop operate on **abstract mechanical concepts only**. The current setting is a sci-fi theme; the architecture must support any future theme without engine changes.

   **What this means in practice:**
   - No simulation code, event template, faction agent, drift formula, or config value name may reference a specific era, setting, or theme. `military_strength` is correct. `fleet_power` is wrong. `region` is correct. `star_system` is wrong. `heavy_combat_unit` is correct. `battleship` is wrong.
   - Theme-specific terms belong only in the theme/content layer (display names, art, prose), not in the engine.
   - Per-era config-driven parameter variation is fine. Code-branched era logic is not. `if era == "settled_reach"` is forbidden; the engine stays branch-blind and era-blind.

   This principle applies to this document too. Sections describing the engine speak the engine's language. Theme-specific terms (e.g., "starship," "galaxy") appear only in Vision and Identity (the default sci-fi presentation to players).

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
2. **Recon phase** — free camera over the mission area with no time pressure. The player observes terrain, enemy positions hidden by fog of war, points of interest, and their own starting deployment. The mission clock does not start until the player hits "Begin Mission."
3. **The mission** — the player commands their forces to accomplish the objective. The simulation is stopped during missions. Rare pre-computed complications may fire (roughly every third mission) based on the archetype's complication table.
4. **Mission resolution** — success exists on a spectrum, not a binary. The tactical layer classifies the outcome into one of the archetype's outcome bands, and the mission outcome resolver translates that into region stat changes applied to the mission region, scaled proportionally to the region's current state. The resolution also determines the **commander's fate**: survived, wounded, or killed. A killed commander is logged in the coherence ledger and becomes part of the lineage's narrative. Commander death is not a fail state — it's a narrative event the generational structure absorbs naturally.
5. **Time jump** — the simulation fast-forwards through a random duration between a configurable min and max (targeting 20–100 years). The player has no agency over the gap length. The player experiences the jump as a **chronicle scroll** — a text-based vertical timeline of 5–10 entries summarizing what happened between chapters, presented alongside an **animated map view** where the player watches faction territories shift, borders redraw, and new factions emerge. Three kinds of entries, in order: consequence entries (direct results of the player's last mission), world entries (things that happened on their own), and setup entries (the last one or two entries teeing up the new chapter). The player can click any entry to expand for extra detail.
6. **New chapter** — the player returns as a character selected by the simulation. **Lineage persistence:** the simulation keeps the player within the same bloodline for 2–4 chapters before rotating to a different family. Within a lineage run, each chapter is a descendant. The simulation rotates to a new lineage when the character selector's rotation logic triggers, the bloodline has died out, or the world's pressure points have shifted to a region where a different lineage is more narratively charged. When the lineage rotates, the new character is selected from the weighted pool: most commonly a descendant of a previous commander from a different lineage, less commonly a descendant of a previous commander's rival, rarely an unrelated person elevated by circumstance.

### Character Selector Algorithm

The character selector runs after the time jump and the mission generator has selected the next mission's region and archetype. It determines whether to continue the current lineage or rotate, and if rotating, picks the new lineage.

**Step 1: Rotation decision.** The ledger tracks a chapter counter for the current lineage. The rotation decision uses three mechanisms:

- **Regional delta scoring** — after the time jump, the selector computes how much the lineage's home region (and adjacent regions) changed in field values during the jump. High total delta means the region is active and the family's story is in motion — stay. Low total delta means things are quiet — natural exit point. The delta score maps to a rotation probability via config curve.
- **Crisis veto** — if the lineage's home region is in an active crisis (stability below a config threshold, or an active event chain in a critical stage), rotation is vetoed regardless of delta score or chapter counter.
- **Hard cap** — a maximum chapter count (config value, ~6) forces rotation regardless of delta score or crisis state.
- **Forced rotation** — if the bloodline has no living members, or the commander died and no immediate family successor exists, rotation is forced immediately.

Flow: check forced rotation → if chapter counter below eligible range (2), stay → if at or above hard cap, rotate → compute delta score → map to probability → roll → if rotation triggers, check crisis veto → if vetoed, stay → otherwise, rotate.

**Step 2: Lineage selection (on rotation).** The selector runs after the mission generator has chosen the mission region. It finds the best lineage for that region:

- **Priority 1 — Previous lineage descendant (~70%).** Check all previous lineages. Does any have living descendants in or near the mission region? Score by recency penalty, descendant count, and chapter gap. Weighted random draw.
- **Priority 2 — Nemesis/rival descendant (~20%).** Check the coherence ledger for named characters who were rivals or antagonists to any previous commander. Descendants in the mission region make this pool eligible.
- **Priority 3 — Unrelated person (~10%).** No previous lineage or nemesis connection. Generate a new character from that region.

Pool weights are config values. If the selected pool has no valid candidates, fall through.

**Step 3: Commander assignment.** The selected character is registered in the coherence ledger as the new commander. The chapter counter is incremented for the lineage. See `bible_simulation.md` for the data contract.

**Step 4: Lineage member generation during time jumps.** During each time jump, a lineage generator module runs a minimal family tree update: N descendants produced (based on jump length and a fertility config value), distributed across regions based on where the family currently lives. Each descendant gets a name, region, and age. No personality traits, no career simulation, no detailed life events — the chronicle distiller and templates add narrative richness in prose; the ledger just tracks who exists and where.

### Onboarding and First Chapter

**Single onboarding screen.** Before chapter 1, the player makes two permanent choices on one screen: **difficulty setting** (Easy/Medium/Hard) and **mission preference weights** (across the 10 mission archetypes, with up to two markable as "rare"). Both are permanent for the entire generational arc. The same onboarding screen fires at the start of each new cycle after Exodus or Extinction.

**Opening time jump.** After confirmation, the game generates the starting world and runs an opening time jump (targeting 20–50 years). The player sees an abbreviated chronicle scroll (3–5 entries, all world entries). The mission generator then runs against the post-jump state, and the character selector draws from the "unrelated person" pool since no previous lineages exist.

### What Carries Over

- **The world remembers everything.** Simulation state carries forward completely. Every mission outcome, every faction shift, every tech advance or cultural collapse persists.
- **The player starts mechanically fresh each chapter.** New character, new forces, new mission. No persistent "player level" or unlocks.
- **The civilization evolves.** Technology advances (or regresses). Tools available in later chapters may differ significantly from early chapters.
- **The Ouroboros.** The game can cycle. If the civilization reaches Extinction with Amnesia, it restarts — and the player's next character exists in a world that contains the ruins of everything that came before.

### Player Civilization Mortality

The player's civilization has no plot armor. It can be conquered, fragmented, or ground into extinction by the same simulation forces that affect every other faction.

When the player's faction collapses (loses all regions, or is reduced below a viability threshold), the generational structure absorbs it: the chronicle frames the fall as a major scroll entry, the character selector reassigns the player to a surviving faction using modified lineage logic (prefer narrative connections; otherwise geographic overlap), and the player continues as a commander in the new faction.

**Cross-faction lineage rotation.** Even when the player's civilization survives, the lineage rotation system can move the player to a different faction for variety — after the hard cap on chapters, the character selector considers candidates across all factions, not just the player's current one.

### Terminal Conditions and the Cycle

Terminal conditions are not endpoints — they are transitions that the generational structure absorbs:

- **Exodus** — the civilization escapes to a new region. Simulation resets to an early-era state with the chronicle and ledger preserved.
- **Extinction with Amnesia** — the civilization dies. Cold restart with relics. The player remembers what their new character does not. Old waypoints exist but inspect panels read "Unknown."
- **The Unbroken Line** — the civilization endures through the late era. Eventually internal pressures force a transition (Exodus, collapse, or voluntary contraction).

The game loops through expansion → conflict → fragmentation → renewal at the faction level, not the global level. Multiple factions cycle independently. The player threads through these cycles via lineage rotation.

---

## Missions

> **Full reference: [`bible_missions.md`](bible_missions.md)**

Missions are generated from simulation state using a curated library of 10 mission archetypes with variables filled by the current world context. Each archetype defines its own simulation trigger conditions, objective shape, asset profile, map character, success spectrum with consequence tables, and complication templates. See `bible_missions.md` for the full generator algorithm, all 10 archetypes, objectives, difficulty/era scaling, briefings, complications, and outcome resolution.

---

## The Player's Toolkit

### What You Command

The player receives a **variable set of assets** per mission. What you get depends on what the civilization can provide (shaped by simulation state, tech level, and mission type).

Asset categories:

- **Forces** — combat units. Hard power. Defend, attack, project force.
- **Science units** — extend knowledge. Explore, investigate anomalies, boost tech.
- **Trade/supply convoys** — economic backbone. Run supply between regions.
- **Intelligence operatives** — eyes and saboteurs.
- **Cultural missions** — slow long-game stabilizers of cultural memory.

Not every mission includes every asset type. Non-military assets sit outside the combat RPS entirely; they have no combat capability and must be protected or evacuated.

### Commanding Forces

- Top-down tactical view.
- Click/select units, tell them where to go and what to do.
- Pause at will to read the field. Pacing is deliberate, not frantic. The skill is in reading the situation and making committed positioning decisions.

### Individual Units

Units feel real but are not deep characters. They have names. Losing one should sting — especially heavy Siege units — but attachment is to the mission and civilization, not individuals. Named tools you care about (like a favorite ship in FTL), not party members in an RPG.

### Light Economy

The player does not manage a civilization-level economy or build a base. The civilization allocates a **starting force** based on mission type and current state. The player's influence is **front-loaded into mission preference weights** set at game start.

This is the "commander, not king" principle applied to logistics. A thriving civilization gives you a well-equipped force. A declining one gives you scraps. The gap is where the drama lives.

**Local reinforcements during missions.** Starting force is roughly half of what the player fields over a full mission. The other half comes from **local reinforcement structures** — military infrastructure already in the region (garrison posts, militia stations, forward operating bases) that produce replacement units at a slow, steady rate. The player captures or holds these structures to receive reinforcements. The enemy has access to the same system. Total capacity is derived from the region's military field — a high-military region has more productive infrastructure. See `bible_combat.md` "Tactical Reinforcement System" for the design.

---

## Force and Combat Design

> **Full reference: [`bible_combat.md`](bible_combat.md)**

Three combat categories (Strike / Line / Siege) on a soft RPS spectrum, with 6 base unit types (2 per category). Each unit has one ability. Force allocation is algorithmic — mission type determines asset profile, civilization state determines what it can produce. Combat plays out on 2.5D vertical layers with moving battlefields and environmental hazards. The tactical engine uses a SC2-style sim/renderer split: a deterministic Python tick engine (20 ticks/sec) owns all gameplay state, Godot renders it. Damage uses multiplicative RPS multipliers (1.5×/0.75×/1.0×) with flat HP and cover density reduction. Engagement pacing is deliberate: minimum 45 seconds for a straight brawl, ~2 minutes with tactical play. Local reinforcement structures provide in-mission unit production. Enemy macro behavior uses a shared behavior script system. See `bible_combat.md` for the full unit roster, abilities, roles, damage model, stat baselines, command vocabulary, pathfinding, power rating, AI-generated variety, force allocation, map layers, tactical variety, enemy macro behavior, tactical reinforcement system, and combat visuals.

---

## The Antagonist System

> **Full reference: [`bible_antagonist.md`](bible_antagonist.md)**

All external antagonists are territorial military factions running the same agent framework as every other faction — same engine, different config weights. Five base archetypes, with more generated by the library builder. Internal antagonists (breakaway factions, coups, extremist movements) emerge from simulation mechanics and can be resolved, absorbed, or turned into allies. See `bible_antagonist.md` for archetype definitions, internal threat mechanics, spatial manifestation, and threat progression.

---

## The Chronicle

> **Full reference: [`bible_chronicle.md`](bible_chronicle.md)**

The chronicle is the player's window into the civilization's history — both the narrative montage during time jumps and the long memory across generations. The chronicle scroll distiller compresses hundreds of ticks into 5–10 entries using a three-pass algorithm (significance scoring, lineage-first clustering, keyed composable template selection). See `bible_chronicle.md` for scroll presentation, distiller algorithm, template framework, and lineage entanglement.

---

## The World

> **Full reference: [`bible_world.md`](bible_world.md)**

The world is a variable-size network of regions connected by a typed adjacency graph. World generation uses tiered templates (from isolated single-faction to contested multi-faction). The map generation system uses a Spine + Gradient hybrid approach with a Strategic Layout Authoring Framework — hand-authored spatial blueprints filtered by archetype topology templates. Per-faction lifecycle stages (Growth → Peak → Decline → Collapse/Rebirth) and civilizational lifecycle mechanics drive macro arcs. See `bible_world.md` for scale, generation templates, topology, lifecycle, spatial navigation, map generation pipeline, visual style, and the sci-fi era ("The Settled Reach").

---

## Tone and Feel

### Elegiac, Not Grim

The game is about civilizations rising and falling over vast timescales. The tone is that of a real history being recorded. There is tragedy — the threat cannot be stopped, only delayed. But there is also humor, beauty, and unexpected moments of hope.

### The Humor

The game has a sense of humor. Easter eggs, dry observations, and unexpected moments of levity are intentional. The humor is in the writing, not in the events. Dry, earned, occasionally absurd.

### The Weight of Time

The generational structure gives the game something almost no other game has: **the passage of centuries felt through play.** The player doesn't just read about time passing — they played the chapter that caused this. They remember the commander who failed, and now they're living with the consequences as someone new.

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

> Quick-reference for design decisions. When the code doesn't make an answer obvious, check here first.

### Core Player Identity

The player is **a commander** — one person with limited tools, given an impossible task by a civilization that has its own plans. The player influences the world but never dictates to it. They receive orders and equipment, not a kingdom and a treasury. The gap between what they need and what they get is where the drama lives. Every design decision should reinforce this: the player is *inside* the world, not *above* it.

### The Five Feelings

The game should produce these distinct experiences depending on the faction's lifecycle state. These are emotional targets — if a mechanic doesn't serve at least one of them, question whether it belongs.

1. **Pioneer survival** (young faction) — scrappy, resource-scarce, every mission matters because the faction can't absorb a loss.
2. **Strategic depth** (established faction) — real military, real logistics, real enemies. The player is a commander with actual resources making actual strategic choices about which fronts to prioritize.
3. **Imperial weight** (overextended faction) — too much territory, not enough resources. Every solution creates a new problem. Managing decline before it becomes collapse.
4. **Elegiac decline** (declining faction) — watching an institution die from the inside while trying to save what you can. Last stands, fighting former allies.
5. **Survival and identity** (faction born from collapse) — a new faction finding its footing in a dangerous world, surrounded by the wreckage of what came before.

The player may experience all five across a single playthrough through lineage rotation — including experiencing the consequences of their own failures from the other side.

### Design Decision Heuristics

- **Uncertainty** — genuine, never faked. If the player can guarantee an outcome, the design is wrong.
- **Control** — the player influences, never dictates. The civilization has its own plans.
- **Loss** — dramatic, never punishing. Losing a region is a chronicle moment, not a game over.
- **Humor** — dry, earned, never forced. The game winks, it doesn't mug.
- **Complexity** — accessible floor, deep ceiling. A new player plays without understanding every system. A skilled player plays differently because they read the situation better.
- **Pacing** — the world is always in motion. Static = broken.
- **Mastery** — mastery means understanding *why* you lost, not that you always win.

### The Litmus Tests

Quick yes/no checks for any feature:

1. **Commander or god?** If god — redesign.
2. **Chronicle material?** Would this produce interesting chronicle entries? If not, it's mechanical overhead without payoff.
3. **Era-agnostic?** Does this work identically with a different theme pack? If it depends on sci-fi specifics, it violates Sacred Principle #3.
4. **Loss is interesting?** Can the player lose and still want to keep playing?
5. **The world doesn't care?** Does the world continue operating regardless of the player's actions?

### Long-Term Design Vision

A separate spoke (if extant) documents the game's foundational design principles — skill ceiling as design target, game-theoretic depth, opt-in complexity, positional thinking over command shortcuts — at the same authority level as the Sacred Design Principles. See `bible_design_vision.md` if present.

---

## Monetization

The current model: **Roman-era sci-fi setting, buy-once at $10–$15.** No DLC ladder. No multi-era pack catalog at launch. Era-agnostic architecture (Sacred Principle #3) is maintained because it's the right architecture for a long-term project, not because a multi-era roadmap is committed.

If the game finds an audience and Westley wants to build another era pack later, the architecture is ready. Until then, one era ships, and it ships well.

Distribution: Steam, single SKU. No subscription, no in-game store, no Steam Workshop at launch.

---

## AI Integration Pillar

> **Full reference: [`bible_ai_pipeline.md`](bible_ai_pipeline.md)**

AI is a core differentiator. The library builder pipeline generates content offline (chronicle templates, mission archetypes, briefing content, complication templates, event narratives), stores it in JSON, and the game reads it at runtime with zero API calls during play. The 3D asset pipeline uses AI-assisted modeling with human cleanup. The dynamic naming system generates names across four categories (people, places, units, factions). See `bible_ai_pipeline.md` for the full pipeline architecture, asset pipeline, and naming system design.

---

## Document Maintenance

### Rules

1. **The bible (hub + spokes) is the single source of truth.** If something in another doc conflicts with any bible file, the bible wins.
2. **Rewrite, never append.** When a design decision changes, the prior text is *deleted*. No "In Flux" sections, no "PIVOT" markers, no "as of date X" callouts, no revision notes at the bottom. The bible always reads as current. History lives in `docs/bible_history/` and `git log`.
3. **Conceptual only.** No implementation details (file paths, function signatures, JSON shapes, config values). Those belong in architecture and stage docs.
4. **Spoke discipline.** A spoke exists only if a system is too long to fit cleanly in the hub. Most decisions live in the hub. If a spoke conflicts with the hub, flag it.
5. **Reading discipline.** Read the hub. Read a spoke only when touching the system it owns.

### Workflow with AI

- **Design happens in dedicated chats (Design Lane, Research Lane).** These are ephemeral — for exploration, not record.
- **Decisions get captured in the bible.** After design produces a decision, the bible gets updated in the same pass. The chat can be discarded.
- **Claude Code reads the hub as its starting point.** When implementation begins, sessions read this hub to understand what the game is, then read spokes only as directed by the task.

---

## Implementation Stage Roadmap

The game is built in numbered stages, each with its own spec document (`docs/stage_specs/stage_N_spec.md`). Each stage proves a specific set of mechanics through behavioral claims (testable invariants) and validation criteria. Later stages assume earlier stages pass.

**Status as of bible rewrite:** Stages 1 through 12.5 landed in some form. Stage 13 (packaging) was in progress at the prior project framing and is now deferred — there is no ship deadline. The stage docs are the working record of what was built and what remains open. See `docs/stage_specs/` for the live state, and `docs/priority_queue.md` for the next feature to land.

Stage capsule list (one line each, full specs in `docs/stage_specs/`):

- **Stage 1** — World graph, passive drift.
- **Stage 2** — Event chain architecture.
- **Stage 3** — Faction agents, territorial conflict.
- **Stage 3.5** — Diplomacy, technology.
- **Stage 4** — Civilizational lifecycle, generational structure.
- **Stage 5** — Chronicle pipeline, coherence ledger, library builder, naming.
- **Stage 5.5** — Mission generation pipeline.
- **Stage 6** — Tactical simulation engine (headless).
- **Stage 7** — Map generation, tactical reinforcement.
- **Stage 7.5** — Enemy macro behavior scripts.
- **Stage 8** — Godot renderer, command interface, save/rewind.
- **Stage 8.5** — Era theme resolution, 3D asset integration.
- **Stage 9** — UI shell (main menu, briefing, library, settings).
- **Stage 10** — Backend integration (live WebSocket bridge replacing UI mocks).
- **Stage 11** — World view, chronicle scroll, seamless transition.
- **Stage 12** — Loop edges (onboarding polish, debrief, autosave, bug-report capture).
- **Stage 12.5** — Combat visual polish.
- **Stage 13** — Packaging + distribution hygiene. Deferred.

Stage 13 and any future stages are picked up only when their feature reaches the top of `docs/priority_queue.md`. Stage roadmap is not a forced march; it's a description of how the systems stack.
