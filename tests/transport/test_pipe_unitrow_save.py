"""VG-CONTRACT-unitrow-save, positive control (holding branch push/vg-contract-unitrow-tests; not landed by itself).

Test copied verbatim from tests/transport/test_pipe_u_observable.py (VG-U-PIPE-TESTS), which moved it here:
test_macro_state_survives_a_save_and_load. It proves R-064-04: "a save and load leaves the next time jump or step as if
never saved (determinism includes every saved section)": after a save and load the next 100 tactical steps give the same
full frame as 100 steps with no load. See FINDING-u-pipe-events-save-load.

Positive control of VG-CONTRACT-unitrow-save: red on main for the reason that load re-emits kills of rows dead before the
save (kill_logged not in OM_UNIT_ROW_FIELDS: the unit row fields kill_logged, tier and fired_tick are not saved or loaded).
Red line: `assert frame_b == frame_a` (the frame after the load carries kill events of units already dead at the save).
Green once the contract piece saves and loads those unit row fields.

The helpers and constants below are copied unchanged from test_pipe_u_observable.py, only those this test needs.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def cmd(name, **kw):
    return {"type": "cmd", "name": name, **kw}


def set_seed(seed, **kw):
    return cmd("set_seed", seed=seed, n_regions=80, features=FEATURES, **kw)


def run(cmds, timeout=400):
    """Send the commands then quit; return every frame after hello."""
    script = b""
    for c in cmds + [QUIT]:
        body = json.dumps(c).encode()
        script += len(body).to_bytes(4, "big") + body
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def of_type(frames, kind):
    return [f for f in frames if f.get("type") == kind]


def last_tactical(frames):
    return of_type(frames, "tactical")[-1]


def start(**kw):
    return cmd("mission_start", faction=0, **kw)


BEGIN = cmd("mission_begin")


def tstep(n, full=False):
    return cmd("tactical_step", n=n, full=full) if full else cmd("tactical_step", n=n)


def checksum_sections(frames):
    return [f["sections"] for f in of_type(frames, "net_ack") if f.get("name") == "net_checksum"]


def save_round_trip(prefix, steps_after, saved_bytes=None):
    """prefix commands, net_checksum, save; then (A) steps_after steps without a load vs (B) a load then the same steps.
    Returns (sections at save, sections right after the load, frame A, frame B, sections after A's steps). When
    `saved_bytes` is a list, the bytes of the .omsave written by the save are appended to it."""
    with tempfile.TemporaryDirectory() as d:
        slot = str(Path(d) / "mid.omsave")
        pre = prefix + [cmd("net_checksum"), cmd("save", path=slot)]
        a = run(pre + [tstep(steps_after, True), cmd("net_checksum")])
        b = run(pre + [cmd("load", path=slot), cmd("net_checksum"), tstep(steps_after, True)])
        if saved_bytes is not None:
            saved_bytes.append(Path(slot).read_bytes())
    at_save = checksum_sections(a)[0]
    return at_save, checksum_sections(b)[1], last_tactical(a), last_tactical(b), checksum_sections(a)[1]


MACRO_SECTION, FOG_SECTION = 7, 6  # tests/net/driver.py SECTIONS order: regions, factions, rng, units, movement, mission, fog, macro, support_map


# Seed 5, all 32 player units ordered to the objective node (8000, 8000): by 3000 steps the bus runner has set the flags
# "objective_N_contested" (csrc/enemy_macro.c om_macro_update_bus_runner, snprintf at :748 and :797) and the saved bytes hold
# those names; 4000 steps leaves a margin. Coverage floor, not a rule value.
MACRO_BUS_STEPS = 4000


def seed5_player_ids():
    return [u["id"] for u in last_tactical(run([set_seed(5), start(), BEGIN]))["units"] if u["faction"] == 0]


def test_macro_state_survives_a_save_and_load():
    """R-064-04: a save and load leaves the next time jump or step as if never saved (determinism includes every saved
    section). The enemy macro writes and reads its force table and its bus flags through msv_* / msr_* (csrc/enemy_macro.c
    macro_state_put and its reader). The bus runner sets "objective_N_contested" flags in play, so msv_str/msr_str and
    msv_u8/msr_u8 run on non-empty names in this state (premise asserted below on the saved bytes); the fog side has no such
    string (FINDING-save-fog-str).

    What shows: seed 5, the player force ordered to node (8000, 8000), MACRO_BUS_STEPS tactical steps, net_checksum, save
    (the .omsave holds b"objective_" and b"_contested"); then 100 steps with no load (A) against load then 100 steps (B): the
    `macro` section hash of net_checksum right after the load equals the one at save and differs from the one 100 steps on (the
    state is live), and the 100-step full tactical frames of A and B are equal key for key.

    Positive controls (scratch breaks, each reverted and rebuilt; the earlier 300-step prefix left msr_u8 broken and the test
    green, which is why the prefix changed):
      u8     csrc/enemy_macro.c:1346 `msr_u8` `(uint32_t)msr_uint(sr, sizeof(uint8_t))` XORed with 1u. Red:
             `assert after_load[MACRO_SECTION] == at_save[MACRO_SECTION]` (CONTROL-MACRO-U8-RESULT).
      str    csrc/enemy_macro.c:1363 in msr_str `dst[i] = (char)msr_u8(sr);` changed to
             `dst[i] = (char)msr_u8(sr) ^ (char)(i == 0);` (the first name byte flips; a break that skips the read desyncs the
             reader, the load fails and the in-process world is left as it was, so it stays green). Red: the same line
             (CONTROL-MACRO-STR-RESULT).
      f64    csrc/enemy_macro.c:1354 in msr_f64 `return v;` changed to `return 0.0;`. Red: the same line
             (CONTROL-MACRO-F64-RESULT)."""
    mine = seed5_player_ids()
    prefix = [set_seed(5), start(), BEGIN, cmd("command", verb="move", units=mine, x=8000.0, y=8000.0), tstep(MACRO_BUS_STEPS)]
    saved = []
    at_save, after_load, frame_a, frame_b, later = save_round_trip(prefix, 100, saved)
    assert b"objective_" in saved[0] and b"_contested" in saved[0]  # premise: a bus flag name is in the saved state
    assert at_save[MACRO_SECTION] != later[MACRO_SECTION]  # the section is live state, not a constant
    assert after_load[MACRO_SECTION] == at_save[MACRO_SECTION]
    assert frame_b == frame_a
