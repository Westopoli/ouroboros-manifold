# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-3
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-01, criteria 3 to 6 (spec lines 27 to 30): the control twin, the fight document's `landscape` and `movement_kind`, the `blocked` column.

3: `control_twin(layout, layout_path, control_dir)` returns `({**layout, "features": [], "movement": "walk"}, twin_path)` for a bound layout, `(None, None)` otherwise;
   `fight()` calls `features.walk_on_ground` when `apply` returned True or `layout.get("movement") == "walk"`; `movement_kind` 1 in a walking fight's document.
4: the twin files `<id>-control.toml` and `<id>-control.json` beside the control fight; the control document's `layout_path` is the TOML.
5: `landscape` and `movement_kind` on `om-fight-2` through `snapshot.validate`.
6: `results.md` gains the final column `blocked`."""
import copy
import json
import shutil
import tempfile
import tomllib
from pathlib import Path

import pytest

import h063_fixtures as fx
from scripts.skilllab.arena import features, run as arena_run, snapshot
from scripts.skilllab.catalogue import produce

HEAD = "| id | a:b | predict | winner | survivors | ticks | agree | blocked |"


def open_field(lid):
    return fx.layout(lid, "open_field", "small_flat", None)


# ---------------------------------------------------------------- criterion 3 and 4: control_twin

@pytest.mark.parametrize("kind", ["chokepoint", "cover", "city", "ridge"])
def test_control_twin_of_a_bound_layout_is_the_walking_layout_without_features(kind, tmp_path):
    """Criterion 3, all four planar kinds: the twin is `{**layout, "features": [], "movement": "walk"}` and the returned path is `<control_dir>/<id>-control.toml`;
    the argument layout is not changed."""
    lay, _ = fx.planar(kind, "L-9320")
    before = copy.deepcopy(lay)
    assert features.bound(lay)
    twin, path = arena_run.control_twin(lay, str(tmp_path / "L-9320.toml"), tmp_path / "control")
    assert twin == {**before, "features": [], "movement": "walk"}
    assert lay == before
    assert Path(path) == tmp_path / "control" / "L-9320-control.toml"


@pytest.mark.parametrize("make", [lambda: open_field("L-9321"), lambda: {**open_field("L-9321"), "features": []},
                                  lambda: {**open_field("L-9321"), "features": [{"kind": "ring", "x": 2000.0, "y": 2000.0, "radius": 400}]}],
                         ids=["no-features-key", "empty-features", "feature-the-engine-is-not-given"])
def test_control_twin_of_an_unbound_layout_is_none_and_writes_nothing(make, tmp_path):
    """Criterion 3: "else `(None, None)` is returned" when `features.bound(layout)` is false (Existence: no key, an empty list, a kind `apply` hands the engine
    nothing for). Nothing is written."""
    lay = make()
    assert not features.bound(lay)
    control = tmp_path / "control"
    control.mkdir()
    assert arena_run.control_twin(lay, str(tmp_path / "L-9321.toml"), control) == (None, None)
    assert list(control.iterdir()) == []


def test_control_twin_writes_the_toml_and_json_the_way_write_layout_does(tmp_path):
    """Criterion 4: `<control-dir>/<id>-control.toml` is `produce.dump_toml(twin)`, `<id>-control.json` is `json.dumps(twin, indent=2)`; the TOML parses, carries the
    id and no feature; the JSON has `features == []` and `movement == "walk"`."""
    lay, _ = fx.planar("chokepoint", "L-9322")
    control = tmp_path / "control"
    control.mkdir()
    twin, path = arena_run.control_twin(lay, str(tmp_path / "L-9322.toml"), control)
    assert sorted(p.name for p in control.iterdir()) == ["L-9322-control.json", "L-9322-control.toml"]
    text = Path(path).read_text()
    assert text == produce.dump_toml(twin)
    parsed = tomllib.loads(text)
    assert parsed["id"] == "L-9322" and not parsed.get("features")
    raw = (control / "L-9322-control.json").read_text()
    assert json.loads(raw) == twin and raw.startswith('{\n  "'), "the JSON is written with indent=2"
    assert json.loads(raw)["features"] == [] and json.loads(raw)["movement"] == "walk"


# ---------------------------------------------------------------- criterion 3: fight() calls walk_on_ground (composition)

def _walk_calls(lay, monkeypatch):
    calls = []
    real = features.walk_on_ground
    monkeypatch.setattr(features, "walk_on_ground", lambda engine, w, types: (calls.append(sorted(types)), real(engine, w, types))[1])
    arena_run.fight(lay, 1, "off", 2)
    return calls


def test_fight_calls_walk_on_ground_for_a_layout_marked_movement_walk_without_features(monkeypatch):
    """Criterion 3, spec line 27: "`fight()` calls `features.walk_on_ground` when `features.apply` returned True or `layout.get("movement") == "walk"`": an open field
    (nothing applied) with `movement: "walk"`, the shape of the control twin, still walks."""
    lay = open_field("L-9323")
    lay["movement"] = "walk"
    assert len(_walk_calls(lay, monkeypatch)) == 1


@pytest.mark.parametrize("with_features,movement,called", [(True, None, True), (True, "walk", True), (False, None, False), (False, "fly", False)],
                         ids=["applied", "applied-and-walk", "flies", "movement-fly"])
def test_control_walk_on_ground_is_unchanged_for_the_other_combinations(with_features, movement, called, monkeypatch):
    """CONTROL (green today, must stay green): features applied -> called once; nothing applied and no movement key, or any movement other than the literal "walk"
    (L27 `== "walk"`) -> not called, the units fly."""
    lay = fx.planar("chokepoint", "L-9323")[0] if with_features else open_field("L-9323")
    if movement:
        lay["movement"] = movement
    assert len(_walk_calls(lay, monkeypatch)) == (1 if called else 0)


def test_the_control_twin_made_by_control_twin_walks_in_fight(tmp_path, monkeypatch):
    """Criterion 3, composition of `control_twin` and `fight`: the chokepoint's twin has empty features (nothing applied) yet `fight()` calls `walk_on_ground` for it,
    so the control walks."""
    lay, _ = fx.planar("chokepoint", "L-9324")
    twin, _ = arena_run.control_twin(lay, str(tmp_path / "L-9324.toml"), tmp_path)
    assert twin["features"] == []
    calls = []
    real = features.walk_on_ground
    monkeypatch.setattr(features, "walk_on_ground", lambda engine, w, types: (calls.append(1), real(engine, w, types))[1])
    arena_run.fight(twin, 1, "off", 2)
    assert calls == [1]


# ---------------------------------------------------------------- criteria 3, 4, 5: the documents through the CLI

def _fight_with_control(tmp_path, lay=None, *extra):
    lay = lay or fx.planar("chokepoint", "L-9301")[0]
    control = tmp_path / "control"
    proc, doc = fx.fight(lay, tmp_path, 1, "--cap-seconds", "5", "--control-dir", control, *extra)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return lay, control, doc, snapshot.read(control / ("%s-control-s1.fight.json" % lay["id"]))


def test_main_and_control_documents_carry_movement_kind_and_landscape(tmp_path):
    """Criteria 3 and 5, spec lines 27 and 29: on the chokepoint fixture both documents carry `movement_kind` 1; every document carries `landscape`, the layout's
    preset name; the control has the same units as the main fight at frame 0."""
    lay, _, doc, control = _fight_with_control(tmp_path)
    assert doc["movement_kind"] == 1 and control["movement_kind"] == 1
    assert doc["landscape"] == control["landscape"] == lay["landscape"] == "small_flat"
    assert [u["id"] for u in doc["frames"][0]["units"]] == [u["id"] for u in control["frames"][0]["units"]]


def test_a_flying_fight_omits_movement_kind_but_still_names_its_landscape(tmp_path):
    """Criterion 3, "a fight whose units fly omits the key", and criterion 5: the open-field fixture flies, `landscape` is written, `movement_kind` is absent."""
    proc, doc = fx.fight(open_field("L-9325"), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "movement_kind" not in doc
    assert doc["landscape"] == "small_flat"


def test_the_tiered_landscape_is_named_in_the_slope_fight(tmp_path):
    """Criterion 5: `landscape` is the layout's preset name, `small_tiered` for the slope fixture (not a constant)."""
    from test_stage3_reach import slope_layout
    proc, doc = fx.fight(slope_layout("L-9326"), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert doc["landscape"] == "small_tiered" and doc["movement_kind"] == 1


def test_control_dir_holds_the_twin_files_and_the_control_names_its_twin(tmp_path):
    """Criterion 4: after `--control-dir` the two twin files exist, the JSON has `features == []`, and the control document's `layout_path` ends `<id>-control.toml`
    and names an existing file (the TOML)."""
    lay, control_dir, _, control = _fight_with_control(tmp_path)
    assert (control_dir / "L-9301-control.toml").is_file()
    twin = json.loads((control_dir / "L-9301-control.json").read_text())
    assert twin["features"] == [] and twin["id"] == "L-9301"
    assert control["layout_path"].endswith("L-9301-control.toml")
    assert Path(control["layout_path"]).resolve() == (control_dir / "L-9301-control.toml").resolve()


def test_control_layout_path_is_repository_relative_under_the_repository():
    """Criterion 4: "repository-relative when under the repository, as `_document` does today": a control dir inside the repository gives a relative `layout_path`."""
    scratch = Path(tempfile.mkdtemp(prefix="stage3-ctl-", dir=fx.ROOT))
    try:
        _, control_dir, doc, control = _fight_with_control(scratch)
        want = (control_dir / "L-9301-control.toml").resolve().relative_to(fx.ROOT.resolve()).as_posix()
        assert control["layout_path"] == want
        assert not Path(control["layout_path"]).is_absolute()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_fight_files_and_twin_files_are_byte_identical_on_a_rerun(tmp_path):
    """Constraints (spec line 15): same layout, seed and flags give byte-identical fight files; the twin files are part of the output."""
    seen = []
    for _ in range(2):   # the same directory twice: a fight file carries its layout's path, so a second directory would differ by design
        _, control_dir, _, _ = _fight_with_control(tmp_path)
        seen.append([p.read_bytes() for p in sorted(control_dir.iterdir())] + [p.read_bytes() for p in sorted((tmp_path / "out").glob("*.fight.json"))])
    assert len(seen[0]) == 4 and seen[0] == seen[1]


# ---------------------------------------------------------------- criterion 5: snapshot.validate

def _v2(**extra):
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    doc.update(extra)
    return doc


def test_control_v2_without_the_new_keys_still_validates():
    """CONTROL (green today, must stay green): an om-fight-2 document with neither key is valid, so the key is optional."""
    assert snapshot.validate(_v2()) == []


def test_validate_accepts_landscape_and_movement_kind_on_v2_present_or_absent():
    """Criterion 5, spec line 29: `landscape` (a string) and `movement_kind` (the int 1) are accepted on `om-fight-2`, together or alone."""
    assert snapshot.validate(_v2(landscape="small_tiered", movement_kind=1)) == []
    assert snapshot.validate(_v2(landscape="small_flat")) == []
    assert snapshot.validate(_v2(movement_kind=1)) == []


@pytest.mark.parametrize("key,value", [("landscape", "small_flat"), ("movement_kind", 1)])
def test_validate_rejects_the_keys_on_a_v1_document_naming_the_key(key, value):
    """CONTROL (green today: the key is unknown to every schema): criterion 5, "still rejects them on `om-fight-1`", the message naming the key. Must stay green."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA)
    assert snapshot.validate(doc) == []
    doc[key] = value
    errors = snapshot.validate(doc)
    assert errors and any(key in e for e in errors), errors


def test_a_written_v2_document_with_both_keys_reads_back(tmp_path):
    """Criterion 5: `snapshot.write` then `snapshot.read` (which validates) round-trips a document carrying both keys."""
    path = tmp_path / "x.fight.json"
    snapshot.write(_v2(landscape="small_tiered", movement_kind=1), path)
    got = snapshot.read(path)
    assert got["landscape"] == "small_tiered" and got["movement_kind"] == 1


# ---------------------------------------------------------------- criterion 6: results.md

def _rows(out):
    lines = (Path(out) / "results.md").read_text().splitlines()
    return lines[0], lines[1], [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[2:]]


def test_results_md_has_the_blocked_column_counting_the_frames_blocked_units(tmp_path):
    """Criterion 6, spec line 30: the header is `HEAD`, a fight with ground gets a final integer cell equal to the sum over its frames of `len(frame["blocked"])`
    (computed here from the fight file), a fight with no `blocked` key gets 0; the header is written once for two runs into one results.md.
    The cover fixture stalls with blocked units (premise asserted: the sum is above 0, so a count of 0 would be a wrong cell and not a quiet fixture)."""
    cover = fx.planar("cover", "L-9327")[0]
    proc, doc = fx.fight(cover, tmp_path, 1, "--cap-seconds", "60")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    want = sum(len(f.get("blocked", [])) for f in doc["frames"])
    assert want > 0, "fixture premise: the cover fight has blocked unit-frames"
    proc, field_doc = fx.fight(open_field("L-9328"), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert all("blocked" not in f for f in field_doc["frames"])
    head, sep, rows = _rows(tmp_path / "out")
    assert head == HEAD
    assert sep.count("---") == 8
    assert [r[0] for r in rows] == ["L-9327", "L-9328"] and all(len(r) == 8 for r in rows)
    assert rows[0][7] == str(want) and rows[1][7] == "0"
