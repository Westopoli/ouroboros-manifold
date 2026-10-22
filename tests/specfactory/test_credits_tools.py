# Rule pins: R-900-01@?, R-900-02@?, R-910-01@?, R-999-01@?
"""Tests for scripts/specfactory/sdk_engineer.py and batch_review.py (the console-credit tools).

No network, no key: every test runs dry-run code paths or plain functions, and `batch_review.client` is
replaced by a function that fails, so a stray call to the API (or to the real key file) cannot pass. The
anthropic and claude_agent_sdk packages are not needed (they are imported only by --submit / fetch / a real run).

Spec: scripts/specfactory/README_credits.md.
 1. the key-file rule: missing and mode 644 refused with the instruction, mode 600 accepted (positive control);
 2. audit-epics dry-run: two tiny epics give two requests, the ledger row naming an epic's rule id rides with
    that epic only, --samples 2 doubles them with different system nonces;
 3. story-reviews dry-run: one PNG and its state json give one request with an image block;
 4. digest: a fabricated results.jsonl becomes queue rows and tables (beyond the three asked: the code path
    fetch uses, checked offline);
 5. sdk_engineer --dry-run: the options it would use, no key read, a main checkout refused (beyond the three asked).
"""
import base64
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import batch_review  # noqa: E402
import sdk_engineer  # noqa: E402

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
CUSTOM_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")  # the Batch API's rule for custom_id
LANE_HEAD = ("| story | lane | run id | screenshot path | qa_state file | reviewer | verdict | W | date |\n"
             "|---|---|---|---|---|---|---|---|---|\n")


@pytest.fixture(autouse=True)
def no_api(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("a dry run must not build an API client or read the key")
    monkeypatch.setattr(batch_review, "client", refuse)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _tree(root: Path, shot: bool = False) -> Path:
    """A throwaway repo: two tiny epics, a ledger with one row naming R-900-01, optionally one story shot."""
    _write(root / "docs/bible/epics/E-90-alpha.md", "# E-90\n\n### S-900 - First\nAs a commander, I want X.\n\nRules\n"
           "- R-900-01  Given a, When b, Then c.\n- R-900-02  Given d, When e, Then f.\n")
    _write(root / "docs/bible/epics/E-91-beta.md", "# E-91\n\n### S-910 - Second\nAs a commander, I want Y.\n\nRules\n"
           "- R-910-01  Given g, When h, Then i.\n")
    _write(root / "docs/northstar/plans/push_ledger_2026-09-22.md", "| Time | Event | Detail |\n|---|---|---|\n"
           "| day1 | ruling | R-900-01 now says z |\n| day1 | other | R-999-01 is somewhere else |\n")
    if shot:
        _write(root / "docs/bible/stories.md", "| Story | Epic | In the commander's words | Status | Depth |\n|---|---|---|---|---|\n"
               '| S-900 | E-90 | "I see X on screen." | Built | `epics/E-90-alpha.md` S-900 |\n')
        shots = root / "docs/northstar/story_reviews/shots/run-1"
        shots.mkdir(parents=True)
        (shots / "S-900.png").write_bytes(PNG_1X1)
        (shots / "S-900.state.json").write_text('{"tick": 3, "inventory": {"hud_texts": {}}}')
    return root


def _requests(out: Path) -> list:
    return [json.loads(line) for line in (out / "requests.jsonl").read_text().splitlines()]


def test_key_file_missing_or_not_mode_600_is_refused(tmp_path, capsys):
    """Spec: refuse to run when the key file is missing or its mode is not 600, print the exact instruction."""
    with pytest.raises(SystemExit) as e:
        sdk_engineer.read_key(tmp_path / "api_key")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "key file missing" in err and "chmod 600 ~/.config/anthropic/api_key" in err

    key = _write(tmp_path / "loose_key", "sk-ant-test-secret\n")
    key.chmod(0o644)
    with pytest.raises(SystemExit) as e:
        sdk_engineer.read_key(key)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "mode is 644, must be 600" in err and "sk-ant-test-secret" not in err

    key.chmod(0o600)  # positive control: the same file at mode 600 is accepted
    assert sdk_engineer.read_key(key) == "sk-ant-test-secret"
    key.write_text("two words\n")  # more than the key on the line is refused too
    with pytest.raises(SystemExit):
        sdk_engineer.read_key(key)
    assert batch_review.read_key is sdk_engineer.read_key  # one rule for both tools


def test_audit_epics_dry_run_two_epics_two_requests(tmp_path, capsys):
    """Spec: one request per epic file; ledger rows that name the epic's rule ids ride with it; --samples repeats."""
    root, out = _tree(tmp_path / "repo"), tmp_path / "out"
    assert batch_review.main(["audit-epics", "--root", str(root), "--out", str(out)]) == 0
    reqs = _requests(out)
    assert [r["custom_id"] for r in reqs] == ["audit-E-90-s1", "audit-E-91-s1"]
    assert all(CUSTOM_ID.match(r["custom_id"]) for r in reqs)
    user = {r["custom_id"]: r["params"]["messages"][0]["content"] for r in reqs}
    assert "R-900-01 now says z" in user["audit-E-90-s1"] and "R-999-01" not in user["audit-E-90-s1"]
    assert "R-900-01 now says z" not in user["audit-E-91-s1"] and "(none)" in user["audit-E-91-s1"]
    assert reqs[0]["params"]["model"] == "claude-sonnet-5-5"
    printed = capsys.readouterr().out
    assert "2 requests" in printed and "total ~$" in printed and "dry run: nothing sent" in printed
    assert not (out / "batch_id.txt").exists()

    out2 = tmp_path / "out2"  # --samples 2: four requests, a different system nonce per sample
    assert batch_review.main(["audit-epics", "--root", str(root), "--out", str(out2), "--samples", "2"]) == 0
    reqs2 = _requests(out2)
    nonces = [re.search(r"nonce ([0-9a-f]{8})", r["params"]["system"]).group(1) for r in reqs2]
    assert len(reqs2) == 4 and len(set(nonces)) == 4
    assert batch_review.main(["audit-epics", "--root", str(root), "--out", str(tmp_path / "o3"), "--model", "claude-fable-5-1"]) == 0
    assert "$5/$25 per MTok" in capsys.readouterr().out


def test_story_reviews_dry_run_one_png_one_state_one_image_request(tmp_path, capsys):
    """Spec: one request per shot with a story id and a state json: image block, story words, rule lines, qa_state."""
    root, out = _tree(tmp_path / "repo", shot=True), tmp_path / "out"
    _write(root / "docs/northstar/story_reviews/shots/run-1/note.png", "not a story shot")  # no story id: skipped
    assert batch_review.main(["story-reviews", "--root", str(root), "--out", str(out)]) == 0
    reqs = _requests(out)
    assert len(reqs) == 1 and CUSTOM_ID.match(reqs[0]["custom_id"])
    content = reqs[0]["params"]["messages"][0]["content"]
    image = [b for b in content if b["type"] == "image"]
    assert len(image) == 1 and image[0]["source"]["type"] == "base64" and image[0]["source"]["media_type"] == "image/png"
    assert base64.b64decode(image[0]["source"]["data"]) == PNG_1X1  # 1x1 is under 1280 wide: sent as is
    text = "".join(b["text"] for b in content if b["type"] == "text")
    assert "I see X on screen." in text and "R-900-01  Given a, When b, Then c." in text
    assert '{"tick":3,"inventory":{"hud_texts":{}}}' in text and "R-900-02" in text
    assert "yes" in reqs[0]["params"]["system"] and "unclear" in reqs[0]["params"]["system"]
    printed = capsys.readouterr().out
    assert "1 requests" in printed and "1 skipped" in printed and "no story id" in printed

    # a shot whose file name carries no story id is mapped through the lane row that lists its path
    shots = root / "docs/northstar/story_reviews/shots/run-1"
    (shots / "opening.png").write_bytes(PNG_1X1)
    (shots / "opening.json").write_text('{"tick": 0}')
    _write(root / "docs/northstar/story_reviews/B.md", LANE_HEAD + "| S-900 (variant) | B | run-1 | "
           "docs/northstar/story_reviews/shots/run-1/opening.png | x | sonnet | yes | pending | 2026-10-01 |\n")
    out2 = tmp_path / "out2"
    assert batch_review.main(["story-reviews", "--root", str(root), "--out", str(out2)]) == 0
    index = json.loads((out2 / "index.json").read_text())
    assert sorted(i["png"].rsplit("/", 1)[1] for i in index["items"].values()) == ["S-900.png", "opening.png"]
    assert {i["story"] for i in index["items"].values()} == {"S-900"} and {i["lane"] for i in index["items"].values()} == {"B"}


def test_digest_turns_results_into_queue_rows_and_tables(tmp_path):
    """Beyond the three asked: the digest fetch writes, from a fabricated results.jsonl (no network)."""
    root = _tree(tmp_path / "repo", shot=True)
    _write(root / "docs/northstar/story_reviews/A.md", LANE_HEAD + "| S-900 | A | run-1 | "
           "docs/northstar/story_reviews/shots/run-1/S-900.png | x | sonnet | yes | approved | 2026-10-01 |\n")
    ok = lambda cid, text, i, o: {"custom_id": cid, "result": {"type": "succeeded", "message": {"model": "claude-sonnet-5-5", "content": [
        {"type": "text", "text": text}], "usage": {"input_tokens": i, "output_tokens": o}}}}
    for kind, args, results in (
            ("audit-epics", [], lambda ids: [ok(ids[0], "| Rule id |\n|---|\n| R-900-01 |", 2000, 100),
                                             {"custom_id": ids[1], "result": {"type": "expired"}}]),
            ("story-reviews", [], lambda ids: [ok(ids[0], "Yes. one | line\nof evidence", 1000, 50)])):
        out = tmp_path / kind
        assert batch_review.main([kind, "--root", str(root), "--out", str(out)] + args) == 0
        ids = [r["custom_id"] for r in _requests(out)]
        (out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results(ids)))
        assert batch_review.main(["digest", "--out", str(out)]) == 0
    audit = (tmp_path / "audit-epics" / "digest.md").read_text()
    assert "## E-90, sample 1 (1 ledger rows)" in audit and "| R-900-01 |" in audit
    assert "audit-E-91-s1: expired" in audit and "tokens in 2,000, out 100" in audit and "$0.00" in audit
    rows = (tmp_path / "story-reviews" / "digest.md").read_text()
    assert ("| S-900 | A | run-1 | docs/northstar/story_reviews/shots/run-1/S-900.png | "
            "docs/northstar/story_reviews/shots/run-1/S-900.state.json | batch claude-sonnet-5-5 | "
            "yes. one / line of evidence | pending |") in rows


def test_sdk_engineer_dry_run_prints_options_without_reading_the_key(tmp_path, capsys, monkeypatch):
    """Beyond the three asked: --dry-run shows the options, never reads the key; a main checkout is refused."""
    def no_key(*a, **k):
        raise AssertionError("--dry-run must not read the key file")
    monkeypatch.setattr(sdk_engineer, "read_key", no_key)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    wt, brief = tmp_path / "wt", _write(tmp_path / "brief.md", "do the thing\n")
    _write(wt / ".git", "gitdir: /elsewhere/.git/worktrees/wt\n")  # a linked worktree's .git is a file
    assert sdk_engineer.main(["--worktree", str(wt), "--brief", str(brief), "--dry-run", "--allowed-tools", "Read,Grep"]) == 0
    out = capsys.readouterr().out
    opts, _ = json.JSONDecoder().raw_decode(out)
    assert opts["cwd"] == str(wt) and opts["model"] == "claude-sonnet-5-5" and opts["setting_sources"] == ["project"]
    assert opts["tools"] == ["Grep", "Read"] and opts["allowed_tools"] == ["Read", "Grep"]  # no Task: no sub-agents
    assert opts["env"]["ANTHROPIC_API_KEY"].startswith("<read from ~/.config/anthropic/api_key")
    assert opts["max_budget_usd"] == 5.0 and opts["max_turns"] == 60 and opts["permission_mode"] == "acceptEdits"
    main_checkout = tmp_path / "main"
    (main_checkout / ".git").mkdir(parents=True)
    with pytest.raises(SystemExit) as e:
        sdk_engineer.main(["--worktree", str(main_checkout), "--brief", str(brief), "--dry-run"])
    assert "not a linked git worktree" in str(e.value)
