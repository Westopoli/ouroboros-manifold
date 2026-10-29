# spec: docs/northstar/plans/2026-10-29-layered-gate-spec.md, section 4 HARNESS-suite-inputs-trim, section 8 F9, F12, N20
# Rule pins: none (harness piece, layered-gate spec section 4)
"""Tests for scripts/specfactory/suite_inputs.toml, the per-suite input table the gate hashes
(HARNESS-suite-inputs-trim). Six groups: (1) no directory-grain entry under a file-grain root,
(2) every declared path exists at HEAD, (3) undeclared_opens positive control, (4) the trim bites
on _input_hash, (5) F9 literal repo paths of the suite sources are covered, (6) F9 positive control.

Spec text in force (section 4 paragraph HARNESS-suite-inputs-trim, then section 8 F9, F12, N20):

  HARNESS-suite-inputs-trim (Tool: Workflow; a single piece, one toml and one test file, file-disjoint
  from lane H; lands alone; owns `scripts/specfactory/suite_inputs.toml`, new
  `tests/specfactory/test_suite_inputs.py`; depends_on none in flight; impact harness). The builder
  re-runs the A15 recipe once per declared suite (`strace -f -e trace=openat,execve -o <log> <venv>/python
  -m pytest <suite> -q -p no:cacheprovider`, one suite at a time, in a worktree from `wt.py new`), lists
  every tracked file the run opened with `merge_gate_support.undeclared_opens(log, repo, [])` (an empty
  declared list returns every tracked file opened), and rewrites each suite's `paths` so that: under
  `docs/northstar`, `scripts/specfactory`, `scripts/skilllab`, `scripts/library`, `scripts/qa` and
  `simulation/` the entries are the opened files, one path each, never a directory; every other entry of
  today's table is kept as it is (`csrc`, `Makefile`, `tests/<suite>`, `docs/bible`, `library`, `assets`,
  `autoload`, `scenes` and the rest stay at directory grain: they are code or data the suite loads by
  glob). The `tests/specfactory` suite is exempt: it tests the harness and the repo and keeps its table
  unchanged. After the rewrite the builder runs `undeclared_opens(log, repo, new_paths)` for each suite
  and pastes the result (it must be empty) and the per-suite entry counts in its report. Tests
  (`tests/specfactory/test_suite_inputs.py`, red on main because the table still names the directories):
  (1) no `paths` entry of the `tests/csim`, `tests/qa/t1` or `tests/transport` tables equals
  `docs/northstar`, `scripts/specfactory`, `scripts/skilllab` or `simulation` or any directory under them
  (a path is a directory when `git cat-file -t HEAD:<path>` says `tree`); (2) every declared path exists
  at `HEAD` (`git rev-parse HEAD:<path>` succeeds), so a renamed input is caught at the pre-gate; (3)
  positive control: a fixture strace log that opens `docs/northstar/spec_factory/mvp_features.toml` is
  covered by the fixture table that names that file (`undeclared_opens` returns `[]`) and a fixture table
  that names only `docs/northstar/other.md` leaves it undeclared (returns the one path); (4) control that
  the trim bites: `_input_hash` of a fixture repo over the trimmed table is unchanged by a commit that
  adds a file under `docs/northstar/plans/` and changed by a commit that edits
  `docs/northstar/spec_factory/mvp_features.toml`. Expected effect on the first harness landing after it
  lands: `GATE regression_csim OK inputs unchanged <hash>` in the gate log and a stage total under 15
  minutes.

  F9, trim under-observation. suite-inputs-trim test (5): every literal repo path in
  `tests/<suite>/**/*.py` matching `(docs|scripts|simulation)/[A-Za-z0-9_./-]+` falls under a declared
  path. Rule for the builder: a directory the suite opens as a directory (strace `openat` with
  `O_DIRECTORY`, or `getdents`) stays at directory grain; only files opened as files are listed by file.
  Test (6), positive control: a fixture table at directory grain covers a new file under that directory.

  F12. The specfactory suite does not run under xdist (it boots Godot and uses worktrees); "under xdist"
  is struck from layer 2's `harness` rule. The suite-inputs-trim builder reports the measured wall time of
  `tests/specfactory`: that suite is exempt from the trim and is timed by one plain run under the gate
  venv (`timeout 2400`), not traced; the 600 s target stays a DRAFT until measured.

  N20. `undeclared_opens` takes the strace text, not a path; the trim's file-grain roots are
  `docs/northstar`, `scripts/specfactory`, `scripts/skilllab`, `scripts/library`, `scripts/qa`,
  `simulation/`; the row field is `status.attach_sha`; the empty-ids case (`skipped: no ids`) is tiers
  amendment item (g); `docs/architecture.md` joins the contract pin list.

Picked details quoted from the brief:

  D1 (DIR_GRAIN_ALLOWED). Group (1): no paths entry of the tests/csim, tests/qa/t1 or tests/transport
  table equals one of the six roots or is a directory under one (git cat-file -t HEAD:<path> says tree),
  unless it is in DIR_GRAIN_ALLOWED (a module constant of the test file, a tuple of repo paths, empty when
  shipped; its comment says: a directory the suite opens as a directory stays at directory grain, spec
  F9; an entry is added only by the ruler with the builder's pasted O_DIRECTORY openat line). The same
  group asserts that DIR_GRAIN_ALLOWED contains none of the six roots and nothing under
  docs/northstar/plans (the ruling DEC-suiteinputs-dirgrain-2026-10-29: the ruler may add only a
  directory strictly under a root, never a root, never under docs/northstar/plans).

  D6. Group (5): every literal repo path in tests/csim/**/*.py, tests/qa/t1/**/*.py and
  tests/transport/**/*.py matching the regex (docs|scripts|simulation)/[A-Za-z0-9_./-]+ that names a
  tracked file at HEAD (D6: trailing . , ; : ) ] stripped; missing paths and stems skipped) equals a
  declared path of that suite's table or lies under a declared directory. Parametrised per suite; the
  failure lists the uncovered literals with the python file each came from. The builder adds to the table
  the files group 5 flags (D6; directory literals are never added).

  D7 (red/green expectation on the base tree). Group (1) must be red for the stated reason: the real
  table still names the directories. Groups (2) and (5) may be red or green on the base (a red one must
  be red because of a table entry, never because of the test). Groups (3), (4), (6) and controls C1 to C3
  are mechanism controls and must be GREEN today.
"""
import ast
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402

TABLE = REPO / "scripts" / "specfactory" / "suite_inputs.toml"
SUITES = ("tests/csim", "tests/qa/t1", "tests/transport")
# N20: the file-grain roots (the spec writes the last one `simulation/`)
ROOTS = ("docs/northstar", "scripts/specfactory", "scripts/skilllab", "scripts/library", "scripts/qa",
         "simulation")
PLANS = "docs/northstar/plans"
# A directory the suite opens as a directory stays at directory grain, spec F9; an entry is added only
# by the ruler with the builder's pasted O_DIRECTORY openat line.
DIR_GRAIN_ALLOWED: tuple[str, ...] = ()

LITERAL = re.compile(r"(?:docs|scripts|simulation)/[A-Za-z0-9_./-]+")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, text=True)


def _object_type(repo: Path, path: str) -> str | None:
    """`git cat-file -t HEAD:<path>`: tree, blob, or None when the path is not at HEAD."""
    r = subprocess.run(["git", "cat-file", "-t", f"HEAD:{path}"], cwd=str(repo),
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _exists_at_head(repo: Path, path: str) -> bool:
    return subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=str(repo),
                          capture_output=True, text=True).returncode == 0


def _table(suite: str) -> list[str]:
    return list(tomllib.load(TABLE.open("rb"))["suites"][suite]["paths"])


def _under_root(path: str) -> bool:
    return any(path == r or path.startswith(r + "/") for r in ROOTS)


def _dir_grain_offenders(repo: Path, paths: list[str], allowed: tuple[str, ...]) -> list[str]:
    """Entries that equal a root or are a directory (tree at HEAD) under one, outside `allowed`."""
    out = []
    for p in paths:
        p = p.rstrip("/")
        if p in allowed or not _under_root(p):
            continue
        if p in ROOTS or _object_type(repo, p) == "tree":
            out.append(p)
    return out


def _string_literals(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [source]
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _repo_literals(source: str) -> list[str]:
    """Every (docs|scripts|simulation)/... literal of a python source, D6: trailing . , ; : ) ] stripped."""
    found = []
    for lit in _string_literals(source):
        for m in LITERAL.finditer(lit):
            s = m.group(0).rstrip(".,;:)]")
            if s:
                found.append(s)
    return found


def _tracked_at_head(repo: Path) -> set[str]:
    out = _git(repo, "ls-tree", "-r", "--name-only", "HEAD").stdout
    return set(out.split("\n")) - {""}


def _uncovered_literals(repo: Path, suite_dir: str, declared: list[str]) -> list[str]:
    """Group-5 check: literals of repo/<suite_dir>/**/*.py naming a tracked file at HEAD that no declared
    path equals or contains. Returns `<literal> (<python file>)` lines, sorted."""
    tracked = _tracked_at_head(repo)
    decl = [d.rstrip("/") for d in declared]
    bad = set()
    for py in sorted((repo / suite_dir).rglob("*.py")):
        rel = py.relative_to(repo).as_posix()
        for lit in _repo_literals(py.read_text(errors="replace")):
            if lit not in tracked:
                continue
            if any(lit == d or lit.startswith(d + "/") for d in decl):
                continue
            bad.add(f"{lit} ({rel})")
    return sorted(bad)


def _strace_open(path: Path, ret: int = 3, flags: str = "O_RDONLY|O_CLOEXEC") -> str:
    return f'openat(AT_FDCWD, "{path}", {flags}) = {ret}\n'


def _fixture_repo(base: Path) -> Path:
    repo = base / "repo"
    (repo / "docs" / "northstar" / "spec_factory").mkdir(parents=True)
    (repo / "docs" / "northstar" / "spec_factory" / "mvp_features.toml").write_text("x = 1\n")
    (repo / "docs" / "northstar" / "other.md").write_text("other\n")
    (repo / "Makefile").write_text("all:\n")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _commit_file(repo: Path, rel: str, text: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", f"touch {rel}")


MVP = "docs/northstar/spec_factory/mvp_features.toml"


@pytest.mark.parametrize("suite", SUITES)
def test_group1_no_directory_grain_under_a_root(suite):
    bad_allow = [a for a in DIR_GRAIN_ALLOWED
                 if a.rstrip("/") in ROOTS or a == PLANS or a.startswith(PLANS + "/")]
    assert not bad_allow, f"DIR_GRAIN_ALLOWED may hold no root and nothing under {PLANS}: {bad_allow}"
    offenders = _dir_grain_offenders(REPO, _table(suite), DIR_GRAIN_ALLOWED)
    assert not offenders, f"{suite}: directory-grain entries under a file-grain root: {offenders}"


@pytest.mark.parametrize("suite", SUITES)
def test_group2_every_declared_path_exists_at_head(suite):
    missing = [p for p in _table(suite) if not _exists_at_head(REPO, p.rstrip("/"))]
    assert not missing, f"{suite}: declared paths missing at HEAD: {missing}"


def test_group3_undeclared_opens_positive_control(tmp_path):
    repo = _fixture_repo(tmp_path)
    log = _strace_open(repo.resolve() / MVP)
    assert mgs.undeclared_opens(log, repo, [MVP, "Makefile"]) == []
    assert mgs.undeclared_opens(log, repo, ["docs/northstar/other.md"]) == [MVP]


def test_group4_trim_bites(tmp_path):
    repo = _fixture_repo(tmp_path)
    trimmed = [MVP, "Makefile"]
    dirgrain = ["docs/northstar", "Makefile"]
    h_trim0 = mgs._input_hash(repo, "HEAD", trimmed)
    h_dir0 = mgs._input_hash(repo, "HEAD", dirgrain)
    assert len(h_trim0) == 16 and all(c in "0123456789abcdef" for c in h_trim0)
    _commit_file(repo, "docs/northstar/plans/added.md", "plan\n")
    assert mgs._input_hash(repo, "HEAD", trimmed) == h_trim0
    # control: the directory-grain table DOES change, so the assertion above can fail
    assert mgs._input_hash(repo, "HEAD", dirgrain) != h_dir0
    _commit_file(repo, MVP, "x = 2\n")
    assert mgs._input_hash(repo, "HEAD", trimmed) != h_trim0


@pytest.mark.parametrize("suite", SUITES)
def test_group5_every_literal_repo_path_is_covered(suite):
    uncovered = _uncovered_literals(REPO, suite, _table(suite))
    assert not uncovered, f"{suite}: literal repo paths not under a declared path: {uncovered}"


def test_group6_directory_grain_table_covers_a_new_file(tmp_path):
    repo = _fixture_repo(tmp_path)
    _commit_file(repo, "docs/northstar/plans/new.md", "new\n")
    new = "docs/northstar/plans/new.md"
    log = _strace_open(repo.resolve() / new)
    assert mgs.undeclared_opens(log, repo, ["docs/northstar"]) == []
    # control in the same test: the file-grain table that does not name it leaves it undeclared
    assert mgs.undeclared_opens(log, repo, [MVP]) == [new]


# ---- controls C1 to C3: each detector must not be vacuous ----

def test_c1_tree_detector_flags_directory_and_file():
    assert _object_type(REPO, "docs/northstar") == "tree"
    assert _object_type(REPO, "Makefile") == "blob"
    assert _object_type(REPO, "no/such/path") is None
    assert _dir_grain_offenders(REPO, ["docs/northstar"], ()) == ["docs/northstar"]
    assert _dir_grain_offenders(REPO, ["docs/northstar"], ("docs/northstar",)) == []
    assert _dir_grain_offenders(REPO, ["Makefile", "csrc"], ()) == []


def test_c2_literal_regex_and_group5_check_are_not_vacuous(tmp_path):
    src = 'a = "see docs/northstar/other.md, and (scripts/x.py)."\nb = "no path here"\n'
    assert _repo_literals(src) == ["docs/northstar/other.md", "scripts/x.py"]
    repo = _fixture_repo(tmp_path)
    (repo / "tests" / "fx").mkdir(parents=True)
    (repo / "tests" / "fx" / "test_a.py").write_text(
        'P = "docs/northstar/other.md"\nQ = "docs/northstar/gone.md"\nR = "docs/northstar"\n')
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "suite")
    # tracked file, nothing covers it: flagged; missing path and directory stem: skipped
    assert _uncovered_literals(repo, "tests/fx", ["Makefile"]) == [
        "docs/northstar/other.md (tests/fx/test_a.py)"]
    assert _uncovered_literals(repo, "tests/fx", ["docs/northstar/other.md"]) == []
    assert _uncovered_literals(repo, "tests/fx", ["docs/northstar"]) == []


def test_c3_fixture_strace_line_is_parsed_by_undeclared_opens(tmp_path):
    repo = _fixture_repo(tmp_path)
    log = _strace_open(repo.resolve() / MVP)
    assert mgs.undeclared_opens(log, repo, []) == [MVP]
    failed = _strace_open(repo.resolve() / MVP, ret=-1)
    assert mgs.undeclared_opens(failed, repo, []) == []
