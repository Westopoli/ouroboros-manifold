# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-12
"""plays: shape of the Setup each play builds, the derived types of reach_play and damage_play, contact placement
from the sensor radius, `unit_stats`, and the plays/formations hand-off."""
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.plays as plays  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402
from scripts.skilllab.plays import (  # noqa: E402
    blob_play, damage_play, line_play, reach_play, unit_stats as real_unit_stats)

DEFAULTS = Setup(groups=(), unit_types={})
ALL_PLAYS = [blob_play, line_play, reach_play, damage_play]
BLOB_PLAYS = [blob_play, reach_play, damage_play]
KIND_OF = {blob_play: "blob", line_play: "line", reach_play: "blob", damage_play: "blob"}   # AC-12: reach and damage use blob like blob_play
SENSORS = {"Vanguard": 700.0, "Warden": 500.0, "Raider": 333.5}


def _fake_unit_stats(monkeypatch, table):
    """Replace plays.unit_stats with a fake reading `table` (unit name -> sensor radius); unknown names raise ValueError.
    Returns the list of names it was asked for. No Engine, no compiler."""
    asked = []

    def fake(name):
        asked.append(name)
        if name not in table:
            raise ValueError("unknown unit type %r" % (name,))
        return {"category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
                "speed": 5.0, "sensor_radius": table[name], "layer_transition_time": 0.0, "aoe_radius": 0.0}

    monkeypatch.setattr(plays, "unit_stats", fake)
    return asked


@pytest.fixture(autouse=True)
def _no_engine_in_plays(monkeypatch):
    """Every test except the unit_stats ones builds against a fake sensor table (700 Vanguard, 500 Warden, 333.5 Raider)."""
    _fake_unit_stats(monkeypatch, SENSORS)


def _depth(play, count):
    """AC-12: a side's depth along the axis: blob radius 80 + 12*sqrt(count); 0 for a line."""
    return 0.0 if play is line_play else 80 + 12 * math.sqrt(count)


def _approx(x):
    return pytest.approx(x, abs=1e-6, rel=0)


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_setup_shape_two_groups_facing_each_other(play):
    """AC-12 (Readings): side 0 of `size` at negative x facing 0, side 1 of enemy_heads at positive x facing 180, on the x axis, layer 0."""
    s = play(16)(8, False)
    g0, g1 = s.groups
    assert isinstance(s, Setup) and isinstance(s.groups, tuple) and len(s.groups) == 2
    assert (g0.side, g0.count, g0.y, g0.facing_deg) == (0, 16, 0.0, 0.0)
    assert (g1.side, g1.count, g1.y, g1.facing_deg) == (1, 8, 0.0, 180.0)
    assert g0.x < 0.0 < g1.x
    assert (g0.layer, g1.layer, g0.order, g1.order, g0.goal, g1.goal) == (0, 0, "attack_move", "attack_move", None, None)
    assert isinstance(g0, Group) and g0.formation == g1.formation == KIND_OF[play]


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_setup_flags_default_to_contract_defaults(play):
    """AC-12: abilities off, max_ticks / sample_every left at the Setup defaults (Q-LAB-03: no stalemate_ticks, no mop-up, no approach)."""
    s = play(4)(4, False)
    assert (s.abilities, s.max_ticks, s.sample_every) == (False, DEFAULTS.max_ticks, DEFAULTS.sample_every)


def test_ac12_blob_and_line_params_follow_the_brief():
    """AC-12 (Readings): blob radius = 80 + 12*sqrt(count) per side (blob_play, reach_play, damage_play); line spacing = 30; the two kinds differ."""
    g0, g1 = blob_play(16)(9, False).groups
    assert g0.params["radius"] == pytest.approx(80 + 12 * math.sqrt(16))
    assert g1.params["radius"] == pytest.approx(80 + 12 * math.sqrt(9))
    for play in (reach_play, damage_play):
        r0, r1 = play(16)(9, False).groups
        assert r0.params["radius"] == pytest.approx(80 + 12 * math.sqrt(16))
        assert r1.params["radius"] == pytest.approx(80 + 12 * math.sqrt(9))
    l0, l1 = line_play(16)(9, False).groups
    assert l0.params["spacing"] == l1.params["spacing"] == 30
    assert g0.formation != l0.formation


@pytest.mark.parametrize("play", [blob_play, line_play])
def test_ac12_plain_plays_use_the_same_plain_unit_both_sides_and_no_custom_types(play):
    """AC-12: side 1 uses side 0's unit and formation; naive plays register no types."""
    for unit in ("Vanguard", "Warden"):
        s = play(6, unit=unit)(5, False)
        assert (s.groups[0].unit, s.groups[1].unit, s.unit_types) == (unit, unit, {})
    assert play(6)(5, False).groups[0].unit == "Vanguard"


@pytest.mark.parametrize("play", [reach_play, damage_play])
@pytest.mark.parametrize("heads", [4, 9, 16, 24])
def test_ac12_modified_and_blob_plays_differ_only_in_side_0_unit(play, heads):
    """AC-12: for equal size and enemy_heads, reach_play / damage_play and blob_play build the same groups (placement included) except side 0's unit."""
    plain = blob_play(16)(heads, False)
    modified = play(16)(heads, False)
    for gp, gm in zip(plain.groups, modified.groups):
        assert (gp.side, gp.count, gp.formation, gp.params, gp.x, gp.y, gp.facing_deg, gp.layer, gp.order, gp.goal) == (
            gm.side, gm.count, gm.formation, gm.params, gm.x, gm.y, gm.facing_deg, gm.layer, gm.order, gm.goal)
    assert plain.groups[1].unit == modified.groups[1].unit and plain.groups[0].unit != modified.groups[0].unit
    assert (plain.abilities, plain.max_ticks, plain.sample_every) == (
        modified.abilities, modified.max_ticks, modified.sample_every)


def test_ac12_reach_play_derives_a_long_type_on_side_0_only():
    """AC-12: side 0 uses `<unit>Long` = base unit with attack_range scaled 1.2; side 1 stays plain and has no entry of its own."""
    s = reach_play(16)(8, False)
    entry = s.unit_types["VanguardLong"]
    assert list(s.unit_types) == ["VanguardLong"]
    assert entry["base"] == "Vanguard" and entry["scale"] == {"attack_range": pytest.approx(1.2)}
    assert not entry.get("set")
    assert (s.groups[0].unit, s.groups[1].unit) == ("VanguardLong", "Vanguard")


def test_ac12_reach_play_unit_and_factor_parameters_are_honoured():
    """AC-12: a non-default unit and factor change the type name, base and scale (no hard-coded Vanguard / 1.2)."""
    s = reach_play(10, unit="Warden", factor=1.5)(10, True)
    assert list(s.unit_types) == ["WardenLong"]
    assert s.unit_types["WardenLong"]["base"] == "Warden"
    assert s.unit_types["WardenLong"]["scale"] == {"attack_range": pytest.approx(1.5)}
    assert (s.groups[0].unit, s.groups[1].unit) == ("WardenLong", "Warden")


def test_ac12_damage_play_derives_a_strong_type_on_side_0_only():
    """AC-12: side 0 uses `<unit>Strong` = base unit with base_damage scaled 1.2 (the default factor); side 1 stays plain with no entry of its own."""
    s = damage_play(16)(8, False)
    entry = s.unit_types["VanguardStrong"]
    assert list(s.unit_types) == ["VanguardStrong"]
    assert entry["base"] == "Vanguard" and entry["scale"] == {"base_damage": pytest.approx(1.2)}
    assert not entry.get("set")
    assert (s.groups[0].unit, s.groups[1].unit) == ("VanguardStrong", "Vanguard")
    assert s.groups[0].formation == s.groups[1].formation == "blob"


def test_ac12_damage_play_unit_and_factor_parameters_are_honoured():
    """AC-12: a non-default unit and factor change the type name, base and scaled stat (no hard-coded Vanguard / 1.2); the stat is base_damage, not attack_range."""
    s = damage_play(10, unit="Warden", factor=1.5)(10, True)
    assert list(s.unit_types) == ["WardenStrong"]
    assert s.unit_types["WardenStrong"]["base"] == "Warden"
    assert s.unit_types["WardenStrong"]["scale"] == {"base_damage": pytest.approx(1.5)}
    assert (s.groups[0].unit, s.groups[1].unit) == ("WardenStrong", "Warden")


def test_ac12_damage_and_reach_plays_scale_different_stats():
    """AC-12: the planted control scales damage, the study knob scales range; the two derived entries are not interchangeable."""
    strong = damage_play(16)(8, False).unit_types["VanguardStrong"]
    long_ = reach_play(16)(8, False).unit_types["VanguardLong"]
    assert set(strong["scale"]) == {"base_damage"} and set(long_["scale"]) == {"attack_range"}


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_swap_leaves_the_setup_unchanged(play):
    """AC-12: the spawn order is applied inside fight, so build(n, True) == build(n, False)."""
    build = play(7)
    assert build(5, True) == build(5, False)


@pytest.mark.parametrize("heads", [1, 24])
def test_ac12_counts_side_0_fixed_side_1_follows_enemy_heads(heads):
    """AC-12 (cardinality one / peak): side 0 stays `size`; side 1 is exactly enemy_heads."""
    for play in (reach_play, damage_play):
        s = play(16)(heads, False)
        assert (s.groups[0].count, s.groups[1].count) == (16, heads)
    assert blob_play(1)(heads, False).groups[0].count == 1


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_groups_are_placeable_by_formations_and_stay_on_their_own_half(play):
    """AC-12 interaction with formations.place: each group's kind/params yield `count` points; sides do not overlap."""
    s = play(16)(12, False)
    pts = [place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params) for g in s.groups]
    assert [len(p) for p in pts] == [16, 12]
    assert max(p[0] for p in pts[0]) < 0.0 < min(p[0] for p in pts[1])


def test_ac12_line_plays_place_units_abreast_across_the_facing():
    """AC-12 interaction: a line play's points share one x (perpendicular to facing 0 / 180) and span (n-1)*spacing in y."""
    g0, g1 = line_play(16)(10, False).groups
    for g in (g0, g1):
        pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
        xs = [p[0] for p in pts]
        ys = sorted(p[1] for p in pts)
        assert max(xs) - min(xs) < 1e-4
        assert ys[-1] - ys[0] == pytest.approx((g.count - 1) * 30.0, abs=1e-3)


@pytest.mark.parametrize("play", [reach_play, damage_play])
def test_ac12_modified_play_blob_points_stay_within_the_blob_radius_of_each_anchor(play):
    """AC-12 interaction: reach_play's and damage_play's groups are blobs; every point lies within the group's radius of its anchor."""
    for g in play(16)(10, False).groups:
        pts = place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
        assert g.formation == "blob"
        assert max(math.hypot(p[0] - g.x, p[1] - g.y) for p in pts) <= g.params["radius"] + 1e-5


def test_ac12_build_is_callable_with_keywords_from_the_spec_signature():
    """AC-12: build(enemy_heads, swap) -> Setup, by name as the spec writes it."""
    assert isinstance(blob_play(3)(enemy_heads=4, swap=True), Setup)


@pytest.mark.parametrize("play", ALL_PLAYS)
@pytest.mark.parametrize("size,heads", [(0, 8), (-1, 8), (8, 0), (8, -3)])
def test_ac12_size_or_enemy_heads_below_one_raises_valueerror_when_build_is_called(play, size, heads):
    """AC-12 (Readings): size or enemy_heads < 1 raises ValueError by the time build(enemy_heads, swap) has been called."""
    with pytest.raises(ValueError):
        play(size)(heads, False)


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_unknown_unit_name_fails_in_unit_stats(play):
    """AC-12 (Readings): an unknown unit name fails in `unit_stats`; the ValueError reaches the caller by the time build has been called."""
    with pytest.raises(ValueError):
        play(4, unit="Zebra")(4, False)


@pytest.mark.parametrize("play", [reach_play, damage_play])
@pytest.mark.parametrize("factor", [0.0, -1.2])
def test_ac12_factor_zero_or_negative_raises_valueerror(play, factor):
    """AC-12 (Readings): factor <= 0 raises ValueError (at play creation or at build) for reach_play and damage_play."""
    with pytest.raises(ValueError):
        play(16, factor=factor)(8, False)


def test_ac12_reach_factor_exactly_one_is_allowed():
    """AC-12 (Readings): factor 1.0 is allowed and scales by 1.0."""
    s = reach_play(16, factor=1.0)(8, False)
    assert s.unit_types["VanguardLong"]["scale"] == {"attack_range": pytest.approx(1.0)}


def test_ac12_damage_factor_exactly_one_is_allowed():
    """AC-12 (Readings): factor 1.0 is allowed and scales base_damage by 1.0 (the null control of AC-23)."""
    s = damage_play(16, factor=1.0)(8, False)
    assert s.unit_types["VanguardStrong"]["scale"] == {"base_damage": pytest.approx(1.0)}


# ---- contact placement (AC-12, Westley 2026-10-02) ----

PLACEMENT_TABLES = [{"Vanguard": 700.0, "Warden": 500.0}, {"Vanguard": 500.0, "Warden": 700.0}, {"Vanguard": 90.25, "Warden": 1234.5}]
PLACEMENT_COUNTS = [(16, 9), (9, 16), (1, 24), (24, 1), (4, 4), (1, 1)]


@pytest.mark.parametrize("play", ALL_PLAYS)
@pytest.mark.parametrize("table", PLACEMENT_TABLES)
@pytest.mark.parametrize("size,heads", PLACEMENT_COUNTS)
def test_ac12_anchors_sit_on_the_x_axis_symmetric_at_sensor_plus_one_plus_depths(monkeypatch, play, table, size, heads):
    """AC-12 contact placement: anchors on the x axis, symmetric about 0, S + 1 + d0 + d1 apart; S read from unit_stats (never 700),
    d = 80 + 12*sqrt(count) for blob plays, 0 for line_play. Exact to 1e-6, so a wrong +1, a missing d0 or d1, a literal sensor
    radius, or anchors off-centre (each side offset by its own depth) all fail."""
    _fake_unit_stats(monkeypatch, table)
    for unit in ("Vanguard", "Warden"):
        s = play(size, unit=unit)(heads, False)
        g0, g1 = s.groups
        gap = table[unit] + 1 + _depth(play, size) + _depth(play, heads)
        assert (g0.y, g1.y) == (0.0, 0.0)
        assert g1.x - g0.x == _approx(gap)
        assert g0.x == _approx(-gap / 2) and g1.x == _approx(gap / 2)


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_sensor_radius_is_read_from_unit_stats_of_the_base_unit_only(monkeypatch, play):
    """AC-12: S is `plays.unit_stats(unit)["sensor_radius"]` for the base unit name (both sides use one base unit); the derived
    `<unit>Long` / `<unit>Strong` names are never looked up (they are not built-ins)."""
    asked = _fake_unit_stats(monkeypatch, {"Warden": 640.0})
    s = play(5, unit="Warden")(7, False)
    assert asked and set(asked) == {"Warden"}
    assert s.groups[1].x - s.groups[0].x == _approx(640.0 + 1 + _depth(play, 5) + _depth(play, 7))


def test_ac12_line_play_anchors_are_exactly_sensor_plus_one_apart_whatever_the_counts(monkeypatch):
    """AC-12: a line has depth 0 (no radius term), so its anchors are exactly S + 1 apart for any counts; a blob of the same counts is wider."""
    _fake_unit_stats(monkeypatch, {"Vanguard": 700.0})
    for size, heads in ((1, 1), (16, 9), (24, 24)):
        g0, g1 = line_play(size)(heads, False).groups
        assert g1.x - g0.x == _approx(701.0)
        b0, b1 = blob_play(size)(heads, False).groups
        assert b1.x - b0.x > g1.x - g0.x + 100.0


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ac12_every_unit_starts_at_least_sensor_plus_one_from_every_enemy_unit(play):
    """AC-12 contact: the sides start just outside the sensor radius, so no pair of opposing formation points is closer than S + 1 = 701."""
    g0, g1 = play(16)(9, False).groups
    p0 = place(g0.formation, g0.count, g0.x, g0.y, g0.facing_deg, g0.params)
    p1 = place(g1.formation, g1.count, g1.x, g1.y, g1.facing_deg, g1.params)
    nearest = min(math.hypot(a[0] - b[0], a[1] - b[1]) for a in p0 for b in p1)
    assert nearest >= 701.0 - 1e-5


# ---- unit_stats (AC-12): throwaway world through engine.Engine, once per name, cached ----

class _Log(list):
    """A list that also carries `ids` (name -> type id of the recording fake)."""


def _recording_engine(monkeypatch, stats_by_name):
    """Patch scripts.skilllab.engine.Engine with a recording fake. `stats_by_name` maps a built-in name to its stats dict.
    Returns the log: tuples ("Engine",), ("new_world", w), ("type_id", name), ("type_stats", w, type_id), ("free_world", w)."""
    import scripts.skilllab.engine as engine_mod
    log = _Log()
    ids = {name: 40 + i for i, name in enumerate(sorted(stats_by_name))}
    by_id = {ids[name]: st for name, st in stats_by_name.items()}

    class RecordingEngine:
        def __init__(self, *args, **kwargs):
            log.append(("Engine",))

        def new_world(self, seed):
            w = ("world", len([e for e in log if e[0] == "new_world"]) + 1)
            log.append(("new_world", w))
            return w

        def type_id(self, name):
            log.append(("type_id", name))
            if name not in ids:
                raise ValueError("unknown unit type %r" % (name,))
            return ids[name]

        def type_stats(self, w, type_id):
            log.append(("type_stats", w, type_id))
            return dict(by_id[type_id])

        def free_world(self, w):
            log.append(("free_world", w))

    monkeypatch.setattr(engine_mod, "Engine", RecordingEngine)
    log.ids = ids
    return log


def _stats(sensor, max_hp=100.0):
    return {"category": 1, "max_hp": max_hp, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
            "speed": 5.0, "sensor_radius": sensor, "layer_transition_time": 0.0, "aoe_radius": 0.0}


def test_ac12_unit_stats_returns_type_stats_of_a_throwaway_world_and_frees_it(monkeypatch):
    """AC-12 unit_stats: builds one Engine and one world, reads type_stats of type_id(name) in that world, returns that dict, frees the world after reading."""
    known = {"ProbeCoreA": _stats(611.0, 77.0), "ProbeCoreB": _stats(222.0, 55.0)}
    log = _recording_engine(monkeypatch, known)
    got = real_unit_stats("ProbeCoreA")
    assert got == known["ProbeCoreA"] and got != known["ProbeCoreB"]
    kinds = [e[0] for e in log]
    assert kinds.count("Engine") == 1 and kinds.count("new_world") == 1 and kinds.count("free_world") == 1
    w = [e for e in log if e[0] == "new_world"][0][1]
    assert ("type_id", "ProbeCoreA") in log
    assert ("type_stats", w, log.ids["ProbeCoreA"]) in log
    assert ("free_world", w) in log
    assert kinds.index("free_world") > kinds.index("type_stats") > kinds.index("new_world")


def test_ac12_unit_stats_caches_per_name_and_builds_again_for_a_new_name(monkeypatch):
    """AC-12 unit_stats: a second call for the same name does not construct Engine or a world again; a different name does, and gets its own stats."""
    known = {"ProbeCacheA": _stats(611.0), "ProbeCacheB": _stats(222.0)}
    log = _recording_engine(monkeypatch, known)
    first = real_unit_stats("ProbeCacheA")
    again = real_unit_stats("ProbeCacheA")
    kinds = [e[0] for e in log]
    assert again == first == known["ProbeCacheA"]
    assert kinds.count("Engine") == 1 and kinds.count("new_world") == 1 and kinds.count("type_stats") == 1
    other = real_unit_stats("ProbeCacheB")
    kinds = [e[0] for e in log]
    assert other == known["ProbeCacheB"] and other != first
    assert kinds.count("Engine") == 2 and kinds.count("new_world") == 2 and kinds.count("type_stats") == 2
    assert kinds.count("free_world") == 2          # every throwaway world freed, none leaked


def test_ac12_unit_stats_unknown_name_raises_valueerror(monkeypatch):
    """AC-12 (Readings): an unknown unit name fails in unit_stats; the engine's ValueError from type_id is not swallowed."""
    _recording_engine(monkeypatch, {"ProbeKnown": _stats(300.0)})
    with pytest.raises(ValueError):
        real_unit_stats("ProbeNoSuchUnit")


def _modules_after_import(extra_import=""):
    code = ("import sys\nimport scripts.skilllab.plays\n%s\nprint('scripts.skilllab.engine' in sys.modules)" % extra_import)
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip()


def test_ac12_importing_plays_does_not_import_engine():
    """AC-12: `plays` imports `engine` only inside unit_stats, so importing plays loads no engine module (and needs no compiler)."""
    assert _modules_after_import() == "False"


def test_ac12_import_check_detects_an_engine_import():
    """Positive control for the import check above: the same probe reports True once engine is imported."""
    assert _modules_after_import("import scripts.skilllab.engine") == "True"



# ---------------------------------------------------------------- LAB-REV2-L2 (Q-LAB-03, ruling 6)

@pytest.mark.parametrize("play", ALL_PLAYS)
@pytest.mark.parametrize("heads", [8, 16, 48])
def test_ruling_6_a_meeting_sends_both_sides_to_one_point_between_them(play, heads):
    """Ruling 6: a meeting is both sides attack-moved to one point. The plays carry Setup.point, the midpoint of the two
    anchors (the sides stand symmetric about x = 0 at the contact distance), and leave each group's own goal None."""
    s = play(16)(heads, False)
    g0, g1 = s.groups
    assert s.point == pytest.approx(((g0.x + g1.x) / 2, (g0.y + g1.y) / 2))
    assert (g0.goal, g1.goal) == (None, None)


@pytest.mark.parametrize("play", ALL_PLAYS)
def test_ruling_6_plays_use_the_group_order_default(play):
    """LAB-REV2-L4 ruler (TD-LAB-REV2-L4-flip): plays leave orders_per_unit at the Setup default, which is False since the flip."""
    assert play(16)(8, False).orders_per_unit is False


@pytest.mark.parametrize("play", [blob_play, line_play, reach_play, damage_play])
@pytest.mark.parametrize("kw", ["approach", "mopup"])
def test_q_lab_03_plays_no_longer_take_approach_or_mopup(play, kw):
    """Q-LAB-03: the approach opening and the mop-up are retired; the keywords are gone (positive control: the play builds)."""
    with pytest.raises(TypeError):
        play(16, **{kw: True})
    assert play(16)(8, False).groups


@pytest.mark.parametrize("name", ["APPROACH", "APPROACH_STOP", "MOPUP", "MOPUP_INTERVAL_TICKS"])
def test_q_lab_03_plays_module_drops_the_approach_and_mopup_constants(name):
    assert not hasattr(plays, name)


def test_ruling_2_damage_play_is_the_one_labelled_asymmetry():
    """Ruling 2: the planted damage scan (damage_play, +20 percent) is the only stat difference between the sides; reach_play is
    kept as the same kind of labelled control. A naive play has none."""
    for naive in (blob_play, line_play):
        s = naive(16)(8, False)
        assert s.unit_types == {} and s.groups[0].unit == s.groups[1].unit
    d = damage_play(16)(8, False)
    assert list(d.unit_types) == ["VanguardStrong"] and d.groups[0].unit != d.groups[1].unit


# ---- LAB-REV2-L2 (Q-LAB-03): plays_space.scan_build loses its mop-up / quiet-from-first-damage flags (the two-line change L2 owns) ----

def test_scan_build_adds_no_stall_flags_to_the_space_play_setups():
    """The three stall flags scan_build used to add (mopup, mopup_interval_ticks, quiet_from_first_damage) are retired with the
    stalemate window: the 16 v 16 scan build IS the play's own setup_fn() and carries none of those fields. (test_plays_space_scan.py,
    owned by LAB-REV2-L3, still asserts the flags; its writer retires those three tests.)"""
    from scripts.skilllab import plays_space
    assert plays_space.PLAYS
    for name in sorted(plays_space.PLAYS):
        built = plays_space.scan_build(name)(None, 16, False)
        assert built == plays_space.PLAYS[name].setup_fn(), name
        assert not any(hasattr(built, f) for f in ("mopup", "mopup_interval_ticks", "quiet_from_first_damage", "stalemate_ticks")), name
