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


def function_signature(text: str, name: str) -> str | None:
    """The verbatim `ret name(params)` text of a top-level definition of
    `name` in `text` (up to, not including, the opening `{`), or None if it
    is not defined there."""
    pattern = re.compile(
        r"^[ \t]*(?:static\s+|inline\s+)*[A-Za-z_][\w\s\*]*?\b" + re.escape(name) + r"\s*\([^;{}]*\)(?=\s*\{)",
        re.M,
    )
    m = pattern.search(text)
    return m.group(0) if m else None


def _first_param(signature: str) -> str | None:
    m = re.search(r"\(([^)]*)\)\s*$", signature)
    if not m:
        return None
    params = m.group(1).split(",")
    return params[0] if params else None


def takes_nonconst_world_first(signature: str) -> bool:
    """True if `signature`'s first parameter is a plain (non-const)
    `om_world *` -- a function that can structurally mutate the world."""
    p = _first_param(signature)
    return p is not None and re.match(r"\s*om_world\s*\*", p) is not None


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


def helper_defs_of(py_path: Path) -> dict[str, ast.FunctionDef]:
    """Every module-level function defined in `py_path` (a conftest.py, or a
    test module itself -- both are just a bag of possible helpers)."""
    tree = ast.parse(py_path.read_text(), filename=str(py_path))
    return {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def symbols_of_function(func: ast.FunctionDef, helper_defs: dict[str, ast.FunctionDef]) -> set[str]:
    return _collect_from_node(func, {}, helper_defs, frozenset())


def parse_node_id(node_id: str) -> tuple[str, str | None]:
    if "::" in node_id:
        file_part, _, rest = node_id.partition("::")
        return file_part, rest
    return node_id, None


def acceptance_node_id_tokens(cmd: str) -> list[str]:
    if not PYTEST_RE.search(cmd):
        return []
    return [tok for tok in cmd.split() if ".py" in tok]


def conftest_chain_helpers(start_dir: Path, project_root: Path,
                            cache: dict[Path, dict[str, ast.FunctionDef]]) -> dict[str, ast.FunctionDef]:
    """Merges helpers from every conftest.py between `start_dir` and
    `project_root` inclusive, nearest-last (so a nearer conftest's helper
    wins a same-name collision) -- pytest applies tests/csim/conftest.py to
    tests/csim/controls/*.py the same way, walking the whole subtree, not
    just a test file's own directory."""
    chain: list[Path] = []
    d = start_dir.resolve()
    while True:
        chain.append(d)
        if d == project_root:
            break
        d = d.parent
    chain.reverse()

    merged: dict[str, ast.FunctionDef] = {}
    for d in chain:
        conftest_path = d / "conftest.py"
        if conftest_path not in cache:
            cache[conftest_path] = helper_defs_of(conftest_path) if conftest_path.is_file() else {}
        merged.update(cache[conftest_path])
    return merged


def collect_acceptance_symbols(card: dict, project: Path) -> tuple[set[str], list[str]]:
    """(symbols, bad_node_ids). bad_node_ids are acceptance tokens naming a
    test file or test function that does not exist (rule e)."""
    symbols: set[str] = set()
    bad_node_ids: list[str] = []
    conftest_cache: dict[Path, dict[str, ast.FunctionDef]] = {}
    module_cache: dict[Path, dict[str, ast.FunctionDef]] = {}
    project_root = project.resolve()

    for cmd in card.get("acceptance") or []:
        for tok in acceptance_node_id_tokens(cmd):
            file_part, test_name = parse_node_id(tok)
            test_path = project / file_part
            if not test_path.is_file():
                bad_node_ids.append(tok)
                continue

            if test_path not in module_cache:
                module_cache[test_path] = helper_defs_of(test_path)
            module_defs = module_cache[test_path]

            if test_name is None:
                targets = [n for name, n in module_defs.items() if name.startswith("test_")]
            else:
                base_name = test_name.split("[", 1)[0]
                if base_name not in module_defs:
                    bad_node_ids.append(tok)
                    continue
                targets = [module_defs[base_name]]

            conftest_helpers = conftest_chain_helpers(test_path.parent, project_root, conftest_cache)
            # module-level functions in the test file itself are helpers too
            # (a local def shadows a same-named conftest import, same as
            # Python's own name resolution would).
            helper_defs = {**conftest_helpers, **module_defs}
            for func in targets:
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
    snippet_files = _split_list(snippet_file)
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

    # (c) snippet_symbol not defined in any listed snippet_file. snippet_file
    # may name more than one file, comma-separated like allowed_files, when a
    # card's snippet_symbols genuinely live in different .c files (e.g. a new
    # step function in one file plus a narrow deferral change to an existing
    # function in another) -- a single file is still the common case and
    # works exactly as before.
    snippet_texts: dict[str, str] = {}
    for sf in snippet_files:
        sp = project / sf
        if sp.is_file():
            snippet_texts[sf] = sp.read_text()
        else:
            findings.append(Finding("FAIL", "MISSING_SNIPPET_FILE", f"snippet_file does not exist: {sf}"))
    snippet_text = "\n".join(snippet_texts.values())  # combined, for the CONST_ONLY/WARN scans below
    for sym in snippet_symbols:
        if snippet_texts and not any(find_function_span(t, sym) is not None for t in snippet_texts.values()):
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

    # (g) CONST_ONLY: the card's snippet_file defines no function that can
    # mutate the world (every top-level definition takes `const om_world *`
    # first, or no om_world* at all), yet the acceptance tests drive
    # om_world_step and assert on the state it produces. This is the 205a
    # class of defect: the card's entire writable surface is a read-back, so
    # nothing in the file it owns can ever produce the mutated state its own
    # acceptance asserts on. Checked over the whole file, not just the
    # declared snippet_symbol(s) -- a card whose file also defines a real
    # mutating step function (e.g. agent.c's om_step_decisions alongside its
    # const om_faction_candidates reader) is a normal, valid shape.
    if snippet_symbols and snippet_text and "om_world_step" in symbols:
        file_symbols = all_defined_symbols(snippet_text)
        signatures = [function_signature(snippet_text, sym) for sym in file_symbols]
        has_mutator = any(sig and takes_nonconst_world_first(sig) for sig in signatures if sig)
        if not has_mutator:
            findings.append(Finding(
                "FAIL", "CONST_ONLY",
                f"{snippet_file} defines no function that can mutate the world "
                f"(every definition takes `const om_world *` or no om_world* at "
                f"all), but acceptance calls om_world_step and asserts on world "
                f"state afterwards -- snippet_symbol {snippet_symbols}",
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


# ---- fuel report: buildable / blocked-by-missing-file / blocked-by-ABI-gap /
# blocked-by-open-Q, over a whole queue, so the cascade's runway line has a
# mechanical source instead of a guess (audit 2026-09-21, item 2). ----

DEFAULT_PROJECT = Path("/home/westopoli/Projects/ouroboros-manifold")
DEFAULT_REGISTER = DEFAULT_PROJECT / "docs/northstar/ambiguity_register.md"
EPIC_RE = re.compile(r"E-?(\d+)")


def _normalize_epic(text: str) -> str | None:
    m = EPIC_RE.search(text)
    return f"E-{int(m.group(1)):02d}" if m else None


def open_epics(register_path: Path) -> set[str]:
    """Epic ids (e.g. "E-05") carrying at least one 'open' row in the
    ambiguity register's "Epic / story" column. CLAUDE.md: "an epic with an
    open flag is not built"."""
    if not register_path.is_file():
        return set()
    epics: set[str] = set()
    for line in register_path.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 5 or not cols[0].startswith("Q-"):
            continue
        if cols[4].lower() != "open":
            continue
        epic = _normalize_epic(cols[1])
        if epic:
            epics.add(epic)
    return epics


def epic_of_card(card: dict) -> str | None:
    for field in ("rules_file", "test_file", "goal"):
        val = card.get(field)
        if isinstance(val, str):
            epic = _normalize_epic(val)
            if epic:
                return epic
    return None


def _iter_live_and_held_cards(queue: Path):
    """Cards still actually in play for a runway count: every `queue/*.md`
    (live) plus every `queue/parked/*.hold` (waiting its turn in
    RELEASE_CHAIN) -- not `.retired`/`.superseded`/`.legacy`/
    `.satisfied-by-*`/`.harness-bug`/`.blocked`/`.done-archived`, which are
    already resolved one way or another and would double-count or pad the
    runway with dead cards."""
    if not queue.is_dir():
        return
    for p in sorted(queue.glob("*.md")):
        yield p
    parked = queue / "parked"
    if parked.is_dir():
        for p in sorted(parked.glob("*.hold")):
            yield p


def fuel_report(queue: Path, project: Path, register_path: Path) -> dict:
    stalled_epics = open_epics(register_path)
    buckets: dict[str, list[str]] = {
        "buildable": [], "missing_file": [], "abi_gap": [], "open_q": [], "other_blocked": [],
    }
    per_epic: dict[str, dict[str, int]] = {}

    for card_path in _iter_live_and_held_cards(queue):
        try:
            card = parse_card(card_path)
        except Exception:
            continue
        if card.get("kind") == "gate":
            continue
        cid = card_id_of(card_path)
        epic = epic_of_card(card) or "unknown"
        per_epic.setdefault(epic, {"buildable": 0, "missing_file": 0, "abi_gap": 0, "open_q": 0, "other_blocked": 0})

        if epic in stalled_epics:
            bucket = "open_q"
        else:
            findings, errors = lint(card_path, project, queue)
            if errors:
                bucket = "other_blocked"
            else:
                codes = {f["code"] for f in findings if f["level"] == "FAIL"}
                if "MISSING_SNIPPET_FILE" in codes:
                    bucket = "missing_file"
                elif "ABI_GAP" in codes:
                    bucket = "abi_gap"
                elif codes:
                    bucket = "other_blocked"
                else:
                    bucket = "buildable"

        buckets[bucket].append(cid)
        per_epic[epic][bucket] += 1

    return {"buckets": buckets, "per_epic": per_epic, "stalled_epics": sorted(stalled_epics)}


def print_fuel_report(report: dict) -> None:
    b = report["buckets"]
    print(f"buildable now:        {len(b['buildable'])}")
    print(f"blocked (missing file): {len(b['missing_file'])}")
    print(f"blocked (ABI gap):     {len(b['abi_gap'])}")
    print(f"blocked (open Q-):     {len(b['open_q'])}")
    print(f"blocked (other FAIL):  {len(b['other_blocked'])}")
    print()
    print("per epic:")
    for epic in sorted(report["per_epic"]):
        counts = report["per_epic"][epic]
        total = sum(counts.values())
        print(f"  {epic}: {total} cards -- buildable={counts['buildable']} "
              f"missing_file={counts['missing_file']} abi_gap={counts['abi_gap']} "
              f"open_q={counts['open_q']} other={counts['other_blocked']}")
    if report["stalled_epics"]:
        print()
        print("epics with an open ambiguity-register flag (not built): " + ", ".join(report["stalled_epics"]))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("card_file", nargs="?")
    ap.add_argument("--project", help="defaults to the card's project: field")
    ap.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fuel", metavar="QUEUE", nargs="?", const=str(DEFAULT_QUEUE),
                     help="report mode: buildable/blocked counts over a whole queue instead of linting one card")
    ap.add_argument("--register", default=str(DEFAULT_REGISTER))
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2

    if args.fuel is not None:
        queue = Path(args.fuel).expanduser()
        project = Path(args.project).expanduser() if args.project else DEFAULT_PROJECT
        report = fuel_report(queue, project, Path(args.register).expanduser())
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_fuel_report(report)
        return 0

    if not args.card_file:
        print("card_file is required unless --fuel is given", file=sys.stderr)
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
