"""E-03 storage wiring (freeze/F2b): struct om_world carries the generation
config and result fields the om_gen_set_* setters, om_world_generate, and
the report accessors (csrc/ouroboros_sim.h ~line 690) need, and a fresh
world reports the documented defaults (E-03 R-021-01, R-021-04, R-021-08,
R-022-05; algorithms.md ALG-30/ALG-31).

No public om_gen_* reader exists (worldgen.c owns them), so the fields are
read through the debug-build accessor om_debug_gen_config (csrc/om_internal.h,
csrc/region.c). OMDebugGenConfigRow mirrors om_debug_gen_config_row field for
field. The setter round-trip test stays red until card B4 replaces the
worldgen.c STUB for om_gen_set_region_range with one that stores its inputs.
"""
import ctypes

from conftest import OMTemplate


class OMDebugGenConfigRow(ctypes.Structure):
    _fields_ = [
        ("region_min", ctypes.c_uint32),
        ("region_max", ctypes.c_uint32),
        ("faction_count", ctypes.c_uint32),
        ("extra_edge_ratio", ctypes.c_double),
        ("player_pref", ctypes.c_int32),
        ("preference_weight", ctypes.c_double),
        ("extra_edges_on", ctypes.c_int32),
        ("home_range", (ctypes.c_double * 4) * 3),
        ("generated", ctypes.c_int32),
        ("edge_count", ctypes.c_uint32),
    ]


def read_gen_config(dbg, w):
    dbg.om_debug_gen_config.argtypes = [ctypes.c_void_p, ctypes.POINTER(OMDebugGenConfigRow)]
    dbg.om_debug_gen_config.restype = None
    row = OMDebugGenConfigRow()
    dbg.om_debug_gen_config(w, ctypes.byref(row))
    return row


# Conqueror, Fortifier, Opportunist rows; mil_lo, mil_hi, eco_lo, eco_hi (R-022-05).
HOME_RANGE_DEFAULTS = [
    [50.0, 65.0, 40.0, 55.0],
    [40.0, 50.0, 50.0, 65.0],
    [45.0, 55.0, 45.0, 55.0],
]


def test_R_021_01_fresh_world_stores_region_range_and_faction_count_defaults(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    row = read_gen_config(dbg, w)
    assert (row.region_min, row.region_max) == (60, 110), \
        "a fresh world's region count range must default to [60, 110] (R-021-01, ALG-31 WORLD_REGION_COUNT_RANGE)"
    assert row.faction_count == 15, \
        "a fresh world's faction count must default to 15 (R-021-01, ALG-31 WORLD_FACTIONS_PER_GAME)"


def test_R_021_04_fresh_world_stores_player_preference_defaults(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    row = read_gen_config(dbg, w)
    assert row.player_pref == OMTemplate.NONE, \
        "a fresh world's player template preference must default to OM_TMPL_NONE (R-021-04)"
    assert row.preference_weight == 0.50, \
        "a fresh world's preference weight must default to 0.50 (R-021-04, ALG-31 WORLD_PLAYER_PREFERENCE_WEIGHT)"


def test_R_021_08_fresh_world_stores_extra_edge_defaults(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    row = read_gen_config(dbg, w)
    assert row.extra_edge_ratio == 0.12, \
        "a fresh world's extra-edge ratio must default to 0.12 (R-021-08, ALG-31 WORLD_EXTRA_EDGE_RATIO)"
    assert row.extra_edges_on == 1, \
        "a fresh world's extra-edge step must default to enabled (om_gen_set_extra_edges_enabled default on)"


def test_R_022_05_fresh_world_stores_archetype_home_range_defaults(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    row = read_gen_config(dbg, w)
    got = [list(row.home_range[i]) for i in range(3)]
    assert got == HOME_RANGE_DEFAULTS, \
        "a fresh world's per-archetype home ranges must default to the R-022-05 numbers (Conqueror 50-65/40-55, Fortifier 40-50/50-65, Opportunist 45-55/45-55)"


def test_R_021_10_fresh_world_reports_not_generated_and_no_edges(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    row = read_gen_config(dbg, w)
    assert row.generated == 0, "a fresh world must report generated == 0 before om_world_generate"
    assert row.edge_count == 0, "a fresh world must report edge_count == 0 before om_world_generate"


def test_R_021_01_region_range_setter_is_stored_without_generating(dbg, dbg_world_factory):
    # Bound here rather than via conftest._bind_e03, which also binds E-03
    # symbols worldgen.c does not define until card B4 lands.
    dbg.om_gen_set_region_range.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
    dbg.om_gen_set_region_range.restype = None
    w = dbg_world_factory(n_regions=1)
    dbg.om_gen_set_region_range(w, 70, 90)
    row = read_gen_config(dbg, w)
    assert (row.region_min, row.region_max) == (70, 90), \
        "om_gen_set_region_range(w, 70, 90) must be stored in the world's generation config (R-021-01)"
    assert row.generated == 0, "setting a generation range must not generate the world"
