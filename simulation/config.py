# Input: none. Output: named constants read by all simulation modules.

DIAGNOSTIC_PRINTS = True  # Set True for tick-by-tick diagnostic output during tuning

# ── Technology (Stage 3.5 A) ─────────────────────────────────────────────────
ENABLE_TECHNOLOGY = True
BASE_TECH_RATE = 0.1
TECH_POPULATION_FLOOR = 0.3
TECH_CONVERGENCE_RATE = 0.1
ARCHETYPE_STARTING_TECH = {
    "conqueror":           (5,  15),
    "fortifier":           (10, 20),
    "warlord":             (5,  10),
    "opportunist":         (8,  15),
    "schism":              (0,   0),
    "player_civilization": (10, 20),
    "breakaway":           (0,   0),
}
ARCHETYPE_TECH_MULTIPLIERS = {
    "conqueror":           {"attack": 0.16, "defense": 0.02, "economy": 0.02},
    "fortifier":           {"attack": 0.03, "defense": 0.09, "economy": 0.08},
    "warlord":             {"attack": 0.14, "defense": 0.04, "economy": 0.02},
    "opportunist":         {"attack": 0.10, "defense": 0.05, "economy": 0.05},
    "schism":              {"attack": 0.12, "defense": 0.04, "economy": 0.04},
    "player_civilization": {"attack": 0.06, "defense": 0.07, "economy": 0.07},
    "breakaway":           {"attack": 0.06, "defense": 0.08, "economy": 0.06},
}
TECH_TIER_BOUNDARIES = [0, 34, 67]  # tier 1: 0–33, tier 2: 34–66, tier 3: 67–100

# ── Diplomacy (Stage 3.5 C–E) ────────────────────────────────────────────────
ENABLE_DIPLOMACY = True
PEACE_FORMATION_THRESHOLD = 80
PEACE_STABILITY_THRESHOLD = 35.0
PEACE_BASE_PROBABILITY = 0.5
ARCHETYPE_PEACE_DISPOSITION = {
    "conqueror": 0.1,
    "fortifier": 2.0,
    "warlord": 0.2,
    "opportunist": 1.0,
    "schism": 0.3,
    "player_civilization": 1.5,
    "breakaway": 0.8,
}
BASE_BETRAYAL_RATE = 0.005
ARCHETYPE_BETRAYAL_WEIGHT = {
    "conqueror": 2.5,
    "fortifier": 0.3,
    "warlord": 2.0,
    "opportunist": 2.0,
    "schism": 1.5,
    "player_civilization": 0.5,
    "breakaway": 1.0,
}
BETRAYAL_OPPORTUNITY_CAP = 3.0
STARTING_STANCE_OVERRIDES = {
    ("conqueror", "player_civilization"): "hostile",
    ("conqueror", "fortifier"):           "hostile",
    ("conqueror", "opportunist"):         "hostile",
    ("conqueror", "warlord"):             "hostile",
    ("conqueror", "schism"):              "hostile",
    ("conqueror", "breakaway"):           "hostile",
    ("schism", "player_civilization"):    "hostile",
    ("schism", "fortifier"):              "hostile",
    ("schism", "opportunist"):            "hostile",
    ("schism", "warlord"):                "hostile",
}

# ── Collision resolution (Stage 3 F5) ────────────────────────────────────────
COLLISION_LOSER_TENSION_BASE         = 5.0   # base tension hit for losing a collision
COLLISION_NARROW_MARGIN              = 0.6   # margin_ratio below this = narrow victory
COLLISION_DOMINANT_MARGIN            = 0.8   # margin_ratio above this = dominant victory
COLLISION_NARROW_MIL_PENALTY         = 0.5   # multiply colony starter military by this on narrow win
COLLISION_RETENTION_MAX              = 0.4   # winner can retain at most this fraction of committed budget
COLLISION_RETENTION_OPPOSITION_SCALE = 0.6   # how strongly opposition erodes retention ceiling
COLLISION_ECONOMY_FLOOR              = 0.4   # economy factor minimum (weakest faction in collision)
COLLISION_ECONOMY_CEILING            = 1.0   # economy factor maximum (strongest faction in collision)

# ── Feature flags ───────────────────────────────────────────────────────────
ENABLE_EVENTS          = True   # proven in Group C
ENABLE_ANTAGONIST      = True   # proven in Group D; still used when ENABLE_FACTIONS=False
ENABLE_FACTIONS        = True   # Stage 0 revision: multi-faction agent loop (Groups I–K)
ENABLE_BORDER_FRICTION = True   # Stage 0 revision: per-tick tension/economy from hostile neighbors (Group J)
ENABLE_RECRUITMENT     = True   # Stage 0 revision: military recovery term in drift (Group J)
ENABLE_TYPED_EDGES     = False  # enabled after Group F is proven
ENABLE_NEIGHBOR_DRIFT  = False  # enabled after Group F is proven
ENABLE_ADJACENCY_BONUS = True   # Stage 1: territorial adjacency bonus on economy drift
ENABLE_OSCILLATION     = True   # Stage 1: sine-wave oscillation on economy and tension drift
ENABLE_EVENTS_STAGE2   = True   # Stage 2: event chain architecture (10-template test set)

# ── Region field initialization — population-first ───────────────────────────
# Population is rolled first; all other fields are derived from it.
# Applies to all factions equally — no per-archetype field ranges at world start.
HOME_POPULATION_RANGE     = (55, 75)
FRONTIER_POPULATION_RANGE = (25, 50)

# Derivation ratios: starting_field = population * ratio + jitter
STARTING_ECO_RATIO     = 1.1   # pop 60 → eco ~66
STARTING_MIL_RATIO     = 0.7   # pop 60 → mil ~42
STARTING_TENSION_RATIO = 0.3   # pop 60 → tension ~18
STARTING_FIELD_JITTER  = 5.0   # ±5 random jitter applied after derivation

# Tech at world start is population-derived (equal footing across factions).
# ARCHETYPE_STARTING_TECH is used only for mid-simulation faction creation.
STARTING_TECH_RATIO    = 0.25  # pop 60 → tech 15

# ── Economy-population capacity coupling ─────────────────────────────────────
ECO_POP_RATIO        = 1.45   # pop 50 supports eco 65; above this → overcapacity decay
ECO_OVERCAPACITY_DECAY = 0.4  # rate at which economy decays when above capacity

# ── Composite axis weights ───────────────────────────────────────────────────
# stability = (military * W_STAB_MILITARY) + ((100 - tension) * W_STAB_TENSION) + (population * W_STAB_POPULATION)
W_STAB_MILITARY    = 0.40
W_STAB_TENSION     = 0.35
W_STAB_POPULATION  = 0.25

# capacity = (economy * W_CAP_ECONOMY) + (population * W_CAP_POPULATION) + (military * W_CAP_MILITARY)
W_CAP_ECONOMY    = 0.50
W_CAP_POPULATION = 0.35
W_CAP_MILITARY   = 0.15

# ── Composite threshold penalties ───────────────────────────────────────────
# If a contributing field drops below its threshold, the composite is multiplied by the penalty.
STAB_MILITARY_THRESHOLD   = 10.0   # below this, stability takes a penalty
STAB_MILITARY_PENALTY     = 0.70
STAB_POPULATION_THRESHOLD = 20.0
STAB_POPULATION_PENALTY   = 0.75

CAP_ECONOMY_THRESHOLD     = 20.0   # below this, capacity takes a penalty
CAP_ECONOMY_PENALTY       = 0.65
CAP_POPULATION_THRESHOLD  = 15.0
CAP_POPULATION_PENALTY    = 0.70

# ── Military strength drift ──────────────────────────────────────────────────
# drift = -military * MILITARY_DECAY_RATE * (1 - economy/100)
MILITARY_DECAY_RATE = 0.006  # fraction of military lost per tick when economy=0 (was 0.03, /5 timescale)

# ── Economy floor ────────────────────────────────────────────────────────────
# Drift, border friction, and standard events cannot push economy below this.
# Represents subsistence-level activity that persists through normal crises.
# Conquest (apply_conquest in faction.py) bypasses this floor.
ECONOMY_FLOOR = 8.0
TENSION_FLOOR = 12.0

# ── Economic output drift ────────────────────────────────────────────────────
# drift = (ECONOMY_BASE_GROWTH * population/100) - (tension/100 * ECONOMY_TENSION_PENALTY_RATE)
ECONOMY_BASE_GROWTH          = 3  # max growth per tick at full population, no tension (was 0.8, /5 timescale)
ECONOMY_TENSION_PENALTY_RATE = 0.40  # drag applied per unit of tension/100 (was 1.5, /5 timescale)

# ── Factional tension drift ──────────────────────────────────────────────────
# economic_tension = ((TENSION_ECONOMY_MIDPOINT - economy) / 100) * TENSION_ECONOMY_RATE * (population / 100)
# stress_pressure  = max(0, TENSION_STRESS_THRESHOLD - stability) * TENSION_STRESS_RATE
# drift = economic_tension + stress_pressure - TENSION_NATURAL_DECAY
TENSION_ECONOMY_RATE       = 0.5   # how strongly economy deviation drives tension
TENSION_ECONOMY_MIDPOINT   = 50.0   # economy level with zero economic pressure on tension
TENSION_STRESS_RATE        = 0.008  # scales how much instability breeds tension (was 0.04, /5 timescale)
TENSION_STRESS_THRESHOLD   = 40.0   # stability below this triggers stress pressure
TENSION_NATURAL_DECAY_RATE = 0.20   # proportional decay: decay = rate * (tension / 100) (was 1.0, /5 timescale)
                                    # higher tension → stronger decay force → real equilibrium

# ── Population drift ─────────────────────────────────────────────────────────
# if economy > POPULATION_SUBSISTENCE: drift = POPULATION_GROWTH_RATE * (1 - population/100)
# else: drift = -(POPULATION_SUBSISTENCE - economy) * POPULATION_DECLINE_RATE
POPULATION_SUBSISTENCE   = 15.0   # economy below this causes population decline
POPULATION_GROWTH_RATE   = 3   # logistic growth coefficient (was 0.25, /5 timescale)
POPULATION_DECLINE_RATE  = 0.2  # decline per unit of economy deficit (was 0.015, /5 timescale)

# ── Subsistence crisis (economy near floor) ─────────────────────────────────
# When economy is within SUBSISTENCE_CRISIS_RANGE of ECONOMY_FLOOR, tension rises
# and population declines proportional to severity. Creates a death spiral that
# makes the economic floor painful rather than a safe equilibrium.
SUBSISTENCE_CRISIS_RANGE  = 3.0    # economy within this of ECONOMY_FLOOR triggers crisis
SUBSISTENCE_TENSION_RATE  = 0.15   # extra tension per tick at floor, scaled by severity and population
SUBSISTENCE_POP_RATE      = 0.08   # extra population decline per tick at floor, scaled by severity

# ── Antagonist (Groups D; kept for backward compat when ENABLE_FACTIONS=False) ──
ANTAGONIST_BUDGET_GROWTH_RATE = 0.04  # budget added per tick (~8 at tick 200)
ANTAGONIST_BUDGET_START       = 0.0
# Drain rates for the Conqueror archetype: pressure_applied * rate = field delta per tick
CONQUEROR_MILITARY_DRAIN_RATE = 0.30  # fraction of allocated pressure that hits military
CONQUEROR_ECONOMY_DRAIN_RATE  = 0.10  # fraction that hits economy

# ── Event system ─────────────────────────────────────────────────────────────
EVENT_NOISE_RANGE  = 10.0  # per-region threshold offset rolled in range [-noise, +noise]
EVENT_GRACE_PERIOD = 3     # no threshold triggers fire during the first N ticks

# ── World templates ──────────────────────────────────────────────────────────
ISOLATED_START_EMPTY_REGION_COUNT = (4, 6)  # range for number of empty regions

# ── Stage 1 — Drift-only isolated start (no factions, no conqueror) ─────────
S1_HOME_MILITARY_RANGE    = (55, 70)
S1_HOME_ECONOMY_RANGE     = (60, 75)
S1_HOME_TENSION_RANGE     = (10, 25)
S1_HOME_POPULATION_RANGE  = (70, 85)

S1_FRONTIER_MILITARY_RANGE    = (20, 35)
S1_FRONTIER_ECONOMY_RANGE     = (25, 40)
S1_FRONTIER_TENSION_RANGE     = (20, 28)
S1_FRONTIER_POPULATION_RANGE  = (15, 30)

S1_EMPTY_REGION_COUNT = (4, 6)

# ── Territorial adjacency bonus (Stage 1) ───────────────────────────────────
NEIGHBOR_ECONOMY_BONUS = 0.05  # economy bonus per inhabited same-faction neighbor, scaled by neighbor eco/100

# ── Oscillation (Stage 1) ───────────────────────────────────────────────────
ECON_OSCILLATION_AMPLITUDE = 6.0     # ±6 economy points (additive, feedback-isolated)
ECON_OSCILLATION_PERIOD    = 15     # ticks per full cycle (50-tick half-cycles for agent windows)
TENSION_OSCILLATION_AMPLITUDE = 2.0  # ±2 tension points (additive, feedback-isolated)
TENSION_OSCILLATION_PERIOD    = 18  # slightly longer than economy so cycles drift apart

# ── Military recruitment (Group J1) ──────────────────────────────────────────
# recruitment = (RECRUITMENT_BASELINE + eco_term) * headroom
# eco_term fires only when economy > RECRUITMENT_THRESHOLD
# baseline always fires (militia from population)
TENSION_RECRUITMENT_SCALE = 0.3  # exponent on (1 - tension/100); lower = tension suppresses recruitment less
RECRUITMENT_BASELINE     = 0.1   # constant recruitment term independent of economy
RECRUITMENT_THRESHOLD    = 20.0   # economy must exceed this for the economy-scaled term
RECRUITMENT_RATE         = 12  # economy-scaled recruitment per tick at full economy, zero tension
RECRUITMENT_CEILING      = 90.0   # recruitment approaches zero as military nears this value;
                                  # drift alone cannot push military past this ceiling

# ── Border friction (Group J2) ────────────────────────────────────────────────
# Applied per-tick to each region that borders a hostile faction's region.
# Tuned low: background stress, not active damage (spec intent: "subtle").
BORDER_FRICTION_TENSION  = 0.5   # tension added per tick from each hostile border
BORDER_FRICTION_ECONOMY  = 0.05   # economy subtracted per tick from each hostile border

# ── Faction agent (Groups K–L) ────────────────────────────────────────────────
BUDGET_GROWTH_RATE          = 0.025 # budget += sum(owned net economy) * this, per tick
REGION_MAINTENANCE_COST     = 8.0   # economy subtracted per owned region before growth calculation
REINFORCE_EFFICIENCY        = 0.5   # fraction of budget spent that converts to military strength
ATTACK_COMMIT_FRACTION      = 0.70  # fraction of current budget committed per attack
ATTACK_CONFIDENCE_RANGE = {         # rolled once per faction at creation; stored on entity
    "conqueror":           (2.0, 6.0),     # very aggressive
    "player_civilization": (20.0, 40.0),   # conservative but not paralyzed
    "breakaway":           (4.0,  8.0),    # scrappy
}
ATTACK_CONFIDENCE_DEFAULT_RANGE = (4.0, 8.0)  # fallback for unknown archetypes
# ── Telegraph vs Surprise attack system ─────────────────────────────────────
SURPRISE_EFFICIENCY_MULT   = 0.5    # attack strength multiplier for surprise attacks
TELEGRAPH_PREP_TICKS       = 1      # ticks between telegraph declaration and execution

ARCHETYPE_TELEGRAPH_PREFERENCE = {
    "conqueror":           0.7,   # prefers overwhelming force (telegraph)
    "warlord":             0.3,   # prefers raids (surprise)
    "fortifier":           0.8,   # methodical when it attacks (telegraph)
    "opportunist":         0.4,   # reads the situation, leans surprise
    "schism":              0.3,   # chaotic, prefers surprise
    "player_civilization": 0.6,   # moderate preference for telegraph
    "breakaway":           0.2,   # desperate, can't afford to be countered
}

# Reactive reinforce: defender response to telegraphed attacks
REACTIVE_REINFORCE_BUDGET_FRACTION = 0.30   # max fraction of budget for reactive reinforce

# Reinforce resolution (used for reactive reinforce)
REINFORCE_EFFICIENCY        = 0.5   # fraction of budget spent that converts to military strength
REINFORCE_VARIANCE_BASE     = (0.85, 1.15)  # base variance multiplier range (±15%)
REINFORCE_VARIANCE_TENSION_SCALE = 0.20     # tension/100 * this extends each side of range
REINFORCE_MIL_CAP = {
    "home":     100,   # Home regions: no reinforcement penalty
    "frontier":  60,   # Frontiers: reinforcement tapers off approaching 60
}

# ── Conqueror attractiveness weights (Group K2) ───────────────────────────────
CONQUEROR_WEAKNESS_WEIGHT = 0.6   # weight on target military weakness
CONQUEROR_VALUE_WEIGHT    = 0.4   # weight on target economic + population value

# ── Budget pressure (Stage 3 tuning) ────────────────────────────────────────
# When budget exceeds break-even attack cost by this ratio, confidence starts dropping.
# At 2x this ratio, confidence is halved. Prevents infinite accumulation.
BUDGET_PRESSURE_THRESHOLD = 1.2

# ── Attack resolution (Group L2) ─────────────────────────────────────────────
ATTACK_EFFICIENCY      = 1.0        # multiplier on committed attack budget
RESISTANCE_FACTOR      = 0.65       # how strongly defender military reduces attack
STOCHASTIC_RANGE       = (0.7, 1.3) # (min, max) random multiplier on net_force
BREAKTHROUGH_THRESHOLD = 15.0       # net_force_mod must exceed this for breakthrough
                                    # below this but > 0 → contested; ≤ 0 → repelled
CONQUEST_THRESHOLD     = 5.0        # defender military below this → conquest

# ── Conquest consequences (Group L3) ─────────────────────────────────────────
CONQUEST_TENSION_SPIKE      = 8.0   # was 15.0, halved for 5x timescale
CONQUEST_POPULATION_LOSS    = 2.0   # was 3.0, halved for 5x timescale
CONQUEST_ECONOMY_DISRUPTION = 5.0   # was 10.0, halved for 5x timescale
CONQUEST_GARRISON_FRACTION  = 0.65  # fraction of committed budget that becomes garrison military

# ── Entrenchment (tenure-based defense bonus) ────────────────────────────────
ENTRENCHMENT_BASE       = 1.0   # defense multiplier at tick 0 of ownership
ENTRENCHMENT_MAX        = 2.0   # defense multiplier at full entrenchment
ENTRENCHMENT_RAMP_TICKS = 3     # ticks to reach max entrenchment

# ── Revolt probability (replaces threshold trigger) ─────────────────────────
REVOLT_BASE_PROBABILITY  = 0.01    # per-region per-tick base probability of revolt
REVOLT_TENSION_EXPONENT  = 0.8     # tension scaling curve (higher = low-tension revolts rarer)
REVOLT_COOLDOWN_TICKS    = 20      # minimum ticks between revolts on same region

# ── Revolt faction creation (Group L4) ───────────────────────────────────────
REVOLT_SUCCESS_RANGE  = (0.30, 0.85)  # range of probability for breakaway formation
REVOLT_MILITARY_STEAL = 0.50          # fraction of region military claimed by breakaway
REVOLT_ECONOMY_STEAL  = 0.30          # fraction of region economy claimed by breakaway

# ── Breakaway starting field buffs ───────────────────────────────────────────
REVOLT_BREAKAWAY_TENSION_CAP = 40.0   # cap tension — revolt succeeded, people are mobilized
REVOLT_BREAKAWAY_POP_FLOOR   = 30.0   # minimum population — revolt needed people
REVOLT_BREAKAWAY_ECO_FLOOR   = 20.0   # minimum economy — seized infrastructure

# ── Unified agent scoring (Stage 3 F1) ───────────────────────────────────────
#
# Per-archetype attractiveness weights. Code reads by archetype name — no branching.
# Adding a new archetype = add a row here, no code changes needed.
ARCHETYPE_ATTRACT_WEIGHTS = {
    "conqueror": {
        "weakness": 0.40, "value": 0.25, "position": 0.35,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
    "warlord": {
        "weakness": 0.20, "value": 0.35, "position": 0.45,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
    "fortifier": {
        "weakness": 0.25, "value": 0.20, "position": 0.55,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
    "opportunist": {
        "weakness": 0.35, "value": 0.30, "position": 0.35,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 1.5, "recent_damage_window": 150,
    },
    "schism": {
        "weakness": 0.20, "value": 0.30, "position": 0.50,
        "tension_primary": True, "can_colonize": False,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
    "player_civilization": {
        "weakness": 0.60, "value": 0.25, "position": 0.15,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
    "breakaway": {
        "weakness": 0.45, "value": 0.30, "position": 0.25,
        "tension_primary": False, "can_colonize": True,
        "recent_damage_boost": 0.0, "recent_damage_window": 0,
    },
}
DEFAULT_ATTRACT_WEIGHTS = {
    "weakness": 0.40, "value": 0.30, "position": 0.30,
    "tension_primary": False, "can_colonize": True,
    "recent_damage_boost": 0.0, "recent_damage_window": 0,
}

# Per-archetype decision weights — bias which action type wins.
ARCHETYPE_DECISION_WEIGHTS = {
    "conqueror":           {"attack": 1.2, "expand": 1.0, "defend": 0.4},
    "warlord":             {"attack": 1.4, "expand": 0.6, "defend": 0.3},
    "fortifier":           {"attack": 0.5, "expand": 0.8, "defend": 1.5},
    "opportunist":         {"attack": 1.0, "expand": 0.7, "defend": 0.6},
    "schism":              {"attack": 1.3, "expand": 0.0, "defend": 0.5},
    "player_civilization": {"attack": 0.3, "expand": 0.5, "defend": 1.5},
    "breakaway":           {"attack": 0.6, "expand": 0.3, "defend": 1.4},
}
DEFAULT_DECISION_WEIGHTS = {"attack": 0.8, "expand": 0.6, "defend": 0.8}

# Sub-weights within the current_value factor (shared across archetypes)
ATTRACT_ECONOMY_SUBWEIGHT    = 0.60
ATTRACT_POPULATION_SUBWEIGHT = 0.40
EXPANSION_POTENTIAL          = 0.15  # score given to uninhabited neighbors of a colonize candidate

# Normalization ranges (maps raw score to 0–1 before weighting)
ATTACK_NORM_RANGE    = (0.0, 40.0)
COLONIZE_NORM_RANGE  = (0.0, 1.0)

# Minimum weighted score to act; below this → accumulate
MIN_ACTION_THRESHOLD = 0.05

# ── Colonization (Stage 3 E1) ─────────────────────────────────────────────────
COLONIZE_COST             = 20.0   # budget spent to claim an uninhabited region
COLONY_START_MILITARY     = 10.0   # starter military for a new colony
COLONY_START_ECONOMY      = 15.0   # starter economy
COLONY_START_TENSION      = 20.0   # starter tension
COLONY_START_POPULATION   = 10.0   # starter population
