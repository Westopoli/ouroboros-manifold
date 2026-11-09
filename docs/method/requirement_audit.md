# Requirement audit

Weekly. It answers two questions for every rule in scope: does the rule as written agree with the bible, and does the test its Proof line names truly enforce it on today's lab and beta. Written 2026-11-09 (DEC-rule-proof-pointers-2026-11-09); the reason is `docs/reports/2026-11-07-rule-enforcement.md`.

## When and who

Westley says **audit**; the Architect chat starts it. The auditors are fresh Sonnet 5.5 agents, `subagent_type: engineer`, one per slice of about one epic, that have not seen the author's reasoning. An auditor reads this card, then `requirements.md` Proof, then its slice. It edits nothing, commits nothing, spawns nothing, and reports once.

## Scope of one run

- Every rule added or changed since the last run: `git log --since=<last run> -p -- docs/bible/epics`.
- Every rule the current lab stage and the current beta stage name (`docs/northstar/story_reviews/westley/lab-staircase.md`, `beta-staircase.md`).
- One rotating epic, E-01 to E-22 in order, whole.

## Half 1: the rule against the bible

For each rule, with file and line for anything that fails:

- It agrees with the hub (`docs/bible/game_bible.md`), `docs/bible/algorithms.md`, its epic's Invariants, every rule it cites, the closed `Q-` rows and `decisions.md`. Where two texts disagree, both are quoted; the auditor does not pick.
- A rule whose text changed since the last run quotes Westley's words or a `DEC-` row, and the diff changes no more than those words require.
- Given, When and Then carry concrete values; every number is Westley's or a named `DRAFT-`.
- Every named thing (a place, a structure, a unit kind, a state) has a bible source. A term with none is reported.

## Half 2: the proof against the rule

For each Proof line, at `origin/main`, with the sha in the report:

- The pointer resolves to a test function, and the test quotes the rule's text as it reads today.
- The six qualifications of `requirements.md` Proof, one by one. The one that fails is named.
- The test is run and is green. It is not skipped, xfail or known-red.
- Its configuration is set beside the lab's and the beta's current launch settings, read from the files that launch them (`scripts/skilllab/`, `scripts/play.sh`), never from memory. Each switch that differs is listed.
- Where a control or a recorded break exists, it is run and turns the test red. Where none exists, the row says so.
- Where the lab's whole-run rule checker covers the rule, its latest result on main is quoted.

A rule with `Proof: unbuilt` is checked for code that implements it after all; a rule with `Proof: MISSING` stays MISSING.

## Report

`docs/reports/YYYY-MM-DD-requirement-audit.md`, one row per rule:

```
PROVEN         | R-###-## | <test file>::<test name> | <sha>
WEAK           | R-###-## | <file:line> | qualification <n>: <what fails>
MISSING        | R-###-## | <code file:line that implements it>
STALE          | R-###-## | <file:line> | pointer or citation that no longer resolves
BIBLE-CONFLICT | R-###-## | <file:line> and <file:line> | both texts, short
```

The chat carries the summary for Westley: how many rules, how many proven, what is unproven in the active stages, what disagrees with the bible.

## After

The Architect sets `verified <sha> <date>` on the PROVEN rows, rewrites every other Proof line to the state found, raises a `Q-` row for each conflict that is Westley's to settle, and puts the test work first in the next plan. A rule of an active stage that is not PROVEN blocks that stage's sign-off.

## Log

Last run: none yet (the first follows the backfill, H-090). Next rotating epic: E-01.
