#!/usr/bin/env python3
"""Stage 7.5 Checkpoint H — Ownership baselines + S7-5 delta integration.

Verifies:
  - 4 prototype archetypes use their authored baselines (not the 33/33/34 fallback)
  - 6 non-prototype archetypes still use the fallback
  - Delta math (map_generator._assign_reinforcement_ownership formula) layered on top
    of each prototype baseline produces sensible ownership distributions across 20
    varied region states (high/low military × high/low tension)
  - No clamp violations or NaN values in any output
  - Player share never < 0.05 or > 0.95 across all inputs
"""
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config
from archetype_filters import get_baseline_ownership, BASELINE_OWNERSHIP

PASS = "✓"
FAIL = "✗ FAIL"
_failures = 0

_PROTOTYPE_ARCHETYPES = ("defensive_stand", "assault", "multi_front_defense", "counterinsurgency")
_NON_PROTOTYPE_ARCHETYPES = ("siege_breaking", "reconquest", "suppression",
                              "evacuation", "raid", "rear_guard")


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


def _apply_delta(base_p: float, base_n: float, base_e: float,
                 military: float, tension: float) -> tuple[float, float, float]:
    """Mirror of map_generator._assign_reinforcement_ownership delta math.
    military and tension are 0–100 region field values.
    """
    player_shift  = config.OWNERSHIP_MILITARY_COEFF * (military - 50) / 50
    neutral_shift = config.OWNERSHIP_TENSION_COEFF  * (tension  - 50) / 50

    p = base_p + player_shift - neutral_shift / 2
    e = base_e - player_shift - neutral_shift / 2
    n = base_n + neutral_shift

    p = max(0.0, min(1.0, p))
    e = max(0.0, min(1.0, e))
    n = max(0.0, min(1.0, n))
    total = p + e + n
    if total > 0:
        p, e, n = p / total, e / total, n / total
    else:
        p, e, n = 0.33, 0.34, 0.33

    return p, n, e


def _region_states():
    """20 varied region state pairs (military, tension)."""
    states = []
    for military in (5, 25, 50, 75, 95):
        for tension in (5, 25, 75, 95):
            states.append((military, tension))
    return states


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_prototype_baselines_authored() -> None:
    _section("PROTOTYPE BASELINES — 4 archetypes have authored baselines")
    expected = {
        "defensive_stand":    (0.50, 0.20, 0.30),
        "assault":            (0.30, 0.20, 0.50),
        "multi_front_defense": (0.50, 0.20, 0.30),
        "counterinsurgency":  (0.30, 0.50, 0.20),
    }
    for archetype, (ep, en, ee) in expected.items():
        got = get_baseline_ownership(archetype)
        _prow(f"{archetype}: baseline matches spec",
              got == (ep, en, ee),
              f"got {got}, expected ({ep}, {en}, {ee})")
        _prow(f"{archetype}: sums to 1.0",
              abs(sum(got) - 1.0) < 1e-9,
              f"sum={sum(got)}")


def test_non_prototype_fallback() -> None:
    _section("NON-PROTOTYPE FALLBACK — 6 archetypes use config.SCRIPT_FALLBACK_OWNERSHIP")
    fallback = config.SCRIPT_FALLBACK_OWNERSHIP
    for archetype in _NON_PROTOTYPE_ARCHETYPES:
        got = get_baseline_ownership(archetype)
        _prow(f"{archetype}: uses fallback",
              got == fallback,
              f"got {got!r}")
    _prow("Fallback sums to 1.0",
          abs(sum(fallback) - 1.0) < 1e-9,
          f"sum={sum(fallback)}")


def test_delta_math_sensible_outputs() -> None:
    _section("DELTA MATH — layered on prototypes produces sensible distributions (20 region states)")
    states = _region_states()

    for archetype in _PROTOTYPE_ARCHETYPES:
        base_p, base_n, base_e = get_baseline_ownership(archetype)
        violations = []
        for military, tension in states:
            p, n, e = _apply_delta(base_p, base_n, base_e, military, tension)
            total = p + n + e
            if p < 0.05 or p > 0.95:
                violations.append(f"player={p:.3f} at mil={military} ten={tension}")
            if e < 0.0 or e > 1.0:
                violations.append(f"enemy={e:.3f} at mil={military} ten={tension}")
            if n < 0.0 or n > 1.0:
                violations.append(f"neutral={n:.3f} at mil={military} ten={tension}")
            if abs(total - 1.0) > 1e-6:
                violations.append(f"sum={total:.6f} at mil={military} ten={tension}")
            if any(v != v for v in (p, n, e)):  # NaN check
                violations.append(f"NaN at mil={military} ten={tension}")

        _prow(f"{archetype}: no violations across 20 region states",
              len(violations) == 0,
              violations[0] if violations else "")


def test_prototype_vs_fallback_differ() -> None:
    _section("BASELINE DIFFERENTIATION — prototype baselines differ from fallback")
    fallback = config.SCRIPT_FALLBACK_OWNERSHIP
    for archetype in _PROTOTYPE_ARCHETYPES:
        got = get_baseline_ownership(archetype)
        _prow(f"{archetype}: baseline differs from 33/33/34 fallback",
              got != fallback,
              f"got {got!r}")


def test_delta_shifts_in_right_direction() -> None:
    _section("DELTA DIRECTION — high military → more player, high tension → more neutral")
    for archetype in _PROTOTYPE_ARCHETYPES:
        base_p, base_n, base_e = get_baseline_ownership(archetype)

        # High military (95), neutral tension (50) → player share should rise vs baseline
        p_hi_mil, _, _ = _apply_delta(base_p, base_n, base_e, 95, 50)
        p_lo_mil, _, _ = _apply_delta(base_p, base_n, base_e, 5, 50)
        _prow(f"{archetype}: high military → more player than low military",
              p_hi_mil > p_lo_mil,
              f"hi={p_hi_mil:.3f} lo={p_lo_mil:.3f}")

        # High tension (95), neutral military (50) → neutral share should rise vs baseline
        _, n_hi_ten, _ = _apply_delta(base_p, base_n, base_e, 50, 95)
        _, n_lo_ten, _ = _apply_delta(base_p, base_n, base_e, 50, 5)
        _prow(f"{archetype}: high tension → more neutral than low tension",
              n_hi_ten > n_lo_ten,
              f"hi={n_hi_ten:.3f} lo={n_lo_ten:.3f}")


# ── Pretty-print baseline table ────────────────────────────────────────────────

def _print_baseline_table() -> None:
    _section("BASELINE TABLE — all archetypes")
    fallback = config.SCRIPT_FALLBACK_OWNERSHIP
    print(f"\n  {'Archetype':<22}  {'Player':>8}  {'Neutral':>8}  {'Enemy':>8}  {'Source'}")
    print(f"  {'─'*22}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*12}")
    for arch in _PROTOTYPE_ARCHETYPES:
        p, n, e = get_baseline_ownership(arch)
        print(f"  {arch:<22}  {p:>8.0%}  {n:>8.0%}  {e:>8.0%}  authored")
    for arch in _NON_PROTOTYPE_ARCHETYPES:
        p, n, e = get_baseline_ownership(arch)
        print(f"  {arch:<22}  {p:>8.0%}  {n:>8.0%}  {e:>8.0%}  fallback")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 74)
    print("  STAGE 7.5 CHECKPOINT H — Ownership Baselines")
    print("=" * 74)

    test_prototype_baselines_authored()
    test_non_prototype_fallback()
    test_delta_math_sensible_outputs()
    test_prototype_vs_fallback_differ()
    test_delta_shifts_in_right_direction()
    _print_baseline_table()

    print()
    print("=" * 74)
    if _failures == 0:
        print(f"  {PASS}  All ownership baseline tests passed.")
    else:
        print(f"  {FAIL}  {_failures} test(s) failed.")
    print("=" * 74)
    sys.exit(0 if _failures == 0 else 1)
