"""E-01 R-005-10: ground blocks sight (terrain stage 2, spec 2026-10-06, "mask" lane).

om_terrain_sight_blocks(w, layer0, x0, y0, layer1, x1, y1): each eye is max(terrain height, floor of
the unit's layer) + OM_TP_SIGHT_EYE_HEIGHT; samples every 25 wu along the segment, skipping samples
strictly less than 50 wu from either end; 1 when terrain at a sample exceeds the line there.

The expected answer comes from a reference sampler written here from om_terrain_height_at (the spec's
rule), and a case is used only when the reference clears or blocks by at least CLEARANCE_WU, so the
sim's fixed-point heights cannot flip it. Cases are found by searching the generated field (seed 11,
canvas 16,000), always on bands 2 and up and with each unit on layer band-1, so the layer floor never
lifts an eye above the ground. Each sees-case test also asserts the ridge case blocks (positive
control: a sampler that never blocks fails them, as the stub does today).

Picked cells (layer, x, y) -> (layer, x, y):
ridge: (4, 12450.0, 2150.0) -> (4, 11883.2, 1583.2)
plateau: (2, 12150.0, 4450.0) -> (1, 12600.0, 4000.0)
flat: (2, 6050.0, 650.0) -> (2, 5801.4, 401.4)
cliff: (2, 7650.0, 8850.0) -> (1, 7650.0, 8520.7)
"""
import json
import pathlib
import random
import subprocess
import sys

import pytest

SEED = 11
CANVAS = 16000.0
CELL_WU = 100.0
EYE_WU = 50.0                 # OM_TP_SIGHT_EYE_HEIGHT default
STEP_WU = 25.0
EXEMPT_WU = 50.0
CLEARANCE_WU = 6.0            # provisional (2026-10-06): margin so fixed-point heights cannot flip a case
SEARCH_RNG_SEED = 20261006    # provisional (2026-10-06)
SEARCH_TRIES = 200000         # provisional (2026-10-06)
MIN_RANGE_WU = 300.0
MAX_RANGE_WU = 900.0
CLIFF_NEAR_WU = 150.0
PLATEAU_OWN_CELLS = 2         # provisional (2026-10-06): own-plateau cells the line crosses before leaving
MIN_BAND = 2
N_OPEN = 20                   # provisional (2026-10-06)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _h(lib, w, x, y):
    return lib.om_terrain_height_at(w, x, y)


def _band(lib, w, x, y):
    return lib.om_terrain_band_at(w, x, y)


def _profile(lib, w, p0, p1):
    """(min clearance, max excess) of the line over the terrain at the non-exempt samples."""
    (x0, y0), (x1, y1) = p0, p1
    e0 = _h(lib, w, x0, y0) + EYE_WU
    e1 = _h(lib, w, x1, y1) + EYE_WU
    d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    n = int(d // STEP_WU)
    min_clear = float("inf")
    samples = []
    for k in range(1, n + 1):
        s = k * STEP_WU
        if s < EXEMPT_WU or d - s < EXEMPT_WU:
            continue
        t = s / d
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        clear = (e0 + (e1 - e0) * t) - _h(lib, w, x, y)
        min_clear = min(min_clear, clear)
        samples.append((x, y, clear))
    return min_clear, samples


def _search(lib, w):
    rng = random.Random(SEARCH_RNG_SEED)
    found = {}
    lo, hi = 5, int(CANVAS / CELL_WU) - 5
    for _ in range(SEARCH_TRIES):
        if len(found) == 4:
            break
        x0 = (rng.randrange(lo, hi) + 0.5) * CELL_WU
        y0 = (rng.randrange(lo, hi) + 0.5) * CELL_WU

        r = rng.uniform(MIN_RANGE_WU, MAX_RANGE_WU)
        # axis-and-diagonal-free direction via a lookup keeps this free of trig library differences
        dx, dy = rng.choice(((1, 0), (0, 1), (-1, 0), (0, -1), (0.7071, 0.7071), (-0.7071, 0.7071),
                             (0.7071, -0.7071), (-0.7071, -0.7071)))
        x1 = x0 + dx * r
        y1 = y0 + dy * r
        if not (100 < x1 < CANVAS - 100 and 100 < y1 < CANVAS - 100):
            continue
        b0, b1 = _band(lib, w, x0, y0), _band(lib, w, x1, y1)
        if b0 < MIN_BAND or b1 < MIN_BAND:
            continue
        mc, samples = _profile(lib, w, (x0, y0), (x1, y1))
        if not samples:
            continue
        max_excess = -min(c for _, _, c in samples)
        bands = [_band(lib, w, x, y) for x, y, _ in samples]
        case = ((b0 - 1, x0, y0), (b1 - 1, x1, y1))
        if "ridge" not in found and max_excess >= CLEARANCE_WU:
            # a ridge higher than both eye lines
            e0 = _h(lib, w, x0, y0) + EYE_WU
            e1 = _h(lib, w, x1, y1) + EYE_WU
            top = max(_h(lib, w, x, y) for x, y, _ in samples)
            if top - max(e0, e1) >= CLEARANCE_WU:
                found["ridge"] = case
        if mc < CLEARANCE_WU:
            continue
        if "flat" not in found and b0 == b1 and all(b == b0 for b in bands):
            found["flat"] = case
        if b0 == b1 + 1 and "plateau" not in found:
            own = 0
            for (x, y, _), b in zip(samples, bands):
                if b != b0:
                    break
                own += 1
            # own-plateau cells = samples (25 wu apart) before the band changes
            if own * STEP_WU >= PLATEAU_OWN_CELLS * CELL_WU:
                found["plateau"] = case
        if b0 == b1 + 1 and "cliff" not in found and bands[-1] == b1:
            # one band transition b0 -> b1, target within CLIFF_NEAR_WU of it
            idx = [i for i in range(1, len(bands)) if bands[i] != bands[i - 1]]
            if len(idx) == 1 and bands[idx[0]] == b1:
                edge_to_target = (len(samples) - idx[0]) * STEP_WU
                if edge_to_target <= CLIFF_NEAR_WU and idx[0] * STEP_WU >= CELL_WU:
                    found["cliff"] = case
    return found


@pytest.fixture
def mk(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    return w


@pytest.fixture
def cases(lib, mk):
    found = _search(lib, mk)
    missing = {"plateau", "ridge", "flat", "cliff"} - set(found)
    assert not missing, f"search found no case for {sorted(missing)}"
    return found


def _blocks(lib, w, case):
    (l0, x0, y0), (l1, x1, y1) = case
    return lib.om_terrain_sight_blocks(w, l0, x0, y0, l1, x1, y1)


def _ridge_blocks(lib, w, cases):
    """Positive control shared by the sees-tests: the sampler can say 1."""
    assert _blocks(lib, w, cases["ridge"]) == 1, "positive control: the ridge case must block"


def test_R_005_10_ridge_higher_than_both_eye_lines_blocks(lib, mk, cases):
    assert _blocks(lib, mk, cases["ridge"]) == 1
    (l0, x0, y0), (l1, x1, y1) = cases["ridge"]
    assert lib.om_terrain_sight_blocks(mk, l1, x1, y1, l0, x0, y0) == 1   # symmetric


def test_R_005_10_plateau_sees_one_band_down_across_its_own_plateau(lib, mk, cases):
    _ridge_blocks(lib, mk, cases)
    assert _blocks(lib, mk, cases["plateau"]) == 0


def test_R_005_10_two_units_on_one_flat_band_see_each_other(lib, mk, cases):
    _ridge_blocks(lib, mk, cases)
    assert _blocks(lib, mk, cases["flat"]) == 0


def test_R_005_10_target_just_below_a_cliff_edge_is_seen_from_the_edge(lib, mk, cases):
    _ridge_blocks(lib, mk, cases)
    assert _blocks(lib, mk, cases["cliff"]) == 0


def test_R_005_10_open_map_blocks_nothing(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_map_set_canvas(w, CANVAS, CANVAS) == 0
    assert lib.om_terrain_present(w) == 0
    rng = random.Random(SEARCH_RNG_SEED)
    for _ in range(N_OPEN):
        x0, y0, x1, y1 = (rng.uniform(100, CANVAS - 100) for _ in range(4))
        assert lib.om_terrain_sight_blocks(w, rng.randrange(5), x0, y0, rng.randrange(5), x1, y1) == 0
    # positive control: the same call blocks once terrain exists (it is the ridge case below)
    assert lib.om_terrain_generate(w, SEED, CANVAS, CANVAS) == 0
    assert _blocks(lib, w, _search(lib, w)["ridge"]) == 1


_CHILD = r"""
import sys, json, ctypes
sys.path.insert(0, sys.argv[1])
import conftest as c
lib = c.load_lib()
w = lib.om_world_new(1, 1)
assert lib.om_map_set_canvas(w, 16000.0, 16000.0) == 0
assert lib.om_terrain_generate(w, 11, 16000.0, 16000.0) == 0
out = [lib.om_terrain_sight_blocks(w, l0, x0, y0, l1, x1, y1) for (l0, x0, y0), (l1, x1, y1) in json.loads(sys.argv[2])]
print(json.dumps(out))
"""


def test_R_005_10_two_processes_agree(lib, mk, cases):
    pairs = [cases[k] for k in ("ridge", "plateau", "flat", "cliff")]
    here = [_blocks(lib, mk, p) for p in pairs]
    runs = []
    for _ in range(2):
        res = subprocess.run([sys.executable, "-c", _CHILD, str(REPO_ROOT / "tests" / "csim"), json.dumps(pairs)],
                             capture_output=True, text=True, timeout=120)
        assert res.returncode == 0, res.stderr
        runs.append(json.loads(res.stdout))
    assert runs[0] == runs[1] == here
    # positive control: not a constant answer
    assert 1 in here and 0 in here
