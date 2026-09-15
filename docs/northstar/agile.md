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
- The epic names what "obviously working" looks like in a 60-second play session, in plain words. This is the seed of the epic's technical end-state (see below) and T2 QA's first target.

If the gate produces no flags on a non-trivial epic, the gate was run too loosely. Re-run it.

## End-state — done looks like this (authored before queue)

Before an epic's stories may be queued for Agora, the epic states, in one place, what the finished epic looks like when it is done — both technically and visually. This is not a per-story acceptance criterion (that is what rules are); it is the whole-epic target the tests and QA aim at, written by Claude or the design chat while the epic is still on paper. It exists so that testing has a destination and the build has a picture to converge on, not just a list of rules to satisfy.

Two required parts, both in the epic file:

- **Technical end-state** — the "Obviously working in 60 seconds" section. What is true in state, traces, data shapes, determinism, and performance when the epic is done: the trajectories a fixed-seed run produces, the checksums that must match, the perf numbers that must hold, the trace facts a T1 run can read. Concrete values, no adjectives. The derivation script feeds this to Agora; the local models build toward it.
- **Visual end-state** — the `## Visual end-state` section. What the player sees on the finished screen and what it tells them, in player-story framing ("the player sees X, which tells them Y"), not a layout spec. This is T2 QA's target and the ground truth the epic's references illustrate. An epic with no player-facing surface of its own says so explicitly and names the epic that renders its state (for example, "None direct — region fields surface in the E-16 world view; this epic produces no pixels of its own"). "None" is a valid answer only when stated on purpose; a blank section is not.

Both parts are finalized at Stage 3, before the epic can be Ready. A visible-surface epic whose visual end-state is still empty is not Ready and is not queued.

## Definition of Ready (Stage 3 exit, Stage 5 entry)

A story is Ready when all of:

- Its epic passed the completeness gate.
- The epic's end-state is written and complete: the technical end-state has concrete values, and the visual end-state is authored (or explicitly "none direct" naming the epic that renders it).
- The e2e file for its epic has no empty section.
- Every input and output is mapped.
- The ambiguity register has zero open flags for the story.
- Scale gates have numbers Westley confirmed.
- Every visible-surface story has a reference.
- R4 watch-fors are assigned with a tier (T1 or T2).

Only Ready stories get tests. Only Tested stories get queued.

## Change protocol

When a requirement changes, whether by Westley's call or because a build revealed the story was wrong:

1. Rewrite the story and its rules in the epic file. Delete the old text; do not annotate it. If the change moves the target, rewrite the epic's end-state (technical and visual) to match; a stale end-state is a stale-doc-tripwire failure.
2. Update the catalog row and backlog status to Revised, then Spec'd for the changed rules.
3. Claude revises the tests. Tests that no longer match a rule are deleted or rewritten in the same pass.
4. The Agora task is respec'd, or parked and re-queued with the new acceptance commands. The old `agora/` branch is discarded.
5. `scripts/derive_agora_rules.py` regenerates the epic's rules file for Agora.
6. One PR carries all of the above. The bible never lags the tests; the tests never lag the bible.

## Sizing

One Agora task is one story and must fit Agora's `max_impl_lines` (250 at time of writing). If a story cannot fit, split the story in the epic file, never in the queue.

## Ambiguity handling

Any question Claude cannot answer from the epic file, the references, or `vision_v2.md` becomes a `Q-###-##` in the register with the concrete question and two or three candidate answers. Claude never picks silently. Flags are batched and presented to Westley per epic. Local models never see an open flag; the rules-derivation script skips epics with open flags.

Before a flag is raised, Claude checks that it is not already answered: `docs/bible/algorithms.md` (constants and equations kept verbatim in Stage 1), the Stage 1 ledger verdicts in `stage1_audit.md`, and closed rows in the register. A flag that duplicates one of these is a defect in the flag, not a question for Westley.

**Trivial decisions (Westley, 2026-09-14).** When the candidates differ only in a way no player would notice and no other story depends on (a strict versus inclusive comparison, a tie-break order, an internal constant with no stated design intent), Claude decides, writes the rule, and records the choice in the epic's rule text with no flag. If in doubt whether a choice is trivial, it is not.

### Register protocol v3 (2026-09-14)

Every flag's candidate-answers column names one candidate as **recommended** — Claude's best guess at the answer, marked inline (e.g. `(b) [recommended] ...`). Westley answers a batch one of two ways:

- **"Approve defaults"** — every recommended candidate in the batch becomes the answer, in one line, no per-flag typing.
- **Override by id** — `Q-021-01: c` (or free text) answers that one flag differently; every other flag in the batch still takes its recommended default.

This does not lower the bar for what counts as a genuine flag (still: never guess, never pick silently) — it lowers the cost of answering once Claude has already formed a recommendation. A flag with no safe recommendation (a real fork with no clear default, or one where guessing wrong is expensive) carries no `[recommended]` marker and needs Westley's explicit pick regardless of "approve defaults."

Folding an answer into the epic's rule text is transcription once the answer is a clean letter-pick whose candidate text is itself sufficient rule content; `scripts/specfactory/fold_answers.py` handles that mechanically. A closed answer that implies new rule content beyond its candidate phrasing (a design decision, not a restatement) stays Claude's to fold by hand, optionally with an `agy` draft first — and if folding it surfaces a *new* gap the candidate didn't cover, that gap is a new flag, not a guess (see the E-03 Q-021-01/Q-021-03 pair, `docs/northstar/spec_factory.md`, for a worked example).
