# Input:  archetype, budget, modifiers, world + registry for agent decisions
# Output: Faction objects; act() returns per-tick decision log dict
#
# Era-agnostic vocabulary: faction, region, military_strength, attack_event.
# No sci-fi-specific terms.

import random
import config
import theme_scifi as theme


class Faction:
    _ARCHETYPE_COLORS = {
        "player_civilization": "#4a9eff",
        "conqueror":           "#ff4a4a",
        "fortifier":           "#4aff9e",
        "opportunist":         "#ffd04a",
        "breakaway":           "#cc88ff",
    }

    def __init__(self, faction_id: str, name: str, archetype: str,
                 budget: float = 0.0,
                 budget_growth_rate: float | None = None,
                 modifiers: dict | None = None,
                 diplomatic_stance: dict | None = None,
                 color: str | None = None,
                 rng: random.Random | None = None) -> None:
        self.id = faction_id
        self.name = name
        # "player_civilization" | "conqueror" | "breakaway"
        self.archetype = archetype
        self.color = color if color is not None else self._ARCHETYPE_COLORS.get(archetype, "#888888")
        self.budget = budget
        self.budget_growth_rate = (
            budget_growth_rate if budget_growth_rate is not None
            else config.BUDGET_GROWTH_RATE
        )
        # {field: additive per-tick bonus applied in compute_drift_deltas, e.g. {"military": 0.02}}
        self.modifiers = modifiers or {}
        # {faction_id: "hostile" | "neutral" | "allied"}
        self.diplomatic_stance = diplomatic_stance or {}
        # Rolled once at creation — faction's attack personality for this game
        conf_range = config.ATTACK_CONFIDENCE_RANGE.get(
            archetype, config.ATTACK_CONFIDENCE_DEFAULT_RANGE
        )
        _rng = rng if rng is not None else random.Random()
        self.attack_confidence = _rng.uniform(*conf_range)
        tech_range = config.ARCHETYPE_STARTING_TECH.get(archetype, (0, 0))
        self.tech_level = _rng.uniform(*tech_range)

    # ── F1: Snapshot-based unified decision (intent-resolution model) ─────────

    def decide(self, snapshot: dict, adjacency: dict, registry: dict,
               rng: random.Random, tick: int,
               damage_history: dict | None = None,
               debug: bool = False) -> dict:
        """Read snapshot, score all viable actions, return Intent dict. No mutations."""
        aweights  = config.ARCHETYPE_ATTRACT_WEIGHTS.get(self.archetype, config.DEFAULT_ATTRACT_WEIGHTS)
        dweights  = config.ARCHETYPE_DECISION_WEIGHTS.get(self.archetype, config.DEFAULT_DECISION_WEIGHTS)
        we        = config.ATTRACT_ECONOMY_SUBWEIGHT
        wp        = config.ATTRACT_POPULATION_SUBWEIGHT
        can_col   = aweights.get("can_colonize", True)
        ten_pri   = aweights.get("tension_primary", False)

        owned_rids = [rid for rid, rd in snapshot.items() if rd["faction_id"] == self.id]

        # ── 1. Build unified candidate pool ───────────────────────────────────
        # attack: enemy-owned hostile neighbor; colonize: unowned neighbor
        seen = set()
        attack_candidates  = {}  # {rid: attractiveness}
        colonize_candidates = {}

        for rid in owned_rids:
            for nid in adjacency.get(rid, []):
                if nid in seen or nid not in snapshot:
                    continue
                seen.add(nid)
                nd = snapshot[nid]
                nf = nd["faction_id"]

                if nf == self.id:
                    continue

                # ── Attractiveness score for this candidate ────────────────
                nfields = nd["fields"]
                factor_1 = (nfields["tension"] / 100.0) if ten_pri else (1.0 - nfields["military"] / 100.0)
                if nf is None:
                    current_value = 0.0
                else:
                    current_value = (nfields["economy"] * we + nfields["population"] * wp) / 100.0
                    current_value *= config.ATTRACT_VALUE_MULTIPLIER

                nb_of_target = adjacency.get(nid, [])
                non_owned    = [n for n in nb_of_target
                                if snapshot.get(n, {}).get("faction_id") != self.id]
                nb_scores    = []
                for n in non_owned:
                    nd2 = snapshot.get(n)
                    if nd2 is None:
                        continue
                    if nd2["faction_id"] is not None:
                        nb_scores.append((nd2["fields"]["economy"] * we
                                          + nd2["fields"]["population"] * wp) / 100.0)
                    else:
                        nb_scores.append(config.EXPANSION_POTENTIAL)
                strategic_position = sum(nb_scores) / len(nb_scores) if nb_scores else 0.0

                attractiveness = (aweights["weakness"] * factor_1
                                  + aweights["value"] * current_value
                                  + aweights["position"] * strategic_position)

                boost = aweights.get("recent_damage_boost", 0.0)
                if boost > 0.0 and damage_history:
                    dmg = damage_history.get(nid, 0.0)
                    attractiveness *= 1.0 + dmg * boost

                if nf is None:
                    if can_col:
                        colonize_candidates[nid] = attractiveness
                else:
                    our_stance   = self.diplomatic_stance.get(nf, "neutral")
                    their_fac    = registry.get(nf)
                    their_stance = their_fac.diplomatic_stance.get(self.id, "neutral") if their_fac else "neutral"
                    if our_stance == "hostile" or their_stance == "hostile":
                        if current_value >= config.MIN_ATTACK_VALUE:
                            attack_candidates[nid] = attractiveness

        # ── 2. Filter attack candidates by expected_net > confidence ──────────
        potential_commit = self.budget * config.ATTACK_COMMIT_FRACTION

        # ── Budget pressure: lower confidence when hoarding ──────────────────
        effective_confidence = self.attack_confidence
        if attack_candidates and self.budget > 0:
            weakest_target_mil = min(
                snapshot[rid]["fields"]["military"] for rid in attack_candidates
            )
            break_even_budget = (weakest_target_mil * config.RESISTANCE_FACTOR) / (
                config.ATTACK_COMMIT_FRACTION * config.ATTACK_EFFICIENCY
            )
            if break_even_budget > 0:
                budget_ratio = self.budget / break_even_budget
                if budget_ratio > config.BUDGET_PRESSURE_THRESHOLD:
                    pressure = config.BUDGET_PRESSURE_THRESHOLD / budget_ratio
                    effective_confidence = self.attack_confidence * pressure

        if attack_candidates:
            weakest_target_mil = min(snapshot[rid]["fields"]["military"] for rid in attack_candidates)
            attack_floor = (
                (weakest_target_mil * config.RESISTANCE_FACTOR + effective_confidence)
                / (config.ATTACK_COMMIT_FRACTION * config.ATTACK_EFFICIENCY)
            )
        else:
            attack_floor = None
        def _target_entrenchment(rid):
            held_since = snapshot[rid].get("held_since_tick")
            if held_since is None:
                return config.ENTRENCHMENT_MAX
            ticks_held = max(0, tick - held_since)
            ratio = min(1.0, ticks_held / config.ENTRENCHMENT_RAMP_TICKS) if config.ENTRENCHMENT_RAMP_TICKS > 0 else 1.0
            return config.ENTRENCHMENT_BASE + (config.ENTRENCHMENT_MAX - config.ENTRENCHMENT_BASE) * ratio

        viable_attacks = {}
        for rid in attack_candidates:
            entrench = _target_entrenchment(rid)
            net = (potential_commit * config.ATTACK_EFFICIENCY
                   - snapshot[rid]["fields"]["military"] * config.RESISTANCE_FACTOR * entrench)
            if net > effective_confidence:
                viable_attacks[rid] = net

        # ── 3. Compute two weighted scores (attack and colonize) ─────────────
        def _norm(val, lo, hi):
            return max(0.0, min(1.0, (val - lo) / (hi - lo))) if val is not None else 0.0

        # Target selection: attractiveness picks the region; expected_net scores the action
        viable_by_attract  = {rid: score for rid, score in attack_candidates.items()
                              if rid in viable_attacks}
        best_attack_rid    = max(viable_by_attract, key=viable_by_attract.get) if viable_by_attract else None
        best_attack_val    = viable_attacks[best_attack_rid]               if best_attack_rid else None
        best_colonize_rid  = max(colonize_candidates, key=colonize_candidates.get) if colonize_candidates else None
        best_colonize_val  = colonize_candidates[best_colonize_rid]        if best_colonize_rid else None

        attack_score   = _norm(best_attack_val,   *config.ATTACK_NORM_RANGE)   * dweights["attack"]  if best_attack_val   is not None else None
        colonize_score = _norm(best_colonize_val, *config.COLONIZE_NORM_RANGE) * dweights["expand"]  if best_colonize_val is not None else None

        # ── 4. Pick winning action ────────────────────────────────────────────
        scored = {}
        if attack_score   is not None: scored["attack"]   = attack_score
        if colonize_score is not None: scored["colonize"] = colonize_score

        best_action = max(scored, key=scored.get) if scored else "accumulate"
        if scored.get(best_action, 0.0) < config.MIN_ACTION_THRESHOLD:
            best_action = "accumulate"
        if best_action == "colonize" and self.budget < config.COLONIZE_COST:
            best_action = "accumulate"

        # ── 6. Build Intent ───────────────────────────────────────────────────
        attack_mode = None
        if best_action == "attack":
            target    = best_attack_rid
            committed = potential_commit
            source    = max(owned_rids, key=lambda r: snapshot[r]["fields"]["military"]) if owned_rids else None
            expected  = best_attack_val

            telegraph_pref = config.ARCHETYPE_TELEGRAPH_PREFERENCE.get(self.archetype, 0.5)
            target_mil = snapshot[best_attack_rid]["fields"]["military"]
            if target_mil > 60:
                telegraph_pref += 0.2
            elif target_mil < 30:
                telegraph_pref -= 0.2
            telegraph_pref = max(0.0, min(1.0, telegraph_pref))
            attack_mode = "telegraph" if rng.random() < telegraph_pref else "surprise"
        elif best_action == "colonize":
            target    = best_colonize_rid
            committed = config.COLONIZE_COST
            source    = next((r for r in owned_rids if target in adjacency.get(r, [])), owned_rids[0] if owned_rids else None)
            expected  = best_colonize_val
        else:
            target, committed, source, expected = None, 0.0, None, None

        intent = {
            "faction_id":      self.id,
            "action":          best_action,
            "target_region":   target,
            "budget_committed": committed,
            "source_region":   source,
            "expected_outcome": expected,
            "attack_mode":     attack_mode,
            "scores": {
                "attack":   attack_score,
                "colonize": colonize_score,
            },
        }

        if debug:
            best_any_rid = max(attack_candidates, key=attack_candidates.get) if attack_candidates else None
            best_any_net = (
                potential_commit * config.ATTACK_EFFICIENCY
                - snapshot[best_any_rid]["fields"]["military"] * config.RESISTANCE_FACTOR
                if best_any_rid else None
            )
            atk_raw = _norm(best_attack_val,    *config.ATTACK_NORM_RANGE)    if best_attack_val    is not None else None
            col_raw = _norm(best_colonize_val,  *config.COLONIZE_NORM_RANGE)  if best_colonize_val  is not None else None
            intent["diag"] = {
                "n_attack_candidates":  len(attack_candidates),
                "n_colonize_candidates": len(colonize_candidates),
                "n_viable_attacks":     len(viable_attacks),
                "potential_commit":     round(potential_commit, 3),
                "attack_confidence":    round(self.attack_confidence, 3),
                "effective_confidence": round(effective_confidence, 3),
                "attack_mode":          attack_mode,
                "best_attack_any": {
                    "rid":          best_any_rid,
                    "attractiveness": round(attack_candidates[best_any_rid], 4) if best_any_rid else None,
                    "military":     round(snapshot[best_any_rid]["fields"]["military"], 2) if best_any_rid else None,
                    "expected_net": round(best_any_net, 4) if best_any_net is not None else None,
                    "viable":       (best_any_rid in viable_attacks) if best_any_rid else None,
                } if attack_candidates else None,
                "best_colonize": {
                    "rid":          best_colonize_rid,
                    "attractiveness": round(best_colonize_val, 4) if best_colonize_val is not None else None,
                } if best_colonize_rid else None,
                "raw_normalized": {
                    "attack":   round(atk_raw, 4) if atk_raw is not None else None,
                    "colonize": round(col_raw, 4) if col_raw is not None else None,
                },
                "weighted_scores": {
                    "attack":   round(attack_score,    4) if attack_score    is not None else None,
                    "colonize": round(colonize_score,  4) if colonize_score  is not None else None,
                },
            }

        return intent

    # ── Reactive reinforce (telegraph defense) ─────────────────────────────────

    def decide_reactive(self, pending_telegraphs: list, snapshot: dict,
                        rng: random.Random) -> dict | None:
        my_threats = [t for t in pending_telegraphs if t["target_faction"] == self.id]
        if not my_threats:
            return None

        worst = max(my_threats, key=lambda t: t["budget_committed"])

        dweights = config.ARCHETYPE_DECISION_WEIGHTS.get(self.archetype, config.DEFAULT_DECISION_WEIGHTS)
        reinforce_prob = min(1.0, dweights["defend"] / 1.5)

        if rng.random() > reinforce_prob:
            return None

        committed = min(
            self.budget * config.REACTIVE_REINFORCE_BUDGET_FRACTION,
            worst["budget_committed"] * 0.5,
        )
        if committed < 1.0:
            return None

        return {
            "faction_id": self.id,
            "action": "reinforce",
            "target_region": worst["target_region"],
            "budget_committed": committed,
        }

    # ── I1: Economic output and military capacity ─────────────────────────────

    def economic_output(self, world) -> float:
        return sum(
            r.fields["economy"]
            for r in world.regions.values()
            if r.faction_id == self.id
        )

    def military_capacity(self, world) -> float:
        return sum(
            r.fields["military"]
            for r in world.regions.values()
            if r.faction_id == self.id
        )

    # ── K1: Budget accumulation ───────────────────────────────────────────────

    def accumulate_budget(self, world) -> float:
        net = sum(
            r.fields["economy"] - config.REGION_MAINTENANCE_COST
            for r in world.regions.values()
            if r.faction_id == self.id and r.fields
        )
        delta = net * self.budget_growth_rate
        self.budget = max(0.0, self.budget + delta)
        return delta

    def to_dict(self) -> dict:
        return {
            "id":                 self.id,
            "name":               self.name,
            "archetype":          self.archetype,
            "budget":             round(self.budget, 3),
            "budget_growth_rate": self.budget_growth_rate,
            "attack_confidence":  round(self.attack_confidence, 2),
            "tech_level":         round(self.tech_level, 4),
            "modifiers":          dict(self.modifiers),
            "diplomatic_stance":  dict(self.diplomatic_stance),
        }


# ── Registry helpers ──────────────────────────────────────────────────────────

def make_registry(*factions) -> dict:
    """Build a {faction_id: Faction} dict from any number of Faction objects."""
    return {f.id: f for f in factions}


def generate_starting_factions(template: str,
                               rng: random.Random | None = None,
                               world=None) -> list:
    """
    Return the starting list of Faction objects for a given world template.
    rng: seeded RNG used to roll per-faction attack_confidence (pass world.rng for
         deterministic per-seed personalities). Falls back to random.Random() if None.
    world: if provided, tech_level is derived from avg population across each faction's
           starting regions (STARTING_TECH_RATIO). Without world, falls back to the
           archetype range roll (used for mid-simulation faction creation).
    Stances are cross-populated; both factions hostile toward each other.
    """
    if template == "isolated_start":
        player = Faction(
            "player", theme.FACTION_DISPLAY_NAMES["player_civilization"], "player_civilization",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"conqueror": "hostile"},
            rng=rng,
        )
        conqueror = Faction(
            "conqueror", theme.FACTION_DISPLAY_NAMES["conqueror"], "conqueror",
            budget=0.0,
            # Militaristic faction: meaningful military drift bonus offsets maintenance decay.
            # 0.5/tick per region lets the conqueror sustain moderate military strength.
            modifiers={"military": 0.05},
            diplomatic_stance={"player": "hostile"},
            rng=rng,
        )
        factions = [player, conqueror]
    elif template == "four_way":
        player = Faction(
            "player", theme.FACTION_DISPLAY_NAMES["player_civilization"], "player_civilization",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"conqueror": "hostile", "fortifier": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        conqueror = Faction(
            "conqueror", theme.FACTION_DISPLAY_NAMES["conqueror"], "conqueror",
            budget=0.0,
            modifiers={"military": 0.05},
            diplomatic_stance={"player": "hostile", "fortifier": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        fortifier = Faction(
            "fortifier", "The Fortifier", "fortifier",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"player": "hostile", "conqueror": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        opportunist = Faction(
            "opportunist", "The Opportunist", "opportunist",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"player": "hostile", "conqueror": "hostile", "fortifier": "hostile"},
            rng=rng,
        )
        factions = [player, conqueror, fortifier, opportunist]
    elif template == "contested_border":
        player = Faction(
            "player", theme.FACTION_DISPLAY_NAMES["player_civilization"], "player_civilization",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"conqueror": "hostile"},
            rng=rng,
        )
        conqueror = Faction(
            "conqueror", theme.FACTION_DISPLAY_NAMES["conqueror"], "conqueror",
            budget=0.0,
            modifiers={"military": 0.05},
            diplomatic_stance={"player": "hostile"},
            rng=rng,
        )
        factions = [player, conqueror]
    elif template == "full_game_50":
        player = Faction(
            "player", theme.FACTION_DISPLAY_NAMES["player_civilization"], "player_civilization",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"conqueror": "hostile", "fortifier": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        conqueror = Faction(
            "conqueror", theme.FACTION_DISPLAY_NAMES["conqueror"], "conqueror",
            budget=0.0,
            modifiers={"military": 0.05},
            diplomatic_stance={"player": "hostile", "fortifier": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        fortifier = Faction(
            "fortifier", "The Fortifier", "fortifier",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"player": "hostile", "conqueror": "hostile", "opportunist": "hostile"},
            rng=rng,
        )
        opportunist = Faction(
            "opportunist", "The Opportunist", "opportunist",
            budget=0.0,
            modifiers={},
            diplomatic_stance={"player": "hostile", "conqueror": "hostile", "fortifier": "hostile"},
            rng=rng,
        )
        factions = [player, conqueror, fortifier, opportunist]
    else:
        raise ValueError(f"No starting factions defined for template: {template!r}")
    if world is not None:
        _apply_population_tech(factions, world)
    return factions

def _apply_population_tech(factions: list, world) -> None:
    """Overwrite tech_level on each faction using avg starting population × STARTING_TECH_RATIO."""
    for faction in factions:
        owned = [r for r in world.regions.values()
                 if r.faction_id == faction.id and r.fields]
        if owned:
            avg_pop = sum(r.fields["population"] for r in owned) / len(owned)
            faction.tech_level = avg_pop * config.STARTING_TECH_RATIO
