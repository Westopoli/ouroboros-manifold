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

WHAT THE WRITER DID NOT PIN (with Westley, listed in the report): whether ONE capped fight of the 30 rejects the mix or a share of them
does (the plan says "a mix that caps is rejected"; the tests use no capped fight and all of them capped); the cap number; and where the
batch calls vet_mixes (the plan names no hook)."""
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
THREE_PER_16 = {"Vanguard": 14, "Warden": 2}


def result(outcome="side0", ticks=900):
    return FightResult(outcome=outcome, margin=0.0, strength_left=(0.0, 0.0), survivors=(0, 0), heads=(16, 16), ticks=ticks,
                       first_contact_tick=-1, firing=[], firing_unit_seconds=(0.0, 0.0))


class Recorder:
    """A fake fight_fn: records every call, answers `outcome_of(index)`."""
    def __init__(self, outcome_of=lambda i: "side0"):
        self.calls, self.outcome_of = [], outcome_of

    def __call__(self, setup, seed, swap):
        self.calls.append((setup, seed, swap))
        return result(self.outcome_of(len(self.calls) - 1))


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


# ---- traceability -------------------------------------------------------------------------------------------------------------------

def test_t11_the_cap_names_the_engine_piece_that_retires_it():
    """Traceability (CLAUDE.md: when B exists because A fails, say so at both sites): sweep.py says the Warden cap is interim and retires
    with FU-warden-no-stack; the other site is the ledger row FU-warden-no-stack, which already names the lab cap."""
    assert "FU-warden-no-stack" in SRC, "sweep.py does not name FU-warden-no-stack"
