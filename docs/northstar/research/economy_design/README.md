# Economy design track

Opened 2026-10-01. Brings the economy (E-19 S-159 and what it touches in E-02, E-10, E-15, E-17) to a level of detail that can be implemented. Design only; the mission-plays plan keeps paired economy parked for building. Nothing here is bible text until a decision is folded into an epic through the Design Lane.

Earlier material: `../options/paired-economy/`, `../options/city-spectacle/` (first options pass, 2026-09-22/23, no pick on either), `../landscape_design/README.md` (the sister generator).

## Goals, in working order

One economy, two drivers: rules when nobody holds the economy seat, a human when someone does.

| # | Goal | Depends on | Status |
|---|---|---|---|
| 1 | Resources and how they become units | (check against 5's verbs before freezing) | foundation decided 2026-10-01 (`current_system.md`); open: the three resources' identities and which unit roles need which |
| 2 | Bases of operations and how they play into objectives | 1 | partly decided (base of operations, resources opposite the objective, expansions, forward bases); the loss condition and mission-type mapping are open |
| 3 | Groundwork for auto-generating economic buildings (sister to biome generation) | 1, 2 | not started |
| 4 | How the economy runs when the player opts out | 1, 2, 3 | not started |
| 5 | How the economy player literally manages the economy | 1 to 4 | foundation decided 2026-10-01 (`current_system.md`); details open |

## Decisions (2026-10-01)

Each row is the sentence Westley was answering and his answer, verbatim.

| Flag | Sentence answered | Westley, verbatim | Recorded as |
|---|---|---|---|
| Q-159-05 | "Depth: 2–3x SC2 *system complexity* (not APM): supply, several resources, tech timings, worker production." | "On "Depth = Not APM", I would like APM to give a small benefit to the player, not nothing. Maybe like 1.1 or 1.2x better if you're faster." | Decided. Speed of hand gives the economy player a small, bounded edge, on the order of 1.1x to 1.2x, never nothing and never the main source of advantage. System complexity stays the depth target. The exact bound and what it multiplies are set when goal 5 is designed. |
| Q-159-06 | "Bases: Every side has a city: defender's home, attacker's forward base. City dies = battle over, no reinforcement or replenishment." | ""Every side has a city" not necessarily, but every side does have some sort of "base of operations" they need to protect, either recieving resources from someplace else or generating them on site (depends on the simulation and specific mission)." | Decided. Every side has a base of operations it must protect. It is not always a city. It either receives resources from elsewhere or generates them on site; which one depends on the simulation and the mission. This amends the 2026-09-22 answer in `../options/city-spectacle/brief.md` section 8 ("Every side has a city"). |
| Q-159-07 | "Persistence: Economy persists through time jumps. Damage persists on short jumps; rebuild speed follows civ economy." | ""Economy persists through time jumps", this might be hard to do in the context of the simulation. I'm not so sure about it anymore, it'd be nice, but what would be really nice is giving the player something they get to carry forward, like abilities or something. This is to be explored, but I think it'd be hard to justify "crazy good economy on the 15th mission together" when the simulation is picking a small mission on a planet with very limited resources and a small force. Whatever we choose needs to consolidate with the other parts of the game." | Open. The 2026-09-22 answer that the economy persists through time jumps (`../options/paired-economy/brief.md` section 8) is withdrawn as a fixed constraint. What carries forward between missions is to be explored; one idea is abilities. Whatever is chosen must fit a simulation that can pick a small mission on a poor planet with a small force, and must consolidate with the rest of the game. |

## Decisions (2026-10-01, later the same day)

Westley, verbatim, answering the four variations in `f_variations.md`:

"I like the contested populace idea, but that's not the economic players job, let's make sure that economic locations are placed throughout the map, and significant resources are placed opposite of the objective, so players are forced to either pick one or fight for both. - For the economic player, let's do 3 resources, and let's make them need to build buildings and manage something like pop count or some variation of it, but we need to find out options for what they can actually *do* like the actions they take, and it needs to be skill based just like playing. Despite the ideas, I still feel like we don't have a clear picture of what the economy can look like. Let's research how other games have made building/managing economies fast-paced or exciting. We want to make it skill based like the combat without making it feel like busy-work, maybe we could invent a "game" of sorts like chess that's to be played within the economic system, that requires thinking ahead like the military combat aspect. Let's dig deeper on that idea, research and come back with many surface level options, nothing too in depth but many different directions."

Recorded as:

- Decided: the contested populace is liked, and winning it is not the economy player's job.
- Decided (map placement, feeds goals 2 and 3): economic locations are placed throughout the map, and significant resources are placed opposite the objective, so a side must pick one or fight for both.
- Decided (economy seat): three resources; the economy player builds buildings and manages a population count or some variation of it.
- Open: what the economy player actually does, action by action. It must be skill-based like combat, need thinking ahead, and not be busy-work. One direction to explore is an invented game, in the manner of chess, played inside the economic system. Research in `prior_art_economy_gameplay.md`; many surface-level directions in `economy_game_directions.md`.

## Decisions (2026-10-01, third round)

Westley, verbatim, answering `economy_game_directions.md` and the lean stated in chat (The Stewards, Hands and The Board, with The Order Board as the link to the commander):

"What is "order board"? You didn't list that. I like your recommendation, give me a description of what a player managing this sort of economy would literally be doing/seeing. I think that also tech choice should be on the economic player, and that's where the veil can come in, tell me more about it and how we could introduce scouting/information gathering into the economy."

Recorded as:

- Liked, not yet a pick: the combination of The Stewards, Hands, The Board and The Order Board.
- Decided: technology choice belongs to the economy player.
- To explore: The Veil, and scouting and information gathering inside the economy. Sketch in `economy_seat_sketch.md`.

## Decisions (2026-10-01, fourth round)

Westley, verbatim, answering `economy_seat_sketch.md`:

"I'm not a fan of the order board, this should really be something they have in their head (like starcraft 2), not physical. In starcraft if you didn't keep an eye on your pop count, you got supply blocked and it took ~30 seconds to fix it, if you were too busy micro'ing and forgot to keep building workers or go to the next tech or keep building production, you ended up behind. That's the kind of dynamic I'm looking for in terms of skill, needing to juggle a couple different things in your mind at once. Skip the order board. - I'm not a fan of the 1 minute in the seat description, that's not really what I had in mind, let's start with something basic and build on it. Let's start with classic AOE Online/3, and include the pieces I've mentioned already, let's grab from Board on the building placement/choice, contested populace, literal workers and also economic buildings, and build on it. - Propose some options for how to build on it given the research we've done, fusions and such, give me 10-15 surface level."

Recorded as:

- Decided: no Order Board. What the commander needs is held in the economy player's head, not shown as tickets.
- Decided (the skill): juggling several things in mind at once, where forgetting one (population cap, worker production, the next technology, production buildings) puts the player behind, as in StarCraft 2.
- Decided (the baseline): classic Age of Empires Online and Age of Empires 3, with placement and building choice from The Board, the contested populace, literal workers, and economic buildings.
- Rejected: the one-minute walkthrough in `economy_seat_sketch.md`. That file's Order Board, crews and stewards are superseded; its technology, Veil and information-gathering sections still stand as material.
- Next: build-ons for the baseline in `baseline_and_buildons.md`.

## Decisions (2026-10-01, fifth round)

Westley, verbatim, answering `baseline_and_buildons.md`:

"We could make the economic player be the "production" manager for the production buildings and the units the "commanding" player recieves, that would actually be a cool dynamic because they'd need to communicate with each other. Mark it as a decision. - I like the expansions idea, but let's not let the main city run dry, just make it so that if they stay and don't expand outward for resrouces they get over-run. - I like the one cap for both, but let's make the cap upgradeable significantly, up to thousands of units/workers. (I'd really like to take advantage of the massive computing power computesr these days have access to, make units/visuals really efficient, and just make the game super busy/huge scale, mark this in the bible in the relevant section as a long term goal). - I like the drop off increase, let's do that - Shipments but they don't have vision, they're blind and if they don't show up than you have no idea what happened. - Yes to seasons/weather, let's make specific regions have specific environmental issues that can happen I love that idea record it. - This isn't enough though, this is like probably 1.2x-1.4x sc2 economy macro, the goal was 2-3x. Mark this as the current economic system, then let's reach outward to figure out how to make it more chess-like, to make them have to think ahead, maybe to pay attention to something going on on the map or see what the enemy is doing in their base. Propose some options, a couple standard, a couple wild"

Recorded as:

- Decided: the economy player is the production manager. He runs the production buildings and makes the units the commander receives; the two have to talk.
- Decided: expansions are in. The main base never runs dry; a side that stays home and does not expand for resources is overrun.
- Decided: one population cap for workers and soldiers together, upgradeable a long way, up to thousands.
- Decided, and written into the bible hub ("Reference Hardware"): huge scale is a long-term goal.
- Decided: haul distance to the drop-off matters.
- Decided: shipments are in, and they are blind. The side has no vision of a shipment on its way; if it does not arrive, nobody is told why.
- Decided: seasons and weather are in. Specific regions have specific environmental troubles.
- Westley's measure: this is about 1.2x to 1.4x a StarCraft 2 economy; the target is 2x to 3x.
- The above is the current economic system, written out in `current_system.md`.
- Next: ways to make it more like chess (thinking ahead, watching the map, reading the enemy's base), in `chess_layer_options.md`.

## Decisions (2026-10-01, sixth round)

Westley, verbatim, answering `chess_layer_options.md`:

"I like the counters/retooling, let's explore that option deeper, maybe specific unit roles need specific resources, and heavier resource collection from a specific resource indicates they're making more of that specific role and you need the counter. - I like the walls/towers/raid lanes, let's tack that on - I like the schedule, if it takes a while to change what production you're focusing on and the fact that enemies can see it, we should also givep players a way to disguise/hide their buildings. - I like the weather on the move, let's do it. - Let's also do the potential forward bases. Record all these decisions, I think we have a strong foundation for the economic system. I think we can call it a day on that design front unless I'm not remembering something"

Recorded as:

- Decided: counters and retooling (S1) is in, to be explored deeper. His direction: specific unit roles need specific resources, so heavy gathering of one resource shows which role a side is making more of, and the other side needs the counter.
- Decided: walls, towers and raid lanes (S3) are in.
- Decided: the schedule (W3) is in. Changing what production is focused on takes a while and the enemy can see it, so players also get a way to disguise or hide their buildings.
- Decided: weather on the move (W4) is in.
- Decided: forward bases (W6) are in.
- Not picked, not rejected: prizes on a clock (S2), a shared market (S4), demands from the civilization (S5), the Keystone (W1), the Contested Tree (W2), agents (W5).
- Westley's read: a strong foundation; this design front pauses here.

## Files

- `prior_art_resources.md`: cited digest of resource systems in other games.
- `resources_options.md`: goal 1 options, three regular and three wild.
- `f_variations.md`: Where People Go expanded, two close and two very different variations.
- `prior_art_economy_gameplay.md`: how other games make economy play fast, skilled and exciting.
- `economy_game_directions.md`: many surface-level directions for what the economy player does.
- `economy_seat_sketch.md`: what the economy player sees and does, technology on the seat, the Veil and information gathering.
- `baseline_and_buildons.md`: the classic baseline and fourteen build-ons.
- `current_system.md`: the current economic system, as decided so far. Read this first.
- `chess_layer_options.md`: options for making the seat more like chess.
