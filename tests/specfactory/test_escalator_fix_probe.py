"""Tests for scripts/specfactory/escalator_fix_probe.py (PX-17/PX-18 handoff
brief). Exercises the pure engine logic -- fence checking, splice
application, the no-worse suite comparison, and the retry feedback loop --
against a fake `agy` runner and synthetic C/Python source files. Never
shells out to the real agy CLI or builds the real C library.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "specfactory"))
import escalator_fix_probe as efp  # noqa: E402


# ---------------------------------------------------------------- fixtures --

def _fake_agy_run(*, functions, rationale="ok", returncode=0, stdout_override=None):
    """Builds a RUN_AGY-compatible fake returning a canned envelope, the
    same shape agy prints under --output-format json (the model's answer
    lives in the "response" field, per agy_json.payload_from_envelope)."""
    import json as _json

    class _Result:
        pass

    def _run(argv, *, env, timeout):
        r = _Result()
        r.returncode = returncode
        if stdout_override is not None:
            r.stdout = stdout_override
        else:
            r.stdout = _json.dumps({"response": {"functions": functions, "rationale": rationale}})
        r.stderr = ""
        return r

    return _run


# ------------------------------------------------------------- call_gemini --

def test_call_gemini_parses_canned_reply(monkeypatch):
    monkeypatch.setattr(efp, "RUN_AGY", _fake_agy_run(
        functions=[{"name": "om_step_decisions", "text": "void om_step_decisions(om_world *w) { (void)w; }\n"}],
        rationale="added the forced-queue check"))
    payload, wall = efp.call_gemini("gemini-3.7-flash-high", "some prompt", timeout=5)
    assert payload["rationale"] == "added the forced-queue check"
    assert payload["functions"][0]["name"] == "om_step_decisions"
    assert wall >= 0


def test_call_gemini_raises_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(efp, "RUN_AGY", _fake_agy_run(functions=[], returncode=2))
    with pytest.raises(efp.AgyCallError):
        efp.call_gemini("gemini-3.7-flash-high", "prompt", timeout=5)


def test_call_gemini_raises_on_schema_mismatch(monkeypatch):
    monkeypatch.setattr(efp, "RUN_AGY", _fake_agy_run(functions=[], stdout_override="not json at all"))
    with pytest.raises(efp.AgyCallError):
        efp.call_gemini("gemini-3.7-flash-high", "prompt", timeout=5)


def test_call_deepseek_parses_canned_reply(monkeypatch):
    calls = {}

    def fake_chat_json(model, system, user, **kwargs):
        calls["model"] = model
        calls["kwargs"] = kwargs
        return {"functions": [{"name": "om_step_reinforce", "text": "void om_step_reinforce(om_world *w) {}\n"}],
                "rationale": "deepseek reply"}

    monkeypatch.setattr(efp, "DEEPSEEK_CHAT_JSON", fake_chat_json)
    payload, wall = efp.call_deepseek("deepseek-v4-flash", "some prompt", timeout=5)
    assert payload["rationale"] == "deepseek reply"
    assert calls["model"] == "deepseek-v4-flash"
    assert calls["kwargs"]["campaign"] == efp.DEEPSEEK_CAMPAIGN
    assert wall >= 0


def test_call_deepseek_raises_on_schema_mismatch(monkeypatch):
    monkeypatch.setattr(efp, "DEEPSEEK_CHAT_JSON", lambda *a, **k: {"not": "the schema"})
    with pytest.raises(efp.AgyCallError):
        efp.call_deepseek("deepseek-v4-flash", "prompt", timeout=5)


def test_call_deepseek_wraps_underlying_exception(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("budget exceeded")

    monkeypatch.setattr(efp, "DEEPSEEK_CHAT_JSON", boom)
    with pytest.raises(efp.AgyCallError):
        efp.call_deepseek("deepseek-v4-flash", "prompt", timeout=5)


def test_call_escalator_dispatches_by_model_name(monkeypatch):
    seen = []
    monkeypatch.setattr(efp, "call_gemini", lambda model, prompt, **kw: (seen.append(("gemini", model)), ({}, 0.0))[1])
    monkeypatch.setattr(efp, "call_deepseek", lambda model, prompt, **kw: (seen.append(("deepseek", model)), ({}, 0.0))[1])

    efp.call_escalator("deepseek-v4-flash", "prompt")
    efp.call_escalator("gemini-3.7-flash-high", "prompt")
    assert seen == [("deepseek", "deepseek-v4-flash"), ("gemini", "gemini-3.7-flash-high")]


def test_call_gemini_builds_the_documented_argv(monkeypatch):
    captured = {}

    def _run(argv, *, env, timeout):
        captured["argv"] = argv
        captured["timeout"] = timeout
        import json as _json
        from types import SimpleNamespace
        return SimpleNamespace(returncode=0, stdout=_json.dumps(
            {"functions": [{"name": "f", "text": "f(){}\n"}], "rationale": "r"}), stderr="")

    monkeypatch.setattr(efp, "RUN_AGY", _run)
    efp.call_gemini("gemini-3.1-pro-high", "PROMPT TEXT", timeout=300)
    argv = captured["argv"]
    assert argv[0] == efp.AGY_BIN
    assert argv[argv.index("--model") + 1] == "gemini-3.1-pro-high"
    assert argv[argv.index("--prompt") + 1] == "PROMPT TEXT"
    assert "--output-format" in argv and argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--json-schema") + 1] == str(efp.SCHEMA_PATH)
    assert "--dangerously-skip-permissions" in argv
    assert "--sandbox" in argv
    assert captured["timeout"] == 300


# ---------------------------------------------------------------- fence ----

def test_check_fence_accepts_exact_match():
    functions = [{"name": "om_step_decisions", "text": "..."}]
    assert efp.check_fence(functions, ["om_step_decisions"]) == []


def test_check_fence_rejects_name_outside_fence():
    functions = [{"name": "om_step_resolve", "text": "..."}]  # not the fenced function
    violations = efp.check_fence(functions, ["om_step_decisions"])
    assert violations == ["om_step_resolve"]


def test_check_fence_rejects_duplicate_of_an_allowed_name():
    functions = [{"name": "f", "text": "a"}, {"name": "f", "text": "b"}]
    violations = efp.check_fence(functions, ["f"])
    assert violations == ["f"]


def test_check_fence_partial_violation_among_several_targets():
    functions = [{"name": "om_step_decisions", "text": "..."}, {"name": "sneaky_extra_fn", "text": "..."}]
    violations = efp.check_fence(functions, ["om_step_decisions", "om_intent_inject"])
    assert violations == ["sneaky_extra_fn"]


# ------------------------------------------------------------ apply/splice --

_C_FILE = """\
int om_untouched(int x) {
    return x + 1;
}

int om_step_decisions(int y) {
    return y - 1;
}

int om_also_untouched(int z) {
    return z * 2;
}
"""

_PY_FILE = '''\
def test_untouched():
    assert 1 == 1


def test_R_036_05_with_probability_min_1_defend():
    assert False, "original"


def test_also_untouched():
    assert 2 == 2
'''


def test_apply_functions_splices_only_the_named_c_function(tmp_path):
    (tmp_path / "csrc").mkdir()
    f = tmp_path / "csrc" / "agent.c"
    f.write_text(_C_FILE)
    target = efp.FenceTarget(file="csrc/agent.c", label="om_step_decisions", symbol="om_step_decisions")

    efp.apply_functions(tmp_path, [target], {"om_step_decisions": "int om_step_decisions(int y) {\n    return y + 999;\n}\n"})

    out = f.read_text()
    assert "return y + 999;" in out
    assert "return x + 1;" in out  # untouched neighbor above
    assert "return z * 2;" in out  # untouched neighbor below


def test_apply_functions_splices_only_the_named_python_function(tmp_path):
    (tmp_path / "tests").mkdir()
    f = tmp_path / "tests" / "test_thing.py"
    f.write_text(_PY_FILE)
    target = efp.FenceTarget(file="tests/test_thing.py",
                              label="test_R_036_05_with_probability_min_1_defend",
                              symbol="test_R_036_05_with_probability_min_1_defend")

    efp.apply_functions(tmp_path, [target], {
        "test_R_036_05_with_probability_min_1_defend": "def test_R_036_05_with_probability_min_1_defend():\n    assert True\n"})

    out = f.read_text()
    assert "def test_R_036_05_with_probability_min_1_defend():\n    assert True" in out
    assert "def test_untouched():\n    assert 1 == 1" in out
    assert "def test_also_untouched():\n    assert 2 == 2" in out
    assert '"original"' not in out


def test_apply_functions_two_targets_same_file_reverse_order_safe(tmp_path):
    """Regression for the reverse-line-order requirement: replacing the
    earlier function with a longer body must not shift the later
    function's span out from under it."""
    (tmp_path / "tests").mkdir()
    f = tmp_path / "tests" / "test_thing.py"
    f.write_text(_PY_FILE)
    t1 = efp.FenceTarget(file="tests/test_thing.py", label="a", symbol="test_untouched")
    t2 = efp.FenceTarget(file="tests/test_thing.py", label="b",
                          symbol="test_R_036_05_with_probability_min_1_defend")

    efp.apply_functions(tmp_path, [t1, t2], {
        "a": "def test_untouched():\n    assert 1 == 1\n    assert 2 == 2\n    assert 3 == 3\n",
        "b": "def test_R_036_05_with_probability_min_1_defend():\n    assert True\n",
    })

    out = f.read_text()
    assert "assert 3 == 3" in out  # the earlier, now-longer function
    assert "def test_R_036_05_with_probability_min_1_defend():\n    assert True" in out
    assert "def test_also_untouched():\n    assert 2 == 2" in out  # never touched


def test_restore_files_reverts_to_original(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("original\n")
    originals = {"x.py": "original\n"}
    f.write_text("mutated\n")
    efp.restore_files(tmp_path, originals)
    assert f.read_text() == "original\n"


# ------------------------------------------------------------ no-worse -----

def test_no_worse_true_when_after_is_subset_of_before():
    before = {"a", "b", "c"}
    after = {"b"}
    ok, new = efp.no_worse(before, after)
    assert ok is True
    assert new == set()


def test_no_worse_false_when_a_new_failure_appears():
    before = {"a", "b"}
    after = {"a", "b", "c"}
    ok, new = efp.no_worse(before, after)
    assert ok is False
    assert new == {"c"}


def test_no_worse_true_on_identical_sets():
    s = {"a", "b"}
    ok, new = efp.no_worse(s, set(s))
    assert ok is True
    assert new == set()


# --------------------------------------------------------- assert shapes --

def test_assertions_preserved_gate_passes_when_all_original_asserts_survive():
    old = "def f():\n    assert x == 1\n    assert y == 2\n"
    new = "def f():\n    assert y == 2\n    assert x == 1\n    assert z == 3\n"  # reordered + one added
    assert efp._assert_shapes(old) <= efp._assert_shapes(new)


def test_assertions_preserved_gate_catches_a_dropped_assertion():
    old = "def f():\n    assert x == 1\n    assert y == 2\n"
    new = "def f():\n    assert x == 1\n"  # y == 2 silently dropped
    missing = efp._assert_shapes(old) - efp._assert_shapes(new)
    assert missing  # non-empty: the drop must be detected


# --------------------------------------------------------------- retry ----

def test_build_prompt_includes_previous_feedback_only_on_retry():
    case = efp.CASES["R7d"]
    targets = list(case.fence)
    texts = {targets[0].label: "void om_step_decisions(om_world *w) { /* body */ }\n"}
    p1 = efp.build_prompt(case, targets, texts, "FAILED test_x", previous_feedback=None)
    assert "Previous attempt failed" not in p1

    p2 = efp.build_prompt(case, targets, texts, "FAILED test_x",
                           previous_feedback="Gate 'target_tests' failed:\nsome pytest output")
    assert "Previous attempt failed" in p2
    assert "some pytest output" in p2


def test_run_single_call_attempt_feeds_gate_failure_back_as_prompt_text(tmp_path, monkeypatch):
    """A fake case with a trivial C fence: first agy reply makes the build
    fail; the harness must retry-eligible-feedback the compiler output.
    Exercises the real _run_agy_call -> apply_functions -> gate wiring
    without a real repo checkout or the real C library."""
    (tmp_path / "csrc").mkdir()
    (tmp_path / "csrc" / "thing.c").write_text(
        "int om_thing(int x) {\n    return x + 1;\n}\n")

    target = efp.FenceTarget(file="csrc/thing.c", label="om_thing", symbol="om_thing")
    case = efp.Case(id="FAKE", probe="PX-17", pre_fix_commit="deadbeef", human_fix_commit=None,
                     fence=(target,), diagnosis="synthetic case for the retry-feedback test",
                     contract_quote="", target_tests=("tests/fake_test.py",))

    replies = iter([
        [{"name": "om_thing", "text": "int om_thing(int x) {\n    this is not valid C\n}\n"}],
        [{"name": "om_thing", "text": "int om_thing(int x) {\n    return x + 2;\n}\n"}],
    ])
    prompts_seen = []

    def fake_run_agy_call(case_, model, worktree, targets_, failing_output, previous_feedback, record):
        prompts_seen.append(previous_feedback)
        reply_functions = next(replies)
        return {fn["name"]: fn["text"] for fn in reply_functions}

    monkeypatch.setattr(efp, "_run_agy_call", fake_run_agy_call)

    def fake_run_make(worktree, **kw):
        src = (worktree / "csrc" / "thing.c").read_text()
        if "this is not valid C" in src:
            return efp.GateResult(False, "build", "gcc error: expected expression")
        return efp.GateResult(True, "build", "build ok")

    monkeypatch.setattr(efp, "run_make", fake_run_make)
    monkeypatch.setattr(efp, "target_tests_gate", lambda wt, c: efp.GateResult(True, "target_tests", "ok"))
    monkeypatch.setattr(efp, "regression_gate", lambda wt, baseline: (efp.GateResult(True, "regression", "ok"), set()))

    record1 = {"case": "FAKE", "model": "fake-model", "attempt": 1, "_baseline_failing": set()}
    ok1, info1 = efp.run_single_call_attempt(case, "fake-model", tmp_path, "no failing output",
                                              None, record1)
    assert ok1 is False
    assert info1["failed_gate"] == "build"
    assert "gcc error" in info1["failed_gate"] or "gcc error" in info1["feedback"]

    feedback = f"Gate '{info1['failed_gate']}' failed:\n{info1['feedback']}"
    record2 = {"case": "FAKE", "model": "fake-model", "attempt": 2, "_baseline_failing": set()}
    ok2, info2 = efp.run_single_call_attempt(case, "fake-model", tmp_path, "no failing output",
                                              feedback, record2)
    assert ok2 is True
    assert prompts_seen[0] is None
    assert prompts_seen[1] == feedback
    assert (tmp_path / "csrc" / "thing.c").read_text().strip() == "int om_thing(int x) {\n    return x + 2;\n}".strip()
