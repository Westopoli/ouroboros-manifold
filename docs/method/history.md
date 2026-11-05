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
| `docs/method/clerk.md` | 93d8649f | The landing clerk: nine landing steps, the proof capture, the look review, test-defect ruling; retired 2026-11-05 (DEC-mail-detached-2026-11-05), landing is `story_loop.md` step 6 |
| `docs/method/runner.md` | cd113bf3 | The runner chat per gate channel; retired 2026-11-05, Westley drives |
| `docs/method/rulebook.md` | 692b54e3 | The five-condition test-defect procedure and patterns table; retired 2026-11-05, one sentence in `story_loop.md` step 3 |
| `docs/method/gate.md` | 93d8649f | The layered gate per landing, channels, records pushes; retired 2026-11-05; `merge_gate.sh` stays for the nightly sweep only |
| `docs/method/communication.md`, `docs/method/agents.toml` | 4530f758 | Mail, station, wake rule, gate queue, process register (H-077 to H-081); retired 2026-11-05, Westley is the mail system; `scripts/method/mail.py`, `station.py`, `scripts/specfactory/gate_queue.py` and the `om-station`/`om-gate-queue` units stay in the tree, stopped |
| `docs/method/reading_list.toml` | 43d539f7 | Per-role re-read list after a compaction (H-062); retired 2026-11-05, the plan file Westley named is re-read instead |
| `.claude/hooks/mail-guard.sh` | 4530f758 | The `SendMessage` denial hook; out of `settings.json` 2026-11-05, file kept |
| `tests/method/test_mail.py`, `test_station.py`, `test_mail_guard.py`, `mailfix.py`, `test_method_check_comm.py` | 7d1d97cf (`mailfix.py` e97041ef) | Tests of the mail system and the `comm_*` method checks; retired 2026-11-05 with the scripts they pin |
| `tests/specfactory/test_method_check_reread.py` | fff63ae7 | Tests of the `plan_reread` check; retired 2026-11-05 |
| `tests/specfactory/test_gate_channels.py::test_t4e_the_clerk_card_calls_land_push_and_names_the_channel_lock`, `tests/specfactory/test_gate_queue.py::test_6_each_result_sends_one_info_mail_to_the_requester` | db9e9e7d | Pinned the retired clerk card and the gate-queue mail step; retired 2026-11-05 |
| `docs/northstar/plans/2026-11-02-beta-staircase.md`, `plans/2026-10-31-lab-staircase.md` | moved, not retired | Now `docs/northstar/story_reviews/westley/beta-staircase.md`, `lab-staircase.md` (2026-11-05) |

Kept unchanged: `docs/northstar/story_reviews/westley/decisions.md`, `docs/northstar/ambiguity_register.md`, the bible.
