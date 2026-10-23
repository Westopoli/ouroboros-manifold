# Rule pins: R-096-08@629328
# spec: R-096-08 (guard) - the landscape batch with guard defenders and the two tall-cover cells expressed
"""landscape batch: 12 expressed cells, nothing unexpressed, defenders guard. Fake sensors, no engine."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_batches import fake_sensors, stub_summary_write  # noqa: E402,F401
from scripts.skilllab import batches  # noqa: E402

TALL = ("tall_cover", "tall_cover_counter")


@pytest.fixture
def d(monkeypatch):
    fake_sensors(monkeypatch)
    return batches.get("landscape")


def test_defender_order_is_guard_and_names_the_variant():
    assert batches.DEFENDER_ORDER == "guard"
    assert batches.get("landscape").variants == (("guard", {}),)


def test_twelve_expressed_cells_and_nothing_unexpressed(d):
    assert len(d.cells) == 12 and all(c.build is not None for c in d.cells)
    assert d.unexpressed == ()
    assert [c.label for c in d.cells][-2:] == list(TALL)
    assert all(c.status != "not expressed" for c in d.cells)


def test_tall_cover_cells_are_unconfirmed_drafts_with_the_numbers_in_the_note(d):
    for c in d.cells[10:]:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == (16, 8, 24, 10), c.label
        assert c.status == "unconfirmed draft", c.label
        assert "height 3" in c.note and "radius 100" in c.note and "150" in c.note, c.note


def test_every_side_one_group_of_every_cell_guards(d):
    for c in d.cells:
        for heads in (8, 24):
            side1 = [g for g in c.build(heads, False).groups if g.side == 1]
            assert side1 and {g.order for g in side1} == {"guard"}, c.label
            assert {g.order for g in c.build(heads, False).groups if g.side == 0} == {"attack_move"}, c.label


def test_tall_cover_cells_have_a_naive_blob_reference_on_the_same_terrain(d, monkeypatch):
    for c in d.cells[10:]:
        assert c.reference is not None and c.reference is not c.build, c.label
        ref, cell = c.reference(12, False), c.build(12, False)
        assert ref.terrain == cell.terrain and ref.terrain.covers, c.label
        assert {g.order for g in ref.groups} == {"attack_move"} and {g.formation for g in ref.groups} == {"blob"}
        assert ref.unit_types == {} and {g.layer for g in ref.groups} == {0}, c.label


def test_counter_cell_lifts_attackers_and_the_plain_cell_does_not(d):
    plain, counter = (c.build(12, False) for c in d.cells[10:])
    assert {g.layer for g in plain.groups if g.side == 0} == {0}
    assert {g.layer for g in counter.groups if g.side == 0} == {3}
    assert "VanguardHigh" in counter.unit_types


def test_all_twelve_cells_have_a_reference(d):
    assert all(c.reference is not None for c in d.cells)


def test_scene_text_says_the_defenders_guard(d):
    assert "guard" in d.scene and "idle" not in d.scene
    assert "not built" not in d.scene


def test_tall_cover_counter_cell_keeps_the_scenes_reach_settings():
    """A cell's settings overlay the scene's own (the counter's draft reach settings), they do not replace them."""
    from scripts.skilllab import batches
    d = batches.get("landscape")
    cell = next(c for c in d.cells if c.label == "tall_cover_counter")
    setup = batches._with_settings(cell.build, {**d.variants[0][1], **cell.settings})(12, False)
    assert setup.settings["OM_TP_RANGE_DOWN_3"] == 1.0
    assert setup.settings["OM_TP_PURSUE_BY_STEERING"] == 1
