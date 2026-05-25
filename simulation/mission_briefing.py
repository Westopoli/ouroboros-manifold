SITUATION_TEMPLATES = {
    "defensive_stand": "Enemy forces under {enemy_faction_name} are bearing down on {region_name}. Our defenses are {military_desc} and the local economy is {economy_desc}. Regional tension is {tension_desc}. Command has authorized a defensive engagement.",
    "siege_breaking": "The siege of {region_name} has persisted for {ticks_under_pressure} ticks. Our garrison's military readiness is {military_desc} and economic output is {economy_desc}. Hostile forces maintain fortified positions along the perimeter. A breakout operation has been authorized.",
    "reconquest": "{region_name} was taken from us by {enemy_faction_name}. The occupier's garrison is still consolidating. Our intelligence indicates regional tension is {tension_desc} — the population has not accepted the new regime. Command has ordered an immediate counterattack.",
    "assault": "Intelligence identifies {region_name} under {enemy_faction_name} control as a viable target. Their military strength is {military_desc} and stability is weakening. Command has authorized an offensive operation to seize the region.",
    "suppression": "A breakaway faction, {enemy_faction_name}, has seized control of {region_name}. The revolt is recent and their forces are not yet entrenched. Command has ordered immediate suppression before the rebels consolidate.",
    "multi_front_defense": "Multiple hostile forces are converging on {region_name}. Threat sources have been identified on {attack_count} fronts. Our position is {military_desc} militarily with {economy_desc} economic reserves. This will require holding on all fronts simultaneously.",
    "interception": "An enemy strike force from {enemy_faction_name} has been detected en route to {region_name}. The force has committed significant resources. Command has authorized an interception — engage and destroy before they reach the target.",
    "evacuation": "{region_name} is lost. Military strength is {military_desc}, economy is {economy_desc}, and stability has collapsed. A superior hostile force holds adjacent territory. Command has ordered evacuation of all recoverable assets. Your objective is to buy time, not hold ground.",
    "containment": "{enemy_faction_name} has expanded rapidly, gaining territory across multiple fronts. Their advance now threatens {region_name} and surrounding regions. Command has authorized a containment operation — draw a line and hold it.",
    "counterinsurgency": "Insurgent activity in {region_name} has escalated beyond civil security capacity. Tension is {tension_desc} and organized resistance cells are operating throughout the region. Command has authorized military intervention with strict rules of engagement — minimize collateral damage.",
}

OBJECTIVE_TEMPLATES_SHORT = {
    "defensive_stand": "Hold {region_name}. Break the attacking force.",
    "siege_breaking": "Break the siege of {region_name}.",
    "reconquest": "Retake {region_name}.",
    "assault": "Take {region_name} from the enemy.",
    "suppression": "Crush the rebels in {region_name}.",
    "multi_front_defense": "Hold {region_name} against attacks from every direction.",
    "interception": "Stop the enemy force before it reaches {region_name}.",
    "evacuation": "{region_name} is lost — buy time for the evacuation.",
    "containment": "Draw a line in front of {region_name} and hold it.",
    "counterinsurgency": "Find and destroy the insurgent fighters hidden in {region_name}.",
}

OBJECTIVE_TEMPLATES_DETAIL = {
    "defensive_stand": "Destroy them or drive them off the map. The region must remain in our hands when the fighting stops.",
    "siege_breaking": "Destroy the enemy bases ringing the region until the encirclement collapses and our supply lines are open again.",
    "reconquest": "Destroy the occupying force and plant our flag before they can dig in. Spare the cities and roads where you can — we want this region back, not a ruin.",
    "assault": "Destroy the defenders and hold the ground at the end of the battle. The region must change hands.",
    "suppression": "Find their scattered cells and destroy them before they regroup into a real army. None may escape to fight another day.",
    "multi_front_defense": "You cannot defend every approach with full strength — choose where to stand and where to give ground. The region must still be ours when the last attacker is beaten.",
    "interception": "Engage them in open country and destroy them in the field. Not one unit may break through to the region.",
    "evacuation": "Protect the convoy long enough for it to reach the extraction point, then pull out. Do not try to hold the region; save who and what you can.",
    "containment": "The enemy is spreading through the borderlands — stop their advance from crossing into our territory. Hold every pass and choke point on the line.",
    "counterinsurgency": "Sweep the region carefully — every building, every patch of cover. Spare the population and their homes where you can; heavy-handed tactics will only feed the revolt.",
}

ASSET_TEMPLATE = "Command is deploying {player_units} units ({player_power:.0f} total combat power) against an estimated {enemy_units} enemy units ({enemy_power:.0f} combat power). {parity_prose}"

SHORTFALL_TEMPLATE = " Due to diminished capacity, the following assets could not be provided: {shortfall_list}."

REINFORCEMENT_TEMPLATE = " {structure_count} production structures will be active in the area of operations ({player_structures} allied, {enemy_structures} hostile, {neutral_structures} contested)."


def _parity_prose(ratio):
    if ratio >= 1.0:
        return "Our forces hold a decisive advantage."
    elif ratio >= 0.95:
        return "Force strength is near parity with the enemy."
    elif ratio >= 0.90:
        return "We are slightly outnumbered but well within fighting capability."
    elif ratio >= 0.85:
        return "We are outnumbered. Tactical discipline will be critical."
    elif ratio >= 0.80:
        return "We are significantly outnumbered. Expect a hard fight."
    return "We are heavily outnumbered. Every unit counts."


def assemble_briefing(archetype, slots):
    situation = SITUATION_TEMPLATES.get(archetype, "Mission details are classified.")
    objective = OBJECTIVE_TEMPLATES_SHORT.get(archetype, "Complete the assigned objective.")
    objective_detail = OBJECTIVE_TEMPLATES_DETAIL.get(archetype, "")

    try:
        situation = situation.format_map(_SafeSlots(slots))
    except (KeyError, ValueError):
        pass
    try:
        objective = objective.format_map(_SafeSlots(slots))
    except (KeyError, ValueError):
        pass
    try:
        objective_detail = objective_detail.format_map(_SafeSlots(slots))
    except (KeyError, ValueError):
        pass

    parity = slots.get("parity_ratio", 1.0)
    slots = dict(slots, parity_prose=_parity_prose(parity))
    assets = ASSET_TEMPLATE.format_map(_SafeSlots(slots))

    shortfall = slots.get("shortfall_types", [])
    if shortfall:
        from collections import Counter
        sc = Counter(shortfall)
        parts = [f"{cnt}× {ut}" for ut, cnt in sc.items()]
        assets += SHORTFALL_TEMPLATE.format(shortfall_list=", ".join(parts))

    reinforcements = slots.get("reinforcements")
    if reinforcements:
        assets += REINFORCEMENT_TEMPLATE.format(
            structure_count=reinforcements.structure_count,
            player_structures=reinforcements.player_structures,
            enemy_structures=reinforcements.enemy_structures,
            neutral_structures=reinforcements.neutral_structures,
        )

    return {
        "situation": situation,
        "objective": objective,
        "objective_detail": objective_detail,
        "assets": assets,
    }


class _SafeSlots(dict):
    def __missing__(self, key):
        return f"{{{key}}}"
