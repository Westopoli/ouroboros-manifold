"""look-judge-rig spec piece 2 (backends): answers are parsed as class/count/coordinates and compared with truth."""
import pytest

from conftest import check, make_png


def judge(*a, **k):
    from scripts.look.backends import judge as j
    return j(*a, **k)


@pytest.fixture
def say(ollama, tmp_path):
    n = [0]

    def _say(text, truth):
        n[0] += 1  # distinct prompt each call so the cache never answers
        ollama.reply = lambda r: text
        return judge(make_png(tmp_path / "a.png"), check("ollama", truth, prompt="q%d" % n[0]))
    return _say


def test_class_match(say):
    """Piece 2: a named class is compared with the truth class."""
    assert say("class: stacked", {"class": "stacked"})["verdict"] == "PASS"
    assert say("class: apart", {"class": "stacked"})["verdict"] == "FAIL"


def test_count_match(say):
    """Piece 2: a count is compared with the truth count."""
    assert say("count: 3", {"count": 3})["verdict"] == "PASS"
    assert say("count: 4", {"count": 3})["verdict"] == "FAIL"


def test_coordinates_match(say):
    """Piece 2: coordinates are compared with the truth coordinates."""
    assert say("coordinates: (10,20) (30,40)", {"coordinates": [[10, 20], [30, 40]]})["verdict"] == "PASS"
    assert say("coordinates: (90,90)", {"coordinates": [[10, 20]]})["verdict"] == "FAIL"


def test_answer_field_is_the_parsed_value(say):
    """Piece 2: `answer` carries the parsed answer, `raw` the model text."""
    out = say("count: 3", {"count": 3})
    assert out["raw"].strip() == "count: 3" and out["answer"] not in (None, "")


@pytest.mark.parametrize("text", ["yes", "Yes.", "yes, they overlap", "YES"])
def test_bare_yes_is_unsure(say, text):
    """Piece 2: never trust a bare yes -> UNSURE."""
    assert say(text, {"count": 1})["verdict"] == "UNSURE"


@pytest.mark.parametrize("text", ["", "I cannot tell", "count: many", "\x00\xff garbage", "coordinates: ((("])
def test_unparseable_never_passes(say, text):
    """Piece 2: unparseable output => UNSURE or FAIL, never PASS."""
    assert say(text, {"count": 1})["verdict"] in ("UNSURE", "FAIL")


def test_wrong_kind_of_answer_never_passes(say):
    """Piece 2: a count answer to a class truth is not a match."""
    assert say("count: 1", {"class": "stacked"})["verdict"] in ("UNSURE", "FAIL")
