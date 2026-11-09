# R5 round 1, fix 1: less text on the pictures. Tests (red) first.

Role: Engineer (Sonnet 5.5), test writer. You write tests only; a different engineer builds. Spawn nothing. Think tersely. Report once, at the end, under 25 lines: files, test names, the command that runs them and its red output's decisive line.

## Westley's words (2026-11-08)

"There's too much text on the screens. I don't even read most of it (only the reachable percentage, and the rest just obscures the actual map. I'd like all that text either scaled down, moved, or removed."

## The rule the tests pin (Architect's reading, DRAFT values his)

In a shot (the `--shot` driver of `obey_layer.gd` and the `--screenshot-batch` / QA-script captures of `hud.gd`), and whenever the overlay is in "quiet" state, the only text drawn is one line in the bottom-left corner: `seed N  reachable P%` (plus ` FAIL` when the prototype's own check fails), at a font size of DRAFT-shot-font 14 px on a 1920x1080 frame, inside a box no taller than DRAFT-shot-box 28 px and no wider than 420 px. Every other panel, label, legend, button and draft list is hidden. The full panel comes back with the existing key `V` (obey overlay) or the HUD's own toggle; `--shot` leaves it hidden. The reachable percentage is the walk flood's reachable share of land cells from the player's base, the number the walk view already computes (`pass4_terrain.gd`, the HUD's reachable line; find its exact source and name it in the test's comment).

## Where

Two worktrees, both get tests:
- `~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`): `scenes/mockups/landscape/obey_layer.gd` (`_run_shots`, `panel_text`, `_declutter`), `obey_overlay.gd` (`set_panel`, the panel `Label`/`PanelContainer`), `hud.gd`. Existing tests `tests/test_mockup_obey.gd`, `tests/test_mockup_obey_assault.gd` (`extends SceneTree`; run with `scripts/run_godot_tests.sh`, read it for the pattern, it says how a child Godot is launched windowed under Xvfb: `env -u DISPLAY -u WAYLAND_DISPLAY xvfb-run -a ...`).
- `~/Projects/om-wt/r5-pass5` (branch `wip/r5-pass5-shots`): `scenes/mockups/landscape/hud.gd` (`_take_screenshot`, `_run_screenshot_batch`, `--screenshot-batch`), `pass5_ui.gd` (buttons and labels), `pass4_ui.gd`; QA script `scenes/mockups/landscape/qa/r5_pass5.json` and `scripts/mockup_qa.sh`.

## Tests to write

New file in each worktree: `tests/test_mockup_shot_quiet.gd` (`extends SceneTree`, same harness as the existing tests). Name the rule in a comment at the top (this brief's path and Westley's sentence). Assertions:

1. **Quiet state hides everything but the line.** Instantiate the mockup scene headlessly, call the quiet entry point (name it `set_quiet(true)` on the layer/HUD; the builder implements it), then walk the scene tree: every `Control` that draws text (`Label`, `RichTextLabel`, `Button`, `SpinBox`, `OptionButton`, `CheckBox`) is `visible == false` or has empty text, except exactly one `Label` whose text matches the regex `^seed \d+  reachable \d+%( FAIL)?$`.
2. **The line's geometry.** That label's global rect: bottom-left anchor (its `global_position.y + size.y` within 24 px of the viewport height, `global_position.x` within 24 px of 0), height at most 28 px, width at most 420 px, font size 14 (`get_theme_font_size("font_size")` or the override).
3. **The number is the walk view's.** The percentage in the line equals the reachable share the terrain analysis reports (round to the same integer the HUD prints), for seed 1 (obey) and layout 01 seed 11 (pass 5).
4. **`--shot` and the QA capture use quiet.** Launch the child Godot as the existing shot tests do, with `--shot <scratch dir>` (obey) and with the QA script (pass 5: a short script of one `screenshot` step is enough), then prove the frame is quiet by pixels: in the saved PNG, the top-right quarter and the right third of the frame (where the panels sat) have no pixel runs of the panel's background colour (`obey_overlay.gd` `style.bg_color` 0.03/0.04/0.07 at 0.86 alpha, composited; measure the colour of the existing panel from a current picture on main first and assert its absence within a tolerance), and the bottom-left 420x28 box has at least 40 pixels of text colour. Use `Image.load_from_file` in GDScript; no PIL needed.
5. **`V` brings the panel back** (obey only): after `set_quiet(false)` the panel label is visible again and non-empty.
6. **Positive control**: run assertion 1 against the current code with quiet never called and show it fails (the panel is visible), so the test is proven to go red against the old behaviour; keep it as a test that asserts the old state is NOT quiet.

Each assertion names this brief and the Westley sentence it proves. No implementation. Run both files; both must be red for the reasons expected (missing `set_quiet`, panels visible). Commit on each worktree's branch with subject `R5 round 1: red tests for the quiet shot line (less text on pictures)` and the trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Never `git add -A` (Godot `--import` writes `.import`/`.uid` files; add only your test files and their `.uid`).
