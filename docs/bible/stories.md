# Story Catalog

One row per user-facing behavior, in the user's words. Every story enters here first, then gets its rules in its epic file. This file carries no design; rationale and rules live in `epics/E-##-*.md`. Status is what is true today, per `docs/northstar/agile.md`: Spec'd, Ready, Tested, Queued, Building, Built, Revised, Killed. IDs are stable for life.

| Story | Epic | In the commander's words | Status | Depth |
|---|---|---|---|---|
| S-001 | E-01 | "Terrain blocks some layers in some places, so I choose to go over, go around, or hide in the blocked layers." | Spec'd | `epics/E-01-layer-system.md` S-001 |
| S-002 | E-01 | "I order selected units to a layer and they go there as soon as they can." | Spec'd | `epics/E-01-layer-system.md` S-002 |
| S-003 | E-01 | "I give units a standing layer preference and they keep to it without me re-ordering at every obstacle." | Spec'd | `epics/E-01-layer-system.md` S-003 |
| S-004 | E-01 | "Changing layers takes time that depends on the unit, and the unit is exposed while it does it." | Spec'd | `epics/E-01-layer-system.md` S-004 |
| S-005 | E-01 | "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." | Spec'd | `epics/E-01-layer-system.md` S-005 |
| S-006 | E-01 | "I spend a pulse to see every layer around a unit for two seconds, then it is gone and on cooldown." | Spec'd | `epics/E-01-layer-system.md` S-006 |
| S-007 | E-01 | "A tall obstacle hides units on more layers than a short one; cover hides but never protects or blocks." | Spec'd | `epics/E-01-layer-system.md` S-007 |
| S-008 | E-01 | "I know whether my unit can shoot an enemy one layer up." | Spec'd, blocked on Q-008-01 | `epics/E-01-layer-system.md` S-008 |
| S-009 | E-01 | "I see at a glance which layer every unit is on and which layer I am focused on." | Spec'd | `epics/E-01-layer-system.md` S-009 |
| S-010 | E-01 | "A unit on a higher layer sits visibly higher on screen, and rises or drops when it changes layer." | Spec'd | `epics/E-01-layer-system.md` S-010 |
| S-011 | E-01 | "An era pack can restrict which layers a unit type may use; the Settled Reach restricts nothing." | Spec'd | `epics/E-01-layer-system.md` S-011 |
| S-012 | E-02 | "Each region's condition is four plain numbers and two summaries." | Ready | `epics/E-02-region-fields-and-drift.md` S-012 |
| S-013 | E-02 | "Garrisons decay when the region cannot pay for them and recruit when times are good." | Ready | `epics/E-02-region-fields-and-drift.md` S-013 |
| S-014 | E-02 | "Economy grows with people, shrinks under unrest, and falls back when it outruns its population." | Ready | `epics/E-02-region-fields-and-drift.md` S-014 |
| S-015 | E-02 | "A region next to a booming friendly region develops faster." | Ready | `epics/E-02-region-fields-and-drift.md` S-015 |
| S-016 | E-02 | "Tension rises with hardship and burns itself out faster the higher it gets." | Ready | `epics/E-02-region-fields-and-drift.md` S-016 |
| S-017 | E-02 | "Population is the slowest number: collapse feels permanent, recovery feels earned." | Ready | `epics/E-02-region-fields-and-drift.md` S-017 |
| S-018 | E-02 | "Regions boom and bust on their own cycles, out of step with each other." | Ready | `epics/E-02-region-fields-and-drift.md` S-018 |
| S-019 | E-02 | "A region that hits bottom stays barely alive but keeps hurting until someone helps." | Ready | `epics/E-02-region-fields-and-drift.md` S-019 |
| S-020 | E-02 | "Same seed, same galaxy, on every machine." | Ready | `epics/E-02-region-fields-and-drift.md` S-020 |
| S-021 | E-03 | "A galaxy small enough to learn, large enough to feel vast, different every campaign." | Spec'd, blocked on Q-021-01 | `epics/E-03-world-generation.md` S-021 |
| S-022 | E-03 | "My home feels established, my frontier feels newly settled." | Spec'd | `epics/E-03-world-generation.md` S-022 |
| S-023 | E-03 | "A connection carries armies, trade, or both, so a region can be rich but exposed." | Spec'd | `epics/E-03-world-generation.md` S-023 |
| S-024 | E-03 | "Peace opens trade routes; betrayal and conquest close them." | Spec'd | `epics/E-03-world-generation.md` S-024 |
| S-025 | E-03 | "Nobody starts on my doorstep; first contact happens, it is not spawned." | Spec'd | `epics/E-03-world-generation.md` S-025 |
| S-026 | E-04 | "Every crisis has a cause I can point to; history reads as consequence, not dice." | Spec'd | `epics/E-04-events-and-chains.md` S-026 |
| S-027 | E-04 | "A crisis spawns follow-ups that may or may not come, depending on how the region is doing when their time arrives." | Spec'd | `epics/E-04-events-and-chains.md` S-027 |
| S-028 | E-04 | "Two blows on the same day hurt together; a resolution and a crisis never both happen at once." | Spec'd | `epics/E-04-events-and-chains.md` S-028 |
| S-029 | E-04 | "A tense region faces a rising chance of revolt every tick, a fever not a switch." | Spec'd | `epics/E-04-events-and-chains.md` S-029 |
| S-030 | E-04 | "The galaxy's crises and booms come from a fixed, authored set." | Spec'd | `epics/E-04-events-and-chains.md` S-030 |
| S-031 | E-04 | "Every time I come back the galaxy has visibly changed." | Spec'd, blocked on Q-031-01 | `epics/E-04-events-and-chains.md` S-031 |
| S-032 | E-05 | "Every faction, mine included, runs the same loop with its own personality; no scripted villain." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-032 |
| S-033 | E-05 | "Each region pays for itself before it feeds my war chest." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-033 |
| S-034 | E-05 | "A conqueror and a fortifier want different things from the same map." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-034 |
| S-035 | E-05 | "A faction attacks only when the numbers say it wins by its own margin of comfort." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-035 |
| S-036 | E-05 | "Some attacks are announced a tick ahead at full strength, others sprung at half." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-036 |
| S-037 | E-05 | "An attack's outcome scales with how decisive it was; a strong garrison absorbs the blow." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-037 |
| S-038 | E-05 | "A region changes hands when its defenders are gone, and is hard to hold afterward." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-038 |
| S-039 | E-05 | "When several factions strike one region at once, the strongest hand usually wins, and pays for the contest." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-039 |
| S-040 | E-05 | "A large empire sheds provinces to institutional revolt no matter how calm they are." | Spec'd, blocked on Q-040-01 | `epics/E-05-faction-agents-and-conflict.md` S-040 |
| S-041 | E-05 | "A region on a hostile border is chronically stressed." | Spec'd, blocked on Q-041-01 | `epics/E-05-faction-agents-and-conflict.md` S-041 |
| S-042 | E-06 | "Every pair of factions is hostile, neutral, or cooperative, and that decides who fights and who trades." | Spec'd, blocked on Q-042-01 | `epics/E-06-diplomacy-and-technology.md` S-042 |
| S-043 | E-06 | "Two neutral neighbors who leave each other alone drift into cooperation." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-043 |
| S-044 | E-06 | "A cooperative partner can turn on me when it is stronger and under pressure." | Spec'd, blocked on Q-045-01 | `epics/E-06-diplomacy-and-technology.md` S-044 |
| S-045 | E-06 | "Each faction's technology is one level that grows with its economy." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-045 |
| S-046 | E-06 | "A conqueror's technology shows up as firepower, a fortifier's as walls and wealth." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-046 |
| S-047 | E-06 | "The weaker partner in a peace catches up toward the stronger, never past it." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-047 |
| S-048 | E-06 | "My units change in kind when my technology crosses a tier line, and fall back if it slips." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-048 |
| S-049 | E-07 | "A revolt that takes hold creates a new faction from the region." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-049 |
| S-050 | E-07 | "A region I took recently can go back to its old owner when it revolts." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-050 |
| S-051 | E-07 | "A breakaway that never grows is absorbed; a faction with no land disappears." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-051 |
| S-052 | E-07 | "My own civilization can fall." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-052 |
| S-053 | E-07 | "The sim knows whether my civilization is expanding, at war, overextended, fragmenting, or settled." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-053 |
| S-054 | E-07 | "A civilization's story can end in survival, escape, or extinction with only relics left." | Deferred (Q-054-01) | `epics/E-07-civilizational-lifecycle.md` S-054 |
| S-055 | E-08 | "Each chapter is briefing, recon, mission, resolution, time jump, new commander, always in that order." | Spec'd | `epics/E-08-generational-structure.md` S-055 |
| S-056 | E-08 | "Decades pass while I am gone, and the world decides how many." | Spec'd, blocked on Q-056-01 | `epics/E-08-generational-structure.md` S-056 |
| S-057 | E-08 | "I stay with a bloodline while its story is alive and move on when it goes quiet." | Spec'd, blocked on Q-057-01 | `epics/E-08-generational-structure.md` S-057 |
| S-058 | E-08 | "My next commander is usually family, sometimes an old enemy's heir, rarely a stranger." | Spec'd | `epics/E-08-generational-structure.md` S-058 |
| S-059 | E-08 | "My bloodline has descendants when I return, spread across nearby regions." | Spec'd | `epics/E-08-generational-structure.md` S-059 |
| S-060 | E-08 | "The people the chronicle names are born, serve, age, and die, and someone takes their place." | Spec'd | `epics/E-08-generational-structure.md` S-060 |
| S-061 | E-08 | "A fallen commander's place is taken by a relative nearby if one exists." | Spec'd | `epics/E-08-generational-structure.md` S-061 |
| S-062 | E-08 | "When my civilization is gone I keep playing in a surviving one." | Spec'd, blocked on Q-062-01 | `epics/E-08-generational-structure.md` S-062 |
| S-063 | E-08 | "I pick a difficulty and the missions I prefer before chapter one, and can change my mind later." | Spec'd, needs reference | `epics/E-08-generational-structure.md` S-063 |
| S-064 | E-08 | "The world remembers everything; my character starts fresh." | Spec'd | `epics/E-08-generational-structure.md` S-064 |
| S-065 | E-09 | "The scroll opens with what my mission did, always tells me about my family, then the biggest stories of the age." | Spec'd, blocked on Q-065-02 | `epics/E-09-chronicle.md` S-065 |
| S-066 | E-09 | "A first contact makes the chronicle even if nothing changed; a small event only if it snowballed." | Spec'd | `epics/E-09-chronicle.md` S-066 |
| S-067 | E-09 | "A famine, its revolt, and the compromise that ended it are one entry." | Spec'd, blocked on Q-067-01 | `epics/E-09-chronicle.md` S-067 |
| S-068 | E-09 | "Each entry reads like a passage from a real history, different every campaign." | Spec'd | `epics/E-09-chronicle.md` S-068 |
| S-069 | E-09 | "I watch the map change on the left while the scroll writes itself on the right, and I can stop and read." | Spec'd, needs reference | `epics/E-09-chronicle.md` S-069 |
| S-070 | E-09 | "Events near my family bubble up into the scroll, as the deeds of a military family." | Spec'd | `epics/E-09-chronicle.md` S-070 |
| S-071 | E-09 | "The scroll never repeats a sentence word for word in a campaign." | Spec'd | `epics/E-09-chronicle.md` S-071 |
| S-072 | E-10 | "My missions come from real trouble in the galaxy, weighted toward where I belong and what I do best." | Spec'd, blocked on Q-072-01 | `epics/E-10-missions.md` S-072 |
| S-073 | E-10 | "Every mission is a recognizable military situation with its own trigger, shape, and map." | Spec'd | `epics/E-10-missions.md` S-073 |
| S-074 | E-10 | "My force is sized to the enemy and shaved by how weak my civilization is, but never so small I cannot win." | Spec'd, blocked on Q-074-01 | `epics/E-10-missions.md` S-074 |
| S-075 | E-10 | "One primary objective I can see progressing, up to three secondary ones." | Spec'd | `epics/E-10-missions.md` S-075 |
| S-076 | E-10 | "A deadline that tightens when things are urgent; time is pressure, never score." | Spec'd, blocked on Q-076-01 | `epics/E-10-missions.md` S-076 |
| S-077 | E-10 | "The result is a spectrum weighing what I achieved and who I brought home." | Spec'd | `epics/E-10-missions.md` S-077 |
| S-078 | E-10 | "The outcome changes the region in proportion to how it was doing." | Spec'd | `epics/E-10-missions.md` S-078 |
| S-079 | E-10 | "I receive my orders as a superior officer would give them, three parts, no haggling." | Spec'd, needs reference | `epics/E-10-missions.md` S-079 |
| S-080 | E-10 | "Hard mode gives me less to work with, never gives the enemy better units." | Spec'd, blocked on Q-080-01 | `epics/E-10-missions.md` S-080 |
| S-081 | E-11 | "Strike beats Siege, Siege beats Line, Line beats Strike, and none of it is a death sentence." | Spec'd, blocked on Q-081-01 | `epics/E-11-units-and-combat.md` S-081 |
| S-082 | E-11 | "Six units I can learn by heart, each with one job." | Spec'd | `epics/E-11-units-and-combat.md` S-082 |
| S-083 | E-11 | "Each unit is its stats plus one or two traits plus one ability." | Spec'd, blocked on Q-083-01 | `epics/E-11-units-and-combat.md` S-083 |
| S-084 | E-11 | "Damage is simple: base times matchup, full damage in range, area damage capped." | Spec'd | `epics/E-11-units-and-combat.md` S-084 |
| S-085 | E-11 | "Fights last long enough to read, reposition, and retreat." | Spec'd | `epics/E-11-units-and-combat.md` S-085 |
| S-086 | E-11 | "Each unit has exactly one ability that amplifies its role and costs something." | Spec'd | `epics/E-11-units-and-combat.md` S-086 |
| S-087 | E-11 | "Every unit on both sides flinches, obeys, then shoots the nearest thing in range." | Spec'd | `epics/E-11-units-and-combat.md` S-087 |
| S-088 | E-11 | "A Strike squad reads as a small group, a Siege unit as a heavy asset, every ability has a cue." | Spec'd, needs reference | `epics/E-11-units-and-combat.md` S-088 |
| S-089 | E-12 | "The map is revealed only around my units." | Spec'd | `epics/E-12-fog-and-sensors.md` S-089 |
| S-090 | E-12 | "A zone of interference shrinks what units inside it see and what outsiders see into it." | Spec'd, blocked on Q-090-01 | `epics/E-12-fog-and-sensors.md` S-090 |
| S-091 | E-12 | "An elevated position sees farther." | Spec'd, blocked on Q-092-01 | `epics/E-12-fog-and-sensors.md` S-091 |
| S-092 | E-12 | "I study the whole map before I commit, then lose sight of all but what my units see." | Spec'd | `epics/E-12-fog-and-sensors.md` S-092 |
| S-093 | E-12 | "Fog changes what I know, never what happens." | Spec'd | `epics/E-12-fog-and-sensors.md` S-093 |
| S-094 | E-12 | "Unexplored space, interference, and revealed ground read differently at a glance." | Spec'd, needs reference | `epics/E-12-fog-and-sensors.md` S-094 |
| S-095 | E-13 | "A selection moves at its slowest member's pace and arrives in its shape; I split off a faster group when I choose." | Spec'd, blocked on Q-095-01 | `epics/E-13-movement-and-command.md` S-095 |
| S-096 | E-13 | "Move is movement, attack-move fights along the way, attack-target commits, ability is a button." | Spec'd | `epics/E-13-movement-and-command.md` S-096 |
| S-097 | E-13 | "Units route around terrain and flow around each other; nothing walks through anything." | Spec'd | `epics/E-13-movement-and-command.md` S-097 |
| S-098 | E-13 | "My back rank shoots over my front rank." | Spec'd | `epics/E-13-movement-and-command.md` S-098 |
| S-099 | E-13 | "My fast units flow around a stalled front faster than slow ones." | Spec'd | `epics/E-13-movement-and-command.md` S-099 |
| S-100 | E-13 | "Units face what they shoot and where they go, and turn rather than snap." | Spec'd | `epics/E-13-movement-and-command.md` S-100 |
| S-101 | E-13 | "I see units turn, slow behind blockers, and settle into their slots." | Spec'd, needs reference | `epics/E-13-movement-and-command.md` S-101 |
| S-102 | E-13 | "Every peer computes the same movement from the same commands." | Spec'd | `epics/E-13-movement-and-command.md` S-102 |
| S-103 | E-16 | "A free camera I manage myself." | Spec'd, blocked on Q-103-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-103 |
| S-104 | E-16 | "A lean HUD that shows what I need and stays out of the way." | Spec'd, needs reference | `epics/E-16-client-camera-hud-and-world-view.md` S-104 |
| S-105 | E-16 | "Click, box-select, bind groups, and never an all-army button." | Spec'd, blocked on Q-105-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-105 |
| S-106 | E-16 | "A 3D star map where territory glows, borders touch, and war flashes." | Spec'd, needs reference | `epics/E-16-client-camera-hud-and-world-view.md` S-106 |
| S-107 | E-16 | "Pan, zoom, orbit, focus a system, pick out a faction." | Spec'd | `epics/E-16-client-camera-hud-and-world-view.md` S-107 |
| S-108 | E-16 | "Mission pulls back into the galaxy and pushes into the next mission without a cut." | Spec'd, needs reference | `epics/E-16-client-camera-hud-and-world-view.md` S-108 |
| S-109 | E-16 | "The screens around a mission read as orders and reports from my civilization." | Spec'd | `epics/E-16-client-camera-hud-and-world-view.md` S-109 |
| S-110 | E-16 | "A main menu that sets the tone and settings that cover the basics." | Spec'd, blocked on Q-110-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-110 |
| S-111 | E-16 | "Saved at every chapter boundary without asking." | Spec'd, blocked on Q-111-01 | `epics/E-16-client-camera-hud-and-world-view.md` S-111 |
| S-112 | E-17 | "Maps built on hand-authored layouts so every map has a chokepoint, a flank, and a reason." | Spec'd, blocked on Q-112-01 | `epics/E-17-map-generation.md` S-112 |
| S-113 | E-17 | "Every place on the map is one of nine things." | Spec'd | `epics/E-17-map-generation.md` S-113 |
| S-114 | E-17 | "The space between waypoints feels dense or open, blind or clear, high or low." | Spec'd, blocked on Q-115-01 | `epics/E-17-map-generation.md` S-114 |
| S-115 | E-17 | "A prosperous region's battlefield is cleaner than a war-torn one's." | Spec'd, blocked on Q-117-01 | `epics/E-17-map-generation.md` S-115 |
| S-116 | E-17 | "Mission maps sized to the situation." | Spec'd, blocked on Q-118-01 | `epics/E-17-map-generation.md` S-116 |
| S-117 | E-17 | "Maps that do not cheat me." | Spec'd, blocked on Q-113-01 | `epics/E-17-map-generation.md` S-117 |
| S-118 | E-17 | "Objectives drift and hazards move during a mission." | Spec'd | `epics/E-17-map-generation.md` S-118 |
| S-119 | E-17 | "Generated sections blend like real terrain, not tiles." | Spec'd, blocked on Q-119-01 | `epics/E-17-map-generation.md` S-119 |
| S-120 | E-14 | "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." | Spec'd, blocked on Q-120-01 | `epics/E-14-enemy-macro-behavior.md` S-120 |
| S-121 | E-14 | "The enemy escalates on a schedule and reacts to me, with the moment shifting each time." | Spec'd, blocked on Q-121-01 | `epics/E-14-enemy-macro-behavior.md` S-121 |
| S-122 | E-14 | "A second enemy force reacts when I rout the first." | Spec'd, blocked on Q-122-01 | `epics/E-14-enemy-macro-behavior.md` S-122 |
| S-123 | E-14 | "Enemy behavior replays exactly like mine." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-123 |
| S-124 | E-14 | "A foreshadowed reinforcement wave arrives once in a while." | Spec'd, blocked on Q-124-01 | `epics/E-14-enemy-macro-behavior.md` S-124 |
| S-125 | E-14 | "A difficulty knob changes how much the enemy has, not how well its units fight." | Spec'd, blocked on Q-125-01 | `epics/E-14-enemy-macro-behavior.md` S-125 |
| S-126 | E-15 | "Half my force comes from the region's garrisons that I capture and hold." | Spec'd, blocked on Q-126-01 | `epics/E-15-reinforcement-supply-and-hazards.md` S-126 |
| S-127 | E-15 | "I capture a garrison by holding it unopposed and can destroy one I cannot hold." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-127 |
| S-128 | E-15 | "The enemy builds toward a composition I can read and adapt to." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-128 |
| S-129 | E-15 | "Convoys and evacuees are real units that die." | Spec'd, blocked on Q-129-01 | `epics/E-15-reinforcement-supply-and-hazards.md` S-129 |
| S-130 | E-15 | "Objectives and garrisons drift and hazards travel." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-130 |
| S-131 | E-15 | "A nebula looks like a place I cannot see into; a garrison looks like something I can take." | Spec'd, needs reference | `epics/E-15-reinforcement-supply-and-hazards.md` S-131 |
| S-132 | E-18 | "Every unit type has a shape I can read at a glance in any era." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-132 |
| S-133 | E-18 | "A faction's technology tier shows in how its ships look, and shows loss when it falls." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-133 |
| S-134 | E-18 | "Shots travel, hits bloom, nothing twitches." | Spec'd, blocked on Q-134-01 | `epics/E-18-visual-style-and-combat-visuals.md` S-134 |
| S-135 | E-18 | "Every ability reads at a glance as an ability in progress." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-135 |
| S-136 | E-18 | "A dying ship flares, burns, drifts, and darkens." | Spec'd, blocked on Q-136-01 | `epics/E-18-visual-style-and-combat-visuals.md` S-136 |
| S-137 | E-18 | "Menus and transitions feel alive from simple elements with precise timing." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-137 |
| S-138 | E-18 | "The whole game looks like one thing, low-poly and stylized." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-138 |
| S-139 | E-19 | "Every peer computes exactly the same galaxy and battle." | Spec'd | `epics/E-19-multiplayer.md` S-139 |
| S-140 | E-19 | "My orders reach every peer with no server in the middle." | Spec'd, blocked on Q-140-01 | `epics/E-19-multiplayer.md` S-140 |
| S-141 | E-19 | "I know what my friends and I are doing together in this galaxy." | Spec'd, blocked on Q-141-01 | `epics/E-19-multiplayer.md` S-141 |
| S-142 | E-19 | "A match nobody can pause or roll back." | Spec'd, blocked on Q-142-01 | `epics/E-19-multiplayer.md` S-142 |
| S-143 | E-19 | "A match with friends who own the same packs moves chronologically through eras." | Spec'd | `epics/E-19-multiplayer.md` S-143 |
| S-144 | E-19 | "Find a match, invite friends, get into the game." | Spec'd, blocked on Q-144-01 | `epics/E-19-multiplayer.md` S-144 |
| S-145 | E-20 | "The engine never says starship; a new era is content, never code." | Spec'd | `epics/E-20-multi-era-and-monetization.md` S-145 |
| S-146 | E-20 | "A checklist of exactly what an era pack contains." | Spec'd, blocked on Q-146-01 | `epics/E-20-multi-era-and-monetization.md` S-146 |
| S-147 | E-20 | "A past, a present, and a future to play, all one game." | Spec'd, blocked on Q-147-01 | `epics/E-20-multi-era-and-monetization.md` S-147 |
| S-148 | E-20 | "A campaign moves chronologically through the eras I own." | Spec'd, blocked on Q-148-01 | `epics/E-20-multi-era-and-monetization.md` S-148 |
| S-149 | E-20 | "A fair price and the chance to earn expansions by playing." | Spec'd, blocked on Q-149-02 | `epics/E-20-multi-era-and-monetization.md` S-149 |
| S-150 | E-20 | "Maps, civilizations, and era systems transfer between eras like skins." | Spec'd, blocked on Q-150-01 | `epics/E-20-multi-era-and-monetization.md` S-150 |
| S-151 | E-20 | "Someday, eras that feel different." | Deferred (A-321) | `epics/E-20-multi-era-and-monetization.md` S-151 |
| S-152 | E-21 | "The game works with no network and no model." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-152 |
| S-153 | E-21 | "One pipeline produces every text library the game reads." | Spec'd, blocked on Q-153-01 | `epics/E-21-offline-ai-pipeline.md` S-153 |
| S-154 | E-21 | "People, places, units, and factions have names that sound like they belong together." | Spec'd, blocked on Q-155-01 | `epics/E-21-offline-ai-pipeline.md` S-154 |
| S-155 | E-21 | "A repeatable pipeline turns concept art into clean low-poly models." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-155 |
| S-156 | E-21 | "Headless bot matches flag broken matchups automatically." | Spec'd, blocked on Q-158-01 | `epics/E-21-offline-ai-pipeline.md` S-156 |
| S-157 | E-21 | "Someday, per-civilization unit variety and generated archetypes." | Deferred (A-278, A-279) | `epics/E-21-offline-ai-pipeline.md` S-157 |
| S-158 | E-21 | "Agora reads distilled rules derived from these epics, never the bible." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-158 |
