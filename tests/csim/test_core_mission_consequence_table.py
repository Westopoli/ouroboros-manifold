"""S-078 consequence table: all 50 (archetype, band) cells.

Calls om_mission_apply_consequences on a fresh world for every pair and
compares mission-region field values against a Python reference computed
from simulation/config.py CONSEQUENCE_TABLES (ALG-59 names it as source).

Adjacent-player entries are verified on two player-owned neighbours (regions
1 and 3). Region 2 is enemy-owned and must stay unchanged. Region 0 is the
mission region.

Argtypes used here are all bound by _bind_e10 (called via _bind_generated at
lib-load time) or _configure_common; no conftest edit is required.
"""
import sys
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "simulation"))
from config import CONSEQUENCE_TABLES  # noqa: E402

from conftest import OMField, set_region, set_faction  # noqa: E402

# ---- index maps ----

ARCHETYPE_IDX = {
    "defensive_stand": 0, "siege_breaking": 1, "reconquest": 2, "assault": 3,
    "suppression": 4, "multi_front_defense": 5, "interception": 6,
    "evacuation": 7, "containment": 8, "counterinsurgency": 9,
}

BAND_ORDER = ("total_failure", "partial_failure", "partial_success",
              "strong_success", "total_success")
BAND_IDX = {n: i for i, n in enumerate(BAND_ORDER)}

FIELD_IDS = {
    "military": OMField.MILITARY, "economy": OMField.ECONOMY,
    "tension": OMField.TENSION, "population": OMField.POPULATION,
}

INIT_VAL = 50.0
CELLS = [(arch, band) for arch in ARCHETYPE_IDX for band in BAND_ORDER]

# ---- Python reference (mirrors outcome_resolver.py compute_delta / _get_target_regions) ----

def _delta(current, form, pct):
    if form == "deficit":
        return (100.0 - current) * pct / 100.0
    return current * pct / 100.0


def _py_mission_fields(arch_name, band_name):
    """Expected mission-region fields after mission/home/exposed entries (all map to mission)."""
    entries = CONSEQUENCE_TABLES.get(arch_name, {}).get(band_name, [])
    fields = {f: INIT_VAL for f in FIELD_IDS}
    for e in entries:
        if e["target"] in ("mission", "home", "exposed"):
            cur = fields[e["field"]]
            fields[e["field"]] = max(0.0, min(100.0, cur + _delta(cur, e["form"], e["pct"])))
    return fields


def _py_adj_fields(arch_name, band_name):
    """Expected neighbour fields after adjacent_player entries (each neighbour starts at INIT_VAL)."""
    entries = CONSEQUENCE_TABLES.get(arch_name, {}).get(band_name, [])
    fields = {f: INIT_VAL for f in FIELD_IDS}
    for e in entries:
        if e["target"] == "adjacent_player":
            cur = fields[e["field"]]
            fields[e["field"]] = max(0.0, min(100.0, cur + _delta(cur, e["form"], e["pct"])))
    return fields


# ---- world setup ----

_PLAYER_FACTION = 1
_ENEMY_FACTION = 2


def _setup(lib, world_factory):
    """4-region world: 0=mission, 1/3=player neighbours, 2=enemy neighbour."""
    w = world_factory(n_regions=4)
    set_faction(lib, w, _PLAYER_FACTION, 0)   # archetype 0 = PLAYER
    # set_region resets the region struct (incl. n_neighbors); set fields first,
    # then set neighbors, then set ownership (ownership also reset by set_region).
    for i in range(4):
        set_region(lib, w, i, military=INIT_VAL, economy=INIT_VAL,
                   tension=INIT_VAL, population=INIT_VAL)
    lib.om_set_neighbors(w, 0, 1)
    lib.om_set_neighbors(w, 0, 2)
    lib.om_set_neighbors(w, 0, 3)
    lib.om_region_set_owner(w, 1, _PLAYER_FACTION, 0)
    lib.om_region_set_owner(w, 2, _ENEMY_FACTION, 0)
    lib.om_region_set_owner(w, 3, _PLAYER_FACTION, 0)
    return w


# ---- parametrized test ----

@pytest.mark.parametrize("arch_name,band_name", CELLS,
                         ids=[f"{a}/{b}" for a, b in CELLS])
def test_consequence_table_cell(lib, world_factory, arch_name, band_name):
    """Every (archetype, band) cell applies correct field deltas to mission region
    and player-owned neighbours, matching config.py CONSEQUENCE_TABLES (ALG-59)."""
    w = _setup(lib, world_factory)
    lib.om_mission_apply_consequences(w, 0,
                                      ARCHETYPE_IDX[arch_name],
                                      BAND_IDX[band_name])

    # Mission region
    exp_ms = _py_mission_fields(arch_name, band_name)
    for fname, fid in FIELD_IDS.items():
        got = lib.om_region_field(w, 0, fid)
        assert got == pytest.approx(exp_ms[fname], abs=1e-4), (
            f"{arch_name}/{band_name}: mission {fname}: "
            f"expected {exp_ms[fname]:.6f} got {got:.6f}"
        )

    # Player-owned neighbours (1 and 3); enemy neighbour (2) not checked here
    exp_adj = _py_adj_fields(arch_name, band_name)
    for nb in (1, 3):
        for fname, fid in FIELD_IDS.items():
            got = lib.om_region_field(w, nb, fid)
            assert got == pytest.approx(exp_adj[fname], abs=1e-4), (
                f"{arch_name}/{band_name}: neighbour {nb} {fname}: "
                f"expected {exp_adj[fname]:.6f} got {got:.6f}"
            )
