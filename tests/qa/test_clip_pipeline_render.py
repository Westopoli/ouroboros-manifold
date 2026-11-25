# spec: the brief for piece LI5 (clips), 2026-11-24, no story file; interface docs/reports/2026-11-24-clip-pipeline-interface.md
"""Clip pipeline, story `clip-pipeline` (Story: clip-pipeline, Tests: clips): the whole CLI, real Godot fight_replay scene under xvfb, real ffmpeg, in the style of
tests/qa/test_fight_replay.py (private Xvfb through xvfb-run, software GL, scratch XDG, never the real display).

Rules proved (the brief's words):
- "turns a layout+seed+engine tree (or an existing fight file) into `<name>.mp4` + `<name>-poster.jpg` + `<name>.facts.json`"
- "ffmpeg H.264 yuv420p `+faststart` 20 fps width 1600, crf chosen so the file is <= a max size argument (default 9 MB), label burned top-left (`<version>  tick N`, real ticks)"
- "ffprobe checks (codec, pix_fmt, fps 20, width 1600, faststart, size cap, frame count equals fight frames), facts schema and hashes, a deterministic re-run gives
  identical facts except times, the camera box is shared across a set (two fights of different extents produce identical camera boxes in their facts), chunked rendering
  gives the same frame count as unchunked on a short fight ... blank-frame statistic check on the output (file/pixel statistics only: no agent opens pictures)"
- facts: "(winner, survivors, last tick, end kind, frames, duration, size, sha256 of mp4 and of the fight file, record and render commands, engine sha)"

Premises dumped (synthetic fights from snapshot.example(schema=om-fight-2), 12 frames 100 ticks apart, units walking 3 wu a frame, last frame moved to the odd tick 1107;
the wide one has every coordinate times 4): fight A box [100, 50, 177.0, 54.0]-ish, fight B four times that; winner A, survivors [3, 0], result.end wipe.
Real-sim fight: L-0047 seed 1, every 100 ticks: wipe at tick 1591.

Controls (green today): test_control_* run the frozen scratch recipe (godot render, ffmpeg encode) on fight A and apply every checker to its output.
Red today: scripts/skilllab/arena/clip.py does not exist (each clip fixture fails with "No module named scripts.skilllab.arena.clip").
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "skilllab" / "integration"))
sys.path.insert(0, str(ROOT))
import clip_pipeline_support as S  # noqa: E402
from scripts.specfactory.merge_gate_support import frame_busyness  # noqa: E402

FACT_KEYS = {"name", "version", "kind", "layout_id", "seed", "snapshot_every_ticks", "winner", "survivors_A_B", "last_tick", "end_kind", "capped", "frames", "first_tick",
             "last_frame_tick", "label", "camera_box", "position_box", "video", "poster", "fight", "record_command", "render_command", "encode_command", "tree", "engine_sha",
             "chunk_frames", "times"}
VIDEO_KEYS = {"file", "codec", "pix_fmt", "fps", "width", "height", "frames", "duration_s", "size_bytes", "max_bytes", "crf", "faststart", "sha256"}
TIMES_KEYS = {"generated_at", "record_s", "render_s", "encode_s"}
FRAMES = 12
LAST_TICK = 1107   # (FRAMES - 1) * 100 + 7, the odd last tick


class Clip:
    """One CLI run: its out dir, facts, the fight document it was made from."""

    def __init__(self, out: Path, name: str, doc: dict | None, proc: subprocess.CompletedProcess, fight_path: Path | None = None):
        self.out, self.name, self.doc, self.proc, self.fight_path = out, name, doc, proc, fight_path
        self.mp4, self.poster, self.facts_path = out / (name + ".mp4"), out / (name + "-poster.jpg"), out / (name + ".facts.json")

    @property
    def facts(self) -> dict:
        return json.loads(self.facts_path.read_text())


def _run(out: Path, name: str, doc: dict | None, fight: Path | None, *extra, work: Path | None = None) -> Clip:
    args = ["--out", out, "--name", name]
    if fight is not None:
        args += ["--fight", fight]
    r = S.run_clip(args + list(extra) + (["--work", work] if work else []))
    assert r.returncode == 0, "clip run %s failed rc=%s\nstdout:\n%s\nstderr:\n%s" % (name, r.returncode, r.stdout[-600:], r.stderr[-1500:])
    return Clip(out, name, doc, r, fight)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """Fight A (narrow) and fight B (4x wider), clips a and b chunked by 5 sharing a camera, a1 (A unchunked), a again in another dir, and the sim clip."""
    root = tmp_path_factory.mktemp("clipworld")
    doc_a, doc_b = S.synthetic_fight(frames=FRAMES, spread=1.0), S.synthetic_fight(frames=FRAMES, spread=4.0)
    fa, fb = S.write_fight(root / "A.fight.json", doc_a), S.write_fight(root / "B.fight.json", doc_b)
    w = {"root": root, "doc_a": doc_a, "doc_b": doc_b, "fa": fa, "fb": fb}
    w["a"] = _run(root / "out-a", "a", doc_a, fa, "--version", "A", "--chunk", "5", "--box-with", fb, work=root / "work-a")
    w["b"] = _run(root / "out-b", "b", doc_b, fb, "--version", "B", "--chunk", "5", "--box-with", fa)
    w["a1"] = _run(root / "out-a1", "a1", doc_a, fa, "--version", "A", "--chunk", "500", "--box-with", fb)
    w["a_again"] = _run(root / "out-a2", "a", doc_a, fa, "--version", "A", "--chunk", "5", "--box-with", fb)
    return w


@pytest.fixture(scope="module")
def sim_clip(tmp_path_factory):
    """The whole path from a layout: record L-0047 in this tree, render, encode."""
    root = tmp_path_factory.mktemp("clipsim")
    c = _run(root / "out", "sim", None, None, "--layout", S.LAYOUT_SMALL, "--seed", "1", "--every", "100", "--version", "today", "--chunk", "10", work=root / "work")
    return c


# ================================================================ controls

def test_control_scratch_render_and_encode_pass_every_checker(tmp_path):
    """CONTROL for every check below: the scene renders fight A with the scratch godot call (12 frame-<i>.png, none blank by the gate's frame_busyness), the scratch
    ffmpeg line makes a clip of those frames that passes video_problems (h264, yuv420p, 20/1, width 1600, faststart, 12 frames, under 9 MB), and the label strip reads back
    'A tick 0' and 'A tick 1107' through tesseract. Premise dumped: the scene writes frame-0.png .. frame-11.png at 1920x1080."""
    fight = S.write_fight(tmp_path / "A.fight.json", S.synthetic_fight(frames=FRAMES))
    shots = tmp_path / "shots"
    assert S.scratch_render(fight, shots) == 0
    names = sorted(p.name for p in shots.glob("frame-*.png"))
    assert names == sorted("frame-%d.png" % i for i in range(FRAMES))
    for n in names:
        assert (shots / n).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and frame_busyness(shots / n) > 0.0, n
    frames = [shots / ("frame-%d.png" % i) for i in range(FRAMES)]
    ticks = [100 * n for n in range(FRAMES - 1)] + [LAST_TICK]
    mp4 = tmp_path / "ctl.mp4"
    S.scratch_encode(frames, ticks, "A", mp4)
    assert S.video_problems(mp4, frames=FRAMES, max_bytes=9_000_000) == []
    assert S.frame_label(mp4, 0, tmp_path) == "A tick 0"
    assert S.frame_label(mp4, FRAMES - 1, tmp_path) == "A tick %d" % LAST_TICK


# ================================================================ the files and ffprobe

@pytest.mark.parametrize("which", ["a", "b", "a1"])
def test_output_files_and_ffprobe_format(world, which):
    """Brief: "`<name>.mp4` + `<name>-poster.jpg` + `<name>.facts.json`" and "ffprobe checks (codec, pix_fmt, fps 20, width 1600, faststart, size cap, frame count
    equals fight frames)": the out dir holds exactly the three files, the mp4 passes video_problems with 12 frames and the 9 MB default cap, and the work dir is gone."""
    c = world[which]
    assert sorted(p.name for p in c.out.iterdir()) == sorted([c.name + ".mp4", c.name + "-poster.jpg", c.name + ".facts.json"])
    assert S.video_problems(c.mp4, frames=len(c.doc["frames"]), max_bytes=9_000_000) == []
    if which == "a":
        assert not (world["root"] / "work-a").exists() or not any((world["root"] / "work-a").iterdir()), "work dir not cleaned"


def test_chunked_and_unchunked_renders_have_the_same_frame_count(world):
    """Brief: "chunked rendering gives the same frame count as unchunked on a short fight": a (chunks of 5: 5, 5, 2) and a1 (one chunk) both have 12 frames, the same
    duration and the same camera box, and both labels run 'A tick 0' to 'A tick 1107'."""
    pa, p1 = S.probe(world["a"].mp4), S.probe(world["a1"].mp4)
    assert pa["frames"] == p1["frames"] == FRAMES
    assert pa["duration"] == pytest.approx(p1["duration"]) == pytest.approx(FRAMES / 20.0, abs=0.01)
    assert world["a"].facts["camera_box"] == world["a1"].facts["camera_box"]
    assert world["a"].facts["chunk_frames"] == 5 and world["a1"].facts["chunk_frames"] == 500


# ================================================================ label

def test_label_burns_version_and_real_ticks_across_a_chunk_edge(world, tmp_path):
    """Brief: "label burned top-left (`<version>  tick N`, real ticks)": clip a (chunks of 5, so frames 4 and 5 sit either side of an edge) reads 'A tick 0',
    'A tick 400', 'A tick 500' and, on the last frame, the odd real tick 'A tick 1107'; clip b reads 'B tick 0'."""
    mp4 = world["a"].mp4
    got = [S.frame_label(mp4, i, tmp_path) for i in (0, 4, 5, FRAMES - 1)]
    assert got == ["A tick 0", "A tick 400", "A tick 500", "A tick %d" % LAST_TICK]
    assert S.frame_label(world["b"].mp4, 0, tmp_path) == "B tick 0"


def test_poster_is_a_labelled_jpeg(world, tmp_path):
    """Brief: "`<name>-poster.jpg`": a JPEG, width 1600, label 'A tick 0' (the first frame's), and not blank by frame_busyness."""
    jpg = world["a"].poster
    assert jpg.read_bytes()[:3] == b"\xff\xd8\xff"
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "csv=p=0", str(jpg)], capture_output=True, text=True, check=True)
    assert p.stdout.strip() == "1600"
    assert S.label_ocr(jpg, tmp_path) == "A tick 0"
    png = tmp_path / "poster.png"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(jpg), str(png)], check=True)
    assert frame_busyness(png) > 0.0


# ================================================================ blank-frame statistic

def test_no_sampled_frame_is_blank_and_the_clip_changes(world, tmp_path):
    """Brief: "blank-frame statistic check on the output (file/pixel statistics only ...)": frames 0, 6 and 11 decoded from clip a each have frame_busyness above 0
    (the story's 'uniform fraction below 1'; a stricter number is Westley's, see the report), and frame 0 and frame 11 are different pictures (decoded bytes differ)."""
    pngs = [S.decode_frame(world["a"].mp4, i, tmp_path / ("f%d.png" % i)) for i in (0, 6, FRAMES - 1)]
    for p in pngs:
        assert frame_busyness(p) > 0.0, "%s is blank" % p.name
    assert pngs[0].read_bytes() != pngs[2].read_bytes()


# ================================================================ facts

@pytest.mark.parametrize("which", ["a", "b"])
def test_facts_schema_values_and_hashes(world, which):
    """Brief: "facts (winner, survivors, last tick, end kind, frames, duration, size, sha256 of mp4 and of the fight file, record and render commands, engine sha)":
    the key set is exactly the interface's, every value is what the fight file and the mp4 say, and both hashes are recomputed from the files."""
    c = world[which]
    f, doc = c.facts, c.doc
    assert set(f) == FACT_KEYS, "extra %s missing %s" % (sorted(set(f) - FACT_KEYS), sorted(FACT_KEYS - set(f)))
    assert set(f["video"]) == VIDEO_KEYS and set(f["times"]) == TIMES_KEYS
    assert (f["name"], f["version"], f["kind"], f["layout_id"], f["seed"]) == (c.name, which.upper(), "fight-file", "L-0001", 1)
    r = doc["result"]
    assert (f["winner"], f["survivors_A_B"], f["last_tick"], f["end_kind"], f["capped"]) == (r["winner"], r["survivors"], r["ticks"], r["end"], r["capped"])
    assert (f["frames"], f["first_tick"], f["last_frame_tick"], f["snapshot_every_ticks"]) == (FRAMES, 0, LAST_TICK, doc["snapshot_every"])
    assert f["label"] == {"first": "%s  tick 0" % which.upper(), "last": "%s  tick %d" % (which.upper(), LAST_TICK)}
    p = S.probe(c.mp4)
    v = f["video"]
    assert (v["file"], v["codec"], v["pix_fmt"], v["fps"], v["width"], v["height"], v["frames"]) == (c.name + ".mp4", "h264", "yuv420p", 20, 1600, p["height"], FRAMES)
    assert v["size_bytes"] == c.mp4.stat().st_size == p["size"] and v["max_bytes"] == 9_000_000 and v["size_bytes"] <= v["max_bytes"]
    assert v["duration_s"] == pytest.approx(FRAMES / 20.0, abs=0.01) and v["faststart"] is True and isinstance(v["crf"], int)
    assert v["sha256"] == S.sha256(c.mp4)
    assert f["poster"] == {"file": c.name + "-poster.jpg", "sha256": S.sha256(c.poster)}
    assert f["fight"]["sha256"] == S.sha256(c.fight_path) and f["fight"]["size_bytes"] == c.fight_path.stat().st_size
    assert f["record_command"] is None and f["tree"] is None and f["engine_sha"] is None
    assert "OM_FIT_EXTRA" in f["render_command"] and "fight_replay.tscn" in f["render_command"]
    assert all(k in f["encode_command"] for k in ("libx264", "yuv420p", "+faststart", "1600"))
    for cmd in (f["render_command"], f["encode_command"]):
        assert str(world["root"]) not in cmd, "a temp path leaked into a recorded command: " + cmd
    assert set(f["times"]) == TIMES_KEYS and all(isinstance(f["times"][k], str if k == "generated_at" else (int, float, type(None))) for k in TIMES_KEYS)


def test_deterministic_rerun_gives_identical_facts_and_bytes_except_times(world):
    """Brief: "a deterministic re-run gives identical facts except times": clip a made twice (different out dirs, the second with the default work dir) has identical
    mp4 and poster bytes and identical facts once `times` is dropped."""
    one, two = world["a"], world["a_again"]
    f1, f2 = one.facts, two.facts
    f1.pop("times"), f2.pop("times")
    assert f1 == f2
    assert S.sha256(one.mp4) == S.sha256(two.mp4) and S.sha256(one.poster) == S.sha256(two.poster)


def test_camera_box_is_shared_across_a_set_of_fights(world):
    """Brief: "the camera box is shared across a set (two fights of different extents produce identical camera boxes in their facts)": fights A and B, run with
    --box-with each other, have different position boxes (B is 4x wider; position_box equals the fight's own units) and one identical camera_box, the union."""
    fa, fb = world["a"].facts, world["b"].facts
    assert fa["position_box"] == [float(v) for v in S.doc_box(world["doc_a"])]
    assert fb["position_box"] == [float(v) for v in S.doc_box(world["doc_b"])]
    assert fa["position_box"] != fb["position_box"]
    assert fa["camera_box"] == fb["camera_box"]
    ba, bb = S.doc_box(world["doc_a"]), S.doc_box(world["doc_b"])
    assert fa["camera_box"] == [min(ba[0], bb[0]), min(ba[1], bb[1]), max(ba[2], bb[2]), max(ba[3], bb[3])]


# ================================================================ size cap

def test_a_tighter_max_size_raises_the_crf(world, tmp_path):
    """Brief: "crf chosen so the file is <= a max size argument (default 9 MB)": the same fight run with --max-mb at 60% of the default run's size gives a file at
    most that cap, a higher crf, and facts that name the cap."""
    base = world["a"].facts["video"]
    cap = int(base["size_bytes"] * 0.6)
    c = _run(tmp_path / "out", "tight", world["doc_a"], world["fa"], "--version", "A", "--chunk", "5", "--box-with", world["fb"], "--max-mb", "%.6f" % (cap / 1e6))
    v = c.facts["video"]
    assert v["max_bytes"] == cap and v["size_bytes"] == c.mp4.stat().st_size <= cap and v["crf"] > base["crf"]
    assert S.video_problems(c.mp4, frames=FRAMES, max_bytes=cap) == []


# ================================================================ from a layout, through the sim

def test_a_layout_clip_records_renders_and_reports_the_sim(sim_clip, tmp_path):
    """Brief: "turns a layout+seed+engine tree ... into" the three files, facts with "record and render commands, engine sha": L-0047, seed 1, every 100 ticks gives a
    clip whose frames equal the fight's, whose last label is the sim's real last tick, whose fight sha is closeup's file's, whose engine_sha is this tree's HEAD and whose
    recorded record command names the layout, and no work-dir path appears in any recorded command."""
    from scripts.skilllab.arena import closeup
    assert closeup.main(["--layout", str(S.ROOT / S.LAYOUT_SMALL), "--seed", "1", "--every-ticks", "100", "--out", str(tmp_path / "ref")]) == 0
    ref = tmp_path / "ref" / "L-0047-s1-every100.fight.json"
    doc = json.loads(ref.read_text())
    f = sim_clip.facts
    head = subprocess.run(["git", "-C", str(S.ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    assert set(f) == FACT_KEYS
    assert (f["kind"], f["layout_id"], f["seed"], f["snapshot_every_ticks"], f["version"]) == ("layout", "L-0047", 1, 100, "today")
    assert (f["winner"], f["survivors_A_B"], f["last_tick"], f["end_kind"]) == (doc["result"]["winner"], doc["result"]["survivors"], doc["result"]["ticks"], doc["result"]["end"])
    assert f["frames"] == len(doc["frames"]) == f["video"]["frames"] and f["last_frame_tick"] == doc["frames"][-1]["tick"]
    assert f["fight"]["sha256"] == S.sha256(ref) and f["engine_sha"] == head and f["tree"] == str(S.ROOT)
    assert "L-0047.toml" in f["record_command"] and "--seed" in f["record_command"]
    for cmd in (f["record_command"], f["render_command"], f["encode_command"]):
        assert str(sim_clip.out.parent) not in cmd, "a temp path leaked into: " + cmd
    assert S.video_problems(sim_clip.mp4, frames=f["frames"], max_bytes=9_000_000) == []
    assert S.frame_label(sim_clip.mp4, f["frames"] - 1, tmp_path) == "today tick %d" % doc["frames"][-1]["tick"]
    assert sorted(p.name for p in sim_clip.out.iterdir()) == ["sim-poster.jpg", "sim.facts.json", "sim.mp4"]
