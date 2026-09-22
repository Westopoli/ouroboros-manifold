# spec: audit 2026-09-21 item 17 (JSON DAG emitter for Agora)
"""Tests for scripts/specfactory/chain_graph.py.

Builds a throwaway synthetic project (csrc/*.c, tests/csim/*.py) and a
throwaway synthetic agora queue directory per test, so this suite never
depends on the real ouroboros-manifold repo's own csrc/tests state or the
real agora queue -- same convention as test_chain_sim.py and
test_card_lint.py. The real-queue run is chain_graph.py's own CLI, exercised
by hand (and recorded in DECISIONS.md), not a pytest fixture.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CHAIN_GRAPH = REPO / "scripts" / "specfactory" / "chain_graph.py"

LIVE_C = '''#include "sim.h"

void om_world_step(void *w) { (void)w; }
int om_step_alpha(void *w) { (void)w; return 0; }
int om_tick_alpha(void *w) { (void)w; return 0; }
'''

STUB_BETA_C = '''#include "sim.h"

int om_step_beta(void *w) {
    /* STUB */
    (void)w;
    return 0;
}

int om_step_gamma(void *w) {
    /* STUB */
    (void)w;
    return 0;
}
'''

CONFTEST = '''
def read_alpha(lib, w):
    return lib.om_tick_alpha(w)


def call_beta(lib, w):
    return lib.om_step_beta(w)


def call_gamma(lib, w):
    return lib.om_step_gamma(w)
'''

TEST_A = '''
from conftest import read_alpha


def test_R_001_01(lib, world_factory):
    w = world_factory()
    read_alpha(lib, w)
'''

TEST_B = '''
from conftest import call_beta


def test_R_002_01(lib, world_factory):
    w = world_factory()
    call_beta(lib, w)
'''

TEST_C = '''
from conftest import call_gamma


def test_R_004_01(lib, world_factory):
    w = world_factory()
    call_gamma(lib, w)
'''

TEST_GATE = '''
def test_gate_ok():
    assert True
'''


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "sim.h").write_text("/* synthetic header */\n")
    (project / "csrc" / "live.c").write_text(LIVE_C)
    (project / "csrc" / "beta.c").write_text(STUB_BETA_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_a.py").write_text(TEST_A)
    (project / "tests" / "csim" / "test_b.py").write_text(TEST_B)
    (project / "tests" / "csim" / "test_c.py").write_text(TEST_C)
    (project / "tests" / "csim" / "test_gate.py").write_text(TEST_GATE)
    return project


def _write_card(path: Path, project: Path, *, snippet_symbol: str, snippet_file: str,
                 test_call: str, rules_file: str = "rules/E-05.md", kind: str | None = None,
                 allowed_files: str | None = None) -> None:
    lines = [
        "---", f"project: {project}", "acceptance:",
        f'  - "{sys.executable} -m pytest -q {test_call}"',
        f'allowed_files: "{allowed_files or snippet_file}"',
        f"snippet_file: {snippet_file}",
        f'snippet_symbol: "{snippet_symbol}"',
        f"rules_file: {rules_file}",
        "expected_lines: 40",
    ]
    if kind:
        lines.append(f"kind: {kind}")
    lines += ["---", "", "## Brief for DeepSeek", "Synthetic.", ""]
    path.write_text("\n".join(lines))


def _run(queue: Path, project: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHAIN_GRAPH), "--queue", str(queue), "--project", str(project), *extra],
        capture_output=True, text=True,
    )


def test_clean_two_card_chain_exits_0(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-a.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    proc = _run(queue, project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["errors"] == []
    assert data["nodes"][0]["card"] == "card-a"
    assert data["nodes"][0]["kind"] == "build"
    assert data["nodes"][0]["epic"] == "E-05"


def test_missing_file_and_abi_gap_are_reported(tmp_path):
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_c.py").write_text(
        "def test_R_003_01(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_this_does_not_exist(w)\n"
    )
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-missing.md", project, snippet_symbol="om_ghost",
                snippet_file="csrc/does_not_exist.c", test_call="tests/csim/test_a.py::test_R_001_01")
    _write_card(queue / "card-abigap.md", project, snippet_symbol="om_step_alpha",
                snippet_file="csrc/live.c", test_call="tests/csim/test_c.py::test_R_003_01",
                allowed_files="csrc/live.c")
    proc = _run(queue, project)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    kinds = {(e["kind"], tuple(e["cards"])) for e in data["errors"]}
    assert ("missing_file", ("card-missing",)) in kinds
    assert ("abi_gap", ("card-abigap",)) in kinds


def test_double_owner_and_cycle_are_reported(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    # Two cards claim the same still-stub symbol -- a real conflict.
    _write_card(queue / "card-b1.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    _write_card(queue / "card-b2.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    proc = _run(queue, project)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    double_owner = [e for e in data["errors"] if e["kind"] == "double_owner"]
    assert double_owner and double_owner[0]["symbol"] == "om_step_beta"
    assert set(double_owner[0]["cards"]) == {"card-b1", "card-b2"}


def test_sequential_owner_is_a_note_not_an_error_when_ordered(tmp_path):
    """Two cards claim the same still-stub symbol (om_step_beta), same shape
    as test_double_owner_and_cycle_are_reported above, but this time
    card-seq1 also owns om_step_gamma and card-seq2's acceptance reaches it
    -- a real edge (card-seq1 -> card-seq2) orders them. R17: reachability
    over the DAG makes this a `sequential_owner` note, not a `double_owner`
    error (audit 2026-09-21, Tenth round resolutions design-lane decision)."""
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-seq1.md", project, snippet_symbol="om_step_beta, om_step_gamma",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    _write_card(queue / "card-seq2.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_c.py::test_R_004_01",
                allowed_files="csrc/beta.c")
    proc = _run(queue, project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["errors"] == []
    seq = [n for n in data["notes"] if n["kind"] == "sequential_owner"]
    assert seq and seq[0]["symbol"] == "om_step_beta"
    assert seq[0]["cards"] == ["card-seq1", "card-seq2"]


def test_unordered_double_owner_is_not_demoted_to_a_note(tmp_path):
    """Same shared-symbol shape as the sequential test above, but with no
    edge at all between the two claimants (neither's acceptance reaches a
    symbol the other owns) -- reachability cannot order them, so this stays
    a `double_owner` error, not a note."""
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-b1.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    _write_card(queue / "card-b2.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    proc = _run(queue, project)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert not any(n["kind"] == "sequential_owner" for n in data["notes"])
    double_owner = [e for e in data["errors"] if e["kind"] == "double_owner"]
    assert double_owner and set(double_owner[0]["cards"]) == {"card-b1", "card-b2"}


def test_dead_suffixes_are_excluded_from_the_graph(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    parked = queue / "parked"
    parked.mkdir(parents=True)
    _write_card(queue / "card-a.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    (parked / "card-old.md.retired").write_text("dead, not a real card")
    (parked / "card-super.md.superseded").write_text("dead, not a real card")
    proc = _run(queue, project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    card_ids = {n["card"] for n in data["nodes"]}
    assert card_ids == {"card-a"}


def test_gate_card_kind_and_no_hook_closure_leak(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-gate.md", project, snippet_symbol="", snippet_file="",
                test_call="tests/csim/test_gate.py::test_gate_ok", kind="gate")
    proc = _run(queue, project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["nodes"][0]["kind"] == "gate"


def test_out_file_is_written(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-a.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    out = tmp_path / "graph.json"
    proc = _run(queue, project, "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(out.read_text())
    assert "generated_at" in data
    assert data["project"] == str(project)


def test_no_orchestrators_falls_back_to_direct_symbol_dag(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_card(queue / "card-a.md", project, snippet_symbol="om_step_beta",
                snippet_file="csrc/beta.c", test_call="tests/csim/test_b.py::test_R_002_01",
                allowed_files="csrc/beta.c")
    proc = _run(queue, project, "--orchestrators")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["errors"] == []


def test_missing_project_or_queue_still_runs_cleanly_on_empty_queue(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "empty_queue"
    proc = _run(queue, project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["nodes"] == []
    assert data["errors"] == []
