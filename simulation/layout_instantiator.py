import random
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from map_gen_contracts import LayoutSpec, EdgeSpec
from tactical_map import SpineNode


class InstantiatedLayout:
    __slots__ = ("layout_id", "canvas_size", "canvas_w", "canvas_h",
                 "seed", "spine_nodes", "node_id_map", "edges")

    def __init__(self, layout_id, canvas_size, canvas_w, canvas_h,
                 seed, spine_nodes, node_id_map, edges):
        self.layout_id   = layout_id
        self.canvas_size = canvas_size
        self.canvas_w    = canvas_w
        self.canvas_h    = canvas_h
        self.seed        = seed
        self.spine_nodes = spine_nodes    # list[SpineNode], absolute positions
        self.node_id_map = node_id_map    # dict[zone_id -> SpineNode]
        self.edges       = edges          # list[EdgeSpec], zone_ids unchanged


def instantiate_layout(layout: LayoutSpec, canvas_size: str, seed: int) -> InstantiatedLayout:
    canvas_w, canvas_h = config.CANVAS_SIZES[canvas_size]
    jitter_x = config.LAYOUT_JITTER_PERCENT * canvas_w
    jitter_y = config.LAYOUT_JITTER_PERCENT * canvas_h

    # Margin keeps nodes away from canvas edge so gradients don't bleed off
    margin_x = jitter_x * 2
    margin_y = jitter_y * 2

    rng = random.Random(seed)

    spine_nodes = []
    node_id_map = {}

    for zone in layout.zones:
        rx, ry = zone.position_ratio

        # Scale ratio to canvas
        base_x = rx * canvas_w
        base_y = ry * canvas_h

        # Deterministic jitter — chokepoints get half jitter to preserve funnel shape
        jx_scale = 0.5 if zone.node_type == "chokepoint" else 1.0
        jy_scale = 0.5 if zone.node_type == "chokepoint" else 1.0

        dx = (rng.random() * 2.0 - 1.0) * jitter_x * jx_scale
        dy = (rng.random() * 2.0 - 1.0) * jitter_y * jy_scale

        x = max(margin_x, min(canvas_w - margin_x, base_x + dx))
        y = max(margin_y, min(canvas_h - margin_y, base_y + dy))

        props = dict(zone.properties)
        props["zone_id"] = zone.zone_id  # carry id forward for engine lookups

        node = SpineNode(position=(x, y), node_type=zone.node_type, properties=props)
        spine_nodes.append(node)
        node_id_map[zone.zone_id] = node

    return InstantiatedLayout(
        layout_id=layout.layout_id,
        canvas_size=canvas_size,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        seed=seed,
        spine_nodes=spine_nodes,
        node_id_map=node_id_map,
        edges=list(layout.edges),
    )


def edge_length(inst: InstantiatedLayout, edge: EdgeSpec) -> float | None:
    n1 = inst.node_id_map.get(edge.from_zone)
    n2 = inst.node_id_map.get(edge.to_zone)
    if not n1 or not n2:
        return None
    dx = n1.position[0] - n2.position[0]
    dy = n1.position[1] - n2.position[1]
    return math.sqrt(dx * dx + dy * dy)
