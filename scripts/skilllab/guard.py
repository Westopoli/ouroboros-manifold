"""Guard cells: degenerate plays the rule set must not be fooled by. Definitions are unconfirmed."""
from __future__ import annotations

from dataclasses import replace

from scripts.skilllab import asym
from scripts.skilllab.asym import Side
from scripts.skilllab.contract import BuildFn, Setup
from scripts.skilllab.evidence import Verdict

GUARD_CELLS = ("all_siege", "camp_top_layer", "max_range_blob")


def guard_play(name, size, siege="Bombard", line="Vanguard", top_layer=4, ranges=None) -> BuildFn:
    if name not in GUARD_CELLS:
        raise ValueError("unknown guard %r" % (name,))
    unit = line
    if name == "all_siege":
        unit = siege
    elif name == "max_range_blob":
        if ranges is None:
            ranges = {n: asym.unit_stats(n)["attack_range"] for n in (line, siege)}
        unit = max(ranges, key=lambda n: ranges[n])
    inner = asym.asym_play(size, Side("blob", ((unit, 1),)), Side("blob", ((line, 1),)))

    def build(enemy_heads, swap):
        s = inner(enemy_heads, swap)
        if name != "camp_top_layer":
            return s
        camp = replace(s.groups[0], layer=top_layer, order="idle")
        return Setup(groups=(camp,) + s.groups[1:], unit_types=s.unit_types)
    return build


def guard_flags(mirror, guard_scans, t) -> list:
    what = ("unconfirmed definition: a guard play flags when its break-even exceeds the mirror's "
            "by more than the tolerance")
    out = []
    for name, scan in guard_scans.items():
        if scan.beats is None or mirror.beats is None:
            out.append(Verdict("guard:" + name, None, None, t.guard_tolerance_units, what + "; a break-even is missing"))
            continue
        diff = scan.beats - mirror.beats
        out.append(Verdict("guard:" + name, diff <= t.guard_tolerance_units, diff, t.guard_tolerance_units, what))
    return out
