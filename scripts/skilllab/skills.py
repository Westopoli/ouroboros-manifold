"""Named, pluggable skilled/counter plays per skill (ruling A145). Only the S2 drafts exist, both an unconfirmed draft.
S1, S3, S4, S5 get no play until they are defined with Westley."""
import math
from dataclasses import dataclass

DRAFT = "unconfirmed draft"


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
        raise ValueError("no %r play for skill %r: S1, S3, S4 and S5 plays are defined with Westley later"
                         % (role, skill)) from None


def _concave(ctx):
    """Unconfirmed draft: 120-degree arc curved around the focus; focus None is the middle of the enemy's front."""
    if ctx.focus is None:
        return "concave", {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(ctx.n)}, ctx.facing_deg
    dx, dy = ctx.focus[0] - ctx.anchor[0], ctx.focus[1] - ctx.anchor[1]
    radius = math.hypot(dx, dy)
    if radius <= 0:
        raise ValueError("focus must differ from the side's anchor")
    return "concave", {"arc_deg": 120, "radius": radius}, math.degrees(math.atan2(dy, dx))


def _column(ctx):
    """Unconfirmed draft: 3-wide column; asym puts its anchor level with the end of the enemy front."""
    return "column", {"spacing": 30, "cols": 3}, ctx.facing_deg


register("S2", "skilled", _concave, DRAFT)
register("S2", "counter", _column, DRAFT)
