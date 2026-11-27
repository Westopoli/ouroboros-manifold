# Rule pins: R-091-13, R-091-14 (lab harness story H-091, lab stage 5, piece L2)
"""LAB stage 5, piece L2 (story H-091): `stage5_measures(doc)`, the lab's readings of a facing-on fight file.

Rule words (docs/stories/H-091.md, "L2 measures and the arc check"):
  R-091-13  `stage5_measures(doc)` returns, per side: hits received by class (front, side, rear), the tick of the first hit of each class, and `answer_delay`: for each unit whose first hit
            received is side or rear, the ticks from that hit to that unit's own next shot (null if it never fires), with the median and the maximum.
  R-091-14  `stage5_measures(doc)` returns `climb`: for each unit that climbed, the ticks it spent with `climbing` strictly between 0 and 1, its mean speed there, its mean speed on flat
            ground before the slope, and the ratio; computed only from an every-tick file (otherwise "not measured").

THE API THIS FILE PINS (the story names the function and its contents, not the module or the key names; the test writer's picks, reported; the lab builder builds to it):
    scripts/skilllab/arena/stage5_measures.py (a new file)   stage5_measures(doc) -> dict, `doc` a fight document (a dict as snapshot.read or json.load gives it)
        result["A"], result["B"]   one per side, keyed by the VICTIM's side letter:
            "hits"          {"front": n, "side": n, "rear": n}       hits received, from the frames' `hits` entries (every entry once)
            "first_hit"     {"front": tick|None, "side": ..., "rear": ...}   the `tick` of the first entry of that class received, None when none
            "answer_delay"  {"units": {unit id: ticks | None}, "median": x | None, "max": x | None}
                 units: every unit of the side whose first hit received (earliest `tick`) is side or rear; ticks = the `tick` of that unit's next entry as attacker `a` with a later tick
                 minus the hit's tick, None when it has none; median and max (statistics.median) over the units whose value is not None, None when there are none.
        result["climb"]   "not measured" when the document's frames are not on every tick (ticks not 0, 1, 2 ... last), else {unit id: {"ticks": n, "speed_slope": v, "speed_flat": v, "ratio": r}}
                 for each unit with at least one frame whose `climbing` is strictly between 0 and 1; `ticks` counts those frames; the speed of tick t is the distance in wu from the unit's frame
                 t-1 position to its frame t position, `speed_slope` the mean of those over the counted ticks, `speed_flat` the mean over the ticks t >= 1 before the unit's first counted tick
                 (frames t-1 and t both with `climbing` 0.0, wu a tick), `ratio` speed_slope / speed_flat. A unit that never climbed is absent; no unit climbed gives {}.
Not tested, the story does not say: a unit that fires on the very tick it is first hit (planted fights avoid it: the delay counts shots strictly after the hit), a unit that climbed with no flat
tick before the slope, the forward-difference reading of 'speed of a tick'.

Planted documents (h091_fixtures.planted_doc) have known hits, facings and climbing values, so every expected number below is worked out in the test. Real fights: the FLANK scenes run with
`closeup --facing on` (the earliest hit of a flank is a side or rear hit) and the SLOPE scene; their measures are checked against the same definitions recomputed from the file here.
Green today: the controls on the shape of the planted documents. Red today: everything that calls `stage5_measures`, for the missing module."""
import importlib
import statistics

import pytest

import h063_fixtures as fx
import h091_fixtures as f9

CLASSES = ("front", "side", "rear")


def measures(doc):
    try:
        mod = importlib.import_module("scripts.skilllab.arena.stage5_measures")
    except ModuleNotFoundError as err:
        pytest.fail("L2 not built: %s" % err)
    return mod.stage5_measures(doc)


def ok(pair, what):
    proc, doc = pair
    if proc.returncode != 0 or doc is None:
        pytest.fail("%s: exit %s, no usable fight file; stderr tail %r" % (what, proc.returncode, proc.stderr[-300:]))
    return doc


# --------------------------------------------------------------------------------------------------------------------- the planted fight
# Units 1 to 4 are side A (the holders), 5 to 8 side B. Shots (tick, attacker, victim, off_deg, class):
HITS = [
    (10, 5, 1, 88.0, "side"),    # unit 1: first hit side; it fires back at tick 20 (delay 10)
    (12, 6, 2, 10.0, "front"),   # unit 2: first hit front, so not in answer_delay although ...
    (13, 8, 2, 100.0, "side"),   # ... it is hit from the side next
    (14, 8, 3, 170.0, "rear"),   # unit 3: first hit rear; it fires back at tick 18 (delay 4) and again at 25
    (14, 2, 7, 95.0, "side"),    # unit 7 (side B): first hit side; it never fires
    (15, 6, 4, 20.0, "front"),   # unit 4: first hit front ...
    (16, 5, 4, 60.0, "side"),    # ... then side (first hit still front: not in answer_delay)
    (17, 8, 3, 30.0, "front"),   # unit 3 again (not its first)
    (18, 3, 6, 5.0, "front"),    # unit 3 answers unit 6 (B's first front hit received: tick 18)
    (20, 1, 5, 12.0, "front"),   # unit 1 answers
    (25, 3, 6, 3.0, "front"),
    (30, 6, 1, 150.0, "rear"),   # unit 1 hit again, from the rear
]
SIDES = {1: "A", 2: "A", 3: "A", 4: "A", 5: "B", 6: "B", 7: "B", 8: "B"}
# Worked out. Hits ON side A (victims 1 to 4): tick 10 side, 12 front, 13 side, 14 rear, 15 front, 16 side, 17 front, 30 rear: front 3, side 3, rear 2; first of each class 12, 10, 14.
# Hits ON side B (victims 5 to 8): 14 side (unit 7), 18 front, 20 front, 25 front: front 3, side 1, rear 0; first 18, 14, None.
# First hit of each unit: unit 1 side at 10, unit 2 front at 12, unit 3 rear at 14, unit 4 front at 15; unit 7 side at 14, unit 6 front at 18, unit 5 front at 20. So the units that count
# are 1 and 3 (side A) and 7 (side B). Unit 1's next shot after 10 is at 20 (delay 10); unit 3's after 14 is at 18 (delay 4); unit 7 never fires (None). Side A: median of [10, 4] = 7.0, max 10.
WANT_A = {"hits": {"front": 3, "side": 3, "rear": 2}, "first_hit": {"front": 12, "side": 10, "rear": 14}}
WANT_B = {"hits": {"front": 3, "side": 1, "rear": 0}, "first_hit": {"front": 18, "side": 14, "rear": None}}


def planted(every=1):
    return f9.planted_doc(SIDES, 30, HITS, every=every)


def test_control_the_planted_document_is_what_the_expectations_assume():
    """Control (green today): the planted document has the frames, `hits` and `fired` flags the worked-out numbers below assume: 31 frames, 12 hits in all, unit 1 fires on tick 20 only,
    unit 3 on ticks 18 and 25, unit 7 never."""
    doc = planted()
    shots = {}
    for f in doc["frames"]:
        for u in f["units"]:
            if u["fired"]:
                shots.setdefault(u["id"], []).append(f["tick"])
    assert len(doc["frames"]) == 31 and len(f9.hit_list(doc)) == 12 and shots[1] == [20] and shots[3] == [18, 25] and 7 not in shots


def test_R_091_13_hits_received_by_class_per_side():
    """R-091-13: "per side: hits received by class (front, side, rear)". Planted: side A takes front 3, side B takes front 3, side A side 3, side B side 1, side A rear 2, side B rear 0
    (the victim's side, every entry counted once)."""
    m = measures(planted())
    assert {s: m[s]["hits"] for s in "AB"} == {"A": WANT_A["hits"], "B": WANT_B["hits"]}


def test_R_091_13_tick_of_the_first_hit_of_each_class():
    """R-091-13: "the tick of the first hit of each class". Planted: side A front 12, side 10, rear 14; side B front 18, side 14, rear None (no rear hit received)."""
    m = measures(planted())
    assert {s: m[s]["first_hit"] for s in "AB"} == {"A": WANT_A["first_hit"], "B": WANT_B["first_hit"]}


def test_R_091_13_answer_delay_per_unit_whose_first_hit_is_side_or_rear():
    """R-091-13: "`answer_delay`: for each unit whose first hit received is side or rear, the ticks from that hit to that unit's own next shot ... with the median and the maximum".
    Planted side A: units 1 (side hit at 10, next shot 20: 10) and 3 (rear hit at 14, next shot 18: 4); not unit 2 or unit 4 (their first hit is front, though a side hit follows); median
    7.0, maximum 10."""
    d = measures(planted())["A"]["answer_delay"]
    assert d["units"] == {1: 10, 3: 4} and d["median"] == pytest.approx(7.0) and d["max"] == 10


def test_R_091_13_answer_delay_is_null_for_a_flanked_unit_that_never_fires():
    """R-091-13: "(null if it never fires)". Planted side B: unit 7 is first hit from the side at 14 and never fires, so its delay is None and, with no other flanked unit, the median and
    maximum are None."""
    d = measures(planted())["B"]["answer_delay"]
    assert d == {"units": {7: None}, "median": None, "max": None}


def test_R_091_13_median_and_max_skip_the_units_that_never_answer():
    """R-091-13: the median and the maximum are over the units that answered. Planted: the side A document plus a unit 9 (side A, first hit side at 12, never fires) keeps median 7.0 and max
    10 for units 1 and 3 and lists unit 9 as None."""
    sides = {**SIDES, 9: "A"}
    d = measures(f9.planted_doc(sides, 30, HITS + [(12, 5, 9, 90.0, "side")]))["A"]["answer_delay"]
    assert d["units"] == {1: 10, 3: 4, 9: None} and d["median"] == pytest.approx(7.0) and d["max"] == 10


def test_R_091_13_a_front_only_fight_has_no_answer_delay():
    """R-091-13: no unit's first hit is side or rear: `units` is empty, the median and the maximum None; the front count is the number of hits."""
    doc = f9.planted_doc({1: "A", 2: "B"}, 10, [(3, 2, 1, 0.0, "front"), (5, 2, 1, 10.0, "front"), (6, 1, 2, 4.0, "front")])
    m = measures(doc)
    assert m["A"]["answer_delay"] == {"units": {}, "median": None, "max": None} and m["A"]["hits"] == {"front": 2, "side": 0, "rear": 0} and m["B"]["hits"]["front"] == 1


def test_R_091_13_a_thinned_file_gives_the_same_hit_measures():
    """R-091-13 with R-091-11: the same fight written every 6 ticks (hits placed in the frame that holds their tick) gives the same hits by class, first-hit ticks and answer delays, since
    `hits` carry their own tick."""
    full, thin = measures(planted(1)), measures(planted(6))
    assert {s: full[s] for s in "AB"} == {s: thin[s] for s in "AB"}


def expected(doc):
    """The R-091-13 numbers recomputed from a real document's `hits`, written independently of the measure: {side: {"hits", "first_hit", "delays"}}."""
    side = {u["id"]: u["side"] for u in doc["frames"][0]["units"]}
    entries = sorted(f9.hit_list(doc), key=lambda h: (h["tick"], h["a"], h["v"]))
    out = {s: {"hits": {c: 0 for c in CLASSES}, "first_hit": {c: None for c in CLASSES}, "delays": {}} for s in "AB"}
    first = {}
    for h in entries:
        o = out[side[h["v"]]]
        o["hits"][h["cls"]] += 1
        o["first_hit"][h["cls"]] = o["first_hit"][h["cls"]] if o["first_hit"][h["cls"]] is not None else h["tick"]
        first.setdefault(h["v"], h)
    for v, h in first.items():
        if h["cls"] != "front":
            later = [e["tick"] for e in entries if e["a"] == v and e["tick"] > h["tick"]]
            out[side[v]]["delays"][v] = (min(later) - h["tick"]) if later else None
    return out


@pytest.fixture(scope="module")
def flanks(tmp_path_factory):
    return {ap: f9.closeup_doc(f9.flank_layout("L-9541", ap), tmp_path_factory.mktemp(ap), 1, "--facing", "on") for ap in ("east", "north", "west")}


def flank(flanks, ap):
    return ok(flanks[ap], "closeup --facing on, %s flank" % ap)


@pytest.mark.parametrize("approach", ["east", "north", "west"])
def test_R_091_13_real_flank_fight_matches_the_definitions(approach, flanks):
    """R-091-13, one real fight (the FLANK scene attacked from the front, the side, the rear; facing on, arc 90, every tick): `stage5_measures` equals the hits by class, the first-hit
    ticks and the answer delays recomputed here from the file's `hits`, per side; and the holders' (side A) first hit has the scene's class."""
    doc = flank(flanks, approach)
    m, want = measures(doc), expected(doc)
    for s in "AB":
        assert m[s]["hits"] == want[s]["hits"] and m[s]["first_hit"] == want[s]["first_hit"], s
        got = m[s]["answer_delay"]
        assert got["units"] == want[s]["delays"], s
        values = [v for v in want[s]["delays"].values() if v is not None]
        assert got["median"] == (pytest.approx(statistics.median(values)) if values else None) and got["max"] == (max(values) if values else None), s
    first = {"east": "front", "north": "side", "west": "rear"}[approach]
    ticks = {c: t for c, t in m["A"]["first_hit"].items() if t is not None}
    assert first in ticks and ticks[first] == min(ticks.values()), "first hit of each class on the holders: %s (the earliest should be %s)" % (m["A"]["first_hit"], first)


def test_R_091_13_a_rear_attack_takes_longer_to_answer_than_a_side_attack(flanks):
    """R-091-13 (the staircase's sentence: a flank hits a side and the flanked unit is slow to answer): over the real fights the median answer delay of the holders first hit from the rear is
    longer than of those first hit from the side, both are above 0 (a unit 90 degrees off turns 45 degrees to be inside the arc, one 180 degrees off turns 135)."""
    med = {ap: measures(flank(flanks, ap))["A"]["answer_delay"] for ap in ("north", "west")}
    assert med["north"]["median"] is not None and med["west"]["median"] is not None, med
    assert 0 < med["north"]["median"] < med["west"]["median"], "median delays side %s, rear %s" % (med["north"]["median"], med["west"]["median"])


# --------------------------------------------------------------------------------------------------------------------- R-091-14
def slope_pos(table):
    return lambda uid, t: (table[uid][t], 0.0)


def walk(start, increments):
    xs = [float(start)]
    for d in increments:
        xs.append(xs[-1] + d)
    return xs


CLIMB_X = {9: walk(100.0, [4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 4, 4, 4, 4]),            # flat ticks 1 to 5 at 4, ticks 6 to 9 climbing at 3, tick 10 at the top, flat again
           10: walk(0.0, [4, 4, 2, 2, 1, 2, 3, 2, 4, 4, 4, 4, 4, 4]),            # flat ticks 1 to 4 (mean 3), climbing ticks 5 to 7 (mean 2), the top at 8, flat again
           11: walk(50.0, [4] * 14)}                                            # never climbs
CLIMB_C = {9: {6: 0.2, 7: 0.4, 8: 0.6, 9: 0.8, 10: 1.0}, 10: {5: 0.3, 6: 0.5, 7: 0.9, 8: 1.0}, 11: {}}
CLIMB_SIDES = {9: "B", 10: "A", 11: "A"}


def climb_doc(every=1, last=14):
    return f9.planted_doc(CLIMB_SIDES, last, pos=slope_pos(CLIMB_X), climbing=lambda uid, t: CLIMB_C[uid].get(t, 0.0), every=every)


def test_R_091_14_planted_climb_ticks_speeds_and_ratio():
    """R-091-14: "for each unit that climbed, the ticks it spent with `climbing` strictly between 0 and 1, its mean speed there, its mean speed on flat ground before the slope, and the ratio".
    Planted every-tick document: unit 9 has climbing 0.2, 0.4, 0.6, 0.8 on ticks 6 to 9 (4 ticks; the value 1.0 on tick 10 is not strictly between) moving 3 wu a tick there and 4 wu a tick
    on flat ticks 1 to 5: speeds 3.0 and 4.0, ratio 0.75. Unit 10 has climbing on ticks 5 to 7 (3 ticks) moving 1, 2, 3 (mean 2.0) after flat ticks 1 to 4 moving 4, 4, 2, 2 (mean 3.0): ratio
    2/3. Unit 11 never climbed: absent."""
    c = measures(climb_doc())["climb"]
    assert sorted(c) == [9, 10]
    assert c[9]["ticks"] == 4 and c[9]["speed_slope"] == pytest.approx(3.0) and c[9]["speed_flat"] == pytest.approx(4.0) and c[9]["ratio"] == pytest.approx(0.75)
    assert c[10]["ticks"] == 3 and c[10]["speed_slope"] == pytest.approx(2.0) and c[10]["speed_flat"] == pytest.approx(3.0) and c[10]["ratio"] == pytest.approx(2.0 / 3.0)


def test_R_091_14_not_measured_from_a_file_that_is_not_every_tick():
    """R-091-14: "computed only from an every-tick file (otherwise "not measured")": the same fight written every 2 ticks gives `climb` == "not measured" (the hit measures stay)."""
    m = measures(climb_doc(every=2))
    assert m["climb"] == "not measured" and set(m) >= {"A", "B", "climb"}


def test_R_091_14_no_unit_climbed_gives_an_empty_table():
    """R-091-14: an every-tick fight in which no row has `climbing` between 0 and 1 gives `climb` == {} (the measure ran; nothing climbed)."""
    doc = f9.planted_doc(CLIMB_SIDES, 14, pos=slope_pos(CLIMB_X))
    assert measures(doc)["climb"] == {}


@pytest.fixture(scope="module")
def slope_docs(tmp_path_factory):
    """(every-tick closeup file, run.py thinned file) of the SLOPE scene, facing on."""
    every1 = f9.closeup_doc(f9.slope_layout("L-9542"), tmp_path_factory.mktemp("slope1"), 1, "--facing", "on")
    thin = fx.fight(f9.slope_layout("L-9542"), tmp_path_factory.mktemp("slope_run"), 1, "--facing", "on")
    return every1, thin


def test_R_091_14_real_slope_fight_matches_the_definition(slope_docs):
    """R-091-14, one real fight (the SLOPE scene, facing on, every tick): each attacker (ids 9 to 16) that climbed has the number of ticks with `climbing` strictly between 0 and 1,
    the mean speed over those ticks, the mean flat speed over the ticks before the first of them, and the ratio recomputed here from the rows; the ratio is below 1 (the climb slows the
    walker: dumped before this stage, 3.67 against 3.99 wu a tick, ratio about 0.92); the holders (ids 1 to 8) never climbed and are absent."""
    doc = ok(slope_docs[0], "closeup --facing on, slope scene")
    c = measures(doc)["climb"]
    assert isinstance(c, dict) and sorted(c) and all(9 <= u <= 16 for u in c), c
    table = f9.rows(doc)
    last = max(table)
    for uid, got in c.items():
        xy = [(table[t][uid]["x"], table[t][uid]["y"]) for t in range(last + 1)]
        speed = lambda t: ((xy[t][0] - xy[t - 1][0]) ** 2 + (xy[t][1] - xy[t - 1][1]) ** 2) ** 0.5
        on = [t for t in range(last + 1) if 0.0 < table[t][uid]["climbing"] < 1.0]
        flat = list(range(1, on[0]))
        assert got["ticks"] == len(on), uid
        assert got["speed_slope"] == pytest.approx(sum(speed(t) for t in on) / len(on)), uid
        assert got["speed_flat"] == pytest.approx(sum(speed(t) for t in flat) / len(flat)), uid
        assert got["ratio"] == pytest.approx(got["speed_slope"] / got["speed_flat"]) and got["ratio"] < 1.0, (uid, got)


def test_R_091_14_a_thinned_real_file_is_not_measured(slope_docs):
    """R-091-14: run.py's own thinned file (a frame about every 100 ticks) of the same fight gives `climb` == "not measured"."""
    assert measures(ok(slope_docs[1], "run.py --facing on, slope scene"))["climb"] == "not measured"


def test_R_091_14_a_real_flank_fight_has_no_climb(flanks):
    """R-091-14: the FLANK scene has no slope: `climb` is {} for the every-tick file."""
    assert measures(flank(flanks, "north"))["climb"] == {}
