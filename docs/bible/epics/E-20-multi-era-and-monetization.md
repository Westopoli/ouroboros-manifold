# E-20 — Multi-Era Skeleton, Era Packs, and Monetization

## Definition-completeness gate (run 2026-09-10)

| Check | Result |
|---|---|
| Every story has at least one Given/When/Then rule with concrete values | Partly. 8 stories, 28 rules; the architecture rules are concrete, the pricing, era-transition and unlock rules carry flags. |
| Every input listed with range and rejection behavior | Yes, see Inputs. |
| Every output listed with where it is observable | Yes, see Outputs. |
| Implied-but-unstated behavior turned into flags | 9 open flags: Q-146-02, Q-147-01, Q-147-02, Q-148-04, Q-148-05, Q-149-01, Q-149-02, Q-150-01, Q-151-02. |
| Every visible-surface story has a reference | Not applicable in this epic; era looks are E-18. |
| "Obviously working" in 60 seconds named | Yes, see below. |

**Gate verdict: not passed.** Blocked on open flags. Launch has two eras, one in space and one on land (S-147), and the base SKU's price buys 3 to 5 eras to start (S-149). The era-feel mechanism is chosen (the Climate of War, S-151, with its values found by the simulation lab); the transition trigger is chosen (the Long Horizon) with its measure open (Q-148-05); the land era's final name and brief (Q-147-01, the Greek placeholder stands in today) and the roster size per era (Q-082-05) still need Westley.

## Purpose

The engine is a skeleton that never names an era. Eras are packs: names, art, prose, unit models by tier, building pieces and environment assets, landforms and environmental troubles, resource names, doctrines, naming pools, chronicle and briefing fragments, and per-era config values the engine consumes uniformly. Maps, era systems, and civilizations are built as transferable systems, Fortnite-skin style, so any map, any skin, any civilization works in any era. The base SKU on Steam costs $15 and buys 3 to 5 eras to start, and the first build starts with two eras, one in space and one on land; each new era costs $3 to $5, some earnable through play and some exclusive. Era unlocks are the one progression unlock at launch. A campaign can move chronologically through eras the player owns.

At launch the two eras' units and rules are the same within an era kind; between space and ground the vision model, the ping and the vision units differ (E-01 S-005, S-162; Westley, 2026-10-02 and 2026-10-05), and the landscape and visuals differ. Differentiation of feel is the Climate of War (S-151): per-era fog thickness, engagement pace, and reinforcement rate. Its values are not invented per era; the simulation lab searches for every region of settings where strategic depth holds (the "lines cross" in more than one place, `docs/northstar/research/layer_dynamics/README.md` section 2), and each such region is a candidate feel for an era (Westley, 2026-10-15).

## Obviously working in 60 seconds

Load the Settled Reach: a mission generates, forces spawn as sci-fi ships at Tier 2. Switch the era pack to the land era: the same seed produces the same map seed, the same unit roster with the same stats, the same objectives, on that era's landscape, drawn as that era's models, named from that era's pools, briefed in that era's prose. Grep the engine for any era name: zero hits.

## Stories

### S-145 — The engine never says "starship"
As an era designer, I want the engine to speak only in abstract terms, so that a new era is content and never code.

Rules
- R-145-01  Given the engine's source and config, When searched, Then no identifier names an era, setting, or theme (region not star system, heavy combat unit not battleship, military strength not fleet power).
- R-145-02  Given per-era variation, When implemented, Then it is a config value the engine reads uniformly; no `if era ==` branch exists anywhere.
- R-145-03  Given the bible, When engine sections are read, Then theme terms appear only in Vision and Identity and in era pack descriptions.
- R-145-04  Given a new era pack, When installed, Then the game runs it with zero engine changes; a contract test loads every shipped pack against the same engine build.

Inputs: source; packs.
Outputs: grep and contract test results.
Open flags: none.

### S-146 — What an era pack is
Flag closed, rule text pending: Q-146-01, the three launch packs carry byte-identical mechanical config for the MVP; the content diff fence asserts it and is written swappable to a within-band check for later eras. The rule below is what the tests read today.
As an era designer, I want a checklist of exactly what a pack contains, so that every era is complete and nothing else.

Direction changed 2026-10-02, rewrite pending: a pack also carries what the economy and the landscape need (S-243), the structures of a pack are no longer a fixed 3 to 6 (E-18 R-133-05, Q-133-01), the reinforcement constants become the pace of production (S-151, Q-151-02), and the launch has two eras where R-146-02 says three (S-147). The rules below are what the game does today.

Rules
- R-146-01  Given an era pack, When validated, Then it contains: identity (name, spatial scale, tone), three tier definitions, one unit model per roster type per tier and per-type silhouette conformance (E-18 S-132), 3 to 6 tiered structures, 5 to 10 environment objects, the ability visual mappings for every ability in the roster, attack visual categories per type, era-specific naming pools, era-specific chronicle and briefing fragments, a strategic view definition, and the per-era config values (unit stat profile per tier, restriction mask or none, elevation flag, reinforcement constants, fog constants).
- R-146-02  Given the launch constraint (A-321), When per-era config values are set for the launch eras, Then they are identical within an era kind except art, names and prose, and between the space era and the ground era they differ only in what the kind decides: the vision model, the ping, the vision units and the landscape (E-01; Westley, 2026-10-05: "no longer byte identical, superceded") [Q-146-01 superseded; Q-146-04: whether the era kind is a pack field].
- R-146-03  Given a pack, When any required entry is missing, Then the pack fails to load with the entry named; a missing optional asset uses the placeholder.
- R-146-04  Given the Era Creation Template (six layers), When a new era is designed, Then it follows those layers in order and stays within the fixed engine abstractions (three categories on a fixed rock-paper-scissors, a 20 to 40 type roster per era [Q-082-05], spine plus five gradients, abstract structure types, three tiers at 0/34/67, three resources, E-22 S-167, and the building kinds of E-22 S-168).

Inputs: pack manifest.
Outputs: validation report; loaded pack.
Open flags: Q-146-02 (whether resource names, doctrine names and environmental troubles are names or mechanics).

### S-147 — Two eras, one skeleton
As a player, I want an era in space and an era on land to play, all one game, so that the smallest version I buy already spans two ages.

Rules
- R-147-01  Given the first build, When eras are listed, Then it contains exactly two, one in space and one on land, each with an era kind, with units and rules the same within a kind and the vision model, ping, vision units, landscape and visuals different between them (Westley, 2026-10-02 and 2026-10-05), chronologically ordered. The Settled Reach is the space era (`assets/eras/settled_reach/`). The land era is Greek antiquity, shipped today as the placeholder pack `assets/eras/greek_placeholder/` ("The Marble Reach", kind ground, era order 1, the six roster types walking, placeholder tone and scale) and reached in the game by the era toggle [Q-147-01: its final name, setting brief and tone, and the ordered roster of eras after the first two].
- R-147-02  Given any era, When a mission runs, Then the map generator, mission generator, agents, events, combat, and chronicle are the same code with the era's pack loaded.
- R-147-03  Given the same seed in two eras, When maps are generated, Then the map seeds are identical and the landscape and the rendering differ, since the land and space landscape systems are sisters with different objects (E-17 S-166; the space system is Q-166-02) [Q-147-02: whether eras share map seeds or eras may weight layouts differently].

Inputs: pack set.
Outputs: era list; contract tests.
Open flags: Q-147-01, Q-147-02.

### S-148 — Moving through eras
As a player, I want a campaign to move chronologically through the eras I own, so that a bloodline can span the ages.

Rules
- R-148-01  Given a campaign in era k and the player owns era k + 1, When the leading civilization's reach for its age tops out, after the chronicle has spent several chapters naming that age being outgrown (the Long Horizon), Then the next time jump lands in era k + 1 with the same galaxy, the same factions, and the same ledger [Q-148-05: the reach measure and its ceiling per age].
- R-148-02  Given the era transition, When the world carries over, Then region fields, ownership, edges, and characters persist and tech is rescaled so that no faction arrives at late game and the leading faction still leads; only the pack changes; the chronicle frames the transition, and characters from earlier eras fade into distant myths with fewer mentions the farther the timeline moves from them.
- R-148-03  Given the last owned era, When the next time jump comes, Then history loops: the jump lands in the first owned era with the same galaxy, the same factions, and the same ledger, in solo campaigns and in matches alike [Q-148-04: what the loop does to tech, characters, and the chronicle, and how it relates to the deferred Ouroboros restart, S-054].
- R-148-04  Given a multiplayer match, When eras traverse, Then E-19 S-143 applies.

Inputs: ownership; campaign state.
Outputs: era in the save; chronicle entry.
Open flags: Q-148-04 (the loop's effect on tech, characters, and the chronicle), Q-148-05 (the reach measure behind the Long Horizon).

### S-149 — Buying and earning eras
As a player, I want a fair price and the chance to earn expansions by playing, so that the game respects my time and my wallet.

Rules
- R-149-01  Given Steam, When the base game is listed, Then it is one SKU at $15 that buys 3 to 5 eras to start, and the first build starts with two eras, one in space and one on land (S-147); no subscription, no in-game store, no Workshop at launch.
- R-149-02  Given a new era, When listed, Then it is $3 to $5.
- R-149-03  Given an earnable era, When its condition is met in play, Then it unlocks without purchase [Q-149-01: the condition, proposed: complete a campaign of 10 chapters in the preceding era].
- R-149-04  Given an exclusive era, When read, Then it is purchase-only and marked so on the store page; the launch plan names which eras are which [Q-149-02].
- R-149-05  Given the unlock system, When read, Then era unlocks are the only unlock type at launch; no player level, no unit unlocks (E-08 R-064-03).

Inputs: store; play state.
Outputs: ownership; store listing.
Open flags: Q-149-01, Q-149-02.

### S-150 — Systems, not components
As an era designer, I want maps, civilizations, and era systems to transfer between eras like skins, so that content compounds instead of forking.

Rules
- R-150-01  Given a layout in the library, When used, Then it is valid in every era with no era tag [Q-150-02: which parts of map generation stay era-agnostic now that the land and space landscapes are sister systems with different objects, E-17 S-166, Q-166-02].
- R-150-02  Given a civilization (archetype weights, naming subset, colors), When used, Then it is valid in every era.
- R-150-03  Given a skin (unit model set), When applied, Then it maps to the six abstract types and three tiers, and to the worker, a unit that cannot fight (E-15 S-129, E-22 S-167), and nothing else.
- R-150-04  Given the settlement generator (E-17 S-166), When it builds, Then the generator is era-agnostic and the building pieces are era-specific (S-243).

Inputs: content libraries.
Outputs: cross-era validity tests.
Open flags: Q-150-01 (what "civilization" content transfers across eras beyond archetypes and names; the Fortnite analogy names skins, dances, maps, and Westley extends it to civilizations).

### S-151 — Eras that feel different
As a player, I want the ancient era to be scout-blind and the future era all-seeing, so that time changes how war feels.

Not deferred (Westley, 2026-10-15: the whole point of the simulation lab is to find multiple points where the lines cross, not one configuration). The lab's search is the source of the values; the story is scheduled when the lab has described more than one crossing.

Rules
- R-151-01  Given an era pack, When loaded, Then the difference between eras is the Climate of War: each era sets its own fog thickness, engagement pace, and reinforcement rate (the pace of production, E-22 S-170, and of strongpoint reinforcement, E-15) as manifest values the engine consumes uniformly [Q-151-02: which economy values an era may set]; units, categories, and counters never change with the era. Chosen through the options pass, `docs/northstar/research/options/era-feel/`, Q-151-01.
- R-151-02  Given the simulation lab's search over the game's settings (`docs/northstar/research/layer_dynamics/README.md`), When it reports, Then it describes every region where the depth conditions hold, not the first found, and each region is recorded as a candidate Climate of War for an era; an era's values are chosen from a reported region, never set by hand outside one.
- R-151-03  Given the planned eras, When one is briefed, Then it follows the Era Creation Template (R-146-04). The brainstorm list of twenty eras is `docs/blender_stuff/3d_model_outline_all_eras.md` (2026-09-11; Settled Reach, Medieval, Roman, Age of Sail, Feudal Japan, World War II, Viking, Cyberpunk, Ancient Egypt, Mongol Steppe, Colonial Mars, Bronze Age Collapse, Napoleonic, Mesoamerican, Cold War, Silk Road, Interwar, Post-Apocalyptic, Polynesian, Renaissance Italy); Westley's spoken list adds Greek (the land era as built), World War I, the 2020s and Imperial China "and many more" (2026-10-15). The ordered, named roster is his and is open under Q-147-01; the list is not a decision.

Inputs: lab reports (crossing regions); the era roster.
Outputs: per-era Climate of War values in the manifest.
Open flags: Q-151-02; Q-147-01 (the era roster).

### S-243 — What an era pack carries for the economy
As an era designer, I want the checklist to name everything the economy and the landscape need from a pack, so that an era is complete and nothing else.

Design decided 2026-10-02, not scheduled for building (E-22, E-17 S-166). This adds to S-146's list and does not replace it.

Rules
- R-243-01  Given an era pack, When validated, Then beyond the entries of S-146 it contains: the building pieces that settlements are built from, with their stages of construction (E-18 S-237); the names of the three resources (E-22 S-167); the mapping from each unit category (Strike, Line, Siege) to the resources it needs (E-22 S-171) [Q-159-08: what the three resources are and which category needs which]; the doctrines the rules can follow [Q-243-01: whether a doctrine's name, description and parameters are pack content or engine config]; the landforms of the era's landscape (E-17 R-166-03); the environmental troubles of its regions (E-15); the worker's model and animation (E-22 S-167); and, for each unit type, whether it walks or flies (E-01 R-001-07).
- R-243-02  Given the space era, When the pack is validated, Then its landform and environmental-trouble entries wait for the space landscape to be designed (Q-166-02); no rule is written for them yet.
- R-243-03  Given the economy entries of two packs, When compared, Then [Q-146-02: which of resource names, doctrine names and environmental troubles count as names, which may differ, and which as mechanics, which may not].

Inputs: pack manifest.
Outputs: validation report.
Open flags: Q-159-08, Q-146-02.

## Inputs

| Input | Source | Range | Rejection |
|---|---|---|---|
| Era pack manifest | Content | as S-146 | missing required entry fails load |
| Ownership | Steam | set of era ids | |
| Campaign era state | Save | era id, order | unknown era refuses load |

## Outputs

| Output | Observable where |
|---|---|
| Loaded pack, validation report | Log; contract tests |
| Era in campaign state | Save; briefing; chronicle |
| Store listing and unlocks | Steam; profile |

## Invariants

- Zero era names in engine source.
- Every pack passes the same contract test.
- The two launch eras' units and rules are the same within an era kind (A-321, Westley 2026-10-02 and 2026-10-05); between kinds the vision model, the ping, the vision units, the landscape and the visuals differ, plus art, names and prose [Q-082-05: whether per-era rosters keep unit profiles identical across the launch packs; Q-146-02].

## Scale requirements

Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): pack load under 2 s; era switch in a campaign under 5 s.

## Look and behavior references

Not applicable; see E-18 per era.

## Ways this could be wrong

- An era-specific constant slips into the engine as a default.
- A pack ships with a mechanical difference and passes because the contract test does not diff config across packs.
- Era transition resets the ledger or the world.
- Earnable eras gated behind a purchase in the store metadata.

## Open ambiguity flags

Q-146-02, Q-147-01, Q-147-02, Q-148-04, Q-148-05, Q-149-01, Q-149-02, Q-150-01, Q-151-02. Details in `docs/northstar/ambiguity_register.md`.

## Depends on

- E-08 (time jumps, unlocks), E-11 (per-tier profiles), E-17 (layouts, S-166 landscape and settlements), E-18 (looks), E-19 (cross-era matches), E-21 (pack content generation), E-22 (resources, doctrines, workers), E-15 (environmental troubles), E-01 (movement kind per unit type).
