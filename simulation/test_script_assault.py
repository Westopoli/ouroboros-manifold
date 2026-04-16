#!/usr/bin/env python3
"""Stage 7.5 Checkpoint E — Assault script tests.

Verifies:
  - Both forces start in their correct initial states
  - Scenario 1: inner_breach flag → Force B commits immediately
  - Scenario 2: HP attrition → Force A weakens, sets force_a_hp_low, Force B commits same cycle
  - Scenario 3: Stall → Force B commits after T+240s timer (no other triggers)
  - No false commits: Force B holds with healthy Force A, no flags, short elapsed time
  - Determinism: same seed, same scenario → identical state sequence across 3 runs
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
    print(f"    {label:<64}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*72}")
    print(f"  {title}")
    print(f"  {'─'*72}")


def _make_test_map():
    """3000×2000 map: garrison defends objective at west, spawns at east."""
    return TacticalMap(
        width=3000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(1500, 1000), node_type="objective"),
            SpineNode(position=(2500, 1000), node_type="enemy_spawn"),
        ],
    )


def _spawn_faction(store: UnitStore, count: int, faction: int, x: int, y: int) -> None:
    for i in range(count):
        store.spawn("Vanguard", faction, x=x + i * 30, y=y)


def _make_runner(script, tactical_map, mission_start_tick: int = 0, seed: int = 42):
    """Returns (runner, bus). Force A = faction 1, Force B = faction 2."""
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
        force_faction_ids={"force_a_garrison": 1, "force_b_reserve": 2},
    )
    return runner, bus


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_initial_states() -> None:
    _section("INITIAL STATES — both forces start in correct states")
    script = load_script("assault")
    tactical_map = _make_test_map()
    runner, _ = _make_runner(script, tactical_map)

    fa = runner.runner_states[0]
    fb = runner.runner_states[1]
    _prow("force_a_garrison: force_id correct",           fa.force_id == "force_a_garrison")
    _prow("force_a_garrison: initial_state defend_aggressive",
          fa.current_state == "defend_aggressive",         f"got {fa.current_state!r}")
    _prow("force_b_reserve: force_id correct",            fb.force_id == "force_b_reserve")
    _prow("force_b_reserve: initial_state hold_position",
          fb.current_state == "hold_position",             f"got {fb.current_state!r}")
    _prow("trans_noise tables populated for both forces",
          len(fa.trans_noise) >= 1 and len(fb.trans_noise) >= 2)


def test_scenario1_inner_breach() -> None:
    _section("SCENARIO 1 — inner_breach: Force B commits immediately on flag")
    script = load_script("assault")
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_faction(store, 4, 1, 2500, 1000)  # Force A garrison
    _spawn_faction(store, 3, 2, 2500, 800)   # Force B reserve
    queue = CommandQueue()
    runner, bus = _make_runner(script, tactical_map)

    bus.set_flag("inner_breach")
    runner.step(0, store, queue)

    fa = runner.runner_states[0]
    fb = runner.runner_states[1]
    _prow("Force A stays in defend_aggressive (HP healthy)",
          fa.current_state == "defend_aggressive",         f"got {fa.current_state!r}")
    _prow("Force B transitions to commit_aggressive",
          fb.current_state == "commit_aggressive",         f"got {fb.current_state!r}")
    _prow("reserve_committed flag is set",                bus.get_flag("reserve_committed"))
    _prow("force_a_hp_low NOT set",                       not bus.get_flag("force_a_hp_low"))
    log_b = [e for e in runner.eval_log if e["force_id"] == "force_b_reserve"]
    _prow("Force B log shows state transition",
          len(log_b) == 1 and log_b[0]["state_before"] == "hold_position",
          f"before={log_b[0]['state_before']!r}" if log_b else "no log entry")


def test_scenario2_hp_attrition() -> None:
    _section("SCENARIO 2 — HP attrition: Force A weakens, Force B commits same eval cycle")
    script = load_script("assault")
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_faction(store, 4, 1, 2500, 1000)  # Force A garrison
    _spawn_faction(store, 3, 2, 2500, 800)   # Force B reserve
    queue = CommandQueue()
    runner, bus = _make_runner(script, tactical_map)

    # Damage Force A to 40% HP — safely below 0.50 threshold even with +10% noise
    # (worst-case perturbed threshold: 0.50 * 1.10 = 0.55; 0.40 < 0.55 guaranteed)
    for uid in range(store.count):
        if store.alive[uid] and store.faction[uid] == 1:
            store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * 0.40

    runner.step(0, store, queue)

    fa = runner.runner_states[0]
    fb = runner.runner_states[1]
    _prow("Force A transitions to defend_weakened",
          fa.current_state == "defend_weakened",           f"got {fa.current_state!r}")
    _prow("force_a_hp_low flag set by Force A on_enter",  bus.get_flag("force_a_hp_low"))
    _prow("Force B transitions to commit_aggressive (same cycle)",
          fb.current_state == "commit_aggressive",         f"got {fb.current_state!r}")
    _prow("reserve_committed flag is set",                bus.get_flag("reserve_committed"))


def test_scenario3_timer() -> None:
    _section("SCENARIO 3 — stall: Force B commits after T+240s, no other triggers")
    script = load_script("assault")
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_faction(store, 4, 1, 2500, 1000)  # Force A at full HP
    _spawn_faction(store, 3, 2, 2500, 800)   # Force B
    queue = CommandQueue()

    # 300s elapsed > 282s safety margin (240 / (1 - 0.15) ≈ 282s)
    # 300s / 0.05s_per_tick = 6000 ticks → mission_start_tick = -6000
    bus = TriggerBus()
    rng = random.Random(42)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=-6000,
        time_limit_ticks=0,
        force_faction_ids={"force_a_garrison": 1, "force_b_reserve": 2},
    )

    runner.step(0, store, queue)

    fa = runner.runner_states[0]
    fb = runner.runner_states[1]
    log_b = [e for e in runner.eval_log if e["force_id"] == "force_b_reserve"]
    _prow("Force A stays in defend_aggressive (HP healthy)",
          fa.current_state == "defend_aggressive",         f"got {fa.current_state!r}")
    _prow("Force B commits via timer",
          fb.current_state == "commit_aggressive",         f"got {fb.current_state!r}")
    if log_b:
        _prow("elapsed_sec ≥ 240 in Force B log",
              log_b[0]["elapsed_sec"] >= 240.0,            f"got {log_b[0]['elapsed_sec']}")
    _prow("reserve_committed flag is set",                bus.get_flag("reserve_committed"))
    _prow("force_a_hp_low NOT set (Force A HP was healthy)", not bus.get_flag("force_a_hp_low"))


def test_no_false_commits() -> None:
    _section("NO FALSE COMMITS — Force B holds in hold_position with no triggers")
    script = load_script("assault")
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_faction(store, 4, 1, 2500, 1000)
    _spawn_faction(store, 3, 2, 2500, 800)
    queue = CommandQueue()
    runner, bus = _make_runner(script, tactical_map, mission_start_tick=0)

    # Run 5 eval cycles — no damage, no bus flags, timer at ~10s (way below 240s)
    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 5):
        runner.step(tick, store, queue)

    fb = runner.runner_states[1]
    _prow("Force B stays in hold_position throughout",
          fb.current_state == "hold_position",             f"got {fb.current_state!r}")
    _prow("reserve_committed NOT set",                    not bus.get_flag("reserve_committed"))


def test_determinism() -> None:
    _section("DETERMINISM — 3 runs with same seed produce identical state sequences")
    script = load_script("assault")
    tactical_map = _make_test_map()

    def _run(seed: int) -> list:
        store = UnitStore()
        _spawn_faction(store, 4, 1, 2500, 1000)
        _spawn_faction(store, 3, 2, 2500, 800)
        queue = CommandQueue()
        bus = TriggerBus()
        bus.set_flag("inner_breach")
        rng = random.Random(seed)
        runner = BehaviorRunner(
            script=script,
            tactical_map=tactical_map,
            bus=bus,
            rng=rng,
            faction_id=1,
            mission_start_tick=0,
            time_limit_ticks=0,
            force_faction_ids={"force_a_garrison": 1, "force_b_reserve": 2},
        )
        INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
        for tick in range(INTERVAL * 6):
            runner.step(tick, store, queue)
        return [(e["force_id"], e["state_before"], e["state_after"]) for e in runner.eval_log]

    r1 = _run(77)
    r2 = _run(77)
    r3 = _run(77)
    _prow("run1 == run2",   r1 == r2)
    _prow("run2 == run3",   r2 == r3)
    _prow("log is non-empty (scenario actually ran)", len(r1) > 0, f"got {len(r1)} entries")


# ── Pretty-print scenario trace ────────────────────────────────────────────────

def _print_sample_trace() -> None:
    _section("SAMPLE TRACE — inner_breach scenario, 6 eval cycles")
    script = load_script("assault")
    tactical_map = _make_test_map()
    store = UnitStore()
    _spawn_faction(store, 4, 1, 2500, 1000)
    _spawn_faction(store, 3, 2, 2500, 800)
    queue = CommandQueue()
    bus = TriggerBus()
    bus.set_flag("inner_breach")
    rng = random.Random(0)
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=0,
        time_limit_ticks=0,
        force_faction_ids={"force_a_garrison": 1, "force_b_reserve": 2},
    )

    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 6):
        runner.step(tick, store, queue)

    print(f"\n  {'Tick':>5}  {'Force':<20}  {'State Before':<22}  {'State After':<22}  {'Cmd'}")
    print(f"  {'─'*5}  {'─'*20}  {'─'*22}  {'─'*22}  {'─'*12}")
    for e in runner.eval_log:
        transition = (
            f"→ {e['state_after']}"
            if e["state_before"] != e["state_after"]
            else ""
        )
        print(
            f"  {e['tick']:>5}  {e['force_id']:<20}  {e['state_before']:<22}  "
            f"{e['state_after']:<22}  {e['command'] or 'none'}"
        )
    print(f"\n  Bus flags after trace: "
          f"inner_breach={bus.get_flag('inner_breach')}  "
          f"reserve_committed={bus.get_flag('reserve_committed')}  "
          f"force_a_hp_low={bus.get_flag('force_a_hp_low')}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 72)
    print("  STAGE 7.5 CHECKPOINT E — Assault Script")
    print("=" * 72)

    test_initial_states()
    test_scenario1_inner_breach()
    test_scenario2_hp_attrition()
    test_scenario3_timer()
    test_no_false_commits()
    test_determinism()
    _print_sample_trace()

    print()
    print("=" * 72)
    if _failures == 0:
        print(f"  {PASS}  All assault script tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 72)
    sys.exit(0 if _failures == 0 else 1)
