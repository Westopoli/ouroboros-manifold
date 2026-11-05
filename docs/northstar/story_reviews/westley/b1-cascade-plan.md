# B1 cascade plan: the approved screens, in the project, on both machines

Architect, 2026-11-05. Westley's prompt: a `/manager-mode` cascade (Sonnet only) that builds B1 of `beta-staircase.md`, following `docs/method/story_loop.md`; requirements first, then the spec, then the cascade, then he runs the beta from `project.godot` in his checkout, on the Linux box and on his Mac, and approves or denies. Every statement below was checked against main at `ef19d691` on 2026-11-05, by reading or running, unless marked otherwise.

## 1. What B1 is, in player terms

He opens the project in his Godot editor, presses F5, and walks the chain he already approved: privacy screen, main menu, NEW CAMPAIGN into the galaxy, a mission, DEPLOY FORCES. In the beta, DEPLOY FORCES leads to an empty flat field under the camera rig with one line of text, `beta B1: field placeholder, dev`, instead of the old tactical view. Mission preparation shows a small `variant` picker with one entry; later stages fill it. Nothing on the three approved screens changes. The same walk works on his Mac after one setup command.

## 2. Pre-flight: what is true on main today

| Fact | Evidence |
|---|---|
| H-067 (the project runs from the editor) is landed. | `git log main` has `7f6769b7 Land H-067 beta-in-the-editor`; `scripts/setup_editor.sh`, the abi check in `autoload/c_bridge.gd` (`EXPECTED_ABI := 9`), the README paragraph and `beta_stage0/editor-setup.md` are on main. |
| H-069 (router ignores a repeated target) is landed. | `36a13557 Land H-069 loading-screen-requests-once`; the H-069 branch in `autoload/scene_router.gd` `go_to()`. |
| H-060 (B1) is NOT landed; nothing of it is on main. | No `scenes/beta/`, no `autoload/beta_mode.gd`, no `beta_field` router key, no `[editor]` section in `project.godot`, no `tests/qa/test_beta_b1_chain.py`. |
| A finished B1 build exists on an old branch, 93 implementation lines plus 497 test lines, gated green on the 2026-11-02 main, never played or landed. | `origin/s/H-060-beta-b1-approved-screens` at `1948fb5e`; `git diff --stat main...` lists 11 files. Reference material for the cascade, not a landing candidate: its base is three landings old and the gate-era proofs it waited for no longer exist. |
| The gate, clerk, proof-picture and mail era ended 2026-11-05. | `docs/method/README.md`, `westley.md` ("No screenshots are produced for you any more"), DEC-mail-detached-2026-11-05, DEC-cap-1500-2026-11-05. H-060's "Pictures and done when" section and the staircase's "every landing refreshes om-beta and its proof is a real screen capture" sentence are therefore stale and are rewritten by this cascade (section 5). |
| `project.godot` on main now carries the `4.6` feature tag. | `4717d408 project.godot: feature tag 4.6`; `editor-setup.md` still says main keeps `4.7` (stale, rewritten in section 5). |
| The project's editor-setup script is Linux-only. | `scripts/setup_editor.sh` calls `scripts/build_pipe_linux.sh` (`-static -msse2 -mfpmath=sse -fexcess-precision=standard`, which clang on macOS rejects, as `build_pipe_macos.sh` says), copies `dist/linux/ouroboros_pipe`, looks for `godot.real`, and fills the Steam libraries from a Linux-box cache path. `scripts/fetch_godotsteam.sh` uses `sha256sum`, which macOS lacks (`shasum -a 256`). `scripts/build_pipe_macos.sh` and `codesign_macos.sh` exist, "not run on this Linux box", and were never run by anyone on a Mac in the record. The GodotSteam zip the fetch script pins ships the macOS universal dylibs (`addons/godotsteam/godotsteam.gdextension` lists `macos.debug`/`macos.release`). |
| The client's pipe lookup already works for a Mac editor run. | `autoload/c_bridge.gd` `_pipe_path()`: `OM_PIPE` env, else beside the executable for an export, else `res://pipe/ouroboros_pipe` in the editor. So on a Mac the setup script only has to put a native pipe at `pipe/ouroboros_pipe`. |
| The cascade skill cannot run inside Westley's checkout as it stands. | `worktree_ops.py preflight` refuses tracked changes in the MAIN checkout root (`Ctx.root` is "MAIN checkout root (never a worktree)"); his checkout has `.claude/settings.local.json` modified and that file is his. The cascade therefore runs in a clone (section 6). |
| The cascade config forbids leaves from touching `autoload/**` and `scenes/**`. | `.claude-swarm.toml` `parent_owned`, pinned word for word by `tests/specfactory/test_swarm_config.py` to the toml block in `docs/northstar/plans/2026-10-21-tool-split-spec.md` section 3. Written for sim-side cascades; B1 is client-side. Both the block and the toml are rewritten in the cascade's first commit (section 5), the test reads the block dynamically and keeps passing. `apex_test_cmd` points at `pre_gate.sh`, which needs three arguments and belongs to the retired gate: replaced in the same commit. |
| The Godot on this box is 4.6.3. | `godot.real --version` prints `4.6.3.stable.official.7d41c59c4`. |

## 3. Requirements map

Bible stories touched, all Seen and unchanged by B1: S-110 main menu, S-106 and S-107 galaxy, S-109 mission preparation (`docs/bible/stories.md`, E-16). B1 adds no rule to any of them; its tests prove that the chain still reaches each screen, nothing more. No open `Q-` row names B1, H-060 or the beta (register read 2026-11-05; Q-NET-01 is closed: ship on 4.6.3).

Harness stories in the cascade (the rules below replace the prose "Tests" list in `docs/stories/H-060.md`; the spec quotes them by id):

**H-060 beta-b1-approved-screens** (Ready since 2026-11-02; rulings 1 to 8 of 2026-11-02 stand)

- R-060-01 Given the game started with `OM_BETA=1`, When the player accepts the privacy screen, presses NEW CAMPAIGN, picks a mission and presses DEPLOY FORCES, Then the QA port's `scene` reports, in order, `res://scenes/privacy_modal/privacy_modal.tscn`, `res://scenes/main_menu/main_menu.tscn`, `res://scenes/galaxy/galaxy_view.tscn`, `res://scenes/mission_briefing/mission_briefing.tscn`, `res://scenes/beta/stage_field.tscn`.
- R-060-02 Given the game started without `OM_BETA`, the `--om-beta` argument or a `beta_build.txt` beside the executable, When the same walk ends at DEPLOY FORCES, Then the scene after it is `res://scenes/tactical_c/tactical_view.tscn` and mission preparation's `qa_state()` has no `variant_picker` key.
- R-060-03 Given beta mode, When mission preparation is up, Then an `OptionButton` named `VariantPicker` with exactly one item sits beside a `Label` whose text is `variant`, and `qa_state()` carries `variant_picker: {count: 1, selected: <int>}`.
- R-060-04 Given the field scene and `OM_BETA_BUILD_FILE` naming a file whose first line is a 40-hex sha, When the scene is ready, Then the HUD label reads `beta B1: field placeholder, <first 8 hex>`; given the variable names a missing file, or is unset and no `beta_build.txt` sits beside the executable, the label reads `beta B1: field placeholder, dev`.
- R-060-05 `BetaMode.active()` (static, `autoload/beta_mode.gd`, no project autoload line) is true when `OM_BETA` is `1`, or `--om-beta` is in `OS.get_cmdline_user_args()` or `OS.get_cmdline_args()`, or `beta_build.txt` exists beside the executable; false otherwise. One place asks the question; no other file reads `OM_BETA`.
- R-060-06 Given `scripts/beta_refresh.sh` build phase with a stubbed export and pipe build, When it succeeds, Then `<root>/beta/<sha>/beta_build.txt` holds exactly the full sha on one line; when the stubbed export fails, no `beta_build.txt` is written.
- R-060-07 `project.godot` carries `[editor]` `run/main_run_args="-- --om-beta"`, so an editor F5 runs the beta, and a `godot --path` run or an export does not. Ruling 8 marked the key spelling UNVERIFIED; settled 2026-11-05 (section 7): `editor/run/main_run_args` is a Godot 4 project setting stored exactly so, and arguments after `--` arrive in `OS.get_cmdline_user_args()`, which `BetaMode.active()` reads. Westley's F5 is the live check; the fallback `OM_BETA=1` remains.
- R-060-08 The field scene `res://scenes/beta/stage_field.tscn` is a flat plane under the existing `scenes/ground3d/camera_rig_3d.gd` rig with one HUD label and nothing else; the headless import of main is clean and the console shows no `SCRIPT ERROR`, `ERROR:` or `Parser Error` while the chain runs.

**H-087 the beta runs on the Mac** (new; Westley 2026-11-05: "the godot scene should be runnable from my mac as well, not just linux box")

- R-087-01 Given `uname -s` is `Darwin`, When `scripts/setup_editor.sh` runs with no pipe or a pipe older than `csrc/`, Then it builds through `scripts/build_pipe_macos.sh` with `ARCH` taken from `uname -m` (`arm64` or `x86_64`) and copies `dist/macos/ouroboros_pipe` to `pipe/ouroboros_pipe` by the same temporary-name-then-move; on Linux nothing changes.
- R-087-02 Given `godot.real` is not on PATH and `/Applications/Godot.app/Contents/MacOS/Godot` exists, When the script runs its import step, Then it uses that binary (the same discovery order `scripts/run_godot_tests.sh` uses); given neither exists it prints `EDITOR SETUP FAILED import` and names the two places it looked.
- R-087-03 Given `sha256sum` is absent and `shasum` present, When `scripts/fetch_godotsteam.sh` verifies the zip, Then it uses `shasum -a 256` and the pinned sha still gates the unpack; the Linux route is unchanged.
- R-087-04 `scripts/setup_editor.sh --check` on Darwin prints the Darwin build line, the Godot binary it would use, and `clang` present or missing; it changes nothing.
- R-087-05 The README "Open in the editor" paragraph says what a Mac needs (Godot 4.6.3 from godotengine.org in `/Applications`, the Xcode command line tools for `clang`) and that the one command is the same.

Tests for both stories run on the Linux box with stubs on PATH (`uname`, `clang`, `shasum`, a fake `Godot.app` path under a scratch `HOME`), in the shape `tests/method/test_setup_editor.py` already uses. No test runs on the Mac; the Mac is proved by Westley's F5 (section 6, step 7). That is the one place this plan relies on his machine: the facts it needs (Godot 4.6.3 installed in `/Applications`, `clang` present) are printed by `--check` before anything is built.

Ambiguities: none left at the design level. The two things the record did not settle were ruling 8's key spelling (settled above) and what "runnable from my Mac" means at the edges: an editor F5 in his checkout, not a signed export. Both go in `decisions.md` with the spec commit; he vetoes by a word.

## 4. Size

About 100 implementation lines for H-060 (the old branch's 93 are the measure), about 60 for H-087, under the 1,500 cap by a wide margin. Two or three leaves by the skill's rubric: the beta mode helper plus the field scene plus the two wiring edits (`mission_briefing.gd`, `scene_router.gd`, `project.godot`) are one coherent responsibility; the Mac setup script and the fetch script are another; the `beta_refresh.sh` line rides with whichever leaf owns `scripts/`. The overlord decides the cut; the spec names every file so the briefs cannot drift.

## 5. Documents the cascade rewrites, so the tree agrees with itself

Every line below is in the spec's file list and lands in the cascade, not after it.

- `docs/stories/H-060.md`: the Tests section becomes the rules R-060-01 to R-060-08; "Pictures and done when" becomes "Done when: Westley presses F5 in his checkout on the Linux box and on the Mac, walks the chain to the field and says these are the approved screens"; the 2026-11-02 "Flag ... tool Workflow" and gate words go.
- `docs/stories/H-087.md`: new, the rules above, Scene line `res://scenes/privacy_modal/privacy_modal.tscn`.
- `docs/method/harness.md`: the H-060 row's status, a new H-087 row.
- `docs/northstar/story_reviews/westley/beta-staircase.md`: the B1 row's "Done when" (F5 on both machines, no pictures); "Where the beta lives" gains the Mac sentence and loses "every landing on the beta channel refreshes the standing build and its proof is a real screen capture"; the "Beta Dispatcher brief" section goes (the role is retired); "Where things stand" is rewritten for B1 at landing time.
- `docs/northstar/ROADMAP.md` section 1: the beta rows (B0 closed with H-067 landed, B1 state, no gate channels).
- `README.md` "Open in the editor": the Mac sentence (R-087-05).
- `docs/northstar/story_reviews/westley/beta_stage0/editor-setup.md`: the sentence claiming main keeps the `4.7` tag is wrong since `4717d408`; rewritten to say main carries `4.6` and the editor will not rewrite it.
- `.claude-swarm.toml` and `docs/northstar/plans/2026-10-21-tool-split-spec.md` section 3 block: `parent_owned` loses `autoload/**` and `scenes/**` (tests, bible, northstar, the frozen header and `signatures.toml`, `Makefile`, `scripts/specfactory/**`, the golden data stay); `apex_test_cmd` becomes the story's verify line (`make && godot.real --headless --import --path . && python3 -m pytest tests/qa/test_beta_b1_chain.py tests/method/test_setup_editor.py tests/method/test_beta_build_sha.py -q -p no:cacheprovider`); `type_contract_path`, `umbrella_test_cmd` and `briefs_dir` set for this cascade. `tests/specfactory/test_swarm_config.py` is not edited.
- `docs/northstar/story_reviews/westley/decisions.md`: the rows in section 7, trailer `Decision:`.
- `docs/northstar/story_reviews/westley/README.md`: "What is here" gains this file; "Waiting on you" gains the B1 verdict row at landing.

## 6. The steps, in `story_loop.md` order

1. **Requirement.** This file. Westley reads it and says go or not. On go, the rules above are written into `docs/stories/H-060.md` and the new `docs/stories/H-087.md` as part of step 2's commit.
2. **Spec.** The Architect (this chat) writes `docs/northstar/plans/cascades/b1-approved-screens/spec.md` in the skill's shape (Summary, acceptance criteria quoting R-060-01 to R-060-08 and R-087-01 to R-087-05, inputs and outputs, every file named, the contract in full, Scale and Boundary profile "unbounded-unknown", Bible Compliance naming E-16 and the two story files), briefs one Sonnet engineer by file path to write the contract stub `autoload/beta_mode.gd` (sentinel body) and the red umbrella `tests/qa/test_beta_b1_chain.py` on the cascade branch, and records the section 7 decisions. Commits on the branch `s/H-060-beta-b1` cut from main in the clone `~/Projects/om-wt/b1` (`git clone ~/Projects/ouroboros-manifold ~/Projects/om-wt/b1`, a clone rather than a worktree because the skill's preflight reads the main checkout root and his checkout is never touched). The old branch `s/H-060-beta-b1-approved-screens` stays as reference and is deleted on his word after the landing.
3. **Tests first.** Inside the cascade: the shard-test-writer (Sonnet 5.5) writes the per-leaf failing tests from the spec and contract; the umbrella is already red from step 2. The 2026-11-02 test file on the old branch is named in the spec as reference material whose premises must be re-dumped on today's main, never copied blind.
4. **Build.** Westley opens a Sonnet 5.5 chat in `~/Projects/om-wt/b1` and types `/manager-mode` with the spec path. Every role Sonnet 5.5 (the skill's default; the plan says so again in the spec header so the overlord cannot drift). Leaves build in the skill's worktrees; the overlord admits by G1 to G10; the final fast-forward lands on `s/H-060-beta-b1` in the clone.
5. **Verify.** The Sonnet chat runs `make`, `godot.real --headless --import`, the three test files, and reads the console for `SCRIPT ERROR`, `ERROR:`, `Parser Error`; any red outside the story is a line in its report, not a block.
6. **Land.** The Sonnet chat plays the merged tree end to end on this box's display with `scripts/play.sh --tree ~/Projects/om-wt/b1 --story H-060 --check` (menu, galaxy, mission preparation, the field) and fixes forward by `/investigate` if anything breaks; then pushes the branch, merges it `--no-ff` into `~/Projects/ouroboros-manifold` main with subject `Land H-060 H-087 beta-b1-approved-screens`, trailers `Story:` and `Tests:`, and pushes main. `om-beta` is not refreshed by this landing (section 7).
7. **Westley's verification, both machines.** Linux: `git pull --ff-only`, `scripts/setup_editor.sh`, open `project.godot`, F5, walk to the field, read `beta B1: field placeholder, dev`, see the `variant` picker on mission preparation. Mac: clone or pull the same main, `scripts/setup_editor.sh --check` first (it names the Godot it found and whether `clang` is present), then `scripts/setup_editor.sh`, open `project.godot` in Godot 4.6.3, F5, the same walk. He writes approve or reject in `ruled.md` (the Architect records his words the turn he gives them). A reject on either machine is the next plan's first item; B2 (H-061) becomes Ready the day B1 is Seen on both.

What the cascade cannot do for him: run anything on the Mac. If `--check` says `clang` is missing, the Xcode command line tools (`xcode-select --install`) are his one install; if it finds no Godot, Godot 4.6.3 from godotengine.org into `/Applications` is the other.

## 7. Decisions recorded with the spec commit (his to veto)

- DEC-b1-cascade-in-a-clone-2026-11-05: a client cascade runs in a clone under `~/Projects/om-wt/`, because the skill's preflight reads the main checkout and his checkout carries his own uncommitted files.
- DEC-client-cascade-parent-owned-2026-11-05: `parent_owned` no longer lists `autoload/**` and `scenes/**`; the beta staircase is client-side and its leaves must write there; tests, bible, northstar, the frozen header, `signatures.toml`, `Makefile` and `scripts/specfactory/**` stay parent-owned. `apex_test_cmd` is the story's verify line, not the retired `pre_gate.sh`.
- DEC-b1-seen-by-f5-2026-11-05: B1 is Seen when Westley walks the chain by F5 in his own checkout on the Linux box and on the Mac; no pictures, no look reviewer, no proof capture (the 2026-11-05 method). `om-beta` is no longer refreshed per landing; it stays the pinned 2026-11-02 snapshot until he asks for a new one.
- DEC-mac-is-editor-f5-2026-11-05: "runnable from my Mac" means the editor F5 of the project after `scripts/setup_editor.sh`, on Godot 4.6.3, with a natively built pipe; a signed macOS export is Steam work (ROADMAP section 2), not B1.
- DEC-ruling-8-settled-2026-11-05: H-060 ruling 8's key is `[editor] run/main_run_args` in `project.godot`; the UNVERIFIED mark is lifted on the Godot 4 project-settings record, and Westley's F5 is the live check.

## 8. What waits on Westley now

1. A go on this plan, or the lines he wants changed.
2. Nothing else before the spec. The Mac facts (which Godot, whether `clang` is installed) are read by `--check` at step 7, not needed now.
