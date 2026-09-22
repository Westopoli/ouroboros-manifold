# Menus mockup — main menu, setup, briefing, debrief

`~/.local/bin/godot --scene scenes/mockups/menus/menus_mockup.tscn` from the repo root. No hotkeys are bound in this mockup (the smoke script's `key R` is a deliberate no-op — nothing in `menus_mockup.gd` or any screen handles keyboard input; the flow is mouse-only). Mouse: click a menu item, a difficulty card, or Accept/Refuse/Continue/Proceed/Resume/Back to move through the flow. Confirmed a `--qa-script`-less launch leaves the QA driver fully inert (no `QA_CALL`/`QA_WARN` output, no `_run.json` written anywhere under `user://`).

## Design as built

Six screens, one state machine (`flow.gd`), one band-math module (`resolve.gd`), fixtures for two missions (seed 11, seed 12). `title` → `setup` (New Campaign) or `campaigns` (Continue); `setup` → `briefing` (Begin, once a difficulty is picked) or `title` (Back); `briefing` → `resolve` (Accept, computes the S-P01 band) or `title` (Refuse — "orders refused; the chapter passes"); `resolve` → `debrief` (Continue, after a 2 s fade); `debrief` → `title` (Proceed); `campaigns` → `briefing` (Resume) or `title` (Back).

Title matches the `E-16/main_menu.png` reference's shape closely: serif "OUROBOROS MANIFOLD" with a per-character breathing pulse, "A WESTOPOLI GAME" studio line, left-aligned monospace list (New Campaign, Continue, Settings greyed "later", Quit), version bottom-right, a seeded star field with one bright core at 70% opacity behind it (`backdrop.gd`, `Control._draw()`, deterministic via accumulated `_process` delta, never wall-clock time). Setup asks one question (difficulty, three cards with one line of consequence prose each) and says mission preferences come later. Briefing renders exactly Situation/Objective/Assets from the fixture, states parity in words ("near parity", "outnumbered by a third") never digits, names the attacker in Situation, and offers only Accept/Refuse. The resolve card fades in the band, one outcome line, and casualties as "n of m did not return" (this screen is exempt from the no-digits rule — only briefing and debrief are R-079-04's scope, and "n of m" is the brief's own spec for this card). Debrief shows the band, objective completion in words, retention in words, and commander fate (killed in action only in the lowest band, survived otherwise) — no digits anywhere here either. Campaigns lists every started campaign with name, chapter, and last band.

`briefing.gd`'s `compose(fixture)` is the single source of truth for section list / attacker-named / has-digits, called by both the root's `qa_state()` and the screen's own render — no duplicate logic to drift apart. All six fault sites are one line each, gated on `QaPlants.is_active(...)`.

Two mid-build fixes worth flagging: the root `Control` had no background fill, so it rendered Godot's default mid-gray clear color instead of the reference's dark navy under the real Compatibility renderer (the headless dummy renderer used by `verify.gd` never surfaces this — it doesn't clear to anything visible). Fixed with a `ColorRect` at `#0A0D12` behind everything. And `Continue`/`Proceed`/`Back` were direct `VBoxContainer` children, which defaults to horizontal-fill, so their hit area (and centered text) stretched the full content width; shrunk to natural size to match Setup/Briefing's buttons.

## Check table

See `qa/checklist.md` for the full table with measured numbers. Summary: all 10 `verify.gd` checks pass clean (`VERIFY OK`) and all 6 plants (`band-random`, `briefing-two-sections`, `difficulty-dropped`, `flow-skips-setup`, `four-bands`, `digits-in-prose`) go `LIVE` under `scripts/mockup_verify.sh menus --plant <id>`. Two clean Xvfb smoke runs match exactly (every state hash equal, every screenshot `diff` 0.000000). All 6 plant Xvfb runs complete with 0 errors and show the expected planted behavior in the state dumps and/or screenshots.

## Visual questions

| q | answer | proof |
|---|---|---|
| Q1 title shape | Yes | `pass1/title.png` |
| Q2 orders not menu | Yes | `pass1/briefing.png` |
| Q3 setup asks one thing | Yes | `pass1/setup.png` |
| Q4 band card in 5s | Yes | `pass1/resolve.png` |
| Q5 dry wit, not cringe | HELD | — |
| Q6 no clipping/digits | Yes clean; digits leak correctly under `digits-in-prose` | `pass1/*`, `plant-digits-in-prose/briefing.png` |

Full detail and the SCREENS-X/BAND-X/SECT-X Xvfb oracle numbers, including one candidate-threshold revision (SCREENS-X's 0.05 floor doesn't fit this mostly-dark UI — measured clean diffs run 0.008–0.026) and one HELD oracle (BAND-X: the smoke script's fixed parity/difficulty/seed never crosses into the band the `four-bands` plant actually breaks — `BANDS-6`'s direct threshold check is what proves that plant live), are in `qa/checklist.md`.

## What the report must answer

1. **Tone.** The flow reads as one voice throughout — dry, terse, present tense, no menu-speak ("Command fields near parity", "the attackers broke first", "you just cannot afford to stumble"). It falls flattest in the setup screen's difficulty-card prose, which reads more like tutorial copy than a line from history. Q5 above is HELD for the same reason — this needs Westley's ear, not a QA check.
2. **Is plain text enough for the briefing, or does it need a visual element?** Plain text reads fine unassisted at both 720p and 1080p — three short paragraphs, no scrolling, no ambiguity about what's being asked. A map thumbnail or force-composition strip would help once a player has seen a dozen briefings and wants to skim past prose to the shape of the fight, not for a first-tester build. Recommend: ship text-only for Round 1, revisit after playtest feedback names this as a real friction point.
3. **Does Refuse need a consequence to feel real?** As built, no — the campaign record's `chapter` does increment internally, but nothing on screen ever surfaces that a refused mission cost anything; the title-screen line is transient and gone on the next action. It reads as a free pass right now. Recommend the campaigns list show a "refused" row distinctly (it currently only distinguishes by `last_band`, which stays whatever it was before the refusal) so the cost is visible somewhere a player would look.
4. **Frame time at 720p.** 20.8–56.2 ms/frame (~18–48 fps) measured; the spread is this shared machine running many concurrent sibling mockup builds during the QA pass (load average 12–22 on a 16-core box), not the scene's own cost — this is a flat-shaded 2D `Control` scene with no 3D draw calls, so it should sit at the low end of that range in isolation. Full numbers including the 1080p batch in `qa/checklist.md`.
5. **Under-defined points.** See "Questions for Westley" below.

## Questions for Westley

- **The resolve formula.** `resolve.gd`'s o/r/roll formula is explicitly a stand-in per the brief (only the 0.75/0.25 weights and the band thresholds are the bible's real numbers). Candidates once real tactical data exists: (a) leave the linear stand-in until a real mission generates it; (b) recalibrate the roll range and difficulty factors against actual playtest outcomes; (c) source `force_size` (currently summed from the fixture's `player_force.units`) from the real mission generator's allocation instead.
- **Casualty display.** Built as "n of m did not return" (raw numbers) on the resolve card, which R-079-04 doesn't restrict (only briefing/debrief). Candidates: (a) keep raw numbers here — they read fast and this card is explicitly the "big reveal" moment; (b) render in words too, for full consistency with the "no raw field numbers" spirit even though the rule doesn't require it; (c) show a proportion or band ("light casualties") instead of exact counts.
- **Refuse's real consequence.** Built exactly as the brief specified — a line and a return to title, "the chapter passes" — with the actual consequence explicitly left undecided. The bible's `R-078-05` (S-078, not S-079) already answers this in the real sim: tension rises 8% of the region's deficit, band = `refusal`. This mockup has no region/tension model to apply that to. Candidates: (a) wire `R-078-05`'s real rule into the mockup once a fixture models tension; (b) keep it inert for the mockup and only pay it off once the real generational loop exists; (c) reconsider whether refusing should cost a chapter at all in the mockup's simplified telling.
- **Continue's behavior.** Built as: Continue always opens the campaigns list. `R-110-03` says Continue resumes at "that boundary" (singular), which reads as "jump straight back in," while `R-111-04` says no fixed limit on campaigns (plural, listable). Candidates: (a) keep the list always, supporting multiple concurrent campaigns; (b) Continue resumes the single most-recent campaign directly when there's only one, list only appears at 2+; (c) Continue always resumes the most recent regardless of count, and the list becomes a separate "campaigns" entry point later.
- **Settings scope for the first tester build.** Still open per `Q-110-01` in the ambiguity register (resolution, fullscreen, two volumes, rebinding, edge scroll are the named candidates). This mockup ships Settings greyed out with no menu behind it, per the brief's "later" instruction.

## Harness note

Every Xvfb run with more than one screenshot hung indefinitely for most of this session — reproduced identically on the untouched `landscape` mockup, so it was never this mockup's own code. Isolated to: any `wait_frames` (or `screenshot`, which itself waits on frames) issued after a `qa_go` call that actually changed screens. Root cause landed on `main` mid-session as two coordinator-directed fixes (`a98c47f`, screensaver; `b65afa8`, the real fix — `qa_boot.gd` now frees every autoload before instantiating the mockup, since `SimBridge`'s immediately-dead sim process was routing `SceneRouter` to an error screen that froze the mockup mid-script). Picked up via `git merge --no-edit main` twice, at the coordinator's direction; `scenes/mockups/_shared/**` was never edited from this branch.

## Next step

Pass-1 screenshots (1920x1080, 6 shots: title, setup, briefing, resolve, debrief, campaigns) are in `pass1/`. The mockup awaits Westley's look.

## Fresh-eyes review (2026-09-22, Sonnet reviewer, screenshots only)

No blockers; ready for Westley's look. Polish list for pass 2: the title's bright core renders as two hard-edged discs rather than a soft glow blending into the field (fake a radial gradient with concentric circles of falling alpha); the Hard difficulty card speaks in the second person while Easy and Medium are impersonal (one voice for all three); the debrief's second line appends "Objective fully achieved" as a status tag rather than a sentence of prose; the menu list is mixed case where the reference is bold capitals and the star field has no swirl or cluster structure (taste calls for Westley, not defects). Q5 (dry wit) leans no: the prose is dry and functional, not witty.
