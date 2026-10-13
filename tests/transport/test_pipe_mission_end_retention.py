"""SV-0: optional `retention` on `mission_end` (debug pipe only).

Spec: docs/northstar/plans/sim_lane_2026-10-12/sv0_spec.md.  R-077-01 (final
score = 0.75 x objective score + 0.25 x retention) and R-077-02 (the band is
the sim's own classification of that score).

Setup as test_pipe_debrief_region_delta.py: seed 16, 80 regions, features 0-7,
mission_start, objective_complete objective 0 (completion 1.0; T1 and T6 use
0.9, see BAND_COMPLETION), then mission_end.
The archetype is read from the mission frame, never hard-coded.  The debrief
frame carries retention as `brought_home` (docs/architecture.md, debrief frame)
and the outcome band as `band` (the om_mission_band int, 0 worst .. 4 best).

No band threshold value is asserted: only the debrief's own numbers, and
relations between debriefs of the same pipe (lower, equal, non-decreasing).

Red on base (field ignored): the debrief retention stays 1.0 (T1, T2), a bad
value is not rejected (T4), and the release pipe answers a debrief (T5).
Green on base: T3 (absent field, determinism) and T6 (band is monotone in
retention; with the field ignored every band is equal, which is non-decreasing).
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE_DBG = ROOT / "pipe/ouroboros_pipe_dbg"
PIPE_REL = ROOT / "pipe/ouroboros_pipe"

FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]

for _p, _t in ((PIPE_DBG, "ouroboros_pipe_dbg"), (PIPE_REL, "ouroboros_pipe")):
    if not _p.exists():
        pytest.fail("pipe/%s missing: run make pipe/%s" % (_t, _t))


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds, pipe=PIPE_DBG):
    quit_cmd = {"type": "cmd", "name": "quit"}
    script = b"".join(_frame(c) for c in cmds + [quit_cmd])
    proc = subprocess.run([str(pipe)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _setup():
    return [
        {"type": "cmd", "name": "set_seed", "seed": 16, "n_regions": 80,
         "features": FEATURES, "new_campaign": False},
        {"type": "cmd", "name": "mission_start", "faction": 0},
    ]


def _complete(completion=1.0):
    return {"type": "cmd", "name": "objective_complete", "objective": 0,
            "completion": completion}


def _end(retention=None, raw=None):
    cmd = {"type": "cmd", "name": "mission_end"}
    if raw is not None:
        cmd["retention"] = raw
    elif retention is not None:
        cmd["retention"] = retention
    return cmd


def _types(frames):
    return [f.get("type") for f in frames]


def _debriefs(frames):
    return [f for f in frames if f.get("type") == "debrief"]


def _one_debrief(frames, what):
    assert any(f.get("type") == "mission" for f in frames), (
        "%s: no mission frame; frames received: %r" % (what, _types(frames)))
    ds = _debriefs(frames)
    assert len(ds) == 1, (
        "%s: expected exactly one debrief frame; frames received: %r (errors: %r)"
        % (what, _types(frames), [f for f in frames if f.get("type") == "error"]))
    return ds[0]


# T1 and T6 use completion 0.9 so that a band can move with retention (with 1.0
# the score at retention 0.0 sits exactly on a band edge; spec "Tests", amended
# 2026-10-13).  It is a fixture input, not a threshold.
BAND_COMPLETION = 0.9


def _debrief_for(retention=None, completion=1.0):
    frames = _run(_setup() + [_complete(completion), _end(retention)])
    return _one_debrief(frames, "retention=%r completion=%r" % (retention, completion))


def test_t1_retention_zero_gives_zero_brought_home_and_lower_band():
    """R-077-01/R-077-02: mission_end retention 0.0 after objective_complete 0.9
    answers a debrief with retention 0.0 and a band lower than the run without
    the field.  Positive control: without the field, retention is 1.0 (no unit
    was hurt).

    Red on base: the field is ignored, brought_home stays 1.0 and the band is
    the same as the run without the field.
    """
    control = _debrief_for(None, BAND_COMPLETION)
    assert control["brought_home"] == pytest.approx(1.0, abs=1e-9), (
        "positive control broke: without the field an unhurt force is retention 1.0; "
        "got %r" % control)
    zero = _debrief_for(0.0, BAND_COMPLETION)
    assert zero["brought_home"] == pytest.approx(0.0, abs=1e-9), (
        "retention 0.0 was not applied: brought_home=%r (field ignored?)" % zero["brought_home"])
    assert zero["band"] < control["band"], (
        "band with retention 0.0 (%r) is not lower than the run without the field (%r)"
        % (zero["band"], control["band"]))


def test_t2_retention_half_is_the_debrief_retention():
    """R-077-01: mission_end retention 0.5 -> debrief retention 0.5 (1e-9).

    Red on base: the field is ignored, brought_home stays 1.0.
    """
    d = _debrief_for(0.5)
    assert abs(d["brought_home"] - 0.5) <= 1e-9, (
        "debrief retention %r != 0.5 (field ignored?)" % d["brought_home"])


def test_t3_absent_field_is_identical_to_a_run_recorded_without_it():
    """R-077-01 (measured retention): with the field absent the whole frame
    stream (debrief and snapshot included) is byte-identical to another run
    recorded without it, and retention is the measured 1.0.

    Green on base and after the change.
    """
    a = _run(_setup() + [_complete(), _end()])
    b = _run(_setup() + [_complete(), _end()])
    _one_debrief(a, "run a")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), (
        "two runs without the field differ; frame types a=%r b=%r" % (_types(a), _types(b)))
    assert _debriefs(a)[0]["brought_home"] == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("bad", [-0.1, 1.1, "x"], ids=["neg", "over", "string"])
def test_t4_bad_retention_errors_and_changes_nothing(bad):
    """R-077-01: retention outside 0..1 or not a number answers
    {"type":"error","name":"mission_end","reason":"bad retention"} and the
    mission stays running: a following mission_end without the field still
    answers a debrief, equal to the one from a run that never saw the bad value.

    Red on base: the bad value is ignored, no error frame (and a debrief is
    answered at the first mission_end).
    """
    frames = _run(_setup() + [_complete(), _end(raw=bad), _end()])
    errs = [f for f in frames if f.get("type") == "error"]
    assert errs and errs[0].get("name") == "mission_end" and errs[0].get("reason") == "bad retention", (
        "retention=%r: expected error mission_end 'bad retention'; errors received: %r, frames: %r"
        % (bad, errs, _types(frames)))
    ds = _debriefs(frames)
    assert len(ds) == 1, (
        "retention=%r: expected exactly one debrief (from the second, field-less mission_end); "
        "frames: %r" % (bad, _types(frames)))
    # The error comes before the debrief: the bad call ended nothing.
    assert _types(frames).index("error") < _types(frames).index("debrief"), (
        "bad retention call produced a debrief before the error: %r" % _types(frames))
    assert ds[0] == _debrief_for(None), (
        "debrief after a rejected retention differs from a clean run: %r" % ds[0])


def test_t5_release_pipe_refuses_the_field():
    """R-077-01: the release pipe answers {"type":"error","name":"mission_end",
    "reason":"debug build required"} to mission_end with retention and changes
    nothing: a following field-less mission_end still answers a debrief.

    Red on base: the release pipe ignores the field and answers a debrief.
    """
    frames = _run(_setup() + [_end(0.5), _end()], pipe=PIPE_REL)
    errs = [f for f in frames if f.get("type") == "error"]
    assert errs and errs[0].get("name") == "mission_end" and errs[0].get("reason") == "debug build required", (
        "release pipe with retention: expected error mission_end 'debug build required'; "
        "errors received: %r, frames: %r" % (errs, _types(frames)))
    assert _types(frames).index("error") < _types(frames).index("debrief"), (
        "release pipe answered a debrief before the error: %r" % _types(frames))
    assert len(_debriefs(frames)) == 1, (
        "release pipe: expected one debrief (from the field-less mission_end); frames: %r"
        % _types(frames))


VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]


def test_t6_band_is_non_decreasing_in_retention():
    """R-077-02: the outcome band follows 0.75 x objective + 0.25 x retention, so
    over retention 0.0, 0.25, 0.5, 0.75, 1.0 (objective completion fixed at BAND_COMPLETION)
    the debrief band never decreases.  No threshold value is asserted.

    Green on base (field ignored: constant band, which is non-decreasing); the
    positive control below makes sure the sweep cannot pass by staying flat.
    """
    bands = [_debrief_for(v, BAND_COMPLETION)["band"] for v in VALUES]
    assert all(a <= b for a, b in zip(bands, bands[1:])), (
        "band decreased as retention rose: retention %r -> bands %r" % (VALUES, bands))


def test_t6_positive_control_sweep_reads_back_and_moves_the_band():
    """R-077-01/R-077-02 positive control for T6: each given retention is read
    back by the debrief, and the band at retention 1.0 is above the band at 0.0.

    Red on base: the field is ignored, brought_home is 1.0 throughout and the
    band is flat.
    """
    ds = [_debrief_for(v, BAND_COMPLETION) for v in VALUES]
    got = [d["brought_home"] for d in ds]
    assert all(abs(g - v) <= 1e-9 for g, v in zip(got, VALUES)), (
        "debrief retention does not read back the given values: given %r, got %r" % (VALUES, got))
    bands = [d["band"] for d in ds]
    assert bands[-1] > bands[0], (
        "band at retention 1.0 (%r) is not above band at retention 0.0 (%r): sweep is flat"
        % (bands[-1], bands[0]))
