# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md line 452 (the HARNESS-gate-reorder paragraph);
# design background docs/northstar/plans/harness/gate-parallel-scout.md.
"""HARNESS-gate-reorder (lane H): the merge gate runs its cheap, decisive stages first and exits at the
first REJECT among them, so a status drift never waits behind the full regression block.

INTERFACES SHARED BY THE BUILDER AND THESE TESTS (fixed in full, verbatim from the paragraph)

1. Stage order in scripts/specfactory/merge_gate.sh: status, footprint, pins, transport, playthrough and
   lane_plays run before csim, specfactory and lab. In the gate's output the stage names are the existing
   ones: `GATE status`, `GATE footprint`, `GATE rule_pins` (the paragraph's "pins"), `GATE transport`,
   `GATE playthrough`, `GATE lane_plays`, then `GATE regression_csim`, `GATE specfactory_regression`,
   `GATE regression_lab`. Test 2 pins "all six before every regression line".
2. A new shell function call `early_exit_if_rejected` sits after the lane_plays stage and before the
   regression block. It checks the GLOBAL REJECTED flag (Architect ruling: a REJECT before the early block,
   such as libm_lint, counts too). When any stage so far has REJECTed, it prints
       GATE early_exit REJECT <stage list>
   naming every REJECTed stage so far, and exits 1 at once (tests assert only that the named stages are in
   it; the separator is the builder's). With no REJECT it prints nothing and the gate goes on.
   `look` stays where it is (after the regression stages); `status` moves into the early block. The order of
   the six stages inside the block is the builder's: no test pins it (the strict-sequence test was dropped).
   RETIRED CLAUSE: tests/specfactory/test_merge_gate.py::test_status_stage_comes_after_look_and_is_called_with_repo_and_base
   asserts `look[0] < status[0]`; that ordering clause is retired by this piece under test-defect row
   TD-HARNESS-gate-reorder-1 (a clerk writes the row and the edit; this file does not touch that test). Its
   inverse, `status` before `regression_csim`, is test 2 below.
3. After the block every stage runs to the end as today: a REJECT after the early block (here
   regression_csim) is followed by the rest of the stages and the `GATE row` summary, exit 1.
4. Known-red handling is unchanged: a suite that is red on main and red on the candidate (baseline red)
   does not REJECT regression_csim.

FIXTURE (the tests/specfactory/test_gate_base_stage.py pattern, :25-72, adapted to the real stages): a
candidate git repo (Makefile that touches the two libs, empty tests/csim, tests/qa/t1) and a "gate repo",
a clone of it holding scripts/specfactory (every file symlinked to this tree, merge_gate.sh included) and
docs/ (symlinked to this tree's docs, except a minimal programme file with a lane table). The gate runs
from the gate repo's script, so `status_check.py --repo <gate repo>` reads the fixture's own lane table.
The lane table cites one sha. Drift variant: a commit that exists only in the gate repo, so it is not an
ancestor of the base and status_check prints `STATUS lane_table DRIFT`. Clean variant: the base commit.

POSITIVE CONTROL: tests/specfactory/fixtures/gate_reorder/merge_gate_pre_reorder.sh is a saved copy of the
script as it was before this piece. The same drift fixture on it prints `GATE regression_csim` before
`GATE status` (test 1c), which is what the new order must end.

UNTESTED: (a) the playthrough and lane_plays known-red lists inside the early block (they need Godot and
xvfb; their behaviour is covered by test_gate_playthrough.py and does not change here); (b) the stage
`<stage list>` separator and exact format beyond containing `status` (the paragraph gives only the
placeholder); (c) where `look` lands relative to `status` (the paragraph is silent; see the report note
on tests/specfactory/test_merge_gate.py:337).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO / "scripts" / "specfactory"
SAVED_OLD_GATE = REPO / "tests" / "specfactory" / "fixtures" / "gate_reorder" / "merge_gate_pre_reorder.sh"
GATE_PATH = "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"
RUN_TIMEOUT_S = 240
PROGRAMME = "docs/northstar/plans/2026-10-07-visible-game-programme.md"
EARLY = ["status", "footprint", "rule_pins", "transport", "playthrough", "lane_plays"]
REGRESSION = ["regression_csim", "specfactory_regression", "regression_lab"]
MAKEFILE = "libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n"
OK_STUB = "import sys\nsys.exit(0)\n"
# Tools whose real runs reject a toy repo for reasons that have nothing to do with the order under test; stubbed so
# the only REJECT in a fixture is the one the test plants. A stage that REJECTs before the early block would
# otherwise trip early_exit_if_rejected in every fixture.
NOISY_TOOLS = ("alg_constants.py", "reach_lint.py", "sig_table.py")


def _pieces(*owns):
    return '[[piece]]\nid = "B1"\nowns = [' + ", ".join(f'"{o}"' for o in owns) + ']\nacceptance = []\ndepends_on = []\n'


PIECES = _pieces("csrc/stub.c")
# Test-defect TD-HARNESS-gate-reorder-1 (ruler Architect 2026-10-29): footprint is in the early block and a REJECT
# there ends the run, so a fixture that must reach the regression block has B1 own every file its candidate commits.
OWNS_CLEAN = _pieces("csrc/stub.c", "feat.txt")
OWNS_NEW_RED = _pieces("csrc/stub.c", "feat.txt", "tests/csim/test_new_red.py")
COPIED_INTO_CANDIDATE = ("csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml", "CLAUDE.md")  # CLAUDE.md: status_check method_pins reads it at the base
LEDGER = "docs/northstar/plans/push_ledger_2026-09-22.md"  # the real ledger has open DRIFT rows: status_check reads it


def _git(cwd, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        "-c", "protocol.file.allow=always", *args],
                       cwd=str(cwd), capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _commit(repo, name, text):
    (Path(repo) / name).parent.mkdir(parents=True, exist_ok=True)
    (Path(repo) / name).write_text(text)
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)
    return _git(repo, "rev-parse", "HEAD")


def _overlay(root, rel_file, text):
    """Make rel_file under root a real file with this tree's text replaced; every dir on its path is a real dir
    whose other entries are symlinks to this tree (docs/ is 380 MB, so it is never copied)."""
    parts = Path(rel_file).parts
    src, dst = REPO, Path(root)
    for part in parts[:-1]:
        src, dst = src / part, dst / part
        if dst.is_symlink():  # left by an earlier overlay: replace it, never write through it
            dst.unlink()
        dst.mkdir(exist_ok=True)
        for e in src.iterdir():
            if e.name != parts[parts.index(part) + 1] and not (dst / e.name).exists():
                (dst / e.name).symlink_to(e)
    (dst / parts[-1]).unlink(missing_ok=True)  # a symlink into this tree: write_text would follow it
    (dst / parts[-1]).write_text(text)


def _build(tmp_path, *, drift, gate_script, candidate_files=None, base_files=None, stubs=None, pieces=PIECES):
    """Returns (gate script path, candidate dir). candidate_files / base_files: {relpath: text} committed on top
    of the common first commit (base_files go into the base commit that origin/main points at)."""
    cand = tmp_path / "cand"
    cand.mkdir()
    _git(cand, "init", "-q", "-b", "main")
    (cand / "csrc").mkdir()
    _commit(cand, "csrc/stub.c", "int om_stub(void) { return 0; }\n")
    _commit(cand, "Makefile", MAKEFILE)
    for d in ("tests/csim", "tests/qa/t1"):
        _commit(cand, d + "/.keep", "\n")
    for rel in COPIED_INTO_CANDIDATE:
        _commit(cand, rel, (REPO / rel).read_text())
    for rel, text in (base_files or {}).items():
        _commit(cand, rel, text)
    base_sha = _git(cand, "rev-parse", "HEAD")
    # A bare origin holding only the base: the gate's own `git fetch origin` must not move origin/main to HEAD.
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(tmp_path / "origin.git"))
    _git(cand, "remote", "add", "origin", str(tmp_path / "origin.git"))
    _git(cand, "push", "-q", "origin", "main")
    _git(cand, "fetch", "-q", "origin")
    for rel, text in (candidate_files or {}).items():
        _commit(cand, rel, text)
    if not candidate_files:
        _commit(cand, "feat.txt", "feat\n")

    root = tmp_path / "gaterepo"
    _git(tmp_path, "clone", "-q", str(cand), str(root))
    _git(root, "update-ref", "refs/remotes/origin/main", base_sha)
    sha = base_sha
    if drift:
        sha = _commit(root, "gate_only.txt", "lane table cites this commit; the base does not contain it\n")
    (root / "scripts" / "specfactory").mkdir(parents=True)
    for f in SPEC_DIR.iterdir():
        if f.name not in ("merge_gate.sh", "merge_gate_support.py", *NOISY_TOOLS):
            (root / "scripts" / "specfactory" / f.name).symlink_to(f)
    # A copy, not a symlink: merge_gate_support.py runs sig_table.py by its resolved path, so only a real file
    # here makes it call the stub next to it.
    shutil.copy(SPEC_DIR / "merge_gate_support.py", root / "scripts" / "specfactory" / "merge_gate_support.py")
    for name, text in {**{n: OK_STUB for n in NOISY_TOOLS}, **(stubs or {})}.items():
        (root / "scripts" / "specfactory" / name).unlink(missing_ok=True)
        (root / "scripts" / "specfactory" / name).write_text(text)
    shutil.copy(gate_script, root / "scripts" / "specfactory" / "merge_gate.sh")
    _overlay(root, PROGRAMME,
             "| Lane | On main | Next piece | First look | Westley row |\n|---|---|---|---|---|\n"
             f"| X | {sha} | - | - | - |\n")
    _overlay(root, "docs/northstar/plans/push/pieces.toml", pieces)
    _overlay(root, LEDGER, "")
    (tmp_path / "pieces.toml").write_text(pieces)
    (tmp_path / "placeholders.txt").write_text("")
    return root / "scripts" / "specfactory" / "merge_gate.sh", cand


def _run(tmp_path, *, drift=False, gate_script=None, candidate_files=None, base_files=None, stubs=None, pieces=PIECES):
    gate, cand = _build(tmp_path, drift=drift, gate_script=gate_script or (SPEC_DIR / "merge_gate.sh"),
                        candidate_files=candidate_files, base_files=base_files, stubs=stubs, pieces=pieces)
    env = {"PATH": GATE_PATH, "HOME": str(Path.home()), "MERGE_GATE_RUNS_CSV": str(tmp_path / "runs.csv"),
           "MERGE_GATE_PIECES": str(tmp_path / "pieces.toml"),
           "MERGE_GATE_PLACEHOLDERS": str(tmp_path / "placeholders.txt")}
    r = subprocess.run(["bash", str(gate), str(cand), "origin/main", "B1"], capture_output=True, text=True,
                       env=env, timeout=RUN_TIMEOUT_S)
    lines = r.stdout.splitlines()
    return r.returncode, lines, r.stdout + r.stderr


def _idx(lines, name):
    """Index of the first `GATE <name> ` line, or None."""
    for i, ln in enumerate(lines):
        if ln.startswith(f"GATE {name} "):
            return i
    return None


def _gate_lines(lines):
    return [ln for ln in lines if ln.startswith("GATE ") and not ln.startswith("GATE row ")]


# ---------------------------------------------------------------- drift fixture: the early exit

def test_1a_status_drift_rejects_and_early_exit_stops_before_csim(tmp_path):
    """HARNESS-gate-reorder, clause 'the gate exits 1 at the first REJECT inside that early block ... printing
    GATE early_exit REJECT <stage list>' and the paragraph's test: a lane table that disagrees with main prints a
    status DRIFT; the output has `GATE status REJECT`, `GATE early_exit REJECT` and no `GATE regression_csim`."""
    rc, lines, out = _run(tmp_path, drift=True)
    assert any(ln.startswith("GATE status REJECT") for ln in lines), out
    early = [ln for ln in lines if ln.startswith("GATE early_exit REJECT")]
    assert early, "no `GATE early_exit REJECT` line:\n" + out
    assert "status" in early[0].split("REJECT", 1)[1], early[0]
    assert not any(ln.startswith("GATE regression_csim") for ln in lines), out
    assert rc == 1, out


def test_1b_early_exit_comes_after_lane_plays_and_nothing_regression_follows(tmp_path):
    """HARNESS-gate-reorder, clause 'a new early_exit_if_rejected call after lane_plays, before the regression
    block': the whole early block still runs (all six stage lines print), then early_exit, then no stage line
    of the regression block or later."""
    rc, lines, out = _run(tmp_path, drift=True)
    ee = _idx(lines, "early_exit")
    assert ee is not None, "no `GATE early_exit` line:\n" + out
    for name in EARLY:
        i = _idx(lines, name)
        assert i is not None and i < ee, f"{name} line missing or after early_exit:\n{out}"
    assert _idx(lines, "lane_plays") < ee
    after = [ln for ln in _gate_lines(lines)[_gate_lines(lines).index(lines[ee]) + 1:]]
    assert after == [], "stage lines after early_exit: " + repr(after)


def test_1c_positive_control_saved_old_script_runs_csim_before_status(tmp_path):
    """HARNESS-gate-reorder positive control (the paragraph's): the same drift fixture on the pre-change stage
    order (saved copy of today's script) shows `GATE regression_csim` before `GATE status`, no early_exit.
    Green on the built tree and after: it proves the fixture drifts and that the order is what changes."""
    rc, lines, out = _run(tmp_path, drift=True, gate_script=SAVED_OLD_GATE)
    csim, status = _idx(lines, "regression_csim"), _idx(lines, "status")
    assert csim is not None and status is not None and csim < status, out
    assert any(ln.startswith("GATE status REJECT") for ln in lines), out
    assert _idx(lines, "early_exit") is None, out
    assert rc == 1, out


# ---------------------------------------------------------------- clean fixture: the order

def test_2_cheap_stages_all_run_before_every_regression_stage(tmp_path):
    """HARNESS-gate-reorder, clause 'status, footprint, pins, transport, playthrough and lane_plays run before
    csim, specfactory and lab': on a clean fixture no early_exit prints and each of the six stage lines precedes
    each of the three regression lines."""
    rc, lines, out = _run(tmp_path, pieces=OWNS_CLEAN)
    assert _idx(lines, "early_exit") is None, out
    for name in EARLY + REGRESSION:
        assert _idx(lines, name) is not None, f"{name} line missing:\n{out}"
    last_early = max(_idx(lines, n) for n in EARLY)
    first_reg = min(_idx(lines, n) for n in REGRESSION)
    assert last_early < first_reg, f"early stage after a regression stage:\n{out}"


# ---------------------------------------------------------------- late reject and known red

NEW_RED = "def test_new_red():\n    assert False, 'new red on the candidate'\n"
OLD_RED = "def test_old_red():\n    assert False, 'red on main and on the candidate'\n"


def test_4_late_reject_still_runs_every_stage_to_the_end(tmp_path):
    """HARNESS-gate-reorder, clause 'after the block every stage runs to the end as today, so a late REJECT
    still shows the full summary': a new red test in tests/csim REJECTs regression_csim after the early block;
    the stages after it (specfactory_regression, regression_lab, look) and the GATE row still print, exit 1,
    no early_exit. Red on the built tree because regression_csim still precedes lane_plays there."""
    rc, lines, out = _run(tmp_path, candidate_files={"tests/csim/test_new_red.py": NEW_RED}, pieces=OWNS_NEW_RED)
    csim = _idx(lines, "regression_csim")
    assert csim is not None and lines[csim].startswith("GATE regression_csim REJECT"), out
    assert _idx(lines, "lane_plays") < csim, "lane_plays must precede regression_csim:\n" + out
    assert _idx(lines, "early_exit") is None, out
    for name in ("specfactory_regression", "regression_lab", "look"):
        assert _idx(lines, name) is not None and _idx(lines, name) > csim, out
    assert any(ln.startswith("GATE row ") for ln in lines), out
    assert rc == 1, out


def test_5_known_red_stage_after_the_early_block_behaves_as_today(tmp_path):
    """HARNESS-gate-reorder, clause 'the known-red handling is unchanged': a csim test red on main AND on the
    candidate is baseline red, not a regression: `GATE regression_csim OK`, no early_exit, exit 0. Red on the
    built tree only because regression_csim still precedes lane_plays there (the order assertion)."""
    rc, lines, out = _run(tmp_path, base_files={"tests/csim/test_old_red.py": OLD_RED}, pieces=OWNS_CLEAN)
    csim = _idx(lines, "regression_csim")
    assert csim is not None and lines[csim].startswith("GATE regression_csim OK"), out
    assert _idx(lines, "early_exit") is None, out
    assert _idx(lines, "lane_plays") < csim, "lane_plays must precede regression_csim:\n" + out
    assert rc == 0, out


# ---------------------------------------------------------------- the global flag

LIBM_REJECT_STUB = "import sys\nprint('libm call in csrc/stub.c')\nsys.exit(1)\n"


def test_6_libm_lint_reject_exits_before_csim_and_early_exit_lists_it(tmp_path):
    """HARNESS-gate-reorder, Architect ruling 3: early_exit_if_rejected checks the GLOBAL REJECTED flag and its line
    lists every REJECT stage so far. A stubbed libm_lint.py that fails (stage 2, before the early block) gives
    `GATE libm_lint REJECT`, then `GATE early_exit REJECT ...libm_lint...` and no regression_csim line, exit 1."""
    rc, lines, out = _run(tmp_path, stubs={"libm_lint.py": LIBM_REJECT_STUB})
    assert any(ln.startswith("GATE libm_lint REJECT") for ln in lines), out
    early = [ln for ln in lines if ln.startswith("GATE early_exit REJECT")]
    assert early, "no `GATE early_exit REJECT` line:\n" + out
    assert "libm_lint" in early[0].split("REJECT", 1)[1], early[0]
    assert not any(ln.startswith("GATE regression_csim") for ln in lines), out
    assert rc == 1, out


def test_6c_positive_control_saved_old_script_runs_csim_after_a_libm_lint_reject(tmp_path):
    """Positive control for test 6 (green before and after): the same libm_lint stub on the saved pre-change
    script REJECTs libm_lint and still runs `GATE regression_csim`, with no early_exit line."""
    rc, lines, out = _run(tmp_path, gate_script=SAVED_OLD_GATE, stubs={"libm_lint.py": LIBM_REJECT_STUB})
    assert any(ln.startswith("GATE libm_lint REJECT") for ln in lines), out
    assert _idx(lines, "regression_csim") is not None, out
    assert _idx(lines, "early_exit") is None, out
    assert rc == 1, out
