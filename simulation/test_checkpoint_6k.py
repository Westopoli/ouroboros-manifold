"""
Checkpoint 6K — Performance stress test (100v100, full tick breakdown).

L16: p95 full tick time < 50ms.
"""
import math
import random
import time
import tracemalloc
import config
from unit import UnitStore, FIELD_X, FIELD_Y
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT            = config.TACTICAL_TICK_DURATION
TICKS         = 3000
TICK_BUDGET   = 50.0   # ms — L16
FACTION_A     = 0
FACTION_B     = 1
CENTER_X      = 6000.0
CENTER_Y      = 6000.0

MIXED_RATIO = {
    "Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
    "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10,
}


def _spawn(store, faction, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(count * frac)))
    while len(roster) > count:
        roster.pop(rng.randrange(len(roster)))
    while len(roster) < count:
        roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = max(5, int(math.sqrt(count)) + 1)
    uids = []
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def run():
    print("=" * 70)
    print("CHECKPOINT 6K — Performance stress test (100v100)")
    print(f"  Ticks: {TICKS}  Budget: p95 < {TICK_BUDGET}ms  (L16)")
    print("=" * 70)

    rng   = random.Random(1)
    tmap  = open_field_large()
    store = UnitStore()

    uids_a = _spawn(store, FACTION_A, CENTER_X - 500, CENTER_Y - 2500, 100, rng)
    uids_b = _spawn(store, FACTION_B, CENTER_X - 500, CENTER_Y + 2500, 100, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y + 2500}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": CENTER_X, "target_y": CENTER_Y - 2500}))

    sim_rng = random.Random(1)

    t_commands  = []
    t_targeting = []
    t_movement  = []
    t_damage    = []
    t_abilities = []
    t_fog       = []
    t_total     = []

    tracemalloc.start()

    for tick in range(TICKS):
        t0 = time.perf_counter()

        ts = time.perf_counter(); process_commands(queue, store, tick);             t_commands.append((time.perf_counter() - ts) * 1000)
        ts = time.perf_counter(); update_targeting(store, tmap, sim_rng, tick=tick); t_targeting.append((time.perf_counter() - ts) * 1000)
        ts = time.perf_counter(); update_movement(store, tmap, DT);                t_movement.append((time.perf_counter() - ts) * 1000)
        ts = time.perf_counter(); deaths, ks = resolve_damage(store, tmap, DT);   t_damage.append((time.perf_counter() - ts) * 1000)

        ts = time.perf_counter()
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        t_abilities.append((time.perf_counter() - ts) * 1000)

        ts = time.perf_counter(); update_fog_timers(store); t_fog.append((time.perf_counter() - ts) * 1000)

        t_total.append((time.perf_counter() - t0) * 1000)

        if tick % 500 == 499:
            active = store.active_ids()
            a = sum(1 for u in active if store.faction[u] == FACTION_A)
            b = sum(1 for u in active if store.faction[u] == FACTION_B)
            print(f"  t={tick+1:>5}  A={a:>3}  B={b:>3}  tick_avg={sum(t_total[-500:])/500:.2f}ms")

        alive_factions = {store.faction[u] for u in store.active_ids()}
        if len(alive_factions) <= 1:
            print(f"  Combat resolved at tick {tick + 1}.")
            break

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def stats(times):
        s = sorted(times)
        n = len(s)
        return {
            "mean": sum(s) / n,
            "min":  s[0],
            "p95":  s[int(n * 0.95)],
            "p99":  s[int(n * 0.99)],
            "max":  s[-1],
        }

    tot  = stats(t_total)
    n    = len(t_total)
    comp = sum(1 for t in t_total if t < TICK_BUDGET)

    print()
    print(f"  {'Subsystem':<16} {'mean':>8} {'p95':>8} {'max':>8}")
    print(f"  {'─'*16} {'─'*8} {'─'*8} {'─'*8}")
    for label, times in [
        ("commands",  t_commands),
        ("targeting", t_targeting),
        ("movement",  t_movement),
        ("damage",    t_damage),
        ("abilities", t_abilities),
        ("fog",       t_fog),
        ("TOTAL",     t_total),
    ]:
        s = stats(times)
        print(f"  {label:<16} {s['mean']:>7.2f}ms {s['p95']:>7.2f}ms {s['max']:>7.2f}ms")

    print()
    print(f"  Ticks measured:   {n}")
    print(f"  Budget compliance: {comp}/{n} ticks < {TICK_BUDGET}ms  ({comp/n:.1%})")
    print(f"  Peak memory:       {peak_mem/1024/1024:.1f} MB")
    print()

    ok = tot["p95"] < TICK_BUDGET
    print(f"  L16: {'PASS' if ok else 'FAIL'}  p95={tot['p95']:.2f}ms  (budget={TICK_BUDGET}ms)")
    print()
    print("Checkpoint 6K complete.")

    if not ok:
        raise AssertionError(f"p95 {tot['p95']:.2f}ms exceeds {TICK_BUDGET}ms budget")


if __name__ == "__main__":
    run()
