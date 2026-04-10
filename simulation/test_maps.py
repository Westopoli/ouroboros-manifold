from tactical_map import TacticalMap, GradientSource, SpineNode


def open_field():
    return TacticalMap(
        width=4000,
        height=4000,
        gradient_sources=[],
        spine_nodes=[],
        layers=1,
    )


def chokepoint():
    sources = []
    # Wall across y=2000 with a 600 wu gap in the center (x=1700 to x=2300).
    # Left wall: x=0 to x=1700. Right wall: x=2300 to x=4000.
    # Two rows (y=1900, y=2100) of overlapping circles for a ~400 wu thick wall.
    for y_off in [1900, 2000, 2100]:
        for x in range(100, 1700, 200):
            sources.append(GradientSource(
                position=(x, y_off), property_type="obstacle_density",
                radius=200, intensity=1.0, falloff="constant",
            ))
        for x in range(2400, 4000, 200):
            sources.append(GradientSource(
                position=(x, y_off), property_type="obstacle_density",
                radius=200, intensity=1.0, falloff="constant",
            ))

    return TacticalMap(
        width=4000,
        height=4000,
        gradient_sources=sources,
        spine_nodes=[],
        layers=1,
    )


def cover_heavy():
    sources = []
    patches = [
        (800, 800), (1600, 600), (2400, 1000), (3200, 800),
        (600, 1600), (1400, 1800), (2600, 1600), (3400, 1800),
        (1000, 2600), (2000, 2400), (3000, 2600), (3600, 2400),
        (800, 3200), (1800, 3400), (2800, 3200), (3400, 3600),
    ]
    for px, py in patches:
        sources.append(GradientSource(
            position=(px, py), property_type="obstacle_density",
            radius=250, intensity=0.9, falloff="linear",
        ))
        sources.append(GradientSource(
            position=(px, py), property_type="cover_density",
            radius=350, intensity=0.6, falloff="linear",
        ))

    return TacticalMap(
        width=4000,
        height=4000,
        gradient_sources=sources,
        spine_nodes=[],
        layers=1,
    )


def sensor_interference():
    sources = []
    intensities = [0.2, 0.5, 0.8, 1.0]
    for i, intensity in enumerate(intensities):
        cx = 1000.0 + i * 800.0
        sources.append(GradientSource(
            position=(cx, 2000.0), property_type="sensor_interference",
            radius=300, intensity=intensity, falloff="constant",
        ))
    return TacticalMap(
        width=4000, height=4000,
        gradient_sources=sources, spine_nodes=[], layers=1,
    )


def multi_layer():
    return TacticalMap(
        width=4000, height=4000,
        gradient_sources=[], spine_nodes=[], layers=3,
    )


def vantage_point():
    return TacticalMap(
        width=4000, height=4000,
        gradient_sources=[], spine_nodes=[
            SpineNode(position=(2000.0, 2000.0), node_type="vantage_point",
                      properties={"radius": 150}),
        ], layers=3,
    )


def open_field_large():
    return TacticalMap(
        width=12000,
        height=12000,
        gradient_sources=[],
        spine_nodes=[],
        layers=1,
    )


def large_operational():
    sources = []
    for x in [1200, 2800]:
        sources.append(GradientSource(
            position=(x, 2000.0), property_type="obstacle_density",
            radius=300, intensity=0.9, falloff="linear",
        ))
    sources.append(GradientSource(
        position=(2000.0, 1000.0), property_type="cover_density",
        radius=400, intensity=0.5, falloff="linear",
    ))
    sources.append(GradientSource(
        position=(2000.0, 3000.0), property_type="cover_density",
        radius=400, intensity=0.5, falloff="linear",
    ))
    return TacticalMap(
        width=4000, height=4000,
        gradient_sources=sources,
        spine_nodes=[
            SpineNode(position=(2000.0, 2000.0), node_type="objective",
                      properties={"radius": 200}),
            SpineNode(position=(1000.0, 1000.0), node_type="staging",
                      properties={}),
            SpineNode(position=(3000.0, 3000.0), node_type="staging",
                      properties={}),
        ],
        layers=1,
    )


def evacuation():
    sources = []
    for y in [1500, 2500]:
        sources.append(GradientSource(
            position=(2000.0, y), property_type="cover_density",
            radius=300, intensity=0.4, falloff="linear",
        ))
    return TacticalMap(
        width=4000, height=4000,
        gradient_sources=sources,
        spine_nodes=[
            SpineNode(position=(500.0, 2000.0), node_type="staging",
                      properties={}),
            SpineNode(position=(3500.0, 2000.0), node_type="extraction",
                      properties={"radius": 150}),
        ],
        layers=1,
    )
