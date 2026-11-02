# History

The method before 2026-10-30 lived in sixteen documents, about 160,000 words. Each is listed with the last commit that touched it on main before the rewrite; `git show <sha>:<path>` reads it. They stayed in the tree for one week after the method landed, then were removed in one commit.

| Document | Last sha | What it held |
|---|---|---|
| `docs/northstar/README.md` | c97606cc | Agora-era position paper; named PLAN.md canonical |
| `docs/northstar/PLAN.md` | abd1024d | 18 principles, the Agora stages, factory roles; what survives of its principles is restated in the cards without attribution |
| `docs/northstar/agile.md` | f35f4d8b | The requirements hierarchy; now `requirements.md` |
| `plans/workflows_2026-10-07/rules.md` | dda6ce64 | Six role sections; now the role cards |
| `plans/workflows_2026-10-07/dispatcher.md` | dda6ce64 | The Dispatcher runbook; now `runner.md` |
| `plans/workflows_2026-10-07/method_check.md` | 7ccc8dbe | Thirteen transcript checks; H-005 cuts the script to six |
| `plans/workflows_2026-10-07/drift_audit.md` | 7499295f | Weekly Sonnet drift audit; now on request |
| `plans/method_rev3_2026-10-26/spec.md` | ddbfe9f0 | 23 gaps, 24 metrics; four metrics kept |
| `plans/2026-10-21-tool-split-spec.md` | d5c1e32b | The six questions for Workflow versus cascade; one line in `architect.md` |
| `plans/2026-10-07-visible-game-spec.md` | 8a92a5d3 | Lane paragraphs, interfaces, owner rows, budget |
| `plans/2026-10-07-visible-game-rulebook.md` | adf02d1e | The stale-test rows; now `rulebook.md` |
| `plans/2026-10-07-visible-game-programme.md` | 41f271a7 | The lane table and scorecard; now `status.sh` |
| `plans/push/pieces.toml` | b8953ed5 | 332 owner rows; ownership is now the merge conflict |
| `plans/push_ledger_2026-09-22.md` | 7bce91fe | TD, FINDING, DRAFT, GATE, EXC rows; now commit trailers |
| `story_reviews/westley/README.md` | 01931049 | The shots table; scenes replaced screenshots |
| `docs/northstar/ROADMAP.md` | 2b03d79b | Lane rows and "Now"; Ready in `stories.md` is the queue |
| `tests/specfactory/test_pieces.py::test_pieces_toml_owns_disjoint`, `tests/specfactory/test_lab_docs.py::test_l7_depends_on_every_other_lab_rev2_row_except_e2_e4_and_l7b` | 38d08cc2 | Tests of `pieces.toml` ownership and the L7 dependency list; retired 2026-11-01 (H-037 part 2a) with the ownership table (H-029, plan ruling 1, Westley 2026-10-30); `git show 38d08cc2:<path>` reads them |

Kept unchanged: `docs/northstar/story_reviews/westley/decisions.md`, `docs/northstar/plans/2026-10-29-layered-gate-spec.md`, `docs/northstar/ambiguity_register.md`, the bible.
