# E-07 fixtures fixed: launch library load + id-by-name (push 2026-09-22)

Scope: S-049, S-050, S-051 fixtures only. tests/csim/conftest.py +
tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py +
tests/csim/test_E07_S050_old_loyalties.py +
tests/csim/test_E07_S051_nations_that_never_were.py. No csrc touched.

## Root cause, confirmed

`queue_external(lib, w, 0, 100, ...)` / `101` never queued anything (bad
template id, `om_event_queue_external` returns -1). Real ids on main:
Revolt Entrenched = 5, Admin Breakaway = 25 (row order in
`csrc/events.c`'s `om_events_load_launch`, `docs/bible/epics/E-04...md`
S-030 table). Fixtures never called `om_events_load_launch` either.

## conftest.py

`template_id(lib, w, name)` and `load_launch_events(lib, w)` already exist
(added under E-04 block earlier). No `template_id_by_name` needed, `template_id`
already does it. Added ONE new helper, `load_only_templates(lib, w, *names)`:
pulls named templates off the real launch library and reloads the world with
just those (position becomes the new id, `template_id` still resolves by
name against the smaller set). Needed because loading all 26 real templates
makes the OTHER 25 templates' own ABOVE/BELOW/PROBABILITY thresholds fire on
these fixtures' region values (tension 70, economy 50, etc were picked
before any real template existed) — E-04's own e2e doc says isolate to
"fields, external spawns, noise offsets hard-fixtured" for exactly this
reason. Loading only the one template needed also drops the ALG-34
"regional-revolt roll, once per region, even at p=0" draw entirely (neither
Revolt Entrenched nor Admin Breakaway is PROBABILITY-kind), so no extra
filler draws needed per region.

## Extra bug found and worked around, not fixed (out of scope, csrc)

`om_event_queue_external`'s queue-phase always rolls one probability draw
for the entry, per E-04's Draw order contract, even at probability=1.0 (a
draw that always "passes" since r<=1.0 is always true). Fixtures never
budgeted this draw since the queue never fired before. Fix: one leading
filler draw (0.99, branch-neutral) in every `force_draws` call that follows
a `queue_external`.

## S-049 due_tick off-by-one

`om_world_step` increments tick BEFORE running the tick body, so the first
call brings tick 0 -> 1. Every single-step S-049 test queued `due_tick=2`
and only stepped once — the event stayed queued forever, never resolved
(`len(revolts) == 0` at the len-check, before template ids even mattered).
Fixed: `due_tick=2` -> `1` everywhere a single step follows; the
two-step test (R-049-06) `due_tick=3` -> `2`. S-050/051 compute `due_tick`
from the step's own return value already, so no off-by-one there.

## Per-test table

### S-049 (4/7 real pass, was 0/7)

1. `test_R_049_01_one_draw_sets_success_rate` — old: `100`, due_tick=2,
   draws `[0.50,0.80]`/`[0.50,0.50,0.50]`. New: resolved id,
   due_tick=1, draws `[0.99,0.50,0.80]`/`[0.99,0.50,0.50,0.50]` (filler +
   rate + check [+ confidence]). PASS.
2. `test_R_049_02_no_faction_forms` — same pattern, draws
   `[0.99,0.50,0.10]`. PASS.
3. `test_R_049_03_region_keeps_military_0_40` — same id/tick/filler fix
   applied, still FAILS: real csrc bug, not a fixture bug (below).
4. `test_R_049_04_its_id_breakaway_tick_region` — same pattern, draws
   `[0.99,0.50,0.10,0.50]`. PASS.
5. `test_R_049_05_success_rate_1_0_with` — same pattern, draws
   `[0.99,0.0,0.50]`. Still FAILS: real csrc bug (below), not a fixture bug.
6. `test_R_049_06_nothing_happens_chain_pruned` — id fix applied to
   `queue_external` AND to the test's own hardcoded `p.template_id == 101`
   pruned-record check (same class of bug, now `== template_id(lib, w,
   "Admin Breakaway")`); due_tick 3->2 for the two-step body. Still FAILS:
   real gap, not a fixture bug (below).
7. `test_R_049_07_every_edge_touching_it_becomes` — same pattern, draws
   `[0.99,0.50,0.10,0.50]`. PASS.

### S-050 (3/5 real pass, was 2/5 vacuous)

All five: `100` -> resolved "Revolt Entrenched" id, `load_only_templates`
in place of nothing, one leading filler draw. `due_tick` already computed
from the prior step's return value, no off-by-one.

1. `test_R_050_01_with_probability_0_5_one` — PASS (both sub-cases; was
   vacuously red at 0 revolts, now genuinely resolves the revert/no-revert
   branch).
2. `test_R_050_02_it_never_reverts` — PASS, was already passing (asserted
   absence; now a real revolt does fire and genuinely fails to revert past
   the 21-tick window — no longer vacuous either).
3. `test_R_050_03_it_never_reverts` (B doesn't exist) — old assertion
   `om_region_owner(w,0) != 1` is a false negative: a *new breakaway* can
   land in faction slot 1 by plain first-free-slot allocation once B (slot
   1) is never created, since nothing else ever claims it. That is not a
   reversion, but the numeric check can't tell the difference. Fixed
   assertion to `len(read_reversions(lib, w)) == 0` — same rule ("it never
   reverts"), read off the reversion log instead of a slot id that can
   coincide by accident. PASS, and still trivially true at stub (nothing
   fires, log empty either way) — same rule, tighter proof.
4. `test_R_050_04_region_s_owner_b_held` — id/filler fix applied, still
   FAILS: real csrc bug (below).
5. `test_R_050_05_it_records_original_restored_factions` — same, still
   FAILS: real csrc bug (below).

### S-051 (isolated: 6/6, was 4/6; combined run: 4/6, 2 different rows red — pollution, see below)

Coordinator-flagged fix applied: `test_R_051_01_it_removed_from_registry_every`
advanced 5 ticks from `created_tick=1` (lands tick 5, age 4) while its own
comment says "tick 6 >= 1+5"; changed `range(5)` -> `range(6)`. Same
assertions. Leaf originally couldn't pass this row regardless (own header
comment: ALG-42 pass-1 zero-region removal "not implemented ... pending
[a constant]"); mid-task the leaf pushed a new commit
(`ca02585 feat(B6): ALG-42 ghost age by name`) that implements it — with the
tick fix, this row now passes standalone.

Also fixed the coordinator's originally-flagged `test_R_051_03_nothing_happens`
Case A: `isolate_agents` turns FACTIONS on; over 55 live-decision ticks
faction 0's budget (set to 25.0, meant to stay >= OM_COLONIZE_COST=20.0 for
the whole window) drifts down through live E-05 spending, breaking the
precondition. Root cause is general, not just this one test: EVERY S-049/
050/051 fixture calls `isolate_agents` (leaves FACTIONS on) then wants pure
events+lifecycle isolation. Fixed the general case: added
`lib.om_world_set_feature(w, OMFeature.FACTIONS, 0)` right after every
`isolate_agents(...)` call in all three files (S-049, S-050, S-051) — none
of these tests' assertions depend on live agent decisions, budget is meant
to be exactly what `set_faction` set it to.

**Pollution found, not fixed (real csrc bug, out of scope):** running the
seven E-07 files together, `test_R_051_02` and `test_R_051_03` fail — but
pass standalone (verified: S-051 alone = 6/6). Traced: `om_world_free`
(csrc/region.c) frees the world struct but never tells `csrc/events.c`'s
global `g_evt_slots[]` table (keyed by raw world pointer, `owner == w`) to
release that world's slot. glibc reliably reuses the freed address for the
next `om_world_new` in the same run (confirmed empirically: one address,
`0x...529936` in one run, reused 18 times across 30-odd worlds). The new
world then inherits a *stale* event-template slot from whatever old,
already-freed world last owned that address — real cross-test
contamination, not a fixture defect (fixture can't fix a dangling
pointer-keyed cache in the library). Affects any test file that creates
enough worlds after an events-using test in the same pytest process.
Reported here for the record, not touched — `om_world_free`/`events.c`
are csrc, protected, out of my remit.

## Real csrc bugs found, not fixed (fixtures correct, csrc red on purpose)

1. **Split reads post-effect region values, bible's worked example reads
   pre-effect.** `docs/bible/epics/E-07-civilizational-lifecycle.md` line 24:
   military 40 -> new faction's region keeps 16 (=40*0.40 exact, no event
   delta subtracted first), population 60 -> stays 60 (no -2 population
   effect subtracted either). `lc_resolve_faction_creation`
   (csrc/lifecycle.c) reads `rg->military`/`rg->population` etc AFTER
   `om_step_events` has already written the SAME tick's Revolt Entrenched
   effect delta back to the region (steps 1-2 run before step 6). Given
   input military 50 -> effect -4.0 -> 46 -> split 46*0.40 = 18.4, not the
   rule-faithful 50*0.40 = 20.0. Breaks `test_R_049_03`,
   `test_R_050_04`, `test_R_050_05` (all check the split math directly).
   Fixture numbers (20.0/30.0/40.0/60.0) are the bible-correct ones, left
   unchanged.
2. **`LC_TEMPLATE_ADMIN_BREAKAWAY` hardcoded to 101** (csrc/lifecycle.c,
   `#define LC_TEMPLATE_ADMIN_BREAKAWAY 101`) — the real events.c table id
   for Admin Breakaway is 25. `lc_resolve_faction_creation`'s
   `is_admin = (template_id == LC_TEMPLATE_ADMIN_BREAKAWAY)` is always false
   for a real fire, so a real Admin Breakaway takes the ordinary revolt
   path (rate/check draws, population floor) instead of the admin path
   (rate=1.0, no population check). Breaks `test_R_049_05`
   (population=10.0 deliberately below the 25 floor, meant to prove admin
   bypasses it — instead gets blocked by the floor, no faction forms).
3. **No owner-mismatch pruning for a directly external-queued admin-chain
   terminal step.** `test_R_049_06` queues Admin Breakaway straight via
   `om_event_queue_external` with `source_faction=0`, then changes the
   region's owner to faction 1, expecting the queued fire to be pruned.
   Nothing in `events.c`'s queue resolution compares `source_faction`
   against the region's live owner for an externally-queued entry
   (`cond_kind` is hardcoded `OM_COND_NONE` in
   `om_event_queue_external`) — that comparison only exists (if at all)
   for chain-spawned intermediate steps dispatched through
   `evt_admin_chain_spawn`'s own cond fields, which this test's call
   pattern bypasses entirely by queuing the terminal step directly. Either
   a real gap (owner-mismatch pruning unimplemented for this call shape)
   or the fixture should exercise the chain through actual chain-spawn
   propagation instead of a raw external queue — flagging both readings,
   not picking one.

## Verification 1: red at stub

Main (`csrc/lifecycle.c` stub, `csrc/events.c` real as of `4b2ae50`/
merged concurrently mid-task). All 16 S-049/050/051 tests fail on main with
the fixed fixtures. First failing line, `test_R_049_01_one_draw_sets_success_rate`:

```
tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py:80: AssertionError
assert 0 == 1
 +  where 0 = len([])
```

(`om_tick_revolts` returns nothing — `om_step_lifecycle` is a stub no-op.)

## Verification 2: green on leaf

`git fetch origin push/B6 && git worktree add --detach /tmp/b6fix
origin/push/B6` (leaf moved once mid-task, `84b4b92` -> `ca02585
feat(B6): ALG-42 ghost age by name`; re-fetched and re-checked out
mid-verification, noted above). Ran, then `rm -rf /tmp/b6fix && git
worktree prune`.

Standalone per file (isolated pytest invocation, no cross-file pollution):

| file | before (B6's own report) | after |
|---|---|---|
| S-049 | 0/7 | 4/7 |
| S-050 | 2/5 (vacuous) | 3/5 |
| S-051 | 4/6 | 6/6 |
| S-052 | 0/2 | 0/2 (untouched, not in scope) |
| S-053 | 7/7 | 7/7 (untouched) |
| S-054 | 1/1 | 1/1 (untouched) |
| wiring | 2/2 | 2/2 (untouched) |
| **total** | **16/30** | **23/30** |

Combined single-process run of all seven files together (the pollution bug
above hits S-051 specifically, 2 different rows red than baseline, same
count by coincidence): 21/30 (S-049 4/7, S-050 3/5, S-051 4/6 [`R_051_02`,
`R_051_03` red from pollution, not from the fix], S-052 0/2, S-053 7/7,
S-054 1/1, wiring 2/2).

## Verification 3: E-04 / E-02 on main, with the conftest change

`tests/csim/test_E04_*.py`: 31 passed. `tests/csim/test_E02_*.py`: 72
passed, 4 skipped. Both match the required counts.

## Files touched

- `tests/csim/conftest.py` — added `load_only_templates` helper, nothing
  else.
- `tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py`
- `tests/csim/test_E07_S050_old_loyalties.py`
- `tests/csim/test_E07_S051_nations_that_never_were.py`

No assertion deleted. Two assertions changed shape, not intent:
`test_R_050_03`'s owner-id check -> reversion-log check (false-negative
fix, above); `test_R_049_06`'s hardcoded `101` pruned-id check -> resolved
id (same bug class as the main fix, just inside an assertion instead of a
`queue_external` call).
