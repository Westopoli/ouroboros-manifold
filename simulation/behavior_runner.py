"""
Shared FSM runner for enemy behavior scripts.

One BehaviorRunner per mission. The tactical engine calls step() every tick;
the runner self-throttles to config.SCRIPT_EVAL_INTERVAL_TICKS and emits
commands into the engine's CommandQueue on evaluation ticks.

# See also: tactical_engine.py — calls runner.step() when ENABLE_BEHAVIOR_SCRIPTS is on.
# See also: script_loader.py — provides validated script dicts consumed here.
# See also: force_composition.py — template names referenced in script forces[].
"""
import random
from dataclasses import dataclass, field

import config
from condition_language import EvaluationContext, evaluate
from trigger_bus import TriggerBus
from command import Command, CommandQueue
from unit import FIELD_HP, FIELD_MAX_HP


@dataclass
class BehaviorRunnerState:
    force_id: str
    current_state: str
    mission_start_tick: int
    faction_id: int = 0
    last_eval_tick: int = -1
    # key = (state_name, trans_index) or (state_name, "hook_N"), value = noise scalar
    trans_noise: dict = field(default_factory=dict)


class BehaviorRunner:
    """
    Drives all forces in one script per mission tick.

    force_faction_ids — optional {force_id: faction_id} dict for multi-force scripts
    where each force group is spawned under a distinct enemy faction. Falls back to
    the single faction_id argument for all forces when omitted.
    """

    def __init__(
        self,
        script: dict,
        tactical_map,
        bus: TriggerBus,
        rng: random.Random,
        faction_id: int,
        mission_start_tick: int = 0,
        time_limit_ticks: int = 0,
        force_faction_ids: dict[str, int] | None = None,
    ):
        self.script = script
        self.map = tactical_map
        self.bus = bus
        self.time_limit_ticks = time_limit_ticks
        self.eval_log: list[dict] = []

        self.runner_states: list[BehaviorRunnerState] = []
        for force_def in script["forces"]:
            fid = (force_faction_ids or {}).get(force_def["force_id"], faction_id)
            rs = BehaviorRunnerState(
                force_id=force_def["force_id"],
                current_state=force_def["initial_state"],
                mission_start_tick=mission_start_tick,
                faction_id=fid,
            )
            for sname, sdef in force_def["states"].items():
                for i, trans in enumerate(sdef.get("transitions", [])):
                    pct = trans.get("noise_pct", config.SCRIPT_NOISE_DEFAULT_PCT)
                    rs.trans_noise[(sname, i)] = rng.uniform(-pct, pct)
                for i, hook in enumerate(sdef.get("reactive_hooks", [])):
                    pct = hook.get("noise_pct", config.SCRIPT_NOISE_DEFAULT_PCT)
                    rs.trans_noise[(sname, f"hook_{i}")] = rng.uniform(-pct, pct)
            self.runner_states.append(rs)

    def step(self, tick: int, store, command_queue: CommandQueue) -> None:
        if tick % config.SCRIPT_EVAL_INTERVAL_TICKS != 0:
            return

        for i, rs in enumerate(self.runner_states):
            faction_units = store.active_ids_for_faction(rs.faction_id)
            if not faction_units:
                continue
            self._eval_force(tick, rs, self.script["forces"][i], faction_units, store, command_queue)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _make_ctx(
        self,
        tick: int,
        rs: BehaviorRunnerState,
        faction_units: list,
        store,
        noise: float = 0.0,
        is_timer: bool = False,
    ) -> EvaluationContext:
        total_hp = sum(max(0.0, store.data[uid, FIELD_HP]) for uid in faction_units)
        total_max = sum(store.data[uid, FIELD_MAX_HP] for uid in faction_units)
        hp_frac = total_hp / total_max if total_max > 0 else 0.0

        elapsed = (tick - rs.mission_start_tick) * config.TACTICAL_TICK_DURATION
        expired = self.time_limit_ticks > 0 and (tick - rs.mission_start_tick) >= self.time_limit_ticks

        if is_timer:
            elapsed = max(0.0, elapsed * (1.0 + noise))
        else:
            hp_frac = max(0.0, min(1.0, hp_frac * (1.0 + noise)))

        return EvaluationContext(
            force_hp_fraction=hp_frac,
            force_unit_count=len(faction_units),
            timer_elapsed_sec=elapsed,
            timer_expired=expired,
            bus=self.bus,
            # Conservative defaults: assume player at full HP, no enemy in detection range.
            # The mission launcher overrides these with real callables when zone tracking is wired.
            player_force_hp_in_zone_fn=lambda zone_id: 1.0,
            enemy_unit_in_range_fn=lambda zone_id, radius: False,
        )

    def _classify(self, condition: str, to_state: str, states_dict: dict) -> str:
        """Return 'survival', 'timer', or 'threshold' for transition priority ordering."""
        if "timer." in condition:
            return "timer"
        if states_dict.get(to_state, {}).get("behavior") == "retreat":
            return "survival"
        return "threshold"

    def _try_transitions(
        self,
        tick: int,
        rs: BehaviorRunnerState,
        transitions: list,
        states_dict: dict,
        faction_units: list,
        store,
    ) -> tuple[str | None, int]:
        """Evaluate transitions in priority order: survival → threshold → timer.
        Returns (to_state, count_tried) — to_state is None if no transition fires.
        """
        buckets: dict[str, list] = {"survival": [], "threshold": [], "timer": []}
        for i, trans in enumerate(transitions):
            cond = trans.get("condition", "")
            to = trans.get("to_state", "")
            kind = self._classify(cond, to, states_dict)
            noise = rs.trans_noise.get((rs.current_state, i), 0.0)
            buckets[kind].append((cond, to, noise))

        tried = 0
        for kind in ("survival", "threshold", "timer"):
            for cond, to, noise in buckets[kind]:
                tried += 1
                ctx = self._make_ctx(tick, rs, faction_units, store, noise, "timer." in cond)
                try:
                    if evaluate(cond, ctx):
                        return to, tried
                except Exception:
                    pass
        return None, tried

    def _resolve_target(self, node_kind: str):
        nodes = self.map.get_spine_nodes_by_type(node_kind)
        return nodes[0].position if nodes else None

    def _emit_command(
        self,
        tick: int,
        state_def: dict,
        faction_units: list,
        command_queue: CommandQueue,
    ) -> str | None:
        behavior = state_def.get("behavior", "defend")
        if behavior == "ambush":
            return None

        tx, ty = self.map.width / 2, self.map.height / 2
        target_res = state_def.get("target_resolution")
        if target_res:
            pos = self._resolve_target(target_res.get("node_kind", ""))
            if pos:
                tx, ty = pos

        cmd_type = "move" if behavior == "retreat" else "attack_move"
        command_queue.add(Command(
            tick=tick,
            type=cmd_type,
            unit_ids=list(faction_units),
            params={"target_x": tx, "target_y": ty},
        ))
        return cmd_type

    def _exec_on_enter(self, state_def: dict) -> None:
        for action in state_def.get("on_enter", []):
            if "set_flag" in action:
                self.bus.set_flag(action["set_flag"])
            elif "clear_flag" in action:
                self.bus.clear_flag(action["clear_flag"])

    def _eval_force(
        self,
        tick: int,
        rs: BehaviorRunnerState,
        force_def: dict,
        faction_units: list,
        store,
        command_queue: CommandQueue,
    ) -> None:
        states_dict = force_def["states"]
        terminal_states = set(self.script.get("terminal_states", []))
        current = rs.current_state

        if current not in states_dict or current in terminal_states:
            return

        state_def = states_dict[current]
        next_state = None
        hooks_tried = 0

        for i, hook in enumerate(state_def.get("reactive_hooks", [])):
            when = hook.get("when", "")
            to = hook.get("to_state", "")
            noise = rs.trans_noise.get((current, f"hook_{i}"), 0.0)
            ctx = self._make_ctx(tick, rs, faction_units, store, noise, False)
            hooks_tried += 1
            try:
                if evaluate(when, ctx):
                    next_state = to
                    break
            except Exception:
                pass

        trans_tried = 0
        if next_state is None:
            next_state, trans_tried = self._try_transitions(
                tick, rs, state_def.get("transitions", []), states_dict, faction_units, store
            )

        prev_state = current
        if next_state is not None and next_state != current:
            rs.current_state = next_state
            new_state_def = states_dict[next_state]
            self._exec_on_enter(new_state_def)
            state_def = new_state_def
            current = next_state

        cmd_type = self._emit_command(tick, state_def, faction_units, command_queue)

        self.eval_log.append({
            "tick": tick,
            "elapsed_sec": round((tick - rs.mission_start_tick) * config.TACTICAL_TICK_DURATION, 1),
            "force_id": rs.force_id,
            "state_before": prev_state,
            "state_after": current,
            "unit_count": len(faction_units),
            "hooks_tried": hooks_tried,
            "trans_tried": trans_tried,
            "command": cmd_type,
        })
