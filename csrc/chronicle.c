/* csrc/chronicle.c -- E-09 chronicle (B8, push/B8). Ports
 * simulation/chronicle_distiller.py + simulation/chronicle_assembler.py
 * (923 py lines) to the frozen C ABI in csrc/ouroboros_sim.h. Per-world
 * state lives in w->chronicle_state / w->chronicle_state_free (F2i,
 * 14ff4d8), same convention as csrc/mission.c's om_mis()/om_mission_state.
 *
 * PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).
 * Use exactly these member names; there are no others.
 * #define OM_MAX_NEIGHBORS 32
 * #define OM_DAMAGE_HISTORY_CAP 64
 *
 * typedef struct {
 *     om_tier  tier;
 *     double   military, economy, tension, population;
 *     double   econ_phase, tension_phase;
 *     double   prev_econ_osc, prev_tension_osc;
 *     int32_t  faction_id;
 *     uint32_t neighbors[OM_MAX_NEIGHBORS];
 *     uint32_t n_neighbors;
 *     om_drift_row last_drift;
 *     uint64_t damage_tick[OM_DAMAGE_HISTORY_CAP];
 *     double   damage_military[OM_DAMAGE_HISTORY_CAP];
 *     double   damage_economy[OM_DAMAGE_HISTORY_CAP];
 *     uint32_t damage_head, damage_len;
 * } om_region;
 *
 * struct om_world {
 *     uint32_t n_regions;
 *     uint64_t seed;
 *     uint64_t tick;
 *     ...
 *     void *chronicle_state;
 *     void (*chronicle_state_free)(void *);
 *     ...
 * };
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

/* OM_SIGNIFICANCE_*_BONUS constants and R-067-02..05 thresholds (OM_CHRON_THRIVED_*,
 * OM_CHRON_SUFFERED_*, OM_CHRON_CASCADE_MIN_EVENTS, OM_CHRON_VICTORY_*, OM_CHRON_DEFEAT_*,
 * OM_CHRON_STALEMATE_*, OM_CHRON_REGIONAL_*) promoted to csrc/om_constants.h
 * (ALG-50/E-09, CONST-1). */

/* ALG-52 selection. */
#define OM_CHRON_CATEGORY_CAP 2

/* ALG-53 assembly. */
#define OM_CHRON_ECHO_WORD_THRESHOLD 6
#define OM_CHRON_DEDUP_OVERLAP_THRESHOLD 0.40
#define OM_CHRON_BASE_WORD_WARN 90
#define OM_CHRON_EXPANDED_WORD_WARN 140
#define OM_CHRON_CONTENT_WORD_MIN_LEN 3

/* S-071 launch library contract. */
#define OM_CHRON_MIN_OPENINGS 6
#define OM_CHRON_MIN_DETAILS 8
#define OM_CHRON_MIN_CLOSINGS 5
#define OM_CHRON_BATCH_REJECTION_LIMIT 0.35
#define OM_CHRON_NEAR_DUP_EDIT_THRESHOLD 3
#define OM_CHRON_N_LINEAGE_CATEGORIES 5
#define OM_CHRON_N_CHAIN_CATEGORIES 8
#define OM_CHRON_N_REGIONAL_CATEGORIES 4
#define OM_CHRON_N_CONSEQUENCE_CATEGORIES 3
#define OM_CHRON_N_CATEGORIES 20
/* R-065-07: the opening jump's scroll has 3 to 5 entries. */
#define OM_CHRON_OPENING_MIN_ENTRIES 3
#define OM_CHRON_OPENING_MAX_ENTRIES 5

/* S-069 presentation constants. */
#define OM_CHRON_SLIDE_IN_SEC 0.40
#define OM_CHRON_SLIDE_OUT_SEC 0.40
#define OM_CHRON_MAP_WIDTH_RATIO 0.62
#define OM_CHRON_WORD_CADENCE_SEC 0.08
#define OM_CHRON_WORD_FADE_SEC 0.20
#define OM_CHRON_ENTRY_HOLD_SEC 3.0

/* OM_CHRON_STABILITY_x, OM_CHRON_CAPACITY_x, OM_CHRON_TENSION_x prose bands
 * promoted to csrc/om_constants.h (E-09 R-068-03, CONST-1). */
#define OM_CHRON_DURATION_DAYS_MAX 5
#define OM_CHRON_DURATION_WEEKS_MAX 15
#define OM_CHRON_DURATION_MONTHS_MAX 30
#define OM_CHRON_DURATION_YEAR_MAX 60

/* Local deterministic RNG (splitmix64), seeded from the ALG-53 jump start
 * tick -- a stream separate from w's own om_rng_draw so re-running assembly
 * never perturbs the sim's own trace/checksum. */
#define CHRON_RNG_GOLDEN 0x9E3779B97F4A7C15ULL
#define CHRON_RNG_MIX1 0xBF58476D1CE4E5B9ULL
#define CHRON_RNG_MIX2 0x94D049BB133111EBULL
#define CHRON_RNG_SHIFT1 30
#define CHRON_RNG_SHIFT2 27
#define CHRON_RNG_SHIFT3 31
#define CHRON_RNG_OUT_SHIFT 11
#define CHRON_RNG_SCALE (1.0 / 9007199254740992.0)

/* Cluster type ids (OMClusterType in every E-09 test file). */
#define CTYPE_CONSEQUENCE 0
#define CTYPE_LINEAGE 1
#define CTYPE_CHAIN 2
#define CTYPE_REGIONAL 3

/* Sparse chronicle category ids (OMLineageCategory/OMChainCategory/
 * OMRegionalCategory/OMOutcomeCategory across the E-09 test files). */
#define CAT_LINEAGE_SUCCESSION 0
#define CAT_LINEAGE_MILITARY_ACTION 1
#define CAT_LINEAGE_THRIVED 2
#define CAT_LINEAGE_SUFFERED 3
#define CAT_LINEAGE_QUIET 4
#define CAT_CHAIN_REVOLT_SPAWNED 10
#define CAT_CHAIN_EXPANSION 11
#define CAT_CHAIN_CASCADE 12
#define CAT_CHAIN_CONFLICT_VICTORY 13
#define CAT_CHAIN_CONFLICT_DEFEAT 14
#define CAT_CHAIN_CONFLICT_STALEMATE 15
#define CAT_CHAIN_CRISIS_RESOLVED_WELL 16
#define CAT_CHAIN_CRISIS_RESOLVED_BADLY 17
#define CAT_REGIONAL_FACTION_SHIFT 20
#define CAT_REGIONAL_GROWTH 21
#define CAT_REGIONAL_DECLINE 22
#define CAT_REGIONAL_STABLE 23
#define CAT_CONSEQUENCE_SUCCESS 30
#define CAT_CONSEQUENCE_FAILURE 31
#define CAT_CONSEQUENCE_MIXED 32
#define CAT_CONSEQUENCE_RIPPLE 33

#define CHRON_MAX_CANDIDATES 256
#define CHRON_MAX_FINAL 16
#define CHRON_MAX_RAW_CHAIN 128
#define CHRON_MAX_TEXT_ENTRIES 64
#define CHRON_MAX_MOCK_ENTRIES 64
#define CHRON_MAX_OWNERSHIP_CHANGES 64
#define CHRON_MAX_KEYFRAMES 256
#define CHRON_MAX_ENTRY_STATES 64
#define CHRON_FULL_TEXT_CAP 16384
#define CHRON_FRAGMENT_TEXT_CAP 320
#define CHRON_SLOT_VALUE_CAP 96
/* Matches om_chronicle_entry.base_text[512]/expanded_text[1024] exactly
 * (csrc/ouroboros_sim.h, the frozen struct). */
#define CHRON_BASE_TEXT_CAP 512
#define CHRON_EXPANDED_TEXT_CAP 1024

typedef struct {
    const char *id;
    const char *text;
    uint32_t category;
    uint32_t type; /* 0 opening, 1 detail, 2 closing */
    uint32_t word_count;
} chron_fragment;

/* Launch fragment library, ported field-for-field from
 * simulation/library/chronicle/fragments.json (E-21 offline generation);
 * category is the sparse chronicle category id, type is 0 opening /
 * 1 detail / 2 closing, word_count is the authored fragment's own count. */
/* constants-table: docs/bible/epics/E-09-chronicle.md S-071 */
static const chron_fragment CHRON_FRAGMENTS[] = {
    { "LT_O_001", "In the generations that followed, {lineage_name} household emerged as one of {region_name}'s most respected families.", 2, 0, 17 },
    { "LT_O_002", "{duration_prose}, {lineage_name} name became synonymous with steady prosperity and quiet influence.", 2, 0, 14 },
    { "LT_O_003", "It was during this period that {lineage_name} line secured the foundations of what later chroniclers would call their golden age.", 2, 0, 22 },
    { "LT_O_004", "The fortunes of {lineage_name} household rose with a patience that distinguished them from the era's more reckless aspirants.", 2, 0, 20 },
    { "LT_O_005", "By the time {character_name} assumed stewardship, {lineage_name} name already carried considerable weight across {region_name}.", 2, 0, 16 },
    { "LT_O_006", "What {lineage_name} family built in those years was not dramatic but enduring, the kind of success measured in generations.", 2, 0, 21 },
    { "LT_D_001", "{lineage_name} estates grew not through conquest but through the careful accumulation of obligations owed and favors granted, until their ledgers read like a census of the region's debts.", 2, 1, 32 },
    { "LT_D_002", "Under {character_name}'s guidance, {lineage_name} household extended its reach into {region_name}'s administrative councils, occupying posts that others considered thankless but that proved, in time, indispensable.", 2, 1, 28 },
    { "LT_D_003", "Where rival houses spent lavishly on spectacle, {lineage_name} invested in granaries, roads, and the quieter instruments of lasting influence. The returns compounded in ways their competitors understood only too late.", 2, 1, 32 },
    { "LT_D_004", "{lineage_name} name appeared with increasing frequency in trade contracts across {region_name}, a presence so gradual that no single rival thought to challenge it until the pattern was already irreversible.", 2, 1, 31 },
    { "LT_D_005", "Marriages were arranged with precision, alliances cultivated through shared harvests rather than shared enemies, and {duration_prose} {lineage_name} household had woven itself into the fabric of {region_name}'s stability.", 2, 1, 30 },
    { "LT_D_006", "With conditions holding at {stability_level} levels, {lineage_name} found space to consolidate rather than merely survive. It was a rare luxury, and they spent it wisely.", 2, 1, 28 },
    { "LT_D_007", "{character_name} proved less a visionary than a reliable steward, and for {lineage_name} line, that distinction mattered more than posterity might credit. The household prospered precisely because no one thought to watch it.", 2, 1, 34 },
    { "LT_D_008", "{lineage_name} coffers deepened, their circle of dependents widened, and a generation that had inherited uncertainty left behind something closer to an institution.", 2, 1, 23 },
    { "LT_C_001", "Later generations of {lineage_name} line would look back on this period as proof that fortune favors not the bold, but the patient. Whether that patience would endure was another question entirely.", 2, 2, 33 },
    { "LT_C_002", "{lineage_name} prosperity was real, but so was the weight of expectation it created. Houses that rise must eventually choose what they are willing to spend to remain standing.", 2, 2, 31 },
    { "LT_C_003", "In {region_name}, {lineage_name} name became one of those quiet certainties that people stopped questioning — the kind of permanence that invites complacency as readily as confidence.", 2, 2, 27 },
    { "LT_C_004", "What {lineage_name} had built was admirable, perhaps even enviable. But no chronicle of enduring success has ever ended without a chapter on what came next.", 2, 2, 27 },
    { "LT_C_005", "For now, {lineage_name} household stood on ground of its own making, {stability_level} in its position and certain of its purpose — a certainty that history rarely leaves undisturbed.", 2, 2, 29 },
    { "LS_O_001", "The years that followed were not kind to {lineage_name} name.", 3, 0, 13 },
    { "LS_O_002", "In {region_name}, where {lineage_name} had once walked with authority, a quieter era of diminishment began.", 3, 0, 16 },
    { "LS_O_003", "{duration_prose}, {lineage_name} household endured what later chroniclers would describe only as a period of loss.", 3, 0, 16 },
    { "LS_O_004", "No single disaster unmade {lineage_name} — it was a slow accumulation of wounds, each compounding the last.", 3, 0, 17 },
    { "LS_O_005", "What befell {lineage_name} in those years left few records and fewer witnesses willing to speak of it.", 3, 0, 17 },
    { "LS_O_006", "A generation later, those who remembered {lineage_name} at their height could scarcely reconcile it with what remained.", 3, 0, 17 },
    { "LS_D_001", "{lineage_name} buried three of their own before the season turned. No battles claimed them — only the particular cruelties of a world grown indifferent to old loyalties.", 3, 1, 29 },
    { "LS_D_002", "{character_name} was the last of {lineage_name} line to hold any post of consequence, and even that was stripped away quietly, without ceremony or explanation, as though the family had simply ceased to matter.", 3, 1, 33 },
    { "LS_D_003", "In {region_name}, the foundations of ordinary life gave way beneath them. {lineage_name} bore the weight of this collapse more than most, their holdings shrinking to what could be maintained by a skeleton household.", 3, 1, 34 },
    { "LS_D_004", "Debts mounted against {lineage_name} estate. Properties were sold at unfavorable terms. Servants departed without being dismissed. By the end, the family's presence in the district was more rumor than fact.", 3, 1, 32 },
    { "LS_D_005", "{lineage_name} sent petitions to every authority that would receive them, but the replies — when they came at all — offered sympathy without substance. {duration_prose}, the family learned the difference between allies and acquaintances.", 3, 1, 35 },
    { "LS_D_006", "{character_name} of {lineage_name} kept meticulous accounts through the worst of it, as though recording each loss might somehow contain it. The ledgers survive. They make for difficult reading.", 3, 1, 30 },
    { "LS_D_007", "What remained of {lineage_name} influence in {region_name} could be measured in silences — seats left empty at council, invitations no longer extended, debts called in by creditors who once would not have dared.", 3, 1, 33 },
    { "LS_D_008", "{lineage_name} name still appeared in the registries, but it carried a different weight now. Children of the household were raised on stories of what had been, and the silence of what was.", 3, 1, 33 },
    { "LS_C_001", "Whether {lineage_name} could recover from such losses remained an open question. But survival itself, in those circumstances, constituted a kind of defiance that later generations would need to decide how to spend.", 3, 2, 33 },
    { "LS_C_002", "{lineage_name} endured, though the word felt hollow. What persisted was not strength but habit — the slow insistence of a name that had forgotten how to disappear.", 3, 2, 28 },
    { "LS_C_003", "In {region_name}, the memory of {lineage_name} decline served as cautionary scripture. Families who had once envied them now invoked their name as proof that nothing was guaranteed.", 3, 2, 29 },
    { "LS_C_004", "Grief, for {lineage_name}, became a kind of inheritance — passed from parent to child not in words but in the careful way they held what little remained.", 3, 2, 28 },
    { "LS_C_005", "{lineage_name} would carry the scars of this period long after the material losses were tallied. Some wounds do not appear in ledgers.", 3, 2, 23 },
    { "LQ_O_001", "For a time, {lineage_name} household knew something rare in {region_name}: years that passed without crisis.", 4, 0, 17 },
    { "LQ_O_002", "The records of {lineage_name} family grow sparse here, not from neglect, but from the gentle poverty of uneventful years.", 4, 0, 20 },
    { "LQ_O_003", "{duration_prose}, {lineage_name} name appeared in no dispatches, no treaties, and no eulogies.", 4, 0, 14 },
    { "LQ_O_004", "What followed for {lineage_name} household was not peace so much as the simple absence of catastrophe.", 4, 0, 17 },
    { "LQ_O_005", "In {region_name}, {lineage_name} family settled into a rhythm that later generations would remember only as warmth.", 4, 0, 17 },
    { "LQ_O_006", "History has little to say about {lineage_name} household during these years, and perhaps that is the point.", 4, 0, 18 },
    { "LQ_D_001", "Children were born into {lineage_name} name and grew old enough to be bored by it. Harvests came and went. The eldest repaired a wall their grandparents had built, and no one thought it worth recording.", 4, 1, 35 },
    { "LQ_D_002", "{lineage_name} estates in {region_name} produced modestly and consistently, enough to keep creditors away and ambition dormant. Neighbors borrowed tools and returned them. Small disputes were settled before they earned names.", 4, 1, 32 },
    { "LQ_D_003", "With conditions across {region_name} holding at {stability_level} levels, {lineage_name} household occupied itself with the slow business of living — marriages arranged without urgency, debts repaid in full, land neither gained nor lost.", 4, 1, 34 },
    { "LQ_D_004", "{lineage_name} family traded no blows and signed no pacts. {duration_prose}, their most consequential act was the planting of an orchard that would not bear fruit for another decade.", 4, 1, 30 },
    { "LQ_D_005", "A younger branch of {lineage_name} line took up letters; an elder cousin kept bees. The family's holdings in {region_name} neither expanded nor contracted, and the ledgers from this period are notable mainly for their tidiness.", 4, 1, 37 },
    { "LQ_D_006", "No one tested {lineage_name} household during these years. Whether this owed to respect, irrelevance, or mere fortune, the sources do not say. The family simply endured, which is its own accomplishment.", 4, 1, 32 },
    { "LQ_D_007", "{lineage_name} household observed the usual rites, settled the usual quarrels, and buried the usual number of elders. Stability in {region_name} held at {stability_level} levels, and life asked nothing extraordinary.", 4, 1, 29 },
    { "LQ_D_008", "{duration_prose}, {lineage_name} name carried quietly forward — not celebrated, not threatened, simply present. A son learned his father's trade. A daughter married into a neighboring family and was, by all accounts, content.", 4, 1, 33 },
    { "LQ_C_001", "It would be easy to skip past these years in {lineage_name} chronicle. But those who lived them would not have traded them for glory.", 4, 2, 25 },
    { "LQ_C_002", "Later, when {lineage_name} name was spoken in harder contexts, some would look back on this period and wonder whether peace had been a gift or merely a pause.", 4, 2, 29 },
    { "LQ_C_003", "{lineage_name} household emerged from these quiet years neither stronger nor weaker — only older, and perhaps wiser for having wanted nothing they did not already possess.", 4, 2, 27 },
    { "LQ_C_004", "In {region_name}, {lineage_name} family had become part of the landscape — expected, unremarkable, and more deeply rooted than anyone, including themselves, quite realized.", 4, 2, 24 },
    { "LQ_C_005", "These were the years {lineage_name} household would not think to mention in their own histories. Contentment seldom makes it into the record. That does not make it less real.", 4, 2, 30 },
    { "LMA_O_001", "When the call to arms came, {lineage_name} household answered without deliberation, as though the obligation had never truly been in question.", 1, 0, 22 },
    { "LMA_O_002", "{lineage_name} committed their forces to the defense of {region_name} under circumstances that left little room for hesitation.", 1, 0, 18 },
    { "LMA_O_003", "It fell to {character_name} to lead {lineage_name} levy into a campaign that would test the family's resolve in full measure.", 1, 0, 22 },
    { "LMA_O_004", "With {faction_name} pressing hard along the frontier, {lineage_name} had no choice but to marshal what strength remained.", 1, 0, 18 },
    { "LMA_O_005", "{lineage_name} name had long carried obligations to {region_name}, and the season's hostilities demanded those obligations be honored in blood.", 1, 0, 19 },
    { "LMA_O_006", "There was no ceremony to {lineage_name} mobilization — only the grim arithmetic of how many could be spared and how quickly.", 1, 0, 20 },
    { "LMA_D_001", "{lineage_name} fielded their garrison under {character_name}, whose {character_rank} carried enough authority to hold the line but not enough to dictate the broader campaign. They fought where they were placed and held what they were given.", 1, 1, 38 },
    { "LMA_D_002", "Across {region_name}, {lineage_name} forces engaged in a series of contested actions that yielded no single decisive moment but collectively shaped the ground on which the next season’s campaigns would be fought.", 1, 1, 33 },
    { "LMA_D_003", "{lineage_name} committed their reserves earlier than prudence would have counseled, but the pressure from {faction_name} left few alternatives. What followed was costly, methodical, and without glory.", 1, 1, 28 },
    { "LMA_D_004", "{character_name} organized {lineage_name} detachments with the economy of someone who understood that replacements would not come. Every position was chosen for defensibility, every withdrawal timed to preserve what could not be rebuilt.", 1, 1, 33 },
    { "LMA_D_005", "{lineage_name} contribution to the campaign was not the stuff of ballads — supply trains guarded, flanks screened, garrisons rotated through thankless postings in {region_name} — but it was the work that kept the effort standing.", 1, 1, 34 },
    { "LMA_D_006", "When {faction_name} struck in force, {lineage_name} units absorbed the worst of the initial assault. The toll was severe, and {field_delta_summary} in the weeks that followed.", 1, 1, 27 },
    { "LMA_D_007", "{lineage_name} fought as their position demanded: without retreat, without reinforcement, and with the particular stubbornness of a household that understood what defeat would cost them beyond the battlefield.", 1, 1, 28 },
    { "LMA_D_008", "Under {character_name}'s command, {lineage_name} forces held their assigned corridor through {region_name} at considerable expense. The ground was kept, though the household would feel the cost for years afterward.", 1, 1, 30 },
    { "LMA_C_001", "{lineage_name} had done what was asked of them, and the record would show it. Whether the sacrifice had been necessary or merely expected was a question no one in authority cared to answer.", 1, 2, 34 },
    { "LMA_C_002", "For {lineage_name}, the campaign left scars that no commendation could address. They had proven their loyalty; the open question was what loyalty had cost them.", 1, 2, 27 },
    { "LMA_C_003", "{lineage_name} withdrew from the field with their obligations fulfilled and their ranks thinned. In {region_name}, their name now carried a weight that owed nothing to commerce or politics.", 1, 2, 30 },
    { "LMA_C_004", "What {lineage_name} purchased with that season's blood was not victory but credibility — the kind that is acknowledged in silence and repaid, if at all, in future considerations.", 1, 2, 29 },
    { "LMA_C_005", "The ledger of {lineage_name} household grew heavier that year. Duty had been met, but duty of that magnitude leaves a family changed in ways that peacetime seldom repairs.", 1, 2, 29 },
    { "SU_O_001", "The mantle of {lineage_name} household passed, as it always had, not with ceremony but with necessity.", 0, 0, 17 },
    { "SU_O_002", "In {region_name}, a new generation of {lineage_name} house stepped into roles their predecessors had held for as long as anyone could recall.", 0, 0, 22 },
    { "SU_O_003", "{duration_prose}, the elder {lineage_name} relinquished what authority remained to them, and younger hands took up the family's obligations.", 0, 0, 18 },
    { "SU_O_004", "{lineage_name} succession unfolded as such things do — quietly, imperfectly, and with the weight of everything left unsaid between parent and child.", 0, 0, 23 },
    { "SU_O_005", "When the time came for {lineage_name} to entrust their affairs to the next generation, the transition was neither swift nor painless.", 0, 0, 22 },
    { "SU_O_006", "A chapter closed for {lineage_name}, though the household itself continued — altered in voice, if not in name.", 0, 0, 18 },
    { "SU_D_001", "{character_name} assumed stewardship of {lineage_name} holdings with a demeanor that suggested long preparation, though those close to the family knew the appointment had come sooner than anyone intended.", 0, 1, 30 },
    { "SU_D_002", "{lineage_name} heir inherited not merely property and title but a web of obligations — debts of loyalty owed and owed to, alliances maintained through habit, and enemies whose grievances predated their birth.", 0, 1, 32 },
    { "SU_D_003", "In {region_name}, {lineage_name} succession was observed with the particular attentiveness that neighbors reserve for any shift in a familiar household. Old arrangements were quietly reassessed; new courtesies extended.", 0, 1, 30 },
    { "SU_D_004", "The younger {lineage_name} kept what customs they could and discarded what no longer served. Certain traditions survived intact; others were amended beyond recognition, though the family would not have described it that way.", 0, 1, 33 },
    { "SU_D_005", "{character_name} of {lineage_name} house brought a different temperament to the family's affairs — less cautious, perhaps, but no less deliberate. The household's priorities shifted in ways that only became legible with time.", 0, 1, 32 },
    { "SU_D_006", "{duration_prose}, {lineage_name} completed a generational transfer that left the family's outward position largely intact. What changed was interior — a matter of instinct, emphasis, and which debts the new steward chose to honor first.", 0, 1, 35 },
    { "SU_D_007", "The retiring {lineage_name} patriarch offered counsel that was received with public gratitude and private reservation. The young do not refuse their elders' wisdom; they simply reinterpret it until it resembles their own.", 0, 1, 30 },
    { "SU_D_008", "Among {lineage_name} kin, the succession was remembered less for who assumed authority than for what was preserved — certain letters, a way of conducting business, an instinct for timing.", 0, 1, 29 },
    { "SU_C_001", "{lineage_name} name endured, carried now by voices that had not yet learned all its inflections. Whether they would prove faithful stewards or restless inheritors remained to be seen.", 0, 2, 29 },
    { "SU_C_002", "Every generation of {lineage_name} house believed itself the rightful custodian of the family's legacy. History would adjudicate, as it always does — slowly, and without appeal.", 0, 2, 26 },
    { "SU_C_003", "In {region_name}, {lineage_name} transition occasioned neither celebration nor mourning, but something more durable: the quiet recognition that continuity demands its own kind of courage.", 0, 2, 25 },
    { "SU_C_004", "What the new {lineage_name} steward would make of their inheritance was, for the moment, less important than the simple fact of its survival. The name persisted. That alone was not nothing.", 0, 2, 31 },
    { "SU_C_005", "{lineage_name} had weathered the passage from one generation to the next, as they had before. The question was never whether the family would continue, but what it would become.", 0, 2, 30 },
    { "CCRW_O_001", "The crisis in {region_name} did not end so much as exhaust itself, leaving behind a stillness that no one yet trusted.", 16, 0, 20 },
    { "CCRW_O_002", "{duration_prose}, {region_name} clawed its way back from the edge — not triumphantly, but with the grim patience of survivors.", 16, 0, 18 },
    { "CCRW_O_003", "By the time the worst had passed in {region_name}, those who remembered its beginning could scarcely believe the holding together.", 16, 0, 19 },
    { "CCRW_O_004", "What saved {region_name} was not brilliance but endurance, and the outcome owed more to stubbornness than to any single decision.", 16, 0, 18 },
    { "CCRW_O_005", "When stability finally returned to {region_name}, it arrived not as a proclamation but as a slow unclenching of ordinary life.", 16, 0, 18 },
    { "CCRW_O_006", "The chronicles of {region_name} record the season the granaries reopened with the same gravity others reserve for battles won.", 16, 0, 17 },
    { "CCRW_D_001", "The chain of failures that had threatened {region_name} — {chain_length} crises deep — was arrested not by outside intervention but by a series of unglamorous local compromises that amounted to rescue.", 16, 1, 31 },
    { "CCRW_D_002", "{character_name} earned no songs for what was done in {region_name}. The work was administrative: rationing enforced, debts restructured, old grievances quietly shelved. Yet it held, and that was enough.", 16, 1, 30 },
    { "CCRW_D_003", "In {region_name}, the worst had passed — though it took time for anyone to believe it. Recovery came unevenly, but the trajectory, at last, pointed upward.", 16, 1, 26 },
    { "CCRW_D_004", "The {event_description} that had set {region_name} spiraling proved, in the end, survivable. Roads reopened. Markets resumed their old rhythms. The damage was real, but it was not terminal.", 16, 1, 28 },
    { "CCRW_D_005", "Conditions across {region_name} steadied to {stability_level} levels — not the prosperity anyone had hoped for, but a foundation solid enough to build upon, and after what had come before, no one complained.", 16, 1, 31 },
    { "CCRW_D_006", "{duration_prose}, the cascading troubles in {region_name} were unwound one by one. Each resolution was partial, each compromise imperfect, but the accumulation of small repairs proved greater than the sum of its parts.", 16, 1, 32 },
    { "CCRW_D_007", "The people of {region_name} did not celebrate. They audited. Stores were counted, walls inspected, obligations tallied. Relief, where it existed, expressed itself as vigilance rather than joy.", 16, 1, 26 },
    { "CCRW_D_008", "{character_name} oversaw the restoration of {region_name} with the demeanor of someone still expecting the next blow. Granaries were filled beyond need, reserves doubled, as though prosperity itself could not yet be believed.", 16, 1, 32 },
    { "CCRW_C_001", "{region_name} had survived, though the scars would govern its choices for a generation. Caution had become the region's defining inheritance, and no one saw fit to question it.", 16, 2, 27 },
    { "CCRW_C_002", "In later years, the recovery of {region_name} would be cited as proof that ruin is not inevitable — though those who lived through it preferred not to test the thesis twice.", 16, 2, 30 },
    { "CCRW_C_003", "The lesson {region_name} carried forward was simple and unromantic: that the difference between collapse and continuity is often nothing more than one correct decision made under duress.", 16, 2, 27 },
    { "CCRW_C_004", "Stability returned to {region_name}, but it was the wary kind — the stability of people who had seen how quickly the ground could shift, and who slept lightly because of it.", 16, 2, 30 },
    { "CCRW_C_005", "What {region_name} reclaimed was not what it had lost. The old order was gone. But what replaced it functioned, and in the arithmetic of survival, that counted as victory.", 16, 2, 28 },
    { "CCRB_O_001", "What befell {region_name} in those years was not a single catastrophe but a sequence of failures, each compounding the last beyond recovery.", 17, 0, 22 },
    { "CCRB_O_002", "The crisis that gripped {region_name} {duration_prose} left behind damage that no subsequent administration would fully repair.", 17, 0, 16 },
    { "CCRB_O_003", "By the time the worst had passed in {region_name}, the word 'resolution' carried a bitter irony that contemporaries did not miss.", 17, 0, 20 },
    { "CCRB_O_004", "There were opportunities to arrest the decline in {region_name}, and the historical record is clear that each one was squandered.", 17, 0, 19 },
    { "CCRB_O_005", "{duration_prose}, the troubles in {region_name} deepened past the threshold where competent leadership alone could have mattered.", 17, 0, 15 },
    { "CCRB_O_006", "Later chroniclers would mark {event_description} as the moment {region_name} crossed from crisis into something more permanent.", 17, 0, 15 },
    { "CCRB_D_001", "The chain of events that tore through {region_name} ran {chain_length} links deep, each one narrowing the range of possible outcomes until nothing remained but the worst of them.", 17, 1, 29 },
    { "CCRB_D_002", "{character_name} attempted to hold {region_name} together through improvisation and personal authority, but the underlying conditions had already moved beyond what any single figure could contain. {field_delta_summary}, and the collapse proceeded with its own momentum.", 17, 1, 36 },
    { "CCRB_D_003", "With stability at {stability_level} levels across {region_name}, decisions made under pressure proved ruinous. Resources went to the wrong positions, alliances to the wrong parties, and each error compounded.", 17, 1, 28 },
    { "CCRB_D_004", "The damage to {region_name} was not merely material. Institutional knowledge was lost, administrative continuity severed, and {field_delta_summary} in ways that would constrain every subsequent effort at reconstruction.", 17, 1, 26 },
    { "CCRB_D_005", "What began as {event_description} in {region_name} metastasized through a chain of dependent failures. Each intervention arrived too late and addressed the wrong symptom, until intervention itself became part of the problem.", 17, 1, 31 },
    { "CCRB_D_006", "Across {region_name}, the population that survived the crisis emerged into circumstances so diminished that the distinction between endurance and defeat became largely academic.", 17, 1, 22 },
    { "CCRB_D_007", "{character_name} bore the brunt of later blame for {region_name}'s unraveling, though the honest assessment is that the situation had already passed the point where individual competence could alter the trajectory.", 17, 1, 29 },
    { "CCRB_D_008", "{duration_prose}, {region_name} shed what had taken generations to build. Granaries emptied, trade routes contracted, and {field_delta_summary} with a finality that left no ambiguity about what had been lost.", 17, 1, 28 },
    { "CCRB_C_001", "{region_name} that emerged from the crisis bore its old name and little else. What had been broken would be rebuilt, if at all, on entirely different foundations.", 17, 2, 28 },
    { "CCRB_C_002", "Historians would debate whether {region_name}'s collapse was inevitable or merely unresisted. For those who lived through it, the distinction offered no comfort whatsoever.", 17, 2, 23 },
    { "CCRB_C_003", "With stability at {stability_level} levels and the old structures in ruin, {region_name} entered a period that later writers would describe only by what it lacked.", 17, 2, 25 },
    { "CCRB_C_004", "The losses sustained in {region_name} were of the kind that reshape a society's sense of what is possible. Ambitions contracted, horizons narrowed, and memory itself became a burden.", 17, 2, 28 },
    { "CCRB_C_005", "In {region_name}, the crisis did not end so much as exhaust itself, leaving behind a silence that the survivors understood as permanent.", 17, 2, 21 },
    { "CCV_O_001", "The contest for {region_name} ended not in negotiation but in the silence that follows a decisive blow.", 13, 0, 17 },
    { "CCV_O_002", "{duration_prose}, the balance of power in {region_name} shifted irreversibly, and the maps were redrawn to match.", 13, 0, 16 },
    { "CCV_O_003", "When the fighting around {region_name} ceased, the borders it left behind bore no resemblance to those that had provoked it.", 13, 0, 19 },
    { "CCV_O_004", "The campaign that broke {faction_name} hold on {region_name} was swift enough that even the victors seemed surprised by its completeness.", 13, 0, 18 },
    { "CCV_O_005", "The fall of {region_name} to new masters was the kind of outcome that later generations would call inevitable, though it had not felt so at the time.", 13, 0, 27 },
    { "CCV_O_006", "{region_name} changed hands in a season, and with it the strategic calculus of every neighboring power.", 13, 0, 15 },
    { "CCV_D_001", "{character_name} committed forces along the full breadth of {region_name}, leaving no corridor for withdrawal. The defending garrisons, cut off from resupply and reinforcement, capitulated piecemeal over a matter of weeks.", 13, 1, 30 },
    { "CCV_D_002", "{faction_name}'s position in {region_name} collapsed from the flanks inward. Supply lines from {adjacent_region} were severed early, and what followed was less a battle than a methodical enclosure.", 13, 1, 29 },
    { "CCV_D_003", "Three engagements decided {region_name}: one at its northern approaches, one at its river crossings, and one — the briefest and most consequential — at the gates of its administrative center. Each was won convincingly.", 13, 1, 31 },
    { "CCV_D_004", "In {region_name}, the transfer was swift and its terms were not negotiated. The victors inherited a territory whose loyalties had shifted, and authority was assumed with cold efficiency.", 13, 1, 28 },
    { "CCV_D_005", "{character_name} accepted the surrender of {region_name}'s remaining garrison without ceremony. Terms were dictated, not negotiated, and the occupying force was installed before the emissaries had returned home.", 13, 1, 27 },
    { "CCV_D_006", "{faction_name}'s armies quit {region_name} in disorder, abandoning stores and fortifications intact. {duration_prose}, a territory that had been bitterly contested became unambiguously held, its former defenders scattered beyond {adjacent_region}.", 13, 1, 30 },
    { "CCV_D_007", "Control of {region_name} was established through a campaign remarkable for its discipline. No sacking, no reprisals — only the systematic replacement of one authority with another, carried out with a conqueror's patience.", 13, 1, 30 },
    { "CCV_D_008", "The road through {region_name} to {adjacent_region} now lay open, and the strategic implications were immediately understood by every power with interests in the corridor. What had been a frontier was now a thoroughfare.", 13, 1, 33 },
    { "CCV_C_001", "The new order in {region_name} would prove durable, not because it was just, but because those who might have contested it no longer possessed the means.", 13, 2, 26 },
    { "CCV_C_002", "{region_name} settled into its new allegiance with the resignation of a territory that had learned the cost of resistance. The old banners came down. No one replaced them for a long while.", 13, 2, 31 },
    { "CCV_C_003", "With {region_name} secured, the victors turned their attention outward. The momentum of conquest is its own argument, and neighboring powers understood what the new borders implied.", 13, 2, 25 },
    { "CCV_C_004", "Histories written by the victors would call {region_name} a liberation. Histories written by the vanquished would call it something else. The territory itself simply endured, as territories do, under new management.", 13, 2, 30 },
    { "CCV_C_005", "The taking of {region_name} redrew more than borders. It redrew expectations — of what could be held, what could be taken, and how quickly the world's arrangements could be unmade.", 13, 2, 29 },
    { "CCS_O_001", "The conflict in {region_name} settled into a posture that resembled neither war nor peace, only the slow erosion of both sides' willingness to continue.", 15, 0, 24 },
    { "CCS_O_002", "{duration_prose}, the struggle for {region_name} ground on without resolution, each season indistinguishable from the last.", 15, 0, 16 },
    { "CCS_O_003", "In {region_name}, what had begun as decisive action calcified into something worse — a stalemate that consumed resources without producing outcomes.", 15, 0, 20 },
    { "CCS_O_004", "No one could say precisely when the war in {region_name} stopped being fought and began simply being endured.", 15, 0, 18 },
    { "CCS_O_005", "By the time exhaustion replaced ambition in {region_name}, the original aims of the conflict had become difficult to recall with any conviction.", 15, 0, 22 },
    { "CCS_O_006", "The front lines across {region_name} held, though the word suggested a firmness that no one on either side still felt.", 15, 0, 20 },
    { "CCS_D_001", "Skirmishes in {region_name} followed a rhythm that owed more to habit than strategy. Ground was taken and surrendered in the same week, positions traded like debts neither party could afford to settle.", 15, 1, 32 },
    { "CCS_D_002", "{character_name} held command in {region_name} through the worst of the grinding, issuing orders that grew more conservative with each passing month. Victory was no longer discussed; the vocabulary had narrowed to holding and enduring.", 15, 1, 34 },
    { "CCS_D_003", "In {region_name}, the cost accrued quietly and without dramatic incident. The stalemate exacted its toll not in single catastrophes but in the steady, undramatic depletion of everything that sustains a prolonged contest.", 15, 1, 35 },
    { "CCS_D_004", "{faction_name} and its adversaries in {region_name} maintained positions that neither could afford to abandon nor reinforce. Messengers traveled between camps with proposals that arrived already obsolete.", 15, 1, 27 },
    { "CCS_D_005", "The garrison towns of {region_name} adapted to indefinite conflict with the grim practicality of people who have stopped expecting resolution. Markets reopened under guard; children grew up measuring time by which siege was which.", 15, 1, 33 },
    { "CCS_D_006", "Tension across {region_name} remained {tension_level}, though the character of that tension had shifted — less the sharp anticipation of battle than the dull weight of a quarrel no one could finish.", 15, 1, 31 },
    { "CCS_D_007", "{duration_prose}, the forces arrayed across {region_name} exchanged neither decisive blows nor terms. {character_name} reportedly described the situation as a wound that refused to either heal or kill.", 15, 1, 27 },
    { "CCS_D_008", "Supply lines into {region_name} thinned to a trickle, yet the commitments they sustained could not be withdrawn without conceding what months of sacrifice had purchased — which, by most honest reckonings, was very little.", 15, 1, 33 },
    { "CCS_C_001", "The stalemate in {region_name} would not end so much as expire — outlasted by the patience of those who had the least invested in its continuation.", 15, 2, 25 },
    { "CCS_C_002", "What {region_name} needed was a resolution. What it received, instead, was the particular cruelty of a conflict that had forgotten its own purpose but not yet learned how to stop.", 15, 2, 31 },
    { "CCS_C_003", "In {region_name}, the cost of the stalemate would be tallied not in battles lost but in the years spent standing still — years that could not be recovered or repurposed.", 15, 2, 30 },
    { "CCS_C_004", "Neither side in {region_name} would claim the deadlock as a success, though both would eventually claim its end. The truth lay somewhere in the exhausted middle.", 15, 2, 27 },
    { "CCS_C_005", "The unresolved tension in {region_name} settled into the region's foundations like damp into stone. Whatever came next would be built atop it, whether anyone acknowledged that fact or not.", 15, 2, 29 },
    { "CCD_O_001", "The defeat at {region_name} did not come suddenly — it came in stages, each one quieter than the last.", 14, 0, 21 },
    { "CCD_O_002", "In the years that followed the collapse of {region_name}, those who had governed it spoke of the end only in euphemism.", 14, 0, 22 },
    { "CCD_O_003", "What {region_name} had taken generations to build, {duration_prose} of sustained pressure was enough to undo.", 14, 0, 17 },
    { "CCD_O_004", "The chronicles of {region_name} record no single hour of ruin — only the accumulated weight of diminishing returns.", 14, 0, 19 },
    { "CCD_O_005", "A generation after {character_name} last held the lines at {region_name}, the memory of that stand had calcified into myth.", 14, 0, 21 },
    { "CCD_O_006", "The withdrawal from {region_name} was orderly in the official dispatches and catastrophic in every other account that survived.", 14, 0, 19 },
    { "CCD_D_001", "The forces arrayed against {region_name} were not exceptional in number; what distinguished them was patience. They waited until {field_delta_summary}, then moved with deliberate calm.", 14, 1, 27 },
    { "CCD_D_002", "{character_name} had warned that {region_name} could not sustain another season of attrition. The warning was filed and not acted upon. By the time it was vindicated, no one remained to act on it.", 14, 1, 33 },
    { "CCD_D_003", "The population of {region_name} did not resist the new order so much as accommodate it. {field_delta_summary}, and there was little left worth defending with conviction.", 14, 1, 25 },
    { "CCD_D_004", "{faction_name} moved into {region_name} without ceremony. There were no proclamations, no formal transfers of authority — only the gradual replacement of one administration's symbols with another's, and the unspoken understanding that protest would be futile.", 14, 1, 36 },
    { "CCD_D_005", "The garrison at {region_name} held longer than expected. The end came not with a battle but with absence — of supply, of reinforcement, of any sign that relief was possible.", 14, 1, 30 },
    { "CCD_D_006", "Accounts from {region_name} describe a peculiar stillness — the kind that descends when the outcome is known but not yet spoken. {field_delta_summary}, and those with means to leave had already done so.", 14, 1, 32 },
    { "CCD_D_007", "The loss of {region_name} was, by most measures, not a surprise. The pattern had been visible for some time: each concession slightly larger than the last, each line drawn slightly closer to the center.", 14, 1, 36 },
    { "CCD_D_008", "{duration_prose}, the position at {region_name} had been quietly reclassified — from essential to strategic, then strategic to symbolic, then symbolic to untenable.", 14, 1, 22 },
    { "CCD_C_001", "The name of {region_name} would appear in documents for some years — in inventories, in border agreements, in the footnotes of treaties. Eventually, even those mentions ceased.", 14, 2, 27 },
    { "CCD_C_002", "What {region_name} had represented — as buffer, as revenue, as proof of reach — was not easily replaced. The absence reshaped expectations for years to come.", 14, 2, 26 },
    { "CCD_C_003", "{character_name} did not speak publicly of {region_name} again. Whether this was grief, or prudence, or simply the habit of those who have outlived the causes they served, the record does not say.", 14, 2, 34 },
    { "CCD_C_004", "The lesson drawn from {region_name} differed depending on who was drawing it. For some, it was a case study in overextension. For others, in betrayal. The disagreement outlasted the loss itself.", 14, 2, 32 },
    { "CCD_C_005", "History would record the fall of {region_name} in a single sentence. Those who had been present understood, without needing to explain it to anyone, why that sentence was insufficient.", 14, 2, 30 },
    { "CRS_O_001", "What fractured {region_name} in those years was not conquest from without, but the slow, irreconcilable divergence of belief within.", 10, 0, 26 },
    { "CRS_O_002", "{faction_name} had governed {region_name} for a generation before the ideology that built them began to consume them.", 10, 0, 22 },
    { "CRS_O_003", "In the season that {event_description} came to pass in {region_name}, no wall fell — yet everything was broken.", 10, 0, 21 },
    { "CRS_O_004", "The rupture in {region_name} announced itself not with fire, but with silence — old allies ceasing, overnight, to speak the same language.", 10, 0, 26 },
    { "CRS_O_005", "There had been warnings in {region_name} long before the break came — dissenters dismissed, grievances filed away, tension left to ferment.", 10, 0, 27 },
    { "CRS_O_006", "Generations of historians have traced the dissolution of {region_name}'s internal order to a single, unresolved question of legitimacy.", 10, 0, 22 },
    { "CRS_D_001", "{character_name} had not set out to lead a revolt. The record suggests a man — or woman — driven past patience by {tension_level} tension that the administration of {region_name} neither acknowledged nor addressed.", 10, 1, 36 },
    { "CRS_D_002", "{faction_name}'s split in {region_name} was not merely political. It was doctrinal — two readings of the same foundational compact, each convinced the other had betrayed it, neither willing to concede the original text's ambiguity.", 10, 1, 40 },
    { "CRS_D_003", "What records survive from {region_name} describe {field_delta_summary} — not as consequence of the revolt, but as its cause. Deprivation had made the theoretical feel urgent and the moderate feel cowardly.", 10, 1, 36 },
    { "CRS_D_004", "The commanders who remained loyal to {faction_name} in {region_name} were, by most accounts, sincerely loyal — and sincerely unable to comprehend how their sincerity had become indistinguishable from complicity.", 10, 1, 33 },
    { "CRS_D_005", "{character_name}'s influence in {region_name} had rested on the assumption that the center would hold. When it did not, the moderate ground was swallowed by the fracture itself.", 10, 1, 27 },
    { "CRS_D_006", "The circulars passed between cells in {region_name} were remarkable less for their radicalism than for their grief — written by people who had once believed in the order they now meant to end.", 10, 1, 33 },
    { "CRS_D_007", "By the time {event_description} had fully run its course through {region_name}, the vocabulary of governance had itself become contested — the same words meaning opposite things depending on who spoke them and where.", 10, 1, 35 },
    { "CRS_D_008", "The {tension_level} tensions that preceded the break in {region_name} had been visible to any observer willing to look. That so few looked remains the most damning fact of the period.", 10, 1, 33 },
    { "CRS_C_001", "{region_name} recovered, in time, the outward forms of order. The underlying fracture was papered over rather than healed, and those who remembered what had been believed — on both sides — did not forgive.", 10, 2, 37 },
    { "CRS_C_002", "The chroniclers of {region_name} were left with the uncomfortable task of explaining how people of evident conviction had arrived at such irreconcilable conclusions from the same inherited principles.", 10, 2, 30 },
    { "CRS_C_003", "What endured in {region_name} was not the faction that prevailed, nor even the ideology it carried — but the habit of suspicion, passed quietly from one generation to the next.", 10, 2, 33 },
    { "CRS_C_004", "{field_delta_summary} in the aftermath, and {region_name} wore its new quietude the way a city wears the silence after a fire — grateful, but altered in ways that would not show for years.", 10, 2, 36 },
    { "CRS_C_005", "The revolt in {region_name} produced no heroes either side could cleanly claim — only survivors, each carrying a private account of how things had gone wrong.", 10, 2, 26 },
    { "CE_O_001", "In the years following the settlement of {region_name}, the first cautious signs of lasting order began to take root.", 11, 0, 21 },
    { "CE_O_002", "A generation after {faction_name} extended its reach into {region_name}, the land had begun to answer back with unexpected generosity.", 11, 0, 22 },
    { "CE_O_003", "What had begun as a frontier venture in {region_name} slowly revealed itself, over {duration_prose}, to be something more enduring.", 11, 0, 21 },
    { "CE_O_004", "The chronicles of {region_name} from this period carry a tone rarely found in older annals — measured hope, held carefully.", 11, 0, 22 },
    { "CE_O_005", "Those who first pushed into {region_name} did not expect to stay; their descendants would not understand why anyone had ever considered leaving.", 11, 0, 24 },
    { "CE_O_006", "In the long interval between crisis and consolidation, {region_name} entered a season of tentative but unmistakable growth.", 11, 0, 18 },
    { "CE_D_001", "Roads that had once served only the movement of soldiers began carrying grain and timber outward from {region_name} toward {adjacent_region}, and the traffic did not stop.", 11, 1, 29 },
    { "CE_D_002", "{faction_name} administrators in {region_name} were cautious men by training, and cautious men, when given stable ground, tend to build carefully and build well.", 11, 1, 28 },
    { "CE_D_003", "Settlers arrived in {region_name} not in great waves but in a steady flow — families and tradespeople who had heard reliable reports and found them, on the whole, accurate.", 11, 1, 29 },
    { "CE_D_004", "The capacity of {region_name} to sustain its new population had been {capacity_level} by early reckoning, and the years proved that estimate neither optimistic nor wrong — only incomplete.", 11, 1, 30 },
    { "CE_D_005", "What the surveyors recorded as marginal land was revealed, through patient labor, to be something richer. {field_delta_summary} across {region_name} in this period, and the balance of confidence shifted with it.", 11, 1, 33 },
    { "CE_D_006", "The connection between {region_name} and {adjacent_region} deepened gradually — first through necessity, then through habit, and finally through something that functioned, if not in law then in practice, like mutual interest.", 11, 1, 33 },
    { "CE_D_007", "The expansion of {region_name} was accomplished, over {duration_prose}, without the grand gestures of conquest — only the slow accumulation of small decisions, each defensible on its own terms.", 11, 1, 31 },
    { "CE_D_008", "{faction_name} held {region_name} not through force of arms in this period but through the more durable grip of usefulness — supplying what neighboring territories could not easily produce themselves.", 11, 1, 31 },
    { "CE_C_001", "Whether this prosperity would endure remained, for the careful observer, an open question. But the foundations laid in {region_name} during these years would prove harder to undo than anyone then anticipated.", 11, 2, 34 },
    { "CE_C_002", "The progress of {region_name} was never inevitable — those who built it knew this better than the historians who later described it as such. That knowledge was, perhaps, the source of its strength.", 11, 2, 36 },
    { "CE_C_003", "{field_delta_summary} — and with it, the expectations of what {region_name} might yet become quietly expanded beyond what its founders had dared to record in writing.", 11, 2, 27 },
    { "CE_C_004", "The eyes of {adjacent_region} turned toward {region_name} in this period not with appetite but with something closer to study, as if reconsidering what the future might reasonably contain.", 11, 2, 31 },
    { "CE_C_005", "What {region_name} had been at the start of this account and what it was at the close were separated not by catastrophe but by the quieter distance of accumulated effort.", 11, 2, 32 },
    { "CC_O_001", "The troubles of {region_name} did not arrive in sequence, as troubles are supposed to — they arrived together, and all at once.", 12, 0, 24 },
    { "CC_O_002", "What the chroniclers of {region_name} struggled most to convey was not any single calamity but the suffocating simultaneity of them all.", 12, 0, 22 },
    { "CC_O_003", "In the period following {event_description}, {region_name} entered a span of compounding disorder that no single account has ever fully untangled.", 12, 0, 22 },
    { "CC_O_004", "The administrators of {region_name} were not incompetent men — they were simply faced, {duration_prose}, with more than administration was ever designed to hold.", 12, 0, 26 },
    { "CC_O_005", "Later generations would look back at {region_name} in this era and search for the moment things began to unravel; they never agreed on one.", 12, 0, 27 },
    { "CC_O_006", "The tension in {region_name} had been building for long enough that when it finally broke, it broke in several directions at once.", 12, 0, 23 },
    { "CC_D_001", "The {event_description} had not yet resolved when new pressures announced themselves in {region_name} — first at the borders, then in the granaries, then in the streets. Each demanded priority. None would wait.", 12, 1, 34 },
    { "CC_D_002", "The tension across {region_name} had reached {tension_level} by any measure available to its governors, and {field_delta_summary} — a combination that left little room for the careful response the situation technically required.", 12, 1, 33 },
    { "CC_D_003", "Dispatches from {region_name} during this period share a common quality of exhaustion — not the exhaustion of men who have fought hard, but of men who cannot identify which fight is the one that matters.", 12, 1, 37 },
    { "CC_D_004", "What had begun as {event_description} in {region_name} extended its consequences outward. Each response spawned a new requirement, and each arrived before the last had been met.", 12, 1, 26 },
    { "CC_D_005", "{field_delta_summary} across {region_name}, and the instability this produced was not the clean instability of a single fracture but the grinding, directionless kind that comes from too many things failing at once.", 12, 1, 33 },
    { "CC_D_006", "The chain of events that consumed {region_name} in this period numbered, by later count, {chain_length} distinct crises — each real, each pressing, and each drawing resources and attention away from all the others.", 12, 1, 35 },
    { "CC_D_007", "There was no shortage of capable men in {region_name}. There was a shortage of hours, of messengers who arrived before decisions had already aged past usefulness, of quiet in which to think.", 12, 1, 34 },
    { "CC_D_008", "The factional tension within {region_name} had reached {tension_level}, and what might have been manageable in isolation became, amid the wider disorder, something closer to a slow collapse of the ordinary compact between governed and governor.", 12, 1, 38 },
    { "CC_C_001", "The record of {region_name} from these years is incomplete not because the scribes were negligent but because events outpaced the capacity of any one account to follow them. Some things were simply never written down.", 12, 2, 37 },
    { "CC_C_002", "That {region_name} emerged from this period at all is, on reflection, the more remarkable fact. The forces arrayed against its continuity were not small, and they did not act one at a time.", 12, 2, 35 },
    { "CC_C_003", "{field_delta_summary} — and with that, whatever remained of confidence in the governing order of {region_name} quietly withdrew from public expression, surviving only in private correspondence and careful silences.", 12, 2, 30 },
    { "CC_C_004", "The weight of this era on {region_name} was not the weight of a single blow but of accumulated pressure — the kind that does not break things cleanly but leaves them permanently misaligned.", 12, 2, 34 },
    { "CC_C_005", "Those who had administered {region_name} through {duration_prose} of compound crisis aged, it was said, as men age in war — not by years but by the specific weight of unresolvable things.", 12, 2, 34 },
    { "RD_O_001", "The decline of {region_name} was not the kind that announces itself — it was the kind that is noticed only after it is complete.", 22, 0, 29 },
    { "RD_O_002", "{duration_prose}, the condition of {region_name} worsened by increments too small for any single season's record to capture.", 22, 0, 21 },
    { "RD_O_003", "Those who had known {region_name} in better times returned to find it not ruined, exactly, but diminished — as a fire is diminished when the wood runs low.", 22, 0, 32 },
    { "RD_O_004", "In the long years that followed, {region_name} continued to exist — continued, even, to function — but something essential had quietly left it.", 22, 0, 27 },
    { "RD_O_005", "The historians who later wrote of {region_name}'s contraction struggled to name a turning point, because there had been none — only the accumulation of small surrenders.", 22, 0, 29 },
    { "RD_O_006", "A generation passed before the people of {region_name} allowed themselves the word they had long been avoiding.", 22, 0, 19 },
    { "RD_D_001", "The roads of {region_name} were the first to show it — maintained, then merely passable, then quietly abandoned to the encroachment of grass and mud. No edict marked the change. It simply happened.", 22, 1, 36 },
    { "RD_D_002", "{field_delta_summary} across {region_name}, and the administrative apparatus that had once managed the region's affairs grew thinner with each cycle of appointments — posts left vacant, correspondence unanswered, decisions deferred until they ceased to matter.", 22, 1, 38 },
    { "RD_D_003", "The {stability_level} stability that characterized {region_name} in those years was not the stability of strength but of exhaustion — a population too depleted by prior hardship to mount either resistance or renewal.", 22, 1, 35 },
    { "RD_D_004", "Craftsmen left {region_name} first, drawn by steadier commissions. Merchants followed, then minor officials. What remained was not a community in crisis but one slowly becoming smaller.", 22, 1, 26 },
    { "RD_D_005", "The {capacity_level} capacity that defined {region_name}'s productive life had not been destroyed by any single event — it had been borrowed against, season after season, until the borrowing outpaced any hope of repayment.", 22, 1, 36 },
    { "RD_D_006", "Surveying records from {region_name} during the period document the same pattern in village after village: fields contracted at the margins, orchards unpruned, irrigation channels silting without being cleared. The center held while the edges retreated.", 22, 1, 37 },
    { "RD_D_007", "There were, in {region_name}, men and women who saw clearly what was happening and said so — in petitions, in sermons, in letters that went unreturned. Their clarity changed nothing. It rarely does.", 22, 1, 35 },
    { "RD_D_008", "{duration_prose}, the population of {region_name} contracted — not through catastrophe but through the quiet arithmetic of departures exceeding arrivals, births failing to replace deaths, and a general sense that the future lay elsewhere.", 22, 1, 36 },
    { "RD_C_001", "{region_name} did not vanish from the maps. It persisted, hollowed, recognizable in outline but no longer in substance — the name outlasting the thing it had named.", 22, 2, 30 },
    { "RD_C_002", "What the era left behind in {region_name} was not ruin but irrelevance — and irrelevance, the chronicles suggest, was the harder condition to recover from.", 22, 2, 26 },
    { "RD_C_003", "The people who remained in {region_name} were not, by any account, without dignity. They had simply inherited a situation that no amount of dignity could fully redress.", 22, 2, 31 },
    { "RD_C_004", "Later administrations would attempt revivals of {region_name} — some earnest, some merely rhetorical. None recovered what the long erosion had taken, because erosion does not leave the original shape intact beneath its work.", 22, 2, 35 },
    { "RD_C_005", "The {stability_level} condition of {region_name} at the close of the period was, in its way, a kind of stability — the stability of a thing that has finished falling and lies where it landed.", 22, 2, 38 },
    { "RG_O_001", "The progress of {region_name} in this period was not the kind that announces itself — it was the kind that is noticed only in retrospect.", 21, 0, 27 },
    { "RG_O_002", "In the years that followed, {region_name} did what stable ground eventually does — it began, without ceremony, to produce.", 21, 0, 20 },
    { "RG_O_003", "Over {duration_prose}, the slow work of building gathered in {region_name} into something that could no longer be called tentative.", 21, 0, 20 },
    { "RG_O_004", "The annals of {region_name} from this era record no great battles, no sudden reversals — only the unhurried accumulation of well-made decisions.", 21, 0, 24 },
    { "RG_O_005", "A generation passed quietly over {region_name}, and when it lifted, the land beneath was measurably different from the land it had covered.", 21, 0, 24 },
    { "RG_O_006", "Those who governed {region_name} through this period left behind no celebrated edicts — only the evidence of their work, which outlasted the records of their names.", 21, 0, 28 },
    { "RG_D_001", "The capacity of {region_name} had reached {capacity_level} — not through any single investment but through patient repair of what had been neglected and quiet extension of what had proven sound.", 21, 1, 30 },
    { "RG_D_002", "{field_delta_summary} across {region_name}, and with it came the particular confidence of people who have watched their labor compound — not dramatically, but reliably, season after season.", 21, 1, 29 },
    { "RG_D_003", "The stability of {region_name} held at {stability_level} through this span, and that steadiness proved its own reward: investment that had waited for calmer conditions began, at last, to arrive.", 21, 1, 31 },
    { "RG_D_004", "The workshops and waterways of {region_name} expanded without fanfare, each addition following from the last with the logic of a structure built by people who intended to use it themselves.", 21, 1, 32 },
    { "RG_D_005", "What {region_name} required above all else was time undisturbed, and {duration_prose} it received that rare gift. The effects were not spectacular. They were, instead, durable.", 21, 1, 28 },
    { "RG_D_006", "The population of {region_name} grew slowly and settled well — not the restless growth of a frontier but the consolidating kind, where people build as though they plan to remain.", 21, 1, 32 },
    { "RG_D_007", "The fields and storehouses of {region_name} did not overflow, but they did not fall short either. That equilibrium, modest as it sounds, was the foundation on which everything else in this period was built.", 21, 1, 36 },
    { "RG_D_008", "{field_delta_summary} in {region_name}, steadily and without the reversals of earlier decades. Those who lived through it mostly did not remark upon it — the surest sign of success.", 21, 1, 28 },
    { "RG_C_001", "The quiet growth of {region_name} in these years would not find its way into songs or speeches. It would find its way, instead, into the improved circumstances of those who came after.", 21, 2, 34 },
    { "RG_C_002", "The capacity built in {region_name} during this period would prove, in the crises that followed, to be neither excess nor luxury — only the margin that made recovery possible.", 21, 2, 31 },
    { "RG_C_003", "That {region_name} had grown stronger was, by the end of this period, beyond dispute. That it had done so without drawing attention to itself was, perhaps, the greatest part of the achievement.", 21, 2, 35 },
    { "RG_C_004", "The stability of {region_name} at {stability_level} was not the stasis of a place that had stopped moving — it was the balance of a place that had learned how to move without stumbling.", 21, 2, 36 },
    { "RG_C_005", "There are eras that teach through catastrophe and eras that teach through example. {region_name} in this period was the latter kind, and its lessons were all the more lasting for being unforced.", 21, 2, 34 },
    { "RS_O_001", "For much of this period, {region_name} presented little of note to those keeping the broader record.", 23, 0, 17 },
    { "RS_O_002", "The affairs of {region_name} during these years were, by most accounts, unremarkable.", 23, 0, 13 },
    { "RS_O_003", "{duration_prose}, {region_name} continued largely as it had — administered, taxed, and otherwise undisturbed.", 23, 0, 14 },
    { "RS_O_004", "The chronicles of {region_name} offer little drama for this stretch — which is, in its own way, a kind of record.", 23, 0, 22 },
    { "RS_O_005", "In the years that concern us here, {region_name} remained {stability_level} and largely outside the current of larger events.", 23, 0, 19 },
    { "RS_O_006", "A generation passed in {region_name} without incident sufficient to warrant more than routine notation.", 23, 0, 14 },
    { "RS_D_001", "Harvests in {region_name} were adequate. The administrative rolls show no unusual levies, no recorded disputes of consequence, no petitions that reached higher authority.", 23, 1, 25 },
    { "RS_D_002", "The condition of {region_name} during this period is best described as {stability_level}. Roads were maintained, obligations met, and the succession of local officials passed without disruption.", 23, 1, 29 },
    { "RS_D_003", "Trade moved through {region_name} at its customary pace. The ledgers from this era show neither the surpluses of a prosperous season nor the shortfalls that might prompt inquiry from above.", 23, 1, 32 },
    { "RS_D_004", "There is little in the surviving record to distinguish one year from the next in {region_name} during this time. The region endured — competently, quietly, without distinction.", 23, 1, 29 },
    { "RS_D_005", "{region_name} appears in the dispatch records of this period only in inventory summaries and routine census figures. No military movements were logged. No factional complaints were forwarded.", 23, 1, 28 },
    { "RS_D_006", "The stability of {region_name} was not celebrated — it was simply expected. {duration_prose}, that expectation was met without notable exception.", 23, 1, 21 },
    { "RS_D_007", "Local governance in {region_name} functioned within its ordinary tolerances. Disputes were resolved at the local level; appeals to higher authority were rare and, when made, largely procedural.", 23, 1, 30 },
    { "RS_D_008", "The population of {region_name} neither grew nor contracted with any urgency in this period. Movement in and out of the region followed seasonal patterns and left no structural mark on the record.", 23, 1, 33 },
    { "RS_C_001", "In this, {region_name} was useful — not as a subject of history, but as a foundation beneath it.", 23, 2, 18 },
    { "RS_C_002", "The quiet of {region_name} during these years would not last indefinitely, but while it held, it required nothing and asked for nothing in return.", 23, 2, 25 },
    { "RS_C_003", "Regions like {region_name} do not often appear in the histories written afterward. Their contribution was the negative space — the absence of crisis that allowed attention to be directed elsewhere.", 23, 2, 31 },
    { "RS_C_004", "What {region_name} offered during this period was continuity. Whether that continuity would prove a foundation or merely a pause remained, for now, an open question.", 23, 2, 27 },
    { "RS_C_005", "The record of {region_name} for these years closes without ceremony — as it opened, and as it was conducted throughout.", 23, 2, 20 },
    { "RFS_O_001", "The old arrangements in {region_name} did not collapse — they were replaced, carefully and without apology, by those who had grown tired of waiting for permission.", 20, 0, 28 },
    { "RFS_O_002", "In the years that reshaped {region_name}, the question was never whether power would change hands but only which hands would receive it and on what terms.", 20, 0, 28 },
    { "RFS_O_003", "The political settlement of {region_name} that had held for a generation gave way, over {duration_prose}, to one that bore almost no resemblance to its predecessor.", 20, 0, 27 },
    { "RFS_O_004", "What {faction_name} accomplished in {region_name} during this period was less a conquest than a reorganization — the same territory, different loyalties, different logic.", 20, 0, 26 },
    { "RFS_O_005", "A new order settled over {region_name} in these years, and those who had prospered under the previous one learned, at varying speeds, to adapt or diminish.", 20, 0, 28 },
    { "RFS_O_006", "The realignment of {region_name} was remembered differently by those who gained from it and those who did not — as it always is.", 20, 0, 24 },
    { "RFS_D_001", "{faction_name} moved carefully in {region_name}, replacing key appointments before announcing any broader intention. By the time the shift was publicly visible, it had already been accomplished in every practical sense.", 20, 1, 33 },
    { "RFS_D_002", "{character_name} became the recognizable face of the new arrangement in {region_name} — present at the right moments, absent from the awkward ones, and careful never to say more than the situation required.", 20, 1, 34 },
    { "RFS_D_003", "The transition of authority in {region_name} was conducted, by the standards of such things, with restraint. Old obligations were discharged; new ones were incurred. The exchange was transactional in form, if not always in spirit.", 20, 1, 36 },
    { "RFS_D_004", "{field_delta_summary} across {region_name} as the political order shifted — a pattern familiar to those who had watched such transitions before. Resources follow power; power follows will; and will, in this case, belonged to the newcomers.", 20, 1, 37 },
    { "RFS_D_005", "{faction_name} did not govern {region_name} as it had governed elsewhere. The region had particular loyalties and grievances, and those who managed it wisely attended to them.", 20, 1, 26 },
    { "RFS_D_006", "The families that had defined {region_name}'s political life for decades found themselves, not dispossessed exactly, but repositioned — consulted rather than commanding, accommodated rather than deferred to.", 20, 1, 28 },
    { "RFS_D_007", "{character_name} understood that {region_name} could not simply be administered from outside — it had to be persuaded, and persuasion required concessions that pure authority would never have offered.", 20, 1, 30 },
    { "RFS_D_008", "The new order in {region_name} announced itself not through proclamation but through the replacement of small courtesies — who was greeted first, whose name appeared in which documents, who sat where at formal gatherings.", 20, 1, 36 },
    { "RFS_C_001", "Whether the new arrangement in {region_name} was better than the one it replaced depended, as such judgments usually do, entirely on where one had stood in the arrangement it replaced.", 20, 2, 33 },
    { "RFS_C_002", "{faction_name} had remade {region_name} in its own image — or close enough that the difference would only become apparent to those who lived there long enough to notice what had quietly vanished.", 20, 2, 35 },
    { "RFS_C_003", "{field_delta_summary} in the years following the transition — a practical measure of how thoroughly the new order had taken hold in {region_name}, and how little appetite remained for reversing it.", 20, 2, 32 },
    { "RFS_C_004", "The political life of {region_name} had been remade, and those who would shape its next chapter would do so from within a framework they had not designed and could not entirely see.", 20, 2, 35 },
    { "RFS_C_005", "What {region_name} had been before remained visible — in the architecture, in the surnames, in the older forms of address. But the center had moved.", 20, 2, 25 },
    { "CS_O_001", "What followed {mission_outcome} at {mission_region} was not fortune — it was consequence, arriving precisely where the effort had been directed.", 30, 0, 23 },
    { "CS_O_002", "The accounts of {mission_outcome} reached the capital before the dust had settled, and with them came the first serious reappraisal of {lineage_name} household's standing.", 30, 0, 30 },
    { "CS_O_003", "In the months that followed {mission_outcome}, the shape of things in {mission_region} began, quietly and then unmistakably, to change.", 30, 0, 24 },
    { "CS_O_004", "{mission_outcome} was, by any measure, the turning point — the moment at which effort and circumstance converged into something irreversible.", 30, 0, 22 },
    { "CS_O_005", "The records are unusually clear on the matter: {mission_outcome} produced effects that could be traced, named, and attributed without ambiguity.", 30, 0, 23 },
    { "CS_O_006", "{duration_prose} after {mission_outcome}, the changes that had seemed merely possible had become, one by one, actual.", 30, 0, 19 },
    { "CS_D_001", "{character_name} had staked considerable reputation on the {mission_archetype} that ended in {mission_outcome}. The vindication was not merely personal — it restructured the assumptions of every commander who had counseled against the attempt.", 30, 1, 35 },
    { "CS_D_002", "The {mission_archetype} had been called reckless by those who did not understand it and unnecessary by those who feared what success would demand of them. {mission_outcome} answered both objections in the same stroke.", 30, 1, 36 },
    { "CS_D_003", "{field_delta_summary} in the wake of {mission_outcome} — not as incidental benefit but as the direct yield of what had been done at {mission_region}. The connection was apparent to anyone reviewing the sequence of events.", 30, 1, 38 },
    { "CS_D_004", "{lineage_name} name appeared in the official dispatches describing {mission_outcome} with a frequency that did not go unnoticed. Credit, in such matters, tends to consolidate around those who have earned the right to it.", 30, 1, 37 },
    { "CS_D_005", "What {mission_outcome} secured in {mission_region} was not simply territory — it was the proof of a method that could not easily be dismissed or forgotten.", 30, 1, 25 },
    { "CS_D_006", "The population of {mission_region} registered {mission_outcome} in practical terms before the political class finished debating. Supply lines reopened. Markets resumed.", 30, 1, 20 },
    { "CS_D_007", "{character_name} received no formal decoration for the {mission_archetype} that produced {mission_outcome}. The altered conditions it left behind were, by most accounts, decoration enough.", 30, 1, 28 },
    { "CS_D_008", "{lineage_name} household's involvement in the events leading to {mission_outcome} was documented carefully — by allies wishing to associate themselves with the result, and by rivals seeking to understand how it had been achieved.", 30, 1, 36 },
    { "CS_C_001", "{mission_outcome} did not close the matter — it opened a larger one. But it opened it from a position of strength, which is the only position worth occupying when the larger matter arrives.", 30, 2, 36 },
    { "CS_C_002", "{lineage_name} household had, by the close of the period, made itself difficult to ignore. {mission_outcome} was not the whole of the reason — but it was the clearest part of it.", 30, 2, 36 },
    { "CS_C_003", "What had been risked in pursuit of {mission_outcome} was considerable. What had been returned was more. The ledger, for once, balanced in the right direction.", 30, 2, 29 },
    { "CS_C_004", "{field_delta_summary} — and the chroniclers who recorded it were careful to trace the line back to {mission_outcome}, because the line was straight and the evidence was plain.", 30, 2, 31 },
    { "CS_C_005", "{mission_outcome} did not guarantee a future — but it made several futures possible that had not been possible before, and that is the more honest measure.", 30, 2, 26 },
    { "CF_O_001", "What had been attempted at {mission_region} ended as {mission_outcome}, and the reckoning that followed was neither swift nor merciful.", 31, 0, 21 },
    { "CF_O_002", "The {mission_archetype} concluded as {mission_outcome} — a result that demanded explanation from those who had authorized it.", 31, 0, 17 },
    { "CF_O_003", "In the weeks that followed {mission_outcome}, {lineage_name} household found itself answering for decisions made under very different expectations.", 31, 0, 21 },
    { "CF_O_004", "The outcome at {mission_region} was recorded as {mission_outcome}, and no subsequent account has found reason to soften that assessment.", 31, 0, 21 },
    { "CF_O_005", "{duration_prose} after {mission_outcome}, the full weight of what had been lost was still being measured.", 31, 0, 16 },
    { "CF_O_006", "Those who commissioned the {mission_archetype} had not prepared for {mission_outcome}, and it showed in everything that came after.", 31, 0, 19 },
    { "CF_D_001", "The {mission_archetype} at {mission_region} had required considerable outlay — in material, in lives, in the credibility of those who had staked their judgment on a different result. {mission_outcome} erased that investment without ceremony.", 31, 1, 34 },
    { "CF_D_002", "{character_name} bore most of the formal responsibility for {mission_outcome}. Whether that attribution was just is a matter the record leaves unresolved, though it did not leave {character_name}'s standing unaffected.", 31, 1, 31 },
    { "CF_D_003", "The consequences of {mission_outcome} were not confined to {mission_region}. {field_delta_summary} in the months that followed, tracing a line of damage that extended well beyond the original theater of effort.", 31, 1, 32 },
    { "CF_D_004", "Internally, {mission_outcome} produced the kind of silence that precedes reorganization. Reports were reviewed, assignments reassigned, and certain names that had appeared prominently in planning documents began to appear less prominently in subsequent ones.", 31, 1, 33 },
    { "CF_D_005", "{lineage_name} name had been attached to the {mission_archetype} from its earliest stages. {mission_outcome} did not sever that attachment — if anything, it made the association more durable, and less flattering.", 31, 1, 33 },
    { "CF_D_006", "At {mission_region}, the gap between the anticipated result and {mission_outcome} was wide enough that misfortune alone could not account for it. The assessments that followed were unsparing.", 31, 1, 27 },
    { "CF_D_007", "{field_delta_summary} in the aftermath of {mission_outcome}. Those who had projected otherwise were not disciplined for optimism — optimism, after all, had been the official posture — but they were not consulted again on comparable matters.", 31, 1, 37 },
    { "CF_D_008", "The dispatches from {mission_region} following {mission_outcome} were terse and factual in the way that dispatches become when there is nothing left to manage impressions of.", 31, 1, 28 },
    { "CF_C_001", "{mission_outcome} was not forgotten quickly. It became instead a reference point — the kind that gets invoked in later arguments without needing explanation, because everyone present already knows what it cost.", 31, 2, 32 },
    { "CF_C_002", "What {mission_outcome} ultimately produced was a revision — of expectations, of alliances, of the confidence with which certain kinds of action would be proposed in the future.", 31, 2, 28 },
    { "CF_C_003", "{character_name} would not hold the same position again. {mission_outcome} had made certain of that, whatever the official accounting eventually said.", 31, 2, 23 },
    { "CF_C_004", "{lineage_name} household absorbed {mission_outcome} without public rupture. The private accounting was another matter, and its effects would surface in decisions made {duration_prose} later, when circumstances allowed for correction.", 31, 2, 31 },
    { "CF_C_005", "History does not always offer clean lessons, but {mission_outcome} at {mission_region} offered one clearly enough: the distance between intention and result is not bridged by confidence alone.", 31, 2, 29 },
    { "CM_O_001", "The chronicles of {mission_region} record {mission_outcome}, though the men who survived it rarely spoke of victory.", 32, 0, 18 },
    { "CM_O_002", "What history would later name {mission_outcome} cost {lineage_name} more than the ledgers ever captured.", 32, 0, 16 },
    { "CM_O_003", "In the months after {mission_outcome} was declared at {mission_region}, the grief arrived on a slower schedule than the celebration.", 32, 0, 21 },
    { "CM_O_004", "{duration_prose}, the campaign at {mission_region} ground toward what the dispatches would call {mission_outcome} — a conclusion that satisfied no one completely.", 32, 0, 24 },
    { "CM_O_005", "{lineage_name} household received news of {mission_outcome} with the particular silence that accompanies results too tangled to celebrate.", 32, 0, 20 },
    { "CM_O_006", "Later generations would argue endlessly about the meaning of {mission_outcome}, each reading the same record and arriving at opposite conclusions.", 32, 0, 21 },
    { "CM_D_001", "What had been intended as {mission_outcome} instead became something harder to name — not failure, not triumph, but the kind of result that reshaped {mission_region} without satisfying anyone.", 32, 1, 28 },
    { "CM_D_002", "{character_name} returned from {mission_region} carrying the honors appropriate to {mission_outcome} and a reserve about the whole affair that deepened with every retelling. Those who asked direct questions received careful answers.", 32, 1, 33 },
    { "CM_D_003", "{character_name}'s campaign yielded {mission_outcome}, though the word 'yielded' perhaps overstated the certainty of it — the consequences would take a generation to fully understand.", 32, 1, 25 },
    { "CM_D_004", "{field_delta_summary} — that much was undeniable. Whether this represented the cost of {mission_outcome} or its substance was a question the court historians debated for years without consensus.", 32, 1, 30 },
    { "CM_D_005", "{lineage_name} had pressed hard for {mission_outcome}, and the record shows they received it. What the record does not show is what {character_name} said to the household in private, on the night the dispatches arrived.", 32, 1, 38 },
    { "CM_D_006", "At {mission_region}, the terms of {mission_outcome} were ratified under a sky that offered no comment. The people who had lived through the campaign signed where they were told to sign.", 32, 1, 32 },
    { "CM_D_007", "In {mission_region}, what the commanders called {mission_outcome} looked rather different to those who lived through it, {lineage_name} household among them.", 32, 1, 21 },
    { "CM_D_008", "The official account of {mission_outcome} omitted the auxiliary losses and the promise {character_name} had made before the campaign — a promise circumstances had made impossible to keep.", 32, 1, 27 },
    { "CM_C_001", "History would not resolve the question of whether {mission_outcome} was worth its cost. It rarely does, for campaigns whose wounds and gains arrive in equal measure.", 32, 2, 28 },
    { "CM_C_002", "Whether {mission_outcome} had been worth the cost was a question {lineage_name} family would debate for generations.", 32, 2, 17 },
    { "CM_C_003", "The ledger of {mission_outcome} balanced only if one squinted — and {lineage_name} name was written on both sides.", 32, 2, 19 },
    { "CM_C_004", "The generation that came after accepted {mission_outcome} as inheritance — the debts and the gains both, without the memory of choosing either.", 32, 2, 22 },
    { "CM_C_005", "History would record {mission_outcome}, though history, as always, would leave out the parts that mattered most to those who lived it.", 32, 2, 21 },
};
/* end constants-table */
#define CHRON_N_FRAGMENTS 380
/* Dense fragment-pool index (0..19) -> sparse category id, in the order the
 * launch library's 20 pools are reported through
 * om_chronicle_fragment_category_count/fragment_pool_counts (S-071). */
static const uint32_t CHRON_DENSE_TO_SPARSE[OM_CHRON_N_CATEGORIES] = {
    CAT_LINEAGE_SUCCESSION, CAT_LINEAGE_MILITARY_ACTION, CAT_LINEAGE_THRIVED,
    CAT_LINEAGE_SUFFERED, CAT_LINEAGE_QUIET,
    CAT_CHAIN_REVOLT_SPAWNED, CAT_CHAIN_EXPANSION, CAT_CHAIN_CASCADE,
    CAT_CHAIN_CONFLICT_VICTORY, CAT_CHAIN_CONFLICT_DEFEAT,
    CAT_CHAIN_CONFLICT_STALEMATE, CAT_CHAIN_CRISIS_RESOLVED_WELL,
    CAT_CHAIN_CRISIS_RESOLVED_BADLY,
    CAT_REGIONAL_FACTION_SHIFT, CAT_REGIONAL_GROWTH, CAT_REGIONAL_DECLINE,
    CAT_REGIONAL_STABLE,
    CAT_CONSEQUENCE_SUCCESS, CAT_CONSEQUENCE_FAILURE, CAT_CONSEQUENCE_MIXED,
};

static const char *chron_category_name(uint32_t category) {
    switch (category) {
    case CAT_LINEAGE_SUCCESSION: return "lineage_succession";
    case CAT_LINEAGE_MILITARY_ACTION: return "lineage_military_action";
    case CAT_LINEAGE_THRIVED: return "lineage_thrived";
    case CAT_LINEAGE_SUFFERED: return "lineage_suffered";
    case CAT_LINEAGE_QUIET: return "lineage_quiet";
    case CAT_CHAIN_REVOLT_SPAWNED: return "chain_revolt_spawned";
    case CAT_CHAIN_EXPANSION: return "chain_expansion";
    case CAT_CHAIN_CASCADE: return "chain_cascade";
    case CAT_CHAIN_CONFLICT_VICTORY: return "chain_conflict_victory";
    case CAT_CHAIN_CONFLICT_DEFEAT: return "chain_conflict_defeat";
    case CAT_CHAIN_CONFLICT_STALEMATE: return "chain_conflict_stalemate";
    case CAT_CHAIN_CRISIS_RESOLVED_WELL: return "chain_crisis_resolved_well";
    case CAT_CHAIN_CRISIS_RESOLVED_BADLY: return "chain_crisis_resolved_badly";
    case CAT_REGIONAL_FACTION_SHIFT: return "regional_faction_shift";
    case CAT_REGIONAL_GROWTH: return "regional_growth";
    case CAT_REGIONAL_DECLINE: return "regional_decline";
    case CAT_REGIONAL_STABLE: return "regional_stable";
    case CAT_CONSEQUENCE_SUCCESS: return "consequence_success";
    case CAT_CONSEQUENCE_FAILURE: return "consequence_failure";
    case CAT_CONSEQUENCE_MIXED: return "consequence_mixed";
case CAT_CONSEQUENCE_RIPPLE: return "consequence_ripple";
    default: return "unknown";
    }
}

/* ---- per-world state (w->chronicle_state / w->chronicle_state_free) ---- */

typedef struct {
    int32_t chain_tag;
    uint32_t region;
    uint32_t category;
} chron_raw_chain_event;

typedef struct {
    uint32_t id;
    char text[512];
    int retained;
    int used;
} chron_text_entry;

typedef struct {
    uint32_t id;
    uint64_t start_tick, end_tick;
    int used;
} chron_mock_entry;

typedef struct {
    uint32_t region;
    uint64_t tick;
} chron_ownership_change;

typedef struct {
    uint32_t id;
    int is_printing;
    int used;
} chron_entry_state;

typedef struct {
    om_chronicle_cluster candidates[CHRON_MAX_CANDIDATES];
    uint32_t n_candidates;
    /* Lineage id behind each candidate / final cluster (-1 none); parallel to
     * candidates[] and clusters[], which the frozen om_chronicle_cluster has
     * no field for. Feeds om_chronicle_entry.lineage_ref. */
    int32_t candidate_lineage[CHRON_MAX_CANDIDATES];
    int32_t cluster_lineage[CHRON_MAX_FINAL];

    chron_raw_chain_event raw_chain[CHRON_MAX_RAW_CHAIN];
    uint32_t n_raw_chain;

    om_chronicle_cluster clusters[CHRON_MAX_FINAL];
    uint32_t n_clusters;

    char full_scroll_text[CHRON_FULL_TEXT_CAP];

    /* One slot per cluster, index-aligned; entry_valid is 0 for a cluster whose
     * assembly failed or that cross-entry dedup dropped. Cleared whenever the
     * cluster list is rebuilt. */
    om_chronicle_entry entries[CHRON_MAX_FINAL];
    uint8_t entry_valid[CHRON_MAX_FINAL];
    uint32_t n_entries;

    chron_text_entry text_entries[CHRON_MAX_TEXT_ENTRIES];
    uint32_t n_text_entries;

    chron_mock_entry mock_entries[CHRON_MAX_MOCK_ENTRIES];
    uint32_t n_mock_entries;

    chron_ownership_change ownership_changes[CHRON_MAX_OWNERSHIP_CHANGES];
    uint32_t n_ownership_changes;

    uint64_t keyframes[CHRON_MAX_KEYFRAMES];
    uint32_t n_keyframes;

    chron_entry_state entry_states[CHRON_MAX_ENTRY_STATES];
    uint32_t n_entry_states;

    int paused;

    /* Set once a distill consumed the candidate pool: the ownership changes
     * recorded so far belong to that finished jump, so the next
     * add_ownership_change_event starts a fresh list and om_chronicle_add_event
     * ignores the stale one. */
    int own_stale;

    int fragments_loaded;
    int invalid_fragment_injected;
    uint32_t invalid_fragment_category;
    char invalid_fragment_slot[64];
} chron_state;

static void chron_state_free(void *p) {
    free(p);
}

static chron_state *chron(om_world *w) {
    chron_state *st = (chron_state *)w->chronicle_state;
    if (!st) {
        st = (chron_state *)calloc(1, sizeof(chron_state));
        w->chronicle_state = st;
        w->chronicle_state_free = chron_state_free;
    }
    return st;
}

static const chron_state *chron_ro(const om_world *w) {
    return (const chron_state *)w->chronicle_state;
}

/* ---- local deterministic RNG (ALG-53: "RNG seeded with the jump start
 * tick"), independent of w's own om_rng_draw stream. ---- */

static uint64_t chron_splitmix_next(uint64_t *state) {
    uint64_t z = (*state += CHRON_RNG_GOLDEN);
    z = (z ^ (z >> CHRON_RNG_SHIFT1)) * CHRON_RNG_MIX1;
    z = (z ^ (z >> CHRON_RNG_SHIFT2)) * CHRON_RNG_MIX2;
    return z ^ (z >> CHRON_RNG_SHIFT3);
}

static double chron_rand01(uint64_t *state) {
    return (double)(chron_splitmix_next(state) >> CHRON_RNG_OUT_SHIFT) * CHRON_RNG_SCALE;
}

static uint32_t chron_rand_index(uint64_t *state, uint32_t n) {
    if (n == 0) return 0;
    double u = chron_rand01(state);
    uint32_t idx = (uint32_t)(u * (double)n);
    if (idx >= n) idx = n - 1;
    return idx;
}

/* ---- digit-free procedural names (no region/faction name accessor exists
 * in the frozen ABI; the epic's "registry names" input is a client/E-21
 * concern not yet wired into csrc). ---- */

static const char *CHRON_REGION_NAMES[] = {
    "the Ashfall Reach", "the Windward Marches", "the Salt Hollow", "the Iron Vale",
    "the Cinder Steppe", "the Glasswater Coast", "the Thornwood", "the Bramblehold",
    "the Greyshore", "the Duskfen", "the Amberfields", "the Stonebridge Cross",
    "the Hollow Crown", "the Emberlight Basin", "the Wraithmoor", "the Suncrest Ridge",
};
#define CHRON_N_REGION_NAMES 16

static const char *CHRON_FACTION_NAMES[] = {
    "the Dominion", "the Concord", "the Ashen League", "the Iron Compact",
    "the Free Cities", "the Sable Court", "the Vanguard Accord", "the Twin Banners",
};
#define CHRON_N_FACTION_NAMES 8

static const char *CHRON_LINEAGE_SURNAMES[] = {
    "Voss", "Kestrel", "Thane", "Ashworth", "Marrow", "Corvane", "Halloway", "Sennett",
};
#define CHRON_N_LINEAGE_SURNAMES 8

static const char *chron_region_name(uint32_t region_idx) {
    return CHRON_REGION_NAMES[region_idx % CHRON_N_REGION_NAMES];
}

static const char *chron_faction_name(int32_t faction_id) {
    if (faction_id < 0) return "an unclaimed people";
    return CHRON_FACTION_NAMES[(uint32_t)faction_id % CHRON_N_FACTION_NAMES];
}

static const char *chron_lineage_surname(uint32_t region_idx) {
    return CHRON_LINEAGE_SURNAMES[region_idx % CHRON_N_LINEAGE_SURNAMES];
}

/* Mirrors generational.c's private GEN_RANK_* values by convention (no
 * shared header declares them); R-070-03 requires every rendered rank read
 * as military, never civilian/political. */
#define CHRON_RANK_SUPREME_COMMANDER 0
#define CHRON_RANK_REGIONAL_COMMANDER 1
#define CHRON_RANK_GARRISON_OFFICER 2
#define CHRON_RANK_LINEAGE_MEMBER 3
#define CHRON_RANK_UNKNOWN 9

static const char *chron_rank_name(uint32_t rank) {
    switch (rank) {
    case CHRON_RANK_SUPREME_COMMANDER: return "marshal";
    case CHRON_RANK_REGIONAL_COMMANDER: return "commander";
    case CHRON_RANK_GARRISON_OFFICER: return "officer";
    case CHRON_RANK_LINEAGE_MEMBER: return "captain";
    default: return "soldier";
    }
}

/* ---- text utilities (ALG-53 dedup / echo) ---- */

static const char *CHRON_STOP_WORDS[] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "its", "their", "was", "were", "had", "has",
    "that", "this", "which", "what", "as", "is", "it", "be", "been", "not",
    "no", "all", "each", "every", "into", "over", "than", "then", "when",
    "after", "before", "while", "until", "across", "beyond",
};
#define CHRON_N_STOP_WORDS (sizeof(CHRON_STOP_WORDS) / sizeof(CHRON_STOP_WORDS[0]))

typedef struct { const char *word; const char *synonym; } chron_synonym_kv;

static const chron_synonym_kv CHRON_SYNONYMS[] = {
    {"instability", "unease"}, {"unrest", "discontent"}, {"tensions", "frictions"},
    {"tension", "friction"}, {"collapsed", "crumbled"}, {"collapse", "breakdown"},
    {"deteriorated", "worsened"}, {"expanded", "grew"}, {"eroded", "weakened"},
    {"mounted", "intensified"}, {"spread", "widened"}, {"surged", "swelled"},
    {"strengthened", "solidified"}, {"contracted", "shrank"}, {"military", "martial"},
    {"commerce", "trade"}, {"battle", "conflict"}, {"battles", "conflicts"},
    {"war", "conflict"}, {"revolt", "uprising"}, {"crisis", "emergency"},
};
#define CHRON_N_SYNONYMS (sizeof(CHRON_SYNONYMS) / sizeof(CHRON_SYNONYMS[0]))

static int chron_is_stop_word(const char *w, size_t len) {
    for (size_t i = 0; i < CHRON_N_STOP_WORDS; i++) {
        if (strlen(CHRON_STOP_WORDS[i]) == len && strncmp(CHRON_STOP_WORDS[i], w, len) == 0)
            return 1;
    }
    return 0;
}

static const char *chron_synonym_of(const char *w, size_t len) {
    for (size_t i = 0; i < CHRON_N_SYNONYMS; i++) {
        if (strlen(CHRON_SYNONYMS[i].word) == len && strncmp(CHRON_SYNONYMS[i].word, w, len) == 0)
            return CHRON_SYNONYMS[i].synonym;
    }
    return NULL;
}

static size_t chron_clean_word(const char *w, size_t len, char *out, size_t outcap) {
    size_t n = 0;
    for (size_t i = 0; i < len && n + 1 < outcap; i++) {
        unsigned char c = (unsigned char)w[i];
        if (isalpha(c)) out[n++] = (char)tolower(c);
    }
    out[n] = '\0';
    return n;
}

static uint32_t chron_word_count(const char *text) {
    if (!text) return 0;
    uint32_t n = 0;
    int in_word = 0;
    for (const char *p = text; *p; p++) {
        if (isspace((unsigned char)*p)) {
            in_word = 0;
        } else if (!in_word) {
            in_word = 1;
            n++;
        }
    }
    return n;
}

/* Content words: lowercase, letters only, length > OM_CHRON_CONTENT_WORD_MIN_LEN,
 * not a stop word (ALG-53 cross-entry dedup / R-068-07). Marks each match into
 * a small fixed table of cleaned words for set-overlap comparison. */
#define CHRON_MAX_CONTENT_WORDS 128

typedef struct {
    char words[CHRON_MAX_CONTENT_WORDS][32];
    uint32_t n;
} chron_word_set;

static void chron_content_words(const char *text, chron_word_set *out) {
    out->n = 0;
    if (!text) return;
    const char *p = text;
    while (*p && out->n < CHRON_MAX_CONTENT_WORDS) {
        while (*p && !isalpha((unsigned char)*p)) p++;
        const char *start = p;
        while (*p && isalpha((unsigned char)*p)) p++;
        size_t len = (size_t)(p - start);
        if (len > OM_CHRON_CONTENT_WORD_MIN_LEN) {
            char clean[32];
            size_t n = chron_clean_word(start, len, clean, sizeof(clean));
            if (n > 0 && !chron_is_stop_word(clean, n)) {
                snprintf(out->words[out->n], sizeof(out->words[out->n]), "%s", clean);
                out->n++;
            }
        }
    }
}

static int chron_word_set_contains(const chron_word_set *set, const char *word) {
    for (uint32_t i = 0; i < set->n; i++) {
        if (strcmp(set->words[i], word) == 0) return 1;
    }
    return 0;
}

static uint32_t chron_word_set_overlap(const chron_word_set *a, const chron_word_set *b) {
    uint32_t overlap = 0;
    for (uint32_t i = 0; i < a->n; i++) {
        int dup = 0;
        for (uint32_t j = 0; j < i; j++) {
            if (strcmp(a->words[j], a->words[i]) == 0) { dup = 1; break; }
        }
        if (!dup && chron_word_set_contains(b, a->words[i])) overlap++;
    }
    return overlap;
}

static uint32_t chron_word_set_unique_count(const chron_word_set *a) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < a->n; i++) {
        int dup = 0;
        for (uint32_t j = 0; j < i; j++) {
            if (strcmp(a->words[j], a->words[i]) == 0) { dup = 1; break; }
        }
        if (!dup) n++;
    }
    return n;
}

/* Word-echo synonym substitution: on a word's second appearance, replace
 * with its curated synonym if one exists (R-068-06). Operates in place on a
 * fixed buffer. */
static void chron_dedup_echo_words(char *text, size_t cap) {
    (void)cap;
    char seen[CHRON_MAX_CONTENT_WORDS][32];
    uint32_t n_seen = 0;
    char out[1024];
    size_t out_len = 0;
    const char *p = text;
    out[0] = '\0';
    while (*p) {
        const char *start = p;
        while (*p && !isspace((unsigned char)*p)) p++;
        size_t tok_len = (size_t)(p - start);
        size_t clean_len = tok_len;
        while (clean_len > 0 && !isalpha((unsigned char)start[clean_len - 1])) clean_len--;
        char clean[32];
        size_t cn = chron_clean_word(start, clean_len, clean, sizeof(clean));

        const char *replacement = NULL;
        if (cn > OM_CHRON_CONTENT_WORD_MIN_LEN && !chron_is_stop_word(clean, cn)) {
            int is_seen = 0;
            for (uint32_t i = 0; i < n_seen; i++) {
                if (strcmp(seen[i], clean) == 0) { is_seen = 1; break; }
            }
            if (is_seen) {
                replacement = chron_synonym_of(clean, cn);
            } else if (n_seen < CHRON_MAX_CONTENT_WORDS) {
                snprintf(seen[n_seen], sizeof(seen[n_seen]), "%s", clean);
                n_seen++;
            }
        }

        if (replacement) {
            int cap_first = isupper((unsigned char)start[0]);
            size_t rlen = strlen(replacement);
            for (size_t i = 0; i < rlen && out_len + 1 < sizeof(out); i++) {
                char c = replacement[i];
                if (i == 0 && cap_first) c = (char)toupper((unsigned char)c);
                out[out_len++] = c;
            }
            for (size_t i = clean_len; i < tok_len && out_len + 1 < sizeof(out); i++) {
                out[out_len++] = start[i];
            }
        } else {
            for (size_t i = 0; i < tok_len && out_len + 1 < sizeof(out); i++) {
                out[out_len++] = start[i];
            }
        }
        if (*p && out_len + 1 < sizeof(out)) out[out_len++] = ' ';
        while (*p && isspace((unsigned char)*p)) p++;
    }
    out[out_len] = '\0';
    strncpy(text, out, cap - 1);
    text[cap - 1] = '\0';
}

#define CHRON_EDIT_DIST_MAX_LEN 255

static uint32_t chron_edit_distance(const char *a, const char *b) {
    size_t la = strlen(a), lb = strlen(b);
    if (la > CHRON_EDIT_DIST_MAX_LEN) la = CHRON_EDIT_DIST_MAX_LEN;
    if (lb > CHRON_EDIT_DIST_MAX_LEN) lb = CHRON_EDIT_DIST_MAX_LEN;
    uint32_t prev[CHRON_EDIT_DIST_MAX_LEN + 1], cur[CHRON_EDIT_DIST_MAX_LEN + 1];
    for (size_t j = 0; j <= lb; j++) prev[j] = (uint32_t)j;
    for (size_t i = 1; i <= la; i++) {
        cur[0] = (uint32_t)i;
        for (size_t j = 1; j <= lb; j++) {
            uint32_t cost = (a[i - 1] == b[j - 1]) ? 0 : 1;
            uint32_t del = prev[j] + 1;
            uint32_t ins = cur[j - 1] + 1;
            uint32_t sub = prev[j - 1] + cost;
            uint32_t m = del < ins ? del : ins;
            cur[j] = m < sub ? m : sub;
        }
        memcpy(prev, cur, sizeof(uint32_t) * (lb + 1));
    }
    return prev[lb];
}

/* ---- slot resolution (ALG-53) ---- */

typedef struct { const char *key; char value[CHRON_SLOT_VALUE_CAP]; } chron_slot_kv;

/* The 16 slots the launch fragment library actually uses (scanned from
 * simulation/library/chronicle/fragments.json); chron_build_slots populates
 * exactly these, in this order. */
#define CHRON_N_SLOTS 16
static const char *CHRON_POPULATED_SLOTS[CHRON_N_SLOTS] = {
    "{character_name}", "{character_rank}", "{lineage_name}", "{faction_name}",
    "{region_name}", "{adjacent_region}", "{event_description}", "{chain_length}",
    "{duration_prose}", "{field_delta_summary}", "{stability_level}", "{capacity_level}",
    "{tension_level}", "{mission_outcome}", "{mission_archetype}", "{mission_region}",
};

/* R-068-03 vocabulary whitelist (identity/event/state/consequence/relational);
 * a superset of CHRON_POPULATED_SLOTS -- character_faction, previous_event_reference
 * and lineage_history_note are valid vocabulary the launch library just doesn't
 * draw on yet, kept here so fragment_library_validate() judges by the epic's
 * full contract, not only today's library contents. */
static const char *CHRON_VALID_SLOTS[] = {
    "{character_name}", "{character_rank}", "{character_faction}", "{lineage_name}",
    "{faction_name}", "{region_name}", "{adjacent_region}", "{event_description}",
    "{chain_length}", "{duration_prose}", "{field_delta_summary}", "{stability_level}",
    "{capacity_level}", "{tension_level}", "{mission_outcome}", "{mission_archetype}",
    "{mission_region}", "{previous_event_reference}", "{lineage_history_note}",
};
#define CHRON_N_VALID_SLOTS (sizeof(CHRON_VALID_SLOTS) / sizeof(CHRON_VALID_SLOTS[0]))

static int chron_slot_is_valid(const char *slot) {
    for (size_t i = 0; i < CHRON_N_VALID_SLOTS; i++) {
        if (strcmp(CHRON_VALID_SLOTS[i], slot) == 0) return 1;
    }
    return 0;
}

static const char *chron_field_delta_phrase(uint32_t effective_category) {
    switch (effective_category) {
    case CAT_LINEAGE_THRIVED: return "prosperity took hold and steadily compounded";
    case CAT_LINEAGE_SUFFERED: return "hardship spread and lingered";
    case CAT_LINEAGE_SUCCESSION: return "the old order gave way to the new";
    case CAT_LINEAGE_MILITARY_ACTION: return "arms decided what words could not";
    case CAT_CHAIN_REVOLT_SPAWNED: return "authority cracked under open defiance";
    case CAT_CHAIN_EXPANSION: return "new ground was claimed and held";
    case CAT_CHAIN_CASCADE: return "one event tumbled into the next";
    case CAT_CHAIN_CONFLICT_VICTORY: return "the field was held and the line advanced";
    case CAT_CHAIN_CONFLICT_DEFEAT: return "the line broke and ground was lost";
    case CAT_CHAIN_CONFLICT_STALEMATE: return "neither side could force the issue";
    case CAT_CHAIN_CRISIS_RESOLVED_WELL: return "the crisis passed and left things stronger";
    case CAT_CHAIN_CRISIS_RESOLVED_BADLY: return "the crisis passed but left scars";
    case CAT_REGIONAL_FACTION_SHIFT: return "the banners over the region changed hands";
    case CAT_REGIONAL_GROWTH: return "the markets and the streets both filled";
    case CAT_REGIONAL_DECLINE: return "the markets and the streets both emptied";
    case CAT_REGIONAL_STABLE: return "conditions held steady through it all";
    case CAT_CONSEQUENCE_SUCCESS: return "the commander's work bore fruit";
    case CAT_CONSEQUENCE_FAILURE: return "the commander's work came to little";
    case CAT_CONSEQUENCE_MIXED: return "the outcome was neither victory nor ruin";
    case CAT_CONSEQUENCE_RIPPLE: return "the echo of it was felt across the border";
    default: return "conditions shifted in ways the record still argues over";
    }
}

static const char *chron_duration_prose(uint64_t span) {
    if (span <= OM_CHRON_DURATION_DAYS_MAX) return "in a matter of days";
    if (span <= OM_CHRON_DURATION_WEEKS_MAX) return "over the following weeks";
    if (span <= OM_CHRON_DURATION_MONTHS_MAX) return "over the following months";
    if (span <= OM_CHRON_DURATION_YEAR_MAX) return "over the span of a year";
    return "across the years that followed";
}

static const char *chron_stability_prose(double v) {
    if (v >= OM_CHRON_STABILITY_HIGH) return "firmly stable";
    if (v >= OM_CHRON_STABILITY_MID) return "reasonably stable";
    if (v >= OM_CHRON_STABILITY_LOW) return "uneasy";
    return "dangerously unstable";
}

static const char *chron_capacity_prose(double v) {
    if (v >= OM_CHRON_CAPACITY_HIGH) return "thriving";
    if (v >= OM_CHRON_CAPACITY_MID) return "adequate";
    if (v >= OM_CHRON_CAPACITY_LOW) return "strained";
    return "depleted";
}

static const char *chron_tension_prose(double v) {
    if (v >= OM_CHRON_TENSION_HIGH) return "volatile";
    if (v >= OM_CHRON_TENSION_MID) return "tense";
    if (v >= OM_CHRON_TENSION_LOW) return "restless";
    return "calm";
}

/* Mechanical event-description noun phrase from a category name: strip its
 * type prefix and swap underscores for spaces (e.g. "chain_conflict_victory"
 * -> "conflict victory"), always lowercase, always non-empty. */
static void chron_event_description(uint32_t effective_category, char *out, size_t cap) {
    const char *name = chron_category_name(effective_category);
    const char *rest = strchr(name, '_');
    rest = rest ? rest + 1 : name;
    size_t n = 0;
    for (const char *p = rest; *p && n + 1 < cap; p++) {
        out[n++] = (*p == '_') ? ' ' : *p;
    }
    out[n] = '\0';
}

static uint32_t chron_effective_category(const om_chronicle_cluster *c) {
    if (c->type == CTYPE_CONSEQUENCE) return CAT_CONSEQUENCE_SUCCESS + c->category;
    return c->category;
}

/* Index layout matches CHRON_POPULATED_SLOTS exactly:
 * 0 character_name, 1 character_rank, 2 lineage_name, 3 faction_name,
 * 4 region_name, 5 adjacent_region, 6 event_description, 7 chain_length,
 * 8 duration_prose, 9 field_delta_summary, 10 stability_level,
 * 11 capacity_level, 12 tension_level, 13 mission_outcome,
 * 14 mission_archetype, 15 mission_region. */
/* Indices into CHRON_POPULATED_SLOTS/chron_slot_kv[], matching its order
 * exactly (see the comment above it). */
enum {
    SLOT_CHARACTER_NAME = 0, SLOT_CHARACTER_RANK, SLOT_LINEAGE_NAME, SLOT_FACTION_NAME,
    SLOT_REGION_NAME, SLOT_ADJACENT_REGION, SLOT_EVENT_DESCRIPTION, SLOT_CHAIN_LENGTH,
    SLOT_DURATION_PROSE, SLOT_FIELD_DELTA_SUMMARY, SLOT_STABILITY_LEVEL, SLOT_CAPACITY_LEVEL,
    SLOT_TENSION_LEVEL, SLOT_MISSION_OUTCOME, SLOT_MISSION_ARCHETYPE, SLOT_MISSION_REGION,
};

#define CHRON_NEIGHBOR_SAMPLE_CAP 4

static void chron_build_slots(const om_world *w, const om_chronicle_cluster *c, chron_slot_kv *slots) {
    uint32_t eff_cat = chron_effective_category(c);
    int32_t owner = om_region_owner(w, c->region);

    for (uint32_t i = 0; i < CHRON_N_SLOTS; i++) slots[i].key = CHRON_POPULATED_SLOTS[i];

    snprintf(slots[SLOT_CHARACTER_NAME].value, CHRON_SLOT_VALUE_CAP, "%s Vane", chron_lineage_surname(c->region));
    snprintf(slots[SLOT_CHARACTER_RANK].value, CHRON_SLOT_VALUE_CAP, "%s", "commander");
    snprintf(slots[SLOT_LINEAGE_NAME].value, CHRON_SLOT_VALUE_CAP, "%s", chron_lineage_surname(c->region));
    snprintf(slots[SLOT_FACTION_NAME].value, CHRON_SLOT_VALUE_CAP, "%s", chron_faction_name(owner));
    snprintf(slots[SLOT_REGION_NAME].value, CHRON_SLOT_VALUE_CAP, "%s", chron_region_name(c->region));

    uint32_t neigh[CHRON_NEIGHBOR_SAMPLE_CAP];
    uint32_t nn = om_region_neighbors(w, c->region, neigh, CHRON_NEIGHBOR_SAMPLE_CAP);
    snprintf(slots[SLOT_ADJACENT_REGION].value, CHRON_SLOT_VALUE_CAP, "%s",
             nn > 0 ? chron_region_name(neigh[0]) : "the neighbouring lands");

    char desc[CHRON_SLOT_VALUE_CAP];
    chron_event_description(eff_cat, desc, sizeof(desc));
    snprintf(slots[SLOT_EVENT_DESCRIPTION].value, CHRON_SLOT_VALUE_CAP, "%s", desc);

    snprintf(slots[SLOT_CHAIN_LENGTH].value, CHRON_SLOT_VALUE_CAP, "%s", "a chain of events");

    uint64_t span = c->end_tick > c->start_tick ? c->end_tick - c->start_tick : 0;
    snprintf(slots[SLOT_DURATION_PROSE].value, CHRON_SLOT_VALUE_CAP, "%s", chron_duration_prose(span));
    snprintf(slots[SLOT_FIELD_DELTA_SUMMARY].value, CHRON_SLOT_VALUE_CAP, "%s", chron_field_delta_phrase(eff_cat));
    snprintf(slots[SLOT_STABILITY_LEVEL].value, CHRON_SLOT_VALUE_CAP, "%s",
             chron_stability_prose(om_region_composite(w, c->region, OM_C_STABILITY)));
    snprintf(slots[SLOT_CAPACITY_LEVEL].value, CHRON_SLOT_VALUE_CAP, "%s",
             chron_capacity_prose(om_region_composite(w, c->region, OM_C_CAPACITY)));
    snprintf(slots[SLOT_TENSION_LEVEL].value, CHRON_SLOT_VALUE_CAP, "%s",
             chron_tension_prose(om_region_field(w, c->region, OM_F_TENSION)));

    const char *outcome = "an uncertain outcome";
    if (c->type == CTYPE_CONSEQUENCE) {
        if (c->category == 0) outcome = "a clear success";
        else if (c->category == 1) outcome = "a costly failure";
        else outcome = "a mixed result";
    }
    snprintf(slots[SLOT_MISSION_OUTCOME].value, CHRON_SLOT_VALUE_CAP, "%s", outcome);
    snprintf(slots[SLOT_MISSION_ARCHETYPE].value, CHRON_SLOT_VALUE_CAP, "%s", "the commander");
    uint32_t mission_region = eff_cat == CAT_CONSEQUENCE_RIPPLE ? om_mission_last_region(w) : c->region;
    snprintf(slots[SLOT_MISSION_REGION].value, CHRON_SLOT_VALUE_CAP, "%s", chron_region_name(mission_region));
}

static int chron_slot_lookup(const chron_slot_kv *slots, const char *key, char *out, size_t outcap) {
    for (size_t i = 0; i < CHRON_N_SLOTS; i++) {
        if (strcmp(slots[i].key, key) == 0) {
            snprintf(out, outcap, "%s", slots[i].value);
            return 1;
        }
    }
    return 0;
}

static void chron_resolve_text(const char *tmpl, const chron_slot_kv *slots, char *out, size_t outcap) {
    size_t out_len = 0;
    const char *p = tmpl;
    while (*p && out_len + 1 < outcap) {
        if (*p == '{') {
            const char *end = strchr(p, '}');
            if (end) {
                char key[64];
                size_t klen = (size_t)(end - p) + 1;
                if (klen >= sizeof(key)) klen = sizeof(key) - 1;
                memcpy(key, p, klen);
                key[klen] = '\0';
                char val[CHRON_SLOT_VALUE_CAP];
                if (chron_slot_lookup(slots, key, val, sizeof(val))) {
                    size_t vlen = strlen(val);
                    for (size_t i = 0; i < vlen && out_len + 1 < outcap; i++) out[out_len++] = val[i];
                    p = end + 1;
                    continue;
                }
            }
        }
        out[out_len++] = *p++;
    }
    out[out_len] = '\0';
}

static void chron_fix_post_period_caps(char *text) {
    for (char *p = text; *p; p++) {
        if (p[0] == '.' && p[1] == ' ' && p[2] && isalpha((unsigned char)p[2])) {
            p[2] = (char)toupper((unsigned char)p[2]);
        }
    }
}

static void chron_capitalize_first(char *text) {
    if (text[0]) text[0] = (char)toupper((unsigned char)text[0]);
}

/* ---- fragment picking + assembly (ALG-53) ---- */

/* Sample cap for one category/type pool -- generous over the launch
 * library's per-pool minimum (S-071: 6 openings / 8 details / 5 closings). */
#define CHRON_POOL_SAMPLE_CAP 64

static uint32_t chron_pool_indices(uint32_t sparse_category, uint32_t type, uint32_t *out, uint32_t max) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < CHRON_N_FRAGMENTS && n < max; i++) {
        if (CHRON_FRAGMENTS[i].category == sparse_category && CHRON_FRAGMENTS[i].type == type) {
            out[n++] = i;
        }
    }
    return n;
}

static const chron_fragment *chron_pick_fragment(uint32_t sparse_category, uint32_t type, uint64_t *rng) {
    uint32_t idx[CHRON_POOL_SAMPLE_CAP];
    uint32_t n = chron_pool_indices(sparse_category, type, idx, (uint32_t)(sizeof(idx) / sizeof(idx[0])));
    if (n == 0) return NULL;
    return &CHRON_FRAGMENTS[idx[chron_rand_index(rng, n)]];
}

/* R-068-05: adjacent fragments that resolve the same slot to a value of
 * OM_CHRON_ECHO_WORD_THRESHOLD+ words get the second occurrence collapsed to
 * an anaphoric form instead of repeating it. */
static const char *chron_anaphoric_form(uint64_t *rng) {
    static const char *forms[] = {"what followed", "the outcome", "what came next"};
    return forms[chron_rand_index(rng, 3)];
}

static void chron_apply_echo_between(const char *tmpl_a, const char *tmpl_b, chron_slot_kv *slots, uint64_t *rng) {
    for (uint32_t i = 0; i < CHRON_N_SLOTS; i++) {
        char needle[80];
        snprintf(needle, sizeof(needle), "%s", slots[i].key);
        if (strstr(tmpl_a, needle) && strstr(tmpl_b, needle)) {
            if (chron_word_count(slots[i].value) >= OM_CHRON_ECHO_WORD_THRESHOLD) {
                snprintf(slots[i].value, CHRON_SLOT_VALUE_CAP, "%s", chron_anaphoric_form(rng));
            }
        }
    }
}

/* Assembles one entry's base/expanded text for `category` (sparse id) and
 * `region_idx`, using `rng` for opening/detail/closing draws. Shared by the
 * distill pipeline and the direct om_chronicle_assemble_cluster_entry seam. */
static int chron_assemble(const om_world *w, uint32_t category, uint32_t region_idx,
                           uint64_t *rng, char *base_out, size_t base_cap,
                           char *expanded_out, size_t expanded_cap, int32_t *fragment_ids) {
    om_chronicle_cluster synth;
    memset(&synth, 0, sizeof(synth));
    synth.type = (category >= CAT_CONSEQUENCE_SUCCESS) ? CTYPE_CONSEQUENCE
               : (category >= CAT_REGIONAL_FACTION_SHIFT) ? CTYPE_REGIONAL
               : (category >= CAT_CHAIN_REVOLT_SPAWNED) ? CTYPE_CHAIN : CTYPE_LINEAGE;
    synth.category = (synth.type == CTYPE_CONSEQUENCE) ? category - CAT_CONSEQUENCE_SUCCESS : category;
    synth.region = region_idx;

    chron_slot_kv slots[CHRON_N_SLOTS];
    chron_build_slots(w, &synth, slots);

    if (category == CAT_CONSEQUENCE_RIPPLE) {
        /* Q-067-01 (b): the 399-fragment library has no ripple pool yet; until it does,
         * one placeholder line (rules: missing library content falls back to a placeholder). */
        char text[CHRON_FRAGMENT_TEXT_CAP];
        chron_resolve_text("Word of what was done at {mission_region} reached {region_name}, where {field_delta_summary}.",
                           slots, text, sizeof(text));
        snprintf(base_out, base_cap, "%s", text);
        snprintf(expanded_out, expanded_cap, "%s", text);
        fragment_ids[0] = fragment_ids[1] = fragment_ids[2] = -1;
        return 1;
    }
    const chron_fragment *opening = chron_pick_fragment(category, 0, rng);
    const chron_fragment *detail = chron_pick_fragment(category, 1, rng);
    const chron_fragment *closing = chron_pick_fragment(category, 2, rng);
    if (!opening || !detail) return 0;
    fragment_ids[0] = (int32_t)(opening - CHRON_FRAGMENTS);
    fragment_ids[1] = (int32_t)(detail - CHRON_FRAGMENTS);
    fragment_ids[2] = closing ? (int32_t)(closing - CHRON_FRAGMENTS) : -1;

    if (closing) chron_apply_echo_between(detail->text, closing->text, slots, rng);
    chron_apply_echo_between(opening->text, detail->text, slots, rng);

    char opening_r[CHRON_FRAGMENT_TEXT_CAP], detail_r[CHRON_FRAGMENT_TEXT_CAP], closing_r[CHRON_FRAGMENT_TEXT_CAP];
    chron_resolve_text(opening->text, slots, opening_r, sizeof(opening_r));
    chron_resolve_text(detail->text, slots, detail_r, sizeof(detail_r));

    char base[1024];
    snprintf(base, sizeof(base), "%s %s", opening_r, detail_r);
    chron_dedup_echo_words(base, sizeof(base));
    chron_fix_post_period_caps(base);
    chron_capitalize_first(base);

    char expanded[1600];
    if (closing) {
        chron_resolve_text(closing->text, slots, closing_r, sizeof(closing_r));
        snprintf(expanded, sizeof(expanded), "%s %s", base, closing_r);
    } else {
        snprintf(expanded, sizeof(expanded), "%s", base);
    }
    chron_dedup_echo_words(expanded, sizeof(expanded));
    chron_fix_post_period_caps(expanded);
    chron_capitalize_first(expanded);

    snprintf(base_out, base_cap, "%s", base);
    snprintf(expanded_out, expanded_cap, "%s", expanded);
    return 1;
}

/* R-068-04: region's first mention in the scroll gets ", held by <faction>"
 * appended once; later mentions and unowned regions get the bare name. */
static void chron_render_region_mention(const om_world *w, uint32_t region_idx, int is_first_mention,
                                         char *out, size_t cap) {
    const char *name = chron_region_name(region_idx);
    int32_t owner = om_region_owner(w, region_idx);
    if (is_first_mention && owner >= 0) {
        snprintf(out, cap, "%s, held by %s", name, chron_faction_name(owner));
    } else {
        snprintf(out, cap, "%s", name);
    }
}

/* ---- categorization (R-067-02..R-067-05) ---- */

static uint32_t chron_categorize_lineage_cluster(const char *template_name, double net_eco, double net_mil, double net_ten) {
    if (strstr(template_name, "succession") || strstr(template_name, "death")) return CAT_LINEAGE_SUCCESSION;
    if (strstr(template_name, "military") || strstr(template_name, "revolt")) return CAT_LINEAGE_MILITARY_ACTION;
    if (net_eco > OM_CHRON_THRIVED_ECO_MIN || net_mil > OM_CHRON_THRIVED_MIL_MIN) return CAT_LINEAGE_THRIVED;
    if (net_eco < OM_CHRON_SUFFERED_ECO_MAX || net_ten > OM_CHRON_SUFFERED_TEN_MIN) return CAT_LINEAGE_SUFFERED;
    return CAT_LINEAGE_QUIET;
}

static uint32_t chron_categorize_chain_cluster(const char *template_name, uint32_t n_events,
                                                double net_mil, double net_eco, double net_ten) {
    if (strstr(template_name, "revolt")) return CAT_CHAIN_REVOLT_SPAWNED;
    if (strstr(template_name, "expansion") || strstr(template_name, "coloniz")) return CAT_CHAIN_EXPANSION;
    if (n_events >= OM_CHRON_CASCADE_MIN_EVENTS) return CAT_CHAIN_CASCADE;
    if (net_mil > OM_CHRON_VICTORY_MIL_MIN && net_ten < OM_CHRON_VICTORY_TEN_MAX) return CAT_CHAIN_CONFLICT_VICTORY;
    if (net_mil < OM_CHRON_DEFEAT_MIL_MAX && net_ten > OM_CHRON_DEFEAT_TEN_MIN) return CAT_CHAIN_CONFLICT_DEFEAT;
    if (fabs(net_mil) <= OM_CHRON_STALEMATE_MIL_ABS_MAX && net_ten > OM_CHRON_STALEMATE_TEN_MIN) return CAT_CHAIN_CONFLICT_STALEMATE;
    if (net_eco > 0.0 && net_ten <= 0.0) return CAT_CHAIN_CRISIS_RESOLVED_WELL;
    return CAT_CHAIN_CRISIS_RESOLVED_BADLY;
}

static uint32_t chron_categorize_regional_cluster(int has_conquest_or_revolt, double net_eco_pop) {
    if (has_conquest_or_revolt) return CAT_REGIONAL_FACTION_SHIFT;
    if (net_eco_pop > OM_CHRON_REGIONAL_GROWTH_MIN) return CAT_REGIONAL_GROWTH;
    if (net_eco_pop < OM_CHRON_REGIONAL_DECLINE_MAX) return CAT_REGIONAL_DECLINE;
    return CAT_REGIONAL_STABLE;
}

/* ---- scoring (ALG-50) ---- */

static double chron_score_base(uint32_t tier, double delta_sum) {
    double boost = delta_sum / OM_SIGNIFICANCE_DELTA_SCALE;
    if (boost > OM_SIGNIFICANCE_DELTA_CAP) boost = OM_SIGNIFICANCE_DELTA_CAP;
    return (double)tier + boost;
}

static double chron_context_multiplier(int in_mission_region, int has_character, uint32_t chain_length, int has_lineage_member) {
    double mult = 1.0;
    if (in_mission_region) mult += OM_SIGNIFICANCE_MISSION_REGION_BONUS;
    if (has_character) mult += OM_SIGNIFICANCE_CHARACTER_BONUS;
    if (chain_length > 1) {
        uint32_t capped = chain_length < OM_CHAIN_LENGTH_CAP ? chain_length : OM_CHAIN_LENGTH_CAP;
        mult += OM_SIGNIFICANCE_CHAIN_LENGTH_BONUS * (double)capped;
    }
    if (has_lineage_member) mult += OM_SIGNIFICANCE_LINEAGE_REGION_BONUS;
    return mult;
}

/* ---- clustering + selection (ALG-51, ALG-52) ---- */

static void chron_push_candidate(chron_state *st, uint32_t type, uint32_t category, uint32_t region,
                                  double score, int32_t chain_tag, uint64_t start_tick, uint64_t end_tick) {
    if (st->n_candidates >= CHRON_MAX_CANDIDATES) return;
    om_chronicle_cluster *c = &st->candidates[st->n_candidates++];
    c->type = type;
    c->category = category;
    c->region = region;
    c->peak_score = score;
    c->chain_tag = chain_tag;
    c->start_tick = start_tick;
    c->end_tick = end_tick;
    st->candidate_lineage[st->n_candidates - 1] = -1;
}

static void chron_push_lineage_candidate(chron_state *st, uint32_t lineage_id, uint32_t region, double score) {
    uint32_t n = st->n_candidates;
    chron_push_candidate(st, CTYPE_LINEAGE, CAT_LINEAGE_QUIET, region, score, -1, 0, 0);
    if (st->n_candidates > n) st->candidate_lineage[n] = (int32_t)lineage_id;
}

/* R-067-03: raw chain events merge by chain_tag (primary region = first
 * seen, category = first event's), then chain clusters sharing (primary
 * region, category) merge into one. Returns the resulting cluster count and
 * appends them to the candidate pool. */
static uint32_t chron_build_chain_clusters(chron_state *st) {
    typedef struct { int32_t tag; uint32_t region; uint32_t category; uint64_t lo, hi; int used; } tag_group;
    tag_group groups[CHRON_MAX_RAW_CHAIN];
    uint32_t n_groups = 0;

    for (uint32_t i = 0; i < st->n_raw_chain; i++) {
        chron_raw_chain_event *e = &st->raw_chain[i];
        int found = -1;
        for (uint32_t g = 0; g < n_groups; g++) {
            if (groups[g].tag == e->chain_tag) { found = (int)g; break; }
        }
        if (found < 0) {
            groups[n_groups].tag = e->chain_tag;
            groups[n_groups].region = e->region;
            groups[n_groups].category = e->category;
            groups[n_groups].lo = groups[n_groups].hi = 0;
            groups[n_groups].used = 1;
            n_groups++;
        }
    }

    uint32_t n_merged = 0;
    for (uint32_t g = 0; g < n_groups; g++) {
        if (!groups[g].used) continue;
        for (uint32_t h = g + 1; h < n_groups; h++) {
            if (groups[h].used && groups[h].region == groups[g].region && groups[h].category == groups[g].category) {
                groups[h].used = 0;
            }
        }
        chron_push_candidate(st, CTYPE_CHAIN, groups[g].category, groups[g].region, 0.0,
                              groups[g].tag, groups[g].lo, groups[g].hi);
        n_merged++;
    }
    st->n_raw_chain = 0;
    return n_merged;
}

static int chron_region_has_lineage_member(const om_world *w, uint32_t region_idx) {
    uint32_t n = om_lineage_count(w);
    for (uint32_t i = 0; i < n; i++) {
        if (om_lineage_member_in_region(w, om_lineage_id_at(w, i), region_idx)) return 1;
    }
    return 0;
}

/* R-067-01: a lineage member lives in the region, or the attached character
 * is in the lineage, or the region is the last mission's region. */
static int chron_is_lineage_event(const om_world *w, uint32_t lineage_id, uint32_t region_idx,
                                   uint32_t attached_character_id, uint32_t mission_region) {
    if (region_idx == mission_region) return 1;
    if (attached_character_id != 0 && om_character_lineage_id(w, attached_character_id) == lineage_id) return 1;
    return om_lineage_member_in_region(w, lineage_id, region_idx);
}

/* ALG-50 with only the lineage term derivable from region_idx alone; the
 * mission-region, attached-character and chain-length terms need per-event
 * context this entry point is not given. */
static double chron_score_event(const om_world *w, uint32_t region_idx, uint32_t tier, double delta_sum) {
    double base = chron_score_base(tier, delta_sum);
    double mult = chron_context_multiplier(0, 0, 0, chron_region_has_lineage_member(w, region_idx));
    return base * mult;
}

/* ALG-51 step 2, "none" case: with no lineage cluster among the candidates,
 * one lineage_quiet cluster for the first lineage, in its first active
 * member's region, else its last history region. */
static void chron_add_quiet_lineage_cluster(const om_world *w, chron_state *st) {
    for (uint32_t i = 0; i < st->n_candidates; i++) {
        if (st->candidates[i].type == CTYPE_LINEAGE) return;
    }
    if (om_lineage_count(w) == 0) return;
    uint32_t id = om_lineage_id_at(w, 0);
    int32_t region = om_lineage_first_member_region(w, id);
    if (region < 0) {
        for (uint32_t k = 0; om_lineage_history_region(w, id, k) >= 0; k++) region = om_lineage_history_region(w, id, k);
    }
    if (region < 0) return;
    chron_push_lineage_candidate(st, id, (uint32_t)region, 0.0);
}

/* Stable descending-score insertion sort -- qsort's tie-break order is
 * implementation-defined (libm_lint flags it), and the determinism contract
 * requires byte-identical behavior across platforms. n stays small (bounded
 * by CHRON_MAX_CANDIDATES), so O(n^2) is fine. */
static void chron_sort_by_score_desc(om_chronicle_cluster *arr, uint32_t n) {
    for (uint32_t i = 1; i < n; i++) {
        om_chronicle_cluster key = arr[i];
        uint32_t j = i;
        while (j > 0 && arr[j - 1].peak_score < key.peak_score) {
            arr[j] = arr[j - 1];
            j--;
        }
        arr[j] = key;
    }
}

/* Category ids used as a hash bucket index below never exceed CAT_CONSEQUENCE_MIXED
 * (32); sized generously past that. */
#define CHRON_SELECTION_CAT_BUCKETS 64

/* ALG-52 Selection: consequence clusters, then lineage clusters, then the
 * rest by peak score descending, skipping a category already used twice,
 * until CHRONICLE_MAX_ENTRIES; if still under CHRONICLE_MIN_ENTRIES, add
 * skipped clusters in score order regardless of the cap. */
static void chron_run_selection(om_world *w) {
    chron_state *st = chron(w);
    om_chronicle_cluster others[CHRON_MAX_CANDIDATES];
    uint32_t n_others = 0;
    uint32_t cat_count[CHRON_SELECTION_CAT_BUCKETS];
    memset(cat_count, 0, sizeof(cat_count));

    if (st->n_candidates == 0) return;
    chron_add_quiet_lineage_cluster(w, st);
    st->n_clusters = 0;
    st->n_entries = 0;
    memset(st->cluster_lineage, 0xFF, sizeof(st->cluster_lineage));

    for (uint32_t i = 0; i < st->n_candidates && st->n_clusters < CHRON_MAX_FINAL; i++) {
        if (st->candidates[i].type == CTYPE_CONSEQUENCE) {
            st->clusters[st->n_clusters++] = st->candidates[i];
        }
    }
    for (uint32_t i = 0; i < st->n_candidates && st->n_clusters < CHRON_MAX_FINAL; i++) {
        if (st->candidates[i].type == CTYPE_LINEAGE) {
            st->cluster_lineage[st->n_clusters] = st->candidate_lineage[i];
            st->clusters[st->n_clusters++] = st->candidates[i];
        }
    }
    for (uint32_t i = 0; i < st->n_candidates; i++) {
        if (st->candidates[i].type != CTYPE_CONSEQUENCE && st->candidates[i].type != CTYPE_LINEAGE) {
            others[n_others++] = st->candidates[i];
        }
    }
    chron_sort_by_score_desc(others, n_others);

    int taken[CHRON_MAX_CANDIDATES];
    memset(taken, 0, sizeof(int) * n_others);

    for (uint32_t i = 0; i < n_others && st->n_clusters < OM_CHRONICLE_MAX_ENTRIES; i++) {
        uint32_t cat = others[i].category % CHRON_SELECTION_CAT_BUCKETS;
        if (cat_count[cat] >= OM_CHRON_CATEGORY_CAP) continue;
        st->clusters[st->n_clusters++] = others[i];
        cat_count[cat]++;
        taken[i] = 1;
    }

    if (st->n_clusters < OM_CHRONICLE_MIN_ENTRIES) {
        for (uint32_t i = 0; i < n_others && st->n_clusters < OM_CHRONICLE_MIN_ENTRIES; i++) {
            if (taken[i]) continue;
            st->clusters[st->n_clusters++] = others[i];
            taken[i] = 1;
        }
    }
}

/* S-065 R-065-07: the opening jump has no consequence/lineage history yet --
 * 3 to 5 synthetic regional entries, cycling categories so the per-category
 * cap never trims below the minimum. */
static void chron_synth_opening(om_world *w) {
    chron_state *st = chron(w);
    static const uint32_t regional_cats[OM_CHRON_N_REGIONAL_CATEGORIES] = {
        CAT_REGIONAL_STABLE, CAT_REGIONAL_GROWTH, CAT_REGIONAL_DECLINE, CAT_REGIONAL_FACTION_SHIFT,
    };
    uint32_t n = w->n_regions;
    if (n < OM_CHRON_OPENING_MIN_ENTRIES) n = OM_CHRON_OPENING_MIN_ENTRIES;
    if (n > OM_CHRON_OPENING_MAX_ENTRIES) n = OM_CHRON_OPENING_MAX_ENTRIES;
    st->n_clusters = 0;
    st->n_entries = 0;
    memset(st->cluster_lineage, 0xFF, sizeof(st->cluster_lineage));
    for (uint32_t i = 0; i < n && st->n_clusters < CHRON_MAX_FINAL; i++) {
        om_chronicle_cluster *c = &st->clusters[st->n_clusters++];
        c->type = CTYPE_REGIONAL;
        c->category = regional_cats[i % OM_CHRON_N_REGIONAL_CATEGORIES];
        c->region = i % (w->n_regions ? w->n_regions : 1);
        c->peak_score = 0.0;
        c->chain_tag = -1;
        c->start_tick = 0;
        c->end_tick = 0;
    }
}

/* ALG-53 assembly over the final selected clusters. Concatenates surviving
 * (post cross-entry dedup, R-068-07) base texts into the scroll buffer;
 * entry_count/get_cluster/count_by_type stay driven by st->clusters, which
 * this does not modify -- only the scroll TEXT is deduplicated here. */
static void chron_assemble_all(om_world *w, uint64_t seed) {
    chron_state *st = chron(w);
    uint64_t rng = seed;
    char bases[CHRON_MAX_FINAL][1024];
    char expandeds[CHRON_MAX_FINAL][1600];
    int ok[CHRON_MAX_FINAL];
    int32_t frags[CHRON_MAX_FINAL][3];
    uint32_t n_seen_regions = 0;
    uint32_t seen_regions[CHRON_MAX_FINAL];

    for (uint32_t i = 0; i < st->n_clusters; i++) {
        uint32_t eff_cat = chron_effective_category(&st->clusters[i]);
        ok[i] = chron_assemble(w, eff_cat, st->clusters[i].region, &rng,
                                bases[i], sizeof(bases[i]), expandeds[i], sizeof(expandeds[i]), frags[i]);
        if (ok[i]) {
            int first = 1;
            for (uint32_t j = 0; j < n_seen_regions; j++) {
                if (seen_regions[j] == st->clusters[i].region) { first = 0; break; }
            }
            if (first) {
                seen_regions[n_seen_regions++] = st->clusters[i].region;
                char mention[160];
                chron_render_region_mention(w, st->clusters[i].region, 1, mention, sizeof(mention));
                const char *bare = chron_region_name(st->clusters[i].region);
                if (strstr(mention, ", held by") && !strstr(bases[i], ", held by")) {
                    char replaced[1024];
                    const char *pos = strstr(bases[i], bare);
                    if (pos) {
                        size_t prefix = (size_t)(pos - bases[i]);
                        snprintf(replaced, sizeof(replaced), "%.*s%s%s", (int)prefix, bases[i],
                                 mention, pos + strlen(bare));
                        snprintf(bases[i], sizeof(bases[i]), "%s", replaced);
                    }
                    pos = strstr(expandeds[i], bare);
                    if (pos) {
                        char replaced2[1600];
                        size_t prefix = (size_t)(pos - expandeds[i]);
                        snprintf(replaced2, sizeof(replaced2), "%.*s%s%s", (int)prefix, expandeds[i],
                                 mention, pos + strlen(bare));
                        snprintf(expandeds[i], sizeof(expandeds[i]), "%s", replaced2);
                    }
                }
            }
        }
    }

    chron_word_set kept_sets[CHRON_MAX_FINAL];
    uint32_t n_kept = 0;

    st->full_scroll_text[0] = '\0';
    st->n_entries = st->n_clusters;
    memset(st->entry_valid, 0, sizeof(st->entry_valid));
    size_t pos = 0;
    for (uint32_t i = 0; i < st->n_clusters; i++) {
        if (!ok[i]) continue;
        chron_word_set words;
        chron_content_words(bases[i], &words);
        int dup = 0;
        if (words.n > 0) {
            for (uint32_t k = 0; k < n_kept; k++) {
                uint32_t overlap = chron_word_set_overlap(&words, &kept_sets[k]);
                uint32_t denom_a = chron_word_set_unique_count(&words);
                uint32_t denom_b = chron_word_set_unique_count(&kept_sets[k]);
                uint32_t denom = denom_a < denom_b ? denom_a : denom_b;
                if (denom > 0 && (double)overlap / (double)denom >= OM_CHRON_DEDUP_OVERLAP_THRESHOLD) {
                    dup = 1;
                    break;
                }
            }
        }
        if (dup) continue;
        kept_sets[n_kept] = words;
        n_kept++;
        om_chronicle_entry *ent = &st->entries[i];
        memset(ent, 0, sizeof(*ent));
        st->entry_valid[i] = 1;
        ent->id = i;
        ent->category = chron_effective_category(&st->clusters[i]);
        ent->region = st->clusters[i].region;
        memcpy(ent->fragment_ids, frags[i], sizeof(ent->fragment_ids));
        ent->region_ref = (int32_t)st->clusters[i].region;
        ent->faction_ref = om_region_owner(w, st->clusters[i].region);
        ent->lineage_ref = st->cluster_lineage[i];
        ent->start_tick = st->clusters[i].start_tick;
        ent->end_tick = st->clusters[i].end_tick;
        snprintf(ent->base_text, sizeof(ent->base_text), "%.511s", bases[i]);
        snprintf(ent->expanded_text, sizeof(ent->expanded_text), "%.1023s", expandeds[i]);
        int n = snprintf(st->full_scroll_text + pos, CHRON_FULL_TEXT_CAP - pos, "%s%s",
                          pos > 0 ? "\n\n" : "", bases[i]);
        if (n > 0) pos += (size_t)n;
        if (pos >= CHRON_FULL_TEXT_CAP) break;
    }
}

/* ---- fragment library introspection (S-071) ---- */

static uint32_t chron_fragment_counts(uint32_t sparse_category, uint32_t type) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < CHRON_N_FRAGMENTS; i++) {
        if (CHRON_FRAGMENTS[i].category == sparse_category && CHRON_FRAGMENTS[i].type == type) n++;
    }
    return n;
}

/* ---- text-entry dedup (R-068-07, S068 test seam) ---- */

static chron_text_entry *chron_find_text_entry(chron_state *st, uint32_t id) {
    for (uint32_t i = 0; i < st->n_text_entries; i++) {
        if (st->text_entries[i].used && st->text_entries[i].id == id) return &st->text_entries[i];
    }
    return NULL;
}

/* ---- keyframe / mock-entry lookups (S-069) ---- */

static chron_entry_state *chron_find_entry_state(chron_state *st, uint32_t id, int create) {
    for (uint32_t i = 0; i < st->n_entry_states; i++) {
        if (st->entry_states[i].used && st->entry_states[i].id == id) return &st->entry_states[i];
    }
    if (create && st->n_entry_states < CHRON_MAX_ENTRY_STATES) {
        chron_entry_state *e = &st->entry_states[st->n_entry_states++];
        e->id = id;
        e->is_printing = 0;
        e->used = 1;
        return e;
    }
    return NULL;
}

/* ==================================================================== */
/* Public ABI (csrc/ouroboros_sim.h "generated from signatures.toml:
 * chronicle.c" section). */
/* ==================================================================== */

void om_chronicle_add_chain_event(om_world *w, int32_t chain_tag, uint32_t region_idx, uint32_t category) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->n_raw_chain >= CHRON_MAX_RAW_CHAIN) return;
    chron_raw_chain_event *e = &st->raw_chain[st->n_raw_chain++];
    e->chain_tag = chain_tag;
    e->region = region_idx;
    e->category = category;
}

void om_chronicle_add_cluster_direct(om_world *w, uint32_t cluster_type, uint32_t category, double score) {
    if (!w) return;
    chron_push_candidate(chron(w), cluster_type, category, 0, score, -1, 0, 0);
}

void om_chronicle_add_consequence_event(om_world *w, uint32_t region_idx, uint32_t outcome) {
    if (!w) return;
    chron_push_candidate(chron(w), CTYPE_CONSEQUENCE, outcome, region_idx, 0.0, -1, 0, 0);
}

void om_chronicle_add_event(om_world *w, uint32_t region_idx, double score) {
    if (!w) return;
    chron_state *st = chron(w);
    /* ALG-51 step 4: a region whose owner changed during the window is a faction shift. */
    uint32_t category = CAT_REGIONAL_STABLE;
    for (uint32_t i = 0; i < st->n_ownership_changes && !st->own_stale; i++) {
        if (st->ownership_changes[i].region == region_idx) { category = CAT_REGIONAL_FACTION_SHIFT; break; }
    }
    chron_push_candidate(st, CTYPE_REGIONAL, category, region_idx, score, -1, 0, 0);
}

void om_chronicle_add_lineage_event(om_world *w, uint32_t lineage_id, uint32_t region_idx, double score) {
    if (!w) return;
    chron_push_lineage_candidate(chron(w), lineage_id, region_idx, score);
}

void om_chronicle_add_mock_entry(om_world *w, uint32_t entry_id, uint64_t start_tick, uint64_t end_tick) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->n_mock_entries >= CHRON_MAX_MOCK_ENTRIES) return;
    chron_mock_entry *e = &st->mock_entries[st->n_mock_entries++];
    e->id = entry_id;
    e->start_tick = start_tick;
    e->end_tick = end_tick;
    e->used = 1;
}

void om_chronicle_add_ownership_change_event(om_world *w, uint32_t region_idx, uint64_t tick) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->own_stale) { st->n_ownership_changes = 0; st->own_stale = 0; }
    if (st->n_ownership_changes >= CHRON_MAX_OWNERSHIP_CHANGES) return;
    chron_ownership_change *e = &st->ownership_changes[st->n_ownership_changes++];
    e->region = region_idx;
    e->tick = tick;
}

void om_chronicle_add_raw_entry(om_world *w, uint32_t entry_id, const char *text) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->n_text_entries >= CHRON_MAX_TEXT_ENTRIES) return;
    chron_text_entry *e = &st->text_entries[st->n_text_entries++];
    e->id = entry_id;
    snprintf(e->text, sizeof(e->text), "%s", text ? text : "");
    e->retained = 1;
    e->used = 1;
}

const char *om_chronicle_apply_slot_echo_anaphora(om_world *w, const char *fragment1_slot, const char *fragment2_slot) {
    static char out[CHRON_SLOT_VALUE_CAP];
    (void)w;
    if (fragment1_slot && chron_word_count(fragment1_slot) >= OM_CHRON_ECHO_WORD_THRESHOLD) {
        snprintf(out, sizeof(out), "%s", "what followed");
    } else {
        snprintf(out, sizeof(out), "%s", fragment2_slot ? fragment2_slot : "");
    }
    return out;
}

const char *om_chronicle_apply_word_echo_synonym(om_world *w, const char *text) {
    static char out[1024];
    (void)w;
    snprintf(out, sizeof(out), "%s", text ? text : "");
    chron_dedup_echo_words(out, sizeof(out));
    return out;
}

int om_chronicle_assemble_cluster_entry(om_world *w, uint32_t category, uint32_t region_idx, om_chronicle_entry *out_entry) {
    if (!w || !out_entry) return 0;
    /* Deterministic per-(category, region) seed for this direct-call seam;
     * no jump start tick is given here (ALG-53's own seeding is
     * om_chronicle_assemble_with_seed's job). CHRON_RNG_GOLDEN doubles as
     * an odd mixing constant. */
    uint64_t rng = (uint64_t)category * CHRON_RNG_GOLDEN + region_idx;
    char base[CHRON_BASE_TEXT_CAP], expanded[CHRON_EXPANDED_TEXT_CAP];
    int32_t frags[3];
    int ok = chron_assemble(w, category, region_idx, &rng, base, sizeof(base), expanded, sizeof(expanded), frags);
    memset(out_entry, 0, sizeof(*out_entry));
    out_entry->fragment_ids[0] = -1;
    out_entry->fragment_ids[1] = -1;
    out_entry->fragment_ids[2] = -1;
    out_entry->region_ref = -1;
    out_entry->faction_ref = -1;
    out_entry->lineage_ref = -1;
    if (!ok) return 0;
    memcpy(out_entry->fragment_ids, frags, sizeof(frags));
    out_entry->region_ref = (int32_t)region_idx;
    out_entry->faction_ref = om_region_owner(w, region_idx);
    out_entry->category = category;
    out_entry->region = region_idx;
    snprintf(out_entry->base_text, sizeof(out_entry->base_text), "%s", base);
    snprintf(out_entry->expanded_text, sizeof(out_entry->expanded_text), "%s", expanded);
    return 1;
}

void om_chronicle_assemble_with_seed(om_world *w, uint64_t seed) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->n_candidates == 0 && st->n_clusters == 0) {
        chron_synth_opening(w);
    } else {
        chron_run_selection(w);
    }
    chron_assemble_all(w, seed);
    st->n_candidates = 0;
    st->own_stale = 1;
}

uint32_t om_chronicle_build_chain_clusters(om_world *w) {
    if (!w) return 0;
    return chron_build_chain_clusters(chron(w));
}

void om_chronicle_build_opening_scroll(om_world *w) {
    if (!w) return;
    chron_synth_opening(w);
}

double om_chronicle_calculate_score(const om_world *w, uint32_t tier, double delta_sum, int in_mission_region,
                                     int has_character, uint32_t chain_length, int has_lineage_member) {
    (void)w;
    double base = chron_score_base(tier, delta_sum);
    double mult = chron_context_multiplier(in_mission_region, has_character, chain_length, has_lineage_member);
    return base * mult;
}

uint32_t om_chronicle_categorize_chain_cluster(const om_world *w, const char *template_name, uint32_t n_events,
                                                double net_mil, double net_eco, double net_ten) {
    (void)w;
    return chron_categorize_chain_cluster(template_name ? template_name : "", n_events, net_mil, net_eco, net_ten);
}

uint32_t om_chronicle_categorize_lineage_cluster(const om_world *w, const char *template_name,
                                                  double net_eco, double net_mil, double net_ten) {
    (void)w;
    return chron_categorize_lineage_cluster(template_name ? template_name : "", net_eco, net_mil, net_ten);
}

uint32_t om_chronicle_categorize_regional_cluster(const om_world *w, int has_conquest_or_revolt, double net_eco_pop) {
    (void)w;
    return chron_categorize_regional_cluster(has_conquest_or_revolt, net_eco_pop);
}

const char *om_chronicle_category_name(uint32_t category) {
    return chron_category_name(category);
}

uint32_t om_chronicle_chain_category_count(const om_world *w) {
    (void)w;
    return OM_CHRON_N_CHAIN_CATEGORIES;
}

double om_chronicle_context_multiplier(const om_world *w, int in_mission_region, int has_character,
                                        uint32_t chain_length, int has_lineage_member) {
    (void)w;
    return chron_context_multiplier(in_mission_region, has_character, chain_length, has_lineage_member);
}

uint32_t om_chronicle_count_by_type(const om_world *w, uint32_t cluster) {
    const chron_state *st = chron_ro(w);
    if (!st) return 0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < st->n_clusters; i++) {
        if (st->clusters[i].type == cluster) n++;
    }
    return n;
}

void om_chronicle_dedup_content_words(om_world *w, double threshold) {
    if (!w) return;
    chron_state *st = chron(w);
    if (st->n_text_entries == 0) return;
    chron_word_set kept_sets[CHRON_MAX_TEXT_ENTRIES];
    uint32_t n_kept = 0;
    for (uint32_t i = 0; i < st->n_text_entries; i++) {
        chron_word_set words;
        chron_content_words(st->text_entries[i].text, &words);
        int dup = 0;
        for (uint32_t k = 0; k < n_kept && words.n > 0; k++) {
            uint32_t overlap = chron_word_set_overlap(&words, &kept_sets[k]);
            uint32_t da = chron_word_set_unique_count(&words);
            uint32_t db = chron_word_set_unique_count(&kept_sets[k]);
            uint32_t denom = da < db ? da : db;
            if (denom > 0 && (double)overlap / (double)denom >= threshold) { dup = 1; break; }
        }
        if (dup) {
            st->text_entries[i].retained = 0;
        } else {
            st->text_entries[i].retained = 1;
            kept_sets[n_kept++] = words;
        }
    }
}

void om_chronicle_dismiss_expanded(om_world *w) {
    if (!w) return;
    chron(w)->paused = 0;
}

void om_chronicle_distill_and_assemble(om_world *w) {
    if (!w) return;
    chron_run_selection(w);
    chron_assemble_all(w, w->tick);
    chron(w)->n_candidates = 0;
    chron(w)->own_stale = 1;
}

uint32_t om_chronicle_entry_count(const om_world *w) {
    const chron_state *st = chron_ro(w);
    return st ? st->n_clusters : 0;
}

int om_chronicle_entry_is_retained(const om_world *w, uint32_t entry_id) {
    chron_state *st = (chron_state *)chron_ro(w);
    if (!st) return 0;
    chron_text_entry *e = chron_find_text_entry(st, entry_id);
    return e ? e->retained : 0;
}

int om_chronicle_fragment_batch_exceeds_rejection_limit(const om_world *w, uint32_t rejected_count, uint32_t total_count) {
    (void)w;
    if (total_count == 0) return 0;
    return ((double)rejected_count / (double)total_count) > OM_CHRON_BATCH_REJECTION_LIMIT;
}

uint32_t om_chronicle_fragment_category_count(const om_world *w) {
    (void)w;
    return OM_CHRON_N_CATEGORIES;
}

int om_chronicle_fragment_check_near_duplicate(const om_world *w, const char *p0, const char *p1) {
    (void)w;
    if (!p0 || !p1) return 0;
    return chron_edit_distance(p0, p1) <= OM_CHRON_NEAR_DUP_EDIT_THRESHOLD;
}

void om_chronicle_fragment_inject_invalid_slot(om_world *w, uint32_t category, const char *invalid_slot) {
    if (!w) return;
    chron_state *st = chron(w);
    st->invalid_fragment_injected = 1;
    st->invalid_fragment_category = category;
    snprintf(st->invalid_fragment_slot, sizeof(st->invalid_fragment_slot), "%s", invalid_slot ? invalid_slot : "");
}

void om_chronicle_fragment_library_load_launch(om_world *w) {
    if (!w) return;
    chron(w)->fragments_loaded = 1;
}

int om_chronicle_fragment_library_validate(const om_world *w) {
    const chron_state *st = chron_ro(w);
    if (st && st->invalid_fragment_injected && !chron_slot_is_valid(st->invalid_fragment_slot)) {
        return 1;
    }
    return 0;
}

int om_chronicle_fragment_pool_counts(const om_world *w, uint32_t category, om_fragment_pool_counts *out) {
    (void)w;
    if (!out) return 1;
    memset(out, 0, sizeof(*out));
    if (category >= OM_CHRON_N_CATEGORIES) return 1;
    uint32_t sparse = CHRON_DENSE_TO_SPARSE[category];
    out->openings = chron_fragment_counts(sparse, 0);
    out->details = chron_fragment_counts(sparse, 1);
    out->closings = chron_fragment_counts(sparse, 2);
    return 0;
}

void om_chronicle_generate_map_keyframes(om_world *w) {
    if (!w) return;
    chron_state *st = chron(w);
    st->n_keyframes = 0;
    for (uint32_t i = 0; i < st->n_mock_entries && st->n_keyframes < CHRON_MAX_KEYFRAMES; i++) {
        st->keyframes[st->n_keyframes++] = st->mock_entries[i].start_tick;
    }
    for (uint32_t i = 0; i < st->n_ownership_changes && st->n_keyframes < CHRON_MAX_KEYFRAMES; i++) {
        st->keyframes[st->n_keyframes++] = st->ownership_changes[i].tick;
    }
}

int om_chronicle_get_cluster(const om_world *w, uint32_t entry, om_chronicle_cluster *out) {
    const chron_state *st = chron_ro(w);
    if (!st || !out || entry >= st->n_clusters) return 0;
    *out = st->clusters[entry];
    return 1;
}

const char *om_chronicle_get_full_scroll_text(const om_world *w) {
    const chron_state *st = chron_ro(w);
    return st ? st->full_scroll_text : "";
}

int om_chronicle_handle_click(om_world *w, uint32_t entry_id) {
    if (!w) return 0;
    chron_state *st = chron(w);
    chron_entry_state *e = chron_find_entry_state(st, entry_id, 1);
    if (!e || e->is_printing) return 0;
    st->paused = 1;
    return 1;
}

int om_chronicle_has_keyframe_at_tick(const om_world *w, uint64_t p0) {
    const chron_state *st = chron_ro(w);
    if (!st) return 0;
    for (uint32_t i = 0; i < st->n_keyframes; i++) {
        if (st->keyframes[i] == p0) return 1;
    }
    return 0;
}

int om_chronicle_has_keyframe_in_range(const om_world *w, uint64_t p0, uint64_t p1) {
    const chron_state *st = chron_ro(w);
    if (!st) return 0;
    for (uint32_t i = 0; i < st->n_keyframes; i++) {
        if (st->keyframes[i] >= p0 && st->keyframes[i] <= p1) return 1;
    }
    return 0;
}

int om_chronicle_is_lineage_event(const om_world *w, uint32_t lineage_id, uint32_t region_idx,
                                   uint32_t attached_character_id, uint32_t mission_region) {
    return chron_is_lineage_event(w, lineage_id, region_idx, attached_character_id, mission_region);
}

int om_chronicle_is_paused(const om_world *w) {
    const chron_state *st = chron_ro(w);
    return st ? st->paused : 0;
}

uint32_t om_chronicle_lineage_category_count(const om_world *w) {
    (void)w;
    return OM_CHRON_N_LINEAGE_CATEGORIES;
}

int om_chronicle_map_is_master_clock(const om_world *w) {
    (void)w;
    return 1;
}

/* Score-diversity period for the synthetic candidates below -- just needs
 * to differ from OM_CHRON_N_REGIONAL_CATEGORIES so scores and categories
 * don't lock-step; not an ALG/epic-cited value. */
#define CHRON_MOCK_SCORE_PERIOD 5
#define CHRON_MOCK_SCORE_BASE 5.0
#define CHRON_MOCK_SCORE_STEP 0.5

void om_chronicle_mock_populate_events(om_world *w, uint32_t n_events) {
    if (!w) return;
    chron_state *st = chron(w);
    static const uint32_t regional_cats[OM_CHRON_N_REGIONAL_CATEGORIES] = {
        CAT_REGIONAL_STABLE, CAT_REGIONAL_GROWTH, CAT_REGIONAL_DECLINE, CAT_REGIONAL_FACTION_SHIFT,
    };
    uint32_t n_regions = w->n_regions ? w->n_regions : 1;
    for (uint32_t i = 0; i < n_events; i++) {
        uint32_t cat = regional_cats[i % OM_CHRON_N_REGIONAL_CATEGORIES];
        uint32_t region = i % n_regions;
        double score = CHRON_MOCK_SCORE_BASE + (double)(i % CHRON_MOCK_SCORE_PERIOD) * CHRON_MOCK_SCORE_STEP;
        chron_push_candidate(st, CTYPE_REGIONAL, cat, region, score, -1, 0, 0);
    }
}

double om_chronicle_presentation_entry_hold_sec(const om_world *w) {
    (void)w;
    return OM_CHRON_ENTRY_HOLD_SEC;
}

double om_chronicle_presentation_map_width_ratio(const om_world *w) {
    (void)w;
    return OM_CHRON_MAP_WIDTH_RATIO;
}

double om_chronicle_presentation_slide_in_sec(const om_world *w) {
    (void)w;
    return OM_CHRON_SLIDE_IN_SEC;
}

double om_chronicle_presentation_slide_out_sec(const om_world *w) {
    (void)w;
    return OM_CHRON_SLIDE_OUT_SEC;
}

double om_chronicle_presentation_word_cadence_sec(const om_world *w) {
    (void)w;
    return OM_CHRON_WORD_CADENCE_SEC;
}

double om_chronicle_presentation_word_fade_sec(const om_world *w) {
    (void)w;
    return OM_CHRON_WORD_FADE_SEC;
}

uint32_t om_chronicle_regional_category_count(const om_world *w) {
    (void)w;
    return OM_CHRON_N_REGIONAL_CATEGORIES;
}

const char *om_chronicle_render_character_rank(const om_world *w, uint32_t character_id) {
    om_character_record rec;
    if (om_character_get_record(w, character_id, &rec) != 0) return chron_rank_name(CHRON_RANK_UNKNOWN);
    return chron_rank_name(rec.rank);
}

const char *om_chronicle_render_region_mention(const om_world *w, uint32_t region_idx, int is_first_mention) {
    static char out[160];
    chron_render_region_mention(w, region_idx, is_first_mention, out, sizeof(out));
    return out;
}

uint32_t om_chronicle_rendered_entry_count(const om_world *w) {
    const chron_state *st = chron_ro(w);
    return st ? st->n_clusters : 0;
}

double om_chronicle_score_base(const om_world *w, uint32_t tier, double delta_sum) {
    (void)w;
    return chron_score_base(tier, delta_sum);
}

double om_chronicle_score_event(const om_world *w, uint32_t region_idx, uint32_t tier, double delta_sum) {
    return chron_score_event(w, region_idx, tier, delta_sum);
}

void om_chronicle_select_clusters(om_world *w) {
    if (!w) return;
    chron_run_selection(w);
}

uint32_t om_chronicle_selected_category_count(const om_world *w, uint32_t category) {
    const chron_state *st = chron_ro(w);
    if (!st) return 0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < st->n_clusters; i++) {
        if (st->clusters[i].category == category) n++;
    }
    return n;
}

void om_chronicle_set_entry_state(om_world *w, uint32_t entry_id, int is_printing) {
    if (!w) return;
    chron_entry_state *e = chron_find_entry_state(chron(w), entry_id, 1);
    if (e) e->is_printing = is_printing;
}

int om_chronicle_validate_event_template_prose(const om_world *w) {
    uint32_t n = om_event_template_count(w);
    for (uint32_t i = 0; i < n; i++) {
        const char *prose = om_event_template_chronicle_prose(w, i);
        if (!prose || !prose[0]) return 1;
    }
    return 0;
}

const char *om_event_template_chronicle_prose(const om_world *w, uint32_t template) {
    static char out[128];
    const char *name = om_event_template_name(w, template);
    if (!name) { out[0] = '\0'; return out; }
    size_t n = 0;
    for (const char *p = name; *p && n + 1 < sizeof(out); p++) {
        out[n++] = (char)tolower((unsigned char)*p);
    }
    out[n] = '\0';
    return out;
}

int om_chronicle_entry_get(const om_world *w, uint32_t index, om_chronicle_entry *out) {
    const chron_state *st = chron_ro(w);
    if (!st || !out || index >= st->n_entries || !st->entry_valid[index]) return 0;
    *out = st->entries[index];
    return 1;
}

int om_chronicle_add_regional_event(om_world *w, uint32_t region_idx, uint32_t category, double score) {
    if (!w || region_idx >= w->n_regions) return 0;
    uint32_t type;
    if (category >= CAT_REGIONAL_FACTION_SHIFT && category <= CAT_REGIONAL_STABLE) type = CTYPE_REGIONAL;
    else if (category >= CAT_CHAIN_REVOLT_SPAWNED && category <= CAT_CHAIN_CRISIS_RESOLVED_BADLY) type = CTYPE_CHAIN;
    else return 0;
    chron_state *st = chron(w);
    if (st->n_candidates >= CHRON_MAX_CANDIDATES) return 0;
    chron_push_candidate(st, type, category, region_idx, score, -1, 0, 0);
    return 1;
}
