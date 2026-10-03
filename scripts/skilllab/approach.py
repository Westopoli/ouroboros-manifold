"""Hold-to-contact opening (Architect ruling A198): attack-moving groups walk as a move group, keeping their
formation slots, to a stop line short of the enemy front, then switch to attack_move on arrival."""
import dataclasses
import math

from scripts.skilllab.contract import Step
from scripts.skilllab.formations import place

ARRIVE = 60.0


def _points(g):
    return place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def _centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def approach_setup(setup, ranges):
    """Return setup with every attack_move group opened as move + an ("arrive", 60) attack_move Step; same object if nothing to do."""
    if setup.approach <= 0:
        return setup
    movers = [i for i, g in enumerate(setup.groups) if g.order == "attack_move"]
    if not movers:
        return setup
    if setup.timeline:
        raise ValueError("approach needs an empty timeline")
    placed = [_points(g) for g in setup.groups]
    side_pts = [[p for g, pts in zip(setup.groups, placed) if g.side == s for p in pts] for s in (0, 1)]
    c0, c1 = _centroid(side_pts[0]), _centroid(side_pts[1])
    norm = math.hypot(c1[0] - c0[0], c1[1] - c0[1])
    if norm == 0:
        return setup
    d = ((c1[0] - c0[0]) / norm, (c1[1] - c0[1]) / norm)
    proj = lambda p: p[0] * d[0] + p[1] * d[1]
    gap = min(proj(p) for p in side_pts[1]) - max(proj(p) for p in side_pts[0])
    stop = setup.approach * min(ranges[g.unit] for g in setup.groups)
    if gap <= stop:
        return setup
    mover_sides = sorted({setup.groups[i].side for i in movers})
    share = (gap - stop) / len(mover_sides)
    groups, steps = list(setup.groups), []
    for i in movers:
        g, sign = setup.groups[i], 1 if setup.groups[i].side == 0 else -1
        cx, cy = _centroid(placed[i])
        groups[i] = dataclasses.replace(g, order="move", goal=(cx + sign * share * d[0], cy + sign * share * d[1]))
        steps.append(Step(group=i, when=("arrive", ARRIVE), order="attack_move", goal=g.goal))
    return dataclasses.replace(setup, groups=tuple(groups), timeline=tuple(steps))
