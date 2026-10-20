# Rule pins: R-164-01@511d57
# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1 with piece C's verdict; test T11); ledger FINDING-lab-d9, FINDING-lab-d7 (Architect ruling 2026-10-20, implementation; Westley may veto)
"""LAB-REV3-C-MIRROR, R1 (the naive mirror pre-check) made verdict-aware. Fast half: every fight is a fake `fight_fn`
(helpers and fixtures reused from test_rev3_b_mirror.py).

RULING (Architect 2026-10-20, implementation; Westley may veto): a mirror is a like-for-like fight. A mirror fight whose result carries
verdict "decided_one_way_reach" (one side can reach the other and not the reverse, R-164-01) cannot be like for like, so the mix is rejected.

BUILDER CONTRACT (sweep.mirror_precheck; everything else in sweep.py is the builder's):
  - a result with `getattr(r, "verdict", None) == "decided_one_way_reach"` rejects the mix: ok False, reason "decided", fights 30. It is
    rejected whether or not it reached the cap. The M9 known-cap exception (P1, FINDING-lab-d9) does NOT apply to a decided fight: M9 with
    one decided fight is rejected "decided" even when every other cap is a P1 Warden cap and even when the decided fight's roster is
    Warden-only.
  - a result with verdict "no_reach_stall" rejects the mix: ok False, reason "stall" (DRAFT reading; it cannot happen in a symmetric
    mirror). Its outcome is "no_reach_stall", never "cap", so it is not counted among the caps. Today it is ACCEPTED (ok True: the precheck
    detects a cap only by `outcome == "cap"`, and "no_reach_stall" is not "cap"); it neither crashes nor reads "capped".
  - cap detection today: `r.outcome == "cap"`. A decided fight that reaches the cap ends as the decided side's win (outcome "side0" or
    "side1", FightResult.outcome comment), so it is invisible to that test. The new rule: a decided fight COUNTS in verdict["caps"] and
    verdict["rosters"][fight index] (= its `living`) when result.ticks >= setup.max_ticks (the Setup the fight was given; the mirror's
    Setup keeps the default 12000), else it does not (caps 0, no roster).
  - a result with no `verdict` attribute (an older fake) behaves exactly as before (getattr default None).
  - a plain elimination mirror (verdict None) passes; an ordinary "cap" outcome still rejects "capped" (unchanged).
  - vet_mixes lists a decided-rejected mix under "rejected" with reason "decided" (and its caps); M9 with a P1 known cap stays accepted.
NOT PINNED (needs a ruling): which reason wins when one mix has BOTH a decided fight and an ordinary cap (or a stall): the test of M9 below
pins only that a decided fight beats a P1 known cap; a mix with a decided fight plus a plain "cap" is left to the builder."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import sweep  # noqa: E402
from tests.skilllab.test_rev3_b_mirror import (  # noqa: E402,F401
    M9, MEASURED, NEW_NON_WARDEN, WARDENS_ONLY, KNOWN, Recorder, result, one_cap)

DECIDED = "decided_one_way_reach"
STALL = "no_reach_stall"
CAP = 12000     # the mirror Setup's default max_ticks (contract.Setup.max_ticks)
M5 = NEW_NON_WARDEN["M5"]
ROSTER = ({"Raider": 3, "Bombard": 1}, {"Bombard": 2})


class Decider:
    """A fake fight_fn: fights in `decided` (index -> dict(outcome, ticks, living, verdict, decided_tick)) are decided/stall/etc.; the rest
    are quiet side0 eliminations. `at_cap` fights get ticks == the given Setup's max_ticks (read from the setup the precheck passes)."""
    def __init__(self, decided, at_cap=()):
        self.decided, self.at_cap, self.n = dict(decided), set(at_cap), 0
        self.cap_seen = None

    def __call__(self, setup, seed, swap):
        i, self.n = self.n, self.n + 1
        self.cap_seen = setup.max_ticks
        if i not in self.decided:
            return result("side0")
        spec = self.decided[i]
        r = result(spec.get("outcome", "side0"), ticks=setup.max_ticks if i in self.at_cap else spec.get("ticks", 400))
        r.verdict, r.decided_tick = spec.get("verdict", DECIDED), spec.get("decided_tick", 1)
        if "living" in spec:
            r.living = spec["living"]
        return r


def decided_fight(**kw):
    return {"verdict": DECIDED, "decided_tick": 1, "outcome": "side0", "ticks": 400, **kw}


# ---- controls (green on the base) --------------------------------------------------------------------------------------------------

def test_control_the_decider_fake_sets_verdict_and_cap_ticks():
    d = Decider({0: decided_fight(), 1: decided_fight()}, at_cap={1})
    setup = sweep._mirror_setup(M5)
    first, second, third = d(setup, 0, False), d(setup, 0, True), d(setup, 1, False)
    assert (first.verdict, first.ticks, second.verdict, second.ticks, third.verdict) == (DECIDED, 400, DECIDED, CAP, None)


def test_control_the_mirror_setup_cap_is_the_contract_default_12000():
    """The cap the precheck's fights are given: the default Setup.max_ticks (the mirror Setup sets none), 12000."""
    assert sweep._mirror_setup(M5).max_ticks == 12000 == CAP


def test_control_a_plain_elimination_mirror_passes():
    """Positive control (3): no verdict anywhere (verdict None on a real FightResult), nothing capped: ok, no reason."""
    assert result("side0").verdict is None
    verdict = sweep.mirror_precheck(M5, fight_fn=Recorder(lambda i: ("side0", "side1", "draw")[i % 3]))
    assert verdict["ok"] is True and verdict["reason"] is None and verdict["caps"] == 0 and verdict["rosters"] == {}, verdict


def test_control_an_ordinary_cap_still_rejects_capped():
    verdict = sweep.mirror_precheck(M5, fight_fn=one_cap(12))
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 1, verdict


def test_control_5_a_result_without_a_verdict_attribute_behaves_as_before():
    """(5) An older fake: a bare object with outcome, ticks, living and NO `verdict`/`decided_tick` attributes (getattr default)."""
    class Old:
        def __init__(self, outcome):
            self.outcome, self.ticks, self.living = outcome, 400, ({}, {})
    assert not hasattr(Old("side0"), "verdict")
    clean = sweep.mirror_precheck(M5, fight_fn=lambda setup, seed, swap: Old("side0"))
    assert clean["ok"] is True and clean["reason"] is None and clean["caps"] == 0, clean
    capped = sweep.mirror_precheck(M5, fight_fn=lambda setup, seed, swap: Old("cap"))
    assert capped["ok"] is False and capped["reason"] == "capped" and capped["caps"] == 30, capped


def test_control_5_m9_known_cap_is_unchanged_without_a_verdict():
    """(2, control) The P1 known cap on M9 (fight 12 capped, side 1 all Wardens) is still ok True known_cap; the roster is printed."""
    verdict = sweep.mirror_precheck(M9, fight_fn=one_cap(12, MEASURED))
    assert verdict["ok"] is True and verdict["reason"] == KNOWN and verdict["caps"] == 1 and verdict["rosters"] == {12: MEASURED}, verdict


# ---- (1) a decided mirror fight rejects the mix ------------------------------------------------------------------------------------

@pytest.mark.parametrize("index", [0, 12, 29])
@pytest.mark.parametrize("outcome", ["side0", "side1"])
def test_decided_not_at_the_cap_rejects_decided_and_is_not_a_cap(index, outcome):
    """(1a) A decided fight (verdict decided_one_way_reach, decided_tick 1, ticks 400, no cap) in an M5 style mix: ok False, reason
    "decided", all 30 fights fought; it did not reach the cap, so caps 0 and no roster. Red today: accepted (ok True)."""
    d = Decider({index: decided_fight(outcome=outcome)})
    verdict = sweep.mirror_precheck(M5, fight_fn=d)
    assert verdict["ok"] is False and verdict["reason"] == "decided", verdict
    assert verdict["caps"] == 0 and verdict["rosters"] == {} and verdict["fights"] == 30, verdict


def test_decided_one_tick_under_the_cap_is_not_a_cap():
    """(1a, boundary) ticks == max_ticks - 1 has not reached the cap: caps 0 (still rejected "decided")."""
    verdict = sweep.mirror_precheck(M5, fight_fn=Decider({5: decided_fight(ticks=CAP - 1, living=ROSTER)}))
    assert verdict["ok"] is False and verdict["reason"] == "decided" and verdict["caps"] == 0 and verdict["rosters"] == {}, verdict


@pytest.mark.parametrize("index", [0, 12, 29])
def test_decided_at_the_cap_rejects_decided_and_counts_as_a_cap_with_its_roster(index):
    """(1b) A decided fight that reached the cap ends as the decided side's win (outcome side0), so it is not outcome "cap": rejected
    "decided" all the same, caps 1, rosters {index: living}. Red today: accepted, caps 0."""
    d = Decider({index: decided_fight(living=ROSTER)}, at_cap={index})
    verdict = sweep.mirror_precheck(M5, fight_fn=d)
    assert d.cap_seen == CAP
    assert verdict["ok"] is False and verdict["reason"] == "decided", verdict
    assert verdict["caps"] == 1 and verdict["fights"] == 30 and verdict["rosters"] == {index: ROSTER}, verdict


def test_two_decided_fights_at_the_cap_count_two():
    d = Decider({4: decided_fight(living=ROSTER), 19: decided_fight(outcome="side1", living=WARDENS_ONLY)}, at_cap={4, 19})
    verdict = sweep.mirror_precheck(M5, fight_fn=d)
    assert verdict["ok"] is False and verdict["reason"] == "decided" and verdict["caps"] == 2, verdict
    assert verdict["rosters"] == {4: ROSTER, 19: WARDENS_ONLY}, verdict


def test_a_decided_fight_at_the_cap_without_a_roster_still_counts_and_rejects():
    """No `living` on the result: still "decided", still a cap (caps 1); the roster entry is whatever the builder's getattr gives."""
    verdict = sweep.mirror_precheck(M5, fight_fn=Decider({7: decided_fight()}, at_cap={7}))
    assert verdict["ok"] is False and verdict["reason"] == "decided" and verdict["caps"] == 1, verdict
    assert list(verdict["rosters"]) == [7], verdict


# ---- (2) M9: the known-cap exception does not apply to a decided fight ----------------------------------------------------------------

def test_m9_with_one_decided_fight_at_the_cap_with_a_warden_only_roster_rejects_decided():
    """(2) The roster matches P1 (side 1 all Wardens) and the fight reached the cap, but its verdict is decided: no exception. Red today: ok."""
    d = Decider({12: decided_fight(living=MEASURED)}, at_cap={12})
    verdict = sweep.mirror_precheck(M9, fight_fn=d)
    assert verdict["ok"] is False and verdict["reason"] == "decided", verdict
    assert verdict["caps"] == 1 and verdict["rosters"] == {12: MEASURED}, verdict


def test_m9_with_a_decided_fight_not_at_the_cap_rejects_decided():
    verdict = sweep.mirror_precheck(M9, fight_fn=Decider({12: decided_fight(living=MEASURED)}))
    assert verdict["ok"] is False and verdict["reason"] == "decided" and verdict["caps"] == 0, verdict


def test_m9_decided_fight_beats_a_p1_known_cap_elsewhere_in_the_same_mix():
    """A P1 known cap (fight 3, an ordinary "cap") plus a decided fight (fight 12): the decided fight rejects the whole mix, "decided"."""
    class Both(Decider):
        def __call__(self, setup, seed, swap):
            i = self.n
            r = super().__call__(setup, seed, swap)
            if i == 3:
                r = result("cap")
                r.living = MEASURED
            return r
    verdict = sweep.mirror_precheck(M9, fight_fn=Both({12: decided_fight(living=MEASURED)}, at_cap={12}))
    assert verdict["ok"] is False and verdict["reason"] == "decided", verdict


# ---- stall: DRAFT reading ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("index", [0, 12])
def test_a_no_reach_stall_fight_rejects_stall_and_is_not_a_cap(index):
    """DRAFT reading: a result with verdict no_reach_stall (outcome "no_reach_stall", ticks 1) rejects the mix, reason "stall"; it is
    neither cap nor win, so caps 0. Today the precheck ACCEPTS it (outcome != "cap"): red today."""
    d = Decider({index: {"verdict": STALL, "outcome": STALL, "ticks": 1}})
    verdict = sweep.mirror_precheck(M5, fight_fn=d)
    assert verdict["ok"] is False and verdict["reason"] == "stall", verdict
    assert verdict["caps"] == 0 and verdict["fights"] == 30, verdict


# ---- (4) vet_mixes ----------------------------------------------------------------------------------------------------------------------

def test_vet_mixes_lists_a_decided_rejected_mix_with_reason_decided_and_keeps_m9_known_cap_accepted():
    table = [{"name": "M9", "units": dict(M9), "used_in": ("p9",), "enabled": True},
             {"name": "M5", "units": dict(M5), "used_in": ("p5",), "enabled": True},
             {"name": "M6", "units": dict(NEW_NON_WARDEN["M6"]), "used_in": ("p6",), "enabled": True}]
    seen = []

    def fight_fn(setup, seed, swap):
        seen.append(1)
        n = len(seen)                                   # fights 1..30 are M9's, 31..60 M5's, 61..90 M6's
        if n == 13:                                     # M9 fight 12: the P1 known cap
            r = result("cap")
            r.living = MEASURED
            return r
        if n == 30 + 5:                                 # M5 fight 4: decided, at the cap
            r = result("side0", ticks=setup.max_ticks)
            r.verdict, r.decided_tick, r.living = DECIDED, 1, ROSTER
            return r
        return result("side0")

    report = sweep.vet_mixes(table, fight_fn=fight_fn)
    assert report["accepted"] == ["M9", "M6"], report
    assert [r["mix"] for r in report["rejected"]] == ["M5"], report
    rej = report["rejected"][0]
    assert rej["reason"] == "decided" and rej["caps"] == 1 and rej["rosters"] == {4: ROSTER}, rej
    assert report["verdicts"]["M9"]["reason"] == KNOWN and report["verdicts"]["M5"]["reason"] == "decided", report["verdicts"]
