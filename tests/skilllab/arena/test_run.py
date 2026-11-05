# spec: docs/stories/H-040.md (Part 2: arena runner); Flag client, Scene res://scenes/proto/fight_replay/fight_replay.tscn (part 3's scene; this file is the runner only)
"""H-040 part 2, the arena runner: `python3 -m scripts.skilllab.arena.run --layout <toml> --seed <int> --out <dir> [--sight off|on] [--cap-seconds 600]`.

Story lines proved here (docs/stories/H-040.md "Part 2: arena runner"):
  "Reads the layout (`tomllib`), refuses one failing `check_layout` (prints `REJECT <id> <rule>`, exit 2)."
  "Writes `<out>/<id>-s<seed>.fight.json` through `snapshot.write`, and appends one row to `<out>/results.md` (`| id | a:b | predict | winner | survivors | ticks | agree |`)."
  "Prints `FIGHT <id> seed <n> winner <A|B|draw> ticks <t> agree <yes|no>` and exits 0."
  "Imports only `scripts.skilllab.engine`, `scripts.skilllab.fight` (the helpers named), `scripts.skilllab.catalogue.produce.check_layout`,
   `scripts.skilllab.arena.snapshot`. Nothing from the "not used before stage 6" list (...trim_report_2026-10-31.md); the test greps the module's imports."
  "Steps the engine, reading `unit_pos`, `unit_hp`, `unit_facing`, `unit_target`, `unit_alive`, `unit_layer` at each tick in `snapshot.frame_ticks(...)` and at the end;
   stops when one side has no survivors or at the cap."
  Tests line: "a 2:2 Vanguard layout fixture runs to a result under the cap, the file validates, `alive` in the last frame matches `survivors`; the same layout and
   seed twice give byte-identical files; a 1:1 fixture with the cap at 1 s writes `capped: true` and `winner: "draw"`; ... a layout fixture breaking R2 gives `REJECT`
   and no file; the import grep."
DEC-lab-stage1-floor-2026-10-31: "sight off by `OM_TP_TARGET_BY_SIGHT` 0, cap DRAFT-fight-cap 600 s".

DEVIATION from the story's fixture sizes, said in the report: H-025 rule R4 (`scripts/skilllab/catalogue/rules.toml`, min = 8, max = 256, Westley's "8 to 256 a
side") makes a 2:2 or 1:1 layout fail `check_layout`, and the runner must refuse a layout that fails it. The fixtures here are therefore the smallest legal ones:
8:12 for the "2:2" run (unequal so the fight has a decided winner; 8:8 Vanguards annihilate each other and the result is a draw), 8:8 for the "1:1" cap run.
No number is invented: the cap is the story's `--cap-seconds 1`; every threshold is the story's DRAFT name (DRAFT-fight-cap, DRAFT-snapshot-seconds, DRAFT-winner).

Premises dumped (checked on the base 034489ed, 2026-10-31):
  - `scripts/skilllab/engine.py` builds its own library with `cc` into a temp dir on first `Engine()` (`build_library`), loaded by ctypes; `make` is not needed for these tests.
  - Engine API used: `Engine()`, `new_world(seed)`, `type_id("Vanguard")` = 2, `spawn(w, type_id, faction, x, y, layer)` (no facing argument; the C header has
    `om_unit_set_facing` but engine.py does not bind it), `param_id("OM_TP_TARGET_BY_SIGHT")`, `set_param`, `order_attack_move(w, ids, x, y)`, `step`, `unit_pos`,
    `unit_hp`, `unit_facing`, `unit_target`, `unit_alive`, `unit_layer`.
  - Vanguard stats: max_hp 500.0, attack_range 300.0, speed 80.0. Fixture 8:12 at x 1800 (A, facing east) and x 2200 (B, facing west), pitch 40, sight off, both
    attack-move to the enemy centroid: B wins at tick 1304 with 0 against 9 left (a direct Engine run, the control below). 8:8 on the same recipe ends 0:0 at tick 3214.
  - `snapshot.frame_ticks(last_tick, 20)` and `snapshot.example()` as landed in H-039; `produce.check_layout(layout, presets, rules)` returns the rule ids violated.
The runner module is imported through no top-level import, so while it is missing the runner tests fail one by one for the missing-module reason and the
control tests (test_control_*) still run green."""
import ast
import importlib.util
import json
import math
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.arena import snapshot  # noqa: E402
from scripts.skilllab.catalogue import produce  # noqa: E402

RUN_MODULE = "scripts.skilllab.arena.run"
RUN_FILE = ROOT / "scripts" / "skilllab" / "arena" / "run.py"
TRIM_REPORT = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "trim_report_2026-10-31.md"
TICK_RATE = 20
PITCH = 40.0   # H-025 round two block pitch (DRAFT-block-pitch); R2 min spacing is 30

# Imports the story allows the runner (scripts.* only; the standard library is checked separately).
ALLOWED = {"scripts.skilllab.engine", "scripts.skilllab.fight", "scripts.skilllab.catalogue.produce", "scripts.skilllab.arena.snapshot",
           "scripts.skilllab.arena.rate",
           "scripts.skilllab.arena.features"}   # rate: H-053 Interfaces 1, run.py --seeds calls rate.rate; features: H-063 Files list, layout features to engine blocking calls

# The trim report's "Not needed for that answer" paragraph names these as prose; each is mapped here to the module that holds it (mapping by the Architect's
# words, one comment per row). The ALLOWED check above is the strict one and covers all of these; this list only gives the failure a name.
NOT_USED_BEFORE_STAGE_6 = {
    "conditions": "Conditions C0 to C9 and pass marks",
    "profile": "The skill-stacking profile",
    "plays": "The fourteen plays",
    "plays_space": "five-layer space plays",
    "skills": "the five skills of the plays",
    "sweep": "The eight knob-sweep families",
    "search": "The ping search scene",
    "search_policies": "The ping search scene (policies)",
    "search_batch": "The ping search scene (batch)",
    "tree": "decision tree",
    "transfer": "transfer",
    "guard": "guard",
    "mapreport": "mapreport",
    "sample": "Layout run 1's sampler",
}


# ---------------------------------------------------------------- fixtures: layouts in the H-025 TOML schema

def _block(n, x0, y0, step_x, cols=4):
    """n Vanguard rows in a block of `cols` columns, pitch 40, rows stepping step_x from x0."""
    return [{"role": "Vanguard", "x": x0 + (i // cols) * step_x * PITCH, "y": y0 + (i % cols) * PITCH, "facing": 0.0, "layer": 0} for i in range(n)]


def make_layout(layout_id, na, nb, predict, gap_x=400.0):
    """A small_flat open-field layout, Vanguard both sides, A at x 2000 - gap_x/2 facing east, B at x 2000 + gap_x/2 facing west."""
    a = _block(na, 2000.0 - gap_x / 2, 1980.0, -1.0)
    b = _block(nb, 2000.0 + gap_x / 2, 1980.0, 1.0)
    for row in b:
        row["facing"] = round(math.pi, 4)
    return {"id": layout_id, "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": predict,
            "predict_why": "Test fixture, no prediction beyond the numbers.", "verdict": "", "feedback": "",
            "side_a": {"headcount": na, "units": a}, "side_b": {"headcount": nb, "units": b}}


def write_layout(layout, directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (layout["id"] + ".toml")
    path.write_text(produce.dump_toml(layout))
    return path


def r2_breaker(layout_id):
    """The 8:12 fixture with side A's second unit 10 wu from its first (R2 min_spacing 30)."""
    layout = make_layout(layout_id, 8, 12, "B")
    layout["side_a"]["units"][1]["x"] = layout["side_a"]["units"][0]["x"] + 10.0
    layout["side_a"]["units"][1]["y"] = layout["side_a"]["units"][0]["y"]
    return layout


def run_cli(layout_path, out, seed=1, *extra):
    """Run the runner as a CLI from the repo root; the missing module is the one red reason while part 2 is unbuilt."""
    if importlib.util.find_spec(RUN_MODULE) is None:
        pytest.fail("scripts/skilllab/arena/run.py is missing: H-040 part 2 (arena runner) is not built")
    cmd = [sys.executable, "-m", RUN_MODULE, "--layout", str(layout_path), "--seed", str(seed), "--out", str(out), *extra]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)


def fight_file(out, layout_id, seed=1):
    return Path(out) / ("%s-s%d.fight.json" % (layout_id, seed))


@pytest.fixture(scope="module")
def main_run(tmp_path_factory):
    """The 8:12 fixture run once, seed 1, into out_1; the shared evidence for the result tests. A missing runner is recorded, not raised, so each
    dependent test fails (not errors) for the missing-module reason."""
    base = tmp_path_factory.mktemp("run_main")
    layout = make_layout("L-9001", 8, 12, "B")
    path = write_layout(layout, base / "layouts")
    out = base / "out_1"
    run = {"layout": layout, "path": path, "out": out, "base": base, "proc": None, "missing": None}
    try:
        run["proc"] = run_cli(path, out, 1)
    except pytest.fail.Exception as exc:
        run["missing"] = str(exc)
    return run


def _doc(run):
    """The main run's fight file read through `snapshot.read` (which validates: "the file validates")."""
    if run["missing"]:
        pytest.fail(run["missing"])
    proc = run["proc"]
    assert proc.returncode == 0, proc.stderr[-2000:] + proc.stdout[-500:]
    return snapshot.read(fight_file(run["out"], "L-9001"))


# ---------------------------------------------------------------- positive controls (green today)

def test_control_fixtures_are_legal_and_the_breaker_breaks_only_r2():
    """Control: the fixture layouts pass check_layout (R1 to R5), the R2 breaker fails with exactly R2, so a REJECT or a pass later is the runner's doing."""
    pre, rul = produce.presets(), produce.rules()
    assert produce.check_layout(make_layout("L-9001", 8, 12, "B"), pre, rul) == []
    assert produce.check_layout(make_layout("L-9002", 8, 8, "A", gap_x=2000.0), pre, rul) == []
    assert produce.check_layout(r2_breaker("L-9003"), pre, rul) == ["R2"]
    # the TOML round trip keeps the layout legal and keeps the fields the runner reads
    loaded = tomllib.loads(produce.dump_toml(make_layout("L-9001", 8, 12, "B")))
    assert loaded["id"] == "L-9001" and loaded["predict"] == "B" and loaded["side_a"]["headcount"] == 8 and len(loaded["side_b"]["units"]) == 12
    assert produce.check_layout(loaded, pre, rul) == []


def test_control_snapshot_example_validates():
    """Control: the H-039 contract the runner writes through is on the tree and its fixture is valid."""
    assert snapshot.validate(snapshot.example()) == []
    assert snapshot.SCHEMA == "om-fight-1" and snapshot.CAP_SECONDS == 600


def test_control_engine_runs_the_fixture_recipe_to_a_decided_result():
    """Control: the C sim loads through engine.py and the story's recipe (spawn at the layout's x, y, layer; sight off; both sides attack-move to the enemy
    centroid) on the 8:12 fixture ends under the 12,000 tick cap with one side wiped out, so a capped or undecided runner result later is the runner's doing."""
    from scripts.skilllab.engine import Engine
    layout = make_layout("L-9001", 8, 12, "B")
    e = Engine()
    w = e.new_world(1)
    try:
        e.disable_abilities(w)
        e.set_param(w, e.param_id("OM_TP_TARGET_BY_SIGHT"), 0)
        vanguard = e.type_id("Vanguard")
        ids = {}
        for faction, key in ((0, "side_a"), (1, "side_b")):
            ids[faction] = [e.spawn(w, vanguard, faction, u["x"], u["y"], u["layer"]) for u in layout[key]["units"]]
        assert all(ids[0]) and all(ids[1]), "a spawn returned unit id 0"
        for faction in (0, 1):
            first = layout["side_a" if faction == 0 else "side_b"]["units"][0]
            assert e.unit_pos(w, ids[faction][0]) == (first["x"], first["y"])
        centroid = {f: (sum(e.unit_pos(w, u)[0] for u in ids[f]) / len(ids[f]), sum(e.unit_pos(w, u)[1] for u in ids[f]) / len(ids[f])) for f in (0, 1)}
        e.order_attack_move(w, ids[0], *centroid[1])
        e.order_attack_move(w, ids[1], *centroid[0])
        alive = (8, 12)
        for tick in range(1, 12000 + 1):
            e.step(w)
            alive = tuple(sum(e.unit_alive(w, u) for u in ids[f]) for f in (0, 1))
            if min(alive) == 0:
                break
        assert min(alive) == 0 and tick < 12000, "premise failed: fixture fight did not end under the cap (alive %r at tick %d)" % (alive, tick)
    finally:
        e.free_world(w)


# ---------------------------------------------------------------- the runner: result, file, determinism

def test_run_prints_fight_line_and_exits_0(main_run):
    """S-H-040 part 2: "Prints `FIGHT <id> seed <n> winner <A|B|draw> ticks <t> agree <yes|no>` and exits 0.\""""
    res = _doc(main_run)["result"]
    proc = main_run["proc"]
    want = "FIGHT L-9001 seed 1 winner %s ticks %d agree %s" % (res["winner"], res["ticks"], "yes" if res["agree"] else "no")
    assert want in [line.strip() for line in proc.stdout.splitlines()], "stdout was %r, wanted the line %r" % (proc.stdout, want)


def test_run_fixture_reaches_a_result_under_the_cap_and_the_file_validates(main_run):
    """S-H-040 part 2: "a 2:2 Vanguard layout fixture runs to a result under the cap, the file validates" (the file is read through `snapshot.read`,
    which validates; 8:12 stands for 2:2, see the module docstring). DRAFT-winner: "the side with survivors when the other has none; both alive at the cap,
    or both dead, is `draw`." DRAFT-fight-cap: 600 s of sim time, 12,000 ticks at 20."""
    doc = _doc(main_run)
    res = doc["result"]
    assert fight_file(main_run["out"], "L-9001").name == "L-9001-s1.fight.json"
    assert doc["layout_id"] == "L-9001" and doc["seed"] == 1 and doc["tick_rate"] == TICK_RATE and doc["sight"] == "off"
    assert res["capped"] is False and 0 < res["ticks"] < snapshot.CAP_SECONDS * TICK_RATE
    a, b = res["survivors"]
    assert min(a, b) == 0 or res["capped"], "an uncapped fight ends when one side has no survivors"
    want_winner = "A" if (a > 0 and b == 0) else "B" if (b > 0 and a == 0) else "draw"
    assert res["winner"] == want_winner
    assert res["predict"] == "B" and res["agree"] == (res["winner"] == "B")


def test_run_alive_in_the_last_frame_matches_survivors(main_run):
    """S-H-040 part 2: "`alive` in the last frame matches `survivors`"; the last frame is the last tick simulated (H-039: "Always includes tick 0 and the last
    tick simulated"), and the per-unit `alive` flags agree with the pair; a dead unit stays in the frame with hp 0.0."""
    doc = _doc(main_run)
    res, last = doc["result"], doc["frames"][-1]
    assert last["tick"] == res["ticks"]
    assert last["alive"] == res["survivors"]
    for side, n in (("A", last["alive"][0]), ("B", last["alive"][1])):
        rows = [u for u in last["units"] if u["side"] == side]
        assert sum(1 for u in rows if u["alive"]) == n
        assert all(u["hp"] == 0.0 for u in rows if not u["alive"]) and all(u["hp"] > 0.0 for u in rows if u["alive"])
    assert len(last["units"]) == 20, "dead units stay in every frame (H-039)"


def test_run_frames_are_the_snapshot_frame_ticks(main_run):
    """S-H-040 part 2: "reading ... at each tick in `snapshot.frame_ticks(...)` and at the end"; DRAFT-snapshot-seconds: a frame every 5 s of sim time (100 ticks
    at 20), doubling to keep at most DRAFT-snapshot-count frames."""
    doc = _doc(main_run)
    ticks = [f["tick"] for f in doc["frames"]]
    assert ticks == snapshot.frame_ticks(doc["result"]["ticks"], TICK_RATE)
    assert doc["snapshot_every"] % (5 * TICK_RATE) == 0 and doc["snapshot_every"] > 0
    assert ticks[0] == 0 and len(ticks) <= snapshot.MAX_FRAMES


def test_run_frame_0_stands_where_the_layout_put_the_units(main_run):
    """S-H-040 part 2: "`spawn` per layout row at the row's x, y, layer ... (positions come from the layout, never from `formations.place`)": frame 0 holds
    the layout's rows, Vanguard, layer 0, every unit alive at full health, side A the layout's side_a, ids ascending."""
    layout, frame = main_run["layout"], _doc(main_run)["frames"][0]
    assert frame["tick"] == 0 and frame["alive"] == [8, 12] and len(frame["units"]) == 20
    for side, key in (("A", "side_a"), ("B", "side_b")):
        got = sorted((round(u["x"], 2), round(u["y"], 2)) for u in frame["units"] if u["side"] == side)
        want = sorted((round(r["x"], 2), round(r["y"], 2)) for r in layout[key]["units"])
        assert got == want, "side %s positions differ from the layout rows" % side
    assert all(u["role"] == "Vanguard" and u["layer"] == 0 and u["alive"] and u["hp"] > 0 for u in frame["units"])
    ids = [u["id"] for u in frame["units"]]
    assert ids == sorted(ids) and len(set(ids)) == 20


def test_run_units_fight_and_record_their_targets(main_run):
    """S-H-040 part 2: "reading `unit_pos`, `unit_hp`, `unit_facing`, `unit_target`, `unit_alive`, `unit_layer`", both sides attack-move to the enemy centroid
    at tick 0, sight off (a target is usable whether or not the side sees it, DEC-lab-stage1-floor-2026-10-31): some unit in some frame has a target, every
    target names a unit of the file, and the units moved from where they stood."""
    frames = _doc(main_run)["frames"]
    ids = {u["id"] for u in frames[0]["units"]}
    targets = [u["target"] for f in frames for u in f["units"] if u["target"] is not None]
    assert targets, "no unit ever had a target: the attack-move order did not engage"
    assert set(targets) <= ids
    first = {u["id"]: (u["x"], u["y"]) for u in frames[0]["units"]}
    assert any((u["x"], u["y"]) != first[u["id"]] for u in frames[-1]["units"] if u["alive"]), "no surviving unit moved"
    assert any(u["hp"] < 500.0 for f in frames for u in f["units"]), "no unit took damage"


def test_run_same_layout_and_seed_twice_give_byte_identical_files(main_run, tmp_path):
    """S-H-040 part 2 / CLAUDE.md "Determinism is a contract": "the same layout and seed twice give byte-identical files" (and the same stdout)."""
    _doc(main_run)
    out_2 = tmp_path / "out_2"
    second = run_cli(main_run["path"], out_2, 1)
    assert second.returncode == 0, second.stderr[-2000:]
    one = fight_file(main_run["out"], "L-9001").read_bytes()
    two = fight_file(out_2, "L-9001").read_bytes()
    assert one == two
    assert main_run["proc"].stdout == second.stdout


# ---------------------------------------------------------------- the cap

def test_run_cap_of_one_second_writes_a_capped_draw(tmp_path):
    """S-H-040 part 2: "a 1:1 fixture with the cap at 1 s writes `capped: true` and `winner: "draw"`" (8:8, the smallest legal pair, 2000 wu apart so nobody
    fights in the second); H-039 DRAFT-winner: "both alive at the cap ... is `draw`", `ticks`: last tick simulated = the cap, 1 s = 20 ticks."""
    layout = make_layout("L-9002", 8, 8, "A", gap_x=2000.0)
    path = write_layout(layout, tmp_path / "layouts")
    proc = run_cli(path, tmp_path / "out", 1, "--cap-seconds", "1")
    assert proc.returncode == 0, proc.stderr[-2000:]
    doc = snapshot.read(fight_file(tmp_path / "out", "L-9002"))
    res = doc["result"]
    assert res["capped"] is True and res["winner"] == "draw"
    assert res["ticks"] == 1 * TICK_RATE and res["survivors"] == [8, 8]
    assert doc["frames"][-1]["tick"] == res["ticks"] and doc["frames"][-1]["alive"] == [8, 8]
    assert res["predict"] == "A" and res["agree"] is False
    assert "FIGHT L-9002 seed 1 winner draw ticks %d agree no" % res["ticks"] in [line.strip() for line in proc.stdout.splitlines()]


def test_run_sight_flag_is_written_to_the_file(tmp_path):
    """S-H-040 part 2: `[--sight off|on]`; H-039: "`sight`: `"off"` or `"on"`" ("off" is the default, stage 1)."""
    layout = make_layout("L-9002", 8, 8, "A", gap_x=2000.0)
    path = write_layout(layout, tmp_path / "layouts")
    proc = run_cli(path, tmp_path / "on", 1, "--cap-seconds", "1", "--sight", "on")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert snapshot.read(fight_file(tmp_path / "on", "L-9002"))["sight"] == "on"
    proc = run_cli(path, tmp_path / "off", 1, "--cap-seconds", "1", "--sight", "off")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert snapshot.read(fight_file(tmp_path / "off", "L-9002"))["sight"] == "off"


# ---------------------------------------------------------------- results.md

def _rows(out, layout_id):
    text = (Path(out) / "results.md").read_text()
    return [[c.strip() for c in line.strip().strip("|").split("|")] for line in text.splitlines() if line.startswith("| " + layout_id)]


def test_run_appends_one_results_row_per_fight(main_run):
    """S-H-040 part 2: "appends one row to `<out>/results.md` (`| id | a:b | predict | winner | survivors | ticks | agree |`)": one row for the first run,
    a second row (not a rewrite) after a second fight into the same out directory."""
    res = _doc(main_run)["result"]
    rows = _rows(main_run["out"], "L-9001")
    assert len(rows) == 1
    cells = rows[0]
    assert len(cells) == 8, "row shape is | id | a:b | predict | winner | survivors | ticks | agree | blocked | (spec lab-stage3 criterion 6), got %r" % cells
    assert cells[0] == "L-9001" and cells[1] == "8:12" and cells[2] == "B" and cells[3] == res["winner"] and cells[5] == str(res["ticks"])
    assert [int(n) for n in "".join(ch if ch.isdigit() else " " for ch in cells[4]).split()] == res["survivors"]
    assert cells[6].lower() in (("yes", "true") if res["agree"] else ("no", "false"))
    second = run_cli(main_run["path"], main_run["out"], 2)
    assert second.returncode == 0, second.stderr[-2000:]
    assert len(_rows(main_run["out"], "L-9001")) == 2
    assert fight_file(main_run["out"], "L-9001", 2).is_file() and fight_file(main_run["out"], "L-9001", 1).is_file()


# ---------------------------------------------------------------- the refusal

def test_run_refuses_a_layout_that_breaks_r2(tmp_path):
    """S-H-040 part 2: "refuses one failing `check_layout` (prints `REJECT <id> <rule>`, exit 2)": the R2 breaker gives `REJECT L-9003 R2` on stdout, exit
    code 2, and no fight file and no results.md (the `--plant`-style control)."""
    path = write_layout(r2_breaker("L-9003"), tmp_path / "layouts")
    out = tmp_path / "out"
    proc = run_cli(path, out, 1)
    assert proc.returncode == 2, "exit code %d, stderr %r" % (proc.returncode, proc.stderr[-1000:])
    assert ["REJECT", "L-9003", "R2"] in [line.split()[:3] for line in proc.stdout.splitlines()], "stdout was %r" % proc.stdout
    assert not out.exists() or not list(out.iterdir()), "files written for a rejected layout: %r" % sorted(p.name for p in out.iterdir())


# ---------------------------------------------------------------- the import rule, by ast

def _imported_modules(tree, package="scripts.skilllab.arena"):
    """Every dotted module name the tree imports, relative imports resolved against `package`; `from m import n` yields m and m.n (n may be a submodule)."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")[: len(package.split(".")) - (node.level - 1)]
                base = ".".join(parts + ([node.module] if node.module else []))
            names.append(base)
            names += ["%s.%s" % (base, a.name) for a in node.names if a.name != "*"]
    return names


def _drift(tree):
    """The `scripts.` imports of the tree that are not one of the four allowed modules (or a name inside one): `from scripts.skilllab import engine` is
    judged as scripts.skilllab.engine, `from scripts.skilllab.catalogue.produce import check_layout` as the module scripts.skilllab.catalogue.produce."""
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names if (a.name == "scripts" or a.name.startswith("scripts.")) and a.name not in ALLOWED]
        elif isinstance(node, ast.ImportFrom):
            base = (node.module or "") if not node.level else ".".join(["scripts", "skilllab", "arena"][: 3 - (node.level - 1)] + ([node.module] if node.module else []))
            if not (base == "scripts" or base.startswith("scripts.")):
                continue
            if base in ALLOWED:
                continue
            bad += [base + "." + a.name for a in node.names if base + "." + a.name not in ALLOWED]
    return sorted(set(bad))


def test_run_imports_only_the_allowed_modules():
    """S-H-040 part 2: "Imports only `scripts.skilllab.engine`, `scripts.skilllab.fight` (the helpers named), `scripts.skilllab.catalogue.produce.check_layout`,
    `scripts.skilllab.arena.snapshot`. Nothing from the "not used before stage 6" list" (DEC-lab-arena-imports-2026-10-31: "an import of any module on the
    not-used list before stage 6 is a scope drift the stage's tests reject"). Read by ast, no text search: every `scripts.` import is allowed, nothing
    imports dynamically, and nothing on the not-used list is named; everything else is the standard library."""
    assert RUN_FILE.is_file(), "scripts/skilllab/arena/run.py is missing: H-040 part 2 (arena runner) is not built"
    tree = ast.parse(RUN_FILE.read_text(), filename=str(RUN_FILE))
    mods = _imported_modules(tree)
    skilllab = [m for m in mods if m == "scripts" or m.startswith("scripts.")]
    drift = _drift(tree)
    assert not drift, "imports outside the story's list: %r" % drift
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            called = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            assert called not in ("__import__", "import_module"), "dynamic import at line %d" % node.lineno
    outside = sorted({m.split(".")[0] for m in mods if not (m == "scripts" or m.startswith("scripts."))} - set(sys.stdlib_module_names) - {"__future__"})
    assert not outside, "non-standard-library imports: %r" % outside
    named = sorted(set(m.rsplit(".", 1)[-1] for m in skilllab) & set(NOT_USED_BEFORE_STAGE_6))
    assert not named, "modules from the trim report's not-used list: %r" % named


def test_control_import_reader_finds_a_planted_drift():
    """Control (positive control of the import detector, green today): the same reader flags a module from the not-used list and a relative import, and
    passes the four allowed ones."""
    tree = ast.parse("from scripts.skilllab.conditions import C0\nimport scripts.skilllab.engine\nfrom . import snapshot\n"
                     "from scripts.skilllab import fight\nfrom scripts.skilllab.catalogue.produce import check_layout\n")
    assert _drift(tree) == ["scripts.skilllab.conditions.C0"]
    assert "scripts.skilllab.conditions" in set(_imported_modules(tree)) and "conditions" in NOT_USED_BEFORE_STAGE_6
    assert _drift(ast.parse("import scripts.skilllab.sweep\nfrom scripts.skilllab import skills\n")) == ["scripts.skilllab.skills", "scripts.skilllab.sweep"]
    ok = "from scripts.skilllab import engine, fight\nfrom scripts.skilllab.catalogue.produce import check_layout\nfrom scripts.skilllab.arena import snapshot\nfrom . import snapshot\n"
    assert _drift(ast.parse(ok)) == []


def test_control_not_used_list_is_still_the_trim_reports():
    """Control: the report the story names exists, still carries the paragraph the list is taken from, and every module mapped from it exists on the tree,
    so a renamed module turns this red instead of silently weakening the import test."""
    text = TRIM_REPORT.read_text()
    assert "## Not needed for that answer" in text
    for word in ("Conditions C0 to C9", "skill-stacking profile", "knob-sweep", "ping search scene", "decision tree", "mapreport"):
        assert word in text, word
    for name in NOT_USED_BEFORE_STAGE_6:
        assert (ROOT / "scripts" / "skilllab" / (name + ".py")).is_file(), name


# ================================================================ H-040 "Orders and fight end" / H-052 (runner changes)
# spec: docs/stories/H-040.md "Orders and fight end (ruled 2026-11-01, DEC-lab-amove-rule-2026-11-01; contract H-052)" and docs/stories/H-052.md. Quoted:
#   "Orders from the layout's `orders` key (H-052): `both_same_point` sends every unit of both sides to one point, DRAFT-same-point the midpoint of the two sides'
#    tick-0 centroids; `hold:<side>` gives the held side no order and sends every attacker to the held side's centre of mass at tick 0."
#   "Fight end: `wipe`, or `silence` after DRAFT-silence-seconds 10 s of sim time with no shot by either side ..., or the 600 s cap as a backstop. `silence` with both
#    sides alive is a `stall`: the runner prints `FIGHT <id> seed <n> STALL ticks <t>` and exits 0."
#   "Tests (part 2): a 8:8 fixture ends by `wipe` well under the cap; a fixture with the two sides out of range and `hold:A` orders where the attacker's point is
#    unreachable (a planted blocker) ends by `silence` at about 10 s with `stall` true (positive control); the same fixture with `both_same_point` ends by `wipe`."
#   H-052: layout `orders = "both_same_point"` or `"hold:A"` / `"hold:B"` (the held side); "a layout without the key means `both_same_point`".
#   H-052 file: `orders` = {"mode": "both_same_point" | "hold_and_attack", "point": [x, y], "attacker": "A" | "B" | null}; `result.end`; `result.stall`; `winner "stall"`.
#
# THE STALL FIXTURE (8 Vanguard a side, sight off, attack range 300, speed 80 wu/s; rewritten after DEC-silence-clause-2026-11-01, which counts movement):
#   The runner builds no walls (it spawns units and nothing else), so a "planted blocker" the engine can feel does not exist as a layout feature today. The
#   blocker used is a standoff: side A (the held side) is two 4-unit clusters at x 1100 and x 2900 (y 2000), so its centre of mass (2020, 2020) is an empty point
#   920 wu from the nearest unit of either cluster, outside weapon range (300) and, since H-057 engage-on-sight (an idle unit acquires out to its type's
#   sensor radius, about 700 wu), outside the distance at which A's idle units would walk out and fight (clusters at x 1400 and 2600, 620 wu, did). Side B (8 units) is a 4x2 block, 40 wu apart, centred on that point
#   (centroid (2020, 2000)): it starts already at the attacker's order point under hold:A, so it has nowhere to walk and no unit of either side moves in the first
#   10 s, and no unit of B is within weapon range of a unit of A. Hold (B attack-moves to A's centre, A no order): no shot and no movement, so the silence end
#   is at 200 to 240 ticks. With both sides attack-moving to the midpoint (2020, 2010) A walks into B and the fight ends by wipe (both_same_point tests).
#   The engine's own behaviour for the pair is pinned by the control below, not assumed. The wipe fixtures put the two sides inside weapon range of each other
#   (first hit at tick 1) so no reading of when the silence clock starts can end them early. GAP reported: a fight whose approach is longer than 10 s with no shot
#   (the six stage 1 layouts, 400 wu apart, first hit about tick 900) ends by `silence` under a literal reading unless the approach counts as movement, which
#   DEC-silence-clause-2026-11-01 now says it does; the old fixture (B walking about 13 s) failed for that reason.
# `orders` in a layout: check_layout reads named keys only (produce._violations), so the extra top-level key passes it (control below); `dump_toml` does not write it, so
# the fixtures prepend the line.

ORDERS_SPLIT_A = [(1100.0 + (i % 2) * 40.0, 2000.0 + (i // 2) * 40.0) for i in range(4)] + [(2900.0 + (i % 2) * 40.0, 2000.0 + (i // 2) * 40.0) for i in range(4)]
ORDERS_SPLIT_B = [(1960.0 + (i % 4) * 40.0, 1980.0 + (i // 4) * 40.0) for i in range(8)]   # already at A's centre: stopped, out of range (DEC-silence-clause-2026-11-01 counts movement)
SILENCE_TICKS_LOW, SILENCE_TICKS_HIGH = 10 * TICK_RATE, 12 * TICK_RATE   # H-040 "about 10 s": the brief's window 10 s to 12 s; DRAFT-silence-seconds 10


def make_stall_layout(layout_id):
    """The standoff fixture above as a legal 8:8 layout (small_flat, Vanguard both sides); A's tick-0 centroid is (2020, 2020), B's (2040, 2920)."""
    def rows(points, facing):
        return [{"role": "Vanguard", "x": x, "y": y, "facing": facing, "layer": 0} for x, y in points]
    return {"id": layout_id, "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "B",
            "predict_why": "Test fixture: A's centre of mass is an empty point out of weapon range.", "verdict": "", "feedback": "",
            "side_a": {"headcount": 8, "units": rows(ORDERS_SPLIT_A, 0.0)}, "side_b": {"headcount": 8, "units": rows(ORDERS_SPLIT_B, round(math.pi, 4))}}


def write_layout_orders(layout, directory, orders=None):
    """write_layout with an `orders = "<value>"` top-level line prepended (None writes no key); returns the path."""
    path = write_layout(layout, directory)
    if orders is not None:
        path.write_text('orders = "%s"\n' % orders + path.read_text())
    return path


def _centroid_of(layout, key):
    rows = layout[key]["units"]
    return sum(r["x"] for r in rows) / len(rows), sum(r["y"] for r in rows) / len(rows)


def _midpoint(layout):
    (ax, ay), (bx, by) = _centroid_of(layout, "side_a"), _centroid_of(layout, "side_b")
    return (ax + bx) / 2, (ay + by) / 2


def _near(point, want, tol=1.0):
    """A point within `tol` wu of `want` (DRAFT-orders-point-rounding: the story gives no rounding of `orders.point`)."""
    return len(point) == 2 and abs(point[0] - want[0]) <= tol and abs(point[1] - want[1]) <= tol


def _stdout_lines(proc):
    return [line.strip() for line in proc.stdout.splitlines()]


def test_control_stall_fixture_is_legal_and_orders_key_is_ignored_by_check_layout(tmp_path):
    """Control, green today: the standoff layout passes check_layout, the TOML with a prepended `orders = "hold:A"` line still loads and still passes check_layout
    (so the layout schema may carry the key without a producer change), and its tick-0 centroids are the premises dumped above."""
    layout = make_stall_layout("L-9101")
    pre, rul = produce.presets(), produce.rules()
    assert produce.check_layout(layout, pre, rul) == []
    path = write_layout_orders(layout, tmp_path, "hold:A")
    loaded = tomllib.loads(path.read_text())
    assert loaded["orders"] == "hold:A"
    assert produce.check_layout(loaded, pre, rul) == []
    assert _near(_centroid_of(layout, "side_a"), (2020.0, 2020.0)) and _near(_centroid_of(layout, "side_b"), (2020.0, 2000.0))
    assert _near(_midpoint(layout), (2020.0, 2010.0))


def test_control_engine_standoff_holds_silent_under_hold_and_wipes_under_one_point():
    """Control, green today: the C sim itself gives the pair the tests below ask the runner for. With the layout's rows spawned directly, B attack-moving to A's centre
    of mass and A given no order, nobody is hit in 400 ticks and everyone is alive (8:8); with both sides attack-moving to the midpoint of the centroids one side is
    wiped out before 12,000 ticks. So a stall or a wipe from the runner later is the runner's rule, not the fixture's."""
    from scripts.skilllab.engine import Engine
    layout = make_stall_layout("L-9101")

    def play(mode, ticks):
        e = Engine()
        w = e.new_world(1)
        try:
            e.disable_abilities(w)
            e.set_param(w, e.param_id("OM_TP_TARGET_BY_SIGHT"), 0)
            vanguard = e.type_id("Vanguard")
            ids = {f: [e.spawn(w, vanguard, f, u["x"], u["y"], u["layer"]) for u in layout[k]["units"]] for f, k in ((0, "side_a"), (1, "side_b"))}
            hp0 = {u: e.unit_hp(w, u) for f in ids for u in ids[f]}
            if mode == "hold":
                e.order_attack_move(w, ids[1], *_centroid_of(layout, "side_a"))
            else:
                e.order_attack_move(w, ids[0], *_midpoint(layout))
                e.order_attack_move(w, ids[1], *_midpoint(layout))
            hit = False
            for tick in range(1, ticks + 1):
                e.step(w)
                hit = hit or any(e.unit_hp(w, u) < hp0[u] for u in hp0)
                alive = tuple(sum(e.unit_alive(w, u) for u in ids[f]) for f in (0, 1))
                if min(alive) == 0:
                    break
            return hit, alive, tick
        finally:
            e.free_world(w)

    hit, alive, _ = play("hold", 400)
    assert not hit and alive == (8, 8), "premise failed: hold fixture was shot at or lost units (%r, %r)" % (hit, alive)
    hit, alive, tick = play("same", 12000)
    assert hit and min(alive) == 0 and tick < 12000, "premise failed: same-point fixture did not end by a wipe (%r, %r, tick %d)" % (hit, alive, tick)


def test_run_default_orders_are_both_same_point_and_the_file_is_v2(main_run):
    """H-052: "a layout without the key means `both_same_point` (stage 1 default)"; "`schema` becomes `om-fight-2`"; "`orders` ... `point` ... the midpoint of the two
    sides' tick-0 centroids"; `attacker` null for both_same_point. The 8:12 fixture has no `orders` key."""
    doc = _doc(main_run)
    assert doc["schema"] == "om-fight-2"
    assert doc["orders"]["mode"] == "both_same_point" and doc["orders"]["attacker"] is None
    assert _near(doc["orders"]["point"], _midpoint(main_run["layout"])), doc["orders"]


def test_run_wipe_fixture_ends_by_wipe_well_under_the_cap(tmp_path):
    """H-040 Tests (part 2): "a 8:8 fixture ends by `wipe` well under the cap". 8:8 Vanguards 200 wu apart (inside weapon range, first shot at once), no `orders` key:
    `result.end == "wipe"`, `stall` false, `capped` false, fewer than half the cap's ticks (the cap is 12,000; 'well under' is not given a number, half is the test's
    reading: DRAFT-well-under), winner not `stall`, no STALL line."""
    layout = make_layout("L-9102", 8, 8, "A", gap_x=200.0)
    proc = run_cli(write_layout(layout, tmp_path / "layouts"), tmp_path / "out", 1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    res = snapshot.read(fight_file(tmp_path / "out", "L-9102"))["result"]
    assert res["end"] == "wipe" and res["stall"] is False and res["capped"] is False
    assert res["ticks"] < snapshot.CAP_SECONDS * TICK_RATE // 2 and min(res["survivors"]) == 0
    assert res["winner"] in ("A", "B", "draw", "none")   # "none": both sides wiped on the same tick (H-053 audit item 2)
    assert not any("STALL" in line for line in _stdout_lines(proc))


def test_run_stall_fixture_with_hold_a_ends_by_silence_at_ten_seconds(tmp_path):
    """H-040 Tests (part 2), the positive control of the stall detector: "a fixture with the two sides out of range and `hold:A` orders where the attacker's point is
    unreachable (a planted blocker) ends by `silence` at about 10 s with `stall` true". `end` silence, `stall` true, `winner` "stall" (not "draw"), `agree` false, both
    sides alive (8:8 in the result and in the last frame), `ticks` between 10 s and 12 s of sim time (200 to 240 at 20 per second), the last frame is the last tick,
    `capped` false; stdout has `FIGHT L-9101 seed 1 STALL ticks <t>` and the exit code is 0."""
    layout = make_stall_layout("L-9101")
    proc = run_cli(write_layout_orders(layout, tmp_path / "layouts", "hold:A"), tmp_path / "out", 1)
    assert proc.returncode == 0, proc.stderr[-2000:] + proc.stdout[-500:]
    doc = snapshot.read(fight_file(tmp_path / "out", "L-9101"))
    res = doc["result"]
    assert res["end"] == "silence" and res["stall"] is True and res["capped"] is False
    assert res["winner"] == "stall" and res["agree"] is False
    assert res["survivors"] == [8, 8] and doc["frames"][-1]["alive"] == [8, 8] and doc["frames"][-1]["tick"] == res["ticks"]
    assert SILENCE_TICKS_LOW <= res["ticks"] <= SILENCE_TICKS_HIGH, "stall at tick %d, wanted %d to %d" % (res["ticks"], SILENCE_TICKS_LOW, SILENCE_TICKS_HIGH)
    assert "FIGHT L-9101 seed 1 STALL ticks %d" % res["ticks"] in _stdout_lines(proc), "stdout was %r" % proc.stdout


def test_run_stall_fixture_with_both_same_point_ends_by_wipe(tmp_path):
    """H-040 Tests (part 2): "the same fixture with `both_same_point` ends by `wipe`": the standoff layout with `orders = "both_same_point"` (and, equally, without the
    key) ends `wipe`, `stall` false, one side with no survivors, well under the cap, and prints a `FIGHT ... winner ...` line, not STALL."""
    layout = make_stall_layout("L-9101")
    for name, orders in (("explicit", "both_same_point"), ("default", None)):
        out = tmp_path / ("out_" + name)
        proc = run_cli(write_layout_orders(layout, tmp_path / ("layouts_" + name), orders), out, 1)
        assert proc.returncode == 0, proc.stderr[-2000:]
        res = snapshot.read(fight_file(out, "L-9101"))["result"]
        assert res["end"] == "wipe" and res["stall"] is False and min(res["survivors"]) == 0, (name, res)
        assert res["ticks"] < snapshot.CAP_SECONDS * TICK_RATE // 2 and res["winner"] in ("A", "B")
        assert any(line.startswith("FIGHT L-9101 seed 1 winner ") for line in _stdout_lines(proc)) and not any("STALL" in line for line in _stdout_lines(proc))


def test_run_orders_in_the_file_for_hold_a_name_the_holder_and_the_attacker(tmp_path):
    """H-052: `orders` = `{"mode": ..., "point": [x, y], "attacker": ...}`; "`hold_and_attack`: the holder (the other side) receives no order and fires from where it
    stands; the attacker attack-moves every unit to `point`, which is the holder's centre of mass at tick 0." `orders = "hold:A"`: mode hold_and_attack, attacker "B",
    point A's centre of mass (2020, 2020)."""
    layout = make_stall_layout("L-9101")
    proc = run_cli(write_layout_orders(layout, tmp_path / "layouts", "hold:A"), tmp_path / "out", 1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    orders = snapshot.read(fight_file(tmp_path / "out", "L-9101"))["orders"]
    assert orders["mode"] == "hold_and_attack" and orders["attacker"] == "B"
    assert _near(orders["point"], _centroid_of(layout, "side_a")), orders


def test_run_orders_in_the_file_for_hold_b_swap_the_sides(tmp_path):
    """H-052: "`orders = "hold:A"` / `orders = "hold:B"` (the held side)": hold:B on the close 8:8 fixture gives attacker "A" and point B's centre of mass; B has no
    order, so with the sides inside weapon range B still fires from where it stands and the fight is decided."""
    layout = make_layout("L-9102", 8, 8, "A", gap_x=200.0)
    proc = run_cli(write_layout_orders(layout, tmp_path / "layouts", "hold:B"), tmp_path / "out", 1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    doc = snapshot.read(fight_file(tmp_path / "out", "L-9102"))
    assert doc["orders"]["mode"] == "hold_and_attack" and doc["orders"]["attacker"] == "A"
    assert _near(doc["orders"]["point"], _centroid_of(layout, "side_b")), doc["orders"]
    assert doc["result"]["end"] == "wipe"


def test_run_both_same_point_orders_in_the_file_hold_the_midpoint(tmp_path):
    """H-052: `both_same_point`: "every unit of both sides attack-moves to `point`"; H-040: DRAFT-same-point "the midpoint of the two sides' tick-0 centroids";
    `attacker` null. Explicit `orders = "both_same_point"` on the standoff layout: point (2030, 2470)."""
    layout = make_stall_layout("L-9101")
    proc = run_cli(write_layout_orders(layout, tmp_path / "layouts", "both_same_point"), tmp_path / "out", 1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    orders = snapshot.read(fight_file(tmp_path / "out", "L-9101"))["orders"]
    assert orders["mode"] == "both_same_point" and orders["attacker"] is None
    assert _near(orders["point"], _midpoint(layout)), orders


def test_run_stall_is_byte_identical_twice(tmp_path):
    """CLAUDE.md "Determinism is a contract": the stall fight, same layout and seed twice, gives byte-identical files and the same stdout."""
    path = write_layout_orders(make_stall_layout("L-9101"), tmp_path / "layouts", "hold:A")
    one, two = run_cli(path, tmp_path / "o1", 1), run_cli(path, tmp_path / "o2", 1)
    assert one.returncode == 0 and two.returncode == 0, one.stderr[-1000:] + two.stderr[-1000:]
    assert fight_file(tmp_path / "o1", "L-9101").read_bytes() == fight_file(tmp_path / "o2", "L-9101").read_bytes()
    assert one.stdout == two.stdout


def test_run_capped_fight_writes_end_cap(tmp_path):
    """H-052: `result.end` "cap" (DRAFT-fight-cap, 'a backstop'); the existing H-040 cap fixture (8:8, 2000 wu apart, cap 1 s: shorter than the 10 s silence) still writes
    `capped: true` and `winner: "draw"` and now `end: "cap"`, `stall` false (the cap is not a stall), and its FIGHT line is the unchanged v1 line."""
    layout = make_layout("L-9002", 8, 8, "A", gap_x=2000.0)
    proc = run_cli(write_layout(layout, tmp_path / "layouts"), tmp_path / "out", 1, "--cap-seconds", "1")
    assert proc.returncode == 0, proc.stderr[-2000:]
    res = snapshot.read(fight_file(tmp_path / "out", "L-9002"))["result"]
    assert res["end"] == "cap" and res["stall"] is False and res["capped"] is True and res["winner"] == "draw"
    assert "FIGHT L-9002 seed 1 winner draw ticks %d agree no" % res["ticks"] in _stdout_lines(proc)


def test_run_main_fixture_ends_by_wipe(main_run):
    """H-052: `end` "wipe" (one side has no survivors): the existing 8:12 fixture, run once, now also says so in the file."""
    res = _doc(main_run)["result"]
    assert res["end"] == "wipe" and res["stall"] is False and min(res["survivors"]) == 0


# ================================================================ H-053 stage 2 (arena-stage2-roles-ranges-winrates)
# spec: docs/stories/H-053.md "What stage 2 adds", "Interfaces" 1 and 7; Flag client. Story Tests line: "`test_run.py` (`--seeds 3` writes three fight files and one rate file)".
# Not pinned by the story: which seed numbers `--seeds N` runs from `--seed S`; the tests read them from the rate file's `seeds` list.

SIX_ROLES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]


def _with_top_keys(layout, **keys):
    """The layout as TOML with extra top-level keys first (a top-level key must precede every table); lists are written as TOML arrays."""
    head = "".join("%s = %s\n" % (k, "[%s]" % ", ".join(repr(float(x)) for x in v) if isinstance(v, list) else repr(v)) for k, v in keys.items())
    return head + produce.dump_toml(layout)


def six_role_layout(layout_id):
    """The 8:12 fixture with the rows' roles cycled through all six roles on both sides (same positions, so it stays legal)."""
    layout = make_layout(layout_id, 8, 12, "B")
    for key in ("side_a", "side_b"):
        for i, row in enumerate(layout[key]["units"]):
            row["role"] = SIX_ROLES[i % 6]
    return layout


def test_control_stage2_fixtures_are_legal_and_toml_carries_the_new_keys():
    """H-053 control, green today: the six-role fixture passes check_layout (R5 lists all six roles), and a TOML with `predict_rate`, `orders` and `orders_point` at the top
    still parses and passes check_layout, so a red below is the runner and not the fixture."""
    pre, rul = produce.presets(), produce.rules()
    assert set(rul["R5"]["roles"]) >= set(SIX_ROLES)
    assert produce.check_layout(six_role_layout("L-9010"), pre, rul) == []
    layout = make_layout("L-9011", 8, 12, "B")
    loaded = tomllib.loads(_with_top_keys(layout, predict_rate=0.75, orders_point=[2000.0, 2100.0]))
    assert loaded["predict_rate"] == 0.75 and loaded["orders_point"] == [2000.0, 2100.0]
    assert produce.check_layout(loaded, pre, rul) == []


def test_seeds_three_writes_three_fight_files_and_one_rate_file(tmp_path):
    """Tests line "`--seeds 3` writes three fight files and one rate file"; story "one `fight.json` per seed, plus `<id>.rate.json`". With `--seed 1 --seeds 3` on the 8:12
    fixture: exactly three `L-9012-s*.fight.json` that validate, one `L-9012.rate.json` whose `seeds` list names those three seeds, `wins_b` 3 (B wins every seed) and
    `rate_a` 0.0, and the layout's `predict_rate` 0.0 carried into the file."""
    layout = make_layout("L-9012", 8, 12, "B")
    path = tmp_path / "layouts" / "L-9012.toml"
    path.parent.mkdir()
    path.write_text(_with_top_keys(layout, predict_rate=0.0))
    out = tmp_path / "out"
    proc = run_cli(path, out, 1, "--seeds", "3")
    assert proc.returncode == 0, proc.stderr[-1500:] + proc.stdout[-500:]
    files = sorted(out.glob("L-9012-s*.fight.json"))
    assert len(files) == 3, [p.name for p in files]
    for p in files:
        snapshot.read(p)
    rates = sorted(out.glob("*.rate.json"))
    assert [p.name for p in rates] == ["L-9012.rate.json"], [p.name for p in rates]
    rate = json.loads(rates[0].read_text())
    assert len(rate["seeds"]) == 3 and sorted(out.joinpath("L-9012-s%d.fight.json" % s).name for s in rate["seeds"]) == [p.name for p in files]
    assert (rate["wins_a"], rate["wins_b"], rate["stalls"]) == (0, 3, 0) and rate["rate_a"] == 0.0 and rate["predict_rate"] == 0.0


def test_a_single_seed_run_still_writes_no_rate_file(tmp_path):
    """Control, green today: without `--seeds` the stage 1 behaviour stands (one fight file, no rate file), so the test above is red for the missing `--seeds` and not for a
    runner that always writes a rate file."""
    layout = make_layout("L-9013", 8, 12, "B")
    path = write_layout(layout, tmp_path / "layouts")
    out = tmp_path / "out"
    proc = run_cli(path, out, 1)
    assert proc.returncode == 0, proc.stderr[-1500:]
    assert len(list(out.glob("*.fight.json"))) == 1 and list(out.glob("*.rate.json")) == []


def test_all_six_roles_run_and_appear_in_frame_zero(tmp_path):
    """Story "All six roles (Raider, Interceptor, Vanguard, Warden, Bombard, Bastion) in one layout": a mixed-role 8:12 layout runs to a valid file whose frame 0 carries every
    role on its units (roster ranges come from the engine; the layout's `range` is absent)."""
    path = write_layout(six_role_layout("L-9014"), tmp_path / "layouts")
    out = tmp_path / "out"
    proc = run_cli(path, out, 1)
    assert proc.returncode == 0, proc.stderr[-1500:]
    doc = snapshot.read(fight_file(out, "L-9014"))
    assert {u["role"] for u in doc["frames"][0]["units"]} == set(SIX_ROLES)


def test_orders_point_names_the_spot_both_sides_go_to(tmp_path):
    """Interfaces 7: "`orders_point` (`[x, y]`, absent for midpoint)"; audit item 5: "both sides go to the exact same spot". With `orders_point = [2000.0, 2100.0]` and the default
    both_same_point the file's `orders.point` is [2000.0, 2100.0], not the centroid midpoint (2010.0, 2040.0 for this fixture)."""
    layout = make_layout("L-9015", 8, 12, "B")
    path = tmp_path / "layouts" / "L-9015.toml"
    path.parent.mkdir()
    path.write_text(_with_top_keys(layout, orders_point=[2000.0, 2100.0]))
    out = tmp_path / "out"
    proc = run_cli(path, out, 1)
    assert proc.returncode == 0, proc.stderr[-1500:]
    orders = snapshot.read(fight_file(out, "L-9015"))["orders"]
    assert orders["mode"] == "both_same_point" and orders["point"] == [2000.0, 2100.0], orders


# ================================================================ H-053 defect: the fight file carries the roster ranges (range rings)
# Brief to the test writer, 2026-11-02: the replay draws a range ring only for a unit whose range is above 0 and the om-fight-2 file carried no range, so no ring was drawn. Intended:
# run.py writes a top-level `ranges` map {role: range in wu} for every role present in the layout, with the roster values (`produce._roster_ranges()`, the same numbers the layout
# converter puts on its rows); schema stays om-fight-2. Format side: tests/skilllab/arena/test_snapshot.py (`ranges`); replay side: tests/qa/test_fight_replay.py.

ROSTER_RANGES = {"Raider": 200.0, "Interceptor": 250.0, "Vanguard": 300.0, "Warden": 350.0, "Bombard": 1200.0, "Bastion": 800.0}


def test_control_roster_ranges_are_the_six_numbers_the_brief_names():
    """Control, green today: the roster function the runner must read gives the six ranges named in the brief (Raider 200, Interceptor 250, Vanguard 300, Warden 350, Bombard 1200,
    Bastion 800), so a red below is the missing `ranges` key and not a moved roster."""
    assert produce._roster_ranges() == ROSTER_RANGES


def test_run_writes_a_ranges_map_for_the_one_role_present(main_run):
    """Brief 2026-11-02: "run.py writes `ranges` for every role present with the roster values". The 8:12 Vanguard fixture's file has `ranges` == {"Vanguard": 300.0} (only the roles
    present), the value the roster function gives, and the file still reads through the checker as om-fight-2."""
    doc = _doc(main_run)
    assert doc["schema"] == snapshot.SCHEMA_V2
    assert doc.get("ranges") == {"Vanguard": produce._roster_ranges()["Vanguard"]}, doc.get("ranges")


def test_run_writes_a_ranges_map_for_all_six_roles(tmp_path):
    """Brief 2026-11-02: the six-role layout's file carries `ranges` for each of the six roles, each equal to the roster's number (read from `produce._roster_ranges()`)."""
    path = write_layout(six_role_layout("L-9016"), tmp_path / "layouts")
    out = tmp_path / "out"
    proc = run_cli(path, out, 1)
    assert proc.returncode == 0, proc.stderr[-1500:]
    doc = snapshot.read(fight_file(out, "L-9016"))
    assert doc.get("ranges") == produce._roster_ranges(), doc.get("ranges")
