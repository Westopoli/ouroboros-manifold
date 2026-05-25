"""
A3 Option B verification — boot each archetype's map generator and report:
  - which layout was picked (and whether any compatible layouts exist)
  - number + types of gradient sources emitted
  - cover_density emission count + (x, y, source_origin_node_type) tuples
  - bounding box of cover placement vs. canvas

Usage: python3 simulation/verify_a3_coverage.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from layout_library import load_all_layouts
from archetype_filters import matching_layouts, ARCHETYPE_FILTERS
from map_generator import generate_map
from map_gen_contracts import GeneratorInput, RegionState


def _rs():
    return RegionState(
        stability=0.5, capacity=50.0, economy=50.0, tension=50.0,
        military=50.0, population=50.0, region_id="verify", tier=0,
    )


CANONICAL_TEN = [
    "defensive_stand", "siege_breaking", "reconquest", "assault",
    "suppression", "multi_front_defense", "interception", "evacuation",
    "containment", "counterinsurgency",
]


def _node_pos_by_id(inst_nodes, source):
    # GradientSource has 'position'; we look up which spine node it originated
    # from by matching position. Two nodes at the same position is unusual but
    # we just return the first match.
    for n in inst_nodes:
        if n.position == source.position:
            return n.node_type
    return "unknown"


def verify(archetype: str, library: dict) -> dict:
    compatible = matching_layouts(archetype, library)
    if not compatible:
        return {
            "archetype": archetype,
            "compatible_layouts": [],
            "chosen_layout_id": None,
            "error": "no_compatible_layouts",
            "cover_sources": [],
            "bbox": None,
        }

    gi = GeneratorInput(archetype=archetype, region_state=_rs(), canvas_size="medium", seed=42)
    try:
        result = generate_map(gi, library)
    except Exception as exc:
        return {
            "archetype": archetype,
            "compatible_layouts": [l.layout_id for l in compatible],
            "chosen_layout_id": None,
            "error": f"{type(exc).__name__}: {exc}",
            "cover_sources": [],
            "bbox": None,
        }

    tm = result.tactical_map
    cover_sources = [s for s in tm.gradient_sources if s.property_type == "cover_density"]

    tagged = []
    for s in cover_sources:
        nt = _node_pos_by_id(tm.spine_nodes, s)
        tagged.append((int(s.position[0]), int(s.position[1]), nt, round(s.radius, 1), round(s.intensity, 2)))

    if cover_sources:
        xs = [s.position[0] for s in cover_sources]
        ys = [s.position[1] for s in cover_sources]
        bbox = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
    else:
        bbox = None

    by_type = {}
    for s in tm.gradient_sources:
        by_type[s.property_type] = by_type.get(s.property_type, 0) + 1

    return {
        "archetype": archetype,
        "compatible_layouts": [l.layout_id for l in compatible],
        "chosen_layout_id": result.chosen_layout_id,
        "canvas": (tm.width, tm.height),
        "all_gradient_counts": by_type,
        "cover_sources": tagged,
        "bbox": bbox,
        "error": None,
    }


def main():
    library = load_all_layouts()

    print("=" * 78)
    print("A3 Option B coverage verification — 10 canonical archetypes")
    print("=" * 78)

    results = []
    for arch in CANONICAL_TEN:
        r = verify(arch, library)
        results.append(r)
        print()
        print(f"--- {arch} ---")
        print(f"  compatible_layouts: {r['compatible_layouts']}")
        if r["error"]:
            print(f"  ERROR: {r['error']}")
            continue
        print(f"  chosen_layout_id:   {r['chosen_layout_id']}")
        print(f"  canvas:             {r['canvas']}")
        print(f"  gradient_counts:    {r['all_gradient_counts']}")
        print(f"  cover_sources ({len(r['cover_sources'])}):")
        for (x, y, nt, rad, intensity) in r["cover_sources"]:
            print(f"    ({x:5d}, {y:5d}) origin={nt:<22} radius={rad:6.1f} intensity={intensity:.2f}")
        if r["bbox"]:
            x0, y0, x1, y1 = r["bbox"]
            print(f"  cover bbox:         ({x0}, {y0}) → ({x1}, {y1})  span=({x1-x0}, {y1-y0})")
        else:
            print("  cover bbox:         NONE")

    print()
    print("=" * 78)
    print("Summary table")
    print("=" * 78)
    print(f"{'archetype':<22} {'gen?':<5} {'cover#':<7} {'bbox span':<22} {'layouts'}")
    for r in results:
        ok = "Y" if r["error"] is None else "N"
        n_cov = len(r["cover_sources"])
        bbox_span = ""
        if r["bbox"]:
            x0, y0, x1, y1 = r["bbox"]
            bbox_span = f"({x1-x0}x{y1-y0})"
        layout_count = len(r["compatible_layouts"])
        print(f"{r['archetype']:<22} {ok:<5} {n_cov:<7} {bbox_span:<22} {layout_count} compatible")


if __name__ == "__main__":
    main()
