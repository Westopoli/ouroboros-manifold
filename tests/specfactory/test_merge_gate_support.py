# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md, item 1
"""Tests for scripts/specfactory/merge_gate_support.py (the footprint fence
and symbol-ownership lint merge_gate.sh calls into)."""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402
import suite_regression as sr  # noqa: E402


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(base_dir: Path) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 0; }\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "rev-parse", "HEAD")
    return repo


def _write_pieces(path: Path, pieces: list[dict]) -> None:
    lines = []
    for p in pieces:
        lines.append("[[piece]]")
        lines.append(f'id = "{p["id"]}"')
        owns = p.get("owns", [])
        lines.append("owns = [" + ", ".join(f'"{o}"' for o in owns) + "]")
        owns_glob = p.get("owns_glob", [])
        if owns_glob:
            lines.append("owns_glob = [" + ", ".join(f'"{o}"' for o in owns_glob) + "]")
        lines.append("")
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------- footprint_check --

def test_positive_control_extra_file_rejected(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])

    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 1; }\n")
    (repo / "tests_edit.py").write_text("x = 1\n")  # outside owns
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is False
    assert "tests_edit.py" in detail


def test_clean_diff_within_owns_accepted(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])

    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 1; }\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is True
    assert detail == "OK"


def test_ignored_paths_never_count_against_the_fence(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])

    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 1; }\n")
    (repo / ".swarm").mkdir()
    (repo / ".swarm" / "note.md").write_text("scratch\n")
    (repo / "logs").mkdir()
    (repo / "logs" / "sim_stderr.log").write_text("noise\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert ok is True
    assert detail == "OK"


def test_gd_uid_sidecar_counts_as_its_gd_file(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "C7", "owns": ["autoload/qa_daemon.gd"]}])

    (repo / "autoload").mkdir()
    (repo / "autoload" / "qa_daemon.gd.uid").write_text("uid://abc\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "C7", pieces_path=pieces)
    assert ok is True, detail


def test_owns_glob_matches(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "C2", "owns_glob": ["scenes/galaxy/**"]}])

    (repo / "scenes" / "galaxy").mkdir(parents=True)
    (repo / "scenes" / "galaxy" / "view.gd").write_text("extends Node\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "C2", pieces_path=pieces)
    assert ok is True, detail


def test_footprint_check_accepts_comma_separated_piece_ids_union(tmp_path):
    """merge_cli.py revert: a piece plus its dependants revert together in
    one candidate, so the fence checks the union of their owns."""
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [
        {"id": "B10", "owns": ["csrc/unit.c"]},
        {"id": "B11", "owns": ["csrc/fog.c"]},
    ])
    (repo / "csrc" / "unit.c").write_text("int om_unit_stub(void) { return 0; }\n")
    (repo / "csrc" / "fog.c").write_text("int om_fog_stub(void) { return 0; }\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B10,B11", pieces_path=pieces)
    assert ok is True, detail


def test_unknown_piece_id_rejected(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])
    ok, detail = mgs.footprint_check(repo, "HEAD", "NOPE", pieces_path=pieces)
    assert ok is False
    assert "NOPE" in detail


# ---------------------------------------------------------------- resolve_piece_id --

def test_footprint_check_increment_id_resolves_to_base_piece(tmp_path):
    """A straggler leaf pushes an increment as `push/C2-1`; the footprint
    fence resolves `C2-1` to `C2` and checks against C2's owns."""
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "C2", "owns_glob": ["scenes/galaxy/**"]}])

    (repo / "scenes" / "galaxy").mkdir(parents=True)
    (repo / "scenes" / "galaxy" / "view.gd").write_text("extends Node\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "C2-1", pieces_path=pieces)
    assert ok is True, detail


def test_footprint_check_b15m_id_unchanged(tmp_path):
    """B15m has no trailing `-<digits>`, so resolution must leave it as-is
    rather than mistaking its own name for an increment suffix."""
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B15m", "owns": ["csrc/events.c"]}])

    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 1; }\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.footprint_check(repo, "HEAD~1", "B15m", pieces_path=pieces)
    assert ok is True, detail


def test_footprint_check_increment_id_with_no_base_piece_still_unknown(tmp_path):
    """`Z9-1` strips to `Z9`, which is not a piece either -- still rejected
    as unknown, not silently accepted."""
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])
    ok, detail = mgs.footprint_check(repo, "HEAD", "Z9-1", pieces_path=pieces)
    assert ok is False
    assert "Z9-1" in detail


# ---------------------------------------------------------------- gd_class_names_check --

def test_positive_control_duplicate_class_name_rejected_with_both_paths(tmp_path):
    """2026-09-22 defect: GalaxyGen declared in two scripts on main; a
    `--script` test run in a fresh worktree does not catch this, but
    Godot's global class registry does once a project imports both."""
    root = tmp_path / "tree"
    (root / "scenes" / "galaxy").mkdir(parents=True)
    (root / "scenes" / "mockups" / "galaxy").mkdir(parents=True)
    (root / "scenes" / "galaxy" / "galaxy_gen.gd").write_text(
        "class_name GalaxyGen\nextends Node\n"
    )
    (root / "scenes" / "mockups" / "galaxy" / "galaxy_gen.gd").write_text(
        "class_name GalaxyGen\nextends Node2D\n"
    )

    ok, detail = mgs.gd_class_names_check(root)
    assert ok is False
    assert "GalaxyGen" in detail
    assert "scenes/galaxy/galaxy_gen.gd" in detail
    assert "scenes/mockups/galaxy/galaxy_gen.gd" in detail


def test_unique_class_names_pass(tmp_path):
    root = tmp_path / "tree"
    (root / "scenes").mkdir(parents=True)
    (root / "scenes" / "a.gd").write_text("class_name GalaxyGen\nextends Node\n")
    (root / "scenes" / "b.gd").write_text("class_name FogView\nextends Node\n")

    ok, detail = mgs.gd_class_names_check(root)
    assert ok is True
    assert "2 classes unique" in detail


def test_class_name_in_comment_or_string_not_counted(tmp_path):
    root = tmp_path / "tree"
    root.mkdir(parents=True)
    (root / "a.gd").write_text(
        "# class_name GalaxyGen\n"
        "extends Node\n"
        'var note = "class_name GalaxyGen"\n'
    )
    (root / "b.gd").write_text("class_name GalaxyGen\nextends Node2D\n")

    ok, detail = mgs.gd_class_names_check(root)
    assert ok is True
    assert "1 classes unique" in detail


def test_ignored_dirs_never_double_count_a_class(tmp_path):
    """merge worktrees live under runs/merge/ in the integrator clone, and
    any ad hoc worktree carries a `worktrees/` path component -- both are
    full second copies of the tree and must not double every class."""
    root = tmp_path / "tree"
    (root / "scenes").mkdir(parents=True)
    (root / "scenes" / "a.gd").write_text("class_name GalaxyGen\nextends Node\n")
    (root / "runs" / "merge" / "scenes").mkdir(parents=True)
    (root / "runs" / "merge" / "scenes" / "a.gd").write_text("class_name GalaxyGen\nextends Node\n")
    (root / ".swarm" / "worktrees" / "leaf-01" / "scenes").mkdir(parents=True)
    (root / ".swarm" / "worktrees" / "leaf-01" / "scenes" / "a.gd").write_text(
        "class_name GalaxyGen\nextends Node\n"
    )
    (root / "build" / "scenes").mkdir(parents=True)
    (root / "build" / "scenes" / "a.gd").write_text("class_name GalaxyGen\nextends Node\n")
    (root / ".godot" / "scenes").mkdir(parents=True)
    (root / ".godot" / "scenes" / "a.gd").write_text("class_name GalaxyGen\nextends Node\n")

    ok, detail = mgs.gd_class_names_check(root)
    assert ok is True, detail
    assert "1 classes unique" in detail


# ---------------------------------------------------------------- acceptance_ids --

def test_acceptance_ids_splits_pytest_and_godot(tmp_path):
    """2026-09-22 defect: a client piece's acceptance mixing pytest node ids
    and Godot test scripts (C2: tests/test_c_bridge.gd, tests/test_galaxy_view.gd
    plus a pytest id) must split into the two lists merge_gate.sh runs
    through different tools."""
    pieces = tmp_path / "pieces.toml"
    pieces.write_text(
        '[[piece]]\n'
        'id = "C2"\n'
        'owns = []\n'
        'acceptance = ["tests/test_c_bridge.gd", "tests/test_galaxy_view.gd", '
        '"tests/csim/test_E04_wiring.py", "tests/csim/test_x.py::test_specific"]\n'
    )
    pytest_ids, godot_ids = mgs.acceptance_ids("C2", pieces_path=pieces)
    assert pytest_ids == ["tests/csim/test_E04_wiring.py", "tests/csim/test_x.py::test_specific"]
    assert godot_ids == ["tests/test_c_bridge.gd", "tests/test_galaxy_view.gd"]


def test_acceptance_ids_pure_godot_piece(tmp_path):
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "C7"\nowns = []\nacceptance = ["tests/test_qa_daemon.gd"]\n')
    pytest_ids, godot_ids = mgs.acceptance_ids("C7", pieces_path=pieces)
    assert pytest_ids == []
    assert godot_ids == ["tests/test_qa_daemon.gd"]


def test_acceptance_ids_unknown_piece_returns_empty(tmp_path):
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B1"\nowns = []\nacceptance = []\n')
    pytest_ids, godot_ids = mgs.acceptance_ids("NOPE", pieces_path=pieces)
    assert pytest_ids == []
    assert godot_ids == []


def test_acceptance_ids_increment_id_resolves_to_base_piece(tmp_path):
    pieces = tmp_path / "pieces.toml"
    pieces.write_text(
        '[[piece]]\n'
        'id = "C2"\n'
        'owns = []\n'
        'acceptance = ["tests/csim/test_E04_wiring.py", "tests/test_c_bridge.gd"]\n'
    )
    pytest_ids, godot_ids = mgs.acceptance_ids("C2-1", pieces_path=pieces)
    assert pytest_ids == ["tests/csim/test_E04_wiring.py"]
    assert godot_ids == ["tests/test_c_bridge.gd"]


def test_acceptance_ids_b15m_unchanged(tmp_path):
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B15m"\nowns = []\nacceptance = ["tests/csim/test_x.py"]\n')
    pytest_ids, godot_ids = mgs.acceptance_ids("B15m", pieces_path=pieces)
    assert pytest_ids == ["tests/csim/test_x.py"]
    assert godot_ids == []


# ---------------------------------------------------------------- DEF_RE / _diff_added_definitions --

def test_positive_control_def_re_return_type_variants(tmp_path):
    """DEF_RE's return-type prefix class must cover digits and pointer
    stars (uint32_t, const-pointer, static-qualified) so real C
    definitions are not silently missed, while a call embedded in an
    assignment or a bare `return` statement is still excluded."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "csrc" / "scratch.c").write_text(
        "uint32_t om_a(void) { return 0; }\n"
        "const om_region *om_b(void) { return 0; }\n"
        "static uint64_t om_c(void) { return 0; }\n"
        "int om_container(void) {\n"
        "    uint32_t n = om_d(0);\n"
        "return om_e(0);\n"
        "}\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    defs = mgs._diff_added_definitions(repo, "HEAD~1")
    symbols = {sym for _, sym in defs}
    assert {"om_a", "om_b", "om_c"} <= symbols
    assert "om_d" not in symbols
    assert "om_e" not in symbols


# ---------------------------------------------------------------- symbol_ownership_check --

def _write_signatures(path: Path, rows: list[tuple[str, str]]) -> None:
    lines = []
    for name, module in rows:
        lines.append("[[symbols]]")
        lines.append(f'name = "{name}"')
        lines.append(f'module = "{module}"')
        lines.append("")
    path.write_text("\n".join(lines))


def test_positive_control_symbol_defined_in_wrong_module_rejected(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    _write_signatures(sigs, [("om_event_fire_manual", "events.c")])
    empty_sm = tmp_path / "symbol_modules.toml"
    empty_sm.write_text("[symbols]\n")

    (repo / "csrc" / "diplomacy.c").write_text(
        "int om_event_fire_manual(void) { return 0; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=empty_sm)
    assert ok is False
    assert "om_event_fire_manual" in detail
    assert "diplomacy.c" in detail
    assert "events.c" in detail


def test_positive_control_pointer_return_type_wrong_module_rejected(tmp_path):
    """Mirrors test_positive_control_symbol_defined_in_wrong_module_rejected
    but with a return type (uint32_t, pointer arg) the pre-fix DEF_RE
    (no digits/no `*` in its type-prefix class) silently missed --
    csrc/collision.c gaining a friction.c-owned symbol must still reject."""
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    _write_signatures(sigs, [("om_step_friction", "friction.c")])
    empty_sm = tmp_path / "symbol_modules.toml"
    empty_sm.write_text("[symbols]\n")

    (repo / "csrc" / "collision.c").write_text(
        "uint32_t om_step_friction(const om_world *w) { return 0; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=empty_sm)
    assert ok is False
    assert "om_step_friction" in detail
    assert "collision.c" in detail
    assert "friction.c" in detail


def test_symbol_defined_in_correct_module_accepted(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    _write_signatures(sigs, [("om_event_fire_manual", "events.c")])
    empty_sm = tmp_path / "symbol_modules.toml"
    empty_sm.write_text("[symbols]\n")

    (repo / "csrc" / "events.c").write_text(
        "int om_event_stub(void) { return 0; }\n"
        "int om_event_fire_manual(void) { return 1; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=empty_sm)
    assert ok is True, detail


def test_unknown_symbol_is_skipped_not_rejected(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    _write_signatures(sigs, [])
    empty_sm = tmp_path / "symbol_modules.toml"
    empty_sm.write_text("[symbols]\n")

    (repo / "csrc" / "events.c").write_text(
        "static int om_event_internal_helper(void) { return 0; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=empty_sm)
    assert ok is True
    assert "not checked" in detail


def test_symbol_modules_override_applies(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    sigs.write_text("")
    sm = tmp_path / "symbol_modules.toml"
    sm.write_text('[symbols]\nom_faction_create_breakaway = "diplomacy.c"\n')

    (repo / "csrc" / "diplomacy.c").write_text(
        "int om_faction_create_breakaway(void) { return 0; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=sm)
    assert ok is True, detail


def test_no_om_definitions_in_diff_is_clean(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    sigs = tmp_path / "signatures.toml"
    sigs.write_text("")
    sm = tmp_path / "symbol_modules.toml"
    sm.write_text("[symbols]\n")

    (repo / "README.md").write_text("docs only\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=sigs,
                                             symbol_modules_path=sm)
    assert ok is True
    assert "no om_* definitions" in detail


# ---------------------------------------------------------------- undertest_warn --

def test_undertest_warn_unknown_piece_skips(tmp_path):
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])
    lines = mgs.undertest_warn(tmp_path, "HEAD", "NOPE", pieces_path=pieces)
    assert len(lines) == 1 and "unknown piece id" in lines[0]


def test_undertest_warn_no_acceptance_skips(tmp_path):
    pieces = tmp_path / "pieces.toml"
    pieces.write_text('[[piece]]\nid = "B1"\nowns = ["csrc/events.c"]\nacceptance = []\n')
    lines = mgs.undertest_warn(tmp_path, "HEAD", "B1", pieces_path=pieces)
    assert len(lines) == 1 and "no pytest acceptance ids" in lines[0]


def test_undertest_warn_no_own_definition_skips(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    pieces.write_text(
        '[[piece]]\nid = "B1"\nowns = ["csrc/events.c"]\n'
        'acceptance = ["tests/csim/test_x.py"]\n'
    )
    (repo / "README.md").write_text("docs\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")
    lines = mgs.undertest_warn(repo, "HEAD~1", "B1", pieces_path=pieces)
    assert len(lines) == 1 and "no new/changed" in lines[0]


# ---------------------------------------------------------------- regression_check --

def _init_pytest_repo(base_dir: Path, *, test_text: str) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "test_synth.py").write_text(test_text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


PYTHON = sr.DEFAULT_PYTHON
GOOD_TEST = "def test_a():\n    assert 1 == 1\n"
BAD_TEST = "def test_a():\n    assert 1 == 1\n\ndef test_b():\n    assert 1 == 2\n"


def test_positive_control_worktree_path_noise_never_looks_like_a_changed_assertion(tmp_path):
    """Real incident found building the F6 rejection replays: a ctypes
    AttributeError's text embeds the .so's own absolute path
    (".../libouroboros.so: undefined symbol: ..."), which is unique to each
    of the before/after worktrees by construction -- a pure no-op diff over
    a file that only ever raises that AttributeError must never be flagged
    as a changed assertion just because the two worktree paths differ."""
    repo = _init_pytest_repo(tmp_path / "repo", test_text=(
        "import pathlib\n"
        "def test_a():\n"
        "    here = pathlib.Path(__file__).resolve().parent\n"
        "    raise AttributeError(f'{here}/lib.so: undefined symbol: om_x')\n"
    ))
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "README.md").write_text("docs only\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs-only candidate")

    ok, detail, report = mgs.regression_check(repo, base_sha, ["test_synth.py"],
                                               python_exe=PYTHON, worktree_root=tmp_path)
    assert ok is True, detail
    assert report.changed_assertions == []


def test_positive_control_regression_check_rejects_new_failure(tmp_path):
    repo = _init_pytest_repo(tmp_path / "repo", test_text=GOOD_TEST)
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "test_synth.py").write_text(BAD_TEST)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail, report = mgs.regression_check(repo, base_sha, ["test_synth.py"],
                                               python_exe=PYTHON, worktree_root=tmp_path,
                                               junit=False)
    assert ok is False
    assert "test_b" in detail
    assert report.new_failures == ["test_synth.py::test_b"]


def test_regression_check_accepts_clean_candidate(tmp_path):
    repo = _init_pytest_repo(tmp_path / "repo", test_text=GOOD_TEST)
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (repo / "README.md").write_text("docs only\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    ok, detail, report = mgs.regression_check(repo, base_sha, ["test_synth.py"],
                                               python_exe=PYTHON, worktree_root=tmp_path,
                                               junit=False)
    assert ok is True, detail
    assert report.new_failures == []


def test_regression_check_removes_its_worktree(tmp_path):
    repo = _init_pytest_repo(tmp_path / "repo", test_text=GOOD_TEST)
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    mgs.regression_check(repo, base_sha, ["test_synth.py"], python_exe=PYTHON,
                          worktree_root=tmp_path, junit=False)
    listing = _git(repo, "worktree", "list").stdout
    assert "merge_gate_before_" not in listing


def test_cli_footprint_exit_codes(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    pieces = tmp_path / "pieces.toml"
    _write_pieces(pieces, [{"id": "B1", "owns": ["csrc/events.c"]}])
    (repo / "csrc" / "events.c").write_text("int om_event_stub(void) { return 1; }\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate")

    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "specfactory" / "merge_gate_support.py"),
         "footprint", str(repo), "HEAD~1", "B1", "--pieces", str(pieces)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("OK")
