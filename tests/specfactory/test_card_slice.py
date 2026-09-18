# spec: docs/northstar/spec_factory.md pipeline (pre-queue mechanical gate)
"""Tests for scripts/specfactory/card_slice.py.

Builds a throwaway synthetic project per test (a small synthetic
ouroboros_sim.h, csrc/*.c, tests/csim/*.py) so this suite never depends on
the real repo's header shape -- card_slice applies to some card's project,
and a synthetic one proves the extraction mechanism without coupling to a
real header.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CARD_SLICE = REPO / "scripts" / "specfactory" / "card_slice.py"

HEADER = '''/* synthetic header */
typedef struct om_world om_world;

/* ---- feature switches (fixture) ----
 * Mirrors the real ABI's feature-gate comment. */
typedef enum {
    OM_FEAT_EVENTS   = 0,
    OM_FEAT_FACTIONS = 1
} om_feature;
void om_world_set_feature(om_world *w, om_feature f, int on);

/* ---- widget diagnostics ---- */
typedef struct om_widget {
    uint32_t idx;
    double   value;
} om_widget;
uint32_t om_widget_list(const om_world *w, int32_t owner, om_widget *out, uint32_t max);

#define OM_MAX_WIDGETS 64

int32_t om_widget_owner(const om_world *w, uint32_t idx);            /* trailing comment stays attached */
void    om_unrelated_untouched(om_world *w, int x);
'''

CONFTEST = '''
def isolate(lib, w):
    lib.om_world_set_feature(w, 1, 1)


def read_widgets(lib, w, owner):
    buf = [0] * 8
    return lib.om_widget_list(w, owner, buf, 8)
'''

TEST_FILE = '''
from conftest import isolate, read_widgets


def test_R_900_01_widgets(lib, world_factory):
    w = world_factory()
    isolate(lib, w)
    read_widgets(lib, w, 0)
'''

AGENT_C = '''#include "ouroboros_sim.h"

uint32_t om_widget_list(const om_world *w, int32_t owner, om_widget *out, uint32_t max) {
    (void)w; (void)owner; (void)out; (void)max;
    return 0;
}
'''


def _init_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "csrc" / "agent.c").write_text(AGENT_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "tests" / "csim" / "test_widgets.py").write_text(TEST_FILE)
    return project


def _write_card(tmp_path: Path, project: Path, *, snippet_symbol="om_widget_list",
                 brief="Reads widgets via om_widget_list. Uses OM_MAX_WIDGETS as the cap.",
                 name="card.md") -> Path:
    card = tmp_path / name
    card.write_text(
        "---\n"
        f"project: {project}\n"
        "acceptance:\n"
        f'  - "{sys.executable} -m pytest -q tests/csim/test_widgets.py::test_R_900_01_widgets"\n'
        'allowed_files: "csrc/agent.c"\n'
        "snippet_file: csrc/agent.c\n"
        f'snippet_symbol: "{snippet_symbol}"\n'
        "header_file: csrc/ouroboros_sim.h\n"
        "expected_lines: 40\n"
        "---\n\n"
        "## Brief for DeepSeek\n"
        f"{brief}\n"
    )
    return card


def _run(card: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CARD_SLICE), str(card), *extra],
        capture_output=True, text=True,
    )


def _fence_body(stdout: str) -> str:
    m = re.search(r"```c\n(.*?)```", stdout, re.S)
    assert m, stdout
    return m.group(1)


def test_slice_includes_acceptance_and_snippet_and_brief_identifiers(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    body = _fence_body(proc.stdout)

    # om_widget_list: reached by acceptance test (via read_widgets) and by snippet_symbol
    assert "uint32_t om_widget_list(const om_world *w, int32_t owner, om_widget *out, uint32_t max);" in body
    # om_widget struct: closure from om_widget_list's parameter list
    assert "typedef struct om_widget {" in body
    # om_world opaque typedef: closure from every prototype's parameter list
    assert "typedef struct om_world om_world;" in body
    # om_world_set_feature + om_feature: reached via isolate() -> lib.om_world_set_feature
    assert "void om_world_set_feature(om_world *w, om_feature f, int on);" in body
    assert "typedef enum {" in body and "OM_FEAT_FACTIONS = 1" in body
    # OM_MAX_WIDGETS: mentioned only in the brief text
    assert "#define OM_MAX_WIDGETS 64" in body
    # never referenced anywhere: must not appear
    assert "om_unrelated_untouched" not in body


def test_trailing_same_line_comment_stays_attached_verbatim(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, snippet_symbol="om_widget_list, om_widget_owner")
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    body = _fence_body(proc.stdout)
    assert "int32_t om_widget_owner(const om_world *w, uint32_t idx);            /* trailing comment stays attached */" in body


def test_banner_is_attached_when_directly_adjacent(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project, snippet_symbol="om_widget_list",
                        brief="Uses om_widget_list and switches OM_FEAT_FACTIONS on.")
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    body = _fence_body(proc.stdout)
    assert "/* ---- feature switches (fixture) ----" in body


def test_every_nonblank_line_is_verbatim_from_header(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    body = _fence_body(proc.stdout)
    header_lines = {line.strip() for line in HEADER.splitlines()}
    for line in body.splitlines():
        if line.strip():
            assert line.strip() in header_lines, f"non-verbatim line: {line!r}"


def test_write_appends_after_brief_when_no_existing_slice(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    proc = _run(card, "--write")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = card.read_text()
    assert "## Header slice" in text
    assert text.index("## Brief for DeepSeek") < text.index("## Header slice")
    assert "```c" in text


def test_write_replaces_existing_slice(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    text = card.read_text() + "\n## Header slice\n\n```c\nSTALE CONTENT\n```\n"
    card.write_text(text)
    proc = _run(card, "--write")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    new_text = card.read_text()
    assert "STALE CONTENT" not in new_text
    assert new_text.count("## Header slice") == 1
    assert "om_widget_list" in new_text


def test_exit_2_on_missing_card(tmp_path):
    proc = _run(tmp_path / "no_such_card.md")
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_exit_2_on_missing_header_file(tmp_path):
    project = _init_project(tmp_path)
    (project / "csrc" / "ouroboros_sim.h").unlink()
    card = _write_card(tmp_path, project)
    proc = _run(card)
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_exit_2_on_project_not_a_directory(tmp_path):
    project = _init_project(tmp_path)
    card = _write_card(tmp_path, project)
    text = card.read_text().replace(f"project: {project}", f"project: {tmp_path / 'nope'}")
    card.write_text(text)
    proc = _run(card)
    assert proc.returncode == 2, proc.stdout + proc.stderr
