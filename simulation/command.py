import hashlib
import numpy as np
from dataclasses import dataclass, field
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, NUM_FIELDS
from movement import apply_group_move
from ability import activate_ability


@dataclass
class Command:
    tick: int
    type: str
    unit_ids: list
    params: dict = field(default_factory=dict)


class CommandQueue:
    def __init__(self):
        self._commands = {}

    def add(self, cmd):
        if cmd.tick not in self._commands:
            self._commands[cmd.tick] = []
        self._commands[cmd.tick].append(cmd)

    def get(self, tick):
        return self._commands.get(tick, [])

    def all_commands(self):
        result = []
        for tick in sorted(self._commands):
            result.extend(self._commands[tick])
        return result


def process_commands(queue, store, tick):
    for cmd in queue.get(tick):
        if cmd.type == "move":
            tx = cmd.params["target_x"]
            ty = cmd.params["target_y"]
            alive_ids = [uid for uid in cmd.unit_ids if store.alive[uid]]
            # apply_group_move is the single entry point for multi-unit target orders.
            # Formation offsets and group registration live there. See movement.py.
            apply_group_move(store, alive_ids, tx, ty)
            for uid in alive_ids:
                store.attack_moving[uid] = False
                store.plain_moving[uid] = True
                store.auto_engage_target[uid] = -1  # break engagement so unit actually moves

        elif cmd.type == "attack_move":
            tx = cmd.params["target_x"]
            ty = cmd.params["target_y"]
            alive_ids = [uid for uid in cmd.unit_ids if store.alive[uid]]
            # apply_group_move is the single entry point for multi-unit target orders.
            # Formation offsets and group registration live there. See movement.py.
            apply_group_move(store, alive_ids, tx, ty)
            for uid in alive_ids:
                store.attack_moving[uid] = True
                store.engage_anchor_set[uid] = False
                store.plain_moving[uid] = False
                store.auto_engage_target[uid] = -1  # break engagement; unit re-engages on arrival

        elif cmd.type == "attack_target":
            target_uid = cmd.params["target_uid"]
            for uid in cmd.unit_ids:
                if store.alive[uid]:
                    store.auto_engage_target[uid] = target_uid

        elif cmd.type == "activate_ability":
            for uid in cmd.unit_ids:
                if store.alive[uid]:
                    activate_ability(store, uid)



def compute_state_hash(store):
    h = hashlib.md5()
    for uid in range(store.count):
        h.update(store.alive[uid].tobytes())
        if store.alive[uid]:
            h.update(store.data[uid, :NUM_FIELDS].tobytes())
            h.update(store.faction[uid].tobytes())
    return h.hexdigest()


class ReplayRecording:
    def __init__(self):
        self.initial_state = None
        self.commands = []
        self.seed = None
        self.map_id = None

    def capture_initial_state(self, store, seed, map_id=""):
        self.seed = seed
        self.map_id = map_id
        self.initial_state = {
            "count": store.count,
            "data": store.data[:store.count].copy(),
            "faction": store.faction[:store.count].copy(),
            "category": store.category[:store.count].copy(),
            "alive": store.alive[:store.count].copy(),
            "unit_type": list(store.unit_type[:store.count]),
        }

    def record_command(self, cmd):
        self.commands.append(cmd)

    def restore_initial_state(self):
        store = UnitStore()
        state = self.initial_state
        n = state["count"]
        store.count = n
        store.data[:n] = state["data"]
        store.faction[:n] = state["faction"]
        store.category[:n] = state["category"]
        store.alive[:n] = state["alive"]
        for i in range(n):
            store.unit_type[i] = state["unit_type"][i]
        return store

    def build_command_queue(self):
        queue = CommandQueue()
        for cmd in self.commands:
            queue.add(cmd)
        return queue
