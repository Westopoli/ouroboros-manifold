"""E-09 (docs/bible/epics/E-09-chronicle.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
escalated): distill and assemble 2,000 events in under 200 ms; the scroll
panel renders 10 entries at 60 fps while the map animates."

Only the distill/assemble half is measurable through the C sim ABI; the
scroll-panel frame-rate half is a client (Godot) rendering claim, out of
scope for tests/csim (see the leaf report's out-of-scope list for the
epics excluded entirely on this basis).
"""
import pytest

from ._scale_helpers import assert_budget, median_ns_with_setup, raw_world

N_REGIONS = 60
N_EVENTS = 2000
CONTROL_N_EVENTS = 200000
BUDGET_NS = 200_000_000  # 200 ms
SEED = 2026091409


def _seed_events(lib, w, n_events, seed):
    for i in range(n_events):
        region = i % N_REGIONS
        score = 10.0 + (i * 37 + seed) % 90
        lib.om_chronicle_add_event(w, region, float(score))


def test_e09_distill_and_assemble_2000_events(lib):
    w = raw_world(lib, N_REGIONS, SEED, features=[])
    med = median_ns_with_setup(
        lambda: _seed_events(lib, w, N_EVENTS, SEED),
        lambda: lib.om_chronicle_distill_and_assemble(w),
        n=100, warmup=5,
    )
    lib.om_world_free(w)
    assert_budget(med, BUDGET_NS, f"E-09 distill_and_assemble({N_EVENTS} events)")


def test_e09_selection_control_note_bounded_by_candidate_cap(lib):
    """Not a pass/fail control: om_chronicle_distill_and_assemble measured
    ~225-240us flat from 2,000 through 200,000 (100x N) seeded events in a
    dry run -- chron_run_selection caps its candidate buffer at
    CHRON_MAX_CANDIDATES (csrc/chronicle.c), so cost is bounded by the cap,
    not by N, once N exceeds it. No buildable N trips a budget/100 control
    for this op; recorded per the brief's "skip the control with a stated
    reason" allowance."""
    w = raw_world(lib, N_REGIONS, SEED, features=[])
    med = median_ns_with_setup(
        lambda: _seed_events(lib, w, CONTROL_N_EVENTS, SEED),
        lambda: lib.om_chronicle_distill_and_assemble(w),
        n=20, warmup=2,
    )
    lib.om_world_free(w)
    print(f"[scale-control-skip] E-09: {CONTROL_N_EVENTS} events, om_chronicle_distill_and_assemble "
          f"raw_median={med / 1000.0:.3f}us -- control not applicable, see docstring")
    pytest.skip(
        f"om_chronicle_distill_and_assemble is bounded by CHRON_MAX_CANDIDATES, not N "
        f"(measured {med / 1000.0:.3f}us at 100x N={CONTROL_N_EVENTS}, still far under budget/100); "
        "no buildable N trips this control for this op"
    )
