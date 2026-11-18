# Rule pins: R-007-01, R-007-02, R-098-02
"""E-01 R-007-01 (Round 5, G8: the seven proof qualifications, docs/method/requirements.md Proof): an obstacle whose height reaches the layer of two units stops them seeing each other after one tick.

Rule word for word (docs/bible/epics/E-01-layer-system.md):
  R-007-01  "Given an obstacle whose height reaches layer 2 between an observer and a target both on layer 1, When one tick passes, Then the target is not visible."

Configuration: the shipped one for a csim scene (what scripts/skilllab/arena/run.py `fight(.., "on")` sets, read 2026-11-17): a 4000 x 4000 canvas, ground era (om_set_era_kind 1), the Raider set to the walking kind,
targeting by sight at its default (on), abilities off, reach 0 up 1 down. What differs from the lab, and why: the lab has no `om_map_add_cover` obstacle (its features are planar boxes, `om_map_block_rect` over every
layer, which reach every layer), so the test builds both: the cover disc of height 2 the rule describes (scene "cover"), and the lab's box (scene "box"). No terrain is generated (a flat world: layer 1 is the layer the
units are spawned on), so the scene does not test how a hill makes the layers. Whether the epic's layer 1 is the C's layer 0 or 1 does not matter here: units on layer 1, cover height 2.0 (as test_PP_move_cover.py).
Then asserted for both the unit's own sight (om_unit_can_see) and the side's visible set (om_player_can_see, the set R-093-02 acquires and fires from), through om_tactical_step (the tick, as play does).
Control (filled): the same scene with the obstacle left out is visible both ways, so an engine that ignored obstacles would fail the rule's assertion; and a cover of height 0.5 that does not reach layer 1... see
test_R_007_01_control_*.
"""
import pytest

from conftest import OMFeature
from test_PP_unit_support import RAIDER, spawn, step

CANVAS = 4000.0
WALKING, ERA_GROUND = 1, 1
OBS, TGT = (1000.0, 2000.0), (1300.0, 2000.0)     # 300 wu apart on the open ground, the obstacle between them
LAYER = 1


def _scene(lib, wf, obstacle):
    w = wf(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_set_era_kind(w, ERA_GROUND) == 0
    assert lib.om_roster_set_movement_kind(w, RAIDER, WALKING) == 0
    lib.om_tactical_disable_abilities(w)
    if obstacle == "cover":
        lib.om_map_add_cover(w, 1150.0, 2000.0, 20.0, 2.0)               # height 2: reaches layers 1 and 2
    elif obstacle == "box":
        assert lib.om_map_block_rect(w, 1100.0, 1900.0, 1200.0, 2100.0, 0, 3) == 0   # the lab's box: every layer
    o = spawn(lib, w, RAIDER, 0, *OBS, layer=LAYER)
    t = spawn(lib, w, RAIDER, 1, *TGT, layer=LAYER)
    return w, o, t


def _seen(lib, w, o, t):
    step(lib, w)
    return bool(lib.om_unit_can_see(w, o, t)), bool(lib.om_player_can_see(w, 0, t))


@pytest.mark.parametrize("obstacle", ["cover", "box"])
def test_R_007_01_an_obstacle_reaching_the_layer_between_two_units_on_it_hides_the_target_after_one_tick(lib, world_factory, obstacle):
    """R-007-01 "Given an obstacle whose height reaches layer 2 between an observer and a target both on layer 1, When one tick passes, Then the target is not visible." Observer (side 0) and target (side 1) on layer 1,
    300 wu apart, the obstacle between them: after one om_tactical_step the observer does not see the target and the observer's side does not have it in its visible set. Scenes: the cover disc of height 2.0 and
    the lab's box (see the module docstring for the configuration and what differs from the lab)."""
    w, o, t = _scene(lib, world_factory, obstacle)
    assert lib.om_unit_get_layer(w, o) == lib.om_unit_get_layer(w, t) == LAYER, "scene broken: the units are on different layers"
    assert _seen(lib, w, o, t) == (False, False), "the target is visible across the %s" % obstacle


def test_R_007_01_control_without_the_obstacle_the_same_scene_is_seen_and_a_low_cover_does_not_hide(lib, world_factory):
    """Control (filled) for R-007-01: the scene of the proof with nothing between the units is seen both ways after one tick, so the assertion of the proof fails against an engine that ignores obstacles; a cover of
    height 0.5 (below the units' layer) leaves them seen too, so the proof is about the height the rule names and not about any disc."""
    w, o, t = _scene(lib, world_factory, None)
    assert _seen(lib, w, o, t) == (True, True)
    w, o, t = _scene(lib, world_factory, None)
    lib.om_map_add_cover(w, 1150.0, 2000.0, 20.0, 0.5)
    assert _seen(lib, w, o, t) == (True, True)
