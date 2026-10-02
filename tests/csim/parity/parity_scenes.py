"""The scenes the parity harness runs through both engines (plan Phase A, Verification item 1).

A scene is plain data: unit list, orders by tick, a hand-built map name, a tick count. Nothing here
touches either engine. Python unit uid u is C unit id u + 1 (the C registry is 1-based and dense).
Maps are hand-built (simulation/test_maps.open_field, simulation/test_obstacle_navigation.
_build_wall_map); no generator. Order verbs are the Python's: "move", "attack_move"; a verb given
more than one unit is the group order (formation slots) on both sides.
"""
from dataclasses import dataclass, field

# Custom unit types (both engines get the same stats). Python spawns them by stats dict, the C
# registers them with om_roster_register_custom_unit. category: 0 Strike, 1 Line, 2 Siege.
CUSTOM_TYPES = {
    # A short-ranged, short-sighted line unit: its sensor (150) is below the Sniper's range (250),
    # so the Sniper can hit it while it sees nothing and has no target (return-fire scene).
    "Picket": {"category": 1, "hp": 500, "base_damage": 5, "attack_interval": 1.0,
               "attack_range": 100, "speed": 80, "sensor_radius": 150,
               "layer_transition_time": 2.0, "aoe_radius": 0, "type_id": 100},
    # A stationary shooter that sees further than it reaches.
    "Sniper": {"category": 0, "hp": 300, "base_damage": 8, "attack_interval": 1.0,
               "attack_range": 250, "speed": 60, "sensor_radius": 300,
               "layer_transition_time": 1.0, "aoe_radius": 0, "type_id": 101},
}


@dataclass(frozen=True)
class Scene:
    name: str
    ticks: int
    map: str                      # "open" (4000 x 4000) or "wall" (2000 x 1000, test_obstacle_navigation)
    units: tuple                  # ((type_name, faction, x, y), ...) in uid order
    orders: tuple = ()            # ((tick, verb, (uid, ...), x, y), ...)
    shows: str = ""               # what the scene exercises (plan requirement ids)


def _row(type_name, faction, x, ys):
    return tuple((type_name, faction, x, y) for y in ys)


SCENES = {
    # Control: a lone unit marching in the open. Nothing here is a port gap; it proves the harness
    # lines the two engines up (same spawn, same tick, same id mapping).
    "control_lone_march": Scene(
        "control_lone_march", 60, "open",
        (("Raider", 0, 1000.0, 2000.0),),
        ((0, "move", (0,), 3500.0, 2000.0),),
        "harness alignment only"),

    # Control 2: the same march on a diagonal. Shows the C's trig approximation (om_atan2, om_cos)
    # against the Python's exact trig; the fixed direction vectors of plan P8 remove it.
    "control_diagonal_march": Scene(
        "control_diagonal_march", 60, "open",
        (("Raider", 0, 1000.0, 1000.0),),
        ((0, "move", (0,), 3000.0, 3000.0),),
        "harness alignment, C trig error"),

    # (1) A unit behind its own row: three idle friends stand abreast in the Raider's way.
    # P8: the sweep (+30, -30, +60, -60, +90, -90, same-layer blockers, friends block).
    "behind_own_row": Scene(
        "behind_own_row", 150, "open",
        _row("Vanguard", 0, 1000.0, (1965.0, 2000.0, 2035.0)) + (("Raider", 0, 880.0, 2000.0),),
        ((0, "move", (3,), 1400.0, 2000.0),),
        "P8 steering sweep, friends block"),

    # (2) The target walks out of range. A attack-moves and engages B; B plain-moves away.
    # P1 (hold only while the target is in range, pursue again), P7 (facing).
    "target_walks_out_of_range": Scene(
        "target_walks_out_of_range", 200, "open",
        (("Raider", 0, 1000.0, 2000.0), ("Vanguard", 1, 1150.0, 2001.0)),
        ((0, "attack_move", (0,), 3000.0, 2000.0), (0, "move", (1,), 3000.0, 2001.0)),
        "P1 pursuit, P7 facing"),

    # (3) Three in file: single-unit move orders to one point, a slow unit leading two fast ones.
    # P8 (units block each other, sweep), collision (same-layer pairs, moving pairs).
    "three_in_file": Scene(
        "three_in_file", 260, "open",
        (("Raider", 0, 700.0, 2000.0), ("Raider", 0, 740.0, 2000.0), ("Vanguard", 0, 780.0, 2000.0)),
        ((0, "move", (0,), 1600.0, 2000.0), (0, "move", (1,), 1600.0, 2000.0),
         (0, "move", (2,), 1600.0, 2000.0)),
        "P8 sweep, collision"),

    # (4) Attack-move group of eight Raiders (4 x 2) against three idle Vanguards.
    # P5 (slots, group ends when every member engaged), P1, P7, collision.
    "attack_move_group_of_8": Scene(
        "attack_move_group_of_8", 260, "open",
        _row("Raider", 0, 800.0, (1920.0, 1960.0, 2000.0, 2040.0))
        + _row("Raider", 0, 840.0, (1920.0, 1960.0, 2000.0, 2040.0))
        + (("Vanguard", 1, 1700.0, 1960.0), ("Vanguard", 1, 1700.0, 2011.0), ("Vanguard", 1, 1700.0, 2063.0)),
        ((0, "attack_move", (0, 1, 2, 3, 4, 5, 6, 7), 2400.0, 2000.0),),
        "P5 group slots and end, P1, P7"),

    # (5) A wall with a gap: the Python's test wall (2 x 16 blocked cells, open at x < 300 and
    # x > 1900), the unit must go around. P3 routing, collision clamp and slide.
    "wall_with_a_gap": Scene(
        "wall_with_a_gap", 520, "wall",
        (("Vanguard", 0, 1000.0, 75.0),),
        ((0, "move", (0,), 1000.0, 925.0),),
        "P3 route around terrain, waypoints"),

    # (6) Return fire on the march: the Picket attack-moves along y = 2000 past an idle Sniper 200 wu
    # off its line. The Sniper (range 250) outreaches the Picket's sensor (150) and range (100), so it
    # hits a Picket that has no target and sees nothing; the Picket must turn on the attacker and
    # attack-move to it, dropping its old destination.
    # P6 (attack-moving units return fire; out of range, attack-move to the attacker), P7.
    "return_fire_on_the_march": Scene(
        "return_fire_on_the_march", 300, "open",
        (("Picket", 0, 800.0, 2000.0), ("Sniper", 1, 1600.0, 2200.0)),
        ((0, "attack_move", (0,), 2500.0, 2000.0),),
        "P6 return fire for attack-moving units, P7"),
}

# Not one of the six: a pile-up, there to measure how much the result depends on the order the
# collision pass takes pairs in (Python: grid cells; C: id order), which the six barely exercise.
SCENES["crowd_converges"] = Scene(
    "crowd_converges", 200, "open",
    tuple(("Vanguard", 0, 2000.0 + 120.0 * c, 2000.0 + 120.0 * s)
          for c, s in ((1, 0), (0.7071, 0.7071), (0, 1), (-0.7071, 0.7071),
                       (-1, 0), (-0.7071, -0.7071), (0, -1), (0.7071, -0.7071))),
    tuple((0, "move", (u,), 2000.0, 2000.0) for u in range(8)),
    "collision: moving pairs, pile-up at one point (R-099-04)")

SIX = ("behind_own_row", "target_walks_out_of_range", "three_in_file",
       "attack_move_group_of_8", "wall_with_a_gap", "return_fire_on_the_march")
