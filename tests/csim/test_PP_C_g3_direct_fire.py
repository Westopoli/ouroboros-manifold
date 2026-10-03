# spec: docs/bible/epics/E-01 R-008-04; rulings-2 A125 (side sight), A185
"""Phase C G3 direct fire: the two R-008-04 cases that need side-sight targeting (moved from the held
g5 file). Red until OM_TP_TARGET_BY_SIGHT is implemented: today a unit in range and reach fires at an
unseen target. Helpers come from test_PP_C_g5_support (in the tree)."""
import pytest

from test_PP_C_g5_support import (
    BOMBARD, EDGE, INTERCEPTOR, RAIDER, SUPPLY, VANGUARD, WINDOW, attack_move, duel, engaged,
    first_hit, get_param, hp, layers_for, open_vision, pos, read_reach, set_param, set_reach, solo_pair,
    spawn, state_snapshot, step, target,
)


# ---------------------------------------------------------------- reach and sight (R-008-04)

def test_R_008_04_reach_is_not_sight_a_target_in_reach_but_unseen_is_not_fired_at(lib, world_factory):
    """R-008-04 with R-164-02: a target within reach and range that the side cannot see is not fired
    at. Vanguard (sensor 700), reach (1, 0), target 1 layer up at 200 wu. Vision factor 0.5 (default):
    seen (350 wu), engaged (control). OM_TP_VISION_UP_1 = 0: not seen, not engaged."""
    got, _ = duel(lib, world_factory, VANGUARD, 2, 3, 200.0, reach=(1, 0))
    assert got, "control: seen and in reach, engaged"
    got, dmg = duel(lib, world_factory, VANGUARD, 2, 3, 200.0, reach=(1, 0), params={"OM_TP_VISION_UP_1": 0.0})
    assert not got and dmg == 0.0


def test_R_008_04_a_spotter_on_the_targets_layer_lets_a_siege_unit_fire_up(lib, world_factory):
    """R-008-04 ('seen by any friendly unit'), A125 siege rule, with reach: a Bombard (sensor 300,
    range 1200) with reach 1 up fires at an enemy one layer up 600 wu away only if its side sees it.
    Without a spotter it does not (control); with a friendly Interceptor (sensor 1000) on the enemy's
    layer 700 wu from it, it does."""
    def run(spotter):
        w = world_factory(n_regions=1)
        assert set_reach(lib, w, BOMBARD, 1, 0) == 0
        b = spawn(lib, w, BOMBARD, 0, 0.0, 0.0, layer=1)
        t = spawn(lib, w, SUPPLY, 1, 600.0, 0.0, layer=2)
        if spotter:
            spawn(lib, w, INTERCEPTOR, 0, 600.0, 700.0, layer=2)
        return engaged(lib, w, b, t, steps=WINDOW + 60)
    assert run(spotter=True), "a spotter's sight is the side's sight"
    assert not run(spotter=False), "without one the Bombard's 150 wu cross-layer sight cannot see 600 wu"
