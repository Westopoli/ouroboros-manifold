# Paired economy multiplayer mode: perception brief

## 1. Feature and status

E-19 S-159 R-159-01 (`docs/bible/epics/E-19-multiplayer.md:104-114`), deferred, no rule at launch. Open flags Q-159-01 (economy role design, `docs/northstar/ambiguity_register.md:148`) and Q-159-03 (which pieces the player builds, `:159`). Hub pointer at `docs/bible/game_bible.md:89`. The landscape design phase (2026-09-21) made the city the tactical battlefield and named the city system the "sister" of the landscape generator. The self-running city that exists when nobody manages it has its own brief in `../city-spectacle/`.

## 2. Player-facing goal as documented

"As a commander, I may someday want to watch a real city grow behind my war, built for me when I fight alone and built with me by a partner when I choose to, so that the civilization feels alive and its growth is something I want to watch, not just a number." (`E-19:106`)

R-159-01: "an optional multiplayer mode, separate from the core commander game, where players queue in pairs and teams of 2, 4, or 6 form from one or more pairs; within a pair, one player commands the pair's military force using the existing tactical and layer system, and the other manages the pair's economy (production, resources, construction, base layout); the economy role's target system complexity is roughly two to three times a proficient StarCraft 2 economy's, so that mastering it demands as much depth as the military role. Building placement, base customization, and construction detail are a major point of this mode: the target is a strong sense of scale, building cities larger and more complex than Age of Empires Online's, not a thin resource-tick abstraction. Exact economy mechanics are unspecified; the reference games (StarCraft 2 for supply and production pressure, Age of Empires 2 and Age of Empires Online for multi-resource gathering and city building) are starting points for research, not a design. This mode does not change the core single-commander game (hub "The Player's Toolkit": no economy, no base building); it is an additional mode that sits beside it." (`E-19:109`)

## 3. Westley's own words

Q-159-01 framing (`ambiguity_register.md:148`): "Westley wants the economy role's system complexity at roughly two to three times a proficient StarCraft 2 economy's, with building placement, city customization, and construction detail a major point (bigger, deeper city-building than Age of Empires Online), and no other constraint on mechanism."

Commit 7bdca88: "Westley corrected: economy role target is 2-3x StarCraft 2 system complexity, not workload/APM."

Landscape answer 4, 2026-09-21 (`docs/northstar/research/landscape_design/README.md:14`): "4: Oh yes, a: cities will be like your homebase long term, something you'll need to protect. Every "fight" at the moment is happening at a city in a civilization, the economy/buildings will be the city itself. I'd like it to be expansive, huge scale, three reference photos (save these) [...] - this will be the economic aspect, but the player doesn't build everything, just pieces (to be designed), the biome generation system and the "population density/city layout" system are very similar in what they map out, just different visuals really, we need the "generation" system to map out "borders" and gradiants, to be used by both systems: hence the "sister" term."

D3, 2026-09-19 (`docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md:107`): "I want a hand in designing the biome/landscape generation system (which the economy/buildings/(civilzations cities) system will use as well as like a "sister" system (because they're very similar) before we start building".

Vision v2 Q3 (`docs/legacy/agora_era/vision_v2.md:39`): "Yes commander not king, given a task force big or small, civ has it's own plans, meant to emulate reality."

## 4. Fixed constraints any option must honor

- The core single-commander game has no economy and no base building; this mode sits beside it (`game_bible.md:87`; `E-19:109`).
- Pairs; teams of 2, 4, or 6 from pairs; one player military, one economy (R-159-01).
- The player builds pieces, not everything; the rest rises from the region economy through the city mapper (Q-159-03; `references/E-17/notes.md:22` "Not wanted: Player-built everything").
- The city and the landscape come from one generator and one placement engine; the city mapper reads population, wealth, and age from the region state (`landscape_design/README.md:26-30`).
- The city is the battlefield and the pair's long-term home base (`landscape_design/README.md:32`).
- Lockstep determinism applies to every mode; 4 peers, 200 ms (`E-19:31-36,140`). No pause in a match (R-142-01).
- The military half keeps Principle 6 (no all-army command) and the layer system.
- The era-agnostic rule: the city's pieces come from the era pack.
- The match shape (co-op in one civilization, opposing civilizations, player count) is itself open (Q-141-01, Q-141-02).
- No IP.

## 5. Prior art already named

StarCraft 2 (supply and production pressure), Age of Empires 2 and Age of Empires Online (multi-resource gathering, city building, playful bright register). Three macro-city concept images in `docs/bible/references/E-17/` (rows 05 to 07 in `notes.md`).

## 6. Contradictions, as questions for Westley

1. Q-159-01 asks for 2 to 3 times StarCraft 2 system complexity with placement and construction as a major point; Q-159-03 says the player builds only pieces. Does the paired economy player build everything (or nearly), while the solo commander's city builds itself with pieces the commander can place?
2. "Cities will be like your homebase long term, something you'll need to protect" and the hub's "no base to build". Confirm the distinction: the city exists and is defended in every mode, and only in the paired mode does a human administer it.
3. Is the economy role played on the same tactical map at the same time as the battle (the city being the battlefield), or on its own view of the same city?
4. Between missions, does the economy player's work persist through the time jump like the region's economy does?

## 7. Proposed option width

Three options, two wild. Each option describes the economy player's session: what they look at, what decisions they make in a minute and in a mission, how their work becomes the commander's units, positions, and walls, and how the pair talks.

## 8. Westley confirms

Batch 2, 2026-09-22, verbatim: "not just pieces, we want to design a mechanism that requires the users to think (like sc2's economy) and juggle tasks (sc2 had supply, multiple resources, tech timings, consistent worker production, a lot of different variables). (we could do another optional mode where players can share military/economic responsibilities). Yes the city builds/runs itself when the player doesn't have the economic mode enabled. same tactical map for both. Yes it will persist, but we don't want the complexity to build forever, we'll need to design a "reset" method that keeps the load from increasing to the point of unreasonableness for the player. One idea is to have "upgrades" that automate tasks and or allow them to focus on other tasks that reap more rewards."

Folded into the brief:

- Depth (question 1): the economy player runs a full economy that demands thought and task juggling, in the register of StarCraft 2's supply, multiple resources, tech timings, and steady worker production. "Pieces only" describes the solo commander, not this role.
- A further optional mode may let both players share military and economic responsibilities. Options may include it.
- Question 2: confirmed. The city builds and runs itself when the economic mode is not enabled. Confirmed 2026-09-22, verbatim: "economic mode: paired queue only, when they start the "universe" they lock in to the configuration they defined at the start. They can't play it without the same number of players, in the same number of slots, with the same eras. Otherwise they'll have to start a new universe." The economic mode exists only through the paired queue, and a universe (a multiplayer campaign) locks its configuration at creation.
- Question 3: same tactical map for both players.
- Question 4: the economy persists through time jumps, and its complexity must not grow without bound. A reset or load-capping mechanism is required; one idea is upgrades that automate earlier tasks so the player moves on to higher-reward ones. Options must say how load stays reasonable over a campaign.
- Roster context: the bible now targets 20 to 40 unit types per era (Q-082-02), so production choices are wide.

## 9. Sub-agent brief

Follow the common template in `../README.md` ("Sub-agent template"). Sections 4 and 8 of this file are the constraints; where they disagree, section 8 wins.

- Options: 3, of which 2 wild.
- A full economy that demands thought and task juggling in the StarCraft 2 register (supply, several resources, tech timings, steady worker production), on the same tactical map as the battle.
- The economy persists through time jumps and must not grow without bound: each option includes its reset or load-capping mechanism (one idea: upgrades that automate earlier tasks).
- The economic role exists only in the paired queue; a universe locks its player count, slots, and eras at creation and can only continue with the same. When nobody holds the role, the city runs itself. An optional shared mode where both players do both is welcome.
- How the economy player's work becomes the commander's units, walls, and positions, and how the pair talks.

## 10. Decision (2026-09-23)

Westley, verbatim: "For paired economy multiplayer mode, the works is good but it's not unique. The Two clocks is a cool idea, but it needs to be more concrete, a phased system of actions is too broad, I'd like a second pass on this idea with more concrete examples of player actions (like the works, specific). Same for The Commons, it could be good but it's too broad, we don't have to literally define what the players would do, but managing "emotions" isn't what I had in mind for managing the economy. I'd like their task to be building mostly, and designing efficient pathways/systems. Let's explore more options in that direction during a second pass on these ideas."

Recorded as: None yet. The Works is good but not unique; the Two Clocks needs concrete player actions; the Commons is too broad and not about emotions. Second pass: building and designing efficient pathways and systems as the economy player's task.
