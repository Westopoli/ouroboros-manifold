#!/usr/bin/env python3
"""Proves, before an Agora card is queued, that its acceptance tests can go
green inside the card's `allowed_files` -- mechanically, no model involved.

Parses the card's acceptance pytest node ids, statically collects the om_*
ctypes symbols those tests reach (directly, or through tests/csim/conftest.py
helper functions), resolves each symbol to the csrc/*.c file that defines it,
and flags a symbol whose only definition is a stub the card cannot touch (its
acceptance can never pass), a symbol defined nowhere (an ABI gap), a
snippet_symbol the card's own snippet_file does not define, an oversized
card, a bad node id, or a stub another queued/parked card already owns (the
202b2 class: the test spans a card boundary).

Usage:
    scripts/specfactory/card_lint.py <card_file> [--project <path>] [--queue <path>] [--json]

Exit code 0 on LINT OK (no FAIL-level findings; WARN-level findings may still
print). Exit code 1 on LINT FAILED (n) -- n is the number of FAIL findings.
Exit code 2 on a usage or parse error (missing card, missing project,
missing/unparseable acceptance).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from green_check import parse_card  # noqa: E402  (reuse the frontmatter parser)

MAX_SNIPPET_SYMBOLS = 5
MAX_EXPECTED_LINES = 80
DEFAULT_QUEUE = Path("/home/westopoli/Projects/agora/queue")

OM_SYMBOL_RE = re.compile(r"^om_[A-Za-z0-9_]*$")
PYTEST_RE = re.compile(r"\bpytest\b")

_C_TOPLEVEL_DEF = re.compile(
    r"^[ \t]*(?:static\s+|inline\s+)*[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
    re.M,
)


def _split_list(value) -> list[str]:
    if isinstance(value, list):
        return [v.strip() for v in value if v.strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def card_id_of(path: Path) -> str:
    return re.sub(r"\.md.*$", "", path.name)


# ---- C source inspection: find a function's definition span and stub-ness ----

def find_function_span(text: str, name: str) -> tuple[int, int] | None:
    """(start, end) char offsets of the brace-matched body of a top-level
    definition of `name` in `text`, or None if it is not defined there."""
    pattern = re.compile(
        r"^[ \t]*(?:static\s+|inline\s+)*[A-Za-z_][\w\s\*]*?\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{",
        re.M,
    )
    m = pattern.search(text)
    if not m:
        return None
    depth = 0
    i = m.end() - 1  # the opening '{'
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return m.start(), i + 1
        i += 1
    return m.start(), len(text)


def is_stub_body(body_text: str) -> bool:
    return re.search(r"\bSTUB\b", body_text) is not None


def all_defined_symbols(text: str) -> list[str]:
    return [m.group(1) for m in _C_TOPLEVEL_DEF.finditer(text)]


def find_symbol_definitions(csrc_dir: Path, symbols: set[str]) -> dict[str, list[dict]]:
    """symbol -> list of {"file": "csrc/x.c", "stub": bool}, one entry per .c
    file in csrc_dir that defines it (normally one; more is a real compile
    error but still worth reporting rather than silently picking one)."""
    results: dict[str, list[dict]] = {s: [] for s in symbols}
    for c_file in sorted(csrc_dir.glob("*.c")):
        text = c_file.read_text()
        for sym in symbols:
            span = find_function_span(text, sym)
            if span is None:
                continue
            body = text[span[0]:span[1]]
            results[sym].append({"file": f"csrc/{c_file.name}", "stub": is_stub_body(body)})
    return results


# ---- static symbol collection: what om_* symbols does a test reach? ----

def _literal_str(node: ast.AST | None, bindings: dict[str, str]) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in bindings:
        return bindings[node.id]
    return None


def _bind_call_args(func_def: ast.FunctionDef, call: ast.Call, outer_bindings: dict[str, str]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    params = [a.arg for a in func_def.args.args]
    for i, arg in enumerate(call.args):
        if i < len(params):
            val = _literal_str(arg, outer_bindings)
            if val is not None:
                bindings[params[i]] = val
    for kw in call.keywords:
        if kw.arg:
            val = _literal_str(kw.value, outer_bindings)
            if val is not None:
                bindings[kw.arg] = val
    return bindings


def _collect_from_node(node: ast.AST, bindings: dict[str, str],
                        helper_defs: dict[str, ast.FunctionDef], visiting: frozenset[str]) -> set[str]:
    found: set[str] = set()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if isinstance(func, ast.Attribute) and OM_SYMBOL_RE.match(func.attr):
            found.add(func.attr)
        elif isinstance(func, ast.Name) and func.id == "getattr":
            if len(call.args) > 1:
                val = _literal_str(call.args[1], bindings)
                if val and OM_SYMBOL_RE.match(val):
                    found.add(val)
        elif isinstance(func, ast.Name) and func.id in helper_defs and func.id not in visiting:
            callee = helper_defs[func.id]
            new_bindings = _bind_call_args(callee, call, bindings)
            found |= _collect_from_node(callee, new_bindings, helper_defs, visiting | {func.id})
    return found


def helper_defs_of(conftest_path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(conftest_path.read_text(), filename=str(conftest_path))
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def symbols_of_function(func: ast.FunctionDef, helper_defs: dict[str, ast.FunctionDef]) -> set[str]:
    return _collect_from_node(func, {}, helper_defs, frozenset())


def parse_node_id(node_id: str) -> tuple[str, str | None]:
    if "::" in node_id:
        file_part, _, rest = node_id.partition("::")
        return file_part, rest
    return node_id, None


def resolve_test_targets(test_path: Path, test_name: str | None) -> list[ast.FunctionDef]:
    tree = ast.parse(test_path.read_text(), filename=str(test_path))
    by_name = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if test_name is None:
        return [n for name, n in by_name.items() if name.startswith("test_")]
    base_name = test_name.split("[", 1)[0]
    if base_name not in by_name:
        raise KeyError(base_name)
    return [by_name[base_name]]


def acceptance_node_id_tokens(cmd: str) -> list[str]:
    if not PYTEST_RE.search(cmd):
        return []
    return [tok for tok in cmd.split() if ".py" in tok]


def collect_acceptance_symbols(card: dict, project: Path) -> tuple[set[str], list[str]]:
    """(symbols, bad_node_ids). bad_node_ids are acceptance tokens naming a
    test file or test function that does not exist (rule e)."""
    symbols: set[str] = set()
    bad_node_ids: list[str] = []
    helper_cache: dict[Path, dict[str, ast.FunctionDef]] = {}

    for cmd in card.get("acceptance") or []:
        for tok in acceptance_node_id_tokens(cmd):
            file_part, test_name = parse_node_id(tok)
            test_path = project / file_part
            if not test_path.is_file():
                bad_node_ids.append(tok)
                continue
            conftest_dir = test_path.parent
            if conftest_dir not in helper_cache:
                conftest_path = conftest_dir / "conftest.py"
                helper_cache[conftest_dir] = helper_defs_of(conftest_path) if conftest_path.is_file() else {}
            helper_defs = helper_cache[conftest_dir]
            try:
                funcs = resolve_test_targets(test_path, test_name)
            except KeyError:
                bad_node_ids.append(tok)
                continue
            for func in funcs:
                symbols |= symbols_of_function(func, helper_defs)

    return symbols, bad_node_ids


# ---- rule (f): does another card already own this stub symbol? ----

def _iter_queue_cards(queue: Path):
    if queue.is_dir():
        for p in sorted(queue.glob("*.md")):
            yield p
        parked = queue / "parked"
        if parked.is_dir():
            for p in sorted(parked.iterdir()):
                if p.is_file():
                    yield p


def find_owning_card(queue: Path, symbol: str, exclude_path: Path, this_snippet_file: str) -> str | None:
    """Card id of another queued/parked card whose snippet_symbol lists
    `symbol` and whose snippet_file differs from this_snippet_file, or None."""
    exclude_resolved = exclude_path.resolve()
    for p in _iter_queue_cards(queue):
        if p.resolve() == exclude_resolved:
            continue
        try:
            other = parse_card(p)
        except Exception:
            continue
        other_symbols = set(_split_list(other.get("snippet_symbol", "")))
        if symbol not in other_symbols:
            continue
        other_snippet_file = other.get("snippet_file", "")
        if other_snippet_file and other_snippet_file != this_snippet_file:
            return card_id_of(p)
    return None


# ---- findings ----

class Finding(dict):
    def __init__(self, level: str, code: str, message: str):
        super().__init__(level=level, code=code, message=message)


def lint(card_path: Path, project: Path, queue: Path) -> tuple[list[Finding], list[str]]:
    """Returns (findings, errors). errors is non-empty only for usage/parse
    problems (exit 2 territory); the caller decides how to report them."""
    errors: list[str] = []
    try:
        card = parse_card(card_path)
    except ValueError as exc:
        return [], [str(exc)]

    if not project.is_dir():
        return [], [f"project is not a directory: {project}"]

    acceptance = card.get("acceptance") or []
    if not acceptance:
        return [], [f"{card_path}: no acceptance commands"]

    findings: list[Finding] = []
    allowed_files = set(_split_list(card.get("allowed_files", "")))
    snippet_file = card.get("snippet_file", "")
    snippet_symbols = _split_list(card.get("snippet_symbol", ""))

    symbols, bad_node_ids = collect_acceptance_symbols(card, project)

    # (e) bad node ids
    for tok in bad_node_ids:
        findings.append(Finding("FAIL", "BAD_NODE_ID", f"acceptance node id does not exist: {tok}"))

    # (d) sizing
    if len(snippet_symbols) > MAX_SNIPPET_SYMBOLS:
        findings.append(Finding(
            "FAIL", "SIZING_SYMBOLS",
            f"{len(snippet_symbols)} snippet_symbols > max {MAX_SNIPPET_SYMBOLS}: {snippet_symbols}",
        ))
    try:
        expected_lines = int(card.get("expected_lines", 0))
    except (TypeError, ValueError):
        expected_lines = 0
    if expected_lines > MAX_EXPECTED_LINES:
        findings.append(Finding(
            "FAIL", "SIZING_LINES",
            f"expected_lines {expected_lines} > max {MAX_EXPECTED_LINES}",
        ))

    # (c) snippet_symbol not defined in snippet_file
    snippet_path = project / snippet_file if snippet_file else None
    snippet_text = ""
    if snippet_path is not None:
        if snippet_path.is_file():
            snippet_text = snippet_path.read_text()
        else:
            findings.append(Finding("FAIL", "SNIPPET_FILE_MISSING", f"snippet_file does not exist: {snippet_file}"))
    for sym in snippet_symbols:
        if snippet_text and find_function_span(snippet_text, sym) is None:
            findings.append(Finding(
                "FAIL", "SNIPPET_SYMBOL_UNDEFINED",
                f"snippet_symbol {sym!r} is not defined in {snippet_file}",
            ))

    # (a)/(b)/(f) resolve every acceptance-reached symbol
    csrc_dir = project / "csrc"
    definitions = find_symbol_definitions(csrc_dir, symbols) if csrc_dir.is_dir() else {}
    for sym in sorted(symbols):
        defs = definitions.get(sym, [])
        if not defs:
            findings.append(Finding("FAIL", "ABI_GAP", f"{sym} is defined nowhere in csrc/*.c"))
            continue
        for d in defs:
            if not d["stub"]:
                continue
            if d["file"] in allowed_files:
                continue
            owner = find_owning_card(queue, sym, card_path, snippet_file)
            if owner:
                findings.append(Finding(
                    "FAIL", "SPANS_ANOTHER_CARD",
                    f"{sym} is a STUB in {d['file']} (outside allowed_files); owned by card {owner}",
                ))
            else:
                findings.append(Finding(
                    "FAIL", "STUB_OUTSIDE_ALLOWED",
                    f"{sym} is a STUB in {d['file']}, which is outside allowed_files {sorted(allowed_files)}",
                ))

    # warn: a stub in the card's own snippet_file that this card does not name
    if snippet_text:
        named = set(snippet_symbols)
        for name in all_defined_symbols(snippet_text):
            if name in named:
                continue
            span = find_function_span(snippet_text, name)
            if span and is_stub_body(snippet_text[span[0]:span[1]]):
                findings.append(Finding(
                    "WARN", "OWN_FILE_STUB_NOT_NAMED",
                    f"{name} is a STUB in {snippet_file} but is not named in snippet_symbol",
                ))

    return findings, errors


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card_file")
    ap.add_argument("--project", help="defaults to the card's project: field")
    ap.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ap.add_argument("--json", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2

    card_path = Path(args.card_file)
    if not card_path.is_file():
        print(f"card not found: {card_path}", file=sys.stderr)
        return 2

    try:
        card = parse_card(card_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    project = Path(args.project).expanduser() if args.project else Path(card.get("project", "")).expanduser()
    queue = Path(args.queue).expanduser()

    findings, errors = lint(card_path, project, queue)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 2

    cid = card_id_of(card_path)
    fail_count = sum(1 for f in findings if f["level"] == "FAIL")

    if args.json:
        print(json.dumps({
            "card": cid,
            "findings": findings,
            "ok": fail_count == 0,
            "fail_count": fail_count,
        }, indent=2))
    else:
        for f in findings:
            print(f"LINT {f['level']} {cid} {f['code']} {f['message']}")
        if fail_count == 0:
            print("LINT OK")
        else:
            print(f"LINT FAILED ({fail_count})")

    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
