"""Rung L1 tests (SPEC.md 15.1, 15.4; E-01 S-164): reach by unit type.

`ll_unit_type.reach[9]` multiplies a type's range by signed offset (target layer minus own layer,
plus 4). A target at a zero-reach offset is never fired at and is not an acquisition candidate;
otherwise the maximum range is `range * rules.range_mult[off] * reach[off]`.

Fixture conventions (every test controls all variables but the one under test):
- spawn_jitter 0, all units hold, flat terrain, layer_spacing 0 (d3 is the xy distance).
- The rules tables range_mult, dmg_mult and aoe_layer_mult are 1.0 at offsets -1, 0, +1, so the
  global tables never decide a fight and only the type's `reach` can.
- The target is a "dummy": the seer type with a huge HP pool. It has dmg 0 so it never fires back
  and never moves; every shot, every damage point and every HP change is the attacker's.
- The attacker senses 2000 (cross-layer sight at offsets +-1 is 1000), so vision never decides.
- "Fires" is read from `res.shots[0]` and `res.damage_dealt[0]`.
- Until the builder replaces the stub in src/ll_reach.c (reach ignored, every offset 1.0), the tests
  that need a zero reach fail with "fired when it must not"; legacy-compat tests pass today.
"""
import pytest

from conftest import grp, make_scenario, table9
from layerlab import scenario
from layerlab.run import run

CROSS = table9(m1=1, z=1, p1=1)          # signed offsets -1, 0, +1 on, for the three global tables
ATTACKER_X, ATTACKER_Y = 1000.0, 1000.0


def reach9(**by_offset):
    """A 9-entry reach list; keys as table9: 'm1', 'z', 'p1', ..."""
    return table9(**by_offset)


def _scn(groups, types=None, rules=None, max_ticks=100):
    scn = make_scenario(groups, run={"max_ticks": max_ticks, "stalemate_ticks": 6000},
                        rules={"spawn_jitter": 0.0, "range_mult": CROSS, "dmg_mult": CROSS,
                               "aoe_layer_mult": CROSS, **(rules or {})})
    scn["types"]["dummy"] = {**scn["types"]["seer"], "hp": 1.0e6}
    scn["types"]["shooter"] = {**scn["types"]["raider"], "sensor": 2000.0}
    scn["types"]["bomber"] = {**scn["types"]["shooter"], "aoe_r": 150.0}
    scn["types"]["quiet_caster"] = {**scn["types"]["caster"], "sensor": 2000.0, "interval_s": 1.0e6}
    for name, fields in (types or {}).items():
        scn["types"][name] = {**scn["types"][name], **fields}
    return scn


def _duel(reach, dist=100.0, own_layer=3, tgt_layer=4, atype="shooter", rules=None, types_extra=None):
    """One attacker (side A, `atype`, with `reach` when not None) against one dummy at `dist` to its east."""
    over = {} if reach is None else {"reach": reach}
    scn = _scn([grp("A", atype, ATTACKER_X, ATTACKER_Y, own_layer),
                grp("B", "dummy", ATTACKER_X + dist, ATTACKER_Y, tgt_layer)],
               types={atype: over, **(types_extra or {})}, rules=rules)
    return run(scn, seed=0)


def _fired(res):
    return res.shots[0] > 0 and res.damage_dealt[0] > 0


def _silent(res):
    return res.shots[0] == 0 and res.damage_dealt[0] == 0.0


# ---- 1. zero reach never fires, with its positive control ------------------------------------------

def test_zero_reach_to_the_layer_above_never_fires():
    """S-164 / SPEC 15.1: reach only on its own layer, target one layer above at 100 (inside range 200,
    visible, tables on): shots 0 and damage 0. Positive control (next test): offset +1 at 1.0 fires."""
    res = _duel(reach9(z=1), dist=100.0)
    assert _silent(res), "fired at a zero-reach offset: shots %s damage %s" % (res.shots, res.damage_dealt)


def test_reach_one_to_the_layer_above_fires_positive_control():
    """S-164 / SPEC 15.1: the same scenario as the zero-reach test with reach[+1] = 1.0 fires, so the
    silence there is the reach and not the fixture (geometry, vision, tables)."""
    res = _duel(reach9(z=1, p1=1), dist=100.0)
    assert _fired(res), "shots %s damage %s" % (res.shots, res.damage_dealt)


# ---- 2. range scaling ---------------------------------------------------------------------------------

@pytest.mark.parametrize("mult,near,far", [(0.5, 90.0, 110.0), (1.5, 290.0, 310.0)])
def test_reach_scales_the_range_at_its_offset(mult, near, far):
    """S-164 / SPEC 15.1: range 200 * reach[+1] = 100 or 300 against a target one layer up. Inside the
    scaled range (90, 290) it is hit; just outside (110, 310) it is not. Static, hold orders."""
    r = reach9(z=1, p1=mult)
    assert _fired(_duel(r, dist=near)), "no hit at %g with reach %g" % (near, mult)
    res = _duel(r, dist=far)
    assert _silent(res), "hit at %g with reach %g: shots %s" % (far, mult, res.shots)


def test_reach_multiplies_with_the_global_range_table():
    """S-164 / SPEC 15.1: effective range = type.range * rules.range_mult[off] * reach[off]. Range 200,
    range_mult[+1] = 0.8, reach[+1] = 1.5 gives 240: hit at 230 (a reach-ignoring engine gives 160 and
    misses), not at 250 (ignoring range_mult gives 300 and hits)."""
    rules = {"range_mult": table9(m1=1, z=1, p1=0.8)}
    r = reach9(z=1, p1=1.5)
    assert _fired(_duel(r, dist=230.0, rules=rules)), "no hit at 230, effective range should be 240"
    res = _duel(r, dist=250.0, rules=rules)
    assert _silent(res), "hit at 250, effective range should be 240: shots %s" % (res.shots,)


# ---- 3. offsets are signed: index = target layer - own layer + 4 ---------------------------------------

@pytest.mark.parametrize("name,reach,own,tgt,fires", [
    ("up_only_fires_up",     reach9(z=1, p1=1), 3, 4, True),
    ("up_only_not_down",     reach9(z=1, p1=1), 4, 3, False),
    ("down_only_fires_down", reach9(m1=1, z=1), 4, 3, True),
    ("down_only_not_up",     reach9(m1=1, z=1), 3, 4, False),
])
def test_reach_offsets_are_signed(name, reach, own, tgt, fires):
    """S-164 / SPEC 15.1: a type with reach only upward (offsets 0 and +1) fires at a target one layer
    above and not at one below; the mirror type (offsets -1 and 0) fires down and not up. Four fights,
    attacker on `own`, dummy on `tgt`, 100 apart; the two firing cases are the positive controls."""
    res = _duel(reach, dist=100.0, own_layer=own, tgt_layer=tgt)
    if fires:
        assert _fired(res), "%s: no fire (shots %s)" % (name, res.shots)
    else:
        assert _silent(res), "%s: fired the wrong way (shots %s)" % (name, res.shots)


# ---- 4. not an acquisition candidate -----------------------------------------------------------------

def test_zero_reach_target_is_not_a_candidate_so_the_farther_eligible_one_is_shot():
    """S-164 / SPEC 15.1: a unit with reach 0 to the near enemy's layer (+1, at 50) and full reach to a
    farther enemy on its own layer (150) shoots the farther one (policy nearest, among the eligible).
    The near one takes nothing. Control: with reach at +1 as well, the near one is the target."""
    def fight(reach):
        scn = _scn([grp("A", "shooter", ATTACKER_X, ATTACKER_Y, 3),
                    grp("B", "dummy", ATTACKER_X + 50.0, ATTACKER_Y, 4),
                    grp("B", "dummy", ATTACKER_X + 150.0, ATTACKER_Y, 3)],
                   types={"shooter": {"reach": reach}})
        return run(scn, seed=0)

    res = fight(reach9(z=1))
    near, far = res.unit[1]["hp"], res.unit[2]["hp"]
    assert far < 1.0e6, "the farther eligible enemy took no damage"
    assert near == 1.0e6, "the zero-reach near enemy was shot (hp %g)" % near
    ctl = fight(reach9(z=1, p1=1))
    assert ctl.unit[1]["hp"] < 1.0e6 and ctl.unit[2]["hp"] == 1.0e6, "control: nearest should win with reach"


# ---- 5. area fire and the burst trigger -------------------------------------------------------------

def test_area_fire_respects_zero_reach():
    """S-164 / SPEC 15.1: reach applies to area fire. A bombard-like type (aoe_r 150) with zero reach to
    the layer above never fires at a target there; with reach[+1] = 1.0 it does (positive control)."""
    assert _silent(_duel(reach9(z=1), dist=100.0, atype="bomber")), "area unit fired at zero reach"
    assert _fired(_duel(reach9(z=1, p1=1), dist=100.0, atype="bomber")), "positive control: no area fire"


def _burst(reach):
    """A quiet caster (normal fire never lands) against three clustered dummies one layer above, 300 away:
    the cluster is inside the caster's range 450 and within one ab_radius 120, so a cast is due."""
    scn = _scn([grp("A", "quiet_caster", ATTACKER_X, ATTACKER_Y, 3)] +
               [grp("B", "dummy", ATTACKER_X + 300.0, ATTACKER_Y + dy, 4) for dy in (-50.0, 0.0, 50.0)],
               types={"quiet_caster": {"reach": reach}}, max_ticks=80)
    return run(scn, seed=0)


def test_burst_trigger_respects_zero_reach():
    """S-164 / SPEC 15.1 and 5.6: a caster with zero reach to the targets' layer never triggers its burst
    (no cast, no shot, no damage); with reach[+1] = 1.0 it casts (positive control: 3 hits of 24)."""
    res = _burst(reach9(z=1))
    assert _silent(res), "burst cast at zero reach: shots %s damage %s" % (res.shots, res.damage_dealt)
    ctl = _burst(reach9(z=1, p1=1))
    assert ctl.shots[0] >= 1 and ctl.damage_dealt[0] == pytest.approx(72.0), \
        "positive control: shots %s damage %s" % (ctl.shots, ctl.damage_dealt)


# ---- 6. loader and validation ---------------------------------------------------------------------------

def _type_index(scn, name):
    return list(scn["types"]).index(name)


def _c_type(scn, name):
    return scenario.to_c(scn).types[_type_index(scn, name)]


def _scn_with(reach):
    return _scn([grp("A", "shooter", ATTACKER_X, ATTACKER_Y, 3),
                 grp("B", "dummy", ATTACKER_X + 100.0, ATTACKER_Y, 4)],
                types={"shooter": {"reach": reach}} if reach is not None else None)


def test_loader_list_sets_reach_on_and_the_entries():
    """SPEC 15.1 / 15.4: a reach list of 9 sets reach_on = 1 and the entries by index (a type without
    reach has reach_on 0). Loader behaviour, already plumbed: passes before the engine rung."""
    vals = [0.0, 0.1, 0.2, 0.3, 1.0, 1.5, 2.0, 2.5, 3.0]
    tc = _c_type(_scn_with(vals), "shooter")
    assert tc.reach_on == 1 and list(tc.reach) == vals
    assert _c_type(_scn_with(None), "shooter").reach_on == 0


@pytest.mark.parametrize("keytype", [int, str])
def test_dict_reach_equals_the_matching_list_and_missing_offsets_are_zero(keytype):
    """SPEC 15.1 / 15.4: a dict {offset: mult} is the list with missing offsets 0 (keys are ints or
    strings, as TOML gives strings). The C type matches, the fights match byte for byte, and the dict
    {0: 1.0} (everything else missing, so 0) never fires at the layer above: that last check is the
    engine behaviour and fails until the stub is replaced."""
    d = {keytype(-1): 0.5, keytype(0): 1.0, keytype(1): 1.5}
    lst = [0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 0.0, 0.0, 0.0]
    a, b = _c_type(_scn_with(d), "shooter"), _c_type(_scn_with(lst), "shooter")
    assert a.reach_on == b.reach_on == 1 and list(a.reach) == list(b.reach) == lst
    assert run(_scn_with(d), seed=3).raw == run(_scn_with(lst), seed=3).raw
    only_own = run(_scn_with({keytype(0): 1.0}), seed=0)
    assert _silent(only_own), "dict with only offset 0 fired up: shots %s" % (only_own.shots,)


@pytest.mark.parametrize("bad", [[1.0] * 8, [1.0] * 10, []])
def test_reach_list_of_the_wrong_length_raises_value_error(bad):
    """SPEC 15.1 / 15.4: the loader raises ValueError for a list that is not 9 long. Control: 9 is fine.
    Loader behaviour, already plumbed: passes before the engine rung."""
    assert run(_scn_with([1.0] * 9), seed=0).ticks > 0
    with pytest.raises(ValueError, match="reach"):
        run(_scn_with(bad), seed=0)


@pytest.mark.parametrize("entry", [-0.5, float("nan"), float("inf"), float("-inf")])
def test_reach_negative_or_non_finite_entry_is_rejected_by_validation(entry):
    """SPEC 15.1 ll_reach_validate: every reach entry of a reach_on type is finite and >= 0. The loader
    does not check values, so the error surfaces from the engine as RuntimeError from ll_run (as the
    other validation tests, e.g. test_pulse.py) whose message names reach. Control: a good list runs."""
    ok = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    assert run(_scn_with(ok), seed=0).ticks > 0
    bad = list(ok)
    bad[5] = entry
    with pytest.raises(RuntimeError, match="reach"):
        run(_scn_with(bad), seed=0)


def test_a_type_without_reach_behaves_like_version_2():
    """SPEC 15.1: no `reach` means reach_on 0 and every offset 1.0: with the tables on, the shooter fires
    at the layer above and the zero-reach silence of the tests above is not the default. Legacy check:
    passes before the engine rung."""
    res = run(_scn_with(None), seed=0)
    assert _fired(res)
    assert _c_type(_scn_with(None), "shooter").reach_on == 0


# ---- mixed fight used by the compatibility and determinism tests ----------------------------------------

def _mixed(per_type_reach=None):
    """Mixed fight, default spawn jitter (the seed varies the draw), attack-move, two layers, area fire
    and a burst caster. per_type_reach: {type name: reach} applied over the types used, or None."""
    groups = [
        grp("A", "raider", 800.0, 900.0, 3, count=4, order="attack_move", goal=[2600.0, 1000.0]),
        grp("A", "bombard", 700.0, 1100.0, 3, count=2, order="attack_move", goal=[2600.0, 1000.0]),
        grp("A", "caster", 750.0, 1000.0, 4, count=1, order="attack_move", goal=[2600.0, 1000.0]),
        grp("B", "vanguard", 2200.0, 950.0, 3, count=3, order="attack_move", goal=[800.0, 1000.0]),
        grp("B", "warden", 2250.0, 1050.0, 4, count=3, order="attack_move", goal=[800.0, 1000.0]),
        grp("B", "interceptor", 2300.0, 1000.0, 4, count=2, order="attack_move", goal=[800.0, 1000.0]),
    ]
    scn = make_scenario(groups, run={"max_ticks": 400, "stalemate_ticks": 6000},
                        rules={"range_mult": CROSS, "dmg_mult": CROSS, "aoe_layer_mult": CROSS})
    for name, r in (per_type_reach or {}).items():
        scn["types"][name] = {**scn["types"][name], "reach": r}
    return scn


def _trace_bytes(res):
    return res.trace.tobytes()


# ---- 7. backward compatibility: no reach is identical to all-ones reach ----------------------------------

def test_no_reach_equals_reach_of_all_ones():
    """SPEC 15 intro and 15.1: a scenario without reach is byte-identical (result fields and trace) to the
    same scenario whose every type carries reach = [1.0] * 9 (reach_on 1, every offset 1.0). Legacy
    check: passes before the engine rung and must keep passing after it."""
    plain = _mixed()
    ones = _mixed({n: [1.0] * 9 for n in plain["types"]})
    assert all(_c_type(ones, n).reach_on == 1 for n in ones["types"])
    assert all(_c_type(plain, n).reach_on == 0 for n in plain["types"])
    for seed in (0, 1, 2):
        a, b = run(plain, seed=seed, trace=True), run(ones, seed=seed, trace=True)
        assert a.shots[0] + a.shots[1] > 0, "the mixed fight must have fire, or it proves nothing"
        assert a.raw == b.raw, "result bytes differ at seed %d" % seed
        assert _trace_bytes(a) == _trace_bytes(b), "trace bytes differ at seed %d" % seed


# ---- 8. determinism ---------------------------------------------------------------------------------------

def test_reach_scenario_is_byte_identical_across_o0_and_o2():
    """SPEC 9 and 15.1: a scenario that uses reach (several types, different tables, fractional and zero
    entries) gives identical result and trace bytes under lib O0 and O2. The fight must also differ from
    the same fight without reach, so the determinism check exercises the reach (fails until the stub is
    replaced: the stub ignores reach)."""
    reach = {
        "raider": reach9(z=1),                          # own layer only
        "bombard": reach9(m1=0.75, z=1, p1=0.5),
        "caster": reach9(z=1, p1=1.25),
        "vanguard": reach9(z=1, p1=1),                  # up, not down
        "warden": reach9(m1=1, z=1),                    # down, not up
        "interceptor": reach9(m1=0.5, z=1.5, p1=0.5),
    }
    scn = _mixed(reach)
    plain = _mixed()
    differs = False
    for seed in (0, 1, 2):
        o0, o2 = run(scn, seed=seed, trace=True, lib="O0"), run(scn, seed=seed, trace=True, lib="O2")
        assert o0.raw == o2.raw, "result bytes differ O0 vs O2 at seed %d" % seed
        assert _trace_bytes(o0) == _trace_bytes(o2), "trace differs O0 vs O2 at seed %d" % seed
        differs = differs or o2.raw != run(plain, seed=seed, trace=True).raw
    assert differs, "the reach scenario gave the same result as no reach: reach was never exercised"
