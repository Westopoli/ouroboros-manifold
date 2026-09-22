# HANDOFF BRIEF — P7 chronicle mockup, pass 2: the scroll over the real galaxy view

Self-contained. Continues `scenes/mockups/chronicle/` (pass 1 plus the review fixes merged 2026-09-22). Read `docs/northstar/research/mockups/chronicle/README.md` ("Mockup review 1") and `docs/northstar/plans/briefs/2026-09-22-p1-galaxy-mockup-pass2.md` first. This brief is handed to the same doer that built galaxy pass 2, after that pass is merged; it depends on it.

- If you are an Opus or Fable chat: plan and review, Sonnet sub-agents build. If you are a Sonnet chat: do the work yourself, spawn no sub-agents.

## What Westley reported, verbatim

"chronicle mockup should really just be the chronicle overlaid on top of the galaxy view (just like in the other version of the game), so the galaxy behind the chronicle is wrong, similar problem to the world view. Really both of these prototypes could be the same agent, they're closely related."

## The change

Drop `mini_galaxy.gd`. The chronicle's map is the galaxy mockup's pass-2 view: load `res://scenes/mockups/galaxy/galaxy_gen.gd`, `galaxy_view.gd` (with its adapter, shells, filaments, ambient rig) and `orbit_camera.gd` from the chronicle scene (the one permitted cross-mockup dependency, by Westley's decision; the chronicle README says so). The scroll panel slides in over it and resizes the map to 62 percent exactly as the legacy `time_jump_sequencer.gd` did; the ownership keyframes drive `set_owner` on the galaxy view (the same recolour plus flash the galaxy's replay uses); the orbit camera auto-orbits during narration and any player input overrides it (R-107-02). The fixture's `galaxy` block goes away: the chronicle's seed selects the galaxy seed, and the fixture's systems are named by galaxy id, so entries mention systems that exist in the generated galaxy (regenerate the two fixtures' mentions against seeds 11 and 12 and keep the prose).

Keep everything the chronicle already proves (entry order, word limits, print cadence, pause and expand, morph timing, the counter, Skip and Proceed). The interactive launch runs on its own (the narration starts after two seconds) as it already does.

## Verification

- Every existing chronicle check green; add: the galaxy view under the scroll is the galaxy mockup's class (not `mini_galaxy`), `owners` after a keyframe match the galaxy view's instance colours, and the map width fraction is 0.62 during narration.
- `qa/smoke.json` unchanged in shape; the 1920x1080 batch re-shot into `pass2/` (keep `pass1/`), plus a first-look run per `scenes/mockups/_shared/README.md` ("First look") if that section exists by then.
- README: "Design as built" rewritten (the dependency on the galaxy mockup stated in one line), the review-2 fixes paragraph, and the remaining rule question (R-069-01 versus S-069's end state).
