"""look-judge-rig spec piece 2 (backends): cache keyed by frame hash + prompt hash + back-end id."""
from conftest import check, make_png


def judge(*a, **k):
    from scripts.look.backends import judge as j
    return j(*a, **k)


def test_second_identical_call_does_not_hit_server(ollama, tmp_path):
    """Piece 2: second call with same frame, prompt, back end is served from cache."""
    png = make_png(tmp_path / "a.png")
    ollama.reply = lambda r: "count: 0"
    first = judge(png, check("ollama"))
    second = judge(png, check("ollama"))
    assert len(ollama.requests) == 1
    assert first["verdict"] == second["verdict"] and first["raw"] == second["raw"]


def test_cache_keys_on_frame_content_not_path(ollama, tmp_path):
    """Piece 2: same bytes under another path hit; different bytes miss."""
    a = make_png(tmp_path / "a.png", b"SAME")
    b = make_png(tmp_path / "b.png", b"SAME")
    c = make_png(tmp_path / "c.png", b"DIFF")
    judge(a, check("ollama"))
    judge(b, check("ollama"))
    assert len(ollama.requests) == 1
    judge(c, check("ollama"))
    assert len(ollama.requests) == 2


def test_changed_prompt_misses(ollama, tmp_path):
    """Piece 2: changing the prompt misses the cache."""
    png = make_png(tmp_path / "a.png")
    judge(png, check("ollama", prompt="one"))
    judge(png, check("ollama", prompt="two"))
    assert len(ollama.requests) == 2


def test_changed_backend_misses(ollama, claude, tmp_path):
    """Piece 2: same frame and prompt on another back end misses the cache."""
    png = make_png(tmp_path / "a.png")
    claude.say("count: 0")
    judge(png, check("ollama"))
    judge(png, check("claude"))
    assert len(ollama.requests) == 1 and len(claude.calls()) == 1


def test_claude_cache_hit_spawns_no_process(claude, tmp_path):
    """Piece 2: cached claude answer spawns no second process."""
    png = make_png(tmp_path / "a.png")
    claude.say("count: 0")
    judge(png, check("claude"))
    judge(png, check("claude"))
    assert len(claude.calls()) == 1


def test_cache_written_under_configured_dir(ollama, tmp_path):
    """Piece 2: answer cache lives in the cache dir (default .cache/look/)."""
    judge(make_png(tmp_path / "a.png"), check("ollama"))
    assert any((tmp_path / "cache").rglob("*"))


def test_failures_are_not_cached_as_answers(tmp_path, monkeypatch, ollama):
    """Piece 2: a transient failure must not poison the cache; a later good answer is fetched."""
    png = make_png(tmp_path / "a.png")
    ollama.status = 500
    assert judge(png, check("ollama"))["verdict"] != "PASS"
    ollama.status = 200
    ollama.reply = lambda r: "count: 0"
    assert judge(png, check("ollama"))["verdict"] == "PASS"
