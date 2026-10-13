"""ALG-53 Assembly (docs/bible/algorithms.md), proving R-068-04 .. R-068-08 (S-068, E-09).

RNG seeded with the jump start tick; slot echo (same value of 6 or more words in adjacent fragments)
becomes an anaphoric form; word echo (4+ letters, non-stop word, second occurrence) is replaced from
the synonym map; the first mention of a region appends ', held by <faction name>'; cross-entry dedup
over content words (lowercase, more than 3 letters, non-stop) drops a later entry whose overlap with
any kept entry is at least 0.40 of the smaller set; the text carries no digits. Expectations are
computed here from those sentences; the synonym map is not read, only 'the second occurrence of a
mapped word changes and nothing else does'.
"""
import ctypes
import re

from conftest import OmChronicleCluster, OmChronicleEntry, set_owner

CHAIN, REGIONAL = 2, 3
STOP = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "its", "their",
        "was", "were", "had", "has", "that", "this", "which", "what", "as", "is", "it", "be", "been", "not", "no", "all",
        "each", "every", "into", "over", "than", "then", "when", "after", "before", "while", "until", "across", "beyond"}


def _text(ptr):
    return ctypes.string_at(ptr).decode()


def _echo(lib, w, text):
    return _text(lib.om_chronicle_apply_word_echo_synonym(w, text=text.encode()))


def _content(text):
    return {m for m in re.findall(r"[a-z]+", text.lower()) if len(m) > 3 and m not in STOP}


def _ref_retained(texts, threshold=0.40):
    kept, out = [], []
    for t in texts:
        words = _content(t)
        dup = False
        for k in kept:
            small = min(len(words), len(k))
            if small and len(words & k) / small >= threshold:
                dup = True
                break
        out.append(not dup)
        if not dup:
            kept.append(words)
    return out


def test_control_ALG_53_a_wrong_threshold_or_denominator_is_detected(lib, world_factory):
    """Positive control: a reference with threshold 0.60, or one dividing by the larger set, disagrees with the sim on the same texts."""
    texts = ["soldiers fought bravely across mountain valley defend homeland harvest",
             "soldiers fought bravely across river bridge toll granary"]
    assert _ref_retained(texts, threshold=0.60) != _ref_retained(texts)
    w = world_factory(n_regions=2)
    for i, t in enumerate(texts, start=1):
        lib.om_chronicle_add_raw_entry(w, entry_id=i, text=t.encode())
    lib.om_chronicle_dedup_content_words(w, threshold=0.40)
    got = [bool(lib.om_chronicle_entry_is_retained(w, entry_id=i)) for i in (1, 2)]
    assert got == _ref_retained(texts) != _ref_retained(texts, threshold=0.60)


def test_ALG_53_cross_entry_dedup_overlap_relative_to_the_smaller_set(lib, world_factory):
    """ALG-53 / R-068-07: the later entry is dropped when its overlap with any kept entry is >= 0.40 of the smaller content-word set (stop words and words of 3 letters or fewer do not count); dropped entries are not compared against later ones."""
    texts = [
        "soldiers fought bravely across mountain valley defend homeland harvest",          # kept, 7 content words
        "soldiers fought bravely across river bridge toll granary",                       # overlap 3 of 7 = 0.43 -> dropped
        "river bridge toll granary harvest tariffs merchants",                            # vs kept #1: harvest = 1/7; kept -> retained
        "merchants tariffs river bridge toll storm",                                      # vs #3: merchants tariffs river bridge toll = 5/6 -> dropped
        "dust over the old road and the old inn",                                         # unrelated -> retained
        "inn road dust",                                                                  # small set {dust, road}: vs #5 overlap 2/2 -> dropped
    ]
    w = world_factory(n_regions=2)
    for i, t in enumerate(texts, start=1):
        lib.om_chronicle_add_raw_entry(w, entry_id=i, text=t.encode())
    lib.om_chronicle_dedup_content_words(w, threshold=0.40)
    got = [bool(lib.om_chronicle_entry_is_retained(w, entry_id=i)) for i in range(1, len(texts) + 1)]
    assert got == _ref_retained(texts)
    assert got[0] and not any(got[i] for i in (1, 3, 5))  # the first always survives; the named duplicates go


def test_ALG_53_word_echo_replaces_only_the_second_occurrence_of_a_mapped_word(lib, world_factory):
    """ALG-53 / R-068-06: 'battle' (4+ letters, not a stop word, in the synonym map) is kept at its first occurrence and replaced at its second; a 3-letter word, a stop word and an unmapped word repeated twice are left alone."""
    w = world_factory(n_regions=2)
    out = _echo(lib, w, "The battle raged until dusk and the battle ended")
    assert out.startswith("The battle raged") and out.count("battle") == 1
    assert out.split()[-2] != "battle"
    for text in ("a war began and the war ended", "which road led to which hill", "the garrison held and the garrison endured"):
        assert _echo(lib, w, text) == text, text


def test_ALG_53_slot_echo_needs_the_same_value_of_six_or_more_words(lib, world_factory):
    """ALG-53 / R-068-05: the same slot value of 6+ words in adjacent fragments gives an anaphoric form; the same value of 5 words does not; two different 7-word values are not an echo, so the second stays as it is."""
    w = world_factory(n_regions=2)

    def echo(a, b):
        return _text(lib.om_chronicle_apply_slot_echo_anaphora(w, fragment1_slot=a.encode(), fragment2_slot=b.encode()))

    six = "the long dispute over the border"
    five = "the dispute over the border"
    assert echo(six, six) in ("what followed", "the outcome", "what came next")
    assert echo(five, five) == five
    other = "a quiet winter in the northern hills"
    assert echo(six, other) == other, "two different values of 6+ words are not a slot echo"


def test_ALG_53_first_mention_of_an_owned_region_appends_held_by_unless_unowned(lib, world_factory):
    """ALG-53 / R-068-04: the first mention reads '<region>, held by <faction>' for an owned region, later mentions the bare name, an unowned region never gets the qualifier."""
    w = world_factory(n_regions=3)
    set_owner(lib, w, 1, 2)
    set_owner(lib, w, 2, -1)
    first = _text(lib.om_chronicle_render_region_mention(w, region_idx=1, is_first_mention=1))
    later = _text(lib.om_chronicle_render_region_mention(w, region_idx=1, is_first_mention=0))
    unowned = _text(lib.om_chronicle_render_region_mention(w, region_idx=2, is_first_mention=1))
    assert first.startswith(later) and first[len(later):].startswith(", held by ") and len(first) > len(later) + len(", held by ")
    assert ", held by" not in later and ", held by" not in unowned


def _scroll(lib, world_factory, seed):
    w = world_factory(n_regions=4, seed=11)
    set_owner(lib, w, 0, 1)
    set_owner(lib, w, 1, 2)
    for ctype, cat, score in ((REGIONAL, 21, 6.0), (CHAIN, 10, 5.0), (CHAIN, 12, 4.0), (REGIONAL, 22, 3.0), (CHAIN, 15, 2.0)):
        lib.om_chronicle_add_cluster_direct(w, cluster_type=ctype, category=cat, score=score)
    lib.om_chronicle_select_clusters(w)
    lib.om_chronicle_assemble_with_seed(w, seed=seed)
    return _text(lib.om_chronicle_get_full_scroll_text(w))


def test_ALG_53_same_seed_same_text_and_different_seeds_differ(lib, world_factory):
    """ALG-53 / R-068-08: the same clusters with the same jump-start-tick seed give identical text; across 12 different seeds the text is not always the same (positive control: the seed matters)."""
    for seed in (0, 50, 137):
        a, b = _scroll(lib, world_factory, seed), _scroll(lib, world_factory, seed)
        assert a and a == b, seed
    texts = {_scroll(lib, world_factory, s) for s in range(1, 13)}
    assert len(texts) > 1


def test_ALG_53_assembled_text_has_no_digits_and_stays_under_the_word_limits(lib, world_factory):
    """ALG-53 / R-068-03: no raw number ever appears; base form under 90 words and expanded under 140 (the warning thresholds), for every category in two regions."""
    w = world_factory(n_regions=3)
    set_owner(lib, w, 0, 1)
    bad = []
    for category in (0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 30, 31, 32):
        for region in (0, 1):
            entry = OmChronicleEntry()
            ok = lib.om_chronicle_assemble_cluster_entry(w, category=category, region_idx=region, out_entry=ctypes.byref(entry))
            if not ok:
                continue
            base, exp = entry.base_text.decode(), entry.expanded_text.decode()
            if re.search(r"\d", base + exp) or len(base.split()) >= 90 or len(exp.split()) >= 140:
                bad.append((category, region, len(base.split()), len(exp.split())))
    assert not bad, bad
