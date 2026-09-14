# E-12 Fog and Sensors — Look and behavior references

**Not literal.** Ouroboros will not copy StarCraft. These two shots pin the three fog states we want; read the state each shows, not the art.

**For test-writers and build models:** "Proves / contrast" names the story the shot grounds and what to check the current build against. If the build does not read like the Aspect cell for that story, that is a finding to raise, not a pass.

## Provided shots (Westley, 2026-09-13)

| # | Story | File | Source | Aspect — the example | Not wanted | Proves / contrast |
|---|---|---|---|---|---|---|
| 01 | S-092, S-094 | `Unexplored.png` | StarCraft (Brood War) | Never-explored space is pure black; only the small bubble the units currently occupy shows terrain | the exact tile art / creep | before any unit has been somewhere, that place is black, not dim |
| 02 | S-094, S-089 | `ExploredButWithoutVision.png` | StarCraft II | The left side is explored but has no current vision: landscape is darkened yet still visible, and the enemy building stays drawn, but no enemy units are shown there | the SC2 tileset itself | remembered terrain and static structures persist dimmed; moving units do not |

## Derived rule — three fog states

1. **Never seen:** pure black. No terrain, no structures.
2. **Explored, no current vision (remembered):** terrain and enemy **buildings** visible but darkened; enemy **units** are not shown (their last-known position is stale and hidden).
3. **Current vision:** full brightness; everything shown.

## Decision to record — fog-memory toggle (Westley, 2026-09-13)

A separate player option (a checkbox) turns memory **off**: with it on, there is no remembered landscape at all — anywhere the player does not currently have unit vision is just **black**, structures included. Default is memory-on (the three-state model above); the checkbox is the hardcore no-memory mode.

→ Needs a story in E-12 (fog-memory toggle, a setting on S-094). Recorded here as a confirmed decision so it is not lost; fold into the epic at Stage 3.
