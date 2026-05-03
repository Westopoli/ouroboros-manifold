import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from map_gen_contracts import GeneratorInput, RegionState
from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout
from fairness_evaluator import evaluate_fairness, is_acceptable
from archetype_filters import matching_layouts, ARCHETYPE_FILTERS

DEFAULT_N = 20


def _default_region_state():
    return RegionState(
        stability=50.0, capacity=0.5, economy=50.0,
        tension=50.0, military=50.0, population=50.0,
        region_id="diag_region", tier=1,
    )


def run_pass_rate_audit(n=DEFAULT_N):
    layout_lib = load_all_layouts()
    region_state = _default_region_state()
    results = {}

    for archetype in sorted(ARCHETYPE_FILTERS.keys()):
        compatible = matching_layouts(archetype, layout_lib)
        if not compatible:
            continue

        arch_results = {}
        for layout in compatible:
            canvas_size = config.ARCHETYPE_BASE_CANVAS.get(archetype, "medium")
            passes = 0
            fail_counts = {"path": 0, "travel": 0, "vantage": 0, "hazard": 0}
            sample_score = None

            for seed in range(1000, 1000 + n):
                inst = instantiate_layout(layout, canvas_size, seed)
                score = evaluate_fairness(inst, archetype)
                if is_acceptable(score):
                    passes += 1
                else:
                    if not score.path_balance_pass and not score.path_balance_skipped:
                        fail_counts["path"] += 1
                    if not score.travel_time_pass and not score.travel_time_skipped:
                        fail_counts["travel"] += 1
                    if not score.vantage_pass and not score.vantage_skipped:
                        fail_counts["vantage"] += 1
                    if not score.hazard_pass and not score.hazard_skipped:
                        fail_counts["hazard"] += 1
                if sample_score is None:
                    sample_score = score

            skips = []
            if sample_score and sample_score.vantage_skipped:
                skips.append("vantage")
            if sample_score and sample_score.hazard_skipped:
                skips.append("hazard")
            if sample_score and sample_score.path_balance_skipped:
                skips.append("path")
            if sample_score and sample_score.travel_time_skipped:
                skips.append("travel")

            arch_results[layout.layout_id] = {
                "passes": passes,
                "total": n,
                "fail_counts": fail_counts,
                "sample": sample_score,
                "skipped_metrics": skips,
            }

        results[archetype] = {
            "compatible_pool": [l.layout_id for l in compatible],
            "pool_size": len(compatible),
            "per_layout": arch_results,
        }

    return results


def print_report(results, n):
    total_pairs = 0
    total_passing = 0

    print(f"\n{'='*70}")
    print(f"  Fairness Pass-Rate Audit  (N={n} seeds per (layout, archetype) pair)")
    print(f"{'='*70}")

    for archetype, data in sorted(results.items()):
        print(f"\n  === {archetype} (pool: {data['pool_size']} layouts) ===")
        for lid, ld in sorted(data["per_layout"].items()):
            total_pairs += 1
            pass_rate = ld["passes"] / ld["total"]
            if ld["passes"] == ld["total"]:
                total_passing += 1
            fails = ld["total"] - ld["passes"]
            reasons = ""
            if fails > 0:
                parts = [f"{k}={v}" for k, v in ld["fail_counts"].items() if v > 0]
                reasons = f"  fails: {' '.join(parts)}"

            s = ld["sample"]
            skips = ld.get("skipped_metrics", [])
            skip_tag = f"  skipped: {' '.join(skips)}" if skips else ""
            print(f"    {lid}: {ld['passes']}/{ld['total']} pass ({pass_rate:.0%}){reasons}{skip_tag}")
            print(f"      ratios: path={s.path_balance_ratio:.2f}(t={s.path_balance_target}) "
                  f"travel={s.travel_time_ratio:.2f}(t={s.travel_time_target})")
            print(f"              vantage={s.vantage_ratio:.2f}(t={s.vantage_target}) "
                  f"hazard={s.hazard_ratio:.2f}(t={s.hazard_target})")

    agg_rate = total_passing / total_pairs if total_pairs else 0
    print(f"\n{'='*70}")
    print(f"  Aggregate: {total_passing}/{total_pairs} pairs with 100% pass rate "
          f"({agg_rate:.0%})")
    print(f"{'='*70}\n")
    return results


if __name__ == "__main__":
    n = DEFAULT_N
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--n" and i + 1 < len(sys.argv) - 1:
            n = int(sys.argv[i + 2])

    results = run_pass_rate_audit(n=n)
    print_report(results, n)
