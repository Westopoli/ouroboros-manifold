# spec: CLAUDE.md "merge gate": every landing is checked against a scripted playthrough.
"""Positive control for the merge gate's playthrough stage: it must fail when the
flow breaks. The suite under test is a planted tmp test file (target=), so no game
code is edited; the real desktop suite is exercised by running the stage itself."""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import merge_gate_support as mgs  # noqa: E402

PY = sys.executable


def _run(tmp_path, body, known=""):
    (tmp_path / "test_flow_planted.py").write_text(body)
    kr = tmp_path / "known_red.txt"
    kr.write_text(known)
    return mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=120, known_red_path=kr,
                                 target="test_flow_planted.py", force=True, setup=False)


def test_broken_flow_fails_stage(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_planted_break():\n    assert False\n")
    assert not ok and "test_s_planted_break" in detail


def test_green_flow_passes_stage(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_planted_ok():\n    assert True\n")
    assert ok, detail


def test_known_red_tolerated_and_now_green_reported(tmp_path):
    ok, _ = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_known\n")
    assert ok
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert True\n", known="test_s_known\n")
    assert ok and "now green, remove from list: test_s_known" in detail


def test_empty_suite_fails_stage(tmp_path):
    ok, _ = _run(tmp_path, "")
    assert not ok


def test_trigger_rules():
    t = mgs.playthrough_trigger
    assert t(["csrc/x.c"]) and t(["autoload/a.gd"]) and t(["project.godot"]) and t(["tests/qa/desktop/t.py"])
    assert not t(["scenes/mockups/a.tscn"]) and not t(["docs/x.md"])
    assert t(["scenes/mockups/a.tscn", "scenes/hud.tscn"])


LEDGER = REPO / "docs/northstar/plans/push_ledger_2026-09-22.md"
ROW_ID = re.compile(r"(FINDING|TD)-[A-Za-z0-9._-]+")
CLOSED = re.compile(r"\bclosed(?! when\b)")  # TD-gate-known-red-empty-form: open = the second cell does not match


def known_red_entries(list_text):
    """Entry lines of the playthrough known-red list as (name, row text or None): a line that is not blank and
    does not start with #, split (the raw line, not stripped first) at its first " :: "; a test id may itself
    contain "::" as a pytest node id does, so a bare "::" is not the separator."""
    entries = []
    for line in list_text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, sep, row = line.partition(" :: ")
        entries.append((name.strip(), row.strip() if sep else None))
    return entries


def ledger_row_states(ledger_text):
    """{row id: open?}: a ledger row is a line starting with "| "; its id is the first whitespace-delimited token
    of its second cell (cells split on " | "); CLOSED when that cell matches \\bclosed(?! when\\b), else OPEN."""
    states = {}
    for line in ledger_text.splitlines():
        if not line.startswith("| "):
            continue
        cells = line.split(" | ")
        if len(cells) < 2 or not cells[1].split():
            continue
        states.setdefault(cells[1].split()[0], not CLOSED.search(cells[1]))
    return states


def known_red_problems(list_text, ledger_text):
    """One message per entry of the list that is not of the form `<test id> :: <row id>` with the row id naming an
    open FINDING or TD row of the ledger."""
    states = ledger_row_states(ledger_text)
    problems = []
    for name, row in known_red_entries(list_text):
        if not name:
            problems.append("no test id before ' :: '")
        elif row is None:
            problems.append(f"{name}: no ' :: <row id>'")
        elif not ROW_ID.fullmatch(row):
            problems.append(f"{name}: '{row}' is not a FINDING or TD row id")
        elif row not in states:
            problems.append(f"{name}: {row} is not a ledger row")
        elif not states[row]:
            problems.append(f"{name}: {row} is closed")
    return problems


def test_known_red_entries_name_open_rows():
    """TD-gate-known-red-empty-form: the empty-file form (`assert lines == []`) cannot hold while a known-red line
    is listed; every line in playthrough_known_red.txt has the form `<test id> :: <row id>` and its row id names
    an open FINDING or TD row of the ledger (open = second cell does not match \\bclosed(?! when\\b))."""
    assert known_red_problems(mgs.DEFAULT_KNOWN_RED.read_text(), LEDGER.read_text()) == []


OPEN_ROW = "FINDING-fixture-open"
CLOSED_ROW = "FINDING-fixture-shut"  # the id must not itself match \bclosed
FIXTURE_LEDGER = (
    "| day | id | files | text |\n"
    f"| day1 | {OPEN_ROW} (finding, owner X; open until P lands) | f | t |\n"
    f"| day1 | {CLOSED_ROW} (finding, closed 2026-10-22 at abc1234) | f | t |\n"
    "| day1 | TD-fixture-closing-later (test-defect, closed when P lands) | f | t |\n"
)


def _fixture_problems(tmp_path, list_text, ledger_text=FIXTURE_LEDGER):
    (tmp_path / "list.txt").write_text(list_text)
    (tmp_path / "ledger.md").write_text(ledger_text)
    return known_red_problems((tmp_path / "list.txt").read_text(), (tmp_path / "ledger.md").read_text())


def test_known_red_entry_with_an_open_row_passes(tmp_path):
    assert _fixture_problems(tmp_path, f"# header\n\ntest_a :: {OPEN_ROW}\n") == []
    assert _fixture_problems(tmp_path, "test_b :: TD-fixture-closing-later\n") == []  # 'closed when' is still open


def test_known_red_entry_with_a_closed_row_fails(tmp_path):
    assert _fixture_problems(tmp_path, f"test_a :: {CLOSED_ROW}\n") == [f"test_a: {CLOSED_ROW} is closed"]


def test_known_red_entry_with_an_id_that_is_not_a_ledger_row_fails(tmp_path):
    assert _fixture_problems(tmp_path, "test_a :: FINDING-fixture-nowhere\n") \
        == ["test_a: FINDING-fixture-nowhere is not a ledger row"]
    assert _fixture_problems(tmp_path, "test_a :: NOTE-fixture\n") == ["test_a: 'NOTE-fixture' is not a FINDING or TD row id"]


def test_known_red_bare_name_without_a_separator_fails(tmp_path):
    assert _fixture_problems(tmp_path, "test_a\n") == ["test_a: no ' :: <row id>'"]


def test_known_red_entry_whose_test_id_contains_double_colon_passes(tmp_path):
    line = f"tests/x.py::test_a :: {OPEN_ROW}\n"
    assert known_red_entries(line) == [("tests/x.py::test_a", OPEN_ROW)]
    assert _fixture_problems(tmp_path, line) == []


def test_known_red_nameless_entry_fails(tmp_path):
    assert _fixture_problems(tmp_path, f" :: {OPEN_ROW}\n") == ["no test id before ' :: '"]


def test_known_red_closed_row_entry_passes_when_the_fixture_row_is_open(tmp_path):
    line = f"test_a :: {CLOSED_ROW}\n"
    assert _fixture_problems(tmp_path, line) != []
    reopened = FIXTURE_LEDGER.replace("closed 2026-10-22 at abc1234", "open until P lands")
    assert _fixture_problems(tmp_path, line, reopened) == []


# HARNESS-gate-venv-link, ruling W9: the playthrough stage strips " :: <row id>" from a known-red entry
# before it matches by prefix. The planted suite is the tmp test file of _run; no game code runs.

def test_known_red_entry_with_a_row_id_tolerates_the_planted_failure(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_known :: FINDING-fixture-open\n")
    assert ok, detail


def test_known_red_entry_with_a_row_id_reports_now_green(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert True\n", known="test_s_known :: FINDING-fixture-open\n")
    assert ok and "now green, remove from list: test_s_known" in detail, detail


def test_known_red_bare_name_entry_still_tolerates_the_planted_failure(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_known\n")
    assert ok, detail


def test_known_red_entry_naming_another_test_still_rejects_the_failure(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_other :: FINDING-fixture-open\n")
    assert not ok and "test_s_known" in detail, detail


def test_known_red_nameless_entry_tolerates_nothing(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert False\n", known=" :: FINDING-fixture-open\n")
    assert not ok and "test_s_known" in detail, detail


def test_known_red_name_containing_double_colon_is_parsed_whole(tmp_path):
    ok, detail = _run(tmp_path, "def test_s_known():\n    assert False\n", known="test_s_known::x :: FINDING-fixture-open\n")
    assert not ok and "test_s_known" in detail, detail


def test_missing_suite_fails_stage(tmp_path):
    ok, detail = mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=60,
                                       target="tests/qa/desktop", force=True, setup=False)
    assert not ok and "suite missing" in detail


def test_build_failure_rejects_and_suite_not_run(tmp_path, monkeypatch):
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "make").write_text("#!/bin/sh\necho planted build break >&2\nexit 1\n")
    (stub / "make").chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub}:/usr/bin:/bin")
    cand = tmp_path / "cand"
    cand.mkdir()
    (cand / "test_flow_planted.py").write_text("def test_s_ran():\n    open('RAN', 'w')\n")
    ok, detail = mgs.playthrough_check(cand, "HEAD", python_exe=PY, timeout=60,
                                       target="test_flow_planted.py", force=True, setup=True)
    assert not ok and detail.startswith("playthrough setup failed: build") and "planted build break" in detail
    assert not (cand / "RAN").exists()


# --- HARNESS-playsplit: the playthrough stage ignores tests/qa/desktop/plays/**; lane_plays owns the plays ---

def _desktop_tree(tmp_path, spine_body, play_body, extra_body=None):
    d = tmp_path / "tests/qa/desktop"
    (d / "plays/A").mkdir(parents=True)
    (d / "test_flow_spine.py").write_text(spine_body)
    (d / "plays/A/test_S_001.py").write_text(play_body)
    if extra_body is not None:
        (d / "test_other_desktop.py").write_text(extra_body)
    kr = tmp_path / "known_red.txt"
    kr.write_text("")
    return kr


def _check(tmp_path, kr):
    return mgs.playthrough_check(tmp_path, "HEAD", python_exe=PY, timeout=120, known_red_path=kr,
                                 target="tests/qa/desktop", force=True, setup=False)


def test_playthrough_command_ignores_plays_dir(tmp_path, monkeypatch):
    """HARNESS-playsplit. Red now: playthrough_check builds `pytest ... tests/qa/desktop` with no
    --ignore, so the flow spine and the play are both collected."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n", "def test_S_001_play():\n    pass\n")
    seen = []
    real = mgs.subprocess.run

    def spy(cmd, *a, **k):
        if isinstance(cmd, list) and "pytest" in cmd:
            seen.append(list(cmd))
        return real(cmd, *a, **k)
    monkeypatch.setattr(mgs.subprocess, "run", spy)
    ok, detail = _check(tmp_path, kr)
    assert ok, detail
    assert len(seen) == 1
    cmd = seen[0]
    assert "tests/qa/desktop" in cmd
    ign = [a for a in cmd if a.startswith("--ignore") and a.rstrip("/").endswith("tests/qa/desktop/plays")]
    assert ign, f"no --ignore of tests/qa/desktop/plays in {cmd}"
    assert "1 passed" in detail, detail  # the spine only, not the play


def test_red_play_does_not_reject_playthrough(tmp_path):
    """HARNESS-playsplit. Red now: a red play under plays/ is collected by the playthrough stage
    and rejects it (ok=False), though only the lane_plays list may carry it."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n",
                       "def test_S_001_play():\n    assert False\n")
    ok, detail = _check(tmp_path, kr)
    assert ok, detail
    assert "test_S_001_play" not in detail


def test_red_desktop_test_outside_plays_still_rejects(tmp_path):
    """HARNESS-playsplit positive control: a red desktop test outside plays/ still rejects.
    Green now and must stay green after the split."""
    kr = _desktop_tree(tmp_path, "def test_flow_spine_ok():\n    pass\n",
                       "def test_S_001_play():\n    pass\n",
                       extra_body="def test_other_broken():\n    assert False\n")
    ok, detail = _check(tmp_path, kr)
    assert not ok and "test_other_broken" in detail
