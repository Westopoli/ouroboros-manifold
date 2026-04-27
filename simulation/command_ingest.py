"""
Validates command packets from the Godot client and applies them to TacticalEngine.

Valid command kinds
  Combat (4):  move, attack_move, attack_target, activate_ability
  Layer  (2):  layer_hard_transfer, layer_preference_set
  Session (2): control_group_bind, control_group_recall  (client bookkeeping — no engine mutation)

Malformed packets are dropped and logged only when config.DEBUG_COMMAND_LOG is True.
"""

import logging
import config
from command import Command
from unit import FIELD_LAYER

logger = logging.getLogger(__name__)

_COMBAT_KINDS = {"move", "attack_move", "attack_target", "activate_ability"}
_LAYER_KINDS  = {"layer_hard_transfer", "layer_preference_set"}
_SESSION_KINDS = {"control_group_bind", "control_group_recall"}
VALID_KINDS = _COMBAT_KINDS | _LAYER_KINDS | _SESSION_KINDS


def ingest(packet: dict, engine) -> tuple:
    """Validate and apply one command packet to the engine.

    Returns (accepted: bool, reason: str).
    Never raises — malformed packets are dropped silently (or logged when
    config.DEBUG_COMMAND_LOG is True).
    """
    try:
        return _ingest(packet, engine)
    except Exception as exc:
        return _drop(f"unhandled error: {exc}")


def _ingest(packet, engine):
    if not isinstance(packet, dict):
        return _drop("packet is not a dict")

    if packet.get("type") != "command":
        return _drop(f"expected type='command', got {packet.get('type')!r}")

    cmd = packet.get("command")
    if not isinstance(cmd, dict):
        return _drop("missing or non-dict 'command' field")

    kind = cmd.get("kind")
    if kind not in VALID_KINDS:
        return _drop(f"unknown kind {kind!r}")

    if kind in _SESSION_KINDS:
        return True, "session"

    unit_uids = cmd.get("unit_uids", [])
    if not isinstance(unit_uids, list) or len(unit_uids) == 0:
        return _drop(f"kind={kind}: unit_uids must be a non-empty list")

    store = engine.store
    valid_uids = []
    for uid in unit_uids:
        if not isinstance(uid, int):
            return _drop(f"kind={kind}: uid {uid!r} is not an int")
        if uid < 0 or uid >= store.count:
            return _drop(f"kind={kind}: uid {uid} out of range (store has {store.count} units)")
        if store.alive[uid]:
            valid_uids.append(uid)

    if not valid_uids:
        return _drop(f"kind={kind}: all {len(unit_uids)} units are dead")

    if kind == "move":
        return _apply_move(cmd, engine, valid_uids, attack_moving=False)
    if kind == "attack_move":
        return _apply_move(cmd, engine, valid_uids, attack_moving=True)
    if kind == "attack_target":
        return _apply_attack_target(cmd, engine, valid_uids)
    if kind == "activate_ability":
        return _apply_activate_ability(engine, valid_uids)
    if kind == "layer_hard_transfer":
        return _apply_layer_hard_transfer(cmd, engine, valid_uids)
    if kind == "layer_preference_set":
        return _apply_layer_preference_set(cmd, engine, valid_uids)

    return _drop(f"unhandled kind {kind!r}")


def _apply_move(cmd, engine, unit_uids, attack_moving):
    target = cmd.get("target")
    if not isinstance(target, dict):
        return _drop("move/attack_move: missing 'target' dict")

    pos = target.get("pos")
    if not isinstance(pos, list) or len(pos) != 2:
        return _drop("move/attack_move: target.pos must be [x, y]")

    x, y = pos
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return _drop("move/attack_move: pos values must be numbers")
    if x < 0 or y < 0:
        return _drop(f"move/attack_move: negative position ({x}, {y})")

    kind_str = "attack_move" if attack_moving else "move"
    engine.command_queue.add(Command(
        tick=engine.tick,
        type=kind_str,
        unit_ids=unit_uids,
        params={"target_x": float(x), "target_y": float(y)},
    ))
    return True, kind_str


def _apply_attack_target(cmd, engine, unit_uids):
    target_uid = cmd.get("target_uid")
    if not isinstance(target_uid, int):
        return _drop("attack_target: target_uid must be an int")
    if target_uid < 0 or target_uid >= engine.store.count:
        return _drop(f"attack_target: target_uid {target_uid} out of range")

    engine.command_queue.add(Command(
        tick=engine.tick,
        type="attack_target",
        unit_ids=unit_uids,
        params={"target_uid": target_uid},
    ))
    return True, "attack_target"


def _apply_activate_ability(engine, unit_uids):
    engine.command_queue.add(Command(
        tick=engine.tick,
        type="activate_ability",
        unit_ids=unit_uids,
        params={},
    ))
    return True, "activate_ability"


def _apply_layer_hard_transfer(cmd, engine, unit_uids):
    target_layer = cmd.get("target_layer")
    if not isinstance(target_layer, int):
        return _drop("layer_hard_transfer: target_layer must be an int")
    if target_layer < 0 or target_layer >= engine.map.layers:
        return _drop(
            f"layer_hard_transfer: target_layer {target_layer} out of range "
            f"[0, {engine.map.layers})"
        )
    for uid in unit_uids:
        engine.store.data[uid, FIELD_LAYER] = float(target_layer)
    return True, "layer_hard_transfer"


def _apply_layer_preference_set(cmd, engine, unit_uids):
    preferred = cmd.get("preferred_layer")  # int or None/null
    if preferred is not None:
        if not isinstance(preferred, int):
            return _drop("layer_preference_set: preferred_layer must be int or null")
        if preferred < 0 or preferred >= engine.map.layers:
            return _drop(
                f"layer_preference_set: preferred_layer {preferred} out of range "
                f"[0, {engine.map.layers})"
            )

    if not hasattr(engine, "layer_preferences"):
        engine.layer_preferences = {}

    for uid in unit_uids:
        if preferred is None:
            engine.layer_preferences.pop(uid, None)
        else:
            engine.layer_preferences[uid] = preferred
    return True, "layer_preference_set"


def _drop(reason: str) -> tuple:
    if getattr(config, "DEBUG_COMMAND_LOG", False):
        logger.warning("command_ingest dropped: %s", reason)
    return False, reason
