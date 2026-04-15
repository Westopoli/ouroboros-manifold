import math
import random
import subprocess
import sys
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_SPEED
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field

DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 10000
FACTION_A, FACTION_B = 0, 1


# ── Spawn helpers ──────────────────────────────────────────────────────────────

def _spawn(store, faction, unit_types, cx, cy, count, rng):
    uids = []
    cols = max(1, int(math.ceil(math.sqrt(count))))
    for i in range(count):
        ut = unit_types[i % len(unit_types)]
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_mixed(store, faction, cx, cy, count, rng):
    n_line   = int(count * 0.4)
    n_strike = int(count * 0.3)
    n_siege  = count - n_line - n_strike
    uids = []
    cols = max(1, int(math.ceil(math.sqrt(count))))
    roster = (["Vanguard"] * 2 + ["Warden"]) * (n_line // 3 + 1)
    roster += (["Raider", "Interceptor"]) * (n_strike // 2 + 1)
    roster += (["Bombard", "Bastion"]) * (n_siege // 2 + 1)
    roster = roster[:count]
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


# ── Engagement runner ──────────────────────────────────────────────────────────

def _run(types_a, types_b, count_a, count_b, cx_a, cy_a, cx_b, cy_b, seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    uids_a = _spawn(store, FACTION_A, types_a, cx_a, cy_a, count_a, rng)
    uids_b = _spawn(store, FACTION_B, types_b, cx_b, cy_b, count_b, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": cx_b, "target_y": cy_b}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": cx_a, "target_y": cy_a}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    first_dmg_tick = None
    max_hp = {uid: store.data[uid, FIELD_HP] for uid in uids_a + uids_b}

    for _ in range(MAX_TICKS):
        engine.step()
        if first_dmg_tick is None:
            for uid in uids_a + uids_b:
                if store.alive[uid] and store.data[uid, FIELD_HP] < max_hp[uid]:
                    first_dmg_tick = engine.tick
                    break
            if first_dmg_tick is None and engine.death_log:
                first_dmg_tick = engine.tick
        if engine.is_terminal():
            break

    duration = (engine.tick - first_dmg_tick) if first_dmg_tick is not None else 0
    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    return {"ticks": engine.tick, "duration": duration, "surv_a": surv_a, "surv_b": surv_b}


def _run_mixed(count, seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    cx_a, cy_a = 1000.0, 2000.0
    cx_b, cy_b = 3000.0, 2000.0

    uids_a = _spawn_mixed(store, FACTION_A, cx_a, cy_a, count, rng)
    uids_b = _spawn_mixed(store, FACTION_B, cx_b, cy_b, count, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": cx_b, "target_y": cy_b}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": cx_a, "target_y": cy_a}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    first_dmg_tick = None
    max_hp = {uid: store.data[uid, FIELD_HP] for uid in uids_a + uids_b}

    for _ in range(MAX_TICKS):
        engine.step()
        if first_dmg_tick is None:
            for uid in uids_a + uids_b:
                if store.alive[uid] and store.data[uid, FIELD_HP] < max_hp[uid]:
                    first_dmg_tick = engine.tick
                    break
            if first_dmg_tick is None and engine.death_log:
                first_dmg_tick = engine.tick
        if engine.is_terminal():
            break

    duration = (engine.tick - first_dmg_tick) if first_dmg_tick is not None else 0
    return {"ticks": engine.tick, "duration": duration}


# ── L5 ─────────────────────────────────────────────────────────────────────────

def test_l5():
    print("=" * 70)
    print("L5 — Small skirmish duration floor  (5v5, all matchups ≥ 45s)")
    print("=" * 70)

    FLOOR_TICKS = 900   # 45 seconds
    SEEDS = [1, 2, 3]
    matchups = [
        ("Strike",  ["Raider", "Interceptor"], "Strike",  ["Raider", "Interceptor"]),
        ("Line",    ["Vanguard", "Warden"],    "Line",    ["Vanguard", "Warden"]),
        ("Siege",   ["Bombard", "Bastion"],    "Siege",   ["Bombard", "Bastion"]),
        ("Strike",  ["Raider", "Interceptor"], "Line",    ["Vanguard", "Warden"]),
        ("Strike",  ["Raider", "Interceptor"], "Siege",   ["Bombard", "Bastion"]),
        ("Line",    ["Vanguard", "Warden"],    "Siege",   ["Bombard", "Bastion"]),
    ]

    print(f"\n  {'Matchup':<28} {'Seed':>5} {'Duration':>10}  Status")
    print(f"  {'-'*28} {'-'*5} {'-'*10}  ------")

    all_pass = True
    for cat_a, types_a, cat_b, types_b in matchups:
        label = f"{cat_a} vs {cat_b}"
        for seed in SEEDS:
            r = _run(types_a, types_b, 5, 5, 1600.0, 2000.0, 2400.0, 2000.0, seed)
            dur_s = r["duration"] * DT
            ok = r["duration"] >= FLOOR_TICKS
            if not ok:
                all_pass = False
            print(f"  {label:<28} {seed:>5} {dur_s:>9.1f}s  {'PASS' if ok else 'FAIL'}")

    print(f"\n  L5: {'PASS' if all_pass else 'FAIL'}  (floor={FLOOR_TICKS * DT:.0f}s)")
    return all_pass


# ── L6 ─────────────────────────────────────────────────────────────────────────

def test_l6():
    print("\n" + "=" * 70)
    print("L6 — Large battle duration floor  (100v100 mixed > 120s)")
    print("=" * 70)

    FLOOR_TICKS = 2400  # 120 seconds
    SEEDS = list(range(1, 11))
    COUNT = 100

    print(f"\n  {'Seed':>6} {'Duration':>10}  Status")
    print(f"  {'-'*6} {'-'*10}  ------")

    durations = []
    all_pass = True
    for seed in SEEDS:
        r = _run_mixed(COUNT, seed)
        dur_s = r["duration"] * DT
        ok = r["duration"] >= FLOOR_TICKS
        if not ok:
            all_pass = False
        durations.append(r["duration"])
        print(f"  {seed:>6} {dur_s:>9.1f}s  {'PASS' if ok else 'FAIL'}")

    avg = sum(durations) / len(durations) * DT
    print(f"\n  Avg duration: {avg:.1f}s")
    print(f"  L6: {'PASS' if all_pass else 'FAIL'}  (floor={FLOOR_TICKS * DT:.0f}s)")
    return all_pass


# ── L7 ─────────────────────────────────────────────────────────────────────────

def test_l7():
    print("\n" + "=" * 70)
    print("L7 — Mirror match baseline  (50v50 identical, 150–200s)")
    print("=" * 70)

    LO_TICKS = 3000  # 150 seconds
    HI_TICKS = 4000  # 200 seconds
    SEEDS = list(range(1, 11))
    COUNT = 50

    print(f"\n  {'Seed':>6} {'Duration':>10}  Status")
    print(f"  {'-'*6} {'-'*10}  ------")

    durations = []
    passes = 0
    for seed in SEEDS:
        r = _run_mixed(COUNT, seed)
        dur_s = r["duration"] * DT
        in_band = LO_TICKS <= r["duration"] <= HI_TICKS
        if in_band:
            passes += 1
        durations.append(r["duration"])
        print(f"  {seed:>6} {dur_s:>9.1f}s  {'in band' if in_band else 'out of band'}")

    avg = sum(durations) / len(durations) * DT
    ok = passes >= len(SEEDS) * 0.7  # warning: 70% in-band counts as pass
    print(f"\n  Avg duration: {avg:.1f}s   In-band: {passes}/{len(SEEDS)}")
    print(f"  L7 (warning): {'PASS' if ok else 'FAIL'}  (target 150–200s, ≥70% in-band)")
    return ok


# ── L17 ────────────────────────────────────────────────────────────────────────

def test_l17():
    print("\n" + "=" * 70)
    print("L17 — Stage 5 regression")
    print("=" * 70)

    stage5 = [
        "test_checkpoint_a",
        "test_checkpoint_b",
        "test_checkpoint_c",
        "test_checkpoint_d",
        "test_checkpoint_e",
        "test_checkpoint_f",
        "test_checkpoint_g",
        "test_checkpoint_g5",
        "test_checkpoint_h",   # pre-existing failure (MockRegion.name) — not Stage 6
        "test_checkpoint_i",
        "test_checkpoint_j",
    ]

    print()
    results = {}
    for name in stage5:
        proc = subprocess.run(
            [sys.executable, f"{name}.py"],
            capture_output=True, text=True
        )
        ok = proc.returncode == 0
        results[name] = ok
        note = ""
        if name == "test_checkpoint_h" and not ok:
            note = "  ← pre-existing, not caused by Stage 6"
        print(f"  {name:<35} {'PASS' if ok else 'FAIL'}{note}")

    pre_existing = {"test_checkpoint_h"}
    regressions = [n for n, ok in results.items() if not ok and n not in pre_existing]
    all_pass = len(regressions) == 0

    print(f"\n  New regressions: {regressions if regressions else 'none'}")
    print(f"  L17: {'PASS' if all_pass else 'FAIL'}")
    return all_pass


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    print("=" * 70)
    print("CHECKPOINT 6L — Engagement Duration + Stage 5 Regression")
    print("=" * 70)

    l5 = test_l5()
    l6 = test_l6()
    l7 = test_l7()
    l17 = test_l17()

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  L5  Small skirmish floor    {'PASS' if l5  else 'FAIL'}")
    print(f"  L6  Large battle floor      {'PASS' if l6  else 'FAIL'}")
    print(f"  L7  Mirror match baseline   {'PASS' if l7  else 'FAIL'}  (warning)")
    print(f"  L17 Stage 5 regression      {'PASS' if l17 else 'FAIL'}")
    print("\nCheckpoint 6L complete.")


if __name__ == "__main__":
    run()
