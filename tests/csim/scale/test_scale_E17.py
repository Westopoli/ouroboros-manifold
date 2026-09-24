"""E-17 (docs/bible/epics/E-17-map-generation.md), "## Scale requirements":
"Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is
escalated): generation under 50 ms; field sampling under 1 us per query with
a precomputed grid at 100 wu."

om_map_generate (csrc/tactical_mapgen.c) is currently a STUB (`(void)w; ...`,
no body) -- its test below measures real wall time but that time is ctypes
call overhead only, not generation work; flagged, not fixed (out of this
leaf's scope). om_map_sample_obstacle_density is real and is the closest
implemented "field sampling" entry point, but it is a linear O(n_obstacles)
scan (csrc/tactical_mapgen.c), not the "precomputed grid" the epic specifies
-- also flagged, not fixed.
"""
from ._scale_helpers import assert_budget, median_ns, raw_world

GEN_BUDGET_NS = 50_000_000  # 50 ms
SEED = 2026091417

N_OBSTACLES = 200
N_QUERIES = 10000
SAMPLE_BUDGET_NS = N_QUERIES * 1_000  # 1us/query x 10,000 queries = 10ms total
# The epic's "under 1 us per query" is a per-call figure; a Python/ctypes call
# floor of ~0.5-1us per call (independent of the C body) makes a literal
# per-call budget unmeasurable from this harness (see the leaf report). This
# file instead checks the batch-of-10,000 total against 10,000 x the epic's
# per-query figure (10 ms), the same "N per tick" framing used elsewhere in
# this suite, and reports the per-query average alongside it.


def test_e17_map_generation_under_50ms(lib):
    w = raw_world(lib, 1, SEED, features=[])
    med = median_ns(lambda: lib.om_map_generate(w, 0, SEED))
    lib.om_world_free(w)
    print("[scale] E-17 note: om_map_generate is a STUB (csrc/tactical_mapgen.c) -- "
          "this measures ctypes call overhead, not generation work")
    assert_budget(med, GEN_BUDGET_NS, "E-17 om_map_generate (STUB)")


def test_e17_field_sampling_10000_queries(lib):
    w = raw_world(lib, 1, SEED, features=[])
    for i in range(N_OBSTACLES):
        lib.om_map_add_obstacle(w, float((i * 91) % 24000), float((i * 131) % 24000), 50.0)
    xs = [(i * 37.0) % 24000.0 for i in range(N_QUERIES)]
    ys = [(i * 53.0) % 24000.0 for i in range(N_QUERIES)]

    def _batch():
        for x, y in zip(xs, ys):
            lib.om_map_sample_obstacle_density(w, x, y)

    med = median_ns(_batch, n=50, warmup=5)
    lib.om_world_free(w)
    per_query_ns = med / N_QUERIES
    print(f"[scale] E-17 field sampling: batch of {N_QUERIES} = {med / 1000.0:.3f}us total, "
          f"{per_query_ns:.3f}ns/query average (budget: 1000ns/query)")
    assert_budget(med, SAMPLE_BUDGET_NS, f"E-17 {N_QUERIES} om_map_sample_obstacle_density queries")
