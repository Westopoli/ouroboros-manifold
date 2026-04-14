"""
diag_perf_movement.py — Isolates cost within update_movement by toggling subsystems.

Run A: full update_movement (collision + probe steering + per-unit loop)
Run B: HARD_COLLISION_ENABLED=False  → removes _resolve_collisions
Run C: also force all detour_remaining=0 each tick → removes probe steering branch

Difference A-B = _resolve_collisions cost
Difference B-C = _probe_is_blocked / steering cost
C alone        = pure per-unit loop cost
"""
import math, random, time
import config
from unit import UnitStore, FIELD_X, FIELD_Y
from movement import update_movement
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT = config.TACTICAL_TICK_DURATION
TICKS = 30
FACTION_A, FACTION_B = 0, 1
CENTER_X, CENTER_Y = 6000.0, 6000.0

MIXED_RATIO = {"Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
               "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10}

def _make_store(rng):
    tmap = open_field_large()
    store = UnitStore()
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(100 * frac)))
    while len(roster) > 100: roster.pop(rng.randrange(len(roster)))
    while len(roster) < 100: roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = 11
    uids_a, uids_b = [], []
    for i, ut in enumerate(roster):
        x = CENTER_X - 500 + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = CENTER_Y - 2500 + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids_a.append(store.spawn(ut, FACTION_A, x, y))
    for i, ut in enumerate(roster):
        x = CENTER_X - 500 + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = CENTER_Y + 2500 + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids_b.append(store.spawn(ut, FACTION_B, x, y))
    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y + 2500}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y - 2500}))
    process_commands(queue, store, 0)
    return store, tmap


def _measure(store, tmap, ticks, disable_collision=False, disable_steering=False):
    orig_collision = config.HARD_COLLISION_ENABLED
    config.HARD_COLLISION_ENABLED = not disable_collision
    times = []
    for _ in range(ticks):
        if disable_steering:
            for uid in store.active_ids():
                store.detour_remaining[uid] = 0.0
        ts = time.perf_counter()
        update_movement(store, tmap, DT)
        times.append((time.perf_counter() - ts) * 1000)
    config.HARD_COLLISION_ENABLED = orig_collision
    return sum(times) / len(times)


print(f"Measuring update_movement cost at 100v100 ({TICKS} ticks each run)...\n")

rng = random.Random(1)
store_a, tmap = _make_store(rng)
mean_full = _measure(store_a, tmap, TICKS)

rng = random.Random(1)
store_b, tmap = _make_store(rng)
mean_no_coll = _measure(store_b, tmap, TICKS, disable_collision=True)

rng = random.Random(1)
store_c, tmap = _make_store(rng)
mean_no_steer = _measure(store_c, tmap, TICKS, disable_collision=True, disable_steering=True)

coll_cost    = mean_full - mean_no_coll
steer_cost   = mean_no_coll - mean_no_steer
loop_cost    = mean_no_steer

print(f"  {'Run':<40} {'mean ms/tick':>14}")
print(f"  {'─'*40} {'─'*14}")
print(f"  {'A: full (collision+steering+loop)':<40} {mean_full:>13.2f}ms")
print(f"  {'B: no collision (steering+loop)':<40} {mean_no_coll:>13.2f}ms")
print(f"  {'C: no collision, no steering (loop)':<40} {mean_no_steer:>13.2f}ms")
print()
print(f"  Breakdown:")
print(f"    _resolve_collisions cost  (A-B): {coll_cost:>8.2f}ms  ({coll_cost/mean_full*100:.0f}%)")
print(f"    _probe_is_blocked cost    (B-C): {steer_cost:>8.2f}ms  ({steer_cost/mean_full*100:.0f}%)")
print(f"    per-unit loop cost          (C): {loop_cost:>8.2f}ms  ({loop_cost/mean_full*100:.0f}%)")
