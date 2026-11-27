# Movement and targeting requirements: the StarCraft 2 reference, in one page

Written 2026-11-24. This is the one page to open before building or changing how a unit moves, acquires, chases, stops or arrives. It indexes the rules; the rule text stays in the epics.

## How to use

Movement and targeting follow StarCraft 2 (Westley, 2026-10-20, 2026-11-06, 2026-11-11). Find your behaviour in the table: if the status is match, keep it; if it is a deliberate difference, the rule and his words are named, keep them; if SC2 is NOT FOUND, no source settles it, so do not guess: use the ruling in the last column, or add a `Q-` row to the register. A change that alters what Westley has already viewed in Godot is told to him first (DEC-stuck-behind-is-expected-2026-11-19). Sources: `docs/reports/2026-11-11-starcraft2-movement-targeting.md` and its appendices `appendix-a-targeting.md`, `appendix-b-movement.md` (page-level confidence there), plus a web check of 2026-11-24 (rows marked 11-24). Engine code: `csrc/unit.c`, `csrc/tactical_move.c`, `csrc/notice_internal.h`.

## Rules table

Confidence: high = Blizzard page or editor documentation read; medium = search snippet; low = forum hearsay.

| Requirement | What SC2 does (source, confidence) | What we do (rule, file) | Status | Westley's words |
|---|---|---|---|---|
| Plain move ignores enemies, even when attacked | Yes (Blizzard unit-controls guide https://news.blizzard.com/en-us/article/4552956/game-guide-basic-unit-controls, high; 11-24) | E-13 R-096-01, E-11 R-087-02; `unit.c` | match | 2026-10-20 "a unit that was on a move command ... seeing enemy does not interrupt move command" |
| Attack-move engages enemies met on the way, then resumes toward its point | Yes (same guide, high; 11-24) | E-13 R-096-02, E-11 R-087-06; `unit.c` | match | 2026-10-02 "It should resume its prior goal after the fight is completed." |
| Acquisition is a distance of its own, not sight range | Weapon field "Minimum Scan Range", separate from range (https://sc2mapster.wiki.gg/wiki/Data/Weapons/Legacy, high; 11-24) | E-11 R-087-04 notice distance; `notice_internal.h` | match | 2026-11-11 "Acquisition range: within attack radius, not vision radius"; 2026-11-17 "aquire within attack radius wins" |
| The distance is weapon range plus a margin | LotV beta: ground scan range 5 became weapon range + 0.5 (https://news.blizzard.com/en-us/article/18483059/starcraft-ii-legacy-of-the-void-beta-patchnotes-1-0, high for the beta; Liquipedia snippet "5 or weapon range, whichever greater", medium). Patch 5.0.11 raised Cyclone lock-on 7 to 7.5 so attack-moved Cyclones do not move below cast range, same intent (https://news.blizzard.com/en-gb/article/23893118/starcraft-ii-5-0-11-patch-notes, high) | margin one tenth of range, `DRAFT-notice-margin` (R-087-04) | match in kind; the number is a draft | 2026-11-17 approved the report; the number is his |
| Same distance for idle, hold, patrol, attack-move | Yes (Liquipedia Automatic Targeting, high) | R-087-04 idle and attack-move | match | |
| Lock is sticky; ends on death, invalid, leaving range, or a more important target | Yes (Automatic Targeting, high) | R-087-03, R-087-08 | match (threat-first not built, see differences) | 2026-11-11 "re-pick should only happen when lock is broken from vision loss, unit dies, or the user intervenes" |
| Pick order: can-hurt-me, priority class, weapon fit, closest only after losing a target; Colossus, Immortal, unsieged Tank prefer closest to previous target | Yes (high; the last item medium snippet 11-24) | R-087-03: nearest | deliberate difference | 2026-11-17 "I approve these two situations as well, though we won't have non-dangerous enemies so we don't need to code for that" |
| Idle (Stop) engages and chases attackers; Hold Position fires, never chases | Yes (Blizzard guide, high; 11-24) | R-087-05, R-087-06 chase with leash; guard R-096-08; hold and stop commands rejected, R-096-06 | match for idle; guard is a difference | 2026-10-13 guard is a radius guard |
| Leash distance | Editor fields "Acquire Leash Radius", "Chase Filters", "Range Slop" exist (high on names); no numbers: NOT FOUND | R-087-05: larger of sensor radius and attack range | unverified | 2026-11-01 "the vision range for that specific unit" |
| Workers do not auto-acquire | Defensive units do not, until attack-moving (Liquipedia, high/medium) | E-11 R-202-01: never acquire | match | |
| Call for help | "Acquire Call For Help Filters" weapon field and a search-effect flag exist (high on existence); radius NOT FOUND | none | unverified | |
| Idle own units give way to a moving unit | Push priority per unit; idle yield, hold-position units resist (appendix-b, Liquipedia patch notes high; idle-yield reported); forum hearsay on details (low to medium) | E-13 R-097-10; DEC-Q087-02 | unverified in detail; open Q-097-04 | 2026-10-20 "idle units are 'obstacles' to moving units, starcraft 2 movement mechanics are the reference, when stuck on blocked refer to them and use their rules" |
| Enemy units are never pushed | Reported (appendix-b), not Blizzard text | R-097-08: enemies collide like allies | unverified | |
| A blocked unit: repath, wait or give up | NOT FOUND anywhere (only an anecdotal "repath" comment) | steering side-step (ALG-68, R-097-03); no give-up, R-099-06 | match to the ruling (ruling, built) | 2026-11-24 "The unit is never supposed to \"give up\" walking towards it's attack move, or trying to find paths aroudn the object blocking it."; DEC-movement-sidestep-2026-11-24 |
| An attack-moving unit never ends its order short of its destination because it is blocked; it keeps routing | not documented; this is Westley's rule | R-099-06 (the give-up of the old R-099-05 is removed) | match to the ruling (ruling, built) | 2026-11-24, as above; priority: "the 'stopping' issue takes priority ... The 'stuck' is a nit-pick, the 'stopping' is game breaking." |
| A unit with an active move or attack order does not stray from it; an attack order strays only for an enemy within its range | SC2 (Blizzard game guide, basic unit controls): a moving unit "will continue towards the destination rather than responding to the attack"; an attack-mover takes "the next closest unit rather than chasing a single retreating unit" | R-099-07; R-087-01 (a hit never moves an attack-mover on its way); open: R-087-06 return-fire pursuit (Q-087-14), range versus notice distance (Q-087-15) | ruling (ruling; engine not yet checked against it) | 2026-11-25 "a unit with an active move or attack order does not stray from that order unless it is an attack order and an enemy is within its range." |
| Units stuck behind their own firing line are expected | not documented | DEC-stuck-behind-is-expected-2026-11-19; the stuck unit side-steps and keeps its order (ALG-68, R-099-06) | ruling (ruling, built); its give-up half is superseded by DEC-movement-sidestep-2026-11-24 | 2026-11-19 "players are expected to micro their units to path around other units already firing" |
| Arrival threshold; group clump on arrival | Clump on arrival (player post, medium); threshold NOT FOUND | E-13 R-099-04: 1.5 x radius per slot | unverified | |
| Group speed | None: each unit at its own speed (appendix-b, high) | R-095-01 slowest member's pace | deliberate difference | his Halo Wars / AoE3 model, hub; 2026-09-16 |
| High ground sees low ground, not the reverse; halfway up a ramp full view | Yes (Liquipedia, Blizzard Q&A, high) | E-05 R-005-09 | match | 2026-10-05, 2026-10-22 |
| Units block shots | No: no source says they do (report 2026-11-11 row E, unverified; medium) | R-098-01 and `csrc/tactical_move.c`: units never block fire; only cover, a wall or ground does (R-098-02) | match | 2026-11-25 "The rule is units never block fire; only cover, walls and ground do." (DEC-units-never-block-fire-2026-11-25) |
| Unit hit by something it cannot see | Not documented (appendix-a) | R-087-01: moves 200 wu away | unverified | 2026-11-06 "would run away ... but doesn't just stay still while being shot" |

## Decision of 2026-11-24: variant A

Westley approved variant A, "the old side-step", of the four-version comparison (artifact https://claude.ai/artifact/8YJhVNwQnRo7FCuXYSS6RG, version 3; DEC-movement-sidestep-2026-11-24): no give-up; a group mate and an idle friend do not block the probe; a detour keeps its side until the straight line is clear. One engine, `csrc/`, for the lab and the beta.

## Deliberate differences

- Threat first and priority classes: not built; every enemy in play can hurt (R-087-03; DEC-targeting-sc2-2026-11-17).
- Guard steps up to 200 wu from its post; SC2 hold position never moves (R-096-08; 2026-10-13, 2026-11-08).
- Unseen attacker: the unit moves away, its position is not shown (R-087-01; 2026-11-06).
- Formation: a group moves at its slowest member's pace and keeps its shape, each unit to its own slot (R-095-01, R-095-02; E-11 S-087 omits this one). A group attack-mover ends at its own slot (DEC-formation-kept-2026-11-19, "B now"); SC2 has no formation speed and clumps on arrival.

## Open questions

1. A unit blocked by its own units: SC2 NOT FOUND. Ours is ruled (2026-11-24 above); it routes by the side-step of ALG-68 (variant A below), built under DEC-movement-sidestep-2026-11-24. Q-097-04 (walker wedged in a standing crowd) is open.
2. Arrival threshold and how far a group settles: NOT FOUND. Ours R-099-04.
3. Call for help: existence only, no radius. Ours has none.
4. Idle-unit pushing: only forum hearsay (low to medium).
5. Leash numbers and Anhalt's GDC 2011 pathfinding talk: NOT FOUND (login wall).

## Reading order for a movement change

1. This page.
2. `docs/bible/epics/E-13-movement-and-command.md`: R-095 to R-099 and the Purpose.
3. `docs/bible/epics/E-11-units-and-combat.md` S-087 (R-087-01 to R-087-10).
4. `docs/northstar/ambiguity_register.md` Q-097-04, and the decisions named above in `docs/northstar/story_reviews/westley/decisions.md`.
5. Reports: `docs/reports/2026-11-18-attack-move-drift.md` (his attack-move words in order), then the 2026-11-11 SC2 report and appendices for page-level sources.
