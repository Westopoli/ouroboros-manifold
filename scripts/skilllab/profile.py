"""The 32-combination skill profile: every subset of the five skills against the naive control."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Optional

PROFILE_SKILLS = ("S1", "S2", "S3", "S4", "S5")


def subsets() -> list:
    return [frozenset(c) for r in range(len(PROFILE_SKILLS) + 1) for c in itertools.combinations(PROFILE_SKILLS, r)]


@dataclass
class ProfileMap:
    map_id: str
    kind: str
    offers: frozenset
    size: int
    scans: dict      # skill subset -> ScanResult, side 0 applying exactly those skills; scans[frozenset()] is the naive control
    counters: dict   # skill -> ScanResult: that skill alone against the counter play
    baselines: dict = field(default_factory=dict)


def beats(scan) -> Optional[int]:
    return scan.beats


def advantage(pm, s) -> Optional[int]:
    a, b = beats(pm.scans[s]), beats(pm.scans[frozenset()])
    return None if a is None or b is None else a - b


def skill_profile(maps) -> list:
    rows = []
    for s in subsets():
        advs = [a for a in (advantage(pm, s) for pm in maps) if a is not None]
        rows.append({"skills": tuple(sorted(s)), "maps": len(advs),
                     "mean_advantage": sum(advs) / len(advs) if advs else None})
    return rows


def validate(pm) -> None:
    missing = [s for s in subsets() if s not in pm.scans]
    if missing:
        raise ValueError("map %s lacks %d of the 32 subsets" % (pm.map_id, len(missing)))
    if pm.size < 1:
        raise ValueError("map %s has size %d" % (pm.map_id, pm.size))
    if not set(pm.offers) <= set(PROFILE_SKILLS):
        raise ValueError("map %s offers unknown skills" % pm.map_id)
    if not set(pm.counters) <= set(pm.offers):
        raise ValueError("map %s has counters for skills it does not offer" % pm.map_id)
