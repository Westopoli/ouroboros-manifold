# Rule pins: R-207-06, R-207-07, R-087-04, R-084-04, R-083-03
"""Engine rule fixes 2026-11-08, F0, the wiring: the online monitor `run.fight` uses, the fight-document keys, `snapshot.validate`, `run.py`,
`closeup.py` and `page.py`.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F0". The pure predicates and their planted/clean traces are tests/skilllab/test_invariants.py
(which also documents the checker's API). What this file pins on top of that API:

    class Monitor(engine, world, width, height, sight)    scripts/skilllab/invariants.py: the online wrapper
        .after_step()      call right after engine.step(world); reads the engine's state, extends the recorded trace by one frame and runs the checks
        .violations        every violation so far, {"rule", "tick", "unit", "detail"} dicts, ordered by (tick, rule, unit); tick counts after_step calls from 1
        .suspended         {rule: switch} of the rules this run cannot judge; sight "off" suspends R-087-03 (its 'leaves the side's sight' clause has no meaning
                           with targeting by sight off) and R-093-02; sight "control" (targeting by sight off too) suspends the same two (2026-11-11 correction,
                           tests/skilllab/arena/test_invariants_continuity_sight_wiring.py); sight "on" suspends nothing
      `run.fight` builds one after spawning (width and height of the landscape preset), calls after_step() after every engine.step, and hands the result to
      `run._document` (through the orders block it returns, as it does for stage4); `closeup.py` gets it for free (it calls both).

    fight document (om-fight-2 only): top-level `violations`  list of at most 20 {"rule": str, "tick": int, "unit": int, "detail": str}, the earliest by
      (tick, rule, unit), and `invalid` bool (True when any violation was found). A clean fight may leave both keys out; these tests read them with a default.
    snapshot.validate accepts both absent or present on om-fight-2 and rejects them on om-fight-1 (and a non-bool `invalid`, a non-list `violations`).
    run.py   one line `INVALID <layout id> <rule> tick <N> unit <U>` per distinct rule (the earliest violation of that rule) on stdout; exit code 2 when any
             fight of the call is invalid, unless `--allow-invalid` (then 0; the fight file is written either way).
    page.py  an invalid fight's row carries the words `INVALID: <rule> tick <N> unit <U>` (its first violation) and no agree/disagree verdict.
    SNAPSHOT.md documents `violations` and `invalid`.

Planted faults are made on the real engine: a wrapper of Engine.step moves a unit with om_unit_set_pos to the middle of a blocked cell on two steps (so the
checker sees a unit inside a box, and a jump of hundreds of wu), whatever the engine's own rule fixes do. The quiet layout never fires a shot: a Vanguard
that holds still and a Bastion that walks 800 wu toward it in 20 s, a box far from the walk. Controls green today: the quiet fight, the schema checks that
reject, an unflagged page.
"""
import ctypes
import importlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab.arena import closeup, features, run, snapshot  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402
from scripts.skilllab.fight import _register_types  # noqa: E402
from test_page_stage3 import visible  # noqa: E402
from test_page_stage4 import build, stage  # noqa: E402

L0039 = oracle.CATALOGUE / "L-0039.toml"
PLANT_STEPS = (5, 6)


def quiet_layout():
    return {"id": "X-f0", "landscape": "small_flat", "orders": "hold:A", "predict": "B",
            "side_a": {"units": [{"role": "Vanguard", "x": 500.0, "y": 500.0, "layer": 0}]},
            "side_b": {"units": [{"role": "Bastion", "x": 3500.0, "y": 3500.0, "layer": 0}]},
            "features": [{"kind": "cover", "x": 3000.0, "y": 600.0, "boxes": [{"x": 3000.0, "y": 600.0, "w": 300, "h": 300}]}]}


@pytest.fixture
def plant(monkeypatch):
    """plant(steps=PLANT_STEPS): from now on Engine.step moves side A's first unit to the centre of the first blocked cell (layer 0) after those step numbers
    (counted over all worlds stepped since). Returns the unit it moved, once known: {"unit": id}."""
    def install(steps=PLANT_STEPS):
        real, state, seen = Engine.step, {"n": 0}, {}

        def step(self, w):
            real(self, w)
            state["n"] += 1
            if state["n"] in steps:
                lib = self._lib
                lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
                cx, cy = next((cx, cy) for cx in range(40) for cy in range(40) if lib.om_navmesh_is_cell_blocked(w, cx, cy, 0))
                seen["unit"] = sorted(self._own[(w.value, 0)])[0]
                lib.om_unit_set_pos(w, seen["unit"], cx * 100 + 50.0, cy * 100 + 50.0)
        monkeypatch.setattr(Engine, "step", step)
        return seen
    return install


def document(layout, sight="off", seconds=20):
    frames, last, end, orders = run.fight(layout, 1, sight, seconds)
    return run._document(layout, "x.toml", 1, sight, frames, last, end, orders)


# ------------------------------------------------------------------ the fight document

def test_F0_a_planted_wall_entry_makes_the_fight_document_invalid(plant):
    """F0: 'The fight document gains optional `violations` (first 20) and `invalid`.' Planted: the Vanguard is on a box cell's centre after steps 5 and 6.
    Red today: the document has neither key."""
    seen = plant()
    doc = document(quiet_layout())
    assert doc.get("invalid") is True, "no `invalid` in the document: keys %s" % sorted(doc)
    rules = {v["rule"] for v in doc["violations"]}
    assert {"R-207-06", "continuity"} <= rules, rules
    first = next(v for v in doc["violations"] if v["rule"] == "R-207-06")
    assert (first["tick"], first["unit"]) == (5, seen["unit"]) and set(first) == {"rule", "tick", "unit", "detail"}
    assert snapshot.validate(doc) == []


def test_F0_the_document_keeps_only_the_first_twenty_violations_in_order(plant):
    """F0: 'violations (first 20)': 30 planted steps give 30 R-207-06 violations (and more); the document holds the earliest 20, ordered."""
    plant(range(5, 35))
    doc = document(quiet_layout(), seconds=30)
    keys = [(v["tick"], v["rule"], v["unit"]) for v in doc.get("violations", [])]
    assert len(keys) == 20 and keys == sorted(keys) and keys[0][0] == 5, keys[:3]


def test_F0_control_the_quiet_fight_is_not_invalid():
    """Control (green today, must stay): a fight in which nothing fires and nothing is out of place leaves the document valid and unflagged."""
    doc = document(quiet_layout())
    assert (doc.get("invalid", False), doc.get("violations", [])) == (False, [])
    assert doc["result"]["ticks"] == 400 and snapshot.validate(doc) == []


# ------------------------------------------------------------------ the online monitor

def _tiny(sight):
    """A world as run.fight builds it for the quiet layout, and the unit ids of side A and B."""
    layout = quiet_layout()
    engine = Engine()
    w = engine.new_world(1)
    engine.disable_abilities(w)
    engine.set_canvas(w, 4000.0, 4000.0)
    engine.block_rect(w, 3000.0, 600.0, 3100.0, 700.0, 0, 4)
    types = _register_types(engine, w, run._setup_for(layout))
    features.walk_on_ground(engine, w, types)
    a = engine.spawn(w, types["Vanguard"][0], 0, 500.0, 500.0, 0)
    b = engine.spawn(w, types["Bastion"][0], 1, 3500.0, 3500.0, 0)
    engine.order_attack_move(w, [b], 500.0, 500.0)
    inv = importlib.import_module("scripts.skilllab.invariants")
    return engine, w, a, b, inv.Monitor(engine, w, 4000.0, 4000.0, sight)


def test_F0_the_online_monitor_flags_a_planted_wall_entry_on_the_tick_it_happens():
    """F0, the online wrapper: after step 5 the Vanguard is set down inside the box; the monitor reports R-207-06 at its tick 5 for that unit."""
    engine, w, a, b, mon = _tiny("on")
    try:
        for n in range(1, 8):
            engine.step(w)
            if n == 5:
                lib = engine._lib
                lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
                lib.om_unit_set_pos(w, a, 3050.0, 650.0)
            mon.after_step()
        found = [(v["tick"], v["unit"]) for v in mon.violations if v["rule"] == "R-207-06"]
        assert found and found[0] == (5, a), mon.violations[:3]
    finally:
        engine.free_world(w)


def test_F0_the_online_monitor_is_silent_on_a_quiet_world():
    """F0 control: 100 quiet steps, no violation."""
    engine, w, a, b, mon = _tiny("on")
    try:
        for _ in range(100):
            engine.step(w)
            mon.after_step()
        assert mon.violations == []
    finally:
        engine.free_world(w)


@pytest.mark.parametrize("sight,suspended", [("off", True), ("on", False)])
def test_F0_a_run_with_sight_off_reports_the_suspended_check(sight, suspended):
    """F0: 'a layout whose check depends on a switch the run turned off (sight off) reports `suspended: <switch>` for that check, never a silent pass':
    with sight off R-087-03 is suspended (and names the switch); with sight on it is judged."""
    engine, w, a, b, mon = _tiny(sight)
    try:
        engine.step(w)
        mon.after_step()
        assert ("R-087-03" in mon.suspended) == suspended and (not suspended or (isinstance(mon.suspended["R-087-03"], str) and mon.suspended["R-087-03"]))
    finally:
        engine.free_world(w)


# ------------------------------------------------------------------ the pure checker on real engine data

@pytest.mark.parametrize("name,sight", [("L-0039", "on"), ("L-0050", "on")])
def test_F0_the_checker_agrees_with_the_test_oracle_on_real_fights(name, sight):
    """F0 against the independent oracle (engine_rules_oracle.py reads the engine its own way): over the same 100-second fight the checker's counts of
    R-207-06, R-087-04, R-084-04 and R-083-03 violations equal the oracle's. Holds before and after the engine fixes (0 = 0 once they land). The trace is
    built by oracle.invariants_trace, the contract's example."""
    inv = importlib.import_module("scripts.skilllab.invariants")
    rec = oracle.played(name, sight)
    rules = inv.Rules(width=4000.0, height=4000.0, blocked_cell=lambda cx, cy, layer: (cx, cy, layer) in rec.blocked)
    rep = inv.check(oracle.invariants_trace(rec), rules, only=["R-207-06", "R-087-04", "R-084-04", "R-083-03"])
    got = {r: len([v for v in rep.violations if v["rule"] == r]) for r in ("R-207-06", "R-087-04", "R-084-04", "R-083-03")}
    want = {"R-207-06": len(oracle.cell_entries(rec)), "R-087-04": len(oracle.fired_while_moving(rec)),
            "R-084-04": len(oracle.moved_in_backswing(rec)), "R-083-03": len(oracle.warden_overheal(rec))}
    assert got == want


# ------------------------------------------------------------------ snapshot.validate

def v2(**extra):
    return dict(snapshot.example(frames=3, units_per_side=2, schema=snapshot.SCHEMA_V2), **extra)


VIOLATION = {"rule": "R-207-06", "tick": 73, "unit": 4, "detail": "Interceptor 5.4 wu inside a blocked cell"}


def test_F0_validate_accepts_violations_and_invalid_on_om_fight_2():
    """F0: `snapshot.validate` accepts the keys present. Red today: unknown top-level keys."""
    assert snapshot.validate(v2(invalid=True, violations=[VIOLATION])) == []
    assert snapshot.validate(v2(invalid=False, violations=[])) == []


def test_F0_validate_control_accepts_both_absent_on_both_schemas():
    """Control (green today): the keys are optional."""
    assert snapshot.validate(v2()) == [] and snapshot.validate(snapshot.example(schema=snapshot.SCHEMA)) == []


@pytest.mark.parametrize("key,value", [("invalid", True), ("violations", [VIOLATION])])
def test_F0_validate_rejects_the_keys_on_om_fight_1(key, value):
    """F0: 'rejects on om-fight-1'. (Green today for the wrong reason, an unknown key; it must stay rejected once the keys are known to om-fight-2.)"""
    doc = dict(snapshot.example(schema=snapshot.SCHEMA), **{key: value})
    assert snapshot.validate(doc), "om-fight-1 accepted `%s`" % key


@pytest.mark.parametrize("extra", [{"invalid": "yes"}, {"violations": "R-207-06"}, {"violations": [{"rule": "R-207-06"}]}],
                         ids=["invalid-not-bool", "violations-not-list", "violation-missing-keys"])
def test_F0_validate_rejects_malformed_values_when_the_keys_are_known(extra):
    """F0 (my reading of 'accepts ... rejects'): a non-bool `invalid`, a non-list `violations`, a violation without rule, tick, unit and detail are errors.
    The accepted-shape test above fails first today; this one is red only for the right reason once that passes (green today: unknown key)."""
    assert snapshot.validate(v2(**extra))
    assert snapshot.validate(v2(invalid=True, violations=[VIOLATION])) == [], "the keys are not accepted at all yet"


def test_F0_snapshot_md_documents_the_keys():
    """F0: 'scripts/skilllab/arena/SNAPSHOT.md documents them.'"""
    text = (Path(run.__file__).parent / "SNAPSHOT.md").read_text()
    assert "violations" in text and "invalid" in text


# ------------------------------------------------------------------ run.py, closeup.py

def _main(args, capsys):
    code = run.main(args)
    return code, capsys.readouterr().out


def test_F0_run_py_prints_one_INVALID_line_per_rule_and_exits_2(plant, tmp_path, capsys):
    """F0: 'run.py prints `INVALID <id> <rule> tick N unit U` per distinct rule and exits 2 when any fight is invalid'. L-0039, sight off, 10 s, the planted
    wall entry. Red today: exit 0, no line. (2026-11-11 correction, Test-defect: this also required a `continuity` line. The plant teleports a unit of the dense
    L-0039 start onto a blocked cell on one layer, beside its friends, and continuity now judges layer changes and unpushed steps only (R-004-08; the tick-6 repeat starts inside
    a blocked cell and is not judged), so only R-207-06 is printed; the two-rule document is test_F0_a_planted_wall_entry_makes_the_fight_document_invalid.)"""
    seen = plant()
    code, out = _main(["--layout", str(L0039), "--seed", "1", "--out", str(tmp_path), "--cap-seconds", "10"], capsys)
    lines = [m.groups() for m in re.finditer(r"^INVALID L-0039 (\S+) tick (\d+) unit (\d+)$", out, re.M)]
    rules = [r for r, _, _ in lines]
    assert code == 2 and len(rules) == len(set(rules)) and "R-207-06" in rules, (code, out)
    assert ("R-207-06", "5", str(seen["unit"])) in lines
    doc = json.loads((tmp_path / "L-0039-s1.fight.json").read_text())
    assert doc["invalid"] is True


def test_F0_allow_invalid_keeps_the_exit_code_zero_and_still_writes_the_flag(plant, tmp_path, capsys):
    """F0: 'unless `--allow-invalid`'. Same fight; exit 0; the fight file is written and flagged."""
    plant()
    code, out = _main(["--layout", str(L0039), "--seed", "1", "--out", str(tmp_path), "--cap-seconds", "10", "--allow-invalid"], capsys)
    doc = json.loads((tmp_path / "L-0039-s1.fight.json").read_text())
    assert (code, doc.get("invalid")) == (0, True), out


def test_F0_run_py_control_a_clean_start_exits_zero_with_no_INVALID_line(tmp_path, capsys):
    """Control (green today and after): one simulated second of L-0039, before anything is in range, exits 0 and prints no INVALID line."""
    code, out = _main(["--layout", str(L0039), "--seed", "1", "--out", str(tmp_path), "--cap-seconds", "1"], capsys)
    assert code == 0 and "INVALID" not in out, out


def test_F0_closeup_files_carry_the_flag(plant, tmp_path):
    """F0: 'wiring in run.py (fight) and closeup.py': the closeup document of a planted fight is invalid and lists the violation."""
    plant()
    assert closeup.main(["--layout", str(L0039), "--seed", "1", "--sight", "off", "--every-ticks", "50", "--out", str(tmp_path)]) == 0
    doc = json.loads(next(tmp_path.glob("*.fight.json")).read_text())
    assert doc.get("invalid") is True and any(v["rule"] == "R-207-06" for v in doc["violations"])


# ------------------------------------------------------------------ page.py

def _flag(out, stem):
    path = out / (stem + ".fight.json")
    doc = json.loads(path.read_text())
    doc["invalid"], doc["violations"] = True, [VIOLATION]
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")


@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_F0_page_marks_an_invalid_fight(rated, tmp_path):
    """F0: 'page.py marks an invalid fight "INVALID: <rule> tick N unit U"'. Red today: the key is unknown, so the row reads 'INVALID <stem>' with the
    schema error instead."""
    out, _ = stage(tmp_path, rated=rated)
    _flag(out, "L-9501-s1")
    assert "INVALID: R-207-06 tick 73 unit 4" in visible(build(out))


def test_F0_page_does_not_rank_an_invalid_fight(tmp_path):
    """F0: '... and does not rank it': an unrated row of an invalid fight carries no agree/disagree verdict (my reading of 'rank'); the same page's valid
    fight does."""
    out, _ = stage(tmp_path, seeds=(1, 2))
    _flag(out, "L-9501-s1")
    text = visible(build(out))
    bad_row, good_row = text.split("L-9501 seed 2")[0], "L-9501 seed 2" + text.split("L-9501 seed 2")[1]
    assert "INVALID: R-207-06" in bad_row and not re.search(r"\b(dis)?agree\b", bad_row.split("INVALID:")[1])
    assert re.search(r"\b(dis)?agree\b", good_row)


def test_F0_page_control_a_valid_fight_has_no_marker(tmp_path):
    """Control (green today and after): an unflagged fight reads no INVALID."""
    out, _ = stage(tmp_path)
    assert "INVALID" not in visible(build(out))
