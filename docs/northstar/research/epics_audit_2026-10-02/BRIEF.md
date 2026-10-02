# Epics and stories audit, 2026-10-02: brief

Westley, 2026-10-02: "after we finish the 5 goals, we're going to do some work on the epics/stories. We'll audit what exists against the recent ce07e919 commit and combat/movement decisions, and design new stories/epics based on the new batch of decisions that we made during this chat."

This audit is the first half: find where the existing bible disagrees with, or has no place for, two sets of decisions. Designing the new stories comes after and is the architect's job, not the auditor's.

## The two decision sets to audit against

**Set L: layer, combat and movement decisions** (commit ce07e919 and what it records).
- `docs/northstar/research/layer_dynamics/README.md`, all of it; sections 2 (the principle), 3 (five skills and their plays), 4 (the measure), 6 (layer rulings in force), 7 (what the engine lacks) matter most.
- `docs/northstar/research/layer_dynamics/LEAVE_OFF.md`.
- `docs/northstar/plans/2026-10-02-tactical-port-parity-requirements.md` (P1 to P9) and `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` if they exist.
- The canonical rules: `docs/bible/epics/E-01-layer-system.md`.

**Set E: economy, base and landscape decisions** (2026-10-01 and 10-02).
- `docs/northstar/research/economy_design/current_system.md` (read first).
- `docs/bible/epics/E-19-multiplayer.md`, story S-159, rules R-159-01 to R-159-21.
- `docs/bible/epics/E-17-map-generation.md`, story S-166, rules R-166-01 to R-166-06.
- `docs/bible/game_bible.md`, "The Player's Toolkit" and "Reference Hardware" (the long-term scale goal).
- `docs/northstar/research/economy_design/README.md` holds Westley's words verbatim, round by round, if a rule's meaning is unclear.

## What to look for, in the epics assigned to you

For every story and rule (`S-###`, `R-###-##`), the Inputs, Outputs, Invariants, Scale requirements, "Ways this could be wrong" and "Depends on" sections:

- **CONTRADICTS**: the text says something a decision in Set L or Set E makes false.
- **STALE**: the text is not false but describes a world the decisions have moved on from (a number, a scope, an assumption, a name).
- **MISSING**: a decision needs something from this epic that the epic has no story or rule for.
- **TOUCH**: the epic is affected and will need a pointer or a small edit, nothing more.

Known going in, to confirm and extend, not to rediscover: E-15 S-126 and S-127 (garrisons produce free units; now strongpoints on height-band slopes paid for by the economy); E-10 S-077 (no rule for the partial-failure cap after losing the original main base); E-17 S-112 to S-119 (hand-authored layout library and old canvas, against terrain-first generation and S-166); E-01 (elevation mapping "fixed globally" against height bands fitted per map); the hub's "The player does not manage an economy or build a base" paragraph; E-14 (enemy economy now on shared rules with optional foresight).

## What to write

One file, the path given in your task, with:

1. A findings table: `| Epic | Story or rule | Class | What the bible says (short quote, with line number) | Which decision it meets (file and rule id or section) | What kind of change it needs |`. The last column names the kind only: rewrite the rule, add a rule, add a story, add a flag, add a pointer, remove. Do not write the new rule.
2. A short list, "Decisions with no home in these epics": decisions from Set L or Set E that belong in one of your epics and have no story there.
3. A short list, "Things I could not judge", with why.

Rules for you: read-only on everything except your one output file. Do not edit the bible, the register, tests or code. No git commands. Do not design, recommend or rank. Quote, do not paraphrase, when stating what the bible says. Plain prose in the file. Do not spawn sub-agents. Report once at the end, caveman-terse, eight lines at most: counts per class and the three most serious findings.
