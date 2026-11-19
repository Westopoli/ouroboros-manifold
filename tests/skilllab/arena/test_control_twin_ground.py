# spec: docs/northstar/plans/engine-rules-2026-11-08/round6.md (L6); docs/stories/H-063.md (the ground control); DEC-stage3-layouts-2026-11-05
"""Round 6, L6 (part two): a ground control stands on the ground it is given.

round6.md L6: "the ground control of L-0084 (the layout with its features emptied, `run.control_twin`) ends at tick 820 with 40 against 56 alive and not one shot fired. The twin keeps side A on
layer 1 and side B on layer 0 while the slope that joined the two layers is gone; with sight off every role's reach is (0,0) ... A control in which no shot can be fired measures nothing. Built: the
twin's units stand on the layer the featureless ground has under them (every unit of a twin whose ground is flat is on one layer), and the twin's file says which units' layers were changed. A layout
whose sides are on different layers by design and not by a feature the twin removes (none in the standing set today) is left as it is and reported by the regression command as a control that cannot
fight. Tests first: the twin of L-0084 has both sides on one layer and its fight ends by elimination or `apart`; the twins of L-0055, L-0073 and L-0039, whose units are already on one layer, are
byte-identical to today's; the pinned stage 3 control fight files that do not change are byte-identical."

WHAT THIS FILE PINS (the lab builder builds to it; the names are the test writer's):
  the ground's layer   as the lab asks the engine for it (`hills.ground_layer`: the terrain band of the cell at (x, y), less one), read in the twin's own world (`run._ground_world(twin, "off")`)
                       and not below layer 0: the twin has no features, so no terrain is laid, the engine reads band 0 everywhere and the ground is layer 0 for every unit (measured 2026-11-19).
                       The test reads it through the engine and not as the number 0, so a ground that is not layer 0 would be followed.
  twin["layers_changed"]  NEW key of the twin `run.control_twin` returns, and so of `<id>-control.json` (the JSON is `json.dumps(twin, indent=2)`): the list of the units whose layer was changed, each as
                       the string "side_a unit 3" / "side_b unit 0" (side key and index in that side's `units`, as `run.layer_mismatch` names a unit), in side A then side B, index order. The key is
                       absent when no unit changed (that keeps a twin that has nothing to change byte-identical to today's). The TOML (`dump_toml`) is not pinned to carry it. Only `layer` of a unit
                       changes: its role, x, y and facing stay as the layout has them, and the layout dict handed to `control_twin` is not edited.
  the twin's fight     `run.fight` / `run._document` at sight off, seed 1, the cap `snapshot.CAP_SECONDS`: at least one shot fired (a unit's hit points lower than at the start, or a unit dead) and the
                       end `wipe` or `apart` (L5), never `silence` with both alive. Red today: the twin ends `silence` at tick 820 with 40:56 and no shot.
  the twins of L-0055, L-0073 and L-0039   their `<id>-control.toml` and `<id>-control.json` as `control_twin` writes them today, pinned by sha256 (taken from this branch's engine rules Round 6 part-one
                       tip, 2026-11-19); no `layers_changed` key. Green today.
  a control that cannot fight   a planted layout on the terraced landscape `small_tiered` whose only feature is a planar `cover` box (a feature the twin removes) and whose sides are on different layers
                       by design (side A on layer 1, side B on layer 0): the box is not terrain, so no ground the twin lays gives A a different layer. The twin is left as it is (the layout with `features` emptied
                       and `movement` "walk", every unit's layer as the layout has it, no `layers_changed`, its two files as `control_twin` writes them today) and the regression command, given a stage 3 row
                       for it (control `ground`, sight off), prints for the control (a line that starts with `<id>-control`) a line that contains the words `cannot fight` and no `end=` key, and does not
                       run the control: `run.fight` is called once, for the row's own fight. The exit code is not pinned.
                       (Assumption, for the builder to correct if wrong: this planted layout is what L6 calls "sides on different layers by design and not by a feature the twin removes".)
Every test names L6 and DEC-stage3-layouts-2026-11-05."""
import hashlib
import json
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import h063_fixtures as fx  # noqa: E402
from scripts.skilllab.arena import hills, run, snapshot  # noqa: E402
from scripts.skilllab.catalogue import produce  # noqa: E402
from test_regression_manifest import _by_name, _control_row, _main, _manifest_file  # noqa: E402

CATALOGUE = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
FIELD = "layers_changed"

# sha256 of (<id>-control.toml, <id>-control.json) as `run.control_twin` writes them from the catalogue layout today (this branch, 2026-11-19).
TWIN_BYTES = {
    "L-0055": ("1c018e25c9e64c235e1109380b53ff30b901568eb0de44f411a5014853d6309f", "0abbee86de09847fa62daa733d6545b39053bfbd8a288f545852b2185af8cc40"),
    "L-0073": ("ca5fa1e32101e0650bd5db0963bbdea0ade6b4725de2fff19252c74a27a274d4", "2aaa691e2a562ef909f987736a6dde16e61babea6dfe339a2f3020a1df8ca119"),
    "L-0039": ("ce33d2ecb2bc506789c91acd5d6e9f2cce251628bf643c960eba4e1162c978ff", "d33eb798677ef0f573de200575e33858c2471c0dd250761a5a39f9f56cef3bdb"),
}


def load(lid):
    path = CATALOGUE / (lid + ".toml")
    with open(path, "rb") as f:
        return tomllib.load(f), path


def twin_of(lid, tmp_path):
    layout, path = load(lid)
    twin, twin_path = run.control_twin(layout, str(path), tmp_path / "control")
    return layout, twin, Path(twin_path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ground_layers(twin):
    """[(side key, index, the layer the twin's featureless ground gives that unit)]: `hills.ground_layer` in the twin's own world, not below layer 0 (module docstring)."""
    engine, w, _ = run._ground_world(twin, "off")
    try:
        return [(key, i, max(0, hills.ground_layer(engine, w, u["x"], u["y"]))) for key in ("side_a", "side_b") for i, u in enumerate(twin[key]["units"])]
    finally:
        engine.free_world(w)


def test_L6_the_ground_twin_of_L_0084_has_every_unit_on_the_layer_the_featureless_ground_gives(tmp_path):
    """L6 "the twin's units stand on the layer the featureless ground has under them (every unit of a twin whose ground is flat is on one layer)": L-0084 (a slope; side A's 40 units on layer 1, side
    B's 56 on layer 0): in its twin every unit of both sides is on the layer the engine gives the ground under it (`ground_layers`), all on one layer, and only `layer` of a unit has changed (role,
    x, y, facing as the layout has them); the layout dict handed in is not edited. Red today: side A stays on layer 1."""
    layout, twin, _ = twin_of("L-0084", tmp_path)
    assert twin is not None and twin["features"] == []
    ground = ground_layers(twin)
    assert len(ground) == 96 and len({g for *_, g in ground}) == 1, "the featureless ground is flat: one layer for every unit, got %s" % sorted({g for *_, g in ground})
    for key, i, g in ground:
        assert twin[key]["units"][i]["layer"] == g, (key, i, twin[key]["units"][i]["layer"], g)
    for key in ("side_a", "side_b"):
        for mine, theirs in zip(twin[key]["units"], layout[key]["units"]):
            assert {k: v for k, v in mine.items() if k != "layer"} == {k: v for k, v in theirs.items() if k != "layer"}
    assert {u["layer"] for u in layout["side_a"]["units"]} == {1} and {u["layer"] for u in layout["side_b"]["units"]} == {0}, "control_twin edited the layout it was given"


def test_L6_the_twin_file_of_L_0084_names_the_units_whose_layer_was_changed(tmp_path):
    """L6 "the twin's file says which units' layers were changed": the twin of L-0084 carries `layers_changed` (module docstring): the 40 units of side A ("side_a unit 0" to "side_a unit 39", in order) and
    none of side B (they already stand on the ground's layer); `<id>-control.json` is `json.dumps(twin, indent=2)` plus a newline, as today, so it carries the same list. Red today: no key."""
    layout, twin, path = twin_of("L-0084", tmp_path)
    assert twin.get(FIELD) == ["side_a unit %d" % i for i in range(40)], twin.get(FIELD)
    on_disk = json.loads(path.with_suffix(".json").read_text())
    assert on_disk[FIELD] == twin[FIELD] and path.with_suffix(".json").read_text() == json.dumps(twin, indent=2) + "\n"
    assert tomllib.loads(path.read_text())["side_a"]["units"][0]["layer"] == twin["side_a"]["units"][0]["layer"], "the TOML the control fight is read from must carry the changed layers"


def test_L6_the_ground_twin_fight_of_L_0084_fires_shots_and_ends_by_elimination_or_apart(tmp_path):
    """L6 "the twin of L-0084 has both sides on one layer and its fight ends by elimination or `apart`" and "A control in which no shot can be fired measures nothing": the twin's fight (sight off, seed 1,
    the stage 3 cap), as the regression command runs it: the document validates, the end is `wipe` or `apart` (never `silence` with both sides alive, never the cap), and shots were fired: some unit's
    hit points are lower in the last frame than in the first, or a unit has died. Red today: the end is `silence` at tick 820, 40 against 56 alive, no hit point lost."""
    _, twin, path = twin_of("L-0084", tmp_path)
    frames, last, end, orders = run.fight(twin, 1, "off", snapshot.CAP_SECONDS)
    doc = run._document(twin, str(path), 1, "off", frames, last, end, orders)
    res = doc["result"]
    assert res["end"] in ("wipe", "apart") and res["capped"] is False, res
    first, final = {u["id"]: u["hp"] for u in doc["frames"][0]["units"]}, doc["frames"][-1]["units"]
    assert any(u["hp"] < first[u["id"]] or not u["alive"] for u in final), "no shot was fired in the twin's fight: %s" % res
    assert snapshot.validate(doc) == [], snapshot.validate(doc)


@pytest.mark.parametrize("lid", sorted(TWIN_BYTES))
def test_L6_the_twins_whose_units_already_stand_on_one_layer_are_byte_identical_to_todays(lid, tmp_path):
    """L6 "the twins of L-0055, L-0073 and L-0039, whose units are already on one layer, are byte-identical to today's": their `<id>-control.toml` and `<id>-control.json` hash to the digests taken from
    `control_twin` before the build (TWIN_BYTES), and the twin has no `layers_changed` key. Green today and must stay green."""
    layout, twin, path = twin_of(lid, tmp_path)
    assert FIELD not in twin
    assert {u["layer"] for key in ("side_a", "side_b") for u in layout[key]["units"]} == {0}
    assert (sha(path), sha(path.with_suffix(".json"))) == TWIN_BYTES[lid]


def terraced_cover_layout(lid="L-9301"):
    """The planted layout of the module docstring: `small_tiered`, one planar `cover` box between two blocks of eight Vanguards, side A on layer 1 and side B on layer 0 by design."""
    _, _, feature, _, yc = fx.KINDS["cover"]()
    return fx.layout(lid, "cover", "small_tiered", feature, yc=yc, a_layer=1)


def test_L6_a_twin_whose_sides_stand_on_different_layers_by_design_is_left_as_it_is(tmp_path):
    """L6 "A layout whose sides are on different layers by design and not by a feature the twin removes ... is left as it is": the planted terraced `cover` layout (module docstring): its twin is the
    layout with `features` emptied and `movement` "walk" and nothing else (every unit's layer as the layout has it: side A on 1, side B on 0), carries no `layers_changed`, and its two files are what
    `control_twin` writes today (`dump_toml(twin)` and `json.dumps(twin, indent=2)` plus a newline). Green today and must stay green."""
    layout = terraced_cover_layout()
    assert produce.check_layout(layout, produce.presets(), produce.rules()) == []
    twin, path = run.control_twin(layout, "L-9301.toml", tmp_path / "control")
    assert twin == {**layout, "features": [], "movement": "walk"} and FIELD not in twin
    assert {u["layer"] for u in twin["side_a"]["units"]} == {1} and {u["layer"] for u in twin["side_b"]["units"]} == {0}
    assert Path(path).read_text() == produce.dump_toml(twin) and Path(path).with_suffix(".json").read_text() == json.dumps(twin, indent=2) + "\n"


def test_L6_the_regression_command_reports_that_control_as_one_that_cannot_fight_and_does_not_run_it(tmp_path, monkeypatch):
    """L6 "reported by the regression command as a control that cannot fight": a stage 3 row (control `ground`, sight off, expected draw) for the planted terraced `cover` layout. The command prints
    its two lines: the fight's (it runs: the first `run.fight` call), and then a line that starts with `L-9301-control` and contains the words `cannot fight` and no `end=` key (nothing ran for it):
    `run.fight` is called exactly once. The exit code is not pinned. Red today: the control runs and its line carries `end=`."""
    catalogue = tmp_path / "catalogue"
    fx.write(terraced_cover_layout(), catalogue)
    real, calls = run.fight, []

    def fight(layout, seed, sight, cap_seconds, *args, **kwargs):
        calls.append(layout["id"])
        return real(layout, seed, sight, cap_seconds, *args, **kwargs)
    monkeypatch.setattr(run, "fight", fight)
    _, out = _main(_manifest_file(tmp_path, _control_row("L-9301", "draw", "off", "ground", 3)), catalogue)
    lines = _by_name(out)
    assert "L-9301" in lines and "L-9301-control" in lines, out
    control = lines["L-9301-control"]
    assert "cannot fight" in control and "end=" not in control, control
    assert calls == ["L-9301"], "the control was run: %s" % calls
