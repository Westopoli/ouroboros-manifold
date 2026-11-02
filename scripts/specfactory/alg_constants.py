#!/usr/bin/env python3
"""Two mechanical jobs for the C rewrite's constants (F3, two-day push):

`--emit PATH`: parses every numeric constant out of docs/bible/algorithms.md's
ALG-NN paragraphs (scalars `IDENT = 8.0`, ranges `IDENT = (55, 75)`, keyed
tables `IDENT[key]: key1 v1, key2 v2`, and the doc's "formula, then trailing
labelled values" convention, e.g. "..., rate `0.5`") and writes them as
`#define OM_<IDENT> <value>` to PATH, grouped by ALG id. Never edits
algorithms.md; only reads it.

`--lint DIR`: fails on any bare numeric literal in DIR/*.c other than 0, 1,
-1, 2, 0.5, an array size in a declaration, a #define line, a sizeof(...)
argument, or a literal inside a `/* constants-table: <bible citation> */`
... `/* end constants-table */` fence (a cited data table, e.g. E-04's
static event-template library, not a tuning constant) -- so a tuned
constant lands in algorithms.md and this header, not scattered through the
C. csrc/{sim,region,faction,agent,resolve}.c predate this lint; their
current literals are grandfathered in
docs/northstar/spec_factory/constants_allowlist.txt, keyed by
file:token:occurrence (the n-th time that exact token text appears among a
file's violations, top to bottom) so editing unrelated lines never shifts
an entry out from under itself (regenerate with --gen-allowlist after a
deliberate change to one of them). The allowlist also accepts the
deprecated file:line:col:token format on read, with a WARN, so a
not-yet-regenerated file does not crash the lint.

Both commands are deterministic and idempotent: same input, same output,
every time.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALGORITHMS_MD = REPO / "docs" / "bible" / "algorithms.md"
ALLOWLIST_PATH = REPO / "docs" / "northstar" / "spec_factory" / "constants_allowlist.txt"
GRANDFATHERED_FILES = {"sim.c", "region.c", "faction.c", "agent.c", "resolve.c"}
ALWAYS_EXEMPT_VALUES = {0.0, 1.0, -1.0, 2.0, 0.5}

# --------------------------------------------------------------------- ALG parsing

# ALG-56's base-minutes table parses as TACTICAL_TICK_RATE_<ARCHETYPE>; those are
# minutes, not tick rates, and mission.c keeps them local, so they are not emitted.
EXCLUDED_NAMES = {
    f"OM_TACTICAL_TICK_RATE_{a}" for a in (
        "ASSAULT", "CONTAINMENT", "COUNTERINSURGENCY", "DEFENSIVE", "EVACUATION",
        "FRONT", "INTERCEPTION", "RECONQUEST", "SIEGE", "SUPPRESSION")
} | {"OM_WAYPOINT_ARRIVE_MULT"}  # ALG-68 states it; tactical_move.c keeps it a local #define

# Hand-maintained header lines that algorithms.md does not state as `IDENT = value`,
# each inserted right after the generated line it follows. Promote a value into
# algorithms.md and delete its entry here; --emit must keep reproducing csrc/om_constants.h.
MANUAL_INSERTS: list[tuple[str, tuple[str, ...]]] = [
    ('/* ALG-21 Damage split */', (
        '#define OM_ALG21_BREAKTHROUGH_ECO 0.3',
        '#define OM_ALG21_BREAKTHROUGH_MIL 0.8',
        '#define OM_ALG21_BREAKTHROUGH_TENSION 0.5',
        '#define OM_ALG21_BREAKTHROUGH_TENSION_CAP 30.0',
        '#define OM_ALG21_CONTESTED_ECO 0.2',
        '#define OM_ALG21_CONTESTED_MIL 0.5',
        '#define OM_ALG21_CONTESTED_TENSION 0.4',
        '#define OM_ALG21_REPELLED_MIL 0.10',
    )),
    ('#define OM_FIELD_MAX 100', (
        '#define OM_PCT_SCALE 100.0                          /* ALG-26/27/28/39 field value to fraction */',
    )),
    ('#define OM_KNOWLEDGE_LOST_POP_DROP 10.0', (
        '#define OM_KNOWLEDGE_LOST_POP_WINDOW 50 /* ALG-27b: population-history window, ticks */',
    )),
    ('#define OM_TECH_CONVERGENCE_RATE 0.1', (
        '/* E-06 Tech tiers (R-048-01) */',
        '#define OM_TECH_TIER_1_MAX 34.0',
        '#define OM_TECH_TIER_2_MAX 67.0',
    )),
    ('#define OM_BASE_BETRAYAL_RATE 0.005', (
        '#define OM_BETRAYAL_OPPORTUNITY_CAP 3.0',
        '#define OM_BETRAYAL_TENSION_SCALE 50.0',
    )),
    ('#define OM_EVENT_TIER_EVT_WAR_WEARINESS 3', (
        '#define OM_SIGNIFICANCE_CHARACTER_BONUS 0.3',
        '#define OM_SIGNIFICANCE_CHAIN_LENGTH_BONUS 0.1',
    )),
    ('#define OM_SIGNIFICANCE_DELTA_SCALE 50.0', (
        '#define OM_SIGNIFICANCE_LINEAGE_REGION_BONUS 0.8',
        '#define OM_SIGNIFICANCE_MISSION_REGION_BONUS 0.5',
        '/* E-09 Chronicle thresholds (R-067-02..R-067-05) */',
        '#define OM_CHRON_CASCADE_MIN_EVENTS 4',
        '#define OM_CHRON_DEFEAT_MIL_MAX -2.0',
        '#define OM_CHRON_DEFEAT_TEN_MIN 3.0',
        '#define OM_CHRON_REGIONAL_DECLINE_MAX -3.0',
        '#define OM_CHRON_REGIONAL_GROWTH_MIN 3.0',
        '#define OM_CHRON_STALEMATE_MIL_ABS_MAX 2.0',
        '#define OM_CHRON_STALEMATE_TEN_MIN 2.0',
        '#define OM_CHRON_SUFFERED_ECO_MAX -3.0',
        '#define OM_CHRON_SUFFERED_TEN_MIN 5.0',
        '#define OM_CHRON_THRIVED_ECO_MIN 2.0',
        '#define OM_CHRON_THRIVED_MIL_MIN 2.0',
        '#define OM_CHRON_VICTORY_MIL_MIN 2.0',
        '#define OM_CHRON_VICTORY_TEN_MAX 3.0',
        '/* E-09 Chronicle prose bands (R-068-03) */',
        '#define OM_CHRON_CAPACITY_HIGH 70.0',
        '#define OM_CHRON_CAPACITY_LOW 30.0',
        '#define OM_CHRON_CAPACITY_MID 50.0',
        '#define OM_CHRON_STABILITY_HIGH 70.0',
        '#define OM_CHRON_STABILITY_LOW 30.0',
        '#define OM_CHRON_STABILITY_MID 50.0',
        '#define OM_CHRON_TENSION_HIGH 60.0',
        '#define OM_CHRON_TENSION_LOW 20.0',
        '#define OM_CHRON_TENSION_MID 40.0',
    )),
    ('#define OM_PARITY_FLOOR 0.75', (
        '#define OM_MISSION_FILL_OVERSHOOT_MULT 1.15',
        '#define OM_MISSION_INSURGENT_POP_HIGH_THRESHOLD 70.0',
        '#define OM_MISSION_INSURGENT_POP_LOW_THRESHOLD 25.0    /* Q-057-02 */',
        '#define OM_MISSION_PARITY_EASY_FLOOR 0.95',
        '#define OM_MISSION_PARITY_HARD_CEILING 0.85',
    )),
    ('/* ALG-58 Outcome */', (
        '#define OM_MISSION_BAND_THRESHOLDS_EVACUATION_T1 0.30',
        '#define OM_MISSION_BAND_THRESHOLDS_EVACUATION_T2 0.50',
        '#define OM_MISSION_BAND_THRESHOLDS_EVACUATION_T3 0.65',
        '#define OM_MISSION_BAND_THRESHOLDS_EVACUATION_T4 0.80',
        '#define OM_MISSION_BAND_THRESHOLDS_MULTI_FRONT_T1 0.15',
        '#define OM_MISSION_BAND_THRESHOLDS_MULTI_FRONT_T2 0.35',
        '#define OM_MISSION_BAND_THRESHOLDS_MULTI_FRONT_T3 0.55',
        '#define OM_MISSION_BAND_THRESHOLDS_MULTI_FRONT_T4 0.75',
        '#define OM_MISSION_BAND_THRESHOLDS_RECONQUEST_ASSAULT_T1 0.25',
        '#define OM_MISSION_BAND_THRESHOLDS_RECONQUEST_ASSAULT_T2 0.45',
        '#define OM_MISSION_BAND_THRESHOLDS_RECONQUEST_ASSAULT_T3 0.65',
        '#define OM_MISSION_BAND_THRESHOLDS_RECONQUEST_ASSAULT_T4 0.82',
        '#define OM_MISSION_BAND_THRESHOLDS_STANDARD_T1 0.20',
        '#define OM_MISSION_BAND_THRESHOLDS_STANDARD_T2 0.40',
        '#define OM_MISSION_BAND_THRESHOLDS_STANDARD_T3 0.60',
        '#define OM_MISSION_BAND_THRESHOLDS_STANDARD_T4 0.80',
        '#define OM_MISSION_COMMANDER_WOUNDED_HP_FRACTION 0.30',
        '#define OM_MISSION_DEBRIEF_RETENTION_MOST_CUTOFF 0.75',
        '#define OM_MISSION_DEBRIEF_RETENTION_SOME_CUTOFF 0.4',
    )),
    ('/* ALG-59 Consequences */', (
        '#define OM_MISSION_REFUSAL_TENSION_DEFICIT_PCT 8.0',
    )),
    ('#define OM_TACTICAL_TICK_RATE 20', (
        '/* ALG-60 Damage — unit roster (ALG-60/61, simulation/config.py unit_stats) */',
        '#define OM_ROSTER_BASTION_DAMAGE 7.0',
        '#define OM_ROSTER_BASTION_HP 1050.0',
        '#define OM_ROSTER_BASTION_INTERVAL 1.8',
        '#define OM_ROSTER_BASTION_RANGE 800.0',
        '#define OM_ROSTER_BASTION_SENSOR 300.0',
        '#define OM_ROSTER_BASTION_SPEED 40.0',
        '#define OM_ROSTER_BOMBARD_AOE 150.0',
        '#define OM_ROSTER_BOMBARD_DAMAGE 17.5',
        '#define OM_ROSTER_BOMBARD_HP 400.0',
        '#define OM_ROSTER_BOMBARD_INTERVAL 3.0',
        '#define OM_ROSTER_BOMBARD_RANGE 1200.0',
        '#define OM_ROSTER_BOMBARD_SENSOR 300.0',
        '#define OM_ROSTER_BOMBARD_SPEED 50.0',
        '#define OM_ROSTER_INTERCEPTOR_DAMAGE 6.0',
        '#define OM_ROSTER_INTERCEPTOR_HP 325.0',
        '#define OM_ROSTER_INTERCEPTOR_INTERVAL 1.0',
        '#define OM_ROSTER_INTERCEPTOR_RANGE 250.0',
        '#define OM_ROSTER_INTERCEPTOR_SENSOR 1000.0',
        '#define OM_ROSTER_INTERCEPTOR_SPEED 130.0',
        '#define OM_ROSTER_RAIDER_DAMAGE 9.0',
        '#define OM_ROSTER_RAIDER_HP 250.0',
        '#define OM_ROSTER_RAIDER_INTERVAL 0.8',
        '#define OM_ROSTER_RAIDER_RANGE 200.0',
        '#define OM_ROSTER_RAIDER_SENSOR 800.0',
        '#define OM_ROSTER_RAIDER_SPEED 150.0',
        '#define OM_ROSTER_VANGUARD_DAMAGE 7.5',
        '#define OM_ROSTER_VANGUARD_HP 500.0',
        '#define OM_ROSTER_VANGUARD_INTERVAL 1.2',
        '#define OM_ROSTER_VANGUARD_RANGE 300.0',
        '#define OM_ROSTER_VANGUARD_SENSOR 700.0',
        '#define OM_ROSTER_VANGUARD_SPEED 80.0',
        '#define OM_ROSTER_WARDEN_DAMAGE 4.0',
        '#define OM_ROSTER_WARDEN_HP 375.0',
        '#define OM_ROSTER_WARDEN_INTERVAL 1.5',
        '#define OM_ROSTER_WARDEN_RANGE 350.0',
        '#define OM_ROSTER_WARDEN_SENSOR 800.0',
        '#define OM_ROSTER_WARDEN_SPEED 70.0',
    )),
    ('/* ALG-63 Abilities */', (
        '#define OM_ABILITY_BARRAGE_COOLDOWN_TICKS 1800.0',
        '#define OM_ABILITY_BARRAGE_DAMAGE_MULT 3.0',
        '#define OM_ABILITY_BARRAGE_RADIUS 100.0',
        '#define OM_ABILITY_BARRAGE_TELEGRAPH_TICKS 30',
        '#define OM_ABILITY_BRACE_COOLDOWN_TICKS 700.0',
        '#define OM_ABILITY_BRACE_DAMAGE_REDUCTION 0.50',
        '#define OM_ABILITY_BRACE_OUTPUT_MULT 1.3',
        '#define OM_ABILITY_BRACE_WINDUP_TICKS 40',
        '#define OM_ABILITY_FORTIFY_COOLDOWN_TICKS 1400.0',
        '#define OM_ABILITY_FORTIFY_DAMAGE_REDUCTION 0.20',
        '#define OM_ABILITY_FORTIFY_DURATION_TICKS 400',
        '#define OM_ABILITY_FORTIFY_SPEED_MULT 0.4',
        '#define OM_ABILITY_INTERCEPT_COOLDOWN_TICKS 600.0',
        '#define OM_ABILITY_INTERCEPT_OUTPUT_MULT 1.5',
        '#define OM_ABILITY_INTERCEPT_SPEED_MULT 1.8',
        '#define OM_ABILITY_RALLY_COOLDOWN_TICKS 1500.0',
        '#define OM_ABILITY_RALLY_HEAL_AMOUNT 112.0',
        '#define OM_ABILITY_RALLY_RADIUS 400.0',
        '#define OM_ABILITY_SURGE_COOLDOWN_TICKS 1500.0',
        '#define OM_ABILITY_SURGE_DURATION_TICKS 60',
        '#define OM_ABILITY_SURGE_OUTPUT_MULT 2.0',
        '#define OM_ABILITY_SURGE_SPEED_MULT 2.5',
    )),
    ('#define OM_ARRIVAL_TOLERANCE_MULT 1.5', (
        '#define OM_ATTACK_MOVE_LEASH_BASELINE 200.0',
        '#define OM_ATTACK_MOVE_LEASH_DIST 0.0',
        '#define OM_COMPOSITION_BASE 50',
        '#define OM_COMPOSITION_BASTION 2',
        '#define OM_COMPOSITION_BOMBARD 3',
        '#define OM_COMPOSITION_INTERCEPTOR 10',
        '#define OM_COMPOSITION_RAIDER 15',
        '#define OM_COMPOSITION_VANGUARD 15',
        '#define OM_COMPOSITION_WARDEN 5',
        '#define OM_GRID_CELL_SIZE 400.0',
    )),
    ('#define OM_MAGIC_BOX_SPREAD_RADIUS 450', (
        '#define OM_RETURN_FIRE_FLEE_DIST 200.0',
    )),
    ('#define OM_NAVMESH_OBSTACLE_THRESHOLD 0.7', (
        '#define OM_OBSTACLE_DENSITY_LOW_THRESHOLD 0.3',
        '#define OM_TERRAIN_SPEED_PENALTY_COEF 0.5',
    )),
    ('/* ALG-68 Steering and collision */', (
        '#define OM_LOS_SAMPLE_STEP 1.0',
    )),
    ('#define OM_STEERING_PROBE_DIST 40', (
        '#define OM_STEERING_SWEEP_COUNT 13',
        '#define OM_STEERING_SWEEP_DELTA_RAD 0.2617993878',
    )),
    ('#define OM_LINE 4.0', (
        '#define OM_MOVE_CAT_LINE_SPEED_MIN 60.0',
        '#define OM_MOVE_CAT_STRIKE_SPEED_MIN 100.0',
    )),
    ('#define OM_LAYER_MASK_RADIUS 600', (
        '#define OM_MISSION_OBJECTIVE_COVER_HEIGHT 5.0',
        '#define OM_MISSION_OBJECTIVE_COVER_RADIUS 400.0',
        '#define OM_SUP_HAZARD_INTERFERENCE_RADIUS 500.0',
    )),
    ('#define OM_SELECTOR_DECAY_BASE 0.75', (
        '/* Math constants */',
        '#define OM_TWO_PI 6.28318530717958647692528676655900577',
    )),
]

# See also: MANUAL_INSERTS. A heading's parenthetical question ids are not in the md title.
TITLE_SUFFIXES = {
    "ALG-76": " (Q-120-03, Q-124-03)",
    "ALG-77": " (Q-060-02)",
}

ALG_HEADER_RE = re.compile(r"\*\*(ALG-\d+[a-z]?)\s+([^*.]+)\.?\*\*")
NUM = r"-?\d+(?:\.\d+)?"


def alg_sort_key(alg_id: str) -> tuple[int, str]:
    m = re.match(r"ALG-(\d+)([a-z]?)", alg_id)
    return (int(m.group(1)), m.group(2))


class Const:
    __slots__ = ("name", "value", "alg_id", "alg_title")

    def __init__(self, name: str, value: str, alg_id: str, alg_title: str):
        self.name = name
        self.value = value
        self.alg_id = alg_id
        self.alg_title = alg_title


def split_alg_blocks(text: str) -> list[tuple[str, str, str]]:
    """[(alg_id, alg_title, block_text)] -- block_text runs from one
    `**ALG-NN ...**` marker to the next (or EOF), so untitled paragraphs
    that follow an ALG marker (e.g. "**Apply.**" after ALG-08) are treated
    as part of that ALG's block. Text before the first marker (the tick
    sequence, the preamble) is out of scope -- the task is ALG paragraphs
    only, and every constant used in the preamble is restated inside its
    owning ALG paragraph."""
    matches = list(ALG_HEADER_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(1), m.group(2).strip(), text[start:end]))
    return blocks


def is_number_str(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def fmt_value(raw: str) -> str:
    """Doubles keep a decimal point at full precision; integers stay integers."""
    raw = raw.strip()
    if "." in raw:
        return raw if raw not in ("-0.0",) else "0.0"
    return raw


def strip_backticks(s: str) -> str:
    return s.replace("`", "")


def snake_upper(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s.strip()).strip("_").upper()


def looks_ambiguous_after(text: str, end: int) -> bool:
    """True if the number just matched (ending at `end`) is immediately
    followed by an arithmetic operator and then another bare number, e.g.
    "= 8.0 + 3.0" -- a compound expression, not one constant's value.
    Handled separately by the compound-assignment pattern; never guessed
    here."""
    rest = text[end:end + 12]
    return bool(re.match(r"\s*[+\-*/·×]\s*-?\d", rest))


# --- Pattern 0: compound "IDENT_A + IDENT_B = v1 + v2" (positional, same operator) ---
COMPOUND_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]*)\s*\+\s*([A-Z][A-Z0-9_]*)\s*=\s*(" + NUM + r")\s*\+\s*(" + NUM + r")\b"
)

# --- Pattern A: scalar "IDENT = NUMBER" ---
SCALAR_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*(" + NUM + r")(?!\s*[.,]?\d)")

# --- Pattern B: range "IDENT = (NUM, NUM)" ---
RANGE_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)"
)

# --- Pattern C: keyed paren-list without a colon: IDENT (k1 (a,b), k2 (c,d), ...) ---
KEYED_PAREN_LIST_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*\(\s*((?:[a-z][a-z_]*\s*\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)\s*,?\s*){2,})\)"
)
KEYED_PAREN_ITEM_RE = re.compile(r"([a-z][a-z_]*)\s*\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)")

# --- Pattern D: keyed colon-list: IDENT[key] or IDENT (labels): key1 v1, key2 v2, ... ---
KEYED_COLON_HEAD_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})(?:\[[a-z_]+\](?:\[[a-z_]+\])?)?"
    r"(?:\s*\(([a-z][a-z, ]*[a-z])\))?\s*:\s*"
)
KEYED_ITEM_RE = re.compile(
    r"([a-z][a-z_]*)\s+(\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)|" + NUM + r"(?:\s*/\s*" + NUM + r"){0,3})"
)
SENTENCE_END_RE = re.compile(r"[.;](?!\d)")

# --- Pattern E: bracketed list of pairs: IDENT = [(a, b), (c, d), ...] ---
BRACKET_PAIRS_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*\[\s*((?:\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)\s*,?\s*)+)\]"
)
PAIR_ITEM_RE = re.compile(r"\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)")

# --- Pattern F: formula backtick-span, then trailing labelled value(s) ---
# F1: one or more ", label `v`" clauses, matched to identifiers by substring.
# F2: a single ", label `v1 / v2 / ... / vN`" clause, matched positionally.
# A label's value may also be a range `(a, b)` (e.g. "range `(0.7, 1.3)`").
LABEL_VALUE = r"(?:\(\s*" + NUM + r"\s*,\s*" + NUM + r"\s*\)|" + NUM + r"(?:\s*/\s*" + NUM + r")*)"
FORMULA_THEN_LABELS_RE = re.compile(
    r"`([^`]+)`((?:\s*,\s*[a-zA-Z][a-zA-Z \-]*`" + LABEL_VALUE + r"`)+)"
)
LABEL_ITEM_RE = re.compile(r",\s*([a-zA-Z][a-zA-Z \-]*?)\s*`(" + LABEL_VALUE + r")`")

# --- Pattern G: formula backtick-span, then a bare `= NUMBER` backtick span
# naming the value of the formula's one still-unresolved identifier, e.g.
# "`capacity = p' . ECO_POP_RATIO`, `= 0.85`." ---
FORMULA_THEN_BARE_EQ_RE = re.compile(r"`([^`]+)`\s*,\s*`=\s*(" + NUM + r")`")


def parse_scalars_and_compounds(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in COMPOUND_RE.finditer(block):
        out.append((m.group(1), fmt_value(m.group(3))))
        out.append((m.group(2), fmt_value(m.group(4))))
        used_spans.append(m.span())
    for m in SCALAR_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        if looks_ambiguous_after(block, m.end()):
            continue
        out.append((m.group(1), fmt_value(m.group(2))))
        used_spans.append(m.span())
    return out


def parse_ranges(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in RANGE_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        out.append((f"{name}_LO", fmt_value(m.group(2))))
        out.append((f"{name}_HI", fmt_value(m.group(3))))
        used_spans.append(m.span())
    return out


def parse_keyed_paren_lists(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in KEYED_PAREN_LIST_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        for item in KEYED_PAREN_ITEM_RE.finditer(m.group(2)):
            key = snake_upper(item.group(1))
            out.append((f"{name}_{key}_LO", fmt_value(item.group(2))))
            out.append((f"{name}_{key}_HI", fmt_value(item.group(3))))
        used_spans.append(m.span())
    return out


TABLE_HEAD_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})(?:\[[a-z_]+\](?:\[[a-z_]+\])?)?[^:\n|]{0,60}:\s*")


def parse_markdown_tables(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """IDENT[key], or IDENT with a short run-up of prose (labels or a
    "for x, y, z" lead-in), then a colon and a markdown pipe table -- row
    key is the table's first column, e.g.
    OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_ATTACK. A column is emitted
    only if every data row's cell in it is a bare number (ALG-11's
    tension-primary/can-colonize/recent-damage-boost columns are not, and
    are silently left out -- reported unparsed instead of guessed)."""
    out = []
    for head in TABLE_HEAD_RE.finditer(block):
        name = head.group(1)
        rest = block[head.end():]
        if not rest.lstrip().startswith("|"):
            continue
        table_start = head.end() + (len(rest) - len(rest.lstrip()))
        blank_idx = block.find("\n\n", table_start)
        table_end = blank_idx if blank_idx != -1 else len(block)
        rows = [ln for ln in block[table_start:table_end].splitlines() if ln.strip().startswith("|")]
        if len(rows) < 3:
            continue
        header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        data_rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows[2:]]
        col_numeric = [
            all(is_number_str(row[ci]) for row in data_rows if ci < len(row))
            for ci in range(len(header))
        ]
        found = False
        for row in data_rows:
            row_key = snake_upper(row[0])
            for ci in range(1, len(header)):
                if ci < len(row) and col_numeric[ci]:
                    out.append((f"{name}_{row_key}_{snake_upper(header[ci])}", fmt_value(row[ci])))
                    found = True
        if found:
            used_spans.append((table_start, table_end))
    return out


def parse_keyed_colon_lists(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for head in KEYED_COLON_HEAD_RE.finditer(block):
        name = head.group(1)
        if block[head.end():].lstrip().startswith("|"):
            continue  # a markdown table -- parse_markdown_tables' job
        labels = [w.strip() for w in head.group(2).split(",")] if head.group(2) else None
        end_m = SENTENCE_END_RE.search(block, head.end())
        region_end = end_m.start() if end_m else len(block)
        region = block[head.end():region_end]
        items = list(KEYED_ITEM_RE.finditer(region))
        if not items:
            continue
        for item in items:
            used_spans.append((head.end() + item.start(), head.end() + item.end()))
            key = snake_upper(item.group(1))
            val = item.group(2)
            if val.startswith("("):
                lo, hi = [v.strip() for v in val.strip("()").split(",")]
                out.append((f"{name}_{key}_LO", fmt_value(lo)))
                out.append((f"{name}_{key}_HI", fmt_value(hi)))
            elif "/" in val:
                parts = [v.strip() for v in val.split("/")]
                if labels and len(labels) == len(parts):
                    for label, v in zip(labels, parts):
                        out.append((f"{name}_{key}_{snake_upper(label)}", fmt_value(v)))
                else:
                    for i, v in enumerate(parts):
                        out.append((f"{name}_{key}_{i}", fmt_value(v)))
            else:
                out.append((f"{name}_{key}", fmt_value(val)))
    return out


BRACE_ROW_IDENT_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\[[a-z_]+\]\[[a-z_]+\]")
BRACE_ROW_RE = re.compile(r"([A-Za-z][A-Za-z]*)\s*\{([^{}]+)\}")
BRACE_ITEM_RE = re.compile(r"([A-Za-z][A-Za-z]*)\s+(" + NUM + r")")


def parse_brace_matrix(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """`IDENT[a][b]` ... "Matrix: Row1 {Col1 v, Col2 v}; Row2 {Col1 v, ...}"
    (ALG-60's damage category matrix) -- one row/col-keyed constant per
    cell."""
    out = []
    for head in BRACE_ROW_IDENT_RE.finditer(block):
        name = head.group(1)
        matrix_idx = block.find("Matrix:", head.end())
        if matrix_idx == -1 or matrix_idx - head.end() > 200:
            continue
        # Rows are chained directly (`Row1 {...}; Row2 {...}; Row3 {...}`),
        # so consume consecutive "; Row {...}" groups rather than bounding
        # by a sentence end -- the rows themselves are ';'-separated.
        pos = matrix_idx + len("Matrix:")
        found = False
        while True:
            gap = re.match(r"\s*;?\s*", block[pos:])
            row_m = BRACE_ROW_RE.match(block, pos + gap.end())
            if not row_m:
                break
            row_key = snake_upper(row_m.group(1))
            for item_m in BRACE_ITEM_RE.finditer(row_m.group(2)):
                col_key = snake_upper(item_m.group(1))
                out.append((f"{name}_{row_key}_{col_key}", fmt_value(item_m.group(2))))
                found = True
            pos = row_m.end()
        if found:
            used_spans.append((matrix_idx, pos))
    return out


def parse_bracket_pairs(block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    out = []
    for m in BRACKET_PAIRS_RE.finditer(block):
        if any(s <= m.start() < e for s, e in used_spans):
            continue
        name = m.group(1)
        pairs = PAIR_ITEM_RE.findall(m.group(2))
        out.append((f"{name}_N", str(len(pairs))))
        for i, (x, y) in enumerate(pairs):
            out.append((f"{name}_{i}_X", fmt_value(x)))
            out.append((f"{name}_{i}_Y", fmt_value(y)))
        used_spans.append(m.span())
    return out


def parse_formula_then_labels(raw_block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """Operates on the ORIGINAL (backtick-preserved) block text, since the
    formula/label split relies on backtick-span boundaries."""
    out = []
    for m in FORMULA_THEN_LABELS_RE.finditer(raw_block):
        formula = m.group(1)
        idents = re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", formula)
        if not idents:
            continue
        items = LABEL_ITEM_RE.findall(m.group(2))
        for label, val in items:
            label_key = snake_upper(label)
            if val.startswith("("):
                lo, hi = [v.strip() for v in val.strip("()").split(",")]
                candidates = sorted(set(i for i in idents if _label_matches(label_key, i)))
                if len(candidates) == 1:
                    out.append((f"{candidates[0]}_LO", fmt_value(lo)))
                    out.append((f"{candidates[0]}_HI", fmt_value(hi)))
                continue
            if "/" in val:
                parts = [v.strip() for v in val.split("/")]
                if len(parts) == len(idents):
                    for ident, v in zip(idents, parts):
                        out.append((ident, fmt_value(v)))
                continue
            candidates = sorted(set(i for i in idents if _label_matches(label_key, i)))
            if len(candidates) == 1:
                out.append((candidates[0], fmt_value(val)))
        used_spans.append(m.span())
    return out


def _label_matches(label_key: str, ident: str) -> bool:
    """True if `label_key` (already SNAKE_UPPER, possibly multi-word, e.g.
    "MAX_HOPS") occupies one or more whole underscore-delimited components
    of `ident`, e.g. "BASE" matches "BASE_BETRAYAL_RATE" and "FLOOR"
    matches "COLLISION_ECONOMY_FLOOR", but "BASE" does not match
    "DATABASE_X"."""
    return f"_{label_key}_" in f"_{ident}_" or ident == label_key


def parse_formula_then_bare_eq(raw_block: str, used_spans: list[tuple[int, int]]) -> list[tuple[str, str]]:
    """"`formula`, `= NUMBER`." -- the value belongs to the formula's one
    identifier that has no other resolution in this same clause."""
    out = []
    for m in FORMULA_THEN_BARE_EQ_RE.finditer(raw_block):
        formula = m.group(1)
        idents = sorted(set(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", formula)))
        if len(idents) == 1:
            out.append((idents[0], fmt_value(m.group(2))))
            used_spans.append(m.span())
    return out


def parse_algorithms_md(text: str) -> tuple[dict[str, Const], list[str], list[str]]:
    blocks = split_alg_blocks(text)
    resolved: dict[str, Const] = {}
    conflicts: list[str] = []
    all_idents_seen: set[str] = set()

    for alg_id, alg_title, raw_block in blocks:
        used_spans: list[tuple[int, int]] = []
        pairs = parse_formula_then_labels(raw_block, used_spans)
        pairs += parse_formula_then_bare_eq(raw_block, used_spans)
        block = strip_backticks(raw_block)
        used_spans = []  # spans above were in raw_block coords; stripping backticks shifts offsets, so re-derive on `block`.
        pairs += parse_bracket_pairs(block, used_spans)
        pairs += parse_brace_matrix(block, used_spans)
        pairs += parse_markdown_tables(block, used_spans)
        pairs += parse_keyed_paren_lists(block, used_spans)
        pairs += parse_keyed_colon_lists(block, used_spans)
        pairs += parse_ranges(block, used_spans)
        pairs += parse_scalars_and_compounds(block, used_spans)

        for name, val in pairs:
            out_name = name if name.startswith("OM_") else f"OM_{name}"
            if out_name in EXCLUDED_NAMES:
                continue
            if out_name in resolved:
                if resolved[out_name].value != val:
                    conflicts.append(
                        f"{out_name}: {resolved[out_name].value} ({resolved[out_name].alg_id}) "
                        f"vs {val} ({alg_id})"
                    )
                continue
            resolved[out_name] = Const(out_name, val, alg_id, alg_title)

        all_idents_seen.update(re.findall(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9]\b", block))

    resolved_bare = {c.name[3:] for c in resolved.values()}
    resolved_bare |= {n[3:] for n in EXCLUDED_NAMES}
    unparsed = sorted(
        ident for ident in all_idents_seen
        if ident not in resolved_bare
        and not any(rb.startswith(ident + "_") for rb in resolved_bare)
    )
    return resolved, unparsed, conflicts


def emit_header(consts: dict[str, Const]) -> str:
    ordered = sorted(consts.values(), key=lambda c: (alg_sort_key(c.alg_id), c.name))
    lines = [
        "/* GENERATED FILE -- do not edit by hand.",
        " * scripts/specfactory/alg_constants.py --emit csrc/om_constants.h",
        " * Source: docs/bible/algorithms.md (ALG-01..75). */",
        "#ifndef OM_CONSTANTS_H",
        "#define OM_CONSTANTS_H",
        "",
    ]
    current_alg = None
    for c in ordered:
        if c.alg_id != current_alg:
            lines.append(f"/* {c.alg_id} {c.alg_title}{TITLE_SUFFIXES.get(c.alg_id, '')} */")
            current_alg = c.alg_id
        lines.append(f"#define {c.name} {c.value}")
    for anchor, extra in MANUAL_INSERTS:
        if anchor not in lines:
            raise SystemExit(f"MANUAL_INSERTS anchor no longer generated: {anchor}")
        at = lines.index(anchor) + 1
        lines[at:at] = extra
    lines.append("")
    lines.append("#endif /* OM_CONSTANTS_H */")
    lines.append("")
    return "\n".join(lines)


def cmd_emit(out_path: Path) -> int:
    text = ALGORITHMS_MD.read_text()
    consts, unparsed, conflicts = parse_algorithms_md(text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(emit_header(consts))
    print(f"emitted {len(consts)} constants to {out_path}")
    if conflicts:
        print(f"CONFLICTS ({len(conflicts)}):")
        for line in conflicts:
            print(f"  {line}")
    if unparsed:
        print(f"UNPARSED ({len(unparsed)}) -- referenced but no value mechanically extracted:")
        for name in unparsed:
            print(f"  {name}")
    return 0


# --------------------------------------------------------------------- csrc lint

DECL_PREFIX_RE = re.compile(
    r"(?:^|[;{}])\s*(?:static\s+|const\s+|volatile\s+)*[A-Za-z_]\w*\s*\**\s*[A-Za-z_]\w*\s*$"
)
DEFINE_LINE_RE = re.compile(r"^\s*#\s*define\b")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"')
CHAR_RE = re.compile(r"'(?:[^'\\\n]|\\.)*'")
SIZEOF_RE = re.compile(r"sizeof\s*\([^()]*\)")
TABLE_START_RE = re.compile(r"^\s*/\*\s*constants-table:\s*(.*?)\s*\*/\s*$")
TABLE_END_RE = re.compile(r"^\s*/\*\s*end constants-table\s*\*/\s*$")
TABLE_CITATION_RE = re.compile(r"docs/bible/|\bS-\d+\b|\bR-\d+-\d+\b|\bALG-\d+\b")
TOKEN_RE = re.compile(
    r"(?<![\w.])(-)?\b(\d+\.\d+(?:[eE][+-]?\d+)?[fFlL]?|\d+[eE][+-]?\d+[fFlL]?|\d+(?:[uUlL]*)|0[xX][0-9a-fA-F]+[uUlL]*)"
)


def _blank(m: re.Match) -> str:
    return "".join(c if c == "\n" else " " for c in m.group(0))


def strip_noise(text: str) -> str:
    text = BLOCK_COMMENT_RE.sub(_blank, text)
    text = LINE_COMMENT_RE.sub(_blank, text)
    text = STRING_RE.sub(_blank, text)
    text = CHAR_RE.sub(_blank, text)
    text = SIZEOF_RE.sub(_blank, text)
    return text


def literal_value(token: str, negative: bool) -> float:
    core = token.rstrip("uUlLfF")
    if core.lower().startswith("0x"):
        v = float(int(core, 16))
    else:
        v = float(core)
    return -v if negative else v


def find_declaration_bracket_spans(line: str) -> list[tuple[int, int]]:
    """[(start, end)] character ranges of every `[...]` on `line` that sits
    directly after a `type name` prefix -- i.e. an array size in a
    declaration, not an indexing expression."""
    spans = []
    for bm in re.finditer(r"\[([^\[\]]*)\]", line):
        prefix = line[:bm.start()]
        if DECL_PREFIX_RE.search(prefix):
            spans.append(bm.span())
        else:
            # a later dimension of the same declaration, e.g. `x[8][16]`
            trail = line[:bm.start()]
            if trail and trail[-1] == "]":
                spans.append(bm.span())
    return spans


def find_constants_table_spans(text: str, rel: str) -> tuple[set[int], list[str]]:
    """[(exempt_lines, errors)] -- `exempt_lines` is the set of 1-based
    line numbers inside a well-formed `constants-table` fence: a
    `/* constants-table: <citation> */` line naming a bible path
    (`docs/bible/...`) or section id (`S-###`, `R-###-##`, `ALG-##`),
    closed by a matching `/* end constants-table */` line before EOF or
    the next start marker. A fence with no citation, an unrecognized
    citation, one still open at EOF, or a start marker nested inside
    another open fence each append an error message and exempt nothing
    for that fence."""
    exempt: set[int] = set()
    errors: list[str] = []
    in_block = False
    block_start = 0
    block_valid = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        start_m = TABLE_START_RE.match(line)
        end_m = TABLE_END_RE.match(line)
        if start_m:
            if in_block:
                errors.append(f"FAIL {rel}:{lineno} nested constants-table marker")
                continue
            citation = start_m.group(1).strip()
            block_valid = bool(citation) and bool(TABLE_CITATION_RE.search(citation))
            if not block_valid:
                errors.append(f"FAIL {rel}:{lineno} constants-table without a bible citation")
            in_block = True
            block_start = lineno
            continue
        if end_m and in_block:
            if block_valid:
                exempt.update(range(block_start, lineno + 1))
            in_block = False
            continue
    if in_block:
        errors.append(f"FAIL {rel}:{block_start} unterminated constants-table block")
    return exempt, errors


def find_violations(text: str) -> list[tuple[int, int, str]]:
    """[(line 1-based, col 1-based, token)] for every bare numeric literal
    in `text` that is not 0, 1, -1, 2, inside a declaration's array-size
    brackets, on a #define line, or inside sizeof(...)."""
    clean = strip_noise(text)
    violations = []
    for lineno, line in enumerate(clean.splitlines(), start=1):
        if DEFINE_LINE_RE.match(line):
            continue
        decl_spans = find_declaration_bracket_spans(line)
        for m in TOKEN_RE.finditer(line):
            start = m.start(1) if m.group(1) else m.start(2)
            token = line[start:m.end(2)]
            val = literal_value(m.group(2), bool(m.group(1)))
            if val in ALWAYS_EXEMPT_VALUES:
                continue
            if any(s <= start < e for s, e in decl_spans):
                continue
            violations.append((lineno, start + 1, token))
    return violations


def find_violations_with_occurrence(text: str) -> list[tuple[int, int, str, int]]:
    """[(lineno, col, token, occurrence)] -- `occurrence` is the 1-based
    count of that exact token text among this text's violations, in the
    same top-to-bottom, left-to-right order find_violations returns them.
    Stable under any edit that does not itself add or remove a matching
    occurrence, so an allowlist keyed on it survives unrelated line
    insertion/deletion."""
    counts: dict[str, int] = {}
    out = []
    for lineno, col, token in find_violations(text):
        counts[token] = counts.get(token, 0) + 1
        out.append((lineno, col, token, counts[token]))
    return out


class Allowlist:
    __slots__ = ("new", "legacy")

    def __init__(self, new: set[tuple[str, str, int]], legacy: set[tuple[str, int, int, str]]):
        self.new = new
        self.legacy = legacy

    def contains(self, rel: str, lineno: int, col: int, token: str, occurrence: int) -> bool:
        return (rel, token, occurrence) in self.new or (rel, lineno, col, token) in self.legacy


def parse_allowlist_lines(lines: list[str]) -> Allowlist:
    """Reads file:token:occurrence (current) and, for a not-yet-regenerated
    file, the deprecated file:line:col:token (matched by its original exact
    line/col, since no occurrence number was ever recorded for it) -- never
    crashes on either, and WARNs once when the deprecated shape is seen."""
    new_entries: set[tuple[str, str, int]] = set()
    legacy_entries: set[tuple[str, int, int, str]] = set()
    saw_legacy = False
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) == 4:
            path, lineno, col, token = parts
            legacy_entries.add((path, int(lineno), int(col), token))
            saw_legacy = True
        elif len(parts) == 3:
            path, token, occurrence = parts
            new_entries.add((path, token, int(occurrence)))
        else:
            raise ValueError(f"unrecognized constants_allowlist.txt line: {line!r}")
    if saw_legacy:
        print(
            f"WARN {ALLOWLIST_PATH}: deprecated file:line:col:token allowlist "
            "entries found -- regenerate with --gen-allowlist"
        )
    return Allowlist(new_entries, legacy_entries)


def load_allowlist() -> Allowlist:
    if not ALLOWLIST_PATH.exists():
        return Allowlist(set(), set())
    return parse_allowlist_lines(ALLOWLIST_PATH.read_text().splitlines())


def lint_file_violations(
    rel: str,
    text: str,
    allowlist: Allowlist,
    grandfathered: bool,
    exempt_lines: frozenset[int] = frozenset(),
) -> list[str]:
    messages = []
    for lineno, col, token, occurrence in find_violations_with_occurrence(text):
        if lineno in exempt_lines:
            continue
        if grandfathered and allowlist.contains(rel, lineno, col, token, occurrence):
            continue
        messages.append(f"FAIL {rel}:{lineno} bare literal `{token}`")
    return messages


def cmd_lint(csrc_dir: Path, strict: bool = False) -> int:
    if not csrc_dir.is_dir():
        print(f"csrc dir not found: {csrc_dir}", file=sys.stderr)
        return 2
    # The lint keys entries by path relative to the tree that holds `csrc_dir`
    # (a merge worktree, not this checkout), and reads that tree's allowlist,
    # so a candidate is judged against the allowlist it carries.
    tree = csrc_dir.resolve().parent
    tree_allowlist = tree / "docs" / "northstar" / "spec_factory" / "constants_allowlist.txt"
    allowlist = (parse_allowlist_lines(tree_allowlist.read_text().splitlines())
                 if tree_allowlist.is_file() else load_allowlist())
    messages = []
    exempted_total = 0
    used_new: set[tuple[str, str, int]] = set()
    used_legacy: set[tuple[str, int, int, str]] = set()
    for c_file in sorted(csrc_dir.glob("*.c")):
        text = c_file.read_text()
        rel = str(c_file.resolve().relative_to(tree))
        grandfathered = c_file.name in GRANDFATHERED_FILES
        exempt_lines, table_errors = find_constants_table_spans(text, rel)
        if strict and grandfathered:
            for lineno, col, token, occurrence in find_violations_with_occurrence(text):
                if lineno not in exempt_lines:
                    used_new.add((rel, token, occurrence))
                    used_legacy.add((rel, lineno, col, token))
        messages.extend(table_errors)
        exempted_total += sum(
            1 for lineno, _col, _token, _occ in find_violations_with_occurrence(text)
            if lineno in exempt_lines
        )
        messages.extend(lint_file_violations(rel, text, allowlist, grandfathered, frozenset(exempt_lines)))
    if strict:
        stale = [f"{r}:{t}:{o}" for r, t, o in sorted(allowlist.new - used_new)]
        stale += [f"{r}:{ln}:{c}:{t}" for r, ln, c, t in sorted(allowlist.legacy - used_legacy)]
        messages.extend(f"STALE {entry}" for entry in stale)
    for m in messages:
        print(m)
    if messages:
        print(f"CONSTANTS LINT FAILED ({len(messages)}) ({exempted_total} table literals exempted)")
        return 1
    print(f"CONSTANTS LINT OK ({exempted_total} table literals exempted)")
    return 0


def gen_allowlist_entries(csrc_dir: Path) -> list[str]:
    """[file:token:occurrence, ...] for every grandfathered file's current
    violations, sorted by (file, source line, source column) so the
    checked-in list reads top to bottom same as the .c files it covers."""
    entries: list[tuple[str, int, int, str, int]] = []
    for c_file in sorted(csrc_dir.glob("*.c")):
        if c_file.name not in GRANDFATHERED_FILES:
            continue
        rel = str(c_file.resolve().relative_to(csrc_dir.resolve().parent))
        for lineno, col, token, occurrence in find_violations_with_occurrence(c_file.read_text()):
            entries.append((rel, lineno, col, token, occurrence))
    entries.sort(key=lambda e: (e[0], e[1], e[2]))
    return [f"{rel}:{token}:{occurrence}" for rel, _lineno, _col, token, occurrence in entries]


def cmd_gen_allowlist(csrc_dir: Path) -> int:
    lines = gen_allowlist_entries(csrc_dir)
    ALLOWLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALLOWLIST_PATH.write_text("\n".join(lines) + "\n")
    print(f"wrote {len(lines)} entries to {ALLOWLIST_PATH}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", metavar="PATH", help="write the generated header to PATH")
    g.add_argument("--lint", metavar="CSRC_DIR", help="lint CSRC_DIR/*.c for bare numeric literals")
    g.add_argument("--gen-allowlist", metavar="CSRC_DIR",
                    help="regenerate the grandfathered-literal allowlist from CSRC_DIR/*.c")
    ap.add_argument("--strict", action="store_true",
                    help="with --lint: also fail on allowlist entries matching no current violation")
    args = ap.parse_args(argv)

    if args.emit:
        return cmd_emit(Path(args.emit))
    if args.lint:
        return cmd_lint(Path(args.lint), args.strict)
    return cmd_gen_allowlist(Path(args.gen_allowlist))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
