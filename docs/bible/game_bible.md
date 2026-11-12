# Ouroboros Manifold — Game Bible

This is the single source of truth for what this game is. If any other doc conflicts with this file, this file wins.

The bible is rewrite-not-append. Decisions that change replace prior text. The bible always describes what the game is right now. Historical snapshots live in `docs/bible_history/`.

## How the bible is organized

- **This hub.** Vision, principles, the shape of the game, tone, monetization. Human-facing and short.
- **`stories.md`.** The story catalog: one row per user-facing behavior with a stable id, its epic, its status, and a pointer to its depth. No design lives there.
- **`epics/E-##-<slug>.md`.** One file per feature area. Each carries the definition-completeness gate result, purpose, stories with Given/When/Then rules, inputs, outputs, invariants, scale requirements, references, ways it could be wrong, open flags, and dependencies. Machine-readable: Agora's rules files derive from these by script.
- **`references/E-##/`.** Screenshots, clips, and notes from games that show how a story should look or behave. The visual ground truth for QA.
- **`algorithms.md`.** The retained equations, named and numbered, with constants. The contract for the C rewrite.
- **`docs/northstar/ambiguity_register.md`.** Every open question, with candidate answers. An epic with an open flag is not built.

Read this hub first. Read an epic only when touching the system it owns.

## Vision and Identity

### What this game is

Ouroboros Manifold is a multiplayer strategic real-time strategy game set in a living, stochastic galaxy. The player is not a god, not a king, and not the leader of a civilization. The player is a commander: one person given a task force and an impossible job by a civilization that has its own plans, its own politics, and its own momentum. The world does not revolve around the player. It moves on its own.

Missions are won or lost on positional skill. A smaller force that understands surrounds, high ground, and the 2.5D layer and vision system beats a larger force that does not. That is the skill ceiling, turned up past StarCraft 2's bar. Combat is full real-time, consistent across every player in a match; a multiplayer match never pauses.

The game is structured as a generational chain of missions. Each mission is a chapter. Between chapters, decades pass and the galaxy evolves through the simulation. The player returns as someone new: a descendant, an old enemy's heir, or a stranger raised by circumstance. The player's career across generations is the story. The bloodline is cosmetic: it changes who the player is and what the chronicle says, never a simulation number.

The game ships across multiple eras built on one shared skeleton. Maps, civilizations, and era systems are transferable systems, not bespoke content. Players who own the same era packs can play a match that moves chronologically through them. Every era has an era kind, space or ground (Westley, 2026-10-05); the kind decides the vision model and the landscape, and the one exception is a ground era with flying units, which borrows pieces of the space model for them.

### The skeleton

What is shared across every era, decided 2026-10-05 (Westley: "we're going to eventually have 20+ eras that are on top of the 'skeleton' we're currently building"):

- The strategic simulation of civilizations, factions and regions; the time jump and the generational loop; campaign carry-over between eras.
- The chronicle machinery (half of each prose and naming pool is shared).
- Mission archetypes and objectives; the layout engine; the fairness numbers (equal distance to the objective; significant resources opposite it).
- The five layers; the command set; group movement at the slowest member's pace; formations.
- The three unit categories and their counter table; the three tiers; the unit roles.
- Enemy AI.
- The economy's structure: three resources, buildings, population, tech choice, the economy seat; a base of operations for every side; the settlement generator.
- The landscape placement engine.
- The five skills and the strategic-depth measure.
- Saves, multiplayer lockstep, and a UI that reads everything from the pack.

Shared within an era kind: the vision model; on the ground, height bands, slopes, walking units and strongpoints; in space, free layers, the ping and the space landscape; landscape objects and environmental troubles.

Supplied per era: identity, models, structures, palette; names and prose; unit types and stats; ability visuals; resource names and building pieces; the landscape kit.

### The core fantasy

You are a commander in a vast civilization. You are given a force, a mission, and a deadline. While you work, the galaxy keeps turning. Factions rise and fall. When your mission ends, success, failure, or something in between, time jumps forward and the galaxy changes in ways shaped by what you did but not controlled by it. Then you return as someone new, in a world that remembers what happened even if your new character does not.

Over many chapters you experience a civilization's rise, its crises, and its potential extinction from inside, not above. You are always one person with limited tools in a galaxy that is genuinely uncertain.

### The feeling

The tragedy of understanding something you cannot fully control. You can read the situation, make the right call, commit your forces, and it still might not be enough. Not because the game cheated, but because the world is too big and too alive for one hand to hold it all. You are inside the machine, reading the currents, doing what you can.

### What it feels like, and what it does not

- StarCraft 2 for feel and unit interaction: surrounds and high ground matter, and here they matter more. For movement and targeting it is the rule book, not only the feel: where a movement or targeting rule of this bible is silent or can be read two ways, StarCraft 2's behaviour is the answer, and a deliberate difference is written as a rule (Westley, 2026-10-20, 2026-11-06, 2026-11-11; E-11 S-087, E-13 Purpose).
- Age of Empires 3 and Halo Wars for large-scale battles and how forces are handled: heavy units individually, light units as squads, a selection moving at the pace of its slowest member.
- Immortal: Gates of Pyre for the combat and accessibility philosophy: low skill floor, high ceiling, rock-paper-scissors with exceptions.
- Art of Rally for the look: low-poly, stylized, clean silhouettes.
- Halo: Combat Evolved for storytelling and world-building, and for music: generated, in that spirit.
- Fortnite for the architecture of content: any skin, any map, any civilization, transferable across eras.
- Not Stellaris: you command a task force, not an empire's economy and diplomacy; the economy behind your war is run by rules, or by a partner (`E-22`).
- Not Total War: there is no campaign map and battle map split. In a mission the world is one world at continuous detail, from a single unit to the battlefield's map view, where the zoom stops (`E-17` S-166, `E-16` S-234); the galaxy is what you see between missions.
- Not a god game: you do not hover above the world pressing buttons. You are in it.

### Design inspiration

The primary narrative and thematic inspiration is the feeling of vast civilizational arcs, of individual action against historical momentum, of reading currents in a world too large for any one person to control. That inspiration is thematic only; the game uses no names, places, or plot from any existing fiction. The future era, the Settled Reach, is the setting where this feeling sits most naturally; other eras carry the same structure into other times.

## Game Shape at a Glance

Two layers with distinct tempos:

- **Tactical layer, missions.** Full real-time RTS. The player commands force groups on a procedurally laid-out map, one engagement per mission, 30 to 60 minutes of continuous play. Behind the fight stands a base and a real economy, run by rules or, in the paired mode, by a second player (`E-22`, `E-19` S-159). The strategic simulation is stopped during a mission; the mission's economy runs on its own tactical rules.
- **Macro layer, the generational simulation.** A batch-tick simulation of factions, regions, and history that runs forward between missions and produces a chronicle of what happened.

The cycle: mission; outcome resolver (the result becomes proportional changes to the mission region); time jump (the simulation runs 20 to 100 years while the player watches the galaxy animate and a five-to-ten-entry chronicle print itself); character selector and mission generator (the next commander and mission are chosen from the new state); mission again, as someone new.

In a mission the player selects force groups and issues move, attack-move, attack-target, and ability orders; uses the three layer actions on purpose (ping a layer, go dark or emit, and reach by unit type, `E-01` S-162 to S-164); reads the engagement; decides when to commit or break off. Alone, the player steers the economy with a dial, a doctrine, and requests made by pointing at the map (`E-16` S-231). Between missions the player watches the chronicle, reads the galaxy, and takes the next orders.

A single-player mission can be paused from the menu and a multiplayer match never pauses (`E-16` S-104, `E-19` S-142); there is no rewind of the galaxy. Chapter boundaries are the save points and the clean exits.

## Sacred Design Principles

These are non-negotiable. Any feature that violates them is wrong.

1. **Genuine stochasticity.** Outcomes are truly uncertain. Player effects, faction agents, and universe noise compete every tick and none fully controls the result. Never fake uncertainty.
2. **Layered civilizational state.** Granular per-region fields (military strength, economic output, factional tension, population) are the ground truth. Composite axes (stability, capacity) are derived from them and govern big-picture decisions. Real state exists at both levels.
3. **Era-agnostic architecture.** The engine speaks only in abstract mechanical terms: region, not star system; heavy combat unit, not battleship; military strength, not fleet power. Per-era variation is config the engine consumes uniformly; no code branches on era. This principle applies to this document: engine sections speak the engine's language, and theme terms appear only where the setting is being described.
4. **Skill ceiling as the design target.** Every system is judged by whether it lets a better-positioned, better-reading player beat a bigger force. Opt-in complexity: a new player plays without understanding every system; a skilled player plays differently because they read the situation better. Traits and abilities never outrank positioning: a player with weak cards who reads the layer system beats a player with strong cards who does not, and layer position weighs more than any ability or passive. Strategic depth means a player with better understanding of the landscape, of unit formation, of the layers, of where the other player is, and of which unit types beat which can defeat a much larger force. What decides an engagement is how many units on each side can get shots off, and for how long: skill is arranging that count in your favour, and the result follows it. No one kind of understanding is enough. Each is worth what the situation makes it worth, they combine when used together, each has an answer on most maps (refusing the fight is one), and together, in the best situations, they beat a much larger force; about three times the numbers is a rough size to aim at, not a pass mark. The rules are tuned until this is true.
5. **Game-theoretic depth.** Decisions have counters, counters have counters, and none is dominant. Soft rock-paper-scissors, never hard.
6. **Positional thinking over command shortcuts.** Any feature that lets the player issue an order without thinking about where their units are is excluded, at every difficulty. There is no all-army command. Control-group exclusive membership is the canonical instance. Accessibility comes from parity tuning, opponent behavior at low difficulty, and opt-in assistive toggles labeled as such, never from flattening space. The economy's controls (the dial, the doctrine and the unit-mix switches) are not orders to units and are outside this principle (Westley, 2026-10-07).
7. **Bible describes now.** Rewrite, never append.

## The Player's Toolkit

The player receives a variable set of assets per mission, shaped by simulation state, tech level, and mission type. Forces are the core; non-combat assets (convoys, evacuees) sit outside the combat triangle and must be protected. Which other asset categories ship is open (`Q-129-01`).

Units feel real but are not deep characters. They have names. Losing one stings, especially a heavy Siege unit, but attachment is to the mission and the civilization, not to individuals.

The commander does not administer an economy or build a base. The civilization allocates a starting force by mission type and its own state: about a fifth of what a full mission can field. The rest, up to and beyond the whole, is made by production that the economy pays for, in the base, in expansions and forward works, and in strongpoints held at the slopes between height bands on land maps (`E-22` S-170, S-175, `E-15`). A side that keeps its production and its economy running ends with more than it started with, and one that loses them fights with a fifth. A thriving civilization gives a well-equipped force. A declining one gives scraps. The gap is where the drama lives.

A real economy stands behind every battle (`E-22`). Every side has a base of operations it must protect, with literal workers, three resources, buildings, production and technology. In the core single-commander game rules run it for the player, and run it well, and the base is a spectacle that builds itself while the fight goes on. In the optional paired mode, in teams of 2 or 4 (teams of 6 are a desired future feature), a second player runs it: he gathers, builds, defends, chooses technology and makes the units the commander receives, so the two have to talk. Each pair is a sub-civilization with its own economy, and each player a sub-commander, a pair reading as a cohesive faction inside the team's civilization (`E-19` S-241). Alone, the commander has one dial for the balance between economy, technology and army, can change the doctrine the rules follow, asks for things by pointing at the map (from the map view too), can override the unit mix the rules pick and switch that behaviour off, and chooses whether the enemy's economy, which runs on the same rules, also scouts, counters and disguises.

Onboarding asks two things before the first chapter, difficulty and mission-type preferences, and both can be changed later. The economy choices of a mission, the starting doctrine and the unit-mix behaviours, are the player's to make, and the enemy economy's foresight is set by the difficulty; where is open (`Q-233-01`). Progression unlocks are era unlocks and, after launch, trait cards (E-11 S-083); there is no player level.

## Tone and Feel

**Elegiac, not grim.** The game is about civilizations rising and falling over vast timescales. The tone is that of a real history being recorded. There is tragedy, and there is humor, beauty, and unexpected hope.

**The humor.** Dry, earned, occasionally absurd. It lives in the writing, not in the events. The game winks; it does not mug.

**The weight of time.** The player played the chapter that caused this. They remember the commander who failed, and now they live with the consequences as someone new.

### The five feelings

Every mechanic should serve at least one of these, which follow the lifecycle of the faction the player currently serves:

1. Pioneer survival (young faction): scrappy, resource-scarce, every mission matters.
2. Strategic depth (established): real military, real logistics, real enemies.
3. Imperial weight (overextended): too much territory, not enough resources.
4. Elegiac decline (declining): watching an institution die from inside while saving what you can.
5. Survival and identity (born from collapse): a new faction finding its footing in the wreckage.

### Design heuristics

Uncertainty genuine, never faked. Control influences, never dictates. Loss dramatic, never punishing. Humor dry, earned, never forced. Complexity: accessible floor, deep ceiling. Pacing: the world is always in motion; static is broken. Mastery means understanding why you lost, not always winning.

### Litmus tests

Commander or god? Chronicle material? Era-agnostic? Is losing interesting? Does the world keep going without the player? If any answer is wrong, redesign.

## What's Unique

1. A genuinely stochastic simulation underneath a strategy game.
2. A generational chapter structure: a series of people inside a civilization that changes around you.
3. Commander, not king.
4. Missions and narrative generated from an offline library, unique to every playthrough.
5. The tragedy of understanding: mastery is knowing why you lost.
6. A 2.5D layer and vision system that pushes positional skill past the genre's bar.
7. Multi-era matches on one skeleton.
8. A real economy behind every battle, run by rules or by a partner, on a world drawn at continuous detail from a single unit to the battlefield, with a base that builds itself.

## Monetization

Steam, one base SKU at $15, which buys 3 to 5 eras to start. The first build starts with two eras, one in space and one on land. Each new era is $3 to $5; some are earnable through play, some are purchase-only. No subscription, no in-game store, no Workshop at launch. The launch eras' units and rules are the same within an era kind; between space and ground the vision model, the ping and the vision units differ (E-01), and landscape, visuals, art, names, and prose differ. Eras that feel different come through per-era fog, pace, and the pace of production (E-20 S-151), with each era's values taken from a distinct region of settings where the simulation lab finds strategic depth holds: the lab looks for several crossings, not one.

## Reference Hardware

Every scale and frame-rate requirement in the epics is defined for the **minimum-spec machine**, never for the development machine: GeForce GTX 1070 (or equivalent), a Ryzen 5 1600 / Core i5-7600 class CPU, 16 GB RAM, a SATA SSD, at 1920×1080. "60 fps" means 60 fps on that machine. The development machine (the forge: Ryzen 7 3700X, RTX 3060) is faster, so a measurement taken there must clear the budget with margin: GPU frame-rate gates by ×1.85 (60 fps on the 1070 is about 110 fps on the 3060), CPU per-tick and latency budgets by ×1.35 (single-thread speed ratio), disk budgets unchanged (SATA SSD on both). The scale suite (`tests/csim/scale/`) applies the CPU factor through `OM_SCALE_CPU_FACTOR`; a run on an actual minimum-spec machine sets it to 1.0. Westley owns these numbers; they are never loosened by a worker, and a miss is escalated.

**Long-term goal: huge scale.** Westley, 2026-10-01: "I'd really like to take advantage of the massive computing power computers these days have access to, make units/visuals really efficient, and just make the game super busy/huge scale." The long-term target is battles and economies of thousands of units and workers on one map, a busy screen at every zoom, reached by making the simulation and the visuals efficient, not by raising the hardware floor. This is a direction, not a budget: the scale requirements in the epics stay as written until Westley changes them, and new systems are designed so they do not stand in the way of it (E-11, E-16, E-18, E-22). The client's budgets stop at 1,000 units while the simulation's run to 10,000, and the client's budgets for thousands stay a direction until the simulation's budgets are reached (Westley, 2026-10-06).

## The Systems

Each is an epic file under `epics/`. Sim core: E-02 region fields and drift, E-03 world generation, E-04 events and chains, E-05 faction agents and conflict, E-06 diplomacy and technology, E-07 civilizational lifecycle, E-08 generational structure, E-09 chronicle, E-10 missions. Tactical: E-01 layer system, E-11 units and combat, E-12 fog and sensors, E-13 movement and command, E-14 enemy macro behavior, E-15 reinforcement, strongpoints and hazards, E-17 map generation (including S-166, settlements that build themselves and landscape with real height), E-22 economy and bases. Client and cross-cutting: E-16 camera, HUD, world view, and screens; E-18 visual style and combat visuals; E-19 multiplayer (including S-159, the paired mode); E-20 multi-era and monetization; E-21 offline AI pipeline. The retained equations are in `algorithms.md`.

## Document Maintenance

1. The bible (hub, catalog, epics, references, algorithms) is the single source of truth. Conflicts elsewhere lose.
2. Rewrite, never append. No "in flux," no "pivot," no "as of" callouts. History lives in `docs/bible_history/` and `git log`.
3. Conceptual, with concrete numbers. Rules carry the values a test needs; they never carry file paths, function signatures, or data shapes. Those belong in `docs/architecture.md`. Player-facing behavior is written as what the player perceives and what it tells them, not as layout.
4. Every story enters `stories.md` first. Every rule maps to at least one test. Every question becomes a flag in the register, never a guess.
5. A change runs the change protocol in `docs/northstar/agile.md`: story rewritten, catalog updated, tests revised, Agora task respec'd, rules file regenerated, one PR.

How the game gets built is not in this file. See `docs/northstar/README.md`.
