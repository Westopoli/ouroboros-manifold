"""PX-7: whole-suite regression gate after DONE (DECISIONS.md's unanswered
half of C7, "Regression found, needs a decision"). Card 203b1's accepted
candidate rewrote om_faction_candidates in csrc/agent.c; Agora's harness at
the time ran only the current card's checks[0], so nothing caught the
regression before merge. Agora's regression gate today (build.py:514-556
predecessor_checks, :955-999 finalize_pass, the Q1 decision) re-runs only the
acceptance tests of DONE predecessor cards that share the candidate's
snippet_file -- narrower than a full suite run (decision option (c) in
DECISIONS.md, never implemented). This module answers: given a worktree and a
candidate diff, which tests/csim tests newly fail (red-after,
green-before) over the WHOLE suite, and how does that compare to what the
predecessor-only rule would have caught over the same diff.

whole_suite_regression() is the claimed gate: full-suite before/after
diffing. predecessor_only_regression() mirrors build.py's real
predecessor_checks/finalize_pass mechanics (re-run a fixed list of tests
after the diff, accept iff none of them fail) without touching the agora
repo -- the caller supplies which tests those predecessor cards owned, since
recomputing "which cards were DONE at that historical instant" is a
replay-time judgment call documented in the PX-7 write-up, not something this
module infers on its own.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
DEFAULT_TEST_ARGS = ("tests/csim",)

_PASSED_RE = re.compile(r"(\d+) passed")
_FAILED_RE = re.compile(r"(\d+) failed")
_ERROR_RE = re.compile(r"(\d+) error")


def parse_pytest(stdout: str) -> tuple[int, int, tuple[str, ...]]:
    """Mirrors agora's own scripts/build.py:parse_pytest: (passed,
    failed+errors, failing/erroring ids), de-duplicated, in encounter order.
    Relies on pytest's default "short test summary info" FAILED/ERROR lines,
    which -q prints without any extra -r flag."""
    passed = int(m.group(1)) if (m := _PASSED_RE.search(stdout or "")) else 0
    failed = int(m.group(1)) if (m := _FAILED_RE.search(stdout or "")) else 0
    errors = int(m.group(1)) if (m := _ERROR_RE.search(stdout or "")) else 0
    ids, seen = [], set()
    for line in (stdout or "").splitlines():
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            rest = line.split(" ", 1)[1].split(" - ", 1)[0].strip()
            if rest not in seen:
                seen.add(rest)
                ids.append(rest)
    return passed, failed + errors, tuple(ids)


def parse_junit_extra(xml_path: Path) -> tuple[dict[str, str], int, int]:
    """(first_assertion, skipped_count, xfailed_count) from a pytest
    `--junitxml` report. `first_assertion` maps a failing/erroring node id
    (`file.py::test_name`, matching parse_pytest's own id shape) to the
    first line of its failure/error message -- the merge gate rejects a
    candidate where an id stays red on both sides of a diff but its first
    assertion line changed, which a bare failing-id-set diff would miss
    entirely (same id, different reason). `skipped_count` is every
    `<skipped>` testcase pytest did not mark as xfail; `xfailed_count` is
    every `<skipped type="pytest.xfail">` (pytest's own junit convention for
    an expected failure) -- an xpass (unexpectedly passing xfail) has no
    `<skipped>` child at all and is counted as passed, same as pytest's own
    short summary treats it."""
    first_assertion: dict[str, str] = {}
    skipped = 0
    xfailed = 0
    if not Path(xml_path).exists():
        return first_assertion, skipped, xfailed
    root = ET.parse(xml_path).getroot()
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        file_attr = tc.get("file")
        module = file_attr if file_attr else classname.replace(".", "/") + ".py"
        node_id = f"{module}::{name}"
        failure = tc.find("failure")
        error = tc.find("error")
        skipped_el = tc.find("skipped")
        if failure is not None or error is not None:
            el = failure if failure is not None else error
            text = (el.get("message") or "") or (el.text or "")
            first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
            first_assertion[node_id] = first_line
        elif skipped_el is not None:
            if skipped_el.get("type") == "pytest.xfail":
                xfailed += 1
            elif is_scale_gated(node_id, skipped_el):
                pass  # counted by parse_junit_scale_gated, on its own line
            else:
                skipped += 1
    return first_assertion, skipped, xfailed


def is_scale_gated(node_id: str, skipped_el) -> bool:
    """A skip under tests/csim/scale/ whose reason names OM_SCALE (A98), or under
    tests/skilllab/ whose reason names OM_LAB_SLOW (the lab's SLOW tier)."""
    reason = (skipped_el.get("message") or "") + (skipped_el.text or "")
    if node_id.startswith("tests/csim/scale/") and "OM_SCALE" in reason:
        return True
    # See also: pieces.toml HARNESS-lab-slow-tier; skill-lab rev 2 spec ruling 13 (SLOW marker).
    # The trailing slash keeps prefixes such as tests/skilllabx/ out.
    return node_id.startswith("tests/skilllab/") and "OM_LAB_SLOW" in reason


def parse_junit_scale_gated(xml_path: Path) -> tuple[str, ...]:
    """Sorted node ids of the scale-gated skips (is_scale_gated) in a junit report."""
    if not Path(xml_path).exists():
        return ()
    ids = []
    for tc in ET.parse(xml_path).getroot().iter("testcase"):
        skipped_el = tc.find("skipped")
        if skipped_el is None or skipped_el.get("type") == "pytest.xfail":
            continue
        module = tc.get("file") or tc.get("classname", "").replace(".", "/") + ".py"
        node_id = f"{module}::{tc.get('name', '')}"
        if is_scale_gated(node_id, skipped_el):
            ids.append(node_id)
    return tuple(sorted(ids))


@dataclass
class RunResult:
    passed: int
    failed: int
    failing_ids: tuple[str, ...]
    wall_s: float
    returncode: int
    stdout: str = field(repr=False, default="")
    stderr: str = field(repr=False, default="")
    first_assertion: dict[str, str] = field(default_factory=dict)
    skipped: int = 0
    xfailed: int = 0
    scale_gated: tuple[str, ...] = ()


def run_pytest(cwd: Path, python_exe: str = DEFAULT_PYTHON, test_args=DEFAULT_TEST_ARGS,
                timeout: int = 600, extra_args: list[str] | None = None,
                junit_path: Path | None = None) -> RunResult:
    """`junit_path`, when given, also captures --junitxml there and populates
    first_assertion/skipped/xfailed from it (parse_junit_extra); omitted,
    behaviour is unchanged from before this capability existed (all three
    default empty/zero)."""
    argv = [python_exe, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            *(extra_args or []), *test_args]
    if junit_path is not None:
        argv.append(f"--junitxml={junit_path}")
    t0 = time.time()
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    wall = time.time() - t0
    passed, failed, ids = parse_pytest(r.stdout)
    first_assertion, skipped, xfailed = ({}, 0, 0) if junit_path is None else parse_junit_extra(junit_path)
    return RunResult(passed=passed, failed=failed, failing_ids=ids, wall_s=round(wall, 2),
                      returncode=r.returncode, stdout=r.stdout, stderr=r.stderr,
                      first_assertion=first_assertion, skipped=skipped, xfailed=xfailed,
                      scale_gated=() if junit_path is None else parse_junit_scale_gated(junit_path))


def apply_diff(cwd: Path, diff_text: str) -> None:
    r = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=str(cwd),
                        input=diff_text, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git apply failed (rc={r.returncode}): {r.stderr}")


@dataclass
class RegressionReport:
    before: RunResult
    after: RunResult
    new_failures: list[str]
    changed_assertions: list[str] = field(default_factory=list)
    skipped_increase: int = 0
    xfailed_increase: int = 0
    accept: bool = True

    def __post_init__(self):
        # Recomputed here (not trusted from the caller) so every construction
        # path -- whole_suite_regression, compare_runs, a hand-built report in
        # a test -- agrees on what "accept" means for the same before/after.
        self.accept = (
            not self.new_failures
            and not self.changed_assertions
            and self.skipped_increase <= 0
            and self.xfailed_increase <= 0
        )


def compare_runs(before: RunResult, after: RunResult) -> RegressionReport:
    """The comparison half of the gate, decoupled from how `before`/`after`
    were produced -- `whole_suite_regression` builds them via diff-apply in
    one worktree; the merge gate (two already-built trees: a base-ref
    worktree and the candidate) builds them by running `run_pytest` once per
    tree and calls this directly. new_failures is red-after/green-before, as
    before; changed_assertions is every id red on BOTH sides whose first
    assertion line differs (same id, different reason -- a failing-id-set
    diff alone would call that a non-event). Both `first_assertion` maps are
    empty unless `run_pytest` was called with `junit_path`, in which case
    changed_assertions is always empty too (nothing to compare)."""
    new_failures = sorted(set(after.failing_ids) - set(before.failing_ids))
    still_red = set(after.failing_ids) & set(before.failing_ids)
    changed_assertions = sorted(
        nid for nid in still_red
        if before.first_assertion.get(nid) is not None
        and after.first_assertion.get(nid) is not None
        and before.first_assertion[nid] != after.first_assertion[nid]
    )
    return RegressionReport(
        before=before, after=after, new_failures=new_failures,
        changed_assertions=changed_assertions,
        skipped_increase=after.skipped - before.skipped,
        xfailed_increase=after.xfailed - before.xfailed,
    )


def whole_suite_regression(worktree: Path, diff_text: str, *, python_exe: str = DEFAULT_PYTHON,
                            test_args=DEFAULT_TEST_ARGS, timeout: int = 600,
                            junit: bool = False) -> RegressionReport:
    """The claimed gate. Records the failing-id set of `test_args` (default
    tests/csim) before the diff, applies it, records after, and reports new
    failures = ids failing after that were NOT failing before (red-after,
    green-before -- a test already red before the diff is never counted as a
    new failure, even if it stays red after). Rejects (accept=False) on any
    new failure, or (when `junit=True`) a changed first-assertion line on an
    id red both sides, or a rise in skipped/xfailed count. The diff is
    applied in place; `worktree` is expected to already be checked out at
    the diff's base commit."""
    worktree = Path(worktree)
    with tempfile.TemporaryDirectory(prefix="suite_regression_junit_") as tmp:
        before_xml = Path(tmp) / "before.xml" if junit else None
        after_xml = Path(tmp) / "after.xml" if junit else None
        before = run_pytest(worktree, python_exe, test_args, timeout, junit_path=before_xml)
        apply_diff(worktree, diff_text)
        after = run_pytest(worktree, python_exe, test_args, timeout, junit_path=after_xml)
    return compare_runs(before, after)


@dataclass
class PredecessorOnlyReport:
    predecessor_tests: list[str]
    result: RunResult
    accept: bool


def predecessor_only_regression(worktree: Path, diff_text: str, predecessor_tests: list[str], *,
                                 python_exe: str = DEFAULT_PYTHON, timeout: int = 600,
                                 apply_first: bool = True) -> PredecessorOnlyReport:
    """Mirrors Agora's real gate (build.py:514-556 predecessor_checks +
    :955-999 finalize_pass): after a candidate diff is applied, only the
    acceptance tests of DONE predecessor cards sharing the candidate's
    snippet_file are re-run; accept=False iff any of THOSE tests now fail.
    Does not look at the rest of the suite at all -- that gap is what this
    probe measures against whole_suite_regression() on the same diff.
    `predecessor_tests` is supplied by the caller (see module docstring)."""
    worktree = Path(worktree)
    if apply_first:
        apply_diff(worktree, diff_text)
    result = run_pytest(worktree, python_exe, list(predecessor_tests), timeout)
    return PredecessorOnlyReport(predecessor_tests=list(predecessor_tests), result=result,
                                  accept=result.failed == 0)


def _run_result_to_dict(r: RunResult) -> dict:
    d = asdict(r)
    d.pop("stdout", None)
    d.pop("stderr", None)
    d["failing_ids"] = list(r.failing_ids)
    d["scale_gated"] = list(r.scale_gated)
    return d


def _report_to_dict(r) -> dict:
    d = asdict(r)
    for k in ("before", "after", "result"):
        if k in d and isinstance(d[k], dict):
            d[k].pop("stdout", None)
            d[k].pop("stderr", None)
    return d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("worktree")
    ap.add_argument("diff_file")
    ap.add_argument("--python", default=DEFAULT_PYTHON)
    ap.add_argument("--test-args", nargs="*", default=list(DEFAULT_TEST_ARGS))
    ap.add_argument("--predecessor-tests", nargs="*", default=None,
                     help="if given, also runs predecessor_only_regression over the same diff")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--junit", action="store_true",
                     help="also capture --junitxml before/after to catch a changed first "
                          "assertion line or a skipped/xfailed rise on an id red both sides")
    args = ap.parse_args(argv)

    diff_text = Path(args.diff_file).read_text()
    report = whole_suite_regression(Path(args.worktree), diff_text, python_exe=args.python,
                                     test_args=args.test_args, timeout=args.timeout,
                                     junit=args.junit)
    out = {"whole_suite": _report_to_dict(report)}

    pred = None
    if args.predecessor_tests:
        pred = predecessor_only_regression(Path(args.worktree), diff_text, args.predecessor_tests,
                                            python_exe=args.python, timeout=args.timeout,
                                            apply_first=False)
        out["predecessor_only"] = _report_to_dict(pred)

    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"whole-suite: before {report.before.passed}p/{report.before.failed}f "
              f"({report.before.wall_s}s) -> after {report.after.passed}p/{report.after.failed}f "
              f"({report.after.wall_s}s); new failures: {report.new_failures or 'none'}; "
              f"changed assertions: {report.changed_assertions or 'none'}; "
              f"skipped_increase={report.skipped_increase} xfailed_increase={report.xfailed_increase}; "
              f"accept={report.accept}")
        if pred is not None:
            print(f"predecessor-only: {pred.result.failed} failed of "
                  f"{len(pred.predecessor_tests)} tests ({pred.result.wall_s}s); "
                  f"accept={pred.accept}")
    return 0 if report.accept else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
