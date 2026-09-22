"""PX-14: tests for scripts/specfactory/parent_patch_fence.py. A synthetic
two-card git repo (never csrc/, never a real agora queue) proves the fence's
two checks distinguish a clean single-function patch from two different
violation shapes:

  (d) a patch that edits ANOTHER card's function under this card's name --
      caught by check 1 (function ownership) alone.
  (a493cfd's actual shape) a patch confined to the function it legitimately
      owns, that ALSO does another card's job inside that function's body --
      invisible to check 1, caught only by check 2 (scope capture: the other
      card's test goes red-before/green-after).

`om_step_b` is written as a stub that sets nothing (mirrors 204b1's function
being unbuilt when a493cfd landed), so `bridge.run_world()`'s own call to it
never overwrites whatever `om_step_a` set -- the same reason 204b1's field
stayed set after 204a1's stray write in the real incident.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "specfactory"))
import parent_patch_fence as ppf  # noqa: E402

PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # see test_suite_regression.py: avoid stale-.pyc false negatives

_PADDING = "".join(f"/* padding line {i} */\n" for i in range(1, 9))

RESOLVE_C_BASE = (
    "/* synthetic fixture, not real csrc */\n"
    "\n"
    "int om_step_a(int w) {\n"
    "    w.a_field = 0;\n"
    "}\n"
    "\n"
    + _PADDING +
    "\n"
    "int om_step_b(int w) {\n"
    "    /* STUB: unbuilt, card B's own job */\n"
    "}\n"
)
# Wide gap between the two functions so git diff's default 3-line context
# around a single-line edit inside one function never reaches the other --
# real replay diffs (a493cfd etc.) hit this naturally in a 600+-line file;
# this fixture is tiny, so the gap has to be built in deliberately.

BRIDGE_PY = (
    "import re\n"
    "from pathlib import Path\n"
    "\n"
    "_SRC = Path(__file__).parent / 'resolve.c'\n"
    "\n"
    "\n"
    "def _body(name):\n"
    "    text = _SRC.read_text()\n"
    "    m = re.search(re.escape(name) + r'\\([^)]*\\)\\s*\\{(.*?)\\n\\}', text, re.S)\n"
    "    return m.group(1) if m else ''\n"
    "\n"
    "\n"
    "class World:\n"
    "    def __init__(self):\n"
    "        self.a_field = 0\n"
    "        self.b_field = 0\n"
    "\n"
    "\n"
    "def _apply(w, name):\n"
    "    for stmt in _body(name).splitlines():\n"
    "        stmt = stmt.strip()\n"
    "        if stmt.startswith('w.a_field'):\n"
    "            w.a_field = int(stmt.split('=')[1].strip().rstrip(';'))\n"
    "        elif stmt.startswith('w.b_field'):\n"
    "            w.b_field = int(stmt.split('=')[1].strip().rstrip(';'))\n"
    "\n"
    "\n"
    "def run_world():\n"
    "    w = World()\n"
    "    _apply(w, 'om_step_a')\n"
    "    _apply(w, 'om_step_b')\n"
    "    return w\n"
)

TEST_CARD_A = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, str(Path(__file__).resolve().parents[2]))\n"
    "import bridge\n"
    "\n"
    "def test_a():\n"
    "    assert bridge.run_world().a_field == 1\n"
)

TEST_CARD_B = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, str(Path(__file__).resolve().parents[2]))\n"
    "import bridge\n"
    "\n"
    "def test_b():\n"
    "    assert bridge.run_world().b_field == 10\n"
)

CARD_A_MD = (
    "---\n"
    "project: dummy\n"
    'goal: "card A owns om_step_a"\n'
    "acceptance:\n"
    "  - \"{python} -m pytest -q -p no:cacheprovider tests/synth/test_cardA.py::test_a\"\n"
    "allowed_files: \"resolve.c\"\n"
    "snippet_file: resolve.c\n"
    'snippet_symbol: "om_step_a"\n'
    "---\n"
    "\n"
    "synthetic card A\n"
)

CARD_B_MD = (
    "---\n"
    "project: dummy\n"
    'goal: "card B owns om_step_b"\n'
    "acceptance:\n"
    "  - \"{python} -m pytest -q -p no:cacheprovider tests/synth/test_cardB.py::test_b\"\n"
    "allowed_files: \"resolve.c\"\n"
    "snippet_file: resolve.c\n"
    'snippet_symbol: "om_step_b"\n'
    "---\n"
    "\n"
    "synthetic card B\n"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _make_repo_and_queue(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "tests" / "synth").mkdir(parents=True)
    (repo / "resolve.c").write_text(RESOLVE_C_BASE)
    (repo / "bridge.py").write_text(BRIDGE_PY)
    (repo / "tests" / "synth" / "test_cardA.py").write_text(TEST_CARD_A)
    (repo / "tests" / "synth" / "test_cardB.py").write_text(TEST_CARD_B)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "px14@test")
    _git(repo, "config", "user.name", "px14")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")

    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "cardA.md").write_text(CARD_A_MD.format(python=PYTHON))
    (queue / "cardB.md").write_text(CARD_B_MD.format(python=PYTHON))
    return repo, queue


def _diff_from_edit(repo: Path, new_text: str) -> str:
    """Default 3-line context, same as every real replay diff in the write-up."""
    orig = (repo / "resolve.c").read_text()
    (repo / "resolve.c").write_text(new_text)
    diff = subprocess.run(["git", "diff"], cwd=repo, capture_output=True, text=True).stdout
    (repo / "resolve.c").write_text(orig)
    return diff


CLEAN_A_ONLY = (
    "/* synthetic fixture, not real csrc */\n"
    "\n"
    "int om_step_a(int w) {\n"
    "    w.a_field = 1;\n"
    "}\n"
    "\n"
    + _PADDING +
    "\n"
    "int om_step_b(int w) {\n"
    "    /* STUB: unbuilt, card B's own job */\n"
    "}\n"
)

VIOLATES_CHECK1_EDITS_OTHER_FUNC = (
    "/* synthetic fixture, not real csrc */\n"
    "\n"
    "int om_step_a(int w) {\n"
    "    w.a_field = 0;\n"
    "}\n"
    "\n"
    + _PADDING +
    "\n"
    "int om_step_b(int w) {\n"
    "    w.b_field = 10;\n"
    "}\n"
)

STEALS_CARD_B_JOB_INSIDE_OWN_FUNCTION = (
    "/* synthetic fixture, not real csrc */\n"
    "\n"
    "int om_step_a(int w) {\n"
    "    w.a_field = 1;\n"
    "    w.b_field = 10;\n"
    "}\n"
    "\n"
    + _PADDING +
    "\n"
    "int om_step_b(int w) {\n"
    "    /* STUB: unbuilt, card B's own job */\n"
    "}\n"
)


# ---------------------------------------------------------------- diff parsing / function spans --

def test_parse_diff_hunks_reads_new_side_range():
    diff = (
        "diff --git a/resolve.c b/resolve.c\n"
        "index 111..222 100644\n"
        "--- a/resolve.c\n"
        "+++ b/resolve.c\n"
        "@@ -2,3 +2,4 @@ int om_step_a(int w) {\n"
        " unchanged\n"
        "+added\n"
    )
    hunks = ppf.parse_diff_hunks(diff)
    assert len(hunks) == 1
    assert hunks[0] == ppf.Hunk(file="resolve.c", new_start=2, new_count=4)


def test_parse_diff_hunks_skips_dev_null_target():
    diff = "diff --git a/x.c b/x.c\n--- a/x.c\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-a\n-b\n"
    assert ppf.parse_diff_hunks(diff) == []


def test_functions_in_file_finds_both_synthetic_functions():
    funcs = ppf.functions_in_file(RESOLVE_C_BASE)
    names = {f[0] for f in funcs}
    assert names == {"om_step_a", "om_step_b"}


# ---------------------------------------------------------------- touched_functions --

def test_touched_functions_maps_hunk_to_enclosing_function(tmp_path):
    repo, _ = _make_repo_and_queue(tmp_path)
    diff = _diff_from_edit(repo, CLEAN_A_ONLY)
    ppf.apply_diff(repo, diff)
    touched = ppf.touched_functions(repo, diff)
    assert touched == {"resolve.c": {"om_step_a"}}


def test_touched_functions_empty_when_hunk_is_between_functions(tmp_path):
    """A hunk landing in the file-scope gap between two functions (an
    #include, a comment) touches no function -- replay case (c)."""
    repo, _ = _make_repo_and_queue(tmp_path)
    new_text = RESOLVE_C_BASE.replace(
        "/* padding line 4 */\n", "/* padding line 4 */\n/* NEW file-scope comment */\n",
    )
    assert new_text != RESOLVE_C_BASE
    diff = _diff_from_edit(repo, new_text)
    ppf.apply_diff(repo, diff)
    touched = ppf.touched_functions(repo, diff)
    assert touched.get("resolve.c", set()) == set()


# ---------------------------------------------------------------- run_fence: check 1 --

def test_fence_negative_control_check1_catches_edit_to_other_cards_function(tmp_path):
    """Brief's replay case (d): a diff under card A's name that edits card
    B's function (om_step_b) must be rejected by function ownership alone."""
    repo, queue = _make_repo_and_queue(tmp_path)
    diff = _diff_from_edit(repo, VIOLATES_CHECK1_EDITS_OTHER_FUNC)
    report = ppf.run_fence("cardA", diff, queue, repo, python_exe=PYTHON, project=None)
    assert report.ownership_pass is False
    assert report.accept is False
    violations = [f for f in report.ownership if f.status == "violation"]
    assert len(violations) == 1
    assert violations[0].function == "om_step_b"
    assert violations[0].owning_card == "cardB"


def test_fence_accepts_clean_diff_confined_to_own_function(tmp_path):
    repo, queue = _make_repo_and_queue(tmp_path)
    diff = _diff_from_edit(repo, CLEAN_A_ONLY)
    report = ppf.run_fence("cardA", diff, queue, repo, python_exe=PYTHON, project=None)
    assert report.ownership_pass is True
    assert report.scope.accept is True
    assert report.accept is True
    assert report.scope.went_green == []


# ---------------------------------------------------------------- run_fence: check 2 (the real shape) --

def test_fence_positive_control_check2_catches_scope_capture_check1_misses(tmp_path):
    """The actual a493cfd shape: the diff touches ONLY om_step_a (card A's
    own function -- check 1 alone would accept this), but also implements
    card B's job inside it, so card B's test goes red-before/green-after."""
    repo, queue = _make_repo_and_queue(tmp_path)
    diff = _diff_from_edit(repo, STEALS_CARD_B_JOB_INSIDE_OWN_FUNCTION)
    report = ppf.run_fence("cardA", diff, queue, repo, python_exe=PYTHON, project=None)

    assert report.ownership_pass is True  # check 1 alone: blind, exactly as the brief predicts
    assert [f.status for f in report.ownership] == ["own"]

    assert report.scope.accept is False  # check 2: catches it
    assert report.scope.went_green == ["tests/synth/test_cardB.py::test_b"]
    assert report.scope.captured_cards == {"cardB": ["tests/synth/test_cardB.py::test_b"]}

    assert report.accept is False  # fence overall: rejects


def test_fence_scope_capture_covers_only_other_cards_not_self(tmp_path):
    """Card A's own test going green from card A's own diff is the whole
    point of the patch -- must never be flagged as scope capture."""
    repo, queue = _make_repo_and_queue(tmp_path)
    diff = _diff_from_edit(repo, CLEAN_A_ONLY)
    report = ppf.run_fence("cardA", diff, queue, repo, python_exe=PYTHON, project=None)
    assert "cardA" not in report.scope.captured_cards
    assert report.scope.tests_run == 1  # only card B's one test is "another card"
    assert report.scope.cards_covered == 1
