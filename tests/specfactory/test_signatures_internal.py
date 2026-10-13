# spec: docs/northstar/spec_factory/signatures.toml internal rows +
# scripts/specfactory/merge_gate_support.py symbol-ownership step.
"""om_step_*, om_rng_*, om_debug_gen_config and the other functions
csrc/om_internal.h declares are private to the C sim: no public header
declaration, no ctypes binding, no build-card symbol. Before this file the
merge gate's symbol-ownership lint had no row for any of them, so a leaf
could define e.g. om_step_friction inside the wrong .c file (csrc/collision.c
say) and the lint would silently SKIP it instead of rejecting -- "no
ownership row, not checked". This proves every om_internal.h prototype now
has an `internal = true` ownership row, that sig_table.py --emit never
touches a header/binding/stub for one, and that the lint actually rejects
a misplaced definition."""
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import card_lint as cl  # noqa: E402  (find_function_span: the one C-definition scanner)
import merge_gate_support as mgs  # noqa: E402
import sig_table as st  # noqa: E402

INTERNAL_HEADER = REPO / "csrc" / "om_internal.h"
SIGNATURES = REPO / "docs" / "northstar" / "spec_factory" / "signatures.toml"
CSRC_DIR = REPO / "csrc"

# The plan's module assignment (task brief), cross-checked below against
# what csrc/*.c actually defines today -- every one of these already has a
# body, so "if none defines it yet" never applies here.
EXPECTED_MODULE = {
    "om_cmd_apply_tick": "cmd_stream.c",
    "om_macro_install_net_hooks": "enemy_macro.c",
    "om_fog_install_net_hooks": "fog.c",
    "om_mission_install_net_hooks": "mission.c",
    "om_mapgen_install_net_hooks": "tactical_mapgen.c",
    "om_terrain_install_net_hooks": "terrain.c",
    "om_terrain_apply_ground": "terrain.c",
    "om_terrain_state_free": "terrain.c",
    "om_walk_route": "walk_route.c",
    "om_move_walker_tick": "tactical_move.c",
    "om_tn_value2": "terrain_noise.c",
    "om_tn_fbm2": "terrain_noise.c",
    "om_tn_sin_q16": "terrain_noise.c",
    "om_tn_cos_q16": "terrain_noise.c",
    "om_move_install_net_hooks": "tactical_move.c",
    "om_support_install_net_hooks": "tactical_support.c",
    "om_unit_install_net_hooks": "unit.c",
    "om_debug_gen_config": "region.c",
    "om_events_install_save_hooks": "events.c",
    "om_faction_step_budget": "faction.c",
    "om_faction_tech_multipliers_recalc": "faction.c",
    "om_fog_faction_sees": "fog.c",
    "om_generational_install_save_hooks": "generational.c",
    "om_grid_iter_begin": "unit.c",
    "om_grid_iter_begin_faction": "unit.c",
    "om_grid_iter_next": "unit.c",
    "om_grid_query_circle": "unit.c",
    "om_grid_query_circle_faction": "unit.c",
    "om_mission_on_begin": "mission.c",
    "om_mission_reset_started": "fog.c",
    "om_mission_tactical_tick": "mission.c",
    "om_move_route_get": "tactical_move.c",
    "om_move_terrain_epoch": "tactical_move.c",
    "om_rng_draw": "sim.c",
    "om_rng_seed": "sim.c",
    "om_step_admin_revolts": "friction.c",
    "om_step_collisions": "collision.c",
    "om_step_decisions": "agent.c",
    "om_step_diplomacy": "diplomacy.c",
    "om_step_events": "events.c",
    "om_step_friction": "friction.c",
    "om_step_lifecycle": "lifecycle.c",
    "om_step_reinforce": "resolve.c",
    "om_step_resolve": "resolve.c",
    "om_step_technology": "diplomacy.c",
    "om_step_telegraphs": "resolve.c",
    "om_support_tick": "tactical_support.c",
    "om_tac_event_push": "unit.c",
    "om_tac_unit_sync_position": "unit.c",
    "om_unit_clear_target": "unit.c",
}

PROTO_RE = re.compile(
    r"^(?P<ret>[A-Za-z_][\w ]*?)\s+(?P<name>om_[a-z0-9_]+)\s*\((?P<params>[^)]*)\)\s*;\s*$",
    re.M,
)


def _split_param(part: str) -> tuple[str, str]:
    part = part.strip()
    stars = part.count("*")
    tokens = part.replace("*", " ").split()
    name = tokens[-1]
    base = " ".join(tokens[:-1])
    return name, base + ("*" * stars)


def parse_om_internal_prototypes(header_text: str) -> dict[str, dict]:
    stripped = re.sub(r"/\*.*?\*/", "", header_text, flags=re.S)
    protos: dict[str, dict] = {}
    for m in PROTO_RE.finditer(stripped):
        params_raw = m.group("params").strip()
        params = []
        if params_raw and params_raw != "void":
            for part in params_raw.split(","):
                pname, ctype = _split_param(part)
                params.append((pname, ctype))
        protos[m.group("name")] = {"restype": m.group("ret").strip(), "params": params}
    return protos


def _signature_rows() -> dict[str, dict]:
    data = tomllib.loads(SIGNATURES.read_text())
    return {row["name"]: row for row in data["symbols"]}


# ---------------------------------------------------------------- the parse itself --

def test_every_om_internal_prototype_is_found():
    protos = parse_om_internal_prototypes(INTERNAL_HEADER.read_text())
    assert set(protos) == set(EXPECTED_MODULE), (
        "csrc/om_internal.h prototypes changed; update EXPECTED_MODULE and "
        "the signatures.toml internal rows together"
    )


# ---------------------------------------------------------------- ownership rows --

def test_every_om_internal_function_has_an_internal_ownership_row():
    protos = parse_om_internal_prototypes(INTERNAL_HEADER.read_text())
    rows = _signature_rows()
    for name, proto in protos.items():
        assert name in rows, f"{name}: no [[symbols]] row in signatures.toml"
        row = rows[name]
        assert row.get("internal") is True, f"{name}: missing internal = true"
        assert row["module"] == EXPECTED_MODULE[name], (
            f"{name}: row module {row['module']!r} != {EXPECTED_MODULE[name]!r}"
        )
        assert row["restype"] == proto["restype"], (
            f"{name}: row restype {row['restype']!r} != header {proto['restype']!r}"
        )
        row_params = [(p["name"], p["ctype"]) for p in row["params"]]
        assert row_params == proto["params"], (
            f"{name}: row params {row_params} != header {proto['params']}"
        )
        assert row["epics"] == ["internal"], f"{name}: epics {row['epics']}"
        assert row["confidence"] == "certain", f"{name}: confidence {row['confidence']}"
        assert row["note"].startswith("internal (om_internal.h)"), f"{name}: note {row['note']!r}"


def test_positive_control_module_is_where_the_symbol_is_actually_defined():
    """Not guessed: the row's module is the .c file card_lint's own
    definition-span scanner finds the body in today."""
    for name, module in EXPECTED_MODULE.items():
        text = (CSRC_DIR / module).read_text()
        assert cl.find_function_span(text, name) is not None, (
            f"{name}: no definition found in csrc/{module}"
        )
        for other in CSRC_DIR.glob("*.c"):
            if other.name == module:
                continue
            assert cl.find_function_span(other.read_text(), name) is None, (
                f"{name}: also defined in {other.name}, not just {module}"
            )


# ---------------------------------------------------------------- sig_table.py skips internal rows --

FIXTURE_HEADER = """/* fixture header */
#ifndef FIX_H
#define FIX_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct om_world om_world;
#ifdef __cplusplus
}
#endif
#endif
"""

FIXTURE_CONFTEST = """import ctypes
# ---- generated from signatures.toml ----
# ---- end generated ----
"""

FIXTURE_TABLE = """[meta]
abi_version = 2

[[symbols]]
name = "om_normal_thing"
module = "diplomacy.c"
restype = "int"
params = [{ name = "w", ctype = "om_world*" }]
epics = ["E-06"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_step_friction"
module = "friction.c"
restype = "void"
params = [{ name = "w", ctype = "om_world*" }]
internal = true
epics = ["internal"]
confidence = "certain"
note = "internal (om_internal.h); no ctypes binding"
"""


def _make_fixture_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "docs" / "northstar" / "spec_factory").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(FIXTURE_HEADER)
    (project / "tests" / "csim" / "conftest.py").write_text(FIXTURE_CONFTEST)
    (project / "docs" / "northstar" / "spec_factory" / "signatures.toml").write_text(FIXTURE_TABLE)
    return project


def _run(project: Path, *args: str) -> subprocess.CompletedProcess:
    sig_table_py = REPO / "scripts" / "specfactory" / "sig_table.py"
    return subprocess.run(
        [sys.executable, str(sig_table_py), "--project", str(project), *args],
        capture_output=True, text=True,
    )


def test_internal_row_never_emits_header_binding_or_stub(tmp_path):
    project = _make_fixture_project(tmp_path)
    proc = _run(project, "--emit", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr

    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    assert "om_step_friction" not in header
    assert "om_step_friction" not in conftest
    assert not (project / "csrc" / "friction.c").is_file(), (
        "an internal row must never get a generated stub module"
    )
    # the one non-internal row still goes through normally
    assert "om_normal_thing" in header
    assert "om_normal_thing" in conftest


def test_emit_is_idempotent_with_an_internal_row_present(tmp_path):
    project = _make_fixture_project(tmp_path)
    assert _run(project, "--emit").returncode == 0
    snapshot = {p: p.read_text() for p in project.rglob("*") if p.is_file()}
    assert _run(project, "--emit").returncode == 0
    again = {p: p.read_text() for p in project.rglob("*") if p.is_file()}
    assert snapshot == again
    assert _run(project, "--check").returncode == 0, "a second run must report nothing stale"


def test_real_project_sig_table_check_is_clean():
    """The real table now carries 15 internal rows; --check on the actual
    repo (no fixture) must still report nothing stale, twice in a row."""
    sig_table_py = REPO / "scripts" / "specfactory" / "sig_table.py"
    first = subprocess.run([sys.executable, str(sig_table_py), "--check", "--json"],
                            capture_output=True, text=True, cwd=REPO)
    assert first.returncode == 0, first.stdout + first.stderr
    second = subprocess.run([sys.executable, str(sig_table_py), "--check", "--json"],
                             capture_output=True, text=True, cwd=REPO)
    assert second.returncode == 0, second.stdout + second.stderr
    assert first.stdout == second.stdout


# ---------------------------------------------------------------- the merge gate lint itself --

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo(base_dir: Path) -> Path:
    repo = base_dir
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "gate@test")
    _git(repo, "config", "user.name", "gate")
    (repo / "csrc").mkdir()
    (repo / "csrc" / "friction.c").write_text(
        "void om_step_friction(void *w) { (void)w; }\n"
        "void om_step_admin_revolts(void *w) { (void)w; }\n"
    )
    (repo / "csrc" / "collision.c").write_text(
        "void om_step_collisions(void *w) { (void)w; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def test_positive_control_om_step_friction_defined_in_collision_c_is_rejected(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    (repo / "csrc" / "collision.c").write_text(
        "void om_step_collisions(void *w) { (void)w; }\n"
        "void om_step_friction(void *w) { (void)w; }\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate: friction step lands in collision.c")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=mgs.DEFAULT_SIGNATURES,
                                             symbol_modules_path=mgs.DEFAULT_SYMBOL_MODULES)
    assert ok is False, detail
    assert "om_step_friction" in detail
    assert "collision.c" in detail
    assert "friction.c" in detail


def test_om_step_friction_defined_in_friction_c_is_accepted(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    (repo / "csrc" / "friction.c").write_text(
        "void om_step_friction(void *w) { (void)w; }\n"
        "void om_step_admin_revolts(void *w) { (void)w; }\n"
        "/* a harmless tweak so the diff has a change to commit */\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "candidate: friction step stays in friction.c")

    ok, detail = mgs.symbol_ownership_check(repo, "HEAD~1", signatures_path=mgs.DEFAULT_SIGNATURES,
                                             symbol_modules_path=mgs.DEFAULT_SYMBOL_MODULES)
    assert ok is True, detail
