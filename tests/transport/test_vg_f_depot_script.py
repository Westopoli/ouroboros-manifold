"""Lane F, the Steam depot upload script (scripts/steam_app_build_5402100.vdf).

Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md lane F ("the depot script") and the Steam spec's
decision "one Steam depot per OS (game binary, pck, pipe exe)"; app id 5402100 (Westley, 2026-10-06). Stories
S-141/S-142 are playable only by someone who can install the build; R-141-01 (friends-only matches) needs the app.

Fenced: builders never edit this file. Depot ids are not specified anywhere, so the test pins only their
shape (three distinct integers other than the app id). The setlive policy is Westley's: see the _park_ file.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VDF = ROOT / "scripts/steam_app_build_5402100.vdf"


def _tokens(text: str) -> list[str]:
    return [a or b for a, b in re.findall(r'"([^"]*)"|([{}])', text)]


def _parse(text: str):
    """Tiny VDF reader: nested dict, keys lowercased, repeated keys kept in order via a list of pairs."""
    toks = _tokens(text)
    pos = 0

    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1
                return items
            key = t.lower()
            pos += 1
            if toks[pos] == "{":
                pos += 1
                items.append((key, block()))
            else:
                items.append((key, toks[pos]))
                pos += 1
        return items

    return block()


def _get(items, key):
    return [v for k, v in items if k == key]


def _load():
    assert VDF.exists(), "S-141: scripts/steam_app_build_5402100.vdf does not exist (depot script not built)"
    root = _parse(VDF.read_text())
    ab = _get(root, "appbuild")
    assert ab, "no appbuild block"
    return ab[0]


def test_control_the_vdf_reader_reads_a_sample():
    """CONTROL: the parser itself works, so an absent depot is not a parser miss."""
    s = '"appbuild" { "appid" "1" "depots" { "2" { "contentroot" "x" } "3" { "contentroot" "y" } } }'
    ab = _get(_parse(s), "appbuild")[0]
    assert _get(ab, "appid") == ["1"] and len(_get(_get(ab, "depots")[0], "2")) == 1


def test_appbuild_names_the_app():
    ab = _load()
    assert _get(ab, "appid") == ["5402100"], "the app id is 5402100 (Westley, 2026-10-06)"


def test_one_depot_per_os():
    """Steam spec: one depot per OS. Three numeric, distinct depot ids that are not the app id."""
    ab = _load()
    depots = _get(ab, "depots")
    assert depots, "no depots block"
    ids = [k for k, v in depots[0] if isinstance(v, list)]
    assert len(ids) == len(set(ids)) == 3, f"expected three distinct depots, got {ids}"
    assert all(i.isdigit() and i != "5402100" for i in ids), ids


def test_each_depot_ships_game_pck_and_pipe_for_its_os():
    """Each depot's file mapping covers the game binary, the pck and the OS's pipe exe (ouroboros_pipe[.exe])."""
    ab = _load()
    depots = _get(ab, "depots")[0]
    text = VDF.read_text()
    want = {"linux": "dist/linux", "windows": "dist/windows", "macos": "dist/macos"}
    seen = {}
    for did, body in depots:
        if not isinstance(body, list):
            continue
        roots = _get(body, "contentroot")
        assert roots, f"depot {did} has no ContentRoot"
        for os_name, frag in want.items():
            if frag in roots[0].replace("\\", "/"):
                seen[os_name] = did
    assert set(seen) == set(want), f"each OS needs a depot whose ContentRoot is under dist/<os>; got {seen}"
    assert "ouroboros_pipe.exe" in text and re.search(r"ouroboros_pipe(?!\.exe)", text), "the pipe exe is not mapped into the depots"
    assert ".pck" in text, "the pck is not mapped into the depots"


def test_build_description_and_output_dir_present():
    ab = _load()
    assert _get(ab, "desc") and _get(ab, "contentroot") is not None
    assert _get(ab, "buildoutput"), "no BuildOutput directory (the build log has to land somewhere)"
