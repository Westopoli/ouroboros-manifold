# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 (new diagram.py; ruling 12 output rule; ruling 4 ceiling hit; ruling 5 both_wrong is a finding); decisions 24 (second crossing), 25 (baseline roles)
"""LAB-REV2-L5 tests for scripts/skilllab/diagram.py: the SVG per notable layout, arrows marking the evidence for each assertion.

The L5 spec row is thin; THE INTERFACE BELOW IS FIXED BY THIS FILE (the builder reads it as the spec). Anything marked QUESTION is a
reading the test writer made and the Architect should confirm; the unmarked lines follow from the spec, the rulings or L4's output.

Input = the rows of one family or smoke CSV (what `rows.fight_row` returns / `rows.write_rows` writes; the columns are L4's: `family`,
`play`, `layout`, `kind` in {grid, refined, sign_flip, control_positive, control_null, control_smoke}, `enemy_heads`, `knob`,
`knob_value`, `baseline` in {none, naive_attacker, naive_defender, naive_defender_attacker_layer, naive_defender_play_layer},
`ceiling_hit`, `outcome`, `agreement`, `predicted_count`, `predicted_type`, `firing_window_0/1`, `weighted_window_0/1`, ...) plus, for
the layout, a `Setup` (groups with formation/anchor/layer, `terrain` blocks and covers, `point`).

    read_rows(path) -> list[dict]
        The CSV that rows.write_rows wrote, typed: INT columns enemy_heads, ceiling_hit, ticks, first_contact_tick, survivors_0,
        survivors_1, heads_0, heads_1; FLOAT columns margin, strength_left_0/1, firing_unit_seconds_0/1, firing_window_0/1,
        weighted_unit_seconds_0/1, weighted_window_0/1, knob_value; every other column stays a str (layout "81" stays "81"); an empty
        cell reads None. Reading what fight_row produced and written by write_rows round-trips every non-None cell.

    Notable(kind, family, play, layout, role, knob_lo, knob_hi, row)      frozen dataclass; `id` property (str, matches
        ^[A-Za-z0-9_-]+$, unique per notable, a function of the fields only)
        kind in {"crossing", "ceiling_hit", "both_wrong"} (constants diagram.CROSSING, CEILING_HIT, BOTH_WRONG)
        crossing:    role = the baseline role crossed, knob_lo < knob_hi the two ADJACENT knob values (grid and refined points,
                     sorted ascending) whose sign of the gain differs; row None
        ceiling_hit: role "none", knob_lo == knob_hi == the knob value, row None
        both_wrong:  family/play/layout/knob_lo/knob_hi/role taken from the row (knob_* = knob_value, role = baseline), row = its index

    notables(rows) -> list[Notable]
        order: crossing, then ceiling_hit, then both_wrong; inside a kind sorted by (family, play, layout, role, knob_lo) and, for
        both_wrong, by row index. Deterministic.
        CROSSING (the sign of the gain, as sweep.py reads it): for each (family, play, layout) and each baseline role present among
        its rows (any baseline other than "none"; decisions 24: a defending play whose rows carry a naive_defender* role gets its own
        crossing against it, a meeting has none), over rows of kind grid or refined only: per knob value, a play scan is the rows with
        baseline "none" and a baseline scan the rows with that role; a cell (one enemy_heads) is won when every row of it has outcome
        side0; break-even = the top enemy_heads when every cell is won (a ceiling hit), else the enemy_heads before the first
        won-to-lost step (scan._crossing), else 0; gain = break-even(play) - break-even(role); the sign is gain > 0 (zero is not
        ahead). One Notable per adjacent pair of knob values whose signs differ. Control kinds (control_*) and sign_flip rows are
        never read.
        CEILING_HIT: rows with baseline "none", kind grid or refined and ceiling_hit == 1 (the column L4 wrote), one Notable per
        (family, play, layout, knob_value). A ceiling_hit == 1 row of a baseline role is not a notable (QUESTION 1).
        BOTH_WRONG: every row (any kind, any baseline) whose agreement == "both_wrong": one Notable per row (ruling 5, a mismatch is
        a finding; the report lists them).

    render(notable, rows, setup) -> str            one self-contained SVG document (a string), byte-identical for the same arguments
        root <svg> (xmlns svg, viewBox "0 0 W H" with W, H numbers): attributes id = notable.id, data-kind, data-family, data-play,
        data-layout, data-role; a <title> child holding family, play and layout.
        layout (top-down, world coordinates written in data attributes, svg positions free but inside the viewBox and with cx
        non-decreasing in data-x):
          <circle class="unit side{0|1} layer-{n}" data-side data-layer data-unit data-x data-y cx cy r>  one per placed unit, the
              positions formations.place(group.formation, group.count, group.x, group.y, group.facing_deg, group.params) gives
          <rect class="wall" data-x0 data-y0 data-x1 data-y1 data-layer-lo data-layer-hi x y width height>  one per Terrain.blocks
          <circle class="cover" data-x data-y data-radius data-height cx cy r>  one per Terrain.covers
          <g class="point" data-x data-y>  once when Setup.point is not None, absent otherwise
        legend: one <g class="legend"> with <text> entries naming side 0, side 1, wall, point, arrow and layer (case-insensitive
              substrings); a <text class="draft" data-draft="NAME"> inside it for every DRAFT number the diagram touches (below)
        arrows: <g class="arrow arrow-{kind}" data-kind data-column data-value data-row data-target-side data-target-x data-target-y>
              holding one <line x1 y1 x2 y2> (endpoints inside the viewBox) and one <text> reading "{column} {value}" (then
              " DRAFT" when data-draft is set). data-row indexes `rows`; data-value is the CSV text of rows[data-row][data-column]
              (floats as repr, ints as str, None as ""); data-target-side is "0", "1" or "point"; data-target-x/y are the world
              coordinates of what the arrow points at: the mean of the placed positions of that side, or Setup.point.
          crossing:    two arrows, data-column "knob_value", values the CSV text of knob_lo and knob_hi, each on a row of the same
                       family/play/layout with baseline "none" and kind grid or refined at that knob value, target side "0"
          ceiling_hit: an arrow "ceiling_hit" (value "1", on a qualifying row, side "0") and an arrow "enemy_heads" (the largest
                       enemy_heads among the qualifying rows of that knob value, side "1")
          both_wrong:  seven arrows on rows[notable.row]: firing_window_0 (side 0), firing_window_1 (side 1), weighted_window_0
                       (side 0), weighted_window_1 (side 1), predicted_count (the predicted side), predicted_type (the predicted
                       side), outcome (the surviving side); the four window arrows carry data-draft="DRAFT-opening-window-ticks"
                       (ruling 5, DRAFT-opening-window-ticks)
        DRAFT numbers touched (legend <text class="draft" data-draft=NAME>, the name from the spec, the value from the library
        constant where one exists, none pinned here): any window arrow -> DRAFT-opening-window-ticks (value text
        contract.OPENING_WINDOW_TICKS); family "arc" -> DRAFT-firing-arc-deg; family "cone" -> DRAFT-aoe-cone-range,
        DRAFT-aoe-cone-deg, DRAFT-aoe-cone-share. Otherwise none.

    render_all(rows, setup_for) -> dict[str, str]   notable.id -> svg, in notables(rows) order; setup_for(notable) -> Setup
    write_all(rows, setup_for, out_dir) -> list[pathlib.Path]   writes <out_dir>/<notable.id>.svg (utf-8, the render_all text) and
        returns the paths in order; writes nothing (no file, the list is empty) when there is no notable.

QUESTIONS for the Architect (none blocks the tests; each is a reading, none is a number):
 1. ceiling_hit notable: only the play's own rows (baseline "none"), not a baseline scan that also beats the top.
 2. A crossing is read from rows (CSV), not from sweep_summary.json (its `refined_vs` is per family, not per play and layout).
 3. "choke" in the spec row has no Setup field; the diagram draws the Terrain blocks (walls) and covers, the choke is the gap between walls.
 4. both_wrong includes control and baseline rows (every row that says both_wrong).
"""
import csv
import os
import re
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
        "arc": "OM_TP_FIRING_ARC_DEG", "cone": "cone"}


def scan_rows(family, play, layout, knob, baseline, beats, kind="grid", per_cell=2, **over):
    """The rows one scan writes: per enemy headcount `per_cell` fights; side0 wins up to `beats` (None: lost everywhere); beats == 48
    is a ceiling hit and then ceiling_hit is 1 on every row, as L4 writes it."""
    ceiling = int(beats == HEADS[-1])
    out = []
    for h in HEADS:
        for _ in range(per_cell):
            won = beats is not None and h <= beats
            out.append(rows_mod.fight_row(fr("side0" if won else "side1"), knob=KNOB[family], knob_value=float(knob),
                                          baseline=baseline, ceiling_hit=ceiling, prefight="ok", family=family, play=play,
                                          layout=layout, kind=kind, enemy_heads=h, **over))
    return out


def sweep_rows(play_be, role_be, family="range_up", play="s3_layer_above", layout="81", refined=()):
    """play_be: {knob value: beats of the play}; role_be: {role: {knob value: beats of that baseline}}. Values in `refined` have kind refined."""
    out = []
    for v, b in sorted(play_be.items()):
        out += scan_rows(family, play, layout, v, "none", b, kind="refined" if v in refined else "grid")
    for role, per_knob in role_be.items():
        for v, b in sorted(per_knob.items()):
            out += scan_rows(family, play, layout, v, role, b, kind="refined" if v in refined else "grid")
    return out


# gain vs a flat baseline of 16: + at 1.0 and 0.75, - at 0.5 and 0.25 -> exactly one crossing, between 0.5 and 0.75
PLAY_BE = {0.25: 8, 0.5: 8, 0.75: 32, 1.0: 40}
FLAT16 = {0.25: 16, 0.5: 16, 0.75: 16, 1.0: 16}


def crossing_rows(**kw):
    return sweep_rows(PLAY_BE, {"naive_attacker": FLAT16}, **kw)


def both_wrong_row(**over):
    base = dict(outcome="side1", agreement="both_wrong", predicted_count="side0", predicted_type="side0",
                firing_window=(30.0, 10.0), weighted_window=(35.0, 12.0))
    base.update(over)
    return rows_mod.fight_row(fr(**base), knob="OM_TP_VISION_UP_1", knob_value=0.5, baseline="none", ceiling_hit=0, prefight="ok",
                              family="vision", play="s3_layer_above", layout="78", kind="grid", enemy_heads=16)


def fake_setup(point=(740.0, 300.0)):
    groups = (Group(0, "Vanguard", 8, "blob", 250.0, 300.0, 0.0, 1, "attack_move", params={"radius": 80.0}),
              Group(0, "Raider", 8, "line", 150.0, 300.0, 0.0, 0, "attack_move", params={"spacing": 40.0}),
              Group(1, "Vanguard", 16, "blob", 750.0, 300.0, 180.0, 0, "guard", params={"radius": 100.0}))
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


# ---------------------------------------------------------------- the crossing detector (positive and negative controls)

def test_crossing_positive_control_one_sign_change_is_one_crossing_between_adjacent_knob_values():
    """Ruling 12 (where the lines cross): the gain turns from - at 0.5 to + at 0.75 -> exactly one crossing, role naive_attacker."""
    n = one(crossing_rows(), diagram.CROSSING)
    assert (n.family, n.play, n.layout, n.role) == ("range_up", "s3_layer_above", "81", "naive_attacker")
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75) and n.row is None


def test_crossing_negative_control_a_play_ahead_everywhere_has_no_crossing():
    """Control: gain > 0 at every knob value -> no crossing notable."""
    always = sweep_rows({0.25: 32, 0.5: 32, 0.75: 40, 1.0: 40}, {"naive_attacker": FLAT16})
    assert [n for n in diagram.notables(always) if n.kind == diagram.CROSSING] == []


def test_crossing_negative_control_a_play_behind_everywhere_has_no_crossing():
    behind = sweep_rows({0.25: 8, 0.5: 8, 0.75: 8, 1.0: 8}, {"naive_attacker": FLAT16})
    assert [n for n in diagram.notables(behind) if n.kind == diagram.CROSSING] == []


def test_zero_gain_is_not_ahead():
    """gain > 0 is the sign (sweep.py): equal break-evens are not ahead, so equal at 0.5 and ahead at 0.75 is a crossing."""
    eq = sweep_rows({0.5: 16, 0.75: 32}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    n = one(eq, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.75)


def test_a_sign_change_in_a_sign_flip_or_control_row_is_not_a_crossing():
    """Controls and the labelled sign-flip point are never read for a crossing (ruling 10, decision 21)."""
    rows = sweep_rows({0.5: 32, 1.0: 40}, {"naive_attacker": {0.5: 16, 1.0: 16}})
    rows += scan_rows("range_up", "s3_layer_above", "81", 2.0, "none", 8, kind="sign_flip")
    rows += scan_rows("range_up", "s3_layer_above", "81", 2.0, "naive_attacker", 16, kind="sign_flip")
    rows += scan_rows("range_up", "s3_layer_above", "81", 0.0, "none", 8, kind="control_positive")
    rows += scan_rows("range_up", "s3_layer_above", "81", 0.0, "naive_attacker", 16, kind="control_null")
    assert [n for n in diagram.notables(rows) if n.kind == diagram.CROSSING] == []


def test_a_refined_point_brackets_the_crossing_more_tightly():
    """A refined value 0.625 between the coarse 0.5 (-) and 0.75 (+) turns the crossing into the adjacent pair (0.5, 0.625) or (0.625, 0.75)."""
    rows = sweep_rows({0.25: 8, 0.5: 8, 0.625: 32, 0.75: 32, 1.0: 40}, {"naive_attacker": {0.25: 16, 0.5: 16, 0.625: 16, 0.75: 16, 1.0: 16}},
                      refined=(0.625,))
    n = one(rows, diagram.CROSSING)
    assert (n.knob_lo, n.knob_hi) == (0.5, 0.625)


def test_defending_play_gets_a_second_crossing_against_the_naive_defender():
    """Decisions 24: each baseline role the rows carry gets its own crossing; two roles that both flip -> two notables, one per role."""
    both = sweep_rows(PLAY_BE, {"naive_attacker": FLAT16, "naive_defender": {0.25: 16, 0.5: 16, 0.75: 36, 1.0: 36}})
    found = [n for n in diagram.notables(both) if n.kind == diagram.CROSSING]
    assert sorted(n.role for n in found) == ["naive_attacker", "naive_defender"]
    by_role = {n.role: (n.knob_lo, n.knob_hi) for n in found}
    assert by_role["naive_attacker"] == (0.5, 0.75) and by_role["naive_defender"] == (0.75, 1.0)
    assert len({n.id for n in found}) == 2


def test_a_meeting_with_only_the_attacker_baseline_has_one_crossing_and_none_for_a_defender():
    """Control for the above: no naive_defender* rows -> no crossing with such a role."""
    found = [n for n in diagram.notables(crossing_rows()) if n.kind == diagram.CROSSING]
    assert [n.role for n in found] == ["naive_attacker"]


def test_the_layer_play_defender_variants_are_roles_of_their_own():
    """Decision 25: naive_defender_attacker_layer and naive_defender_play_layer are separate baseline roles, each read by itself."""
    rows = sweep_rows(PLAY_BE, {"naive_defender_attacker_layer": FLAT16, "naive_defender_play_layer": {0.25: 4, 0.5: 4, 0.75: 4, 1.0: 4}})
    found = {n.role: (n.knob_lo, n.knob_hi) for n in diagram.notables(rows) if n.kind == diagram.CROSSING}
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


# ---------------------------------------------------------------- the ceiling-hit detector

def ceiling_rows(ceiling_beats=48, **kw):
    return sweep_rows({0.5: ceiling_beats, 1.0: 24}, {"naive_attacker": {0.5: 16, 1.0: 16}}, **kw)


def test_ceiling_hit_positive_control_one_notable_per_family_play_layout_knob():
    """Ruling 4: a play that beats the top headcount at one knob value is a ceiling hit notable, never 'no gain'."""
    n = one(ceiling_rows(), diagram.CEILING_HIT)
    assert (n.family, n.play, n.layout, n.role, n.knob_lo, n.knob_hi, n.row) == ("range_up", "s3_layer_above", "81", "none", 0.5, 0.5, None)


def test_ceiling_hit_negative_control_no_ceiling_rows_no_notable():
    assert [n for n in diagram.notables(ceiling_rows(ceiling_beats=40)) if n.kind == diagram.CEILING_HIT] == []


def test_a_baseline_scan_that_hits_the_ceiling_is_not_a_ceiling_hit_notable():
    """The play's own rows (baseline none) carry the notable; a naive baseline at the ceiling does not (QUESTION 1)."""
    rows = sweep_rows({0.5: 24}, {"naive_attacker": {0.5: 48}})
    assert [n for n in diagram.notables(rows) if n.kind == diagram.CEILING_HIT] == []


def test_a_ceiling_hit_in_a_control_kind_is_not_a_notable():
    rows = scan_rows("range_up", "s3_layer_above", "81", 0.0, "none", 48, kind="control_positive")
    assert [n for n in diagram.notables(rows) if n.kind == diagram.CEILING_HIT] == []


# ---------------------------------------------------------------- the both_wrong detector

def test_both_wrong_positive_control_every_both_wrong_row_is_a_finding():
    rows = crossing_rows() + [both_wrong_row(), both_wrong_row(ticks=301)]
    found = [n for n in diagram.notables(rows) if n.kind == diagram.BOTH_WRONG]
    assert [n.row for n in found] == [len(rows) - 2, len(rows) - 1]
    assert {(n.family, n.play, n.layout, n.role) for n in found} == {("vision", "s3_layer_above", "78", "none")}
    assert len({n.id for n in found}) == 2


@pytest.mark.parametrize("agreement", ["both_right", "count_wrong_type_right", "count_right_type_wrong", "n/a"])
def test_both_wrong_negative_control_the_other_four_agreements_are_not_notable(agreement):
    row = both_wrong_row(agreement=agreement)
    assert [n for n in diagram.notables([row]) if n.kind == diagram.BOTH_WRONG] == []


# ---------------------------------------------------------------- order, ids, determinism, the no-notable control

def test_notables_are_ordered_crossing_then_ceiling_then_both_wrong_and_deterministic():
    rows = crossing_rows() + ceiling_rows(play="s3_types_by_reach") + [both_wrong_row()]
    a, b = diagram.notables(rows), diagram.notables(list(rows))
    assert a == b
    assert [n.kind for n in a] == [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG]


def test_ids_are_filesystem_safe_unique_and_a_function_of_the_fields():
    rows = crossing_rows() + crossing_rows(layout="78") + ceiling_rows(play="s3_types_by_reach") + [both_wrong_row()]
    ns = diagram.notables(rows)
    assert len(ns) >= 4
    ids = [n.id for n in ns]
    assert len(set(ids)) == len(ids) and all(re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)
    assert [n.id for n in diagram.notables(rows)] == ids


def test_no_crossing_no_ceiling_no_both_wrong_means_no_diagram_at_all(tmp_path):
    """The control of the spec row: a fake with no crossing produces no diagram (and writes no file)."""
    rows = sweep_rows({0.25: 32, 0.5: 32, 0.75: 40, 1.0: 40}, {"naive_attacker": FLAT16, "naive_defender": FLAT16})
    assert diagram.notables(rows) == []
    assert diagram.render_all(rows, setup_for) == {}
    assert diagram.write_all(rows, setup_for, tmp_path / "out") == []
    assert not list(tmp_path.rglob("*.svg"))


# ---------------------------------------------------------------- render: shape, layout, legend

def every_kind_rows():
    return crossing_rows() + ceiling_rows(play="s3_types_by_reach") + [both_wrong_row()]


@pytest.fixture(scope="module")
def rendered():
    rows = every_kind_rows()
    return rows, {n.kind: (n, diagram.render(n, rows, fake_setup())) for n in diagram.notables(rows)}


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
def test_render_is_one_well_formed_svg_with_the_notable_in_its_attributes(rendered, kind):
    rows, by_kind = rendered
    n, svg = by_kind[kind]
    root = parse(svg)
    assert viewbox(root)[0] > 0 and viewbox(root)[1] > 0
    assert root.get("id") == n.id and root.get("data-kind") == kind
    assert (root.get("data-family"), root.get("data-play"), root.get("data-layout"), root.get("data-role")) == \
        (n.family, n.play, n.layout, n.role)
    title = [text_of(e) for e in els(root, "title")]
    assert title and all(w in title[0] for w in (n.family, n.play, n.layout))


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
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


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
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
    for u in units:
        classes = u.get("class").split()
        assert "side" + u.get("data-side") in classes and "layer-" + u.get("data-layer") in classes
    assert {u.get("data-layer") for u in units if u.get("data-side") == "0"} == {"0", "1"}      # a layer play shows both layers


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


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
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
    return [dict(column=a.get("data-column"), value=a.get("data-value"), row=int(a.get("data-row")), side=a.get("data-target-side"),
                 tx=float(a.get("data-target-x")), ty=float(a.get("data-target-y")), draft=a.get("data-draft"),
                 label=text_of([e for e in a.iter() if tag(e) == "text"][0]), el=a) for a in arrows(root)]


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
def test_every_arrow_label_equals_a_csv_value(rendered, kind, tmp_path):
    """Spec row: 'every arrow label equals a CSV value': data-value is the CSV text of rows[data-row][data-column]; the label shows it."""
    rows, by_kind = rendered
    csv_cells = cells_of(rows, tmp_path)
    root = parse(by_kind[kind][1])
    facts = arrow_facts(root)
    assert facts
    for f in facts:
        assert f["value"] == csv_cells[f["row"]][f["column"]], f
        assert f["label"].startswith("%s %s" % (f["column"], f["value"])), f
        assert ("DRAFT" in f["label"]) == (f["draft"] is not None)


@pytest.mark.parametrize("kind", [diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG])
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


def test_crossing_arrows_mark_the_two_knob_values_on_the_play_scan(rendered, tmp_path):
    """Assertion type 'crossing': one knob_value arrow per bracketing value, each on a row of that play's own scan, pointing at side 0."""
    rows, by_kind = rendered
    n, svg = by_kind[diagram.CROSSING]
    facts = arrow_facts(parse(svg))
    assert [f["column"] for f in facts] == ["knob_value", "knob_value"]
    assert sorted(f["value"] for f in facts) == sorted([repr(n.knob_lo), repr(n.knob_hi)])
    for f in facts:
        r = rows[f["row"]]
        assert (r["family"], r["play"], r["layout"], r["baseline"]) == (n.family, n.play, n.layout, "none")
        assert r["kind"] in ("grid", "refined") and repr(r["knob_value"]) == f["value"]
        assert f["side"] == "0" and f["draft"] is None


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
        assert (r["family"], r["play"], r["layout"], r["baseline"], r["knob_value"]) == (n.family, n.play, n.layout, "none", n.knob_lo)
        assert r["ceiling_hit"] == 1


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


def test_arrow_targets_are_the_side_centroids_or_the_point(rendered):
    """The arrow head is at what it marks: the mean of the side's placed positions, or Setup.point."""
    rows, by_kind = rendered
    setup = fake_setup()
    for kind in (diagram.CROSSING, diagram.CEILING_HIT, diagram.BOTH_WRONG):
        for f in arrow_facts(parse(by_kind[kind][1])):
            tx, ty = positions_of(setup, int(f["side"])) if f["side"] in ("0", "1") else setup.point
            assert (f["tx"], f["ty"]) == pytest.approx((tx, ty), abs=1e-3), f


def test_crossing_diagram_has_no_ceiling_or_both_wrong_arrows_negative_control(rendered):
    """Each assertion type draws only its own arrows."""
    _, by_kind = rendered
    cols = {k: {f["column"] for f in arrow_facts(parse(svg))} for k, (_, svg) in by_kind.items()}
    assert cols[diagram.CROSSING] == {"knob_value"}
    assert not cols[diagram.CROSSING] & cols[diagram.CEILING_HIT] and not cols[diagram.CROSSING] & cols[diagram.BOTH_WRONG]
    assert not cols[diagram.CEILING_HIT] & cols[diagram.BOTH_WRONG]


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
    rows = sweep_rows({90: 8, 120: 32, 180: 40, 270: 40, 360: 40}, {"naive_attacker": {90: 16, 120: 16, 180: 16, 270: 16, 360: 16}},
                      family="arc", play="s2_concave")
    n = one(rows, diagram.CROSSING)
    assert set(drafts(parse(diagram.render(n, rows, fake_setup())))) == {"DRAFT-firing-arc-deg"}


def test_cone_family_diagram_marks_the_three_cone_drafts():
    rows = sweep_rows({150: 8, 300: 32, 600: 40}, {"naive_attacker": {150: 16, 300: 16, 600: 16}}, family="cone", play="s2_concave")
    n = one(rows, diagram.CROSSING)
    assert set(drafts(parse(diagram.render(n, rows, fake_setup())))) == {"DRAFT-aoe-cone-range", "DRAFT-aoe-cone-deg", "DRAFT-aoe-cone-share"}


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
    assert {r["agreement"] for r in rows} <= {"both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a"}
    wrong = [i for i, r in enumerate(rows) if r["agreement"] == "both_wrong"]
    assert [n.row for n in diagram.notables(rows) if n.kind == diagram.BOTH_WRONG] == wrong
    assert len(diagram.render_all(rows, lambda _n: s)) == len(diagram.notables(rows))
