"""
Layer accessibility mask source placement.

Zones with a "layer_restrictions" property list the layers that ARE accessible
in that zone's area.  For every layer NOT in that list a blocking GradientSource
(property_type="layer_block_N") is emitted at the zone's position.

Zones without "layer_restrictions" are fully accessible on all layers — no
sources are emitted for them.

TacticalMap.layer_accessibility(x, y, layer) returns True when the sampled
layer_block_N value is < 0.5, i.e. no blocking source is nearby.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from layout_instantiator import InstantiatedLayout
from tactical_map import GradientSource


def place_layer_masks(inst: InstantiatedLayout) -> list[GradientSource]:
    sources: list[GradientSource] = []
    for node in inst.spine_nodes:
        restrictions = node.properties.get("layer_restrictions")
        if restrictions is None:
            continue
        accessible = set(restrictions)
        for layer in range(config.LAYER_COUNT):
            if layer not in accessible:
                sources.append(GradientSource(
                    position=node.position,
                    property_type=f"layer_block_{layer}",
                    radius=config.LAYER_MASK_RADIUS,
                    intensity=config.LAYER_MASK_INTENSITY,
                ))
    return sources
