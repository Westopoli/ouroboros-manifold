# Piece status audit, 2026-10-02

Scope: every one of the 73 `[[piece]]` rows in `docs/northstar/plans/push/pieces.toml` at origin/main `39b6b55c`, compared with the push ledger (`docs/northstar/plans/push_ledger_2026-09-22.md`), git history on origin/main, and the files each piece owns. `pieces.toml` was not edited; the Architect lands corrections.

## Method and caveats

- Status shapes in the file: `{ state = "attached", attach_sha = ... }` (21 rows), the bare string `"pending"` (50 rows), and no status key at all (`core`, `B10c`).
- Test evidence: `tests/csim` was run on a clean worktree of origin/main with the project venv: 1191 passed, 129 failed, 60 skipped, 2 xfailed. 99 of the 129 failures are detector-control tests under `tests/csim/controls/` (the known pre-existing set; the ledger's last sweeps read 128 to 129 failures). The 30 non-control failures are: E-06 R-045-09 (1), E-10 R-078-06 (1), E-11 R-085-02 and R-085-04 (2), E-15 R-130-02 (1), E-17 S112 to S119 (25, no piece row owns E-17 tests).
- Per-piece "red" counts below are non-control csim failures inside the piece's own acceptance files. Godot-test acceptance (`*.gd`) was not run, so GDScript pieces rely on ledger rows.
- Ledger piece ids in the early day2 sweep rows ("B8 never attached", "B10b never landed") are stale; later sweeps (passes 6, 7, final, bk-41 to bk-45) supersede them. The ledger never recorded `pieces.toml` attaches after day2 for the B-series, which is why the file lags.
- "Attached" is proposed only where the acceptance suite is green or has only a documented, ruled red, and the owned file shows increments merged through the gate. Confidence is mine, not a gate result.
- Many later landings went through `merge_gate` with a "footprint REJECT, unknown piece id" accepted by hand, so the gate never wrote an attach for them.

## Requested pieces

| Piece | Status in toml | Evidence | Proposed | Conf |
|---|---|---|---|---|
| B10 | attached (617827a) | ledger day1 "attach B10" row (the first, empty-sha row was corrected; real attach `617827a`, tag `attach/B10`). Acceptance 6 files, 0 red. | attached (correct) | high |
| B10b | pending | Ledger day2 rows: B10b REJECT then "B10b never landed" sweep (E-11 S084 x4, S085 x4, S087 x8 red). Now S084 and S087 files are green; only R-085-02 and R-085-04 in `test_E11_S085_long_enough_to_think.py` are red (ledger bk-41: "possibly new from B10c-11"; open since). `csrc/unit.c` 28 commits, last `18b393ff`. | attached with two open reds (R-085-02, R-085-04), or leave pending until those two are ruled. Architect call. | medium |
| B10c | no status key | No acceptance. 16 commits on main with subject `B10c-N` (up to B10c-11, `cf1a44c3` auto-Fortify fix; list ends `ff2d92a2`, 2026-09-25). Depends on B10b. | attached, and add the missing `status` line | medium |
| B11 | pending | 9 commits `B11-N`; ledger "merge B11-1", "B11-6-r", "B11-8" OK. E-12 acceptance 6 files, 0 red (ledger pass 7 showed 1 red R-093-02, since fixed). `csrc/fog.c` 16 commits, last `9826c415`. | attached | high |
| B13 | pending | 9 commits `B13-N`; ledger "B13-4", "B13-6", "B13-7 (W-1f)" merged; bk-44 "E14: 0f/22p". E-14 acceptance 6 files, 0 red. `csrc/enemy_macro.c` 12 commits, last `e1d91528` (F3 contact skip). | attached | high |
| core | no status key | Wave-0, M0 direct to main, never merged through the gate. All six owned files exist and changed through 2026-10-01 (e.g. HDR5 `38e935a4`, `e3b6de2d`). No acceptance. | n/a: add `status = "attached"` for uniformity or document wave-0 rows as status-less | high |
| A2-contract | pending | Ledger day10 "A2 LANDED": `push/A2pipe-land` merged as `57f0fcb`, contract commit `c5ff2085` on main (declares `om_mission_refresh_context`, `om_mission_last_region`). Branches `push/A2`, `push/A2-contract`, `push/A2pipe-land` all ancestors of main. Landed with accepted footprint REJECT "unknown piece id A2". | attached (57f0fcb) | high |
| A94-contract | pending | Branch `origin/push/A94-contract` (`e3005090`, 2026-10-02: 2 missing rows, 15 internal rows, 4 param renames, doc comments to notes, header regenerate) is 1 commit ahead of main, not merged. No ledger LANDED row. Owner rows themselves are on main (`4f22acff`, `35a9026c` "marked reviewed"). | pending, in flight (branch pushed, awaiting gate and land) | high |
| A94-harness | pending | `push/A94-harness-fixes` (`2e7f1c23`) merged on main (ledger day17 row "A94 harness fixes LANDED", gated with piece id none). `push/A94-harness-followup` (`5187b375`, 2 commits ahead: EXPECTED_MODULE +15, conftest regenerated) not merged; it depends on A94-contract. | pending, partially landed (first unit landed, follow-up in flight) | high |

## Pieces whose overlapping `owns` currently collide

`pieces.py --check` reports no owns-overlap finding. Its only failure is the known `T1: acceptance id did not collect (tests/transport batch rc=2)`. `owner_lint.py` prints `OWNER LINT OK (73 pieces checked)`. The file-sharing groups below all overlap but are ordered by `depends_on`, so the lint accepts them:

- `csrc/unit.c`: B10, B10b, B10c (B10c after B10b after B10).
- `csrc/generational.c`: B7, B7b, B5-chronicle, B6-lifecycle, B6-collapse-pick (B7 then B5-chronicle then B6-lifecycle then B6-collapse-pick then B7b).
- `csrc/chronicle.c`: B8, B6-lifecycle.
- `csrc/diplomacy.c`: B5, B5b. `csrc/tactical_move.c`: B12, B12b.
- `csrc/ouroboros_sim.h`: core, A2-contract, A94-contract (core, then A2-contract, then A94-contract). `csrc/om_internal.h`: core, A94-contract. `docs/northstar/spec_factory/signatures.toml`: A2-contract, A94-contract.
- `autoload/c_bridge.gd`: C2, T2g, C3, C4, C5, C8. `scenes/galaxy/**`, `scenes/mission_briefing/**`, `scenes/debrief/**`, `scenes/tactical_c/**`, `scenes/main_menu/**`, `scenes/world/chronicle_*`: C8 with their original owners.
- `scripts/specfactory/[!m]*` (A94-harness) against K1's `scripts/specfactory/pack_validate.py`: ordered via A94-harness `depends_on = ["K1"]`.

Two soft spots, not lint failures: `A94-harness` owns `tests/csim/conftest.py` and `scripts/specfactory/[!m]*`, so any new specfactory file whose name starts with "m" is unowned until a row names it (documented in the file's own comment). And `G-legacytests`, `G-qadesktoptests` etc. own paths with `owns = []` plus globs; footprint fencing for those is by glob only.

## Full table

Red counts are non-control csim failures in the piece's acceptance files. "Landed" evidence cites SHAs on origin/main. Status "ok" means toml status already matches.

| Piece | Toml status | Evidence | Proposed | Conf |
|---|---|---|---|---|
| B1 | attached 4b2ae50 | ledger "attach B1"; later A81 `66daaa64` merge (piece B1); E-04 0 red | ok | high |
| B2 | attached 35964fd | ledger "attach B2"; 0 red | ok | high |
| B3 | attached ee5ef97 | ledger "attach B3"; 0 red | ok | high |
| B4 | attached 45c4441 | ledger "attach B4" (day2); 0 red | ok | high |
| B5 | pending | `csrc/diplomacy.c` 10 commits, last `3f293bf8`; 27 commits mention B5 (B5-chr, B5-chr2, B5-loadscreen etc.); ledger `217af934` "B5 + B7 + T1-b7 LANDED". E-06 acceptance 7 files, 1 red: R-045-09 (balance finding, ledger day16 A88/A90, awaiting Westley, not skipped) | attached, R-045-09 open | medium |
| B5b | pending | No `B5b` commit subjects. Acceptance `test_E06_S048_three_tiers_of_technology.py` 0 red. Same file as B5. | attached (acceptance green); verify S-048 landed under which commit | low |
| B6 | attached 2f918f1 | ledger "attach B6"; 0 red; later lifecycle (B6-lifecycle) landed on top | ok | high |
| B7 | attached 84bdfa5 | ledger "attach B7"; E-08 0 red | ok | high |
| B7b | pending | Acceptance `test_E08_S055_...` 0 red; ledger day2 B7b leftovers (R-055-04, R-055-05, R-064-04) all resolved by pass 7 "E-08 50p/0f"; only commit named B7b is the ordering row `1b8e5f38` | attached | medium |
| B8 | pending | Ledger day2 sweep "chronicle.c never attached" is stale; pass 7 and final "E-09 39p/0f"; today E-09 acceptance 7 files 0 red; `csrc/chronicle.c` 18 commits, last `414960ae`; G-C2, G-C3, REGNAMES landed on top | attached | high |
| B9 | pending | B9-9-r3 merged (day2), 16 `B9-N` commits, A3fb, A3fb-pins landed; acceptance 9 files, 1 red R-078-06 (ledger: pre-existing S078, never fixed) | attached, R-078-06 open | medium |
| B10 | attached 617827a | see requested table | ok | high |
| B10b | pending | see requested table | attached with 2 reds, or hold | medium |
| B10c | none | see requested table | attached, add status | medium |
| B11 | pending | see requested table | attached | high |
| B12 | pending | 14 `B12-N` commits (B12-11-r, B12-12, B12-13, B12-14-r merged); E-13 acceptance 7 files, 0 red (R-099-01 fixed as test-defect, day6) | attached | high |
| B12b | pending | `f929ef48`; acceptance `test_E13_S096_four_commands.py` 0 red (ledger day2: R-096-01..05 red then; green now) | attached | medium |
| B13 | pending | see requested table | attached | high |
| B14 | pending | 9 `B14-N` commits (B14-5-r, B14-6, B14-7-r, B14-8 merged); E-15 acceptance 6 files, 1 red R-130-02 (ledger bk-41 "pre-existing", open) | attached, R-130-02 open | medium |
| B15m | pending | 7 `B15m-N` commits (B15m-1, B15m-5-r merged); acceptance 6 files 0 red. Note E-17 mapgen tests (25 red) belong to no piece row. | attached | high |
| C7 | attached 9782557 | ledger day1 "attach C7" | ok | high |
| T1 | attached 5296b14 | ledger "attach T1", tag `attach/T1`; `pieces.py --check` T1 transport-collect failure is a check problem (rc=2 collecting `tests/transport` bare dir), not a status problem | ok | high |
| C2 | attached a3e6dfb | ledger "attach C2" | ok | high |
| K1 | attached 84107fd | ledger "attach K1, K2" | ok | high |
| Q2 | pending | `scripts/qa/rts_detectors.py` on main, one commit `07c724be` (2026-09-24, "qa(Q2): rts detectors, four bug catalog checks + run_all"); ledger day2 "merge Q2 REJECT" on two pre-existing t1 controls, sweep notes then say tests/qa/t1 now collects (31p/2f, the 2f are the known controls); 3 mentions in git log | attached | medium |
| T2c | pending | `csrc/save.c` 3 commits, last `3f293bf8`; ledger T2c-2 rejected twice on symbol ownership day2, then bk-44 "E16: 0f/9p"; `test_E16_S111_saving.py` 0 red today | attached | high |
| T2g | attached 36535f1 | ledger day1 "attach T2g" | ok | high |
| C3 | attached 2531652 | ledger "attach C3" | ok | high |
| C4 | attached 85c6f4d | ledger "attach C4" | ok | high |
| C5 | attached d429d15 | ledger "attach C5" | ok | high |
| K2 | attached a59b13e | ledger day2 "attach K1, K2" | ok | high |
| Q1 | attached d7cf54c4 | owns `agora/projects/ouroboros/**` outside this repo, 0 commits here; sha `d7cf54c4` is in-repo. Not verifiable from this tree. | ok (unverified) | low |
| MK-layers | attached eb42a70 | files last touched at `eb42a707` | ok | medium |
| MK-chronicle | attached 6abaff8 | research dir last `6abaff84`, scenes later touched `037ed262` (09-28) | ok | medium |
| C8 | attached 9f9f8de | ledger day1 "attach C8" | ok | high |
| MK-harness | pending | Ledger day1 "merge MK-harness": `mockup/harness-pass2` (`ff6da0a`) on main; owned files `scripts/mockup_qa.sh` (7 commits), `scripts/mockup_verify.sh`, `scenes/mockups/_shared/**`, `scenes/mockups/landscape/qa/**` all present, last touched 2026-09-22 | attached | medium |
| C1 | attached 764ed59 | ledger "attach C1" | ok | high |
| core | none | see requested table | n/a, add status | high |
| G-uidatabus | pending | Owner-only gap row, `owns = []`, `tests_pending`. Target `autoload/ui_data_bus.gd` has 12 commits, last `980bf65e` (2026-10-01). No landing row of its own. | leave pending or mark "owner-only"; no build to attach | low |
| G-tacticalbridge | pending | Same shape; `autoload/tactical_bridge.gd` 10 commits, last `0170a6ac` | same | low |
| G-simbridge | pending | `4f9f54d8` removed dead push-signal wiring (HEAD of the recent history). Same shape. | same | low |
| G-errorscreen | pending | `scenes/error_screen/**` last `0c18655a` 2026-09-28; `tests/test_error_screen.gd` | same | low |
| G-settings | pending | `scenes/settings/**` last `980bf65e` (C3-G5 landed day13) | same | low |
| G-eralib | pending | `scenes/era_library/**` last `a425a08b`; ERA-screen-impl merged `b57d4efe` | same | low |
| G-bugreport | pending | `scenes/bug_report/**`, `autoload/bug_report_manager.gd` last `f23f989c` | same | low |
| G-debug | pending | `scenes/debug/**` last `6fb9680c` | same | low |
| G-projectgodot | pending | `project.godot` 16 commits; the live checkout has an uncommitted change on it (Westley's, untouched) | same | low |
| G-swarmarchive | pending | `.swarm/**` last `e950f2e1` 2026-09-22 | same | low |
| G-legacytactical | pending | `scenes/tactical/**` last `009c99ac` | same | low |
| G-mockupqa | pending | mockup qa dirs last touched 2026-09-22 | same | low |
| G-qadesktoptests | pending | `tests/qa/desktop/**` last `c217c016` | same | low |
| G-legacytests | pending | listed tests: 3 of 6 paths absent on main (`test_cover_render.gd`, `test_input_router_control_groups.gd`, `test_input_router_selection.gd`: commit `eeb6fd9`... removed or moved); stale owns entries | review owns list; fix before attaching | medium |
| G-timejump | pending | `scenes/world/time_jump_sequencer.gd` 13 commits, last `6fb9680c` 2026-10-02 | same as other G rows | low |
| G-tacticalvisibility | pending | `scripts/tactical/visibility.gd` absent on main (3 commits touching the path, last `009c99ac` deleted or moved it) | stale owns path; drop or repoint | medium |
| G-debugoverlay | pending | `autoload/debug_overlay.gd`, `4daebc83` G4 gated by flag | same as other G rows | low |
| G-missionmetrics | pending | single old commit 2026-04-20 | same | low |
| G-wsinputsanitizer | pending | last `f1224ae2` 2026-09-14 | same | low |
| C6-cmd | pending | `scenes/commander_assign/` does not exist; no commit names C6-cmd | pending (not started) | high |
| C6-refuse | pending | `scenes/mission_refuse/` does not exist; no commit names C6-refuse | pending (not started) | high |
| B5-chronicle | pending | ordering row `da3888e4`; ledger day13 "B5-chr2 + B5-chr ... LANDED" (candidate on `b1d53b7e`); 2 commits mention the id | attached, but verify the "chain wiring in gen_time_jump" scope fully landed (this row is mission-plays plan B5, ledger names B5-chr) | low |
| B6-lifecycle | pending | ledger day14 "B6-lifecycle ... LANDED", save version 3 to 4 (`61277731`) | attached | high |
| B6-collapse-pick | pending | `4fc2dcd3` "land B6-collapse-pick with TD-collapse-lifecycle"; ledger day14 row `eb3b4e6a`; acceptance `test_E08_S062_collapse_pick.py` 0 red | attached | high |
| G-errorpanel | pending | ledger `ff35638c` "G2 error panels LANDED"; both owned files on main (`caedf7ac`) | attached | high |
| G-flags | pending | `autoload/feature_flags.gd` exists, last `4daebc83` (G4, `ENABLE_DEBUG_OVERLAY` default false); only the owner-row commit `49a8be98` names the id; no LANDED row naming G-flags | attached (file exists and is used by G4); confirm with M3 | medium |
| G-eramanifest | pending | ERA-validator and ERA-screen merges (`ff4a74af`, `b57d4efe`); manifests changed in `089770b5` | attached | medium |
| DOCS-arch | pending | `docs/architecture.md` 58 commits; `ceaae31b` "A4-frame-docs ... DOCS-arch owner"; mission frame contract landed | attached (ongoing docs owner; consider a standing status) | medium |
| HARNESS-sigblocked | pending | ledger day8 "merge A68-gate-impl landed 51c02ada" (sig_blocked step) | attached | high |
| HARNESS-symown | pending | merge `17a5d991` (symbol_ownership comment-only prototype handling); `scale_gated_tests.txt` added with A98 | attached | high |
| G-infopanel | pending | merge `3e234131` "A82 region names, info panels read chronicle_names" | attached | high |
| HARNESS-runnertime | pending | merge `d0b696ac` (A87 runner-declared time impl); ledger row `67b0ea4c` | attached | high |
| A94-harness | pending | see requested table | pending, partial | high |
| A94-contract | pending | see requested table | pending, in flight | high |
| A2-contract | pending | see requested table | attached 57f0fcb | high |

## Counts

- Rows whose status looks wrong (proposed change from the toml value): 29.
  - Pending that should be attached: B5, B5b, B7b, B8, B9, B10b (with caveat), B11, B12, B12b, B13, B14, B15m, T2c, Q2, MK-harness, A2-contract, B5-chronicle, B6-lifecycle, B6-collapse-pick, G-errorpanel, G-flags, G-eramanifest, DOCS-arch, HARNESS-sigblocked, HARNESS-symown, G-infopanel, HARNESS-runnertime (27).
  - Status key missing: B10c (should be attached), core (n/a) (2).
- Rows correct as is: the 21 attached rows (Q1 and the MK-* rows unverifiable from this tree), C6-cmd, C6-refuse, A94-harness, A94-contract.
- Rows with stale owns paths (not status): G-legacytests (3 of 6 paths absent), G-tacticalvisibility (path absent).
- G-* ownership-only rows (19 of the G rows, not counted above): no build to attach; "pending" is not wrong but means "owner row only". Architect should decide whether those need a status at all.
- Attaches that carry a known open red: B5 (R-045-09, Westley balance finding), B9 (R-078-06), B10b (R-085-02, R-085-04), B14 (R-130-02). Do not mark these attached without recording the red.
