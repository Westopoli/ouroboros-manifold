"""PX-15 prototype: control liveness gate (DECISIONS.md R10).

R10's claim: a positive control proves nothing unless it behaves
differently on the clean build and on the debug build with its own
OM_BUG_* injected. Three real incidents were dead controls for three
different reasons, each found by hand after burning a card's full attempt
budget:

  R7h  tests/csim/controls/test_control_e05_agent_reads_live.py -- the
       step-3d read it checks completes, for every faction, before step 3f
       ever mutates anything this tick. No build, correct or buggy, can
       make that observation differ.
  R7l  tests/csim/controls/test_control_e05_garrison_before_damage.py --
       its own numbers (military 20.0, damage -16.0) never drive
       fmax(0, ...) negative, so "clamp then add garrison" and "add
       garrison then clamp" land on the same 31.3 either way.
  R9   tests/csim/controls/test_control_e05_telegraph_after_reinforce.py --
       the reorder it injects moves a step that writes synchronously, so
       swapping step 3c's position changes nothing the test can observe.

R10's fix is mechanical, not conventions-based: run the control twice
against the current build -- once as written (using the `dbg` fixture,
which injects its bug), once with the injection neutralised -- and compare
outcomes. LIVE if they differ (whichever direction: most controls are
written to PASS when the bug is injected, so LIVE usually means "passes
injected, fails clean", but this checker compares outcomes, it does not
assume a direction). DEAD if they agree. ERROR if the control cannot run
at all.

Neutralisation mechanism (chosen for fidelity, per the PX-15 brief): a
scratch copy of tests/csim (never the real tree) gets `om_debug_inject`
monkeypatched to a no-op, appended to a copy of conftest.py, gated on the
PX15_NEUTRALIZE env var. The test file itself is copied byte-for-byte --
only the fault is absent, the test body that asserts on it is unchanged.
This is faithful for every OM_BUG_* id except one discovered while building
this checker: OM_BUG_OSC_AS_LEVEL is enum value 0, and csrc/region.c's
om_world_new initialises w->inject = 0 too, so a debug-build world that
never calls om_debug_inject at all is already, by construction, in
OSC_AS_LEVEL's injected state. Neutralising that one control's injection
call does not reach a genuinely clean state -- it reaches the build's own
default state, which happens to equal the bug. See the PX-15 report for
the direct measurement that confirms this (release build vs. debug build
with no injection call diverge; debug-with-injection(0) and
debug-with-no-call are bit-identical). This checker still reports whatever
that comparison says (DEAD, in this case) because R10's rule is symmetric
under whichever build is "clean" -- it is the C harness's sentinel choice
that is not faithful here, not this checker's method.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLS_DIR = REPO_ROOT / "tests" / "csim" / "controls"
DEFAULT_PYTHON = "/home/westopoli/Projects/agora/.venv/bin/python"
NEUTRALIZE_ENV = "PX15_NEUTRALIZE"

# Appended (never inserted into) a *scratch copy* of tests/csim/conftest.py.
# _configure_debug is looked up by name at call time inside the dbg()
# fixture, so redefining it later in the same module's globals overrides it
# without touching a single line the real conftest.py wrote.
NEUTRALIZE_SNIPPET = '''

# ---- PX-15 scratch-only neutralization hook (never in the real tree) ----
import os as _px15_os
if _px15_os.environ.get("PX15_NEUTRALIZE"):
    _px15_real_configure_debug = _configure_debug

    def _configure_debug(h):
        _px15_real_configure_debug(h)
        h.om_debug_inject = lambda *a, **kw: None
'''


# ---------------------------------------------------------------- bug_id_of --

def bug_id_of(control_file: Path) -> Optional[str]:
    """The OM_BUG_*/OMBug.* member a control names, e.g. "OMBug.EMPTY_DRIFTS"
    or "OMBugE05.INJECT_IGNORED" -- the second argument of its
    `<handle>.om_debug_inject(w, <this>)` call site, found by walking the
    AST for a Call whose func attr is om_debug_inject. Returns None if no
    such call exists (or its argument isn't a plain Name/Attribute)."""
    try:
        tree = ast.parse(control_file.read_text())
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "om_debug_inject"):
            continue
        if len(node.args) < 2:
            continue
        arg = node.args[1]
        if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name):
            return f"{arg.value.id}.{arg.attr}"
        if isinstance(arg, ast.Name):
            return arg.id
    return None


# ---------------------------------------------------------------- outcomes --

@dataclass(frozen=True)
class Outcome:
    status: str  # "passed" | "failed" | "error" | "skipped"
    message: str = ""


@dataclass
class Verdict:
    control: str
    bug_id: Optional[str]
    verdict: str  # "LIVE" | "DEAD" | "ERROR"
    reason: str
    as_written: Outcome
    neutralized: Outcome


def _first_line(text: str) -> str:
    return (text or "").splitlines()[0] if text else ""


def detect_uncheckable_cause(outcome: Outcome) -> Optional[str]:
    """Why a single run can't be trusted as a real pass/fail, grouped into
    the three causes the sweep reports: "unbuilt stub" (skip, or a ctypes
    AttributeError for a symbol the library doesn't export yet), "missing
    enum member" (an OMBug*/OMBugE0* attribute the control names but the
    header doesn't define -- most of E-06..E-17's controls), or "collection
    error" (anything else raised during setup/collection, e.g. the
    fixture's own COMPILE ERROR path, or a bad import)."""
    text = outcome.message or ""
    if outcome.status == "skipped":
        return "unbuilt stub"
    if "undefined symbol" in text:
        return "unbuilt stub"
    if "COMPILE ERROR" in text:
        return "unbuilt stub"
    if "has no attribute" in text and ("OMBug" in text or "type object" in text):
        return "missing enum member"
    if outcome.status == "error":
        return "collection error"
    return None


def judge(as_written: Outcome, neutralized: Outcome) -> tuple[str, str]:
    """Pure LIVE/DEAD/ERROR decision over a pair of Outcomes. Checked before
    the direction-agnostic pass/fail comparison: an uncheckable run (missing
    enum member, unbuilt stub, collection error) is ERROR even when both
    sides agree, since e.g. the same AttributeError on both sides would
    otherwise read as a spurious DEAD."""
    for label, outcome in (("as-written", as_written), ("neutralized", neutralized)):
        cause = detect_uncheckable_cause(outcome)
        if cause:
            detail = _first_line(outcome.message)
            reason = f"{cause} ({label} run {outcome.status}"
            reason += f": {detail})" if detail else ")"
            return "ERROR", reason

    if as_written.status != neutralized.status:
        return "LIVE", f"as-written={as_written.status}, neutralized={neutralized.status}"
    return "DEAD", f"both runs {as_written.status}"


RunPair = Callable[[Path], tuple[Outcome, Outcome]]


def liveness(control_file: Path, *, run_pair: Optional[RunPair] = None,
             scratch_root: Optional[Path] = None, python_exe: Optional[str] = None,
             project: Optional[Path] = None) -> Verdict:
    """Run one control both ways and judge it. `run_pair`, when given,
    replaces the real (scratch tree + subprocess pytest) mechanics with
    anything returning (as_written, neutralized) Outcomes -- used by the
    unit tests so they never need the real C build."""
    control_file = Path(control_file)
    bug_id = bug_id_of(control_file)
    if run_pair is None:
        as_written, neutralized = _real_run_pair(
            control_file, scratch_root=scratch_root, python_exe=python_exe, project=project,
        )
    else:
        as_written, neutralized = run_pair(control_file)
    verdict, reason = judge(as_written, neutralized)
    return Verdict(control=control_file.name, bug_id=bug_id, verdict=verdict,
                    reason=reason, as_written=as_written, neutralized=neutralized)


# ---------------------------------------------------------------- scratch tree --
# Never touches tests/csim/ or csrc/ in the real repo. A scratch tree mirrors
# the two directories a control needs (tests/csim/conftest.py, plus whichever
# tests/csim/controls/*.py files are under test) at the same relative depth,
# so conftest.py's own REPO_ROOT = parents[2] resolves to the scratch tree
# root -- and libouroboros.so / libouroboros_dbg.so are symlinked there too,
# so the run is against the real repo's *current build*, isolated so the
# scratch pytest process can never race the real repo's own conftest-driven
# `make` (which agora's own build may be touching concurrently).

def ensure_scratch_tree(scratch_root: Path, project: Optional[Path] = None) -> Path:
    project = Path(project) if project else REPO_ROOT
    tree = Path(scratch_root) / "tree"
    controls_dir = tree / "tests" / "csim" / "controls"
    controls_dir.mkdir(parents=True, exist_ok=True)

    for name in ("libouroboros.so", "libouroboros_dbg.so"):
        link = tree / name
        target = project / name
        if link.is_symlink() or link.exists():
            link.unlink()
        if target.exists():
            link.symlink_to(target)

    conftest_src = (project / "tests" / "csim" / "conftest.py").read_text()
    conftest_dst = tree / "tests" / "csim" / "conftest.py"
    conftest_dst.write_text(conftest_src + NEUTRALIZE_SNIPPET)

    # conftest.py's world_factory reads the feature-set tables relative to
    # REPO_ROOT (D1, conftest-only): mirror docs/northstar/spec_factory/*.toml
    # into the scratch tree so the fixtures resolve there too.
    spec_src = project / "docs" / "northstar" / "spec_factory"
    spec_dst = tree / "docs" / "northstar" / "spec_factory"
    spec_dst.mkdir(parents=True, exist_ok=True)
    for toml in spec_src.glob("*.toml"):
        shutil.copyfile(toml, spec_dst / toml.name)
    return tree


def sync_controls(tree: Path, control_paths: list[Path]) -> None:
    """Make tree/tests/csim/controls contain exactly `control_paths`, copied
    byte-for-byte (never symlinked -- these are the exact bytes being
    judged, and must survive the real tree changing under them mid-sweep)."""
    controls_dir = tree / "tests" / "csim" / "controls"
    wanted = {p.name for p in control_paths}
    for existing in controls_dir.glob("*.py"):
        if existing.name not in wanted:
            existing.unlink()
    for p in control_paths:
        shutil.copyfile(p, controls_dir / p.name)


def parse_junit(xml_path: Path) -> dict[str, Outcome]:
    out: dict[str, Outcome] = {}
    if not xml_path.exists():
        return out
    root = ET.parse(xml_path).getroot()
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        module = classname.rsplit(".", 1)[-1] if classname else ""
        key = f"{module}.py"
        failure = tc.find("failure")
        error = tc.find("error")
        skipped = tc.find("skipped")
        if failure is not None:
            out[key] = Outcome("failed", failure.get("message") or (failure.text or ""))
        elif error is not None:
            out[key] = Outcome("error", error.get("message") or (error.text or ""))
        elif skipped is not None:
            out[key] = Outcome("skipped", skipped.get("message") or (skipped.text or ""))
        else:
            out[key] = Outcome("passed", "")
    return out


def run_batch(tree: Path, control_paths: list[Path], *, neutralize: bool,
              python_exe: Optional[str] = None, timeout: int = 600) -> dict[str, Outcome]:
    sync_controls(tree, control_paths)
    python_exe = python_exe or DEFAULT_PYTHON
    junit_path = tree / ("junit_neutralized.xml" if neutralize else "junit_as_written.xml")
    env = os.environ.copy()
    if neutralize:
        env[NEUTRALIZE_ENV] = "1"
    else:
        env.pop(NEUTRALIZE_ENV, None)
    subprocess.run(
        [python_exe, "-m", "pytest", "tests/csim/controls", "-q", "--no-header",
         "--color=no", "-p", "no:cacheprovider", f"--junitxml={junit_path}"],
        cwd=str(tree), env=env, capture_output=True, text=True, timeout=timeout,
    )
    results = parse_junit(junit_path)
    for p in control_paths:
        results.setdefault(p.name, Outcome("error", "not collected (no matching junit testcase)"))
    return results


def _real_run_pair(control_file: Path, *, scratch_root: Optional[Path] = None,
                    python_exe: Optional[str] = None,
                    project: Optional[Path] = None) -> tuple[Outcome, Outcome]:
    scratch_root = Path(scratch_root) if scratch_root else Path(os.environ.get("TMPDIR") or "/tmp") / "om_control_liveness"
    tree = ensure_scratch_tree(scratch_root, project)
    as_written = run_batch(tree, [control_file], neutralize=False, python_exe=python_exe)
    neutralized = run_batch(tree, [control_file], neutralize=True, python_exe=python_exe)
    return as_written[control_file.name], neutralized[control_file.name]


# ---------------------------------------------------------------- sweep --

@dataclass
class SweepReport:
    verdicts: list[Verdict]
    elapsed_s: float
    mean_s_per_control: float


def sweep(control_paths: Optional[list[Path]] = None, *, scratch_root: Optional[Path] = None,
          python_exe: Optional[str] = None, project: Optional[Path] = None) -> SweepReport:
    """One pair of batched pytest invocations over every control in
    `control_paths` (default: all of tests/csim/controls), instead of one
    pair per file -- both libraries are already built, so the whole cost is
    two pytest collect-and-run passes, not 2*N process starts."""
    if control_paths is None:
        control_paths = sorted(CONTROLS_DIR.glob("test_control_*.py"))
    scratch_root = Path(scratch_root) if scratch_root else Path(os.environ.get("TMPDIR") or "/tmp") / "om_control_liveness"

    start = time.perf_counter()
    tree = ensure_scratch_tree(scratch_root, project)
    as_written_map = run_batch(tree, control_paths, neutralize=False, python_exe=python_exe)
    neutralized_map = run_batch(tree, control_paths, neutralize=True, python_exe=python_exe)
    elapsed = time.perf_counter() - start

    verdicts = []
    for p in control_paths:
        aw = as_written_map[p.name]
        ne = neutralized_map[p.name]
        verdict, reason = judge(aw, ne)
        verdicts.append(Verdict(control=p.name, bug_id=bug_id_of(p), verdict=verdict,
                                 reason=reason, as_written=aw, neutralized=ne))

    mean = elapsed / len(control_paths) if control_paths else 0.0
    return SweepReport(verdicts=verdicts, elapsed_s=elapsed, mean_s_per_control=mean)


# ---------------------------------------------------------------- CLI --

def _verdict_to_dict(v: Verdict) -> dict:
    d = asdict(v)
    return d


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("controls", nargs="*", help="specific control files (default: every "
                    "tests/csim/controls/test_control_*.py)")
    ap.add_argument("--scratch-root", default=None)
    ap.add_argument("--project", default=None, help="tree whose conftest, libs and spec tables the scratch tree mirrors (default: this repo)")
    ap.add_argument("--python", default=None, help=f"interpreter for the scratch pytest runs "
                     f"(default: {DEFAULT_PYTHON})")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    control_paths = [Path(c).resolve() for c in args.controls] if args.controls else None
    scratch_root = Path(args.scratch_root) if args.scratch_root else None

    report = sweep(control_paths, scratch_root=scratch_root, python_exe=args.python,
                  project=Path(args.project) if args.project else None)

    live = sum(1 for v in report.verdicts if v.verdict == "LIVE")
    dead = sum(1 for v in report.verdicts if v.verdict == "DEAD")
    err = sum(1 for v in report.verdicts if v.verdict == "ERROR")
    summary = (f"LIVE={live} DEAD={dead} ERROR={err} total={len(report.verdicts)} "
               f"elapsed={report.elapsed_s:.1f}s mean={report.mean_s_per_control * 1000:.0f}ms/control")

    if args.json:
        print(json.dumps({
            "elapsed_s": report.elapsed_s,
            "mean_s_per_control": report.mean_s_per_control,
            "live": live, "dead": dead, "error": err,
            "summary": summary,
            "verdicts": [_verdict_to_dict(v) for v in report.verdicts],
        }, indent=2))
    else:
        for v in report.verdicts:
            print(f"{v.verdict:5s} {v.control} bug={v.bug_id} -- {v.reason}")
        print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
