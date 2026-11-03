# spec: docs/stories/H-073.md "A gate that cannot get graphics memory says so, instead of reporting a failing test."
"""H-073 gate-gpu-preflight, tests 1 to 4 of the story's Tests section. Hermetic: a stub `nvidia-smi` on PATH,
a stub pytest standing in for python_exe, a tmp lane map; no GPU, no Godot, no gate run.

Not tested (parked as questions in the report, nothing pinned): the wait/poll loop and the `GATE <stage> GPU-LOW`
line of merge_gate.sh (Change part 2), the docs sentences (part 4), the function signature, the boundary free==need."""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SPEC = REPO / "scripts" / "specfactory"
sys.path.insert(0, str(SPEC))

import merge_gate_support as mgs  # noqa: E402

PREFLIGHT = SPEC / "gpu_preflight.py"


def _exe(path: Path, body: str) -> Path:
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _stub_smi(bindir: Path, line: str) -> None:
    bindir.mkdir(exist_ok=True)
    _exe(bindir / "nvidia-smi", f"echo '{line}'\n")


def _cli(path_dir: Path):
    """Run the preflight CLI with PATH reduced to path_dir only (python is called by absolute path)."""
    return subprocess.run([sys.executable, str(PREFLIGHT)], env={"PATH": str(path_dir)},
                          capture_output=True, text=True, timeout=30)


# ---- controls: green today, so a red below means the feature is missing, not that the harness is broken ----

def test_control_stub_nvidia_smi_prints_the_chosen_line(tmp_path):
    """Control for Tests 1 to 3: the stub on PATH answers the story's query with the chosen line."""
    _stub_smi(tmp_path / "bin", "11887,12288")
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                         env={"PATH": str(tmp_path / "bin")}, capture_output=True, text=True, timeout=30)
    assert out.stdout.strip() == "11887,12288"


# ---- Change part 1: the CLI ----

@pytest.mark.parametrize("line", ["11887,12288", "11887, 12288"])
def test_h073_1_low_memory_prints_gpu_low_and_exits_3(tmp_path, line):
    """H-073 Tests 1: 'A stub `nvidia-smi` on PATH printing `11887,12288` gives `GPU LOW 401 need 3000` and exit 3.'
    (the second param is nvidia-smi's real csv spacing)."""
    _stub_smi(tmp_path / "bin", line)
    r = _cli(tmp_path / "bin")
    assert r.stdout.strip() == "GPU LOW 401 need 3000", (r.stdout, r.stderr)
    assert r.returncode == 3


@pytest.mark.parametrize("line", ["2000,12288", "2000, 12288"])
def test_h073_2_enough_memory_prints_gpu_ok_and_exits_0(tmp_path, line):
    """H-073 Tests 2 (the proceed control): 'A stub printing `2000,12288` gives `GPU OK 10288` and exit 0.'"""
    _stub_smi(tmp_path / "bin", line)
    r = _cli(tmp_path / "bin")
    assert r.stdout.strip() == "GPU OK 10288", (r.stdout, r.stderr)
    assert r.returncode == 0


def test_h073_3_no_nvidia_smi_prints_unknown_and_exits_0(tmp_path):
    """H-073 Tests 3: 'With no `nvidia-smi` on PATH the CLI prints `GPU UNKNOWN` and exits 0.'"""
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _cli(empty)
    assert r.stdout.strip() == "GPU UNKNOWN", (r.stdout, r.stderr)
    assert r.returncode == 0


# ---- Change part 3: classification of a stubbed lane_plays / playthrough log ----

def _lane_run(tmp_path, pytest_out: str):
    """lane_plays_check over one touched play, with a stub python_exe printing pytest_out for that play."""
    plays = tmp_path / "tests/qa/desktop/plays/A"
    plays.mkdir(parents=True)
    (plays / "test_s_x.py").write_text("def test_s_x():\n    pass\n")
    lane_map = tmp_path / "lane_plays.toml"
    lane_map.write_text('[lanes]\nA = ["scenes/a/**"]\n[shared]\n')
    known = tmp_path / "known_red.txt"
    known.write_text("")
    stub = _exe(tmp_path / "fakepy", f"cat <<'EOF_LOG'\n{pytest_out}\nEOF_LOG\n")
    return mgs.lane_plays_check(tmp_path, "HEAD", python_exe=str(stub), timeout=60, known_red_path=known,
                                lane_map_path=lane_map, changed=["scenes/a/x.tscn"], setup=False)


def _pt_run(tmp_path, pytest_out: str):
    (tmp_path / "suite").mkdir()
    known = tmp_path / "known_red.txt"
    known.write_text("")
    stub = _exe(tmp_path / "fakepy", f"cat <<'EOF_LOG'\n{pytest_out}\nEOF_LOG\n")
    return mgs.playthrough_check(tmp_path, "HEAD", python_exe=str(stub), timeout=60, known_red_path=known,
                                 target="suite", force=True, setup=False)


ASSERT_LOG = ("FAILED tests/qa/desktop/plays/A/test_s_x.py::test_s_x - assert 1 == 2\n"
              "E   assert 1 == 2")
GPU_LOGS = {
    "ERR_CANT_CREATE": "ERROR: Condition \"err != VK_SUCCESS\" is true. ERR_CANT_CREATE",
    "index_array_create": "ERROR: index_array_create (servers/rendering/rendering_device.cpp:3421)",
    "VK_ERROR_OUT_OF_DEVICE_MEMORY": "vkAllocateMemory failed: VK_ERROR_OUT_OF_DEVICE_MEMORY",
}


def test_control_ordinary_assertion_failure_is_a_red_outside_known_red_list(tmp_path):
    """Control for Tests 4: 'an ordinary assertion failure in the same stubbed log still is a `red outside
    known-red list`', in both stages."""
    (tmp_path / "lane").mkdir()
    ok, detail = _lane_run(tmp_path / "lane", ASSERT_LOG)
    assert not ok and "red outside known-red list" in detail and "GPU-MEMORY" not in detail
    (tmp_path / "pt").mkdir()
    ok, detail = _pt_run(tmp_path / "pt", ASSERT_LOG.replace("plays/A/test_s_x.py::test_s_x", "suite::test_s_x"))
    assert not ok and "red outside known-red list" in detail and "GPU-MEMORY" not in detail


@pytest.mark.parametrize("sig", sorted(GPU_LOGS))
def test_h073_4_lane_plays_gpu_signature_is_gpu_memory(tmp_path, sig):
    """H-073 Tests 4 / Change 3: 'A red whose log carries `ERR_CANT_CREATE`, `index_array_create` or
    `VK_ERROR_OUT_OF_DEVICE_MEMORY` is classified `GPU-MEMORY` ... never as `red outside known-red list`.'
    Here: the lane_plays stage, rc=134 style abort after the signature."""
    log = ("FAILED tests/qa/desktop/plays/A/test_s_x.py::test_s_x - daemon exited rc=134\n" + GPU_LOGS[sig])
    ok, detail = _lane_run(tmp_path, log)
    assert not ok
    assert "GPU-MEMORY" in detail, detail
    assert "red outside known-red list" not in detail, detail


@pytest.mark.parametrize("sig", sorted(GPU_LOGS))
def test_h073_4_playthrough_gpu_signature_is_gpu_memory(tmp_path, sig):
    """H-073 Change 3: both `playthrough_check` and `lane_plays_check` build the message; the playthrough stage
    classifies the same signatures as `GPU-MEMORY`."""
    log = "FAILED suite::test_s_x - daemon exited rc=134\n" + GPU_LOGS[sig]
    ok, detail = _pt_run(tmp_path, log)
    assert not ok
    assert "GPU-MEMORY" in detail, detail
    assert "red outside known-red list" not in detail, detail
