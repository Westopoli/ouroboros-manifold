# spec: docs/legacy/test_specs/drift-gate-and-green-check.md::Acceptance criteria::AC-1
"""S-160 -- Drift can be switched off, and off means off.

R-160-01 .. R-160-04. sim.c ignored OM_FEAT_DRIFT entirely (card 202b2 /
the 2026-09-17 harness defect investigation): the drift loop ran
unconditionally, before the faction/friction/admin-revolt block, instead of
gated and last (tick sequence step 5, docs/bible/algorithms.md:9-29). This
module proves the gate now works and the step sits in the right place.
"""
from conftest import (
    OMArchetype,
    OMFeature,
    OMField,
    OMTier,
    OmTraceRow,
    set_faction,
    set_owner,
    set_region,
    set_tech_multipliers,
)


def _all_fields(lib, w, idx):
    return tuple(lib.om_region_field(w, idx, f) for f in
                 (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION))


def test_R_160_01_drift_off_leaves_fields_unchanged(lib, world_factory):
    # R-160-01 says "every region" (plural): one region alone could pass by
    # accident if a fix only gated the loop's first iteration or similar --
    # three regions with distinct values each catch a partial/off-by-one gate.
    w = world_factory(n_regions=3)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)
    set_region(lib, w, 1, tier=OMTier.HOME, military=5.0, economy=12.0,
               tension=90.0, population=8.0)
    set_region(lib, w, 2, tier=OMTier.FRONTIER, military=99.0, economy=33.0,
               tension=0.0, population=100.0)

    before = [_all_fields(lib, w, idx) for idx in range(3)]
    lib.om_world_step(w)
    after = [_all_fields(lib, w, idx) for idx in range(3)]

    assert after == before, (
        "OM_FEAT_DRIFT is off but at least one region's fields moved -- the "
        "drift step ran anyway (checked across all 3 regions, not just one)"
    )


def test_R_160_02_default_world_has_only_drift_on(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_world_feature(w, OMFeature.DRIFT) == 1, (
        "om_world_new must switch OM_FEAT_DRIFT on by default"
    )
    for feat in (OMFeature.EVENTS, OMFeature.FACTIONS, OMFeature.FRICTION,
                 OMFeature.ADMIN_REVOLTS, OMFeature.DIPLOMACY,
                 OMFeature.TECHNOLOGY, OMFeature.LIFECYCLE):
        assert lib.om_world_feature(w, feat) == 0, (
            f"om_world_new must leave feature {feat} off by default -- only "
            "DRIFT is decided (S-160); every other default is open flag A4"
        )


def test_R_160_02_default_world_drifts(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)
    lib.om_world_step(w)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) != 66.0, (
        "a freshly-made world did not drift on its own tick -- DRIFT is not "
        "actually on by default"
    )


def test_R_160_03_budget_step_reads_pre_drift_economy(lib, world_factory):
    """Given a faction owning regions with economy 66, 40, and 9, and DRIFT
    also on, When one tick runs, Then Δbudget still equals
    ((66-8)+(40-8)+(9-8))*0.025 = 2.275 -- the same-tick budget step must
    read economy as it stood before this tick's drift, matching tick.py's
    order (faction agents at step 3, drift at step 5)."""
    w = world_factory(n_regions=3)
    for feat in (OMFeature.EVENTS, OMFeature.FRICTION, OMFeature.ADMIN_REVOLTS,
                 OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY, OMFeature.LIFECYCLE):
        lib.om_world_set_feature(w, feat, 0)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 1)

    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=0.0, confidence=5.0)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)

    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=66.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=40.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=9.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 2, 0, held_since=-1)

    initial_budget = lib.om_faction_budget(w, 0)
    lib.om_world_step(w)
    budget_after = lib.om_faction_budget(w, 0)
    delta_budget = budget_after - initial_budget

    expected_delta = ((66.0 - 8.0) + (40.0 - 8.0) + (9.0 - 8.0)) * 0.025
    assert abs(delta_budget - expected_delta) < 1e-6, (
        f"budget delta {delta_budget} does not match pre-drift economy delta "
        f"{expected_delta} -- the budget step is reading economy after this "
        "tick's drift already moved it"
    )


def test_R_160_04_drift_off_emits_no_trace_rows(lib, world_factory):
    # R-160-04: trace/checksum emission (om_trace_append + the
    # checksum-on-cadence write) lives inside the per-region drift loop
    # today (csrc/sim.c, the `if (w->trace_on) { ... }` block right after the
    # clamp, before the loop closes). Spec Constraints
    # (docs/legacy/test_specs/drift-gate-and-green-check.md line 25): "Trace and
    # checksum emission (currently inside the per-region drift loop) move
    # with the loop" -- once the gate fix lands, that whole block sits
    # inside the `if (om_world_feature(w, OM_FEAT_DRIFT))` guard, so a
    # DRIFT-off world's loop body (including trace emission) never runs at
    # all. Zero ticks should ever append a row, checksum-cadence boundary or
    # not. RED today: the bug runs the loop (and its trace/checksum write)
    # unconditionally, so the buggy build appends a row every tick anyway.
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    lib.om_trace_enable(w, 1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=60.0,
               tension=20.0, population=50.0)

    cadence = lib.om_checksum_cadence()
    lib.om_world_run(w, cadence + 2)  # cross at least one checksum boundary

    assert lib.om_trace_len(w) == 0, (
        "OM_FEAT_DRIFT is off but the trace buffer has rows -- the "
        "emission living inside the drift loop ran anyway"
    )


def test_R_160_04_drift_on_checksum_cadence_still_works(lib, world_factory):
    # R-160-04, companion case: with DRIFT explicitly
    # on, the checksum-cadence behavior the gate fix relocates must still
    # hold (spec Constraints, same line: emission "move[s] with the loop"
    # rather than being deleted). Scoped small (1 region, cadence+2 ticks)
    # because test_E02_S020_determinism.py::test_R_020_03_checksum_emitted_
    # only_on_cadence already owns full coverage of this shape.
    # NOTE (vacuous today, like test_R_160_02_default_world_drifts above):
    # the current bug runs the drift loop -- and its trace/checksum
    # emission -- unconditionally, so a DRIFT-on world already behaves this
    # way before the real fix. This assertion is kept because it will still
    # hold, for the right reason, once the gate is real.
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 1)
    lib.om_trace_enable(w, 1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=60.0,
               tension=20.0, population=50.0)

    cadence = lib.om_checksum_cadence()
    n_ticks = cadence + 2
    lib.om_world_run(w, n_ticks)
    n = lib.om_trace_len(w)
    rows = (OmTraceRow * n)()
    lib.om_trace_read(w, 0, n, rows)

    for row in sorted(rows, key=lambda r: r.tick):
        if row.tick % cadence == 0:
            assert row.checksum != 0, f"tick {row.tick} should carry a checksum"
        else:
            assert row.checksum == 0, f"tick {row.tick} should not carry a checksum"


