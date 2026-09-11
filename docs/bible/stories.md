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
| S-012 | E-02 | "Each region's condition is four plain numbers and two summaries." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-012 |
| S-013 | E-02 | "Garrisons decay when the region cannot pay for them and recruit when times are good." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-013 |
| S-014 | E-02 | "Economy grows with people, shrinks under unrest, and falls back when it outruns its population." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-014 |
| S-015 | E-02 | "A region next to a booming friendly region develops faster." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-015 |
| S-016 | E-02 | "Tension rises with hardship and burns itself out faster the higher it gets." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-016 |
| S-017 | E-02 | "Population is the slowest number: collapse feels permanent, recovery feels earned." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-017 |
| S-018 | E-02 | "Regions boom and bust on their own cycles, out of step with each other." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-018 |
| S-019 | E-02 | "A region that hits bottom stays barely alive but keeps hurting until someone helps." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-019 |
| S-020 | E-02 | "Same seed, same galaxy, on every machine." | Spec'd | `epics/E-02-region-fields-and-drift.md` S-020 |
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
