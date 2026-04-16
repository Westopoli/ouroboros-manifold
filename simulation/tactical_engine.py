import random
import numpy as np
import config
from unit import UnitStore, FIELD_HP
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import compute_visibility, update_fog_timers
from command import Command, CommandQueue, process_commands, compute_state_hash
from objectives import Objective, update_objectives, check_terminal, build_mission_result
from reinforcement import step_reinforcement
from spine_drift import update_drifting_nodes


class TacticalEngine:
    def __init__(self, tactical_map, store=None, seed=None):
        self.map = tactical_map
        self.store = store or UnitStore()
        self.tick = 0
        self.dt = config.TACTICAL_TICK_DURATION
        self.death_log = []
        self.rng = random.Random(seed)
        self.command_queue = CommandQueue()
        self.objectives = []
        self.player_faction = 0
        self.time_limit_ticks = 0
        self.initial_power = 0.0
        self.archetype = "defensive_stand"
        self.commander_uid = None
        self.event_log = []
        self.reinforcement_structures = []
        self.enable_reinforcement = True
        # Populated by the mission launcher when ENABLE_BEHAVIOR_SCRIPTS is on.
        # See also: behavior_runner.py — runner implementation.
        self.behavior_runners = []

    def step(self):
        if config.ENABLE_BEHAVIOR_SCRIPTS and self.behavior_runners:
            for runner in self.behavior_runners:
                runner.step(self.tick, self.store, self.command_queue)
        process_commands(self.command_queue, self.store, self.tick)
        update_targeting(self.store, self.map, self.rng)  # before movement so attack_move sees current targets
        update_movement(self.store, self.map, self.dt)
        deaths, kill_sources = resolve_damage(self.store, self.map, self.dt)

        barrage_events = update_abilities(self.store, self.dt)
        if barrage_events:
            b_deaths, b_kills = resolve_barrage(self.store, barrage_events)
            deaths.extend(b_deaths)
            kill_sources.update(b_kills)

        update_fog_timers(self.store)

        if self.map.drifting_nodes:
            update_drifting_nodes(self, self.tick)

        if self.enable_reinforcement and self.reinforcement_structures:
            step_reinforcement(self, self.dt)

        if self.objectives:
            update_objectives(self.objectives, self.store, self.player_faction, self.tick)

        if deaths:
            for uid in deaths:
                self.death_log.append({
                    "uid": uid,
                    "tick": self.tick,
                    "killer": kill_sources.get(uid, -1),
                })
        self.tick += 1

    def run(self, max_ticks):
        for _ in range(max_ticks):
            self.step()
            if self.is_terminal():
                break

    def run_mission(self, max_ticks=None):
        limit = max_ticks or self.time_limit_ticks or 30000
        for _ in range(limit):
            self.step()
            terminal = self._check_mission_terminal()
            if terminal:
                break
        return self.build_result()

    def _check_mission_terminal(self):
        if self.objectives:
            reason = check_terminal(
                self.objectives, self.store, self.player_faction,
                self.tick, self.time_limit_ticks,
            )
            if reason:
                return reason

        factions_alive = set()
        for uid in self.store.active_ids():
            factions_alive.add(self.store.faction[uid])
        if len(factions_alive) <= 1:
            return "combat_over"

        return None

    def build_result(self):
        return build_mission_result(
            mission_id="",
            objectives=self.objectives,
            store=self.store,
            player_faction=self.player_faction,
            initial_power=self.initial_power,
            archetype=self.archetype,
            tick=self.tick,
            commander_uid=self.commander_uid,
        )

    def is_terminal(self):
        factions_alive = set()
        for uid in self.store.active_ids():
            factions_alive.add(self.store.faction[uid])
            if len(factions_alive) > 1:
                return False
        return True

    def get_winner(self):
        factions = set()
        for uid in self.store.active_ids():
            factions.add(self.store.faction[uid])
        if len(factions) == 1:
            return factions.pop()
        return None

    def get_survivors(self, faction_id):
        return self.store.active_ids_for_faction(faction_id)

    def export_full_state(self) -> dict:
        """Serialize complete engine state for quit-and-resume.

        Returns a JSON-serializable dict. Restore via restore_from_state() on a
        fresh engine that already has its TacticalMap set.
        """
        s = self.store
        n = s.count

        rng_v, rng_instate, rng_gauss = self.rng.getstate()

        # move_groups has set values and int-keyed offsets — normalize for JSON
        mg_serial = {}
        for gid, grp in s.move_groups.items():
            mg_serial[str(gid)] = {
                "uids": grp["uids"],
                "target_x": grp["target_x"],
                "target_y": grp["target_y"],
                "offsets": {str(k): list(v) for k, v in grp["offsets"].items()},
                "moving": sorted(grp["moving"]),
            }

        cmds_serial = {}
        for tick_key, cmds in self.command_queue._commands.items():
            cmds_serial[str(tick_key)] = [
                {"tick": c.tick, "type": c.type, "unit_ids": c.unit_ids, "params": c.params}
                for c in cmds
            ]

        objs_serial = [
            {
                "id": o.id, "type": o.type, "weight": o.weight,
                "params": o.params, "is_primary": o.is_primary,
                "completion": o.completion, "failed": o.failed,
                "_hold_ticks": o._hold_ticks,
            }
            for o in self.objectives
        ]

        structs_serial = [
            {
                "structure_uid": st.structure_uid,
                "position": list(st.position),
                "layer": st.layer,
                "hp": st.hp,
                "max_hp": st.max_hp,
                "owner_faction": st.owner_faction,
                "capture_progress": st.capture_progress,
                "production_timer_sec": st.production_timer_sec,
                "production_target_unit_type": st.production_target_unit_type,
                "capture_radius": st.capture_radius,
                "_capturing_faction": st._capturing_faction,
            }
            for st in self.reinforcement_structures
        ]

        return {
            "tick": self.tick,
            "player_faction": self.player_faction,
            "time_limit_ticks": self.time_limit_ticks,
            "initial_power": self.initial_power,
            "archetype": self.archetype,
            "commander_uid": self.commander_uid,
            "enable_reinforcement": self.enable_reinforcement,
            "death_log": list(self.death_log),
            "event_log": list(self.event_log),
            "layer_preferences": dict(getattr(self, "layer_preferences", {})),
            "rng_state": {
                "version": rng_v,
                "internalstate": list(rng_instate),
                "gauss_next": rng_gauss,
            },
            "store": {
                "count": n,
                "data": s.data[:n].tolist(),
                "faction": s.faction[:n].tolist(),
                "category": s.category[:n].tolist(),
                "alive": s.alive[:n].tolist(),
                "unit_type": list(s.unit_type[:n]),
                "target_x": s.target_x[:n].tolist(),
                "target_y": s.target_y[:n].tolist(),
                "has_move_target": s.has_move_target[:n].tolist(),
                "effective_speed": s.effective_speed[:n].tolist(),
                "auto_engage_target": s.auto_engage_target[:n].tolist(),
                "ability_target_x": s.ability_target_x[:n].tolist(),
                "ability_target_y": s.ability_target_y[:n].tolist(),
                "waypoints": {str(k): v for k, v in s.waypoints.items()},
                "pulse_remaining": s.pulse_remaining[:n].tolist(),
                "pulse_cooldown": s.pulse_cooldown[:n].tolist(),
                "attack_moving": s.attack_moving[:n].tolist(),
                "engage_anchor_x": s.engage_anchor_x[:n].tolist(),
                "engage_anchor_y": s.engage_anchor_y[:n].tolist(),
                "engage_anchor_set": s.engage_anchor_set[:n].tolist(),
                "detour_dx": s.detour_dx[:n].tolist(),
                "detour_dy": s.detour_dy[:n].tolist(),
                "detour_remaining": s.detour_remaining[:n].tolist(),
                "plain_moving": s.plain_moving[:n].tolist(),
                "move_group_id": s.move_group_id[:n].tolist(),
                "move_groups": mg_serial,
                "_next_move_group_id": s._next_move_group_id,
            },
            "command_queue": cmds_serial,
            "objectives": objs_serial,
            "reinforcement_structures": structs_serial,
        }

    def restore_from_state(self, state: dict) -> None:
        """Restore engine from a dict produced by export_full_state().

        Call on a fresh engine that already has its TacticalMap set.
        No logic changes — purely restoring field values.
        """
        from reinforcement import ReinforcementStructure

        self.tick = state["tick"]
        self.player_faction = state["player_faction"]
        self.time_limit_ticks = state["time_limit_ticks"]
        self.initial_power = state["initial_power"]
        self.archetype = state["archetype"]
        self.commander_uid = state["commander_uid"]
        self.enable_reinforcement = state["enable_reinforcement"]
        self.death_log = list(state["death_log"])
        self.event_log = list(state["event_log"])
        self.layer_preferences = dict(state.get("layer_preferences", {}))

        rs = state["rng_state"]
        self.rng.setstate((rs["version"], tuple(rs["internalstate"]), rs["gauss_next"]))

        sd = state["store"]
        s = self.store
        n = sd["count"]
        s.count = n

        s.data[:n] = np.array(sd["data"], dtype=np.float64)
        s.faction[:n] = np.array(sd["faction"], dtype=np.int32)
        s.category[:n] = np.array(sd["category"], dtype=np.int8)
        s.alive[:n] = np.array(sd["alive"], dtype=np.bool_)
        for i in range(n):
            s.unit_type[i] = sd["unit_type"][i]
        s.target_x[:n] = np.array(sd["target_x"], dtype=np.float64)
        s.target_y[:n] = np.array(sd["target_y"], dtype=np.float64)
        s.has_move_target[:n] = np.array(sd["has_move_target"], dtype=np.bool_)
        s.effective_speed[:n] = np.array(sd["effective_speed"], dtype=np.float64)
        s.auto_engage_target[:n] = np.array(sd["auto_engage_target"], dtype=np.int32)
        s.ability_target_x[:n] = np.array(sd["ability_target_x"], dtype=np.float64)
        s.ability_target_y[:n] = np.array(sd["ability_target_y"], dtype=np.float64)
        s.waypoints = {int(k): v for k, v in sd["waypoints"].items()}
        s.pulse_remaining[:n] = np.array(sd["pulse_remaining"], dtype=np.int32)
        s.pulse_cooldown[:n] = np.array(sd["pulse_cooldown"], dtype=np.int32)
        s.attack_moving[:n] = np.array(sd["attack_moving"], dtype=np.bool_)
        s.engage_anchor_x[:n] = np.array(sd["engage_anchor_x"], dtype=np.float64)
        s.engage_anchor_y[:n] = np.array(sd["engage_anchor_y"], dtype=np.float64)
        s.engage_anchor_set[:n] = np.array(sd["engage_anchor_set"], dtype=np.bool_)
        s.detour_dx[:n] = np.array(sd["detour_dx"], dtype=np.float64)
        s.detour_dy[:n] = np.array(sd["detour_dy"], dtype=np.float64)
        s.detour_remaining[:n] = np.array(sd["detour_remaining"], dtype=np.float64)
        s.plain_moving[:n] = np.array(sd["plain_moving"], dtype=np.bool_)
        s.move_group_id[:n] = np.array(sd["move_group_id"], dtype=np.int32)
        s._next_move_group_id = sd["_next_move_group_id"]
        s.move_groups = {
            int(gid): {
                "uids": grp["uids"],
                "target_x": grp["target_x"],
                "target_y": grp["target_y"],
                "offsets": {int(k): tuple(v) for k, v in grp["offsets"].items()},
                "moving": set(grp["moving"]),
            }
            for gid, grp in sd["move_groups"].items()
        }

        self.command_queue = CommandQueue()
        for tick_str, cmds in state["command_queue"].items():
            for cd in cmds:
                self.command_queue.add(Command(
                    tick=cd["tick"], type=cd["type"],
                    unit_ids=cd["unit_ids"], params=cd["params"],
                ))

        self.objectives = []
        for od in state["objectives"]:
            obj = Objective(od["id"], od["type"], od["weight"], od["params"], od["is_primary"])
            obj.completion = od["completion"]
            obj.failed = od["failed"]
            obj._hold_ticks = od["_hold_ticks"]
            self.objectives.append(obj)

        self.reinforcement_structures = []
        for sd_s in state["reinforcement_structures"]:
            st = ReinforcementStructure(
                structure_uid=sd_s["structure_uid"],
                position=tuple(sd_s["position"]),
                layer=sd_s["layer"],
                hp=sd_s["hp"],
                max_hp=sd_s["max_hp"],
                owner_faction=sd_s["owner_faction"],
                capture_progress=sd_s["capture_progress"],
                production_timer_sec=sd_s["production_timer_sec"],
                production_target_unit_type=sd_s["production_target_unit_type"],
                capture_radius=sd_s["capture_radius"],
            )
            st._capturing_faction = sd_s["_capturing_faction"]
            self.reinforcement_structures.append(st)
