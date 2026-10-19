"""Helpers for the LAB-REV2-BASE tests (decisions 25 and 26): the fill order of a naive blob, blocked-cell reading, and a fake base
build for sweep.default_builds. No engine here."""
import math

from scripts.skilllab import formations
from scripts.skilllab.contract import Block, Group, Setup, Terrain

GOLDEN_ANGLE = 2.399963229728653     # formations._GOLDEN_ANGLE: the fill order of a blob is its Fermat spiral


def radius_of(count):
    """The blob radius every naive scene gives a blob of `count` units (scenes._blob_group, sweep._naive_side)."""
    return 80 + 12 * math.sqrt(count)


def positions(g):
    """Where fight() puts the units of a group: formations.place on the group's own fields (the seam every consumer uses)."""
    return formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)


def in_block(blocks, layer, p):
    """A point stands in a blocked cell of its layer (the pre-flight no_fit reading: bounds inclusive)."""
    return any(b.layer_lo <= layer <= b.layer_hi and b.x0 <= p[0] <= b.x1 and b.y0 <= p[1] <= b.y1 for b in blocks)


def fill_order(n, x, y, radius):
    """The existing fill order of a blob of n units (n >= 2), CONTINUED past its last cell: the anchor first when n is odd, then the
    pairs (p_i, reflection of p_i) of formations._blob, with d_i = radius * sqrt((i + 0.5) / (n // 2)) and angle i * golden angle, for i
    = 0, 1, 2, ... without end. Positions rounded to 6 places as formations._blob rounds. THE TEST WRITER'S READING of decision 26
    ("skips to the next free cell in its existing fill order"): the order is not reshuffled by a skip, the cells beyond the last one of
    the open-ground blob are the next ones of the same spiral (same pairs count, same radius)."""
    pairs = n // 2
    if n % 2:
        yield (float(x), float(y))
    i = 0
    while True:
        d = radius * math.sqrt((i + 0.5) / pairs)
        a = i * GOLDEN_ANGLE
        dx, dy = round(d * math.cos(a), 6), round(d * math.sin(a), 6)
        yield (float(x + dx), float(y + dy))
        yield (float(x - dx), float(y - dy))
        i += 1


def expected_skipping(g, blocks):
    """The positions a naive blob group g holds when its next cell is skipped while blocked: the first g.count free cells of fill_order."""
    out = []
    for p in fill_order(g.count, g.x, g.y, radius_of(g.count)):
        if not in_block(blocks, g.layer, p):
            out.append(p)
            if len(out) == g.count:
                return out
    raise AssertionError("fill order exhausted")      # unreachable: the sequence never ends


def keyed(pts, nd=4):
    return sorted((round(p[0], nd), round(p[1], nd)) for p in pts)


def slab_through(g, dx0, dx1, dy0, dy1, layer_lo=0, layer_hi=4):
    """A wall in FINAL coordinates through group g's blob: x from g.x + dx0 to g.x + dx1, y from g.y + dy0 to g.y + dy1."""
    return Block(g.x + dx0, g.y + dy0, g.x + dx1, g.y + dy1, layer_lo, layer_hi)


def fake_base(groups, blocks=(), label="ok", canvas=(4000.0, 4000.0), point=(2000.0, 1000.0)):
    """A stand-in for scenes.placed_scene's return: build(enemy_heads, swap) -> Setup of `groups` on a hand-built terrain, whose
    labels['prefight'] is `label` whatever the Setup is (a base that is wrong about itself on purpose)."""
    def build(enemy_heads, swap):
        build.labels["prefight"] = label
        return Setup(groups=tuple(groups), unit_types={}, terrain=Terrain(canvas=canvas, blocks=tuple(blocks)), point=point)
    build.labels = {"placement_shift": 0.0, "prefight": None}
    return build


def vg(side, unit, count, x, y, layer=0, order="attack_move", facing=0.0):
    return Group(side=side, unit=unit, count=count, formation="blob", x=x, y=y, facing_deg=facing, layer=layer, order=order,
                 params={"radius": radius_of(count)})
