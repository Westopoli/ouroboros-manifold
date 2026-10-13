"""ALG-64 Squads (docs/bible/algorithms.md; S-088, R-088-01): "A Strike unit is one entity (one HP, one position);
squad membership is rendering only."

The sim keeps one unit row per Strike unit however many craft the client draws for it (om_unit_render_craft_count,
3 to 5 for Strike): the unit count rises by one per spawn, the unit has one HP value that one hit reduces by the
whole hit (no per-craft split), and one position that one move shifts. Positive control: a second spawn counts as a
second entity, so a count that ignored spawns would not pass.
"""
import pytest

from conftest import OMFeature

RAIDER, INTERCEPTOR = 0, 1
PLAYER, ENEMY = 0, 1


def _world(lib):
    w = lib.om_world_new(1, 1)
    assert w
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    return w


@pytest.mark.parametrize("utype", [RAIDER, INTERCEPTOR])
def test_ALG_64_a_strike_unit_is_one_entity_with_one_hp_and_one_position(lib, utype):
    w = _world(lib)
    crafts = lib.om_unit_render_craft_count(w, utype)
    assert crafts > 1  # the client draws a squad ...
    before = lib.om_unit_count(w)
    u = lib.om_unit_spawn(w, utype, PLAYER, 100.0, 200.0, 0)
    assert lib.om_unit_count(w) == before + 1  # ... but the sim holds one entity
    max_hp = lib.om_unit_profile_max_hp(w, utype)
    assert lib.om_unit_hp(w, u) == pytest.approx(max_hp)  # one HP, not crafts x HP
    attacker = lib.om_unit_spawn(w, RAIDER, ENEMY, 150.0, 200.0, 0)
    lib.om_unit_set_hp(w, u, max_hp)
    base_hit = 10.0
    lib.om_unit_deal_damage(w, attacker, u, base_hit)
    mult = 1.0  # Strike attacker versus Strike target: ALG-60 CATEGORY_MULTIPLIER 1.0, output 1.0, reduction 0
    assert lib.om_unit_hp(w, u) == pytest.approx(max_hp - base_hit * mult)  # the whole hit lands on the one HP
    assert lib.om_unit_get_pos(w, u) == pytest.approx((100.0, 200.0))  # one position


def test_control_ALG_64_two_spawns_are_two_entities(lib):
    w = _world(lib)
    before = lib.om_unit_count(w)
    lib.om_unit_spawn(w, RAIDER, PLAYER, 0.0, 0.0, 0)
    lib.om_unit_spawn(w, RAIDER, PLAYER, 10.0, 0.0, 0)
    assert lib.om_unit_count(w) == before + 2
    assert lib.om_unit_count(w) != before + lib.om_unit_render_craft_count(w, RAIDER) * 2  # not one entity per craft
