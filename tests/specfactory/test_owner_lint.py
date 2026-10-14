# spec: docs/northstar/plans/witty-cuddling-goblet.md::Wave 0 item 3
"""Tests for scripts/specfactory/owner_lint.py (single-owner-in-flight gate)."""
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OWNER_LINT = REPO / "scripts" / "specfactory" / "owner_lint.py"

sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
import owner_lint as ol  # noqa: E402


def _write_pieces(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pieces.toml"
    path.write_text(body)
    return path


def _run(pieces_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(OWNER_LINT), "--pieces", str(pieces_path)],
        capture_output=True, text=True,
    )


def test_help():
    proc = subprocess.run([sys.executable, str(OWNER_LINT), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--pieces" in proc.stdout


def test_positive_control_two_in_flight_pieces_same_file_fails(tmp_path):
    """Planted violation: X and Y are both pending (in flight) and both own
    csrc/foo.c with no depends_on ordering between them -- exactly the race
    the single-owner rule exists to forbid."""
    pieces_toml = _write_pieces(tmp_path, """
[[piece]]
id = "X"
owns = ["csrc/foo.c"]
status = "pending"

[[piece]]
id = "Y"
owns = ["csrc/foo.c"]
status = "pending"
""")
    proc = _run(pieces_toml)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "X/Y" in proc.stdout
    assert "OWNER LINT FAILED (1 in-flight overlap(s))" in proc.stdout


def test_attached_piece_against_pending_piece_is_not_a_finding(tmp_path):
    """The in-flight filter's whole job: check_owns_disjoint alone would
    flag this (it counts attached pieces too), but an attached piece is
    already landed on main -- nothing races against it."""
    pieces_toml = _write_pieces(tmp_path, """
[[piece]]
id = "X"
owns = ["csrc/foo.c"]
status = { state = "attached", attach_sha = "abc1234" }

[[piece]]
id = "Y"
owns = ["csrc/foo.c"]
status = "pending"
""")
    proc = _run(pieces_toml)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OWNER LINT OK" in proc.stdout


def test_two_attached_pieces_same_file_is_not_a_finding(tmp_path):
    pieces_toml = _write_pieces(tmp_path, """
[[piece]]
id = "X"
owns = ["csrc/foo.c"]
status = { state = "attached", attach_sha = "abc1234" }

[[piece]]
id = "Y"
owns = ["csrc/foo.c"]
status = { state = "attached", attach_sha = "def5678" }
""")
    proc = _run(pieces_toml)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_depends_on_ordering_still_exempt_even_in_flight(tmp_path):
    """check_owns_disjoint's own depends_on exemption is untouched: two
    in-flight pieces sharing a file is fine when one depends on the other
    (a wave-3 follow-up sequenced after its base piece)."""
    pieces_toml = _write_pieces(tmp_path, """
[[piece]]
id = "B5"
owns = ["csrc/diplomacy.c"]
status = "pending"

[[piece]]
id = "B5b"
owns = ["csrc/diplomacy.c"]
depends_on = ["B5"]
status = "pending"
""")
    proc = _run(pieces_toml)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_is_in_flight_status_shapes():
    assert ol.is_in_flight({"status": "pending"}) is True
    assert ol.is_in_flight({}) is True
    assert ol.is_in_flight({"status": {"state": "attached", "attach_sha": "x"}}) is False
    assert ol.is_in_flight({"status": "done"}) is False
    assert ol.is_in_flight({"status": {"state": "done"}}) is False


def test_real_pieces_toml_on_main_is_clean():
    real_pieces = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"
    data = tomllib.loads(real_pieces.read_text())
    findings = ol.in_flight_overlaps(list(data.get("piece", [])))
    assert findings == [], findings


# Architect 2026-10-14, HARNESS-westley-folder: docs/northstar/story_reviews/westley/* is a
# shared record like the ledger: no piece owns it, so two in-flight pieces listing it are no
# overlap. See also: pieces.SHARED_RECORD_GLOBS, test_merge_gate_support.py::
# test_westley_folder_files_are_not_a_footprint.
def test_westley_folder_listed_by_two_in_flight_pieces_is_not_a_finding(tmp_path):
    # Positive control first: an ordinary file listed twice with no ordering still fails.
    control_toml = _write_pieces(tmp_path, """
[[piece]]
id = "X"
owns = ["docs/northstar/story_reviews/A.md"]
status = "pending"

[[piece]]
id = "Y"
owns = ["docs/northstar/story_reviews/A.md"]
status = "pending"
""")
    control = _run(control_toml)
    assert control.returncode == 1, control.stdout + control.stderr

    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    pieces_toml = _write_pieces(shared_dir, """
[[piece]]
id = "X"
owns = ["docs/northstar/story_reviews/westley/README.md", "docs/northstar/story_reviews/westley/A-S1-x.png"]
status = "pending"

[[piece]]
id = "Y"
owns = ["docs/northstar/story_reviews/westley/README.md"]
owns_glob = ["docs/northstar/story_reviews/westley/**"]
status = "pending"
""")
    proc = _run(pieces_toml)
    assert proc.returncode == 0, proc.stdout + proc.stderr
