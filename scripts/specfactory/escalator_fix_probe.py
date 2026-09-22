"""PX-17/PX-18 prototype: can the escalator (Gemini via agy) fix an
already-diagnosed defect alone, unattended, under a parent-patch fence?

Handoff brief: docs/northstar/proving_ground/ (PX-17/PX-18 write-ups once
run). Design source: docs/northstar/PLAN.md "The Factory" (Roles table,
"Gates the worker cannot move"); DECISIONS.md fifth/seventh rounds and R8,
C4, C6 (docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md).

This tool never writes a fix itself. It hands a real, already-diagnosed
incident to Gemini through the same `agy` CLI invocation shape Agora's
build-intervene uses (~/Projects/agora/scripts/agy_client.py::chat), under
a parent-patch fence (only the named function(s) may change), applies the
reply with function-level splice (~/Projects/agora/scripts/splice.py), gates
it, and scores the outcome. Sub-agents implement, never design (CLAUDE.md);
this script is the harness the experiment runs inside, not a substitute for
Gemini's own attempt.

Usage: python escalator_fix_probe.py run <case_id> --model <agy-model-id>
  [--worktree DIR] [--results DIR] [--max-attempts 3] [--repo REPO_ROOT]
Case ids: R7a, R7d, R8 (PX-17); R7f, R7l (PX-18).
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AGORA_SCRIPTS = pathlib.Path.home() / "Projects" / "agora" / "scripts"
SCHEMA_PATH = pathlib.Path(__file__).resolve().parent / "escalator_fix_schema.json"
PYTHON_BIN = os.environ.get("SPECFACTORY_PYTHON",
                             str(pathlib.Path.home() / "Projects" / "agora" / ".venv" / "bin" / "python"))
AGY_BIN = os.environ.get("AGY_BIN", "agy")

sys.path.insert(0, str(AGORA_SCRIPTS))
import splice  # noqa: E402  (agora scripts/splice.py: extract/replace)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agy_json import payload_from_envelope  # noqa: E402
import fixture_defects  # noqa: E402


# ============================================================ data model ==

@dataclasses.dataclass(frozen=True)
class FenceTarget:
    """One function (or, for R7a, one explicit line range) an escalator
    call may touch. `label` is the exact string Gemini must return as the
    reply's `name` -- for a real C/Python function this is the function
    name; for a non-function fenced range (R7a's #include block) it is a
    synthetic label the prompt spells out explicitly."""
    file: str
    label: str
    symbol: str | None = None
    lines: str | None = None

    def lang(self) -> str:
        return splice.lang_of(self.file)


@dataclasses.dataclass(frozen=True)
class Case:
    id: str
    probe: str  # "PX-17" | "PX-18"
    pre_fix_commit: str
    human_fix_commit: str | None
    fence: tuple[FenceTarget, ...]
    diagnosis: str
    contract_quote: str
    target_tests: tuple[str, ...]
    role_note: str = (
        "You are the escalator in an autonomous build system (Agora). A "
        "diagnosis below already identifies a real defect in already-merged "
        "code (or an already-authored test). Fix only inside the fence.")
    pattern_reference: str | None = None
    sequential: bool = False  # True: fence targets are separate agy calls, in order
    extra_gates: tuple[str, ...] = ()  # names of case-specific gate functions to run after green+no-worse
    pre_fix_commit_is_dynamic: bool = False  # True: resolve pre_fix_commit as `git rev-parse HEAD` in REPO
    target_tests_mode: str = "pass"  # "pass": target_tests must all pass. "no_compile_failure" (R7a):
    # the fenced fix is a build prerequisite only, not new logic -- the target tests are expected to
    # still be mostly red on real assertions; the gate is that they compile and collect at all.
    reference_splice: tuple[tuple[str, str], ...] = ()  # (file, symbol) pairs to splice in from the real
    # repo's HEAD before any gating, when the fenced test needs C the fence's own pre-fix commit hasn't
    # built yet (both the writer and any reader stub the test calls)
    prereq_copy_from_human_fix: tuple[str, ...] = ()  # new files the target tests need that the fence
    # can't create (e.g. R8's new control test) -- copied verbatim from human_fix_commit at setup,
    # never authored by Gemini, same as every other case's pre-existing target tests
    prereq_text_patches: tuple[tuple[str, str, str], ...] = ()  # (file, old, new) storage prerequisites
    # outside the fence (a new enum entry, a new struct field) the fence's own function can't add --
    # same class as R2/R7a, applied once at setup before any Gemini call


class FenceViolation(ValueError):
    """Gemini's reply named a function outside the fence, or the reply
    otherwise did not match exactly the fenced function set."""


class AgyCallError(RuntimeError):
    """agy itself failed (nonzero exit, timeout, or schema mismatch)."""


class TransportUnavailable(RuntimeError):
    """A --transport was named whose backing package/binary is not
    installed or importable in this interpreter. A harness setup problem,
    never a model finding -- kept separate from AgyCallError so run_case's
    retry loop (which treats AgyCallError as retryable-with-feedback) does
    not swallow it; the CLI exits 3 on this instead."""


@dataclasses.dataclass
class PytestResult:
    returncode: int
    stdout: str
    stderr: str
    failing: set[str]

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclasses.dataclass
class GateResult:
    ok: bool
    name: str
    detail: str


# =================================================================== agy ==

def RUN_AGY(argv: list[str], *, env: dict, timeout: int) -> subprocess.CompletedProcess:
    """The one function in this module that spawns agy. Module-level hook
    by design -- tests monkeypatch this attribute with a fake."""
    return subprocess.run(argv, env=env, capture_output=True, text=True, timeout=timeout)


def _agy_env() -> dict:
    # Same isolation agy_client.py uses: agy falls back to file-based token
    # storage over the real keyring sign-in when these are set (2026-09
    # gemini_compute.md spike).
    env = os.environ.copy()
    for key in ("SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"):
        env.pop(key, None)
    local_bin = str(pathlib.Path.home() / ".local" / "bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    return env


def call_gemini(model: str, prompt_text: str, *, timeout: int = 300) -> tuple[dict, float]:
    """One escalator call. Returns (payload, wall_seconds). Raises
    AgyCallError on a process-level failure or a schema mismatch."""
    argv = [AGY_BIN, "--model", model, "--prompt", prompt_text,
            "--output-format", "json", "--json-schema", str(SCHEMA_PATH),
            "--dangerously-skip-permissions", "--sandbox"]
    t0 = time.monotonic()
    try:
        result = RUN_AGY(argv, env=_agy_env(), timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AgyCallError(f"agy timed out after {timeout}s: {exc}") from exc
    wall = time.monotonic() - t0
    if result.returncode != 0:
        raise AgyCallError(f"agy exited {result.returncode}: {result.stderr[-800:]}")
    payload = payload_from_envelope(result.stdout, ("functions", "rationale"))
    if payload is None:
        raise AgyCallError(f"agy reply did not match the expected schema: {result.stdout[:800]!r}")
    return payload, wall


DEEPSEEK_CAMPAIGN = "px17-px18-escalator-probe"
DEEPSEEK_SYSTEM = "Follow the fence and the output contract exactly. Reply with JSON only, nothing else."


def DEEPSEEK_CHAT_JSON(model: str, system: str, user: str, **kwargs):
    """The one function in this module that calls DeepSeek. Module-level
    hook by design -- tests monkeypatch this attribute with a fake, same
    pattern as RUN_AGY."""
    if str(AGORA_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(AGORA_SCRIPTS))
    import deepseek_client
    return deepseek_client.chat_json(model, system, user, **kwargs)


def call_deepseek(model: str, prompt_text: str, *, timeout: int = 300) -> tuple[dict, float]:
    """One escalator call through DeepSeek's direct API (Agora's driver
    model, not agy) -- swapped in 2026-09-21 when every agy quota group
    (Gemini ~45h, Claude/GPT ~4h) was exhausted at run time. Returns the
    same (payload, wall_seconds) contract as call_gemini; agy_client.py's
    own docstring notes it was built as a drop-in for this same
    deepseek_client.chat() reply shape."""
    t0 = time.monotonic()
    try:
        payload = DEEPSEEK_CHAT_JSON(model, DEEPSEEK_SYSTEM, prompt_text,
                                      json_schema={"type": "object"}, timeout=timeout,
                                      campaign=DEEPSEEK_CAMPAIGN, purpose="escalator-fix-probe")
    except Exception as exc:
        raise AgyCallError(f"deepseek call failed: {exc}") from exc
    wall = time.monotonic() - t0
    if not isinstance(payload, dict) or "functions" not in payload or "rationale" not in payload:
        raise AgyCallError(f"deepseek reply did not match the expected schema: {payload!r}")
    return payload, wall


ANTHROPIC_SYSTEM = "Follow the fence and the output contract exactly. Reply with JSON only, nothing else."
ANTHROPIC_KEY_FILE = pathlib.Path("~/.config/agora/anthropic.key").expanduser()


def ANTHROPIC_CHAT(model: str, system: str, user: str, *, timeout: int) -> str:
    """The one function in this module that calls the Anthropic Messages
    API through the Anthropic Python SDK. Module-level hook by design --
    tests monkeypatch this attribute with a fake, same pattern as
    RUN_AGY/DEEPSEEK_CHAT_JSON. Raises TransportUnavailable if the SDK
    (the `anthropic` package) is not installed in this interpreter."""
    try:
        import anthropic
    except ImportError as exc:
        raise TransportUnavailable(
            "the 'anthropic' package is not installed in this interpreter -- "
            "the api-anthropic transport needs the Anthropic Python SDK "
            f"(pip install anthropic in the venv running this probe): {exc}") from exc
    key = os.environ.get("ANTHROPIC_API_KEY") or (
        ANTHROPIC_KEY_FILE.read_text().strip() if ANTHROPIC_KEY_FILE.exists() else None)
    if not key:
        raise AgyCallError(f"no Anthropic API key configured (ANTHROPIC_API_KEY or {ANTHROPIC_KEY_FILE})")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(model=model, max_tokens=4096, temperature=0.2, system=system,
                                   messages=[{"role": "user", "content": user}], timeout=timeout)
    return "".join(getattr(block, "text", "") for block in resp.content)


def call_anthropic(model: str, prompt_text: str, *, timeout: int = 300) -> tuple[dict, float]:
    """One escalator call through the Anthropic Messages API (the
    api-anthropic transport -- --transport only, there is no by-model-name
    inference to this transport). Returns the same (payload, wall_seconds)
    contract as call_gemini/call_deepseek."""
    t0 = time.monotonic()
    try:
        text = ANTHROPIC_CHAT(model, ANTHROPIC_SYSTEM, prompt_text, timeout=timeout)
    except TransportUnavailable:
        raise
    except Exception as exc:
        raise AgyCallError(f"anthropic call failed: {exc}") from exc
    wall = time.monotonic() - t0
    payload = payload_from_envelope(text, ("functions", "rationale"))
    if payload is None:
        raise AgyCallError(f"anthropic reply did not match the expected schema: {text[:800]!r}")
    return payload, wall


_TRANSPORTS = ("api-deepseek", "api-anthropic", "agy")


def resolve_transport(transport: str | None, model: str) -> str:
    """--transport, when given, is authoritative. Otherwise: the original
    by-model-name heuristic (deepseek-prefixed names go to the DeepSeek
    API, everything else to agy). There is no by-name heuristic for
    api-anthropic -- it is reached only through an explicit --transport."""
    if transport is not None:
        if transport not in _TRANSPORTS:
            raise ValueError(f"unknown transport {transport!r}, expected one of {_TRANSPORTS}")
        return transport
    return "api-deepseek" if model.startswith("deepseek") else "agy"


def call_escalator(model: str, prompt_text: str, *, timeout: int = 300,
                    transport: str | None = None) -> tuple[dict, float]:
    """Dispatches by `transport` when given, else by model name (the
    original heuristic: deepseek-prefixed models to the DeepSeek API,
    everything else to agy)."""
    resolved = resolve_transport(transport, model)
    if resolved == "api-deepseek":
        return call_deepseek(model, prompt_text, timeout=timeout)
    if resolved == "api-anthropic":
        return call_anthropic(model, prompt_text, timeout=timeout)
    return call_gemini(model, prompt_text, timeout=timeout)


# ================================================================ prompt ==

_OUTPUT_CONTRACT = """\
Output contract: reply with JSON matching this schema exactly, nothing else:
{"functions": [{"name": "<exact fence label>", "text": "<complete replacement text>"}], "rationale": "<one sentence>"}
- Return one entry per fenced target listed above, in the order listed, and no others.
- Each entry's "name" must be EXACTLY the quoted string after name= in that target's heading
  below -- copy it character for character. It is never the file path, never the file path
  combined with the label, and never anything after "in ...". For example if a heading reads
  ### name="om_step_decisions" (in csrc/agent.c), the JSON "name" is exactly om_step_decisions,
  not csrc/agent.c, and not "csrc/agent.c :: om_step_decisions".
- Each entry's "text" is the COMPLETE replacement text for that one fenced target: for a
  named function, the entire function from its signature/return type through its closing
  brace, nothing before or after it; for an explicit line range, exactly the replacement
  lines for that range. Do not include any other function, any #include line (unless the
  fence itself is an #include block), or any commentary outside the JSON.
- You have no repository access. Everything you need is in this prompt."""


def build_prompt(case: Case, targets: list[FenceTarget], current_texts: dict[str, str],
                  failing_output: str, previous_feedback: str | None) -> str:
    parts = [case.role_note, "", "## Diagnosis", case.diagnosis]
    if case.contract_quote:
        parts += ["", "## Contract (quoted verbatim, do not paraphrase against it)", case.contract_quote]
    if case.pattern_reference:
        parts += ["", "## Pattern already used elsewhere in this codebase", case.pattern_reference]
    parts += ["", "## Fenced target(s) -- current text"]
    for t in targets:
        parts += [f'### name="{t.label}" (in {t.file})', "```", current_texts[t.label].rstrip("\n"), "```"]
    parts += ["", "## Failing test output (current, before your fix)", "```", failing_output.strip()[-4000:], "```"]
    if previous_feedback:
        parts += ["", "## Previous attempt failed -- feedback", previous_feedback.strip()[-4000:]]
    parts += ["", _OUTPUT_CONTRACT]
    return "\n".join(parts)


# ============================================================ fence/diff ==

def check_fence(functions: list[dict], allowed_labels: list[str]) -> list[str]:
    """Returns the list of violating names (empty = clean). A violation is
    any returned name not in the fence, or the fence not being covered
    exactly once each (duplicates count as a violation too)."""
    allowed = set(allowed_labels)
    seen: dict[str, int] = {}
    violations: list[str] = []
    for fn in functions:
        name = fn.get("name", "")
        seen[name] = seen.get(name, 0) + 1
        if name not in allowed:
            violations.append(name)
    for name, count in seen.items():
        if name in allowed and count > 1:
            violations.append(name)
    return violations


def _resolve_lines(text: str, target: FenceTarget) -> str | None:
    """target.lines == "*" is the whole-file sentinel (R7l: the plan fences
    the whole control file, not one function, because the detector's own
    numbers live in the module docstring above the test function -- outside
    any function-scoped fence)."""
    if target.lines == "*":
        return f"1-{len(text.splitlines())}"
    return target.lines


def apply_functions(worktree: pathlib.Path, targets: list[FenceTarget],
                     functions_by_label: dict[str, str]) -> dict[str, str]:
    """Splice each target's returned text over its current span. Returns
    {file: unified-diff-ish before/after snippet} for the results record.
    Raises splice.SpliceError if a target's symbol/lines can't be found."""
    diffs: dict[str, str] = {}
    by_file: dict[str, list[FenceTarget]] = {}
    for t in targets:
        by_file.setdefault(t.file, []).append(t)

    for rel_file, file_targets in by_file.items():
        path = worktree / rel_file
        text = path.read_text()
        lang = splice.lang_of(rel_file)
        # Apply in reverse line order so an earlier splice's line-count
        # change never invalidates a later span in the same file.
        spans = [(t, splice.extract(text, symbol=t.symbol, lines=_resolve_lines(text, t), lang=lang))
                 for t in file_targets]
        spans.sort(key=lambda ts: ts[1].start, reverse=True)
        before_snippets = []
        for t, span in spans:
            before_snippets.append(f"--- {rel_file} :: {t.label} (before) ---\n{span.body}")
            text = splice.replace(text, span, functions_by_label[t.label])
        path.write_text(text)
        after = "\n".join(f"--- {rel_file} :: {t.label} (after) ---\n{functions_by_label[t.label]}"
                           for t, _ in spans)
        diffs[rel_file] = "\n".join(before_snippets) + "\n" + after
    return diffs


def restore_files(worktree: pathlib.Path, originals: dict[str, str]) -> None:
    for rel_file, text in originals.items():
        (worktree / rel_file).write_text(text)


# ================================================================= gates ==

def run_make(worktree: pathlib.Path, *, timeout: int = 180) -> GateResult:
    res = subprocess.run(["make", "-s", "libouroboros.so", "libouroboros_dbg.so"],
                          cwd=str(worktree), capture_output=True, text=True, timeout=timeout)
    ok = res.returncode == 0
    return GateResult(ok, "build", (res.stdout + res.stderr)[-4000:] if not ok else "build ok")


_FAILED_RE = re.compile(r"^(?:FAILED|ERROR) (\S+)", re.M)


def run_pytest(worktree: pathlib.Path, args: list[str], *, timeout: int = 120) -> PytestResult:
    argv = [PYTHON_BIN, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", *args]
    res = subprocess.run(argv, cwd=str(worktree), capture_output=True, text=True, timeout=timeout)
    failing = set(_FAILED_RE.findall(res.stdout))
    return PytestResult(res.returncode, res.stdout, res.stderr, failing)


def compute_suite_failing_ids(worktree: pathlib.Path, *, timeout: int = 120) -> set[str]:
    result = run_pytest(worktree, ["tests/csim"], timeout=timeout)
    return result.failing


def no_worse(before: set[str], after: set[str]) -> tuple[bool, set[str]]:
    """True (ok) iff `after` introduces no failing id absent from `before`."""
    new = after - before
    return (not new), new


def target_tests_gate(worktree: pathlib.Path, case: Case) -> GateResult:
    args = list(case.target_tests)
    result = run_pytest(worktree, args)
    if case.target_tests_mode == "no_compile_failure":
        combined = result.stdout + result.stderr
        if "COMPILE ERROR" in combined:
            return GateResult(False, "target_tests", combined[-4000:])
        if result.returncode not in (0, 1):
            # not plain pass/fail -- a pytest usage or collection-level crash
            return GateResult(False, "target_tests", combined[-4000:])
        return GateResult(True, "target_tests", "compiles and collects (tests may still be red on assertions)")
    if result.ok:
        return GateResult(True, "target_tests", "target tests pass")
    return GateResult(False, "target_tests", result.stdout[-4000:] + "\n" + result.stderr[-1000:])


def regression_gate(worktree: pathlib.Path, baseline_failing: set[str]) -> tuple[GateResult, set[str]]:
    after = compute_suite_failing_ids(worktree)
    ok, new = no_worse(baseline_failing, after)
    detail = "no new failures" if ok else f"{len(new)} new failure(s): {sorted(new)[:20]}"
    return GateResult(ok, "regression", detail), after


# ---------------------------------------------------- PX-18 extra gates --

def gate_assertions_preserved(worktree: pathlib.Path, case: Case, ctx: dict) -> GateResult:
    """Every assert statement in the ORIGINAL fenced function(s) must still
    appear (as an equivalent AST) somewhere in the NEW text. Catches a
    'fix' that quietly drops an assertion instead of correcting the
    fixture around it."""
    missing_all: dict[str, list[str]] = {}
    for t in case.fence:
        old_src = ctx["originals_by_label"][t.label]
        new_src = ctx["new_texts_by_label"][t.label]
        old_asserts = _assert_shapes(old_src)
        new_asserts = _assert_shapes(new_src)
        missing = sorted(old_asserts - new_asserts)
        if missing:
            missing_all[t.label] = missing
    if missing_all:
        return GateResult(False, "assertions_preserved", f"assertions dropped: {missing_all}")
    return GateResult(True, "assertions_preserved", "every original assertion shape survives")


def _assert_shapes(func_src: str) -> set[str]:
    try:
        tree = ast.parse(func_src)
    except SyntaxError:
        return set()
    return {ast.dump(node.test, annotate_fields=False) for node in ast.walk(tree) if isinstance(node, ast.Assert)}


def gate_red_at_stub(worktree: pathlib.Path, case: Case, ctx: dict) -> GateResult:
    """The edited test must still fail against the unimplemented (stub) C
    it was originally red against -- a 'fix' that also happens to turn
    green with nothing built is vacuous."""
    stub_dir = ctx["stub_worktree"]
    for rel_file in {t.file for t in case.fence}:
        (stub_dir / rel_file).write_text((worktree / rel_file).read_text())
    result = run_pytest(stub_dir, list(case.target_tests))
    if result.ok:
        return GateResult(False, "red_at_stub", "edited test(s) pass against the unbuilt stub -- vacuous")
    return GateResult(True, "red_at_stub", "still red against the stub, for the expected reason")


def gate_two_agent_confound_clears(worktree: pathlib.Path, case: Case, ctx: dict) -> GateResult:
    findings = {}
    for t in case.fence:
        result = fixture_defects.two_agent_confound(worktree / t.file, t.symbol)
        if result.get("flag"):
            findings[t.label] = result
    if findings:
        return GateResult(False, "two_agent_confound", f"still confounded: {findings}")
    return GateResult(True, "two_agent_confound", "no two-agent confound remains")


def apply_reference_splice(worktree: pathlib.Path, pairs: tuple[tuple[str, str], ...]) -> None:
    """R7f-specific setup step, applied once to a worktree right after
    checkout, before any Gemini call: the fenced tests exercise
    om_step_reinforce (card 204a2's job, the writer) and om_tick_reinforces
    (its reader), both still unbuilt stubs at R7f's pre-fix commit
    (3f183d7) -- the real implementation does not land until later the same
    day. The executor verified R7f's own fix by hand-patching the real
    (now-merged, HEAD) reinforce logic in locally, uncommitted, then
    reverting before committing the test-only fix (DECISIONS.md fifth
    round, R7f row). This reproduces that step mechanically: splice HEAD's
    real functions into this worktree's stubs so the case's own
    target-tests gate means something (green against real behavior), while
    a SEPARATE, unspliced stub worktree still gates 'red for the right
    reason, not vacuously green' (gate_red_at_stub)."""
    for rel_file, symbol in pairs:
        ref_text = (REPO_ROOT / rel_file).read_text()
        ref_span = splice.extract(ref_text, symbol=symbol, lines=None, lang=splice.lang_of(rel_file))
        stub_text = (worktree / rel_file).read_text()
        stub_span = splice.extract(stub_text, symbol=symbol, lines=None, lang=splice.lang_of(rel_file))
        (worktree / rel_file).write_text(splice.replace(stub_text, stub_span, ref_span.body))


def gate_vacuous_clears(worktree: pathlib.Path, case: Case, ctx: dict) -> GateResult:
    """branch_coverage_of_control (PX-13) itself is convention-dependent: it
    regexes the docstring for 'military from X to Y' and
    '.garrison == pytest.approx(NUM' rather than reading the executed
    values. A reply that can't be parsed at all is NOT a pass -- that would
    let an unverifiable rewrite through silently -- so 'could not extract'
    is scored as a gate failure with feedback naming the exact phrasing
    the checker needs, not treated the same as 'no defect found'."""
    t = case.fence[0]
    result = fixture_defects.branch_coverage_of_control(worktree / t.file)
    if result.get("flag") == "VACUOUS_CONTROL":
        return GateResult(False, "vacuous_clears", f"still vacuous: {result}")
    if "correct" in result and "buggy" in result:
        diff = abs(result["correct"] - result["buggy"])
        if diff <= 1e-6:
            return GateResult(False, "vacuous_clears", f"formulas still within 1e-6: {result}")
        return GateResult(True, "vacuous_clears", f"distinguishing: correct={result['correct']} buggy={result['buggy']}")
    return GateResult(False, "vacuous_clears",
                       "the docstring could not be parsed for its military/damage/garrison numbers "
                       "(scripts/specfactory/fixture_defects.py needs the exact phrasing 'military "
                       "from <before> to <after>' and '.garrison == pytest.approx(<value>' somewhere "
                       f"in the file) -- rewrite the docstring to use that phrasing verbatim: {result}")


def gate_liveness_report(worktree: pathlib.Path, case: Case, ctx: dict) -> GateResult:
    """Informational only (never blocks): OM_BUG_GARRISON_BEFORE_DAMAGE has
    no C branch yet (R10/PX-15), so full liveness cannot pass regardless of
    the fixture. Runs control_liveness.py and records what it says."""
    t = case.fence[0]
    res = subprocess.run([PYTHON_BIN, "scripts/specfactory/control_liveness.py", str(worktree / t.file)],
                          cwd=str(worktree), capture_output=True, text=True, timeout=60)
    return GateResult(True, "liveness_report", (res.stdout + res.stderr)[-2000:])


EXTRA_GATES = {
    "assertions_preserved": gate_assertions_preserved,
    "red_at_stub": gate_red_at_stub,
    "two_agent_confound": gate_two_agent_confound_clears,
    "vacuous_clears": gate_vacuous_clears,
    "liveness_report": gate_liveness_report,
}


# ============================================================= case reg ==

_RNG_CONTRACT = """\
(csrc/ouroboros_sim.h, "the world RNG contract")
One PCG32 stream per world (O'Neill PCG-XSH-RR 64/32, the reference pcg32_random_r).
u = uniform in [0, 1) with 53 bits: a = next32() >> 5, b = next32() >> 6,
u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0) (two 32-bit outputs, a then b).
Forced RNG draws (fixture): this queues values that the next n uniform draws return
instead of the stream, in order; when the queue empties the stream resumes. "Every
consumer of the stream (agents, resolution, friction, admin roll...) takes from the
same queue, so tests set draws in the documented draw order. Draw order is part of
the contract." """

_FACTION_SET_PATTERN = """\
(csrc/faction.c::om_faction_set, the existing pattern every other draw site follows)
double u;
if (w->rng_forced_len > 0) {
    u = w->rng_forced[w->rng_forced_head];
    w->rng_forced_head++;
    w->rng_forced_len--;
} else {
    uint32_t next32 = (uint32_t)((w->rng_state >> 12) + w->rng_inc);
    w->rng_state = next32 * 6364136223846793005ULL + w->rng_inc;
    uint32_t a = next32 >> 5;
    next32 = (uint32_t)((w->rng_state >> 12) + w->rng_inc);
    w->rng_state = next32 * 6364136223846793005ULL + w->rng_inc;
    uint32_t b = next32 >> 6;
    u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
}"""

_INJECT_CONTRACT = """\
(csrc/ouroboros_sim.h, "intent injection (fixture)")
"Places an intent into the next om_world_step exactly as if faction_id had decided it
in step 3d: an attack (with mode; a telegraphed one enters the pending list and
resolves at tick + 3), a colonize, or a reinforce. A faction with an injected intent
this tick skips its own 3d decision, so a test controls exactly which intents
collide." """

_ALG_20_21_22 = """\
(docs/bible/algorithms.md)
ALG-20 Attack. effective_attack = commit * ATTACK_EFFICIENCY * tech_attack(attacker) * surprise,
surprise = SURPRISE_EFFICIENCY_MULT = 0.5 in surprise mode else 1. effective_defense =
m * RESISTANCE_FACTOR * tech_defense(defender) * entrenchment. net = (effective_attack -
effective_defense) * U(STOCHASTIC_RANGE), range (0.7, 1.3), one RNG draw.
ALG-21 Damage split. Breakthrough if net > BREAKTHROUGH_THRESHOLD = 15.0: dm = -0.8*net,
de = -0.3*net, dt = +min(0.5*net, 30.0). Contested if 0 < net <= 15: dm = -0.5*net,
de = -0.2*net, dt = +0.4*net. Repelled if net <= 0: dm = -0.10 * effective_attack, de = 0,
dt = +2.0. Budget spent = commit.
ALG-22 Conquest. Not repelled and m + dm < CONQUEST_THRESHOLD = 5.0: the region changes
owner; garrison = commit * CONQUEST_GARRISON_FRACTION = 0.65 is added to military AFTER
DAMAGE; extra de -= 5.0, dt += 8.0, dp -= 2.0; the economy floor is bypassed."""

_R036_RULES = """\
(docs/bible/epics/E-05-faction-agents-and-conflict.md, S-036)
R-036-05  Given a telegraphed attack is pending against a faction, When that faction's
reactive window runs, Then with probability min(1, defend weight / 1.5) it commits
min(budget * 0.30, attacker commit * 0.5) to reinforce the target, and commits nothing
if that is below 1.0.
R-036-06  Given a reinforce of commit 10 on a frontier region with military 30 and
tension 50, When resolved, Then base = 10 * 0.5 * (60 - 30)/60 = 2.5 and
d_military = 2.5 * U(0.75, 1.25)."""


def _make_cases() -> dict[str, Case]:
    cases: dict[str, Case] = {}

    cases["R7a"] = Case(
        id="R7a", probe="PX-17",
        pre_fix_commit="e024dde", human_fix_commit="4945db8",
        fence=(FenceTarget(file="csrc/resolve.c", label="resolve.c_include_block", lines="34-37"),),
        diagnosis=(
            "Every candidate fails to compile: "
            "`csrc/resolve.c: implicit declaration of function 'fmin'`; function-level splice "
            "cannot add #include lines, so the skeleton must carry math.h. This is a parent-patch "
            "storage/skeleton prerequisite (same class as the header's struct-field prerequisites), "
            "not new designed logic: add exactly one #include line, `#include <math.h>`, to the "
            "existing include block below, in the same style as the other includes there."),
        contract_quote="",
        target_tests=("tests/csim/test_E05_S036_declared_or_sprung.py",
                       "tests/csim/test_E05_S037_battles_have_a_shape.py"),
        target_tests_mode="no_compile_failure",
    )

    cases["R7d"] = Case(
        id="R7d", probe="PX-17",
        pre_fix_commit="bdf3ead", human_fix_commit="ecfcffe",
        fence=(FenceTarget(file="csrc/agent.c", label="om_step_decisions", symbol="om_step_decisions"),),
        diagnosis=(
            "3d's telegraph-versus-surprise draw (the mode-selection draw inside "
            "om_step_decisions, commented 'Draw random u ~ U(0, 1)') reads w->rng_state/w->rng_inc "
            "directly and never checks w->rng_forced_len at all -- every other draw site in this "
            "codebase checks the forced queue first, per the header's own documented RNG contract "
            "('every consumer of the stream... takes from the same queue'). A forced value meant "
            "for 3d's mode draw is silently skipped instead of consumed there. Fix only that one "
            "draw site inside om_step_decisions to check w->rng_forced_len first, exactly like the "
            "existing pattern below. Do not change anything else in the function."),
        contract_quote=_RNG_CONTRACT,
        pattern_reference=_FACTION_SET_PATTERN,
        target_tests=("tests/csim/test_px17_scratch_r7d.py",),
    )

    cases["R8"] = Case(
        id="R8", probe="PX-17",
        pre_fix_commit="212ba88", human_fix_commit="30e86bb",
        fence=(
            FenceTarget(file="csrc/agent.c", label="om_step_decisions", symbol="om_step_decisions"),
            FenceTarget(file="csrc/resolve.c", label="om_intent_inject", symbol="om_intent_inject"),
        ),
        sequential=True,
        diagnosis=(
            "om_intent_inject is a no-op under FACTIONS: the header's documented contract promises "
            "that an injected intent enters the next step as if decided in 3d, that a telegraphed "
            "one enters the pending list and resolves at tick + 3, and that 'a faction with an "
            "injected intent this tick skips its own 3d decision'. The code honours none of it: "
            "om_step_decisions starts with decisions_n = 0 and recomputes every faction with no "
            "skip for an already-injected faction; om_intent_inject never writes w->telegraphs[]. "
            "This is class 'merged code violating a documented contract' -- under the routing rule "
            "(design decisions reach Westley, everything else is cleared by the escalator so the "
            "local model keeps moving), you are the escalator fixing this autonomously, tests-first, "
            "under the named-function fence, two sequential fenced edits: "
            "(1) csrc/agent.c::om_step_decisions -- at the top of the function, a faction that "
            "already holds a decision entry for the tick this step is about to compute (an injected "
            "entry, stamped with the tick it applies to) must be preserved and skip its own "
            "recompute for this tick, instead of being wiped along with everything else. "
            "(2) csrc/resolve.c::om_intent_inject -- a TELEGRAPH-mode injection must append an "
            "entry to w->telegraphs[] with maturity tick + 3, matching how a normally-declared "
            "telegraph is recorded; a SURPRISE-mode or COLONIZE injection is unaffected. "
            "The REINFORCE consumer is out of scope for both edits."),
        contract_quote=_INJECT_CONTRACT,
        target_tests=("tests/csim/controls/test_control_e05_inject_ignored.py"
                       "::test_control_inject_ignored_trips_the_detector",),
        prereq_copy_from_human_fix=("tests/csim/controls/test_control_e05_inject_ignored.py",),
        prereq_text_patches=(
            ("csrc/ouroboros_sim.h",
             "    OM_BUG_SAME_TICK_REDECLARE       = 110  /* 3d re-declares against a target this faction\n"
             "                                              * already resolved an attack against this tick */\n"
             "} om_bug_e05;",
             "    OM_BUG_SAME_TICK_REDECLARE       = 110, /* 3d re-declares against a target this faction\n"
             "                                              * already resolved an attack against this tick */\n"
             "    OM_BUG_INJECT_IGNORED            = 111  /* 3d wipes an om_intent_inject entry and\n"
             "                                              * recomputes the faction's decision naturally */\n"
             "} om_bug_e05;"),
            ("tests/csim/conftest.py",
             "    SAME_TICK_REDECLARE = 110\n",
             "    SAME_TICK_REDECLARE = 110\n    INJECT_IGNORED = 111\n"),
        ),
    )

    cases["R7f"] = Case(
        id="R7f", probe="PX-18",
        pre_fix_commit="3f183d7", human_fix_commit="d3273fa",
        fence=(
            FenceTarget(file="tests/csim/test_E05_S036_declared_or_sprung.py",
                        label="test_R_036_05_with_probability_min_1_defend",
                        symbol="test_R_036_05_with_probability_min_1_defend"),
            FenceTarget(file="tests/csim/test_E05_S036_declared_or_sprung.py",
                        label="test_R_036_06_base_10_0_5_60",
                        symbol="test_R_036_06_base_10_0_5_60"),
        ),
        diagnosis=(
            "This is a test-defect finding (class 'test-defect' under the routing rule: a finding "
            "that a test problem, not a story problem, escalates to the escalator autonomously to "
            "fix the test; Westley is not involved). Two of eight sub-cases in these two test "
            "functions are confounded, found by hand-patching a reference reinforce implementation "
            "and reading read_telegraphs/read_decisions on every sub-case, not guessed: "
            "test_R_036_05's Case 2 (world w_alt, defender archetype Fortifier, budget 100) gives "
            "the DEFENDER's own attack candidate enough budget to clear its own viability bar, so "
            "it also declares its own attack against the attacker this same tick -- correct "
            "behavior (E-05 runs the identical decision loop for every faction, no scripted "
            "villain), not something the fixture anticipated. The fixture's assertion reads "
            "`len(read_reinforces(lib, w_alt)) == 1`, an aggregate count that is now confounded by "
            "the defender's own unrelated reinforce-adjacent record. Fix: filter to the record for "
            "the region actually under test (target_idx == 1) instead of assuming it is the only "
            "reinforce record this tick -- the exact same pattern test_R_036_01/02 already use for "
            "decisions (indexing to the faction under test instead of asserting a bare length). "
            "test_R_036_06's tier-ceiling sub-case (world w_cap) has the opposite problem: the "
            "ATTACKER's own budget (50/0.7) against a military-60 target falls below the attack- "
            "viability bar, so no telegraph is ever declared and the scenario cannot exercise the "
            "reinforce headroom cap it is meant to test at all. Fix: raise the attacker's budget in "
            "w_cap to 200/0.7 (the same order of budget R-036-01 already proves viable against an "
            "even tougher military-70 target) so a telegraph is declared; none of the values this "
            "rule actually asserts (commit, headroom, base, delta) depend on the attacker's exact "
            "commit above its own viability floor. Do not weaken, remove, or loosen any existing "
            "assertion about commit, headroom, base, delta, or the probability gate in either "
            "function -- only the two problems named above."),
        contract_quote=_R036_RULES,
        target_tests=(
            "tests/csim/test_E05_S036_declared_or_sprung.py::test_R_036_05_with_probability_min_1_defend",
            "tests/csim/test_E05_S036_declared_or_sprung.py::test_R_036_06_base_10_0_5_60",
        ),
        extra_gates=("assertions_preserved", "red_at_stub", "two_agent_confound"),
        reference_splice=(("csrc/resolve.c", "om_step_reinforce"), ("csrc/resolve.c", "om_tick_reinforces")),
    )

    cases["R7l"] = Case(
        id="R7l", probe="PX-18",
        pre_fix_commit="HEAD", human_fix_commit=None, pre_fix_commit_is_dynamic=True,
        fence=(FenceTarget(file="tests/csim/controls/test_control_e05_garrison_before_damage.py",
                            label="test_control_e05_garrison_before_damage.py", lines="*"),),
        diagnosis=(
            "This fence is the WHOLE FILE, not one function: the module docstring above the test "
            "documents the exact scenario numbers (military, damage, garrison) this control relies "
            "on, and it must stay accurate to whatever numbers you choose -- update it together with "
            "the test function, in the same reply, as one replacement for the whole file. This "
            "repository's own tooling (scripts/specfactory/fixture_defects.py) checks the docstring "
            "mechanically for two exact phrasings, so use them verbatim somewhere in the docstring: "
            "'military from <before-value> to <after-value>' (the defender's military before and "
            "after the attack's damage, not counting garrison) and, in the test body, "
            "'.garrison == pytest.approx(<value>' (already the convention the existing assertion "
            "uses -- keep it). "
            "This is a test-defect finding (class 'test-defect' under the routing rule; Westley is "
            "not involved). This positive control for OM_BUG_GARRISON_BEFORE_DAMAGE (bug id 106: "
            "'garrison added before damage, then destroyed by it') reuses test_R_038_01's exact "
            "numbers (defender military 20.0, damage delta -16.0, garrison 27.3), but "
            "military + damage = 4.0 never goes negative, so the correct order "
            "(max(0, m + d) + g) and the buggy order (max(0, m + g + d)) land on the exact same "
            "number (31.3) regardless of which one a candidate implements -- the control cannot "
            "fail no matter what is built, which is Principle 3 ('every detector ships with a "
            "positive control') violated by the control itself, the same failure class as R7h and "
            "R9 (a control that cannot observe the difference it exists to detect). Fix: rework the "
            "whole scenario (attacker/defender setup, commit, effective_attack, effective_defense) "
            "so the defender's military is low enough relative to the damage that the fmax(0.0, ...) "
            "clamp actually engages under one ordering and not the other -- a distinguishing case, "
            "not a one-line number swap -- while the scenario still lands in a clean breakthrough "
            "(net > 15.0) and conquest (post-damage military < 5.0) exactly as the rest of the test "
            "already asserts (attacks[0].outcome == BREAKTHROUGH, conquest == 1). Military around "
            "10.0 with the same damage/garrison numbers is one candidate order of magnitude (military "
            "10.0, damage -16.0 => max(0, 10-16)+27.3 = 27.3 correct vs max(0, 10+27.3-16) = 21.3 "
            "buggy -- a real, checkable 6.0 difference), but the commit/effective_attack/"
            "effective_defense inputs that produce that military and damage under ALG-20/21 have to "
            "be reworked together, not just the military literal."),
        contract_quote=_ALG_20_21_22,
        target_tests=("tests/csim/controls/test_control_e05_garrison_before_damage.py"
                       "::test_control_garrison_before_damage_trips_the_detector",),
        extra_gates=("vacuous_clears", "liveness_report"),
    )

    return cases


CASES = _make_cases()


# ================================================================ engine ==

def _git(repo: pathlib.Path, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def resolve_pre_fix_commit(case: Case, repo: pathlib.Path) -> str:
    if case.pre_fix_commit_is_dynamic:
        return _git(repo, "rev-parse", "HEAD")
    return case.pre_fix_commit


def make_worktree(repo: pathlib.Path, commit: str, dest: pathlib.Path) -> None:
    if dest.exists():
        raise FileExistsError(f"worktree destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "--detach", str(dest), commit],
                    check=True, capture_output=True, text=True)


def remove_worktree(repo: pathlib.Path, dest: pathlib.Path) -> None:
    subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(dest)],
                    capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "worktree", "prune"], capture_output=True, text=True)


_SCRATCH_R7D_TEST = (pathlib.Path(__file__).resolve().parent / "escalator_fix_fixtures"
                      / "test_px17_scratch_r7d.py")


def _write_case_fixtures(worktree: pathlib.Path, case: Case) -> None:
    if case.id == "R7d":
        dest = worktree / "tests" / "csim" / "test_px17_scratch_r7d.py"
        dest.write_text(_SCRATCH_R7D_TEST.read_text())


def _apply_prereqs(repo: pathlib.Path, worktree: pathlib.Path, case: Case) -> None:
    """Storage prerequisites and pre-existing target-test fixtures the fence
    can't create (new files, new enum entries) -- applied once at setup,
    never authored by Gemini. Same class as R2/R7a's parent-patch
    precedent: the fence is a function, not the file or the header."""
    for rel_file in case.prereq_copy_from_human_fix:
        assert case.human_fix_commit, f"{case.id}: prereq_copy_from_human_fix needs human_fix_commit"
        text = _git(repo, "show", f"{case.human_fix_commit}:{rel_file}")
        dest = worktree / rel_file
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text + ("\n" if not text.endswith("\n") else ""))
    for rel_file, old, new in case.prereq_text_patches:
        path = worktree / rel_file
        text = path.read_text()
        if old not in text:
            raise RuntimeError(f"{case.id}: prereq patch text not found in {rel_file}: {old!r}")
        path.write_text(text.replace(old, new, 1))


def _run_agy_call(case: Case, model: str, worktree: pathlib.Path, targets: list[FenceTarget],
                   failing_output: str, previous_feedback: str | None, record: dict) -> dict[str, str]:
    """One escalator call for `targets` (a subset of case.fence). Returns
    {label: replacement_text}. Raises FenceViolation or AgyCallError."""
    current_texts = {}
    for t in targets:
        text = (worktree / t.file).read_text()
        span = splice.extract(text, symbol=t.symbol, lines=_resolve_lines(text, t), lang=t.lang())
        current_texts[t.label] = span.body

    prompt = build_prompt(case, targets, current_texts, failing_output, previous_feedback)
    payload, wall = call_escalator(model, prompt, timeout=300, transport=record.get("_transport"))
    record.setdefault("agy_calls", []).append({
        "targets": [t.label for t in targets], "wall_seconds": round(wall, 2),
        "rationale": payload.get("rationale", "")})

    functions = payload.get("functions", [])
    allowed = [t.label for t in targets]
    violations = check_fence(functions, allowed)
    if violations or len(functions) != len(allowed):
        raise FenceViolation(f"reply named {[f.get('name') for f in functions]}, "
                              f"fence allows only {allowed}")

    return {fn["name"]: fn["text"] for fn in functions}


def run_single_call_attempt(case: Case, model: str, worktree: pathlib.Path,
                             failing_output: str, previous_feedback: str | None,
                             record: dict) -> tuple[bool, dict]:
    targets = list(case.fence)
    originals_by_label = {}
    for t in targets:
        text = (worktree / t.file).read_text()
        span = splice.extract(text, symbol=t.symbol, lines=_resolve_lines(text, t), lang=t.lang())
        originals_by_label[t.label] = span.body

    new_texts = _run_agy_call(case, model, worktree, targets, failing_output, previous_feedback, record)
    diffs = apply_functions(worktree, targets, new_texts)
    record["diff"] = diffs
    return _gate_after_apply(case, worktree, record, originals_by_label, new_texts)


def run_sequential_attempt(case: Case, model: str, worktree: pathlib.Path,
                            failing_output: str, previous_feedback: str | None,
                            record: dict) -> tuple[bool, dict]:
    originals_by_label = {}
    new_texts: dict[str, str] = {}
    diffs: dict[str, str] = {}
    for t in case.fence:
        text = (worktree / t.file).read_text()
        span = splice.extract(text, symbol=t.symbol, lines=_resolve_lines(text, t), lang=t.lang())
        originals_by_label[t.label] = span.body

        one = _run_agy_call(case, model, worktree, [t], failing_output, previous_feedback, record)
        new_texts.update(one)
        diffs.update(apply_functions(worktree, [t], one))

        build = run_make(worktree)
        if not build.ok:
            record["diff"] = diffs
            return False, {"failed_gate": build.name, "feedback": build.detail}

    record["diff"] = diffs
    return _gate_after_apply(case, worktree, record, originals_by_label, new_texts)


def _gate_after_apply(case: Case, worktree: pathlib.Path, record: dict,
                       originals_by_label: dict[str, str], new_texts: dict[str, str]) -> tuple[bool, dict]:
    build = run_make(worktree)
    if not build.ok:
        return False, {"failed_gate": build.name, "feedback": build.detail}

    tt = target_tests_gate(worktree, case)
    if not tt.ok:
        return False, {"failed_gate": tt.name, "feedback": tt.detail}

    baseline = record["_baseline_failing"]
    reg, after_failing = regression_gate(worktree, baseline)
    record["failing_ids_after"] = sorted(after_failing)
    if not reg.ok:
        return False, {"failed_gate": reg.name, "feedback": reg.detail}

    ctx = {"originals_by_label": originals_by_label, "new_texts_by_label": new_texts,
           "stub_worktree": record.get("_stub_worktree"),
           "human_fix_worktree": record.get("_human_fix_worktree")}
    for gate_name in case.extra_gates:
        gate_fn = EXTRA_GATES[gate_name]
        result = gate_fn(worktree, case, ctx)
        record.setdefault("extra_gates", {})[gate_name] = result.detail
        if not result.ok:
            return False, {"failed_gate": result.name, "feedback": result.detail}

    return True, {}


def run_case(case_id: str, model: str, *, repo: pathlib.Path = REPO_ROOT,
             scratch_root: pathlib.Path, results_dir: pathlib.Path,
             max_attempts: int = 3, transport: str | None = None) -> dict:
    case = CASES[case_id]
    results_dir.mkdir(parents=True, exist_ok=True)
    pre_fix = resolve_pre_fix_commit(case, repo)

    worktree = scratch_root / f"{case_id}-{model}"
    stub_worktree = None
    human_fix_worktree = None
    made = []
    try:
        make_worktree(repo, pre_fix, worktree)
        made.append(worktree)
        _write_case_fixtures(worktree, case)
        _apply_prereqs(repo, worktree, case)

        if "red_at_stub" in case.extra_gates:
            # Unspliced, pristine copy of the pre-fix state: proves an
            # edited test is still red for the right reason, not vacuous.
            stub_worktree = scratch_root / f"{case_id}-{model}-stub"
            make_worktree(repo, pre_fix, stub_worktree)
            made.append(stub_worktree)
            run_make(stub_worktree)

        if case.reference_splice:
            apply_reference_splice(worktree, case.reference_splice)
            if case.human_fix_commit:
                # One-time harness precondition, not an attempt: the human
                # fix must itself pass against the same reference splice,
                # or the splice (not Gemini) is broken.
                human_fix_worktree = scratch_root / f"{case_id}-{model}-humanfix"
                make_worktree(repo, case.human_fix_commit, human_fix_worktree)
                made.append(human_fix_worktree)
                apply_reference_splice(human_fix_worktree, case.reference_splice)
                build = run_make(human_fix_worktree)
                if not build.ok:
                    raise RuntimeError(f"reference splice does not build against the human fix: {build.detail}")
                check = run_pytest(human_fix_worktree, list(case.target_tests))
                if not check.ok:
                    raise RuntimeError("reference splice is broken: the human fix itself fails against it:\n"
                                        + check.stdout[-3000:])

        run_make(worktree)
        baseline_failing = compute_suite_failing_ids(worktree)
        failing_output = run_pytest(worktree, list(case.target_tests)).stdout

        previous_feedback = None
        attempts_log = []
        verdict = "failed"
        for attempt_n in range(1, max_attempts + 1):
            record: dict = {"case": case_id, "model": model, "attempt": attempt_n,
                             "_baseline_failing": baseline_failing,
                             "_stub_worktree": stub_worktree, "_human_fix_worktree": human_fix_worktree,
                             "_transport": transport}
            try:
                if case.sequential:
                    ok, info = run_sequential_attempt(case, model, worktree, failing_output,
                                                       previous_feedback, record)
                else:
                    ok, info = run_single_call_attempt(case, model, worktree, failing_output,
                                                        previous_feedback, record)
            except FenceViolation as exc:
                record["gate_reached"] = "fence-violation"
                record["error"] = str(exc)
                _write_record(results_dir, record)
                verdict = "fence-violation"
                break
            except AgyCallError as exc:
                record["gate_reached"] = "agy-error"
                record["error"] = str(exc)
                previous_feedback = f"Your previous reply could not be used: {exc}"
                _write_record(results_dir, record)
                continue

            for key in ("_baseline_failing", "_stub_worktree", "_human_fix_worktree", "_transport"):
                record.pop(key, None)
            if ok:
                record["gate_reached"] = "done"
                _write_record(results_dir, record)
                verdict = "fixed-first-try" if attempt_n == 1 else "fixed-after-retry"
                break
            record["gate_reached"] = info["failed_gate"]
            record["gate_feedback"] = info["feedback"][:4000]
            _write_record(results_dir, record)
            previous_feedback = f"Gate '{info['failed_gate']}' failed:\n{info['feedback'][:3000]}"
            attempts_log.append(record)
        else:
            verdict = "failed"

        summary = {"case": case_id, "probe": case.probe, "model": model, "verdict": verdict,
                   "attempts_used": attempt_n, "pre_fix_commit": pre_fix}
        (results_dir / f"{case_id}__{_safe(model)}__verdict.json").write_text(json.dumps(summary, indent=2))
        return summary
    finally:
        for wt in made:
            remove_worktree(repo, wt)


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)


def _write_record(results_dir: pathlib.Path, record: dict) -> None:
    path = results_dir / f"{record['case']}__{_safe(record['model'])}__attempt{record['attempt']}.json"
    serializable = {k: v for k, v in record.items() if not k.startswith("_")}
    path.write_text(json.dumps(serializable, indent=2, default=str))


# =================================================================== cli ==

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("case_id", choices=sorted(CASES))
    run_p.add_argument("--model", required=True)
    run_p.add_argument("--scratch", default="/tmp/specfactory-escalator-probe")
    run_p.add_argument("--results", default=None)
    run_p.add_argument("--max-attempts", type=int, default=3)
    run_p.add_argument("--repo", default=str(REPO_ROOT))
    run_p.add_argument("--transport", choices=_TRANSPORTS, default=None,
                        help="override the by-model-name dispatch (api-deepseek, api-anthropic, agy)")
    run_p.add_argument("--dry-run", action="store_true",
                        help="print the resolved transport and model, make no model call, exit 0")
    args = parser.parse_args(argv)

    if args.cmd == "run":
        if args.dry_run:
            resolved = resolve_transport(args.transport, args.model)
            print(json.dumps({"case": args.case_id, "model": args.model, "transport": resolved}, indent=2))
            return 0
        scratch_root = pathlib.Path(args.scratch)
        results_dir = pathlib.Path(args.results) if args.results else scratch_root / "results"
        try:
            summary = run_case(args.case_id, args.model, repo=pathlib.Path(args.repo),
                                scratch_root=scratch_root, results_dir=results_dir,
                                max_attempts=args.max_attempts, transport=args.transport)
        except TransportUnavailable as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        print(json.dumps(summary, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
