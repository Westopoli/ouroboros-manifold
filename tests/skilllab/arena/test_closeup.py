# spec: docs/stories/H-088.md (closeup replay: watch a fight like a video, Westley's request 2026-11-07)
# Rule pins: none (lab harness story H-088)
"""H-088 closeup, part A: `scripts/skilllab/arena/closeup.py` runs the same fight as `run.py` and keeps a frame every K ticks (no thinning to 20 frames).

Criteria (named in each docstring as CL-n; the brief's list A of 2026-11-07):
CL-1 frames at ticks 0, K, 2K, ... and the last tick, no duplicate, `snapshot_every` K.     CL-2 `result` equals the normal runner's, for every K and sight.
CL-3 `--from-tick A --to-tick B` keeps A <= tick <= B (tick 0 not forced).     CL-4 file name `<id>[-control]-s<seed>-every<K>.fight.json`.
CL-5 K < 1 is an error (non-zero exit, stderr, no file).     CL-6 frames at ticks the normal file has equal the normal file's frames.
CL-7 the existing path (`run.fight`, `run._document`, `run.main`) is byte for byte what it was.     CL-8 the module runs as `python -m` (one slow test).

Fixtures: OPEN = h088 open field, side A Raider vs side B Vanguard, both_same_point, seed 1 (premises dumped on base 633ea3e4: sight off 585 ticks, on 575, control 575, all
wipe; normal frames at 0, 100 .. 500, last). COVER = the h088 cover fixture with side A Raiders, hold:A, sight on (4490 ticks, wipe, snapshot_every 400, `built_features`,
`blocked`). Both end by themselves, so nothing here needs `--cap-seconds` (closeup is not specified to take one).
Controls (green today, must stay green): the CL-7 pins and signatures, the normal runs the closeup tests compare with."""
import contextlib
import hashlib
import importlib
import inspect
import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import h063_fixtures as fx
import h088_fixtures as f8
from scripts.skilllab.arena import run as arena_run, snapshot
from scripts.skilllab.fight import TICKS_PER_SECOND

ROOT = Path(__file__).resolve().parents[3]
OPEN_TICKS = {"off": 585, "on": 575, "control": 575}   # dumped 2026-11-07 on base 633ea3e4
OPEN_NORMAL_FRAMES = {"off": [0, 100, 200, 300, 400, 500, 585], "on": [0, 100, 200, 300, 400, 500, 575]}
# CL-7 pins: sha256 of run.main's fight file (layout_path replaced by "layout_path_pinned", as h088_fixtures.sight_off_digests) and results.md, recorded on base 633ea3e4.
PINS = {
    ("open", "off"): ("a92f75f7c27a0dff559742fffca94cfa3ed3bbe60ca32564ca8f3e901fcb2fc8", "50b2ea2453446efa5e3b91eb9045509c0ed6ce6c147fdb14dc1d6798fc80f35f"),
    ("open", "on"): ("dfe0b59b24662c5bd832fc55376090f877a3c1aba082ba3bf37a6c089871b757", "0ce389e63a247e2fb1e07de00983a92d7f17ecbe3acae572a101912ce6f33d35"),
    ("cover", "on"): ("dee5c1cb5bdd98d601dc38d003cbb107b12c6121ac3b62114adb4aa3085d3167", "481c4854124ad471f861c4b794b6fdce0545daa33a72ef4df064ccfc20ead75d"),
}


def _layout(case):
    if case == "open":
        return f8.open_layout("L-9920", roles=("Raider", "Vanguard"))
    lay = f8.cover_layout("L-9921")
    for u in lay["side_a"]["units"]:
        u["role"] = "Raider"
    return lay


def _call(main, argv):
    buf, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as e:
            code = e.code
    return SimpleNamespace(returncode=int(code or 0), stdout=buf.getvalue(), stderr=err.getvalue())


def closeup_main():
    """`scripts.skilllab.arena.closeup.main`, imported late so a missing module fails the closeup tests and not the collection (or the controls)."""
    return importlib.import_module("scripts.skilllab.arena.closeup").main


def dense_name(lid, seed, k, sight="on"):
    return "%s%s-s%d-every%s.fight.json" % (lid, "-control" if sight == "control" else "", seed, k)


class Lab:
    """Runs the normal runner and closeup for the fixtures, once per distinct call (module-scoped, so the engine runs are shared)."""

    def __init__(self, root):
        self.root, self.cache, self.n = Path(root), {}, 0

    def layout_path(self, case):
        return fx.write(_layout(case), self.root / "layouts")

    def normal(self, case, sight):
        """(fight document read raw, directory) of `run.main` for the case; sight "control" is `--sight on --control sight --control-dir` and its control file."""
        key = ("normal", case, sight)
        if key not in self.cache:
            self.n += 1
            out, cdir = self.root / ("normal%d" % self.n), self.root / ("control%d" % self.n)
            extra = ["--sight", "on", "--control", "sight", "--control-dir", str(cdir)] if sight == "control" else ["--sight", sight]
            proc = fx.run(self.layout_path(case), out, 1, *extra)
            assert proc.returncode == 0, proc.stdout + proc.stderr
            lid = _layout(case)["id"]
            f = (cdir / ("%s-control-s1.fight.json" % lid)) if sight == "control" else (out / ("%s-s1.fight.json" % lid))
            self.cache[key] = (json.loads(f.read_text()), out)
        return self.cache[key]

    def dense(self, case, sight, k, *extra, seed=1):
        """(process, document or None, output directory) of `closeup.main` for the case."""
        key = ("dense", case, sight, k, extra, seed)
        if key not in self.cache:
            self.n += 1
            out = self.root / ("dense%d" % self.n)
            proc = _call(closeup_main(), ["--layout", str(self.layout_path(case)), "--seed", str(seed), "--sight", sight, "--every-ticks", str(k), "--out", str(out),
                                          *[str(e) for e in extra]])
            f = out / dense_name(_layout(case)["id"], seed, k, sight)
            self.cache[key] = (proc, json.loads(f.read_text()) if f.exists() else None, out)
        return self.cache[key]

    def ok(self, case, sight, k, *extra, seed=1):
        proc, doc, out = self.dense(case, sight, k, *extra, seed=seed)
        assert proc.returncode == 0 and doc is not None, "closeup exit %d, file written: %s\n%s%s" % (proc.returncode, doc is not None, proc.stdout, proc.stderr)
        return doc


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    return Lab(tmp_path_factory.mktemp("closeup"))


def expected_ticks(last, k, a=None, b=None):
    ticks = sorted(set(range(0, last + 1, k)) | {last})
    return [t for t in ticks if (a is None or t >= a) and (b is None or t <= b)]


def by_tick(doc):
    return {f["tick"]: f for f in doc["frames"]}


# ---------------------------------------------------------------- controls: the existing path

def test_control_the_normal_runs_the_closeup_tests_compare_with_have_the_dumped_premises(lab):
    """CONTROL (green today, must stay green), the premises of CL-1 to CL-6: the normal runner on OPEN gives 585 / 575 / 575 ticks (sight off / on / control), all wipes, normal
    frames at 0, 100 ... and the last tick; on COVER 4490 ticks with `built_features` and per-frame `blocked`."""
    got = {s: lab.normal("open", s)[0] for s in ("off", "on", "control")}
    cover = lab.normal("cover", "on")[0]
    assert ({s: (d["result"]["ticks"], d["result"]["end"]) for s, d in got.items()},
            {s: [f["tick"] for f in d["frames"]] for s, d in got.items() if s != "control"},
            cover["result"]["ticks"], "built_features" in cover, all("blocked" in f for f in cover["frames"])) == (
        {s: (t, "wipe") for s, t in OPEN_TICKS.items()}, OPEN_NORMAL_FRAMES, 4490, True, True)


@pytest.mark.parametrize("case,sight", sorted(PINS))
def test_control_the_existing_runner_output_is_byte_identical_to_the_pinned_files(tmp_path, case, sight):
    """CONTROL (green today, must stay green), CL-7 ("tests must pin that default byte-identical"): `run.main` on the fixture writes the fight file and results.md with the
    sha256 recorded on base 633ea3e4, before closeup's optional parameter exists."""
    proc = fx.run(fx.write(_layout(case), tmp_path / "layouts"), tmp_path / "out", 1, "--sight", sight)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    f = tmp_path / "out" / ("%s-s1.fight.json" % _layout(case)["id"])
    assert (f8._pinned_sha(f), hashlib.sha256((tmp_path / "out" / "results.md").read_bytes()).hexdigest()) == PINS[(case, sight)]


@pytest.mark.parametrize("sight", ["off", "on"])
def test_control_fight_called_the_old_way_keeps_its_frames_and_document(sight):
    """CONTROL (green today, must stay green), CL-7: `run.fight(layout, seed, sight, cap)` (four positional arguments) returns frames at 0, every 100 ticks and the last tick,
    and `run._document` with its eight positional arguments gives a document with those ticks, `snapshot_every` 100, and a body `snapshot.validate` accepts."""
    lay = _layout("open")
    frames, last, end, orders = arena_run.fight(lay, 1, sight, 600)
    doc = arena_run._document(lay, Path("L-9920.toml"), 1, sight, frames, last, end, orders)
    assert (sorted(frames), last, [f["tick"] for f in doc["frames"]], doc["snapshot_every"], snapshot.validate(doc)) == (
        OPEN_NORMAL_FRAMES[sight], OPEN_TICKS[sight], OPEN_NORMAL_FRAMES[sight], 100, [])


def test_control_any_new_parameter_of_fight_and_document_is_optional():
    """CONTROL (green today, must stay green), CL-7 ("a new optional parameter ... whose default keeps today's behaviour"): every parameter of `run.fight` after
    (layout, seed, sight, cap_seconds) and of `run._document` after its eight today has a default, so every existing caller is unchanged."""
    fight_extra = list(inspect.signature(arena_run.fight).parameters.values())[4:]
    doc_extra = list(inspect.signature(arena_run._document).parameters.values())[8:]
    assert [p.name for p in fight_extra + doc_extra if p.default is inspect.Parameter.empty] == []


# ---------------------------------------------------------------- CL-1 frame ticks

@pytest.mark.parametrize("sight,k", [("on", 1), ("on", 7), ("on", 10), ("on", 5), ("off", 10), ("control", 7)])
def test_cl1_frames_are_at_0_k_2k_and_the_last_tick(lab, sight, k):
    """CL-1 ("keeps a frame every K ticks from tick 0 to the last tick of the fight (inclusive of tick 0 and the last tick), with NO thinning to 20 frames"; `snapshot_every`
    = K): the frame ticks are exactly 0, K, 2K ... and the last tick (once, even when it is a multiple of K), the last tick is the fight's (the normal runner's), the schema
    is om-fight-2 and `snapshot_every` is K."""
    doc = lab.ok("open", sight, k)
    ticks = [f["tick"] for f in doc["frames"]]
    assert (ticks, doc["result"]["ticks"], doc["snapshot_every"], doc["schema"], len(ticks) > 20) == (
        expected_ticks(OPEN_TICKS[sight], k), OPEN_TICKS[sight], k, "om-fight-2", True)


def test_cl1_k_larger_than_the_fight_gives_tick_0_and_the_last_tick(lab):
    """CL-1: with K 1000 (longer than the 575-tick fight) the frames are at ticks 0 and 575 and `snapshot_every` is 1000."""
    doc = lab.ok("open", "on", 1000)
    assert ([f["tick"] for f in doc["frames"]], doc["snapshot_every"]) == ([0, 575], 1000)


def test_cl1_cover_fight_keeps_a_frame_every_k_ticks_with_blocked_and_built_features(lab):
    """CL-1 and "same per-frame/unit keys including ... built_features": on COVER (4490 ticks, ground fight) K 50 gives 0, 50 ... 4450 and 4490, every frame carries `blocked`,
    and the document carries `built_features`, `sights`, `movement_kind`."""
    doc = lab.ok("cover", "on", 50)
    assert ([f["tick"] for f in doc["frames"]], all("blocked" in f for f in doc["frames"]), {"built_features", "sights", "movement_kind"} <= set(doc)) == (
        expected_ticks(4490, 50), True, True)


# ---------------------------------------------------------------- CL-2 result unchanged

@pytest.mark.parametrize("sight", ["off", "on", "control"])
def test_cl2_result_equals_the_normal_runners_for_every_k(lab, sight):
    """CL-2 ("the closeup fight's `result` (winner, survivors, ticks, end, stall, capped, first_seen) is identical to the normal run.py fight for the same layout/seed/sight,
    for several K"; "`result` unchanged by K"): K 1, 7 and 10 give the normal runner's result (sight control against `--sight on --control sight`); `first_seen` is in it
    exactly when sight is on (the control rule set's own fight file has none, as `_document` writes `sights` and `first_seen` only for a run with sight on)."""
    normal = lab.normal("open", sight)[0]["result"]
    got = {k: lab.ok("open", sight, k)["result"] for k in (1, 7, 10)}
    assert (got, ("first_seen" in normal) == (sight == "on")) == ({1: normal, 7: normal, 10: normal}, True)


def test_cl2_cover_result_equals_the_normal_runners(lab):
    """CL-2 on the ground-fight fixture: COVER at K 50 and K 100 gives the normal runner's result (4490 ticks, first_seen included)."""
    normal = lab.normal("cover", "on")[0]["result"]
    assert [lab.ok("cover", "on", k)["result"] for k in (50, 100)] == [normal, normal]


@pytest.mark.parametrize("sight", ["off", "on", "control"])
def test_cl2_the_document_outside_frames_and_every_equals_the_normal_files(lab, sight):
    """CL-2 / CL-6 ("the same document shape as a normal fight file ... `seen`, `sights`, `result.first_seen`, `built_features`, `orders`"): every top-level key of the closeup
    document except `snapshot_every` and `frames` equals the normal fight file's (schema, ranges, layout_id, layout_path, landscape, seed, tick_rate, sight, orders, sights,
    movement_kind, result), and the key sets agree."""
    normal = lab.normal("open", sight)[0]
    doc = lab.ok("open", sight, 10)
    rest = lambda d: {k: v for k, v in d.items() if k not in ("snapshot_every", "frames")}
    assert rest(doc) == rest(normal)


def test_cl2_two_closeup_runs_are_byte_identical(tmp_path):
    """CL-2 / "Determinism is a contract": the same layout, seed, sight and K written twice give byte-identical files (the one `layout_path` string aside, as in the CL-7 pins)."""
    runs = []
    for n in (1, 2):
        lab2 = Lab(tmp_path / ("run%d" % n))
        _, doc, out = lab2.dense("open", "on", 7)
        assert doc is not None
        raw = (out / dense_name("L-9920", 1, 7)).read_text()
        runs.append(raw.replace(json.dumps(json.loads(raw)["layout_path"]), '"layout_path_pinned"'))   # the layout sits in a different temporary directory each time
    assert runs[0] == runs[1]


# ---------------------------------------------------------------- CL-3 window

@pytest.mark.parametrize("a,b,k,want", [
    (50, 150, 10, list(range(50, 151, 10))),
    (45, 125, 10, list(range(50, 121, 10))),
    (30, 60, 7, [35, 42, 49, 56]),
    (1, 20, 7, [7, 14]),                          # tick 0 is not forced when a window is given
    (0, 20, 7, [0, 7, 14]),
    (None, 40, 7, [0, 7, 14, 21, 28, 35]),        # only --to-tick: from the start, tick 0 included
    (500, None, 10, list(range(500, 571, 10)) + [575]),   # only --from-tick: to the end, the last tick included
    (500, 9999, 10, list(range(500, 571, 10)) + [575]),
    (571, 575, 10, [575]),                        # nothing but the last tick lies in the window
])
def test_cl3_window_keeps_only_frames_between_from_and_to(lab, a, b, k, want):
    """CL-3 ("If `--from-tick`/`--to-tick` are given, only frames with A <= tick <= B are written (tick 0 is not forced then)"): the frame ticks of the OPEN sight-on fight
    (last tick 575) are the multiples of K (and the last tick) inside the window; `snapshot_every` stays K and `result` is the normal runner's."""
    extra = (["--from-tick", a] if a is not None else []) + (["--to-tick", b] if b is not None else [])
    doc = lab.ok("open", "on", k, *extra)
    assert ([f["tick"] for f in doc["frames"]], doc["snapshot_every"], doc["result"]) == (want, k, lab.normal("open", "on")[0]["result"])


def test_cl3_windowed_frames_equal_the_unwindowed_ones(lab):
    """CL-3 / CL-6: a frame in a window is the frame the full dense file has at that tick."""
    full, part = by_tick(lab.ok("open", "on", 10)), by_tick(lab.ok("open", "on", 10, "--from-tick", 100, "--to-tick", 300))
    assert (sorted(part), all(part[t] == full[t] for t in part)) == (list(range(100, 301, 10)), True)


# ---------------------------------------------------------------- CL-4 file name

@pytest.mark.parametrize("sight,seed,k", [("on", 1, 7), ("off", 3, 10), ("control", 2, 25)])
def test_cl4_one_document_named_id_control_infix_seed_every_k(lab, sight, seed, k):
    """CL-4 ("writes one document `<layout id>[-control]-s<seed>-every<K>.fight.json` ... the `-control` infix exactly when `--sight control`"): the output directory holds
    that one file and nothing else."""
    proc, doc, out = lab.dense("open", sight, k, seed=seed)
    assert (proc.returncode, sorted(p.name for p in out.iterdir()), doc is not None and doc["seed"]) == (0, [dense_name("L-9920", seed, k, sight)], seed)


# ---------------------------------------------------------------- CL-5 K < 1

@pytest.mark.parametrize("k", [0, -5])
def test_cl5_every_ticks_below_one_is_an_error_and_writes_nothing(lab, k):
    """CL-5 ("K < 1 is an error (non-zero exit, message on stderr, no file)"): `--every-ticks 0` and `-5` exit non-zero with something on stderr, and the output directory has
    no file (or does not exist)."""
    proc, _, out = lab.dense("open", "on", k)
    files = sorted(p.name for p in out.rglob("*")) if out.exists() else []
    assert (proc.returncode != 0, bool(proc.stderr.strip()), files) == (True, True, [])


# ---------------------------------------------------------------- CL-6 frames equal the normal file's

@pytest.mark.parametrize("case,sight,k", [("open", "off", 10), ("open", "on", 1), ("open", "on", 10), ("open", "control", 10), ("cover", "on", 50), ("open", "on", 7)])
def test_cl6_frames_at_ticks_the_normal_file_has_are_the_normal_frames(lab, case, sight, k):
    """CL-6 ("frames in the dense file at the ticks that the normal file also has are equal to the normal file's frames (same units, positions, target, seen)"): every frame
    of the normal file whose tick the dense file also has is equal, whole (units with `seen`, `blocked`, alive counts). For K that divides the normal spacing that is every
    normal frame; for K 7 it is at least tick 0 (and the last tick, 575 not being a multiple of 7 but kept as the last)."""
    normal, dense = by_tick(lab.normal(case, sight)[0]), by_tick(lab.ok(case, sight, k))
    common = sorted(set(normal) & set(dense))
    assert (all(normal[t] == dense[t] for t in common), set(common) >= (set(normal) if k != 7 else {0, 575}), len(common) >= 2) == (True, True, True)


# ---------------------------------------------------------------- CL-8 the module runs as a CLI

def test_cl8_python_dash_m_writes_the_dense_file(tmp_path):
    """CL-8 ("CLI `python -m scripts.skilllab.arena.closeup --layout <toml> --seed N --sight ... --every-ticks K --out DIR`"): the module run as a script (the one slow test: a
    fresh engine build) exits 0 and writes the named file with frames at 0, 100 ... and the last tick, 100 ticks apart."""
    path = fx.write(_layout("open"), tmp_path / "layouts")
    proc = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.closeup", "--layout", str(path), "--seed", "1", "--sight", "on", "--every-ticks", "100",
                           "--out", str(tmp_path / "out")], cwd=ROOT, capture_output=True, text=True, timeout=300)
    f = tmp_path / "out" / dense_name("L-9920", 1, 100)
    got = json.loads(f.read_text()) if f.exists() else None
    assert (proc.returncode, got and [fr["tick"] for fr in got["frames"]]) == (0, OPEN_NORMAL_FRAMES["on"]), proc.stderr[-600:]
