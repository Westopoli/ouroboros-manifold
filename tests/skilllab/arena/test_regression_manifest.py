# spec: docs/northstar/plans/engine-rules-2026-11-08/round6.md (L2); docs/stories/H-040.md ("Orders and fight end")
"""Round 6, L2: the approved fights are the lab's standing set (DEC-regression-set-2026-11-18).

round6.md L2, word for word: "A manifest `docs/northstar/research/layer_dynamics/arena/approved.toml`: one row per fight with its stage, layout or situation, sight setting, control kind, his
expected winner and rate where he gave one, and the decision that approved it. Rows: stage 1 L-0054 (sight off); stage 2 SIT-0101 and SIT-0103 to SIT-0108 (sight off; SIT-0102 was denied as a
roster finding); stage 3 L-0055, L-0073, L-0084, L-0039 (sight off) each with its ground control; stage 4 L-0061, L-0080, L-0083, L-0039 (sight on) each with its sight control.
`python3 -m scripts.skilllab.arena.regression` runs every row (seed 1), prints one line per fight (end, winner, survivors, ticks, agreement with his expectation, checker reports) and exits
non-zero if any fight ends without an elimination or the checker reports a rule. It gives each fight the orders its layout names and nothing more. The sweep under
`docs/reports/2026-11-07-rule-enforcement/sweep/` reads the manifest instead of its own layout lists and no longer switches the catalogue's rejection rule off.
Proof: a test that the manifest names exactly the fights of the stage decisions (DEC-stage1-seen-2026-11-01, DEC-stage2-seen-2026-11-02, DEC-stage3-layouts-2026-11-05,
DEC-stage4-layouts-2026-11-05) and that every row loads; a slow test that runs the command and expects exit 0, with no list of expected draws: it is red while stage 1 ends in a stand-off and
while SIT-0105 to SIT-0107 do not convert, and that red is the signal." And the fixed point: "One order per side. A lab fight gets one attack-move per side at tick 0 ... and never another."

THE API THIS FILE PINS (the lab builder builds to it; the manifest file itself is the builder's):

  approved.toml     one `[[fight]]` table per fight, keys
                      stage            int, 1 to 4
                      layout | situation   exactly one: a catalogue id `L-0054`, or a situation id `SIT-0101` (the converter gives it an id of its own, `L-0101` onwards, when the row runs)
                      sight            "off" (stages 1 to 3) or "on" (stage 4)
                      control          "none" (stages 1 and 2), "ground" (stage 3: the twin with the features emptied), "sight" (stage 4: targeting by sight off), the kinds of run.py `--control`
                      expected_winner  "A", "B" or "draw", the file's own `predict` (the layout's, or the situation's `Predict:`)
                      predict_rate     side A's win rate where his file gives one: the layout's `predict_rate`; for a situation the `Expected win rate:` as the converter turns it into side A's
                                       (Predict A: the number, B: one minus it, draw: 0.5). Absent when the file gives none (L-0054).
                      decision         the id of the decision row (docs/northstar/story_reviews/westley/decisions.md) that approved the fight's stage
  python -m scripts.skilllab.arena.regression [--manifest PATH] [--catalogue DIR] [--situations DIR]
                    defaults: the real manifest, the real catalogue, the real situations directory. `main(argv=None)` returns the exit code (0 when every fight ended by elimination and the checker
                    reported nothing; non-zero otherwise) and `python -m` exits with it. A `layout` row is the file `<catalogue>/<id>.toml`. Seed 1, every fight. The fights run one after
                    another IN THIS PROCESS (no pool, no subprocess): the order-count test below counts calls through `scripts.skilllab.engine.Engine`.
                    One stdout line per fight (a summary line besides is allowed; it names no row's id), in manifest order, naming the row's id and these keys, in this form:
                      <id> sight=<on|off> end=<wipe|silence|cap> winner=<A|B|stall|none> survivors=<a>:<b> ticks=<n> agree=<yes|no|-> checker=<none|rule[,rule...]>
                    plus the word DRAW on the line of a fight that ended with both sides alive (`end` silence or cap). `agree` is yes when the winner is the expected one, no when it is not (a
                    disagreement alone is not a failure: DEC-stage1-seen-2026-11-01 accepted one), `-` when the row expects a draw.
  the sweep         docs/reports/2026-11-07-rule-enforcement/sweep/sweep.py reads its fights from the manifest and does not set `ALLOW_R6`.

The cheapest real fights are the fixtures of tests/skilllab/arena/test_run.py (`make_stall_layout`: eight Vanguards a side, small_flat, sight off): `hold:A` ends by silence at tick 200 with 8:8 alive
(the draw); `both_same_point` ends by wipe at about tick 1,700 (the elimination). The checker report is a real fight in which `Engine.step` moves one unit 300 wu sideways in tick 5 (the repository's
own way of planting a fault, tests/skilllab/arena/test_invariants_wiring.py): `continuity` is reported.

Red today: the manifest, the command and the sweep change do not exist. The slow test (OM_LAB_SLOW=1) is red until both Round 6 tracks are merged (stage 1 ends in a stand-off on the Round 5
engine, SIT-0105 to SIT-0107 do not convert); it is not run by the test writer. Controls that hold today: the decision ids exist, the approved layout files exist and pass `check_layout`.
"""
import contextlib
import ctypes
import importlib
import io
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.skilllab.catalogue.produce import check_layout, presets, rules  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402
from test_run import make_stall_layout, write_layout_orders  # noqa: E402
from test_run_apart_end import plant_shot  # noqa: E402

LD = ROOT / "docs" / "northstar" / "research" / "layer_dynamics"
MANIFEST = LD / "arena" / "approved.toml"
CATALOGUE = LD / "catalogue"
SITUATIONS = LD / "situations"
DECISIONS = ROOT / "docs" / "northstar" / "story_reviews" / "westley" / "decisions.md"
SWEEP = ROOT / "docs" / "reports" / "2026-11-07-rule-enforcement" / "sweep" / "sweep.py"

DEC1 = "DEC-stage1-seen-2026-11-01"
DEC2 = "DEC-stage2-seen-2026-11-02"
DEC3 = "DEC-stage3-layouts-2026-11-05"
DEC4 = "DEC-stage4-layouts-2026-11-05"

# (stage, kind, id, sight, control, decision): the rows of round6.md L2. SIT-0102 is not here (denied as a roster finding).
ROWS = ([(1, "layout", "L-0054", "off", "none", DEC1)]
        + [(2, "situation", "SIT-%04d" % n, "off", "none", DEC2) for n in (101, 103, 104, 105, 106, 107, 108)]
        + [(3, "layout", lid, "off", "ground", DEC3) for lid in ("L-0055", "L-0073", "L-0084", "L-0039")]
        + [(4, "layout", lid, "on", "sight", DEC4) for lid in ("L-0061", "L-0080", "L-0083", "L-0039")])

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")


# ------------------------------------------------------------------------------------------------------------ the manifest

def _manifest():
    if not MANIFEST.exists():
        pytest.fail("L2 not built: %s does not exist" % MANIFEST.relative_to(ROOT))
    with open(MANIFEST, "rb") as f:
        return tomllib.load(f)["fight"]


def _key(fight):
    kind = "layout" if "layout" in fight else "situation"
    return fight["stage"], kind, fight[kind]


def _expected(kind, ident):
    """(predict, side A's rate or None) as his file gives it: the layout's `predict` and `predict_rate`; a situation's `Predict:` and `Expected win rate:` as the converter turns them (situations.py `_layout`)."""
    if kind == "layout":
        with open(CATALOGUE / (ident + ".toml"), "rb") as f:
            lay = tomllib.load(f)
        return lay["predict"], lay.get("predict_rate")
    text = next(SITUATIONS.glob(ident + "-*.md")).read_text()
    predict = re.search(r"^Predict:[ \t]*(\S+)", text, re.M).group(1)
    number = float(re.search(r"^Expected win rate:[ \t]*(\S+)", text, re.M).group(1))
    return predict, {"A": number, "B": 1 - number, "draw": 0.5}[predict]


def test_L2_the_manifest_names_exactly_the_fights_of_the_stage_decisions():
    """L2 proof: 'the manifest names exactly the fights of the stage decisions': sixteen rows, one per (stage, layout or situation) of ROWS, none twice, none more (SIT-0102 and the denied
    layouts are not in it); L-0039 is in twice, once per stage. Each row names exactly one of `layout` and `situation`. Red today: no manifest."""
    fights = _manifest()
    assert sorted(_key(f) for f in fights) == sorted((s, k, i) for s, k, i, *_ in ROWS)
    assert all(("layout" in f) != ("situation" in f) for f in fights)


def test_L2_each_row_has_its_stage_sight_control_and_deciding_decision():
    """L2: 'its stage, layout or situation, sight setting, control kind ... and the decision that approved it': stages 1 to 3 sight off and stage 4 on; control none (1, 2), ground (3), sight (4);
    the decision of the row's stage (DEC-stage1-seen-2026-11-01, DEC-stage2-seen-2026-11-02, DEC-stage3-layouts-2026-11-05, DEC-stage4-layouts-2026-11-05). Red today: no manifest."""
    got = {_key(f): (f.get("sight"), f.get("control"), f.get("decision")) for f in _manifest()}
    assert got == {(s, k, i): (sight, control, dec) for s, k, i, sight, control, dec in ROWS}


def test_L2_each_row_carries_his_expected_winner_and_rate_from_his_own_file():
    """L2: 'his expected winner and rate where he gave one': the layout's `predict` and `predict_rate` (side A's rate), or the situation's `Predict:` and `Expected win rate:` as side A's. L-0054
    (predict draw, no rate in its file) has an expected winner `draw` and no `predict_rate` key. Red today: no manifest."""
    for f in _manifest():
        kind = "layout" if "layout" in f else "situation"
        want, rate = _expected(kind, f[kind])
        assert f.get("expected_winner") == want, (f[kind], f.get("expected_winner"), want)
        if rate is None:
            assert "predict_rate" not in f, (f[kind], f["predict_rate"])
        else:
            assert f.get("predict_rate") == pytest.approx(rate), (f[kind], f.get("predict_rate"), rate)


@pytest.mark.parametrize("dec", [DEC1, DEC2, DEC3, DEC4])
def test_L2_control_each_decision_the_spec_names_is_a_row_of_the_decision_log(dec):
    """L2 proof names four decisions: each is a row of docs/northstar/story_reviews/westley/decisions.md (control, green today)."""
    assert re.search(r"^\| \d{4}-\d{2}-\d{2} \| %s \|" % re.escape(dec), DECISIONS.read_text(), re.M), "%s is no row of decisions.md" % dec


def test_L2_every_manifest_row_names_one_of_those_decisions():
    """L2: the `decision` of every row is one of the four (and all four are used). Red today: no manifest."""
    assert {f["decision"] for f in _manifest()} == {DEC1, DEC2, DEC3, DEC4}


@pytest.mark.parametrize("lid", ["L-0054", "L-0055", "L-0073", "L-0084", "L-0039", "L-0061", "L-0080", "L-0083"])
def test_L2_control_the_approved_layout_file_exists_and_passes_check_layout(lid):
    """L2 'every row loads' (the layout half; control, green today): the file parses and the producer's own `check_layout` finds nothing wrong with it."""
    with open(CATALOGUE / (lid + ".toml"), "rb") as f:
        assert check_layout(tomllib.load(f), presets(), rules()) == []


def test_L2_every_layout_row_loads_into_a_runnable_fight():
    """L2 proof 'every row loads' (layout rows): each `layout` row names a file in the catalogue that parses and passes `check_layout`, with units on both sides. Red today: no manifest."""
    layouts = [f["layout"] for f in _manifest() if "layout" in f]
    assert layouts
    for lid in layouts:
        with open(CATALOGUE / (lid + ".toml"), "rb") as fh:
            lay = tomllib.load(fh)
        assert check_layout(lay, presets(), rules()) == [] and lay["side_a"]["units"] and lay["side_b"]["units"], lid


def test_L2_every_situation_row_converts(tmp_path):
    """L2 proof 'every row loads' (situation rows): each `situation` row's file converts (the converter's CLI, alone in its directory, exit 0, CONVERTED). Red today: no manifest, and
    SIT-0105 to SIT-0107 are rejected ('arc too small', L3)."""
    import shutil
    sits = [f["situation"] for f in _manifest() if "situation" in f]
    assert sits
    for sit in sits:
        src = tmp_path / sit
        src.mkdir()
        shutil.copy(next(SITUATIONS.glob(sit + "-*.md")), src)
        done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.situations", "--dir", str(src), "--out", str(tmp_path / (sit + "-out")), "--next-id", "L-0101"],
                              cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        assert done.returncode == 0 and "CONVERTED" in done.stdout, "%s: %s" % (sit, (done.stdout + done.stderr).strip())


# ------------------------------------------------------------------------------------------------------------ the command

def _reg():
    try:
        return importlib.import_module("scripts.skilllab.arena.regression")
    except ModuleNotFoundError as err:
        pytest.fail("L2 not built: %s" % err)


def _row(layout, expected, stage=1):
    return ('[[fight]]\nstage = %d\nlayout = "%s"\nsight = "off"\ncontrol = "none"\nexpected_winner = "%s"\ndecision = "%s"\n\n' % (stage, layout, expected, DEC1))


@pytest.fixture(scope="module")
def planted(tmp_path_factory):
    """A catalogue of three planted layouts (the stall fixture): L-9101 `hold:A` (ends by silence, 8:8: the draw), L-9102 and L-9103 `both_same_point` (end by wipe, side A wins 8:0)."""
    cat = tmp_path_factory.mktemp("catalogue")
    write_layout_orders(make_stall_layout("L-9101"), cat, "hold:A")
    write_layout_orders(make_stall_layout("L-9102"), cat, "both_same_point")
    write_layout_orders(make_stall_layout("L-9103"), cat, "both_same_point")
    return cat


def _manifest_file(tmp_path, *rows):
    path = tmp_path / "manifest.toml"
    path.write_text("".join(rows))
    return path


def _main(manifest, cat):
    """(exit code, stdout) of `regression.main` called in this process."""
    reg, buf = _reg(), io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = reg.main(["--manifest", str(manifest), "--catalogue", str(cat)])
    return code, buf.getvalue()


def _lines_of(out, label):
    return [ln for ln in out.splitlines() if label in ln]


def _field(line, name):
    m = re.search(r"\b%s=(\S*)" % name, line)
    assert m, "no %s= in %r" % (name, line)
    return m.group(1)


def test_L2_command_a_fight_that_ends_by_elimination_gives_exit_0_and_one_line(planted, tmp_path):
    """L2: 'prints one line per fight (end, winner, survivors, ticks, agreement with his expectation, checker reports) and exits non-zero if any fight ends without an elimination or the
    checker reports a rule'. The command itself (`python -m`, a subprocess), one planted row, L-9102 (wipe, side A wins), expected A: exit 0; one line naming L-9102 with end=wipe, winner=A,
    survivors=8:0, a tick count, agree=yes, checker=none, and no DRAW. Red today: no module."""
    manifest = _manifest_file(tmp_path, _row("L-9102", "A"))
    done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.regression", "--manifest", str(manifest), "--catalogue", str(planted)],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    lines = _lines_of(done.stdout, "L-9102")
    assert done.returncode == 0, (done.returncode, done.stdout[-800:], done.stderr[-800:])
    assert len(lines) == 1, done.stdout
    line = lines[0]
    assert (_field(line, "end"), _field(line, "winner"), _field(line, "survivors"), _field(line, "agree"), _field(line, "checker")) == ("wipe", "A", "8:0", "yes", "none")
    assert int(_field(line, "ticks")) > 0 and _field(line, "sight") == "off" and "DRAW" not in line


def test_L2_command_a_fight_that_ends_with_both_sides_alive_gives_a_non_zero_exit_and_says_so(planted, tmp_path):
    """L2: 'exits non-zero if any fight ends without an elimination'. L-9101 (`hold:A`, the stall fixture): both sides alive at tick 200 (end silence, 8:8): non-zero exit, and its one line
    says DRAW with end=silence and survivors=8:8 (the winner key reads `stall`). Red today: no module."""
    code, out = _main(_manifest_file(tmp_path, _row("L-9101", "draw")), planted)
    (line,) = _lines_of(out, "L-9101")
    assert code != 0, out
    assert "DRAW" in line and (_field(line, "end"), _field(line, "survivors"), _field(line, "winner")) == ("silence", "8:8", "stall"), line


def test_L2_command_a_winner_other_than_his_expected_one_is_reported_not_failed(planted, tmp_path):
    """L2 'agreement with his expectation' is a column, not a failure (DEC-stage1-seen-2026-11-01 accepted a disagreement): L-9103 ends by wipe with side A winning; the row expects B: exit 0,
    agree=no on its one line. Red today: no module."""
    code, out = _main(_manifest_file(tmp_path, _row("L-9103", "B")), planted)
    (line,) = _lines_of(out, "L-9103")
    assert code == 0 and (_field(line, "agree"), _field(line, "winner"), _field(line, "end")) == ("no", "A", "wipe"), (code, out)


def test_L2_command_a_checker_report_gives_a_non_zero_exit_and_the_rule_on_the_line(planted, tmp_path, monkeypatch):
    """L2: 'exits non-zero if ... the checker reports a rule'. The same wipe fight as L-9102, with `Engine.step` moving side A's first unit 300 wu sideways in its fifth step (a real fault the
    checker sees as `continuity`): the fight still ends by wipe, the exit is non-zero, and its line says checker=continuity (the rule id, comma-joined if more) and not DRAW. Red today: no module."""
    real, state = Engine.step, {"n": 0}

    def step(self, w):
        real(self, w)
        state["n"] += 1
        if state["n"] == 5:
            u = sorted(self._own[(w.value, 0)])[0]
            x, y = self.unit_pos(w, u)
            self._lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
            self._lib.om_unit_set_pos(w, u, x, y + 300.0)
    monkeypatch.setattr(Engine, "step", step)
    code, out = _main(_manifest_file(tmp_path, _row("L-9102", "A")), planted)
    (line,) = _lines_of(out, "L-9102")
    assert code != 0, out
    assert _field(line, "end") == "wipe" and "continuity" in _field(line, "checker").split(",") and "DRAW" not in line, line


class _Orders:
    """Records every order call through `Engine` (every `order_*` method) per fight, with the number of `Engine.step` calls made on that world before it."""

    def __init__(self, mp):
        self.fights = []
        me = self
        real_new, real_step = Engine.new_world, Engine.step

        def new_world(engine, seed):
            me.fights.append({"orders": [], "steps": 0})
            return real_new(engine, seed)

        def step(engine, w):
            me.fights[-1]["steps"] += 1
            return real_step(engine, w)
        mp.setattr(Engine, "new_world", new_world)
        mp.setattr(Engine, "step", step)
        for name in [n for n in dir(Engine) if n.startswith("order_")]:
            def wrapped(engine, w, ids, *args, _real=getattr(Engine, name), _name=name):
                ids = list(ids)
                me.fights[-1]["orders"].append((_name, len(ids), tuple(args), me.fights[-1]["steps"]))
                return _real(engine, w, ids, *args)
            mp.setattr(Engine, name, wrapped)

    def played(self):
        """The orders of each fight that stepped (a world built only to test routes takes no step)."""
        return [f["orders"] for f in self.fights if f["steps"] > 0]


def test_L2_command_one_order_per_side_at_tick_0_and_nothing_after(planted, tmp_path, monkeypatch):
    """DEC-one-click-2026-11-18 / round6.md fixed point 1 ('It gives each fight the orders its layout names and nothing more'): through the lab's engine wrapper the command's fights get exactly the
    orders `run.fight` gives the same layouts today, all before the first step: L-9102 (`both_same_point`) two attack-moves, one per side of eight units, to one point; L-9101 (`hold:A`) one
    attack-move for side B of eight units; no other order method is called and none after tick 0. Red today: no module."""
    rec = _Orders(monkeypatch)
    _main(_manifest_file(tmp_path, _row("L-9102", "A"), _row("L-9101", "draw")), planted)
    regression_orders = rec.played()
    from scripts.skilllab.arena import run, snapshot
    rec.fights.clear()
    for lid in ("L-9102", "L-9101"):
        with open(planted / (lid + ".toml"), "rb") as f:
            run.fight(tomllib.load(f), 1, "off", snapshot.CAP_SECONDS)
    today = rec.played()
    assert len(regression_orders) == 2, "the command played %d fights, not 2" % len(regression_orders)
    assert regression_orders == today
    both, hold = regression_orders
    assert [(name, n, steps) for name, n, _, steps in both] == [("order_attack_move", 8, 0), ("order_attack_move", 8, 0)] and both[0][2] == both[1][2]
    assert [(name, n, steps) for name, n, _, steps in hold] == [("order_attack_move", 8, 0)]


def test_L2_command_prints_one_line_per_row_in_manifest_order(planted, tmp_path):
    """L2 'prints one line per fight': a manifest of three rows (wipe, draw, wipe) gives three lines naming L-9102, L-9101, L-9103 in that order, one each, and the exit is non-zero (the middle
    one is a draw). Red today: no module."""
    code, out = _main(_manifest_file(tmp_path, _row("L-9102", "A"), _row("L-9101", "draw"), _row("L-9103", "A")), planted)
    named = [re.search(r"L-910\d", ln).group(0) for ln in out.splitlines() if re.search(r"L-910\d", ln)]
    assert named == ["L-9102", "L-9101", "L-9103"] and code != 0, (code, out)


# ---- a row's control runs as a second fight (round6.md L2: "the control runs as a second fight of the row, on its own line, held to the same two conditions; the expected winner is compared for the fight only")

def _control_row(layout, expected, sight, control, stage):
    return ('[[fight]]\nstage = %d\nlayout = "%s"\nsight = "%s"\ncontrol = "%s"\nexpected_winner = "%s"\ndecision = "%s"\n\n' % (stage, layout, sight, control, expected, DEC3 if stage == 3 else DEC4))


def _by_name(out):
    """{first word of the line: line} of the fight lines of `out` (a fight line starts with the fight's id; the summary line starts with `regression:`)."""
    return {ln.split()[0]: ln for ln in out.splitlines() if re.match(r"L-\d{4}", ln)}


@pytest.fixture(scope="module")
def planted_cover(tmp_path_factory):
    """A catalogue with L-9201, the cover fixture of h063_fixtures (a box between two blocks of eight Vanguards, `both_same_point`): the fight ends by wipe with side B winning 0:4, its ground
    control (the twin with the features emptied) by wipe with side A winning 2:0."""
    import h063_fixtures as fx
    cat = tmp_path_factory.mktemp("catalogue_cover")
    lay, _ = fx.planar("cover", "L-9201")
    fx.write(lay, cat)
    return cat


@pytest.fixture(scope="module")
def controls_run(planted, planted_cover, tmp_path_factory):
    """One run of a manifest of two rows, each with a control: L-9201 (stage 3, sight off, control ground, expects B) and L-9102 (stage 4, sight on, control sight, expects A)."""
    work = tmp_path_factory.mktemp("controls")
    (work / "L-9201.toml").write_text((planted_cover / "L-9201.toml").read_text())
    (work / "L-9102.toml").write_text((planted / "L-9102.toml").read_text())
    manifest = _manifest_file(work, _control_row("L-9201", "B", "off", "ground", 3), _control_row("L-9102", "A", "on", "sight", 4))
    code, out = _main(manifest, work)
    return code, out


def test_L2_command_a_ground_control_runs_as_a_second_fight_on_its_own_line(controls_run):
    """L2 'a row of stage 3 ... names a control (`ground` ...): the control runs as a second fight of the row, on its own line': the row L-9201 prints two lines, the fight and then `L-9201-control`,
    right after it, each with its own result (the fight ends 0:4 with B the winner, the control with the features emptied 2:0 with A the winner, both by wipe, both at sight off, no checker report);
    the exit is 0 because both fights pass. Red today only if the control is not run."""
    code, out = controls_run
    lines = [ln.split()[0] for ln in out.splitlines() if ln.startswith("L-")]
    assert lines.index("L-9201-control") == lines.index("L-9201") + 1, out
    fight, control = _by_name(out)["L-9201"], _by_name(out)["L-9201-control"]
    assert [_field(fight, k) for k in ("end", "winner", "survivors", "sight", "checker")] == ["wipe", "B", "0:4", "off", "none"], fight
    assert [_field(control, k) for k in ("end", "winner", "survivors", "sight", "checker")] == ["wipe", "A", "2:0", "off", "none"], control
    assert code == 0, out


def test_L2_command_a_sight_control_runs_as_a_second_fight_on_its_own_line(controls_run):
    """L2 'a row of stage ... 4 names a control (... `sight`: targeting by sight off): the control runs as a second fight of the row, on its own line': the row L-9102 at sight on prints two
    lines, the fight (`sight=on`) and then `L-9102-control` (`sight=off`: targeting by sight is off in the control), each ending by wipe with no checker report."""
    code, out = controls_run
    names = [ln.split()[0] for ln in out.splitlines() if ln.startswith("L-")]
    assert names.index("L-9102-control") == names.index("L-9102") + 1 and names.count("L-9102") == 1, out
    fight, control = _by_name(out)["L-9102"], _by_name(out)["L-9102-control"]
    assert (_field(fight, "sight"), _field(fight, "end"), _field(fight, "checker")) == ("on", "wipe", "none"), fight
    assert (_field(control, "sight"), _field(control, "end"), _field(control, "checker")) == ("off", "wipe", "none"), control
    assert code == 0, out


def test_L2_command_the_expected_winner_is_compared_for_the_fight_only(controls_run):
    """L2 'the expected winner is compared for the fight only': L-9201 expects B; its fight is won by B (agree=yes) and its control by A, which would read agree=no if it were compared; the control's
    `agree` is `-`. L-9102 expects A and both are won by A (agree=yes for the fight, `-` for the control, which would read yes)."""
    _, out = controls_run
    lines = _by_name(out)
    assert (_field(lines["L-9201"], "agree"), _field(lines["L-9201-control"], "agree")) == ("yes", "-"), (lines["L-9201"], lines["L-9201-control"])
    assert (_field(lines["L-9102"], "agree"), _field(lines["L-9102-control"], "agree")) == ("yes", "-"), (lines["L-9102"], lines["L-9102-control"])


def test_L2_command_a_control_that_ends_with_both_sides_alive_fails_the_run_though_the_fight_passes(planted, tmp_path, monkeypatch):
    """L2 'held to the same two conditions': the row L-9102 (stage 4, control sight): its fight ends by wipe, and its control, given a 10 s cap by a wrapper of `run.fight` on the row's second
    call only, ends at the cap with both sides alive. The control's line says DRAW (not the fight's), and the exit is non-zero."""
    from scripts.skilllab.arena import run
    real, calls = run.fight, []

    def fight(layout, seed, sight, cap_seconds, *args, **kwargs):
        calls.append(sight)
        return real(layout, seed, sight, 10 if len(calls) == 2 else cap_seconds, *args, **kwargs)
    monkeypatch.setattr(run, "fight", fight)
    code, out = _main(_manifest_file(tmp_path, _control_row("L-9102", "A", "on", "sight", 4)), planted)
    lines = _by_name(out)
    assert calls == ["on", "control"], calls
    assert "DRAW" not in lines["L-9102"] and _field(lines["L-9102"], "end") == "wipe", lines["L-9102"]
    assert "DRAW" in lines["L-9102-control"] and _field(lines["L-9102-control"], "end") != "wipe", lines["L-9102-control"]
    assert code != 0, out


def _plant_reports(monkeypatch, reports, only_fight=None):
    """Plant checker reports through the Monitor, the seam `run.fight` reads its verdict from: `reports` is [(tick, rule)], each added to `Monitor.violations` (unit 1) when the monitor of the fight
    reaches that tick; `only_fight` is the 1-based number of the fight to plant in (the Monitors are built one per fight, in play order), None for every fight. A planted report is what the
    checker would have kept: the fight document keeps the first `invariants.KEEP` of them by (tick, rule, unit). (A real fault, `Engine.step` moving a unit 300 wu in tick 5 as the checker test above
    does, is reported as `continuity` in a sight-off fight but not in a walking one: tried on L-9102 at sight on, 300, -300 and 1000 wu.)"""
    from scripts.skilllab import invariants
    real_init, real_after, built = invariants.Monitor.__init__, invariants.Monitor.after_step, []

    def init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        built.append(self)
        self._planted_number = len(built)

    def after_step(self):
        real_after(self)
        if only_fight in (None, self._planted_number):
            for tick, rule in reports:
                if tick == self.tick:
                    self.violations.append({"rule": rule, "tick": tick, "unit": 1, "detail": "planted"})
    monkeypatch.setattr(invariants.Monitor, "__init__", init)
    monkeypatch.setattr(invariants.Monitor, "after_step", after_step)
    return built


def test_L2_command_a_control_that_carries_a_checker_report_fails_the_run_though_the_fight_passes(planted, tmp_path, monkeypatch):
    """L2 'held to the same two conditions': the row L-9102 (stage 4, control sight), with one checker report (`continuity`, tick 5) planted in the SECOND fight only (the control). The fight's
    line says checker=none, the control's line names continuity, and the exit is non-zero although both fights end by wipe."""
    built = _plant_reports(monkeypatch, [(5, "continuity")], only_fight=2)
    code, out = _main(_manifest_file(tmp_path, _control_row("L-9102", "A", "on", "sight", 4)), planted)
    lines = _by_name(out)
    assert len(built) == 2, built
    assert (_field(lines["L-9102"], "checker"), _field(lines["L-9102"], "end")) == ("none", "wipe"), lines["L-9102"]
    assert (_field(lines["L-9102-control"], "checker"), _field(lines["L-9102-control"], "end")) == ("continuity", "wipe"), lines["L-9102-control"]
    assert code != 0, out


# ---- every checker report is read

@pytest.mark.parametrize("late_tick", [21, 900])
def test_L2_command_every_checker_report_is_read_not_only_the_first_twenty(planted, tmp_path, monkeypatch, late_tick):
    """L2 'prints one line per fight (... checker reports)': the fight document keeps only the first 20 reports (`invariants.KEEP`), so a rule first broken after them must still reach the line.
    The row L-9102 (sight off, ends by wipe), with 20 reports of `continuity` planted at ticks 1 to 20 and one of `R-096-08` at tick `late_tick` (the 21st report by tick, and one far
    later): the line names both rule ids and the exit is non-zero. Red today: `regression._play` reads `doc["violations"]`, which `run._document` cuts at 20, so the line says
    checker=continuity and `R-096-08` is missing."""
    _plant_reports(monkeypatch, [(t, "continuity") for t in range(1, 21)] + [(late_tick, "R-096-08")])
    code, out = _main(_manifest_file(tmp_path, _row("L-9102", "A")), planted)
    (line,) = _lines_of(out, "L-9102")
    assert _field(line, "end") == "wipe" and code != 0, (code, out)
    assert sorted(_field(line, "checker").split(",")) == ["R-096-08", "continuity"], line


@SLOW
def test_L2_slow_the_real_manifest_runs_to_elimination_with_no_checker_report():
    """round6.md L2 proof, the slow test: `python -m scripts.skilllab.arena.regression` on the real manifest exits 0 (every approved fight ends by elimination under its one order per side, the
    checker reports nothing). No list of expected draws. RED until both Round 6 tracks are merged (stage 1 L-0054 ends in a stand-off at tick 11,020 on the Round 5 engine; SIT-0105 to SIT-0107
    do not convert; the overlap predicate reports until E3): that red is the signal. The test writer did not run it. SLOW = OM_LAB_SLOW=1, as the lab's other slow tests."""
    done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.regression"], cwd=str(ROOT), capture_output=True, text=True, timeout=3000)
    assert done.returncode == 0, "exit %d\n%s\n%s" % (done.returncode, done.stdout[-3000:], done.stderr[-1500:])


# ------------------------------------------------------------------------------------------------------------ the sweep

def test_L2_the_sweep_reads_its_fights_from_the_manifest_and_keeps_the_rejection_rule_on():
    """L2: 'The sweep ... reads the manifest instead of its own layout lists and no longer switches the catalogue's rejection rule off.' sweep.py names approved.toml, no longer has its own id
    lists (LEGACY, OPEN, FEAT, HEAVY) and never sets ALLOW_R6 (inv_check's switch for the catalogue rule R6). Red today: it has all four lists and `ALLOW_R6 = True`."""
    src = SWEEP.read_text()
    assert "approved.toml" in src
    assert not re.search(r"^\s*(LEGACY|OPEN|FEAT|HEAVY)\s*=", src, re.M), "sweep.py still carries its own layout lists"
    assert not re.search(r"ALLOW_R6\s*=\s*True", src), "sweep.py still switches the catalogue's rejection rule off"


def test_L2_the_sweeps_tasks_are_the_manifests_fights_and_no_others():
    """L2: running `tasks()` of the sweep names every layout of the manifest and no catalogue layout outside it (a task is read by the `L-nnnn` ids in it, whatever its shape; a converted situation
    is an id of L-0101 to L-0109). Red today: 'tasks' lists 67 catalogue layouts of which most are not in the manifest."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("om_r6_sweep", SWEEP)
    sweep = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SWEEP.parent))
    try:
        spec.loader.exec_module(sweep)
        tasks = sweep.tasks()
    finally:
        sys.path.remove(str(SWEEP.parent))
    named = {i for t in tasks for i in re.findall(r"L-\d{4}", repr(t))}
    approved = {f["layout"] for f in _manifest() if "layout" in f}
    converted = {"L-%04d" % n for n in range(101, 110)}
    assert approved <= named and named <= approved | converted, (sorted(approved - named), sorted(named - approved - converted))


# ------------------------------------------------------------------------------------------------------------ L5: a quiet end with every order finished is `apart`

# round6.md L5 / DEC-formation-kept-2026-11-19 / docs/stories/H-040.md "Orders and fight end", the command's half (the runner's half is tests/skilllab/arena/test_run_apart_end.py, which also says
# which fixtures stand for which state): "The regression command prints `APART` on the line and does not fail on it; a quiet end of any other kind ... stays `silence` with `stall` true and fails, as
# does the time cap." The word APART stands on the line as DRAW stands on a draw's; the `end=` key reads `apart`; the line's `winner=` word for an apart end is `none` (L5).
# An apart end needs a fight in which a shot was fired (2026-11-19): the fixtures plant one as test_run_apart_end.plant_shot does.
# The planted catalogue's L-9101 (`hold:A`, the stall fixture) is the quiet fight (no unit holds an order or a target at tick 200, the enemies 820 wu apart; apart with a shot planted, silence without); the state of a unit that still holds an
# order is planted as test_run_apart_end.py plants it, by wrapping `Engine.unit_destination`.

def test_L5_command_an_apart_end_prints_APART_and_is_not_counted_as_a_failure(planted, tmp_path, monkeypatch):
    """L5: the stall fixture (L-9101, `hold:A`, 8:8 at tick 200, nobody holding an order, the nearest enemies about 820 wu apart) with a shot planted (`test_run_apart_end.plant_shot`: the hit points of
    unit 1 drop at tick 1, the seam `run.fight` reads; the sides fought) is an apart end: its one line says end=apart, survivors=8:8, checker=none, winner=none (the line's winner word for an apart end),
    carries the word APART and not DRAW; with a wipe row beside it the command exits 0 and its summary says 0 failed. Red today: the line says end=silence and DRAW, and the exit is 1."""
    plant_shot(monkeypatch)
    code, out = _main(_manifest_file(tmp_path, _row("L-9101", "draw"), _row("L-9102", "A")), planted)
    (line,) = _lines_of(out, "L-9101")
    assert (_field(line, "end"), _field(line, "survivors"), _field(line, "checker"), _field(line, "winner")) == ("apart", "8:8", "none", "none"), line
    assert "APART" in line and "DRAW" not in line, line
    assert code == 0 and "0 failed" in out, (code, out)


def test_L5_command_mirror_the_same_fight_with_no_shot_fired_is_silence_and_fails(planted, tmp_path):
    """L5 ("A fight in which no shot was ever fired is never this kind ... it stays `silence`"): the same row, L-9101, with nothing planted: no shot is ever fired, so the end is `silence`, the line says
    DRAW with winner=stall and not APART, and the exit is non-zero with 1 failed in the summary. Green today and must stay green."""
    code, out = _main(_manifest_file(tmp_path, _row("L-9101", "draw")), planted)
    (line,) = _lines_of(out, "L-9101")
    assert (_field(line, "end"), _field(line, "winner")) == ("silence", "stall") and "DRAW" in line and "APART" not in line, line
    assert code != 0 and "1 failed" in out, (code, out)


def test_L5_command_a_silence_end_with_both_sides_alive_still_fails_and_prints_DRAW(planted, tmp_path, monkeypatch):
    """L5: the same fight with one unit (id 1) still holding a destination as far as the engine says (`Engine.unit_destination` answers a point for it): the quiet end is `silence`, the line says DRAW and not
    APART, and the exit is non-zero with 1 failed in the summary. Green today (silence with both alive is a failure) and must stay green."""
    real = Engine.unit_destination
    monkeypatch.setattr(Engine, "unit_destination", lambda self, w, u: (2000.0, 2600.0) if u == 1 else real(self, w, u))
    code, out = _main(_manifest_file(tmp_path, _row("L-9101", "draw")), planted)
    (line,) = _lines_of(out, "L-9101")
    assert _field(line, "end") == "silence" and "DRAW" in line and "APART" not in line, line
    assert code != 0 and "1 failed" in out, (code, out)


def test_L5_command_the_time_cap_still_fails_even_when_the_fight_was_quiet(planted, tmp_path, monkeypatch):
    """L5: the same fight with the cap cut to 5 s (`snapshot.CAP_SECONDS`, which the command reads each fight; tick 100, before the 10 s silence window can close): the end is `cap`, the line says DRAW and
    not APART, the exit is non-zero. Green today and must stay green."""
    from scripts.skilllab.arena import snapshot
    monkeypatch.setattr(snapshot, "CAP_SECONDS", 5)
    code, out = _main(_manifest_file(tmp_path, _row("L-9101", "draw")), planted)
    (line,) = _lines_of(out, "L-9101")
    assert _field(line, "end") == "cap" and "DRAW" in line and "APART" not in line, line
    assert code != 0, (code, out)
