import time
import random
import math
import tracemalloc
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_ABILITY_ACTIVE
from ability import ABILITY_INACTIVE
from tactical_engine import TacticalEngine
from movement import apply_group_move
from test_maps import open_field_large

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION
SUSTAINED_TICKS = 3000
TICK_BUDGET_MS = 50.0

MAP_CENTER_X = 6000.0
MAP_CENTER_Y = 6000.0


def spawn_mixed(store, faction, count, center_x, center_y, facing_x, rng):
    ratio = {"Vanguard": 0.25, "Warden": 0.15, "Raider": 0.15,
             "Interceptor": 0.15, "Bombard": 0.15, "Bastion": 0.15}
    role_counts = {}
    placed = 0
    for ut, frac in ratio.items():
        n = max(1, round(count * frac))
        if placed + n > count:
            n = count - placed
        role_counts[ut] = n
        placed += n
        if placed >= count:
            break

    sign = 1.0 if facing_x > center_x else -1.0
    rows = {"Vanguard": 0, "Warden": 1, "Raider": 2, "Interceptor": 2, "Bombard": 3, "Bastion": 4}
    uids = []
    for ut, n in role_counts.items():
        row_x = center_x + sign * rows[ut] * 60.0
        start_y = center_y - (n - 1) * 60.0 / 2.0
        for i in range(n):
            x = row_x + rng.uniform(-15.0, 15.0)
            y = start_y + i * 60.0 + rng.uniform(-15.0, 15.0)
            uids.append(store.spawn(ut, faction, x, y))
    return uids


def run():
    print("=" * 70)
    print("CHECKPOINT 6K-CLOSE — Close Spawn Variant (large field)")
    print("=" * 70)
    print(f"  Scenario: 200v200 mixed, open_field_large (12000×12000)")
    print(f"  Spawn:    A at x=5000, B at x=7000 (2000wu apart vs 6000wu in 6K)")
    print(f"  Target:   p95 tick time < {TICK_BUDGET_MS:.0f}ms")
    print(f"  Duration: {SUSTAINED_TICKS} ticks ({SUSTAINED_TICKS * DT:.0f}s sim-time)")
    print()

    rng = random.Random(1)
    tmap = open_field_large()
    store = UnitStore()

    uids_a = spawn_mixed(store, FACTION_A, 200, 5000.0, MAP_CENTER_Y, MAP_CENTER_X, rng)
    uids_b = spawn_mixed(store, FACTION_B, 200, 7000.0, MAP_CENTER_Y, MAP_CENTER_X, rng)

    apply_group_move(store, uids_a, MAP_CENTER_X, MAP_CENTER_Y)
    apply_group_move(store, uids_b, MAP_CENTER_X, MAP_CENTER_Y)

    engine = TacticalEngine(tmap, store, seed=1)

    tracemalloc.start()
    tick_times = []
    subsystem_totals = {"damage": 0.0, "movement": 0.0, "abilities": 0.0,
                        "fog": 0.0, "targeting": 0.0, "commands": 0.0}

    import damage as dmg_mod
    from ability import update_abilities, resolve_barrage
    from fog_of_war import update_fog_timers
    from command import process_commands

    for t in range(SUSTAINED_TICKS):
        t0 = time.perf_counter()

        t_cmd = time.perf_counter()
        process_commands(engine.command_queue, engine.store, engine.tick)
        subsystem_totals["commands"] += time.perf_counter() - t_cmd

        t_tgt = time.perf_counter()
        from damage import update_targeting
        update_targeting(engine.store, engine.map, engine.rng)
        subsystem_totals["targeting"] += time.perf_counter() - t_tgt

        t_mov = time.perf_counter()
        from movement import update_movement
        update_movement(engine.store, engine.map, engine.dt)
        subsystem_totals["movement"] += time.perf_counter() - t_mov

        t_dmg = time.perf_counter()
        deaths, kill_sources = dmg_mod.resolve_damage(engine.store, engine.map, engine.dt)
        subsystem_totals["damage"] += time.perf_counter() - t_dmg

        t_abl = time.perf_counter()
        barrage_events = update_abilities(engine.store, engine.dt)
        if barrage_events:
            resolve_barrage(engine.store, barrage_events)
        subsystem_totals["abilities"] += time.perf_counter() - t_abl

        t_fog = time.perf_counter()
        update_fog_timers(engine.store)
        subsystem_totals["fog"] += time.perf_counter() - t_fog

        if deaths:
            for uid in deaths:
                engine.death_log.append({"uid": uid, "tick": engine.tick, "killer": kill_sources.get(uid, -1)})
        engine.tick += 1

        tick_times.append((time.perf_counter() - t0) * 1000.0)

        if engine.tick % 100 == 0:
            active = engine.store.active_ids()
            surv_a = sum(1 for u in active if engine.store.faction[u] == FACTION_A)
            surv_b = sum(1 for u in active if engine.store.faction[u] == FACTION_B)
            avg_dist = sum(math.sqrt((engine.store.data[u, FIELD_X] - MAP_CENTER_X)**2 +
                                     (engine.store.data[u, FIELD_Y] - MAP_CENTER_Y)**2)
                           for u in active) / max(len(active), 1)
            with_target = sum(1 for u in active if engine.store.auto_engage_target[u] >= 0)
            print(f"  t={engine.tick:>4}  A={surv_a} B={surv_b}  avg_dist={avg_dist:.0f}wu  targets_set={with_target}/{len(active)}")

        if engine.tick == 500:
            active = engine.store.active_ids()
            n_inactive = sum(1 for u in active if engine.store.data[u, FIELD_ABILITY_ACTIVE] == ABILITY_INACTIVE)
            tgt_set   = sum(1 for u in active if engine.store.auto_engage_target[u] >= 0)
            tgt_unset = sum(1 for u in active if engine.store.auto_engage_target[u] < 0)
            print(f"  [t=500] ability_inactive={n_inactive}/{len(active)}  target_set={tgt_set}  target_unset={tgt_unset}")

        if engine.is_terminal():
            print(f"  Combat resolved early at tick {engine.tick} — one side eliminated.")
            break

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tick_times.sort()
    n = len(tick_times)
    mean_ms   = sum(tick_times) / n
    min_ms    = tick_times[0]
    max_ms    = tick_times[-1]
    p95_ms    = tick_times[int(n * 0.95)]
    p99_ms    = tick_times[int(n * 0.99)]
    compliant = sum(1 for t in tick_times if t < TICK_BUDGET_MS)

    print(f"  Ticks measured:  {n}")
    print(f"  Alive at end:    A={len(engine.get_survivors(FACTION_A))}  B={len(engine.get_survivors(FACTION_B))}")
    print()
    print(f"  {'Metric':<20} {'Value':>10}")
    print(f"  {'------':<20} {'-----':>10}")
    print(f"  {'min (ms)':<20} {min_ms:>10.2f}")
    print(f"  {'mean (ms)':<20} {mean_ms:>10.2f}")
    print(f"  {'p95 (ms)':<20} {p95_ms:>10.2f}  {'<-- target' if p95_ms < TICK_BUDGET_MS else '<-- FAIL'}")
    print(f"  {'p99 (ms)':<20} {p99_ms:>10.2f}")
    print(f"  {'max (ms)':<20} {max_ms:>10.2f}")
    print(f"  {'budget compliance':<20} {compliant/n:>9.1%}  ({compliant}/{n} ticks < {TICK_BUDGET_MS:.0f}ms)")
    print(f"  {'peak memory':<20} {peak_mem/1024/1024:>9.1f} MB")
    print()

    total_sub = sum(subsystem_totals.values())
    print(f"  Subsystem breakdown (total across {n} ticks):")
    for name, secs in sorted(subsystem_totals.items(), key=lambda x: -x[1]):
        pct = secs / total_sub * 100 if total_sub > 0 else 0
        print(f"    {name:<14} {secs*1000:>8.1f} ms total  {pct:>5.1f}%")

    print()
    print(f"  p95={'PASS' if p95_ms < TICK_BUDGET_MS else 'FAIL'}  (p95={p95_ms:.2f}ms, budget={TICK_BUDGET_MS:.0f}ms)")
    print()
    print("Checkpoint 6K-close complete.")


if __name__ == "__main__":
    run()
