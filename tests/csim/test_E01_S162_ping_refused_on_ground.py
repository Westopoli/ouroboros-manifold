"""E-01 S-162 / R-005-09 (ground era, terrain stage 2 spec 2026-10-06, lane "fog"): the ping is space-only. In a ground era
(om_era_kind 1) om_command_ping is refused with reason 5 (pp_contract.md section 6: after the caster check, before the
reach check), reveals nothing, and costs no cooldown; era kind 0 casts as today.

Fixture follows test_E01_S162_ping_reveal_follows_units.py: caster RAIDER on engine layer 0, an enemy INTERCEPTOR (a flyer: a walking type is placed on its band whatever layer is asked) on layer 4
(four layers up, never passively seen), the ping 1,500 wu from the caster (reach 2,000). Units sit on the terrain-seed-11
band-1 line of test_E01_T2_fog_support.py. RAIDER is a walker here (kind 1); the ping is the space-era caster verb.

Expected today (fog.c casts in every era): test_ground_ping_refused_with_reason_5, test_ground_ping_checked_before_reach,
test_ground_ping_reveals_nothing, test_refusal_costs_no_cooldown are red; test_unknown_caster_is_still_reason_1 and
test_era_kind_0_ping_casts are guards (green today).
"""
import pytest

from test_E01_T2_fog_support import (PING_OK, PING_REASON_CASTER, PING_REASON_GROUND, PING_REASON_REACH, INTERCEPTOR, RAIDER,
                                     Scan, make_ground_world, open_line, spawn)

HIGH = 4
CAST_DX = 1500.0
REACH_BEYOND = 2600.0   # provisional (2026-10-06): past OM_TP_PING_REACH (2,000)
MISSING_CASTER = 9999


def _scene(lib, world_factory, era):
    w = make_ground_world(lib, world_factory, era_kind=era)
    x0, y, _, _ = open_line(Scan(lib, w), 17)
    caster = spawn(lib, w, RAIDER, 0, x0, y, 0)
    enemy = spawn(lib, w, INTERCEPTOR, 1, x0 + CAST_DX + 100.0, y, HIGH)
    return w, caster, enemy, x0, y


def test_ground_ping_refused_with_reason_5(lib, world_factory):
    """S-162 ground rule: reason 5, a valid ping point and a live caster."""
    w, caster, enemy, x0, y = _scene(lib, world_factory, 1)
    assert lib.om_command_ping(w, caster, HIGH, x0 + CAST_DX, y) == PING_REASON_GROUND


def test_ground_ping_checked_before_reach(lib, world_factory):
    """Contract: the era check precedes the reach check, so a point beyond reach still answers 5 in a ground era."""
    w, caster, enemy, x0, y = _scene(lib, world_factory, 1)
    assert lib.om_command_ping(w, caster, HIGH, x0 + REACH_BEYOND, y) == PING_REASON_GROUND


def test_unknown_caster_is_still_reason_1(lib, world_factory):
    """Contract: the caster check comes first. Guard (green today)."""
    w, caster, enemy, x0, y = _scene(lib, world_factory, 1)
    assert lib.om_command_ping(w, MISSING_CASTER, HIGH, x0 + CAST_DX, y) == PING_REASON_CASTER


def test_ground_ping_reveals_nothing(lib, world_factory):
    """A refused ping changes nothing: the enemy four layers up stays hidden after a tick. Control: era 0 reveals it."""
    seen = {}
    for era in (0, 1):
        w, caster, enemy, x0, y = _scene(lib, world_factory, era)
        assert lib.om_player_can_see(w, 0, enemy) == 0, "control: hidden before the cast"
        lib.om_command_ping(w, caster, HIGH, x0 + CAST_DX, y)
        lib.om_tactical_step(w)
        seen[era] = lib.om_player_can_see(w, 0, enemy)
    assert seen[0] == 1, "control: the era 0 ping reveals the enemy"
    assert seen[1] == 0, "a ground-era ping revealed a unit"


def test_refusal_costs_no_cooldown(lib, world_factory):
    """A refused ping starts no cooldown: back in era 0 the same caster casts at once."""
    w, caster, enemy, x0, y = _scene(lib, world_factory, 1)
    assert lib.om_command_ping(w, caster, HIGH, x0 + CAST_DX, y) == PING_REASON_GROUND
    assert lib.om_set_era_kind(w, 0) == 0
    assert lib.om_command_ping(w, caster, HIGH, x0 + CAST_DX, y) == PING_OK


def test_era_kind_0_ping_casts(lib, world_factory):
    """Space era: the ping casts as today. Guard (green today)."""
    w, caster, enemy, x0, y = _scene(lib, world_factory, 0)
    assert lib.om_command_ping(w, caster, HIGH, x0 + CAST_DX, y) == PING_OK
