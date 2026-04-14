import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_gen_contracts import ZoneSpec, EdgeSpec, DriftPathSpec, LayoutSpec

_LIBRARY_DIR = os.path.join(os.path.dirname(__file__), "layout_library")
_registry: dict[str, LayoutSpec] = {}


def _parse_layout(data: dict) -> LayoutSpec:
    zones = tuple(
        ZoneSpec(
            zone_id=z["zone_id"],
            position_ratio=tuple(z["position_ratio"]),
            node_type=z["node_type"],
            properties=z.get("properties", {}),
        )
        for z in data["zones"]
    )
    edges = tuple(
        EdgeSpec(
            from_zone=e["from_zone"],
            to_zone=e["to_zone"],
            edge_type=e["edge_type"],
        )
        for e in data["edges"]
    )
    drift_paths = tuple(
        DriftPathSpec(
            zone_id=d["zone_id"],
            waypoints=tuple(tuple(wp) for wp in d["waypoints"]),
            period_ticks=d["period_ticks"],
            mode=d["mode"],
        )
        for d in data.get("drift_paths", [])
    )
    return LayoutSpec(
        layout_id=data["layout_id"],
        name=data["name"],
        canvas_class=data["canvas_class"],
        zones=zones,
        edges=edges,
        tags=tuple(data.get("tags", [])),
        drift_paths=drift_paths,
    )


def _validate(layout: LayoutSpec) -> list[str]:
    errors = []
    zone_ids = {z.zone_id for z in layout.zones}

    seen_ids = set()
    for z in layout.zones:
        if z.zone_id in seen_ids:
            errors.append(f"duplicate zone_id: {z.zone_id}")
        seen_ids.add(z.zone_id)
        x, y = z.position_ratio
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            errors.append(f"zone {z.zone_id} position_ratio out of [0,1]: {z.position_ratio}")

    for e in layout.edges:
        if e.from_zone not in zone_ids:
            errors.append(f"edge references unknown from_zone: {e.from_zone}")
        if e.to_zone not in zone_ids:
            errors.append(f"edge references unknown to_zone: {e.to_zone}")

    for dp in layout.drift_paths:
        if dp.zone_id not in zone_ids:
            errors.append(f"drift_path references unknown zone_id: {dp.zone_id}")

    return errors


def load_all_layouts() -> dict[str, LayoutSpec]:
    global _registry
    _registry = {}
    for fname in sorted(os.listdir(_LIBRARY_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(_LIBRARY_DIR, fname)
        with open(path) as f:
            data = json.load(f)
        layout = _parse_layout(data)
        errors = _validate(layout)
        if errors:
            raise ValueError(f"Layout {layout.layout_id} failed validation: {errors}")
        _registry[layout.layout_id] = layout
    return _registry


def get_layout(layout_id: str) -> LayoutSpec:
    if not _registry:
        load_all_layouts()
    return _registry[layout_id]


def layouts_for_archetype(archetype: str) -> list[LayoutSpec]:
    if not _registry:
        load_all_layouts()
    return [l for l in _registry.values() if archetype in l.tags]
