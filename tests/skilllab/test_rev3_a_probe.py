# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2; defects D1, D10); ledger FINDING-lab-d1, FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T2 (R6, D1, D10): the inert-knob probe. Before a family is swept on a play, ONE fight with the knob at the band's extreme
must change the row hash against base; otherwise the batch refuses the family on that play and says so in the artifact. Fast half,
driven by fakes (no engine). The real-engine half (s3_layer_above, the two-layer knobs) is tests/skilllab/integration/test_rev3_a_probe_real.py.

BUILDER CONTRACT (the names are the test writer's; the plan names only the files probe.py and sweep.py):
  scripts/skilllab/probe.py (NEW)
    inert(build, settings, enemy_heads=16, seed=0, swap=False, fight_fn=None, base_settings=None) -> bool
        fights `build(enemy_heads, swap)` exactly twice through `fight_fn(setup, seed, swap)` (default fight.fight): once as built plus
        `base_settings` merged into `setup.settings` (None: nothing added; the base fight), once with `settings` merged
        ({**setup.settings, **settings}); True when `rows.fight_row` of the two results is identical (the row hash did not change),
        False otherwise. Nothing else is fought. `base_settings` exists for families whose point sets a CO-SETTING besides the knob:
        the emitting point sets the joint vision (0.125 or 0.25) as well as OM_TP_EMIT_SIGHT_MULT / OM_TP_EMIT_SEEN_MULT, and a base
        fight at the default vision would differ from the extreme through the vision alone and never read inert (measured: sight 1.0,
        2.0, 4.0 at vision 0.125 give one row; the vision alone moves it). The probe of a family fights, as its base, the extreme point
        with the family's own knob keys at sweep.BASES (emitting: the two EMIT_* keys only; every other family: all its keys).
  scripts/skilllab/sweep.py
    run_family(..., probe=False) gains the keyword `probe` (default False, Architect ruling 2026-10-20: the batch runner and the CLI turn
    it on, see tests/skilllab/test_rev3_a_batch.py; fakes driving run_family elsewhere stay untouched). With probe=True, before scanning
    a (play, layout) the family's EXTREME grid point is fought through probe.inert on the play's own "play" build. PINNED (W2 of the
    audit): the extreme is the grid point with the SMALLEST value, the band's low edge 0.25 x base (range_up and damage_up 0.25,
    vision 0.125); a knob that only bites near base (0.75) is inert for the probe, a knob that bites at the extreme is not; when inert the (play, layout) is not scanned, no row of that play is written (control
    rows included), the probe's own fights are the only fights of that play, and `entry["refused"]` gains
    {"family", "play", "layout", "role": "play", "reason": "inert_knob"}. A play that is not inert runs as without the probe.
    Real families set the one-layer and two-layer knobs together (sweep._range_up, _vision_settings), so range_up's extreme point bites on
    s3_layer_above even though the two-layer knobs alone do not (tests/skilllab/integration/test_rev3_a_probe_real.py).
Red today: `scripts.skilllab.probe` does not exist and run_family has no `probe` keyword."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab import rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

BASE = {"OM_TP_RANGE_UP_1": 1.0, "OM_TP_RANGE_UP_2": 1.0, "OM_TP_RANGE_DOWN_1": 1.0, "OM_TP_RANGE_DOWN_2": 1.0}
CAPS = sweep.Capabilities(arc=True, cone=True)


def changed(setup):
    return any(setup.settings.get(k, v) != v for k, v in BASE.items())


def sensitive_plays(*plays):
    """A fight function whose result (the margin, so the row) moves when a range knob leaves its base, on the named plays only."""
    def result(setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        margin = 0.25 if changed(setup) and setup.unit_types["_play"] in plays else 0.5
        return _fr("side0" if enemy <= 24 else "side1", enemy, margin=margin)
    return result


def plain_build(enemy_heads, swap):
    return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": "p", "_role": "play"})


def fought(result_of):
    fight_fn = ScriptedFight(result_of=result_of)
    return fight_fn, fight_fn.calls


def test_positive_control_the_sensitive_fake_changes_its_row_and_the_inert_one_does_not():
    """Green on the lab tip: the fakes below are what they claim, so a True or False from the probe is the probe's."""
    sens = ScriptedFight(result_of=sensitive_plays("p"))
    base, moved = plain_build(16, False), plain_build(16, False)
    moved = Setup(groups=(), unit_types=moved.unit_types, settings={"OM_TP_RANGE_UP_1": 0.25})
    assert rows_mod.fight_row(sens(base, 0, False)) != rows_mod.fight_row(sens(moved, 0, False))
    flat = ScriptedFight(result_of=sensitive_plays())
    assert rows_mod.fight_row(flat(base, 0, False)) == rows_mod.fight_row(flat(moved, 0, False))


def test_t2_the_probe_says_inert_when_the_row_does_not_move():
    """T2 (R6): identical rows at the extreme and at base is inert. Red today: no probe module."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays())
    assert probe.inert(plain_build, {"OM_TP_RANGE_UP_2": 0.25}, fight_fn=fight_fn) is True
    assert len(calls) == 2


def test_t2_the_probe_says_not_inert_when_the_row_moves():
    """T2 positive control (R6): the one-layer knob moving the row is not inert. Red today only for the missing module."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    assert probe.inert(plain_build, {"OM_TP_RANGE_UP_1": 0.25}, fight_fn=fight_fn) is False
    assert len(calls) == 2


def test_t2_the_probe_fights_base_unchanged_and_the_extreme_with_the_settings_merged():
    """T2: one fight carries no probe setting, the other carries exactly the knob's settings, at the asked headcount and seed."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    probe.inert(plain_build, {"OM_TP_RANGE_UP_1": 0.25, "OM_TP_RANGE_UP_2": 0.25}, enemy_heads=20, seed=3, swap=True, fight_fn=fight_fn)
    assert sorted(((c["settings"].get("OM_TP_RANGE_UP_1"), c["settings"].get("OM_TP_RANGE_UP_2")) for c in calls),
                  key=lambda pair: (pair[0] is not None, pair)) == [(None, None), (0.25, 0.25)]
    assert {(c["enemy"], c["seed"], c["swap"]) for c in calls} == {(20, 3, True)}


def test_t2_the_base_fight_carries_the_base_settings_when_given():
    """T2 (W3 support): base_settings go into the base fight only, so a co-setting shared by both fights cannot make the knob look live.
    Red today: no probe module."""
    from scripts.skilllab import probe
    fight_fn, calls = fought(sensitive_plays("p"))
    probe.inert(plain_build, {"OM_TP_VISION_UP_1": 0.125, "OM_TP_EMIT_SIGHT_MULT": 1.0}, fight_fn=fight_fn,
                base_settings={"OM_TP_VISION_UP_1": 0.125, "OM_TP_EMIT_SIGHT_MULT": 2.0})
    assert sorted(c["settings"]["OM_TP_EMIT_SIGHT_MULT"] for c in calls) == [1.0, 2.0]
    assert {c["settings"]["OM_TP_VISION_UP_1"] for c in calls} == {0.125}


def run(tmp_path, plays, result_of, **kw):
    fight_fn = ScriptedFight(result_of=result_of)
    entry = sweep.run_family("range_up", tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=plays, fight_fn=fight_fn,
                             caps=CAPS, **kw)
    return entry, fight_fn


def test_t2_a_family_inert_on_a_play_is_refused_there_and_run_on_the_others(tmp_path):
    """T2 (R6, D10): p1 does not respond to the knob, p2 does: p1 is listed `inert_knob`, writes no row and is fought only by the probe;
    p2 runs. Red today: run_family has no `probe` keyword."""
    entry, fight_fn = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"), probe=True)
    assert [(r["family"], r["play"], r["layout"], r["role"], r["reason"]) for r in entry["refused"]] == [("range_up", "p1", "A", "play", "inert_knob")]
    assert len([c for c in fight_fn.calls if c["play"] == "p1"]) <= 2
    with open(tmp_path / entry["csv"], newline="") as fh:
        plays = {r["play"] for r in csv.DictReader(fh)}
    assert plays == {"p2"}


def only_at(value, *plays):
    """A fight function that reacts to OM_TP_RANGE_UP_1 == `value` only (not to any other change from base)."""
    def result(setup, seed, swap):
        enemy = setup.unit_types["enemy"]
        hit = setup.settings.get("OM_TP_RANGE_UP_1") == value and setup.unit_types["_play"] in plays
        return _fr("side0" if enemy <= 24 else "side1", enemy, margin=0.25 if hit else 0.5)
    return result


def test_t2_the_probe_uses_the_extreme_grid_point_and_a_knob_that_bites_there_is_not_refused(tmp_path):
    """T2 (W2): the fake reacts at 0.25 (the grid point with the smallest value) and nowhere else: the play is not refused. Red today:
    no `probe` keyword."""
    assert min(p.value for p in sweep.grid("range_up")) == 0.25
    entry, _ = run(tmp_path, ("p1",), only_at(0.25, "p1"), probe=True)
    assert entry["refused"] == []


def test_t2_a_knob_that_bites_only_near_base_is_inert_for_the_probe(tmp_path):
    """T2 (W2): the fake reacts at 0.75 only; the probe fights the extreme 0.25, sees no change and refuses the play, although the
    coarse grid would have shown a change at 0.75. Red today: no `probe` keyword."""
    entry, fight_fn = run(tmp_path, ("p1",), only_at(0.75, "p1"), probe=True)
    assert [(r["play"], r["reason"]) for r in entry["refused"]] == [("p1", "inert_knob")]
    assert len(fight_fn.calls) <= 2


def test_t2_a_family_that_bites_everywhere_refuses_nothing(tmp_path):
    """T2 positive control (R6): both plays respond, nothing is refused and both play. Red today only for the missing keyword."""
    entry, _ = run(tmp_path, ("p1", "p2"), sensitive_plays("p1", "p2"), probe=True)
    assert entry["refused"] == []
    with open(tmp_path / entry["csv"], newline="") as fh:
        assert {r["play"] for r in csv.DictReader(fh)} == {"p1", "p2"}


def test_positive_control_without_the_probe_an_inert_play_is_swept_like_any_other(tmp_path):
    """Green on the lab tip: the probe is the only thing that refuses it (the default is the Architect's, see the module docstring)."""
    entry, _ = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"))
    assert entry["refused"] == []
