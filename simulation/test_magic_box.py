"""
Magic Box Spread Threshold — Regression Tests
==============================================
Verifies that apply_group_move abandons formation offsets when units are
scattered beyond MAGIC_BOX_SPREAD_RADIUS, and preserves them when tight.

TEST 1  Tight group → formation offsets preserved
TEST 2  Scattered group → all targets converge to click point
TEST 3  Boundary: unit exactly at threshold → formation preserved
TEST 4  Boundary: unit 1wu beyond threshold → scattered
TEST 5  Single unit → early-return path, no move_group
TEST 6  FORMATION_MOVE_ENABLED=False → no move_group
TEST 7  Config constant exists and is positive
TEST 8  Scattered group still registers a move_group
"""

import sys
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_engine import TacticalEngine
from test_maps import open_field
from movement import apply_group_move


def _banner(label):
    print(f"\n{'─' * 62}")
    print(f"  {label}")
    print('─' * 62)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _info(label, value):
    print(f"  [INFO]  {label}: {value}")


def _make_engine():
    return TacticalEngine(open_field())


def test_tight_group():
    _banner("TEST 1  Tight group → formation offsets preserved")
    engine = _make_engine()
    uids = []
    for i in range(10):
        uid = engine.store.spawn("Raider", 0, 500.0 + i * 55.0, 500.0)
        uids.append(uid)

    apply_group_move(engine.store, uids, 2000.0, 2000.0)

    gid = engine.store.move_group_id[uids[0]]
    offsets = engine.store.move_groups[gid]["offsets"]
    has_nonzero = any(abs(ox) + abs(oy) > 1.0 for ox, oy in offsets.values())

    results = []
    results.append(_result("move_group created", gid >= 0, f"gid={gid}"))
    results.append(_result("offsets are non-zero (formation preserved)", has_nonzero))
    return all(results)


def test_scattered_group():
    _banner("TEST 2  Scattered group → all targets converge to click point")
    engine = _make_engine()
    positions = [(0, 0), (0, 2000), (2000, 0), (2000, 2000), (1000, 1000)]
    uids = []
    for x, y in positions:
        uid = engine.store.spawn("Raider", 0, float(x), float(y))
        uids.append(uid)

    tx, ty = 3000.0, 3000.0
    apply_group_move(engine.store, uids, tx, ty)

    gid = engine.store.move_group_id[uids[0]]
    offsets = engine.store.move_groups[gid]["offsets"]
    all_zero = all(abs(ox) + abs(oy) < 0.01 for ox, oy in offsets.values())
    all_target_match = all(
        abs(engine.store.target_x[uid] - tx) < 0.01 and
        abs(engine.store.target_y[uid] - ty) < 0.01
        for uid in uids
    )

    results = []
    results.append(_result("all offsets are (0, 0)", all_zero))
    results.append(_result("all unit targets = click point", all_target_match))
    return all(results)


def test_boundary_at_threshold():
    _banner("TEST 3  Boundary: unit exactly at threshold → formation preserved")
    engine = _make_engine()
    radius = config.MAGIC_BOX_SPREAD_RADIUS
    # With 2 units, centroid is midpoint. Place them 2*radius apart so
    # each unit is exactly `radius` from the centroid (not beyond — strict >).
    uid_a = engine.store.spawn("Raider", 0, 500.0, 500.0)
    uid_b = engine.store.spawn("Raider", 0, 500.0 + 2.0 * radius, 500.0)

    apply_group_move(engine.store, [uid_a, uid_b], 2000.0, 2000.0)

    gid = engine.store.move_group_id[uid_a]
    offsets = engine.store.move_groups[gid]["offsets"]
    has_nonzero = any(abs(ox) + abs(oy) > 1.0 for ox, oy in offsets.values())

    return _result("offsets non-zero at exact threshold (strict >)", has_nonzero)


def test_boundary_beyond_threshold():
    _banner("TEST 4  Boundary: unit 1wu beyond threshold → scattered")
    engine = _make_engine()
    radius = config.MAGIC_BOX_SPREAD_RADIUS
    # With 2 units, centroid is midpoint. Place them 2*(radius+1) apart so
    # each unit is (radius+1) from the centroid.
    uid_a = engine.store.spawn("Raider", 0, 500.0, 500.0)
    uid_b = engine.store.spawn("Raider", 0, 500.0 + 2.0 * (radius + 1.0), 500.0)

    apply_group_move(engine.store, [uid_a, uid_b], 2000.0, 2000.0)

    gid = engine.store.move_group_id[uid_a]
    offsets = engine.store.move_groups[gid]["offsets"]
    all_zero = all(abs(ox) + abs(oy) < 0.01 for ox, oy in offsets.values())

    return _result("all offsets zero beyond threshold", all_zero)


def test_single_unit():
    _banner("TEST 5  Single unit → early-return path, no move_group")
    engine = _make_engine()
    uid = engine.store.spawn("Raider", 0, 500.0, 500.0)

    apply_group_move(engine.store, [uid], 2000.0, 2000.0)

    has_group = bool(engine.store.move_groups)
    has_target = engine.store.has_move_target[uid]

    results = []
    results.append(_result("no move_group created", not has_group))
    results.append(_result("unit has move target", has_target))
    return all(results)


def test_formation_disabled():
    _banner("TEST 6  FORMATION_MOVE_ENABLED=False → no move_group")
    engine = _make_engine()
    uids = []
    for i in range(5):
        uid = engine.store.spawn("Raider", 0, 500.0 + i * 30.0, 500.0)
        uids.append(uid)

    old_val = config.FORMATION_MOVE_ENABLED
    config.FORMATION_MOVE_ENABLED = False
    try:
        apply_group_move(engine.store, uids, 2000.0, 2000.0)
        has_group = bool(engine.store.move_groups)
        all_have_target = all(engine.store.has_move_target[uid] for uid in uids)
    finally:
        config.FORMATION_MOVE_ENABLED = old_val

    results = []
    results.append(_result("no move_group created", not has_group))
    results.append(_result("all units have move target", all_have_target))
    return all(results)


def test_config_exists():
    _banner("TEST 7  Config constant exists and is positive")
    results = []
    results.append(_result("MAGIC_BOX_SPREAD_RADIUS exists",
                           hasattr(config, "MAGIC_BOX_SPREAD_RADIUS")))
    results.append(_result("MAGIC_BOX_SPREAD_RADIUS > 0",
                           config.MAGIC_BOX_SPREAD_RADIUS > 0,
                           f"value={config.MAGIC_BOX_SPREAD_RADIUS}"))
    return all(results)


def test_scattered_registers_group():
    _banner("TEST 8  Scattered group still registers a move_group")
    engine = _make_engine()
    positions = [(0, 0), (2000, 2000), (3500, 500)]
    uids = []
    for x, y in positions:
        uid = engine.store.spawn("Raider", 0, float(x), float(y))
        uids.append(uid)

    tx, ty = 2000.0, 1000.0
    apply_group_move(engine.store, uids, tx, ty)

    results = []
    results.append(_result("move_groups has 1 entry", len(engine.store.move_groups) == 1,
                           f"count={len(engine.store.move_groups)}"))

    gid = next(iter(engine.store.move_groups))
    group = engine.store.move_groups[gid]
    results.append(_result("group target matches click point",
                           group["target_x"] == tx and group["target_y"] == ty))
    results.append(_result("moving set contains all units",
                           len(group["moving"]) == len(uids)))
    return all(results)


if __name__ == "__main__":
    results = [
        test_tight_group(),
        test_scattered_group(),
        test_boundary_at_threshold(),
        test_boundary_beyond_threshold(),
        test_single_unit(),
        test_formation_disabled(),
        test_config_exists(),
        test_scattered_registers_group(),
    ]

    total = len(results)
    n_pass = sum(results)
    print(f"\n{'═' * 62}")
    print(f"  Magic Box tests: {n_pass}/{total} passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
