# Rule pins: R-096-01@d86536
# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-2
"""engine.py: build command by architecture (observed through monkeypatch), the Engine surface, one real-library smoke."""
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab.engine import Engine, build_library  # noqa: E402

METHODS = ["new_world", "free_world", "register_unit_type", "type_id", "type_stats", "disable_abilities", "spawn",
           "order_attack_move", "order_move", "step", "unit_hp", "unit_pos", "unit_layer", "unit_alive", "can_shoot",
           "add_blocker"]
STAT_KEYS = ["category", "max_hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius",
             "layer_transition_time", "aoe_radius"]
LIB_NAME = "libouroboros.dylib" if sys.platform == "darwin" else "libouroboros.so"
HAVE_CC = shutil.which("cc") is not None
needs_cc = pytest.mark.skipif(not HAVE_CC, reason="no cc on PATH")


def _snapshot():
    """Library-like files at the repo root (name -> mtime): a build into the root would add or change one."""
    found = {}
    for pat in ("libouroboros*", "*.so", "*.dylib", "*.o", "*.a"):
        found.update({p.name: p.stat().st_mtime_ns for p in ROOT.glob(pat)})
    return found


def _argv(cmd):
    return shlex.split(cmd) if isinstance(cmd, str) else [str(c) for c in cmd]


@pytest.fixture
def compiles(monkeypatch):
    """Patch subprocess.run to record compiler commands and write an empty output file; returns a runner."""
    calls = []

    def fake_run(cmd, *args, **kwargs):
        argv = _argv(cmd)
        calls.append(argv)
        if "-o" in argv:
            Path(argv[argv.index("-o") + 1]).write_bytes(b"")     # no mkdir: the build must have made its directory
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def run(machine, scratch=None):
        monkeypatch.setattr(platform, "machine", lambda: machine)
        monkeypatch.setattr(subprocess, "run", fake_run)
        calls.clear()
        build_library(scratch) if scratch is not None else build_library()
        return [c for c in calls if any(a.endswith(".c") for a in c)]

    return run


# ---------------------------------------------------------------- AC 2: the build command

@pytest.mark.parametrize("machine", ["x86_64", "AMD64", "i386", "i686", "x86"])
def test_ac2_x86_machines_get_the_sse_flags(compiles, tmp_path, machine):
    """AC-2 (Readings): x86_64, AMD64, i386, i686 and x86 all count as x86 and get -msse2 -mfpmath=sse."""
    cmds = compiles(machine, tmp_path)
    assert cmds and all("-msse2" in c and "-mfpmath=sse" in c for c in cmds)


@pytest.mark.parametrize("machine", ["arm64", "aarch64"])
def test_ac2_arm_machines_do_not_get_the_sse_flags(compiles, tmp_path, machine):
    """AC-2: on arm no -msse2 and no -mfpmath=sse (the compiler would reject them)."""
    cmds = compiles(machine, tmp_path)
    assert cmds and not any("-msse2" in c or "-mfpmath=sse" in c for c in cmds)


@pytest.mark.parametrize("machine", ["x86_64", "arm64"])
def test_ac2_makefile_flags_are_on_the_command_for_every_architecture(compiles, tmp_path, machine):
    """AC-2 (Readings): exactly -O2 plus the Makefile's common and determinism flags (sse pair on x86 only), the csrc include, shared output, every csrc/*.c source."""
    cmds = compiles(machine, tmp_path)
    flags = ["-O2", "-std=c11", "-Wall", "-Wextra", "-fPIC", "-fno-fast-math", "-ffp-contract=off",
             "-fexcess-precision=standard", "-fno-math-errno", "-shared"]
    inc = [(ROOT / a[2:]).resolve() for c in cmds for a in c if a.startswith("-I") and len(a) > 2]
    srcs = {Path(a).name for c in cmds for a in c if a.endswith(".c")}
    assert all(f in c for c in cmds for f in flags)
    expected = set(flags) | ({"-msse2", "-mfpmath=sse"} if machine == "x86_64" else set())
    for c in cmds:      # exact: no extra flag (-ffast-math, -O3, -march=native ...) may ride along
        dash = {a for a in c[1:] if a.startswith("-") and not a.startswith("-I") and a != "-o"}
        assert dash == expected, sorted(dash ^ expected)
    assert (ROOT / "csrc").resolve() in inc
    assert srcs == {p.name for p in (ROOT / "csrc").glob("*.c")}
    assert Path(cmds[0][0]).name == "cc"


def test_ac2_output_goes_to_the_given_scratch_dir_with_the_platform_name_never_the_repo_root(compiles, tmp_path):
    """AC-2: -o lands in scratch_dir as libouroboros.{dylib,so}; the repo root gains and changes nothing."""
    before = _snapshot()
    cmds = compiles("arm64", tmp_path)
    outs = [Path(c[c.index("-o") + 1]).resolve() for c in cmds if "-o" in c]
    assert outs and all(o.parent == tmp_path.resolve() for o in outs) and any(o.name == LIB_NAME for o in outs)
    assert _snapshot() == before


def test_ac2_no_scratch_dir_means_a_fresh_temp_dir_outside_the_repo_each_call(compiles):
    """AC-2: scratch_dir=None builds into a new temporary directory outside the repo tree every time."""
    first = compiles("arm64")
    second = compiles("arm64")
    dirs = [Path(c[c.index("-o") + 1]).resolve().parent for c in first + second]
    assert ROOT.resolve() not in [p for d in dirs for p in [d, *d.parents]]
    assert dirs[0] != dirs[-1]


def test_ac2_a_missing_scratch_dir_is_created(compiles, tmp_path):
    """AC-2 (Readings): a scratch_dir that does not exist yet is created (the fake compiler writes -o without mkdir)."""
    target = tmp_path / "fresh_scratch"
    cmds = compiles("arm64", target)
    assert target.is_dir() and cmds and Path(cmds[0][cmds[0].index("-o") + 1]).resolve().parent == target.resolve()


class _Err(str):
    """stderr that also answers .decode(), so the test does not care whether the build asks for text or bytes."""
    def decode(self, *a, **k):
        return str(self)


@pytest.mark.parametrize("raises", [False, True])
def test_ac2_compiler_failure_raises_runtimeerror_with_the_last_2000_chars_of_stderr(monkeypatch, tmp_path, raises):
    """AC-2 (Readings): a failing compiler (exit status, or CalledProcessError under check=True) -> RuntimeError holding stderr[-2000:]."""
    err = _Err("HEAD" + "x" * 2500 + "TAIL")

    def failing_run(cmd, *args, **kwargs):
        if kwargs.get("check") or raises:
            raise subprocess.CalledProcessError(1, cmd, output="", stderr=err)
        return subprocess.CompletedProcess(cmd, 1, "", err)

    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    monkeypatch.setattr(subprocess, "run", failing_run)
    with pytest.raises(RuntimeError) as exc:
        build_library(tmp_path)
    assert str(err)[-2000:] in str(exc.value) and "HEAD" not in str(exc.value)


def test_ac2_missing_cc_raises_runtimeerror(monkeypatch, tmp_path):
    """AC-2 (Readings): no `cc` (the run raises FileNotFoundError / which() finds nothing) -> RuntimeError, not the raw OS error."""
    def no_cc(cmd, *args, **kwargs):
        raise FileNotFoundError("cc")

    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    monkeypatch.setattr(subprocess, "run", no_cc)
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    with pytest.raises(RuntimeError) as exc:
        build_library(tmp_path)
    assert not isinstance(exc.value, NotImplementedError)     # the sentinel's error is a RuntimeError too


@pytest.mark.parametrize("sysplat,system,suffix", [("darwin", "Darwin", ".dylib"), ("linux", "Linux", ".so"),
                                                   ("freebsd13", "FreeBSD", ".so")])
def test_ac2_library_suffix_is_dylib_on_macos_and_so_elsewhere(compiles, monkeypatch, tmp_path, sysplat, system, suffix):
    """AC-2 (Readings): the -o file is libouroboros.dylib on macOS and libouroboros.so on every other system."""
    monkeypatch.setattr(sys, "platform", sysplat)
    monkeypatch.setattr(platform, "system", lambda: system)
    cmds = compiles("arm64", tmp_path)
    assert Path(cmds[0][cmds[0].index("-o") + 1]).name == "libouroboros" + suffix


# ---------------------------------------------------------------- AC 3: the Engine surface

def test_ac3_engine_has_every_method_of_the_spec():
    """AC-3: Engine carries the sixteen methods the harness calls."""
    assert [m for m in METHODS if not callable(getattr(Engine, m, None))] == []


def test_ac3_engine_with_a_nonexistent_library_path_raises_oserror(tmp_path):
    """AC-3 (Readings): Engine(lib_path) for a path that does not exist raises OSError."""
    with pytest.raises(OSError):
        Engine(tmp_path / "no_such_library.so")


# ---------------------------------------------------------------- real library (one build, shared)

@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not HAVE_CC:
        pytest.skip("no cc on PATH")
    before = _snapshot()
    scratch = tmp_path_factory.mktemp("scratch")
    lib = build_library(scratch)
    return {"lib": lib, "scratch": scratch, "before": before}


@pytest.fixture(scope="module")
def eng(built):
    return Engine(built["lib"])


@needs_cc
def test_ac2_real_build_lands_in_scratch_and_leaves_the_repo_root_alone(built):
    """AC-2: the real build is a library file inside the scratch dir; nothing in the repo root changed."""
    lib = Path(built["lib"]).resolve()
    assert lib.is_file() and lib.parent == built["scratch"].resolve() and lib.name == LIB_NAME
    assert _snapshot() == built["before"]


@needs_cc
def test_ac3_type_id_maps_the_six_builtin_names_and_rejects_others(eng):
    """AC-3 (Readings): Raider 0 .. Bastion 5 (csrc/unit.c); case-sensitive; Supply and Evacuation and unknown names raise ValueError."""
    ids = {n: eng.type_id(n) for n in ("Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion")}
    assert ids == {"Raider": 0, "Interceptor": 1, "Vanguard": 2, "Warden": 3, "Bombard": 4, "Bastion": 5}
    for bad in ("Zebra", "", "vanguard", "VANGUARD", "Supply", "Evacuation"):    # AC-3 Readings: case-sensitive, six names only
        with pytest.raises(ValueError):
            eng.type_id(bad)


@needs_cc
def test_ac3_smoke_spawn_order_step_and_read_back(eng):
    """AC-3: two opposed Vanguards in a real world: spawn, register a custom type, order, step, read hp/pos/layer/alive, free."""
    w = eng.new_world(5)
    try:
        eng.disable_abilities(w)
        vg = eng.type_id("Vanguard")
        a = eng.spawn(w, vg, 0, -100.0, 0.0, 0)
        b = eng.spawn(w, vg, 1, -40.0, 0.0, 0)
        stats = eng.type_stats(w, vg)
        hp0 = eng.unit_hp(w, a)
        assert stats["max_hp"] == pytest.approx(hp0) and stats["attack_range"] > 0 and a != b
        assert eng.unit_pos(w, a) == pytest.approx((-100.0, 0.0), abs=1.0) and eng.unit_layer(w, a) == 0
        assert eng.unit_alive(w, a)
        assert eng.can_shoot(w, a, b) is True
        assert set(stats) == set(STAT_KEYS)     # AC-3: exactly the nine keys (no role, no ability_id)
        eng.order_attack_move(w, [a], -40.0, 0.0)
        eng.order_attack_move(w, [b], -100.0, 0.0)
        for _ in range(100):
            eng.step(w)
        assert eng.unit_hp(w, a) < hp0 and eng.unit_hp(w, b) < hp0     # both took damage: step really runs the fight
        custom = {"category": 1, "role": "line", "max_hp": 123.0, "base_damage": 5.0, "attack_interval": 20.0,
                  "attack_range": 80.0, "speed": 4.0, "sensor_radius": 150.0, "layer_transition_time": 2.5,
                  "aoe_radius": 7.0, "ability_id": 0}
        eng.register_unit_type(w, 100, custom)
        c = eng.spawn(w, 100, 0, 500.0, 0.0, 0)
        assert eng.unit_hp(w, c) == pytest.approx(123.0)
        assert set(eng.type_stats(w, 100)) == set(STAT_KEYS)
        m = eng.spawn(w, vg, 0, -100.0, 400.0, 0)
        eng.order_move(w, [m], -100.0, 550.0)
        for _ in range(33):                                              # the plain move arrives at step 33 (R-096-01), then the unit is idle
            eng.step(w)
            if eng.unit_destination(w, m) is None: break
        assert abs(eng.unit_pos(w, m)[1] - 550.0) <= 22.5 + 1e-9        # order_move moved it to the goal, within OM_ARRIVAL_TOLERANCE_MULT 1.5 x OM_UNIT_COLLISION_RADIUS 15
    finally:
        eng.free_world(w)


def _c_define(name):
    """Numeric value of `#define name <number>` from csrc/om_constants.h or csrc/unit.c."""
    for f in ("om_constants.h", "unit.c"):
        m = re.search(r"^#define\s+%s\s+(-?[0-9.]+)" % re.escape(name), (ROOT / "csrc" / f).read_text(), re.M)
        if m:
            return float(m.group(1))
    raise AssertionError("no #define %s in csrc" % name)


@needs_cc
def test_ac3_type_stats_is_exactly_the_nine_keys_and_matches_the_vanguard_constants(eng):
    """AC-3: type_stats(Vanguard) has exactly the nine keys, each valued as csrc/om_constants.h and unit.c define the built-in."""
    w = eng.new_world(5)
    try:
        stats = eng.type_stats(w, eng.type_id("Vanguard"))
        assert set(stats) == set(STAT_KEYS) and len(stats) == 9
        assert stats == pytest.approx({
            "category": _c_define("OM_CAT_LINE"), "max_hp": _c_define("OM_ROSTER_VANGUARD_HP"),
            "base_damage": _c_define("OM_ROSTER_VANGUARD_DAMAGE"),
            "attack_interval": _c_define("OM_ROSTER_VANGUARD_INTERVAL"),
            "attack_range": _c_define("OM_ROSTER_VANGUARD_RANGE"), "speed": _c_define("OM_ROSTER_VANGUARD_SPEED"),
            "sensor_radius": _c_define("OM_ROSTER_VANGUARD_SENSOR"),
            "layer_transition_time": _c_define("OM_ROSTER_VANGUARD_LAYER_TRANSITION"),
            "aoe_radius": _c_define("OM_ROSTER_VANGUARD_AOE")})
    finally:
        eng.free_world(w)


@needs_cc
def test_ac3_type_stats_of_a_registered_type_returns_each_registered_value_under_its_own_key(eng):
    """AC-3: distinct values per stat (category 1, layer_transition_time 2.5, aoe_radius 7.0 ...) come back under the right keys."""
    w = eng.new_world(5)
    try:
        custom = {"category": 1, "role": "line", "max_hp": 123.0, "base_damage": 5.0, "attack_interval": 20.0,
                  "attack_range": 80.0, "speed": 4.0, "sensor_radius": 150.0, "layer_transition_time": 2.5,
                  "aoe_radius": 7.0, "ability_id": 0}
        eng.register_unit_type(w, 100, custom)
        got = eng.type_stats(w, 100)
        assert set(got) == set(STAT_KEYS)
        assert got == pytest.approx({k: custom[k] for k in STAT_KEYS})
    finally:
        eng.free_world(w)


@needs_cc
def test_ac3_add_blocker_makes_can_shoot_false_only_for_a_pair_it_lies_between(eng):
    """AC-3 (Readings): Bombard and Raider 200 apart can shoot; a side blocker changes nothing, radius <= 0 raises, one between blocks."""
    w = eng.new_world(5)
    try:
        a = eng.spawn(w, eng.type_id("Bombard"), 0, 0.0, 0.0, 0)
        b = eng.spawn(w, eng.type_id("Raider"), 1, 200.0, 0.0, 0)
        assert eng.can_shoot(w, a, b) is True
        eng.add_blocker(w, 100.0, 150.0, 20.0)
        assert eng.can_shoot(w, a, b) is True
        for bad_radius in (0.0, -5.0):          # AC-3 Readings: radius <= 0 raises ValueError
            with pytest.raises(ValueError):
                eng.add_blocker(w, 100.0, 0.0, bad_radius)
        assert eng.can_shoot(w, a, b) is True
        eng.add_blocker(w, 100.0, 0.0, 20.0)
        assert eng.can_shoot(w, a, b) is False
    finally:
        eng.free_world(w)


@needs_cc
def test_ac2_library_is_built_once_per_process_however_many_engines():
    """AC-2: Engine() twice in one fresh process compiles once (the module-level cache); the first Engine() does compile."""
    code = (
        "import json, subprocess\n"
        "real = subprocess.run\n"
        "n = []\n"
        "def spy(cmd, *a, **k):\n"
        "    if any(str(c).endswith('.c') for c in (cmd.split() if isinstance(cmd, str) else cmd)):\n"
        "        n.append(1)\n"
        "    return real(cmd, *a, **k)\n"
        "subprocess.run = spy\n"
        "from scripts.skilllab.engine import Engine\n"
        "Engine(); after_one = len(n)\n"
        "Engine(); print(json.dumps([after_one, len(n)]))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-1500:]
    after_one, after_two = json.loads(out.stdout.strip().splitlines()[-1])
    assert after_one >= 1 and after_two == after_one
