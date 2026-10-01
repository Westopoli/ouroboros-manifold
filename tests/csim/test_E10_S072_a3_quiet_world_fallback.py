"""A3 (mission.c half): om_mission_setup_fallback, the quiet-world fallback.

R-072-07 / R-072-08 (fallback Defensive Stand, enemy faction, enemy power),
R-074-01 (default form: strongest region's military x 2000), R-074-04 (the
player's budget is P * parity). Ruling: docs/northstar/plans/2026-10-01-architect-rulings.md A3.
Isolation tests, no pipe. Choosing the region and the enemy faction (BFS
nearest, five retries, quiet_world) is the pipe piece's job (push/A3-tests2).

Observables, since the C ABI has no archetype/region getter:
  * enemy faction: faction of the spawned enemy units, and om_mission_get_enemy_faction
  * enemy power: om_mission_get_enemy_power
  * player budget: sum of om_unit_power over om_mission_get_player_units, bounded
    by P * parity (R-074-04 overshoot tolerance 1.15 is OM_MISSION_FILL_OVERSHOOT_MULT)
  * archetype: the map canvas (cover disc at canvas/2) of Defensive Stand
    (category 1) against a control archetype of another category
  * region: om_mission_get_player_parity, which reads the region's capacity
"""
import ctypes

import pytest

from conftest import OMArchetype, OMTier, set_faction, set_owner, set_region

DEFENSIVE_STAND = 0
CONTROL_ARCHETYPE = 4  # Suppression: small canvas, category 0
PLAYER, ENEMY, OTHER = 0, 1, 2
P_PER_MILITARY = 2000.0
OVERSHOOT = 1.15


def _units(lib, w):
    out = []
    for i in range(lib.om_unit_count(w)):
        uid = lib.om_unit_id_at(w, i)
        if uid:
            out.append((lib.om_unit_get_faction(w, uid), lib.om_unit_get_unit_type(w, uid)))
    return out


def _player_counts(lib, w):
    counts = (ctypes.c_uint32 * 6)()
    lib.om_mission_get_player_units(w, PLAYER, counts, 6)
    return list(counts)


def _player_power(lib, w):
    return sum(lib.om_unit_power(t) * n for t, n in enumerate(_player_counts(lib, w)))


def _cheapest_unit_power(lib):
    return min(lib.om_unit_power(t) for t in range(6) if lib.om_unit_power(t) > 0.0)


def _world(lib, world_factory, enemy_military=(30.0, 10.0), other_military=90.0, seed=1):
    """r0, r1 player regions (r1 has more economy so capacity differs); the enemy
    faction owns one region per entry of enemy_military; a third faction owns a
    stronger region the fallback must ignore."""
    n = 2 + len(enemy_military) + 1
    w = world_factory(n_regions=n, seed=seed)
    set_faction(lib, w, PLAYER, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY, OMArchetype.CONQUEROR)
    set_faction(lib, w, OTHER, OMArchetype.CONQUEROR)
    set_region(lib, w, 0, tier=OMTier.HOME, military=20.0, economy=10.0, tension=30.0, population=50.0, faction_id=PLAYER)
    set_region(lib, w, 1, tier=OMTier.HOME, military=20.0, economy=90.0, tension=5.0, population=50.0, faction_id=PLAYER)
    set_owner(lib, w, 0, PLAYER)
    set_owner(lib, w, 1, PLAYER)
    for k, mil in enumerate(enemy_military):
        set_region(lib, w, 2 + k, tier=OMTier.HOME, military=mil, economy=40.0, tension=20.0, population=50.0, faction_id=ENEMY)
        set_owner(lib, w, 2 + k, ENEMY)
    last = n - 1
    set_region(lib, w, last, tier=OMTier.HOME, military=other_military, economy=40.0, tension=20.0, population=50.0, faction_id=OTHER)
    set_owner(lib, w, last, OTHER)
    return w


def _snapshot(lib, w):
    return (
        lib.om_mission_get_enemy_faction(w),
        lib.om_mission_get_enemy_power(w),
        lib.om_mission_get_player_parity(w, PLAYER),
        tuple(_player_counts(lib, w)),
        tuple(_units(lib, w)),
    )


def _cover_x(lib, w):
    assert lib.om_map_cover_count(w) >= 1
    x, y, r, h = (ctypes.c_double() for _ in range(4))
    assert lib.om_map_cover_at(w, 0, ctypes.byref(x), ctypes.byref(y), ctypes.byref(r), ctypes.byref(h)) == 1
    return x.value


def test_R_072_08_sets_the_enemy_faction(lib, world_factory):
    """R-072-08: the enemy is the faction the caller passed, even when a stronger
    non-player faction exists (choosing it is the pipe's job)."""
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert lib.om_mission_get_enemy_faction(w) == ENEMY
    factions = {f for f, _ in _units(lib, w)}
    assert factions == {PLAYER, ENEMY}, f"unit factions {factions}"


def test_R_072_08_control_other_faction_is_honoured(lib, world_factory):
    """Positive control: passing the third faction makes it the enemy, so the
    previous test is not satisfied by a hard-coded answer."""
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, OTHER)
    assert lib.om_mission_get_enemy_faction(w) == OTHER
    assert {f for f, _ in _units(lib, w)} == {PLAYER, OTHER}


def test_R_072_07_archetype_is_defensive_stand(lib, world_factory):
    """R-072-07: the mission is a Defensive Stand; the cover disc sits at half the
    Defensive Stand canvas, which differs from the control archetype's."""
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    want = lib.om_map_get_canvas_base_dimension(lib.om_map_archetype_canvas_category(DEFENSIVE_STAND)) / 2.0
    control = lib.om_map_get_canvas_base_dimension(lib.om_map_archetype_canvas_category(CONTROL_ARCHETYPE)) / 2.0
    assert want != control, "fixture: control archetype must use a different canvas"
    assert _cover_x(lib, w) == pytest.approx(want)


def test_R_072_07_control_canvas_tracks_archetype(lib, world_factory):
    """Positive control for the archetype detector: a plain om_mission_setup of the
    control archetype yields a different canvas than the fallback."""
    ref = _world(lib, world_factory)
    lib.om_mission_setup(ref, 0, CONTROL_ARCHETYPE, 0)
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert _cover_x(lib, ref) != _cover_x(lib, w)


def test_R_072_07_region_is_the_one_passed(lib, world_factory):
    """R-072-07: the mission region is the one passed. Parity reads the region's
    capacity, so each region's parity matches a plain Defensive Stand setup there."""
    seen = []
    for region in (0, 1):
        ref = _world(lib, world_factory)
        lib.om_mission_setup(ref, region, DEFENSIVE_STAND, 0)
        w = _world(lib, world_factory)
        lib.om_mission_setup_fallback(w, region, ENEMY)
        got = lib.om_mission_get_player_parity(w, PLAYER)
        assert got == pytest.approx(lib.om_mission_get_player_parity(ref, PLAYER))
        seen.append(got)
    assert seen[0] != seen[1], "control: the two regions must give different parity"


def test_R_074_01_enemy_power_is_strongest_region_military_times_2000(lib, world_factory):
    """R-074-01 default form, A3 ruling 3: P = the enemy faction's strongest
    region's military x 2000 (30.0 here, not the sum 40.0, not the other
    faction's 90.0)."""
    w = _world(lib, world_factory, enemy_military=(30.0, 10.0), other_military=90.0)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert lib.om_mission_get_enemy_power(w) == pytest.approx(30.0 * P_PER_MILITARY)


def test_R_074_01_control_power_tracks_the_strongest_region(lib, world_factory):
    """Positive control: a stronger enemy region changes P."""
    w = _world(lib, world_factory, enemy_military=(30.0, 55.0))
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert lib.om_mission_get_enemy_power(w) == pytest.approx(55.0 * P_PER_MILITARY)


def test_R_074_04_player_budget_is_P_times_parity(lib, world_factory):
    """R-074-04, A3 ruling 3: the player's budget is P * parity. The fill never
    overshoots the budget by more than the 1.15 unit tolerance, and is not far
    below it (a floor of half, loose on purpose: capacity shortfall and the
    parity-floor top-up also act on the force)."""
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    budget = lib.om_mission_get_enemy_power(w) * lib.om_mission_get_player_parity(w, PLAYER)
    assert budget > 0.0
    power = _player_power(lib, w)
    assert power <= budget * OVERSHOOT, f"player power {power} over budget {budget}"
    assert power >= budget * 0.5, f"player power {power} far under budget {budget}"


def test_R_074_04_control_budget_scales_with_enemy_power(lib, world_factory):
    """Positive control: a stronger enemy region gives the player more power."""
    lo = _world(lib, world_factory, enemy_military=(10.0,))
    lib.om_mission_setup_fallback(lo, 0, ENEMY)
    hi = _world(lib, world_factory, enemy_military=(60.0,))
    lib.om_mission_setup_fallback(hi, 0, ENEMY)
    assert _player_power(lib, hi) > _player_power(lib, lo) > 0.0


def test_R_072_08_regions_with_military_field_enemy_units(lib, world_factory):
    """R-072-08: an enemy faction whose regions have military fields units."""
    w = _world(lib, world_factory)
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    enemy_units = [t for f, t in _units(lib, w) if f == ENEMY]
    assert len(enemy_units) > 0
    assert sum(_player_counts(lib, w)) > 0


def test_R_072_08_zero_power_still_fields_one_enemy_unit(lib, world_factory):
    """R-072-08: an enemy faction with P = 0 still fields at least one unit, and
    P is raised to the power of one unit of its cheapest profile (cheapest =
    lowest positive om_unit_power; see the report's ambiguity note)."""
    w = _world(lib, world_factory, enemy_military=(0.0, 0.0))
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert len([1 for f, _ in _units(lib, w) if f == ENEMY]) >= 1
    assert lib.om_mission_get_enemy_power(w) == pytest.approx(_cheapest_unit_power(lib))


def test_R_072_08_sub_unit_power_is_raised_to_one_unit(lib, world_factory):
    """R-072-08: P > 0 but below one cheapest unit would field nothing, so it is
    raised to one unit of the cheapest profile."""
    tiny = _cheapest_unit_power(lib) / P_PER_MILITARY / 2.0
    w = _world(lib, world_factory, enemy_military=(tiny, 0.0))
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert lib.om_mission_get_enemy_power(w) == pytest.approx(_cheapest_unit_power(lib))
    assert len([1 for f, _ in _units(lib, w) if f == ENEMY]) >= 1


def test_R_072_08_control_power_not_raised_when_it_fields_units(lib, world_factory):
    """Positive control for the raise: when P already fields units it is the plain
    military x 2000, never bumped to the cheapest unit's power."""
    w = _world(lib, world_factory, enemy_military=(30.0,))
    lib.om_mission_setup_fallback(w, 0, ENEMY)
    assert lib.om_mission_get_enemy_power(w) == pytest.approx(30.0 * P_PER_MILITARY)
    assert lib.om_mission_get_enemy_power(w) != pytest.approx(_cheapest_unit_power(lib))


@pytest.mark.parametrize("enemy_military", [(30.0, 10.0), (0.0, 0.0)])
def test_R_072_08_deterministic_same_world_same_result(lib, world_factory, enemy_military):
    """Determinism: the same world and call twice give the same enemy, power,
    parity, force and unit list."""
    snaps = []
    for _ in range(2):
        w = _world(lib, world_factory, enemy_military=enemy_military, seed=7)
        lib.om_mission_setup_fallback(w, 0, ENEMY)
        snaps.append(_snapshot(lib, w))
    assert snaps[0] == snaps[1]
    assert snaps[0][1] > 0.0


def test_R_072_08_control_determinism_detector_sees_a_difference(lib, world_factory):
    """Positive control for the determinism comparison: different enemy strength
    gives a different snapshot."""
    a = _world(lib, world_factory, enemy_military=(30.0,), seed=7)
    lib.om_mission_setup_fallback(a, 0, ENEMY)
    b = _world(lib, world_factory, enemy_military=(50.0,), seed=7)
    lib.om_mission_setup_fallback(b, 0, ENEMY)
    assert _snapshot(lib, a) != _snapshot(lib, b)
