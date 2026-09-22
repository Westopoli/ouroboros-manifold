"""F5 window control for csrc/unit.c (E-11, wave 1 card B10).

Rule (docs/bible/algorithms.md ALG-60 "Damage", Reduction): "Brace 0.50 +
Fortify 0.20 for any friendly within FORTIFY_RADIUS of an active Bastion +
Warden aura 0.10 per Warden within WARDEN_AURA_RADIUS." A lone unit with only
its own Brace ability forced active (no Bastion, no Warden nearby) must read
damage reduction exactly 0.50.

PLANT: under OM_BUG_BRACE_REDUCTION_WRONG_CONSTANT, om_unit_damage_reduction
applies Fortify's constant (0.20) to an active Brace instead of Brace's own
0.50.
"""
import pytest

from conftest import OMBugE11


def test_control_brace_reduction_wrong_constant_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE11.BRACE_REDUCTION_WRONG_CONSTANT)

    uid = dbg.om_unit_spawn(w, 0, 0, 0.0, 0.0, 0)
    dbg.om_unit_set_brace_active(w, uid, 1)

    reduction = dbg.om_unit_damage_reduction(w, uid)

    assert reduction == pytest.approx(0.20, abs=1e-9), (
        "OM_BUG_BRACE_REDUCTION_WRONG_CONSTANT injected but an active, "
        "isolated Brace still reads its correct reduction (0.50) instead of "
        "Fortify's 0.20 -- the detector did not trip"
    )
