import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP
from power_rating import compute_power_rating
from tactical_engine import TacticalEngine
from movement import apply_group_move
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
MAX_TICKS = 10000

CATEGORY_UNITS = {
    "Strike": ["Raider", "Interceptor"],
    "Line":   ["Vanguard", "Warden"],
    "Siege":  ["Bombard", "Bastion"],
}

MATCHUPS = [
    ("Strike", "Siege",   "Strike > Siege (favored)"),
    ("Siege",  "Line",    "Siege > Line (favored)"),
    ("Line",   "Strike",  "Line > Strike (favored)"),
    ("Strike", "Strike",  "Strike vs Strike (mirror)"),
    ("Line",   "Line",    "Line vs Line (mirror)"),
    ("Siege",  "Siege",   "Siege vs Siege (mirror)"),
]

SEEDS = [1, 2, 3, 4, 5]


def get_power(unit_type):
    s = dict(config.UNIT_STATS[unit_type])
    s["unit_type"] = unit_type
    return compute_power_rating(s)


def build_force(store, category, faction_id, start_x, start_y, rng, target_count=10):
    types = CATEGORY_UNITS[category]
    half = target_count // 2
    roster = [types[0]] * half + [types[1]] * (target_count - half)
    rng.shuffle(roster)
    uids = []
    for i, ut in enumerate(roster):
        x = start_x + (i % 5) * 60.0
        y = start_y + (i // 5) * 60.0
        uid = store.spawn(ut, faction_id, x, y)
        uids.append(uid)
    return uids


def force_power(store, uids):
    total = 0.0
    for uid in uids:
        s = dict(config.UNIT_STATS[store.unit_type[uid]])
        s["unit_type"] = store.unit_type[uid]
        total += compute_power_rating(s)
    return total


def run_matchup(cat_a, cat_b, seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    uids_a = build_force(store, cat_a, FACTION_A, 1700.0, 1850.0, rng)
    uids_b = build_force(store, cat_b, FACTION_B, 2100.0, 1850.0, rng)

    apply_group_move(store, uids_a, 2000.0, 2000.0)
    apply_group_move(store, uids_b, 2000.0, 2000.0)

    power_a = force_power(store, uids_a)
    power_b = force_power(store, uids_b)
    initial_count_a = len(uids_a)
    initial_count_b = len(uids_b)

    engine = TacticalEngine(tmap, store)
    engine.run(MAX_TICKS)

    winner = engine.get_winner()
    duration_ticks = engine.tick
    duration_sec = duration_ticks * config.TACTICAL_TICK_DURATION

    survivors_a = len(engine.get_survivors(FACTION_A))
    survivors_b = len(engine.get_survivors(FACTION_B))
    retention_a = survivors_a / initial_count_a if initial_count_a > 0 else 0
    retention_b = survivors_b / initial_count_b if initial_count_b > 0 else 0

    winner_label = "A" if winner == FACTION_A else ("B" if winner == FACTION_B else "Draw")

    return {
        "seed": seed,
        "winner": winner_label,
        "duration_ticks": duration_ticks,
        "duration_sec": duration_sec,
        "survivors_a": survivors_a,
        "survivors_b": survivors_b,
        "retention_a": retention_a,
        "retention_b": retention_b,
        "power_a": power_a,
        "power_b": power_b,
    }


def run():
    print("=" * 70)
    print("CHECKPOINT 6C — Damage Model and RPS Triangle")
    print("=" * 70)

    print("\n  Power ratings per unit type:")
    for cat, types in CATEGORY_UNITS.items():
        for ut in types:
            pr = get_power(ut)
            print(f"    {ut:<14} ({cat:<6})  power = {pr:.1f}")
    print()

    all_results = {}
    for cat_a, cat_b, label in MATCHUPS:
        results = []
        for seed in SEEDS:
            r = run_matchup(cat_a, cat_b, seed)
            results.append(r)
        all_results[label] = results

    for label, results in all_results.items():
        print(f"\n  {'=' * 66}")
        print(f"  {label}")
        print(f"  {'=' * 66}")
        cat_a, cat_b = label.split(" vs " if " vs " in label else " > ")
        if " > " in label:
            parts = label.split(" > ")
            cat_a = parts[0]

        print(f"  {'Seed':>4} {'Winner':>7} {'Duration':>10} {'Surv A':>8} {'Surv B':>8} "
              f"{'Ret A':>7} {'Ret B':>7} {'Power A':>9} {'Power B':>9}")
        print(f"  {'----':>4} {'-------':>7} {'----------':>10} {'--------':>8} {'--------':>8} "
              f"{'-------':>7} {'-------':>7} {'---------':>9} {'---------':>9}")

        a_wins = 0
        total_duration = 0.0
        total_ret_a = 0.0
        total_ret_b = 0.0
        for r in results:
            if r["winner"] == "A":
                a_wins += 1
            total_duration += r["duration_sec"]
            total_ret_a += r["retention_a"]
            total_ret_b += r["retention_b"]
            print(f"  {r['seed']:>4} {r['winner']:>7} {r['duration_sec']:>8.1f}s "
                  f"{r['survivors_a']:>8} {r['survivors_b']:>8} "
                  f"{r['retention_a']:>6.1%} {r['retention_b']:>6.1%} "
                  f"{r['power_a']:>9.0f} {r['power_b']:>9.0f}")

        n = len(results)
        print(f"\n  Summary: A wins {a_wins}/{n} ({a_wins/n:.0%}) | "
              f"Avg duration {total_duration/n:.1f}s | "
              f"Avg retention A={total_ret_a/n:.1%} B={total_ret_b/n:.1%}")

    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"\n  {'Matchup':<35} {'A Win%':>7} {'Avg Dur':>8} {'A Ret':>7} {'B Ret':>7}")
    print(f"  {'-'*35} {'-'*7} {'-'*8} {'-'*7} {'-'*7}")

    for label, results in all_results.items():
        n = len(results)
        a_wins = sum(1 for r in results if r["winner"] == "A")
        avg_dur = sum(r["duration_sec"] for r in results) / n
        avg_ret_a = sum(r["retention_a"] for r in results) / n
        avg_ret_b = sum(r["retention_b"] for r in results) / n
        print(f"  {label:<35} {a_wins/n:>6.0%} {avg_dur:>7.1f}s {avg_ret_a:>6.1%} {avg_ret_b:>6.1%}")

    print("\n  Expected: favored side wins consistently with >60% retention")
    print("  Expected: mirror matches ~50/50")
    print("\nCheckpoint 6C complete.")


if __name__ == "__main__":
    run()
