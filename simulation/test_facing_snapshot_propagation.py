"""
Diagnostic — Facing Propagates Through Snapshot + Delta
=======================================================

Bisection step 2 for the launch_todo "Fix unit rotation not working" bug.

If `test_facing_convergence.py` passes (sim updates facing_rad correctly) and
THIS test passes (snapshot + delta carry facing_rad to the wire), then the
bug is in how the Godot renderer consumes facing_rad — most likely in
`scenes/tactical/unit_renderer.gd` around the squad mesh transform.

If THIS test fails, the bug is in `snapshot_serializer.py` — facing_rad isn't
being put on the wire.
"""

import math
import sys

sys.path.insert(0, ".")

import config
import facing
from facing import update_facing, _wrap_angle
from snapshot_serializer import full_snapshot, delta, apply_delta
from tactical_engine import TacticalEngine
from test_maps import open_field
from unit import FIELD_FACING_RAD


def _reset_facing_module():
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


def _make_engine():
    _reset_facing_module()
    eng = TacticalEngine(open_field(), seed=1)
    eng.player_faction = 0
    eng.archetype = "assault"
    eng.region_fields = {"military": 50.0, "tension": 50.0, "economy": 50.0, "population": 50.0}
    eng.objectives = []
    return eng


def test_full_snapshot_includes_facing():
    print("\n--- TEST 1: full_snapshot includes facing_rad ---")
    eng = _make_engine()
    eng.store.spawn("Vanguard", 0, 1000.0, 1000.0)
    eng.store.spawn("Raider", 1, 1300.0, 1000.0)
    eng.store.data[0, FIELD_FACING_RAD] = 1.234

    snap = full_snapshot(eng)
    units = snap.get("units", [])
    _check("snapshot has units", len(units) >= 2, f"len(units)={len(units)}")
    if not units:
        return
    u0 = next((u for u in units if u["uid"] == 0), None)
    _check("unit 0 in snapshot", u0 is not None)
    if u0 is None:
        return
    _check("unit 0 has facing_rad field", "facing_rad" in u0, f"keys={sorted(u0.keys())}")
    _check("snapshot facing_rad matches store (rounded to 4dp)",
           u0.get("facing_rad") == round(1.234, 4),
           f"got={u0.get('facing_rad')}")


def test_delta_emits_facing_change():
    """Step the engine — facing_rad changes — delta carries the update."""
    print("\n--- TEST 2: delta emits facing_rad on change ---")
    eng = _make_engine()
    a = eng.store.spawn("Vanguard", 0, 1000.0, 1000.0)
    b = eng.store.spawn("Raider", 1, 1300.0, 1000.0)
    eng.store.data[a, FIELD_FACING_RAD] = math.pi  # facing west, target is east
    eng.store.auto_engage_target[a] = b

    base = full_snapshot(eng)
    base_units = {u["uid"]: u for u in base["units"]}
    initial_facing = base_units[a]["facing_rad"]

    update_facing(eng.store, config.TACTICAL_TICK_DURATION)
    eng.tick += 1
    new_facing = float(eng.store.data[a, FIELD_FACING_RAD])

    _check("update_facing actually moved the angle",
           abs(new_facing - initial_facing) > 1e-4,
           f"before={initial_facing:.4f} after={new_facing:.4f}")

    d = delta(eng, base)
    updated = d.get("units_updated", [])
    a_update = next((u for u in updated if u["uid"] == a), None)
    _check("delta has an update entry for unit a", a_update is not None)
    if a_update is None:
        return
    _check("delta entry includes facing_rad",
           "facing_rad" in a_update,
           f"keys={sorted(a_update.keys())}")


def test_apply_delta_round_trip_preserves_facing():
    """A snapshot + delta applied = a snapshot whose unit has the new facing."""
    print("\n--- TEST 3: apply_delta round-trip preserves facing ---")
    eng = _make_engine()
    a = eng.store.spawn("Vanguard", 0, 1000.0, 1000.0)
    b = eng.store.spawn("Raider", 1, 1300.0, 1000.0)
    eng.store.data[a, FIELD_FACING_RAD] = math.pi
    eng.store.auto_engage_target[a] = b

    base = full_snapshot(eng)
    update_facing(eng.store, config.TACTICAL_TICK_DURATION)
    eng.tick += 1
    new_facing = round(float(eng.store.data[a, FIELD_FACING_RAD]), 4)

    d = delta(eng, base)
    rebuilt = apply_delta(base, d)
    rebuilt_units = {u["uid"]: u for u in rebuilt["units"]}
    a_rebuilt = rebuilt_units.get(a)
    _check("rebuilt snapshot still has unit a", a_rebuilt is not None)
    if a_rebuilt is None:
        return
    _check("rebuilt facing_rad equals current store value",
           a_rebuilt.get("facing_rad") == new_facing,
           f"rebuilt={a_rebuilt.get('facing_rad')} store={new_facing}")


if __name__ == "__main__":
    test_full_snapshot_includes_facing()
    test_delta_emits_facing_change()
    test_apply_delta_round_trip_preserves_facing()
    print(f"\n{'='*40}\n{_pass} passed, {_fail} failed")
    sys.exit(0 if _fail == 0 else 1)
