import copy
import math

import config
from unit import (
    FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_HP, FIELD_MAX_HP,
    FIELD_ABILITY_COOLDOWN, FIELD_FACING_RAD, FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE,
)
from fog_of_war import compute_visibility


class DeadReckoningTracker:
    """Tracks per-unit dead-reckoning state to suppress redundant position updates.

    On-course units are omitted from units_updated; the client extrapolates
    pos += velocity * dt each tick using the last sent velocity.

    Resyncs fire when:
      - Unit is new (never sent)
      - Velocity magnitude changes by > DR_VEL_CHANGE_THRESHOLD wu/s
      - Predicted position deviates from actual by > DR_RESYNC_THRESHOLD world units

    Call reset() whenever a full snapshot is sent so the client's ground truth
    re-anchors and dead-reckoning restarts cleanly.
    """

    def __init__(self):
        # uid → {'sent_pos': [x,y], 'sent_vel': [vx,vy], 'sent_tick': int}
        self._state: dict = {}

    def needs_resync(self, uid, cur_pos: list, vel: list, current_tick: int) -> bool:
        if uid not in self._state:
            return True
        s = self._state[uid]

        # Velocity magnitude change
        pv = s['sent_vel']
        dv = math.sqrt((vel[0] - pv[0]) ** 2 + (vel[1] - pv[1]) ** 2)
        if dv > config.DR_VEL_CHANGE_THRESHOLD:
            return True

        # Position prediction error
        dt = config.TACTICAL_TICK_DURATION
        elapsed = (current_tick - s['sent_tick']) * dt
        pred_x = s['sent_pos'][0] + pv[0] * elapsed
        pred_y = s['sent_pos'][1] + pv[1] * elapsed
        err = math.sqrt((cur_pos[0] - pred_x) ** 2 + (cur_pos[1] - pred_y) ** 2)
        return err > config.DR_RESYNC_THRESHOLD

    def mark_sent(self, uid, pos: list, vel: list, tick: int):
        self._state[uid] = {
            'sent_pos': list(pos),
            'sent_vel': list(vel),
            'sent_tick': tick,
        }

    def remove(self, uid):
        self._state.pop(uid, None)

    def reset(self):
        """Call when a full snapshot is sent — client has ground truth, restart DR."""
        self._state.clear()


def full_snapshot(engine) -> dict:
    store = engine.store
    tmap = engine.map

    units = []
    for uid in range(store.count):
        if store.alive[uid]:
            units.append(_unit_entry(store, uid, engine.player_faction))

    structures = [_structure_entry(s) for s in engine.reinforcement_structures]
    objectives = [_objective_entry(o) for o in engine.objectives]

    visibility = compute_visibility(store, tmap)
    player_visible = set()
    for uid, visible_set in visibility.items():
        if int(store.faction[uid]) == int(engine.player_faction):
            player_visible.update(visible_set)

    spine_nodes = []
    for i, sn in enumerate(tmap.spine_nodes):
        spine_nodes.append({
            "id": f"{sn.node_type}_{i}",
            "type": sn.node_type,
            "pos": [sn.position[0], sn.position[1]],
            "layer": sn.properties.get("layer"),
        })

    gradient_sources = []
    for gs in tmap.gradient_sources:
        gradient_sources.append({
            "property": gs.property_type,
            "pos": [gs.position[0], gs.position[1]],
            "radius": gs.radius,
            "intensity": gs.intensity,
        })

    drifting_nodes = []
    for dn in tmap.drifting_nodes:
        drifting_nodes.append({
            "id": dn.node_id,
            "type": dn.node_type,
            "waypoints": [[wp[0], wp[1]] for wp in dn.waypoints],
            "period_ticks": dn.period_ticks,
            "mode": dn.mode,
            "current_pos": list(dn.position_at(engine.tick)),
        })

    return {
        "type": "snapshot",
        "tick": engine.tick,
        "mission_id": getattr(engine, "mission_id", ""),
        "map": {
            "canvas_size": [tmap.width, tmap.height],
            "spine_nodes": spine_nodes,
            "gradient_sources": gradient_sources,
            "drifting_nodes": drifting_nodes,
        },
        "units": units,
        "structures": structures,
        "objectives": objectives,
        "fog_of_war": {
            "player_visible_unit_uids": sorted(player_visible),
            "partial_visibility_uids": [],  # post-Stage-8 feature
        },
        "tick_rate_hz": config.TICK_HZ,
    }


def delta(engine, prev_state: dict, dr_tracker=None) -> dict:
    """Compute a tick delta.

    dr_tracker — DeadReckoningTracker instance (optional).
      With tracker: suppresses position updates for on-course units; emits
      velocity alongside position on resyncs.
      Without tracker (None): legacy mode — sends all changed positions.
      Use legacy mode for reconstruction tests and headless tools.
    """
    store = engine.store
    dt = config.TACTICAL_TICK_DURATION

    prev_units = {u["uid"]: u for u in prev_state.get("units", [])}
    prev_structures = {s["uid"]: s for s in prev_state.get("structures", [])}
    prev_objectives = {o["id"]: o for o in prev_state.get("objectives", [])}

    current_alive = {uid for uid in range(store.count) if store.alive[uid]}
    prev_alive = set(prev_units.keys())

    # New units — always full entry, velocity = [0, 0]
    units_added = []
    for uid in (current_alive - prev_alive):
        entry = _unit_entry(store, uid, engine.player_faction)
        entry["velocity"] = [0.0, 0.0]
        if dr_tracker is not None:
            dr_tracker.mark_sent(uid, entry["pos"], [0.0, 0.0], engine.tick)
        units_added.append(entry)

    # Removed units
    units_removed = list(prev_alive - current_alive)
    if dr_tracker is not None:
        for uid in units_removed:
            dr_tracker.remove(uid)

    # Changed units
    units_updated = []
    for uid in current_alive & prev_alive:
        cur = _unit_entry(store, uid, engine.player_faction)
        prev = prev_units[uid]

        # Non-positional state changes always sent when they occur
        state_changes = {}
        if cur["hp"] != prev["hp"]:
            state_changes["hp"] = cur["hp"]
        if cur["layer"] != prev["layer"]:
            state_changes["layer"] = cur["layer"]
        if cur["ability_cd_sec"] != prev["ability_cd_sec"]:
            state_changes["ability_cd_sec"] = cur["ability_cd_sec"]
        if cur["facing_rad"] != prev.get("facing_rad", 0.0):
            state_changes["facing_rad"] = cur["facing_rad"]
        if cur["attack_target"] != prev.get("attack_target", -1):
            state_changes["attack_target"] = cur["attack_target"]

        # Positional update: dead-reckon or always send
        pos_update = {}
        if dr_tracker is not None:
            prev_pos = prev["pos"]
            cur_pos = cur["pos"]
            vel = [
                round((cur_pos[0] - prev_pos[0]) / dt, 4),
                round((cur_pos[1] - prev_pos[1]) / dt, 4),
            ]
            if dr_tracker.needs_resync(uid, cur_pos, vel, engine.tick):
                pos_update["pos"] = cur_pos
                pos_update["velocity"] = vel
                dr_tracker.mark_sent(uid, cur_pos, vel, engine.tick)
            # else: on course — client dead-reckons, no pos/velocity in delta
        else:
            if cur["pos"] != prev["pos"]:
                pos_update["pos"] = cur["pos"]

        combined = {**state_changes, **pos_update}
        if combined:
            combined["uid"] = uid
            units_updated.append(combined)

    # Structures
    structures_updated = []
    for s in engine.reinforcement_structures:
        uid = s.structure_uid
        prev = prev_structures.get(uid)
        if not prev:
            continue
        cur = _structure_entry(s)
        changed = {k: cur[k] for k in ("hp", "owner", "capture_progress", "production_timer_sec")
                   if cur[k] != prev.get(k)}
        if changed:
            changed["uid"] = uid
            structures_updated.append(changed)

    # Objectives
    objectives_updated = []
    for obj in engine.objectives:
        cur = _objective_entry(obj)
        prev = prev_objectives.get(obj.id, {})
        if cur["progress"] != prev.get("progress") or cur["status"] != prev.get("status"):
            objectives_updated.append(cur)

    # Events: unit deaths
    events = []
    for uid in (prev_alive - current_alive):
        prev_u = prev_units[uid]
        events.append({
            "kind": "unit_destroyed",
            "uid": uid,
            "at": prev_u["pos"],
            "layer": prev_u["layer"],
        })

    return {
        "type": "delta",
        "tick": engine.tick,
        "units_updated": units_updated,
        "units_added": units_added,
        "units_removed": units_removed,
        "structures_updated": structures_updated,
        "objectives_updated": objectives_updated,
        "command_acks": [],  # populated by command_ingest.py in Checkpoint C
        "events": events,
    }


def apply_delta(snapshot: dict, d: dict) -> dict:
    """Fold a delta into a snapshot, returning an updated snapshot.
    Used for reconstruction tests — not called during live play.

    Handles both legacy deltas (pos always present when changed) and
    dead-reckoning deltas (pos absent for on-course units; velocity used
    to extrapolate). Units not in units_updated are dead-reckoned via
    their stored velocity.
    """
    dt = config.TACTICAL_TICK_DURATION
    result = copy.deepcopy(snapshot)
    result["tick"] = d["tick"]

    units_by_uid = {u["uid"]: u for u in result["units"]}
    updated_uids = set()

    for uid in d.get("units_removed", []):
        units_by_uid.pop(uid, None)

    for u in d.get("units_added", []):
        units_by_uid[u["uid"]] = u

    for upd in d.get("units_updated", []):
        uid = upd["uid"]
        if uid in units_by_uid:
            units_by_uid[uid].update(upd)
        updated_uids.add(uid)

    # Dead-reckon units not explicitly updated this tick
    for uid, unit in units_by_uid.items():
        if uid in updated_uids:
            continue
        vel = unit.get("velocity", [0.0, 0.0])
        if vel[0] != 0.0 or vel[1] != 0.0:
            unit["pos"] = [
                round(unit["pos"][0] + vel[0] * dt, 4),
                round(unit["pos"][1] + vel[1] * dt, 4),
            ]

    result["units"] = sorted(units_by_uid.values(), key=lambda u: u["uid"])

    structs_by_uid = {s["uid"]: s for s in result.get("structures", [])}
    for upd in d.get("structures_updated", []):
        uid = upd["uid"]
        if uid in structs_by_uid:
            structs_by_uid[uid].update(upd)
    result["structures"] = list(structs_by_uid.values())

    objs_by_id = {o["id"]: o for o in result.get("objectives", [])}
    for upd in d.get("objectives_updated", []):
        objs_by_id[upd["id"]] = upd
    result["objectives"] = list(objs_by_id.values())

    return result


def _unit_entry(store, uid, player_faction) -> dict:
    return {
        "uid": uid,
        "type": store.unit_type[uid],
        "pos": [
            round(float(store.data[uid, FIELD_X]), 4),
            round(float(store.data[uid, FIELD_Y]), 4),
        ],
        "layer": int(store.data[uid, FIELD_LAYER]),
        "hp": round(float(store.data[uid, FIELD_HP]), 4),
        "max_hp": round(float(store.data[uid, FIELD_MAX_HP]), 4),
        "faction": int(store.faction[uid]),
        "facing_rad": round(float(store.data[uid, FIELD_FACING_RAD]), 4),
        "attack_target": int(store.auto_engage_target[uid]),
        "attack_interval": round(float(store.data[uid, FIELD_ATTACK_INTERVAL]), 4),
        "attack_range": round(float(store.data[uid, FIELD_ATTACK_RANGE]), 4),
        "ability_cd_sec": round(float(store.data[uid, FIELD_ABILITY_COOLDOWN]), 4),
        "selection_eligible": int(store.faction[uid]) == int(player_faction),
        "velocity": [0.0, 0.0],  # updated via delta; snapshot always starts at rest
    }


def _structure_entry(s) -> dict:
    return {
        "uid": s.structure_uid,
        "pos": [s.position[0], s.position[1]],
        "layer": s.layer,
        "hp": s.hp,
        "max_hp": s.max_hp,
        "owner": s.owner_faction,
        "capture_progress": round(s.capture_progress, 4),
        "production_timer_sec": round(s.production_timer_sec, 4),
        "production_target": s.production_target_unit_type,
        "capture_radius": s.capture_radius,
    }


def _objective_entry(obj) -> dict:
    if obj.failed:
        status = "failed"
    elif obj.completion >= 1.0:
        status = "complete"
    else:
        status = "in_progress"
    return {
        "id": obj.id,
        "type": obj.type,
        "progress": round(obj.completion, 4),
        "status": status,
    }


def delta_baseline(engine) -> dict:
    """Lightweight prev-state for delta comparison. Skips fog, map, spine nodes."""
    store = engine.store
    units = []
    for uid in range(store.count):
        if store.alive[uid]:
            units.append({
                "uid": uid,
                "pos": [
                    round(float(store.data[uid, FIELD_X]), 4),
                    round(float(store.data[uid, FIELD_Y]), 4),
                ],
                "layer": int(store.data[uid, FIELD_LAYER]),
                "hp": round(float(store.data[uid, FIELD_HP]), 4),
                "ability_cd_sec": round(float(store.data[uid, FIELD_ABILITY_COOLDOWN]), 4),
                "facing_rad": round(float(store.data[uid, FIELD_FACING_RAD]), 4),
                "attack_target": int(store.auto_engage_target[uid]),
            })
    structures = [_structure_entry(s) for s in engine.reinforcement_structures]
    objectives = [_objective_entry(o) for o in engine.objectives]
    return {"units": units, "structures": structures, "objectives": objectives}
