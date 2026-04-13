"""
Checkpoint: formation movement performance budget — 100v100 full-composition battle.

Formation layout per side (realistic doctrine):
  Strike (Raider/Interceptor) — front row, 25 units
  Line   (Vanguard/Warden)   — middle rows, 40 units
  Siege  (Bombard/Bastion)   — back rows,  35 units

Both sides attack_move toward each other. FORMATION_MOVE_ENABLED=True.
Measures update_movement avg ms/tick over 1500 ticks.
"""

import math
import random
import time
import config

config.FORMATION_MOVE_ENABLED = True

from unit import UnitStore, FIELD_X, FIELD_Y
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT    = config.TACTICAL_TICK_DURATION
TICKS = 1500

# Map center — both sides march toward this
CENTER_X = 6000.0
CENTER_Y = 6000.0

# Faction A: south side (high y), faces north
# Faction B: north side (low y), faces south
FACTION_A = 0
FACTION_B = 1


def _spawn_side(store, faction, sign, rng):
    """
    sign=+1 → faction A (south, front row has smallest y offset from center)
    sign=-1 → faction B (north, front row has largest y offset from center)

    Row offsets from CENTER_Y (positive = away from enemy for A, toward for B):
      strike_y_off =  sign * 2800   (front  — closest to enemy)
      line_y_off   =  sign * 3200   (middle)
      siege_y_off  =  sign * 3700   (back   — furthest from enemy)
    """
    strike_y = CENTER_Y + sign * 2800
    line_y   = CENTER_Y + sign * 3200
    siege_y  = CENTER_Y + sign * 3700

    uids = []

    # Strike — 25 units (13 Raider, 12 Interceptor), 1 row
    n_strike = 25
    spacing  = 50.0
    start_x  = CENTER_X - (n_strike - 1) * spacing / 2.0
    for i in range(n_strike):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x  = start_x + i * spacing + rng.uniform(-8, 8)
        y  = strike_y + rng.uniform(-12, 12)
        uids.append(store.spawn(ut, faction, x, y))

    # Line — 40 units (25 Vanguard, 15 Warden), 2 rows of 20
    n_line  = 40
    row_gap = 55.0
    spacing = 45.0
    start_x = CENTER_X - 9 * spacing / 2.0  # 10 per half-row (20 wide)
    for i in range(n_line):
        row = i // 20
        col = i % 20
        ut  = "Vanguard" if (i % 8) < 5 else "Warden"
        x   = CENTER_X - 9 * spacing / 2.0 + col * spacing + rng.uniform(-8, 8)
        y   = line_y + sign * row * row_gap + rng.uniform(-10, 10)
        uids.append(store.spawn(ut, faction, x, y))

    # Siege — 35 units (18 Bombard, 17 Bastion), 2 rows
    n_siege  = 35
    row_gap  = 70.0
    spacing  = 60.0
    for i in range(n_siege):
        row = i // 18
        col = i % 18
        ut  = "Bombard" if i % 2 == 0 else "Bastion"
        x   = CENTER_X - 8 * spacing / 2.0 + col * spacing + rng.uniform(-10, 10)
        y   = siege_y + sign * row * row_gap + rng.uniform(-10, 10)
        uids.append(store.spawn(ut, faction, x, y))

    return uids


def run():
    print("=" * 70)
    print("CHECKPOINT — formation movement performance budget (100v100)")
    print(f"  Scenario:  100v100 mixed, attack_move, open_field_large")
    print(f"  Formation: Strike front / Line middle / Siege back")
    print(f"  Ticks:     {TICKS}  ({TICKS * DT:.0f}s sim-time)")
    print("=" * 70)

    tmap  = open_field_large()
    store = UnitStore()
    rng   = random.Random(1)

    uids_a = _spawn_side(store, FACTION_A, +1, rng)
    uids_b = _spawn_side(store, FACTION_B, -1, rng)

    assert len(uids_a) == 100, f"Expected 100 units for A, got {len(uids_a)}"
    assert len(uids_b) == 100, f"Expected 100 units for B, got {len(uids_b)}"

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y - 2800}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y + 2800}))

    sim_rng   = random.Random(1)
    mov_times = []

    for t in range(TICKS):
        process_commands(queue, store, t)
        update_targeting(store, tmap, sim_rng)

        t0 = time.perf_counter()
        update_movement(store, tmap, DT)
        mov_times.append((time.perf_counter() - t0) * 1000.0)

        resolve_damage(store, tmap, DT)
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        update_fog_timers(store)

        if t % 300 == 299:
            active = store.active_ids()
            a_alive = sum(1 for u in active if store.faction[u] == FACTION_A)
            b_alive = sum(1 for u in active if store.faction[u] == FACTION_B)
            n = len(mov_times)
            window = mov_times[max(0, n - 300):]
            print(f"  t={t+1:>5}  A={a_alive:>3}  B={b_alive:>3}  "
                  f"mov_avg(last 300)={sum(window)/len(window):.3f}ms")

        alive_factions = {store.faction[u] for u in store.active_ids()}
        if len(alive_factions) <= 1:
            print(f"  Combat resolved at tick {t + 1}.")
            break

    avg_ms  = sum(mov_times) / len(mov_times)
    min_ms  = min(mov_times)
    max_ms  = max(mov_times)
    mov_times_sorted = sorted(mov_times)
    p95_ms  = mov_times_sorted[int(len(mov_times_sorted) * 0.95)]

    print()
    print(f"  update_movement over {len(mov_times)} ticks:")
    print(f"    avg = {avg_ms:.3f} ms/tick")
    print(f"    min = {min_ms:.3f} ms/tick")
    print(f"    p95 = {p95_ms:.3f} ms/tick")
    print(f"    max = {max_ms:.3f} ms/tick")
    print()

    # Budget ceiling: set from first measured run. Update if the scenario changes.
    budget_ms = MOVEMENT_BUDGET_MS
    passed = avg_ms <= budget_ms
    print(f"  Budget: avg <= {budget_ms:.3f} ms/tick")
    if passed:
        print(f"  PASS  ({avg_ms:.3f} <= {budget_ms:.3f})")
    else:
        print(f"  FAIL  ({avg_ms:.3f} > {budget_ms:.3f})")
        raise AssertionError(
            f"update_movement avg {avg_ms:.3f} ms/tick exceeds budget {budget_ms:.3f}"
        )


# Ceiling set from first measured run (avg=37.4ms). 50ms gives ~1.34× headroom.
# If the scenario changes or movement is optimized, re-measure and update.
MOVEMENT_BUDGET_MS = 50.0

if __name__ == "__main__":
    run()
