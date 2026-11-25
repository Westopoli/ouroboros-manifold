# spec: the brief for piece LI5 (clips), 2026-11-24, no story file; interface docs/reports/2026-11-24-clip-pipeline-interface.md ("Scene change")
"""Clip pipeline, story `clip-pipeline` (Story: clip-pipeline, Tests: clips): `OM_FIT_EXTRA` on the fight replay scene.

Rule proved (the brief's words): "one fixed camera box for a set of fights (union of positions, so versions of one fight are comparable: `OM_FIT_EXTRA`-style env into
`scenes/proto/fight_replay/fight_replay.gd`, read how the scratch project copy `r6-clips/proj` did it)". The scratch copy reads `OM_FIT_EXTRA="x0,y0,x1,y1"` in
`_setup_camera` and widens the box of every position (and ground feature) to hold it; the margin and the fit run on the widened box.

The observable is `qa_state().camera.fit` (the scene reports the box it fitted, [x0, y0, x1, y1], margin included), read through the daemon like tests/qa/test_fight_replay.py.
Premises dumped (read from the scene today, fight snapshot.example with units walking 3 wu a frame, x 100..~180, y 50..58): `camera.fit` is four numbers; without the variable
the fit is the positions' box plus margin max(0.1 x larger extent, 100 wu), so it holds every unit and reaches 100 wu out on each side.

Controls (green today): test_control_*. Red today: the scene ignores OM_FIT_EXTRA, so the fit does not widen (test_extra_widens_the_fit_to_hold_the_box) and two chunks of one fight
given the whole fight's box still fit different boxes (test_two_chunks_with_one_extra_fit_one_camera).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "qa"))
sys.path.insert(0, str(ROOT / "tests" / "skilllab" / "integration"))
sys.path.insert(0, str(ROOT))

import clip_pipeline_support as S  # noqa: E402
from test_fight_replay import ReplayGame, _state  # noqa: E402
from daemon_client import pick_free_port  # noqa: E402


def _fit(monkeypatch, fight: Path, extra: str | None) -> list:
    monkeypatch.setenv("OM_FIGHT", str(fight))
    for var in ("OM_AUTOPLAY", "OM_SHOT_OUT", "OM_LAYOUT", "OM_FIT_EXTRA"):
        monkeypatch.delenv(var, raising=False)
    if extra is not None:
        monkeypatch.setenv("OM_FIT_EXTRA", extra)
    g = ReplayGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080")
    g.start()
    try:
        g.wait_for_port(timeout=90.0)
        qa = _state(g, label="fight_replay camera.fit")["qa"]
        return [float(v) for v in qa["camera"]["fit"]]
    finally:
        g.stop()


@pytest.fixture()
def fight(tmp_path):
    doc = S.synthetic_fight(frames=12)
    return S.write_fight(tmp_path / "f.fight.json", doc), doc


def _chunk(doc: dict, lo: int, hi: int, tmp_path: Path, name: str) -> Path:
    d = dict(doc)
    d["frames"] = doc["frames"][lo:hi]
    return S.write_fight(tmp_path / name, d)


def test_control_fit_without_the_variable_holds_the_positions_with_a_margin(fight, monkeypatch):
    """CONTROL: camera.fit is four numbers, holds every unit position of the fight, and reaches at least 100 wu (the scene's FIT_MIN_WU margin) beyond them on each side."""
    path, doc = fight
    fit = _fit(monkeypatch, path, None)
    x0, y0, x1, y1 = S.doc_box(doc)
    assert len(fit) == 4
    assert fit[0] <= x0 - 100.0 + 1e-3 and fit[1] <= y0 - 100.0 + 1e-3 and fit[2] >= x1 + 100.0 - 1e-3 and fit[3] >= y1 + 100.0 - 1e-3


def test_extra_widens_the_fit_to_hold_the_box(fight, monkeypatch):
    """Brief: "one fixed camera box for a set of fights (union of positions ...": OM_FIT_EXTRA="-300,-200,700,500" (a box far wider than the fight) makes camera.fit hold it
    (fit x0 <= -300, y0 <= -200, x1 >= 700, y1 >= 500). A box past about 1,500 wu a side makes a wide field, where the scene follows the centroid and camera.fit is that
    window (H-053), so this box stays under it."""
    path, _ = fight
    fit = _fit(monkeypatch, path, "-300,-200,700,500")
    assert fit[0] <= -300.0 and fit[1] <= -200.0 and fit[2] >= 700.0 and fit[3] >= 500.0, fit


def test_an_extra_inside_the_fight_box_changes_nothing(fight, monkeypatch):
    """Brief: "union of positions": an extra box already inside the fight's own box widens nothing, so the fit equals the fit without the variable (a union, not a replacement)."""
    path, doc = fight
    x0, y0, x1, y1 = S.doc_box(doc)
    inside = "%s,%s,%s,%s" % (x0 + 5, y0 + 1, x1 - 5, y1 - 1)
    assert _fit(monkeypatch, path, inside) == pytest.approx(_fit(monkeypatch, path, None))


def test_two_chunks_with_one_extra_fit_one_camera(fight, tmp_path, monkeypatch):
    """Brief: "chunks of 500 frames" with "one fixed camera box": the first and the second half of one fight, each given the whole fight's position box as OM_FIT_EXTRA,
    fit the same camera.fit. Premise (control inside the test): without the variable the two halves fit different boxes, since the units walk."""
    _, doc = fight
    first, second = _chunk(doc, 0, 6, tmp_path, "c0.fight.json"), _chunk(doc, 6, 12, tmp_path, "c1.fight.json")
    assert _fit(monkeypatch, first, None) != pytest.approx(_fit(monkeypatch, second, None)), "premise: the halves must fit differently without the extra"
    box = ",".join(repr(float(v)) for v in S.doc_box(doc))
    assert _fit(monkeypatch, first, box) == pytest.approx(_fit(monkeypatch, second, box))
