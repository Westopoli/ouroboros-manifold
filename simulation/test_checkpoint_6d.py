import math
import random
import multiprocessing
import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_engine import TacticalEngine
from movement import apply_group_move
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 30000

UNIT_TYPES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]
CATEGORIES = {"Raider": "Strike", "Interceptor": "Strike", "Vanguard": "Line",
              "Warden": "Line", "Bombard": "Siege", "Bastion": "Siege"}
CAT_NAMES = ["Strike", "Line", "Siege"]


def spawn_line(store, unit_type, faction, count, start_x, start_y, rng=None):
    uids = []
    for i in range(count):
        jx = rng.uniform(-15.0, 15.0) if rng else 0.0
        jy = rng.uniform(-15.0, 15.0) if rng else 0.0
        x = start_x + (i % 10) * 50.0 + jx
        y = start_y + (i // 10) * 50.0 + jy
        uid = store.spawn(unit_type, faction, x, y)
        uids.append(uid)
    return uids


def spawn_mixed(store, faction, count, center_x, center_y, facing_x, rng=None):
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
    row_spacing = 50.0
    col_spacing = 50.0
    rows = {"Vanguard": 0, "Warden": 1, "Raider": 2, "Interceptor": 2, "Bombard": 3, "Bastion": 4}

    uids = []
    for ut, n in role_counts.items():
        row = rows[ut]
        row_x = center_x + sign * row * row_spacing
        start_y = center_y - (n - 1) * col_spacing / 2.0
        for i in range(n):
            jx = rng.uniform(-10.0, 10.0) if rng else 0.0
            jy = rng.uniform(-10.0, 10.0) if rng else 0.0
            x = row_x + jx
            y = start_y + i * col_spacing + jy
            uid = store.spawn(ut, faction, x, y)
            uids.append(uid)
    return uids


def run_engagement(type_a, type_b, count, seed=1, mixed=False):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    if mixed:
        uids_a = spawn_mixed(store, FACTION_A, count, 1600.0, 2000.0, 2200.0, rng)
        uids_b = spawn_mixed(store, FACTION_B, count, 2200.0, 2000.0, 1600.0, rng)
    else:
        uids_a = spawn_line(store, type_a, FACTION_A, count, 1600.0, 1800.0, rng)
        uids_b = spawn_line(store, type_b, FACTION_B, count, 2200.0, 1800.0, rng)

    apply_group_move(store, uids_a, 2000.0, 2000.0)
    apply_group_move(store, uids_b, 2000.0, 2000.0)

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.run(MAX_TICKS)

    duration_sec = engine.tick * DT
    winner = engine.get_winner()
    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))

    kill_buckets = {}
    for d in engine.death_log:
        bucket = int(d["tick"] * DT / 5.0) * 5
        kill_buckets[bucket] = kill_buckets.get(bucket, 0) + 1

    return {
        "duration_ticks": engine.tick,
        "duration_sec": duration_sec,
        "winner": "A" if winner == FACTION_A else ("B" if winner == FACTION_B else "Draw"),
        "survivors_a": surv_a,
        "survivors_b": surv_b,
        "initial_a": len(uids_a),
        "initial_b": len(uids_b),
        "kill_buckets": kill_buckets,
    }


def _run_5v5(args):
    ta, tb = args
    r = run_engagement(ta, tb, 5)
    return (ta, tb, r)


def _run_mixed(args):
    count, seed = args
    r = run_engagement(None, None, count, seed=seed, mixed=True)
    return (count, seed, r)


def run():
    print("=" * 70)
    print("CHECKPOINT 6D — Engagement Duration Tuning")
    print("=" * 70)

    # --- 5v5 all type permutations (parallelized) ---
    print("\n  5v5 — All Type Permutations (L5: each >= 10 seconds)")

    l5_jobs = [(ta, tb) for ta in UNIT_TYPES for tb in UNIT_TYPES]
    with multiprocessing.Pool() as pool:
        l5_results = pool.map(_run_5v5, l5_jobs)

    print(f"  {'Type A':<14} {'Type B':<14} {'Duration':>8} {'Winner':>7} {'Status':>7}")
    print(f"  {'-'*14} {'-'*14} {'-'*8} {'-'*7} {'-'*7}")

    l5_failures = []
    for ta, tb, r in l5_results:
        ok = r["duration_sec"] >= 10.0
        status = "OK" if ok else "FAIL"
        if not ok:
            l5_failures.append((ta, tb, r["duration_sec"]))
        print(f"  {ta:<14} {tb:<14} {r['duration_sec']:>7.1f}s {r['winner']:>7} {status:>7}")

    if l5_failures:
        print(f"\n  L5 FAILURES ({len(l5_failures)}):")
        for ta, tb, dur in l5_failures:
            print(f"    {ta} vs {tb}: {dur:.1f}s (need >=10s)")
    else:
        print(f"\n  L5: ALL PASS")

    # --- 50v50 and 100v100 (parallelized together) ---
    mixed_jobs = [(50, s) for s in [1, 2, 3]] + [(100, s) for s in [1, 2, 3]]
    with multiprocessing.Pool() as pool:
        mixed_results = pool.map(_run_mixed, mixed_jobs)

    l7_results = [r for count, seed, r in mixed_results if count == 50]
    l6_results = [r for count, seed, r in mixed_results if count == 100]

    # --- 50v50 mirror ---
    print(f"\n{'=' * 70}")
    print("  50v50 Mixed Mirror (L7: 150-200 seconds)")
    print(f"{'=' * 70}")

    for i, (count, seed, r) in enumerate(mixed_results):
        if count != 50:
            continue
        ok = 150.0 <= r["duration_sec"] <= 200.0
        status = "OK" if ok else "FAIL"
        print(f"  Seed {seed}: {r['duration_sec']:.1f}s | Winner: {r['winner']} | "
              f"Surv A: {r['survivors_a']}/{r['initial_a']} B: {r['survivors_b']}/{r['initial_b']} | {status}")

    avg_dur = sum(r["duration_sec"] for r in l7_results) / len(l7_results)
    print(f"\n  Average duration: {avg_dur:.1f}s (target: 150-200s)")

    print(f"\n  Kill Timeline (seed 1, 5-second buckets):")
    buckets = l7_results[0]["kill_buckets"]
    if buckets:
        max_t = max(buckets.keys())
        for t in range(0, max_t + 5, 5):
            count = buckets.get(t, 0)
            bar = "#" * count
            print(f"    {t:>3}-{t+5:<3}s: {count:>3} kills  {bar}")

    # --- 100v100 mixed ---
    print(f"\n{'=' * 70}")
    print("  100v100 Mixed (L6: > 60 seconds)")
    print(f"{'=' * 70}")

    for count, seed, r in mixed_results:
        if count != 100:
            continue
        ok = r["duration_sec"] > 60.0
        status = "OK" if ok else "FAIL"
        print(f"  Seed {seed}: {r['duration_sec']:.1f}s | Winner: {r['winner']} | "
              f"Surv A: {r['survivors_a']}/{r['initial_a']} B: {r['survivors_b']}/{r['initial_b']} | {status}")

    avg_dur = sum(r["duration_sec"] for r in l6_results) / len(l6_results)
    print(f"\n  Average duration: {avg_dur:.1f}s (target: >60s)")

    print(f"\n  Kill Timeline (seed 1, 5-second buckets):")
    buckets = l6_results[0]["kill_buckets"]
    if buckets:
        max_t = max(buckets.keys())
        for t in range(0, max_t + 5, 5):
            count = buckets.get(t, 0)
            bar = "#" * count
            print(f"    {t:>3}-{t+5:<3}s: {count:>3} kills  {bar}")

    print("\nCheckpoint 6D complete.")


if __name__ == "__main__":
    run()
