"""Rung K2 tests, SPEC.md 14.3 as corrected: the hidden layer is real, S3 is layer (guess + 1), S4 is info,
S1 on a flat map is exactly the naive play.

Run from toys/layerlab/. Expected red until the Doer brings plays.py to the corrected semantics.

Conventions these tests fix (SPEC gaps):
- The S3 layer is clipped to 1..5 (guess + 1 with a hidden layer of 5 gives 5; below 1 gives 1). It is checked
  on `compose` with hand-set `hidden` and `layer` values, outside the sampler's range {2, 3, 4}.
- The naive side's layer rule lives in `build_scenario` (it knows the config): `compose` has no config, and a
  naive compose (no skills) stays on `sit.layer`.
- `build_scenario(..., config=None)` is the base rules: only same-layer units fight, so the naive side stays on
  `sit.layer`. LA, LB and LC allow cross-layer fire: the naive side stands on `sit.hidden["layer"]`.
- The skilled side in `build_scenario` is label A when swap is False and label B when swap is True.
- Slots are independent, so on a flat map S1 is a no-op in every combination (S1 + C equals C).
- Every combination containing S4 carries the flag `info=given` in its profile cells; the others do not.
"""
import dataclasses
import itertools

import pytest

from test_skill_k2 import (FAMILIES, MIXED, _centroid, _compose, _enemy, _m, _scripted_fights, _sit, _units)

CONFIGS = (None, "LA", "LB", "LC")
FLAT_HIDDEN = {"route": 0, "layer": 4}              # sit.layer is 3: the hidden layer differs from the default guess


def _build(sit, skills, config, ratio=1.5, swap=False, size=4, ladder="line"):
    return _m("plays").build_scenario(sit, frozenset(skills), size, ladder, config=config)(ratio, swap)


def _layers(scn, label):
    return {u["layer"] for u in _units(scn["groups"]) if u["side"] == label}


def _roles(swap):
    return ("B", "A") if swap else ("A", "B")        # (skilled label, naive label)


# ------------------------------------------------------------------ (a) the naive side stands on the hidden layer

@pytest.mark.parametrize("swap", (False, True))
@pytest.mark.parametrize("config", CONFIGS, ids=str)
@pytest.mark.parametrize("hidden_layer", (2, 4))
def test_naive_side_layer_is_the_hidden_layer_only_under_cross_layer_fire(config, swap, hidden_layer):
    sit = _sit("flat", hidden={"route": 0, "layer": hidden_layer})
    assert sit.hidden["layer"] != sit.layer
    scn = _build(sit, (), config, swap=swap)
    skilled, naive = _roles(swap)
    assert _layers(scn, naive) == ({sit.layer} if config is None else {hidden_layer})
    assert _layers(scn, skilled) == {sit.layer}                  # an unskilled own force stays on the default layer


def test_naive_layer_check_has_a_positive_control():
    sit = _sit("flat", hidden=FLAT_HIDDEN)
    base = _layers(_build(sit, (), None), "B")
    lever = _layers(_build(sit, (), "LA"), "B")
    assert base == {sit.layer} and lever == {4} and base != lever


# ------------------------------------------------------------------ (b) S3 is layer (guess + 1), clipped to 1..5

@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("hidden_layer,expected", [(-1, 1), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 5), (6, 5)])
def test_s3_with_s4_is_hidden_layer_plus_one_clipped(side, hidden_layer, expected):
    sit = _sit("flat", hidden={"route": 0, "layer": hidden_layer})
    assert {g["layer"] for g in _compose(sit, side, ("S3", "S4"))} == {expected}


@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("hidden_layer", (2, 3, 4, 5))
def test_s3_without_s4_is_the_default_layer_plus_one_whatever_is_hidden(side, hidden_layer):
    sit = _sit("flat", hidden={"route": 0, "layer": hidden_layer})
    assert {g["layer"] for g in _compose(sit, side, ("S3",))} == {sit.layer + 1}


@pytest.mark.parametrize("layer,expected", [(1, 2), (4, 5), (5, 5)])
def test_s3_without_s4_is_clipped_to_layer_5(layer, expected):
    sit = _sit("flat", layer=layer, hidden={"route": 0, "layer": 2})
    assert {g["layer"] for g in _compose(sit, 0, ("S3",))} == {expected}


# ------------------------------------------------------------------ (c) S4 alone is the naive play

@pytest.mark.parametrize("swap", (False, True))
@pytest.mark.parametrize("config", CONFIGS, ids=str)
@pytest.mark.parametrize("ratio", (1.0, 2.5))
def test_s4_alone_equals_the_naive_play_under_every_config(config, swap, ratio):
    sit = _sit("flat", hidden=FLAT_HIDDEN)
    assert _build(sit, ("S4",), config, ratio, swap) == _build(sit, (), config, ratio, swap)


@pytest.mark.parametrize("swap", (False, True))
def test_s4_only_matters_through_s3_positive_control(swap):
    sit = _sit("flat", hidden=FLAT_HIDDEN)
    s3, both = _build(sit, ("S3",), "LA", swap=swap), _build(sit, ("S3", "S4"), "LA", swap=swap)
    skilled, _ = _roles(swap)
    assert both["groups"] != s3["groups"]
    assert _layers(s3, skilled) == {sit.layer + 1} and _layers(both, skilled) == {FLAT_HIDDEN["layer"] + 1}


# ------------------------------------------------------------------ (d) S1 on a flat map is exactly the naive play

@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("ladder", ("blob", "line", "hold"))
def test_s1_on_flat_is_exactly_the_naive_play(side, ladder):
    sit = _sit("flat", mix=MIXED)
    s1 = _compose(sit, side, ("S1",), 6, ladder)
    assert s1 == _compose(sit, side, (), 6, ladder)             # the group dicts compare equal
    expected = "hold" if ladder == "hold" else "attack_move"
    assert {g["order"] for g in s1} == {expected}
    assert (all("goals" not in g for g in s1)) == (ladder == "hold")


@pytest.mark.parametrize("side", (0, 1))
def test_s1_on_flat_is_a_no_op_in_every_combination(side):
    sit = _sit("flat", mix=MIXED, hidden={"route": 1, "layer": 2})
    enemy = _enemy(sit, 6)
    rest = [s for s in ("S2", "S3", "S4", "S5")]
    for n in range(len(rest) + 1):
        for c in itertools.combinations(rest, n):
            assert _compose(sit, side, c + ("S1",), 6, "line", enemy) == _compose(sit, side, c, 6, "line", enemy), c


@pytest.mark.parametrize("family", [f for f in FAMILIES if f != "flat"])
@pytest.mark.parametrize("side", (0, 1))
def test_s1_on_featured_families_still_holds_at_the_family_point(family, side):
    sit = _sit(family)
    groups = _compose(sit, side, ("S1",), 4)
    naive = _compose(sit, side, (), 4)
    assert groups != naive                                       # positive control: not the naive play
    assert {g["order"] for g in groups} == {"hold"} and all("goals" not in g for g in groups)
    assert {g["order"] for g in naive} == {"attack_move"}
    a = _centroid([(u["x"], u["y"]) for u in _units(groups)])
    b = _centroid([(u["x"], u["y"]) for u in _units(naive)])
    assert (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > 1.0


# ------------------------------------------------------------------ (e) a right guess is one layer above the enemy

@pytest.mark.parametrize("swap", (False, True))
def test_under_la_the_informed_skilled_force_is_one_layer_above_the_naive_enemy(swap):
    sit = _sit("flat", hidden={"route": 0, "layer": 2})
    assert sit.layer == 3
    skilled, naive = _roles(swap)
    informed = _build(sit, ("S3", "S4"), "LA", swap=swap)
    guessing = _build(sit, ("S3",), "LA", swap=swap)
    assert _layers(informed, naive) == {2} and _layers(informed, skilled) == {3}      # one above
    assert _layers(guessing, naive) == {2} and _layers(guessing, skilled) == {4}      # two above: a wrong guess


# ------------------------------------------------------------------ (f) S4 is labelled `info=given` in the profile

def test_profile_flags_info_given_for_every_combination_containing_s4(monkeypatch):
    rstar_mod = __import__("layerlab.skill.rstar", fromlist=["run_fights"])
    monkeypatch.setattr(rstar_mod, "run_fights",
                        lambda jobs, *a, **k: [_scripted_fights(scn) for scn, _seed in jobs])
    sit = dataclasses.replace(_sit("flat"), hidden=dict(FLAT_HIDDEN))
    combos = [frozenset(), frozenset({"S3"}), frozenset({"S4"}), frozenset({"S3", "S4"}), frozenset({"S1", "S4"})]
    prof = _m("plays").profile([sit], sizes=(4,), ratios=(0.7, 1.4, 2.8), refine=1, seeds=(0,), combos=combos,
                               processes=0)
    assert len(prof.cells) == len(combos)
    for c in prof.cells:
        assert ("info=given" in c["flags"]) == ("S4" in c["combo"]), sorted(c["combo"])
