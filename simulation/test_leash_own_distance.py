"""Python reference: the attack-move leash measures the PURSUER, never the target (R-087-05, R-096-03,
ruling A188, Addendum 64/65; the C twin is tests/csim/test_PP_leash_own_distance.py).

Old rule (movement.py `_update_attack_move_state`): the target's distance from the anchor over 200 wu drops
the target, so a Vanguard (range 300) that takes a target at 294 wu drops it the next tick (pinned today by
test_parity_changes.py::test_A176_documented_vanguard_range_300_vs_leash_200_drops_target, which A188
re-pins as a documented change). New rule: the unit's own distance from its anchor is tested.
Positive controls are green on the old rule and must stay green.
Run from this directory: `python -m pytest -q test_leash_own_distance.py`.
"""
import pytest

from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field
from unit import FIELD_X, FIELD_Y, FIELD_HP

LEASH = 200.0  # _ATTACK_MOVE_LEASH_SQ in movement.py is 200 x 200; read, not a new threshold
X0, Y0 = 2000.0, 2000.0


def _acquired(kind="Vanguard", enemy_gap=150.0):
    """`kind` at (X0, Y0) attack-moves north; a stationary Bastion `enemy_gap` wu north. Steps until the
    unit holds it (a cohort cycle). Returns (engine, unit, enemy, anchor)."""
    e = TacticalEngine(open_field(), seed=1)
    r = e.store.spawn(kind, 0, X0, Y0)
    b = e.store.spawn("Bastion", 1, X0, Y0 + enemy_gap)
    e.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[r],
                                params={"target_x": X0, "target_y": 3500.0}))
    for _ in range(40):
        e.step()
        if int(e.store.auto_engage_target[r]) == b and e.store.engage_anchor_set[r]:
            return e, r, b, (float(e.store.engage_anchor_x[r]), float(e.store.engage_anchor_y[r]))
    pytest.fail("fixture: the unit never took the target")


def _place(e, uid, x, y):
    e.store.data[uid, FIELD_X] = x
    e.store.data[uid, FIELD_Y] = y


def _kept(e, r, b, anchor):
    """The target is still held AND still on the original anchor. The Python can drop and re-take an in-range
    target within one step (a re-take re-anchors where the unit stands), so 'held' alone cannot see a drop."""
    return (int(e.store.auto_engage_target[r]) == b and bool(e.store.engage_anchor_set[r])
            and (float(e.store.engage_anchor_x[r]), float(e.store.engage_anchor_y[r])) == anchor)


def test_A188_vanguard_with_target_294_from_its_anchor_holds_and_fires_until_it_dies():
    """R-087-05 / A188: a Vanguard holds a Bastion 294 wu from its anchor (beyond 200, inside range 300). At
    its anchor it never drops it for the leash: held on every tick until the target dies, the unit does not
    move. RED on the old rule: the target (294 wu from the anchor) is dropped the next tick."""
    e, r, b, (ax, ay) = _acquired()
    _place(e, b, ax, ay + 294.0)
    e.store.data[b, FIELD_HP] = 15.0   # a short fight; not a rule number
    held = 0
    for _ in range(400):
        if e.store.data[b, FIELD_HP] <= 0 or not e.store.alive[b]:
            break
        assert _kept(e, r, b, (ax, ay)), "target dropped for the leash while holding at the anchor (held %d ticks)" % held
        held += 1
        e.step()
    assert not e.store.alive[b] or e.store.data[b, FIELD_HP] <= 0, "the held target never died"
    assert held >= 2
    assert abs(float(e.store.data[r, FIELD_Y]) - ay) <= 1.0 and abs(float(e.store.data[r, FIELD_X]) - ax) <= 1.0


def test_A188_unit_inside_200_of_its_anchor_keeps_a_target_far_from_the_anchor():
    """R-087-05 / A188 boundary: the unit stands 199 wu from its anchor, the target 350 wu from it (151 wu from
    the unit, in range). Still held on the same anchor after the next tick. RED on the old rule."""
    e, r, b, (ax, ay) = _acquired()
    _place(e, r, ax, ay + 199.0)
    _place(e, b, ax, ay + 350.0)
    e.step()
    assert _kept(e, r, b, (ax, ay)), "a unit 199 wu from its anchor dropped its target for the leash"


def test_A188_positive_control_unit_over_200_from_its_anchor_drops_its_target():
    """R-096-03 / A188 positive control (green on the old rule, must stay green): the unit stands 201 wu from
    its anchor, the target 350 wu from it (in range). The unit itself is past the leash: it drops the target (the Python may re-take it in range at once, on a new anchor)."""
    e, r, b, (ax, ay) = _acquired()
    _place(e, r, ax, ay + 201.0)
    _place(e, b, ax, ay + 350.0)
    e.step()
    assert not _kept(e, r, b, (ax, ay)), "a unit 201 wu from its anchor kept its target"


def test_A188_range_at_most_200_behaves_as_before():
    """Guard (green before and after): a Raider (range 200) holds a Bastion 150 wu ahead without moving, and
    drops it when it stands 201 wu from its anchor (target 250 wu from the anchor, in range)."""
    e, r, b, (ax, ay) = _acquired("Raider")
    e.step()
    assert _kept(e, r, b, (ax, ay))
    assert abs(float(e.store.data[r, FIELD_Y]) - ay) <= 1.0
    _place(e, r, ax, ay + 201.0)
    _place(e, b, ax, ay + 250.0)
    e.step()
    assert not _kept(e, r, b, (ax, ay))


def test_A188_the_leash_is_a_real_distance_not_a_constant():
    """Positive control for the 199/201 pair: LEASH read from this file is the 200 wu the code uses."""
    assert LEASH == 200.0
