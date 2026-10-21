# Story Catalog

One row per user-facing behavior, in the user's words. Every story enters here first, then gets its rules in its epic file. This file carries no design; rationale and rules live in `epics/E-##-*.md`. Status is what is true today, per `docs/northstar/agile.md`: Spec'd, Ready, Tested, Queued, Building, Built, Revised, Killed, Seen. IDs are stable for life.

| Story | Epic | In the commander's words | Status | Depth |
|---|---|---|---|---|
| S-001 | E-01 | "Terrain blocks some layers in some places, so I choose to go over, go around, or hide in the blocked layers." | Spec'd | `epics/E-01-layer-system.md` S-001 |
| S-002 | E-01 | "I order selected units to a layer and they go there as soon as they can." | Spec'd | `epics/E-01-layer-system.md` S-002 |
| S-003 | E-01 | "I give units a standing layer preference and they keep to it without me re-ordering at every obstacle." | Spec'd | `epics/E-01-layer-system.md` S-003 |
| S-004 | E-01 | "Changing layers takes time and exposes the unit; on a slope the halfway line is a place I can see and hold." | Spec'd | `epics/E-01-layer-system.md` S-004 |
| S-005 | E-01 | "I see less on other layers than on my own, and nothing three layers away, unless I hold a vantage." | Spec'd | `epics/E-01-layer-system.md` S-005 |
| S-006 | E-01 | "I spend a pulse to see every layer around a unit for two seconds, then it is gone and on cooldown." | Spec'd | `epics/E-01-layer-system.md` S-006 |
| S-007 | E-01 | "A tall obstacle hides units on more layers than a short one; cover hides but never protects or blocks." | Spec'd | `epics/E-01-layer-system.md` S-007 |
| S-008 | E-01 | "I know whether my unit can shoot an enemy one layer up." | Spec'd, blocked on Q-008-02, Q-008-03 | `epics/E-01-layer-system.md` S-008 |
| S-009 | E-01 | "I see at a glance which layer every unit is on and which layer I am focused on." | Spec'd; for the beta the vision tube serves (Q-009-02 closed) | `epics/E-01-layer-system.md` S-009 |
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
| S-021 | E-03 | "A galaxy small enough to learn, large enough to feel vast, different every campaign." | Ready | `epics/E-03-world-generation.md` S-021 |
| S-022 | E-03 | "My home feels established, my frontier feels newly settled." | Ready | `epics/E-03-world-generation.md` S-022 |
| S-023 | E-03 | "A connection carries armies, trade, or both, so a region can be rich but exposed." | Ready | `epics/E-03-world-generation.md` S-023 |
| S-024 | E-03 | "Peace opens trade routes; betrayal and conquest close them." | Ready | `epics/E-03-world-generation.md` S-024 |
| S-025 | E-03 | "Nobody starts on my doorstep; first contact happens, it is not spawned." | Ready | `epics/E-03-world-generation.md` S-025 |
| S-026 | E-04 | "Every crisis has a cause I can point to; history reads as consequence, not dice." |  Tested | `epics/E-04-events-and-chains.md` S-026 |
| S-027 | E-04 | "A crisis spawns follow-ups that may or may not come, depending on how the region is doing when their time arrives." |  Tested | `epics/E-04-events-and-chains.md` S-027 |
| S-028 | E-04 | "Two blows on the same day hurt together; a resolution and a crisis never both happen at once." |  Tested | `epics/E-04-events-and-chains.md` S-028 |
| S-029 | E-04 | "A tense region faces a rising chance of revolt every tick, a fever not a switch." |  Tested | `epics/E-04-events-and-chains.md` S-029 |
| S-030 | E-04 | "The galaxy's crises and booms come from a fixed, authored set." |  Tested | `epics/E-04-events-and-chains.md` S-030 |
| S-031 | E-04 | "Every time I come back the galaxy has visibly changed." | Spec'd | `epics/E-04-events-and-chains.md` S-031 |
| S-032 | E-05 | "Every faction, mine included, runs the same loop with its own personality; no scripted villain." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-032 |
| S-033 | E-05 | "Each region pays for itself before it feeds my war chest." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-033 |
| S-034 | E-05 | "A conqueror and a fortifier want different things from the same map." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-034 |
| S-035 | E-05 | "A faction attacks only when the numbers say it wins by its own margin of comfort." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-035 |
| S-036 | E-05 | "Some attacks are announced a tick ahead at full strength, others sprung at half." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-036 |
| S-037 | E-05 | "An attack's outcome scales with how decisive it was; a strong garrison absorbs the blow." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-037 |
| S-038 | E-05 | "A region changes hands when its defenders are gone, and is hard to hold afterward." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-038 |
| S-039 | E-05 | "When several factions strike one region at once, the strongest hand usually wins, and pays for the contest." |  Tested | `epics/E-05-faction-agents-and-conflict.md` S-039 |
| S-040 | E-05 | "A large empire sheds provinces to institutional revolt no matter how calm they are." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-040 |
| S-041 | E-05 | "A region on a hostile border is chronically stressed." | Spec'd | `epics/E-05-faction-agents-and-conflict.md` S-041 |
| S-042 | E-06 | "Every pair of factions is hostile, neutral, or cooperative, and that decides who fights and who trades." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-042 |
| S-043 | E-06 | "Two neutral neighbors who leave each other alone drift into cooperation." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-043 |
| S-044 | E-06 | "A cooperative partner can turn on me when it is stronger and under pressure." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-044 |
| S-045 | E-06 | "Each faction's technology is one level that grows with its economy." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-045 |
| S-046 | E-06 | "A conqueror's technology shows up as firepower, a fortifier's as walls and wealth." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-046 |
| S-047 | E-06 | "The weaker partner in a peace catches up toward the stronger, never past it." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-047 |
| S-048 | E-06 | "My units change in kind when my technology crosses a tier line, and fall back if it slips." | Spec'd | `epics/E-06-diplomacy-and-technology.md` S-048 |
| S-049 | E-07 | "A revolt that takes hold creates a new faction from the region." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-049 |
| S-050 | E-07 | "A region I took recently can go back to its old owner when it revolts." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-050 |
| S-051 | E-07 | "A breakaway that never grows is absorbed; a faction with no land disappears." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-051 |
| S-052 | E-07 | "My own civilization can fall." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-052 |
| S-053 | E-07 | "The sim knows whether my civilization is expanding, at war, overextended, fragmenting, or settled." | Spec'd | `epics/E-07-civilizational-lifecycle.md` S-053 |
| S-054 | E-07 | "A civilization's story can end in survival, escape, or extinction with only relics left." | Deferred | `epics/E-07-civilizational-lifecycle.md` S-054 |
| S-055 | E-08 | "Each chapter is briefing, recon, mission, resolution, time jump, new commander, always in that order." | Spec'd | `epics/E-08-generational-structure.md` S-055 |
| S-056 | E-08 | "Decades pass while I am gone, and the world decides how many." | Spec'd | `epics/E-08-generational-structure.md` S-056 |
| S-057 | E-08 | "I stay with a bloodline while its story is alive and move on when it goes quiet." | Spec'd | `epics/E-08-generational-structure.md` S-057 |
| S-058 | E-08 | "My next commander is usually family, sometimes an old enemy's heir, rarely a stranger." | Spec'd | `epics/E-08-generational-structure.md` S-058 |
| S-059 | E-08 | "My bloodline has descendants when I return, spread across nearby regions." | Spec'd | `epics/E-08-generational-structure.md` S-059 |
| S-060 | E-08 | "The people the chronicle names are born, serve, age, and die, and someone takes their place." | Spec'd | `epics/E-08-generational-structure.md` S-060 |
| S-061 | E-08 | "A fallen commander's place is taken by a relative nearby if one exists." | Spec'd | `epics/E-08-generational-structure.md` S-061 |
| S-062 | E-08 | "When my civilization is gone I keep playing in a surviving one." | Spec'd | `epics/E-08-generational-structure.md` S-062 |
| S-063 | E-08 | "I pick a difficulty and the missions I prefer before chapter one, and can change my mind later." | Spec'd, needs reference | `epics/E-08-generational-structure.md` S-063 |
| S-064 | E-08 | "The world remembers everything; my character starts fresh." | Spec'd | `epics/E-08-generational-structure.md` S-064 |
| S-065 | E-09 | "The scroll opens with what my mission did, always tells me about my family, then the biggest stories of the age." | Spec'd | `epics/E-09-chronicle.md` S-065 |
| S-066 | E-09 | "A first contact makes the chronicle even if nothing changed; a small event only if it snowballed." | Spec'd | `epics/E-09-chronicle.md` S-066 |
| S-067 | E-09 | "A famine, its revolt, and the compromise that ended it are one entry." | Spec'd | `epics/E-09-chronicle.md` S-067 |
| S-068 | E-09 | "Each entry reads like a passage from a real history, different every campaign." | Spec'd | `epics/E-09-chronicle.md` S-068 |
| S-069 | E-09 | "I watch the map change on the left while the scroll writes itself on the right, and I can stop and read." | Spec'd, needs reference | `epics/E-09-chronicle.md` S-069 |
| S-070 | E-09 | "Events near my family bubble up into the scroll, as the deeds of a military family." | Spec'd | `epics/E-09-chronicle.md` S-070 |
| S-071 | E-09 | "The scroll never repeats a sentence word for word in a campaign." | Spec'd | `epics/E-09-chronicle.md` S-071 |
| S-072 | E-10 | "My missions come from real trouble in the galaxy, weighted toward where I belong and what I do best." | Spec'd | `epics/E-10-missions.md` S-072 |
| S-073 | E-10 | "Every mission is a recognizable military situation with its own trigger, shape, and map." | Spec'd | `epics/E-10-missions.md` S-073 |
| S-074 | E-10 | "My force is sized to the enemy and shaved by how weak my civilization is, but never so small I cannot win." | Spec'd | `epics/E-10-missions.md` S-074 |
| S-075 | E-10 | "One primary objective I can see progressing, up to three secondary ones." | Spec'd | `epics/E-10-missions.md` S-075 |
| S-076 | E-10 | "A deadline that tightens when things are urgent; time is pressure, never score." | Spec'd | `epics/E-10-missions.md` S-076 |
| S-077 | E-10 | "The result is a spectrum weighing what I achieved and who I brought home." | Spec'd | `epics/E-10-missions.md` S-077 |
| S-078 | E-10 | "The outcome changes the region in proportion to how it was doing." | Spec'd | `epics/E-10-missions.md` S-078 |
| S-079 | E-10 | "I receive my orders as a superior officer would give them, three parts, no haggling." | Spec'd, needs reference | `epics/E-10-missions.md` S-079 |
| S-080 | E-10 | "Hard mode gives me less to work with, never gives the enemy better units." | Spec'd | `epics/E-10-missions.md` S-080 |
| S-081 | E-11 | "Strike beats Siege, Siege beats Line, Line beats Strike, and none of it is a death sentence." | Spec'd | `epics/E-11-units-and-combat.md` S-081 |
| S-082 | E-11 | "A roster of 20 to 40 unit types per era, each with a job I can learn." | Spec'd, blocked on Q-082-03 to Q-082-05 | `epics/E-11-units-and-combat.md` S-082 |
| S-083 | E-11 | "I unlock trait cards and build a force that plays my way, and cards never beat positioning." | Spec'd, post-launch, blocked on Q-083-03 | `epics/E-11-units-and-combat.md` S-083 |
| S-084 | E-11 | "Damage is simple: base times matchup, full damage in range, area damage capped." | Spec'd | `epics/E-11-units-and-combat.md` S-084 |
| S-085 | E-11 | "Fights last long enough to read, reposition, and retreat." | Spec'd | `epics/E-11-units-and-combat.md` S-085 |
| S-086 | E-11 | "Each unit has exactly one ability that amplifies its role and costs something." | Spec'd | `epics/E-11-units-and-combat.md` S-086 |
| S-087 | E-11 | "Every unit on both sides flinches, obeys, then shoots the nearest thing in range." | Spec'd | `epics/E-11-units-and-combat.md` S-087 |
| S-088 | E-11 | "A Strike squad reads as a small group, a Siege unit as a heavy asset, every ability has a cue." | Spec'd, needs reference | `epics/E-11-units-and-combat.md` S-088 |
| S-089 | E-12 | "The map is revealed only around my units." | Spec'd | `epics/E-12-fog-and-sensors.md` S-089 |
| S-090 | E-12 | "A zone of interference shrinks what units inside it see and what outsiders see into it." | Spec'd | `epics/E-12-fog-and-sensors.md` S-090 |
| S-091 | E-12 | "An elevated position sees farther." | Spec'd | `epics/E-12-fog-and-sensors.md` S-091 |
| S-092 | E-12 | "I study the whole map before I commit, then lose sight of all but what my units see." | Spec'd | `epics/E-12-fog-and-sensors.md` S-092 |
| S-093 | E-12 | "Fog binds my units and the enemy's by one rule; what I am shown never changes what happens." | Spec'd | `epics/E-12-fog-and-sensors.md` S-093 |
| S-094 | E-12 | "Unexplored space, interference, and revealed ground read differently at a glance." | Spec'd, needs reference | `epics/E-12-fog-and-sensors.md` S-094 |
| S-095 | E-13 | "A selection moves at its slowest member's pace and arrives in its shape; I split off a faster group when I choose." | Spec'd | `epics/E-13-movement-and-command.md` S-095 |
| S-096 | E-13 | "Move is movement, attack-move fights along the way, attack-target commits, ability is a button." | Spec'd | `epics/E-13-movement-and-command.md` S-096 |
| S-097 | E-13 | "Units route around terrain and flow around each other; nothing walks through anything." | Spec'd | `epics/E-13-movement-and-command.md` S-097 |
| S-098 | E-13 | "My back rank shoots over my front rank." | Spec'd | `epics/E-13-movement-and-command.md` S-098 |
| S-099 | E-13 | "My fast units flow around a stalled front faster than slow ones." | Spec'd | `epics/E-13-movement-and-command.md` S-099 |
| S-100 | E-13 | "Units face what they shoot and where they go, and turn rather than snap." | Spec'd | `epics/E-13-movement-and-command.md` S-100 |
| S-101 | E-13 | "I see units turn, slow behind blockers, and settle into their slots." | Spec'd, needs reference | `epics/E-13-movement-and-command.md` S-101 |
| S-102 | E-13 | "Every peer computes the same movement from the same commands." | Spec'd | `epics/E-13-movement-and-command.md` S-102 |
| S-103 | E-16 | "A free camera I manage myself, with the Angle Rack, the Layer Peel, and a flip key." | Seen | `epics/E-16-client-camera-hud-and-world-view.md` S-103 |
| S-104 | E-16 | "A lean HUD that shows what I need and stays out of the way." | Spec'd, needs reference | `epics/E-16-client-camera-hud-and-world-view.md` S-104 |
| S-105 | E-16 | "Click, box-select, bind groups, and never an all-army button." | Spec'd | `epics/E-16-client-camera-hud-and-world-view.md` S-105 |
| S-106 | E-16 | "A 3D star map where territory glows, borders touch, and war flashes." | Seen | `epics/E-16-client-camera-hud-and-world-view.md` S-106 |
| S-107 | E-16 | "Pan, zoom, orbit, focus a system, pick out a faction." | Seen | `epics/E-16-client-camera-hud-and-world-view.md` S-107 |
| S-108 | E-16 | "Mission pulls back into the galaxy and pushes into the next mission without a cut." | Spec'd, needs reference; prototype first (Westley, 2026-10-15), mockup in build | `epics/E-16-client-camera-hud-and-world-view.md` S-108 |
| S-109 | E-16 | "The screens around a mission read as orders and reports from my civilization." | Spec'd | `epics/E-16-client-camera-hud-and-world-view.md` S-109 |
| S-110 | E-16 | "A main menu that sets the tone and settings that cover the basics." | Seen | `epics/E-16-client-camera-hud-and-world-view.md` S-110 |
| S-111 | E-16 | "Saved at every chapter boundary without asking." | Spec'd | `epics/E-16-client-camera-hud-and-world-view.md` S-111 |
| S-112 | E-17 | "Maps built on hand-authored strategic layouts." | Spec'd (the layouts stay and terrain-first generation is added, the layout calls for places and the landscape engine must produce them, S-191 R-191-10; rewrite pending; see S-186, S-191) | `epics/E-17-map-generation.md` S-112 |
| S-113 | E-17 | "Every place on the map is one of nine things." | Spec'd (the nine kinds stay and found places are added, S-191 R-191-10; rewrite pending; see S-191, S-192) | `epics/E-17-map-generation.md` S-113 |
| S-114 | E-17 | "The space between waypoints feels dense or open, blind or clear, high or low." | Spec'd (the gradients stay and terrain-driven fields are added; rewrite pending; see S-188 to S-190) | `epics/E-17-map-generation.md` S-114 |
| S-115 | E-17 | "A prosperous region's battlefield is cleaner than a war-torn one's." | Spec'd (the region's flavoring stays and a seed-derived climate and landform are added; rewrite pending; see S-187) | `epics/E-17-map-generation.md` S-115 |
| S-116 | E-17 | "Mission maps sized to the situation." | Spec'd (direction changed, rewrite pending; see S-195) | `epics/E-17-map-generation.md` S-116 |
| S-117 | E-17 | "Maps that do not cheat me." | Spec'd (the fairness check stays and also scores terrain-first maps; rewrite pending; see S-197) | `epics/E-17-map-generation.md` S-117 |
| S-118 | E-17 | "Objectives drift and hazards move during a mission." | Spec'd (the moving objectives stay; on a map that combines a layout with terrain they follow walking routes on the terrain, S-191 R-191-10) | `epics/E-17-map-generation.md` S-118 |
| S-119 | E-17 | "Generated sections blend like real terrain, not tiles." | Spec'd (terrain is added to the layouts; rewrite pending; see S-186, S-196) | `epics/E-17-map-generation.md` S-119 |
| S-120 | E-14 | "Enemy forces advance, hold, patrol, ambush, or retreat, cautiously, aggressively, or in echelons." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-120 |
| S-121 | E-14 | "The enemy escalates on a schedule and reacts to me, with the moment shifting each time." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-121 |
| S-122 | E-14 | "A second enemy force reacts when I rout the first." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-122 |
| S-123 | E-14 | "Enemy behavior replays exactly like mine." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-123 |
| S-124 | E-14 | "A foreshadowed reinforcement wave arrives once in a while." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-124 |
| S-125 | E-14 | "A difficulty knob changes how much the enemy has, not how well its units fight." | Spec'd | `epics/E-14-enemy-macro-behavior.md` S-125 |
| S-126 | E-15 | "A fifth of my force is given; the rest I take from the region's garrisons and hold." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-126 |
| S-127 | E-15 | "I capture a garrison by holding it unopposed and can destroy one I cannot hold." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-127 |
| S-128 | E-15 | "The enemy builds toward a composition I can read and adapt to." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-128 |
| S-129 | E-15 | "Convoys and evacuees are real units that die." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-129 |
| S-130 | E-15 | "Objectives and garrisons drift and hazards travel." | Spec'd | `epics/E-15-reinforcement-supply-and-hazards.md` S-130 |
| S-131 | E-15 | "A nebula looks like a place I cannot see into; a garrison looks like something I can take." | Spec'd, needs reference | `epics/E-15-reinforcement-supply-and-hazards.md` S-131 |
| S-132 | E-18 | "Every unit type has a shape I can read at a glance in any era." | Spec'd, needs reference; Q-132-02 parked for the beta | `epics/E-18-visual-style-and-combat-visuals.md` S-132 |
| S-133 | E-18 | "A faction's technology tier shows in how its ships look, and shows loss when it falls." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-133 |
| S-134 | E-18 | "Shots travel, hits bloom, nothing twitches." | Spec'd | `epics/E-18-visual-style-and-combat-visuals.md` S-134 |
| S-135 | E-18 | "Every ability reads at a glance as an ability in progress." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-135 |
| S-136 | E-18 | "A dying ship flares, burns, drifts, and darkens." | Spec'd | `epics/E-18-visual-style-and-combat-visuals.md` S-136 |
| S-137 | E-18 | "Menus and transitions feel alive from simple elements with precise timing." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-137 |
| S-138 | E-18 | "The whole game looks like one thing, low-poly and stylized." | Spec'd, needs reference | `epics/E-18-visual-style-and-combat-visuals.md` S-138 |
| S-139 | E-19 | "Every peer computes exactly the same galaxy and battle." | Spec'd | `epics/E-19-multiplayer.md` S-139 |
| S-140 | E-19 | "My orders reach every peer with no server in the middle." | Spec'd | `epics/E-19-multiplayer.md` S-140 |
| S-141 | E-19 | "I know what my friends and I are doing together in this galaxy." | Seen; co-op only at launch | `epics/E-19-multiplayer.md` S-141 |
| S-142 | E-19 | "A match nobody can pause or roll back." | Spec'd | `epics/E-19-multiplayer.md` S-142 |
| S-143 | E-19 | "A match with friends who own the same packs moves chronologically through eras." | Seen | `epics/E-19-multiplayer.md` S-143 |
| S-144 | E-19 | "Find a match, invite friends, get into the game." | Spec'd, blocked on Q-144-03 | `epics/E-19-multiplayer.md` S-144 |
| S-145 | E-20 | "The engine never says starship; a new era is content, never code." | Spec'd | `epics/E-20-multi-era-and-monetization.md` S-145 |
| S-146 | E-20 | "A checklist of exactly what an era pack contains." | Spec'd, blocked on Q-082-05 | `epics/E-20-multi-era-and-monetization.md` S-146 |
| S-147 | E-20 | "An era in space and an era on land to play, all one game." | Spec'd; both eras exist as packs (Settled Reach, Greek placeholder "The Marble Reach"); the land era's final name and brief are Q-147-01 | `epics/E-20-multi-era-and-monetization.md` S-147 |
| S-148 | E-20 | "A campaign moves chronologically through the eras I own." | Spec'd, blocked on Q-148-04, Q-148-05 | `epics/E-20-multi-era-and-monetization.md` S-148 |
| S-149 | E-20 | "A fair price and the chance to earn expansions by playing." | Spec'd, blocked on Q-149-02 | `epics/E-20-multi-era-and-monetization.md` S-149 |
| S-150 | E-20 | "Maps, civilizations, and era systems transfer between eras like skins." | Spec'd, blocked on Q-150-01 | `epics/E-20-multi-era-and-monetization.md` S-150 |
| S-151 | E-20 | "Eras that feel different." | Spec'd; values come from the simulation lab's crossings (Westley, 2026-10-15), not scheduled | `epics/E-20-multi-era-and-monetization.md` S-151 |
| S-152 | E-21 | "The game works with no network and no model." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-152 |
| S-153 | E-21 | "One pipeline produces every text library the game reads." | Spec'd, blocked on Q-153-01 | `epics/E-21-offline-ai-pipeline.md` S-153 |
| S-154 | E-21 | "People, places, units, and factions have names that sound like they belong together." | Spec'd, blocked on Q-155-01 | `epics/E-21-offline-ai-pipeline.md` S-154 |
| S-155 | E-21 | "A repeatable pipeline turns concept art into clean low-poly models." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-155 |
| S-156 | E-21 | "Headless bot matches flag broken matchups automatically." | Spec'd, blocked on Q-156-02 | `epics/E-21-offline-ai-pipeline.md` S-156 |
| S-157 | E-21 | "Someday, per-civilization unit variety and generated archetypes." | Deferred (A-278, A-279) | `epics/E-21-offline-ai-pipeline.md` S-157 |
| S-158 | E-21 | "Agora reads distilled rules derived from these epics, never the bible." | Spec'd | `epics/E-21-offline-ai-pipeline.md` S-158 |
| S-159 | E-19 | "A real economy: run by a partner, or running itself." | Design decided 2026-10-01 and 10-07, not scheduled (Q-159-08 in part) | `epics/E-19-multiplayer.md` S-159 |
| S-160 | E-02 | "A feature I switch off actually skips its step; a fresh world drifts by default." | Ready | `epics/E-02-region-fields-and-drift.md` S-160 |
| S-161 | E-16 | "I pull the camera back until the battle reads as a map and give groups move orders from there." | Spec'd, blocked on Q-103-05 | `epics/E-16-client-camera-hud-and-world-view.md` S-161 |
| S-162 | E-01 | "I ping a layer I choose at a place I choose and see it for a moment; whoever I ping learns roughly where I am." | Spec'd | `epics/E-01-layer-system.md` S-162 |
| S-163 | E-01 | "I choose which of my forces look and which stay quiet; looking further means being seen." | Spec'd | `epics/E-01-layer-system.md` S-163 |
| S-164 | E-01 | "Each unit type reaches only certain layers with its fire, so where I put each type decides who gets shots off." | Spec'd | `epics/E-01-layer-system.md` S-164 |
| S-165 | E-17 | "Someday, perhaps: lanes where my troops move faster and strategic ground where they move slower." | Deferred (Q-165-01) | `epics/E-17-map-generation.md` S-165 |
| S-166 | E-17 | "Cities and bases that build themselves around what I place, on ground with real height." | Design decided 2026-10-02, not scheduled; now holds Westley's direction and the fixed principles, the rules that carry them out are S-186 to S-197 | `epics/E-17-map-generation.md` S-166 |
| S-167 | E-22 | "I train workers who walk to a source and bring back one of three resources." | Design decided 2026-10-01, not scheduled (Q-159-08 in part, Q-167-01, Q-167-02) | `epics/E-22-economy-and-bases.md` S-167 |
| S-168 | E-22 | "I place buildings where I choose and the city reshapes around them." | Design decided 2026-10-01 and 10-02, not scheduled (Q-168-03) | `epics/E-22-economy-and-bases.md` S-168 |
| S-169 | E-22 | "Workers and soldiers share one population cap that I can raise a very long way." | Design decided 2026-10-01, not scheduled (Q-169-01) | `epics/E-22-economy-and-bases.md` S-169 |
| S-170 | E-22 | "I run the production buildings and plan what they make, and changing a building's focus takes a while." | Design decided 2026-10-01, not scheduled (Q-159-08, Q-170-01 to -03) | `epics/E-22-economy-and-bases.md` S-170 |
| S-171 | E-22 | "Strike, Line and Siege counter each other, and what a side gathers shows what it is making." | Design decided 2026-10-01, not scheduled (Q-159-08, Q-171-01) | `epics/E-22-economy-and-bases.md` S-171 |
| S-172 | E-22 | "I can hide what my production is doing from an enemy who sees my buildings." | Design decided 2026-10-01, not scheduled (Q-159-09, Q-172-01) | `epics/E-22-economy-and-bases.md` S-172 |
| S-173 | E-22 | "I choose the technology my side goes for, and a normal match has time to go up one or two levels." | Design decided in part 2026-10-02, not scheduled (Q-159-12; Q-173-01, -02 parked post-beta) | `epics/E-22-economy-and-bases.md` S-173 |
| S-174 | E-22 | "I build walls, gates and towers to cover the lanes raiders take to my workers and shipments." | Design decided 2026-10-01, not scheduled (Q-174-02) | `epics/E-22-economy-and-bases.md` S-174 |
| S-175 | E-22 | "I grow settlements into new bases and build forward works near the front, and a side that stays home is overrun." | Design decided 2026-10-01 and 10-07, not scheduled (Q-175-04) | `epics/E-22-economy-and-bases.md` S-175 |
| S-176 | E-22 | "Shipments come from the civilization and from my forward posts, I see them on the road but they give me no vision, and nobody tells me when one is killed." | Design decided 2026-10-01 and 10-06, not scheduled; no open flag | `epics/E-22-economy-and-bases.md` S-176 |
| S-177 | E-22 | "Every side has a base to protect, and the rich resources lie away from the objective." | Design decided 2026-10-02 and 10-06, not scheduled (Q-177-07) | `epics/E-22-economy-and-bases.md` S-177 |
| S-178 | E-22 | "A fallen base is occupied, not destroyed, and I fall back to an expansion or forward works." | Design decided 2026-10-02 and 10-06, not scheduled; no open flag | `epics/E-22-economy-and-bases.md` S-178 |
| S-179 | E-22 | "When nobody holds the economy seat, rules run it well by a doctrine I can change on the fly." | Design decided 2026-10-02, not scheduled (Q-179-02) | `epics/E-22-economy-and-bases.md` S-179 |
| S-180 | E-22 | "Alone I have one dial and I ask for things by pointing at the map." | Design decided 2026-10-02 and 10-06, not scheduled (Q-180-01) | `epics/E-22-economy-and-bases.md` S-180 |
| S-181 | E-22 | "The enemy's economy runs on the same rules, and the difficulty decides whether it also scouts, counters and disguises." | Design decided 2026-10-02 and 10-07, not scheduled; no open flag | `epics/E-22-economy-and-bases.md` S-181 |
| S-182 | E-22 | "I carry something forward between missions, without the fifteenth mission becoming lopsided." | Decided for the beta 2026-10-07: nothing carries forward, a post-beta idea (Q-159-13 to be designed) | `epics/E-22-economy-and-bases.md` S-182 |
| S-186 | E-17 | "Every map starts as real ground, height and water from the seed." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-17-map-generation.md` S-186 |
| S-187 | E-17 | "Mesas, canyons, island chains and fjords, not only rolling hills." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-17-map-generation.md` S-187 |
| S-188 | E-17 | "A mountainside is a stack of layers an attacker has to climb." | Design decided 2026-10-02, not scheduled; flag Q-166-04 (Q-188-01 closed 2026-10-15); land maps only (space: S-246) | `epics/E-17-map-generation.md` S-188 |
| S-189 | E-17 | "Some ground is too steep to walk, and slopes are the ways between layers." | Design decided 2026-10-02, not scheduled; no open flag (the walking limit is 35 degrees, Q-189-02 closed 2026-10-04; the route count-and-width rule, Q-189-04 closed 2026-10-15); land maps only | `epics/E-17-map-generation.md` S-189 |
| S-190 | E-17 | "The layers follow the land under my units." | Design decided 2026-10-02, not scheduled; no open flag; land maps only | `epics/E-17-map-generation.md` S-190 |
| S-191 | E-17 | "Bases, objectives and resources sit where the land puts them." | Design decided 2026-10-02, not scheduled; no open flag (Q-191-05 closed 2026-10-15, the figures come from the lab); land maps only | `epics/E-17-map-generation.md` S-191 |
| S-192 | E-17 | "Ways up and down I can hold, narrow places to fight over, high ground to take." | Design decided 2026-10-02, not scheduled; no open flag; land maps only | `epics/E-17-map-generation.md` S-192 |
| S-193 | E-17 | "Cities rise from scaffolds in waves, climb cliffs and reshape around what I place, and dense districts slow units and give cover but always leave natural paths through." | Design decided 2026-10-02, not scheduled; flags Q-193-04, Q-193-05 (parked) | `epics/E-17-map-generation.md` S-193 |
| S-194 | E-17 | "One continuous world from a single unit to the whole battlefield." | Design decided 2026-10-02, not scheduled; flag Q-194-01 | `epics/E-17-map-generation.md` S-194 |
| S-195 | E-17 | "Bigger matches have bigger maps." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-17-map-generation.md` S-195 |
| S-196 | E-17 | "A land era and a space era look different over the same kind of map." | Design decided 2026-10-02, not scheduled; the space landscape is S-246 | `epics/E-17-map-generation.md` S-196 |
| S-197 | E-17 | "A map that favors the defender is still one I can win." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-17-map-generation.md` S-197 |
| S-200 | E-01 | "On a land map the height of the ground decides which layers are rock and which are air, and what walkers can climb." | Design decided 2026-10-02, not scheduled (Q-166-04, Q-189-02; space is S-246) | `epics/E-01-layer-system.md` S-200 |
| S-201 | E-11 | "The land era has units that walk, so slopes and strongpoints at slopes decide where an army can go." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-11-units-and-combat.md` S-201 |
| S-202 | E-11 | "Workers are real units that cannot fight, can be killed, and count in the population cap and the unit budgets." | Design decided 2026-10-02 and 10-07, not scheduled; no open flag | `epics/E-11-units-and-combat.md` S-202 |
| S-203 | E-11 | "Every unit type costs the three resources by its category and takes its share of the population cap." | Design decided 2026-10-02, not scheduled (Q-159-08, Q-169-01, Q-167-01) | `epics/E-11-units-and-combat.md` S-203 |
| S-204 | E-11 | "Walls, gates, towers and production buildings are things on the map that block, are seen and can be attacked." | Design decided 2026-10-02 and 10-07, not scheduled (Q-174-02) | `epics/E-11-units-and-combat.md` S-204 |
| S-205 | E-12 | "An enemy building appears when my units see it and shows what it is doing, so scouting reads a base and hiding a building is a play." | Design decided 2026-10-02, not scheduled (Q-159-09 parked) | `epics/E-12-fog-and-sensors.md` S-205 |
| S-206 | E-12 | "My side remembers which kinds of enemy unit it has seen, and nothing about where." | Design decided 2026-10-02, not scheduled (Q-206-02) | `epics/E-12-fog-and-sensors.md` S-206 |
| S-207 | E-13 | "Routes follow the buildings that rise and fall, the slopes and the steep ground, and no unit is stuck in terrain or walks off the map." | Buildings, slopes, steep ground: design decided 2026-10-02, not scheduled (Q-174-02). Push-out and clamp (R-207-06, R-207-07): ruled, built with the tactical port | `epics/E-13-movement-and-command.md` S-207 |
| S-208 | E-13 | "I can put units on guard at a post so a choke or a slope top holds without them running out." | Ruled 2026-10-13 (R-096-08, radius guard), not scheduled past the lab; Q-208-01 (hold fire) open | `epics/E-13-movement-and-command.md` S-208 |
| S-209 | E-13 | "Workers walk the same ground and take the same room as soldiers, and count among the live units." | Design decided 2026-10-02, not scheduled | `epics/E-13-movement-and-command.md` S-209 |
| S-210 | E-10 | "Each side starts from the base its mission type calls for, and an attacker gets a forward base." | Design decided 2026-10-02 and 10-07, not scheduled (Q-177-07, Q-210-07 liberty: Architect) | `epics/E-10-missions.md` S-210 |
| S-211 | E-10 | "The resources on the map fit the situation, tilted toward the better position, and I always have the means to do the job." | Design decided 2026-10-02 and 10-07, not scheduled (Q-211-02, to be explored) | `epics/E-10-missions.md` S-211 |
| S-212 | E-10 | "Losing my main base costs me the result, never better than partial failure, but I can fall back to what I still hold." | Design decided 2026-10-02 and 10-07, not scheduled; no open flag | `epics/E-10-missions.md` S-212 |
| S-213 | E-10 | "A mission starts with technology that follows the civilization only slightly, so there is still room to climb." | Design decided in part 2026-10-02, not scheduled (Q-173-01, Q-159-12) | `epics/E-10-missions.md` S-213 |
| S-214 | E-10 | "More players on the team means a bigger map, more enemies and more resources: 64,000 wu for 4 to 6." | Design decided 2026-10-02 and 10-07, not scheduled (teams of 6 are a desired future feature) | `epics/E-10-missions.md` S-214 |
| S-215 | E-14 | "The enemy runs an economy on my rules, richer and more farsighted as the difficulty sets." | Design decided 2026-10-02 and 10-07, not scheduled (Q-215-04) | `epics/E-14-enemy-macro-behavior.md` S-215 |
| S-216 | E-14 | "The enemy defends its bases, falls back to what it holds and raids my workers and shipments." | Design decided 2026-10-02 and 10-07, not scheduled | `epics/E-14-enemy-macro-behavior.md` S-216 |
| S-217 | E-14 | "The enemy moves between layers, pings and goes quiet as I can." | Design decided 2026-10-02, not scheduled (Q-217-01) | `epics/E-14-enemy-macro-behavior.md` S-217 |
| S-218 | E-15 | "Strongpoints stand at the slopes between height bands; hold one and I hold the way up or down and produce on that band, paid for by my economy." | Design decided 2026-10-02, not scheduled, land maps only (space: S-246) | `epics/E-15-reinforcement-supply-and-hazards.md` S-218 |
| S-219 | E-15 | "My region's trouble travels across the map where both sides see it and shuts down what it passes over." | Design decided 2026-10-02, not scheduled (Q-219-02 to be designed, Q-219-04 parked) | `epics/E-15-reinforcement-supply-and-hazards.md` S-219 |
| S-220 | E-02 | "What I did in a mission shows in the region when I come back." | Direction decided in part 2026-10-02, not scheduled; Q-220-01, Q-220-02, Q-159-13 | `epics/E-02-region-fields-and-drift.md` S-220 |
| S-221 | E-02 | "Each region has its own climate, landform and trouble, derived from the seed, with no change to the region record." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-02-region-fields-and-drift.md` S-221 |
| S-222 | E-02 | "A settlement grows in step with how its region is doing." | Decided in part 2026-10-02, not scheduled; Q-193-04, Q-193-05 (E-17, parked) | `epics/E-02-region-fields-and-drift.md` S-222 |
| S-223 | E-03 | "The galaxy says how far a mission's region lies from the civilization." | Design decided 2026-10-02, not scheduled; no rule reads the supply distance since 2026-10-06 | `epics/E-03-world-generation.md` S-223 |
| S-224 | E-03 | "A 400-region galaxy starts within a time Westley has confirmed." | Open; Q-224-01 | `epics/E-03-world-generation.md` S-224 |
| S-225 | E-04 | "The history I read agrees with the ground I fight on." | Open; Q-225-01, Q-225-02 | `epics/E-04-events-and-chains.md` S-225 |
| S-226 | E-05 | "A faction's standing in the galaxy carries into the economy it fights with." | Decided in part 2026-10-07; Q-226-02 parked for the beta | `epics/E-05-faction-agents-and-conflict.md` S-226 |
| S-227 | E-06 | "A mission starts from the faction's technology, only slightly." | Decided in part 2026-10-02, not scheduled; Q-227-02, Q-227-03, and Q-173-01 held in E-22, Q-159-12 | `epics/E-06-diplomacy-and-technology.md` S-227 |
| S-228 | E-08 | "My pair is part of the chapter, the ledger and the world." | Direction decided 2026-10-02, not scheduled; Q-228-01, Q-228-02 | `epics/E-08-generational-structure.md` S-228 |
| S-230 | E-16 | "As the economy player of a pair, my screen shows resources, workers, the yield of a lot before I place, my schedule, technology and defenses, and no list of what the commander needs." | Design decided 2026-10-02 and 10-07, not scheduled; Q-230-02 parked for the beta | `epics/E-16-client-camera-hud-and-world-view.md` S-230 |
| S-231 | E-16 | "Alone, I have a dial, a doctrine switch, unit-mix switches and I ask by pointing, even from the map view." | Design decided 2026-10-02 and 10-07, not scheduled; Q-231-01 and -02 liberty: Architect | `epics/E-16-client-camera-hud-and-world-view.md` S-231 |
| S-232 | E-16 | "I see my ping and my emitting forces, I am told when I am pinged and from which way, and told when a unit cannot reach a layer." | Spec'd, keys decided in part 2026-10-07 (Q-232-03) | `epics/E-16-client-camera-hud-and-world-view.md` S-232 |
| S-233 | E-16 | "I choose how the rules run my economy and whether the enemy's economy is clever." | Design decided 2026-10-02 and 10-07, not scheduled; no open flag | `epics/E-16-client-camera-hud-and-world-view.md` S-233 |
| S-234 | E-16 | "I zoom from a single unit to the battlefield's map view in one smooth drawing, and the zoom stops there." | Spec'd; the Sand Table is decided by the prototype (Q-103-05) | `epics/E-16-client-camera-hud-and-world-view.md` S-234 |
| S-235 | E-16 | "The map shows where the economy is, weather moving across it, and the ticker tells me what happened to it." | Design decided 2026-10-02 and 10-12 (Q-235-01 closed), not scheduled | `epics/E-16-client-camera-hud-and-world-view.md` S-235 |
| S-236 | E-18 | "The ground is drawn in deep detail up close and as the shape of the land far away, with no pop between." | Design decided 2026-10-02, not scheduled; land maps only (space: S-246) | `epics/E-18-visual-style-and-combat-visuals.md` S-236 |
| S-237 | E-18 | "A base starts as ground under construction and rises stage by stage, spreading and thickening." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-18-visual-style-and-combat-visuals.md` S-237 |
| S-238 | E-18 | "I see workers walk and gather, weather cross the map, and disguised buildings look like what they pretend to be." | Design decided 2026-10-02, not scheduled; Q-238-01 | `epics/E-18-visual-style-and-combat-visuals.md` S-238 |
| S-239 | E-18 | "A ping, an emitting force and a ping alert read at a glance." | Spec'd, look decided 2026-10-07 | `epics/E-18-visual-style-and-combat-visuals.md` S-239 |
| S-240 | E-18 | "A screen of thousands of units, workers and buildings stays smooth." | Direction only until the simulation's budgets (10,000) are reached | `epics/E-18-visual-style-and-combat-visuals.md` S-240 |
| S-241 | E-19 | "My pair is a sub-civilization in a team of 2 or 4, and the map, resources and enemies grow with the team; teams of 6 are a desired future feature." | Seen (Westley 2026-10-21; the TeamSize choice is a stub until R-241-03 scaling); no open flag | `epics/E-19-multiplayer.md` S-241 |
| S-242 | E-19 | "My building, scheduling and requests reach my partner as commands like any other." | Design decided 2026-10-02, not scheduled; no open flag | `epics/E-19-multiplayer.md` S-242 |
| S-243 | E-20 | "The era pack checklist names what the economy and the landscape need." | Design decided 2026-10-02, not scheduled; Q-243-01, Q-159-08, Q-146-02, Q-146-03 | `epics/E-20-multi-era-and-monetization.md` S-243 |
| S-244 | E-21 | "The names and teaching text for the economy come from the same pipeline as every other library." | Design decided 2026-10-02, not scheduled; Q-244-01 | `epics/E-21-offline-ai-pipeline.md` S-244 |
| S-245 | E-16 | "I report a bug or leave feedback from the game or the website, with the last seconds captured, and it reaches a queue a model works through." | Design direction 2026-10-06, not scheduled; Q-245-01 to Q-245-03 | `epics/E-16-client-camera-hud-and-world-view.md` S-245 |
| S-246 | E-17 | "In space each layer is a sheet of open and blocked space with real obstacles filling it, and the layers sit visibly apart." | Design decided 2026-10-07, not scheduled no open flag | `epics/E-17-map-generation.md` S-246 |
