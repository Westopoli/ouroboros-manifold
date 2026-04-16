#!/usr/bin/env python3
"""Stage 7.5 Checkpoint C — BehaviorRunner tests.

Verifies:
  - Runner starts in stub script's initial_state ('advance_cautious')
  - Emits 'attack_move' commands toward the objective spine node each eval cycle
  - Stays in 'advance_cautious' while HP is healthy and timer hasn't elapsed
  - Transitions to 'retreat_cautious' when unit HP drops to near-zero
  - Transitions to 'advance_aggressive' when timer condition is satisfied
  - eval_log records correct per-cycle data (state, unit count, command)
  - Engine integration: behavior_runners wired into TacticalEngine.step()
"""
import os
import sys
import random
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from tactical_map import TacticalMap, SpineNode
from unit import UnitStore, FIELD_HP, FIELD_MAX_HP
from command import CommandQueue
from trigger_bus import TriggerBus
from script_loader import load_script
from behavior_runner import BehaviorRunner
import config

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prow(label: str, ok: bool, detail: str = "") -> None:
    global _failures
    if not ok:
        _failures += 1
    status = PASS if ok else FAIL
    suffix = f"  [{detail}]" if detail else ""
    print(f"    {label:<58}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*70}")
    print(f"  {title}")
    print(f"  {'─'*70}")


# ── Test map ──────────────────────────────────────────────────────────────────

def _make_test_map():
    """2000×2000 map with objective at east end and enemy_spawn at west end."""
    return TacticalMap(
        width=2000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(1800, 1000), node_type="objective"),
            SpineNode(position=(200,  1000), node_type="enemy_spawn"),
        ],
    )


def _spawn_enemy_force(store: UnitStore, count: int = 3, faction: int = 1):
    """Spawn Vanguard units near the enemy_spawn node."""
    uids = []
    for i in range(count):
        uid = store.spawn("Vanguard", faction, x=200 + i * 30, y=1000)
        uids.append(uid)
    return uids


def _make_runner(script, tactical_map, faction_id=1, seed=42):
    bus = TriggerBus()
    rng = random.Random(seed)
    return BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=faction_id,
        mission_start_tick=0,
        time_limit_ticks=0,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_initial_state() -> None:
    _section("INITIAL STATE — runner starts in correct state")
    script = load_script("siege_breaking")  # non-prototype → stub
    tactical_map = _make_test_map()
    runner = _make_runner(script, tactical_map)

    rs = runner.runner_states[0]
    _prow("force_id is 'force_main'",   rs.force_id == "force_main")
    _prow("initial state: advance_cautious", rs.current_state == "advance_cautious")
    _prow("mission_start_tick == 0",    rs.mission_start_tick == 0)
    _prow("trans_noise table populated", len(rs.trans_noise) >= 2)


def test_attack_move_toward_objective() -> None:
    _section("ATTACK_MOVE — emits attack_move toward objective each eval cycle")
    script = load_script("raid")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    uids = _spawn_enemy_force(store, count=3, faction=1)
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1)

    EVAL_INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    RUN_TICKS = EVAL_INTERVAL * 5  # 5 evaluation cycles

    for tick in range(RUN_TICKS):
        runner.step(tick, store, queue)

    expected_evals = 5  # ticks 0, 40, 80, 120, 160
    actual_evals = len(runner.eval_log)
    _prow(f"eval_log has {expected_evals} entries", actual_evals == expected_evals,
          f"got {actual_evals}")

    # Every command should be attack_move
    commands_all_attack_move = all(e["command"] == "attack_move" for e in runner.eval_log)
    _prow("all eval cycles emit 'attack_move'", commands_all_attack_move)

    # State never changed (healthy HP, timer not elapsed)
    states_stable = all(e["state_after"] == "advance_cautious" for e in runner.eval_log)
    _prow("state stays 'advance_cautious' throughout", states_stable)

    # Command target should be objective position (1800, 1000)
    cmds_at_eval = [c for c in queue.all_commands() if c.type == "attack_move"]
    target_correct = all(
        c.params["target_x"] == 1800 and c.params["target_y"] == 1000
        for c in cmds_at_eval
    )
    _prow("all attack_move targets objective (1800, 1000)", target_correct)


def test_hp_threshold_transition() -> None:
    _section("HP THRESHOLD — transitions to retreat when HP is near zero")
    script = load_script("evacuation")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=3, faction=1)
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1)

    # Damage units to ~10% HP (well below the 0.30 threshold in stub)
    for uid in range(store.count):
        if store.alive[uid]:
            store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * 0.08

    # Step once at an eval tick
    runner.step(0, store, queue)

    log = runner.eval_log
    _prow("one eval log entry recorded", len(log) == 1)
    if log:
        entry = log[0]
        _prow(f"state_before is 'advance_cautious'",
              entry["state_before"] == "advance_cautious")
        _prow(f"state_after is 'retreat_cautious' (HP transition fired)",
              entry["state_after"] == "retreat_cautious",
              f"got {entry['state_after']!r}")
        _prow("command issued is 'move' (retreat behavior)",
              entry["command"] == "move",
              f"got {entry['command']!r}")


def test_timer_transition() -> None:
    _section("TIMER TRANSITION — advances to aggressive state after 120 elapsed sec")
    script = load_script("suppression")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=3, faction=1)
    queue = CommandQueue()

    # Runner started at tick 0; simulate starting the mission 2500 ticks ago
    # so elapsed = 2500 * 0.05 = 125 sec > 120 sec threshold
    bus = TriggerBus()
    rng = random.Random(99)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=-2500,  # mission started 2500 ticks ago
        time_limit_ticks=0,
    )

    runner.step(0, store, queue)

    log = runner.eval_log
    _prow("one eval log entry recorded", len(log) == 1)
    if log:
        entry = log[0]
        _prow("elapsed_sec ≥ 120 (timer fires)",  entry["elapsed_sec"] >= 120.0,
              f"elapsed={entry['elapsed_sec']}")
        _prow("state_after is 'advance_aggressive'",
              entry["state_after"] == "advance_aggressive",
              f"got {entry['state_after']!r}")


def test_no_units_skips_eval() -> None:
    _section("NO UNITS — runner skips evaluation when faction has no alive units")
    script = load_script("rear_guard")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    # Intentionally spawn no units
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1)

    runner.step(0, store, queue)

    _prow("eval_log is empty when no alive units", len(runner.eval_log) == 0,
          f"got {len(runner.eval_log)}")


def test_non_eval_ticks_skipped() -> None:
    _section("THROTTLE — runner skips non-evaluation ticks")
    script = load_script("reconquest")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=2, faction=1)
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1)

    # Step for one full interval minus one tick (no full cycle complete except tick 0)
    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL + 1):
        runner.step(tick, store, queue)

    # Should have entries at tick 0 and tick INTERVAL only
    eval_ticks = [e["tick"] for e in runner.eval_log]
    _prow(f"exactly 2 eval entries (tick 0 and tick {INTERVAL})",
          len(eval_ticks) == 2, f"got {eval_ticks}")


def test_engine_integration() -> None:
    _section("ENGINE INTEGRATION — BehaviorRunner.step() wired into TacticalEngine.step()")
    from tactical_engine import TacticalEngine

    script = load_script("siege_breaking")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=3, faction=1)

    engine = TacticalEngine(tactical_map, store=store, seed=0)
    bus = TriggerBus()
    rng = random.Random(7)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=0,
        time_limit_ticks=0,
    )

    # Temporarily enable the flag and attach the runner
    orig_flag = config.ENABLE_BEHAVIOR_SCRIPTS
    config.ENABLE_BEHAVIOR_SCRIPTS = True
    engine.behavior_runners = [runner]

    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for _ in range(INTERVAL * 3):
        engine.step()

    config.ENABLE_BEHAVIOR_SCRIPTS = orig_flag

    evals = len(runner.eval_log)
    _prow(f"runner received {evals} eval calls via engine.step()", evals == 3,
          f"got {evals}")
    _prow("behavior_runners attribute present on engine",
          hasattr(engine, "behavior_runners"))


def test_eval_log_fields() -> None:
    _section("EVAL LOG — per-entry fields are correct and complete")
    script = load_script("evacuation")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=4, faction=1)
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1)

    runner.step(0, store, queue)

    log = runner.eval_log
    _prow("log has 1 entry", len(log) == 1)
    if not log:
        return
    e = log[0]

    required_keys = {"tick", "elapsed_sec", "force_id", "state_before", "state_after",
                     "unit_count", "hooks_tried", "trans_tried", "command"}
    _prow("all required fields present", required_keys.issubset(e.keys()))
    _prow(f"tick == 0",                    e["tick"] == 0)
    _prow(f"elapsed_sec == 0.0",           e["elapsed_sec"] == 0.0)
    _prow(f"unit_count == 4",              e["unit_count"] == 4)
    _prow(f"state_before == state_after",  e["state_before"] == e["state_after"])
    _prow(f"trans_tried >= 1",             e["trans_tried"] >= 1,
          f"got {e['trans_tried']}")


# ── Pretty-print eval log ──────────────────────────────────────────────────────

def _print_sample_trace() -> None:
    _section("SAMPLE TRACE — 8 eval cycles, healthy force (advance_cautious)")
    script = load_script("siege_breaking")  # stub
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_enemy_force(store, count=4, faction=1)
    queue = CommandQueue()
    runner = _make_runner(script, tactical_map, faction_id=1, seed=0)

    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 8):
        runner.step(tick, store, queue)

    print(f"\n  {'Tick':>5}  {'Elapsed':>8}  {'State':<22}  {'Units':>5}  {'Trans':>5}  {'Command'}")
    print(f"  {'─'*5}  {'─'*8}  {'─'*22}  {'─'*5}  {'─'*5}  {'─'*12}")
    for e in runner.eval_log:
        transition_arrow = (
            f"{e['state_before'][:10]}→{e['state_after'][:10]}"
            if e["state_before"] != e["state_after"]
            else e["state_after"]
        )
        print(
            f"  {e['tick']:>5}  {e['elapsed_sec']:>7.1f}s  {transition_arrow:<22}  "
            f"{e['unit_count']:>5}  {e['trans_tried']:>5}  {e['command'] or 'none'}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 72)
    print("  STAGE 7.5 CHECKPOINT C — BehaviorRunner")
    print("=" * 72)

    test_initial_state()
    test_attack_move_toward_objective()
    test_hp_threshold_transition()
    test_timer_transition()
    test_no_units_skips_eval()
    test_non_eval_ticks_skipped()
    test_engine_integration()
    test_eval_log_fields()
    _print_sample_trace()

    print()
    print("=" * 72)
    if _failures == 0:
        print(f"  {PASS}  All runner tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 72)
    sys.exit(0 if _failures == 0 else 1)
