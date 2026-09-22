"""S-160 -- D1 (docs/northstar/plans/briefs/2026-09-22-two-day-push.md,
decision 4): om_world_new() itself sets no feature any more; the DRIFT-on
default that used to live in csrc/region.c is gone. Fixtures (world_factory,
dbg_world_factory) apply an epic's feature set from
docs/northstar/spec_factory/mvp_features.toml on top of a raw world -- this
module calls lib.om_world_new directly, bypassing those fixtures, to prove
the raw contract itself.
"""
from conftest import OMField, OMTier

_ALL_FEATURES = range(9)  # OM_FEAT_EVENTS (0) .. OM_FEAT_TACTICAL (8)


def test_R_160_raw_world_has_every_feature_off(lib):
    w = lib.om_world_new(1, 1)
    assert w, "om_world_new returned NULL"
    try:
        for feat in _ALL_FEATURES:
            assert lib.om_world_feature(w, feat) == 0, (
                f"a raw om_world_new world has feature {feat} on -- om_world_new "
                "must set no feature (D1)"
            )
    finally:
        lib.om_world_free(w)


def test_R_160_raw_world_step_changes_no_field(lib):
    w = lib.om_world_new(1, 1)
    assert w, "om_world_new returned NULL"
    try:
        rc = lib.om_region_set(w, 0, OMTier.HOME, 50.0, 50.0, 20.0, 50.0, 0.3, 1.1, -1)
        assert rc == 0
        fields = (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION)
        before = [lib.om_region_field(w, 0, f) for f in fields]
        tick = lib.om_world_step(w)
        assert tick == 1
        after = [lib.om_region_field(w, 0, f) for f in fields]
        assert before == after, (
            "om_world_step changed a region field with every feature off -- "
            "a raw world must be a true no-op tick"
        )
    finally:
        lib.om_world_free(w)
