"""Positive control for OM_BUG_COMPOSITE_PRE_CLAMP.

Watch-for: "Composite-before-clamp -- stability/capacity computed from
pre-clamp fields." Order of operations (docs/northstar/e2e/E-02.md):
compute drift -> clamp fields -> recompute composites from the clamped
fields (R-012-01).

Drives tension to the clamp ceiling under sustained positive pressure (low
economy, low stability, high population), confirms the stored field is
clamped to 100.0, then computes the ALG-09 stability the clamped fields
imply and asserts the debug build's actual composite -- with
OM_BUG_COMPOSITE_PRE_CLAMP injected -- no longer matches it.
"""
from conftest import OMBug, OMComposite, OMField, OMTier, set_region


def test_control_composite_pre_clamp_trips_the_clamp_order_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=0.0, economy=0.0,
               tension=90.0, population=100.0)
    dbg.om_debug_inject(w, OMBug.COMPOSITE_PRE_CLAMP)

    for _ in range(50):
        dbg.om_world_step(w)

    m = dbg.om_region_field(w, 0, OMField.MILITARY)
    t = dbg.om_region_field(w, 0, OMField.TENSION)
    p = dbg.om_region_field(w, 0, OMField.POPULATION)
    assert t == 100.0, "fixture did not overflow tension to the clamp ceiling; adjust setup"

    expected_stability = m * 0.40 + (100.0 - t) * 0.35 + p * 0.25
    if m < 10.0:
        expected_stability *= 0.70
    if p < 20.0:
        expected_stability *= 0.75
    expected_stability = round(expected_stability, 2)

    actual_stability = dbg.om_region_composite(w, 0, OMComposite.STABILITY)
    assert abs(actual_stability - expected_stability) > 1e-6, (
        "OM_BUG_COMPOSITE_PRE_CLAMP injected but stability still matches the "
        "post-clamp expectation -- the composite-order detector did not trip"
    )
