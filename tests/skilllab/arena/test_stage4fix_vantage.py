# Rule pins: R-001-06, R-001-07, R-004-06, R-005-09, R-200-01
# spec: docs/reports/2026-11-06-stage4-fix-plan.md::F1 (vantage becomes real terrain); Story H-088 follow-up; Flag client
"""Stage 4 fix F1: a `vantage` feature is built as engine terrain (scripts/skilllab/arena/hills.py, features.apply(exact=True)).

Westley 2026-11-06 (decisions.md DEC-stage4-trap-intent, DEC-stage4-no-reach-up): "Red can fire up only at a certain point of moving up the hill ... if red decides to
move up the hill, blue should become in vision as soon as they crest over the half-way point up the hill, as the rules of the game are defined." No reach-up
setting: a unit on the ramp is on the upper layer from the slope midline (R-004-06, R-004-08), and only then sees and is seen by the rise (R-005-09).

Fixture: `small_tiered`, hill centre (1100, 2000) radius 700 (the H-088 vantage fixture): rim at x 1800, foot at x 2000 (RAMP_WU 200), so the midline is near
x 1900 on the +x side. A low walker starts at (2300, 2000) and attack-moves west; a Vanguard stands still on the rise at (1700, 2000).
The engine's flip is read from the walker's own layer each tick, the band boundary from `Engine.terrain_band_at` on the walker's row, and the drawn midline (radius + 100)
is compared with both. The stage 4 rule set is set by hand here exactly as run.fight sets it (ground era, walkers, reach 0 up 1 down)."""
import math

import pytest

import h063_fixtures as fx
import h088_fixtures as fx88
from scripts.skilllab.arena import features, run as arena_run
from scripts.skilllab.catalogue import produce
from scripts.skilllab.engine import Engine
from scripts.skilllab.fight import _register_types

CX, CY, RADIUS, RAMP = 1100.0, 2000.0, 700.0, 200.0


def _world(low_xy, rise_xy):
    """(engine, world, low walker id, rise unit id) with the vantage fixture's terrain built exactly as the runner builds it under --sight on."""
    lay = fx88.vantage_layout("L-9820")
    e = Engine()
    w = e.new_world(1)
    e.disable_abilities(w)
    preset = produce.presets()[lay["landscape"]]
    features.apply(e, w, lay, preset, 1, exact=True)
    types = _register_types(e, w, arena_run._setup_for(lay))
    features.walk_on_ground(e, w, types)
    e.set_era_kind(w, 1)
    for type_id, _ in types.values():
        e.set_reach(w, type_id, 0, 1)
    tid = types["Vanguard"][0]
    low = e.spawn(w, tid, 1, low_xy[0], low_xy[1], 0)
    rise = e.spawn(w, tid, 0, rise_xy[0], rise_xy[1], 1)
    return e, w, low, rise


def _climb(heading_deg=0.0, ticks=700):
    """Walk a low unit toward the hill centre from `heading_deg` (0 = from +x) at distance 400 beyond the foot; returns the per-tick rows
    [(tick, x, y, layer, low sees rise, rise sees low)] and the engine."""
    a = math.radians(heading_deg)
    start = (CX + (RADIUS + RAMP + 400) * math.cos(a), CY + (RADIUS + RAMP + 400) * math.sin(a))
    e, w, low, rise = _world(start, (CX + 600 * math.cos(a), CY + 600 * math.sin(a)))
    e.order_attack_move(w, [low], CX + 400 * math.cos(a), CY + 400 * math.sin(a))
    rows = []
    for t in range(1, ticks + 1):
        e.step(w)
        x, y = e.unit_pos(w, low)
        rows.append((t, x, y, e.unit_layer(w, low), e.can_see(w, low, rise), e.can_see(w, rise, low)))
    return rows, e, w


def test_a_unit_placed_on_the_rise_starts_on_layer_1_from_the_ground():
    """R-200-01/02: the layer is the ground's, not the layout's column. Terrain band at the fixture's side A positions is 2 (layer 1), at side B's is 1 (layer 0)."""
    e, w, low, rise = _world((2600.0, 2000.0), (1400.0, 2000.0))
    assert e.terrain_band_at(w, 1400.0, 2000.0) == 2 and e.terrain_band_at(w, 2600.0, 2000.0) == 1
    assert e.unit_layer(w, rise) == 1 and e.unit_layer(w, low) == 0


def test_the_walker_changes_layer_exactly_where_the_ramp_midline_is():
    """R-004-06, R-001-06: below the midline the walker is on layer 0, at or above it on layer 1, flipping once. The flip sits on the cell boundary where the
    engine's band changes on the walker's row, and within 60 wu of the drawn midline (radius + RAMP / 2 from the hill centre)."""
    rows, e, w = _climb(0.0)
    layers = [r[3] for r in rows]
    assert layers[0] == 0 and layers[-1] == 1 and sorted(set(layers)) == [0, 1]
    flip = next(i for i, l in enumerate(layers) if l == 1)
    assert all(l == 1 for l in layers[flip:]), "the walker flips back after the midline"
    x_flip, y_flip = rows[flip][1], rows[flip][2]
    assert e.terrain_band_at(w, x_flip, y_flip) == 2 and e.terrain_band_at(w, rows[flip - 1][1], rows[flip - 1][2]) == 1, "the flip is where the engine's band changes"
    assert abs(x_flip - (CX + RADIUS + RAMP / 2)) <= 60.0, "flip at x %.1f against the drawn midline %.1f" % (x_flip, CX + RADIUS + RAMP / 2)


@pytest.mark.parametrize("heading", [0.0, 45.0, 90.0, 270.0, 315.0])
def test_the_flip_is_within_one_cell_of_the_drawn_midline_from_every_side(heading):
    """The drawn midline is a ring at radius + RAMP / 2; the engine's flip is a cell boundary, so it can sit up to about one cell off along a diagonal."""
    rows, _, _ = _climb(heading)
    flip = next(i for i, r in enumerate(rows) if r[3] == 1)
    d = math.hypot(rows[flip][1] - CX, rows[flip][2] - CY)
    assert abs(d - (RADIUS + RAMP / 2)) <= 100.0, (heading, d)


def test_from_the_flip_tick_the_climber_sees_and_is_seen_by_the_rise_and_before_it_the_low_unit_sees_nothing_up():
    """R-005-09: a lower layer never sees up. Before the flip tick the low unit's can_see of the rise unit is false on every tick; from the flip tick it is true
    (same layer, 200 wu apart), and the rise unit sees the climber from that tick too (R-004-06: from the midline the climber counts as the upper layer)."""
    rows, _, _ = _climb(0.0)
    flip = next(i for i, r in enumerate(rows) if r[3] == 1)
    assert not any(r[4] for r in rows[:flip]), "the low unit saw up before the midline"
    assert all(r[4] and r[5] for r in rows[flip:flip + 20]), "after the midline the climber and the rise see each other"


def test_the_layer_column_must_agree_with_the_ground_or_the_runner_rejects(tmp_path):
    """The brief: the `layer` column must agree with the ground or the preflight rejects. A side A unit on the rise written layer 0, and a side B unit on flat ground
    written layer 1, each REJECT with exit 2 under --sight on; the consistent fixture runs (control)."""
    ok = fx88.vantage_layout("L-9821")
    assert fx.run(fx.write(ok, tmp_path / "ok"), tmp_path / "ok_out", 1, "--sight", "on", "--cap-seconds", "2").returncode == 0
    for side, layer in (("side_a", 0), ("side_b", 1)):
        bad = fx88.vantage_layout("L-9822")
        bad[side]["units"][0]["layer"] = layer
        proc = fx.run(fx.write(bad, tmp_path / side), tmp_path / (side + "_out"), 1, "--sight", "on", "--cap-seconds", "2")
        assert proc.returncode == 2 and "REJECT L-9822 G1 layer: %s unit 0" % side in proc.stdout, proc.stdout


def test_the_hill_is_not_built_under_sight_off(tmp_path):
    """Stages 1 to 3 are unchanged: `--sight off` builds no terrain for a vantage (the layer column is the layout's, no REJECT for a disagreeing column)."""
    bad = fx88.vantage_layout("L-9823")
    bad["side_a"]["units"][0]["layer"] = 0
    proc = fx.run(fx.write(bad, tmp_path), tmp_path / "out", 1, "--sight", "off", "--cap-seconds", "2")
    assert proc.returncode == 0, proc.stdout


def test_two_hills_and_the_unsupported_cases():
    """hills.py builds each vantage with height_band 1; another band, or a vantage in a one-layer preset, raises ValueError (as features._slope_heights does)."""
    from scripts.skilllab.arena import hills
    pre = produce.presets()
    f = [{"kind": "vantage", "x": 1000.0, "y": 1000.0, "radius": 300.0, "height_band": 1}, {"kind": "vantage", "x": 3000.0, "y": 3000.0, "radius": 300.0, "height_band": 1}]
    cm = hills.heights(f, 40, 40)
    assert len(cm) == 1600 and max(cm) > min(cm)
    with pytest.raises(ValueError):
        hills.heights([dict(f[0], height_band=2)], 40, 40)
    with pytest.raises(ValueError):
        hills.check_preset(pre["small_flat"])
