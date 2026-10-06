#!/usr/bin/env python3
"""Side-by-side look page input: render the C sim's ported terrain (seeds 11, 12, 13 at 16,000).

Usage: python scripts/terrain_look.py [outdir]   (needs libouroboros.so built)
Bands use the walkers mockup's band ramp; unwalkable cells are tinted magenta;
slope midlines are marked white. Prints walkable share, largest 4-neighbour
walkable region and band shares per seed. Terrain stage 1 spec, "look" lane.
"""
import ctypes
import pathlib
import struct
import sys
import zlib
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
CANVAS = 16000.0
SEEDS = (11, 12, 13)
# scenes/mockups/walkers/walkers_mockup.gd BAND_COLOURS (0..1 floats) as 8-bit.
BAND_RGB = [(102, 184, 107), (184, 204, 97), (230, 173, 77), (184, 122, 77), (235, 230, 224)]
STEEP_RGB = (217, 26, 217)
STEEP_MIX = 0.55
SLOPE_RGB = (255, 255, 255)
SCALE = 4  # pixels per cell


class Slope(ctypes.Structure):
    _fields_ = [("x0", ctypes.c_double), ("y0", ctypes.c_double), ("x1", ctypes.c_double),
                ("y1", ctypes.c_double), ("mx", ctypes.c_double), ("my", ctypes.c_double),
                ("length", ctypes.c_double), ("lower_band", ctypes.c_int32),
                ("upper_band", ctypes.c_int32)]


def load():
    lib = ctypes.CDLL(str(ROOT / "libouroboros.so"))
    P = ctypes.c_void_p
    lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    lib.om_world_new.restype = P
    lib.om_world_free.argtypes = [P]
    lib.om_map_set_canvas.argtypes = [P, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_generate.argtypes = [P, ctypes.c_uint64, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_cells.argtypes = [P, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
    lib.om_terrain_dump_bands.argtypes = [P, ctypes.c_void_p, ctypes.c_uint32]
    lib.om_terrain_dump_bands.restype = ctypes.c_uint32
    lib.om_terrain_walkable_at.argtypes = [P, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_slope_count.argtypes = [P]
    lib.om_terrain_slope_count.restype = ctypes.c_uint32
    lib.om_terrain_slope_get.argtypes = [P, ctypes.c_uint32, ctypes.POINTER(Slope)]
    return lib


def png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    pathlib.Path(path).write_bytes(data)


def largest_region(walk, n):
    seen = bytearray(n * n)
    best = 0
    for s in range(n * n):
        if not walk[s] or seen[s]:
            continue
        seen[s] = 1
        q = deque([s])
        size = 0
        while q:
            c = q.popleft()
            size += 1
            x, y = c % n, c // n
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < n and 0 <= ny < n:
                    i = ny * n + nx
                    if walk[i] and not seen[i]:
                        seen[i] = 1
                        q.append(i)
        best = max(best, size)
    return best


def look(lib, seed, outdir):
    w = lib.om_world_new(1, seed)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, seed, CANVAS, CANVAS) == 0
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    lib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    n = cw.value
    assert cw.value == ch.value
    buf = (ctypes.c_uint8 * (n * n))()
    assert lib.om_terrain_dump_bands(w, buf, n * n) == n * n
    bands = bytes(buf)
    cell = CANVAS / n
    walk = bytearray(n * n)
    for cy in range(n):
        for cx in range(n):
            walk[cy * n + cx] = 1 if lib.om_terrain_walkable_at(w, (cx + 0.5) * cell, (cy + 0.5) * cell) else 0
    px = [[0] * (n * SCALE * 3) for _ in range(n * SCALE)]
    for cy in range(n):
        for cx in range(n):
            i = cy * n + cx
            r, g, b = BAND_RGB[max(1, min(5, bands[i])) - 1]
            if not walk[i]:
                r, g, b = [round(a * (1 - STEEP_MIX) + t * STEEP_MIX) for a, t in zip((r, g, b), STEEP_RGB)]
            for dy in range(SCALE):
                row = px[cy * SCALE + dy]
                for dx in range(SCALE):
                    o = (cx * SCALE + dx) * 3
                    row[o:o + 3] = (r, g, b)
    k = lib.om_terrain_slope_count(w)
    for j in range(k):
        s = Slope()
        lib.om_terrain_slope_get(w, j, ctypes.byref(s))
        x = int(s.mx / CANVAS * n * SCALE)
        y = int(s.my / CANVAS * n * SCALE)
        for dy in (0, 1):
            for dx in (0, 1):
                if 0 <= x + dx < n * SCALE and 0 <= y + dy < n * SCALE:
                    px[y + dy][(x + dx) * 3:(x + dx) * 3 + 3] = SLOPE_RGB
    png(pathlib.Path(outdir) / f"sim_seed{seed}.png", n * SCALE, n * SCALE, px)
    total = n * n
    shares = [bands.count(bytes([b])) / total * 100 for b in range(1, 6)]
    print(f"seed {seed}: cells {n}x{n}, walkable {sum(walk) / total * 100:.1f}%, "
          f"largest walkable region {largest_region(walk, n) / total * 100:.1f}% of cells, "
          f"slopes {k}, band shares 1-5 " + " ".join(f"{s:.1f}%" for s in shares))
    lib.om_world_free(w)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "docs/northstar/research/landscape_design/sim_port")
    lib = load()
    for sd in SEEDS:
        look(lib, sd, out)
