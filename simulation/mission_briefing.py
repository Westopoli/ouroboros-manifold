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

OBJECTIVE_TEMPLATES = {
    "defensive_stand": "Hold {region_name} against the incoming assault. Destroy or rout the attacking force. Preserve defensive infrastructure where possible.",
    "siege_breaking": "Break the siege on {region_name}. Destroy enemy forward positions along the perimeter. Reopen supply lines and relieve the garrison.",
    "reconquest": "Retake {region_name}. Destroy the occupying garrison and secure the region. Preserve civilian infrastructure where tactically feasible.",
    "assault": "Seize {region_name}. Destroy the defending force and capture key positions. Breach fortifications and establish control.",
    "suppression": "Destroy the rebel force in {region_name}. Locate and engage scattered rebel positions. Prevent escape and consolidation.",
    "multi_front_defense": "Defend {region_name} on all fronts. Prioritize threats and allocate forces accordingly. Accept losses where necessary to hold critical positions.",
    "interception": "Intercept and destroy the enemy force before it reaches {region_name}. Engage in open field. Prevent any breakthrough to the target.",
    "evacuation": "Cover the evacuation of {region_name}. Extract all designated assets. Delay the enemy advance. Withdraw once extraction is complete — do not attempt to hold.",
    "containment": "Establish and hold a defensive boundary protecting {region_name} and adjacent territories. Prevent hostile expansion past the line. Garrison chokepoints and cover gaps.",
    "counterinsurgency": "Locate and neutralize insurgent forces in {region_name}. Clear sector by sector. Minimize damage to civilian infrastructure — collateral damage worsens the underlying instability.",
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
    objective = OBJECTIVE_TEMPLATES.get(archetype, "Complete the assigned objective.")

    try:
        situation = situation.format_map(_SafeSlots(slots))
    except (KeyError, ValueError):
        pass
    try:
        objective = objective.format_map(_SafeSlots(slots))
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
        "assets": assets,
    }


class _SafeSlots(dict):
    def __missing__(self, key):
        return f"{{{key}}}"
