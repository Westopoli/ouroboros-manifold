"""SV-2: History, the sim viewer's fold of pipe frames into per-region state, rings,
events, missions and a seeded force layout.

Spec: docs/northstar/plans/2026-10-12-simviewer-spec.md "Shared interfaces".
Tests: tests/simviewer/test_history.py. Tooling only, not the sim: pure stdlib.
"""
import math
import random

LAYOUT_ITERATIONS = 200
LAYOUT_SEED = 1
RING = 60
SIX = ("military", "economy", "tension", "population", "stability", "capacity")


class History:
    def __init__(self):
        self.tick = 0
        self.regions = {}
        self.edges = []
        self.factions = {}
        self.missions = []
        self._rings = {}
        self._events = {}
        self._pending_mission = None
        self._layout = None
        self._layout_key = None

    def apply(self, frame):
        kind = frame.get("type")
        if kind == "snapshot":
            self.tick = frame["tick"]
            self.edges = [(e["a"], e["b"]) for e in frame["edges"]]
            self.factions = {f["id"]: dict(f) for f in frame["factions"]}
            for r in frame["regions"]:
                self._set_region(r, r["tier"])
        elif kind == "delta":
            self.tick = frame["tick"]
            for r in frame["regions"]:
                old = self.regions.get(r["i"])
                self._set_region(r, old["tier"] if old else None)
            for f in frame["factions"]:
                self.factions.setdefault(f["id"], {"id": f["id"]}).update(f)
            for e in frame["events"]:
                self._events.setdefault(e["region"], []).append(
                    {k: e[k] for k in ("tick", "template", "chain", "delta")})
        elif kind == "mission":
            self._pending_mission = frame
        elif kind == "debrief":
            m = self._pending_mission or {}
            self.missions.append({"tick": self.tick, "region": m.get("region"),
                                  "archetype": m.get("archetype"), "band": frame["band"],
                                  "region_delta": frame["region_delta"]})
            self._pending_mission = None

    def _set_region(self, r, tier):
        self.regions[r["i"]] = {"owner": r["owner"], "tier": tier, **{k: r[k] for k in SIX}}
        for k in SIX:
            ring = self._rings.setdefault((r["i"], k), [])
            ring.append(r[k])
            del ring[:-RING]

    def ring(self, region, field):
        return list(self._rings.get((region, field), []))

    def events(self, region):
        return list(self._events.get(region, []))

    @staticmethod
    def diff(before, after):
        keys = ("owner",) + SIX
        return sorted(i for i in set(before) | set(after)
                      if i not in before or i not in after
                      or any(before[i][k] != after[i][k] for k in keys))

    def layout(self):
        key = (tuple(sorted(self.regions)), tuple(sorted(self.edges)))
        if key != self._layout_key:
            self._layout_key = key
            self._layout = _force_layout(key[0], key[1])
        return dict(self._layout)


def _force_layout(nodes, edges):
    """Fruchterman-Reingold on the unit square; every ordering is sorted."""
    rng = random.Random(LAYOUT_SEED)
    pos = {n: [rng.random(), rng.random()] for n in nodes}
    if len(nodes) < 2:
        return {n: (round(p[0], 3), round(p[1], 3)) for n, p in pos.items()}
    k = math.sqrt(1.0 / len(nodes))
    temp = 0.1
    cool = temp / (LAYOUT_ITERATIONS + 1)
    for _ in range(LAYOUT_ITERATIONS):
        disp = {n: [0.0, 0.0] for n in nodes}
        for ai, a in enumerate(nodes):
            for b in nodes[ai + 1:]:
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d = max(math.sqrt(dx * dx + dy * dy), 1e-6)
                f = k * k / d / d
                disp[a][0] += dx * f
                disp[a][1] += dy * f
                disp[b][0] -= dx * f
                disp[b][1] -= dy * f
        for a, b in edges:
            if a == b or a not in pos or b not in pos:
                continue
            dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
            d = max(math.sqrt(dx * dx + dy * dy), 1e-6)
            f = d / k
            disp[a][0] -= dx * f
            disp[a][1] -= dy * f
            disp[b][0] += dx * f
            disp[b][1] += dy * f
        for n in nodes:
            dx, dy = disp[n]
            d = max(math.sqrt(dx * dx + dy * dy), 1e-6)
            step = min(d, temp) / d
            pos[n][0] += dx * step
            pos[n][1] += dy * step
        temp -= cool
    return {n: (round(p[0], 3), round(p[1], 3)) for n, p in pos.items()}
