# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (piece LAB-REV3-B); Architect ruling 2026-10-20 (implementation; Westley may veto): the batch sweeps all seven vision plays, the SMOKE keeps the original two
"""LAB-REV3-B-SMOKE: the quick health check (`sweep.run_smoke`) runs its own list of plays, not the batch's.

Piece B added five mix plays to the vision family (`sweep.PLAYS_BY_FAMILY["vision"]` holds seven now): the batch sweeps all seven (Westley's
requirement: all five layers, vision up and down swept where it can bite). The smoke is a health check and keeps the original two vision plays
(`s3_layer_above`, `s3_types_by_reach`), with `s3_vision_control` as the family's designated control. `run_smoke` iterated
`PLAYS_BY_FAMILY["vision"]`, so the smoke grew from 6 to 21 defect cells (red set: test_sweep.py::test_smoke_runs_vision_half_only_on_the_three_
layouts_plus_the_three_controls and ::test_smoke_counts_its_defects_like_a_sweep_entry, test_drift_fix_blind.py::test_smoke_counts_blind_posts_
apart_and_asserts_no_other_cap; they are left as they are and go green when the smoke reads SMOKE_PLAYS).

BUILDER CONTRACT (the pick between "an explicit mapping" and "the first two of each family" is the Architect's delegation: pinned as the mapping):
  - `scripts/skilllab/sweep.py` defines the module constant `SMOKE_PLAYS`, a dict {family: tuple of play names} for the families the smoke
    runs (today only "vision"), next to `PLAYS_BY_FAMILY`; `SMOKE_PLAYS["vision"] == ("s3_layer_above", "s3_types_by_reach")`, in that order.
  - Every play of SMOKE_PLAYS[family] is also in PLAYS_BY_FAMILY[family] (the smoke is a subset of the batch). PLAYS_BY_FAMILY is NOT shrunk:
    "vision" still holds the seven plays.
  - `s3_vision_control` (sweep.VISION_CONTROL_PLAY, the designated Control.play of the vision positive control) is in neither mapping.
  - `run_smoke` reads `sweep.SMOKE_PLAYS["vision"]` at call time (the module attribute, not a copy taken at import) for the plays of its
    vision half. Layouts, the vision 0.5 point, the baselines of each play and the three lab controls stay as they are.
Tests the ruling retires: none (the three tests above are right as written, except for one comparison noted below); one existing test changes its
parametrization source (test_vision_control.py::test_positive_control_the_structural_check_flags_the_mixed_sweep_plays, TD-LAB-REV3-B-smoke).
NOTE for the ruler: test_sweep.py::test_smoke_runs_vision_half_only_on_the_three_layouts_plus_the_three_controls also asserts
`set(sweep.PLAYS_BY_FAMILY["vision"]) == {"s3_layer_above", "s3_types_by_reach"}` in a chained comparison; that half stays false while the batch
holds seven plays, so the test cannot go green on a builder's change alone (see the report of this piece)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import fake_builds  # noqa: E402
from test_sweep import World, control_builds  # noqa: E402
from scripts.skilllab import plays_space, sweep  # noqa: E402

SMOKE_VISION = ("s3_layer_above", "s3_types_by_reach")
MIX_PLAYS = ("s3_raider_bombard", "s3_interceptor_bombard", "s3_interceptor_raider", "s3_bombard_bastion", "s3_bombard_bastion_level")
BATCH_VISION = SMOKE_VISION + MIX_PLAYS


# ---- the contract ------------------------------------------------------------------------------------------------------------------

def test_t1_smoke_plays_maps_vision_to_the_original_two_plays_in_order():
    assert isinstance(sweep.SMOKE_PLAYS, dict)
    assert tuple(sweep.SMOKE_PLAYS["vision"]) == SMOKE_VISION


def test_t1_every_smoke_play_is_also_a_batch_play_of_its_family():
    assert sweep.SMOKE_PLAYS, "positive control: the mapping has families to check"
    for family, plays in sweep.SMOKE_PLAYS.items():
        assert family in sweep.PLAYS_BY_FAMILY, family
        assert plays and len(set(plays)) == len(plays), (family, plays)
        assert set(plays) <= set(sweep.PLAYS_BY_FAMILY[family]), (family, set(plays) - set(sweep.PLAYS_BY_FAMILY[family]))


def test_t1_the_batch_is_not_shrunk_it_still_holds_all_seven_vision_plays():
    """Westley's requirement: the batch covers all five layers. The two-play list is the smoke's, never the batch's."""
    assert set(sweep.PLAYS_BY_FAMILY["vision"]) == set(BATCH_VISION) and len(sweep.PLAYS_BY_FAMILY["vision"]) == 7
    assert set(sweep.PLAYS_BY_FAMILY["vision"]) > set(sweep.SMOKE_PLAYS["vision"]), "positive control: the smoke list is a strict subset"


def test_t1_the_vision_control_play_is_in_neither_list_and_is_the_designated_control():
    assert sweep.VISION_CONTROL_PLAY == "s3_vision_control"
    assert sweep.controls("vision")["positive"].play == sweep.VISION_CONTROL_PLAY
    assert sweep.VISION_CONTROL_PLAY in plays_space.PLAYS, "positive control: the name is a registered play, so its absence below means something"
    assert sweep.VISION_CONTROL_PLAY not in sweep.SMOKE_PLAYS["vision"]
    assert not [f for f, plays in sweep.PLAYS_BY_FAMILY.items() if sweep.VISION_CONTROL_PLAY in plays]
    assert not [f for f, plays in sweep.SMOKE_PLAYS.items() if sweep.VISION_CONTROL_PLAY in plays]


# ---- the smoke builds exactly its own plays ----------------------------------------------------------------------------------------

def _run(tmp_path, log):
    world = World()
    sweep.run_smoke(tmp_path, workers=1, builds=fake_builds(log=log), fight_fn=world, control_builds=control_builds())
    return world


def test_t2_the_smoke_builds_and_fights_exactly_the_smoke_plays_of_the_vision_half_not_the_batchs_seven(tmp_path):
    log = []
    world = _run(tmp_path, log)
    built = {play for play, _ in log}
    assert built == set(SMOKE_VISION), built      # red today for this reason: the smoke builds all seven batch plays
    assert built == set(sweep.SMOKE_PLAYS["vision"])
    assert not built & set(MIX_PLAYS), built & set(MIX_PLAYS)
    assert sweep.VISION_CONTROL_PLAY not in built
    fought = {c["play"] for c in world.calls} - {"mirror", "numbers", "planted"}
    assert fought == set(SMOKE_VISION), fought
    assert {c["play"] for c in world.calls} >= {"mirror", "numbers", "planted"}, "positive control: the three lab controls are still fought"


def test_t2_the_smoke_reads_smoke_plays_at_call_time_positive_control(tmp_path, monkeypatch):
    """Positive control of the test above: a different SMOKE_PLAYS gives a different set of built plays, so the smoke reads the mapping
    (and does not carry a literal list of its own)."""
    monkeypatch.setattr(sweep, "SMOKE_PLAYS", {"vision": ("s3_raider_bombard", "s3_bombard_bastion_level")})
    log = []
    world = _run(tmp_path, log)
    assert {play for play, _ in log} == {"s3_raider_bombard", "s3_bombard_bastion_level"}
    assert {c["play"] for c in world.calls} - {"mirror", "numbers", "planted"} == {"s3_raider_bombard", "s3_bombard_bastion_level"}


def test_t2_the_batch_family_run_still_covers_all_seven_plays(tmp_path):
    """The batch (run_family with no `plays`) iterates PLAYS_BY_FAMILY: the smoke change must not touch it."""
    log = []
    sweep.run_family("vision", tmp_path, builds=fake_builds(log=log), layouts={"A": {"id": 1}}, fight_fn=World(),
                     caps=sweep.Capabilities(True, True))
    assert {play for play, _ in log} >= set(BATCH_VISION)
