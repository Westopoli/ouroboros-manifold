import math
import random
import time
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED
from damage import resolve_damage, update_targeting
from movement import update_movement, _ensure_navmesh
from ability import update_abilities, resolve_barrage
from fog_of_war import compute_visibility, update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import chokepoint

FACTION_STRIKE = 0
FACTION_LINE = 1
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 300
TARGET_X = 2000.0
TARGET_Y = 1610.0
DIAG_TICKS = {50, 100, 150, 200, 250}


def _spawn_strike_arc_x(store, faction, center_x, center_y, count, rng):
    uids = []
    spacing = 55.0
    start_x = center_x - (count - 1) * spacing / 2.0
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        jx = rng.uniform(-10, 10)
        jy = rng.uniform(-15, 15)
        x = start_x + i * spacing + jx
        y = center_y + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line_formed(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        jx = rng.uniform(-15, 15)
        jy = rng.uniform(-15, 15)
        x = center_x + (i % 5) * 40.0 + jx
        y = center_y + (i // 5) * 40.0 + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def run():
    rng = random.Random(1)
    tmap = chokepoint()
    store = UnitStore()

    strike_uids = _spawn_strike_arc_x(store, FACTION_STRIKE, 2000.0, 2900.0, 10, rng)
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 1100.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="move", unit_ids=strike_uids,
                      params={"target_x": TARGET_X, "target_y": TARGET_Y}))

    sim_rng = random.Random(1)
    mov_times = []
    tick = 0

    print(f"Formation Baseline — Strike plain_move to ({TARGET_X:.0f}, {TARGET_Y:.0f})")
    print(f"Strike spawns at (2000, 2900), Line at (2000, 1100) — Line is stationary")
    print("=" * 70)

    for t in range(MAX_TICKS):
        process_commands(queue, store, tick)
        update_targeting(store, tmap, sim_rng)

        t0 = time.perf_counter()
        update_movement(store, tmap, DT)
        mov_times.append((time.perf_counter() - t0) * 1000.0)

        deaths, kill_sources = resolve_damage(store, tmap, DT)
        barrage_events = update_abilities(store, DT)
        if barrage_events:
            resolve_barrage(store, barrage_events)
        update_fog_timers(store)

        tick += 1

        if tick in DIAG_TICKS:
            alive = [u for u in strike_uids if store.alive[u]]
            print(f"\nTick {tick} ({tick * DT:.1f}s):")

            if not alive:
                print("  Strike: all dead")
                continue

            xs = [store.data[u, FIELD_X] for u in alive]
            ys = [store.data[u, FIELD_Y] for u in alive]
            centroid_x = sum(xs) / len(xs)
            centroid_y = sum(ys) / len(ys)
            centroid_dist = math.sqrt((centroid_x - TARGET_X)**2 + (centroid_y - TARGET_Y)**2)
            dists = [math.sqrt((store.data[u, FIELD_X] - TARGET_X)**2 +
                               (store.data[u, FIELD_Y] - TARGET_Y)**2) for u in alive]
            mean_dist = sum(dists) / len(dists)

            print(f"  centroid=({centroid_x:.1f}, {centroid_y:.1f})  "
                  f"dist_to_target={centroid_dist:.1f}  mean_unit_dist={mean_dist:.1f}")

            print(f"  {'uid':<6} {'type':<14} {'x':>7} {'y':>7} "
                  f"{'dist_to_tgt':>12} {'detour_rem':>11} {'has_tgt'}")
            for u in alive:
                ux = store.data[u, FIELD_X]
                uy = store.data[u, FIELD_Y]
                d = math.sqrt((ux - TARGET_X)**2 + (uy - TARGET_Y)**2)
                det = store.detour_remaining[u]
                ht = store.has_move_target[u]
                print(f"  {u:<6} {store.unit_type[u]:<14} {ux:>7.1f} {uy:>7.1f} "
                      f"{d:>12.1f} {det:>11.1f} {ht}")

    avg_mov_ms = sum(mov_times) / len(mov_times) if mov_times else 0.0
    print(f"\n{'=' * 70}")
    print(f"update_movement: avg={avg_mov_ms:.3f} ms/tick over {len(mov_times)} ticks  "
          f"(min={min(mov_times):.3f}  max={max(mov_times):.3f})")


if __name__ == "__main__":
    run()
