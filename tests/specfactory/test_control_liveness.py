"""PX-15: tests for scripts/specfactory/control_liveness.py (DECISIONS.md
R10 -- a positive control that behaves identically on the clean build and
its own debug-build injection is dead, whatever the reason). These exercise
bug_id_of() against synthetic files and the real controls' AST shapes, and
judge()'s pure LIVE/DEAD/ERROR decision over synthetic Outcome pairs and a
fake runner -- none of this compiles or runs the real C build.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "specfactory"))
import control_liveness as cl  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLS_DIR = REPO_ROOT / "tests" / "csim" / "controls"


# ---------------------------------------------------------------- bug_id_of --

def test_bug_id_of_parses_OMBug_member(tmp_path):
    f = tmp_path / "test_control_x.py"
    f.write_text(
        "from conftest import OMBug, OMTier, set_region\n\n\n"
        "def test_control_x_trips_the_detector(dbg, dbg_world_factory):\n"
        "    w = dbg_world_factory(n_regions=1)\n"
        "    dbg.om_debug_inject(w, OMBug.EMPTY_DRIFTS)\n"
        "    dbg.om_world_step(w)\n"
    )
    assert cl.bug_id_of(f) == "OMBug.EMPTY_DRIFTS"


def test_bug_id_of_parses_OMBugE05_member_inside_a_helper(tmp_path):
    f = tmp_path / "test_control_y.py"
    f.write_text(
        "from conftest import OMBugE05\n\n\n"
        "def _build(dbg, w, inject_bug):\n"
        "    if inject_bug:\n"
        "        dbg.om_debug_inject(w, OMBugE05.INJECT_IGNORED)\n"
        "    return w\n"
    )
    assert cl.bug_id_of(f) == "OMBugE05.INJECT_IGNORED"


def test_bug_id_of_returns_none_with_no_injection_call(tmp_path):
    f = tmp_path / "test_control_nothing.py"
    f.write_text("def test_x(dbg):\n    pass\n")
    assert cl.bug_id_of(f) is None


def test_bug_id_of_returns_none_on_syntax_error(tmp_path):
    f = tmp_path / "test_control_broken.py"
    f.write_text("def test_x(dbg:\n    pass\n")
    assert cl.bug_id_of(f) is None


@pytest.mark.parametrize("filename, expected", [
    ("test_control_empty_drifts.py", "OMBug.EMPTY_DRIFTS"),
    ("test_control_composite_pre_clamp.py", "OMBug.COMPOSITE_PRE_CLAMP"),
    ("test_control_ge_not_gt.py", "OMBug.GE_NOT_GT"),
    ("test_control_osc_as_level.py", "OMBug.OSC_AS_LEVEL"),
    ("test_control_raw_not_trend.py", "OMBug.RAW_NOT_TREND"),
    ("test_control_slow.py", "OMBug.SLOW"),
    ("test_control_e05_inject_ignored.py", "OMBugE05.INJECT_IGNORED"),
    ("test_control_e05_agent_reads_live.py", "OMBugE05.AGENT_READS_LIVE"),
    ("test_control_e05_garrison_before_damage.py", "OMBugE05.GARRISON_BEFORE_DAMAGE"),
    ("test_control_e05_telegraph_after_reinforce.py", "OMBugE05.TELEGRAPH_AFTER_REINFORCE"),
    ("test_control_e04_chain_counter_unsaved.py", "OMBugE04.CHAIN_COUNTER_UNSAVED"),
    ("test_control_e03_corridor_chaining_leaves_a_faction_unreachable.py",
     "OMBug.CORRIDOR_CHAINING_LEAVES_A_FACTION_UNREACHABLE"),
])
def test_bug_id_of_parses_real_control_shapes(filename, expected):
    path = CONTROLS_DIR / filename
    assert path.exists(), f"fenced control moved/renamed: {path}"
    assert cl.bug_id_of(path) == expected


# ---------------------------------------------------------------- judge --

def test_judge_live_when_outcomes_differ_pass_then_fail():
    verdict, reason = cl.judge(cl.Outcome("passed", ""), cl.Outcome("failed", "assert False"))
    assert verdict == "LIVE"
    assert "as-written=passed" in reason and "neutralized=failed" in reason


def test_judge_live_when_outcomes_differ_fail_then_pass():
    # Most controls PASS when the bug is injected (they assert "the detector
    # trips"), but judge() must not assume a direction.
    verdict, reason = cl.judge(cl.Outcome("failed", "assert 1 == 1"), cl.Outcome("passed", ""))
    assert verdict == "LIVE"


def test_judge_dead_when_both_fail_the_same_way():
    aw = cl.Outcome("failed", "assert 1 != 1")
    ne = cl.Outcome("failed", "assert 1 != 1")
    verdict, reason = cl.judge(aw, ne)
    assert verdict == "DEAD"


def test_judge_dead_when_both_pass():
    verdict, reason = cl.judge(cl.Outcome("passed", ""), cl.Outcome("passed", ""))
    assert verdict == "DEAD"


def test_judge_error_missing_enum_member_even_if_both_sides_agree():
    msg = "AttributeError: type object 'OMBug' has no attribute 'FOO'"
    aw = cl.Outcome("failed", msg)
    ne = cl.Outcome("failed", msg)
    verdict, reason = cl.judge(aw, ne)
    assert verdict == "ERROR"
    assert "missing enum member" in reason


def test_judge_error_missing_symbol_unbuilt_stub():
    msg = "AttributeError: /repo/libouroboros_dbg.so: undefined symbol: om_something_new"
    aw = cl.Outcome("failed", msg)
    ne = cl.Outcome("failed", msg)
    verdict, reason = cl.judge(aw, ne)
    assert verdict == "ERROR"
    assert "unbuilt stub" in reason


def test_judge_error_when_one_side_cannot_collect():
    aw = cl.Outcome("error", "collection error: ImportError: cannot import name 'foo'")
    ne = cl.Outcome("passed", "")
    verdict, reason = cl.judge(aw, ne)
    assert verdict == "ERROR"
    assert "collection error" in reason


def test_judge_error_skipped_is_unbuilt_stub():
    msg = "no csrc/*.c implementation yet; nothing to build"
    aw = cl.Outcome("skipped", msg)
    ne = cl.Outcome("skipped", msg)
    verdict, reason = cl.judge(aw, ne)
    assert verdict == "ERROR"
    assert "unbuilt stub" in reason


# ---------------------------------------------------------------- liveness() with a fake runner --

def test_liveness_live_via_fake_runner(tmp_path):
    f = tmp_path / "test_control_fake_live.py"
    f.write_text(
        "from conftest import OMBug\n\n"
        "def test_x(dbg):\n"
        "    dbg.om_debug_inject(dbg, OMBug.EMPTY_DRIFTS)\n"
    )

    def fake_runner(path):
        assert path == f
        return cl.Outcome("passed", ""), cl.Outcome("failed", "assert False")

    v = cl.liveness(f, run_pair=fake_runner)
    assert v.verdict == "LIVE"
    assert v.bug_id == "OMBug.EMPTY_DRIFTS"
    assert v.control == "test_control_fake_live.py"


def test_liveness_dead_via_fake_runner(tmp_path):
    f = tmp_path / "test_control_fake_dead.py"
    f.write_text(
        "from conftest import OMBugE05\n\n"
        "def test_x(dbg):\n"
        "    dbg.om_debug_inject(dbg, OMBugE05.TELEGRAPH_AFTER_REINFORCE)\n"
    )

    def fake_runner(path):
        return cl.Outcome("failed", "assert 1 != 1"), cl.Outcome("failed", "assert 1 != 1")

    v = cl.liveness(f, run_pair=fake_runner)
    assert v.verdict == "DEAD"
    assert v.bug_id == "OMBugE05.TELEGRAPH_AFTER_REINFORCE"


def test_liveness_error_via_fake_runner_cannot_collect(tmp_path):
    f = tmp_path / "test_control_fake_error.py"
    f.write_text("def test_x(dbg:\n    pass\n")  # deliberately unparsable

    def fake_runner(path):
        return (cl.Outcome("error", "collection error: SyntaxError: invalid syntax"),
                cl.Outcome("error", "collection error: SyntaxError: invalid syntax"))

    v = cl.liveness(f, run_pair=fake_runner)
    assert v.verdict == "ERROR"
    assert v.bug_id is None  # unparsable file: no call site found either


# ---------------------------------------------------------------- parse_junit --

def test_parse_junit_missing_file_returns_empty(tmp_path):
    assert cl.parse_junit(tmp_path / "does_not_exist.xml") == {}


def test_parse_junit_reads_pass_fail_error_skip(tmp_path):
    xml_path = tmp_path / "junit.xml"
    xml_path.write_text(
        '<?xml version="1.0"?>\n'
        '<testsuites>\n'
        '  <testsuite>\n'
        '    <testcase classname="tests.csim.controls.test_control_a" name="test_a"/>\n'
        '    <testcase classname="tests.csim.controls.test_control_b" name="test_b">\n'
        '      <failure message="AssertionError: boom">trace</failure>\n'
        '    </testcase>\n'
        '    <testcase classname="tests.csim.controls.test_control_c" name="test_c">\n'
        '      <error message="fixture setup failed">trace</error>\n'
        '    </testcase>\n'
        '    <testcase classname="tests.csim.controls.test_control_d" name="test_d">\n'
        '      <skipped message="no csrc/*.c">trace</skipped>\n'
        '    </testcase>\n'
        '  </testsuite>\n'
        '</testsuites>\n'
    )
    results = cl.parse_junit(xml_path)
    assert results["test_control_a.py"] == cl.Outcome("passed", "")
    assert results["test_control_b.py"].status == "failed"
    assert "boom" in results["test_control_b.py"].message
    assert results["test_control_c.py"].status == "error"
    assert results["test_control_d.py"].status == "skipped"
