"""PX-14: parent-patch fence (DECISIONS.md R7j/R7k/R7l). A hand patch (a
"parent patch", written by the session that owns csrc/, not a model
candidate) obeys the same ownership rule a card does: it may touch only the
function its diagnosis names, and never do another card's job.

The incident this answers: `a493cfd` ("fix(csrc): om_step_telegraphs
implemented the wrong damage formula", card 204a1's `snippet_symbol`) also
added conquest detection, garrison, and ownership transfer inside
`om_step_telegraphs` -- entirely 204b1's job (`om_step_resolve`), per its own
card title and acceptance list. The subtlety this module exists to prove:
a function-ownership check ALONE would have accepted `a493cfd`, because the
only function its diff touches (`om_step_telegraphs`) genuinely is 204a1's
own `snippet_symbol`. What makes it a violation is invisible to a
line-range-to-function-name check: the patch did another card's job *inside*
the function it legitimately owns. Two checks, run together:

1. check_function_ownership(): every function a diff's hunks overlap (by
   post-patch line range, via card_lint.py's own brace matcher -- not git's
   funcname heuristic, though that heuristic was confirmed to agree with it
   on all three real replay commits during development) must be in the
   named card's own `snippet_symbol`, or must belong to no other card. Any
   function claimed by ANOTHER card's `snippet_symbol` is a violation.
   Catches a patch that edits `om_step_resolve` under 204a1's name -- but
   would NOT, alone, catch `a493cfd` (see above).
2. check_scope_capture(): every OTHER queued-or-parked card's acceptance
   tests (their `checks`, i.e. the pytest node ids in their frontmatter
   `acceptance:` list) are run once before the patch and once after, in the
   same worktree, as a single combined pytest invocation each side (not one
   subprocess per card -- there can be dozens of cards). Any test that goes
   red-before/green-after is attributed back to whichever card's acceptance
   list names it. That is scope capture: the patch made another card's job
   done. Catches `a493cfd`.

Fence accepts iff both checks pass.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from green_check import parse_card  # noqa: E402  (frontmatter parser)
from card_lint import all_defined_symbols, card_id_of, find_function_span, _split_list  # noqa: E402
from suite_regression import DEFAULT_PYTHON, RunResult, apply_diff, run_pytest  # noqa: E402

DEFAULT_QUEUE = Path("/home/westopoli/Projects/agora/queue")
# Agora's queue is shared across projects (agora itself, agora-proving-ground,
# ouroboros-manifold, switchboard, the-best-salesmen all have cards mixed
# together under the same queue/ and queue/parked/ directories -- confirmed
# empirically: an unfiltered scope-capture run picked up a the-best-salesmen
# card whose acceptance command named a Supabase test file that does not
# exist in this repo, which made pytest abort the whole combined invocation
# with "file or directory not found" and silently report 0 passed/0 failed
# instead of erroring loudly). Card scope must be filtered to this project.
DEFAULT_PROJECT = "/home/westopoli/Projects/ouroboros-manifold"

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.M)
_DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.M)
_NODE_ID_RE = re.compile(r"tests/\S+\.py(?:::\S+)?")


# ---- diff -> touched functions (post-patch line ranges, card_lint's own brace matcher) --

@dataclass
class Hunk:
    file: str
    new_start: int
    new_count: int


def parse_diff_hunks(diff_text: str) -> list[Hunk]:
    """One Hunk per @@ block, attributed to the nearest preceding
    '+++ b/<path>' line. A '/dev/null' target (pure file deletion) is
    skipped -- out of scope for a function-ownership check."""
    hunks: list[Hunk] = []
    current_file: str | None = None
    for line in diff_text.splitlines():
        m = _DIFF_FILE_RE.match(line)
        if m:
            current_file = None if m.group(1) == "/dev/null" else m.group(1)
            continue
        m = _HUNK_RE.match(line)
        if m and current_file:
            new_start = int(m.group(1))
            new_count = int(m.group(2)) if m.group(2) is not None else 1
            hunks.append(Hunk(file=current_file, new_start=new_start, new_count=max(new_count, 1)))
    return hunks


def functions_in_file(text: str) -> list[tuple[str, int, int]]:
    """(name, start_line, end_line), 1-indexed inclusive, for every
    top-level function definition card_lint.py's own brace matcher finds."""
    out = []
    for name in all_defined_symbols(text):
        span = find_function_span(text, name)
        if span is None:
            continue
        start_line = text.count("\n", 0, span[0]) + 1
        end_line = text.count("\n", 0, span[1]) + 1
        out.append((name, start_line, end_line))
    return out


def touched_functions(worktree: Path, diff_text: str) -> dict[str, set[str]]:
    """file -> set of function names whose brace-matched span overlaps any
    hunk's new-side line range. Reads the POST-patch file, so `diff_text`
    must already be applied in `worktree`. A hunk that falls between
    functions at file scope (an #include, say) touches no function -- a
    real, reportable case, not a scan defect."""
    hunks = parse_diff_hunks(diff_text)
    by_file: dict[str, list[Hunk]] = {}
    for h in hunks:
        by_file.setdefault(h.file, []).append(h)
    result: dict[str, set[str]] = {}
    for file_rel, file_hunks in by_file.items():
        path = worktree / file_rel
        if not path.exists():
            continue
        funcs = functions_in_file(path.read_text())
        touched: set[str] = set()
        for h in file_hunks:
            lo, hi = h.new_start, h.new_start + h.new_count - 1
            for name, start, end in funcs:
                if start <= hi and end >= lo:
                    touched.add(name)
        result[file_rel] = touched
    return result


# ---- card/queue loading (queue + parked, every suffix: .md, .md.hold, .md.retired, ...) --

@dataclass
class CardInfo:
    card_id: str
    path: Path
    project: str
    snippet_file: str
    symbols: set[str]
    acceptance: list[str]


def _iter_card_files(queue: Path):
    if not queue.is_dir():
        return
    for p in sorted(queue.glob("*.md*")):
        if p.is_file():
            yield p
    parked = queue / "parked"
    if parked.is_dir():
        for p in sorted(parked.glob("*.md*")):
            if p.is_file():
                yield p


def load_cards(queue: Path, *, project: str | None = DEFAULT_PROJECT) -> list[CardInfo]:
    """`project`, when given, filters to cards whose frontmatter `project:`
    field matches exactly -- the queue is shared across several unrelated
    projects (see DEFAULT_PROJECT's comment); pass None to disable the
    filter and load every card the queue directory contains."""
    cards = []
    for p in _iter_card_files(queue):
        try:
            raw = parse_card(p)
        except Exception:
            continue
        card_project = raw.get("project", "") if isinstance(raw.get("project"), str) else ""
        if project is not None and card_project != project:
            continue
        acceptance = raw.get("acceptance", [])
        if isinstance(acceptance, str):
            acceptance = [acceptance]
        cards.append(CardInfo(
            card_id=card_id_of(p),
            path=p,
            project=card_project,
            snippet_file=raw.get("snippet_file", "") if isinstance(raw.get("snippet_file"), str) else "",
            symbols=set(_split_list(raw.get("snippet_symbol", ""))),
            acceptance=list(acceptance),
        ))
    return cards


def _owning_card(cards: list[CardInfo], symbol: str, exclude_card_id: str) -> str | None:
    for c in cards:
        if c.card_id == exclude_card_id:
            continue
        if symbol in c.symbols:
            return c.card_id
    return None


# ---- check 1: function ownership --

@dataclass
class OwnershipFinding:
    function: str
    file: str
    status: str  # "own" | "unowned" | "violation"
    owning_card: str | None = None


def check_function_ownership(cards: list[CardInfo], this_card: CardInfo,
                              touched: dict[str, set[str]]) -> list[OwnershipFinding]:
    findings: list[OwnershipFinding] = []
    for file_rel, funcs in touched.items():
        for fn in sorted(funcs):
            if fn in this_card.symbols:
                findings.append(OwnershipFinding(function=fn, file=file_rel, status="own"))
                continue
            owner = _owning_card(cards, fn, this_card.card_id)
            if owner:
                findings.append(OwnershipFinding(function=fn, file=file_rel, status="violation", owning_card=owner))
            else:
                findings.append(OwnershipFinding(function=fn, file=file_rel, status="unowned"))
    return findings


# ---- check 2: scope capture --

def _node_ids(acceptance: list[str]) -> list[str]:
    ids: list[str] = []
    for cmd in acceptance:
        ids.extend(m.group(0) for m in _NODE_ID_RE.finditer(cmd))
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _other_card_node_ids(cards: list[CardInfo], exclude_card_id: str) -> tuple[list[str], dict[str, list[str]]]:
    """(sorted union of node ids, node id -> owning card ids)."""
    id_owners: dict[str, list[str]] = {}
    for c in cards:
        if c.card_id == exclude_card_id:
            continue
        for nid in _node_ids(c.acceptance):
            id_owners.setdefault(nid, []).append(c.card_id)
    return sorted(id_owners), id_owners


@dataclass
class ScopeCaptureReport:
    tests_run: int
    cards_covered: int
    before: RunResult | None = field(default=None, repr=False)
    after: RunResult | None = field(default=None, repr=False)
    went_green: list[str] = field(default_factory=list)
    captured_cards: dict[str, list[str]] = field(default_factory=dict)
    accept: bool = True


def check_scope_capture(worktree: Path, cards: list[CardInfo], this_card_id: str,
                         *, before: RunResult | None, after: RunResult | None,
                         ids: list[str], id_owners: dict[str, list[str]]) -> ScopeCaptureReport:
    if not ids or before is None or after is None:
        return ScopeCaptureReport(tests_run=0, cards_covered=0)
    went_green = sorted(set(before.failing_ids) - set(after.failing_ids))
    captured: dict[str, list[str]] = {}
    for nid in went_green:
        for owner in id_owners.get(nid, []):
            captured.setdefault(owner, []).append(nid)
    cards_covered = len({c for owners in id_owners.values() for c in owners})
    return ScopeCaptureReport(tests_run=len(ids), cards_covered=cards_covered, before=before, after=after,
                               went_green=went_green, captured_cards=captured, accept=not went_green)


def _require_clean_pytest_run(result: RunResult | None, label: str, ids: list[str]) -> None:
    """pytest given a node id it can't collect (a file that doesn't exist,
    for instance) aborts the WHOLE invocation with a nonzero, non-1
    returncode and prints nothing pytest_pytest's own FAILED/ERROR lines --
    parse_pytest then silently reports 0 passed/0 failed, indistinguishable
    from a genuinely clean run. Found empirically on the real replay: a
    the-best-salesmen card's acceptance command leaked into an unfiltered
    scope-capture run and produced exactly this false "0 failed" (returncode
    4, "file or directory not found"). 0=all ids passed, 1=some failed; any
    other code is a hard error this tool refuses to interpret as green."""
    if result is None:
        return
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"scope-capture {label} run did not collect cleanly (returncode={result.returncode}, "
            f"{len(ids)} node ids); refusing to trust a 0-failed result. stderr tail: "
            f"{result.stderr[-500:]!r}"
        )


# ---- orchestration --

@dataclass
class FenceReport:
    card_id: str
    ownership: list[OwnershipFinding]
    ownership_pass: bool
    scope: ScopeCaptureReport
    accept: bool


def run_fence(card_id: str, diff_text: str, queue: Path, worktree: Path,
              python_exe: str = DEFAULT_PYTHON, timeout: int = 600,
              project: str | None = DEFAULT_PROJECT) -> FenceReport:
    cards = load_cards(queue, project=project)
    this_card = next((c for c in cards if c.card_id == card_id), None)
    if this_card is None:
        raise ValueError(f"card {card_id!r} not found under {queue} (or its parked/ subdir)")

    ids, id_owners = _other_card_node_ids(cards, card_id)
    before = run_pytest(worktree, python_exe, test_args=ids, timeout=timeout) if ids else None
    _require_clean_pytest_run(before, "before", ids)

    apply_diff(worktree, diff_text)

    touched = touched_functions(worktree, diff_text)
    ownership = check_function_ownership(cards, this_card, touched)
    ownership_pass = not any(f.status == "violation" for f in ownership)

    after = run_pytest(worktree, python_exe, test_args=ids, timeout=timeout) if ids else None
    _require_clean_pytest_run(after, "after", ids)
    scope = check_scope_capture(worktree, cards, card_id, before=before, after=after, ids=ids, id_owners=id_owners)

    return FenceReport(card_id=card_id, ownership=ownership, ownership_pass=ownership_pass,
                        scope=scope, accept=ownership_pass and scope.accept)


def _run_result_dict(r: RunResult | None) -> dict | None:
    if r is None:
        return None
    d = asdict(r)
    d.pop("stdout", None)
    d.pop("stderr", None)
    d["failing_ids"] = list(r.failing_ids)
    return d


def _report_dict(report: FenceReport) -> dict:
    d = asdict(report)
    d["scope"]["before"] = _run_result_dict(report.scope.before)
    d["scope"]["after"] = _run_result_dict(report.scope.after)
    return d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("card_id")
    ap.add_argument("diff_file")
    ap.add_argument("--queue", default=str(DEFAULT_QUEUE))
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--python", default=DEFAULT_PYTHON)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--project", default=DEFAULT_PROJECT,
                     help="filter queue cards to this project (default: ouroboros-manifold); "
                          "pass an empty string to disable the filter")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    diff_text = Path(args.diff_file).read_text()
    project = args.project or None
    report = run_fence(args.card_id, diff_text, Path(args.queue), Path(args.worktree),
                        python_exe=args.python, timeout=args.timeout, project=project)

    if args.json:
        print(json.dumps(_report_dict(report), indent=2))
    else:
        if report.accept:
            print(f"OK: {args.card_id} -- {len(report.ownership)} function(s) touched, all owned "
                  f"or unclaimed; scope capture clean ({report.scope.tests_run} other-card tests, "
                  f"{report.scope.cards_covered} cards checked).")
        else:
            print(f"VIOLATION: {args.card_id}")
            for f in report.ownership:
                if f.status == "violation":
                    print(f"  function ownership: {f.function} ({f.file}) belongs to {f.owning_card}")
                elif f.status == "unowned":
                    print(f"  function ownership: {f.function} ({f.file}) has no owning card")
            for card, tests in report.scope.captured_cards.items():
                print(f"  scope capture: {card}'s tests went red-before/green-after: {', '.join(tests)}")
    return 0 if report.accept else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
