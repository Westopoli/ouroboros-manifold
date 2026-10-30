# Requirements

Stories are the north star. Nothing is built that is not a story, and a story is built only when it is Ready.

## Hierarchy

| Level | ID | What it is | Lives in |
|---|---|---|---|
| Epic | `E-##` | A feature area, one file | `docs/bible/epics/E-##-<slug>.md` |
| Story | `S-###` | One player-facing behaviour in the player's words | `docs/bible/stories.md` (one row) and the epic file (one section) |
| Rule | `R-###-##` | One acceptance criterion, Given/When/Then with concrete values, mapped to at least one test | the epic file |
| Flag | `Q-###-##` | An open question with two or three candidate answers; blocks Ready | `docs/northstar/ambiguity_register.md` |
| Reference | none | A clip, shot or note from another game showing how a story should look or feel | `docs/bible/references/E-##/` |
| Harness story | `H-###` | Work on the method or the tooling, same columns as a story | `docs/method/harness.md` |

IDs are stable for life. A killed story keeps its row with status Killed.

## Story template

```
### S-042 — Units on different layers see differently
As a commander, I want a unit's layer to change what it can see, so that choosing a layer is a real tactical decision.

Rules
- R-042-01  Given a Line unit on layer 2 and an enemy on layer 1 at distance 8, When one tick passes, Then the enemy is in the unit's visible set.
- R-042-02  Given the same units at distance 14, When one tick passes, Then the enemy is not in the visible set.

Inputs: layer command (1..3), unit position, enemy position, fog state.
Outputs: visible set per unit in the tick delta; HUD vision cone; fog reveal on screen.
Scale: 1,000 units computing visibility in under 2 ms per tick.
Scene: scenes/tactical/tactical.tscn --seed 7 --story S-042 (the state Westley plays).
References: references/E-07/notes.md, item 2.
Ways this could be wrong: visibility identical across layers; cone drawn but set unchanged.
Open flags: none.
```

Rules use concrete values, never adjectives. "Sees further" is not a rule; "sees at 14, not at 8" is.

## Status

Spec'd (written), Ready (below), Tested (landed on main with its tests green, the game opened and the scene reached by the clerk), Revised (built, then changed; back to Spec'd for the changed rules), Killed, Seen (Tested, and Westley approved the scene). In flight is not a status: it is the branch `s/S-###-*` on origin.

## Definition of Ready

- Every rule is Given/When/Then with concrete values; every input has its range and rejection behaviour; every output says where it is observable.
- The epic names what "obviously working" looks like in sixty seconds of play, and its visual end-state in player-story framing ("the player sees X, which tells them Y"), or says "none direct" and names the epic that renders it.
- The register has no open flag for the story.
- Every threshold, tolerance and scale number was given by Westley or is a named `DRAFT-` with a register row.
- Every visible-surface story has a reference and names its scene (the run line that puts the game in the story's state).
- If the Architect marked the story "prototype: needed", the prototype is approved and its record is linked.

Only Ready stories get specs; only stories with red tests get builders.

## Prototype gate

Anything judged by eye or feel (how a thing looks, moves, lays out or plays) is prototyped before it is specified; wiring, refactors and rules whose numbers are confirmed are not. The Architect marks the story; Westley can overrule either way. A mockup is a Godot scene under `scenes/mockups/` for things he must play; an instrument is a harness under `scripts/` or `toys/` that runs the rule and prints charts for things he must read. One pass is a spec under a page, one builder, the scene or the page committed, Westley plays or reads it, his words recorded verbatim with the Architect's reading. Three passes without approval stop the passes: the Architect writes an options page with two or three directions. A prototype may skip determinism, budgets, tests and polish; it is never loaded by the game; it reports what it costs. Approval is recorded verbatim in `docs/northstar/research/<topic>/README.md`, his decisions become rules in the epic, and the game code is then built fresh, tests first; the prototype is a reference, not a source.

## Flags

A question the Architect cannot answer from the epic, the references, `docs/bible/algorithms.md` or a closed register row becomes a `Q-` row with the concrete question and two or three candidates, one marked `[recommended]` when there is a safe default. Westley answers "approve defaults" for a batch or overrides by id (`Q-021-01: c`). A flag with no safe default carries no marker and waits for his pick. Trivial choices (a strict versus inclusive comparison, a tie-break order, an internal constant with no design intent) the Architect decides and writes into the rule text; if in doubt whether it is trivial, it is not. Rule meaning Westley has no recorded words on is his; everything else the Architect decides and records in `decisions.md`, and he may veto.

## Change protocol

When a requirement changes: rewrite the story and its rules in the epic (delete the old text; history is `git log`); set the catalog row to Revised, then Spec'd for the changed rules; the tests are rewritten in the same change; the story file under `docs/stories/` is rewritten; one commit carries all of it. The bible never lags the tests and the tests never lag the bible. A story that cannot fit 1,000 implementation lines is split in the epic, never in the queue.
