# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2; defects D1, D10); ledger FINDING-lab-d1, FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T2 (R6, D1, D10): the inert-knob probe. Before a family is swept on a play, the knob at the band's extreme must change
SOME row against its base across the sweep's coarse headcounts and seeds 0 and 1; otherwise the batch refuses the family on that
play and says so in the artifact. A family is inert on a (play, layout) only when EVERY row at the extreme is byte-identical to its base
row at every (headcount, seed); one differing row means NOT inert (Architect ruling 2026-10-20, rev 3 plan R6; reason: the one-point
probe, 16 heads seed 0, refused range_up on s3_layer_above although the sweep measured it biting at 32, 40 and 48 heads). The headcounts
are NOT a literal list, they are the sweep's own coarse list, sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP))
| {sweep.ENEMY_TO}) (scan.scan builds that expression inline; there is no function to import, the tests write it out as COARSE); every
count below is derived from len(COARSE): 2 seeds x len(COARSE) points, N_FIGHTS = 2 * 2 * len(COARSE) fights without a base cache,
2 * len(COARSE) with the base rows cached. "A row" is what rows.fight_row reads: a field it ignores (firing, winner) cannot make a knob
bite, a field it reads (ticks, survivors, reengage, margin ...) can. Fast half, driven by fakes (no engine). The real-engine half is
tests/skilllab/integration/test_rev3_a_probe_real.py; the `probed` record, the sweep.run cache and the artifact are
tests/skilllab/test_rev3_a_probed.py; the frozen names are tests/skilllab/test_rev3_a_frozen_names.py.

BUILDER CONTRACT (the names are the test writer's DRAFT, the Architect may veto; the plan names only the files probe.py and sweep.py):
  scripts/skilllab/probe.py
    survey(build, settings, heads=None, seeds=(0, 1), swap=False, fight_fn=None, base_settings=None, base_cache=None) -> dict
        `heads=None` means the sweep's coarse list above. For every (h, seed) of heads x seeds, in that order (heads major), fights
        `build(h, swap)` through `fight_fn(setup, seed, swap)` (default fight.fight): the base (with `base_settings` merged into
        `setup.settings`; None: nothing added) and the knob (`settings` merged); returns
            {(h, seed): {"differed": bool, "base_cached": bool}}
        `differed` is True when `rows.fight_row` of the two results differs. Never stops early: every point is fought whatever the rows say.
        `base_cache` is a dict the CALLER owns (None: no caching): the base row of (h, seed) is looked up in it and, when present, the
        base fight is NOT made and `base_cached` is True; otherwise the base is fought, its row stored under (h, seed) and `base_cached`
        is False. The caller keys the dict per (play, layout, base settings): the base is the family's keys at BASES, the same fight for
        every knob of every family with those keys.
    inert(build, settings, heads=None, seeds=(0, 1), swap=False, fight_fn=None, base_settings=None, base_cache=None) -> bool
        True when no point differed, i.e. `not any(v["differed"] for v in survey(...).values())`. When it says True it has fought the
        whole set; when it says False the fights it made are a subset of the survey's (it may stop at the first differing row).
        `base_settings` exists for families whose point sets a CO-SETTING besides the knob: the emitting point sets the joint vision as
        well as OM_TP_EMIT_SIGHT_MULT / OM_TP_EMIT_SEEN_MULT, and a base at the default vision would differ through the vision alone.
        The probe of a family fights, as its base, the extreme point with ONLY the family's own keys at sweep.BASES.
  scripts/skilllab/sweep.py
    run_family(..., probe=False, base_cache=None) (probe defaults to False and stays so; the batch runner and the CLI turn it on, see
    tests/skilllab/test_rev3_a_batch.py; `base_cache` is the caller's dict, None: a private one). With probe=True, before scanning a
    (play, layout) the family's EXTREME grid point (the SMALLEST value: range_up and damage_up 0.25, vision 0.125) is surveyed on the
    play's own "play" build at the coarse headcounts and seeds 0 and 1, the cache key being (play, layout, tuple(sorted(base settings
    .items()))). When no row differs the (play, layout) is not scanned, no row of that play is written (control rows included), the
    probe's own fights are the only fights of that play, and `entry["refused"]` gains
        {"family", "play", "layout", "role": "play", "reason": "inert_knob", "checked": COARSE, "seeds": [0, 1]}
    (`checked` is the coarse list as a list of ints). A play with one differing row runs as without the probe. A (play, layout) refused
    earlier by the pre-flight is not probed and has no record; arc and cone (no OM_TP_* setting) are not probed at all. The entry gains
    `entry["probed"]`, one record per (family, play, layout) probed, refused or not (tests/skilllab/test_rev3_a_probed.py).
    Real families set the one-layer and two-layer knobs together (sweep._range_up, _vision_settings).
Red today: `probe.survey` does not exist, `inert` has no `heads`/`seeds` keywords and probes one point, run_family refuses on one point,
has no `base_cache`, and its refusals carry no `checked`/`seeds`."""
import csv
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab import rows as rows_mod, scan, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

BASE = {"OM_TP_RANGE_UP_1": 1.0, "OM_TP_RANGE_UP_2": 1.0, "OM_TP_RANGE_DOWN_1": 1.0, "OM_TP_RANGE_DOWN_2": 1.0}
CAPS = sweep.Capabilities(arc=True, cone=True)


def changed(setup):
    return any(setup.settings.get(k, v) != v for k, v in BASE.items())


def reacts(pred=None, *plays, field=None):
    """A fight function whose result moves when a range knob leaves its base, on the named plays only (none named: every play) and only
    at the (headcount, seed) points where `pred(enemy, seed)` holds (None: everywhere). By default the margin moves; `field`, a
    (name, value) pair, moves that FightResult field instead and leaves the margin alone."""
    def result(setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        hit = changed(setup) and (not plays or setup.unit_types["_play"] in plays) and (pred is None or pred(enemy, seed))
        base = _fr("side0" if enemy <= 24 else "side1", enemy, margin=0.5)
        if not hit:
            return base
        return dataclasses.replace(base, **{field[0]: field[1]}) if field else _fr("side0" if enemy <= 24 else "side1", enemy, margin=0.25)
    return result


def sensitive_plays(*plays, heads=None, seeds=None):
    """`reacts` for the named plays, only at the named headcounts and seeds (None: everywhere); no play named: no play reacts."""
    if not plays:
        return reacts(lambda e, sd: False)
    return reacts(lambda e, sd: (heads is None or e in heads) and (seeds is None or sd in seeds), *plays)


def plain_build(enemy_heads, swap):
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": "p", "_role": "play"})


def fought(result_of):
    fight_fn = ScriptedFight(result_of=result_of)
    return fight_fn, fight_fn.calls


KNOB = {"OM_TP_RANGE_UP_1": 0.25}
COARSE = sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP)) | {sweep.ENEMY_TO})   # the sweep's own coarse list
HEADS, SEEDS = tuple(COARSE), (0, 1)
SWEEP_SET = {(h, s) for h in HEADS for s in SEEDS}
N_FIGHTS = 2 * 2 * len(COARSE)          # base + knob, two seeds, every coarse headcount
N_CACHED = 2 * len(COARSE)              # the knob fights alone, the base rows cached
AT = COARSE[3]                          # a headcount in the middle of the list (32 today)


def flags(got):
    """The survey dict reduced to {(heads, seed): differed}."""
    return {k: v["differed"] for k, v in got.items()}


def fought_pairs(calls):
    """{(heads, seed): [knob-moved?, ...]} over the recorded calls: each (heads, seed) should be fought once as base, once moved."""
    out = {}
    for c in calls:
        out.setdefault((c["enemy"], c["seed"]), []).append(changed(c["setup"]))
    return out


def test_positive_control_the_sensitive_fake_changes_its_row_and_the_inert_one_does_not():
    """Green on the lab tip: the fakes below are what they claim, so a True or False from the probe is the probe's."""
    sens = ScriptedFight(result_of=sensitive_plays("p"))
    base = plain_build(COARSE[1], False)
    moved = Setup(groups=(), unit_types=base.unit_types, settings=dict(KNOB))
    assert rows_mod.fight_row(sens(base, 0, False)) != rows_mod.fight_row(sens(moved, 0, False))
    flat = ScriptedFight(result_of=sensitive_plays())
    assert rows_mod.fight_row(flat(base, 0, False)) == rows_mod.fight_row(flat(moved, 0, False))
    only_at = ScriptedFight(result_of=sensitive_plays("p", heads=(AT,)))

    def differs(h, seed, fn):
        b = plain_build(h, False)
        return rows_mod.fight_row(fn(b, seed, False)) != rows_mod.fight_row(fn(Setup(groups=(), unit_types=b.unit_types, settings=dict(KNOB)), seed, False))

    assert [differs(h, 0, only_at) for h in HEADS] == [h == AT for h in HEADS]
    only1 = ScriptedFight(result_of=sensitive_plays("p", seeds=(1,)))
    assert [differs(COARSE[1], sd, only1) for sd in SEEDS] == [False, True]


def test_positive_control_the_row_compares_what_fight_row_reads_and_nothing_else():
    """Green on the lab tip (D2 of the audit): the fields the fakes below move are read by rows.fight_row (ticks, survivors, reengage)
    or ignored by it (firing, winner), so a probe that compares FightResult equality, or only the margin, is caught."""
    base = _fr("side0", 16)
    for name, value in (("ticks", base.ticks + 1), ("survivors", (7, 1)), ("reengage", (1, 0))):
        assert rows_mod.fight_row(dataclasses.replace(base, **{name: value})) != rows_mod.fight_row(base), name
    for name, value in (("firing", [(1, 2, 3)]), ("winner", "side1")):
        assert dataclasses.replace(base, **{name: value}) != base
        assert rows_mod.fight_row(dataclasses.replace(base, **{name: value})) == rows_mod.fight_row(base), name


def test_t2_the_probe_says_inert_only_when_no_row_moves_and_then_fights_the_whole_sweep_set():
    """T2 (i, ii, iv; R6): a fake flat everywhere is inert, and the fights are exactly the sweep's coarse headcounts (scan.COARSE_STEP)
    x seeds 0 and 1, each once as base (no knob) and once with the knob: N_FIGHTS. Red today: the probe fights 2 at 16 heads, seed 0."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays())
    assert probe.inert(plain_build, {"OM_TP_RANGE_UP_2": 0.25}, fight_fn=fight_fn) is True
    assert len(calls) == N_FIGHTS
    pairs = fought_pairs(calls)
    assert set(pairs) == SWEEP_SET and all(sorted(v) == [False, True] for v in pairs.values()), pairs


def test_t2_a_row_that_moves_at_one_mid_headcount_only_is_not_inert_and_the_survey_says_bites_from_there():
    """T2 (i, R6) the regression: a knob silent below one headcount and biting from it is not inert. Red today: the one-point probe at
    16 heads says inert."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p", heads=[h for h in COARSE if h >= AT]))
    assert probe.inert(plain_build, KNOB, fight_fn=fight_fn) is False
    fight_fn, calls = fought(sensitive_plays("p", heads=(AT,)))
    got = probe.survey(plain_build, KNOB, fight_fn=fight_fn)
    assert flags(got) == {(h, s): h == AT for h in HEADS for s in SEEDS}
    assert min(h for (h, s), differed in flags(got).items() if differed) == AT


def test_t2_a_row_that_moves_for_one_seed_only_is_not_inert():
    """T2 (iii, R6): the fake reacts on seed 1 only, at every headcount; seed 0 alone would read inert. Red today: seed 0 only."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(sensitive_plays("p", seeds=(1,)))
    assert probe.inert(plain_build, KNOB, fight_fn=fight_fn) is False
    fight_fn, _ = fought(sensitive_plays("p", seeds=(1,)))
    got = probe.survey(plain_build, KNOB, fight_fn=fight_fn)
    assert flags(got) == {(h, s): s == 1 for h in HEADS for s in SEEDS}


def test_t2_the_survey_does_not_stop_early_and_records_every_point():
    """T2 (v): the fake reacts from the very first point (smallest headcount, seed 0) and the survey still fights all N_FIGHTS and
    reports which points differ. Red today: no `survey`."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p", heads=(COARSE[0],)))
    got = probe.survey(plain_build, KNOB, fight_fn=fight_fn)
    assert len(calls) == N_FIGHTS and set(fought_pairs(calls)) == SWEEP_SET
    assert list(got) == sorted(SWEEP_SET) and {k for k, d in flags(got).items() if d} == {(COARSE[0], 0), (COARSE[0], 1)}


def test_t2_the_survey_of_an_inert_knob_is_all_false():
    """T2 (ii): inert is the survey with no True. Red today: no `survey`."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(sensitive_plays())
    assert flags(probe.survey(plain_build, KNOB, fight_fn=fight_fn)) == {k: False for k in SWEEP_SET}


def test_t2_the_probe_says_not_inert_when_the_row_moves():
    """T2 positive control (R6): the one-layer knob moving the row everywhere is not inert, and the survey is all True."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(sensitive_plays("p"))
    assert probe.inert(plain_build, KNOB, fight_fn=fight_fn) is False
    fight_fn, _ = fought(sensitive_plays("p"))
    assert flags(probe.survey(plain_build, KNOB, fight_fn=fight_fn)) == {k: True for k in SWEEP_SET}


@pytest.mark.parametrize("field", [("ticks", 101), ("survivors", (7, 1)), ("reengage", (1, 0))])
def test_t2_a_row_field_other_than_the_margin_moving_alone_is_not_inert(field):
    """T2 (D2 of the audit): the knob changes ONE field of the row and nothing else (the margin is untouched): ticks, survivors or
    reengage; the probe reads the row, so it is not inert at any point. Red today: the probe reads one point only; red after a builder
    that compares only the margin."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(reacts(None, "p", field=field))
    assert probe.inert(plain_build, KNOB, fight_fn=fight_fn) is False
    fight_fn, _ = fought(reacts(None, "p", field=field))
    assert flags(probe.survey(plain_build, KNOB, fight_fn=fight_fn)) == {k: True for k in SWEEP_SET}


@pytest.mark.parametrize("field", [("firing", [(1, 2, 3)]), ("winner", "side1")])
def test_t2_a_field_the_row_ignores_moving_alone_is_inert(field):
    """T2 positive control (D2 of the audit): firing and winner are not in rows.fight_row, so a knob that moves only them leaves the row
    identical at every point: inert (a builder comparing FightResult equality reads it as not inert and fails here)."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(reacts(None, "p", field=field))
    assert probe.inert(plain_build, KNOB, fight_fn=fight_fn) is True


def test_t2_the_probe_fights_base_unchanged_and_the_extreme_with_the_settings_merged():
    """T2: one fight carries no probe setting, the other carries exactly the knob's settings, at the asked headcount and seed."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    probe.inert(plain_build, {"OM_TP_RANGE_UP_1": 0.25, "OM_TP_RANGE_UP_2": 0.25}, heads=(20,), seeds=(3,), swap=True, fight_fn=fight_fn)
    assert sorted(((c["settings"].get("OM_TP_RANGE_UP_1"), c["settings"].get("OM_TP_RANGE_UP_2")) for c in calls),
                  key=lambda pair: (pair[0] is not None, pair)) == [(None, None), (0.25, 0.25)]
    assert {(c["enemy"], c["seed"], c["swap"]) for c in calls} == {(20, 3, True)}


def test_t2_the_default_headcounts_are_the_sweeps_coarse_list_read_from_scan():
    """T2 (Q2): `heads=None` fights the coarse list derived from scan.COARSE_STEP and sweep.ENEMY_FROM/ENEMY_TO, not a literal.
    Red today: no `survey`."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays())
    probe.survey(plain_build, KNOB, fight_fn=fight_fn)
    assert sorted({c["enemy"] for c in calls}) == COARSE


def test_t2_a_second_knob_of_the_same_family_fights_the_base_rows_once_in_total():
    """T2 (Q1 i): with a caller-owned `base_cache` the first knob fights N_FIGHTS (bases and knobs) and a second knob of the same family
    on the same (play, layout) fights N_CACHED, knobs only: no (heads, seed) base fight is repeated. Red today: no `survey`."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    cache = {}
    probe.survey(plain_build, {"OM_TP_RANGE_UP_1": 0.25}, fight_fn=fight_fn, base_cache=cache)
    assert len(calls) == N_FIGHTS and set(cache) == SWEEP_SET
    first = len(calls)
    probe.survey(plain_build, {"OM_TP_RANGE_UP_1": 0.5}, fight_fn=fight_fn, base_cache=cache)
    second = calls[first:]
    assert len(second) == N_CACHED and all(changed(c["setup"]) for c in second)
    bases = [(c["enemy"], c["seed"]) for c in calls if not changed(c["setup"])]
    assert len(bases) == len(set(bases)) == N_CACHED


def test_t2_the_survey_records_whether_the_base_row_came_from_the_cache():
    """T2 (Q1 ii): every point carries `base_cached`: False on the first knob, True on the second; with no cache it is always False.
    A cached base gives the same `differed` as a fought one. Red today: no `survey`."""
    from scripts.skilllab import probe
    fight_fn, _ = fought(sensitive_plays("p", heads=(AT,)))
    cache = {}
    one = probe.survey(plain_build, KNOB, fight_fn=fight_fn, base_cache=cache)
    two = probe.survey(plain_build, KNOB, fight_fn=fight_fn, base_cache=cache)
    assert {v["base_cached"] for v in one.values()} == {False} and {v["base_cached"] for v in two.values()} == {True}
    assert flags(one) == flags(two) == {(h, s): h == AT for h in HEADS for s in SEEDS}
    plain = probe.survey(plain_build, KNOB, fight_fn=fight_fn)
    assert {v["base_cached"] for v in plain.values()} == {False}


def test_t2_the_base_fight_carries_the_base_settings_when_given():
    """T2 (W3 support): base_settings go into the base fight only, so a co-setting shared by both fights cannot make the knob look live."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    probe.survey(plain_build, {"OM_TP_VISION_UP_1": 0.125, "OM_TP_EMIT_SIGHT_MULT": 1.0}, heads=(COARSE[1],), seeds=(0,), fight_fn=fight_fn,
                 base_settings={"OM_TP_VISION_UP_1": 0.125, "OM_TP_EMIT_SIGHT_MULT": 2.0})
    assert sorted(c["settings"]["OM_TP_EMIT_SIGHT_MULT"] for c in calls) == [1.0, 2.0]
    assert {c["settings"]["OM_TP_VISION_UP_1"] for c in calls} == {0.125}


def run(tmp_path, plays, result_of, family="range_up", layouts=None, builds=None, **kw):
    fight_fn = ScriptedFight(result_of=result_of)
    entry = sweep.run_family(family, tmp_path, builds=builds or fake_builds(), layouts=layouts or {"A": {"id": 1}}, plays=plays,
                             fight_fn=fight_fn, caps=CAPS, **kw)
    return entry, fight_fn


@pytest.mark.parametrize("family", ["emitting", "vision", "range_up"])
def test_t2_run_family_probes_the_extreme_against_the_family_keys_at_bases_only(tmp_path, family):
    """T2 (D1 of the audit, W3): through run_family(probe=True), for every sweep point (heads, seed) there are exactly two fights, the
    moved one carrying the family's extreme point as it stands (the smallest value) and the base one carrying the same point with ONLY
    the family's own keys at sweep.BASES: for emitting the two EMIT_* multipliers at their bases and the joint vision co-setting still
    at its extreme (0.125, 0.05); for the others every key of the point at its base. A builder that resets every key, or only some,
    or none, fails. Red today: one point, the base is the build as is."""
    point = min(sweep.grid(family), key=lambda p: p.value).settings
    own = ("OM_TP_EMIT_SIGHT_MULT", "OM_TP_EMIT_SEEN_MULT") if family == "emitting" else tuple(point)
    base = {**point, **{k: sweep.BASES[k] for k in own}}
    if family == "emitting":
        assert (base["OM_TP_VISION_UP_1"], base["OM_TP_VISION_UP_2"]) == (0.125, 0.05) and base != {k: sweep.BASES[k] for k in point}
    entry, fight_fn = run(tmp_path, ("p1",), sensitive_plays(), family=family, probe=True)
    assert [r["reason"] for r in entry["refused"]] == ["inert_knob"]
    by_point = {}
    for c in fight_fn.calls:       # the family's designated-play controls (vision, damage_up) run on their own play after the loop
        if c["play"] != "p1":
            continue
        by_point.setdefault((c["enemy"], c["seed"]), []).append(c["settings"])
    assert set(by_point) == SWEEP_SET
    for k, got in by_point.items():
        assert sorted(got, key=lambda d: sorted(d.items())) == sorted([point, base], key=lambda d: sorted(d.items())), (k, got)


def test_t2_a_family_inert_on_a_play_is_refused_there_and_run_on_the_others(tmp_path):
    """T2 (R6, D10, iv): p1 does not respond to the knob, p2 does: p1 is listed `inert_knob` with what the probe checked, writes no row
    and is fought only by the probe, N_FIGHTS fights over the sweep's coarse headcounts x seeds 0 and 1; p2 runs. Red today: the
    refusal comes from one point (2 fights) and carries no `checked`/`seeds`."""
    entry, fight_fn = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"), probe=True)
    assert entry["refused"] == [{"family": "range_up", "play": "p1", "layout": "A", "role": "play", "reason": "inert_knob",
                                 "checked": COARSE, "seeds": [0, 1]}]
    p1 = [c for c in fight_fn.calls if c["play"] == "p1"]
    assert len(p1) == N_FIGHTS and {(c["enemy"], c["seed"]) for c in p1} == SWEEP_SET
    with open(tmp_path / entry["csv"], newline="") as fh:
        plays = {r["play"] for r in csv.DictReader(fh)}
    assert plays == {"p2"}


def test_t2_a_family_that_bites_from_a_mid_headcount_is_not_refused_and_runs(tmp_path):
    """T2 (R6) the regression through run_family: the fake is silent below one headcount and reacts from it; the play is not refused
    and is swept. Red today: the one-point probe at 16 heads refuses it."""
    entry, _ = run(tmp_path, ("p1",), sensitive_plays("p1", heads=[h for h in COARSE if h >= AT]), probe=True)
    assert entry["refused"] == []
    with open(tmp_path / entry["csv"], newline="") as fh:
        assert {r["play"] for r in csv.DictReader(fh)} == {"p1"}


def test_t2_a_family_that_reacts_on_seed_1_only_is_not_refused(tmp_path):
    """T2 (iii) through run_family: seed 1 only moves the row. Red today: seed 0 alone is probed."""
    entry, _ = run(tmp_path, ("p1",), sensitive_plays("p1", seeds=(1,)), probe=True)
    assert entry["refused"] == []


def test_t2_two_plays_and_two_layouts_never_share_base_rows(tmp_path):
    """T2 (D3 of the audit): the base differs by play (p1 0.5, p2 0.4) and the knob changes nothing, so both plays are inert; with one
    `base_cache` dict passed to run_family each (play, layout) still costs N_FIGHTS: a cache keyed without the play would hand p2 the
    rows of p1 and read p2 as biting (not refused); keyed without the layout it would halve the cost of layout B (the fakes do not tell
    the layouts apart, so the per-play count is 2 x N_FIGHTS). Red today: no `base_cache`."""
    def result(setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        return _fr("side0" if enemy <= 24 else "side1", enemy, margin=0.5 if setup.unit_types["_play"] == "p1" else 0.4)

    entry, fight_fn = run(tmp_path, ("p1", "p2"), result, layouts={"A": {"id": 1}, "B": {"id": 2}}, probe=True, base_cache={})
    assert [(r["play"], r["layout"]) for r in entry["refused"]] == [("p1", "A"), ("p2", "A"), ("p1", "B"), ("p2", "B")]
    for play in ("p1", "p2"):
        assert len([c for c in fight_fn.calls if c["play"] == play]) == 2 * N_FIGHTS


def only_at(value, *plays):
    """A fight function that reacts to OM_TP_RANGE_UP_1 == `value` only (not to any other change from base)."""
    def result(setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        hit = setup.settings.get("OM_TP_RANGE_UP_1") == value and setup.unit_types["_play"] in plays
        return _fr("side0" if enemy <= 24 else "side1", enemy, margin=0.25 if hit else 0.5)
    return result


def test_t2_the_probe_uses_the_extreme_grid_point_and_a_knob_that_bites_there_is_not_refused(tmp_path):
    """T2 (W2): the fake reacts at 0.25 (the grid point with the smallest value) and nowhere else: the play is not refused."""
    assert min(p.value for p in sweep.grid("range_up")) == 0.25
    entry, _ = run(tmp_path, ("p1",), only_at(0.25, "p1"), probe=True)
    assert entry["refused"] == []


def test_t2_a_knob_that_bites_only_near_base_is_inert_for_the_probe(tmp_path):
    """T2 (W2): the fake reacts at 0.75 only; the probe fights the extreme 0.25 at every sweep point, sees no change and refuses the
    play (N_FIGHTS fights), although the coarse grid would have shown a change at 0.75."""
    entry, fight_fn = run(tmp_path, ("p1",), only_at(0.75, "p1"), probe=True)
    assert [(r["play"], r["reason"]) for r in entry["refused"]] == [("p1", "inert_knob")]
    assert len(fight_fn.calls) == N_FIGHTS


def test_t2_a_family_that_bites_everywhere_refuses_nothing(tmp_path):
    """T2 positive control (R6): both plays respond, nothing is refused and both play."""
    entry, _ = run(tmp_path, ("p1", "p2"), sensitive_plays("p1", "p2"), probe=True)
    assert entry["refused"] == []
    with open(tmp_path / entry["csv"], newline="") as fh:
        assert {r["play"] for r in csv.DictReader(fh)} == {"p1", "p2"}


def test_positive_control_without_the_probe_an_inert_play_is_swept_like_any_other(tmp_path):
    """Green on the lab tip: the probe is the only thing that refuses it (the default is the Architect's, see the module docstring)."""
    entry, _ = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"))
    assert entry["refused"] == []
