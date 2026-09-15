# E-16 Client Camera, HUD, and World View — Look and behavior references

**Not literal.** Ouroboros will not copy any game below. Read the aspect each shot pins, not the art.

**For test-writers and build models:** "Proves / contrast" names the story the shot grounds and what to check the current build against. If the build does not read like the Aspect cell for that story, that is a finding to raise, not a pass.

## Provided shot (Westley, 2026-09-13)

| # | Story | File | Source | Aspect — the example | Not wanted | Proves / contrast |
|---|---|---|---|---|---|---|
| 01 | S-104 | `E-16.png` | IMMORTAL: Gates of Pyre (IGoP, alpha footage) | The tactical HUD shape: segmented resource bars top-left, minimap bottom-left, a command card (train/tech/build/power) bottom-center with hotkeys, a selected-unit panel bottom-right | the sci-fi/Brood art, exact icons | HUD tells the player what is needed and nothing else; confirms the "IGoP HUD" the bible cites |

## TBD — design phase, not a screenshot

The **main menu, galaxy map, and strategic-to-tactical transition** are not referenced from other games. Westley does not yet know the exact look; these get a design phase (Claude builds simple mockups / a prototype to interact with — a prototype, not the final version). The original in-game UI "looked nice" and is the starting point. The existing in-game galaxy view already has good animation and is reused for E-09 (see `references/E-09/notes.md`), captured 2026-09-14 as `references/E-09/time_jump_galaxy_and_scroll.png`.

- S-106, S-107 galaxy map — reuse existing in-game galaxy view; reference `references/E-09/time_jump_galaxy_and_scroll.png` (captured 2026-09-14).
- S-110 main menu — reuse the existing in-game menu; reference `main_menu.png` (captured 2026-09-14): title in a serif face over a slowly turning particle galaxy with one bright core, a left-aligned monospace list (New Game, Continue, Era Library, Settings, Quit), studio line above the title, version bottom-right. Round 1 keeps this shape. Not wanted: Westley to add one sentence.
- S-108 seamless transition — design phase.
- S-110 main menu and settings — design phase; original UI is the baseline.
- S-103 tactical camera — design phase with the E-01 layer prototype.
