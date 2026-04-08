import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_ATTACK_RANGE, CATEGORY_MAP
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field
from damage import _friendly_blocks_shot

FACTION_A = 0  # Strike force
FACTION_B = 1  # Line force
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000

MULTIPLIER_PAIRS = [
    (1.50, 0.75, "2.00:1"),
    (1.30, 0.85, "1.53:1"),
    (1.20, 0.90, "1.33:1"),
]

SCENARIOS = ["headon_10v10", "surround_10v10", "headon_15v10"]

# Mixed compositions — unit types don't match force category
STRIKE_COMP = [
    ("Vanguard", 3),   # front screen
    ("Raider", 5),     # glass cannons
    ("Interceptor", 2),
]

LINE_COMP = [
    ("Vanguard", 5),   # heavy front
    ("Warden", 3),     # support
    ("Raider", 2),     # flankers
]

# 15-unit versions (scaled proportionally)
STRIKE_COMP_15 = [
    ("Vanguard", 4),
    ("Raider", 8),
    ("Interceptor", 3),
]


def _spawn_force(store, faction, force_category, comp, cx, cy, rng):
    """Spawn units and override their category to the force's category tag."""
    cat_id = CATEGORY_MAP[force_category]
    uids = []
    i = 0
    for unit_type, count in comp:
        for _ in range(count):
            x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
            y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
            uid = store.spawn(unit_type, faction, x, y)
            store.category[uid] = cat_id  # override to force category
            uids.append(uid)
            i += 1
    return uids


def _firing_pct(store, uids, active):
    alive = [u for u in uids if store.alive[u]]
    if not alive:
        return 0.0
    firing = 0
    for uid in alive:
        tgt = store.auto_engage_target[uid]
        if tgt < 0 or not store.alive[tgt]:
            continue
        if _friendly_blocks_shot(store, uid, tgt, active):
            continue
        ax, ay = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tx, ty = store.data[tgt, FIELD_X], store.data[tgt, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        if dist <= store.data[uid, FIELD_ATTACK_RANGE]:
            firing += 1
    return firing / len(alive)


def _build(scenario, seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    queue = CommandQueue()

    if scenario == "headon_10v10":
        line_uids = _spawn_force(store, FACTION_B, "Line", LINE_COMP,
                                 2000.0, 2500.0, rng)
        strike_uids = _spawn_force(store, FACTION_A, "Strike", STRIKE_COMP,
                                   2000.0, 1500.0, rng)
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))

    elif scenario == "surround_10v10":
        line_uids = _spawn_force(store, FACTION_B, "Line", LINE_COMP,
                                 2000.0, 2000.0, rng)
        strike_a = _spawn_force(store, FACTION_A, "Strike", STRIKE_COMP[:2],
                                2000.0, 800.0, rng)
        # Second group: remaining comp
        strike_b = _spawn_force(store, FACTION_A, "Strike",
                                [STRIKE_COMP[2]],
                                2000.0, 3200.0, rng)
        # Split: 8 north (3 Van + 5 Raid), 2 south (2 Int)
        strike_uids = strike_a + strike_b
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_a,
                          params={"target_x": 2000.0, "target_y": 2000.0}))
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_b,
                          params={"target_x": 2000.0, "target_y": 2000.0}))

    elif scenario == "headon_15v10":
        line_uids = _spawn_force(store, FACTION_B, "Line", LINE_COMP,
                                 2000.0, 2500.0, rng)
        strike_uids = _spawn_force(store, FACTION_A, "Strike", STRIKE_COMP_15,
                                   2000.0, 1500.0, rng)
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))

    return tmap, store, strike_uids, line_uids, queue


def _run_one(scenario, seed):
    tmap, store, strike_uids, line_uids, queue = _build(scenario, seed)
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    fire_s, fire_l = [], []
    last_sample = -999

    for _ in range(MAX_TICKS):
        engine.step()
        if engine.tick >= last_sample + 50:
            active = store.active_ids()
            if any(store.auto_engage_target[u] >= 0 for u in active if store.alive[u]):
                fire_s.append(_firing_pct(store, strike_uids, active))
                fire_l.append(_firing_pct(store, line_uids, active))
                last_sample = engine.tick
        if engine.is_terminal():
            break

    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    winner = "Strike" if surv_a > surv_b else ("Line" if surv_b > surv_a else "Draw")
    avg_fs = sum(fire_s) / len(fire_s) if fire_s else 0.0
    avg_fl = sum(fire_l) / len(fire_l) if fire_l else 0.0
    return winner, engine.tick * DT, surv_a, surv_b, avg_fs, avg_fl


def run():
    seeds = list(range(1, 26))

    orig_table = {}
    for cat_a in config.CATEGORY_MULTIPLIER:
        orig_table[cat_a] = dict(config.CATEGORY_MULTIPLIER[cat_a])

    print("=" * 95)
    print("6J MIXED COMP — Strike vs Line with mixed unit types, force-level RPS")
    print("=" * 95)
    print()
    print("  Strike force (cat=Strike): 3 Vanguard + 5 Raider + 2 Interceptor")
    print("  Line force   (cat=Line):   5 Vanguard + 3 Warden + 2 Raider")
    print("  15-unit Strike:            4 Vanguard + 8 Raider + 3 Interceptor")
    print("  Category override: all units in a force get the force's category tag")

    all_results = {}

    for line_vs_strike, strike_vs_line, label in MULTIPLIER_PAIRS:
        config.CATEGORY_MULTIPLIER["Line"]["Strike"] = line_vs_strike
        config.CATEGORY_MULTIPLIER["Strike"]["Line"] = strike_vs_line

        print(f"\n{'=' * 95}")
        print(f"  Line→Strike {line_vs_strike:.2f}  Strike→Line {strike_vs_line:.2f}  (eff {label})")
        print(f"{'=' * 95}")

        pair_results = {}
        for scenario in SCENARIOS:
            wins_s = 0
            total_dur = 0.0
            total_ss = 0
            total_sl = 0
            total_fs = 0.0
            total_fl = 0.0

            for seed in seeds:
                w, dur, ss, sl, fs, fl = _run_one(scenario, seed)
                if w == "Strike":
                    wins_s += 1
                total_dur += dur
                total_ss += ss
                total_sl += sl
                total_fs += fs
                total_fl += fl

            n = len(seeds)
            pair_results[scenario] = {
                "wins": wins_s,
                "dur": total_dur / n,
                "ss": total_ss / n,
                "sl": total_sl / n,
                "fs": total_fs / n,
                "fl": total_fl / n,
            }

        hdr = (f"  {'Scenario':<20} {'S wins':>8} {'Avg dur':>9} "
               f"{'S surv':>7} {'L surv':>7} {'S fire%':>8} {'L fire%':>8}")
        print(hdr)
        print(f"  {'-'*20} {'-'*8} {'-'*9} {'-'*7} {'-'*7} {'-'*8} {'-'*8}")
        for scenario in SCENARIOS:
            r = pair_results[scenario]
            print(f"  {scenario:<20} {r['wins']:>5}/25 {r['dur']:>8.1f}s "
                  f"{r['ss']:>7.1f} {r['sl']:>7.1f} "
                  f"{r['fs']:>7.0%} {r['fl']:>7.0%}")

        all_results[label] = pair_results

    for cat_a in orig_table:
        for cat_b in orig_table[cat_a]:
            config.CATEGORY_MULTIPLIER[cat_a][cat_b] = orig_table[cat_a][cat_b]

    print(f"\n{'=' * 95}")
    print("  FINAL COMPARISON")
    print(f"{'=' * 95}")
    print(f"  {'Multiplier (eff)':>20} {'Head-on S wins':>15} {'Surround S wins':>16} {'15v10 S wins':>13}")
    print(f"  {'-'*20} {'-'*15} {'-'*16} {'-'*13}")

    target_hit = None
    for _, _, label in MULTIPLIER_PAIRS:
        r = all_results[label]
        hw = r["headon_10v10"]["wins"]
        sw = r["surround_10v10"]["wins"]
        nw = r["headon_15v10"]["wins"]
        hw_pct = hw / 25
        sw_pct = sw / 25
        nw_pct = nw / 25

        marker = ""
        if hw_pct < 0.30 and 0.30 <= sw_pct <= 0.60 and nw_pct > 0.60:
            marker = " <-- TARGET"
            if target_hit is None:
                target_hit = label

        print(f"  {label:>20} {hw:>12}/25 {sw:>13}/25 {nw:>10}/25{marker}")

    print()
    if target_hit:
        print(f"  Target criteria met at {target_hit}")
    else:
        print("  No pair met all three target criteria.")
        print("  Target: head-on <30%, surround 30-60%, 15v10 >60%")

    print(f"\n{'=' * 95}")
    print("Mixed comp tuning complete.")


if __name__ == "__main__":
    run()
