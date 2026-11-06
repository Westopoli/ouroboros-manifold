# spec: docs/northstar/plans/cascades/lab-stage4/spec.md::Acceptance criteria::AC-1
# Rule pins: none (lab harness story H-088)
"""lab-stage4 leaf-01, criteria 1, 2, 4, 5 and 6 (spec lines 21, 22, 24, 25, 26): `--sight on` is a rule set, the fight file says who saw whom, `--control sight`, the
vantage and cover fixtures, through the real engine (called in-process the way test_stage3_control.py calls it).

1: sight on = targeting by sight left on, ground era, canvas, every role walks, reach 0 up 1 down for every role, the holder of hold:A / hold:B on order_guard, the
   document's `movement_kind` 1 and `orders.guard`; sight off changes nothing (byte pin in h088_fixtures.SIGHT_OFF_PIN).
2: per-unit `seen`, `sights`, `result.first_seen` (sampled every CHECK_EVERY ticks, tick 0 included); none of the three with sight off.
4: `--control sight`, `--control ground`, the two extra `results.md` columns with sight on only.
5: VANTAGE: the high ground sees down and fires down; the low ground never sees up.   6: COVER hides; the guard stays within GUARD_RADIUS.

Criterion 4's `--control sight` fight is the stage 4 rule set with targeting by sight off (`fight(.., "control", ..)` internally, document `sight` "off"), so the vantage
control has A firing down (criterion 5's control).
Controls (green today, must stay green): the sight-off byte pin, the sight-off engine calls, the sight-off documents, `--control ground`'s files."""
import json
import shutil
from pathlib import Path

import pytest

import h063_fixtures as fx
import h088_fixtures as f8
from scripts.skilllab.arena import features, run as arena_run, snapshot
from scripts.skilllab.arena.run import CHECK_EVERY
from scripts.skilllab.catalogue import produce
from scripts.skilllab.engine import Engine

GUARD_RADIUS = 200.0   # R-096-08, the engine's (spec criterion 6)
OLD_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree | blocked |"
NEW_HEAD = "| id | a:b | predict | winner | survivors | ticks | agree | blocked | first seen A | first seen B |"
SPIED = ("set_era_kind", "set_canvas", "set_movement_kind", "set_reach", "set_param", "order_guard")


def run_ok(lay, directory, *extra):
    """The fight document of `lay` through the CLI (in-process); the exit code is checked here, once."""
    proc, doc = fx.fight(lay, directory, 1, *extra)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return doc


def spy(monkeypatch):
    """Record the arguments (after the world) of every call to the engine bindings stage 4 sets; the real binding still runs."""
    calls = {name: [] for name in SPIED}
    for name in SPIED:
        def wrapper(self, *args, _n=name, _real=getattr(Engine, name), **kw):
            calls[_n].append(args[1:])
            return _real(self, *args, **kw)
        monkeypatch.setattr(Engine, name, wrapper)
    return calls


def summary(calls, orders):
    sight_off = Engine().param_id("OM_TP_TARGET_BY_SIGHT")
    walkers = sorted(c[0] for c in calls["set_movement_kind"] if c[1] == 1)
    return {"era_kinds": sorted({c[0] for c in calls["set_era_kind"]}), "canvas_set": bool(calls["set_canvas"]), "walkers": len(walkers),
            "reach": sorted({c[1:] for c in calls["set_reach"]}), "reach_types_are_the_walkers": sorted(c[0] for c in calls["set_reach"]) == walkers,
            "sight_switched_off": sum(1 for c in calls["set_param"] if c == (sight_off, 0)), "guards": len(calls["order_guard"]), "orders_guard": orders.get("guard")}


def names(directory):
    """Sorted file names in `directory`, [] when it does not exist."""
    return sorted(p.name for p in Path(directory).iterdir()) if Path(directory).is_dir() else []


def result_rows(out):
    lines = (Path(out) / "results.md").read_text().splitlines()
    return lines[0], lines[1], [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[2:]]


@pytest.fixture(autouse=True)
def _scratch_cwd(tmp_path, monkeypatch):
    """Run from the test's scratch directory: argparse takes `--control` for an abbreviation of `--control-dir` until the flag exists, and that makes a directory named
    after its value in the current directory."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture(scope="module")
def vantage_on(tmp_path_factory):
    d = tmp_path_factory.mktemp("vantage_on")
    return run_ok(f8.vantage_layout("L-9801"), d, "--sight", "on", "--cap-seconds", "60"), d


@pytest.fixture(scope="module")
def vantage_off(tmp_path_factory):
    return run_ok(f8.vantage_layout("L-9802"), tmp_path_factory.mktemp("vantage_off"), "--sight", "off", "--cap-seconds", "60")


# ---------------------------------------------------------------- the fixtures themselves

def test_control_the_fixtures_are_legal_layouts_and_the_crossing_helper_discriminates():
    """CONTROL (green today, must stay green): the vantage, cover (with and without boxes) and open-field fixtures pass `check_layout` and the route check (so a REJECT in
    a test below is the cascade and not a bad fixture); `crossing_pairs` names pairs for the cover fixture and `crosses` tells a segment through the middle box from one
    that passes clear of every box."""
    lays = [f8.vantage_layout("L-9890"), f8.cover_layout("L-9891"), f8.cover_layout("L-9892", boxes=False), f8.open_layout("L-9893")]
    legal = ([produce.check_layout(l, produce.presets(), produce.rules()) for l in lays], [arena_run.unreachable(l) for l in lays])
    cover = f8.cover_layout("L-9891")
    rows = [dict(u, id=i, side=side) for i, (side, u) in enumerate([("A", u) for u in cover["side_a"]["units"]] + [("B", u) for u in cover["side_b"]["units"]])]
    cells = f8.blocked_cells(cover)
    assert (legal, len(f8.crossing_pairs(cover, rows)) > 0, f8.crosses((1700, 2000), (2300, 2000), cells), f8.crosses((1700, 1700), (2300, 1700), cells)) == (
        ([[]] * 4, [None] * 4), True, True, False)


# ---------------------------------------------------------------- criterion 1: the rule set

def test_control_sight_off_files_are_byte_identical_to_the_pinned_ones(tmp_path):
    """CONTROL (green today, must stay green), criterion 1, spec line 21: the H-063 chokepoint fixture with `--sight off` writes the main fight file, the control twin's
    fight file and `results.md` with the sha256 recorded on main 240773dd (h088_fixtures.SIGHT_OFF_PIN)."""
    _, got = f8.sight_off_digests(tmp_path)
    assert got == f8.SIGHT_OFF_PIN


def test_sight_on_gives_the_engine_the_stage4_rule_set(monkeypatch):
    """Criterion 1: on an open field with two roles and no features, `--sight on` keeps targeting by sight on (OM_TP_TARGET_BY_SIGHT never set to 0), sets era kind 1,
    sets a canvas, makes every role a walker, sets reach (0 up, 1 down) for those same types and orders no guard (both_same_point: `orders.guard` is false)."""
    calls = spy(monkeypatch)
    _, _, _, orders = arena_run.fight(f8.open_layout("L-9803", roles=("Raider", "Vanguard")), 1, "on", 1)
    assert summary(calls, orders) == {"era_kinds": [1], "canvas_set": True, "walkers": 2, "reach": [(0, 1)], "reach_types_are_the_walkers": True,
                                      "sight_switched_off": 0, "guards": 0, "orders_guard": False}


def test_control_sight_off_leaves_the_engine_as_it_is_today(monkeypatch):
    """CONTROL (green today, must stay green), criterion 1 "`--sight off` changes nothing from today": the same open field with `--sight off` switches targeting by
    sight off, sets no era kind, no canvas, no reach, no walker and no guard, and the orders block has no `guard` key."""
    calls = spy(monkeypatch)
    _, _, _, orders = arena_run.fight(f8.open_layout("L-9803", roles=("Raider", "Vanguard")), 1, "off", 1)
    assert summary(calls, orders) == {"era_kinds": [], "canvas_set": False, "walkers": 0, "reach": [], "reach_types_are_the_walkers": True,
                                      "sight_switched_off": 1, "guards": 0, "orders_guard": None}


def test_the_control_rule_set_is_stage4_with_targeting_by_sight_off(monkeypatch):
    """Criterion 4, spec line 24: `fight(.., "control", ..)` is the stage 4 rule set except that targeting by sight is switched off (OM_TP_TARGET_BY_SIGHT set to 0 once):
    era kind 1, a canvas, every role a walker, reach (0 up, 1 down) for those types, the holder (hold:A) guarded and `orders.guard` true."""
    calls = spy(monkeypatch)
    frames, _, _, orders = arena_run.fight(f8.vantage_layout("L-9816"), 1, "control", 1)
    holder_ids = sorted(u["id"] for u in frames[0]["units"] if u["side"] == "A")
    got = summary(calls, orders)
    got["guarded"] = [sorted(c[0]) for c in calls["order_guard"]]
    assert got == {"era_kinds": [1], "canvas_set": True, "walkers": 1, "reach": [(0, 1)], "reach_types_are_the_walkers": True, "sight_switched_off": 1, "guards": 1,
                   "orders_guard": True, "guarded": [holder_ids]}


@pytest.mark.parametrize("sight,switched_off", [("on", 0), ("control", 1)])
def test_the_rule_set_is_given_to_a_layout_with_bound_features_too(sight, switched_off, monkeypatch):
    """Criterion 1 and 4, spec lines 21 and 24 (audit Y3): "whether or not the layout has features": the cover fixture (`features.bound`, planar boxes, where `fight()` takes the
    ground branch) gets era kind 1, a canvas, walkers, reach (0 up, 1 down), the holder guarded and `orders.guard` true; targeting by sight is switched off once for the
    control and never for sight on."""
    calls = spy(monkeypatch)
    lay = f8.cover_layout("L-9821")
    _, _, _, orders = arena_run.fight(lay, 1, sight, 1)
    got = summary(calls, orders)
    assert (features.bound(lay), got["era_kinds"], got["canvas_set"], got["walkers"], got["reach"], got["guards"], got["orders_guard"], got["sight_switched_off"]) == (
        True, [1], True, 1, [(0, 1)], 1, True, switched_off)


@pytest.mark.parametrize("orders,holder", [("hold:A", "A"), ("hold:B", "B")])
def test_the_holder_of_a_hold_layout_is_ordered_to_guard(orders, holder, monkeypatch):
    """Criterion 1, spec line 21 (DEC-stage4-guard-holder): with `hold:A` / `hold:B` the holder's units, and only they, get `order_guard` after spawning, and the orders
    block says `guard: true`."""
    calls = spy(monkeypatch)
    frames, _, _, doc_orders = arena_run.fight(f8.vantage_layout("L-9804", orders=orders), 1, "on", 1)
    holder_ids = sorted(u["id"] for u in frames[0]["units"] if u["side"] == holder)
    assert {"guarded": [sorted(c[0]) for c in calls["order_guard"]], "orders_guard": doc_orders.get("guard")} == {"guarded": [holder_ids], "orders_guard": True}


def test_every_sight_on_document_walks_and_names_its_guard(tmp_path):
    """Criterion 1, spec line 21: the document of a sight-on fight with no features (open field, both_same_point) carries `movement_kind` 1 and `orders.guard` false."""
    doc = run_ok(f8.open_layout("L-9805"), tmp_path, "--sight", "on", "--cap-seconds", "1")
    assert (doc.get("movement_kind"), doc["orders"].get("guard")) == (1, False)


# ---------------------------------------------------------------- criterion 2: seen, sights, first_seen

def test_every_unit_lists_the_living_enemies_it_sees_and_a_dead_unit_lists_none(vantage_on):
    """Criterion 2, spec line 22: per frame and unit, `seen` is a sorted list of ids of living units of the other side, `[]` for a dead unit. Premise asserted: the
    60 s vantage fight has a dead unit in some frame (otherwise the dead-unit clause would pass by absence)."""
    doc, _ = vantage_on
    bad = []
    for f in doc["frames"]:
        living = {u["id"]: u["side"] for u in f["units"] if u["alive"]}
        for u in f["units"]:
            ok = u["seen"] == sorted(u["seen"]) and all(e in living and living[e] != u["side"] for e in u["seen"]) and (u["alive"] or u["seen"] == [])
            if not ok:
                bad.append((f["tick"], u["id"], u["alive"], u["seen"]))
    assert (bad, any(not u["alive"] for f in doc["frames"] for u in f["units"])) == ([], True)   # the second is the fixture premise: someone dies in the 60 s fight


def test_sights_are_each_roles_sensor_radius(tmp_path):
    """Criterion 2, spec line 22: `sights` is `{role: sensor radius}` from `engine.type_stats`, one key per role in the fight (two roles here, with different radii)."""
    engine = Engine()
    w = engine.new_world(1)
    try:
        want = {r: engine.type_stats(w, engine.type_id(r))["sensor_radius"] for r in ("Raider", "Vanguard")}
    finally:
        engine.free_world(w)
    doc = run_ok(f8.open_layout("L-9806", roles=("Raider", "Vanguard")), tmp_path, "--sight", "on", "--cap-seconds", "1")
    assert doc.get("sights") == want and want["Raider"] != want["Vanguard"]


def test_first_seen_samples_tick_zero(tmp_path):
    """Criterion 2, spec line 22: "tick 0 included": two sides 600 wu apart (inside the Vanguard sensor radius) see each other at tick 0, so `first_seen` is
    `{"A": 0, "B": 0}` as ints (0, not null, and not a bool)."""
    doc = run_ok(f8.open_layout("L-9807"), tmp_path, "--sight", "on", "--cap-seconds", "1")
    first = doc["result"].get("first_seen", {})
    assert (first, [type(v) for v in first.values()]) == ({"A": 0, "B": 0}, [int, int])


def test_seen_is_per_unit_not_per_side(tmp_path):
    """Criterion 2, spec line 22 (audit Y2): "the living enemy unit ids **this unit** sees": on the open field one A unit is moved to x 900, 1400 wu from side B (Vanguard
    sensor radius 700); at frame 0 its own list is empty while the lists of its seven siblings are not. A side's union written into every unit would fail."""
    lay = f8.open_layout("L-9820")
    lay["side_a"]["units"][0]["x"] = 900.0
    units = run_ok(lay, tmp_path, "--sight", "on", "--cap-seconds", "1")["frames"][0]["units"]
    a = [u for u in units if u["side"] == "A"]
    far = [u["seen"] for u in a if u["x"] < 1000.0]
    assert (far, len(a), all(u["seen"] for u in a if u["x"] >= 1000.0)) == ([[]], 8, True)


def test_first_seen_is_a_sample_tick_that_agrees_with_the_frames(vantage_on):
    """Criterion 2: `first_seen.A` is a multiple of CHECK_EVERY (one sim second), strictly earlier than the first frame in which an A unit sees (the vantage geometry puts the
    first sight between two frames, so a first_seen read off the frames is later: audit Y1), and a frame at exactly that tick has one."""
    doc, _ = vantage_on
    a = doc["result"]["first_seen"]["A"]
    ticks = [f["tick"] for f in doc["frames"]]
    sees = [f["tick"] for f in doc["frames"] if any(u["seen"] for u in f["units"] if u["side"] == "A")]
    assert (a % CHECK_EVERY == 0, a < min(sees), a not in ticks or a in sees) == (True, True, True)


def test_first_seen_is_sampled_on_check_every_not_on_frames(tmp_path, monkeypatch):
    """Criterion 2, spec line 22 (audit Y1, saboteur T4): "the first sampled tick (every `CHECK_EVERY`, tick 0 included)". The runner reads the module constant at call time, so
    the vantage fixture is run with it patched to 10**9 (only tick 0 is sampled and the vantage A, 1200 wu from B, does not see there: null), and to 1, 3 and 7 ticks:
    `first_seen.A` is then the earliest multiple of the patched value at which A has sight, oracle the CHECK_EVERY=1 run's value rounded up to that multiple (A keeps sight
    once it has it). A `first_seen` taken from the frames (every 100 ticks), from a hard-coded cadence, or sampled every second or every other multiple (2 * CHECK_EVERY)
    finds a later tick for some value."""
    got = {}
    for n in (10**9, 1, 3, 7):
        monkeypatch.setattr(arena_run, "CHECK_EVERY", n)
        got[n] = run_ok(f8.vantage_layout("L-9819"), tmp_path / str(n), "--sight", "on", "--cap-seconds", "20")["result"].get("first_seen", {}).get("A", "no first_seen")
    exact = got[1]
    up = lambda n: -(-exact // n) * n if isinstance(exact, int) else exact
    want = {10**9: None, 1: exact, 3: up(3), 7: up(7)}
    assert (got, isinstance(exact, int)) == (want, True)


def test_control_sight_off_documents_carry_none_of_the_three_keys(vantage_off):
    """CONTROL (green today, must stay green), criterion 2: "With `--sight off` none of the three keys is written": no `seen` on any unit, no `sights`, no `first_seen`."""
    doc = vantage_off
    assert (any("seen" in u for f in doc["frames"] for u in f["units"]), "sights" in doc, "first_seen" in doc["result"]) == (False, False, False)


def test_sight_on_fight_files_are_byte_identical_on_a_rerun(tmp_path):
    """Constraints (spec line 15): same layout, seed and flags give byte-identical fight files, the new keys included (premise: the file has `first_seen`)."""
    lay, files = f8.vantage_layout("L-9808"), []
    for _ in range(2):   # the same directory twice: a fight file carries its layout's path
        run_ok(lay, tmp_path, "--sight", "on", "--cap-seconds", "20")
        files.append((tmp_path / "out" / "L-9808-s1.fight.json").read_bytes())
    assert files[0] == files[1] and b"first_seen" in files[0]


# ---------------------------------------------------------------- criterion 4: results.md, --control

@pytest.mark.parametrize("sight,head,cells,tail", [("on", NEW_HEAD, 10, ["0", "0"]), ("off", OLD_HEAD, 8, None)], ids=["on", "off-control-green"])
def test_results_md_has_the_first_seen_columns_with_sight_on_only(sight, head, cells, tail, tmp_path):
    """Criterion 4, spec line 24: with `--sight on` the header is NEW_HEAD (a ten-cell separator and rows, last two cells the tick or `-`: `0` and `0` on the open
    field); with `--sight off` the header and rows are stage 3's (8 cells). The off row is a CONTROL (green today)."""
    run_ok(f8.open_layout("L-9809"), tmp_path, "--sight", sight, "--cap-seconds", "1")
    got_head, sep, rows = result_rows(tmp_path / "out")
    assert (got_head, sep.count("---"), len(rows[0]), rows[0][8:] or None) == (head, cells, cells, tail)


def test_results_md_prints_a_dash_for_a_side_that_never_saw(vantage_on):
    """Criterion 4, spec line 24: "tick or `-`": the row prints each side's `first_seen` tick in its cell, and `-` for a side that never saw. Stage 4 fix F1 (2026-11-06): the
    vantage is real terrain, B climbs it and sees A from the midline, so both cells are ticks (B no earlier than A, the sample is a sim second); the dash is read from a fight whose sides never meet."""
    doc, d = vantage_on
    first = doc["result"]["first_seen"]
    assert first["B"] >= first["A"] and result_rows(d / "out")[2][0][8:] == [str(first["A"]), str(first["B"])]
    lay = f8.open_layout("L-9819")
    for u in lay["side_b"]["units"]:
        u["x"] += 1500.0   # 3800 wu apart, out of every sensor radius; one second of fight, nobody sees anyone
    for u in lay["side_a"]["units"]:
        u["x"] -= 1500.0
    d2 = d.parent / "dash"
    run_ok(lay, d2, "--sight", "on", "--cap-seconds", "1")
    assert result_rows(d2 / "out")[2][0][8:] == ["-", "-"]


def test_control_sight_writes_one_control_fight_per_seed_and_nothing_else(tmp_path):
    """Criterion 4, spec line 24 and ruling Q4: `--control sight --control-dir D` with `--seeds 2` writes `D/<id>-control-s1.fight.json` and `-s2` and no twin layout; each
    control document has `sight` "off", `movement_kind` 1, `orders.guard` true (hold:A, as applied), none of `seen`, `sights`, `first_seen`, and the main fight's
    `layout_path` (the original layout). The layout has no ground feature `features.bound` knows."""
    lay = f8.vantage_layout("L-9810")
    lay["predict_rate"] = 0.5
    path, ctl = fx.write(lay, tmp_path / "layouts"), tmp_path / "control"
    on = fx.run(path, tmp_path / "on", 1, "--sight", "on", "--cap-seconds", "5", "--seeds", "2", "--control-dir", ctl, "--control", "sight")
    files = ["L-9810-control-s1.fight.json", "L-9810-control-s2.fight.json"]
    docs = [snapshot.read(ctl / n) if (ctl / n).exists() else {} for n in files]
    main_paths = [snapshot.read(tmp_path / "on" / n.replace("-control", "")).get("layout_path") for n in files]
    assert (on.returncode, names(ctl), [d.get("sight") for d in docs], [d.get("movement_kind") for d in docs], [d.get("orders", {}).get("guard") for d in docs],
            [(any("seen" in u for f in d.get("frames", []) for u in f["units"]), "sights" in d, "first_seen" in d.get("result", {})) for d in docs],
            [d.get("layout_path") for d in docs]) == (0, files, ["off"] * 2, [1] * 2, [True] * 2, [(False, False, False)] * 2, main_paths)


def test_control_sight_without_a_control_dir_writes_nothing(tmp_path):
    """Criterion 4, spec line 24 and ruling Q4: `--control sight` without `--control-dir` (sight on) exits 0 and writes no control file anywhere: the output directory holds
    the main fight and `results.md` only, and the working directory (a scratch one, see `_scratch_cwd`) gets nothing but the layout and output directories. A chokepoint layout is used because a bound layout is the one that writes control files."""
    path = fx.write(fx.planar("chokepoint", "L-9817")[0], tmp_path / "layouts")   # a bound layout: the case where a control dir would otherwise get twin files
    proc = fx.run(path, tmp_path / "out", 1, "--sight", "on", "--cap-seconds", "1", "--control", "sight")
    assert (proc.returncode, names(tmp_path / "out"), names(Path.cwd())) == (0, ["L-9817-s1.fight.json", "results.md"], ["layouts", "out"])


def test_control_sight_is_written_for_a_layout_with_features_too(tmp_path):
    """Criterion 4, spec line 24: "for every layout, whether or not `features.bound(layout)`": a chokepoint layout (bound) with `--sight on --control sight` writes the
    sight-off control fight, the control names the original layout and no twin layout files are written."""
    ctl = tmp_path / "control"
    doc = run_ok(fx.planar("chokepoint", "L-9811")[0], tmp_path, "--sight", "on", "--cap-seconds", "5", "--control-dir", ctl, "--control", "sight")
    got = names(ctl)
    control = snapshot.read(ctl / "L-9811-control-s1.fight.json") if got else {}
    assert (got, control.get("sight"), control.get("layout_path")) == (["L-9811-control-s1.fight.json"], "off", doc["layout_path"])


def test_control_ground_is_the_default_control(tmp_path):
    """Criterion 4, spec line 24: "`--control ground` (default; today's twin)": the chokepoint run with `--control ground` writes the same three files (twin TOML,
    twin JSON, control fight) with the same bytes as the run without the flag."""
    def control_files(*extra):
        shutil.rmtree(tmp_path / "control", ignore_errors=True)
        run_ok(fx.planar("chokepoint", "L-9812")[0], tmp_path, "--sight", "off", "--cap-seconds", "5", "--control-dir", tmp_path / "control", *extra)
        return {n: (tmp_path / "control" / n).read_bytes() for n in names(tmp_path / "control")}
    default, explicit = control_files(), control_files("--control", "ground")
    assert (sorted(default), default == explicit) == (["L-9812-control-s1.fight.json", "L-9812-control.json", "L-9812-control.toml"], True)


def test_control_ground_with_sight_on_writes_the_twin_and_its_sight_on_fight(tmp_path):
    """Criterion 4, spec line 24 (audit Y6): "`--control ground` is allowed with `--sight on`": on a `features.bound` layout the run exits 0 and writes the twin layout (TOML
    and JSON, `features` emptied) and `D/<id>-control-s1.fight.json`, the twin fight with sight on (the stage 4 rule set: `seen` on the units, `orders.guard` as applied) whose
    `layout_path` is the twin TOML."""
    ctl = tmp_path / "control"
    lay = f8.cover_layout("L-9823")
    run_ok(lay, tmp_path, "--sight", "on", "--cap-seconds", "5", "--control-dir", ctl, "--control", "ground")
    files = names(ctl)
    twin = json.loads((ctl / "L-9823-control.json").read_text()) if "L-9823-control.json" in files else {}
    doc = snapshot.read(ctl / "L-9823-control-s1.fight.json") if "L-9823-control-s1.fight.json" in files else {"layout_path": "", "frames": [{"units": []}]}
    assert (files, twin.get("features"), doc.get("sight"), doc["layout_path"].endswith("L-9823-control.toml"), all("seen" in u for u in doc["frames"][0]["units"])) == (
        ["L-9823-control-s1.fight.json", "L-9823-control.json", "L-9823-control.toml"], [], "on", True, True)


def test_control_sight_needs_sight_on(tmp_path):
    """Criterion 4, spec line 24: "`--control sight` is only meaningful with `--sight on`; with `--sight off` it is a usage error (exit 2)": the same command exits 0
    with `--sight on` and 2 with `--sight off` (so the 2 is the rule and not an unknown flag)."""
    path = fx.write(f8.open_layout("L-9813"), tmp_path / "layouts")
    codes = {s: fx.run(path, tmp_path / ("out-" + s), 1, "--sight", s, "--cap-seconds", "1", "--control-dir", tmp_path / "control", "--control", "sight").returncode for s in ("on", "off")}
    assert codes == {"on": 0, "off": 2}


# ---------------------------------------------------------------- criterion 5: the vantage

def test_the_high_ground_sees_down_and_the_low_ground_never_sees_up(vantage_on):
    """Criterion 5, spec line 25 (R-005-09): in some frame an A unit's `seen` is non-empty; a B unit's `seen` is non-empty only while that unit is on layer 1 (a lower
    layer never sees up; stage 4 fix F1, 2026-11-06: the hill is terrain, so B sees A from the ramp's midline, when it is on the upper layer); `first_seen.A` is an int and
    `first_seen.B` is a tick no earlier than A's."""
    doc, _ = vantage_on
    units = [u for f in doc["frames"] for u in f["units"]]
    first = doc["result"]["first_seen"]
    assert (any(u["seen"] for u in units if u["side"] == "A"), any(u["seen"] and u["layer"] == 0 for u in units if u["side"] == "B"), isinstance(first["A"], int),
            isinstance(first["B"], int) and first["B"] >= first["A"]) == (True, False, True, True)


def test_the_high_ground_fires_down_and_is_never_hit(vantage_on):
    """Criterion 5, spec line 25: some B unit's hp falls below its tick-0 value in some frame, and no A unit's does in any frame before a B unit is on layer 1 (A fires
    down, B cannot see up; stage 4 fix F1, 2026-11-06: once B is on the ramp's upper half the fight is on equal terms)."""
    doc, _ = vantage_on
    start = {u["id"]: u["hp"] for u in doc["frames"][0]["units"]}
    low = [f for f in doc["frames"][:next(i for i, f in enumerate(doc["frames"]) if any(u["layer"] == 1 and u["side"] == "B" for u in f["units"]))]]
    hurt = {"A": any(u["hp"] < start[u["id"]] for f in low for u in f["units"] if u["side"] == "A"),
            "B": any(u["hp"] < start[u["id"]] for f in doc["frames"] for u in f["units"] if u["side"] == "B")}
    assert hurt == {"A": False, "B": True}


def test_control_the_sight_off_control_fight_has_the_high_ground_firing_down(tmp_path):
    """Criterion 5, spec line 25, control (ruling Q1): the vantage fixture with `--sight on --control-dir D --control sight`, 60 s: in the control document some A unit
    has a non-null `target` in some frame (everyone engages without sight; A fires down, reach 0 up 1 down)."""
    run_ok(f8.vantage_layout("L-9818"), tmp_path, "--sight", "on", "--cap-seconds", "60", "--control-dir", tmp_path / "control", "--control", "sight")
    control = snapshot.read(tmp_path / "control" / "L-9818-control-s1.fight.json") if names(tmp_path / "control") else {"frames": []}
    assert any(u["target"] is not None for f in control["frames"] for u in f["units"] if u["side"] == "A")


def test_nobody_fires_at_what_the_cover_hides(tmp_path):
    """Criteria 5 and 6, spec lines 25 and 26, and the summary ("units fire only at what their side sees", R-093-02; cover blocks sight, not hits, R-007-04; audit Y4): the
    cover fixture with the sides moved to x 1850 and 2150 (300 wu apart, inside the Vanguard weapon range, the three boxes between them): with sight on no unit has a target in
    any frame that crosses a box; the same fight with targeting by sight off (`--control sight`) has targets across the boxes. The vantage fixture cannot tell the two apart.
    Stage 4 fix F2 (2026-11-06): the boxes block their snapped cells only (three 100 x 100 cells, y 1900 to 2200), so the rows of units at y 1860 have a clear line and may
    fire, and a unit with a clear line lets its side see (R-093-02 is the side's visible set), so a teammate behind a box may hold the target: the test reads "no target across a
    blocked cell that the unit's side does not see"."""
    lay = f8.cover_layout("L-9822")
    for u in lay["side_a"]["units"]:
        u["x"] = 1850.0
    for u in lay["side_b"]["units"]:
        u["x"] = 2150.0
    on = run_ok(lay, tmp_path, "--sight", "on", "--cap-seconds", "5", "--control-dir", tmp_path / "control", "--control", "sight")
    control = snapshot.read(tmp_path / "control" / "L-9822-control-s1.fight.json") if names(tmp_path / "control") else {"frames": []}
    def across(d, unseen_only):
        """(unit, target) pairs whose segment crosses a blocked cell; `unseen_only`: only those whose target no unit of the unit's side lists in `seen` (R-093-02 is the side's set)."""
        cells = f8.blocked_cells(lay)
        out = []
        for f in d["frames"]:
            pos = {u["id"]: (u["x"], u["y"]) for u in f["units"]}
            side = {u["id"]: u["side"] for u in f["units"]}
            side_sees = {s: {e for u in f["units"] if u["side"] == s for e in u.get("seen", [])} for s in "AB"}
            out += [(u["id"], u["target"]) for u in f["units"] if u["target"] is not None and f8.crosses(pos[u["id"]], pos[u["target"]], cells)
                    and not (unseen_only and u["target"] in side_sees[side[u["id"]]])]
        return out
    assert (across(on, True), bool(across(control, False))) == ([], True)


# ---------------------------------------------------------------- criterion 6: cover and guard

def frame0(tmp_path, boxes):
    lay = f8.cover_layout("L-9814" if boxes else "L-9815", boxes=boxes)
    return lay, run_ok(lay, tmp_path, "--sight", "on", "--cap-seconds", "1")["frames"][0]["units"]


def test_cover_hides_every_pair_whose_segment_crosses_a_box(tmp_path):
    """Criterion 6, spec line 26 (R-007-01, R-007-02): at frame 0 of the cover fixture no unit lists, in `seen`, a unit of the other side across a box's engine cells.
    Premise asserted: there is at least one crossing pair."""
    lay, units = frame0(tmp_path, True)
    pairs, seen = f8.crossing_pairs(lay, units), {u["id"]: u["seen"] for u in units}
    assert pairs and [p for p in pairs if p[1] in seen[p[0]]] == []


def test_without_the_boxes_the_same_pairs_are_seen(tmp_path):
    """Criterion 6, spec line 26, positive control: the same units with `features` emptied: every pair the boxes would hide is seen (a lists b), so the hiding above is
    the cover and not the distance."""
    lay, units = frame0(tmp_path, False)
    pairs, seen = f8.crossing_pairs(f8.cover_layout("L-9814"), units), {u["id"]: u["seen"] for u in units}
    assert pairs and [p for p in pairs if p[1] not in seen[p[0]]] == []


def test_the_guarded_holder_stays_within_the_guard_radius(vantage_on):
    """Criterion 6, spec line 26 (R-096-08): in the vantage fixture the holder A is guarded (`orders.guard`), the units walk (`movement_kind` 1) and no A unit is ever
    more than GUARD_RADIUS (200 wu) from its tick-0 position in any frame."""
    doc, _ = vantage_on
    start = {u["id"]: (u["x"], u["y"]) for u in doc["frames"][0]["units"]}
    far = max(((u["x"] - start[u["id"]][0]) ** 2 + (u["y"] - start[u["id"]][1]) ** 2) ** 0.5 for f in doc["frames"] for u in f["units"] if u["side"] == "A")
    assert (doc["orders"].get("guard"), doc.get("movement_kind"), far <= GUARD_RADIUS) == (True, 1, True)
