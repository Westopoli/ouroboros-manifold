#!/usr/bin/env python3
"""Run one brief through a Claude Code agent (Claude Agent SDK) inside a worktree, billed to the Console credits.

  sdk_engineer.py --worktree <path> --brief <file> [--model claude-sonnet-5-5] [--max-budget-usd 5]
                  [--max-turns 60] [--allowed-tools Bash,Read,Edit,Write,Grep,Glob] [--dry-run]

The API key is read at run time from ~/.config/anthropic/api_key (one line, mode 600; missing or any other mode:
refuses) and passed to the agent process only as env={"ANTHROPIC_API_KEY": key}. Never export it or write it to a
settings file: an exported key switches every subscription chat to Console billing. --dry-run prints the options,
reads no key, sends nothing. Needs claude_agent_sdk (om-push/venv-sdk); batch_review.py imports read_key from here.
The agent loads the worktree's .claude/settings.json (deny rules, git-guard hook) and CLAUDE.md, not ~/.claude;
only the --allowed-tools exist for it (no Task, so no sub-agents) and they run unasked. Assistant text goes to
stdout; result, usage and cost to <worktree>/.sdk_engineer_report.md (untracked; the SDK's cost estimate, not a
bill). Exit 0 ok; 1 agent error or bad arguments; 2 key file refused.
"""
import argparse
import asyncio
import dataclasses
import datetime
import json
import os
import sys
from pathlib import Path

KEY_FILE = Path.home() / ".config" / "anthropic" / "api_key"
KEY_HELP = """To create it once, in a terminal (the key stays out of shell history and the environment):
  mkdir -p ~/.config/anthropic
  (umask 077; read -rsp 'API key: ' k; echo; printf '%s\\n' "$k" > ~/.config/anthropic/api_key)
  chmod 600 ~/.config/anthropic/api_key
Never export it or put it in a settings file: Claude Code would then bill the Console in every subscription chat."""


def key_problem(path: Path = KEY_FILE) -> str | None:
    """Why the key file is unusable (never its contents), or None."""
    if not path.is_file():
        return f"key file missing: {path}"
    mode = path.stat().st_mode & 0o777
    return None if mode == 0o600 else f"key file mode is {mode:03o}, must be 600: {path}"


def read_key(path: Path = KEY_FILE) -> str:
    """The key, from the file only. Exits 2 with the exact instruction if the file is missing or not mode 600."""
    problem = key_problem(path)
    key = "" if problem else path.read_text().strip()
    if not problem and len(key.split()) != 1:
        problem = f"key file must hold the key on one line and nothing else: {path}"
    if problem:
        print(f"{problem}\n{KEY_HELP}", file=sys.stderr)
        sys.exit(2)
    return key


def build_options(a: argparse.Namespace, key: str | None) -> dict:
    """ClaudeAgentOptions keyword arguments; key=None gives the dry-run placeholder."""
    allowed = [t.strip() for t in a.allowed_tools.split(",") if t.strip()]
    return dict(
        cwd=str(a.worktree), model=a.model, max_turns=a.max_turns, max_budget_usd=a.max_budget_usd,
        tools=sorted({t.split("(")[0] for t in allowed}), allowed_tools=allowed, permission_mode="acceptEdits",
        setting_sources=["project"], system_prompt={"type": "preset", "preset": "claude_code"},
        env={"ANTHROPIC_API_KEY": key or "<read from ~/.config/anthropic/api_key at run time>"})


async def run(prompt: str, opts: dict):
    try:
        from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKError, ResultMessage, TextBlock, query
    except ImportError:
        sys.exit("claude_agent_sdk is not installed here; run with /home/westopoli/Projects/om-push/venv-sdk/bin/python")
    result = err = None
    try:
        async for m in query(prompt=prompt, options=ClaudeAgentOptions(**opts)):
            if isinstance(m, AssistantMessage):
                for b in m.content:
                    if isinstance(b, TextBlock):
                        print(b.text, flush=True)
            elif isinstance(m, ResultMessage):
                result = m
    except ClaudeSDKError as e:  # an error result raises after its ResultMessage was yielded
        err = f"{type(e).__name__}: {e}"
    return result, err


def write_report(a: argparse.Namespace, result, err: str | None) -> Path:
    d = {k: v for k, v in dataclasses.asdict(result).items() if k != "result"} if result else {}
    (path := a.worktree / ".sdk_engineer_report.md").write_text("\n".join([
        "# SDK engineer report", "", f"- {datetime.date.today()}, model {a.model}, brief {a.brief}",
        f"- {d.get('subtype')}, {d.get('num_turns')} turns, ${d.get('total_cost_usd')} (SDK client-side estimate, not a bill)",
        f"- exception: {err or 'none'}", "", "```json", json.dumps(d, indent=1, default=str), "```", "",
        "## Result", "", (result.result if result else None) or err or "(none)", ""]))
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--worktree", required=True, type=Path)
    p.add_argument("--brief", required=True, type=Path)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--max-budget-usd", type=float, default=5.0)
    p.add_argument("--max-turns", type=int, default=60)
    p.add_argument("--allowed-tools", default="Bash,Read,Edit,Write,Grep,Glob")
    p.add_argument("--dry-run", action="store_true", help="print the options and exit 0; no key read, no network")
    a = p.parse_args(argv)
    a.worktree = a.worktree.resolve()
    if not (a.worktree / ".git").is_file():  # a linked worktree has a .git file, a main checkout a directory
        sys.exit(f"{a.worktree} is not a linked git worktree (git worktree add -b <branch> <path> origin/main)")
    if not a.brief.is_file():
        sys.exit(f"brief not found: {a.brief}")
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        sys.exit("ANTHROPIC_AUTH_TOKEN is set; Claude Code ranks it above the key file. Unset it for this run.")
    if a.dry_run:
        print(json.dumps(build_options(a, None), indent=2))
        print(f"brief: {a.brief} ({len(a.brief.read_text())} chars); key file: {key_problem() or 'ok (mode 600)'}")
        return 0
    result, err = asyncio.run(run(a.brief.read_text(), build_options(a, read_key())))
    print(f"done: {result.subtype if result else 'no result'}, report {write_report(a, result, err)}")
    return 0 if result and not result.is_error and not err else 1


if __name__ == "__main__":
    sys.exit(main())
