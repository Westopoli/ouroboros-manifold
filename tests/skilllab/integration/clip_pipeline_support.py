"""Shared helpers of the clip-pipeline tests (not collected). Interface: docs/reports/2026-11-24-clip-pipeline-interface.md.

Everything here reads files or runs tools; nothing opens a picture: checks are ffprobe fields, box order in the mp4, hashes, the gate's `frame_busyness` (a file
statistic over a decoded frame) and tesseract on the label strip (a program reading pixels). Also holds `scratch_encode`, a frozen copy of the scratch ffmpeg line
(`r6-clips/tmp/enc.py`): it makes the deliberately wrong clips (no faststart, other fps or width) the checkers must reject.
See also: tests/qa/test_fight_replay.py (the scene launch this mirrors)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PY = os.environ.get("OM_CLIP_PYTHON") or sys.executable
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
LAYOUT_SMALL = "docs/northstar/research/layer_dynamics/catalogue/L-0047.toml"  # 32 units, wipe at tick 1591 (every 2), runs in about a second
LAYOUT_REJECTED = "docs/northstar/research/layer_dynamics/catalogue/L-0001.toml"  # closeup prints "REJECT L-0001 R6" and exits 2

sys.path.insert(0, str(ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def env_clean(extra: dict | None = None) -> dict:
    """Child environment for Godot and the CLI: no seat display, software GL, scratch XDG, the caller's TMPDIR."""
    env = dict(os.environ)
    for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
        env.pop(var, None)
    env["LC_ALL"] = "C"
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env["GALLIUM_DRIVER"] = "llvmpipe"
    if not env.get("XDG_DATA_HOME"):
        env["XDG_DATA_HOME"] = str(Path(tempfile.gettempdir()) / "clip-xdg")
    env.update(extra or {})
    return env


def run_clip(args: list, cwd: Path = ROOT, env: dict | None = None, timeout: int = 1700) -> subprocess.CompletedProcess:
    """`python -m scripts.skilllab.arena.clip <args>` in the repo."""
    return subprocess.run([PY, "-m", "scripts.skilllab.arena.clip", *map(str, args)], cwd=str(cwd), env=env or env_clean(),
                          capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------- synthetic fight files (the scene reads them; the sim is not needed)

def synthetic_fight(frames: int = 12, units_per_side: int = 3, spread: float = 1.0, odd_last: bool = True, layout_id: str = "L-0001", seed: int = 1) -> dict:
    """An om-fight-2 document from snapshot.example: frames 100 ticks apart, units walking right 3 wu a frame, x scaled by `spread` (a wider fight is a
    different extent). With `odd_last` the last frame sits at an odd tick off the grid, like a real fight's last tick (1591 in L-0047)."""
    from scripts.skilllab.arena import snapshot
    doc = snapshot.example(frames=frames, units_per_side=units_per_side, schema=snapshot.SCHEMA_V2)
    for n, fr in enumerate(doc["frames"]):
        for u in fr["units"]:
            u["x"] = round((u["x"] + 3.0 * n) * spread, 2)
            u["y"] = round(u["y"] * spread, 2)
    if odd_last:
        doc["frames"][-1]["tick"] += 7
        doc["result"]["ticks"] = doc["frames"][-1]["tick"]
    doc["layout_id"], doc["seed"] = layout_id, seed
    return doc


def write_fight(path: Path, doc: dict) -> Path:
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def doc_box(doc: dict) -> list:
    xs = [u["x"] for fr in doc["frames"] for u in fr["units"]]
    ys = [u["y"] for fr in doc["frames"] for u in fr["units"]]
    return [min(xs), min(ys), max(xs), max(ys)]


def write_long_fight(path: Path, frames: int, units_per_side: int, every: int = 2) -> Path:
    """A fight file of `frames` frames (`every` ticks apart) written one frame at a time, so the writer itself stays small. The keys are sorted as a real fight
    file's are, so header keys come both before and after `frames` (built_features < frames < landscape ... tick_rate)."""
    from scripts.skilllab.arena import snapshot
    base = snapshot.example(frames=3, units_per_side=units_per_side, schema=snapshot.SCHEMA_V2)
    base["built_features"] = []
    base["landscape"] = "small_flat"
    last = (frames - 1) * every
    base["result"].update({"ticks": last, "survivors": [units_per_side, 0], "end": "wipe", "winner": "A"})
    base["snapshot_every"] = every
    base["frames"] = ["@@FRAMES@@"]
    text = json.dumps(base, sort_keys=True, indent=2) + "\n"
    head, tail = text.split('    "@@FRAMES@@"\n')
    proto = snapshot.example(frames=2, units_per_side=units_per_side, schema=snapshot.SCHEMA_V2)["frames"][0]["units"]
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for n in range(frames):
            rows = [dict(u, x=round(u["x"] + 0.5 * n, 2)) for u in proto]
            fr = {"alive": [units_per_side, units_per_side if n < frames - 1 else 0], "tick": n * every, "units": rows}
            if n == frames - 1:
                for r in rows:
                    if r["side"] == "B":
                        r["alive"], r["hp"] = False, 0.0
            f.write(textwrap.indent(json.dumps(fr, sort_keys=True, indent=2), "    ") + (",\n" if n < frames - 1 else "\n"))
        f.write(tail)
    return path


# ---------------------------------------------------------------- mp4 checks

def probe(mp4: Path) -> dict:
    """ffprobe: codec, pix_fmt, rates, size in pixels, counted frames, duration, bytes."""
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=codec_name,pix_fmt,avg_frame_rate,r_frame_rate,width,height,nb_read_frames:format=duration,size", "-of", "json", str(mp4)],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return {"codec": s["codec_name"], "pix_fmt": s["pix_fmt"], "avg_frame_rate": s["avg_frame_rate"], "r_frame_rate": s["r_frame_rate"],
            "width": s["width"], "height": s["height"], "frames": int(s["nb_read_frames"]), "duration": float(j["format"]["duration"]), "size": int(j["format"]["size"])}


def top_boxes(mp4: Path) -> list:
    """Top-level ISO box types in file order (ftyp, moov, mdat ...)."""
    types, size_total = [], mp4.stat().st_size
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
            types.append(typ.decode("latin1"))
            if size < 8:
                break
            pos += size
    return types


def is_faststart(mp4: Path) -> bool:
    t = top_boxes(mp4)
    return "moov" in t and "mdat" in t and t.index("moov") < t.index("mdat")


def video_problems(mp4: Path, width: int = 1600, frames: int | None = None, max_bytes: int | None = None) -> list:
    """Every way `mp4` misses the brief's format: codec h264, yuv420p, 20 fps, width 1600, faststart, size cap, frame count."""
    p = probe(mp4)
    bad = []
    if p["codec"] != "h264":
        bad.append("codec %s" % p["codec"])
    if p["pix_fmt"] != "yuv420p":
        bad.append("pix_fmt %s" % p["pix_fmt"])
    if p["avg_frame_rate"] != "20/1" or p["r_frame_rate"] != "20/1":
        bad.append("fps %s / %s" % (p["avg_frame_rate"], p["r_frame_rate"]))
    if p["width"] != width:
        bad.append("width %d" % p["width"])
    if not is_faststart(mp4):
        bad.append("not faststart: boxes %s" % top_boxes(mp4))
    if frames is not None and p["frames"] != frames:
        bad.append("frames %d, wanted %d" % (p["frames"], frames))
    if max_bytes is not None and p["size"] > max_bytes:
        bad.append("size %d over cap %d" % (p["size"], max_bytes))
    return bad


def decode_frame(mp4: Path, index: int, out_png: Path, crop: str | None = None, extra_vf: str = "") -> Path:
    vf = "select=eq(n\\,%d)" % index + ("," + crop if crop else "") + extra_vf
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp4), "-vf", vf, "-frames:v", "1", str(out_png)], check=True)
    assert out_png.exists() and out_png.stat().st_size > 0, "ffmpeg wrote no frame %d of %s" % (index, mp4)
    return out_png


def label_ocr(image: Path, work: Path, crop: str = "crop=800:80:0:0") -> str:
    """The burned label read back by tesseract: the top-left strip, inverted and doubled, whitespace squeezed."""
    strip = work / ("strip-%s.png" % image.stem)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(image), "-vf", crop + ",negate,scale=iw*2:ih*2:flags=lanczos", str(strip)], check=True)
    text = subprocess.run(["tesseract", str(strip), "stdout", "--psm", "7"], capture_output=True, text=True, check=True).stdout
    return " ".join(text.split())


def frame_label(mp4: Path, index: int, work: Path) -> str:
    png = decode_frame(mp4, index, work / ("lab-%s-%d.png" % (mp4.stem, index)))
    return label_ocr(png, work)


# ---------------------------------------------------------------- synthetic PNG frames

def make_pngs(folder: Path, count: int, size=(960, 540), noise: bool = False) -> list:
    """`count` frames: a grey ramp with a bright square that moves right each frame; with `noise` a random speckle on top (it makes the encoder spend bytes)."""
    import numpy as np
    from PIL import Image
    folder.mkdir(parents=True, exist_ok=True)
    w, h = size
    rng = np.random.default_rng(7)
    ramp = np.tile(np.linspace(30, 120, w, dtype=np.uint8), (h, 1))
    out = []
    for i in range(count):
        a = np.stack([ramp, ramp // 2, 255 - ramp], axis=2)
        x = 40 + 12 * i
        a[200:260, x:x + 60] = (240, 240, 60)
        if noise:
            a = np.clip(a.astype(np.int16) + rng.integers(-60, 60, a.shape), 0, 255).astype(np.uint8)
        p = folder / ("f%05d.png" % i)
        Image.fromarray(a).save(p)
        out.append(p)
    return out


# ---------------------------------------------------------------- the scratch ffmpeg line, frozen (wrong clips for the checker controls)

def scratch_encode(frames: list, ticks: list, version: str, out_mp4: Path, crf: int = 23, faststart: bool = True, fps: int = 20, width: int = 1600) -> None:
    """Control for encode_clip: scratch enc.py's ffmpeg line (label burn, scale, yuv420p, faststart) over PNG frames. `faststart=False`, another `fps` or `width`
    make the deliberately wrong clips the checkers must reject."""
    work = out_mp4.parent / (out_mp4.stem + "-seq")
    work.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(frames):
        link = work / ("f%05d.png" % i)
        if not link.exists():
            os.symlink(p, link)
    base = "fontfile=%s:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.9:boxborderw=6:x=20:y=8" % FONT
    pad = " " * 30
    parts = []
    for i, t in enumerate(ticks):
        parts.append("drawtext=%s:enable='eq(n,%d)':text='%s  tick %d%s'" % (base, i, version, t, pad))
    vf = "scale=%d:-2:flags=lanczos,format=yuv420p," % width + ",".join(parts)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(fps), "-i", str(work / "f%05d.png"), "-vf", vf, "-c:v", "libx264", "-preset", "medium",
           "-crf", str(crf), "-pix_fmt", "yuv420p"] + (["-movflags", "+faststart"] if faststart else []) + ["-r", str(fps), str(out_mp4)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(work)
