"""Python reference, parity changes (Addendum 63 / A176, A177, A179, A180; diagnosis 2026-10-03).

The Python reference is tooling only. Four rulings change it so the C and the Python agree:
  A176 (C2)  the attack-move leash is anchored where the unit stood when it took a target IN RANGE; a sensor
             sighting is a move goal, not a target-with-an-anchor. Same fix as the C's A167 (R-087-05 as amended).
  A177 (C3)  the backswing lock is 10 ticks (0.5 s at 20 ticks per second), not 11 (float residue of 0.5 - 0.05 x 10).
  A179 (W2)  a unit that reaches a waypoint moves toward the next one on that same tick (no standing tick).
  A180 (W3)  a route waypoint's arrival radius is 2 x collision radius = 30 wu, the final one included (R-099-04).
             The Python already does this; the test keeps the pair equal (green now, the C is corrected to match).
Tests 1 to 3 are red on the old behaviour; test 4 and the positive controls are green.
Run from this directory: `python -m pytest -q test_parity_changes.py`.
"""
import math

import pytest

import config
from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field
from unit import FIELD_X, FIELD_Y, FIELD_ATTACK_RANGE, FIELD_ATTACK_TIMER

LEASH = 200.0  # _ATTACK_MOVE_LEASH_SQ in movement.py is 200 x 200; read, not a new threshold


def _engine():
    return TacticalEngine(open_field(), seed=1)


# ---------------------------------------------------------------- A176 / C2: the leash anchor

def _sight_scene(kind, pad, gap0, enemy_kind="Bastion", n=90):
    """Own unit `kind` at (2000,2000) attack-moves north; stationary enemy `gap0` wu north.
    `pad` same-faction dummies are spawned first so the unit's id (hence its targeting cohort turn) varies."""
    e = _engine()
    for i in range(pad):
        e.store.spawn("Raider", 0, 100.0 + 50.0 * i, 100.0)
    r = e.store.spawn(kind, 0, 2000.0, 2000.0)
    b = e.store.spawn(enemy_kind, 1, 2000.0, 2000.0 + gap0)
    e.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[r],
                                params={"target_x": 2000.0, "target_y": 3500.0}))
    rows = []
    for _ in range(n):
        e.step()
        rows.append((float(e.store.data[b, FIELD_Y] - e.store.data[r, FIELD_Y]),
                     float(e.store.data[r, FIELD_Y]),
                     int(e.store.auto_engage_target[r]) == b))
    return rows, float(e.store.data[r, FIELD_ATTACK_RANGE])


@pytest.mark.parametrize("pad", [0, 1, 2, 3])
def test_A176_sighting_at_700_is_no_anchor_target_kept_once_in_range(pad):
    """A176 / C2: a Raider (range 200, sensor 800) sights a stationary enemy at ~700 wu while attack-moving.
    From the first tick end with the enemy inside attack range the unit holds (does not walk on) and the target
    is kept, whatever the unit's targeting cohort turn. The old Python anchors the leash at the sighting, drops
    the target in the same tick, and walks on until its cohort turn finds the enemy in range."""
    rows, rng = _sight_scene("Raider", pad, 700.0)
    first = next(i for i, r in enumerate(rows) if r[0] <= rng)
    assert rows[first][2], "target not held on the tick the enemy came inside attack range"
    assert all(r[2] for r in rows[first:first + 20]), "target dropped while in range and inside the leash"
    assert rows[first + 1][1] == rows[first][1], "unit walked on after the enemy was in range"


def test_A176_positive_control_enemy_taken_in_range_is_kept():
    """Positive control (green on the old rule too): the enemy starts 150 wu away, inside range 200, so no
    sighting is involved; the unit takes it in range, anchors there, and keeps it. Proves the detector reads
    'target held'."""
    rows, rng = _sight_scene("Raider", 0, 150.0, n=30)
    assert all(r[0] <= rng for r in rows)
    assert all(r[2] for r in rows[4:30])


def test_A176_documented_vanguard_range_300_vs_leash_200_drops_target():
    """Documented CHANGE, A188 (R-087-05, R-096-03): the A176 parity case (a Vanguard, range 300, takes the enemy
    in range at ~298 wu, the target is beyond the 200 leash from the anchor, so it drops it and walks on) is
    superseded. The leash now tests the unit's OWN distance from its anchor, never the target's, so the Vanguard
    stops at 300 wu from the enemy, keeps the target on every tick it has the enemy in range (including while the
    enemy is between 200 and 300 wu away), and does not walk on. Pair equal with the C (om_tac_leash_broken)."""
    rows, rng = _sight_scene("Vanguard", 0, 700.0, n=140)
    assert rng == 300.0
    first = next(i for i, r in enumerate(rows) if r[0] <= rng)
    assert rows[first][0] > LEASH, "scene never put the enemy in (200,300]"
    assert all(r[2] for r in rows[first:]), "target dropped while in range and the unit held at its anchor"
    assert rows[-1][1] == rows[first + 1][1], "the Vanguard walked on after the enemy was in range"


# ---------------------------------------------------------------- A177 / C3: backswing is 10 ticks

def _fire_to_move_gap(backswing_sec):
    """Raider attack-moves north behind a Bastion fleeing at 2 wu/tick, ~195 wu ahead. Returns the number of
    ticks from the tick the Raider fires to the first later tick on which it moves."""
    saved = config.ATTACK_BACKSWING_SEC
    config.ATTACK_BACKSWING_SEC = backswing_sec
    try:
        e = _engine()
        r = e.store.spawn("Raider", 0, 2000.0, 2000.0)
        b = e.store.spawn("Bastion", 1, 2000.0, 2195.0)
        e.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[r],
                                    params={"target_x": 2000.0, "target_y": 5000.0}))
        e.command_queue.add(Command(tick=0, type="move", unit_ids=[b],
                                    params={"target_x": 2000.0, "target_y": 5000.0}))
        fire = None
        for t in range(60):
            y0 = float(e.store.data[r, FIELD_Y])
            e.step()
            if fire is None:
                if e.store.data[r, FIELD_ATTACK_TIMER] > 0.7:  # reset to the 0.8 s interval: it fired
                    fire = t
            elif float(e.store.data[r, FIELD_Y]) > y0:
                return t - fire
        return None
    finally:
        config.ATTACK_BACKSWING_SEC = saved


def test_A177_backswing_lock_is_ten_ticks():
    """A177 / C3: 0.5 s at 20 ticks per second is 10 ticks. The C locks the fire tick plus nine more and moves
    on fire + 10. The old Python counts 0.5 down in floats (0.5 - 0.05 x 10 = 6.9e-17, still > 0) and moves on
    fire + 11."""
    assert config.ATTACK_BACKSWING_SEC == 0.5
    assert _fire_to_move_gap(0.5) == 10


def test_A177_positive_control_the_lock_is_measured():
    """Positive control (green now and after): the same scene with no backswing moves sooner than with 0.5 s,
    so the fire-to-move gap really reflects the lock."""
    assert _fire_to_move_gap(0.0) < _fire_to_move_gap(0.5)


# ---------------------------------------------------------------- A179 / W2: no standing tick per waypoint

def _route(start, wps):
    """One Raider walks the waypoint list `wps` (last one is the goal). Returns (positions per tick, ticks until
    the move target is cleared)."""
    e = _engine()
    u = e.store.spawn("Raider", 0, start[0], start[1])
    e.store.set_move_target(u, wps[-1][0], wps[-1][1])
    e.store.waypoints[u] = list(wps)
    pos = [start]
    for t in range(400):
        e.step()
        pos.append((float(e.store.data[u, FIELD_X]), float(e.store.data[u, FIELD_Y])))
        if not e.store.has_move_target[u]:
            return pos, t + 1
    raise AssertionError("route never finished")


def test_A179_two_waypoint_route_loses_no_tick_per_waypoint():
    """A179 / W2: a unit that reaches a waypoint continues toward the next on that same tick. Route
    (1000,1000) -> (1300,1000) -> (1300,1300). Each leg alone takes n ticks including its own arrival tick;
    chained, the arrival tick of the first leg is also the first step of the second, so the total is
    n1 + n2 - 1. The old Python spends the waypoint-arrival tick standing still (n1 + n2)."""
    start, w1, w2 = (1000.0, 1000.0), (1300.0, 1000.0), (1300.0, 1300.0)
    leg1, n1 = _route(start, [w1])
    leg2, n2 = _route(leg1[-1], [w2])
    chained, total = _route(start, [w1, w2])
    assert total <= n1 + n2 - 1
    # no tick of the walk stands still before the final arrival
    still = [i for i in range(1, total) if chained[i] == chained[i - 1]]
    assert still == [], f"standing ticks at {still}"


def test_A179_positive_control_single_leg_matches_its_own_count():
    """Positive control (green now and after): a one-waypoint route has no waypoint hand-over, so chaining it
    adds nothing and the helper's tick count is stable: same route twice gives the same count."""
    _, a = _route((1000.0, 1000.0), [(1300.0, 1000.0)])
    _, b = _route((1000.0, 1000.0), [(1300.0, 1000.0)])
    assert a == b and a > 30


# ---------------------------------------------------------------- A180 / W3: final waypoint radius 30

def test_A180_final_waypoint_arrival_radius_is_two_collision_radii():
    """A180 / W3, R-099-04: the final waypoint's arrival radius is 2 x collision radius = 30 wu in the Python
    as in the C (the C is corrected from 22.5). A Raider (7.5 wu per tick) walking at a waypoint 300 wu away
    stops on the first tick end it is under 30 wu from it: 22.5 wu short, not 15 (the radius of one collision
    radius) and not stopping at 30 exactly. Green now; pins the pair."""
    assert config.UNIT_COLLISION_RADIUS * 2 == 30
    pos, _ = _route((1000.0, 1000.0), [(1300.0, 1000.0)])
    final = pos[-1]
    left = math.hypot(1300.0 - final[0], 1000.0 - final[1])
    assert 22.5 <= left < 30.0
    assert left == pytest.approx(22.5, abs=1e-6)


def test_A180_positive_control_the_walk_does_not_stop_early():
    """Positive control (green now): one tick before the end the unit is still at or beyond 30 wu from the
    waypoint, so the stop is the radius and not an early halt."""
    pos, _ = _route((1000.0, 1000.0), [(1300.0, 1000.0)])
    before = pos[-3]  # the last tick only detects the arrival and does not move
    assert math.hypot(1300.0 - before[0], 1000.0 - before[1]) >= 30.0
