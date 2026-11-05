# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-1
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-01, criterion 1 (and 2 as a limit that must still hold): the reachability route check runs on the engine's rules, through the real engine.

`features.first_unreachable(engine, w, layout, preset, point, sides)` builds a 50 wu grid (NAV_CELL): every `_engine_boxes` rectangle rounded out to whole cells
(`floor(lo / 50)` to `ceil(hi / 50) - 1`), and for a slope the engine's walk mask (union over the preset's layers, DRAFT-reach-mask-union). Spec lines 21 to 23.

Geometry note: the chokepoint walls here run from the field edge to the gap (y 0 to the inner edge, inner edge to 4000), so the gap is the only way through; the
short walls of the shared fixture can be walked around and would never reject. The gap sizes follow from the rounding rule: a gap whose inner edges (y1, y2) round
out to whole 50 wu cells is shut when no whole cell lies between them."""
import pytest

import h063_fixtures as fx
from scripts.skilllab.arena import features, run as arena_run
from scripts.skilllab.catalogue import produce
from scripts.skilllab.engine import Engine

FIELD = 4000.0
SLOPE_FEATURE = {"kind": "slope", "x": 2000.0, "y": 2000.0, "length": 600, "width": 200, "heading": 0.0, "from_band": 0, "to_band": 1}


def gap_layout(lid, gap, orders="hold:A"):
    """Chokepoint on small_flat: walls x 1700 to 2300 from the field edges to the gap, inner edges at 2000 -/+ gap/2."""
    lo, hi = fx.YC - gap / 2, fx.YC + gap / 2
    walls = [fx.rect(2000, lo / 2, 600, lo), fx.rect(2000, (hi + FIELD) / 2, 600, FIELD - hi)]
    feature = {"kind": "chokepoint", "x": 2000.0, "y": fx.YC, "gap": gap, "radius": 600, "walls": walls}
    return fx.layout(lid, "chokepoint", "small_flat", feature, orders=orders)


def grid_units(n, x0, layer, per_row=3, y0=1960.0):
    return [{"role": "Vanguard", "x": x0 + (i % per_row) * 40.0, "y": y0 + (i // per_row) * 40.0, "facing": 0.0, "layer": layer} for i in range(n)]


def slope_layout(lid, b_overrides=None):
    """SLOPE_FIXTURE of the spec: small_tiered, hold:A, A on layer 1 at x 2480 to 2560, B on layer 0 at x 1000 to 1080, y 1960 to 2040. `b_overrides` {index: (x, y)}."""
    lay = fx.layout(lid, "slope", "small_tiered", dict(SLOPE_FEATURE), orders="hold:A")
    lay["side_a"] = {"headcount": 8, "units": grid_units(8, 2480.0, 1)}
    lay["side_b"] = {"headcount": 8, "units": grid_units(8, 1000.0, 0)}
    for i, (x, y) in (b_overrides or {}).items():
        lay["side_b"]["units"][i].update(x=x, y=y)
    return lay


def ring(cx, cy):
    """Four 40 wu strips round a 200 wu square: a closed pen whose inside survives the 50 wu rounding (two whole open cells a side at least)."""
    return [fx.rect(cx, cy - 120, 280, 40), fx.rect(cx, cy + 120, 280, 40), fx.rect(cx - 120, cy, 40, 280), fx.rect(cx + 120, cy, 40, 280)]


def centroid(lay, side):
    pts = lay[side]["units"]
    return sum(u["x"] for u in pts) / len(pts), sum(u["y"] for u in pts) / len(pts)


def reach(lay, sides=("side_b",), point=None, seed=1, tweak=None):
    """first_unreachable on a world with the layout applied (spec 1: `w` is a world on which apply has run). Default point: side A's centroid (orders hold:A)."""
    engine = Engine()
    if tweak:
        tweak(engine)
    w = engine.new_world(seed)
    try:
        preset = produce.presets()[lay["landscape"]]
        features.apply(engine, w, lay, preset, seed)
        return features.first_unreachable(engine, w, lay, preset, point or centroid(lay, "side_a"), sides)
    finally:
        engine.free_world(w)


# ---------------------------------------------------------------- controls: the fixtures are legal layouts

def test_control_fixtures_pass_check_layout():
    """CONTROL (green today): the gap, touching-walls and slope fixtures are legal layouts (R1 to R7), so a REJECT below is the route check and not a bad fixture."""
    pre, rul = produce.presets(), produce.rules()
    for gap in (0, 60, 200):
        assert produce.check_layout(gap_layout("L-9300", gap), pre, rul) == [], "gap %d" % gap
    assert produce.check_layout(slope_layout("L-9301"), pre, rul) == []
    assert produce.check_layout(slope_layout("L-9301", {3: (2000.0, 1500.0)}), pre, rul) == []


# ---------------------------------------------------------------- (a) and (b): planar blocks on the 50 wu grid

@pytest.mark.parametrize("gap,rejected", [(0, True), (60, True), (80, True), (100, False), (200, False)])
def test_planar_gap_follows_the_engines_50wu_rounding(gap, rejected):
    """Criterion 1 (a) and (b), spec lines 21 and 22. Gap 0 is walls touching (b), 60 is the spec's own example (inner edges 1970 and 2030: today's 20 wu grid lets it
    through, the engine's rounding shuts it), 200 is the open control. Gap 80 (edges 1960 and 2040) is shut by the rule too (the walls round out to cells ending and starting at 2000), gap 100 (edges 1950 and 2050) keeps two whole cells open. B attacks (hold:A), so the first B unit is named."""
    got = reach(gap_layout("L-9302", gap))
    assert got == ("side_b unit 0" if rejected else None), "gap %d wu: %r" % (gap, got)


def test_unit_pen_is_rejected_and_names_the_unit_in_row_order():
    """Criterion 1: "the first-unit naming (`side_a` rows first, then `side_b`) are as today". A unit of each side in its own closed pen: both sides asked, the line
    names side A's unit 5; only side B asked, it names side B's unit 0."""
    lay = fx.layout("L-9303", "city", "small_flat", None)
    lay["side_a"] = {"headcount": 8, "units": grid_units(8, 1000.0, 0)}
    lay["side_b"] = {"headcount": 8, "units": grid_units(8, 3000.0, 0)}
    lay["side_a"]["units"][5].update(x=500.0, y=1000.0)
    lay["side_b"]["units"][0].update(x=3000.0, y=2800.0)
    lay["features"] = [{"kind": "city", "x": 2000.0, "y": 2000.0, "radius": 800, "buildings": ring(500.0, 1000.0) + ring(3000.0, 2800.0)}]
    assert reach(lay, ("side_a", "side_b"), point=(2000.0, 2000.0)) == "side_a unit 5"
    assert reach(lay, ("side_b",), point=(2000.0, 2000.0)) == "side_b unit 0"


def test_the_pass_rule_covers_every_unit_when_the_route_is_open():
    """Cardinality many: 256 units a side (R4 maximum) on an open 200 wu gap, both sides asked: no unit is unreachable, None."""
    lay = gap_layout("L-9304", 200, orders="both_same_point")
    lay["side_a"] = {"headcount": 256, "units": grid_units(256, 200.0, 0, per_row=16, y0=1200.0)}
    lay["side_b"] = {"headcount": 256, "units": grid_units(256, 3000.0, 0, per_row=16, y0=1200.0)}
    assert reach(lay, ("side_a", "side_b"), point=(2000.0, 2000.0)) is None


@pytest.mark.parametrize("features_value", [None, []])
def test_a_layout_without_planar_rectangles_or_slope_returns_none(features_value):
    """Criterion 1, last sentence: "The function returns None when the layout has neither planar rectangles nor a slope" (Existence: no `features` key, an empty list).
    A world on which nothing was applied is enough."""
    lay = fx.layout("L-9305", "open_field", "small_flat", None)
    if features_value is not None:
        lay["features"] = features_value
    engine = Engine()
    w = engine.new_world(1)
    try:
        assert features.first_unreachable(engine, w, lay, produce.presets()["small_flat"], (2000.0, 2000.0), ("side_a", "side_b")) is None
    finally:
        engine.free_world(w)


# ---------------------------------------------------------------- (c): the slope, from the engine's walk mask

def test_slope_unit_on_the_cliff_is_rejected_and_the_foot_passes():
    """Criterion 1 (c), spec lines 22 and 23: SLOPE_FIXTURE with B unit 3 on the cliff (2000, 1500: inside the slope columns, outside the ribbon rows) is rejected
    naming that unit; with every B unit at the foot it passes."""
    assert reach(slope_layout("L-9306", {3: (2000.0, 1500.0)})) == "side_b unit 3"
    assert reach(slope_layout("L-9306")) is None


def test_slope_unit_on_the_ribbon_is_not_rejected():
    """Criterion 1 (c) and the known limit "the route check treats the ribbon as the only way up" (criterion 2): a B unit standing in the ribbon rows (2000, 2000) can
    reach the top, so the cliff rejection is the cliff and not the whole slope."""
    assert reach(slope_layout("L-9307", {3: (2000.0, 2000.0)})) is None


def test_slope_unit_on_the_far_cliff_row_is_rejected_too():
    """Criterion 1 (c): the cliff is both flanks of the ribbon; a unit at (2000, 2500), outside the ribbon rows on the other side, is rejected as well."""
    assert reach(slope_layout("L-9308", {5: (2000.0, 2500.0)})) == "side_b unit 5"


def test_slope_walk_mask_is_the_union_over_the_presets_layers():
    """Criterion 1, DRAFT-reach-mask-union: "a cell is open if any layer's mask is non-zero". The real masks block the cliff unit; with one layer's mask patched to open
    everywhere the same unit passes. Every layer of the preset (small_tiered has 3) is asked."""
    asked = []

    def tweak(engine):
        real = engine.terrain_walk_mask

        def mask(w, layer):
            asked.append(int(layer))
            data = real(w, layer)
            return b"\x01" * len(data) if int(layer) == 1 else data
        engine.terrain_walk_mask = mask
    lay = slope_layout("L-9309", {3: (2000.0, 1500.0)})
    assert reach(lay, tweak=tweak) is None, "a cell open on layer 1 must be open"
    assert sorted(set(asked)) == list(range(produce.presets()["small_tiered"]["layers"]))


def test_slope_walk_mask_is_read_once_per_layer_not_per_unit():
    """Criterion 1 and the brief's hot path (linear-ish in cells plus units): the mask reads do not grow with the unit count, 8 against 128 a side."""
    def reads(n):
        count = []

        def tweak(engine):
            real = engine.terrain_walk_mask
            engine.terrain_walk_mask = lambda w, layer: (count.append(1), real(w, layer))[1]
        lay = slope_layout("L-9310")
        lay["side_a"] = {"headcount": n, "units": grid_units(n, 2480.0, 1, per_row=8)}
        lay["side_b"] = {"headcount": n, "units": grid_units(n, 1000.0, 0, per_row=8)}
        reach(lay, tweak=tweak)
        return len(count)
    small, many = reads(8), reads(128)
    assert 0 < small == many <= produce.presets()["small_tiered"]["layers"]


# ---------------------------------------------------------------- composition: run.unreachable calls the new signature

def test_run_unreachable_calls_first_unreachable_with_the_engine_and_an_applied_world(monkeypatch):
    """Composition (criterion 1, brief): `run.unreachable(layout)` builds a throwaway world, applies the features, calls `features.first_unreachable(engine, w, layout,
    preset, point, sides)` and frees the world. A spy sees the engine, a world whose terrain exists (apply ran: the walk mask is non-empty), the preset of the landscape,
    the orders point (side A's centroid) and the moving side; its answer is returned, and exactly one world is made and freed."""
    seen, worlds = {}, []
    real_new, real_free = Engine.new_world, Engine.free_world
    monkeypatch.setattr(Engine, "new_world", lambda self, seed: (worlds.append("new"), real_new(self, seed))[1])
    monkeypatch.setattr(Engine, "free_world", lambda self, w: (worlds.append("free"), real_free(self, w))[1])

    def spy(engine, w, layout, preset, point, sides):
        seen.update(engine=engine, mask=len(engine.terrain_walk_mask(w, 0)), preset=preset, point=point, sides=tuple(sides), layout=layout)
        return "side_b unit 7"
    monkeypatch.setattr(features, "first_unreachable", spy)
    lay = slope_layout("L-9311")
    assert arena_run.unreachable(lay) == "side_b unit 7"
    assert isinstance(seen["engine"], Engine)
    assert seen["mask"] > 0, "the world had no applied terrain when the route check ran"
    assert seen["preset"] == produce.presets()["small_tiered"]
    assert seen["sides"] == ("side_b",) and seen["layout"] is lay
    assert tuple(round(c, 2) for c in seen["point"]) == tuple(round(c, 2) for c in centroid(lay, "side_a"))
    assert worlds == ["new", "free"]


def test_run_unreachable_agrees_with_the_direct_call_on_planar_gaps():
    """Composition: through `run.unreachable` (no engine handed in) the 60 wu gap is rejected and the 200 wu gap passes, the same answers as the direct call above."""
    assert arena_run.unreachable(gap_layout("L-9312", 60)) == "side_b unit 0"
    assert arena_run.unreachable(gap_layout("L-9312", 200)) is None
    assert arena_run.unreachable(slope_layout("L-9313", {3: (2000.0, 1500.0)})) == "side_b unit 3"
    assert arena_run.unreachable(slope_layout("L-9313")) is None


def test_cli_rejects_the_60wu_gap_and_the_touching_walls_with_the_r8_line(tmp_path):
    """Criterion 1 (a)(b) through the CLI: exit 2, exactly `REJECT <id> R8 unreachable: side_b unit 0`, no fight file written."""
    for gap, lid in ((60, "L-9314"), (0, "L-9315")):
        proc, doc = fx.fight(gap_layout(lid, gap), tmp_path / lid, 1, "--cap-seconds", "5")
        assert proc.returncode == 2, proc.stdout + proc.stderr
        assert [l for l in proc.stdout.splitlines() if l.startswith("REJECT")] == ["REJECT %s R8 unreachable: side_b unit 0" % lid]
        assert doc is None


def test_cli_accepts_the_200wu_gap_and_the_slope_foot_and_rejects_the_cliff_unit(tmp_path):
    """Criterion 1 (a) and (c) through the CLI: the 200 wu gap and the slope with every B unit at the foot run to a fight (exit 0); the cliff unit is REJECTed."""
    for lay in (gap_layout("L-9316", 200), slope_layout("L-9317")):
        proc, doc = fx.fight(lay, tmp_path / lay["id"], 1, "--cap-seconds", "5")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert doc is not None
    proc, doc = fx.fight(slope_layout("L-9318", {3: (2000.0, 1500.0)}), tmp_path / "cliff", 1, "--cap-seconds", "5")
    assert proc.returncode == 2 and "REJECT L-9318 R8 unreachable: side_b unit 3" in proc.stdout
    assert doc is None
