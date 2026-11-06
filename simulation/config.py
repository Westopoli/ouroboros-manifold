# Input: none. Output: named constants read by all simulation modules.

DIAGNOSTIC_PRINTS = True  # Set True for tick-by-tick diagnostic output during tuning

# ── Technology (Stage 3.5 A) ─────────────────────────────────────────────────
ENABLE_TECHNOLOGY = True
BASE_TECH_RATE = 0.35
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
    ("fortifier", "player_civilization"): "hostile",
    ("fortifier", "opportunist"):         "hostile",
    ("opportunist", "player_civilization"): "hostile",
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
ECO_POP_RATIO        = 0.85   # pop 50 supports eco 42.5; above this → overcapacity decay
ECO_OVERCAPACITY_DECAY = 15.0  # rate at which economy decays when above capacity

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
ECONOMY_BASE_GROWTH          = 2.0  # max growth per tick at full population, no tension
ECONOMY_TENSION_PENALTY_RATE = 0.40  # drag applied per unit of tension/100 (was 1.5, /5 timescale)

# ── Factional tension drift ──────────────────────────────────────────────────
# economic_tension = ((TENSION_ECONOMY_MIDPOINT - economy) / 100) * TENSION_ECONOMY_RATE * (population / 100)
# stress_pressure  = max(0, TENSION_STRESS_THRESHOLD - stability) * TENSION_STRESS_RATE
# drift = economic_tension + stress_pressure - TENSION_NATURAL_DECAY
TENSION_ECONOMY_RATE       = 0.5   # how strongly economy deviation drives tension
TENSION_ECONOMY_MIDPOINT   = 50.0   # economy level with zero economic pressure on tension
TENSION_STRESS_RATE        = 0.008  # scales how much instability breeds tension (was 0.04, /5 timescale)
TENSION_STRESS_THRESHOLD   = 40.0   # stability below this triggers stress pressure
TENSION_NATURAL_DECAY_RATE = 0.20   # proportional decay: decay = rate * (tension / 100)
                                    # higher tension → stronger decay force → real equilibrium

# ── Population drift ─────────────────────────────────────────────────────────
# if economy > POPULATION_SUBSISTENCE: drift = POPULATION_GROWTH_RATE * (1 - population/100)
# else: drift = -(POPULATION_SUBSISTENCE - economy) * POPULATION_DECLINE_RATE
POPULATION_SUBSISTENCE   = 15.0   # economy below this causes population decline
POPULATION_GROWTH_RATE   = 2.0   # logistic growth coefficient
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

# ── World generation ─────────────────────────────────────────────────────────
WORLD_REGION_COUNT_RANGE = (40, 60)
WORLD_FACTIONS_PER_GAME = 15
WORLD_EXTRA_EDGE_RATIO = 0.12
WORLD_MIN_FACTION_SEPARATION = 1

# ── Stage 1 — Drift-only isolated start (no factions, no conqueror) ─────────
S1_HOME_MILITARY_RANGE    = (55, 70)
S1_HOME_ECONOMY_RANGE     = (60, 75)
S1_HOME_TENSION_RANGE     = (10, 25)
S1_HOME_POPULATION_RANGE  = (70, 85)

S1_FRONTIER_MILITARY_RANGE    = (20, 35)
S1_FRONTIER_ECONOMY_RANGE     = (25, 40)
S1_FRONTIER_TENSION_RANGE     = (20, 28)
S1_FRONTIER_POPULATION_RANGE  = (15, 30)


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
BORDER_FRICTION_TENSION  = 0.15  # tension added per tick from each hostile border
BORDER_FRICTION_ECONOMY  = 0.05   # economy subtracted per tick from each hostile border

# ── Faction agent (Groups K–L) ────────────────────────────────────────────────
BUDGET_GROWTH_RATE          = 0.025 # budget += sum(owned net economy) * this, per tick
REGION_MAINTENANCE_COST     = 8.0   # economy subtracted per owned region before growth calculation
ATTACK_COMMIT_FRACTION      = 0.70  # fraction of current budget committed per attack
ATTACK_CONFIDENCE_RANGE = {         # rolled once per faction at creation; stored on entity
    "conqueror":           (2.0, 6.0),     # very aggressive
    "fortifier":           (4.0, 10.0),    # methodical but willing
    "player_civilization": (3.0, 8.0),      # similar to other factions
    "breakaway":           (2.0,  5.0),    # scrappy — lowered so breakaways act sooner
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

# ── Budget pressure (Stage 3 tuning) ────────────────────────────────────────
# When budget exceeds break-even attack cost by this ratio, confidence starts dropping.
# At 2x this ratio, confidence is halved. Prevents infinite accumulation.
BUDGET_PRESSURE_THRESHOLD = 0.8

# ── Attack resolution (Group L2) ─────────────────────────────────────────────
ATTACK_EFFICIENCY      = 1.0        # multiplier on committed attack budget
RESISTANCE_FACTOR      = 0.55       # how strongly defender military reduces attack
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
ENTRENCHMENT_RAMP_TICKS = 100   # ticks to reach max entrenchment

# ── Revolt probability (replaces threshold trigger) ─────────────────────────
REVOLT_BASE_PROBABILITY  = 0.007   # per-region per-tick base probability of revolt (lowered from 0.015 for admin revolt coexistence)
REVOLT_TENSION_EXPONENT  = 0.8     # tension scaling curve (higher = low-tension revolts rarer)
REVOLT_COOLDOWN_TICKS    = 12      # minimum ticks between revolts on same region

# ── Revolt faction creation (Group L4) ───────────────────────────────────────
REVOLT_SUCCESS_RANGE  = (0.50, 0.95)  # range of probability for breakaway formation
REVOLT_MILITARY_STEAL = 0.60          # fraction of region military claimed by breakaway
REVOLT_ECONOMY_STEAL  = 0.40          # fraction of region economy claimed by breakaway

# ── Latent loyalty (revolt reversion) ───────────────────────────────────────
LATENT_LOYALTY_TICKS = 20          # ticks after conquest where revolts can restore previous faction
LATENT_LOYALTY_REVERT_CHANCE = 0.5 # probability a revolt restores previous faction vs new breakaway

# ── Breakaway starting field buffs ───────────────────────────────────────────
REVOLT_BREAKAWAY_TENSION_CAP = 40.0   # cap tension — revolt succeeded, people are mobilized
REVOLT_BREAKAWAY_POP_FLOOR   = 25.0   # minimum population — matches COLONY_START_POPULATION
REVOLT_BREAKAWAY_ECO_FLOOR   = 20.0   # minimum economy — seized infrastructure

MIN_ATTACK_VALUE       = 0.05   # don't attack regions worth less than this (eco+pop component)
ATTRACT_VALUE_MULTIPLIER = 2.0  # amplify value component so developed regions outscore wastelands
ZOMBIE_CLEANUP_TICKS   = 50     # ticks before zombie breakaway can be absorbed

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
    "fortifier":           {"attack": 0.8, "expand": 0.8, "defend": 1.5},
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
COLONY_START_ECONOMY      = 20.0   # starter economy
COLONY_START_TENSION      = 20.0   # starter tension
COLONY_START_POPULATION   = 25.0   # starter population

# ── Administrative revolts (Stage 4) ─────────────────────────────────────────
ENABLE_ADMIN_REVOLTS           = True
ADMIN_REVOLT_BASE_RATE         = 0.001   # per-region per-tick base probability
ADMIN_REVOLT_SCALING_RATE      = 0.0005  # quadratic scaling coefficient above inflection
ADMIN_REVOLT_INFLECTION_POINT  = 4       # territory count where quadratic scaling begins
ADMIN_REVOLT_CHAIN_LENGTH_RANGE = (3, 8) # total ticks for separatist chain to complete

# ── Lifecycle phase classification (Stage 4) ─────────────────────────────────
LIFECYCLE_EXPANSION_EMPTY_THRESHOLD  = 0.3   # >30% of accessible regions empty → expansion
LIFECYCLE_CONFLICT_ATTACK_RATE       = 0.05  # attacks per tick threshold → conflict
LIFECYCLE_OVEREXTENSION_DRAIN_RATIO  = 0.4   # maintenance/income ratio → overextended
LIFECYCLE_FRAGMENTATION_REVOLT_RATE  = 0.02  # revolts per tick → fragmenting

# ── Time jump (Stage 4) ─────────────────────────────────────────────────────
TIME_JUMP_MIN_TICKS = 20
TIME_JUMP_MAX_TICKS = 100
TIME_JUMP_TICKS_PER_CHAPTER = 50

# ── Keyframe selection (Stage 11) ──────────────────────────────────────────
KEYFRAME_MAX_PER_TIME_JUMP = 12
OWNERSHIP_TIMELINE_STRIDE = 2  # snapshot every Nth tick; 1 = every tick, 5-10 = smoother transitions


# ── Character selector (Stage 5.5) ──────────────────────────────────────────
SELECTOR_MIN_CHAPTERS          = 2      # minimum chapters before rotation is eligible
SELECTOR_HARD_CAP              = 6      # maximum chapters before forced rotation
SELECTOR_DELTA_SAFE            = 200.0  # total region delta above which rotation probability is minimal
SELECTOR_MAX_ROTATION_PROB     = 0.8    # rotation probability when delta == 0 (quiet jump)
SELECTOR_MIN_ROTATION_PROB     = 0.1    # rotation probability when delta >= DELTA_SAFE
SELECTOR_CRISIS_THRESHOLD      = 20.0   # stability below this vetoes rotation
SELECTOR_POOL_PREVIOUS_WEIGHT  = 0.70   # probability of drawing from previous lineage pool
SELECTOR_POOL_NEMESIS_WEIGHT   = 0.20   # probability of drawing from nemesis pool
SELECTOR_POOL_UNRELATED_WEIGHT = 0.10   # probability of drawing from unrelated pool
SELECTOR_RECENCY_PENALTY_WINDOW = 1     # lineages played within this many rotations get 0 recency score
SELECTOR_GAP_BONUS_PEAK        = 4      # chapters ago at which gap bonus peaks
SELECTOR_PROXIMITY_HOPS        = 2      # max adjacency hops for "near mission region" candidate search
# Pool weights dict derived from the three authoritative constants above.
LINEAGE_POOL_WEIGHTS = {
    "previous_descendant": SELECTOR_POOL_PREVIOUS_WEIGHT,
    "nemesis_descendant":  SELECTOR_POOL_NEMESIS_WEIGHT,
    "unrelated":           SELECTOR_POOL_UNRELATED_WEIGHT,
}

# ── Mission (Stage 5.5 / reconciliation Phase 7) ─────────────────────────
REFUSAL_TENSION_PENALTY_PCT = 8   # tension +8% of deficit when player refuses a mission
ARCHETYPE_TIME_LIMITS = {         # base time limits in tactical ticks (20/sec)
    "defensive_stand":      3600,  # 3 min
    "siege_breaking":       5400,  # 4.5 min
    "assault":              4800,  # 4 min
    "reconquest":           6000,  # 5 min
    "counterinsurgency":    4200,  # 3.5 min
    "suppression":          3600,  # 3 min
    "containment":          5400,  # 4.5 min
    "multi_front_defense":  4800,  # 4 min
    "interception":         3000,  # 2.5 min
    "evacuation":           2400,  # 2 min
}
TIME_PRESSURE_SCALING = 0.2       # urgency scales time limit down by up to 20%
TIME_LIMIT_FLOOR_PCT  = 0.6       # time limit never drops below 60% of base

# ── Objective defaults (Stage 11d) ───────────────────────────────────────
OBJECTIVE_ZONE_RADIUS_DEFAULT       = 600    # world units
OBJECTIVE_HOLD_DURATION_TICKS_DEFAULT = 1200  # 60 seconds at 20 ticks/sec
OBJECTIVE_EXTRACTION_RADIUS_DEFAULT = 200    # world units

# ── Chronicle distiller (Stage 5) ─────────────────────────────────────────
CHRONICLE_MIN_ENTRIES                = 5
CHRONICLE_MAX_ENTRIES                = 10
SIGNIFICANCE_DELTA_SCALE             = 50.0
SIGNIFICANCE_DELTA_CAP               = 3.0
SIGNIFICANCE_MISSION_REGION_BONUS    = 0.5
SIGNIFICANCE_CHARACTER_BONUS         = 0.3
SIGNIFICANCE_CHAIN_LENGTH_BONUS      = 0.1
CHAIN_LENGTH_CAP                     = 5
SIGNIFICANCE_LINEAGE_REGION_BONUS    = 0.8

# ── Naming system (Stage 5) ────────────────────────────────────────────────
NAME_REUSE_COOLDOWN_TICKS                  = 500   # ticks after death before name returns to pool
NAME_REUSE_MAIN_CHARACTER_COOLDOWN_TICKS   = 4500  # extended cooldown for player's active commanders
NAME_DEDUP_THRESHOLD           = 3      # minimum Levenshtein distance between names in same faction
PLAYER_FACTION_SUBSET_WIDTH    = (3, 4, 4)  # (roots, patterns, tags) — wider than default
DEFAULT_FACTION_SUBSET_WIDTH   = (2, 3, 3)  # (roots, patterns, tags) — standard width

# ── Coherence ledger (Stage 5) ─────────────────────────────────────────────
LINEAGE_FERTILITY_RATE         = 0.03   # descendants per lineage member per tick during time jumps
LINEAGE_SPREAD_PROBABILITY     = 0.1    # probability a new descendant is placed in an adjacent region
REGIONAL_COMMANDER_DEATH_PROB  = 0.3    # probability regional commander dies on conquest
NATURAL_DEATH_BASE_AGE         = 200    # tick-age at which natural death probability begins
NATURAL_DEATH_RATE             = 0.01   # per-tick death probability above base age
CHARACTER_ATTACHMENT_TIER_THRESHOLD = 3  # minimum event significance tier for character attachment

# ── Library builder / validator (Stage 5) ──────────────────────────────────
FRAGMENT_DEDUP_THRESHOLD       = 3      # minimum Levenshtein distance between fragments in same pool
BUILDER_DEDUP_LOSS_FLAG        = 0.30   # flag category if >30% lost to dedup
BUILDER_NAME_OVERSHOOT         = 1.10   # generate 10% extra names to absorb dedup losses
LIFESPAN_MIN                   = 150    # minimum lifespan in ticks
LIFESPAN_MAX                   = 350    # maximum lifespan in ticks

# ── Tactical engine core (Stage 6) ──────────────────────────────────────────
TACTICAL_TICK_RATE             = 20      # ticks per second
TACTICAL_TICK_DURATION         = 0.05    # seconds per tick (1 / TICK_RATE)
ATTACK_BACKSWING_SEC           = 0.5     # movement pause after firing (SC2-style backswing, prevents chase jitter)

# ── Canvas sizing (Stage 6) ─────────────────────────────────────────────────
CANVAS_SMALL                   = (8000, 8000)
CANVAS_MEDIUM                  = (16000, 16000)
CANVAS_LARGE                   = (24000, 24000)
CANVAS_SIMULATION_MODIFIER_RANGE = 0.30  # ±30% canvas size variation

# ── Category multiplier matrix (Stage 6) ────────────────────────────────────
CATEGORY_MULTIPLIER = {
    "Strike": {"Strike": 1.0, "Line": 0.75, "Siege": 1.5},
    "Line":   {"Strike": 1.5, "Line": 1.0,  "Siege": 0.75},
    "Siege":  {"Strike": 0.20, "Line": 1.5,  "Siege": 1.0},
}

# ── Unit stat baselines — Tier 2 (Stage 6) ──────────────────────────────────
UNIT_STATS = {
    "Raider":      {"category": "Strike", "hp": 250,  "base_damage": 9,    "attack_interval": 0.8,
                    "attack_range": 200, "speed": 150, "sensor_radius": 800,
                    "layer_transition_time": 1.0, "aoe_radius": 0},
    "Interceptor": {"category": "Strike", "hp": 325,  "base_damage": 6,    "attack_interval": 1.0,
                    "attack_range": 250, "speed": 130, "sensor_radius": 1000,
                    "layer_transition_time": 1.2, "aoe_radius": 0},
    "Vanguard":    {"category": "Line",   "hp": 500,  "base_damage": 7.5,  "attack_interval": 1.2,
                    "attack_range": 300, "speed": 80,  "sensor_radius": 700,
                    "layer_transition_time": 2.5, "aoe_radius": 0},
    "Warden":      {"category": "Line",   "hp": 375,  "base_damage": 4,    "attack_interval": 1.5,
                    "attack_range": 350, "speed": 70,  "sensor_radius": 800,
                    "layer_transition_time": 2.0, "aoe_radius": 0},
    "Bombard":     {"category": "Siege",  "hp": 400,  "base_damage": 17.5, "attack_interval": 3.0,
                    "attack_range": 1200, "speed": 50,  "sensor_radius": 300,
                    "layer_transition_time": 4.0, "aoe_radius": 150},
    "Bastion":     {"category": "Siege",  "hp": 1050, "base_damage": 7,    "attack_interval": 1.8,
                    "attack_range": 800, "speed": 40,  "sensor_radius": 300,
                    "layer_transition_time": 5.0, "aoe_radius": 0},
}

# ── AoE damage cap (Stage 6) ────────────────────────────────────────────────
AOE_DAMAGE_CAP_MULTIPLIER      = 4.0

# ── Elevation (Stage 6, era-configurable) ────────────────────────────────────
ELEVATION_DAMAGE_BONUS_ENABLED = False   # disabled for space era
ELEVATION_DAMAGE_BONUS_PER_TIER = 0.10
ELEVATION_SENSOR_BONUS_PER_TIER = 0.15

# ── Ability parameters (Stage 6) ────────────────────────────────────────────
SURGE_SPEED_MULTIPLIER         = 2.5
SURGE_DAMAGE_MULTIPLIER        = 2.0
SURGE_DURATION_TICKS           = 60      # 3 sec
SURGE_COOLDOWN_TICKS           = 1500    # 75 sec

INTERCEPT_DETECTION_RADIUS     = 350
INTERCEPT_SPEED_MULTIPLIER     = 1.8
INTERCEPT_DAMAGE_MULTIPLIER    = 1.5
INTERCEPT_COOLDOWN_TICKS       = 600     # 30 sec

BRACE_WINDUP_TICKS             = 40      # 2 sec
BRACE_DAMAGE_REDUCTION         = 0.50
BRACE_DAMAGE_MULTIPLIER        = 1.3
BRACE_COOLDOWN_TICKS           = 700     # 35 sec

RALLY_RADIUS                   = 400
RALLY_HEAL_AMOUNT              = 112
RALLY_COOLDOWN_TICKS           = 1500    # 75 sec

WARDEN_AURA_RADIUS             = 300
WARDEN_AURA_DAMAGE_REDUCTION   = 0.10
WARDEN_AURA_REPAIR_RATE        = 0.075   # HP per tick

BARRAGE_DAMAGE_MULTIPLIER      = 3.0
BARRAGE_RADIUS                 = 100
BARRAGE_TELEGRAPH_TICKS        = 30      # 1.5 sec
BARRAGE_COOLDOWN_TICKS         = 1800    # 90 sec

FORTIFY_RADIUS                 = 350
FORTIFY_DAMAGE_REDUCTION       = 0.20
FORTIFY_DURATION_TICKS         = 400     # 20 sec
FORTIFY_SPEED_MULTIPLIER       = 0.4
FORTIFY_COOLDOWN_TICKS         = 1400    # 70 sec

# ── Fog of war (Stage 6) ────────────────────────────────────────────────────
CONE_LAYER_1_FACTOR            = 0.50
CONE_LAYER_2_FACTOR            = 0.20
CONE_LAYER_3_FACTOR            = 0.0
VANTAGE_CONE_MULTIPLIER        = 2.0
VANTAGE_EXTRA_LAYER            = 1

PULSE_RADIUS                   = 500
PULSE_REVEAL_TICKS             = 40      # 2 sec
PULSE_COOLDOWN_TICKS           = 400     # 20 sec

# ── Pathfinding (Stage 6) ───────────────────────────────────────────────────
NAVMESH_OBSTACLE_THRESHOLD     = 0.7
NAVMESH_CELL_SIZE              = 100
SPATIAL_HASH_CELL_SIZE         = 300  # sensor-pursuit queries — large cells keep long-range march queries cheap
TARGET_HASH_CELL_SIZE          = 100  # attack-range ring search — finer than sensor hash, coarser than collision
TARGETING_COHORT_COUNT         = 4    # stagger acquisition queries across N ticks; validation every tick
STEERING_OBSTACLE_AVOIDANCE_RANGE = 50
UNIT_COLLISION_RADIUS          = 15
STEERING_PROBE_DIST            = 40
STEERING_DETOUR_MIN_DIST       = 60
HARD_COLLISION_ENABLED         = True
COLLISION_RESOLUTION_ITERATIONS = 10

# ── Formation movement (formation_move_spec) ─────────────────────────────────
FORMATION_MOVE_ENABLED         = True    # kill switch: set False to restore pre-formation behavior
ARRIVAL_TOLERANCE_MULT         = 1.5     # per-unit slot arrival radius multiplier
GROUP_ARRIVAL_RADIUS           = 2.0 * UNIT_COLLISION_RADIUS  # centroid-arrival threshold
MAGIC_BOX_SPREAD_RADIUS        = 450.0   # max centroid-to-unit distance before formation offsets are abandoned

# ── Objectives and outcome classification (Stage 6) ─────────────────────────
OUTCOME_WEIGHT_OBJECTIVE       = 0.75
OUTCOME_WEIGHT_RETENTION       = 0.25

OUTCOME_THRESHOLDS = {
    "defensive_stand":     [0.20, 0.40, 0.60, 0.80],
    "siege_breaking":      [0.20, 0.40, 0.60, 0.80],
    "reconquest":          [0.25, 0.45, 0.65, 0.82],
    "assault":             [0.25, 0.45, 0.65, 0.82],
    "suppression":         [0.20, 0.40, 0.60, 0.80],
    "multi_front_defense": [0.15, 0.35, 0.55, 0.75],
    "interception":        [0.20, 0.40, 0.60, 0.80],
    "evacuation":          [0.30, 0.50, 0.65, 0.80],
    "containment":         [0.20, 0.40, 0.60, 0.80],
    "counterinsurgency":   [0.20, 0.40, 0.60, 0.80],
}

# ── Power rating (Stage 6) ──────────────────────────────────────────────────
POWER_RATING_COVER_ASSUMPTION  = 0.15    # average cover density assumption for effective HP
RANGE_NORMALIZATION            = 600
SPEED_NORMALIZATION            = 150
ABILITY_POWER_BONUS = {
    "Raider": 0.15, "Interceptor": 0.12, "Vanguard": 0.20,
    "Warden": 0.25, "Bombard": 0.18, "Bastion": 0.20,
}
AOE_POWER_MULTIPLIER           = 1.5

# ── Replay (Stage 6) ────────────────────────────────────────────────────────
REPLAY_FORMAT                  = "json"

# ── Behavior scripts (Stage 7.5) ────────────────────────────────────────────
ENABLE_BEHAVIOR_SCRIPTS             = True    # flipped True in Stage 7.5 Checkpoint I
SCRIPT_EVAL_INTERVAL_TICKS          = 40      # 2 sec at 20 Hz
SCRIPT_NOISE_DEFAULT_PCT            = 0.15    # threshold noise when transition omits noise_pct
SCRIPT_TIMER_NOISE_DEFAULT_PCT      = 0.20    # timer noise when transition omits noise_pct
COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS = {
    "concentrated": 0.25,   # 3 cells: 2 ambush + 1 patrol
    "dispersed":    0.50,   # 4 cells: 2 ambush + 1 patrol + 1 sleeper
    "fragmented":   0.25,   # 6 cells: 3 ambush + 1 patrol + 2 sleepers
}
SCRIPT_FALLBACK_OWNERSHIP           = (0.33, 0.33, 0.34)  # (player, neutral, enemy) for non-prototype archetypes

# ── Debrief and metrics (Stage 12) ──────────────────────────────────────────
METRICS_SAMPLE_INTERVAL_SEC         = 1.0
IMPACT_PREVIEW_MAX_SENTENCES        = 3

# ── Bug report (Stage 12) ─────────────────────────────────────────────────
BUG_REPORT_BUFFER_SECONDS           = 5
BUG_REPORT_BUFFER_CADENCE_SEC       = 1.0
BUG_REPORT_COMMAND_BUFFER_SECONDS   = 5
BUG_REPORT_OUTPUT_DIR               = "logs/reports"

# ── Autosave (Stage 12) ───────────────────────────────────────────────────
AUTOSAVE_SLOT_ID                    = "autosave"

# ── Unit facing (Stage 12.5) ──────────────────────────────────────────────
FACING_ROTATION_SPEED_STRIKE        = 6.0   # rad/s — fastest
FACING_ROTATION_SPEED_LINE          = 4.0   # rad/s
FACING_ROTATION_SPEED_SIEGE         = 2.5   # rad/s — slowest

# ── Stage 12 kill switches ────────────────────────────────────────────────
ENABLE_STAGE12_DEBRIEF              = True
ENABLE_STAGE12_AUTOSAVE             = True
ENABLE_STAGE12_BUG_REPORT           = True

# ── Mission generator trigger thresholds (Stage 5.5) ────────────────────────
SIEGE_BREAKING_MIN_TICKS            = 200
SUPPRESSION_MAX_AGE                 = 300
EVAC_MILITARY_THRESHOLD             = 15
EVAC_ECONOMY_THRESHOLD              = 20
EVAC_STABILITY_THRESHOLD            = 15
CONTAINMENT_EXPANSION_THRESHOLD     = 2

# ── Mission generator scoring (Stage 5.5) ───────────────────────────────────
GENERATOR_URGENCY_WEIGHT            = 0.5
GENERATOR_RELEVANCE_WEIGHT          = 0.3
GENERATOR_PREFERENCE_WEIGHT         = 0.2
GENERATOR_TOP_N_CANDIDATES          = 5
GENERATOR_DEFAULT_PREFERENCE        = 0.5
GENERATOR_RARE_PREFERENCE           = 0.1
ARCHETYPE_TIME_LIMITS = {
    "defensive_stand": 300, "siege_breaking": 400, "reconquest": 350,
    "assault": 400, "suppression": 250, "multi_front_defense": 450,
    "interception": 300, "evacuation": 250, "containment": 400,
    "counterinsurgency": 300,
}

# ── Urgency scoring (Stage 5.5) ─────────────────────────────────────────────
URGENCY_FIELD_WEIGHT                = 0.4
URGENCY_CONFLICT_WEIGHT             = 0.4
URGENCY_CHAIN_WEIGHT                = 0.2

# ── Relevance scoring (Stage 5.5) ───────────────────────────────────────────
RELEVANCE_LINEAGE_WEIGHT            = 0.4
RELEVANCE_PROXIMITY_WEIGHT          = 0.3
RELEVANCE_ARCHETYPE_WEIGHT          = 0.3
RELEVANCE_MAX_HOPS                  = 5
RELEVANCE_ARCHETYPE_FIT_THRESHOLD   = 3

# ── Force allocation (Stage 5.5) ────────────────────────────────────────────
BUDGET_TO_POWER_SCALE               = 300.0   # A1 — 2× to put mission unit counts in 30–100 band
MILITARY_TO_POWER_SCALE             = 2000.0  # A1 — same
PARITY_BREAKPOINTS                  = [
    (0.0, 0.80),
    (0.3, 0.85),
    (0.5, 0.90),
    (0.7, 0.95),
    (1.0, 1.00),
]
PARITY_EASY_FLOOR                   = 0.95
PARITY_HARD_CEILING                 = 0.85
PARITY_FLOOR                        = 0.75    # hard floor — skilled player can always win
CAPACITY_SHORTFALL_THRESHOLD        = 0.4
CAPACITY_SHORTFALL_REDUCTION        = 0.20

# ── Insurgent force sizing (Stage 5.5) ──────────────────────────────────────
INSURGENT_MIL_HIGH_POP_RANGE        = (40, 70)
INSURGENT_MIL_LOW_POP_RANGE         = (20, 50)
INSURGENT_POP_HIGH_THRESHOLD        = 70       # population >= this uses high range
INSURGENT_POP_LOW_THRESHOLD         = 25       # population <= this uses low range

# ── Asset profiles (Stage 5.5) ──────────────────────────────────────────────
ASSET_PROFILES = {
    "defensive_stand":     {"Raider": 0.05, "Interceptor": 0.10, "Vanguard": 0.15, "Warden": 0.15, "Bombard": 0.15, "Bastion": 0.40},
    "siege_breaking":      {"Raider": 0.15, "Interceptor": 0.10, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.20, "Bastion": 0.20},
    "reconquest":          {"Raider": 0.20, "Interceptor": 0.10, "Vanguard": 0.30, "Warden": 0.10, "Bombard": 0.20, "Bastion": 0.10},
    "assault":             {"Raider": 0.15, "Interceptor": 0.15, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.25, "Bastion": 0.10},
    "suppression":         {"Raider": 0.25, "Interceptor": 0.20, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.05, "Bastion": 0.15},
    "multi_front_defense": {"Raider": 0.10, "Interceptor": 0.15, "Vanguard": 0.20, "Warden": 0.15, "Bombard": 0.15, "Bastion": 0.25},
    "interception":        {"Raider": 0.25, "Interceptor": 0.20, "Vanguard": 0.25, "Warden": 0.10, "Bombard": 0.10, "Bastion": 0.10},
    "evacuation":          {"Raider": 0.10, "Interceptor": 0.05, "Vanguard": 0.10, "Warden": 0.15, "Bombard": 0.05, "Bastion": 0.55},
    "containment":         {"Raider": 0.05, "Interceptor": 0.15, "Vanguard": 0.15, "Warden": 0.20, "Bombard": 0.10, "Bastion": 0.35},
    "counterinsurgency":   {"Raider": 0.25, "Interceptor": 0.25, "Vanguard": 0.20, "Warden": 0.15, "Bombard": 0.05, "Bastion": 0.10},
}

# ── Canvas size and reinforcements (Stage 5.5) ──────────────────────────────
CANVAS_SIZE_RANGES = {
    "small":  (8000, 12000),
    "medium": (12000, 20000),
    "large":  (20000, 28000),
}
ARCHETYPE_BASE_CANVAS = {
    "defensive_stand": "medium", "siege_breaking": "large", "reconquest": "medium",
    "assault": "large", "suppression": "small", "multi_front_defense": "large",
    "interception": "medium", "evacuation": "medium", "containment": "large",
    "counterinsurgency": "small",
}
MILITARY_TO_STRUCTURES_SCALE        = 0.06
STRUCTURE_COUNT_RANGE = {
    "small":  (2, 4),
    "medium": (3, 6),
    "large":  (4, 8),
}
STRUCTURE_PRODUCTION_RATE           = 0.022
# Player/enemy/neutral structure split per archetype: (player_frac, enemy_frac, neutral_frac)
ARCHETYPE_STRUCTURE_SPLIT = {
    "defensive_stand":     (0.50, 0.25, 0.25),
    "siege_breaking":      (0.33, 0.33, 0.34),
    "reconquest":          (0.25, 0.50, 0.25),
    "assault":             (0.25, 0.50, 0.25),
    "suppression":         (0.40, 0.30, 0.30),
    "multi_front_defense": (0.40, 0.35, 0.25),
    "interception":        (0.33, 0.34, 0.33),
    "evacuation":          (0.50, 0.25, 0.25),
    "containment":         (0.33, 0.34, 0.33),
    "counterinsurgency":   (0.40, 0.30, 0.30),
}

# ── Outcome Resolver ──
# Consequence tables: transcribed from docs/bible_history/bible_2_00_missions.md success spectrums.
# Each delta: field, form ("deficit" = +pct of (100-current), "current" = pct of current), pct, target.
# Positive pct = field increases. Negative pct = field decreases.
CONSEQUENCE_TABLES = {
    "defensive_stand": {
        "total_success": [
            {"field": "military",  "form": "deficit",  "pct": 15,  "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -10, "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -2,  "target": "mission"},
        ],
        "strong_success": [
            {"field": "military",  "form": "deficit",  "pct": 8,   "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "partial_success": [
            {"field": "military",  "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -10, "target": "mission"},
        ],
        "partial_failure": [
            {"field": "military",  "form": "current",  "pct": -15, "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 10,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -15, "target": "mission"},
        ],
        "total_failure": [
            {"field": "military",   "form": "current",  "pct": -30, "target": "mission"},
            {"field": "tension",    "form": "deficit",  "pct": 20,  "target": "mission"},
            {"field": "economy",    "form": "current",  "pct": -20, "target": "mission"},
            {"field": "population", "form": "current",  "pct": -5,  "target": "mission"},
        ],
    },
    "siege_breaking": {
        "total_success": [
            {"field": "military",  "form": "deficit",  "pct": 10,  "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -15, "target": "mission"},
            {"field": "economy",   "form": "deficit",  "pct": 10,  "target": "mission"},
        ],
        "strong_success": [
            {"field": "military",  "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -10, "target": "mission"},
            {"field": "economy",   "form": "deficit",  "pct": 5,   "target": "mission"},
        ],
        "partial_success": [
            {"field": "military",  "form": "current",  "pct": -3,  "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "economy",   "form": "deficit",  "pct": 3,   "target": "mission"},
        ],
        "partial_failure": [
            {"field": "military",  "form": "current",  "pct": -10, "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "total_failure": [
            {"field": "military",  "form": "current",  "pct": -20, "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 15,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -10, "target": "mission"},
        ],
    },
    "reconquest": {
        "total_success": [
            {"field": "tension",   "form": "current",  "pct": -10, "target": "mission"},
            {"field": "economy",   "form": "deficit",  "pct": 5,   "target": "mission"},
        ],
        "strong_success": [
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "partial_success": [
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -15, "target": "mission"},
        ],
        "partial_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "adjacent_player"},
        ],
        "total_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 10,  "target": "adjacent_player"},
            {"field": "military",  "form": "current",  "pct": -5,  "target": "adjacent_player"},
        ],
    },
    "assault": {
        "total_success": [],
        "strong_success": [],
        "partial_success": [
            {"field": "military",  "form": "current",  "pct": -30, "target": "mission"},
        ],
        "partial_failure": [
            {"field": "military",  "form": "current",  "pct": -10, "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "home"},
        ],
        "total_failure": [
            {"field": "military",  "form": "current",  "pct": -3,  "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 15,  "target": "home"},
            {"field": "military",  "form": "current",  "pct": -10, "target": "home"},
        ],
    },
    "suppression": {
        "total_success": [
            {"field": "tension",   "form": "current",  "pct": -15, "target": "mission"},
            {"field": "economy",   "form": "deficit",  "pct": 5,   "target": "mission"},
        ],
        "strong_success": [
            {"field": "tension",   "form": "current",  "pct": -8,  "target": "mission"},
        ],
        "partial_success": [],
        "partial_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "adjacent_player"},
        ],
        "total_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 10,  "target": "adjacent_player"},
        ],
    },
    "multi_front_defense": {
        "total_success": [
            {"field": "military",  "form": "deficit",  "pct": 10,  "target": "mission"},
            {"field": "tension",   "form": "current",  "pct": -10, "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "strong_success": [
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -10, "target": "mission"},
        ],
        "partial_success": [
            {"field": "military",  "form": "current",  "pct": -10, "target": "mission"},
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -15, "target": "mission"},
        ],
        "partial_failure": [
            {"field": "military",   "form": "current",  "pct": -20, "target": "mission"},
            {"field": "tension",    "form": "deficit",  "pct": 15,  "target": "mission"},
            {"field": "economy",    "form": "current",  "pct": -20, "target": "mission"},
            {"field": "population", "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "total_failure": [
            {"field": "military",   "form": "current",  "pct": -35, "target": "mission"},
            {"field": "tension",    "form": "deficit",  "pct": 25,  "target": "mission"},
            {"field": "economy",    "form": "current",  "pct": -25, "target": "mission"},
            {"field": "population", "form": "current",  "pct": -10, "target": "mission"},
        ],
    },
    "interception": {
        "total_success": [
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
        ],
        "strong_success": [
            {"field": "military",  "form": "current",  "pct": -3,  "target": "mission"},
        ],
        "partial_success": [],
        "partial_failure": [],
        "total_failure": [
            {"field": "military",  "form": "current",  "pct": -15, "target": "mission"},
        ],
    },
    "evacuation": {
        "total_success": [
            {"field": "economy",    "form": "deficit",  "pct": 5,  "target": "adjacent_player"},
            {"field": "population", "form": "deficit",  "pct": 3,  "target": "adjacent_player"},
        ],
        "strong_success": [
            {"field": "economy",    "form": "deficit",  "pct": 3,  "target": "adjacent_player"},
            {"field": "population", "form": "deficit",  "pct": 2,  "target": "adjacent_player"},
        ],
        "partial_success": [
            {"field": "economy",    "form": "deficit",  "pct": 1,  "target": "adjacent_player"},
            {"field": "population", "form": "deficit",  "pct": 1,  "target": "adjacent_player"},
        ],
        "partial_failure": [],
        "total_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 10, "target": "adjacent_player"},
        ],
    },
    "containment": {
        "total_success": [
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "adjacent_player"},
        ],
        "strong_success": [
            {"field": "tension",   "form": "current",  "pct": -3,  "target": "adjacent_player"},
        ],
        "partial_success": [
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "exposed"},
        ],
        "partial_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 10,  "target": "exposed"},
            {"field": "economy",   "form": "current",  "pct": -5,  "target": "exposed"},
        ],
        "total_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 15,  "target": "adjacent_player"},
            {"field": "economy",   "form": "current",  "pct": -10, "target": "adjacent_player"},
        ],
    },
    "counterinsurgency": {
        "total_success": [
            {"field": "tension",   "form": "current",  "pct": -20, "target": "mission"},
            {"field": "military",  "form": "deficit",  "pct": 5,   "target": "mission"},
        ],
        "strong_success": [
            {"field": "tension",   "form": "current",  "pct": -12, "target": "mission"},
            {"field": "military",  "form": "deficit",  "pct": 3,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -3,  "target": "mission"},
        ],
        "partial_success": [
            {"field": "tension",   "form": "current",  "pct": -5,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -8,  "target": "mission"},
        ],
        "partial_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 5,   "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -12, "target": "mission"},
        ],
        "total_failure": [
            {"field": "tension",   "form": "deficit",  "pct": 15,  "target": "mission"},
            {"field": "economy",   "form": "current",  "pct": -15, "target": "mission"},
            {"field": "military",  "form": "current",  "pct": -5,  "target": "mission"},
        ],
    },
}
# Special outcomes that trigger region transfer (conquest resolution)
REGION_TRANSFER_OUTCOMES = {
    "reconquest": {"total_success", "strong_success", "partial_success"},
    "assault": {"total_success", "strong_success"},
    "suppression": {"total_success", "strong_success"},
}
COMMANDER_DEATH_EVENT_ID = "evt_commander_killed_in_action"

# ── Stage 7: Map Generation ──────────────────────────────────────────────────
ENABLE_STAGE7_MAP_GEN = True   # ON: Checkpoint I passed; see docs/architecture.md

CANVAS_SIZES = {"small": (8000, 8000), "medium": (16000, 16000), "large": (24000, 24000)}
STRUCTURE_COUNT_RANGES = {"small": (2, 4), "medium": (3, 6), "large": (4, 8)}
LAYOUT_JITTER_PERCENT = 0.03

REINFORCEMENT_CAPTURE_RADIUS = 300.0
REINFORCEMENT_CAPTURE_DURATION_SEC = 10.0
REINFORCEMENT_STRUCTURE_HP = 3000
BASE_PRODUCTION_TIME_SEC = 30.0
POWER_NORMALIZATION = 100.0           # tune from Stage 6 baseline unit power
UNIT_POWER_RATINGS = {
    "Raider":      50,
    "Interceptor": 60,
    "Vanguard":    100,
    "Warden":      80,
    "Bombard":     150,
    "Bastion":     200,
}

COMPOSITION_SKEW_THRESHOLD = 0.70
COMPOSITION_SHIFT_MAGNITUDE = 0.15

OWNERSHIP_MILITARY_COEFF = 0.15
OWNERSHIP_TENSION_COEFF  = 0.15

FAIRNESS_MAX_RETRIES = 5

# Per-node-type gradient intensity and radius
GRADIENT_CHOKEPOINT_INTENSITY      = 0.85
GRADIENT_CHOKEPOINT_RADIUS         = 600.0
GRADIENT_STAGING_INTENSITY         = 0.60
GRADIENT_STAGING_RADIUS            = 800.0
GRADIENT_VANTAGE_INTENSITY         = 0.90
GRADIENT_VANTAGE_RADIUS            = 700.0
GRADIENT_HAZARD_INTENSITY          = 0.75
GRADIENT_HAZARD_RADIUS             = 500.0
# flank_route: mild obstacle + mild cover (hazardous but traversable)
GRADIENT_FLANK_OBSTACLE_INTENSITY  = 0.35
GRADIENT_FLANK_OBSTACLE_RADIUS     = 450.0
GRADIENT_FLANK_COVER_INTENSITY     = 0.40
GRADIENT_FLANK_COVER_RADIUS        = 450.0
# A3 Option B (2026-05-20): cover at defensible positions + approach corridors,
# per docs/bible_history/bible_2_00_world.md:188 ("cover density gradients are placed in defensible
# positions and approach corridors"). Calibration anchors:
#   staging cover  = (800, 0.60)  — broad safe area, player rear
#   flank cover    = (450, 0.40)  — mild concealment along flank
# Chokepoint cover sits between: tighter than staging, denser than flank, since
# it's prepared defensive ground. Objective cover is the smallest blob (single
# focal point with prepared positions). Hazard cover mirrors flank intensity
# (rebels hide "behind cover" within sensor interference zones per bible_missions
# counterinsurgency line, but the hazard itself is not the cover — cover is mild).
GRADIENT_CHOKEPOINT_COVER_INTENSITY = 0.55
GRADIENT_CHOKEPOINT_COVER_RADIUS    = 550.0
GRADIENT_OBJECTIVE_COVER_INTENSITY  = 0.50
GRADIENT_OBJECTIVE_COVER_RADIUS     = 400.0
GRADIENT_HAZARD_COVER_INTENSITY     = 0.35
GRADIENT_HAZARD_COVER_RADIUS        = 400.0

# Layer accessibility masks
LAYER_COUNT        = 5
LAYER_MASK_RADIUS  = 600.0   # blocking influence radius per restricting zone
LAYER_MASK_INTENSITY = 1.0   # always blocks — no partial coverage

# Simulation flavoring — region state → gradient intensity deltas
# Each coefficient is the maximum signed contribution from that field at extremes.
# stability (0-1):    instability = 1 - stability
# capacity  (0-1):    used directly
# economy, tension, military, population (0-100): normalised to 0-1 internally
FLAVOR_STABILITY_SI_COEFF     = 0.15   # instability → +sensor_interference
FLAVOR_STABILITY_COV_COEFF    = 0.10   # instability → +cover_density
FLAVOR_CAPACITY_OBS_COEFF     = 0.12   # high capacity → -obstacle_density
FLAVOR_ECONOMY_OBS_COEFF      = 0.10   # high economy → -obstacle_density
FLAVOR_TENSION_COV_COEFF      = 0.12   # high tension → +cover_density
FLAVOR_MILITARY_OBS_COEFF     = 0.10   # high military → +obstacle_density
FLAVOR_POPULATION_SCALE_COEFF = 0.08   # population above/below midpoint → scales all density
FLAVOR_MAX_DELTA              = 0.20   # per-property absolute delta cap

# ── Stage 8: Socket server / WebSocket bridge ─────────────────────────────────
SOCKET_HOST                = "127.0.0.1"
SOCKET_PORT                = 8765
TICK_HZ                    = 20
SNAPSHOT_INTERVAL_SEC      = 5.0
RECONNECT_GRACE_SEC        = 30.0
INTERPOLATION_BUFFER_TICKS = 3

# Dead-reckoning suppression (snapshot_serializer.py DeadReckoningTracker)
DR_RESYNC_THRESHOLD        = 1.0   # world units of position prediction error before forcing resync
DR_VEL_CHANGE_THRESHOLD    = 20.0  # wu/s of velocity magnitude change before forcing resync
# DR_RESYNC_THRESHOLD tightened from 3.0 to 1.0 in Stage 8.5 H.5 to shrink
# per-tick backward snap magnitudes (client DR over-prediction was producing
# p95 270 wu backward corrections with the old 3.0 threshold).
# See logs/perf_report.md and docs/legacy/stage_specs/stage_8_5_spec.md H.5.

# Camera / input (consumed by Godot client via snapshot metadata)
CAMERA_ANGLE_DEGREES       = 60.0
CAMERA_ZOOM_MIN            = 0.5
CAMERA_ZOOM_MAX            = 2.0
CAMERA_PAN_SPEED_WU_PER_SEC = 1500.0

# Control groups
CONTROL_GROUP_COUNT        = 10   # keys 1..0 (0 = group 10)

# Persistence
SAVE_ROOT                  = "user://saves"   # Godot path; Python maps to OS path

# Command ingest
DEBUG_COMMAND_LOG          = False  # log dropped packets; noisy in tests, useful for debugging

# Kill switches — both OFF until their checkpoint passes
ENABLE_STAGE8_SOCKET       = False
ENABLE_STAGE8_PERSISTENCE  = False

# ── Stage 10: Pipe transport ──────────────────────────────────────────────────
CRASH_LOG_PATH   = "logs/crash_report.txt"
STDERR_LOG_PATH  = "logs/sim_stderr.log"
IS_RELEASE_BUILD = False

# ── World view / Stage 11 ─────────────────────────────────────────────────
WORLD_VIEW_ENABLED = True
CHRONICLE_SCROLL_ENABLED = True
KEYFRAME_STREAM_ENABLED = True

# ── Stage 11g: World view inspection (kill-switch flags, default OFF) ─────
# Each flag, when False, must leave behavior bit-identical to pre-stage-11g.
# See docs/legacy/stage_specs/stage_11g_world_view_inspection_spec.md
ENABLE_FACTION_PALETTE     = True   # deterministic faction hue + vivacity scaling
ENABLE_INSPECTION_PANELS   = True   # region/faction info panels on click
ENABLE_INSPECTION_PAUSE    = True   # panels pause world view animation
ENABLE_CHRONICLE_MENTIONS  = True   # clickable region/faction names in chronicle
ENABLE_OWNERSHIP_HISTORY   = False  # per-faction count history + per-region prior owners

# Chronicle scroll
SCROLL_PER_WORD_CADENCE_SEC = 0.08
SCROLL_PER_WORD_FADE_DURATION_SEC = 0.20
SCROLL_ENTRY_MIN_DISPLAY_DURATION_SEC = 3.0
SCROLL_PANEL_SLIDE_IN_DURATION_SEC = 0.40
SCROLL_PANEL_SLIDE_OUT_DURATION_SEC = 0.40
SCROLL_PANEL_WIDTH_FRACTION = 0.38

# World view visuals
WORLD_VIEW_TERRITORY_BUBBLE_OPACITY = 0.25
WORLD_VIEW_TERRITORY_BUBBLE_RADIUS_SCALE = 1.6
WORLD_VIEW_CONTOUR_THRESHOLD = 0.08
WORLD_VIEW_CONTOUR_BRIGHTNESS = 1.4
WORLD_VIEW_CONTOUR_LINE_THICKNESS_PX = 1.5
WORLD_VIEW_FLASH_DURATION_SEC = 0.35
WORLD_VIEW_FLASH_INTENSITY = 0.7
WORLD_VIEW_TERRITORY_TRANSITION_DURATION_SEC = 1.0

# Camera choreography
CAMERA_PULL_BACK_DURATION_SEC = 2.5
CAMERA_WORLD_VIEW_FADE_IN_DURATION_SEC = 1.0
CAMERA_AMBIENT_ORBIT_SPEED_NARRATION = 0.03
CAMERA_AMBIENT_ORBIT_SPEED_SETTLED = 0.01
CAMERA_PUSH_IN_DURATION_SEC = 3.0
TACTICAL_SCENE_FREE_DELAY_MS = 500

# Ambient liveliness during post-narration hold
AMBIENT_LIVELINESS_FLICKER_MIN_INTERVAL_SEC = 3.0
AMBIENT_LIVELINESS_FLICKER_MAX_INTERVAL_SEC = 5.0
AMBIENT_LIVELINESS_FLICKER_INTENSITY_FRACTION = 0.15
AMBIENT_LIVELINESS_HIGHLIGHT_PULSE_PERIOD_SEC = 1.5

# Exit
EXIT_FADE_TO_BLACK_DURATION_SEC = 0.6

# ── Wave 2.5R: Asteroid cover (per-asteroid LOS model) ───────────────────────
ASTEROID_SPATIAL_HASH_CELL   = 100.0
LAYER_Z_FLOORS               = [0.0, 30.0, 100.0]
LAYER_Z_CEILINGS             = [30.0, 100.0, 300.0]
ASTEROID_BASE_DENSITY        = 0.00090
ASTEROID_SCALE_DISTRIBUTION  = {"tiny": 0.60, "small": 0.25, "medium": 0.10, "huge": 0.05}
ASTEROID_SCALE_RANGES        = {"tiny": (1.0, 3.0), "small": (3.0, 8.0), "medium": (8.0, 20.0), "huge": (20.0, 80.0)}
ASTEROID_HEIGHT_RATIO_RANGE  = (0.5, 2.0)
ASTEROID_MOVEMENT_BLOCK_RADIUS = 8.0
