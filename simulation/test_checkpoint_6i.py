import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP
from tactical_engine import TacticalEngine
from command import Command, CommandQueue, ReplayRecording, compute_state_hash
from objectives import Objective
from power_rating import compute_power_rating
from test_maps import large_operational

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION


def _initial_power(store, faction):
    total = 0.0
    for uid in store.active_ids_for_faction(faction):
        stats = config.UNIT_STATS.get(store.unit_type[uid])
        if stats:
            s = dict(stats)
            s["unit_type"] = store.unit_type[uid]
            total += compute_power_rating(s)
    return total


def _spawn_force(store, faction, center_x, center_y, composition, rng):
    uids = []
    i = 0
    for unit_type, count in composition.items():
        for j in range(count):
            jx = rng.uniform(-20, 20)
            jy = rng.uniform(-20, 20)
            x = center_x + (i % 5) * 50.0 + jx
            y = center_y + (i // 5) * 50.0 + jy
            uid = store.spawn(unit_type, faction, x, y)
            uids.append(uid)
            i += 1
    return uids


def _build_scenario(seed=1):
    rng = random.Random(seed)
    tmap = large_operational()
    store = UnitStore()

    comp_a = {"Vanguard": 5, "Warden": 3, "Raider": 4, "Bombard": 3}
    comp_b = {"Vanguard": 5, "Warden": 3, "Interceptor": 4, "Bastion": 3}

    uids_a = _spawn_force(store, FACTION_A, 1000.0, 1000.0, comp_a, rng)
    uids_b = _spawn_force(store, FACTION_B, 3000.0, 3000.0, comp_b, rng)

    initial_enemy_hp = sum(store.data[uid, FIELD_HP] for uid in uids_b)

    objectives = [
        Objective("eliminate", "eliminate_force", 0.7,
                  {"enemy_faction": FACTION_B, "initial_enemy_hp": initial_enemy_hp},
                  is_primary=True),
        Objective("survive", "survive_duration", 0.3,
                  {"duration_ticks": 2000}, is_primary=False),
    ]

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                      params={"target_x": 2000.0, "target_y": 2000.0}))
    queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                      params={"target_x": 2000.0, "target_y": 2000.0}))
    queue.add(Command(tick=200, type="activate_ability", unit_ids=[uids_a[0]],
                      params={}))

    return tmap, store, uids_a, uids_b, objectives, queue, seed


def _run_engine(tmap, store, objectives, queue, seed, max_ticks=3000):
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue
    engine.objectives = objectives
    engine.player_faction = FACTION_A
    engine.time_limit_ticks = max_ticks
    engine.initial_power = _initial_power(store, FACTION_A)
    engine.archetype = "assault"

    result = engine.run_mission(max_ticks)
    return engine, result


def test_full_mission():
    print("=" * 70)
    print("  FULL MISSION — large_operational, scripted commands")
    print("=" * 70)

    tmap, store, uids_a, uids_b, objectives, queue, seed = _build_scenario()

    recording = ReplayRecording()
    recording.capture_initial_state(store, seed, "large_operational")
    for cmd in queue.all_commands():
        recording.record_command(cmd)

    engine, result = _run_engine(tmap, store, objectives, queue, seed)

    print(f"  Map: large_operational (4000x4000)")
    print(f"  Force A: {len(uids_a)} units | Force B: {len(uids_b)} units")
    print(f"  Duration: {engine.tick} ticks ({engine.tick * DT:.1f}s)")
    print(f"  Deaths: {len(engine.death_log)}")

    print(f"\n  Outcome:")
    print(f"    Band:            {result.outcome_band}")
    print(f"    Objective score: {result.objective_score:.3f}")
    print(f"    Retention:       {result.force_retention:.3f}")
    print(f"    Ticks elapsed:   {result.ticks_elapsed}")

    if engine.death_log:
        first = engine.death_log[0]
        print(f"\n  First kill: tick {first['tick']} uid {first['uid']} "
              f"({store.unit_type[first['uid']]}) by uid {first['killer']}")

    final_hash = compute_state_hash(engine.store)
    print(f"\n  Final state hash: {final_hash}")

    ok = (engine.tick > 0 and result.outcome_band in [
        "total_success", "strong_success", "partial_success",
        "partial_failure", "total_failure"])
    print(f"\n  Full mission: {'PASS' if ok else 'FAIL'}")
    return ok, recording, final_hash


def test_replay(recording, expected_hash):
    print(f"\n{'=' * 70}")
    print("  REPLAY — Verify identical final state")
    print("=" * 70)

    store = recording.restore_initial_state()
    queue = recording.build_command_queue()
    tmap = large_operational()

    initial_enemy_hp = 0.0
    for uid in store.active_ids_for_faction(FACTION_B):
        initial_enemy_hp += store.data[uid, FIELD_HP]

    objectives = [
        Objective("eliminate", "eliminate_force", 0.7,
                  {"enemy_faction": FACTION_B, "initial_enemy_hp": initial_enemy_hp},
                  is_primary=True),
        Objective("survive", "survive_duration", 0.3,
                  {"duration_ticks": 2000}, is_primary=False),
    ]

    engine, result = _run_engine(tmap, store, objectives, queue, recording.seed)

    replay_hash = compute_state_hash(engine.store)
    match = replay_hash == expected_hash

    print(f"  Live hash:   {expected_hash}")
    print(f"  Replay hash: {replay_hash}")
    print(f"  Match: {match}")

    print(f"\n  Replay: {'PASS' if match else 'FAIL'}")
    return match


def test_determinism():
    print(f"\n{'=' * 70}")
    print("  DETERMINISM — 5 identical runs (L15)")
    print("=" * 70)

    hashes = []
    for run_id in range(5):
        tmap, store, uids_a, uids_b, objectives, queue, seed = _build_scenario(seed=42)

        engine, result = _run_engine(tmap, store, objectives, queue, seed)
        h = compute_state_hash(engine.store)
        hashes.append(h)
        print(f"  Run {run_id + 1}: {h} | ticks={engine.tick} band={result.outcome_band}")

    all_match = len(set(hashes)) == 1
    print(f"\n  All hashes identical: {all_match}")
    print(f"  L15: {'PASS' if all_match else 'FAIL'}")
    return all_match


def test_state_hash_sampling():
    print(f"\n{'=' * 70}")
    print("  STATE HASH SAMPLING — 5 tick samples, live vs replay")
    print("=" * 70)

    seed = 7
    tmap = large_operational()
    sample_ticks = [50, 150, 300, 500, 800]

    # Live run
    rng = random.Random(seed)
    store1 = UnitStore()
    comp = {"Vanguard": 5, "Raider": 5}
    uids_a = _spawn_force(store1, FACTION_A, 1000.0, 1500.0, comp, rng)
    uids_b = _spawn_force(store1, FACTION_B, 3000.0, 2500.0, comp, random.Random(seed))

    recording = ReplayRecording()
    recording.capture_initial_state(store1, seed, "large_operational")

    queue1 = CommandQueue()
    queue1.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                       params={"target_x": 2000.0, "target_y": 2000.0}))
    queue1.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                       params={"target_x": 2000.0, "target_y": 2000.0}))
    for cmd in queue1.all_commands():
        recording.record_command(cmd)

    engine1 = TacticalEngine(tmap, store1, seed=seed)
    engine1.command_queue = queue1
    live_hashes = {}
    for tick in range(max(sample_ticks) + 1):
        engine1.step()
        if engine1.tick in sample_ticks:
            live_hashes[engine1.tick] = compute_state_hash(engine1.store)

    # Replay
    store2 = recording.restore_initial_state()
    queue2 = recording.build_command_queue()
    tmap2 = large_operational()
    engine2 = TacticalEngine(tmap2, store2, seed=seed)
    engine2.command_queue = queue2
    replay_hashes = {}
    for tick in range(max(sample_ticks) + 1):
        engine2.step()
        if engine2.tick in sample_ticks:
            replay_hashes[engine2.tick] = compute_state_hash(engine2.store)

    print(f"  {'Tick':>6} {'Live Hash':>34} {'Replay Hash':>34} {'Match':>6}")
    print(f"  {'-'*6} {'-'*34} {'-'*34} {'-'*6}")

    all_match = True
    for t in sample_ticks:
        lh = live_hashes.get(t, "N/A")
        rh = replay_hashes.get(t, "N/A")
        match = lh == rh
        if not match:
            all_match = False
        print(f"  {t:>6} {lh:>34} {rh:>34} {'OK' if match else 'FAIL':>6}")

    print(f"\n  Hash sampling: {'PASS' if all_match else 'FAIL'}")
    return all_match


def run():
    print("=" * 70)
    print("CHECKPOINT 6I — Command Protocol and Replay (Integration)")
    print("=" * 70)

    results = {}

    ok, recording, final_hash = test_full_mission()
    results["Full mission"] = ok

    results["Replay"] = test_replay(recording, final_hash)
    results["Determinism (L15)"] = test_determinism()
    results["Hash sampling"] = test_state_hash_sampling()

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name:<24} {'PASS' if passed else 'FAIL'}")

    total_pass = sum(1 for v in results.values() if v)
    print(f"\n  {total_pass}/{len(results)} tests passed")
    print("\nCheckpoint 6I complete.")


if __name__ == "__main__":
    run()
