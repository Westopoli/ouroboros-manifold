# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI2 (the isolation measures); interface: docs/reports/2026-11-24-li2-interface.md
"""Measures over one fight document (`om-fight-2`), pure Python: no engine, no look-rig import (the overlap rule is copied), no clock.

A cell the file cannot support is a string starting with NOT_MEASURED, never 0 or an empty list. Every `DRAFT_*` value is a proposal; Westley owns the numbers.
`load_fight` streams: the frames of a 230 MB file are decoded one at a time and never held together."""
import json
import math

NOT_MEASURED = "not measured"

DRAFT_OPENING_WINDOW_40 = 40     # DRAFT-opening-window-40: ticks from first contact that count as the opening
DRAFT_STUCK_TICKS = 200          # DRAFT-stuck-ticks: still this long, short of the point, with nothing in notice = orders ended short
DRAFT_IDLE_TICKS_200 = 200       # DRAFT-idle-ticks-200: still this long at the end = idle (the facts' count)
DRAFT_IDLE_FRONT_BEHIND = 40     # DRAFT-idle-front-behind: a living friend this near and nearer the point puts an idle unit behind the firing line
DRAFT_ARRIVED_WU_75 = 75         # DRAFT-arrived-75: within this of orders.point = arrived
DRAFT_STILL_WU_PER_TICK = 0.05   # DRAFT-still: still = moved under this per tick of the frame gap ...
DRAFT_STILL_SLACK_WU = 0.01      # DRAFT-still: ... plus this (r6-compare/tmp/stats.py)
DRAFT_OVERLAP_RADIUS_15 = 15     # DRAFT-overlap-radius: the look rig's check_overlap rule
DRAFT_OVERLAP_MAX_TICKS_3 = 3    # DRAFT-overlap-max-ticks: a run longer than this many frames is listed

# om_constants.h:518-526: category of each role, and the damage multiplier of attacker category against target category
CATEGORY = {"Vanguard": "Line", "Warden": "Line", "Raider": "Strike", "Interceptor": "Strike", "Bombard": "Siege", "Bastion": "Siege"}
MULTIPLIER = {("Line", "Line"): 1.0, ("Line", "Siege"): 0.75, ("Line", "Strike"): 1.5,
              ("Siege", "Line"): 1.5, ("Siege", "Siege"): 1.0, ("Siege", "Strike"): 0.20,
              ("Strike", "Line"): 0.75, ("Strike", "Siege"): 1.5, ("Strike", "Strike"): 1.0}

_CHUNK = 1 << 20
_SPACE = " \t\r\n"


def _nm(why):
    return NOT_MEASURED + ": " + why


def _is_nm(x):
    return isinstance(x, str) and x.startswith(NOT_MEASURED)


# ---------------------------------------------------------------- reading

class _Text:
    """A forward-only window on a text file: decode one JSON value at a time, reading more only when the value is cut by the window."""

    def __init__(self, fh):
        self.fh, self.buf, self.pos, self.eof = fh, "", 0, False
        self.dec = json.JSONDecoder()

    def _more(self):
        chunk = self.fh.read(_CHUNK)
        if not chunk:
            self.eof = True
        self.buf = self.buf[self.pos:] + chunk
        self.pos = 0

    def peek(self):
        """The next non-space character ('' at the end of the file); leaves it unread."""
        while True:
            while self.pos < len(self.buf) and self.buf[self.pos] in _SPACE:
                self.pos += 1
            if self.pos < len(self.buf):
                return self.buf[self.pos]
            if self.eof:
                return ""
            self._more()

    def take(self, ch):
        if self.peek() != ch:
            raise ValueError("fight file: expected %r, found %r" % (ch, self.peek()))
        self.pos += 1

    def value(self):
        self.peek()
        while True:
            try:
                v, end = self.dec.raw_decode(self.buf, self.pos)
            except json.JSONDecodeError:
                if self.eof:
                    raise
                self._more()
                continue
            if end == len(self.buf) and not self.eof and not isinstance(v, (dict, list)):
                self._more()           # a number or literal may continue in the next chunk
                continue
            self.pos = end
            return v


def _keys(t):
    """Yield each top-level key with the reader at its value; the caller must consume the value. Header keys may sit on either side of `frames`."""
    t.take("{")
    while t.peek() != "}":
        key = t.value()
        t.take(":")
        yield key
        if t.peek() == ",":
            t.take(",")


def _frames_of(t):
    t.take("[")
    while t.peek() != "]":
        yield t.value()
        if t.peek() == ",":
            t.take(",")
    t.take("]")


class _Frames:
    """Re-iterable: every iteration re-reads the file and yields one frame at a time."""

    def __init__(self, path):
        self.path = path

    def __iter__(self):
        with open(self.path, encoding="utf-8") as fh:
            t = _Text(fh)
            for key in _keys(t):
                if key == "frames":
                    yield from _frames_of(t)
                    return
                t.value()


def load_fight(path):
    """The fight's top-level keys, and `frames`: a re-iterable that decodes one frame at a time."""
    doc = {}
    with open(path, encoding="utf-8") as fh:
        t = _Text(fh)
        for key in _keys(t):
            if key == "frames":
                for _ in _frames_of(t):
                    pass
            else:
                doc[key] = t.value()
    doc["frames"] = _Frames(path)
    return doc


# ---------------------------------------------------------------- result and margins

def result_of(doc):
    r = doc["result"]
    end, winner = r.get("end"), r.get("winner")
    word = "cap" if (end == "cap" or r.get("capped")) else winner if winner in ("A", "B") else "draw"
    return {"winner": word, "end": end, "survivors": list(r["survivors"]), "last_tick": r["ticks"], "defect": word in ("draw", "cap")}


def survivors(doc):
    return list(doc["result"]["survivors"])


def margin_survivors(doc):
    a, b = survivors(doc)
    return a - b


def margin_hp_share(doc):
    first = last = None
    for frame in doc["frames"]:
        first = frame if first is None else first
        last = frame
    start = {u["id"]: (u["side"], u["hp"]) for u in first["units"]}
    heads = {s: sum(1 for side, _ in start.values() if side == s) for s in "AB"}
    share = {"A": 0.0, "B": 0.0}
    for u in last["units"]:
        if u["hp"] > 0 and start[u["id"]][1] > 0:
            share[u["side"]] += u["hp"] / start[u["id"]][1]
    return share["A"] / heads["A"] - share["B"] / heads["B"]


# ---------------------------------------------------------------- firing

def _has_fired(doc):
    for frame in doc["frames"]:
        return any("fired" in u for u in frame["units"])
    return False


def _no_fired():
    return _nm("the fight file has no per-unit fired flag")


def _firing_rows(doc, weighted):
    """[(tick, ticks since the previous frame, [firing A, firing B], [weighted A, weighted B])], one per frame."""
    rows, prev_tick, sides_roles = [], None, {}
    for frame in doc["frames"]:
        units = frame["units"]
        for u in units:
            sides_roles[u["id"]] = (u["side"], u["role"])
        gap = 0 if prev_tick is None else frame["tick"] - prev_tick
        prev_tick = frame["tick"]
        count, weight = [0, 0], [0.0, 0.0]
        for u in units:
            if not u.get("fired"):
                continue
            s = 0 if u["side"] == "A" else 1
            count[s] += 1
            if weighted:
                target = _target_of(u, units, sides_roles)
                if target is not None:
                    weight[s] += MULTIPLIER[(CATEGORY[u["role"]], CATEGORY[sides_roles[target][1]])]
        rows.append((frame["tick"], gap, count, weight))
    return rows


def _target_of(u, units, sides_roles):
    """The row's target, else the nearest living enemy this frame (squared distance, lower id)."""
    t = u.get("target")
    if t is not None and t in sides_roles and sides_roles[t][0] != u["side"]:
        return t
    best = None
    for v in units:
        if v["alive"] and v["side"] != u["side"]:
            key = ((v["x"] - u["x"]) ** 2 + (v["y"] - u["y"]) ** 2, v["id"])
            if best is None or key < best:
                best = key
    return None if best is None else best[1]


def _unit_seconds(rows, rate, first, window_ticks, field):
    """[A, B] unit-seconds of `field` over all frames (first None) or over [first, first + window_ticks)."""
    return [sum(row[field][s] * row[1] for row in rows if first is None or first <= row[0] < first + window_ticks) / rate for s in (0, 1)]


def _first_contact_of(rows):
    return next((row[0] for row in rows if row[2][0] + row[2][1] > 0), None)


def first_contact_tick(doc):
    if not _has_fired(doc):
        return _no_fired()
    for frame in doc["frames"]:
        if any(u.get("fired") for u in frame["units"]):
            return frame["tick"]
    return None


def units_firing(doc, window_ticks=DRAFT_OPENING_WINDOW_40):
    if not _has_fired(doc):
        return _no_fired()
    rows = _firing_rows(doc, weighted=False)
    rate = doc.get("tick_rate", 20)
    first = _first_contact_of(rows)
    window = [0.0, 0.0] if first is None else _unit_seconds(rows, rate, first, window_ticks, 2)
    return {"by_frame": [[t, count[0], count[1]] for t, _, count, _ in rows], "first_contact": first, "window_ticks": window_ticks,
            "window": window, "whole": _unit_seconds(rows, rate, None, 0, 2),
            "peak": [max(count[0] for _, _, count, _ in rows), max(count[1] for _, _, count, _ in rows)]}


def _leader(a, b):
    return "A" if a > b else "B" if b > a else "tie"


def agreement_word(winner, count, type_):
    if _is_nm(count) or _is_nm(type_):
        return _nm("a prediction is not measured")
    if winner not in ("A", "B") or "tie" in (count, type_):
        return "n/a"
    count_right, type_right = count == winner, type_ == winner
    if count_right and type_right:
        return "both_right"
    if type_right:
        return "count_wrong_type_right"
    return "count_right_type_wrong" if count_right else "both_wrong"


def predictions(doc, window_ticks=DRAFT_OPENING_WINDOW_40):
    if not _has_fired(doc):
        nm = _no_fired()
        return {"count": nm, "type": nm, "window_count": nm, "window_weighted": nm, "agreement": nm}
    rows = _firing_rows(doc, weighted=True)
    rate = doc.get("tick_rate", 20)
    first = _first_contact_of(rows)
    window_count = [0.0, 0.0] if first is None else _unit_seconds(rows, rate, first, window_ticks, 2)
    window_weighted = [0.0, 0.0] if first is None else _unit_seconds(rows, rate, first, window_ticks, 3)
    count, type_ = _leader(*window_count), _leader(*window_weighted)
    return {"count": count, "type": type_, "window_count": window_count, "window_weighted": window_weighted,
            "agreement": agreement_word(result_of(doc)["winner"], count, type_)}


def never_fired(doc):
    if not _has_fired(doc):
        return _no_fired()
    side, fired = {}, set()
    for i, frame in enumerate(doc["frames"]):
        for u in frame["units"]:
            if i == 0:
                side[u["id"]] = u["side"]
            if u.get("fired"):
                fired.add(u["id"])
    n = {s: sum(1 for uid, sd in side.items() if sd == s and uid not in fired) for s in "AB"}
    return {"A": n["A"], "B": n["B"], "total": n["A"] + n["B"], "units_start": len(side)}


# ---------------------------------------------------------------- movement

def _notice(doc, u):
    """How far a unit notices an enemy: its sight when the file has sights, else its weapon range."""
    sights = doc.get("sights")
    if sights and u["role"] in sights:
        return sights[u["role"]]
    return (doc.get("ranges") or {}).get(u["role"], 0.0)


def _still_scan(doc, visit):
    """Walk the frames keeping, for each living unit, the tick its current still-and-targetless run began (`since`). visit(frame, living, since) runs after each frame.
    Returns the last frame's living units, its tick and the runs still open at the end."""
    prev, prev_tick, since = None, None, {}
    for frame in doc["frames"]:
        living = {u["id"]: u for u in frame["units"] if u["alive"]}
        if prev is not None:
            allowed = DRAFT_STILL_WU_PER_TICK * (frame["tick"] - prev_tick) + DRAFT_STILL_SLACK_WU
            for uid, u in living.items():
                p = prev.get(uid)
                if p is not None and math.hypot(u["x"] - p["x"], u["y"] - p["y"]) < allowed and u.get("target") is None:
                    since.setdefault(uid, prev_tick)
                else:
                    since.pop(uid, None)
            for uid in [k for k in since if k not in living]:
                del since[uid]
        prev, prev_tick = living, frame["tick"]
        visit(frame, living, since)
    return prev, prev_tick, since


def orders_ended_short(doc, stuck_ticks=DRAFT_STUCK_TICKS):
    """The file carries no per-unit destination, so this is the fallback of the interface: a unit of the ordered side(s), still and targetless for stuck_ticks,
    DRAFT_ARRIVED_WU_75 or more from orders.point, with no living enemy in notice, at its last living frame."""
    orders = doc.get("orders")
    if not orders or "point" not in orders or orders.get("mode") not in ("both_same_point", "hold_and_attack"):
        return _nm("the fight file carries no destination for these orders")
    ordered = {"A", "B"} if orders["mode"] == "both_same_point" else {orders["attacker"]}
    px, py = orders["point"]
    last = {}   # id -> (short at its last living frame, row)

    def visit(frame, living, since):
        for uid, u in living.items():
            if u["side"] not in ordered:
                continue
            run = since.get(uid)
            short = (run is not None and frame["tick"] - run >= stuck_ticks and math.hypot(u["x"] - px, u["y"] - py) >= DRAFT_ARRIVED_WU_75
                     and not any(v["side"] != u["side"] and math.hypot(v["x"] - u["x"], v["y"] - u["y"]) <= _notice(doc, u) for v in living.values()))
            last[uid] = (short, {"id": uid, "side": u["side"], "x": u["x"], "y": u["y"], "tick": frame["tick"], "since": run})

    at_end, _, _ = _still_scan(doc, visit)
    rows = [(uid, row) for uid, (short, row) in last.items() if short]
    return {"basis": "fallback: still for stuck_ticks, no target, not within 75 wu of orders.point, no enemy in notice",
            "alive_at_end": [row for uid, row in sorted(rows, key=lambda r: r[0]) if uid in at_end],
            "died": [row for uid, row in sorted(rows, key=lambda r: r[0]) if uid not in at_end]}


def idle_units(doc, min_ticks=DRAFT_IDLE_TICKS_200):
    orders = doc.get("orders")
    if not orders or "point" not in orders:
        return _nm("the fight file has no orders.point")
    px, py = orders["point"]
    at_end, last_tick, since = _still_scan(doc, lambda *_: None)
    units = []
    for uid, run in since.items():
        if last_tick - run < min_ticks:
            continue
        u = at_end[uid]
        dist = math.hypot(u["x"] - px, u["y"] - py)
        if dist < DRAFT_ARRIVED_WU_75:
            kind = "arrived"
        elif any(v["side"] == u["side"] and vid != uid and math.hypot(v["x"] - u["x"], v["y"] - u["y"]) < DRAFT_IDLE_FRONT_BEHIND
                 and math.hypot(v["x"] - px, v["y"] - py) < dist for vid, v in at_end.items()):
            kind = "behind"
        else:
            kind = "front"
        units.append({"id": uid, "side": u["side"], "class": kind, "since": run, "x": u["x"], "y": u["y"]})
    units.sort(key=lambda r: r["id"])
    return {"total": len(units), **{k: sum(r["class"] == k for r in units) for k in ("arrived", "behind", "front")}, "units": units}


def spread_at(doc, ticks):
    """{tick: {A: rms distance from the side's centre, B: ...}} for the living, in the order asked."""
    want, got = set(ticks), {}
    for frame in doc["frames"]:
        if frame["tick"] not in want:
            continue
        cell = {}
        for s in "AB":
            pts = [(u["x"], u["y"]) for u in frame["units"] if u["alive"] and u["side"] == s]
            if not pts:
                cell[s] = _nm("no living unit of side %s" % s)
                continue
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            cell[s] = math.sqrt(sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / len(pts))
        got[frame["tick"]] = cell
    return {t: got.get(t, _nm("no frame at tick %d" % t)) for t in ticks}


# ---------------------------------------------------------------- overlap

def overlap_pairs(doc, radius=DRAFT_OVERLAP_RADIUS_15, max_ticks=DRAFT_OVERLAP_MAX_TICKS_3):
    """The look rig's check_overlap rule, copied: same layer, alive, distance strictly under radius; runs counted in frames; a run longer than max_ticks is listed."""
    run, longest, max_per_frame, total = {}, {}, 0, 0
    for frame in doc["frames"]:
        cells = {}
        for u in frame["units"]:
            if u["alive"]:
                cells.setdefault((int(u["x"] // radius), int(u["y"] // radius)), []).append(u)
        now = {}
        for (cx, cy), here in cells.items():
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for a in here:
                        for b in cells.get((cx + dx, cy + dy), ()):
                            if a["id"] < b["id"] and a["layer"] == b["layer"]:
                                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                                if d < radius:
                                    k = (a["id"], b["id"])
                                    before = run.get(k, {"ticks": 0, "min_dist": d})
                                    now[k] = {"ticks": before["ticks"] + 1, "min_dist": min(before["min_dist"], d), "last_tick": frame["tick"]}
        run = now
        max_per_frame, total = max(max_per_frame, len(now)), total + len(now)
        for k, r in now.items():
            if r["ticks"] > max_ticks and (k not in longest or r["ticks"] > longest[k]["ticks"]):
                longest[k] = dict(r)
    pairs = [{"a": k[0], "b": k[1], "ticks": r["ticks"], "last_tick": r["last_tick"], "min_dist": round(r["min_dist"], 3)} for k, r in sorted(longest.items())]
    return {"verdict": "FAIL" if pairs else "PASS", "pairs": pairs, "radius": radius, "max_ticks": max_ticks,
            "max_per_frame": max_per_frame, "total_pair_frames": total}


# ---------------------------------------------------------------- reading of parts against the whole

def reading(parts, whole):
    words = ("pass", "fail", "no stated direction")
    if whole not in words or any(p not in words for p in parts):
        raise ValueError("unknown word in %r, %r" % (list(parts), whole))
    if whole == "no stated direction":
        return "no stated direction"
    stated = [p for p in parts if p != "no stated direction"]
    if all(p == "pass" for p in stated):
        return "all pass" if whole == "pass" else "parts pass and whole fails"
    return "a part fails and the whole crosses" if whole == "pass" else "all fail"


def measure_fight(doc, spread_ticks=()):
    return {"result": result_of(doc), "survivors": survivors(doc), "margin_survivors": margin_survivors(doc), "margin_hp_share": margin_hp_share(doc),
            "first_contact_tick": first_contact_tick(doc), "units_firing": units_firing(doc), "predictions": predictions(doc),
            "never_fired": never_fired(doc), "orders_ended_short": orders_ended_short(doc), "idle_units": idle_units(doc),
            "spread": spread_at(doc, list(spread_ticks)), "overlap": overlap_pairs(doc)}
