# Rule pins: R-990-01@?
# spec: docs/stories/H-077.md (mail-and-station), Tests 1 to 8; rule 2 of docs/method/communication.md
"""H-077 scripts/method/mail.py. Rule: "Mailboxes exist only for the named chats in the registry
`docs/method/agents.toml`." Every test uses a temp OM_PUSH_DIR and a fixture registry (tests/method/mailfix.py).
Control (green today): the fixture registry parses and the story's refused patterns match their examples.
Runtime: a few seconds."""
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailfix import MAIL, REGISTRY, iso, lines, mail, make_env, put_mail  # noqa: E402

MAX = 1500  # DRAFT-mail-max, docs/method/README.md Numbers
BLACKBOARD = [r"\b(landed|pushed|merged) (at|on|to)?\s*[0-9a-f]{7,}", r"\bslots? (freed|free|held)\b",
              r"\bin flight\b", r"\bsweep (pass|green|red)\b", r"\bstatus:"]


def inbox(root, agent):
    return lines(root / agent / "inbox.jsonl")


def test_control_registry_fixture_and_patterns_are_sound():
    """Control: the fixture registry parses with two rules agents; the story's refusal patterns hit their examples."""
    reg = tomllib.loads(REGISTRY)
    assert sum(1 for t in reg.values() if t.get("rules")) == 2
    assert re.search(BLACKBOARD[0], "H-057 landed at 1a2b3c4d")
    assert not any(re.search(p, "H-057 blocked: needs a ruling on the gate") for p in BLACKBOARD)


def test_t0_script_exists():
    """H-077 Files: scripts/method/mail.py is new."""
    assert MAIL.exists(), f"{MAIL} missing"


def test_t1_register_makes_directory_unknown_refused_and_nothing_hard_coded(tmp_path):
    """H-077 Tests 1: "`register` makes the directory from the fixture registry; an unknown name is refused; a second
    architect and a planner added to the fixture registry register the same way (nothing is hard-coded)." """
    env, root = make_env(tmp_path)
    for name in ("architect", "architect2", "planner"):
        r = mail(env, "register", name)
        assert r.returncode == 0 and f"MAIL OK registered {name}" in r.stdout, (name, r.stdout, r.stderr)
        assert (root / name).is_dir(), name
    r = mail(env, "register", "ghost")
    assert r.returncode == 1 and "MAIL REFUSED" in r.stdout, (r.stdout, r.stderr)
    assert not (root / "ghost").exists()


def test_t2_send_appends_exactly_one_line_with_every_field(tmp_path):
    """H-077 Interfaces, Mail line: id, ts, from, to, class, re, text, attach, read (null)."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    r = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "ask", "--re", "H-057", "need a ruling")
    assert r.returncode == 0 and re.match(r"MAIL OK \S+ -> architect ask", r.stdout), (r.stdout, r.stderr)
    got = inbox(root, "architect")
    assert len(got) == 1
    m = got[0]
    assert set(m) == {"id", "ts", "from", "to", "class", "re", "text", "attach", "read"}, m
    assert (m["from"], m["to"], m["class"], m["re"], m["text"], m["attach"], m["read"]) == \
        ("runner-lab", "architect", "ask", "H-057", "need a ruling", [], None)


def test_t2_concurrent_sends_append_two_intact_lines(tmp_path):
    """H-077 Tests 2: "two concurrent sends append two intact lines (the lock)." """
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    big = "y" * 1000
    ps = [subprocess.Popen([sys.executable, str(MAIL), "send", "--me", s, "--to", "architect", "--class", "info", big],
                           env=env, stdout=subprocess.PIPE, text=True) for s in ("runner-lab", "runner-beta")]
    for p in ps:
        p.communicate(timeout=30)
    got = inbox(root, "architect")
    assert sorted(m["from"] for m in got) == ["runner-beta", "runner-lab"] and all(m["text"] == big for m in got)


def test_t3_each_refused_pattern_refuses_and_appends_nothing(tmp_path):
    """H-077 Tests 3 and Interfaces: `MAIL REFUSED blackboard: <pattern>` for each state-report pattern."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    for text in ("H-057 landed at 1a2b3c4d", "two slots freed", "H-040 in flight", "sweep green on main", "status: all fine"):
        r = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "info", text)
        assert r.returncode == 1 and "MAIL REFUSED blackboard:" in r.stdout, (text, r.stdout, r.stderr)
    assert inbox(root, "architect") == []


def test_t3_positive_control_same_words_as_a_request_pass(tmp_path):
    """H-077 Tests 3: `"H-057 blocked: needs a ruling on ..."` passes; `"H-057 landed at 1a2b3c4d"` is refused."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    ok = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "block", "H-057 blocked: needs a ruling on the gate")
    bad = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "info", "H-057 landed at 1a2b3c4d")
    assert ok.returncode == 0 and "MAIL OK" in ok.stdout, (ok.stdout, ok.stderr)
    assert bad.returncode == 1
    assert len(inbox(root, "architect")) == 1


def test_t3_unknown_agent_is_refused(tmp_path):
    """H-077 Interfaces: `MAIL REFUSED unknown agent <name>`."""
    env, root = make_env(tmp_path)
    r = mail(env, "send", "--me", "runner-lab", "--to", "ghost", "--class", "info", "hello")
    assert r.returncode == 1 and "MAIL REFUSED unknown agent ghost" in r.stdout, (r.stdout, r.stderr)


def test_t4_ask_to_a_non_rules_agent_is_refused(tmp_path):
    """H-077 Tests 4: "`ask` to an agent with `rules = false` is refused" (`class ask needs rules = true`)."""
    env, root = make_env(tmp_path)
    mail(env, "register", "planner")
    r = mail(env, "send", "--me", "runner-lab", "--to", "planner", "--class", "ask", "which one?")
    assert r.returncode == 1 and "MAIL REFUSED class ask needs rules = true" in r.stdout, (r.stdout, r.stderr)
    assert inbox(root, "planner") == []


def test_t4_to_rules_with_two_rules_agents_writes_two_lines(tmp_path):
    """H-077 Tests 4: "`--to rules` with two rules agents writes two lines." """
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    mail(env, "register", "architect2")
    mail(env, "register", "planner")
    r = mail(env, "send", "--me", "runner-lab", "--to", "rules", "--class", "ask", "a question for the rulers")
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert len(inbox(root, "architect")) == 1 and len(inbox(root, "architect2")) == 1
    assert inbox(root, "planner") == []


def test_t5_sender_not_in_senders_is_refused_and_star_accepts_any(tmp_path):
    """H-077 Tests 5: "A sender not in `senders` is refused; `senders = ["*"]` accepts any." """
    env, root = make_env(tmp_path)
    for n in ("architect", "closed", "westley"):
        mail(env, "register", n)
    bad = mail(env, "send", "--me", "runner-lab", "--to", "closed", "--class", "info", "hi")
    assert bad.returncode == 1 and "MAIL REFUSED sender runner-lab not allowed by closed.senders" in bad.stdout, (bad.stdout, bad.stderr)
    nobody = mail(env, "send", "--me", "architect", "--to", "westley", "--class", "info", "hi")
    assert nobody.returncode == 1 and "not allowed by westley.senders" in nobody.stdout
    good = mail(env, "send", "--me", "architect", "--to", "closed", "--class", "info", "hi")
    star = mail(env, "send", "--me", "whoever", "--to", "architect", "--class", "info", "hi")
    assert good.returncode == 0 and star.returncode == 0, (good.stdout, star.stdout)


def test_t6_over_max_is_refused_with_attach_hint_and_file_passes(tmp_path):
    """H-077 Tests 6: "Text over DRAFT-mail-max is refused with the attach hint; the same text in a file with
    `--attach` passes." DRAFT-mail-max is 1,500 characters (README Numbers)."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    text = "z" * (MAX + 1)
    r = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "info", text)
    assert r.returncode == 1 and f"MAIL REFUSED text over {MAX} chars, put it in a file and --attach it" in r.stdout, (r.stdout, r.stderr)
    f = tmp_path / "long.txt"
    f.write_text(text)
    r = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "info", "see file", "--attach", str(f))
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert inbox(root, "architect")[0]["attach"] == [str(f)]
    exact = mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "info", "z" * MAX)
    assert exact.returncode == 0, "exactly DRAFT-mail-max characters is allowed"


def test_t7_read_prints_digest_once_and_moves_lines_to_delivered(tmp_path):
    """H-077 Tests 7: "`read` prints the digest once and moves lines to `delivered.jsonl` with `read` set; a second
    `read` prints `MAIL none`." Digest line: `MAIL <class> <from> <re> <ts>: <text> [attach: <paths>]`."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    mail(env, "send", "--me", "runner-lab", "--to", "architect", "--class", "block", "--re", "H-057", "stuck on the gate")
    r = mail(env, "read", "--me", "architect")
    assert r.returncode == 0
    digest = [x for x in r.stdout.splitlines() if x.startswith("MAIL ")]
    assert len(digest) == 1 and re.match(r"MAIL block runner-lab H-057 \S+: stuck on the gate", digest[0]), r.stdout
    assert inbox(root, "architect") == []
    done = lines(root / "architect" / "delivered.jsonl")
    assert len(done) == 1 and done[0]["read"], done
    again = mail(env, "read", "--me", "architect")
    assert again.returncode == 0 and again.stdout.strip() == "MAIL none", again.stdout


def test_t8_wait_returns_when_flag_created_removes_it_and_prints_digest(tmp_path):
    """H-077 Tests 8: "`wait` returns when the flag is created by another process, removes the flag and prints the
    digest." """
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    p = subprocess.Popen([sys.executable, str(MAIL), "wait", "--me", "architect", "--max", "20"], env=env,
                         stdout=subprocess.PIPE, text=True)
    time.sleep(1)
    assert p.poll() is None, "wait must block while there is no flag"
    put_mail(root, "architect", cls="block", text="wake up")
    (root / "architect" / "flag").touch()
    out, _ = p.communicate(timeout=15)
    assert p.returncode == 0 and "MAIL block" in out and "wake up" in out, out
    assert not (root / "architect" / "flag").exists()


def test_t8_wait_max_without_flag_prints_idle(tmp_path):
    """H-077 Tests 8: "`--max 1` without a flag prints `MAIL idle 1s`." """
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    r = mail(env, "wait", "--me", "architect", "--max", "1")
    assert r.returncode == 0 and "MAIL idle 1s" in r.stdout, (r.stdout, r.stderr)


def test_t9_list_shows_registry_with_unread_counts(tmp_path):
    """H-077 Interfaces: `list`: the registry as a table (name, role, rules, wake, unread count)."""
    env, root = make_env(tmp_path)
    mail(env, "register", "architect")
    put_mail(root, "architect", n=3)
    r = mail(env, "list")
    row = next((x for x in r.stdout.splitlines() if x.split()[:1] == ["architect"]), "")
    assert r.returncode == 0 and "architect.md" in row and "true" in row.lower() and row.split()[-1] == "3", r.stdout
