# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 (new diagram.py; ruling 12 output rule; ruling 4 ceiling hit; ruling 5 both_wrong is a finding); decisions 24 (second crossing), 25 (baseline roles), 29 (L5 readings), 31 (L5 audit items)
"""LAB-REV2-L5 tests for scripts/skilllab/diagram.py: the SVG per notable layout, arrows marking the evidence for each assertion.

The L5 spec row is thin; THE INTERFACE BELOW IS FIXED BY THIS FILE (the builder reads it as the spec). Anything marked QUESTION is a
reading the test writer made and the Architect should confirm; the unmarked lines follow from the spec, the rulings or L4's output.

Input = the rows of one family or smoke CSV (what `rows.fight_row` returns / `rows.write_rows` writes; the columns are L4's: `family`,
`play`, `layout`, `point`, `kind` in {grid, refined, sign_flip, control_positive, control_null, control_smoke}, `enemy_heads`, `knob`,
`knob_value`, `baseline` in {none, naive_attacker, naive_defender, naive_defender_attacker_layer, naive_defender_play_layer},
`ceiling_hit`, `outcome`, `agreement`, `predicted_count`, `predicted_type`, `firing_window_0/1`, `weighted_window_0/1`, ...) plus, for
the layout, a `Setup` (groups with formation/anchor/layer, `terrain` blocks and covers, `point`).
`point` (decision 31 A, written by the L4 follow-on in sweep.py and rows.py) is a string, the family-local label of the series a row
belongs to: cone rows `half=<deg>` (knob_value = range), emitting rows `vision=<v>` (knob_value = sight), every other row `-`.

    read_rows(path) -> list[dict]
        The CSV that rows.write_rows wrote, typed: INT columns enemy_heads, ceiling_hit, ticks, first_contact_tick, survivors_0,
        survivors_1, heads_0, heads_1; FLOAT columns margin, strength_left_0/1, firing_unit_seconds_0/1, firing_window_0/1,
        weighted_unit_seconds_0/1, weighted_window_0/1, knob_value; every other column stays a str (layout "81" stays "81", point
        "half=45" stays "half=45"); an empty cell reads None. Reading what fight_row produced and written by write_rows round-trips
        every non-None cell.

    Notable(kind, family, play, layout, point, role, knob_lo, knob_hi, heads, row)      frozen dataclass; `id` property (str, matches
        ^[A-Za-z0-9_-]+$, unique per notable, a function of the fields only, so two notables that differ in any field (point and
        knob_lo included) never share an id)
        kind in {"crossing", "ceiling_hit", "both_wrong"} (constants diagram.CROSSING, CEILING_HIT, BOTH_WRONG)
        crossing:    point = the series label; role = the baseline role crossed; knob_lo < knob_hi the two ADJACENT knob values of that
                     series (grid and refined points, sorted NUMERICALLY, ascending) whose sign of the gain differs; row None;
                     heads = the break-even headcount of the play scan at the one of the two knob values where the play is ahead
                     (the headcount of "the bracketing cell": setup_for(notable) builds the fight there; QUESTION 5)
        ceiling_hit: role "none", knob_lo == knob_hi == the knob value, row None, heads = the largest enemy_heads among its rows
        both_wrong:  family/play/layout/point/knob_lo/knob_hi/role/heads taken from the row (knob_* = knob_value, role = baseline,
                     heads = enemy_heads), row = its index. In a both_wrong row predicted_count, predicted_type and outcome are each
                     "side0" or "side1": a tie predicts "tie" and the agreement is then "n/a", so "tie" cannot occur beside both_wrong.

    notables(rows) -> list[Notable]
        order: crossing, then ceiling_hit, then both_wrong; inside a kind sorted by (family, play, layout, point, role, knob_lo) and,
        for both_wrong, by row index; family, play, layout, point and role sort as STRINGS (layout "192" before "78"), knob_lo as a
        FLOAT (90.0 before 120.0). Deterministic, also across processes with different PYTHONHASHSEED.
        CROSSING (the sign of the gain, as sweep.py reads it): for each series (family, play, layout, point) and each baseline role
        present among its rows (any baseline other than "none"; decisions 24: a defending play whose rows carry a naive_defender*
        role gets its own crossing against it, a meeting has none), over rows of kind grid or refined only: per knob value, a play
        scan is the rows with baseline "none" and a baseline scan the rows with that role, both of that series; a cell (one
        enemy_heads) is won when every row of it has outcome side0; break-even = the top enemy_heads when every cell is won (a
        ceiling hit), else the enemy_heads before the FIRST won-to-lost step (scan._crossing; a later flip back to won is not read),
        else 0 (lost in every cell, or lost in the first); gain = break-even(play) - break-even(role); the sign is gain > 0 (zero is
        not ahead). One Notable per adjacent pair of knob values whose signs differ. Control kinds (control_*) and sign_flip rows are
        never read. Series never merge: the nine cone points of one range sit in three series (one per half-angle), each read along
        range, and a row of one series is never part of another's scan even when knob_value and enemy_heads agree.
        CEILING_HIT: rows with baseline "none", kind grid or refined and ceiling_hit == 1 (the column L4 wrote), one Notable per
        (family, play, layout, point, knob_value). A ceiling_hit == 1 row of a baseline role is not a notable (QUESTION 1; decision
        29 item 3): it is listed by baseline_ceilings.
        BOTH_WRONG: every row (any kind, any baseline) whose agreement == "both_wrong": one Notable per row (ruling 5, a mismatch is
        a finding; the report lists them). Decision 29 item 6: a control or a baseline row is included, with its role (and, for a
        control, its kind) in the label (the <title> text), and a both_wrong on a control is the strongest finding against the measure.

    baseline_ceilings(rows) -> list[dict]       decision 29 item 3: one dict per (family, play, layout, point, role, knob_value) whose
        baseline scan has kind grid or refined and ceiling_hit == 1 (the baseline also wins everywhere, so no crossing is possible
        there); keys family, play, layout, point, role, knob_value (float); sorted like notables; [] when there is none. Never a Notable.

    render(notable, rows, setup) -> str            one self-contained SVG document (a string), byte-identical for the same arguments
        root <svg> (xmlns svg, viewBox "0 0 W H" with W, H numbers): attributes id = notable.id, data-kind, data-family, data-play,
        data-layout, data-point, data-role; a <title> child holding family, play and layout (and, for a both_wrong notable, the role
        and, when the row's kind starts "control_", that kind).
        layout (top-down, world coordinates written in data attributes, svg positions free but inside the viewBox and with cx
        non-decreasing in data-x):
          <circle class="unit side{0|1} layer-{n}" data-side data-layer data-unit data-x data-y cx cy r>  one per placed unit;
              data-unit is Group.unit (the unit TYPE name, not an index); positions are what
              formations.place(group.formation, group.count, group.x, group.y, group.facing_deg, group.params) gives
          <rect class="wall" data-x0 data-y0 data-x1 data-y1 data-layer-lo data-layer-hi x y width height>  one per Terrain.blocks
          <circle class="cover" data-x data-y data-radius data-height cx cy r>  one per Terrain.covers
          <g class="point" data-x data-y>  once when Setup.point is not None, absent otherwise
          the choke is the gap between two walls (QUESTION 3): it has no element of its own
        legend: one <g class="legend"> with <text> entries naming side 0, side 1, wall, point, arrow and layer (case-insensitive
              substrings); a <text class="draft" data-draft="NAME"> inside it for every DRAFT number the diagram touches (below)
        arrows: <g class="arrow arrow-{kind}" data-kind data-column data-value data-row data-target-side data-target-x data-target-y>
              holding one <line x1 y1 x2 y2> (endpoints inside the viewBox) and one <text>. `kind` (the arrow's evidence kind, also
              the data-kind attribute and the suffix of the class token arrow-{kind}) is: crossing -> "play" or "baseline";
              ceiling_hit -> "ceiling"; both_wrong -> "window" (the four window arrows), "prediction" (predicted_count and
              predicted_type) or "outcome". data-row indexes `rows`; data-value is the CSV text of rows[data-row][data-column]
              (floats as repr, ints as str, None as ""); data-target-side is "0", "1" or "point"; data-target-x/y are the world
              coordinates of what the arrow points at: the mean of the placed positions of that side, or Setup.point. The text is
              "{column} {value}" (then " DRAFT" when data-draft is set) for every arrow except the crossing ones.
          crossing (decision 31 D; QUESTION 6): the evidence is the break-even rows. For each of the two knob values (knob_lo,
                       knob_hi) and for each of the two scans, the play's (baseline "none", kind "play") and the role's (kind
                       "baseline"), an arrow to the FIRST row (lowest index) of each BRACKETING cell of that scan: the cell at the
                       break-even headcount (when it is above 0) and the cell at the first lost headcount after it (when the scan
                       has a won-to-lost step); a scan that won everywhere has only its top cell, a scan lost in the first cell has
                       only that first cell. Arrow: data-column "enemy_heads", data-value the CSV text of enemy_heads, data-outcome the
                       CSV text of the row's outcome, data-knob the CSV text of the row's knob_value, data-role the row's baseline
                       ("none" for the play), data-target-side "0"; the text reads exactly "({enemy_heads}, {outcome})". Every
                       such row has the family, play, layout and point of the notable.
          ceiling_hit: an arrow "ceiling_hit" (value "1", on a qualifying row, side "0") and an arrow "enemy_heads" (the largest
                       enemy_heads among the qualifying rows of that knob value, side "1"); both kind "ceiling"
          both_wrong:  seven arrows on rows[notable.row]: firing_window_0 (side 0), firing_window_1 (side 1), weighted_window_0
                       (side 0), weighted_window_1 (side 1), predicted_count (the predicted side), predicted_type (the predicted
                       side), outcome (the surviving side); the four window arrows carry data-draft="DRAFT-opening-window-ticks"
                       (ruling 5, DRAFT-opening-window-ticks)
        DRAFT numbers touched (legend <text class="draft" data-draft=NAME>, the name from the spec, the value from the library
        constant where one exists, none pinned here): any window arrow -> DRAFT-opening-window-ticks (value text
        contract.OPENING_WINDOW_TICKS); family "arc" -> DRAFT-firing-arc-deg; family "cone" -> DRAFT-aoe-cone-range,
        DRAFT-aoe-cone-deg, DRAFT-aoe-cone-share. Otherwise none (decision 31 F: the legend marks only what its rows touch).

    render_all(rows, setup_for) -> dict[str, str]   notable.id -> svg, in notables(rows) order; setup_for(notable) -> Setup
    write_all(rows, setup_for, out_dir) -> list[pathlib.Path]   writes <out_dir>/<notable.id>.svg (utf-8, the render_all text) and
        returns the paths in order; writes nothing (no file, no directory, the list is empty) when there is no notable.

    setup_for(notable) is the caller's: report.artifact and the `artifact` command pass one (scripts/skilllab/__main__.py builds it
    as sweep.smoke_layouts()[notable.layout] -> sweep.default_builds(notable.play, "play", features)(notable.heads, False); that
    build needs the map, not the engine, but is SLOW-gated here because it runs the real scene code: see the last test).

QUESTIONS for the Architect (none blocks the tests; each is a reading, none is a number):
 1. ceiling_hit notable: only the play's own rows (baseline "none"), not a baseline scan that also beats the top (decision 29 item 3).
 2. A crossing is read from rows (CSV), not from sweep_summary.json (its `refined_vs` is per family, not per play and layout).
 3. "choke" in the spec row has no Setup field; the diagram draws the Terrain blocks (walls) and covers, the choke is the gap between walls.
 4. both_wrong includes control and baseline rows (decision 29 item 6).
 5. `Notable.heads` and the cell the diagram is drawn at: the play's break-even headcount where the play is ahead (the Notable has no
    other headcount; setup_for needs one).
 6. Which rows are "the break-even rows at both bracketing headcounts" (decision 31 D): read as above, per knob value and per scan.
"""
import csv
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import contract, diagram, formations, rows as rows_mod  # noqa: E402
from scripts.skilllab.contract import Block, Cover, FightResult, Group, Setup, Terrain  # noqa: E402

HEADS = (8, 16, 24, 32, 40, 48)        # the scan range of ruling 4
OPENING_DRAFT = "DRAFT-opening-window-ticks"
SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real engine and the real placed scenes; set OM_LAB_SLOW=1")


# ---------------------------------------------------------------- fixtures (fake data, no engine)

def fr(outcome="side0", **kw):
    base = dict(outcome=outcome, margin=0.5, strength_left=(0.5, 0.0), survivors=(8, 0), heads=(16, 16), ticks=300,
                first_contact_tick=20, firing=[], firing_unit_seconds=(100.0, 50.0), firing_window=(20.0, 10.0),
                weighted_unit_seconds=(110.0, 55.0), weighted_window=(22.0, 11.0), predicted_count="side0",
                predicted_type="side0", agreement="both_right")
    base.update(kw)
    return FightResult(**base)


KNOB = {"range_up": "OM_TP_RANGE_UP_1", "vision": "OM_TP_VISION_UP_1", "damage_up": "OM_TP_DAMAGE_UP_1",
        "arc": "OM_TP_FIRING_ARC_DEG", "cone": "cone", "emitting": "OM_TP_EMIT_SIGHT_MULT"}


def scan_rows(family, play, layout, knob, baseline, beats, kind="grid", per_cell=2, point="-", won=None, **over):
    """The rows one scan writes: per enemy headcount `per_cell` fights; side0 wins up to `beats` (None: lost everywhere); beats == 48
    is a ceiling hit and then ceiling_hit is 1 on every row, as L4 writes it. `won`, a set of headcounts, overrides beats (a scan
    that flips back to won). `point` is set on the finished row, so the helper does not care whether rows.fight_row knows the name."""
    is_won = (lambda h: h in won) if won is not None else (lambda h: beats is not None and h <= beats)
    ceiling = int(all(is_won(h) for h in HEADS))
    out = []
    for h in HEADS:
        for _ in range(per_cell):
            row = rows_mod.fight_row(fr("side0" if is_won(h) else "side1"), knob=KNOB[family], knob_value=float(knob),
                                     baseline=baseline, ceiling_hit=ceiling, prefight="ok", family=family, play=play,
                                     layout=layout, kind=kind, enemy_heads=h, **over)
            row["point"] = point
            out.append(row)
    return out


def sweep_rows(play_be, role_be, family="range_up", play="s3_layer_above", layout="81", refined=(), point="-"):
    """play_be: {knob value: beats of the play}; role_be: {role: {knob value: beats of that baseline}}. Values in `refined` have kind refined."""
    out = []
    for v, b in sorted(play_be.items()):
        out += scan_rows(family, play, layout, v, "none", b, kind="refined" if v in refined else "grid", point=point)
    for role, per_knob in role_be.items():
        for v, b in sorted(per_knob.items()):
            out += scan_rows(family, play, layout, v, role, b, kind="refined" if v in refined else "grid", point=point)
    return out


# gain vs a flat baseline of 16: + at 1.0 and 0.75, - at 0.5 and 0.25 -> exactly one crossing, between 0.5 and 0.75
PLAY_BE = {0.25: 8, 0.5: 8, 0.75: 32, 1.0: 40}
FLAT16 = {0.25: 16, 0.5: 16, 0.75: 16, 1.0: 16}


def crossing_rows(**kw):
    return sweep_rows(PLAY_BE, {"naive_attacker": FLAT16}, **kw)


def both_wrong_row(**over):
    base = dict(outcome="side1", agreement="both_wrong", predicted_count="side0", predicted_type="side0",
                firing_window=(30.0, 10.0), weighted_window=(35.0, 12.0))
    kind, baseline = over.pop("kind", "grid"), over.pop("baseline", "none")
    base.update(over)
    row = rows_mod.fight_row(fr(**base), knob="OM_TP_VISION_UP_1", knob_value=0.5, baseline=baseline, ceiling_hit=0, prefight="ok",
                             family="vision", play="s3_layer_above", layout="78", kind=kind, enemy_heads=16)
    row["point"] = "-"
    return row


def fake_setup(point=(740.0, 300.0)):
    """Both sides stand on two layers (side 0: 8 on layer 1 and 8 on layer 0; side 1: 8 on layer 0 and 8 on layer 1)."""
    groups = (Group(0, "Vanguard", 8, "blob", 250.0, 300.0, 0.0, 1, "attack_move", params={"radius": 80.0}),
              Group(0, "Raider", 8, "line", 150.0, 300.0, 0.0, 0, "attack_move", params={"spacing": 40.0}),
              Group(1, "Vanguard", 8, "blob", 750.0, 260.0, 180.0, 0, "guard", params={"radius": 100.0}),
              Group(1, "Raider", 8, "blob", 750.0, 360.0, 180.0, 1, "guard", params={"radius": 60.0}))
    terrain = Terrain(canvas=(1000.0, 600.0),
                      blocks=(Block(480.0, 20.0, 520.0, 240.0, 0, 2), Block(480.0, 360.0, 520.0, 580.0, 0, 3)),
                      covers=(Cover(650.0, 300.0, 40.0, 1),))
    return Setup(groups=groups, unit_types={}, terrain=terrain, point=point)


def setup_for(_notable):
    return fake_setup()


def cells_of(rows, tmp_path):
    """The CSV text of every row, as the file holds it."""
    path = tmp_path / "rows.csv"
    rows_mod.write_rows(rows, path)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def tag(e):
    return e.tag.split("}")[-1]


def parse(svg):
    root = ET.fromstring(svg)
    assert tag(root) == "svg"
    return root


def els(root, name, cls=None):
    return [e for e in root.iter() if tag(e) == name and (cls is None or cls in (e.get("class") or "").split())]


def arrows(root):
    return [e for e in root.iter() if "arrow" in (e.get("class") or "").split()]


def text_of(e):
    return "".join(e.itertext()).strip()


def viewbox(root):
    parts = root.get("viewBox").split()
    assert len(parts) == 4 and parts[0] == "0" and parts[1] == "0"
    return float(parts[2]), float(parts[3])


def positions_of(setup, side):
    pts = [p for g in setup.groups if g.side == side for p in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def one(rows_, kind):
    found = [n for n in diagram.notables(rows_) if n.kind == kind]
    assert len(found) == 1, found
    return found[0]


def kinds(rows_, kind):
    return [n for n in diagram.notables(rows_) if n.kind == kind]


def first_idx(rows_, **match):
    return next(i for i, r in enumerate(rows_) if all(r[k] == v for k, v in match.items()))


# ---------------------------------------------------------------- read_rows

def test_read_rows_round_trips_typed_cells(tmp_path):
    """read_rows types the INT and FLOAT columns and keeps labels as str (layout "81" stays "81"); None cells read None."""
    rows = crossing_rows()[:3] + [both_wrong_row()]
    path = tmp_path / "r.csv"
    rows_mod.write_rows(rows, path)
    back = diagram.read_rows(path)
    assert len(back) == len(rows)
    for want, got in zip(rows, back):
        assert {k: v for k, v in got.items() if v is not None} == want
    assert back[0]["layout"] == "81" and isinstance(back[0]["layout"], str)
    assert isinstance(back[0]["enemy_heads"], int) and isinstance(back[0]["knob_value"], float)
    assert isinstance(back[0]["ceiling_hit"], int) and isinstance(back[0]["firing_window_0"], float)


def test_read_rows_keeps_the_point_a_str_even_when_it_looks_like_a_number(tmp_path):
    """Negative control of the typing: `point` is a label (`-`, `half=45`, `vision=0.125`), never parsed."""
    rows = scan_rows("cone", "s2_concave", "81", 150, "none", 8, point="half=45")[:1] + crossing_rows()[:1]
    path = tmp_path / "r.csv"
    rows_mod.write_rows(rows, path)
    back = diagram.read_rows(path)
    assert [r["point"] for r in back] == ["half=45", "-"] and all(isinstance(r["point"], str) for r in back)


# ---------------------------------------------------------------- the crossing detector (positive and negative controls)

def test_crossing_positive_control_one_sign_change_is_one_crossing_between_adjacent_knob_values():
    """Ruling 12 (where the lines cross): the gain turns from - at 0.5 to + at 0.75 -> exactly one crossing, role naive_attacker."""
    n = one(crossing_rows(), diagram.CROSSING)
    assert (n.family, n.play, n.layout, n.point, n.role) == ("range_up", "s3_layer_above", "81", "-", "naive_attacker")
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75) and n.row is None
    assert n.heads == 32                      # the play is ahead at 0.75 and its break-even there is 32 (QUESTION 5)


def test_crossing_heads_is_read_where_the_play_is_ahead_also_when_that_is_the_low_knob_value():
    """Positive control of the other direction: ahead at 0.25 (break-even 40), behind at 0.5 (8) -> heads 40, not 8."""
    rows = sweep_rows({0.25: 40, 0.5: 8}, {"naive_attacker": {0.25: 16, 0.5: 16}})
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi, n.heads) == (0.25, 0.5, 40)


def test_crossing_negative_control_a_play_ahead_everywhere_has_no_crossing():
    """Control: gain > 0 at every knob value -> no crossing notable."""
    always = sweep_rows({0.25: 32, 0.5: 32, 0.75: 40, 1.0: 40}, {"naive_attacker": FLAT16})
    assert kinds(always, diagram.CROSSING) == []


def test_crossing_negative_control_a_play_behind_everywhere_has_no_crossing():
    behind = sweep_rows({0.25: 8, 0.5: 8, 0.75: 8, 1.0: 8}, {"naive_attacker": FLAT16})
    assert kinds(behind, diagram.CROSSING) == []


def test_zero_gain_is_not_ahead():
    """gain > 0 is the sign (sweep.py): equal break-evens are not ahead, so equal at 0.5 and ahead at 0.75 is a crossing."""
    eq = sweep_rows({0.5: 16, 0.75: 32}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    n = one(eq, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75)


def test_a_play_lost_in_every_cell_has_break_even_zero_and_is_behind_a_baseline_that_wins_somewhere():
    """First-lost-cell path (scan._crossing finds no won-to-lost step): break-even 0. Play lost everywhere at 0.5 vs baseline 16 is
    behind (gain -16), ahead at 0.75 (32 - 16): a crossing. Together with the equal-zero case below it separates 0 from 'no scan'."""
    rows = sweep_rows({0.5: None, 0.75: 32}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi, n.heads) == (0.5, 0.75, 32)


def test_a_lost_first_cell_does_not_make_the_break_even_zero_when_a_later_cell_is_won():
    """First-lost-cell path: won at 16 and 24 but lost at 8. scan._crossing reads only won-to-lost steps, so 8 (lost) then 16 (won) is no
    step and the break-even is 24 (before the 24 -> 32 step). Against a flat 16: ahead at 0.5 (24), level at 0.75 (16, won={16}): a crossing
    whose play is ahead at the low knob value, so heads = 24."""
    rows = (scan_rows("range_up", "s3_layer_above", "81", 0.5, "none", None, won={16, 24}) +
            scan_rows("range_up", "s3_layer_above", "81", 0.5, "naive_attacker", 16) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "none", None, won={16}) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "naive_attacker", 16))
    # break-even(play@0.5) = 24 (before the first won-to-lost step 24 -> 32) > 16: ahead; play@0.75 = 16, gain 0: not ahead -> a crossing
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi, n.heads) == (0.5, 0.75, 24)


def test_two_lost_everywhere_scans_have_gain_zero_and_no_crossing():
    """Negative control of the break-even-0 path: play None vs baseline None is gain 0, not ahead, at every knob value."""
    rows = sweep_rows({0.5: None, 0.75: None}, {"naive_attacker": {0.5: None, 0.75: None}})
    assert kinds(rows, diagram.CROSSING) == []


def test_a_play_ahead_of_a_baseline_that_is_lost_everywhere_is_ahead():
    """Break-even 0 of the baseline: play 8 vs None is gain +8 at both knob values, so no crossing; with the play at None at 0.5 it is gain 0."""
    ahead = sweep_rows({0.5: 8, 0.75: 8}, {"naive_attacker": {0.5: None, 0.75: None}})
    assert kinds(ahead, diagram.CROSSING) == []
    flip = sweep_rows({0.5: None, 0.75: 8}, {"naive_attacker": {0.5: None, 0.75: None}})
    n = one(flip, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75)


def test_break_even_is_before_the_first_won_to_lost_step_so_a_later_flip_back_to_won_is_not_read():
    """Multi-flip path: the play at 0.5 wins 8, loses 16, wins 24 and 32, loses the rest. Break-even = 8 (first step), not 32. Against
    a flat 16 it is behind at 0.5 and ahead at 0.75 (32): one crossing. A detector that took the last won cell would call 0.5 ahead
    (32 - 16) and find none."""
    rows = (scan_rows("range_up", "s3_layer_above", "81", 0.5, "none", None, won={8, 24, 32}) +
            scan_rows("range_up", "s3_layer_above", "81", 0.5, "naive_attacker", 16) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "none", 32) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "naive_attacker", 16))
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi, n.heads) == (0.5, 0.75, 32)


def test_a_sign_change_in_a_sign_flip_or_control_row_is_not_a_crossing():
    """Controls and the labelled sign-flip point are never read for a crossing (ruling 10, decision 21)."""
    rows = sweep_rows({0.5: 32, 1.0: 40}, {"naive_attacker": {0.5: 16, 1.0: 16}})
    rows += scan_rows("range_up", "s3_layer_above", "81", 2.0, "none", 8, kind="sign_flip")
    rows += scan_rows("range_up", "s3_layer_above", "81", 2.0, "naive_attacker", 16, kind="sign_flip")
    rows += scan_rows("range_up", "s3_layer_above", "81", 0.0, "none", 8, kind="control_positive")
    rows += scan_rows("range_up", "s3_layer_above", "81", 0.0, "naive_attacker", 16, kind="control_null")
    assert kinds(rows, diagram.CROSSING) == []


def test_a_refined_point_brackets_the_crossing_more_tightly():
    """A refined value 0.625 between the coarse 0.5 (-) and 0.75 (+) turns the crossing into the adjacent pair (0.5, 0.625) or (0.625, 0.75)."""
    rows = sweep_rows({0.25: 8, 0.5: 8, 0.625: 32, 0.75: 32, 1.0: 40}, {"naive_attacker": {0.25: 16, 0.5: 16, 0.625: 16, 0.75: 16, 1.0: 16}},
                      refined=(0.625,))
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.625)


def test_defending_play_gets_a_second_crossing_against_the_naive_defender():
    """Decisions 24: each baseline role the rows carry gets its own crossing; two roles that both flip -> two notables, one per role."""
    both = sweep_rows(PLAY_BE, {"naive_attacker": FLAT16, "naive_defender": {0.25: 16, 0.5: 16, 0.75: 36, 1.0: 36}})
    found = kinds(both, diagram.CROSSING)
    assert sorted(n.role for n in found) == ["naive_attacker", "naive_defender"]
    by_role = {n.role: (n.knob_lo, n.knob_hi) for n in found}
    assert by_role["naive_attacker"] == (0.5, 0.75) and by_role["naive_defender"] == (0.75, 1.0)
    assert len({n.id for n in found}) == 2


def test_a_meeting_with_only_the_attacker_baseline_has_one_crossing_and_none_for_a_defender():
    """Control for the above: no naive_defender* rows -> no crossing with such a role."""
    assert [n.role for n in kinds(crossing_rows(), diagram.CROSSING)] == ["naive_attacker"]


def test_the_layer_play_defender_variants_are_roles_of_their_own():
    """Decision 25: naive_defender_attacker_layer and naive_defender_play_layer are separate baseline roles, each read by itself."""
    rows = sweep_rows(PLAY_BE, {"naive_defender_attacker_layer": FLAT16, "naive_defender_play_layer": {0.25: 4, 0.5: 4, 0.75: 4, 1.0: 4}})
    found = {n.role: (n.knob_lo, n.knob_hi) for n in kinds(rows, diagram.CROSSING)}
    assert found == {"naive_defender_attacker_layer": (0.5, 0.75)}


def test_a_defect_cell_is_not_won_so_it_cannot_make_a_play_ahead():
    """A cell is won only when every row is side0 (scan.cell_result): one cap row in a cell makes it lost, as in the scan."""
    rows = sweep_rows({0.5: 40, 0.75: 40}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    for r in rows:
        if r["baseline"] == "none" and r["knob_value"] == 0.75 and r["enemy_heads"] == 16:
            r["outcome"] = "cap"
            break
    # play at 0.75: heads 8 won, 16 has one cap row -> lost, break-even 8 < 16: behind; at 0.5 it is ahead -> a crossing
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75)


# ---------------------------------------------------------------- the series: point groups the rows (decision 31 A)

def cone_series(point, play_be, family="cone", play="s2_concave", layout="81", role_be=None):
    return sweep_rows(play_be, {"naive_attacker": role_be or {k: 16 for k in play_be}}, family=family, play=play, layout=layout, point=point)


def test_two_series_with_the_same_knob_values_are_two_crossings_not_one_merged_scan():
    """Positive control: half=22.5 and half=45 both cross between range 150 and 300; they share knob_value and enemy_heads and differ
    only in `point`. Grouped by (family, play, layout, point) there are two crossings with two ids; merged, there would be one."""
    rows = cone_series("half=22.5", {150: 8, 300: 32, 600: 40}) + cone_series("half=45", {150: 8, 300: 32, 600: 40})
    found = kinds(rows, diagram.CROSSING)
    assert [(n.point, n.knob_lo, n.knob_hi) for n in found] == [("half=22.5", 150.0, 300.0), ("half=45", 150.0, 300.0)]
    assert len({n.id for n in found}) == 2 and all(re.fullmatch(r"[A-Za-z0-9_-]+", n.id) for n in found)


def test_a_series_ahead_everywhere_does_not_hide_the_crossing_of_its_neighbour():
    """Negative control of the merge: half=90 is ahead at every range, half=22.5 crosses; only the second is a crossing."""
    rows = cone_series("half=90", {150: 32, 300: 32, 600: 40}) + cone_series("half=22.5", {150: 8, 300: 32, 600: 40})
    found = kinds(rows, diagram.CROSSING)
    assert [(n.point, n.knob_lo, n.knob_hi) for n in found] == [("half=22.5", 150.0, 300.0)]


def test_the_nine_cone_points_are_three_series_read_along_range():
    """Cone 3 by 3: each half-angle is a series along range. The crossing sits between 300 and 600 in one series and between 150 and 300 in
    another; a series that never changes sign has none. knob_lo and knob_hi are floats."""
    rows = (cone_series("half=22.5", {150: 8, 300: 8, 600: 32}) + cone_series("half=45", {150: 8, 300: 32, 600: 40}) +
            cone_series("half=90", {150: 32, 300: 32, 600: 40}))
    found = {n.point: (n.knob_lo, n.knob_hi) for n in kinds(rows, diagram.CROSSING)}
    assert found == {"half=22.5": (300.0, 600.0), "half=45": (150.0, 300.0)}
    assert all(isinstance(v, float) for pair in found.values() for v in pair)


def test_emitting_vision_levels_are_series_along_sight():
    rows = cone_series("vision=0.125", {1.0: 8, 2.0: 32, 4.0: 40}, family="emitting", play="s3_dark_striker") + \
        cone_series("vision=0.25", {1.0: 32, 2.0: 32, 4.0: 40}, family="emitting", play="s3_dark_striker")
    found = [(n.point, n.knob_lo, n.knob_hi) for n in kinds(rows, diagram.CROSSING)]
    assert found == [("vision=0.125", 1.0, 2.0)]


def test_a_row_without_a_series_label_in_another_series_does_not_join_it():
    """The `-` series of range_up and a cone series of the same play name never mix (family is part of the group too)."""
    rows = crossing_rows(play="s2_concave") + cone_series("half=45", {150: 32, 300: 32, 600: 40})
    found = kinds(rows, diagram.CROSSING)
    assert [(n.family, n.point) for n in found] == [("range_up", "-")]


# ---------------------------------------------------------------- the ceiling-hit detector

def ceiling_rows(ceiling_beats=48, **kw):
    return sweep_rows({0.5: ceiling_beats, 1.0: 24}, {"naive_attacker": {0.5: 16, 1.0: 16}}, **kw)


def test_ceiling_hit_positive_control_one_notable_per_family_play_layout_point_knob():
    """Ruling 4: a play that beats the top headcount at one knob value is a ceiling hit notable, never 'no gain'."""
    n = one(ceiling_rows(), diagram.CEILING_HIT)
    assert (n.family, n.play, n.layout, n.point, n.role, n.knob_lo, n.knob_hi, n.row) == \
        ("range_up", "s3_layer_above", "81", "-", "none", 0.5, 0.5, None)
    assert n.heads == 48


def test_ceiling_hits_of_two_series_at_the_same_knob_value_are_two_notables():
    rows = cone_series("half=22.5", {300: 48}) + cone_series("half=45", {300: 48})
    found = kinds(rows, diagram.CEILING_HIT)
    assert [(n.point, n.knob_lo) for n in found] == [("half=22.5", 300.0), ("half=45", 300.0)] and len({n.id for n in found}) == 2


def test_ceiling_hit_negative_control_no_ceiling_rows_no_notable():
    assert kinds(ceiling_rows(ceiling_beats=40), diagram.CEILING_HIT) == []


def test_a_baseline_scan_that_hits_the_ceiling_is_not_a_ceiling_hit_notable():
    """The play's own rows (baseline none) carry the notable; a naive baseline at the ceiling does not (QUESTION 1)."""
    rows = sweep_rows({0.5: 24}, {"naive_attacker": {0.5: 48}})
    assert kinds(rows, diagram.CEILING_HIT) == []


def test_a_ceiling_hit_in_a_control_kind_is_not_a_notable():
    rows = scan_rows("range_up", "s3_layer_above", "81", 0.0, "none", 48, kind="control_positive")
    assert kinds(rows, diagram.CEILING_HIT) == []


def test_baseline_ceiling_is_listed_for_a_baseline_that_also_wins_everywhere_and_is_never_a_notable():
    """Decision 29 item 3. Positive control: naive_attacker beats 48 at 0.5 while the play beats 24: listed, with its role, and no
    ceiling_hit notable comes from it (the play's own rows are not at the ceiling)."""
    rows = sweep_rows({0.5: 24, 1.0: 24}, {"naive_attacker": {0.5: 48, 1.0: 16}})
    assert diagram.baseline_ceilings(rows) == [dict(family="range_up", play="s3_layer_above", layout="81", point="-",
                                                    role="naive_attacker", knob_value=0.5)]
    assert [n for n in diagram.notables(rows) if n.kind == diagram.CEILING_HIT] == []


def test_baseline_ceiling_is_listed_beside_a_play_that_also_hits_the_ceiling_with_its_own_notable():
    """Both win everywhere: the play's ceiling hit is a notable, the baseline's is a baseline_ceiling; no crossing is possible there."""
    rows = sweep_rows({0.5: 48, 1.0: 24}, {"naive_attacker": {0.5: 48, 1.0: 16}, "naive_defender": {0.5: 16, 1.0: 16}})
    assert [(d["role"], d["knob_value"]) for d in diagram.baseline_ceilings(rows)] == [("naive_attacker", 0.5)]
    assert [(n.kind, n.knob_lo) for n in diagram.notables(rows) if n.kind == diagram.CEILING_HIT] == [(diagram.CEILING_HIT, 0.5)]


def test_baseline_ceiling_negative_controls_none_listed_for_a_play_ceiling_a_control_or_a_sign_flip():
    assert diagram.baseline_ceilings(ceiling_rows()) == []                                 # only the play (baseline none) hits it
    ctl = scan_rows("range_up", "s3_layer_above", "81", 0.0, "naive_attacker", 48, kind="control_null")
    flip = scan_rows("range_up", "s3_layer_above", "81", 2.0, "naive_attacker", 48, kind="sign_flip")
    assert diagram.baseline_ceilings(ctl + flip) == [] and diagram.baseline_ceilings([]) == []


def test_baseline_ceilings_are_sorted_with_the_notable_keys_and_one_per_role_and_knob():
    rows = (cone_series("half=45", {300: 8, 600: 8}, role_be={300: 48, 600: 48}) +
            cone_series("half=22.5", {300: 8}, role_be={300: 48}, play="a_play"))
    got = [(d["play"], d["point"], d["knob_value"]) for d in diagram.baseline_ceilings(rows)]
    assert got == [("a_play", "half=22.5", 300.0), ("s2_concave", "half=45", 300.0), ("s2_concave", "half=45", 600.0)]


# ---------------------------------------------------------------- the both_wrong detector

def test_both_wrong_positive_control_every_both_wrong_row_is_a_finding():
    rows = crossing_rows() + [both_wrong_row(), both_wrong_row(ticks=301), both_wrong_row(ticks=302)]
    found = kinds(rows, diagram.BOTH_WRONG)
    assert [n.row for n in found] == [len(rows) - 3, len(rows) - 2, len(rows) - 1]
    assert {(n.family, n.play, n.layout, n.point, n.role, n.heads) for n in found} == {("vision", "s3_layer_above", "78", "-", "none", 16)}
    assert len({n.id for n in found}) == 3


@pytest.mark.parametrize("agreement", ["both_right", "count_wrong_type_right", "count_right_type_wrong", "n/a"])
def test_both_wrong_negative_control_the_other_four_agreements_are_not_notable(agreement):
    row = both_wrong_row(agreement=agreement)
    assert kinds([row], diagram.BOTH_WRONG) == []


@pytest.mark.parametrize("kind,baseline", [("control_positive", "none"), ("control_null", "none"), ("control_smoke", "none"),
                                           ("grid", "naive_attacker"), ("grid", "naive_defender")])
def test_both_wrong_in_a_control_or_a_baseline_row_is_a_notable_with_the_role_and_kind_in_the_label(kind, baseline):
    """Decision 29 item 6: the strongest finding against the measure is a both_wrong on a control; the label carries the role (and the
    kind of a control) so the page can say what was wrong."""
    rows = [both_wrong_row(kind=kind, baseline=baseline)]
    n = one(rows, diagram.BOTH_WRONG)
    assert n.role == baseline and n.row == 0
    title = text_of(els(parse(diagram.render(n, rows, fake_setup())), "title")[0])
    if kind.startswith("control_"):
        assert kind in title
    if baseline != "none":
        assert baseline in title


def test_a_plain_play_row_both_wrong_title_names_neither_a_baseline_nor_a_control_kind_negative_control():
    rows = [both_wrong_row()]
    title = text_of(els(parse(diagram.render(one(rows, diagram.BOTH_WRONG), rows, fake_setup())), "title")[0])
    assert "naive" not in title and "control_" not in title


# ---------------------------------------------------------------- order, ids, determinism, the no-notable control

def multi_rows():
    """16 crossings (2 families x 2 plays x 2 layouts x 2 roles), the rows given in the reverse of the order the detector returns them."""
    rows = []
    for family in ("vision", "range_up"):
        for play in ("s3_types_by_reach", "s3_layer_above"):
            for layout in ("78", "192"):
                rows += sweep_rows(PLAY_BE, {"naive_defender": FLAT16, "naive_attacker": FLAT16}, family=family, play=play, layout=layout)
    return rows


def every_kind_rows():
    return crossing_rows() + ceiling_rows(play="s3_types_by_reach") + [both_wrong_row()]


def test_notables_are_ordered_crossing_then_ceiling_then_both_wrong_and_deterministic():
    rows = every_kind_rows()
    a, b = diagram.notables(rows), diagram.notables(list(rows))
    assert a == b
    assert [n.kind for n in a] == [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG]


def test_crossings_are_sorted_by_family_play_layout_role_as_strings():
    """Within a kind: (family, play, layout, point, role, knob_lo). Layout is a str: "192" sorts before "78"."""
    got = [(n.family, n.play, n.layout, n.role) for n in kinds(multi_rows(), diagram.CROSSING)]
    want = [(f, p, l, r) for f in ("range_up", "vision") for p in ("s3_layer_above", "s3_types_by_reach") for l in ("192", "78")
            for r in ("naive_attacker", "naive_defender")]
    assert got == want and len(got) == 16


def test_notables_do_not_depend_on_the_order_of_the_rows():
    rows = multi_rows() + ceiling_rows(play="s3_types_by_reach")
    assert diagram.notables(rows[::-1]) == diagram.notables(rows)


def test_series_sort_by_point_as_a_string_inside_a_family_play_layout():
    rows = (cone_series("half=90", {150: 8, 300: 32}) + cone_series("half=22.5", {150: 8, 300: 32}) + cone_series("half=45", {150: 8, 300: 32}))
    assert [n.point for n in kinds(rows, diagram.CROSSING)] == ["half=22.5", "half=45", "half=90"]


def test_crossings_of_one_series_are_ordered_by_numeric_knob_lo_arc_7_5_before_15():
    """A string sort puts "15.0" before "7.5". Gain -, +, -, -, - over 7.5, 15, 30, 60, 120 (the arc grid, decision 47): crossings
    (7.5, 15) and (15, 30)."""
    rows = sweep_rows({7.5: 8, 15: 32, 30: 8, 60: 8, 120: 8}, {"naive_attacker": {v: 16 for v in (7.5, 15, 30, 60, 120)}},
                      family="arc", play="s2_concave")
    got = [(n.knob_lo, n.knob_hi) for n in kinds(rows, diagram.CROSSING)]
    assert got == [(7.5, 15.0), (15.0, 30.0)]
    assert [(n.knob_lo, n.knob_hi) for n in kinds(rows[::-1], diagram.CROSSING)] == got


def test_cone_range_crossing_has_float_bounds_150_and_300():
    rows = cone_series("half=45", {150: 8, 300: 32, 600: 40})
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (150.0, 300.0) and isinstance(n.knob_lo, float) and isinstance(n.knob_hi, float)


def test_ceiling_hits_are_ordered_by_numeric_knob_value_7_5_15_120():
    """A string sort gives 120.0, 15.0, 7.5."""
    rows = sweep_rows({120: 48, 7.5: 48, 15: 48}, {}, family="arc", play="s2_concave")
    got = [n.knob_lo for n in kinds(rows, diagram.CEILING_HIT)]
    assert got == [7.5, 15.0, 120.0] and [n.knob_lo for n in kinds(rows[::-1], diagram.CEILING_HIT)] == got


def test_ceiling_hits_sort_by_family_play_layout_then_knob():
    rows = (sweep_rows({0.5: 48}, {}, family="vision", play="b_play", layout="78") + sweep_rows({0.5: 48}, {}, family="range_up", play="b_play", layout="78") +
            sweep_rows({0.5: 48}, {}, family="range_up", play="a_play", layout="81") + sweep_rows({0.5: 48}, {}, family="range_up", play="a_play", layout="192"))
    assert [(n.family, n.play, n.layout) for n in kinds(rows, diagram.CEILING_HIT)] == [
        ("range_up", "a_play", "192"), ("range_up", "a_play", "81"), ("range_up", "b_play", "78"), ("vision", "b_play", "78")]


def test_both_wrong_notables_are_ordered_by_row_index():
    rows = [both_wrong_row(ticks=t) for t in (1, 2, 3)]
    assert [n.row for n in kinds(rows, diagram.BOTH_WRONG)] == [0, 1, 2]


def test_ids_are_filesystem_safe_unique_and_a_function_of_the_fields():
    rows = multi_rows() + ceiling_rows(play="s3_types_by_reach") + [both_wrong_row(), both_wrong_row(ticks=301)]
    ns = diagram.notables(rows)
    assert len(ns) >= 18
    ids = [n.id for n in ns]
    assert len(set(ids)) == len(ids) and all(re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)
    assert [n.id for n in diagram.notables(rows)] == ids


def test_ids_differ_across_knob_values_series_and_points_that_look_alike():
    """Unique across knob values: the two crossings of one arc series, the three ceiling hits, and points whose text is close
    ("half=22.5" and "half=225" must not collapse once the characters outside [A-Za-z0-9_-] are replaced)."""
    arc = sweep_rows({7.5: 8, 15: 32, 30: 8}, {"naive_attacker": {7.5: 16, 15: 16, 30: 16}}, family="arc", play="s2_concave")
    ceil = sweep_rows({7.5: 48, 15: 48, 120: 48}, {}, family="arc", play="s2_concave")
    alike = cone_series("half=22.5", {300: 48}) + cone_series("half=225", {300: 48}) + cone_series("half=22-5", {300: 48})
    for rows in (arc, ceil, alike):
        ids = [n.id for n in diagram.notables(rows)]
        assert len(ids) >= 2 and len(set(ids)) == len(ids), ids
    assert len(diagram.notables(alike)) == 3


def test_ids_and_notables_are_the_same_across_processes_with_different_hash_seeds():
    """No hash order, no clock, no counter (determinism is a contract): the ids and the svg bytes of one fixture in two fresh
    interpreters with PYTHONHASHSEED 0 and 1 hash to the same value."""
    script = (
        "import sys, hashlib\n"
        "sys.path.insert(0, %r)\nsys.path.insert(0, %r)\n"
        "import test_diagram as t\n"
        "from scripts.skilllab import diagram\n"
        "rows = t.multi_rows() + t.ceiling_rows(play='s3_types_by_reach') + [t.both_wrong_row()] + "
        "t.cone_series('half=45', {150: 8, 300: 32, 600: 40}) + t.cone_series('half=22.5', {150: 8, 300: 32, 600: 40})\n"
        "out = diagram.render_all(rows, t.setup_for)\n"
        "h = hashlib.sha256()\n"
        "for k, v in out.items():\n    h.update(k.encode()); h.update(v.encode())\n"
        "print(len(out), h.hexdigest())\n" % (str(ROOT), str(Path(__file__).resolve().parent)))
    outs = []
    for seed in ("0", "1"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        done = subprocess.run([sys.executable, "-c", script], cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr[-2000:]
        outs.append(done.stdout.strip())
    assert outs[0] == outs[1] and int(outs[0].split()[0]) >= 18


def test_no_crossing_no_ceiling_no_both_wrong_means_no_diagram_at_all_and_no_directory(tmp_path):
    """The control of the spec row: a fake with no crossing produces no diagram, no file and no directory."""
    rows = sweep_rows({0.25: 32, 0.5: 32, 0.75: 40, 1.0: 40}, {"naive_attacker": FLAT16, "naive_defender": FLAT16})
    assert diagram.notables(rows) == []
    assert diagram.render_all(rows, setup_for) == {}
    assert diagram.write_all(rows, setup_for, tmp_path / "out") == []
    assert not list(tmp_path.rglob("*.svg")) and not (tmp_path / "out").exists()


# ---------------------------------------------------------------- render: shape, layout, legend

@pytest.fixture(scope="module")
def rendered():
    rows = every_kind_rows()
    return rows, {n.kind: (n, diagram.render(n, rows, fake_setup())) for n in diagram.notables(rows)}


ALL_KINDS = [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG]


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_render_is_one_well_formed_svg_with_the_notable_in_its_attributes(rendered, kind):
    rows, by_kind = rendered
    n, svg = by_kind[kind]
    root = parse(svg)
    assert viewbox(root)[0] > 0 and viewbox(root)[1] > 0
    assert root.get("id") == n.id and root.get("data-kind") == kind
    assert (root.get("data-family"), root.get("data-play"), root.get("data-layout"), root.get("data-point"), root.get("data-role")) == \
        (n.family, n.play, n.layout, n.point, n.role)
    title = [text_of(e) for e in els(root, "title")]
    assert title and all(w in title[0] for w in (n.family, n.play, n.layout))


def test_a_series_notable_carries_its_point_in_the_attribute():
    rows = cone_series("half=22.5", {150: 8, 300: 32, 600: 40})
    n = one(rows, diagram.CROSSING)
    assert parse(diagram.render(n, rows, fake_setup())).get("data-point") == "half=22.5"


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_render_is_deterministic_byte_for_byte(rendered, kind):
    """The same input gives the same bytes: no clock, no counter, no hash order (determinism is a contract)."""
    rows, by_kind = rendered
    n, svg = by_kind[kind]
    assert diagram.render(n, rows, fake_setup()) == svg
    assert diagram.render(n, [dict(reversed(list(r.items()))) for r in rows], fake_setup()) == svg      # key order of a row is not input


def test_render_all_equals_render_per_notable_and_write_all_writes_those_bytes(tmp_path):
    rows = every_kind_rows()
    got = diagram.render_all(rows, setup_for)
    ns = diagram.notables(rows)
    assert list(got) == [n.id for n in ns]
    for n in ns:
        assert got[n.id] == diagram.render(n, rows, fake_setup())
    paths = diagram.write_all(rows, setup_for, tmp_path / "svgs")
    assert [Path(p).name for p in paths] == [n.id + ".svg" for n in ns]
    for p, n in zip(paths, ns):
        assert Path(p).read_text(encoding="utf-8") == got[n.id]


def test_render_all_asks_setup_for_once_per_notable_in_notables_order():
    rows = every_kind_rows()
    asked = []
    diagram.render_all(rows, lambda n: asked.append(n) or fake_setup())
    assert asked == diagram.notables(rows)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_layout_has_every_unit_with_side_layer_type_and_world_position(rendered, kind):
    _, by_kind = rendered
    root = parse(by_kind[kind][1])
    setup = fake_setup()
    units = els(root, "circle", "unit")
    assert len(units) == sum(g.count for g in setup.groups) == 32
    want = []
    for g in setup.groups:
        for (x, y) in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            want.append((g.side, g.layer, g.unit, round(x, 3), round(y, 3)))
    got = [(int(u.get("data-side")), int(u.get("data-layer")), u.get("data-unit"), round(float(u.get("data-x")), 3),
            round(float(u.get("data-y")), 3)) for u in units]
    assert sorted(got) == sorted(want)
    assert {u.get("data-unit") for u in units} == {"Vanguard", "Raider"}          # the type name, never an index
    for u in units:
        classes = u.get("class").split()
        assert "side" + u.get("data-side") in classes and "layer-" + u.get("data-layer") in classes
    for side in ("0", "1"):                       # a layer play shows both layers, on both sides
        assert {u.get("data-layer") for u in units if u.get("data-side") == side} == {"0", "1"}, side


def test_layout_x_order_is_kept_and_everything_is_inside_the_viewbox(rendered):
    _, by_kind = rendered
    root = parse(by_kind[diagram.CROSSING][1])
    w, h = viewbox(root)
    units = sorted(els(root, "circle", "unit"), key=lambda u: float(u.get("data-x")))
    cx = [float(u.get("cx")) for u in units]
    assert cx == sorted(cx)
    for u in units:
        assert 0 <= float(u.get("cx")) <= w and 0 <= float(u.get("cy")) <= h
    for r in els(root, "rect", "wall"):
        assert 0 <= float(r.get("x")) and float(r.get("x")) + float(r.get("width")) <= w
        assert 0 <= float(r.get("y")) and float(r.get("y")) + float(r.get("height")) <= h


def test_layout_has_the_walls_the_covers_and_the_point(rendered):
    _, by_kind = rendered
    root = parse(by_kind[diagram.CROSSING][1])
    walls = [(float(r.get("data-x0")), float(r.get("data-y0")), float(r.get("data-x1")), float(r.get("data-y1")),
              int(r.get("data-layer-lo")), int(r.get("data-layer-hi"))) for r in els(root, "rect", "wall")]
    assert sorted(walls) == [(480.0, 20.0, 520.0, 240.0, 0, 2), (480.0, 360.0, 520.0, 580.0, 0, 3)]
    covers = [(float(c.get("data-x")), float(c.get("data-y")), float(c.get("data-radius")), int(c.get("data-height")))
              for c in els(root, "circle", "cover")]
    assert covers == [(650.0, 300.0, 40.0, 1)]
    pts = els(root, "g", "point")
    assert len(pts) == 1 and (float(pts[0].get("data-x")), float(pts[0].get("data-y"))) == (740.0, 300.0)


def test_layout_without_terrain_or_point_draws_no_wall_cover_or_point():
    """Negative control of the layout elements."""
    rows = crossing_rows()
    setup = Setup(groups=fake_setup().groups, unit_types={})
    root = parse(diagram.render(one(rows, diagram.CROSSING), rows, setup))
    assert not els(root, "rect", "wall") and not els(root, "circle", "cover") and not els(root, "g", "point")
    assert len(els(root, "circle", "unit")) == 32


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_legend_names_the_sides_the_walls_the_point_the_arrows_and_the_layers(rendered, kind):
    _, by_kind = rendered
    root = parse(by_kind[kind][1])
    legends = els(root, "g", "legend")
    assert len(legends) == 1
    text = " ".join(text_of(t) for t in els(legends[0], "text")).lower()
    for word in ("side 0", "side 1", "wall", "point", "arrow", "layer"):
        assert word in text, word


# ---------------------------------------------------------------- render: arrows carry the CSV value they come from

def arrow_facts(root):
    out = []
    for a in arrows(root):
        out.append(dict(kind=a.get("data-kind"), classes=(a.get("class") or "").split(), column=a.get("data-column"), value=a.get("data-value"),
                        row=int(a.get("data-row")), side=a.get("data-target-side"), tx=float(a.get("data-target-x")),
                        ty=float(a.get("data-target-y")), draft=a.get("data-draft"), outcome=a.get("data-outcome"),
                        knob=a.get("data-knob"), role=a.get("data-role"),
                        label=text_of([e for e in a.iter() if tag(e) == "text"][0]), el=a))
    return out


ARROW_KINDS = {diagram.CROSSING: {"play", "baseline"}, diagram.CEILING_HIT: {"ceiling"}, diagram.BOTH_WRONG: {"window", "prediction", "outcome"}}


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_every_arrow_has_a_kind_its_class_token_and_only_its_notables_kinds(rendered, kind):
    """arrow-{kind} is the class token carrying the arrow's data-kind; a crossing draws play and baseline arrows, a ceiling hit ceiling
    arrows, a both_wrong window, prediction and outcome arrows, and nothing else."""
    _, by_kind = rendered
    facts = arrow_facts(parse(by_kind[kind][1]))
    assert facts
    for f in facts:
        assert f["kind"] in ARROW_KINDS[kind], f
        assert "arrow" in f["classes"] and ("arrow-" + f["kind"]) in f["classes"], f
        assert len([c for c in f["classes"] if c.startswith("arrow-")]) == 1
    assert {f["kind"] for f in facts} == ARROW_KINDS[kind]


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_every_arrow_label_equals_a_csv_value(rendered, kind, tmp_path):
    """Spec row: 'every arrow label equals a CSV value': data-value is the CSV text of rows[data-row][data-column]; the label shows it
    (a crossing arrow's label is the pair "(enemy_heads, outcome)", both CSV texts)."""
    rows, by_kind = rendered
    csv_cells = cells_of(rows, tmp_path)
    facts = arrow_facts(parse(by_kind[kind][1]))
    assert facts
    for f in facts:
        assert f["value"] == csv_cells[f["row"]][f["column"]], f
        if kind == diagram.CROSSING:
            assert f["outcome"] == csv_cells[f["row"]]["outcome"] and f["knob"] == csv_cells[f["row"]]["knob_value"]
            assert f["label"] == "(%s, %s)" % (csv_cells[f["row"]]["enemy_heads"], csv_cells[f["row"]]["outcome"]), f
        else:
            assert f["label"].startswith("%s %s" % (f["column"], f["value"])), f
        assert ("DRAFT" in f["label"]) == (f["draft"] is not None)


@pytest.mark.parametrize("kind", ALL_KINDS)
def test_every_arrow_has_a_line_inside_the_viewbox(rendered, kind):
    _, by_kind = rendered
    root = parse(by_kind[kind][1])
    w, h = viewbox(root)
    for a in arrows(root):
        lines = [e for e in a.iter() if tag(e) == "line"]
        assert len(lines) == 1
        x1, y1, x2, y2 = (float(lines[0].get(k)) for k in ("x1", "y1", "x2", "y2"))
        assert 0 <= x1 <= w and 0 <= x2 <= w and 0 <= y1 <= h and 0 <= y2 <= h
        assert (x1, y1) != (x2, y2)


def crossing_evidence(rows, n):
    """(kind, knob, enemy_heads) -> arrow fact, for the crossing diagram of notable n."""
    svg = diagram.render(n, rows, fake_setup())
    facts = arrow_facts(parse(svg))
    got = {(f["kind"], float(f["knob"]), int(f["value"])): f for f in facts}
    assert len(got) == len(facts)
    return got


def test_crossing_arrows_mark_the_break_even_rows_at_both_bracketing_headcounts_for_the_play_and_the_baseline(rendered):
    """Decision 31 D, the worked example. PLAY_BE (8 at 0.5, 32 at 0.75) and a flat baseline 16: at each knob value each scan has a
    won-to-lost step, so each shows the won cell and the lost cell next to it: 2 knob values x 2 scans x 2 headcounts = 8 arrows."""
    rows, by_kind = rendered
    n, svg = by_kind[diagram.CROSSING]
    got = crossing_evidence(rows, n)
    assert set(got) == {("play", 0.5, 8), ("play", 0.5, 16), ("baseline", 0.5, 16), ("baseline", 0.5, 24),
                        ("play", 0.75, 32), ("play", 0.75, 40), ("baseline", 0.75, 16), ("baseline", 0.75, 24)}
    for (kind, knob, heads), f in got.items():
        r = rows[f["row"]]
        assert (r["family"], r["play"], r["layout"], r["point"]) == (n.family, n.play, n.layout, n.point)
        assert r["baseline"] == ("none" if kind == "play" else n.role) and f["role"] == r["baseline"]
        assert (r["kind"] in ("grid", "refined")) and r["knob_value"] == knob and r["enemy_heads"] == heads
        assert f["row"] == first_idx(rows, family=n.family, play=n.play, layout=n.layout, point=n.point, baseline=r["baseline"],
                                     knob_value=knob, enemy_heads=heads)                     # the first row of the cell
        assert f["column"] == "enemy_heads" and f["side"] == "0" and f["draft"] is None


def test_crossing_arrows_label_the_won_cell_side0_and_the_lost_cell_side1(rendered):
    """The labels are (enemy_heads, outcome): the break-even cell reads side0, the first lost cell side1."""
    rows, by_kind = rendered
    got = crossing_evidence(rows, by_kind[diagram.CROSSING][0])
    assert got[("play", 0.75, 32)]["label"] == "(32, side0)" and got[("play", 0.75, 40)]["label"] == "(40, side1)"
    assert got[("baseline", 0.5, 16)]["label"] == "(16, side0)" and got[("baseline", 0.5, 24)]["label"] == "(24, side1)"


def test_crossing_arrows_for_a_ceiling_scan_and_a_scan_lost_everywhere_show_the_rows_the_scan_has():
    """A play that won everywhere at 0.75 has only its top cell (48); a play lost in every cell at 0.5 has only its first cell (8)."""
    rows = sweep_rows({0.5: None, 0.75: 48}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    n = one(rows, diagram.CROSSING)
    got = crossing_evidence(rows, n)
    assert {k for k in got if k[0] == "play"} == {("play", 0.5, 8), ("play", 0.75, 48)}
    assert {k for k in got if k[0] == "baseline"} == {("baseline", 0.5, 16), ("baseline", 0.5, 24), ("baseline", 0.75, 16), ("baseline", 0.75, 24)}
    assert got[("play", 0.5, 8)]["label"] == "(8, side1)" and got[("play", 0.75, 48)]["label"] == "(48, side0)"


def test_crossing_arrows_of_one_series_never_point_at_a_row_of_another():
    rows = cone_series("half=22.5", {150: 8, 300: 32, 600: 40}) + cone_series("half=45", {150: 8, 300: 32, 600: 40})
    for n in kinds(rows, diagram.CROSSING):
        for f in crossing_evidence(rows, n).values():
            assert rows[f["row"]]["point"] == n.point


def test_crossing_arrows_of_a_multi_flip_scan_bracket_the_first_step():
    """Multi-flip: the play at 0.5 wins 8, loses 16, wins 24 and 32: the evidence is the first step, (8, 16), not the later flip."""
    rows = (scan_rows("range_up", "s3_layer_above", "81", 0.5, "none", None, won={8, 24, 32}) +
            scan_rows("range_up", "s3_layer_above", "81", 0.5, "naive_attacker", 16) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "none", 32) +
            scan_rows("range_up", "s3_layer_above", "81", 0.75, "naive_attacker", 16))
    got = crossing_evidence(rows, one(rows, diagram.CROSSING))
    assert {k[2] for k in got if k[:2] == ("play", 0.5)} == {8, 16}


def test_ceiling_hit_arrows_mark_the_flag_and_the_top_headcount(rendered):
    """Assertion type 'ceiling hit': a ceiling_hit arrow on the play's side and an enemy_heads arrow carrying the top headcount on side 1."""
    rows, by_kind = rendered
    n, svg = by_kind[diagram.CEILING_HIT]
    facts = {f["column"]: f for f in arrow_facts(parse(svg))}
    assert set(facts) == {"ceiling_hit", "enemy_heads"}
    assert facts["ceiling_hit"]["value"] == "1" and facts["ceiling_hit"]["side"] == "0"
    assert facts["enemy_heads"]["value"] == str(max(HEADS)) and facts["enemy_heads"]["side"] == "1"
    for f in facts.values():
        r = rows[f["row"]]
        assert (r["family"], r["play"], r["layout"], r["point"], r["baseline"], r["knob_value"]) == \
            (n.family, n.play, n.layout, n.point, "none", n.knob_lo)
        assert r["ceiling_hit"] == 1


def test_ceiling_hit_arrows_of_one_series_read_only_that_series_rows():
    rows = cone_series("half=22.5", {300: 48}) + cone_series("half=45", {300: 48})
    for n in kinds(rows, diagram.CEILING_HIT):
        for f in arrow_facts(parse(diagram.render(n, rows, fake_setup()))):
            assert rows[f["row"]]["point"] == n.point


def test_both_wrong_arrows_point_the_prediction_one_way_and_the_outcome_the_other(rendered):
    """Assertion type 'both_wrong': the count and type predictions point at side 0, the outcome at side 1 (the survivor)."""
    rows, by_kind = rendered
    n, svg = by_kind[diagram.BOTH_WRONG]
    facts = {f["column"]: f for f in arrow_facts(parse(svg))}
    assert set(facts) == {"firing_window_0", "firing_window_1", "weighted_window_0", "weighted_window_1", "predicted_count",
                          "predicted_type", "outcome"}
    assert all(f["row"] == n.row for f in facts.values())
    assert [facts[c]["side"] for c in ("firing_window_0", "weighted_window_0", "predicted_count", "predicted_type")] == ["0"] * 4
    assert [facts[c]["side"] for c in ("firing_window_1", "weighted_window_1", "outcome")] == ["1"] * 3
    assert facts["predicted_count"]["value"] == "side0" and facts["outcome"]["value"] == "side1"
    assert facts["firing_window_0"]["value"] == "30.0"
    assert {facts[c]["kind"] for c in ("firing_window_0", "firing_window_1", "weighted_window_0", "weighted_window_1")} == {"window"}
    assert {facts["predicted_count"]["kind"], facts["predicted_type"]["kind"]} == {"prediction"} and facts["outcome"]["kind"] == "outcome"


def test_both_wrong_arrows_follow_the_row_when_the_prediction_is_side1_and_the_outcome_side0():
    """Positive control of the mirror case: predicted side1, survivor side0 -> prediction arrows target side 1, the outcome arrow side 0."""
    rows = [both_wrong_row(outcome="side0", predicted_count="side1", predicted_type="side1")]
    facts = {f["column"]: f for f in arrow_facts(parse(diagram.render(one(rows, diagram.BOTH_WRONG), rows, fake_setup())))}
    assert facts["predicted_count"]["side"] == facts["predicted_type"]["side"] == "1" and facts["outcome"]["side"] == "0"


def test_arrow_targets_are_the_side_centroids_or_the_point(rendered):
    """The arrow head is at what it marks: the mean of the side's placed positions, or Setup.point."""
    rows, by_kind = rendered
    setup = fake_setup()
    for kind in ALL_KINDS:
        for f in arrow_facts(parse(by_kind[kind][1])):
            tx, ty = positions_of(setup, int(f["side"])) if f["side"] in ("0", "1") else setup.point
            assert (f["tx"], f["ty"]) == pytest.approx((tx, ty), abs=1e-3), f


def test_each_assertion_type_draws_only_its_own_arrows_negative_control(rendered):
    _, by_kind = rendered
    cols = {k: {f["column"] for f in arrow_facts(parse(svg))} for k, (_, svg) in by_kind.items()}
    assert cols[diagram.CROSSING] == {"enemy_heads"} and cols[diagram.CEILING_HIT] == {"ceiling_hit", "enemy_heads"}
    assert not cols[diagram.CROSSING] & cols[diagram.BOTH_WRONG] and not cols[diagram.CEILING_HIT] & cols[diagram.BOTH_WRONG]
    kinds_ = {k: {f["kind"] for f in arrow_facts(parse(svg))} for k, (_, svg) in by_kind.items()}
    assert not kinds_[diagram.CROSSING] & kinds_[diagram.CEILING_HIT] and not kinds_[diagram.CROSSING] & kinds_[diagram.BOTH_WRONG]


# ---------------------------------------------------------------- DRAFT numbers touched are marked

def drafts(root):
    legend = els(root, "g", "legend")[0]
    return {t.get("data-draft"): text_of(t) for t in legend.iter() if tag(t) == "text" and "draft" in (t.get("class") or "").split()}


def test_window_arrows_are_marked_draft_and_the_legend_gives_the_window_length(rendered):
    _, by_kind = rendered
    root = parse(by_kind[diagram.BOTH_WRONG][1])
    marked = {f["column"] for f in arrow_facts(root) if f["draft"]}
    assert marked == {"firing_window_0", "firing_window_1", "weighted_window_0", "weighted_window_1"}
    assert {f["draft"] for f in arrow_facts(root) if f["draft"]} == {OPENING_DRAFT}
    d = drafts(root)
    assert set(d) == {OPENING_DRAFT} and str(contract.OPENING_WINDOW_TICKS) in d[OPENING_DRAFT] and OPENING_DRAFT in d[OPENING_DRAFT]


def test_a_diagram_without_a_window_arrow_marks_no_opening_window_draft(rendered):
    """Negative control: a vision crossing and a ceiling hit touch no DRAFT number."""
    _, by_kind = rendered
    for kind in (diagram.CROSSING, diagram.CEILING_HIT):
        assert drafts(parse(by_kind[kind][1])) == {}


def test_arc_family_diagram_marks_the_firing_arc_draft():
    rows = sweep_rows({7.5: 8, 15: 32, 30: 40, 60: 40, 120: 40}, {"naive_attacker": {7.5: 16, 15: 16, 30: 16, 60: 16, 120: 16}},
                      family="arc", play="s2_concave")
    n = one(rows, diagram.CROSSING)
    assert set(drafts(parse(diagram.render(n, rows, fake_setup())))) == {"DRAFT-firing-arc-deg"}


def test_cone_family_diagram_marks_the_three_cone_drafts():
    rows = cone_series("half=45", {150: 8, 300: 32, 600: 40})
    n = one(rows, diagram.CROSSING)
    assert set(drafts(parse(diagram.render(n, rows, fake_setup())))) == {"DRAFT-aoe-cone-range", "DRAFT-aoe-cone-deg", "DRAFT-aoe-cone-share"}


def test_a_both_wrong_diagram_of_the_arc_family_marks_the_window_and_the_arc():
    """The legend marks the union of what the diagram touches (window arrows and the family)."""
    row = both_wrong_row()
    row["family"] = "arc"
    assert set(drafts(parse(diagram.render(one([row], diagram.BOTH_WRONG), [row], fake_setup())))) == {OPENING_DRAFT, "DRAFT-firing-arc-deg"}


# ---------------------------------------------------------------- SLOW: real placed scenes and real fights

@pytest.fixture(scope="module")
def library():
    from scripts.skilllab import engine
    return engine.Engine()


def real_setups():
    """The real placed Setup of s3_layer_above on the first smoke layout whose pre-flight is ok (no engine needed to build it)."""
    from scripts.skilllab import sweep
    for layout, features in sweep.smoke_layouts().items():
        build = sweep.default_builds("s3_layer_above", "play", features)
        setup = build(16, False)
        if build.labels.get("prefight") == "ok":
            return layout, setup
    pytest.skip("no smoke layout is pre-flight ok for s3_layer_above")


@SLOW
def test_real_fight_rows_and_a_real_placed_scene_make_a_consistent_both_wrong_diagram(library, tmp_path):
    """SLOW 1: a real fight on a real placed scene -> its row (agreement rewritten to both_wrong: a labelled synthetic positive
    control, the engine does not promise one) -> the diagram has every real unit, wall and cover and every arrow equals the CSV."""
    from scripts.skilllab import fight
    layout, setup = real_setups()
    result = fight.fight(setup, 0, False, engine=library)
    row = rows_mod.fight_row(result, knob="OM_TP_VISION_UP_1", knob_value=0.5, baseline="none", ceiling_hit=0, prefight="ok",
                             family="vision", play="s3_layer_above", layout=layout, kind="grid", enemy_heads=16)
    row["agreement"] = "both_wrong"
    row["point"] = "-"
    rows = [row]
    n = one(rows, diagram.BOTH_WRONG)
    svg = diagram.render(n, rows, setup)
    assert svg == diagram.render(n, rows, setup)
    root = parse(svg)
    assert len(els(root, "circle", "unit")) == sum(g.count for g in setup.groups)
    assert len(els(root, "rect", "wall")) == len(setup.terrain.blocks) and len(els(root, "circle", "cover")) == len(setup.terrain.covers)
    csv_cells = cells_of(rows, tmp_path)
    for f in arrow_facts(root):
        assert f["value"] == csv_cells[f["row"]][f["column"]]
    assert [Path(p).name for p in diagram.write_all(rows, lambda _n: setup, tmp_path / "o")] == [n.id + ".svg"]


@SLOW
def test_real_agreement_values_are_all_known_and_a_real_both_wrong_would_be_listed(library):
    """SLOW 2: over real fights of a cross-layer scene the engine's `agreement` is one of the five words; any real both_wrong row is a
    notable with a diagram (the detector on real output; zero both_wrong rows is a valid result)."""
    from scripts.skilllab import fight
    rows = []
    for seed in range(3):
        for swap in (False, True):
            g0 = Group(side=0, unit="VR", count=16, formation="blob", x=1000.0, y=1000.0, facing_deg=0.0, layer=1, order="attack_move",
                       params={"radius": 90.0})
            g1 = Group(side=1, unit="VR", count=16, formation="blob", x=1500.0, y=1000.0, facing_deg=180.0, layer=0,
                       order="attack_move", params={"radius": 90.0})
            s = Setup(groups=(g0, g1), unit_types={"VR": {"base": "Vanguard", "reach": (1, 1)}}, max_ticks=4000, point=(1250.0, 1000.0),
                      settings={"OM_TP_VISION_UP_1": 0.5, "OM_TP_VISION_DOWN_1": 0.5})
            r = fight.fight(s, seed, swap, engine=library)
            rows.append(rows_mod.fight_row(r, knob="OM_TP_VISION_UP_1", knob_value=0.5, baseline="none", ceiling_hit=0, prefight="ok",
                                           family="vision", play="s3_layer_above", layout="x", kind="grid", enemy_heads=16))
            rows[-1]["point"] = "-"
    assert {r["agreement"] for r in rows} <= {"both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a"}
    wrong = [i for i, r in enumerate(rows) if r["agreement"] == "both_wrong"]
    assert [n.row for n in diagram.notables(rows) if n.kind == diagram.BOTH_WRONG] == wrong
    assert len(diagram.render_all(rows, lambda _n: s)) == len(diagram.notables(rows))
