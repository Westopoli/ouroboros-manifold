"""Registered space-lab draft plays (spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md, lane "plays").
Ten plays, each a Setup plus timeline in play coordinates (centre 0, 0; side 0 on the left), none measured. Every number
is a named draft constant, provisional (2026-10-05), for Westley's look at docs/northstar/research/layer_dynamics/plays_drafts.md.
Regenerate the page: python -m scripts.skilllab.plays_space"""
import dataclasses
import math
from dataclasses import dataclass
from pathlib import Path

from scripts.skilllab.contract import Block, Group, Setup, Step, Terrain
from scripts.skilllab import plays
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
SCREEN_HP_FACTOR = 2.0
SCREEN_RANGE_FACTOR = 1.2
SCREEN_AHEAD = 60.0
SCREEN_BEHIND = 60.0
# provisional (2026-10-05): S3 reach by layer
HIGH_COUNT = 8                  # units on layer 1 that fire down one layer
HIGH_LAYER = 1
HIGH_DOWN_STRENGTH = 1.0        # OM_TP_{RANGE,DAMAGE,VISION}_DOWN_1
# provisional (2026-10-05): S4 bait
BAIT_COUNT = 4
BAIT_FALLBACK_TICK = 100
BAIT_FALLBACK_X = -300.0        # offset behind the bait's own anchor
CLOSE_TICK = 150                # main force attack-moves
DETACH_COUNT = 2                # do-not-chase counter: only this many follow the bait
# provisional (2026-10-05): S5 keep the vulnerable type away
FRAIL_COUNT = 6
FRAIL_HP_FACTOR = 0.5
FRAIL_BACK = 400.0              # how far behind the strong line the frail type stands
# provisional (2026-10-05): S1 outrange counter
OUTRANGE_FACTOR = 1.2

_LONG = {"base": "Vanguard", "scale": {"attack_range": SCREEN_RANGE_FACTOR}, "set": {}}
_TOUGH = {"base": "Vanguard", "scale": {"max_hp": SCREEN_HP_FACTOR}, "set": {}}
_FRAIL = {"base": "Vanguard", "scale": {"max_hp": FRAIL_HP_FACTOR}, "set": {}}
_HIGH = {"base": "Vanguard", "scale": {}, "set": {}, "reach": (0, HIGH_LAYER)}
_OUT = {"base": "Vanguard", "scale": {"attack_range": OUTRANGE_FACTOR}, "set": {}}


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


def _blob(side, unit, count, x, order="attack_move"):
    return _g(side, unit, count, "blob", x, order=order, radius=80 + 12 * math.sqrt(count))


def _line(side, unit, count, x, y=0.0, order="attack_move", spacing=LINE_SPACING, goal=None):
    return _g(side, unit, count, "line", x, y, order, goal, spacing=spacing)


def _enemy(x=START_GAP / 2):
    return _blob(1, "Vanguard", UNITS, x)


def _wall():
    return Terrain(canvas=CANVAS, blocks=(Block(-WALL_HALF, -CANVAS[1] / 2, WALL_HALF, -GAP_HALF, 0, 4),
                                          Block(-WALL_HALF, GAP_HALF, WALL_HALF, CANVAS[1] / 2, 0, 4)))


def _setup(groups, timeline=(), unit_types=None, terrain=None, settings=None):
    base = Setup(groups=tuple(groups), unit_types=dict(unit_types or {}), timeline=tuple(timeline),
                 settings=dict(settings or {}), terrain=Terrain(canvas=CANVAS))
    return with_terrain(lambda e, s: base, terrain or Terrain(canvas=CANVAS))(UNITS, False)


def _hold_choke():
    return _setup([_line(0, "Vanguard", UNITS, HOLD_X, order="guard"), _blob(1, "Vanguard", UNITS, START_GAP / 2)],
                  terrain=_wall())


def _concave():
    return _setup([_g(0, "Vanguard", UNITS, "concave", -START_GAP / 2, arc_deg=CONCAVE_ARC_DEG, radius=CONCAVE_RADIUS), _enemy()])


def _spread_line():
    return _setup([_line(0, "Vanguard", UNITS, -START_GAP / 2, spacing=SPREAD_SPACING), _enemy()])


def _screen():
    return _setup([_line(0, "VanguardTough", SCREEN_COUNT, -START_GAP / 2 + SCREEN_AHEAD),
                   _line(0, "VanguardLong", UNITS - SCREEN_COUNT, -START_GAP / 2 - SCREEN_BEHIND), _enemy()],
                  unit_types={"VanguardTough": _TOUGH, "VanguardLong": _LONG})


def _types_by_reach():
    settings = {"OM_TP_%s_DOWN_1" % k: HIGH_DOWN_STRENGTH for k in ("RANGE", "DAMAGE", "VISION")}
    return _setup([_g(0, "VanguardHigh", HIGH_COUNT, "blob", -START_GAP / 2, layer=HIGH_LAYER,
                      radius=80 + 12 * math.sqrt(HIGH_COUNT)),
                   _blob(0, "Vanguard", UNITS - HIGH_COUNT, -START_GAP / 2), _enemy()],
                  unit_types={"VanguardHigh": _HIGH}, settings=settings)


def _bait_steps(bait, main, x):
    return (Step(bait, ("tick", BAIT_FALLBACK_TICK), "move", goal=(x + BAIT_FALLBACK_X * (1 if x < 0 else -1), 0.0)),
            Step(main, ("tick", CLOSE_TICK), "attack_move"))


def _bait():
    x = -START_GAP / 2
    return _setup([_blob(0, "Vanguard", BAIT_COUNT, x),
                   _g(0, "Vanguard", UNITS - BAIT_COUNT, "concave", x - 200, order="guard",
                      arc_deg=CONCAVE_ARC_DEG, radius=CONCAVE_RADIUS), _enemy()],
                  timeline=_bait_steps(0, 1, x))


def _vulnerable_away():
    return _setup([_line(0, "Vanguard", UNITS - FRAIL_COUNT, -START_GAP / 2),
                   _line(0, "VanguardFrail", FRAIL_COUNT, -START_GAP / 2 - FRAIL_BACK), _enemy()],
                  unit_types={"VanguardFrail": _FRAIL})


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
    return _setup([_blob(0, "VanguardOut", UNITS, -START_GAP / 2),
                   _line(1, "Vanguard", UNITS, -HOLD_X, order="guard")],
                  unit_types={"VanguardOut": _OUT}, terrain=_wall())


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
    "s2_screen": _play(_screen, "S2", {"SCREEN_COUNT": SCREEN_COUNT, "SCREEN_HP_FACTOR": SCREEN_HP_FACTOR,
                                       "SCREEN_RANGE_FACTOR": SCREEN_RANGE_FACTOR, "SCREEN_AHEAD": SCREEN_AHEAD,
                                       "SCREEN_BEHIND": SCREEN_BEHIND},
        "Eight tough units (double hit points) stand in front; eight long-range units stand in a line behind them. All attack-move."),
    "s3_types_by_reach": _play(_types_by_reach, "S3", {"HIGH_COUNT": HIGH_COUNT, "HIGH_LAYER": HIGH_LAYER,
                                                      "HIGH_DOWN_STRENGTH": HIGH_DOWN_STRENGTH},
        "Eight units sit one layer above the enemy and fire down at full strength, which the enemy cannot return; "
        "the other eight fight on the enemy's layer."),
    "s4_bait": _play(_bait, "S4", {"BAIT_COUNT": BAIT_COUNT, "BAIT_FALLBACK_TICK": BAIT_FALLBACK_TICK,
                                   "BAIT_FALLBACK_X": BAIT_FALLBACK_X, "CLOSE_TICK": CLOSE_TICK},
        "Four units attack-move at the enemy. At tick 100 they move back; the other twelve guard in an arc behind "
        "them and at tick 150 attack-move, closing around whoever followed."),
    "s5_vulnerable_away": _play(_vulnerable_away, "S5", {"FRAIL_COUNT": FRAIL_COUNT, "FRAIL_HP_FACTOR": FRAIL_HP_FACTOR,
                                                         "FRAIL_BACK": FRAIL_BACK},
        "Ten full-strength units form the front line; six frail units (half hit points) stand 400 behind it, away from the enemy."),
    "s2_mass_one_end": _play(_mass_one_end, "S2", {"SPREAD_SPACING": SPREAD_SPACING, "COLUMN_SPACING": COLUMN_SPACING,
                                                   "COLUMN_COLS": COLUMN_COLS},
        "Counter to the spread line. The enemy is spread wide; side 0 masses in a three-wide column at one end of it "
        "and attack-moves to that end, so only the few defenders there can fire."),
    "s4_do_not_chase": _play(_do_not_chase, "S4", {"BAIT_COUNT": BAIT_COUNT, "DETACH_COUNT": DETACH_COUNT,
                                                   "BAIT_FALLBACK_TICK": BAIT_FALLBACK_TICK, "CLOSE_TICK": CLOSE_TICK},
        "Counter to the bait. The enemy plays the bait; fourteen of side 0 guard and do not move, two attack-move as a small detachment."),
    "s1_outrange": _play(_outrange, "S1", {"OUTRANGE_FACTOR": OUTRANGE_FACTOR, "HOLD_X": HOLD_X},
        "Counter to the held choke. The enemy holds behind the wall; side 0 are all long-range units (reach x1.2) "
        "and attack-move, to fire from outside the holders' range."),
}


_ANCHORS = {
    "s1_hold_choke": Anchors("defender", "choke_mouth", "blob"),
    "s1_outrange": Anchors("defender", "reach_beyond_exit", "blob"),
    "s2_concave": Anchors("defender", "exit_concave", "blob"),
    "s2_spread_line": Anchors("defender", "exit_line", "blob"),
    "s2_screen": Anchors("defender", "exit_screen", "blob"),
    "s3_types_by_reach": Anchors("defender", "behind_cover", "blob"),
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
    steps = tuple(dataclasses.replace(t, goal=(t.goal[0] + delta[setup.groups[t.group].side], t.goal[1]))
                  if t.goal is not None else t for t in setup.timeline)
    return dataclasses.replace(setup, groups=groups, timeline=steps)


def scan_build(name):
    if name not in PLAYS:
        raise ValueError("no space play named %r" % (name,))
    fn = PLAYS[name].setup_fn

    def build(terrain, enemy_heads, swap, start_distance=None):
        if enemy_heads < 1:
            raise ValueError("enemy_heads must be at least 1, got %r" % (enemy_heads,))
        setup = dataclasses.replace(fn(), mopup=plays.MOPUP, mopup_interval_ticks=plays.MOPUP_INTERVAL_TICKS,
                                    quiet_from_first_damage=True)
        enemy = [g for g in setup.groups if g.side == 1]
        if len(enemy) > enemy_heads:
            raise ValueError("%s has %d enemy groups, needs at least that many heads" % (name, len(enemy)))
        counts = [max(1, round(g.count * enemy_heads / UNITS)) for g in enemy]
        for i in range(len(counts) - 1):
            counts[i] = min(counts[i], enemy_heads - (len(counts) - 1 - i) - sum(counts[:i]))
        counts[-1] = enemy_heads - sum(counts[:-1])
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
