# spec: batch runner spec addendum 4 (batch4_spec.md) section 1 - scripts/skilllab/compose.py, five slots
"""compose(skills): the five-slot rule (where, shape, layer, info, matchup). No engine."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import compose, skills  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from tests.skilllab.fakes_batches import fake_sensors  # noqa: E402


@pytest.fixture
def s3_registered(strip):
    """A fake S3 skilled play (status "fake"); the real S3 entry, if any, is saved and restored afterwards."""
    strip("S3")
    skills.register("S3", "skilled", lambda ctx: ("blob", {"radius": 100}, ctx.facing_deg), "fake")
    try:
        yield
    finally:
        skills.unregister("S3", "skilled")


def test_slots_and_skill_slot():
    assert compose.SLOTS == ("where", "shape", "layer", "info", "matchup")
    assert compose.SKILL_SLOT == {"S1": "where", "S2": "shape", "S3": "layer", "S4": "info", "S5": "matchup"}


def test_compose_empty_is_naive_and_expressible():
    c = compose.compose(())
    assert c.skills == () and c.missing == () and c.expressible is True and c.note == ""
    assert c.slots == {s: None for s in compose.SLOTS}
    assert list(c.slots) == list(compose.SLOTS)


def test_compose_one_registered_skill():
    c = compose.compose(["S2"])
    assert c.skills == ("S2",) and c.missing == () and c.expressible is True and c.note == ""
    assert c.slots == {"where": None, "shape": "S2", "layer": None, "info": None, "matchup": None}


def test_compose_one_skill_without_a_play(strip):
    strip("S1")
    c = compose.compose(["S1"])
    assert c.skills == ("S1",) and c.missing == ("S1",) and c.expressible is False
    assert c.slots["where"] == "S1" and c.note == "no skilled play for S1"


def test_compose_several_sorts_and_names_the_missing(strip):
    strip("S1", "S3", "S5")
    c = compose.compose(("S5", "S1", "S3"))
    assert c.skills == ("S1", "S3", "S5") and c.missing == ("S1", "S3", "S5") and c.expressible is False
    assert c.note == "no skilled play for S1, S3, S5"
    assert c.slots == {"where": "S1", "shape": None, "layer": "S3", "info": None, "matchup": "S5"}


def test_compose_accepts_sets_and_frozensets_alike():
    assert compose.compose({"S4", "S2"}) == compose.compose(frozenset({"S2", "S4"})) == compose.compose(["S4", "S2"])


def test_compose_all_five(strip):
    strip("S1", "S3", "S4", "S5")
    c = compose.compose(["S1", "S2", "S3", "S4", "S5"])
    assert c.missing == ("S1", "S3", "S4", "S5") and c.note == "no skilled play for S1, S3, S4, S5"
    assert c.slots == {"where": "S1", "shape": "S2", "layer": "S3", "info": "S4", "matchup": "S5"}


def test_missing_skill_beats_the_several_skills_note(strip):
    strip("S1")
    c = compose.compose(["S1", "S2"])
    assert c.missing == ("S1",) and c.note == "no skilled play for S1" and c.expressible is False


@pytest.mark.parametrize("bad", [["S9"], ["S2", "S2"], ["S1", "S3", "S1"], ["s2"]])
def test_unknown_or_repeated_skill_raises(bad):
    with pytest.raises(ValueError):
        compose.compose(bad)


def test_composition_is_frozen():
    c = compose.compose(["S2"])
    assert dataclasses.is_dataclass(c)
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.note = "x"


def test_registry_driven_register_and_restore(s3_registered, strip):
    strip("S1")
    c = compose.compose(["S3"])
    assert c.missing == () and c.expressible is True and c.note == "" and c.slots["layer"] == "S3"
    assert compose.compose(["S1", "S3"]).missing == ("S1",)
    pair = compose.compose(["S2", "S3"])
    assert pair.missing == () and pair.expressible is False
    assert pair.note.startswith("slot plays do not exist yet to fill ")
    assert "shape" in pair.note and "layer" in pair.note and pair.note.endswith(" together")
    assert "no skilled play" not in pair.note


def test_registry_restored_after_the_fixture():
    """The fake S3 is gone: S3 has either no entry or its real one, never the status "fake"."""
    try:
        play = skills.get("S3", "skilled")
    except ValueError:
        assert compose.compose(["S3"]).missing == ("S3",)
    else:
        assert play.status != "fake"
        assert compose.compose(["S3"]).missing == ()


def test_build_none_is_blob_v_blob(monkeypatch):
    fake_sensors(monkeypatch)
    got = compose.compose(()).build(16)(12, False)
    want = asym_play(16, Side("blob"), Side("blob"))(12, False)
    assert got == want
    assert [(g.formation, g.count) for g in got.groups] == [("blob", 16), ("blob", 12)]


def test_build_s2_is_skilled_v_blob(monkeypatch):
    fake_sensors(monkeypatch)
    build = compose.compose(["S2"]).build(16)
    assert build(10, False) == asym_play(16, Side("skilled", skill="S2"), Side("blob"))(10, False)
    assert [g.formation for g in build(10, False).groups] == ["concave", "blob"]
    assert build.labels["play_side0"] == "S2:skilled"


def test_build_a_registered_s3(s3_registered, monkeypatch):
    fake_sensors(monkeypatch)
    setup = compose.compose(["S3"]).build(8)(8, False)
    assert setup.groups[0].formation == "blob" and setup.groups[0].params == {"radius": 100}


def test_build_raises_not_implemented_with_the_note(s3_registered, strip):
    strip("S1")
    for names in (["S1"], ["S1", "S2", "S3"], ["S2", "S3"]):
        c = compose.compose(names)
        with pytest.raises(NotImplementedError, match=c.note):
            c.build(16)
