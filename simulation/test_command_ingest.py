"""
Checkpoint C — Command Ingest Validation
=========================================
Tests that command_ingest.py correctly accepts, rejects, and routes all
command kinds. No socket server involved — direct calls to ingest().

  TEST 1  Valid combat commands accepted and routed to engine.command_queue
  TEST 2  Valid layer commands applied to engine state immediately
  TEST 3  Session commands accepted without mutating engine state
  TEST 4  Malformed packets dropped (all rejection categories)
  TEST 5  Unit validation: dead units, out-of-range UIDs, non-int UIDs

Output legend
  [PASS]  assertion met
  [FAIL]  assertion failed — detail on same line
  [INFO]  informational metric (no pass/fail judgment)
"""

import sys
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_LAYER, FIELD_HP
from tactical_engine import TacticalEngine
from test_maps import open_field, multi_layer
from command_ingest import ingest

config.DEBUG_COMMAND_LOG = False  # keep test output clean


# ── helpers ──────────────────────────────────────────────────────────────────

def _banner(label):
    print(f"\n{'─' * 62}")
    print(f"  {label}")
    print('─' * 62)


def _result(label, passed, detail=""):
    tag = "[PASS]" if passed else "[FAIL]"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {tag}  {label}{suffix}")
    return passed


def _info(label, value):
    print(f"  [INFO]  {label}: {value}")


def _make_engine(layers=1):
    tmap = multi_layer() if layers > 1 else open_field()
    engine = TacticalEngine(tmap)
    return engine


def _spawn(engine, faction, x, y, unit_type="Raider"):
    engine.store.spawn(unit_type, faction, x, y)
    return engine.store.count - 1  # uid of newly spawned unit


# ── Test 1 — Valid combat commands ───────────────────────────────────────────

def test_combat_commands():
    _banner("TEST 1  Valid combat commands accepted → routed to engine.command_queue")
    results = []

    engine = _make_engine()
    uid0 = _spawn(engine, 0, 500.0, 500.0)
    uid1 = _spawn(engine, 0, 600.0, 600.0)
    uid2 = _spawn(engine, 1, 2000.0, 2000.0)  # enemy target

    # move
    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": [uid0, uid1], "target": {"pos": [1000.0, 1000.0]}},
    }, engine)
    results.append(_result("move accepted", ok, reason))
    results.append(_result("move queued", len(engine.command_queue.all_commands()) == 1,
                           f"queue length={len(engine.command_queue.all_commands())}"))

    # attack_move
    engine2 = _make_engine()
    uid_a = _spawn(engine2, 0, 100.0, 100.0)
    ok2, r2 = ingest({
        "type": "command",
        "command": {"kind": "attack_move", "unit_uids": [uid_a], "target": {"pos": [3000.0, 3000.0]}},
    }, engine2)
    results.append(_result("attack_move accepted", ok2, r2))
    results.append(_result("attack_move queued", len(engine2.command_queue.all_commands()) == 1))

    # attack_target
    engine3 = _make_engine()
    uid_attacker = _spawn(engine3, 0, 100.0, 100.0)
    uid_target = _spawn(engine3, 1, 3000.0, 3000.0)
    ok3, r3 = ingest({
        "type": "command",
        "command": {"kind": "attack_target", "unit_uids": [uid_attacker], "target_uid": uid_target},
    }, engine3)
    results.append(_result("attack_target accepted", ok3, r3))
    cmd = engine3.command_queue.all_commands()[0]
    results.append(_result("attack_target params carry target_uid",
                           cmd.params.get("target_uid") == uid_target,
                           f"params={cmd.params}"))

    # activate_ability
    engine4 = _make_engine()
    uid_ab = _spawn(engine4, 0, 200.0, 200.0)
    ok4, r4 = ingest({
        "type": "command",
        "command": {"kind": "activate_ability", "unit_uids": [uid_ab]},
    }, engine4)
    results.append(_result("activate_ability accepted", ok4, r4))
    results.append(_result("activate_ability queued", len(engine4.command_queue.all_commands()) == 1))

    return all(results)


# ── Test 2 — Valid layer commands ─────────────────────────────────────────────

def test_layer_commands():
    _banner("TEST 2  Layer commands mutate engine state immediately")
    results = []

    engine = _make_engine(layers=3)
    uid0 = _spawn(engine, 0, 500.0, 500.0)
    uid1 = _spawn(engine, 0, 600.0, 600.0)

    initial_layer = int(engine.store.data[uid0, FIELD_LAYER])

    # layer_hard_transfer moves both units to layer 2
    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "layer_hard_transfer", "unit_uids": [uid0, uid1], "target_layer": 2},
    }, engine)
    results.append(_result("layer_hard_transfer accepted", ok, reason))
    new_layer0 = int(engine.store.data[uid0, FIELD_LAYER])
    new_layer1 = int(engine.store.data[uid1, FIELD_LAYER])
    results.append(_result("uid0 moved to layer 2", new_layer0 == 2,
                           f"layer={new_layer0}"))
    results.append(_result("uid1 moved to layer 2", new_layer1 == 2,
                           f"layer={new_layer1}"))

    # layer_preference_set stores preference in engine dict
    ok2, r2 = ingest({
        "type": "command",
        "command": {"kind": "layer_preference_set", "unit_uids": [uid0], "preferred_layer": 1},
    }, engine)
    results.append(_result("layer_preference_set accepted", ok2, r2))
    pref = engine.layer_preferences.get(uid0)
    results.append(_result(f"uid0 preference stored as 1", pref == 1,
                           f"got {pref!r}"))

    # clearing preference (null)
    ok3, r3 = ingest({
        "type": "command",
        "command": {"kind": "layer_preference_set", "unit_uids": [uid0], "preferred_layer": None},
    }, engine)
    results.append(_result("layer_preference_set null clears preference", ok3, r3))
    results.append(_result("uid0 preference removed",
                           uid0 not in engine.layer_preferences,
                           f"dict={engine.layer_preferences}"))

    return all(results)


# ── Test 3 — Session commands ─────────────────────────────────────────────────

def test_session_commands():
    _banner("TEST 3  Session commands accepted without mutating engine state")
    results = []

    engine = _make_engine()
    uid0 = _spawn(engine, 0, 100.0, 100.0)

    for kind in ("control_group_bind", "control_group_recall"):
        q_before = len(engine.command_queue.all_commands())
        ok, reason = ingest({
            "type": "command",
            "command": {"kind": kind, "unit_uids": [uid0]},
        }, engine)
        q_after = len(engine.command_queue.all_commands())
        results.append(_result(f"{kind} accepted", ok and reason == "session",
                               f"accepted={ok} reason={reason!r}"))
        results.append(_result(f"{kind} no queue mutation", q_before == q_after,
                               f"before={q_before} after={q_after}"))

    return all(results)


# ── Test 4 — Malformed packet rejection ──────────────────────────────────────

def test_malformed_rejection():
    _banner("TEST 4  Malformed packets dropped — all rejection categories")
    results = []

    engine = _make_engine()
    uid0 = _spawn(engine, 0, 100.0, 100.0)

    cases = [
        # (label, packet, expect_accepted)
        ("non-dict packet",
         "this is a string", False),
        ("wrong type field",
         {"type": "hello", "command": {"kind": "move"}}, False),
        ("missing command field",
         {"type": "command"}, False),
        ("non-dict command field",
         {"type": "command", "command": "move"}, False),
        ("unknown kind",
         {"type": "command", "command": {"kind": "nuke", "unit_uids": [uid0]}}, False),
        ("empty unit_uids",
         {"type": "command", "command": {"kind": "move", "unit_uids": [], "target": {"pos": [1.0, 1.0]}}}, False),
        ("non-list unit_uids",
         {"type": "command", "command": {"kind": "move", "unit_uids": uid0, "target": {"pos": [1.0, 1.0]}}}, False),
        ("move missing target",
         {"type": "command", "command": {"kind": "move", "unit_uids": [uid0]}}, False),
        ("move target.pos not a list",
         {"type": "command", "command": {"kind": "move", "unit_uids": [uid0], "target": {"pos": "1,2"}}}, False),
        ("move target.pos wrong length",
         {"type": "command", "command": {"kind": "move", "unit_uids": [uid0], "target": {"pos": [1.0]}}}, False),
        ("move negative position",
         {"type": "command", "command": {"kind": "move", "unit_uids": [uid0], "target": {"pos": [-1.0, 500.0]}}}, False),
        ("attack_target missing target_uid",
         {"type": "command", "command": {"kind": "attack_target", "unit_uids": [uid0]}}, False),
        ("attack_target target_uid string",
         {"type": "command", "command": {"kind": "attack_target", "unit_uids": [uid0], "target_uid": "0"}}, False),
        ("layer_hard_transfer missing target_layer",
         {"type": "command", "command": {"kind": "layer_hard_transfer", "unit_uids": [uid0]}}, False),
        ("layer_hard_transfer out of range",
         {"type": "command", "command": {"kind": "layer_hard_transfer", "unit_uids": [uid0], "target_layer": 99}}, False),
        ("layer_preference_set bad type",
         {"type": "command", "command": {"kind": "layer_preference_set", "unit_uids": [uid0], "preferred_layer": "high"}}, False),
    ]

    for label, pkt, expected in cases:
        ok, reason = ingest(pkt, engine)
        passed = (ok == expected)
        results.append(_result(label,
                               passed,
                               f"accepted={ok} reason={reason!r}" if not passed else ""))

    _info("rejection cases tested", len(cases))
    return all(results)


# ── Test 5 — Unit validation ──────────────────────────────────────────────────

def test_unit_validation():
    _banner("TEST 5  Unit validation: dead units, out-of-range UIDs, non-int UIDs")
    results = []

    engine = _make_engine()
    uid_live = _spawn(engine, 0, 100.0, 100.0)
    uid_dead = _spawn(engine, 0, 200.0, 200.0)

    # kill uid_dead directly
    engine.store.alive[uid_dead] = False

    ok, reason = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": [uid_dead], "target": {"pos": [500.0, 500.0]}},
    }, engine)
    results.append(_result("dead unit rejected", not ok, f"reason={reason!r}"))

    ok2, reason2 = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": [999], "target": {"pos": [500.0, 500.0]}},
    }, engine)
    results.append(_result("out-of-range uid rejected", not ok2, f"reason={reason2!r}"))

    ok3, reason3 = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": [-1], "target": {"pos": [500.0, 500.0]}},
    }, engine)
    results.append(_result("negative uid rejected", not ok3, f"reason={reason3!r}"))

    ok4, reason4 = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": ["0"], "target": {"pos": [500.0, 500.0]}},
    }, engine)
    results.append(_result("string uid rejected", not ok4, f"reason={reason4!r}"))

    # live unit still accepted after all the above
    ok5, reason5 = ingest({
        "type": "command",
        "command": {"kind": "move", "unit_uids": [uid_live], "target": {"pos": [500.0, 500.0]}},
    }, engine)
    results.append(_result("live unit accepted after rejections", ok5, f"reason={reason5!r}"))

    return all(results)


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = [
        test_combat_commands(),
        test_layer_commands(),
        test_session_commands(),
        test_malformed_rejection(),
        test_unit_validation(),
    ]

    total = len(passed)
    n_pass = sum(passed)
    print(f"\n{'═' * 62}")
    print(f"  Checkpoint C result: {n_pass}/{total} tests passed")
    print(f"{'═' * 62}\n")
    sys.exit(0 if n_pass == total else 1)
