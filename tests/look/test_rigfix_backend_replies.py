"""look-judge-rig fixes, defects 2 and 3 (measurement 2026-11-24): (2) an empty reply was cached as a success (5 empty ollama replies frozen in the cache); (3) `parse()` used
fullmatch and rejected one line carrying several fields such as `class: count, count: 7` (33 of 38 ollama count UNSUREs). Spec piece 2: "Fails closed: any error, timeout or
unparseable answer is UNSURE, never PASS. Only successful back-end replies are cached (key: frame hash + prompt hash + back-end id), never failures."

Defined here (the spec leaves it open): a reply is parsed for the key the check's truth asks for. A line may carry several `key: value` fields separated by commas; the
requested key present with one value is that value. The requested key present with two different values is UNSURE; the same value twice is not ambiguous.
"""
import pytest

from conftest import check, make_png


def judge(*a, **k):
    from scripts.look.backends import judge as j
    return j(*a, **k)


def cache_files(tmp_path):
    return sorted((tmp_path / "cache").glob("*.json"))


def test_control_a_real_reply_is_cached_and_not_asked_twice(ollama, tmp_path):
    """Positive control (spec piece 2), green today: a successful reply writes one cache file and the second identical call makes no second request."""
    ollama.reply = lambda r: "count: 0"
    png = make_png(tmp_path / "a.png")
    assert judge(png, check("ollama"))["verdict"] == "PASS"
    assert judge(png, check("ollama"))["verdict"] == "PASS"
    assert len(ollama.requests) == 1 and len(cache_files(tmp_path)) == 1


@pytest.mark.parametrize("empty", ["", "   ", "\n\t \n"])
def test_empty_ollama_reply_is_unsure_and_not_cached(ollama, tmp_path, empty):
    """Spec piece 2 "only successful back-end replies are cached ... never failures": an empty or whitespace-only reply is UNSURE, leaves no cache file, and the next call
    asks the back end again (and can then PASS)."""
    png = make_png(tmp_path / "a.png")
    ollama.reply = lambda r: empty
    assert judge(png, check("ollama"))["verdict"] == "UNSURE"
    assert cache_files(tmp_path) == [], "the empty reply was frozen in the cache"
    ollama.reply = lambda r: "count: 0"
    assert judge(png, check("ollama"))["verdict"] == "PASS"
    assert len(ollama.requests) == 2


@pytest.mark.parametrize("empty", ["", "  \n"])
def test_empty_claude_reply_is_unsure_and_not_cached(claude, tmp_path, empty):
    """Spec piece 2, same rule for the claude back end: an empty reply is UNSURE and not cached; the next call asks again."""
    png = make_png(tmp_path / "a.png")
    claude.say(empty)
    assert judge(png, check("claude"))["verdict"] == "UNSURE"
    assert cache_files(tmp_path) == []
    claude.say("count: 0")
    assert judge(png, check("claude"))["verdict"] == "PASS"
    assert len(claude.calls()) == 2


@pytest.fixture
def say(ollama, tmp_path):
    n = [0]

    def _say(text, truth):
        n[0] += 1  # distinct prompt each call so the cache never answers
        ollama.reply = lambda r: text
        return judge(make_png(tmp_path / "a.png"), check("ollama", truth, prompt="q%d" % n[0]))
    return _say


def test_control_single_field_replies_still_parse(say):
    """Positive control (spec piece 2), green today: one-field replies and a bare yes keep their verdicts."""
    assert say("count: 7", {"count": 7})["verdict"] == "PASS"
    assert say("count: 8", {"count": 7})["verdict"] == "FAIL"
    assert say("yes", {"count": 7})["verdict"] == "UNSURE"


@pytest.mark.parametrize("text,truth,want", [
    ("class: count, count: 7", {"count": 7}, "PASS"),
    ("class: count, count: 8", {"count": 7}, "FAIL"),
    ("count: 7, class: count", {"count": 7}, "PASS"),
    ("class: apart, count: 3", {"class": "apart"}, "PASS"),
    ("class: stacked, count: 3", {"class": "apart"}, "FAIL"),
    ("count: 7, count: 7", {"count": 7}, "PASS"),
    ("coordinates: (10,20) (30,40), count: 2", {"coordinates": [[10, 20], [30, 40]]}, "PASS"),
])
def test_one_line_with_several_fields_answers_the_requested_key(say, text, truth, want):
    """Spec piece 2 "answers are parsed as class/count/coordinates": a line with several `key: value` fields is answered by the field the check asks for."""
    assert say(text, truth)["verdict"] == want


@pytest.mark.parametrize("text,truth,want", [
    ("count: 7, count: 8", {"count": 7}, "UNSURE"),
    ("count: 7, count: 8", {"count": 8}, "UNSURE"),
    ("class: apart, class: stacked", {"class": "apart"}, "UNSURE"),
    ("class: apart, count: 3", {"coordinates": [[1, 2]]}, None),
])
def test_ambiguous_or_missing_requested_key_never_passes(say, text, truth, want):
    """Spec piece 2 "unparseable answer is UNSURE, never PASS": two different values for the requested key are UNSURE (not PASS, not FAIL); a line without the requested key
    never passes."""
    v = say(text, truth)["verdict"]
    assert v != "PASS"
    if want:
        assert v == want
