import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP
from power_rating import compute_power_rating
from objectives import (
    Objective, update_objectives, check_terminal,
    compute_scores, compute_retention, classify_outcome, build_mission_result,
)
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
ARCHETYPE = "defensive_stand"


def _initial_power(store, faction):
    total = 0.0
    for uid in store.active_ids_for_faction(faction):
        stats = config.UNIT_STATS.get(store.unit_type[uid])
        if stats:
            s = dict(stats)
            s["unit_type"] = store.unit_type[uid]
            total += compute_power_rating(s)
    return total


def test_all_5_bands():
    print("=" * 70)
    print("  OUTCOME BANDS — 5 scripted scenarios (L13)")
    print("=" * 70)

    scenarios = [
        _scenario_total_success,
        _scenario_strong_success,
        _scenario_partial_success,
        _scenario_partial_failure,
        _scenario_total_failure,
    ]

    bands_produced = set()
    print(f"  {'Scenario':<22} {'Obj Score':>10} {'Retention':>10} {'Final':>8} {'Band':<18}")
    print(f"  {'-'*22} {'-'*10} {'-'*10} {'-'*8} {'-'*18}")

    for fn in scenarios:
        name, obj_score, retention, final_score, band = fn()
        bands_produced.add(band)
        print(f"  {name:<22} {obj_score:>10.3f} {retention:>10.3f} {final_score:>8.3f} {band:<18}")

    expected = {"total_success", "strong_success", "partial_success", "partial_failure", "total_failure"}
    ok = expected == bands_produced
    missing = expected - bands_produced
    if missing:
        print(f"\n  Missing bands: {missing}")

    print(f"\n  L13: {'PASS' if ok else 'FAIL'} (all 5 bands produced)")
    return ok


def _make_scenario(obj_completion, player_hp_frac, player_alive_frac):
    store = UnitStore()
    player_uids = []
    for i in range(10):
        uid = store.spawn("Vanguard", FACTION_A, 1000.0 + i * 50, 2000.0)
        player_uids.append(uid)
    for i in range(5):
        store.spawn("Raider", FACTION_B, 3000.0 + i * 50, 2000.0)

    initial_power = _initial_power(store, FACTION_A)

    alive_count = max(1, int(len(player_uids) * player_alive_frac))
    for uid in player_uids[alive_count:]:
        store.kill(uid)
    for uid in player_uids[:alive_count]:
        store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * player_hp_frac

    obj = Objective("obj_1", "eliminate_force", 1.0,
                    {"enemy_faction": FACTION_B, "initial_enemy_hp": 1.0}, is_primary=True)
    obj.completion = obj_completion

    obj_score = compute_scores([obj])
    retention = compute_retention(store, FACTION_A, initial_power)
    final_score = (obj_score * config.OUTCOME_WEIGHT_OBJECTIVE +
                   retention * config.OUTCOME_WEIGHT_RETENTION)
    band = classify_outcome(final_score, ARCHETYPE)
    return obj_score, retention, final_score, band


def _scenario_total_success():
    obj_score, retention, final, band = _make_scenario(1.0, 0.9, 1.0)
    return "Total success", obj_score, retention, final, band


def _scenario_strong_success():
    obj_score, retention, final, band = _make_scenario(0.8, 0.6, 0.8)
    return "Strong success", obj_score, retention, final, band


def _scenario_partial_success():
    obj_score, retention, final, band = _make_scenario(0.6, 0.5, 0.6)
    return "Partial success", obj_score, retention, final, band


def _scenario_partial_failure():
    obj_score, retention, final, band = _make_scenario(0.35, 0.4, 0.5)
    return "Partial failure", obj_score, retention, final, band


def _scenario_total_failure():
    obj_score, retention, final, band = _make_scenario(0.05, 0.2, 0.2)
    return "Total failure", obj_score, retention, final, band


def test_retention_affects_band():
    print(f"\n{'=' * 70}")
    print("  RETENTION COMPARISON — Same objective, different retention (L14)")
    print("=" * 70)

    obj_score_a, ret_a, final_a, band_a = _make_scenario(0.7, 0.9, 1.0)
    obj_score_b, ret_b, final_b, band_b = _make_scenario(0.7, 0.2, 0.3)

    print(f"  Scenario A (high retention): obj={obj_score_a:.3f} ret={ret_a:.3f} final={final_a:.3f} band={band_a}")
    print(f"  Scenario B (low retention):  obj={obj_score_b:.3f} ret={ret_b:.3f} final={final_b:.3f} band={band_b}")

    scores_differ = abs(final_a - final_b) > 0.01
    print(f"\n  Final scores differ: {scores_differ}")

    ok = scores_differ
    print(f"  L14: {'PASS' if ok else 'FAIL'} (retention affects final score)")
    return ok


def test_terminal_objective_completion():
    print(f"\n{'=' * 70}")
    print("  TERMINAL — Objective completion")
    print("=" * 70)

    store = UnitStore()
    store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    target = store.spawn("Raider", FACTION_B, 3000.0, 2000.0)

    obj = Objective("destroy_1", "destroy_targets", 1.0,
                    {"target_uids": [target]}, is_primary=True)

    reason = check_terminal([obj], store, FACTION_A, 0, 10000)
    print(f"  Before kill: terminal = {reason}")

    store.kill(target)
    update_objectives([obj], store, FACTION_A, 1)
    reason = check_terminal([obj], store, FACTION_A, 1, 10000)
    print(f"  After kill:  terminal = {reason} (completion={obj.completion:.1f})")

    ok = reason == "objectives_resolved"
    print(f"\n  Terminal (objective): {'PASS' if ok else 'FAIL'}")
    return ok


def test_terminal_time_expiry():
    print(f"\n{'=' * 70}")
    print("  TERMINAL — Time expiry")
    print("=" * 70)

    store = UnitStore()
    store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    store.spawn("Raider", FACTION_B, 3000.0, 2000.0)

    obj = Objective("hold_1", "hold_zone", 1.0,
                    {"zone_x": 2000.0, "zone_y": 2000.0, "zone_radius": 200,
                     "hold_duration_ticks": 99999}, is_primary=True)

    time_limit = 500
    reason = check_terminal([obj], store, FACTION_A, 499, time_limit)
    print(f"  Tick 499: terminal = {reason}")

    reason = check_terminal([obj], store, FACTION_A, 500, time_limit)
    print(f"  Tick 500: terminal = {reason}")

    ok = reason == "time_expired"
    print(f"\n  Terminal (time): {'PASS' if ok else 'FAIL'}")
    return ok


def test_terminal_force_eliminated():
    print(f"\n{'=' * 70}")
    print("  TERMINAL — Force elimination")
    print("=" * 70)

    store = UnitStore()
    player = store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    store.spawn("Raider", FACTION_B, 3000.0, 2000.0)

    obj = Objective("survive_1", "survive_duration", 1.0,
                    {"duration_ticks": 10000}, is_primary=True)

    reason = check_terminal([obj], store, FACTION_A, 50, 10000)
    print(f"  Player alive: terminal = {reason}")

    store.kill(player)
    reason = check_terminal([obj], store, FACTION_A, 51, 10000)
    print(f"  Player dead:  terminal = {reason}")

    ok = reason == "force_eliminated"
    print(f"\n  Terminal (elimination): {'PASS' if ok else 'FAIL'}")
    return ok


def test_mission_result_construction():
    print(f"\n{'=' * 70}")
    print("  MISSION RESULT — Dataclass construction")
    print("=" * 70)

    store = UnitStore()
    commander = store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    for i in range(4):
        store.spawn("Raider", FACTION_A, 2000.0 + (i + 1) * 50, 2000.0)

    target = store.spawn("Bastion", FACTION_B, 3000.0, 2000.0)
    initial_power = _initial_power(store, FACTION_A)

    objectives = [
        Objective("primary", "destroy_targets", 0.7, {"target_uids": [target]}, is_primary=True),
        Objective("secondary", "survive_duration", 0.3, {"duration_ticks": 1000}, is_primary=False),
    ]

    store.kill(target)
    store.kill(commander)
    update_objectives(objectives, store, FACTION_A, 500)
    objectives[1].completion = 0.5

    result = build_mission_result(
        mission_id="test_mission_001",
        objectives=objectives,
        store=store,
        player_faction=FACTION_A,
        initial_power=initial_power,
        archetype=ARCHETYPE,
        tick=500,
        commander_uid=commander,
    )

    print(f"  mission_id:          {result.mission_id}")
    print(f"  outcome_band:        {result.outcome_band}")
    print(f"  objective_score:     {result.objective_score:.3f}")
    print(f"  force_retention:     {result.force_retention:.3f}")
    print(f"  commander_survived:  {result.commander_survived}")
    print(f"  ticks_elapsed:       {result.ticks_elapsed}")
    print(f"  per_objective:")
    for po in result.per_objective:
        print(f"    {po['id']}: type={po['type']} completion={po['completion']:.2f} "
              f"weight={po['weight']} primary={po['is_primary']} failed={po['failed']}")

    checks = {
        "mission_id": result.mission_id == "test_mission_001",
        "outcome_band valid": result.outcome_band in [
            "total_success", "strong_success", "partial_success",
            "partial_failure", "total_failure"],
        "per_objective count": len(result.per_objective) == 2,
        "commander_survived": not result.commander_survived,
        "ticks_elapsed": result.ticks_elapsed == 500,
    }
    ok = all(checks.values())
    if not ok:
        for name, passed in checks.items():
            if not passed:
                print(f"  FAILED CHECK: {name} (got {getattr(result, name.split()[0], '?')})")

    print(f"\n  MissionResult: {'PASS' if ok else 'FAIL'}")
    return ok


def test_hold_zone_objective():
    print(f"\n{'=' * 70}")
    print("  HOLD ZONE — Per-tick evaluation")
    print("=" * 70)

    store = UnitStore()
    player = store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)

    obj = Objective("hold", "hold_zone", 1.0,
                    {"zone_x": 2000.0, "zone_y": 2000.0, "zone_radius": 200,
                     "hold_duration_ticks": 100}, is_primary=True)

    for tick in range(50):
        update_objectives([obj], store, FACTION_A, tick)
    print(f"  After 50 ticks (uncontested): completion = {obj.completion:.2f}")

    enemy = store.spawn("Raider", FACTION_B, 2050.0, 2000.0)
    for tick in range(50, 70):
        update_objectives([obj], store, FACTION_A, tick)
    print(f"  After 20 more ticks (contested): completion = {obj.completion:.2f}")

    store.kill(enemy)
    for tick in range(70, 120):
        update_objectives([obj], store, FACTION_A, tick)
    print(f"  After 50 more ticks (uncontested): completion = {obj.completion:.2f}")

    ok = obj.completion >= 1.0
    print(f"\n  Hold zone: {'PASS' if ok else 'FAIL'}")
    return ok


def run():
    print("=" * 70)
    print("CHECKPOINT 6H — Objectives and Outcome Classification")
    print("=" * 70)

    results = {}
    results["5 bands (L13)"] = test_all_5_bands()
    results["Retention (L14)"] = test_retention_affects_band()
    results["Hold zone eval"] = test_hold_zone_objective()
    results["Terminal: objective"] = test_terminal_objective_completion()
    results["Terminal: time"] = test_terminal_time_expiry()
    results["Terminal: elimination"] = test_terminal_force_eliminated()
    results["MissionResult"] = test_mission_result_construction()

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name:<24} {'PASS' if passed else 'FAIL'}")

    total_pass = sum(1 for v in results.values() if v)
    print(f"\n  {total_pass}/{len(results)} tests passed")
    print("\nCheckpoint 6H complete.")


if __name__ == "__main__":
    run()
