# spec: PX-16 prototype experiment (docs/northstar/proving_ground/PX-16-graph-scheduler-simulation.md)
"""Tests for scripts/specfactory/chain_sim.py.

Two groups, same convention as test_tick_closure.py: the DAG-building tests
use a synthetic project (own csrc/*.c, tests/csim/*.py, own cards) so this
suite never depends on the real ouroboros-manifold repo's own csrc/tests
state; the replay tests use a synthetic 6-card graph with hand-computed
expected numbers for every policy. The real-data DAG/replay against the
real RELEASE_CHAIN and agora/runs/ is `chain_sim.py`'s own CLI, run by hand
for PX-16's numbers, not a pytest suite.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import chain_sim  # noqa: E402
from chain_sim import Cycle  # noqa: E402


# ------------------------------------------------------------------
# plateau_cutoff
# ------------------------------------------------------------------

def test_plateau_cutoff_fires_on_three_identical_failing_sets():
    candidates = [
        {"failing": {"a", "b"}, "wall_s": 100.0},
        {"failing": {"a", "b"}, "wall_s": 100.0},
        {"failing": {"a", "b"}, "wall_s": 100.0},
        {"failing": {"a", "b"}, "wall_s": 100.0},
        {"failing": set(), "wall_s": 100.0},
    ]
    n, wall_s = chain_sim.plateau_cutoff(candidates, k=3)
    assert n == 3
    assert wall_s == 300.0


def test_plateau_cutoff_no_plateau_consumes_everything():
    candidates = [
        {"failing": {"a"}, "wall_s": 50.0},
        {"failing": {"b"}, "wall_s": 50.0},
        {"failing": {"a", "b"}, "wall_s": 50.0},
        {"failing": set(), "wall_s": 50.0},
    ]
    n, wall_s = chain_sim.plateau_cutoff(candidates, k=3)
    assert n == 4
    assert wall_s == 200.0


def test_plateau_cutoff_ignores_empty_failing_sets():
    # three passing candidates in a row must never read as a plateau
    candidates = [
        {"failing": set(), "wall_s": 10.0},
        {"failing": set(), "wall_s": 10.0},
        {"failing": set(), "wall_s": 10.0},
    ]
    n, wall_s = chain_sim.plateau_cutoff(candidates, k=3)
    assert n == 3
    assert wall_s == 30.0


# ------------------------------------------------------------------
# build_dag on a synthetic project
# ------------------------------------------------------------------

SIM_C = '''#include "sim.h"

void om_world_step(om_world *w) {
    om_step_alpha(w);
    om_step_beta(w);
}
'''

ALPHA_C = '''#include "sim.h"

void om_step_alpha(om_world *w) {
    /* STUB */
    (void)w;
}

int om_tick_alpha(const om_world *w, int *out, int max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}
'''

BETA_C = '''#include "sim.h"

void om_step_beta(om_world *w) {
    /* STUB */
    (void)w;
}

int om_tick_beta(const om_world *w, int *out, int max) {
    (void)w; (void)out; (void)max;
    return 0;
}
'''

GAMMA_C = '''#include "sim.h"

int om_region_set(om_world *w, int idx) {
    (void)w; (void)idx;
    return 0;
}

int om_world_new(void) { return 1; }
void om_world_free(int w) { (void)w; }
'''

TEST_CARD_B = '''
def test_R_010_01_reads_alpha(lib, world_factory):
    w = world_factory()
    lib.om_world_step(w)
    buf = [0] * 8
    lib.om_tick_alpha(w, buf, 8)
'''

TEST_CARD_C = '''
def test_R_011_01_reads_region_set(lib, world_factory):
    w = world_factory()
    lib.om_region_set(w, 0)
'''

TEST_CARD_A = '''
def test_R_009_01_writes_alpha(lib, world_factory):
    w = world_factory()
    lib.om_world_step(w)
'''

TEST_CARD_GATE = '''
def test_R_009_01_writes_alpha(lib, world_factory):
    w = world_factory()
    lib.om_world_step(w)


def test_R_010_01_reads_alpha(lib, world_factory):
    w = world_factory()
    lib.om_world_step(w)
'''

CONFTEST = '''
'''


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "sim.h").write_text("/* synthetic header */\n")
    (project / "csrc" / "sim.c").write_text(SIM_C)
    (project / "csrc" / "alpha.c").write_text(ALPHA_C)
    (project / "csrc" / "beta.c").write_text(BETA_C)
    (project / "csrc" / "gamma.c").write_text(GAMMA_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_card_a.py").write_text(TEST_CARD_A)
    (project / "tests" / "csim" / "test_card_b.py").write_text(TEST_CARD_B)
    (project / "tests" / "csim" / "test_card_c.py").write_text(TEST_CARD_C)
    (project / "tests" / "csim" / "test_gate.py").write_text(TEST_CARD_GATE)
    return project


def _card(project: Path, *, snippet_symbol: str, test_file: str, kind: str | None = None,
          goal: str = "goal") -> dict:
    card = {
        "project": str(project),
        "acceptance": [f"pytest -q {test_file}"],
        "snippet_symbol": snippet_symbol,
        "test_file": test_file,
        "goal": goal,
    }
    if kind:
        card["kind"] = kind
    return card


def test_build_dag_edge_from_stub_owner_to_reader(tmp_path):
    project = _init_project(tmp_path)
    cards = {
        "card-a": _card(project, snippet_symbol="om_step_alpha, om_tick_alpha",
                         test_file="tests/csim/test_card_a.py"),
        "card-b": _card(project, snippet_symbol="om_step_beta, om_tick_beta",
                         test_file="tests/csim/test_card_b.py"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "card-b"], cards, project, csrc_texts)
    pairs = {(e["from"], e["to"]) for e in dag["edges"]}
    assert ("card-a", "card-b") in pairs
    assert dag["duplicate_owners"] == {}


def test_build_dag_no_edge_when_symbol_already_real(tmp_path):
    project = _init_project(tmp_path)
    # om_region_set is already real code (gamma.c, no STUB body). card-a
    # claims it as its own snippet_symbol (a stale/harmless claim -- the
    # function is done) and card-c's test genuinely calls it; that must
    # never manufacture a dependency edge, since nothing there is still a
    # stub. Positive control: card-b really does depend on card-a (proven
    # by test_build_dag_edge_from_stub_owner_to_reader above), so this
    # detector can fail.
    cards = {
        "card-a": _card(project, snippet_symbol="om_region_set",
                         test_file="tests/csim/test_card_a.py"),
        "card-c": _card(project, snippet_symbol="om_step_beta, om_tick_beta",
                         test_file="tests/csim/test_card_c.py"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "card-c"], cards, project, csrc_texts)
    assert dag["edges"] == []


def test_build_dag_duplicate_owner_reported(tmp_path):
    project = _init_project(tmp_path)
    cards = {
        "card-a": _card(project, snippet_symbol="om_step_alpha",
                         test_file="tests/csim/test_card_a.py"),
        "card-a2": _card(project, snippet_symbol="om_step_alpha",
                          test_file="tests/csim/test_card_a.py"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "card-a2"], cards, project, csrc_texts)
    assert dag["duplicate_owners"] == {"om_step_alpha": ["card-a", "card-a2"]}


def test_build_dag_gate_depends_on_every_card_of_its_story(tmp_path):
    project = _init_project(tmp_path)
    cards = {
        "card-a": _card(project, snippet_symbol="om_step_alpha, om_tick_alpha",
                         test_file="tests/csim/test_E01_S009_thing.py"),
        "card-b": _card(project, snippet_symbol="om_step_beta, om_tick_beta",
                         test_file="tests/csim/test_E01_S010_other.py"),
        "gate": _card(project, snippet_symbol="", test_file="tests/csim/test_gate.py",
                      kind="gate", goal="story S-009 gate: every S-009 card composes"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "card-b", "gate"], cards, project, csrc_texts)
    pairs = {(e["from"], e["to"]) for e in dag["edges"]}
    assert ("card-a", "gate") in pairs
    assert ("card-b", "gate") not in pairs


def test_build_dag_gate_ignores_a_retired_phantom_of_the_same_story(tmp_path):
    project = _init_project(tmp_path)
    cards = {
        "card-a": _card(project, snippet_symbol="om_step_alpha, om_tick_alpha",
                         test_file="tests/csim/test_E01_S009_thing.py"),
        "phantom": _card(project, snippet_symbol="om_step_beta, om_tick_beta",
                          test_file="tests/csim/test_E01_S009_thing.py"),
        "gate": _card(project, snippet_symbol="", test_file="tests/csim/test_gate.py",
                      kind="gate", goal="story S-009 gate: every S-009 card composes"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "phantom", "gate"], cards, project, csrc_texts,
                               exclude_from_gates=frozenset({"phantom"}))
    pairs = {(e["from"], e["to"]) for e in dag["edges"]}
    assert ("card-a", "gate") in pairs
    assert ("phantom", "gate") not in pairs


def test_edge_stats_counts_real_vs_serial_implied(tmp_path):
    project = _init_project(tmp_path)
    cards = {
        "card-a": _card(project, snippet_symbol="om_step_alpha, om_tick_alpha",
                         test_file="tests/csim/test_card_a.py"),
        "card-b": _card(project, snippet_symbol="om_step_beta, om_tick_beta",
                         test_file="tests/csim/test_card_b.py"),
    }
    csrc_texts = {p.name: p.read_text() for p in (project / "csrc").glob("*.c")}
    dag = chain_sim.build_dag(["card-a", "card-b"], cards, project, csrc_texts)
    stats = chain_sim.edge_stats(dag)
    assert stats == {"nodes": 2, "real_edges": 1, "serial_implied_edges": 1}


# ------------------------------------------------------------------
# simulate() on a synthetic 6-card graph, hand-computed expectations
#
#   A -> B -> D -> F
#   A -> C -> D
#   E: independent, no edges at all
#
# Real ("as it ran") history (S0's literal timeline), minutes from t=0:
#   A  c1  [0,10)    UNSATISFIABLE            (real next A cycle starts t=100)
#   A  c2  [100,105) DONE
#   B  c1  [105,113) DONE
#   C  c1  [113,119) DONE
#   D  c1  [119,131) INCOMPLETE  (5 candidates, 144s each, identical failing
#                                 set every time -- a textbook plateau that
#                                 never breaks within this cycle)
#   D  c2  [131,137) DONE
#   E  c1  [137,157) DONE
#   F  c1  [157,161) DONE
# ------------------------------------------------------------------

EDGES = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "F")]
NODES = ["A", "B", "C", "D", "E", "F"]
PRIORITY = {n: i for i, n in enumerate(NODES)}


def _plateau_candidates():
    # 5 candidates x 144s = 720s = 12.0 min; first 3 share an identical
    # non-empty failing set, so plateau_cutoff(k=3) stops at candidate 3
    # (432s = 7.2 min) -- 4.8 min of wasted building saved, and the cycle
    # never actually reaches a passing candidate anyway (its real outcome
    # is INCOMPLETE, not DONE), so this is a true early stop, not a false one.
    return [{"failing": {"x", "y"}, "wall_s": 144.0} for _ in range(5)]


def _cycles():
    return {
        "A": [
            Cycle(dur_min=10.0, outcome="UNSATISFIABLE", gap_to_next_min=90.0),
            Cycle(dur_min=5.0, outcome="DONE", gap_to_next_min=None),
        ],
        "B": [Cycle(dur_min=8.0, outcome="DONE", gap_to_next_min=None)],
        "C": [Cycle(dur_min=6.0, outcome="DONE", gap_to_next_min=None)],
        "D": [
            Cycle(dur_min=12.0, outcome="INCOMPLETE", candidates=_plateau_candidates(),
                  gap_to_next_min=0.0),
            Cycle(dur_min=6.0, outcome="DONE", gap_to_next_min=None),
        ],
        "E": [Cycle(dur_min=20.0, outcome="DONE", gap_to_next_min=None)],
        "F": [Cycle(dur_min=4.0, outcome="DONE", gap_to_next_min=None)],
    }


def _run(**overrides):
    kwargs = dict(nodes=NODES, edges=EDGES, cycles_by_task=_cycles(),
                  priority_of=lambda n: PRIORITY[n], targets=NODES)
    kwargs.update(overrides)
    return chain_sim.simulate(**kwargs)


def test_s0_serial_timeline_matches_the_hand_built_history():
    rows = [
        ("A", 0, 10.0, "UNSATISFIABLE"), ("A", 100, 5.0, "DONE"),
        ("B", 105, 8.0, "DONE"), ("C", 113, 6.0, "DONE"),
        ("D", 119, 12.0, "INCOMPLETE"), ("D", 131, 6.0, "DONE"),
        ("E", 137, 20.0, "DONE"), ("F", 157, 4.0, "DONE"),
    ]
    import datetime as dt
    base = dt.datetime(2000, 1, 1)
    rows = [(t, base + dt.timedelta(minutes=m), d, o) for (t, m, d, o) in rows]
    result = chain_sim.s0_timeline(rows)
    assert result["building_min"] == 71.0
    assert result["idle_min"] == 90.0
    assert result["finish_min"] == 161.0


def test_s1_dag_escalate_and_continue_fills_idle_with_independent_work():
    # S1: no plateau shortening yet. The GPU never idles while E (no deps)
    # is ready; the only idle left is the stretch where NOTHING is ready
    # (A blocked 10->100, E already finished at 30).
    result = _run(use_plateau=False, fix_delay_min=None)
    assert result["all_done"]
    assert result["building_min"] == 71.0  # same total work as S0
    assert result["idle_min"] == 70.0      # 100 - 30: a real, unavoidable gap
    assert result["finish_min"] == 141.0


def test_s1_idle_is_real_when_nothing_else_is_ready():
    # Same run: confirm the one remaining idle stretch is exactly the gap
    # where A is blocked and every other ready node has already run out.
    result = _run(use_plateau=False, fix_delay_min=None)
    idle_events = [e for e in result["events"] if e[0] == "IDLE"]
    assert idle_events == [("IDLE", 30.0, 100.0)]


def test_s2_plateau_shortens_wasted_building_without_changing_idle():
    result = _run(use_plateau=True, fix_delay_min=None)
    assert result["all_done"]
    assert result["building_min"] == 71.0 - 4.8
    assert result["idle_min"] == 70.0
    assert abs(result["finish_min"] - 136.2) < 1e-9


def test_s3_autonomous_fix_faster_than_human_erases_the_idle_gap():
    # A 15-minute autonomous fix lands (t=25) before E even finishes
    # (t=30), so the GPU never runs dry at all.
    result = _run(use_plateau=True, fix_delay_min=15.0)
    assert result["all_done"]
    assert result["idle_min"] == 0.0
    assert abs(result["building_min"] - 66.2) < 1e-9


def test_s3_autonomous_fix_slower_than_human_workaround_still_helps():
    # A 60-minute autonomous fix is slower than a lucky independent card,
    # but still much faster than the real 90-minute human latency.
    result_60 = _run(use_plateau=True, fix_delay_min=60.0)
    result_s2 = _run(use_plateau=True, fix_delay_min=None)
    assert result_60["idle_min"] < result_s2["idle_min"]
    assert result_60["idle_min"] == 40.0  # blocked_until = 10+60=70; E ends at 30


def test_retired_phantom_never_blocks_the_targets():
    # A phantom card with no dependents (nothing needs it) that never goes
    # DONE must not stop the simulation from finishing the real targets.
    cycles = _cycles()
    cycles["PHANTOM"] = [Cycle(dur_min=5.0, outcome="INCOMPLETE", gap_to_next_min=None)] * 12
    nodes = NODES + ["PHANTOM"]
    priority = {**PRIORITY, "PHANTOM": -1}  # highest priority, competes hardest
    result = chain_sim.simulate(nodes=nodes, edges=EDGES, cycles_by_task=cycles,
                                 priority_of=lambda n: priority[n], targets=NODES,
                                 retire_on_block=frozenset({"PHANTOM"}))
    assert result["all_done"]
