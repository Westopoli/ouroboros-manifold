# spec: the brief for piece LI5 (clips), 2026-11-24, no story file; interface docs/reports/2026-11-24-clip-pipeline-interface.md
"""Clip pipeline, story `clip-pipeline` (Story: clip-pipeline, Tests: clips): the functions of `scripts/skilllab/arena/clip.py` that need no Godot.

Rules proved (the brief's words, quoted; there is no S-/R- id for this piece):
- "streaming recorder (a fight longer than 10,000 ticks must fit the 3 GB cap: chunks of 500 frames)"
- "one fixed camera box for a set of fights (union of positions, so versions of one fight are comparable ...)"
- "ffmpeg H.264 yuv420p `+faststart` 20 fps width 1600, crf chosen so the file is <= a max size argument (default 9 MB), label burned top-left
  (`<version>  tick N`, real ticks)"
- "ffprobe checks (codec, pix_fmt, fps 20, width 1600, faststart, size cap, frame count equals fight frames)"
- "missing Godot or ffmpeg is an error not a silent skip"

Controls (green without the module, they show the checkers can pass AND can fail): test_control_*; the scratch recorder control was retired once record_fight matched closeup's
bytes (Test-defect commit).

The 3 GB cap proxy (a full render of 10,000+ ticks takes the better part of an hour under software GL): the streaming functions (`position_box`, `split_chunks`) run
on a 414 MB, 10,500-frame fight file in a child whose address space is limited to 1 GiB, a third of the real cap. The control shows `json.load` of the same file
dies at that limit, so a pass means the functions stream. The render's frames are bounded by the chunk size (500), tested in tests/qa/test_clip_pipeline_render.py.
"""
from __future__ import annotations

import json
import resource
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clip_pipeline_support as S  # noqa: E402
from scripts.specfactory.merge_gate_support import frame_busyness  # noqa: E402

LONG_FRAMES = 10_500          # every 2 ticks: last tick 20,998, past the brief's 10,000
LONG_UNITS = 80               # a side: 160 units a frame, a 414 MB file
PROXY_LIMIT = 1 << 30         # address space of the proxy child (a third of the 3 GB cap)


def _clip():
    from scripts.skilllab.arena import clip  # red today: the module does not exist
    return clip


def _limited(code: str, *argv: str, limit: int = PROXY_LIMIT, timeout: int = 1700) -> subprocess.CompletedProcess:
    def lim():
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    return subprocess.run([S.PY, "-c", code, *argv], cwd=str(S.ROOT), preexec_fn=lim, capture_output=True, text=True, timeout=timeout, env=S.env_clean())


@pytest.fixture(scope="module")
def long_fight(tmp_path_factory) -> Path:
    return S.write_long_fight(tmp_path_factory.mktemp("long") / "L-0001-s1-every2.fight.json", LONG_FRAMES, LONG_UNITS)


@pytest.fixture()
def fight12(tmp_path) -> tuple[Path, dict]:
    doc = S.synthetic_fight(frames=12)
    return S.write_fight(tmp_path / "f12.fight.json", doc), doc


# ================================================================ controls

def test_control_scratch_encode_passes_every_video_check_and_the_checks_can_fail(tmp_path):
    """CONTROL for the ffprobe, faststart, frame-count and label checks: the scratch ffmpeg line over 12 frames passes all of them (label read back by tesseract,
    including the odd last tick), and deliberately wrong clips (no faststart, 25 fps, width 1280, short frame count) are each reported."""
    frames = S.make_pngs(tmp_path / "png", 12)
    ticks = [n * 100 for n in range(11)] + [1107]
    good = tmp_path / "good.mp4"
    S.scratch_encode(frames, ticks, "A", good)
    assert S.video_problems(good, frames=12, max_bytes=9_000_000) == []
    assert S.frame_label(good, 0, tmp_path) == "A tick 0"
    assert S.frame_label(good, 11, tmp_path) == "A tick 1107"
    nofast = tmp_path / "nofast.mp4"
    S.scratch_encode(frames, ticks, "A", nofast, faststart=False)
    assert any("faststart" in p for p in S.video_problems(nofast))
    fps25 = tmp_path / "fps25.mp4"
    S.scratch_encode(frames, ticks, "A", fps25, fps=25)
    assert any("fps" in p for p in S.video_problems(fps25))
    narrow = tmp_path / "narrow.mp4"
    S.scratch_encode(frames, ticks, "A", narrow, width=1280)
    assert any("width" in p for p in S.video_problems(narrow))
    assert any("frames" in p for p in S.video_problems(good, frames=13))
    assert any("size" in p for p in S.video_problems(good, max_bytes=10))


def test_control_blank_statistic_can_fail_and_pass(tmp_path):
    """CONTROL for the blank-frame statistic (the gate's frame_busyness, H-040's 'none blank'): a flat black clip scores 0, a varied clip scores above 0."""
    flat, varied = tmp_path / "flat.mp4", tmp_path / "varied.mp4"
    for path, src in ((flat, "color=c=black:s=640x360:r=20:d=1"), (varied, "testsrc=s=640x360:r=20:d=1")):
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", src, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    assert frame_busyness(S.decode_frame(flat, 3, tmp_path / "flat.png")) == 0.0
    assert frame_busyness(S.decode_frame(varied, 3, tmp_path / "varied.png")) > 0.0


def test_control_json_load_of_the_long_file_dies_at_the_proxy_limit(long_fight):
    """CONTROL for the memory proxy: loading the 10,500-frame file whole in a child limited to 1 GiB fails with MemoryError, so the proxy limit is tight enough
    that only a streaming reader passes. Premise dumped: the file is over 400 MB and holds 10,500 frames."""
    assert long_fight.stat().st_size > 400 * 2**20
    r = _limited("import json,sys; d=json.load(open(sys.argv[1])); print(len(d['frames']))", str(long_fight))
    assert r.returncode != 0 and "MemoryError" in r.stderr, "json.load did not hit the limit: rc=%s out=%r err=%r" % (r.returncode, r.stdout, r.stderr[-200:])
    ok = _limited("import sys; print(open(sys.argv[1]).readline().strip())", str(long_fight))
    assert ok.returncode == 0, "the limit is too small even to start python: " + ok.stderr[-200:]


# ================================================================ pure functions

def test_label_text_is_version_two_spaces_tick():
    """Brief: "label burned top-left (`<version>  tick N`, real ticks)"."""
    clip = _clip()
    assert clip.label_text("A", 0) == "A  tick 0"
    assert clip.label_text("today", 6408) == "today  tick 6408"


def test_constants_match_the_brief():
    """Brief: "chunks of 500 frames", "20 fps width 1600", "(default 9 MB)"."""
    clip = _clip()
    assert (clip.CHUNK_FRAMES, clip.FPS, clip.WIDTH, clip.DEFAULT_MAX_MB) == (500, 20, 1600, 9)


def test_position_box_is_the_min_and_max_of_every_unit_position(fight12):
    """Brief: "one fixed camera box ... (union of positions ...)": position_box reads every unit of every frame (dead units too)."""
    clip = _clip()
    path, doc = fight12
    assert [float(v) for v in clip.position_box(path)] == [float(v) for v in S.doc_box(doc)]


def test_union_box_takes_the_outer_edges():
    """Brief: "union of positions": the union of two boxes is the smallest box holding both."""
    clip = _clip()
    assert [float(v) for v in clip.union_box([0, 10, 100, 50], [-5, 20, 80, 90])] == [-5.0, 10.0, 100.0, 90.0]
    assert [float(v) for v in clip.union_box([1, 2, 3, 4])] == [1.0, 2.0, 3.0, 4.0]


def test_split_chunks_cuts_frames_in_order_and_keeps_the_header(fight12, tmp_path):
    """Brief: "chunks of 500 frames": 12 frames in chunks of 5 give 5, 5, 2; their frames joined are the file's frames; every other key is copied unchanged."""
    clip = _clip()
    path, doc = fight12
    chunks = clip.split_chunks(path, tmp_path / "chunks", 5)
    assert [c["frames"] for c in chunks] == [5, 5, 2]
    assert [c["first_tick"] for c in chunks] == [doc["frames"][0]["tick"], doc["frames"][5]["tick"], doc["frames"][10]["tick"]]
    assert [Path(c["file"]).name for c in chunks] == ["chunk-000.fight.json", "chunk-001.fight.json", "chunk-002.fight.json"]
    joined = []
    for c in chunks:
        part = json.loads(Path(c["file"]).read_text())
        joined += part.pop("frames")
        assert part == {k: v for k, v in doc.items() if k != "frames"}
    assert joined == doc["frames"]


def test_split_chunks_one_chunk_when_the_file_is_shorter(fight12, tmp_path):
    """Brief: "chunks of 500 frames" and the default CHUNK_FRAMES: a 12-frame file is one chunk of 12 (the unchunked case the render test compares against)."""
    clip = _clip()
    path, doc = fight12
    chunks = clip.split_chunks(path, tmp_path / "chunks")
    assert [c["frames"] for c in chunks] == [12]


# ================================================================ the 3 GB cap proxy

def test_position_box_streams_a_fight_longer_than_10000_ticks(long_fight):
    """Brief: "a fight longer than 10,000 ticks must fit the 3 GB cap": position_box over the 10,500-frame (last tick 20,998) file in a 1 GiB child answers
    from the file's positions (x from 100 to 140+0.5*10499+..., y from 50)."""
    code = "import sys, json; from scripts.skilllab.arena import clip; print(json.dumps(clip.position_box(sys.argv[1])))"
    r = _limited(code, str(long_fight))
    assert r.returncode == 0, "position_box did not fit 1 GiB: " + r.stderr[-400:]
    box = json.loads(r.stdout)
    assert box[0] == 100.0 and box[1] == 50.0
    assert box[2] == pytest.approx(140.0 + 2.0 * (LONG_UNITS - 1) + 0.5 * (LONG_FRAMES - 1), abs=0.01)


def test_split_chunks_streams_a_fight_longer_than_10000_ticks(long_fight, tmp_path):
    """Brief: "a fight longer than 10,000 ticks must fit the 3 GB cap: chunks of 500 frames": split_chunks over the 10,500-frame file in a 1 GiB child writes 21
    chunks of 500 (10,500 = 21 x 500), each holding the header and its slice, and the first tick of chunk k is 1000 k."""
    code = "import sys, json; from scripts.skilllab.arena import clip; print(json.dumps([[c['frames'], c['first_tick']] for c in clip.split_chunks(sys.argv[1], sys.argv[2], 500)]))"
    r = _limited(code, str(long_fight), str(tmp_path / "chunks"))
    assert r.returncode == 0, "split_chunks did not fit 1 GiB: " + r.stderr[-400:]
    rows = json.loads(r.stdout)
    assert [n for n, _ in rows] == [500] * 21
    assert [t for _, t in rows] == [1000 * k for k in range(21)]
    last = json.loads((tmp_path / "chunks" / "chunk-020.fight.json").read_text())
    assert len(last["frames"]) == 500 and last["frames"][-1]["tick"] == 2 * (LONG_FRAMES - 1) and last["result"]["ticks"] == 2 * (LONG_FRAMES - 1)


# ================================================================ record

def test_record_fight_writes_the_bytes_closeup_writes(tmp_path):
    """Brief: "streaming recorder": the fight file from record_fight (layout L-0047, seed 1, every 100) is byte-identical to closeup's for the same arguments, and
    named <id>-s<seed>-every<K>.fight.json."""
    clip = _clip()
    from scripts.skilllab.arena import closeup
    assert closeup.main(["--layout", str(S.ROOT / S.LAYOUT_SMALL), "--seed", "1", "--every-ticks", "100", "--out", str(tmp_path / "ref")]) == 0
    got = clip.record_fight(layout=S.ROOT / S.LAYOUT_SMALL, seed=1, every=100, out_dir=tmp_path / "rec", work_dir=tmp_path / "work")
    assert Path(got).name == "L-0047-s1-every100.fight.json"
    assert Path(got).read_bytes() == (tmp_path / "ref" / "L-0047-s1-every100.fight.json").read_bytes()


def test_record_fight_in_a_named_tree_runs_that_tree(tmp_path):
    """Brief: "a layout+seed+engine tree": record_fight(tree=<this repo>) runs the sim there and gives the same bytes as the default tree; a tree that is not a
    directory is a ClipError."""
    clip = _clip()
    a = clip.record_fight(layout=S.ROOT / S.LAYOUT_SMALL, seed=1, every=100, out_dir=tmp_path / "a", work_dir=tmp_path / "wa")
    b = clip.record_fight(layout=S.ROOT / S.LAYOUT_SMALL, seed=1, every=100, out_dir=tmp_path / "b", work_dir=tmp_path / "wb", tree=S.ROOT)
    assert Path(a).read_bytes() == Path(b).read_bytes()
    with pytest.raises(clip.ClipError):
        clip.record_fight(layout=S.ROOT / S.LAYOUT_SMALL, seed=1, every=100, out_dir=tmp_path / "c", work_dir=tmp_path / "wc", tree=tmp_path / "no-such-tree")


# ================================================================ encode

def _encode(clip, tmp_path, frames, ticks, **kw):
    out = tmp_path / "enc.mp4"
    res = clip.encode_clip(frames, ticks, kw.pop("version", "A"), out, kw.pop("max_bytes", 9_000_000), work=tmp_path / "w", **kw)
    return out, res


def test_encode_clip_meets_the_format_and_burns_real_ticks(tmp_path):
    """Brief: "ffmpeg H.264 yuv420p `+faststart` 20 fps width 1600 ... label burned top-left (`<version>  tick N`, real ticks)" and "ffprobe checks (codec,
    pix_fmt, fps 20, width 1600, faststart, size cap, frame count equals fight frames)": 12 frames, last tick odd (1107), come out as 12 frames of h264 yuv420p
    20/1, width 1600, moov before mdat, under 9 MB; frame 0 reads 'A tick 0' and frame 11 'A tick 1107'; the result dict reports crf and the size on disk."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 12)
    ticks = [n * 100 for n in range(11)] + [1107]
    out, res = _encode(clip, tmp_path, frames, ticks)
    assert S.video_problems(out, frames=12, max_bytes=9_000_000) == []
    assert res["size_bytes"] == out.stat().st_size and isinstance(res["crf"], int) and "libx264" in res["command"]
    assert S.frame_label(out, 0, tmp_path) == "A tick 0"
    assert S.frame_label(out, 11, tmp_path) == "A tick 1107"


def test_encode_clip_raises_crf_until_the_file_fits_the_cap(tmp_path):
    """Brief: "crf chosen so the file is <= a max size argument": speckled frames at a roomy cap (premise: the file is over 1,000,000 bytes) and at a 1,000,000
    byte cap: the second file is at most the cap, with a higher crf than the first."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 30, noise=True)
    ticks = [2 * n for n in range(30)]
    (tmp_path / "big").mkdir()
    big, big_res = _encode(clip, tmp_path / "big", frames, ticks, max_bytes=60_000_000)
    assert big_res["size_bytes"] > 1_000_000, "premise: the roomy encode must overshoot the tight cap, got %d" % big_res["size_bytes"]
    (tmp_path / "tight").mkdir()
    small, small_res = _encode(clip, tmp_path / "tight", frames, ticks, max_bytes=1_000_000)
    assert small_res["size_bytes"] == S.probe(small)["size"] <= 1_000_000
    assert small_res["crf"] > big_res["crf"]
    assert S.video_problems(small, frames=30, max_bytes=1_000_000) == []


def test_encode_clip_names_a_cap_it_cannot_meet(tmp_path):
    """Brief: "crf chosen so the file is <= a max size argument": a 1,000 byte cap no crf can meet is SizeCapUnreachable, and no mp4 is left behind."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 6, noise=True)
    out = tmp_path / "enc.mp4"
    with pytest.raises(clip.SizeCapUnreachable):
        clip.encode_clip(frames, list(range(6)), "A", out, 1000, work=tmp_path / "w")
    assert not out.exists()


def test_encode_clip_is_deterministic(tmp_path):
    """Brief: "a deterministic re-run gives identical facts except times" (the facts carry the mp4's sha256): the same frames and labels encode to the same bytes."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 8)
    (tmp_path / "1").mkdir()
    (tmp_path / "2").mkdir()
    one, _ = _encode(clip, tmp_path / "1", frames, list(range(8)))
    two, _ = _encode(clip, tmp_path / "2", frames, list(range(8)))
    assert S.sha256(one) == S.sha256(two)


def test_encode_clip_without_ffmpeg_is_an_error(tmp_path):
    """Brief: "missing Godot or ffmpeg is an error not a silent skip": encode_clip with an ffmpeg that is not there raises ToolMissing naming it, and writes no file."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 3)
    out = tmp_path / "enc.mp4"
    with pytest.raises(clip.ToolMissing, match="ffmpeg"):
        clip.encode_clip(frames, [0, 1, 2], "A", out, 9_000_000, ffmpeg=str(tmp_path / "no-ffmpeg"), work=tmp_path / "w")
    assert not out.exists()


def test_make_poster_is_a_jpeg_of_the_first_frame_with_its_label(tmp_path):
    """Brief: "`<name>-poster.jpg`" and "label burned top-left (`<version>  tick N`)": the poster of frame 0 is a JPEG 1600 wide whose label reads 'A tick 0'
    and which is not blank."""
    clip = _clip()
    frames = S.make_pngs(tmp_path / "png", 3)
    jpg = tmp_path / "poster.jpg"
    clip.make_poster(frames[0], "A", 0, jpg)
    assert jpg.read_bytes()[:3] == b"\xff\xd8\xff"
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "csv=p=0", str(jpg)], capture_output=True, text=True, check=True)
    assert p.stdout.strip() == "1600"
    assert S.label_ocr(jpg, tmp_path) == "A tick 0"
    png = tmp_path / "poster.png"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(jpg), str(png)], check=True)
    assert frame_busyness(png) > 0.0


def test_record_fight_from_a_situation_converts_it_like_the_lab_does(tmp_path):
    """Brief: "turns a layout+seed+engine tree ... into" a clip, with the situation form the scratch recorder took (`--situation SIT-NNNN`, converted by
    situations.convert as regression._layout does). Premise dumped by running the scratch rec.py today: SIT-0101, seed 1, every 100 gives file
    L-0101-s1-every100.fight.json, winner B, wipe, last tick 586, 7 frames."""
    clip = _clip()
    got = clip.record_fight(situation="SIT-0101", seed=1, every=100, out_dir=tmp_path / "rec", work_dir=tmp_path / "work")
    assert Path(got).name == "L-0101-s1-every100.fight.json"
    doc = json.loads(Path(got).read_text())
    assert (doc["layout_id"], doc["result"]["winner"], doc["result"]["ticks"], len(doc["frames"])) == ("L-0101", "B", 586, 7)
