# Menus mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs on 2026-09-22, Godot 4.6.3, llvmpipe (`gl_compatibility`), 1280x720 unless noted. Every threshold here is a candidate; Westley owns the final number.

## Check table (verify.gd, headless)

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | resolve(0.9, medium, 11, T) twice equal; seed 12 differs; same seed same band | pass | band-random | FAIL, 1 FAIL line — `PLANT band-random LIVE (1 FAIL)` |
| EDGES-2 | every allowed edge transitions; disallowed rejected with a reason; title→briefing direct rejected | pass | flow-skips-setup | FAIL — `PLANT flow-skips-setup LIVE (3 FAIL)` (cascades into SETUP-3, CAMP-9 too, since `begin` from `briefing` is no longer a valid edge once `new_campaign` skips `setup`) |
| SETUP-3 | difficulty in campaign record; changes resolve score | pass | difficulty-dropped | FAIL — `PLANT difficulty-dropped LIVE (1 FAIL)` |
| SECT-4 | briefing renders exactly Situation, Objective, Assets; attacker named | pass | briefing-two-sections | FAIL — `PLANT briefing-two-sections LIVE (1 FAIL)` |
| DIGITS-5 | no digit in briefing or debrief text | pass | digits-in-prose | FAIL — `PLANT digits-in-prose LIVE (1 FAIL)` |
| BANDS-6 | finals 0.1/0.3/0.5/0.7/0.9 map to the five bands in order; monotone in parity | pass | four-bands | FAIL — `PLANT four-bands LIVE (1 FAIL)` |
| WEIGHTS-7 | E-10 60-second example: o=1.0, r=0.67 → final 0.9175, total_success | pass | none | — |
| CONTROLS-8 | title controls exactly New Campaign/Continue/Settings/Quit; briefing exactly Accept/Refuse | pass | none | — |
| CAMP-9 | two started campaigns listed with chapter/last_band; Resume reaches briefing | pass | none | — |
| JSON-10 | qa_state() round-trips JSON with every key; qa_plant('nope') false; every PLANTS id true | pass | none | — |

Clean: `scripts/mockup_verify.sh menus` → `VERIFY OK`, exit 0. Each plant run individually via `scripts/mockup_verify.sh menus --plant <id>` → `PLANT <id> LIVE (N FAIL)`, exit 0 (the wrapper's own success), inner `godot` exit 1. All six plants confirmed live.

## Xvfb oracles

Clean run: `scripts/mockup_qa.sh run menus scenes/mockups/menus/qa/smoke.json <scratch>/clean1 --res 1280x720`. `errors.txt` count 0, `exit.txt` 0, no `UNIFORM` line (after the background-fill fix — see report), `_qa.adapter` = `llvmpipe (LLVM 21.1.8, 256 bits)`, `_qa.method` = `gl_compatibility`. Two clean runs (`clean1`, `clean2`): every `.json`'s `hash` equal, every screenshot `diff` = `0.000000` at fuzz 5 (well under the 0.005 candidate).

| id | oracle | threshold (candidate) | measured clean | measured planted | plant |
|---|---|---|---|---|---|
| ERR-0 | `errors.txt` count, `exit.txt`, no `UNIFORM` | count 0; exit 0 | count 0, exit 0, no UNIFORM (all 6 shots + all 6 plant runs) | same | none |
| GPU-0 | `_qa.adapter` contains `llvmpipe`, `_qa.method == "gl_compatibility"` | exact | `llvmpipe (LLVM 21.1.8, 256 bits)`, `gl_compatibility` | — | none |
| DET-1 pixel | two clean runs: every `.json` hash equal; `diff` on every screenshot | equal; diff < 0.005 | hash equal on all 5 stateful screens; diff 0.000000 on all 6 screenshots | — | none |
| SCREENS-X | consecutive screenshots differ | (revised, see below) clean > 0; flow-skips-setup: setup == briefing | title→setup 0.025909, setup→briefing 0.025544, briefing→resolve 0.020678, resolve→debrief 0.010941, debrief→campaigns 0.008180 | setup vs briefing diff = **0.000000** (identical — the fault) | flow-skips-setup |
| BAND-X | resolve card crop contains the band colour named in state | exact | `resolve.json.resolve.band == "total_success"`; `TOTAL SUCCESS` renders in the theme's total_success green (`Color(0.3,0.9,0.4)`), confirmed by eye in `resolve.png` | not exercised — see HELD below | four-bands |
| SECT-X | briefing screenshot has three heading crops | exact | SITUATION / OBJECTIVE / ASSETS all present, confirmed by eye in `briefing.png` | ASSETS heading and body absent, confirmed by eye in `plant-briefing-two-sections/briefing.png` | briefing-two-sections |

**SCREENS-X revised.** The brief's candidate (diff ≥ 0.05) does not hold: this is a small, mostly-empty dark UI (most of the 1280x720 frame is background at every screen), so even a full content swap only moves 0.8–2.6% of pixels. Every consecutive pair still differs by a clearly non-zero amount (0.008–0.026), and the fault case (`flow-skips-setup`, setup screenshot identical to briefing's) reads as an exact `0.000000` — a >1000x gap from the smallest clean pair. Recommend revising the clean floor down to something like `> 0.005` (still comfortably above DET-1's noise floor) rather than `0.05`.

**BAND-X not exercised by `four-bands` in the smoke script — HELD.** `qa/smoke.json` always resolves at parity 0.9 / hard / seed 11, which scores ≈0.897 — inside `total_success` regardless of whether `four-bands` is active (the plant only collapses the `partial_failure` band, `final < t2 = 0.40`, into `total_failure`; 0.897 never gets close). The deterministic `BANDS-6` check is the real proof this plant is live (see check table). A future smoke script wanting a visual demonstration would need a lower-parity or refuse-then-accept path that lands in `[0.20, 0.40)`.

## Visual questions

Read against `docs/bible/references/E-16/main_menu.png` and the tone section of `docs/bible/game_bible.md`.

| q | question | answer | proving screenshot |
|---|---|---|---|
| Q1 | Does the title keep the reference's shape: serif title over a turning field with one bright core, monospace list left, studio line above, version bottom-right? | **Yes.** Serif "OUROBOROS MANIFOLD", "A WESTOPOLI GAME" studio line above, left-aligned JetBrains Mono list (New Campaign / Continue / Settings greyed / Quit), `v0.1.0-mockup` bottom-right, star field with one bright core off-center right. | `pass1/title.png` |
| Q2 | Does the briefing read as orders from a superior officer (three parts, no haggling) and not as a menu or a stat sheet? | **Yes.** Situation/Objective/Assets, prose throughout, no numeric fields, no dropdowns or sliders — just Accept and Refuse. | `pass1/briefing.png` |
| Q3 | Does setup ask one thing and say the rest comes later? | **Yes.** Three difficulty cards, one line each: "Mission preferences come later. This choice is made once, at the beginning of the history." | `pass1/setup.png` |
| Q4 | Can the band card be read in five seconds: band, outcome line, casualties? | **Yes.** "TOTAL SUCCESS" in green, one outcome sentence, "0 of 12 did not return" — three lines, nothing else until Continue. | `pass1/resolve.png` |
| Q5 | Does the prose have the hub's dry wit somewhere without being cringe? | **Held, see below.** | — |
| Q6 | Any clipped or overlapping text at 720p; any digits leaking into prose? | **No clipping** on any of the 6 screens at 1280x720 or 1920x1080. **No digits** in briefing/debrief prose clean (confirmed by `DIGITS-5` and by eye); digits **do** leak under the `digits-in-prose` plant ("90 percent parity"), as intended. | `pass1/*.png` (clean); `plant-digits-in-prose/briefing.png` (planted) |

**HELD: Q5.** The fixture prose ("expect the cost to fall on the wall garrison, not the clock") and the hard-difficulty card ("you just cannot afford to stumble") lean dry and matter-of-fact, which is in the right register, but neither is a clear joke or a wink — a Sonnet implementor chat is not well placed to self-judge "does this land as funny" per the caveman/tone rule (a design call, not a QA measurement). Candidates for Westley: (a) this register (terse, dry, understated) already reads as the hub's voice and needs no punchline; (b) one line of the fixture prose should carry a sharper, more specific joke (e.g. in `assets_note` or a difficulty card); (c) tone belongs entirely in the fixture-writing pass, not the mockup's plumbing, and should wait for real narrative-fragment authoring.

## Timings

`timing_ms.swap` (root's `_show_screen`, C++ `Time.get_ticks_usec` around the visibility toggle + `refresh()` call): 0.017–0.93 ms across all 6 screens — screen swap itself is effectively free; all of it is Godot's own per-frame draw cost, not app logic.

`fps_ms` (`Performance.TIME_PROCESS`, one sample per screenshot) under llvmpipe, this machine currently running many concurrent sibling mockup builds:

| resolution | min | max |
|---|---|---|
| 1280x720 | 20.8 ms (~48 fps) | 56.2 ms (~18 fps) |
| 1920x1080 | 28.4 ms (~35 fps) | 116.1 ms (~8.6 fps) |

This is a flat-shaded 2D scene (`Control._draw`, `Label`, no 3D), so the per-frame cost is almost entirely draw-call and font-rasterization overhead, not fill rate — the wide spread above is contention from other agents' concurrent Godot/Xvfb processes on this shared machine (load average 12–22 on 16 cores while these numbers were taken), not this scene's own cost. Retested in isolation this should sit near the low end throughout.

## Harness-level finding (fixed upstream, not in this mockup's files)

Every multi-screenshot Xvfb run hung indefinitely (reproduced identically on the untouched `landscape` mockup, at every system load level tried, with both `--grab engine` and `--grab external`) until two upstream harness fixes landed on `main` mid-session: `a98c47f` (Xvfb screensaver blanking) and the real cause, `b65afa8` (`qa_boot.gd` now frees every autoload before instantiating the mockup scene — previously `SimBridge`'s dead sim process routed `SceneRouter` to an error screen that faded to black and freed the mockup out from under the QA driver). Merged into this branch via `git merge --no-edit main` at the coordinator's direction; `scenes/mockups/_shared/**` was not edited by this chat. See the finishing report for the full isolation trail.
