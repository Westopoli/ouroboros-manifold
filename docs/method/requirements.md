# Requirements

Stories are the north star. Nothing is built that is not a story, and a story is built only when it is Ready.

## Hierarchy

| Level | ID | What it is | Lives in |
|---|---|---|---|
| Epic | `E-##` | A feature area, one file | `docs/bible/epics/E-##-<slug>.md` |
| Story | `S-###` | One player-facing behaviour in the player's words | `docs/bible/stories.md` (one row) and the epic file (one section) |
| Rule | `R-###-##` | One acceptance criterion, Given/When/Then with concrete values, carrying a Proof line once built (Proof, below) | the epic file |
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
  Proof: tests/csim/test_E01_S042_layer_sight.py::test_enemy_at_8_is_visible | scenario | verified 1a2b3c4d 2026-11-09
- R-042-02  Given the same units at distance 14, When one tick passes, Then the enemy is not in the visible set.
  Proof: unbuilt

Inputs: layer command (1..3), unit position, enemy position, fog state.
Outputs: visible set per unit in the tick delta; HUD vision cone; fog reveal on screen.
Scale: 1,000 units computing visibility in under 2 ms per tick.
Scene: res://scenes/tactical/tactical.tscn --seed 7 (the state Westley plays; copied into the story file).
References: references/E-07/notes.md, item 2.
Ways this could be wrong: visibility identical across layers; cone drawn but set unchanged.
Open flags: none.
```

Rules use concrete values, never adjectives. "Sees further" is not a rule; "sees at 14, not at 8" is.

## Proof

A rule that code implements points at the one test that enforces it. Written 2026-11-09 after the stage 4 lab re-run showed rules that were written, built and green in tests, and broken in play (`docs/reports/2026-11-07-rule-enforcement.md`).

The pointer is its own line directly under the rule in the epic file, never on the rule line (rule pins hash that line):

```
  Proof: <test file>::<test name> | scenario, whole-run or client | verified <sha> <date>
  Proof: unbuilt        (no code claims the rule)
  Proof: MISSING        (code exists and no test qualifies)
```

Each bullet of an epic's Invariants section carries a Proof line too; a test cites it as "E-13 Invariant 2". A rule is built only when its Proof line names a test, and a story is Tested or Seen only when every one of its rules has one. `MISSING` and `unbuilt` are written out so that a gap shows in the epic.

A test qualifies as proof when all six hold:

1. It is one named test function that names the rule id and quotes the rule's current text. A mention of the id elsewhere in a file is not a proof.
2. It asserts the rule's Then, not that something happened nearby (hit points fell, a distance closed). A hash or golden is never a proof: it detects change, not a broken rule.
3. It runs in the shipped configuration, the settings the lab batch and `scripts/play.sh` launch today (walking units, obstacles, sight on), or the Proof line names the switch that differs and why.
4. A rule worded never, always or every tick, and every Invariant, is proved by a whole-run test that checks each tick of a fight, not the final state.
5. It goes red against wrong code: a filled control or a recorded break of the rule's code turns it red. A placeholder control does not count.
6. It is not skipped, not xfail and not on a known-red list. A known-red proof means the rule is unproven.

A `Test-defect:` commit that touches a proof test updates the `verified` sha, and never weakens a per-tick check to a final-state check without naming the invariant test that replaces it. The weekly check of rules and proofs is `requirement_audit.md`.

Backfill: all 22 epics receive Proof lines in one pass before further stage work (Westley, 2026-11-09; H-090).

## Status

Spec'd (written), Ready (below), Tested (landed on main with its tests green, every rule carrying a Proof line that names a test, the game opened and the scene reached by the overlord), Revised (built, then changed; back to Spec'd for the changed rules), Killed, Seen (Tested, and Westley approved the scene). In flight is not a status: it is the branch `s/S-###-*` on origin.

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

When a requirement changes: rewrite the story and its rules in the epic (delete the old text; history is `git log`); set the catalog row to Revised, then Spec'd for the changed rules; the tests are rewritten in the same change; the story file under `docs/stories/` is rewritten; one commit carries all of it. A rule that is reworded or renumbered moves its Proof line and the test's citation in that commit. A change to a rule's text quotes Westley's words or a `DEC-` row beside it and changes no more than those words require. The bible never lags the tests and the tests never lag the bible. A story that cannot fit 1,500 implementation lines is split in the epic, never in the queue.
