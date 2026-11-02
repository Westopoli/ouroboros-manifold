# Rule pins: R-039-05@b3cf0e, R-999-05@?
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


def _write_raw_card(tmp_path: Path, project: Path, *, snippet_file: str, snippet_symbol: str,
                     acceptance: list[str]) -> Path:
    card = tmp_path / "card.md"
    lines = ["---", f"project: {project}", "acceptance:"]
    lines += [f'  - "{a}"' for a in acceptance]
    lines += [
        f'allowed_files: "{snippet_file}"',
        f"snippet_file: {snippet_file}",
        f'snippet_symbol: "{snippet_symbol}"',
        "expected_lines: 40",
        "---",
        "",
        "## Brief for DeepSeek",
        "Synthetic card, not real.",
        "",
    ]
    card.write_text("\n".join(lines))
    return card


def test_rule_g_const_only_symbol_with_world_step_fails(tmp_path):
    # The 205a class of defect: the card's snippet_file (elsewhere.c) defines
    # only a `const om_world *` read-back (om_pending_telegraphs) and nothing
    # that can mutate the world, but acceptance drives om_world_step and
    # expects mutated world state -- exactly collision.c's real shape before
    # this fix (om_tick_collisions was its only exported symbol).
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_001_03_reads_stub(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_pending_telegraphs(w, None, 0)\n"
    )
    card = _write_raw_card(
        tmp_path, project, snippet_file="csrc/elsewhere.c", snippet_symbol="om_pending_telegraphs",
        acceptance=[
            f"{sys.executable} -m pytest -q "
            "tests/csim/test_widgets.py::test_R_001_02_other "
            "tests/csim/test_widgets.py::test_R_001_03_reads_stub"
        ],
    )
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "CONST_ONLY" in proc.stdout


def test_rule_g_mutating_symbol_with_world_step_passes(tmp_path):
    # 204a3's shape: the snippet_symbol (om_world_step itself here, standing
    # in for a real mutating step function) takes a non-const om_world *, so
    # CONST_ONLY must not fire even though acceptance also drives om_world_step.
    project = _init_project(tmp_path)
    card = _write_raw_card(
        tmp_path, project, snippet_file="csrc/live.c", snippet_symbol="om_world_step",
        acceptance=[
            f"{sys.executable} -m pytest -q "
            "tests/csim/test_widgets.py::test_R_001_01_basic "
            "tests/csim/test_widgets.py::test_R_001_02_other"
        ],
    )
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "CONST_ONLY" not in proc.stdout


def test_forbidden_allowed_path_scripts_specfactory_fails(tmp_path):
    # PX-10 (docs/northstar/plans/briefs/2026-09-21-px-batch-b-spec-content-
    # boundary.md): a card may not allow a path under scripts/specfactory/ --
    # that is where the gates and validators it is lint-checked against live.
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, allowed_files="scripts/specfactory/pack_validate.py")
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FORBIDDEN_ALLOWED_PATH" in proc.stdout
    assert "scripts/specfactory/pack_validate.py" in proc.stdout


def test_forbidden_allowed_path_tests_dir_fails(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, allowed_files="tests/csim/test_widgets.py")
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FORBIDDEN_ALLOWED_PATH" in proc.stdout
    assert "tests/csim/test_widgets.py" in proc.stdout


def test_forbidden_allowed_path_one_of_several_still_named(tmp_path):
    # A card mixing a legitimate allowed path with a forbidden one still
    # fails, and the finding names the forbidden path, not the legitimate one.
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, allowed_files="csrc/agent.c, scripts/specfactory/card_lint.py")
    proc = _run(card)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FORBIDDEN_ALLOWED_PATH" in proc.stdout
    assert "scripts/specfactory/card_lint.py" in proc.stdout


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


# ---- --fuel report mode (audit 2026-09-21, item 2) ----

def _run_fuel(queue: Path, project: Path, register: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CARD_LINT), "--fuel", str(queue), "--project", str(project),
         "--register", str(register), *extra],
        capture_output=True, text=True,
    )


def _write_fuel_card(path: Path, project: Path, *, rules_file: str, snippet_file: str,
                      snippet_symbol: str, test_call: str) -> None:
    lines = [
        "---", f"project: {project}", "acceptance:",
        f'  - "{sys.executable} -m pytest -q tests/csim/test_widgets.py::{test_call}"',
        f'allowed_files: "{snippet_file}"', f"snippet_file: {snippet_file}",
        f'snippet_symbol: "{snippet_symbol}"', f"rules_file: {rules_file}",
        "expected_lines: 40", "---", "", "## Brief for DeepSeek", "Synthetic.", "",
    ]
    path.write_text("\n".join(lines))


def test_fuel_report_buckets_buildable_missing_file_and_open_q(tmp_path):
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_002_01_missing(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    lib.om_this_symbol_does_not_exist(w)\n"
        "\n\n"
        "def test_R_999_05_flagged_rule(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    isolate_agents(lib, w)\n"
        "    set_faction(lib, w, 0, 1)\n"
    )
    queue = tmp_path / "queue"
    parked = queue / "parked"
    parked.mkdir(parents=True)

    # E-01: buildable (live queue card, real project.c function, no FAIL).
    _write_fuel_card(queue / "001-e01-ok.md", project, rules_file="rules/E-01.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_001_01_basic")
    # E-02: blocked by a missing snippet_file (parked, .hold).
    _write_fuel_card(parked / "002-e02-missing.md.hold", project, rules_file="rules/E-02.md",
                      snippet_file="csrc/does_not_exist.c", snippet_symbol="om_ghost",
                      test_call="test_R_001_01_basic")
    # E-03: blocked by an ABI gap (symbol defined nowhere).
    _write_fuel_card(parked / "003-e03-abigap.md.hold", project, rules_file="rules/E-03.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_002_01_missing")
    # A dead suffix (.retired) must not be counted at all.
    (parked / "004-e04-dead.md.retired").write_text("not a real card")

    register = tmp_path / "ambiguity_register.md"
    register.write_text(
        "| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n"
        "|---|---|---|---|---|---|\n"
        "| Q-999-01 | E-05 / S-999 | Does R-999-05 need a draw? | (a) x; (b) y | open | |\n"
    )
    # E-05, story S-999: only the flagged rule (R-999-05) is held, not the epic.
    _write_fuel_card(parked / "005-e05-openq.md.hold", project, rules_file="rules/E-05.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_999_05_flagged_rule")
    # Same epic, same story-numbering family, a DIFFERENT rule the row never
    # names -- proves the hold is rule-scoped, not epic- or even story-wide
    # once a row narrows to a specific rule (R13/Q-039-01).
    _write_fuel_card(queue / "006-e05-unflagged.md", project, rules_file="rules/E-05.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_001_01_basic")

    proc = _run_fuel(queue, project, register, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert "001-e01-ok" in data["buckets"]["buildable"]
    assert "002-e02-missing" in data["buckets"]["missing_file"]
    assert "003-e03-abigap" in data["buckets"]["abi_gap"]
    assert "005-e05-openq" in data["buckets"]["open_q"]
    assert "006-e05-unflagged" in data["buckets"]["buildable"]
    assert "004-e04-dead" not in " ".join(sum(data["buckets"].values(), []))
    assert data["per_epic"]["E-01"]["buildable"] == 1
    assert data["per_epic"]["E-02"]["missing_file"] == 1
    assert data["per_epic"]["E-03"]["abi_gap"] == 1
    assert data["per_epic"]["E-05"]["open_q"] == 1
    assert data["per_epic"]["E-05"]["buildable"] == 1
    assert "R-999-05" in data["flagged_rules"]
    assert data["flagged_stories"] == []


def test_fuel_report_open_flag_holds_whole_story_when_no_rule_named(tmp_path):
    """A register row whose Question text names no rule id (only a story in
    the "Epic / story" column) holds every rule of that story -- the
    ambiguity has not been narrowed yet."""
    project = _init_project(tmp_path)
    (project / "tests" / "csim" / "test_widgets.py").write_text(
        TEST_FILE + "\n\n"
        "def test_R_998_01_in_flagged_story(lib, world_factory):\n"
        "    w = world_factory()\n"
        "    isolate_agents(lib, w)\n"
        "    set_faction(lib, w, 0, 1)\n"
    )
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_fuel_card(queue / "007-e05-story-held.md", project, rules_file="rules/E-05.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_998_01_in_flagged_story")
    _write_fuel_card(queue / "008-e05-story-unheld.md", project, rules_file="rules/E-05.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_001_01_basic")
    register = tmp_path / "ambiguity_register.md"
    register.write_text(
        "| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n"
        "|---|---|---|---|---|---|\n"
        "| Q-998-01 | E-05 / S-998 | Some open question naming no rule. | (a) x; (b) y | open | |\n"
    )
    proc = _run_fuel(queue, project, register, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert "007-e05-story-held" in data["buckets"]["open_q"]
    assert "008-e05-story-unheld" in data["buckets"]["buildable"]
    assert data["flagged_stories"] == ["S-998"]


def test_fuel_report_real_register_holds_r_039_05_not_205a(tmp_path):
    """R13/Q-039-01, the real audit finding: the real ambiguity register
    flags R-039-05 by name. A card whose acceptance proves that rule is
    held; the real 205a card (re-cut to exclude R-039-05) is not. The card is
    a vendored copy (tests/specfactory/fixtures/), identical to Agora's parked
    205a-e05-collision-lottery.md.hold, so the test needs no other checkout."""
    sys.path.insert(0, str(CARD_LINT.parent))
    import card_lint  # noqa: E402

    project = card_lint.DEFAULT_PROJECT
    # Vendored register as it stood before 1ec91c0c closed Q-039-01 (2026-10-18).
    register = Path(__file__).resolve().parent / "fixtures" / "ambiguity_register_pre_1ec91c0c.md"
    flagged_rules, flagged_stories = card_lint.register_flags(register)
    assert "R-039-05" in flagged_rules

    held_card = {
        "acceptance": [
            f"{sys.executable} -m pytest -q "
            "tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py"
            "::test_R_039_05_each_collider_s_strength_applied"
        ],
    }
    assert card_lint.card_is_held(held_card, project, flagged_rules, flagged_stories)

    real_205a = card_lint.parse_card(
        Path(__file__).resolve().parent / "fixtures" / "205a-e05-collision-lottery.md"
    )
    assert not card_lint.card_is_held(real_205a, project, flagged_rules, flagged_stories)


def test_control_register_without_open_flag_does_not_hold_r_039_05(tmp_path):
    """Positive control for the test above: a register with no open flag
    flags no rule, so the R-039-05 card is not held. See also:
    test_fuel_report_real_register_holds_r_039_05_not_205a."""
    sys.path.insert(0, str(CARD_LINT.parent))
    import card_lint  # noqa: E402

    register = tmp_path / "ambiguity_register.md"
    register.write_text("| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n|---|---|---|---|---|---|\n")
    flagged_rules, flagged_stories = card_lint.register_flags(register)
    assert "R-039-05" not in flagged_rules
    held_card = {
        "acceptance": [
            f"{sys.executable} -m pytest -q "
            "tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py"
            "::test_R_039_05_each_collider_s_strength_applied"
        ],
    }
    assert not card_lint.card_is_held(held_card, card_lint.DEFAULT_PROJECT, flagged_rules, flagged_stories)


def test_fuel_report_text_mode_prints_summary(tmp_path):
    project = _init_project(tmp_path)
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_fuel_card(queue / "001-e01-ok.md", project, rules_file="rules/E-01.md",
                      snippet_file="csrc/agent.c", snippet_symbol="om_faction_candidates",
                      test_call="test_R_001_01_basic")
    register = tmp_path / "ambiguity_register.md"
    register.write_text("| Flag | Epic / story | Question | Candidate answers | Status | Answer |\n|---|---|---|---|---|---|\n")
    proc = _run_fuel(queue, project, register)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "buildable now:" in proc.stdout
    assert "blocked (missing file):" in proc.stdout
    assert "blocked (ABI gap):" in proc.stdout
    assert "blocked (open Q-):" in proc.stdout
