"""Terrain for a Setup: shifting play coordinates into canvas coordinates (plan Phase S item 5a)."""
import dataclasses
import math

from scripts.skilllab.contract import Terrain

CANVAS_MAX = 28000.0


def shift_terrain(t, dx, dy):
    blocks = tuple(dataclasses.replace(b, x0=b.x0 + dx, y0=b.y0 + dy, x1=b.x1 + dx, y1=b.y1 + dy) for b in t.blocks)
    covers = tuple(dataclasses.replace(c, x=c.x + dx, y=c.y + dy) for c in t.covers)
    return Terrain(canvas=t.canvas, blocks=blocks, covers=covers)


def _validate_terrain(t):
    for side in t.canvas:
        if not (math.isfinite(side) and 0 < side <= CANVAS_MAX):
            raise ValueError("canvas side must be in (0, %d], got %r" % (CANVAS_MAX, side))
    for b in t.blocks:
        if b.x0 == b.x1 or b.y0 == b.y1:
            raise ValueError("block %r has zero area" % (b,))
        if not 0 <= b.layer_lo <= b.layer_hi <= 4:
            raise ValueError("block %r needs 0 <= layer_lo <= layer_hi <= 4" % (b,))
    for c in t.covers:
        if not c.radius > 0:
            raise ValueError("cover %r needs a positive radius" % (c,))
        if not (isinstance(c.height, int) or float(c.height).is_integer()) or not 0 <= c.height <= 5:
            raise ValueError("cover %r needs a whole height 0..5" % (c,))


def _shift_point(p, dx, dy):
    return (p[0] + dx, p[1] + dy)


def _check_inside(p, canvas, what):
    if not (0 <= p[0] <= canvas[0] and 0 <= p[1] <= canvas[1]):
        raise ValueError("%s %r lies outside the canvas %r" % (what, p, canvas))


def with_terrain(build, terrain):
    _validate_terrain(terrain)
    dx, dy = terrain.canvas[0] / 2, terrain.canvas[1] / 2

    def wrapped(enemy_heads, swap):
        setup = build(enemy_heads, swap)
        groups = []
        for g in setup.groups:
            params = dict(g.params)
            if "points" in params:
                params["points"] = [_shift_point(p, dx, dy) for p in params["points"]]
                for p in params["points"]:
                    _check_inside(p, terrain.canvas, "group point")
            goal = None if g.goal is None else _shift_point(g.goal, dx, dy)
            moved = dataclasses.replace(g, x=g.x + dx, y=g.y + dy, goal=goal, params=params)
            _check_inside((moved.x, moved.y), terrain.canvas, "group position")
            if goal is not None:
                _check_inside(goal, terrain.canvas, "group goal")
            groups.append(moved)
        steps = []
        for s in setup.timeline:
            goal = None if s.goal is None else _shift_point(s.goal, dx, dy)
            if goal is not None:
                _check_inside(goal, terrain.canvas, "step goal")
            steps.append(dataclasses.replace(s, goal=goal))
        point = None if setup.point is None else _shift_point(setup.point, dx, dy)
        if point is not None:
            _check_inside(point, terrain.canvas, "setup point")
        return dataclasses.replace(setup, groups=tuple(groups), timeline=tuple(steps), point=point,
                                   terrain=shift_terrain(terrain, dx, dy))

    return wrapped
