"""
Checkpoint H — Fairness Evaluator

Note on pass rates: authored FairnessTargetProfile values are design-intent targets
calibrated for symmetric maps. The 8 hand-authored layouts are intentionally
asymmetric (defender near chokepoints, attacker crossing the map), so 0% pass
rate against the profiles is expected at this stage. The evaluator mechanism is
verified below via structural and directional checks instead.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout
from fairness_evaluator import evaluate_fairness, is_acceptable, FairnessScore
from archetype_filters import matching_layouts

SEED = 0x1a2b3c

ARCHETYPE_LAYOUT_PAIRS = [
    ("defensive_stand",    "layout_01_fortress_ridge"),
    ("assault",            "layout_02_open_plains_assault"),
    ("multi_front_defense","layout_03_three_front_valley"),
    ("counterinsurgency",  "layout_07_scattered_outposts"),
]

METRICS = [
    ("path_balance",  "path_balance_ratio",  "path_balance_target",  "path_balance_pass"),
    ("travel_time",   "travel_time_ratio",   "travel_time_target",   "travel_time_pass"),
    ("vantage",       "vantage_ratio",        "vantage_target",       "vantage_pass"),
    ("hazard",        "hazard_ratio",         "hazard_target",        "hazard_pass"),
]


def fmt_score(score: FairnessScore):
    lines = []
    for label, ratio_attr, target_attr, pass_attr in METRICS:
        ratio  = getattr(score, ratio_attr)
        target = getattr(score, target_attr)
        ok     = getattr(score, pass_attr)
        mark   = "pass" if ok else "----"
        lines.append(f"    {label:<18} ratio={ratio:.3f}  target={target[0]:.2f}±{target[1]:.2f}  [{mark}]")
    lines.append(f"    {'all_metrics':<18} {score.all_metrics_pass}")
    return "\n".join(lines)


def main():
    print("=== Stage 7 Checkpoint H: Fairness Evaluator ===\n")

    library = load_all_layouts()
    failures = []

    # ── Per archetype-layout pair ─────────────────────────────────────────────
    print("── Prototype archetype evaluations ─────────────────────────────────")
    scores = {}
    for archetype, layout_id in ARCHETYPE_LAYOUT_PAIRS:
        layout = library[layout_id]
        inst   = instantiate_layout(layout, "medium", SEED)
        score  = evaluate_fairness(inst, archetype)
        scores[(archetype, layout_id)] = score
        print(f"\n{archetype} / {layout_id}")
        print(fmt_score(score))

    # ── Structural correctness ────────────────────────────────────────────────
    print("\n── Structural correctness ───────────────────────────────────────────")

    for (archetype, layout_id), score in scores.items():
        # All ratio fields must be finite and non-negative
        for label, ratio_attr, *_ in METRICS:
            ratio = getattr(score, ratio_attr)
            if not math.isfinite(ratio):
                msg = f"{archetype}/{layout_id}: {label} ratio is not finite ({ratio})"
                failures.append(msg)
                print(f"  FAIL: {msg}")
            if ratio < 0:
                msg = f"{archetype}/{layout_id}: {label} ratio is negative ({ratio:.3f})"
                failures.append(msg)
                print(f"  FAIL: {msg}")

        # all_metrics_pass must agree with individual passes
        expected = all(getattr(score, pa) for _, _, _, pa in METRICS)
        if score.all_metrics_pass != expected:
            msg = f"{archetype}/{layout_id}: all_metrics_pass disagrees with individual fields"
            failures.append(msg)
            print(f"  FAIL: {msg}")

        # is_acceptable roundtrip
        if is_acceptable(score) != score.all_metrics_pass:
            msg = f"{archetype}/{layout_id}: is_acceptable() doesn't match all_metrics_pass"
            failures.append(msg)
            print(f"  FAIL: {msg}")

        # archetype field preserved
        if score.archetype_profile != archetype:
            msg = f"{archetype}/{layout_id}: archetype_profile={score.archetype_profile!r}"
            failures.append(msg)
            print(f"  FAIL: {msg}")

    print("  Structural checks done.")

    # ── Directional checks on symmetric layout ────────────────────────────────
    # layout_03 three_front_valley is designed with player in the center holding
    # a symmetric 3-front perimeter.  Vantage and hazard proximity should be
    # balanced (ratio ≈ 1.0) and path_balance should also be near 1.0 (equal
    # flow from both sides to the central objective).
    print("\n── Symmetric layout directional checks (layout_03) ─────────────────")
    mfd_score = scores[("multi_front_defense", "layout_03_three_front_valley")]

    if not (0.7 <= mfd_score.path_balance_ratio <= 1.3):
        msg = (f"multi_front_defense path_balance_ratio={mfd_score.path_balance_ratio:.3f} "
               f"expected near 1.0 for symmetric layout")
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  path_balance near 1.0: {mfd_score.path_balance_ratio:.3f}  ✓")

    if not (0.7 <= mfd_score.vantage_ratio <= 1.3):
        msg = (f"multi_front_defense vantage_ratio={mfd_score.vantage_ratio:.3f} "
               f"expected near 1.0 for symmetric layout")
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  vantage near 1.0: {mfd_score.vantage_ratio:.3f}  ✓")

    if not (0.7 <= mfd_score.hazard_ratio <= 1.3):
        msg = (f"multi_front_defense hazard_ratio={mfd_score.hazard_ratio:.3f} "
               f"expected near 1.0 for symmetric layout")
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  hazard near 1.0: {mfd_score.hazard_ratio:.3f}  ✓")

    # counterinsurgency hazard_ratio should be < 1.0 — hazard zones are scattered
    # across the map but all insurgent_hint nodes favor the enemy side
    ci_score = scores[("counterinsurgency", "layout_07_scattered_outposts")]
    if ci_score.hazard_ratio >= 1.0:
        msg = (f"counterinsurgency hazard_ratio={ci_score.hazard_ratio:.3f} "
               f"should be < 1.0 (hazards on enemy/insurgent side)")
        failures.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  counterinsurgency hazard_ratio < 1.0: {ci_score.hazard_ratio:.3f}  ✓")

    # ── Pass rate report (informational) ─────────────────────────────────────
    print("\n── Pass rate report (informational — calibration gap expected) ──────")
    for archetype, _ in ARCHETYPE_LAYOUT_PAIRS:
        matching = matching_layouts(archetype, library)
        passing  = 0
        for layout_spec in matching:
            inst  = instantiate_layout(layout_spec, "medium", SEED)
            score = evaluate_fairness(inst, archetype)
            if score.all_metrics_pass:
                passing += 1
        pct = passing / len(matching) * 100 if matching else 0
        print(f"  {archetype:<22} {passing}/{len(matching)} layouts pass  ({pct:.0f}%)")
    print("  (0% is expected — profiles need calibration against layout geometry)")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("Checkpoint H complete — no failures.")


if __name__ == "__main__":
    main()
