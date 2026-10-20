# Rule pins: R-083-03@bbc7c0
# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1, test T11; defects D2, D9); docs/northstar/plans/push_ledger_2026-09-22.md FU-warden-no-stack; ledger FINDING-lab-d2, FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, R1 and T11 (D2, D9): the 30-fight naive mirror pre-check of a mix, and the Warden cap it enforces. Fast half: every fight
is a fake `fight_fn`. The real fights are integration/test_rev3_b_mirror_real.py (OM_LAB_SLOW=1).

R1: "A 30-fight naive mirror per new mix before it enters a batch; a mix that caps is rejected and reported." T11: "A mix with more than
4 Wardens per 16 is refused by the mirror pre-check."

BUILDER CONTRACT (names and call shapes pinned here; everything else in scripts/skilllab/sweep.py is the builder's; the plan puts both
in sweep.py):
  sweep.MIRROR_FIGHTS = 30            the Architect's number, a DRAFT (the count is on the open list for Westley): its definition line
                                      carries `DRAFT-mirror-fights`
  sweep.mirror_precheck(units, *, fights=MIRROR_FIGHTS, fight_fn=None, map_fn=None) -> dict
      `units` is a {type: count} dict, the `units` of a MIXES row (16 units). The verdict has at least the keys
        "mix"     the units given
        "ok"      True when the mix may enter a batch
        "reason"  None when ok, else "warden_cap" (T11) or "capped" (a mix whose mirror fights hit the cap)
        "fights"  how many fights were fought (0 when refused before any fight)
        "caps"    how many of them ended "cap"
      The mirror is NAIVE and a mirror: `fights` fights of the mix against the same mix, 16 v 16, every group a blob with order
      attack_move, no timeline, all groups on one layer; the fights are the pairs (seed, swap) over seeds, all distinct, each fought as
      `fight_fn(setup, seed, swap)` (the call shape of scan.run_jobs, or one `map_fn(jobs)` call when map_fn is given).
      More than 4 Wardens per 16 (units["Warden"] * 16 > 4 * sum(units.values())) is refused BEFORE any fight: ok False, reason
      "warden_cap", fights 0, fight_fn never called (the Warden stall is 20 of 20 caps at 16 Wardens; a refusal that fights first would
      be a cap detection, not the cap).
  sweep.vet_mixes(rows, *, fight_fn=None, map_fn=None) -> {"accepted": [row names], "rejected": [{"mix": name, "reason": ..., "caps": n, ...}]}
      runs mirror_precheck on the units of each ENABLED row of `rows` (a list of MIXES rows) and sorts the names; it changes no row (the
      table's `enabled` flag is edited by a person after the report: the writer's reading of "rejected and reported").
  The source of sweep.py names the retirement: a line near the Warden cap carries `FU-warden-no-stack` (traceability, plan note
  2026-10-20: the cap is interim and retires with that engine piece under a TD row).

THE KNOWN CAP (Architect ruling 2026-10-20, implementation; plan R1; Westley may veto): one capped fight rejects a mix, EXCEPT a cap
whose cause is a recorded finding with a queued fix. M9 (12 Vanguard + 4 Warden) caps once in 30 (seed 6, unswapped, 12000 ticks): the
Warden stall of FINDING-lab-d9, fix FU-warden-no-stack. For such a mix mirror_precheck returns ok True, reason "known_cap:FINDING-lab-d9"
and the cap list; M9 stays enabled and vet_mixes shows it accepted. The Warden pattern (Architect definition): a capped fight is the known
Warden cap when, at the cap, every living unit on each side that still has a living unit is a Warden. Any other capped fight on M9, and any
cap on M5 to M8 (or on a mix with no Warden), rejects the mix with reason "capped". The exception retires with the engine piece (a TD row
removes it).
  RATIFIED SHAPE (Architect, 2026-10-20): FightResult gains a defaulted field `living`, a tuple of two dicts ({unit name: count} for side 0,
  then side 1), the units alive at the end of the fight, filled by fight.py at the end of every fight (test_rev3_b_living.py); the verdict
  gains `rosters` = {capped fight index: living} for every capped fight (the living roster printed so the pattern is checkable). A capped
  result without `living` is off the pattern and rejects. The fight index is the call order of the 30 fights, and fight i is seed i // 2
  with swap i % 2 == 1 (DRAFT: fight 12 is seed 6 unswapped). The tests below set `living` on a fake result as an attribute (a
  FightResult-like object); the B builder owns the contract.py and fight.py edit (one field, one fill site).

NOT PINNED (listed in the report): the cap number; where the batch calls vet_mixes (the plan names no hook); what the artifact prints for
M9's caps (report.py is outside B's file list and the plan gives no shape); a mix with Wardens other than M9 (the pattern is pinned for
M9's units only); how many Warden-pattern caps in one mix are still "known" (M9's is one in 30)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import sweep  # noqa: E402
from scripts.skilllab.contract import FightResult  # noqa: E402

SRC = (ROOT / "scripts" / "skilllab" / "sweep.py").read_text()
M3 = {"Vanguard": 8, "Bombard": 8}
M9 = {"Vanguard": 12, "Warden": 4}
KNOWN = "known_cap:FINDING-lab-d9"
WARDENS_ONLY = ({"Warden": 3}, {"Warden": 2})
NEW_NON_WARDEN = {"M5": {"Raider": 8, "Bombard": 8}, "M6": {"Interceptor": 8, "Bombard": 8}, "M7": {"Raider": 8, "Interceptor": 8},
                  "M8": {"Bombard": 8, "Bastion": 8}}
THREE_PER_16 = {"Vanguard": 14, "Warden": 2}


def result(outcome="side0", ticks=900):
    return FightResult(outcome=outcome, margin=0.0, strength_left=(0.0, 0.0), survivors=(0, 0), heads=(16, 16), ticks=ticks,
                       first_contact_tick=-1, firing=[], firing_unit_seconds=(0.0, 0.0))


class Recorder:
    """A fake fight_fn: records every call, answers `outcome_of(index)`; `living_of(index)`, when given, is set as the result's `living`
    (the ratified field: the units alive at the last tick, ({side 0 name: count}, {side 1 name: count}))."""
    def __init__(self, outcome_of=lambda i: "side0", living_of=None):
        self.calls, self.outcome_of, self.living_of = [], outcome_of, living_of

    def __call__(self, setup, seed, swap):
        self.calls.append((setup, seed, swap))
        i = len(self.calls) - 1
        r = result(self.outcome_of(i))
        if self.living_of is not None:
            r.living = self.living_of(i)
        return r


def one_cap(index=12, living=None):
    """One capped fight of the 30 (fight `index`), every other fight quiet; `living` is that fight's living roster (None: not given)."""
    return Recorder(lambda i: "cap" if i == index else "side0", None if living is None else (lambda i: living))


def never(setup, seed, swap):
    raise AssertionError("a fight was fought")


def base_of(setup, g):
    entry = setup.unit_types.get(g.unit)
    return entry.get("base", g.unit) if entry else g.unit


def roster(setup, side):
    out = {}
    for g in setup.groups:
        if g.side == side:
            out[base_of(setup, g)] = out.get(base_of(setup, g), 0) + g.count
    return out


# ---- the fake and the checks it supports (controls, green on the lab tip) ------------------------------------------------------------

def test_control_the_recorder_records_and_answers():
    r = Recorder(lambda i: "cap" if i == 1 else "side0")
    assert r(None, 0, False).outcome == "side0" and r(None, 1, True).outcome == "cap" and len(r.calls) == 2


def test_control_a_fight_that_must_not_happen_raises():
    with pytest.raises(AssertionError):
        never(None, 0, False)


# ---- T11: the Warden cap ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("units", [{"Vanguard": 11, "Warden": 5}, {"Vanguard": 8, "Warden": 8}, {"Raider": 8, "Warden": 8}, {"Warden": 16}],
                         ids=lambda u: "+".join("%s%d" % (k[0], v) for k, v in u.items()))
def test_t11_a_mix_with_more_than_4_wardens_per_16_is_refused_before_any_fight(units):
    """T11 (D9). This is an INTERIM LAB CAP, 4 Wardens per 16, and it retires with the engine piece FU-warden-no-stack (R-083-03 rewritten
    2026-10-20: Wardens do not stack; the stall measured by the lab, 20 of 20 caps at 16 Wardens and 8 of 8 for two built-in sides of 8,
    is the evidence row of that piece); the ruler writes the TD row that deletes this test when the piece lands. Red today: no pre-check."""
    verdict = sweep.mirror_precheck(units, fight_fn=never)
    assert verdict["ok"] is False and verdict["reason"] == "warden_cap", verdict
    assert verdict["fights"] == 0


@pytest.mark.parametrize("units", [M9, THREE_PER_16, M3], ids=["M9-V12-W4", "V14-W2", "M3-no-warden"])
def test_t11_control_a_mix_at_or_under_the_cap_is_not_refused_for_wardens(units):
    """Positive control for T11: 4 Wardens per 16 (the M9 shape), 2, and none are not refused; a quiet fake gives ok."""
    rec = Recorder()
    verdict = sweep.mirror_precheck(units, fight_fn=rec)
    assert verdict["ok"] is True and verdict["reason"] is None and verdict["caps"] == 0, verdict
    assert len(rec.calls) == verdict["fights"] == sweep.MIRROR_FIGHTS


def test_t11_the_default_path_refuses_wardens_without_the_engine(monkeypatch):
    """No fight_fn given: the refusal still happens before anything is fought (the default fight function is replaced by one that raises)."""
    from scripts.skilllab import fight as fight_module
    monkeypatch.setattr(fight_module, "fight", never)
    verdict = sweep.mirror_precheck({"Vanguard": 8, "Warden": 8})
    assert verdict["ok"] is False and verdict["reason"] == "warden_cap" and verdict["fights"] == 0


# ---- R1: the 30 fights --------------------------------------------------------------------------------------------------------------

def test_r1_the_count_is_30_and_is_marked_draft():
    assert sweep.MIRROR_FIGHTS == 30
    lines = [ln for ln in SRC.splitlines() if re.match(r"^MIRROR_FIGHTS\s*=", ln)]
    assert len(lines) == 1 and re.search(r"DRAFT-mirror-fights(?![\w-])", lines[0]), lines


def test_r1_a_mix_is_fought_30_times_in_30_distinct_seed_and_swap_pairs():
    rec = Recorder()
    verdict = sweep.mirror_precheck(M3, fight_fn=rec)
    assert len(rec.calls) == 30 and verdict["fights"] == 30
    assert len({(seed, swap) for _setup, seed, swap in rec.calls}) == 30


def test_r1_the_count_is_a_keyword():
    rec = Recorder()
    assert sweep.mirror_precheck(M3, fights=5, fight_fn=rec)["fights"] == 5 and len(rec.calls) == 5


def test_r1_every_fight_is_a_naive_mirror_of_the_mix_16_v_16():
    """Both sides field exactly `units`, 16 each; every group is a blob attack-moving, on one layer, no timeline (naive)."""
    rec = Recorder()
    sweep.mirror_precheck(M9, fight_fn=rec)
    assert rec.calls
    for setup, _seed, _swap in rec.calls:
        assert roster(setup, 0) == M9 and roster(setup, 1) == M9, (roster(setup, 0), roster(setup, 1))
        assert {g.formation for g in setup.groups} == {"blob"} and {g.order for g in setup.groups} == {"attack_move"}
        assert len({g.layer for g in setup.groups}) == 1
        assert tuple(setup.timeline) == ()


def test_r1_the_wardens_of_the_mirror_are_built_in_wardens_not_copies():
    """D3 (piece A) in B's pre-check: the Warden aura and the Bastion cap are keyed on the built-in ids, so the mirror must not copy them
    into custom types (a copy that renames the Warden would make the mirror answer about a type that has no aura)."""
    rec = Recorder()
    sweep.mirror_precheck(M9, fight_fn=rec)
    setup = rec.calls[0][0]
    names = {g.unit for g in setup.groups}
    assert "Warden" in names
    entry = setup.unit_types.get("Warden")
    assert entry is None or (entry.get("base") == "Warden" and not entry.get("scale") and not entry.get("set"))


def test_r1_a_mix_whose_every_fight_caps_is_rejected_as_capped():
    verdict = sweep.mirror_precheck(M3, fight_fn=Recorder(lambda i: "cap"))
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 30 and verdict["fights"] == 30, verdict


def test_r1_a_mix_with_no_capped_fight_is_accepted_whoever_wins():
    verdict = sweep.mirror_precheck(M3, fight_fn=Recorder(lambda i: ("side0", "side1", "draw")[i % 3]))
    assert verdict["ok"] is True and verdict["caps"] == 0, verdict


def test_r1_the_map_fn_path_is_one_call_for_all_the_jobs():
    calls = []

    def map_fn(jobs):
        calls.append(list(jobs))
        return [result() for _ in jobs]

    verdict = sweep.mirror_precheck(M3, map_fn=map_fn)
    assert len(calls) == 1 and len(calls[0]) == 30 and verdict["ok"] is True


# ---- the seed scheme (DRAFT) -------------------------------------------------------------------------------------------------------

def test_r1_fight_i_is_seed_i_div_2_and_swapped_when_i_is_odd():
    """DRAFT scheme, so that "seed 6, unswapped" (M9's cap, FINDING-lab-d9) is reproducible: fight i uses seed i // 2 and swap i % 2 == 1,
    so fight 12 is seed 6 unswapped. The 30 pairs are exactly that set, and the fights come in index order. Red today: no pre-check."""
    rec = Recorder()
    sweep.mirror_precheck(M3, fight_fn=rec)
    got = [(seed, swap) for _setup, seed, swap in rec.calls]
    assert set(got) == {(i // 2, i % 2 == 1) for i in range(30)}, got
    assert got == [(i // 2, i % 2 == 1) for i in range(30)], got
    assert got[12] == (6, False)


# ---- one capped fight rejects a mix (ruling 2026-10-20) -----------------------------------------------------------------------------

@pytest.mark.parametrize("index", [0, 12, 29])
@pytest.mark.parametrize("name", sorted(NEW_NON_WARDEN) + ["M3"])
def test_r1_exactly_one_capped_fight_of_30_rejects_a_mix_without_wardens(name, index):
    """R1 ("a mix that caps is rejected and reported"), at one cap in 30, wherever it falls: M5 to M8 (and M3). Red today: no pre-check."""
    verdict = sweep.mirror_precheck({**NEW_NON_WARDEN, "M3": M3}[name], fight_fn=one_cap(index))
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 1 and verdict["fights"] == 30, verdict


@pytest.mark.parametrize("living", [WARDENS_ONLY, ({"Raider": 2, "Bombard": 1}, {"Raider": 1}), None], ids=["wardens-only", "ordinary", "none-given"])
@pytest.mark.parametrize("name", sorted(NEW_NON_WARDEN))
def test_r1_a_cap_on_m5_to_m8_rejects_whatever_the_living_roster(name, living):
    """The Warden pattern is M9's exception only: an all-Warden roster at a cap of a mix that fields no Wardens is not a known cap (it
    cannot happen; the pre-check does not reason about it). Red today: no pre-check."""
    verdict = sweep.mirror_precheck(NEW_NON_WARDEN[name], fight_fn=one_cap(12, living))
    assert verdict["ok"] is False and verdict["reason"] == "capped", verdict


# ---- the known cap: M9, FINDING-lab-d9 (FU-warden-no-stack) ---------------------------------------------------------------------------

@pytest.mark.parametrize("living", [WARDENS_ONLY, ({"Warden": 1}, {}), ({}, {"Warden": 4})],
                         ids=["wardens-both-sides", "side-1-all-dead", "side-0-all-dead"])
@pytest.mark.parametrize("index", [12, 3])
def test_t1_m9_with_a_cap_at_the_warden_pattern_is_ok_with_the_known_cap_reason(index, living):
    """R1 exception (a) (T1 goes green with M9 enabled): the capped fight's living roster is only Wardens on each side that has a living
    unit -> ok True, reason "known_cap:FINDING-lab-d9", the cap counted, the roster in the result. The pattern, not the seed, makes the
    cap known (index 3 as well as 12). Red today: no pre-check."""
    verdict = sweep.mirror_precheck(M9, fight_fn=one_cap(index, living))
    assert verdict["ok"] is True and verdict["reason"] == KNOWN, verdict
    assert verdict["caps"] == 1 and verdict["fights"] == 30, verdict
    assert verdict["rosters"] == {index: living}, verdict


@pytest.mark.parametrize("living", [({"Warden": 2, "Vanguard": 1}, {"Warden": 2}), ({"Warden": 2}, {"Vanguard": 3}),
                                    ({"Vanguard": 4}, {"Vanguard": 2}), ({"Warden": 1, "Bombard": 1}, {})],
                         ids=["vanguard-left-on-side-0", "vanguard-left-on-side-1", "no-wardens-at-all", "one-side-dead-other-mixed"])
def test_t1_m9_with_a_cap_where_a_non_warden_is_alive_is_rejected(living):
    """R1 exception (b): any other capped fight on M9 rejects the mix, reason "capped"; the living roster is printed all the same."""
    verdict = sweep.mirror_precheck(M9, fight_fn=one_cap(12, living))
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 1, verdict
    assert verdict["rosters"] == {12: living}, verdict


def test_t1_m9_with_a_cap_that_gives_no_living_roster_is_rejected():
    """A capped fight whose result carries no `living` cannot be shown to be at the Warden pattern: rejected, not waved through."""
    verdict = sweep.mirror_precheck(M9, fight_fn=one_cap(12, None))
    assert verdict["ok"] is False and verdict["reason"] == "capped", verdict


def test_t1_m9_with_one_known_cap_and_one_other_cap_is_rejected():
    rec = Recorder(lambda i: "cap" if i in (12, 20) else "side0",
                   lambda i: WARDENS_ONLY if i == 12 else ({"Warden": 2, "Vanguard": 2}, {"Warden": 1}))
    verdict = sweep.mirror_precheck(M9, fight_fn=rec)
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 2, verdict


def test_t1_m9_with_no_cap_is_ok_with_no_reason():
    """Control: a clean M9 is plain ok, not a known cap."""
    verdict = sweep.mirror_precheck(M9, fight_fn=Recorder())
    assert verdict["ok"] is True and verdict["reason"] is None and verdict["caps"] == 0, verdict


def test_t1_the_known_cap_exception_names_its_finding_in_the_source():
    """Traceability: the exception names FINDING-lab-d9 where it is made (retires with FU-warden-no-stack under a TD row)."""
    assert KNOWN in SRC, "sweep.py does not hold the reason %r" % KNOWN


# ---- vet_mixes: rejected and reported -----------------------------------------------------------------------------------------------

def rows():
    return [{"name": "MA", "units": dict(M3), "used_in": ("pa",), "enabled": True},
            {"name": "MB", "units": {"Vanguard": 8, "Warden": 8}, "used_in": ("pb",), "enabled": True},
            {"name": "MC", "units": {"Raider": 8, "Bombard": 8}, "used_in": ("pc",), "enabled": True},
            {"name": "MD", "units": {"Vanguard": 8, "Raider": 8}, "used_in": ("pd",), "enabled": False}]


def test_r1_vet_mixes_accepts_rejects_and_reports_by_name_and_reason():
    """MA is quiet, MB has 8 Wardens (warden_cap, no fight), MC caps in every fight (capped), MD is disabled and not looked at."""
    seen = []

    def fight_fn(setup, seed, swap):
        seen.append(roster(setup, 0))
        return result("cap" if roster(setup, 0).get("Raider") else "side0")

    table = rows()
    report = sweep.vet_mixes(table, fight_fn=fight_fn)
    assert report["accepted"] == ["MA"], report
    by_name = {r["mix"]: r for r in report["rejected"]}
    assert set(by_name) == {"MB", "MC"}, report
    assert by_name["MB"]["reason"] == "warden_cap" and by_name["MC"]["reason"] == "capped" and by_name["MC"]["caps"] == 30
    assert {tuple(sorted(r)) for r in seen} == {tuple(sorted(M3)), ("Bombard", "Raider")}      # MB and MD never fought
    assert table == rows(), "vet_mixes edited a row"


def test_r1_vet_mixes_of_a_clean_table_rejects_nothing():
    report = sweep.vet_mixes([r for r in rows() if r["name"] == "MA"], fight_fn=Recorder())
    assert report["accepted"] == ["MA"] and report["rejected"] == [], report


def test_t1_vet_mixes_shows_m9_accepted_with_a_known_cap_and_a_clean_m9_accepted():
    """R1 exception (d): M9 stays enabled and vet_mixes lists it accepted, with its Warden-pattern cap or without."""
    m9 = [{"name": "M9", "units": dict(M9), "used_in": ("p9",), "enabled": True}]
    capped = sweep.vet_mixes(m9, fight_fn=one_cap(12, WARDENS_ONLY))
    assert capped["accepted"] == ["M9"] and capped["rejected"] == [], capped
    clean = sweep.vet_mixes(m9, fight_fn=Recorder())
    assert clean["accepted"] == ["M9"] and clean["rejected"] == [], clean


def test_t1_vet_mixes_still_rejects_m9_for_a_cap_off_the_pattern_and_a_non_warden_row_for_a_warden_pattern_cap():
    table = [{"name": "M9", "units": dict(M9), "used_in": ("p9",), "enabled": True},
             {"name": "M5", "units": {"Raider": 8, "Bombard": 8}, "used_in": ("p5",), "enabled": True}]
    seen = []

    def fight_fn(setup, seed, swap):
        seen.append(1)
        r = result("cap" if len(seen) in (13, 43) else "side0")        # fight 12 of each mix
        r.living = WARDENS_ONLY if len(seen) == 13 else ({"Raider": 1}, {})
        return r

    report = sweep.vet_mixes(table, fight_fn=fight_fn)
    assert report["accepted"] == ["M9"] and [r["mix"] for r in report["rejected"]] == ["M5"], report
    assert report["rejected"][0]["reason"] == "capped" and report["rejected"][0]["caps"] == 1


# ---- traceability -------------------------------------------------------------------------------------------------------------------

def test_t11_the_cap_names_the_engine_piece_that_retires_it():
    """Traceability (CLAUDE.md: when B exists because A fails, say so at both sites): sweep.py says the Warden cap is interim and retires
    with FU-warden-no-stack; the other site is the ledger row FU-warden-no-stack, which already names the lab cap."""
    assert "FU-warden-no-stack" in SRC, "sweep.py does not name FU-warden-no-stack"
