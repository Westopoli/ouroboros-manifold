import random
import config
from unit import UnitStore, FIELD_HP
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import compute_visibility, update_fog_timers
from command import CommandQueue, process_commands, compute_state_hash
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

    def step(self):
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
