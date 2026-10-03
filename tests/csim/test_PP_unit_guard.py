"""PP-unit: the guard stance (E-13 S-096, R-096-05; Architect A170, Addendum 62; contract
docs/northstar/plans/push/pp_contract.md section 6 "The guard call").

R-096-05 (the builder writes it into E-13 with the landing): a unit ordered to guard holds its
position, fires at any target it can shoot in range, never pursues, and resumes nothing; a move,
attack-move or layer order ends the guard. Westley, in the record: "Yes a guard stance is fine".
Engine call: om_command_guard(w, ids, n) (ABI 4, PP-contract). Until it lands every test below
fails naming the missing symbol (a failure, not a skip).

Observables. Position and om_unit_get_destination (has_dest) are exact reads. "Guard in force" is
probed by return fire (R-087-06): an idle unit hit by an attacker beyond its range gets that attacker's
place as a destination (has_dest = 1); a guarding unit must not, so after the same hit it has no
destination and has not moved. Each probe has a positive control on an unguarded (idle) unit.

Scene unit: Vanguard (range 300, sensor 700, speed 80 = 4 wu per tick). Targets are Supply units (never
fire), so only what the test delivers hurts or draws a unit. The choke scenario uses Vanguards on both
sides. Not tested, and flagged in the report: facing after a hit (no getter pinned), a guard order on a
unit with a pending layer transfer (the contract leaves it to the builder).
"""
import ctypes

import pytest

from conftest import OMFeature, OMWorldP
from test_PP_unit_support import (SUPPLY, VANGUARD, attack_move, dest, hp, kill, pos, set_param, spawn,
                                  step, target)

CYCLE = 4  # one full cohort cycle


# ---- the contract call, resolved at call time so a missing symbol fails by name ----

def guard(lib, w, ids):
    if not hasattr(lib, "om_command_guard"):
        pytest.fail("contract missing: om_command_guard is not exported by libouroboros.so "
                    "(PP-contract A170 not landed yet)")
    fn = lib.om_command_guard
    fn = getattr(fn, "raw", fn)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    fn.restype = ctypes.c_int
    ids = list(ids)
    arr = (ctypes.c_uint32 * max(len(ids), 1))(*ids)
    return fn(w, arr, len(ids))


def guard_null_ids(lib, w, n):
    guard(lib, w, [])  # fails by name if the symbol is missing
    fn = getattr(lib.om_command_guard, "raw", lib.om_command_guard)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    return fn(w, None, n)


def move(lib, w, ids, x, y):
    ids = list(ids)
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return lib.om_command_move.raw(w, arr, len(ids), float(x), float(y))


def set_layer(lib, w, ids, layer):
    ids = list(ids)
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    fn = getattr(lib.om_command_set_layer, "raw", lib.om_command_set_layer)
    fn.argtypes = [OMWorldP, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    return fn(w, arr, len(ids), layer)


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def hit(lib, w, victim, attacker, dmg=10.0):
    lib.om_unit_deal_damage(w, attacker, victim, dmg)


def probe_return_fire(lib, w, u, attacker_layer=0):
    """Hit u from a Supply 900 wu away (beyond range 300 and sensor 700), run a cohort cycle, return
    (has_dest, position). An unguarded idle unit gets the attacker's place as its goal (R-087-06)."""
    ux, uy = pos(lib, w, u)
    attacker = spawn(lib, w, SUPPLY, 1, ux + 900.0, uy, layer=attacker_layer)
    hit(lib, w, u, attacker)
    step(lib, w, CYCLE)
    return dest(lib, w, u)[0], pos(lib, w, u)


def vanguard_with_far_friend(lib, w):
    """Vanguard at the origin, id 2 (id 1 a far-off friend), as in the return fire tests."""
    spawn(lib, w, SUPPLY, 0, -9000.0, 0.0)
    return spawn(lib, w, VANGUARD, 0, 0.0, 0.0)


# ---- hold: no walk without a target in reach ----

def test_R_096_05_guard_holds_while_an_enemy_stands_beyond_range(lib, world_factory):
    """Enemy 500 wu away (sensor 700 sees it, range 300 does not reach it). The guard stays exactly
    where it is, and holds nothing as a destination, for 60 ticks."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    assert guard(lib, w, [u]) == 0
    step(lib, w, 60)
    assert pos(lib, w, u) == (0.0, 0.0), f"guard walked to {pos(lib, w, u)}"
    assert dest(lib, w, u)[0] == 0


def test_control_R_096_05_attack_moving_unit_walks_toward_the_same_enemy(lib, world_factory):
    """Positive control for the hold test (green today): the same scene with an attack-move order
    closes on the enemy 500 wu away. The distance test would pass for a unit that cannot walk at all
    without this."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 60)
    assert pos(lib, w, u) != (0.0, 0.0), "an attack-moving unit with an enemy in sight should walk"


def test_R_096_05_guard_does_not_step_toward_an_enemy_that_stays_out_of_range(lib, world_factory):
    """The enemy stays 450 wu off for 120 ticks (two sensor-and-cohort cycles over): no step toward it,
    no change in the distance, and the enemy takes no damage."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 450.0, 0.0)
    before = hp(lib, w, enemy)
    assert guard(lib, w, [u]) == 0
    step(lib, w, 120)
    assert pos(lib, w, u) == (0.0, 0.0)
    assert hp(lib, w, enemy) == before


# ---- fire: a guard shoots what it can reach ----

def _charged_guard_and_far_enemy(lib, w):
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)   # outside sensor while the attack timer charges
    assert guard(lib, w, [u]) == 0
    step(lib, w, 30)
    return u, enemy


def test_R_096_05_guard_fires_at_an_enemy_that_comes_into_range(lib, world_factory):
    """The enemy appears 250 wu away (inside range 300); within 30 ticks the guard has hit it, and has
    not moved."""
    w = world_factory(n_regions=1)
    u, enemy = _charged_guard_and_far_enemy(lib, w)
    before = hp(lib, w, enemy)
    lib.om_unit_teleport(w, enemy, 250.0, 0.0, 0)
    step(lib, w, 30)
    assert hp(lib, w, enemy) < before, "guard should fire at a target in range"
    assert pos(lib, w, u) == (0.0, 0.0)


def test_control_R_096_05_idle_unit_also_fires_so_the_scene_can_hit(lib, world_factory):
    """Positive control for the fire test (green today): the same scene with no order at all lands a shot,
    so a red result above is the guard's fault, not the scene's."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)
    step(lib, w, 30)
    before = hp(lib, w, enemy)
    lib.om_unit_teleport(w, enemy, 250.0, 0.0, 0)
    step(lib, w, 30)
    assert hp(lib, w, enemy) < before


def test_R_096_05_guard_that_loses_its_target_does_not_resume_any_march(lib, world_factory):
    """Resumes nothing: attack-moving to (0, -3000), then guard; the enemy comes into range, is shot,
    and dies. The guard stays put with no goal; the old march is not taken up again."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    enemy = spawn(lib, w, SUPPLY, 1, 5000.0, 0.0)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 10)
    stopped_at = pos(lib, w, u)
    assert guard(lib, w, [u]) == 0
    lib.om_unit_teleport(w, enemy, stopped_at[0] + 250.0, stopped_at[1], 0)
    step(lib, w, 30)
    assert hp(lib, w, enemy) < 100.0, "fixture: the guard should have shot"
    kill(lib, w, enemy)
    step(lib, w, 60)
    assert pos(lib, w, u) == stopped_at
    assert dest(lib, w, u)[0] == 0


# ---- return fire turns a guard but does not move it ----

def test_R_096_05_distant_attacker_does_not_move_a_guard(lib, world_factory):
    """Hit by an attacker beyond range: an unguarded idle unit would take the attacker's place as its goal
    (R-087-06, see the control). A guard keeps its place and has no destination. Plain reading: return fire
    may turn it (no getter pinned here), it never moves it."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    assert guard(lib, w, [u]) == 0
    has, p = probe_return_fire(lib, w, u)
    assert has == 0, "return fire gave a guarding unit a destination"
    assert p == (0.0, 0.0)


def test_control_R_096_05_idle_unit_hit_by_a_distant_attacker_gets_a_goal(lib, world_factory):
    """Positive control for the probe (green today): an idle unit hit the same way has the attacker's
    place as its destination."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    has, _ = probe_return_fire(lib, w, u)
    assert has == 1


def test_R_096_05_guard_hit_from_in_range_fires_back_without_moving(lib, world_factory):
    """Hit by an attacker 280 wu away (in range): the guard targets it (R-087-06, in range) and stays put."""
    w = world_factory(n_regions=1)
    u = vanguard_with_far_friend(lib, w)
    assert guard(lib, w, [u]) == 0
    attacker = spawn(lib, w, SUPPLY, 1, 280.0, 0.0)
    hit(lib, w, u, attacker)
    step(lib, w)
    assert target(lib, w, u) == attacker
    step(lib, w, 40)
    assert pos(lib, w, u) == (0.0, 0.0)


# ---- orders that end the guard ----

def test_R_096_05_a_move_order_ends_the_guard(lib, world_factory):
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    assert guard(lib, w, [u]) == 0
    step(lib, w, 10)
    move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 20)
    assert pos(lib, w, u)[1] < -40.0, f"a moved unit should walk (4 wu per tick); at {pos(lib, w, u)}"
    assert dest(lib, w, u)[0] == 1


def test_R_096_05_an_attack_move_order_ends_the_guard(lib, world_factory):
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    assert guard(lib, w, [u]) == 0
    step(lib, w, 10)
    attack_move(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 20)
    assert pos(lib, w, u)[1] < -40.0, f"an attack-moving unit should walk; at {pos(lib, w, u)}"


def test_R_096_05_a_layer_order_ends_the_guard(lib, world_factory):
    """The guard is ended by om_command_set_layer: after the unit has settled on layer 1 a distant hit
    gives it a goal again. SKIPS (not fails) while om_command_set_layer is still the PP-contract stub (an
    unguarded unit ordered to layer 1 never leaves layer 0)."""
    w = world_factory(n_regions=1)
    probe_unit = spawn(lib, w, VANGUARD, 0, 5000.0, 5000.0)
    set_layer(lib, w, [probe_unit], 1)
    step(lib, w, 600)
    if lib.om_unit_get_layer(w, probe_unit) != 1:
        pytest.skip("om_command_set_layer is not built yet (stub): the layer-order case waits for PP-unit")
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    assert guard(lib, w, [u]) == 0
    set_layer(lib, w, [u], 1)
    step(lib, w, 600)
    assert lib.om_unit_get_layer(w, u) == 1, "fixture: the transfer should have completed"
    has, _ = probe_return_fire(lib, w, u, attacker_layer=1)
    assert has == 1, "after a layer order the unit is no longer guarding: return fire should give it a goal"


@pytest.mark.parametrize("order", ["move", "attack_move"])
def test_R_096_05_guard_order_cancels_a_pending_move(lib, world_factory, order):
    """A unit already walking to (0, -3000) is ordered to guard: it stops where it stands and the goal is
    gone."""
    w = world_factory(n_regions=1)
    u = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    (move if order == "move" else attack_move)(lib, w, [u], 0.0, -3000.0)
    step(lib, w, 10)
    walked_to = pos(lib, w, u)
    assert walked_to[1] < -20.0, "fixture: the unit should be under way"
    assert dest(lib, w, u)[0] == 1
    assert guard(lib, w, [u]) == 0
    assert dest(lib, w, u)[0] == 0, "the guard order should drop the destination"
    step(lib, w, 40)
    assert pos(lib, w, u)[1] == pytest.approx(walked_to[1], abs=4.0 + 1e-9), "at most the step in flight"
    last = pos(lib, w, u)
    step(lib, w, 40)
    assert pos(lib, w, u) == last, "once stopped the guard does not move again"


# ---- group, refusals ----

def test_R_096_05_a_group_of_units_all_guard(lib, world_factory):
    """Three units attack-moved together (a move group) are ordered to guard in one call: none walks, none
    keeps a destination. Control: the same trio left alone walks (green today)."""
    w = world_factory(n_regions=1)
    ids = [spawn(lib, w, VANGUARD, 0, 0.0, 120.0 * k) for k in range(3)]
    attack_move(lib, w, ids, 3000.0, 120.0)
    step(lib, w, 5)
    assert guard(lib, w, ids) == 0
    held = [pos(lib, w, i) for i in ids]
    step(lib, w, 60)
    for i, p in zip(ids, held):
        assert pos(lib, w, i) == p and dest(lib, w, i)[0] == 0, f"unit {i} kept moving"
    # control: an unguarded trio
    w2 = world_factory(n_regions=1)
    ids2 = [spawn(lib, w2, VANGUARD, 0, 0.0, 120.0 * k) for k in range(3)]
    attack_move(lib, w2, ids2, 3000.0, 120.0)
    step(lib, w2, 65)
    assert all(pos(lib, w2, i)[0] > 100.0 for i in ids2), "control: the unguarded group should have marched"


def test_R_096_05_an_unknown_id_is_refused_and_changes_nothing(lib, world_factory):
    """Contract: unknown or dead ids are skipped (the sibling convention), the call returns 0, and no
    other unit is changed on their account: a live unit that is not listed is not guarding (it has a goal
    after a distant hit), a live unit listed with the unknown id is. A NULL id list with n > 0 returns -1."""
    w = world_factory(n_regions=1)
    listed = spawn(lib, w, VANGUARD, 0, 0.0, 0.0)
    unlisted = spawn(lib, w, VANGUARD, 0, 3000.0, 3000.0)
    assert guard(lib, w, [999999, listed]) == 0
    has_listed, _ = probe_return_fire(lib, w, listed)
    has_unlisted, _ = probe_return_fire(lib, w, unlisted)
    assert has_listed == 0, "the live id in the same call should guard"
    assert has_unlisted == 1, "an unlisted unit must not be guarding"
    assert guard(lib, w, [999999]) == 0
    dead = spawn(lib, w, VANGUARD, 0, -3000.0, -3000.0)
    kill(lib, w, dead)
    step(lib, w, 2)
    assert guard(lib, w, [dead]) == 0
    assert guard_null_ids(lib, w, 3) == -1
    assert guard_null_ids(lib, w, 0) == 0


# ---- the choke in miniature ----

def _choke(lib, w):
    """Canvas 3000 x 3000, a wall along y in [1000, 1100) on layer 0 with a gap x in [1400, 1600)."""
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    assert set_param(lib, w, "OM_TP_ROUTE_AROUND_TERRAIN", 1) == 0
    assert lib.om_map_set_canvas(w, 3000.0, 3000.0) == 0
    assert lib.om_map_block_rect(w, 0.0, 1000.0, 1400.0, 1100.0, 0, 0) == 0
    assert lib.om_map_block_rect(w, 1600.0, 1000.0, 3000.0, 1100.0, 0, 0) == 0
    defenders = [spawn(lib, w, VANGUARD, 0, x, 1050.0) for x in (1450.0, 1550.0)]
    attackers = [spawn(lib, w, VANGUARD, 1, x, 1700.0) for x in (1300.0, 1400.0, 1500.0, 1600.0)]
    attack_move(lib, w, attackers, 1500.0, 100.0)
    return defenders, attackers


def test_R_096_05_choke_guard_holds_the_gap_against_a_larger_line(lib, world_factory):
    """Two defenders in the gap, guarding, against four attackers marching through it: after 150 ticks the
    defenders have not moved, are alive, hold no goal, no attacker is south of the wall, and the attackers
    took damage (the guard fired)."""
    w = world_factory(n_regions=1)
    defenders, attackers = _choke(lib, w)
    starts = [pos(lib, w, d) for d in defenders]
    assert guard(lib, w, defenders) == 0
    step(lib, w, 150)
    for d, p in zip(defenders, starts):
        assert pos(lib, w, d) == p, f"defender {d} left the gap: {pos(lib, w, d)}"
        assert dest(lib, w, d)[0] == 0
        assert hp(lib, w, d) > 0.0
    assert all(pos(lib, w, a)[1] >= 1100.0 for a in attackers), "an attacker got through the gap"
    assert min(hp(lib, w, a) for a in attackers) < 500.0, "the guard should have fired on the line"


def test_control_R_096_05_choke_attack_moving_defenders_walk_out_through_the_gap(lib, world_factory):
    """Positive control for the choke test (green today): the same scene with the defenders attack-moving
    toward the line walk out of the gap, to the far side of the wall (y >= 1100)."""
    w = world_factory(n_regions=1)
    defenders, attackers = _choke(lib, w)
    attack_move(lib, w, defenders, 1500.0, 2500.0)
    step(lib, w, 150)
    assert any(pos(lib, w, d)[1] >= 1100.0 for d in defenders if hp(lib, w, d) > 0.0), \
        "an attack-moving defender should have walked out through the gap"
