# Replaces socket_server.py's TCP transport with stdio pipe I/O.
# Godot spawns this process and communicates over stdin/stdout.
# See socket_server.py — that file's TCP transport is superseded by this module.
#
# Protocol: 4-byte big-endian length header + UTF-8 JSON body, both directions.
# Stdout is owned entirely by this protocol. Stray print() calls are intercepted
# by _StdoutTrap and routed to stderr (logs/sim_stderr.log) to prevent corruption.

import sys
import os
import json
import struct
import threading
import queue
import platform
import traceback
import logging
import time

SIM_VERSION = "0.10.0"

_real_stdout_buffer = None
_original_stdout = None  # prevent GC from closing the buffer — see _setup_io()


class _StdoutTrap:
    """Routes stray print() calls to stderr so they don't corrupt the pipe protocol."""

    def write(self, s):
        if s.strip():
            try:
                sys.stderr.write(f"[pipe:stdout-intercepted] {s}\n")
                sys.stderr.flush()
            except Exception:
                pass
        return len(s)

    def flush(self):
        pass


def _setup_io():
    global _real_stdout_buffer, _original_stdout
    _original_stdout = sys.stdout  # prevent GC from closing the underlying buffer
    _real_stdout_buffer = sys.stdout.buffer

    import config as _cfg
    os.makedirs("logs", exist_ok=True)
    stderr_log = open(_cfg.STDERR_LOG_PATH, "w", encoding="utf-8", buffering=1)
    sys.stderr = stderr_log
    sys.stdout = _StdoutTrap()
    logging.basicConfig(stream=stderr_log, level=logging.INFO, format="%(levelname)s %(message)s")


def _install_crash_handler():
    import config as _cfg

    def _handler(exc_type, exc_val, exc_tb):
        try:
            os.makedirs("logs", exist_ok=True)
            tb_text = _strip_abs_paths(
                "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            )
            with open(_cfg.CRASH_LOG_PATH, "w", encoding="utf-8") as f:
                f.write(f"sim_version: {SIM_VERSION}\n")
                f.write(f"os: {platform.system()} {platform.release()}\n")
                f.write(f"python: {sys.version}\n")
                f.write("\n--- traceback ---\n")
                f.write(tb_text)
        except Exception:
            pass  # crash handler must never itself crash

    sys.excepthook = _handler


def _strip_abs_paths(text: str) -> str:
    """Strip cwd prefix from absolute paths in a traceback string."""
    for cwd in (os.path.realpath(os.getcwd()), os.getcwd()):
        for sep in ("/", os.sep):
            key = cwd.rstrip(sep) + sep
            if key in text:
                text = text.replace(key, "")
    return text


def _build_mission_briefing(engine, snapshot: dict, player_faction: int) -> dict:
    if hasattr(engine, "mission_briefing_data") and engine.mission_briefing_data:
        return engine.mission_briefing_data

    # Fallback stub for test harness / __main__ mode
    player_by_type: dict = {}
    enemy_count: int = 0
    for u in snapshot.get("units", []):
        if u.get("faction") == player_faction:
            t = str(u.get("type", "unit")).lower()
            player_by_type[t] = player_by_type.get(t, 0) + 1
        else:
            enemy_count += 1
    player_units = [
        {"type_abstract": t, "type_display_name": t.capitalize(), "category": "line", "count": c}
        for t, c in player_by_type.items()
    ]
    total_player = sum(player_by_type.values())
    parity = int(100 * total_player / max(enemy_count, 1))
    return {
        "mission_id_label": "OP-%04d" % snapshot.get("tick", 0),
        "chapter": 1,
        "generation": 1,
        "era_id": "settled_reach",
        "mission_title": "Field Engagement",
        "mission_subtitle": "Forces in contact across the operational area",
        "tick_counter": snapshot.get("tick", 0),
        "situation_text": "Forces are in contact. Engage and destroy the enemy.",
        "objective_primary": {
            "text": "Destroy the enemy force.",
            "archetype": "Assault",
            "success_spectrum_label": "TOTAL VICTORY",
        },
        "objectives_secondary": [],
        "enemy_assessment": {
            "faction_name": "Enemy Force",
            "archetype_label": "UNKNOWN",
            "military_stat": min(100, enemy_count * 10),
            "military_stat_max": 100,
            "tech_tier": 1,
            "behavior_tag": "ACTIVE",
        },
        "player_force": {
            "parity_percentage": parity,
            "units": player_units,
        },
        "region_state": {
            "name": "Operational Area",
            "tier": "Frontier",
            "economy": {"value": 50, "max": 100},
            "military": {"value": 60, "max": 100},
            "tension": {"value": 80, "max": 100},
        },
        "commander_lineage": {
            "name": "Commander",
            "generation_number": 1,
            "predecessor_name": "",
            "predecessor_status": "",
        },
        "reinforcement_note": "",
    }


ARCHETYPE_TITLES = {
    "defensive_stand":     ("Defensive Stand", "Hold the line against incoming attack"),
    "siege_breaking":      ("Siege Breaking", "Break the enemy's stranglehold"),
    "reconquest":          ("Reconquest", "Take back what was lost"),
    "assault":             ("Assault", "Seize enemy territory by force"),
    "suppression":         ("Suppression", "Crush the breakaway before it consolidates"),
    "multi_front_defense": ("Multi-Front Defense", "Hold on all fronts simultaneously"),
    "interception":        ("Interception", "Destroy the enemy before they reach the target"),
    "evacuation":          ("Evacuation", "Buy time and extract what you can"),
    "containment":         ("Containment", "Draw a line and hold it"),
    "counterinsurgency":   ("Counterinsurgency", "Root out the insurgents with precision"),
}

ARCHETYPE_BEHAVIOR_TAGS = {
    "defensive_stand":     "ATTACKING",
    "siege_breaking":      "ENTRENCHED",
    "reconquest":          "OCCUPYING",
    "assault":             "DEFENDING",
    "suppression":         "SCATTERED",
    "multi_front_defense": "MULTI-AXIS ATTACK",
    "interception":        "EN ROUTE",
    "evacuation":          "OVERWHELMING FORCE",
    "containment":         "EXPANDING",
    "counterinsurgency":   "INSURGENT CELLS",
}

UNIT_CATEGORIES = {
    "Raider": "strike", "Interceptor": "strike",
    "Vanguard": "line", "Warden": "line",
    "Bombard": "siege", "Bastion": "siege",
}


def _mission_setup_to_briefing(setup, sim_env, cmdr_selection):
    """Convert MissionSetup + world state into the dict shape mission_briefing.gd expects."""
    region = sim_env["world"].regions.get(setup.region_id)
    region_name = getattr(region, "name", setup.region_id) if region else setup.region_id

    title, subtitle = ARCHETYPE_TITLES.get(setup.archetype, ("Mission", "Engage the enemy"))

    enemy_force = setup.enemy_forces[0] if setup.enemy_forces else None
    enemy_fid = enemy_force.faction_id if enemy_force else None
    enemy_faction = sim_env["registry"].get(enemy_fid) if enemy_fid else None
    enemy_name = getattr(enemy_faction, "name", str(enemy_fid)) if enemy_faction else "Enemy Force"
    enemy_power = enemy_force.total_power if enemy_force else 0

    situation_parts = []
    if setup.briefing.get("situation"):
        situation_parts.append(setup.briefing["situation"])
    if setup.briefing.get("objective"):
        situation_parts.append(setup.briefing["objective"])
    if setup.briefing.get("assets"):
        situation_parts.append(setup.briefing["assets"])
    situation_text = "\n\n".join(situation_parts) if situation_parts else "Mission details are classified."

    # Primary objective from the setup's objectives list
    primary_obj = None
    secondary_objs = []
    for obj_spec in setup.objectives:
        obj_entry = {
            "text": obj_spec.type.replace("_", " ").capitalize() + ".",
            "archetype": setup.archetype.replace("_", " ").title(),
        }
        if obj_spec.is_primary:
            obj_entry["success_spectrum_label"] = "PRIMARY OBJECTIVE"
            primary_obj = obj_entry
        else:
            obj_entry["weight_label"] = "SECONDARY"
            secondary_objs.append(obj_entry)
    if not primary_obj:
        primary_obj = {"text": "Complete the mission.", "archetype": setup.archetype.replace("_", " ").title(), "success_spectrum_label": "PRIMARY OBJECTIVE"}

    # Player force unit list — aggregate by type
    unit_counts: dict = {}
    for fu in setup.player_force.units:
        key = fu.unit_type
        if key not in unit_counts:
            unit_counts[key] = {"type_abstract": key.lower(), "type_display_name": key, "category": UNIT_CATEGORIES.get(key, "line"), "count": 0}
        unit_counts[key]["count"] += 1
    parity_pct = int(100 * setup.player_force.total_power / max(enemy_power, 1))

    # Region state bars
    region_fields = {}
    if region:
        region_fields = {
            "name": region_name,
            "tier": getattr(region, "tier", "Frontier"),
            "economy": {"value": int(region.fields.get("economy", 50)), "max": 100},
            "military": {"value": int(region.fields.get("military", 50)), "max": 100},
            "tension": {"value": int(region.fields.get("tension", 50)), "max": 100},
        }
    else:
        region_fields = {"name": "Unknown", "tier": "Frontier", "economy": {"value": 50, "max": 100}, "military": {"value": 50, "max": 100}, "tension": {"value": 50, "max": 100}}

    # Commander lineage
    lineage_data = {"name": "Commander", "generation_number": 1, "predecessor_name": "", "predecessor_status": ""}
    if cmdr_selection:
        lineage_data["name"] = cmdr_selection.character_name or "Commander"
        lineage_data["generation_number"] = cmdr_selection.chapter_number or 1
        ledger = sim_env.get("ledger")
        if ledger and cmdr_selection.lineage_id:
            history = ledger.get_lineage_history(cmdr_selection.lineage_id) if hasattr(ledger, "get_lineage_history") else []
            if len(history) > 1:
                prev_char = ledger.get_character_by_id(history[-2]) if hasattr(ledger, "get_character_by_id") and len(history) >= 2 else None
                if prev_char:
                    lineage_data["predecessor_name"] = getattr(prev_char, "name", "")
                    lineage_data["predecessor_status"] = "Retired" if getattr(prev_char, "alive", True) else "KIA"

    # Reinforcement note
    reinforce_note = ""
    if setup.reinforcements and setup.reinforcements.structure_count > 0:
        reinforce_note = "%d production structures in the area (%d allied, %d hostile, %d contested)." % (
            setup.reinforcements.structure_count,
            setup.reinforcements.player_structures,
            setup.reinforcements.enemy_structures,
            setup.reinforcements.neutral_structures,
        )

    gen_state = sim_env.get("gen_state")
    chapter_num = gen_state.chapter_count if gen_state else 1

    return {
        "mission_id_label": "OP-%04d" % sim_env.get("current_tick", 0),
        "chapter": chapter_num,
        "generation": cmdr_selection.chapter_number if cmdr_selection else 1,
        "era_id": "settled_reach",
        "mission_title": title,
        "mission_subtitle": subtitle,
        "tick_counter": sim_env.get("current_tick", 0),
        "situation_text": situation_text,
        "objective_primary": primary_obj,
        "objectives_secondary": secondary_objs,
        "enemy_assessment": {
            "faction_name": enemy_name,
            "archetype_label": setup.archetype.replace("_", " ").upper(),
            "military_stat": min(100, int(enemy_power / 10)),
            "military_stat_max": 100,
            "tech_tier": 1,
            "behavior_tag": ARCHETYPE_BEHAVIOR_TAGS.get(setup.archetype, "ACTIVE"),
        },
        "player_force": {
            "parity_percentage": parity_pct,
            "units": list(unit_counts.values()),
        },
        "region_state": region_fields,
        "commander_lineage": lineage_data,
        "reinforcement_note": reinforce_note,
    }


def _generate_and_build_engine(sim_env, logger):
    """Run the mission generator against current world state, build a TacticalEngine from the result."""
    from mission_generator import generate_mission
    from force_allocator import allocate_forces
    from map_generator import generate_map
    from map_gen_contracts import GeneratorInput, RegionState
    from layout_library import load_all_layouts
    from tactical_engine import TacticalEngine
    from tactical_map import TacticalMap
    from objectives import Objective, compute_time_limit
    from reinforcement import ReinforcementStructure
    from power_rating import compute_power_rating
    from unit import FIELD_HP
    from generational import run_character_selection
    import config as _cfg

    world = sim_env["world"]
    registry = sim_env["registry"]
    player_fid = sim_env["player_fid"]
    current_tick = sim_env.get("current_tick", 0)
    rng = world.rng

    mission_raw = generate_mission(
        world=world,
        registry=registry,
        player_faction_id=player_fid,
        event_log=sim_env.get("event_log", []),
        action_log=sim_env.get("action_log", []),
        conquest_log=sim_env.get("conquest_log", []),
        current_tick=current_tick,
        difficulty=sim_env.get("difficulty", "medium"),
        rng=rng,
        ledger=sim_env.get("ledger"),
        current_lineage_id=sim_env.get("player_lineage_id"),
        player_preferences=sim_env.get("player_preferences"),
    )

    if mission_raw is None:
        logger.warning("mission generator returned None — building fallback assault mission")
        mission_raw = _build_fallback_mission(sim_env, rng, logger)

    setup = mission_raw["setup"]
    archetype = setup.archetype
    logger.info("mission selected: archetype=%s region=%s score=%.3f",
                archetype, setup.region_id, setup.metadata.get("score", 0))

    # Commander selection — runs after mission generator per bible
    cmdr_selection = None
    gen_state = sim_env.get("gen_state")
    ledger = sim_env.get("ledger")
    if gen_state and ledger:
        cmdr_selection = run_character_selection(
            gen_state, ledger, world, setup, rng, current_tick,
            current_lineage_id=sim_env.get("player_lineage_id"),
        )
        if cmdr_selection and cmdr_selection.lineage_id:
            sim_env["player_lineage_id"] = cmdr_selection.lineage_id
        logger.info("commander: %s (lineage=%s, rotation=%s)",
                     cmdr_selection.character_name if cmdr_selection else "none",
                     cmdr_selection.lineage_id if cmdr_selection else "none",
                     cmdr_selection.rotation_reason if cmdr_selection else "none")

    # Build tactical map
    region = world.regions.get(setup.region_id)
    region_state = RegionState(
        stability=region.composites.get("stability", 50.0) if hasattr(region, "composites") else 50.0,
        capacity=region.composites.get("capacity", 0.5) if hasattr(region, "composites") else 0.5,
        economy=region.fields.get("economy", 50.0),
        tension=region.fields.get("tension", 50.0),
        military=region.fields.get("military", 50.0),
        population=region.fields.get("population", 50.0),
        region_id=region.id,
        tier=getattr(region, "tier", 0),
    )
    canvas_size = _cfg.ARCHETYPE_BASE_CANVAS.get(archetype, "medium")
    # See also: simulation/mission_generator.py — seed source; current_tick fallback only for pre-Stage-11b saves
    map_seed = setup.map_params.get("seed", current_tick)
    seed_source = "map_params" if "seed" in setup.map_params else "current_tick_fallback"
    logger.debug("map gen seed=%d source=%s", map_seed, seed_source)
    gen_input = GeneratorInput(archetype=archetype, region_state=region_state,
                                canvas_size=canvas_size, seed=map_seed)
    layout_lib = load_all_layouts()

    try:
        map_result = generate_map(gen_input, layout_lib)
        tmap = map_result.tactical_map
        logger.info("map generated: layout=%s, size=%dx%d", map_result.chosen_layout_id, tmap.width, tmap.height)
    except Exception as e:
        logger.error("map generation failed (%s), falling back to open field", e)
        tmap = TacticalMap(width=4000, height=4000, layers=1, spine_nodes=[], gradient_sources=[])

    # Create engine
    eng = TacticalEngine(tmap, seed=current_tick)
    eng.player_faction = 0
    eng.mission_id = setup.mission_id
    eng.archetype = archetype

    region_fields = {
        "military": region.fields.get("military", 50.0),
        "tension": region.fields.get("tension", 50.0),
        "economy": region.fields.get("economy", 50.0),
        "population": region.fields.get("population", 50.0),
    }
    eng.region_fields = region_fields

    # Spawn player units (faction 0) — bottom of map
    map_w, map_h = tmap.width, tmap.height
    cols = 10
    player_units = setup.player_force.units
    for i, fu in enumerate(player_units):
        x = map_w * 0.1 + (i % cols) * 180.0
        y = map_h * 0.1 + (i // cols) * 120.0
        eng.store.spawn(fu.unit_type, 0, x, y)

    # Spawn enemy units (faction 1) — top of map
    enemy_units = setup.enemy_forces[0].units if setup.enemy_forces else []
    for i, fu in enumerate(enemy_units):
        x = map_w * 0.1 + (i % cols) * 180.0
        y = map_h * 0.9 - (i // cols) * 120.0
        eng.store.spawn(fu.unit_type, 1, x, y)

    # Compute initial player power for outcome scoring
    player_power = 0.0
    for uid in eng.store.active_ids_for_faction(0):
        stats = _cfg.UNIT_STATS.get(eng.store.unit_type[uid])
        if stats:
            s = dict(stats)
            s["unit_type"] = eng.store.unit_type[uid]
            player_power += compute_power_rating(s)
    eng.initial_power = player_power

    # See also: simulation/mission_generator.py:_build_objectives — fills static params;
    # this fills runtime-known params (enemy HP, zone coords, escort UIDs).
    enemy_hp = sum(eng.store.data[uid, FIELD_HP] for uid in eng.store.active_ids_for_faction(1))
    eng.objectives = []
    for obj_spec in setup.objectives:
        params = dict(obj_spec.params)
        if obj_spec.type == "eliminate_force":
            params.setdefault("enemy_faction", 1)
            params.setdefault("initial_enemy_hp", enemy_hp)
        elif obj_spec.type == "hold_zone":
            params.setdefault("zone_x", map_w * 0.5)
            params.setdefault("zone_y", map_h * 0.5)
        elif obj_spec.type == "escort_to_extraction":
            params.setdefault("extraction_x", map_w * 0.1)
            params.setdefault("extraction_y", map_h * 0.9)
            params.setdefault("escort_uids", [uid for uid in eng.store.active_ids_for_faction(0)])
        eng.objectives.append(Objective(
            obj_spec.id, obj_spec.type, obj_spec.weight, params, is_primary=obj_spec.is_primary))

    # Time limit — urgency-scaled per bible
    urgency = setup.metadata.get("urgency", 0.0)
    eng.time_limit_ticks = compute_time_limit(archetype, urgency)

    # Commander UID (first player unit)
    player_ids = eng.store.active_ids_for_faction(0)
    eng.commander_uid = player_ids[0] if player_ids else None

    # Behavior scripts for enemy AI
    if _cfg.ENABLE_BEHAVIOR_SCRIPTS:
        try:
            from script_loader import load_script
            from behavior_runner import BehaviorRunner
            from trigger_bus import TriggerBus
            script = load_script(archetype)
            bus = TriggerBus()
            runner = BehaviorRunner(
                script, tmap, bus, rng, faction_id=1,
                mission_start_tick=0, time_limit_ticks=eng.time_limit_ticks)
            eng.behavior_runners = [runner]
            logger.info("behavior script loaded for archetype=%s", archetype)
        except Exception as e:
            logger.warning("failed to load behavior script for %s: %s", archetype, e)

    # Reinforcement structures — placed at spine node positions so terrain_renderer
    # can match them for 3D model rendering.
    # See also: scenes/tactical/terrain_renderer.gd:_build_structure_node — matches by position key.
    eng.reinforcement_structures = []
    reinf_spine = [sn for sn in tmap.spine_nodes if sn.node_type == "reinforcement_structure"]
    _OWNER_MAP = {"player": 0, "enemy": 1, "neutral": -1}
    for struct_id, sn in enumerate(reinf_spine):
        owner = _OWNER_MAP.get(sn.properties.get("initial_owner", "neutral"), -1)
        eng.reinforcement_structures.append(ReinforcementStructure(
            structure_uid=struct_id,
            position=sn.position,
            layer=int(sn.properties.get("layer", 0)),
            hp=_cfg.REINFORCEMENT_STRUCTURE_HP,
            max_hp=_cfg.REINFORCEMENT_STRUCTURE_HP,
            owner_faction=owner,
            capture_progress=0.0,
            production_timer_sec=0.0,
            production_target_unit_type="Raider",
            capture_radius=_cfg.REINFORCEMENT_CAPTURE_RADIUS,
        ))

    # Build and attach the rich briefing data
    eng.mission_briefing_data = _mission_setup_to_briefing(setup, sim_env, cmdr_selection)

    # Store mission info for chronicle use in next time jump
    sim_env["mission_info"] = {
        "mission_id": setup.mission_id,
        "archetype": archetype,
        "region_id": setup.region_id,
    }
    sim_env["last_mission_region"] = setup.region_id

    logger.info("engine built: %d player units, %d enemy units, time_limit=%d, reinforcements=%d",
                len(player_units), len(enemy_units), eng.time_limit_ticks, len(eng.reinforcement_structures))
    return eng


def _build_fallback_mission(sim_env, rng, logger):
    """Build a minimal assault mission when no triggers fire."""
    from force_allocator import allocate_forces
    from mission_briefing import assemble_briefing
    from mission_contracts import MissionSetup, ObjectiveSpec
    from mission_generator import _build_variable_slots, ARCHETYPE_OBJECTIVES
    import config as _cfg

    world = sim_env["world"]
    registry = sim_env["registry"]
    player_fid = sim_env["player_fid"]
    current_tick = sim_env.get("current_tick", 0)

    # Find a hostile-adjacent region to attack
    player_regions = [r for r in world.regions.values() if r.faction_id == player_fid]
    target_region = None
    for pr in player_regions:
        for nid in world.get_neighbors(pr.id):
            neighbor = world.regions.get(nid)
            if neighbor and neighbor.faction_id and neighbor.faction_id != player_fid:
                target_region = neighbor
                break
        if target_region:
            break

    if not target_region:
        # No hostile neighbor — pick any non-player region
        for r in world.regions.values():
            if r.faction_id != player_fid:
                target_region = r
                break
    if not target_region:
        target_region = player_regions[0] if player_regions else list(world.regions.values())[0]

    archetype = "assault"
    capacity = target_region.composites.get("capacity", 0.5) if hasattr(target_region, "composites") else 0.5
    capacity_norm = capacity / 100.0 if capacity > 1.0 else capacity

    enemy_fid = target_region.faction_id or "enemy"
    allocation = allocate_forces(archetype, {}, target_region, capacity_norm,
                                  sim_env.get("difficulty", "medium"),
                                  player_fid, enemy_fid, rng)

    objectives = []
    for i, (obj_type, weight, is_primary) in enumerate(ARCHETYPE_OBJECTIVES.get(archetype, [("generic_objective", 1.0, True)])):
        objectives.append(ObjectiveSpec(
            id=f"obj_{archetype}_{i}", type=obj_type, weight=weight, params={}, is_primary=is_primary))

    variable_slots = _build_variable_slots(
        {"archetype": archetype, "trigger_context": {}, "region_id": target_region.id},
        target_region, world, registry, player_fid)
    variable_slots["player_units"] = len(allocation["player_force"].units)
    variable_slots["enemy_units"] = len(allocation["enemy_force"].units)
    variable_slots["player_power"] = allocation["player_force"].total_power
    variable_slots["enemy_power"] = allocation["enemy_force"].total_power
    variable_slots["parity_ratio"] = allocation["parity_ratio"]
    variable_slots["shortfall_types"] = allocation["shortfall_types"]
    variable_slots["reinforcements"] = allocation["reinforcements"]

    briefing = assemble_briefing(archetype, variable_slots)
    mission_id = f"mission_{archetype}_{target_region.id}_{current_tick}"

    # See also: simulation/mission_generator.py — seed source for non-fallback missions
    map_seed = rng.randint(0, 2**31 - 1)
    setup = MissionSetup(
        mission_id=mission_id,
        archetype=archetype,
        region_id=target_region.id,
        map_params={"seed": map_seed},
        player_force=allocation["player_force"],
        enemy_forces=[allocation["enemy_force"]],
        objectives=objectives,
        reinforcements=allocation["reinforcements"],
        time_limit_ticks=_cfg.ARCHETYPE_TIME_LIMITS.get(archetype, 300),
        behavior_script_id=f"behavior_{archetype}",
        briefing=briefing,
        difficulty=sim_env.get("difficulty", "medium"),
        metadata={"score": 0.0, "urgency": 0.0, "relevance": 0.0, "preference": 0.5},
    )

    logger.info("fallback mission: assault on %s", target_region.id)
    return {"setup": setup, "scored_candidates": [], "selected": None, "allocation": allocation}


def _send_message(msg: dict):
    """Write one length-prefixed JSON message to real stdout."""
    encoded = json.dumps(msg).encode("utf-8")
    _real_stdout_buffer.write(struct.pack(">I", len(encoded)) + encoded)
    _real_stdout_buffer.flush()


def _read_message(buf) -> dict | None:
    """Read one length-prefixed JSON message from a binary buffer. Returns None on EOF."""
    header = buf.read(4)
    if len(header) < 4:
        return None
    length = struct.unpack(">I", header)[0]
    body = buf.read(length)
    if len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


def _stdin_reader(cmd_queue: queue.Queue, cmd_file_path: str | None = None):
    """Background thread: reads commands from stdin or polls a command file."""
    if cmd_file_path:
        _file_cmd_reader(cmd_queue, cmd_file_path)
    else:
        buf = sys.stdin.buffer
        while True:
            msg = _read_message(buf)
            if msg is None:
                cmd_queue.put(None)
                break
            cmd_queue.put(msg)


def _file_cmd_reader(cmd_queue: queue.Queue, path: str):
    """Poll a newline-delimited JSON file for commands."""
    logger = logging.getLogger(__name__)
    while not os.path.exists(path):
        time.sleep(0.05)
    f = open(path, "r", encoding="utf-8")
    while True:
        line = f.readline()
        if line.strip():
            try:
                msg = json.loads(line)
                logger.info("cmd file: received %s", msg.get("cmd", msg.get("type", "?")))
                cmd_queue.put(msg)
            except json.JSONDecodeError:
                pass
        else:
            time.sleep(0.05)


LIFECYCLE_CMDS = {"proceed_to_next_mission", "continue_from_debrief", "ready_for_time_jump", "ready_for_tactical"}


def _drain_commands(cmd_queue, engine, logger):
    """Drain all pending commands. Returns a lifecycle command string if one arrived, else None."""
    import command_ingest
    lifecycle_cmd = None
    while True:
        try:
            pkt = cmd_queue.get_nowait()
            if pkt is None:
                return "eof"
            cmd_str = pkt.get("cmd", "")
            if cmd_str in LIFECYCLE_CMDS:
                logger.info("lifecycle command: %s", cmd_str)
                lifecycle_cmd = cmd_str
            else:
                logger.info("command received: type=%s kind=%s", pkt.get("type"), pkt.get("command", {}).get("kind") if isinstance(pkt.get("command"), dict) else cmd_str)
                command_ingest.ingest(pkt, engine)
        except queue.Empty:
            break
    return lifecycle_cmd


def _wait_for_command(cmd_queue, target_cmd, engine, logger, timeout=None):
    """Block until a specific lifecycle command arrives. Tactical commands are still processed.
    Sends periodic heartbeats so the Godot reader thread unblocks and can flush outgoing commands."""
    import command_ingest
    deadline = time.monotonic() + timeout if timeout else None
    heartbeat_interval = 0.2
    next_heartbeat = time.monotonic() + heartbeat_interval
    while True:
        now = time.monotonic()
        if now >= next_heartbeat:
            _send_message({"type": "heartbeat"})
            next_heartbeat = now + heartbeat_interval
        wait_time = 0.05
        if deadline:
            remaining = deadline - now
            if remaining <= 0:
                return None
            wait_time = min(wait_time, remaining)
        try:
            pkt = cmd_queue.get(timeout=wait_time)
            if pkt is None:
                return "eof"
            cmd_str = pkt.get("cmd", "")
            if cmd_str == target_cmd:
                logger.info("received expected command: %s", target_cmd)
                return target_cmd
            if cmd_str in LIFECYCLE_CMDS:
                logger.info("lifecycle command (unexpected during wait for %s): %s", target_cmd, cmd_str)
                if cmd_str == target_cmd:
                    return cmd_str
            else:
                if engine is not None:
                    command_ingest.ingest(pkt, engine)
        except queue.Empty:
            continue


def _run_tactical_phase(engine, cmd_queue, logger):
    """Run the tactical tick loop until mission ends or stdin closes. Returns 'terminal' or 'eof'."""
    from snapshot_serializer import full_snapshot, delta, delta_baseline, DeadReckoningTracker
    import config as _config

    dr_tracker = DeadReckoningTracker()
    prev_state = full_snapshot(engine)
    _send_message(prev_state)
    _send_message({
        "type": "sim_state",
        "mission_briefing": _build_mission_briefing(engine, prev_state, getattr(engine, "player_faction", 0)),
    })

    tick_interval = 1.0 / _config.TICK_HZ
    next_snap_at = time.monotonic() + _config.SNAPSHOT_INTERVAL_SEC
    tick_num = 0
    start_time = time.monotonic()

    while True:
        lc = _drain_commands(cmd_queue, engine, logger)
        if lc == "eof":
            return "eof"

        engine.step()

        if engine.is_terminal():
            snap = full_snapshot(engine)
            _send_message(snap)
            logger.info("mission terminal at tick %d, winner=%s", engine.tick, engine.get_winner())
            return "terminal"

        now = time.monotonic()
        if now >= next_snap_at:
            pkt = full_snapshot(engine)
            dr_tracker.reset()
            next_snap_at += _config.SNAPSHOT_INTERVAL_SEC
        else:
            pkt = delta(engine, prev_state, dr_tracker)

        prev_state = delta_baseline(engine)
        _send_message(pkt)

        tick_num += 1
        sleep_for = (start_time + tick_num * tick_interval) - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)


def _build_debrief_payload(engine):
    """Build the debrief dict that the Godot debrief scene expects."""
    from objectives import build_mission_result
    from debrief_data import assemble_debrief

    player_faction = getattr(engine, "player_faction", 0)
    mission_id = getattr(engine, "mission_id", "mission_unknown")
    archetype = getattr(engine, "archetype", "assault")
    objectives = getattr(engine, "objectives", [])
    initial_power = getattr(engine, "initial_power", 1.0)
    commander_uid = getattr(engine, "commander_uid", None)

    mission_result = build_mission_result(
        mission_id, objectives, engine.store, player_faction,
        initial_power, archetype, engine.tick, commander_uid)

    region_fields = getattr(engine, "region_fields", {
        "military": 60.0, "tension": 50.0, "economy": 50.0, "population": 50.0,
    })

    return assemble_debrief(mission_result, archetype, region_fields)


def _run_debrief_phase(engine, cmd_queue, logger, debrief=None):
    """Send debrief data and wait for continue_from_debrief. Returns 'continue' or 'eof'."""
    if debrief is None:
        debrief = _build_debrief_payload(engine)
    _send_message({"type": "debrief", **debrief})
    logger.info("sent debrief, band=%s", debrief.get("outcome_band"))

    result = _wait_for_command(cmd_queue, "continue_from_debrief", engine, logger)
    if result == "eof":
        return "eof"
    return "continue"


def _run_time_jump_phase(sim_env, cmd_queue, engine, logger):
    """Wait for sequencer ready signal, run time jump, send messages. Returns 'done' or 'eof'."""
    from time_jump import run_time_jump
    from world_view.time_jump_emitter import build_time_jump_messages
    import config as _config

    result = _wait_for_command(cmd_queue, "ready_for_time_jump", engine, logger, timeout=10.0)
    if result == "eof":
        return "eof"
    if result is None:
        logger.warning("timeout waiting for ready_for_time_jump, proceeding anyway")

    chapter = sim_env.get("chapter_num", 1)
    tj_id = f"tj_{chapter:04d}"

    tj_result = run_time_jump(
        sim_env["world"],
        _config.TIME_JUMP_TICKS_PER_CHAPTER,
        sim_env["registry"],
        sim_env["pending_queue"],
        sim_env["noise_offsets"],
        sim_env["trigger_state"],
        sim_env.get("stances", {}),
        sim_env.get("pending_telegraphs", []),
        sim_env["world"].rng,
        start_tick=sim_env.get("current_tick", 0),
        coherence_ledger=sim_env.get("ledger"),
        naming_system=sim_env.get("ns"),
        player_lineage_id=sim_env.get("player_lineage_id"),
        last_mission_region=sim_env.get("last_mission_region"),
        last_mission_outcome=sim_env.get("last_mission_outcome"),
        mission_info=sim_env.get("mission_info"),
    )

    sim_env["current_tick"] = tj_result["end_tick"]

    # Accumulate logs for mission generator triggers
    sim_env.setdefault("event_log", []).extend(tj_result.get("events", []))
    sim_env.setdefault("action_log", []).extend(tj_result.get("faction_actions", []))
    sim_env.setdefault("conquest_log", []).extend(tj_result.get("conquests", []))

    scroll_entries = tj_result.get("scroll_entries", [])
    events_total = tj_result.get("events_total", 0)
    logger.info("time jump result: %d events, %d scroll entries, %d territory changes, %d conquests",
                events_total, len(scroll_entries), len(tj_result.get("territory_changes", [])),
                len(tj_result.get("conquests", [])))
    for i, se in enumerate(scroll_entries):
        logger.info("  scroll_entry[%d]: tick_range=%s text=%s", i, getattr(se, "tick_range", "?"), getattr(se, "base_text", "?")[:80])

    messages = build_time_jump_messages(tj_result, tj_id)
    msg_types = {}
    for msg in messages:
        t = msg.get("type", "?")
        msg_types[t] = msg_types.get(t, 0) + 1
    logger.info("sending %d time jump messages for %s: %s", len(messages), tj_id, msg_types)
    for msg in messages:
        _send_message(msg)

    return "done"


def _run_opening_time_jump(sim_env, logger):
    """Run the opening time jump and send messages. Called after ready_for_time_jump is received."""
    from time_jump import run_time_jump
    from world_view.time_jump_emitter import build_time_jump_messages
    import config as _config

    tj_id = "tj_opening"

    tj_result = run_time_jump(
        sim_env["world"],
        _config.TIME_JUMP_TICKS_PER_CHAPTER,
        sim_env["registry"],
        sim_env["pending_queue"],
        sim_env["noise_offsets"],
        sim_env["trigger_state"],
        sim_env.get("stances", {}),
        sim_env.get("pending_telegraphs", []),
        sim_env["world"].rng,
        start_tick=0,
        coherence_ledger=sim_env.get("ledger"),
        naming_system=sim_env.get("ns"),
        player_lineage_id=sim_env.get("player_lineage_id"),
    )

    sim_env["current_tick"] = tj_result["end_tick"]

    sim_env.setdefault("event_log", []).extend(tj_result.get("events", []))
    sim_env.setdefault("action_log", []).extend(tj_result.get("faction_actions", []))
    sim_env.setdefault("conquest_log", []).extend(tj_result.get("conquests", []))

    scroll_entries = tj_result.get("scroll_entries", [])
    events_total = tj_result.get("events_total", 0)
    logger.info("opening time jump: %d events, %d scroll entries, %d territory changes",
                events_total, len(scroll_entries), len(tj_result.get("territory_changes", [])))

    messages = build_time_jump_messages(tj_result, tj_id)
    logger.info("sending %d opening time jump messages", len(messages))
    for msg in messages:
        _send_message(msg)


def _run_waiting_phase(cmd_queue, engine, logger):
    """Wait for proceed_to_next_mission. Returns 'proceed' or 'eof'."""
    result = _wait_for_command(cmd_queue, "proceed_to_next_mission", engine, logger)
    if result == "eof":
        return "eof"
    return "proceed"


def run(engine_factory, *, sim_env=None, crash_after_ready: bool = False, test_print: bool = False, cmd_file_path: str | None = None, use_mission_generator: bool = True):
    """
    Main entry point for the pipe transport game loop.
    engine_factory: callable() → TacticalEngine (first mission, used when use_mission_generator=False)
    sim_env: dict with world, registry, ledger, etc. for time jumps.
             If None, time jumps are skipped (single-mission mode).
    use_mission_generator: when True and sim_env is provided, generates real missions
                           from world state. When False, uses engine_factory for all missions.
    """
    _setup_io()
    _install_crash_handler()

    logger = logging.getLogger(__name__)
    logger.info("pipe transport starting, version=%s", SIM_VERSION)

    _send_message({"type": "progress", "step": "loading_config", "pct": 0.2})
    _send_message({"type": "progress", "step": "initializing_simulation", "pct": 0.4})

    if sim_env is not None and use_mission_generator:
        engine = None  # built after opening time jump
    else:
        engine = engine_factory()

    _send_message({"type": "progress", "step": "building_world", "pct": 0.8})

    if test_print:
        print("debug_intercept_test")  # intentional — tests that _StdoutTrap intercepts this

    _send_message({"type": "ready", "version": SIM_VERSION})
    logger.info("sent ready message")

    if crash_after_ready:
        raise RuntimeError("deliberate crash for pipe transport crash-handler test")

    cmd_queue = queue.Queue()
    reader = threading.Thread(target=_stdin_reader, args=(cmd_queue, cmd_file_path), daemon=True)
    reader.start()
    if cmd_file_path:
        logger.info("reading commands from file: %s", cmd_file_path)

    chapter_num = 1

    # Opening time jump — bible: "generates the starting world and immediately runs a time jump"
    # The player sees an abbreviated opening chronicle scroll before their first mission.
    # No timeout: the player may spend time in menus before reaching the time_jump scene.
    if sim_env is not None and use_mission_generator:
        sim_env["chapter_num"] = 0  # opening jump is chapter 0
        logger.info("=== OPENING TIME JUMP (waiting for sequencer) ===")
        result = _wait_for_command(cmd_queue, "ready_for_time_jump", engine, logger)
        if result == "eof":
            logger.info("stdin closed waiting for opening time jump ready")
            return

        _run_opening_time_jump(sim_env, logger)

        logger.info("=== WAITING FOR OPENING SCROLL ===")
        result = _run_waiting_phase(cmd_queue, engine, logger)
        if result == "eof":
            logger.info("stdin closed during opening scroll wait")
            return

        engine = _generate_and_build_engine(sim_env, logger)
        logger.info("first mission generated from post-jump world state")
        _send_message({"type": "next_mission", "chapter": chapter_num})
        if hasattr(engine, "mission_briefing_data") and engine.mission_briefing_data:
            _send_message({"type": "sim_state", "mission_briefing": engine.mission_briefing_data})

    result = _wait_for_command(cmd_queue, "ready_for_tactical", engine, logger, timeout=30.0)
    if result == "eof":
        logger.info("stdin closed waiting for initial ready_for_tactical")
        return
    if result is None:
        logger.warning("timeout waiting for initial ready_for_tactical, proceeding anyway")

    while True:
        logger.info("=== TACTICAL PHASE (chapter %d) ===", chapter_num)
        result = _run_tactical_phase(engine, cmd_queue, logger)
        if result == "eof":
            logger.info("stdin closed during tactical phase")
            return

        logger.info("=== DEBRIEF PHASE ===")
        debrief_data = _build_debrief_payload(engine)
        result = _run_debrief_phase(engine, cmd_queue, logger, debrief_data)
        if result == "eof":
            logger.info("stdin closed during debrief phase")
            return

        if sim_env is not None:
            sim_env["last_mission_outcome"] = debrief_data.get("outcome_band", "partial_success")
            sim_env["chapter_num"] = chapter_num
            logger.info("=== TIME JUMP PHASE ===")
            result = _run_time_jump_phase(sim_env, cmd_queue, engine, logger)
            if result == "eof":
                logger.info("stdin closed during time jump phase")
                return

            logger.info("=== WAITING PHASE ===")
            result = _run_waiting_phase(cmd_queue, engine, logger)
            if result == "eof":
                logger.info("stdin closed during waiting phase")
                return

            chapter_num += 1
            if use_mission_generator:
                engine = _generate_and_build_engine(sim_env, logger)
            else:
                engine = engine_factory()
            logger.info("new engine created for chapter %d", chapter_num)
            _send_message({"type": "next_mission", "chapter": chapter_num})
            if hasattr(engine, "mission_briefing_data") and engine.mission_briefing_data:
                _send_message({"type": "sim_state", "mission_briefing": engine.mission_briefing_data})

            result = _wait_for_command(cmd_queue, "ready_for_tactical", engine, logger, timeout=10.0)
            if result == "eof":
                logger.info("stdin closed waiting for tactical ready")
                return
            if result is None:
                logger.warning("timeout waiting for ready_for_tactical, proceeding anyway")
        else:
            # No sim environment — single-mission mode, exit after debrief
            logger.info("no sim_env, exiting after debrief")
            return


def _setup_sim_env(seed=42):
    import world as world_mod
    import faction as faction_mod
    import events as _events
    import naming_system as _naming_mod
    import coherence_ledger as _ledger_mod
    from generational import GenerationalState
    import config as _cfg

    _cfg.ENABLE_EVENTS = True
    _cfg.ENABLE_FACTIONS = True
    _cfg.ENABLE_BORDER_FRICTION = True
    _cfg.ENABLE_RECRUITMENT = True
    _cfg.ENABLE_ADJACENCY_BONUS = True
    _cfg.ENABLE_OSCILLATION = True
    _cfg.ENABLE_TECHNOLOGY = False
    _cfg.ENABLE_DIPLOMACY = False

    w = world_mod.generate_random(seed=seed)
    factions = faction_mod.generate_starting_factions(rng=w.rng, world=w)
    registry = faction_mod.make_registry(*factions)

    ns = _naming_mod.NamingSystem()
    library_path = os.path.join(os.path.dirname(__file__), "library", "naming", "names.json")
    if os.path.exists(library_path):
        with open(library_path) as _lf:
            _lib_names = json.load(_lf)
        for fid, fac in registry.items():
            lib_entry = _lib_names.get(fid) or _lib_names.get(fac.archetype, {})
            for cat in ["people", "places", "factions"]:
                names = lib_entry.get(cat, [])
                if names:
                    ns.load_pool(fid, cat, names)
                else:
                    ns.ensure_pool(fid, cat)
    else:
        for fid in registry:
            for cat in ["people", "places", "factions"]:
                ns.ensure_pool(fid, cat)
    for fid, fac in registry.items():
        display_name = ns.get_name(fid, "factions", current_tick=0, rng=w.rng)
        if display_name:
            fac.name = display_name

    # Assign region names from library "places" pools
    _all_neutral_places = set()
    for fid in registry:
        _all_neutral_places.update(ns._pools.get((fid, "places"), []))
    ns.load_pool("neutral", "places", list(_all_neutral_places))

    for region in w.regions.values():
        pool_key = region.faction_id if region.faction_id else "neutral"
        name = ns.get_name(pool_key, "places", current_tick=0, rng=w.rng)
        if name:
            region.name = name

    ledger = _ledger_mod.CoherenceLedger(ns)
    for fid in registry:
        home_regions = [r for r in w.regions.values() if r.faction_id == fid]
        if home_regions:
            ledger.assign_faction_leader(fid, home_regions[0].id, 0, w.rng)

    noise_offsets = _events.roll_noise_offsets(list(w.regions.keys()), w.rng)
    pending_queue = _events.PendingQueue()

    player_fid = None
    for fid, fac in registry.items():
        if fac.archetype == "player_civilization":
            player_fid = fid
            break
    if not player_fid:
        player_fid = list(registry.keys())[0]

    leader = ledger.get_faction_leader(player_fid)
    player_lineage_id = ledger.create_lineage(leader.id) if leader else None

    gen_state = GenerationalState(player_fid, start_tick=0)
    if leader and player_lineage_id:
        gen_state.current_chapter["character_id"] = leader.id
        ledger.increment_chapter(player_lineage_id)

    return {
        "world": w,
        "registry": registry,
        "ledger": ledger,
        "ns": ns,
        "noise_offsets": noise_offsets,
        "trigger_state": {},
        "pending_queue": pending_queue,
        "player_fid": player_fid,
        "player_lineage_id": player_lineage_id,
        "gen_state": gen_state,
        "stances": {},
        "pending_telegraphs": [],
        "current_tick": 0,
        "event_log": [],
        "action_log": [],
        "conquest_log": [],
        "difficulty": "medium",
    }


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Stage 13 — when run from a frozen/exported build, Godot passes
    # `--root <game_root>` so file I/O (logs/, saves, crash report) lands next
    # to the game executable instead of inside the PyInstaller bundle. In dev
    # mode (running this file directly with Python) `--root` is absent and we
    # fall through to os.getcwd(). This must happen before _setup_io() runs,
    # since that creates logs/ and opens the stderr log file.
    if "--root" in sys.argv:
        _root = sys.argv[sys.argv.index("--root") + 1]
        try:
            os.chdir(_root)
        except OSError as _e:
            sys.stderr.write(f"[pipe] failed to chdir to --root {_root!r}: {_e}\n")

    import config
    from tactical_engine import TacticalEngine
    from tactical_map import TacticalMap, SpineNode, GradientSource
    from reinforcement import ReinforcementStructure
    from command import Command

    _crash = "--crash" in sys.argv
    _test_print = "--test-print" in sys.argv
    _cmd_file = None
    if "--cmd-file" in sys.argv:
        _cmd_file = sys.argv[sys.argv.index("--cmd-file") + 1]

    UNIT_ROSTER = ["Vanguard", "Vanguard", "Vanguard", "Warden",
                   "Raider", "Raider", "Interceptor", "Interceptor",
                   "Bombard", "Bastion"]
    UNITS_PER_SIDE = int(sys.argv[sys.argv.index("--units") + 1]) if "--units" in sys.argv else 50

    def _make_engine():
        map_size = 2000 if UNITS_PER_SIDE <= 5 else 4000
        tmap = TacticalMap(
            width=map_size, height=map_size, layers=1,
            spine_nodes=[],
            gradient_sources=[],
        )
        eng = TacticalEngine(tmap, seed=42)
        eng.player_faction = 0
        eng.mission_id = "mission_001"
        eng.archetype = "assault"
        eng.region_fields = {"military": 60.0, "tension": 50.0, "economy": 50.0, "population": 50.0}

        if UNITS_PER_SIDE <= 5:
            cx = map_size / 2.0
            for i in range(UNITS_PER_SIDE):
                eng.store.spawn("Raider", 0, cx - 150.0, cx - 200.0 - i * 80.0)
                eng.store.spawn("Raider", 1, cx + 150.0, cx + 200.0 + i * 80.0)
        else:
            cols = 10
            for i in range(UNITS_PER_SIDE):
                ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
                x = 400.0 + (i % cols) * 180.0
                y = 400.0 + (i // cols) * 120.0
                eng.store.spawn(ut, 0, x, y)
            for i in range(UNITS_PER_SIDE):
                ut = UNIT_ROSTER[i % len(UNIT_ROSTER)]
                x = 400.0 + (i % cols) * 180.0
                y = 3600.0 - (i // cols) * 120.0
                eng.store.spawn(ut, 1, x, y)

        from power_rating import compute_power_rating
        from unit import FIELD_HP
        from objectives import Objective
        player_power = 0.0
        enemy_hp = 0.0
        for uid in eng.store.active_ids_for_faction(0):
            stats = config.UNIT_STATS.get(eng.store.unit_type[uid])
            if stats:
                s = dict(stats)
                s["unit_type"] = eng.store.unit_type[uid]
                player_power += compute_power_rating(s)
        for uid in eng.store.active_ids_for_faction(1):
            enemy_hp += eng.store.data[uid, FIELD_HP]
        eng.initial_power = player_power
        eng.objectives = [
            Objective("eliminate_enemy", "eliminate_force", 1.0,
                      {"enemy_faction": 1, "initial_enemy_hp": enemy_hp}, is_primary=True),
        ]

        a_ids = eng.store.active_ids_for_faction(0)
        eng.command_queue.add(Command(
            tick=0, type="attack_move", unit_ids=a_ids,
            params={"target_x": 2000.0, "target_y": 3600.0},
        ))
        b_ids = eng.store.active_ids_for_faction(1)
        eng.command_queue.add(Command(
            tick=0, type="attack_move", unit_ids=b_ids,
            params={"target_x": 2000.0, "target_y": 400.0},
        ))

        eng.reinforcement_structures = []
        return eng

    _sim_env = _setup_sim_env()
    _use_gen = "--real-missions" in sys.argv
    run(_make_engine, sim_env=_sim_env, crash_after_ready=_crash, test_print=_test_print, cmd_file_path=_cmd_file, use_mission_generator=_use_gen)
