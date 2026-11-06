# HANDOFF BRIEF — P9 menu, setup, briefing and debrief mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

The screens the README decision (`docs/northstar/README.md:30`) calls "TBD design, not references": main menu, generational setup, mission briefing and debrief. They start simple and are iterated on player feedback, so they get a mockup, not a reference pull. Round 1 stories (`docs/legacy/mvp/feature_mvps.md`): E-16 S-110 minimal (title, new campaign, continue, quit; R-110-01's menu list, settings scope per Q-110-01 listed but not built), S-111 as a stub (autosave at chapter boundaries; R-111-04's campaign list without a fixed slot count); E-08 S-063 minimal (pick a difficulty; mission preferences wait; Q-063-02 answered: once at the beginning of the history); E-10 S-079 minimal (orders in three parts as plain text, no voice, no art; R-079-01 to R-079-04), S-077 (the five-band spectrum, R-077-01, R-077-02), and the prototype `S-P01` auto-resolved mission card (`docs/legacy/mvp/feature_mvps.md`, E-10 block: "the briefing states the situation; the outcome resolver's band math takes force parity and one seeded roll and returns a band on S-077's spectrum; the card shows the band and casualties. No player choice"). Read `docs/bible/epics/E-16-client-camera-hud-and-world-view.md` lines 132 to 156, `E-08-generational-structure.md` lines 142 to 154, `E-10-missions.md` lines 114 to 127 and 143 to 155.

The 60-second paragraphs you touch: E-10 (the briefing has three sections and names the attacker; forces at parity 0.90; the final score 0.75 · 1.0 + 0.25 · 0.67 = 0.917 is `total_success`), E-08 (pick a difficulty at the start; the commander rotation is not this mockup). References: `docs/bible/references/E-16/main_menu.png` (title in a serif face over a slowly turning particle galaxy with one bright core, a left-aligned monospace list, studio line above the title, version bottom-right; "Round 1 keeps this shape") with its row in `references/E-16/notes.md`; `E-08/notes.md` and `E-10/notes.md` say the setup, briefing and debrief references are missing. Judge the menu against the capture and the other three against the rules and the tone of the hub (`docs/bible/game_bible.md`, "Tone": playful, dry, never cringe; orders read like a superior officer, not a menu).

This mockup is the flow alone, on fixtures: title, setup (one difficulty choice), briefing (three sections of plain text with Accept and Refuse only), the auto-resolved card, debrief, and back to the title; plus a stub campaign list for Continue. No sim, no galaxy animation beyond a cheap static field (the galaxy mockup owns the real one).

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/menus`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/menus/**` and `docs/northstar/research/mockups/menus/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/menus/menus_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh menus [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run menus <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `scenes/main_menu/main_menu.gd:22-60,176-215,295-325` (menu build, `_create_menu_item`, entrance animation; hover glyph bloom at 217 is optional), `scenes/main_menu/menu_title_heartbeat.gd:52-102` (per-character title labels with a breathing pulse, PULSE_FREQ 0.15, 0.92 to 1.0; skip the glyph scramble), `scenes/onboarding/onboarding.gd:99-160,313` (difficulty column and select), `scenes/mission_briefing/mission_briefing.gd:66-140,164-260,597-610` (header, situation text, objective cards, footer), `scenes/debrief/debrief.gd:102-160,373` (outcome section, `_band_color`), `autoload/mock_data_source.gd:146-190` (a hand-written briefing dict). The briefing shape the real pipe emits: `simulation/pipe_transport.py:105-146` (`mission_title, mission_subtitle, situation_text, objective_primary {text, archetype, success_spectrum_label}, enemy_assessment {faction_name, archetype_label, behavior_tag}, player_force {parity_percentage, units[]}, region_state {name, tier}, commander_lineage {name, generation_number, predecessor_name, predecessor_status}, reinforcement_note`); the debrief shape at `:772-795` and `simulation/debrief_data.py`. Band thresholds per archetype from R-077-02 (defensive_stand [0.20, 0.40, 0.60, 0.80]). Theme: `autoload/theme_constants.gd` colours and type sizes to copy into `theme.gd`; fonts `theme/fonts/Newsreader-*.ttf` (title, briefing prose) and `JetBrainsMono-*.ttf` (menu list, labels); the dead `theme/terminal_glass_theme.tres` may be copied into your directory as a `.tres` if it helps, not referenced in place.

## What to build

```
scenes/mockups/menus/
  menus_mockup.tscn         root Control "MenusMockup" with menus_mockup.gd; children Screens (Control), Backdrop, QADriver
  menus_mockup.gd           the contract; owns the flow, the fixtures, the seeded roll, screen swap
  flow.gd                   RefCounted: the state machine (title, setup, briefing, resolve, debrief, campaigns); allowed edges; campaign record
  resolve.gd                RefCounted: S-P01 band math from parity, difficulty and one seeded roll; casualties; R-077 thresholds as data
  theme.gd                  colours, type sizes, fonts (copied constants)
  screens/title.gd, setup.gd, briefing.gd, resolve_card.gd, debrief.gd, campaigns.gd   one Control each, built in code
  backdrop.gd               a cheap static star field and one bright core (quads), slow rotation; no shaders
  fixtures/briefing_seed11.json, briefing_seed12.json   in the pipe_transport briefing shape, with the attacker named in the situation and the enemy assessment
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `flow.gd`

States and edges: `title` to `setup` (New Campaign), `title` to `campaigns` (Continue), `title` quits (Quit; in the mockup, a label "would quit"); `campaigns` to `title` (Back) or to `briefing` (Resume a listed campaign); `setup` to `briefing` (Begin, with a difficulty chosen) or `title` (Back); `briefing` to `resolve` (Accept) or `title` (Refuse, which in the mockup returns to the title with a line "orders refused; the chapter passes"; list the real consequence as under-defined); `resolve` to `debrief` (Continue); `debrief` to `title` (Proceed). Any other transition is rejected with a reason. `flow.gd` holds the campaign record `{name, difficulty, chapter, last_band}`; Begin writes it and Continue lists it (R-111-04: no fixed slot count; the mockup keeps records in memory and lists as many as were started).

### 2. `resolve.gd`

`resolve(parity: float, difficulty: String, seed: int, thresholds: Array) -> {score, band, casualties, retention}`: objective score o = clamp(parity × difficulty factor (easy 1.15, medium 1.0, hard 0.85) + roll, 0, 1) with roll uniform in [−0.15, 0.15] from a `RandomNumberGenerator` seeded from `seed`; retention r = clamp(0.55 + 0.5 × o + roll/2, 0, 1); final = 0.75 · o + 0.25 · r (R-077-01); band by thresholds (R-077-02); casualties = round((1 − r) × the force size). Monotone in parity for a fixed roll. The exact formula is a stand-in and is listed as under-defined; the band mapping and the 0.75/0.25 weights are the bible's.

### 3. Screens

Title: studio line above, the title in Newsreader with the breathing pulse, a left-aligned monospace list New Campaign, Continue, Settings (greyed, "later"), Quit; version bottom-right; the backdrop behind at 70 percent opacity (R-110-01). Setup: "Before your first chapter" with three difficulty cards (easy, medium, hard) each with one line of consequence prose, a Begin button enabled once one is chosen, a note that mission preferences come later (Q-063-02: shown once at the start). Briefing: header with the mission title and region; three sections in order, Situation, Objective, Assets, each a paragraph of plain prose from the fixture with the attacker named in Situation and parity stated in prose in Assets (R-079-01); no numbers rendered as digits (R-079-04: render parity as words such as "near parity" or "outnumbered by a third"); the only controls are Accept and Refuse (R-079-02). Resolve card (S-P01): "The battle is fought" with a two-second fade, then the band name in the band's colour, one line of outcome prose, casualties as "n of m did not return", no choices, a Continue button. Debrief: band, the primary objective with completion in words, retention in words, commander fate (survived unless the roll is in the lowest band), Proceed (R-079-03). Campaigns: a list of started campaigns with name, chapter, last band; Resume and Back.

### 4. The contract

`PLANTS = ["band-random", "briefing-two-sections", "difficulty-dropped", "flow-skips-setup", "four-bands", "digits-in-prose"]`. `qa_state()`: `seed`, `hash`, `screen`, `difficulty`, `campaigns` (list of records), `briefing {title, sections (names in order), attacker_named, has_digits}`, `resolve {score, band, casualties, retention}` (null before resolve), `controls` (the visible buttons' labels on the current screen), `timing_ms {swap}`, `regen_count`. `qa_seed(n)` (selects the fixture and the roll seed); `qa_go(action)` performs a menu action by name (`new_campaign`, `continue`, `quit`, `pick_easy`, `pick_medium`, `pick_hard`, `begin`, `accept`, `refuse`, `resolve_continue`, `proceed`, `back`, `resume:<name>`); `qa_set("parity", f)` overrides the fixture's parity for the resolve.

Fault sites: `band-random` uses the global RNG for the roll; `briefing-two-sections` drops Assets; `difficulty-dropped` ignores the chosen difficulty in resolve and the campaign record; `flow-skips-setup` routes New Campaign straight to the briefing; `four-bands` collapses `partial_failure` into `total_failure`; `digits-in-prose` renders the parity percentage as digits.

### 5. Build order (commit after each)

verify.gd red and stubs; flow.gd; resolve.gd; theme and backdrop; title and setup; briefing; resolve card and debrief; campaigns; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh menus`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/menus): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/menus/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh menus --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/menus/menus_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/menus/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | `resolve(0.9, "medium", 11, T)` twice equal; seed 12 differs in roll; same seed same band | H | `band-random` |
| EDGES-2 | every allowed edge transitions and every disallowed one is rejected with a reason; `title` to `briefing` directly is rejected | H | `flow-skips-setup` |
| SETUP-3 | the difficulty picked at setup appears in the campaign record and changes `resolve` (easy versus hard at the same parity and seed give different scores) | H | `difficulty-dropped` |
| SECT-4 | the briefing fixture renders exactly three sections in the order Situation, Objective, Assets; Situation names the attacker's faction name; Assets states parity in words | H (instantiate) | `briefing-two-sections` |
| DIGITS-5 | no briefing or debrief text contains a digit (R-079-04) | H (instantiate) | `digits-in-prose` |
| BANDS-6 | with defensive_stand thresholds, finals 0.1, 0.3, 0.5, 0.7, 0.9 map to the five bands in order; monotone in parity for a fixed roll | H | `four-bands` |
| WEIGHTS-7 | the E-10 60-second example: o = 1.0, r = 0.67 gives final 0.9175 and `total_success` | H | none |
| CONTROLS-8 | on the briefing screen `controls` is exactly Accept and Refuse; on the title exactly New Campaign, Continue, Settings, Quit (R-079-02, R-110-01) | H (instantiate) | none |
| CAMP-9 | two campaigns started in a row both appear in `campaigns` with their chapter and last band; Resume goes to the briefing | H | none |
| JSON-10 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |

Xvfb oracles: SCREENS-X (each screen's screenshot differs from the previous, `diff` ≥ 0.05; under `flow-skips-setup` the setup screenshot equals the briefing's); BAND-X (the resolve card crop contains the band colour named in the state; under `four-bands` a `partial_failure` roll shows the `total_failure` colour); SECT-X (the briefing screenshot has three heading crops; under `briefing-two-sections` the third is background); ERR-0, GPU-0, DET-1 pixel; a 1920x1080 title shot for the reference comparison.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `screenshot title`; `state title`; `call qa_go new_campaign`; `wait_frames 20`; `screenshot setup`; `call qa_go pick_hard`; `call qa_go begin`; `wait_frames 20`; `screenshot briefing`; `state briefing`; `call qa_go accept`; `wait_frames 90`; `screenshot resolve`; `state resolve`; `call qa_go resolve_continue`; `wait_frames 20`; `screenshot debrief`; `state debrief`; `call qa_go proceed`; `wait_frames 20`; `call qa_go continue`; `wait_frames 20`; `screenshot campaigns`; `state campaigns`; `call qa_go back`; `seed 12`; `call qa_go new_campaign`; `call qa_go pick_easy`; `call qa_go begin`; `call qa_go accept`; `wait_frames 90`; `state resolve_seed12`; `key R`; `state after_r`. Review batch at 1920x1080: title, setup, briefing, resolve, debrief, campaigns (6 shots) into `docs/northstar/research/mockups/menus/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-16/main_menu.png` and the tone section of `docs/bible/game_bible.md`.

| q | question | proves |
|---|---|---|
| Q1 | Does the title keep the reference's shape: serif title over a turning field with one bright core, monospace list left, studio line above, version bottom-right? | R-110-01, reference row |
| Q2 | Does the briefing read as orders from a superior officer (three parts, no haggling) and not as a menu or a stat sheet? | R-079-01, R-079-02, R-079-04 |
| Q3 | Does setup ask one thing (difficulty) and say the rest comes later? | S-063 minimal |
| Q4 | Can the band card be read in five seconds: band, outcome line, casualties? | S-P01, R-079-03 |
| Q5 | Does the prose have the hub's dry wit somewhere without being cringe? | tone |
| Q6 | Any clipped or overlapping text at 720p; any digits leaking into prose? | hygiene, R-079-04 |

## What the report must answer

1. Tone: does the whole flow feel like one game, and where did the prose fall flat?
2. Are plain-text orders enough, or does the briefing need one visual element (map thumbnail, portrait) to read?
3. Whether Refuse needs a consequence to feel real.
4. Frame time under llvmpipe at 720p (2D; should be high).
5. Under-defined points with candidates: the resolve formula, casualty display, Refuse's consequence, Continue's behaviour, the Settings scope for the first tester build (Q-110-01 says resolution, fullscreen, two volumes, rebinding, edge scroll).

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/menus/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh menus` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh menus --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run menus scenes/mockups/menus/qa/smoke.json <scratch>/menus/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/menus/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/menus/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/menus/**` and `docs/northstar/research/mockups/menus/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/menus/menus_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
