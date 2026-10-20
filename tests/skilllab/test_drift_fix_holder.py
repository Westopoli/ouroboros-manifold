# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 25 (naive defender: one blob per unit type at that type's mean anchor) and
# decision 24 (a meeting has no holder), as rulings 2 and 3 of the LAB-REV2-FIX piece (Architect, decisions 41 and 42, 2026-10-19)
"""LAB-REV2-FIX, sweep half: who is a holder, and where the naive defender's blobs stand.

INTERFACE FROZEN FOR THE BUILDER
  sweep.baseline_roles(setup) -> tuple of roles. It replaces baseline_roles(play): the play's NAME is never read (the defect: the old
    function keyed off the "s3_" prefix). `setup` is the play's own Setup. HOLDER = some side-0 group has order "guard" (derived from the
    Setup, decision 41 ruling 3). Roles:
      - a meeting (no side-0 guard group; an empty Setup too): ("naive_attacker",), no naive_defender* role at all;
      - a holder whose side-0 groups all stand on layers some side-1 group stands on: ("naive_attacker", "naive_defender");
      - a holder with a side-0 group on a layer NO side-1 group stands on: ("naive_attacker", "naive_defender_attacker_layer",
        "naive_defender_play_layer") ("as today": what the s3 plays had). This layer reading is the test writer's, the ruling does not
        say it: question Q-FIX-1 in the piece report. Tests that pin it say so.
    run_family and run_smoke call it with builds(play, "play", layout)(ENEMY_FROM, False), once per (layout, play), before the role
    builds are made, and make no build of a naive_defender* role for a meeting.
  sweep._naive_side / default_builds(play, "naive_defender*", features): ONE blob per unit type (per (type, layer) for the play-layer
    variant) at that type's mean anchor (the mean of that type's group anchors; the tests give a type's groups equal counts, so a count
    weighting and a plain mean agree), same units and counts, formation blob, radius 80 + 12 sqrt(n), the play's order, timeline dropped.
    A one-type side is unchanged from today (the hash in test_sweep_baselines.py::OPEN_BASELINE_HASH).
Real plays: read from the PLACED Setup (default_builds(play, "play", features)), where placement gives a defender-anchored play its guard
order. 12 of the 15 hold (EXPECTED_ROLES); s2_mass_one_end, s3_dark_striker and s3_ping_then_commit attack and have no holder."""
import csv
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import fake_base, positions, radius_of, vg  # noqa: E402
from fakes_scans import ScriptedFight, fake_builds, fake_groups  # noqa: E402
from scripts.skilllab import formations, plays_space, scenes, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

FEATS = {"blocked_layer_top": 0, "choke_width_bodies": 0, "cover_density_corridor": 0, "detour_ratio": 0, "lane_count": 0,
         "start_distance": 1400}
ATT, HOLD = "naive_attacker", "naive_defender"
LAYER_ROLES = ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer")
EXPECTED_ROLES = {**{p: (ATT, HOLD) for p in ("s1_hold_choke", "s1_outrange", "s2_concave", "s2_screen", "s2_spread_line", "s4_bait",
                                              "s4_do_not_chase", "s5_vulnerable_away")},
                  # s3_vision_control (LAB-VISION-CONTROL): anchors role "defender", so side 0 is placed on guard; its only group is on layer 1
                  # and the enemy stands on layer 0, so it is a holder with a group on another layer, like the three above
                  **{p: LAYER_ROLES for p in ("s3_layer_above", "s3_over_the_choke", "s3_types_by_reach", "s3_vision_control")},
                  **{p: (ATT,) for p in ("s2_mass_one_end", "s3_dark_striker", "s3_ping_then_commit")}}


# ---- ruling 3: the holder comes from the Setup ----------------------------------------------------------------------------------------

def placed_setup(play):
    """The Setup the sweep reads: the PLACED scene (sweep.default_builds), where scenes.placed_scene gives the defender of a play its
    guard order. scan_build's own Setup is not what the sweep fights."""
    return sweep.default_builds(play, "play", FEATS)(16, False)


@pytest.mark.parametrize("play", sorted(plays_space.PLAYS))
def test_a_real_play_is_a_holder_exactly_when_its_placed_side_0_has_a_guard_group(play):
    """The 14 real plays, read from their placed Setup: eight hold on the enemy's layer, three hold with a group on another layer, three
    meet and carry the naive attacker alone (s3_dark_striker and s3_ping_then_commit were given the layer roles by their s3_ name; the
    attackers of s2_mass_one_end the plain defender: that was the defect)."""
    assert sweep.baseline_roles(placed_setup(play)) == EXPECTED_ROLES[play]


def test_control_the_expected_table_matches_the_guard_groups_it_is_read_from():
    """Positive control for the test above, from the groups themselves and not from sweep.baseline_roles."""
    for play in sorted(plays_space.PLAYS):
        s = placed_setup(play)
        assert any(g.side == 0 and g.order == "guard" for g in s.groups) == (len(EXPECTED_ROLES[play]) > 1), play


def test_a_name_starting_s3_with_no_guard_group_is_a_meeting_and_the_name_is_not_read():
    """Red before: baseline_roles keyed off the s3_ prefix. The function takes a Setup now, so the name cannot reach it; the sweep-level
    test below pins that the sweep never asks for the defender baselines of such a play."""
    assert sweep.baseline_roles(Setup(groups=fake_groups("s3_pretender", meeting=True), unit_types={})) == (ATT,)


def test_a_name_not_starting_s3_with_a_guard_group_is_a_holder():
    assert sweep.baseline_roles(Setup(groups=fake_groups("p_guard"), unit_types={})) == (ATT, HOLD)


def test_an_empty_setup_is_a_meeting():
    assert sweep.baseline_roles(Setup(groups=(), unit_types={})) == (ATT,)


def test_only_side_0_guard_counts():
    """A guard group on side 1 (the enemy holds) makes no holder of side 0."""
    side0, side1 = fake_groups("p")
    side0 = dataclasses.replace(side0, order="attack_move")
    side1 = dataclasses.replace(side1, order="guard")
    assert sweep.baseline_roles(Setup(groups=(side0, side1), unit_types={})) == (ATT,)


def test_a_layer_holder_carries_the_two_layer_variants_in_place_of_the_plain_defender():
    """Q-FIX-1 (the test writer's reading of 'as today'): a holder with a group on a layer the enemy is not on."""
    assert sweep.baseline_roles(Setup(groups=fake_groups("s3_x"), unit_types={})) == LAYER_ROLES


# ---- the sweep follows the Setup, not the name -----------------------------------------------------------------------------------------

LAYOUTS = {"A": {"id": 1}}


def run_family(tmp_path, builds, plays, family="range_up"):
    fights = ScriptedFight(be_of=lambda s: 20)
    entry = sweep.run_family(family, tmp_path, builds=builds, layouts=LAYOUTS, plays=plays, fight_fn=fights,
                             caps=sweep.Capabilities(arc=True, cone=True))
    with open(tmp_path / ("sweep_%s.csv" % family), newline="") as fh:
        return entry, fights, list(csv.DictReader(fh))


def test_the_sweep_builds_and_fights_no_defender_baseline_for_a_meeting_whatever_its_name(tmp_path):
    log = []
    builds = fake_builds(log=log, meeting=("s3_pretender",))
    entry, fights, rows = run_family(tmp_path, builds, ("s3_pretender", "p_guard"))
    assert not [1 for play, role in log if play == "s3_pretender" and role.startswith("naive_defender")]
    assert {r["baseline"] for r in rows if r["play"] == "s3_pretender"} == {"none", ATT}
    assert set(entry["refined_vs"]) == {ATT, HOLD}                 # the holder play adds its role; the meeting adds none
    assert not [c for c in fights.calls if c["play"] == "s3_pretender" and c["role"].startswith("naive_defender")]


def test_control_the_same_name_with_a_guard_group_is_fought_against_the_layer_variants(tmp_path):
    """Positive control for the test above: with a guard group the s3_ name gets its defender baselines (Q-FIX-1 roles)."""
    _, _, rows = run_family(tmp_path, fake_builds(), ("s3_pretender",))
    assert {r["baseline"] for r in rows if r["kind"] == "grid"} == {"none", *LAYER_ROLES}


def test_a_guard_group_play_not_named_s3_gets_the_plain_defender(tmp_path):
    _, _, rows = run_family(tmp_path, fake_builds(), ("p_guard",))
    assert {r["baseline"] for r in rows if r["kind"] == "grid"} == {"none", ATT, HOLD}


def test_the_smoke_of_two_meetings_runs_the_naive_attacker_alone(tmp_path):
    meeting = fake_builds(meeting=tuple(sweep.PLAYS_BY_FAMILY["vision"]))
    fights = ScriptedFight(be_of=lambda s: 20)
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    sweep.run_smoke(tmp_path / "m", workers=1, builds=meeting, layouts=LAYOUTS, fight_fn=fights, control_builds=controls)
    with open(tmp_path / "m" / "smoke.csv", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["family"] == "vision"]
    assert rows and {r["baseline"] for r in rows} == {"none", ATT}
    sweep.run_smoke(tmp_path / "h", workers=1, builds=fake_builds(), layouts=LAYOUTS, fight_fn=ScriptedFight(be_of=lambda s: 20),
                    control_builds=controls)                                                    # control: holders add the defender roles
    with open(tmp_path / "h" / "smoke.csv", newline="") as fh:
        assert {r["baseline"] for r in csv.DictReader(fh) if r["family"] == "vision"} > {"none", ATT}


# ---- ruling 2: one blob per unit type at that type's mean anchor -------------------------------------------------------------------------

@pytest.fixture
def fake_scene(monkeypatch):
    def install(base):
        monkeypatch.setattr(sweep, "_layouts", {})
        monkeypatch.setattr(scenes, "placed_scene", lambda layout, play, start_distance, features, counter=False: base)
        return lambda role: sweep.default_builds("fake_play", role, FEATS)
    return install


ENEMY = vg(1, "Vanguard", 8, 3000.0, 1000.0, layer=0, order="attack_move", facing=180.0)


def own(setup):
    return [g for g in setup.groups if g.side == 0]


def test_two_types_at_two_anchors_get_two_blobs_at_the_two_type_means(fake_scene):
    base = fake_base([vg(0, "Vanguard", 8, 800.0, 900.0, order="guard"), vg(0, "Raider", 8, 1200.0, 1100.0, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    blobs = {g.unit: g for g in own(setup)}
    assert len(own(setup)) == 2 and set(blobs) == {"Vanguard", "Raider"}
    assert (blobs["Vanguard"].x, blobs["Vanguard"].y) == (800.0, 900.0) and (blobs["Raider"].x, blobs["Raider"].y) == (1200.0, 1100.0)
    assert {g.unit: g.count for g in own(setup)} == {"Vanguard": 8, "Raider": 8}
    assert all(g.formation == "blob" and g.order == "guard" and g.params == {"radius": radius_of(8)} for g in own(setup))
    assert positions(blobs["Vanguard"]) == formations.place("blob", 8, 800.0, 900.0, blobs["Vanguard"].facing_deg, {"radius": radius_of(8)})
    assert list(setup.groups[len(own(setup)):]) == [ENEMY] and setup.timeline == ()


def test_control_two_types_at_one_anchor_still_stand_on_it(fake_scene):
    """Positive control: when the type means coincide the blobs share the common anchor (the one the old code used for every blob)."""
    base = fake_base([vg(0, "Vanguard", 8, 1000.0, 1000.0, order="guard"), vg(0, "Raider", 8, 1000.0, 1000.0, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    assert {(g.x, g.y) for g in own(setup)} == {(1000.0, 1000.0)}


def test_unequal_counts_keep_their_counts_each_at_its_own_anchor(fake_scene):
    base = fake_base([vg(0, "Vanguard", 5, 700.0, 900.0, order="guard"), vg(0, "Raider", 11, 1300.0, 1100.0, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    got = {g.unit: (g.count, g.x, g.y) for g in own(setup)}
    assert got == {"Vanguard": (5, 700.0, 900.0), "Raider": (11, 1300.0, 1100.0)}


def test_a_type_split_over_two_groups_is_one_blob_at_the_mean_of_its_groups(fake_scene):
    """Equal counts, so a count-weighted and a plain mean agree: the type's mean anchor is (800, 1000)."""
    base = fake_base([vg(0, "Vanguard", 4, 600.0, 900.0, order="guard"), vg(0, "Vanguard", 4, 1000.0, 1100.0, order="guard"),
                      vg(0, "Raider", 8, 1500.0, 1000.0, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    got = {g.unit: (g.count, g.x, g.y) for g in own(setup)}
    assert got == {"Vanguard": (8, 800.0, 1000.0), "Raider": (8, 1500.0, 1000.0)}


def test_the_play_layer_variant_is_one_blob_per_type_and_layer_each_at_its_type_mean(fake_scene):
    base = fake_base([vg(0, "Vanguard", 8, 800.0, 1000.0, layer=0, order="guard"), vg(0, "Raider", 8, 1200.0, 1000.0, layer=1, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_play_layer")(8, False)
    got = {(g.unit, g.layer): (g.count, g.x, g.y) for g in own(setup)}
    assert got == {("Vanguard", 0): (8, 800.0, 1000.0), ("Raider", 1): (8, 1200.0, 1000.0)}


def test_the_point_is_the_mean_of_the_blob_positions(fake_scene):
    """Ruling 6 of the lab (guard groups): Setup.point follows the blobs wherever the type means put them."""
    base = fake_base([vg(0, "Vanguard", 8, 800.0, 900.0, order="guard"), vg(0, "Raider", 8, 1200.0, 1100.0, order="guard"), ENEMY])
    setup = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    pts = [p for g in own(setup) for p in positions(g)]
    assert setup.point == pytest.approx((sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)), abs=1e-6)
