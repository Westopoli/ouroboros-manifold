# Rule pins: R-091-07, R-091-08, R-091-09, R-091-10, R-091-11 (lab harness story H-091, lab stage 5, piece L1; engine rule E-13 R-100-04)
"""LAB stage 5, piece L1 (story H-091): the lab switch `--facing {off,on}` and `--arc-deg N` of `python -m scripts.skilllab.arena.run`, and what a facing-on fight file carries.

Rule words (docs/stories/H-091.md, "L1 the lab switch and the fight file"):
  R-091-07  `python -m scripts.skilllab.arena.run` takes `--facing {off,on}` (default off) and `--arc-deg N` (default 90, used only with facing on). With facing off, the fight files of
            L-0054, L-0055 with its twin and L-0080 with `--sight on` are byte-identical to the files main writes.
  R-091-08  With facing on, every unit's frame-0 `facing` equals its layout facing (a holder with no facing in the layout faces the enemy's centre of mass; an attacker faces its order
            point), set with `om_unit_set_facing` before the first tick.
  R-091-09  With facing on, the document's top level gains `stage5: {"arc_deg": N, "slope_up_div": V, "front_deg": 45, "rear_deg": 135}` and the sim's `OM_TP_FIRING_ARC_DEG` is N for
            the whole fight.
  R-091-10  With facing on, every unit row gains `climbing`: 0.0 off a slope, otherwise its position along the slope from the foot (0) to the top (1), computed from the slope's record
            and the unit's position (E-01 R-004-06); a unit walking up a slope has `climbing` rising tick by tick and its `layer` changes once.
  R-091-11  With facing on, every frame gains `hits`: one entry `{"a": attacker id, "v": victim id, "tick": T, "off_deg": D, "cls": "front"|"side"|"rear"}` for every shot fired since the
            previous frame, where D is the angle between the victim's facing and the direction from victim to attacker at tick T; in an every-6-ticks file no shot is lost (the count
            equals the every-tick file's).

Premises dumped on this tree (s/lab5-engine e008c38bb, 2026-11-26, facing off, before any lab stage 5 line was written), scenes in h091_fixtures.py:
  FLANK scene, 8 + 8 Vanguards, sight off, seed 1, attackers 200 wu away: the holders (ids 1 to 8) stand at x 1980 and 2020, y 1940 to 2060, facing 0.0 until they hold a target, then turn
  toward it at 0.2 rad a tick (facing is not cosmetic: the face pass turns a unit with a target); first shots on ticks 1 to 4 from both sides; the earliest hit on a holder is front (east
  attack, tick 1), side (north, tick 1, 90.0 degrees) or rear (west, tick 1, 180.0); later first hits on other holders can be of any class; fights end in a wipe at ticks 2377 to 2548
  (A wins east and west, B north, today). With the attackers 700 wu away (`distance`) they walk 400 wu in, the holders turn toward them from tick 79 and the first shot (tick 83) hits a
  holder already turned 45 degrees: the scene of the R-091-08 tests, whose holders keep their layout facing until tick 79.
  SLOPE scene, seed 1: the attackers (ids 9 to 16) walk 3.99 wu a tick on flat ground and 3.67 wu a tick on the ramp (x 1700 to 2300, every attacker within 50 wu of y 2000 there), are on
  the ramp for 162 or 163 ticks each, and each unit's `layer` goes 0 to 1 exactly once (tick 296 to 312, at x about 2198); the holders (x 2700) fire first on tick 346, after the ramp is
  crossed.
Interface assumptions the story leaves open (each is the test writer's pick, reported): the closeup CLI (`scripts.skilllab.arena.closeup`, the only writer of an every-tick or every-6-ticks
file) takes the same `--facing` and `--arc-deg` as run.py and writes the same additions; "at tick T" of a hit's `off_deg` is the victim's facing at the start (frame T-1) or at the end (frame
T) of tick T, positions as frame T has them.
Controls (green today, must stay green): the three pinned fight files written with no flag; a facing-off file has no `stage5`, no `climbing`, no `hits`; the parameter stays 360 with facing
off; layout facing is not applied with facing off (every unit starts facing east)."""
import json
import statistics

import pytest

import h063_fixtures as fx
import h091_fixtures as f9
from scripts.skilllab.engine import Engine

ARC_PARAM = "OM_TP_FIRING_ARC_DEG"


def ok(pair, what):
    """(process, doc) -> doc; a refused or missing run fails the test with the CLI's own words."""
    proc, doc = pair
    if proc.returncode != 0 or doc is None:
        pytest.fail("%s: exit %s, no usable fight file; stdout %r, stderr tail %r" % (what, proc.returncode, proc.stdout[-300:], proc.stderr[-300:]))
    return doc


def spy_arc(monkeypatch):
    """After every engine step of every fight run in this process, append the OM_TP_FIRING_ARC_DEG the world reads; returns the list."""
    seen, real = [], Engine.step

    def step(self, w):
        real(self, w)
        seen.append(self.get_param(w, self.param_id(ARC_PARAM)))
    monkeypatch.setattr(Engine, "step", step)
    return seen


def facing_on(lay, directory, every=None, *extra):
    """A facing-on fight of `lay`: the every-`every`-ticks closeup file, or run.py's thinned file when `every` is None."""
    if every is None:
        return fx.fight(lay, directory, 1, "--facing", "on", *extra)
    return f9.closeup_doc(lay, directory, every, "--facing", "on", *extra)


@pytest.fixture(scope="module")
def north1(tmp_path_factory):
    return facing_on(f9.flank_layout("L-9511", "north"), tmp_path_factory.mktemp("north1"), 1)


@pytest.fixture(scope="module")
def north6(tmp_path_factory):
    return facing_on(f9.flank_layout("L-9511", "north"), tmp_path_factory.mktemp("north6"), 6)


@pytest.fixture(scope="module")
def north_run(tmp_path_factory):
    return facing_on(f9.flank_layout("L-9511", "north"), tmp_path_factory.mktemp("north_run"))


@pytest.fixture(scope="module")
def slope1(tmp_path_factory):
    return facing_on(f9.slope_layout("L-9512"), tmp_path_factory.mktemp("slope1"), 1)


# ------------------------------------------------------------------------------------------------------------------------------ R-091-07

@pytest.mark.parametrize("key", list(f9.PINS))
def test_R_091_07_control_with_no_flag_the_pinned_fight_files_are_what_the_tree_writes(key, tmp_path):
    """R-091-07 CONTROL (green today, must stay green): the pins (h091_fixtures.PINS, recorded before any stage 5 line) are what the tree writes with no flag, so a red below is the missing
    switch and not a moved pin."""
    proc, got = f9.run_pin(key, tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert got == f9.PINS[key][1]


@pytest.mark.parametrize("key", list(f9.PINS))
def test_R_091_07_facing_off_writes_the_pinned_fight_files_byte_for_byte(key, tmp_path):
    """R-091-07: "With facing off, the fight files of L-0054, L-0055 with its twin and L-0080 with `--sight on` are byte-identical to the files main writes." `--facing off` is accepted
    (red today: the runner does not know the flag) and the sha256 of each file (layout_path pinned) is the recorded one."""
    proc, got = f9.run_pin(key, tmp_path, "--facing", "off")
    assert proc.returncode == 0, "run.py refused --facing off: " + proc.stdout[-200:] + proc.stderr[-300:]
    assert got == f9.PINS[key][1]


def test_R_091_07_facing_off_ignores_arc_deg_and_adds_nothing(tmp_path, monkeypatch):
    """R-091-07: "`--arc-deg N` (default 90, used only with facing on)". With `--facing off --arc-deg 60` the file is byte-identical to the file with no flag, carries no `stage5`, no
    `climbing`, no `hits`, and the parameter stays at the engine's 360 for every tick (red today: the flags are unknown)."""
    lay = f9.flank_layout("L-9513", "north")
    base = fx.fight(lay, tmp_path / "base", 1)[1]
    seen = spy_arc(monkeypatch)
    doc = ok(fx.fight(lay, tmp_path / "off", 1, "--facing", "off", "--arc-deg", "60"), "run.py --facing off --arc-deg 60")
    assert json.dumps(dict(doc, layout_path="pinned"), sort_keys=True) == json.dumps(dict(base, layout_path="pinned"), sort_keys=True)   # the two layouts are written in different directories: `layout_path` is the one key that differs
    assert "stage5" not in doc and not any("climbing" in u for f in doc["frames"] for u in f["units"]) and not any("hits" in f for f in doc["frames"])
    assert set(seen) == {360.0} and len(seen) == doc["result"]["ticks"], "the arc parameter left 360 with facing off: %s" % sorted(set(seen))


def test_R_091_07_the_default_is_facing_off_and_the_default_arc_is_90(tmp_path):
    """R-091-07: "`--facing {off,on}` (default off) and `--arc-deg N` (default 90...)". No flag: no `stage5` key (control, green today). `--facing on` alone: `stage5.arc_deg` 90; with
    `--arc-deg 120`: 120 (red today: the flag is unknown)."""
    lay = f9.flank_layout("L-9514", "east")
    assert "stage5" not in fx.fight(lay, tmp_path / "none", 1)[1]
    assert ok(fx.fight(lay, tmp_path / "on", 1, "--facing", "on"), "--facing on")["stage5"]["arc_deg"] == 90
    assert ok(fx.fight(lay, tmp_path / "on120", 1, "--facing", "on", "--arc-deg", "120"), "--facing on --arc-deg 120")["stage5"]["arc_deg"] == 120


# ------------------------------------------------------------------------------------------------------------------------------ R-091-08

def distinct_facings(lay):
    """`lay` with a facing on every unit that no default and no 'toward the enemy' rule gives: holders 1.0 + 0.1 i, attackers -2.0 + 0.05 i (radians, inside -pi..pi)."""
    for i, u in enumerate(lay["side_a"]["units"]):
        u["facing"] = round(1.0 + 0.1 * i, 4)
    for i, u in enumerate(lay["side_b"]["units"]):
        u["facing"] = round(-2.0 + 0.05 * i, 4)
    return lay


def test_R_091_08_control_facing_off_starts_every_unit_facing_east(tmp_path):
    """R-091-08 CONTROL (green today): with facing off the layout's per-row `facing` is not applied (run.py known gap): every unit's frame-0 facing is the engine default 0.0 although the
    layout gives 1.0 + 0.1 i and -2.0 + 0.05 i."""
    doc = fx.fight(distinct_facings(f9.flank_layout("L-9515", "north", 700.0)), tmp_path, 1)[1]
    assert {u["facing"] for u in doc["frames"][0]["units"]} == {0.0}


def test_R_091_08_frame_zero_facing_is_the_layout_facing(tmp_path):
    """R-091-08: "With facing on, every unit's frame-0 `facing` equals its layout facing ... set with `om_unit_set_facing` before the first tick." Each of the sixteen units has its own
    layout facing; the file rounds to 3 decimals. The attackers start 700 wu away, so the holders (no order, no target before tick 79) still have their layout facing on frame 1 (every-tick file): nothing overwrote it."""
    lay = distinct_facings(f9.flank_layout("L-9515", "north", 700.0))
    doc = ok(f9.closeup_doc(lay, tmp_path, 1, "--facing", "on"), "closeup --facing on")
    want = [u["facing"] for u in lay["side_a"]["units"]] + [u["facing"] for u in lay["side_b"]["units"]]
    got0 = [u["facing"] for u in doc["frames"][0]["units"]]
    assert got0 == pytest.approx(want, abs=6e-4), "frame-0 facings %s, layout %s" % (got0, want)
    got1 = [u["facing"] for u in doc["frames"][1]["units"]][:8]
    assert got1 == pytest.approx(want[:8], abs=6e-4), "the holders' facing on tick 1 %s, layout %s" % (got1, want[:8])


def test_R_091_08_a_layout_with_no_facing_faces_the_holder_to_the_enemy_and_the_attacker_to_its_order_point(tmp_path):
    """R-091-08: "(a holder with no facing in the layout faces the enemy's centre of mass; an attacker faces its order point)". The north FLANK scene written with no `facing` key on any
    row: each holder's frame-0 facing is the bearing to side B's centre of mass (from the unit, or from the holder block's centre: the story does not say which, either is taken, to
    1e-3), each attacker's the bearing to `orders.point` (from the unit or from the block's centre). The holders look north (about -1.57), the attackers south (about 1.57), neither east."""
    lay = f9.flank_layout("L-9516", "north")
    proc, doc = f9.run_without_facing(lay, tmp_path, "--facing", "on")
    doc = ok((proc, doc), "run.py --facing on, layout with no facing")
    a, b = doc["frames"][0]["units"][:8], doc["frames"][0]["units"][8:]
    com = lambda us: {"x": sum(u["x"] for u in us) / len(us), "y": sum(u["y"] for u in us) / len(us)}
    point = {"x": doc["orders"]["point"][0], "y": doc["orders"]["point"][1]}
    wrong = []
    for us, to, name in ((a, com(b), "holder"), (b, point, "attacker")):
        for u in us:
            near = min(abs(u["facing"] - f9.bearing(u, to)), abs(u["facing"] - f9.bearing(com(us), to)))
            if near > 1e-3:
                wrong.append((name, u["id"], u["facing"], round(f9.bearing(u, to), 3)))
    assert wrong == [], "units not facing the enemy's centre of mass (holders) or the order point (attackers): %s" % wrong


# ------------------------------------------------------------------------------------------------------------------------------ R-091-09

def test_R_091_09_control_facing_off_file_has_no_stage5_key(tmp_path):
    """R-091-09 CONTROL (green today): a facing-off document has no `stage5` key."""
    assert "stage5" not in fx.fight(f9.flank_layout("L-9517", "east"), tmp_path, 1)[1]


@pytest.mark.parametrize("arc", [60, 120, 360])
def test_R_091_09_stage5_block_and_the_arc_is_set_for_the_whole_fight(arc, tmp_path, monkeypatch):
    """R-091-09: "the document's top level gains `stage5: {"arc_deg": N, "slope_up_div": V, "front_deg": 45, "rear_deg": 135}` and the sim's `OM_TP_FIRING_ARC_DEG` is N for the whole
    fight." Checked per tick: after every engine step of the fight the parameter reads N (and there are as many steps as the result's ticks, so no tick is skipped); V is the engine's
    OM_TP_SLOPE_UP_DIV, 1.1."""
    seen = spy_arc(monkeypatch)
    doc = ok(fx.fight(f9.flank_layout("L-9518", "north"), tmp_path, 1, "--facing", "on", "--arc-deg", str(arc)), "run.py --facing on --arc-deg %d" % arc)
    assert doc["stage5"] == {"arc_deg": arc, "slope_up_div": pytest.approx(1.1), "front_deg": 45, "rear_deg": 135}
    assert len(seen) == doc["result"]["ticks"] and set(seen) == {float(arc)}, "OM_TP_FIRING_ARC_DEG over the fight: %s over %d steps" % (sorted(set(seen)), len(seen))


def test_R_091_09_slope_up_div_is_the_engines_value(tmp_path):
    """R-091-09: `slope_up_div` is V, the fight's OM_TP_SLOPE_UP_DIV; read from a world the library makes (`Engine.get_param`), not typed here."""
    e = Engine()
    w = e.new_world(1)
    try:
        engine_value = e.get_param(w, e.param_id("OM_TP_SLOPE_UP_DIV"))
    finally:
        e.free_world(w)
    doc = ok(fx.fight(f9.flank_layout("L-9518", "east"), tmp_path, 1, "--facing", "on"), "run.py --facing on")
    assert doc["stage5"]["slope_up_div"] == pytest.approx(engine_value)


# ------------------------------------------------------------------------------------------------------------------------------ R-091-10

def test_R_091_10_control_facing_off_rows_have_no_climbing(tmp_path):
    """R-091-10 CONTROL (green today): with facing off no unit row has `climbing`."""
    doc = fx.fight(f9.slope_layout("L-9519"), tmp_path, 1, "--cap-seconds", "30")[1]
    assert not any("climbing" in u for f in doc["frames"] for u in f["units"])


def test_R_091_10_every_row_has_climbing_zero_off_a_slope(tmp_path):
    """R-091-10: "every unit row gains `climbing`: 0.0 off a slope". On the FLANK scene (open flat field, no slope) every row of every frame of the thinned file has `climbing` 0.0, a
    float (red today: the key is missing)."""
    doc = ok(facing_on(f9.flank_layout("L-9520", "east"), tmp_path), "run.py --facing on")
    values = [u.get("climbing") for f in doc["frames"] for u in f["units"]]
    assert values and all(isinstance(v, float) and v == 0.0 for v in values), "climbing values %s" % sorted({repr(v) for v in values})


def test_R_091_10_climbing_is_the_position_along_the_ramp_on_every_tick(slope1):
    """R-091-10: "otherwise its position along the slope from the foot (0) to the top (1), computed from the slope's record and the unit's position". The SLOPE scene's ramp is x 1700
    (foot) to 2300 (top), y 1900 to 2100 (record: x 2000, length 600, width 200, heading 0). On EVERY tick of the every-tick file, for every unit row: a unit strictly inside the ramp
    has climbing (x - 1700) / 600 to 1e-3; a unit outside it (a wu or more past the foot or the sides) has 0.0; past the top (a wu or more) the story's 'off a slope' is 0.0 and 'the top' is
    1.0, and either is accepted there. At least 100 unit-ticks are on the ramp, so the check bites."""
    doc = ok(slope1, "closeup --facing on, slope scene")
    on_ramp, bad = 0, []
    for f in doc["frames"]:
        for u in f["units"]:
            c, inside_y = u.get("climbing"), abs(u["y"] - f9.SLOPE_Y) < f9.SLOPE_HALF_WIDTH - 1.0
            if f9.SLOPE_FOOT + 1.0 < u["x"] < f9.SLOPE_TOP - 1.0 and inside_y:
                on_ramp += 1
                if c is None or abs(c - (u["x"] - f9.SLOPE_FOOT) / (f9.SLOPE_TOP - f9.SLOPE_FOOT)) > 1e-3:
                    bad.append((f["tick"], u["id"], u["x"], c))
            elif u["x"] < f9.SLOPE_FOOT - 1.0 or not inside_y and abs(u["y"] - f9.SLOPE_Y) > f9.SLOPE_HALF_WIDTH + 1.0:
                if c != 0.0:
                    bad.append((f["tick"], u["id"], u["x"], c))
            elif u["x"] > f9.SLOPE_TOP + 1.0 and c not in (0.0, 1.0):
                bad.append((f["tick"], u["id"], u["x"], c))
    assert on_ramp >= 100, "only %d unit-ticks on the ramp (the scene's premise)" % on_ramp
    assert bad == [], "climbing wrong at (tick, unit, x, climbing): %s" % bad[:6]


def test_R_091_10_a_walker_climbing_rises_tick_by_tick_and_its_layer_changes_once(slope1):
    """R-091-10: "a unit walking up a slope has `climbing` rising tick by tick and its `layer` changes once." Per attacker (ids 9 to 16), per tick of the every-tick file: while the unit
    is on the ramp `climbing` never falls and rises on every tick the unit moved forward by 1 wu or more (the key is a float of three decimals or more); over the fight its `layer` goes 0 to 1 once and never back (dumped: it does,
    before this stage, at tick 296 to 312)."""
    doc = ok(slope1, "closeup --facing on, slope scene")
    table = f9.rows(doc)
    ticks = sorted(table)
    for uid in range(9, 17):
        series = [(t, table[t][uid]) for t in ticks]
        ramp = [(t, r) for t, r in series if 0.0 < r.get("climbing", -1.0) < 1.0]
        assert len(ramp) >= 100, "unit %d has %d ticks with climbing strictly between 0 and 1" % (uid, len(ramp))
        for (t0, r0), (t1, r1) in zip(ramp, ramp[1:]):
            if t1 != t0 + 1:
                continue
            assert r1["climbing"] >= r0["climbing"], "unit %d: climbing fell from %s to %s at tick %d" % (uid, r0["climbing"], r1["climbing"], t1)
            if r1["x"] - r0["x"] >= 1.0:
                assert r1["climbing"] > r0["climbing"], "unit %d moved forward on tick %d and climbing did not rise (%s)" % (uid, t1, r1["climbing"])
        changes = [(a[0], a[1]["layer"], b[1]["layer"]) for a, b in zip(series, series[1:]) if a[1]["layer"] != b[1]["layer"]]
        assert [(x, y) for _, x, y in changes] == [(0, 1)], "unit %d layer changes (tick, from, to): %s" % (uid, changes)


# ------------------------------------------------------------------------------------------------------------------------------ R-091-11

def test_R_091_11_control_facing_off_frames_have_no_hits(tmp_path):
    """R-091-11 CONTROL (green today): a facing-off file has no `hits` in any frame, and its `fired` flags are what `hits` is cross-checked against below (some unit fires)."""
    doc = fx.fight(f9.flank_layout("L-9521", "north"), tmp_path, 1)[1]
    assert not any("hits" in f for f in doc["frames"]) and any(u["fired"] for f in doc["frames"] for u in f["units"])


def test_R_091_11_every_frame_has_hits_with_the_five_keys(north1):
    """R-091-11: "every frame gains `hits`: one entry `{"a", "v", "tick", "off_deg", "cls"}`". Every frame of the every-tick file has a `hits` list (frame 0: empty), every entry has exactly
    those five keys with an int a, v and tick, a number off_deg from 0 to 180 and a cls of front, side or rear; the file has hits (a fight with no shot would prove nothing)."""
    doc = ok(north1, "closeup --facing on, north flank")
    assert all(isinstance(f.get("hits"), list) for f in doc["frames"]) and doc["frames"][0]["hits"] == []
    entries = f9.hit_list(doc)
    assert len(entries) > 100, "only %d hits in the fight" % len(entries)
    bad = [h for h in entries if sorted(h) != ["a", "cls", "off_deg", "tick", "v"] or not all(type(h[k]) is int for k in ("a", "v", "tick"))
           or not isinstance(h["off_deg"], (int, float)) or not 0.0 <= h["off_deg"] <= 180.0 or h["cls"] not in ("front", "side", "rear")]
    assert bad == [], bad[:3]


def test_R_091_11_one_entry_per_shot_on_every_tick(north1):
    """R-091-11: "one entry ... for every shot fired since the previous frame". In the every-tick file each frame's `hits` entries carry the frame's own tick, and their attackers are
    the units whose row says `fired` in that frame, once each (plus a unit that died on the tick it fired: its row says not alive, so not `fired`), on every tick of the fight; the victim is the attacker's `target` on that tick or the tick before (the shot may kill
    the target, which the engine then drops)."""
    doc = ok(north1, "closeup --facing on, north flank")
    table, bad = f9.rows(doc), []
    for f in doc["frames"]:
        t = f["tick"]
        shooters = sorted(u["id"] for u in f["units"] if u["fired"])
        got = sorted(h["a"] for h in f["hits"])
        gone = [a for a in got if a not in shooters and table[t][a]["alive"]]   # a shooter killed on the tick it fired has `fired` false (alive and ...): its entry is still owed
        if len(set(got)) != len(got) or gone or any(s not in got for s in shooters) or any(h["tick"] != t for h in f["hits"]):
            bad.append((t, "hits attackers %s, fired rows %s" % (got, shooters)))
            continue
        for h in f["hits"]:
            before = table[t - 1][h["a"]]["target"] if t > 0 else None
            if h["v"] not in (table[t][h["a"]]["target"], before):
                bad.append((t, "attacker %d hit %d, target %s then %s" % (h["a"], h["v"], before, table[t][h["a"]]["target"])))
    assert bad == [], "frames where hits and fired disagree: %s" % bad[:5]


def test_R_091_11_off_deg_is_the_angle_at_the_victim_and_cls_follows_the_thresholds(north1):
    """R-091-11: "D is the angle between the victim's facing and the direction from victim to attacker at tick T"; classes front up to 45, rear from 135, side between
    (DRAFT-stage5-front-deg, DRAFT-stage5-rear-deg). For every hit of the every-tick file D equals that angle computed from the rows (positions of frame T, the victim's facing in frame T
    or in frame T-1: the story says 'at tick T' and the engine's rule reads the facing at the start of the tick), to the file's own rounding (0.25 deg); and `cls` is the class of D: the
    three classes all occur in this fight (the holders are hit from the side, then from the front once they have turned, and the attackers from the front)."""
    doc = ok(north1, "closeup --facing on, north flank")
    table, bad, seen = f9.rows(doc), [], set()
    for h in f9.hit_list(doc):
        t, v, a = h["tick"], table[h["tick"]][h["v"]], table[h["tick"]][h["a"]]
        toward = f9.bearing(v, a)
        mine = [f9.off_deg(table[at][h["v"]]["facing"], toward) for at in (t, t - 1) if at in table]
        if min(abs(h["off_deg"] - m) for m in mine) > f9.ROUND_DEG:
            bad.append((t, h["a"], h["v"], h["off_deg"], [round(m, 2) for m in mine]))
        if h["cls"] != f9.cls_of(h["off_deg"]):
            bad.append((t, h["a"], h["v"], h["off_deg"], h["cls"]))
        seen.add(h["cls"])
    assert bad == [], "off_deg or cls wrong at (tick, a, v, off_deg, ...): %s" % bad[:5]
    assert {"side", "front"} <= seen, "classes seen %s" % sorted(seen)


@pytest.mark.parametrize("approach,first", [("east", "front"), ("north", "side"), ("west", "rear")])
def test_R_091_11_the_first_hit_a_holder_takes_has_the_class_of_the_side_it_came_from(approach, first, tmp_path):
    """R-091-11 (the staircase's sentence: a flank hits a side): in the every-tick file of the FLANK scene attacked from the front (east), the side (north) and the rear (west) the
    earliest hit on the holders (ids 1 to 8; dumped: tick 1 in all three, 0 to 20, 90.0 and 180.0 degrees off) has class front, side, rear in turn, with off_deg within 25 deg of 0, 90 and
    180."""
    doc = ok(f9.closeup_doc(f9.flank_layout("L-9522", approach), tmp_path, 1, "--facing", "on"), "closeup --facing on, %s flank" % approach)
    mine = [h for h in f9.hit_list(doc) if h["v"] <= 8]
    assert mine, "no hit on the holders"
    h = min(mine, key=lambda e: (e["tick"], e["a"]))
    assert h["cls"] == first and abs(h["off_deg"] - {"front": 0, "side": 90, "rear": 180}[first]) <= 25, h


def test_R_091_11_a_thinned_file_loses_no_shot(north1, north6, north_run):
    """R-091-11: "in an every-6-ticks file no shot is lost (the count equals the every-tick file's)". The every-6-ticks closeup file and run.py's own thinned file (about every 100
    ticks) hold the same hits as the every-tick file, entry for entry (a, v, tick, off_deg, cls), each in the frame whose window (the previous frame's tick, this frame's tick] holds
    its tick."""
    full = ok(north1, "closeup every 1")
    key = lambda h: (h["tick"], h["a"], h["v"], h["off_deg"], h["cls"])
    want = sorted(key(h) for h in f9.hit_list(full))
    for pair, name in ((north6, "every 6 ticks"), (north_run, "run.py thinned")):
        doc = ok(pair, name)
        assert len(f9.hit_list(doc)) == len(want), "%s: %d hits, every-tick file %d" % (name, len(f9.hit_list(doc)), len(want))
        assert sorted(key(h) for h in f9.hit_list(doc)) == want, name
        prev = None
        for f in doc["frames"]:
            lo = -1 if prev is None else prev
            assert all(lo < h["tick"] <= f["tick"] for h in f["hits"]), "%s: a hit outside the window of frame %d" % (name, f["tick"])
            prev = f["tick"]


def test_R_091_09_the_arc_the_lab_sets_changes_the_fight(tmp_path):
    """R-091-09 with R-091-01 (the arc reaches the shot): the same north attack with `--arc-deg 90` and `--arc-deg 360`. The holders face east and are attacked from the north, so with the
    arc at 90 each has to turn before it answers: the median tick of the holders' (ids 1 to 8) first shots is later than with 360, read from the `hits` of the every-tick files."""
    lay = f9.flank_layout("L-9523", "north")
    first = {}
    for arc in (90, 360):
        doc = ok(f9.closeup_doc(lay, tmp_path / str(arc), 1, "--facing", "on", "--arc-deg", str(arc)), "closeup --facing on --arc-deg %d" % arc)
        shots = {}
        for h in f9.hit_list(doc):
            if h["a"] <= 8:
                shots.setdefault(h["a"], h["tick"])
        first[arc] = shots
    assert first[90] and first[360], first
    assert statistics.median(first[90].values()) > statistics.median(first[360].values()), "median first shot of a holder: arc 90 %s, arc 360 %s" % (
        statistics.median(first[90].values()), statistics.median(first[360].values()))
