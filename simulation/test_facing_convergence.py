"""
Diagnostic — Facing Convergence Pipeline Test
=============================================

Bisection harness for the launch_todo "Fix unit rotation not working" bug.

If THIS test passes, the sim-side facing pipeline is correct — meaning
update_facing() does what facing.py docstring claims. Then the bug is
downstream (snapshot delta consumption, renderer mesh transform, or the
squad-mesh-to-facing-rad wiring in unit_renderer.gd).

If THIS test fails, the bug is in facing.py / config rotation speeds /
how auto_engage_target or move_target are read.

Output legend:
  [PASS] / [FAIL] — assertion result
  [INFO]          — diagnostic value, no pass/fail
"""

import math
import sys

sys.path.insert(0, ".")

import config
import facing
from facing import update_facing, _wrap_angle, _shortest_arc, TWO_PI
from unit import (
    UnitStore, FIELD_X, FIELD_Y, FIELD_FACING_RAD, MAX_UNITS,
    CATEGORY_LINE,
)


def _reset_facing_module():
    """update_facing() carries module-level state across calls — reset for each test."""
    facing._facing_log_counter = 0
    facing._prev_initialized = False
    facing._prev_x[:] = 0.0
    facing._prev_y[:] = 0.0


_pass = 0
_fail = 0


def _check(name, ok, detail=""):
    global _pass, _fail
    tag = "[PASS]" if ok else "[FAIL]"
    if ok:
        _pass += 1
    else:
        _fail += 1
    print(f"{tag} {name}{('  ' + detail) if detail else ''}")
    return ok


def test_engage_target_convergence():
    """Unit A at origin, target B 200px east. A starts facing west (pi).
    A's auto_engage_target points at B. After enough ticks, A should face east (~0)."""
    print("\n--- TEST 1: convergence on auto_engage_target ---")
    _reset_facing_module()
    store = UnitStore()
    a = store.spawn("Vanguard", 0, 0.0, 0.0)
    b = store.spawn("Raider", 1, 200.0, 0.0)
    assert a == 0 and b == 1
    store.data[a, FIELD_FACING_RAD] = math.pi  # facing west
    store.auto_engage_target[a] = b

    dt = config.TACTICAL_TICK_DURATION
    rot_speed = config.FACING_ROTATION_SPEED_LINE  # Vanguard is line per current config
    expected_ticks = int(math.ceil(math.pi / (rot_speed * dt))) + 2
    print(f"[INFO] dt={dt} rot_speed={rot_speed} expected_ticks≈{expected_ticks}")

    for _ in range(expected_ticks * 2):
        update_facing(store, dt)

    final = store.data[a, FIELD_FACING_RAD]
    final_wrapped = _wrap_angle(final)
    err = abs(_shortest_arc(final_wrapped, 0.0))
    _check("facing converges to atan2(target − unit) ≈ 0",
           err < 0.05,
           f"final={final_wrapped:.4f} err={err:.4f} rad")


def test_move_target_when_no_engage():
    """No engage target. A has a move target due-north. A should rotate to face north (pi/2)."""
    print("\n--- TEST 2: convergence on move target ---")
    _reset_facing_module()
    store = UnitStore()
    a = store.spawn("Vanguard", 0, 100.0, 100.0)
    store.data[a, FIELD_FACING_RAD] = 0.0
    store.has_move_target[a] = True
    store.target_x[a] = 100.0
    store.target_y[a] = 1000.0

    dt = config.TACTICAL_TICK_DURATION
    rot_speed = config.FACING_ROTATION_SPEED_LINE
    expected_ticks = int(math.ceil((math.pi / 2) / (rot_speed * dt))) + 2

    for _ in range(expected_ticks * 2):
        update_facing(store, dt)

    final = _wrap_angle(store.data[a, FIELD_FACING_RAD])
    err = abs(_shortest_arc(final, math.pi / 2))
    _check("facing converges to atan2(move target dy, dx) ≈ pi/2",
           err < 0.05,
           f"final={final:.4f} err={err:.4f} rad")


def test_rotation_speed_cap_strike_faster_than_siege():
    """Siege should never out-rotate Strike — config invariant + behavior check."""
    print("\n--- TEST 3: rotation speed cap ordering ---")
    _check("config: strike > line > siege",
           config.FACING_ROTATION_SPEED_STRIKE
           > config.FACING_ROTATION_SPEED_LINE
           > config.FACING_ROTATION_SPEED_SIEGE,
           f"S={config.FACING_ROTATION_SPEED_STRIKE} L={config.FACING_ROTATION_SPEED_LINE} G={config.FACING_ROTATION_SPEED_SIEGE}")

    _reset_facing_module()
    store = UnitStore()
    strike = store.spawn("Raider", 0, 0.0, 0.0)
    siege = store.spawn("Bombard", 0, 0.0, 0.0)
    enemy = store.spawn("Vanguard", 1, 200.0, 0.0)

    for u in (strike, siege):
        store.data[u, FIELD_FACING_RAD] = math.pi
        store.auto_engage_target[u] = enemy

    dt = config.TACTICAL_TICK_DURATION
    update_facing(store, dt)
    update_facing(store, dt)

    strike_arc = abs(_shortest_arc(_wrap_angle(store.data[strike, FIELD_FACING_RAD]), 0.0))
    siege_arc = abs(_shortest_arc(_wrap_angle(store.data[siege, FIELD_FACING_RAD]), 0.0))
    # Strike has rotated MORE toward target after 2 ticks => smaller residual arc.
    _check("after 2 ticks: strike has smaller residual arc than siege",
           strike_arc < siege_arc,
           f"strike_residual={strike_arc:.4f} siege_residual={siege_arc:.4f}")


def test_no_target_no_velocity_holds_facing():
    """Stationary unit with no engage and no move target keeps current facing."""
    print("\n--- TEST 4: stationary holds facing ---")
    _reset_facing_module()
    store = UnitStore()
    a = store.spawn("Vanguard", 0, 500.0, 500.0)
    initial = 1.234
    store.data[a, FIELD_FACING_RAD] = initial

    for _ in range(10):
        update_facing(store, config.TACTICAL_TICK_DURATION)

    final = store.data[a, FIELD_FACING_RAD]
    _check("facing unchanged when no target and no velocity",
           abs(final - initial) < 1e-9,
           f"initial={initial} final={final}")


if __name__ == "__main__":
    test_engage_target_convergence()
    test_move_target_when_no_engage()
    test_rotation_speed_cap_strike_faster_than_siege()
    test_no_target_no_velocity_holds_facing()
    print(f"\n{'='*40}\n{_pass} passed, {_fail} failed")
    sys.exit(0 if _fail == 0 else 1)
