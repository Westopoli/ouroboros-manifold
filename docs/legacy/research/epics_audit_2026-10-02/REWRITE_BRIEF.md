# Bible rewrite, 2026-10-02: brief for drafters

Westley: "Old epics should be updated to be consistent with the new decisions."

You are drafting bible text against decisions already made. You do not design. The architect reviews every file before it is committed.

## Read, in this order

1. `docs/legacy/research/epics_audit_2026-10-02/BRIEF.md` (what the two decision sets are and where they live).
2. `docs/legacy/research/epics_audit_2026-10-02/DECISIONS.md` (Westley's answers to the audit's holes; these override anything older).
3. `docs/northstar/research/economy_design/current_system.md` and `docs/northstar/research/economy_design/README.md` (the economy as decided; his words verbatim by round).
4. The findings file for your epics, named in your task. Every row there is something to resolve.
5. The epics you own, in full.
6. One well-formed epic as the model of the format, for example `docs/bible/epics/E-21-offline-ai-pipeline.md`.

## Story numbers are allocated

Use only the numbers given to you. Rule ids are `R-<story>-<nn>`. Flags are `Q-<story>-<nn>`.

The new epic **E-22, Economy and bases** takes over the rules of E-19 S-159. Its stories, fixed so everyone can cite them:

| Story | Title | Takes over |
|---|---|---|
| S-167 | Resources and workers | R-159-03 |
| S-168 | Building and placement | R-159-04 (placement), E-17 R-166-03 (the city reshapes around a placed building) |
| S-169 | One population cap | R-159-05 |
| S-170 | Production and the schedule | R-159-06 |
| S-171 | Counters | R-159-07 (counters); unit families are the three categories |
| S-172 | Disguise | R-159-07 (disguise); Q-159-09 |
| S-173 | Technology | R-159-08; DECISIONS H4; Q-159-12 |
| S-174 | Defenses and raid lanes | R-159-04 (defenses) |
| S-175 | Expansions and forward bases | R-159-09 (expansions, forward production) |
| S-176 | Shipments | R-159-11 |
| S-177 | Bases, resources and the situation | R-159-09 (base of operations), R-159-10, R-159-15, R-159-16; Q-159-14 |
| S-178 | When a base falls | R-159-14; DECISIONS H11 |
| S-179 | The economy without a player | R-159-02, R-159-18 |
| S-180 | The commander alone | R-159-19, R-159-20 |
| S-181 | The enemy's economy | R-159-21 |
| S-182 | What carries forward | R-159-13; Q-159-07, Q-159-13 |

S-159 stays in E-19 as the paired mode itself (R-159-01, team sizes, the universe lock, drop-out). Strongpoints (R-159-17) and moving weather (R-159-12) are rewritten into E-15. Cite E-22 stories by story number (for example "E-22 S-170"), not by rule number, since rule numbers are being assigned now.

Other allocations: E-17 uses S-166 and S-186 to S-199. E-01, E-11, E-12, E-13 use S-200 to S-209. E-10, E-14, E-15 use S-210 to S-219. E-02 to E-08 use S-220 to S-229. E-16, E-18, E-19, E-20, E-21 use S-230 to S-245.

## Rules for the text

- **Rewrite, never append.** The bible says what the game is. No history, no "previously", no narration of the change. The one exception is below.
- **Rules that are built and tested stay as they are.** Before changing any existing rule, run `grep -rl "R-###-##" tests/ csrc/ scripts/ 2>/dev/null`. If anything cites it, leave the rule's text untouched, put one line under the story heading in this form: "Direction changed 2026-10-02, rewrite pending: <one sentence on the decided direction, citing the story that holds it>. The rules below are what the game does today." and list the rule in your sidecar under "Needs a ledger row". If nothing cites it, rewrite it outright.
- **Format.** Keep each epic's sections: the gate table, Purpose, Obviously working in 60 seconds, Stories, Inputs, Outputs, Invariants, Scale requirements, references, Ways this could be wrong, Open ambiguity flags, Depends on. A story is `### S-### — <title>`, one sentence "As a ..., I want ..., so that ...", then `Rules`, each `- R-###-##  Given ..., When ..., Then ...`, then `Inputs:`, `Outputs:`, `Open flags:`.
- **Never invent a number, a threshold, a tolerance, a name or a mechanism.** Westley owns them. Where a decision gives a number, use it. Where it does not, write the rule with the number left to a flag, in the form `[Q-###-##: what is needed]`, and put the flag in your sidecar with two or three candidate answers. An epic with an open flag is not built; that is expected here.
- **Never guess past a decision.** If the decisions do not say, flag it. Do not fill the gap with what seems reasonable.
- **Quote Westley only from the files above**, exactly, and only where a rule's meaning rests on his words.
- **Status.** Everything from the economy and landscape decisions is "design decided, not scheduled for building". Say so once per story or epic, not per rule.
- **Space.** The space-era landscape is not designed (Q-166-02). Write no stories for it. Rules about ground, height bands, slopes, walking units and strongpoints apply to land maps; say so where it matters, and point at Q-166-02.
- **No IP.** No names, places or plot from existing fiction. Other games may be named as references, as the bible already does.
- **Prose.** Plain, complete sentences. No em dashes used as asides, no semicolon chains.

## What you must not touch

Tests, code, `docs/bible/stories.md`, `docs/northstar/ambiguity_register.md`, any epic not named in your task, and anything under `tests/`. No git commands. Do not spawn sub-agents.

## Your sidecar

Write `docs/legacy/research/epics_audit_2026-10-02/sidecar_<your name>.md` with:

1. **Catalog rows** for `stories.md`, one per new or retitled story: `| S-### | E-## | "<one-line summary in the player's voice>" | <status and flags> | <file and anchor> |`.
2. **Register rows** for every new flag: `| Q-###-## | E-## / S-### | <question> | <candidates> | open | |`.
3. **Flags to close**, with the decision that closes each.
4. **Needs a ledger row**: tested rules whose direction changed.
5. **Findings resolved**: for each row of your findings file, one of: done (where), flagged (which Q), left (why).
6. **Could not do**, with why.

Report once at the end, caveman-terse, eight lines at most: stories added, rules rewritten, flags opened, tested rules left with a note, anything you could not do.
