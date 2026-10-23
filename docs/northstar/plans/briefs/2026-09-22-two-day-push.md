# The two-day push: parallel build of the backend and placeholder client, pieces attached one at a time

## Context

Westley has two days of effectively unlimited Claude usage (2026-09-22 and 23). His brief (DECISIONS.md, Twelfth round, verbatim): masses of Claude sub-agents in manager-mode cascades; get the MVP done and whatever is ready beyond it; all backend code and simple placeholders, no polish; "I'm the blocker, not the code being written." His structure: agents work in parallel on individual pieces; pieces are fitted into the "main" prototype when they finish; start with the ultimately simple game (main menu) and tack functionality on one piece at a time, checking with QA that nothing broke; pieces stay separate until attached; the straggler rule: when five of fifteen agents finish, those five start the next piece while the ten finish.

Two other chats run in parallel: one builds nine placeholder-data client mockups on one shared QA contract (`qa_state()`, `qa_plant(id)`, `qa_seed(n)`, `qa_set`, `qa_camera`, `verify.gd`, `scripts/mockup_verify.sh <name>`; briefs `docs/northstar/plans/briefs/2026-09-22-*.md`; none reads the C sim), one does deep research. This plan treats the mockups as client pieces that arrive during the window and adopts their QA contract for the main prototype.

Inputs: `docs/northstar/plans/archive/work_inventory_2026-09-22.md`; a three-angle design panel with two judges (integration-first, parallelism-first, risk-first); an adversarial pass of three refuters plus per-finding verification (64 confirmed findings, all folded in below; journals under this session's `subagents/workflows/`, copied to `docs/northstar/proving_ground/evidence/push_2026-09-22/panel/` at F0); the overnight factory (merge queue in a bare clone, whole-suite regression tooling, escalator seat, graph scheduler).

Westley's answers (2026-09-22): three manager chats, each on the updated manager-mode skill with Sonnet overlords and Sonnet shard testers (his instruction after approval); workflows launched one at a time on his go-ahead (session limit); `symbol_modules.toml` accepted with the additions; the design lane authors the twelve window controls; D1 conftest-only now, signature form after the window.

Standing rule suspended for the window and recorded (Twelfth round): Claude never writes a card's implementation. Rules that stay: tests are the spec and are fenced (leaves never edit `tests/**`); determinism contract; no runtime API calls; no stink; sub-agents implement, never design; stale-doc tripwire; nobody stages Westley's dirty files; every manager and leaf works in its own clean clone or worktree.

## Facts that shaped the method (verified against the repo by the panel and the refuters)

- `tests/csim` collects 686 (567 tests + 119 controls, 92 placeholders); `tests/qa/t1` 20 more. Running `pytest tests/csim tests/qa/t1` in one invocation fails collection for 205 files (the two `conftest.py` names collide); the two directories run as separate invocations everywhere below. E-02 baseline 56 passed / 4 skipped. Main is red by design (~560 red), so `agora/scripts/merge_queue.py:115-117` (whole suite must exit 0) cannot gate as is; the gate compares failing-id sets between the rebased base and the candidate in the same run.
- Tests call 631 distinct `lib.om_*` symbols (234 keyword-argument call sites); the header declares 84; only `_bind_e03`, `_bind_e04`, `_bind_e05` exist in `conftest.py`, so E-06..E-17 have no ctypes bindings and raw ctypes would drop their kwargs silently. 27 `ctypes.Structure` definitions (23 names) live inside E-06..E-17 tests and fix layouts the header must match byte for byte. The freeze generates declarations, bindings with `paramflags`, struct mirrors and skeletons from one table.
- `skeleton_gen.py` is on both skeleton branches (`b63d345`); it is taken with `git show b63d345:scripts/specfactory/skeleton_gen.py > ...` (git-guard blocks `checkout <sha> -- path`).
- Tactical orchestrators: E-11's tests drive `om_tactical_step` (37 calls) and `om_tactical_tick` (7); E-13 drives `om_world_step` (27 calls); `om_tactical_tick_to`, `om_tactical_run`, `om_tactical_run_until_eliminated`, `om_tactical_run_until_engagement_ends` also exist. E-13 also calls `om_visibility_compute` (fog) and `om_world_get_state_checksum` (sim.c, absent).
- Name drift: `om_unit_hp` (5 files) vs `om_unit_get_hp` (4). `om_faction_create_breakaway` is called only by E-06 S-042 (not S-049). Save/load is already contracted by E-08's tests as `om_save_state_size`, `om_save_state_write`, `om_load_state_read`.
- `manager-mode`'s tracked `.claude-swarm.toml` (commit 081f36b) points at an old cascade with `max_impl_lines = 200`; `worktree_ops.py base --commit-artifacts` commits every dirty path (the tracked `.swarm/` tree, 116 files) onto the branch every leaf forks from; its `preflight`, `base`, `commit` and `admit` refuse a dirty clone; its `add` bases on the wave's fixed `base_sha`. Godot rewrites tracked `logs/sim_stderr.log` and `logs/crash_report.txt` on every launch (`simulation/pipe_transport.py:49,64` via `autoload/sim_bridge.gd:58`). `.claude/hooks/git-guard.sh` is tracked and denies any Bash command containing `git rebase`, `reset --hard`, `clean`, `-D` in every clone.
- `merge_queue.py:94` fetches the candidate branch from `project` only and keys its lock on `project`'s slug (`:35-36,69`); its default whole-suite timeout is 600 s. The agora harness lives only on branch `wn/qa-director` (126 commits ahead of `main`).
- The `agora-dispatcher.service` unit is enabled with `Restart=always`; `agora-tmux.service` is enabled too.
- RAM: 31.7 GB total; the `win11edu` VM (qemu, 15.3 GB RSS) is running today (Tuesday); 7.6 GB available, swap nearly full. Concurrency below is capped by this unless the VM is stopped.
- `clang` is not installed; the compiler-variance gate is gcc `-O0` versus `-O2`. The Makefile bakes `-O2` into `CFLAGS_DET`, has no `-Werror` and one output name per target.
- `Q-065-02` and `Q-120-01` are closed; only `Q-039-01` is open among the rules the window touches.
- The mockup chat is committing and pushing `main` today and its `mockup/*` branches are local to Westley's checkout.

## Decisions taken by the design lane for the window (recorded in DECISIONS.md, Thirteenth round, at execution start)

1. **One signature table.** `docs/northstar/spec_factory/signatures.toml`: `[symbols]` rows (symbol, module, params with names and C types, return type, source tests) and `[structs]` rows (name, ordered fields with C types) for every symbol and structure E-06..E-17 tests use, plus T1, T2, Q2 symbols. E-03, E-04, E-05 rows are **derived by parsing the current header and conftest**, never transcribed, and the generator asserts the 84 existing declarations and the three existing bindings are byte-identical after generation. `scripts/specfactory/sig_table.py` emits header blocks, `_bind_e06.._bind_e17` with `paramflags`, struct mirrors, and the twelve skeletons. Eleven Sonnet transcribers (E-06..E-17) write rows and an ambiguity report; the design lane resolves ambiguities. ABI version 2.
2. **Ownership rows added to `symbol_modules.toml`** (Westley accepted the table; these are the corrections and additions): `om_unit_hp` = declared alias wrapper of `om_unit_get_hp` in `unit.c`; `om_faction_create_breakaway` = `diplomacy.c` (its only caller is E-06 S-042; the earlier `lifecycle.c` attribution was wrong and is corrected); `om_mission_start`, `om_mission_unit_tier` = `mission.c`; `om_save_state_size`, `om_save_state_write`, `om_load_state_read` = new module `save.c` (E-16); `om_world_get_state_checksum`, `om_abi_layout_check` = `sim.c` (core, landed by M0 at F2); `pipe/om_pipe.c` = T1; `om_map_add_cover`, `om_map_add_obstacle` = `tactical_mapgen.c` fixture primitives while the generator stays held; `collision.c` = E-05.
3. **Tactical orchestrators.** `OM_FEAT_TACTICAL`: with a tactical map loaded, `om_world_step` calls `om_tactical_step` after the strategic steps, so E-13's tests stand; the orchestrator set for closure is {`om_tactical_step`, `om_tactical_tick`, `om_tactical_tick_to`, `om_tactical_run`, `om_tactical_run_until_eliminated`, `om_tactical_run_until_engagement_ends`}, written into `tick_closure.py`'s `ORCHESTRATORS` and a new `specfactory.toml` `[chain_graph] orchestrators` that `tick_closure.py` reads. `om_tactical_trace_*` (unit rows per tick) is declared in the freeze for Q2.
4. **D1 for the window, conftest-only.** `om_world_new` keeps its signature; the C default becomes empty (the DRIFT-on line in `region.c` goes); `conftest.py`'s `world_factory` applies each epic's set from `docs/northstar/spec_factory/mvp_features.toml`; one new test proves the default is gone. Zero test edits.
5. **Constants.** `csrc/om_constants.h` from `algorithms.md` ALG-01..75 by `alg_constants.py --emit`; `--lint` forbids bare numeric literals in module `.c` files (0, 1, -1, array sizes exempt); `libm_lint.py` lints `csrc/**/*.c` recursively and its banned list gains `rand`, `time`, `clock`, `qsort`.
6. **`OM_BUG_*` ranges** per module reserved at freeze (E-03 300s exist; E-06 400s, E-07 500s, E-08 600s, E-09 700s, E-10 800s, E-11 900s, E-12 1000s, E-13 1100s, E-14 1200s, E-15 1300s, E-17 1400s, T1 1500s, save 1600s).
7. **Controls.** The design lane authors one live control per module in `tests/csim/controls/`; the leaf plants its C branch; LIVE is required only for the attaching piece; `control_liveness.py` ERROR on a module not yet attached is recorded as pending, never counted; the 92 placeholders stay in the failing baseline. Each gate run passes a unique `--scratch-root`.
8. **Merge and attach mechanics (all corrections from the refuters).**
   - Clones come from the GitHub URL, never from the live checkout; F0's control asserts `git remote get-url origin` is GitHub in every clone. Agora clone: `git clone -b wn/qa-director`.
   - Managers `git push origin push/<piece>`; M0 (`~/Projects/om-push/m0`) fetches `origin push/<piece>` and calls `merge_candidate(project=<m0 clone>, ...)`, so the lock is one lock and the candidate source is origin. `merge_cli.py` runs detached with its own timeout above the gate length, begins with `git worktree prune` and deletes stale `_merge_*` refs, and treats a timeout as a harness error retried once.
   - `merge_cli.py` cherry-picks the leaf's commit sha(s) from `.swarm/<slug>/wave-N.base.json` onto fresh `origin/main`, never rebases the whole branch, so manager-mode's artifact commits never reach main. The footprint fence ignores `.swarm/**`, `.claude/**`, `logs/**`, and `.gd.uid` sidecars count as part of their `.gd`.
   - The gate (`scripts/specfactory/merge_gate.sh`, set as `whole_suite`): `make OPT=-O2 WERROR=1` under its own timeout (a make timeout or `COMPILE ERROR` exits with a distinct harness code, retried once, never counted as regression); `libm_lint.py`; `alg_constants.py --lint`; footprint fence (`git diff --name-only <base>..HEAD` minus ignores equals the piece's `owns`); symbol-ownership lint against `signatures.toml`; `suite_regression.py` in its before/after mode on `tests/csim` and, separately, `tests/qa/t1` (failing ids and first assertion lines on the rebased base versus the candidate; no new red id, no changed assertion line, no rise in skipped/xfailed); the piece's acceptance ids green; `pytest tests/qa/t1` (desync detector, trace detectors); after `attach/T1`, also `pytest tests/transport` and `make pipe/ouroboros_pipe`; `checksum_trace.py --lib build/O0/libouroboros.so --seed 1 --ticks 500` equals the `build/O2` run (separate output dirs); `undertest_check.py` shadow-fixture and diff mutation as WARN rows (block only on lines a named rule owns). `merge_cli.py revert <piece>`: build, lints and footprint only, reverts dependants in reverse attach order in the same candidate, records the post-revert failing set. M0's own commits (docs, tests, controls, ledger) also go through `merge_cli.py` under a docs-and-tests profile (collection plus lints), never a direct push.
   - Three rejection replays (an `om_pow` revert, a planted red id, a `tests/` edit) plus one acceptance replay (a manager-mode-produced candidate must pass) run before the swarm; gate wall time is recorded and the timeout set from it.
9. **One integrator.** M0 is the only writer of `origin/main`, including the mockup chat's branches. At hour 0 the mockup chat is told: push every `mockup/*` to origin, stop merging into `main`, report branches. Until then M0 adds the live checkout as a fetch-only remote to see them.
10. **Manager-mode use.** One manager-mode slug per piece; per-clone `.claude-swarm.toml` (umbrella = the piece's acceptance ids, `max_impl_lines = 2500`, `parent_owned` += `csrc/sim.c`, `csrc/region.c`, `csrc/*.h`, `project.godot`, `tests/**`, `docs/**`, `footprint_ignore` = `.swarm/**`, `.claude/**`, `logs/**`); the test-writer phase is skipped because the fenced tests pre-exist (recorded); managers never run `admit`, `sync`, `finish` or `cleanup --purge`; `push/<piece>` is the leaf branch; a clone's `main` moves only by `git pull --ff-only origin main`. Straggler increments are committed by the manager with `git add <owns> && git commit` in the leaf worktree and pushed as `push/<id>-N`; parked and diagnosis notes live under `.swarm/<slug>/`, not the worktree root.
11. **Acceptance at spawn is mechanical** (closure inside {own module} ∪ {attached modules}; leftovers become `<piece>b` follow-ups: B5b for S-048, B7b for tests needing `chronicle.c` or `unit.c`, B10b, B12b for S-096's fog call). B12 depends on B11 as well as B10.
12. **Visual claims** are filed `held` with screenshot paths for Westley's eyes; never a gate.

## Wave 0: the freeze (design lane, budget 8 to 10 hours with the struct track; nothing attaches before it, but six leaves start under it)

| Step | Owner | Output | Positive control |
|---|---|---|---|
| F0 baseline, hygiene, clones | M0 | `git rm --cached logs/*` + `.gitignore logs/`; `.gitignore` also `.swarm/` artifacts under the new slugs; `systemctl --user disable --now agora-dispatcher.service` (re-enabled at window close, ledger row); `win11edu` VM stopped for the window (Westley); clones from GitHub `~/Projects/om-push/{m0,m1,m2,m3}` and `~/Projects/agora-push` (`-b wn/qa-director`), each with `.venv -> ~/Projects/agora/.venv` symlinked; `worktree_ops.py preflight` green in each; `baseline_pre.json` (two id sets, first assertion lines, skipped/xfailed) from two pytest invocations; catalog rows refreshed (S-040/S-041 Tested, E-02 Built, E-03 Tested); panel journals copied under `evidence/push_2026-09-22/panel/`; push ledger opened; mockup chat messaged | preflight refuses the live checkout and accepts the clones; `git remote get-url origin` is GitHub in all four; dispatcher `inactive` and `disabled` |
| F1 signature table | eleven Sonnet transcribers (E-06..E-17) under M0 via Workflow; M0 dedupes | `signatures.toml` `[symbols]` and `[structs]` rows; ambiguity report per epic | a row contradicted by its call sites is reported, not guessed |
| F1s struct track (parallel to F1) | one Sonnet helper under M0 | the 27 test-side `ctypes.Structure` layouts as `[structs]` rows with C types and order | a field order swap fails `test_conftest_bindings.py` |
| F1b generate and land | M0 with one Sonnet helper | `sig_table.py` output: header blocks, bindings with `paramflags`, struct mirrors, twelve skeletons (`skeleton_gen.py` via `git show`); `tests/specfactory/test_conftest_bindings.py` (every kwarg at every call site exists in its binding; E-03/E-04/E-05 declarations and bindings byte-identical to before); `card_lint.py --fuel` over `evidence/card_regen/<E>` per epic reports ABI_GAP 0 | freeze control: `red_check.py --forbid TypeError,ArgumentError,AttributeError` (new flag) over E-06..E-17 shows every test red on an assertion or STUB, zero forbidden classes outside the 92 placeholders; E-02 still 56/4 |
| F2 wiring and D1 | M0 | `sim.c` hooks at 4.25, 4.5, 6, the `OM_FEAT_TACTICAL` call, `om_world_get_state_checksum`, `om_abi_layout_check`; `region.c`'s `om_world_generate` marked `__attribute__((weak))` (B4's strong definition overrides; M0 deletes the weak after `attach/B4`); `OM_BUG_*` order-swap branches; `test_E06_wiring.py`, `test_E07_wiring.py`, `test_E11_wiring.py`; D1 conftest-only; `mvp_features.toml`; `specfactory.toml` orchestrators; Makefile `OPT ?= -O2`, `WERROR` toggle, `build/O0` and `build/O2` output dirs, `pipe/ouroboros_pipe` target; tag `freeze/F2` | wiring tests red before, green after, red under the swap branches; both builds link |
| F3 constants | one Sonnet leaf under M0 | `om_constants.h`, `alg_constants.py --emit/--lint`, extended recursive `libm_lint.py` | a planted `0.33` in a scratch module fails the lint |
| F4 transport shapes | M0 | `docs/architecture.md` "C transport v1": hello (abi, seed, features), snapshot (tick, checksum, regions with owner and composites, factions, edges), delta, command (`step`, `run_to`, `set_seed`, `set_feature`, `inject`, `save`, `load`), tactical snapshot, chronicle frame, mission frame, debrief frame; three JSON schemas; fixture `tests/transport/fixtures/snapshot_seed1_tick10.json` via ctypes; `tests/transport/test_pipe_shapes.py` red; no names, positions or prose (C5 rule) | a removed key fails the shape test |
| F5 controls | M0 | one live control per module in `tests/csim/controls/` with the fault named in the module's brief | `fixture_defects.py` clean on each |
| F6 gate, cli, seams | M0 with one Sonnet helper | `merge_gate.sh`, `agora/scripts/merge_cli.py` (merge, revert, docs profile), `checksum_trace.py`, `pieces.toml` (id, owns, acceptance ids, depends_on, status); `project.godot` autoload line `QADaemon`, `tests/test_qa_daemon.gd` red, `scripts/qa_harness.sh` skeleton (Xvfb, never `:0`); C7 itself creates `autoload/qa_daemon.gd` and `scenes/harness/**` (no add/add conflict) | the three rejection replays and the manager-mode acceptance replay, exit codes and wall times in the ledger; C1 baseline `scripts/run_godot_tests.sh tests/test_boot_scripts_parse.gd tests/test_privacy_modal.gd` green |

Started at hour 0 on already-declared symbols, before the freeze: **B1 events**, **B2 collisions**, **B3 friction and revolts**, **B4 world generation** (M1); **C7 daemon** (M3); **K1 validator** (M0 via Workflow). They rebase in the merge queue onto the freeze.

## Waves 1 to 3

| Wave | Piece | Manager | Owns | Acceptance | Depends on |
|---|---|---|---|---|---|
| 1 | B1 events | M1 | `csrc/events.c` | E-04 | none |
| 1 | B2 collisions | M1 | `csrc/collision.c` | E-05 S-039 minus R-039-05 | none |
| 1 | B3 friction, revolts | M1 | `csrc/friction.c` | E-05 S-040, S-041 | none |
| 1 | B4 world generation | M1 | `csrc/worldgen.c` | E-03 | F2's weak attribute |
| 1 | B5 diplomacy, technology | M1 | `csrc/diplomacy.c` | E-06 minus S-048 (B5b) | freeze |
| 1 | B6 lifecycle | M1 | `csrc/lifecycle.c` | E-07 | freeze |
| 1 | B7 generational | M1 | `csrc/generational.c` | E-08 by closure (B7b) | freeze |
| 1 | B10 units, combat, tactical orchestrators | M2 | `csrc/unit.c` | E-11 by closure (B10b) | freeze, F2 |
| 1 | B9 missions | M2 | `csrc/mission.c` | E-10 by closure | freeze |
| 1 | B15m map fixture primitives | M2 | `csrc/tactical_mapgen.c` (fixture functions only) | the E-11..E-13 fixture calls | freeze |
| 1 | C7 harness daemon | M3 | `autoload/qa_daemon.gd`, `scenes/harness/**`, `scripts/qa_harness.sh` (after F6) | `tests/test_qa_daemon.gd`, liveness precheck under Xvfb | none |
| 1 | T1 pipe server | M3 | `csrc/pipe/om_pipe.c` | `tests/transport/` | F4, F2 |
| 1 | C2 galaxy view | M3 | `scenes/galaxy/**`, `autoload/c_bridge.gd` | `tests/test_galaxy_view.gd` against the fixture, rebind to T1 when it attaches; galaxy mockup plant ids | F4 |
| 1 | K1 validator | M0 | `scripts/specfactory/pack_validate.py`, `banned_words.txt`, `evidence/px10/` | PX-10 brief's controls | none |
| 2 | B8 chronicle | M1 | `csrc/chronicle.c` | E-09 | B7 |
| 2 | B11 fog | M2 | `csrc/fog.c` | E-12 | B10 |
| 2 | B12 movement, command | M2 | `csrc/tactical_move.c` | E-13 by closure (B12b) | B10, B11, F2 |
| 2 | B13 enemy macro | M2 | `csrc/enemy_macro.c` | E-14 | B10 |
| 2 | B14 reinforcement, hazards | M2 | `csrc/tactical_support.c` | E-15 | B10, B9 |
| 2 | Q2 tactical detectors | M2 impl, M0 tests | `scripts/qa/rts_detectors.py` (imported by `tests/qa/t1`) | rubber-band, stuck, backwards, dropped order on planted builds | B10, F2 |
| 2 | T2c save and load, C | M1 | `csrc/save.c` | `tests/csim/test_E16_S111_saving.py` (M0, day 1 midday) | B7 |
| 2 | T2g save slots, Godot | M3 | `scenes/load_game/**` | `tests/test_load_game.gd` | T2c, T1 |
| 2 | C3 chronicle scroll rebind | M3 | `scenes/world/chronicle_*` | `tests/test_chronicle_scroll.gd`; mockup p7 plants | B8, T1 |
| 2 | C4 briefing and debrief rebind | M3 | `scenes/mission_briefing/**`, `scenes/debrief/**` | `tests/test_briefing_debrief.gd`; mockup p9 plants | B9, T1 |
| 2 | C5 minimal tactical view | M3 | `scenes/tactical_c/**` | `tests/test_tactical_view.gd`; mockup p4/p8 plants | B10, B12, T1 tactical frame |
| 2 | Q1 campaign data | M0 | `agora/projects/ouroboros/**` | data lint | C7 |
| 3 | B5b, B7b, B10b, B12b | M1, M2 | same modules | leftover tests now in closure | the modules they span |
| 3 | K2 Greek placeholder pack | M0 | `assets/eras/<placeholder>/` | K1 green, contract test loads both packs | K1 |
| held | B15 generator, C6 landscape view | | | | Westley's third look, then the E-17 rewrite |
| held | P6 layers, P8 real eras, P9 multiplayer | | | | flags |

## Attach order and gates

Attach = `merge_cli.py push/<piece>` (fetch from origin, cherry-pick onto fresh `origin/main`, `merge_gate.sh`, push), then the post-attach check in `~/Projects/om-push/m0`, then a ledger row and `git tag attach/<piece>` pushed to origin (managers `git fetch --tags` before spawning).

1. **C1 + C7**: `scripts/run_godot_tests.sh tests/test_qa_daemon.gd tests/test_boot_scripts_parse.gd tests/test_privacy_modal.gd`; `scripts/qa_harness.sh liveness` (mandatory desktop precheck); daemon `state` read on the menu. Godot runs use a cwd or `--root` outside the checkout so nothing tracked is rewritten.
2. **B1, B2, B3, then B4** (P0 gate): E-02/E-04/E-05 whole suites green except the Q-039-01 skip; `run_trace.py --regions 60 --ticks 5000` under budget; `checksum_trace.py` O0 equals O2; `OM_BUG_EMPTY_DRIFTS` and `OM_BUG_OSC_AS_LEVEL` trip; E-03 green after B4.
3. **T1, then C2** (P1 gate): `pytest tests/transport`; `pipe/ouroboros_pipe --seed 1 --regions 60` over a 10-step script gives the ctypes checksum; daemon `state` equals the snapshot; region colour equals owner; galaxy plants caught; liveness.
4. **B5, B6**: E-06 (minus S-048), E-07 green; daemon state still equals snapshot with the three features on.
5. **B7, B8, C3** (P7 brought forward): E-08, E-09 green; two runs seed 11 jump 50 give identical entry ids and checksum; every entry references an existing region or faction; "readable pace" held.
6. **B9, C4** (P3): E-10 green; 50-seed sweep, every objective centre resolves; briefing shows the marker name; plant `objective-unnamed` fails.
7. **B10, B11, B12, C5** (P4, P5 sim-side): E-11, E-12, E-13 green; Q2 rows silent on clean, loud on plants over a scripted command stream; visibility set equals `om_visibility_compute`; the visual half held.
8. **B13, B14**: E-14, E-15 green; S-123 replay same commands same checksum.
9. **T2c, T2g**: save at a chapter boundary, load, identical checksum and ledger.
10. **K1, K2**: validator rejects the broken pack, accepts the clean one; contract test loads both packs.

Every attach also runs the gate list in decision 8, `systemctl --user is-active agora-dispatcher.service` = inactive, and `git status --short` in Westley's checkout untouched. Red before push: piece parked (`.swarm/<slug>/PARKED.md` with failing ids and first assertion lines), returned to its manager as a repair task, slot moves on. Red after push (something the gate does not cover): `merge_cli.py revert <piece>` before any other merge; main red for at most one gate cycle. After any revert, a straggler's next submission is a fresh branch off main carrying `git diff main..<leaf> -- <owns>` as one commit. Any header change after the freeze is a `freeze/F2b` commit by M0 (ABI 3) that regenerates `tests/transport/fixtures`, reruns `tests/transport` and every attached client test before push, and broadcasts a sync.

## The straggler rule, concrete

- Done = branch on `origin/main` and tagged `attach/<piece>`, never the leaf's report.
- On every `attach/*` tag (`git fetch --tags`), each manager `git pull --ff-only origin main` in its clone, then `base --wave N+1 --commit-artifacts --yes`, then `add --wave N+1 --leaf <next>` for the first unspawned piece whose `depends_on` are all tagged. Five of fifteen finish, five seats take the next five eligible pieces at once; the ten stragglers keep their seats and are never rebased or interrupted (they meet main only at merge, by cherry-pick).
- A straggler submits increments: `push/<id>-1` after its first story group is green (manager commits `git add <owns> && git commit` in the leaf worktree), and keeps working; partial merges are allowed when the acceptance subset is green and nothing new is red.
- Time boxes: at 2× the size estimate the manager asks for a checkpoint (green ids, red ids, first assertion lines); at 3×, or after three distinct candidates fail an identical id set, the manager waits for the straggler's current increment to merge, then stops it and spawns a split leaf for the remaining stories from that main (never two live leaves on one file); a piece that cannot name a cause is parked with `.swarm/<slug>/NEEDS-DIAGNOSIS.md` for M0 (bug, test-defect, contradiction).
- Dependants start on merged increments as soon as the symbols they consume are on main (stub-aware closure at spawn).

## Managers and ownership (no two managers share a file; every rebase or reset goes through `merge_queue.py` or `worktree_ops.py`; the phrase "git rebase" never appears in a Bash command, commit message or ledger row)

| Manager | Where | Owns | Pieces |
|---|---|---|---|
| M0 design lane + integrator | this session; `~/Projects/om-push/m0`; Workflow tool for its own leaves | `docs/**`, `tests/**`, `csrc/ouroboros_sim.h`, `om_internal.h`, `om_constants.h`, `sim.c`, `region.c`, `Makefile`, `project.godot`, `scripts/specfactory/**`, `scripts/qa/**` tests, `origin/main` | F0..F6, every attach and revert, K1, K2, Q1, T2 tests, Q2 tests, ledger, register rows, mockup merges |
| M1 strategic sim | Sonnet chat, updated manager-mode (overlord and shard testers Sonnet), `~/Projects/om-push/m1` | `csrc/{events,collision,friction,worldgen,diplomacy,lifecycle,generational,chronicle,save}.c` | B1..B8, B5b, B7b, T2c |
| M2 tactical sim | Sonnet chat, updated manager-mode (overlord and shard testers Sonnet), `~/Projects/om-push/m2` | `csrc/{unit,mission,fog,tactical_move,enemy_macro,tactical_support,tactical_mapgen}.c`, `scripts/qa/rts_detectors.py` | B9..B15m, B10b, B12b, Q2 impl |
| M3 transport + client | Sonnet chat, updated manager-mode (overlord and shard testers Sonnet), `~/Projects/om-push/m3` | `csrc/pipe/**`, `autoload/{qa_daemon,c_bridge}.gd`, `scenes/harness/**`, `scripts/qa_harness.sh` (after F6), `scenes/galaxy/**`, `scenes/tactical_c/**`, `scenes/world/chronicle_*`, `scenes/mission_briefing/**`, `scenes/debrief/**`, `scenes/load_game/**` | C7, T1, C2, C3, C4, C5, T2g |

Concurrency: with the VM stopped, 8 C leaves per manager and 4 Godot leaves, Godot QA capped at 2 at 1280x720; with the VM running, 4 C leaves per manager and 2 Godot processes total. Leaves run only their acceptance ids locally. Per-leaf briefs: card path(s), `card_slice` header slice, control fault site, owns list, acceptance ids, the constants and determinism rules verbatim, the caveman report-back line.

## Day-3 corrections (2026-09-24, after the drift audit)

Measured against this plan after two days: M1 never received a brief and died; M2 and M3 ran manager-mode cascades on day 1, then sat at rate-limit prompts overnight; M0 became the only manager and briefed every leaf directly (176 agent spawns in the M0 chat, 34 in M3, 13 in M2). The freeze did not hold (15 header commits after F2: per-module state slots, save hooks, a return type, cross-module accessors), the merge harness needed 13 fixes, 8 test-fix commits landed under the gate, and 5 of 25 gate runs on day 3 were rejected on sequencing or harness errors. The leaves' code is sound (no piece has introduced a new red id); the waste is in the scaffolding. These rules replace the "Managers and ownership" and "Manager-mode use" text above for the rest of the push.

1. **Two Sonnet manager chats, not three, and not M0.** Westley opens `M-sim` (clone `~/Projects/om-push/m1`, every `csrc/*.c` piece) and `M-client` (clone `~/Projects/om-push/m3`, `csrc/pipe/**`, `autoload/**`, `scenes/**`, `scripts/qa_harness.sh`) in their own terminals. Each reads `docs/northstar/plans/push/pieces.toml`, the ledger tail and `docs/northstar/plans/briefs/leaf-mechanics.md` (the shared mechanics block, written once), takes the next `pending` piece whose `depends_on` are tagged or merged as increments, and runs it. M0 (this chat) only rules, merges, tags and writes the ledger; it spawns no leaves except test-fix and core-header doers.
2. **On the rate-limit prompt, managers choose "wait here, then continue automatically".** A manager that stops on that prompt has cost a night twice. Westley sets that once per chat.
3. **Direct leaves, no overlord or shard testers.** One Sonnet leaf per piece, in a worktree, with the standing mechanics file plus a five-line delta (piece id, owns, acceptance, known leftovers, the state slot). The gate is the tester; the leaf runs only its acceptance ids and the lints, never the whole-suite before/after (the gate computes that).
4. **Header gaps are batched.** A leaf that needs a symbol or slot another module does not expose leaves the id red and names the symbol; M0 collects the names from every report of the day into one `F2-<letter>` core commit (docs profile), then the affected leaves resume. No per-gap core doer.
5. **Fixture sanity before the leaf.** Before a piece is assigned, one cheap Sonnet pass reads its acceptance tests against the header and conftest and lists fixture defects (positional `set_region` calls, `>=` on `pytest.approx`, expected values that do not follow the ALG arithmetic, superseded Q- numbers). Those go through the test-fix gate first, so the module leaf never diagnoses tests mid-build.
6. **Gate order is fixed by M0.** Transport-touching pieces before anything else when `tests/transport` is red by design; one increment id shape (`<piece>-N`); a branch is never checked out in the m0 clone when its merge is queued; bookkeeping travels on `bk-N` branches through the docs profile, never a direct push.
7. **Bible drift is a stop.** A test that asserts numbers from a closed Q- row's superseded example (R-120-03) is a stale-doc tripwire failure: the epic is corrected and the test fixed under the gate before the piece proceeds.

Spawning from M0 versus from Westley's terminals: leaves spawned from M0 cost M0's context (every brief and report lands in the Fable transcript, which then compacts and loses in-flight agent handles), die together on a rate limit, and cannot outlive the chat. Leaves spawned from a Sonnet manager chat cost Sonnet context, are restartable from `pieces.toml` plus the ledger, and keep running while M0 is paused or compacting. The coordination loss that hurt day 1 (misrouted messages, an unbriefed M1) is removed by the standing brief file: a manager needs no message from M0 to start, only the tags on origin.

## Westley's part

- Hour 0 (15 minutes): stop `win11edu` for the window (`virsh -c qemu:///session shutdown win11edu`); open three manager chats with the manager-mode skill in the three clones when M0 says the clones exist; confirm the dispatcher stays disabled for 48 h; tell the mockup chat to push `mockup/*` and stop merging `main`.
- Optional day 1: `Q-039-01` (unblocks R-039-05; the only open rule in the window).
- Day 1 evening (30 minutes): fly C1+C7 and the galaxy view over T1 when the ledger says P1 is green; thumbs per `held` claim.
- Day 2: P3 briefing look, P4 tactical look; the landscape third look if he wants E-17 to move (outside the window regardless).
- Never during the window: commit, pull, stash or checkout in the live checkouts; start the dispatcher. `git pull --ff-only` when M0 says a rung is green.

## Honest estimate

- Day 1: freeze on `origin/main` by hour 8 to 10 (the struct track and the signature table are the long pole); wave 1 spawned (about 13 leaves plus the six hour-0 starts); by midnight B1..B4 attached and P0 green (E-03, E-04, E-05 built minus R-039-05); C7 attached with the main-menu baseline; T1 attached against the fixture; C2 in progress; B5, B6 attached or close; B7, B9, B10 running as stragglers; K1 done.
- Day 2: P1 closed on the live pipe by mid-morning; B7 and B10 attach; B8, B11, B13, B14 spawn, B12 after B11; P7 sim-side green with C3 by evening; P3 with C4 by afternoon; Q2 detectors in; C5 spawns late and does not close P4 inside the window (code present, gate not run); T2c done, T2g partial; one or two of B12/B13/B14 into day 3.
- Not in the window: E-17 generator and landscape view, layers, eras beyond the placeholder pack, multiplayer, D1's signature form, anything visual beyond placeholders.

## Risks and the specific mitigation

| Risk | Failure it causes | Mitigation |
|---|---|---|
| A signature or struct row inferred wrong | a module can never satisfy its tests | one table; ambiguous rows reported not guessed; E-03/04/05 rows derived and byte-checked; freeze control with `--forbid`; `om_abi_layout_check` in the pipe hello |
| Kwargs dropped by ctypes | tests pass garbage | bindings carry `paramflags`; `test_conftest_bindings.py` checks every call site |
| Leaf hard-codes fixture answers or tunes constants | green tests, wrong game | `om_constants.h` plus literal lint; shadow-fixture and mutation rows at attach; 50-seed rung sweeps |
| Determinism broken inside a module | contract broken, desync later | recursive libm lint with the extended list; repeat-seed and desync tests; O0 vs O2 checksum; `-Werror`; UBSan in M0's nightly sweep |
| Manager-mode artifacts or logs on a piece branch | fence rejects everything | cherry-pick of leaf shas only; fence ignores `.swarm/**`, `.claude/**`, `logs/**`; logs untracked at F0; Godot runs with cwd outside the checkout |
| A later piece breaks an attached piece's tests | invisible under a frozen baseline | before/after regression on the rebased base in the same gate run; no frozen baseline |
| Revert rejected by its own gate | main red across cycles | `merge_cli.py revert` profile skips acceptance and regression, reverts dependants in the same candidate |
| Two managers on one file | rebase conflicts, parks | ownership table; C7 creates its own files; T2 split into T2c/T2g; K1 under M0 only; split-at-3× only after the increment merges |
| Scope theft | duplicate symbols, later cards unbuildable | symbol-ownership lint; both `.so` links in the merge worktree |
| Integrator throughput | queue backs up | detached `merge_cli` with explicit timeout; leaves run acceptance ids only; P0 trace hourly unless `sim.c`-adjacent; harness-coded make timeouts retried, never parked |
| RAM (VM holds 15 GB) | OOM kills, flaky make timeouts read as regressions | VM stopped or concurrency halved; make timeout is a harness code |
| Two writers on main (mockup chat) | rebase races, foreign reverts | mockup chat pushes branches and stops merging at hour 0; M0 merges them |
| Bash 600 s cap kills a gate mid-run | stale `_merge_*` refs block every later merge | `merge_cli` detached, prunes refs and worktrees on start |
| Westley unavailable at hour 0 | freeze waits | every question has a pre-chosen default and a one-hour clock; the VM stop is the only item without a default |
| Dispatcher restarts | parked cards dispatched onto the same files | unit disabled at F0, checked before every attach |

## Verification of the plan itself

- Before spawn: the freeze control (every E-06..E-17 test red on an assertion, zero forbidden exception classes), `test_conftest_bindings.py` green, the three rejection replays and the manager-mode acceptance replay with wall times, E-02 56/4, preflight green in every clone, origins on GitHub, dispatcher disabled, VM state recorded.
- Per attach: the gate list in decision 8, a ledger row, the pushed tag.
- Per rung: the numbered gates; green on a clean build and red on its planted build.
- End of window: push ledger summary; `stories.md` statuses flipped to Built for merged stories; DECISIONS.md Thirteenth round rows; the standing rule reinstated; dispatcher re-enabled; `chain_graph.py` and the card set regenerated so the factory resumes where the push left off.
