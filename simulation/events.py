# Input:  event template dicts, region fields/composites, pending queue entries
# Output: triggered template IDs, field deltas, chain spawn lists

import random
import config

_chain_counter = 0

def _next_chain_tag() -> str:
    global _chain_counter
    _chain_counter += 1
    return f"chain_{_chain_counter:04d}"

def reset_chain_counter():
    global _chain_counter
    _chain_counter = 0

# ── Template library ─────────────────────────────────────────────────────────

TEMPLATES = {
    "evt_garrison_collapse": {
        "id":                "evt_garrison_collapse",
        "name":              "Garrison Collapse",
        "trigger_field":     "military",
        "trigger_threshold": 30,
        "trigger_direction": "below",
        "immediate_effects": {"military": -2, "tension": +3},
        "chain_spawns": [
            {
                "template_id": "evt_border_incursion",
                "delay_range":  [3, 7],
                "probability":  0.55,
                "conditions":   {"military": {"below": 18}},
            },
            {
                "template_id": "evt_emergency_levy",
                "delay_range":  [2, 5],
                "probability":  0.40,
                "conditions":   {"economy": {"above": 25}},
            },
        ],
        "chain_tags":    ["military_crisis"],
        "exclusion_tags": [],
        "significance_tier": 4,
    },
    "evt_border_incursion": {
        "id":                "evt_border_incursion",
        "name":              "Border Incursion",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"military": -2, "economy": -2, "tension": +2},
        "chain_spawns": [
            {
                "template_id": "evt_regional_revolt",
                "delay_range":  [4, 10],
                "probability":  0.35,
                "conditions":   {"tension": {"above": 55}},
            },
        ],
        "chain_tags":    ["military_crisis"],
        "exclusion_tags": [],
        "significance_tier": 4,
    },
    "evt_emergency_levy": {
        "id":                "evt_emergency_levy",
        "name":              "Emergency Levy",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"military": +3, "economy": -2, "tension": +2},
        "chain_spawns": [],
        "chain_tags":    ["military_crisis"],
        "exclusion_tags": ["military_relief"],
        "significance_tier": 3,
    },
    "evt_regional_revolt": {
        "id":                "evt_regional_revolt",
        "name":              "Regional Revolt",
        "trigger_field":     "tension",
        "trigger_threshold": 60,
        "trigger_direction": "above",
        "immediate_effects": {"military": -2, "economy": -2, "tension": +4},
        "chain_spawns": [
            {
                "template_id": "evt_revolt_crushed",
                "delay_range":  [3, 8],
                "probability":  0.45,
                "conditions":   {"military": {"above": 35}},
            },
            {
                "template_id": "evt_revolt_entrenched",
                "delay_range":  [5, 12],
                "probability":  0.30,
                "conditions":   {"tension": {"above": 65}},
            },
        ],
        "chain_tags":    ["political_unrest"],
        "exclusion_tags": ["political_resolution"],
        "significance_tier": 4,
    },
    "evt_revolt_crushed": {
        "id":                "evt_revolt_crushed",
        "name":              "Revolt Crushed",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"military": -1, "tension": -2},
        "chain_spawns": [],
        "chain_tags":    ["political_unrest"],
        "exclusion_tags": ["revolt_outcome"],
        "significance_tier": 3,
    },
    "evt_revolt_entrenched": {
        "id":                "evt_revolt_entrenched",
        "name":              "Revolt Entrenched",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"military": -4, "economy": -2, "tension": +2, "population": -2},
        "chain_spawns": [],
        "chain_tags":    ["political_unrest"],
        "exclusion_tags": ["revolt_outcome"],
        "significance_tier": 5,
        "creates_faction":   True,   # L4: signals tick.py to create a breakaway faction
    },
    "evt_trade_boom": {
        "id":                "evt_trade_boom",
        "name":              "Trade Boom",
        "trigger_field":     "economy",
        "trigger_threshold": 55,
        "trigger_direction": "above",
        "immediate_effects": {"economy": +2, "population": +1, "tension": +1},
        "chain_spawns": [
            {
                "template_id": "evt_prosperity_unrest",
                "delay_range":  [8, 15],
                "probability":  0.25,
                "conditions":   {"tension": {"above": 40}},
            },
        ],
        "chain_tags":    ["economic_surge"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_prosperity_unrest": {
        "id":                "evt_prosperity_unrest",
        "name":              "Prosperity Unrest",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"tension": +4, "economy": -1},
        "chain_spawns": [],
        "chain_tags":    ["economic_surge", "political_unrest"],
        "exclusion_tags": [],
        "significance_tier": 2,
    },
    "evt_population_crisis": {
        "id":                "evt_population_crisis",
        "name":              "Population Crisis",
        "trigger_field":     "population",
        "trigger_threshold": 20,
        "trigger_direction": "below",
        "immediate_effects": {"economy": -2, "military": -2, "tension": +2},
        "chain_spawns": [],
        "chain_tags":    ["demographic_collapse"],
        "exclusion_tags": [],
        "significance_tier": 4,
        "creates_faction":   False,
    },
    # ── Stage 0 revision: new event types (Groups L3–L4) ─────────────────────
    "evt_resistance_movement": {
        "id":                "evt_resistance_movement",
        "name":              "Resistance Movement",
        "trigger_field":     None,   # chain-only; spawned by conquest follow-up
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"tension": +5, "military": -2},
        "chain_spawns": [],
        "chain_tags":    ["political_unrest", "conquest_aftermath"],
        "exclusion_tags": [],
        "significance_tier": 3,
        "creates_faction":   False,
    },
    "CONQUEST_UNREST": {
        "id":                "CONQUEST_UNREST",
        "name":              "Conquest Unrest",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"tension": +6, "economy": -2, "military": -1},
        "chain_spawns": [
            {
                "template_id": "evt_regional_revolt",
                "delay_range":  [5, 12],
                "probability":  0.35,
                "conditions":   {"tension": {"above": 55}},
            },
        ],
        "chain_tags":    ["conquest_aftermath", "political_unrest"],
        "exclusion_tags": [],
        "significance_tier": 4,
        "creates_faction":   False,
    },
    "evt_labor_shortage": {
        "id":                "evt_labor_shortage",
        "name":              "Labor Shortage",
        "trigger_field":     "population",
        "trigger_threshold": 40,
        "trigger_direction": "below",
        "immediate_effects": {"economy": -2, "tension": +2},
        "chain_spawns": [
            {
                "template_id": "evt_immigration_wave",
                "delay_range":  [5, 12],
                "probability":  0.40,
                "conditions":   {"economy": {"above": 30}},
            },
        ],
        "chain_tags":    ["demographic_pressure"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_immigration_wave": {
        "id":                "evt_immigration_wave",
        "name":              "Immigration Wave",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"population": +3, "economy": +1, "tension": +2},
        "chain_spawns": [],
        "chain_tags":    ["demographic_pressure"],
        "exclusion_tags": [],
        "significance_tier": 2,
    },
    "evt_infrastructure_decay": {
        "id":                "evt_infrastructure_decay",
        "name":              "Infrastructure Decay",
        "trigger_field":     "economy",
        "trigger_threshold": 40,
        "trigger_direction": "below",
        "immediate_effects": {"economy": -3, "tension": +2, "population": -1},
        "chain_spawns": [],
        "chain_tags":    ["economic_decline"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_military_buildup": {
        "id":                "evt_military_buildup",
        "name":              "Military Buildup",
        "trigger_field":     "military",
        "trigger_threshold": 50,
        "trigger_direction": "above",
        "immediate_effects": {"military": +2, "economy": -2, "tension": +1},
        "chain_spawns": [
            {
                "template_id": "evt_war_weariness",
                "delay_range":  [8, 15],
                "probability":  0.35,
                "conditions":   {"tension": {"above": 30}},
            },
        ],
        "chain_tags":    ["military_expansion"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_war_weariness": {
        "id":                "evt_war_weariness",
        "name":              "War Weariness",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"tension": +3, "military": -2, "economy": -1},
        "chain_spawns": [],
        "chain_tags":    ["military_expansion"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_cultural_renaissance": {
        "id":                "evt_cultural_renaissance",
        "name":              "Cultural Renaissance",
        "trigger_field":     "economy",
        "trigger_threshold": 60,
        "trigger_direction": "above",
        "immediate_effects": {"tension": -3, "economy": +1, "population": +1},
        "chain_spawns": [],
        "chain_tags":    ["cultural_shift"],
        "exclusion_tags": [],
        "significance_tier": 2,
    },
    "evt_famine": {
        "id":                "evt_famine",
        "name":              "Famine",
        "trigger_field":     "economy",
        "trigger_threshold": 10,
        "trigger_direction": "below",
        "immediate_effects": {"population": -3, "tension": +4, "economy": -1},
        "chain_spawns": [
            {
                "template_id": "evt_regional_revolt",
                "delay_range":  [4, 10],
                "probability":  0.30,
                "conditions":   {"tension": {"above": 45}},
            },
            {
                "template_id": "evt_famine_relief",
                "delay_range":  [5, 12],
                "probability":  0.55,
                "conditions":   {"economy": {"above": 12}},
            },
        ],
        "chain_tags":    ["economic_decline"],
        "exclusion_tags": [],
        "significance_tier": 4,
    },
    "evt_famine_relief": {
        "id":                "evt_famine_relief",
        "name":              "Famine Relief",
        "trigger_field":     None,
        "trigger_threshold": None,
        "trigger_direction": None,
        "immediate_effects": {"economy": +3, "tension": -3, "population": +2},
        "chain_spawns": [],
        "chain_tags":    ["economic_decline"],
        "exclusion_tags": [],
        "significance_tier": 3,
    },
    "evt_diplomatic_incident": {
        "id":                "evt_diplomatic_incident",
        "name":              "Diplomatic Incident",
        "trigger_field":     "tension",
        "trigger_threshold": 35,
        "trigger_direction": "above",
        "immediate_effects": {"tension": +3, "military": +1, "economy": -1},
        "chain_spawns": [],
        "chain_tags":    ["political_unrest"],
        "exclusion_tags": [],
        "significance_tier": 2,
    },
    "evt_harvest_surplus": {
        "id":                "evt_harvest_surplus",
        "name":              "Harvest Surplus",
        "trigger_field":     "population",
        "trigger_threshold": 50,
        "trigger_direction": "above",
        "immediate_effects": {"economy": +2, "population": +1, "tension": -1},
        "chain_spawns": [],
        "chain_tags":    ["economic_surge"],
        "exclusion_tags": [],
        "significance_tier": 2,
    },
}


def get_template(template_id: str) -> dict:
    return TEMPLATES[template_id]


# ── Per-region noise offsets ──────────────────────────────────────────────────

def roll_noise_offsets(region_ids: list, rng: random.Random) -> dict:
    """Roll once-per-time-jump threshold noise offsets for each (region, template) pair."""
    offsets = {}
    for rid in region_ids:
        offsets[rid] = {}
        for tid, tmpl in TEMPLATES.items():
            if tmpl["trigger_field"] is not None:
                offsets[rid][tid] = rng.uniform(
                    -config.EVENT_NOISE_RANGE, config.EVENT_NOISE_RANGE
                )
    return offsets


# ── Threshold trigger evaluation ─────────────────────────────────────────────

def evaluate_triggers(region, noise_offsets: dict, trigger_state: dict,
                      tick: int = 0) -> list:
    """
    Return list of template IDs whose threshold is newly crossed this tick.
    trigger_state: {region_id: {template_id: bool}} — True means threshold is currently breached.
    Only fires on the crossing tick; resets when field recovers past threshold.
    """
    if tick <= config.EVENT_GRACE_PERIOD:
        # Still update trigger_state so the first real tick doesn't see a false crossing
        region_offsets = noise_offsets.get(region.id, {})
        region_state   = trigger_state.setdefault(region.id, {})
        for tid, tmpl in TEMPLATES.items():
            if tmpl["trigger_field"] is None:
                continue
            field_val = region.fields[tmpl["trigger_field"]]
            offset    = region_offsets.get(tid, 0.0)
            threshold = tmpl["trigger_threshold"] + offset
            region_state[tid] = (
                field_val > threshold if tmpl["trigger_direction"] == "above"
                else field_val < threshold
            )
        return []

    triggered = []
    region_offsets = noise_offsets.get(region.id, {})
    region_state   = trigger_state.setdefault(region.id, {})

    for tid, tmpl in TEMPLATES.items():
        if tmpl["trigger_field"] is None:
            continue
        field_val = region.fields[tmpl["trigger_field"]]
        offset    = region_offsets.get(tid, 0.0)
        threshold = tmpl["trigger_threshold"] + offset
        was_active = region_state.get(tid, False)

        if tmpl["trigger_direction"] == "above":
            now_active = field_val > threshold
        else:
            now_active = field_val < threshold

        region_state[tid] = now_active

        if now_active and not was_active:
            triggered.append(tid)

    return triggered


# ── Event firing ─────────────────────────────────────────────────────────────

def fire_event(template_id: str, region, tick: int, chain_tag: str, rng: random.Random) -> dict:
    """Apply immediate effects; return chain spawns to enqueue."""
    tmpl = TEMPLATES[template_id]
    for field, delta in tmpl["immediate_effects"].items():
        if field == "economy":
            floor = config.ECONOMY_FLOOR
        elif field == "tension":
            floor = config.TENSION_FLOOR
        else:
            floor = 0.0
        region.fields[field] = max(floor, min(100.0, region.fields[field] + delta))
    region.recompute_composites()

    spawns = []
    for spawn in tmpl["chain_spawns"]:
        delay = rng.randint(*spawn["delay_range"])
        spawns.append({
            "template_id": spawn["template_id"],
            "region_id":   region.id,
            "due_tick":    tick + delay,
            "probability": spawn["probability"],
            "conditions":  spawn["conditions"],
            "chain_tag":   chain_tag,
        })
    return {
        "template_id":      template_id,
        "name":             tmpl["name"],
        "region_id":        region.id,
        "tick":             tick,
        "field_deltas":     tmpl["immediate_effects"],
        "chain_tag":        chain_tag,
        "spawns":           spawns,
        "exclusion_tags":   tmpl["exclusion_tags"],
        "creates_faction":  tmpl.get("creates_faction", False),
    }


# ── Pending event queue ───────────────────────────────────────────────────────

class PendingQueue:
    def __init__(self):
        self._queue = []

    def enqueue(self, entry: dict) -> None:
        self._queue.append(entry)

    def due_this_tick(self, tick: int) -> list:
        return [e for e in self._queue if e["due_tick"] == tick]

    def remove(self, entries: list) -> None:
        ids_to_remove = {id(e) for e in entries}
        self._queue = [e for e in self._queue if id(e) not in ids_to_remove]

    def size(self) -> int:
        return len(self._queue)


# ── Condition checking ────────────────────────────────────────────────────────

def _conditions_met(conditions: dict, region) -> bool:
    for field, constraint in conditions.items():
        val = region.fields[field]
        if "above" in constraint and val <= constraint["above"]:
            return False
        if "below" in constraint and val >= constraint["below"]:
            return False
    return True


# ── Pending event resolution ─────────────────────────────────────────────────

def resolve_pending(queue: PendingQueue, world, tick: int, rng: random.Random) -> list:
    """
    Resolve all events due this tick.
    Simultaneous events on the same region apply deltas against tick-start state.
    Mutually exclusive events: higher-probability winner fires, loser is delayed 1-2 ticks.
    Returns list of fired event result dicts.
    """
    due = queue.due_this_tick(tick)
    queue.remove(due)

    # Group by region for collision handling
    by_region = {}
    for entry in due:
        by_region.setdefault(entry["region_id"], []).append(entry)

    fired = []
    for rid, entries in by_region.items():
        region = world.regions[rid]

        # Snapshot fields at tick start so simultaneous events all read the same state
        tick_start_fields = {k: v for k, v in region.fields.items()}

        # Mutual exclusion: collect all exclusion tags present; keep highest-prob winner
        resolved, delayed = _resolve_exclusions(entries, tick, rng)

        # Delayed entries go back in the queue
        for entry in delayed:
            queue.enqueue(entry)

        # Accumulate deltas from all resolved entries, roll each for probability + conditions
        combined_deltas = {f: 0.0 for f in region.fields}
        for entry in resolved:
            if not _conditions_met(entry["conditions"], region):
                continue
            if rng.random() > entry["probability"]:
                continue
            tmpl = TEMPLATES[entry["template_id"]]
            for field, delta in tmpl["immediate_effects"].items():
                combined_deltas[field] += delta

            result = {
                "template_id":    entry["template_id"],
                "name":           tmpl["name"],
                "region_id":      rid,
                "tick":           tick,
                "field_deltas":   tmpl["immediate_effects"],
                "chain_tag":      entry["chain_tag"],
                "spawns":         [],
                "exclusion_tags": tmpl["exclusion_tags"],
                "creates_faction": tmpl.get("creates_faction", False),
            }
            # Queue chain spawns
            for spawn in tmpl["chain_spawns"]:
                delay = rng.randint(*spawn["delay_range"])
                spawn_entry = {
                    "template_id": spawn["template_id"],
                    "region_id":   rid,
                    "due_tick":    tick + delay,
                    "probability": spawn["probability"],
                    "conditions":  spawn["conditions"],
                    "chain_tag":   entry["chain_tag"],
                }
                queue.enqueue(spawn_entry)
                result["spawns"].append(f"{spawn['template_id']}@tick_{tick + delay}")
            fired.append(result)

        # Apply combined deltas once (simultaneous resolution against tick-start state)
        for field, delta in combined_deltas.items():
            if delta != 0.0:
                if field == "economy":
                    floor = config.ECONOMY_FLOOR
                elif field == "tension":
                    floor = config.TENSION_FLOOR
                else:
                    floor = 0.0
                region.fields[field] = max(floor, min(100.0, tick_start_fields[field] + delta))
        if any(d != 0.0 for d in combined_deltas.values()):
            region.recompute_composites()

    return fired


def _resolve_exclusions(entries: list, tick: int, rng: random.Random):
    """
    Among entries sharing an exclusion tag, keep the highest-probability one.
    The rest are delayed 1-2 ticks and returned separately.
    """
    resolved = list(entries)
    delayed  = []

    all_excl_tags = set()
    for e in entries:
        tmpl = TEMPLATES[e["template_id"]]
        all_excl_tags.update(tmpl["exclusion_tags"])

    for tag in all_excl_tags:
        conflicting = [
            e for e in resolved if tag in TEMPLATES[e["template_id"]]["exclusion_tags"]
        ]
        if len(conflicting) <= 1:
            continue
        winner = max(conflicting, key=lambda e: e["probability"])
        for loser in conflicting:
            if loser is winner:
                continue
            resolved.remove(loser)
            loser_copy = dict(loser)
            loser_copy["due_tick"] = tick + rng.randint(1, 2)
            delayed.append(loser_copy)

    return resolved, delayed
