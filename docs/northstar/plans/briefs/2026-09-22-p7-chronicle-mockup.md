# HANDOFF BRIEF — P7 chronicle and time-jump mockup

Self-contained. Handed to an implementor 2026-09-22. Sibling briefs: `2026-09-22-mockup-qa-harness.md` (the harness you use), `2026-09-21-p2-landscape-mockup.md` (the shape to copy).

## Context

Rung P7 of the prototype ladder (`docs/northstar/PLAN.md:168`): "Time jump and chronicle: entries reference real state; deterministic per seed; readable pace." Epic E-09, Round 1 stories S-065 (five to ten entries in the right order, R-065-01 to R-065-05), S-066 (what counts as notable; data only here), S-068 (written from fragments, R-068-02, R-068-07, R-068-08), S-069 minimal (watching history happen: galaxy on one side, scroll on the other, no animation choreography beyond the rules named; R-069-01 to R-069-06), S-071 (the fragment library contract, as the fixture's shape). Also E-08's keyframe map animation (the map animates border changes during the jump). Read `docs/bible/epics/E-09-chronicle.md` lines 28 to 57 and 73 to 104. Q-065-02 (setup entries) is open: the mockup ends the scroll with no setup entry and lists the question.

The 60-second paragraph: after a successful mission in region R where a famine chain ran and two regions changed hands, the scroll shows entry 1 in the consequence-success register naming R and the outcome, one lineage entry, a chain entry for the famine in one paragraph, regional entries for the changed regions; 5 to 10 entries, none sharing 40 percent of their content words, none over 90 words in base form; clicking a printed entry pauses everything and the expanded form adds a closing sentence and names; same seed, same events, same text.

Reference, and the one thing to match: `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` with its rows in `references/E-09/notes.md` (map on the left filling about two thirds, territory shells glowing where factions touch, lanes as thin threads, the map animating while the text streams; on the right one entry at a time in a serif face, wide measure, faction names in the faction's colour, reading as a passage of history). Look at it before building. The legacy screen that produced it is live in the repo and is the feel to copy, not to load.

This mockup is the split screen alone: a small own galaxy of about twenty points with owner colour and border morphs on the left (sixty lines of code, not the galaxy mockup), the scroll on the right, an eight-entry fixture in the real message shapes, word-by-word printing at the bible's cadence, click to pause and expand, Skip and Proceed.

## Rules for the implementor

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build; ask Westley about his Claude usage before a batch of more than two doers. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.
- You are in a git worktree on branch `mockup/chronicle`. Commit there after each working step with the trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Do not push; the design chat merges into `main`. Never stage files you did not create or edit for this brief. Never check out another branch.
- Touch only `scenes/mockups/chronicle/**` and `docs/northstar/research/mockups/chronicle/**`. Nothing else: not `csrc/`, `simulation/`, `tests/`, `docs/bible/`, other `docs/northstar/`, other `scenes/`, `scenes/mockups/_shared/` (if the harness is broken, stop and report; do not patch it), `project.godot`.
- This is a mockup: placeholder primitives only (boxes, cylinders, prisms, planes, quads, flat colours, `Label3D`, `Control._draw`). No imported models, no textures beyond vertex colour and flat shading. GDScript only. No autoload dependency and no dependency on any other scene: the scene must work if every autoload were removed. You may copy code from the legacy files named under "Godot facts" into your directory and you may reference `theme/fonts/*.ttf` by `res://` path; you may not `preload` or `load` anything outside your directory except `res://scenes/mockups/_shared/qa_driver.gd` and `qa_plants.gd`.
- Renderer parity: your QA renders run under the Compatibility renderer on software GL; Westley views Forward+ on an RTX 3060. Use only what looks the same in both: `StandardMaterial3D` (vertex colour as albedo is fine), `ArrayMesh`/`ImmediateMesh`, `MultiMeshInstance3D`, `Label3D`, one `DirectionalLight3D`, `WorldEnvironment` sky, ambient and depth fog, `CanvasLayer`, `CPUParticles3D`. Do not use SDFGI, VoxelGI, volumetric fog, SSR, SSAO, SSIL, glow, decals, `GPUParticles3D`, or screen-texture shaders.
- No era named in any script identifier or node name (bible rule R-145-01). Where the era shows it is data under `kits/` or `fixtures/`.
- Deterministic: every random draw comes from your own `RandomNumberGenerator` seeded from an integer seed; never the global RNG, never the wall clock. Same seed, same state hash, same pixels.
- **Never set `DISPLAY` yourself and never use `:0` or `:1`.** Every windowed run goes through `scripts/mockup_qa.sh`, which creates a private Xvfb. The GPU belongs to the Agora chain.
- No docstrings or comments except the `# plant: <id>` line above each check in `verify.gd`. Minimal, direct code.
- When something in this brief is under-defined, do not decide: build the simplest thing that shows the question and list it in the finishing report with two or three candidate answers.

## Godot facts (reconnaissance 2026-09-22)

- Binary `~/.local/bin/godot`, `4.6.3.stable.official`. Project root is the repo root. `project.godot` declares Forward+, 1920x1080, fullscreen, stretch `canvas_items`/`expand`, no `[input]` map (use raw keycodes as the landscape mockup does). Nineteen autoloads run on any `--path .` scene launch; one spawns the Python sim and warns about a mac path; harmless. `--script` SceneTree mode loads no autoloads.
- Scene convention: a short `.tscn` (root node with your root script, a `QADriver` child with `res://scenes/mockups/_shared/qa_driver.gd`, and whatever nodes you need) plus scripts. Every mockup scene in this repo is launched by path, never as the main scene. Westley's command is `~/.local/bin/godot --scene scenes/mockups/chronicle/chronicle_mockup.tscn` from the repo root; keep that name.
- The harness (read `scenes/mockups/_shared/README.md` first): `scripts/mockup_verify.sh chronicle [--plant id]` runs your `verify.gd` headless; `scripts/mockup_qa.sh run chronicle <script.json> <outdir> [--res 1280x720] [--plant id]` runs the scene under Xvfb with `--fixed-fps 30` and replays a JSON action list (`wait_frames`, `move`, `click`, `click_node`, `drag`, `wheel`, `key`, `key_down`, `key_up`, `call`, `seed`, `plant`, `pause`, `screenshot`, `state`, `tree`, `wait_file`); `scripts/mockup_qa.sh diff a.png b.png` prints the fraction of differing pixels; `scripts/mockup_qa.sh scan <outdir>` writes `errors.txt`, `shots.txt`, `marks.txt`. Your scene root must implement the contract: `const PLANTS: Array[String]`, `qa_state() -> Dictionary` (JSON-safe, canonical from data, never from HUD labels; always `seed`, `hash`, `timing_ms`, `regen_count` plus the keys named below), `qa_plant(id) -> bool`, `qa_seed(n)`, and the optional `qa_set(name, value)` and `qa_camera(...)` this brief names. Plants are activated through `preload("res://scenes/mockups/_shared/qa_plants.gd").is_active("<id>")` at a one-line fault site.
- Under Xvfb a 3D scene renders at a few frames per second; keep QA scripts short (a few hundred frames), use 1280x720 by default, and take the 1920x1080 review shots only in the final batch. Window pixels equal screenshot pixels; canvas coordinates are scaled by the stretch (use `click_node` rather than raw pixels for HUD buttons).
- Input gotchas: a full-rect `Control` with the default `mouse_filter = STOP` swallows synthetic mouse events before `_unhandled_input`; put world mouse handling in `_unhandled_input` on a non-Control node and set every full-rect Control to `MOUSE_FILTER_IGNORE` unless it is the designated click surface. Set `focus_mode = FOCUS_NONE` on Buttons and click empty ground before key verbs so a SpinBox does not eat letters.
- Copy the feel of the landscape mockup's HUD and camera code where it fits: `scenes/mockups/landscape/hud.gd` (kit discovery, timing prints, screenshot key), `camera_rig.gd` (pan, edge scroll, wheel zoom, public `pan_to`/`set_height`).
- Colours available to copy: `autoload/theme_constants.gd` (BASE `#0A0D12`, PRIMARY `#e8e6e1`, ERA_ACCENTS), faction colours `#4099FF` and `#FF4738` from `assets/eras/settled_reach/manifest.json`, the hue-from-id function in `autoload/faction_palette.gd:38`. Fonts: `theme/fonts/` (JetBrainsMono, Newsreader).
- Legacy to copy from (never to load): `scenes/world/time_jump_sequencer.gd:56-110` (layout: map SubViewport full-rect, chronicle panel anchored at `anchor_left = 0.62`), `:264-300` (`_apply_keyframe` drives ownership colour), `:373-410` (narration and timeline advance); `scenes/world/chronicle_scroll_panel.gd:87-170` (`begin_time_jump`, `queue_entry`, `start_printing`, `skip_all`, `slide_in`/`slide_out` 400 ms); `scenes/world/chronicle_entry.gd:154-230` (word-by-word print with per-word alpha, `_assign_word_colors` for faction tinting, `_rebuild_bbcode` wrapping mentions in `[url=region:rid]`); `scenes/world/chronicle_entry_expansion.gd`; `scenes/debug/test_chronicle_scroll.gd:6-60` and `test_time_jump.gd:7-100` (hand fixtures with base and expanded forms and mentions). Message shapes to author the fixture in: `chronicle_entry {type, time_jump_id, entry_id, tick_range_start, tick_range_end, base_form, expanded_form, mentions[]}` and `time_jump_start {time_jump_id, span_years, total_keyframes, total_entries, faction_names{}, ownership_timeline[]}` (`docs/architecture.md:128-182`, `simulation/world_view/keyframe_message.py:24-65`). Fonts: `theme/fonts/Newsreader-*.ttf` for the entries, JetBrainsMono for the HUD.
- Fragment prose: write the eight entries yourself in the register of `simulation/library/chronicle/fragments.json` (read twenty fragments for tone), with invented region, faction and character names (no names from any existing fiction; no era named in code). Categories per R-065: entry 1 consequence-success naming the mission region and the outcome; one lineage entry; one chain entry (a famine chain in one paragraph); regional entries for two regions that changed hands; the rest by descending score with at most two per category. Base form under 90 words; expanded adds one closing sentence with names.

## What to build

```
scenes/mockups/chronicle/
  chronicle_mockup.tscn     root Control "ChronicleMockup" with chronicle_mockup.gd; children MapViewport (SubViewportContainer), Scroll (Control), HUD, QADriver
  chronicle_mockup.gd       the contract; owns fixture load, the jump clock, phase machine, pause
  jump.gd                   RefCounted: loads a fixture, validates entry order and word limits, exposes keyframes and entries by tick; hash()
  mini_galaxy.gd            Node3D inside the SubViewport: ~20 system points, edges, owner colour, border morph over 2 s on a keyframe
  scroll_panel.gd           Control: slides in over 0.40 s, resizes the map to 62 percent, prints entries word by word (0.08 s per word, 0.20 s fade), blinking cursor on printed entries, click to expand
  entry_view.gd             Control: one entry; base and expanded forms; mention spans coloured by faction
  hud.gd                    CanvasLayer: Skip (S), Proceed (Enter, enabled at the end), Reset (R), pace label, entry counter
  fixtures/jump_seed11.json, jump_seed12.json (a second jump with different events and ownership changes)
  verify.gd
  qa/smoke.json, qa/checklist.md
```

### 1. `jump.gd` and the fixtures

A fixture is `{"time_jump_start": {...}, "entries": [chronicle_entry...], "galaxy": {"systems": [...], "edges": [...]}}`. `ownership_timeline` is a list of `{tick, system_id, owner}`; `total_keyframes` about 12 over a 2,400-tick span; each entry's tick range contains at least one keyframe (R-069-05); every ownership change has a keyframe. `jump.gd` loads it, checks R-065-01 (5 to 10 entries), the register order (consequence first, then lineage, then the rest in descending score with at most two per category), R-068-02 word limits, R-068-07 (drop a later entry sharing 40 percent of content words with an earlier one, and report it), and exposes `entries_by_tick(t)`, `keyframes_by_tick(t)`, `hash()`. The mockup's clock is the map animation (R-069-03): a tick counter advancing at 20 ticks per second of real time, seeded only in the sense that the fixture is fixed; `qa_seed(n)` selects fixture `jump_seed<n>.json`.

### 2. `mini_galaxy.gd`

Twenty to thirty system points from the fixture in a flattened disc, edges between listed pairs, owner colour by faction hue (copy the hue function from `autoload/faction_palette.gd:38`), a faint starfield of static quads. On a keyframe: the changed system's colour tweens over 2.0 s and a soft ring pulses at it (the "border visibly morphs over two seconds" from the E-16 60-second text). A slow auto-orbit (R-107-02 says player input overrides it; a right-drag does). Rendered into a `SubViewport` so the panel can resize it to 62 percent width.

### 3. `scroll_panel.gd` and `entry_view.gd`

At jump start the panel slides in from the right over 0.40 s and the map container resizes to 62 percent (R-069-01). When the clock reaches an entry's `tick_range_start`, the entry starts printing: words every 0.08 s, each fading 0 to 1 over 0.20 s (R-069-02); a printed entry shows a blinking cursor and holds at least 3.0 s (R-069-03). Clicking a printing entry does nothing; clicking a printed entry overlays the expanded form and pauses the clock, the map tween, and any printing entry; dismissing (click or Escape) resumes from the exact word and frame (R-069-04). Mention spans (`mentions[]` with kind, id, char range) render in the faction's colour via BBCode `[color]` and `[url]`. Serif font (Newsreader), wide measure, one entry per block, auto-scroll to the printing entry. At the last entry the panel stays; Proceed becomes enabled; Skip prints everything instantly and jumps the map to its final ownership.

### 4. The contract

`PLANTS = ["order-shuffled", "expand-noop", "no-pause", "entries-duplicate", "morph-instant", "cadence-wallclock"]`. `qa_state()`: `seed`, `hash`, `tick`, `phase` (`idle`, `narrating`, `paused`, `done`), `entries` (list of `{entry_id, category, printed_words, total_words, printed, expanded}`), `expanded_id`, `owners` (system id to owner), `map_width_fraction`, `pace {word_interval_s, fade_s}`, `dropped_entries`, `timing_ms {load}`, `regen_count`. `qa_seed(n)`; `qa_set("skip", true)`; `qa_tick(n)` advances the clock n ticks synchronously (printing is driven by the clock, so words also advance: one word per 0.08 s = 1.6 ticks; define the mapping and make it exact); `qa_click_entry(entry_id)`; `qa_dismiss()`.

Fault sites: `order-shuffled` reverses the entry order after validation; `expand-noop` shows the base form when expanded; `no-pause` keeps the clock running while expanded; `entries-duplicate` disables the R-068-07 drop and appends a near-copy of entry 3; `morph-instant` sets the colour without a tween; `cadence-wallclock` prints words from `Time.get_ticks_msec()` instead of the clock.

### 5. Build order (commit after each)

verify.gd red and stubs; fixtures and jump.gd; mini galaxy with morphs; scroll panel printing; expansion and pause; HUD, Skip, Proceed; smoke, checklist, screenshots, README.

## TDD protocol

1. Step 0: write `verify.gd` (`extends SceneTree`; `_init` runs one `_check_<id>()` per row of the check table below, then `quit(0)` or `quit(1)`; prints `FAIL: <id> <msg>` per failure and `VERIFY OK` on success, sharing one `_assert(cond, msg)`). Run `scripts/mockup_verify.sh chronicle`: it must print exactly one `FAIL:` line per check and exit 1. Commit as `test(mockup/chronicle): red verify.gd`.
2. Step 0 also: the root stub with `PLANTS`, `qa_state`, `qa_plant` (returns true for every listed id even before the feature exists), `qa/smoke.json`, `qa/checklist.md` copied from the template below, the `QADriver` child in the `.tscn`, and `docs/northstar/research/mockups/chronicle/README.md` with a one-paragraph "Design as built" placeholder.
3. Each build step: implement, run `mockup_verify.sh`, the named checks flip green, commit. Never edit a threshold; Westley owns them.
4. Every check carries its plant in a `# plant: <id>` line. Once the feature behind a check exists, `scripts/mockup_verify.sh chronicle --plant <id>` must print `PLANT <id> LIVE`; if it prints `DEAD`, fix the check or the fault site before committing.
5. Headless checks (verify.gd, dummy renderer, no autoloads): pure data, node-tree shape, API contract, determinism, CPU timing. Instantiate the scene when a check needs the tree: `var root = load("res://scenes/mockups/chronicle/chronicle_mockup.tscn").instantiate(); get_root().add_child(root); await process_frame`. Never call screenshot verbs headless.
6. Xvfb checks (driver plus shell): pixel diffs, pixel probes at projected positions, screenshot inspection, `fps_ms`. One clean run and one run per plant, in separate out dirs under your scratchpad; never mix the `plant` verb into a clean script.
7. `verify.gd` stays between 100 and 200 lines: at most 12 checks, each at most 15 lines.
8. After the clean and planted Xvfb runs, fill `qa/checklist.md` with the measured numbers, Read every screenshot, answer every visual question with the proving screenshot's name, fix every "no", rerun, and list what you cannot judge under `HELD:`.
9. Copy the review screenshots (1920x1080 batch) into `docs/northstar/research/mockups/chronicle/pass1/` and commit them; do not commit any other run output.
10. The report's check table lists, per check: clean result, plant id, planted result.

## Verify checks (`verify.gd`)

| id | check | where | plant |
|---|---|---|---|
| DET-1 | `qa_seed(11)`, `qa_tick(1200)` twice gives equal `hash` and equal `printed_words` per entry; seed 12 differs | H | `cadence-wallclock` |
| COUNT-2 | both fixtures have 5 to 10 entries after validation (R-065-01) | H | `entries-duplicate` (11 entries or a duplicate survives) |
| ORDER-3 | entry 1 is the consequence cluster naming the mission region; a lineage entry exists; no category has more than 2 entries; remaining entries are in descending score (R-065-02 to R-065-05) | H | `order-shuffled` |
| WORDS-4 | every base form under 90 words and every expanded under 140; expanded adds at least one sentence and at least one mention not in the base (R-068-02) | H | `expand-noop` |
| DUP-5 | no two surviving entries share 40 percent or more of content words relative to the shorter (R-068-07); a fixture with a planted near-copy drops the later one and reports it | H | `entries-duplicate` |
| KEY-6 | every entry's tick range contains a keyframe and every ownership change has one (R-069-05) | H | none; self-test with a broken fixture |
| PACE-7 | after `qa_tick` of exactly the ticks for 10 words, the printing entry has 10 words printed; `pace.word_interval_s == 0.08` | H | `cadence-wallclock` |
| PAUSE-8 | `qa_click_entry` on a printed entry sets `phase == "paused"`, `expanded_id`, and `qa_tick(100)` changes nothing; `qa_dismiss` resumes from the same word; clicking a printing entry does nothing (R-069-04) | H | `no-pause` |
| MORPH-9 | after a keyframe the system's colour is strictly between old and new at 1.0 s and equals new at 2.0 s | H (instantiate) | `morph-instant` |
| LAYOUT-10 | at narration start `map_width_fraction` is 0.62 and at the end 1.0 (R-069-01); the entry count on screen equals the validated count (R-069-06) | H (instantiate) | none |
| JSON-11 | `qa_state()` round-trips through JSON with every key; `qa_plant("nope")` false; every `PLANTS` id true | H | none |

Xvfb oracles: PRINT-X (`mid_print.png` shows a partially printed entry: `printed_words` strictly between 0 and total, and the text crop differs from `end.png`); EXPAND-X (the expanded overlay crop in `expanded.png` is taller than the collapsed entry crop in `mid_print.png`; under `expand-noop` the word counts are equal); MORPH-X (`diff before_morph.png after_morph.png` ≥ 0.005 over the map crop and `owners` changed; under `morph-instant` the 1.0 s frame equals the 2.0 s frame); PAUSE-X (two screenshots 60 frames apart while paused are identical, `diff` < 0.001 excluding the blinking cursor's crop); SEED-X (`diff end_seed11.png end_seed12.png` ≥ 0.10); ERR-0, GPU-0, DET-1 pixel.

## QA script and screenshots

`qa/smoke.json`: `state boot`; `seed 11`; `wait_frames 30`; `screenshot slide_in`; `call qa_tick 40`; `screenshot mid_print`; `state mid_print`; `call qa_tick 400`; `state printed`; `call qa_click_entry 1`; `wait_frames 2`; `screenshot expanded`; `state expanded`; `wait_frames 60`; `screenshot expanded_later`; `call qa_dismiss`; `call qa_tick 1`; `screenshot before_morph`; `state before_morph`; `call qa_tick 20`; `screenshot morph_1s`; `call qa_tick 20`; `screenshot after_morph`; `state after_morph`; `call qa_set skip true`; `wait_frames 5`; `screenshot end_seed11`; `state end`; `seed 12`; `call qa_set skip true`; `wait_frames 5`; `screenshot end_seed12`; `state end_seed12`; `key R`; `state after_r`. Pick the morph ticks from the fixture's first keyframe after entry 1. Review batch at 1920x1080: slide in, mid print, expanded, before and after morph, end for both seeds (7 shots) into `docs/northstar/research/mockups/chronicle/pass1/`.

## Checklist: visual questions

Read each PNG beside `docs/bible/references/E-09/time_jump_galaxy_and_scroll.png` and its rows in `references/E-09/notes.md`.

| q | question | proves |
|---|---|---|
| Q1 | Does the screen read as the reference's cousin: map two thirds left and animating, one entry at a time on the right in a serif face, faction names coloured? | rows 01 and 02 |
| Q2 | Does the printing pace read as writing itself, not a dump, and not a crawl (0.08 s per word is about 12 words per second; say whether that is readable)? | R-069-02 |
| Q3 | Does the morph read as a border changing, and does it line up with an entry about that region? | R-069-05, E-16 60-second text |
| Q4 | Does the expanded form read as more of the same passage, and does everything visibly stop while it is open? | R-069-04 |
| Q5 | Do the entries read as fragments of a real history, with a sense of humour where it fits, and never as log lines or filler? | hub tone, S-068 |
| Q6 | Any magenta, black, clipped or overlapping text at 720p? | hygiene |

## What the report must answer

1. Pace and legibility: is 0.08 s per word readable; what would you set?
2. Does the map side need more than points and morphs to read as the reference (shells, lanes)?
3. Whether the fixture's shapes were enough or the real message shapes need a field the mockup invented.
4. Frame time under llvmpipe at 720p with the SubViewport.
5. Under-defined points with candidates: the setup entry (Q-065-02), the per-category cap (Q-065-01), the expansion animation, whether Skip should also skip the morphs, the blinking cursor.

## Finishing report

Write it as your final message and also as the "Design as built" and "Questions for Westley" sections of `docs/northstar/research/mockups/chronicle/README.md` (normal prose; that file is read by Westley), ending with a "Next step" line that says the pass-1 screenshots are in `pass1/` and the mockup awaits his look. The report answers the numbered questions below, includes the check table (check, clean result, plant, planted result), the answers to the visual questions with proving screenshots, the `HELD:` list, timings (`timing_ms`, `fps_ms` under llvmpipe at 720p), the list of commits, and every under-defined point with two or three candidates and no decision.

## Verification (done when all of these hold)

- `scripts/mockup_verify.sh chronicle` prints `VERIFY OK`, exit 0; `scripts/mockup_verify.sh chronicle --plant <id>` prints `PLANT <id> LIVE` for every id in `PLANTS`.
- `scripts/mockup_qa.sh run chronicle scenes/mockups/chronicle/qa/smoke.json <scratch>/chronicle/clean` gives `exit.txt` 0, `errors.txt` 0, no `UNIFORM` line, `_qa.adapter` containing `llvmpipe`; a second clean run matches the first on every `hash` and every screenshot (`diff` under 0.005).
- One run per plant under `<scratch>/chronicle/plant-<id>` and every deterministic oracle in the checklist shows the planted number on the wrong side of its threshold.
- `qa/checklist.md` is filled; every visual question is answered or held; the pass-1 screenshots are committed under `docs/northstar/research/mockups/chronicle/pass1/`.
- `git status --short` on your branch shows only `scenes/mockups/chronicle/**` and `docs/northstar/research/mockups/chronicle/**`; `git diff --stat main -- scenes/tactical scenes/world scenes/main_menu scenes/mockups/landscape scenes/mockups/_shared tests csrc docs/bible docs/northstar/PLAN.md project.godot` is empty.
- The interactive command (`~/.local/bin/godot --scene scenes/mockups/chronicle/chronicle_mockup.tscn`) is documented in the README with its hotkeys; you cannot run it on Westley's seat, so confirm instead that a wrapper run without `--qa-script` leaves the driver inert (no `_run.json`).
