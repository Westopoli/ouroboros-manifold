# Objectives mockup (P3)

This mockup shows P3 of the prototype ladder (`docs/northstar/PLAN.md:164`): given an archetype, the primary objective is placed at the right kind of place on a generated map, marked and named on the ground and in the HUD, its progress is legible, and the placement is satisfiable.

## Run it

```
~/.local/bin/godot --scene scenes/mockups/objectives/objectives_mockup.tscn
```

Hotkeys: archetype dropdown and seed spinbox in the top-left panel; **R** regenerates with the current dropdown/spinbox values; **T** advances 50 toy ticks; **P** toggles autoplay at 20 ticks/second until the mission completes. Mouse wheel zooms (height 800-20,000wu), WASD pans, edge-scroll pans. The 200x200 minimap bottom-right shows every fixture node as a dot, the player spawn as a blue square, and the current objective as a kind-specific glyph.

A wrapper run without `--qa-script` leaves the `QADriver` inert — confirmed: `qa_driver.gd`'s `_ready()` returns immediately when `--qa-script` is absent from `OS.get_cmdline_user_args()`, so no `_run.json` or any other QA output file is ever written on Westley's own interactive launch.

## Design as built

**places.gd** loads one of the three seeded fixture dumps (`fixtures/nodes_seed{11,12,13}.json`, produced once by `tools/dump_nodes.gd` from the landscape mockup's `FieldMap.generate()`, never at runtime) and exposes `nodes_of`/`candidates`/`player_spawn`/`enemy_spawn`/`route_length`/`route_path`. Routing is a real `AStarGrid2D` over a 100wu grid; cells within 150wu of any `hazard_anchor` are always blocked, cells within 1200wu have a 5% seeded chance of being blocked (deterministic per-cell, not draw-order-dependent), giving the "not always a straight line" behaviour the brief asked for without making the map impassable.

**mission_gen.gd** carries the ten-archetype table from R-073-01 (the "or" row, Reconquest, takes its first-listed kind per the brief's instruction). For each kind it picks a candidate node (seeded, cycling through alternates on failure and recording what it skipped), checks satisfiability (inside canvas, >=2000wu from the player spawn, route time within the R-076-01 time budget), and builds the toy-tick state (target/enemy scatter, escort route with a small seeded cosmetic jitter). `tick()` advances progress per R-075-02 to R-075-06, including the hold_zone pause window (200-300) and completion at 1.0 (R-075-07).

**markers.gd** draws the beam/label/ring/glyph/scatter/route per kind, sharing a small static mesh+material cache across regenerates (kept from an early debugging pass that turned out not to be the cause of a real stall — see "Questions for Westley"). **objectives_mockup.gd** additionally draws every fixture node as a small flat box (this was missing through most of the build — `places.gd`'s own spec said to draw the node vocabulary, and nothing did until a late fix, commit `24384ec`), and a faction-blue block at the player spawn.

**camera_rig.gd** is a fixed top-down rig (pitch 90 degrees, R-103-03) copied down from the landscape mockup's pan/edge-scroll/zoom, with the ground-follow and band-pitch logic stripped since this mockup has no terrain. The root auto-pans the camera to the current mission's position on every regenerate, keeping whatever height was last set — this was a real fix partway through the build; without it, switching archetypes left the camera looking at empty ground.

**hud.gd** is the archetype dropdown, seed spinbox, Regenerate/Tick+50/Play controls, the objective line with a text-art progress bar, a satisfiable readout (route length, time limit, skipped-candidate list), and the minimap.

## Bugs found and fixed along the way

Three real bugs surfaced only under the Xvfb/llvmpipe QA path, not headless:

1. **Camera never marked `current`.** The lone `Camera3D` node never had `current = true` set; nothing in the 3D view rendered at all until this was added.
2. **`places.gd`'s node-drawing spec was never implemented.** `map_zoom.png` was a bare plane with only the mission marker until commit `24384ec` added the missing box+label per node.
3. **`Label3D` text does not render in this Xvfb/Compatibility/llvmpipe test environment**, for both the marker name and the place-node type labels, despite the underlying data being correct (`qa_state()`/NAME-7 confirm `label.text` is set). Tried and ruled out within this session's budget: `fixed_size` true/false, default vs custom `pixel_size`, billboard on/off with a manual top-down rotation instead, font_size 32-64, two different font files. Left as a flagged, unresolved finding — see below.

Two harness-level bugs (not this mockup's code) were chased and fixed upstream mid-session, both merged from `main`: Xvfb's screensaver blanking the window after 600s of a slow run (`a98c47f`), and `SimBridge`'s dead-pid error route fading the screen and freeing the mockup mid-script even under `qa_boot.gd`'s script-mode boot (`b65afa8`). A third, still-unresolved background-gradient artifact (see checklist) was diagnosed at length — ground plane, sky colour, fog, camera far-clip, and directional shadow were each tested independently and ruled out — without finding the cause; it does not obscure any functional element.

## What the report answers

1. **Does each kind read at a glance; which glyph or ring did not work?** 4 of 5 kinds in the smoke batch are visually distinct at a glance (hold_zone ring+cube, destroy_targets diamond+scatter, escort cone+route, eliminate cross+ring+scatter). The 5th, `multi_front_defense`, is pixel-identical to `defensive_stand` — both are hold_zone at the same objective-node location, a direct consequence of R-073-01's table (see point 6 below), not a glyph design failure.
2. **Is the landscape's nine-node vocabulary enough, or did a kind need information the node list doesn't carry?** Enough, with one gap noted for E-17's owner: the landscape generator (`field_map.gd`) never actually emits a `transit` node in any of the three dumped fixtures — only 8 of the advertised 9 types appear. None of the five Round-1 kinds needed `transit`, so this didn't block anything here, but it means the "one generator, nine node types" claim is currently aspirational for that one type.
3. **How often was a node skipped as unsatisfiable, and why?** Zero times across 30 (10 archetypes x 3 fixtures) checks in the clean pass — the candidate positions this landscape generator produces are all comfortably within the time/distance budget. The skip path only fires under the synthetic ROUTE-6 test fixture and the fault-injected plants.
4. **Frame time under llvmpipe at 720p; generation time.** `timing_ms.gen` 22.6-36ms (budget 200ms). `fps_ms` 198-310ms/frame — but this session ran under severe concurrent-session contention (up to 8 other `godot` processes, system swap 7+/8GB in use); a quiet machine should be well under the brief's ~1s/frame worst-case estimate.
5. **Under-defined points** — see the next section.

## Questions for Westley

Two visual bugs need your own eyes on your RTX 3060/Forward+ seat before I'd trust any conclusion drawn from the Xvfb captures alone:

- **Label3D text invisible under Xvfb/Compatibility/llvmpipe.** Every in-world name — the objective's own label and every place-node's type label — renders with correct data (confirmed programmatically) but zero visible glyphs in every screenshot this session took, across every configuration tried. Does it show on your machine? If yes, this is purely a headless-test-environment limitation and can be ignored. If no, it's a real bug worth its own investigation (candidates: something about procedurally-created, non-scene-authored `Label3D` nodes; a font/atlas issue specific to this project's `theme/fonts/` set; something about billboard mode at extreme top-down pitch).
- **A soft background gradient** shows behind the 3D scene at every camera height in every Xvfb capture (see `pass1/map_zoom.png`). I ruled out, one at a time: the ground plane (removed it entirely — no change), its size, its shading mode, the sky's colours (swapped to solid magenta — no change), fog (disabled — no change), the camera's far clip (40,000 to 150,000 — no change), and the directional light's shadow (disabled — no change). It never obscures the ring/glyphs/route/HUD, and I didn't find the actual cause within this session's budget. My best guess is an Xvfb/llvmpipe artifact tied to this session's heavy concurrent load (swap was 7+/8GB used most of the session) rather than anything in the scene, but I can't prove that without a quiet re-run.

Design points I did not decide, each with two or three candidates:

1. **Time-limit scaling for a walkable mockup** (the brief itself flagged this as under-defined). Built: base `B = 350` ticks flat for every archetype (not varied by canvas tier), scaled x20 for the mockup. Candidates: (a) keep it flat as built — simplest reading of the brief's own text; (b) scale `B` by the archetype's `canvas` field via the Q-076-01 band (small=250, medium=350, large=450); (c) ask you for the real per-archetype base minutes once Q-076-01 itself is answered.
2. **Escort route rule.** Built: the real A* path (over the same blocked-cell grid used for satisfiability) drives the actual satisfiability check and the rendered route's *shape*; a small seeded lateral jitter (+-80wu on interior points) is layered on top purely for visual variety and to give `mission_hash` seed-sensitivity, without touching the satisfiability math. Candidates: (a) keep as built; (b) drop the cosmetic jitter, accept the escort archetype is visually seed-invariant like hold_zone (would drop SEED-2 below its 6/10 floor unless something else changes); (c) if the landscape generator ever produces more than one `extraction` node, let seed choose among them instead of jittering.
3. **How secondaries would show.** Round 1 has none (`docs/northstar/mvp/feature_mvps.md`'s E-10 block); nothing was built for this. Candidate for whenever it's needed: reuse `mission_marker.gd`'s own precedent — `SECONDARY_COLOR` (dimmer gray-blue), smaller glyph, no beam.
4. **Marker's look at the far band.** At the map zoom band, the ring/glyph shrink to a handful of pixels but the ring stays the dominant readable shape (confirmed via a direct objective-centred height-12000 shot); the place-node boxes shrink similarly. Whether that's "enough" at 20,000wu (this mockup's max zoom) is a judgment call for you once the label-rendering question above is resolved and names are actually visible to judge legibility against.
5. **Kind coverage for Round 1's ten archetypes.** R-073-01's table only ever produces 4 distinct primary kinds across the 10 archetypes (hold_zone x4, destroy_targets x3, eliminate_force x2, escort_to_extraction x1); `survive_duration` never appears. `mission_gen.gd` fully implements survive_duration's placement and tick logic (it's one of the five kinds R-075 defines), it just has no archetype that selects it in Round 1. Candidates: (a) accept 4-kind visual coverage for Round 1, survive_duration proven only by its own code path (not exercised by any of the ten archetypes) until a later round adds one; (b) treat this as a sign `multi_front_defense` (currently "hold_zone x2", simplified to a single hold_zone for Round 1) was meant to be the survive_duration representative — this would contradict R-073-01's literal table, so not chosen; (c) ask whether Round 1 wants an eleventh, synthetic archetype purely to exercise survive_duration visually.

## Next step

The pass-1 screenshots (1920x1080, 10 shots: five kinds at tactical zoom, map zoom, HUD at 30% and 90% progress, seed 11 and seed 12) are committed under `pass1/`. The mockup awaits your look — especially the two visual bugs above, which need a Forward+ seat to resolve either way.
