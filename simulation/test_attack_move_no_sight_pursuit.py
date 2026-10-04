"""Python reference: an attack-moving unit holds its slot and route until it can SHOOT, not until it sees
(R-087-04, R-087-05, R-096-02, R-096-03; ruling A199; the C twin is tests/csim/test_PP_attack_move_no_sight_pursuit.py).
Rule marked for playtest review, A199.

Old rule (damage.py update_targeting, the `if store.attack_moving[uid]` sensor-pursuit block): an attack-mover with
no enemy in range makes the nearest VISIBLE enemy its move target (set_move_target) and its auto_engage_target.
New rule: slot and route kept; halt and fire in attack range; an acquired target is pursued under the leash.
The Python has no switch for this: the baseline test lives in the C twin only.
Scenes: Vanguard (range 300, sensor 700, speed 80), idle Raider (range 200, sensor 800, hp 250) of faction 1.
Slot arrival radius = config.ARRIVAL_TOLERANCE_MULT x config.UNIT_COLLISION_RADIUS, not a free tolerance.
Run from this directory: `python -m pytest -q test_attack_move_no_sight_pursuit.py`.
"""
import math

from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field
from unit import FIELD_X, FIELD_Y, FIELD_HP
import config

ARRIVAL = config.ARRIVAL_TOLERANCE_MULT * config.UNIT_COLLISION_RADIUS
VAN_RANGE = 300.0
LINE_N, SPACING = 32, 40.0
LINE_X0, LINE_Y = 1000.0, 1000.0
CLICK = (1620.0, 3000.0)
TICKS = 700


def _d(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def _xy(e, uid):
    return float(e.store.data[uid, FIELD_X]), float(e.store.data[uid, FIELD_Y])


def _attack_move(e, ids, x, y):
    e.command_queue.add(Command(tick=e.tick if hasattr(e, "tick") else 0, type="attack_move", unit_ids=list(ids),
                                params={"target_x": x, "target_y": y}))


def _line(enemy_xy):
    e = TacticalEngine(open_field(), seed=1)
    ids = [e.store.spawn("Vanguard", 0, LINE_X0 + i * SPACING, LINE_Y) for i in range(LINE_N)]
    enemy = e.store.spawn("Raider", 1, *enemy_xy)
    # TD-PP-A199-line-fixture: 32 units 40 wu apart sit 620 wu from their centroid, past MAGIC_BOX_SPREAD_RADIUS
    # (450, R-095-03), so one group order drops every slot to the raw click. Issue it as two chunks of 16 (300 wu from
    # their own centroid), each to the click plus its chunk's offset from the line's centroid (the skill lab's way).
    half = LINE_N // 2
    cx = LINE_X0 + (LINE_N - 1) * SPACING / 2.0
    for chunk in (ids[:half], ids[half:]):
        cc = sum(_xy(e, u)[0] for u in chunk) / len(chunk)
        _attack_move(e, chunk, CLICK[0] + cc - cx, CLICK[1])
    e.step()
    slots = {u: (float(e.store.target_x[u]), float(e.store.target_y[u])) for u in ids}
    assert len({(round(x), round(y)) for x, y in slots.values()}) == LINE_N, "fixture: slots collapsed to the click (R-095-03)"
    assert all(e.store.has_move_target[u] for u in ids), "fixture: a line unit has no slot after the group attack-move"
    return e, ids, enemy, slots


def _run_line(enemy_xy):
    """(max slot miss at the end, closest approach of any unit to the enemy, enemy hp, max slot miss on the tick
    the enemy first lost hp or None)."""
    e, ids, enemy, slots = _line(enemy_xy)
    ex, ey = _xy(e, enemy)
    closest, at_hit = 1e9, None
    for _ in range(TICKS):
        e.step()
        closest = min(closest, min(_d(*_xy(e, u), ex, ey) for u in ids))
        if at_hit is None and float(e.store.data[enemy, FIELD_HP]) < 250.0:
            at_hit = max(_d(*_xy(e, u), *slots[u]) for u in ids)
    miss = max(_d(*_xy(e, u), *slots[u]) for u in ids)
    return miss, closest, float(e.store.data[enemy, FIELD_HP]), at_hit


def test_R_087_04_A199_a_32_unit_line_reaches_its_slots_with_the_shape_intact_past_a_seen_enemy():
    """R-087-04 / R-096-02 / A199: a 32-unit line attack-moves with an idle Raider 450 wu off its east flank (seen,
    never in attack range 300). Every unit ends within the arrival radius of its own slot and nothing fires.
    RED now: update_targeting sets the seen enemy as each unit's move target; the line walks off to it."""
    east = LINE_X0 + (LINE_N - 1) * SPACING
    miss, closest, ehp, _ = _run_line((east + 450.0, 2000.0))
    assert miss <= ARRIVAL, "a unit ended %.1f wu from its slot (arrival radius %.1f): the line walked off to the seen enemy" % (miss, ARRIVAL)
    assert closest > VAN_RANGE and ehp == 250.0, "fixture: the enemy was inside attack range (%.0f wu) or hit" % closest


def test_control_R_087_04_A199_the_slot_miss_detector_trips_when_the_route_leads_to_the_enemy():
    """Positive control (green now and after): the enemy stands ON the route in range of the passing units; they
    halt and fire short of their slots, so the same slot-miss reading, taken on the tick the enemy first loses hp
    (it dies before the end and the line resumes), is over the arrival radius."""
    _, closest, ehp, at_hit = _run_line((LINE_X0 + 15.5 * SPACING, 2000.0))
    assert closest <= VAN_RANGE and ehp < 250.0, "fixture: the line never engaged the enemy on its route"
    assert at_hit is not None and at_hit > ARRIVAL, "control: units were firing but still read as at their slots (miss %s)" % at_hit


def _lone(enemy_xy):
    e = TacticalEngine(open_field(), seed=1)
    u = e.store.spawn("Vanguard", 0, 2000.0, 500.0)
    b = e.store.spawn("Raider", 1, *enemy_xy)
    _attack_move(e, [u], 2000.0, 3000.0)
    return e, u, b


def _goal(e, u):
    return float(e.store.target_x[u]), float(e.store.target_y[u])


def _diverted(e, u, goal=(2000.0, 3000.0)):
    return bool(e.store.has_move_target[u]) and _d(*_goal(e, u), *goal) > 1e-6


def test_R_087_04_A199_a_lone_attack_mover_keeps_its_goal_and_takes_no_target_for_an_enemy_it_only_sees():
    """R-087-04 / A199: with an idle Raider 450 wu to its side (seen, out of range) the Vanguard keeps its march
    goal, holds no target for 60 ticks, and drifts sideways by no more than the arrival radius.
    RED now: update_targeting sets the target and the move target to the Raider."""
    e, u, b = _lone((2450.0, 800.0))
    for _ in range(60):
        e.step()
        assert int(e.store.auto_engage_target[u]) < 0, "took the enemy it only sees as its target"
        assert not _diverted(e, u), "its goal was replaced by the seen enemy's position"
    assert abs(_xy(e, u)[0] - 2000.0) <= ARRIVAL, "it drifted sideways toward the enemy"


def test_control_R_087_04_A199_the_diverted_goal_detector_reads_a_changed_order():
    """Positive control (green now and after): with no enemy in sensor range the goal is the click; a new
    attack-move to another point then reads as diverted, so a True above would be a real change of goal."""
    e, u, b = _lone((3900.0, 3900.0))
    e.step()
    assert not _diverted(e, u)
    _attack_move(e, [u], 2500.0, 3000.0)
    e.step()
    assert _diverted(e, u)


def test_R_087_04_A199_halt_and_fire_when_an_enemy_is_in_attack_range():
    """R-087-04 / A199 guard (green now and after): an idle Raider 250 wu ahead is inside range 300. The unit
    halts (same place at tick 40 and 60), the enemy loses hp, and the unit holds it as its target."""
    e, u, b = _lone((2000.0, 750.0))
    for _ in range(40):
        e.step()
    p40 = _xy(e, u)
    for _ in range(20):
        e.step()
    assert _d(*p40, *_xy(e, u)) <= 0.5, "the unit kept walking with an enemy in attack range"
    assert float(e.store.data[b, FIELD_HP]) < 250.0, "it halted but never fired"
    assert int(e.store.auto_engage_target[u]) == b


def test_R_087_05_A199_an_acquired_target_that_walks_out_of_range_stays_held_under_the_leash():
    """R-087-05 / A199 guard (green now and after): after acquiring a Raider 250 ahead, the Raider is moved to 350
    ahead (out of range). While the unit is inside 200 wu of its anchor it keeps the target on every tick of the
    next 10, on the same anchor."""
    e, u, b = _lone((2000.0, 750.0))
    for _ in range(40):
        e.step()
        if int(e.store.auto_engage_target[u]) == b and e.store.engage_anchor_set[u]:
            break
    assert int(e.store.auto_engage_target[u]) == b, "fixture: no acquisition"
    ax, ay = float(e.store.engage_anchor_x[u]), float(e.store.engage_anchor_y[u])
    ux, uy = _xy(e, u)
    e.store.data[b, FIELD_X] = ux
    e.store.data[b, FIELD_Y] = uy + 350.0
    for _ in range(10):
        e.step()
        assert _d(*_xy(e, u), ax, ay) < 200.0
        assert int(e.store.auto_engage_target[u]) == b, "the acquired target was dropped while inside the leash"
        assert (float(e.store.engage_anchor_x[u]), float(e.store.engage_anchor_y[u])) == (ax, ay)
    # R-087-04: "pursues an acquired target that leaves that range under the leash": it walks back into range.
    for _ in range(40):
        e.step()
    assert _d(*_xy(e, u), *_xy(e, b)) <= VAN_RANGE, "it held its place and never pursued the target that left its range"
    assert _d(*_xy(e, u), ax, ay) < 200.0 and int(e.store.auto_engage_target[u]) == b


def test_R_087_04_A199_a_lone_attack_mover_resumes_its_route_after_the_fight():
    """R-087-04 / A199: a Vanguard kills a weak Raider (hp 20) in range on its way, then continues and ends within
    the arrival radius of its destination."""
    e, u, b = _lone((2000.0, 750.0))
    e.store.data[b, FIELD_HP] = 20.0
    for _ in range(TICKS + 200):
        e.step()
    assert not e.store.alive[b] or e.store.data[b, FIELD_HP] <= 0, "fixture: the enemy never died"
    assert _d(*_xy(e, u), 2000.0, 3000.0) <= ARRIVAL, "it did not resume its route: ended %s" % (_xy(e, u),)


def test_R_087_04_A199_an_idle_unit_never_walks_toward_a_seen_enemy():
    """Guard (green now and after): a unit with no order stays put with an enemy in sensor range, out of attack
    range, and takes no target."""
    e = TacticalEngine(open_field(), seed=1)
    u = e.store.spawn("Vanguard", 0, 2000.0, 500.0)
    e.store.spawn("Raider", 1, 2450.0, 800.0)
    for _ in range(60):
        e.step()
    assert _d(*_xy(e, u), 2000.0, 500.0) <= 0.5
    assert int(e.store.auto_engage_target[u]) < 0
