# spec: PF-8 prototype experiment, H1 (tick-stage closure)
"""Tests for scripts/specfactory/tick_closure.py.

Synthetic sim.c/cards, same style as test_card_lint.py -- this module proves
the closure mechanism, not the real ouroboros-manifold repo's own state (the
real-data replay against the actual 204a1/204a2/204a3 recut history is a
separate script, not a pytest suite, per the PF-8 brief).
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import tick_closure  # noqa: E402

SIM_C = '''#include "ouroboros_sim.h"

uint64_t om_world_step(om_world *w) {
    w->tick++;
    om_faction_step_budget(w);     /* 3b */
    om_step_telegraphs(w);         /* 3c */
    om_step_decisions(w);          /* 3d */
    om_step_reinforce(w);          /* 3e */
    om_step_resolve(w);            /* 3f */
    om_step_friction(w);           /* 4 */
    om_step_admin_revolts(w);      /* 4.1 */
    return w->tick;
}
'''

RESOLVE_C = '''#include "ouroboros_sim.h"

void om_step_telegraphs(om_world *w) {
    /* STUB, but a real one resets and writes the attacks buffer */
    w->attacks_n = 0;
    w->attacks[w->attacks_n] = 0;
    w->attacks_n++;
    /* also reads an existing reinforcement for its own defense math --
       a read, not a write, so it must not count as owning reinforces_n */
    if (w->reinforces_n > 0) { int x = w->reinforces[0]; (void)x; }
}

uint32_t om_tick_attacks(const om_world *w, om_attack *out, uint32_t max) {
    uint32_t n = w->attacks_n;
    if (n > max) n = max;
    for (uint32_t i = 0; i < n; i++) out[i] = w->attacks[i];
    return n;
}

void om_step_reinforce(om_world *w) {
    /* STUB, but a real one resets and writes the reinforces buffer */
    w->reinforces_n = 0;
    w->reinforces[w->reinforces_n] = 0;
    w->reinforces_n++;
}

uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max) {
    uint32_t n = w->reinforces_n;
    if (n > max) n = max;
    for (uint32_t i = 0; i < n; i++) out[i] = w->reinforces[i];
    return n;
}

void om_step_resolve(om_world *w) {
    /* STUB, appends into the same attacks buffer as om_step_telegraphs --
       does not reset it, only increments the shared counter */
    w->attacks[w->attacks_n] = 0;
    w->attacks_n++;
    /* reads decisions to find surprise attacks to resolve, never writes it */
    if (w->decisions_n > 0) { int x = w->decisions[0]; (void)x; }
}
'''

AGENT_C = '''#include "ouroboros_sim.h"

void om_step_decisions(om_world *w) {
    w->decisions_n = 0;
    w->decisions[w->decisions_n] = 0;
    w->decisions_n++;
}

uint32_t om_pending_telegraphs(const om_world *w, om_telegraph *out, uint32_t max) {
    uint32_t n = w->telegraphs_n;
    if (n > max) n = max;
    for (uint32_t i = 0; i < n; i++) out[i] = w->telegraphs[i];
    return n;
}

uint32_t om_tick_decisions(const om_world *w, om_decision *out, uint32_t max) {
    uint32_t n = w->decisions_n;
    if (n > max) n = max;
    for (uint32_t i = 0; i < n; i++) out[i] = w->decisions[i];
    return n;
}

uint32_t om_faction_candidates(const om_world *w, int fid, om_candidate *out, uint32_t max) {
    /* a live scoring function, no backing buffer of its own -- reads
       generic per-faction/region state that every hook also touches */
    uint32_t n = max;
    for (uint32_t i = 0; i < n; i++) out[i] = w->regions[fid];
    return n;
}
'''

FRICTION_C = '''#include "ouroboros_sim.h"

void om_step_friction(om_world *w) {
    w->friction_n = 0;
}

void om_step_admin_revolts(om_world *w) {
    w->admin_rolls_n = 0;
}

void om_faction_step_budget(om_world *w) {
    w->faction_budget[0] = 0;
}
'''


CONFTEST = '''
def isolate_agents(lib, w):
    lib.om_world_set_feature(w, 1, 1)


def _read_records(lib, w, name, max_records=8):
    buf = [0] * max_records
    n = getattr(lib, name)(w, buf, max_records)
    return buf[:n]


def read_attacks(lib, w):
    return _read_records(lib, w, "om_tick_attacks")


def read_reinforces(lib, w):
    return _read_records(lib, w, "om_tick_reinforces")


def read_telegraphs(lib, w):
    return _read_records(lib, w, "om_pending_telegraphs")


def read_candidates(lib, w, fid, max_records=8):
    buf = [0] * max_records
    n = lib.om_faction_candidates(w, fid, buf, max_records)
    return buf[:n]


def read_decisions(lib, w):
    return _read_records(lib, w, "om_tick_decisions")
'''

CARD_204A1_TEST = '''
from conftest import isolate_agents, read_reinforces


def test_R_036_03_it_resolves_in_step_3c(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    lib.om_world_step(w)
    reinforces = read_reinforces(lib, w)
    assert len(reinforces) >= 0
'''

CARD_204A2_TEST = '''
from conftest import isolate_agents, read_reinforces


def test_R_036_05_reactive_reinforce(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    lib.om_world_step(w)
    reinforces = read_reinforces(lib, w)
    assert len(reinforces) >= 0
'''

CARD_204A3_TEST = '''
from conftest import isolate_agents, read_attacks


def test_R_037_01_core_attack(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    lib.om_world_step(w)
    attacks = read_attacks(lib, w)
    assert len(attacks) >= 0
'''

CARD_203A1_TEST = '''
from conftest import isolate_agents, read_candidates


def test_R_034_05_it_scored_once(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    lib.om_world_step(w)
    candidates = read_candidates(lib, w, 0)
    assert len(candidates) >= 0
'''

CARD_203E_TEST = '''
from conftest import isolate_agents, read_decisions


def test_R_036_01_telegraph_preference(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    lib.om_world_step(w)
    decisions = read_decisions(lib, w)
    assert len(decisions) >= 0
'''


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text("/* synthetic header */\n")
    (project / "csrc" / "sim.c").write_text(SIM_C)
    (project / "csrc" / "resolve.c").write_text(RESOLVE_C)
    (project / "csrc" / "agent.c").write_text(AGENT_C)
    (project / "csrc" / "friction.c").write_text(FRICTION_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_204a1.py").write_text(CARD_204A1_TEST)
    (project / "tests" / "csim" / "test_204a2.py").write_text(CARD_204A2_TEST)
    (project / "tests" / "csim" / "test_204a3.py").write_text(CARD_204A3_TEST)
    (project / "tests" / "csim" / "test_203a1.py").write_text(CARD_203A1_TEST)
    (project / "tests" / "csim" / "test_203e.py").write_text(CARD_203E_TEST)
    return project


def _write_card(tmp_path: Path, name: str, project: Path, *, test_file: str,
                 test_name: str, snippet_symbol: str) -> Path:
    card = tmp_path / f"{name}.md"
    card.write_text(
        "\n".join([
            "---",
            f"project: {project}",
            "acceptance:",
            f'  - "{sys.executable} -m pytest -q tests/csim/{test_file}::{test_name}"',
            'allowed_files: "csrc/resolve.c"',
            "snippet_file: csrc/resolve.c",
            f'snippet_symbol: "{snippet_symbol}"',
            "expected_lines: 40",
            "---",
            "",
            "## Brief for DeepSeek",
            "Synthetic card, not real.",
            "",
        ])
    )
    return card


def _csrc_texts(project: Path) -> dict:
    return {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}


def test_hooks_in_order_reads_the_orchestrator_body_in_tick_order():
    hooks = tick_closure.hooks_in_order(SIM_C)
    assert hooks == [
        "om_faction_step_budget",
        "om_step_telegraphs",
        "om_step_decisions",
        "om_step_reinforce",
        "om_step_resolve",
        "om_step_friction",
        "om_step_admin_revolts",
    ]


def test_expand_closure_adds_hooks_only_when_orchestrator_present():
    hooks = tick_closure.hooks_in_order(SIM_C)
    assert tick_closure.expand_closure({"om_world_step"}, hooks) == {"om_world_step"} | set(hooks)
    assert tick_closure.expand_closure({"om_faction_candidates"}, hooks) == {"om_faction_candidates"}


def test_204a1_needs_204a2s_reinforce_hook_when_204a2_not_done(tmp_path):
    """R1/R7-interim shape: 204a1's own acceptance reads back a reactive
    reinforce that only om_step_reinforce (204a2's hook) ever populates, but
    card_lint's plain symbol collector never sees om_step_reinforce at all
    -- it is never called by name from Python, only reached as a side
    effect of om_world_step."""
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, "204a1", project, test_file="test_204a1.py",
                        test_name="test_R_036_03_it_resolves_in_step_3c",
                        snippet_symbol="om_step_telegraphs, om_tick_attacks")
    owner_map = {
        "om_step_telegraphs": "204a1", "om_tick_attacks": "204a1",
        "om_step_reinforce": "204a2", "om_tick_reinforces": "204a2",
        "om_step_resolve": "204a3",
    }
    findings = tick_closure.stub_hooks_needed(
        card, project, _csrc_texts(project), done_symbols=set(), owner_map=owner_map,
    )
    hooks_found = {f["hook"] for f in findings}
    assert "om_step_reinforce" in hooks_found
    assert all(f["owner"] == "204a2" for f in findings if f["hook"] == "om_step_reinforce")


def test_204a1_is_clean_once_204a2_is_done(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, "204a1", project, test_file="test_204a1.py",
                        test_name="test_R_036_03_it_resolves_in_step_3c",
                        snippet_symbol="om_step_telegraphs, om_tick_attacks")
    owner_map = {
        "om_step_telegraphs": "204a1", "om_tick_attacks": "204a1",
        "om_step_reinforce": "204a2", "om_tick_reinforces": "204a2",
        "om_step_resolve": "204a3",
    }
    done = {"om_step_reinforce", "om_tick_reinforces"}
    findings = tick_closure.stub_hooks_needed(
        card, project, _csrc_texts(project), done_symbols=done, owner_map=owner_map,
    )
    assert findings == []


def test_204a3_needs_204a1s_telegraph_hook_when_204a1_not_done(tmp_path):
    """R1 shape: 204a3's telegraph-mode tests read back through
    om_tick_attacks (its own reader), but the array is only ever populated
    by om_step_telegraphs (204a1's hook)."""
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, "204a3", project, test_file="test_204a3.py",
                        test_name="test_R_037_01_core_attack",
                        snippet_symbol="om_step_resolve, om_tick_attacks")
    owner_map = {
        "om_step_telegraphs": "204a1",
        "om_step_reinforce": "204a2", "om_tick_reinforces": "204a2",
        "om_step_resolve": "204a3", "om_tick_attacks": "204a3",
    }
    findings = tick_closure.stub_hooks_needed(
        card, project, _csrc_texts(project), done_symbols=set(), owner_map=owner_map,
    )
    hooks_found = {f["hook"] for f in findings}
    assert "om_step_telegraphs" in hooks_found


def test_card_reading_an_unrelated_hook_is_not_flagged(tmp_path):
    """False-positive control: this card also calls om_world_step, so bare
    expand_closure() would put every undone hook (om_step_reinforce,
    om_step_resolve, ...) in its closure -- but it only ever reads back
    through om_faction_candidates, which touches none of those hooks'
    fields, so none of them should be reported. Matches the real 203a1/
    203c/203e shape (candidate-scoring cards that also drive a step)."""
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, "203a1", project, test_file="test_203a1.py",
                        test_name="test_R_034_05_it_scored_once",
                        snippet_symbol="om_faction_candidates")
    owner_map = {
        "om_step_telegraphs": "204a1", "om_tick_attacks": "204a1",
        "om_step_reinforce": "204a2", "om_tick_reinforces": "204a2",
        "om_step_resolve": "204a3",
        "om_faction_candidates": "203a1",
    }
    findings = tick_closure.stub_hooks_needed(
        card, project, _csrc_texts(project), done_symbols=set(), owner_map=owner_map,
    )
    assert findings == []


def test_reader_of_a_field_another_hook_only_reads_is_not_flagged(tmp_path):
    """om_step_resolve reads w->decisions (to find surprise attacks to
    resolve) but never resets or increments decisions_n -- only
    om_step_decisions owns that counter. A card whose test reads
    om_tick_decisions must not be told it needs om_step_resolve just
    because om_step_resolve's body happens to mention w->decisions.
    Matches the real 203e shape exactly (S-036 R-036-01/02)."""
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, "203e", project, test_file="test_203e.py",
                        test_name="test_R_036_01_telegraph_preference",
                        snippet_symbol="om_pending_telegraphs, om_step_decisions")
    owner_map = {
        "om_step_decisions": "203e", "om_pending_telegraphs": "203e",
        "om_step_telegraphs": "204a1", "om_tick_attacks": "204a1",
        "om_step_reinforce": "204a2", "om_tick_reinforces": "204a2",
        "om_step_resolve": "204a3",
    }
    findings = tick_closure.stub_hooks_needed(
        card, project, _csrc_texts(project), done_symbols=set(), owner_map=owner_map,
    )
    assert findings == []


def test_build_owner_map_ignores_snippet_file_unlike_card_lints_own_rule():
    records = [
        {"card_id": "204a1", "snippet_symbol": "om_step_telegraphs, om_tick_attacks"},
        {"card_id": "204a2", "snippet_symbol": "om_step_reinforce, om_tick_reinforces"},
        {"card_id": "204a3", "snippet_symbol": "om_step_resolve"},
    ]
    owner_map = tick_closure.build_owner_map(records)
    assert owner_map["om_step_reinforce"] == "204a2"
    assert owner_map["om_step_telegraphs"] == "204a1"
    assert owner_map["om_step_resolve"] == "204a3"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
