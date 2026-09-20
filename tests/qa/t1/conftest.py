"""T1 QA fixtures for the desync detector (tests/qa/t1/).

Reuses the fenced ABI mirror in tests/csim/conftest.py -- the same ctypes
struct layouts, the same session-scoped `lib`/`dbg` build-and-load fixtures,
and the same E-05 fixture helpers -- instead of maintaining a second copy that
could silently drift from csrc/ouroboros_sim.h. Loaded under a private module
name (not the bare "conftest" pytest gives its own file) so this directory's
tests collect cleanly whether run alone or alongside tests/csim/ in the same
pytest session.

Does not edit tests/csim/conftest.py; only reads and re-exposes it.
"""
import importlib.util
import pathlib
import sys

import pytest

_CSIM_CONFTEST = pathlib.Path(__file__).resolve().parents[2] / "csim" / "conftest.py"
_spec = importlib.util.spec_from_file_location("_qa_t1_csim_conftest", _CSIM_CONFTEST)
_csim = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _csim
_spec.loader.exec_module(_csim)

# ---- fixtures (already @pytest.fixture-marked in tests/csim/conftest.py;
# pytest registers them by the name they appear under in this module) ----
lib = _csim.lib
dbg = _csim.dbg
world_factory = _csim.world_factory
dbg_world_factory = _csim.dbg_world_factory

# ---- ABI mirrors and helpers this suite's tests need ----
OMTier = _csim.OMTier
OMField = _csim.OMField
OmTraceRow = _csim.OmTraceRow
OMArchetype = _csim.OMArchetype
OMStance = _csim.OMStance
OMEdge = _csim.OMEdge
OMAction = _csim.OMAction
OMMode = _csim.OMMode
OMFeature = _csim.OMFeature
set_region = _csim.set_region
isolate_agents = _csim.isolate_agents
set_faction = _csim.set_faction
set_stance = _csim.set_stance
set_tech_multipliers = _csim.set_tech_multipliers
set_owner = _csim.set_owner
set_edge = _csim.set_edge
force_draws = _csim.force_draws
