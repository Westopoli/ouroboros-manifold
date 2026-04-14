import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from layout_library import load_all_layouts, get_layout, layouts_for_archetype
from collections import Counter


def main():
    print("=== Stage 7 Checkpoint A: Layout Library ===\n")

    layouts = load_all_layouts()
    print(f"Layouts loaded: {len(layouts)}")
    for lid, layout in layouts.items():
        print(f"  {lid}: '{layout.name}' [{layout.canvas_class}] tags={list(layout.tags)}")
    print()

    layout = get_layout("layout_01_fortress_ridge")
    print(f"Layout: {layout.name}")
    print(f"  Canvas class: {layout.canvas_class}")
    print(f"  Tags: {list(layout.tags)}")
    print(f"  Zones: {len(layout.zones)}")
    print(f"  Edges: {len(layout.edges)}")
    print(f"  Drift paths: {len(layout.drift_paths)}")
    print()

    zone_types = Counter(z.node_type for z in layout.zones)
    print("Zone breakdown by node_type:")
    for ntype, count in sorted(zone_types.items()):
        print(f"  {ntype}: {count}")
    print()

    edge_types = Counter(e.edge_type for e in layout.edges)
    print("Edge breakdown by edge_type:")
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype}: {count}")
    print()

    for archetype in ("assault", "defensive_stand", "counterinsurgency"):
        matching = layouts_for_archetype(archetype)
        print(f"layouts_for_archetype('{archetype}'): {[l.layout_id for l in matching]}")
    print()

    print("Validation status: PASS (load_all_layouts raises on failure)")
    print()

    viewer_json = os.path.join(os.path.dirname(__file__), "layout_library", "layout_01_fortress_ridge.json")
    print(f"Viewer launch command:")
    print(f"  python -m simulation.map_viewer {viewer_json}")


if __name__ == "__main__":
    main()
