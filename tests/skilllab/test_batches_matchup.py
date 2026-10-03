# spec: batch runner spec addendum 2 (batch2_spec.md) - the "matchup" batch in scripts/skilllab/batches.py
"""Matchup batch: 10 x 10 pairs of unit types and even mixes, weighted firing on. Fake scan only; no engine."""
import csv
import dataclasses
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from scripts.skilllab.matchup import matchup_grid_html  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, fake_sensors, faked  # noqa: E402

PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
PURE = ("Vanguard", "Raider", "Bombard", "Bastion")
MIXED = ("Vanguard+Raider", "Vanguard+Bombard", "Vanguard+Bastion", "Raider+Bombard", "Raider+Bastion",
         "Bombard+Bastion")
AXIS = PURE + MIXED
SIZES = (16, 32)
EXPECTED = [(r, c, n) for n in SIZES for r in AXIS for c in AXIS]


def _label(r, c, n):
    return f"{r}_v_{c}@{n}"


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _beats(r, c, n):
    """A distinct in-range break-even for most pairs; one pair has none."""
    if (r, c, n) == ("Bastion", "Raider", 16):
        return None
    return n // 2 + (AXIS.index(r) * 7 + AXIS.index(c) * 3) % n


def _results():
    return {(_label(r, c, n), None): _beats(r, c, n) for r, c, n in EXPECTED}


def _run(tmp_path, fake=None, sub="out", mutate=None):
    defn = faked(batches.get("matchup"))
    if mutate:
        defn = mutate(defn)
    fake = fake or FakeScan(_results())
    return defn, fake, batches.run(defn, tmp_path / sub, scan_fn=fake)


def test_matchup_definition_fields_and_cell_order():
    d = batches.get("matchup")
    assert d.name == "matchup" and d.title and d.scene
    assert d.weighted is True
    assert d.variants == (("default", {}),)
    assert [c.label for c in d.cells] == [_label(*x) for x in EXPECTED]      # 200 cells, size 16 then 32
    for c, (r, col, n) in zip(d.cells, EXPECTED):
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates, c.status) == (n, n // 2, n * 3 // 2, 10, "naive")
        assert c.build is not None and c.reference is None


def test_matchup_scene_and_unexpressed_lines():
    d = batches.get("matchup")
    for want in ("the weighted count reads the engine's target (its sight and reach), so a unit counts once the engine has given it a target",
                 "only even two-type mixes; unequal mixes and three-type mixes are not included",
                 "arrangement is the default interleaved only"):
        assert want in d.unexpressed
    assert "weighted" in d.scene and "blob" in d.scene


def test_matchup_builds_put_the_mix_on_each_side(monkeypatch):
    fake_sensors(monkeypatch)
    d = batches.get("matchup")
    by = {c.label: c for c in d.cells}

    def counts(setup, side):
        out = {}
        for g in setup.groups:
            if g.side == side:
                out[g.unit] = out.get(g.unit, 0) + g.count
        return out
    pairs = (("Vanguard", "Bastion"), ("Vanguard+Raider", "Bombard"), ("Raider", "Raider+Bastion"),
             ("Bombard+Bastion", "Vanguard+Bombard"), ("Bastion", "Bastion"))
    for r, c in pairs:
        cell = by[_label(r, c, 16)]
        setup = cell.build(8, False)
        for side, name, heads in ((0, r, 16), (1, c, 8)):
            kinds = name.split("+")
            assert counts(setup, side) == {k: heads // len(kinds) for k in kinds}, (r, c, side)
    setup = by[_label("Vanguard", "Raider", 32)].build(24, False)
    assert counts(setup, 0) == {"Vanguard": 32} and counts(setup, 1) == {"Raider": 24}


def test_matchup_scanned_once_per_cell_with_range_and_weighted_setups(tmp_path):
    _, fake, _ = _run(tmp_path)
    assert len(fake.calls) == 200
    want = sorted((_label(*x), x[2], x[2] // 2, x[2] * 3 // 2) for x in EXPECTED)
    assert sorted((c["label"], c["size"], c["enemy_from"], c["enemy_to"]) for c in fake.calls) == want
    assert all(c["setup"].weighted is True for c in fake.calls)
    assert all(c["replicates"] == 10 and c["setup"].settings == {"OM_TP_PURSUE_BY_STEERING": 1} for c in fake.calls)


def test_weighted_comes_from_the_batch_flag(tmp_path):
    """A matchup run whose batch is not weighted must not turn weighted on (mutant catcher for a hard-coded flag)."""
    _, fake, _ = _run(tmp_path, sub="off", mutate=lambda d: dataclasses.replace(d, weighted=False))
    assert all(c["setup"].weighted is False for c in fake.calls)
    _, fake, _ = _run(tmp_path, sub="on")
    assert all(c["setup"].weighted is True for c in fake.calls)


def test_matchup_results_carry_weighted_unit_seconds(tmp_path):
    _, _, paths = _run(tmp_path)
    res = _section(_text(paths["run"]), "Results")
    line = [ln for ln in res.splitlines() if _label("Vanguard", "Raider", 16) in ln]
    assert line
    assert re.search(r"weighted firing unit.seconds 1\.50 side 0, 0\.75 side 1", line[0])
    assert "%" not in res and "None" not in res
    assert "16 units beat" in line[0]
    none_line = [ln for ln in res.splitlines() if _label("Bastion", "Raider", 16) in ln]
    assert "no break-even in range" in none_line[0]


def test_matchup_cells_table_lists_all_pairs(tmp_path):
    _, _, paths = _run(tmp_path)
    sec = _section(_text(paths["run"]), "Cells")
    assert sum("_v_" in ln for ln in sec.splitlines()) == 200
    assert "Bombard+Bastion_v_Vanguard+Raider@32" in sec


def test_matchup_run_file_lists_unexpressed(tmp_path):
    _, _, paths = _run(tmp_path)
    t = _text(paths["run"])
    assert t.index(PROVISIONAL) < t.index("## Scene")
    sec = _section(t, "What the instrument could not express")
    assert "weighted count reads the engine's target" in sec
    assert "only even two-type mixes" in sec and "default interleaved only" in sec


def test_matchup_page_has_one_grid_per_size_and_no_cell_charts(tmp_path):
    _, _, paths = _run(tmp_path)
    page = _text(paths["page"])
    assert PROVISIONAL in page
    assert page.count('<table class="grid">') == 2
    assert "<svg" not in page
    for n in SIZES:
        grid = matchup_grid_html(AXIS, AXIS, {(r, c): _beats(r, c, n) for r in AXIS for c in AXIS}, n, "x")
        table = re.search(r'<table class="grid">.*?</table>', grid, re.S).group(0)
        assert table in page, n
        head = re.search(r"<h2>(Most lopsided pair:.*?|No pair has a break-even in range\.)</h2>", grid).group(0)
        assert head in page, n
    assert page.index('<table class="grid">') < page.rindex('<table class="grid">')


def test_matchup_csv_rows(tmp_path):
    _, _, paths = _run(tmp_path)
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 100 * 17 * 2 + 100 * 33 * 2
    assert {r["cell"] for r in rows} == {_label(*x) for x in EXPECTED}
    assert {r["variant"] for r in rows} == {"default"}
    assert "weighted_unit_seconds_0" in rows[0]
    assert "defender_order" not in rows[0]


def test_matchup_deterministic(tmp_path):
    _, _, a = _run(tmp_path, sub="one")
    _, _, b = _run(tmp_path, sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
