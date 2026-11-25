# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arms F and W), section 5 (the comparison row), section 7 (LI4)
"""Helpers shared by test_isolation_fw_*.py (piece LI4-FW; interface: docs/reports/2026-11-24-li4fw-interface.md). The module under test is imported lazily so a missing module
fails each test (red), not the collection.

Premises dumped 2026-11-24 by running the real labs (scratch: engine-rules-baseline/li4/), `then` = 4fa618ce7 with its own lab, `now` = origin/main 893a5af7f with its own lab,
seeds 10 and 1 (they give the same fight, the walker survey `engine-rules-baseline/walkers/all_rows.csv` and these runs agree on every cell below except the one marked SURVEY):
  stage 3 layouts at seed 10 (winner survivors last_tick end):  then L-0055 A 21:0 3394 wipe, L-0073 A 17:0 6175 wipe, L-0084 B 0:6 2268 wipe, L-0039 draw 8:8 12000 cap
                                                                 now  L-0055 A 19:0 1963, L-0073 A 19:0 2516, L-0084 A 18:0 2097, L-0039 A 2:0 3081 (all wipe)
  control twins (`run --control-dir`, file `<id>-control-s<seed>.fight.json`):  then A 23:0 2196 / A 22:0 2156 / SURVEY: stall 40:56 820 silence (the survey says B 0:36 1159: the then lab has no
                                                                 L6 layer fix, so the slope twin's side A stands on a layer the flat ground does not give) / A 3:0 2606
                                                                 now  A 19:0 2188 / A 13:0 4395 / B 0:27 1361 / B 0:5 2352
  the rule checker (F0, `invalid` and `violations` in the fight file): the lab at `then` writes neither; at `now`, the layout run is INVALID R-097-05 for L-0055 and L-0084 and valid for
  L-0073 and L-0039; the twin is INVALID R-097-05 for L-0073 only. The lab exits 2 on an invalid fight and still writes the file, and the LI1 runner turns that exit into an error row of stage
  `layout` (found by this piece: L-0055 and L-0084 at `now` are error rows through `isolation_runner.run_one` today). The tests below say a fight the checker marks invalid is a row with its rule listed.
  A neutral-role copy (every unit Vanguard, range 300) of each layout passes check_layout and runs at both versions (probe)."""
import importlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import isolation_fixtures as fx

ROOT = fx.ROOT
NOW_SHA = "893a5af7fc54de5bb238a5fabb528e2ddf70ed91"      # origin/main when the facts below were dumped
LD = ROOT / "docs/northstar/research/layer_dynamics"
STAGE3 = ("L-0055", "L-0073", "L-0084", "L-0039")
KIND = {"L-0055": "chokepoint", "L-0073": "city", "L-0084": "slope", "L-0039": "cover"}
EXPECTED = {"L-0055": ("A", 0.98), "L-0073": ("A", 0.75), "L-0084": ("A", 0.6), "L-0039": ("B", 0.25)}     # arena/approved.toml stage 3 rows
STAGE_WORDS, STAGE_DATE = "I rule approval on stage 3, we are go to move to stage 4", "2026-11-05"
WORDS = {"L-0055": "Blue is expected to win 98% of the time.", "L-0073": "blue expected to win 75% of the time", "L-0084": "blue expected to win 60% of the time",
         "L-0039": ("cover: rejected, this position is technically worse for blue because they have less space to spread out units to get firing angles on red. Without being changed red is "
                    "expected to win 75% of the time depending on where units stop (how much range both units have, I can't tell unless I see a fight)")}
NO_PICTURE = "no per-picture verdict"
FW_KEYS = fx.ROW_KEYS | {"variant", "invalid", "measures"}
# (winner as isolation_measures.result_of says it, survivors, last_tick, end): layout then/now, control then/now
FACTS = {
    "L-0055": {"layout": {"then": ("A", [21, 0], 3394, "wipe"), "now": ("A", [19, 0], 1963, "wipe")},
               "control": {"then": ("A", [23, 0], 2196, "wipe"), "now": ("A", [19, 0], 2188, "wipe")},
               "invalid_now": {"layout": ["R-097-05"], "control": []}, "verdict": ("same", 0), "matches": {"then": True, "now": True}},
    "L-0073": {"layout": {"then": ("A", [17, 0], 6175, "wipe"), "now": ("A", [19, 0], 2516, "wipe")},
               "control": {"then": ("A", [22, 0], 2156, "wipe"), "now": ("A", [13, 0], 4395, "wipe")},
               "invalid_now": {"layout": [], "control": ["R-097-05"]}, "verdict": ("same", 0), "matches": {"then": True, "now": True}},
    "L-0084": {"layout": {"then": ("B", [0, 6], 2268, "wipe"), "now": ("A", [18, 0], 2097, "wipe")},
               "control": {"then": ("draw", [40, 56], 820, "silence"), "now": ("B", [0, 27], 1361, "wipe")},     # then control: a stall, a defect cell (lab says stall, the measure says draw)
               "invalid_now": {"layout": ["R-097-05"], "control": []}, "verdict": ("changed", 2), "matches": {"then": False, "now": True}},
    "L-0039": {"layout": {"then": ("cap", [8, 8], 12000, "cap"), "now": ("A", [2, 0], 3081, "wipe")},
               "control": {"then": ("A", [3, 0], 2606, "wipe"), "now": ("B", [0, 5], 2352, "wipe")},
               "invalid_now": {"layout": [], "control": []}, "verdict": ("changed", 2), "matches": {"then": "n/a", "now": False}},
}
RATE = {"L-0055": {"then": (1.0, 2.0), "now": (1.0, 2.0)}, "L-0073": {"then": (1.0, 25.0), "now": (1.0, 25.0)},
        "L-0084": {"then": (0.0, 60.0), "now": (1.0, 40.0)}, "L-0039": {"then": (0.0, 25.0), "now": (1.0, 75.0)}}      # (measured rate of side A over the two seeds, gap in points to predict_rate)
_memo = {}


def fw():
    return importlib.import_module("scripts.skilllab.arena.isolation_fw")


def im():
    return importlib.import_module("scripts.skilllab.arena.isolation_measures")


def doc_of(row):
    return json.loads(Path(row["fight_path"]).read_text())


def pick(rows, version, arm, variant, seed=10):
    (row,) = [r for r in rows if (r["version"], r["arm"], r["variant"], r["seed"]) == (version, arm, variant, seed)]
    return row


def runs(scratch, layout):
    """SimpleNamespace(w, f): rows of arm W (seeds 10 and 1, then and now, layout and twin: 8 fights) and arm F (seed 10: 4 fights) of one stage 3 layout, one `run_arms` call each, memoised per scratch.
    About 3 to 4 minutes (probe: 15 s a fight, the 12000-tick cap fight longer)."""
    key = (str(scratch), layout)
    if key not in _memo:
        mod = fw()
        w = mod.run_arms(["then", "now"], scratch, Path(scratch) / ("w-%s" % layout) / "rows.jsonl", arms=("W",), layouts=(layout,), seeds=(10, 1), repo=ROOT,
                         out_dir=Path(scratch) / ("w-fights-%s" % layout))
        f = mod.run_arms(["then", "now"], scratch, Path(scratch) / ("f-%s" % layout) / "rows.jsonl", arms=("F",), layouts=(layout,), seeds=(10,), repo=ROOT,
                         out_dir=Path(scratch) / ("f-fights-%s" % layout))
        _memo[key] = SimpleNamespace(w=w, f=f)
    return _memo[key]


def comparison(scratch, layout):
    key = ("cmp", str(scratch), layout)
    if key not in _memo:
        r = runs(scratch, layout)
        (_memo[key],) = fw().comparison_rows(r.w + r.f, repo=ROOT)
    return _memo[key]


def lab_job(args, cwd, timeout=1800):
    """A lab command under the memory cap, as every build and fight of this work is run."""
    cmd = ["timeout", str(timeout), "systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3G", "-p", "MemorySwapMax=0", "--", "nice", "-n", "10", *args]
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
