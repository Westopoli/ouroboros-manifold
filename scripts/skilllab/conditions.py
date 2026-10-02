"""Conditions C0, C1, C2 as pure functions of scans and Thresholds. Definitions are unconfirmed; every detail says so."""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from scripts.skilllab.evidence import Verdict, firing_advantage, points


@dataclass(frozen=True)
class MapFiring:
    map_id: str
    offers: frozenset
    mirror: object
    skilled: object
    size: int


def _cell_at(scan, heads):
    return next((c for c in scan.cells if c.enemy_heads == heads), None)


def check_c0(mirror, size, t) -> Verdict:
    what = ("unconfirmed definition: every mirror cell below size is won, every cell above is not, and the "
            "break-even sits within the tolerance of size")
    if _cell_at(mirror, size) is None:
        return Verdict("C0", False, mirror.loses_to, t.c0_tolerance_units, what + "; the scan does not cover size")
    ordered = (all(c.won for c in mirror.cells if c.enemy_heads < size)
               and not any(c.won for c in mirror.cells if c.enemy_heads > size))
    near = mirror.loses_to is not None and abs(mirror.loses_to - size) <= t.c0_tolerance_units
    return Verdict("C0", ordered and near, mirror.loses_to, t.c0_tolerance_units, what)


def check_c1(maps, skill, t) -> Verdict:
    what = ("unconfirmed definition: on maps offering the play, the skilled mean firing advantage at equal numbers "
            "exceeds the mirror's largest absolute firing advantage by more than the minimum; share of such maps")
    offering = [m for m in maps if skill in m.offers]
    if not offering:
        return Verdict("C1", None, None, t.c1_map_share, what + "; no map offers the play")
    won = 0
    for m in offering:
        mirror_cell, skilled_cell = _cell_at(m.mirror, m.size), _cell_at(m.skilled, m.size)
        noise = max((abs(firing_advantage(f)) for f in mirror_cell.fights), default=0.0) if mirror_cell else 0.0
        advs = [firing_advantage(f) for f in skilled_cell.fights] if skilled_cell else []
        if advs and sum(advs) / len(advs) > noise + t.c1_min_firing_advantage:
            won += 1
    share = won / len(offering)
    return Verdict("C1", share >= t.c1_map_share, share, t.c1_map_share, what)


def _ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out = [Fraction(0)] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = Fraction(i + j + 2, 2)
        i = j + 1
    return out


def _spearman(xs, ys):
    if len(xs) < 3:
        return 0.0
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return 0.0
    return float(sum((a - mx) * (b - my) for a, b in zip(rx, ry))) / math.sqrt(float(sxx * syy))


def check_c2(scans, t) -> Verdict:
    what = ("unconfirmed definition: Spearman rank correlation of firing advantage against margin over every pooled "
            "fight, and the share of fights whose margin differs from the least-squares line by more than the margin")
    pts = [p for s in scans for p in points(s)]
    xs, ys = [Fraction(p.firing_adv) for p in pts], [Fraction(p.margin) for p in pts]
    rho = _spearman(xs, ys)
    off = 0.0
    if pts:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else Fraction(0)
        limit = Fraction(t.c2_off_trend_margin)
        off = sum(1 for x, y in zip(xs, ys) if abs(y - (my + b * (x - mx))) > limit) / len(pts)
    holds = rho >= t.c2_rank_agreement and off <= t.c2_off_trend_share
    return Verdict("C2", holds, (rho, off), (t.c2_rank_agreement, t.c2_off_trend_share), what)
