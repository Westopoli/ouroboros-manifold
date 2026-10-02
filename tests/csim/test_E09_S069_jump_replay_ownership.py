"""G-C3 (Architect rulings round 2, A48 item 13): the sim owns the jump replay data.

R-069-05 (map keyframes, "every ownership change has a keyframe") and ALG-45 / R-056-03
(an ownership snapshot every OM_OWNERSHIP_TIMELINE_STRIDE = 2 ticks, k = 0 the state
before the jump). Contract: docs/architecture.md "chronicle frame" (ownership and
keyframes fields); accessors om_time_jump_ownership_snapshot_count,
om_time_jump_get_ownership_snapshot, om_chronicle_keyframe_count,
om_chronicle_get_keyframe in csrc/ouroboros_sim.h.

Red on main: the accessors are not exported (symbol missing). Each test has a
positive control (the control_ functions) so a stub that returns 0 or constant
data cannot pass.
"""
import ctypes

from conftest import set_owner
from test_E08_S056_decades_pass_while_i_am_gone import OmTimeJumpReport

STRIDE = 2
SENTINEL = 0x7ABCDEF1


def _owners(lib, w, n):
    return [lib.om_region_owner(w, i) for i in range(n)]


def _snapshot(lib, w, k, n, cap=None):
    cap = n if cap is None else cap
    buf = (ctypes.c_int32 * max(cap, 1))(*([SENTINEL] * max(cap, 1)))
    ret = lib.om_time_jump_get_ownership_snapshot(w, k, buf, cap)
    return ret, list(buf)[:n]


def _jump(lib, w, ticks):
    report = OmTimeJumpReport()
    assert lib.om_time_jump_run(w, ticks, ctypes.byref(report)) == 0
    return report


def test_R_056_03_snapshot_count_matches_report(lib, world_factory):
    """Snapshot count is jump_ticks // STRIDE + 1 and equals report.n_snapshots."""
    w = world_factory(n_regions=6)
    assert lib.om_time_jump_ownership_snapshot_count(w) == 0  # control: nothing before a jump
    for ticks in (30, 20, 25):
        report = _jump(lib, w, ticks)
        assert lib.om_time_jump_ownership_snapshot_count(w) == ticks // STRIDE + 1
        assert lib.om_time_jump_ownership_snapshot_count(w) == report.n_snapshots


def test_R_056_03_snapshot_zero_is_pre_jump_and_last_is_end(lib, world_factory):
    """Snapshot 0 is the owner of each region before the jump's first tick; with an
    even length the last snapshot (k = n/2) is the owner at the end tick."""
    n = 6
    w = world_factory(n_regions=n)
    for i, f in enumerate([0, 1, -1, 0, 1, -1]):
        set_owner(lib, w, i, f)
    before = _owners(lib, w, n)
    assert before != [-1] * n and len(set(before)) > 1  # control: a non-trivial pattern
    _jump(lib, w, 30)
    after = _owners(lib, w, n)
    count = lib.om_time_jump_ownership_snapshot_count(w)
    ret0, snap0 = _snapshot(lib, w, 0, n)
    retl, snapl = _snapshot(lib, w, count - 1, n)
    assert ret0 == n and retl == n
    assert snap0 == before
    assert snapl == after


def test_R_056_03_every_snapshot_is_full_and_valid(lib, world_factory):
    n = 6
    w = world_factory(n_regions=n)
    for i, f in enumerate([0, 1, -1, 0, 1, -1]):
        set_owner(lib, w, i, f)
    _jump(lib, w, 40)
    nf = lib.om_faction_count(w)
    for k in range(lib.om_time_jump_ownership_snapshot_count(w)):
        ret, snap = _snapshot(lib, w, k, n)
        assert ret == n
        assert all(SENTINEL != v and -1 <= v < max(nf, 2) for v in snap), (k, snap)


def test_R_056_03_snapshot_getter_refusals_write_nothing(lib, world_factory):
    """k out of range and cap < n_regions return 0 and leave the buffer untouched;
    the in-range call with a big enough cap is the control that the buffer is written."""
    n = 6
    w = world_factory(n_regions=n)
    _jump(lib, w, 20)
    count = lib.om_time_jump_ownership_snapshot_count(w)
    ret, snap = _snapshot(lib, w, count, n)
    assert ret == 0 and snap == [SENTINEL] * n
    ret, snap = _snapshot(lib, w, 0, n, cap=n - 1)
    assert ret == 0 and snap[: n - 1] == [SENTINEL] * (n - 1)
    ret, snap = _snapshot(lib, w, 0, n)  # control
    assert ret == n and SENTINEL not in snap


def test_R_056_03_second_jump_replaces_the_timeline(lib, world_factory):
    """The accessors describe the last completed jump: its snapshot 0 is the state
    the first jump ended in."""
    n = 6
    w = world_factory(n_regions=n)
    for i, f in enumerate([0, 1, -1, 0, 1, -1]):
        set_owner(lib, w, i, f)
    _jump(lib, w, 20)
    mid = _owners(lib, w, n)
    _jump(lib, w, 20)
    _, snap0 = _snapshot(lib, w, 0, n)
    assert snap0 == mid
    assert lib.om_time_jump_ownership_snapshot_count(w) == 20 // STRIDE + 1


def test_R_069_05_keyframes_are_exposed_in_stored_order(lib, world_factory):
    """A mock entry starting at tick 10 and an ownership change at tick 35 give
    keyframes [10, 35]; calling generate again does not double them."""
    w = world_factory(n_regions=4)
    assert lib.om_chronicle_keyframe_count(w) == 0  # control: none before generate
    lib.om_chronicle_add_mock_entry(w, entry_id=1, start_tick=10, end_tick=20)
    lib.om_chronicle_add_ownership_change_event(w, region_idx=2, tick=35)
    for _ in range(2):
        lib.om_chronicle_generate_map_keyframes(w)
        assert lib.om_chronicle_keyframe_count(w) == 2
        got = []
        for i in range(2):
            t = ctypes.c_uint64(SENTINEL)
            assert lib.om_chronicle_get_keyframe(w, i, ctypes.byref(t)) == 1
            got.append(t.value)
        assert got == [10, 35]


def test_R_069_05_keyframe_getter_out_of_range_writes_nothing(lib, world_factory):
    w = world_factory(n_regions=4)
    lib.om_chronicle_add_ownership_change_event(w, region_idx=1, tick=7)
    lib.om_chronicle_generate_map_keyframes(w)
    n = lib.om_chronicle_keyframe_count(w)
    assert n == 1
    t = ctypes.c_uint64(SENTINEL)
    assert lib.om_chronicle_get_keyframe(w, n, ctypes.byref(t)) == 0
    assert t.value == SENTINEL
    assert lib.om_chronicle_get_keyframe(w, 0, ctypes.byref(t)) == 1  # control
    assert t.value == 7


def test_A59_odd_jump_length_adds_no_final_snapshot(lib, world_factory):
    """A59: an odd length keeps n // STRIDE + 1 snapshots (every 2 ticks from the
    start); no snapshot is added for the end tick. Control: the even length 24
    holds the same 13, so 25 gains nothing over 24 (a final-snapshot rule would give 14)."""
    n = 6
    w = world_factory(n_regions=n)
    for ticks, want in ((25, 13), (31, 16), (24, 13)):
        report = _jump(lib, w, ticks)
        count = lib.om_time_jump_ownership_snapshot_count(w)
        assert count == want == report.n_snapshots, (ticks, count)
        ret, snap = _snapshot(lib, w, count, n)  # one past the last
        assert ret == 0 and snap == [SENTINEL] * n
        assert _snapshot(lib, w, count - 1, n)[0] == n  # control: the last real one


def _keyframes(lib, w):
    out = []
    for i in range(lib.om_chronicle_keyframe_count(w)):
        t = ctypes.c_uint64(SENTINEL)
        assert lib.om_chronicle_get_keyframe(w, i, ctypes.byref(t)) == 1
        out.append(t.value)
    return out


def test_A59_keyframes_sorted_ascending_without_duplicates(lib, world_factory):
    """Mock entries at 50, 10, 35 and ownership changes at 35 (equal to an entry
    tick), 10 and 5 give [5, 10, 35, 50]. Today's list is [50, 10, 35, 35, 10, 5]."""
    w = world_factory(n_regions=4)
    for eid, start in ((1, 50), (2, 10), (3, 35)):
        lib.om_chronicle_add_mock_entry(w, entry_id=eid, start_tick=start, end_tick=start + 5)
    for region, tick in ((0, 35), (1, 10), (2, 5)):
        lib.om_chronicle_add_ownership_change_event(w, region_idx=region, tick=tick)
    lib.om_chronicle_generate_map_keyframes(w)
    assert _keyframes(lib, w) == [5, 10, 35, 50]
    assert lib.om_chronicle_keyframe_count(w) == 4
    # control: lookups still see every distinct tick after the sort and dedup
    for t in (5, 10, 35, 50):
        assert lib.om_chronicle_has_keyframe_at_tick(w, t) == 1
    assert lib.om_chronicle_has_keyframe_at_tick(w, 20) == 0


def test_A59_keyframes_cleared_when_a_jump_starts(lib, world_factory):
    """Keyframes are per jump: a jump clears the list, and the next generate
    returns a sorted unique list again (not the first jump's ticks piled on)."""
    w = world_factory(n_regions=6)
    lib.om_chronicle_add_mock_entry(w, entry_id=1, start_tick=900001, end_tick=900005)
    lib.om_chronicle_generate_map_keyframes(w)
    assert _keyframes(lib, w) == [900001]  # control: the list is populated before the jump
    _jump(lib, w, 20)
    assert lib.om_chronicle_keyframe_count(w) == 0
    assert lib.om_chronicle_has_keyframe_at_tick(w, 900001) == 0
    lib.om_chronicle_generate_map_keyframes(w)
    kfs = _keyframes(lib, w)
    assert kfs == sorted(set(kfs)), kfs
    _jump(lib, w, 20)
    assert lib.om_chronicle_keyframe_count(w) == 0
    lib.om_chronicle_generate_map_keyframes(w)
    kfs = _keyframes(lib, w)
    assert kfs == sorted(set(kfs)), kfs
