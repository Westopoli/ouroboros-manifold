# spec: batch runner spec addendum 3 (batch3_spec.md) - the "combinations" batch in scripts/skilllab/batches.py
"""Combinations batch: 32 subset cells driven by the skills registry, plus counter:S2, and the Profile section."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, profile, skills  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, fake_sensors, faked  # noqa: E402

PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
DRAFT = "draft"
S3_AT_IMPORT = skills.get("S3", "skilled")
SUBSETS = profile.subsets()
LABELS = ["combo:none" if not s else "combo:" + "+".join(sorted(s)) for s in SUBSETS] + ["counter:S2"]


@pytest.fixture
def s3_registered(strip):
    """A fake S3 skilled play (a plain blob with radius 100); the real S3 entry is saved and restored afterwards."""
    strip("S3")
    skills.register("S3", "skilled", lambda ctx: ("blob", {"radius": 100}, ctx.facing_deg), DRAFT)
    try:
        yield
    finally:
        skills.unregister("S3", "skilled")


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _run(tmp_path, fake=None, sub="out"):
    defn = faked(batches.get("combinations"))
    fake = fake or FakeScan()
    return defn, fake, batches.run(defn, tmp_path / sub, scan_fn=fake)


def _rows(text):
    """The Profile section's data rows: list or table lines, minus an optional header and any separator."""
    lines = [ln.strip() for ln in _section(text, "Profile").splitlines() if ln.strip().startswith(("-", "|"))]
    lines = [ln for ln in lines if not re.fullmatch(r"[|\-\s:]+", ln)]
    if len(lines) == 33:
        lines = lines[1:]
    assert len(lines) == 32, lines
    return lines


def test_33_cells_in_order_with_fields():
    d = batches.get("combinations")
    assert d.name == "combinations" and d.title and d.scene
    assert len(LABELS) == 33 and LABELS[0] == "combo:none" and LABELS[-1] == "counter:S2"
    assert [c.label for c in d.cells] == LABELS
    assert d.variants == (("default", {}),) and d.weighted is False
    for c in d.cells:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == (16, 8, 24, 10), c.label


def test_with_only_s2_registered_two_subsets_are_expressed(strip):
    strip("S1", "S3", "S4", "S5")
    d = batches.get("combinations")
    cells = {c.label: c for c in d.cells}
    expressed = [c.label for c in d.cells[:32] if c.build is not None]
    assert expressed == ["combo:none", "combo:S2"]
    assert cells["combo:none"].status == "naive"
    assert cells["combo:S2"].status == skills.get("S2", "skilled").status == DRAFT
    assert cells["counter:S2"].build is not None and cells["counter:S2"].status == skills.get("S2", "counter").status
    for label in LABELS[:32]:
        if label not in expressed:
            assert cells[label].build is None and cells[label].status == "not expressed", label


def test_notes_name_the_skills_with_no_play(strip):
    strip("S1", "S3", "S4", "S5")
    cells = {c.label: c for c in batches.get("combinations").cells}
    assert "S1" in cells["combo:S1"].note and "S2" not in cells["combo:S1"].note
    assert "S1" in cells["combo:S1+S2"].note and "S2" not in cells["combo:S1+S2"].note
    n = cells["combo:S3+S4+S5"].note
    assert all(s in n for s in ("S3", "S4", "S5")) and "S1" not in n and "S2" not in n
    assert "S1" in cells["combo:S1+S2+S3+S4+S5"].note
    assert "no rule for combining plays" not in " ".join(c.note for c in cells.values())


def test_real_builds(monkeypatch):
    fake_sensors(monkeypatch)
    cells = {c.label: c for c in batches.get("combinations").cells}
    none, s2, counter = (cells[k].build(16, False) for k in ("combo:none", "combo:S2", "counter:S2"))
    assert [(g.formation, g.count) for g in none.groups] == [("blob", 16), ("blob", 16)]
    assert [g.formation for g in s2.groups] == ["concave", "blob"] and s2.groups[0].count == 16
    assert [g.formation for g in counter.groups] == ["column", "line"]


def test_scan_only_expressed_cells(tmp_path, strip):
    strip("S1", "S3", "S4", "S5")
    _, fake, _ = _run(tmp_path)
    assert [c["label"] for c in fake.calls] == ["combo:none", "combo:S2", "counter:S2"]
    for c in fake.calls:
        assert (c["size"], c["enemy_from"], c["enemy_to"], c["replicates"]) == (16, 8, 24, 10)
        assert c["setup"].settings == batches.BASE_SETTINGS


def test_registering_s3_changes_the_result(s3_registered, monkeypatch, strip):
    strip("S1", "S4", "S5")
    fake_sensors(monkeypatch)
    d = batches.get("combinations")
    cells = {c.label: c for c in d.cells}
    assert [c.label for c in d.cells[:32] if c.build is not None] == ["combo:none", "combo:S2", "combo:S3"]
    assert cells["combo:S3"].status == DRAFT
    setup = cells["combo:S3"].build(16, False)
    assert setup.groups[0].formation == "blob" and setup.groups[0].params == {"radius": 100}   # the S3 play, not S2's
    pair = cells["combo:S2+S3"]
    assert pair.build is None and pair.status == "not expressed"
    assert "no rule" not in pair.note and "slot plays do not exist yet to fill" in pair.note
    assert "shape" in pair.note and "layer" in pair.note
    assert "S3" not in cells["combo:S3+S4"].note and "S4" in cells["combo:S3+S4"].note
    assert "S1" in cells["combo:S1+S3"].note and "no rule" not in cells["combo:S1+S3"].note


def test_registry_is_restored_after_the_fixture():
    cells = {c.label: c for c in batches.get("combinations").cells}
    assert skills.get("S3", "skilled") == S3_AT_IMPORT      # the real S3 draft is back, the fake one is gone
    assert cells["combo:S3"].status == DRAFT


def test_scan_calls_follow_the_registry(s3_registered, tmp_path, strip):
    strip("S1", "S4", "S5")
    defn = faked(batches.get("combinations"))
    fake = FakeScan()
    batches.run(defn, tmp_path / "o", scan_fn=fake)
    assert [c["label"] for c in fake.calls] == ["combo:none", "combo:S2", "combo:S3", "counter:S2"]


def test_profile_section_rows_and_arithmetic(tmp_path, strip):
    strip("S1", "S3", "S4", "S5")
    results = {("combo:none", None): 12, ("combo:S2", None): 17}
    _, _, paths = _run(tmp_path, FakeScan(results))
    t = _text(paths["run"])
    heads = [m.group(1) for m in re.finditer(r"^## (.+?)\s*$", t, re.M)]
    assert heads.index("Results") < heads.index("Profile") < heads.index("What the instrument could not express")
    rows = _rows(t)
    assert "12" in rows[0]
    assert "S2" in rows[2] and "17" in rows[2] and re.search(r"(?<![\d.])5(?![\d.])", rows[2])
    assert "S1" in rows[1] and rows[1].count("not expressed") >= 2
    assert all("not expressed" in r for r in rows[3:] if "S2" not in r)
    assert "unconfirmed definition" in _section(t, "Profile")
    assert "%" not in _section(t, "Profile")


def test_profile_negative_advantage(tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("combo:none", None): 15, ("combo:S2", None): 10}))
    row = _rows(_text(paths["run"]))[2]
    assert "10" in row and "-5" in row


def test_profile_none_cases(tmp_path):
    _, _, a = _run(tmp_path, FakeScan({("combo:none", None): None, ("combo:S2", None): 17}), sub="a")
    row = _rows(_text(a["run"]))[2]
    assert "17" in row and "no break-even in range" in row                  # no control, so no advantage
    _, _, b = _run(tmp_path, FakeScan({("combo:none", None): 12, ("combo:S2", None): None}), sub="b")
    row = _rows(_text(b["run"]))[2]
    assert row.count("no break-even in range") >= 2                         # neither a break-even nor an advantage
    assert "None" not in _text(a["run"]) + _text(b["run"])


def test_profile_row_for_a_registered_s3(s3_registered, tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("combo:none", None): 10, ("combo:S3", None): 14}))
    rows = _rows(_text(paths["run"]))
    s3_index = SUBSETS.index(frozenset({"S3"}))
    assert "S3" in rows[s3_index] and "14" in rows[s3_index] and re.search(r"(?<![\d.])4(?![\d.])", rows[s3_index])
    pair = rows[SUBSETS.index(frozenset({"S2", "S3"}))]
    assert pair.count("not expressed") >= 2


def test_page_has_the_profile_table_and_charts(tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("combo:none", None): 12, ("combo:S2", None): 17}))
    page = _text(paths["page"])
    assert PROVISIONAL in page
    m = re.search(r"<h2>\s*Profile\s*</h2>", page)
    assert m
    tail = page[m.end():]
    assert tail.count("<tr") >= 33 and "<table" in tail
    assert "S2" in tail and "17" in tail
    assert page.count("<svg") >= 3
    for label in ("combo:none", "combo:S2", "counter:S2"):
        assert label in page


def test_combinations_deterministic(tmp_path):
    _, _, a = _run(tmp_path, sub="one")
    _, _, b = _run(tmp_path, sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
