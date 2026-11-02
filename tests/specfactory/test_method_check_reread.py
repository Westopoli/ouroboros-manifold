# spec: docs/stories/H-062.md "Tests" (H-062 tests 1 to 8)
"""H-062 plan-reread-after-compaction: scripts/specfactory/method_check.py over synthetic transcripts.

Each test names its H-062 test number. The script is copied into a temp repo so its repo root (where it finds
docs/method/reading_list.toml and docs/northstar/ROADMAP.md) is the fixture, not this checkout (Architect ruling 1).
Positive controls (named *_control) pass on main today; the rest are red until the builder lands H-062.
"""
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_method_check as base  # noqa: E402  (module import only: its tests are not re-collected)

REPO = base.REPO
SONNET, FABLE = base.SONNET, base.FABLE
PLAN_LAB = "docs/northstar/plans/2026-10-31-lab-staircase.md"
PLAN_BETA = "docs/northstar/plans/2026-11-02-beta-staircase.md"
PLAN_OTHER = "docs/northstar/plans/2026-11-02-beta-dispatcher-context.md"
ARCH_DOC = "docs/method/architect.md"
RUN_DOC = "docs/method/runner.md"
ROADMAP = "docs/northstar/ROADMAP.md"
SENTENCE = ("this plan needs to be re-read, fully, because you are the architect and the plan execution depends on your "
            "ability to guide the dispatchers in their work and collaborate between them and help them when they get "
            "stuck. If you don't have full context of the plan, guesses will be made, and the output will not be what "
            "the plan file required, verifications will fail, and we'll waste time and effort on issues that could have "
            "been avoided.")
LISTS = {
    "architect": [ROADMAP, PLAN_BETA, PLAN_LAB, ARCH_DOC],
    "runner_lab": [RUN_DOC, ROADMAP, PLAN_LAB],
    "runner_beta": [RUN_DOC, ROADMAP, PLAN_BETA, PLAN_OTHER],
}
ROADMAP_TEXT = f"""# Roadmap

## 1. Now building

Plan file `{PLAN_LAB}` runs the lab; the beta plan is `plans/2026-11-02-beta-staircase.md`.

| Staircase | Story |
|---|---|
| lab | H-040 |

## 2. The beta critical path

Not section 1: `{PLAN_OTHER}` is only named here.
"""
MUTATING = {
    "Edit": ("Edit", {"file_path": "{r}/notes.md", "old_string": "a", "new_string": "b"}),
    "Write": ("Write", {"file_path": "{r}/notes.md", "content": "x"}),
    "Bash": ("Bash", {"command": "touch {r}/marker"}),
    "Agent": ("Agent", {"prompt": "do a thing", "subagent_type": "doer"}),
    "SendMessage": ("SendMessage", {"to": "someone", "message": "hi"}),
}


def make_repo(tmp_path, lists=LISTS, match=("beta", "7f"), roadmap=ROADMAP_TEXT):
    root = tmp_path / "repo"
    (root / "scripts" / "specfactory").mkdir(parents=True)
    shutil.copy(base.SCRIPT, root / "scripts" / "specfactory" / "method_check.py")
    (root / "docs" / "northstar").mkdir(parents=True)
    (root / "docs" / "method").mkdir(parents=True)
    (root / ROADMAP).write_text(roadmap)
    if lists is not None:
        t = ""
        for table, files in lists.items():
            t += f"[{table}]\nfiles = {json.dumps(files)}\n"
            if table == "runner_beta":
                t += f"match = {json.dumps(list(match))}\n"
        (root / "docs" / "method" / "reading_list.toml").write_text(t)
    return root


def call(root, spec):
    n, inp = spec
    return (n, {k: v.format(r=root) if isinstance(v, str) else v for k, v in inp.items()})


def read(root, rel):
    return ("Read", {"file_path": str(root / rel)})


def turn(root, model, tools=(), ctx=60000):
    return base.assistant(model, tools=list(tools), ctx=ctx, cwd=str(root))


def named(name, key="agent-name"):
    if key == "custom-title":
        return {"type": "custom-title", "customTitle": name, "sessionId": "abc"}
    return {"type": "agent-name", "agentName": name, "sessionId": "abc"}


def go(tmp_path, root, entries, stdin_mode=False):
    t = base.write_transcript(tmp_path, entries)
    args = [sys.executable, str(root / "scripts" / "specfactory" / "method_check.py"),
            "--live-checkout", str(tmp_path / "live")]
    if stdin_mode:
        r = subprocess.run(args, input=json.dumps({"transcript_path": str(t), "session_id": "abc"}),
                           capture_output=True, text=True, timeout=60)
    else:
        r = subprocess.run(args + ["--transcript", str(t)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def reread_block(out):
    """The `METHOD plan_reread` line and its indented detail lines, or None when the check is absent."""
    lines = out.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("METHOD plan_reread "):
            j = i + 1
            while j < len(lines) and lines[j].startswith(" "):
                j += 1
            return "\n".join(lines[i:j])
    return None


def reread_verdict(out):
    b = reread_block(out)
    assert b is not None, f"no 'METHOD plan_reread' line (check not built) in:\n{out}"
    return re.match(r"METHOD plan_reread (OK|DRIFT)", b).group(1)


def after_compaction(root, model, first_tools, session="lab-runner", pre=()):
    """pre-marker turns, the compaction marker, then one turn per element of first_tools."""
    return [named(session), turn(root, model), *pre, base.compact()] + [turn(root, model, [t]) for t in first_tools]


# ---- H-062 test 1: plan_reread -------------------------------------------------------------------------------

def test_h062_t1_control_harness_runs_copied_script(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [named("lab-runner"), turn(root, SONNET), base.compact(), turn(root, SONNET)])
    assert base.verdict(out) == "OK"  # control: copy-into-temp-repo harness works on main


@pytest.mark.parametrize("tool", sorted(MUTATING))
def test_h062_t1_mutation_before_reread_is_drift(tmp_path, tool):
    root = make_repo(tmp_path)
    reads = [read(root, f) for f in LISTS["runner_lab"]]
    out = go(tmp_path, root, after_compaction(root, SONNET, [call(root, MUTATING[tool])] + reads))
    assert reread_verdict(out) == "DRIFT"
    blk = reread_block(out)
    for f in LISTS["runner_lab"]:
        assert f in blk, f"unread file {f} not named:\n{blk}"
    assert base.verdict(out) == "DRIFT"


def test_h062_t1_names_only_the_still_unread_files(tmp_path):
    root = make_repo(tmp_path)
    ents = after_compaction(root, SONNET, [read(root, RUN_DOC), call(root, MUTATING["Edit"])])
    blk = reread_block(go(tmp_path, root, ents))
    assert blk and blk.startswith("METHOD plan_reread DRIFT"), blk
    assert PLAN_LAB in blk and RUN_DOC not in blk


@pytest.mark.parametrize("tool", sorted(MUTATING))
def test_h062_t1_control_read_first_no_drift(tmp_path, tool):
    root = make_repo(tmp_path)
    reads = [read(root, f) for f in LISTS["runner_lab"]]
    out = go(tmp_path, root, after_compaction(root, SONNET, reads + [call(root, MUTATING[tool])]))
    assert "METHOD plan_reread DRIFT" not in out  # control: green on main by absence, stays green when built


def test_h062_t1_cat_reader_counts_as_a_read(tmp_path):
    root = make_repo(tmp_path)
    reads = [("Bash", {"command": f"cat {root / f}"}) for f in LISTS["runner_lab"]]
    out = go(tmp_path, root, after_compaction(root, SONNET, reads + [call(root, MUTATING["Edit"])]))
    assert reread_verdict(out) == "OK"


def test_h062_t1_mutation_before_the_marker_is_not_blamed(tmp_path):
    root = make_repo(tmp_path)
    reads = [read(root, f) for f in LISTS["runner_lab"]]
    pre = [turn(root, SONNET, [call(root, MUTATING["Edit"])])]
    out = go(tmp_path, root, after_compaction(root, SONNET, reads, pre=pre))
    assert reread_verdict(out) == "OK"


# ---- H-062 test 2: beta vs lab lists -------------------------------------------------------------------------

def read_only(root, files, mutate=True, session="x", key="agent-name", model=SONNET):
    ents = [named(session, key), turn(root, model), base.compact()]
    ents += [turn(root, model, [read(root, f)]) for f in files]
    if mutate:
        ents.append(turn(root, model, [call(root, MUTATING["Edit"])]))
    return ents


def test_h062_t2_control_runner_named_beta_clean_when_all_read(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, read_only(root, LISTS["runner_beta"], session="ouroboros-manifold-beta"))
    assert "METHOD plan_reread DRIFT" not in out  # control: absent on main, must stay absent when built


@pytest.mark.parametrize("key", ["agent-name", "custom-title"])
def test_h062_t2_beta_runner_held_to_beta_list_not_lab(tmp_path, key):
    root = make_repo(tmp_path)
    # read the whole LAB list only: the beta runner still owes the beta-only files, not the lab-only one
    blk = reread_block(go(tmp_path, root, read_only(root, LISTS["runner_lab"], session="ouroboros-manifold-beta", key=key)))
    assert blk and blk.startswith("METHOD plan_reread DRIFT"), blk
    assert PLAN_BETA in blk and PLAN_OTHER in blk
    assert PLAN_LAB not in blk  # cross-blame: lab file never charged to a beta runner


@pytest.mark.parametrize("name", ["ouroboros-manifold-lab", "ouroboros-manifold-90", ""])
def test_h062_t2_lab_runner_held_to_lab_list_not_beta(tmp_path, name):
    root = make_repo(tmp_path)
    ents = read_only(root, [RUN_DOC, ROADMAP, PLAN_BETA, PLAN_OTHER], session=name)  # all beta files, no lab plan
    blk = reread_block(go(tmp_path, root, ents))
    assert blk and blk.startswith("METHOD plan_reread DRIFT"), blk
    assert PLAN_LAB in blk
    assert PLAN_BETA not in blk and PLAN_OTHER not in blk


def test_h062_t2_runner_named_7f_is_held_to_beta_list(tmp_path):
    root = make_repo(tmp_path)
    blk = reread_block(go(tmp_path, root, read_only(root, LISTS["runner_lab"], session="ouroboros-manifold-7f")))
    assert blk and blk.startswith("METHOD plan_reread DRIFT"), blk
    assert PLAN_BETA in blk and PLAN_OTHER in blk and PLAN_LAB not in blk


def test_h062_t2_architect_named_beta_still_gets_architect_list(tmp_path):
    root = make_repo(tmp_path)
    ents = read_only(root, LISTS["architect"], session="beta-staircase-gate-channel", model=FABLE)
    out = go(tmp_path, root, ents)
    assert reread_verdict(out) == "OK"  # held to the architect list (all read), not the beta runner list
    first = out.splitlines()[0]
    assert first.startswith("METHOD read first:") and ARCH_DOC in first and RUN_DOC not in first


# ---- H-062 test 3: hook output -------------------------------------------------------------------------------

def test_h062_t3_control_role_header_present(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [named("a"), turn(root, FABLE), base.compact(), turn(root, FABLE)], stdin_mode=True)
    assert any(l.startswith("METHOD role architect") for l in out.splitlines())  # control, green on main


def test_h062_t3_read_first_line_precedes_role_header(tmp_path):
    root = make_repo(tmp_path)
    for name, model, key in (("lab-runner", SONNET, "runner_lab"), ("ouroboros-manifold-beta", SONNET, "runner_beta"),
                             ("architect-chat", FABLE, "architect")):
        out = go(tmp_path, root, [named(name), turn(root, model), base.compact(), turn(root, model)], stdin_mode=True)
        lines = out.splitlines()
        assert lines[0].startswith("METHOD read first:"), f"{name}: first line is {lines[0]!r}"
        for f in LISTS[key]:
            assert f in lines[0], f"{name}: {f} missing from {lines[0]!r}"
        other = set().union(*(LISTS[k] for k in LISTS if k != key)) - set(LISTS[key])
        for f in other:
            assert f not in lines[0], f"{name}: foreign file {f} on the read-first line"
        assert next(i for i, l in enumerate(lines) if l.startswith("METHOD role")) > 0


def test_h062_t3_architect_gets_one_paragraph_per_plan_named_in_section_1(tmp_path):
    root = make_repo(tmp_path, lists={**LISTS, "architect": LISTS["architect"] + [PLAN_OTHER]})
    out = go(tmp_path, root, [named("arch"), turn(root, FABLE), base.compact(), turn(root, FABLE)], stdin_mode=True)
    lines = out.splitlines()
    assert lines[0].startswith("METHOD read first:")
    assert out.count("PLAN RE-READ ") == 2, out  # lab plan (full path) and beta plan (plans/<name> suffix)
    for p in (PLAN_LAB, PLAN_BETA):
        assert f"PLAN RE-READ {p}: {SENTENCE}" in out
    assert f"PLAN RE-READ {PLAN_OTHER}" not in out  # in the list but named only in section 2
    assert min(i for i, l in enumerate(lines) if l.startswith("PLAN RE-READ")) > 0
    assert any(l.startswith("METHOD next:") for l in lines)  # NEXT keeps its place


def test_h062_t3_runner_gets_no_plan_paragraph(tmp_path):
    root = make_repo(tmp_path)
    for name in ("lab-runner", "ouroboros-manifold-beta"):
        out = go(tmp_path, root, [named(name), turn(root, SONNET), base.compact(), turn(root, SONNET)], stdin_mode=True)
        assert out.startswith("METHOD read first:"), out
        assert "PLAN RE-READ" not in out


# ---- H-062 test 4: context rule ------------------------------------------------------------------------------

def ctx_line(out):
    return next(l for l in out.splitlines() if l.startswith("METHOD context "))


def test_h062_t4_control_clean_context(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [turn(root, FABLE, ctx=300000), turn(root, FABLE, ctx=310000)])
    assert base.checks(out)["context"][0] == "OK"  # control, green on main


def test_h062_t4_405k_with_a_compaction_since_is_not_drift(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [turn(root, FABLE, ctx=405000), base.compact(), turn(root, FABLE, ctx=40000)])
    assert base.checks(out)["context"][0] == "OK"
    assert "Compaction at 400k is the only context rule" in ctx_line(out)  # red on main: the old rule text


def test_h062_t4_470k_without_a_compaction_is_drift(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [turn(root, FABLE, ctx=300000), turn(root, FABLE, ctx=470000)])
    assert base.checks(out)["context"][0] == "DRIFT"  # control half: green on main
    assert "a turn past 400k without a compaction is drift (docs/method/architect.md)" in ctx_line(out)  # red on main
    assert "Restart from memory" not in ctx_line(out)


# ---- H-062 test 5: model switch ------------------------------------------------------------------------------

def test_h062_t5_control_all_fable_is_architect_with_code_edits(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [turn(root, FABLE, [("Write", {"file_path": f"{root}/x.py", "content": "1"})])])
    assert out.count("METHOD role architect") == 1 and base.checks(out)["code_edits"][0] == "DRIFT"  # control


def test_h062_t5_fable_first_then_sonnet_keeps_architect_role(tmp_path):
    root = make_repo(tmp_path)
    ents = [turn(root, FABLE), turn(root, SONNET, [("Write", {"file_path": f"{root}/x.py", "content": "1"})]),
            turn(root, SONNET)]
    out = go(tmp_path, root, ents)
    assert "METHOD role architect" in out
    assert base.checks(out)["code_edits"][0] == "DRIFT"  # the Fable-only rule still applies


def test_h062_t5_sonnet_first_stays_runner_even_after_fable_turn(tmp_path):
    root = make_repo(tmp_path)
    out = go(tmp_path, root, [turn(root, SONNET), turn(root, FABLE), turn(root, FABLE)])
    assert "METHOD role runner" in out and "code_edits" not in base.checks(out)


# ---- H-062 test 7: missing reading list ----------------------------------------------------------------------

def test_h062_t7_missing_list_prints_none_and_no_drift(tmp_path):
    root = make_repo(tmp_path, lists=None)
    assert not (root / "docs" / "method" / "reading_list.toml").exists()
    out = go(tmp_path, root, after_compaction(root, SONNET, [call(root, MUTATING["Edit"])]), stdin_mode=True)
    assert out.splitlines()[0] == "METHOD read first: NONE (docs/method/reading_list.toml missing)", out.splitlines()[0]
    assert "METHOD plan_reread DRIFT" not in out
    assert "PLAN RE-READ" not in out
    assert "METHOD error" not in out
    assert base.verdict(out) == "OK"


# ---- H-062 test 8: the real reading list ---------------------------------------------------------------------

def test_h062_t8_real_reading_list_has_three_tables_and_match():
    p = REPO / "docs" / "method" / "reading_list.toml"
    assert p.exists(), "docs/method/reading_list.toml missing (the builder lands it)"
    d = tomllib.loads(p.read_text())
    for table in ("architect", "runner_lab", "runner_beta"):
        assert isinstance(d.get(table, {}).get("files"), list) and d[table]["files"], table
    assert d["runner_beta"]["match"] == ["beta", "7f"]
    assert {ROADMAP, PLAN_BETA, PLAN_LAB, ARCH_DOC} <= set(d["architect"]["files"])
    assert PLAN_OTHER in d["runner_beta"]["files"] and PLAN_OTHER not in d["runner_lab"]["files"]
    assert PLAN_LAB in d["runner_lab"]["files"] and PLAN_BETA in d["runner_beta"]["files"]
