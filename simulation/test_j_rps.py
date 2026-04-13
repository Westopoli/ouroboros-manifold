"""
test_j_rps.py — L1/L2/L3: RPS triangle validation.

6 matchups × 5 seeds. Both forces attack_move toward center.
Measures win rate, duration, force retention per matchup.

Claims checked:
  L1: Strike beats Siege  — winner >60% win rate, winner retention >60%
  L2: Siege beats Line    — same
  L3: Line beats Strike   — same
  Mirrors: ~50/50

Dump written for Strike vs Siege seed 1 (L1 failure scenario — most useful to inspect).

Run:  python3 test_j_rps.py
View: python3 sim_viewer.py /tmp/j_rps_strike_vs_siege.jsonl
"""
import sys
import math
import random
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from power_rating import compute_power_rating
from test_maps import open_field
from sim_logger import SimLogger, config_snapshot

FACTION_A = 0
FACTION_B = 1
MAX_TICKS = 12000   # 600s cap — far more than any real fight needs
SEEDS     = [1, 2, 3, 4, 5]

CATEGORY_UNITS = {
    "Strike": ["Raider",   "Interceptor"],
    "Line":   ["Vanguard", "Warden"],
    "Siege":  ["Bombard",  "Bastion"],
}

MATCHUPS = [
    ("Strike", "Siege",  "Strike > Siege (L1)",   True),
    ("Siege",  "Line",   "Siege > Line  (L2)",    True),
    ("Line",   "Strike", "Line > Strike (L3)",    True),
    ("Strike", "Strike", "Strike mirror",         False),
    ("Line",   "Line",   "Line mirror",           False),
    ("Siege",  "Siege",  "Siege mirror",          False),
]

DUMP_MATCHUP = ("Strike", "Siege")
DUMP_SEED    = 1
DUMP_PATH    = "/tmp/j_rps_strike_vs_siege.jsonl"


def _force_power_rating(unit_type):
    s = dict(config.UNIT_STATS[unit_type])
    s["unit_type"] = unit_type
    return compute_power_rating(s)


def _spawn_force(store, category, faction_id, cx, cy, count, rng):
    types = CATEGORY_UNITS[category]
    half  = count // 2
    roster = [types[0]] * half + [types[1]] * (count - half)
    rng.shuffle(roster)
    uids = []
    cols = 5
    for i, ut in enumerate(roster):
        jx = rng.uniform(-8, 8)
        jy = rng.uniform(-8, 8)
        x  = cx + (i % cols) * 55.0 + jx
        y  = cy + (i // cols) * 55.0 + jy
        uids.append(store.spawn(ut, faction_id, x, y))
    return uids


def _force_power(store, uids):
    total = 0.0
    for uid in uids:
        s = dict(config.UNIT_STATS[store.unit_type[uid]])
        s["unit_type"] = store.unit_type[uid]
        total += compute_power_rating(s)
    return total


def run_matchup(cat_a, cat_b, seed, log_dump=False):
    rng   = random.Random(seed)
    tmap  = open_field()
    store = UnitStore()
    count = 10  # units per side

    # Force A south of center, Force B north of center
    uids_a = _spawn_force(store, cat_a, FACTION_A, 1800.0, 1400.0, count, rng)
    uids_b = _spawn_force(store, cat_b, FACTION_B, 1800.0, 2600.0, count, rng)

    power_a = _force_power(store, uids_a)
    power_b = _force_power(store, uids_b)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": 2000.0, "target_y": 2600.0}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": 2000.0, "target_y": 1400.0}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    logger = None
    if log_dump:
        logger = SimLogger(
            DUMP_PATH, f"rps_{cat_a}_vs_{cat_b}_s{seed}", tmap,
            {FACTION_A: (cat_a, "#3b82f6"), FACTION_B: (cat_b, "#ef4444")},
            config_snapshot(),
        )

    first_damage_tick = None
    for _ in range(MAX_TICKS):
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

    winner = engine.get_winner()
    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    ret_a  = surv_a / count
    ret_b  = surv_b / count

    winner_label = (
        "A" if winner == FACTION_A else
        "B" if winner == FACTION_B else
        "Draw"
    )

    return {
        "seed":          seed,
        "winner":        winner_label,
        "duration_sec":  engine.tick * config.TACTICAL_TICK_DURATION,
        "survivors_a":   surv_a,
        "survivors_b":   surv_b,
        "retention_a":   ret_a,
        "retention_b":   ret_b,
        "power_a":       power_a,
        "power_b":       power_b,
        "parity":        power_a / power_b if power_b > 0 else 0,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*70}")
print(f"  TACTICAL RPS TRIANGLE — L1 / L2 / L3")
print(f"  {len(SEEDS)} seeds per matchup  |  10 units per side")
print(f"{'═'*70}")

all_results = {}

for cat_a, cat_b, label, is_rps in MATCHUPS:
    results = []
    for seed in SEEDS:
        do_dump = (cat_a, cat_b) == DUMP_MATCHUP and seed == DUMP_SEED
        r = run_matchup(cat_a, cat_b, seed, log_dump=do_dump)
        results.append(r)
        print(f"  {label:<28} seed={seed}  winner={r['winner']}  "
              f"dur={r['duration_sec']:5.1f}s  "
              f"ret_A={r['retention_a']*100:4.0f}%  ret_B={r['retention_b']*100:4.0f}%  "
              f"parity={r['parity']:.2f}")

    wins_a = sum(1 for r in results if r["winner"] == "A")
    wins_b = sum(1 for r in results if r["winner"] == "B")
    mean_dur  = sum(r["duration_sec"] for r in results) / len(results)
    mean_pa   = sum(r["parity"] for r in results) / len(results)

    winner_ret  = []
    for r in results:
        if r["winner"] == "A":
            winner_ret.append(r["retention_a"])
        elif r["winner"] == "B":
            winner_ret.append(r["retention_b"])
    mean_winner_ret = (sum(winner_ret) / len(winner_ret)) if winner_ret else 0.0

    all_results[(cat_a, cat_b)] = {
        "wins_a": wins_a, "wins_b": wins_b, "mean_dur": mean_dur,
        "mean_winner_ret": mean_winner_ret, "mean_parity": mean_pa,
        "is_rps": is_rps, "label": label,
    }
    print()

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'─'*70}")
print(f"  SUMMARY")
print(f"{'─'*70}")
print(f"  {'Matchup':<30} {'A wins':>7} {'B wins':>7} {'Mean dur':>9} "
      f"{'Winner ret':>11} {'Parity':>7}")
print(f"  {'─'*30} {'─'*7} {'─'*7} {'─'*9} {'─'*11} {'─'*7}")

for (cat_a, cat_b, label, _), v in zip(MATCHUPS, all_results.values()):
    print(f"  {label:<30} {v['wins_a']:>7} {v['wins_b']:>7} "
          f"{v['mean_dur']:>8.1f}s {v['mean_winner_ret']*100:>10.0f}% "
          f"{v['mean_parity']:>7.2f}")

# ── Claim evaluation ──────────────────────────────────────────────────────────

print(f"\n{'─'*70}")
print(f"  CLAIM EVALUATION")
print(f"{'─'*70}")

RPS_EXPECTED = {
    ("Strike", "Siege"):  "A",  # L1: Strike beats Siege
    ("Siege",  "Line"):   "A",  # L2: Siege beats Line
    ("Line",   "Strike"): "A",  # L3: Line beats Strike
}

n = len(SEEDS)
for (cat_a, cat_b), expected_winner in RPS_EXPECTED.items():
    v    = all_results[(cat_a, cat_b)]
    wins = v["wins_a"] if expected_winner == "A" else v["wins_b"]
    win_rate = wins / n
    ret      = v["mean_winner_ret"]
    label    = v["label"]

    win_ok = win_rate >= 0.6
    ret_ok = ret      >= 0.6
    status = "PASS" if (win_ok and ret_ok) else "FAIL"

    print(f"  {status}  {label}")
    print(f"         win rate {win_rate*100:.0f}%  (need ≥60%)  {'✓' if win_ok else '✗'}")
    print(f"         winner retention {ret*100:.0f}%  (need ≥60%)  {'✓' if ret_ok else '✗'}")

print(f"\n  Dump (Strike vs Siege s{DUMP_SEED}): {DUMP_PATH}")
print(f"  View: python3 sim_viewer.py {DUMP_PATH}")
print(f"{'═'*70}\n")
