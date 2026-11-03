# spec: docs/stories/H-073.md "A gate that cannot get graphics memory says so, instead of reporting a failing test."
"""H-073 Change part 2: the gpu_wait function of merge_gate.sh, extracted and run with a stub nvidia-smi.
Hermetic; env overrides MERGE_GATE_GPU_WAIT_S=1 and MERGE_GATE_GPU_POLL_S=0 keep it fast. Positive control: enough memory proceeds."""
import stat
import subprocess
import sys
from pathlib import Path

SPEC = Path(__file__).resolve().parent.parent.parent / "scripts" / "specfactory"


def _run(tmp_path, line, wait_s="1"):
    smi = tmp_path / "bin" / "nvidia-smi"
    smi.parent.mkdir()
    smi.write_text(f"#!/bin/sh\necho '{line}'\n")
    smi.chmod(smi.stat().st_mode | stat.S_IXUSR)
    script = (f"gate_line() {{ echo \"GATE $1 $2 $3\"; }}\n"
              f"source <(sed -n '/^# gpu_wait begin/,/^# gpu_wait end/p' {SPEC}/merge_gate.sh)\n"
              "gpu_wait lane_plays; echo PROCEEDED\n")
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=60,
                          env={"PATH": f"{tmp_path}/bin:/usr/bin:/bin", "PYTHON": sys.executable, "GATE_DIR": str(SPEC),
                               "MERGE_GATE_GPU_WAIT_S": wait_s, "MERGE_GATE_GPU_POLL_S": "0"})


def test_h073_2_low_memory_after_wait_is_gpu_low_exit_3(tmp_path):
    r = _run(tmp_path, "11887,12288")
    assert r.returncode == 3, (r.stdout, r.stderr)
    assert "GATE lane_plays GPU-LOW GPU LOW 401 need 3000 after" in r.stdout and "PROCEEDED" not in r.stdout


def test_h073_2_control_enough_memory_proceeds(tmp_path):
    r = _run(tmp_path, "2000,12288")
    assert r.returncode == 0 and "PROCEEDED" in r.stdout and "GPU-LOW" not in r.stdout
