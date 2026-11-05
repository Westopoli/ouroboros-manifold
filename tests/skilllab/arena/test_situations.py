# spec: docs/stories/H-040.md (Part 5: situations converter); Flag client (tool part, no scene of its own)
"""H-040 part 5: the situations converter, `scripts/skilllab/arena/situations.py`.

H-040 Part 5, word for word: "reads every `SIT-*.md` written from `TEMPLATE.md` (its tables; the format is in the template), writes
`L-NNNN.toml` and `.json` in the H-025 schema with `features` from the template's geometry table, runs `check_layout`, prints
`CONVERTED <sit> <layout>` or `REJECT <sit> <rule or missing field>` and exits 2 on any REJECT. Units are placed in 40 wu blocks
(DRAFT-block-pitch, the H-025 round-two spacing) from the block's anchor, count and facing in the table; the author writes no per-unit
rows. A situation whose `stage` is above the current one is still converted (it waits in the catalogue)."

Story test line: "the template's own example converts to a layout that passes `check_layout` with the stated headcounts and predict; a copy
missing `predict` gives `REJECT ... missing predict`; two files get consecutive ids."

Every number is an Architect draft dated 2026-10-31 that Westley rules: DRAFT-block-pitch (40 wu, the story's number; the same value as
`PITCH` in `scripts/skilllab/catalogue/produce.py:19`). The tests add no number of their own.

TEMPLATE.md carries no separate example section: its own filled-in values (Stage 1, open_field, small_flat, Predict A, Vanguard 16 at
(800, 2000) east against Vanguard 16 at (3200, 2000) west) are the example, and the whole file is copied. The converter is run as a
subprocess, as the story's run line does, so while the module is missing every conversion test fails for the missing-module reason and
the controls still run green."""
import json
import math
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.catalogue.produce import check_layout, presets, rules  # noqa: E402

LD = ROOT / "docs" / "northstar" / "research" / "layer_dynamics"
TEMPLATE = LD / "situations" / "TEMPLATE.md"
PITCH = 40.0  # DRAFT-block-pitch
NEXT_ID = "L-0100"
TOL = 0.05  # layout coordinates are rounded to 2 decimals in the H-025 schema (produce.py _round_unit)


# ---------------------------------------------------------------- helpers

def _run(dir_, out, next_id=NEXT_ID):
    """The story's CLI, as a subprocess from the repo root; the finished process."""
    return subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.situations", "--dir", str(dir_), "--out", str(out), "--next-id", next_id],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=120)


def _said(r):
    return r.stdout + r.stderr


def _sit(tmp_path, name, text):
    d = tmp_path / "situations"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text)
    return d


def _converted(tmp_path, texts):
    """Write each (name, text) to a situations dir, convert, and require exit 0; (result, out dir)."""
    d = None
    for name, text in texts:
        d = _sit(tmp_path, name, text)
    out = tmp_path / "catalogue"
    out.mkdir()
    r = _run(d, out)
    assert r.returncode == 0, "converter exit %d: %s" % (r.returncode, _said(r))
    return r, out


def _load(out, lid):
    with open(out / (lid + ".toml"), "rb") as f:
        return tomllib.load(f)


def _example():
    return TEMPLATE.read_text()


def _swap(text, old, new):
    assert old in text, "premise: template no longer contains %r" % old
    return text.replace(old, new, 1)


def _check(layout):
    return check_layout(layout, presets(), rules())


# ---------------------------------------------------------------- controls (green today)

def test_control_check_layout_passes_an_existing_catalogue_layout():
    """H-040 part 5 control: `check_layout` on a produced H-025 layout passes, so a red below is the missing converter, not the checker."""
    with open(LD / "catalogue" / "L-0037.toml", "rb") as f:
        layout = tomllib.load(f)
    assert _check(layout) == []


def test_control_check_layout_sees_a_broken_layout():
    """H-040 part 5 control (detector): the same layout with side A's headcount off by one is caught as R4."""
    with open(LD / "catalogue" / "L-0037.toml", "rb") as f:
        layout = tomllib.load(f)
    layout["side_a"]["headcount"] += 1
    assert _check(layout) == ["R4"]


def test_control_template_example_premises():
    """Premise dump: the template's headers and example values the conversion tests rely on."""
    t = _example()
    for header in ("| side | role     | count | anchor x | anchor y | facing | range | layer |", "| kind      | x    | y    | size      | notes"):
        assert header in t
    for line in ("Stage: 1", "Kind: open_field", "Field: small_flat", "Predict: A"):
        assert re.search(r"^" + re.escape(line) + r"\b", t, re.M), line
    assert re.search(r"^\| A\s*\| Vanguard \| 16\s*\| 800\s*\| 2000\s*\| east\s*\| 0\s*\| 0\s*\|", t, re.M)
    assert re.search(r"^\| B\s*\| Vanguard \| 16\s*\| 3200\s*\| 2000\s*\| west\s*\| 0\s*\| 0\s*\|", t, re.M)


# ---------------------------------------------------------------- the template's example converts

def test_example_converts_prints_converted_and_exits_0(tmp_path):
    """Part 5: prints `CONVERTED <sit> <layout>` for a situation it converted."""
    r, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    lines = [ln for ln in _said(r).splitlines() if ln.startswith("CONVERTED")]
    assert len(lines) == 1, _said(r)
    assert re.fullmatch(r"CONVERTED SIT-0001\S* L-0100", lines[0]), lines[0]
    assert not any(ln.startswith("REJECT") for ln in _said(r).splitlines())


def test_example_writes_toml_and_json_that_agree(tmp_path):
    """Part 5: writes `L-NNNN.toml` and `.json` in the H-025 schema (the same layout in both files)."""
    _, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    assert (out / "L-0100.toml").is_file() and (out / "L-0100.json").is_file()
    toml_layout = _load(out, "L-0100")
    json_layout = json.loads((out / "L-0100.json").read_text())
    assert toml_layout == json_layout
    for key in ("id", "situation", "landscape", "predict", "predict_why", "side_a", "side_b"):
        assert key in toml_layout, key
    for side in ("side_a", "side_b"):
        assert set(toml_layout[side]) >= {"headcount", "units"}
        for u in toml_layout[side]["units"]:
            assert set(u) >= {"role", "x", "y", "facing", "layer"}


def test_example_passes_check_layout_with_stated_headcounts_and_predict(tmp_path):
    """Part 5: the template's own example converts to a layout that passes check_layout with the stated headcounts and predict."""
    _, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    layout = _load(out, "L-0100")
    assert _check(layout) == []
    assert layout["id"] == "L-0100"
    assert layout["situation"] == "open_field"
    assert layout["landscape"] == "small_flat"
    assert layout["predict"] == "A"
    assert layout["predict_why"] == "Equal roles and equal counts, but A starts closer to the centre and engages first."
    assert layout["side_a"]["headcount"] == 16 and len(layout["side_a"]["units"]) == 16
    assert layout["side_b"]["headcount"] == 16 and len(layout["side_b"]["units"]) == 16
    assert {u["role"] for u in layout["side_a"]["units"] + layout["side_b"]["units"]} == {"Vanguard"}
    assert {u["layer"] for u in layout["side_a"]["units"] + layout["side_b"]["units"]} == {0}


def test_example_features_come_from_the_empty_geometry_table(tmp_path):
    """Part 5: `features` from the template's geometry table; the example's table is empty (open field)."""
    _, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    layout = _load(out, "L-0100")
    assert "features" in layout and list(layout["features"]) == []


def test_facings_are_radians_east_zero_west_pi(tmp_path):
    """Part 5: facing taken from the table (east, west); the H-025 schema stores radians (produce.py _round_unit), east 0, west pi."""
    _, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    layout = _load(out, "L-0100")
    assert all(abs(u["facing"]) < 1e-3 for u in layout["side_a"]["units"])
    assert all(abs(abs(u["facing"]) - math.pi) < 1e-3 for u in layout["side_b"]["units"])


# ---------------------------------------------------------------- 40 wu blocks from the anchor

def _near_multiple(v, pitch=PITCH):
    return abs(v / pitch - round(v / pitch)) * pitch < TOL


def test_units_are_placed_in_40_wu_blocks_from_the_anchor(tmp_path):
    """Part 5: "Units are placed in 40 wu blocks (DRAFT-block-pitch ...) from the block's anchor, count and facing in the table"."""
    _, out = _converted(tmp_path, [("SIT-0001-example.md", _example())])
    layout = _load(out, "L-0100")
    for side, (ax, ay) in (("side_a", (800.0, 2000.0)), ("side_b", (3200.0, 2000.0))):
        pts = [(u["x"], u["y"]) for u in layout[side]["units"]]
        dists = sorted(math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(pts) for b in pts[i + 1:])
        assert abs(dists[0] - PITCH) < TOL, "%s nearest pair %.2f apart, want %s" % (side, dists[0], PITCH)
        # a block on a grid: every offset between two units is a whole number of pitches on both axes (east and west face along x)
        for a in pts:
            for b in pts:
                assert _near_multiple(a[0] - b[0]) and _near_multiple(a[1] - b[1]), "%s %s -> %s off the 40 wu grid" % (side, a, b)
        # from the anchor: the block sits around its anchor, 16 units on a 4 x 4 grid reach at most 4 pitches
        assert all(math.hypot(x - ax, y - ay) <= 4 * PITCH for x, y in pts), "%s strays from anchor (%s, %s)" % (side, ax, ay)
    assert max(u["x"] for u in layout["side_a"]["units"]) < min(u["x"] for u in layout["side_b"]["units"])


def test_a_side_of_two_rows_places_each_block_at_its_own_anchor(tmp_path):
    """Template: "One row per block of one role on one side; several rows per side are fine. `count` is 8 to 256 per side in total.\""""
    t = _example()
    two = _swap(t, "| A    | Vanguard | 16    | 800      | 2000     | east   | 0     | 0     |",
                "| A    | Vanguard | 8     | 800      | 1000     | east   | 0     | 0     |\n| A    | Vanguard | 8     | 800      | 3000     | east   | 0     | 0     |")
    _, out = _converted(tmp_path, [("SIT-0001-example.md", two)])
    layout = _load(out, "L-0100")
    assert _check(layout) == []
    ys = [u["y"] for u in layout["side_a"]["units"]]
    assert layout["side_a"]["headcount"] == 16 and len(ys) == 16
    assert sum(1 for y in ys if y < 2000) == 8 and sum(1 for y in ys if y > 2000) == 8


# ---------------------------------------------------------------- REJECT

def test_missing_predict_is_rejected_naming_the_field(tmp_path):
    """Part 5: prints `REJECT <sit> <rule or missing field>` and exits 2; a copy missing `predict` gives `REJECT ... missing predict`."""
    text = _example()
    no_predict = re.sub(r"^Predict:.*\n", "", text, flags=re.M)
    assert "Predict:" not in no_predict, "premise: the Predict line was not removed"
    d = _sit(tmp_path, "SIT-0001-example.md", no_predict)
    out = tmp_path / "catalogue"
    out.mkdir()
    r = _run(d, out)
    assert r.returncode == 2, "exit %d: %s" % (r.returncode, _said(r))
    assert re.search(r"^REJECT SIT-0001\S* .*missing predict", _said(r), re.M), _said(r)
    assert not any(ln.startswith("CONVERTED") for ln in _said(r).splitlines())


def test_one_reject_among_two_files_still_exits_2(tmp_path):
    """Part 5: "exits 2 on any REJECT"; the good file is still reported CONVERTED."""
    bad = re.sub(r"^Predict:.*\n", "", _example(), flags=re.M)
    d = _sit(tmp_path, "SIT-0001-example.md", _example())
    _sit(tmp_path, "SIT-0002-example.md", bad)
    out = tmp_path / "catalogue"
    out.mkdir()
    r = _run(d, out)
    assert r.returncode == 2, "exit %d: %s" % (r.returncode, _said(r))
    said = _said(r)
    assert re.search(r"^CONVERTED SIT-0001\S* L-0100", said, re.M), said
    assert re.search(r"^REJECT SIT-0002\S* .*missing predict", said, re.M), said


# ---------------------------------------------------------------- consecutive ids, stage

def test_two_files_get_consecutive_ids(tmp_path):
    """Part 5: two files get consecutive ids from `--next-id` (L-0100, L-0101), in file-name order."""
    second = _swap(_swap(_swap(_example(), "Predict: A", "Predict: B"),
                         "| A    | Vanguard | 16    |", "| A    | Vanguard | 8     |"),
                   "| B    | Vanguard | 16    |", "| B    | Vanguard | 64    |")
    r, out = _converted(tmp_path, [("SIT-0001-example.md", _example()), ("SIT-0002-example.md", second)])
    said = _said(r)
    assert re.search(r"^CONVERTED SIT-0001\S* L-0100", said, re.M), said
    assert re.search(r"^CONVERTED SIT-0002\S* L-0101", said, re.M), said
    one, two = _load(out, "L-0100"), _load(out, "L-0101")
    assert (one["id"], two["id"]) == ("L-0100", "L-0101")
    assert (one["predict"], one["side_a"]["headcount"], one["side_b"]["headcount"]) == ("A", 16, 16)
    assert (two["predict"], two["side_a"]["headcount"], two["side_b"]["headcount"]) == ("B", 8, 64)
    assert _check(one) == [] and _check(two) == []
    assert sorted(p.name for p in out.glob("L-*")) == ["L-0100.json", "L-0100.toml", "L-0101.json", "L-0101.toml"]


def test_a_situation_above_the_current_stage_is_still_converted(tmp_path):
    """Part 5: "A situation whose `stage` is above the current one is still converted (it waits in the catalogue)." Current stage is 1."""
    later = _swap(_example(), "Stage: 1", "Stage: 4")
    r, out = _converted(tmp_path, [("SIT-0001-example.md", later)])
    assert re.search(r"^CONVERTED SIT-0001\S* L-0100", _said(r), re.M), _said(r)
    assert _check(_load(out, "L-0100")) == []


# ================================================================ H-053 stage 2 (arena-stage2-roles-ranges-winrates)
# spec: docs/stories/H-053.md "Arc blocks", "Interfaces" 2, 3 and 7; Flag client. Story Tests line: "`test_situations.py` (an arc converts to units on the arc facing the
# centre, spacing at the pitch, `check_layout` clean)".
# Interfaces 2, quoted: "Arc columns in the Sides table, after the existing ones: `shape` (`block`, the default when blank, or `arc`), `centre_x`, `centre_y`, `radius`,
# `start_deg`, `end_deg` ... Angles in degrees in the converter's own convention (`COMPASS`: atan2 with y growing south ...), the arc running from `start_deg` to `end_deg`
# clockwise on screen. ... the chord between neighbours is `PITCH` (40 wu): angular step `2*asin(PITCH/(2*radius))`; the n units sit at `start_deg + k*step` for k in 0..n-1
# ... Each unit faces the arc's centre (`atan2(centre_y - y, centre_x - x)`). An arc that cannot hold its count ... is rejected with exactly: `arc too small: <n> units at
# pitch 40 on <span>° need radius <r>` where `<r>` is `ceil(PITCH / (2*sin(span_rad / (2*(n-1)))))` and `<span>` is the span in whole degrees."
# Interfaces 3: "records the arc under the side as `side_a.arc = {centre: [x, y], radius, start_deg, end_deg}` (absent for blocks). `check_layout` gains R6, "arc placement":
# when a side carries `arc`, every unit of that side lies within 1 wu of `radius` from `centre`, else ... `R6 arc placement: unit <id> is <d> wu from the centre, radius <r>`."
# Interfaces 7: "`Expected win rate: <0 to 1, side A>` (required for `Stage: 2` and above, Reject `missing expected win rate` ...), `Orders: both_same_point | hold:A | hold:B`
# ..., `Orders point: midpoint | <x> <y>` ... Layout keys: `predict_rate` (float), `orders` (the H-052 string), `orders_point` (`[x, y]`, absent for midpoint)."
# Architect ruling (2026-11-01): R6 is the existing wall standoff rule (rules.toml), so arc placement takes the next free id, R7, not the story's R6. The tests use an
# open_field layout and read the rule id "R7" plus the message text "arc placement: unit <id> is <d> wu from the centre, radius <r>".

ARC_COLUMNS = ("shape", "centre_x", "centre_y", "radius", "start_deg", "end_deg")
ARC = {"n": 10, "cx": 1500.0, "cy": 2000.0, "r": 400.0, "start": 154.0, "end": 206.0}   # chord 40 at r 400 is a 5.7296 degree step; 9 steps = 51.6 degrees of the 52 given


def _sit2(stage="2", expected="0.75", orders="both_same_point", orders_point="midpoint", arc=ARC, a_role="Bombard", a_rows=None):
    """A stage 2 situation text: side A an arc of `arc["n"]` `a_role`, side B a block of 8 Raiders at (3200, 2000) facing west. `expected` None leaves the line out; `arc` None makes side A a plain block of 16 Vanguards at (800, 2000); `a_rows` (a list of raw table rows) replaces side A's row."""
    head = ["# SIT-0200 open_field (test)", "", "Stage: %s" % stage, "Kind: open_field", "Field: small_flat", "Predict: A"]
    if expected is not None:
        head.append("Expected win rate: %s" % expected)
    head += ["Orders: %s" % orders, "Orders point: %s" % orders_point, "Why: An arc of long guns holds against a rush."]
    cols = "| side | role | count | anchor x | anchor y | facing | range | layer | " + " | ".join(ARC_COLUMNS) + " |"
    sep = "|" + "---|" * (8 + len(ARC_COLUMNS))
    row_a = ("| A | Vanguard | 16 | 800 | 2000 | east | 0 | 0 | block |  |  |  |  |  |" if arc is None else "| A | %s | %d | 0 | 0 | east | 0 | 0 | arc | %s | %s | %s | %s | %s |" % (a_role, arc["n"], arc["cx"], arc["cy"], arc["r"], arc["start"], arc["end"]))
    row_b = "| B | Raider | 8 | 3200 | 2000 | west | 0 | 0 | block |  |  |  |  |  |"
    if a_rows is not None:
        row_a = "\n".join(a_rows)
    feats = ["", "## Features", "", "| kind | x | y | size | notes |", "|---|---|---|---|---|", "|  |  |  |  | (none) |", "", "## Defender", "", "none"]
    return "\n".join(head + ["", "## Sides", "", cols, sep, row_a, row_b] + feats) + "\n"


def _arc_expected(n, cx, cy, r, start):
    step = 2 * math.asin(PITCH / (2 * r))
    out = []
    for k in range(n):
        a = math.radians(start) + k * step
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def test_control_stage1_file_without_expected_rate_converts_and_extra_head_lines_are_ignored(tmp_path):
    """H-053 Interfaces 7 control, green today: a Stage 1 file with no `Expected win rate` line converts (the line is required for Stage 2 and above only), so the Reject test
    below is red for the missing rule and not for a converter that rejects every file lacking the line."""
    text = re.sub(r"^Expected win rate:.*\n", "", _example(), flags=re.M)
    assert "Expected win rate" not in text
    _converted(tmp_path, [("SIT-0001-example.md", text)])


def test_control_arc_geometry_helper_matches_the_story_spacing():
    """H-053 control, green today: the test's own arc formula puts neighbours exactly PITCH apart and every unit at radius r (so the converter tests below compare to a
    correct expectation), and a 10-unit arc at r 400 fits inside the 52 degrees the fixture gives."""
    pts = _arc_expected(ARC["n"], ARC["cx"], ARC["cy"], ARC["r"], ARC["start"])
    assert len(pts) == 10
    for p, q in zip(pts, pts[1:]):
        assert abs(math.hypot(q[0] - p[0], q[1] - p[1]) - PITCH) < 1e-6
    assert all(abs(math.hypot(x - ARC["cx"], y - ARC["cy"]) - ARC["r"]) < 1e-6 for x, y in pts)
    assert 9 * math.degrees(2 * math.asin(PITCH / (2 * ARC["r"]))) <= ARC["end"] - ARC["start"]


def test_arc_converts_to_units_on_the_arc_facing_the_centre_at_the_pitch(tmp_path):
    """Story "units spaced at the block pitch along the arc, each facing the arc's centre" and Tests line "an arc converts to units on the arc facing the centre, spacing at the
    pitch": side A's ten units sit at start_deg + k*step on the radius-400 ring, each faces atan2(cy - y, cx - x), neighbours are 40 wu apart (within rounding)."""
    _, out = _converted(tmp_path, [("SIT-0200-arc.md", _sit2())])
    layout = _load(out, "L-0100")
    units = layout["side_a"]["units"]
    assert layout["side_a"]["headcount"] == 10 and len(units) == 10 and {u["role"] for u in units} == {"Bombard"}
    want = _arc_expected(ARC["n"], ARC["cx"], ARC["cy"], ARC["r"], ARC["start"])
    for u, (x, y) in zip(units, want):
        assert abs(u["x"] - x) < TOL and abs(u["y"] - y) < TOL, "unit at (%s, %s), the arc wants (%.2f, %.2f)" % (u["x"], u["y"], x, y)
        face = math.atan2(ARC["cy"] - u["y"], ARC["cx"] - u["x"])
        assert abs(math.atan2(math.sin(u["facing"] - face), math.cos(u["facing"] - face))) < 0.01, "facing %s, toward the centre is %.4f" % (u["facing"], face)
    for p, q in zip(units, units[1:]):
        assert abs(math.hypot(q["x"] - p["x"], q["y"] - p["y"]) - PITCH) < 0.1


def test_arc_layout_records_the_arc_under_the_side_and_check_layout_is_clean(tmp_path):
    """Architect ruling 2026-11-01 (replaces Interfaces 3's single `arc`): the converter records `side_a.arcs` as a LIST, one entry per arc row, each `{centre: [x, y], radius, start_deg,
    end_deg}`, in both the TOML and the JSON; a side with no arc row carries no `arcs` (or an empty one); `check_layout` (R1 to R5 and the arc rule R7) returns no violation."""
    _, out = _converted(tmp_path, [("SIT-0200-arc.md", _sit2())])
    toml_layout, json_layout = _load(out, "L-0100"), json.loads((out / "L-0100.json").read_text())
    for layout in (toml_layout, json_layout):
        assert "arc" not in layout["side_a"]
        arcs = layout["side_a"]["arcs"]
        assert isinstance(arcs, list) and len(arcs) == 1
        assert [float(c) for c in arcs[0]["centre"]] == [1500.0, 2000.0] and float(arcs[0]["radius"]) == 400.0
        assert float(arcs[0]["start_deg"]) == 154.0 and float(arcs[0]["end_deg"]) == 206.0
        assert not layout["side_b"].get("arcs")
    assert _check(toml_layout) == []


ARC2 = {"n": 5, "cx": 1900.0, "cy": 2000.0, "r": 300.0, "start": 160.0, "end": 200.0}   # a second arc east of the first: chord 40 at r 300 is 7.65 degrees, 4 steps = 30.6 of the 40 given


def _arc_row(a, role="Bombard"):
    return "| A | %s | %d | 0 | 0 | east | 0 | 0 | arc | %s | %s | %s | %s | %s |" % (role, a["n"], a["cx"], a["cy"], a["r"], a["start"], a["end"])


def test_two_arc_rows_on_one_side_give_two_arcs_entries_each_unit_on_its_own_ring(tmp_path):
    """Architect ruling 2026-11-01: "each Sides row is its own block or arc (an arc row's count is its units; two arc rows are two arcs)". Two arc rows on side A (10 Bombards on the
    radius-400 ring, 5 Wardens on the radius-300 ring) give `side_a.arcs` with two entries in row order, 15 units, the first 10 on the first ring and the last 5 on the second; `check_layout` is clean."""
    rows = [_arc_row(ARC), _arc_row(ARC2, "Warden")]
    _, out = _converted(tmp_path, [("SIT-0200-two.md", _sit2(a_rows=rows))])
    layout = _load(out, "L-0100")
    arcs, units = layout["side_a"]["arcs"], layout["side_a"]["units"]
    assert len(arcs) == 2 and layout["side_a"]["headcount"] == 15 and len(units) == 15
    assert [float(a["radius"]) for a in arcs] == [400.0, 300.0]
    for u in units[:10]:
        assert abs(math.hypot(u["x"] - 1500.0, u["y"] - 2000.0) - 400.0) < 1.0
    for u in units[10:]:
        assert abs(math.hypot(u["x"] - 1900.0, u["y"] - 2000.0) - 300.0) < 1.0
    assert _check(layout) == []


def test_an_arc_row_and_a_block_row_on_one_side_convert_clean(tmp_path):
    """Architect ruling 2026-11-01: "a side MAY mix arc and block rows". Side A is the 10-unit arc plus a block of 8 Vanguards anchored at (800, 3000): 18 units, one `arcs` entry,
    the 8 block units are not on the arc, and `check_layout` is clean."""
    rows = [_arc_row(ARC), "| A | Vanguard | 8 | 800 | 3000 | east | 0 | 0 | block |  |  |  |  |  |"]
    _, out = _converted(tmp_path, [("SIT-0200-mix.md", _sit2(a_rows=rows))])
    layout = _load(out, "L-0100")
    units = layout["side_a"]["units"]
    assert len(units) == 18 and layout["side_a"]["headcount"] == 18 and len(layout["side_a"]["arcs"]) == 1
    assert {u["role"] for u in units[10:]} == {"Vanguard"}
    assert all(abs(math.hypot(u["x"] - 1500.0, u["y"] - 2000.0) - 400.0) > 100.0 for u in units[10:])
    assert _check(layout) == []


def test_an_arc_that_cannot_hold_its_count_is_rejected_with_the_needed_radius(tmp_path):
    """Interfaces 2 and audit item 9: forty units on a radius-100 arc over 52 degrees cannot sit at the pitch; the converter prints `REJECT <sit> arc too small: 40 units at pitch
    40 on 52° need radius <r>` with r = ceil(PITCH / (2*sin(span_rad / (2*(n-1))))), exits 2, and writes no layout."""
    arc = dict(ARC, n=40, r=100.0)
    d = _sit(tmp_path, "SIT-0200-small.md", _sit2(arc=arc))
    out = tmp_path / "catalogue"
    out.mkdir()
    r = _run(d, out)
    need = math.ceil(PITCH / (2 * math.sin(math.radians(52) / (2 * 39))))
    assert r.returncode == 2, _said(r)
    assert "REJECT SIT-0200-small arc too small: 40 units at pitch 40 on 52° need radius %d" % need in _said(r), _said(r)
    assert list(out.glob("L-*.toml")) == []


def test_stage_two_without_expected_win_rate_is_rejected(tmp_path):
    """Interfaces 7: `Expected win rate` is required for `Stage: 2` and above; the converter prints `REJECT ... missing expected win rate` and exits 2."""
    d = _sit(tmp_path, "SIT-0200-norate.md", _sit2(expected=None, arc=None))
    out = tmp_path / "catalogue"
    out.mkdir()
    r = _run(d, out)
    assert r.returncode == 2 and re.search(r"^REJECT SIT-0200-norate .*missing expected win rate", _said(r), re.M), _said(r)


def test_layout_carries_predict_rate_orders_and_orders_point(tmp_path):
    """Interfaces 7 layout keys: `Expected win rate: 0.8`, `Orders: hold:A`, `Orders point: 1500 2000` give `predict_rate = 0.8`, `orders = "hold:A"`, `orders_point = [1500, 2000]`
    (TOML and JSON); the default `Orders point: midpoint` leaves `orders_point` out."""
    _, out = _converted(tmp_path, [("SIT-0200-keys.md", _sit2(expected="0.8", orders="hold:A", orders_point="1500 2000", arc=None))])
    for layout in (_load(out, "L-0100"), json.loads((out / "L-0100.json").read_text())):
        assert layout["predict_rate"] == 0.8 and layout["orders"] == "hold:A"
        assert [float(c) for c in layout["orders_point"]] == [1500.0, 2000.0]
        assert layout["predict"] == "A"
    out2 = tmp_path / "catalogue2"
    out2.mkdir()
    d = _sit(tmp_path / "second", "SIT-0201-mid.md", _sit2(arc=None))
    assert _run(d, out2).returncode == 0
    mid = _load(out2, "L-0100")
    assert "orders_point" not in mid and mid["predict_rate"] == 0.75


# ---------------------------------------------------------------- check_layout arc placement (Interfaces 3 as amended: `arcs` list, each unit against its own arc)

def _ring(a, k, off=0.0):
    ang = math.radians(a["start"]) + k * 2 * math.asin(PITCH / (2 * a["r"]))
    return a["cx"] + (a["r"] + off) * math.cos(ang), a["cy"] + (a["r"] + off) * math.sin(ang)


def _arc_layout(displace=0.0, onto_other=False):
    """An in-memory open_field layout: side A ten Bombards on ring 1 (`arcs[0]`) and five Wardens on ring 2 (`arcs[1]`), side B eight Raiders in a block. Each A unit is tagged
    `arc: <index>` and each arcs entry carries `count`, so either grouping the builder chose (tag or row order) identifies a unit's own arc. With `displace`, unit 3 of ring 1 is
    pushed that many wu outward; with `onto_other`, it is moved onto ring 2 (a point 15 degrees before ring 2's first unit): off its own arc but on the other arc's ring."""
    a = []
    for i in range(ARC["n"]):
        x, y = _ring(ARC, i, displace if i == 3 else 0.0)
        if i == 3 and onto_other:
            ang = math.radians(ARC2["start"] - 15.0)
            x, y = ARC2["cx"] + ARC2["r"] * math.cos(ang), ARC2["cy"] + ARC2["r"] * math.sin(ang)
        a.append({"role": "Bombard", "x": round(x, 2), "y": round(y, 2), "facing": 0.0, "layer": 0, "arc": 0})
    for i in range(ARC2["n"]):
        x, y = _ring(ARC2, i)
        a.append({"role": "Warden", "x": round(x, 2), "y": round(y, 2), "facing": 0.0, "layer": 0, "arc": 1})
    b = [{"role": "Raider", "x": 3200.0, "y": 1800.0 + 40.0 * i, "facing": 3.1416, "layer": 0} for i in range(8)]
    arcs = [{"centre": [A["cx"], A["cy"]], "radius": A["r"], "start_deg": A["start"], "end_deg": A["end"], "count": A["n"]} for A in (ARC, ARC2)]
    return {"id": "L-9200", "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "A", "predict_why": "t", "verdict": "", "feedback": "",
            "side_a": {"headcount": 15, "units": a, "arcs": arcs}, "side_b": {"headcount": 8, "units": b}}


def test_control_arc_layout_without_the_arcs_record_ignores_a_displaced_unit():
    """H-053 control, green today: the same layout with a unit 5 wu off its ring and no `arcs` record on the side passes check_layout, so the R7 reds below come from the arc rule."""
    layout = _arc_layout(displace=5.0)
    del layout["side_a"]["arcs"]
    assert _check(layout) == []


def test_arc_layout_with_every_unit_on_its_own_ring_passes():
    """Interfaces 3 as amended: every unit within 1 wu of its own arc's radius from its own centre; check_layout returns no violation."""
    assert _check(_arc_layout()) == []


def test_unit_off_the_ring_is_rejected_as_arc_placement():
    """Interfaces 3: a unit 5 wu off its ring is rejected: check_layout reports R7 (arc placement; R6 is the wall standoff rule), and the violation text reads
    `arc placement: unit <id> is <d> wu from the centre, radius 400`."""
    from scripts.skilllab.catalogue import produce
    layout = _arc_layout(displace=5.0)
    assert _check(layout) == ["R7"]
    details = [d for r, d in produce._violations(layout, presets(), rules()) if r == "R7"]
    assert details and re.search(r"arc placement: unit \S+ is [\d.]+ wu from the centre, radius 400", details[0]), details


def test_unit_on_the_other_arcs_ring_but_off_its_own_is_rejected():
    """Architect ruling 2026-11-01, positive control for the per-arc check: a ring-1 unit moved onto ring 2 lies exactly on a ring of the side, yet not on its own, so R7 rejects it
    (a check that tested every unit against every arc of the side would pass it)."""
    layout = _arc_layout(onto_other=True)
    ring2 = layout["side_a"]["units"][3]
    assert abs(math.hypot(ring2["x"] - ARC2["cx"], ring2["y"] - ARC2["cy"]) - ARC2["r"]) < 0.01
    assert _check(layout) == ["R7"]
