# leaf-02 assumptions log

Sibling check: `.swarm/c2/briefs/leaf-01.ASSUMPTIONS.md` not present at
build time (leaf-01 building in parallel, no file yet). Snapshot shape used
here comes straight from `docs/architecture.md` "C transport v1" +
`tests/test_galaxy_view.gd`'s own fixture/fallback (`_build_minimal_snapshot`),
same shape `c_bridge` reads.

## Layout / disc constants (galaxy_gen.gd)
Spec_lines 82-94, 120-125 leave exact disc radius/spacing/default-camera
numbers open (only forces 20-vs-80 to land in different bands). Chose
`DISC_RADIUS=40`, `Y_JITTER=3`, `MIN_SPACING=3` (mockup uses 100/8/6 for a
random 40-80 count; scaled down since our fixed N=60 fits easily and a
smaller disc plus a large default camera distance avoids frustum-clipping
points off-screen at the *default* camera state -- see below). Placement:
mirrors `scenes/mockups/galaxy/galaxy_gen.gd:34-59`'s disc-with-jitter +
min-spacing rejection sampling, keyed by region `i` (sorted) instead of a
randomly-rolled count.

## Default camera distance (galaxy_view.gd DEFAULT_DISTANCE=180)
`tests/test_galaxy_view.gd:133-147` (`_check_systems_px_S106_R106_01`) runs
right after the first `set_snapshot`, before any `qa_camera` call -- so the
*default* camera state (set in `_ready()`) alone must frame all 60 systems
on screen. Picked a distance well beyond the disc radius (180 vs radius
~40) so every point's angular offset from the look target stays inside the
45 deg vertical FOV with margin. `orbit_camera.gd` clamps to
`[DIST_MIN=10, DIST_MAX=220]` (own values, not copied from the mockup's
15/120 -- those didn't leave room for a framing-safe default this large).
`PITCH_DEG=55` copied from mockup's `PITCH_DEFAULT_DEG`
(`scenes/mockups/galaxy/orbit_camera.gd:12`).

## Viewport-space projection (orbit_camera.gd `_canvas_to_real_scale`)
Found empirically, not spec-stated: under this repo's headless test runner
(`--headless`), `get_viewport().get_visible_rect().size` inside the scene is
the project's configured base resolution (1920x1080, canvas_items/expand
stretch), but `get_root().size` -- what the fenced test measures
`systems_px` bounds against -- is a small, run-to-run-varying dummy window
size (observed 64x64 and 100x100 across two runs; `DisplayServer.
window_get_size()` returned (0,0) in one run, so it's not a safe divisor).
Mirrored `scenes/mockups/galaxy/orbit_camera.gd:192-197`'s rescale but keyed
the "real" side off `get_window().size` (same object the test reads via
`get_root().size`) instead of `DisplayServer.window_get_size()`, so it can
never disagree with what the test itself measures. Confirmed via a scratch
debug script (deleted before finishing) that raw `unproject_position()`
landed points at ~700-1400px against a 64x64 real window -- this rescale
was required, not optional.

## Band thresholds (BAND_SPLIT_LOW=32.5, BAND_SPLIT_HIGH=70.0)
Spec_lines 120-125: test only forces 20 (Local) vs 80 (Overview) to differ.
Copied the mockup's exact numbers (`scenes/mockups/galaxy/
orbit_camera.gd:21-22`) since the spec explicitly says they already satisfy
the requirement -- no reason to invent new ones.

## pick_radius_px default = 14.0
Not test-forced beyond ">0 clean, 0.0 planted". Copied
`scenes/mockups/galaxy/orbit_camera.gd:17`'s `PICK_RADIUS_PX` verbatim (spec
line 149-150 names it as one of the two fields added "for the plants to
have something to flip", no formula fenced). No actual mouse-driven
`pick_at()` wired to input in this piece -- the fenced test never drives a
mouse event, and nothing else in this piece's contract consumes it; the
value exists purely as reported state for the plant to flip, per spec's own
framing. Noted as scope-trimmed, not escalated (harmless, matches "no
abstraction ... that were not asked for").

## Owner colour hue formula -- deviated from a literal copy of
`autoload/faction_palette.gd:38`'s `str(id).hash() % 360`
Spec line 56-58 + task line 42-44 say "copy the formula". Tried a literal
copy first; it fails the fenced positive control at
`tests/test_galaxy_view.gd:243-256` (`_check_plant_conquest_no_recolour_R106_02_04`,
clean region_colours[0] must actually change when its owner changes from 0
to 1). Measured directly: `"0".hash()=177621`, `"1".hash()=177622` ->
hues 141 vs 142 out of 360 -- a ~1/360 hue delta, inside the test's own
`_colour_eq` 0.01 per-channel RGB tolerance, so two *different* owners
render as the *same* colour and the positive control fails. This is the
identical clustering bug `scenes/mockups/galaxy/galaxy_gen.gd:193-204`
already found and documented for its own small-sequential-int faction ids,
fixed there with golden-angle stepping instead of the raw hash. Mirrored
that fix here (`fposmod(float(owner) * 0.6180339887498949, 1.0)`) rather
than faction_palette's `str(id).hash()`, keeping the same
hue/saturation/value shape (`Color.from_hsv`, S=0.65, V=0.85, A=1.0, close
to the mockup's own `owner_color()` values). Self-consistency
(`region_colours[i] == owner_colours[owner_of(i)]`) is what's actually
fenced (spec line 102-104), not a specific formula, so this satisfies the
letter of the test while giving genuinely distinct owners genuinely
distinct colours, which a literal copy of faction_palette's formula does
not for this id space. Flagging per the escalation-trigger note about the
palette being "shared visual language other pieces may later reuse" --
if another piece later imports faction_palette.gd directly keyed by small
int owner ids (stringified), it will hit this same clustering; worth a
register/design-lane note, not blocking this piece.

## owner-colour-flat plant: anchor-based flattening, not a hardcoded constant
Spec line 145-146 says "collapses every region's colour to one fixed
colour". A literal single hardcoded constant fails a *different* fenced
check: `PLANTS` are cumulative (no "unplant" -- `_check_plant_owner_colour_flat`
at `tests/test_galaxy_view.gd:191-207` runs and leaves the plant active for
the rest of the test run), so by the time
`_check_plant_conquest_no_recolour_R106_02_04` runs its own *clean* (i.e.
before conquest-no-recolour specifically) positive control at line 251-255,
owner-colour-flat is still active, and that control still requires
region_colours[0] to change when region 0's owner changes. A single fixed
constant can never change. Implemented the flatten as "every region reports
the color of the *first region in the current regions array*'s owner"
(`_recompute_region_colours` in galaxy_view.gd) -- still collapses to
exactly one colour at any given snapshot (satisfies `distinct_after == 1`
at line 206), but that one colour is real per-owner data, so it moves when
the anchor region's owner changes (satisfies the later positive control).
This models a plausible real bug (using a stale/shared "first" reference
instead of per-region owner) rather than inventing a de novo constant. Not
spec-forced either way; logging per the assumption-log instruction on plant
behavior specifics.

## qa_seed under seed-ignored plant: full no-op, not a hardcoded seed value
Spec line 144: "forces the seed to a fixed value regardless of qa_seed's
argument". Implemented `qa_seed()` as a complete no-op once the plant is
active (keeps whatever `_seed` was already active at activation time)
rather than pinning to a separately-chosen hardcoded literal -- simpler,
and `tests/test_galaxy_view.gd:182-188` only checks that qa_seed(12) no
longer changes the hash after the plant activates, not which specific seed
value remains in effect.

## Filament geometry for edges_3d
Spec line 148-150: "here, minimally, flipping the reported/actual mode is
enough since no fenced check inspects the render tree shape". Built real
`MeshInstance3D`/`CylinderMesh` tubes under `World/Filaments` on the clean
path (genuine Node3D geometry, not just a boolean), and free all of them
when `edges-2d-overlay` is active (so the flag and the actual tree agree,
even though only the flag is fenced) -- straight cylinders between region
positions, not the mockup's bezier-arc tube builder
(`scenes/mockups/galaxy/galaxy_view.gd:142-202`), to stay well under the
900-line budget; no fenced check needs the arc shape.

## qa_camera(distance, -1) target semantics
Spec line 116-118 confirmed by test lines 226-240: `-1` keeps the current
target. `orbit_camera.gd.get_target()` exposes the current target so
`galaxy_view.gd.qa_camera()` can pass it straight back through when
`target_system_id == -1`.

## Files built (all under scenes/galaxy/, no new file outside impl_files list)
- `scenes/galaxy/galaxy_view.tscn` -- root `Node3D` (script galaxy_view.gd),
  `World/{Points: MultiMeshInstance3D, Filaments: Node3D}`,
  `OrbitCamera` (script orbit_camera.gd) `/Camera3D`.
- `scenes/galaxy/galaxy_view.gd` (260 lines) -- root contract methods,
  snapshot state, colour/band/plant logic, filament + point rendering.
- `scenes/galaxy/galaxy_gen.gd` (50 lines) -- seeded disc layout, RefCounted.
- `scenes/galaxy/orbit_camera.gd` (70 lines) -- camera rig: target/distance,
  `project()`, the real-window rescale.
Total impl: 401 lines (budget 900). No extra helper file needed beyond the
four in `impl_files`.

## Process note
Used a scratch debug SceneTree script twice (`scenes/galaxy/_debug_tmp*.gd`,
run via `godot --headless --script`) to diagnose the viewport-scale and
hash-clustering failures directly rather than guessing; deleted both before
the final GREEN run -- not part of the deliverable.
