# Agile Method — Epics, Stories, Rules, Flags

The project uses an agile method so requirements can change while Agora builds. This file defines the requirement hierarchy, the ID scheme, the story template, the change protocol, the definition-completeness gate, and the Definition of Ready.

## Hierarchy

| Level | ID | What it is | Lives in |
|---|---|---|---|
| Epic | `E-##` | A feature area (Layer System, Fog and Vision, Faction Agents). One file. | `docs/bible/epics/E-##-<slug>.md` |
| Story | `S-###` | One user-facing behavior in the user's words. One row in the catalog, one section in its epic. | `docs/bible/stories.md` and the epic file |
| Rule | `R-###-##` | One acceptance criterion for a story, Given/When/Then. Maps to at least one test. | epic file |
| Ambiguity flag | `Q-###-##` | An open question on a story, marked `[NEEDS WESTLEY]`, with candidate answers. Blocks Ready. | `docs/northstar/ambiguity_register.md` |
| Reference | none | A screenshot, clip, or note about a similar game showing how a story should look or behave. | `docs/bible/references/E-##/` |

IDs are stable for life. A killed story keeps its ID with status Killed in the catalog so tests, tasks, and history still resolve.

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
References: references/E-07/notes.md, item 2.
Ways this could be wrong: visibility identical across layers; cone drawn but set unchanged; set changes but fog render does not.
Open flags: none.
```

Rules use concrete values, never adjectives. "Sees further" is not a rule; "sees at 14, not at 8" is.

## Status vocabulary

Story status in `stories.md` and the backlog: Spec'd (written, gate not run), Ready (gate passed, flags empty, references attached), Tested (tests written and red), Queued (Agora task exists), Building (Agora worktree active), Built (merged, tests green), Revised (built, then the story changed; goes back to Spec'd for the changed rules), Killed.

## Definition-completeness gate (Stage 2 exit per epic)

Recorded at the top of the epic file as a checklist with a date.

- Every story has at least one rule; every rule is Given/When/Then with concrete values.
- Every input a player or the sim can produce is listed with its range and its rejection behavior.
- Every output is listed with where it is observable: state field, screen region, chronicle, save.
- Anything the epic implies but does not state is turned into a `Q-###-##` flag, not left implicit.
- Every visible-surface story has a reference.
- The epic names what "obviously working" looks like in a 60-second play session, in plain words, so T2 QA has a target.

If the gate produces no flags on a non-trivial epic, the gate was run too loosely. Re-run it.

## Definition of Ready (Stage 3 exit, Stage 5 entry)

A story is Ready when all of:

- Its epic passed the completeness gate.
- The e2e file for its epic has no empty section.
- Every input and output is mapped.
- The ambiguity register has zero open flags for the story.
- Scale gates have numbers Westley confirmed.
- Every visible-surface story has a reference.
- R4 watch-fors are assigned with a tier (T1 or T2).

Only Ready stories get tests. Only Tested stories get queued.

## Change protocol

When a requirement changes, whether by Westley's call or because a build revealed the story was wrong:

1. Rewrite the story and its rules in the epic file. Delete the old text; do not annotate it.
2. Update the catalog row and backlog status to Revised, then Spec'd for the changed rules.
3. Claude revises the tests. Tests that no longer match a rule are deleted or rewritten in the same pass.
4. The Agora task is respec'd, or parked and re-queued with the new acceptance commands. The old `agora/` branch is discarded.
5. `scripts/derive_agora_rules.py` regenerates the epic's rules file for Agora.
6. One PR carries all of the above. The bible never lags the tests; the tests never lag the bible.

## Sizing

One Agora task is one story and must fit Agora's `max_impl_lines` (250 at time of writing). If a story cannot fit, split the story in the epic file, never in the queue.

## Ambiguity handling

Any question Claude cannot answer from the epic file, the references, or `vision_v2.md` becomes a `Q-###-##` in the register with the concrete question and two or three candidate answers. Claude never picks silently. Flags are batched and presented to Westley per epic. Local models never see an open flag; the rules-derivation script skips epics with open flags.
