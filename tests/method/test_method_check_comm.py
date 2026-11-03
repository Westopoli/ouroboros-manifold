# spec: docs/stories/H-077.md (mail-and-station), Tests 11; rules 1 and 3 of docs/method/communication.md
"""H-077 method_check.py rules comm_send, comm_state_checks, comm_mail_first, and the `wakeups` / `polling` changes.
Rules: "No chat is pushed a message" (comm_send: a `SendMessage` whose `to` is not `main` or a sub-agent id);
"more than three Bash segments in one wakeup" that start `git log|status|rev-parse|branch`, `status.sh`,
`status_check.py`, `flock`, or `ls` on a `.lock` (comm_state_checks); "Every turn begins with `mail.py read --me <name>`"
(comm_mail_first; a wakeup that is Westley's own typed turn is exempt). A wakeup is the span from one user turn to the
next. UNSTATED INTERFACE (reported): a user entry is Westley's typed turn when its content is a plain string not
starting `<task-notification>`; a tool_result entry is not a user turn. The `polling` exemption: a Bash whose command
begins `python3 scripts/method/mail.py wait`. Transcript helpers come from tests/specfactory/test_method_check.py.
Control (green today): `polling` flags `sleep`.
Runtime: a few seconds."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "specfactory"))
from test_method_check import SONNET, assistant, bash, checks, run, write_transcript  # noqa: E402

READ = "python3 scripts/method/mail.py read --me runner-lab"
LOG = "git log --oneline -3"


def note():
    return {"type": "user", "message": {"role": "user", "content": "<task-notification>done</task-notification>"}}


def westley(text="go on"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def go(tmp_path, entries):
    r = run(tmp_path, write_transcript(tmp_path, entries))
    assert r.returncode == 0, r.stderr
    return checks(r.stdout), r.stdout


def verdict_of(tmp_path, cid, entries):
    c, out = go(tmp_path, entries)
    assert cid in c, f"no METHOD {cid} line:\n{out}"
    return c[cid][:2]


def a(cmd):
    return assistant(SONNET, tools=[bash(cmd)])


def test_control_polling_still_flags_sleep(tmp_path):
    c, out = go(tmp_path, [note(), a("sleep 5")])
    assert c["polling"][:2] == ("DRIFT", 1)


def test_t11_cross_session_sendmessage_is_one_comm_send_drift(tmp_path):
    """H-077 Tests 11: "one with a cross-session `SendMessage` prints one `DRIFT comm_send`"."""
    e = [note(), a(READ),
         assistant(SONNET, tools=[("SendMessage", {"to": "ouroboros-manifold-90 [8a69cc]", "message": "hi"})])]
    assert verdict_of(tmp_path, "comm_send", e) == ("DRIFT", 1)


def test_t11_sendmessage_to_main_or_sub_agent_is_not_comm_send(tmp_path):
    """Rule: a `SendMessage` whose `to` is not `main` or a sub-agent id is drift; these two are not."""
    e = [note(), a(READ),
         assistant(SONNET, tools=[("SendMessage", {"to": "main", "message": "hi"})]),
         assistant(SONNET, tools=[("SendMessage", {"to": "a93eaf778770b83ac", "message": "hi"})])]
    assert verdict_of(tmp_path, "comm_send", e) == ("OK", 0)


def test_t11_five_git_log_segments_in_one_wakeup_is_one_drift(tmp_path):
    """H-077 Tests 11: "five `git log` segments in one wakeup prints one `DRIFT comm_state_checks`"."""
    e = [note(), a(READ)] + [a(LOG) for _ in range(5)]
    assert verdict_of(tmp_path, "comm_state_checks", e) == ("DRIFT", 1)


def test_t11_three_git_log_segments_is_none(tmp_path):
    """H-077 Tests 11: "three prints none" (the rule is more than three)."""
    e = [note(), a(READ)] + [a(LOG) for _ in range(3)]
    assert verdict_of(tmp_path, "comm_state_checks", e) == ("OK", 0)


def test_t11_state_checks_count_per_wakeup_not_per_session(tmp_path):
    """Rule: "a wakeup is the span from one user turn to the next": 3 + 3 across two wakeups is none."""
    e = [note(), a(READ)] + [a(LOG) for _ in range(3)] + [note(), a(READ)] + [a(LOG) for _ in range(3)]
    assert verdict_of(tmp_path, "comm_state_checks", e) == ("OK", 0)


def test_t11_wakeup_opening_with_cat_is_comm_mail_first_drift(tmp_path):
    """H-077 Tests 11: "one whose wakeup opens with `cat` prints `DRIFT comm_mail_first`"."""
    e = [note(), a("cat docs/method/runner.md")]
    assert verdict_of(tmp_path, "comm_mail_first", e) == ("DRIFT", 1)


def test_t11_wakeup_opening_with_mail_read_is_none(tmp_path):
    """H-077 Tests 11: "one opening with `mail.py read` prints none"."""
    e = [note(), a(READ), a("cat docs/method/runner.md")]
    assert verdict_of(tmp_path, "comm_mail_first", e) == ("OK", 0)


def test_t11_westleys_typed_turn_is_exempt_from_mail_first(tmp_path):
    """H-077 Interfaces: "a wakeup that is Westley's own typed turn is exempt"."""
    e = [westley(), a("cat docs/method/runner.md")]
    assert verdict_of(tmp_path, "comm_mail_first", e) == ("OK", 0)


def test_t11_background_mail_wait_is_not_polling(tmp_path):
    """H-077 Tests 11 (control): "a wakeup that is a background `mail.py wait` Bash prints no `polling` DRIFT"; and
    the `wakeups` rule text gains "or `mail.py wait`"."""
    e = [note(), a(READ),
         assistant(SONNET, tools=[("Bash", {"command": "python3 scripts/method/mail.py wait --me runner-lab", "run_in_background": True})])]
    c, out = go(tmp_path, e)
    assert c["polling"][:2] == ("OK", 0), out
    wake_line = next(x for x in out.splitlines() if x.startswith("METHOD wakeups "))
    assert "or `mail.py wait`" in wake_line, wake_line
