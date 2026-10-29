# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 32, A94 ("Gate" bullet: last unit of the group)
"""Three new merge gate steps that close the A92 'gate gap': nothing the gate ran
covered tests/specfactory, sig_table --check or stale allowlist lines.

Contract these tests pin (none of it exists yet, so the new-step tests are red).
Step names are PINNED here and are listed as ambiguities in the unit report:

  specfactory_regression
      merge_gate.sh runs the existing `merge_gate_support.py regression <cand> <base>
      tests/specfactory` and prints `GATE specfactory_regression OK|REJECT <detail>`.
      Regression, not absolute: a test failing in both base and candidate (today
      test_snapshot_fixture, awaiting Westley) never rejects; a test that fails only in
      the candidate rejects and its id is named in the detail. The step runs after
      regression_csim / regression_qa_t1 (full profile only, not --revert).
  sig_check
      `merge_gate_support.py sig-check [--project DIR] [--table PATH]` runs
      `sig_table --check` (exit 0 iff --emit would change no file; the BLOCKED-only
      check stays in sig_blocked). Python: `mgs.sig_check(project, table) -> (ok, detail)`;
      detail names the stale files. merge_gate.sh prints `GATE sig_check OK|REJECT` and
      judges the CANDIDATE: --project "$CANDIDATE", table = the candidate's own
      docs/northstar/spec_factory/signatures.toml. Runs next to sig_blocked, so it is
      part of the --revert profile too.
  allowlist_strict
      `alg_constants.py --lint CSRC_DIR --strict` is the plain lint plus: exit 1 and a
      `STALE <entry>` line for every constants_allowlist.txt line (of the tree holding
      CSRC_DIR) that matches no current violation. Without --strict the lint is
      unchanged (tolerates stale lines; step 3 `alg_constants` keeps using it).
      merge_gate.sh prints `GATE allowlist_strict OK|REJECT` from that call on the
      candidate's csrc. Runs next to alg_constants (both profiles).
Every test builds its own fake repo; the real-repo tests at the bottom run the same
checks on this checkout (origin/main) and pass only once the steps are implemented AND
main is clean under them.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SPEC = REPO / "scripts" / "specfactory"
GATE = SPEC / "merge_gate.sh"
SUPPORT = SPEC / "merge_gate_support.py"
ALG = SPEC / "alg_constants.py"
SIG = SPEC / "sig_table.py"
sys.path.insert(0, str(SPEC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import merge_gate_support as mgs  # noqa: E402
from gate_toy_root import fake_gate_root, gate_env  # noqa: E402

PY = sys.executable
TABLE_REL = Path("docs/northstar/spec_factory/signatures.toml")
ALLOW_REL = Path("docs/northstar/spec_factory/constants_allowlist.txt")

META = "[meta]\nabi_version = 2\nsymbol_count = 1\nstruct_count = 0\nambiguous_remaining = 0\n\n"
ROW_A = '''[[symbols]]
name = "om_stub"
module = "stub.c"
restype = "int"
params = []
epics = ["E-09"]
confidence = "likely"
note = "test fixture"
'''
ROW_B = ROW_A.replace("om_stub", "om_stub_b")

HEADER = "#ifndef OM_FAKE_H\n#define OM_FAKE_H\n#include <stdint.h>\ntypedef struct om_world om_world;\n#ifdef __cplusplus\n#endif\n#endif\n"
CONFTEST = ("import ctypes\n\n# ---- generated from signatures.toml ----\n# ---- end generated ----\n")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _base_repo(tmp_path: Path) -> Path:
    """A fake candidate repo in the shape test_gate_sig_blocked.py uses, plus a
    generated-clean signature table, an empty allowlist and a passing specfactory test."""
    repo = tmp_path / "cand"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    _write(repo, "csrc/stub.c", "int om_stub(void) { return 0; }\nint om_stub_b(void) { return 0; }\n")
    _write(repo, "csrc/ouroboros_sim.h", HEADER)
    _write(repo, "Makefile", "libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n")
    (repo / "tests" / "csim").mkdir(parents=True)
    _write(repo, "tests/csim/conftest.py", CONFTEST)
    _write(repo, str(TABLE_REL), META + ROW_A)
    _write(repo, str(ALLOW_REL), "")
    _write(repo, "tests/specfactory/test_fixture_ok.py", "def test_ok():\n    assert True\n")
    emitted = subprocess.run([PY, str(SIG), "--project", str(repo), "--emit"],
                             capture_output=True, text=True)
    assert emitted.returncode == 0, emitted.stdout + emitted.stderr
    _commit(repo, "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _gate(tmp_path: Path, repo: Path, base_ref: str = "HEAD") -> subprocess.CompletedProcess:
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/stub.c"]\nacceptance = []\ndepends_on = []\n')
    env = {"MERGE_GATE_PIECES": str(pieces),
           "MERGE_GATE_SIGNATURES": str(repo / TABLE_REL),
           "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}
    return subprocess.run(["bash", str(GATE), str(repo), base_ref, "B1"],
                          capture_output=True, text=True, env=env, timeout=240)


def _gate_to_regression(tmp_path: Path, repo: Path, base_ref: str, *owned: str) -> subprocess.CompletedProcess:
    """Test-defect TD-HARNESS-gate-reorder-2 to -4 (ruler Architect 2026-10-29): the run must get past the early
    block (decisive line: `GATE early_exit REJECT footprint;status;placeholder_controls`), so B1 owns the files the
    candidate commits, status_check.py and sig_table.py (sig_blocked reads the gate's own tree, which a fake root lacks)
    are stubs in a fake gate root, the placeholder list is empty and HOME is set."""
    pieces = tmp_path / "pieces.toml"
    owns = ", ".join(f'"{o}"' for o in ("csrc/stub.c", *owned))
    pieces.write_text(f'[[piece]]\nid = "B1"\nowns = [{owns}]\nacceptance = []\ndepends_on = []\n')
    gate = fake_gate_root(tmp_path, noisy=("sig_table.py", "status_check.py"))
    return subprocess.run(["bash", str(gate), str(repo), base_ref, "B1"], capture_output=True, text=True,
                          env=gate_env(tmp_path, pieces, MERGE_GATE_SIGNATURES=str(repo / TABLE_REL)), timeout=240)


def _line(proc: subprocess.CompletedProcess, step: str) -> str:
    return next((ln for ln in proc.stdout.splitlines() if ln.startswith(f"GATE {step} ")), "")


# ------------------------------------------------------------ fixture controls (green now)

def test_control_fake_repo_is_emit_clean(tmp_path):
    """The fixture itself: a freshly emitted fake repo is not stale; adding a row makes it stale."""
    repo = _base_repo(tmp_path)
    clean = subprocess.run([PY, str(SIG), "--project", str(repo), "--check"], capture_output=True, text=True)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    _write(repo, str(TABLE_REL), META + ROW_A + "\n" + ROW_B)
    stale = subprocess.run([PY, str(SIG), "--project", str(repo), "--check"], capture_output=True, text=True)
    assert stale.returncode == 1, stale.stdout + stale.stderr


# ------------------------------------------------------------ step 2: sig_check

def test_sig_check_passes_a_clean_candidate(tmp_path):
    repo = _base_repo(tmp_path)
    ok, detail = mgs.sig_check(repo, repo / TABLE_REL)
    assert ok is True, detail


def test_sig_check_rejects_a_stale_header(tmp_path):
    """Planted: the table gained a row but --emit was never rerun (the A2-contract failure)."""
    repo = _base_repo(tmp_path)
    _write(repo, str(TABLE_REL), META + ROW_A + "\n" + ROW_B)
    ok, detail = mgs.sig_check(repo, repo / TABLE_REL)
    assert ok is False
    assert "csrc/ouroboros_sim.h" in detail


def test_sig_check_rejects_a_stale_conftest(tmp_path):
    """Planted: generated conftest region hand-edited away from the table."""
    repo = _base_repo(tmp_path)
    conftest = repo / "tests/csim/conftest.py"
    text = conftest.read_text()
    conftest.write_text(text.replace("# ---- end generated ----", "# hand edit\n# ---- end generated ----"))
    ok, detail = mgs.sig_check(repo, repo / TABLE_REL)
    assert ok is False
    assert "tests/csim/conftest.py" in detail


def test_sig_check_cli_exit_codes(tmp_path):
    repo = _base_repo(tmp_path)

    def run():
        return subprocess.run([PY, str(SUPPORT), "sig-check", "--project", str(repo),
                               "--table", str(repo / TABLE_REL)], capture_output=True, text=True)
    good = run()
    assert good.returncode == 0, good.stdout + good.stderr
    _write(repo, str(TABLE_REL), META + ROW_A + "\n" + ROW_B)
    bad = run()
    assert bad.returncode == 1 and "csrc/ouroboros_sim.h" in bad.stdout + bad.stderr


def test_gate_sig_check_passes_clean_candidate(tmp_path):
    proc = _gate(tmp_path, _base_repo(tmp_path))
    assert "GATE sig_check OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_sig_check_rejects_stale_header(tmp_path):
    repo = _base_repo(tmp_path)
    _write(repo, str(TABLE_REL), META + ROW_A + "\n" + ROW_B)
    _commit(repo, "table row without emit")
    proc = _gate(tmp_path, repo, "HEAD~1")
    assert "GATE sig_check REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert proc.returncode == 1


def test_gate_sig_check_rejects_stale_conftest(tmp_path):
    repo = _base_repo(tmp_path)
    conftest = repo / "tests/csim/conftest.py"
    conftest.write_text(conftest.read_text().replace("# ---- end generated ----",
                                                     "# hand edit\n# ---- end generated ----"))
    _commit(repo, "hand-edited generated conftest")
    proc = _gate(tmp_path, repo, "HEAD~1")
    assert "GATE sig_check REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert proc.returncode == 1


# ------------------------------------------------------------ step 3: allowlist_strict

SIM_C = "int om_sim_probe(void) { double x = 3.14159; return (int)x; }\n"
LIVE_ENTRY = "csrc/sim.c:3.14159:1"
STALE_ENTRY = "csrc/sim.c:6.28318:1"


def _allowlist_repo(tmp_path: Path, *entries: str) -> Path:
    repo = _base_repo(tmp_path)
    _write(repo, "csrc/sim.c", SIM_C)
    _write(repo, str(ALLOW_REL), "\n".join(entries) + "\n")
    _commit(repo, "grandfathered literal + allowlist")
    return repo


def _lint(repo: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(ALG), "--lint", str(repo / "csrc"), *flags], capture_output=True, text=True)


def test_control_plain_lint_tolerates_a_stale_line(tmp_path):
    """The gap itself (green now, stays green): plain --lint passes with a stale extra entry."""
    repo = _allowlist_repo(tmp_path, LIVE_ENTRY, STALE_ENTRY)
    assert _lint(repo).returncode == 0


def test_strict_lint_passes_an_exact_allowlist(tmp_path):
    repo = _allowlist_repo(tmp_path, LIVE_ENTRY)
    proc = _lint(repo, "--strict")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_strict_lint_rejects_a_stale_extra_line_and_names_it(tmp_path):
    repo = _allowlist_repo(tmp_path, LIVE_ENTRY, STALE_ENTRY)
    proc = _lint(repo, "--strict")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"STALE {STALE_ENTRY}" in proc.stdout
    assert f"STALE {LIVE_ENTRY}" not in proc.stdout


def test_strict_lint_still_rejects_a_new_bare_literal(tmp_path):
    """--strict is the plain lint plus the stale check, not instead of it."""
    repo = _allowlist_repo(tmp_path, LIVE_ENTRY)
    _write(repo, "csrc/sim.c", SIM_C + "int om_sim_probe2(void) { return (int)9.87654; }\n")
    proc = _lint(repo, "--strict")
    assert proc.returncode == 1 and "9.87654" in proc.stdout


def test_gate_allowlist_strict_passes_exact_allowlist(tmp_path):
    proc = _gate(tmp_path, _allowlist_repo(tmp_path, LIVE_ENTRY))
    assert "GATE allowlist_strict OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_allowlist_strict_rejects_stale_line(tmp_path):
    repo = _allowlist_repo(tmp_path, LIVE_ENTRY)
    base = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, str(ALLOW_REL), LIVE_ENTRY + "\n" + STALE_ENTRY + "\n")
    _commit(repo, "stale allowlist line")
    proc = _gate(tmp_path, repo, base)
    assert "GATE allowlist_strict REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert STALE_ENTRY in _line(proc, "allowlist_strict")
    assert "GATE alg_constants OK" in proc.stdout  # the plain step still tolerates it: the gap
    assert proc.returncode == 1


# ------------------------------------------------------------ step 1: specfactory_regression

PLANTED_FAIL = "def test_planted_new_failure():\n    assert False, 'planted'\n"


def test_gate_specfactory_regression_rejects_a_new_failure(tmp_path):
    repo = _base_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, "tests/specfactory/test_planted.py", PLANTED_FAIL)
    _commit(repo, "plant a failing specfactory test")
    proc = _gate_to_regression(tmp_path, repo, base, "tests/specfactory/test_planted.py")
    assert "GATE specfactory_regression REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert "test_planted_new_failure" in _line(proc, "specfactory_regression")
    assert proc.returncode == 1


def test_gate_specfactory_regression_passes_a_clean_candidate(tmp_path):
    repo = _base_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo, "tests/specfactory/test_second_ok.py", "def test_second_ok():\n    assert True\n")
    _commit(repo, "another passing specfactory test")
    proc = _gate_to_regression(tmp_path, repo, base, "tests/specfactory/test_second_ok.py")
    assert "GATE specfactory_regression OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_specfactory_regression_tolerates_a_standing_red(tmp_path):
    """Compared to base, not absolute: a test already failing at base (the standing
    test_snapshot_fixture red) does not reject a candidate that leaves it failing."""
    repo = _base_repo(tmp_path)
    _write(repo, "tests/specfactory/test_standing_red.py", "def test_standing_red():\n    assert False\n")
    _commit(repo, "standing red in base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", base)  # stage 0 base replaces the base arg with origin/main
    _write(repo, "tests/specfactory/test_unrelated_ok.py", "def test_unrelated_ok():\n    assert True\n")
    _commit(repo, "unrelated change")
    proc = _gate_to_regression(tmp_path, repo, base, "tests/specfactory/test_unrelated_ok.py")
    assert "GATE specfactory_regression OK" in proc.stdout, proc.stdout + proc.stderr


def test_gate_specfactory_regression_runs_after_the_csim_regressions():
    """Step order in merge_gate.sh: full profile only (after the --revert early return)."""
    text = GATE.read_text()
    assert "specfactory_regression" in text
    assert text.index("specfactory_regression") > text.index("regression_qa_t1")
    assert text.index("specfactory_regression") > text.index('"$REVERT_MODE" -eq 1')


# ------------------------------------------------------------ real repo (origin/main), red until implemented

def test_real_repo_sig_check_ok():
    proc = subprocess.run([PY, str(SUPPORT), "sig-check", "--project", str(REPO)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_real_repo_allowlist_strict_ok():
    proc = subprocess.run([PY, str(ALG), "--lint", str(REPO / "csrc"), "--strict"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_real_repo_gate_script_wires_all_three_steps():
    """The gate script names every pinned step and routes tests/specfactory through the
    regression subcommand with the candidate and base_ref (no pytest from inside this
    suite: it would recurse)."""
    text = GATE.read_text()
    for step in ("specfactory_regression", "sig_check", "allowlist_strict"):
        assert f" {step} " in text or f" {step}\"" in text or f"reject {step}" in text, step
    assert "tests/specfactory" in text
    assert "sig-check" in text
    assert "--strict" in text
