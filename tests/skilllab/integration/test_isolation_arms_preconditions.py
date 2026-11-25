# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 1 (preconditions 1 to 8) and section 8 ("Still his, all `DRAFT-` in the code"); CLAUDE.md "Westley owns every threshold and tolerance"
"""LI3 preconditions on the module itself: no cell, no run (a second each; the module is read as source and as constants).

R1 the scan is his: 16 against 8 to 48 (README 4: "scanned over 8 to 48 against 16"), the default heads are every headcount; the mirror is 16 v 16.
R2 every numeric constant the module defines is named and on a line that says `DRAFT-` (a number nobody gave) or `Westley` / `README` (a number he gave); no name says threshold, tolerance or pass mark.
R3 never a second click: the module issues no order and imports no engine (the lab's one order per side is the only order); a fight that stalls is a finding about the units, not a reason to add one (DEC-one-click-2026-11-18).
R4 flags are signals, never verdicts: a flag is a name from a closed list; there is no key, function or constant that is a pass mark; no single headcount is a verdict (`part_word_m` reads direction in every cell, not one number).
R5 the module is new code in a new file behind the runner and the measures; it changes neither (the interface of LI1 and LI2 is theirs)."""
import ast
import re
import subprocess

import isolation_arms_fixtures as af
import isolation_fixtures as fx

LI3_BASE = "ace81d52e37101588eea55ffd681d0c64ef6d03b"   # the merge of LI2 into the LI1 build: the tree this piece starts from
SRC = fx.ROOT / "scripts" / "skilllab" / "arena" / "isolation_arms.py"


def test_r1_the_scan_is_westleys_sixteen_against_eight_to_forty_eight():
    a = af.arms()
    assert (a.OWN_HEADS, a.SCAN_FROM, a.SCAN_TO) == (16, 8, 48)
    assert tuple(a.SCAN_HEADS) == tuple(range(8, 49))
    assert a.OWN_HEADS in a.SCAN_HEADS, "the 16 v 16 mirror is part of the scan"
    assert a.STAGE4_LAYOUTS == ("L-0061", "L-0080", "L-0083", "L-0039")
    assert isinstance(a.DRAFT_SPREAD_TICKS, tuple) and a.DRAFT_SPREAD_TICKS[0] == 0 and list(a.DRAFT_SPREAD_TICKS) == sorted(set(a.DRAFT_SPREAD_TICKS))


def test_r2_every_numeric_constant_is_named_and_says_whose_number_it_is():
    tree = ast.parse(SRC.read_text())
    lines = SRC.read_text().splitlines()
    names = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        ids = [t.id for t in target.elts if isinstance(t, ast.Name)] if isinstance(target, ast.Tuple) else [target.id] if isinstance(target, ast.Name) else []
        if ids and all(i.isupper() for i in ids) and any(isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) for n in ast.walk(node.value)):
            names += ids
            text = " ".join(lines[node.lineno - 1:node.end_lineno])
            assert re.search(r"DRAFT-|Westley|README", text), "%s: a number with no owner on its line" % ids
    assert {"OWN_HEADS", "SCAN_FROM", "SCAN_TO", "DRAFT_SPREAD_TICKS", "DRAFT_HOLDER_STEP_WU", "V_HEADS"} <= set(names)
    assert not [n for n in names if re.search(r"THRESHOLD|TOLERANCE|PASS|MARK|SCORE", n)]


def test_r3_the_module_issues_no_order_and_imports_no_engine():
    text = SRC.read_text()
    tree = ast.parse(text)
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not [m for m in imported if m.endswith(".engine") or m == "scripts.skilllab.engine"], imported
    assert not re.search(r"order_attack_move|order_guard|order_move|order_idle|set_order", text)
    assert "isolation_runner" in text and "isolation_measures" in text, "every run goes through LI1's runner and is measured by LI2"


def test_r4_flags_are_a_closed_list_of_names_and_there_is_no_pass_mark():
    a = af.arms()
    assert set(a.FLAGS) == {"defect", "invalid", "orders_ended_short"} and list(a.FLAGS) == sorted(a.FLAGS)
    public = {n for n in dir(a) if not n.startswith("_")}
    assert not [n for n in public if re.search(r"^(is_)?(pass|passed|fail|failed|verdict|ok)$", n, re.I)]
    for fn in ("scan_m", "run_m", "run_v_flat", "run_v_stage4", "m_layout", "v_layout", "layout_toml", "layout_id_m", "layout_id_v", "stopping_check", "blocks_of", "flags_of", "vision_report", "part_word_m", "part_word_v"):
        assert callable(getattr(a, fn)), fn


def test_r5_the_module_is_new_and_the_runner_and_measures_are_untouched():
    assert SRC.is_file()
    for rel in ("scripts/skilllab/arena/isolation_runner.py", "scripts/skilllab/arena/isolation_measures.py"):
        changed = subprocess.run(["git", "--no-optional-locks", "-C", str(fx.ROOT), "diff", "--name-only", LI3_BASE, "--", rel], capture_output=True, text=True).stdout.strip()
        assert changed == "", "%s differs from the base of LI3: LI3 is a new file behind them (wiring, if any, is its own later commit)" % rel
