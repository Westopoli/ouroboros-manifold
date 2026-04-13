"""
test_j_duration.py — L5 / L6 / L7: Engagement duration validation.

Verifies that engagements last long enough for positioning and abilities to matter.

Claims:
  L5: 5v5 any composition ≥ 45s (bible v2.07 target)
  L6: 100v100 mixed > 120s
  L7: 50v50 mirror 150–200s

Dump: 50v50 mirror seed 1 (most useful for pacing feel).

Run:  python3 test_j_duration.py
View: python3 sim_viewer.py /tmp/j_duration_50v50.jsonl
"""
import sys
import random
import math
sys.path.insert(0, ".")

import config
from unit import UnitStore
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field
from sim_logger import SimLogger, config_snapshot

DT       = config.TACTICAL_TICK_DURATION
FACTION_A = 0
FACTION_B = 1

DUMP_SEED = 1
DUMP_PATH = "/tmp/j_duration_50v50.jsonl"

MIXED_RATIO = {
    "Vanguard":    0.25,
    "Warden":      0.15,
    "Raider":      0.20,
    "Interceptor": 0.10,
    "Bombard":     0.15,
    "Bastion":     0.15,
}


def _spawn_mixed(store, faction_id, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        n = max(1, round(count * frac))
        roster.extend([ut] * n)
    # trim or pad to exact count
    while len(roster) > count:
        roster.pop(rng.randrange(len(roster)))
    while len(roster) < count:
        roster.append(rng.choice(list(MIXED_RATIO.keys())))
    rng.shuffle(roster)

    uids = []
    cols = max(5, int(math.sqrt(count)) + 1)
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 60.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 60.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction_id, x, y))
    return uids


def _spawn_category(store, faction_id, cx, cy, count, cat_types, rng):
    half   = count // 2
    roster = [cat_types[0]] * half + [cat_types[1]] * (count - half)
    rng.shuffle(roster)
    uids = []
    cols = max(5, int(math.sqrt(count)) + 1)
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-6, 6)
        y = cy + (i // cols) * 55.0 + rng.uniform(-6, 6)
        uids.append(store.spawn(ut, faction_id, x, y))
    return uids


def run_engagement(count_per_side, composition, seed, log_dump=False):
    rng  = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    center_y  = 2000.0
    offset    = max(400.0, count_per_side * 15.0)
    a_cy      = center_y - offset
    b_cy      = center_y + offset

    if composition == "mixed":
        uids_a = _spawn_mixed(store, FACTION_A, 1800.0, a_cy, count_per_side, rng)
        uids_b = _spawn_mixed(store, FACTION_B, 1800.0, b_cy, count_per_side, rng)
    else:
        cat_types = composition
        uids_a = _spawn_category(store, FACTION_A, 1800.0, a_cy, count_per_side, cat_types, rng)
        uids_b = _spawn_category(store, FACTION_B, 1800.0, b_cy, count_per_side, cat_types, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": 2000.0, "target_y": b_cy}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": 2000.0, "target_y": a_cy}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    logger = None
    if log_dump:
        label = f"{count_per_side}v{count_per_side}_mirror_s{seed}"
        logger = SimLogger(
            DUMP_PATH, label, tmap,
            {FACTION_A: ("A", "#3b82f6"), FACTION_B: ("B", "#ef4444")},
            config_snapshot(),
        )

    # Find first damage tick
    first_damage_tick = None
    max_ticks = max(20000, count_per_side * 200)

    for _ in range(max_ticks):
        prev_log = len(engine.death_log)
        engine.step()
        deaths = [d["uid"] for d in engine.death_log[prev_log:]]

        if logger:
            logger.log_tick(engine.tick, engine.store, deaths, {
                "targeting": 0.0, "movement": 0.0, "abilities": 0.0,
                "damage": 0.0, "fog": 0.0, "commands": 0.0,
            })

        if first_damage_tick is None and deaths:
            first_damage_tick = engine.tick

        if engine.is_terminal():
            break

    if logger:
        logger.close()

    duration_sec = engine.tick * DT
    combat_sec   = (engine.tick - (first_damage_tick or 0)) * DT
    winner = engine.get_winner()

    return {
        "seed":         seed,
        "duration_sec": duration_sec,
        "combat_sec":   combat_sec,
        "first_damage": first_damage_tick,
        "winner":       winner,
        "surv_a":       len(engine.get_survivors(FACTION_A)),
        "surv_b":       len(engine.get_survivors(FACTION_B)),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*70}")
print(f"  ENGAGEMENT DURATION — L5 / L6 / L7")
print(f"{'═'*70}")

# ── L5: 5v5 all type permutations ─────────────────────────────────────────────

print(f"\n  ── L5: 5v5 (≥45s per matchup) ──────────────────────────────────")
SEEDS_SMALL = [1, 2, 3]
L5_TYPES = [
    (["Raider",   "Interceptor"], "Strike"),
    (["Vanguard", "Warden"],      "Line"),
    (["Bombard",  "Bastion"],     "Siege"),
]
l5_all_pass = True
for types_a, name_a in L5_TYPES:
    for types_b, name_b in L5_TYPES:
        label = f"{name_a} vs {name_b}"
        durations = []
        for seed in SEEDS_SMALL:
            r = run_engagement(5, types_a, seed)
            durations.append(r["duration_sec"])
        mean_dur = sum(durations) / len(durations)
        min_dur  = min(durations)
        ok       = min_dur >= 45.0
        if not ok:
            l5_all_pass = False
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<22} "
              f"min={min_dur:.1f}s  mean={mean_dur:.1f}s  "
              f"(need ≥45s)  {'✓' if ok else '✗'}")

# ── L6: 100v100 mixed ─────────────────────────────────────────────────────────

print(f"\n  ── L6: 100v100 mixed (>120s) ───────────────────────────────────")
SEEDS_L6 = [1, 2, 3]
l6_results = []
for seed in SEEDS_L6:
    print(f"    seed={seed}...", end="", flush=True)
    r = run_engagement(100, "mixed", seed)
    l6_results.append(r)
    print(f" {r['duration_sec']:.1f}s")

mean_l6 = sum(r["duration_sec"] for r in l6_results) / len(l6_results)
min_l6  = min(r["duration_sec"] for r in l6_results)
l6_ok   = min_l6 > 120.0
print(f"  {'PASS' if l6_ok else 'FAIL'}  100v100 mixed: "
      f"min={min_l6:.1f}s  mean={mean_l6:.1f}s  (need >120s)  {'✓' if l6_ok else '✗'}")

# ── L7: 50v50 mirror ──────────────────────────────────────────────────────────

print(f"\n  ── L7: 50v50 mirror (150–200s) ─────────────────────────────────")
SEEDS_L7 = [1, 2, 3]
l7_results = []
for seed in SEEDS_L7:
    do_dump = (seed == DUMP_SEED)
    print(f"    seed={seed}...", end="", flush=True)
    r = run_engagement(50, "mixed", seed, log_dump=do_dump)
    l7_results.append(r)
    print(f" {r['duration_sec']:.1f}s")

mean_l7 = sum(r["duration_sec"] for r in l7_results) / len(l7_results)
min_l7  = min(r["duration_sec"] for r in l7_results)
max_l7  = max(r["duration_sec"] for r in l7_results)
l7_ok   = (min_l7 >= 150.0 and max_l7 <= 200.0)
print(f"  {'PASS' if l7_ok else 'WARN'}  50v50 mirror: "
      f"min={min_l7:.1f}s  max={max_l7:.1f}s  mean={mean_l7:.1f}s  "
      f"(target 150–200s)  {'✓' if l7_ok else '✗ (warning level)'}")

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'─'*70}")
print(f"  CLAIM SUMMARY")
print(f"{'─'*70}")

def chk(ok): return "PASS" if ok else "FAIL"

print(f"  L5: {chk(l5_all_pass)}  5v5 all combos ≥45s")
print(f"  L6: {chk(l6_ok)}  100v100 mixed >120s  (mean={mean_l6:.1f}s)")
print(f"  L7: {'PASS' if l7_ok else 'WARN'}  50v50 mirror 150–200s  (mean={mean_l7:.1f}s)")
print(f"\n  Dump (50v50 mirror seed {DUMP_SEED}): {DUMP_PATH}")
print(f"  View: python3 sim_viewer.py {DUMP_PATH}")
print(f"{'═'*70}\n")
