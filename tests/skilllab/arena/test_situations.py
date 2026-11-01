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
    d.mkdir(exist_ok=True)
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
    with open(LD / "catalogue" / "L-0001.toml", "rb") as f:
        layout = tomllib.load(f)
    assert _check(layout) == []


def test_control_check_layout_sees_a_broken_layout():
    """H-040 part 5 control (detector): the same layout with side A's headcount off by one is caught as R4."""
    with open(LD / "catalogue" / "L-0001.toml", "rb") as f:
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
