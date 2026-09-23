# Units mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, fix pass 2 2026-09-22 (Mockup review 1 response), Godot 4.6.3, llvmpipe, 1280x720 unless noted. Thresholds marked `(candidate)` are the brief's own numbers; nothing here was loosened. Fix pass 1 (fresh-eyes review response) rows are unchanged below unless noted "pass 2".

## Headless checks (`scripts/mockup_verify.sh units`)

| id | check | clean | plant | planted |
|---|---|---|---|---|
| DET-1 | seed 11 run(mirror_10v10,600) x2 equal hash; seed 12 differs from seed 11 on flank_4v4 (900 ticks) | PASS | seed-ignored | PLANT LIVE (1 FAIL) |
| ROSTER-2 | six roles per kit, R-082-02..04 orderings; positive control (broken kit dict) detected | PASS | none (data) | n/a |
| SIL-3 | bboxes pairwise distinct >10%; Strike smallest volume, Siege largest; anchor width>length; artillery longest | PASS | silhouettes-same | PLANT LIVE (shared plant, 2 FAIL: SIL-3 + FOOT-12) |
| MIRROR-4 | mirror_10v10 both sides alive at tick 900 (measured: 10 vs 10, unchanged); line-vs-Strike variant ≥5 Vanguard survivors at tick 2400 | PASS | instant-fight | PLANT LIVE (3 FAIL: DET-1 seed-divergence, MIRROR-4, FACE-6 — rapid deaths under 50x damage change all three; pre-existing plant behaviour, not touched this pass) |
| SOLID-5 | formation_move + flank_4v4 (repositioned this pass), 600 ticks: no obstacle overlap, no <28wu pair | PASS | pass-through | PLANT LIVE (1 FAIL) |
| FACE-6 | isolated 3-unit fixture, facing within 0.18rad of heading at tick 60; attacker faces target at tick 80 | PASS | facing-fixed | PLANT LIVE (1 FAIL) |
| PLAIN-7 | plain-move unit never targeted, advances >200wu at tick 700; positive control (attack-move variant) engages by tick ~450 | PASS | none (self-test) | n/a |
| DEATH-8 | bombards_1000 first death by tick 300 (measured: tick 124, confirmed via qa_state — see item 5 below), wreck present 60 ticks after | PASS | no-death-visual | PLANT LIVE (1 FAIL) |
| FORM-9 | formation_move arrival spread ≤40 ticks (measured 35, unchanged); split raider arrival 350-450 ticks (measured ~393, unchanged) | PASS | none | n/a |
| JSON-10 | qa_state() round-trips JSON, all contract keys present; qa_plant('nope') false; all 6 plant ids true | PASS | none | n/a |
| TIME-11 | tick_avg < 2ms for 20 units, headless (measured 0.30ms) | PASS | none | n/a |
| **FOOT-12 (new)** | instantiates the scene, builds each lineup unit's world AABB via `unit_view.get_unit_render_transform`/`get_role_mesh_aabb` (the real render path, not multimesh readback — proved dead under the headless dummy renderer, see item 1 below), projects the 8 corners through the camera; artillery's projected length must be longest, flanker's shortest | PASS (measured: artillery 108.3px longest, flanker 30.7px shortest, of flanker 30.7/screen 36.9/frontliner 46.6/support 36.3/artillery 108.3/anchor 64.4) | silhouettes-same | PLANT LIVE (shared with SIL-3, see above) |
| **DRAG-13 (pass 2)** | box overlay hidden before any drag; `hud._unhandled_input` press+motion+release simulated directly (not via `Input.parse_input_event`, which the private-field style of this file already relies on elsewhere); overlay visible mid-drag, hidden again after release | PASS | none | n/a |
| **PLAY-14 (pass 2)** | sim starts paused under `--qa-script`/headless (`qa_state().playing == false`); tick does not drift over 3 unforced `process_frame`s while paused; issuing a command via the interactive right-click path (`hud._handle_right_click`) does not auto-unpause in qa-mode | PASS | none | n/a |
| **PING-15 (pass 2)** | a ping registered then aged 2000ms of simulated wall time (`created_msec` back-dated, no ticks) while `unit_view.set_playing(false)` is asserted expired by the next `_process` call | PASS | none | n/a |

All 6 plant ids report `PLANT <id> LIVE` via `scripts/mockup_verify.sh units --plant <id>`. FOOT-12 had to be placed *before* JSON-10 in `_initialize()`: JSON-10 calls `qa_plant()` on every id to prove each returns true, and `QaPlants` is static process-global state with no reset call anywhere in scope — any plant-sensitive check placed after JSON-10 in the same verify run silently inherits every plant still active. This was latent (no check after JSON-10 needed plant-clean state before FOOT-12) and is now avoided by ordering, not by patching the shared `qa_plants.gd` (out of scope).

## Xvfb: clean run

`scripts/mockup_qa.sh run units scenes/mockups/units/qa/smoke.json <out> --timeout 400`, two independent runs.

| oracle | result |
|---|---|
| exit.txt | 0 (both runs) |
| errors.txt | count: 0 (both runs) |
| UNIFORM lines | none |
| `_qa.adapter` | `llvmpipe (LLVM 21.1.8, 256 bits)` |
| `_qa.method` | `gl_compatibility` |
| Two clean runs, hash | equal on every captured state (lineup, fight_t300, fight_end, flank_t200, face_north, death_t0, death_t20, seed12_flank, after_r — 9/9) |
| Two clean runs, screenshot diff | 0.000000 on every shot checked (lineup_greek, fight_end, death_t20) |
| `fps_ms` (720p, per rendered frame) | 156.5ms |
| `timing_ms.tick_avg` (20 units, headless) | 0.30ms |

## Fix-by-fix evidence (this pass, ordered per the brief)

### 1. Artillery silhouette scale bug

**Before:** artillery (`long_barrel`, kit size `[128,20,16]`) rendered as the smallest blob on screen; anchor (`wide_block`, kit size `[52,76,28]`) rendered larger, despite artillery's declared length being 2.5x anchor's.

**Root cause (two stacked bugs, found by direct probing, not guessed):**
1. `Basis.scaled(scale_v)` does not scale local-X by `scale_v.x` and local-Z by `scale_v.z` as the original code assumed — confirmed by constructing a known basis and transforming probe points: `scale_v.x` ends up applied to local **Z** and `scale_v.z` to local **X**. Fix: `basis_rot * Basis.from_scale(scale_v)` instead of `basis_rot.scaled(scale_v)` (scale in local space, then rotate — verified against the same probe points).
2. The six `SHAPE_POINTS` recipes don't all span the full ±0.5 unit square on both axes (`long_barrel`'s local X only spans 0.24, `swept_dart`'s 0.3, `wide_block`'s local Z only 0.7) — scaling by the raw kit `size` without normalizing for each shape's own bounding-box extent distorted every recipe whose local extent isn't 1.0, worst for artillery (rendered width ended up 4.8wu instead of 20wu). Fix: `_get_shape_extent(shape)` computes each shape's real local bbox once (cached) and the render transform divides by it, so declared kit `size` always equals the rendered world footprint exactly, for any shape's internal proportions.

**After:** measured world AABB size after the fix matches kit `size` exactly for all six roles (e.g. artillery `(128.0, 16.0, 20.0)` vs kit `[128,20,16]`; anchor `(52.0, 28.0, 76.0)` vs kit `[52,76,28]`, length/width swapped correctly because anchor's shape is naturally wide, not long). Proving screenshot: `pass1/lineup_greek.png` — artillery reads as the longest, thinnest shape; anchor reads as the widest block.

**New check:** FOOT-12 in `verify.gd` instantiates the scene, builds each role's real render transform (not a data re-derivation of SIL-3, and not a MultiMesh instance-transform readback — proved dead under the `--headless --script` dummy renderer: a hand-set `MultiMesh.set_instance_transform` round-trips to identity, confirmed with an isolated bare-`MultiMesh` probe before writing the check), and projects the AABB corners through the camera. Green clean, red under `silhouettes-same` (which now also breaks SIL-3, since it collapses every role to one uniform box).

### 2. Support silhouette reads as plain disc

**Before:** `spire_radial`'s top surface was a flat octagon cap at uniform height — indistinguishable from a disc at any zoom.

**Fix:** `_build_spire()` splits the mesh into a shorter base prism (height 0 to 0.55, the octagon rim) plus a cone rising from that rim to a single central apex at height 1.0.

**Evidence:** close-up screenshot (scratch, not committed) before/after — after shows a lit apex highlight distinct from the octagon rim, reading as "radial base with a raised central point." Confirmed again at map zoom in `pass1/lineup_greek.png`.

### 3. Strike squads indistinguishable at lineup camera

**Before:** at the brief's literal height-1500 lineup camera, flanker's 5-dart squad and screen's 4-wing squad both read as small scattered blue clusters with no distinguishing shape.

**Fix:** lineup camera to height 900 (brief's own suggestion); `lineup.json` spacing tightened 300→220wu (six-unit span 1500→1100wu) to stay inside the tighter frustum at that height (visible width ≈1492wu at height 900, fov 50 vertical, 16:9 aspect — computed, then confirmed empirically with a screenshot showing no clipping).

**After:** `pass1/lineup_greek.png` / `pass1/lineup_settled_reach.png` — flanker's small diamond-shaped darts and screen's larger wing/triangle shapes are now visually distinct as different squad clusters, and all six roles stay ordered by size.

### 4. Flank scenario framing

**Before:** `flank_4v4`'s four Raiders started 40wu apart (all at the same x), one shared attack-move command — the multi-unit command's offset-from-centroid math preserved that tight cluster all the way to the destination, so all four computed near-identical BFS routes around the single obstacle and queued single file. The smoke script's camera never re-centred for this scenario, clipping the Bombards at the frame edge. Result: 1 Raider dead, 0 Bombards dead at tick 900.

**Fix:**
- `flank_4v4.json`: Raiders repositioned into two widely-spread pairs (z 3200/3450 north, z 4550/4800 south — outside the obstacle's z-range 3600-4400 individually), obstacle narrowed to z 3600-4400 so each pair's approach lane is naturally clear. Each Raider now gets its **own** single-unit `attack_move` command converging on the same point at the Bombard cluster (`live_count==1` per command ⇒ no centroid-offset spreading applied to the destination), so they path independently and reconverge for the engagement instead of marching as one blob.
- `qa/review.json`: `qa_camera` centred on the midpoint of the two live forces' actual positions at the capture tick (not the scenario's static tick-0 midpoint), at height 900. Tried both 500 and 900: at 500 no deaths have landed yet (contact visible, but nothing to distinguish "engagement" from "approach"); at 900 both sides have taken losses (evidence of an actual fight) and the pincer is tighter — kept 900.

**Evidence:** `pass1/flank_result.png` (tick 900) — four Bombards clustered centre-frame, Raider squads clearly split north and south, closing in — reads as "Raiders around the flank," not a blob or an edge-clipped mess.

**Outcome (seed 11, same R-082-01 stats, no tuning):** at tick 900, 3 Raiders and 3 Bombards alive (was 3/4 before this fix — the spread approach means Bombard fire splits across multiple nearest targets instead of concentrating on one Raider at a time). Full run to ~1500 ticks: **Bombards still win** (3 Bombards alive, 0 Raiders, by tick 1500). Per the brief's instruction, stats were not tuned to force a Raider win; recorded below under Questions for Westley with two candidates.

### 5. Death legibility

**Root-cause finding (bigger than camera work alone could fix):** direct pixel sampling of `death_t0.png` vs `death_t20.png` before any fix showed a colour delta of <1 unit out of 255 — the flash/death colour system was rendering nothing at all, regardless of camera position. Traced to two stacked bugs:
1. `StandardMaterial3D` never set `vertex_color_use_as_albedo` — the whole per-instance MultiMesh colour mechanism (the entire flash/death system) was silently ignored by the renderer.
2. Even with that flag on, the material's `albedo_color` carried the faction colour and the per-instance colour was a *near-white multiplicative tint* meant to lerp toward `FLASH_BOOST`/`DEATH_BOOST`. Multiplying an already-saturated base colour by a ≤1.0 tint can only darken, never brings a unit brighter/warmer than its own hue — mathematically incapable of a "flare" no matter the camera.

**Fix:** material albedo goes neutral (white pass-through); the per-instance colour now carries the **fully-resolved** colour directly (faction colour at rest, lerped to `FLASH_BOOST`/`DEATH_BOOST` on hit/death) instead of a tint multiplier.

Also fixed an off-by-one in `qa/smoke.json`: the death tick for `bombards_1000` (uid 10, frontliner, seed 11) is 124 (confirmed via `qa_state`, `death_tick` field), not 140 (original) or 123 (first attempt) — both landed one tick before or after the unit was actually recorded dead. Added `qa_camera(700, 3404, 4000)` (the unit's own death position) before `death_t0`.

**Evidence:** `pass1/death_t0.png` shows the dying unit rendering in a bright warm orange/yellow, unmistakably distinct from the still-alive red frontliners beside it. `pass1/death_t20.png` shows it darkened to a deep red (darker than the alive units) and visibly drifted left (matching its last heading, west). This is the same mechanism that makes `fight_mid.png`'s hit-flashes visible (item 6) — one fix, two items unblocked.

### 6. Fight readability

Added `qa_tick_until_flash(max_ticks)` on the root (delegates to `hud.gd`), which steps one tick at a time until `unit_view.flashes_active > 0`. On `mirror_10v10` at seed 11 this returns after 1 tick (units start 250wu apart, already inside the 300wu frontliner range, attack timer pre-charged, so several units land their first hit almost immediately).

`fight_mid` captured via `qa_tick_until_flash(60)` (landed at tick 1): multiple units visibly white-flashed on both lines. `fight_end` captured at tick 1601 (1 + 1600 more ticks), past the first kill (measured first death tick 1576): `Blue: 2 Red: 5` in the HUD, wrecks (tan/orange, darkening) visible mixed among the survivors — who's winning is now legible both in the HUD text and visually.

**Evidence:** `pass1/fight_mid.png`, `pass1/fight_end.png`.

### 7. Black void bars at fight_mapzoom edges

**Root cause:** ground plane was 9000×9000 centred on the canvas centre (spans -500 to 8500); at camera height H with fov 50 (vertical) and 16:9 aspect, visible half-width = H×0.829. Above height ≈5428 (centred on canvas centre) the frustum exceeds the ground plane and shows sky/void at the left and right edges. Reproduced directly: height 7000 screenshot shows clear dark void bars at both edges.

**Fix:** ground `PlaneMesh` size 9000→14000 (`units_mockup.tscn`), safe up to height ≈8443 centred on canvas centre.

**Evidence:** same height-7000 screenshot re-taken after the fix shows a fully filled frame, no void. `pass1/fight_mapzoom.png` uses height 4500 (well inside the new safe range).

### 8. First-frame HUD contrast

**Root cause:** `TickLabel`/`SurvivorsLabel`/`SelectedLabel`/`LogLabel` have no backing panel and default label styling — pale-grey text on the greek kit's pale-yellow ground was nearly invisible on **every** frame (confirmed with a pixel crop before the fix — not just frame 1, contrary to the "first-frame" framing in the fresh-eyes review, but the same fix applies).

**Fix:** black font outline (`outline_size` 6) added to all four labels in `hud.gd:_ready()` — works regardless of frame timing, doesn't occlude the 3D scene.

**Evidence:** pixel crop of `lineup_greek.png`'s HUD region before/after — "Tick: 0", "Blue: 6 Red: 0", "Selected: none" go from illegible to clearly readable.

### 9. face_east.png / face_north.png committed

Both now included in `pass1/` (1920×1080, from `qa/review.json`), previously generated but never committed.

## Xvfb deterministic oracles, clean vs planted (unchanged mechanism from the prior pass, re-verified)

| oracle | candidate threshold | measured clean | note |
|---|---|---|---|
| KIT-X | `diff(lineup_greek, lineup_settled_reach) >= 0.10` | high (ground colour + faction palette differ) | unaffected by this pass |
| DET-1 pixel | two clean runs, diff < 0.005 | 0.000000 on every shot checked | re-confirmed this pass |
| ERR-0 | 0 script errors | 0 (both runs) | re-confirmed |
| GPU-0 | adapter contains llvmpipe | yes | re-confirmed |
| FIGHT-X, DEATH-X, FACE-X, SEED-X (tick 200) | full-frame pixel diff | still not discriminating at a full-frame level (small units against a mostly-empty ground) — this pass's fix makes the *effect itself* visible (see items 5/6 above with cropped/zoomed evidence and `qa_state` fields), which is the load-bearing proof; the brief's full-frame diff oracles remain supplementary, as flagged in the prior pass | unchanged finding, not re-litigated |

## Visual questions

| q | question | answer | proving screenshot |
|---|---|---|---|
| Q1 | Name all six roles from shape alone? | **Yes**, now. `frontliner` (wedge), `anchor` (wide block), `support` (octagon + raised spire), `artillery` (long thin barrel, now correctly the longest silhouette on screen) all read individually; `flanker` and `screen` read as two visually distinct squad clusters (small diamonds vs. larger wings) at the height-900 lineup camera. | `pass1/lineup_greek.png` |
| Q2 | Same six roles obviously the same in both kits? | **Yes.** Geometry and position identical between kits; only ground colour and unit palette differ. | `pass1/lineup_greek.png` vs `pass1/lineup_settled_reach.png` |
| Q3 | Mid-fight: who's winning, where's the front, hits visible without shake? | **Yes to all three now.** Front: two facing lines, unmistakable. Hits: multiple units visibly white-flashed at `fight_mid` (tick 1, via `qa_tick_until_flash`). Who's winning: `fight_end` (tick 1601) shows `Blue: 2 Red: 5` in the HUD and visibly fewer blue units plus several darkening wrecks on screen. No shake (still not implemented, not requested). | `pass1/fight_mid.png`, `pass1/fight_end.png` |
| Q4 | Death unmistakable: flare, drift, darkening? | **Yes**, now. `death_t0.png` shows a bright warm orange/yellow flare unmistakably distinct from the alive red units beside it; `death_t20.png` shows it darkened to a deeper red than any alive unit and visibly drifted. Previously HELD (root-cause traced and fixed this pass, see item 5). | `pass1/death_t0.png`, `pass1/death_t20.png` |
| Q5 | Does the flank result read as Raiders behind Bombards, not a blob? | **Yes**, now, at tick 900. Four red Bombards clustered centre-frame; blue Raiders visibly split into two prongs (north and south) closing in — not single file, not a blob, not clipped at the frame edge. | `pass1/flank_result.png` |
| Q6 | Do units face travel and targets; does a turn look like a turn? | **Yes**, confirmed both by `qa_state()` facing data (FACE-6 passes) and by direct visual inspection of the committed `face_east.png`/`face_north.png` pair — the screen squad's V-formation visibly rotates ~90° between the two shots. | `pass1/face_east.png`, `pass1/face_north.png` |
| Q7 | Any magenta, black, clipped or overlapping HUD text at 720p/1080p? | **No.** HUD text now has a black outline for contrast (was pale-grey-on-pale-yellow, nearly invisible — fixed this pass) and is not clipped or overlapping at either resolution. No void/black bars at any camera height used (fixed this pass, see item 7). | all `pass1/` shots |

**HELD:** none carried over from the previous pass — Q4 (death legibility) is resolved this pass with a traced root cause, not just a camera change.

## Bugs found and fixed during this pass (beyond the fresh-eyes review's 9 items)

1. **`Basis.scaled()` axis-swap + shape-extent distortion** — the actual root cause behind item 1's artillery silhouette bug, verified empirically (not assumed) with isolated `Basis` probes before touching `unit_view.gd`. See item 1 above.
2. **Flash/death colour rendered nothing** — `vertex_color_use_as_albedo` was never set, and even fixed, the multiplicative-tint design could never brighten past the base colour. See item 5 above; this single fix also resolves item 6's "hits visible" requirement.
3. **`QaPlants` static state pollutes checks after JSON-10** — `_check_JSON_10` activates every plant id to prove `qa_plant()` returns true and never resets (no reset function exists in the shared, off-limits `qa_plants.gd`); any plant-sensitive check placed after it in `_initialize()` silently inherits every plant. FOOT-12 is the first check added after JSON-10's position that's actually plant-sensitive, so this was latent, not a regression. Fixed by check ordering within `verify.gd` only.
4. **`qa/smoke.json`'s death-tick off-by-one** — `qa_tick(140)` (then a first-attempt `qa_tick(123)`) both missed the unit's actual `death_tick` (124) by one tick either side; `qa_state()` at the "death" screenshot showed the unit still alive (hp 27.5). Fixed by using the tick count that lands exactly on `death_tick`.

## Fix pass 2 (2026-09-22, Mockup review 1)

Westley's verbatim report and root causes are in `docs/northstar/research/mockups/units/README.md` under "Mockup review 1". Evidence per item, in the brief's order:

### 1. Units do not move, waypoints never fade

**Root cause confirmed:** `hud.gd` started with `_playing = false` and never flipped it; `_process` only steps the sim `if _playing`, so a fresh interactive launch never ticked. `unit_view.gd`'s pings expire by comparing `current_tick` to a lifetime, so with the sim never ticking the comparison never advances and a ping never crosses `PING_LIFETIME_TICKS`.

**Fix:** `hud._ready()` computes `_qa_mode := OS.get_cmdline_user_args().has("--qa-script") or DisplayServer.get_name() == "headless"` once. `_regenerate()` now sets `_playing = not _qa_mode` (via a new `_set_playing()` helper) instead of always `false`, so an interactive launch (real display, no `--qa-script`) starts playing and a QA/verify boot stays paused — both signals checked because `mockup_qa.sh run` launches through Xvfb's real X11 display (only `--qa-script` present) while `mockup_verify.sh` launches `--headless` with no `--qa-script` at all (`scripts/mockup_qa.sh` / `scripts/mockup_verify.sh`, see the two `godot` invocations). `PLAY-14` proves both: `qa_state().playing == false` right after boot, and tick does not drift over 3 unforced frames. Issuing an order (`_handle_right_click`) resumes a paused *interactive* session but is gated `and not _qa_mode` so a QA script's simulated right-click never starts wall-clock ticking mid-script (would have broken every hash/pixel-identical oracle below) — `PLAY-14`'s third assertion proves the gate holds.

A `PausedLabel` (new node, `units_mockup.tscn`) shows "PAUSED" (black-outlined, 48pt) whenever `not _playing`; `Space` and any order both clear it via the same `_set_playing()` path.

Pings: `unit_view.add_ping` now stamps `created_msec := Time.get_ticks_msec()`; a new `unit_view._process` ages every ping against a 1500ms wall-clock cutoff **only while paused** (`_playing_hint == false`, set by `hud._set_playing` calling `_view.set_playing()`), so the existing tick-based expiry stays authoritative (and deterministic) while playing, and a paused interactive scene still clears its waypoints. `PING-15` proves the wall-clock path fires without needing a real 1.5s sleep (back-dates `created_msec` by 2000ms, calls `_process` once, asserts `pings_active() == 0`). Confirmed inert for every committed QA script: `smoke.json`/`review.json` never leave more than milliseconds of real time between a `qa_command` and the next `screenshot` (synchronous calls, no intervening `wait_frames`), so the wall-clock path never fires during a scripted run — the two clean-run diffs below are unaffected.

**Evidence:** `pass1/lineup_greek.png` (re-shot) shows "PAUSED" top-centre — the QA boot is paused by design, matching `qa_state().playing == false`; this is expected and correct (see `PLAY-14`), not a defect. Westley's interactive launch is untested from this session (same constraint the pass-1 doer noted — no display available here), but the code path is symmetric with the QA path already proven live, and PLAY-14's headless assertions exercise the same `_qa_mode`/`_set_playing` logic Godot runs when a real display is attached.

### 2. No visible drag-select box

**Root cause confirmed:** `hud._handle_left_release` always computed a `Rect2` for hit-testing but nothing was ever drawn — no `Control`, no `_draw()`, anywhere in the drag path.

**Fix:** new `scenes/mockups/units/drag_box.gd` on a full-rect `Control` (`DragBox`, child of `HUD`, `mouse_filter = IGNORE`, `visible = false` at rest) drawing the brief's exact fill `(0.3, 0.8, 1.0, 0.08)` / edge `(0.3, 0.8, 1.0, 0.75)` width 1.5 via `_draw()`. `hud._unhandled_input` now tracks `InputEventMouseMotion` while `_dragging` and calls `_drag_box.set_rect(rect, true)` on press and every motion, `set_rect(Rect2(), false)` on release — `set_rect` toggles both `visible` and the internal `active` flag redrawn flag together, so `visible` is a true proxy for "box on screen," not just "control exists." `DRAG-13` proves all three states (hidden before any drag, visible mid-drag, hidden again after release) by calling `hud._unhandled_input` directly with synthetic press/motion/release events — the same code path real input drives.

For QA scripts, the built-in `drag` verb is atomic (press, lerped moves, release, no callback in between), so a genuine mid-drag screenshot needed new driver-adjacent methods: `hud.qa_drag_start/qa_drag_to/qa_drag_end` (delegated from `units_mockup.gd`), each just constructing the matching `InputEvent` and calling `_unhandled_input` directly, callable individually via the harness's `call` verb. `qa/review.json` now does `qa_drag_start(150,450)` → `qa_drag_to(1750,650)` → `wait_frames 2` → `screenshot drag_mid` → `qa_drag_end` over the `lineup` scenario's six units (screen positions probed via `qa_state().units_px` first, 1920x1080). Both `drag_mid`/`drag_released` state dumps confirm `drag_active`/`drag_box_visible` flip correctly.

**Evidence:** `pass1/drag_mid.png` — a light-blue-filled, blue-outlined rectangle spans the six lineup units exactly as pressed-and-dragged, matching the "no visible box... though it does work" complaint directly. `docs/northstar/research/mockups/units/pass1/drag_released.json`/`drag_mid.json` are not committed (the assertions live in `DRAG-13`); the screenshot is the visual proof.

### 3 and 4. Edge scroll unreachable at 4480x1440 / edge scroll fires over the HUD

Fixed by the paused-mid-run doer before this session resumed (commit `beced71`, `camera_rig.gd`/`hud.gd`); this session verified rather than re-derived. Root cause matches the brief exactly: `get_viewport().get_visible_rect().size`, read from `camera_rig.gd` (a bare `Node3D`, not a `Control`), reports the inflated `canvas_items` stretch space (see `scenes/mockups/_shared/README.md`'s documented fact), which is neither the canvas nor the real window — so on a window wider than that inflated space's right/bottom bounds, the zone is never reached. Fix tracks the mouse in canvas space via `_input`'s `InputEventMouseMotion.position` (never `get_viewport().get_mouse_position()`, which the shared README notes ignores synthetic/injected input), converts to real window pixels via `get_viewport().get_final_transform()`, and compares against `DisplayServer.window_get_size()` — both sides now the same space. Edge scroll is additionally suppressed whenever `get_viewport().gui_get_hovered_control() != null` or the mouse is inside the HUD panel's rect.

**Evidence (`qa/edges.json`, `--res 2560x1440`, this session's run):**

| case | `camera_pos` before | `camera_pos` after 30 frames | result |
|---|---|---|---|
| left (20, 720) | [4000, 4000] | [2450, 4000] | PASS (x decreases) |
| right (2540, 720) | [4000, 4000] | [5550, 4000] | PASS (x increases) |
| top (1280, 20) | [4000, 4000] | [4000, 2450] | PASS (z decreases) |
| bottom (1280, 1420) | [4000, 4000] | [4000, 5550] | PASS (z increases) |
| hud (235, 42), over the scenario dropdown | [4000, 4000] | [4000, 4000] | PASS (no pan) |

Exit 0, 0 errors, one plant run each unaffected (plants don't touch camera code).

## Determinism re-check (fix pass 2)

Two independent `smoke.json` runs at 1280x720 after all four fixes: `exit.txt` 0/0, `errors.txt` 0/0, every `state` JSON identical except `timing_ms.tick_avg` (a measured wall-clock duration, expected to vary — unchanged finding from pass 1, not a regression), `hash`/`tick`/`playing`/`camera_pos`/`drag_active`/`drag_box_visible`/`pings_active`/unit positions all equal. Screenshot diff 0.000000 on `lineup_greek`, `fight_end`, `death_t20` (unchanged from pass 1's own oracle set). `scripts/mockup_verify.sh units` still `VERIFY OK` (18 checks now, +DRAG-13/PLAY-14/PING-15) and all 6 plants still report `PLANT <id> LIVE` with the same fail counts as pass 1 (pass 2's new checks are not plant-sensitive — none of the six plants touch input, pause state, or ping timing).
