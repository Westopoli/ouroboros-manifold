# R5 round 1, fix 1: less text on the pictures. Build to green.

Role: Engineer (Sonnet 5.5), builder. Never edit a test; a test you believe wrong is reported. Spawn nothing. Think tersely. Report once, under 25 lines: commits, files, green summary per worktree, before/after counts of the other test files, anything you believe wrong.

## Tests

`tests/test_mockup_shot_quiet.gd` in `~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`, red 17 pass / 4 fail) and in `~/Projects/om-wt/r5-pass5` (branch `wip/r5-pass5-shots`, red 14 pass / 6 fail). Run `scripts/run_godot_tests.sh tests/test_mockup_shot_quiet.gd` (about 50 s). Read the test and the brief `2026-11-08-r5-round1-text-tests.md` first. Other test files must keep their counts (`test_mockup_obey.gd` 304/6, `test_mockup_obey_assault.gd` 449/5, `test_mockup_landscape_water_views.gd` 77/0 in obey; water views 77/0 in pass 5); run them before and after.

## Build (rulings by the Architect, 2026-11-08)

1. Obey: `ObeyLayer.set_quiet(on: bool)`. Quiet hides the overlay panel, the legend, every `draw_string` label of `obey_overlay.gd` (pad names, choke text, vantage, entry arrow label; the shapes stay), and the landscape HUD's controls; it shows one `Label` bottom-left, text `seed N  reachable P%` plus ` FAIL` when `res.report.pass` is false, font size 14 px, box at most 28 px tall and 420 px wide, 24 px from the corner at most. `P` is `p4.metrics.walk[str(limit)].reach_pct` at the HUD's current limit, rounded to an integer. Key `V` toggles quiet (quiet on shows the line only; quiet off shows the full panel; the old "overlay visible" meaning of `V` is folded into this). `--shot` calls `set_quiet(true)` before the first capture.
2. Pass 5: `HUD.set_quiet(on: bool)` with the same line and the same hiding (pass 5 buttons and labels, pass 4 UI, the HUD's own labels and sliders); ` FAIL` when pass 5's own check reports a failure (its equal-distance or route check result, whichever `pass5_layout`/`pass5_places` expose; if none is exposed, omit FAIL and say so in the report). The QA `screenshot` step and `--screenshot-batch` call `set_quiet(true)` before capturing; the existing manual screenshot key keeps whatever state is on. Add a key to toggle it (pick an unused one, print it in the HUD's key list).
3. Constants named (`SHOT_FONT_PX` 14, `SHOT_BOX_H` 28, `SHOT_BOX_W` 420, `SHOT_MARGIN` 24) with a comment naming the brief.

Constraints: minimal diff; no refactor of the HUD; add only changed files (`git add <paths>`), never `-a`/`-A` (Godot churn in `.import`/`.uid` stays unstaged). Build in `r5-obey` first for the overlay, in `r5-pass5` for the HUD; the shared `hud.gd` change is made once and cherry-picked to the other worktree. Commit subject `R5 round 1: quiet shot line (seed and reachable only); V toggles the panel`, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. No pictures.
