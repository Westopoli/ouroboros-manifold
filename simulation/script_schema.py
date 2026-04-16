"""
JSON schema definition and validator for behavior script files.

validate_script(script_dict) -> list[ValidationError]

Checks (in order):
  1. Required top-level fields present
  2. Per-force: required fields, initial_state exists in states
  3. Per-state: valid behavior + modifier, condition expressions parse + type-check
  4. Per-transition: condition validates, to_state defined (dead-state check)
  5. Per-reactive-hook: when-condition validates, to_state defined
  6. Per-on_enter action: set/clear_flag references declared bus flag
  7. Non-terminal states have at least one outgoing transition
  8. Unreachable-state check (BFS from initial_state)

Cross-validation against layout spine_node_ids is optional; pass
layout_spine_node_ids to enable it. Without a layout, target_resolution
node_kind references are accepted as-is.
"""
from condition_language import validate as _validate_condition, ValidationError

VALID_BEHAVIORS = frozenset({"advance", "defend", "patrol", "ambush", "retreat"})
VALID_MODIFIERS = frozenset({"cautious", "aggressive", "phased"})


# ── Internal helpers ───────────────────────────────────────────────────────────

def _validate_action(action: dict, prefix: str, bus_vocab: set[str], errors: list) -> None:
    if "set_flag" in action:
        flag = action["set_flag"]
        if flag not in bus_vocab:
            errors.append(ValidationError(
                f"{prefix}: set_flag references undeclared bus flag {flag!r}"
            ))
    elif "clear_flag" in action:
        flag = action["clear_flag"]
        if flag not in bus_vocab:
            errors.append(ValidationError(
                f"{prefix}: clear_flag references undeclared bus flag {flag!r}"
            ))
    else:
        errors.append(ValidationError(
            f"{prefix}: unknown action type (supported: 'set_flag', 'clear_flag')"
        ))


def _validate_transition(
    trans: dict,
    prefix: str,
    all_states: dict,
    bus_vocab: set[str],
    errors: list,
) -> None:
    condition = trans.get("condition")
    if condition is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'condition'"))
    elif not isinstance(condition, str):
        errors.append(ValidationError(f"{prefix}: 'condition' must be a string"))
    else:
        for e in _validate_condition(condition, bus_vocab):
            errors.append(ValidationError(f"{prefix} condition {condition!r}: {e}"))

    to_state = trans.get("to_state")
    if to_state is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'to_state'"))
    elif to_state not in all_states:
        errors.append(ValidationError(
            f"{prefix}: to_state {to_state!r} is not defined in this force's states — dead state"
        ))

    noise_pct = trans.get("noise_pct")
    if noise_pct is not None and not isinstance(noise_pct, (int, float)):
        errors.append(ValidationError(f"{prefix}: 'noise_pct' must be numeric, got {type(noise_pct).__name__}"))


def _validate_hook(
    hook: dict,
    prefix: str,
    all_states: dict,
    bus_vocab: set[str],
    errors: list,
) -> None:
    when = hook.get("when")
    if when is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'when'"))
    elif not isinstance(when, str):
        errors.append(ValidationError(f"{prefix}: 'when' must be a string expression"))
    else:
        for e in _validate_condition(when, bus_vocab):
            errors.append(ValidationError(f"{prefix} when {when!r}: {e}"))

    to_state = hook.get("to_state")
    if to_state is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'to_state'"))
    elif to_state not in all_states:
        errors.append(ValidationError(
            f"{prefix}: to_state {to_state!r} is not defined in this force's states — dead state"
        ))


def _validate_state(
    state_def: dict,
    state_name: str,
    prefix: str,
    all_states: dict,
    bus_vocab: set[str],
    terminal_states: set[str],
    layout_spine_node_ids: set[str] | None,
    errors: list,
) -> None:
    behavior = state_def.get("behavior")
    if behavior is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'behavior'"))
    elif behavior not in VALID_BEHAVIORS:
        errors.append(ValidationError(
            f"{prefix}: behavior {behavior!r} not valid; must be one of {sorted(VALID_BEHAVIORS)}"
        ))

    modifier = state_def.get("modifier")
    if modifier is None:
        errors.append(ValidationError(f"{prefix}: missing required field 'modifier'"))
    elif modifier not in VALID_MODIFIERS:
        errors.append(ValidationError(
            f"{prefix}: modifier {modifier!r} not valid; must be one of {sorted(VALID_MODIFIERS)}"
        ))

    target_res = state_def.get("target_resolution")
    if target_res is not None and layout_spine_node_ids is not None:
        node_kind = target_res.get("node_kind")
        if node_kind and node_kind not in layout_spine_node_ids:
            errors.append(ValidationError(
                f"{prefix}: target_resolution node_kind {node_kind!r} not found in layout spine nodes"
            ))

    for j, trans in enumerate(state_def.get("transitions", [])):
        _validate_transition(trans, f"{prefix}.transitions[{j}]", all_states, bus_vocab, errors)

    for j, hook in enumerate(state_def.get("reactive_hooks", [])):
        _validate_hook(hook, f"{prefix}.reactive_hooks[{j}]", all_states, bus_vocab, errors)

    for j, action in enumerate(state_def.get("on_enter", [])):
        _validate_action(action, f"{prefix}.on_enter[{j}]", bus_vocab, errors)


def _reachable_states(initial_state: str, states: dict) -> set[str]:
    reachable: set[str] = set()
    queue = [initial_state]
    while queue:
        current = queue.pop()
        if current in reachable or current not in states:
            continue
        reachable.add(current)
        state_def = states[current]
        for trans in state_def.get("transitions", []):
            s = trans.get("to_state")
            if s and s not in reachable:
                queue.append(s)
        for hook in state_def.get("reactive_hooks", []):
            s = hook.get("to_state")
            if s and s not in reachable:
                queue.append(s)
    return reachable


def _validate_force(
    force: dict,
    prefix: str,
    bus_vocab: set[str],
    terminal_states: set[str],
    layout_spine_node_ids: set[str] | None,
    errors: list,
) -> None:
    for field in ("force_id", "composition_template", "initial_state", "states"):
        if field not in force:
            errors.append(ValidationError(f"{prefix}: missing required field {field!r}"))

    if "states" not in force or "initial_state" not in force:
        return

    states: dict = force["states"]
    initial_state: str = force["initial_state"]

    if initial_state not in states:
        errors.append(ValidationError(
            f"{prefix}: initial_state {initial_state!r} not defined in states"
        ))

    for state_name, state_def in states.items():
        _validate_state(
            state_def,
            state_name,
            f"{prefix}.states[{state_name!r}]",
            states,
            bus_vocab,
            terminal_states,
            layout_spine_node_ids,
            errors,
        )

    # Non-terminal states must have at least one outgoing transition
    for state_name, state_def in states.items():
        if state_name not in terminal_states:
            if not state_def.get("transitions"):
                errors.append(ValidationError(
                    f"{prefix}: non-terminal state {state_name!r} has no transitions — runner will trap here"
                ))

    # Unreachable-state check
    if initial_state in states:
        reachable = _reachable_states(initial_state, states)
        for state_name in states:
            if state_name not in reachable:
                errors.append(ValidationError(
                    f"{prefix}: state {state_name!r} is unreachable from initial_state {initial_state!r}"
                ))


# ── Public API ─────────────────────────────────────────────────────────────────

def validate_script(
    script_dict: dict,
    layout_spine_node_ids: set[str] | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []

    for field in ("script_id", "archetype", "forces", "trigger_bus_vocabulary", "terminal_states"):
        if field not in script_dict:
            errors.append(ValidationError(f"missing required top-level field: {field!r}"))

    if errors:
        return errors

    if not isinstance(script_dict["forces"], list) or not script_dict["forces"]:
        errors.append(ValidationError("'forces' must be a non-empty list"))
        return errors

    bus_vocab: set[str] = set(script_dict["trigger_bus_vocabulary"])
    terminal_states: set[str] = set(script_dict["terminal_states"])

    for i, force in enumerate(script_dict["forces"]):
        force_id = force.get("force_id", f"force[{i}]")
        _validate_force(
            force,
            f"force {force_id!r}",
            bus_vocab,
            terminal_states,
            layout_spine_node_ids,
            errors,
        )

    return errors
