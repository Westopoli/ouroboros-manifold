"""Render checks of the look-judge rig (docs/northstar/plans/cascades/look-judge-rig/spec.md piece 3): code over a frame PNG and its sidecar.

The sidecar of `<dir>/frame-<i>.id.png` or `<dir>/frame-<i>.png` is `<dir>/frame-<i>.json` (written by scenes/proto/fight_replay/replay_sidecar.gd):
{"frame", "width", "height", "units": [{"id", "side", "x", "y", "radius", "colour": "#rrggbb"}]}, x, y, radius in screen pixels.
A verdict is {"verdict": "PASS"|"FAIL", "reason", "numbers"}; a missing sidecar or image is FAIL, never PASS and never a raise (spec: fail closed).
Thresholds (max_offset_px, DRAFT-look-position-offset-px) are Westley's and are passed in; there is no default.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image


class SidecarMissing(Exception):
    pass


def sidecar_path(png: Path) -> Path:
    png = Path(png)
    m = re.match(r"^(frame-\d+)(\.id)?\.png$", png.name)
    if not m:
        raise SidecarMissing("no sidecar naming for %s" % png.name)
    return png.with_name(m.group(1) + ".json")


def load_sidecar(png: Path) -> dict:
    try:
        p = sidecar_path(png)
        return json.loads(p.read_text())
    except (OSError, ValueError) as e:
        raise SidecarMissing("sidecar missing or unreadable for %s: %s" % (Path(png).name, e))


def _rgb(png: Path) -> np.ndarray:
    return np.array(Image.open(png).convert("RGB"))


def _colour(hexs: str) -> tuple[int, int, int]:
    return int(hexs[1:3], 16), int(hexs[3:5], 16), int(hexs[5:7], 16)


def _disc(u: dict, shape: tuple[int, int]) -> np.ndarray:
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return (xx - u["x"]) ** 2 + (yy - u["y"]) ** 2 <= u["radius"] ** 2


def overlaps(id_png: Path) -> list[dict]:
    """Pairs of sidecar discs sharing pixels: [{"a", "b", "pixels"}], a < b, sorted."""
    sc = load_sidecar(id_png)
    shape = (int(sc["height"]), int(sc["width"]))
    units = sorted(sc["units"], key=lambda u: u["id"])
    discs = [_disc(u, shape) for u in units]
    out = []
    for i, a in enumerate(units):
        for j in range(i + 1, len(units)):
            n = int((discs[i] & discs[j]).sum())
            if n > 0:
                out.append({"a": a["id"], "b": units[j]["id"], "pixels": n})
    return sorted(out, key=lambda r: (r["a"], r["b"]))


def unit_pixels(id_png: Path) -> dict:
    """{unit id: count of pixels of that unit's ID colour in the image}."""
    sc = load_sidecar(id_png)
    img = _rgb(id_png)
    return {u["id"]: int((img == _colour(u["colour"])).all(axis=2).sum()) for u in sc["units"]}


def _verdict(ok: bool, reason: str, numbers: dict | None = None) -> dict:
    return {"verdict": "PASS" if ok else "FAIL", "reason": reason, "numbers": numbers or {}}


def check_position(id_png: Path, *, max_offset_px: float) -> dict:
    """Each unit's ID-colour centroid lies within max_offset_px of its sidecar x, y."""
    try:
        sc = load_sidecar(id_png)
        img = _rgb(id_png)
    except (SidecarMissing, OSError) as e:
        return _verdict(False, "sidecar or image unavailable: %s" % e)
    worst, bad = 0.0, []
    for u in sc["units"]:
        ys, xs = np.nonzero((img == _colour(u["colour"])).all(axis=2))
        if len(xs) == 0:
            bad.append(u["id"])
            worst = float("inf")
            continue
        off = float(np.hypot(xs.mean() - u["x"], ys.mean() - u["y"]))
        worst = max(worst, off)
        if off > max_offset_px:
            bad.append(u["id"])
    numbers = {"max_offset_px": max_offset_px, "worst_offset_px": worst, "bad_ids": bad}
    if bad:
        return _verdict(False, "units %s drawn off their sidecar position or not drawn" % bad, numbers)
    return _verdict(True, "every unit within %s px of its sidecar position" % max_offset_px, numbers)


def check_blank(png: Path) -> dict:
    """FAIL when the image is one flat colour."""
    try:
        img = _rgb(png)
    except OSError as e:
        return _verdict(False, "image unavailable: %s" % e)
    flat = bool((img == img[0, 0]).all())
    return _verdict(not flat, "image is one flat colour" if flat else "image holds more than one colour")


def check_frozen(png_a: Path, png_b: Path) -> dict:
    """FAIL when the two images are pixel-identical."""
    try:
        a, b = _rgb(png_a), _rgb(png_b)
    except OSError as e:
        return _verdict(False, "image unavailable: %s" % e)
    same = a.shape == b.shape and bool((a == b).all())
    return _verdict(not same, "the two frames are pixel-identical" if same else "the frames differ")
