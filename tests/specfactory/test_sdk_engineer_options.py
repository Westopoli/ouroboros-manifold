# Rule pins: none (harness piece, no R-id; FINDING-sdk-engineer-buffer-1mb)
"""HARNESS-sdk-buffer: sdk_engineer.py puts max_buffer_size = DRAFT-sdk-buffer-bytes into ClaudeAgentOptions.

Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "**HARNESS-sdk-buffer (Architect 2026-10-23 ..."
(ledger FINDING-sdk-engineer-buffer-1mb, DRAFT-sdk-buffer-bytes = 16 MiB = 16777216 bytes, Westley vetoes).
The test reads the built options via --dry-run and asserts the field; positive control: main's dry-run has no such field.

UNSTATED INTERFACES chosen here (the paragraph names the option, not its JSON shape):
 - the dry-run JSON key is the SDK keyword itself, "max_buffer_size", an int number of bytes (not "16MiB");
 - build_options(a, key) returns the same key, so the dry-run and the real run cannot differ;
 - the SDK's 1 MB default is 1048576 bytes (ledger row day38), so the draft is exactly 16 times it.
No network, no key: dry-run only.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import sdk_engineer  # noqa: E402

DRAFT_SDK_BUFFER_BYTES = 16 * 1024 * 1024  # DRAFT-sdk-buffer-bytes, 16777216
SDK_DEFAULT_BYTES = 1048576


def _dry_run_options(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    wt, brief = tmp_path / "wt", tmp_path / "brief.md"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n")
    brief.write_text("do the thing\n")
    assert sdk_engineer.main(["--worktree", str(wt), "--brief", str(brief), "--dry-run"]) == 0
    return json.JSONDecoder().raw_decode(capsys.readouterr().out)[0]


def _assert_buffer_field(opts):
    assert "max_buffer_size" in opts, "no max_buffer_size: the SDK's 1 MB default still kills a run"
    assert opts["max_buffer_size"] == DRAFT_SDK_BUFFER_BYTES
    assert isinstance(opts["max_buffer_size"], int) and not isinstance(opts["max_buffer_size"], bool)


def test_dry_run_options_carry_the_16_mib_buffer(tmp_path, capsys, monkeypatch):
    """FINDING-sdk-engineer-buffer-1mb: --dry-run shows max_buffer_size = 16777216."""
    _assert_buffer_field(_dry_run_options(tmp_path, capsys, monkeypatch))


def test_buffer_is_sixteen_times_the_sdk_default(tmp_path, capsys, monkeypatch):
    """FINDING-sdk-engineer-buffer-1mb: one tool result under 16 MiB survives; the default was 1048576."""
    opts = _dry_run_options(tmp_path, capsys, monkeypatch)
    assert opts.get("max_buffer_size", 0) == 16 * SDK_DEFAULT_BYTES


def test_build_options_and_real_run_share_the_field(tmp_path):
    """FINDING-sdk-engineer-buffer-1mb: build_options (used by the real run with a key) has the field too."""
    import argparse
    a = argparse.Namespace(worktree=tmp_path, model="claude-sonnet-5-5", max_turns=60, max_budget_usd=5.0,
                           allowed_tools="Read,Grep")
    _assert_buffer_field(sdk_engineer.build_options(a, "sk-test"))
    _assert_buffer_field(sdk_engineer.build_options(a, None))


def test_other_options_unchanged_by_the_buffer_field(tmp_path, capsys, monkeypatch):
    """Scope: the new field adds nothing else; the existing options keep their values."""
    opts = _dry_run_options(tmp_path, capsys, monkeypatch)
    assert opts["model"] == "claude-sonnet-5-5" and opts["max_turns"] == 60 and opts["max_budget_usd"] == 5.0
    assert opts["permission_mode"] == "acceptEdits" and opts["setting_sources"] == ["project"]


def test_positive_control_an_options_dict_without_the_field_is_rejected():
    """Positive control: the assertion helper fails on main's shape (no max_buffer_size), passes with it."""
    main_shape = {"cwd": "x", "model": "m", "max_turns": 60}
    with pytest.raises(AssertionError, match="no max_buffer_size"):
        _assert_buffer_field(main_shape)
    _assert_buffer_field({**main_shape, "max_buffer_size": DRAFT_SDK_BUFFER_BYTES})
    with pytest.raises(AssertionError):
        _assert_buffer_field({**main_shape, "max_buffer_size": SDK_DEFAULT_BYTES})
