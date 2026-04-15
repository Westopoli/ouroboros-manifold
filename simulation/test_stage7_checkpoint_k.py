"""
Checkpoint K — Production Timer + Composition Reactivity

Tests:
  1. Production timing — each unit type spawns in expected ticks (power-rating formula)
  2. Composition reactivity:
       40/35/25  → no trigger (no category ≥ 70%)
       70/20/10  → trigger at threshold; 15% shift toward counter
       75/15/10  → above threshold; same shift magnitude
       Verify: shift direction is toward counter category
       Verify: < 70% produces no change
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import types
import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_map import TacticalMap
from reinforcement import ReinforcementStructure, step_reinforcement, select_enemy_unit_type

PLAYER  = 0
ENEMY   = 1
DT      = config.TACTICAL_TICK_DURATION

OUT_DIR = os.path.join(os.path.dirname(__file__), "tuning_output", "stage7", "checkpoint_k")


def _make_engine(owner_faction, unit_type):
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    engine = types.SimpleNamespace(map=tmap, store=store, reinforcement_structures=[])
    structure = ReinforcementStructure(
        structure_uid=1,
        position=(2000.0, 2000.0),
        layer=0,
        hp=float(config.REINFORCEMENT_STRUCTURE_HP),
        max_hp=float(config.REINFORCEMENT_STRUCTURE_HP),
        owner_faction=owner_faction,
        capture_progress=0.0,
        production_timer_sec=0.0,
        production_target_unit_type=unit_type,
        capture_radius=config.REINFORCEMENT_CAPTURE_RADIUS,
    )
    engine.reinforcement_structures = [structure]
    return engine, structure


# ── Section 1: Production timing ─────────────────────────────────────────────

def run_production_timing():
    print("\n── Section 1: Production timing ────────────────────────────────────────")
    print(f"  {'Unit':<14} {'Power':>6} {'Expected(s)':>12} {'Expected(ticks)':>16} "
          f"{'Actual(ticks)':>14} {'Match':>6}")
    print(f"  {'-'*14} {'-'*6} {'-'*12} {'-'*16} {'-'*14} {'-'*6}")

    failures = []
    for unit_type in config.UNIT_POWER_RATINGS:
        engine, structure = _make_engine(ENEMY, unit_type)
        power    = config.UNIT_POWER_RATINGS[unit_type]
        expected_sec   = config.BASE_PRODUCTION_TIME_SEC * (power / config.POWER_NORMALIZATION)
        expected_ticks = expected_sec / DT

        before_count = engine.store.count
        spawn_tick   = None
        for t in range(int(expected_ticks) + 5):
            step_reinforcement(engine, DT)
            if engine.store.count > before_count:
                spawn_tick = t + 1
                break

        ok = spawn_tick is not None and abs(spawn_tick - expected_ticks) <= 1
        mark = "✓" if ok else "✗"
        print(f"  {unit_type:<14} {power:>6} {expected_sec:>12.1f} {expected_ticks:>16.1f} "
              f"{spawn_tick if spawn_tick else '—':>14} {mark:>6}")

        if not ok:
            failures.append(
                f"{unit_type}: expected spawn at tick {expected_ticks:.1f}, got {spawn_tick}"
            )
        else:
            # Verify unit is at structure position with correct faction
            uid = engine.store.count - 1
            assert engine.store.faction[uid] == ENEMY, \
                f"FAIL {unit_type}: spawned unit has wrong faction"
            assert engine.store.alive[uid], \
                f"FAIL {unit_type}: spawned unit not alive"
            ux = engine.store.data[uid, FIELD_X]
            uy = engine.store.data[uid, FIELD_Y]
            assert (ux, uy) == (2000.0, 2000.0), \
                f"FAIL {unit_type}: spawned at wrong position ({ux},{uy})"

    return failures


# ── Section 2: Composition reactivity ────────────────────────────────────────

# Counter mapping matches reinforcement.py _COUNTER
COUNTER = {"Strike": "Line", "Line": "Siege", "Siege": "Strike"}


def _check_skew(label, player_comp, expect_trigger, dominant_cat=None):
    base_target = {"Strike": 0.40, "Line": 0.35, "Siege": 0.25}
    current_comp = {"Strike": 0.33, "Line": 0.33, "Siege": 0.34}

    result = select_enemy_unit_type(base_target, current_comp, player_comp)

    total = sum(result.values())
    assert abs(total - 1.0) < 1e-9, f"FAIL {label}: result doesn't sum to 1.0 ({total})"

    if not expect_trigger:
        assert result == base_target or all(
            abs(result.get(k, 0) - base_target[k]) < 1e-9 for k in base_target
        ), f"FAIL {label}: expected no change but result differs from base_target"
        print(f"  {label}: no trigger  ✓  "
              f"Strike={result.get('Strike',0):.3f}  "
              f"Line={result.get('Line',0):.3f}  "
              f"Siege={result.get('Siege',0):.3f}")
        return []

    # Triggered: verify counter_cat increased
    counter_cat = COUNTER[dominant_cat]
    pre  = base_target.get(counter_cat, 0.0)
    post = result.get(counter_cat, 0.0)
    shift = post - pre

    # After renormalization the net shift may be slightly less than 0.15; allow ±0.02
    ok_direction = post > pre
    ok_magnitude = abs(shift - config.COMPOSITION_SHIFT_MAGNITUDE) < 0.02

    print(f"  {label}: triggered  "
          f"dominant={dominant_cat}  counter={counter_cat}  "
          f"pre={pre:.3f}  post={post:.3f}  shift={shift:+.3f}  "
          f"direction={'✓' if ok_direction else '✗'}  "
          f"magnitude={'✓' if ok_magnitude else '✗'}")

    failures = []
    if not ok_direction:
        failures.append(f"{label}: counter_cat {counter_cat} did not increase "
                        f"(pre={pre:.3f} post={post:.3f})")
    if not ok_magnitude:
        failures.append(f"{label}: shift magnitude {shift:.3f} not near "
                        f"{config.COMPOSITION_SHIFT_MAGNITUDE}")
    return failures


def run_composition_reactivity():
    print("\n── Section 2: Composition reactivity ───────────────────────────────────")
    print(f"  Base target: Strike=0.40  Line=0.35  Siege=0.25")
    print(f"  Skew threshold: {config.COMPOSITION_SKEW_THRESHOLD}  "
          f"Shift magnitude: {config.COMPOSITION_SHIFT_MAGNITUDE}")
    print()

    failures = []

    # No trigger: max is 40%, well below 70%
    failures += _check_skew(
        "40/35/25 (no trigger)",
        player_comp={"Strike": 0.40, "Line": 0.35, "Siege": 0.25},
        expect_trigger=False,
    )

    # Trigger at threshold: Strike exactly 70%
    failures += _check_skew(
        "70/20/10 Strike dominant",
        player_comp={"Strike": 0.70, "Line": 0.20, "Siege": 0.10},
        expect_trigger=True,
        dominant_cat="Strike",
    )

    # Above threshold: Strike 75%
    failures += _check_skew(
        "75/15/10 Strike dominant",
        player_comp={"Strike": 0.75, "Line": 0.15, "Siege": 0.10},
        expect_trigger=True,
        dominant_cat="Strike",
    )

    # Line dominant
    failures += _check_skew(
        "70/20/10 Line dominant",
        player_comp={"Strike": 0.20, "Line": 0.70, "Siege": 0.10},
        expect_trigger=True,
        dominant_cat="Line",
    )

    # Siege dominant
    failures += _check_skew(
        "70/20/10 Siege dominant",
        player_comp={"Strike": 0.10, "Line": 0.20, "Siege": 0.70},
        expect_trigger=True,
        dominant_cat="Siege",
    )

    # Just under threshold: 69% should not trigger
    failures += _check_skew(
        "69/21/10 (no trigger)",
        player_comp={"Strike": 0.69, "Line": 0.21, "Siege": 0.10},
        expect_trigger=False,
    )

    return failures


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    all_failures = []

    print("Checkpoint K — Production + Composition Reactivity")
    print("=" * 60)

    all_failures += run_production_timing()
    all_failures += run_composition_reactivity()

    if all_failures:
        print(f"\n{len(all_failures)} FAILURE(S):")
        for f in all_failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nCheckpoint K complete — no failures.")


if __name__ == "__main__":
    main()
