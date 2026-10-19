# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L4 (knob families and bands, controls, bisection, smoke and sweep commands); rulings 3, 4, 10, 11, 13
"""LAB-REV2-L4: scripts/skilllab/sweep.py (NEW), driven by fakes. No engine, no map, no pool process.

THIS FILE FREEZES THE sweep.py INTERFACE FOR THE BUILDER (the spec names the families, grids and commands; it names no function).
Anything marked "pinned" below is asserted; anything else in sweep.py is the builder's.

    FAMILY_ORDER = ("vision", "range_up", "damage_up", "emitting", "arc", "cone", "sign_flip")   # run order; sign_flip last
    SIZE, ENEMY_FROM, ENEMY_TO, REPLICATES = 16, 8, 48, 3
    BASES: {key: base value}; in_band(value, base) -> bool, true for 0.25 * base <= value <= 4 * base
    Point (frozen dataclass): family, knob (OM_TP_* name, or "cone"), value (float), settings {OM_TP_* name: number},
        setup {Setup field: value} (firing_arc_deg, cone), kind, label
        kind in {"grid", "refined", "sign_flip", "control_positive", "control_null"}
    grid(family) -> list[Point]            the coarse points in the spec's order (kind "grid"; sign_flip family: kind "sign_flip")
    controls(family) -> {"positive": Control, "null": Control}   Control: points (list[Point]), reach (None or (0, 0)), check(results),
        max_ticks (CONTROL_MAX_TICKS for a control that needs no result, None for one that does: the fight runs to its own cap),
        play (str or None; decisions 22)
        check(results_by_point) -> bool, results_by_point = [[FightResult, ...] per control point, in points order]
        play: None means the control is fought on every play the run covers (the vision and the null controls). A name means the
        control is ONE DESIGNATED FIGHT on that play, whatever `plays` the run was given: the entry's "ok" comes from that fight alone,
        never from a conjunction over plays (decisions 22). Damage-up's positive control is designated on "s3_types_by_reach". The
        control's rows are in the csv with kind "control_positive" and play = the designated play. A play on which a knob is inert is
        never the designated fight; an inert observation with no rule behind it is a finding (ledger FINDING-damage-up-layer-above),
        not an exemption: no test here asserts a damage-up response on s3_layer_above.
    refine(values, differs, max_rounds=2) -> [(round, value), ...]    differs(value) -> bool, called once per value
    Capabilities(arc, cone) (namedtuple of bool); detect(engine) -> Capabilities; skip_reason(family, caps) -> str | None
    baseline_roles(play) -> tuple of roles; the roles for sweep rows: "play", "reach_zero" (the null control's build), and the
        baselines "naive_attacker", "naive_defender" (a play whose name starts "s3_" has "naive_defender_attacker_layer" and
        "naive_defender_play_layer" in place of "naive_defender", ruling 3 DRAFT). Decisions 24: a play with a holder carries a
        `naive_defender*` role and gets the second listed crossing against it; a meeting (both sides attack-moved, no holder) carries
        none and has none. refined_vs has one key per role that some run play's baseline_roles lists, and no other.
    run_family(family, out_dir, *, builds, layouts, plays=None, fight_fn=None, map_fn=None, caps=None, replicates=REPLICATES,
               full_scan=False) -> dict    full_scan False (the default) scans by bisection, True fights every headcount 8 to 48
        the entry: family, skipped, csv, rows, refined (sorted values added by refinement, all baselines), refined_vs ({baseline role:
        sorted values refined for the sign change of the gain against that baseline}), refused, controls ({"positive"/"null": {"ok"}}; the positive one also carries "play": the designated play, or None),
        defects ({"cap_rows": cap fights outside control_* kinds, "draw_rows": draw fights, "cells": distinct (play, layout, kind,
        knob_value, baseline, enemy_heads) non-control cells holding a cap or a draw}), saturated_at_vision (emitting)
        builds(play, role, layout_features) -> BuildFn (build.labels["prefight"] is set when the build is called, as
        scenes.placed_scene does); layouts {name: features}; caps None means detect the real library.
    run(families, out_dir, workers=1, full_scan=False, **same keywords) -> dict; calls sweep.run_family(name, out_dir, **kw) once per family, in the
        given order; with workers > 1 and no map_fn it fights through pool.FightPool(workers, lean=True).map
    SMOKE_LAYOUTS = ("81", "78", "192"); smoke_layouts() -> {name: features}; run_smoke(out_dir, workers=12, full_scan=False, **same keywords)
    -> dict; its summary carries "defects" with the same three counts as a sweep entry. Smoke control rows have a kind starting
    "control_"; the vision rows do not.
    Refinement (families vision, range_up, damage_up, arc only): the sign of a point is "gain > 0", gain = break-even of the play minus the
    break-even of the baseline at the same knob value, a ceiling hit counting as the top of the range (48) and a scan with no break-even
    (lost everywhere) as 0; gain exactly 0 is not positive. Midpoints are arithmetic. The CLI flag `--full-scan` (sweep, smoke, controls,
    reach) selects the linear scan; controls and reach are always linear.
Files: sweep_<family>.csv per run family, sweep_summary.json; smoke.csv, smoke_summary.json.
CSV columns (labels on the rows beside rows.fight_row's own): family, play, layout, kind, enemy_heads, knob, knob_value, baseline
(`none` for the play itself), ceiling_hit (0 or 1, of the row's scan), prefight.
"""
import ast
import csv
import dataclasses
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import FakePool, ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab import __main__ as cli, pool, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

ALL = None   # set below: Capabilities(arc=True, cone=True)
V1, V2 = "OM_TP_VISION_UP_1", "OM_TP_VISION_UP_2"


def caps(arc=True, cone=True):
    return sweep.Capabilities(arc=arc, cone=cone)


def values(family, kind="grid"):
    return [p.value for p in sweep.grid(family) if p.kind == kind]


def points(family):
    return [p for p in sweep.grid(family)]


# ---- the grids equal the spec's lists --------------------------------------------------------------------------------------

def test_family_order_and_sizes_are_the_spec_batch_order():
    assert sweep.FAMILY_ORDER == ("vision", "range_up", "damage_up", "emitting", "arc", "cone", "sign_flip")
    assert (sweep.SIZE, sweep.ENEMY_FROM, sweep.ENEMY_TO, sweep.REPLICATES) == (16, 8, 48, 3)


def test_vision_one_layer_grid_and_the_two_layer_ratio():
    """Vision, one layer 0.125, 0.25, 0.5, 1.0 (symmetric: up and down together, ruling 10); two layers at the 0.4 ratio,
    0.05, 0.1, 0.2, 0.4; the engine refuses above 1.0."""
    pts = points("vision")
    assert [p.value for p in pts] == [0.125, 0.25, 0.5, 1.0] and {p.kind for p in pts} == {"grid"}
    for p in pts:
        assert p.family == "vision" and p.knob == V1 and p.setup == {}
        assert p.settings[V1] == p.settings["OM_TP_VISION_DOWN_1"] == p.value
        assert p.settings[V2] == pytest.approx(0.4 * p.value) == pytest.approx(p.settings["OM_TP_VISION_DOWN_2"])
        assert set(p.settings) == {V1, "OM_TP_VISION_DOWN_1", V2, "OM_TP_VISION_DOWN_2"}
    assert [round(p.settings[V2], 10) for p in pts] == [0.05, 0.1, 0.2, 0.4]
    assert max(p.settings[V1] for p in pts) <= 1.0


def test_range_up_grid_two_layers_at_the_same_value_and_range_down_one():
    pts = points("range_up")
    assert [p.value for p in pts] == [1.0, 0.75, 0.5, 0.25] and {p.kind for p in pts} == {"grid"}
    for p in pts:
        assert p.knob == "OM_TP_RANGE_UP_1"
        assert p.settings == {"OM_TP_RANGE_UP_1": p.value, "OM_TP_RANGE_UP_2": p.value,
                              "OM_TP_RANGE_DOWN_1": 1.0, "OM_TP_RANGE_DOWN_2": 1.0}


def test_damage_up_grid():
    pts = points("damage_up")
    assert [p.value for p in pts] == [1.0, 0.75, 0.5, 0.25] and {p.kind for p in pts} == {"grid"}
    for p in pts:
        assert p.knob == "OM_TP_DAMAGE_UP_1" and p.settings["OM_TP_DAMAGE_UP_1"] == p.value
        assert all(k.startswith("OM_TP_DAMAGE_") for k in p.settings)      # the layer-2 and down values are the builder's, inside the band


def test_emitting_runs_only_jointly_with_vision_0125_and_025():
    """(sight, seen) in {(1.0, 1.5), (2.0, 3.0), (4.0, 6.0)} jointly with vision 0.125 and 0.25 and with nothing else: six points."""
    pts = points("emitting")
    got = {(p.settings["OM_TP_EMIT_SIGHT_MULT"], p.settings["OM_TP_EMIT_SEEN_MULT"], p.settings[V1]) for p in pts}
    assert got == {(s, t, v) for (s, t) in ((1.0, 1.5), (2.0, 3.0), (4.0, 6.0)) for v in (0.125, 0.25)} and len(pts) == 6
    for p in pts:
        assert p.family == "emitting" and p.kind == "grid" and p.knob == "OM_TP_EMIT_SIGHT_MULT" and p.value == p.settings["OM_TP_EMIT_SIGHT_MULT"]
        assert p.settings["OM_TP_EMIT_SEEN_MULT"] > p.settings["OM_TP_EMIT_SIGHT_MULT"]      # R-163-01: seen always above sight
        assert p.settings["OM_TP_VISION_DOWN_1"] == p.settings[V1] and p.settings[V2] == pytest.approx(0.4 * p.settings[V1])


def test_emitting_never_sweeps_the_base_vision_it_is_reported_saturated():
    assert all(p.settings[V1] < 0.5 for p in points("emitting"))


def test_arc_grid_through_the_firing_arc_parameter():
    pts = points("arc")
    assert [p.value for p in pts] == [360, 270, 180, 120, 90] and {p.kind for p in pts} == {"grid"}
    for p in pts:
        assert p.knob == "OM_TP_FIRING_ARC_DEG" and p.setup == {"firing_arc_deg": float(p.value)} and p.settings == {}


def test_cone_grid_range_by_half_angle_at_share_one_on_vanguard():
    """Range 150, 300, 600 by half-angle 22.5, 45, 90 at share 1.0. The type is Vanguard (the arc and cone plays are all-Vanguard
    M0 mixes; the spec names no type: flagged in the report)."""
    pts = points("cone")
    assert len(pts) == 9 and {p.kind for p in pts} == {"grid"}
    got = {(p.setup["cone"]["Vanguard"]) for p in pts}
    assert got == {(r, h, 1.0) for r in (150, 300, 600) for h in (22.5, 45, 90)}
    for p in pts:
        assert list(p.setup) == ["cone"] and list(p.setup["cone"]) == ["Vanguard"] and p.knob == "cone" and p.value == p.setup["cone"]["Vanguard"][0]


def test_the_sign_flip_points_are_range_up_2_and_damage_up_2_labelled_and_last():
    pts = points("sign_flip")
    assert [(p.knob, p.value) for p in pts] == [("OM_TP_RANGE_UP_1", 2.0), ("OM_TP_DAMAGE_UP_1", 2.0)]
    assert {p.kind for p in pts} == {"sign_flip"} and all("sign-flip" in p.label for p in pts)
    assert pts[0].settings["OM_TP_RANGE_UP_2"] == 2.0
    assert sweep.FAMILY_ORDER[-1] == "sign_flip"


def test_nothing_above_one_is_a_sweep_point_only_the_labelled_sign_flip():
    """Firing up is a penalty: range-up and damage-up grids run from 1.0 down to 0.25, never above."""
    for fam in ("range_up", "damage_up"):
        assert all(v <= 1.0 for v in values(fam))
    others = [p for fam in sweep.FAMILY_ORDER if fam != "sign_flip" for p in points(fam)]
    for p in others:
        for k, v in p.settings.items():
            if k.startswith(("OM_TP_RANGE_UP", "OM_TP_DAMAGE_UP", "OM_TP_RANGE_DOWN", "OM_TP_DAMAGE_DOWN")):
                assert v <= 1.0, (p, k)


def test_every_setting_a_point_sets_is_a_real_engine_parameter():
    """Names are read against the header's parameter enum (the contract), so a typo in a knob name fails here, not in a night run.
    OM_TP_FIRING_ARC_DEG is E0's: it is in the header only after E0 lands, and the arc family's knob is that name."""
    from scripts.skilllab import engine as engine_module
    ids = set(engine_module._load_param_ids()) | {"OM_TP_FIRING_ARC_DEG"}
    names = {k for fam in sweep.FAMILY_ORDER for p in points(fam) for k in p.settings}
    names |= {p.knob for fam in sweep.FAMILY_ORDER for p in points(fam) if p.knob != "cone"}
    for fam in sweep.FAMILY_ORDER:
        for c in sweep.controls(fam).values():
            names |= {k for p in c.points for k in p.settings}
    assert names and names <= ids, sorted(names - ids)


# ---- the band ---------------------------------------------------------------------------------------------------------------

def test_in_band_is_a_closed_interval_from_a_quarter_to_four_times_the_base():
    assert sweep.in_band(0.25, 1.0) and sweep.in_band(4.0, 1.0) and sweep.in_band(1.0, 1.0)
    assert not sweep.in_band(0.2499, 1.0) and not sweep.in_band(4.0001, 1.0) and not sweep.in_band(0.0, 1.0)
    assert sweep.in_band(0.125, 0.5) and not sweep.in_band(0.12, 0.5)


def test_bases_are_the_bibles_values_or_westleys_start():
    b = sweep.BASES
    assert (b[V1], b[V2], b["OM_TP_RANGE_UP_1"], b["OM_TP_DAMAGE_UP_1"]) == (0.5, 0.2, 1.0, 1.0)
    assert (b["OM_TP_EMIT_SIGHT_MULT"], b["OM_TP_EMIT_SEEN_MULT"]) == (2.0, 3.0)        # Westley's start (2026-10-13)
    assert b["OM_TP_FIRING_ARC_DEG"] == 360.0 and (b["cone_range"], b["cone_half_angle"]) == (300.0, 45.0)    # DRAFT bases


def test_no_grid_or_sign_flip_point_leaves_the_band_around_its_base():
    """Spec ruling 11: every sweep stays inside 0.25x to 4x of its base. Every setting key a point sets has a base."""
    checked = 0
    for fam in sweep.FAMILY_ORDER:
        for p in points(fam):
            for k, v in p.settings.items():
                assert k in sweep.BASES, (fam, k)
                if k.endswith(("_DOWN_1", "_DOWN_2")) and k.startswith(("OM_TP_RANGE", "OM_TP_DAMAGE")):
                    continue
                assert sweep.in_band(v, sweep.BASES[k]), (fam, k, v)
                checked += 1
            if "firing_arc_deg" in p.setup:
                assert sweep.in_band(p.setup["firing_arc_deg"], sweep.BASES["OM_TP_FIRING_ARC_DEG"])
            if "cone" in p.setup:
                rng, half, share = p.setup["cone"]["Vanguard"]
                assert sweep.in_band(rng, sweep.BASES["cone_range"]) and sweep.in_band(half, sweep.BASES["cone_half_angle"]) and share == 1.0
    assert checked > 40


def test_positive_control_a_point_outside_the_band_is_caught_by_the_same_check():
    """The detector above is not vacuous: 5.0 for a base of 1.0 fails in_band, and a grid-shaped Point carrying it is not in the band."""
    bad = dataclasses.replace(points("range_up")[0], settings={"OM_TP_RANGE_UP_1": 5.0})
    assert not sweep.in_band(bad.settings["OM_TP_RANGE_UP_1"], sweep.BASES["OM_TP_RANGE_UP_1"])


# ---- refinement ------------------------------------------------------------------------------------------------------------

def _refine(vals, true_set, **kw):
    calls = []

    def differs(v):
        calls.append(v)
        return v in true_set if not callable(true_set) else true_set(v)

    return sweep.refine(vals, differs, **kw), calls


def test_refine_halves_only_between_the_two_coarse_points_that_bracket_a_sign_change_at_most_two_rounds():
    """Coarse 1.0, 0.75, 0.5, 0.25 with the sign true at 1.0 and 0.75 only: the change is between 0.75 and 0.5. Round 1 adds 0.625
    (false); round 2 halves the bracket 0.75 to 0.625 and adds 0.6875 (false); there is no round 3."""
    got, calls = _refine([1.0, 0.75, 0.5, 0.25], lambda v: v >= 0.75)
    assert got == [(1, 0.625), (2, 0.6875)]
    assert sorted(calls) == sorted([1.0, 0.75, 0.5, 0.25, 0.625, 0.6875]) and len(calls) == len(set(calls))      # one call per value


def test_refine_follows_the_bracket_when_the_new_point_is_on_the_other_side():
    got, _ = _refine([1.0, 0.75, 0.5, 0.25], lambda v: v >= 0.7)
    assert got == [(1, 0.625), (2, 0.6875)]        # change lies in (0.6875, 0.75)
    got, _ = _refine([1.0, 0.75, 0.5, 0.25], lambda v: v >= 0.6)
    assert got == [(1, 0.625), (2, 0.5625)]       # 0.625 is true, so the bracket is now 0.625 to 0.5 and round 2 halves it


def test_refine_adds_nothing_without_a_sign_change():
    for truth in (lambda v: True, lambda v: False):
        got, calls = _refine([1.0, 0.75, 0.5, 0.25], truth)
        assert got == [] and sorted(calls) == [0.25, 0.5, 0.75, 1.0]


def test_refine_halves_every_bracket_when_there_are_two_changes():
    got, _ = _refine([1.0, 0.75, 0.5, 0.25], lambda v: v in (1.0, 0.75, 0.25) or (v < 0.3 and v > 0.2), max_rounds=1)
    assert sorted(v for _r, v in got) == [0.375, 0.625]       # 0.75|0.5 and 0.5|0.25


def test_refine_max_rounds_zero_and_one():
    assert _refine([1.0, 0.75, 0.5, 0.25], lambda v: v >= 0.75, max_rounds=0)[0] == []
    assert _refine([1.0, 0.75, 0.5, 0.25], lambda v: v >= 0.75, max_rounds=1)[0] == [(1, 0.625)]


def test_refine_never_leaves_the_coarse_range():
    got, _ = _refine([0.125, 0.25, 0.5, 1.0], lambda v: v >= 0.5)
    assert got and all(0.125 <= v <= 1.0 for _r, v in got)
    assert all(0.25 <= v <= 0.5 for _r, v in got)


# ---- skipping a family the library cannot run ---------------------------------------------------------------------------------

def test_skip_reason_names_the_missing_arc_parameter_and_the_missing_cone_symbol():
    assert sweep.skip_reason("arc", caps(arc=False)) is not None and "OM_TP_FIRING_ARC_DEG" in sweep.skip_reason("arc", caps(arc=False))
    assert "om_roster_set_cone" in sweep.skip_reason("cone", caps(cone=False))
    for fam in ("vision", "range_up", "damage_up", "emitting", "sign_flip"):
        assert sweep.skip_reason(fam, caps(arc=False, cone=False)) is None
    assert sweep.skip_reason("arc", caps()) is None and sweep.skip_reason("cone", caps()) is None
    assert sweep.skip_reason("arc", caps(arc=True, cone=False)) is None and sweep.skip_reason("cone", caps(arc=False, cone=True)) is None


class FakeLib:
    """An Engine stand-in for detect(): param_id raises ValueError for unknown parameters; set_cone raises AttributeError when the
    symbol is absent (measured on the lab branch's library) and ValueError when it is the E0 stub."""

    def __init__(self, params=(), cone="absent"):
        self.params, self.cone = set(params), cone
        self.freed = 0

    def param_id(self, name):
        if name not in self.params:
            raise ValueError("unknown parameter %r" % (name,))
        return 1

    def new_world(self, seed):
        return object()

    def free_world(self, w):
        self.freed += 1

    def type_id(self, name):
        return 2

    def set_cone(self, w, type_id, range, half_angle, share):
        if self.cone == "absent":      # engine.Engine.set_cone on a library without the symbol: ctypes raises AttributeError
            raise AttributeError("undefined symbol: om_roster_set_cone")
        if self.cone != "built":       # the E0 stub: the symbol exists and returns -1, which Engine.set_cone turns into ValueError
            raise ValueError("om_roster_set_cone returned -1")


def test_detect_reads_the_parameter_table_and_probes_the_cone_symbol():
    assert sweep.detect(FakeLib()) == sweep.Capabilities(arc=False, cone=False)
    assert sweep.detect(FakeLib(params={"OM_TP_FIRING_ARC_DEG"})) == sweep.Capabilities(arc=True, cone=False)
    assert sweep.detect(FakeLib(cone="built")) == sweep.Capabilities(arc=False, cone=True)
    lib = FakeLib(params={"OM_TP_FIRING_ARC_DEG"}, cone="built")
    assert sweep.detect(lib) == sweep.Capabilities(arc=True, cone=True) and lib.freed >= 1      # the probe world is freed


def test_detect_cone_is_false_when_the_symbol_is_a_not_built_stub():
    """After E0 and before E2 the symbol exists and returns -1 (engine.set_cone raises ValueError): not usable."""
    assert sweep.detect(FakeLib(params={"OM_TP_FIRING_ARC_DEG"}, cone="stub")).cone is False


# ---- controls ---------------------------------------------------------------------------------------------------------------

def _res(outcome="side0", **kw):
    return _fr(outcome, kw.pop("enemy", 16), **kw)


def test_every_family_has_a_null_control_and_vision_and_damage_have_a_positive_one():
    for fam in ("vision", "range_up", "damage_up", "emitting"):
        c = sweep.controls(fam)["null"]
        assert c.reach == (0, 0) and len(c.points) >= 2 and {p.kind for p in c.points} == {"control_null"}
        assert [p.settings for p in c.points] == [p.settings for p in points(fam)] and [p.setup for p in c.points] == [p.setup for p in points(fam)]
    for fam in ("arc", "cone"):
        assert "null" in sweep.controls(fam)
    assert sweep.controls("vision")["positive"].reach is None and sweep.controls("damage_up")["positive"].reach is None
    assert set(sweep.controls("sign_flip")) <= {"null", "positive"}


def test_arc_null_control_is_the_parameter_set_to_360_against_the_parameter_never_set():
    """Overseer default (DRAFT): arc 360 equals unset. The reach (0, 0) pin does not apply to arc: the two points are the real play with
    OM_TP_FIRING_ARC_DEG pushed to the world at 360 against the play with the parameter untouched (the lab skips the parameter at 360
    in the arc grid, so only an explicit setting can show the engine's 360 gate leaks)."""
    c = sweep.controls("arc")["null"]
    assert c.reach is None and len(c.points) == 2 and {p.kind for p in c.points} == {"control_null"}
    explicit, unset = sorted(c.points, key=lambda p: -len(p.settings))
    assert explicit.settings == {"OM_TP_FIRING_ARC_DEG": 360.0} and explicit.setup == {}
    assert unset.settings == {} and unset.setup == {}
    a, b = _res("side0", margin=0.5), _res("side0", margin=0.5)
    assert c.check([[a, b], [a, b]]) is True
    assert c.check([[a, b], [a, _res("side0", margin=0.25)]]) is False            # positive control: a differing row is caught
    assert c.check([[a, b], [a]]) is False


def test_cone_null_control_is_a_cone_of_range_zero_against_no_cone():
    """Overseer default (DRAFT): cone range 0 equals no cone (range 0 clears the cone, spec om_roster_set_cone)."""
    c = sweep.controls("cone")["null"]
    assert c.reach is None and len(c.points) == 2 and {p.kind for p in c.points} == {"control_null"}
    zero, none = sorted(c.points, key=lambda p: -len(p.setup))
    assert zero.setup == {"cone": {"Vanguard": (0.0, 45.0, 1.0)}} and zero.settings == {}
    assert none.setup == {} and none.settings == {}
    a = _res("side0", margin=0.5)
    assert c.check([[a], [a]]) is True and c.check([[a], [_res("side0", margin=0.1)]]) is False


def test_control_lengths_only_the_damage_control_needs_a_finished_fight():
    """Vision zero and every null control read rows that do not need a result: they stop at CONTROL_MAX_TICKS. The damage control
    reads a result (damage-up 0.5 changes it) and a capped fight at 600 ticks hides the effect, so it runs to elimination (max_ticks
    None; decisions 23). The 12000-tick cap is a threshold and does not move."""
    assert sweep.controls("vision")["positive"].max_ticks == sweep.CONTROL_MAX_TICKS
    for fam in ("vision", "range_up", "damage_up", "emitting", "arc", "cone"):
        assert sweep.controls(fam)["null"].max_ticks == sweep.CONTROL_MAX_TICKS, fam
    assert sweep.controls("damage_up")["positive"].max_ticks is None


def test_vision_positive_control_is_vision_zero_both_directions():
    c = sweep.controls("vision")["positive"]
    assert len(c.points) == 1 and c.points[0].kind == "control_positive" and c.points[0].value == 0.0
    assert c.points[0].settings[V1] == c.points[0].settings["OM_TP_VISION_DOWN_1"] == 0.0 and c.points[0].settings[V2] == 0.0


def test_vision_zero_check_wants_16_v_16_and_no_shot():
    check = sweep.controls("vision")["positive"].check
    quiet = _res("cap", fus=(0.0, 0.0), survivors=(16, 16))
    assert check([[quiet, quiet]]) is True
    assert check([[quiet, _res("cap", fus=(1.0, 0.0), survivors=(16, 16))]]) is False      # a shot was counted
    assert check([[quiet, _res("cap", fus=(0.0, 0.0), survivors=(15, 16))]]) is False      # a unit fell
    assert check([[quiet, _res("side0")]]) is False


def test_null_check_wants_byte_identical_rows_across_the_points():
    check = sweep.controls("vision")["null"].check
    a, b = _res("cap", fus=(0.0, 0.0)), _res("cap", fus=(0.0, 0.0))
    assert check([[a, b], [a, b], [a, b], [a, b]]) is True
    assert check([[a, b], [a, b], [a, b], [a, _res("cap", fus=(0.5, 0.0))]]) is False
    assert check([[a, b], [a, b], [a, b], [a]]) is False                                  # a different number of fights


def _lean(result, window=(12.75, 9.25)):
    """A result as the pool's lean mode returns it: the per-tick series are gone (trim_series), the window counts are row values."""
    return dataclasses.replace(result, firing=[], firing_window=window, weighted_window=window)


def test_damage_positive_control_changes_the_result_and_not_the_count():
    """The count is the opening-window firing count (a row value), not the per-tick firing series: the series is empty on a lean
    result (the pool, workers > 1), and the check must still work."""
    c = sweep.controls("damage_up")["positive"]
    assert [p.value for p in c.points] == [1.0, 0.5] and all(p.kind == "control_positive" for p in c.points)
    assert c.play == "s3_types_by_reach"                                                   # decisions 22: one designated fight
    assert sweep.controls("vision")["positive"].play is None and all(sweep.controls(f)["null"].play is None for f in ("vision", "damage_up"))
    base = [_lean(_res("side0", margin=0.5)) for _ in range(2)]
    half = [_lean(_res("side0", margin=0.25)) for _ in range(2)]
    assert c.check([base, half]) is True
    assert c.check([base, base]) is False                                                  # nothing changed
    moved = [_lean(_res("side0", margin=0.25), window=(9.0, 9.25)) for _ in range(2)]
    assert c.check([base, moved]) is False                                                 # the count moved too
    full = [dataclasses.replace(r, firing=[(0, 16, 16)]) for r in base]
    assert c.check([full, [dataclasses.replace(r, firing=[(0, 16, 16)]) for r in half]]) is True        # with the series present as well


# ---- run_family with fakes ----------------------------------------------------------------------------------------------------

class World(ScriptedFight):
    """Scripted fights keyed on role and settings. be_of(role, settings) -> break-even. Flags plant defects for the controls."""

    def __init__(self, be_of=None, arc_be=None, cone_be=None, **flags):
        super().__init__(be_of=lambda setup: be_of(setup.unit_types["_role"], setup.settings) if be_of else 20)
        self.flags, self.arc_be, self.cone_be = flags, arc_be, cone_be

    def __call__(self, setup, seed, swap):
        role, s, enemy = setup.unit_types["_role"], setup.settings, setup.unit_types["enemy"]
        self.calls.append(dict(setup=setup, seed=seed, swap=swap, enemy=enemy, role=role, play=setup.unit_types["_play"],
                               settings=dict(s), states=setup.states, max_ticks=setup.max_ticks, extra=dict(arc=setup.firing_arc_deg, cone=dict(setup.cone)),
                               key=(setup.unit_types["_play"], role, tuple(sorted(s.items())), setup.firing_arc_deg, setup.max_ticks, enemy, seed, swap)))
        if role == "reach_zero":
            leak = (sum(v for v in s.values() if isinstance(v, (int, float))) + setup.firing_arc_deg
                    + sum(c[0] for c in setup.cone.values())) if self.flags.get("null_leaks") else 0.0
            return _fr("cap", enemy, firing=((0, 0, 0),), fus=(leak, 0.0), survivors=(16, 16))
        if role == "play" and self.flags.get("arc_param_leaks") and "OM_TP_FIRING_ARC_DEG" in s:
            return _fr("side0", enemy, margin=0.9)
        if role == "play" and self.flags.get("cone_zero_leaks") and any(c[0] == 0 for c in setup.cone.values()):
            return _fr("side0", enemy, margin=0.9)
        if (self.flags.get("defects") and role == "play" and enemy == sweep.ENEMY_FROM and setup.max_ticks != sweep.CONTROL_MAX_TICKS
                and setup.unit_types["_play"] not in ("mirror", "numbers", "planted") and seed < 2 and not swap):
            return _fr("cap" if seed == 0 else "draw", enemy)           # one cap and one draw in the smallest cell of every play scan
        if role == "play" and s.get(V1) == 0.0:
            if self.flags.get("vision_zero_shoots"):
                return _fr("cap", enemy, fus=(1.0, 1.0), survivors=(10, 12))
            return _fr("cap", enemy, firing=((0, 0, 0),), fus=(0.0, 0.0), survivors=(16, 16))
        be = self.be_of(setup)
        if self.arc_be is not None:
            be = self.arc_be(role, setup.firing_arc_deg)
        if self.cone_be is not None:
            be = self.cone_be(role, setup.cone)
        out = _fr("side0" if be is not None and enemy <= be else "side1", enemy)
        d = s.get("OM_TP_DAMAGE_UP_1")
        if role == "play" and d is not None and enemy == 16 and setup.unit_types["_play"] not in self.flags.get("damage_inert_plays", ()):
            window = (12.75 * d, 9.25) if self.flags.get("damage_count_moves") else (12.75, 9.25)
            out = dataclasses.replace(out, margin=0.5 if self.flags.get("damage_blind") else 0.5 * d, firing=[],
                                      firing_window=window, weighted_window=window)
        return out


def run(tmp_path, family, world=None, plays=("p2",), layouts=None, caps_=None, builds=None, **kw):
    world = world or World()
    entry = sweep.run_family(family, tmp_path, builds=builds or fake_builds(), layouts=layouts or {"A": {"id": 1}}, plays=plays,
                             fight_fn=world, caps=caps_ or caps(), **kw)
    return entry, world


def read(tmp_path, family):
    with open(tmp_path / ("sweep_%s.csv" % family), newline="") as fh:
        return list(csv.DictReader(fh))


def test_run_family_writes_the_csv_with_the_pinned_columns_and_the_summary_entry(tmp_path):
    entry, world = run(tmp_path, "range_up")
    rows = read(tmp_path, "range_up")
    assert entry["csv"] == "sweep_range_up.csv" and entry["skipped"] is None and entry["rows"] == len(rows) > 0
    assert {"family", "play", "layout", "kind", "enemy_heads", "knob", "knob_value", "baseline", "ceiling_hit", "prefight", "outcome",
            "predicted_count", "predicted_type", "agreement", "firing_window_0", "weighted_window_0"} <= set(rows[0])
    assert {r["family"] for r in rows} == {"range_up"} and {r["play"] for r in rows} == {"p2"} and {r["layout"] for r in rows} == {"A"}
    assert {r["knob"] for r in rows} == {"OM_TP_RANGE_UP_1"} and {r["prefight"] for r in rows} == {"ok"}
    assert {r["kind"] for r in rows} >= {"grid", "control_null"}
    assert {float(r["knob_value"]) for r in rows if r["kind"] == "grid"} == {1.0, 0.75, 0.5, 0.25}
    assert {r["outcome"] for r in rows} <= {"side0", "side1", "draw", "cap"}


def test_every_cell_is_three_replicates_in_both_orders_and_no_fight_repeats(tmp_path):
    """3 replicates per cell: 6 fights per (point, role, headcount), each (seed, swap) once."""
    _, world = run(tmp_path, "range_up")          # not damage_up: its positive control may repeat a grid cell's fights
    groups = {}
    for c in world.calls:
        if c["max_ticks"] == sweep.CONTROL_MAX_TICKS:
            continue            # the control cells are their own cells (test_vision_controls_...)
        groups.setdefault((c["role"], tuple(sorted(c["settings"].items())), c["enemy"]), []).append((c["seed"], c["swap"]))
    assert groups and all(sorted(v) == sorted((s, w) for s in range(3) for w in (False, True)) for v in groups.values())
    assert len(world.calls) == len({c["key"] for c in world.calls})


def test_replicates_keyword_changes_the_cell_size(tmp_path):
    _, world = run(tmp_path, "range_up", replicates=2)
    sizes = {}
    for c in world.calls:
        if c["max_ticks"] == sweep.CONTROL_MAX_TICKS:
            continue
        sizes.setdefault((c["role"], tuple(sorted(c["settings"].items())), c["enemy"]), []).append(1)
    assert {len(v) for v in sizes.values()} == {4}


def test_the_scan_range_is_eight_to_forty_eight_by_bisection_not_forty_one_cells(tmp_path):
    """Ruling 4 and the 90 s mark: the play and each baseline are scanned from 8 to 48 enemy units, and the bisection fights at
    most 14 of the 41 headcounts per scan."""
    _, world = run(tmp_path, "damage_up")
    for role in ("play", "naive_attacker"):
        heads = sorted({c["enemy"] for c in world.calls if c["role"] == role and c["settings"].get("OM_TP_DAMAGE_UP_1") == 1.0
                        and c["play"] == "p2"})            # not the designated control fight on s3_types_by_reach (decisions 22)
        assert heads[0] == 8 and heads[-1] == 48 and len(heads) <= 14, (role, heads)


def test_both_baselines_are_run_and_reported_for_a_plain_play(tmp_path):
    entry, world = run(tmp_path, "range_up", plays=("s2_concave",))
    rows = read(tmp_path, "range_up")
    assert {c["role"] for c in world.calls} == {"play", "reach_zero", "naive_attacker", "naive_defender"}
    assert {r["baseline"] for r in rows if r["kind"] == "grid"} == {"none", "naive_attacker", "naive_defender"}
    assert {r["baseline"] for r in rows if r["kind"] == "control_null"} == {"none"}


def test_a_layer_play_gets_the_naive_defender_twice_on_the_attackers_layer_and_on_the_plays(tmp_path):
    entry, world = run(tmp_path, "range_up", plays=("s3_layer_above",))
    rows = read(tmp_path, "range_up")
    assert {r["baseline"] for r in rows if r["kind"] == "grid"} == {"none", "naive_attacker", "naive_defender_attacker_layer",
                                                                     "naive_defender_play_layer"}
    assert sweep.baseline_roles("s3_layer_above") == ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer")
    assert sweep.baseline_roles("s2_concave") == ("naive_attacker", "naive_defender")
    assert sweep.baseline_roles("s3_types_by_reach")[1:] == ("naive_defender_attacker_layer", "naive_defender_play_layer")


def test_states_are_on_for_every_sweep_fight_controls_included(tmp_path):
    """Harness spec rev 2: Setup.states is on for sweep and smoke."""
    _, world = run(tmp_path, "vision")
    assert world.calls and all(c["states"] is True for c in world.calls)


def test_a_ceiling_hit_marks_every_row_of_that_scan_and_only_that_scan(tmp_path):
    """The play wins at every headcount (beats the top of 8..48): ceiling_hit 1 on the play's rows, 0 on a baseline that loses."""
    entry, _ = run(tmp_path, "range_up", world=World(be_of=lambda role, s: 99 if role == "play" else 16))
    rows = read(tmp_path, "range_up")
    play = [r for r in rows if r["baseline"] == "none" and r["kind"] == "grid"]
    base = [r for r in rows if r["baseline"] == "naive_attacker"]
    assert play and {r["ceiling_hit"] for r in play} == {"1"} and base and {r["ceiling_hit"] for r in base} == {"0"}
    assert entry["refined"] == []        # a play that beats everything everywhere has no sign change to refine


def test_the_refinement_adds_the_two_rounds_between_the_bracketing_values_and_nothing_else(tmp_path):
    """Play break-even 20 at range 1.0 and 0.75, 12 below; the naive attacker is 16 everywhere. The gain changes sign between 0.75
    and 0.5: refined points 0.625 and 0.6875 (kind `refined`), every cell at them fought like any other, the band kept."""
    be = lambda role, s: (20 if s.get("OM_TP_RANGE_UP_1", 1.0) >= 0.75 else 12) if role == "play" else 16
    entry, world = run(tmp_path, "range_up", world=World(be_of=be))
    rows = read(tmp_path, "range_up")
    refined = {float(r["knob_value"]) for r in rows if r["kind"] == "refined"}
    assert refined == {0.625, 0.6875} and entry["refined"] == [0.625, 0.6875]
    assert {r["baseline"] for r in rows if r["kind"] == "refined"} == {"none", "naive_attacker", "naive_defender"}
    assert all(sweep.in_band(v, 1.0) for v in refined)
    assert {float(r["knob_value"]) for r in rows if r["kind"] == "grid"} == {1.0, 0.75, 0.5, 0.25}


def test_no_sign_change_means_no_refined_row(tmp_path):
    for be in (lambda role, s: 25 if role == "play" else 16, lambda role, s: 10 if role == "play" else 16):
        entry, _ = run(tmp_path, "range_up", world=World(be_of=be))
        assert entry["refined"] == [] and "refined" not in {r["kind"] for r in read(tmp_path, "range_up")}


def _be_range(play, attacker=16, defender=lambda v: 16):
    """A range_up world: the play's break-even follows `play(v)` (None: lost everywhere; 99: beats the top of 8 to 48), the naive
    attacker's is `attacker` and the naive defender's `defender(v)`, v being the range-up value of the cell."""
    def be(role, s):
        v = s.get("OM_TP_RANGE_UP_1", 1.0)
        return play(v) if role == "play" else defender(v) if role.startswith("naive_defender") else attacker
    return be


def test_a_gain_against_the_naive_attacker_that_is_positive_but_negative_against_the_naive_defender_lists_a_second_crossing(tmp_path):
    """Decisions 21: refinement follows the sign against the naive attacker; the crossing against the naive defender is listed in
    its own entry. Play break-even 20 from range-up 0.7 up, 12 below; attacker 16; defender 18 from 0.9 up, 22 below. Gains against
    the attacker: +4 +4 -4 -4 (1.0 .. 0.25), against the defender +2 -2 -10 -10. Attacker crossing: 0.75|0.5, refined 0.625 and
    0.6875. Defender crossing: 1.0|0.75, refined 0.875 (still negative) and 0.9375 (positive)."""
    be = _be_range(lambda v: 20 if v >= 0.7 else 12, defender=lambda v: 18 if v >= 0.9 else 22)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=be))
    assert entry["refined_vs"] == {"naive_attacker": [0.625, 0.6875], "naive_defender": [0.875, 0.9375]}
    assert entry["refined"] == [0.625, 0.6875, 0.875, 0.9375]
    rows = read(tmp_path, "range_up")
    assert {float(r["knob_value"]) for r in rows if r["kind"] == "refined"} == {0.625, 0.6875, 0.875, 0.9375}
    assert {r["baseline"] for r in rows if r["kind"] == "refined"} == {"none", "naive_attacker", "naive_defender"}


def test_the_naive_defender_alone_flipping_does_not_move_the_attacker_refinement(tmp_path):
    """Positive control for the test above, the other way round: the defender's gain changes sign and the attacker's never does."""
    be = _be_range(lambda v: 20, attacker=10, defender=lambda v: 18 if v >= 0.9 else 22)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=be))
    assert entry["refined_vs"]["naive_attacker"] == [] and entry["refined_vs"]["naive_defender"] == [0.875, 0.9375]
    assert entry["refined"] == [0.875, 0.9375]


def test_a_meeting_has_no_holder_so_no_second_crossing_and_a_play_with_a_holder_has_one(tmp_path, monkeypatch):
    """Decisions 24: the second listed crossing goes to every play whose baseline_roles carries a naive_defender* role (a holder), and
    to no other. p_meet is a meeting (no holder): its roles are the naive attacker alone. The defender's gain changes sign, the
    attacker's never does, so the second crossing exists exactly where a defender baseline is run."""
    real = sweep.baseline_roles
    monkeypatch.setattr(sweep, "baseline_roles", lambda play: ("naive_attacker",) if play == "p_meet" else real(play))
    be = _be_range(lambda v: 20, attacker=10, defender=lambda v: 18 if v >= 0.9 else 22)
    entry, world = run(tmp_path / "meet", "range_up", world=World(be_of=be), plays=("p_meet",))
    assert set(entry["refined_vs"]) == {"naive_attacker"} and entry["refined"] == [] and entry["refined_vs"]["naive_attacker"] == []
    assert not [c for c in world.calls if c["role"].startswith("naive_defender")]
    assert {r["baseline"] for r in read(tmp_path / "meet", "range_up")} <= {"none", "naive_attacker"}
    entry, _ = run(tmp_path / "both", "range_up", world=World(be_of=be), plays=("p_meet", "p2"))        # positive control: a holder play adds it
    assert entry["refined_vs"]["naive_defender"] == [0.875, 0.9375] and set(entry["refined_vs"]) == {"naive_attacker", "naive_defender"}


def test_a_layer_play_lists_a_crossing_per_defender_baseline(tmp_path):
    be = _be_range(lambda v: 20 if v >= 0.7 else 12, defender=lambda v: 16)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=be), plays=("s3_layer_above",))
    assert set(entry["refined_vs"]) == set(sweep.baseline_roles("s3_layer_above")) == {
        "naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer"}
    assert all(v == [0.625, 0.6875] for v in entry["refined_vs"].values())


def test_a_gain_of_exactly_zero_is_not_a_sign_change(tmp_path):
    """Strictly greater: a play that ties its baseline (gain 0) is not ahead. Tie above the line, loss below: no change at all;
    tie below the line, win above: the one change is between the win and the tie (0.75|0.5)."""
    tie_then_loss = _be_range(lambda v: 16 if v >= 0.7 else 12)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=tie_then_loss))
    assert entry["refined"] == [] and entry["refined_vs"]["naive_attacker"] == []
    win_then_tie = _be_range(lambda v: 20 if v >= 0.7 else 16)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=win_then_tie))
    assert entry["refined_vs"]["naive_attacker"] == [0.625, 0.6875] and entry["refined"] == [0.625, 0.6875]


def test_a_play_with_no_break_even_counts_as_no_gain_not_as_a_gain(tmp_path):
    """A play lost at every headcount (beats None) below range-up 0.7 and 20 above: against a naive attacker at 16 the gain is positive
    above and not positive below, so the change is found and refined. (A None counted as a gain would hide it.)"""
    be = _be_range(lambda v: 20 if v >= 0.7 else None)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=be))
    assert entry["refined_vs"]["naive_attacker"] == [0.625, 0.6875]


def test_a_baseline_with_no_break_even_is_no_gain_for_the_baseline_too(tmp_path):
    """The other side of the None rule: a play at 20 against a naive attacker that loses everywhere (None) is ahead at every point,
    and a play that also loses everywhere is level (gain 0): no sign change in either, nothing refined."""
    entry, _ = run(tmp_path, "range_up", world=World(be_of=_be_range(lambda v: 20, attacker=None)))
    assert entry["refined"] == []
    entry, _ = run(tmp_path, "range_up", world=World(be_of=_be_range(lambda v: None, attacker=None)))
    assert entry["refined"] == []


def test_a_ceiling_hit_at_one_coarse_point_counts_as_the_top_of_the_range(tmp_path):
    """Range-up 1.0 beats every headcount (ceiling hit, break-even 48); 0.75 is 20, below 0.7 it is 12, attacker 16. Gains +32 +4 -4 -4:
    the one change is 0.75|0.5. (A ceiling hit read as 'no break-even' would invent a second change between 0.75 and 1.0.)"""
    be = _be_range(lambda v: 99 if v >= 0.9 else 20 if v >= 0.7 else 12)
    entry, _ = run(tmp_path, "range_up", world=World(be_of=be))
    rows = read(tmp_path, "range_up")
    assert {r["ceiling_hit"] for r in rows if r["baseline"] == "none" and r["kind"] == "grid" and float(r["knob_value"]) == 1.0} == {"1"}
    assert entry["refined_vs"]["naive_attacker"] == [0.625, 0.6875] and entry["refined"] == [0.625, 0.6875]


def test_a_play_and_a_baseline_both_at_the_ceiling_are_level(tmp_path):
    entry, _ = run(tmp_path, "range_up", world=World(be_of=_be_range(lambda v: 99, attacker=99)))
    assert entry["refined"] == []


def test_vision_refines_between_the_bracketing_pair_with_both_layers_at_the_ratio(tmp_path):
    """Play break-even 20 from vision 0.35 up, 12 below; attacker 16. The change is 0.25|0.5: the arithmetic midpoint 0.375 (ahead),
    then 0.3125 (behind). A refined vision point carries the same two-layer settings as a grid point."""
    be = lambda role, s: (20 if s.get(V1, 0.5) >= 0.35 else 12) if role == "play" else 16
    entry, world = run(tmp_path, "vision", world=World(be_of=be))
    assert entry["refined"] == [0.3125, 0.375]
    for v in (0.3125, 0.375):
        calls = [c for c in world.calls if c["settings"].get(V1) == v and c["role"] == "play"]
        assert calls and all(c["settings"][V2] == pytest.approx(0.4 * v) and c["settings"]["OM_TP_VISION_DOWN_1"] == v for c in calls)
        assert all(sweep.in_band(c["settings"][V1], 0.5) for c in calls)


def test_damage_up_refines_by_the_arithmetic_midpoint(tmp_path):
    be = lambda role, s: (20 if s.get("OM_TP_DAMAGE_UP_1", 1.0) >= 0.7 else 12) if role == "play" else 16
    entry, _ = run(tmp_path, "damage_up", world=World(be_of=be))
    assert entry["refined"] == [0.625, 0.6875]


def test_arc_refines_between_the_bracketing_arcs_by_the_arithmetic_midpoint(tmp_path):
    """Play break-even 20 from an arc of 200 degrees up, 12 below; attacker 16. Coarse 360, 270, 180, 120, 90: the change is
    270|180, so 225 (ahead), then 202.5 (ahead). The refined points go to the world as firing_arc_deg."""
    arc_be = lambda role, arc: (20 if arc >= 200 else 12) if role == "play" else 16
    entry, world = run(tmp_path, "arc", world=World(arc_be=arc_be), plays=("s2_concave",))
    assert entry["refined"] == [202.5, 225.0]
    assert {c["extra"]["arc"] for c in world.calls if c["role"] == "play"} >= {225.0, 202.5}
    assert all(sweep.in_band(v, 360.0) for v in entry["refined"])
    assert {float(r["knob_value"]) for r in read(tmp_path, "arc") if r["kind"] == "refined"} == {202.5, 225.0}


@pytest.mark.parametrize("family,world_kw", [
    ("emitting", dict(be_of=lambda role, s: (20 if s.get("OM_TP_EMIT_SIGHT_MULT", 2.0) >= 2.0 else 12) if role == "play" else 16)),
    ("cone", dict(cone_be=lambda role, cone: (20 if cone and cone["Vanguard"][0] >= 300 else 12) if role == "play" else 16)),
    ("sign_flip", dict(be_of=lambda role, s: (20 if "OM_TP_RANGE_UP_1" in s and s["OM_TP_RANGE_UP_1"] > 1.0 else 12) if role == "play" else 16)),
])
def test_emitting_cone_and_sign_flip_never_refine_even_with_a_sign_change(tmp_path, family, world_kw):
    """Only vision, range_up, damage_up and arc refine. Each world here has a gain that changes sign across the family's points."""
    plays_ = ("s3_dark_striker",) if family == "emitting" else ("s2_concave",) if family == "cone" else ("p2",)
    entry, _ = run(tmp_path, family, world=World(**world_kw), plays=plays_)
    rows = read(tmp_path, family)
    assert entry["refined"] == [] and "refined" not in {r["kind"] for r in rows}
    gains = {(r["knob"], r["knob_value"]) for r in rows if r["kind"] in ("grid", "sign_flip")}
    assert len(gains) >= 2          # positive control: the family has several points the gain could change across


def test_the_sign_flip_family_writes_its_own_labelled_file(tmp_path):
    entry, _ = run(tmp_path, "sign_flip")
    rows = read(tmp_path, "sign_flip")
    assert {r["kind"] for r in rows} == {"sign_flip"} and {(r["knob"], float(r["knob_value"])) for r in rows} == {
        ("OM_TP_RANGE_UP_1", 2.0), ("OM_TP_DAMAGE_UP_1", 2.0)}
    assert entry["refined"] == []


# ---- the controls through the family run ---------------------------------------------------------------------------------------

def test_vision_controls_pass_on_a_faithful_world_and_the_null_control_runs_reach_zero(tmp_path):
    entry, world = run(tmp_path, "vision")
    assert entry["controls"]["positive"]["ok"] is True and entry["controls"]["null"]["ok"] is True
    zero = [c for c in world.calls if c["settings"].get(V1) == 0.0]
    assert zero and {c["enemy"] for c in zero} == {16} and {c["role"] for c in zero} == {"play"}
    assert {c["max_ticks"] for c in zero} == {sweep.CONTROL_MAX_TICKS} and sweep.CONTROL_MAX_TICKS < 12000      # no 12000-tick no-shot fights
    nulls = [c for c in world.calls if c["role"] == "reach_zero"]
    assert nulls and {c["enemy"] for c in nulls} == {16} and {c["max_ticks"] for c in nulls} == {sweep.CONTROL_MAX_TICKS}
    assert {c["settings"][V1] for c in nulls} == {0.125, 0.25, 0.5, 1.0}


def test_the_vision_positive_control_detector_fires_when_vision_zero_still_shoots(tmp_path):
    entry, _ = run(tmp_path, "vision", world=World(vision_zero_shoots=True))
    assert entry["controls"]["positive"]["ok"] is False and entry["controls"]["null"]["ok"] is True


def test_the_null_control_detector_fires_when_reach_zero_rows_differ_across_the_points(tmp_path):
    for fam in ("vision", "range_up"):
        entry, _ = run(tmp_path, fam, world=World(null_leaks=True), plays=("s2_concave",))
        assert entry["controls"]["null"]["ok"] is False, fam
        entry, _ = run(tmp_path, fam, plays=("s2_concave",))
        assert entry["controls"]["null"]["ok"] is True, fam


def test_the_arc_null_control_runs_the_real_play_at_360_set_and_unset_and_its_detector_fires(tmp_path):
    entry, world = run(tmp_path, "arc", plays=("s2_concave",))
    assert entry["controls"]["null"]["ok"] is True and "positive" not in entry["controls"]
    ctl = [c for c in world.calls if c["max_ticks"] == sweep.CONTROL_MAX_TICKS]
    assert ctl and {c["role"] for c in ctl} == {"play"} and {c["enemy"] for c in ctl} == {16}        # no reach-zero build for arc
    assert {"OM_TP_FIRING_ARC_DEG" in c["settings"] for c in ctl} == {True, False}
    assert {c["settings"]["OM_TP_FIRING_ARC_DEG"] for c in ctl if "OM_TP_FIRING_ARC_DEG" in c["settings"]} == {360.0}
    assert {c["extra"]["arc"] for c in ctl} == {360.0}
    leaky, _ = run(tmp_path, "arc", world=World(arc_param_leaks=True), plays=("s2_concave",))
    assert leaky["controls"]["null"]["ok"] is False


def test_the_cone_null_control_runs_the_real_play_with_a_zero_range_cone_and_without_and_its_detector_fires(tmp_path):
    entry, world = run(tmp_path, "cone", plays=("s2_concave",))
    assert entry["controls"]["null"]["ok"] is True and "positive" not in entry["controls"]
    ctl = [c for c in world.calls if c["max_ticks"] == sweep.CONTROL_MAX_TICKS]
    assert ctl and {c["role"] for c in ctl} == {"play"} and {c["enemy"] for c in ctl} == {16}
    assert {tuple(sorted(c["extra"]["cone"].items())) for c in ctl} == {(), (("Vanguard", (0.0, 45.0, 1.0)),)}
    leaky, _ = run(tmp_path, "cone", world=World(cone_zero_leaks=True), plays=("s2_concave",))
    assert leaky["controls"]["null"]["ok"] is False


def test_the_damage_controls(tmp_path):
    entry, world = run(tmp_path, "damage_up")
    assert entry["controls"]["positive"]["ok"] is True
    assert {c["max_ticks"] for c in world.calls if c["role"] != "reach_zero"} == {12000}          # no fight but the null control is cut short
    assert {c["max_ticks"] for c in world.calls if c["role"] == "reach_zero"} == {sweep.CONTROL_MAX_TICKS}
    assert run(tmp_path, "damage_up", world=World(damage_blind=True))[0]["controls"]["positive"]["ok"] is False
    assert run(tmp_path, "damage_up", world=World(damage_count_moves=True))[0]["controls"]["positive"]["ok"] is False


def test_the_damage_positive_control_is_one_designated_fight_not_a_conjunction_over_plays(tmp_path):
    """Decisions 22. The control fights s3_types_by_reach whatever plays the run covers; a play that does not respond to damage-up
    (the real s3_layer_above, FINDING-damage-up-layer-above) does not turn the control off; the designated fight not responding does."""
    both = ("s3_layer_above", "s3_types_by_reach")
    entry, world = run(tmp_path / "a", "damage_up", plays=both, world=World(damage_inert_plays=("s3_layer_above",)))
    assert entry["controls"]["positive"]["ok"] is True and entry["controls"]["positive"]["play"] == "s3_types_by_reach"
    rows = read(tmp_path / "a", "damage_up")
    assert {r["play"] for r in rows if r["kind"] == "control_positive"} == {"s3_types_by_reach"}
    assert {r["play"] for r in rows if r["kind"] == "grid"} == set(both)
    entry, world = run(tmp_path / "b", "damage_up", plays=("p2",), world=World())                  # the designated play is not in `plays`
    assert entry["controls"]["positive"]["ok"] is True
    assert {c["play"] for c in world.calls if c["settings"].get("OM_TP_DAMAGE_UP_1") == 0.5 and c["role"] == "play"
            and c["enemy"] == 16 and c["play"] != "p2"} == {"s3_types_by_reach"}
    entry, _ = run(tmp_path / "c", "damage_up", plays=both, world=World(damage_inert_plays=("s3_types_by_reach",)))
    assert entry["controls"]["positive"]["ok"] is False                                           # positive control: the detector still fires


def test_control_rows_are_in_the_csv_with_their_kind(tmp_path):
    run(tmp_path, "vision")
    rows = read(tmp_path, "vision")
    assert {r["kind"] for r in rows} >= {"control_positive", "control_null", "grid"}
    assert {r["enemy_heads"] for r in rows if r["kind"].startswith("control_")} == {"16"}


def test_emitting_is_reported_saturated_at_the_base_vision_not_swept(tmp_path):
    entry, _ = run(tmp_path, "emitting", plays=("s3_dark_striker",))
    assert entry["saturated_at_vision"] == [0.5]
    assert {float(r["knob_value"]) for r in read(tmp_path, "emitting") if r["kind"] == "grid"} == {1.0, 2.0, 4.0}


# ---- defects: caps outside the controls, draws, and the cells that hold them ----------------------------------------------------

CONTROL_KINDS = ("control_positive", "control_null")


def _defects_of(rows):
    """Recount from the CSV: the pinned definition of entry["defects"] (header)."""
    cell = lambda r: (r["play"], r["layout"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    bad = [r for r in rows if r["outcome"] in ("cap", "draw") and not r["kind"].startswith("control_")]
    return {"cap_rows": sum(r["outcome"] == "cap" for r in bad), "draw_rows": sum(r["outcome"] == "draw" for r in rows),
            "cells": len({cell(r) for r in bad})}


def test_a_faithful_world_has_no_defects_and_its_only_caps_are_in_control_kinds(tmp_path):
    """Controls cap by design (CONTROL_MAX_TICKS < 12000): a cap is allowed in a control_* kind and in no other. The vision-zero
    control caps here, so the exclusion is exercised (positive control), and the pinned defect count is still zero."""
    entry, _ = run(tmp_path, "vision")
    rows = read(tmp_path, "vision")
    caps = {r["kind"] for r in rows if r["outcome"] == "cap"}
    assert caps and caps <= set(CONTROL_KINDS)
    assert entry["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0} == _defects_of(rows)


def test_a_cap_or_a_draw_outside_the_controls_is_counted_as_a_defect(tmp_path):
    """The smallest cell of every play scan holds one cap (seed 0) and one draw (seed 1): 4 grid points, so 4 caps, 4 draws, 4 cells."""
    entry, _ = run(tmp_path, "damage_up", world=World(defects=True))
    rows = read(tmp_path, "damage_up")
    assert entry["defects"] == {"cap_rows": 4, "draw_rows": 4, "cells": 4} == _defects_of(rows)
    assert {r["kind"] for r in rows if r["outcome"] == "cap"} - set(CONTROL_KINDS) == {"grid"}      # the detector's input is really there


def test_a_cap_in_a_control_kind_alone_is_not_a_defect_but_a_draw_in_one_is_counted(tmp_path):
    class W(World):
        def __call__(self, setup, seed, swap):
            out = super().__call__(setup, seed, swap)
            if setup.max_ticks == sweep.CONTROL_MAX_TICKS and seed == 0 and not swap:
                return _fr("draw", setup.unit_types["enemy"], fus=out.firing_unit_seconds)
            return out
    entry, _ = run(tmp_path, "vision", world=W())
    rows = read(tmp_path, "vision")
    assert entry["defects"]["cap_rows"] == 0 and entry["defects"]["draw_rows"] == sum(r["outcome"] == "draw" for r in rows) > 0
    assert entry["defects"]["cells"] == 0 and entry["defects"] == _defects_of(rows)


# ---- --full-scan: the linear scan; bisection is the default -------------------------------------------------------------------------

def _play_heads(world, setting="OM_TP_DAMAGE_UP_1", value=1.0):
    return sorted({c["enemy"] for c in world.calls if c["role"] == "play" and c["settings"].get(setting) == value
                   and c["max_ticks"] != sweep.CONTROL_MAX_TICKS and c["play"] == "p2"})      # p2: not the designated damage control


def test_run_family_scans_every_headcount_with_full_scan_and_by_bisection_without(tmp_path):
    _, world = run(tmp_path / "bis", "damage_up")
    assert len(_play_heads(world)) <= 14
    _, world = run(tmp_path / "lin", "damage_up", full_scan=True)
    assert _play_heads(world) == list(range(8, 49))
    _, world = run(tmp_path / "off", "damage_up", full_scan=False)
    assert len(_play_heads(world)) <= 14


def test_the_full_scan_rows_are_a_superset_of_the_bisection_rows(tmp_path):
    run(tmp_path / "bis", "damage_up")
    run(tmp_path / "lin", "damage_up", full_scan=True)
    key = lambda r: (r["play"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    bis = {key(r) for r in read(tmp_path / "bis", "damage_up")}
    lin = {key(r) for r in read(tmp_path / "lin", "damage_up")}
    assert bis < lin


def test_run_hands_full_scan_to_every_family(tmp_path, monkeypatch):
    got = []
    monkeypatch.setattr(sweep, "run_family", lambda name, out_dir, **kw: got.append((name, kw.get("full_scan", False))) or {"family": name, "csv": None})
    sweep.run(["damage_up", "arc"], tmp_path / "a", builds=fake_builds(), layouts={"A": {}}, fight_fn=World(), full_scan=True)
    sweep.run(["damage_up"], tmp_path / "b", builds=fake_builds(), layouts={"A": {}}, fight_fn=World())
    assert got == [("damage_up", True), ("arc", True), ("damage_up", False)]


def test_smoke_scans_every_headcount_with_full_scan_and_by_bisection_without(tmp_path):
    _, world, _ = _smoke(tmp_path / "bis", control_builds=control_builds())
    plays_ = set(sweep.PLAYS_BY_FAMILY["vision"])
    heads = lambda w: sorted({c["enemy"] for c in w.calls if c["play"] in plays_ and c["role"] == "play"})
    assert len(heads(world)) <= 14
    _, world, _ = _smoke(tmp_path / "lin", control_builds=control_builds(), full_scan=True)
    assert heads(world) == list(range(8, 49))


# ---- prefight refusals -------------------------------------------------------------------------------------------------------

def test_a_refused_cell_is_not_fought_and_is_listed_the_other_plays_still_run(tmp_path):
    log = []
    refuse = {("p_bad", "play"): "no_reach"}
    entry, world = run(tmp_path, "damage_up", plays=("p_bad", "p_ok"), builds=fake_builds(refuse=refuse, log=log))
    assert not [c for c in world.calls if c["play"] == "p_bad"]
    assert [c for c in world.calls if c["play"] == "p_ok"]
    assert [(r["play"], r["layout"], r["reason"]) for r in entry["refused"]] == [("p_bad", "A", "no_reach")]
    assert {r["play"] for r in read(tmp_path, "damage_up") if not r["kind"].startswith("control_")} == {"p_ok"}


def test_positive_control_with_nothing_refused_the_list_is_empty(tmp_path):
    entry, _ = run(tmp_path, "damage_up")
    assert entry["refused"] == []


def test_prefight_is_checked_at_the_smallest_and_largest_headcount(tmp_path):
    """Whether the units fit can depend on the headcount: a build refused only at 48 is refused."""
    seen = []

    def builds(play, role, layout):
        def build(enemy_heads, swap):
            seen.append(enemy_heads)
            build.labels["prefight"] = "no_fit" if enemy_heads == 48 and role == "play" else "ok"
            return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": play, "_role": role})
        build.labels = {"prefight": None}
        return build

    entry, world = run(tmp_path, "damage_up", builds=builds)
    assert {8, 48} <= set(seen) and not [c for c in world.calls if c["play"] == "p2"] and entry["refused"] and entry["refused"][0]["reason"] == "no_fit"


# ---- skipped families ---------------------------------------------------------------------------------------------------------

def test_arc_and_cone_are_skipped_with_a_recorded_reason_when_the_library_lacks_them(tmp_path):
    for fam, word in (("arc", "OM_TP_FIRING_ARC_DEG"), ("cone", "om_roster_set_cone")):
        entry, world = run(tmp_path, fam, caps_=caps(arc=False, cone=False), plays=("s2_concave",))
        assert word in entry["skipped"] and entry["csv"] is None and entry["rows"] == 0 and world.calls == []
        assert not (tmp_path / ("sweep_%s.csv" % fam)).exists()


def test_arc_and_cone_run_when_the_library_has_them_and_pass_the_setup_fields_through(tmp_path):
    entry, world = run(tmp_path, "arc", plays=("s2_concave",))
    assert entry["skipped"] is None and {c["extra"]["arc"] for c in world.calls if c["role"] == "play"} >= {360.0, 270.0, 180.0, 120.0, 90.0}
    entry, world = run(tmp_path, "cone", plays=("s2_concave",))
    cones = [c["extra"]["cone"] for c in world.calls if c["role"] == "play"]
    assert {tuple(c["Vanguard"]) for c in cones if c} >= {(150, 22.5, 1.0), (600, 90, 1.0)}


# ---- run() and the sweep_summary.json -------------------------------------------------------------------------------------------

def test_run_calls_the_families_in_the_given_order_and_writes_the_summary(tmp_path, monkeypatch):
    order = []
    monkeypatch.setattr(sweep, "run_family", lambda name, out_dir, **kw: order.append(name) or {"family": name, "skipped": None, "csv": "sweep_%s.csv" % name})
    summary = sweep.run(list(sweep.FAMILY_ORDER), tmp_path, builds=fake_builds(), layouts={"A": {}}, fight_fn=World())
    assert order == list(sweep.FAMILY_ORDER)
    on_disk = json.loads((tmp_path / "sweep_summary.json").read_text())
    assert on_disk == json.loads(json.dumps(summary)) and on_disk["order"] == list(sweep.FAMILY_ORDER)
    assert list(on_disk["families"]) == list(sweep.FAMILY_ORDER)


def test_run_writes_the_skipped_family_into_the_summary_and_no_file(tmp_path):
    summary = sweep.run(["damage_up", "arc", "cone"], tmp_path, builds=fake_builds(), layouts={"A": {}}, plays=("s2_concave",),
                        fight_fn=World(), caps=caps(arc=False, cone=False))
    on_disk = json.loads((tmp_path / "sweep_summary.json").read_text())
    assert on_disk["families"]["damage_up"]["skipped"] is None and on_disk["families"]["damage_up"]["csv"] == "sweep_damage_up.csv"
    assert "OM_TP_FIRING_ARC_DEG" in on_disk["families"]["arc"]["skipped"] and "om_roster_set_cone" in on_disk["families"]["cone"]["skipped"]
    assert sorted(p.name for p in tmp_path.glob("sweep_*.csv")) == ["sweep_damage_up.csv"] and json.loads(json.dumps(summary)) == on_disk


def test_run_is_byte_identical_twice(tmp_path):
    for d in ("a", "b"):
        sweep.run(["damage_up", "sign_flip"], tmp_path / d, builds=fake_builds(), layouts={"A": {}}, plays=("p2",), fight_fn=World(), caps=caps())
    for name in ("sweep_damage_up.csv", "sweep_sign_flip.csv", "sweep_summary.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes(), name


def test_workers_go_through_the_pool_and_give_the_same_rows(tmp_path, monkeypatch):
    """workers=1 and map_fn None fights in-process through fight_fn; workers=3 builds pool.FightPool(3, lean=True) and fights through
    its map. The rows are the same bytes. (sweep reaches the pool as `pool.FightPool`, so this patch holds.)"""
    FakePool.instances.clear()
    FakePool.fight_fn = World()
    monkeypatch.setattr(pool, "FightPool", FakePool)
    sweep.run(["damage_up"], tmp_path / "w3", workers=3, builds=fake_builds(), layouts={"A": {}}, plays=("p2",), caps=caps())
    sweep.run(["damage_up"], tmp_path / "w1", workers=1, builds=fake_builds(), layouts={"A": {}}, plays=("p2",), fight_fn=World(), caps=caps())
    assert len(FakePool.instances) == 1 and FakePool.instances[0].workers == 3 and FakePool.instances[0].lean is True
    assert FakePool.instances[0].maps
    assert (tmp_path / "w3" / "sweep_damage_up.csv").read_bytes() == (tmp_path / "w1" / "sweep_damage_up.csv").read_bytes()


# ---- smoke ----------------------------------------------------------------------------------------------------------------------

def test_the_smoke_layouts_are_81_78_192_of_layout_run_1():
    assert sweep.SMOKE_LAYOUTS == ("81", "78", "192")
    assert sweep.smoke_layouts() == {
        "81": {"blocked_layer_top": 4, "choke_width_bodies": 2, "cover_density_corridor": 0.3, "detour_ratio": 0, "lane_count": 2, "start_distance": 1400},
        "78": {"blocked_layer_top": 4, "choke_width_bodies": 4, "cover_density_corridor": 0, "detour_ratio": 1.5, "lane_count": 1, "start_distance": 1400},
        "192": {"blocked_layer_top": 0, "choke_width_bodies": 8, "cover_density_corridor": 0, "detour_ratio": 1.5, "lane_count": 0, "start_distance": 2800}}


def test_the_smoke_layouts_are_the_run_1_draw_by_index():
    from scripts.skilllab import depth
    draw = depth.lhs_draw(200, 0)
    assert [draw[i] for i in (81, 78, 192)] == [sweep.smoke_layouts()[k] for k in sweep.SMOKE_LAYOUTS]


def _smoke(tmp_path, world=None, workers=1, **kw):
    world = world or World()
    summary = sweep.run_smoke(tmp_path, workers=workers, builds=fake_builds(), fight_fn=world, **kw)
    with open(tmp_path / "smoke.csv", newline="") as fh:
        return summary, world, list(csv.DictReader(fh))


def control_builds():
    return {name: (lambda enemy_heads, swap, name=name: Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": name, "_role": "play"}))
            for name in ("mirror", "numbers", "planted")}


def test_smoke_runs_vision_half_only_on_the_three_layouts_plus_the_three_controls(tmp_path):
    summary, world, rows = _smoke(tmp_path, control_builds=control_builds())
    vision = [r for r in rows if r["family"] == "vision"]
    assert {r["layout"] for r in vision} == {"81", "78", "192"} and {float(r["knob_value"]) for r in vision} == {0.5}
    assert {r["play"] for r in vision} == set(sweep.PLAYS_BY_FAMILY["vision"]) == {"s3_layer_above", "s3_types_by_reach"}
    ctl = [r for r in rows if r["family"] == "controls"]
    assert all(r["kind"].startswith("control_") for r in ctl) and not any(r["kind"].startswith("control_") for r in vision)
    assert {r["play"] for r in ctl} == {"mirror", "numbers", "planted"}
    assert {(r["play"], r["enemy_heads"]) for r in ctl} == {("mirror", "16"), ("numbers", "8"), ("planted", "16")}
    assert {c["settings"].get(V1) for c in world.calls if c["play"] in sweep.PLAYS_BY_FAMILY["vision"]} == {0.5}


def test_smoke_has_states_on_and_writes_the_summary_with_the_row_hash_outcomes_and_prefight(tmp_path):
    import hashlib
    summary, world, rows = _smoke(tmp_path, control_builds=control_builds())
    assert world.calls and all(c["states"] is True for c in world.calls)
    on_disk = json.loads((tmp_path / "smoke_summary.json").read_text())
    assert on_disk == json.loads(json.dumps(summary))
    assert on_disk["rows_sha256"] == hashlib.sha256((tmp_path / "smoke.csv").read_bytes()).hexdigest()
    assert set(on_disk["outcomes"]) <= {"side0", "side1", "draw", "cap"} and sum(on_disk["outcomes"].values()) == len(rows)
    assert list(on_disk["prefight"]) == ["ok"] and on_disk["prefight"]["ok"] > 0 and on_disk["refused"] == []


def test_smoke_counts_its_defects_like_a_sweep_entry(tmp_path):
    """The smallest cell of each of the 3 layouts x 2 plays holds one cap and one draw (the play role only): 6 of each, 6 cells.
    A faithful world has none."""
    summary, _, rows = _smoke(tmp_path / "clean", control_builds=control_builds())
    assert summary["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0} == _defects_of(rows)
    assert not [r for r in rows if r["outcome"] == "cap" and not r["kind"].startswith("control_")]      # decisions 23: read from the rows
    summary, _, rows = _smoke(tmp_path / "bad", world=World(defects=True), control_builds=control_builds())
    assert summary["defects"] == {"cap_rows": 6, "draw_rows": 6, "cells": 6} == _defects_of(rows)
    assert len([r for r in rows if r["outcome"] == "cap" and not r["kind"].startswith("control_")]) == 6      # positive control for the row check
    assert json.loads((tmp_path / "bad" / "smoke_summary.json").read_text())["defects"] == summary["defects"]


def test_smoke_lists_the_refused_cells(tmp_path):
    sweep.run_smoke(tmp_path / "r", workers=1, builds=fake_builds(refuse={("s3_layer_above", "play"): "unroutable"}), fight_fn=World(),
                    control_builds=control_builds())
    refused = json.loads((tmp_path / "r" / "smoke_summary.json").read_text())["refused"]
    assert {(r["play"], r["reason"]) for r in refused} == {("s3_layer_above", "unroutable")} and len(refused) == 3      # one per layout


def test_smoke_rows_are_the_same_bytes_at_one_and_twelve_workers(tmp_path, monkeypatch):
    FakePool.instances.clear()
    FakePool.fight_fn = World()
    monkeypatch.setattr(pool, "FightPool", FakePool)
    sweep.run_smoke(tmp_path / "w12", workers=12, builds=fake_builds(), control_builds=control_builds())
    sweep.run_smoke(tmp_path / "w1", workers=1, builds=fake_builds(), control_builds=control_builds(), fight_fn=World())
    assert FakePool.instances[0].workers == 12
    assert (tmp_path / "w12" / "smoke.csv").read_bytes() == (tmp_path / "w1" / "smoke.csv").read_bytes()
    a = json.loads((tmp_path / "w12" / "smoke_summary.json").read_text())
    assert a["rows_sha256"] == json.loads((tmp_path / "w1" / "smoke_summary.json").read_text())["rows_sha256"]


# ---- the commands ------------------------------------------------------------------------------------------------------------------

def test_the_smoke_command_defaults_to_twelve_workers(tmp_path, monkeypatch):
    got = []
    monkeypatch.setattr(sweep, "run_smoke", lambda out_dir, workers=12, **kw: got.append((Path(out_dir), workers)) or {"rows_sha256": "x"})
    assert cli.main(["smoke", "--out", str(tmp_path)]) == 0
    assert cli.main(["smoke", "--out", str(tmp_path), "--workers", "3"]) == 0
    assert got == [(tmp_path, 12), (tmp_path, 3)]


def test_the_sweep_command_runs_all_families_in_order_or_the_named_one(tmp_path, monkeypatch):
    got = []
    monkeypatch.setattr(sweep, "run", lambda families, out_dir, workers=1, **kw: got.append((list(families), Path(out_dir), workers)) or {"families": {}})
    assert cli.main(["sweep", "--out", str(tmp_path)]) == 0
    assert cli.main(["sweep", "all", "--out", str(tmp_path), "--workers", "4"]) == 0
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path)]) == 0
    assert got[0][0] == list(sweep.FAMILY_ORDER) and got[1] == (list(sweep.FAMILY_ORDER), tmp_path, 4) and got[2][0] == ["damage_up"]


def test_the_sweep_command_refuses_an_unknown_family_and_names_the_valid_ones(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(sweep, "run", lambda *a, **k: pytest.fail("must not run"))
    assert cli.main(["sweep", "nonsense", "--out", str(tmp_path)]) == 2
    out = capsys.readouterr().out
    assert all(f in out for f in sweep.FAMILY_ORDER)


def test_the_sweep_command_prints_the_files_it_wrote(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(sweep, "run", lambda families, out_dir, workers=1, **kw: {"families": {"damage_up": {"csv": "sweep_damage_up.csv"}}})
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path)]) == 0
    assert "sweep_summary.json" in capsys.readouterr().out


def test_the_sweep_and_smoke_commands_accept_full_scan_and_default_to_bisection(tmp_path, monkeypatch):
    """Overseer default: `--full-scan` is a CLI flag selecting the linear scan; without it the commands pass nothing or False."""
    got = []
    monkeypatch.setattr(sweep, "run", lambda families, out_dir, workers=1, **kw: got.append(("sweep", bool(kw.get("full_scan", False)))) or {"families": {}})
    monkeypatch.setattr(sweep, "run_smoke", lambda out_dir, workers=12, **kw: got.append(("smoke", bool(kw.get("full_scan", False)))) or {"rows_sha256": "x"})
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path)]) == 0
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path), "--full-scan"]) == 0
    assert cli.main(["smoke", "--out", str(tmp_path)]) == 0
    assert cli.main(["smoke", "--out", str(tmp_path), "--full-scan", "--workers", "2"]) == 0
    assert got == [("sweep", False), ("sweep", True), ("smoke", False), ("smoke", True)]


def test_the_controls_and_reach_commands_accept_full_scan_and_stay_linear(tmp_path, monkeypatch):
    """controls and reach chart a dot per fight at every headcount, so they scan linearly with or without the flag
    (test_main.py and test_main_reach.py pin the default; this pins that the flag is accepted and changes nothing)."""
    from scripts.skilllab import scan as scan_mod
    seen = []
    monkeypatch.setattr(scan_mod, "scan", lambda build, size, lo, hi, **kw: seen.append(kw.get("full_scan")) or (_ for _ in ()).throw(RuntimeError("stop")))
    for argv in (["controls", "--out", str(tmp_path), "--full-scan"], ["reach", "--out", str(tmp_path), "--full-scan"]):
        with pytest.raises(RuntimeError):
            cli.main(argv)
    assert seen == [True, True]


def test_an_unknown_option_is_still_refused(tmp_path, capsys):
    """Positive control for the two tests above: argparse does refuse what it does not know, so 'accepted' means something."""
    with pytest.raises(SystemExit) as exc:
        cli.main(["smoke", "--out", str(tmp_path), "--no-such-flag"])
    assert exc.value.code == 2


# ---- the orders_per_unit default stays True (decisions 23, superseding the L4 flip of decisions 13 and 21) ------------------------------

# Decisions 13 and 21 flipped the Setup default to False in the L4 landing, only because E1 lands in the same landing. Decisions 23
# tightened that: the default flips to the group attack-move only when E1 is in the landing AND the smoke caps zero under group orders.
# Until both hold `orders_per_unit` stays True. The smoke does not (7 of 108 play fights cap on layout 192 under group orders:
# ledger FINDING-group-orders-cap), so the earlier fix pass's ruler rows (ledger TD-LAB-REV2-L4-flip, 13 functions, 42 items) are
# undone: every test about the default asserts True again, and a test about the group order asks for orders_per_unit=False.
def test_the_orders_per_unit_default_is_true_until_e1_is_landed_and_the_smoke_caps_zero_under_group_orders():
    assert Setup(groups=(), unit_types={}).orders_per_unit is True
    f = {f.name: f for f in dataclasses.fields(Setup)}["orders_per_unit"]
    assert f.default is True


def test_the_undone_flip_left_no_test_asserting_the_group_order_as_the_default():
    """The flip rows are undone: no test file asserts `orders_per_unit is False` as the Setup default on a play, a scene or a Setup
    (positive control: the explicit per-unit and group-order calls are still there)."""
    for rel in ("tests/skilllab/test_fight_outcomes.py", "tests/skilllab/test_plays.py", "tests/skilllab/test_asym.py",
                "tests/skilllab/test_placed_by_feature.py", "tests/skilllab/test_objective_scene.py",
                "tests/skilllab/integration/test_slots_real.py", "tests/skilllab/integration/test_sweep_real.py"):
        text = (ROOT / rel).read_text()
        assert ".orders_per_unit is False" not in text, rel
        assert "TD-LAB-REV2-L4-flip" not in text, rel
    assert "orders_per_unit=True" in (ROOT / "tests/skilllab/test_fight_outcomes.py").read_text()
    assert "orders_per_unit=False" in (ROOT / "tests/skilllab/test_fight_outcomes.py").read_text()
    assert "orders_per_unit=True" in (ROOT / "tests/skilllab/test_objective_scene.py").read_text()      # the far-open-ground fight stays per-unit


def _orders(fake):
    return sorted(c[2] for c in fake.calls_named("order_attack_move"))


def test_a_default_setup_issues_one_order_per_unit_and_orders_per_unit_false_one_per_group(seam, monkeypatch):
    """Fight-level proof of both paths on the fake engine (the same harness test_fight_outcomes.py uses)."""
    import scripts.skilllab.fight as fight_mod
    import scripts.skilllab.formations as formations_mod
    from test_fight_outcomes import G, run
    stub = lambda kind, n, x, y, facing_deg, params: [(x + 7.0 * i, y) for i in range(n)]
    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)
    base = dict(groups=(G(0, 3), G(1, 3)), unit_types={}, max_ticks=2, point=(25.0, -40.0))
    _, fake = run(Setup(**base))
    assert _orders(fake) == [[1], [2], [3], [4], [5], [6]]
    _, fake = run(Setup(**base, orders_per_unit=False))
    assert _orders(fake) == [[1, 2, 3], [4, 5, 6]]


def test_the_sweep_and_smoke_builds_do_not_set_orders_per_unit():
    """The orders default is Setup's; sweep.py never overrides it per cell."""
    tree = ast.parse((ROOT / "scripts/skilllab/sweep.py").read_text())
    names = {n.arg for n in ast.walk(tree) if isinstance(n, ast.keyword)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "orders_per_unit" not in names


def test_sweep_module_names_no_retired_field_or_helper():
    src = (ROOT / "scripts/skilllab/sweep.py").read_text()
    for gone in ("mopup", "approach", "stalemate", "decided_by_survivors", "hold_anchor", "placement_shift", "WIN_MARGIN", "weighted="):
        assert gone not in src, gone
