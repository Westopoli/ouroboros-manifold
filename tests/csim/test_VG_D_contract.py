"""Visible-game programme lane D, contract amendment K-d, sim side (docs/northstar/plans/2026-10-07-visible-game-spec.md
rev 4, "Contract gates" row K-d and lane D; docs/northstar/plans/preflight_2026-10-07/5-space-kit.md).
Fenced: builders never edit this file.

Proves S-246 (R-246-01: a space mission's five layers are open-or-blocked sheets, the generator ported into the
simulation; Q-STAGE3-03 b) and E-01 R-001-04 (a binary mask per layer): the getters om_space_field_generate_nodes,
om_space_field_present and om_space_field_get_mask, their determinism, and that the mask they report is the one
routing reads (the mapgen blocked bits, via om_map_sample_layer_accessibility).

ASSUMED PROTOTYPES (the spec names the symbols, not their arguments; a mismatch with K-d's signatures.toml is a
K-d question, not a test defect; mirrors om_terrain_generate / om_terrain_dump_bands):
  int      om_space_field_generate_nodes(om_world*, uint32_t seed, double canvas_w, double canvas_h)   0 ok, nonzero refused
  int      om_space_field_present(const om_world*)                                               1 when a field is held
  uint32_t om_space_field_get_mask(const om_world*, uint32_t layer, uint8_t *out, uint32_t cap)  layer 0..4; writes one
           byte per 100 wu cell, row-major (cy * 240 + cx), 1 = blocked, 0 = open (the blocked_bits sense, not the
           mockup's open = 1); returns the cell count (57600), 0 when no field or layer >= 5 or cap too small
Canvas 24000 wu (the kit's default, field_map_space.gd generate(seed, canvas = 24000)); 240 x 240 cells; 5 layers.

Not asserted here (no number or shape given): blocked share per density, connectivity/carve (lane D's statistical
piece), refusal of other canvases.
On main every symbol is missing, so every test fails on the K-d symbol check.
"""
import ctypes

import pytest

W = ctypes.c_void_p
U8P = ctypes.POINTER(ctypes.c_uint8)
CANVAS = 24000.0
DENSITY = 35.0
N = 240
CELLS = N * N
LAYERS = 5
SEED = 11
NEW = ["om_space_field_generate_nodes", "om_space_field_present", "om_space_field_get_mask"]


def bind(lib):
    missing = [n for n in NEW if not hasattr(lib, n)]
    assert not missing, f"K-d symbols missing from libouroboros.so: {missing}"
    g = lib.om_space_field_generate_nodes
    g.argtypes, g.restype = [W, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32], ctypes.c_int
    p = lib.om_space_field_present
    p.argtypes, p.restype = [W], ctypes.c_int
    m = lib.om_space_field_get_mask
    m.argtypes, m.restype = [W, ctypes.c_uint32, U8P, ctypes.c_uint32], ctypes.c_uint32
    return g, p, m


def make_world(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    return w


def masks_of(lib, w):
    out = []
    for k in range(LAYERS):
        buf = (ctypes.c_uint8 * CELLS)()
        n = lib.om_space_field_get_mask(w, k, buf, CELLS)
        assert n == CELLS, f"layer {k}: get_mask returned {n}, expected {CELLS}"
        out.append(bytes(buf))
    return out


def differing_layers(a, b):
    """Layer indices where two mask sets differ. Positive control below proves it sees a planted flip."""
    return [k for k in range(LAYERS) if a[k] != b[k]]


def test_symbols_present_and_bind(lib):
    bind(lib)


def test_no_field_before_generate(lib, world_factory):
    """R-246-01 negative: a world with no generated field reports none and writes nothing."""
    bind(lib)
    w = make_world(lib, world_factory)
    assert lib.om_space_field_present(w) == 0
    buf = (ctypes.c_uint8 * CELLS)()
    assert lib.om_space_field_get_mask(w, 0, buf, CELLS) == 0
    assert lib.om_space_field_present(None) == 0


def test_generate_makes_five_binary_layers_with_both_states(lib, world_factory):
    """R-246-01 / R-001-04: five layers, each cell open or blocked; every layer has blocked cells and open cells."""
    g, _, _ = bind(lib)
    w = make_world(lib, world_factory)
    assert g(w, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert lib.om_space_field_present(w) == 1
    for k, m in enumerate(masks_of(lib, w)):
        assert set(m) <= {0, 1}, f"layer {k}: values {sorted(set(m))}"
        assert set(m) == {0, 1}, f"layer {k}: not both open and blocked (blocked cells: {sum(m)})"


def test_get_mask_bounds(lib, world_factory):
    """Layer 5 and a short buffer return 0 and write nothing."""
    g, _, _ = bind(lib)
    w = make_world(lib, world_factory)
    assert g(w, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    buf = (ctypes.c_uint8 * CELLS)()
    assert lib.om_space_field_get_mask(w, LAYERS, buf, CELLS) == 0
    assert lib.om_space_field_get_mask(w, 0, buf, CELLS - 1) == 0
    assert not any(buf), "a refused read wrote into the buffer"


def test_same_seed_identical_masks_two_worlds(lib, world_factory):
    """Determinism contract: same seed, byte-identical masks."""
    g, _, _ = bind(lib)
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert g(a, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0 and g(b, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert differing_layers(masks_of(lib, a), masks_of(lib, b)) == []


def test_different_seed_changes_a_layer(lib, world_factory):
    g, _, _ = bind(lib)
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert g(a, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0 and g(b, SEED + 1, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert differing_layers(masks_of(lib, a), masks_of(lib, b)), "seeds 11 and 12 gave identical fields"


def test_control_differing_layers_detects_a_flip():
    """Positive control for differing_layers."""
    a = [bytes(CELLS)] * LAYERS
    b = list(a)
    b[3] = bytes([1]) + bytes(CELLS - 1)
    assert differing_layers(a, b) == [3] and differing_layers(a, a) == []


def test_generated_mask_is_what_routing_reads(lib, world_factory):
    """R-246-01 'masks written to blocked_bits' (pre-flight 5): the reported mask equals
    om_map_sample_layer_accessibility (1 open) at every cell centre of every layer."""
    g, _, _ = bind(lib)
    w = make_world(lib, world_factory)
    assert g(w, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    f = lib.om_map_sample_layer_accessibility
    f.argtypes, f.restype = [W, ctypes.c_double, ctypes.c_double, ctypes.c_uint32], ctypes.c_int
    bad = []
    for k, m in enumerate(masks_of(lib, w)):
        for cy in range(0, N, 3):
            for cx in range(0, N, 3):
                if f(w, (cx + .5) * 100.0, (cy + .5) * 100.0, k) != (0 if m[cy * N + cx] else 1):
                    bad.append((k, cx, cy))
    assert not bad, f"{len(bad)} cells where get_mask disagrees with routing, first {bad[:3]}"


def test_regenerate_replaces_field(lib, world_factory):
    """A second generate (another seed) replaces the first; no stale blocked bits from the first remain."""
    g, _, _ = bind(lib)
    a, b = make_world(lib, world_factory), make_world(lib, world_factory)
    assert g(a, SEED, CANVAS, CANVAS, DENSITY, None, None, 0) == 0 and g(a, SEED + 1, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert g(b, SEED + 1, CANVAS, CANVAS, DENSITY, None, None, 0) == 0
    assert differing_layers(masks_of(lib, a), masks_of(lib, b)) == []
