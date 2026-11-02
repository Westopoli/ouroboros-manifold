# spec: docs/stories/H-053.md (arena-stage2-roles-ranges-winrates), "What stage 2 adds" and "Interfaces" items 1, 5, 6; Flag client (library part, no scene of its own)
"""H-053, the win rate over seeds: `scripts/skilllab/arena/rate.py` and `run.py --seeds N`.

Story lines proved here (docs/stories/H-053.md):
  "The runner gains `--seeds N` (DRAFT-seeds-per-layout 20, Westley's rule: predictions are probabilities); one `fight.json` per seed, plus `<id>.rate.json`:
   `{wins_a, wins_b, stalls, seeds, rate_a, predict_rate, agree}`."
  "Agree when `|rate_a - predict_rate| <= DRAFT-rate-band 0.10` ... Any stall is listed by seed and brought to him."
  Interfaces 1: "`rate(fights, predict_rate, band=0.10) -> dict` ... Keys: `layout_id`, `seeds` (the list of seed numbers run), `wins_a`, `wins_b`, `stalls`,
   `stall_seeds` ..., `none_seeds` ..., `rate_a` = `wins_a / len(seeds)` (stalls and none count as no win for either side), `predict_rate`, `band`, `agree`
   (`abs(rate_a - predict_rate) <= band` and no stall and no none seed), `firing_capable` (`{"A": mean, "B": mean}`), `median_seed` (the seed whose fight has the
   median tick count; lower seed on ties)."
  Interfaces 5: "the first-contact point is the position, at the first-shot frame, of the unit whose hp dropped first (lowest unit id on ties); a side's
   `firing_capable` is the count of its units alive at frame 0 whose role range ... reaches that point from the unit's frame-0 position (`distance <= range`);
   the rate file carries the mean over seeds per side, rounded to one decimal."
  Tests line: "20 seeds of a lopsided fixture give rate 1.0 and agree with 0.98; a stall seed is counted and listed; positive control: a fixture with predict_rate 0.0
   disagrees".

Premises dumped (checked on the stage 1 branch b7ef1b2f merged with origin/main, 2026-11-01): Engine roster ranges via `Engine.type_stats(w, type_id)["attack_range"]`:
Raider 200, Interceptor 250, Vanguard 300, Warden 350, Bombard 1200, Bastion 800. The runner today takes `--seed` (required), writes `<out>/<id>-s<seed>.fight.json`
and `results.md`; it has no `--seeds`, no rate file, and `scripts/skilllab/arena/rate.py` does not exist.
Not pinned (the story does not say): which seed numbers `--seeds N` runs from `--seed S`; the tests read them from the rate file's `seeds` list. No test reads a
boundary of the band (0.10 is a float edge); tests sit clear of it. The library tests pass synthetic fight dicts that validate under `snapshot.validate`."""
import copy
import importlib.util
import json
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

RATE_MODULE = "scripts.skilllab.arena.rate"
RUN_MODULE = "scripts.skilllab.arena.run"
PITCH = 40.0
RATE_KEYS = {"layout_id", "seeds", "wins_a", "wins_b", "stalls", "stall_seeds", "none_seeds", "rate_a", "predict_rate", "band", "agree", "firing_capable",
             "median_seed"}


# ---------------------------------------------------------------- fixtures

def fight(seed, winner="A", ticks=1000, layout_id="L-9100"):
    """A valid om-fight-2 document with no shot (hp never drops), the result overridden: only seed, winner and ticks matter to the win count."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    doc["layout_id"], doc["seed"] = layout_id, seed
    res = doc["result"]
    res["winner"], res["ticks"] = winner, ticks
    res["predict"], res["agree"] = "A", winner == "A"   # the checker ties agree to winner == predict
    if winner == "stall":
        res.update({"end": "silence", "stall": True, "survivors": [2, 2], "capped": False})
    elif winner == "none":
        res.update({"end": "wipe", "stall": False, "survivors": [0, 0], "capped": False})
    return doc


def contact_fight(seed, extra_in_range=0, layout_id="L-9101"):
    """A fight whose first hp drop is B's unit 11 on frame 1, at (1000, 500). Frame 0 units (alive): side A Raider at 150 from the point (in range 200), Raider at
    500 (out), Bombard at 1000 (in, 1200), Vanguard at 350 (out, 300), plus `extra_in_range` Wardens at 300 (in, 350); side B Vanguard 11 at the point (in, 300)
    and Vanguard 12 at 1000 from it (out). So A has 2 + extra, B has 1."""
    px, py = 1000.0, 500.0
    rows = [("A", "Raider", px - 150), ("A", "Raider", px - 500), ("A", "Bombard", px - 1000), ("A", "Vanguard", px - 350)]
    rows += [("A", "Warden", px - 300)] * extra_in_range
    units = [{"id": i + 1, "side": s, "role": r, "x": x, "y": py, "layer": 0, "facing": 0.0, "hp": 100.0, "alive": True, "target": None}
             for i, (s, r, x) in enumerate(rows)]
    units.append({"id": 11, "side": "B", "role": "Vanguard", "x": px, "y": py, "layer": 0, "facing": 3.14, "hp": 100.0, "alive": True, "target": None})
    units.append({"id": 12, "side": "B", "role": "Vanguard", "x": px + 1000, "y": py, "layer": 0, "facing": 3.14, "hp": 100.0, "alive": True, "target": None})
    alive = [sum(u["side"] == s for u in units) for s in "AB"]
    f0 = {"tick": 0, "alive": alive, "units": copy.deepcopy(units)}
    f1 = {"tick": 100, "alive": alive, "units": copy.deepcopy(units)}
    f2 = {"tick": 200, "alive": alive, "units": copy.deepcopy(units)}
    for u in f1["units"]:   # on frame 1 the A units have moved and B's unit 11 is hurt; the point is where unit 11 stands on frame 1
        if u["id"] == 11:
            u["hp"], u["x"], u["y"] = 90.0, px, py
        elif u["side"] == "A":
            u["x"] += 25.0
    for u in f2["units"]:
        if u["id"] == 11:
            u["hp"], u["x"] = 70.0, px + 300.0   # later movement of the damaged unit must not move the contact point
    doc = fight(seed, layout_id=layout_id)
    doc["frames"] = [f0, f1, f2]
    doc["result"].update({"survivors": alive, "ticks": 200})
    return doc


def load_rate():
    if importlib.util.find_spec(RATE_MODULE) is None:
        pytest.fail("scripts/skilllab/arena/rate.py is missing: H-053 (win rate over seeds) is not built")
    return importlib.import_module(RATE_MODULE)


def layout_toml(layout_id, na, nb, predict_rate, tmp):
    """A 12:8 (or na:nb) Vanguard open-field layout as TOML with a top-level `predict_rate` (A bigger, so A wins)."""
    def block(n, x0, step):
        return [{"role": "Vanguard", "x": x0 + (i // 4) * step * PITCH, "y": 1980.0 + (i % 4) * PITCH, "facing": 0.0 if step < 0 else 3.1416, "layer": 0}
                for i in range(n)]
    layout = {"id": layout_id, "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "A", "predict_why": "test fixture", "verdict": "",
              "feedback": "", "side_a": {"headcount": na, "units": block(na, 1800.0, -1.0)}, "side_b": {"headcount": nb, "units": block(nb, 2200.0, 1.0)}}
    assert produce.check_layout(layout, produce.presets(), produce.rules()) == []
    path = Path(tmp) / (layout_id + ".toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("predict_rate = %r\n" % predict_rate + produce.dump_toml(layout))
    return path


def run_seeds(layout_path, out, seeds):
    if importlib.util.find_spec(RUN_MODULE) is None:
        pytest.fail("scripts/skilllab/arena/run.py is missing")
    return subprocess.run([sys.executable, "-m", RUN_MODULE, "--layout", str(layout_path), "--seed", "1", "--seeds", str(seeds), "--out", str(out)],
                          cwd=ROOT, capture_output=True, text=True, timeout=900)


# ---------------------------------------------------------------- positive controls (green today)

def test_control_fixtures_validate_and_carry_the_numbers_the_detectors_read(tmp_path):
    """H-053 Interfaces 1 and 5. Control: every synthetic fight validates under the checker, a stall fixture is a real stall (silence end, both sides alive), the
    contact fixture's first hp drop is unit 11 on frame 1 and the ranges the fixture assumes are the engine's, so a red below is the missing rate.py."""
    for w in ("A", "B", "stall"):   # "none" is not valid under today's checker: see test_checker_accepts_winner_none
        assert snapshot.validate(fight(1, w)) == [], w
    st = fight(1, "stall")
    assert st["result"]["end"] == "silence" and st["result"]["survivors"] == [2, 2]
    doc = contact_fight(1)
    assert snapshot.validate(doc) == []
    f0, f1 = doc["frames"][0], doc["frames"][1]
    dropped = [b["id"] for a, b in zip(f0["units"], f1["units"]) if b["hp"] < a["hp"]]
    assert dropped == [11]
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(1)
    try:
        got = {r: e.type_stats(w, e.type_id(r))["attack_range"] for r in ("Raider", "Vanguard", "Warden", "Bombard")}
    finally:
        e.free_world(w)
    assert got == {"Raider": 200.0, "Vanguard": 300.0, "Warden": 350.0, "Bombard": 1200.0}


# ---------------------------------------------------------------- the library

def test_twenty_all_a_seeds_give_rate_one_and_agree_with_098():
    """Tests line "20 seeds of a lopsided fixture give rate 1.0 and agree with 0.98" (Interfaces 1: `rate_a` = `wins_a / len(seeds)`, agree within the band)."""
    rate = load_rate().rate([fight(s, "A", 1000 + s) for s in range(1, 21)], 0.98)
    assert RATE_KEYS <= set(rate), "rate keys %s lack %s" % (sorted(rate), sorted(RATE_KEYS - set(rate)))
    assert rate["layout_id"] == "L-9100" and rate["seeds"] == list(range(1, 21))
    assert (rate["wins_a"], rate["wins_b"], rate["stalls"]) == (20, 0, 0)
    assert rate["rate_a"] == 1.0 and rate["predict_rate"] == 0.98 and rate["band"] == 0.10
    assert rate["agree"] is True and rate["stall_seeds"] == [] and rate["none_seeds"] == []


def test_predict_zero_disagrees_on_the_same_seeds():
    """Scoring: "the positive control becomes a fixture whose predict is the other side and disagrees" (detector control: the same twenty A-win seeds agree when A was guessed and do not when B was)."""
    mod = load_rate()
    fights = [fight(s, "A", 1000 + s) for s in range(1, 21)]
    assert mod.rate(fights, 0.98)["agree"] is True
    for f in fights:
        f["result"]["predict"] = "B"
    assert mod.rate(fights, 0.98)["agree"] is False


def test_the_band_is_ten_points_not_fifteen():
    """Scoring: the band is the number that colours the gap, not the verdict ("`agree` no longer reads them"); the key `band` stays 0.10. 16 of 20 is 0.8 with A guessed and A the majority winner:
    predicted 0.75 (5 points), 0.67 (13 points) and 0.60 (20 points) all agree."""
    mod = load_rate()
    fights = [fight(s, "A" if s <= 16 else "B", 1000) for s in range(1, 21)]
    assert mod.rate(fights, 0.75)["rate_a"] == 0.8 and mod.rate(fights, 0.75)["band"] == 0.10
    assert mod.rate(fights, 0.75)["agree"] is True
    assert mod.rate(fights, 0.60)["agree"] is True
    assert mod.rate(fights, 0.67)["agree"] is True


def test_a_stall_seed_is_counted_and_listed():
    """Tests line "a stall seed is counted and listed"; Interfaces 1: `stall_seeds` lists the seed numbers whose winner is "stall", a stall counts as no win for either
    side. (Whether a stall seed blocks `agree` is not pinned since Scoring: open question in the report.)"""
    fights = [fight(s, "stall" if s == 3 else "A", 1000) for s in range(1, 6)]
    rate = load_rate().rate(fights, 0.80)
    assert rate["stalls"] == 1 and rate["stall_seeds"] == [3]
    assert (rate["wins_a"], rate["wins_b"]) == (4, 0) and rate["rate_a"] == 0.8


def test_checker_accepts_winner_none_for_a_same_tick_wipe():
    """Audit item 2: "`result.winner` is `\"none\"`, `end` is `\"wipe\"`" for both sides wiped on the same tick. The runner writes that file through `snapshot.write`, so the checker must
    accept it (today it rejects: "result.winner is not A, B, draw or stall"). Gap for the builder: snapshot.py is not in the story's Files list."""
    assert snapshot.validate(fight(1, "none")) == []


def test_a_same_tick_wipe_is_listed_as_none_and_blocks_agree():
    """Audit item 2 / Interfaces 1: `result.winner` "none" (both sides wiped on the same tick) is listed in `none_seeds`, counts as no win, and blocks `agree`."""
    fights = [fight(s, "none" if s == 2 else "A", 1000) for s in range(1, 6)]
    rate = load_rate().rate(fights, 0.80)
    assert rate["none_seeds"] == [2] and rate["stall_seeds"] == [] and rate["stalls"] == 0
    assert rate["wins_a"] == 4 and rate["rate_a"] == 0.8 and rate["agree"] is False


def test_median_seed_is_the_median_tick_count_and_the_lower_seed_on_ties():
    """Interfaces 1: `median_seed` is "the seed whose fight has the median tick count; lower seed on ties". Ticks by seed 1..5 are 500, 100, 300, 300, 200: sorted 100, 200,
    300, 300, 500, the median is 300, held by seeds 3 and 4, so 3."""
    fights = [fight(s, "A", t) for s, t in zip(range(1, 6), (500, 100, 300, 300, 200))]
    assert load_rate().rate(fights, 0.5)["median_seed"] == 3


def test_firing_capable_counts_units_whose_range_reaches_the_first_contact_point():
    """Interfaces 5, quoted in the header. Seed 1: A has 2 units in range of unit 11's frame-1 position (Raider at 150, Bombard at 1000), B has 1 (unit 11 itself); seed 2 adds a
    Warden at 300 so A has 3. Mean over the two seeds: A 2.5, B 1.0. The later movement of unit 11 on frame 2 does not move the contact point."""
    rate = load_rate().rate([contact_fight(1), contact_fight(2, extra_in_range=1)], 0.5)
    assert rate["firing_capable"] == {"A": 2.5, "B": 1.0}


# ---------------------------------------------------------------- firing_capable at the first-shot frame (defect found at the stage 2 look review)
# DRAFT, pending Architect confirmation (brief to the test writer, 2026-11-02): Interfaces 5 as written measures frame-0 positions against the first-contact point, which reads 0
# for a side that closes in. Intended rule: count the units ALIVE AT THE FIRST-SHOT FRAME, at their positions in that frame, whose roster range reaches the first-contact point
# (the position of the first-damaged unit at the first-shot frame); per side; mean over seeds. Red ids below: test_firing_capable_counts_the_side_that_closes_in_*,
# test_firing_capable_ignores_a_unit_that_is_dead_at_the_first_shot_frame. Control: test_firing_capable_a_side_still_out_of_range_at_the_first_shot_frame_counts_zero.

def closing_fight(seed, b_end_x, dead_b_unit=False, layout_id="L-9102"):
    """A Vanguard (range 300) A unit 1 at (1000, 500), hurt on frame 1 (so the contact point is (1000, 500)); B Vanguard unit 2 starts at (1600, 500), 600 wu away on frame 0, and is at
    (`b_end_x`, 500) on frame 1. With `dead_b_unit`, B unit 3 stands 100 wu from the point on frame 0 and is dead on frame 1 (hp 0, alive false; its id is above 1, so unit 1 still
    drops first by id)."""
    def unit(i, side, x, hp=100.0, alive=True):
        return {"id": i, "side": side, "role": "Vanguard", "x": x, "y": 500.0, "layer": 0, "facing": 0.0 if side == "A" else 3.14, "hp": hp, "alive": alive, "target": None}
    f0 = [unit(1, "A", 1000.0), unit(2, "B", 1600.0)]
    f1 = [unit(1, "A", 1000.0, hp=90.0), unit(2, "B", b_end_x)]
    if dead_b_unit:
        f0.append(unit(3, "B", 1100.0))
        f1.append(unit(3, "B", 1100.0, hp=0.0, alive=False))
    frames = [{"tick": 0, "alive": [1, len(f0) - 1], "units": f0}, {"tick": 100, "alive": [1, len(f1) - 1 - dead_b_unit], "units": f1}]
    doc = fight(seed, layout_id=layout_id)
    doc["frames"] = frames
    doc["result"].update({"survivors": frames[1]["alive"], "ticks": 100})
    assert snapshot.validate(doc) == [], snapshot.validate(doc)
    return doc


def test_firing_capable_a_side_still_out_of_range_at_the_first_shot_frame_counts_zero():
    """Interfaces 5 (positive control for the fix below, green today). B closes from 600 wu only to 500 wu of the hurt unit by the first-shot frame, outside its Vanguard range 300,
    so B counts 0 under both the current and the intended rule; A's unit 1 is the hurt unit itself (distance 0) and counts 1."""
    rate = load_rate().rate([closing_fight(1, 1500.0)], 0.5)
    assert rate["firing_capable"] == {"A": 1.0, "B": 0.0}, rate["firing_capable"]


def test_firing_capable_counts_the_side_that_closes_in_by_the_first_shot_frame():
    """Interfaces 5, amended (DRAFT, Architect to confirm): "units alive at the first-shot frame, at their positions in that frame, whose roster range reaches the first-contact point".
    B is 600 wu from the point on frame 0 and 200 wu on the first-shot frame (Vanguard range 300): B counts 1. Today it reads 0 (frame-0 positions)."""
    rate = load_rate().rate([closing_fight(1, 1200.0)], 0.5)
    assert rate["firing_capable"] == {"A": 1.0, "B": 1.0}, rate["firing_capable"]


def test_firing_capable_ignores_a_unit_that_is_dead_at_the_first_shot_frame():
    """Interfaces 5, amended (DRAFT): only units alive AT THE FIRST-SHOT FRAME count. B unit 3 is 100 wu from the point on frame 0 (in range) but dead on frame 1, and B unit 2 is
    still out of range (500 wu): B counts 0. Today the dead unit is counted from frame 0 and B reads 1."""
    rate = load_rate().rate([closing_fight(1, 1500.0, dead_b_unit=True)], 0.5)
    assert rate["firing_capable"] == {"A": 1.0, "B": 0.0}, rate["firing_capable"]


# ---------------------------------------------------------------- the runner writes it

@pytest.fixture(scope="module")
def lopsided(tmp_path_factory):
    """20 seeds of a 12:8 Vanguard fixture (A bigger) with predict_rate 0.98, run once through `run.py --seeds 20`."""
    base = tmp_path_factory.mktemp("rate20")
    path = layout_toml("L-9110", 12, 8, 0.98, base / "layouts")
    out = base / "out"
    return {"out": out, "proc": run_seeds(path, out, 20)}


def test_runner_twenty_seeds_write_twenty_fights_and_a_rate_file_that_agrees(lopsided):
    """Tests line "20 seeds of a lopsided fixture give rate 1.0 and agree with 0.98", through the runner: `--seeds 20` writes twenty fight files and `L-9110.rate.json` with rate 1.0 and agree true,
    and the rate file's `seeds` match the fight files on disk."""
    proc, out = lopsided["proc"], lopsided["out"]
    assert proc.returncode == 0, proc.stderr[-1500:] + proc.stdout[-500:]
    files = sorted(out.glob("L-9110-s*.fight.json"))
    assert len(files) == 20, [p.name for p in files]
    rate = json.loads((out / "L-9110.rate.json").read_text())
    assert RATE_KEYS <= set(rate)
    assert len(rate["seeds"]) == 20 and sorted((out / ("L-9110-s%d.fight.json" % s)).name for s in rate["seeds"]) == [p.name for p in files]
    assert rate["rate_a"] == 1.0 and rate["predict_rate"] == 0.98 and rate["agree"] is True
    assert rate["stalls"] == 0 and rate["stall_seeds"] == [] and rate["none_seeds"] == []


def test_runner_rate_file_is_what_rate_py_computes_from_the_fight_files(lopsided):
    """Interfaces 1: "`run.py --seeds N` calls it and writes `<id>.rate.json` beside the fight files": the file equals `rate(fights, predict_rate)` over the fight files on disk."""
    out = lopsided["out"]
    assert lopsided["proc"].returncode == 0
    written = json.loads((out / "L-9110.rate.json").read_text())
    fights = [snapshot.read(out / ("L-9110-s%d.fight.json" % s)) for s in written["seeds"]]
    assert load_rate().rate(fights, 0.98) == written
