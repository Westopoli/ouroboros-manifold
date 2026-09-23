# leaf-01 Q1 -- owner-pointer registry binding, real ABA hazard confirmed

Not blocking. Escalating for record + future leaves (B10-2/3/4, same file).

## finding

Spec architecture: static file-local unit registry, bound to one `om_world*`
owner, rebind-and-clear when `owner != w`. Brief itself flags the risk:
world_factory frees a test's world at teardown, next `om_world_new` can get
same malloc addr.

Confirmed this isn't a rare corner case -- it's 100% reproducible here.
Added temp debug print, ran the two acceptance files: every single
`om_world_new` in the run got the *same* address (glibc tcache LIFO reuse,
same struct size, tight alloc/free loop, nothing else disturbs it). Pure
`owner != w` check never fires across test boundaries in this suite --
every cross-test "rebind" is a false negative.

Concretely: R-081-03 (bastion) leaves a *living* faction-0 unit in the
registry. R-081-04 reuses the same world addr, so its first spawn silently
appends new Vanguards onto that leftover Bastion instead of a clean slate
-- corrupts R-081-04's baseline fight (ttk reduction came out negative).

No in-band signal fixes this generally: `om_world_new` calloc-zeroes the
struct every time (same seed/n_regions in every test here), so content is
byte-identical call to call -- can't fingerprint a "new" world by content
either. True fix needs either a generation/serial field on `om_world`
(header change, out of my scope) or `om_world_free` calling into unit.c
(no hook exists, sibling-owned file).

## what I did instead (proceeding under this, not blocked)

Added a `battle_ticked` flag to the static registry, set by
`om_tactical_run`/`om_tactical_run_until_eliminated`. `om_unit_spawn`/
`om_unit_spawn_for_category` check it: if a battle already got ticked
since the last (re)bind, a new spawn call forces a full reset first (same
wipe `om_tactical_reset` does), regardless of whether `owner == w` by
coincidence or by genuine continuation.

Works because in every B10-1 fenced test, the pattern is always spawn-all
-> tick -> query, and any *second* scenario in the same test explicitly
calls `om_tactical_reset` first (which clears the flag) -- so this leaf's
tests never spawn reinforcements into an already-ticked, not-yet-reset
battle. Verified: 10/10 in the two acceptance files, adapter green, both
lints green, stable across repeat runs.

## risk for later increments

If a future B10 increment (reinforcements mid-fight, something calling
`om_tactical_run` more than once per battle with new spawns in between)
needs "add units to a battle already ticked, same world, no reset," this
flag will wrongly nuke that battle. Whoever picks up B10-2/3/4 on this
file should know this landmine exists and either lift the flag check or
get the real header-level generation fix Westley may want to approve.
