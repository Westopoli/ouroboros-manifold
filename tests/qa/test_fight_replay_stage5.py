# spec: docs/stories/H-091.md::R1 replay::R-091-18 to R-091-22
# Rule pins: none (lab stage 5, story H-091; R-091-NN are lab rules)
"""LAB stage 5, piece R1 (story H-091, rules R-091-18 to R-091-22): the replay draws arcs, hit marks, a climb bar and a band mark
(scenes/proto/fight_replay/fight_replay.gd, new file scenes/proto/fight_replay/replay_arcs.gd).

Everything of stage 5 is gated on the top-level `stage5` key, as the stage 4 sight drawing is gated on `seen`. The fight files are hand-written JSON (not run through the arena;
the checker does not know the stage 5 keys yet, R-091-12), staged from `snapshot.example` (valid before the stage 5 keys go in, asserted): 4 frames 100 ticks apart, 8 units
(ids 1 to 4 side A, 5 to 8 side B; Vanguard, Vanguard, Raider, Raider on each side), landscape small_tiered (it has the bands), nobody dead until unit 4 dies on the last frame.
The file's fields are those fixed by the story: top-level `stage5 {arc_deg, slope_up_div, front_deg, rear_deg}` (R-091-09, arc_deg 120 so the number is read from the file and is
not the 90 default), per-unit `climbing` (R-091-10), per-frame `hits [{a, v, tick, off_deg, cls}]` (R-091-11).

Premises read from the scene today (dumped, not assumed): `qa_state()` carries `hud_tick`, `hollow_units`, `glyphs` and none of `arcs`, `hit_marks`, `climbing_units`, `band_marks`;
the HUD and the legend are Label controls read from the daemon's `hud_texts`; keys Space/Right, Left step, R and V toggle, C is unbound.

What `qa_state()` gives for the drawing itself is `drawn5` (the geometry and colours `_draw_stage5` put on the overlay, read back from what it drew): the wedge's length and span, the hit
colours, the climb bar's fill fraction, the band colours. Only the exact band colours are not asserted (the story names none: band 0 and band 1 differ, a band's units share one). Premise taken where the story is silent: `qa_state().arcs` lists the wedges drawn, so after key C (wedges off) it is `[]`; the HUD totals line is a
Label of its own whose text is `front N  side N  rear N`; the legend rows are Labels whose text names the arc, the three classes, the climb and the bands (checked by word, the
story gives no row text); the running totals are the hits of frames 0 up to the one shown (so they fall when a frame is stepped back)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from test_fight_replay import _hud_lines, _key, _open, _state, _write_fight  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402

NEW_KEYS = ("arcs", "hit_marks", "climbing_units", "band_marks")
ARC_DEG = 120.0
FRAMES = 4
TOTALS = re.compile(r"front (\d+)  side (\d+)  rear (\d+)")
STAGE3_TICK = "tick %d  A %d  B %d  blocked 0  frame %d/%d"

# Hits per frame, (attacker, victim, tick, off_deg, cls): frame 0 none; frame 1 a front and a side; frame 2 none; frame 3 a rear and a front on one victim (3) and a side.
HITS = {0: [], 1: [(5, 1, 60, 10.0, "front"), (6, 2, 80, 90.0, "side")], 2: [],
        3: [(7, 3, 250, 170.0, "rear"), (5, 3, 280, 30.0, "front"), (1, 6, 300, 100.0, "side")]}
# The running totals the HUD line shows on each frame (front, side, rear).
RUNNING = {0: (0, 0, 0), 1: (1, 1, 0), 2: (1, 1, 0), 3: (2, 2, 1)}
# `climbing` per frame, {unit id: value}; every other unit is 0.0. Unit 1 climbs; unit 3 reaches exactly 1.0 on frame 1 (not strictly between); unit 2 is at 0.25 on frame 2.
CLIMB = {0: {}, 1: {1: 0.5, 3: 1.0}, 2: {1: 0.5, 2: 0.25}, 3: {1: 1.0}}
# Units whose layer is 1 per frame: 3 and 7 always; unit 2 moves up on frame 2 (its layer changes once).
UP = {0: {3, 7}, 1: {3, 7}, 2: {2, 3, 7}, 3: {2, 3, 7}}
FACING_A = {1: 0.0, 2: 0.4, 3: -0.8, 4: 1.2}
FACING_B = {5: 3.1, 6: 2.5, 7: -2.9, 8: 2.0}


def stage5_doc(with_key: bool = True) -> dict:
    """The 4-frame, 8-unit fight with the stage 5 fields; `with_key` False leaves the top-level `stage5` key out and keeps `climbing` and `hits` (the file the replay must not draw)."""
    doc = snapshot.example(frames=FRAMES, units_per_side=4, schema=snapshot.SCHEMA_V2)
    roles = ["Vanguard", "Vanguard", "Raider", "Raider"]
    for n, f in enumerate(doc["frames"]):
        for u in f["units"]:
            k = (u["id"] - 1) % 4
            u["role"], u["hp"], u["alive"] = roles[k], 100.0, True
            u["x"], u["y"] = (100.0 + 40.0 * k) if u["side"] == "A" else (700.0 + 40.0 * k), 100.0 + 90.0 * k
            u["facing"] = (FACING_A if u["side"] == "A" else FACING_B)[u["id"]] + (0.3 * n if u["id"] == 1 else 0.0)
            u["layer"] = 1 if u["id"] in UP[n] else 0
        f["tick"] = 100 * n
        f["alive"] = [4, 4]
        if n == FRAMES - 1:
            f["units"][3].update({"hp": 0.0, "alive": False})
            f["alive"] = [3, 4]
    doc["ranges"] = {"Raider": 150.0, "Vanguard": 250.0}
    doc["landscape"] = "small_tiered"
    doc["result"].update({"winner": "draw", "survivors": [3, 4], "ticks": 300, "capped": True, "agree": False, "end": "cap", "stall": False})
    assert snapshot.validate(doc) == [], snapshot.validate(doc)
    for n, f in enumerate(doc["frames"]):
        for u in f["units"]:
            u["climbing"] = CLIMB[n].get(u["id"], 0.0)
        f["hits"] = [{"a": a, "v": v, "tick": t, "off_deg": d, "cls": c} for a, v, t, d, c in HITS[n]]
    if with_key:
        doc["stage5"] = {"arc_deg": ARC_DEG, "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135}
    return doc


def _collect(g) -> dict:
    """Walk the open scene: frames 0 to 3 forward ({i: {"qa", "lines"}}), then Left twice to frame 1 (`back`), then key C (`c_off`) and key C again (`c_on`), all on frame 1."""
    out = {"frames": {}}
    for i in range(FRAMES):
        st = _state(g, lambda q, i=i: q.get("frame") == i, timeout=15.0, label="frame %d" % i)
        out["frames"][i] = {"qa": st["qa"], "lines": _hud_lines(st)}
        if i < FRAMES - 1:
            _key(g, "Space")
    for _ in range(2):
        _key(g, "Left")
    for name, key in (("back", None), ("c_off", "C"), ("c_on", "C")):
        if key:
            _key(g, key)
        st = _state(g, lambda q: q.get("frame") == 1, timeout=15.0, label="frame 1 after %s" % name)
        out[name] = {"qa": st["qa"], "lines": _hud_lines(st)}
    return out


def _session(tmp_path_factory, name: str, doc: dict) -> dict:
    path = _write_fight(tmp_path_factory.mktemp(name) / "L-0001-s1.fight.json", doc)
    with pytest.MonkeyPatch.context() as mp:
        g = _open(mp, path)
        try:
            g.wait_for_port(timeout=90.0)
            return _collect(g)
        finally:
            g.stop()


@pytest.fixture(scope="module")
def s5(tmp_path_factory) -> dict:
    """One run of the scene on the stage 5 file (the scene is launched once for the module, as the stage 4 tests launch it once per test)."""
    return _session(tmp_path_factory, "s5", stage5_doc())


@pytest.fixture(scope="module")
def nokey(tmp_path_factory) -> dict:
    """One run of the scene on the same file with the top-level `stage5` key taken out (`climbing` and `hits` stay in)."""
    return _session(tmp_path_factory, "nokey", stage5_doc(with_key=False))


def living(doc: dict, n: int) -> list[dict]:
    return [u for u in doc["frames"][n]["units"] if u["alive"]]


def _arcs(qa: dict):
    """Sorted (id, facing, arc_deg) of `qa_state().arcs`, None when the key is missing."""
    if not isinstance(qa.get("arcs"), list):
        return None
    return sorted((e.get("id"), round(float(e.get("facing", float("nan"))), 4), round(float(e.get("arc_deg", float("nan"))), 4)) for e in qa["arcs"])


def _want_arcs(doc: dict, n: int) -> list:
    return sorted((u["id"], round(u["facing"], 4), ARC_DEG) for u in living(doc, n))


DOC = stage5_doc()


# ---------------------------------------------------------------- control (green today)

def test_control_stage5_fixture_is_a_valid_fight_and_the_scene_opens_it_with_the_stage_4_keys(s5):
    """CONTROL (green today): the staged file is valid before its stage 5 keys go in (asserted in `stage5_doc`), the replay opens it with `frame_count` 4 and the stage 4 keys it
    already has (`hollow_units`, `hud_tick`, `glyphs`), steps through all four frames with the alive counts of the file, and the fixture's premises hold (hits on frames 1 and 3
    only, a climb on frames 1 and 2, unit 4 dead on the last frame), so a red below is the missing stage 5 drawing and not a bad file."""
    qas = [s5["frames"][i]["qa"] for i in range(FRAMES)]
    assert [q["frame_count"] for q in qas] == [FRAMES] * FRAMES
    assert [[q["alive_a"], q["alive_b"]] for q in qas] == [f["alive"] for f in DOC["frames"]]
    assert all(k in qas[0] for k in ("hollow_units", "hud_tick", "glyphs")) and len(qas[0]["glyphs"]) == 6
    assert [len(h) for h in HITS.values()] == [0, 2, 0, 3] and [len(c) for c in CLIMB.values()] == [0, 2, 2, 1]
    assert [u["id"] for u in DOC["frames"][3]["units"] if not u["alive"]] == [4]


# ---------------------------------------------------------------- R-091-18 arcs

def test_r_091_18_one_arc_wedge_per_living_unit_centred_on_its_facing_the_files_arc_deg_wide(s5):
    """R-091-18: "Given a fight file with a `stage5` key, Then the replay draws one arc wedge per living unit (centred on its facing, the file's `arc_deg` wide, as long as that
    role's range) and `qa_state().arcs` lists `{id, facing, arc_deg}` for each". Every frame: `arcs` has one entry per living unit with the unit's facing in that frame (unit 1's
    facing changes each frame) and the file's `arc_deg` (120, not the 90 default). The wedge's length is asserted on the drawn geometry (`drawn5`) below."""
    got = {i: _arcs(s5["frames"][i]["qa"]) for i in range(FRAMES)}
    assert got == {i: _want_arcs(DOC, i) for i in range(FRAMES)}, "qa_state().arcs per frame: %r" % {i: s5["frames"][i]["qa"].get("arcs") for i in range(FRAMES)}


def test_r_091_18_a_dead_unit_has_no_wedge(s5):
    """R-091-18, "one arc wedge per living unit": on the last frame unit 4 is dead, so `arcs` has 7 entries and none has id 4 (frames 0 to 2: 8 entries, id 4 present)."""
    arcs = [s5["frames"][i]["qa"].get("arcs") for i in range(FRAMES)]
    assert [None if a is None else (len(a), 4 in [e["id"] for e in a]) for a in arcs] == [(8, True), (8, True), (8, True), (7, False)], arcs


def test_r_091_18_a_file_without_the_stage5_key_draws_nothing_new_and_carries_none_of_the_new_qa_keys(nokey):
    """R-091-18: "given a file without the key, nothing new is drawn and `qa_state()` carries none of the new keys". The same file with `climbing` and `hits` but no `stage5` key:
    on every frame `qa_state()` has none of `arcs`, `hit_marks`, `climbing_units`, `band_marks`, and no Label holds a `front N  side N  rear N` line. Positive control in the
    same state: the stage 4 keys are there, so the state is the replay's own."""
    qas = [nokey["frames"][i]["qa"] for i in range(FRAMES)]
    assert all("hollow_units" in q and "hud_tick" in q for q in qas), "premise: the state is the replay's"
    assert [[k for k in NEW_KEYS if k in q] for q in qas] == [[]] * FRAMES
    assert [[t for t in nokey["frames"][i]["lines"] if TOTALS.fullmatch(t)] for i in range(FRAMES)] == [[]] * FRAMES


def test_r_091_18_the_wedges_are_drawn_by_the_new_file_replay_arcs_gd():
    """R-091-18 and the story's "new file `scenes/proto/fight_replay/replay_arcs.gd`" (CLAUDE.md: new code in new files): the file exists and fight_replay.gd refers to it, and
    fight_replay.gd defines no `_draw_arc*` of its own (the layout shot's features stay shared, test_fight_replay_features.py)."""
    arcs = ROOT / "scenes/proto/fight_replay/replay_arcs.gd"
    replay = (ROOT / "scenes/proto/fight_replay/fight_replay.gd").read_text()
    assert arcs.exists(), "scenes/proto/fight_replay/replay_arcs.gd does not exist"
    assert "replay_arcs" in replay, "fight_replay.gd never refers to replay_arcs.gd"
    assert not re.search(r"^func _\w*arc\w*\(", replay, re.M), "fight_replay.gd defines its own arc drawing"


# ---------------------------------------------------------------- R-091-19 hit marks and the HUD totals

def test_r_091_19_hit_marks_list_every_hit_entry_of_the_frame_on_its_victim_with_its_class(s5):
    """R-091-19: "For every entry of the frame's `hits`, a mark is drawn on the victim in the class's colour (front white, side orange, rear red) for that frame; `qa_state().hit_marks`
    lists `{v, cls}`". Frame 0: none; frame 1: (1 front), (2 side); frame 2: none (the marks of frame 1 are not carried); frame 3: (3 rear), (3 front), (6 side), the victim 3
    twice, once per entry. The colours are asserted on the drawn marks (`drawn5`) below."""
    want = {i: sorted((v, c) for a, v, t, d, c in HITS[i]) for i in range(FRAMES)}
    got = {i: (sorted((e.get("v"), e.get("cls")) for e in q["hit_marks"]) if isinstance(q.get("hit_marks"), list) else None)
           for i, q in ((i, s5["frames"][i]["qa"]) for i in range(FRAMES))}
    assert got == want, "qa_state().hit_marks per frame: %r" % {i: s5["frames"][i]["qa"].get("hit_marks") for i in range(FRAMES)}


def test_r_091_19_the_hud_gains_a_line_front_side_rear_with_the_running_totals(s5):
    """R-091-19: "the HUD gains its own line `front N  side N  rear N` with the running totals". A Label of that text on every frame, the totals the hits of frames 0 up to the one
    shown: (0,0,0), (1,1,0), (1,1,0), (2,2,1); stepping back with Left twice from frame 3 shows frame 1's (1,1,0) again."""
    def totals(lines):
        found = [tuple(int(x) for x in TOTALS.fullmatch(t).groups()) for t in lines if TOTALS.fullmatch(t)]
        return found[0] if len(found) == 1 else found
    got = {i: totals(s5["frames"][i]["lines"]) for i in range(FRAMES)}
    assert got == RUNNING, "Label texts per frame: %r" % {i: s5["frames"][i]["lines"] for i in range(FRAMES)}
    assert totals(s5["back"]["lines"]) == RUNNING[1], "after stepping back to frame 1: %r" % s5["back"]["lines"]


def test_r_091_19_the_tick_line_text_is_unchanged_with_a_stage5_file(s5):
    """R-091-19: "(the tick line's text is unchanged)". A file with the `stage5` key and no `seen` or `sights` keeps the stage 3 line `tick %d  A %d  B %d  blocked 0  frame %d/%d`
    on every frame, as one Label of its own and as `hud_tick`. The totals are not in it (they go on their own line)."""
    for i in range(FRAMES):
        f = DOC["frames"][i]
        want = STAGE3_TICK % (f["tick"], f["alive"][0], f["alive"][1], i, FRAMES)
        s = s5["frames"][i]
        assert want in s["lines"], "frame %d: no Label %r among %s" % (i, want, s["lines"])
        assert s["qa"].get("hud_tick") == want, "frame %d hud_tick %r" % (i, s["qa"].get("hud_tick"))


# ---------------------------------------------------------------- R-091-20 climb bar

def test_r_091_20_climbing_units_lists_a_unit_exactly_when_its_climbing_is_strictly_between_0_and_1(s5):
    """R-091-20: "A unit whose `climbing` is strictly between 0 and 1 shows a bar above its glyph filled to that fraction; `qa_state().climbing_units` lists `{id, climbing}`". Every
    frame: frame 0 none; frame 1 only unit 1 at 0.5 (unit 3 at exactly 1.0 is not listed); frame 2 units 1 (0.5) and 2 (0.25); frame 3 none (unit 1 at exactly 1.0, the top). The
    bar's fill is asserted on the drawn bar (`drawn5`) below."""
    want = {i: sorted((u, c) for u, c in CLIMB[i].items() if 0.0 < c < 1.0) for i in range(FRAMES)}
    got = {i: (sorted((e.get("id"), round(float(e.get("climbing", -1.0)), 4)) for e in q["climbing_units"]) if isinstance(q.get("climbing_units"), list) else None)
           for i, q in ((i, s5["frames"][i]["qa"]) for i in range(FRAMES))}
    assert got == want, "qa_state().climbing_units per frame: %r" % {i: s5["frames"][i]["qa"].get("climbing_units") for i in range(FRAMES)}


# ---------------------------------------------------------------- R-091-21 band marks and legend

def test_r_091_21_band_marks_list_every_living_unit_with_its_layer_on_every_frame(s5):
    """R-091-21: "Every living unit carries a small mark in its band's colour from `layer` (band 0 and band 1 differ) ... `qa_state().band_marks` lists `{id, layer}`". Every frame:
    one entry per living unit (8, 8, 8, then 7 with unit 4 dead) with the unit's layer in that frame: units 3 and 7 on layer 1 throughout, unit 2 on layer 0 then layer 1 from frame 2.
    The colours are asserted on the drawn marks (`drawn5`) below."""
    want = {i: sorted((u["id"], u["layer"]) for u in living(DOC, i)) for i in range(FRAMES)}
    got = {i: (sorted((e.get("id"), e.get("layer")) for e in q["band_marks"]) if isinstance(q.get("band_marks"), list) else None)
           for i, q in ((i, s5["frames"][i]["qa"]) for i in range(FRAMES))}
    assert got == want, "qa_state().band_marks per frame: %r" % {i: s5["frames"][i]["qa"].get("band_marks") for i in range(FRAMES)}


LEGEND_WORDS = {"arc": r"\barc\b", "front": r"\bfront\b", "side": r"\bside\b", "rear": r"\brear\b", "climb": r"\bclimb", "band": r"\bbands?\b"}


def _legend_words(lines: list[str]) -> dict:
    """{word: Labels naming it} over the Label texts that are not the totals line."""
    rows = [t for t in lines if not TOTALS.fullmatch(t)]
    return {w: [t for t in rows if re.search(p, t, re.I)] for w, p in LEGEND_WORDS.items()}


def test_r_091_21_the_legend_gains_rows_for_the_arc_the_three_hit_colours_the_climb_bar_and_the_bands(s5):
    """R-091-21: "the legend gains rows for the arc, the three hit colours, the climb bar and the bands". The story gives no row text, so each of the words arc, front, side, rear,
    climb and band is looked for (as a word, any case) in a Label text other than the totals line; with the stage 5 key every word is in some Label."""
    found = _legend_words(s5["frames"][0]["lines"])
    assert [w for w, rows in found.items() if not rows] == [], "no legend Label names %s; Label texts: %s" % ([w for w, r in found.items() if not r], s5["frames"][0]["lines"])


def test_r_091_21_control_the_legend_of_a_file_without_the_stage5_key_has_none_of_those_rows(nokey):
    """CONTROL for the legend test (green today and must stay green): the same words are in no Label of the file without the `stage5` key, so the rows above are the new ones and
    not words the old legend already holds."""
    found = _legend_words(nokey["frames"][0]["lines"])
    assert {w: rows for w, rows in found.items() if rows} == {}, "the old legend already names %s" % found


# ---------------------------------------------------------------- R-091-22 key C

def test_r_091_22_key_c_switches_the_wedges_off_and_on_and_the_default_is_on(s5):
    """R-091-22: "Key C switches the wedges off and on; the default is on." Frame 1, reached by two Left steps from frame 3: wedges on (8 entries in `arcs`, the default, and the file's
    facings); after key C `arcs` is `[]` and the other new keys (hit_marks, climbing_units, band_marks) are unchanged; after key C again the 8 wedges are back."""
    on = _arcs(s5["back"]["qa"])
    off = s5["c_off"]["qa"].get("arcs")
    again = _arcs(s5["c_on"]["qa"])
    assert (on, off, again) == (_want_arcs(DOC, 1), [], _want_arcs(DOC, 1)), "arcs: default %r, after C %r, after C again %r" % (
        s5["back"]["qa"].get("arcs"), off, s5["c_on"]["qa"].get("arcs"))
    for k in ("hit_marks", "climbing_units", "band_marks"):
        assert s5["c_off"]["qa"].get(k) == s5["back"]["qa"].get(k) is not None, "key C changed or lacks %s" % k


# ---------------------------------------------------------------- what is drawn (qa_state().drawn5, read back from the drawn geometry)

ROLE_OF = {i: ["Vanguard", "Vanguard", "Raider", "Raider"][(i - 1) % 4] for i in range(1, 9)}
HIT_RGB = {"front": (255, 255, 255), "side": (255, 128, 0), "rear": (255, 0, 0)}  # the story: front white, side orange, rear red


def _drawn(s5, i: int, key: str) -> list:
    d = s5["frames"][i]["qa"].get("drawn5")
    assert isinstance(d, dict) and isinstance(d.get(key), list), "frame %d: qa_state().drawn5 is %r" % (i, d)
    return d[key]


def _rgb(html: str) -> tuple:
    return tuple(int(html[k:k + 2], 16) for k in (0, 2, 4))


def test_r_091_18_each_wedge_is_as_long_as_its_roles_range_and_the_files_arc_deg_wide(s5):
    """R-091-18, "the file's `arc_deg` wide, as long as that role's range": on every frame the drawn wedge of each living unit is `ranges[role]` long (250 Vanguard, 150 Raider)
    and spans the file's 120 degrees, measured on the polyline drawn, not read from the file."""
    for i in range(FRAMES):
        got = sorted((w["id"], round(w["length"], 3), round(w["span_deg"], 3)) for w in _drawn(s5, i, "wedges"))
        want = sorted((u["id"], DOC["ranges"][ROLE_OF[u["id"]]], ARC_DEG) for u in living(DOC, i))
        assert got == want, "frame %d: drawn wedges %r" % (i, got)


def test_r_091_19_each_hit_mark_is_drawn_in_its_classs_colour(s5):
    """R-091-19, "in the class's colour (front white, side orange, rear red)": on every frame each hit entry is drawn once, on its victim, in the colour of its class
    (a channel may differ by 1 from the story's value in the colour's text)."""
    for i in range(FRAMES):
        marks = _drawn(s5, i, "hits")
        assert sorted((h["v"], h["cls"]) for h in marks) == sorted((v, c) for a, v, t, d, c in HITS[i]), "frame %d: drawn hit marks %r" % (i, marks)
        for h in marks:
            assert max(abs(a - b) for a, b in zip(_rgb(h["colour"]), HIT_RGB[h["cls"]])) <= 1, "frame %d: %s hit on %d drawn %s" % (i, h["cls"], h["v"], h["colour"])


def test_r_091_20_the_climb_bar_is_filled_to_the_units_climbing_fraction(s5):
    """R-091-20, "a bar above its glyph filled to that fraction": on every frame the drawn bars are those of `climbing_units`, each filled (width of the fill over the width of the bar,
    measured on the drawn geometry) to the unit's `climbing`."""
    for i in range(FRAMES):
        got = sorted((b["id"], round(b["fill"], 4)) for b in _drawn(s5, i, "bars"))
        assert got == sorted((u, c) for u, c in CLIMB[i].items() if 0.0 < c < 1.0), "frame %d: drawn bars %r" % (i, got)


def test_r_091_21_the_band_marks_are_drawn_in_a_colour_per_band_and_band_0_and_band_1_differ(s5):
    """R-091-21, "a small mark in its band's colour from `layer` (band 0 and band 1 differ)": on every frame each living unit has one drawn mark; units of one layer share a colour
    and the colour of layer 0 is not that of layer 1."""
    for i in range(FRAMES):
        marks = _drawn(s5, i, "bands")
        assert sorted(m["id"] for m in marks) == sorted(u["id"] for u in living(DOC, i)), "frame %d: drawn band marks %r" % (i, marks)
        by_layer = {}
        for m in marks:
            by_layer.setdefault(1 if m["id"] in UP[i] else 0, set()).add(m["colour"])
        assert sorted(len(c) for c in by_layer.values()) == [1, 1], "frame %d: colours per layer %r" % (i, by_layer)
        assert by_layer[0] != by_layer[1], "band 0 and band 1 share the colour %r" % by_layer


def test_r_091_22_key_c_takes_the_drawn_wedges_off_and_on(s5):
    """R-091-22: key C removes the wedges themselves, not only the `arcs` list: on frame 1 the drawn wedges are 8 by default, none after key C, 8 again after key C again, and the
    other marks drawn (hits, bars, bands) are the same in all three."""
    def drawn(k):
        d = s5[k]["qa"]["drawn5"]
        return len(d["wedges"]), {key: d[key] for key in ("hits", "bars", "bands")}
    on, off, again = drawn("back"), drawn("c_off"), drawn("c_on")
    assert (on[0], off[0], again[0]) == (8, 0, 8), (on[0], off[0], again[0])
    assert on[1] == off[1] == again[1]
