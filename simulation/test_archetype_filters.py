import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from layout_library import load_all_layouts
from archetype_filters import (
    ARCHETYPE_FILTERS, FAIRNESS_PROFILES, evaluate_filter,
    matching_layouts, get_fairness_profile,
)
from map_gen_contracts import ZoneSpec, EdgeSpec, LayoutSpec


# ── Pathological test layouts ─────────────────────────────────────────────────

def _make_layout(zones, edges, layout_id="test"):
    return LayoutSpec(
        layout_id=layout_id,
        name=layout_id,
        canvas_class="medium",
        zones=tuple(zones),
        edges=tuple(edges),
        tags=(),
        drift_paths=(),
    )

def _z(zid, ntype, props=None):
    return ZoneSpec(zone_id=zid, position_ratio=(0.5, 0.5),
                    node_type=ntype, properties=props or {})

def _e(frm, to, etype="path"):
    return EdgeSpec(from_zone=frm, to_zone=to, edge_type=etype)


PATHOLOGICAL = {
    "no_chokepoints": _make_layout(
        [_z("s","staging"), _z("sp","spawn_point"), _z("o","objective"),
         _z("t1","transit"), _z("t2","transit")],
        [_e("s","t1"), _e("t1","t2"), _e("t2","o"), _e("sp","o"),
         _e("s","t2","flank"), _e("s","t2","flank")],
        "no_chokepoints",
    ),
    "no_flank_edges": _make_layout(
        [_z("s","staging"), _z("sp","spawn_point"), _z("o","objective"),
         _z("c","chokepoint")],
        [_e("s","c"), _e("c","o"), _e("sp","o"),
         _e("s","o"), _e("s","c"), _e("s","o")],
        "no_flank_edges",
    ),
    "no_hazard_zones": _make_layout(
        [_z("s","staging"), _z("sp","spawn_point"), _z("o","objective"),
         _z("c","chokepoint")],
        [_e("s","c"), _e("c","o"), _e("sp","o"),
         _e("s","o"), _e("s","c"), _e("s","o")],
        "no_hazard_zones",
    ),
    "too_few_chokepoints_for_multifront": _make_layout(
        [_z("s","staging"), _z("sp","spawn_point"), _z("o","objective"),
         _z("c1","chokepoint"), _z("c2","chokepoint")],
        [_e("s","c1"), _e("c1","o"), _e("s","c2"), _e("c2","o"),
         _e("sp","o"), _e("s","o"), _e("s","o"), _e("s","o"), _e("s","o"), _e("s","o")],
        "two_chokepoints",
    ),
    "minimal_valid": _make_layout(
        [_z("s","staging"), _z("sp","spawn_point"), _z("o","objective"),
         _z("c","chokepoint"), _z("h1","hazard_zone_anchor"), _z("h2","hazard_zone_anchor")],
        [_e("s","c"), _e("c","o"), _e("sp","o"),
         _e("s","o","flank"), _e("s","o"), _e("s","o"), _e("s","o")],
        "minimal_valid",
    ),
}

PROTOTYPE_ARCHETYPES = ["defensive_stand", "assault", "multi_front_defense", "counterinsurgency"]
STUB_ARCHETYPES      = ["siege_breaking", "reconquest", "suppression", "evacuation", "raid", "rear_guard"]


def main():
    print("=== Stage 7 Checkpoint B: Archetype Compatibility Filters ===\n")

    # ── Filter rule summary ──
    print("Filter rules per archetype:")
    for arch in PROTOTYPE_ARCHETYPES:
        print(f"\n  [{arch}] (prototype)")
        _print_filter(ARCHETYPE_FILTERS[arch], indent=4)
    for arch in STUB_ARCHETYPES:
        print(f"\n  [{arch}] (stub — refined in Stage 7.5)")
        _print_filter(ARCHETYPE_FILTERS[arch], indent=4)

    print()

    # ── Fairness profiles ──
    print("Fairness target profiles (prototype archetypes):")
    for arch in PROTOTYPE_ARCHETYPES:
        p = get_fairness_profile(arch)
        print(f"  {arch}:")
        print(f"    path_balance={p.path_balance}  travel_time={p.travel_time_balance}"
              f"  vantage={p.vantage_balance}  hazard={p.hazard_balance}")
    print()

    # ── Sample layout evaluation ──
    library = load_all_layouts()
    sample = library["layout_01_fortress_ridge"]
    print(f"Evaluation on sample layout: {sample.layout_id}\n")
    print(f"  {'archetype':<28}  {'pass?':<6}  note")
    print(f"  {'-'*28}  {'-'*6}  ----")
    for arch in list(PROTOTYPE_ARCHETYPES) + STUB_ARCHETYPES:
        result = evaluate_filter(ARCHETYPE_FILTERS[arch], sample)
        tag    = "PASS" if result else "fail"
        kind   = "prototype" if arch in PROTOTYPE_ARCHETYPES else "stub"
        print(f"  {arch:<28}  {tag:<6}  ({kind})")

    print()

    # ── Pathological rejection table ──
    print("Pathological layout rejection table:")
    header_archs = PROTOTYPE_ARCHETYPES
    col_w = 14
    header = f"  {'layout':<32}  " + "  ".join(f"{a[:col_w]:<{col_w}}" for a in header_archs)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for name, layout in PATHOLOGICAL.items():
        results = {a: evaluate_filter(ARCHETYPE_FILTERS[a], layout) for a in header_archs}
        row = f"  {name:<32}  " + "  ".join(
            f"{'PASS' if results[a] else 'FAIL':<{col_w}}" for a in header_archs
        )
        print(row)

    print()
    print("Expected rejections:")
    print("  no_chokepoints                → defensive_stand FAIL, assault FAIL, multi_front_defense FAIL")
    print("  no_flank_edges                → assault FAIL")
    print("  no_hazard_zones               → counterinsurgency FAIL (only 0 hazard zones)")
    print("  too_few_chokepoints_for_multi → multi_front_defense FAIL (2 < 3 required)")


def _print_filter(f, indent=0):
    pad = " " * indent
    t = f["type"]
    if t == "all_of":
        print(f"{pad}all_of:")
        for sub in f["filters"]:
            _print_filter(sub, indent + 2)
    elif t == "any_of":
        print(f"{pad}any_of:")
        for sub in f["filters"]:
            _print_filter(sub, indent + 2)
    elif t == "not":
        print(f"{pad}not:")
        _print_filter(f["filter"], indent + 2)
    elif t == "count_zone_type":
        print(f"{pad}count(zone:{f['node_type']}) {f['op']} {f['n']}")
    elif t == "count_edge_type":
        print(f"{pad}count(edge:{f['edge_type']}) {f['op']} {f['n']}")
    elif t == "has_zone_with_property":
        val = f.get("value", "*")
        print(f"{pad}has_zone_with_property({f['key']}={val})")
    elif t == "layer_accessibility_variety":
        print(f"{pad}layer_accessibility_variety {f['op']} {f['n']}")
    else:
        print(f"{pad}{f}")


if __name__ == "__main__":
    main()
