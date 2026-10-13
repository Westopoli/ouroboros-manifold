# Pre-flight scout 7-story-plays (2026-10-07, Sonnet, read-only)

Scout 7 report (read-only; worktree `pf-vg7` removed). Everything below is from origin/main at fetch time, except where I say "unverified".

## 1. Stories per lane

Statuses are from `docs/bible/stories.md`. The catalog has 239 rows. No story carries a `Seen` status yet. The vocabulary in `docs/northstar/agile.md:39` ends at Spec'd, Ready, Tested, Queued, Building, Built, Revised, Killed.

| Lane | Stories (status today) | Reference |
|---|---|---|
| A | S-104 (Spec'd, needs reference), S-105, S-009 (blocked Q-009-02), S-010, S-005, S-007, S-075, S-096, S-101 (needs reference), S-134, S-136, S-234 (Sand Table decided by prototype, Q-103-05), S-132 (blocked Q-132-02), S-133 (needs reference) | Only S-104 has an image, `E-16/E-16.png`. S-101 is covered by `E-13/E-13.png` via S-095 and S-088. S-132, S-133 and S-134 have named sources in `E-18/notes.md` but no image. |
| B | S-106 (needs reference), S-107, S-108 (needs reference) | `E-09/time_jump_galaxy_and_scroll.png` is mapped to S-106 and S-107. S-108 is "design phase", with no image. |
| C | S-236, S-001, S-004, S-207 (all "Design decided 2026-10-02, not scheduled" or Spec'd), S-132 (walkers) | None. E-17 images map to S-114, S-115, S-116, S-119 and S-159, not to C's stories. |
| D | S-166 group: S-186 to S-197 plus S-196. S-007 is shared with A. | `E-17-5/6/7` macro-city images (S-119 and S-116) are the nearest. |
| E | S-209, S-210, S-211, S-212, S-230, S-231, S-233, S-235, S-237, S-238, and E-22 S-167 to S-182. All are "Design decided, not scheduled". S-182 is Open. | None. `references/E-15` and `E-22` have no images. `E-15/notes.md` says TBD. |
| F | S-141, S-142 (Spec'd), plus E-19 S-139, S-140, S-143, S-144 (blocked Q-144-03), S-159, S-241, S-242 | `E-19/notes.md` is a stub with an empty table. |

**Orphans, with a proposed owner:**
- **A, fog:** the lane deliverables list fog, but the acceptance list has no E-12 story. S-089, S-090, S-091, S-092, S-093, S-094 and S-205 are all Spec'd or Design decided. `E-12/Unexplored.png` and `ExploredButWithoutVision.png` exist. Add them to A.
- **A, units and combat:** S-081, S-085, S-086 and S-087 are visible in play. S-088 (needs reference) is covered by `E-13/E-13.png`. S-095, S-097, S-098, S-099 and S-100 (movement and facing) are visible too. All go to A.
- **A, other E-16 and E-18:**
  - S-103 camera (blocked Q-103-04) and S-161 map view (blocked Q-103-05).
  - S-135 abilities (needs reference) and S-138 whole look (`E-18-1/2.png`, `E-17-1` to `-4`, spans every lane).
  - S-232 and S-239 (ping, both blocked) go to A or E. S-240 is a perf story, no lane.
- **C or E, buildings and walls:** S-201, S-202, S-203, S-204 and S-206.
- **B, galaxy screens:** S-072 (missions from galaxy trouble), S-073.
- **No lane at all:**
  - Briefing and debrief: S-077, S-078, S-079 (needs reference), S-109, S-074.
  - Chronicle: S-065 to S-071 (only S-069 is shared with lane B's image).
  - Menus and shell: S-110 (`E-16/main_menu.png` exists), S-111, S-137.
  - Campaign screens: E-08 S-055 to S-063. E-08 and E-10 notes say "no shots, simple first pass".
  - Bug report: S-245 (not scheduled).
- **Not visual:** the rest of E-02 to E-07 (Ready or Tested) and S-102, S-084, S-080 (no-op). These need no play.

## 2. The mission-plays harness

- **"Play" is not a defined artifact.** The 2026-09-30 plan (`plans/2026-09-30-mission-plays-plan.md`) is Waves A to C of sim wiring. Its eight specs are `plans/briefs/2026-09-30-sonnet-relay/00` to `07`: CLAUDE.md, register answers, clock tests and code, QA gate, harness bug, visual checks. None defines a play script.
- **The closest thing** is `tests/qa/desktop/*.py`, 9 pytest modules (flow spine 478 lines, tactical play 261). They use `daemon_client.py`: `GodotGame` launches the real game under a private `xvfb-run`, with `--fixed-fps 30`, `--resolution` (default 1280x720), `--qa-port` and `--seed N`. It uses a scratch cwd and a temp `OM_SAVE_DIR`. `DaemonClient.call(verb, *args)` speaks newline-delimited JSON on a TCP port.
- **The second harness** is mockup-only. `qa_driver.gd` is driven by `--qa-script` (JSON) and `--qa-grab engine|external`. It is never loaded in daemon mode with `--qa-script`, because `_ready` quits on a missing root contract (`qa_daemon.gd:10-20`).
- **Daemon verbs** (`qa_daemon.gd:164-190`):
  - `state`, `tree`, `seed`, `fixture`, `pause`, `step n`, `inject`, `plant id`.
  - `screenshot name`, `qa_select [ids]`.
  - `input` sub-verbs: `move`, `click x y [btn]`, `click_node` (script-only, because it needs `_root`), `drag x0 y0 x1 y1 [steps]`, `wheel n`, `key NAME`, `key_down`, `key_up`, `wait_frames`.
  - "Wait for a state condition" is a client-side `wait_for(client, predicate, timeout)` polling `state()` (`daemon_client.py:222`). On timeout it prints the last scene and the control names.
- **Assertions** are plain pytest on `state()["result"]["qa"]`, `tree()` controls and pixels. The tactical-screenshot check reads the PNG with numpy and counts pixels that differ from the median background (`test_flow_spine.py:331-340`, min 300 pixels).
- **Era arg:** none on main. The only CLI args are `--seed`, `--qa-port` and `--qa-script`. Terrain stage 3 (spec rev 3, on `push/terrain3-land-2`) puts the era toggle in the main menu and settings, so a play must click it until a `--era` arg exists.
- **Screenshots** are written under the game's own user dir, `<user_dir>/qa/<name>.png` (the instance's `user_dir`, which is `$XDG_DATA_HOME/data` when the launching env sets it; the fixed `~/.local/share/data/qa` path was retired by TD-HARNESS-qadir / HARNESS-userdir). The caller chooses the name, for example `flow_04_tactical`. There is no run id and no per-run folder. A parallel run or a re-run overwrites the file. Agora instead copies each shot into `runs/qa-*/shot-N.png` with xdotool import. Resolution is whatever `--resolution` says. Agora's QA is still 1280x720 on main (`qa.toml:102`).
- **Driving to an ending:** yes, two ways.
  - By real time: missions are 30 to 60 minutes of battle at 20 ticks/s, so up to an hour per play.
  - By `["step", n]`: `qa_daemon.gd:_do_step` calls `scene.qa_step(n)` (`tactical_view.gd:436`), which calls `tactical_step_n(n)` and reloads the frame. When the frame says `mission_over`, the view routes to debrief (`tactical_view.gd:151-177`). A play can step in chunks to 12000+ ticks and then reach debrief, chronicle and galaxy. The flow spine currently just clicks `EndMission` (`test_flow_spine.py:343`). Nobody has driven a mission to its natural ending through the daemon.
- **Hazard, unverified:** `qa_daemon.gd` never sets `process_mode` to ALWAYS, and `_do_pause` sets `tree.paused`. A paused daemon would likely stop polling and hang. Agora's commit "json wait_ticks no longer pauses the daemon" (2026-10-04) points the same way. Use `step` without `pause`, or set the daemon's process mode to always.

## 3. What the driver cannot do today, and the smallest addition

| Need | Today | Smallest addition |
|---|---|---|
| 3D picking (lane C) | `qa_state` exposes `units_px` (2D) and `systems_px` (galaxy) so a play clicks projected pixels. No 3D equivalent. | The 3D scene's `qa_state` emits `units_px` and `objects_px` from `Camera3D.unalatform`... that is, `unproject_position`. Plays then click those pixels, as galaxy and tactical already do. No driver change. |
| Drag box-select | `drag` exists (lerped moves). | Nothing. `qa_box_select` exists for the 2D view. Lane C needs the same data in state, using the same projection helper. |
| Hover | `move` warps the mouse. No tooltip or hover readback. | Add a `hover` field to `tree` (the Control under the pointer), or state `hovered_id` per scene. |
| Control-group keys | `key` takes only a name. `_do_key` sets no modifiers. | Add an optional modifier list to `key`/`_do_key` (`ctrl`, `shift`, `alt`: three bool properties on `InputEventKey`). About 10 lines in `qa_driver.gd`. |
| HUD text | `tree` already returns every visible Control's `text` and `rect_px`, Labels included (`qa_daemon.gd:_collect_tree`). | Nothing for Labels. Text drawn with `_draw()` or `draw_string` is not covered, so lane A's HUD must use Control nodes. |
| A shot in flight, timing | `step n` is deterministic, but real time (30 fps, llvmpipe) is not. | The play steps to an exact tick, then screenshots. `screenshot` awaits `frame_post_draw` first. Fix the pause hazard above so a held frame stays queryable. |
| Per-run shot names | A single shared dir (see 2). | Add an optional out-dir or run-id arg to daemon `screenshot`, or have the client prefix the name. |

## 4. `qa_state()` today (24 definitions in `scenes/`)

- **Scenes with `qa_state`:** galaxy_view, tactical_view, debrief, mission_briefing, main_menu, chronicle_scroll_panel, onboarding, loading_screen, privacy_modal, new_game, load_game, settings, era_library, era_detail, error_screen, tutorial_overlay, bug_report_popup, time_jump_sequencer.
- **galaxy_view** (`galaxy_view.gd:158`): `system_count`, `owners`, `edge_counts`, `systems_px`, `region_colours`, `owner_colours`, `band`, `distance`, `pick_radius_px`. These are data and pixel positions.
- **tactical_view** (`:244`): `tick`, `canvas`, `scale`, `unit_count`, `units` (faction, type, tier, hp, layer, facing, state, x, y), `units_px`, `selected`, `camera`, `last_command`, `error_panel`.
- **mission_briefing** (`:851`): `archetype`, `deadline_ticks`, `objectives` (kind, node, primary), `deploy_enabled`.
- **debrief, main_menu, chronicle:** `band`, deltas; `continue_enabled`, `slot_count`; `entries`, `owners`, `expanded_id`.
- **Not reported:** the tactical view has no fog state, cover, objective-marker positions, HUD label text, `CanvasLayer` presence, shot or effect counts, or structures. Every "no" in the programme's Context ("no objective marker, no cover, no fog") is invisible to `qa_state`.
- **What the element inventory must add:** named presence and visibility flags (`has_fog_layer`, `has_objective_marker`, `has_minimap`, `has_hud_clock`) and counts (`markers`, `cover_cells`, `structures`, `shots_in_flight`). Add HUD text as read from the Control nodes.
- **Cheapest place:** a shared helper in `autoload/qa_daemon.gd` that walks the current scene and builds a `nodes_by_name` inventory (name, class, visible, count) from `current_scene`. It reuses `_collect_tree`. It would return under `state()["inventory"]` with no change per scene. Scene-specific counts (fog cells, markers) still need one `qa_state` line each in the lane's own scene. The rule: nodes by name from the helper, data counts from the scene.

## 5. The reviewer

- **Agora's QA player:** `~/Projects/agora/scripts/qa_explore.py` (the loop), `qa_desktop.py` (Xvfb and screenshots), `qa_tactical.py` (EndMission gate), `qa_oracle.py` (pure `classify`/`fingerprint` of events into Findings), `qa_backlog.py` (appends rows to `docs/northstar/qa_backlog.md` on a `qa-backlog` branch in `om-push/m3`).
- **Model:** `WORKER_MODEL = qwen3-coder:30b` (`ollama_client.py:18`). Installed models are `gpt-oss:20b`, `qwen3:8b` and `qwen3-coder:30b`. None is a vision model, and `ollama_client.chat` has no `images` parameter. Nothing in `qa_explore.py` sends an image. The model sees only `state`, the tree and the trail text. Screenshots are saved but never looked at.
- **Campaign format:** front-matter markdown, for example `campaigns/todo/007-ouroboros-qa.md` (`tool: qa-fix-loop`, `qa_actions`, `profile`, `mode: record`, `budget_usd`). `projects/ouroboros/qa.toml` is the profile.
- **Last runs:** about 65 `runs/qa-20261005*` and `-20261006*` directories. The newest, `qa-20261006-0111`, ran 128 turns at about 7.6 s per turn. Its screenshots are about 4.4 KB each, which is near-uniform frames. Findings are in `campaigns/007-ouroboros-qa/findings-ledger.jsonl`, last seen 2026-10-05 23:37.
- **Not landed on Agora main:**
  - `relay/05-qa-gate` (EndMission 10-minute gate, 1920x1080 display) is not on main (`qa.toml` is still 1280x720).
  - `relay/07-visual-checks` (blank and frozen frame detectors, `scripts/qa_visual.py`) is not on main either (the file does not exist).
  - The 30B has never played a full mission. The programme's guard 1 `look` stage should reuse spec 07's blank-frame check (`BLANK_RANGE_MAX = 8`).
- **Story review inputs and outputs:**
  - Inputs: the story words from `stories.md`, `qa_state` plus the tree text, the screenshot path, and the reference image paths from `references/E-##/`.
  - Output: a verdict of yes, no or unclear, plus one to three evidence lines.
  - The 30B can only judge from text, so it can answer "do the named nodes and counts exist". It cannot judge "does it read as a unit shape". Use it as the deterministic pre-filter, then send the image to a model that can see.
- **Sonnet/Haiku fallback shape:** one Agent per story batch with `Read` on the screenshot and reference PNGs (`Read` shows images). The prompt holds the story words, the Aspect and "Not wanted" cells from `references/E-##/notes.md`, and the `qa_state` JSON. Return a verdict line plus a short evidence note, not a prose report. Haiku for yes/no presence checks, Sonnet for "reads at a glance" register judgements.

## 6. The review queue

- **File:** `docs/northstar/story_reviews/<lane>.md`, one markdown table per lane.
- **Columns:** `story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date`.
- **Screenshots:** committed copies under `docs/northstar/story_reviews/shots/<run id>/<story>.png`. The run id is a timestamp plus the commit hash, so a re-run never overwrites. `qa_state` dumps sit beside the PNGs.
- **`Seen` status:**
  - Add `Seen` to the vocabulary in `agile.md:39`: "Built, and the player has been shown it and Westley approved".
  - Only a clerk edits the Status cell in `stories.md`, and only when the queue row says approved. The clerk changes the cell and commits it with the queue row, in one commit.
  - Reviewer agents never edit `stories.md`, and neither does the 30B.
  - A rejected row sets the story back to Built or Revised.
- **Catch:** many Status cells hold compound text such as "Spec'd, blocked on Q-009-02". `Seen` can only apply once the flag is closed, which is consistent with "an epic with an open flag is not built".

## 7. Cost

- **Wall time per play:** the 32-test desktop suite ran in 151 s (ROADMAP:268). That is about 7 module launches, so about 20 s per launch for boot, New Game, galaxy, briefing and Deploy. A story play that reaches tactical and screenshots takes about 25 to 40 s.
- **Fast-forward to a mission ending:** `step` in chunks. Pipe cost is 140 to 450 ms per tactical step at 5,000 units (spec 05). A 12,000-tick mission is about 1 to 2 minutes if steps batch. In real time it is 30 to 60 minutes.
- **Counts:** about 14 stories for A, 3 for B, 5 for C, about 12 for D, 26 for E and 9 for F. With the orphans that is roughly 60 to 80 visible plays. Many share a moment: several lane-A stories can be captured in one play. Estimate 25 to 40 distinct scenarios.
- **Total desktop time:** 30 scenarios × 40 s is about 20 minutes serial. With the 30B text pre-filter on the lab box, add about 8 s per turn.
- **Reviewer call:** one 1080p screenshot costs about 1.5 to 3k image tokens (my estimate, not measured). With story words, state JSON and 1 to 2 reference images (1 to 3 MB PNGs, downscaled) a call is about 5 to 10k input tokens and about 200 out. For about 70 stories that is 0.35 to 0.7M input tokens per full pass. Haiku makes this negligible. Sonnet is about 5 times Haiku. The 30B costs zero tokens but cannot see.

## Pieces the guard needs, and owners

1. **Driver additions** (`scenes/mockups/_shared/qa_driver.gd`, `autoload/qa_daemon.gd`): key modifiers, a hover readback, a per-run screenshot directory or name, `process_mode` ALWAYS for the daemon (verify the pause hang first). Owner: Engineer writes the tests first, a Doer builds. These are two files with owners in `pieces.toml` (C7, C8).
2. **`qa_state` inventory helper:** `autoload/qa_daemon.gd` adds `inventory` to `state()`. Each lane's scene then adds its own counts as part of its pieces (A's tactical view, B's galaxy, C's 3D view).
3. **Projected-pixel contract for 3D scenes** (`units_px` and `objects_px` via `unproject_position`): a contract piece in lane C, since it changes `qa_state`.
4. **The queue:** `docs/northstar/story_reviews/`, its format, `agile.md` vocabulary, `stories.md` header. Owner: the Architect writes the format. A clerk applies verdicts.
5. **Story play scripts:** `tests/qa/desktop/plays/<story>.py`, fenced, written by the test writer per lane, one scenario per moment.
6. **The reviewer task:** (a) the Agora text pre-filter on `qa_state` and `tree`, using the deterministic checks (Agora owns it; needs `relay/05` and `relay/07` landed first); (b) the Sonnet/Haiku image-review Agent, a brief template in the repo.
7. **The gate `look` stage:** `scripts/specfactory/merge_gate.sh` after step 9b (playthrough), with the blank-frame and near-uniform checks (spec 07's `qa_visual.py` logic) and screenshot attachment. Owner: Engineer, tests first.
8. **Baseline captures:** `docs/northstar/baselines/2026-10-07_visible/`, a one-off play of every current screen, a clerk job.

Caveat on estimates: the "about 20 s per launch" and "25 to 40 s per play" figures come from 151 s over about 7 modules and a 32-test count, not from a single timed run. I did not execute any game or play.
