"""Rung R0 test 2 (SPEC.md section 10): positive controls (README section 6 controls, X1)."""
import pytest

from layerlab import scenario
from layerlab.ffi import WIN_A, WIN_B, WIN_CAP, WIN_STALEMATE
from layerlab.run import run

SEEDS = range(20)


@pytest.fixture(scope="module")
def scn(scenarios_dir):
    return scenario.load(str(scenarios_dir / "r0_raiders_10v5.toml"))


def test_10v5_a_wins_every_seed(scn):
    """README section 6 control X1 (positive control): 10 against 5 identical raiders,
    flat, same layer: A wins on 20 of 20 seeds."""
    losses = [(s, r.winner) for s in SEEDS for r in [run(scn, seed=s)] if r.winner != WIN_A]
    assert not losses, "A failed to win seeds (seed, winner): %s" % losses


def test_5v5_mirror_splits(scn):
    """README section 6 control (mirror of X1): 5 against 5 identical raiders, same
    formation: each side wins at least 4 of 20 seeds and there is no stalemate or cap."""
    mirror = scenario.set_path(scn, "groups[0].count", 5)
    winners = [run(mirror, seed=s).winner for s in SEEDS]
    a_wins = winners.count(WIN_A)
    b_wins = winners.count(WIN_B)
    assert WIN_STALEMATE not in winners and WIN_CAP not in winners, winners
    assert a_wins >= 4, "A won only %d of 20 (winners=%s)" % (a_wins, winners)
    assert b_wins >= 4, "B won only %d of 20 (winners=%s)" % (b_wins, winners)


def test_crippled_a_never_wins(scn):
    """README section 6 control (detector is live): A cut to 1 raider against 10: A never
    wins on any of 20 seeds, so the 10v5 'A wins' check can fail."""
    crippled = scenario.set_path(scn, "groups[0].count", 1)
    crippled = scenario.set_path(crippled, "groups[1].count", 10)
    winners = [run(crippled, seed=s).winner for s in SEEDS]
    assert WIN_A not in winners, "1 v 10 produced an A win: winners=%s" % winners
