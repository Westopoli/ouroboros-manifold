#!/usr/bin/env python3
# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md "### HARNESS-context-guard, the 400k hard stop"
"""Context guard hook: block a prompt or tool call once the chat's context passes the threshold.

Runs as UserPromptSubmit and PreToolUse. Reads hook JSON on stdin, or --transcript with --prompt
or --tool/--tool-input. Exit 0 passes; exit 2 blocks. It never fails on an error of its own.
"""
import argparse
import json
import os
import re
import sys

TOKENS = 400000  # DRAFT-context-guard-tokens
WORD = "handoff"  # DRAFT-context-guard-word
TAIL_BYTES = 4194304  # DRAFT-context-guard-tail-bytes


def context_tokens(path):
    """Last non-sidechain assistant usage in the tail window (the size method_check.py uses), or None."""
    with open(path, "rb") as f:
        size = f.seek(0, os.SEEK_END)
        start = max(0, size - TAIL_BYTES)
        f.seek(start)
        data = f.read()
    lines = data.split(b"\n")
    if start > 0:
        lines = lines[1:]  # the first line was cut by the window
    for line in reversed(lines):
        try:
            e = json.loads(line)
            if e.get("type") != "assistant" or e.get("isSidechain"):
                continue
            u = e["message"]["usage"]
            return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--prompt")
    ap.add_argument("--tool")
    ap.add_argument("--tool-input")
    ap.add_argument("--threshold", type=int, default=TOKENS)
    ap.add_argument("--word", default=WORD)
    ap.add_argument("--memory-dir", default="~/.claude/projects/")
    a, _ = ap.parse_known_args()
    if a.transcript:
        path, prompt, tool, tool_input = a.transcript, a.prompt or "", a.tool, a.tool_input
    else:
        d = json.loads(sys.stdin.read())
        path, prompt = d.get("transcript_path"), d.get("prompt") or ""
        tool = d.get("tool_name") if d.get("hook_event_name") == "PreToolUse" or d.get("tool_name") else None
        tool_input = d.get("tool_input")
    if not path or not os.path.isfile(path):
        return 0
    ctx = context_tokens(path)
    if ctx is None or ctx <= a.threshold:
        return 0
    n, t = ctx // 1000, a.threshold // 1000
    if tool:
        if isinstance(tool_input, str):
            tool_input = json.loads(tool_input)
        if tool in ("Write", "Edit"):
            target = os.path.realpath(os.path.expanduser((tool_input or {}).get("file_path", "")))
            mem = os.path.realpath(os.path.expanduser(a.memory_dir))
            if target.startswith(mem.rstrip("/") + "/"):
                return 0
        print(f"CONTEXT GUARD {n}k past {t}k: tool call blocked; write the continuation memory with the Write tool "
              "(under ~/.claude/projects/) and stop; this chat restarts from memory", file=sys.stderr)
        return 2
    if re.search(r"(?<![\w-])" + re.escape(a.word) + r"(?![\w-])", prompt, re.IGNORECASE):
        print(f"CONTEXT GUARD handoff turn allowed at {n}k: write the continuation memory and stop")
        return 0
    print(f"CONTEXT GUARD {n}k past {t}k: this chat restarts from memory (CLAUDE.md Usage discipline); "
          f'send one prompt containing "{a.word}" to write the continuation memory, then start a new chat', file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except BaseException:
        code = 0
    sys.exit(code)
