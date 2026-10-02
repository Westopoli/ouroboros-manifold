"""Asymmetric plays: a role (blob, line, skilled, counter) and a unit mix per side."""
import math
from dataclasses import dataclass

from scripts.skilllab.contract import Group, Setup
from scripts.skilllab.formations import place
from scripts.skilllab.plays import unit_stats

_ROLES = {"blob": "blob", "line": "line", "skilled": "concave", "counter": "column"}
_ARRANGEMENTS = ("interleaved", "layered")


@dataclass(frozen=True)
class Side:
    role: str
    mix: tuple = (("Vanguard", 1),)
    arrangement: str = "interleaved"


def _params(role, n):
    if role == "blob":
        return {"radius": 80 + 12 * math.sqrt(n)}
    if role == "line":
        return {"spacing": 30}
    if role == "skilled":
        return {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(n)}
    return {"spacing": 30, "cols": 3}


def _split(n, mix):
    """Largest remainder; ties go to the earlier name."""
    total = sum(w for _, w in mix)
    counts = [n * w // total for _, w in mix]
    order = sorted(range(len(mix)), key=lambda i: (-(n * mix[i][1] % total), i))
    for i in order[:n - sum(counts)]:
        counts[i] += 1
    return counts


def _assign(pts, counts, arrangement, dirx):
    """Type index per point, aligned with pts."""
    n = len(pts)
    if arrangement == "layered":
        idx = sorted(range(n), key=lambda i: -dirx * pts[i][0])   # nearest the enemy first
        out = [0] * n
        k = 0
        for t, c in enumerate(counts):
            for i in idx[k:k + c]:
                out[i] = t
            k += c
        return out
    given, out = [0] * len(counts), []
    for k in range(n):
        t = max((t for t in range(len(counts)) if given[t] < counts[t]),
                key=lambda t: (counts[t] * (k + 1) / n - given[t], -t))
        given[t] += 1
        out.append(t)
    return out


def _check(side, size):
    if side.role not in _ROLES:
        raise ValueError("unknown role %r" % (side.role,))
    if side.arrangement not in _ARRANGEMENTS:
        raise ValueError("unknown arrangement %r" % (side.arrangement,))
    if size < 1:
        raise ValueError("size and enemy_heads must be >= 1")
    if not side.mix or any(w <= 0 for _, w in side.mix):
        raise ValueError("mix needs entries with positive weights")


def _local(side, n, idx, anchor_y):
    """Points at x = 0 plus the per-name point lists (mix order, empty names dropped)."""
    f = 0.0 if idx == 0 else 180.0
    pts = place(_ROLES[side.role], n, 0.0, anchor_y, f, _params(side.role, n))
    counts = _split(n, side.mix)
    return pts, counts


def _groups(side, idx, pts, counts, shift, anchor_y):
    f = 0.0 if idx == 0 else 180.0
    if len(side.mix) == 1:
        return [Group(side=idx, unit=side.mix[0][0], count=counts[0], formation=_ROLES[side.role], x=shift,
                      y=anchor_y, facing_deg=f, layer=0, order="attack_move",
                      params=_params(side.role, counts[0]))]
    kinds = _assign(pts, counts, side.arrangement, 1 if idx == 0 else -1)
    out = []
    for t, (name, _) in enumerate(side.mix):
        mine = [(x + shift, y) for (x, y), k in zip(pts, kinds) if k == t]
        if mine:
            out.append(Group(side=idx, unit=name, count=len(mine), formation="points", x=0.0, y=0.0,
                             facing_deg=f, layer=0, order="attack_move", params={"points": mine}))
    return out


def asym_play(size, side0, side1, unit_types=None):
    for s in (side0, side1):
        _check(s, size)
    if side0.role == side1.role == "counter":
        raise ValueError("counter against counter is not defined")

    def build(enemy_heads, swap):
        _check(side1, enemy_heads)
        sides, heads = (side0, side1), (size, enemy_heads)
        types = dict(unit_types or {})
        names = {n for s in sides for n, _ in s.mix}
        gap = max(unit_stats(types.get(n, {}).get("base", n))["sensor_radius"] for n in sorted(names)) + 1
        # a counter needs the enemy's y extent, so the other side is placed first
        anchor_y, local = [0.0, 0.0], [None, None]
        for i in sorted((0, 1), key=lambda i: sides[i].role == "counter"):
            if sides[i].role == "counter":
                ys = [y for _, y in local[1 - i][0]]
                anchor_y[i] = (max(ys) - min(ys)) / 2.0
            local[i] = _local(sides[i], heads[i], i, anchor_y[i])
        shift = (-gap / 2 - max(x for x, _ in local[0][0]), gap / 2 - min(x for x, _ in local[1][0]))
        groups = [_groups(sides[i], i, *local[i], shift[i], anchor_y[i]) for i in (0, 1)]
        for i in (0, 1):
            if sides[i].role == "counter":
                enemy = [p for g in groups[1 - i] for p in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
                goal = max(enemy, key=lambda p: p[1])
                groups[i] = [Group(**{**g.__dict__, "goal": goal}) for g in groups[i]]
        return Setup(groups=tuple(groups[0] + groups[1]), unit_types=types)
    return build


def two_sizes(sizes, side0, side1, unit_types=None):
    sizes = list(sizes)
    if len(sizes) != 2 or sizes[0] == sizes[1] or min(sizes) < 1:
        raise ValueError("two_sizes needs exactly two distinct positive sizes")
    return {s: asym_play(s, side0, side1, unit_types) for s in sizes}
