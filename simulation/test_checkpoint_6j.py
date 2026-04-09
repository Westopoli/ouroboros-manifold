import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_ATTACK_RANGE, FIELD_LAYER
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from movement import apply_group_move
from power_rating import compute_power_rating
from test_maps import chokepoint

FACTION_A = 0  # Strike (disadvantaged)
FACTION_B = 1  # Line (advantaged)
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


def _bounding_box(store, uids):
    alive = [u for u in uids if store.alive[u]]
    if not alive:
        return None
    xs = [store.data[u, FIELD_X] for u in alive]
    ys = [store.data[u, FIELD_Y] for u in alive]
    return min(xs), max(xs), min(ys), max(ys)


def _force_snapshot(store, uids, label, tick, active, verbose=False):
    alive = [u for u in uids if store.alive[u]]
    valid_target = 0
    no_target = 0
    pathing = 0

    lines = []
    for uid in alive:
        tgt = store.auto_engage_target[uid]
        has_tgt = tgt >= 0 and store.alive[tgt]

        if not has_tgt:
            if store.has_move_target[uid]:
                pathing += 1
            else:
                no_target += 1
            dist = -1.0
        else:
            ax = store.data[uid, FIELD_X]
            ay = store.data[uid, FIELD_Y]
            tx = store.data[tgt, FIELD_X]
            ty = store.data[tgt, FIELD_Y]
            dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
            valid_target += 1

        if verbose:
            px = store.data[uid, FIELD_X]
            py = store.data[uid, FIELD_Y]
            lines.append(
                f"      uid={uid:>3} {store.unit_type[uid]:>12} "
                f"pos=({px:7.1f},{py:7.1f}) "
                f"tgt={tgt:>3} dist={dist:7.1f}"
            )

    print(f"    {label} @ tick {tick}: "
          f"alive={len(alive)} firing={valid_target} "
          f"no_tgt={no_target} pathing={pathing}")
    for line in lines:
        print(line)

    return len(alive), valid_target, 0, no_target, pathing


def _run_engagement(seed, flank, verbose=False):
    rng = random.Random(seed)
    tmap = chokepoint()
    store = UnitStore()

    line_uids = _spawn_line(store, FACTION_B, 2000.0, 2500.0, 10, rng)
    strike_uids = _spawn_strike(store, FACTION_A, 2000.0, 1200.0, 10, rng)

    queue = CommandQueue()
    if flank:
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 1800.0}))
        queue.add(Command(tick=150, type="fast_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 3200.0}))
        queue.add(Command(tick=300, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))
    else:
        queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                          params={"target_x": 2000.0, "target_y": 2500.0}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    first_damage_tick = None
    snapshot_ticks = set()
    arrival_ticks = {}  # uid → tick first in weapon range of any Line unit
    last_snapshot_tick = -999

    for t in range(MAX_TICKS):
        engine.step()

        if verbose and flank:
            for uid in strike_uids:
                if uid in arrival_ticks or not store.alive[uid]:
                    continue
                ax = store.data[uid, FIELD_X]
                ay = store.data[uid, FIELD_Y]
                atk_range = store.data[uid, FIELD_ATTACK_RANGE]
                for lid in line_uids:
                    if not store.alive[lid]:
                        continue
                    dx = store.data[lid, FIELD_X] - ax
                    dy = store.data[lid, FIELD_Y] - ay
                    if math.sqrt(dx * dx + dy * dy) <= atk_range:
                        arrival_ticks[uid] = engine.tick
                        break

        if first_damage_tick is None and engine.death_log:
            first_damage_tick = engine.tick

        if first_damage_tick is None:
            for uid in strike_uids + line_uids:
                if store.alive[uid] and store.data[uid, FIELD_HP] < config.UNIT_STATS[store.unit_type[uid]]["hp"]:
                    first_damage_tick = engine.tick
                    break

        if first_damage_tick is not None and first_damage_tick not in snapshot_ticks:
            snapshot_ticks.add(first_damage_tick)

        do_snapshot = (first_damage_tick is not None
                       and engine.tick >= last_snapshot_tick + 200
                       and engine.tick > first_damage_tick)

        if verbose and (engine.tick in snapshot_ticks or do_snapshot):
            active = store.active_ids()
            is_first = engine.tick == first_damage_tick
            if is_first:
                print(f"\n    --- FIRST DAMAGE @ tick {engine.tick} ---")
            else:
                print(f"\n    --- snapshot @ tick {engine.tick} ---")

            _force_snapshot(store, strike_uids, "Strike", engine.tick, active,
                            verbose=(flank))
            _force_snapshot(store, line_uids, "Line", engine.tick, active,
                            verbose=(flank and is_first))

            if is_first:
                bb_s = _bounding_box(store, strike_uids)
                bb_l = _bounding_box(store, line_uids)
                if bb_s:
                    print(f"    Strike bbox: x=[{bb_s[0]:.0f}..{bb_s[1]:.0f}] "
                          f"y=[{bb_s[2]:.0f}..{bb_s[3]:.0f}] "
                          f"spread=({bb_s[1]-bb_s[0]:.0f} x {bb_s[3]-bb_s[2]:.0f})")
                if bb_l:
                    print(f"    Line bbox:   x=[{bb_l[0]:.0f}..{bb_l[1]:.0f}] "
                          f"y=[{bb_l[2]:.0f}..{bb_l[3]:.0f}] "
                          f"spread=({bb_l[1]-bb_l[0]:.0f} x {bb_l[3]-bb_l[2]:.0f})")

            snapshot_ticks.add(engine.tick)
            last_snapshot_tick = engine.tick

        if engine.is_terminal():
            break

    if verbose and flank and arrival_ticks:
        print(f"\n    --- ARRIVAL SPREAD (flank) ---")
        sorted_arr = sorted(arrival_ticks.items(), key=lambda x: x[1])
        for uid, atick in sorted_arr:
            print(f"      uid={uid:>3} {store.unit_type[uid]:>12} entered range @ tick {atick}")
        first_arr = sorted_arr[0][1]
        last_arr = sorted_arr[-1][1]
        print(f"    First arrival: tick {first_arr}  Last: tick {last_arr}  "
              f"Gap: {last_arr - first_arr} ticks ({(last_arr - first_arr) * DT:.1f}s)")

    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    winner = "Strike" if surv_a > surv_b else ("Line" if surv_b > surv_a else "Draw")
    ret_a = surv_a / len(strike_uids) if strike_uids else 0.0
    ret_b = surv_b / len(line_uids) if line_uids else 0.0

    return {
        "winner": winner,
        "ticks": engine.tick,
        "duration_sec": engine.tick * DT,
        "surv_strike": surv_a,
        "surv_line": surv_b,
        "retention_strike": ret_a,
        "retention_line": ret_b,
    }


def run():
    print("=" * 70)
    print("CHECKPOINT 6J — Soft RPS with Positioning")
    print("=" * 70)

    seeds = list(range(1, 26))

    # Direct approach — summary only
    print(f"\n  DIRECT APPROACH — Strike vs Line, {len(seeds)} seeds")
    print(f"  {'Seed':>6} {'Winner':>8} {'Duration':>10} {'Strike surv':>12} {'Line surv':>10}")
    print(f"  {'-'*6} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

    direct_results = []
    for seed in seeds:
        r = _run_engagement(seed, flank=False, verbose=False)
        direct_results.append(r)
        print(f"  {seed:>6} {r['winner']:>8} {r['duration_sec']:>9.1f}s "
              f"{r['surv_strike']:>12} {r['surv_line']:>10}")

    direct_strike_wins = sum(1 for r in direct_results if r["winner"] == "Strike")
    direct_win_rate = direct_strike_wins / len(direct_results)
    direct_avg_dur = sum(r["duration_sec"] for r in direct_results) / len(direct_results)
    direct_avg_ret = sum(r["retention_strike"] for r in direct_results) / len(direct_results)

    # Flank approach — verbose diagnostics for seed 1
    print(f"\n  FLANK APPROACH — Strike vs Line, {len(seeds)} seeds")
    print(f"\n  === DETAILED DIAGNOSTICS: seed 1 ===")
    r_diag = _run_engagement(1, flank=True, verbose=True)
    print(f"\n  === END DIAGNOSTICS ===\n")

    print(f"  {'Seed':>6} {'Winner':>8} {'Duration':>10} {'Strike surv':>12} {'Line surv':>10}")
    print(f"  {'-'*6} {'-'*8} {'-'*10} {'-'*12} {'-'*10}")

    flank_results = []
    for seed in seeds:
        r = _run_engagement(seed, flank=True, verbose=False)
        flank_results.append(r)
        print(f"  {seed:>6} {r['winner']:>8} {r['duration_sec']:>9.1f}s "
              f"{r['surv_strike']:>12} {r['surv_line']:>10}")

    flank_strike_wins = sum(1 for r in flank_results if r["winner"] == "Strike")
    flank_win_rate = flank_strike_wins / len(flank_results)
    flank_avg_dur = sum(r["duration_sec"] for r in flank_results) / len(flank_results)
    flank_avg_ret = sum(r["retention_strike"] for r in flank_results) / len(flank_results)

    # Comparison
    print(f"\n{'=' * 70}")
    print("  COMPARISON")
    print("=" * 70)
    print(f"  {'':>16} {'Direct':>10} {'Flank':>10}")
    print(f"  {'-'*16} {'-'*10} {'-'*10}")
    print(f"  {'Strike wins':>16} {direct_strike_wins:>10} {flank_strike_wins:>10}")
    print(f"  {'Win rate':>16} {direct_win_rate:>9.0%} {flank_win_rate:>9.0%}")
    print(f"  {'Avg duration':>16} {direct_avg_dur:>9.1f}s {flank_avg_dur:>9.1f}s")
    print(f"  {'Avg retention':>16} {direct_avg_ret:>9.1%} {flank_avg_ret:>9.1%}")

    positioning_helps = flank_win_rate > direct_win_rate
    l4_pass = flank_win_rate >= 0.30

    print(f"\n  Positioning improves Strike win rate: {positioning_helps}")
    print(f"  L4: {'PASS' if l4_pass else 'FAIL'} (flank win rate ≥ 30%)")

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Soft RPS + Positioning (L4)  {'PASS' if l4_pass else 'FAIL'}")

    print("\nCheckpoint 6J complete.")


if __name__ == "__main__":
    run()
