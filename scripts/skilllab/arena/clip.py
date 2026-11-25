"""The clip pipeline (story `clip-pipeline`; interface docs/reports/2026-11-24-clip-pipeline-interface.md): one command from a layout (or a fight file) to
`<name>.mp4` + `<name>-poster.jpg` + `<name>.facts.json`.

CLI: python -m scripts.skilllab.arena.clip --out DIR --name NAME [--version LABEL] (--layout L.toml | --situation SIT-NNNN | --fight F.fight.json)
     [--seed N --every K] [--tree DIR] [--box x0,y0,x1,y1] [--box-with FIGHT]... [--max-mb 9] [--chunk 500] [--work DIR] [--keep-work]
     [--godot PATH] [--ffmpeg PATH] [--ffprobe PATH]
Steps: record the fight (clip_record.py, in the engine tree named), cut it into chunks of 500 frames, render each chunk with the fight_replay scene under xvfb (one camera
for every chunk and every clip of a set: OM_FIT_EXTRA), encode H.264 yuv420p +faststart 20 fps width 1600 with the real tick burned top-left, the least crf that fits the
size cap, a poster, the facts. Every reader of a fight file streams it, so peak memory does not grow with the file.
Exit codes: 0 ok; 2 bad arguments, bad fight file or a layout the lab rejects (REJECT lines on stdout); 3 a tool is missing; 4 godot, ffmpeg or the recorder failed;
5 no crf meets the size cap. A failed run leaves none of the three files. Wrapped in the caller's memory cap, as every capped job here is.
See also: tests/skilllab/integration/test_clip_pipeline_*.py, tests/qa/test_clip_pipeline_render.py."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CHUNK_FRAMES = 500
WIDTH = 1600
FPS = 20
DEFAULT_MAX_MB = 9
DEFAULT_GODOT = "~/.local/bin/godot.real"
SCENE = "res://scenes/proto/fight_replay/fight_replay.tscn"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
START_CRF = 23  # the scratch recipe's crf; at 20 tesseract misreads frame 0 of the test clips
WORST_CRF = 51
RENDER_TIMEOUT = 3600  # seconds one chunk may take (500 frames under software GL)
LABEL_PAD = " " * 30  # the black box behind the label is as wide as the longest label
RECORDER = Path(__file__).resolve().with_name("clip_record.py")
_DECODER = json.JSONDecoder()
_VERSION_OK = re.compile(r"[\w .+()/-]+")


class ClipError(Exception):
    """A tool or the recorder failed (exit 4)."""


class BadInput(ClipError):
    """An argument, a fight file or a layout that cannot make a clip (exit 2)."""


class Rejected(BadInput):
    """A layout the lab rejects; `lines` are the REJECT lines closeup would print."""

    def __init__(self, lines):
        super().__init__("\n".join(lines))
        self.lines = lines


class ToolMissing(ClipError):
    """godot, ffmpeg, ffprobe or xvfb-run is not there (exit 3)."""


class SizeCapUnreachable(ClipError):
    """crf 51 is still over the size cap (exit 5)."""


# ---------------------------------------------------------------- reading a fight file as a stream

class _Stream:
    """A text file read in blocks; `value()` decodes one JSON value at the cursor, so a frame at a time is in memory."""

    def __init__(self, f):
        self.f, self.buf, self.pos, self.eof = f, "", 0, False

    def _more(self):
        chunk = self.f.read(1 << 22)
        if not chunk:
            self.eof = True
            return
        self.buf = self.buf[self.pos:] + chunk
        self.pos = 0

    def peek(self) -> str:
        while True:
            while self.pos < len(self.buf) and self.buf[self.pos] in " \t\r\n":
                self.pos += 1
            if self.pos < len(self.buf):
                return self.buf[self.pos]
            if self.eof:
                return ""
            self._more()

    def take(self, ch: str) -> None:
        if self.peek() != ch:
            raise ValueError("expected %r, found %r" % (ch, self.peek()))
        self.pos += 1

    def value(self):
        self.peek()
        while True:
            try:
                v, end = _DECODER.raw_decode(self.buf, self.pos)
                if end < len(self.buf) or self.eof:  # a number touching the block's end may be cut short
                    self.pos = end
                    return v
            except json.JSONDecodeError:
                if self.eof:
                    raise
            self._more()


def _walk(path):
    """Yield ("key", name, value) for every top-level key but `frames`, and ("frame", frame) for each frame in order."""
    with open(path, encoding="utf-8") as f:
        s = _Stream(f)
        s.take("{")
        if s.peek() != "}":
            while True:
                key = s.value()
                s.take(":")
                if key == "frames":
                    s.take("[")
                    if s.peek() != "]":
                        while True:
                            yield "frame", s.value()
                            if s.peek() != ",":
                                break
                            s.pos += 1
                    s.take("]")
                else:
                    yield "key", key, s.value()
                if s.peek() != ",":
                    break
                s.pos += 1
        s.take("}")


def _scan(path) -> dict:
    """One pass over a fight file: `header` (every key but frames), the position box, `ticks` (one per frame). BadInput when it is unreadable or has no frame."""
    header, ticks = {}, []
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    try:
        for item in _walk(path):
            if item[0] == "key":
                header[item[1]] = item[2]
                continue
            ticks.append(int(item[1]["tick"]))
            for u in item[1]["units"]:
                x, y = float(u["x"]), float(u["y"])
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise BadInput("%s: not a readable fight file (%s: %s)" % (path, type(e).__name__, e))
    if not ticks or x0 == float("inf"):
        raise BadInput("%s: the fight file holds no frame with a unit" % path)
    return {"header": header, "box": [x0, y0, x1, y1], "ticks": ticks}


def position_box(fight_path) -> list:
    """[x0, y0, x1, y1]: the min and max of every unit position in every frame (dead units too)."""
    return _scan(fight_path)["box"]


def union_box(*boxes) -> list:
    return [min(float(b[0]) for b in boxes), min(float(b[1]) for b in boxes), max(float(b[2]) for b in boxes), max(float(b[3]) for b in boxes)]


def split_chunks(fight_path, chunk_dir, frames_per_chunk=CHUNK_FRAMES) -> list:
    """Cut the fight into chunk-NNN.fight.json files of `frames_per_chunk` frames (each the whole document but for its slice of frames);
    [{"file", "first_tick", "frames"}] in order."""
    header = _scan(fight_path)["header"]
    chunk_dir = Path(chunk_dir)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    chunks, cur = [], []

    def flush():
        path = chunk_dir / ("chunk-%03d.fight.json" % len(chunks))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(header, frames=cur), f, sort_keys=True, indent=2)
            f.write("\n")
        chunks.append({"file": path, "first_tick": int(cur[0]["tick"]), "frames": len(cur)})

    for item in _walk(fight_path):
        if item[0] == "frame":
            cur.append(item[1])
            if len(cur) == frames_per_chunk:
                flush()
                cur = []
    if cur:
        flush()
    return chunks


def label_text(version, tick) -> str:
    return "%s  tick %s" % (version, tick)


# ---------------------------------------------------------------- tools

def _need(tool, label: str) -> str:
    """The tool's path, or ToolMissing naming it."""
    p = os.path.expanduser(str(tool))
    found = p if os.sep in p and os.path.isfile(p) and os.access(p, os.X_OK) else shutil.which(p) if os.sep not in p else None
    if not found:
        raise ToolMissing("%s not found: %s" % (label, tool))
    return found


def _run(cmd, what: str, **kw) -> subprocess.CompletedProcess:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    except subprocess.TimeoutExpired:
        raise ClipError("%s timed out" % what)
    if r.returncode != 0:
        raise ClipError("%s failed (exit %d): %s" % (what, r.returncode, (r.stderr or r.stdout)[-600:]))
    return r


# ---------------------------------------------------------------- record

def _record_argv(layout, situation, seed, every, out_dir, work_dir) -> list:
    argv = [sys.executable, "-P", str(RECORDER)]
    argv += ["--layout", str(layout)] if layout else ["--situation", situation, "--work", str(work_dir)]
    return argv + ["--seed", str(seed), "--every", str(every), "--out", str(out_dir)]


def record_fight(*, layout=None, situation=None, seed, every, out_dir, tree=None, work_dir=None) -> Path:
    """Run the fight of `layout` (a TOML) or `situation` ("SIT-NNNN", converted into `work_dir`) in the engine tree `tree` (default: this repo) and write
    `<id>-s<seed>-every<K>.fight.json`, the bytes closeup writes, into `out_dir`. A layout the lab rejects is Rejected."""
    tree = Path(tree) if tree else REPO
    if not tree.is_dir():
        raise BadInput("engine tree %s is not a directory" % tree)
    if layout is not None:
        layout = Path(layout).resolve()
    if situation is not None and work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="clip-sit-"))
    env = dict(os.environ, PYTHONPATH=str(tree))
    r = subprocess.run(_record_argv(layout, situation, seed, every, out_dir, work_dir), cwd=str(tree), env=env, capture_output=True, text=True)
    rejects = [ln for ln in r.stdout.splitlines() if ln.startswith("REJECT")]
    if r.returncode == 2 and rejects:
        raise Rejected(rejects)
    if r.returncode != 0:
        raise ClipError("the recorder failed (exit %d) in %s: %s" % (r.returncode, tree, r.stderr[-600:]))
    return Path(out_dir) / r.stdout.split("WROTE ")[-1].strip()


# ---------------------------------------------------------------- encode

def _check_version(version: str) -> None:
    if not _VERSION_OK.fullmatch(version):
        raise BadInput("label %r: only letters, digits, space and . + ( ) / - are burned" % version)


def _drawtext(text: str, enable: str) -> str:
    return "drawtext=fontfile=%s:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.9:boxborderw=6:x=20:y=8:%stext='%s%s'" % (FONT, enable, text, LABEL_PAD)


def _label_filters(version: str, ticks) -> str:
    """drawtext filters that burn `label_text(version, ticks[i])` on frame i; a run of ticks at one step is one filter counting with the frame number."""
    out, i, n = [], 0, len(ticks)
    while i < n:
        j, step = i, 0
        if i + 1 < n:
            step, j = ticks[i + 1] - ticks[i], i + 1
            while j + 1 < n and ticks[j + 1] - ticks[j] == step:
                j += 1
        if j == i:
            out.append(_drawtext(label_text(version, ticks[i]), "enable='eq(n,%d)':" % i))
        else:
            out.append(_drawtext("%s  tick %%{eif\\:%d+%d*(n-%d)\\:d}" % (version, ticks[i], step, i), "enable='between(n,%d,%d)':" % (i, j)))
        i = j + 1
    return ",".join(out)


def encode_clip(frames, ticks, version, out_mp4, max_bytes, ffmpeg="ffmpeg", work=None) -> dict:
    """Encode PNG `frames` (ticks[i] the real tick of frame i) to `out_mp4`: H.264 yuv420p +faststart, 20 fps, width 1600, label burned top-left, the least crf
    from START_CRF up whose file is <= max_bytes. {"crf", "size_bytes", "command"}; SizeCapUnreachable (no file left) when crf 51 is still over."""
    ffmpeg = _need(ffmpeg, "ffmpeg")
    _check_version(version)
    if len(frames) != len(ticks):
        raise BadInput("%d frames but %d ticks" % (len(frames), len(ticks)))
    out_mp4 = Path(out_mp4)
    work = Path(work) if work else Path(tempfile.mkdtemp(prefix="clip-enc-"))
    seq = work / "seq"
    seq.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(frames):
        link = seq / ("f%05d.png" % i)
        if not link.is_symlink():
            os.symlink(os.path.abspath(p), link)
    vf = "scale=%d:-2:flags=lanczos,format=yuv420p,%s" % (WIDTH, _label_filters(version, ticks))

    def argv(crf: int, dest: Path) -> list:
        return [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(FPS), "-i", str(seq / "f%05d.png"), "-vf", vf, "-c:v", "libx264", "-preset", "medium",
                "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-r", str(FPS), str(dest)]

    tried = {}

    def size_at(crf: int) -> int:
        if crf not in tried:
            dest = work / ("try-crf%d.mp4" % crf)
            _run(argv(crf, dest), "ffmpeg")
            tried[crf] = dest.stat().st_size
        return tried[crf]

    try:
        best = START_CRF
        if size_at(START_CRF) > max_bytes:
            if size_at(WORST_CRF) > max_bytes:
                raise SizeCapUnreachable("no crf up to %d brings the clip under %d bytes (crf %d gives %d)" % (WORST_CRF, max_bytes, WORST_CRF, tried[WORST_CRF]))
            lo, best = START_CRF, WORST_CRF   # lo is over the cap, best is under it
            while best - lo > 1:
                mid = (lo + best) // 2
                lo, best = (lo, mid) if size_at(mid) <= max_bytes else (mid, best)
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(work / ("try-crf%d.mp4" % best)), str(out_mp4))
    finally:
        for crf in tried:
            (work / ("try-crf%d.mp4" % crf)).unlink(missing_ok=True)
    return {"crf": best, "size_bytes": out_mp4.stat().st_size, "command": shlex.join(argv(best, out_mp4))}


def make_poster(frame, version, tick, out_jpg, ffmpeg="ffmpeg") -> None:
    """The first frame as a JPEG, width 1600, with the clip's label."""
    ffmpeg = _need(ffmpeg, "ffmpeg")
    _check_version(version)
    vf = "scale=%d:-2:flags=lanczos,%s" % (WIDTH, _drawtext(label_text(version, tick), ""))
    Path(out_jpg).parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(frame), "-frames:v", "1", "-vf", vf, "-q:v", "2", str(out_jpg)], "ffmpeg (poster)")


# ---------------------------------------------------------------- render

def _render_chunk(xvfb: str, godot: str, chunk: Path, shots: Path, box: str, xdg: Path, frames: int) -> list:
    """Render one chunk file with the fight_replay scene; its frame PNGs in order."""
    shots.mkdir(parents=True)
    env = dict(os.environ, OM_FIGHT=str(chunk), OM_SHOT_OUT=str(shots), OM_FIT_EXTRA=box, LIBGL_ALWAYS_SOFTWARE="1", GALLIUM_DRIVER="llvmpipe", LC_ALL="C")
    for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
        env.pop(var, None)
    env.setdefault("XDG_DATA_HOME", str(xdg))
    cmd = _render_argv(xvfb, godot)
    with open(shots / "log.txt", "w") as log:
        try:
            rc = subprocess.run(cmd, cwd=str(shots), env=env, stdout=log, stderr=subprocess.STDOUT, timeout=RENDER_TIMEOUT).returncode
        except subprocess.TimeoutExpired:
            raise ClipError("godot timed out rendering %s" % chunk.name)
    pngs = [shots / ("frame-%d.png" % i) for i in range(frames)]
    if rc != 0 or not all(p.is_file() and p.stat().st_size > 0 for p in pngs):
        raise ClipError("godot failed rendering %s (exit %d, log %s)" % (chunk.name, rc, shots / "log.txt"))
    return pngs


def _render_argv(xvfb: str, godot: str) -> list:
    return [xvfb, "-a", "-s", "-screen 0 1920x1080x24", godot, "--path", str(REPO), "--display-driver", "x11", "--rendering-driver", "opengl3", "-w", "--position", "0,0",
            "--resolution", "1920x1080", "--fixed-fps", "30", SCENE]


# ---------------------------------------------------------------- the clip

def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _faststart(mp4: Path) -> bool:
    """True when the moov box comes before the mdat box."""
    seen, size_total = [], mp4.stat().st_size
    with open(mp4, "rb") as f:
        pos = 0
        while pos < size_total:
            f.seek(pos)
            head = f.read(8)
            if len(head) < 8:
                break
            size, typ = struct.unpack(">I4s", head)
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
            elif size == 0:
                size = size_total - pos
            seen.append(typ.decode("latin1"))
            if size < 8:
                break
            pos += size
    return "moov" in seen and "mdat" in seen and seen.index("moov") < seen.index("mdat")


def _probe(ffprobe: str, mp4: Path) -> dict:
    out = _run([ffprobe, "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                "stream=codec_name,pix_fmt,r_frame_rate,width,height,nb_read_packets:format=duration", "-of", "json", str(mp4)], "ffprobe").stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = (int(v) for v in s["r_frame_rate"].split("/"))
    return {"codec": s["codec_name"], "pix_fmt": s["pix_fmt"], "fps": num // den if num % den == 0 else num / den, "width": s["width"], "height": s["height"],
            "frames": int(s["nb_read_packets"]), "duration_s": round(float(j["format"]["duration"]), 3)}


def _git_head(tree: Path) -> str:
    return _run(["git", "-C", str(tree), "rev-parse", "HEAD"], "git rev-parse").stdout.strip()


def _box_arg(text: str) -> list:
    parts = text.split(",")
    try:
        if len(parts) != 4:
            raise ValueError
        return [float(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError("%r is not x0,y0,x1,y1" % text)


def _positive(kind):
    def parse(text):
        v = kind(text)
        if v <= 0:
            raise argparse.ArgumentTypeError("%s is not above 0" % text)
        return v
    return parse


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m scripts.skilllab.arena.clip", description="A layout or a fight file to an mp4, a poster and a facts file.")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--name", required=True)
    ap.add_argument("--version", help="the label before `tick N` (default: the name)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--layout", type=Path)
    src.add_argument("--situation")
    src.add_argument("--fight", type=Path)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--every", type=_positive(int), help="a frame every K ticks")
    ap.add_argument("--tree", type=Path, help="engine tree for --layout / --situation (default: this repo)")
    ap.add_argument("--box", type=_box_arg, help="extra camera extent x0,y0,x1,y1")
    ap.add_argument("--box-with", type=Path, action="append", default=[], help="a fight whose positions the camera also holds (repeatable)")
    ap.add_argument("--max-mb", type=_positive(float), default=DEFAULT_MAX_MB)
    ap.add_argument("--chunk", type=_positive(int), default=CHUNK_FRAMES)
    ap.add_argument("--work", type=Path)
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--godot", default=DEFAULT_GODOT)
    ap.add_argument("--ffmpeg", default="ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe")
    return ap


def _make(a) -> None:
    tools = {"godot": _need(a.godot, "godot"), "ffmpeg": _need(a.ffmpeg, "ffmpeg"), "ffprobe": _need(a.ffprobe, "ffprobe"), "xvfb-run": _need("xvfb-run", "xvfb-run")}
    _check_version(a.version or a.name)
    version = a.version or a.name
    work = Path(os.path.abspath(a.work)) if a.work else Path(tempfile.mkdtemp(prefix="clip-"))
    if work.exists() and any(work.iterdir()):
        raise BadInput("--work %s is not empty" % work)
    work.mkdir(parents=True, exist_ok=True)
    out_dir = Path(os.path.abspath(a.out))
    try:
        times = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "record_s": None}
        tree = sha = record_cmd = None
        if a.fight:
            fight, kind = a.fight, "fight-file"
            fight_file = str(a.fight)
        else:
            tree = Path(os.path.abspath(a.tree)) if a.tree else REPO
            if a.layout and not a.layout.is_file():
                raise BadInput("layout %s is not a file" % a.layout)
            t0 = time.monotonic()
            fight = record_fight(layout=a.layout, situation=a.situation, seed=a.seed, every=a.every, out_dir=work / "fight", tree=tree, work_dir=work / "sit")
            times["record_s"] = round(time.monotonic() - t0, 1)
            kind, fight_file = ("layout" if a.layout else "situation"), fight.name
            sha = _git_head(tree)
            record_cmd = shlex.join(["python", *_record_argv(a.layout and a.layout.resolve(), a.situation, a.seed, a.every, work / "fight", work / "sit")[1:]])
        scan = _scan(fight)
        pos_box = scan["box"]
        camera = union_box(pos_box, *([a.box] if a.box else []), *(position_box(p) for p in a.box_with))
        box_str = ",".join(repr(v) for v in camera)

        t0 = time.monotonic()
        chunks = split_chunks(fight, work / "chunks", a.chunk)
        pngs = []
        for k, c in enumerate(chunks):
            pngs += _render_chunk(tools["xvfb-run"], tools["godot"], c["file"], work / "shots" / ("c%03d" % k), box_str, work / "xdg", c["frames"])
        times["render_s"] = round(time.monotonic() - t0, 1)
        ticks = scan["ticks"]
        if len(pngs) != len(ticks):
            raise ClipError("rendered %d frames for a fight of %d" % (len(pngs), len(ticks)))

        t0 = time.monotonic()
        max_bytes = int(round(a.max_mb * 1e6))
        mp4, poster, facts_path = work / (a.name + ".mp4"), work / (a.name + "-poster.jpg"), work / (a.name + ".facts.json")
        enc = encode_clip(pngs, ticks, version, mp4, max_bytes, tools["ffmpeg"], work=work / "enc")
        make_poster(pngs[0], version, ticks[0], poster, tools["ffmpeg"])
        times["encode_s"] = round(time.monotonic() - t0, 1)

        head, res = scan["header"], scan["header"].get("result", {})
        render_env = "OM_FIGHT=<work>/chunks/chunk-000.fight.json OM_SHOT_OUT=<work>/shots/c000 OM_FIT_EXTRA=%s" % box_str
        facts = {"name": a.name, "version": version, "kind": kind, "layout_id": head.get("layout_id"), "seed": head.get("seed"), "snapshot_every_ticks": head.get("snapshot_every"),
                 "winner": res.get("winner"), "survivors_A_B": res.get("survivors"), "last_tick": res.get("ticks"), "end_kind": res.get("end"), "capped": res.get("capped"),
                 "frames": len(ticks), "first_tick": ticks[0], "last_frame_tick": ticks[-1],
                 "label": {"first": label_text(version, ticks[0]), "last": label_text(version, ticks[-1])}, "camera_box": camera, "position_box": pos_box,
                 "video": dict(file=mp4.name, **_probe(tools["ffprobe"], mp4), size_bytes=mp4.stat().st_size, max_bytes=max_bytes, crf=enc["crf"], faststart=_faststart(mp4),
                               sha256=_sha256(mp4)),
                 "poster": {"file": poster.name, "sha256": _sha256(poster)},
                 "fight": {"file": fight_file, "sha256": _sha256(fight), "size_bytes": Path(fight).stat().st_size},
                 "record_command": record_cmd, "render_command": "%s %s" % (render_env, shlex.join(_render_argv("xvfb-run", a.godot))),
                 "encode_command": enc["command"], "tree": None if tree is None else str(tree), "engine_sha": sha, "chunk_frames": a.chunk, "times": times}
        for key in ("record_command", "render_command", "encode_command"):
            if facts[key]:
                facts[key] = facts[key].replace(str(work), "<work>").replace(str(out_dir), "<out>")
        facts_path.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in (mp4, poster, facts_path):
            shutil.move(str(p), str(out_dir / p.name))
        print("CLIP %s frames %d crf %d size %d -> %s" % (a.name, len(ticks), enc["crf"], facts["video"]["size_bytes"], out_dir))
    finally:
        if not a.keep_work:
            shutil.rmtree(work, ignore_errors=True)


def main(argv=None) -> int:
    ap = _parser()
    a = ap.parse_args(argv)
    if a.fight:
        if a.seed is not None or a.every is not None or a.tree:
            ap.error("--seed, --every and --tree are for --layout and --situation, not --fight")
    elif a.seed is None or a.every is None:
        ap.error("--layout and --situation need --seed and --every")
    try:
        _make(a)
    except Rejected as e:
        print("\n".join(e.lines))
        return 2
    except ClipError as e:
        print("clip: %s" % e, file=sys.stderr)
        return 2 if isinstance(e, BadInput) else 3 if isinstance(e, ToolMissing) else 5 if isinstance(e, SizeCapUnreachable) else 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
