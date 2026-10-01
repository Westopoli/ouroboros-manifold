# Economy design track

Opened 2026-10-01. Brings the economy (E-19 S-159 and what it touches in E-02, E-10, E-15, E-17) to a level of detail that can be implemented. Design only; the mission-plays plan keeps paired economy parked for building. Nothing here is bible text until a decision is folded into an epic through the Design Lane.

Earlier material: `../options/paired-economy/`, `../options/city-spectacle/` (first options pass, 2026-09-22/23, no pick on either), `../landscape_design/README.md` (the sister generator).

## Goals, in working order

One economy, two drivers: rules when nobody holds the economy seat, a human when someone does.

| # | Goal | Depends on | Status |
|---|---|---|---|
| 1 | Resources and how they become units | (check against 5's verbs before freezing) | in progress: options in `resources_options.md` |
| 2 | Bases of operations and how they play into objectives | 1 | not started |
| 3 | Groundwork for auto-generating economic buildings (sister to biome generation) | 1, 2 | not started |
| 4 | How the economy runs when the player opts out | 1, 2, 3 | not started |
| 5 | How the economy player literally manages the economy | 1 to 4 | not started |

## Decisions (2026-10-01)

Each row is the sentence Westley was answering and his answer, verbatim.

| Flag | Sentence answered | Westley, verbatim | Recorded as |
|---|---|---|---|
| Q-159-05 | "Depth: 2–3x SC2 *system complexity* (not APM): supply, several resources, tech timings, worker production." | "On "Depth = Not APM", I would like APM to give a small benefit to the player, not nothing. Maybe like 1.1 or 1.2x better if you're faster." | Decided. Speed of hand gives the economy player a small, bounded edge, on the order of 1.1x to 1.2x, never nothing and never the main source of advantage. System complexity stays the depth target. The exact bound and what it multiplies are set when goal 5 is designed. |
| Q-159-06 | "Bases: Every side has a city: defender's home, attacker's forward base. City dies = battle over, no reinforcement or replenishment." | ""Every side has a city" not necessarily, but every side does have some sort of "base of operations" they need to protect, either recieving resources from someplace else or generating them on site (depends on the simulation and specific mission)." | Decided. Every side has a base of operations it must protect. It is not always a city. It either receives resources from elsewhere or generates them on site; which one depends on the simulation and the mission. This amends the 2026-09-22 answer in `../options/city-spectacle/brief.md` section 8 ("Every side has a city"). |
| Q-159-07 | "Persistence: Economy persists through time jumps. Damage persists on short jumps; rebuild speed follows civ economy." | ""Economy persists through time jumps", this might be hard to do in the context of the simulation. I'm not so sure about it anymore, it'd be nice, but what would be really nice is giving the player something they get to carry forward, like abilities or something. This is to be explored, but I think it'd be hard to justify "crazy good economy on the 15th mission together" when the simulation is picking a small mission on a planet with very limited resources and a small force. Whatever we choose needs to consolidate with the other parts of the game." | Open. The 2026-09-22 answer that the economy persists through time jumps (`../options/paired-economy/brief.md` section 8) is withdrawn as a fixed constraint. What carries forward between missions is to be explored; one idea is abilities. Whatever is chosen must fit a simulation that can pick a small mission on a poor planet with a small force, and must consolidate with the rest of the game. |

## Files

- `prior_art_resources.md`: cited digest of resource systems in other games.
- `resources_options.md`: goal 1 options, three regular and three wild.
