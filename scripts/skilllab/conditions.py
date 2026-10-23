"""Conditions C0, C1, C2 as pure functions of scans and Thresholds. Definitions are unconfirmed; every detail says so."""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from fractions import Fraction

from scripts.skilllab.contract import CellResult, FightResult, ScanResult
from scripts.skilllab.diagram import SCAN_KINDS
from scripts.skilllab.evidence import DEFAULT_BASIS, Verdict, check_basis, firing_advantage, points
from scripts.skilllab.profile import PROFILE_SKILLS, advantage, beats, subsets, validate


@dataclass(frozen=True)
class MapFiring:
    map_id: str
    offers: frozenset
    mirror: object
    skilled: object
    size: int
    baselines: dict = field(default_factory=dict)


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


def _noise(scan, size, basis):
    cell = _cell_at(scan, size)
    return max((abs(firing_advantage(f, basis)) for f in cell.fights), default=0.0) if cell else 0.0


def _c1_holds(reference, skilled, size, t, basis):
    cell = _cell_at(skilled, size)
    advs = [firing_advantage(f, basis) for f in cell.fights] if cell else []
    return bool(advs) and sum(advs) / len(advs) > _noise(reference, size, basis) + t.c1_min_firing_advantage


def _c1_verdict(code, maps, reference, t, basis, what):
    if not maps:
        return Verdict(code, None, None, t.c1_map_share, what + "; no map offers the play")
    won = sum(1 for m in maps if _c1_holds(reference(m), m.skilled, m.size, t, basis))
    share = won / len(maps)
    return Verdict(code, share >= t.c1_map_share, share, t.c1_map_share, what)


def _c1_what(reference, basis):
    return ("unconfirmed definition: on maps offering the play, the skilled mean firing advantage at equal numbers on the %s "
            "exceeds the largest absolute firing advantage of %s by more than the minimum; share of such maps" % (basis, reference))


def check_c1(maps, skill, t, basis=DEFAULT_BASIS) -> Verdict:
    check_basis(basis)
    offering = [m for m in maps if skill in m.offers]
    return _c1_verdict("C1", offering, lambda m: m.mirror, t, basis, _c1_what("the mirror", basis))


def check_c1_baselines(maps, skill, t, basis=DEFAULT_BASIS) -> list:
    check_basis(basis)
    offering = [m for m in maps if skill in m.offers]
    roles = sorted({r for m in offering for r in m.baselines})
    return [_c1_verdict("C1@" + role, [m for m in offering if role in m.baselines], lambda m, role=role: m.baselines[role], t, basis,
                        _c1_what("the %s baseline" % role, basis))
            for role in roles]


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


def _c2_stats(pts, t):
    xs, ys = [Fraction(p.firing_adv) for p in pts], [Fraction(p.margin) for p in pts]
    rho = _spearman(xs, ys)
    off = 0.0
    if pts:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else Fraction(0)
        limit = Fraction(t.c2_off_trend_margin)
        off = sum(1 for x, y in zip(xs, ys) if abs(y - (my + b * (x - mx))) > limit) / len(pts)
    return rho, off, rho >= t.c2_rank_agreement and off <= t.c2_off_trend_share


def check_c2(scans, t, basis=DEFAULT_BASIS) -> Verdict:
    what = ("unconfirmed definition: Spearman rank correlation of firing advantage (%s) against margin over every pooled "
            "fight, and the share of fights whose margin differs from the least-squares line by more than the margin" % check_basis(basis))
    rho, off, holds = _c2_stats([p for s in scans for p in points(s, basis=basis)], t)
    return Verdict("C2", holds, (rho, off), (t.c2_rank_agreement, t.c2_off_trend_share), what)


def c2_table(scans, t) -> list:
    out = []
    for basis in ("window", "whole"):
        by_heads = {}
        for s in scans:
            for c in s.cells:
                by_heads.setdefault(c.enemy_heads, []).extend(points(s, heads=c.enemy_heads, basis=basis))
        pooled = [p for h in by_heads for p in by_heads[h]]
        if not pooled:
            continue
        for scope, heads, pts in [("pooled", None, pooled)] + [("cell", h, by_heads[h]) for h in sorted(by_heads)]:
            rho, off, holds = _c2_stats(pts, t)
            out.append({"scope": scope, "enemy_heads": heads, "basis": basis, "fights": len(pts), "rho": rho,
                        "off_trend_share": off, "holds": holds})
    return out


_FULL = frozenset(PROFILE_SKILLS)
_EMPTY = frozenset()
_UND = "undecided"


def _b(pm, s):
    return beats(pm.scans[s])


def _c3_map(pm, t):
    for s in subsets():
        if len(s) < 2:
            continue
        parts = [_b(pm, s - {x}) for x in sorted(s)]
        if _b(pm, s) is None or None in parts:
            return False, _UND
        if _b(pm, s) < (1 + t.c3_stack_gain) * max(parts):
            return False, ""
    return True, ""


def _c4_map(pm, t):
    full = advantage(pm, _FULL)
    if full is None or full <= 0:
        return False, "no full-set advantage"
    for x in PROFILE_SKILLS:
        a = advantage(pm, frozenset({x}))
        if a is None:
            return False, _UND
        if a / full > t.c4_max_share:
            return False, ""
    return True, ""


def _c5_map(pm, t):
    full = _b(pm, _FULL)
    if full is None:
        return False, _UND
    if full == 0:
        return False, "no full-set beats"
    for x in PROFILE_SKILLS:
        part = _b(pm, _FULL - {x})
        if part is None:
            return False, _UND
        if (full - part) / full < t.c5_min_loss:
            return False, ""
    return True, ""


def _c6_map(pm, t):
    applicable = False
    for x in sorted(pm.offers):
        adv = advantage(pm, frozenset({x}))
        if adv is None or adv <= 0:
            continue
        applicable = True
        counter = pm.counters.get(x)
        if counter is None or beats(counter) is None:
            return False, _UND
        if (_b(pm, frozenset({x})) - beats(counter)) / adv < t.c6_return_share:
            return False, ""
    return (True, "") if applicable else (None, "")


def _share_verdict(code, what, results, mark) -> Verdict:
    results = [r for r in results if r[0] is not None]
    if not results:
        return Verdict(code, None, None, mark, what + "; no applicable map")
    holding = sum(1 for ok, _ in results if ok)
    und = sum(1 for _, frag in results if frag == _UND)
    nofull = sum(1 for _, frag in results if frag.startswith("no full-set"))
    detail = "%s; %d of %d maps hold; %d undecided" % (what, holding, len(results), und)
    if nofull:
        detail += "; %d with no full-set advantage" % nofull
    share = holding / len(results)
    return Verdict(code, share >= mark, share, mark, detail)


def check_c3(maps, t) -> Verdict:
    what = ("unconfirmed definition: on every subset of two or more skills, beats is at least (1 + gain) times the "
            "best beats with one skill removed; share of maps")
    return _share_verdict("C3", what, [_c3_map(m, t) for m in maps], t.c8_map_share)


def check_c4(maps, t) -> Verdict:
    what = ("unconfirmed definition: each single skill's advantage over the naive control is at most the maximum "
            "share of the full set's advantage; share of maps")
    return _share_verdict("C4", what, [_c4_map(m, t) for m in maps], t.c8_map_share)


def check_c5(maps, t) -> Verdict:
    what = ("unconfirmed definition: removing any one skill from the full set loses at least the minimum fraction "
            "of the full set's beats; share of maps")
    return _share_verdict("C5", what, [_c5_map(m, t) for m in maps], t.c8_map_share)


def check_c6(maps, t) -> Verdict:
    what = ("unconfirmed definition: against the counter play, the skilled side gives back at least the return "
            "share of each offered skill's advantage; share of maps where some offered skill has a positive advantage")
    return _share_verdict("C6", what, [_c6_map(m, t) for m in maps], t.c6_map_share)


def check_c7(maps, t) -> Verdict:
    what = "unconfirmed definition: report only; beats of the full skill set divided by army size, top three maps"
    ratios = sorted(((m.map_id, _b(m, _FULL) / m.size) for m in maps if _b(m, _FULL) is not None),
                    key=lambda r: (-r[1], r[0]))[:3]
    detail = (what + "; " + ", ".join("%s %s" % r for r in ratios)) if ratios else what + "; no map has a decided full-set beats"
    return Verdict("C7", None, ratios, t.c7_ceiling_targets, detail)


def check_c9(maps, t) -> Verdict:
    what = ("unconfirmed definition: report only; (min, median, max, fights outside the bounds) of fight length in "
            "ticks over every full-skill-set fight")
    ticks = sorted(f.ticks for m in maps for c in m.scans[_FULL].cells for f in c.fights)
    if not ticks:
        return Verdict("C9", None, None, t.c9_length_bounds_ticks, what + "; no fights")
    lo, hi = t.c9_length_bounds_ticks
    n = len(ticks)
    median = ticks[n // 2] if n % 2 else (ticks[n // 2 - 1] + ticks[n // 2]) / 2
    outside = sum(1 for k in ticks if k < lo or k > hi)
    return Verdict("C9", None, (ticks[0], median, ticks[-1], outside), t.c9_length_bounds_ticks, what)


def check_c8(maps, t, c1_skills=PROFILE_SKILLS, basis=DEFAULT_BASIS) -> Verdict:
    check_basis(basis)
    what = ("unconfirmed definition: a map holds when C1 (%s) holds for each offered skill among %s and its per-map C3, "
            "C4, C5 and C6 hold (C6 not applicable counts as holding; C2 is set-level and not included); share of maps"
            % (basis, ", ".join(c1_skills)))
    results = []
    for m in maps:
        ok = all(_c1_holds(m.scans[_EMPTY], m.scans[frozenset({x})], m.size, t, basis) for x in sorted(m.offers) if x in c1_skills)
        ok = ok and all(p(m, t)[0] is not False for p in (_c3_map, _c4_map, _c5_map, _c6_map))
        results.append((ok, ""))
    return _share_verdict("C8", what, results, t.c8_map_share)


def _c0_all(maps, t) -> Verdict:
    what = "unconfirmed definition: C0 over the naive control of every open map; all must hold"
    open_maps = [m for m in maps if m.kind == "open"]
    if not open_maps:
        return Verdict("C0", None, None, t.c0_tolerance_units, what + "; no open map given")
    vs = [check_c0(m.scans[_EMPTY], m.size, t) for m in open_maps]
    failing = [m.map_id for m, v in zip(open_maps, vs) if not v.holds]
    detail = what + ("; failing: " + ", ".join(failing) if failing else "")
    return Verdict("C0", not failing, [v.value for v in vs], t.c0_tolerance_units, detail)


def evaluate_all(maps, t, basis=DEFAULT_BASIS) -> list:
    check_basis(basis)
    for m in maps:
        validate(m)
    out = [_c0_all(maps, t)]
    for skill in PROFILE_SKILLS:
        offering = [MapFiring(m.map_id, m.offers, m.scans[_EMPTY], m.scans[frozenset({skill})], m.size, m.baselines)
                    for m in maps if skill in m.offers]
        if offering:
            out.append(replace(check_c1(offering, skill, t, basis), code="C1:" + skill))
            out += [replace(v, code="%s:%s" % (v.code, skill)) for v in check_c1_baselines(offering, skill, t, basis)]
    out.append(check_c2([sc for m in maps for sc in m.scans.values()]
                        + [sc for m in maps for sc in m.counters.values()], t, basis))
    out += [fn(maps, t) for fn in (check_c3, check_c4, check_c5, check_c6, check_c7)]
    out.append(check_c8(maps, t, basis=basis))
    out.append(check_c9(maps, t))
    return out


def evaluate_bases(maps, t) -> dict:
    return {basis: evaluate_all(maps, t, basis) for basis in ("window", "whole")}


# ---- the conditions the rows of a sweep CSV alone support (decision 35) ------------------------------------------------------------

EQUAL_NUMBERS = 16   # decision 35 item 3: C1 reads the equal-numbers cell only


def _fight_of_row(r):
    return FightResult(outcome=r["outcome"], margin=r["margin"], strength_left=(0.0, 0.0), survivors=(0, 0), heads=(0, 0),
                       ticks=r.get("ticks") or 0, first_contact_tick=0, firing=[],
                       firing_unit_seconds=(r["firing_unit_seconds_0"], r["firing_unit_seconds_1"]),
                       firing_window=(r["firing_window_0"], r["firing_window_1"]))


def row_scan(rows) -> ScanResult:
    """Every fight of the rows as the cells of one scan (by enemy_heads), for c2_table; no break-even is claimed."""
    cells = {}
    for r in rows:
        cells.setdefault(r["enemy_heads"], []).append(_fight_of_row(r))
    return ScanResult(size=EQUAL_NUMBERS, cells=[CellResult(h, fs, 0.0, False) for h, fs in sorted(cells.items())], beats=None, loses_to=None)


def row_c1(rows, basis=DEFAULT_BASIS):
    """(lines, missing) of C1 against each naive baseline from CSV rows (grid and refined kinds). Per (family, play, layout, point,
    knob value) and baseline role present in the rows, at enemy_heads EQUAL_NUMBERS: the mean firing advantage of the play's rows
    and the largest absolute firing advantage of the role's rows. A key whose play or role has no row at that cell is in `missing`.
    Sorted by (family, play, layout, point), knob value, role."""
    check_basis(basis)
    play, base, keys = {}, {}, set()
    for r in rows:
        if r.get("kind") not in SCAN_KINDS or r.get("knob_value") is None:
            continue
        series, knob, role = (r["family"], r["play"], r["layout"], r.get("point") or "-"), r["knob_value"], r["baseline"]
        if role != "none":
            keys.add((series, knob, role))
        if r["enemy_heads"] == EQUAL_NUMBERS:
            adv = firing_advantage(_fight_of_row(r), basis)
            (play.setdefault((series, knob), []) if role == "none" else base.setdefault((series, knob, role), [])).append(adv)
    lines, missing = [], []
    for series, knob, role in sorted(keys):
        ours, theirs = play.get((series, knob)), base.get((series, knob, role))
        entry = dict(zip(("family", "play", "layout", "point"), series), knob=knob, role=role)
        if ours and theirs:
            lines.append(dict(entry, advantage=sum(ours) / len(ours), baseline_max=max(abs(a) for a in theirs)))
        else:
            missing.append(entry)
    return lines, missing
