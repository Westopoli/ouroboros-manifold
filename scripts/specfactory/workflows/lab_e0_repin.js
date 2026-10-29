export const meta = {
  name: 'lab-e0-repin',
  description: 'LAB-REV2-E0 re-pin: merge origin/main into push/labrev2-e0 (ABI 8 to 9, save 12 to 13), tests branch with raised base literals, golden re-record, red/green check, consistency audit, pre_gate and push of both branches (contract piece, one landing by a separate clerk)',
  phases: [{ title: 'Merge' }, { title: 'Goldens' }, { title: 'Redcheck' }, { title: 'Audit' }, { title: 'Push' }],
}
// Spec: amendment_e0_rebase_2026-10-29 (Architect ouroboros-manifold-41; DEC-lab-E0-rebase-2026-10-29).
// SECOND-FABLE AUDIT GATE (contract piece, as vg-wave13-laneE7r.js): the Dispatcher spawns the architect agent (subagent_type: architect) on the amendment (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md from line 114 on origin/main) plus this script, and passes the verdict in args.audit ('pass'). Findings, if any, are folded into the amendment before launch. Westley's "Plan approved" stands (the Dispatcher confirms).
// Launch: Workflow({scriptPath, args: {audit: 'pass'}}). args.skip = { merge: 'push/labrev2-e0-r', tests: 'push/labrev2-e0-tests-r', goldens: 'push/labrev2-e0-tests-r' } steps already ok (resume rule: nothing landed re-runs).
// Local refs: the two branches are created in the shared repo and passed between agents by local branch name (worktrees share the object store); nothing goes to origin until the Push phase, after pre_gate.
// Branch names: push/labrev2-e0-r (code, from 4decde94), push/labrev2-e0-tests-r (tests, from 787d5146). Worktree names: lab-e0r, lab-e0tr, lab-e0g, lab-e0red-main, lab-e0red-merged, lab-e0audit, lab-e0push.
// Ledger: no ledger edits on either branch. TD-LAB-E0-base-literals is already on main (commit 51a2d2bd). TD-LAB-E0-goldens is written by the landing clerk from the goldens agent's report.
// Audited 2026-10-29 by the second-Fable architect agent (two reports); findings folded in this revision.
// Piece for pre_gate: LAB-REV2-E0 (its owns on main already hold the golden files, commit 51a2d2bd; this script touches neither pieces.toml nor the ledger).
if (!(args && args.audit === 'pass')) return { stopped: 'no-audit', message: 'args.audit must be "pass": the Dispatcher spawns the architect agent on the amendment plus this script first' }
const SKIP = (args && args.skip) || {}
const PIECE = 'LAB-REV2-E0'
const E0 = 'push/labrev2-e0-r'
const E0T = 'push/labrev2-e0-tests-r'
const E0_OLD = '4decde94'
const E0T_OLD = '787d5146'
const PIN_FILES = [
  'csrc/ouroboros_sim.h', 'csrc/om_internal.h', 'csrc/pipe/pipe_internal.h', 'csrc/checksum_full.c', 'csrc/terrain.c',
  'docs/northstar/spec_factory/signatures.toml', 'docs/architecture.md', 'scenes/load_game/load_game.gd',
  'tests/test_load_game_wrong_version.gd', 'tests/csim/conftest.py', 'tests/csim/test_E02_S020_abi.py',
  'tests/csim/test_E01_T3_contract.py', 'tests/csim/test_VG_E_contract.py', 'tests/csim/test_VG_E_ke3.py',
  'tests/csim/test_VG_E_ke5.py', 'tests/csim/test_PP_settings.py', 'tests/specfactory/test_pp_contract.py',
  'tests/transport/test_pipe_shapes.py', 'tests/transport/test_pipe_vg_e.py', 'tests/csim/test_E16_C2_save_version.py',
  'tests/csim/test_E16_B5_save_version.py',
]
const CONFLICTS = [
  'csrc/ouroboros_sim.h', 'csrc/om_internal.h', 'csrc/checksum_full.c', 'csrc/terrain.c', 'docs/architecture.md',
  'docs/northstar/spec_factory/signatures.toml', 'tests/csim/test_E01_T3_contract.py', 'tests/csim/test_VG_E_contract.py',
  'tests/csim/test_VG_E_ke3.py', 'tests/csim/test_VG_E_ke5.py',
]
const NON_PIN = ['csrc/tactical_move.c', 'csrc/unit.c', 'docs/northstar/plans/push/pp_contract.md', 'scripts/specfactory/reach_allowlist.toml']
const GOLDEN_FILES = ['tests/csim/test_VG_W_w1_planner.py', 'tests/csim/test_VG_E_e1q_field.py', 'tests/simviewer/']
const CONTRACT_TEST = 'tests/specfactory/test_pp_contract_lab_rev2.py'
const GREP = "git grep -nE 'OM_ABI_VERSION|OM_SAVE_FORMAT_VERSION|EXPECTED_ABI|EXPECTED_VERSION|SAVE_FORMAT' -- . ':!docs/northstar/plans' ':!docs/bible_history' ':!docs/northstar/story_reviews' ':!scripts/specfactory/workflows' ':!docs/legacy' ':!docs/northstar/proving_ground' ':!tests/specfactory/fixtures'"
const NUMBERS = 'OM_ABI_VERSION 9 (csrc/ouroboros_sim.h:31), OM_SAVE_FORMAT_VERSION 13 (csrc/om_internal.h:37), OM_PIPE_SAVE_FORMAT_VERSION 13 (csrc/pipe/pipe_internal.h:18), CURRENT_SAVE_VERSION 13 (scenes/load_game/load_game.gd:5), conftest EXPECTED_ABI_VERSION 9 and OM_TP__COUNT / conftest _COUNT 66 to 67 (the FIRING_ARC_DEG binding stays)'

const RULES = `Read docs/northstar/plans/workflows_2026-10-07/rules.md first (git show origin/main:docs/northstar/plans/workflows_2026-10-07/rules.md); your role's section is your rule set. Rules: model Sonnet 5.5; you spawn nothing; think tersely; report once at the end, no interim notices; STOP at 60 tool calls (DRAFT-e0-call-cap) and report what is left. Stage files by name only, never git add -A or commit -a. Worktree ONLY through python3 ~/Projects/ouroboros-manifold/scripts/specfactory/wt.py new <name> --owner <your label> --purpose "<words>" --base <ref> [--branch <branch>] (path ~/Projects/om-push/wt/<name>); every command names an absolute path; never use ~/Projects/ouroboros-manifold as a working tree and never touch it. First git -C ~/Projects/ouroboros-manifold fetch -q origin. NEVER run git rebase, a forced push, git stash, git commit --amend, make clean, rm -rf or git worktree remove; no command whose target you cannot write out as a literal path; if a command might be destructive or unresolvable, leave it and list it. Never push to main. Build: make && make pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg in the worktree. Python ~/Projects/ouroboros-manifold/.venv/bin/python (run pytest as that python -m pytest -q -p no:cacheprovider). Do not stage *.uid, *.import or build outputs. Do not push (the Push phase does it); commit locally on your branch. Run wt.py done <path> <sha> only for a tree whose branch is pushed (none before the Push phase). STOP RULES: any conflict outside the files you are told to resolve; any file outside your list changed; a number nobody gave; a golden diff outside the movement section; anything the brief leaves open. A STOP reports ok=false with stop_reason and the decisive lines pasted verbatim; you do not work around it. Pins of this piece: ${NUMBERS}.`

const REPORT = { type: 'object', properties: { ok: { type: 'boolean' }, branch: { type: 'string' }, sha: { type: 'string' }, summary: { type: 'string' }, stop_reason: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, hits: { type: 'array', items: { type: 'string' } }, goldens: { type: 'array', items: { type: 'string' } }, lines: { type: 'array', items: { type: 'string' } } }, required: ['ok', 'branch', 'sha', 'summary'] }
const VERDICT = { type: 'object', properties: { pass: { type: 'boolean' }, evidence: { type: 'string' } }, required: ['pass', 'evidence'] }
const done = (label) => SKIP[label] ? { ok: true, branch: SKIP[label], sha: 'skipped', summary: `skipped: ${SKIP[label]} already ok` } : null
const opts = (label, phaseName, schema) => ({ label, phase: phaseName, schema, agentType: 'engineer', model: 'sonnet' })

let out = {}

phase('Merge')
// Code branch and tests branch touch disjoint branches: run them in parallel.
const mkMerge = () => done('merge') || agent(`${RULES}
Role: merge engineer (Engineer), rules.md section (a), contract piece ${PIECE}. Task: bring the E0 code branch up to date by MERGE (never rebase).
1. wt.py new lab-e0r --owner merge-e0 --purpose "LAB-REV2-E0 re-pin" --base ${E0_OLD} --branch ${E0} (verify git rev-parse origin/push/labrev2-e0 starts with ${E0_OLD}, else STOP).
2. In that worktree: git merge --no-edit origin/main. List the conflicting files with git diff --name-only --diff-filter=U. They must be a subset of exactly these ten: ${CONFLICTS.join(', ')}. ANY other conflicting file is a STOP (paste the list). Resolve only those: keep main's text and E0's additions, with E0's numbers moved to ABI 9 and save format 13 (E0 originally bumped 7 to 8 and 11 to 12; main already took 8 and 12 in VG-CONTRACT-E7, commit d3bf1614). Keep E7's om_mission_get_force_group binding and signature row together with E0's additions in conftest and signatures.toml.
3. Re-pin to 9 and 13 every version pin in these files (grep each; line numbers move): ${PIN_FILES.join(', ')}. Specifics: tests/csim/conftest.py EXPECTED_ABI_VERSION 9 and its _COUNT 66 to 67; tests/csim/test_VG_E_contract.py also the stale text near line 8; test_VG_E_ke3.py text near line 84; test_VG_E_ke5.py text near lines 634 to 645; tests/csim/test_E16_C2_save_version.py EXPECTED_VERSION 13; tests/csim/test_E16_B5_save_version.py EXPECTED_VERSION 13 AND the "later build" word 13 to 14 at about lines 95 and 98, in both the docstring and the code (the textual merge is silent here because main already has 13; without this edit the refusal test breaks). Non-pin files in E0's diff that must merge clean and are not re-pinned: ${NON_PIN.join(', ')}. The OM_PP_ROWS row { OM_PP_REAL, OM_PP_ARC_DEFAULT, OM_PP_ARC_LO, OM_PP_ARC_HI } must sit after the FLYER_SEEN row with OM_TP__COUNT 67. Edit no file outside the pin list, the ten conflicts and the four non-pin files.
4. Leftover grep, from the worktree root: ${GREP} ; list every hit that still says 8 or 12 as a version (or 13 as the B5 "later build" word). The list must be empty apart from history text (comments recording that E7 took 8 and 12 and earlier versions were 7 and 11 are history; paste them under "hits" each tagged with the word history). A hit in a pin file or one of the four non-pin files that is not history: fix it. A hit in any other file is listed under "hits" tagged with the word outside and is never a STOP (the landing clerk judges it).
5. Build (make && make pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg) and run the .py pin files of the list with pytest. Pin files that fail only because of a golden hash are NOT yours (list them in summary, do not edit; the Goldens phase takes them). Any other red is a STOP.
6. Commit the merge, and the re-pin as a second commit, on ${E0}; do NOT push. Report: branch ${E0}, sha, files = the conflict files you resolved, hits = every grep hit still at 8/12 with the history verdict (empty list if none), summary = make result and pytest tail lines.`, opts('merge-e0', 'Merge', REPORT))

const mkTests = () => done('tests') || agent(`${RULES}
Role: test writer (Engineer), rules.md section (d), tests branch of ${PIECE}. The only source edit: ${CONTRACT_TEST} lines about 59 to 60, BASE_ABI_BEFORE_E0 = 7 to 8 and BASE_SAVE_BEFORE_E0 = 11 to 12 (the file's own comment names this owed edit; classed test-defect, ledger row TD-LAB-E0-base-literals already on main, Architect amendment 2026-10-29; the guard test_base_literals_equal_the_numbers_on_origin_main_before_e0 near line 483 is the positive control). BASE_COUNT_BEFORE_E0 stays 66.
1. wt.py new lab-e0tr --owner tests-e0 --purpose "LAB-REV2-E0 tests re-pin" --base ${E0T_OLD} --branch ${E0T} (verify origin/push/labrev2-e0-tests starts with ${E0T_OLD}, else STOP). The branch holds exactly one file, ${CONTRACT_TEST}; verify with git diff --stat origin/main...HEAD before the merge.
2. git merge --no-edit origin/main. Any conflict is a STOP.
3. Make the two-literal edit. Edit nothing else; in particular no ledger edit (the row is on main).
4. Commit on ${E0T}; do NOT push. Report: branch ${E0T}, sha, summary = git diff --stat origin/main..HEAD verbatim (expected: exactly the one contract test file).`, opts('tests-e0', 'Merge', REPORT))

const [merge, tests] = await parallel([mkMerge, mkTests])
out = { ...out, merge, tests }
if (!(merge && merge.ok)) return { ...out, stopped: 'merge' }
if (!(tests && tests.ok)) return { ...out, stopped: 'tests' }
if (merge.hits && merge.hits.some((h) => !/history|outside/i.test(h))) return { ...out, stopped: 'leftover-pins', hits: merge.hits }

phase('Goldens')
// The tests writer, not the merge engineer, re-records. E0's saved movement setting moves the movement section of the full checksum, so goldens recorded for save 12 move (TD-VG-E-27 did the same for E7). Only GOLDEN_D in test_VG_W_w1_planner.py moves; the golden commit is cherry-picked onto the tests branch, so it holds the contract test file plus that golden file.
const goldens = done('goldens') || await agent(`${RULES}
Role: test writer (Engineer), rules.md section (d), goldens of ${PIECE} (the landing clerk writes ledger row TD-LAB-E0-goldens from your report). Base: the merged E0 tree with the tests branch applied.
1. wt.py new lab-e0g --owner goldens-e0 --purpose "LAB-REV2-E0 goldens" --base ${E0T} --branch ${E0T}-g (local branch; its commit is cherry-picked onto ${E0T} at the end). In the worktree: git merge --no-edit ${E0} (local branch). Any conflict is a STOP. Build.
2. Run the goldens the way the gate runs csim (merge_gate.sh stage 6: MALLOC_PERTURB_=255 pytest over tests/csim; no gate stage names tests/simviewer, it rides suite_regression, so run it directly): MALLOC_PERTURB_=255 ~/Projects/ouroboros-manifold/.venv/bin/python -m pytest -q -p no:cacheprovider ${GOLDEN_FILES.join(' ')} under timeout 1800 and systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 -- nice -n 10. Paste the failing assertion lines. Expected result (spec): the real golden is only GOLDEN_D in tests/csim/test_VG_W_w1_planner.py. tests/csim/test_VG_E_e1q_field.py stores no golden (its save_sha256 near line 416 is a recording print) and tests/simviewer/fixtures/*.json carry the light checksum, which skips the parameters, so they do not move: they are controls and must stay green. Expected delta, per seed (1 and 3) in GOLDEN_D: save_sha256, full_ret, sections[4] (movement) and save_len (plus 8) move; checksum (the light one) and every other section stay. Any failure in e1q_field or the simviewer fixtures, any moved light checksum, or any moved non-movement section is a STOP with old and new pasted.
3. Before editing, verify the delta above by comparing per-section hashes old against new ('sections' in GOLDEN_D; use the section dump the test uses): sections[4] differs, every other section is byte-identical, checksum unchanged, save_len +8. Anything else is a STOP (paste old and new values); do not re-record it.
4. Re-record only the verified GOLDEN_D values, editing only those literals (no assertion, tolerance or logic change). Re-run the three golden targets: all green. Re-run ${CONTRACT_TEST} too.
5. No ledger edit. Edit only the golden file. Commit it in lab-e0g, then in the lab-e0tr worktree run git cherry-pick <that sha> onto ${E0T} (a conflict is a STOP); no fast-forward of ${E0T} to the -g branch, so ${E0T} holds exactly the contract test file plus the golden file. Do NOT push. The code branch ${E0} is unchanged.
Report (this is the landing clerk's source for the TD row, so complete): branch ${E0T}, sha = git -C <lab-e0tr> rev-parse HEAD after the cherry-pick, goldens = one line per golden changed as 'file :: key :: old -> new', summary = verification result per golden, lines = the failing assertion lines before the edit.`, opts('goldens-e0', 'Goldens', REPORT))
out = { ...out, goldens }
if (!(goldens && goldens.ok)) return { ...out, stopped: 'goldens' }

phase('Redcheck')
// The E0 contract tests: red on origin/main, green on the merged tree. The test file is not on main, so copy it from the tests branch into a main worktree.
const red = await agent(`${RULES}
Role: red checker (Engineer), rules.md section (d). Contract tests ${CONTRACT_TEST} for ${PIECE}.
A. Red on main: wt.py new lab-e0red-main --owner red-e0 --purpose "E0 red check" --base origin/main --branch push/labrev2-e0-redmain (local, never pushed). Write the file there with git show ${E0T}:${CONTRACT_TEST} > <worktree>/${CONTRACT_TEST} (untracked; do not commit it). Build. Run it with pytest. It MUST be red; paste the decisive failing assertion line (file:line and message) and the counts. If it is green, or fails at collection for a harness reason rather than the missing feature, STOP and paste why.
B. Green on the merged tree: wt.py new lab-e0red-merged --owner red-e0 --purpose "E0 green check" --base ${E0T} --branch push/labrev2-e0-greencheck (local, never pushed); git merge --no-edit ${E0} (conflict = STOP). Build. Run ${CONTRACT_TEST}: it MUST be fully green, with test_base_literals_equal_the_numbers_on_origin_main_before_e0 green or skipped-by-design (it skips on the merged tree, test file lines 483 to 498), and test_later_build_save_word green. Any red is a STOP with the assertion line pasted. Also run the pin .py files (${PIN_FILES.filter((f) => f.endsWith('.py')).join(' ')}) and the three golden targets (${GOLDEN_FILES.join(', ')}); all green.
Report ok, branch ${E0T}, sha = the merged tree HEAD sha you ran, lines = [main-red decisive line, merged-green pytest summary line], summary.`, opts('red-check', 'Redcheck', REPORT))
out = { ...out, red }
if (!(red && red.ok)) return { ...out, stopped: 'redcheck' }

phase('Audit')
const audit = await agent(`${RULES}
Role: consistency auditor (Engineer, fresh; you have not seen the author's reasoning), rules.md section (c), read-only; try to refute the merged tree. Scratch tree: wt.py new lab-e0audit --owner audit-e0 --purpose "E0 consistency audit" --base ${E0T} --branch push/labrev2-e0-auditview (local), then git merge --no-edit ${E0} inside it; commit nothing you keep. Check, with file:line evidence and the sha read:
1. Every pin at 9 and 13: ${NUMBERS}; pin files: ${PIN_FILES.join(', ')}; run ${GREP} and list any remaining 8/12 that is not history text.
2. The OM_PP_ROWS row { OM_PP_REAL, OM_PP_ARC_DEFAULT, OM_PP_ARC_LO, OM_PP_ARC_HI } is appended after the FLYER_SEEN row; OM_TP__COUNT and tests/csim/conftest.py _COUNT are 67.
3. No file outside LAB-REV2-E0's owns changed: list git diff --name-only origin/main...HEAD of the merged tree and compare each file with the owns of ${PIECE} in docs/northstar/plans/push/pieces.toml on origin/main; the three golden files (tests/csim/test_VG_W_w1_planner.py, tests/csim/test_VG_E_e1q_field.py, tests/simviewer/fixtures/*.json) are in its owns on main since 51a2d2bd; anything else is a fail.
4. tests/csim/conftest.py carries both E7's om_mission_get_force_group binding and E0's additions, and HARNESS-csim-xdist's change if it has landed on origin/main (git log origin/main -- tests/csim/conftest.py).
5. The goldens report (given below) lists old and new for every changed value, and no golden changed outside the movement section: check against git diff of the golden files. Goldens report: ${JSON.stringify(goldens.goldens || [])}. The tests branch holds exactly the one contract test file plus tests/csim/test_VG_W_w1_planner.py, no ledger change, no code.
Report pass (true only if all five hold) and evidence (the decisive line for each failed item, or one line per item when passing).`, opts('audit-e0', 'Audit', VERDICT))
out = { ...out, audit }
if (!(audit && audit.pass)) return { ...out, stopped: 'audit' }

phase('Push')
const push = await agent(`${RULES}
Role: push clerk (Engineer), rules.md section (a) pre-gate bullet. Both branches are local only: ${E0} (sha ${merge.sha}) and ${E0T} (sha ${goldens.sha}).
1. wt.py new lab-e0push --owner push-e0 --purpose "E0 pre_gate" --base ${E0T} --branch push/labrev2-e0-pre (local); git merge --no-edit ${E0}; conflict = STOP. Build. Run: scripts/specfactory/pre_gate.sh ~/Projects/om-push/wt/lab-e0push origin/main ${PIECE} ${CONTRACT_TEST} ${GOLDEN_FILES.slice(0, 2).join(' ')} (absolute worktree path; the three positional arguments come before the test paths). It must end 'PRE_GATE verdict OK'. Any PRE_GATE REJECT is a STOP: paste the lines and push nothing.
2. Only then push both branches by name from their own trees (plain push, no force): git -C ~/Projects/om-push/wt/lab-e0r push origin ${E0} ; git -C ~/Projects/om-push/wt/lab-e0tr push origin ${E0T}. Verify with git ls-remote origin that both shas match. If a sha you are given reads 'skipped' (resume run), use `git rev-parse` of the local branch instead.
3. wt.py done <path> <sha> for lab-e0r and lab-e0tr only. The other trees (lab-e0g, lab-e0red-main, lab-e0red-merged, lab-e0audit, lab-e0push) hold local-only commits: do not call done on them; list their paths in summary for the reaping clerk.
Report: ok, branch ${E0}, sha = pushed code sha, summary = the PRE_GATE lines verbatim plus the pushed tests sha, lines = both ls-remote lines.`, opts('pre-gate-push', 'Push', REPORT))
out = { ...out, push }
if (!(push && push.ok)) return { ...out, stopped: 'push' }

return {
  ...out,
  branches: { code: E0, codeSha: merge.sha, tests: E0T, testsSha: goldens.sha },
  goldens: goldens.goldens,
  tdRows: ['TD-LAB-E0-goldens (the landing clerk writes it from the goldens list above; TD-LAB-E0-base-literals is already on main)'],
  next: 'landing clerk (separate, the Dispatcher runs it): write TD-LAB-E0-goldens from the goldens list, merge both branches, gate, then the E2 plus E4 workflow',
}
