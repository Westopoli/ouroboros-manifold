"""Render checks of the look-judge rig (docs/northstar/plans/cascades/look-judge-rig/spec.md piece 3): code over a frame PNG and its sidecar.

The sidecar of `<dir>/frame-<i>.id.png` or `<dir>/frame-<i>.png` is `<dir>/frame-<i>.json` (written by scenes/proto/fight_replay/replay_sidecar.gd):
{"frame", "width", "height", "units": [{"id", "side", "x", "y", "radius", "colour": "#rrggbb"}]}, x, y, radius in screen pixels.
A verdict is {"verdict": "PASS"|"FAIL", "reason", "numbers"}; a missing sidecar or image is FAIL, never PASS and never a raise (spec: fail closed).
Thresholds (max_offset_px, DRAFT-look-position-offset-px) are Westley's and are passed in; there is no default.
"""
from __future__ import annotations

import json
import math
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


def _shared_pixels(a: dict, b: dict, shape: tuple[int, int]) -> int:
    """Pixels inside both sidecar discs, counted in the window around the two centres (never a full-frame mask)."""
    if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) > a["radius"] + b["radius"]:
        return 0  # triangle inequality: no pixel can lie in both
    x0 = max(0, int(math.floor(max(a["x"] - a["radius"], b["x"] - b["radius"]))))
    x1 = min(shape[1], int(math.ceil(min(a["x"] + a["radius"], b["x"] + b["radius"]))) + 1)
    y0 = max(0, int(math.floor(max(a["y"] - a["radius"], b["y"] - b["radius"]))))
    y1 = min(shape[0], int(math.ceil(min(a["y"] + a["radius"], b["y"] + b["radius"]))) + 1)
    if x1 <= x0 or y1 <= y0:
        return 0
    yy, xx = np.mgrid[y0:y1, x0:x1]
    inside = lambda u: (xx - u["x"]) ** 2 + (yy - u["y"]) ** 2 <= u["radius"] ** 2
    return int((inside(a) & inside(b)).sum())


def overlaps(id_png: Path, *, fight: dict | None = None, frame: int | None = None, radius_wu: float | None = None) -> list[dict]:
    """Pairs of units standing inside each other: [{"a", "b", ...}], a < b, sorted.

    With `fight`, `frame` (index into fight["frames"], the i of frame-<i>.id.png) and `radius_wu`: the living same-layer units of that fight frame closer than radius_wu
    (R-097-05, judged on the fight file's wu geometry; the sidecar has no layer or alive); each row carries "dist_wu". Without them: the sidecar discs that share
    pixels, each row carrying "pixels".
    """
    if fight is not None:
        us = sorted((u for u in fight["frames"][frame]["units"] if u["alive"]), key=lambda u: u["id"])
        return [{"a": a["id"], "b": b["id"], "dist_wu": d} for i, a in enumerate(us) for b in us[i + 1:]
                if a["layer"] == b["layer"] and (d := math.hypot(a["x"] - b["x"], a["y"] - b["y"])) < radius_wu]
    sc = load_sidecar(id_png)
    shape = (int(sc["height"]), int(sc["width"]))
    units = sorted(sc["units"], key=lambda u: u["id"])
    out = []
    for i, a in enumerate(units):
        for b in units[i + 1:]:
            n = _shared_pixels(a, b, shape)
            if n > 0:
                out.append({"a": a["id"], "b": b["id"], "pixels": n})
    return out


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
