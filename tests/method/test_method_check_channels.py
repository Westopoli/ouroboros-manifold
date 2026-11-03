# spec: docs/stories/H-059.md (two-gate-channels), ruling 6: method_check.py accepts the new lock names in command lines
"""H-059: the polling rule of scripts/specfactory/method_check.py knows `gate-lab.lock` and `gate-beta.lock` the way it
knew `gate.lock`: "No chat sits in a wait loop or polls a gate; clerks inside scripts do" (docs/method/runner.md).
Transcripts are built with the helpers of tests/specfactory/test_method_check.py (imported, that file is not edited).
Runtime: a few seconds."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "specfactory"))
from test_method_check import SONNET, assistant, bash, checks, run, write_transcript  # noqa: E402

GATE_LOCKS = ("gate-lab.lock", "gate-beta.lock")
CLERK_LOCKS = ("push.lock", "play.lock")


def _polling(tmp_path, *cmds):
    entries = [assistant(SONNET, tools=[bash(c)]) for c in cmds]
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    return checks(r.stdout)["polling"][:2]


def test_c1_old_gate_lock_name_in_a_non_reader_command_still_counts(tmp_path):
    """Control: the existing behaviour (a non-reader segment naming a gate lock is polling) is what the new names copy."""
    assert _polling(tmp_path, "watch -n 5 ls ~/Projects/om-push/gate-lab.lock") == ("DRIFT", 1)


def test_c2_reader_segments_naming_a_channel_lock_count_for_nothing(tmp_path):
    """Control: reading a lock file is not polling."""
    cmds = [f"{w} ~/Projects/om-push/{n}" for n in GATE_LOCKS for w in ("cat", "ls")]
    assert _polling(tmp_path, *cmds) == ("OK", 0)


def test_t1_channel_gate_lock_names_in_a_non_reader_command_count_as_polling(tmp_path):
    """H-059 ruling 6: "accept the three new names ... (`gate-lab.lock`, `gate-beta.lock`, ...)" in command lines:
    each channel gate lock behaves as gate.lock did."""
    for n in GATE_LOCKS:
        (tmp_path / n).mkdir()
        assert _polling(tmp_path / n, f"watch -n 5 ls ~/Projects/om-push/{n}") == ("DRIFT", 1), n


def test_c3_flock_on_any_of_the_lock_names_in_a_chat_is_polling(tmp_path):
    """H-059 ruling 6: a chat that takes any of the clerk-side locks with flock waits on a gate (control, green today: the
    flock word alone already counts, so the new names must not break it)."""
    cmds = [f"flock -w 60 ~/Projects/om-push/{n} true" for n in GATE_LOCKS + CLERK_LOCKS]
    assert _polling(tmp_path, *cmds) == ("DRIFT", len(cmds))
