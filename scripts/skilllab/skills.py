"""Named, pluggable skilled/counter plays per skill. Every entry is a draft (ruling 2026-10-06 supersedes A145 for
registration: S1, S3, S4, S5 are registered too, not measured). Each fn gives side 0's formation for asym_play;
the full plays are in plays_space.py."""
import math
from dataclasses import dataclass

DRAFT = "draft"


@dataclass(frozen=True)
class SideCtx:
    """What a play sees: unit count, side index, anchor in play coordinates, focus (or None), default facing."""
    n: int
    idx: int
    anchor: tuple
    focus: object
    facing_deg: float


@dataclass(frozen=True)
class Play:
    skill: str
    role: str
    fn: object
    status: str


_REGISTRY = {}


def register(skill, role, fn, status):
    _REGISTRY[(skill, role)] = Play(skill, role, fn, status)


def unregister(skill, role):
    get(skill, role)
    del _REGISTRY[(skill, role)]


def get(skill, role):
    try:
        return _REGISTRY[(skill, role)]
    except KeyError:
        raise ValueError("no %r play registered for skill %r" % (role, skill)) from None


def _concave(ctx):
    """Draft: 120-degree arc curved around the focus; focus None is the middle of the enemy's front."""
    if ctx.focus is None:
        return "concave", {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(ctx.n)}, ctx.facing_deg
    dx, dy = ctx.focus[0] - ctx.anchor[0], ctx.focus[1] - ctx.anchor[1]
    radius = math.hypot(dx, dy)
    if radius <= 0:
        raise ValueError("focus must differ from the side's anchor")
    return "concave", {"arc_deg": 120, "radius": radius}, math.degrees(math.atan2(dy, dx))


def _column(ctx):
    """Draft: 3-wide column; asym puts its anchor level with the end of the enemy front."""
    return "column", {"spacing": 30, "cols": 3}, ctx.facing_deg


register("S2", "skilled", _concave, DRAFT)
register("S2", "counter", _column, DRAFT)


def _hold(ctx):
    """Draft S1: a line of the plays_space spacing; the wall and the guard order are in plays_space.s1_hold_choke."""
    return "line", {"spacing": 30}, ctx.facing_deg


def _types_by_reach(ctx):
    """Draft S3: a blob; the layer split and roster mix are in plays_space (s3_layer_above, s3_types_by_reach, s3_over_the_choke, s3_dark_striker, s3_ping_then_commit)."""
    return "blob", {"radius": 80 + 12 * math.sqrt(ctx.n)}, ctx.facing_deg


register("S1", "skilled", _hold, DRAFT)
register("S1", "counter", _types_by_reach, DRAFT)   # draft: a blob; the Bastion mix is in plays_space.s1_outrange
register("S3", "skilled", _types_by_reach, DRAFT)
register("S4", "skilled", _types_by_reach, DRAFT)   # draft: the bait orders are in plays_space.s4_bait
register("S4", "counter", _types_by_reach, DRAFT)   # draft: the guard orders are in plays_space.s4_do_not_chase
register("S5", "skilled", _hold, DRAFT)             # draft: the frail type behind is in plays_space.s5_vulnerable_away


def has_counter(skill):
    return (skill, "counter") in _REGISTRY
