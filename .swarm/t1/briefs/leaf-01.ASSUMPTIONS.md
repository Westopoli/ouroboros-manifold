# leaf-01 assumptions (T1, csrc/pipe/om_pipe.c)

Each line: choice, then citation (header line / spec section).

1. First `hello` (before any `set_seed`) uses placeholder `seed:0,
   n_regions:0, features:[]` since no world exists yet. T1.md line 39: "pick
   the simplest correct-looking value and log it as an assumption, not a
   question." Nothing in the fenced test reads these fields on hello.

2. Current tick tracked manually in the server (`g_tick`, set from
   `om_world_step`'s return value, reset to 0 on `set_seed`/fresh
   `om_world_new`). Grepped `csrc/ouroboros_sim.h` for any
   `om_world_tick`/`om_world_get_tick`-shaped getter -- none exists; the only
   tick accessors are `om_world_step` (returns new tick, line 129),
   `om_world_run` (line 130), and the fixture-only setter
   `om_world_set_tick` (line 133, no matching getter). T1.md lines 73-76
   flags this as an open call ("check for an om_world_tick-shaped accessor
   before assuming you must track it yourself") -- confirmed none exists.

3. `set_seed` emits no frame at all (silent), per the spec's documented
   deviation from docs/architecture.md. T1.md lines 41-58.

4. `snapshot` cmd and post-`load` both reply with the `{"type":"snapshot",...}`
   frame directly, not a generic `{"type":"ack",...}` first. T1.md's general
   "answer every command except step/run_to/set_seed with ack" (line 143-145)
   is reconciled against its own explicit carve-out for load ("load replies
   with the post-load snapshot, per doc", line 153-155) and the snapshot
   section's own defined response shape (lines 60-68): the richer typed frame
   IS the command's answer for these two, `ack` covers `set_feature`/
   `inject`/`save` only. `quit` gets neither (flush + exit 0, line 155).

5. Attack record's doc/header "band" mismatch: `om_attack_result` (header
   line 384-404) has `mode` (line 389, telegraph/surprise) and `outcome`
   (line 390, breakthrough/contested/repelled) -- no `band` member. Per
   T1.md's own steer (lines 111-115: "outcome is the closer semantic match"),
   emitted JSON key `"outcome"` sourced from the struct's `outcome` field.
   `mode` is not emitted (not in T1.md's listed attack field set).

6. `om_tick_admin_rolls` -> `revolts`: filtered to `triggered == 1` entries
   only, dropping every non-triggered roll. Header `om_admin_roll.triggered`
   field, line 460. T1.md lines 119-121.

7. `om_tick_events` -> `events`: emitted `tick, region, template, chain,
   source, delta[4], creates_faction`; left out `draw` and `n_spawned` (T1.md
   lines 106-109 explicitly calls these two optional / not in the doc's
   shape -- chose to leave them out, keeping the delta minimal and matching
   docs/architecture.md's documented shape rather than adding fields no
   consumer has asked for). Header `om_fired_event`, lines 607-617.

8. `om_region_neighbors` (header line 740) is declared but not implemented in
   any `csrc/*.c` file and is absent from `libouroboros.so`'s exported
   symbols (`nm -D` confirmed) -- linking against it fails. Worked around by
   building the snapshot's `edges` array with an O(N^2) sweep over
   `om_region_edge(w, i, j, &t)` for all `i < j < g_n_regions` instead (the
   exact fallback the header's own comment at line 738 names).
   `om_region_edge` is implemented (`csrc/faction.c:26`) and exported.
   Escalated: `.swarm/t1/questions/leaf-01-Q1.md`. `unanswered: true`.

9. Collision record's JSON key for `faction[OM_MAX_COLLIDERS]` is
   `"factions"` (plural, array), matching T1.md's own phrasing
   ("faction[0..n_colliders)->factions", line 117-118). Header
   `om_collision`, lines 408-422.

10. Faction `stance` array (both in `snapshot` and internally when deciding
    who to iterate) built as `om_faction_stance(id, k)` for `k` in ascending
    id order `0..count-1`, skipping `k == id` -- directed from `id` toward
    `k`. Header `om_faction_stance(w, from, toward)`, line 267. T1.md lines
    78-80.

11. `load` command: since `om_load_state_read(w, buffer, length)` (header
    line 1294) takes an existing `om_world*` to load into rather than
    constructing one from the save blob, and no world may exist yet if
    `load` is the first command received, the server lazily creates a
    minimal placeholder world (`om_world_new(1, 0)`) before loading into it
    when `W == NULL`. Not exercised by the fenced test. `unanswered: false`
    (internal implementation choice, no cross-piece wire-format effect).

12. `load`: after a successful load the server cannot recover the reloaded
    world's true tick counter (see assumption 2 -- no getter exists), so
    `g_tick` is left at whatever it was tracking before the load rather than
    guessed at. Not exercised by the fenced test; would read wrong for a
    real cross-process resume-from-save flow until a tick getter exists.
    `unanswered: true` (same root cause as leaf-01-Q1's tick-getter gap, but
    not escalated separately -- covered by assumption 2's citation).

13. `save`: writes directly via `fopen(path, "wb")`; the server does not
    create missing parent directories for `path`. Not exercised by the
    fenced test, out of scope per T1.md (no directory-creation behavior is
    specified anywhere in the spec).

14. Tick-log reader calls (`om_tick_events`, `om_tick_attacks`,
    `om_tick_collisions`, `om_tick_admin_rolls`, `om_pending_telegraphs`) and
    `om_region_edge` sweep results are all defensively clamped to their
    buffer capacity (`if (n > CAP) n = CAP;`) after the call, in case a
    reader's return value means "total available" rather than "count
    written" -- the doc comment above the tick-log readers (header line
    317-321) doesn't specify which, and `om_region_neighbors`'s comment
    (header line 736-737, "may exceed max") shows at least one reader in
    this header family uses the "total available" convention. Buffers sized
    generously (8192 for tick logs, 512/1024 for neighbors/telegraphs) so
    this should never actually truncate at realistic region/faction counts.
