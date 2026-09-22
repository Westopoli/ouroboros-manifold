"""F5 window control for csrc/tactical_support.c (E-15, wave 2 card B14).

Rule (docs/bible/algorithms.md ALG-75 "Capture and production"): "Each
structure: capture radius REINFORCEMENT_CAPTURE_RADIUS = 300, HP
REINFORCEMENT_STRUCTURE_HP = 3000." A freshly placed structure's HUD data
(om_structure_hud.max_hp) must read 3000.0.

Read via om_structure_get_hud_data (which takes om_world*), not the pure
om_structure_get_base_max_hp(void) getter declared alongside it: that one
takes no om_world* at all, so no per-world om_debug_inject could ever gate
it -- a control built on it could not fail on any build, correct or buggy
(CLAUDE.md).

PLANT: under OM_BUG_STRUCTURE_MAX_HP_WRONG_CONSTANT,
om_structure_get_hud_data fills max_hp with REINFORCEMENT_CAPTURE_RADIUS
(300.0) instead of REINFORCEMENT_STRUCTURE_HP (3000.0) -- a plausible
mix-up of the two constants named in the same ALG-75 sentence.
"""
import ctypes

import pytest

from conftest import OMBugE15, OMStructureHUD


def test_control_structure_max_hp_wrong_constant_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugE15.STRUCTURE_MAX_HP_WRONG_CONSTANT)

    sid = dbg.om_map_add_structure(w, 0.0, 0.0, -1)

    hud = OMStructureHUD()
    dbg.om_structure_get_hud_data(w, sid, ctypes.byref(hud))

    assert hud.max_hp == pytest.approx(300.0, abs=1e-9), (
        "OM_BUG_STRUCTURE_MAX_HP_WRONG_CONSTANT injected but max_hp still "
        "reads the correct REINFORCEMENT_STRUCTURE_HP (3000.0) instead of "
        "REINFORCEMENT_CAPTURE_RADIUS (300.0) -- the detector did not trip"
    )
