# spec: docs/northstar/spec_factory.md pipeline (pre-queue mechanical gate)
"""Tests for scripts/specfactory/card_lint.py.

Builds a throwaway synthetic project per test (csrc/*.c, tests/csim/*.py,
tests/csim/conftest.py) so this suite never depends on the real
ouroboros-manifold repo's own csrc/tests state -- card_lint applies to some
card's project, and a synthetic one proves the mechanism without coupling to
a real card or a real build.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CARD_LINT = REPO / "scripts" / "specfactory" / "card_lint.py"

CONFTEST = '''
def isolate_agents(lib, w):
    lib.om_world_set_feature(w, 1, 1)


def set_faction(lib, w, faction_id, archetype):
    lib.om_faction_set(w, faction_id, archetype)


def _read_records(lib, w, name, max_records=8):
    buf = [0] * max_records
    n = getattr(lib, name)(w, buf, max_records)
    return buf[:n]


def read_decisions(lib, w):
    return _read_records(lib, w, "om_tick_decisions")


def read_widgets(lib, w, kind):
    return _read_records(lib, w, kind)
'''

TEST_FILE = '''
from conftest import isolate_agents, set_faction, read_decisions


def test_R_001_01_basic(lib, world_factory):
    w = world_factory()
    isolate_agents(lib, w)
    set_faction(lib, w, 0, 1)
    decisions = read_decisions(lib, w)
    assert decisions is not None


def test_R_001_02_other(lib, world_factory):
    w = world_factory()
    lib.om_world_step(w)
'''

LIVE_C = '''#include "ouroboros_sim.h"

void om_world_set_feature(om_world *w, int f, int on) { (void)w; (void)f; (void)on; }
int om_faction_set(om_world *w, int fid, int arch) { (void)w; (void)fid; (void)arch; return 0; }
int om_world_step(om_world *w) { (void)w; return 0; }
int om_tick_decisions(const om_world *w, void *out, int max) { (void)w; (void)out; (void)max; return 0; }
'''

STUB_ELSEWHERE_C = '''#include "ouroboros_sim.h"
/* body below is a STUB the build card replaces. */

int om_pending_telegraphs(const om_world *w, void *out, int max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}
'''

AGENT_C = '''#include "ouroboros_sim.h"

int om_faction_candidates(const om_world *w, int fid, void *out, int max) {
    (void)w; (void)fid; (void)out; (void)max;
    return 0;
}

int om_step_decisions_helper_not_named(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}
'''


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text("/* synthetic header */\n")
    (project / "csrc" / "live.c").write_text(LIVE_C)
    (project / "csrc" / "elsewhere.c").write_text(STUB_ELSEWHERE_C)
    (project / "csrc" / "agent.c").write_text(AGENT_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_widgets.py").write_text(TEST_FILE)
    return project


def _write_card(tmp_path: Path, project: Path, *, acceptance=None, allowed_files="csrc/agent.c",
                 snippet_symbol="om_faction_candidates", expected_lines=40, extra_frontmatter="") -> Path:
    if acceptance is None:
        acceptance = [
            f"{sys.executable} -m pytest -q "
            "tests/csim/test_widgets.py::test_R_001_01_basic "
            "tests/csim/test_widgets.py::test_R_001_02_other"
        ]
    card = tmp_path / "card.md"
    lines = ["---", f"project: {project}", "acceptance:"]
    lines += [f'  - "{a}"' for a in acceptance]
    lines += [
        f'allowed_files: "{allowed_files}"',
        "snippet_file: csrc/agent.c",
        f'snippet_symbol: "{snippet_symbol}"',
        f"expected_lines: {expected_lines}",
    ]
    if extra_frontmatter:
        lines.append(extra_frontmatter)
    lines.append("---")
    lines.append("")
    lines.append("## Brief for DeepSeek")
    lines.append("Synthetic card, not real.")
    card.write_text("\n".join(lines) + "\n")
    return card


def _run(card: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CARD_LINT), str(card), *extra],
        capture_output=True, text=True,
    )


def test_lint_ok_when_everything_resolves(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LINT OK" in proc.stdout


def test_rule_a_stub_outside_allowed_files_fails(tmp_path):
    project = _init_project(tmp_path)
    # test_widgets.py's read_widgets helper isn't called by any test yet;
    # add a test that reaches the stub in elsewhere.c via a direct lib call.
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_001_03_stub(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_pending_telegraphs(w, None, 0)\n"
    )
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_widgets.py::test_R_001_03_stub"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STUB_OUTSIDE_ALLOWED" in proc.stdout
    assert "om_pending_telegraphs" in proc.stdout
    assert "LINT FAILED (1)" in proc.stdout


def test_rule_b_symbol_defined_nowhere_is_abi_gap(tmp_path):
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_001_04_ghost(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_this_symbol_does_not_exist(w)\n"
    )
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_widgets.py::test_R_001_04_ghost"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "ABI_GAP" in proc.stdout
    assert "om_this_symbol_does_not_exist" in proc.stdout


def test_rule_c_snippet_symbol_not_defined_in_snippet_file(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, snippet_symbol="om_symbol_never_written")
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SNIPPET_SYMBOL_UNDEFINED" in proc.stdout
    assert "om_symbol_never_written" in proc.stdout


def test_rule_d_too_many_snippet_symbols_fails(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, snippet_symbol="a, b, c, d, e, f")
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SIZING_SYMBOLS" in proc.stdout


def test_rule_d_expected_lines_too_large_fails(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, expected_lines=500)
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SIZING_LINES" in proc.stdout


def test_rule_e_bad_node_id_missing_file(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_does_not_exist.py::test_x"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "BAD_NODE_ID" in proc.stdout


def test_rule_e_bad_node_id_missing_function(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_widgets.py::test_no_such_test"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "BAD_NODE_ID" in proc.stdout


def test_rule_f_spans_another_card(tmp_path):
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_001_05_stub(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_pending_telegraphs(w, None, 0)\n"
    )
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "OTHER-card.md").write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        '  - "true"\n'
        'allowed_files: "csrc/elsewhere.c"\n'
        "snippet_file: csrc/elsewhere.c\n"
        'snippet_symbol: "om_pending_telegraphs"\n'
        "---\n"
    )
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_widgets.py::test_R_001_05_stub"
    ])
    proc = _run(card, "--queue", str(queue))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "SPANS_ANOTHER_CARD" in proc.stdout
    assert "OTHER-card" in proc.stdout


def test_warn_own_file_stub_not_named_does_not_fail(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)  # agent.c has an unnamed stub helper
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "LINT WARN" in proc.stdout
    assert "OWN_FILE_STUB_NOT_NAMED" in proc.stdout
    assert "LINT OK" in proc.stdout


def test_transitive_dynamic_getattr_symbol_is_resolved(tmp_path):
    # read_decisions -> _read_records(lib, w, "om_tick_decisions") -> getattr(lib, name)(...)
    # This is exactly the tests/csim/conftest.py _read_records shape; if this
    # resolution is broken, om_tick_decisions never enters the symbol set and
    # every rule downstream of it (a/b/f) silently never fires for readers.
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # om_tick_decisions resolves to live.c and is not a stub, so it must not
    # appear as a finding -- but we can prove it was reached by making it a
    # stub outside allowed_files and checking the finding names it.
    (project / "csrc" / "live.c").write_text(
        LIVE_C.replace(
            'int om_tick_decisions(const om_world *w, void *out, int max) { (void)w; (void)out; (void)max; return 0; }',
            'int om_tick_decisions(const om_world *w, void *out, int max) {\n'
            "    /* STUB */\n"
            "    (void)w; (void)out; (void)max;\n"
            "    return 0;\n"
            "}\n",
        )
    )
    proc = _run(card, "--json")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    codes = {(f["code"], f["message"]) for f in data["findings"]}
    assert any("om_tick_decisions" in msg for _code, msg in codes), data


def test_exit_2_on_missing_card(tmp_path):
    proc = _run(tmp_path / "no_such_card.md")
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_exit_2_on_project_not_a_directory(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    text = card.read_text().replace(f"project: {project}", f"project: {tmp_path / 'does_not_exist'}")
    card.write_text(text)
    proc = _run(card)
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_exit_2_on_empty_acceptance(tmp_path):
    project = _init_project(tmp_path)
    card = tmp_path / "card.md"
    card.write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        'allowed_files: "csrc/agent.c"\n'
        "snippet_file: csrc/agent.c\n"
        'snippet_symbol: "om_faction_candidates"\n'
        "---\n"
    )
    proc = _run(card)
    assert proc.returncode == 2, proc.stdout + proc.stderr


NESTED_CONFTEST = '''
def isolate_agents(lib, w):
    lib.om_world_set_feature(w, 1, 1)


def reach_stub_via_conftest(lib, w):
    lib.om_pending_telegraphs(w, None, 0)
'''

NESTED_CONTROLS_TEST = '''
from conftest import reach_stub_via_conftest


def test_R_900_01_via_conftest_helper(lib, world_factory):
    w = world_factory()
    reach_stub_via_conftest(lib, w)
'''

LOCAL_HELPER_TEST = '''
def _reach_stub_locally(lib, w):
    lib.om_pending_telegraphs(w, None, 0)


def test_R_901_01_via_local_helper(lib, world_factory):
    w = world_factory()
    _reach_stub_locally(lib, w)
'''

CHAIN_CONFTEST = '''
def isolate_agents(lib, w):
    lib.om_world_set_feature(w, 1, 1)


def reach_stub_from_conftest(lib, w):
    lib.om_pending_telegraphs(w, None, 0)
'''

CHAIN_CONTROLS_TEST = '''
from conftest import reach_stub_from_conftest


def _wrapper_local(lib, w):
    reach_stub_from_conftest(lib, w)


def test_R_902_01_chained_local_then_conftest(lib, world_factory):
    w = world_factory()
    _wrapper_local(lib, w)
'''

LOCAL_GETATTR_TEST = '''
def _read_dynamic(lib, w, name, max_records=8):
    buf = [0] * max_records
    n = getattr(lib, name)(w, buf, max_records)
    return buf[:n]


def _read_decisions_local(lib, w):
    return _read_dynamic(lib, w, "om_tick_decisions")


def test_R_903_01_local_helper_getattr(lib, world_factory):
    w = world_factory()
    rows = _read_decisions_local(lib, w)
    assert rows is not None
'''


def _init_nested_project(tmp_path: Path, *, subdir: str, conftest_src: str, test_src: str,
                          test_filename: str = "test_control_thing.py") -> Path:
    """Like _init_project, but the test lives at tests/<subdir>/controls/ with
    its conftest.py one directory up at tests/<subdir>/ -- there is no
    conftest.py in the controls/ directory itself, mirroring
    tests/csim/controls/ in the real repo."""
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    controls_dir = project / "tests" / subdir / "controls"
    controls_dir.mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text("/* synthetic header */\n")
    (project / "csrc" / "live.c").write_text(LIVE_C)
    (project / "csrc" / "elsewhere.c").write_text(STUB_ELSEWHERE_C)
    (project / "csrc" / "agent.c").write_text(AGENT_C)
    (project / "tests" / subdir / "conftest.py").write_text(conftest_src)
    (controls_dir / test_filename).write_text(test_src)
    return f"tests/{subdir}/controls/{test_filename}", project


def test_stub_reached_only_via_conftest_two_dirs_up_fails(tmp_path):
    node_path, project = _init_nested_project(
        tmp_path, subdir="x", conftest_src=NESTED_CONFTEST, test_src=NESTED_CONTROLS_TEST,
    )
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q {node_path}::test_R_900_01_via_conftest_helper"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STUB_OUTSIDE_ALLOWED" in proc.stdout
    assert "om_pending_telegraphs" in proc.stdout
    assert "LINT FAILED (1)" in proc.stdout


def test_stub_reached_only_via_module_local_helper_fails(tmp_path):
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_local_helper.py").write_text(LOCAL_HELPER_TEST)
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_local_helper.py::test_R_901_01_via_local_helper"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STUB_OUTSIDE_ALLOWED" in proc.stdout
    assert "om_pending_telegraphs" in proc.stdout
    assert "LINT FAILED (1)" in proc.stdout


def test_stub_reached_via_chained_local_then_conftest_helper_fails(tmp_path):
    node_path, project = _init_nested_project(
        tmp_path, subdir="y", conftest_src=CHAIN_CONFTEST, test_src=CHAIN_CONTROLS_TEST,
    )
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q {node_path}::test_R_902_01_chained_local_then_conftest"
    ])
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "STUB_OUTSIDE_ALLOWED" in proc.stdout
    assert "om_pending_telegraphs" in proc.stdout
    assert "LINT FAILED (1)" in proc.stdout


def test_transitive_dynamic_getattr_through_local_helper_is_resolved(tmp_path):
    # Same shape as test_transitive_dynamic_getattr_symbol_is_resolved, but
    # the getattr(lib, name) call chain is two module-local helpers in the
    # test file itself, not tests/csim/conftest.py's _read_records.
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_local_getattr.py").write_text(LOCAL_GETATTR_TEST)
    card = _write_card(tmp_path, project, acceptance=[
        f"{sys.executable} -m pytest -q tests/csim/test_local_getattr.py::test_R_903_01_local_helper_getattr"
    ])
    proc = _run(card, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr

    (project / "csrc" / "live.c").write_text(
        LIVE_C.replace(
            'int om_tick_decisions(const om_world *w, void *out, int max) { (void)w; (void)out; (void)max; return 0; }',
            'int om_tick_decisions(const om_world *w, void *out, int max) {\n'
            "    /* STUB */\n"
            "    (void)w; (void)out; (void)max;\n"
            "    return 0;\n"
            "}\n",
        )
    )
    proc = _run(card, "--json")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    codes = {(f["code"], f["message"]) for f in data["findings"]}
    assert any("om_tick_decisions" in msg for _code, msg in codes), data


def test_json_output_shape(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["fail_count"] == 0
    assert isinstance(data["findings"], list)
