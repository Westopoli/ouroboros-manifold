"""Auto-fires post-time-jump per BLOCKER 1 design (fork 1 + 4).

Called at the end of `_run_time_jump_phase` / `_run_opening_time_jump` in
pipe_transport. No Godot involvement on the trigger side — sim saves itself.
"""

import config
import save_writer
from save.world_serializer import serialize_world


def autosave_world_view(sim_env: dict) -> None:
    if not getattr(config, "ENABLE_STAGE12_AUTOSAVE", True):
        return
    world = sim_env["world"]
    factions = sim_env.get("registry", {})
    chronicle_entries = sim_env.get("chronicle_entries", [])
    tick = sim_env.get("current_tick", 0)
    era_id = sim_env.get("era_id", "settled_reach")
    stances = sim_env.get("stances", {})

    payload = serialize_world(
        world=world,
        factions=factions,
        chronicle_entries=chronicle_entries,
        tick=tick,
        era_id=era_id,
        stances=stances,
        naming_system=sim_env.get("ns"),
        ledger=sim_env.get("ledger"),
        gen_state=sim_env.get("gen_state"),
        pending_queue=sim_env.get("pending_queue"),
        player_lineage_id=sim_env.get("player_lineage_id"),
        trigger_state=sim_env.get("trigger_state", {}),
        noise_offsets=sim_env.get("noise_offsets", {}),
    )

    save_writer.write_sim_state(
        config.AUTOSAVE_SLOT_ID,
        {
            "chapter_number": sim_env.get("chapter_num", 0),
            "year": tick,
            "rng_state": "",
            "sim_state": payload,
            "last_time_jump_messages": sim_env.get("last_time_jump_messages", []),
        },
    )
