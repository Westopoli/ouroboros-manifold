"""C2 / R-029 border friction (E-05, ALG border friction) under the adjacency-walk rewrite of
om_step_friction: the output must not change by one bit at small n. The goldens below were captured
on the O(n^2) edge-scan implementation (origin/main + push/T1-b7-td, before HDR5): a 60-region range
(raised to the feasible 69 by generation), seed 7, features 0-7, 150 ticks.

Two goldens: the world state checksum after 150 ticks (the same om_world_get_state_checksum
scripts/specfactory/checksum_trace.py prints) and a sha256 over every om_friction record of every
tick, which names friction directly instead of through the whole state.
"""
import ctypes
import hashlib

from conftest import OmFriction, gen_set_region_range, generate

SEED = 7
TICKS = 150
GOLDEN_FINAL_CHECKSUM = 5255701497181831602
GOLDEN_FRICTION_SHA256 = "315b11b5a92558359133a84506de999268cf4c5c09f703e5ee28cacb18db7bf9"
GOLDEN_FRICTION_RECORDS = 4252


def _friction_reader(lib):
    """A private function pointer to om_tick_friction typed with this module's OmFriction. The shared lib attribute can carry argtypes bound to another copy of the class (tests/csim/scale/_scale_helpers.py execs conftest.py under a second module name, and an OM_SCALE=1 run binds first), so it is never used here."""
    proto = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(OmFriction), ctypes.c_uint32)
    return proto(("om_tick_friction", lib))


def _run(lib, seed):
    read = _friction_reader(lib)
    w = lib.om_world_new(0, seed)
    assert w
    for feat in range(8):
        lib.om_world_set_feature(w, feat, 1)
    gen_set_region_range(lib, w, 60, 60)
    assert generate(lib, w) == 1
    h = hashlib.sha256()
    n = 0
    for _ in range(TICKS):
        lib.om_world_step(w)
        buf = (OmFriction * 256)()
        count = read(w, buf, 256)
        n += count
        for r in buf[:count]:
            h.update(bytes(r))
    checksum = lib.om_world_get_state_checksum(w)
    lib.om_world_free(w)
    return checksum, h.hexdigest(), n


def test_control_C2_the_trace_discriminates_and_friction_is_exercised(lib):
    """Control: another seed gives another checksum and hash, and the golden run really emits friction records, so equality below is not vacuous."""
    c_a, h_a, n_a = _run(lib, SEED)
    c_b, h_b, _ = _run(lib, SEED + 1)
    assert n_a > 0
    assert c_a != c_b and h_a != h_b


def test_R_029_friction_state_checksum_is_unchanged_by_the_adjacency_walk(lib):
    """Given the golden seed at 60 regions, When 150 ticks run, Then the final state checksum equals the pre-rewrite value."""
    checksum, _, _ = _run(lib, SEED)
    assert checksum == GOLDEN_FINAL_CHECKSUM


def test_R_029_friction_records_are_unchanged_by_the_adjacency_walk(lib):
    """Given the golden seed, When 150 ticks run, Then the friction records (count and bytes, in order) equal the pre-rewrite run."""
    _, digest, n = _run(lib, SEED)
    assert n == GOLDEN_FRICTION_RECORDS
    assert digest == GOLDEN_FRICTION_SHA256
