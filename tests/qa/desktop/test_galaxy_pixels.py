# spec: docs/northstar/plans/push/specs/C2.md::S-106/R-106-01
"""Piece C2-5: the galaxy's owner colours must reach the screen pixels.

Look 4 (docs/northstar/proving_ground/evidence/push_2026-09-22/first_look/
README.md, "Look 4") found the galaxy's qa_state() correct (80 systems,
51 owned, 16 distinct region colours) while every dot and edge drew black:
tests/test_galaxy_view.gd only reads qa_state(), never a pixel, so the
render bug passed every fenced test. This detector closes that gap by
reading the real screenshot at each owned system's projected position
(qa_state()["systems_px"]) and comparing it to that region's
qa_state()["region_colours"] entry.

Rules proven (S-106/R-106-01: a region is drawn in its owner's colour):
  C2-5-01  most isolated owned systems show their region colour on screen.
  C2-5-02  the owned systems show several different colours on screen, not
           one colour or none.
Positive control: the owner-colour-flat plant collapses every region to one
colour, so the same detector must report a failure on it.
"""
from __future__ import annotations

import struct
import time
import zlib
from pathlib import Path

import numpy as np
import pytest

from daemon_client import (
    GodotGame,
    control_center,
    find_control,
    pick_free_port,
    wait_for,
)

GALAXY_SCENE = "res://scenes/galaxy/galaxy_view.tscn"
MAIN_MENU_SCENE = "res://scenes/main_menu/main_menu.tscn"
PRIVACY_MODAL_SCENE = "res://scenes/privacy_modal/privacy_modal.tscn"

BOOT_TIMEOUT_S = 45.0
STEP_TIMEOUT_S = 10.0
ISOLATION_PX = 12.0
CHANNEL_TOLERANCE = 40
MIN_SAMPLES = 5
MIN_MATCH_FRACTION = 0.6
MIN_DISTINCT_SCREEN_COLOURS = 5
DISTINCT_STEP = 32


def _read_png_rgb(path: Path) -> np.ndarray:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG: %s" % path
    pos, width, height, depth, ctype = 8, 0, 0, 0, 0
    idat = b""
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    assert depth == 8 and ctype in (2, 6), "unsupported PNG (depth %d type %d)" % (depth, ctype)
    bpp = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = width * bpp
    out = np.zeros((height, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    offset = 0
    for y in range(height):
        ftype = raw[offset]
        line = np.frombuffer(raw, dtype=np.uint8, count=stride, offset=offset + 1).astype(np.int32)
        offset += 1 + stride
        if ftype == 0:
            cur = line
        elif ftype == 1:
            cur = line.copy()
            for x in range(bpp, stride):
                cur[x] = (cur[x] + cur[x - bpp]) & 255
        elif ftype == 2:
            cur = (line + prev) & 255
        elif ftype == 3:
            cur = line.copy()
            for x in range(stride):
                left = cur[x - bpp] if x >= bpp else 0
                cur[x] = (cur[x] + ((left + prev[x]) >> 1)) & 255
        elif ftype == 4:
            cur = line.copy()
            for x in range(stride):
                a = cur[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                cur[x] = (cur[x] + pred) & 255
        else:
            raise AssertionError("bad PNG filter %d" % ftype)
        out[y] = cur
        prev = cur
    return out.reshape(height, width, bpp)[:, :, :3]


def _boot_to_galaxy(game: GodotGame) -> None:
    client = game.client
    deadline = time.monotonic() + BOOT_TIMEOUT_S
    clicked = False
    while time.monotonic() < deadline:
        scene = client.state()["result"].get("scene")
        if scene == MAIN_MENU_SCENE:
            break
        if scene == PRIVACY_MODAL_SCENE and not clicked:
            accept = find_control(client.tree(), "AcceptButton")
            if accept is not None:
                client.click(*control_center(accept))
                clicked = True
        time.sleep(0.5)
    else:
        raise AssertionError("never reached the main menu")
    time.sleep(2.0)
    client.click(*control_center(find_control(client.tree(), "NewGame")))
    wait_for(client, lambda s: s.get("scene") == GALAXY_SCENE, STEP_TIMEOUT_S, label="galaxy")
    time.sleep(2.0)


def _sample_owned_systems(client, shot_name: str) -> list[tuple[int, tuple[float, float, float], np.ndarray]]:
    qa = client.state()["result"]["qa"]
    client.screenshot(shot_name)
    time.sleep(0.5)
    img = _read_png_rgb(client.user_dir / "qa" / (shot_name + ".png"))
    height, width = img.shape[:2]
    px = {int(i): v for i, v in qa["systems_px"].items()}
    samples = []
    for key, owner in qa["owners"].items():
        i = int(key)
        if int(owner) < 0 or i not in px:
            continue
        x, y = px[i]
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < width and 0 <= yi < height):
            continue
        nearest = min(
            (((x - ox) ** 2 + (y - oy) ** 2) ** 0.5 for j, (ox, oy) in px.items() if j != i),
            default=1e9,
        )
        if nearest < ISOLATION_PX:
            continue
        col = qa["region_colours"][str(i)] if str(i) in qa["region_colours"] else qa["region_colours"][i]
        expected = tuple(float(c) * 255.0 for c in col[:3])
        samples.append((i, expected, img[yi, xi]))
    return samples


def _detector_failures(samples) -> list[str]:
    problems = []
    if len(samples) < MIN_SAMPLES:
        problems.append("only %d isolated owned systems in view, need %d" % (len(samples), MIN_SAMPLES))
        return problems
    hits = sum(1 for _, exp, got in samples if max(abs(exp[k] - float(got[k])) for k in range(3)) <= CHANNEL_TOLERANCE)
    frac = hits / len(samples)
    if frac < MIN_MATCH_FRACTION:
        first = samples[0]
        problems.append(
            "C2-5-01: %d of %d isolated owned systems show their region colour (%.2f < %.2f); "
            "e.g. region %d expected rgb %s, screen rgb %s"
            % (hits, len(samples), frac, MIN_MATCH_FRACTION, first[0],
               tuple(round(c) for c in first[1]), tuple(int(c) for c in first[2]))
        )
    # TD-VG-B-11: count the distinct EXPECTED owner colours among samples that matched within
    # CHANNEL_TOLERANCE of their own region's colour (not screen-colour buckets, which label glow smears).
    matched = [exp for _, exp, got in samples
               if max(abs(exp[k] - float(got[k])) for k in range(3)) <= CHANNEL_TOLERANCE]
    distinct = {tuple(int(round(c)) for c in exp) for exp in matched}
    if len(distinct) < MIN_DISTINCT_SCREEN_COLOURS:
        problems.append(
            "C2-5-02: owned systems show %d distinct screen colours, need >= %d"
            % (len(distinct), MIN_DISTINCT_SCREEN_COLOURS)
        )
    return problems


@pytest.fixture()
def galaxy_game():
    g = GodotGame(qa_port=pick_free_port(), seed=1)
    g.start()
    g.wait_for_port(timeout=60.0)
    try:
        _boot_to_galaxy(g)
        yield g
    finally:
        g.stop()


def test_c2_5_owner_colours_reach_the_pixels(galaxy_game):
    samples = _sample_owned_systems(galaxy_game.client, "c2_5_galaxy_clean")
    problems = _detector_failures(samples)
    assert not problems, "; ".join(problems)


def test_control_owner_colour_flat_trips_the_detector(galaxy_game):
    client = galaxy_game.client
    resp = client.call("plant", "owner-colour-flat")
    assert resp.get("ok") and resp["result"].get("activated"), "plant did not activate: %r" % resp
    time.sleep(1.5)
    samples = _sample_owned_systems(client, "c2_5_galaxy_flat")
    problems = _detector_failures(samples)
    assert problems, (
        "control is dead: the detector reported no problem on a galaxy whose regions all share one "
        "colour (%d samples)" % len(samples)
    )


MIN_PLANT_DIFF_PX = 500


def test_c2_5b_owner_colour_flat_plant_reaches_the_pixels(galaxy_game):
    """look 5: the plant changed region_colours in qa_state() but never re-rendered the
    points, so the screen kept the real owner colours (0 of 921600 pixels differed).
    A fault planted in the render path must show in the render."""
    client = galaxy_game.client
    client.screenshot("c2_5b_before")
    time.sleep(0.5)
    before = _read_png_rgb(client.user_dir / "qa" / "c2_5b_before.png")
    resp = client.call("plant", "owner-colour-flat")
    assert resp.get("ok") and resp["result"].get("activated"), "plant did not activate: %r" % resp
    time.sleep(1.5)
    client.screenshot("c2_5b_after")
    time.sleep(0.5)
    after = _read_png_rgb(client.user_dir / "qa" / "c2_5b_after.png")
    differing = int(np.any(before != after, axis=2).sum())
    assert differing >= MIN_PLANT_DIFF_PX, (
        "owner-colour-flat changed %d of %d pixels (need >= %d): the plant is state-only"
        % (differing, before.shape[0] * before.shape[1], MIN_PLANT_DIFF_PX)
    )


MIN_EDGES_2D_DIFF_PX = 200


def test_c2_7_edges_2d_overlay_plant_reaches_the_pixels(galaxy_game):
    """QA-002: edges-2d-overlay plant removed all edges (drew nothing).
    After the fix, planting edges-2d-overlay must draw 2D lines between
    system screen positions, changing >= MIN_EDGES_2D_DIFF_PX pixels
    compared to the clean screenshot. Also verifies edge_counts is
    preserved (the plant changes rendering, never the edge data)."""
    client = galaxy_game.client

    qa_clean = client.state()["result"]["qa"]
    clean_edge_total = sum(int(v) for v in qa_clean.get("edge_counts", {}).values())

    client.screenshot("c2_7_clean")
    time.sleep(0.5)
    clean_img = _read_png_rgb(client.user_dir / "qa" / "c2_7_clean.png")

    resp = client.call("plant", "edges-2d-overlay")
    assert resp.get("ok") and resp["result"].get("activated"), (
        "plant did not activate: %r" % resp
    )
    time.sleep(1.5)

    qa_planted = client.state()["result"]["qa"]
    planted_edge_total = sum(int(v) for v in qa_planted.get("edge_counts", {}).values())
    assert planted_edge_total == clean_edge_total, (
        "QA-002: edge_counts total changed after plant: clean=%d planted=%d"
        % (clean_edge_total, planted_edge_total)
    )

    client.screenshot("c2_7_planted")
    time.sleep(0.5)
    planted_img = _read_png_rgb(client.user_dir / "qa" / "c2_7_planted.png")

    differing = int(np.any(clean_img != planted_img, axis=2).sum())
    assert differing >= MIN_EDGES_2D_DIFF_PX, (
        "QA-002 edges-2d-overlay: plant changed %d of %d pixels (need >= %d); "
        "the plant drew nothing (all edges vanished)"
        % (differing, clean_img.shape[0] * clean_img.shape[1], MIN_EDGES_2D_DIFF_PX)
    )
