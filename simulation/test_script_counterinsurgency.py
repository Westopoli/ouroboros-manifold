#!/usr/bin/env python3
"""Stage 7.5 Checkpoint G — Counterinsurgency script tests.

Verifies:
  - Fragmentation roll distribution over 50 missions matches config weights within ±5%
  - Concentrated (3 cells): ambush_triggered → both ambush cells attack, patrol escalates
  - Dispersed (4 cells): both ambush cells engaged → sleeper activates (same eval cycle)
  - Fragmented (6 cells): sleeper chain — sleeper_1 activates, sets sleeper_1_activated,
    sleeper_2 activates in same eval cycle
  - Ambush cells emit no commands while dormant (ambush behavior → None)
  - Determinism: same seed produces the same bucket and same state sequence
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
    print(f"    {label:<68}  {status}{suffix}")


def _section(title: str) -> None:
    print()
    print(f"  {'─'*74}")
    print(f"  {title}")
    print(f"  {'─'*74}")


def _make_test_map():
    return TacticalMap(
        width=2000,
        height=2000,
        spine_nodes=[
            SpineNode(position=(1800, 1000), node_type="objective"),
            SpineNode(position=(1000, 1000), node_type="ambush_zone"),
            SpineNode(position=(200,  1000), node_type="enemy_spawn"),
        ],
    )


def _spawn_cells(store: UnitStore, n_forces: int, n_units: int = 2) -> dict[int, list[int]]:
    """Spawn n_units per force for factions 1..n_forces. Returns {faction: [uid]}."""
    result = {}
    for faction in range(1, n_forces + 1):
        uids = []
        for i in range(n_units):
            uid = store.spawn("Raider", faction, x=200 + i * 20, y=500 + faction * 100)
            uids.append(uid)
        result[faction] = uids
    return result


def _faction_map(script: dict) -> dict[str, int]:
    """Assign sequential faction IDs to force_ids in order."""
    return {f["force_id"]: i + 1 for i, f in enumerate(script["forces"])}


def _make_runner(script, tactical_map, bus=None, mission_start_tick=0, seed=42):
    if bus is None:
        bus = TriggerBus()
    rng = random.Random(seed)
    fmap = _faction_map(script)
    store = UnitStore()
    _spawn_cells(store, len(script["forces"]))
    runner = BehaviorRunner(
        script=script,
        tactical_map=tactical_map,
        bus=bus,
        rng=rng,
        faction_id=1,
        mission_start_tick=mission_start_tick,
        time_limit_ticks=0,
        force_faction_ids=fmap,
    )
    return runner, bus, store


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_fragmentation_distribution() -> None:
    _section("FRAGMENTATION DISTRIBUTION — 50 missions within ±5% of config weights")
    counts = {"concentrated": 0, "dispersed": 0, "fragmented": 0}
    cell_counts = {3: "concentrated", 4: "dispersed", 6: "fragmented"}

    # Use a master RNG to generate independent mission seeds. Sequential integer
    # seeds fed directly into Mersenne Twister produce correlated first draws,
    # biasing the sample. A master RNG gives proper independence while keeping
    # the test fully deterministic.
    master = random.Random(3)
    for _ in range(50):
        script = load_script("counterinsurgency", seed=master.randint(0, 2**31))
        n = len(script["forces"])
        bucket = cell_counts.get(n)
        if bucket:
            counts[bucket] += 1

    weights = config.COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS
    print(f"\n    {'Bucket':<14}  {'Expected':>10}  {'Got':>5}  {'Got%':>6}  {'Delta':>7}")
    print(f"    {'─'*14}  {'─'*10}  {'─'*5}  {'─'*6}  {'─'*7}")
    all_ok = True
    for bucket in ("concentrated", "dispersed", "fragmented"):
        expected_pct = weights[bucket]
        got = counts[bucket]
        got_pct = got / 50
        delta = abs(got_pct - expected_pct)
        ok = delta <= 0.05
        if not ok:
            all_ok = False
        marker = "✓" if ok else "✗"
        print(f"    {bucket:<14}  {expected_pct:>10.0%}  {got:>5}  {got_pct:>6.1%}  {delta:>+7.1%}  {marker}")

    _prow("All bucket counts within ±5% of config weights", all_ok)
    _prow("Total missions accounted for", sum(counts.values()) == 50,
          f"got {sum(counts.values())}")


def test_concentrated_scenario() -> None:
    _section("CONCENTRATED (3 cells) — ambush_triggered fires both ambushes, patrol escalates")
    script = load_script("counterinsurgency", seed=0)  # seed=0 → concentrated
    # Verify we got the right bucket
    if len(script["forces"]) != 3:
        # Find a seed that gives concentrated
        for s in range(200):
            script = load_script("counterinsurgency", seed=s)
            if len(script["forces"]) == 3:
                break
    _prow("Script is concentrated (3 forces)", len(script["forces"]) == 3,
          f"got {len(script['forces'])}")
    if len(script["forces"]) != 3:
        return

    tactical_map = _make_test_map()
    bus = TriggerBus()
    bus.set_flag("ambush_triggered")
    runner, bus, store = _make_runner(script, tactical_map, bus=bus)
    queue = CommandQueue()

    runner.step(0, store, queue)

    states = {rs.force_id: rs.current_state for rs in runner.runner_states}
    _prow("cell_a_ambush → attack_aggressive",
          states.get("cell_a_ambush") == "attack_aggressive",
          f"got {states.get('cell_a_ambush')!r}")
    _prow("cell_b_ambush → attack_aggressive",
          states.get("cell_b_ambush") == "attack_aggressive",
          f"got {states.get('cell_b_ambush')!r}")
    _prow("cell_c_patrol → attack_aggressive (via cell_a/b_engaged hook)",
          states.get("cell_c_patrol") == "attack_aggressive",
          f"got {states.get('cell_c_patrol')!r}")
    _prow("cell_a_engaged flag set", bus.get_flag("cell_a_engaged"))
    _prow("cell_b_engaged flag set", bus.get_flag("cell_b_engaged"))

    # Ambush cells emit no commands before triggering
    script2 = load_script("counterinsurgency", seed=0)
    if len(script2["forces"]) != 3:
        for s in range(200):
            script2 = load_script("counterinsurgency", seed=s)
            if len(script2["forces"]) == 3:
                break
    runner2, _, store2 = _make_runner(script2, tactical_map)
    queue2 = CommandQueue()
    runner2.step(0, store2, queue2)
    ambush_cmds = [e["command"] for e in runner2.eval_log
                   if e["force_id"] in ("cell_a_ambush", "cell_b_ambush")]
    _prow("Ambush cells emit None while dormant (no command)",
          all(c is None for c in ambush_cmds),
          f"got {ambush_cmds}")


def test_dispersed_scenario() -> None:
    _section("DISPERSED (4 cells) — both ambushes engaged → sleeper activates same cycle")
    # Find a dispersed seed
    script = None
    for s in range(200):
        sc = load_script("counterinsurgency", seed=s)
        if len(sc["forces"]) == 4:
            script = sc
            seed_used = s
            break
    _prow("Script is dispersed (4 forces)", script is not None and len(script["forces"]) == 4,
          f"none found" if script is None else f"seed={seed_used}")
    if script is None or len(script["forces"]) != 4:
        return

    tactical_map = _make_test_map()
    bus = TriggerBus()
    bus.set_flag("ambush_triggered")
    runner, bus, store = _make_runner(script, tactical_map, bus=bus, seed=seed_used)
    queue = CommandQueue()

    runner.step(0, store, queue)

    states = {rs.force_id: rs.current_state for rs in runner.runner_states}
    _prow("cell_a_ambush → attack_aggressive",
          states.get("cell_a_ambush") == "attack_aggressive",
          f"got {states.get('cell_a_ambush')!r}")
    _prow("cell_b_ambush → attack_aggressive",
          states.get("cell_b_ambush") == "attack_aggressive",
          f"got {states.get('cell_b_ambush')!r}")
    _prow("cell_a_engaged flag set",            bus.get_flag("cell_a_engaged"))
    _prow("cell_b_engaged flag set",            bus.get_flag("cell_b_engaged"))
    _prow("cell_d_sleeper → activate_aggressive (both engaged in same cycle)",
          states.get("cell_d_sleeper") == "activate_aggressive",
          f"got {states.get('cell_d_sleeper')!r}")


def test_fragmented_scenario() -> None:
    _section("FRAGMENTED (6 cells) — sleeper chain: sleeper_1 → sleeper_1_activated → sleeper_2")
    # Find a fragmented seed
    script = None
    for s in range(200):
        sc = load_script("counterinsurgency", seed=s)
        if len(sc["forces"]) == 6:
            script = sc
            seed_used = s
            break
    _prow("Script is fragmented (6 forces)", script is not None and len(script["forces"]) == 6,
          f"none found" if script is None else f"seed={seed_used}")
    if script is None or len(script["forces"]) != 6:
        return

    tactical_map = _make_test_map()
    bus = TriggerBus()
    bus.set_flag("ambush_triggered")
    runner, bus, store = _make_runner(script, tactical_map, bus=bus, seed=seed_used)
    queue = CommandQueue()

    runner.step(0, store, queue)

    states = {rs.force_id: rs.current_state for rs in runner.runner_states}
    _prow("All 3 ambush cells → attack_aggressive",
          all(states.get(f"cell_{c}_ambush") == "attack_aggressive"
              for c in ("a", "b", "c")),
          str({c: states.get(f"cell_{c}_ambush") for c in ("a", "b", "c")}))
    _prow("cell_a_engaged and cell_b_engaged set",
          bus.get_flag("cell_a_engaged") and bus.get_flag("cell_b_engaged"))
    _prow("cell_e_sleeper_1 → activate_aggressive (cell_a AND cell_b engaged)",
          states.get("cell_e_sleeper_1") == "activate_aggressive",
          f"got {states.get('cell_e_sleeper_1')!r}")
    _prow("sleeper_1_activated flag set by sleeper_1 on_enter",
          bus.get_flag("sleeper_1_activated"))
    _prow("cell_f_sleeper_2 → activate_aggressive (chain via sleeper_1_activated)",
          states.get("cell_f_sleeper_2") == "activate_aggressive",
          f"got {states.get('cell_f_sleeper_2')!r}")


def test_ambush_no_proximity_trigger() -> None:
    _section("AMBUSH PROXIMITY — cells stay dormant with no bus flag and no player nearby")
    # Use any bucket; ambush cells all start dormant
    script = load_script("counterinsurgency", seed=1)
    tactical_map = _make_test_map()
    runner, bus, store = _make_runner(script, tactical_map)
    queue = CommandQueue()

    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 3):
        runner.step(tick, store, queue)

    ambush_states = [rs.current_state for rs in runner.runner_states
                     if "ambush" in rs.force_id]
    _prow("All ambush cells stay in 'ambush' with no trigger",
          all(s == "ambush" for s in ambush_states),
          str(ambush_states))
    _prow("No bus flags set",
          not bus.get_flag("cell_a_engaged") and not bus.get_flag("cell_b_engaged"))


def test_determinism() -> None:
    _section("DETERMINISM — same seed → same bucket + same state sequence")
    def _run(seed):
        script = load_script("counterinsurgency", seed=seed)
        tactical_map = _make_test_map()
        bus = TriggerBus()
        bus.set_flag("ambush_triggered")
        runner, bus, store = _make_runner(script, tactical_map, bus=bus, seed=seed)
        queue = CommandQueue()
        INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
        for tick in range(INTERVAL * 4):
            runner.step(tick, store, queue)
        return (
            len(script["forces"]),
            [(e["force_id"], e["state_before"], e["state_after"]) for e in runner.eval_log],
        )

    r1 = _run(7)
    r2 = _run(7)
    r3 = _run(7)
    _prow("Same bucket across 3 runs",       r1[0] == r2[0] == r3[0], f"cells={r1[0]}")
    _prow("Same state sequence across 3 runs", r1[1] == r2[1] == r3[1])


# ── Pretty-print trace ─────────────────────────────────────────────────────────

def _print_sample_trace() -> None:
    _section("SAMPLE TRACE — fragmented bucket, sleeper chain")
    script = None
    for s in range(200):
        sc = load_script("counterinsurgency", seed=s)
        if len(sc["forces"]) == 6:
            script = sc
            seed_used = s
            break
    if script is None:
        print("  (no fragmented seed found in first 200)")
        return

    tactical_map = _make_test_map()
    bus = TriggerBus()
    bus.set_flag("ambush_triggered")
    runner, bus, store = _make_runner(script, tactical_map, bus=bus, seed=seed_used)
    queue = CommandQueue()
    INTERVAL = config.SCRIPT_EVAL_INTERVAL_TICKS
    for tick in range(INTERVAL * 3):
        runner.step(tick, store, queue)

    print(f"\n  {'Tick':>5}  {'Cell':<22}  {'Before':<20}  {'After':<20}  {'Cmd'}")
    print(f"  {'─'*5}  {'─'*22}  {'─'*20}  {'─'*20}  {'─'*12}")
    for e in runner.eval_log:
        print(
            f"  {e['tick']:>5}  {e['force_id']:<22}  {e['state_before']:<20}  "
            f"{e['state_after']:<20}  {e['command'] or 'none'}"
        )
    print(f"\n  Bus flags: cell_a={bus.get_flag('cell_a_engaged')}  "
          f"cell_b={bus.get_flag('cell_b_engaged')}  "
          f"cell_c={bus.get_flag('cell_c_engaged')}  "
          f"sleeper_1_activated={bus.get_flag('sleeper_1_activated')}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 74)
    print("  STAGE 7.5 CHECKPOINT G — Counterinsurgency Script")
    print("=" * 74)

    test_fragmentation_distribution()
    test_concentrated_scenario()
    test_dispersed_scenario()
    test_fragmented_scenario()
    test_ambush_no_proximity_trigger()
    test_determinism()
    _print_sample_trace()

    print()
    print("=" * 74)
    if _failures == 0:
        print(f"  {PASS}  All counterinsurgency tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 74)
    sys.exit(0 if _failures == 0 else 1)
