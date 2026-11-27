"""Lab stage 5 measures (story docs/stories/H-091.md, R-091-13 and R-091-14): what a `--facing on` fight file says about flank hits and the climb.

`stage5_measures(doc)` -> {"A": side, "B": side, "climb": ...}; `doc` is a fight document (as snapshot.read or json.load gives it).
  side (keyed by the VICTIM's side) = {"hits": {"front": n, "side": n, "rear": n}, "first_hit": {"front": tick | None, ...},
      "answer_delay": {"units": {unit id: ticks | None}, "median": x | None, "max": x | None}}
  `hits` and `first_hit` count every entry of every frame's `hits` once, by the entry's own `tick`, so a thinned file gives the same numbers as an every-tick one. `answer_delay.units` has
  each unit whose first hit received (the earliest by tick, then attacker and victim id) is side or rear: the ticks from that hit to the unit's next shot as attacker at a later tick
  (a shot on the very tick of the hit does not count), None if it has none; `median` (statistics.median) and `max` are over the units that have a value.
  climb = "not measured" unless the frames are on every tick (ticks 0, 1, 2 ... last); else {unit id: {"ticks", "speed_slope", "speed_flat", "ratio"}} for each unit with a frame whose
      `climbing` is strictly between 0 and 1: `ticks` counts those frames, a tick's speed is the distance from the unit's position in frame t-1 to its position in frame t (wu a tick; tick 0 has
      none), `speed_slope` is the mean over the counted ticks, `speed_flat` the mean over the ticks before the unit's first counted tick whose frames t-1 and t both have `climbing` 0.0,
      `ratio` speed_slope / speed_flat (None, with speed_flat None, when no flat tick precedes the slope). {} when no unit climbed.
See also: scripts/skilllab/arena/stage5.py (writes what this reads)."""
import math
import statistics

CLASSES = ("front", "side", "rear")


def _hits(doc):
    """Every entry of every frame's `hits`, once each, ordered by (tick, attacker, victim)."""
    return sorted((h for f in doc["frames"] for h in f.get("hits", [])), key=lambda h: (h["tick"], h["a"], h["v"]))


def _side_measures(entries, side_of, letter):
    mine = [h for h in entries if side_of[h["v"]] == letter]
    first_hit = {c: next((h["tick"] for h in mine if h["cls"] == c), None) for c in CLASSES}
    first = {}
    for h in mine:
        first.setdefault(h["v"], h)
    delays = {}
    for v, h in sorted(first.items()):
        if h["cls"] != "front":
            later = [e["tick"] for e in entries if e["a"] == v and e["tick"] > h["tick"]]
            delays[v] = (later[0] - h["tick"]) if later else None
    answered = [d for d in delays.values() if d is not None]
    return {"hits": {c: sum(1 for h in mine if h["cls"] == c) for c in CLASSES}, "first_hit": first_hit,
            "answer_delay": {"units": delays, "median": statistics.median(answered) if answered else None, "max": max(answered) if answered else None}}


def _climb(doc):
    frames = doc["frames"]
    if [f["tick"] for f in frames] != list(range(len(frames))):
        return "not measured"
    rows = [{u["id"]: u for u in f["units"]} for f in frames]
    out = {}
    for uid in sorted(rows[0]):
        on = [t for t, r in enumerate(rows) if 0.0 < r[uid].get("climbing", 0.0) < 1.0]
        if not on:
            continue
        speed = lambda t: math.hypot(rows[t][uid]["x"] - rows[t - 1][uid]["x"], rows[t][uid]["y"] - rows[t - 1][uid]["y"])
        slope = [speed(t) for t in on if t >= 1]
        flat = [speed(t) for t in range(1, on[0]) if rows[t - 1][uid].get("climbing", 0.0) == 0.0 and rows[t][uid].get("climbing", 0.0) == 0.0]
        speed_slope = sum(slope) / len(slope) if slope else None
        speed_flat = sum(flat) / len(flat) if flat else None
        out[uid] = {"ticks": len(on), "speed_slope": speed_slope, "speed_flat": speed_flat,
                    "ratio": speed_slope / speed_flat if speed_slope is not None and speed_flat else None}
    return out


def stage5_measures(doc):
    """The measures of the module docstring for one `--facing on` fight document."""
    side_of = {u["id"]: u["side"] for u in doc["frames"][0]["units"]}
    entries = _hits(doc)
    return {"A": _side_measures(entries, side_of, "A"), "B": _side_measures(entries, side_of, "B"), "climb": _climb(doc)}
