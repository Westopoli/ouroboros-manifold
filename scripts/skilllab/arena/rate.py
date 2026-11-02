"""H-053: the win rate of one layout over its seeds (spec: docs/stories/H-053.md "Interfaces" 1 and 5). A library; `run.py --seeds N` calls it and writes
`<id>.rate.json`. DRAFT-rate-band 0.10 (Westley, 2026-11-01)."""
import math

from scripts.skilllab.catalogue.produce import _roster_ranges

BAND = 0.10


def first_shot(doc):
    """(frame index, unit id) of the first frame in which some unit's hp is lower than in the previous frame, the unit being the lowest id among those that dropped;
    None when no unit is ever hurt."""
    frames = doc["frames"]
    for i in range(1, len(frames)):
        before = {u["id"]: u["hp"] for u in frames[i - 1]["units"]}
        hurt = sorted(u["id"] for u in frames[i]["units"] if u["hp"] < before.get(u["id"], u["hp"]))
        if hurt:
            return i, hurt[0]
    return None


def _firing_capable(doc, ranges):
    """{"A": n, "B": n} for one fight, or None when no shot was fired. DRAFT-firing-capable-at-first-shot (pending Architect; amends Interfaces 5, which read frame 0):
    the units ALIVE at the first-shot frame, at their positions in that frame, whose roster range reaches the first-contact point."""
    shot = first_shot(doc)
    if shot is None:
        return None
    frame, uid = shot
    units = doc["frames"][frame]["units"]
    point = next(u for u in units if u["id"] == uid)
    count = {"A": 0, "B": 0}
    for u in units:
        if u["alive"] and math.hypot(u["x"] - point["x"], u["y"] - point["y"]) <= ranges[u["role"]]:
            count[u["side"]] += 1
    return count


def rate(fights, predict_rate, band=BAND):
    """The rate file's content for the fight dicts of one layout (one per seed)."""
    seeds = [f["seed"] for f in fights]
    wins = lambda w: sum(1 for f in fights if f["result"]["winner"] == w)
    stall_seeds = [f["seed"] for f in fights if f["result"]["winner"] == "stall"]
    none_seeds = [f["seed"] for f in fights if f["result"]["winner"] == "none"]
    rate_a = wins("A") / len(seeds)
    ranges = _roster_ranges()
    capable = [c for c in (_firing_capable(f, ranges) for f in fights) if c]
    ticks = sorted((f["result"]["ticks"], f["seed"]) for f in fights)
    return {"layout_id": fights[0]["layout_id"], "seeds": seeds, "wins_a": wins("A"), "wins_b": wins("B"), "stalls": len(stall_seeds),
            "stall_seeds": stall_seeds, "none_seeds": none_seeds, "rate_a": rate_a, "predict_rate": predict_rate, "band": band,
            "agree": abs(rate_a - predict_rate) <= band and not stall_seeds and not none_seeds,
            "firing_capable": {s: round(sum(c[s] for c in capable) / len(capable), 1) if capable else -1 for s in "AB"},
            "median_seed": ticks[(len(ticks) - 1) // 2][1]}
