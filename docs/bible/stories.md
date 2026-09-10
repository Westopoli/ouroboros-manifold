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
