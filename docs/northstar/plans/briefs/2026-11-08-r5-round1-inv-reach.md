# R5 round 1, investigation 2: reachable ground, feature scale, and bases in the environment

Role: Engineer (Sonnet 5.5), read-only investigation with measurements. Spawn nothing. Think tersely. Report once, at the end, under 80 lines, as the text of one report section (normal prose, for a human reader). Do not open any PNG as an image; read code and data, run the generator headlessly to measure.

## Westley's words (2026-11-08)

"I think that the landscape engine is too 'large scale', I feel that we need to scale specific hills/points/mountains to be more dense and vary in height. For example, the technical 'width/height' of the map is correct in terms of unit walk-time, however I imagined an environment with more landscape variety per-map. For example, if you look at the walk.png, sometimes significant portions of the map aren't walkable. Like on L03 it even says only 11% of the map is reachable. That's too little. I want to explore options for how to keep the tremendous sense of scale we're getting from the large mountains, while still making the areas reachable, like there's a lot of great mountains that have no way to access their peaks."

"Bases are always 'flat', that's not how I want it to be, bases should be *in* the environment, not be only in valleys. Bases should be able to be on mountain sides, even intense ones."

## Where

Pass 5 worktree `~/Projects/om-wt/r5-pass5` (branch `wip/r5-pass5-shots`): generator `scenes/mockups/landscape/field_map.gd` (noise, relief, bands, `spacing_for`, lakes and rivers after the 2026-11-08 fix), analysis `pass4_terrain.gd` (bands `lo`/`step`, `slope_tan`, walk flood at the 30 or 35 degree limit, ramps, peaks), pads `pass5_layout.gd` (`PAD_WU`, `_level`/stamp functions). Terrain-obeys worktree `~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`): the same landscape files plus `obey_layer.gd` (`_stamp`, `_level_heights`, `base-pad`, `ramp-grade`, `ramp-reach`). Kits: `scenes/mockups/landscape/kits/*.json` (relief, band count, noise settings). Pictures and panels on main under `~/Projects/ouroboros-manifold/docs/northstar/story_reviews/westley/layout_engine/r5-recovery/`. Bible rules that bind: `docs/bible/epics/E-17-map-generation.md` R-189-02 (ground steeper than 35 degrees is impassable), R-189-07 (two routes to every important place), R-192-03 (vantages on real peaks, reachable by a slope; about 30 percent of other peaks may be unreachable), R-186-xx (height bands), E-01 R-001-06/07 (slopes join bands, a walker changes band only by a slope), R-004-07 (1.1x uphill slowing). Read them before writing options.

Scratch scripts only under `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/db98320a-0522-401b-91ae-f1f3583f73a5/scratchpad/`. `godot.real --headless --path <worktree> -s <script>` runs a `SceneTree` script.

## Measure first (one table)

For the five pass 5 pictures (layouts 01, 03, 05, 06, 08 at seed 11, 24,000 wu) and the five terrain-obeys as-is seeds (1 to 5, 16,000 wu): percent of land cells walkable (slope within the limit), percent reachable from the player base, percent water, percent above the walk limit, count of peaks and how many are reachable, mean and max height, and the dominant feature wavelength (the noise's largest octave in wu, from the kit or the code). Where the pictures' own numbers exist (panel text, `_on.json`, HUD lines) quote them and say whether your measurement agrees.

## Then find the causes

1. Why so little is reachable: steepness share versus water share versus cut-off flat ground (flat land the walker cannot reach because a ridge or water rings it). Give the split per map.
2. Where the 30 or 35 degree limit bites: the slope distribution (histogram in 5 degree bins) of land cells.
3. The feature scale: the noise octaves and relief amplitude in wu; what one mountain's footprint is (wu across) versus the canvas; how many distinct hills a 24,000 wu map holds today.
4. How peaks are reached today: the ramp cutter (`ramp-grade`, `ramp-reach`, pass 4 ramps) and why most peaks stay cut off.
5. How bases are placed: every place that levels ground for a pad (file:line), what "flat" means in wu and degrees, and what the pad check (`ring` max slope 35) requires.

## Then options (the part he will read)

Write 3 to 5 options for "keep the sense of scale, make the ground reachable, more hills per map, peaks with a way up", each with: what changes (which constants or which algorithm), a predicted effect on the table's numbers, what it costs (walk time across the map, visual scale), and a one-line risk. Candidates to assess, add your own: (a) more octaves at shorter wavelength with the same total relief (denser hills, same peaks); (b) terrace the slopes into the bible's height bands with slopes between them so every band is walkable and steep faces are short (R-001-06); (c) a ramp pass that guarantees at least one slope to every peak above a size (spiral or switchback, grade under 35); (d) lower the band step so cliffs are shorter and more of the face is under the limit; (e) raise the walk limit (bible says 35, so this is a rule change, flag it). Give each a recommended first draft value.

Then 2 to 3 options for bases in the environment: (a) a base is a footing, not a levelling: the pad request becomes "a connected walkable area of radius r, any slope under the limit, on any band", terraced into 2 to 4 steps when on a hillside; (b) the base keeps a small flat core (say 300 wu) and the rest of its radius is left as the mountain is, with a carved road out; (c) no pad at all, the base is placed where the ground already has a walkable area of the size needed, searched by score. For each: how the objective, resource sites and strongpoints (E-15, at slopes between bands) would follow the same rule, and what the panel's `ring` check becomes.

Close with your one recommendation for the next picture round (which option(s), which drafts), in three lines.
