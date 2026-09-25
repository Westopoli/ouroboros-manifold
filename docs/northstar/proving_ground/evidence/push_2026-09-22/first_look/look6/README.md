# Look 6 (post-C2-5b, B9-11, B12-11, B14-7), 2026-09-24

Base: `origin/main` at `571a76a` (QA lane brief). Seed 1, 1280x720, real boot → New Game → galaxy (200 ticks, 6 plants) → Mission → briefing → Deploy → tactical (one click) → End Mission → debrief → Continue → chronicle → Return → galaxy → Continue from autosave (run 2). Driver: scratch tooling (`look6_driver.py`), deleted after run, not in repo. Screenshots in `look6/`, numbers in `look6.json`.

**Held claims, not passes: what one Xvfb/software-GL run rendered.**

Desktop QA suite: 14/14 passed before run.
Liveness: `LIVENESS OK os_inputs=3 scene=res://scenes/harness/harness.tscn`.

## Bottom line

Galaxy renders correctly (owner-coloured dots, edges, 29 conquests recoloured over 200 ticks). Main menu, briefing, debrief, Continue flow all reach their scene and render meaningful data. Tactical view loads the live frame (tick=1) but renders completely blank — no units, no map, no fog. Chronicle is empty after a 250-tick game. Three bug rows filed (QA-001 through QA-003).

## Screen by screen

### Main menu (`00_main_menu.png`)

Full render: "OUROBOROS MANIFOLD" title, "A WESTOPOLI GAME", all 5 items (NEW GAME, CONTINUE (greyed/disabled), ERA LIBRARY, SETTINGS, QUIT), tagline "Have an access key? Visit the Era Library to redeem it.", "Replay Tutorial" bottom-left, version v0.9.0 bottom-right. Screenshot taken 1.5s after scene swap to let the entrance animation finish.

- `continue_enabled`: false — correct (no saves, fresh run)
- `slot_count`: 0 — correct

Boot to menu: 1.1s wall clock.

### Galaxy at tick 0 (`01_galaxy.png`)

80 coloured dots with grey 3D filament edges, centre of screen, MISSION button bottom-right. Multi-colour: 16 distinct region colours, 51 owned regions at tick 0. Owner colours match `qa_state().region_colours`.

- `system_count`: 80, `owned`: 51, `distinct_colours`: 16

Menu-to-galaxy transition: 0.73s.

### Galaxy at tick 200 (`01b_galaxy_t200.png`, `gal_plant_clean.png`)

29 owner changes, 29 recoloured. Every region that changed owner drew its new owner's colour: 29/29. Conquest recolour pipeline works end to end (C2-4 + C2-5b confirmed live). `step_200_s`: 0.91s wall clock for all 200 ticks to complete.

### Plants (post-200-tick galaxy)

Baseline: `gal_plant_clean.png` (taken right before first plant, post-200 ticks, all owners live). Plants applied in order, no unplant between them (gap noted below).

| plant id | activated | diff_px / 921600 | read |
|---|---|---|---|
| `seed-ignored` | true | 0 | behaviour-only: flag `qa_seed()` checks; no re-layout triggered this run |
| `owner-colour-flat` | true | 5907 | visible change — all dots render the same salmon red (`plant_owner_colour_flat.png`); filament edges still grey; confirms `_recompute_region_colours` path now fires and produces a renderable diff |
| `edges-2d-overlay` | true | 36936 | stacked on `owner-colour-flat`; edges disappear entirely (`plant_edges_2d_overlay.png`): 3D filaments suppressed, 2D overlay renders nothing — no 2D edge sprites exist yet |
| `pick-radius-zero` | true | 36936 | stacked; diff dominated by `edges-2d-overlay` already active; behaviour-only by design (changes `pick_radius_px` in `qa_state`) |
| `bands-frozen` | true | 36936 | stacked; behaviour-only (freezes camera-distance band at current value) |
| `conquest-no-recolour` | true | 36936 | stacked; positive control — would show stale colours after a conquest; stacked diff again dominated by earlier plants |

**Plant stacking gap**: `qa_plant` has no unplant, so each screenshot captures cumulative effects of all previous plants. `edges-2d-overlay` is the first plant that produces a large visual change; plants 4-6 show 36936 diff even if they produce no further visual change of their own. To get clean per-plant pixel diffs, the daemon needs an `unplant` verb (or each plant run needs a fresh game instance). This is a QA capability gap, not a game bug; plants 4-6 are not confirmed broken or working from pixel diff alone.

**`owner-colour-flat` now works** (diff was 0 in look 4 because the world was empty at t=0; look 6 at t=200 with real owners: 5907 px difference confirmed).

**`edges-2d-overlay` removes all edges**: the 2D overlay path draws nothing where 3D filaments would be. At current base, no 2D edge sprites, so switching mode to 2D produces blank edge layer. Filed as QA-002 (wrong but not blocking play; the default mode shows 3D edges correctly).

### Mission briefing (`02_briefing.png`)

Scene reached in 0.94s. Screenshot shows:

- "MISSION BRIEFING" header, "// Chapter 0 // Generation 0"
- "TICK 300" (deadline) top-right; ERA chip
- "MISSION OBJECTIVES": "Unmarked Position" — real data from sim
- "INTELLIGENCE REPORT": blank (no text rendered)
- "ENEMY ASSESSMENT": MILITARY 0, TECH TIER 0 — zeros, live sim fields absent
- "YOUR FORCE": FORCE PARITY 0 — zero
- "REGION STATE": ECONOMY 0, MILITARY 0, TENSION 0 — zeros
- "COMMANDER LINEAGE": Generation 1, "First of the line" — correct generational data
- Buttons: DEPLOY FORCES, REVIEW CHRONICLE, BACK

Objective name is live data. Force, enemy, and region panels show zeros because those sim fields are absent in the briefing frame (expected gap per E-10/E-11; not a new regression). Intelligence Report blank is same expected gap.

`briefing_qa.objectives` from driver: null — driver read wrong key (`objective_count`); the real key is `objectives` (array). The briefing itself renders one objective correctly.

### Tactical view (`03_tactical.png`, `03b_tactical_after_click.png`)

Scene reached in 0.69s after Deploy click. Screenshot shows: completely blank grey screen. Only "END MISSION" button top-right.

`qa_state()` at tick 1 returns `canvas: 24000` and `units` dict (not `unit_count`). Driver read wrong key (`unit_count`), recorded 0. Actual unit count not read this run; look5 at equivalent point showed 572 units (276 faction 0, 296 faction 1). Frame loaded (tick=1 confirms `mission_begin` fired and one tactical step ran). Units exist in the sim, but nothing renders on screen.

One click sent to (640, 360): second screenshot byte-identical to first (no visual response to click, expected since no visible units or map to interact with).

**QA-001**: blank tactical view filed below.

### Debrief (`04_debrief.png`)

Scene reached 0.62s after EndMission. Shows:

- "MISSION DEBRIEF" header
- OUTCOME: "PARTIAL FAILURE", "Score: 0%"
- FORCE STATUS: Force Retained 100%, Objective Score 0%, Commander SURVIVED
- SIMULATION IMPACT: header only, no stat rows

`band`: partial_failure, `achieved_pct`: 0.0, `brought_home_pct`: 100.0, `region_delta` all 0.

Partial failure + 0% score is expected (mission ended immediately at tick 1, no objective progress made). All force retained because no combat. Region deltas all 0 is expected for a zero-combat outcome.

"SIMULATION IMPACT" renders with just the header and no rows when all deltas are 0. Player can infer nothing happened, but an explicit "no impact" line would be clearer. **Not filing as a bug** — behaviour is technically correct; could be improved.

### Chronicle (`05_chronicle.png`)

Scene reached 0.62s after Continue. Shows: "CHRONICLE" header top-left, "RETURN" button below it, rest of screen blank grey.

`entries` from `qa_state()` (correct key this time): 0 entries, 0 dropped, 0 unresolved. After a 250-tick game with 29 conquests, there are genuinely 0 chronicle entries. Same result as look 5. Chronicle generation apparently requires different conditions (specific events, character deaths, other triggers). Player sees an empty screen.

**QA-003** filed (wrong: player sees empty chronicle with no explanation).

### Return to galaxy (`06_return_galaxy.png`)

Scene reached 0.62s after Return. Galaxy at tick 250 (200 step + 50-tick jump after mission), 80 systems. Colours updated post-conquest. Pixel difference vs `01_galaxy.png`: non-zero (colour shifts from the 29 conquests).

### Run 2: Continue from autosave

Autosave `campaign_1.omsave` written at tick 250 during run 1.

Fresh boot with `OM_SAVE_DIR` pointing at the same save dir. Boot: 1.1s. Menu: `continue_enabled` true, `slot_count` 1 — correct. Clicked Continue → Load Game screen → Load_campaign_1 → galaxy. Galaxy loaded at tick 250 (matches saved tick). `system_count` 80. Continue flow works end to end.

## Plant screenshots note

Pixel diffs for plants 3-6 (`edges-2d-overlay`, `pick-radius-zero`, `bands-frozen`, `conquest-no-recolour`) are all 36936 because plants stack and no unplant exists. The diff measures vs `gal_plant_clean` (t=200, before any plant). After `owner-colour-flat` (5907 diff) then `edges-2d-overlay` (cumulative 36936 diff), the remaining plants produce no additional visual change on top. This does NOT mean plants 4-6 are broken — it means their visual effects cannot be isolated without a fresh boot or an unplant verb.

## What a player would notice

1. Main menu: clean. Title present, menu items correct, CONTINUE greyed correctly on first launch.
2. Galaxy: looks good — coloured systems, edges visible, evolves over time.
3. Briefing: mostly placeholders (enemy/force/region all zeros). "Unmarked Position" as objective is real but opaque.
4. Tactical: **completely blank**. Player clicks Deploy and sees nothing — no map, no units, just grey. This is the most visible problem in the current build.
5. Debrief: readable. Outcome clear.
6. Chronicle: empty. Player wonders why.
7. Continue: works perfectly.

## Files

- `00_main_menu.png` — main menu, ~1.5s after scene swap
- `01_galaxy.png` — galaxy at tick 0 after New Game
- `01b_galaxy_t200.png` — galaxy at tick 200 after step verb
- `02_briefing.png` — mission briefing
- `03_tactical.png` — tactical view after Deploy (blank)
- `03b_tactical_after_click.png` — after one click at (640, 360) (unchanged)
- `04_debrief.png` — mission debrief
- `05_chronicle.png` — chronicle after 50-tick jump (empty)
- `06_return_galaxy.png` — galaxy at tick 250 after Return
- `07_menu_with_save.png` — main menu in run 2 (Continue enabled)
- `08_load_game.png` — load game screen in run 2
- `09_loaded_galaxy.png` — galaxy at tick 250 after loading save
- `gal_plant_clean.png` — clean galaxy at t=200, before any plant
- `plant_seed_ignored.png` — seed-ignored planted (identical to clean)
- `plant_owner_colour_flat.png` — owner-colour-flat (all dots same red, edges still grey)
- `plant_edges_2d_overlay.png` — edges-2d-overlay stacked (dots red, edges gone)
- `plant_pick_radius_zero.png` — pick-radius-zero stacked (same as edges shot)
- `plant_bands_frozen.png` — bands-frozen stacked (same as edges shot)
- `plant_conquest_no_recolour.png` — conquest-no-recolour stacked (same as edges shot)
- `look6.json` — full numeric record
