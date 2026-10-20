"""Registered space-lab draft plays (spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md, lane "plays").
Twenty-two plays, each a Setup plus timeline in play coordinates (centre 0, 0; side 0 on the left), none measured. Every number
is a named draft constant, provisional (2026-10-05), for Westley's look at docs/northstar/research/layer_dynamics/plays_drafts.md.
Regenerate the page: python -m scripts.skilllab.plays_space"""
import dataclasses
import math
from dataclasses import dataclass
from pathlib import Path

from scripts.skilllab.contract import Block, Group, Setup, Step, Terrain
from scripts.skilllab.terrain import shift_terrain, with_terrain

STATUS = "unconfirmed draft, not measured, for Westley's look"
PAGE = Path(__file__).resolve().parents[2] / "docs" / "northstar" / "research" / "layer_dynamics" / "plays_drafts.md"

# provisional (2026-10-05): shared by every play
UNITS = 16                      # side 0 always fields this many
CANVAS = (4000.0, 4000.0)       # open canvas and wall extent
START_GAP = 700.0               # distance between the two anchors at tick 0 (plays start at contact distance)
LINE_SPACING = 30.0             # naive line spacing, as plays.py
BLOB_RADIUS = 80 + 12 * math.sqrt(UNITS)   # naive blob radius, as plays.py
# provisional (2026-10-05): S1 choke
WALL_HALF = 50.0                # half thickness of the wall at x = 0
GAP_HALF = 60.0                 # half width of the opening
HOLD_X = -150.0                 # where the holders stand, behind the wall
# provisional (2026-10-05): S2
CONCAVE_ARC_DEG = 120
CONCAVE_RADIUS = 150 + 12 * math.sqrt(UNITS)
SPREAD_SPACING = 60.0           # spread line: wider than LINE_SPACING
COLUMN_SPACING = 30.0
COLUMN_COLS = 3
SCREEN_COUNT = 8                # tough units in front; the rest are long-range behind
SCREEN_AHEAD = 60.0
SCREEN_BEHIND = 60.0
# provisional (2026-10-05): S3 reach by layer
HIGH_LAYER = 1
# provisional (2026-10-05): S4 bait
BAIT_COUNT = 4
BAIT_FALLBACK_TICK = 100
BAIT_FALLBACK_X = -300.0        # offset behind the bait's own anchor
CLOSE_TICK = 150                # main force attack-moves
DETACH_COUNT = 2                # do-not-chase counter: only this many follow the bait
# provisional (2026-10-05): S5 keep the vulnerable type away
FRAIL_BACK = 400.0              # how far behind the strong line the frail type stands
# provisional (2026-10-05): S1 outrange counter
OUTRANGE_FACTOR = 1.2

_REACH = {"Vanguard": (0, 0), "Raider": (1, 1), "Interceptor": (2, 1), "Warden": (0, 0), "Bombard": (0, 2), "Bastion": (0, 2)}


def _types(*names):
    return {n: {"base": n, "reach": _REACH[n]} for n in names if n != "Vanguard"}


@dataclass(frozen=True)
class Anchors:
    """Where a play stands, in layout terms (spec Rev 4): who defends, the defender's anchor kind, the attacker's kind."""
    role: str        # "defender" | "attacker": which role the play's own side 0 takes
    defender: str    # choke_mouth | reach_beyond_exit | exit_concave | exit_line | exit_screen | behind_cover | lane_mouth | far_side
    attacker: str    # blob | mass_one_end | hold | stand_off


@dataclass(frozen=True)
class PlayDraft:
    setup_fn: object
    timeline: tuple
    skill: str
    status: str
    numbers: dict
    words: str
    anchors: Anchors = None


def _g(side, unit, count, formation, x, y=0.0, order="attack_move", goal=None, layer=0, **params):
    return Group(side=side, unit=unit, count=count, formation=formation, x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=layer, order=order, goal=goal, params=params)


def _blob(side, unit, count, x, order="attack_move", layer=0):
    return _g(side, unit, count, "blob", x, order=order, layer=layer, radius=80 + 12 * math.sqrt(count))


def _line(side, unit, count, x, y=0.0, order="attack_move", spacing=LINE_SPACING, goal=None):
    return _g(side, unit, count, "line", x, y, order, goal, spacing=spacing)


def _enemy(mix, x=START_GAP / 2, layer=0, order="attack_move"):
    """Side 1 fields the same mix as side 0, one blob per type, on one layer."""
    return [_g(1, t, n, "blob", x, layer=layer, order=order, radius=80 + 12 * math.sqrt(n)) for t, n in mix]


def _wall(top=4):
    return Terrain(canvas=CANVAS, blocks=(Block(-WALL_HALF, -CANVAS[1] / 2, WALL_HALF, -GAP_HALF, 0, top),
                                          Block(-WALL_HALF, GAP_HALF, WALL_HALF, CANVAS[1] / 2, 0, top)))


def _setup(groups, timeline=(), unit_types=None, terrain=None, settings=None):
    base = Setup(groups=tuple(groups), unit_types=dict(unit_types or {}), timeline=tuple(timeline),
                 settings=dict(settings or {}), terrain=Terrain(canvas=CANVAS))
    return with_terrain(lambda e, s: base, terrain or Terrain(canvas=CANVAS))(UNITS, False)


def _hold_choke():
    return _setup([_line(0, "Vanguard", UNITS, HOLD_X, order="guard"), *_enemy([("Vanguard", UNITS)])],
                  terrain=_wall())


def _concave():
    return _setup([_g(0, "Vanguard", UNITS, "concave", -START_GAP / 2, arc_deg=CONCAVE_ARC_DEG, radius=CONCAVE_RADIUS), *_enemy([("Vanguard", UNITS)])])


def _spread_line():
    return _setup([_line(0, "Vanguard", UNITS, -START_GAP / 2, spacing=SPREAD_SPACING), *_enemy([("Vanguard", UNITS)])])


# The roster mixes as one table. The units' order is the order of the side-1 groups. M0 (all Vanguard) is not a row.
MIXES = [
    {"name": "M1", "units": {"Vanguard": 8, "Raider": 8}, "used_in": ("s3_layer_above", "s3_dark_striker", "s3_ping_then_commit", "s5_vulnerable_away"), "enabled": True},   # DRAFT-mix-M1
    {"name": "M2", "units": {"Vanguard": 8, "Interceptor": 8}, "used_in": ("s3_types_by_reach",), "enabled": True},   # DRAFT-mix-M2
    {"name": "M3", "units": {"Vanguard": 8, "Bombard": 8}, "used_in": ("s2_screen",), "enabled": True},   # DRAFT-mix-M3
    {"name": "M3b", "units": {"Vanguard": 7, "Raider": 1, "Bombard": 8}, "used_in": ("s3_over_the_choke",), "enabled": True},   # DRAFT-mix-M3b
    {"name": "M4", "units": {"Vanguard": 8, "Bastion": 8}, "used_in": ("s1_outrange",), "enabled": True},   # DRAFT-mix-M4
    {"name": "M5", "units": {"Raider": 8, "Bombard": 8}, "used_in": ("s3_raider_bombard",), "enabled": True},   # DRAFT-mix-M5
    {"name": "M6", "units": {"Interceptor": 8, "Bombard": 8}, "used_in": ("s3_interceptor_bombard",), "enabled": True},   # DRAFT-mix-M6
    {"name": "M7", "units": {"Raider": 8, "Interceptor": 8}, "used_in": ("s3_interceptor_raider",), "enabled": True},   # DRAFT-mix-M7
    {"name": "M8", "units": {"Bombard": 8, "Bastion": 8}, "used_in": ("s3_bombard_bastion", "s3_bombard_bastion_level"), "enabled": True},   # DRAFT-mix-M8
    {"name": "M9", "units": {"Vanguard": 12, "Warden": 4}, "used_in": ("s2_warden_line",), "enabled": True},   # DRAFT-mix-M9
]


def _mix(play):
    """The units of the one enabled row of MIXES that names `play`, read at each call."""
    rows = [r for r in MIXES if play in r["used_in"]]
    if not rows:
        raise ValueError("%s has no mix: no row of MIXES names it" % play)
    on = [r for r in rows if r["enabled"]]
    if not on:
        raise ValueError("%s: mix %s is disabled" % (play, rows[0]["name"]))
    if len(on) > 1:
        raise ValueError("%s has two mixes: %s" % (play, ", ".join(r["name"] for r in on)))
    return dict(on[0]["units"])


def _screen():
    m = _mix("s2_screen")
    return _setup([_line(0, "Vanguard", m["Vanguard"], -START_GAP / 2 + SCREEN_AHEAD),
                   _line(0, "Bombard", m["Bombard"], -START_GAP / 2 - SCREEN_BEHIND)]
                  + _enemy(m.items()), unit_types=_types("Bombard"))


def _layer_above():
    m = _mix("s3_layer_above")
    return _setup([_blob(0, "Raider", m["Raider"], -START_GAP / 2, layer=1),
                   _blob(0, "Vanguard", m["Vanguard"], -START_GAP / 2)] + _enemy(m.items()), unit_types=_types("Raider"))


def _types_by_reach():
    m = _mix("s3_types_by_reach")
    return _setup([_blob(0, "Interceptor", m["Interceptor"], -START_GAP / 2, layer=1),
                   _blob(0, "Vanguard", m["Vanguard"], -START_GAP / 2)] + _enemy(m.items()), unit_types=_types("Interceptor"))


def _stack(play, enemy_layer, *placements):
    """Side 0: one blob per (type, layer) of `placements`, a type listed on several layers splitting its row count between them; side 1: the
    same mix on `enemy_layer`. Every type of the play's mix is placed."""
    m = _mix(play)
    layers = {}
    for unit, layer in placements:
        layers.setdefault(unit, []).append(layer)
    if set(layers) != set(m):
        raise ValueError("%s places %s, its mix holds %s" % (play, sorted(layers), sorted(m)))
    groups = [_blob(0, unit, count, -START_GAP / 2, layer=layer) for unit, ls in layers.items()
              for count, layer in zip([m[unit] // len(ls) + (i < m[unit] % len(ls)) for i in range(len(ls))], ls) if count]
    return _setup(groups + _enemy(m.items(), layer=enemy_layer), unit_types=_types(*m))


def _raider_bombard():
    return _stack("s3_raider_bombard", 2, ("Raider", 1), ("Bombard", 3))


def _interceptor_bombard():
    return _stack("s3_interceptor_bombard", 3, ("Interceptor", 1), ("Bombard", 4))


def _interceptor_raider():
    return _stack("s3_interceptor_raider", 4, ("Interceptor", 2), ("Raider", 3))


def _bombard_bastion():
    return _stack("s3_bombard_bastion", 2, ("Bombard", 4), ("Bombard", 3), ("Bastion", 4), ("Bastion", 3))


def _bombard_bastion_level():
    return _stack("s3_bombard_bastion_level", 4, ("Bombard", 4), ("Bastion", 4))


def _warden_line():
    m = _mix("s2_warden_line")
    return _setup([_line(0, "Vanguard", m["Vanguard"], -START_GAP / 2 + SCREEN_AHEAD),
                   _line(0, "Warden", m["Warden"], -START_GAP / 2 - SCREEN_BEHIND)] + _enemy(m.items()), unit_types=_types("Warden"))


def _vision_control():
    return _setup([_blob(0, "Raider", UNITS, -START_GAP / 2, layer=HIGH_LAYER)] + _enemy([("Raider", UNITS)]),
                  unit_types=_types("Raider"))


def _over_the_choke():
    m = _mix("s3_over_the_choke")
    return _setup([_blob(0, "Bombard", m["Bombard"], HOLD_X, layer=2),
                   _blob(0, "Vanguard", m["Vanguard"], HOLD_X),
                   _g(0, "Raider", m["Raider"], "blob", WALL_HALF + 100.0, radius=10.0)] + _enemy(m.items()),
                  unit_types=_types("Raider", "Bombard"), terrain=_wall(top=1))


def _dark_striker():
    m = _mix("s3_dark_striker")
    groups = [_blob(0, "Raider", m["Raider"], -START_GAP / 2, layer=1),
              _blob(0, "Vanguard", m["Vanguard"], -START_GAP / 2)] + _enemy(m.items())
    enemy_on = [Step.set_emission(i, True) for i, g in enumerate(groups) if g.side == 1]
    return _setup(groups, timeline=[Step.set_emission(0, False), Step.set_emission(1, False), *enemy_on], unit_types=_types("Raider"))


def _ping_then_commit():
    m = _mix("s3_ping_then_commit")
    groups = [_blob(0, "Raider", m["Raider"], -START_GAP / 2, layer=1),
              _blob(0, "Vanguard", m["Vanguard"], -START_GAP / 2)] + _enemy(m.items())
    return _setup(groups, timeline=[Step.ping(0, START_GAP / 2, 0.0)], unit_types=_types("Raider"))


def _bait_steps(bait, main, x):
    return (Step(bait, ("tick", BAIT_FALLBACK_TICK), "move", goal=(x + BAIT_FALLBACK_X * (1 if x < 0 else -1), 0.0)),
            Step(main, ("tick", CLOSE_TICK), "attack_move"))


def _bait():
    x = -START_GAP / 2
    return _setup([_blob(0, "Vanguard", BAIT_COUNT, x),
                   _g(0, "Vanguard", UNITS - BAIT_COUNT, "concave", x - 200, order="guard",
                      arc_deg=CONCAVE_ARC_DEG, radius=CONCAVE_RADIUS), *_enemy([("Vanguard", UNITS)])],
                  timeline=_bait_steps(0, 1, x))


def _vulnerable_away():
    m = _mix("s5_vulnerable_away")
    return _setup([_line(0, "Vanguard", m["Vanguard"], -START_GAP / 2), _line(0, "Raider", m["Raider"], -START_GAP / 2 - FRAIL_BACK)]
                  + _enemy(m.items()), unit_types=_types("Raider"))


def _mass_one_end():
    end_y = (UNITS - 1) * SPREAD_SPACING / 2
    return _setup([_g(0, "Vanguard", UNITS, "column", -START_GAP / 2, end_y, goal=(START_GAP / 2, end_y),
                      spacing=COLUMN_SPACING, cols=COLUMN_COLS),
                   _line(1, "Vanguard", UNITS, START_GAP / 2, spacing=SPREAD_SPACING)])


def _do_not_chase():
    x = START_GAP / 2
    return _setup([_blob(0, "Vanguard", UNITS - DETACH_COUNT, -x, order="guard"),
                   _blob(0, "Vanguard", DETACH_COUNT, -x),
                   _blob(1, "Vanguard", BAIT_COUNT, x),
                   _g(1, "Vanguard", UNITS - BAIT_COUNT, "concave", x + 200, order="guard",
                      arc_deg=CONCAVE_ARC_DEG, radius=CONCAVE_RADIUS)],
                  timeline=_bait_steps(2, 3, x))


def _outrange():
    m = _mix("s1_outrange")
    return _setup([_blob(0, "Bastion", m["Bastion"], -START_GAP / 2), _blob(0, "Vanguard", m["Vanguard"], -START_GAP / 2),
                   _line(1, "Vanguard", m["Vanguard"], -HOLD_X, order="guard"), _line(1, "Bastion", m["Bastion"], -HOLD_X, order="guard")],
                  unit_types=_types("Bastion"), terrain=_wall())


def _play(fn, skill, numbers, words):
    return PlayDraft(fn, tuple(fn().timeline), skill, STATUS, numbers, words)


PLAYS = {
    "s1_hold_choke": _play(_hold_choke, "S1", {"WALL_HALF": WALL_HALF, "GAP_HALF": GAP_HALF, "HOLD_X": HOLD_X},
        "A wall crosses the middle with one narrow opening. Side 0 stands in a line just behind it and holds fire "
        "in range (guard); the enemy blob attack-moves at it, so few can fire at once."),
    "s2_concave": _play(_concave, "S2", {"CONCAVE_ARC_DEG": CONCAVE_ARC_DEG, "CONCAVE_RADIUS": CONCAVE_RADIUS},
        "Side 0 forms a 120-degree arc curved around the point where the enemy arrives and attack-moves."),
    "s2_spread_line": _play(_spread_line, "S2", {"SPREAD_SPACING": SPREAD_SPACING},
        "Side 0 spreads in one wide line, twice the naive spacing, so every unit is in range together."),
    "s2_screen": _play(_screen, "S2", {"SCREEN_AHEAD": SCREEN_AHEAD, "SCREEN_BEHIND": SCREEN_BEHIND},
        "Eight Vanguards stand in front; eight Bombards stand in a line behind them. All attack-move."),
    "s3_layer_above": _play(_layer_above, "S3", {"HIGH_LAYER": HIGH_LAYER},
        "Eight Raiders sit one layer above the enemy and fire down; the eight Vanguards fight on the enemy's layer."),
    "s3_types_by_reach": _play(_types_by_reach, "S3", {"HIGH_LAYER": HIGH_LAYER},
        "Eight Interceptors sit one layer above the enemy; the eight Vanguards fight on the enemy's layer."),
    "s3_raider_bombard": _play(_raider_bombard, "S3", {},
        "Eight Raiders sit one layer below the enemy and fire up; eight Bombards sit one layer above it and fire down. The enemy is on layer 2."),
    "s3_interceptor_bombard": _play(_interceptor_bombard, "S3", {},
        "Eight Interceptors sit two layers below the enemy and fire up; eight Bombards sit one layer above it. The enemy is on layer 3."),
    "s3_interceptor_raider": _play(_interceptor_raider, "S3", {},
        "Eight Interceptors sit two layers below the enemy and eight Raiders one layer below it, all firing up. The enemy is on layer 4."),
    "s3_bombard_bastion": _play(_bombard_bastion, "S3", {},
        "Bombards and Bastions stand on layers 3 and 4, half of each type on each, two and one layers above the enemy on layer 2, and fire down."),
    "s3_bombard_bastion_level": _play(_bombard_bastion_level, "S3", {},
        "Bombards and Bastions stand on the enemy's layer, layer 4, and fire level."),
    "s2_warden_line": _play(_warden_line, "S2", {"SCREEN_AHEAD": SCREEN_AHEAD, "SCREEN_BEHIND": SCREEN_BEHIND},
        "Twelve Vanguards stand in front; four Wardens stand in a line behind them. All attack-move."),
    "s3_vision_control": _play(_vision_control, "S3", {"HIGH_LAYER": HIGH_LAYER},
        "Sixteen Raiders sit one layer above sixteen Raiders; every pair is cross-layer. The vision family's positive control "
        "fixture only: no ordinary sweep runs it."),
    "s3_over_the_choke": _play(_over_the_choke, "S3", {"WALL_HALF": WALL_HALF, "GAP_HALF": GAP_HALF},
        "Bombards fire over the wall top; a Raider past the choke spots for them."),
    "s3_dark_striker": _play(_dark_striker, "S3", {"HIGH_LAYER": HIGH_LAYER},
        "Side 0 goes silent at tick 0; the enemy is switched to emit at tick 0, at the emitting family's values."),
    "s3_ping_then_commit": _play(_ping_then_commit, "S3", {"HIGH_LAYER": HIGH_LAYER},
        "Side 0 pings the enemy layer at the enemy anchor at tick 0, then attack-moves."),
    "s4_bait": _play(_bait, "S4", {"BAIT_COUNT": BAIT_COUNT, "BAIT_FALLBACK_TICK": BAIT_FALLBACK_TICK,
                                   "BAIT_FALLBACK_X": BAIT_FALLBACK_X, "CLOSE_TICK": CLOSE_TICK},
        "Four units attack-move at the enemy. At tick 100 they move back; the other twelve guard in an arc behind "
        "them and at tick 150 attack-move, closing around whoever followed."),
    "s5_vulnerable_away": _play(_vulnerable_away, "S5", {"FRAIL_BACK": FRAIL_BACK},
        "Eight Vanguards form the front line; eight Raiders stand 400 behind it, away from the enemy."),
    "s2_mass_one_end": _play(_mass_one_end, "S2", {"SPREAD_SPACING": SPREAD_SPACING, "COLUMN_SPACING": COLUMN_SPACING,
                                                   "COLUMN_COLS": COLUMN_COLS},
        "Counter to the spread line. The enemy is spread wide; side 0 masses in a three-wide column at one end of it "
        "and attack-moves to that end, so only the few defenders there can fire."),
    "s4_do_not_chase": _play(_do_not_chase, "S4", {"BAIT_COUNT": BAIT_COUNT, "DETACH_COUNT": DETACH_COUNT,
                                                   "BAIT_FALLBACK_TICK": BAIT_FALLBACK_TICK, "CLOSE_TICK": CLOSE_TICK},
        "Counter to the bait. The enemy plays the bait; fourteen of side 0 guard and do not move, two attack-move as a small detachment."),
    "s1_outrange": _play(_outrange, "S1", {"OUTRANGE_FACTOR": OUTRANGE_FACTOR, "HOLD_X": HOLD_X},
        "Counter to the held choke. The enemy holds behind the wall; side 0 mixes Bastions and Vanguards and attack-moves."),
}


_ANCHORS = {
    "s1_hold_choke": Anchors("defender", "choke_mouth", "blob"),
    "s1_outrange": Anchors("defender", "reach_beyond_exit", "blob"),
    "s2_concave": Anchors("defender", "exit_concave", "blob"),
    "s2_spread_line": Anchors("defender", "exit_line", "blob"),
    "s2_screen": Anchors("defender", "exit_screen", "blob"),
    "s3_types_by_reach": Anchors("defender", "behind_cover", "blob"),
    "s3_layer_above": Anchors("defender", "behind_cover", "blob"),
    "s3_vision_control": Anchors("defender", "behind_cover", "blob"),
    "s3_raider_bombard": Anchors("defender", "behind_cover", "blob"),
    "s3_bombard_bastion_level": Anchors("defender", "behind_cover", "blob"),
    "s3_interceptor_bombard": Anchors("defender", "behind_cover", "blob"),
    "s3_interceptor_raider": Anchors("defender", "behind_cover", "blob"),
    "s3_bombard_bastion": Anchors("attacker", "exit_line", "blob"),
    "s2_warden_line": Anchors("defender", "exit_screen", "blob"),
    "s3_over_the_choke": Anchors("defender", "choke_mouth", "blob"),
    "s3_dark_striker": Anchors("attacker", "exit_line", "blob"),
    "s3_ping_then_commit": Anchors("attacker", "exit_line", "blob"),
    "s4_bait": Anchors("defender", "lane_mouth", "blob"),
    "s5_vulnerable_away": Anchors("defender", "far_side", "blob"),
    "s2_mass_one_end": Anchors("attacker", "exit_line", "mass_one_end"),
    "s4_do_not_chase": Anchors("attacker", "lane_mouth", "hold"),
}
PLAYS = {name: dataclasses.replace(p, anchors=_ANCHORS[name]) for name, p in PLAYS.items()}
# s1_outrange is also the counter to s1_hold_choke (side 0 attacks the hold formation from a stand-off); scenes.placed_scene(..., counter=True) reads this row.
COUNTER_USE = {"s1_outrange": Anchors("attacker", "choke_mouth", "stand_off")}


def _spread(setup, start_distance):
    anchor = {}
    for g in setup.groups:
        anchor.setdefault(g.side, g.x)
    centre = CANVAS[0] / 2
    delta = {0: centre - start_distance / 2 - anchor[0], 1: centre + start_distance / 2 - anchor[1]}
    near = lambda x: delta[min(anchor, key=lambda s: abs(anchor[s] - x))]
    groups = tuple(dataclasses.replace(g, x=g.x + delta[g.side],
                                       goal=None if g.goal is None else (g.goal[0] + near(g.goal[0]), g.goal[1]))
                   for g in setup.groups)
    steps = tuple(dataclasses.replace(t, goal=(t.goal[0] + delta[1 if t.order == "ping" else setup.groups[t.group].side], t.goal[1]))
                  if t.goal is not None else t for t in setup.timeline)
    return dataclasses.replace(setup, groups=groups, timeline=steps)


def _scale(enemy, heads):
    """Largest-remainder scaling of the side-1 group counts to `heads`, every group at least 1."""
    want = [g.count * heads / UNITS for g in enemy]
    counts = [max(1, int(w)) for w in want]
    while sum(counts) < heads:
        i = max(range(len(want)), key=lambda i: want[i] - counts[i])
        counts[i] += 1
    while sum(counts) > heads:
        i = min((i for i in range(len(want)) if counts[i] > 1), key=lambda i: want[i] - counts[i])
        counts[i] -= 1
    return counts


def scan_build(name):
    if name not in PLAYS:
        raise ValueError("no space play named %r" % (name,))
    fn = PLAYS[name].setup_fn

    def build(terrain, enemy_heads, swap, start_distance=None):
        if enemy_heads < 1:
            raise ValueError("enemy_heads must be at least 1, got %r" % (enemy_heads,))
        setup = fn()
        enemy = [g for g in setup.groups if g.side == 1]
        if len(enemy) > enemy_heads:
            raise ValueError("%s has %d enemy groups, needs at least that many heads" % (name, len(enemy)))
        counts = _scale(enemy, enemy_heads)
        new = {}
        for g, c in zip(enemy, counts):
            params = dict(g.params)
            if g.formation == "blob":
                params["radius"] = 80 + 12 * math.sqrt(c)
            new[id(g)] = dataclasses.replace(g, count=c, params=params)
        groups = tuple(new.get(id(g), g) for g in setup.groups)
        setup = dataclasses.replace(setup, groups=groups)
        if start_distance is not None:
            setup = _spread(setup, start_distance)
        if terrain is None:
            return setup
        first = {}
        for g in setup.groups:
            first.setdefault(g.side, g)
        mid = ((first[0].x + first[1].x) / 2, (first[0].y + first[1].y) / 2)
        return dataclasses.replace(setup, terrain=shift_terrain(terrain, *mid))

    return build


def _group_line(g):
    where = "layer %d, at (%g, %g)" % (g.layer, g.x, g.y)
    goal = "" if g.goal is None else ", goal (%g, %g)" % g.goal
    return "- side %d: %d x %s, %s, %s, order %s%s" % (g.side, g.count, g.unit, g.formation, where, g.order, goal)


def _step_line(s):
    goal = "" if s.goal is None else " to (%g, %g)" % s.goal
    return "- group %d, at %s %s: %s%s" % (s.group, s.when[0], ", ".join(str(v) for v in s.when[1:]) or "-", s.order, goal)


def render_drafts_page():
    out = ["# Space-lab draft plays", "",
           "Generated by `python -m scripts.skilllab.plays_space`; do not edit by hand. Every play is %s. "
           "Coordinates: centre (0, 0), side 0 on the left, sides start %g apart. Every number is a named constant, "
           "provisional (2026-10-05)." % (STATUS, START_GAP), ""]
    for name in sorted(PLAYS):
        p = PLAYS[name]
        setup = p.setup_fn()
        out += ["## %s (%s)" % (name, p.skill), "", "Status: %s." % p.status, "", p.words, "", "Numbers:"]
        out += ["- %s = %g" % (k, p.numbers[k]) for k in sorted(p.numbers)]
        out += ["", "Groups (canvas coordinates, canvas centre %g, %g):" % (CANVAS[0] / 2, CANVAS[1] / 2)]
        out += [_group_line(g) for g in setup.groups]
        if p.timeline:
            out += ["", "Timeline:"] + [_step_line(s) for s in p.timeline]
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    PAGE.write_text(render_drafts_page())
