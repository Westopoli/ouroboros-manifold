# spec: ruling A145 as superseded for registration by the Architect ruling of 2026-10-06 (plays registered as drafts, status "draft"), brief t1b
"""skills registry + asym wiring: S2 drafts registered, a skill with no entry refuses, focus-centred concave, labels in rows.
Assumes get() returns a Play spec with `.fn` and `.status`. `asym.unit_stats` is faked; no Engine, no compiler."""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.asym as asym  # noqa: E402
import scripts.skilllab.rows as rows  # noqa: E402
import scripts.skilllab.skills as skills  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.contract import FightResult  # noqa: E402
from scripts.skilllab.formations import place  # noqa: E402

DRAFT = "draft"


@pytest.fixture(autouse=True)
def _fake_stats(monkeypatch):
    """Every unit type has sensor radius 700."""
    monkeypatch.setattr(asym, "unit_stats", lambda name: {
        "category": 1, "max_hp": 100.0, "base_damage": 10.0, "attack_interval": 20.0, "attack_range": 100.0,
        "speed": 5.0, "sensor_radius": 700.0, "layer_transition_time": 0.0, "aoe_radius": 0.0})


@pytest.fixture
def fake_play():
    """Register a throwaway ("TEST","skilled") play wrapping the S2 draft; yields a call log; always unregisters."""
    calls = []
    real = skills.get("S2", "skilled").fn

    def fn(ctx):
        calls.append(ctx)
        return real(ctx)

    skills.register("TEST", "skilled", fn, "fake status")
    yield calls
    try:
        skills.unregister("TEST", "skilled")
    except (KeyError, ValueError):
        pass


def _points(setup, side):
    out = []
    for g in setup.groups:
        if g.side == side:
            out += place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
    return out


def test_s2_drafts_registered_as_unconfirmed():
    """Both S2 plays exist and say 'draft'."""
    assert skills.get("S2", "skilled").status == DRAFT
    assert skills.get("S2", "counter").status == DRAFT


@pytest.mark.parametrize("pair", [("S9", "skilled"), ("S9", "counter"), ("TEST", "skilled"),
                                  ("S2", "blob"), ("S2", "nope")])
def test_get_unknown_pair_raises(pair):
    """An unregistered (skill, role) is a ValueError, never a default play."""
    with pytest.raises(ValueError):
        skills.get(*pair)


@pytest.mark.parametrize("skill", ["S9"])
@pytest.mark.parametrize("role", ["skilled", "counter"])
def test_undefined_skills_error_names_westley(skill, role):
    """Ruling 2026-10-06: S1/S3/S4/S5 no longer raise once registered; asym_play still refuses a skill with no entry."""
    other = Side("line")
    with pytest.raises(ValueError):
        asym_play(16, Side(role, skill=skill), other)(16, False)


def test_fake_play_plugs_in_and_does_not_leak():
    """Control: after a fixture-less registration is removed, the pair is unknown again."""
    skills.register("TEST", "skilled", lambda ctx: None, "x")
    skills.unregister("TEST", "skilled")
    with pytest.raises(ValueError):
        skills.get("TEST", "skilled")


def test_registered_fake_play_is_used_by_asym_play(fake_play):
    """A registered play is what asym_play calls, and its status reaches the labels."""
    build = asym_play(16, Side("skilled", skill="TEST"), Side("line"))
    setup = build(16, False)
    assert fake_play, "registered fn was never called"
    assert len(_points(setup, 0)) == 16
    assert build.labels["play_side0"] == "TEST:skilled"
    assert build.labels["status_side0"] == "fake status"


def test_fake_play_gone_after_previous_test():
    """No leakage between tests: the fixture's registration from the previous test is removed."""
    with pytest.raises(ValueError):
        skills.get("TEST", "skilled")


def _fit_centre_x(pts, cy):
    """Solve s so that pts are equidistant from (s, cy) using the first and last point."""
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    num = x1 ** 2 - x0 ** 2 + (y1 - cy) ** 2 - (y0 - cy) ** 2
    return num / (2 * (x1 - x0))


def test_concave_centres_on_focus():
    """Focus (0, 200): arc centre is that point (up to the contact x shift), radius = anchor-to-focus 200,
    side centroid on the focus side. Tolerance 1e-5 allows place()'s 6-decimal rounding."""
    s = asym_play(16, Side("skilled", focus=(0, 200)), Side("line"))(16, False)
    pts = _points(s, 0)
    cx = _fit_centre_x(pts, 200.0)
    dists = [math.hypot(x - cx, y - 200.0) for x, y in pts]
    assert dists == pytest.approx([200.0] * 16, abs=1e-5, rel=0)
    assert sum(y for _, y in pts) / 16 > 0


def test_concave_focus_none_keeps_today_points():
    """Control: focus None equals the default Side and today's concave (radius 150+12*sqrt(n), 120 degrees)."""
    a = asym_play(16, Side("skilled"), Side("line"))(16, False)
    b = asym_play(16, Side("skilled", focus=None), Side("line"))(16, False)
    assert a == b
    g = [g for g in a.groups if g.side == 0][0]
    assert g.formation == "concave" and g.params == {"arc_deg": 120, "radius": 150 + 12 * math.sqrt(16)}
    off = asym_play(16, Side("skilled", focus=(0, 200)), Side("line"))(16, False)
    assert _points(off, 0) != _points(a, 0)


def test_labels_for_every_role():
    """Draft plays say 'draft'; naive plays say 'naive' and never 'draft'."""
    l = asym_play(16, Side("skilled"), Side("line")).labels
    assert l["play_side0"] == "S2:skilled" and l["status_side0"] == DRAFT
    assert l["play_side1"] == "line" and l["status_side1"] == "naive"
    l = asym_play(16, Side("blob"), Side("counter", skill="S2")).labels
    assert l["play_side0"] == "blob" and l["status_side0"] == "naive"
    assert l["play_side1"] == "S2:counter" and l["status_side1"] == DRAFT
    for role in ("blob", "line"):
        assert DRAFT not in asym_play(16, Side(role, skill="S1"), Side(role)).labels.values()


def _result():
    """A FightResult written the rev 2 way (spec contract): every new field set, none left to its default."""
    return FightResult(outcome="side0", margin=0.5, strength_left=(1.0, 0.0), survivors=(3, 0), heads=(16, 16), ticks=10,
                       first_contact_tick=2, firing=[], firing_unit_seconds=(1.0, 2.0), winner="side0", states=[(5, 1, 0)],
                       weighted_unit_seconds=(3.0, 4.0), firing_window=(0.5, 1.5), weighted_window=(2.5, 3.5),
                       predicted_count="side1", predicted_type="side0", agreement="count_wrong_type_right")


NEW_COLUMNS = ("firing_window_0", "firing_window_1", "weighted_unit_seconds_0", "weighted_unit_seconds_1", "weighted_window_0",
               "weighted_window_1", "predicted_count", "predicted_type", "agreement", "knob", "knob_value", "baseline", "ceiling_hit", "prefight")


def test_labels_flow_into_fight_row_and_csv(tmp_path):
    """fight_row(result, **labels) keeps the label columns; no label name collides with a fixed row key (the fixed keys now include
    knob, knob_value, baseline, ceiling_hit and prefight); the rev 2 result columns reach the row and the CSV."""
    labels = asym_play(16, Side("skilled"), Side("counter")).labels
    assert not set(labels) & set(rows._FIXED)
    row = rows.fight_row(_result(), baseline="naive_defender", prefight="no_reach", **labels)
    for k in ("play_side0", "play_side1", "status_side0", "status_side1"):
        assert row[k] == labels[k]
    assert (row["firing_window_0"], row["weighted_window_1"], row["agreement"]) == (0.5, 3.5, "count_wrong_type_right")
    assert (row["baseline"], row["prefight"], row["knob"], row["ceiling_hit"]) == ("naive_defender", "no_reach", "none", 0)
    path = tmp_path / "out.csv"
    rows.write_rows([row], path)
    head, body = path.read_text().splitlines()[:2]
    cols = head.split(",")
    assert {"play_side0", "play_side1", "status_side0", "status_side1", *NEW_COLUMNS} <= set(cols)
    assert DRAFT in body and "naive_defender" in body and "no_reach" in body and "count_wrong_type_right" in body


def test_control_a_label_named_like_a_result_column_is_refused():
    """Control for the collision assertion: a label named like a rev 2 result column is refused by fight_row."""
    for clash in ("agreement", "predicted_type", "weighted_window_0", "firing_window_1"):
        with pytest.raises(ValueError):
            rows.fight_row(_result(), **{clash: "x"})


def test_every_registered_space_play_has_a_draft_registry_entry():
    """Each plays_space play (the 14 of rev 2) points at a registered skills entry with status draft; S3 and S5 have no counter."""
    from scripts.skilllab import plays_space
    assert len(plays_space.PLAYS) == 14
    for name, p in plays_space.PLAYS.items():
        role = "counter" if name in ("s2_mass_one_end", "s4_do_not_chase", "s1_outrange") else "skilled"
        assert skills.get(p.skill, role).status == DRAFT, name
    assert {p.skill for p in plays_space.PLAYS.values()} == {"S1", "S2", "S3", "S4", "S5"}
    assert not skills.has_counter("S3") and not skills.has_counter("S5")


@pytest.mark.parametrize("name", ["asym.py", "skills.py"])
def test_source_labels_unconfirmed_draft(name):
    """The code itself carries the status string 'draft'."""
    assert DRAFT in (ROOT / "scripts" / "skilllab" / name).read_text()
