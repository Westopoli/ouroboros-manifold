"""PX-13 prototype: flag three fixture-defect classes before any model call
touches a card (Factory section, docs/northstar/PLAN.md; DECISIONS.md fifth
round). Each detector is static AST-over-the-test-plus-C-step-order, or a
cheap arithmetic re-derivation of a control's own stated numbers -- neither
one runs the debug build.

The three real incidents this is built from (all in
docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md):

  R7h  tests/csim/controls/test_control_e05_agent_reads_live.py needs step
       3d to observe a step-3f mutation in the SAME tick. csrc/sim.c's
       om_world_step runs the whole 3d loop before 3f ever starts, so no
       build -- buggy or correct -- can make that observation differ. See
       tick_order_reachability().

  R7l  tests/csim/controls/test_control_e05_garrison_before_damage.py reuses
       numbers (military 20.0, damage -16.0, garrison 27.3) where
       military + damage = 4.0 never goes negative, so the correct order
       (clamp, then add garrison) and the buggy order (add garrison, then
       clamp the total) land on the same number. See
       branch_coverage_of_control().

  R7e  tests/csim/test_E05_S036_declared_or_sprung.py's
       test_R_036_05_with_probability_min_1_defend, Case 2 sub-block (fixed
       in d3273fa): the defender's own budget cleared its own attack
       viability bar, so it counter-declared the same tick and added a
       second, unrelated read_reinforces() record the fixture never
       anticipated -- confounding an aggregate `len(...) == 1` assertion.
       See two_agent_confound().

Each function's rule derivations (commit = 0.70 * budget, defense =
military * 0.55 * entrenchment, entrenchment 2.0 when held_since == -1) come
from docs/bible/epics/E-05-faction-agents-and-conflict.md's own R-035-01/02
worked examples -- not re-derived from csrc, which this task is read-only
on.
"""
from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_C = REPO_ROOT / "csrc" / "sim.c"

# ---------------------------------------------------------------- shared --

# Tick-step order, csrc/sim.c::om_world_step (read, never edited by this
# task). 3a is the budget snapshot memcpy -- not a hook call, so it never
# appears in tick_closure.hooks_in_order(), but it is still a real step
# other steps are compared against.
STEP_ORDER = ["3a", "3b", "3c", "3d", "3e", "3f", "4", "4.1"]


def _step_index(label: str | None) -> int | None:
    return STEP_ORDER.index(label) if label in STEP_ORDER else None


# Which E-05 tick step each conftest.py reader surfaces. Not derived from
# csrc (the buffer-to-hook ownership mapping needs hook bodies this task
# cannot read for every source file they might live in); taken from the E-05
# epic's own step call-outs: R-036-03 "resolves in step 3c", R-036-04
# "resolves ... in the same tick's step 3f", R-036-05/06 "step 3e", and the
# OM_BUG_E05 enum comments in ouroboros_sim.h for friction/admin. A reader
# added to conftest.py without an entry here just makes check 1 silently
# permissive for it -- see the report's limitations.
READER_STEP = {
    "read_candidates": "3d",
    "read_decisions": "3d",
    "read_telegraphs": "3c",
    "read_attacks": "3f",
    "read_collisions": "3f",
    "read_colonizations": "3f",
    "read_reinforces": "3e",
    "read_friction": "4",
    "read_admin_rolls": "4.1",
}


def _call_name(call: ast.Call) -> str | None:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _name_arg(call: ast.Call, idx: int) -> str | None:
    if idx < len(call.args) and isinstance(call.args[idx], ast.Name):
        return call.args[idx].id
    return None


def _literal(node: ast.AST | None):
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _calls_in_source_order(func: ast.FunctionDef) -> list[ast.Call]:
    calls = [n for n in ast.walk(func) if isinstance(n, ast.Call)]
    calls.sort(key=lambda c: (c.lineno, c.col_offset))
    return calls


def _test_functions(tree: ast.Module):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            yield node


# ------------------------------------------------------- check 1: order --

def _mode_of_inject_intent(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Attribute):
            return kw.value.attr
    if len(call.args) > 7 and isinstance(call.args[7], ast.Attribute):
        return call.args[7].attr
    # conftest.inject_intent's own default, per its signature
    # (..., mode=OMMode.SURPRISE)
    return "SURPRISE"


def _scan_function_for_order_violation(func: ast.FunctionDef) -> list[dict]:
    """A SURPRISE inject_intent() resolves through om_step_resolve (step
    3f) on the very next om_world_step() call for that same world variable
    (R-036-04: "resolves in the same tick's step 3f"; conftest's own
    docstring: "the faction then skips its own 3d decision this tick").
    If a read_* mapped to a step earlier than 3f is then read back with no
    further om_world_step() call in between, that read was produced by a
    hook that had already run, in this same tick, before 3f ever executed
    -- true for every build, buggy or correct, so the assertion cannot
    distinguish them. A TELEGRAPH-mode intent resolves ticks later (3c, a
    different call), so it never arms this check.
    """
    armed: dict[str, str | tuple] = {}
    findings: list[dict] = []
    for call in _calls_in_source_order(func):
        name = _call_name(call)
        if name == "inject_intent":
            wv = _name_arg(call, 1)
            if wv is None:
                continue
            mode = _mode_of_inject_intent(call)
            if mode == "SURPRISE":
                armed[wv] = "3f"
            elif mode == "TELEGRAPH":
                armed.pop(wv, None)
        elif name == "om_world_step":
            wv = _name_arg(call, 0)
            state = armed.get(wv)
            if state == "3f":
                armed[wv] = ("RESOLVED", "3f")
            elif isinstance(state, tuple):
                armed.pop(wv, None)  # a second tick has passed; order is fine now
        elif name in READER_STEP:
            wv = _name_arg(call, 1)
            state = armed.get(wv)
            if isinstance(state, tuple) and state[0] == "RESOLVED":
                mutator_step = state[1]
                reader_step = READER_STEP[name]
                if _step_index(reader_step) < _step_index(mutator_step):
                    findings.append({
                        "test": func.name,
                        "reader": name,
                        "reader_step": reader_step,
                        "mutator_step": mutator_step,
                        "world": wv,
                        "line": call.lineno,
                    })
                armed.pop(wv, None)
    return findings


def tick_order_reachability(control_file: str | Path) -> dict:
    """Flag UNSATISFIABLE_BY_ORDER when a control asks a reader mapped to
    tick step S to observe a same-tick SURPRISE-attack mutation that, per
    csrc/sim.c's own hooks_in_order(), cannot have happened yet by step S.
    """
    text = Path(control_file).read_text()
    tree = ast.parse(text)
    findings: list[dict] = []
    for func in _test_functions(tree):
        findings.extend(_scan_function_for_order_violation(func))
    if findings:
        return {"flag": "UNSATISFIABLE_BY_ORDER", "findings": findings}
    return {"flag": None, "findings": []}


# ----------------------------------------------------- check 2: vacuous --

BUG_ID_RE = re.compile(r"om_debug_inject\(\s*\w+\s*,\s*OMBugE05\.([A-Z_]+)\s*\)")

# Two-formula pairs for bug ids whose "ways this could be wrong" text names
# an explicit correct-order vs buggy-order pair. Only GARRISON_BEFORE_DAMAGE
# is populated (from ouroboros_sim.h's own comment, "Garrison added before
# damage, then destroyed by it.", and R-038-01's "post-damage military plus
# garrison"). Adding an entry here is what it costs to extend this check to
# another bug id -- it is not derived automatically from the enum comment,
# which never spells out the arithmetic, only the English shape of the bug.
FORMULA_TABLE = {
    "GARRISON_BEFORE_DAMAGE": {
        "correct": "max(0, m + d) + g",
        "buggy": "max(0, m + g + d)",
    },
}


def _eval_formula(expr: str, m: float, d: float, g: float) -> float:
    return eval(expr, {"__builtins__": {}}, {"max": max, "m": m, "d": d, "g": g})  # noqa: S307


def _extract_defender_military_and_delta(text: str) -> tuple[float | None, float | None]:
    num = r"-?\d+(?:\.\d+)?"
    m = re.search(rf"military\s+from\s+({num})\s+to\s+({num})", text)
    if not m:
        return None, None
    m_from, m_to = float(m.group(1)), float(m.group(2))
    return m_from, m_to - m_from


def _extract_garrison(text: str) -> float | None:
    # [\d.]+ on the final group would also happily eat a sentence-ending
    # period after the number ("= 27.3." -> "27.3."), so the last group is
    # a strict \d+\.\d+ (or a bare \d+) instead.
    num = r"\d+(?:\.\d+)?"
    m = re.search(rf"garrison\s*=\s*commit\s*\*\s*{num}\s*=\s*{num}\s*\*\s*{num}\s*=\s*({num})", text)
    if m:
        return float(m.group(1))
    m = re.search(rf"\.garrison\s*==\s*pytest\.approx\(({num})", text)
    if m:
        return float(m.group(1))
    return None


def _grid_search_distinguishing_military(formulas: dict, m_from: float, d: float, g: float,
                                          lo: float = 0.0, hi: float = 100.0, step: float = 1.0) -> float | None:
    best = None
    n = int((hi - lo) / step) + 1
    for i in range(n):
        cand = lo + i * step
        c = _eval_formula(formulas["correct"], cand, d, g)
        b = _eval_formula(formulas["buggy"], cand, d, g)
        if abs(c - b) > 1e-9 and (best is None or abs(cand - m_from) < abs(best - m_from)):
            best = cand
    return best


def branch_coverage_of_control(control_file: str | Path, reference_stub: str | Path | None = None) -> dict:
    """Flag VACUOUS_CONTROL when a control's own numbers make its stated
    correct-order and buggy-order formulas land on the same value, so no
    build can fail it. `reference_stub` is accepted for a future dynamic
    cross-check (compiling a tiny reference and comparing against the debug
    build) but unused here -- the docstring/comment extraction below was
    enough for every control this task had numbers to check against; see
    the report for what that leaves uncovered.
    """
    text = Path(control_file).read_text()
    bug_match = BUG_ID_RE.search(text)
    if not bug_match or bug_match.group(1) not in FORMULA_TABLE:
        return {"flag": None, "reason": "no two-formula table entry for this control's bug id"}
    formulas = FORMULA_TABLE[bug_match.group(1)]

    m_from, d = _extract_defender_military_and_delta(text)
    g = _extract_garrison(text)
    if m_from is None or d is None or g is None:
        return {"flag": None, "reason": "could not extract military/delta/garrison from the fixture"}

    correct_val = _eval_formula(formulas["correct"], m_from, d, g)
    buggy_val = _eval_formula(formulas["buggy"], m_from, d, g)
    if abs(correct_val - buggy_val) > 1e-9:
        return {"flag": None, "correct": correct_val, "buggy": buggy_val, "m": m_from, "d": d, "g": g}

    suggestion = _grid_search_distinguishing_military(formulas, m_from, d, g)
    return {
        "flag": "VACUOUS_CONTROL",
        "correct": correct_val,
        "buggy": buggy_val,
        "m": m_from, "d": d, "g": g,
        "suggested_military": suggestion,
    }


# ------------------------------------------------------ check 3: 2-agent --

def _rhs_kind(value: ast.AST) -> tuple | None:
    """Classify a read_*(...) right-hand side as ('call', reader, world)
    for an unfiltered direct call, or ('filtered', reader, world) for a
    list comprehension filtering that same call's result down to the
    entity under test -- the distinction two_agent_confound cares about."""
    if isinstance(value, ast.Call):
        name = _call_name(value)
        if name and name.startswith("read_"):
            return ("call", name, _name_arg(value, 1))
    if isinstance(value, ast.ListComp) and value.generators:
        it = value.generators[0].iter
        if isinstance(it, ast.Call):
            name = _call_name(it)
            if name and name.startswith("read_"):
                return ("filtered", name, _name_arg(it, 1))
    return None


def _collect_read_bindings(func: ast.FunctionDef) -> dict[str, tuple]:
    bindings: dict[str, tuple] = {}
    for stmt in ast.walk(func):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            kind = _rhs_kind(stmt.value)
            if kind:
                bindings[stmt.targets[0].id] = kind
    return bindings


def _unfiltered_len_read(test_expr: ast.AST, bindings: dict[str, tuple]) -> tuple[str | None, str | None]:
    if not isinstance(test_expr, ast.Compare):
        return None, None
    left = test_expr.left
    if not (isinstance(left, ast.Call) and _call_name(left) == "len" and len(left.args) == 1):
        return None, None
    arg = left.args[0]
    direct = _rhs_kind(arg)
    if direct and direct[0] == "call":
        return direct[1], direct[2]
    if isinstance(arg, ast.Name) and arg.id in bindings:
        kind, reader, wv = bindings[arg.id]
        if kind == "call":
            return reader, wv
    return None, None


def _collect_faction_and_region_info(func: ast.FunctionDef) -> tuple[dict, dict]:
    factions: dict[str, dict[int, dict]] = defaultdict(dict)
    regions: dict[str, dict[int, dict]] = defaultdict(dict)
    for call in _calls_in_source_order(func):
        name = _call_name(call)
        wv = _name_arg(call, 1)
        if wv is None:
            continue
        if name == "set_faction" and len(call.args) > 3:
            fid = _literal(call.args[2])
            arche = call.args[3].attr if isinstance(call.args[3], ast.Attribute) else None
            budget = None
            for kw in call.keywords:
                if kw.arg == "budget":
                    budget = _literal(kw.value)
            if fid is not None:
                info = factions[wv].setdefault(fid, {})
                info["archetype"] = arche
                info["budget"] = budget if budget is not None else 0.0
        elif name == "set_region":
            fid = military = None
            for kw in call.keywords:
                if kw.arg == "faction_id":
                    fid = _literal(kw.value)
                elif kw.arg == "military":
                    military = _literal(kw.value)
            if fid is not None and fid >= 0 and military is not None:
                regions[wv].setdefault(fid, {})["military"] = military
        elif name == "set_owner" and len(call.args) > 3:
            fid = _literal(call.args[3])
            held_since = None
            for kw in call.keywords:
                if kw.arg == "held_since":
                    held_since = _literal(kw.value)
            if fid is not None:
                regions[wv].setdefault(fid, {})["held_since"] = held_since if held_since is not None else -1
    return factions, regions


def two_agent_confound(test_file: str | Path, node_id: str) -> dict:
    """Flag TWO_AGENT_CONFOUND when a two-faction fixture gives the
    higher-faction-id agent (by this suite's own convention, faction 0 /
    region 0 is always the declared attacker's home and faction 1 / region 1
    the target -- see the docstring's Limitations note) enough budget to
    attack the lower-id faction's own region, and the assertion reads an
    aggregate length instead of filtering to the entity under test.

    Viability, from docs/bible/epics/E-05-faction-agents-and-conflict.md's
    own R-035-01/02: commit = 0.70 * budget; defense = target_military *
    0.55 * entrenchment (entrenchment 2.0 when held_since == -1, else
    approximated at 1.5 -- this suite's fixtures only ever use -1). Viable
    when commit - defense > 0. This is the same formula the real R7e
    incident (and its own fix, d3273fa) turned on.
    """
    text = Path(test_file).read_text()
    tree = ast.parse(text)
    func = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == node_id:
            func = node
            break
    if func is None:
        return {"flag": None, "reason": f"{node_id} not found in {test_file}"}

    factions, regions = _collect_faction_and_region_info(func)
    bindings = _collect_read_bindings(func)

    findings = []
    for stmt in ast.walk(func):
        if not isinstance(stmt, ast.Assert):
            continue
        reader, wv = _unfiltered_len_read(stmt.test, bindings)
        if reader is None:
            continue
        fset = factions.get(wv, {})
        rset = regions.get(wv, {})
        if len(fset) != 2:
            continue
        low_id, high_id = sorted(fset)
        high_info = fset[high_id]
        if high_info.get("archetype") == "DEFAULT":
            continue
        low_region = rset.get(low_id, {})
        mil = low_region.get("military")
        if mil is None:
            continue
        held_since = low_region.get("held_since", -1)
        entrenchment = 2.0 if held_since in (None, -1) else 1.5
        defense = mil * 0.55 * entrenchment
        commit = (high_info.get("budget") or 0.0) * 0.70
        net = commit - defense
        if net > 0:
            findings.append({
                "acting_faction": high_id, "archetype": high_info.get("archetype"),
                "budget": high_info.get("budget"), "commit": commit,
                "target_faction": low_id, "defense": defense, "net": net,
                "reader": reader, "world": wv, "assertion_line": stmt.lineno,
            })
    if findings:
        return {"flag": "TWO_AGENT_CONFOUND", "findings": findings}
    return {"flag": None, "findings": []}


# ---------------------------------------------------------------- sweep --

def sweep(project: Path = REPO_ROOT) -> dict:
    """Run all three checks over every tests/csim/controls/test_control_e05_*.py
    and tests/csim/test_E05_*.py file (check 3 against every test_* function
    in each E05 story file). Returns {path: [findings]}. Not a pytest entry
    point -- this is the report-generation sweep the PX-13 brief asks for."""
    out: dict[str, list[dict]] = {}
    controls_dir = project / "tests" / "csim" / "controls"
    csim_dir = project / "tests" / "csim"
    for path in sorted(controls_dir.glob("test_control_e05_*.py")):
        findings = []
        r1 = tick_order_reachability(path)
        if r1["flag"]:
            findings.append(("tick_order_reachability", r1))
        r2 = branch_coverage_of_control(path)
        if r2.get("flag"):
            findings.append(("branch_coverage_of_control", r2))
        text = path.read_text()
        tree = ast.parse(text)
        for func in _test_functions(tree):
            r3 = two_agent_confound(path, func.name)
            if r3.get("flag"):
                findings.append(("two_agent_confound", r3))
        if findings:
            out[str(path.relative_to(project))] = findings
    for path in sorted(csim_dir.glob("test_E05_*.py")):
        findings = []
        r1 = tick_order_reachability(path)
        if r1["flag"]:
            findings.append(("tick_order_reachability", r1))
        text = path.read_text()
        tree = ast.parse(text)
        for func in _test_functions(tree):
            r3 = two_agent_confound(path, func.name)
            if r3.get("flag"):
                findings.append(("two_agent_confound", r3))
        if findings:
            out[str(path.relative_to(project))] = findings
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(sweep(), indent=2, default=str))
