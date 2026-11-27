# Rule pins: R-091-23, R-091-24 (lab harness story H-091, lab stage 5, the pinned flank probe and the slope flag)
"""LAB stage 5, added 2026-11-27 (story H-091, "Added 2026-11-27 after the first measurements").

Rule words (docs/stories/H-091.md):
  R-091-23  A seventh probe scene `pinned_flank` exists beside the others, marked DRAFT and "Architect-made probe, not a catalogue layout": the same holding block of 8 Vanguards facing
            east; a front group of 8 Vanguards to the east and a rear group of 8 Vanguards to the west, farther away, so that the rear group's first hit comes at least
            DRAFT-stage5-pinned-delay 100 ticks after the front group's first hit; order rule R2 (the holder holds, every attacker attack-moves onto the holder's centre of mass). It passes
            the preflight with `--facing on` and runs to a wipe at seed 1. With `--arc-deg 90` the holders receive rear-class hits on at least DRAFT-stage5-pinned-rear-ticks 50 distinct
            ticks (the lock keeps them facing their front target, R-087-03 as written).
  R-091-24  With `--facing on` the runner takes `--slope-up-div V`: it sets `OM_TP_SLOPE_UP_DIV` to V for that fight and writes V in `stage5.slope_up_div`; without the flag the engine's own
            value (1.1) is used and written. With facing off the flag is refused with a usage error. A unit climbing with V 2.0 has a slope-to-flat speed ratio within 0.05 of 0.5; with the
            default, within 0.05 of 0.909.

Interface assumptions the story leaves open (each is the test writer's pick, reported):
  - The file is docs/northstar/research/layer_dynamics/arena/stage5/pinned_flank.toml (the brief names it); its id is not tested (the story gives none). The holder is the side the layout's
    `orders` ("hold:A" or "hold:B") names, as in test_stage5_scenes.py; the attackers are the other side, one group with x east of the holder's centre of mass, one with x west of it.
  - "The same holding block as front.toml": side A's unit rows (role, x, y, facing, layer) equal front.toml's, and are 8 Vanguards, 2 ranks of 4, 40 wu apart, facing east (0.0), `orders` the
    same as front.toml's ("hold:A"). "Farther away": the rear group's nearest unit is farther from the holder's centre of mass than the front group's nearest unit.
  - "Recorded every tick" is the lab's every-tick writer (scripts.skilllab.arena.closeup, which takes --facing and --arc-deg) for R-091-23. For R-091-24 the story names the runner
    (run.py) only: the every-tick record is made by calling run.py's own main with `run.fight` forced to every=1, `run._document` to dense_every=1 and `snapshot.write` and `snapshot.read` replaced by a
    plain JSON write and read (both refuse more than the frame limit; closeup does the same plain write). closeup is NOT asked to take `--slope-up-div` (the story does not name it): a gap, reported.
  - A hit on a holder is an entry of a frame's `hits` (R-091-11) whose victim is a unit of the holder's side; its tick is the entry's own `tick`; "rear-class" is `cls == "rear"`.
  - "Usage error": a non-zero exit (argparse's 2) whose stderr has an `error:` line naming `--slope-up-div`, that is not argparse's "unrecognized arguments" (that is what the flag gets today: the
    flag must be KNOWN and refused, not unknown), and writes no fight file.
  - "Slope-to-flat speed ratio" is stage5_measures(doc)["climb"][unit]["ratio"] (R-091-14), checked for each of the 8 attackers of climb_slope.toml (the scene exists on this tree).
Controls (green today): front.toml every tick with `--facing on --arc-deg 90`: the holders take front-class hits from tick 1 and no rear-class hit (the hit readers work); a scratch pinned
flank built from the fixtures (the flank fixture's holder and east group, a west group of 8 with its front rank 800 wu out) gives first front hit tick 1, first rear hit tick 121, rear-class hits
on 180 ticks (dumped 2026-11-27: so the two drafted numbers 100 and 50 are satisfiable in this engine); the default run of climb_slope writes slope_up_div 1.1 and its attackers' climb ratio
is within 0.05 of 0.909 (dumped: 0.899 to 0.959 over the 8 units); facing off without the flag runs.
Red today: pinned_flank.toml does not exist; the runner has no `--slope-up-div` (argparse: unrecognized arguments), so neither the written value, the 0.5 ratio nor the refusal exists."""
import json
import tomllib
from pathlib import Path

import pytest

import h063_fixtures as fx
import h091_fixtures as f9
from scripts.skilllab.arena import closeup, run as arena_run
from scripts.skilllab.arena.stage5_measures import stage5_measures
from scripts.skilllab.catalogue import produce

PROBE_DIR = fx.ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "arena" / "stage5"
PINNED = PROBE_DIR / "pinned_flank.toml"
PHRASES = ("DRAFT", "Architect-made probe, not a catalogue layout")
ARC_DEG = "90"                 # DRAFT-stage5-arc-deg
PINNED_DELAY = 100             # DRAFT-stage5-pinned-delay (ticks)
PINNED_REAR_TICKS = 50         # DRAFT-stage5-pinned-rear-ticks (distinct ticks)
FACING_EAST_TOL = 0.001        # radians; a layout writes facing to 4 decimals
SPACING_WU = 40.0
CLIMB_TOL = 0.05               # the story: "within 0.05"
RATIO_DEFAULT, RATIO_V2 = 0.909, 0.5
V2 = 2.0                       # DRAFT-stage5-climb-compare
ENGINE_DEFAULT = 1.1           # the engine's own OM_TP_SLOPE_UP_DIV


# ------------------------------------------------------------------------------------------------ files and runs

def load_pinned():
    """The layout dict of pinned_flank.toml; a missing file is a failed test with the path in the message."""
    if not PINNED.is_file():
        pytest.fail("R-091-23: the probe file %s does not exist (docs/stories/H-091.md, R-091-23)" % PINNED.relative_to(fx.ROOT))
    with open(PINNED, "rb") as f:
        return tomllib.load(f)


def load_front():
    with open(PROBE_DIR / "front.toml", "rb") as f:
        return tomllib.load(f)


def header(path):
    """The block of `#` comment lines before the first key of the file."""
    lines = []
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if s.startswith("#"):
            lines.append(s.lstrip("#").strip())
        elif s:
            break
    return "\n".join(lines)


def every_tick(path, out, *extra):
    """The closeup CLI (a frame every tick, `--facing on --arc-deg 90`) on the layout file `path`, in-process; returns (exit code, the fight document or None)."""
    code = closeup.main(["--layout", str(path), "--seed", "1", "--sight", "off", "--every-ticks", "1", "--out", str(out), "--facing", "on", "--arc-deg", ARC_DEG, *extra])
    files = sorted(Path(out).glob("*.fight.json"))
    return code, (json.loads(files[0].read_text()) if files else None)


def holder_hits(doc, holder):
    """Every entry of every frame's `hits` whose victim belongs to side `holder` ("A" or "B"), by the entry's own tick."""
    side = {u["id"]: u["side"] for u in doc["frames"][0]["units"]}
    return [h for f in doc["frames"] for h in f["hits"] if side[h["v"]] == holder]


def hit_ticks(hits, cls):
    return sorted({h["tick"] for h in hits if h["cls"] == cls})


def holder_letter(lay):
    assert lay.get("orders") in ("hold:A", "hold:B"), "the layout's orders %r name no holder" % lay.get("orders")
    return lay["orders"][-1]


def run_every_tick_through_run_py(path, out, *extra, monkeypatch):
    """run.py's own CLI (`arena_run.main`) on layout file `path` with `--facing on --arc-deg 90` and `extra`, recording every tick (module docstring); returns (process, document or None)."""
    real_fight, real_document = arena_run.fight, arena_run._document
    monkeypatch.setattr(arena_run, "fight", lambda *a, **k: real_fight(*a, **{**k, "every": 1}))
    monkeypatch.setattr(arena_run, "_document", lambda *a, **k: real_document(*a, **{**k, "dense_every": 1}))
    monkeypatch.setattr(arena_run.snapshot, "write", lambda doc, p: Path(p).write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8"))
    monkeypatch.setattr(arena_run.snapshot, "read", lambda p: json.loads(Path(p).read_text(encoding="utf-8")))   # main reads the file back, and read refuses more than the frame limit too
    proc = fx.run(path, out, 1, "--facing", "on", "--arc-deg", ARC_DEG, *extra)
    files = sorted(Path(out).glob("*.fight.json"))
    return proc, (json.loads(files[0].read_text()) if files else None)


def climb_ratios(doc):
    climb = stage5_measures(doc)["climb"]
    assert climb != "not measured", "the file is not an every-tick file"
    return climb


@pytest.fixture(scope="module")
def pinned_every_tick(tmp_path_factory):
    """A callable returning (exit code, document) of pinned_flank.toml recorded every tick with `--facing on --arc-deg 90`, run once on the first call (a missing file fails the calling test, not
    the fixture)."""
    cache = []

    def get():
        if not cache:
            load_pinned()
            cache.append(every_tick(PINNED, tmp_path_factory.mktemp("pinned_every_tick")))
        return cache[0]
    return get


@pytest.fixture(scope="module")
def climb_default(tmp_path_factory):
    """(process, document) of climb_slope.toml through run.py, every tick, no flag; run once."""
    mp = pytest.MonkeyPatch()
    try:
        return run_every_tick_through_run_py(PROBE_DIR / "climb_slope.toml", tmp_path_factory.mktemp("climb_default"), monkeypatch=mp)
    finally:
        mp.undo()


@pytest.fixture(scope="module")
def climb_v2(tmp_path_factory):
    """(process, document) of climb_slope.toml through run.py, every tick, `--slope-up-div 2.0`; run once."""
    mp = pytest.MonkeyPatch()
    try:
        return run_every_tick_through_run_py(PROBE_DIR / "climb_slope.toml", tmp_path_factory.mktemp("climb_v2"), "--slope-up-div", V2, monkeypatch=mp)
    finally:
        mp.undo()


# ------------------------------------------------------------------------------------------------ R-091-23 controls

def test_R_091_23_control_front_probe_holders_take_front_hits_from_tick_1_and_no_rear_hits(tmp_path):
    """R-091-23 control: on front.toml (the story's front scene, on this tree) recorded every tick with `--facing on --arc-deg 90` the hit readers of this file see the holders
    (side A) take front-class hits from tick 1 and no rear-class hit at all, so a red below means the pinned scene is missing or wrong, not that the readers are blind."""
    code, doc = every_tick(PROBE_DIR / "front.toml", tmp_path)
    assert code == 0 and doc is not None
    hits = holder_hits(doc, holder_letter(load_front()))
    assert hit_ticks(hits, "front")[:1] == [1], "first front-class hit tick: %s" % hit_ticks(hits, "front")[:1]
    assert hit_ticks(hits, "rear") == []


def test_R_091_23_control_a_pinned_flank_built_from_the_fixtures_meets_both_drafted_numbers(tmp_path):
    """R-091-23 control (the two drafted numbers are satisfiable): the flank fixture's holder block and 8 attackers from the east, plus 8 attackers from the west with their front rank 800 wu
    from the holder's centre, hold:A, run every tick with `--facing on --arc-deg 90`: the first rear-class hit on a holder is at least 100 ticks after the first front-class hit and the
    holders take rear-class hits on at least 50 distinct ticks (dumped 2026-11-27: ticks 1 and 121, 180 rear ticks)."""
    lay = f9.flank_layout("L-9498", "east")
    lay["side_b"] = {"headcount": 16, "units": lay["side_b"]["units"] + f9.attacker_block("west", distance=800.0)}
    proc, doc = f9.closeup_doc(lay, tmp_path, 1, "--facing", "on", "--arc-deg", ARC_DEG)
    assert proc.returncode == 0 and doc is not None, proc.stdout + proc.stderr
    hits = holder_hits(doc, "A")
    front, rear = hit_ticks(hits, "front"), hit_ticks(hits, "rear")
    assert front and rear, "front ticks %s, rear ticks %s" % (front[:3], rear[:3])
    assert rear[0] - front[0] >= PINNED_DELAY, "rear first hit %d, front first hit %d" % (rear[0], front[0])
    assert len(rear) >= PINNED_REAR_TICKS, "%d rear-class ticks" % len(rear)


# ------------------------------------------------------------------------------------------------ R-091-23 the scene

def test_R_091_23_pinned_flank_exists_marked_draft_and_architect_made_probe():
    """R-091-23: "A seventh probe scene `pinned_flank` exists beside the others, marked DRAFT and 'Architect-made probe, not a catalogue layout'": the file is in the stage5 directory and
    its header comment holds both phrases."""
    load_pinned()
    head = header(PINNED)
    for phrase in PHRASES:
        assert phrase in head, "header lacks %r" % phrase


def test_R_091_23_pinned_flank_has_front_toml_holding_block_8_vanguards_2_ranks_of_4_40_wu_apart_facing_east_holding():
    """R-091-23: "the same holding block of 8 Vanguards facing east": the holder's rows equal front.toml's, are 8 Vanguards in 2 ranks of 4, 40 wu apart, facing east (0.0), and the order is
    the holder holds (`orders` the same as front.toml's, "hold:A")."""
    lay, front = load_pinned(), load_front()
    mine, theirs = lay["side_a"]["units"], front["side_a"]["units"]
    key = lambda u: (u["role"], u["x"], u["y"], u["facing"], u["layer"])
    assert sorted(map(key, mine)) == sorted(map(key, theirs)), "side A is not front.toml's holding block"
    assert len(mine) == 8 and {u["role"] for u in mine} == {"Vanguard"}
    xs, ys = sorted({u["x"] for u in mine}), sorted({u["y"] for u in mine})
    assert len(xs) == 2 and xs[1] - xs[0] == SPACING_WU, "ranks at x %s" % xs
    assert len(ys) == 4 and all(b - a == SPACING_WU for a, b in zip(ys, ys[1:])), "files at y %s" % ys
    assert all(abs(u["facing"]) <= FACING_EAST_TOL for u in mine), "not all facing east"
    assert lay["orders"] == front["orders"] == "hold:A"


def test_R_091_23_pinned_flank_has_a_front_group_of_8_vanguards_to_the_east_and_a_farther_rear_group_of_8_to_the_west():
    """R-091-23: "a front group of 8 Vanguards to the east and a rear group of 8 Vanguards to the west, farther away": the attacking side is 16 Vanguards, 8 with x east of the holder's centre
    of mass and 8 west of it, and the western group's nearest unit is farther from that centre than the eastern group's."""
    lay = load_pinned()
    holder = "side_a" if holder_letter(lay) == "A" else "side_b"
    attackers = lay["side_b" if holder == "side_a" else "side_a"]["units"]
    units = lay[holder]["units"]
    cx, cy = sum(u["x"] for u in units) / len(units), sum(u["y"] for u in units) / len(units)
    east, west = [u for u in attackers if u["x"] > cx], [u for u in attackers if u["x"] < cx]
    assert len(east) == 8 and len(west) == 8 and len(attackers) == 16, "%d east, %d west, %d attackers" % (len(east), len(west), len(attackers))
    assert {u["role"] for u in attackers} == {"Vanguard"}
    near = lambda g: min(((u["x"] - cx) ** 2 + (u["y"] - cy) ** 2) ** 0.5 for u in g)
    assert near(west) > near(east), "rear group nearest %.1f wu, front group nearest %.1f wu" % (near(west), near(east))


def test_R_091_23_pinned_flank_passes_the_preflight_r1_to_r8():
    """R-091-23: "It passes the preflight": `check_layout` names no rule (R1 to R7) and `unreachable` (R8) names no unit."""
    lay = load_pinned()
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == [], "pinned_flank.toml breaks %s" % produce.check_layout(lay, produce.presets(), produce.rules())
    assert arena_run.unreachable(lay) is None, "R8: %s cannot reach its orders point" % arena_run.unreachable(lay)


def test_R_091_23_pinned_flank_runs_to_a_wipe_at_seed_1_with_facing_on(tmp_path):
    """R-091-23: "It passes the preflight with `--facing on` and runs to a wipe at seed 1": the CLI with `--facing on` exits 0 with no REJECT line, writes the file, and `result.end` is
    "wipe"."""
    load_pinned()
    proc = fx.run(PINNED, tmp_path, 1, "--facing", "on")
    assert proc.returncode == 0 and "REJECT" not in proc.stdout, "exit %s; %s" % (proc.returncode, (proc.stdout + proc.stderr)[-400:])
    doc = json.loads(next(tmp_path.glob("*.fight.json")).read_text())
    assert doc["stage5"]["arc_deg"] == 90
    assert doc["result"]["end"] == "wipe", "ended %r at tick %s, not in a wipe" % (doc["result"]["end"], doc["result"]["ticks"])


def test_R_091_23_the_rear_groups_first_hit_comes_at_least_100_ticks_after_the_front_groups(pinned_every_tick):
    """R-091-23: "so that the rear group's first hit comes at least DRAFT-stage5-pinned-delay 100 ticks after the front group's first hit": with `--facing on --arc-deg 90` recorded every tick, the
    first rear-class hit on a holder is at least 100 ticks after the first front-class hit on a holder."""
    code, doc = pinned_every_tick()
    assert code == 0 and doc is not None
    hits = holder_hits(doc, holder_letter(load_pinned()))
    front, rear = hit_ticks(hits, "front"), hit_ticks(hits, "rear")
    assert front, "the holders took no front-class hit"
    assert rear, "the holders took no rear-class hit"
    assert rear[0] - front[0] >= PINNED_DELAY, "first rear-class hit tick %d, first front-class hit tick %d: %d ticks apart" % (rear[0], front[0], rear[0] - front[0])


def test_R_091_23_the_holders_take_rear_class_hits_on_at_least_50_distinct_ticks(pinned_every_tick):
    """R-091-23: "With `--arc-deg 90` the holders receive rear-class hits on at least DRAFT-stage5-pinned-rear-ticks 50 distinct ticks": the distinct ticks of the rear-class entries in the
    every-tick file's `hits` on the holders number at least 50."""
    code, doc = pinned_every_tick()
    assert code == 0 and doc is not None
    rear = hit_ticks(holder_hits(doc, holder_letter(load_pinned())), "rear")
    assert len(rear) >= PINNED_REAR_TICKS, "rear-class hits on %d distinct ticks" % len(rear)


# ------------------------------------------------------------------------------------------------ R-091-24

def test_R_091_24_control_the_default_run_writes_the_engines_1_1_and_the_attackers_climb_at_0_909(climb_default):
    """R-091-24 control (green today): "without the flag the engine's own value (1.1) is used and written ... with the default, within 0.05 of 0.909": climb_slope.toml through run.py with
    `--facing on`, no flag, every tick: `stage5.slope_up_div` is 1.1 and each of the 8 attackers' slope-to-flat ratio is within 0.05 of 0.909."""
    proc, doc = climb_default
    assert proc.returncode == 0 and doc is not None, proc.stdout + proc.stderr
    assert doc["stage5"]["slope_up_div"] == ENGINE_DEFAULT
    climb = climb_ratios(doc)
    assert len(climb) == 8, "%d units climbed" % len(climb)
    off = {u: c["ratio"] for u, c in climb.items() if c["ratio"] is None or abs(c["ratio"] - RATIO_DEFAULT) > CLIMB_TOL}
    assert not off, "ratios not within %.2f of %.3f: %s" % (CLIMB_TOL, RATIO_DEFAULT, off)


def test_R_091_24_control_facing_off_without_the_flag_runs(tmp_path):
    """R-091-24 control (green today): the refusal below is of the flag, not of the layout: climb_slope.toml with facing off and no `--slope-up-div` exits 0 and writes its fight file."""
    proc = fx.run(PROBE_DIR / "climb_slope.toml", tmp_path, 1)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert list(tmp_path.glob("*.fight.json"))


def test_R_091_24_slope_up_div_is_written_in_the_stage5_block(tmp_path):
    """R-091-24: "With `--facing on` the runner takes `--slope-up-div V`: it sets `OM_TP_SLOPE_UP_DIV` to V for that fight and writes V in `stage5.slope_up_div`": with V 2.0 the run exits 0
    and the file's `stage5.slope_up_div` is 2.0 (the engine's 1.1 otherwise)."""
    proc = fx.run(PROBE_DIR / "climb_slope.toml", tmp_path, 1, "--facing", "on", "--slope-up-div", V2)
    assert proc.returncode == 0, "exit %s: %s" % (proc.returncode, (proc.stdout + proc.stderr)[-300:])
    doc = json.loads(next(tmp_path.glob("*.fight.json")).read_text())
    assert doc["stage5"]["slope_up_div"] == V2


def test_R_091_24_a_unit_climbing_with_v_2_0_has_a_slope_to_flat_speed_ratio_within_0_05_of_0_5(climb_v2):
    """R-091-24: "A unit climbing with V 2.0 has a slope-to-flat speed ratio within 0.05 of 0.5": climb_slope.toml through run.py with `--facing on --slope-up-div 2.0`, recorded every tick:
    each of the 8 attackers' ratio (stage5_measures climb) is within 0.05 of 0.5 (the flag moves the climb, not only the number written)."""
    proc, doc = climb_v2
    assert proc.returncode == 0 and doc is not None, "exit %s: %s" % (proc.returncode, (proc.stdout + proc.stderr)[-300:])
    climb = climb_ratios(doc)
    assert len(climb) == 8, "%d units climbed" % len(climb)
    off = {u: c["ratio"] for u, c in climb.items() if c["ratio"] is None or abs(c["ratio"] - RATIO_V2) > CLIMB_TOL}
    assert not off, "ratios not within %.2f of %.1f: %s" % (CLIMB_TOL, RATIO_V2, off)


def test_R_091_24_the_flag_is_refused_with_facing_off_by_a_usage_error(tmp_path):
    """R-091-24: "With facing off the flag is refused with a usage error": `--slope-up-div 2.0` without `--facing on` exits non-zero, with an `error:` line naming `--slope-up-div` that is not
    argparse's "unrecognized arguments" (the flag must be known and refused), and writes no fight file."""
    proc = fx.run(PROBE_DIR / "climb_slope.toml", tmp_path, 1, "--slope-up-div", V2)
    assert proc.returncode != 0, "exit %s: the flag was accepted with facing off" % proc.returncode
    errors = [line for line in proc.stderr.splitlines() if "error:" in line]
    assert errors and "--slope-up-div" in errors[-1], "stderr: %s" % proc.stderr[-300:]
    assert "unrecognized" not in errors[-1], "the flag is unknown to the runner, not refused: %s" % errors[-1]
    assert not list(tmp_path.glob("*.fight.json"))
