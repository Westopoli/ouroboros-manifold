# Spec factory

Reorganizes how a story goes from a closed register flag to a Tested test suite, naming the owner of every step and automating the transcription-class ones. Claude's role shrinks from writing every artifact to reviewing three diffs per epic (e2e, tests, card) and judging one Sonnet sub-agent's audit of the filled tests per story. `agy` (Antigravity CLI, `docs/northstar/research/gemini_compute.md`) is the drafting sub-agent; it never designs, never edits `docs/bible/**` or `docs/northstar/**` directly, and returns findings plus a proposed change on ambiguity, per `CLAUDE.md`'s sub-agent rules.

## Budget check before any model batch

Every runner that calls a model (`draft_e2e.py`, `fill_tests.py`, `draft_card.py`) refuses to start until `FACTORY_BUDGET` is set to `gemini` or `claude` (`scripts/specfactory/budget_gate.py`). Before setting it, the chat asks Westley for his current Claude usage and reads `agy`'s `/credits`. Rule from 2026-09-14: test authoring emptied Antigravity's Gemini five-hour window in about twenty minutes across two chats, so `gemini` is for short bursts only; `claude` means Claude Code Sonnet sub-agents on the Claude Max subscription, which Westley wants to see running in his terminal. Night-side Agora use of `agy` is a separate decision recorded on the `spec` tool when it exists.

## The pipeline

| Step | Owner | Automation |
|---|---|---|
| Write epic file, completeness gate, raise flags | Claude | none (judgment) |
| Answer flags | Westley | register protocol v3 (`agile.md`): every flag carries a recommended candidate; Westley answers "approve defaults" or overrides by id |
| Fold answers into rules | script for clean letter-picks; `agy` drafts free-text/design folds; Claude reviews and applies | `scripts/specfactory/fold_answers.py` |
| Draft e2e file | `agy` from the epic file and the e2e template; Claude reviews and owns the scale gates and end-state | prompt/schema TBD when the first e2e file is drafted this way |
| Confirm scale gates | Westley (numbers), Claude proposes | none |
| DoR check | script: every section non-empty, zero open flags for the epic, references present for visible-surface stories, scale gates dated | `scripts/specfactory/dor_check.py` |
| Test skeleton per rule | script emits one `def test_R_###_##_<slug>` per rule with docstring and fixture signature; `agy` fills arrange/act/assert from the rule's numbers and `conftest.py`'s helpers | `scripts/specfactory/gen_test_skeleton.py` |
| Positive controls | script emits one skeleton per "Ways this could be wrong" item, naming the `OM_BUG_*` enum member it expects | `scripts/specfactory/gen_controls.py` |
| Audit filled tests | one Sonnet sub-agent (Claude Code, Max sub — not `agy`) per filled test file; audits the filled bodies against the epic, e2e, ABI, and `algorithms.md`; returns a verdict + per-rule findings + escalations; never edits the suite; no file audited twice | `docs/northstar/spec_factory/prompts/audit_tests.md`; Claude spawns the sub-agent, no runner script |
| Red check | script runs pytest on the new files; every one must fail or error, none may pass | `scripts/specfactory/red_check.py` |
| Green check | script proves a reference implementation (`tests/csim/references/<card-id>.c`) flips a card's acceptance commands from failing to passing, applied inside a scratch git worktree at HEAD; refuses (exit 2) if acceptance already passes on the unmodified project | `scripts/specfactory/green_check.py` |
| Rules file | existing derivation script | `scripts/derive_agora_rules.py` (already scripted, unchanged) |
| Card | script for the YAML frontmatter (acceptance command, allowed files, rules_file, test_file); `agy` drafts the prose brief from the rules file only, never from tests (the E-02 finding: a brief written from tests leaks implementation instead of intent) | `scripts/specfactory/gen_card.py` |
| Run card, ledger | Agora, `build_ledger.py` | already scripted |
| Findings on a failed card | `agy` first pass from `report.md` and the diff; Claude decides | prompt TBD, needed once the first card runs |

## Claude's review checklist (per epic)

- The Sonnet audit runs first and hands you findings; your review judges them — accept the must-fix, escalate the real ambiguities into register flags, reject the noise — rather than re-deriving every test from scratch. The audit is one Sonnet sub-agent per filled file, never a second pass over the same file: at this test volume, TDD depth plus `red_check` catch what a second auditor would.
- Every rule has a test. Every number in a test traces to a rule, not to a guess.
- No generated test can pass today (`red_check.py` proves this mechanically; still read the failures — an error for the wrong reason, e.g. a typo'd fixture name, is not the same as a red test proving the rule is unbuilt).
- Controls invert a real, named fixture — not a strawman.
- The card brief names the rules file and cites no equation directly (equations live in `algorithms.md`; the brief points there).
- Nothing in the epic file is stale relative to the register (this is the stale-doc tripwire, and folding is exactly where staleness creeps in — see the E-03 run below).

## Fold classification: mechanical vs. design

`fold_answers.py` only ever removes a flag reference; it never writes rule content. The dividing line, in practice (from the E-03 run below):

- **Mechanical** — the closed answer confirms existing rule text, narrows scope of an existing rule, or defers something to a documented future story. Claude (or an `agy` draft Claude reviews) edits the rule text directly; `fold_answers.py --apply` then strips the flag reference.
- **Design** — the closed answer retires or replaces a mechanism the current rules describe, and applying it raises a question the candidate text does not answer (a genuine new fork, not implied by the letter picked). This is a new `Q-###-##` flag, not a guess, even though the flag that produced it is already closed. Closing a flag does not always finish the fold.

## First real use: E-03, 2026-09-14

E-03 (World Generation) was the first epic run through the factory, day-side, before the Agora `spec` tool exists. Register had 5 closed-but-unfolded flags (Q-021-01, Q-021-02, Q-022-01, Q-024-01, Q-025-01) referenced across S-021, S-022, S-024, S-025.

`fold_answers.py` surfaced all 5 with their letter pick, candidate text, and full answer in one pass (a few seconds; previously this meant re-reading the whole register by hand against the whole epic). Of those:

- **Q-024-01 and Q-025-01 folded clean** — Q-024-01 became a documented future-story note under S-024 (no new rule, no test yet); Q-025-01's fold caught that the epic's Purpose section and R-025-02 both stated a blanket "no home touches another home" rule that the actual answer (player-to-NPC only) contradicts — a stale-doc bug that predates this session, now fixed, plus a new rule (R-025-04) added for the extra-edge re-roll the answer implies.
- **Q-021-01 and Q-022-01 hit real design gaps.** Q-021-01 retires the generic per-faction generator for three named templates (Isolated, Twin Colony, Archipelago) from the retired `bible_2_00_world.md` spoke — but that retired design describes the templates as the *player's* shape, with NPCs placed around it, not a shape independently rolled by all 15 factions the current epic generates identically. Applying the answer raises a question its candidate text never addressed. Q-022-01 confirms per-archetype starting ranges, giving Conqueror's numbers as an example — but Fortifier's and Opportunist's ranges were never stated anywhere, bible or register. Both became new flags (Q-021-03, Q-022-02) rather than guessed answers, per the ambiguity rule. E-03 is not Ready: `dor_check.py E-03` reports exactly these 2 open flags plus an undated scale gate.

**Time.** Reading the register against the epic and doing the two clean folds by hand: about 20 minutes, versus E-02's precedent of doing this kind of pass across a whole session with no tool support. The two blocked flags could not have been resolved faster by any tool — they needed the retired-bible cross-reference and the missing-numbers check, which is exactly the judgment `CLAUDE.md` reserves for Claude.

**Scripts verified end to end**, all against real repo files (not fixtures): `fold_answers.py` (dry-run and `--apply`), `dor_check.py` (correctly reports E-03 not-Ready, E-02 Ready), `gen_test_skeleton.py` (26 stubs for E-03's 26 rules, correct ids), `gen_controls.py` (6 stubs for E-03's 6 watch-for items), `red_check.py` (confirmed the 26 generated stubs collect and every one errors — none pass — both against a bare scratch directory and against the real `tests/csim/` with its conftest), `gen_card.py` (emits the same YAML shape as the existing `agora/queue/200-e02-region-state.md` card). The generated E-03 test files were removed after verification — E-03 is not Ready, so they do not belong in the fenced suite yet; regenerate with `gen_test_skeleton.py E-03` once Q-021-03 and Q-022-02 close.

**Bug found in the tools themselves, not the epic:** the first draft of `gen_test_skeleton.py` and `gen_controls.py` embedded rule text and watch-for text directly into generated Python string literals; a rule containing a double-quoted word (R-023-03's `"nearby"`) produced a `SyntaxError` at collection, which `red_check.py` correctly caught as a real problem (a collection error, not a red test). Fixed by using `repr()` for the failure message and swapping any literal `"""` in embedded text. Left as a note here because it is exactly the kind of thing a future epic with quoted terms in its rule text (there will be more) would hit again if this file didn't say to check for it.

## Scripts

All under `scripts/specfactory/`, Python 3.14 stdlib only (no new dependencies), plus `scripts/agy_task.sh`:

- `fold_answers.py` — report/apply closed-flag folding (mechanical half only).
- `dor_check.py` — Definition of Ready gate.
- `gen_test_skeleton.py` — one pytest stub per rule.
- `gen_controls.py` — one control stub per "Ways this could be wrong" item.
- `red_check.py` — proves a batch of new tests is all-red.
- `green_check.py` — proves a reference implementation, whose body lives at `tests/csim/references/<card-id>.c`, makes a card's acceptance commands pass in a scratch git worktree, after confirming they fail on the untouched project.
- `gen_card.py` — emits an Agora card's YAML frontmatter in the existing `agora/queue/*.md` shape.

Prompts and schemas for the `agy`-drafted steps (e2e draft, test-body fill, card brief, findings) are not yet written — none of E-03's blocked flags needed them this session (the fold's design gaps needed Claude's judgment, not `agy`'s drafting), and writing a prompt against a step that hasn't run for real yet risks specifying the wrong shape. Written when the next epic clears its register and reaches the draft-e2e step for real.


## Audit experiment (Westley, 2026-09-15)

The per-file Sonnet audit step is on trial. Only one wave ran; the rest of the filled files ship unaudited on purpose, so the two groups can be compared on what Agora does with them: candidates to green, INCOMPLETE and reset counts per card, and whether a card's failure traces to a test defect. Compare when the E-04 and E-05 cards have run.

| File | Audited | Findings |
|---|---|---|
| tests/csim/test_E05_S032_every_faction_is_a_person.py | yes | MUST-FIX: R-032-03 dropped the weakness term on the empty candidate (0.084 became 0.684, colonize score 0.342); fixed |
| tests/csim/test_E05_S033_territory_pays_or_costs.py | yes | clean |
| tests/csim/test_E05_S034_who_looks_worth_taking.py | yes | clean; R-034-07 was a hard ABI-gap failure, fixed by adding the damage-history fixture |
| tests/csim/test_E05_S035_attack_only_when_it_adds_up.py | yes | minor: two unused imports |
| tests/csim/test_E05_S036_declared_or_sprung.py | yes | MUST-FIX: `len(decisions) == 1` asserted where the ABI records one decision per faction (systemic, fixed in 11 places across the E-05 files); ESCALATE: Q-036-02 budget reservation while a telegraph waits |
| tests/csim/test_E05_S037 to S-041 (5 files) | no | control group |
| tests/csim/controls/test_control_e05_* (9 files) | no | control group |
| tests/csim/test_E04_S026 to S-030 (5 files) | no | control group |
| tests/csim/controls/test_control_e04_* (9 files) | no | control group |
| E-03 files | yes (build-brief chat) | that chat's audit caught a weakened determinism assert, a fabricated register citation, and a stale-equation root cause |

Cards that draw on audited files: 202, 203, 204a (S-036). Cards on unaudited files: 204b, 205, 206, 207, 208a, 208b, 209, 210.
