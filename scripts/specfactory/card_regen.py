#!/usr/bin/env python3
"""Regenerates per-story build cards for an epic from the om_* symbols its
own tests actually call (DECISIONS.md R22: the queue's one placeholder card
per story for E-03 and E-06 through E-17 names an epic-wide step symbol
(`om_diplomacy_step`, ...) that no test calls, while the tests call about
600 per-story symbols no card names).

Reads the epic's existing queue cards (read-only) only to learn: which
module (`snippet_file`) the epic owns, and to reuse `rules_file`,
`header_file`, `extra_context_files`, `max_wall_minutes`, `project`, and the
numbering prefix each story already has. Writes new cards to a scratch
output directory only -- never to the queue, never to csrc/, never to
tests/.

For every tests/csim/test_E<NN>_S<###>_*.py of the epic: collects the
om_* symbols each test function calls (directly, or through the same
conftest.py/test-module helper chain card_lint.py walks); a symbol already
defined in csrc/*.c with a non-STUB body is "built" and excluded. The
story's remaining (unbuilt) symbols are ordered by first appearance across
its tests (a symbol that co-occurs with an earlier symbol in the same test
sorts after it; helper-call symbols are inlined at the call site) and cut
into cards of at most 5 symbols. A test's acceptance line is assigned to
the earliest card whose cumulative symbol set covers that test's own
unbuilt closure, so no card's acceptance ever spans a stub outside itself.

Usage:
    scripts/specfactory/card_regen.py E-06 [E-07 ...] --out ROOT
        [--project P] [--queue Q] [--report] [--json]

With --out, writes ROOT/<epic>/<card-id>.md for every generated card plus
ROOT/<epic>/report.md, for every epic given. With --report, prints the
listing and writes nothing. --json prints the full structured result
instead of (or alongside, with neither --out nor --report suppressing it)
the plain-text listing.

When more than one epic is given in the same invocation, also computes
cross-epic symbol overlap (a symbol whose unbuilt set appears in more than
one of the given epics) and writes ROOT/cross_epic.md.

Exit code 0 on success. Exit code 2 on a usage error, or when an epic has
no existing queue card to learn its module/prefix from.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import card_lint as cl  # noqa: E402  (reuse symbol-collection + C-scan machinery)
from green_check import parse_card  # noqa: E402  (reuse the frontmatter parser)

MAX_SNIPPET_SYMBOLS = cl.MAX_SNIPPET_SYMBOLS  # 5
MAX_EXPECTED_LINES = cl.MAX_EXPECTED_LINES  # 80
LINES_PER_SYMBOL = 12
MAX_CARDS_BEFORE_OVERSIZED = 6

DEFAULT_PROJECT = cl.DEFAULT_PROJECT
DEFAULT_QUEUE = cl.DEFAULT_QUEUE

TEST_FILE_RE = re.compile(r"^test_E(\d+)_S(\d{3})_.*\.py$")
OLD_CARD_ID_RE = re.compile(r"^(\d+)([a-z])\d*-(.+)$")
STORY_HEADING_RE = re.compile(r"^###\s+(S-\d{3})\b")
RULE_LINE_RE = re.compile(r"^-\s+(R-\d{3}-\d{2})\b")
PYTEST_EXE_RE = re.compile(r"^(\S+)\s+-m\s+pytest\b")


# ---- ordered symbol collection (first-appearance order, same walk as
# card_lint's set-based _collect_from_node, but position-tracked so helper
# calls are inlined at their own call site) ----

def _ordered_events(node: ast.AST, bindings: dict[str, str],
                     helper_defs: dict[str, ast.FunctionDef], visiting: frozenset[str]) -> list[tuple[tuple, str]]:
    events: list[tuple[tuple, str]] = []
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        pos = (call.lineno, call.col_offset)
        if isinstance(func, ast.Attribute) and cl.OM_SYMBOL_RE.match(func.attr):
            events.append((pos + (0,), func.attr))
        elif isinstance(func, ast.Name) and func.id == "getattr":
            if len(call.args) > 1:
                val = cl._literal_str(call.args[1], bindings)
                if val and cl.OM_SYMBOL_RE.match(val):
                    events.append((pos + (0,), val))
        elif isinstance(func, ast.Name) and func.id in helper_defs and func.id not in visiting:
            callee = helper_defs[func.id]
            new_bindings = cl._bind_call_args(callee, call, bindings)
            sub = _ordered_events(callee, new_bindings, helper_defs, visiting | {func.id})
            for j, (_, sym) in enumerate(sub):
                events.append((pos + (j + 1,), sym))
    return events


def ordered_symbols_of_function(func: ast.FunctionDef, helper_defs: dict[str, ast.FunctionDef]) -> list[str]:
    events = _ordered_events(func, {}, helper_defs, frozenset())
    events.sort(key=lambda e: e[0])
    seen: set[str] = set()
    order: list[str] = []
    for _, sym in events:
        if sym not in seen:
            seen.add(sym)
            order.append(sym)
    return order


# ---- epic bible rule extraction ----

def parse_epic_rules(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """(rule_id -> verbatim rule line, story_id -> verbatim heading line)."""
    rule_lines: dict[str, str] = {}
    story_heading: dict[str, str] = {}
    current_story: str | None = None
    for line in text.splitlines():
        hm = STORY_HEADING_RE.match(line)
        if hm:
            current_story = hm.group(1)
            story_heading[current_story] = line.rstrip()
            continue
        rm = RULE_LINE_RE.match(line.lstrip())
        if rm and current_story:
            rule_lines[rm.group(1)] = line.rstrip()
    return rule_lines, story_heading


def find_epic_bible_file(project: Path, epic: str) -> Path | None:
    matches = sorted((project / "docs" / "bible" / "epics").glob(f"{epic}-*.md"))
    return matches[0] if matches else None


# ---- old-queue discovery: module, shared fields, per-story numbering prefix ----

def iter_epic_source_cards(queue: Path):
    """Same live-and-waiting filter skeleton_gen.py uses: queue/*.md plus
    queue/parked/*.md.hold -- every other parked suffix is already resolved
    and not a source of truth for a story's numbering."""
    if not queue.is_dir():
        return
    for p in sorted(queue.glob("*.md")):
        yield p
    parked = queue / "parked"
    if parked.is_dir():
        for p in sorted(parked.glob("*.md.hold")):
            yield p


def load_epic_cards(queue: Path, epic: str) -> list[tuple[Path, dict]]:
    out = []
    for p in iter_epic_source_cards(queue):
        try:
            card = parse_card(p)
        except Exception:
            continue
        if cl.epic_of_card(card) == epic:
            out.append((p, card))
    return out


def story_num_of(card: dict) -> str | None:
    tf = card.get("test_file", "")
    if not isinstance(tf, str):
        return None
    m = re.search(r"S(\d{3})", tf)
    return m.group(1) if m else None


def card_stem(path: Path) -> str:
    name = path.name
    for suf in (".md.hold", ".md"):
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def epic_shared_fields(cards: list[tuple[Path, dict]]) -> dict:
    sample = cards[0][1]
    module_files = cl._split_list(sample.get("snippet_file", ""))
    py_exe = "python"
    for cmd in sample.get("acceptance") or []:
        m = PYTEST_EXE_RE.match(cmd.strip())
        if m:
            py_exe = m.group(1)
            break
    return {
        "project": sample.get("project", str(DEFAULT_PROJECT)),
        "module_file": module_files[0] if module_files else "",
        "header_file": sample.get("header_file", ""),
        "extra_context_files": sample.get("extra_context_files", ""),
        "rules_file": sample.get("rules_file", ""),
        "max_wall_minutes": sample.get("max_wall_minutes", ""),
        "py_exe": py_exe,
        "old_placeholder_symbols": sorted({
            sym for _, c in cards for sym in cl._split_list(c.get("snippet_symbol", ""))
        }),
    }


def story_numbering(cards: list[tuple[Path, dict]]) -> dict[str, tuple[str, str, str]]:
    """story number ("042") -> (prefix, letter, tail), read from any one of
    the story's existing cards -- every old card for a story shares the same
    prefix and tail, only the a<N> suffix and symbol differ."""
    out: dict[str, tuple[str, str, str]] = {}
    for p, c in cards:
        num = story_num_of(c)
        if not num or num in out:
            continue
        m = OLD_CARD_ID_RE.match(card_stem(p))
        if not m:
            continue
        out[num] = (m.group(1), m.group(2), m.group(3))
    return out


# ---- per-story regeneration ----

def _unbuilt(symbols: set[str], csrc_dir: Path, already_available: set[str]) -> set[str]:
    if not symbols:
        return set()
    definitions = cl.find_symbol_definitions(csrc_dir, symbols) if csrc_dir.is_dir() else {}
    built = {s for s in symbols if any(not d["stub"] for d in definitions.get(s, []))}
    return symbols - built - already_available


def regen_story(test_path: Path, tests_dir: Path, csrc_dir: Path,
                 prefix: str, letter: str, tail: str,
                 rule_lines: dict[str, str], story_heading: dict[str, str],
                 shared: dict, conftest_cache: dict, epic_claimed: set[str]) -> dict:
    """epic_claimed is every symbol an earlier story of this SAME epic (all
    stories share one module file) already assigned to a card in this run --
    a later story's tests may still call it, but it is treated as available,
    not re-carded, so two cards never both claim to define the same function
    in the same file (the sequential_owner pattern, DECISIONS.md R21).
    Stories are processed in story-number order, so "earlier" means lower
    story number."""
    module_defs = cl.helper_defs_of(test_path)
    test_funcs = sorted(
        ((name, node) for name, node in module_defs.items() if name.startswith("test_")),
        key=lambda kv: kv[1].lineno,
    )
    conftest_helpers = cl.conftest_chain_helpers(test_path.parent, tests_dir, conftest_cache)
    helper_defs = {**conftest_helpers, **module_defs}

    symbols_per_test: dict[str, set[str]] = {
        name: cl.symbols_of_function(node, helper_defs) for name, node in test_funcs
    }
    all_symbols: set[str] = set().union(*symbols_per_test.values()) if symbols_per_test else set()
    unbuilt_all = _unbuilt(all_symbols, csrc_dir, epic_claimed)
    unbuilt_per_test = {name: (syms & unbuilt_all) for name, syms in symbols_per_test.items()}

    order: list[str] = []
    seen: set[str] = set()
    for name, node in test_funcs:
        for sym in ordered_symbols_of_function(node, helper_defs):
            if sym in unbuilt_all and sym not in seen:
                seen.add(sym)
                order.append(sym)
    no_test_order_fallback = sorted(unbuilt_all - seen)  # should stay empty; see report
    order += no_test_order_fallback

    story_num = re.search(r"S(\d{3})", test_path.name).group(1)
    story_id = f"S-{story_num}"

    result = {
        "story_id": story_id,
        "test_file": f"tests/csim/{test_path.name}",
        "cards": [],
        "already_satisfiable": [],
        "no_test_order_fallback": no_test_order_fallback,
        "oversized": False,
        "missing_rule_ids": [],
    }

    if not order:
        result["already_satisfiable"] = [name for name, _ in test_funcs]
        return result

    chunks = [order[i:i + MAX_SNIPPET_SYMBOLS] for i in range(0, len(order), MAX_SNIPPET_SYMBOLS)]
    result["oversized"] = len(chunks) > MAX_CARDS_BEFORE_OVERSIZED

    cum: list[str] = []
    cum_sets: list[set[str]] = []
    for chunk in chunks:
        cum = cum + chunk
        cum_sets.append(set(cum))

    card_tests: list[list[str]] = [[] for _ in chunks]
    for name, _node in test_funcs:
        closure = unbuilt_per_test[name]
        if not closure:
            result["already_satisfiable"].append(name)
            continue
        k = next((i for i, s in enumerate(cum_sets) if closure <= s), len(chunks) - 1)
        card_tests[k].append(name)

    n = len(chunks)
    heading = story_heading.get(story_id, f"### {story_id}")

    for i, chunk in enumerate(chunks):
        seq = i + 1
        card_id = f"{prefix}{letter}{seq if n > 1 else ''}-{tail}"
        tests = card_tests[i]
        rule_ids = sorted({
            f"R-{rm.group(1)}-{rm.group(2)}"
            for name in tests
            for rm in [cl.TEST_RULE_ID_RE.match(name)] if rm
        })
        quoted_lines = []
        for rid in rule_ids:
            line = rule_lines.get(rid)
            if line is None:
                result["missing_rule_ids"].append(rid)
            else:
                quoted_lines.append(line)

        acceptance = [
            f"{shared['py_exe']} -m pytest -q -p no:cacheprovider "
            f"tests/csim/{test_path.name}::{name}"
            for name in tests
        ]
        expected_lines = min(MAX_EXPECTED_LINES, LINES_PER_SYMBOL * len(chunk))
        goal = (
            f"{shared['module_file']} implements {story_id} card {seq} of {n} "
            f"({', '.join(chunk)})"
        )
        result["cards"].append({
            "card_id": card_id,
            "symbols": chunk,
            "tests": tests,
            "acceptance": acceptance,
            "rule_ids": rule_ids,
            "quoted_lines": quoted_lines,
            "heading": heading,
            "expected_lines": expected_lines,
            "goal": goal,
        })

    return result


def render_card(card: dict, shared: dict, epic: str, bible_file: str, test_file_rel: str) -> str:
    def q(s: str) -> str:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = ["---"]
    lines.append(f"project: {shared['project']}")
    lines.append(f"goal: {q(card['goal'])}")
    lines.append("acceptance:")
    for cmd in card["acceptance"]:
        lines.append(f"  - {q(cmd)}")
    lines.append(f"allowed_files: {q(shared['module_file'])}")
    lines.append(f"snippet_file: {shared['module_file']}")
    lines.append(f"snippet_symbol: {q(','.join(card['symbols']))}")
    if shared["header_file"]:
        lines.append(f"header_file: {shared['header_file']}")
    if shared["extra_context_files"]:
        lines.append(f"extra_context_files: {shared['extra_context_files']}")
    if shared["rules_file"]:
        lines.append(f"rules_file: {shared['rules_file']}")
    lines.append(f"test_file: {test_file_rel}")
    lines.append(f"expected_lines: {card['expected_lines']}")
    if shared["max_wall_minutes"] != "":
        lines.append(f"max_wall_minutes: {shared['max_wall_minutes']}")
    lines.append("---")
    lines.append("")
    lines.append("## Brief for DeepSeek")
    lines.append("")
    lines.append(f"Quoted verbatim from {bible_file} ({card['heading']}):")
    lines.append("")
    for line in card["quoted_lines"]:
        lines.append(line)
    lines.append("")
    lines.append("## Header slice")
    lines.append("")
    lines.append("(run card_slice.py --write after the skeleton lands)")
    lines.append("")
    return "\n".join(lines)


# ---- epic-level driver ----

def regen_epic(epic: str, project: Path, queue: Path) -> dict:
    epic = cl._normalize_epic(epic) or epic
    epic_num_m = re.match(r"E-(\d+)", epic)
    if not epic_num_m:
        raise ValueError(f"not an epic id: {epic}")
    epic_num = int(epic_num_m.group(1))

    old_cards = load_epic_cards(queue, epic)
    if not old_cards:
        raise ValueError(f"no existing queue cards found for {epic} under {queue}")

    shared = epic_shared_fields(old_cards)
    numbering = story_numbering(old_cards)

    tests_dir = project / "tests" / "csim"
    csrc_dir = project / "csrc"
    bible_path = find_epic_bible_file(project, epic)
    rule_lines, story_heading = parse_epic_rules(bible_path.read_text()) if bible_path else ({}, {})
    bible_file_rel = f"docs/bible/epics/{bible_path.name}" if bible_path else "docs/bible/epics/<not found>"

    test_files = sorted(tests_dir.glob(f"test_E{epic_num:02d}_S*_*.py")) if tests_dir.is_dir() else []

    conftest_cache: dict = {}
    stories: list[dict] = []
    missing_numbering: list[str] = []
    epic_claimed: set[str] = set()  # sequential ownership across stories, R21

    for tf in test_files:
        m = TEST_FILE_RE.match(tf.name)
        if not m:
            continue
        story_num = m.group(2)
        if story_num not in numbering:
            missing_numbering.append(f"S-{story_num}")
            continue
        prefix, letter, tail = numbering[story_num]
        story_result = regen_story(
            tf, tests_dir, csrc_dir, prefix, letter, tail,
            rule_lines, story_heading, shared, conftest_cache, epic_claimed,
        )
        for c in story_result["cards"]:
            epic_claimed.update(c["symbols"])
        stories.append(story_result)

    # symbols the old placeholder card(s) named that no test calls (R22,
    # re-confirmed here rather than assumed): every symbol any test in this
    # epic calls, across every story file, whether built or not.
    all_called: set[str] = set()
    for tf in test_files:
        module_defs = cl.helper_defs_of(tf)
        conftest_helpers = cl.conftest_chain_helpers(tf.parent, tests_dir, conftest_cache)
        helper_defs = {**conftest_helpers, **module_defs}
        for name, node in module_defs.items():
            if name.startswith("test_"):
                all_called |= cl.symbols_of_function(node, helper_defs)
    placeholder_no_test = sorted(set(shared["old_placeholder_symbols"]) - all_called)

    return {
        "epic": epic,
        "module_file": shared["module_file"],
        "rules_file": shared["rules_file"],
        "bible_file": bible_file_rel,
        "stories": stories,
        "missing_numbering": missing_numbering,
        "placeholder_no_test": placeholder_no_test,
        "shared": shared,
    }


def cross_epic_overlap(results: dict[str, dict]) -> dict[str, list[str]]:
    """symbol -> sorted list of epics whose regenerated cards both claim it."""
    owner: dict[str, set[str]] = {}
    for epic, result in results.items():
        for story in result["stories"]:
            for card in story["cards"]:
                for sym in card["symbols"]:
                    owner.setdefault(sym, set()).add(epic)
    return {sym: sorted(epics) for sym, epics in owner.items() if len(epics) > 1}


# ---- rendering: report.md and card files ----

def render_report(result: dict, cross_epic: dict[str, list[str]]) -> str:
    epic = result["epic"]
    lines = [f"# Card regen report -- {epic}", ""]
    lines.append(
        f"Module: `{result['module_file']}`. Rules file: `{result['rules_file']}`. "
        f"Bible: `{result['bible_file']}`."
    )
    lines.append("")
    if result["shared"]["old_placeholder_symbols"]:
        lines.append(
            "Old placeholder symbol(s) this epic's existing queue cards name: "
            f"`{', '.join(result['shared']['old_placeholder_symbols'])}`."
        )
        lines.append("")

    total_cards = sum(len(s["cards"]) for s in result["stories"])
    total_symbols = len({sym for s in result["stories"] for c in s["cards"] for sym in c["symbols"]})
    total_tests = sum(len(t) for s in result["stories"] for c in s["cards"] for t in [c["tests"]])
    lines.append(f"Cards generated: {total_cards}. Distinct symbols carded: {total_symbols}. "
                 f"Tests assigned to a card: {total_tests}.")
    lines.append("")

    lines.append("## Numbering prefixes (per story, reused from the old queue)")
    for s in result["stories"]:
        if s["cards"]:
            prefix_example = s["cards"][0]["card_id"]
        else:
            prefix_example = "(none -- already satisfiable)"
        lines.append(f"- {s['story_id']}: {prefix_example}")
    lines.append("")

    lines.append("## Cards generated")
    for s in result["stories"]:
        lines.append(f"### {s['story_id']}")
        if not s["cards"]:
            lines.append("(no card -- every test already satisfiable with built symbols)")
        for c in s["cards"]:
            lines.append(f"- `{c['card_id']}`: symbols=[{', '.join(c['symbols'])}] "
                         f"tests=[{', '.join(c['tests'])}]")
        lines.append("")

    lines.append("## Tests with no unbuilt symbol (already satisfiable)")
    any_sat = False
    for s in result["stories"]:
        if s["already_satisfiable"]:
            any_sat = True
            lines.append(f"- {s['story_id']}: {', '.join(s['already_satisfiable'])}")
    if not any_sat:
        lines.append("none")
    lines.append("")

    lines.append("## Symbols with no test (skipped)")
    if result["placeholder_no_test"]:
        lines.append(
            "Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): "
            f"{', '.join(result['placeholder_no_test'])}. Not carried into the regenerated cards."
        )
    else:
        lines.append("none")
    fallback_syms = sorted({sym for s in result["stories"] for sym in s["no_test_order_fallback"]})
    if fallback_syms:
        lines.append(
            "Order-fallback (unbuilt symbol found by the set-walk but not by the "
            f"position-walk -- should not happen; investigate): {', '.join(fallback_syms)}"
        )
    lines.append("")

    lines.append("## Stories needing more than 6 cards (design-lane question, not decided)")
    oversized = [s for s in result["stories"] if s["oversized"]]
    if oversized:
        for s in oversized:
            lines.append(f"- {s['story_id']}: {len(s['cards'])} cards")
    else:
        lines.append("none")
    lines.append("")

    lines.append(
        "## Cards with no acceptance test of their own (design-lane question, not decided)"
    )
    lines.append(
        "A card can end up with symbols but zero tests when every test needing "
        "them also needs a later card's symbols (the test's own closure is "
        "wider than the 5-symbol cap covers in one card). Candidates: (a) "
        "merge such a card forward into the next one, exceeding the cap only "
        "for this story (needs approval -- sizing caps are fixed); (b) accept "
        "the card as a pure prerequisite with no acceptance of its own (needs "
        "a card-format change -- card_lint.py currently hard-errors on empty "
        "acceptance); (c) leave it as a real card_lint finding and re-cut the "
        "test itself so its assertions split the same way the symbols do."
    )
    no_accept = [(s["story_id"], c["card_id"]) for s in result["stories"] for c in s["cards"] if not c["tests"]]
    if no_accept:
        for story_id, card_id in no_accept:
            lines.append(f"- {story_id}: `{card_id}`")
    else:
        lines.append("none")
    lines.append("")

    if result["missing_numbering"]:
        lines.append("## Stories with a test file but no existing queue card to learn a prefix from")
        lines.append(", ".join(result["missing_numbering"]))
        lines.append("")

    missing_rules = sorted({rid for s in result["stories"] for rid in s["missing_rule_ids"]})
    if missing_rules:
        lines.append("## Rule ids named by a test but not found in the bible epic file")
        lines.append(", ".join(missing_rules))
        lines.append("")

    lines.append("## Cross-epic symbol ownership")
    this_epic_overlap = {sym: epics for sym, epics in cross_epic.items() if epic in epics}
    if this_epic_overlap:
        for sym, epics in sorted(this_epic_overlap.items()):
            lines.append(f"- `{sym}`: {', '.join(epics)}")
    elif cross_epic:
        lines.append("none touching this epic")
    else:
        lines.append("not computed (single-epic invocation; run with sibling epics to compute)")
    lines.append("")

    return "\n".join(lines)


def render_cross_epic_md(cross_epic: dict[str, list[str]]) -> str:
    lines = ["# Cross-epic symbol ownership -- card_regen", ""]
    if not cross_epic:
        lines.append("none -- no symbol appears in more than one processed epic's regenerated cards")
    else:
        for sym, epics in sorted(cross_epic.items()):
            lines.append(f"- `{sym}`: {', '.join(epics)}")
    lines.append("")
    return "\n".join(lines)


def write_epic_output(result: dict, out_dir: Path, cross_epic: dict[str, list[str]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for s in result["stories"]:
        for c in s["cards"]:
            text = render_card(c, result["shared"], result["epic"], result["bible_file"], s["test_file"])
            (out_dir / f"{c['card_id']}.md").write_text(text)
    (out_dir / "report.md").write_text(render_report(result, cross_epic))


# ---- CLI ----

def print_text_summary(result: dict) -> None:
    epic = result["epic"]
    total_cards = sum(len(s["cards"]) for s in result["stories"])
    print(f"== {epic} ({result['module_file']}) ==")
    print(f"  cards: {total_cards}")
    for s in result["stories"]:
        ids = [c["card_id"] for c in s["cards"]]
        print(f"  {s['story_id']}: {', '.join(ids) or '(none, already satisfiable)'}")
    print()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("epics", nargs="+")
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ap.add_argument("--out", help="output root directory; writes <out>/<epic>/*.md + report.md")
    ap.add_argument("--report", action="store_true", help="print the listing only, write nothing")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    project = Path(args.project).expanduser()
    queue = Path(args.queue).expanduser()
    if not project.is_dir():
        print(f"project is not a directory: {project}", file=sys.stderr)
        return 2

    results: dict[str, dict] = {}
    for epic in args.epics:
        try:
            results[cl._normalize_epic(epic) or epic] = regen_epic(epic, project, queue)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    cross_epic = cross_epic_overlap(results) if len(results) > 1 else {}

    if args.json:
        print(json.dumps({"results": results, "cross_epic": cross_epic}, indent=2))
    else:
        for result in results.values():
            print_text_summary(result)

    if args.report:
        return 0

    if args.out:
        out_root = Path(args.out).expanduser()
        for epic, result in results.items():
            write_epic_output(result, out_root / epic, cross_epic)
        if len(results) > 1:
            (out_root / "cross_epic.md").write_text(render_cross_epic_md(cross_epic))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
