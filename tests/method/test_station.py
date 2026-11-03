# spec: docs/stories/H-077.md (mail-and-station), Tests 9; rule 4 of docs/method/communication.md
"""H-077 scripts/method/station.py. Rule: "The station decides every flag; no model does." Unread age is set by writing
old `ts` values into the inbox (the story's "fake clock" without a new interface); `--once` runs one loop.
Numbers: DRAFT-mail-linger 20 min, DRAFT-mail-batch 5 (README Numbers); fixture overrides: runner-lab linger_min 3,
batch 2; runner-beta wake = ["info"]. Control (green today): the fixture registry carries the overrides under test.
Runtime: a few seconds."""
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailfix import REGISTRY, STATION, lines, make_env, put_mail, station_once  # noqa: E402


def flag(root, a):
    return (root / a / "flag").exists()


def log(root):
    p = root / "station.log"
    return p.read_text().splitlines() if p.exists() else []


def test_control_fixture_registry_has_the_overrides():
    reg = tomllib.loads(REGISTRY)
    assert reg["runner-lab"]["linger_min"] == 3 and reg["runner-lab"]["batch"] == 2 and reg["runner-beta"]["wake"] == ["info"]


def test_t0_script_exists():
    assert STATION.exists(), f"{STATION} missing"


def test_t9_block_raises_the_flag_at_once_and_logs_the_class(tmp_path):
    """H-077 Tests 9: "a `block` raises the flag at once"; log line `<ts> flag <agent> class=<c> unread=<n>`."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="block", minutes_ago=0)
    r = station_once(env)
    assert r.returncode == 0, r.stderr
    assert flag(root, "architect")
    ln = log(root)
    assert len(ln) == 1 and " flag architect class=block unread=1" in ln[0], ln


def test_t9_one_fresh_info_does_not_raise(tmp_path):
    """H-077 Tests 9: "an `info` does not"."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="info", minutes_ago=0)
    assert station_once(env).returncode == 0
    assert not flag(root, "architect") and log(root) == []


def test_t9_five_info_raise_by_batch(tmp_path):
    """H-077 Tests 9: "five `info` do" (DRAFT-mail-batch 5); four do not."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="info", n=4)
    assert station_once(env).returncode == 0 and not flag(root, "architect")
    put_mail(root, "architect", cls="info", n=1)
    assert station_once(env).returncode == 0 and flag(root, "architect")
    assert "batch=5" in log(root)[-1] and "unread=5" in log(root)[-1], log(root)


def test_t9_one_old_info_raises_by_linger(tmp_path):
    """H-077 Tests 9: "one `info` older than `linger_min` does" (DRAFT-mail-linger 20): 25 min raises, 15 min not."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="info", minutes_ago=15)
    assert station_once(env).returncode == 0 and not flag(root, "architect")
    put_mail(root, "planner", cls="info", minutes_ago=25)
    assert station_once(env).returncode == 0
    assert (root / "planner" / "flag").exists() and "linger=" in log(root)[-1] and "flag planner" in log(root)[-1], log(root)


def test_t9_a_raised_flag_is_not_raised_twice(tmp_path):
    """H-077 Tests 9: "a raised flag is not raised twice" (one station.log line after two loops)."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="ask")
    station_once(env)
    station_once(env)
    assert len(log(root)) == 1, log(root)


def test_t9_per_agent_overrides_are_honoured(tmp_path):
    """H-077 Tests 9 / Interfaces: per-agent `wake`, `linger_min`, `batch` overrides. runner-lab batch 2 raises at two
    info; a 5 min old info raises on its linger_min 3; runner-beta wake=["info"] raises on one fresh info and does not
    raise on a block (class not in its wake, and nothing else triggers)."""
    env, root = make_env(tmp_path)
    put_mail(root, "runner-lab", cls="info", n=2)
    put_mail(root, "closed", cls="info", minutes_ago=5)  # default linger 20: no flag
    put_mail(root, "runner-beta", cls="info")
    station_once(env)
    assert flag(root, "runner-lab") and "batch=2" in " ".join(l for l in log(root) if "runner-lab" in l)
    assert not flag(root, "closed")
    assert flag(root, "runner-beta") and "class=info" in " ".join(l for l in log(root) if "runner-beta" in l)
    env2, root2 = make_env(tmp_path / "second")
    put_mail(root2, "runner-lab", cls="info", minutes_ago=5)
    put_mail(root2, "runner-beta", cls="block")
    station_once(env2)
    assert flag(root2, "runner-lab") and "linger=" in " ".join(l for l in log(root2) if "runner-lab" in l)
    assert not flag(root2, "runner-beta")


def test_t9_station_never_reads_text_or_moves_mail(tmp_path):
    """H-077 Interfaces: "never reads text": the inbox is byte-identical after a loop."""
    env, root = make_env(tmp_path)
    put_mail(root, "architect", cls="block", text="secret words")
    before = (root / "architect" / "inbox.jsonl").read_bytes()
    station_once(env)
    assert flag(root, "architect"), "the loop must run and raise (else this proves nothing)"
    assert (root / "architect" / "inbox.jsonl").read_bytes() == before
    assert "secret words" not in "\n".join(log(root))
