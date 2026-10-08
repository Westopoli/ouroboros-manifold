// Visible game programme, wave 4: lane C (3D ground) in two workflows by args.part: 'a' (C2, C2b, C3, C4 from K0 fixtures; C5 the view host) or 'b' (C6, C7, C8, C10 x6, C9 plays).
// Part a's C2..C4 need only K0 (heights fixture); C5 needs lane A part b landed (A12) and F5 landed. Part b needs part a landed.
// Launch: Workflow({scriptPath, args: {part: 'a', ctests: 'push/vg-c-tests'}}).
export const meta = {
  name: 'vg-wave4-laneC',
  description: 'Visible game lane C (3D ground): mesh, bands, camera rig, picking, the SubViewport host, units in 3D, slopes, LOD, re-projection of lane A, plays',
  phases: [{ title: 'Build' }, { title: 'Clerk' }, { title: 'Plays' }],
}
const SPEC = 'docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4 (lane C, section 2, section 7 liberties: flyer altitude layer floor + 150 wu with a shadow disc; ground colour band ramp + steep tint + walkable), docs/northstar/plans/preflight_2026-10-07/4-land-3d.md (the mockup\'s files and lines: ground.gd, camera_rig.gd, pass4_ui.gd _pick at :380, field_map.gd), the mockup on origin/push/proto-land-iter (scenes/mockups/landscape/, read with git show; never edited), stage 3\'s terrain_layer.gd on main, the bible E-18 S-236, E-01 S-001/S-004/S-010, E-13 S-207, and the register rows Q-S3-02 (the layers mockup\'s two-circle transition cue: one circle on the moving unit, one at the Y of the target layer) and Q-009-02 (the vision tube makes hidden units visible; no occlusion mark)'
const RULES = `Rules: model Sonnet 5.5; never spawn sub-agents; think tersely; your last message is the report, no interim notices. Worktree ONLY by absolute path: git -C ~/Projects/ouroboros-manifold fetch -q && git -C ~/Projects/ouroboros-manifold worktree add -b <branch> ~/Projects/om-push/wt/<suffix> origin/main. Never touch ~/Projects/ouroboros-manifold itself. No stash/rebase/amend/force; never push to main. make && make pipe/ouroboros_pipe for desktop runs. Godot ~/.local/bin/godot.real (every Godot or xvfb run wrapped in timeout 1800: two wave-1 runs hung for 8 h); tests via scripts/run_godot_tests.sh <file>; never stage *.import or *.uid; long runs inside systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=0 -- nice -n 10 <cmd>; gates detached, 5-min polls. Builders never edit tests; existing tests re-pinned only through the rulebook (rows 3, 5, 12, 31 for the 3D camera: the 2D zoom semantics hold on the map band and the rig publishes camera {x,y} and scale as the map band's equivalents) with ledger rows TD-VG-C-<n>. New files live under scenes/ground3d/. Stop and report on a file outside your list, a number nobody gave, a frame field the table lacks. Push your branch, write .wt-done. Stop past 120k context.`
const REPORT = { type: 'object', properties: { ok: { type: 'boolean' }, branch: { type: 'string' }, sha: { type: 'string' }, summary: { type: 'string' }, red_ids: { type: 'array', items: { type: 'string' } }, stop_reason: { type: 'string' }, parked: { type: 'array', items: { type: 'string' } } }, required: ['ok', 'branch', 'sha', 'summary'] }
const CT = (args && args.ctests) || 'push/vg-c-tests'
const PART = (args && args.part) || 'a'
const C = {
  a: [
    { id: 'C2', file: 'scenes/ground3d/ground_mesh.gd', what: 'one MeshInstance3D built from the heights array (cells_w x cells_h, int32 cm, values at cell centres: honour the half-cell offset against the mockup\'s corner grid), quads as two triangles, SurfaceTool normals (mockup ground.gd:8-58)' },
    { id: 'C2b', file: 'scenes/ground3d/ground_bands.gd', what: 'per-vertex colour by band (the walkers mockup\'s ramp), steep tint where walkable is 0, no zones, no water' },
    { id: 'C3', file: 'scenes/ground3d/camera_rig_3d.gd', what: 'the rig from the mockup camera_rig.gd: height-following above the terrain under the pan target smoothed 0.2 s, pan (keys, edge 60 px), wheel zoom 150 to about 1.2x canvas, pitch 50° to 90° by height, bands micro/tactical/map, set_top_down; publishes camera {x,y} and scale (map-band equivalents) for qa_state' },
    { id: 'C4', file: 'scenes/ground3d/projection.gd', what: 'to_screen via Camera3D.unproject_position(Vector3(x, h(x,y), y)) and to_world via the ray-march + bisect pick against the height field (mockup pass4_ui.gd _pick); the bilinear height sampler' },
    { id: 'C5', file: 'scenes/tactical_c/tactical_view.gd (VG-VIEW link; after A12 and F5)', what: 'the view hosts a SubViewport with Ground3D (C2, C2b, C3, C4) under the 2D shell; _to_screen/_to_world delegate to projection.gd in a ground era; units_px stays screen pixels; qa_state gains ground3d (camera height, band, mesh stats) and objects_px; terrain_layer.gd demoted to the map band' },
  ],
  b: [
    { id: 'C6', file: 'scenes/ground3d/units_3d.gd', what: 'units positioned in 3D: walkers at the ground height, flyers at their layer floor + 150 wu with a ground shadow disc; lane A\'s shapes projected (unit_visuals untouched)' },
    { id: 'C7', file: 'scenes/ground3d/slopes_view.gd', what: 'slope bands drawn as ground joining layers with the midline (R-001-06, R-004-06), the two-circle transition cue for a unit changing layer (Q-S3-02: one circle on the unit, one at the target layer\'s Y), blocked-layer view' },
    { id: 'C8', file: 'scenes/ground3d/ground_lod.gd', what: 'mesh chunking with distance LOD and a no-pop test (R-236-01: continuous detail from one unit to the map view)' },
    { id: 'C10a', file: 'scenes/tactical_c/fog_layer.gd (handoff A→C)', what: 'fog discs re-projected onto the ground in a ground era (perspective radii re-derived)' },
    { id: 'C10b', file: 'scenes/tactical_c/map_layer.gd (handoff)', what: 'cover and obstacles re-projected' },
    { id: 'C10c', file: 'scenes/tactical_c/objective_markers.gd (handoff)', what: 'beacons and rings on the ground' },
    { id: 'C10d', file: 'scenes/tactical_c/fx/shots.gd (handoff)', what: 'shots between projected positions' },
    { id: 'C10e', file: 'scenes/tactical_c/fx/deaths.gd (handoff)', what: 'wrecks on the ground' },
    { id: 'C10f', file: 'scenes/tactical_c/layer_view.gd (handoff)', what: 'layer rings at their layer heights' },
  ],
}

phase('Build')
const pieces = C[PART]
const first = pieces.filter(p => p.id !== 'C5')
const builds = await parallel(first.map(p => () => agent(`${RULES}\nRole: Doer for lane C piece ${p.id} of ${SPEC}. Branch push/vg-${p.id.toLowerCase()}, suffix vg-${p.id.toLowerCase()}; merge origin/${CT} (lane C's tests, never edited)${PART === 'b' ? '; part a is on main' : ''}. Edit ONLY ${p.file}. Build: ${p.what}. Done when tests/test_vg_c_${p.id.toLowerCase()}.gd is green${PART === 'b' ? ' and the lane A tests of the touched file stay green' : ''}. Report ok, branch, sha, summary, red_ids, parked.`, { label: `build:${p.id}`, phase: 'Build', schema: REPORT, agentType: 'doer', model: 'sonnet' })))
let c5 = null
if (PART === 'a') {
  const ok = builds.filter(Boolean).filter(r => r.ok)
  if (ok.length === first.length) c5 = await agent(`${RULES}\nRole: Doer for lane C piece C5 (the VG-VIEW link) of ${SPEC}. Branch push/vg-c5, suffix vg-c5; merge ${ok.map(r => 'origin/' + r.branch).join(' ')} and origin/${CT}. Edit ONLY scenes/tactical_c/tactical_view.gd (and tests re-pinned under rulebook rows 3/5/12/31 with ledger rows). Build: ${pieces.find(p => p.id === 'C5').what}. Done when tests/test_vg_c_c5.gd green, tests/test_tactical_view.gd and test_tactical_camera.gd green (re-pinned where the rulebook allows), tests/test_qa_state_scenes.gd green, the desktop flow spine and tests/qa/desktop/test_ground_era.py green under xvfb. Report ok, branch, sha, summary, red_ids, parked.`, { label: 'build:C5', phase: 'Build', schema: REPORT, agentType: 'doer', model: 'sonnet' })
}
const green = [...builds, c5].filter(Boolean).filter(r => r.ok)
log(`lane C part ${PART}: ${green.length} green`)

phase('Clerk')
const clerk = await agent(`${RULES}\nRole: landing clerk (Engineer) for lane C part ${PART}. Branch push/vg-c${PART}-land, suffix vg-c${PART}-land, from origin/main; merge ${green.map(r => 'origin/' + r.branch).join(', ')}, then origin/main. VG-C (section 6) owns scenes/ground3d/**, terrain.c, era_config.gd and, for part b, the six handed-off lane A files (edit VG-A's row to hand them over and back after landing); add the new tests. Park files off the candidate, listed. Suites: tests/test_vg_c_*.gd, tests/test_tactical_*.gd, tests/test_qa_state_scenes.gd, the desktop flow spine, test_ground_era.py, test_tactical_play.py (xvfb). Gate: flock -w 14400 ~/Projects/om-push/gate.lock env TMPDIR=~/Projects/om-push/tmp-<suffix> MERGE_GATE_SUITE_TIMEOUT=2400 MERGE_GATE_PLAYTHROUGH_TIMEOUT=2400 MERGE_GATE_PIECES=<worktree>/docs/northstar/plans/push/pieces.toml scripts/specfactory/merge_gate.sh <worktree> origin/main VG-C,${PART === 'a' ? 'VG-VIEW,' : 'VG-A,'}PP-ledger,C5,C8,TERRAIN-1,TERRAIN-3,<what the footprint names>, detached, 5-min polls. If no REJECT: push the branch then git push origin HEAD:main (authorised; go line Q-PROG-01). Else branch only. Write .wt-done. Report ok, branch, sha, summary, red_ids, parked.`, { label: `clerk:C${PART}`, phase: 'Clerk', schema: REPORT, agentType: 'engineer', model: 'sonnet' })

phase('Plays')
let plays = null
if (clerk && clerk.ok && PART === 'b') plays = await agent(`${RULES}\nRole: story-play runner and reviewer (Engineer). Detached worktree of origin/main (suffix vg-c-plays). Run tests/qa/desktop/plays/C/*.py and, again, tests/qa/desktop/plays/A/*.py (lane A's plays re-run on the 3D ground to catch regressions) under xvfb at 1920x1080, --era greek_placeholder for the ground plays; shots and state files under docs/northstar/story_reviews/shots/<run id>/. Review each (Read the screenshot and the references under docs/bible/references/E-17, E-18, E-01, E-13): yes/no/unclear with evidence against the story words and rules; rows into docs/northstar/story_reviews/C.md and new rows in A.md marked "re-run after C". Commit on push/vg-c-reviews, push. Report ok, branch, sha, summary (verdicts; any lane A story that regressed).`, { label: 'plays:C', phase: 'Plays', schema: REPORT, agentType: 'engineer', model: 'sonnet' })
return { builds, c5, clerk, plays }
