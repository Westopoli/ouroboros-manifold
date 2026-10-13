# spec: batch runner spec addendum 3 (batch3_spec.md) - the "layers" batch in scripts/skilllab/batches.py
"""Layers batch: LA, LB, LC tables by three scenes, plus the 16 reach-against-body-size cells. Fake scan; no engine."""
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
DRAFT = "draft"
SCENES = ("mirror", "choke", "choke_phase_b")
UPS = ((0.5, 0.25), (0.5, 0.5), (0.75, 0.25), (0.75, 0.5), (1.0, 0.25), (1.0, 0.5))
SWEEP_NOTE = "settings are draft sweep points (A174)"
REACH_NOTE = ("reach set per the reach table (Vanguard 0 up 0 down); every unit is on layer 0, so the "
              "layer settings have no effect in this scene (a layered scene is still needed)")
REACH_TABLE_TEXT = ("Vanguard and Warden 0 up 0 down; Raider 1 up 1 down; Interceptor 2 up 1 down; "
                    "Bombard and Bastion 0 up 2 down (set per cell on the unit type through om_roster_set_reach)")


def _la():
    s = {}
    for n, v in ((1, 0.5), (2, 0.2), (3, 0.0), (4, 0.0)):
        s["OM_TP_VISION_UP_%d" % n] = s["OM_TP_VISION_DOWN_%d" % n] = v
    for n in (1, 2):
        for name in ("RANGE", "DAMAGE"):
            s["OM_TP_%s_UP_%d" % (name, n)] = s["OM_TP_%s_DOWN_%d" % (name, n)] = 1.0
    return s


def _lb(u1, u2):
    return {**_la(), "OM_TP_RANGE_UP_1": u1, "OM_TP_RANGE_UP_2": u2}


def _lc(u1, u2, d):
    return {**_lb(u1, u2), "OM_TP_DAMAGE_UP_1": d, "OM_TP_DAMAGE_UP_2": d / 2, "OM_TP_DAMAGE_DOWN_1": 1.0,
            "OM_TP_DAMAGE_DOWN_2": 1.0}


def _dims(label):
    """(size, enemy_from, enemy_to) of a cell: the Phase B choke is 8 defenders against 7 to 12 attackers."""
    return (8, 7, 12) if "choke_phase_b" in label else (16, 8, 24)


def _expected():
    """[(label, settings, expressed, note_ok)] in the spec's order."""
    out = []
    for scene in SCENES:
        out.append(("LA:" + scene, _la(), True))
    for scene in SCENES:
        for u1, u2 in UPS:
            out.append(("LB:%s:up1=%s,up2=%s" % (scene, u1, u2), _lb(u1, u2), True))
    for scene in SCENES:
        for d in (0.5, 0.75):
            for u1, u2 in UPS:
                out.append(("LC:%s:up1=%s,up2=%s,dmg1=%s" % (scene, u1, u2, d), _lc(u1, u2, d), True))
    for r in (10, 15, 20, 30):
        for a in (150, 200, 300, 450):
            out.append(("body%d_range%d_ratio%.1f" % (2 * r, a, a / (2 * r)), {"OM_TP_UNIT_COLLISION_RADIUS": r}, True))
    return out


EXPECTED = _expected()
BODY = [e for e in EXPECTED if e[0].startswith("body")]
EXPRESSED = [e[0] for e in EXPECTED if e[2]]
NOT_EXPRESSED = [e[0] for e in EXPECTED if not e[2]]


def _text(p):
    return Path(p).read_text(encoding="utf-8")


def _section(text, head):
    m = re.search(r"^## %s\s*$" % re.escape(head), text, re.M)
    assert m, head
    nxt = re.search(r"^## ", text[m.end():], re.M)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


def _run(tmp_path, fake=None, sub="out", real=False, mutate=None):
    defn = faked(batches.get("layers"), real=real)
    if mutate:
        defn = mutate(defn)
    fake = fake or FakeScan()
    return defn, fake, batches.run(defn, tmp_path / sub, scan_fn=fake)


def test_counts_and_order_and_labels():
    d = batches.get("layers")
    assert d.name == "layers" and d.title and d.scene
    assert len(EXPECTED) == 3 + 18 + 36 + 16 == 73
    assert [c.label for c in d.cells] == [e[0] for e in EXPECTED]
    assert d.variants == (("default", {}),) and d.weighted is False


def test_every_cell_is_16_units_against_8_to_24_with_10_replicates_except_choke_phase_b():
    for c in batches.get("layers").cells:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == _dims(c.label) + (10,), c.label


def test_choke_phase_b_cells_are_8_defenders_against_7_to_12():
    cells = [c for c in batches.get("layers").cells if "choke_phase_b" in c.label]
    assert [c.label for c in cells][0] == "LA:choke_phase_b" and len(cells) == 1 + 6 + 12
    for c in cells:
        assert (c.size, c.enemy_from, c.enemy_to, c.replicates) == (8, 7, 12, 10), c.label


def test_settings_per_cell_including_not_expressed():
    d = batches.get("layers")
    for c, (label, settings, _) in zip(d.cells, EXPECTED):
        assert c.settings == settings, label
    for c in d.cells:
        if c.build is None:
            assert c.settings, c.label            # kept on not-expressed cells so a later change only adds a build


def test_celldef_settings_field_defaults_to_empty():
    assert batches.CellDef("x", 1, 1, 1, 1, None, "naive").settings == {}
    assert batches.get("formation").cells[0].settings == {}


def test_which_cells_are_expressed():
    d = batches.get("layers")
    assert [c.label for c in d.cells if c.build is not None] == EXPRESSED
    assert [c.label for c in d.cells if c.build is None] == NOT_EXPRESSED
    assert len(EXPRESSED) == 3 + 54 + 16 and "LA:mirror" in EXPRESSED and "LA:choke" in EXPRESSED
    assert "LA:choke_phase_b" in EXPRESSED
    for c in d.cells:
        if c.build is not None:
            assert c.status == DRAFT, c.label
        else:
            assert c.status == "not expressed", c.label


def test_notes():
    d = {c.label: c for c in batches.get("layers").cells}
    assert d["LA:mirror"].note == SWEEP_NOTE and d["LA:choke"].note == SWEEP_NOTE
    assert d["LA:choke_phase_b"].note == SWEEP_NOTE
    for label, c in d.items():
        if label.startswith(("LB:", "LC:")):
            assert c.note == REACH_NOTE, label
    for label, settings, _ in BODY:
        r, c = settings["OM_TP_UNIT_COLLISION_RADIUS"], d[label]
        body, rng = int(label[4:].split("_")[0]), int(label.split("_range")[1].split("_")[0])
        ratio = label.split("_ratio")[1]
        assert body == 2 * r
        for token in (str(r), str(body), str(rng), ratio):
            assert token in c.note, (label, token, c.note)


def test_lb_lc_cells_are_expressed_with_reach_per_the_table(monkeypatch):
    """test-defect fix: the stale gate said LB/LC need set_reach, which engine.py binds and G5 provides."""
    fake_sensors(monkeypatch)
    d = {c.label: c for c in batches.get("layers").cells}
    for label, c in d.items():
        if label.startswith(("LB:", "LC:")):
            assert c.build is not None and c.status == DRAFT, label
            setup = c.build(8 if "phase_b" in label else 16, False)
            names = {g.unit for g in setup.groups}
            assert len(names) == 1, label
            (name,) = names
            assert setup.unit_types[name] == {"base": "Vanguard", "reach": (0, 0)}, label


def test_body_cells_are_raider_mirrors_with_ranged_unit_types(monkeypatch):
    fake_sensors(monkeypatch)
    d = {c.label: c for c in batches.get("layers").cells}
    for label, settings, _ in BODY:
        rng = int(label.split("_range")[1].split("_")[0])
        name = "RaiderR%d" % rng
        setup = d[label].build(16, False)
        assert {g.unit for g in setup.groups} == {name}, label
        assert [g.side for g in setup.groups] == [0, 1] and [g.count for g in setup.groups] == [16, 16]
        assert setup.unit_types[name] == {"base": "Raider", "set": {"attack_range": rng}}, label
        assert setup.terrain is None and all(g.layer == 0 for g in setup.groups)


def test_mirror_is_one_layer_blob_v_blob_and_choke_is_the_sampled_wall(monkeypatch):
    fake_sensors(monkeypatch)
    d = {c.label: c for c in batches.get("layers").cells}
    mirror, choke = d["LA:mirror"].build(16, False), d["LA:choke"].build(12, False)
    for setup, heads in ((mirror, 16), (choke, 12)):
        assert [(g.side, g.formation, g.layer, g.order, g.unit) for g in setup.groups] == [
            (0, "blob", 0, "attack_move", "Vanguard"), (1, "blob", 0, "attack_move", "Vanguard")]
        assert setup.groups[1].count == heads
    assert mirror.terrain is None
    assert choke.terrain == shift_terrain(maps.sample_map("wall", 0), 2000.0, 2000.0)


def test_choke_phase_b_build_is_the_phase_b_scene(monkeypatch):
    fake_sensors(monkeypatch)
    d = {c.label: c for c in batches.get("layers").cells}
    setup = d["LA:choke_phase_b"].build(9, False)
    assert [(g.side, g.count, g.formation, g.order) for g in setup.groups] == [
        (0, 8, "line", "attack_move"), (1, 9, "blob", "attack_move")]
    assert setup.terrain.canvas == (3000.0, 1600.0) and len(setup.terrain.blocks) == 2
    assert [g.layer for g in setup.groups] == [0, 0]


def test_scan_calls_only_expressed_cells_with_the_overlay(tmp_path):
    _, fake, _ = _run(tmp_path)
    assert [c["label"] for c in fake.calls] == EXPRESSED
    assert not {c["label"] for c in fake.calls} & set(NOT_EXPRESSED)
    want = {e[0]: e[1] for e in EXPECTED}
    for c in fake.calls:
        assert c["setup"].settings == {**batches.BASE_SETTINGS, **want[c["label"]]}, c["label"]
        assert (c["size"], c["enemy_from"], c["enemy_to"], c["replicates"]) == _dims(c["label"]) + (10,)


def test_settings_overlay_order_base_then_variant_then_cell(tmp_path):
    def mutate(defn):
        variants = (("v", {"A": 1, "B": 2, "OM_TP_PURSUE_BY_STEERING": 5}),)
        cells = []
        for c in defn.cells:
            if c.label == "LA:mirror":
                c = dataclasses.replace(c, settings={"B": 3, "C": 4})
            elif c.label == "LA:choke":
                c = dataclasses.replace(c, settings={"OM_TP_PURSUE_BY_STEERING": 0})
            cells.append(c)
        return dataclasses.replace(defn, variants=variants, cells=tuple(cells))
    _, fake, _ = _run(tmp_path, mutate=mutate)
    got = {c["label"]: c["setup"].settings for c in fake.calls}
    assert got["LA:mirror"] == {"OM_TP_PURSUE_BY_STEERING": 5, "A": 1, "B": 3, "C": 4}
    assert got["LA:choke"] == {"OM_TP_PURSUE_BY_STEERING": 0, "A": 1, "B": 2}


def test_unexpressed_lines():
    d = batches.get("layers")
    joined = " ".join(d.unexpressed)
    assert "tall" in joined and "reach" in joined
    assert "om_roster_set_reach" in joined and "Phase C G5" not in joined
    assert "the LB and LC tables wait for reach" not in d.unexpressed   # test-defect fix: the binding exists
    assert "the choke cells use a sampled wall from maps.sample_map; the Phase B choke scene is its own cell, choke_phase_b" in d.unexpressed
    assert any(REACH_TABLE_TEXT in u for u in d.unexpressed)


def test_scene_text_says_drafts_and_sampled_wall():
    scene = batches.get("layers").scene
    assert "A174" in scene and "Architect" in scene and "not confirmed" in scene
    assert "LB" in scene and "LC" in scene
    assert "sampled wall" in scene
    assert "Phase B choke" in scene and "attack-move" in scene and "8 defenders" in scene


def test_run_file(tmp_path):
    _, _, paths = _run(tmp_path, FakeScan({("body20_range150_ratio7.5", None): 21}))
    t = _text(paths["run"])
    assert t.index(PROVISIONAL) < t.index("## Scene")
    cells = _section(t, "Cells")
    assert all(label in cells for label, _, _ in EXPECTED)
    results = _section(t, "Results")
    line = [ln for ln in results.splitlines() if ln.startswith("- body20_range150_ratio7.5")][0]
    assert "(unconfirmed draft)" in line and "16 units beat 21, lose to 22" in line
    assert sum(ln.startswith("- ") for ln in results.splitlines()) == 73
    sec = _section(t, "What the instrument could not express")
    assert "the LB and LC tables wait for reach" not in sec
    assert REACH_TABLE_TEXT in sec and "the choke cells use a sampled wall from maps.sample_map; the Phase B choke scene is its own cell, choke_phase_b" in sec
    assert "LB:mirror:up1=0.5,up2=0.25" not in sec
    assert "None" not in t


def test_page_and_csv(tmp_path):
    _, _, paths = _run(tmp_path)
    page = _text(paths["page"])
    assert PROVISIONAL in page and page.count("<svg") >= 73
    for label in EXPRESSED:
        assert label in page
    with open(paths["csv"], newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 54 * 17 * 2 + 19 * 6 * 2
    assert {r["cell"] for r in rows} == set(EXPRESSED)
    assert {r["status"] for r in rows} == {DRAFT}


def test_layers_deterministic(tmp_path):
    _, _, a = _run(tmp_path, sub="one")
    _, _, b = _run(tmp_path, sub="two")
    for k in ("csv", "run", "page"):
        assert Path(a[k]).read_bytes() == Path(b[k]).read_bytes(), k
