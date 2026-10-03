# spec: batch runner spec addendum 2 (batch2_spec.md) - the "landscape" batch in scripts/skilllab/batches.py
"""Landscape batch: five map kinds, attackers against idle defenders, each cell with a naive-v-naive reference."""
import csv
import dataclasses
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, maps  # noqa: E402
from scripts.skilllab.terrain import shift_terrain  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, fake_sensors, faked  # noqa: E402

PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
KINDS = ("open", "block", "wall", "lane", "cover_field")
SCANNED = [f"{k}:{p}_v_defenders" for k in KINDS for p in ("blob", "line")]
TALL = {"tall_cover": "tall cover with height needs layer reach (Phase C G5)",
        "tall_cover_counter": "a layer above the cover needs layer reach and layer orders (Phase C G4, G5)"}
GUARD_LINE = "guard order not built: defenders idle"


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _run(tmp_path, fake=None, sub="out", real=False):
    defn = faked(batches.get("landscape"), real=real)
    fake = fake or FakeScan()
    return defn, fake, batches.run(defn, tmp_path / sub, scan_fn=fake)


def test_landscape_cells_in_order_with_fields():
    assert maps.KINDS == KINDS
    d = batches.get("landscape")
    assert d.name == "landscape" and d.title and d.scene
    assert [c.label for c in d.cells] == SCANNED + list(TALL)
    assert d.variants == (("idle", {}),)
    assert d.weighted is False and batches.DEFENDER_ORDER == "idle"
    for c in d.cells[:10]:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates, c.status) == (16, 8, 24, 10, "naive"), c.label
        assert c.build is not None and c.reference is not None and c.reference is not c.build
    for c in d.cells[10:]:
        assert c.build is None and c.status == "not expressed" and c.note == TALL[c.label]
    assert GUARD_LINE in d.unexpressed
    joined = " ".join(d.unexpressed)
    assert "tall_cover" in joined and "tall_cover_counter" in joined


def test_cell_builds_idle_the_defenders_and_leave_attackers(monkeypatch):
    fake_sensors(monkeypatch)
    d = batches.get("landscape")
    for c in d.cells[:10]:
        kind, rest = c.label.split(":")
        for heads in (8, 24):
            setup = c.build(heads, False)
            side0 = [g for g in setup.groups if g.side == 0]
            side1 = [g for g in setup.groups if g.side == 1]
            assert len(side0) == 1 and len(side1) == 1, c.label
            assert [g.order for g in side1] == ["idle"], c.label
            assert [g.order for g in side0] == ["attack_move"], c.label
            assert side0[0].formation == rest.split("_")[0] and side1[0].formation == "blob", c.label
            assert (side0[0].count, side1[0].count) == (16, heads)
            assert setup.terrain == shift_terrain(maps.sample_map(kind, 0), 2000.0, 2000.0), c.label


def test_reference_is_naive_against_naive_without_the_idle_rewrite(monkeypatch):
    """Mutant catcher: a reference built like the cell (idle defenders) must fail here."""
    fake_sensors(monkeypatch)
    d = batches.get("landscape")
    for c in d.cells[:10]:
        kind = c.label.split(":")[0]
        for heads in (8, 24):
            ref, cell = c.reference(heads, False), c.build(heads, False)
            assert [g.order for g in ref.groups if g.side == 1] == ["attack_move"], c.label
            assert [g.order for g in ref.groups if g.side == 0] == ["attack_move"], c.label
            assert {g.formation for g in ref.groups} == {"blob"}, c.label        # naive blob against naive blob
            assert ref.terrain == cell.terrain == shift_terrain(maps.sample_map(kind, 0), 2000.0, 2000.0), c.label
            assert ref != cell


def test_scan_once_per_cell_and_once_per_reference(tmp_path):
    d, fake, _ = _run(tmp_path)
    assert len(fake.calls) == 20
    cells = [c for c in fake.calls if not c["label"].endswith("#ref")]
    refs = [c for c in fake.calls if c["label"].endswith("#ref")]
    assert sorted(c["label"] for c in cells) == sorted(SCANNED)
    assert sorted(c["label"][:-4] for c in refs) == sorted(SCANNED)
    for c in fake.calls:
        assert (c["size"], c["enemy_from"], c["enemy_to"], c["replicates"]) == (16, 8, 24, 10)
        assert c["setup"].weighted is False
    assert not {c["label"] for c in fake.calls} & set(TALL)


def test_scan_sees_idle_defenders_and_unidled_references(tmp_path, monkeypatch):
    fake_sensors(monkeypatch)
    _, fake, _ = _run(tmp_path, real=True)
    assert len(fake.calls) == 20
    for c in fake.calls:
        side1 = [g.order for g in c["setup"].groups if g.side == 1]
        side0 = [g.order for g in c["setup"].groups if g.side == 0]
        want = ["attack_move"] if c["label"].endswith("#ref") else ["idle"]
        assert side1 == want and side0 == ["attack_move"], c["label"]


def test_reference_sentence_under_each_results_line(tmp_path):
    results = {("open:blob_v_defenders#ref", None): 12, ("block:line_v_defenders#ref", None): None,
               ("wall:blob_v_defenders", None): 20}
    _, _, paths = _run(tmp_path, FakeScan(results))
    lines = _section(_text(paths["run"]), "Results").splitlines()

    def after(label):
        i = [k for k, ln in enumerate(lines) if label in ln and "naive against naive" not in ln]
        assert len(i) == 1, label
        return lines[i[0] + 1]
    assert "naive against naive on this map: 16 units beat 12, lose to 13" in after("open:blob_v_defenders")
    assert "naive against naive on this map: no break-even in range" in after("block:line_v_defenders")
    assert "naive against naive on this map: 16 units beat 15, lose to 16" in after("lane:blob_v_defenders")
    assert "16 units beat 20" in [ln for ln in lines if "wall:blob_v_defenders" in ln][0]
    assert "None" not in "\n".join(lines)
    assert sum("naive against naive on this map" in ln for ln in lines) == 10


def test_page_has_charts_and_reference_sentences(tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("open:blob_v_defenders#ref", None): 12}))
    page = _text(paths["page"])
    assert PROVISIONAL in page
    assert page.count("<svg") >= 10
    for label in SCANNED:
        assert label in page
    assert page.count("naive against naive on this map") == 10
    assert "naive against naive on this map: 16 units beat 12, lose to 13" in page


def test_not_expressed_cells_listed_in_run_file_and_page(tmp_path):
    _, _, paths = _run(tmp_path)
    sec = _section(_text(paths["run"]), "What the instrument could not express")
    for label, note in TALL.items():
        assert label in sec and note in sec
    page = _text(paths["page"])
    for label, note in TALL.items():
        assert label in page and note in page


def test_run_file_and_page_say_defenders_idle_because_guard_is_not_built(tmp_path):
    _, _, paths = _run(tmp_path)
    t = _text(paths["run"])
    assert "idle" in _section(t, "Scene") and "guard" in _section(t, "Scene")
    assert GUARD_LINE in _section(t, "What the instrument could not express")
    page = _text(paths["page"])
    assert "idle" in page and "guard" in page
    assert t.index(PROVISIONAL) < t.index("## Scene")


def test_csv_rows_carry_defender_order(tmp_path):
    _, _, paths = _run(tmp_path)
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 10 * 17 * 2
    assert {r["defender_order"] for r in rows} == {"idle"}
    assert {r["cell"] for r in rows} == set(SCANNED)       # references are not rows
    assert {r["variant"] for r in rows} == {"idle"}


def test_landscape_deterministic(tmp_path):
    _, _, a = _run(tmp_path, sub="one")
    _, _, b = _run(tmp_path, sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
