"""PP-fog / PP-move / PP-mapgen rule tests, cover endpoint exemption and cover height.

Proves E-13 R-098-02 (S-098), E-01 R-007-01, R-007-02, R-007-05, R-007-06 (S-007), as reworded by Addendum 45
(docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md, row "Cover"). Westley, 2026-10-02:
"Yes, we should definitely build it now" (cover height); fire follows the vision rule and a unit standing
inside a cover obstacle is seen and shot as normal.

The call is the existing `om_map_add_cover(w, x, y, radius, double height)`; the height is read as layers 1..height.

Layer indexing: the C numbers unit layers from 0 (om_unit_spawn(..., layer), E-17's tests), the epic numbers them
from 1. The scenes below are chosen so that the verdict is the same under either reading: height 2 covers unit
layer 1 and does not reach unit layer 3; height 5 reaches layer 3. Layer 0 is not used with a short cover.

Vision is om_unit_can_see; fire is om_combat_can_shoot. "Exactly as vision is" is tested by comparing the two over
one table of scenes.
"""
import math

import pytest

from conftest import OMFeature

RAIDER = 0
FRIEND, ENEMY = 0, 1

# observer (0,0), target (200,0), cover disc radius 20 at (100,0) between them
OBS = (0.0, 0.0)
TGT = (200.0, 0.0)
COVER = (100.0, 0.0, 20.0)


@pytest.fixture
def tw(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


def _scene(lib, w, obs, tgt, layer, height, cover=COVER):
    o = lib.om_unit_spawn(w, RAIDER, FRIEND, obs[0], obs[1], layer)
    t = lib.om_unit_spawn(w, RAIDER, ENEMY, tgt[0], tgt[1], layer)
    if height is not None:
        lib.om_map_add_cover(w, cover[0], cover[1], cover[2], float(height))
    return o, t


# (id, observer, target, unit layer, cover height, blocked?)
SCENES = [
    # R-007-01: obstacle reaching layer 2, both units on layer 1, line passes through it: hidden
    ("short_cover_blocks_its_own_layer", OBS, TGT, 1, 2.0, True),
    # R-007-02: same obstacle, both on layer 3: it does not reach, visible
    ("short_cover_does_not_reach_layer_3", OBS, TGT, 3, 2.0, False),
    # control for the height reading: a tall obstacle does reach layer 3
    ("tall_cover_reaches_layer_3", OBS, TGT, 3, 5.0, True),
    # control: no cover at all
    ("no_cover", OBS, TGT, 3, None, False),
    # control: the line misses the disc (offset 60 wu from the centre, radius 20)
    ("line_misses_the_disc", (0.0, 60.0), (200.0, 60.0), 1, 5.0, False),
    # R-007-06: the observer stands inside the disc: it sees and shoots out of it as in the open
    ("observer_inside_cover", (95.0, 0.0), TGT, 1, 5.0, False),
    # R-007-06: the target stands inside the disc: it is seen and shot as in the open
    ("target_inside_cover", OBS, (105.0, 0.0), 1, 5.0, False),
    # control: both outside, the line passes through (the base blocked case, tall cover, layer 1)
    ("both_outside_line_through", OBS, TGT, 1, 5.0, True),
]


@pytest.mark.parametrize("sid,obs,tgt,layer,height,blocked", SCENES, ids=[s[0] for s in SCENES])
def test_R_007_01_02_06_vision_follows_cover_height_and_endpoint_exemption(lib, tw, sid, obs, tgt, layer, height, blocked):
    """E-01 R-007-01, R-007-02, R-007-06: an obstacle blocks a sight line only on the layers its height reaches, and
    only a line that passes through it between two units both outside it. Vision already exempts an endpoint inside
    the disc (green today); it does not yet read the height (the 'short cover does not reach layer 3' scene is red)."""
    o, t = _scene(lib, tw, obs, tgt, layer, height)
    lib.om_tactical_step(tw)
    assert lib.om_unit_can_see(tw, o, t) == (0 if blocked else 1), f"{sid}: vision verdict wrong"


@pytest.mark.parametrize("sid,obs,tgt,layer,height,blocked", SCENES, ids=[s[0] for s in SCENES])
def test_R_098_02_fire_is_blocked_exactly_as_vision_is(lib, tw, sid, obs, tgt, layer, height, blocked):
    """E-13 R-098-02: given a cover obstacle between them on the layers involved, the shot is blocked exactly as
    vision is: cover blocks only up to its height, and only a line through it between two outside units; a unit
    standing inside cover is fired at, and fires, as normal (E-01 R-007-06). The C's fire test ignores both the
    height and the endpoint exemption (every scene except the plain blocked ones and the no-cover control is red)."""
    o, t = _scene(lib, tw, obs, tgt, layer, height)
    assert lib.om_combat_can_shoot(tw, o, t) == (0 if blocked else 1), f"{sid}: fire verdict wrong"
    assert lib.om_combat_can_shoot(tw, t, o) == (0 if blocked else 1), f"{sid}: fire verdict wrong (reverse)"
    assert lib.om_combat_can_shoot(tw, o, t) == lib.om_unit_can_see(tw, o, t), f"{sid}: fire and sight disagree"


def test_R_007_05_cover_never_blocks_movement(lib, tw):
    """E-01 R-007-05: cover in a unit's path does not affect its movement. A Raider ordered through the middle of a
    cover disc walks its full 7.5 wu per tick across it. Green today; stays green."""
    u = lib.om_unit_spawn(tw, RAIDER, FRIEND, 70.0, 0.0, 0)
    lib.om_map_add_cover(tw, 100.0, 0.0, 20.0, 5.0)
    lib.om_command_move(tw, u, 400.0, 0.0)
    x_prev = 70.0
    for _ in range(8):
        lib.om_tactical_step(tw)
        x, y = lib.om_unit_get_pos(tw, u)
        assert x - x_prev == pytest.approx(7.5, abs=0.01)
        assert abs(y) < 0.05
        x_prev = x
