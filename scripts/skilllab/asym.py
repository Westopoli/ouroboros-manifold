"""Asymmetric plays: a role (blob, line, skilled, counter) and a unit mix per side.
A skilled side's groups get a goal that lands the arc's focus on the target (Side.focus, else the enemy's first anchor).
Skilled and counter come from the skills registry; the S2 ones are an unconfirmed draft and every build says so in build.labels."""
import math
from dataclasses import dataclass
from typing import Optional

from scripts.skilllab import skills
from scripts.skilllab.contract import Group, Setup
from scripts.skilllab.formations import place
from scripts.skilllab.plays import max_ticks_for, unit_stats

_ROLES = {"blob": "blob", "line": "line", "skilled": "concave", "counter": "column"}
_ARRANGEMENTS = ("interleaved", "layered", "layered_short_front")


@dataclass(frozen=True)
class Side:
    role: str
    mix: tuple = (("Vanguard", 1),)
    arrangement: str = "interleaved"
    skill: str = "S2"
    focus: Optional[tuple] = None


def _plan(side, n, idx, anchor_y):
    """(formation, params, facing_deg) for one side."""
    f = 0.0 if idx == 0 else 180.0
    if side.role == "blob":
        return "blob", {"radius": 80 + 12 * math.sqrt(n)}, f
    if side.role == "line":
        return "line", {"spacing": 30}, f
    return skills.get(side.skill, side.role).fn(skills.SideCtx(n, idx, (0.0, anchor_y), side.focus, f))


def _split(n, mix):
    """Largest remainder; ties go to the earlier name."""
    total = sum(w for _, w in mix)
    counts = [n * w // total for _, w in mix]
    order = sorted(range(len(mix)), key=lambda i: (-(n * mix[i][1] % total), i))
    for i in order[:n - sum(counts)]:
        counts[i] += 1
    return counts


def _assign(pts, counts, arrangement, dirx, rank=None):
    """Type index per point, aligned with pts. rank orders the types for layered_short_front."""
    n = len(pts)
    if arrangement == "layered_short_front":
        order = sorted(range(len(counts)), key=lambda t: (rank[t], t))
        idx = sorted(range(n), key=lambda i: -dirx * pts[i][0])
        out = [0] * n
        k = 0
        for t in order:
            for i in idx[k:k + counts[t]]:
                out[i] = t
            k += counts[t]
        return out
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
    """Plan, points at x = 0 and the per-name counts."""
    plan = _plan(side, n, idx, anchor_y)
    return plan, place(plan[0], n, 0.0, anchor_y, plan[2], plan[1]), _split(n, side.mix)


def _groups(side, idx, plan, pts, counts, shift, anchor_y, unit_types=None):
    formation, params, f = plan
    if len(side.mix) == 1:
        return [Group(side=idx, unit=side.mix[0][0], count=counts[0], formation=formation, x=shift,
                      y=anchor_y, facing_deg=f, layer=0, order="attack_move", params=params)]
    rank = [unit_stats((unit_types or {}).get(n, {}).get("base", n))["attack_range"] for n, _ in side.mix]
    kinds = _assign(pts, counts, side.arrangement, 1 if idx == 0 else -1, rank)
    out = []
    for t, (name, _) in enumerate(side.mix):
        mine = [(x + shift, y) for (x, y), k in zip(pts, kinds) if k == t]
        if mine:
            out.append(Group(side=idx, unit=name, count=len(mine), formation="points", x=0.0, y=0.0,
                             facing_deg=f, layer=0, order="attack_move", params={"points": mine}))
    return out


def _label(side):
    if side.role in ("blob", "line"):
        return side.role, "naive"
    return "%s:%s" % (side.skill, side.role), skills.get(side.skill, side.role).status


def asym_play(size, side0, side1, unit_types=None):
    for s in (side0, side1):
        _check(s, size)
    if side0.role == side1.role == "counter":
        raise ValueError("counter against counter is not defined")
    labels = {}
    for i, s in enumerate((side0, side1)):
        labels["play_side%d" % i], labels["status_side%d" % i] = _label(s)

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
                ys = [y for _, y in local[1 - i][1]]
                anchor_y[i] = (max(ys) - min(ys)) / 2.0
            local[i] = _local(sides[i], heads[i], i, anchor_y[i])
        shift = (-gap / 2 - max(x for x, _ in local[0][1]), gap / 2 - min(x for x, _ in local[1][1]))
        groups = [_groups(sides[i], i, *local[i], shift[i], anchor_y[i], types) for i in (0, 1)]
        for i in (0, 1):
            if sides[i].role == "counter":
                enemy = [p for g in groups[1 - i] for p in place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
                goal = max(enemy, key=lambda p: p[1])
                groups[i] = [Group(**{**g.__dict__, "goal": goal}) for g in groups[i]]
        for i in (0, 1):
            if sides[i].role == "skilled":
                formation, params, f = local[i][0]
                rad = math.radians(f)
                centre = (shift[i] + params["radius"] * math.cos(rad), anchor_y[i] + params["radius"] * math.sin(rad))
                t = sides[i].focus or (groups[1 - i][0].x, groups[1 - i][0].y)
                goals = []
                for g in groups[i]:
                    pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
                    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
                    goals.append(Group(**{**g.__dict__, "goal": (cx + t[0] - centre[0], cy + t[1] - centre[1])}))
                groups[i] = goals
        return Setup(groups=tuple(groups[0] + groups[1]), unit_types=types, point=(0.0, 0.0),
                     max_ticks=max_ticks_for(size, enemy_heads))
    build.labels = labels
    return build


def two_sizes(sizes, side0, side1, unit_types=None):
    sizes = list(sizes)
    if len(sizes) != 2 or sizes[0] == sizes[1] or min(sizes) < 1:
        raise ValueError("two_sizes needs exactly two distinct positive sizes")
    return {s: asym_play(s, side0, side1, unit_types) for s in sizes}
