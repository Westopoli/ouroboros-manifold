import time
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_LAYER
from tactical_engine import TacticalEngine
from movement import apply_group_move, _compute_preferred_velocities, _compute_orca_line, _solve_lp_2d_safe
from ability import update_abilities, resolve_barrage
from test_maps import open_field_large

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION
WARMUP_TICKS = 1000


def spawn_mixed(store, faction, count, center_x, center_y, facing_x, rng):
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
    rows = {"Vanguard": 0, "Warden": 1, "Raider": 2, "Interceptor": 2, "Bombard": 3, "Bastion": 4}
    uids = []
    for ut, n in role_counts.items():
        row_x = center_x + sign * rows[ut] * 60.0
        start_y = center_y - (n - 1) * 60.0 / 2.0
        for i in range(n):
            x = row_x + rng.uniform(-15.0, 15.0)
            y = start_y + i * 60.0 + rng.uniform(-15.0, 15.0)
            uids.append(store.spawn(ut, faction, x, y))
    return uids


def profile_rvo(store, active, tmap):
    agent_radius = config.UNIT_COLLISION_RADIUS
    neighbor_dist = config.RVO_NEIGHBOR_DIST
    time_horizon = config.RVO_TIME_HORIZON
    max_neighbors = config.RVO_MAX_NEIGHBORS
    combined_radius = agent_radius * 2.0
    neighbor_dist_sq = neighbor_dist * neighbor_dist

    t_pref = time.perf_counter()
    preferred = _compute_preferred_velocities(store, active, DT)
    t_pref_end = time.perf_counter()

    current_vel = {}
    for uid in active:
        pv = preferred[uid]
        current_vel[uid] = (pv[0], pv[1])

    # Phase A: spatial hash rebuild
    t_a0 = time.perf_counter()
    tmap.spatial_hash.clear()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])
    t_a1 = time.perf_counter()

    t_query_total = 0.0
    t_orca_total = 0.0
    t_lp_total = 0.0
    neighbor_counts_post_cap = []   # after sort-and-trim to max_neighbors
    candidate_counts_raw = []       # returned by spatial hash query (before any filter)
    candidate_counts_filtered = []  # after uid/layer/distance filter, before cap

    for uid in active:
        pref_vx, pref_vy, max_speed = preferred[uid]
        px = store.data[uid, FIELD_X]
        py = store.data[uid, FIELD_Y]
        my_layer = store.data[uid, FIELD_LAYER]

        # Phase B: neighbor query
        tq0 = time.perf_counter()
        raw = tmap.spatial_hash.query(px, py, neighbor_dist)
        candidate_counts_raw.append(len(raw))
        neighbors = []
        for other in sorted(raw):
            if other == uid:
                continue
            if store.data[other, FIELD_LAYER] != my_layer:
                continue
            ox = store.data[other, FIELD_X]
            oy = store.data[other, FIELD_Y]
            dx = ox - px
            dy = oy - py
            d_sq = dx * dx + dy * dy
            if d_sq < neighbor_dist_sq:
                neighbors.append((other, d_sq))
        candidate_counts_filtered.append(len(neighbors))
        neighbors.sort(key=lambda x: x[1])
        if len(neighbors) > max_neighbors:
            neighbors = neighbors[:max_neighbors]
        tq1 = time.perf_counter()
        t_query_total += tq1 - tq0
        neighbor_counts_post_cap.append(len(neighbors))

        if not neighbors:
            continue

        # Phase C: ORCA line construction
        tc0 = time.perf_counter()
        orca_lines = []
        va_x, va_y = current_vel[uid]
        for other, _ in neighbors:
            ob_x = store.data[other, FIELD_X]
            ob_y = store.data[other, FIELD_Y]
            vb_x, vb_y = current_vel[other]
            line = _compute_orca_line(px, py, ob_x, ob_y, va_x, va_y, vb_x, vb_y, combined_radius, time_horizon)
            if line is not None:
                orca_lines.append(line)
        tc1 = time.perf_counter()
        t_orca_total += tc1 - tc0

        if not orca_lines:
            continue

        # Phase D: LP solve
        tl0 = time.perf_counter()
        _solve_lp_2d_safe(orca_lines, pref_vx, pref_vy, max_speed)
        tl1 = time.perf_counter()
        t_lp_total += tl1 - tl0

    total = (time.perf_counter() - t_pref) * 1000
    print(f"\n  === compute_rvo_velocities (single tick, {len(active)} units) ===")
    print(f"  preferred_velocities:  {(t_pref_end - t_pref)*1000:7.2f} ms")
    print(f"  (a) hash rebuild:      {(t_a1 - t_a0)*1000:7.2f} ms")
    print(f"  (b) neighbor query:    {t_query_total*1000:7.2f} ms")
    print(f"  (c) ORCA line build:   {t_orca_total*1000:7.2f} ms")
    print(f"  (d) LP solve:          {t_lp_total*1000:7.2f} ms")
    print(f"  total measured:        {total:7.2f} ms")
    n_units = len(active)
    avg_raw  = sum(candidate_counts_raw)      / n_units
    max_raw  = max(candidate_counts_raw)
    avg_filt = sum(candidate_counts_filtered) / n_units
    max_filt = max(candidate_counts_filtered)
    avg_post = sum(neighbor_counts_post_cap)  / n_units
    max_post = max(neighbor_counts_post_cap)
    hitting_cap = sum(1 for c in neighbor_counts_post_cap if c >= max_neighbors)
    print(f"  candidates (spatial hash raw):    avg={avg_raw:.1f}  max={max_raw}")
    print(f"  candidates (after layer+dist):    avg={avg_filt:.1f}  max={max_filt}")
    print(f"  neighbors  (after cap={max_neighbors}):       avg={avg_post:.1f}  max={max_post}  hitting_cap={hitting_cap}/{n_units}")


def profile_abilities(store):
    from ability import ABILITY_MAP, ABILITY_INACTIVE, ABILITY_ACTIVE, ABILITY_WINDUP, ABILITY_TELEGRAPH
    from unit import FIELD_ABILITY_COOLDOWN, FIELD_ABILITY_ACTIVE as FAA, FIELD_ABILITY_DURATION

    import ability as abl_mod

    t_outer0 = time.perf_counter()
    count_intercept_checks = 0
    count_intercept_scans = 0
    for uid in store.active_ids():
        if store.data[uid, FAA] == ABILITY_INACTIVE:
            if store.unit_type[uid] == "Interceptor" and store.data[uid, FIELD_ABILITY_COOLDOWN] == 0:
                count_intercept_checks += 1
                count_intercept_scans += len(store.active_ids())
    t_outer1 = time.perf_counter()

    # Time the actual outer loop
    t_loop0 = time.perf_counter()
    for uid in store.active_ids():
        if store.data[uid, FIELD_ABILITY_COOLDOWN] > 0:
            pass
        if store.data[uid, FAA] == ABILITY_INACTIVE:
            pass
    t_loop1 = time.perf_counter()

    # Time _check_intercept scan specifically (run it)
    from ability import _check_intercept, _apply_warden_aura_healing
    t_intercept0 = time.perf_counter()
    for uid in store.active_ids():
        _check_intercept(store, uid)
    t_intercept1 = time.perf_counter()

    t_aura0 = time.perf_counter()
    _apply_warden_aura_healing(store)
    t_aura1 = time.perf_counter()

    print(f"\n  === update_abilities (single tick, {len(store.active_ids())} units) ===")
    print(f"  outer loop (no-op):    {(t_loop1 - t_loop0)*1000:7.2f} ms")
    print(f"  _check_intercept all:  {(t_intercept1 - t_intercept0)*1000:7.2f} ms  ({count_intercept_checks} interceptors w/ cooldown=0, ~{count_intercept_scans} unit scans)")
    print(f"  _apply_warden_aura:    {(t_aura1 - t_aura0)*1000:7.2f} ms")
    wardens = [uid for uid in store.active_ids() if store.unit_type[uid] == "Warden"]
    print(f"  wardens alive: {len(wardens)}")


def run():
    print("=" * 70)
    print("PROFILE — Single-tick breakdown (after warmup)")
    print("=" * 70)

    rng = random.Random(1)
    tmap = open_field_large()
    store = UnitStore()

    # 6K-close spawn: 2000wu apart on large field (units pack tight quickly)
    uids_a = spawn_mixed(store, FACTION_A, 200, 5000.0, 6000.0, 6000.0, rng)
    uids_b = spawn_mixed(store, FACTION_B, 200, 7000.0, 6000.0, 6000.0, rng)
    apply_group_move(store, uids_a, 6000.0, 6000.0)
    apply_group_move(store, uids_b, 6000.0, 6000.0)

    engine = TacticalEngine(tmap, store, seed=1)

    print(f"  Warming up {WARMUP_TICKS} ticks...", end="", flush=True)
    for _ in range(WARMUP_TICKS):
        engine.step()
    print(" done.")
    print(f"  Alive after warmup: A={len(engine.get_survivors(FACTION_A))}  B={len(engine.get_survivors(FACTION_B))}")

    # --- Spatial hash bucket stats at this moment ---
    active = store.active_ids()
    tmap.spatial_hash.clear()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    occupied = {k: v for k, v in tmap.spatial_hash._cells.items() if v}
    bucket_sizes = [len(v) for v in occupied.values()]
    total_units = sum(bucket_sizes)
    print(f"\n  Spatial hash state (cell_size={config.NAVMESH_CELL_SIZE}wu):")
    print(f"    total units inserted: {total_units}")
    print(f"    occupied cells:       {len(occupied)}")
    print(f"    avg units/cell:       {total_units/len(occupied):.2f}")
    print(f"    max units/cell:       {max(bucket_sizes)}")
    print(f"    cells with >1 unit:   {sum(1 for s in bucket_sizes if s > 1)}")

    # --- Profile RVO ---
    profile_rvo(store, active, tmap)

    # --- Replicate 6K loop structure for 5 consecutive ticks, time each subsystem ---
    from damage import resolve_damage, update_targeting
    from movement import update_movement
    from fog_of_war import update_fog_timers
    from command import process_commands
    import damage as dmg_mod

    print(f"\n  === 6K-loop-style timing (5 ticks at tick {engine.tick}) ===")
    print(f"  {'Tick':<6} {'targeting':>10} {'movement':>10} {'abilities':>10}")
    for _ in range(5):
        process_commands(engine.command_queue, engine.store, engine.tick)

        t0 = time.perf_counter()
        update_targeting(engine.store, engine.map, engine.rng)
        ms_tgt = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        update_movement(engine.store, engine.map, engine.dt)
        ms_mov = (time.perf_counter() - t0) * 1000

        deaths, kill_sources = dmg_mod.resolve_damage(engine.store, engine.map, engine.dt)

        t0 = time.perf_counter()
        barrage_events = update_abilities(engine.store, engine.dt)
        if barrage_events:
            resolve_barrage(engine.store, barrage_events)
        ms_abl = (time.perf_counter() - t0) * 1000

        update_fog_timers(engine.store)
        if deaths:
            for uid in deaths:
                engine.death_log.append({"uid": uid, "tick": engine.tick, "killer": kill_sources.get(uid, -1)})
        engine.tick += 1
        print(f"  {engine.tick:<6} {ms_tgt:>10.2f} {ms_mov:>10.2f} {ms_abl:>10.2f}")

    # --- Direct timing of full update_abilities call ---
    t_direct = time.perf_counter()
    update_abilities(engine.store, engine.dt)
    t_direct_end = time.perf_counter()
    print(f"\n  Direct update_abilities call: {(t_direct_end - t_direct)*1000:.2f} ms")

    t_mov = time.perf_counter()
    update_movement(engine.store, engine.map, engine.dt)
    t_mov_end = time.perf_counter()
    print(f"  Direct update_movement call:  {(t_mov_end - t_mov)*1000:.2f} ms")

    # --- Profile abilities ---
    profile_abilities(store)

    print()


if __name__ == "__main__":
    run()
