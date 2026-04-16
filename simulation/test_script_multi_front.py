#!/usr/bin/env python3
"""Stage 7.5 Checkpoint F — Multi-Front Defense script tests.

Verifies:
  - All three forces start in advance_cautious
  - Scenario 1: Player crushes Force A → Forces B and C escalate via cascading hooks
  - Scenario 2: Player ignores all fronts → staggered escalation (A at ~60s, B at ~120s, C at ~180s)
  - any_front_broke_through fires when a force commits to advance_aggressive
  - 2-force variant loads and runs without crashing on a 2-vector map
  - Determinism holds across 3 runs with the same seed
"""
import os
import sys
import random
import copy
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

_FORCE_FACTIONS = {
    "force_a_primary":   1,
    "force_b_secondary": 2,
    "force_c_tertiary":  3,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prow(label: str, ok: bool, detail: str = "") -> None:
    global _failures
    if not ok:
        _failures += 1
    status = PASS if ok else FAIL
    suffix = f"  [{detail}]" if detail else ""
    print(f"    {label:<66}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*74}")
    print(f"  {title}")
    print(f"  {'─'*74}")


def _make_test_map():
    """3-vector map: objective east, chokepoint centre, enemy_spawn west."""
    return TacticalMap(
        width=2000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(1800, 1000), node_type="objective"),
            SpineNode(position=(1000, 1000), node_type="chokepoint"),
            SpineNode(position=(200,  1000), node_type="enemy_spawn"),
        ],
    )


def _spawn_faction(store: UnitStore, count: int, faction: int, x: int, y: int) -> None:
    for i in range(count):
        store.spawn("Vanguard", faction, x=x + i * 30, y=y)


def _make_store_3front():
    store = UnitStore()
    _spawn_faction(store, 3, 1, 200, 1000)  # Force A
    _spawn_faction(store, 3, 2, 200, 700)   # Force B
    _spawn_faction(store, 3, 3, 200, 1300)  # Force C
    return store


def _make_runner(script, tactical_map, mission_start_tick: int = 0, seed: int = 42,
                 force_faction_ids: dict | None = None):
    """Returns (runner, bus)."""
    bus = TriggerBus()
    rng = random.Random(seed)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=mission_start_tick,
        time_limit_ticks=0,
        force_faction_ids=force_faction_ids or _FORCE_FACTIONS,
    )
    return runner, bus


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_initial_states() -> None:
    _section("INITIAL STATES — all three forces start in advance_cautious")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()
    runner, _ = _make_runner(script, tactical_map)

    fa, fb, fc = runner.runner_states
    _prow("force_a_primary:   force_id correct",    fa.force_id == "force_a_primary")
    _prow("force_a_primary:   advance_cautious",     fa.current_state == "advance_cautious",
          f"got {fa.current_state!r}")
    _prow("force_b_secondary: force_id correct",    fb.force_id == "force_b_secondary")
    _prow("force_b_secondary: advance_cautious",     fb.current_state == "advance_cautious",
          f"got {fb.current_state!r}")
    _prow("force_c_tertiary:  force_id correct",    fc.force_id == "force_c_tertiary")
    _prow("force_c_tertiary:  advance_cautious",     fc.current_state == "advance_cautious",
          f"got {fc.current_state!r}")


def test_scenario1_cascade_aggression() -> None:
    _section("SCENARIO 1 — Force A broken: Forces B and C escalate via cascading hooks")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()
    store = _make_store_3front()
    queue = CommandQueue()
    runner, bus = _make_runner(script, tactical_map)

    # Simulate Force A having retreated: set force_a_broken before eval
    bus.set_flag("force_a_broken")
    runner.step(0, store, queue)

    fa, fb, fc = runner.runner_states
    _prow("Force B escalated to advance_aggressive",
          fb.current_state == "advance_aggressive",  f"got {fb.current_state!r}")
    _prow("Force C escalated to advance_aggressive",
          fc.current_state == "advance_aggressive",  f"got {fc.current_state!r}")
    _prow("any_front_broke_through set (B or C committed)", bus.get_flag("any_front_broke_through"))
    # Force A has force_a_broken already set externally; it doesn't run into retreat_cautious
    # here, so any_front_broke_through is set by B or C entering advance_aggressive
    log_b = [e for e in runner.eval_log if e["force_id"] == "force_b_secondary"]
    log_c = [e for e in runner.eval_log if e["force_id"] == "force_c_tertiary"]
    _prow("Force B log: state_before was advance_cautious",
          log_b and log_b[0]["state_before"] == "advance_cautious",
          f"got {log_b[0]['state_before']!r}" if log_b else "no log")
    _prow("Force C log: state_before was advance_cautious",
          log_c and log_c[0]["state_before"] == "advance_cautious",
          f"got {log_c[0]['state_before']!r}" if log_c else "no log")
    _prow("Escalation direction: both went AGGRESSIVE (not retreat)",
          fb.current_state == "advance_aggressive" and fc.current_state == "advance_aggressive")


def test_scenario2_staggered_escalation() -> None:
    _section("SCENARIO 2 — Staggered escalation: A at ~60s, B at ~120s, C at ~180s")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()

    # Safety margins for noise_pct=0.15: need elapsed > threshold / (1 - 0.15)
    # Force A >= 60s  → need > 70.6s → use 80s  = 1600 ticks → start -1600
    # Force B >= 120s → need > 141s  → use 160s = 3200 ticks → start -3200
    # Force C >= 180s → need > 212s  → use 240s = 4800 ticks → start -4800

    def _run_at(elapsed_ticks: int, seed: int = 42):
        store = _make_store_3front()
        queue = CommandQueue()
        runner, bus = _make_runner(script, tactical_map,
                                   mission_start_tick=-elapsed_ticks, seed=seed)
        runner.step(0, store, queue)
        return runner.runner_states, bus

    # At 80s: only Force A's timer fires (60s); B (120s) and C (180s) don't
    states_80, bus_80 = _run_at(1600)
    fa80, fb80, fc80 = states_80
    _prow("At 80s: Force A escalated",
          fa80.current_state == "advance_aggressive",  f"got {fa80.current_state!r}")
    _prow("At 80s: Force B still cautious (timer 120s not reached)",
          fb80.current_state == "advance_cautious",    f"got {fb80.current_state!r}")
    _prow("At 80s: Force C still cautious (timer 180s not reached)",
          fc80.current_state == "advance_cautious",    f"got {fc80.current_state!r}")
    _prow("At 80s: any_front_broke_through set by Force A's advance_aggressive on_enter",
          bus_80.get_flag("any_front_broke_through"))

    # At 160s: Force A and Force B timers both fire; C (180s) doesn't
    states_160, bus_160 = _run_at(3200)
    fa160, fb160, fc160 = states_160
    _prow("At 160s: Force A escalated",
          fa160.current_state == "advance_aggressive", f"got {fa160.current_state!r}")
    _prow("At 160s: Force B escalated (timer 120s fired)",
          fb160.current_state == "advance_aggressive", f"got {fb160.current_state!r}")
    _prow("At 160s: Force C still cautious (timer 180s not reached)",
          fc160.current_state == "advance_cautious",   f"got {fc160.current_state!r}")

    # At 240s: all three timers have fired
    states_240, bus_240 = _run_at(4800)
    fa240, fb240, fc240 = states_240
    _prow("At 240s: Force A escalated",
          fa240.current_state == "advance_aggressive", f"got {fa240.current_state!r}")
    _prow("At 240s: Force B escalated",
          fb240.current_state == "advance_aggressive", f"got {fb240.current_state!r}")
    _prow("At 240s: Force C escalated (timer 180s fired)",
          fc240.current_state == "advance_aggressive", f"got {fc240.current_state!r}")


def test_any_front_broke_through() -> None:
    _section("ANY_FRONT_BROKE_THROUGH — flag set when a force commits to advance_aggressive")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()
    store = _make_store_3front()
    queue = CommandQueue()
    # 80s elapsed → Force A escalates
    runner, bus = _make_runner(script, tactical_map, mission_start_tick=-1600)

    _prow("any_front_broke_through NOT set before eval", not bus.get_flag("any_front_broke_through"))
    runner.step(0, store, queue)
    _prow("any_front_broke_through SET after Force A advances aggressive",
          bus.get_flag("any_front_broke_through"))


def test_2force_variant() -> None:
    _section("2-FORCE VARIANT — 2-force script runs without crashing on 2-vector map")
    script_3 = load_script("multi_front_defense")

    # Build a 2-force version from the first two forces of the 3-force script
    script_2 = copy.deepcopy(script_3)
    script_2["script_id"] = "multi_front_defense_2v"
    script_2["forces"] = script_2["forces"][:2]

    tactical_map = TacticalMap(
        width=2000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(1800, 1000), node_type="objective"),
            SpineNode(position=(1000, 1000), node_type="chokepoint"),
            SpineNode(position=(200,  1000), node_type="enemy_spawn"),
        ],
    )
    store = UnitStore()
    _spawn_faction(store, 3, 1, 200, 1000)
    _spawn_faction(store, 3, 2, 200, 700)
    queue = CommandQueue()

    bus = TriggerBus()
    rng = random.Random(0)
    runner = BehaviorRunner(
        script=script_2,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=0,
        time_limit_ticks=0,
        force_faction_ids={"force_a_primary": 1, "force_b_secondary": 2},
    )

    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    crashed = False
    try:
        for tick in range(INTERVAL * 4):
            runner.step(tick, store, queue)
    except Exception as e:
        crashed = True
        _prow(f"2-force variant did not crash",  False, str(e))

    if not crashed:
        _prow("2-force variant ran 4 eval cycles without crashing", True)
        _prow("eval_log has entries for both forces",
              any(e["force_id"] == "force_a_primary"   for e in runner.eval_log) and
              any(e["force_id"] == "force_b_secondary" for e in runner.eval_log))
        _prow("runner has exactly 2 states",       len(runner.runner_states) == 2)


def test_determinism() -> None:
    _section("DETERMINISM — 3 runs with same seed produce identical state sequences")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()

    def _run(seed: int) -> list:
        store = _make_store_3front()
        queue = CommandQueue()
        bus = TriggerBus()
        bus.set_flag("force_a_broken")
        rng = random.Random(seed)
        runner = BehaviorRunner(
            script=script,
            tactical_map=tactical_map,
            bus=bus,
            rng=rng,
            faction_id=1,
            mission_start_tick=0,
            time_limit_ticks=0,
            force_faction_ids=_FORCE_FACTIONS,
        )
        INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
        for tick in range(INTERVAL * 5):
            runner.step(tick, store, queue)
        return [(e["force_id"], e["state_before"], e["state_after"]) for e in runner.eval_log]

    r1 = _run(33)
    r2 = _run(33)
    r3 = _run(33)
    _prow("run1 == run2",                              r1 == r2)
    _prow("run2 == run3",                              r2 == r3)
    _prow("log is non-empty (scenario actually ran)",  len(r1) > 0, f"{len(r1)} entries")


# ── Pretty-print trace ─────────────────────────────────────────────────────────

def _print_sample_trace() -> None:
    _section("SAMPLE TRACE — cascade scenario (Force A broken), 5 eval cycles")
    script = load_script("multi_front_defense")
    tactical_map = _make_test_map()
    store = _make_store_3front()
    queue = CommandQueue()
    bus = TriggerBus()
    bus.set_flag("force_a_broken")
    rng = random.Random(0)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=0,
        time_limit_ticks=0,
        force_faction_ids=_FORCE_FACTIONS,
    )
    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 5):
        runner.step(tick, store, queue)

    print(f"\n  {'Tick':>5}  {'Force':<22}  {'Before':<22}  {'After':<22}  {'Cmd'}")
    print(f"  {'─'*5}  {'─'*22}  {'─'*22}  {'─'*22}  {'─'*12}")
    for e in runner.eval_log:
        print(
            f"  {e['tick']:>5}  {e['force_id']:<22}  {e['state_before']:<22}  "
            f"{e['state_after']:<22}  {e['command'] or 'none'}"
        )
    print(f"\n  Bus: force_a_broken={bus.get_flag('force_a_broken')}  "
          f"force_b_broken={bus.get_flag('force_b_broken')}  "
          f"force_c_broken={bus.get_flag('force_c_broken')}  "
          f"any_front_broke_through={bus.get_flag('any_front_broke_through')}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 74)
    print("  STAGE 7.5 CHECKPOINT F — Multi-Front Defense Script")
    print("=" * 74)

    test_initial_states()
    test_scenario1_cascade_aggression()
    test_scenario2_staggered_escalation()
    test_any_front_broke_through()
    test_2force_variant()
    test_determinism()
    _print_sample_trace()

    print()
    print("=" * 74)
    if _failures == 0:
        print(f"  {PASS}  All multi-front defense tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 74)
    sys.exit(0 if _failures == 0 else 1)
