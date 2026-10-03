"""RET-1 (R-077-01): retention = surviving unit power / deployed power, damaged units
counted by HP fraction, capped at 1. om_mission_end hardcodes
om_mission_compute_retention(1.0, 1.0) today, so retention is always 1.0.

Deployed force = the player-faction units the mission spawned; power per unit type is
om_unit_power (R-074-06). Units made during the mission are left out of these tests
(Q-212-04 is open), so none are spawned.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype, OMEdge, OMFeature, OMTier, om_debrief, set_edge, set_faction, set_owner, set_region,
)

PLAYER_FAC = 0
ENEMY_FAC = 1
ASSAULT = 3


def _mission(lib, world_factory):
    w = world_factory(n_regions=2, seed=7)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=60.0, faction_id=ENEMY_FAC)
    set_region(lib, w, 1, tier=OMTier.HOME, military=60.0, faction_id=PLAYER_FAC)
    lib.om_mission_setup(w, 0, ASSAULT, 0)
    lib.om_mission_build_objectives(w, ASSAULT)
    return w


def _player_units(lib, w):
    return [u for u in (lib.om_unit_id_at(w, i) for i in range(lib.om_unit_count(w)))
            if u and lib.om_unit_get_faction(w, u) == PLAYER_FAC]


def _retention_after_end(lib, w):
    lib.om_mission_end(w)
    d = om_debrief()
    assert lib.om_mission_get_debrief(w, ctypes.byref(d)) == 1
    return d.retention


def test_untouched_force_retains_everything(lib, world_factory):
    """Control: nobody hurt -> retention 1.0 (also what the stub returns, so it passes today)."""
    w = _mission(lib, world_factory)
    assert _player_units(lib, w)
    assert _retention_after_end(lib, w) == pytest.approx(1.0, abs=1e-9)


def test_every_unit_at_half_hp_retains_one_half(lib, world_factory):
    """R-077-01: damaged units count by HP fraction -> all at 50 percent HP gives 0.5."""
    w = _mission(lib, world_factory)
    for u in _player_units(lib, w):
        lib.om_unit_set_hp(w, u, lib.om_unit_get_hp(w, u) / 2.0)
    r = _retention_after_end(lib, w)
    assert r == pytest.approx(0.5, abs=1e-6), "retention %r, expected 0.5: om_mission_end ignores real unit power" % r


def test_half_the_deployed_power_dead_retains_the_surviving_power_share(lib, world_factory):
    """R-077-01: kill units until at least half of the deployed power is dead; retention
    is surviving power / deployed power with om_unit_power per type (R-074-06)."""
    w = _mission(lib, world_factory)
    units = _player_units(lib, w)
    power = {u: lib.om_unit_power(lib.om_unit_get_unit_type(w, u)) for u in units}
    deployed = sum(power.values())
    assert deployed > 0.0
    dead = 0.0
    for u in units:
        if dead >= deployed / 2.0:
            break
        lib.om_unit_set_hp(w, u, 0.0)
        dead += power[u]
    expected = (deployed - dead) / deployed
    assert expected < 1.0
    r = _retention_after_end(lib, w)
    assert r == pytest.approx(expected, abs=1e-6), (
        "retention %r, expected %r (surviving/deployed power): om_mission_end hardcodes 1.0" % (r, expected))
