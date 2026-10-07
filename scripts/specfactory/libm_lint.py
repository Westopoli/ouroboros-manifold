#!/usr/bin/env python3
"""Fails on any call to a libm transcendental, or another non-deterministic
libc call, anywhere in csrc/**/*.c.

CLAUDE.md's determinism contract: same seed, same command stream, byte-
identical trace on Windows, macOS, and Linux -- "no platform transcendental
calls without a deterministic implementation" and "no ... hash-order or
wall-clock input to the sim". `om_sin` and `om_pow` exist precisely so the
sim never calls libm `sin()`/`pow()` (audit 2026-09-21, finding 1: `pow()`
was missed at `csrc/sim.c:206` until this fix). `rand`/`srand` bypass the
sim's own seeded stream; `time`/`clock` are wall-clock; `qsort`/`bsearch`
have platform-defined tie-break order for equal keys, which is a hash-order
class non-determinism. This lint is the mechanical backstop so the next
miss is caught before it ships, not found by a platform build months later.
Recursive (csrc/**/*.c) so a subdirectory module (e.g. csrc/pipe/) is
covered without a second lint to remember.

Usage:
    scripts/specfactory/libm_lint.py [csrc_dir]

Exit 0: no banned call found. Exit 1: prints one `FAIL <file>:<line> <fn>()`
line per banned call found. Exit 2: csrc_dir does not exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED = [
    "pow", "exp", "log", "log2", "log10", "sin", "cos", "tan",
    "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh", "exp2", "cbrt",
    "fma", "hypot", "ldexp", "frexp", "rint",
    "rand", "srand", "time", "clock", "qsort", "bsearch",
]
ALLOWED = {"sqrt", "fabs", "floor", "ceil", "round", "trunc", "fmin", "fmax", "fmod"}

assert ALLOWED.isdisjoint(BANNED)

BANNED_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BANNED) + r")\s*\(")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
WEAK_ATTR_RE = re.compile(r"__attribute__\s*\(\(\s*weak\s*\)\)")
DIRECTIVE_IF_RE = re.compile(r"^\s*#\s*(if|ifdef|ifndef)\b(.*)$")
DIRECTIVE_ELSE_RE = re.compile(r"^\s*#\s*(else|elif)\b")
DIRECTIVE_ENDIF_RE = re.compile(r"^\s*#\s*endif\b")

DEFAULT_CSRC = Path(__file__).resolve().parents[2] / "csrc"


def compute_debug_inject_exempt(lines: list[str]) -> list[bool]:
    """True for every line compiled only under `#ifdef OM_DEBUG_INJECT`
    (the debug-only fault-injection library, never linked into the release
    libouroboros.so) -- these branches exist specifically to reproduce a
    real, historical non-determinism bug for a control test (e.g.
    OM_BUG_LIBM_POW's own `pow()` call), so a libm call there is the point,
    not a violation. A line under that guard's `#else` (the release path)
    is never exempt. Handles simple nesting: a frame born inside an already
    exempt frame stays exempt regardless of its own condition."""
    exempt: list[bool] = []
    stack: list[dict] = []
    current = False
    for line in lines:
        m_if = DIRECTIVE_IF_RE.match(line)
        m_else = DIRECTIVE_ELSE_RE.match(line)
        m_endif = DIRECTIVE_ENDIF_RE.match(line)
        if m_if:
            is_guard = m_if.group(1) == "ifdef" and "OM_DEBUG_INJECT" in m_if.group(2)
            frame = {"true": True if is_guard else current, "false": current}
            frame["current"] = frame["true"]
            stack.append(frame)
            current = frame["current"]
        elif m_else and stack:
            stack[-1]["current"] = stack[-1]["false"]
            current = stack[-1]["current"]
        elif m_endif and stack:
            stack.pop()
            current = stack[-1]["current"] if stack else False
        exempt.append(current)
    return exempt


def strip_comments(text: str) -> str:
    """Blanks out /* */ and // comment bodies, preserving line numbers and
    every other character position (so a prose comment discussing a banned
    function by name, e.g. this file's own "libm sin()", is never mistaken
    for a call site). Newlines inside block comments are kept so line
    numbers downstream stay correct."""
    def _blank_block(m: re.Match) -> str:
        return "".join(c if c == "\n" else " " for c in m.group(0))

    text = BLOCK_COMMENT_RE.sub(_blank_block, text)
    text = LINE_COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)
    return text


def find_calls(text: str) -> list[tuple[int, str]]:
    """(lineno, function_name) for every banned call site in `text`. A
    plain word-boundary match: `\\bpow\\(` does not match inside `om_pow(`
    (no boundary between the '_' and 'p', both word characters), so the
    deterministic replacements are never flagged. Comments are stripped
    first so a prose mention of a banned function's name is never a false
    positive. A line whose function definition carries
    `__attribute__((weak))` is skipped: this codebase's convention
    (csrc/region.c) is a weak fallback body that a later strong definition
    in the same link unit always overrides (documented at region.c's own
    weak-stub block), so the call it makes never actually executes -- the
    identical convention as this file's own header comment, verified by
    the codebase's own libouroboros.so link (no multiple-definition error,
    the strong symbol wins)."""
    text = strip_comments(text)
    lines = text.splitlines()
    debug_exempt = compute_debug_inject_exempt(lines)
    findings: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if WEAK_ATTR_RE.search(line) or debug_exempt[i]:
            continue
        for m in BANNED_RE.finditer(line):
            findings.append((i + 1, m.group(1)))
    return findings


def lint_text(path_label: str, text: str) -> list[str]:
    return [
        f"FAIL {path_label}:{lineno} libm {fn}() call -- not deterministic across platforms"
        for lineno, fn in find_calls(text)
    ]


def lint_dir(csrc_dir: Path) -> list[str]:
    messages: list[str] = []
    for c_file in sorted(csrc_dir.rglob("*.c")):
        messages.extend(lint_text(str(c_file), c_file.read_text()))
    return messages


def main(argv: list[str]) -> int:
    csrc_dir = Path(argv[0]) if argv else DEFAULT_CSRC
    if not csrc_dir.is_dir():
        print(f"csrc dir not found: {csrc_dir}", file=sys.stderr)
        return 2
    messages = lint_dir(csrc_dir)
    for m in messages:
        print(m)
    if messages:
        print(f"LIBM LINT FAILED ({len(messages)})")
        return 1
    print("LIBM LINT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
