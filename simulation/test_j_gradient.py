"""
test_j_gradient.py — L4: Soft RPS gradient validation.

Strike vs Line, 4 tiers with increasing defender disadvantage. 25 seeds per tier.
The geometric mechanism: Line's front rank halts on engagement (stationary-immovable),
later-arriving Line units deflect via probe steering rather than reaching firing
position. Result: reduced Line firing % in flank scenarios vs head-on.

Tiers:
  T1: Head-on — Strike attacks Line directly, both formed
  T2: Wall-constrained — Line packed against east wall, Strike approaches from west
      (Line compressed into fewer rows, later units blocked by front rank + wall)
  T3a: Column flank — Line in single column facing north, Strike flanks from west
       (Strike plain_moves to west side of column, then attack_moves across)
  T3b: Engaged flank — Line already fighting Siege, Strike arrives from west flank
       (Line halted on Siege targets, Strike attacks from perpendicular angle)

Claims (L4):
  TTW ratio T2/T1 ≥ 1.3  (Strike survives longer when Line is constrained)
  TTW ratio T3/T1 ≥ 1.6
  T1 win rate ≤ 5%
  Monotonic improvement in firing% from T1 → T3

Dump: T3a seed 1 (most instructive flanking geometry to watch)

Run:  python3 test_j_gradient.py
View: python3 sim_viewer.py /tmp/j_gradient_t3a.jsonl
"""
import sys
import math
import random
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_ATTACK_RANGE
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field
from sim_logger import SimLogger, config_snapshot

FACTION_S = 0   # Strike
FACTION_L = 1   # Line
N         = 12  # units per side (6 Raider + 6 Interceptor vs 8 Vanguard + 4 Warden)
SEEDS     = list(range(1, 26))   # 25 seeds per tier
MAX_TICKS = 8000
DT        = config.TACTICAL_TICK_DURATION

DUMP_SEED = 1
DUMP_PATH = "/tmp/j_gradient_t3a.jsonl"


def _spawn_strike(store, cx, cy, rng):
    uids = []
    types = ["Raider"] * 6 + ["Interceptor"] * 6
    rng.shuffle(types)
    for i, ut in enumerate(types):
        x = cx + (i % 4) * 45.0 + rng.uniform(-6, 6)
        y = cy + (i // 4) * 45.0 + rng.uniform(-6, 6)
        uids.append(store.spawn(ut, FACTION_S, x, y))
    return uids


def _spawn_line(store, cx, cy, rng, formation="grid"):
    uids = []
    types = ["Vanguard"] * 8 + ["Warden"] * 4
    rng.shuffle(types)
    if formation == "grid":
        for i, ut in enumerate(types):
            x = cx + (i % 4) * 50.0 + rng.uniform(-6, 6)
            y = cy + (i // 4) * 50.0 + rng.uniform(-6, 6)
            uids.append(store.spawn(ut, FACTION_L, x, y))
    elif formation == "column":
        # Tight column: 2 wide, 6 deep — oriented north-south
        for i, ut in enumerate(types):
            x = cx + (i % 2) * 40.0 + rng.uniform(-4, 4)
            y = cy + (i // 2) * 70.0 + rng.uniform(-4, 4)
            uids.append(store.spawn(ut, FACTION_L, x, y))
    return uids


def _fire_pct(store, uids):
    firing = 0
    alive  = 0
    for uid in uids:
        if not store.alive[uid]:
            continue
        alive += 1
        tgt = store.auto_engage_target[uid]
        if tgt >= 0 and store.alive[tgt]:
            firing += 1
    return (firing / alive) if alive > 0 else 0.0


def _run_tier(seed, tier, log_dump=False):
    rng   = random.Random(seed)
    tmap  = open_field()
    store = UnitStore()

    logger = None

    if tier == "T1":
        # Head-on: Strike south, Line north, both attack_move toward center
        su = _spawn_strike(store, 1800.0, 1200.0, rng)
        lu = _spawn_line(store, 1800.0, 2600.0, rng, "grid")

        queue = CommandQueue()
        queue.add(Command(tick=0, type="attack_move", unit_ids=su,
                          params={"target_x": 2000.0, "target_y": 2600.0}))
        queue.add(Command(tick=0, type="attack_move", unit_ids=lu,
                          params={"target_x": 2000.0, "target_y": 1200.0}))

    elif tier == "T2":
        # Wall-constrained: Line packed in east half (x=2800-3100), Strike approaches from west.
        # Line is compressed into a tighter horizontal band; front units block rear units.
        su = _spawn_strike(store, 500.0, 1800.0, rng)
        lu = _spawn_line(store, 2850.0, 1800.0, rng, "grid")

        queue = CommandQueue()
        queue.add(Command(tick=0, type="attack_move", unit_ids=su,
                          params={"target_x": 2950.0, "target_y": 1950.0}))
        queue.add(Command(tick=0, type="attack_move", unit_ids=lu,
                          params={"target_x": 500.0, "target_y": 1950.0}))

    elif tier == "T3a":
        # Flank vs column: Line in north-south column at x=2000, Strike starts at west.
        # Strike plain_moves to flanking position (west of Line midpoint) then attack_moves.
        su = _spawn_strike(store, 200.0, 1600.0, rng)
        lu = _spawn_line(store, 1980.0, 1400.0, rng, "column")
        line_mid_y = 1400.0 + (N // 4) * 70.0  # midpoint of column

        queue = CommandQueue()
        # Phase 1: plain move to flanking position west of Line's center
        queue.add(Command(tick=0, type="move", unit_ids=su,
                          params={"target_x": 700.0, "target_y": line_mid_y}))
        # Phase 2: attack_move from flank position into column
        queue.add(Command(tick=200, type="attack_move", unit_ids=su,
                          params={"target_x": 2000.0, "target_y": line_mid_y}))

        if log_dump:
            logger = SimLogger(
                DUMP_PATH, "gradient_T3a_s1", tmap,
                {FACTION_S: ("Strike", "#3b82f6"), FACTION_L: ("Line", "#ef4444")},
                config_snapshot(),
            )

    elif tier == "T3b":
        # Engaged flank: Line attack_moves against Siege (Bastions), Strike flanks from west.
        # When Strike arrives, Line is already halted engaging Siege — can't respond to flank.
        siege_uids = []
        for i in range(4):  # 4 Bastions in the east
            x = 2800.0 + (i % 2) * 70.0
            y = 1800.0 + (i // 2) * 70.0
            siege_uids.append(store.spawn("Bastion", 2, x, y))  # faction 2 = Siege (dummy)

        su = _spawn_strike(store, 200.0, 1700.0, rng)
        lu = _spawn_line(store, 1800.0, 1700.0, rng, "grid")

        queue = CommandQueue()
        # Line engages Siege immediately
        queue.add(Command(tick=0, type="attack_move", unit_ids=lu,
                          params={"target_x": 2800.0, "target_y": 1850.0}))
        # Strike: plain_move to flanking position, then attack Line from west
        queue.add(Command(tick=0, type="move", unit_ids=su,
                          params={"target_x": 700.0, "target_y": 1950.0}))
        queue.add(Command(tick=150, type="attack_move", unit_ids=su,
                          params={"target_x": 2000.0, "target_y": 1850.0}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    # Track per-tick stats after first contact
    first_contact_tick = None
    fire_pct_samples   = []   # (tick, line_fire_pct)
    damage_ticks_strike = 0   # ticks Strike units took damage
    total_damage_to_s   = 0.0
    total_damage_to_l   = 0.0

    prev_hp_s = {uid: store.data[uid, FIELD_HP] for uid in su}
    prev_hp_l = {uid: store.data[uid, FIELD_HP] for uid in lu}

    for t in range(MAX_TICKS):
        prev_log = len(engine.death_log)
        engine.step()
        deaths = [d["uid"] for d in engine.death_log[prev_log:]]

        if logger:
            logger.log_tick(engine.tick, engine.store, deaths, {
                "targeting": 0.0, "movement": 0.0, "abilities": 0.0,
                "damage": 0.0, "fog": 0.0, "commands": 0.0,
            })

        # Track firing %
        if first_contact_tick is None:
            # Check for first damage
            for uid in su:
                if store.alive[uid]:
                    new_hp = store.data[uid, FIELD_HP]
                    if new_hp < prev_hp_s.get(uid, new_hp):
                        first_contact_tick = engine.tick
            for uid in lu:
                if store.alive[uid]:
                    new_hp = store.data[uid, FIELD_HP]
                    if new_hp < prev_hp_l.get(uid, new_hp):
                        first_contact_tick = engine.tick

        # Update HP snapshots
        for uid in su:
            if store.alive[uid]:
                prev_hp_s[uid] = store.data[uid, FIELD_HP]
        for uid in lu:
            if store.alive[uid]:
                prev_hp_l[uid] = store.data[uid, FIELD_HP]

        if first_contact_tick is not None:
            fp = _fire_pct(store, lu)
            fire_pct_samples.append(fp)

        if engine.is_terminal():
            break

    if logger:
        logger.close()

    # Compute TTW (time to wipe — engagement duration from first contact to end)
    duration_ticks = engine.tick
    ttw = (duration_ticks - (first_contact_tick or 0)) * DT

    winner = engine.get_winner()
    surv_s = len(engine.get_survivors(FACTION_S))
    surv_l = len(engine.get_survivors(FACTION_L))

    mean_fire_pct = (sum(fire_pct_samples) / len(fire_pct_samples)
                     if fire_pct_samples else 0.0)

    # Damage ratio: total damage dealt to Line / total damage dealt to Strike
    # (proxy: HP lost)
    hp_lost_s = sum(config.UNIT_STATS[t]["hp"] for t in ["Raider"]*6 + ["Interceptor"]*6) - \
                sum(store.data[uid, FIELD_HP] for uid in su if store.alive[uid])
    hp_lost_l = sum(config.UNIT_STATS[t]["hp"] for t in ["Vanguard"]*8 + ["Warden"]*4) - \
                sum(store.data[uid, FIELD_HP] for uid in lu if store.alive[uid])
    dmg_ratio = (hp_lost_s / hp_lost_l) if hp_lost_l > 0 else 999.0

    return {
        "seed":          seed,
        "winner":        "S" if winner == FACTION_S else ("L" if winner == FACTION_L else "Draw"),
        "ttw":           ttw,
        "surv_s":        surv_s,
        "surv_l":        surv_l,
        "mean_fire_pct": mean_fire_pct,
        "dmg_ratio":     dmg_ratio,
        "first_contact": first_contact_tick,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

print(f"\n{'═'*70}")
print(f"  SOFT RPS GRADIENT — L4")
print(f"  25 seeds per tier  |  {N} units per side  |  Strike vs Line")
print(f"{'═'*70}")

TIERS = ["T1", "T2", "T3a", "T3b"]
tier_stats = {}

for tier in TIERS:
    print(f"\n  ── {tier} ", end="", flush=True)
    results = []
    for seed in SEEDS:
        do_dump = (tier == "T3a" and seed == DUMP_SEED)
        r = _run_tier(seed, tier, log_dump=do_dump)
        results.append(r)
        print(".", end="", flush=True)
    print()

    wins_s    = sum(1 for r in results if r["winner"] == "S")
    win_rate  = wins_s / len(SEEDS)
    mean_ttw  = sum(r["ttw"] for r in results) / len(results)
    std_ttw   = math.sqrt(sum((r["ttw"] - mean_ttw)**2 for r in results) / len(results))
    mean_fire = sum(r["mean_fire_pct"] for r in results) / len(results)
    mean_dmg  = sum(r["dmg_ratio"] for r in results) / len(results)

    tier_stats[tier] = {
        "win_rate": win_rate, "mean_ttw": mean_ttw, "std_ttw": std_ttw,
        "mean_fire_pct": mean_fire, "mean_dmg_ratio": mean_dmg,
    }

    print(f"    win_rate={win_rate*100:.1f}%  "
          f"TTW={mean_ttw:.1f}±{std_ttw:.1f}s  "
          f"Line_fire%={mean_fire*100:.1f}%  "
          f"dmg_ratio={mean_dmg:.2f}")

# ── Summary table ─────────────────────────────────────────────────────────────

print(f"\n{'─'*70}")
print(f"  GRADIENT SUMMARY (all tiers vs T1 baseline)")
print(f"{'─'*70}")
print(f"  {'Tier':<8} {'Win%':>6} {'TTW(s)':>8} {'TTW ratio':>10} "
      f"{'Line fire%':>11} {'Dmg ratio':>10}")
print(f"  {'─'*8} {'─'*6} {'─'*8} {'─'*10} {'─'*11} {'─'*10}")

t1_ttw = tier_stats["T1"]["mean_ttw"]
for tier in TIERS:
    s = tier_stats[tier]
    ttw_ratio = s["mean_ttw"] / t1_ttw if t1_ttw > 0 else 0
    print(f"  {tier:<8} {s['win_rate']*100:>5.1f}%  {s['mean_ttw']:>7.1f}s "
          f"  {ttw_ratio:>9.2f}x  {s['mean_fire_pct']*100:>9.1f}%  "
          f"  {s['mean_dmg_ratio']:>9.2f}")

# ── Claim evaluation ──────────────────────────────────────────────────────────

print(f"\n{'─'*70}")
print(f"  CLAIM EVALUATION (L4 — behavioral gradient)")
print(f"{'─'*70}")

t1 = tier_stats["T1"]
t2 = tier_stats["T2"]
t3 = tier_stats["T3a"]

t1_win_ok   = t1["win_rate"] <= 0.05
t2_ttw_ok   = (tier_stats["T2"]["mean_ttw"] / t1_ttw) >= 1.3 if t1_ttw > 0 else False
t3_ttw_ok   = (tier_stats["T3a"]["mean_ttw"] / t1_ttw) >= 1.6 if t1_ttw > 0 else False

# Monotonic checks
ttw_mono    = (t2["mean_ttw"] >= t1["mean_ttw"] and t3["mean_ttw"] >= t2["mean_ttw"])
fire_mono   = (t2["mean_fire_pct"] <= t1["mean_fire_pct"] and
               t3["mean_fire_pct"] <= t2["mean_fire_pct"])
dmg_mono    = (t2["mean_dmg_ratio"] >= t1["mean_dmg_ratio"] and
               t3["mean_dmg_ratio"] >= t2["mean_dmg_ratio"])

all_pass = t1_win_ok and t2_ttw_ok and t3_ttw_ok and ttw_mono

def chk(ok): return "✓" if ok else "✗"

print(f"  {chk(t1_win_ok)}  T1 win rate ≤5%: {tier_stats['T1']['win_rate']*100:.1f}%")
print(f"  {chk(t2_ttw_ok)}  TTW ratio T2/T1 ≥1.3x: {(t2['mean_ttw']/t1_ttw):.2f}x")
print(f"  {chk(t3_ttw_ok)}  TTW ratio T3/T1 ≥1.6x: {(t3['mean_ttw']/t1_ttw):.2f}x")
print(f"  {chk(ttw_mono)}  TTW monotone T1→T2→T3: {t1['mean_ttw']:.1f}→{t2['mean_ttw']:.1f}→{t3['mean_ttw']:.1f}s")
print(f"  {chk(fire_mono)}  Line firing% monotone (decreasing): "
      f"{t1['mean_fire_pct']*100:.1f}%→{t2['mean_fire_pct']*100:.1f}%→{t3['mean_fire_pct']*100:.1f}%")
print(f"  {chk(dmg_mono)}  Dmg ratio monotone (Strike deals relatively more): "
      f"{t1['mean_dmg_ratio']:.2f}→{t2['mean_dmg_ratio']:.2f}→{t3['mean_dmg_ratio']:.2f}")
print()
print(f"  Overall: {'PASS' if all_pass else 'FAIL'}")
print(f"\n  Dump (T3a seed {DUMP_SEED}): {DUMP_PATH}")
print(f"  View: python3 sim_viewer.py {DUMP_PATH}")
print(f"{'═'*70}\n")
