# Rule pins: none (H-053 section "Replay readability", Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn)
# spec: docs/stories/H-053.md "Replay readability (ruled 2026-11-02 ...)", items 1 to 5; look review scratch/stage2/look_review_1.md
"""H-053 Replay readability, replay scene: camera fit, one ring per role per side, six role glyphs, labelled end and rate lines.

Quoted. Item 1: "zoomed so a unit is at least 14 px across on the 1920x1080 window ... `qa_state()` gains `camera: {fit: [x0, y0, x1, y1], unit_px}`."
Item 2: "one ring per role per side ... with a distinct line style per role ... The legend lists each ring: `<side> <role> <range> wu <style>`. A ring may leave the
frame ...; an off-frame ring is still listed ... `qa_state()` gains `rings: [{side, role, range, style, centre: [x, y]}]`." Item 3: "Six distinct shapes ... the legend
shows each. `qa_state()` gains `glyphs: {role: shape}`." Item 5: "`end: A wins (wipe)`, `end: B wins (wipe)`, `end: mutual wipe, no winner`, `end: stall (silence)`,
`end: cap`; and the HUD rate line reads `rate A <m> vs target <p> (gap <n> pts, not scored); guess <A|B|draw>: AGREE|DISAGREE` (story quote superseded by the Architect's 2026-11-02 ruling, DEC-stage-scoring-loose-2026-11-02). `qa_state()` gains `end_label` and `rate_label`
(strings, compared exactly in tests)."

Each scene test is isolation (the scene alone on a hand-written file) and integration (the file goes through snapshot.write/validate, the same path run.py feeds).
Architect answers (2026-11-02, recorded with the Replay readability ruling) are pinned here: `rate_label` is set on EVERY frame when a rate file exists (it is the layout's
verdict) and "" when none; `end_label` is last-frame-only, "" before; `qa_state` `facing_px` equals the glyph size, minimum 8; ring-centre ties go to the lowest unit id; style
names solid/dotted/dashed/dash_dot/long_dash/double and glyph names triangle/diamond/square/pentagon/circle/hexagon in role order Raider, Interceptor, Vanguard, Warden, Bombard,
Bastion; sides spelt A and B; rates with two decimals; camera margin 10% of the span each side; wide fields fit per frame with unit_px >= 14.

Positive controls (green today): every fixture validates through snapshot.validate; the label checker rejects "wins" in a mutual-wipe label and accepts it in a win label;
the world-space bounding box helper agrees with a hand-computed box.
Red on the built tree: qa_state has none of camera, rings, glyphs, end_label, rate_label.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[1]

from test_fight_replay import _hud_lines, _key, _open, _state, _write_fight  # noqa: E402
from scripts.skilllab.arena import snapshot  # noqa: E402

STYLES = ["solid", "dotted", "dashed", "dash_dot", "long_dash", "double"]
SHAPES = ["triangle", "diamond", "square", "pentagon", "circle", "hexagon"]
ROLES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]
RANGES = {"Raider": 150.0, "Interceptor": 200.0, "Vanguard": 250.0, "Warden": 400.0, "Bombard": 1200.0, "Bastion": 100.0}


def _fight(tmp_path: Path, gap: float = 1000.0, winner: str = "A", end: str = "wipe", name: str = "L-0001-s1", predict: str = "A") -> tuple[Path, dict]:
    """24 units, two of each of the six roles per side (ids 1..12 A, 13..24 B), 3 frames. A's units sit at x 0 and 50, B's at gap and gap+50, y by role (40 wu apart); the
    second unit of a role is the one nearer the enemy for A (x 50) and the first for B (x gap). Unit 1 of A drifts +20 x and +10 y per frame (so a box over all frames is
    larger than frame 0's). Last frame by `winner`/`end`: A (B all dead), B (A all dead), none (all dead), stall/cap (all alive)."""
    base = []
    for side_n, side in enumerate("AB"):
        for r, role in enumerate(ROLES):
            for k in range(2):
                x = (0.0 if k == 0 else 50.0) if side == "A" else gap + 50.0 * k
                base.append({"id": side_n * 12 + r * 2 + k + 1, "side": side, "role": role, "x": x, "y": 100.0 + 40.0 * r, "layer": 0,
                             "facing": 0.0 if side == "A" else 3.142, "hp": 100.0, "alive": True, "target": None})
    frames = []
    for n in range(3):
        rows = json.loads(json.dumps(base))
        rows[0]["x"] += 20.0 * n
        rows[0]["y"] += 10.0 * n
        if n == 2:
            for u in rows:
                if (winner == "A" and u["side"] == "B") or (winner == "B" and u["side"] == "A") or winner == "none":
                    u["hp"], u["alive"] = 0.0, False
        frames.append({"tick": n * 100, "alive": [sum(1 for u in rows if u["side"] == s and u["alive"]) for s in "AB"], "units": rows})
    stall, cap = winner == "stall", winner == "cap"
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    doc["frames"] = frames
    doc["ranges"] = dict(RANGES)
    doc["result"].update({"winner": "draw" if cap else winner, "survivors": frames[-1]["alive"], "ticks": 200, "capped": cap, "predict": predict,
                          "agree": ("draw" if cap else winner) == predict, "end": "silence" if stall else ("cap" if cap else end), "stall": stall})
    assert snapshot.validate(doc) == [], snapshot.validate(doc)
    return _write_fight(tmp_path / (name + ".fight.json"), doc), doc


def _all_positions(doc: dict) -> list[tuple[float, float]]:
    return [(u["x"], u["y"]) for f in doc["frames"] for u in f["units"]]


def _rate_file(tmp_path: Path, rate_a: float, predict_rate: float, agree: bool, mirror: bool = False) -> None:
    (tmp_path / "L-0001.rate.json").write_text(json.dumps(
        {"layout_id": "L-0001", "seeds": [1], "wins_a": 1, "wins_b": 0, "stalls": 0, "stall_seeds": [], "none_seeds": [], "rate_a": rate_a, "predict_rate": predict_rate,
         "band": 0.1, "agree": agree, "mirror": mirror, "firing_capable": {"A": 1.0, "B": 1.0}, "median_seed": 1}) + "\n")


def _qa(monkeypatch, path: Path, last: bool = False) -> tuple[dict, dict]:
    """(qa_state, full state) of a fresh scene on `path`, frame 0, or the last frame (2 steps)."""
    g = _open(monkeypatch, path)
    try:
        g.wait_for_port(timeout=90.0)
        st = _state(g)
        if last:
            _key(g, "Space")
            _key(g, "Space")
            st = _state(g, lambda q: q["frame"] == 2, timeout=15.0, label="last frame")
        return st["qa"], st
    finally:
        g.stop()


def _label_ok(label: str, winner: str) -> bool:
    """The label checker used below (kept here so its control is green today): a mutual wipe or stall or cap label never says "wins"."""
    return ("wins" in label) == (winner in ("A", "B"))


# ---------------------------------------------------------------- positive controls (green today)

@pytest.mark.parametrize("winner", ["A", "B", "none", "stall", "cap"])
def test_control_readability_fixtures_validate_and_have_24_units(winner, tmp_path):
    """H-053 Replay readability, harness control: every fixture (win A, win B, mutual wipe, stall, cap) validates through snapshot.validate, has 24 units on frame 0,
    and its last-frame alive counts match its result.survivors, so a red below is the scene and not a bad file."""
    path, doc = _fight(tmp_path, winner=winner)
    back = json.loads(path.read_text())
    assert len(back["frames"][0]["units"]) == 24 and back["frames"][-1]["alive"] == back["result"]["survivors"]
    assert (back["result"]["survivors"] == [0, 0]) == (winner == "none")


def test_control_label_checker_rejects_wins_in_a_mutual_wipe_and_accepts_it_in_a_win():
    """H-053 item 5 "(positive control: the mutual-wipe label never reads "wins")": the checker passes the item's own strings and fails a wrong one, so a green below is meaningful."""
    assert _label_ok("end: A wins (wipe)", "A") and _label_ok("end: B wins (wipe)", "B")
    assert _label_ok("end: mutual wipe, no winner", "none") and _label_ok("end: stall (silence)", "stall") and _label_ok("end: cap", "draw")
    assert not _label_ok("end: A wins (wipe)", "none")
    assert not _label_ok("end: mutual wipe, no winner", "A")


def test_control_bounding_box_helper_matches_a_hand_computed_box(tmp_path):
    """H-053 item 1 control: over all frames the fixture's unit positions span x 0..1050 (unit 1 drifts only to 40, B's far unit sits at 1050) and y 100..300
    (unit 1 drifts only to 120), so the box is [0, 100, 1050, 300]; the helper agrees, so the containment test below compares against the right box."""
    _, doc = _fight(tmp_path)
    xs, ys = zip(*_all_positions(doc))
    assert (min(xs), min(ys), max(xs), max(ys)) == (0.0, 100.0, 1050.0, 300.0)


# ---------------------------------------------------------------- item 1: camera fit

def test_camera_fit_contains_every_unit_over_all_frames_and_units_are_at_least_14_px(tmp_path, monkeypatch):
    """Item 1: "fits the bounding box of every unit position over all frames of the fight, 10% margin, fixed for the whole fight, zoomed so a unit is at least 14 px across
    on the 1920x1080 window ... `camera: {fit: [x0, y0, x1, y1], unit_px}`". Contained: fit is a superset of the box of all positions in all frames (the margin split is not
    pinned); fixed: the same fit on frame 0 and the last frame; unit_px >= 14."""
    path, doc = _fight(tmp_path)
    xs, ys = zip(*_all_positions(doc))
    q0, _ = _qa(monkeypatch, path)
    q2, _ = _qa(monkeypatch, path, last=True)
    assert "camera" in q0, "qa_state keys %s lack camera" % sorted(q0)
    x0, y0, x1, y1 = q0["camera"]["fit"]
    assert x0 <= min(xs) and y0 <= min(ys) and x1 >= max(xs) and y1 >= max(ys), "fit %s does not contain box %s" % (q0["camera"]["fit"], (min(xs), min(ys), max(xs), max(ys)))
    assert q0["camera"]["fit"] == q2["camera"]["fit"], "fit changed over the fight"
    assert q0["camera"]["unit_px"] >= 14
    w, h = max(xs) - min(xs), max(ys) - min(ys)   # Architect: margin 10% of the span each side (at least; the window's aspect may widen one axis)
    eps = 1e-3
    assert x0 <= min(xs) - 0.1 * w + eps and x1 >= max(xs) + 0.1 * w - eps and y0 <= min(ys) - 0.1 * h + eps and y1 >= max(ys) + 0.1 * h - eps, \
        "fit %s has under a 10%% margin round box %s" % (q0["camera"]["fit"], (min(xs), min(ys), max(xs), max(ys)))


def test_a_4000_wu_field_keeps_units_at_14_px(tmp_path, monkeypatch):
    """Item 1 "(when the fight needs a wider field than that allows, the units keep 14 px and the camera follows the fight's centroid)": A and B 4000 wu apart, unit_px >= 14."""
    path, _ = _fight(tmp_path, gap=4000.0)
    q, _ = _qa(monkeypatch, path)
    assert "camera" in q, "qa_state keys %s lack camera" % sorted(q)
    assert q["camera"]["unit_px"] >= 14


def test_a_wide_field_fits_per_frame_with_units_at_14_px_on_every_frame(tmp_path, monkeypatch):
    """Architect: on a wide field the fit is per frame with unit_px >= 14: on frame 0 and on the last frame the fit contains that frame's centroid and unit_px >= 14."""
    path, doc = _fight(tmp_path, gap=4000.0)
    for last, n in ((False, 0), (True, 2)):
        q, _ = _qa(monkeypatch, path, last=last)
        assert "camera" in q, "qa_state keys %s lack camera" % sorted(q)
        pts = [(u["x"], u["y"]) for u in doc["frames"][n]["units"]]
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        x0, y0, x1, y1 = q["camera"]["fit"]
        assert x0 <= cx <= x1 and y0 <= cy <= y1, "frame %d: fit %s misses the centroid %s" % (n, q["camera"]["fit"], (cx, cy))
        assert q["camera"]["unit_px"] >= 14


def _facing_ok(facing_px, unit_px) -> bool:
    """The facing check kept here so its control is green today: the tick equals the glyph size and is never under 8."""
    return facing_px == max(8, unit_px) and facing_px >= 8


def test_control_facing_checker_rejects_a_short_tick_and_a_mismatch():
    """H-053 item 4 control: 14 px glyph with a 14 px tick passes; a 5 px tick (the old one), a 20 px tick on a 14 px glyph and a 7 px tick on a 7 px glyph fail."""
    assert _facing_ok(14, 14) and not _facing_ok(5, 14) and not _facing_ok(20, 14) and not _facing_ok(7, 7)


def test_facing_tick_equals_the_glyph_size(tmp_path, monkeypatch):
    """Item 4: "Facing tick length equals the glyph size (never under 8 px)"; Architect: `qa_state` key `facing_px` equals the glyph size (camera unit_px), minimum 8."""
    path, _ = _fight(tmp_path)
    q, _ = _qa(monkeypatch, path)
    assert "facing_px" in q and "camera" in q, "qa_state keys %s" % sorted(q)
    assert _facing_ok(q["facing_px"], q["camera"]["unit_px"]), "facing_px %r, unit_px %r" % (q["facing_px"], q["camera"]["unit_px"])


# ---------------------------------------------------------------- items 2 and 3: rings, legend, glyphs

def test_rings_are_one_per_role_per_side_with_a_style_per_role(tmp_path, monkeypatch):
    """Item 2: "one ring per role per side ... a distinct line style per role": 12 entries (6 roles x 2 sides, not 24 per-unit rings), each with the file's range for the role,
    a non-empty style, six distinct styles in all, and the same style for a role on both sides (style is per role, colour is per side)."""
    path, _ = _fight(tmp_path)
    q, _ = _qa(monkeypatch, path)
    assert "rings" in q, "qa_state keys %s lack rings" % sorted(q)
    rings = q["rings"]
    assert len(rings) == 12 and {(r["side"], r["role"]) for r in rings} == {(s, role) for s in {r["side"] for r in rings} for role in ROLES}
    assert len({r["side"] for r in rings}) == 2
    for r in rings:
        assert r["range"] == RANGES[r["role"]] and isinstance(r["style"], str) and r["style"]
    by_role = {}
    for r in rings:
        by_role.setdefault(r["role"], set()).add(r["style"])
    assert all(len(s) == 1 for s in by_role.values()), "a role has different styles per side: %s" % by_role
    assert len({next(iter(s)) for s in by_role.values()}) == 6, "styles are not six distinct: %s" % by_role
    assert {role: next(iter(s)) for role, s in by_role.items()} == dict(zip(ROLES, STYLES)), "style names by role: %s" % by_role
    assert {r["side"] for r in rings} == {"A", "B"}, "side spelling: %s" % {r["side"] for r in rings}


def test_ring_is_centred_on_the_unit_of_that_role_nearest_the_opposing_centroid_at_frame_0(tmp_path, monkeypatch):
    """Item 2: "centred on that side's unit of that role nearest the opposing centroid at frame 0". Fixture: A's second unit of each role (x 50) is nearest B; B's first
    (x 1000) is nearest A. So A rings are at x 50 and B rings at x 1000, y = 100 + 40 * role index."""
    path, _ = _fight(tmp_path)
    q, _ = _qa(monkeypatch, path)
    a = "A"
    for r in q["rings"]:
        want_x = 50.0 if r["side"] == a else 1000.0
        want_y = 100.0 + 40.0 * ROLES.index(r["role"])
        assert [round(v, 1) for v in r["centre"]] == [want_x, want_y], r


def test_a_tie_for_nearest_the_opposing_centroid_goes_to_the_lowest_unit_id(tmp_path, monkeypatch):
    """Architect: ring-centre ties go to the lowest unit id. A's two Raiders (ids 1 and 2) sit at y 150 and 250 on the same x, B's centroid y is 200, so both are exactly as near;
    the A Raider ring is centred on unit 1 (0, 150). Control: the fixture is a true tie and still validates."""
    path, doc = _fight(tmp_path)
    f0 = doc["frames"][0]["units"]
    f0[0].update(x=0.0, y=150.0)
    f0[1].update(x=0.0, y=250.0)
    cy = sum(u["y"] for u in f0 if u["side"] == "B") / 12
    assert cy == 200.0 and abs(f0[0]["y"] - cy) == abs(f0[1]["y"] - cy) and f0[0]["id"] == 1 and f0[1]["id"] == 2 and snapshot.validate(doc) == []
    path = _write_fight(tmp_path / "tie.fight.json", doc)
    q, _ = _qa(monkeypatch, path)
    assert "rings" in q, "qa_state keys %s lack rings" % sorted(q)
    ring = [r for r in q["rings"] if r["side"] == "A" and r["role"] == "Raider"]
    assert len(ring) == 1 and [round(v, 1) for v in ring[0]["centre"]] == [0.0, 150.0], ring


def test_an_off_frame_ring_is_still_listed_in_rings_and_in_the_legend(tmp_path, monkeypatch):
    """Item 2: "A ring may leave the frame ...; an off-frame ring is still listed and its visible arc is drawn" and "The legend lists each ring: `<side> <role> <range> wu <style>`".
    Fixture: Bombard range 1200 on a field about 1100 wu wide, so the ring leaves the fit (asserted from qa_state first); all 12 rings still have a legend line."""
    path, _ = _fight(tmp_path)
    q, st = _qa(monkeypatch, path)
    assert "rings" in q and "camera" in q, "qa_state keys %s" % sorted(q)
    x0, y0, x1, y1 = q["camera"]["fit"]
    bombards = [r for r in q["rings"] if r["role"] == "Bombard"]
    assert bombards and all(r["centre"][0] - r["range"] < x0 or r["centre"][0] + r["range"] > x1 for r in bombards), "Bombard ring does not leave the fit"
    lines = _hud_lines(st)
    for r in q["rings"]:
        want = "%s %s %g wu %s" % (r["side"], r["role"], r["range"], r["style"])
        assert any(want in t for t in lines), "no legend text %r among Label texts %s" % (want, lines)


def test_six_distinct_role_glyphs_and_the_legend_shows_each(tmp_path, monkeypatch):
    """Item 3: "Six distinct shapes ... side by colour; the legend shows each. `glyphs: {role: shape}`": six roles, six distinct non-empty shape names, and each role's
    name and shape name appear together in a Label text (the legend)."""
    path, _ = _fight(tmp_path)
    q, st = _qa(monkeypatch, path)
    assert "glyphs" in q, "qa_state keys %s lack glyphs" % sorted(q)
    g = q["glyphs"]
    assert set(g) == set(ROLES) and all(isinstance(v, str) and v for v in g.values())
    assert len(set(g.values())) == 6, "glyph shapes not distinct: %s" % g
    assert g == dict(zip(ROLES, SHAPES)), "glyph names by role: %s" % g
    lines = _hud_lines(st)
    for role, shape in g.items():
        assert any(role in t and shape in t for t in lines), "legend lacks %s with %s among Label texts %s" % (role, shape, lines)


# ---------------------------------------------------------------- item 5: end and rate lines

END_CASES = [
    ("A", "end: A wins (wipe)"),
    ("B", "end: B wins (wipe)"),
    ("none", "end: mutual wipe, no winner"),
    ("stall", "end: stall (silence)"),
    ("cap", "end: cap"),
]


@pytest.mark.parametrize("winner,label", END_CASES, ids=[c[0] for c in END_CASES])
def test_end_label_on_the_last_frame_is_exactly_the_story_string(winner, label, tmp_path, monkeypatch):
    """Item 5: end_label is one of the five strings, compared exactly, on the last frame; the HUD shows the same text; the mutual-wipe label never reads "wins"."""
    path, _ = _fight(tmp_path, winner=winner)
    q, st = _qa(monkeypatch, path, last=True)
    assert "end_label" in q, "qa_state keys %s lack end_label" % sorted(q)
    assert q["end_label"] == label
    assert _label_ok(q["end_label"], winner)
    assert label in _hud_lines(st), "no HUD text equal to %r among Label texts %s" % (label, _hud_lines(st))


@pytest.mark.parametrize("rate_a,predict_rate,agree,label", [
    (0.75, 0.75, True, "rate A 0.75 vs target 0.75 (gap 0 pts, not scored); guess A: AGREE"),
    (0.25, 0.75, False, "rate A 0.25 vs target 0.75 (gap 50 pts, not scored); guess A: DISAGREE"),
    (1.0, 0.60, False, "rate A 1.00 vs target 0.60 (gap 40 pts, not scored); guess A: DISAGREE"),
], ids=["agree", "disagree", "clean-win-disagree"])
def test_rate_label_names_measured_target_gap_guess_and_the_verdict(rate_a, predict_rate, agree, label, tmp_path, monkeypatch):
    """Item 5 as ruled 2026-11-02: with a rate file beside the fight the rate_label is `rate A <m> vs target <p> (gap <n> pts, not scored); guess <A|B|draw>: AGREE|DISAGREE` compared
    exactly (m, p two decimals; n whole points = round(|m-p|*100); `guess` is the layout's predict, fights[0].result.predict = A here); the HUD shows it."""
    path, _ = _fight(tmp_path)
    _rate_file(tmp_path, rate_a, predict_rate, agree)
    q, st = _qa(monkeypatch, path, last=True)
    assert "rate_label" in q, "qa_state keys %s lack rate_label" % sorted(q)
    assert q["rate_label"] == label
    assert label in _hud_lines(st), "no HUD text equal to %r among Label texts %s" % (label, _hud_lines(st))


@pytest.mark.parametrize("predict", ["B", "draw"])
def test_rate_label_guess_shows_the_layouts_predict(predict, tmp_path, monkeypatch):
    """The `guess` word is the layout's predict read from the fight's result (not hard-wired to A): predict B and draw (not a mirror: rate file mirror false) read
    `guess B` / `guess draw` with the rate file's AGREE|DISAGREE word. Control: the A case above reads `guess A`."""
    path, _ = _fight(tmp_path, predict=predict)
    _rate_file(tmp_path, 0.25, 0.75, False)
    q, _ = _qa(monkeypatch, path, last=True)
    assert q.get("rate_label") == "rate A 0.25 vs target 0.75 (gap 50 pts, not scored); guess %s: DISAGREE" % predict, q.get("rate_label")


def test_rate_label_exact_mirror_draw_is_not_scored(tmp_path, monkeypatch):
    """Ruled 2026-11-02: an exact-mirror draw reads `rate A <m> vs target <p> (gap <n> pts, not scored); guess draw: NOT SCORED (mirror)` (rate file mirror true, predict draw), on every frame.
    Positive control inside: the same fight with mirror false reads AGREE, never NOT SCORED, so the words come from the mirror flag."""
    path, _ = _fight(tmp_path, predict="draw")
    _rate_file(tmp_path, 0.5, 0.5, True, mirror=True)
    want = "rate A 0.50 vs target 0.50 (gap 0 pts, not scored); guess draw: NOT SCORED (mirror)"
    q0, _ = _qa(monkeypatch, path)
    q2, st = _qa(monkeypatch, path, last=True)
    assert q0.get("rate_label") == want and q2.get("rate_label") == want, "%r / %r" % (q0.get("rate_label"), q2.get("rate_label"))
    assert want in _hud_lines(st), "no HUD text equal to %r among Label texts %s" % (want, _hud_lines(st))
    _rate_file(tmp_path, 0.5, 0.5, True, mirror=False)
    q, _ = _qa(monkeypatch, path, last=True)
    assert q.get("rate_label") == "rate A 0.50 vs target 0.50 (gap 0 pts, not scored); guess draw: AGREE", q.get("rate_label")


# ---------------------------------------------------------------- when the labels are set (Architect answers)

def test_rate_label_is_the_layouts_verdict_on_every_frame_and_empty_without_a_rate_file(tmp_path, monkeypatch):
    """Architect: `rate_label` is set on EVERY frame when a rate file exists (frame 0 and the last frame carry the same exact string) and is "" when there is none.
    Control inside: the no-rate-file run reads "" on both frames, so a non-empty value below comes from the file."""
    label = "rate A 0.75 vs target 0.75 (gap 0 pts, not scored); guess A: AGREE"
    path, _ = _fight(tmp_path, name="L-0001-s1")
    q0, _ = _qa(monkeypatch, path)
    q2, _ = _qa(monkeypatch, path, last=True)
    assert q0.get("rate_label") == "" and q2.get("rate_label") == "", "no rate file: %r / %r (keys %s)" % (q0.get("rate_label"), q2.get("rate_label"), sorted(q0))
    _rate_file(tmp_path, 0.75, 0.75, True)
    q0, _ = _qa(monkeypatch, path)
    q2, _ = _qa(monkeypatch, path, last=True)
    assert q0.get("rate_label") == label and q2.get("rate_label") == label, "with a rate file: %r / %r" % (q0.get("rate_label"), q2.get("rate_label"))


def test_end_label_is_empty_before_the_last_frame(tmp_path, monkeypatch):
    """Architect: `end_label` stays last-frame-only, "" before. Frame 0 of a win fixture reads "" (the last frame reads the story string, see the end-label test)."""
    path, _ = _fight(tmp_path, winner="A")
    q0, _ = _qa(monkeypatch, path)
    assert q0.get("end_label") == "", "frame 0 end_label %r (keys %s)" % (q0.get("end_label"), sorted(q0))
