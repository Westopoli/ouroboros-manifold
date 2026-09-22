# spec: docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md R16/R17
"""Tests for scripts/specfactory/skeleton_gen.py.

Builds a throwaway synthetic project (csrc/, tests/csim/, a queue with live
and parked cards) per test, exactly like test_card_lint.py, so this suite
never depends on the real ouroboros-manifold repo's own state.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SKELETON_GEN = REPO / "scripts" / "specfactory" / "skeleton_gen.py"

HEADER = '''#ifndef OUROBOROS_SIM_H
#define OUROBOROS_SIM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct om_world om_world;
typedef enum { OM_TIER_EMPTY = 0 } om_tier;
typedef struct { uint32_t value; } om_widget;

void om_world_free(om_world *w);

#ifdef __cplusplus
}
#endif

#endif /* OUROBOROS_SIM_H */
'''

OM_INTERNAL = '''#ifndef OM_INTERNAL_H
#define OM_INTERNAL_H
#include "ouroboros_sim.h"

#define OM_MAX_NEIGHBORS 32

typedef struct {
    om_tier tier;
    double  military;
} om_region;

struct om_world {
    uint32_t n_regions;
    om_region *regions;

    /* a nested note, like ALG-11's damage-history comment in the real
     * om_internal.h (docs/bible/algorithms.md ALG-11; R-034-07). */
    uint32_t extra;
};

void om_step_events(om_world *w);

#endif /* OM_INTERNAL_H */
'''

OTHER_C = '''#include "ouroboros_sim.h"
double om_chronicle_dead(const om_world *w) { (void)w; return 1.0; }
'''

CONFTEST = '''import ctypes


class OmWidget(ctypes.Structure):
    _fields_ = [("value", ctypes.c_uint32)]


def _bind_e09(lib):
    if getattr(lib, "_e09_bound", False):
        return
    V = ctypes.c_void_p
    P = ctypes.POINTER
    lib.om_chronicle_step.argtypes = [V]
    lib.om_chronicle_step.restype = None
    lib.om_chronicle_shared.argtypes = [V]
    lib.om_chronicle_shared.restype = None
    lib.om_chronicle_dead.argtypes = [V]
    lib.om_chronicle_dead.restype = ctypes.c_double
    for name, st in (("om_chronicle_reader", OmWidget),):
        fn = getattr(lib, name)
        fn.argtypes = [V, P(st), ctypes.c_uint32]
        fn.restype = ctypes.c_uint32
    lib._e09_bound = True
'''

TEST_FILE = '''from conftest import _bind_e09


def test_R_999_01_synthetic(lib, world_factory):
    w = world_factory()
    _bind_e09(lib)
    lib.om_chronicle_step(w)
    lib.om_chronicle_note(w)
    lib.om_chronicle_reader(w, None, 8)
    lib.om_chronicle_ghost(w)
    lib.om_chronicle_dead(w)
    lib.om_chronicle_shared(w)
'''


def _card_text(*, snippet_file: str, snippet_symbol: str, rules_file: str = "rules/E-09.md") -> str:
    return (
        "---\n"
        "project: /unused\n"
        f'allowed_files: "{snippet_file}"\n'
        f"snippet_file: {snippet_file}\n"
        f'snippet_symbol: "{snippet_symbol}"\n'
        f"rules_file: {rules_file}\n"
        "---\n\n## Brief for DeepSeek\nSynthetic card, not real.\n"
    )


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "csrc" / "om_internal.h").write_text(OM_INTERNAL)
    (project / "csrc" / "other.c").write_text(OTHER_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_E09_S999_synthetic.py").write_text(TEST_FILE)
    return project


def _init_queue(tmp_path: Path) -> Path:
    queue = tmp_path / "queue"
    parked = queue / "parked"
    parked.mkdir(parents=True)
    (queue / "220a-e09-chronicle-step.md").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_step"))
    (parked / "220b-e09-chronicle-note.md.hold").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_note"))
    (parked / "220c-e09-chronicle-dead.md.hold").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_dead"))
    (parked / "220d-e09-chronicle-unused.md.hold").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_unused"))
    (parked / "220e-e09-chronicle-reader.md.hold").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_reader"))
    (parked / "220h-e09-chronicle-shared.md.hold").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_shared"))
    (parked / "220f-e09-chronicle-conflict.md.hold").write_text(
        _card_text(snippet_file="csrc/other_owner.c", snippet_symbol="om_chronicle_shared"))
    # a dead suffix must never be consulted
    (parked / "220g-e09-chronicle-retired.md.retired").write_text(
        _card_text(snippet_file="csrc/chronicle.c", snippet_symbol="om_chronicle_should_never_appear"))
    return queue


def _run(project: Path, queue: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKELETON_GEN), "--project", str(project), "--queue", str(queue), *extra],
        capture_output=True, text=True,
    )


def test_generates_only_qualifying_symbols_and_writes_c_file(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    chronicle_c = (project / "csrc" / "chronicle.c").read_text()
    assert "/* STUB */" in chronicle_c
    assert "void om_chronicle_step(om_world *w) {" in chronicle_c
    assert "(void)w;" in chronicle_c
    assert "uint32_t om_chronicle_reader(om_world *w, om_widget *a1, uint32_t a2) {" in chronicle_c
    assert "return 0;" in chronicle_c
    # refused symbols never get a body
    assert "om_chronicle_note(" not in chronicle_c
    assert "om_chronicle_dead(" not in chronicle_c
    assert "om_chronicle_unused(" not in chronicle_c
    assert "om_chronicle_ghost(" not in chronicle_c
    assert "om_chronicle_should_never_appear" not in chronicle_c

    # collision.c shape: header comment, PRIVATE LAYOUT quoting om_internal.h, includes
    assert "PRIVATE LAYOUT" in chronicle_c
    assert "struct om_world {" in chronicle_c
    assert "om_region;" in chronicle_c
    assert '#include "ouroboros_sim.h"' in chronicle_c
    assert '#include "om_internal.h"' in chronicle_c
    assert "E-09" in chronicle_c
    assert "220a-e09-chronicle-step" in chronicle_c


def test_appends_header_declarations_with_epic_comment(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    assert "csrc/chronicle.c skeleton" in header
    assert "E-09" in header
    assert "void om_chronicle_step(om_world *w);" in header
    assert "uint32_t om_chronicle_reader(om_world *w, om_widget *a1, uint32_t a2);" in header
    # never touches the closing guard
    assert header.rstrip().endswith("#endif /* OUROBOROS_SIM_H */")
    # the extern "C" wrapper still closes after the inserted block
    assert header.index("void om_chronicle_step") < header.rindex('#ifdef __cplusplus')


def test_refuses_no_mirror_and_reports_it(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue, "--report")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (project / "csrc" / "chronicle.c").exists()
    assert "om_chronicle_note" in proc.stdout
    assert "no mirror" in proc.stdout


def test_refuses_already_defined_elsewhere(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    chronicle = next(m for m in data if m["module_file"] == "csrc/chronicle.c")
    assert ["om_chronicle_dead", "csrc/other.c"] in [list(x) for x in chronicle["refused_already_elsewhere"]]
    assert "om_chronicle_dead" not in chronicle["generated"]


def test_no_card_and_not_test_called_are_reported(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    chronicle = next(m for m in data if m["module_file"] == "csrc/chronicle.c")
    assert "om_chronicle_ghost" in chronicle["no_card"]
    assert "om_chronicle_unused" in chronicle["not_test_called"]
    # a retired card's symbol must never surface anywhere
    joined = json.dumps(chronicle)
    assert "om_chronicle_should_never_appear" not in joined


def test_conflict_symbol_claimed_by_two_files_is_flagged(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    chronicle = next(m for m in data if m["module_file"] == "csrc/chronicle.c")
    assert "om_chronicle_shared" in chronicle["conflicts"]
    assert "csrc/other_owner.c" in chronicle["conflicts"]["om_chronicle_shared"]
    # never generated anywhere while two cards disagree about its file --
    # generating it in one risks a duplicate definition once the other lands
    assert "om_chronicle_shared" not in chronicle["generated"]
    # unrelated symbols in the same module are unaffected
    assert "om_chronicle_step" in chronicle["generated"]


def test_idempotent_rerun_is_byte_identical(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc1 = _run(project, queue)
    assert proc1.returncode == 0, proc1.stdout + proc1.stderr
    c_before = (project / "csrc" / "chronicle.c").read_text()
    h_before = (project / "csrc" / "ouroboros_sim.h").read_text()

    proc2 = _run(project, queue)
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    c_after = (project / "csrc" / "chronicle.c").read_text()
    h_after = (project / "csrc" / "ouroboros_sim.h").read_text()

    assert c_before == c_after
    assert h_before == h_after


def test_refuses_to_overwrite_a_real_implementation(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc1 = _run(project, queue)
    assert proc1.returncode == 0, proc1.stdout + proc1.stderr

    real_c = (
        '#include "ouroboros_sim.h"\n'
        '#include "om_internal.h"\n'
        "void om_chronicle_step(om_world *w) {\n"
        "    (void)w; /* a real hand-written implementation, not a stub */\n"
        "}\n"
    )
    (project / "csrc" / "chronicle.c").write_text(real_c)

    # auto-discovery now leaves a real implementation alone; force it via
    # --modules to prove the overwrite guard itself refuses, not just skips.
    proc2 = _run(project, queue, "--modules", "csrc/chronicle.c")
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    assert "chronicle.c" in proc2.stderr
    assert (project / "csrc" / "chronicle.c").read_text() == real_c


def test_generated_c_file_is_syntactically_valid(tmp_path):
    # Regression: om_internal.h's struct bodies carry their own nested
    # /* ... */ notes (ALG-11 in the real file; the fixture's own note
    # above). Quoting them verbatim inside skeleton_gen's own wrapping
    # comment without escaping "*/" closes that comment early and corrupts
    # every line after it into stray C tokens -- catch it with a real
    # compiler, not just a substring check.
    import shutil
    cc = shutil.which("cc") or shutil.which("gcc")
    if cc is None:
        import pytest
        pytest.skip("no C compiler available")
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    compile_proc = subprocess.run(
        [cc, "-std=c11", "-Wall", "-Wextra", "-I", str(project / "csrc"), "-fsyntax-only",
         str(project / "csrc" / "chronicle.c")],
        capture_output=True, text=True,
    )
    assert compile_proc.returncode == 0, compile_proc.stdout + compile_proc.stderr
    assert compile_proc.stderr == ""


def test_modules_flag_restricts_target_set(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    proc = _run(project, queue, "--modules", "csrc/chronicle.c")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (project / "csrc" / "chronicle.c").exists()


def test_report_mode_writes_nothing_at_all(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    header_before = (project / "csrc" / "ouroboros_sim.h").read_text()
    proc = _run(project, queue, "--report")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (project / "csrc" / "chronicle.c").exists()
    assert (project / "csrc" / "ouroboros_sim.h").read_text() == header_before


def test_discover_modules_ignores_files_that_already_exist(tmp_path):
    project = _init_project(tmp_path)
    queue = _init_queue(tmp_path)
    # om_chronicle_dead's snippet_file is csrc/chronicle.c (missing) -- but also
    # exercise that an existing file (csrc/other.c) is never treated as a target.
    (queue / "999-other-owner.md").write_text(
        _card_text(snippet_file="csrc/other.c", snippet_symbol="om_chronicle_dead"))
    proc = _run(project, queue, "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert not any(m["module_file"] == "csrc/other.c" for m in data)
