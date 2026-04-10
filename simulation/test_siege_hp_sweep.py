import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_RANGE, FIELD_LAYER
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from movement import apply_group_move
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION

SIEGE_HP_LEVELS = [
    ("S1", 900, 1800),
    ("S2", 750, 1500),
    ("S3", 700, 1400),
    ("S4", 600, 1200),
]

# ── 6C helpers ──────────────────────────────────────────────────────────────

CATEGORY_UNITS = {
    "Strike": ["Raider", "Interceptor"],
    "Line":   ["Vanguard", "Warden"],
    "Siege":  ["Bombard", "Bastion"],
}

RPS_MATCHUPS = [
    ("Strike", "Siege",  "Strike > Siege"),
    ("Siege",  "Line",   "Siege > Line"),
    ("Line",   "Strike", "Line > Strike"),
]

def _build_6c_force(store, category, faction_id, start_x, start_y, rng, count=10):
    types = CATEGORY_UNITS[category]
    half = count // 2
    roster = [types[0]] * half + [types[1]] * (count - half)
    rng.shuffle(roster)
    uids = []
    for i, ut in enumerate(roster):
        x = start_x + (i % 5) * 60.0
        y = start_y + (i // 5) * 60.0
        uid = store.spawn(ut, faction_id, x, y)
        uids.append(uid)
    return uids


def run_6c():
    results = {}
    for cat_a, cat_b, label in RPS_MATCHUPS:
        wins_a = 0
        total_dur = 0.0
        for seed in [1, 2, 3, 4, 5]:
            rng = random.Random(seed)
            tmap = open_field()
            store = UnitStore()
            uids_a = _build_6c_force(store, cat_a, FACTION_A, 1700.0, 1850.0, rng)
            uids_b = _build_6c_force(store, cat_b, FACTION_B, 2100.0, 1850.0, rng)
            apply_group_move(store, uids_a, 2000.0, 2000.0)
            apply_group_move(store, uids_b, 2000.0, 2000.0)
            engine = TacticalEngine(tmap, store, seed=seed)
            engine.run(10000)
            winner = engine.get_winner()
            if winner == FACTION_A:
                wins_a += 1
            total_dur += engine.tick * DT
        results[label] = {"wins": wins_a, "avg_dur": total_dur / 5}
    return results


# ── 6D helpers ──────────────────────────────────────────────────────────────

UNIT_TYPES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]

def _spawn_line_6d(store, unit_type, faction, count, start_x, start_y, rng=None):
    uids = []
    for i in range(count):
        jx = rng.uniform(-15.0, 15.0) if rng else 0.0
        jy = rng.uniform(-15.0, 15.0) if rng else 0.0
        x = start_x + (i % 10) * 50.0 + jx
        y = start_y + (i // 10) * 50.0 + jy
        uid = store.spawn(unit_type, faction, x, y)
        uids.append(uid)
    return uids


def _spawn_mixed_6d(store, faction, count, center_x, center_y, facing_x, rng=None):
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


def run_6d():
    results = {}

    # L5: 5v5 all permutations
    l5_failures = []
    for ta in UNIT_TYPES:
        for tb in UNIT_TYPES:
            rng = random.Random(1)
            tmap = open_field()
            store = UnitStore()
            uids_a = _spawn_line_6d(store, ta, FACTION_A, 5, 1600.0, 1800.0, rng)
            uids_b = _spawn_line_6d(store, tb, FACTION_B, 5, 2200.0, 1800.0, rng)
            apply_group_move(store, uids_a, 2000.0, 2000.0)
            apply_group_move(store, uids_b, 2000.0, 2000.0)
            engine = TacticalEngine(tmap, store, seed=1)
            engine.run(30000)
            dur = engine.tick * DT
            if dur < 10.0:
                l5_failures.append((ta, tb, dur))
    results["l5_failures"] = l5_failures

    # L7: 50v50 mirror
    l7_durs = []
    for seed in [1, 2, 3]:
        rng = random.Random(seed)
        tmap = open_field()
        store = UnitStore()
        uids_a = _spawn_mixed_6d(store, FACTION_A, 50, 1600.0, 2000.0, 2200.0, rng)
        uids_b = _spawn_mixed_6d(store, FACTION_B, 50, 2200.0, 2000.0, 1600.0, rng)
        apply_group_move(store, uids_a, 2000.0, 2000.0)
        apply_group_move(store, uids_b, 2000.0, 2000.0)
        engine = TacticalEngine(tmap, store, seed=seed)
        engine.run(30000)
        l7_durs.append(engine.tick * DT)
    results["l7_avg"] = sum(l7_durs) / len(l7_durs)
    results["l7_durs"] = l7_durs

    # L6: 100v100 mixed
    l6_durs = []
    for seed in [1, 2, 3]:
        rng = random.Random(seed)
        tmap = open_field()
        store = UnitStore()
        uids_a = _spawn_mixed_6d(store, FACTION_A, 100, 1600.0, 2000.0, 2200.0, rng)
        uids_b = _spawn_mixed_6d(store, FACTION_B, 100, 2200.0, 2000.0, 1600.0, rng)
        apply_group_move(store, uids_a, 2000.0, 2000.0)
        apply_group_move(store, uids_b, 2000.0, 2000.0)
        engine = TacticalEngine(tmap, store, seed=seed)
        engine.run(30000)
        l6_durs.append(engine.tick * DT)
    results["l6_avg"] = sum(l6_durs) / len(l6_durs)

    return results


# ── Gradient helpers ────────────────────────────────────────────────────────

NUM_GRAD_SEEDS = 25
MAX_TICKS_GRAD = 6000
FACTION_STRIKE = 0
FACTION_LINE = 1

def _spawn_strike(store, faction, cx, cy, count, rng):
    uids = []
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line_formed(store, faction, cx, cy, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
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
        ax, ay = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tx, ty = store.data[tgt, FIELD_X], store.data[tgt, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        if dist <= store.data[uid, FIELD_ATTACK_RANGE]:
            firing += 1
    return firing / len(alive)


def _run_engagement_grad(store, tmap, queue, strike_uids, line_uids, seed):
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    fire_s_samples = []
    fire_l_samples = []
    last_sample = -999
    first_kill_tick = None

    for _ in range(MAX_TICKS_GRAD):
        engine.step()

        if first_kill_tick is None:
            for uid in strike_uids + line_uids:
                if not store.alive[uid]:
                    first_kill_tick = engine.tick
                    break

        if engine.tick >= last_sample + 50:
            active = store.active_ids()
            any_engaged = any(store.auto_engage_target[u] >= 0
                              for u in active if store.alive[u])
            if any_engaged:
                fire_s_samples.append(_measure_firing(store, strike_uids))
                fire_l_samples.append(_measure_firing(store, line_uids))
                last_sample = engine.tick

        if engine.is_terminal():
            break

    surv_s = len(engine.get_survivors(FACTION_STRIKE))
    surv_l = len(engine.get_survivors(FACTION_LINE))
    strike_wins = surv_s > surv_l

    total_dmg_to_line = sum(
        store.data[u, FIELD_MAX_HP] - store.data[u, FIELD_HP]
        for u in line_uids if not store.alive[u]
    ) + sum(
        store.data[u, FIELD_MAX_HP] - store.data[u, FIELD_HP]
        for u in line_uids if store.alive[u]
    )
    total_dmg_to_strike = sum(
        store.data[u, FIELD_MAX_HP] - store.data[u, FIELD_HP]
        for u in strike_uids if not store.alive[u]
    ) + sum(
        store.data[u, FIELD_MAX_HP] - store.data[u, FIELD_HP]
        for u in strike_uids if store.alive[u]
    )
    dmg_ratio = total_dmg_to_line / total_dmg_to_strike if total_dmg_to_strike > 0 else 0.0

    avg_fire_s = sum(fire_s_samples) / len(fire_s_samples) if fire_s_samples else 0.0
    avg_fire_l = sum(fire_l_samples) / len(fire_l_samples) if fire_l_samples else 0.0

    return {
        "strike_wins": strike_wins,
        "ttw": engine.tick,
        "dmg_ratio": dmg_ratio,
        "fire_delta": avg_fire_s - avg_fire_l,
        "first_kill_ticks": first_kill_tick or MAX_TICKS_GRAD,
    }


def _setup_t1(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    queue = CommandQueue()
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2500.0, 10, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 2000.0, 1500.0, 10, rng)
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2500.0}))
    return _run_engagement_grad(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t2(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    queue = CommandQueue()
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2000.0, 10, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))
    return _run_engagement_grad(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t3a(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    queue = CommandQueue()
    line_uids = []
    for i in range(10):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = 2000.0 + rng.uniform(-15, 15)
        y = 1325.0 + i * 150.0 + rng.uniform(-15, 15)
        line_uids.append(store.spawn(ut, FACTION_LINE, x, y))
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))
    return _run_engagement_grad(store, tmap, queue, strike_uids, line_uids, seed)


def _setup_t3b(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    queue = CommandQueue()
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 2000.0, 10, rng)
    for i in range(3):
        x = 2000.0 + (i % 3) * 60.0 + rng.uniform(-10, 10)
        y = 1500.0 + rng.uniform(-10, 10)
        store.spawn("Bombard", FACTION_STRIKE, x, y)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)
    queue.add(Command(tick=60, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))
    return _run_engagement_grad(store, tmap, queue, strike_uids, line_uids, seed)


def run_gradient():
    seeds = list(range(1, NUM_GRAD_SEEDS + 1))
    tiers = [
        ("T1", "Head-on formed", _setup_t1),
        ("T2", "Flank vs formed", _setup_t2),
        ("T3a", "Flank vs column", _setup_t3a),
        ("T3b", "Flank vs engaged", _setup_t3b),
    ]

    tier_stats = {}
    for tier_id, tier_name, setup_fn in tiers:
        results = []
        for seed in seeds:
            results.append(setup_fn(seed))

        wins = sum(1 for r in results if r["strike_wins"])
        ttws = [r["ttw"] for r in results]
        ttw_mean = sum(ttws) / len(ttws)
        dmg_mean = sum(r["dmg_ratio"] for r in results) / len(results)
        fire_mean = sum(r["fire_delta"] for r in results) / len(results)

        tier_stats[tier_id] = {
            "wins": wins,
            "win_rate": wins / NUM_GRAD_SEEDS,
            "ttw_mean": ttw_mean,
            "dmg_ratio": dmg_mean,
            "fire_delta": fire_mean,
        }

    t1 = tier_stats["T1"]
    for tid in tier_stats:
        tier_stats[tid]["ttw_ratio"] = (tier_stats[tid]["ttw_mean"] / t1["ttw_mean"]
                                        if t1["ttw_mean"] > 0 else 0.0)

    t2 = tier_stats["T2"]
    t3a = tier_stats["T3a"]
    t3b = tier_stats["T3b"]
    t3_ttw_ratio = max(t3a["ttw_ratio"], t3b["ttw_ratio"])
    t3_win_rate = max(t3a["win_rate"], t3b["win_rate"])
    t3_dmg_ratio = max(t3a["dmg_ratio"], t3b["dmg_ratio"])

    checks = [
        t2["ttw_ratio"] >= 1.3,
        t3_ttw_ratio >= 1.6,
        t1["win_rate"] <= 0.05,
        t3_win_rate >= t2["win_rate"] >= t1["win_rate"],
        t2["fire_delta"] > t1["fire_delta"],
        t3_dmg_ratio >= t2["dmg_ratio"] >= t1["dmg_ratio"],
    ]

    return tier_stats, sum(checks), len(checks), checks


# ── Main sweep ──────────────────────────────────────────────────────────────

def run():
    orig_bombard_hp = config.UNIT_STATS["Bombard"]["hp"]
    orig_bastion_hp = config.UNIT_STATS["Bastion"]["hp"]

    all_data = {}

    for level, bomb_hp, bast_hp in SIEGE_HP_LEVELS:
        config.UNIT_STATS["Bombard"]["hp"] = bomb_hp
        config.UNIT_STATS["Bastion"]["hp"] = bast_hp

        print(f"\n{'='*100}")
        print(f"  {level}: Bombard HP={bomb_hp}, Bastion HP={bast_hp}")
        print(f"{'='*100}")

        print(f"  Running 6C (RPS triangle)...")
        rps = run_6c()
        for label, r in rps.items():
            print(f"    {label}: {r['wins']}/5 wins, avg {r['avg_dur']:.1f}s")

        print(f"  Running 6D (durations)...")
        dur = run_6d()
        print(f"    L5 failures: {len(dur['l5_failures'])}")
        for ta, tb, d in dur['l5_failures']:
            print(f"      {ta} vs {tb}: {d:.1f}s")
        print(f"    L7 50v50 avg: {dur['l7_avg']:.1f}s (target 90-150s)")
        print(f"    L6 100v100 avg: {dur['l6_avg']:.1f}s (target >60s)")

        print(f"  Running gradient...")
        grad_stats, grad_pass, grad_total, grad_checks = run_gradient()
        for tid in ["T1", "T2", "T3a", "T3b"]:
            s = grad_stats[tid]
            print(f"    {tid}: {s['wins']}/{NUM_GRAD_SEEDS} wins, TTW {s['ttw_mean']:.0f}, "
                  f"ratio {s['ttw_ratio']:.2f}x, dmg {s['dmg_ratio']:.2f}, fire {s['fire_delta']:+.1%}")
        print(f"    Gradient: {grad_pass}/{grad_total} checks pass")

        all_data[level] = {"rps": rps, "dur": dur, "grad": grad_stats,
                           "grad_pass": grad_pass, "grad_total": grad_total,
                           "grad_checks": grad_checks}

    config.UNIT_STATS["Bombard"]["hp"] = orig_bombard_hp
    config.UNIT_STATS["Bastion"]["hp"] = orig_bastion_hp

    # ── Comparison table ────────────────────────────────────────────────────
    print(f"\n\n{'='*120}")
    print("COMPARISON TABLE")
    print(f"{'='*120}")

    hdr = (f"  {'Level':<6} {'Bomb HP':>7} {'Bast HP':>7} | "
           f"{'StS wins':>8} {'StS dur':>7} | "
           f"{'SgL wins':>8} {'SgL dur':>7} | "
           f"{'LSt wins':>8} {'LSt dur':>7} | "
           f"{'50v50':>7} | "
           f"{'Grad':>5}")
    print(hdr)
    print(f"  {'------':<6} {'-------':>7} {'-------':>7}   "
          f"{'--------':>8} {'-------':>7}   "
          f"{'--------':>8} {'-------':>7}   "
          f"{'--------':>8} {'-------':>7}   "
          f"{'-------':>7}   "
          f"{'-----':>5}")

    check_labels = ["TTW T2/T1≥1.3", "TTW T3/T1≥1.6", "WR T1≤5%",
                     "WR mono", "Fire mono", "Dmg mono"]

    best_level = None
    best_score = -1

    for level, bomb_hp, bast_hp in SIEGE_HP_LEVELS:
        d = all_data[level]
        rps = d["rps"]
        dur = d["dur"]

        sts = rps["Strike > Siege"]
        sgl = rps["Siege > Line"]
        lst = rps["Line > Strike"]

        l7 = dur["l7_avg"]
        gp = d["grad_pass"]
        gt = d["grad_total"]

        rps_ok = sts["wins"] >= 3 and sgl["wins"] >= 3 and lst["wins"] >= 3
        dur_ok = len(dur["l5_failures"]) == 0 and 90 <= l7 <= 150 and dur["l6_avg"] > 60
        score = (1 if rps_ok else 0) + (1 if dur_ok else 0) + gp / gt

        if score > best_score:
            best_score = score
            best_level = level

        marker = ""
        if rps_ok and dur_ok and gp == gt:
            marker = " <-- ALL PASS"

        print(f"  {level:<6} {bomb_hp:>7} {bast_hp:>7} | "
              f"{sts['wins']:>5}/5  {sts['avg_dur']:>6.1f}s | "
              f"{sgl['wins']:>5}/5  {sgl['avg_dur']:>6.1f}s | "
              f"{lst['wins']:>5}/5  {lst['avg_dur']:>6.1f}s | "
              f"{l7:>6.1f}s | "
              f"{gp}/{gt}{marker}")

    print()
    print(f"  Gradient check detail:")
    for level, _, _ in SIEGE_HP_LEVELS:
        checks = all_data[level]["grad_checks"]
        detail = "  ".join(f"{check_labels[i]}:{'P' if checks[i] else 'F'}" for i in range(len(checks)))
        print(f"    {level}: {detail}")

    print()
    if best_level:
        d = all_data[best_level]
        rps = d["rps"]
        dur = d["dur"]
        rps_ok = (rps["Strike > Siege"]["wins"] >= 3 and
                  rps["Siege > Line"]["wins"] >= 3 and
                  rps["Line > Strike"]["wins"] >= 3)
        dur_ok = (len(dur["l5_failures"]) == 0 and
                  90 <= dur["l7_avg"] <= 150 and dur["l6_avg"] > 60)

        if rps_ok and dur_ok and d["grad_pass"] == d["grad_total"]:
            print(f"  {best_level} passes all criteria.")
        else:
            issues = []
            if not rps_ok:
                issues.append("RPS triangle incomplete")
            if not dur_ok:
                issues.append(f"duration targets missed (L7={dur['l7_avg']:.1f}s)")
            if d["grad_pass"] < d["grad_total"]:
                issues.append(f"gradient {d['grad_pass']}/{d['grad_total']}")
            print(f"  Closest: {best_level} — still failing: {', '.join(issues)}")

    print(f"\n{'='*120}")
    print("Siege HP sweep complete.")


if __name__ == "__main__":
    run()
