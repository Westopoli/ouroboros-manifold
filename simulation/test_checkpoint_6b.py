import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED
from movement import update_movement, apply_group_move
from test_maps import open_field


UNIT_TYPES_SIDE_A = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                     "Warden", "Bombard", "Bombard", "Bastion", "Bastion"]
UNIT_TYPES_SIDE_B = ["Raider", "Raider", "Interceptor", "Vanguard", "Vanguard",
                     "Warden", "Bombard", "Bombard", "Bastion", "Bastion"]

FACTION_A = 0
FACTION_B = 1
CENTER = (2000.0, 2000.0)
DT = config.TACTICAL_TICK_DURATION
SAMPLE_TICKS = [50, 100, 150, 200]


def spawn_units(store):
    for i, ut in enumerate(UNIT_TYPES_SIDE_A):
        x = 200.0 + i * 80.0
        y = 200.0 + i * 40.0
        store.spawn(ut, FACTION_A, x, y)

    for i, ut in enumerate(UNIT_TYPES_SIDE_B):
        x = 3800.0 - i * 80.0
        y = 3800.0 - i * 40.0
        store.spawn(ut, FACTION_B, x, y)


def print_positions(store, label):
    print(f"\n  {label}:")
    print(f"    {'ID':>3} {'Type':<14} {'Faction':>7} {'X':>8} {'Y':>8}")
    print(f"    {'---':>3} {'-'*14:<14} {'-'*7:>7} {'-'*8:>8} {'-'*8:>8}")
    for uid in range(store.count):
        if not store.alive[uid]:
            continue
        x, y = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        f = "A" if store.faction[uid] == FACTION_A else "B"
        print(f"    {uid:>3} {store.unit_type[uid]:<14} {f:>7} {x:>8.1f} {y:>8.1f}")


def verify_speed(store, prev_positions, tick_count):
    print(f"\n  Speed Verification (ticks {tick_count - 50 + 1}–{tick_count}):")
    all_ok = True
    for uid in range(store.count):
        if not store.alive[uid] or not store.has_move_target[uid]:
            continue
        px, py = prev_positions[uid]
        cx, cy = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        dist_moved = math.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        expected_speed = store.data[uid, FIELD_SPEED]
        expected_dist = expected_speed * DT * 50
        ratio = dist_moved / expected_dist if expected_dist > 0 else 0
        ok = 0.85 <= ratio <= 1.15
        if not ok:
            all_ok = False
            print(f"    WARN unit {uid} ({store.unit_type[uid]}): moved {dist_moved:.1f}, "
                  f"expected ~{expected_dist:.1f} (ratio {ratio:.3f})")
    if all_ok:
        print(f"    All units within 15% of expected distance — OK")


def verify_separation(store):
    min_dist = float("inf")
    min_pair = (-1, -1)
    active = store.active_ids()
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if store.data[a, FIELD_Y] != store.data[b, FIELD_Y]:
                pass
            ax, ay = store.data[a, FIELD_X], store.data[a, FIELD_Y]
            bx, by = store.data[b, FIELD_X], store.data[b, FIELD_Y]
            d = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
            if d < min_dist:
                min_dist = d
                min_pair = (a, b)

    threshold = config.UNIT_COLLISION_RADIUS * 2
    ok = min_dist >= threshold
    status = "OK" if ok else "WARN"
    print(f"\n  Separation Check:")
    print(f"    Closest pair: units {min_pair[0]} & {min_pair[1]}, distance = {min_dist:.1f}")
    print(f"    Minimum threshold (2 × collision radius): {threshold:.1f}")
    print(f"    Status: {status}")
    return ok


def run():
    print("=" * 60)
    print("CHECKPOINT 6B — Unit State and Movement")
    print("=" * 60)

    tmap = open_field()
    store = UnitStore()
    spawn_units(store)

    for uid in range(store.count):
        store.set_move_target(uid, CENTER[0], CENTER[1])

    print_positions(store, "Initial Positions (tick 0)")

    prev_positions = {}
    for uid in range(store.count):
        prev_positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    for tick in range(1, 201):
        update_movement(store, tmap, DT)

        if tick == 50:
            for uid in range(store.count):
                prev_positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

        if tick in SAMPLE_TICKS:
            print_positions(store, f"Positions at tick {tick} (t={tick * DT:.1f}s)")
            if tick > 50:
                verify_speed(store, prev_positions, tick)
                for uid in range(store.count):
                    prev_positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    verify_separation(store)

    print("\n  Arrival Check:")
    arrived = 0
    still_moving = 0
    for uid in range(store.count):
        x, y = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        d = math.sqrt((x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2)
        if d < 50:
            arrived += 1
        elif store.has_move_target[uid]:
            still_moving += 1
        else:
            arrived += 1
    print(f"    Arrived at center (within 50 wu): {arrived}")
    print(f"    Still moving: {still_moving}")

    unit_speeds = {}
    for uid in range(store.count):
        ut = store.unit_type[uid]
        spd = store.data[uid, FIELD_SPEED]
        if ut not in unit_speeds:
            unit_speeds[ut] = spd
    print("\n  Speed Reference:")
    for ut in sorted(unit_speeds, key=lambda x: -unit_speeds[x]):
        ticks_to_center = 2800 / (unit_speeds[ut] * DT)
        print(f"    {ut:<14} {unit_speeds[ut]:>6.0f} wu/s → ~{ticks_to_center:.0f} ticks to cross 2800 wu")

    print()
    test_group_move()
    print("\nCheckpoint 6B complete.")


def test_group_move():
    print("=" * 60)
    print("GROUP MOVE — Speed Matching Test")
    print("=" * 60)

    tmap = open_field()
    store = UnitStore()
    for i, ut in enumerate(UNIT_TYPES_SIDE_A):
        x = 200.0 + i * 80.0
        y = 200.0 + i * 40.0
        store.spawn(ut, FACTION_A, x, y)

    faction_a_ids = list(range(10))
    target = (2000.0, 2000.0)
    apply_group_move(store, faction_a_ids, target[0], target[1])

    start_positions = {}
    for uid in faction_a_ids:
        start_positions[uid] = (store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    for _ in range(100):
        update_movement(store, tmap, DT)

    expected_speed = 40.0  # Bastion speed — slowest in group
    expected_dist = expected_speed * DT * 100

    print(f"\n  Expected speed: {expected_speed} wu/s (Bastion, slowest in group)")
    print(f"  Expected distance in 100 ticks: {expected_dist:.1f} wu")
    print(f"\n    {'ID':>3} {'Type':<14} {'Base Spd':>8} {'Dist Moved':>10} {'Ratio':>7} {'Status':>7}")
    print(f"    {'---':>3} {'-'*14:<14} {'-'*8:>8} {'-'*10:>10} {'-'*7:>7} {'-'*7:>7}")

    all_ok = True
    distances = []
    for uid in faction_a_ids:
        sx, sy = start_positions[uid]
        cx, cy = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        dist = math.sqrt((cx - sx) ** 2 + (cy - sy) ** 2)
        distances.append(dist)
        ratio = dist / expected_dist if expected_dist > 0 else 0
        ok = 0.95 <= ratio <= 1.05
        if not ok:
            all_ok = False
        status = "OK" if ok else "WARN"
        base_spd = store.data[uid, FIELD_SPEED]
        print(f"    {uid:>3} {store.unit_type[uid]:<14} {base_spd:>8.0f} {dist:>10.1f} {ratio:>7.3f} {status:>7}")

    avg_dist = sum(distances) / len(distances)
    max_spread = max(distances) - min(distances)
    print(f"\n  Average distance: {avg_dist:.1f} wu")
    print(f"  Max spread: {max_spread:.1f} wu (cohesion {'OK' if max_spread < expected_dist * 0.10 else 'WARN'})")
    print(f"  Overall: {'PASS' if all_ok else 'FAIL'}")
    print()


if __name__ == "__main__":
    run()
