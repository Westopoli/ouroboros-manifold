# spec: PX-13 prototype experiment (Factory section, docs/northstar/PLAN.md)
"""Tests for scripts/specfactory/fixture_defects.py.

Two layers, same pattern test_tick_closure.py and test_card_lint.py already
use: synthetic fixtures for the mechanism (this suite never depends on the
real repo's test bodies changing shape under it), plus a second layer that
runs the same three checks against the actual, frozen incident/counterpart
files named in docs/northstar/research/harness_defects_2026-09-17/
DECISIONS.md (R7h, R7l, R7e) -- those are already-committed history, not
live targets another agent is editing, so pinning to their real paths is
safe and is what the PX-13 brief's "Experiments" section asks for directly.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import fixture_defects as fd  # noqa: E402

R7E_COMMIT = "d3273fa"
R7E_FILE = "tests/csim/test_E05_S036_declared_or_sprung.py"
R7E_NODE = "test_R_036_05_with_probability_min_1_defend"

# R7h control (tests/csim/controls/test_control_e05_agent_reads_live.py) went
# live-fixed in 2a6fb4f -- the unsatisfiable 3d-reads-after-3f pattern this
# check detects no longer exists in that file. R7H_COMMIT pins the pre-fix
# blob so the positive control still has something real to bite.
R7H_COMMIT = "66f4128"
R7H_FILE = "tests/csim/controls/test_control_e05_agent_reads_live.py"


def _git_show(rev: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout


# ======================================================================
# check 1: tick_order_reachability -- synthetic
# ======================================================================

SYNTH_HEADER = '''
from conftest import (
    OMAction, OMArchetype, OMEdge, OMMode, OMStance, OMTier,
    force_draws, inject_intent, isolate_agents, read_attacks,
    read_candidates, read_decisions, set_edge, set_faction, set_owner,
    set_region, set_stance,
)
'''


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(SYNTH_HEADER + body)
    return p


SAME_TICK_EARLY_READER = '''
def test_control_synthetic_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=3)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, 100)
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_faction(dbg, w, 2, OMArchetype.CONQUEROR, budget=0.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    set_region(dbg, w, 2, tier=OMTier.HOME, military=50.0, faction_id=2)
    set_owner(dbg, w, 2, 2, held_since=-1)
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0, commit=90.0)
    dbg.om_world_step(w)
    cands = read_candidates(dbg, w, 2)
    assert cands[0].weakness != pytest.approx(0.70, abs=1e-6)
'''

SAME_STEP_READER_OK = '''
def test_control_synthetic_reads_at_the_mutation_step(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, 100)
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0, commit=90.0)
    dbg.om_world_step(w)
    attacks = read_attacks(dbg, w)
    assert len(attacks) == 1
'''

NEXT_TICK_READER_OK = '''
def test_control_synthetic_reads_a_tick_later(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, 100)
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0, commit=90.0)
    dbg.om_world_step(w)
    dbg.om_world_step(w)
    cands = read_candidates(dbg, w, 1)
'''

TELEGRAPH_MODE_OK = '''
def test_control_synthetic_telegraph_does_not_arm(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=50.0, faction_id=0)
    set_owner(dbg, w, 0, 0, held_since=-1)
    set_region(dbg, w, 1, tier=OMTier.HOME, military=30.0, faction_id=1)
    set_owner(dbg, w, 1, 1, held_since=-1)
    inject_intent(dbg, w, 0, OMAction.ATTACK, target_idx=1, source_idx=0, commit=90.0, mode=OMMode.TELEGRAPH)
    dbg.om_world_step(w)
    cands = read_candidates(dbg, w, 1)
'''


def test_tick_order_reachability_flags_same_tick_earlier_step_read(tmp_path):
    p = _write(tmp_path, "test_control_synth1.py", SAME_TICK_EARLY_READER)
    result = fd.tick_order_reachability(p)
    assert result["flag"] == "UNSATISFIABLE_BY_ORDER"
    f = result["findings"][0]
    assert f["reader"] == "read_candidates"
    assert f["reader_step"] == "3d"
    assert f["mutator_step"] == "3f"


def test_tick_order_reachability_silent_when_reader_matches_mutation_step(tmp_path):
    p = _write(tmp_path, "test_control_synth2.py", SAME_STEP_READER_OK)
    assert fd.tick_order_reachability(p) == {"flag": None, "findings": []}


def test_tick_order_reachability_silent_across_a_tick_boundary(tmp_path):
    p = _write(tmp_path, "test_control_synth3.py", NEXT_TICK_READER_OK)
    assert fd.tick_order_reachability(p) == {"flag": None, "findings": []}


def test_tick_order_reachability_silent_for_telegraph_mode(tmp_path):
    p = _write(tmp_path, "test_control_synth4.py", TELEGRAPH_MODE_OK)
    assert fd.tick_order_reachability(p) == {"flag": None, "findings": []}


# ---- check 1 against the real R7h incident and a real clean counterpart --

def test_tick_order_reachability_flags_the_real_r7h_control(tmp_path):
    frozen = _git_show(R7H_COMMIT, R7H_FILE)
    p = tmp_path / "frozen_r7h.py"
    p.write_text(frozen)
    result = fd.tick_order_reachability(p)
    assert result["flag"] == "UNSATISFIABLE_BY_ORDER"
    f = result["findings"][0]
    assert f["reader"] == "read_candidates"
    assert f["reader_step"] == "3d"
    assert f["mutator_step"] == "3f"


def test_tick_order_reachability_silent_on_the_live_r7h_control_after_its_fix():
    # Fixed live in 2a6fb4f: the unsatisfiable pattern is gone, so the tool
    # correctly finds nothing against the current file.
    result = fd.tick_order_reachability(REPO / R7H_FILE)
    assert result == {"flag": None, "findings": []}


def test_tick_order_reachability_silent_on_real_conquest_on_band_control():
    result = fd.tick_order_reachability(REPO / "tests/csim/controls/test_control_e05_conquest_on_band.py")
    assert result == {"flag": None, "findings": []}


def test_tick_order_reachability_silent_on_real_s034_story_test():
    result = fd.tick_order_reachability(REPO / "tests/csim/test_E05_S034_who_looks_worth_taking.py")
    assert result == {"flag": None, "findings": []}


def test_tick_order_reachability_silent_on_the_fixed_r7e_test(tmp_path):
    fixed = _git_show(R7E_COMMIT, R7E_FILE)
    p = tmp_path / "fixed_r7e.py"
    p.write_text(fixed)
    result = fd.tick_order_reachability(p)
    assert result == {"flag": None, "findings": []}


# ======================================================================
# check 2: branch_coverage_of_control -- synthetic
# ======================================================================

def _garrison_control_text(military: float, damage: float, garrison: float) -> str:
    military_to = military + damage
    return f'''
"""Positive control for OM_BUG_GARRISON_BEFORE_DAMAGE.

Synthetic: a telegraphed breakthrough drops defender military from
{military} to {military_to} (net {military}, delta military {damage}) and
conquers the region with garrison {garrison}.
"""
from conftest import OMBugE05, force_draws, isolate_agents, read_attacks, set_faction, set_region


def test_control_synthetic_garrison_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    isolate_agents(dbg, w)
    dbg.om_debug_inject(w, OMBugE05.GARRISON_BEFORE_DAMAGE)
    set_region(dbg, w, 1, tier=0, military={military}, faction_id=1)
    force_draws(dbg, w, [1.0, 0.8])
    dbg.om_world_step(w)
    attacks = read_attacks(dbg, w)
    att = attacks[0]
    assert att.garrison == pytest.approx({garrison}, abs=1e-6)
    assert dbg.om_region_field(w, 1, 0) != pytest.approx({military_to + garrison}, abs=1e-6)
'''


def test_branch_coverage_flags_vacuous_control(tmp_path):
    # Same shape as the real R7l incident: m=20, d=-16 (never clamps), g=27.3.
    text = _garrison_control_text(military=20.0, damage=-16.0, garrison=27.3)
    p = tmp_path / "test_control_synth_garrison_vacuous.py"
    p.write_text(text)
    result = fd.branch_coverage_of_control(p)
    assert result["flag"] == "VACUOUS_CONTROL"
    assert result["correct"] == pytest.approx(31.3, abs=1e-6)
    assert result["buggy"] == pytest.approx(31.3, abs=1e-6)
    assert result["suggested_military"] is not None
    # The suggested value must actually distinguish the two formulas.
    sm = result["suggested_military"]
    correct = fd._eval_formula("max(0, m + d) + g", sm, -16.0, 27.3)
    buggy = fd._eval_formula("max(0, m + g + d)", sm, -16.0, 27.3)
    assert correct != pytest.approx(buggy, abs=1e-6)


def test_branch_coverage_silent_when_numbers_distinguish(tmp_path):
    # military=5, damage=-16 -> m + d = -11 (clamps to 0 in the correct
    # order); m + g + d = 5 + 27.3 - 16 = 16.3 (does not clamp) -- distinct.
    text = _garrison_control_text(military=5.0, damage=-16.0, garrison=27.3)
    p = tmp_path / "test_control_synth_garrison_distinguishing.py"
    p.write_text(text)
    result = fd.branch_coverage_of_control(p)
    assert result["flag"] is None
    assert result["correct"] != pytest.approx(result["buggy"], abs=1e-6)


def test_branch_coverage_silent_on_unknown_bug_id(tmp_path):
    text = '''
from conftest import OMBugE05
def test_control_synthetic_other_bug(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=2)
    dbg.om_debug_inject(w, OMBugE05.COLLISION_MAX_STRENGTH)
'''
    p = tmp_path / "test_control_synth_other.py"
    p.write_text(text)
    result = fd.branch_coverage_of_control(p)
    assert result["flag"] is None
    assert "reason" in result


# ---- check 2 against the real R7l incident and a real clean counterpart --

def test_branch_coverage_flags_the_real_r7l_control():
    result = fd.branch_coverage_of_control(
        REPO / "tests/csim/controls/test_control_e05_garrison_before_damage.py"
    )
    assert result["flag"] == "VACUOUS_CONTROL"
    assert result["m"] == pytest.approx(20.0)
    assert result["d"] == pytest.approx(-16.0)
    assert result["g"] == pytest.approx(27.3)


def test_branch_coverage_silent_on_real_conquest_on_band_control():
    result = fd.branch_coverage_of_control(
        REPO / "tests/csim/controls/test_control_e05_conquest_on_band.py"
    )
    assert result["flag"] is None


# ======================================================================
# check 3: two_agent_confound -- synthetic
# ======================================================================

def _reinforce_confound_text(second_budget: float, filtered: bool) -> str:
    read_expr = (
        "[r for r in read_reinforces(lib, w) if r.target_idx == 1]"
        if filtered else
        "read_reinforces(lib, w)"
    )
    return f'''
from conftest import OMArchetype, force_draws, isolate_agents, read_reinforces, set_faction, set_owner, set_region, set_stance


def test_R_999_99_synthetic_case(lib, world_factory):
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=40.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget={second_budget})
    set_stance(lib, w, 0, 1, 0)
    set_region(lib, w, 0, tier=0, military=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=0, military=10.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    force_draws(lib, w, [0.1, 0.5, 0.5])
    lib.om_world_step(w)
    reinforces = {read_expr}
    assert len(reinforces) == 1
'''


def test_two_agent_confound_flags_unfiltered_high_budget_second_faction(tmp_path):
    p = tmp_path / "test_synth_confound.py"
    p.write_text(_reinforce_confound_text(second_budget=100.0, filtered=False))
    result = fd.two_agent_confound(p, "test_R_999_99_synthetic_case")
    assert result["flag"] == "TWO_AGENT_CONFOUND"
    f = result["findings"][0]
    assert f["acting_faction"] == 1
    assert f["target_faction"] == 0
    assert f["net"] > 0


def test_two_agent_confound_silent_when_filtered(tmp_path):
    p = tmp_path / "test_synth_confound_filtered.py"
    p.write_text(_reinforce_confound_text(second_budget=100.0, filtered=True))
    result = fd.two_agent_confound(p, "test_R_999_99_synthetic_case")
    assert result == {"flag": None, "findings": []}


def test_two_agent_confound_silent_when_second_faction_not_viable(tmp_path):
    p = tmp_path / "test_synth_confound_low_budget.py"
    p.write_text(_reinforce_confound_text(second_budget=50.0, filtered=False))
    result = fd.two_agent_confound(p, "test_R_999_99_synthetic_case")
    assert result == {"flag": None, "findings": []}


def test_two_agent_confound_silent_when_second_faction_is_default(tmp_path):
    text = '''
from conftest import OMArchetype, force_draws, isolate_agents, read_reinforces, set_faction, set_owner, set_region, set_stance


def test_R_999_98_synthetic_default(lib, world_factory):
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=40.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.DEFAULT, budget=1000.0)
    set_stance(lib, w, 0, 1, 0)
    set_region(lib, w, 0, tier=0, military=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=0, military=10.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    force_draws(lib, w, [0.1, 0.5, 0.5])
    lib.om_world_step(w)
    reinforces = read_reinforces(lib, w)
    assert len(reinforces) == 1
'''
    p = tmp_path / "test_synth_confound_default.py"
    p.write_text(text)
    result = fd.two_agent_confound(p, "test_R_999_98_synthetic_default")
    assert result == {"flag": None, "findings": []}


# ---- check 3 against the real R7e incident (pre-fix) and its own fix -----

def test_two_agent_confound_flags_the_real_r7e_defective_test(tmp_path):
    defective = _git_show(f"{R7E_COMMIT}^", R7E_FILE)
    p = tmp_path / "defective_r7e.py"
    p.write_text(defective)
    result = fd.two_agent_confound(p, R7E_NODE)
    assert result["flag"] == "TWO_AGENT_CONFOUND"
    f = result["findings"][0]
    assert f["acting_faction"] == 1
    assert f["archetype"] == "FORTIFIER"
    assert f["target_faction"] == 0
    assert f["net"] > 0


def test_two_agent_confound_silent_on_the_real_r7e_fixed_test(tmp_path):
    fixed = _git_show(R7E_COMMIT, R7E_FILE)
    p = tmp_path / "fixed_r7e.py"
    p.write_text(fixed)
    result = fd.two_agent_confound(p, R7E_NODE)
    assert result == {"flag": None, "findings": []}
