"""Positive control for OM_BUG_TRIGGERS_READ_LIVE (om_bug_e04 = 208).

Snapshot-versus-live reads (docs/northstar/e2e/E-04.md, "Snapshot-versus-live
reads" and "Order of operations" step 6): "Deltas from due queued events and
fired fresh triggers sum per region, and that combined delta applies once
against the tick-start snapshot" (R-026-07, ALG-33, ALG-36). The matching
watch-for's own wording covers this for the due-queue side ("Sequential
same-tick queue application", R-028-01: "per-region net field change != the
clamped sum of individual deltas applied once against tick-start fields").
This control proves the same requirement for two independent FRESH TRIGGERS
that both cross their own tick-start threshold in the same region on the
same tick.

Direct code trace + empirical measurement (2026-09-22, against
csrc/events.c on branch push/B1-5, both in a throwaway worktree): the
original cross-region-swap fixture this file used to carry could never
observe OM_BUG_TRIGGERS_READ_LIVE, because `should_fire[]` for every
template in a region is fully decided in evt_evaluate_triggers's first pass
(all reads happen before any effect is applied), regardless of the
live/snapshot switch -- confirmed directly: swapping which region holds
which crossing, or making one trigger's effect field overlap another
trigger's threshold field, never changes which templates fire, on the
clean build or with this bug injected. The bug's actual reachable effect
sits downstream of firing entirely, in om_step_events's end-of-tick batch
apply: that block (which would otherwise clamp the whole tick's summed
delta against the tick-start snapshot once) is skipped for this bug --
`push/B1-5`'s events.c fix -- so a touched region is left holding whatever
evt_evaluate_triggers's own inline mutation wrote as each trigger fired,
in template-table order, each clamped separately. Two triggers firing in
the same region on the same tick therefore apply sequentially with an
intermediate clamp instead of once against the snapshot: template A's
effect can clamp the field to its floor, and template B's effect then
adds to that clamped floor value instead of to the true (lower, unclamped)
intermediate the snapshot rule requires.

Fixture: military pinned at 1.0 (deliberately just above its 0.0 floor).
"Population Crisis" (tid 8, POP < 20, effect military -2.0) and
"Diplomatic Incident" (tid 19, TEN > 35, effect military +1.0) both cross
their own tick-start threshold on the same tick, in the same region --
population drops from 25.0 to 15.0, tension rises from 20.0 to 36.0;
neither crossing is caused by the other's effect. A clean build sums both
military deltas (-2.0 + 1.0 = -1.0) against the tick-start snapshot once:
1.0 - 1.0 = 0.0, which does not even reach the 0.0 floor. Measured
directly: clean final military = 0.0. With OM_BUG_TRIGGERS_READ_LIVE
injected, Population Crisis (lower template id, fires first) applies -2.0
inline and clamps to the floor (1.0 - 2.0 = -1.0 -> 0.0), then Diplomatic
Incident applies +1.0 on top of that already-floored value (0.0 + 1.0 =
1.0), since the reconciling batch-apply that would otherwise redo this
against the snapshot is skipped for this bug. Measured directly: injected
final military = 1.0.
"""
from conftest import (
    OMBugE04,
    OMField,
    OMSource,
    OMTier,
    force_draws,
    isolate_events,
    load_launch_events,
    read_events,
    set_owner,
    set_region,
    set_tech_multipliers,
    template_id,
    zero_all_noise,
)


def test_control_triggers_read_live_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load_launch_events(dbg, w)
    zero_all_noise(dbg, w)

    tid_crisis = template_id(dbg, w, "Population Crisis")     # POP < 20, effect military -2.0
    tid_incident = template_id(dbg, w, "Diplomatic Incident")  # TEN > 35, effect military +1.0

    set_region(dbg, w, 0, tier=OMTier.HOME, military=1.0, economy=48.0, tension=20.0, population=25.0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_tech_multipliers(dbg, w, 0, 1.0, 1.0, 1.0)
    force_draws(dbg, w, [1.0] * 50)
    dbg.om_debug_inject(w, OMBugE04.TRIGGERS_READ_LIVE)

    for _ in range(3):
        dbg.om_world_step(w)

    # Tick 4: two independent tick-start crossings in the same region --
    # population falls below 20 (Population Crisis), tension rises above 35
    # (Diplomatic Incident). Neither crossing is caused by the other's effect;
    # both are judged against this tick's own tick-start snapshot.
    set_region(dbg, w, 0, tier=OMTier.HOME, military=1.0, economy=48.0, tension=36.0, population=15.0)
    dbg.om_world_step(w)

    events = read_events(dbg, w)
    fired_ids = {e.template_id for e in events if e.region_idx == 0 and e.source == OMSource.TRIGGER}
    assert tid_crisis in fired_ids and tid_incident in fired_ids, (
        "the forward run did not fire both independent tick-start crossings "
        "-- this control's own setup is broken, not the detector"
    )

    military = dbg.om_region_field(w, 0, OMField.MILITARY)

    # A clean build sums both military deltas (-2.0 + 1.0 = -1.0) against the
    # tick-start snapshot once (1.0 - 1.0 = 0.0, never reaching the floor).
    # OM_BUG_TRIGGERS_READ_LIVE applies Population Crisis's -2.0 inline first
    # (floor-clamped to 0.0), then Diplomatic Incident's +1.0 on top of that
    # already-floored value (0.0 + 1.0 = 1.0), because the batch-apply that
    # would otherwise reconcile the tick's summed delta against the snapshot
    # is skipped for this bug.
    assert military == 1.0, (
        f"OM_BUG_TRIGGERS_READ_LIVE injected but final military == {military!r}, "
        "not the 1.0 the sequential-clamp compounding produces -- the live "
        "trigger-effect detector did not trip"
    )
