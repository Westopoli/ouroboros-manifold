# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md, item 4
"""Tests for scripts/specfactory/pieces.py (validates
docs/northstar/plans/push/pieces.toml)."""
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import pieces as pc  # noqa: E402

PIECES_TOML = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"


def test_positive_control_duplicate_id_fails():
    findings = pc.check_unique_ids([{"id": "B1"}, {"id": "B2"}, {"id": "B1"}])
    fails = [f for f in findings if f[0] == "FAIL"]
    assert len(fails) == 1
    assert "B1" in fails[0][1]


def test_unique_ids_clean():
    findings = pc.check_unique_ids([{"id": "B1"}, {"id": "B2"}])
    assert findings == []


def test_positive_control_owns_overlap_with_no_ordering_fails():
    pieces = [
        {"id": "X", "owns": ["csrc/foo.c"], "depends_on": []},
        {"id": "Y", "owns": ["csrc/foo.c"], "depends_on": []},
    ]
    findings = pc.check_owns_disjoint(pieces)
    fails = [f for f in findings if f[0] == "FAIL"]
    assert len(fails) == 1


def test_owns_overlap_allowed_when_sequenced_by_depends_on():
    pieces = [
        {"id": "B5", "owns": ["csrc/diplomacy.c"], "depends_on": []},
        {"id": "B5b", "owns": ["csrc/diplomacy.c"], "depends_on": ["B5"]},
    ]
    findings = pc.check_owns_disjoint(pieces)
    assert findings == []


def test_owns_overlap_allowed_transitively():
    pieces = [
        {"id": "A", "owns": ["csrc/foo.c"], "depends_on": []},
        {"id": "B", "owns": [], "depends_on": ["A"]},
        {"id": "C", "owns": ["csrc/foo.c"], "depends_on": ["B"]},
    ]
    findings = pc.check_owns_disjoint(pieces)
    assert findings == []


def test_owns_glob_overlap_detected():
    pieces = [
        {"id": "X", "owns_glob": ["scenes/galaxy/**"], "depends_on": []},
        {"id": "Y", "owns": ["scenes/galaxy/view.gd"], "depends_on": []},
    ]
    findings = pc.check_owns_disjoint(pieces)
    fails = [f for f in findings if f[0] == "FAIL"]
    assert len(fails) == 1


def test_owns_disjoint_no_overlap_is_clean():
    pieces = [
        {"id": "X", "owns": ["csrc/a.c"], "depends_on": []},
        {"id": "Y", "owns": ["csrc/b.c"], "depends_on": []},
    ]
    assert pc.check_owns_disjoint(pieces) == []


def test_patterns_overlap_disjoint_prefixes_false():
    assert pc.patterns_overlap("scenes/galaxy/**", "scenes/tactical_c/**") is False


def test_patterns_overlap_exact_match_true():
    assert pc.patterns_overlap("csrc/foo.c", "csrc/foo.c") is True


def test_transitive_depends_follows_chain():
    by_id = {
        "A": {"depends_on": []},
        "B": {"depends_on": ["A"]},
        "C": {"depends_on": ["B"]},
    }
    assert pc.transitive_depends(by_id, "C") == {"A", "B"}


def test_transitive_depends_tolerates_unknown_dep():
    by_id = {"A": {"depends_on": ["freeze"]}}
    assert pc.transitive_depends(by_id, "A") == {"freeze"}


def test_root_of_recognises_known_roots():
    assert pc._root_of("tests/csim/test_x.py") == "tests/csim"
    assert pc._root_of("tests/qa/t1/test_y.py") == "tests/qa/t1"
    assert pc._root_of("tests/transport") == "tests/transport"
    assert pc._root_of("scenes/foo.gd") is None


def test_acceptance_missing_gd_file_fails(tmp_path):
    (tmp_path / "tests").mkdir()
    pieces = [{"id": "C7", "acceptance": ["tests/test_missing.gd"]}]
    findings = pc.check_acceptance(pieces, tmp_path)
    assert findings == [("FAIL", "C7", "acceptance godot script missing: tests/test_missing.gd")]


def test_acceptance_missing_gd_file_warns_when_tests_pending(tmp_path):
    pieces = [{"id": "C2", "acceptance": ["tests/test_missing.gd"], "tests_pending": True}]
    findings = pc.check_acceptance(pieces, tmp_path)
    assert findings == [("WARN", "C2", "acceptance godot script missing: tests/test_missing.gd")]


def test_acceptance_present_gd_file_clean(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_present.gd").write_text("extends SceneTree\n")
    pieces = [{"id": "C7", "acceptance": ["tests/test_present.gd"]}]
    assert pc.check_acceptance(pieces, tmp_path) == []


def test_acceptance_missing_pytest_path_fails(tmp_path):
    pieces = [{"id": "B1", "acceptance": ["tests/csim/test_nope.py"]}]
    findings = pc.check_acceptance(pieces, tmp_path)
    assert findings == [("FAIL", "B1", "acceptance path does not exist: tests/csim/test_nope.py")]


def test_acceptance_missing_pytest_path_warns_when_pending(tmp_path):
    pieces = [{"id": "T2c", "acceptance": ["tests/csim/test_nope.py"], "tests_pending": True}]
    findings = pc.check_acceptance(pieces, tmp_path)
    assert findings == [("WARN", "T2c", "acceptance path does not exist: tests/csim/test_nope.py")]


def test_acceptance_unrecognised_root_warns(tmp_path):
    pieces = [{"id": "Q1", "acceptance": ["agora/projects/ouroboros/qa.toml"]}]
    findings = pc.check_acceptance(pieces, tmp_path)
    assert len(findings) == 1 and findings[0][0] == "WARN"


def test_acceptance_collector_injected_success(tmp_path):
    csim = tmp_path / "tests" / "csim"
    csim.mkdir(parents=True)
    (csim / "test_a.py").write_text("def test_a(): pass\n")
    pieces = [{"id": "B1", "acceptance": ["tests/csim/test_a.py"]}]
    calls = []

    def fake_collector(node_ids, root):
        calls.append((tuple(node_ids), root))
        return 0, ""

    findings = pc.check_acceptance(pieces, tmp_path, collector=fake_collector)
    assert findings == []
    assert calls == [(("tests/csim/test_a.py",), "tests/csim")]


def test_collector_collection_error_warns_when_tests_pending(tmp_path):
    """A fenced test the design lane writes ahead of a piece's own build
    (e.g. it imports scripts.qa.rts_detectors, which does not exist yet)
    fails to COLLECT, not just fails an assertion -- for a tests_pending
    piece this is expected redness, not a defect."""
    csim = tmp_path / "tests" / "csim"
    csim.mkdir(parents=True)
    (csim / "test_a.py").write_text("def test_a(): pass\n")
    pieces = [{"id": "Q2", "acceptance": ["tests/csim/test_a.py"], "tests_pending": True}]

    def fake_collector(node_ids, root):
        return 2, "ERROR tests/csim/test_a.py\n"

    findings = pc.check_acceptance(pieces, tmp_path, collector=fake_collector)
    assert findings == [("WARN", "Q2", "acceptance id did not collect (tests/csim batch rc=2): tests/csim/test_a.py")]


def test_positive_control_collector_reports_collection_error(tmp_path):
    csim = tmp_path / "tests" / "csim"
    csim.mkdir(parents=True)
    (csim / "test_a.py").write_text("def test_a(): pass\n")
    pieces = [{"id": "B1", "acceptance": ["tests/csim/test_a.py"]}]

    def fake_collector(node_ids, root):
        return 2, "ERROR tests/csim/test_a.py\n"

    findings = pc.check_acceptance(pieces, tmp_path, collector=fake_collector)
    assert len(findings) == 1
    assert findings[0][0] == "FAIL"
    assert "B1" in findings[0][1]


def test_acceptance_never_mixes_csim_and_qa_t1_in_one_collector_call(tmp_path):
    csim = tmp_path / "tests" / "csim"
    qa = tmp_path / "tests" / "qa" / "t1"
    csim.mkdir(parents=True)
    qa.mkdir(parents=True)
    (csim / "test_a.py").write_text("def test_a(): pass\n")
    (qa / "test_b.py").write_text("def test_b(): pass\n")
    pieces = [
        {"id": "B1", "acceptance": ["tests/csim/test_a.py"]},
        {"id": "Q2", "acceptance": ["tests/qa/t1/test_b.py"]},
    ]
    seen_roots = []

    def fake_collector(node_ids, root):
        seen_roots.append((root, tuple(node_ids)))
        return 0, ""

    pc.check_acceptance(pieces, tmp_path, collector=fake_collector)
    assert sorted(seen_roots) == [
        ("tests/csim", ("tests/csim/test_a.py",)),
        ("tests/qa/t1", ("tests/qa/t1/test_b.py",)),
    ]


def test_pieces_toml_parses_and_has_unique_ids():
    pieces = pc.load_pieces(PIECES_TOML)
    assert len(pieces) > 0
    findings = pc.check_unique_ids(pieces)
    assert findings == []


def test_pieces_toml_is_valid_toml():
    data = tomllib.loads(PIECES_TOML.read_text())
    assert "piece" in data
