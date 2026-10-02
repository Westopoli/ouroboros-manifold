"""Tests for the pending list (Architect ruling A135, rulings-2 Addendum 46):
tests/csim/parity/pending.txt names test ids that are red until a later wave;
the hook in tests/csim/parity/conftest.py (pytest_collection_modifyitems)
marks each listed id pytest.mark.xfail(strict=True, reason="PP pending: code
not built yet"). Proves the PP-parity pending-list mechanism (A135); no
S-### / R-###-## story applies, the list is merge-gate infrastructure
(scripts/specfactory/suite_regression.py counts xfail separately).

The hook is exercised in a self-contained tmp tree: the real conftest.py is
COPIED next to a throwaway pending.txt and throwaway tests, and pytest runs
there in a subprocess (own rootdir, no ancestor conftest, so nothing here
touches the real suite). pending.txt is read from the directory of the
conftest that holds the hook.
"""
import pathlib
import subprocess
import sys
import textwrap

import pytest

PARITY_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = PARITY_DIR.parents[2]
REAL_PENDING = PARITY_DIR / "pending.txt"
REAL_CONFTEST = PARITY_DIR / "conftest.py"
REASON = "PP pending: code not built yet"

FIXTURE_TESTS = textwrap.dedent('''
    def test_fails():
        assert False, "red until built"

    def test_passes():
        assert True

    def test_other_fails():
        assert False, "a real failure the list must never hide"
''')


def parse_pending(text):
    """The list format: one id per line, '#' comment lines and blank lines
    ignored. Returns the ids in file order."""
    ids = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ids.append(line)
    return ids


def run_fixture(tmp_path, pending_text, tests=FIXTURE_TESTS):
    """Build the tmp tree (conftest copy + pending.txt + sub/test_fx.py) and
    run pytest on it. Returns (returncode, stdout+stderr)."""
    assert REAL_CONFTEST.is_file(), (
        "tests/csim/parity/conftest.py with the pending-list hook is not built yet")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "conftest.py").write_text(REAL_CONFTEST.read_text())
    (tmp_path / "pending.txt").write_text(pending_text)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "test_fx.py").write_text(tests)
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rA",
         "--rootdir", str(tmp_path), str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def outcome_lines(out, word):
    return [ln for ln in out.splitlines() if ln.startswith(word + " ")]


def has(out, word, nodeid):
    return any(ln.split()[1] == nodeid for ln in outcome_lines(out, word)
               if len(ln.split()) > 1)


ID_FAILS = "sub/test_fx.py::test_fails"
ID_PASSES = "sub/test_fx.py::test_passes"
ID_OTHER = "sub/test_fx.py::test_other_fails"


def test_pending_listed_failing_test_is_xfailed(tmp_path):
    """A135: a listed failing test is reported xfailed, with the PP reason."""
    tests = FIXTURE_TESTS.replace("def test_other_fails", "def _helper_not_a_test")
    code, out = run_fixture(tmp_path, ID_FAILS + "\n", tests)
    assert has(out, "XFAIL", ID_FAILS), out
    assert REASON in "\n".join(outcome_lines(out, "XFAIL")), out
    assert has(out, "PASSED", ID_PASSES), out
    assert not outcome_lines(out, "FAILED"), out
    assert code == 0, out


def test_pending_listed_passing_test_fails_strict(tmp_path):
    """A135: a listed PASSING test is reported failed (strict XPASS), so its
    line must be removed when the code lands."""
    code, out = run_fixture(tmp_path, ID_PASSES + "\n")
    assert has(out, "FAILED", ID_PASSES), out
    assert "XPASS(strict)" in out, out
    assert code != 0, out


def test_pending_unlisted_failing_test_still_fails(tmp_path):
    """Positive control for the hook: it never hides a real failure. A
    failing test absent from the list stays FAILED even while a sibling
    failing test is listed (and xfailed)."""
    code, out = run_fixture(tmp_path, ID_FAILS + "\n")
    assert has(out, "XFAIL", ID_FAILS), out
    assert has(out, "FAILED", ID_OTHER), out
    assert code != 0, out


def test_pending_empty_list_hides_nothing(tmp_path):
    """Positive control: with nothing listed both failing tests FAIL and
    nothing is xfailed (the hook is inert on an empty list)."""
    code, out = run_fixture(tmp_path, "# nothing pending\n\n")
    assert has(out, "FAILED", ID_FAILS), out
    assert has(out, "FAILED", ID_OTHER), out
    assert not outcome_lines(out, "XFAIL"), out
    assert has(out, "PASSED", ID_PASSES), out
    assert code != 0, out


def test_pending_comment_and_blank_lines_are_ignored(tmp_path):
    """A commented-out id does nothing, blank and whitespace-only lines are
    ignored, and the real id between them still applies."""
    text = "\n".join([
        "# a header comment",
        "",
        "# " + ID_PASSES,
        "   ",
        ID_FAILS,
        "",
        "# " + ID_OTHER,
        "",
    ])
    code, out = run_fixture(tmp_path, text)
    assert has(out, "XFAIL", ID_FAILS), out
    assert has(out, "PASSED", ID_PASSES), out      # its commented line was ignored
    assert has(out, "FAILED", ID_OTHER), out       # its commented line was ignored
    assert not has(out, "XFAIL", ID_PASSES) and not has(out, "XFAIL", ID_OTHER), out


def test_pending_stale_id_is_an_error_naming_it(tmp_path):
    """Stale-line guard: a listed id that no longer exists is an error that
    names the id (a removed or renamed test must not leave a dead line)."""
    gone = "sub/test_fx.py::test_removed_long_ago"
    code, out = run_fixture(tmp_path, ID_PASSES + "\n" + gone + "\n")
    assert code != 0, out
    assert "test_removed_long_ago" in out, out
    assert "PASSED" not in "\n".join(ln for ln in out.splitlines()
                                     if ln.startswith("PASSED")), (
        "a stale line must stop the run, not run the suite anyway: " + out)


def test_pending_duplicate_line_is_an_error(tmp_path):
    """A duplicate line is an error that names the id. Uses a passing id so a
    missing hook (no error raised, run is green) cannot pass this test."""
    code, out = run_fixture(tmp_path, ID_PASSES + "\n# again below\n" + ID_PASSES + "\n")
    assert code != 0, out
    assert "test_passes" in out, out
    assert not outcome_lines(out, "PASSED"), (
        "a duplicate line must stop the run, not run the suite anyway: " + out)


def test_real_pending_file_exists_and_ids_are_well_formed():
    """The real list exists, has no duplicate id, and every id has the
    `path::name` shape relative to the repo root (initially empty, so green:
    a placeholder keeping the list honest)."""
    assert REAL_PENDING.is_file(), "tests/csim/parity/pending.txt missing"
    ids = parse_pending(REAL_PENDING.read_text())
    assert len(ids) == len(set(ids)), "duplicate ids: %r" % sorted(
        i for i in set(ids) if ids.count(i) > 1)
    for i in ids:
        assert "::" in i and not i.startswith("/"), "malformed id %r" % i
        assert (REPO_ROOT / i.split("::", 1)[0]).is_file(), "no such file for %r" % i


def test_real_pending_ids_all_exist_in_collection():
    """Every id in the real pending.txt is a test pytest actually collects
    (no stale line). Empty list: nothing to check, green now."""
    ids = parse_pending(REAL_PENDING.read_text())
    if not ids:
        return
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
         "--collect-only", "-q", "tests"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)
    collected = {ln.strip() for ln in r.stdout.splitlines() if "::" in ln}
    missing = [i for i in ids if i not in collected]
    assert not missing, "pending ids not collected (stale?): %r" % missing


def test_parse_pending_positive_control():
    """The parser used by the real-file tests: comments/blank skipped, ids kept."""
    assert parse_pending("# c\n\n  \na.py::t\n# b.py::t\nc.py::u\n") == ["a.py::t", "c.py::u"]
