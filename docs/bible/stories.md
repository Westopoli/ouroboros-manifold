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
