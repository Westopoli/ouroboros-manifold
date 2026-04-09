import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_ATTACK_RANGE, FIELD_LAYER
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field, chokepoint, cover_heavy

FACTION_A = 0  # Strike
FACTION_B = 1  # Line
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000


def _spawn_strike(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        jx = rng.uniform(-15, 15)
        jy = rng.uniform(-15, 15)
        x = center_x + (i % 5) * 40.0 + jx
        y = center_y + (i // 5) * 40.0 + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        jx = rng.uniform(-15, 15)
        jy = rng.uniform(-15, 15)
        x = center_x + (i % 5) * 40.0 + jx
        y = center_y + (i // 5) * 40.0 + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _firing_pct(store, uids):
    alive = [u for u in uids if store.alive[u]]
    if not alive:
        return 0.0
    firing = 0
    for uid in alive:
        tgt = store.auto_engage_target[uid]
        if tgt < 0 or not store.alive[tgt]:
            continue
        ax, ay = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tx, ty = store.data[tgt, FIELD_X], store.data[tgt, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        if dist <= store.data[uid, FIELD_ATTACK_RANGE]:
            firing += 1
    return firing / len(alive)


def _build_scenario(name, seed):
    rng = random.Random(seed)

    if name == "open_headon_10v10":
        tmap = open_field()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 10, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1500.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "open_flank_10v10":
        tmap = open_field()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2000.0, 10, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 3500.0, 2000.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="fast_move", unit_ids=strike_uids,
                          params={"target_x": 2500.0, "target_y": 2000.0}))
        queue.add(Command(tick=100, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2000.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "open_surround_10v10":
        tmap = open_field()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2000.0, 10, rng)
        strike_a = _spawn_strike(store, FACTION_A, 2000.0, 800.0, 5, rng)
        strike_b = _spawn_strike(store, FACTION_A, 2000.0, 3200.0, 5, rng)
        strike_uids = strike_a + strike_b
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_a,
                          params={"target_x": 2000.0, "target_y": 2000.0}))
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_b,
                          params={"target_x": 2000.0, "target_y": 2000.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "choke_headon_10v10":
        tmap = chokepoint()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 10, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1200.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "choke_flank_10v10":
        tmap = chokepoint()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 10, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1200.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 1800.0}))
        queue.add(Command(tick=150, type="fast_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 3200.0}))
        queue.add(Command(tick=300, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "open_headon_15v10":
        tmap = open_field()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 10, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1500.0, 15, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "open_headon_10v15":
        tmap = open_field()
        store = UnitStore()
        line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 15, rng)
        strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1500.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
        return tmap, store, strike_uids, line_uids, queue

    if name == "cover_strike_10v10":
        tmap = cover_heavy()
        store = UnitStore()
        # Strike starts near cover patch at (1400, 1800)
        strike_uids = _spawn_strike(store, FACTION_A, 1400.0, 1800.0, 10, rng)
        line_uids = _spawn_line(store, FACTION_B, 2600.0, 1600.0, 10, rng)
        queue = CommandQueue()
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2600.0, "target_y": 1600.0}))
        return tmap, store, strike_uids, line_uids, queue

    raise ValueError(f"Unknown scenario: {name}")


def _run_scenario(name, seed):
    tmap, store, strike_uids, line_uids, queue = _build_scenario(name, seed)
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    firing_samples_a = []
    firing_samples_b = []
    sample_interval = 50
    last_sample = -999

    for _ in range(MAX_TICKS):
        engine.step()

        if engine.tick >= last_sample + sample_interval:
            active = store.active_ids()
            any_engaged = any(store.auto_engage_target[u] >= 0
                              for u in active if store.alive[u])
            if any_engaged:
                firing_samples_a.append(_firing_pct(store, strike_uids))
                firing_samples_b.append(_firing_pct(store, line_uids))
                last_sample = engine.tick

        if engine.is_terminal():
            break

    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    winner = "Strike" if surv_a > surv_b else ("Line" if surv_b > surv_a else "Draw")

    avg_fire_a = sum(firing_samples_a) / len(firing_samples_a) if firing_samples_a else 0.0
    avg_fire_b = sum(firing_samples_b) / len(firing_samples_b) if firing_samples_b else 0.0

    return {
        "winner": winner,
        "duration": engine.tick * DT,
        "surv_strike": surv_a,
        "surv_line": surv_b,
        "fire_pct_strike": avg_fire_a,
        "fire_pct_line": avg_fire_b,
    }


SCENARIOS = [
    ("open_headon_10v10",   "Open head-on 10v10"),
    ("open_flank_10v10",    "Open flank 10v10"),
    ("open_surround_10v10", "Open surround 10v10"),
    ("choke_headon_10v10",  "Choke head-on 10v10"),
    ("choke_flank_10v10",   "Choke flank 10v10"),
    ("open_headon_15v10",   "Open head-on 15v10"),
    ("open_headon_10v15",   "Open head-on 10v15"),
    ("cover_strike_10v10",  "Cover Strike 10v10"),
]


def run():
    seeds = list(range(1, 26))

    print("=" * 110)
    print("6J MATRIX — Strike vs Line, 25 seeds per scenario")
    print("=" * 110)

    rows = []
    for scenario_key, scenario_label in SCENARIOS:
        results = []
        for seed in seeds:
            results.append(_run_scenario(scenario_key, seed))

        strike_wins = sum(1 for r in results if r["winner"] == "Strike")
        avg_dur = sum(r["duration"] for r in results) / len(results)
        avg_surv_s = sum(r["surv_strike"] for r in results) / len(results)
        avg_surv_l = sum(r["surv_line"] for r in results) / len(results)
        avg_fire_s = sum(r["fire_pct_strike"] for r in results) / len(results)
        avg_fire_l = sum(r["fire_pct_line"] for r in results) / len(results)

        rows.append((scenario_label, strike_wins, avg_dur, avg_surv_s,
                      avg_surv_l, avg_fire_s, avg_fire_l))

        print(f"  {scenario_label} done — Strike wins {strike_wins}/25")

    print()
    hdr = (f"  {'Scenario':<26} {'Strike wins':>11} {'Avg dur':>9} "
           f"{'Avg S surv':>10} {'Avg L surv':>10} "
           f"{'S fire%':>9} {'L fire%':>9}")
    print(hdr)
    print(f"  {'-'*26} {'-'*11} {'-'*9} {'-'*10} {'-'*10} {'-'*9} {'-'*9}")

    for label, sw, dur, ss, ls, fs, fl in rows:
        print(f"  {label:<26} {sw:>8}/25 {dur:>8.1f}s "
              f"{ss:>10.1f} {ls:>10.1f} "
              f"{fs:>8.0%} {fl:>8.0%}")

    print(f"\n{'=' * 110}")
    print("Matrix complete.")


if __name__ == "__main__":
    run()
