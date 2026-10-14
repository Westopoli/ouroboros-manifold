# spec: Architect ruling (matchup next item): layered cells at size 16 beside the interleaved ones, A174 draft
"""Matchup batch layered cells: 84 extra cells at size 16 (pairs with a mix), page third grid. Fake scan only."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym  # noqa: E402
from scripts.skilllab import batches  # noqa: E402
from scripts.skilllab.matchup import matchup_grid_html  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked, stub_summary_write  # noqa: E402,F401
from tests.skilllab.test_batches_matchup import AXIS, EXPECTED, MIXED, PURE, _beats, _label, _section, _text  # noqa: E402

RANGES = {"Raider": 200.0, "Vanguard": 300.0, "Bombard": 500.0, "Bastion": 250.0}
LAYERED = [(r, c) for r in AXIS for c in AXIS if r in MIXED or c in MIXED]
SCENE_SENTENCE = ("Layered cells (short-range types in front, long-range behind) run at size 16 only, "
                  "so the batch stays under about 30 minutes.")
NEW_LINE = ("arrangement: interleaved in every cell; layered (short range in front, long range behind) only at size 16 "
            "and only on the even two-type mixes, in the first pass; the reverse arrangement and layered at 32 are not run")


def _lab(r, c):
    return f"{r}_v_{c}@16:layered"


def _lbeats(r, c):
    """Break-evens for layered cells, different from every interleaved one at size 16."""
    return 1 + (AXIS.index(r) * 5 + AXIS.index(c) * 11) % 7


def _results():
    res = {(_label(r, c, n), None): _beats(r, c, n) for r, c, n in EXPECTED}
    res.update({(_lab(r, c), None): _lbeats(r, c) for r, c in LAYERED})
    return res


@pytest.fixture(autouse=True)
def _fake_ranges(monkeypatch):
    monkeypatch.setattr(asym, "unit_stats", lambda name: {
        "category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0,
        "attack_range": RANGES[name], "speed": 5.0, "sensor_radius": 700.0,
        "layer_transition_time": 0.0, "aoe_radius": 0.0})


def _run(tmp_path, sub="out"):
    defn = faked(batches.get("matchup"))
    return defn, batches.run(defn, tmp_path / sub, scan_fn=FakeScan(_results()))


def test_284_cells_old_ones_first_in_old_order():
    d = batches.get("matchup")
    assert len(d.cells) == 284
    assert [c.label for c in d.cells[:200]] == [_label(*x) for x in EXPECTED]
    assert all(":layered" not in c.label for c in d.cells[:200])
    assert all(c.size == 16 and c.status == "unconfirmed draft" for c in d.cells[200:])


def test_layered_labels_are_exactly_the_pairs_with_a_mix():
    d = batches.get("matchup")
    labels = [c.label for c in d.cells[200:]]
    assert len(labels) == 84 and len(set(labels)) == 84
    assert set(labels) == {_lab(r, c) for r, c in LAYERED}
    assert not any(_lab(r, c) in labels for r in PURE for c in PURE)
    assert all(c.size == 16 and (c.enemy_from, c.enemy_to, c.replicates) == (8, 24, 10) for c in d.cells[200:])


def _units(setup, side):
    return [g for g in setup.groups if g.side == side]


def _xs(g):
    return [x for x, _ in g.params["points"]]


@pytest.mark.parametrize("r,c", (("Vanguard+Raider", "Bastion"), ("Bombard", "Raider+Bastion"),
                                 ("Raider+Bombard", "Vanguard+Bastion")))
def test_layered_builds_rank_mix_sides_by_range(r, c):
    cell = {x.label: x for x in batches.get("matchup").cells}[_lab(r, c)]
    setup = cell.build(16, False)
    for side, name in ((0, r), (1, c)):
        gs = _units(setup, side)
        kinds = name.split("+")
        if len(kinds) == 1:
            assert len(gs) == 1 and gs[0].unit == kinds[0] and gs[0].count == 16
            continue
        assert all(g.formation == "points" for g in gs) and len(gs) == 2
        short, long_ = sorted(gs, key=lambda g: RANGES[g.unit])
        assert (short.count, long_.count) == (8, 8)
        if side == 0:     # nearest the enemy is the largest x
            assert min(_xs(short)) >= max(_xs(long_))
        else:
            assert max(_xs(short)) <= min(_xs(long_))


def test_layered_pure_side_matches_the_interleaved_build():
    by = {x.label: x for x in batches.get("matchup").cells}
    a = by[_lab("Vanguard+Raider", "Bastion")].build(16, False)
    b = by[_label("Vanguard+Raider", "Bastion", 16)].build(16, False)
    assert _units(a, 1) == _units(b, 1)
    assert [g.unit for g in _units(b, 0)] and not all(g.params == h.params for g, h in zip(_units(a, 0), _units(b, 0)))


def test_run_file_has_new_unexpressed_line_and_scene_sentence_once(tmp_path):
    _, paths = _run(tmp_path)
    t = _text(paths["run"])
    sec = _section(t, "What the instrument could not express")
    assert NEW_LINE in sec and "default interleaved only" not in sec
    assert t.count(SCENE_SENTENCE) == 1
    assert SCENE_SENTENCE in batches.get("matchup").scene
    assert NEW_LINE in batches.get("matchup").unexpressed


def test_run_file_cells_and_results_include_layered(tmp_path):
    _, paths = _run(tmp_path)
    t = _text(paths["run"])
    assert sum("_v_" in ln for ln in _section(t, "Cells").splitlines()) == 284
    res = _section(t, "Results")
    for r, c in LAYERED:
        assert any(_lab(r, c) in ln for ln in res.splitlines()), (r, c)


def _tables(page):
    return re.findall(r'<table class="grid">.*?</table>', page, re.S)


def test_page_has_three_grids_the_third_titled_layered(tmp_path):
    _, paths = _run(tmp_path)
    page = _text(paths["page"])
    assert page.count('<table class="grid">') == 3
    assert "layered, 16 units" in page
    assert page.index("16 units") < page.index("32 units") < page.index("layered, 16 units")


def test_existing_grids_show_only_interleaved_results(tmp_path):
    _, paths = _run(tmp_path)
    page = _text(paths["page"])
    tabs = _tables(page)
    for n, table in zip((16, 32), tabs[:2]):
        want = matchup_grid_html(AXIS, AXIS, {(r, c): _beats(r, c, n) for r in AXIS for c in AXIS}, n, "x")
        assert re.search(r'<table class="grid">.*?</table>', want, re.S).group(0) == table, n


def test_layered_grid_uses_layered_for_mixes_and_interleaved_for_pure_pairs(tmp_path):
    _, paths = _run(tmp_path)
    tab = _tables(_text(paths["page"]))[2]
    cells = {}
    for r in AXIS:
        for c in AXIS:
            cells[(r, c)] = _lbeats(r, c) if (r, c) in LAYERED else _beats(r, c, 16)
    want = matchup_grid_html(AXIS, AXIS, cells, 16, "x")
    assert re.search(r'<table class="grid">.*?</table>', want, re.S).group(0) == tab
    assert tab != _tables(_text(paths["page"]))[0]
    for r in PURE:
        for c in PURE:
            assert cells[(r, c)] == _beats(r, c, 16)


def test_page_has_a_paragraph_about_the_layered_grid(tmp_path):
    _, paths = _run(tmp_path)
    page = _text(paths["page"])
    i = page.index("layered, 16 units")
    assert re.search(r"<p>[^<]*(pure|interleaved)[^<]*</p>", page[:i][-1500:] + page[i:]) 
