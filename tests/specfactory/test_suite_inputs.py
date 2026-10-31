# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md section 4 (HARNESS-suite-inputs-trim) and section 8 F9; docs/stories/H-019.md "Rulings 2026-10-31"
# Rule pins: none (harness piece, layered-gate spec section 4)
"""H-019 suite-inputs-trim: scripts/specfactory/suite_inputs.toml declares only the inputs a suite really reads.

Story goal (docs/stories/H-019.md, ruling 1): the gate's csim baseline cache survives docs-only commits on main.
Measured on the first csim-running gate after landing (a sim or contract flag, or --tier slow) whose base sits past
at least one docs-only main commit since the previous csim baseline: it prints `regression_csim OK inputs unchanged
<hash>` (or `baseline: cached` for csim). That measurement is the Dispatcher's, not a test here; F12's wall time of
tests/specfactory is a builder report line (ruling 4), not a test.

Spec text (section 4), tests (1) to (4), word for word:
  (1) no `paths` entry of the `tests/csim`, `tests/qa/t1` or `tests/transport` tables equals `docs/northstar`,
  `scripts/specfactory`, `scripts/skilllab`, `scripts/library`, `scripts/qa` or `simulation` or any directory under
  them (a path is a directory when `git cat-file -t HEAD:<path>` says `tree`).
  (2) every declared path exists at `HEAD` (`git rev-parse HEAD:<path>` succeeds), so a renamed input is caught at
  the pre-gate;
  (3) positive control: a fixture strace log that opens `docs/northstar/spec_factory/mvp_features.toml` is covered
  by the fixture table that names that file (`undeclared_opens` returns `[]`) and a fixture table that names only
  `docs/northstar/other.md` leaves it undeclared (returns the one path);
  (4) control that the trim bites: `_input_hash` of a fixture repo over the trimmed table is unchanged by a commit
  that adds a file under `docs/northstar/plans/` and changed by a commit that edits
  `docs/northstar/spec_factory/mvp_features.toml`.
Spec text (section 8 F9), tests (5) and (6):
  (5) every literal repo path in `tests/<suite>/**/*.py` matching `(docs|scripts|simulation)/[A-Za-z0-9_./-]+` falls
  under a declared path.
  (6) positive control: a fixture table at directory grain covers a new file under that directory.

Rulings of 2026-10-31 that shape the tests (they override the spec paragraph where they differ):
  Q2 DIR_GRAIN_ALLOWED below is an empty tuple with the two guard assertions of DEC-suiteinputs-dirgrain-2026-10-29
  (no root in it, nothing under docs/northstar/plans). Test (1) is strict except for its entries. The builder never
  edits it: the ruler's admissions are added by the test writer, with the ruling in the commit body.
  Q3 test (5) counts a literal only when it names a tracked file at HEAD; a literal naming a directory or an untracked
  name is skipped. Test (6)'s fixture is a directory-grain entry covering a new file under it.

Picked details (test-writer choices where the spec is silent; none is a threshold):
  - test (5) reads the string constants of each file with `ast` (docstrings left out: they are prose, never opened),
    runs the regex over each constant, strips trailing `. , ; : ) ]`, and checks the suites tests/csim, tests/qa/t1
    and tests/transport (tests/specfactory is exempt from the trim);
  - test (1) and (4) read the three trimmed tables; test (2) reads all four tables;
  - a declared path covers a literal when it equals it or is a directory prefix of it (the rule of undeclared_opens).
"""
import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SPECFACTORY = REPO / "scripts" / "specfactory"
TOML_PATH = SPECFACTORY / "suite_inputs.toml"
sys.path.insert(0, str(SPECFACTORY))

import merge_gate_support as mgs  # noqa: E402

GRAIN_ROOTS = ("docs/northstar", "scripts/specfactory", "scripts/skilllab", "scripts/library", "scripts/qa",
               "simulation")
PLANS = "docs/northstar/plans"
# A directory the suite opens as a directory from a non-Godot process stays at directory grain (spec F9). An entry is
# added only by the test writer on the ruler's ruling (DEC-suiteinputs-dirgrain-2026-10-29), never by the builder.
DIR_GRAIN_ALLOWED = ()

TRIMMED_SUITES = ("tests/csim", "tests/qa/t1", "tests/transport")
ALL_SUITES = TRIMMED_SUITES + ("tests/specfactory",)
MVP = "docs/northstar/spec_factory/mvp_features.toml"
LITERAL_RE = re.compile(r"(?:docs|scripts|simulation)/[A-Za-z0-9_./-]+")


# ------------------------------------------------------------------ helpers

def _git(repo, *args, check=True):
    return subprocess.run(["git", *args], cwd=repo, check=check, capture_output=True, text=True)


def _table(suite):
    return list(tomllib.loads(TOML_PATH.read_text())["suites"][suite]["paths"])


def _is_tree(repo, path):
    r = _git(repo, "cat-file", "-t", f"HEAD:{path}", check=False)
    return r.returncode == 0 and r.stdout.strip() == "tree"


def _under_or_equal(path, root):
    return path == root or path.startswith(root + "/")


def _guard_violations(allowed):
    """The two guard assertions on DIR_GRAIN_ALLOWED: no root, nothing under docs/northstar/plans."""
    return [a for a in allowed
            if a.rstrip("/") in GRAIN_ROOTS or _under_or_equal(a.rstrip("/"), PLANS)]


def _dir_grain_offenders(entries, repo, allowed):
    """Entries that equal a file-grain root or lie under one, are trees at HEAD of `repo`, and are not allowed."""
    return [p for p in entries
            if any(_under_or_equal(p.rstrip("/"), r) for r in GRAIN_ROOTS)
            and _is_tree(repo, p.rstrip("/")) and p not in allowed]


def _missing_at_head(entries, repo):
    return [p for p in entries if _git(repo, "rev-parse", f"HEAD:{p}", check=False).returncode != 0]


def _string_constants(source):
    """String constants of a python source outside docstrings (the picked detail of test (5))."""
    tree = ast.parse(source)
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                doc_nodes.add(id(body[0].value))
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes]


def _literal_paths(source):
    out = []
    for s in _string_constants(source):
        for m in LITERAL_RE.finditer(s):
            out.append(m.group(0).rstrip(".,;:)]"))
    return out


def _tracked_files(repo):
    return set(_git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.split("\n")) - {""}


def _covered(path, declared):
    return any(path == d.rstrip("/") or path.startswith(d.rstrip("/") + "/") for d in declared)


def _uncovered_literals(sources, tracked, declared):
    """[(literal, python file)] for each literal naming a tracked file at HEAD that no declared path covers.
    A directory literal and an untracked name are skipped (ruling Q3)."""
    out = []
    for name, text in sources.items():
        try:
            lits = _literal_paths(text)
        except SyntaxError:
            continue
        for lit in lits:
            if lit in tracked and not _covered(lit, declared):
                out.append((lit, name))
    return sorted(set(out))


def _suite_sources(suite):
    return {f.relative_to(REPO).as_posix(): f.read_text(errors="replace") for f in sorted((REPO / suite).rglob("*.py"))}


def _fixture_repo(tmp_path, files):
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "g@t")
    _git(repo, "config", "user.name", "g")
    _commit(repo, "base", files)
    return repo


def _commit(repo, msg, files):
    for rel, text in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _strace(repo, *rels):
    return "".join(f'12345 openat(AT_FDCWD, "{repo}/{rel}", O_RDONLY|O_CLOEXEC) = {3 + i}\n'
                   for i, rel in enumerate(rels))


BASE_FILES = {
    "Makefile": "all:\n",
    MVP: "[default]\n",
    "docs/northstar/other.md": "other\n",
    "docs/northstar/plans/old.md": "old\n",
}


# ------------------------------------------------------------------ (1) no directory at file-grain roots

@pytest.mark.parametrize("suite", TRIMMED_SUITES)
def test_H019_1_no_table_entry_is_a_root_or_a_directory_under_one(suite):
    """H-019 spec section 4 test (1): no entry of the suite's table equals a file-grain root or is a directory
    under one (tree at HEAD), except an entry of DIR_GRAIN_ALLOWED."""
    bad = _dir_grain_offenders(_table(suite), REPO, DIR_GRAIN_ALLOWED)
    assert bad == [], f"{suite}: directory-grain entries under the six roots: {bad}"


def test_H019_1_guard_dir_grain_allowed_holds_no_root_and_nothing_under_plans():
    """H-019 ruling Q2 (DEC-suiteinputs-dirgrain-2026-10-29): the two guard assertions on DIR_GRAIN_ALLOWED."""
    assert isinstance(DIR_GRAIN_ALLOWED, tuple)
    assert [a for a in DIR_GRAIN_ALLOWED if a.rstrip("/") in GRAIN_ROOTS] == [], "DIR_GRAIN_ALLOWED holds a root"
    assert [a for a in DIR_GRAIN_ALLOWED if _under_or_equal(a.rstrip("/"), PLANS)] == [], \
        "DIR_GRAIN_ALLOWED holds a path under docs/northstar/plans"


def test_H019_1_control_detector_flags_planted_directory_and_the_guard_flags_planted_entries(tmp_path):
    """H-019 test (1) positive control (green today): on a fixture repo the detector flags a root, a directory under
    a root and ignores a file, a directory outside the roots and an allowed directory; the guard flags a root and a
    path under docs/northstar/plans and passes a directory strictly under a root."""
    repo = _fixture_repo(tmp_path, {**BASE_FILES, "scripts/specfactory/a.py": "x\n", "simulation/library/m.py": "x\n",
                                    "csrc/c.c": "x\n"})
    entries = ["docs/northstar", "scripts/specfactory", "simulation", "simulation/library", "csrc", "Makefile",
               MVP, "scripts/specfactory/a.py", "docs/northstar/plans"]
    assert _dir_grain_offenders(entries, repo, ()) == [
        "docs/northstar", "scripts/specfactory", "simulation", "simulation/library", "docs/northstar/plans"]
    assert _dir_grain_offenders(entries, repo, ("simulation/library",)) == [
        "docs/northstar", "scripts/specfactory", "simulation", "docs/northstar/plans"]
    assert _guard_violations(("docs/northstar", "scripts/qa/", "simulation")) == [
        "docs/northstar", "scripts/qa/", "simulation"]
    assert _guard_violations(("docs/northstar/plans", "docs/northstar/plans/x")) == [
        "docs/northstar/plans", "docs/northstar/plans/x"]
    assert _guard_violations(("simulation/library", "scripts/specfactory/sub")) == []


# ------------------------------------------------------------------ (2) every declared path exists at HEAD

@pytest.mark.parametrize("suite", ALL_SUITES)
def test_H019_2_every_declared_path_exists_at_head(suite):
    """H-019 spec section 4 test (2): `git rev-parse HEAD:<path>` succeeds for every declared path."""
    missing = _missing_at_head(_table(suite), REPO)
    assert missing == [], f"{suite}: declared paths absent at HEAD: {missing}"


def test_H019_2_control_a_renamed_input_is_reported(tmp_path):
    """H-019 test (2) positive control (green today): a path absent at HEAD of a fixture repo is listed."""
    repo = _fixture_repo(tmp_path, BASE_FILES)
    assert _missing_at_head(["Makefile", MVP, "docs/northstar/renamed.md"], repo) == ["docs/northstar/renamed.md"]
    assert _missing_at_head(["Makefile", MVP], repo) == []


# ------------------------------------------------------------------ (3) undeclared_opens positive control

def test_H019_3_control_a_fixture_open_is_covered_by_the_table_that_names_the_file(tmp_path):
    """H-019 spec section 4 test (3) (green today): undeclared_opens returns [] for a table naming mvp_features.toml
    and exactly the one path for a table naming only docs/northstar/other.md; an empty table returns the path (the
    fixture line is parsed, so the [] is not vacuous)."""
    repo = _fixture_repo(tmp_path, BASE_FILES)
    log = _strace(repo, MVP)
    assert mgs.undeclared_opens(log, repo, []) == [MVP]
    assert mgs.undeclared_opens(log, repo, [MVP, "Makefile"]) == []
    assert mgs.undeclared_opens(log, repo, ["docs/northstar/other.md"]) == [MVP]


# ------------------------------------------------------------------ (4) the trim bites

def _hashes_around_two_commits(tmp_path, paths):
    """(hash at base, hash after a commit adding a file under docs/northstar/plans, hash after a further commit
    editing mvp_features.toml) of `paths` in a fixture repo."""
    repo = _fixture_repo(tmp_path, BASE_FILES)
    h0 = mgs._input_hash(repo, "HEAD", paths)
    _commit(repo, "records: a new plan", {"docs/northstar/plans/new.md": "new\n"})
    h1 = mgs._input_hash(repo, "HEAD", paths)
    _commit(repo, "edit mvp features", {MVP: "[default]\nEVENTS = 1\n"})
    h2 = mgs._input_hash(repo, "HEAD", paths)
    return h0, h1, h2


def test_H019_4_control_a_file_grain_table_ignores_plans_and_sees_the_edit_while_directory_grain_does_not(tmp_path):
    """H-019 spec section 4 test (4) mechanism (green today): over a trimmed fixture table [mvp_features.toml,
    Makefile] _input_hash is unchanged by a commit adding a file under docs/northstar/plans/ and changed by a commit
    editing mvp_features.toml; with the directory-grain table [docs/northstar, Makefile] the first commit does change
    the hash (so the assertion can fail)."""
    h0, h1, h2 = _hashes_around_two_commits(tmp_path / "trim", [MVP, "Makefile"])
    assert h1 == h0
    assert h2 != h1
    d0, d1, _d2 = _hashes_around_two_commits(tmp_path / "dir", ["docs/northstar", "Makefile"])
    assert d1 != d0


@pytest.mark.parametrize("suite", TRIMMED_SUITES)
def test_H019_4_a_plans_commit_leaves_the_suite_input_hash_unchanged(tmp_path, suite):
    """H-019 spec section 4 test (4), real tables: a commit adding a file under docs/northstar/plans/ does not move
    the suite's input hash (the goal: a docs-only commit leaves the csim baseline cache valid), and a commit editing
    a file the table names as a file moves it."""
    paths = _table(suite)
    h0, h1, h2 = _hashes_around_two_commits(tmp_path, paths)
    assert h1 == h0, (f"{suite}: a new file under docs/northstar/plans moved the input hash; entries that cover it: "
                      f"{[p for p in paths if p in ('docs', 'docs/northstar')]}")
    if MVP in paths:
        assert h2 != h1, f"{suite}: editing {MVP} did not move the input hash"


def test_H019_4_csim_names_mvp_features_toml_as_a_file():
    """H-019 spec section 4 test (4): tests/csim/conftest.py opens docs/northstar/spec_factory/mvp_features.toml
    (MVP_FEATURES_PATH), so the trimmed csim table names that file and not its directory."""
    paths = _table("tests/csim")
    assert MVP in paths, "tests/csim table does not name docs/northstar/spec_factory/mvp_features.toml"
    assert "docs/northstar" not in paths


# ------------------------------------------------------------------ (5) literal paths fall under a declared path

@pytest.mark.parametrize("suite", TRIMMED_SUITES)
def test_H019_5_every_literal_tracked_file_in_the_suite_sources_falls_under_a_declared_path(suite):
    """H-019 spec section 8 F9 test (5), ruling Q3: each literal in tests/<suite>/**/*.py matching
    (docs|scripts|simulation)/[A-Za-z0-9_./-]+ that names a tracked file at HEAD equals a declared path of the
    suite's table or lies under a declared directory; directory and untracked literals are skipped."""
    bad = _uncovered_literals(_suite_sources(suite), _tracked_files(REPO), _table(suite))
    assert bad == [], f"{suite}: literal tracked files not under a declared path: {bad}"


def test_H019_5_control_the_scan_reads_real_suite_sources():
    """H-019 test (5) non-vacuity (green today): the scan of the real suite sources finds at least one literal that
    names a tracked file, so an empty `bad` list above is not an empty scan."""
    tracked = _tracked_files(REPO)
    found = [lit for suite in TRIMMED_SUITES for text in _suite_sources(suite).values()
             for lit in _literal_paths(text) if lit in tracked]
    assert found, "no literal tracked file found in tests/csim, tests/qa/t1 or tests/transport"


def test_H019_5_control_the_literal_detector_extracts_flags_and_skips(tmp_path):
    """H-019 test (5) positive control (green today): the extraction finds a planted literal in a fixture source
    (not in a docstring, trailing punctuation stripped); a tracked file literal no declared path covers is flagged;
    it is not flagged when the table names the file or a directory above it; a directory literal and an untracked
    name are skipped."""
    repo = _fixture_repo(tmp_path, {**BASE_FILES, "scripts/qa/run.py": "x\n"})
    tracked = _tracked_files(repo)
    src = ('"""Prose: docs/northstar/other.md and scripts/qa/run.py live here."""\n'
           'A = "scripts/qa/run.py"\n'
           'B = "see docs/northstar/other.md."\n'
           'C = "docs/northstar/plans"\n'          # a directory
           'D = "docs/northstar/untracked.md"\n'   # untracked
           'E = f"scripts/qa/{name}.py"\n')        # an f-string stem
    assert _literal_paths(src) == ["scripts/qa/run.py", "docs/northstar/other.md", "docs/northstar/plans",
                                   "docs/northstar/untracked.md", "scripts/qa/"]
    srcs = {"tests/x/a.py": src}
    assert _uncovered_literals(srcs, tracked, ["Makefile"]) == [
        ("docs/northstar/other.md", "tests/x/a.py"), ("scripts/qa/run.py", "tests/x/a.py")]
    assert _uncovered_literals(srcs, tracked, ["scripts/qa/run.py"]) == [("docs/northstar/other.md", "tests/x/a.py")]
    assert _uncovered_literals(srcs, tracked, ["scripts/qa", "docs/northstar/other.md"]) == []
    assert _uncovered_literals(srcs, tracked, ["scripts/qa", "docs/northstar"]) == []


# ------------------------------------------------------------------ (6) directory grain covers a new file

def test_H019_6_a_directory_grain_entry_covers_a_new_file_under_it(tmp_path):
    """H-019 spec section 8 F9 test (6), ruling Q3 (green today): a fixture table at directory grain
    (docs/northstar) covers a new tracked file under that directory (undeclared_opens returns [] and the literal
    check finds nothing uncovered); the file-grain table naming only docs/northstar/other.md leaves it undeclared."""
    repo = _fixture_repo(tmp_path, BASE_FILES)
    new = "docs/northstar/plans/new.md"
    _commit(repo, "a new file under the declared directory", {new: "new\n"})
    log = _strace(repo, new)
    assert mgs.undeclared_opens(log, repo, []) == [new]
    assert mgs.undeclared_opens(log, repo, ["docs/northstar"]) == []
    assert mgs.undeclared_opens(log, repo, ["docs/northstar/other.md"]) == [new]
    srcs = {"tests/x/a.py": f'P = "{new}"\n'}
    assert _uncovered_literals(srcs, _tracked_files(repo), ["docs/northstar"]) == []
    assert _uncovered_literals(srcs, _tracked_files(repo), ["docs/northstar/other.md"]) == [(new, "tests/x/a.py")]
