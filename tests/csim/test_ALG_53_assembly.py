"""ALG-53 Assembly (docs/bible/algorithms.md), rules R-068-01..R-068-08 (E-09, S-068).

Isolation: the assembly pieces reachable through ctypes, each on a hand-built input with the expected
result computed here from the row: seeded determinism (om_chronicle_assemble_with_seed), slot echo
(om_chronicle_apply_slot_echo_anaphora), word echo (om_chronicle_apply_word_echo_synonym), the first-mention
", held by <faction>" qualifier on an assembled scroll, and cross-entry dedup (om_chronicle_dedup_content_words
through om_chronicle_add_raw_entry). Constants: csrc/om_constants.h, else the file-local defines in
csrc/chronicle.c (dedup 0.40, echo 6 words, content word length 3).
unstated: the stop-word list, the synonym map contents and the anaphoric form chosen (the row names none),
Westley's.
unstated: how the "warnings at base >= 90 words or expanded >= 140" are surfaced; OM_CHRON_BASE_WORD_WARN and
OM_CHRON_EXPANDED_WORD_WARN are defined in chronicle.c and used nowhere, so no ctypes entry shows a warning;
not asserted, Westley's.
"""
import ctypes

import pytest

from alg_consts import const

DEDUP = const("CHRON_DEDUP_OVERLAP_THRESHOLD")
ECHO_WORDS = const("CHRON_ECHO_WORD_THRESHOLD")
MIN_LEN = const("CHRON_CONTENT_WORD_MIN_LEN")


def _s(p):
    return ctypes.string_at(p).decode("utf-8")


def _entries(lib, w, texts):
    for i, t in enumerate(texts, start=1):
        lib.om_chronicle_add_raw_entry(w, entry_id=i, text=t.encode())
    lib.om_chronicle_dedup_content_words(w, threshold=DEDUP)
    return [lib.om_chronicle_entry_is_retained(w, entry_id=i) for i in range(1, len(texts) + 1)]


# Content words below are invented (not in any stop list) and longer than MIN_LEN.
A5 = "zorvik quendal marrowby thistlen ostrakan"          # 5 unique content words


def test_ALG_53_dedup_drops_later_entry_at_exactly_the_threshold(lib, world_factory):
    """ALG-53 / R-068-07: overlap >= 0.40 of the smaller set drops the later entry; 2 of 5 shared words is exactly 0.40."""
    w = world_factory(n_regions=2)
    b_two_shared = "zorvik quendal pellamar dunwick rastolen"
    assert _entries(lib, w, [A5, b_two_shared]) == [1, 0]


def test_ALG_53_dedup_keeps_later_entry_below_the_threshold(lib, world_factory):
    """ALG-53: 1 of 5 shared (0.20) keeps both; the first entry always survives."""
    w = world_factory(n_regions=2)
    b_one_shared = "zorvik pellamar dunwick rastolen cormanth"
    assert _entries(lib, w, [A5, b_one_shared]) == [1, 1]


def test_ALG_53_dedup_denominator_is_the_smaller_set(lib, world_factory):
    """ALG-53: the ratio is over the smaller set. A has 10 content words, B has 5 and shares 2:
    2/5 = 0.40 drops B; over the larger set it would be 0.20 and keep B."""
    w = world_factory(n_regions=2)
    a10 = "zorvik quendal marrowby thistlen ostrakan velmoor pindrath gaulwick hobsender yarrowen"
    b5 = "zorvik quendal pellamar dunwick rastolen"
    assert _entries(lib, w, [a10, b5]) == [1, 0]


def test_ALG_53_dedup_ignores_words_of_three_letters_or_fewer_and_stop_words(lib, world_factory):
    """ALG-53: content words are > 3 letters and not stop words; shared short words and stop words never count."""
    assert MIN_LEN == 3
    w = world_factory(n_regions=2)
    a = "zorvik quendal marrowby the and for war cat"
    b = "pellamar dunwick rastolen the and for war cat"
    assert _entries(lib, w, [a, b]) == [1, 1]


def test_ALG_53_dedup_positive_control_nothing_shared_rejects_a_drop(lib, world_factory):
    """Positive control: entries with no shared content words are both kept, so an expectation that the later one drops must fail."""
    w = world_factory(n_regions=2)
    got = _entries(lib, w, [A5, "pellamar dunwick rastolen cormanth belwether"])
    with pytest.raises(AssertionError):
        assert got == [1, 0]


def test_ALG_53_slot_echo_replaces_a_slot_of_six_or_more_words(lib, world_factory):
    """ALG-53 / R-068-05: a slot value of >= 6 words in adjacent fragments is replaced by an anaphoric form; 5 words is kept."""
    w = world_factory(n_regions=2)
    six = " ".join(["word"] * ECHO_WORDS)
    five = " ".join(["word"] * (ECHO_WORDS - 1))
    assert _s(lib.om_chronicle_apply_slot_echo_anaphora(w, fragment1_slot=six.encode(), fragment2_slot=six.encode())) != six
    assert _s(lib.om_chronicle_apply_slot_echo_anaphora(w, fragment1_slot=five.encode(), fragment2_slot=five.encode())) == five


def test_ALG_53_word_echo_replaces_only_the_second_occurrence_of_a_content_word(lib, world_factory):
    """ALG-53 / R-068-06: the second occurrence of a 4+ letter non-stop word is replaced from the map; the first stays.
    'battle' has a map entry (map contents are unstated, so only 'one occurrence of the word remains' is asserted)."""
    w = world_factory(n_regions=2)
    out = _s(lib.om_chronicle_apply_word_echo_synonym(w, text=b"The battle raged until the battle ended."))
    assert out.lower().count("battle") == 1
    assert out.startswith("The battle raged")


def test_ALG_53_word_echo_leaves_stop_words_short_words_and_unmapped_words(lib, world_factory):
    """ALG-53: a repeated stop word, a word of 3 letters ('war' has a map entry but is too short), and a word with
    no synonym are all left alone."""
    w = world_factory(n_regions=2)
    text = "the war and the war zorvikan zorvikan"
    assert _s(lib.om_chronicle_apply_word_echo_synonym(w, text=text.encode())) == text


def _scroll(lib, world_factory, seed_world, assemble_seed):
    w = world_factory(n_regions=4, seed=seed_world)
    lib.om_chronicle_mock_populate_events(w, n_events=12)
    lib.om_chronicle_assemble_with_seed(w, seed=assemble_seed)
    return _s(lib.om_chronicle_get_full_scroll_text(w))


def test_ALG_53_same_seed_same_text_and_the_seed_matters(lib, world_factory):
    """ALG-53 / R-068-08: RNG seeded with the jump start tick: the same seed gives byte-identical text; over seeds 1..24
    more than one distinct text appears (positive control that the seed is live, not ignored)."""
    texts = {}
    for seed in range(1, 25):
        t1 = _scroll(lib, world_factory, 100, seed)
        t2 = _scroll(lib, world_factory, 100, seed)
        assert t1 and t1 == t2, f"seed {seed}"
        texts[seed] = t1
    assert len(set(texts.values())) > 1


def test_ALG_53_first_mention_of_an_owned_region_gets_held_by_once(lib, world_factory):
    """ALG-53: the first mention of a region appends ', held by <faction name>' (unless the entry already names both);
    later mentions of the same region do not. Four owned regions, 12 events cycling over them: at most one qualifier per region."""
    from conftest import set_owner
    w = world_factory(n_regions=4, seed=100)
    for r in range(4):
        set_owner(lib, w, r, faction_id=r % 2)
    lib.om_chronicle_mock_populate_events(w, n_events=12)
    lib.om_chronicle_assemble_with_seed(w, seed=7)
    text = _s(lib.om_chronicle_get_full_scroll_text(w))
    n = text.count(", held by")
    assert 1 <= n <= 4, text
