# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decisions 25 and 26 (LAB-REV2-BASE); interface in tests/skilllab/test_sweep_baselines.py and test_naive_blob_skip.py
"""LAB-REV2-BASE, part 3 of 3: the real scenes on the smoke layouts, pre-flight read through the real library. No fight is run.

  - Every build sweep.default_builds makes (play, naive_attacker, naive_defender and its two layer variants) carries
    labels["prefight"] == scenes.preflight(<its own Setup>) (decision 25). Red before on layout 192 / s2_concave / naive_defender, whose
    label is the play's 'no_fit' while the baseline's own Setup is fine.
  - Layout 192 (choke 8 bodies, start distance 2800) at 24 and 48 enemy units: the naive attacker's defender blob used to stand in the
    wall ('no_fit' from 24 up, the 192 / 48 case); with decision 26 it skips the wall, nothing is refused, no scan is cut, and no unit of
    any baseline stands in a block. (Layouts 81 and 78 are not pinned: the plays themselves are refused there.)
  - Gated (OM_LAB_SLOW=1, a few seconds with a fake fight function; gated as the brief asks): sweep.run_family over the real builds on
    layout 192 for the two layer plays reaches 48 for the play and every baseline, lists no refusal and no cut cell.
  - Ruling 25's construction on a real layer play, green before and after.
"""
import csv
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import in_block, positions  # noqa: E402
from fakes_scans import _fr  # noqa: E402
from scripts.skilllab import engine, scenes, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="the sweep over the real builds; set OM_LAB_SLOW=1")
PLAYS = ("s2_concave", "s3_layer_above", "s3_types_by_reach")
S3 = ("s3_layer_above", "s3_types_by_reach")


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def roles_of(play):
    return ("play",) + sweep.baseline_roles(play)


@pytest.mark.parametrize("heads", [8, 48])
@pytest.mark.parametrize("play", PLAYS)
@pytest.mark.parametrize("layout", sweep.SMOKE_LAYOUTS)
def test_every_build_is_labelled_with_the_preflight_of_its_own_setup(library, layout, play, heads):
    features = sweep.smoke_layouts()[layout]
    for role in roles_of(play):
        build = sweep.default_builds(play, role, features)
        setup = build(heads, False)
        assert build.labels["prefight"] == scenes.preflight(setup, library), (layout, play, role, heads)


@pytest.mark.parametrize("heads", [8, 24, 48])
@pytest.mark.parametrize("play", S3)
def test_layout_192_places_every_baseline_in_open_cells_at_every_headcount(library, play, heads):
    """The 192 / 48 case: the play fits on 192 at every headcount, so every baseline fits (decision 26): label 'ok', no unit in a block."""
    features = sweep.smoke_layouts()["192"]
    for role in roles_of(play):
        build = sweep.default_builds(play, role, features)
        setup = build(heads, False)
        assert build.labels["prefight"] == "ok", (play, role, heads)
        stuck = [(g.side, g.unit, p) for g in setup.groups for p in positions(g) if in_block(setup.terrain.blocks, g.layer, p)]
        assert not stuck, (play, role, heads, stuck[:3])
        assert sum(g.count for g in setup.groups if g.side == 1) == heads


def test_ruling_25_variants_on_a_real_layer_play(library):
    """Green before and after. s3_layer_above on 192: the play-layer variant keeps each type on the layer the play gave it (a layer play's
    arrangement minus its skill), the attacker-layer variant puts every type on the attacker's layer, and neither is one raised layer."""
    features = sweep.smoke_layouts()["192"]
    play = sweep.default_builds("s3_layer_above", "play", features)(16, False)
    plays_side0 = {(g.unit, g.layer) for g in play.groups if g.side == 0}
    attackers = {g.layer for g in play.groups if g.side == 1}
    assert len({layer for _u, layer in plays_side0}) >= 2 and len(attackers) == 1
    pl = sweep.default_builds("s3_layer_above", "naive_defender_play_layer", features)(16, False)
    al = sweep.default_builds("s3_layer_above", "naive_defender_attacker_layer", features)(16, False)
    assert {(g.unit, g.layer) for g in pl.groups if g.side == 0} == plays_side0
    assert {g.layer for g in al.groups if g.side == 0} == attackers
    for variant in (pl, al):
        assert variant.timeline == ()
        assert sorted((g.unit, g.count) for g in variant.groups if g.side == 0) == sorted(
            (g.unit, g.count) for g in play.groups if g.side == 0)
        assert [g for g in variant.groups if g.side == 1] == [g for g in play.groups if g.side == 1]


@SLOW
def test_e_the_sweep_over_the_real_builds_on_layout_192_reaches_48_with_nothing_refused_or_cut(tmp_path):
    """The 192 / 48 case end to end (fake fights, real scenes and pre-flight): nothing refused, nothing cut, every role scanned up to 48."""
    calls = []

    def fight_fn(setup, seed, swap):
        enemy = sum(g.count for g in setup.groups if g.side == 1)
        calls.append(enemy)
        return _fr("side0" if enemy <= 20 else "side1", enemy)

    layouts = {"192": sweep.smoke_layouts()["192"]}
    entry = sweep.run_family("damage_up", tmp_path, layouts=layouts, plays=S3, fight_fn=fight_fn, caps=sweep.Capabilities(True, True))
    with open(tmp_path / "sweep_damage_up.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert entry["refused"] == [] and entry["baseline_no_fit"] == []
    for play in S3:
        for baseline in ("none",) + sweep.baseline_roles(play):
            heads = [int(r["enemy_heads"]) for r in rows if r["play"] == play and r["baseline"] == baseline and r["kind"] == "grid"]
            assert heads and max(heads) == 48, (play, baseline)
    assert {r["baseline_no_fit"] for r in rows} == {"0"} and {r["prefight"] for r in rows} == {"ok"}
