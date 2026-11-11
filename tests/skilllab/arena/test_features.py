# Rule pins: R-001-06@9f9051, R-001-07@8f31c3
# spec: docs/stories/H-063.md (arena stage 3, the ground pushes back); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn
"""H-063, the layout's features become obstacles for the sim (scripts/skilllab/arena/features.py and run.py).

Story lines proved here (docs/stories/H-063.md):
  "The layout's features become obstacles for the sim. Chokepoint walls (a gap between), city buildings, cover boxes as blocks, a slope band with
   `OM_TP_SLOPE_UP_DIV`, plateau and ridge edges as tier steps on one travel layer (R-001-06 and R-001-07: terrain tiers, not planes)."
  "Tests: a chokepoint fixture blocks units outside the gap: positions never inside a wall box over the fight; positive control: the same fight with the walls
   removed has units inside the box area."
  "Sight stays off (`OM_TP_TARGET_BY_SIGHT` 0), abilities off, engine rules of H-057 (engage on sight, per-type leash). Orders per the two rules (H-052)."
  "Hazard discs and the vantage's second visual band stay drawn only (stage 7)."

Premises dumped (base aac0cd41, 2026-11-02, the stage 2 runner, which ignores `features`): an 8:8 Vanguard fixture, A at x 1000, B at x 3000, default orders, rests at
x 1850/2150 around the midpoint, so a 600 wu rectangle centred on the midpoint holds resting units; fight frames are 100 to 200 ticks apart, so these tests measure
resting positions, never a crossing. The slope fixture (small_tiered, defender on layer 1) in the stage 2 runner stalls at tick 580 with B at x 2593 and moves B
400 wu per 100 ticks across the slope's x range.

Engine expressibility (report): walls, boxes, buildings and ridge rectangles are planar blocks; `Engine.block_rect` (om_map_block_rect, signatures.toml) already
expresses them. The slope band and tier steps need terrain heights: the C side has `om_terrain_set_heights` (ouroboros_sim.h:166) but `scripts/skilllab/engine.py`
binds neither it nor a slope setter, so the builder adds a binding in the harness file engine.py (not a contract change; the story's Files list does not name engine.py).

Runtime (second pass): the fixtures call the arena CLI in-process (h063_fixtures.run), so the engine library builds once per session (13 s) and a fight costs
little; planar runs stop at 20 s of fight (`--cap-seconds 20`, 400 ticks, enough for the resting positions). Fixture headcounts stay 8:8 (H-025 R4 minimum). Rulings used
(H-063 "Rulings for the build", 5, 7 and 8): the runner writes an optional per-frame `blocked` list, the validator accepts it present or absent, feature kinds built
are chokepoint, cover, city, ridge (the flank_route feature's `ridge` rectangle) and slope; plateau and tier steps are not tested; engine.py gains a terrain-heights
binding.

Every test is red today because the runner ignores the features; the `test_control_*` tests are green today and keep a red from being a broken harness."""
import pytest

import h063_fixtures as fx
from scripts.skilllab.catalogue import produce

NAMES = ["chokepoint", "cover", "city", "ridge"]
CAP = ("--cap-seconds", "20")


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Per planar kind: (layout, rects, fight doc with the features, fight doc of the control without them), each run once, seed 1."""
    out = {}
    for name in NAMES:
        lay, rects = fx.planar(name, "L-91%02d" % NAMES.index(name))
        base = tmp_path_factory.mktemp("feat_" + name)
        with_p, with_doc = fx.fight(lay, base / "with", 1, *CAP)
        ctl_p, ctl_doc = fx.fight(fx.without_features(lay), base / "without", 1, *CAP)
        out[name] = (lay, rects, with_p, with_doc, ctl_p, ctl_doc)
    return out


@pytest.mark.parametrize("name", NAMES)
def test_control_fixture_is_legal_and_the_control_fight_has_units_in_the_box_area(name, runs):
    """H-063 Tests: "positive control: the same fight with the walls removed has units inside the box area". CONTROL (green today, and after the build): the
    fixture passes check_layout, the features-emptied twin passes too, runs, and has at least one unit position inside a rectangle of the feature, so a
    feature fight with none inside is the engine's blocking and not a fixture whose units never go there."""
    lay, rects, _, _, ctl_p, ctl_doc = runs[name]
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == []
    assert produce.check_layout(fx.without_features(lay), produce.presets(), produce.rules()) == []
    assert ctl_p.returncode == 0, ctl_p.stdout[-300:] + ctl_p.stderr[-500:]
    assert fx.units_inside(ctl_doc, rects), "premise failed: the control fight never has a unit inside %r" % (rects,)


@pytest.mark.parametrize("name", NAMES)
def test_units_are_never_inside_a_feature_rectangle_over_the_fight(name, runs):
    """H-063 "Chokepoint walls (a gap between), city buildings, cover boxes as blocks ... ridge edges" and Tests "positions never inside a wall box over the fight".
    ISOLATION of features.py: the fight with the features runs (exit 0) and no unit, dead or alive, in any written frame has its centre strictly inside a wall, box,
    building or ridge rectangle of the layout."""
    _, rects, with_p, with_doc, _, _ = runs[name]
    assert with_p.returncode == 0, with_p.stdout[-300:] + with_p.stderr[-500:]
    bad = fx.units_inside(with_doc, rects)
    assert not bad, "units inside the %s rectangles (tick, unit, x, y): %r" % (name, bad[:5])


def test_control_the_gap_of_the_chokepoint_lets_units_through(tmp_path):
    """H-063 "Chokepoint walls (a gap between)". CONTROL (green today, must stay green): B (the attacker, hold:A) starts at x 3000 on the line through the 200 wu
    gap (y 1900 to 2100) and the walls at x 1700 to 2300 stand either side of it; the fight ends decided and B has units west of the walls, so blocking walls must
    not close the gap."""
    walls = [fx.rect(2000, 1650, 600, 500), fx.rect(2000, 2350, 600, 500)]
    feature = {"kind": "chokepoint", "x": 2000.0, "y": 2000.0, "gap": 200, "radius": 600, "walls": walls}
    lay = fx.layout("L-9120", "chokepoint", "small_flat", feature, orders="hold:A")
    proc, doc = fx.fight(lay, tmp_path)
    assert proc.returncode == 0, proc.stdout[-300:] + proc.stderr[-500:]
    assert doc["result"]["winner"] in ("A", "B"), "the attackers never got through the gap: %r" % doc["result"]
    assert any(u["x"] < 1700 and u["side"] == "B" for f in doc["frames"] for u in f["units"]), "no B unit ever west of the walls"


def test_slope_slows_the_climbers(tmp_path):
    """H-063 "a slope band with `OM_TP_SLOPE_UP_DIV`" and "where the geometry slows or stops a unit". Slope fixture: small_tiered, ribbon 600 long and 200 wide along
    +x from band 0 (west) to band 1 (east), side A holds on layer 1 at x 2600, side B on layer 0 at x 1200 attacks over the ribbon (hold:A). At the latest tick both
    fights wrote, the mean x of B's living units with the slope is below the same fight with `features` emptied (a climb at 1 / OM_TP_SLOPE_UP_DIV of the pace)."""
    feature = {"kind": "slope", "x": 2000.0, "y": 2000.0, "length": 600, "width": 200, "heading": 0.0, "from_band": 0, "to_band": 1}
    lay = fx.layout("L-9121", "slope", "small_tiered", feature, orders="hold:A", a_layer=1, ax=2600.0, bx=1200.0)
    lay["side_b"]["units"] = fx.block(8, 1200.0, 2000.0, 0.0)   # B west of the ribbon, facing east
    for u in lay["side_a"]["units"]:
        u["facing"] = 3.1416
    p1, d1 = fx.fight(lay, tmp_path / "slope", 1, *CAP)
    p2, d2 = fx.fight(fx.without_features(lay), tmp_path / "flat", 1, *CAP)
    assert p1.returncode == 0 and p2.returncode == 0, (p1.stdout + p1.stderr)[-500:] + (p2.stdout + p2.stderr)[-500:]
    ticks = sorted({f["tick"] for f in d1["frames"]} & {f["tick"] for f in d2["frames"]} - {0})
    assert ticks, "premise failed: no common frame tick between the slope and the control fight"
    t = [x for x in ticks if x <= 400][-1]
    mean_b = lambda doc: (lambda xs: sum(xs) / len(xs))([u["x"] for f in doc["frames"] if f["tick"] == t for u in f["units"] if u["side"] == "B" and u["alive"]])
    assert mean_b(d1) < mean_b(d2) - 1.0, "tick %d: B mean x with the slope %.1f is not below the flat control %.1f" % (t, mean_b(d1), mean_b(d2))


def test_features_module_maps_a_layout_to_engine_blocking_calls():
    """H-063 Files "`scripts/skilllab/arena/features.py` (new: layout features to engine blocking calls)". The module exists and run.py imports it (the isolation
    of the new system is test_units_are_never_inside_a_feature_rectangle_over_the_fight; this is the wiring: reachable from the runner, not only from tests)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[3] / "scripts" / "skilllab" / "arena"
    assert (root / "features.py").exists(), "scripts/skilllab/arena/features.py is missing"
    text = (root / "run.py").read_text()
    assert "arena.features" in text or "arena import features" in text or "import features" in text, "run.py does not import arena/features.py"


def test_control_engine_binds_the_terrain_band_query_today():
    """H-063 ruling 8 control (green today): engine.py already binds `om_terrain_band_at`, so the red test below is the missing heights binding."""
    from pathlib import Path
    text = (Path(__file__).resolve().parents[3] / "scripts" / "skilllab" / "engine.py").read_text()
    assert '"om_terrain_band_at"' in text


def test_engine_binds_the_terrain_heights_setter():
    """H-063 Files "`scripts/skilllab/engine.py` (terrain heights binding for the slope)" and ruling 8: "`scripts/skilllab/engine.py` gains the harness binding
    (`om_terrain_set_heights` or the slope setter the engine exposes), no contract change". The signature table names `om_terrain_set_heights` (ouroboros_sim.h:166) and
    an Engine method calls it."""
    from pathlib import Path
    text = (Path(__file__).resolve().parents[3] / "scripts" / "skilllab" / "engine.py").read_text()
    assert '"om_terrain_set_heights"' in text, "no signature entry for om_terrain_set_heights in scripts/skilllab/engine.py"
    assert "self._lib.om_terrain_set_heights(" in text, "no Engine method calls om_terrain_set_heights"


def test_runner_writes_blocked_per_frame_for_the_gap_queue(runs):
    """H-063 "a marker on units blocked for more than 2 s: the first-contact queue at a gap" and ruling 5: "the runner writes an optional per-frame `blocked` list (unit
    rows blocked more than 2 s, judged at sample ticks) into the fight file". The ridge fight has `blocked` on every frame, a list of ints, and at some
    frame it is not empty (units stall at the ridge). CONTROL half: the features-emptied twin has no blocked unit in any frame (absent or empty), so the marker is the
    ground's.
    Test-defect (engine rule fixes F1 to F4, 2026-11-11): the chokepoint and cover fights no longer list a unit blocked (measured: 0 on every frame, seed 1, cap 60 s, sight on
    and off), because a unit that halts at the walls now holds its lock on an enemy and fires, and `blocked` counts only units with no target. The ridge fixture (one wall
    across the field, small_tiered) still stalls targetless units (6 on the frames at 300 and 400 ticks), so the marker is proved there."""
    _, _, with_p, with_doc, _, ctl_doc = runs["ridge"]
    assert with_p.returncode == 0, with_p.stdout[-300:] + with_p.stderr[-500:]
    frames = with_doc["frames"]
    assert all(isinstance(f.get("blocked"), list) and all(isinstance(i, int) for i in f["blocked"]) for f in frames), "a frame has no int list `blocked`"
    assert any(f["blocked"] for f in frames), "no unit is ever listed blocked at the ridge"
    assert not any(f.get("blocked") for f in ctl_doc["frames"]), "the no-features control lists blocked units"


def test_fight_file_validator_accepts_blocked_present_or_absent():
    """H-063 ruling 5: "additive and optional, schema name `om-fight-2` unchanged ... the validator accepts it absent or present", and Files "`SNAPSHOT.md` (optional
    `blocked`)". CONTROL half (green today): the example document without `blocked` validates. Red half: a frame carrying `blocked: [1]` validates too, the schema name is
    still om-fight-2, and SNAPSHOT.md documents the key."""
    from pathlib import Path
    from scripts.skilllab.arena import snapshot
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    assert snapshot.validate(doc) == []
    doc["frames"][1]["blocked"] = [doc["frames"][1]["units"][0]["id"]]
    assert snapshot.validate(doc) == []
    assert doc["schema"] == "om-fight-2"
    assert "blocked" in (Path(__file__).resolve().parents[3] / "scripts" / "skilllab" / "arena" / "SNAPSHOT.md").read_text()
