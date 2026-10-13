# spec: batch runner spec addendum 3 (batch3_spec.md) - the "enemy_position" batch in scripts/skilllab/batches.py
"""enemy_position batch: control plus three position plays, four not-expressed cells. Fake scan; no engine."""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, fake_sensors, faked  # noqa: E402

PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
DRAFT = "draft"
SCANNED = ["blob", "bait", "ambush", "fall_back"]
NOTES = {"bait_hold_fire": "needs hold-fire, not built", "ambush_hold_fire": "needs hold-fire, not built",
         "dark_approach": "going dark, emission per unit, needs Phase C G6",
         "dark_ambush": "going dark, emission per unit, needs Phase C G6"}
DRAFT_NUMBERS = "draft numbers: turn or spring tick 100, bait share 0.25, none confirmed"


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _run(tmp_path, fake=None, sub="out", real=False):
    defn = faked(batches.get("enemy_position"), real=real)
    fake = fake or FakeScan()
    return defn, fake, batches.run(defn, tmp_path / sub, scan_fn=fake)


def test_definition_cells_in_order_with_fields():
    d = batches.get("enemy_position")
    assert d.name == "enemy_position" and d.title and d.scene
    assert d.variants == (("default", {}),)
    assert [c.label for c in d.cells] == SCANNED + list(NOTES)
    for c in d.cells:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == (16, 8, 24, 10), c.label
    assert d.cells[0].status == "naive" and d.cells[0].build is not None
    for c in d.cells[1:4]:
        assert c.status == DRAFT and c.build is not None, c.label
    for c in d.cells[4:]:
        assert c.build is None and c.status == "not expressed" and c.note == NOTES[c.label], c.label
    assert d.weighted is False


def test_unexpressed_lists_the_four_and_the_draft_numbers():
    d = batches.get("enemy_position")
    for label in NOTES:
        assert label in d.unexpressed
    assert DRAFT_NUMBERS in d.unexpressed


def test_real_builds_are_blob_control_and_the_three_plays(monkeypatch):
    fake_sensors(monkeypatch)
    d = batches.get("enemy_position")
    steps = {c.label: len(c.build(16, False).timeline) for c in d.cells[:4]}
    assert steps == {"blob": 0, "bait": 2, "ambush": 1, "fall_back": 2}
    assert [g.order for g in d.cells[2].build(16, False).groups] == ["idle", "attack_move"]
    labels = {c.label: c.build.labels["play_side0"] for c in d.cells[:4]}
    assert labels["blob"] == "blob"
    for name in SCANNED[1:]:
        assert name in labels[name]


def test_scans_only_the_four_expressed_cells_never_the_not_expressed(tmp_path):
    d, fake, _ = _run(tmp_path)
    assert [c["label"] for c in fake.calls] == SCANNED
    assert not {c["label"] for c in fake.calls} & set(NOTES)
    for c in fake.calls:
        assert (c["size"], c["enemy_from"], c["enemy_to"], c["replicates"]) == (16, 8, 24, 10)
        assert c["setup"].settings == batches.BASE_SETTINGS and c["setup"].weighted is False


def test_scan_sees_the_timeline_of_each_real_build(tmp_path, monkeypatch):
    fake_sensors(monkeypatch)
    _, fake, _ = _run(tmp_path, real=True)
    got = {c["label"]: len(c["setup"].timeline) for c in fake.calls}
    assert got == {"blob": 0, "bait": 2, "ambush": 1, "fall_back": 2}


def test_run_file_statuses_and_notes(tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("bait", None): 20, ("ambush", None): None}))
    t = _text(paths["run"])
    assert t.index(PROVISIONAL) < t.index("## Scene")
    cells = _section(t, "Cells")
    for label in SCANNED + list(NOTES):
        assert label in cells
    results = _section(t, "Results")
    assert "16 units beat 20, lose to 21" in [ln for ln in results.splitlines() if ln.startswith("- bait")][0]
    assert "no break-even in range" in [ln for ln in results.splitlines() if ln.startswith("- ambush")][0]
    for name in ("bait", "ambush", "fall_back"):
        assert "(unconfirmed draft)" in [ln for ln in results.splitlines() if ln.startswith("- " + name)][0]
    assert "(unconfirmed draft)" not in [ln for ln in results.splitlines() if ln.startswith("- blob")][0]
    assert not any(label in results for label in NOTES)
    assert "None" not in t


def test_unexpressed_section_has_notes_and_draft_numbers(tmp_path):
    _, _, paths = _run(tmp_path)
    t = _text(paths["run"])
    sec = _section(t, "What the instrument could not express")
    for label, note in NOTES.items():
        assert label in sec and note in sec
    assert DRAFT_NUMBERS in sec
    scene = _section(t, "Scene")
    assert "draft" in scene
    assert "100" in t and "0.25" in t


def test_page_has_charts_and_not_expressed_notes(tmp_path):
    _, _, paths = _run(tmp_path)
    page = _text(paths["page"])
    assert PROVISIONAL in page and page.count("<svg") >= 4
    for label in SCANNED:
        assert label in page
    for label, note in NOTES.items():
        assert label in page and note in page


def test_csv_rows_only_for_expressed_cells(tmp_path):
    _, _, paths = _run(tmp_path)
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 4 * 17 * 2
    assert {r["cell"] for r in rows} == set(SCANNED)
    assert {r["variant"] for r in rows} == {"default"}
    assert {r["status"] for r in rows} == {"naive", DRAFT}


def test_enemy_position_deterministic(tmp_path):
    _, _, a = _run(tmp_path, sub="one")
    _, _, b = _run(tmp_path, sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
