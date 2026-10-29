# Method rev 3: close the 23 gaps, with hard tests that fail loudly (spec)

Status: Phase 0, Architect, 2026-10-26. Westley approved the plan on 2026-10-26 ("go ahead with plan execution"). Source plan: the Architect chat's plan file, copied below from "Design" on. The retro it answers: `docs/northstar/story_reviews/westley/method_retro_2026-10-24.md` and `retro_2026-10-24/method_cost.md`.

Tool line: every piece here is `Tool: Workflow` (harness work, ends in no frame, one piece each). Builders are Sonnet 5.5 engineers or doers on the subscription, run in parallel on disjoint files (DEC-method-rev3-parallel-2026-10-26); landings one at a time through the gate. Westley's words (2026-10-26) that fix the scope: "Subscription in parallel"; "The lab is more important than the beta ... We should prioritize the lab and finish building that first"; look rule kept; FAIL is report only; "Each individual fix should have how exactly it's measured thought out ahead of time."

## Rule-text diffs (land in Phase 4, after the audit and Westley's approval; nothing below changes before that)

| File | Old sentence (exact) | New sentence | Gap |
|---|---|---|---|
| CLAUDE.md "Tests are the spec" | "Every story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###`/`R-###-##` it proves." | "Every sim, pipe and lab story exists as failing tests before any code, in fenced paths builders cannot edit, each naming the `S-###`/`R-###-##` it proves. A client or look piece asserts its `qa_state()` element inventory in a test its builder writes and ships a shot; no separate tests writer." | G01 |
| CLAUDE.md Workflow specs "The script" | "tests first by a different agent than the builder, red on the built tree" | "for sim, pipe and lab pieces, tests first by a different agent than the builder, red on the built tree" | G01 |
| CLAUDE.md Workflow specs "The script" | "a ruler agent inside the script applies the rulebook to a builder's test-defect stop, and only new rule meaning goes to the Architect" | "the landing clerk applies the rulebook to a builder's test-defect stop and writes `ruler=clerk` in the row; only new rule meaning goes to the Architect (`ruler=fable`)" | G02 |
| CLAUDE.md Git | "Ledger, register and epic updates are committed and pushed as they happen." | "One ledger row per landing, written by the landing clerk; a `DRAFT-` row only when a number is new; register and epic updates with the landing that needs them." | G03 |
| CLAUDE.md Task matching, Architect row | "architecture, planning, specs and workflow scripts, rulings, arbitration, briefs, abstract or cross-cutting diagnosis" | "architecture, planning, contract specs (header, pipe frames, save format), rulings, arbitration, abstract or cross-cutting diagnosis; the per-piece spec paragraph and the review of a built piece are Sonnet work" | G04 |
| CLAUDE.md Architecture rules | "**Build units are small.** A Doer or 30B unit is about one file and under about 100 lines; larger work is split when the card is written." | "**Build units are one responsibility.** A Sonnet piece is one coherent responsibility: at most one cross-cutting concern, two or three outside integrations, rule clusters that share a failure domain (manager-mode decomposition rule, research 2026-08); the line cap is 1,000 and the complexity gate (cyclomatic 10, nesting 3) is advisory. A 30B card stays about one file under about 100 lines." | G07 |
| CLAUDE.md Workflow specs "Audit" | "Audit: a fresh Sonnet auditor that has not seen the author's reasoning reads the spec against the bible and the code and tries to refute it" | "Audit, for a contract spec or the beta list only: a fresh Sonnet auditor that has not seen the author's reasoning reads the spec against the bible and the code and tries to refute it" | G19 |
| CLAUDE.md Task matching | "Every spawn names its model." | "Every spawn names its model and starts its description with `<piece id> <role>` (roles: spec, tests, build, land, audit); every report starts with one line `RESULT success|stop:<reason>`." | G11, G12 |
| CLAUDE.md Usage discipline | (new bullet) | "One Architect chat and one Dispatcher chat at a time; a third coordinator is an exception row." | G21 |
| CLAUDE.md North Star | (new sentence after "where another doc disagrees, `docs/northstar/` wins.") | "Method text (this file, `docs/northstar/plans/workflows_2026-10-07/`, `docs/northstar/README.md`, `PLAN.md`) changes only in a commit that also adds to a `retro_*` folder, at most one retro per 14 days; weekly numbers: `scripts/specfactory/method_metrics.py`." | G23 |
| CLAUDE.md Usage discipline | "every tool call re-reads the caller's whole context" paragraph: cap the file at 120 lines by moving the measured history (the 2026-10-07 to 10-10 numbers) to `retro_2026-10-10/README.md` and pointing at it | | G08 |
| `workflows_2026-10-07/dispatcher.md` and the landing template | the landing clerk's steps: add "append the `GATE row` line to `docs/northstar/plans/push/gate_runs.csv` in the records commit"; "rerun the gate at most once; a second failure goes to the Dispatcher"; "rule a test-defect stop with the rulebook, `ruler=clerk`" | | G06, G10, G02 |

Every new sentence gets a `rule_pins.toml` entry (RECORDS-mm-1) so a later edit that drops it fails the gate's pins check.

## Pieces and owners

| Piece | Owns | Acceptance | Model |
|---|---|---|---|
| HARNESS-mm-1a | `scripts/specfactory/method_metrics.py` (git and ledger metrics M01, M02, M04, M05, M10, M11, M12, M19, M20, M23, M24), `scripts/specfactory/method_thresholds.toml` | `tests/specfactory/test_method_metrics.py` cases `1a_*` | Sonnet 5.5 |
| HARNESS-mm-1b | `scripts/specfactory/method_metrics_runs.py` (runs and transcript metrics M01b, M03, M06, M07, M08, M13, M14, M15, M21, M22; imported by mm-1a's CLI) | cases `1b_*` | Sonnet 5.5 |
| HARNESS-mm-1c | `scripts/specfactory/method_metrics_cli.py` (M16, M17, M18, `--week --phase --write --last`, the W43 self-check) and `docs/northstar/plans/method_rev3_2026-10-26/metrics/` | cases `1c_*` | Sonnet 5.5 |
| HARNESS-mm-2 | `scripts/specfactory/merge_gate.sh` (GATE row, default 2400, timeout cause), `scripts/specfactory/suite_regression.py` (timeout signal) | `tests/specfactory/test_gate_row.py` | Sonnet 5.5 |
| HARNESS-mm-3 | `scripts/specfactory/sdk_engineer.py` (run row), `scripts/specfactory/status_check.py` (checks `findings`, `metrics`; `story` in KNOWN_KEYS) | `tests/specfactory/test_sdk_runs.py`, new cases in `tests/specfactory/test_status_check.py` | Sonnet 5.5 |
| HARNESS-mm-4 | `scripts/specfactory/method_check.py` (scratch exclusion), `scripts/specfactory/method_weekly.sh`, `scripts/specfactory/systemd/om-method-metrics.service`, `.timer` | new cases in `tests/specfactory/test_method_check.py`, `tests/specfactory/test_method_weekly.py` | Sonnet 5.5 |
| HARNESS-mm-5 | `scripts/specfactory/launch_check.sh` (pre-flight checks), `scripts/specfactory/spec_provenance.py` (reason 9 WARN) | new cases in `tests/specfactory/test_launch_check.py`, `tests/specfactory/test_spec_provenance.py` | Sonnet 5.5 |
| HARNESS-mm-6 | `.claude/settings.json` (SessionStart hook line for `--last`); queued behind HARNESS-context-guard-2, which owns the file today | one case in `tests/specfactory/test_method_weekly.py` | Sonnet 5.5 |
| RECORDS-mm-1 | `docs/northstar/plans/push/pieces.toml` status normalisation (40 rows) and `contract = true` flags, `scripts/specfactory/rule_pins.toml` entries, `docs/northstar/plans/push/gate_runs.csv` header | `status_check.py` clean, `pieces.py --check` clean | Sonnet 5.5 |

The tests writer (one Sonnet engineer, Phase 1) owns every test file above until the builders start; builders never edit them. Fixtures: `tests/specfactory/fixtures/method_metrics/`.

## Amendments (Architect, 2026-10-26, after the records clerk's report)

- A1 contract flag. `contract = true` joins `KNOWN_KEYS` in `status_check.py` (HARNESS-mm-3, with `story`). Scope: a row is a contract piece when it owns `csrc/ouroboros_sim.h` or `csrc/signatures.toml`, or its id starts with `CONTRACT-`, `VG-CONTRACT`, `LAB-CONTRACT` or `A*-contract`/`PP-contract`/`SPEEDCAP-contract`. Rows that own `docs/architecture.md` or `csrc/save.c` for one paragraph (VG-W2, VG-E1R, VG-E-prodslot, SV-0, core, and the like) are not contract pieces. The flags are applied by the landing clerk of HARNESS-mm-3 in its records commit (RECORDS-mm-1 step 2 moves there).
- A2 sentence pins. `rule_pins.toml` pins `R-###-##` test rules only and has no sentence form, so the rev 3 sentences get their own records file: `docs/northstar/plans/method_rev3_2026-10-26/pins.toml`, `[[pin]] file = "CLAUDE.md"  sentence = "<exact new sentence>"  since = ""  gap = "G01"`. `status_check.py` gains check `method_pins` (HARNESS-mm-3): for every pin with a non-empty `since`, the sentence must appear verbatim in `git show <base>:<file>`; DRIFT when missing, OK otherwise; a pin with `since = ""` is skipped (the sentence lands in Phase 4, when the clerk fills `since`). RECORDS-mm-1 step 3 writes `pins.toml` with the 11 sentences from "Rule-text diffs", every `since` empty. The tests writer adds the `method_pins` cases (DRIFT on a missing dated pin, OK on an empty `since`, OK when present) to `tests/specfactory/test_status_check.py`.
- A3 RECORDS-mm-1 scope after the clerk's run: step 1 done (41 rows: 36 attached with sha, 2 attached without, 3 queued), step 4 done, ledger row done; step 2 moves to mm-3's landing; step 3 is now `pins.toml` as in A2. RECORDS-mm-1 flips to attached when `pins.toml` is on main.
- A4 interfaces fixed by the tests writer (push/mm-tests 4b17890; the tests are the spec where this list and "The gaps" differ). Gate row path classes: product_lines = csrc/ autoload/ scenes/, lab_lines = scripts/skilllab/, test_lines = tests/, docs_lines = docs/; the `phase` switch picks which columns count as product inside the metrics (lab: product_lines plus lab_lines; beta: product_lines). M10 reads rc-0 rows with lab_lines = 0, including rows with product_lines = 0 (that is the test-only landing it exists to catch). M09 belongs to mm-1a. M10c (complexity count) is deferred to a later piece; mm-1a prints nothing for it. Roles: spec, tests, build, land, audit, verify, records; `draft` and `review` only for Fable runs (M06b). A landed piece is the `label` of an rc-0 gate row. M17 age is the week's Sunday minus the blame date. Transcript spend for M06 and M07 needs a `[prices]` table in method_thresholds.toml (list prices per model, DRAFT, empty until Westley gives it); while empty, M06 and M07 count sdk_runs.csv only. `metrics/<week>.json` is `{"week", "metrics": [{"id", "status", "value", "threshold"}]}`. `sdk_engineer.py` takes `--piece`, `--role`, `--label`. `launch_check.sh` reads a `preflight` key in its args JSON. `spec_provenance.py` prints `PROVENANCE WARN` and exits 0 on reason 9; the four existing reason-9 cases now expect that (TD rows by the mm-5 landing clerk, `ruler=clerk`, rule changed by DEC-method-rev3-plan). `method_weekly.sh --dry-run` prints `+ <command>` lines. The gate row is printed on every exit including a base REJECT. The suite-timeout signal: `suite_regression.py` catches `subprocess.TimeoutExpired` and prints `suite-timeout <N>s`, exit 1; the gate quotes it. Not in this rev: the free-enum-slot pre-flight check, the pre_gate provenance WARN case, the transcript price table.
- A5 rulings from the builders' reports (Architect, 2026-10-26). Landing order: mm-5 first, because `spec_provenance.py` reason 9 (63 quantified sentences in this spec with no `[ASSERT]`) rejects every other landing's pre_gate until mm-5 makes it WARN. Each landing carries only its own acceptance tests (ledger row METHOD-rev3-landing-scope). TD-HARNESS-mm-1a-1: `test_1a_M04_fail_40_docs_10_product` asserts "4.0" but its world holds 43 docs-only commits by the spec's definition (every path under docs/; the three records commits count), so the value is 4.3; the landing clerk changes the assertion to FAIL with 4.3, `ruler=clerk`. Where mm-1a and mm-1b read the tests differently from "The gaps", the tests stand (A4): M10 is the median of `product_lines` over all rc-0 rows; M20 off-phase in lab means `lab_lines = 0` with `product_lines > 0`; M11c counts png, jpg, jpeg, gif, svg, csv, json, html only; M19c matches the candidate sha or a merge's second parent; M13 is the worst piece (max); M21b counts rule-lines per session; a sub-agent run read from `.meta.json` has cost 0; `[prices]` is not read yet (M06, M07 on sdk_runs.csv only); `judge` prints DRAFT instead of PASS while `approved = ""` and FAIL stays FAIL, so an unapproved threshold still fails loudly. `sdk_engineer.py` outcome is `success` or `error`; `stop:<reason>` comes only from the agent's RESULT line (mm-1b reads it). Ledger rows not yet committed count as today for `findings` (mm-3).
- A6 rulings from mm-2's report (Architect, 2026-10-26). TD-HARNESS-mm-2-1: `tests/specfactory/test_gate_base_stage.py` tests 2 and 3 assert `len(gate) == 1` over lines starting `GATE `, and the spec's `GATE row` line (printed on every exit, A4) is one more; the landing clerk filters `GATE row ` out in that file's `_run`, `ruler=clerk`. Queue time: the gate cannot see the `.start` marker, so it reads `MERGE_GATE_QUEUE_S` (default 0); the landing clerk exports it as the seconds from its `.start` marker to the moment it takes the lock (landing template line). Pre-gate pollution: `pre_gate.sh` runs `merge_gate.sh --revert`, which now appends a row to `~/Projects/om-push/gate_runs.csv`; HARNESS-mm-7 (one line in `pre_gate.sh`: `export MERGE_GATE_RUNS_CSV=/dev/null`, with a case in `test_gate_row.py`) stops that; until it lands, every landing clerk deletes from that machine file the rows whose label is its own piece and whose rc is not from its real gate, and M09 ignores rows with `stage_s` under 60. The timeout reaches the gate as a `TimeoutExpired` traceback in the stage log (the support module runs pytest in-process), so the gate greps the log for it; `suite_regression.py`'s own CLI also prints `suite-timeout <N>s`.
- A7 (Architect, 2026-10-26): the tests call `scripts/specfactory/method_metrics.py` directly, so mm-1c also owns that file for its last line only: `sys.exit(main())` becomes `import method_metrics_cli; sys.exit(method_metrics_cli.main())`; mm-1a's `main()` stays for its own cases. mm-1c builds after mm-1a (ordering edge).
- A8 (Architect, 2026-10-26, after mm-1c's report; for the auditors). The W43 snapshot measured M04 at 7.26 (334 docs-only against 46 product commits), not the 18.4 `method_cost.md` H2c gave (332 against 18): the two counts differ in commit set (H2c counted every commit on every branch, `--no-merges`, all parents; the metric counts what it counts, and the auditors say which is right and whether the toml baseline should change). M06 and M09 have no W43 records (empty sdk_runs.csv, header-only gate_runs.csv), so the self-check holds only through mm-1c's `--baseline M06,M09` flag, which judges the spec's W43 numbers from the toml and says so in the numbers cell. That flag is a way to make the self-check pass without records; auditor B's task 2 covers it. M18 real: 218 finished trees not reaped, 373 GB, 254 unmerged push branches. M19c real: 13 of 13 product commits without a gate row. M16 real: lanes VG-B and VG-F have attached look pieces and no verdict row. A full run takes about 2.5 minutes (the `du` over `wt/`); the weekly timer absorbs it, the compaction hook uses `--last` (reads the stored json, no recompute). M16's toml `value = 2, direction = ">="` means "lanes with at least 2 look pieces", the FAIL compare is lanes-without-verdict `<= 0`. Landing plan: mm-5, mm-2, mm-3, then mm-1a + mm-1b + mm-1c as one landing from push/mm-1c, then mm-4.

## Design

Three records fixes come first, because without them half the metrics have nothing to read (G17 was "records cannot answer the question they exist for"):

1. Gate rows. `merge_gate.sh` ends with one line `GATE row <csv>` and appends it to `~/Projects/om-push/gate_runs.csv` (machine-local, survives `/var/tmp` cleanup). Columns: date, label, branch, base sha, candidate sha, queue_s (`.start` marker to lock), stage_s (sum of `[N.Ns]` stage times), rc, reject_stages, reject_causes (the regression stages must name `suite-timeout <N>s` in their REJECT detail when `suite_regression.py` timed out; today the GATE line says only `baseline: computed <sha>` and the cause is buried in the stage log), product_lines, test_lines, docs_lines, lab_lines (from `git diff --numstat base..candidate` by path class). The landing clerk appends the same line to `docs/northstar/plans/push/gate_runs.csv` in the landing's records commit (landing template step 4 gains one line).
2. Run rows. `sdk_engineer.py` appends one row per run to `~/Projects/om-push/runs/sdk_runs.csv`: date, label, piece id, role, model, turns, cost, outcome (`success`, `stop:<reason>`, `error`). Subscription spawns are read from the transcripts: `~/.claude/projects/<slug>/<session>/subagents/agent-*.meta.json` and the parent's Agent tool_use entries (2,611 sub-agent transcripts exist today). New rule text: "Every spawn names its model and its piece id, as `<piece id> <role>` at the start of its description", and every brief's report schema starts with one line `RESULT success|stop:<reason>`. Transcript parsing reuses `method_check.py`'s loader and `role_of`.
3. Ledger fields. Every `FINDING-` row dated on or after 2026-10-26 carries `found-by=<test|frame|play|look|audit|spec|probe|other>` in its Event cell; every `TD-` row carries `ruler=<sonnet|fable|clerk>`. `status_check.py` gains check `findings` (DRIFT on a missing token after the date). `pieces.toml` rows with a non-standard status form (40 today) are normalised in one records piece, and `story` joins `KNOWN_KEYS`.

Then one script computes every metric from those records plus git, the ledger, `pieces.toml`, `stories.md`, the Westley README, the transcripts directory and the `.wt-state` files (never a live `wt.py status`, which takes over 120 s on 558 trees):

- `scripts/specfactory/method_metrics.py --week 2026-W45 [--phase lab|beta] [--write]`: prints one line per metric, `METRIC <id> PASS|FAIL|DRAFT|NA <value> vs <op><threshold> <gap> (<the numbers behind it>) <week>`, and on FAIL up to three decisive rows under it (the gate row, the ledger ids, the commit shas). Exit 1 on any FAIL. `--write` stores `docs/northstar/plans/method_rev3_2026-10-26/metrics/<week>.json` and appends a row to that folder's README table. The week of a ledger row is the `git blame` author date of its line on origin/main (as `method_cost.md` H1b did); the week of a commit is its author date; the week of a transcript entry is its timestamp.
- `scripts/specfactory/method_thresholds.toml`: one table per metric: id, gap, DRAFT name, value, direction, unit, `approved = ""`, baseline W43 value, window, `phase` (lab, beta, or both).
- `tests/specfactory/test_method_metrics.py` plus `tests/specfactory/fixtures/method_metrics/`: for every metric a known-good fixture that must PASS and a known-bad fixture that must FAIL (the positive control), a tamper test (unapproved threshold prints DRAFT, not PASS), and a self-check that the frozen W43 snapshot (`metrics/2026-W43.json`, the measured bad week) still trips M04, M06, M09, M18 and M19. That snapshot is the standing positive control: if a later change to the script stops seeing the bad week, the suite goes red.
- Loudness: the `SessionStart` compact hook runs `method_metrics.py --last` after `method_check.py` and prints the FAIL lines of the latest stored week; the gate's status stage prints `STATUS metrics WARN <ids>`; the weekly run writes the row on Westley's page README (`story_reviews/westley/README.md`) and a ledger row `METRIC-<week>` listing every FAIL with its number.
- Weekly run without a chat: a systemd user timer `om-method-metrics.timer` (Sunday 23:00, precedent `agora-dispatcher.service`) runs `scripts/specfactory/method_weekly.sh`: `wt.py new`, fetch, `method_metrics.py --week <last ISO week> --write`, commit, records-lock push (DEC-records-lock), `wt.py done`. No model is called.
- Rule text is pinned: every rewritten sentence in CLAUDE.md, `dispatcher.md`, the landing template and the Workflow-specs section gets a `rule_pins.toml` entry (`rule_pins.py check`, existing), so a later edit that drops the sentence fails the gate's pins check. This is the "fix in force" check for every rule-only fix below.

## The gaps: fix, how it is verified, when it fails

Each entry: the fix; **In force** (how we check the fix is being followed); **Effect** (the metric, its DRAFT threshold, the exact procedure); **Fails loudly when**; **Positive control** (the fixture that must FAIL); **W43** (the bad week's value, where measured).

**G01 Tests-first by a separate writer for client and look pieces.**
Fix: tests-first stays for `csrc/`, `tests/csim`, `tests/transport` and lab measures; a client or look piece asserts its `qa_state()` element inventory in a test the builder writes, ships a shot, no separate writer. CLAUDE.md "Tests are the spec" and Workflow specs "The script" rewritten; sentences pinned.
In force: M01b, runs with role `tests` whose piece's `owns` paths are only under `autoload/` or `scenes/` = 0 per week (sdk_runs.csv plus sub-agent meta joined to `pieces.toml`).
Effect: M01, code-only test lines added over game-code lines added per ISO week: `git log origin/main --since --until --no-merges --numstat`; test code = paths under `tests/` with extension `.py .gd .c .h`, not under `tests/fixtures/`, basename without `golden`; game code = the phase's product paths with `.c .h .gd .tscn .py`; ratio of summed additions; NA when game additions are under 200. DRAFT ≤ 1.5 (the research's 1:1 to 1.5:1).
Fails loudly when: M01 > 1.5 or M01b > 0. Line names the two sums and the offending run labels.
Positive control: fixture repo with 300 game lines and 600 test lines added in the week (ratio 2.0) and one `tests` run on a scenes-only piece.
W43: compute at Phase 2 (all-files ratio was 2.24).

**G02 Every test-defect ruled by Fable.**
Fix: the landing clerk rules test-defect stops with the rulebook (`rules.md` section the ruler uses today); Fable only for new rule meaning. `dispatcher.md` and the landing template rewritten; pinned.
In force: M03, TD rows in the week with `ruler=fable` ≤ 2; TD rows without a `ruler=` token (after 2026-10-26) counted under M19a.
Effect: M02, TD rows in the week over landings in the week (gate rows with rc 0 whose candidate sha is on origin/main) ≤ 1.0; absolute TD rows ≤ 10.
Fails loudly when: either bound is passed; the line lists the TD ids and their rulers.
Positive control: ledger fixture with 12 TD rows, 3 `ruler=fable`, 4 landings.
W43: 144 TD rows, every ruling by the Architect.

**G03 Per-piece records ceremony.**
Fix: one ledger row per landing, written by the landing clerk; a `DRAFT-` row only when a number is new; the provenance lint's reason 9 (quantified quote not inside an assert) becomes WARN; the attach flip stays. `spec_provenance.py` reason 9 severity changed; pinned text in the landing template.
In force: M05, ledger rows in the week over landings ≤ 3; M05b `DRAFT-` rows per week ≤ 2; unit test in `test_merge_gate.py` style that a spec with a reason-9 case gets `PRE_GATE provenance WARN`, not REJECT.
Effect: M04, docs-only commits over product commits per week ≤ 2.0: `git log --since --until --no-merges --name-only`; a commit is product if any path is under the phase's product paths, docs-only if every path is under `docs/`.
Fails loudly when: M04 > 2.0 or M05 > 3 or M05b > 2; the line gives both commit counts.
Positive control: fixture week with 40 docs-only commits and 10 product commits (4.0); ledger fixture with 20 rows and 4 landings.
W43: M04 18.4 (332 over 18); 492 ledger rows.

**G04 Fable as per-piece drafter and reviewer.**
Fix: Sonnet drafts the per-piece spec paragraph and reviews the built piece; Fable only on a contract piece (`csrc/ouroboros_sim.h`, `signatures.toml`, pipe frames, save format) or a ruling. CLAUDE.md Task matching rewritten; pinned.
In force: M06b, runs with model `claude-fable-*` and role `draft` or `review` whose piece id is not flagged `contract = true` in `pieces.toml` = 0 per week.
Effect: M06, Fable share of model spend per week ≤ 25%: credit runs from `sdk_runs.csv` cost; subscription runs from transcript `usage` fields at list prices (the weighting `retro_2026-10-10` used), summed per model.
Fails loudly when: M06 > 25% or M06b > 0; the line names the Fable run labels and their dollars.
Positive control: runs fixture with Fable $60 of $90 and one Fable draft on a non-contract piece.
W43: 67% ($132 of $197 on credit).

**G05 Coordinator context 300k to 900k, polling in chat.**
Fix: landed (context guard at 400k, autocompact 200k, no-polls rule). Nothing new to build; this plan verifies it stays true.
In force: `test_context_guard.py` green; `settings.json` hook line present (a test greps it).
Effect: M08, assistant entries across every transcript touched in the week whose `usage` total (input plus cache_read plus cache_creation) exceeds 400,000 = 0; M08b, polling DRIFT turns in the week = 0, by running `method_check.py --transcript` on each session file and counting the dated DRIFT lines under `polling` that fall in the week.
Fails loudly when: either count is above 0; the line gives session id, timestamp and context size of the worst call.
Positive control: synthetic transcript (the `test_method_check.py` builders) with one 450k call and two polling turns.
W43: 638 calls over 400k; 149 polling calls in one hour.

**G06 Gate rejects on its own 600 s suite timeout under QA load.**
Fix: `merge_gate.sh` default `MERGE_GATE_SUITE_TIMEOUT` 2400 (the landing template already exports 2400); the regression stages name `suite-timeout <N>s` in their REJECT detail; the gate holds the Agora play lock (landed, DEC-gate-holds-agora-lock-2026-10-24).
In force: unit test reads the script's default (600 today at `merge_gate.sh:30`) and asserts 2400; unit test feeds a timed-out `suite_regression.py` result and asserts the GATE line carries `suite-timeout`.
Effect: M09, gate rows in the week whose `reject_causes` contains `suite-timeout` = 0; M09b, median `stage_s` of rc-0 rows ≤ 3600 s; M09c, max `queue_s` ≤ 3600 s.
Fails loudly when: any bound passed; the line quotes the gate row.
Positive control: gate_runs fixture with two timeout rows, one 4,000 s pass, one 7,680 s queue.
W43: 5 of 9 timeouts; passes 51 to 66 min; queue 128 min.

**G07 Pieces too small for their fixed cost.**
Scope: the Sonnet builder's unit (one piece), nothing else. Clerks, tests writers and auditors are not sized by this rule. The 30B keeps the 100-line card only when `DOER_BACKEND = agora-30b`.
Fix: CLAUDE.md "A Doer or 30B unit is about one file and under about 100 lines" is replaced by the manager-mode decomposition rule (`claude-manager-mode` research 2026-08, Phase C and K15/K18/K19): a piece is one coherent responsibility, judged by rule clusters, cross-cutting concerns (at most one) and outside integrations (at most two or three), not by line count; the line cap is the manager-mode `max_impl_lines` 1,000 (its measured runs: 345 real lines over 5 files with no correctness break, 585 the highest tested; no ceiling found); its complexity gate (cyclomatic ≤ 10, nesting ≤ 3, calibrated on 72 functions) runs advisory on every landed piece. Judgment, not correctness, is what broke at 3 files in that research, and only when the leaf wrote its own tests; our fenced tests keep that fix. Pinned.
In force: pin check; M10b, pieces landed in the week whose `product_lines` exceed 1,000 = 0; M10c, functions in the landed diff over cyclomatic 10 or nesting 3 printed as WARN (count shown, no FAIL until Westley sets a bound).
Effect: M10, median `product_lines` over the week's rc-0 gate rows that touch product paths ≥ 40, evaluated only when there are at least 3 such rows (else NA). A floor against pieces too small, not a cap.
Fails loudly when: median < 40 or M10b > 0; the line lists the rows and their product lines.
Positive control: gate_runs fixture with product lines 0, 12, 30 (median 12); one row at 1,200.
W43: median 0 over the five measurable merges.

**G08 Method prose weight.**
Fix: CLAUDE.md at or under 120 lines; lab data (png, csv, json, html) lives under `docs/northstar/research/*/data/` (one move, Westley's word) and is excluded from counts; method prose grows only with a retro.
In force: M11b, `git show origin/main:CLAUDE.md | wc -l` ≤ 120; M11c, files added in the week under `docs/northstar/` with a non-`.md` extension outside a `data/` directory = 0.
Effect: M11, `.md` lines added under `docs/northstar/` in the week over product lines added ≤ 2.0, except a week with a commit adding a file under `docs/northstar/plans/retro_*/` (then NA).
Fails loudly when: any of the three; the line names the files.
Positive control: fixture week with 2,000 md lines and 500 product lines, one `.png` under `plans/`, CLAUDE.md of 130 lines.
W43: CLAUDE.md 97 lines; ratio compute; lab data 1.33M lines under `research/`.

**G09 No scoped beta list.**
Fix: after the lab (Westley's order): `docs/northstar/plans/beta_<date>/stories.md`, at most 25 ordered stories, loop closed, a line `Approved: Westley <date>`; every product piece names its story in `pieces.toml` (`story = "S-###"`).
In force: M12a, during `phase = beta` the file exists with ≤ 25 rows and the approval line; M12b, landed product pieces in the week with a `story` on the list ≥ 80%.
Effect: M12c, stories moved to Seen in the week (stories.md status cell, week by blame) ≥ 1.
Fails loudly when: in `beta`, any of the three; NA in `lab`.
Positive control: fixture with a 30-row list and 3 of 6 landed pieces on it.
W43: NA (8 Seen in six weeks, first on day 34).

**G10 Landings retried.**
Fix: the landing clerk runs `pre_gate.sh` on the merged tree before taking the lock (template step 2 already), reruns the gate at most once on its own, and hands a second failure to the Dispatcher. Landing template rewritten; pinned.
In force: M13, landing runs per landed piece ≤ 2 (sdk_runs.csv role `land` plus sub-agent meta descriptions `<piece> land`, joined to landed pieces).
Effect: M13b, landing cost per piece ≤ builder cost per piece (same join).
Fails loudly when: either; the line lists the landing run labels per piece.
Positive control: runs fixture with 4 landing runs on one piece.
W43: lm 5, wtcap 4, sd 3; landing $11.86 against builders $3.60.

**G11 Eight roles per piece.**
Fix: four per piece: `spec` (Sonnet; Fable for a contract piece), `tests` (sim, pipe, lab only), `build`, `land` (the clerk also rules test-defects and writes the one ledger row). Auditor only on a contract spec or the beta list. CLAUDE.md Task matching and Workflow specs rewritten; pinned.
In force: M14b, roles seen per landed piece ⊆ {spec, tests, build, land, audit-contract}.
Effect: M14, runs per landed piece ≤ 4 (median over the week's landed pieces).
Fails loudly when: either; the line lists the extra roles.
Positive control: runs fixture with 7 runs on one piece including `records` and `verify`.
W43: 6 to 12 per piece.

**G12 Workflow runs stopped on spec or records gaps.**
Fix: `launch_check.sh` grows the pre-flight list as executable checks (owner rows for every file the spec names, named functions exist at the base, free enum slots, the fenced tests red at the base), so a gap stops the launch, not the run.
In force: `test_launch_check.py` cases, one per new check, each with a fixture that must fail the launch.
Effect: M15, runs in the week whose outcome is `stop:spec` or `stop:records` over all runs ≤ 20% (sdk_runs.csv outcome column; sub-agent reports' first line `RESULT ...`).
Fails loudly when: above 20%; the line names the stopped runs and reasons.
Positive control: runs fixture with 4 stops of 10.
W43: 20 of 32 (10-14 to 10-21).

**G13 Fan-out before the first look.**
Fix: landed (skeleton first). Verified only.
In force and effect: M16, for every lane prefix listed in `method_thresholds.toml` (`lanes = ["VG-A", "VG-C", ...]`), count attached pieces whose `owns` include a `scenes/` path (look pieces) and verdict rows in `decisions.md` or the Westley README naming that prefix; a lane with ≥ 2 attached look pieces and 0 verdicts fails.
Fails loudly when: any such lane; the line names it and its pieces.
Positive control: pieces fixture with three attached `scenes/` pieces under `VG-X` and no verdict row.
W43: 0 since 10-13.

**G14 Lanes serialise on Westley.**
Fix: keep (his word). Report only.
Effect shown: M17, rows on `story_reviews/westley/README.md` whose Verdict cell is empty or says `awaiting`: count and oldest age in days (blame date). No threshold, no FAIL; printed every week and at every compaction so he sees when he is the bottleneck.
Positive control: fixture README with 3 open rows, oldest 12 days, prints `METRIC M17 NA 3 rows, oldest 12 d`.
W43: 6 rows awaiting.

**G15 Worktree sprawl.**
Fix: landed (wt cap); the weekly timer runs `wt.py reap` after a dry run with literal paths.
In force: `test_wt_cap.py` green.
Effect: M18a, directories under `~/Projects/om-push/wt/` whose `.wt-state` says `active` ≤ 12; M18b, with `.wt-done` present and not yet reaped ≤ 20; M18c, `du -sm wt/` ≤ 120 GB; M18d, `git for-each-ref refs/remotes/origin/push/` branches not in `git branch -r --merged origin/main` with committer date older than 14 days ≤ 10. Read from the state files only, never a live `wt.py status`.
Fails loudly when: any bound; the line lists the oldest offenders.
Positive control: fixture tree with 14 active state files; branch list fixture with 12 stale unmerged.
W43: 558 trees, 258 GB, 86 unmerged branches.

**G16 Merge overhead unmeasured.**
Fix: every landing writes a gate row with size columns, fast-forward or merge. Verified by M19c (below) and used by M10.

**G17 Records cannot answer the question they exist for.**
Fix: the three records fixes in Design.
In force and effect: M19a, `FINDING-` rows with blame date ≥ 2026-10-26 lacking `found-by=` plus `TD-` rows lacking `ruler=` = 0; M19b, `pieces.toml` rows whose `status` is not `{ state = "<attached|queued|superseded|landed|pending>" ... }` = 0 (via `pieces.py load_pieces`); M19c, first-parent commits on origin/main in the week touching product paths that have no gate row with a matching candidate or merge sha = 0 (print as a percentage too).
Fails loudly when: any count above 0; the line lists the ids or shas.
Positive control: ledger fixture with one untagged FINDING row; pieces fixture with one `status = "attached"` string; a week with two product commits and one gate row.
W43: 40 non-standard status rows; 0 gate rows in the repo; 182 FINDING rows untagged.

**G18 Lab and beta compete.**
Fix: Westley: lab first. `phase = lab` in `method_thresholds.toml` until he flips it; the beta list (G09) waits.
In force and effect: M20, rc-0 gate rows in the week with zero lines under the phase's product paths and nonzero lines under the other phase's paths, over all rc-0 rows ≤ 20% (during `lab`: client-only landings are the exception).
Fails loudly when: above 20%; the line names the landings.
Positive control: gate_runs fixture with 3 client-only rows of 5 during `lab`.
W43: compute (lab landings were the product that week).

**G19 Audits and verifies cost more than builds.**
Fix: an audit only for a contract spec or the beta list; `verify` folds into the landing clerk's report. Workflow specs "Audit" rewritten; pinned.
In force: M07b, runs with role `audit` whose piece is not `contract = true` and not the beta list = 0; runs with role `verify` = 0.
Effect: M07, audit plus verify share of weekly spend ≤ 5% (same spend join as M06).
Fails loudly when: either; the line names the run labels.
Positive control: runs fixture with audit $9 of $100 and one `verify` run.
W43: 6.2% ($12.27 of $197), 22 Sonnet audits in two days.

**G20 Compaction and method-check ceremony.**
Fix: `method_check.py` `code_edits` excludes `~/Projects/om-push/scratch/**` (runner scripts for clerks are briefs, not code); exception rows (`EXC-`) remain the path for a justified break.
In force: `test_method_check.py` case: a Write under `scratch/` by the architect role is not a `code_edits` DRIFT; a Write under `scripts/` still is.
Effect: M21a, `EXC-` ledger rows in the week ≤ 1; M21b, DRIFT lines (all rules) across the week's transcripts ≤ 2 (method_check per session, dated lines in the week).
Fails loudly when: either; the line names the rows and the sessions.
Positive control: ledger fixture with 2 EXC rows; synthetic transcript with 3 DRIFT turns.
W43: 1 EXC row; 2 DRIFT lines at this chat's last compaction.

**G21 Multiple coordinator chats.**
Fix: one Architect chat and one Dispatcher chat at a time; a third is an exception row. CLAUDE.md Usage discipline rewritten; pinned.
In force and effect: M22, for every hour of the week, the number of distinct top-level session transcripts (not `subagents/`) with an assistant entry in that hour whose `role_of` is architect or dispatcher; max over hours ≤ 2.
Fails loudly when: above 2; the line names the sessions and the hour.
Positive control: three synthetic transcripts (two Fable, one Sonnet) with entries in the same hour.
W43: 3 (two Architect chats and the Dispatcher).

**G22 Fixtures and goldens counted as tests.**
Fix: goldens and generated data live under `tests/fixtures/`; the gate's suite still runs them; the ratios exclude them (M01 is already code-only).
In force: M23, files added in the week under `tests/` outside `tests/fixtures/` with extension `.json .csv .png .txt` or basename containing `golden` = 0.
Effect: M01's exclusion (its fixture test adds 5,000 fixture lines and asserts the ratio does not move).
Fails loudly when: M23 above 0; the line names the files.
Positive control: fixture week adding `tests/csim/golden_x.json`.
W43: compute.

**G23 Method rewritten under load.**
Fix: method text (CLAUDE.md, `docs/northstar/plans/workflows_2026-10-07/*`, `docs/northstar/README.md`, `PLAN.md`, the landing template, `dispatcher.md`) changes only in a commit that also adds to a `retro_*` folder; at most one retro per 14 days. CLAUDE.md North Star paragraph gains the sentence; pinned.
In force and effect: M24a, commits in the week touching those paths without a `retro_*` path in the same commit ≤ 3; M24b, distinct `retro_*` folders created in the trailing 14 days ≤ 1.
Fails loudly when: either; the line lists the commits.
Positive control: fixture week with 5 method-text commits and no retro path; two retro folders in 10 days.
W43: 4 method revisions in 14 days.

## Artifacts

Repo (worktrees under `~/Projects/om-push/wt/`, never the live checkout):
- `docs/northstar/plans/method_rev3_2026-10-26/spec.md`: the entries above with the exact rule-text diffs (old sentence, new sentence, file) and the `Tool:` line per piece. `README.md` in that folder: the weekly metrics table. `metrics/2026-W43.json`: the frozen bad week. `audit_findings.md`: Phase 3.
- `scripts/specfactory/method_metrics.py`, `method_thresholds.toml`, `method_weekly.sh`, `systemd/om-method-metrics.{service,timer}`; edits to `merge_gate.sh` (gate row, timeout cause, default 2400), `suite_regression.py` (timeout signalled to the gate), `sdk_engineer.py` (run row), `status_check.py` (checks `findings` and `metrics`, `story` in `KNOWN_KEYS`), `method_check.py` (scratch exclusion), `launch_check.sh` (pre-flight checks), `spec_provenance.py` (reason 9 WARN), `rule_pins.toml` (pinned sentences), `.claude/settings.json` (hook line).
- `tests/specfactory/test_method_metrics.py`, `test_gate_row.py` (extends the `test_merge_gate.py` pattern), `test_sdk_runs.py`, new cases in `test_method_check.py`, `test_launch_check.py`, `test_spec_provenance.py`; fixtures under `tests/specfactory/fixtures/method_metrics/`.
- Records: `docs/northstar/plans/push/gate_runs.csv`, `pieces.toml` rows for every piece below with owner rows and `contract` flags on the contract pieces, `decisions.md` rows, ledger rows, the Westley README row.
- Machine: `~/Projects/om-push/gate_runs.csv`, `~/Projects/om-push/runs/sdk_runs.csv`, `~/.config/systemd/user/om-method-metrics.{service,timer}`.

Pieces (one owner each, file-disjoint, so they build in parallel; `Tool: Workflow` each, harness work ends in no frame):
- HARNESS-mm-1a `method_metrics.py` and `method_thresholds.toml`: metrics over git and the ledger (M01, M02, M04, M05, M09, M10, M11, M12, M19, M20, M23, M24), the thresholds toml, `test_method_metrics.py` cases `test_1a_*`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-1b `method_metrics_runs.py`: metrics over runs and transcripts (M01b, M03, M06, M07, M08, M13, M14, M15, M21, M22), cases `test_1b_*`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-1c `method_metrics_cli.py`: M16, M17, M18, the CLI, `--write`, `--last`, the W43 self-check and snapshot, cases `test_1c_*`; also the last line of `method_metrics.py` (A7). [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-7 `pre_gate.sh`: one line, `export MERGE_GATE_RUNS_CSV=/dev/null`, so a dry run writes no gate row (A6); one case in `test_gate_row.py`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-2 gate row: `merge_gate.sh`, `suite_regression.py` timeout signal, `test_gate_row.py`, the landing template line. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-3 run rows and ledger fields: `sdk_engineer.py`, `status_check.py` (`findings`, `story` key), `test_sdk_runs.py`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-4 loudness: `settings.json` hook line, `status_check.py` check `metrics`, `method_check.py` scratch exclusion with its test case, `method_weekly.sh`, the systemd unit files. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-6 `.claude/settings.json` SessionStart hook line `method_metrics.py --last`; pending behind HARNESS-context-guard-2 (A3). [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-5 `launch_check.sh` pre-flight checks with `test_launch_check.py` cases; `spec_provenance.py` reason 9 WARN (the quantified-quote and [ASSERT] findings; the unquoted-[W] finding stays a reject) with its test. [P docs/northstar/story_reviews/westley/decisions.md:65]
- RECORDS-mm-1 `pieces.toml` normalisation (41 rows, done 7448d665), `pins.toml` (A2), `metrics/2026-W43.json` baseline, the lab data move (G08) if Westley approves it. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Phases

Phase 0, spec (Architect, this chat, no spawns, about two turns):
- Write `spec.md` with the entries above, the rule-text diffs, the thresholds.toml draft, briefs for the tests writer, the builders, the landing clerk and the two auditors; `pieces.toml` rows; DEC rows (parallel budget, lab first, look rule kept, report-only). Records-only push under `records.lock`.
- Westley reads the rule-text diffs. Nothing in CLAUDE.md changes until Phase 4.

Phase 1, tests first (one Sonnet engineer, subscription):
- Writes every test red on origin/main for the stated reason (script missing, csv missing, hook line missing, default 600), the failing assertion lines pasted in its report, positive controls green on the fixtures. Harness work, so tests-first applies.
- Pre-flight before launch, read from origin/main and the machine: the gate's stage-line format `GATE <name> <status> <detail> [N.Ns]` and the five timeout logs under `/var/tmp/om-push/`; how `suite_regression.py` reports a timeout (exit code and text); the `agent-*.meta.json` fields (description, subagent type, model) under one session's `subagents/`; the `method_check.py` loader and `role_of` signatures; `pieces.py load_pieces`; `pre_gate.sh` and `test_merge_gate.py` conventions; the Westley README's Verdict cell wording for open rows.

Phase 2, build (Sonnet doers in parallel on the HARNESS pieces, then landings one at a time through the gate):
- Each doer: one piece, its tests fenced, `pre_gate.sh` before the push, report once with `RESULT` as its first line. A test-defect stop is ruled by the landing clerk with the rulebook (G02 applied to itself; the ruling gets `ruler=clerk`).
- Landing clerk per piece, gate, push; the first landing after mm-2 writes the first real gate row.
- The baseline: once mm-1 lands, run `method_metrics.py --week 2026-W43 --write` and `--week 2026-W44` from the records as they are; freeze W43 as the positive control.

Phase 3, two Sonnet auditors (parallel, fresh, neither sees the other's brief or this plan's reasoning):
- Auditor A, validity: for each metric, does the number measure the fix's claimed effect; can a week be gamed to PASS while the behaviour continues (tests under `tests/fixtures/`, docs under a `data/` folder, a landing with no gate row, a spawn without a piece id); are the W43 baselines right against `method_cost.md`; is any threshold a number nobody gave.
- Auditor B, engineering: run the suite; try to make the W43 snapshot PASS by editing only the script; try to make a legitimate week FAIL (a retro week, an idle week, a week with one landing, a week with no spawns); check the transcript parser against a real session and its `subagents/`; check the gate row against a real gate log under `/var/tmp/om-push/`.
- Schema per auditor: FINDINGS (id, metric, claim, evidence lines, severity), under 60 lines.
- The Architect then reproduces every finding: for each, the auditor's evidence, the Architect's evidence, verdict holds / weakened / refuted, and what changes if it holds. Written to `audit_findings.md` and summarised on Westley's page with both sides. Westley rules per finding and approves or changes every DRAFT threshold (the `approved` field gets his date).

Phase 4, the fixes land:
- Rule text: CLAUDE.md, `workflows_2026-10-07/` files, `dispatcher.md`, the landing template, per the approved diffs, in one retro-folder commit (M24 counts it as the retro week); the sentences pinned in `rule_pins.toml`.
- Harness defaults flip (`SUITE_TIMEOUT` 2400, hook line, timer installed on Westley's word).
- Findings that held become fixes to the metrics before the thresholds are approved.
- Ledger row `METHOD-rev3` with the date, and `metrics/2026-W45.json` as the first live week.

Phase 5, constant verification:
- Weekly: the timer writes the week's json, the README row, the ledger row, the FAIL lines on Westley's page. Every compaction prints the latest FAILs. Every gate prints WARN on a failing metric.
- Monthly: a fresh Sonnet drift auditor (the existing `drift_audit.md` cadence) re-reads the metrics against the ledger and reports gaming or stale thresholds, unedited, to Westley.
- The lab runs first under the new method; its landings are the first live data. The beta list (G09) is written when Westley says the lab is done; `phase` flips to `beta` on his word.
- The A/B experiment from the retro page stays a separate go with a separate budget.

## Verification

- `python3 -m pytest tests/specfactory/test_method_metrics.py tests/specfactory/test_gate_row.py tests/specfactory/test_sdk_runs.py tests/specfactory/test_method_check.py tests/specfactory/test_launch_check.py` green on the landed tree; red on origin/main before Phase 2 with the reasons the tests writer pasted.
- `method_metrics.py --week 2026-W43` prints FAIL for M04 (18.4 vs ≤ 2.0), M06 (67% vs ≤ 25%), M09 (5 vs 0), M18 (558 trees, 86 branches), M19b (40 vs 0) and exits 1. Any later script change that loses one of those lines fails the self-check test.
- `method_metrics.py --week 2026-W45` after Phase 4 prints a line for every metric, none `DRAFT` once Westley has approved, and the json lands on main by the timer without a chat.
- A deliberate bad landing (a test-only merge with 0 product lines) in a scratch worktree produces a gate row with `product_lines=0`, and the next weekly run flags M10.
- A deliberate timed-out suite (`MERGE_GATE_SUITE_TIMEOUT=1` on a scratch candidate) produces a gate row with `suite-timeout` in `reject_causes`, and the weekly run flags M09.
- `method_check.py` on this chat's transcript after Phase 2: `code_edits` no longer counts the scratch runner scripts.

## What waits on Westley

- Approval of this plan, then the rule-text diffs in `spec.md` (Phase 0).
- Every DRAFT threshold's number (after Phase 3, with the auditors' findings in front of him).
- The lab data move under `data/` (G08) and installing the systemd timer on his machine.
- Rulings on each auditor finding that holds or is weakened.
- The word that the lab is done, which starts the beta list.

## Amendment A9 (2026-10-27): Phase 4 pieces after the audit

Westley 2026-10-27: the draft numbers are back-tested (finding table, `audit_findings.md`; "Let's do #1"), the fixes build in parallel with it, one Dispatcher chat runs it (`dispatcher_context_phase4.md`). Three pieces replace the five sketched in `audit_findings.md`, by the G07 rule (one responsibility each). Tool: Workflow (harness, no frame; the Dispatcher runs them as Agent clerks, one tests writer then two builders then landings, as Phase 2 did). Tests first by a different agent than the builders (CLAUDE.md "The script"; harness pieces are sim-side by that rule).

- HARNESS-mm-8, metrics correctness (briefs/builder_mm8.md): findings 1, 3 to 23, 25 to 27, 32 to 35, plus the `--weeks` back-test table, the baselines (M04 7.26 lab, M08 1229, M19a 0) and the `[prices]` rows. Owns `scripts/specfactory/method_metrics.py`, `method_metrics_runs.py`, `method_metrics_cli.py`, `method_thresholds.toml`, `tests/specfactory/test_method_metrics.py`, `tests/specfactory/fixtures/method_metrics/*`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- HARNESS-mm-9, gate row csv (briefs/builder_mm9.md): findings 2 and 24. Owns `scripts/specfactory/merge_gate.sh`, `tests/specfactory/test_gate_row.py`, `tests/specfactory/test_sdk_runs.py`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- RECORDS-mm-2, records repair (briefs/records_clerk_mm2.md): the eight mangled gate rows rewritten from the gate logs, the empty run rows deleted, the 32 workflow scripts moved (DEC-workflow-scripts-move-2026-10-27), the W43 snapshot re-written by the fixed script, the back-test table saved. Owns `docs/northstar/plans/push/gate_runs.csv`, `docs/northstar/plans/method_rev3_2026-10-26/metrics/*`, `scripts/specfactory/workflows/*`. [P docs/northstar/story_reviews/westley/decisions.md:65]
- Decisions folded in: DEC-m04-docs-only-week (M04 NA when no product commit), DEC-scripts-tests-not-product (scripts/tests-only commits count in neither M04 term), DEC-m01-lab-ratio-kept, DEC-workflow-scripts-move. Q5: M21b is the week sum, counting only DRIFT lines that are breaches (rules `polling`, `gate_runs`, `live_tree`, `main_push`, `wakeups`, `spawn_model`, `fable_spawns`, `messages`; not `context`, which M08 counts, and not `code_edits` from doer or engineer transcripts); its number is set from the back-test (draft stays 2 until then). [P docs/northstar/story_reviews/westley/decisions.md:65]
- Thresholds: none approved yet. The back-test (`method_metrics.py --weeks 2026-W38..2026-W44`) lands as `metrics/backtest_2026-10-27.md`; Westley approves from it. [P docs/northstar/story_reviews/westley/decisions.md:65]
- CLAUDE.md: `CLAUDE_trim_draft.md` lands in the retro commit after Westley's word on the section moves (not in this hand-off). [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A10 (2026-10-27): token ledger and the coordinator metrics

- HARNESS-mm-12 (Tool: Workflow; tests first): `scripts/specfactory/token_ledger.py` (about 150 lines, reusing `method_metrics_runs.py`'s transcript loader): per day and per piece, planned tokens (from `method_thresholds.toml` `[estimates]`, new table: task type, median, ceiling, calls cap) against actual (transcript usage, cache reads at face value), the week's running total against the allotment (DEC-daily-allotment-2026-10-27: 300 M a day, 60 Dispatcher, 180 pieces, 60 reserve). New metrics in `method_metrics_runs.py`: M25 tokens per landed piece against its ceiling (FAIL above); M26 week total against the allotment (report only); M27 text-only turns per event-triggered episode in the Dispatcher chat (DRAFT ≤ 0.1); M28 cross-session messages per day (DRAFT ≤ 4); M29 fix-pass runs per piece (DRAFT ≤ 1). Owns `token_ledger.py`, `tests/specfactory/test_token_ledger.py`; the metric additions land in `method_metrics_runs.py` and the toml after HARNESS-mm-8 (ordering edge). Also: `method_metrics.py` line 37 `METHOD_PATHS` still names `docs/northstar/plans/workflows_2026-10-07/` for the workflow scripts; it adds `scripts/specfactory/workflows/` (Dispatcher 2026-10-28). Also: M06 and M07 price only sub-agent and SDK runs, so top-level coordinator chats are left out; W43 reads Fable $0 of $324 while the W43 transcripts hold about 585 M Fable tokens (roughly $360 at the toml prices, about half the week's dollars). M06 and M07 add every top-level session's usage, priced by its model (Architect, back-test review 2026-10-28). [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A11 (2026-10-28): after the workflow-script move

- HARNESS-mm-14 (Tool: Workflow; a doer, no tests writer: the existing `tests/specfactory/test_launch_check.py` gains one case first by the same doer, allowed because the piece is a path constant): `scripts/specfactory/launch_check.sh` `WF_DIR` becomes `scripts/specfactory/workflows` (DEC-workflow-scripts-move-2026-10-27); a script under the old path is rejected with the same message. Records with it, one clerk: `pieces.toml` rows VG-RECORD and VG-CONTRACT-E3 point at the new path and RECORDS-mm-2's `owns_glob` for `scripts/specfactory/workflows/*` is dropped (landed, ownership returns to the lane rows); `metrics/README.md` keeps the re-snapshotted 2026-W43 row only; the three pre-landing HARNESS-mm-8 rows (base and footprint rejects) are deleted from `~/Projects/om-push/gate_runs.csv`. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A12 (2026-10-28): the weekly run before the timer is installed

- HARNESS-mm-15 (Tool: Workflow; one doer writes the three test cases first in `tests/specfactory/test_method_weekly.py`, then the fix, allowed because each is a one-line change in a shell script): three defects found reading `scripts/specfactory/method_weekly.sh` before installing the timer (Architect 2026-10-28). (1) The week: `date -d "last week"` on Sunday 23:00 names the week before the one ending (on 2026-11-01 it gives W43, not W44); the week is `date +%G-W%V` when run on a Sunday, else `date -d "last sunday" +%G-W%V`. (2) The exit: `method_metrics.py --write` exits 1 on any FAIL and `set -e` then ends the script before the commit, so a week with a FAIL is never recorded; the call keeps its output and continues (`|| true` with a comment naming the reason). (3) The reap: the script runs `wt.py reap` for real, which Westley has not ordered (the reap stays halted); the script runs `wt.py reap --dry-run` only and writes its output into the week's commit as `metrics/<week>_reap_dryrun.txt`; the real reap returns on his word as its own change. Test cases: the dry-run prints the right week for a Sunday and a Wednesday (fake `date` via `OM_NOW`, a new optional variable); a FAIL from the metrics still reaches the commit line; no line runs `wt.py reap` without `--dry-run`. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A13 (2026-10-28): threshold approvals on their own; the token ledger paused

Westley 2026-10-28: "skip the ledger for now, let's just finish the #4 I asked for from the original plan." HARNESS-mm-12 (A10) is paused, not landed; its branches stay on origin unlanded and its worktrees are finished with `wt.py done`. Phase 4d lands on its own:

- HARNESS-mm-16 (Tool: Workflow; one doer writes the test case first, then the edit, allowed because it is a data change in one file): in `scripts/specfactory/method_thresholds.toml` every `approved = ""` becomes `approved = "Westley 2026-10-28"` and table M21b `value` becomes 8 (DEC-thresholds-approved-2026-10-28); nothing else in the file. Test case in `tests/specfactory/test_method_metrics.py`: every table with an `approved` key reads `Westley 2026-10-28`, M21b is 8, M01 is 1.5, and an approved metric inside its limit prints PASS, not DRAFT. [P docs/northstar/story_reviews/westley/decisions.md:65]
- Order at the Dispatcher: HARNESS-mm-16, then HARNESS-mm-15 (A12, the weekly run), then the timer is installed. HARNESS-mm-12 waits for Westley's word. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A14 (2026-10-28): the token ledger resumes, in parallel

- Westley 2026-10-28: "have the dispatcher build the token-ledger and that repair in parallel with 15/16." HARNESS-mm-12 (A10: `token_ledger.py`, the `[estimates]` table, M25 to M29, and the repair of M06 and M07 to include coordinator spend) builds now beside HARNESS-mm-16 and HARNESS-mm-15. The approvals stay in mm-16 (A13); mm-12's briefs drop them, and its new tables M25 to M29 start DRAFT. Landings stay one at a time through the gate: mm-16, then mm-15, then mm-12 (it owns the toml after mm-16; ordering edge). [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A15 (2026-10-28): a faster merge gate, through the chain already specced

Westley asked the Dispatcher (2026-10-28) to parallelise the gate. Measured on the mm-16 landing (4,220 s): the four regression stages are 4,094 s of it (csim 1,801 s, specfactory 1,858 s, transport 393 s, qa_t1 42 s), each running twice, on main (`baseline: computed <sha>`) and on the candidate. The baseline cache is keyed on the main sha and every records commit between landings moves main, so it never hits. 16 cores, load 5.7 to 7.4 during the gate.

The fix is already designed and audited: `docs/northstar/plans/harness/gate-parallel-scout.md` (2026-10-13, design B) and the lane H pieces in `plans/2026-10-07-visible-game-spec.md` lines 442 to 454, queued since 2026-10-23 and never launched because the beta programme paused: HARNESS-gate-cache-seed, then HARNESS-csim-xdist, HARNESS-gate-reorder, HARNESS-gate-concurrent (HARNESS-gate-tiers and -remote later). No new piece is made; the chain is launched from its own spec paragraphs, with one amendment to the first:

- HARNESS-gate-cache-seed, amended: the cache key is each suite's input hash (the git tree hash of the paths the suite reads, declared in a new `scripts/specfactory/suite_inputs.toml` derived from one `strace -f -e trace=openat,execve` run of each suite on main), with the harness sha, instead of the pushed sha, so a records commit between the gate and the next landing no longer misses the cache (the paragraph's own stated hole); and a stage whose candidate input hash equals the base's prints `OK inputs unchanged <hash>` and runs nothing. Positive controls: an edit under a declared input runs the stage; an edit outside skips it; a sample run that opens a repo file outside the declared set fails a coverage test; a different harness sha ignores the cache. [P docs/northstar/story_reviews/westley/decisions.md:65]
- Order: HARNESS-mm-12 lands on the current gate after mm-15 and is not held. HARNESS-gate-cache-seed builds now (its dependencies are all attached) and lands after mm-12; then HARNESS-csim-xdist, then HARNESS-gate-reorder, then HARNESS-gate-concurrent, each measured by its gate row's `stage_s` against the previous. The scout's estimate for the end state: 1,300 to 1,900 s per cached gate (22 to 32 minutes) against 4,220 s today; a harness-only landing skips the csim, qa_t1 and transport stages once cache-seed is in. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A16 (2026-10-28): the timer is installed; two follow-ups

The weekly timer is installed on Westley's machine (`om-method-metrics.timer`, next run Sunday 2026-11-01 23:00, Persistent) after HARNESS-mm-15 landed (9f2d233a). Two things found doing it:

- HARNESS-mm-18 (Tool: Workflow; one doer, the test cases first in `tests/specfactory/test_method_weekly.py`, node-id acceptance as mm-15): (1) the unit's `ExecStart` runs `method_weekly.sh` from the live checkout, which lags main (its copy lacked mm-15's fixes and would have run the real reap); the installed unit carries a drop-in `~/.config/systemd/user/om-method-metrics.service.d/run-from-main.conf` that runs the script as it is on origin/main, and the repo's unit file gains the same `ExecStart` so the drop-in can be deleted after this lands; (2) the reap dry-run output goes to `$WT/metrics/` (a new top-level folder in the repo) instead of `docs/northstar/plans/method_rev3_2026-10-26/metrics/`; it moves there. Lands before Sunday 2026-11-01 23:00, ahead of HARNESS-gate-cache-seed in the serial queue. [P docs/northstar/story_reviews/westley/decisions.md:65]

## Amendment A17 (2026-10-29): M27 measured the wrong thing

The Dispatcher's first W44 reading, M27 = 1.0 (56 text-only turns in 56 event episodes), is exact, not noise: every wakeup ends with one text-only closing turn, so the ratio is 1.0 by construction. The context audit of 2026-10-27 had read the 252 text-only turns of 2026-10-19 and 10-20 as status chatter; they were the closing lines of 252 wakeups (252 episodes), one each. Item 1 of DEC-coordinator-wakeups-2026-10-27 as worded saves nothing; `dispatcher.md` step 3 is reworded (fewer wakeups, smaller context). The levers that change the cost are the number of wakeups and the context size per call.

- HARNESS-mm-19 (Tool: Workflow; one doer, the test case first): M27 becomes the Dispatcher's median context tokens per event episode summed over its calls (the cost of one wakeup), DRAFT ceiling 1.0 M (about three calls at 330k; Westley's number when he approves); its old definition and its test case are retired with a TD row. Also: assistant entries that share one `message.id` (Claude Code writes one entry per content block) count as one call in M27 and M28. Queued after HARNESS-gate-cache-seed. [P docs/northstar/story_reviews/westley/decisions.md:65]
