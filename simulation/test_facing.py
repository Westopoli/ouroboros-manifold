import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_FACING_RAD, CATEGORY_NAMES
from tactical_engine import TacticalEngine
from test_maps import open_field

TICK_COUNT = 200
DT = config.TACTICAL_TICK_DURATION
ROTATION_CAPS = {
    "Strike": config.FACING_ROTATION_SPEED_STRIKE,
    "Line": config.FACING_ROTATION_SPEED_LINE,
    "Siege": config.FACING_ROTATION_SPEED_SIEGE,
}


def wrap(a):
    a = a % (2 * math.pi)
    return a if a >= 0 else a + 2 * math.pi


def angular_diff(a, b):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return abs(d)


print("=" * 70)
print("  Stage 12.5 Checkpoint A — Unit Facing Verification (50v50)")
print("=" * 70)

tmap = open_field()
engine = TacticalEngine(tmap, seed=42)
engine.player_faction = 0
store = engine.store

unit_types = list(config.UNIT_STATS.keys())
for i in range(50):
    t = unit_types[i % len(unit_types)]
    store.spawn(t, 0, 500 + (i % 10) * 60, 500 + (i // 10) * 60)
for i in range(50):
    t = unit_types[i % len(unit_types)]
    store.spawn(t, 1, 2500 + (i % 10) * 60, 500 + (i // 10) * 60)

# Give faction 0 an attack-move toward faction 1
for uid in store.active_ids_for_faction(0):
    store.set_move_target(uid, 2500, 500)
    store.attack_moving[uid] = True

# Track per-unit facing history for angular velocity measurement
prev_facing = {}
max_angular_vel = {"Strike": 0.0, "Line": 0.0, "Siege": 0.0}
facing_samples = []

for tick in range(TICK_COUNT):
    engine.step()

    for uid in range(store.count):
        if not store.alive[uid]:
            continue
        cat_name = CATEGORY_NAMES.get(int(store.category[uid]), "?")
        f = store.data[uid, FIELD_FACING_RAD]

        if uid in prev_facing:
            av = angular_diff(prev_facing[uid], f) / DT
            if cat_name in max_angular_vel:
                max_angular_vel[cat_name] = max(max_angular_vel[cat_name], av)
        prev_facing[uid] = f

    if tick in (50, 100, 150, 199):
        sample_uids = [0, 1, 2, 3, 4, 25, 50, 51, 52, 75]
        print(f"\n--- Tick {tick} ---")
        print(f"  {'uid':>4} {'cat':>7} {'state':>10} {'facing':>8} {'target/heading':>20}")
        for uid in sample_uids:
            if uid >= store.count or not store.alive[uid]:
                continue
            cat = CATEGORY_NAMES.get(int(store.category[uid]), "?")
            f = store.data[uid, FIELD_FACING_RAD]
            tgt = store.auto_engage_target[uid]
            if tgt >= 0 and store.alive[tgt]:
                tx = store.data[tgt, FIELD_X]
                ty = store.data[tgt, FIELD_Y]
                state = "attacking"
                target_str = f"({tx:.0f}, {ty:.0f})"
            elif store.has_move_target[uid]:
                state = "moving"
                target_str = f"({store.target_x[uid]:.0f}, {store.target_y[uid]:.0f})"
            else:
                state = "idle"
                target_str = "-"
            print(f"  {uid:>4} {cat:>7} {state:>10} {f:>8.4f} {target_str:>20}")

print("\n" + "=" * 70)
print("  Max angular velocity by category (rad/s)")
print("=" * 70)
passes = 0
fails = 0
for cat in ("Strike", "Line", "Siege"):
    measured = max_angular_vel[cat]
    cap = ROTATION_CAPS[cat]
    tolerance = cap * 1.05  # 5% tolerance for floating point
    ok = measured <= tolerance
    status = "PASS" if ok else "FAIL"
    if ok:
        passes += 1
    else:
        fails += 1
    print(f"  [{status}]  {cat}: max={measured:.2f} rad/s, cap={cap:.1f} rad/s")

# Run 100 more ticks so attacking units have time to converge
for tick in range(100):
    engine.step()
    for uid in range(store.count):
        if not store.alive[uid]:
            continue
        cat_name = CATEGORY_NAMES.get(int(store.category[uid]), "?")
        f = store.data[uid, FIELD_FACING_RAD]
        if uid in prev_facing:
            av = angular_diff(prev_facing[uid], f) / DT
            if cat_name in max_angular_vel:
                max_angular_vel[cat_name] = max(max_angular_vel[cat_name], av)
        prev_facing[uid] = f

# Verify attacking units face their targets (after convergence)
print("\n" + "=" * 70)
print("  Facing accuracy — attacking units face target (after convergence)")
print("=" * 70)
angle_errors = []
for uid in range(store.count):
    if not store.alive[uid]:
        continue
    tgt = store.auto_engage_target[uid]
    if tgt < 0 or not store.alive[tgt]:
        continue
    px, py = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
    tx, ty = store.data[tgt, FIELD_X], store.data[tgt, FIELD_Y]
    expected = wrap(math.atan2(ty - py, tx - px))
    actual = store.data[uid, FIELD_FACING_RAD]
    err = angular_diff(actual, expected)
    angle_errors.append(err)

if angle_errors:
    avg_err = sum(angle_errors) / len(angle_errors)
    max_err = max(angle_errors)
    ok = avg_err < math.radians(10)  # average within 10 degrees
    status = "PASS" if ok else "FAIL"
    if ok:
        passes += 1
    else:
        fails += 1
    print(f"  [{status}]  {len(angle_errors)} attacking units — avg error: {math.degrees(avg_err):.1f}°, max: {math.degrees(max_err):.1f}°")
else:
    print("  [SKIP]  No attacking units at end of run")

print(f"\n{'=' * 70}")
if fails == 0:
    print(f"  Checkpoint A — ALL {passes} CHECKS PASSED")
else:
    print(f"  Checkpoint A — {fails} FAILURES, {passes} passed")
print("=" * 70)
