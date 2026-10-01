"""B5 / architect rulings 2 Addendum A2: the resolved mission result survives save and load.

Finish a mission (or refuse it), save, load into a fresh pipe session, jump: entry 1 of the
chronicle frame is the consequence cluster (cluster_type 0, outcome category 0..2 (success, failure, mixed),
R-065-02). A save made after that jump, loaded and jumped again, carries no second
consequence. A save with no mission result carries none (control).

Positive control: test_control_no_mission_result_has_no_consequence proves the detector
does not see a consequence cluster that is not there; the jump-without-save case proves it
sees one that is.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES,
            "new_campaign": False}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
END = {"type": "cmd", "name": "mission_end"}
REFUSE = {"type": "cmd", "name": "mission_refuse"}
JUMP = {"type": "cmd", "name": "jump", "ticks": 30}
CONSEQUENCE_CLUSTER = 0
OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_MIXED = 0, 1, 2  # the frame carries the cluster category, not the 30..32 entry category
OUTCOME_CATEGORIES = (OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_MIXED)
REFUSAL_BAND = 5

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=120)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def _save(path):
    return {"type": "cmd", "name": "save", "path": path}


def _load(path):
    return {"type": "cmd", "name": "load", "path": path}


def _chronicles(frames):
    return [f for f in frames if f["type"] == "chronicle"]


def _no_errors(frames):
    errs = [f for f in frames if f["type"] == "error"]
    assert not errs, errs


def _consequences(chron):
    """The mission-result cluster. Ripple clusters (B5-4) share cluster_type 0 but carry category 3, so the outcome category tells them apart."""
    return [e for e in chron["entries"] if e["cluster_type"] == CONSEQUENCE_CLUSTER and e["category"] in OUTCOME_CATEGORIES]


def _assert_entry_one_is_consequence(chron):
    assert chron["entries"], chron
    first = chron["entries"][0]
    assert first["cluster_type"] == CONSEQUENCE_CLUSTER, "entry 1 is not a consequence cluster: %r" % first
    assert first["category"] in OUTCOME_CATEGORIES, first
    assert len(_consequences(chron)) == 1, chron["entries"]
    return first


def _finish_save_load_jump(d, finish):
    path = str(Path(d) / "slot.omsave")
    saved = _run([SET_SEED, START] + finish + [_save(path)])
    _no_errors(saved)
    assert any(f["type"] == "ack" and f["name"] == "save" for f in saved), saved
    return _run([SET_SEED, _load(path), JUMP]), path


def test_finished_mission_result_survives_save_load_jump():
    with tempfile.TemporaryDirectory() as d:
        frames, _ = _finish_save_load_jump(d, [BEGIN, END])
        _no_errors(frames)
        chrons = _chronicles(frames)
        assert len(chrons) == 1, [f["type"] for f in frames]
        _assert_entry_one_is_consequence(chrons[0])


def test_unplayed_mission_ended_at_recon_survives_save_load_jump():
    with tempfile.TemporaryDirectory() as d:
        frames, _ = _finish_save_load_jump(d, [END])
        _no_errors(frames)
        _assert_entry_one_is_consequence(_chronicles(frames)[0])


def test_refused_mission_survives_save_load_jump_as_failure():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "slot.omsave")
        saved = _run([SET_SEED, START, REFUSE, _save(path)])
        _no_errors(saved)
        debrief = next(f for f in saved if f["type"] == "debrief")
        assert debrief["band"] == REFUSAL_BAND, debrief
        frames = _run([SET_SEED, _load(path), JUMP])
        _no_errors(frames)
        first = _assert_entry_one_is_consequence(_chronicles(frames)[0])
        assert first["category"] == OUTCOME_FAILURE, "refusal must read as consequence failure: %r" % first


def test_consequence_entry_matches_the_unsaved_jump():
    """The loaded world's entry 1 equals the one the same world produces with no save in between."""
    with tempfile.TemporaryDirectory() as d:
        loaded, _ = _finish_save_load_jump(d, [BEGIN, END])
        direct = _run([SET_SEED, START, BEGIN, END, JUMP])
        _no_errors(direct)
        want = _assert_entry_one_is_consequence(_chronicles(direct)[0])
        got = _assert_entry_one_is_consequence(_chronicles(loaded)[0])
        assert (got["category"], got["refs"]) == (want["category"], want["refs"]), (got, want)


def test_save_after_the_jump_does_not_repeat_the_consequence():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "after.omsave")
        first = _run([SET_SEED, START, BEGIN, END, JUMP, _save(path)])
        _no_errors(first)
        _assert_entry_one_is_consequence(_chronicles(first)[0])  # fixture check: the first jump had one
        again = _run([SET_SEED, _load(path), JUMP])
        _no_errors(again)
        chrons = _chronicles(again)
        assert len(chrons) == 1, [f["type"] for f in again]
        assert not _consequences(chrons[0]), "consequence repeated after load: %r" % _consequences(chrons[0])


def test_control_no_mission_result_has_no_consequence():
    with tempfile.TemporaryDirectory() as d:
        path = str(Path(d) / "none.omsave")
        saved = _run([SET_SEED, {"type": "cmd", "name": "step", "n": 5}, _save(path)])
        _no_errors(saved)
        frames = _run([SET_SEED, _load(path), JUMP])
        _no_errors(frames)
        chrons = _chronicles(frames)
        assert len(chrons) == 1 and chrons[0]["entries"], "jump produced no chronicle entries"
        assert not _consequences(chrons[0]), _consequences(chrons[0])


def test_same_sequence_twice_gives_identical_chronicle_frames():
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        a, _ = _finish_save_load_jump(d1, [BEGIN, END])
        b, _ = _finish_save_load_jump(d2, [BEGIN, END])
        ca, cb = _chronicles(a), _chronicles(b)
        assert ca and ca == cb
        _assert_entry_one_is_consequence(ca[0])
