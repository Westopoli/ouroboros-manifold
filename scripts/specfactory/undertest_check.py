#!/usr/bin/env python3
"""PX-06 prototype experiment: two Factory gates from docs/northstar/PLAN.md's
"Gates the worker cannot move" section.

(a) shadow_fixture -- a candidate that hard-codes a fixture's expected answer
    must fail once that fixture's literal is perturbed; a candidate that
    genuinely computes the answer must keep passing (with the expected value
    recomputed, when the test's own docstring states the formula).

(b) mutate_diff -- mutating only the lines a candidate changed (comparison
    flips, +/-, */÷, numeric literal replacement, if-negation) must make at
    least one acceptance test fail. If every mutant of a changed line
    survives the whole acceptance suite, that line was never actually
    constrained by any test and the card is UNDER_TESTED.

Both are read-only with respect to the real repo: all builds and test runs
happen in scratch directories materialized with `git archive`, never in the
project's own working tree or in a `git worktree`.

Real incident this replays: card 204a1's merged `om_step_telegraphs`
(ouroboros commit 0d65f9e) passed its single acceptance test
(test_R_036_03_it_resolves_in_step_3c, which only asserts effective_attack)
while getting five formulas wrong -- see docs/northstar/research/
harness_defects_2026-09-17/DECISIONS.md, R7g. The fix is a493cfd. The
R-037 tests (tests/csim/test_E05_S037_battles_have_a_shape.py) are the
tests that would have caught it, had they been in the acceptance set.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card_lint import find_function_span  # noqa: E402


def python_bin() -> str:
    agora_python = Path("/home/westopoli/Projects/agora/.venv/bin/python")
    if agora_python.exists():
        return str(agora_python)
    venv_python = REPO / ".venv" / "bin" / "python3"
    return str(venv_python) if venv_python.exists() else sys.executable


# ---------------------------------------------------------------------------
# Scratch trees
# ---------------------------------------------------------------------------

def _archive_tree(project: Path, sha: str, dest: Path) -> None:
    """Materializes `project`'s tree at `sha` into `dest` via `git archive`
    (never `git worktree`, never the project's own working tree)."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(project), "archive", sha],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise RuntimeError(f"git archive {sha} failed: {archive.stderr.decode(errors='replace')}")
    tar = subprocess.run(
        ["tar", "-x", "-C", str(dest)],
        input=archive.stdout,
        capture_output=True,
    )
    if tar.returncode != 0:
        raise RuntimeError(f"tar extract of {sha} into {dest} failed: {tar.stderr.decode(errors='replace')}")


def _make(tree: Path, target: str = "libouroboros.so") -> tuple[bool, str, float]:
    start = time.monotonic()
    proc = subprocess.run(
        ["make", "-s", target], cwd=str(tree), capture_output=True, text=True, timeout=180,
    )
    seconds = time.monotonic() - start
    return proc.returncode == 0, proc.stdout + proc.stderr, seconds


def _clear_pycache(tree: Path) -> None:
    """Removes every __pycache__ under `tree`. Needed between two pytest runs
    of a test file whose source we rewrote in place: CPython's .pyc cache is
    keyed on (size, mtime), and a perturbed literal of the same character
    length written within the same mtime second is indistinguishable from
    the original to that cache, so the stale bytecode -- and its stale
    assertion -- gets silently reused otherwise."""
    for d in tree.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def _run_pytest(tree: Path, node_ids: list[str]) -> tuple[dict[str, bool], str, float]:
    """Runs pytest once per node id (a node id that fails to collect must not
    take any other node id down with it -- see baseline-skip handling in
    mutate_diff). Returns {node_id: passed} (missing/errored counts as
    not-passed), the combined output, and total wall time."""
    if not node_ids:
        return {}, "", 0.0
    results: dict[str, bool] = {}
    outputs = []
    total_seconds = 0.0
    for nid in node_ids:
        start = time.monotonic()
        proc = subprocess.run(
            [python_bin(), "-m", "pytest", "-v", "--no-header", "-p", "no:cacheprovider", nid],
            cwd=str(tree), capture_output=True, text=True, timeout=180,
        )
        total_seconds += time.monotonic() - start
        output = proc.stdout + proc.stderr
        outputs.append(output)
        passed = False
        for line in output.splitlines():
            m = re.match(r"^(\S+)\s+(PASSED|FAILED|ERROR)\b", line)
            if m and m.group(1) == nid:
                passed = m.group(2) == "PASSED"
        results[nid] = passed
    return results, "\n".join(outputs), total_seconds


# ---------------------------------------------------------------------------
# (a) shadow_fixture
# ---------------------------------------------------------------------------

def shadow_fixture(test_file: str, node_id: str, perturbation: dict,
                    *, project: Path = REPO, sha: str | None = None) -> dict:
    """Runs `node_id` (from `test_file`, relative to `project`) twice: once
    unmodified, once with `perturbation` applied to its source text.

    perturbation:
      {"find": <exact substring, must occur exactly once>,
       "replace": <replacement text>,
       "recompute": [(find, replace), ...]}   # optional

    Rule (kept simple, stated here): perturbation["find"]/["replace"] changes
    one input literal (e.g. an economy value passed to set_region). If the
    test's own docstring states the formula it checks, the caller supplies
    "recompute" pairs that also rewrite the expected literal(s) to the
    formula's new answer -- a genuine candidate must then still pass. If no
    "recompute" is given, the check instead requires the test's PASS/FAIL
    outcome to differ between the unmodified and perturbed run: an
    unperturbed-vs-perturbed outcome that does NOT change means the
    candidate's answer did not depend on the literal we changed, which is
    exactly the hard-coded-fixture shape this check exists to catch.

    Returns {"baseline_pass", "perturbed_pass", "verdict", "baseline_output",
    "perturbed_output"}. verdict is one of "OK" (genuine: passes both, or a
    detected outcome change), "HARDCODE_SUSPECTED" (outcome did not change
    with no recompute given), or "INCONCLUSIVE" (baseline itself did not
    pass, so nothing about the perturbation can be concluded).
    """
    scratch = Path(tempfile.mkdtemp(prefix="shadow_fixture_"))
    try:
        tree = scratch / "tree"
        _archive_tree(project, sha or "HEAD", tree)
        ok, out, _ = _make(tree)
        if not ok:
            raise RuntimeError(f"build failed for shadow_fixture at {sha or 'HEAD'}:\n{out}")

        test_path = tree / test_file
        original_source = test_path.read_text()

        _clear_pycache(tree)
        baseline_results, baseline_output, _ = _run_pytest(tree, [node_id])
        baseline_pass = baseline_results.get(node_id, False)

        find = perturbation["find"]
        replace = perturbation["replace"]
        if original_source.count(find) != 1:
            raise ValueError(
                f"perturbation[find]={find!r} must occur exactly once in {test_file}, "
                f"found {original_source.count(find)}"
            )
        perturbed_source = original_source.replace(find, replace)
        for rfind, rreplace in perturbation.get("recompute", []):
            # Every occurrence is rewritten (unlike `find`/`replace` above,
            # which targets one specific input literal): a docstring formula
            # and its own assertions typically repeat the same old answer
            # more than once, and all of them must move to the new answer.
            if perturbed_source.count(rfind) < 1:
                raise ValueError(f"recompute find={rfind!r} not found")
            perturbed_source = perturbed_source.replace(rfind, rreplace)

        test_path.write_text(perturbed_source)
        _clear_pycache(tree)
        perturbed_results, perturbed_output, _ = _run_pytest(tree, [node_id])
        perturbed_pass = perturbed_results.get(node_id, False)

        if not baseline_pass:
            verdict = "INCONCLUSIVE"
        elif perturbation.get("recompute"):
            verdict = "OK" if perturbed_pass else "FAIL"
        else:
            verdict = "OK" if perturbed_pass != baseline_pass else "HARDCODE_SUSPECTED"

        return {
            "baseline_pass": baseline_pass,
            "perturbed_pass": perturbed_pass,
            "verdict": verdict,
            "baseline_output": baseline_output,
            "perturbed_output": perturbed_output,
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------
# (b) mutate_diff
# ---------------------------------------------------------------------------

_COMPARISON_FLIPS = {"<=": "<", "<": "<=", ">=": ">", ">": ">=", "==": "!=", "!=": "=="}
_COMPARISON_RE = re.compile(r"<=|>=|==|!=|<|(?<!-)>")
_ARITH_FLIPS = {"+": "-", "-": "+", "*": "/", "/": "*"}
_ARITH_RE = re.compile(r"(?<![+\-*/=])\s([+\-*/])\s(?![+\-*/=])")
_NUMBER_RE = re.compile(r"\b\d+\.\d+\b|\b\d+\b")
_IF_RE = re.compile(r"\bif\s*\((.*)\)(\s*\{?\s*)$")


def _line_mutants(line: str) -> list[tuple[str, str]]:
    """[(label, mutated_line), ...] for one source line, per the operator
    catalog: comparison flips, +/-, */÷, numeric literal -> 0/1, if-negate."""
    out: list[tuple[str, str]] = []

    for m in _COMPARISON_RE.finditer(line):
        op = m.group(0)
        new_op = _COMPARISON_FLIPS[op]
        mutated = line[:m.start()] + new_op + line[m.end():]
        out.append((f"comparison {op}->{new_op} @col{m.start()}", mutated))

    for m in _ARITH_RE.finditer(line):
        op = m.group(1)
        new_op = _ARITH_FLIPS[op]
        mutated = line[:m.start(1)] + new_op + line[m.end(1):]
        out.append((f"arithmetic {op}->{new_op} @col{m.start(1)}", mutated))

    for m in _NUMBER_RE.finditer(line):
        literal = m.group(0)
        for target in ("0", "1"):
            if literal == target:
                continue
            mutated = line[:m.start()] + target + line[m.end():]
            out.append((f"literal {literal}->{target} @col{m.start()}", mutated))

    m = _IF_RE.search(line)
    if m:
        cond = m.group(1)
        mutated = line[:m.start()] + f"if (!({cond})){m.group(2)}"
        out.append(("if-negate", mutated))

    return out


def _changed_line_numbers(project: Path, base_sha: str, candidate_sha: str,
                           snippet_file: str, line_start: int, line_end: int) -> set[int]:
    """Candidate-side (1-indexed) line numbers touched by the diff, within
    [line_start, line_end], from `git diff -U0` hunk headers."""
    proc = subprocess.run(
        ["git", "-C", str(project), "diff", "-U0", base_sha, candidate_sha, "--", snippet_file],
        capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git diff {base_sha}..{candidate_sha} -- {snippet_file} failed: {proc.stderr}")
    changed: set[int] = set()
    cur = None
    added_seen = 0
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for raw in proc.stdout.splitlines():
        hm = hunk_re.match(raw)
        if hm:
            cur = int(hm.group(1))
            added_seen = 0
            continue
        if cur is None:
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line_no = cur + added_seen
            if line_start <= line_no <= line_end:
                changed.add(line_no)
            added_seen += 1
    return changed


def mutate_diff(base_sha: str, candidate_sha: str, snippet_file: str, function: str,
                 acceptance_node_ids: list[str], *, project: Path = REPO, cap: int = 40) -> dict:
    """Mutates the lines `candidate_sha` changed (relative to `base_sha`)
    inside `function` in `snippet_file`, one mutation at a time, in a scratch
    tree built from `candidate_sha`. Runs `acceptance_node_ids` against each
    mutant. Caps at `cap` mutants, taken in a fixed deterministic order
    (ascending line number, then mutation label) -- no randomness.

    Returns {"verdict", "total_mutants", "killed", "survived",
    "survivors": [{"line", "text", "mutation", "seconds"}],
    "baseline_valid_ids", "baseline_skipped_ids", "seconds_per_mutant"}.
    Node ids that do not already pass on the unmutated candidate are
    reported in "baseline_skipped_ids" and excluded from kill detection --
    a test that fails before any mutation cannot be said to "kill" a mutant.
    """
    scratch = Path(tempfile.mkdtemp(prefix="mutate_diff_"))
    try:
        tree = scratch / "tree"
        _archive_tree(project, candidate_sha, tree)
        ok, out, build_seconds = _make(tree)
        if not ok:
            raise RuntimeError(f"build failed for candidate {candidate_sha}:\n{out}")

        target_path = tree / snippet_file
        candidate_text = target_path.read_text()
        span = find_function_span(candidate_text, function)
        if span is None:
            raise ValueError(f"{function} not found in {snippet_file} at {candidate_sha}")
        line_start = candidate_text.count("\n", 0, span[0]) + 1
        line_end = candidate_text.count("\n", 0, span[1]) + 1

        changed_lines = _changed_line_numbers(
            project, base_sha, candidate_sha, snippet_file, line_start, line_end,
        )

        lines = candidate_text.splitlines(keepends=True)
        mutant_plan: list[tuple[int, str, str]] = []
        for line_no in sorted(changed_lines):
            original_line = lines[line_no - 1]
            for label, mutated_line in _line_mutants(original_line):
                if mutated_line == original_line:
                    continue
                mutant_plan.append((line_no, label, mutated_line))
        mutant_plan.sort(key=lambda t: (t[0], t[1]))
        mutant_plan = mutant_plan[:cap]

        baseline_results, baseline_output, _ = _run_pytest(tree, acceptance_node_ids)
        baseline_valid_ids = [nid for nid in acceptance_node_ids if baseline_results.get(nid)]
        baseline_skipped_ids = [nid for nid in acceptance_node_ids if nid not in baseline_valid_ids]

        details = []
        mutant_seconds = []
        for line_no, label, mutated_line in mutant_plan:
            original_line = lines[line_no - 1]
            lines[line_no - 1] = mutated_line
            target_path.write_text("".join(lines))

            mut_start = time.monotonic()
            build_ok, build_out, m_build_seconds = _make(tree)
            if not build_ok:
                # A mutant that doesn't compile is a kill by construction --
                # no valid acceptance test can ever pass against it.
                killed = True
                test_seconds = 0.0
            else:
                results, _, test_seconds = _run_pytest(tree, baseline_valid_ids)
                killed = any(not results.get(nid, False) for nid in baseline_valid_ids)
            total_seconds = time.monotonic() - mut_start
            mutant_seconds.append(total_seconds)

            lines[line_no - 1] = original_line
            target_path.write_text("".join(lines))

            details.append({
                "line": line_no, "text": original_line.strip(), "mutation": label,
                "killed": killed, "survived": not killed, "seconds": total_seconds,
                "build_seconds": m_build_seconds, "test_seconds": test_seconds,
            })

        survivors = [d for d in details if d["survived"]]
        killed_count = len(details) - len(survivors)
        verdict = "UNDER_TESTED" if survivors else "OK"

        return {
            "verdict": verdict,
            "total_mutants": len(details),
            "killed": killed_count,
            "survived": len(survivors),
            "survivors": survivors,
            "details": details,
            "baseline_valid_ids": baseline_valid_ids,
            "baseline_skipped_ids": baseline_skipped_ids,
            "baseline_output": baseline_output,
            "build_seconds": build_seconds,
            "seconds_per_mutant": (sum(mutant_seconds) / len(mutant_seconds)) if mutant_seconds else 0.0,
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main(argv: list[str]) -> int:
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
