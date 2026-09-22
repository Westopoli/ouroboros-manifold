"""F5 window control for csrc/save.c (E-16 by the two-day-push brief's own
per-module numbering; the epic file is E-16-client-camera-hud-and-world-view.md
S-111, wave 2 card T2c).

Rule (docs/bible/epics/E-16-client-camera-hud-and-world-view.md R-111-02):
"the world ... [is] restored such that the next jump is deterministic."
tests/csim/test_E16_S111_saving.py's own live control
(test_control_R_111_02_om_bug_save_skips_rng_state_trips_the_detector)
already covers the RNG-stream leg of this rule at id 1600; this control
covers a different leg with a different concrete number: the tick counter.
om_world_set_tick(w, 500) moves a fresh world directly to tick 500 with no
other side effect (the header's own contract: "The next om_world_step()
then returns tick + 1"). Saved and loaded into a fresh world (which starts
at tick 0), the next step on the loaded world must also return 501.

PLANT: under OM_BUG_SAVE_SKIPS_TICK, the tick counter is never written into
(or restored from) the save buffer, so the loaded world's next step returns
1 (as if it had never left tick 0), not 501. Per the precedent set by
OM_BUG_SAVE_SKIPS_RNG_STATE (test_E16_S111_saving.py), the bug is injected
on the SOURCE world and is expected to be implemented inside
om_save_state_write (which takes that world), not om_load_state_read.
"""
import ctypes

from conftest import OMBugSave


def test_control_save_skips_tick_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_debug_inject(w, OMBugSave.SAVE_SKIPS_TICK)

    dbg.om_world_set_tick(w, 500)

    size = dbg.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    dbg.om_save_state_write(w, buf, size)

    w_loaded = dbg_world_factory(n_regions=1)
    dbg.om_load_state_read(w_loaded, buf, size)

    next_tick = dbg.om_world_step(w_loaded)

    assert next_tick == 1, (
        "OM_BUG_SAVE_SKIPS_TICK injected but the loaded world's next step "
        "still correctly returned 501 (tick 500 restored) instead of 1 "
        "(as if the world had never left tick 0) -- the detector did not trip"
    )
