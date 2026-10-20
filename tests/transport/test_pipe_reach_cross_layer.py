# Rule pins: R-082-01@7030c1, R-164-01@511d57
"""VG-T-REACH-TESTS (Lane T, T1): the bible's reach table, proved through the game.

PATH: PIPE. Every scene below is driven the way the client drives the game, over the frames of
docs/architecture.md and nothing else: `set_seed`, `mission_start`, `mission_begin`, `command`
(`set_layer`, `attack_move`) and `tactical_step`. No csim setter is called, so a game that never sets a
unit type's reach stays red here whatever the C function does when it is handed a value by hand
(docs/northstar/plans/drift_audits/2026-10-19-positioning-green-tests.md, D1 and test N1).

Rule proved (R-164-01, E-01), word for word: "Given a unit type, When its reach is read, Then it names the layer
offsets it can fire at: its own layer, and how many layers up and how many down: Line its own layer, Raider one
layer either way, Interceptor two up and one down, Siege two down [Q-008-03: the range and damage at each offset]."
Names: Line = Vanguard, Warden; Siege = Bombard, Bastion (E-11 R-082-01 table); Raider and Interceptor are Strike
types named in the rule. Westley 2026-10-19: "a better positioned force WILL succeed, that's the intent of the game".

Cases (offset = target layer minus attacker layer; "+2" is a target two layers above the attacker):
  fires:       Raider +1, Raider -1, Interceptor +2, Interceptor -1, Bombard -2
  does not:    Raider +2, Interceptor -2, Bombard +1
  controls:    Vanguard +1 (Line reach 0, green today); Raider on the target's own layer (green today)
A case that fires is red today for ONE reason, the one the rule names: every type reads reach (0, 0) in the shipped
game, so nothing fires across a layer. The "does not" cases and the controls are green today and must stay green.

Scene (premises dumped by running it; seed and distances are the writer's harness numbers, ledger row
DRAFT-t1-steps): seed 18, 80 regions, features 0..7 (space era). That mission is archetype 0, 28 player units against
31 enemy units, the forces 15,800 wu apart, every unit on layer 0, every enemy unit idle until the macro moves it. The
player's first unit of the attacker's type is sent to layer 2 by `command set_layer`; every enemy unit present at the
start is sent to layer 2 + offset by `command set_layer` (the pipe takes the order for any unit id: the harness
rearranges the enemy, it asserts nothing about the enemy's own orders). The attacker is then sent by `command
attack_move` at the nearest enemy, re-aimed every 50 ticks, to a point STANDOFF wu short of it (100 wu; 40 wu for the
Bombard, whose sensor 300 reaches an enemy two layers away only to 60 wu: cross-layer vision is 0.5 one layer, 0.2 two
layers, 0 beyond, tactical_move.c:376). `tactical_step` runs in chunks of 10 ticks. The scene ends when the attacker
fires at an enemy, when it dies, or N = 120 ticks after it has stopped within standoff + 15 wu of the nearest enemy.
Evidence: the frame's `events` list (`[0, shooter, target, tick]`, docs/architecture.md) for the attacker's fire, and
the target's `hp` in the frames for the loss (up to FOLLOW = 60 more ticks, a Bombard shell and a Warden's healing
both being later than the shot).

Positive control per detector: "fires" is only believed when the same harness shows the attacker's fire in the
same-layer control and not in the Line control; "does not fire" is only believed when the attacker stood within
standoff + 15 wu of an enemy, on its ordered layer, with that enemy on the stated layer, and alive for one targeting cohort
turn plus one frame (4 + 10 ticks) after that: otherwise the case fails on its premise, never passes by default. (The
measured fires happen on the first tick the enemy is in range and in sight, with no interval wait, so a unit that
stood at the enemy for that long and did not fire was held back by the reach. With the table wired, an enemy that
reaches the attacker kills it within about 70 ticks, so a longer survival premise would fail for the wrong reason.)

Failing line on main 092fa89a (reach (0, 0)), tests/transport/test_pipe_reach_cross_layer.py:214, the `assert` marked RED:
  AssertionError: raider_up_1: Raider (layer 2) fired at no enemy on layer 3 and the enemy lost no hp (arrived=1670,
  dead=None, fire=None, end tick 1790; reach (0, 0): nothing fires across a layer)
The other four cases that fire fail on the same line with their own name, layer and ticks.
"""
import json
import math
import subprocess
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

# Harness numbers (ledger row DRAFT-t1-steps; the writer's, found by running the scene).
SEED = 18
N_REGIONS = 80
FEATURES = list(range(8))
ATTACKER_LAYER = 2        # the middle of the five layers, so every offset from -2 to +2 exists
CHUNK = 10                # ticks per tactical_step
AIM_EVERY = 5             # chunks between attack_move re-aims (50 ticks)
ARRIVE_SLACK = 15.0       # wu: "arrived" is within standoff + this of the nearest enemy
WINDOW = 120              # N: ticks watched after arrival (the csim g5 WINDOW)
FOLLOW = 90               # ticks to wait for the hp to fall after a fire event (a Bombard interval is 60)
MAX_TICKS = 8000          # loop bound, not a rule value
COHORT = 4                # ticks of one targeting cohort turn (test_PP_C_g5_support.py WINDOW comment)
# Attribution of a hit: the enemy units within the attacker's AoE of its target (0 wu for direct fire) that are below the hp they
# started with, counted only while no other player unit has fired (`others_fired`).

RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = range(6)
STANDOFF = {RAIDER: 100.0, INTERCEPTOR: 100.0, VANGUARD: 100.0, BOMBARD: 40.0}
NAME = {RAIDER: "Raider", INTERCEPTOR: "Interceptor", VANGUARD: "Vanguard", BOMBARD: "Bombard"}


class Pipe:
    """The pipe as a client uses it: one frame in, the frames it answers with out (docs/architecture.md)."""

    def __init__(self):
        self.p = subprocess.Popen([str(PIPE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.watchdog = threading.Timer(300.0, self.p.kill)  # a scene takes about a second; a hung pipe must not hang the suite
        self.watchdog.start()
        assert self._read()["type"] == "hello"

    def _read(self):
        head = self.p.stdout.read(4)
        assert len(head) == 4, "the pipe closed its output"
        return json.loads(self.p.stdout.read(int.from_bytes(head, "big")))

    def send(self, name, replies, **kw):
        body = json.dumps({"type": "cmd", "name": name, **kw}).encode()
        self.p.stdin.write(len(body).to_bytes(4, "big") + body)
        self.p.stdin.flush()
        return [self._read() for _ in range(replies)]

    def command(self, verb, units, **kw):
        (r,) = self.send("command", 1, verb=verb, units=units, **kw)
        assert r["type"] == "ack", r

    def step(self, n):
        (f,) = self.send("tactical_step", 1, n=n, full=True)
        assert f["type"] == "tactical", f
        return f

    def close(self):
        try:
            self.send("quit", 0)
        finally:
            self.watchdog.cancel()
            self.p.stdin.close()
            self.p.stdout.close()
            self.p.wait(timeout=30)


def _dist(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def run_scene(atype, offset):
    """Play one scene (see the module docstring). Returns the evidence dict."""
    pipe = Pipe()
    try:
        pipe.send("set_seed", 0, seed=SEED, n_regions=N_REGIONS, features=FEATURES)
        (mission,) = pipe.send("mission_start", 1, faction=0)
        assert mission["type"] == "mission", mission
        (frame,) = pipe.send("mission_begin", 1)
        assert frame["type"] == "tactical", frame
        aoe = {p["type"]: p for p in frame["profiles"]}[atype]["aoe"]
        enemies = {u["id"] for u in frame["units"] if u["faction"] != 0}
        mine = [u for u in frame["units"] if u["faction"] == 0 and u["type"] == atype]
        assert enemies and mine, "premise: the mission holds both sides and a unit of the attacker's type"
        aid = mine[0]["id"]
        elayer = ATTACKER_LAYER + offset
        pipe.command("set_layer", sorted(enemies), layer=elayer)
        pipe.command("set_layer", [aid], layer=ATTACKER_LAYER)
        start_hp = {u["id"]: u["hp"] for u in frame["units"] if u["id"] in enemies}
        ev = dict(aid=aid, elayer=elayer, arrived=None,
                  dead=None, fire=None, loss=None, end=None, survived=0, others_fired=0)
        standoff = STANDOFF[atype]
        k = 0
        while frame["tick"] < MAX_TICKS:
            idx = {u["id"]: u for u in frame["units"]}
            a = idx.get(aid)
            if a is None:
                ev["dead"] = frame["tick"]
                break
            near = min((idx[i] for i in enemies if i in idx), key=lambda u: _dist(a, u))
            d = _dist(a, near)
            if ev["arrived"] is None and d <= standoff + ARRIVE_SLACK and a["layer"] == ATTACKER_LAYER \
                    and not a["state"] & 4:
                ev["arrived"] = frame["tick"]
                ev["arrival"] = dict(dist=round(d, 1), attacker_layer=a["layer"], enemy_layer=near["layer"])
            if ev["arrived"] is not None:
                ev["survived"] = frame["tick"] - ev["arrived"]
                if ev["survived"] >= WINDOW:
                    break
            elif k % AIM_EVERY == 0:
                f = max(d - standoff, 0.0) / d
                pipe.command("attack_move", [aid], x=a["x"] + (near["x"] - a["x"]) * f,
                             y=a["y"] + (near["y"] - a["y"]) * f)
            k += 1
            # One tick per frame once the attacker has fired: the enemy's Wardens heal a few hp a tick, which
            # would hide a small hit from a ten-tick frame.
            frame = pipe.step(CHUNK if ev["fire"] is None else 1)
            idx = {u["id"]: u for u in frame["units"]}
            for e in frame.get("events", []):
                if e[0] != 0 or e[1] not in idx:
                    continue
                if e[1] == aid and e[2] in enemies and ev["fire"] is None and e[2] in idx:
                    ev["fire"] = dict(tick=e[3], target=e[2], target_layer=idx[e[2]]["layer"],
                                      attacker_layer=idx[aid]["layer"], dist=round(_dist(idx[aid], idx[e[2]]), 1))
                elif e[1] != aid and idx[e[1]]["faction"] == 0:
                    ev["others_fired"] += 1  # attribution premise: no other player unit fired
            if ev["fire"] is not None and aid in idx:
                tgt = idx.get(ev["fire"]["target"])
                hit = [u for u in (idx[i] for i in enemies if i in idx)
                       if tgt is not None and _dist(u, tgt) <= max(aoe, 0.0) and u["hp"] < start_hp[u["id"]]]
                if hit:
                    ev["loss"] = dict(tick=frame["tick"], units=[u["id"] for u in hit], hp=hit[0]["hp"],
                                      start_hp=start_hp[hit[0]["id"]])
                    break
                if frame["tick"] - ev["fire"]["tick"] > FOLLOW:
                    break
            elif ev["fire"] is not None:
                break  # the attacker died while its hit was pending
        ev["end"] = frame["tick"]
        if ev["dead"] is None and ev["arrived"] is not None:
            ev["survived"] = frame["tick"] - ev["arrived"]
        return ev
    finally:
        pipe.close()


_CACHE = {}


def scene(atype, offset):
    if (atype, offset) not in _CACHE:
        _CACHE[(atype, offset)] = run_scene(atype, offset)
    return _CACHE[(atype, offset)]


def assert_fired_across(case, atype, offset):
    ev = scene(atype, offset)
    who = f"{case}: {NAME[atype]} (layer {ATTACKER_LAYER})"
    # RED today for the stated reason: reach (0, 0) means nothing fires across a layer.
    assert ev["loss"] is not None, (
        f"{who} fired at no enemy on layer {ev['elayer']} and the enemy lost no hp "
        f"(arrived={ev['arrived']}, dead={ev['dead']}, fire={ev['fire']}, end tick {ev['end']}; "
        "reach (0, 0): nothing fires across a layer)")
    assert ev["fire"]["target_layer"] == ev["elayer"] != ev["fire"]["attacker_layer"], ev["fire"]
    assert ev["others_fired"] == 0, f"{who}: another player unit fired, so the hp loss is not the attacker's ({ev})"


def assert_did_not_fire(case, atype, offset):
    ev = scene(atype, offset)
    who = f"{case}: {NAME[atype]} (layer {ATTACKER_LAYER})"
    assert ev["arrived"] is not None, f"premise: {who} never came within standoff of an enemy ({ev})"
    assert ev["arrival"]["attacker_layer"] == ATTACKER_LAYER and ev["arrival"]["enemy_layer"] == ev["elayer"], ev
    assert ev["survived"] >= COHORT + CHUNK, f"premise: {who} was not alive a cohort turn and a frame at the enemy ({ev})"
    assert ev["fire"] is None and ev["loss"] is None, f"{who} fired across {offset:+d} layers: {ev['fire']}"


# ---- the bible rows ----

# Strict xfail until VG-T-REACH-WIRE lands (FINDING-reach-not-wired): the wiring turns these into XPASS(strict)
# failures, and the wiring piece removes the mark. The failing line above is the evidence.
XFAIL = pytest.mark.xfail(strict=True, reason="VG-T-REACH-WIRE: R-164-01 reach not wired, FINDING-reach-not-wired")
FIRES = [
    pytest.param("raider_up_1", RAIDER, +1, marks=XFAIL, id="raider_up_1"),
    pytest.param("raider_down_1", RAIDER, -1, marks=XFAIL, id="raider_down_1"),
    pytest.param("interceptor_up_2", INTERCEPTOR, +2, marks=XFAIL, id="interceptor_up_2"),
    pytest.param("interceptor_down_1", INTERCEPTOR, -1, marks=XFAIL, id="interceptor_down_1"),
    pytest.param("bombard_down_2", BOMBARD, -2, marks=XFAIL, id="bombard_down_2"),
]
DOES_NOT = [
    ("raider_up_2", RAIDER, +2), ("interceptor_down_2", INTERCEPTOR, -2), ("bombard_up_1", BOMBARD, +1),
]


@pytest.mark.parametrize("case,atype,offset", FIRES)
def test_R_164_01_the_type_fires_at_the_offsets_its_reach_names(case, atype, offset):
    """R-164-01 (PIPE): the type fires at an enemy `offset` layers from it, the attacker's layer differing from the
    target's. RED today: reach (0, 0), the enemy loses no hp."""
    assert_fired_across(case, atype, offset)


@pytest.mark.parametrize("case,atype,offset", DOES_NOT, ids=[c[0] for c in DOES_NOT])
def test_R_164_01_the_type_does_not_fire_at_the_offsets_its_reach_leaves_out(case, atype, offset):
    """R-164-01 (PIPE): an enemy in range and in sight at an offset the table leaves out is not fired at. Green today
    and after: the premises (arrived, alive an interval, on the stated layers) make the silence mean the reach."""
    assert_did_not_fire(case, atype, offset)


def test_R_164_01_control_line_reach_is_its_own_layer_only():
    """R-164-01 positive control (PIPE): a Vanguard (Line: its own layer) one layer below its target does not fire.
    Green today and after the table is wired."""
    assert_did_not_fire("vanguard_up_1", VANGUARD, +1)


def test_R_164_01_control_the_same_scene_on_one_layer_hits():
    """R-164-01 positive control (PIPE): the same scene with attacker and enemy on the same layer: the enemy loses hp.
    Green today; it proves the harness can see a hit, so the red cases are red for the reach and not the harness."""
    ev = scene(RAIDER, 0)
    assert ev["loss"] is not None, f"the harness saw no hit even on one layer: {ev}"
    assert ev["fire"]["target_layer"] == ev["fire"]["attacker_layer"] == ATTACKER_LAYER, ev["fire"]
