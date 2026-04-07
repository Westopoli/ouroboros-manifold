from tactical_map import TacticalMap


def open_field():
    return TacticalMap(
        width=4000,
        height=4000,
        gradient_sources=[],
        spine_nodes=[],
        layers=1,
    )
