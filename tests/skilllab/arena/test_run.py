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
ALLOWED = {"scripts.skilllab.engine", "scripts.skilllab.fight", "scripts.skilllab.catalogue.produce", "scripts.skilllab.arena.snapshot"}

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
    assert len(cells) == 7, "row shape is | id | a:b | predict | winner | survivors | ticks | agree |, got %r" % cells
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
