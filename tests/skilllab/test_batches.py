# spec: batch runner spec (batch_spec.md) - scripts/skilllab/batches.py, NAMES/get/run, run file and page
"""Batch definitions and run() with a fake scan function; no engine."""
import csv
import dataclasses
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.skilllab.scan as scan_mod  # noqa: E402
from scripts.skilllab import batches, skills  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, fake_sensors, faked  # noqa: E402

PROVISIONAL = "Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed."
DRAFT = "draft"
SKILLS_UNEXPRESSED = ["S1", "S3", "S4", "S5"]


def _run(name, tmp_path, fake=None, sub="out", mutate=None):
    defn = faked(batches.get(name))
    if mutate:
        defn = mutate(defn)
    fake = fake or FakeScan()
    paths = batches.run(defn, tmp_path / sub, scan_fn=fake)
    return defn, fake, paths


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def test_names_and_get():
    assert batches.NAMES == ("formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations", "layers", "layout_search")
    assert batches.BASE_SETTINGS == {"OM_TP_PURSUE_BY_STEERING": 1}
    for n in batches.NAMES:
        if n == "layout_search":
            # P4 adds layout_search by design; it is dispatched through batches.layout_search, not get().
            assert callable(batches.layout_search)
            with pytest.raises(ValueError):
                batches.get(n)
            continue
        d = batches.get(n)
        assert d.name == n and d.title and d.scene
        assert dataclasses.is_dataclass(d)


def test_unknown_name_raises_value_error():
    with pytest.raises(ValueError):
        batches.get("nonsense")


FORMATION = [(f"{k}@{n}{suffix}", n, kind, st, p0, p1, unit)
             for suffix, unit in (("", "Vanguard"), (":Raider", "Raider"))
             for n in (16, 8, 32)
             for k, kind, st, p0, p1 in (("line", "line", "naive", "line", "blob"),
                                         ("blob", "blob", "naive", "blob", "blob"),
                                         ("concave", "concave", DRAFT, "S2:skilled", "blob"),
                                         ("counter", "counter", DRAFT, "S2:counter", "line"))]


def test_formation_cells_in_order_with_exact_fields(strip):
    strip("S1", "S3", "S4", "S5")
    d = batches.get("formation")
    assert [c.label for c in d.cells] == [f[0] for f in FORMATION]
    assert len(d.cells) == 24
    for c, (label, n, _, st, p0, p1, _unit) in zip(d.cells, FORMATION):
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == (n, n // 2, n * 3 // 2, 10), label
        assert c.status == st, label
        assert c.build is not None and c.build.labels["play_side0"] == p0, label
        assert c.build.labels["play_side1"] == p1, label
    assert d.variants == (("default", {}),)


def test_formation_unexpressed_list_names_the_gaps():
    d = batches.get("formation")
    joined = " ".join(d.unexpressed)
    for s in SKILLS_UNEXPRESSED:
        assert s in joined
    assert "short-range" not in joined and "Raider" not in joined      # the Raider variant is now in the batch
    assert "first anchor" in joined


def test_formation_status_comes_from_the_registered_play(strip):
    strip("S1", "S3", "S4", "S5")
    orig_s, orig_c = skills.get("S2", "skilled"), skills.get("S2", "counter")
    try:
        for role, orig in (("skilled", orig_s), ("counter", orig_c)):
            skills.unregister("S2", role)
            skills.register("S2", role, orig.fn, "confirmed with Westley")
        d = batches.get("formation")
        got = {c.label: c.status for c in d.cells}
        assert got["concave@16"] == got["counter@32"] == "confirmed with Westley"
        assert got["line@16"] == "naive"
    finally:
        for role, orig in (("skilled", orig_s), ("counter", orig_c)):
            skills.unregister("S2", role)
            skills.register("S2", role, orig.fn, orig.status)
    assert {c.label: c.status for c in batches.get("formation").cells}["concave@8"] == DRAFT


FOCUS = [("identical", "naive"), ("damage", "naive"), ("reach", "naive"),
         ("S2_skilled", DRAFT), ("S2_counter", DRAFT)]


def test_focus_fire_cells_and_variants(strip):
    strip("S1", "S3", "S4", "S5")
    d = batches.get("focus_fire")
    assert [c.label for c in d.cells] == [f[0] for f in FOCUS] + ["S1_skilled", "S3_skilled", "S4_skilled", "S5_skilled"]
    for c, (label, st) in zip(d.cells, FOCUS):
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates, c.status) == (16, 8, 24, 10, st), label
        assert c.build is not None
    for c in d.cells[5:]:
        assert c.build is None and c.status == "not expressed"
        assert c.note == "no skilled play until defined with Westley (A145)"
        assert c.label.split("_")[0] in d.unexpressed
    assert d.variants == (("nearest", {"OM_TP_TARGET_POLICY": 0}), ("most_damaged", {"OM_TP_TARGET_POLICY": 1}))


def test_scan_called_once_per_cell_and_variant_with_the_stated_args(tmp_path):
    for name, cells, variants in (("formation", 24, 1), ("focus_fire", 5, 2)):
        _, fake, paths = _run(name, tmp_path, sub=name)
        assert len(fake.calls) == cells * variants
        d = batches.get(name)
        want = [(c.label, c.size, c.enemy_from, c.enemy_to) for c in d.cells if c.build is not None
                for _ in d.variants]
        assert sorted((c["label"], c["size"], c["enemy_from"], c["enemy_to"]) for c in fake.calls) == sorted(want)
        assert all(c["replicates"] == 10 for c in fake.calls)


def test_settings_overlay_on_every_setup(tmp_path):
    _, fake, _ = _run("formation", tmp_path, sub="f")
    assert all(c["setup"].settings == {"OM_TP_PURSUE_BY_STEERING": 1} for c in fake.calls)
    _, fake, _ = _run("focus_fire", tmp_path, sub="g")
    for c in fake.calls:
        assert c["setup"].settings in ({"OM_TP_PURSUE_BY_STEERING": 1, "OM_TP_TARGET_POLICY": 0},
                                       {"OM_TP_PURSUE_BY_STEERING": 1, "OM_TP_TARGET_POLICY": 1})
    assert sorted({c["policy"] for c in fake.calls}) == [0, 1]
    assert sum(c["policy"] == 0 for c in fake.calls) == sum(c["policy"] == 1 for c in fake.calls) == 5


def test_default_scan_fn_is_looked_up_at_call_time(tmp_path, monkeypatch):
    fake = FakeScan()
    monkeypatch.setattr(scan_mod, "scan", fake)
    paths = batches.run(faked(batches.get("formation")), tmp_path / "late")
    assert len(fake.calls) == 24 and set(paths) == {"csv", "run", "page", "summary"}


def test_not_expressed_cells_are_never_scanned_and_are_listed(tmp_path):
    _, fake, paths = _run("focus_fire", tmp_path)
    assert not {c["label"] for c in fake.calls} & {"S1_skilled", "S3_skilled", "S4_skilled", "S5_skilled"}
    sec = _section(_text(paths["run"]), "What the instrument could not express")
    for s in ("S1_skilled", "S3_skilled", "S4_skilled", "S5_skilled"):
        assert s in sec


def test_only_unexpressed_cells_scan_nothing_but_still_write(tmp_path):
    def only(d):
        return dataclasses.replace(d, cells=tuple(c for c in d.cells if c.build is None))
    _, fake, paths = _run("focus_fire", tmp_path, mutate=only)
    assert fake.calls == []
    for k in ("csv", "run", "page"):
        assert Path(paths[k]).exists()
    assert "S1_skilled" in _section(_text(paths["run"]), "What the instrument could not express")


def test_paths_and_out_dir_created(tmp_path):
    out = tmp_path / "a" / "b"
    paths = batches.run(faked(batches.get("formation")), out, scan_fn=FakeScan())
    assert paths == {"csv": out / "formation.csv", "run": out / "formation_run.md",
                     "page": out / "formation_page.html"} or \
        {k: Path(v) for k, v in paths.items()} == {"csv": out / "formation.csv", "run": out / "formation_run.md",
                                                  "page": out / "formation_page.html", "summary": out / "summary.json"}


def test_csv_rows_carry_labels(tmp_path, strip):
    strip("S1", "S3", "S4", "S5")
    d, fake, paths = _run("focus_fire", tmp_path)
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 5 * 2 * 17 * 2
    assert {r["variant"] for r in rows} == {"nearest", "most_damaged"}
    assert {r["cell"] for r in rows} == {c.label for c in d.cells if c.build is not None}
    assert {r["size"] for r in rows} == {"16"}
    assert {r["enemy_heads"] for r in rows} == {str(n) for n in range(8, 25)}
    status = {r["cell"]: r["status"] for r in rows}
    assert status["S2_skilled"] == DRAFT and status["identical"] == "naive"
    assert "ticks" in rows[0] and "outcome" in rows[0]


def test_csv_size_and_range_for_formation(tmp_path):
    _, _, paths = _run("formation", tmp_path)
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    r = [r for r in rows if r["cell"] == "line@8"]
    assert {x["size"] for x in r} == {"8"} and {x["variant"] for x in r} == {"default"}
    assert {x["enemy_heads"] for x in r} == {str(n) for n in range(4, 13)}


def test_run_file_sections_in_fixed_order_with_provisional_line(tmp_path):
    d, _, paths = _run("formation", tmp_path)
    t = _text(paths["run"])
    assert t.startswith("# " + d.title)
    heads = ["## Scene", "## Cells", "## Results", "## What the instrument could not express", "## Files"]
    pos = [t.index(h) for h in heads]
    assert pos == sorted(pos)
    assert t.index(PROVISIONAL) < pos[0] and t.index(PROVISIONAL) > t.index("# " + d.title)
    assert d.scene in _section(t, "Scene")
    assert "## What changes" not in t
    files = _section(t, "Files")
    for n in ("formation.csv", "formation_run.md", "formation_page.html"):
        assert n in files


def test_cells_table_lists_every_cell_with_status(tmp_path, strip):
    strip("S1", "S3", "S4", "S5")
    d, _, paths = _run("focus_fire", tmp_path)
    sec = _section(_text(paths["run"]), "Cells")
    for c in d.cells:
        line = [ln for ln in sec.splitlines() if re.search(r"\b%s\b" % c.label, ln)]
        assert line, c.label
        assert c.status in line[0]
        assert str(c.replicates * 2) in line[0]
    assert DRAFT in [ln for ln in sec.splitlines() if "S2_skilled" in ln][0]


def test_results_are_counts_not_ratios(tmp_path):
    fake = FakeScan({("identical", 0): 15})
    _, _, paths = _run("focus_fire", tmp_path, fake)
    res = _section(_text(paths["run"]), "Results")
    assert "%" not in res
    assert not re.search(r"\d\s*/\s*\d", res)
    assert not re.search(r"ratio|percent", res, re.I)
    assert "16 units beat 15, lose to 16" in res
    assert re.search(r"unit.seconds", res)
    assert "100" in res                      # mean fight ticks from the hand-built fights
    assert "(unconfirmed draft)" in [ln for ln in res.splitlines() if "S2_skilled" in ln][0]


def test_no_break_even_in_range_when_beats_is_none(tmp_path):
    fake = FakeScan({("line@16", None): None})
    _, _, paths = _run("formation", tmp_path, fake)
    res = _section(_text(paths["run"]), "Results")
    line = [ln for ln in res.splitlines() if "line@16" in ln]
    assert line and "no break-even in range" in "\n".join(line)
    assert "beat None" not in res and "None" not in res
    other = [ln for ln in res.splitlines() if "blob@16" in ln]
    assert other and "no break-even in range" not in "\n".join(other)


def test_stalled_count_beside_each_result(tmp_path):
    fake = FakeScan({("blob@16", None): (15, 2)})
    _, _, paths = _run("formation", tmp_path, fake)
    res = _section(_text(paths["run"]), "Results")
    block = "\n".join(ln for ln in res.splitlines() if "blob@16" in ln)
    assert re.search(r"stalled\D{0,15}2\b|\b2\D{0,15}stalled", block)
    block0 = "\n".join(ln for ln in res.splitlines() if "line@16" in ln)
    assert re.search(r"stalled\D{0,15}0\b|\b0\D{0,15}stalled", block0)


FOCUS_RESULTS = {("identical", 0): 14, ("identical", 1): 16,      # gains
                 ("damage", 0): 16, ("damage", 1): 13,            # loses
                 ("reach", 0): 15, ("reach", 1): 15}              # no change


def test_focus_fire_what_changes(tmp_path):
    _, _, paths = _run("focus_fire", tmp_path, FakeScan(FOCUS_RESULTS))
    t = _text(paths["run"])
    assert t.index("## Results") < t.index("## What changes") < t.index("## Files")
    sec = _section(t, "What changes")

    def line(label):
        got = [ln for ln in sec.splitlines() if re.search(r"\b%s\b" % label, ln)]
        assert got, label
        return got[0]
    g, lo, nc = line("identical"), line("damage"), line("reach")
    assert "gains" in g and "loses" not in g and "no change" not in g
    assert "loses" in lo and "gains" not in lo and "no change" not in lo
    assert "no change" in nc and "gains" not in nc and "loses" not in nc
    assert "14" in g and "16" in g and "16" in lo and "13" in lo
    assert "%" not in sec


def test_page_has_provisional_line_and_one_chart_per_cell_and_variant(tmp_path):
    d, _, paths = _run("focus_fire", tmp_path, FakeScan(FOCUS_RESULTS))
    page = _text(paths["page"])
    assert PROVISIONAL in page and d.title in page
    assert page.count("<svg") >= 5 * 2
    for c in d.cells:
        if c.build is not None:
            assert c.label in page
    assert "nearest" in page and "most_damaged" in page
    d2, _, p2 = _run("formation", tmp_path, sub="f")
    assert _text(p2["page"]).count("<svg") >= 24


def test_formation_raider_cells_play_all_raider_on_both_sides(monkeypatch):
    fake_sensors(monkeypatch)
    d = batches.get("formation")
    assert len(d.cells) == 24
    for c, (label, n, _, _st, _p0, _p1, unit) in zip(d.cells, FORMATION):
        for heads in (c.enemy_from, c.enemy_to):
            setup = c.build(heads, False)
            assert {g.unit for g in setup.groups} == {unit}, label
            assert sum(g.count for g in setup.groups if g.side == 0) == n, label
            assert sum(g.count for g in setup.groups if g.side == 1) == heads, label


def test_formation_raider_cells_scanned_with_same_range_and_statuses(tmp_path):
    _, fake, _ = _run("formation", tmp_path)
    got = {c["label"]: (c["size"], c["enemy_from"], c["enemy_to"]) for c in fake.calls}
    for label, n, *_ in FORMATION:
        assert got[label] == (n, n // 2, n * 3 // 2), label
    assert all(not c["weighted"] for c in fake.calls)


RAIDER_RESULTS = {("line@16", None): 15, ("line@16:Raider", None): 16,       # Raider larger
                  ("blob@16", None): 15, ("blob@16:Raider", None): 15,       # same
                  ("concave@16", None): 16, ("concave@16:Raider", None): 14,  # Raider smaller
                  ("counter@16", None): None, ("counter@16:Raider", None): 12,
                  ("line@8", None): 7, ("line@8:Raider", None): 6}


def _raider_lines(path):
    sec = _section(_text(path), "Vanguard against Raider")
    out = {}
    for ln in sec.splitlines():
        m = re.search(r"\b((?:line|blob|concave|counter)@\d+): Vanguard", ln)
        if m:
            out[m.group(1)] = ln
    return sec, out


def test_vanguard_against_raider_section_in_run_file(tmp_path):
    _, _, paths = _run("formation", tmp_path, FakeScan(RAIDER_RESULTS))
    t = _text(paths["run"])
    assert t.index("## Results") < t.index("## Vanguard against Raider") < t.index("## What the instrument could not express")
    sec, lines = _raider_lines(paths["run"])
    assert list(lines) == [f"{k}@{n}" for n in (16, 8, 32) for k in ("line", "blob", "concave", "counter")]
    assert "line@16: Vanguard 16 units beat 15; Raider 16 units beat 16; Raider larger" in lines["line@16"]
    assert "blob@16: Vanguard 16 units beat 15; Raider 16 units beat 15; same" in lines["blob@16"]
    assert "concave@16: Vanguard 16 units beat 16; Raider 16 units beat 14; Raider smaller" in lines["concave@16"]
    assert "line@8: Vanguard 8 units beat 7; Raider 8 units beat 6; Raider smaller" in lines["line@8"]
    assert "%" not in sec and not re.search(r"ratio|percent", sec, re.I)


def test_vanguard_against_raider_none_reads_no_break_even(tmp_path):
    _, _, paths = _run("formation", tmp_path, FakeScan(RAIDER_RESULTS))
    _, lines = _raider_lines(paths["run"])
    assert "Vanguard 16 units: no break-even in range" in lines["counter@16"] or \
        "no break-even in range" in lines["counter@16"].split("Raider")[0]
    assert "Raider 16 units beat 12" in lines["counter@16"]
    assert "None" not in "\n".join(lines.values())
    _, _, p2 = _run("formation", tmp_path, FakeScan({("line@16:Raider", None): None}), sub="r")
    _, l2 = _raider_lines(p2["run"])
    assert "no break-even in range" in l2["line@16"].split("Raider")[1]
    assert "None" not in "\n".join(l2.values())


def test_vanguard_against_raider_in_page_and_not_in_other_batches(tmp_path):
    _, _, paths = _run("formation", tmp_path, FakeScan(RAIDER_RESULTS))
    page = _text(paths["page"])
    assert "Vanguard against Raider" in page
    for word in ("Raider larger", "Raider smaller", "same"):
        assert word in page.split("Vanguard against Raider", 1)[1]
    _, _, p2 = _run("focus_fire", tmp_path, sub="g")
    assert "Vanguard against Raider" not in _text(p2["run"]) + _text(p2["page"])


@pytest.mark.parametrize("name", ["formation", "focus_fire", "matchup", "landscape", "enemy_position", "combinations", "layers"])
def test_deterministic_byte_identical(tmp_path, name):
    _, _, a = _run(name, tmp_path, FakeScan(FOCUS_RESULTS), sub="one")
    _, _, b = _run(name, tmp_path, FakeScan(FOCUS_RESULTS), sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
