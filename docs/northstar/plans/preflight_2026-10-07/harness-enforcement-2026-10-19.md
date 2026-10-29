# Harness pre-flight fact sheet, origin/main 3c85c9498044fdef8aaeb5803a328f77982af651 (2026-10-19)
Worktree: ~/Projects/om-push/wt/preflight-harness (detached). Paths below are repo-relative to it. Facts only, no design.

## 1. scripts/specfactory/spec_provenance.py (191 lines, stdlib only)
- CLI: `spec_provenance.py <spec.md>` (usage line 179: `usage: spec_provenance.py <spec.md>`). Exit 1 any finding, 0 none, 2 usage (not exactly 1 arg or not a file) (main, :177-187). Output `<argv path>:<line>: (<n>) <text>` (:186). Findings are a sorted set (:184).
- Unit (split_units :46-73, class Unit :39-43): heading line (`raw.startswith("#")` :63) is its own unit; a list item (LIST_ITEM :34 `^\s*(?:[-*+]|\d+[.)])\s+`) starts a unit and absorbs following non-blank non-list lines (:68-69); otherwise a blank-separated paragraph (:70-71). Blank line flushes and clears lead (:61-62). Fenced ``` blocks are skipped entirely (:57-60). Unit.line = first line. A list item inherits the "lead-in" paragraph before it as tag cover (`lead` :52-53; tag_text :43).
- CODE_SPAN :25 `re.compile(r"`[^`]*`")`. Unit.plain = CODE_SPAN.sub(" ", text) (:42). All reasons except 2 search `u.plain`, so a tag inside backticks does not count. Reason 2 uses `u.text` (unblanked).
- Tag regexes (verbatim):
  - TAG_START :26 `\[W Q-|\[W \d{4}-\d\d-\d\d|\[B R-|\[P |\[DRAFT-` (so `[W ` needs Q- or a date to count as cover)
  - B_TAG :36 `\[B (R-[^\]]*)\]` ; RULE_ID :35 `R-\d+-\d+`
  - [P ...] parse in reason3 :93 `\[P ([^\]]*)\]` ; CITATION :30 `[A-Za-z_][\w./-]*:\d+`
  - [W Q-..] parse in reason5 :110 `\[W (Q-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)`
  - [DRAFT-..] parse in reason6 :117 `\[(DRAFT-[A-Za-z0-9-]+)\]`
  - BEHAVIOUR_WORDS :27 `\b(when|then|shows|sees|draws|refuses|accepts|default)\b` (re.I) ; NUMBER :28 `(?<![\w.\-/#])\d` ; STAND_INS :29 ("liberty","as the builder drafted","architect default") ; APPROVAL :31 ; PIECE_ID :32-33 ; CLASH_PAIRS :22 `[("refuse","clear"),("ring","never form rings")]`.
  - There is no parse of a `[W ...]` quote's text, a quantifier, `[ASSERT ...]`, or a pin on `[B R-id]` anywhere. A `[W <date>...]` tag only covers reason 1; it is never validated beyond TAG_START.
- Seven reasons (emitting line):
  1. :80 "behaviour unit without a provenance tag: <first 70 chars>" (NUMBER or BEHAVIOUR_WORDS in plain, and no TAG_START in tag_text; reason1 :76-80)
  2. :88 "words that stand in for a source: {p!r}" (reason2 :83-88)
  3. :95 "[P x] has no file:line citation"; :97 "heading claims approval with no file:line citation" (reason3 :91-97)
  4. :105 "[B R-id] is not in docs/bible/epics" (reason4 :100-105; checks each R-id in the tag against ctx["rules"])
  5. :112 "[W Q-x] register row is not closed" (reason5 :108-112)
  6. :119 "[DRAFT-x] has no ledger or register row" (reason6 :115-119)
  7. :136/:139/:142 "<ids>: 'refuse' at line N versus 'clear' at line M" / "'ring' ... versus 'never form rings' in the rule cited at line" (reason7 :122-143; per shared PIECE_ID)
- Context loading: find_root :149-153 = first ancestor of the spec holding `docs/bible/epics`, else SCRIPT_REPO (:24). load_context :156-174:
  - epics: `root/docs/bible/epics/*.md`; `rules[rid]` = concatenation of EVERY line that contains the id anywhere (:160-161), not only the `- R-id  Given` line. No hashing exists.
  - register `root/docs/northstar/ambiguity_register.md` and ledger `root/docs/northstar/plans/push_ledger_2026-09-22.md` (hardcoded names :162-163): every line starting `|` is appended to `rows` (:170). For the register only, a row whose cell[0] starts `Q-` and has >4 cells sets `closed[Q] = cells[4].lower().startswith("closed")` (:172-173) -- cell index 4 = Status. Naive `split("|")` (:171): the register row Q-191-15 (register line 361) has extra unescaped pipes, so its cells shift (awk saw 12 fields instead of 8).
  - DRAFT rows: reason6 searches the whole `rows` text (all table lines of both files, any column) for the name with word boundaries `(?<![\w-])NAME(?![\w-])` (:118). Bare `DRAFT-x` in ledger table rows qualifies; there is no separate DRAFT registry file.
- Invocation: only from pre_gate.sh :116 (env PRE_GATE_SPEC). No other caller on main (grep scripts/ tests/). It is not in merge_gate.sh.
- Observation (ran it): `python3 scripts/specfactory/spec_provenance.py docs/northstar/plans/2026-10-07-visible-game-spec.md` prints reason counts 1:151, 2:12, 3:2, 7:26 (191 findings), because that spec's tags are written inside backticks (blanked by CODE_SPAN). The lint is not run on that file anywhere on main.

## 2. scripts/specfactory/pre_gate.sh (123 lines)
- Header :1-15. `set -uo pipefail` (:15), no `-e`. Usage `pre_gate.sh <candidate_worktree> <base_ref> <piece_ids> [<test path> ...]`; exit 2 on usage/missing worktree (:17-24); exit 1 verdict REJECT (:118-121), 0 OK (:122-123).
- Vars :26-36: HERE, WT, BASE, PIECES, `shift 3`, VENV_PYTHON="${PRE_GATE_PYTHON:-$HOME/Projects/ouroboros-manifold/.venv/bin/python}" (:31), MERGE_GATE="${PRE_GATE_MERGE_GATE:-$HERE/merge_gate.sh}" (:32), REJECTED=0 (:34), OUT=mktemp, trap rm (:35-36).
- Steps in order: (1) noise :38-79 (git status --porcelain -uall for .uid / .import offenders; deleted .import in diff); (2) gate :81-89 `"$MERGE_GATE" --revert "$WT" "$BASE" "$PIECES"`; (3) tests :91-113 (per arg: .gd via scripts/run_godot_tests.sh, tests/qa/desktop* under xvfb-run + pytest, else pytest -x); then the provenance step :115-116; verdict :118-123.
- spec_provenance invocation, :116 (one line, quoted whole):
  `[[ -n "${PRE_GATE_SPEC:-}" ]] && { "$VENV_PYTHON" "$HERE/spec_provenance.py" "$WT/$PRE_GATE_SPEC" && echo "PRE_GATE provenance OK $PRE_GATE_SPEC" || { echo "PRE_GATE provenance REJECT $PRE_GATE_SPEC"; REJECTED=1; }; }`
  Spec path is relative to the candidate worktree. spec_provenance stdout/stderr go straight to the pre_gate output. Unset or empty PRE_GATE_SPEC means no output.
- Step pattern to copy (gate step :82-89): run command, capture `rc=$?`, `if (( rc != 0 )); then echo "PRE_GATE <step> REJECT <detail>"; REJECTED=1; else echo "PRE_GATE <step> OK <detail>"; fi`. Line format regex in the test: `^PRE_GATE (noise|gate|tests|verdict) (OK|REJECT|WARN)\b` (tests/specfactory/test_pre_gate.py:18; "provenance" is not in it).

## 3. scripts/specfactory/status_check.py (193 lines)
- CLI (:166-175): `--repo` (default repo of the script), `--base` (origin/main), `--programme`, `--pieces`, `--stories`, `--reviews`, `--roadmap` (defaults :25-29, relative paths resolved against --repo by `at()` :178-180). Output `STATUS <check> OK|DRIFT <detail>` (:188); exit 0 all OK else 1 (:189). No usage exit 2.
- Checks (called :183-186):
  - lane_table (:55-74): table headed `| Lane | On main |` in docs/northstar/plans/2026-10-07-visible-game-programme.md; every 7-40 hex sha in the "On main" cells must be an ancestor of --base (`git merge-base --is-ancestor`); DRIFT line :73; "no table headed" :59.
  - pieces (:102-111): parse_pieces :77-99 is a line regex parser, NOT tomllib; reads per [[piece]] only `id = "..."` and, from the line starting `status =`, `state = "..."` and `attach_sha = "..."`. DRIFT :107 when state=="attached" with a sha that is not an ancestor. in_flight ids are listed in the OK line :110-111. Other keys (script, args) are ignored.
  - seen (:114-136): reads every `*.md` in docs/northstar/story_reviews/ (top directory only via glob, so westley/README.md is not read); rows with cells[VERDICT_COL=7] == "approved" (:33, :121, 9-column format, index 7 = "Westley verdict") counted; compared with docs/bible/stories.md rows whose Status cell (column found from a header row starting `Story`, default index 3) starts with "Seen" (:132). DRIFT :135 when counts differ. Counts only; it does not match story ids.
  - roadmap (:139-163): section `## 1. Now building` of docs/northstar/ROADMAP.md holds no row starting `| Visible game lane` (:155) and the "visible game programme" row names the programme file.
- Does NOT read docs/northstar/ambiguity_register.md (grep: no occurrence in the file). No check on register status, "until Westley", or closed rows exists.
- Not called by merge_gate.sh (grep -n status_check scripts/specfactory/merge_gate.sh: no hit). Only references: CLAUDE.md:72 (guard 7, "after every landing"), docs/northstar/plans/workflows_2026-10-07/{dispatcher.md:48 area, drift_audit.md, context_dispatcher_2026-10-10.md}, vg-harness-method.js (which built it). Nothing automatic runs it on main.

## 4. scripts/specfactory/owner_lint.py (98 lines)
- Rule (docstring :2-21, in_flight_overlaps :52-72): reuses pieces.check_owns_disjoint unmodified, keeps a finding only when BOTH pieces are in flight (:70). In flight = `piece_state` not in ("attached","done") (:36-49); `status` may be a bare string or a table `{state=...}` (:40-45). A missing status counts as in flight (returns "").
- pieces.check_owns_disjoint (scripts/specfactory/pieces.py:110-130): for every pair, every owns/owns_glob pattern pair that `patterns_overlap` is a FAIL UNLESS one piece is in the other's TRANSITIVE depends_on chain (`if qid in chain_p or pid in chain_q: continue`, :121-124). So: two queued pieces may own the same file ONLY if one depends_on (transitively) the other; a depends_on edge exempts the pair. Finding text: "owns overlap with no depends_on ordering between them: P owns 'x', Q owns 'y'" (:127-128).
- CLI `--pieces` only (:81). Prints `<level> <pair>: <msg>` per finding then `OWNER LINT FAILED (n in-flight overlap(s))` exit 1, or `OWNER LINT OK (n pieces checked)` exit 0 (:87-94). Called by merge_gate.sh :211-221 (stage 5c) against the gate repo's own pieces.toml, also in --revert mode.
- pieces.toml status values seen on main (tomllib count over 197 rows): table attached 113, table queued 40, bare "attached" 36, bare "pending" 3, table superseded 1, table landed 1, table pending 1, table in_flight 1, missing status 1. "queued", "landed", "superseded" are all counted as in flight by owner_lint (only "attached"/"done" are not).

## 5. tests/specfactory/ (51 .py files + fixtures/ dir with spec_rev10.md (290 lines, the rev 10 spec) and 205a-e05-collision-lottery.md)
One line each (the file's own `# spec:`/docstring subject):
alg_constants (briefs two-day-push decision 5 F3); card_lint, card_slice, libm_lint (spec_factory.md pipeline pre-queue gate); card_regen (harness defects R22); chain_graph (JSON DAG emitter); chain_sim (PX-16 scheduler simulation); checksum_trace (two-day-push item 3); conftest_bindings, sig_table (decision 1 / F1b); control_liveness (PX-15); escalator_fix_probe (PX-17/18); fixture_defects (PX-13); gate_a94_steps, gate_control_liveness, gate_look_and_times, gate_mergebase_lab, gate_placeholder_controls, gate_playthrough, gate_regression_paths, gate_sig_blocked (merge_gate.sh stages, one rulings addendum each); gd_reach_lint (HARNESS-gdreach); green_check (drift gate AC-5); integration_check; journal (HARNESS-journal); lane_plays_check (HARNESS-laneplays); merge_gate, merge_gate_support (two-day-push item 1); method_check; owner_lint; pack_validate, pack_validate_movement; parent_patch_fence (PX-14); pieces (item 4); pp_contract, pp_contract_guard; prefetch_measure (PX-19); pre_gate; reach_lint, size_lint (witty-cuddling-goblet Wave 0 item 3); red_check; runner_declared_time (A87); signatures_internal; snapshot_fixture; spec_provenance; status_check; story_reviews_format (G4 queue format); suite_regression (PX-7); tactical_trace; tick_closure (PF-8); undertest_check (PX-06).
- Invocation: 41 of 51 import subprocess; the tests for the four relevant scripts run them as subprocess by path. Examples:
  - tests/specfactory/test_spec_provenance.py:62-64 `def _lint(spec): return subprocess.run([sys.executable, str(SCRIPT), str(spec)], cwd=REPO, capture_output=True, text=True)`
  - tests/specfactory/test_owner_lint.py:21-25 subprocess `[sys.executable, str(OWNER_LINT), "--pieces", str(pieces_path)]`; the same file also imports it (`import owner_lint as ol`, :11-12).
  - tests/specfactory/test_status_check.py:153 `subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path, timeout=60)`; test_pre_gate.py runs the shell script with env.
- Fixtures built in-test, no fixture repo on disk:
  - test_spec_provenance.py:34-60,78-90: constants EPIC_TEXT (rule R-990-01 in docs/bible/epics/E-99-test.md), REGISTER_TEXT (6-column table, Q-990-01 closed, Q-990-02 open), LEDGER_TEXT (DRAFT-test-thing), PASSING_SPEC; `_tree(tmp_path, spec_text)` writes root/docs/bible/epics, docs/northstar/ambiguity_register.md, docs/northstar/plans/push_ledger_2026-09-22.md and spec.md. 17 tests (:105-265), one per reason plus a rev10 acceptance (>=39 findings on fixtures/spec_rev10.md, :265).
  - test_pre_gate.py:29-45 `_make_repo`: `git init` in tmp_path, base commit on branch "base", HEAD one commit ahead; a stub merge gate via PRE_GATE_MERGE_GATE; PRE_GATE_SPEC cases at :208-225 (env_extra).
  - test_status_check.py:35-40 REVIEW_HEADER (9-column), builds a throwaway git repo with two commits, branch "base", a side-branch commit.
  - test_story_reviews_format.py:11-37 checks the real README.md header against the 9 COLUMNS.

## 6. Tag inventory under docs/northstar/plans/**/*.md
Command: ad-hoc python (scratchpad/inv.py: per file, `re.findall` on raw text vs on text with `` `[^`]*` `` removed; "inside" = raw minus blanked count, "bare" = count outside backticks). Also `grep -rIc '\[W ' docs`.
- `[B R-`: inside backticks / bare = 35 / 10 in total. Files: 2026-10-07-visible-game-spec.md 29 / 10; 2026-10-19-enforcement-and-redirect.md 3 / 0; drift_checks/2026-10-11-spec-authoring.md 1 / 0; push_ledger_2026-09-22.md 1 / 0; workflows_2026-10-07/rules.md 1 / 0. (docs/ outside plans: pieces.toml has 1 in a comment line.)
- `[W `: inside / bare = 29 / 2. Files: visible-game-spec 22 / 1; enforcement-and-redirect 3 / 0; drift_audits/2026-10-19-decision-consistency.md 0 / 1; drift_audits/2026-10-19-decision-to-spec.md 1 / 0; drift_checks/2026-10-11-spec-authoring.md 1 / 0; rules.md 2 / 0. (docs/northstar/ROADMAP.md has 1 outside plans.) The only two bare `[W ` hits are in a drift audit report.
- `[DRAFT-`: inside / bare-in-brackets = 21 / 4 (visible-game-spec 16 / 3; enforcement-and-redirect 2 / 0; spec-authoring 1 / 0; push_ledger 1 / 1; rules.md 1 / 0). Bare `DRAFT-name` without brackets: 137 (push_ledger 106; d-view-spec 11; skill-lab-rev2-spec 6; drift_audits/2026-10-18 4; transition-mockup-spec 3; the rest 1 to 2 each).
- `[P `: inside 39 / bare 0 (visible-game-spec 37; spec-authoring 1; rules.md 1).
- Consequence: nearly every real tag on main is inside backticks (as documentation or a quoted instance); no spec on main is written the way spec_provenance expects (bare tags).
- `[W` quotes with a quantifier word (at least, at most, never, always, every, all, only, no more than, any age, within): regex `\[W [^\n]*?\](?=[\s`.,;)]|$)` over raw text, case-insensitive whole word: visible-game-spec.md 3 of 23 tags; every other file 0. Rough (a quote containing `]` is cut short); treat the figure as a lower bound.

## 7. Tests naming rules
- Files under tests/ containing an `R-\d{3}-\d{2}` token: 525 (421 .py, 96 .gd, 6 .c, 2 .md; dirs: csim 311, transport 41, qa 44, skilllab 17, specfactory 11, net 4, simviewer 1, long 1, top-level .gd/.py the rest). Command: `grep -rlE 'R-[0-9]{3}-[0-9]{2}' tests | wc -l`.
- Citation styles (per-file classification, a file may count in several; python scratch, .py/.gd/.c only):
  1. Module docstring or header string in lines 1-15: 368 files. e.g. tests/transport/test_pipe_mission_refuse_chronicle.py:1 `"""B3 + B5 (mission-plays plan, R-065-02): the refusal reaches the chronicle.`
  2. Comment line (`#`): 247 files (112 in the first 15 lines, 135 later). e.g. tests/test_time_jump_replay.gd:4 `# G-C3 client unit 2 (A48 item 13, A52, A59, A65; E-09 R-069-03, R-069-05;`
  3. Assertion message: 107 files. e.g. tests/test_time_jump_replay.gd:171 `_assert(absf(elapsed - 5.0) <= TOL_SYNTH, "R-069-03: a 10-tick replay took ...` ; tests/transport/test_pipe_mission_frame_briefing_fields.py:74 `assert len(primary) == 1, "R-075-01: exactly one primary objective, got %r" % objs`
  Also test docstrings (193 files cite in later docstrings), e.g. tests/test_debrief_live_ctypes.py:97 `"""S-077 R-077-01/02: pipe band int matches ctypes band for the same world."""`.
- Fixed-position header: none. Closest: a free-form line `Rules:` / `Rules proved:` / `# Rules proved:` in 27 files (17 .py, 10 .gd), at varying lines (line 3 to 19), format varies. Examples: tests/csim/test_VG_E_ke2.py:4 `Rules: R-218-01 (ground structure count capped at the slope count), R-218-05 (...), R-218-06 (...)`; tests/test_tactical_camera.gd:5 `# Rules proved: E-16 S-103 R-103-01 (free camera, no forced follow, pan and`; tests/csim/test_PP_C_g5_direct_fire.py:4 `Rules proved: R-164-02 'Given a target at ...'`; tests/test_vg_a_a16.gd:14 `# Rules quoted word for word (method rev 3), and which test proves each:`.
- tests/csim/test_VG_P_p1_layout.py:1-50: docstring lines 1-37+ ("Spec: ..." line 3; "Rules proved, quoted word for word (method rev 3; test_the_quoted_rules_are_the_bibles checks each quote against the files)" ~line 17), then `E-22 (docs/bible/epics/E-22-economy-and-bases.md):` and the full rule lines `R-177-02  Given ...` plus the rule's table rows. There is an existing quote-check test: test_VG_P_p1_layout.py:672-688 `test_the_quoted_rules_are_the_bibles`: for each id reads the epic, `text = [l[2:] for l in lines if l.startswith("- " + rid + " ")]`, `assert len(text) == 1`, and `" ".join(text[0].split()) in doc` (whitespace-normalised substring of the module docstring); the R-177-02 table rows are taken from `e22[i:i + 14]` lines starting `|`; also checks the register's `verbatim: "(Q191-03: ...)" Read as` text.
- tests/csim/test_VG_E_ke2.py:1-30: docstring `"""VG-CONTRACT-E2 (K-e2): ... Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 8, "Lane E1 part a2..." / Rules: R-218-01 (...), R-218-05 (...), R-218-06 (...; liberty 2026-10-10).` No rule text quoted, ids only.
- .gd example tests/test_vg_a_camera.gd:1-10: `extends SceneTree` then comment header `# VG-A piece A11. Proves S-234's unblocked half and R-103-01/02 (...), R-103-04 (...), spec A11 (...)`. tests/test_vg_b_b23.gd:3-12: `# Proves (bible E-16, docs/bible/epics/E-16-...md):` then `#   S-106 "A 3D star map ..."` and `#   R-106-01  Given the world view, When drawn, ...` (rule text copied in comments).

## 8. Epic rule lines (docs/bible/epics/*.md, 22 files)
- Shape: `- R-###-##  Given <x>, When <y>, Then <z>.` (two spaces after the id). Examples: E-10-*.md:34 `- R-072-01  Given the player's regions and every region adjacent to them, When the candidate pool is built, Then each (region, archetype) pair whose trigger condition holds enters the pool; ...`; :35 `- R-072-02  Given a candidate, When urgency is computed, Then urgency = clamp(0.4 · deficit + ...)`.
- Command: `grep -hE '^- R-[0-9]{3}-[0-9]{2}( |$)' *.md | wc -l` = 1188 rule lines; `grep -hoE '^- R-[0-9]{3}-[0-9]{2}' | sort | uniq -d` = no output; sort -u = 1188. So 1188 ids, 0 duplicates as line starts. 1290 lines in epics mention some R-id (rules plus cross references).
- 14 rule lines are not `  Given` form (status text instead): E-07:107 (R-054-01 "Deferred with the feature..."), E-11:61 (R-082-10 "Shape ruled ..."), E-13:118 (R-100-04 "DRAFT (Westley, ...; Q-100-01): Given a unit ..."), E-16:41 (R-103-10 "Idea only..."), E-17:168 (R-165-01), E-17:180-185 (R-166-01..06), E-19:119 (R-159-01), E-21:102 (R-157-01), E-22:203 (R-177-03 "Removed 2026-10-06").
- Multi-line: each rule is one physical line. Checked by script: only 1 of 1188 rule lines is followed by a non-blank line that is not a `- ` bullet or heading: E-01-layer-system.md:53 is an indented sub-bullet `  - Note: ...`. Tables that belong to a rule (R-177-02's) follow after the rule line (test uses the 14 lines after it) -- they are not part of the rule line.

## 9. Review queue rows (docs/northstar/story_reviews/)
- Header of B.md:3, F.md:3, README.md:9 (all identical, 9 columns), verbatim:
  `| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date |`
  westley/README.md:9 (different, 6 columns): `| File here | Story | Lane | Queue row (run id) | Original | What to judge |`. Rows B.md 16 table lines, F.md 3, westley/README.md 26 table lines. Other queue files: A, C, D, E, P, V .md (P.md holds prototype rows).
- Who writes rows (grep -rn story_reviews scripts/ scripts/specfactory/workflows/*.js | head -20): no script writes them. Workflow text only: vg-wave1.js:17 (G4 piece defines the format files), vg-wave1.js:37, vg-wave2b8-laneB-land6.js:23, vg-wave2b9-laneB-land7.js:25, vg-wave5-laneE1b-r2.js:4,13,42,76,77,101,106,107, vg-wave2b11-laneB-look.js:33, vg-resume-laneE1a.js:65 (story-play runner / landing-clerk agent prompts). The rule text is docs/northstar/plans/workflows_2026-10-07/rules.md:35 ("Shots to the queue (method rev 2): for every player-facing piece in the landing, run its story play ... copy the png and qa_state json to docs/northstar/..."). Scripts that mention the dir: scripts/specfactory/pieces.py:43-46 (SHARED_RECORD_GLOBS = ("docs/northstar/story_reviews/westley/*",), shared by rule, not owned) and status_check.py:28.
- Row fields present now: story, lane, run id (e.g. `20261008-1234-dbd1372`, timestamp-commit), screenshot path, qa_state file, reviewer (`sonnet`), reviewer verdict free text (`no. 80 systems, 73 owned, band Overview, d=180, ...`), Westley verdict, date. There is no legend field, no unit-of-number field, no camera-band field: "legend" appears 0 times in any queue file; a camera band appears only inside the free-text reviewer verdict in 6 lines of B.md (grep -ciE 'band (Overview|Local|Galaxy|Region)|camera band' B.md = 6). Run id is its own column (cell index 2). Rows checked: B.md:5-7 (S-106, S-107, S-108), F.md:5-6 (S-141, S-140).
- README format spec: story_reviews/README.md:5-13; test_story_reviews_format.py checks the header (9 columns) against it.

## 10. Workflow scripts (docs/northstar/plans/workflows_2026-10-07/)
- 39 .js files (vg-harness-method, vg-kh, vg-resume-laneB-names / C-land2 / D / E1a / F-fog, vg-split, vg-wave1, wave2-contract, wave2b ... wave2b13, wave2c-pipe, wave3-laneA, wave3c, wave4-laneC, wave4c, wave5-laneE1 / E1a2 / E1a3 / E1b / E1b-r2, wave6 ... wave6e, wave9-laneE1q). No `*.args.json` on main (ls, git ls-files grep: none). Non-js: rules.md, dispatcher.md, drift_audit.md, method_check.md, journals, two context_*.md. Newest by git log: vg-wave9-laneE1q.js (2026-10-11 17:53).
- Args are read from a global `args` (no JSON file load): vg-wave9-laneE1q.js:27-30
  `const STAGE = (args && args.stage) || 'contract'` / `const SKIP = (args && args.skip) || {}` / `const RULINGS = (args && args.rulings) || ''` / `const DERIVED = (args && args.derived) || ''`. Across all scripts the keys read are args.base (16 uses), skip 9, part 8, rulings 6, derived 4, draft_dir 3, w, support, stage, pipe. Launch shape in header comments: `Workflow({scriptPath, args: {stage: 'contract'}})` (:4-5).
- Preflight phase, vg-wave9-laneE1q.js:53-59 (first lines; line 53 `phase('Preflight')`, then):
  `const common = \`(1) the spec has the section "Lane E1 part c ..." at rev 10d or later (quote the title line's rev); (2) pieces.toml: a VG-CONTRACT-E5 row owning the K-e5 files ...\`` ; `const stageChecks = STAGE === 'contract' ? \`(6) OM_SAVE_FORMAT_VERSION is 9 in csrc/om_internal.h, ...\` : ...` ; :58 `const pre = await agent(\`${RULES.replace('worktree add -b <branch>', 'worktree add --detach')}\nRole: read-only scout (Engineer), rules.md section (c); detached worktree of origin/main, suffix vg-e1q-pre, removed after. Stage ${STAGE}. Check and quote with file:line: ${common} ${stageChecks} Report ...\`)` ; :59 `if (!pre || pre.blocking) return { stage: STAGE, pre, stopped: 'preflight' }`. Meta/phases :22-26. The Preflight phase is one scout agent call (an LLM prompt), not code that reads files or hashes; the script has no `fs`/`crypto`.
- Self-hashing: `grep -n "createHash\|sha256\|readFileSync\|crypto" *.js` = no hit in any script on main. No script hashes its own source or args.
- Drafts copies: ~/Projects/om-push/scratch/drafts-2026-10-12/ has 44 .js (plus .orig*, .pre-*, .parse.mjs variants, and args-a16.json, args-aroute.json, args-w2.json, args-wave12.json; args-w2.json starts `{ "audited": true, "layout": "..." ...`). Names present in BOTH main and drafts: 0 (`comm -12` empty), so no `cmp` pairs. Draft scripts are wave10, wave11, wave12 and wave2b14 -- all newer than anything on main, none landed.

## 11. docs/northstar/plans/push/pieces.toml (2700 lines, 197 [[piece]] rows)
- Header comment :1-12 describes owns / owns_glob / acceptance / tests_pending / depends_on.
- Key counts (tomllib): id 197, manager 197, owns 197, depends_on 197, status 196, acceptance 195, wave 187, size_estimate 178, owns_glob 166, tests_pending 146. No `script` key, no `args` key (also grep for `^script|^args` empty). `status` is a bare string (e.g. "pending", "attached") in 39 rows, otherwise an inline table `{ state = "...", attach_sha = "..." }`.
- One row in full (docs/northstar/plans/push/pieces.toml:499-507):
```
[[piece]]
id = "MK-chronicle"
manager = "mockup"
wave = 3
owns = []
owns_glob = ["scenes/mockups/chronicle/**", "docs/northstar/research/mockups/chronicle/**"]
acceptance = []
depends_on = []
status = { state = "attached", attach_sha = "6abaff8" }
```
  A typical live row (VG-A16, :1953-1961) also has `tests_pending = false` and `size_estimate = "..."`, trailing `# comment` after depends_on.
- Tooling that reads pieces.toml (grep -rln pieces.toml scripts/): merge_gate.sh (PIECES_TOML :20; passes to owner_lint, size_lint, undertest, pieces), merge_gate_support.py:151 (tomllib), owner_lint.py (via pieces.load_pieces), pieces.py:50 (tomllib `data.get("piece", [])`; no unknown-key rejection found: grep for KNOWN_KEYS/unknown key empty), size_lint.py, status_check.py (own line regex parser, :77-99).

## 12. docs/northstar/ambiguity_register.md (516 lines)
- Header (:7) verbatim: `| Flag | Epic / story | Question | Candidate answers | Status | Answer |` (6 cells).
- Rows beginning `| Q-`: 508. Status first word: closed 399 (+1 long "closed 2026-10-02: Westley accepts a residual ..." +1 "closed (default a, number is DRAFT-start-fraction; ...)" = 401 start with closed), open 103 (+1 "open (structure and names answered)" = 104), superseded 1, deferred 1, "-" 1 (Q-191-15, register :361, its text contains unescaped pipes so cells shift; true status not parsed). Command: `grep '^| Q-' | awk -F'|' '{s=$6; ...}'` ($6 = Status).
- Readers (grep -rln ambiguity_register scripts/ tests/ docs/northstar/plans/workflows_2026-10-07/): scripts/specfactory/spec_provenance.py (:162), card_lint.py (:462), dor_check.py (:27), fold_answers.py (:33), scripts/derive_agora_rules.py (:29); tests: tests/specfactory/test_spec_provenance.py, test_card_lint.py (+ fixtures/205a-e05-collision-lottery.md), tests/csim/test_VG_P_p1_layout.py, tests/csim/scale/test_scale_C2_jump.py, tests/test_vg_d_view.gd; workflows: drift_audit.md, vg-wave5-laneE1a2.js, vg-wave9-laneE1q.js. status_check.py and merge_gate.sh do not read it.
- Status values with a parenthesis exist ("closed (default a, ...)", "open (structure and names answered)"), so an exact-match status check would see these as distinct values; spec_provenance uses startswith("closed") (:173).
- Closed rows whose Answer cell (cell 6) contains "default": 15 rows (awk: status starts "closed", $7 matches `until Westley|Westley to confirm|[Dd]efault`): Q-E03-01, Q-005-04, Q-021-06, Q-113-01, Q-105-02, Q-232-03, Q-233-01, Q-239-01, Q-242-01, Q-242-04, Q-191-11, Q-191-13, Q-210-07, Q-215-01, Q-218-07. Of these only Q-218-07 contains "until Westley" in the answer. "Westley to confirm" in a closed row's Answer cell: 0. The phrase "Westley to confirm" occurs once in the file, register line 77 (Q-022-02, status closed), in a non-Answer cell. "until Westley" in any column of any row: Q-191-15 (status "-"), Q-218-07 (closed), Q-193-08, Q-193-09, Q-168-06, Q-B23b-01 (all open). No row has status `reading (Westley to confirm)`.

## 13. scripts/specfactory/merge_gate.sh (615 lines)
- Helpers :74-77 `reject() { gate_line "$1" REJECT "${*:2}"; REJECTED=1; }`, ok, warn, harness; `gate_line` prints `GATE <step> <status> <detail> [<n>s]`. Exit 0/1/3. `--revert` flag :27-29 (REVERT_MODE): revert exits after stage 5c (:226-231), so only make, lints, footprint run.
- Stage headers (name, line): 1 make 81; 2 libm_lint 103; 3 alg_constants --lint 112; 4 footprint fence 129; 4b gd class_name uniqueness 139; 5 symbol-ownership lint 148; 5a signature table BLOCKED items 158; 5a2 signature artifacts emit-clean 168; 5b reachability lint 178; 5b-gd Godot reach lint 201; 5c single-owner lint 211; (revert-mode exit :226-231) ; 5c control liveness 233; 6 suite_regression 253; 7 piece acceptance ids green 290; 6c godot import 297; 7b piece acceptance ids godot side 405; 8 tests/qa/t1 retired 425; 9 tests/transport 431; 9b playthrough 486; 9b lane_plays 498; 10 checksum_trace O0 vs O2 512; 10b tactical_trace 540; 11 undertest_check (WARN only) 573; 12 size_lint (WARN only) 583; 13 look (WARN only) 596; final exit :611-615.
- status_check.py is not a stage. No stage reads story_reviews/.
- Stage pattern to copy (single-owner lint, :211-221):
```
OWNER_LOG="$SCRATCH_ROOT/owner_lint.log"
"$PYTHON" "$GATE_DIR/owner_lint.py" --pieces "$PIECES_TOML" >"$OWNER_LOG" 2>&1
if [[ $? -ne 0 ]]; then
    reject owner_lint "$(cat "$OWNER_LOG")"
else
    ok owner_lint "$(tail_oneline "$OWNER_LOG" 1)"
fi
```
  Tools always come from the gate's own repo (`$GATE_DIR`, header :11-15), never the candidate. A stage placed before the REVERT_MODE exit (after 5c at :221) runs in --revert (and so in pre_gate); one placed after :231 runs only in the full gate. A WARN-only stage uses `warn <name> "<detail>"` (stages 11-13).

## Could not determine / caveats
- Which gate runs `status_check.py` after landings: no automatic caller found on main (only prose in CLAUDE.md:72 and dispatcher docs).
- Quantifier-word count in `[W` quotes (fact 6) is a lower bound from a line-regex over backticked tags; no parser for tag text exists to count it exactly.
- Register Q-191-15 (line 361) status unreadable by pipe split (stray `|` in its text).
- `cmp` of workflow scripts vs drafts: no names in common, so none run.
