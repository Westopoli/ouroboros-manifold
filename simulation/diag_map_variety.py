import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from map_gen_contracts import GeneratorInput, RegionState
from map_generator import generate_map
from layout_library import load_all_layouts
from archetype_filters import matching_layouts, ARCHETYPE_FILTERS

LAYOUT_DIVERSITY_MIN_UNIQUE = 2
DEFAULT_N = 10
DEFAULT_TICK = 1000


def _default_region_state():
    return RegionState(
        stability=50.0, capacity=0.5, economy=50.0,
        tension=50.0, military=50.0, population=50.0,
        region_id="diag_region", tier=1,
    )


def run_variety_check(n=DEFAULT_N, fixed_seed=None):
    layout_lib = load_all_layouts()
    region_state = _default_region_state()
    results = {}

    for archetype in sorted(ARCHETYPE_FILTERS.keys()):
        compatible = matching_layouts(archetype, layout_lib)
        if not compatible:
            print(f"  {archetype}: SKIP (no compatible layouts)")
            continue

        pool_size = len(compatible)
        layout_counts = {}

        for i in range(n):
            if fixed_seed is not None:
                seed = fixed_seed
            else:
                seed = random.randint(0, 2**31 - 1)

            canvas_size = config.ARCHETYPE_BASE_CANVAS.get(archetype, "medium")
            gen_input = GeneratorInput(
                archetype=archetype, region_state=region_state,
                canvas_size=canvas_size, seed=seed,
            )
            result = generate_map(gen_input, layout_lib)
            lid = result.chosen_layout_id
            layout_counts[lid] = layout_counts.get(lid, 0) + 1

        unique = len(layout_counts)
        ratio = unique / pool_size
        results[archetype] = {
            "pool_size": pool_size,
            "unique_layouts": unique,
            "ratio": ratio,
            "histogram": layout_counts,
        }

    return results


def print_report(results, n):
    print(f"\n{'='*60}")
    print(f"  Map Variety Report  (N={n} missions per archetype)")
    print(f"{'='*60}\n")

    all_pass = True
    for archetype, data in sorted(results.items()):
        unique = data["unique_layouts"]
        pool = data["pool_size"]
        exempt = pool <= 2
        status = "PASS" if unique >= LAYOUT_DIVERSITY_MIN_UNIQUE or exempt else "FAIL"
        if status == "FAIL":
            all_pass = False
        tag = " (exempt: pool≤2)" if exempt and unique < LAYOUT_DIVERSITY_MIN_UNIQUE else ""
        print(f"  {archetype}:")
        print(f"    pool_size={pool}  unique={unique}  "
              f"ratio={data['ratio']:.2f}  [{status}]{tag}")
        for lid, count in sorted(data["histogram"].items()):
            print(f"      {lid}: {count}/{n}")
    print()
    print(f"  Aggregate: {'PASS' if all_pass else 'FAIL'}  "
          f"(min_unique={LAYOUT_DIVERSITY_MIN_UNIQUE}, pool≤2 exempt)")
    print()
    return all_pass


if __name__ == "__main__":
    n = DEFAULT_N
    fixed_seed = DEFAULT_TICK

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--n" and i + 1 < len(sys.argv) - 1:
            n = int(sys.argv[i + 2])
        if arg == "--seed" and i + 1 < len(sys.argv) - 1:
            fixed_seed = int(sys.argv[i + 2])
        if arg == "--random":
            fixed_seed = None

    results = run_variety_check(n=n, fixed_seed=fixed_seed)
    passed = print_report(results, n)
    sys.exit(0 if passed else 1)
