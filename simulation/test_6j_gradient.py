import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_RANGE, FIELD_LAYER
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from movement import apply_group_move
from test_maps import open_field

FACTION_STRIKE = 0
FACTION_LINE = 1
FACTION_SIEGE = 2
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000
NUM_SEEDS = 25


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


def _spawn_line_formed(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        jx = rng.uniform(-15, 15)
        jy = rng.uniform(-15, 15)
        x = center_x + (i % 5) * 40.0 + jx
        y = center_y + (i // 5) * 40.0 + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line_column(store, faction, lead_x, lead_y, count, spacing, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        jx = rng.uniform(-10, 10)
        jy = rng.uniform(-10, 10)
        x = lead_x + jx
        y = lead_y + i * spacing + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_bombards(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        jx = rng.uniform(-20, 20)
        jy = rng.uniform(-20, 20)
        x = center_x + (i % 3) * 60.0 + jx
        y = center_y + jy
        uids.append(store.spawn("Bombard", faction, x, y))
    return uids


def _measure_firing(store, uids):
    alive = [u for u in uids if store.alive[u]]
    if not alive:
        return 0.0
    firing = 0
    for uid in alive:
        tgt = store.auto_engage_target[uid]
        if tgt < 0 or not store.alive[tgt]:
            continue
        ax = store.data[uid, FIELD_X]
        ay = store.data[uid, FIELD_Y]
        tx = store.data[tgt, FIELD_X]
        ty = store.data[tgt, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        if dist > store.data[uid, FIELD_ATTACK_RANGE]:
            continue
        firing += 1
    return firing / len(alive)


def _total_damage_dealt_to(store, uids):
    total = 0.0
    for uid in uids:
        max_hp = store.data[uid, FIELD_MAX_HP]
        if store.alive[uid]:
            total += max_hp - store.data[uid, FIELD_HP]
        else:
            total += max_hp
    return total


def _run_tier(tier_name, setup_fn, seeds):
    results = []
    for seed in seeds:
        r = setup_fn(seed)
        results.append(r)
    return results


def _setup_t1(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    # Line holds position in tight formation. Strike advances head-on.
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2500.0, 10, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 2000.0, 1500.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2500.0}))

    return _run_engagement(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t2(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2000.0, 10, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))

    return _run_engagement(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t3a(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    # Line stationary in column (150 wu spacing, ~1350 wu total spread).
    # Strike attacks from 90° flank into column midpoint. Line's rear units
    # are too far to fire initially — Strike gets piecemeal engagement.
    line_uids = _spawn_line_column(store, FACTION_LINE, 2000.0, 1325.0, 10, 150.0, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))

    return _run_engagement(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t3b(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    # Line near Bombards (within engagement range) — fight starts immediately.
    # Bombards allied to Strike so Line fights them. Strike arrives from Line's
    # 3-o'clock after 3 sec delay. Line's HP and attention are split.
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2000.0, 10, rng)
    _spawn_bombards(store, FACTION_STRIKE, 2000.0, 1500.0, 3, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=60, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))

    return _run_engagement(store, tmap, queue, strike_uids, line_uids, seed)


def _run_engagement(store, tmap, queue, strike_uids, line_uids, seed):
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    first_damage_tick = None
    first_strike_kill_tick = None
    fire_samples_strike = []
    fire_samples_line = []
    sample_interval = 50

    for t in range(MAX_TICKS):
        engine.step()

        if first_damage_tick is None:
            for uid in strike_uids + line_uids:
                if store.alive[uid] and store.data[uid, FIELD_HP] < store.data[uid, FIELD_MAX_HP]:
                    first_damage_tick = engine.tick
                    break

        if first_strike_kill_tick is None:
            for uid in strike_uids:
                if not store.alive[uid]:
                    first_strike_kill_tick = engine.tick
                    break

        if first_damage_tick is not None and engine.tick % sample_interval == 0:
            fire_samples_strike.append(_measure_firing(store, strike_uids))
            fire_samples_line.append(_measure_firing(store, line_uids))

        if engine.is_terminal():
            break

    surv_strike = len(engine.get_survivors(FACTION_STRIKE))
    surv_line = len(engine.get_survivors(FACTION_LINE))
    strike_wins = surv_strike > 0 and surv_line == 0

    dmg_to_line = _total_damage_dealt_to(store, line_uids)
    dmg_to_strike = _total_damage_dealt_to(store, strike_uids)
    dmg_ratio = dmg_to_line / dmg_to_strike if dmg_to_strike > 0 else 0.0

    avg_fire_strike = sum(fire_samples_strike) / len(fire_samples_strike) if fire_samples_strike else 0.0
    avg_fire_line = sum(fire_samples_line) / len(fire_samples_line) if fire_samples_line else 0.0
    fire_delta = avg_fire_strike - avg_fire_line

    ttw = engine.tick - first_damage_tick if first_damage_tick is not None else engine.tick
    first_kill_offset = first_strike_kill_tick - first_damage_tick if (first_strike_kill_tick and first_damage_tick) else ttw

    return {
        "strike_wins": strike_wins,
        "ttw": ttw,
        "dmg_ratio": dmg_ratio,
        "fire_delta": fire_delta,
        "first_kill_ticks": first_kill_offset,
        "ticks": engine.tick,
    }


def run():
    seeds = list(range(1, NUM_SEEDS + 1))

    tiers = [
        ("T1", "Head-on formed", _setup_t1),
        ("T2", "Flank vs formed", _setup_t2),
        ("T3a", "Flank vs column", _setup_t3a),
        ("T3b", "Flank vs engaged", _setup_t3b),
    ]

    print("=" * 108)
    print("6J BEHAVIORAL GRADIENT — Strike vs Line, %d seeds per tier" % NUM_SEEDS)
    print("=" * 108)

    all_results = {}
    for tier_id, tier_name, setup_fn in tiers:
        results = []
        for seed in seeds:
            r = setup_fn(seed)
            results.append(r)
        all_results[tier_id] = results
        wins = sum(1 for r in results if r["strike_wins"])
        print(f"  {tier_id} {tier_name} done — Strike wins {wins}/{NUM_SEEDS}")

    print()
    print(f"{'Tier':<6}{'Scenario':<22}{'Strike Wins':>12}{'TTW(mean±std)':>16}"
          f"{'TTW Ratio':>10}{'Dmg Ratio':>10}{'Fire% Δ':>9}{'1st Kill(ticks)':>16}")
    print(f"{'----':<6}{'--------------------':<22}{'-----------':>12}{'-------------':>16}"
          f"{'---------':>10}{'---------':>10}{'-------':>9}{'---------------':>16}")

    tier_stats = {}
    for tier_id, tier_name, _ in tiers:
        results = all_results[tier_id]
        wins = sum(1 for r in results if r["strike_wins"])
        ttws = [r["ttw"] for r in results]
        ttw_mean = sum(ttws) / len(ttws)
        ttw_std = math.sqrt(sum((t - ttw_mean) ** 2 for t in ttws) / len(ttws))
        dmg_mean = sum(r["dmg_ratio"] for r in results) / len(results)
        fire_mean = sum(r["fire_delta"] for r in results) / len(results)
        fk_mean = sum(r["first_kill_ticks"] for r in results) / len(results)

        tier_stats[tier_id] = {
            "wins": wins,
            "win_rate": wins / NUM_SEEDS,
            "ttw_mean": ttw_mean,
            "ttw_std": ttw_std,
            "dmg_ratio": dmg_mean,
            "fire_delta": fire_mean,
            "first_kill": fk_mean,
        }

    t1_ttw = tier_stats["T1"]["ttw_mean"]
    for tier_id, tier_name, _ in tiers:
        s = tier_stats[tier_id]
        ttw_ratio = s["ttw_mean"] / t1_ttw if t1_ttw > 0 else 0.0
        s["ttw_ratio"] = ttw_ratio
        print(f"{tier_id:<6}{tier_name:<22}{s['wins']:>4}/{NUM_SEEDS:<7}"
              f"{s['ttw_mean']:>8.0f} ± {s['ttw_std']:<6.0f}"
              f"{ttw_ratio:>8.2f}×"
              f"{s['dmg_ratio']:>10.2f}"
              f"{s['fire_delta']:>+8.1%}"
              f"{s['first_kill']:>13.0f}")

    # Gradient checks
    print(f"\nGRADIENT CHECK:")

    t1 = tier_stats["T1"]
    t2 = tier_stats["T2"]
    t3a = tier_stats["T3a"]
    t3b = tier_stats["T3b"]
    t3_ttw_ratio = max(t3a["ttw_ratio"], t3b["ttw_ratio"])
    t3_win_rate = max(t3a["win_rate"], t3b["win_rate"])
    t3_dmg_ratio = max(t3a["dmg_ratio"], t3b["dmg_ratio"])

    checks = []

    c1 = t2["ttw_ratio"] >= 1.3
    checks.append(c1)
    print(f"  TTW ratio T2/T1 >= 1.3:  {t2['ttw_ratio']:.2f}  {'PASS' if c1 else 'FAIL'}")

    c2 = t3_ttw_ratio >= 1.6
    checks.append(c2)
    print(f"  TTW ratio T3/T1 >= 1.6:  {t3_ttw_ratio:.2f}  {'PASS' if c2 else 'FAIL'}")

    c3 = t1["win_rate"] <= 0.05
    checks.append(c3)
    print(f"  Win rate T1 <= 5%%:       {t1['win_rate']:.0%}    {'PASS' if c3 else 'FAIL'}")

    t2_wr = t2["win_rate"]
    mono_win = (t3_win_rate >= t2_wr >= t1["win_rate"])
    checks.append(mono_win)
    print(f"  Win rate T3 > T2 > T1:   {t1['win_rate']:.0%} -> {t2_wr:.0%} -> {t3_win_rate:.0%}  {'PASS' if mono_win else 'FAIL'} (monotonic)")

    c5 = t2["fire_delta"] > t1["fire_delta"]
    checks.append(c5)
    print(f"  Fire%% Δ T2 > T1:        {t1['fire_delta']:+.1%} -> {t2['fire_delta']:+.1%}  {'PASS' if c5 else 'FAIL'}")

    mono_dmg = (t3_dmg_ratio >= t2["dmg_ratio"] >= t1["dmg_ratio"])
    checks.append(mono_dmg)
    print(f"  Dmg ratio T3 > T2 > T1:  {t1['dmg_ratio']:.2f} -> {t2['dmg_ratio']:.2f} -> {t3_dmg_ratio:.2f}  {'PASS' if mono_dmg else 'FAIL'} (monotonic)")

    all_pass = all(checks)
    print(f"\n  L4 (revised): {'PASS' if all_pass else 'FAIL'} ({sum(checks)}/{len(checks)} gradient checks)")
    print()


if __name__ == "__main__":
    run()
