#!/usr/bin/env python3
"""Stage 7.5 Checkpoint D — Defensive Stand script tests.

Verifies:
  - defensive_stand.json loads and validates clean (0 errors)
  - Force A starts in 'advance_cautious_to_chokepoint', Force B in 'wait'
  - Force B timer transition fires at ~T+45s
  - Force B HP threshold fires → retreat_set_flag → sets force_b_broken bus flag
  - Force A reactive hook fires on bus.force_b_broken → advance_aggressive
  - Force A HP threshold fires → retreat_cautious
  - Force A timer transition fires at ~T+180s → advance_aggressive
  - Determinism: 5 reruns with same seed produce identical noise tables
  - force_composition templates exist and produce sensible unit rosters
"""
import os
import sys
import json
import random
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from tactical_map import TacticalMap, SpineNode
from unit import UnitStore
from command import CommandQueue
from trigger_bus import TriggerBus
from script_schema import validate_script
from script_loader import load_script
from behavior_runner import BehaviorRunner
from force_composition import COMPOSITION_TEMPLATES
import config

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0

FACTION_A = 1  # Force A — main thrust
FACTION_B = 2  # Force B — flanker


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prow(label: str, ok: bool, detail: str = "") -> None:
    global _failures
    if not ok:
        _failures += 1
    status = PASS if ok else FAIL
    suffix = f"  [{detail}]" if detail else ""
    print(f"    {label:<60}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*70}")
    print(f"  {title}")
    print(f"  {'─'*70}")


def _make_ds_map():
    """Map with chokepoint, objective, and two enemy_spawn nodes."""
    return TacticalMap(
        width=3000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(200,  1000), node_type="enemy_spawn"),   # primary (Force A)
            SpineNode(position=(200,   600), node_type="enemy_spawn"),   # secondary (Force B)
            SpineNode(position=(1200, 1000), node_type="chokepoint"),
            SpineNode(position=(2800, 1000), node_type="objective"),
        ],
    )


def _load_ds_script():
    path = os.path.join(os.path.dirname(__file__), "scripts", "defensive_stand.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _make_runner(script, tactical_map, seed=42, mission_start_tick=0):
    """One runner for both forces; Force A = faction 1, Force B = faction 2."""
    bus = TriggerBus()
    rng = random.Random(seed)
    return BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=FACTION_A,
        mission_start_tick=mission_start_tick,
        time_limit_ticks=0,
        force_faction_ids={
            "force_a_main_thrust": FACTION_A,
            "force_b_flanker":     FACTION_B,
        },
    )


def _spawn_vanguards(store, count, faction, x, y):
    for i in range(count):
        store.spawn("Vanguard", faction, x + i * 40, y)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_schema_validation() -> None:
    _section("SCHEMA — defensive_stand.json loads and validates clean")
    script = _load_ds_script()
    errors = validate_script(script)
    ok = len(errors) == 0
    _prow("0 validation errors", ok)
    if not ok:
        for e in errors:
            print(f"    UNEXPECTED ERROR: {e}")
    _prow("script_id == 'defensive_stand_v1'", script.get("script_id") == "defensive_stand_v1")
    _prow("2 forces defined", len(script.get("forces", [])) == 2)
    _prow("'force_b_broken' in trigger_bus_vocabulary",
          "force_b_broken" in script.get("trigger_bus_vocabulary", []))


def test_initial_states() -> None:
    _section("INITIAL STATES — Force A in cautious advance, Force B in wait")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 3, FACTION_A, 200, 1000)
    _spawn_vanguards(store, 2, FACTION_B, 200, 600)
    runner = _make_runner(script, tactical_map)

    rs_a = runner.runner_states[0]
    rs_b = runner.runner_states[1]
    _prow("Force A force_id == 'force_a_main_thrust'", rs_a.force_id == "force_a_main_thrust")
    _prow("Force A initial state: advance_cautious_to_chokepoint",
          rs_a.current_state == "advance_cautious_to_chokepoint")
    _prow("Force A faction_id == 1", rs_a.faction_id == FACTION_A)
    _prow("Force B force_id == 'force_b_flanker'", rs_b.force_id == "force_b_flanker")
    _prow("Force B initial state: wait", rs_b.current_state == "wait")
    _prow("Force B faction_id == 2", rs_b.faction_id == FACTION_B)
    _prow("noise table populated for both forces",
          len(rs_a.trans_noise) >= 3 and len(rs_b.trans_noise) >= 4)


def test_force_b_timer_transition() -> None:
    _section("FORCE B TIMER — 'wait' → 'advance_cautious_to_objective' at T+45s")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 3, FACTION_A, 200, 1000)
    _spawn_vanguards(store, 2, FACTION_B, 200, 600)

    # mission_start = -1200 ticks → elapsed at tick 0 = 60s > 45s / (1-0.15) ≈ 53s
    runner = _make_runner(script, tactical_map, seed=42, mission_start_tick=-1200)
    queue = CommandQueue()
    runner.step(0, store, queue)

    b_entries = [e for e in runner.eval_log if e["force_id"] == "force_b_flanker"]
    _prow("Force B has one eval log entry", len(b_entries) == 1)
    if b_entries:
        e = b_entries[0]
        _prow(f"Force B elapsed_sec >= 45",  e["elapsed_sec"] >= 45,
              f"got {e['elapsed_sec']}")
        _prow("Force B: wait → advance_cautious_to_objective",
              e["state_before"] == "wait" and e["state_after"] == "advance_cautious_to_objective",
              f"{e['state_before']} → {e['state_after']}")


def test_force_b_hp_retreat_and_bus_flag() -> None:
    _section("FORCE B RETREAT + BUS FLAG — low HP → retreat_set_flag → force_b_broken set")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 3, FACTION_A, 200, 1000)
    uids_b = []
    for i in range(2):
        uid = store.spawn("Vanguard", FACTION_B, 200 + i * 40, 600)
        uids_b.append(uid)

    runner = _make_runner(script, tactical_map, seed=42)
    # Fast-forward Force B to advance_cautious_to_objective (skip 'wait')
    runner.runner_states[1].current_state = "advance_cautious_to_objective"

    # Damage Force B to 5% HP
    from unit import FIELD_HP, FIELD_MAX_HP
    for uid in uids_b:
        store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * 0.05

    queue = CommandQueue()
    runner.step(0, store, queue)

    b_entries = [e for e in runner.eval_log if e["force_id"] == "force_b_flanker"]
    _prow("Force B eval entry recorded", len(b_entries) == 1)
    if b_entries:
        e = b_entries[0]
        _prow("Force B: advance_cautious → retreat_set_flag (HP < 30%)",
              e["state_after"] == "retreat_set_flag",
              f"got {e['state_after']!r}")
        _prow("command is 'move' (retreat behavior)", e["command"] == "move",
              f"got {e['command']!r}")

    flag_set = runner.bus.get_flag("force_b_broken")
    _prow("force_b_broken bus flag is set after transition", flag_set)


def test_force_a_reactive_hook() -> None:
    _section("FORCE A REACTIVE HOOK — bus.force_b_broken → advance_aggressive")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 4, FACTION_A, 200, 1000)
    _spawn_vanguards(store, 2, FACTION_B, 200, 600)

    runner = _make_runner(script, tactical_map, seed=42)
    runner.bus.set_flag("force_b_broken")  # pre-set the flag

    queue = CommandQueue()
    runner.step(0, store, queue)

    a_entries = [e for e in runner.eval_log if e["force_id"] == "force_a_main_thrust"]
    _prow("Force A eval entry recorded", len(a_entries) == 1)
    if a_entries:
        e = a_entries[0]
        _prow("Force A: cautious → advance_aggressive via reactive hook",
              e["state_after"] == "advance_aggressive",
              f"got {e['state_after']!r}")
        _prow("hooks_tried >= 1", e["hooks_tried"] >= 1, f"got {e['hooks_tried']}")
        _prow("command is 'attack_move'", e["command"] == "attack_move",
              f"got {e['command']!r}")

    # Verify target is objective (2800, 1000)
    cmds = [c for c in queue.all_commands() if c.type == "attack_move"]
    a_cmds = [c for c in cmds if FACTION_A in c.unit_ids]
    if a_cmds:
        tgt = (a_cmds[-1].params["target_x"], a_cmds[-1].params["target_y"])
        _prow(f"attack_move targets objective (2800, 1000)", tgt == (2800.0, 1000.0), f"got {tgt}")
    else:
        _prow("attack_move emitted for Force A", False, "no attack_move found")


def test_force_a_hp_threshold() -> None:
    _section("FORCE A HP THRESHOLD — HP < 40% → retreat_cautious")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    uids_a = []
    for i in range(3):
        uid = store.spawn("Vanguard", FACTION_A, 200 + i * 40, 1000)
        uids_a.append(uid)
    _spawn_vanguards(store, 2, FACTION_B, 200, 600)

    from unit import FIELD_HP, FIELD_MAX_HP
    for uid in uids_a:
        store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * 0.20  # 20% HP

    runner = _make_runner(script, tactical_map, seed=42)
    queue = CommandQueue()
    runner.step(0, store, queue)

    a_entries = [e for e in runner.eval_log if e["force_id"] == "force_a_main_thrust"]
    _prow("Force A eval entry recorded", len(a_entries) == 1)
    if a_entries:
        e = a_entries[0]
        _prow("Force A: advance_cautious → retreat_cautious (HP < 40%)",
              e["state_after"] == "retreat_cautious",
              f"got {e['state_after']!r}")
        _prow("command is 'move' (retreat)", e["command"] == "move",
              f"got {e['command']!r}")


def test_force_a_timer_transition() -> None:
    _section("FORCE A TIMER — T+180s → advance_aggressive")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 4, FACTION_A, 200, 1000)
    _spawn_vanguards(store, 2, FACTION_B, 200, 600)

    # elapsed at tick 0 = 4500 * 0.05 = 225s  > 180 / 0.85 ≈ 212s  (safe margin over max noise)
    runner = _make_runner(script, tactical_map, seed=42, mission_start_tick=-4500)
    queue = CommandQueue()
    runner.step(0, store, queue)

    a_entries = [e for e in runner.eval_log if e["force_id"] == "force_a_main_thrust"]
    _prow("Force A eval entry recorded", len(a_entries) == 1)
    if a_entries:
        e = a_entries[0]
        _prow(f"elapsed_sec >= 180", e["elapsed_sec"] >= 180,
              f"got {e['elapsed_sec']}")
        _prow("Force A: advance_cautious → advance_aggressive (timer)",
              e["state_after"] == "advance_aggressive",
              f"got {e['state_after']!r}")


def test_determinism() -> None:
    _section("DETERMINISM — 5 reruns with same seed produce identical noise tables")
    script = _load_ds_script()
    tactical_map = _make_ds_map()

    noise_tables = []
    for _ in range(5):
        bus = TriggerBus()
        rng = random.Random(77)
        runner = BehaviorRunner(
            script=script, tactical_map=tactical_map, bus=bus, rng=rng,
            faction_id=FACTION_A, mission_start_tick=0, time_limit_ticks=0,
            force_faction_ids={"force_a_main_thrust": FACTION_A, "force_b_flanker": FACTION_B},
        )
        # Capture noise tables for both forces (sort keys for stable comparison)
        combined = {}
        for rs in runner.runner_states:
            for k, v in rs.trans_noise.items():
                combined[str((rs.force_id, k))] = round(v, 10)
        noise_tables.append(combined)

    all_equal = all(t == noise_tables[0] for t in noise_tables)
    _prow("All 5 noise tables are identical", all_equal)
    key_count = len(noise_tables[0])
    _prow(f"Noise table has {key_count} entries (≥5 expected)", key_count >= 5,
          f"got {key_count}")

    # Also verify different seeds produce different tables
    rng2 = random.Random(999)
    runner2 = BehaviorRunner(
        script=script, tactical_map=tactical_map, bus=TriggerBus(), rng=rng2,
        faction_id=FACTION_A, mission_start_tick=0,
    )
    diff_table = {str((rs.force_id, k)): round(v, 10)
                  for rs in runner2.runner_states for k, v in rs.trans_noise.items()}
    _prow("Different seed produces different noise table", diff_table != noise_tables[0])


def test_force_composition_templates() -> None:
    _section("FORCE COMPOSITION — templates exist and reference valid unit types")
    for template_name in ("defensive_stand_attacker", "defensive_stand_attacker_light"):
        template = COMPOSITION_TEMPLATES[template_name]
        ratios_sum = sum(template.values())
        all_valid = all(ut in config.UNIT_STATS for ut in template)
        ratio_ok = abs(ratios_sum - 1.0) <= 0.01
        _prow(f"{template_name}: all unit types valid", all_valid)
        _prow(f"{template_name}: ratios sum to ~1.0 ({ratios_sum:.2f})", ratio_ok)


# ── Pretty trace ──────────────────────────────────────────────────────────────

def _print_mission_trace() -> None:
    _section("MISSION TRACE — both forces over 10 eval cycles (healthy HP, T=0)")
    script = _load_ds_script()
    tactical_map = _make_ds_map()
    store = UnitStore()
    _spawn_vanguards(store, 4, FACTION_A, 200, 1000)
    _spawn_vanguards(store, 3, FACTION_B, 200, 600)

    runner = _make_runner(script, tactical_map, seed=0)
    queue = CommandQueue()
    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 10):
        runner.step(tick, store, queue)

    print(f"\n  {'Force':<22}  {'Tick':>5}  {'Elapsed':>8}  {'State':<32}  {'Cmd'}")
    print(f"  {'─'*22}  {'─'*5}  {'─'*8}  {'─'*32}  {'─'*12}")
    for e in runner.eval_log:
        arrow = (f"{e['state_before'][:14]}→{e['state_after'][:14]}"
                 if e["state_before"] != e["state_after"]
                 else e["state_after"])
        print(
            f"  {e['force_id']:<22}  {e['tick']:>5}  {e['elapsed_sec']:>7.1f}s"
            f"  {arrow:<32}  {e['command'] or 'none'}"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 72)
    print("  STAGE 7.5 CHECKPOINT D — Defensive Stand Script")
    print("=" * 72)

    test_schema_validation()
    test_initial_states()
    test_force_b_timer_transition()
    test_force_b_hp_retreat_and_bus_flag()
    test_force_a_reactive_hook()
    test_force_a_hp_threshold()
    test_force_a_timer_transition()
    test_determinism()
    test_force_composition_templates()
    _print_mission_trace()

    print()
    print("=" * 72)
    if _failures == 0:
        print(f"  {PASS}  All defensive stand tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 72)
    sys.exit(0 if _failures == 0 else 1)
