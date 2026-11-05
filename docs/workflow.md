# Workflow — the per-epic pipeline

How a session runs under the north star. Read `CLAUDE.md` first, then `docs/northstar/README.md`; this file is the how-to for one cycle. `docs/northstar/PLAN.md` is canonical where the two disagree.

## Who does what

- **Claude (day-side, a human present)** designs: epic files, the ambiguity register, end-to-end definitions, sprint plans, and the fenced tests. Claude never runs in an unattended path (Agora D16).
- **Agora (night-side, unattended)** builds Tested stories against the fenced tests, runs T1 state QA and T2 visual QA, and escalates to a flag file when stuck.
- **Westley** answers flags, supplies references, confirms scale numbers, merges, and decides on escalations.

## One cycle for one epic

1. **Stage 2 gate.** The epic file exists and has run the definition-completeness gate (`docs/northstar/agile.md`). Every implied behavior is a `Q-` flag in `docs/northstar/ambiguity_register.md`; every visible-surface story has a reference in `docs/bible/references/E-##/`.
2. **Flags answered.** Westley answers the epic's flags in the register. Each answer becomes a rule in the epic file; the flag row stays with its answer. Zero open flags for the epic.
3. **Stage 3, end-to-end definition.** `docs/northstar/e2e/E-##.md`: full input and output space, edge cases, scale gates with numbers Westley confirmed, R4 bug watch-fors assigned to T1 or T2, failure evidence to capture. Exit is the Definition of Ready.
4. **Stage 4, roadmap.** The epic's stories are placed on the ladder in `docs/northstar/roadmap.md` and the product backlog `docs/legacy/agora_era/backlog.md`; a sprint file `docs/northstar/sprints/S##.md` names stories, dependencies, tests, scale gates, QA tier, Agora task stubs, exit criteria, and budget.
5. **Stage 5, tests.** Claude writes the failing tests in fenced paths: C unit and equation tests, invariant and trajectory tests, scale benchmarks, T1 scenarios with positive controls, T2 director missions, contract tests. Every test names its `S-###`/`R-###-##`. Story status becomes Tested.
6. **Derive rules.** `scripts/derive_agora_rules.py` writes `~/Projects/agora/projects/ouroboros/rules/E-##.md`. It refuses any epic with an open flag.
7. **Queue.** One Agora task per story, `acceptance:` = the test commands, bounded by `max_impl_lines`. Status Queued, then Building.
8. **Build and QA (Agora, unattended).** Worker iterates to green; QA runs on every task; stalls climb the escalation ladder; spirals halt and write `docs/northstar/ESCALATION.md`.
9. **Merge.** Human merge gate. Status Built. The stale-doc tripwire runs on the PR.
10. **Change protocol** when a story turns out wrong: rewrite the story and rules, update catalog and backlog, revise tests, respec or park the task, regenerate the rules file, one PR.

## Sizing

One task is one story and fits Agora's `max_impl_lines` (250). If a story cannot fit, split the story in the epic file, never in the queue.

## Git

- Branch `wn/<type>-<slug>` off `main`, `type ∈ {bug, feat, refactor, chore, docs}`.
- Plain git and `gh`. PR against `main`. Westley merges.
- Never commit on `main`. Guardrails: `.claude/settings.json`, `.claude/hooks/git-guard.sh`.
- One PR carries one epic's design pass, or one story's tests, or one change-protocol pass. No umbrellas.
- Commit and push each meaningful unit of ledger, register, or epic work; Westley reads on GitHub.

## Testing rigor

Both levels for every system: isolation (system alone, everything else fixtured) and integration (realistic scene). List every actor and variable in the scene; prove the fixture before asserting on the system; a failing assertion is a system bug only when the fixture is proven clean. Never loosen an invariant to pass; narrowing scope is allowed, widening thresholds needs Westley.

## Escalation

Agora: retry within `max_iterations`; stall at 3 identical failures escalates to DeepSeek (reorganize or solve-direct); spiral signals halt the task, park it, and write the flag file with English summary, failing output, diff, run ids, seed, screenshots. Westley opens Claude and decides: respec, split, revert, or start over. An opt-in `/loop` watcher is documented and off by default.

Claude, in a session: one targeted iteration after a failed confirmation; if it still fails, write up findings and stop.

## Sub-agents

Implement, never design. Cannot edit `docs/bible/**`, `docs/northstar/**`, `CLAUDE.md`, or test thresholds. Caveman directive appended to every sub-agent prompt (see `CLAUDE.md`).

## Reference files

- `CLAUDE.md` — rules of the road
- `docs/northstar/README.md`, `PLAN.md`, `principles.md`, `agile.md`
- `docs/northstar/ambiguity_register.md` — every open question
- `docs/bible/game_bible.md`, `stories.md`, `epics/`, `references/`, `algorithms.md`
- `docs/northstar/research/` — R1 to R4 briefs
- `docs/northstar/proving_ground/` — Stage 0 probes and scorecard
- `docs/architecture.md` — transport shapes and engine internals
