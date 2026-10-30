# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 27, A68 (harness half)
"""The merge gate runs `sig_table --report` and rejects on any BLOCKED item.

Contract these tests pin (the implementation does not exist yet, so all are red):
  - merge_gate_support.sig_blocked_check(project, table) -> (ok, detail), ok False
    iff `sig_table --report` for that project/table lists a BLOCKED item;
    detail carries the BLOCKED lines.
  - `merge_gate_support.py sig-blocked [--project DIR] [--table PATH]` prints the
    detail and exits 1 on BLOCKED, 0 otherwise.
  - merge_gate.sh prints `GATE sig_blocked OK|REJECT <detail>`, passing
    --project "$REPO_ROOT" --table "$SIGNATURES_TOML", and SIGNATURES_TOML honours
    the env override MERGE_GATE_SIGNATURES (default: the repo's signatures.toml).
Each test builds its own temp table; none depends on the real table's state.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GATE = REPO / "scripts" / "specfactory" / "merge_gate.sh"
SUPPORT = REPO / "scripts" / "specfactory" / "merge_gate_support.py"
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_toy_root import write_story  # noqa: E402

import merge_gate_support as mgs  # noqa: E402

CLEAN_ROW = '''[[symbols]]
name = "om_gatetest_clean_probe"
module = "chronicle.c"
restype = "uint32_t"
params = [{ name = "w", ctype = "const om_world*" }, { name = "index", ctype = "uint32_t" }]
epics = ["E-09"]
confidence = "likely"
note = "test fixture"
'''

# A pointer to a type neither the header nor the table's [[structs]] declares:
# the same shape om_chronicle_mention_get had before A68.
UNMAPPABLE_ROW = '''[[symbols]]
name = "om_gatetest_unmappable_probe"
module = "chronicle.c"
restype = "int"
params = [{ name = "w", ctype = "const om_world*" }, { name = "out", ctype = "om_gatetest_no_such_struct*" }]
epics = ["E-09"]
confidence = "likely"
note = "test fixture: planted unmappable parameter"
'''

META = "[meta]\nabi_version = 2\nsymbol_count = 1\nstruct_count = 0\nambiguous_remaining = 0\n\n"


def _table(tmp_path: Path, *rows: str) -> Path:
    p = tmp_path / "signatures.toml"
    p.write_text(META + "\n".join(rows))
    return p


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _sig_report(table: Path) -> str:
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "specfactory" / "sig_table.py"),
         "--project", str(REPO), "--table", str(table), "--report"],
        capture_output=True, text=True).stdout


def test_control_planted_table_really_reports_blocked(tmp_path):
    """The fixture itself: sig_table lists the planted row and not the clean one."""
    assert "BLOCKED" in _sig_report(_table(tmp_path, UNMAPPABLE_ROW))
    assert "BLOCKED" not in _sig_report(_table(tmp_path, CLEAN_ROW))


def test_sig_blocked_check_rejects_a_blocked_item(tmp_path):
    ok, detail = mgs.sig_blocked_check(REPO, _table(tmp_path, UNMAPPABLE_ROW))
    assert ok is False
    assert "om_gatetest_unmappable_probe" in detail


def test_sig_blocked_check_passes_a_clean_table(tmp_path):
    ok, detail = mgs.sig_blocked_check(REPO, _table(tmp_path, CLEAN_ROW))
    assert ok is True, detail


def test_sig_blocked_cli_exit_codes(tmp_path):
    def run(table: Path):
        return subprocess.run(
            [sys.executable, str(SUPPORT), "sig-blocked", "--project", str(REPO), "--table", str(table)],
            capture_output=True, text=True)
    bad = run(_table(tmp_path, UNMAPPABLE_ROW))
    assert bad.returncode == 1 and "om_gatetest_unmappable_probe" in bad.stdout + bad.stderr
    good = run(_table(tmp_path, CLEAN_ROW))
    assert good.returncode == 0, good.stdout + good.stderr


def _gate(tmp_path: Path, table: Path) -> subprocess.CompletedProcess:
    repo = tmp_path / "cand"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "stub.c").write_text("int om_stub(void) { return 0; }\n")
    (repo / "Makefile").write_text("libouroboros.so:\n\ttouch $@\nlibouroboros_dbg.so:\n\ttouch $@\n")
    (repo / "tests" / "csim").mkdir(parents=True)
    write_story(repo, "B1")  # H-020
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/stub.c"]\nacceptance = []\ndepends_on = []\n')
    env = {"MERGE_GATE_PIECES": str(pieces), "MERGE_GATE_SIGNATURES": str(table),
           "PATH": "/usr/bin:/bin:/home/westopoli/Projects/agora/.venv/bin"}
    return subprocess.run(["bash", str(GATE), str(repo), "HEAD", "B1"],
                          capture_output=True, text=True, env=env, timeout=120)


def test_gate_step_exists_and_rejects_a_blocked_table(tmp_path):
    proc = _gate(tmp_path, _table(tmp_path, UNMAPPABLE_ROW))
    assert "GATE sig_blocked REJECT" in proc.stdout, proc.stdout + proc.stderr
    assert proc.returncode == 1


def test_gate_step_passes_a_clean_table(tmp_path):
    proc = _gate(tmp_path, _table(tmp_path, CLEAN_ROW))
    assert "GATE sig_blocked OK" in proc.stdout, proc.stdout + proc.stderr
