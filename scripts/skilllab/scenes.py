"""Hand-built scenes in canvas coordinates."""
import dataclasses
import math

from scripts.skilllab import formations, maps, plays, plays_space
from scripts.skilllab.contract import SHIFT_MAX, SILENCE_TICKS, Block, Group, Setup, Terrain
from scripts.skilllab.terrain import shift_terrain

_CANVAS = (3000.0, 1600.0)
_WALL = (1500, 1600)
_GAP = (700, 900)


def phase_b_choke(defenders=8):
    """The Phase B choke: a wall with a gap, defenders in a line behind it, attackers in a blob in front."""
    def build(enemy_heads, swap):
        if defenders < 1 or enemy_heads < 1:
            raise ValueError("defenders and enemy_heads must be >= 1")
        terrain = Terrain(canvas=_CANVAS, blocks=(Block(_WALL[0], 0, _WALL[1], _GAP[0], 0, 4),
                                                  Block(_WALL[0], _GAP[1], _WALL[1], _CANVAS[1], 0, 4)))
        return Setup(groups=(
            Group(side=0, unit="Vanguard", count=defenders, formation="line", x=1700.0, y=800.0, facing_deg=180.0,
                  layer=0, order="attack_move", params={"spacing": 30}),
            Group(side=1, unit="Vanguard", count=enemy_heads, formation="blob", x=800.0, y=800.0, facing_deg=0.0,
                  layer=0, order="attack_move", params={"radius": 80 + 12 * math.sqrt(enemy_heads)})),
            unit_types={}, terrain=terrain)
    build.labels = {"play_side0": "defenders line", "play_side1": "attackers blob",
                    "status_side0": "naive", "status_side1": "naive"}
    return build


def guard_defenders(build):
    """Side 1 of the built setup holds the guard order (R-096-08)."""
    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        groups = tuple(dataclasses.replace(g, order="guard") if g.side == 1 else g for g in setup.groups)
        return dataclasses.replace(setup, groups=groups)
    return wrapped


def objective_scene(start_distance, unit="Vanguard", size=16):
    """Both groups start start_distance apart and attack-move to an objective midway between them."""
    def build(enemy_heads, swap):
        if size < 1 or enemy_heads < 1:
            raise ValueError("size and enemy_heads must be >= 1")
        objective = (0.0, 0.0)
        groups = tuple(
            Group(side=side, unit=unit, count=count, formation="blob", x=x, y=0.0, facing_deg=facing, layer=0,
                  order="attack_move", goal=objective, params={"radius": 80 + 12 * math.sqrt(count)})
            for side, count, x, facing in ((0, size, -start_distance / 2, 0.0), (1, enemy_heads, start_distance / 2, 180.0)))
        return Setup(groups=groups, unit_types={}, start_distance=start_distance, objective=objective,
                     mopup=plays.MOPUP, mopup_interval_ticks=plays.MOPUP_INTERVAL_TICKS,
                     max_ticks=plays.max_ticks_for(size, enemy_heads), quiet_from_first_damage=True)
    return build


# Placed scenes (spec docs/northstar/plans/2026-10-06-layout-search-spec.md Rev 3 and Rev 4)
FIT_STEP = 50.0          # ruled (Architect 2026-10-07): wu a formation is moved along the corridor axis per fit attempt, both directions, nearest first
FIT_LIMIT = 800.0        # ruled (Architect 2026-10-07): the farthest it is moved before the scene gives up and records None
BEHIND_COVER = 150.0     # provisional (2026-10-07): short-reach types stand this far in front of the long-reach ones
AMBUSH_BEHIND = 200.0    # provisional (2026-10-07): the ambush group stands this far behind the bait group, as plays_space
NAIVE_PLAYS = ("naive", "naive_line")
_NAIVE_ANCHORS = plays_space.Anchors("attacker", "choke_mouth", "blob")


def _walls_and_lanes(layout):
    thick = maps.LAYOUT_WALL_THICK
    walls = sorted((b for b in layout.blocks if abs((b.x1 - b.x0) - thick) < 1e-6), key=lambda b: b.y0)
    lanes = [b for b in layout.blocks if abs((b.x1 - b.x0) - thick) >= 1e-6]
    return walls, lanes


def _resolve(layout, features):
    """The layout's choke centre, wall thickness, lane x range (or None) and covers, in layout coordinates."""
    walls, lanes = _walls_and_lanes(layout)
    if features.choke_width_bodies and len(walls) >= 2:
        a, b = walls[:2]
        centre, thick = ((a.x0 + a.x1) / 2, (a.y1 + b.y0) / 2), maps.LAYOUT_WALL_THICK
    else:
        centre, thick = (0.0, 0.0), 0.0
    lane_x = (min(b.x0 for b in lanes), max(b.x1 for b in lanes)) if features.lane_count and lanes else None
    return centre, thick, lane_x, layout.covers


def _walkable(layout, groups, margin):
    """Every unit of every group stands outside the layout's blocks on the group's layer."""
    return not any(b.layer_lo <= g.layer <= b.layer_hi and b.x0 - margin <= x <= b.x1 + margin and b.y0 - margin <= y <= b.y1 + margin
                   for g in groups for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
                   for b in layout.blocks)


def _anchor_points(kind, s, centre, thick, lane_x, covers, reach):
    """(mouth, anchor): the choke mouth on the defender's side and the defender's anchor for this kind, layout coordinates."""
    mouth = (centre[0] + s * thick / 2, centre[1])
    if kind == "reach_beyond_exit":
        return mouth, (mouth[0] + s * reach * plays_space.OUTRANGE_FACTOR, mouth[1])
    if kind == "exit_line":
        return mouth, (mouth[0] + s * reach, mouth[1])
    if kind == "lane_mouth":
        return mouth, mouth if lane_x is None else ((lane_x[0] if s < 0 else lane_x[1]), centre[1])
    if kind == "far_side":
        return mouth, (centre[0] + s * plays_space.FRAIL_BACK, centre[1])
    if kind == "behind_cover":
        if not covers:
            return mouth, (mouth[0] + s * BEHIND_COVER / 2, mouth[1])
        c = min(covers, key=lambda c: math.dist((c.x, c.y), mouth))
        return mouth, (c.x + s * c.radius, c.y)
    return mouth, mouth


def _defender_positions(kind, n_groups, mouth, anchor, s):
    """One (x, y) per defender group, in group order."""
    if kind == "exit_screen":
        return [(mouth[0] - s * plays_space.SCREEN_AHEAD, mouth[1]), (mouth[0] + s * plays_space.SCREEN_BEHIND, mouth[1])]
    if kind == "behind_cover":
        return [anchor, (anchor[0] - s * BEHIND_COVER, anchor[1])]
    if kind == "lane_mouth":
        return [anchor, (anchor[0] + s * AMBUSH_BEHIND, anchor[1])][:n_groups]
    if kind == "far_side":
        return [mouth, anchor]
    return [anchor] * n_groups


def _blob_group(side, unit, count, x, y, facing, order):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=facing, layer=0, order=order,
                 params={"radius": 80 + 12 * math.sqrt(count)})


def _naive_defender(play, heads):
    if play == "naive":
        return _blob_group(1, "Vanguard", heads, 0.0, 0.0, 180.0, "guard")
    return Group(side=1, unit="Vanguard", count=heads, formation="line", x=0.0, y=0.0, facing_deg=180.0, layer=0, order="guard",
                 params={"spacing": plays_space.SPREAD_SPACING})


def _groups_and_timeline(play, anchors, heads, swap):
    """The play's groups and timeline before placement, defender groups first for a defender play."""
    if play in NAIVE_PLAYS:
        return (_blob_group(0, "Vanguard", plays_space.UNITS, 0.0, 0.0, 0.0, "attack_move"), _naive_defender(play, heads)), (), {}, {}
    setup = plays_space.scan_build(play)(None, heads, False)
    groups = setup.groups
    if anchors.role == "defender":
        groups = tuple(g for g in groups if g.side == 0) + (_blob_group(1, "Vanguard", heads, 0.0, 0.0, 180.0, "attack_move"),)
    return groups, setup.timeline, setup.unit_types, setup.settings


def placed_scene(layout, play, start_distance, features, counter=False):
    """build(enemy_heads, swap) for `play` placed on `layout` (Rev 4): the defender stands already in shape at its anchor on guard,
    the attacker `start_distance` from the choke on the other side attack-moves at it. Side 0 is the skilled, counter or naive side;
    the defender is side 0 for a defender play and side 1 for an attacker play. `counter` uses a play as the counter it is
    (plays_space.COUNTER_USE). build.labels['placement_shift'] is the signed wu the defender was moved along the corridor axis."""
    if play in NAIVE_PLAYS:
        anchors = _NAIVE_ANCHORS
    else:
        anchors = plays_space.COUNTER_USE.get(play) if counter else None
        anchors = anchors or plays_space.PLAYS[play].anchors
    ds = 0 if anchors.role == "defender" else 1
    s = -1 if ds == 0 else 1
    centre, thick, lane_x, covers = _resolve(layout, features)
    reach = plays.unit_stats("Vanguard")["attack_range"]
    mouth, anchor = _anchor_points(anchors.defender, s, centre, thick, lane_x, covers, reach)
    face_d, face_a = (0.0, 180.0) if s < 0 else (180.0, 0.0)
    attack_x = centre[0] - s * start_distance
    tx = layout.canvas[0] / 2 + s * (start_distance - 500.0) / 2 - centre[0]
    ty = layout.canvas[1] / 2 - centre[1]
    terrain = shift_terrain(layout, tx, ty)

    def build(enemy_heads, swap):
        if enemy_heads < 1:
            raise ValueError("enemy_heads must be at least 1")
        groups, timeline, unit_types, settings = _groups_and_timeline(play, anchors, enemy_heads, swap)
        is_def = [g.side == ds for g in groups]
        d_idx = [i for i, g in enumerate(groups) if g.side == ds]
        positions = _defender_positions(anchors.defender, len(d_idx), mouth, anchor, s)
        placed = list(groups)
        for i, (x, y) in zip(d_idx, positions):
            placed[i] = dataclasses.replace(groups[i], x=x, y=y, facing_deg=face_d, order="guard")
        shift = None
        steps_out = [0] + [k * sign for k in range(1, int(FIT_LIMIT / FIT_STEP) + 1) for sign in (s, -s)]
        for k in steps_out:
            moved = [dataclasses.replace(placed[i], x=placed[i].x + k * FIT_STEP) for i in d_idx]
            if _walkable(layout, moved, SHIFT_MAX) and all(
                    abs(placed[i].x - centre[0]) < 1e-9 or (placed[i].x - centre[0]) * (g.x - centre[0]) > 0 for i, g in zip(d_idx, moved)):
                shift = k * FIT_STEP
                for i, g in zip(d_idx, moved):
                    placed[i] = g
                break
        end_y = 0.0
        if anchors.attacker == "mass_one_end":
            line = next(g for g in placed if g.side == ds)
            end_y = (line.count - 1) * plays_space.SPREAD_SPACING / 2
        for i, g in enumerate(groups):
            if is_def[i]:
                continue
            goal = None
            if anchors.attacker == "mass_one_end":
                goal = (placed[d_idx[0]].x, placed[d_idx[0]].y + end_y)
            placed[i] = dataclasses.replace(g, x=attack_x, y=centre[1] + end_y, facing_deg=face_a, goal=goal)
        steps = tuple(dataclasses.replace(
            t, when=("seen",) if play == "s4_bait" else t.when, goal=None if t.goal is None else (placed[t.group].x + s * abs(t.goal[0] - groups[t.group].x),
                                                 placed[t.group].y + t.goal[1] - groups[t.group].y)) for t in timeline)
        points = [p for i in d_idx for p in formations.place(placed[i].formation, placed[i].count, placed[i].x, placed[i].y,
                                                              placed[i].facing_deg, placed[i].params)]
        hold = (sum(p[0] for p in points) / len(points) + tx, sum(p[1] for p in points) / len(points) + ty)
        build.labels["placement_shift"] = shift
        final = tuple(dataclasses.replace(g, x=g.x + tx, y=g.y + ty, goal=None if g.goal is None else (g.goal[0] + tx, g.goal[1] + ty))
                      for g in placed)
        return Setup(groups=final, unit_types=dict(unit_types), settings=dict(settings), timeline=steps, terrain=terrain,
                     decided_by_survivors=True, silence_ticks=SILENCE_TICKS, defender_side=ds, hold_anchor=hold)
    build.labels = {"placement_shift": None}
    return build
