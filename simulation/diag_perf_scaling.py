"""
diag_perf_scaling.py — Confirm O(n²) scaling by sweeping unit count.

Runs update_movement for 20 ticks at n = 10, 25, 50, 75, 100 per side.
O(n²) shows ratio ≈ n² / n_base². O(n) shows ratio ≈ n / n_base.
"""
import math, random, time
import config
from unit import UnitStore
from movement import update_movement
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT = config.TACTICAL_TICK_DURATION
TICKS = 20
FACTION_A, FACTION_B = 0, 1
CENTER_X, CENTER_Y = 6000.0, 6000.0
UNIT_TYPES = ["Vanguard", "Raider", "Interceptor", "Warden", "Bombard", "Bastion"]

def _make_store(n_per_side, rng):
    tmap = open_field_large()
    store = UnitStore()
    cols = max(5, int(math.sqrt(n_per_side)) + 1)
    uids_a, uids_b = [], []
    for i in range(n_per_side):
        ut = UNIT_TYPES[i % len(UNIT_TYPES)]
        x = CENTER_X - 500 + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = CENTER_Y - 2500 + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids_a.append(store.spawn(ut, FACTION_A, x, y))
    for i in range(n_per_side):
        ut = UNIT_TYPES[i % len(UNIT_TYPES)]
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

print(f"Scaling test — update_movement mean ms/tick over {TICKS} ticks\n")
print(f"  {'n/side':>7}  {'total':>6}  {'mean ms':>9}  {'ratio':>7}  {'expected O(n²)':>14}")
print(f"  {'─'*7}  {'─'*6}  {'─'*9}  {'─'*7}  {'─'*14}")

baseline = None
for n in [10, 25, 50, 75, 100]:
    rng = random.Random(1)
    store, tmap = _make_store(n, rng)
    times = []
    for _ in range(TICKS):
        ts = time.perf_counter()
        update_movement(store, tmap, DT)
        times.append((time.perf_counter() - ts) * 1000)
    mean_ms = sum(times) / len(times)
    if baseline is None:
        baseline = mean_ms
        baseline_n = n
    ratio = mean_ms / baseline
    expected_n2 = (n / baseline_n) ** 2
    print(f"  {n:>7}  {2*n:>6}  {mean_ms:>9.2f}ms  {ratio:>6.1f}×  {expected_n2:>13.1f}×")

print()
print("  If ratio ≈ expected O(n²): collision/probe are dominant.")
print("  If ratio ≈ n/n_base: scaling is linear (other bottleneck).")
