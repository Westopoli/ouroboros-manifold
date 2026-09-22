# spec: docs/northstar/plans/briefs/2026-09-22-two-day-push.md decision 1 and the F1b row
"""Tests for scripts/specfactory/sig_table.py: the one generator that turns
docs/northstar/spec_factory/signatures.toml into header declaration blocks,
struct typedefs, ctypes bindings with paramflags, struct mirrors and STUB
skeletons. Every test builds a throwaway project under tmp_path so the real
header and conftest are never touched."""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SIG_TABLE = REPO / "scripts" / "specfactory" / "sig_table.py"

HEADER = """/* fixture header */
#ifndef FIX_H
#define FIX_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct om_world om_world;

typedef enum { OM_ARCH_PLAYER = 0 } om_archetype;

typedef struct om_existing {
    uint32_t a;
    double   b;
} om_existing;

/* ---- lifecycle ---- */
int  om_already(om_world *w,
                uint32_t idx);
uint32_t om_tick_existing(const om_world *w, om_existing *out, uint32_t max);

#ifdef __cplusplus
}
#endif

#endif /* FIX_H */
"""

CONFTEST = """import ctypes


class OMWorld(ctypes.Structure):
    pass


OMWorldP = ctypes.POINTER(OMWorld)


class OmExisting(ctypes.Structure):
    _fields_ = [
        ("a", ctypes.c_uint32),
        ("b", ctypes.c_double),
    ]


def _bind_e05(lib):
    if getattr(lib, "_e05_bound", False):
        return
    V = ctypes.c_void_p
    lib.om_already.argtypes = [V, ctypes.c_uint32]; lib.om_already.restype = ctypes.c_int
    lib._e05_bound = True


def _bind(lib, name, argtypes, restype, params, kw=False):
    pass


# ---- generated from signatures.toml ----
# ---- end generated ----
"""

OM_INTERNAL = """#ifndef OM_INTERNAL_H
#define OM_INTERNAL_H
#include "ouroboros_sim.h"
#define OM_MAX_NEIGHBORS 32

typedef struct {
    uint32_t n;
} om_region;

struct om_world {
    uint32_t n_regions;
    om_region *regions;
};
#endif
"""

EXISTING_C = """/* csrc/diplomacy.c fixture */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

int om_already(om_world *w, uint32_t idx) {
    (void)w; (void)idx;
    return 7;
}
"""

TABLE = """[meta]
abi_version = 2

[[symbols]]
name = "om_already"
module = "diplomacy.c"
restype = "int"
params = [{ name = "w", ctype = "om_world*" }, { name = "idx", ctype = "uint32_t" }]
epics = ["E-06"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_diplomacy_new_thing"
module = "diplomacy.c"
restype = "double"
params = [{ name = "w", ctype = "const om_world*" }, { name = "faction_id", ctype = "int32_t" }, { name = "archetype", ctype = "om_archetype" }]
epics = ["E-06", "E-08"]
confidence = "likely"
kwargs = ["faction_id"]
note = ""

[[symbols]]
name = "om_character_get_record"
module = "generational.c"
restype = "int"
params = [{ name = "w", ctype = "const om_world*" }, { name = "id", ctype = "uint32_t" }, { name = "out", ctype = "OmCharacterRecord*" }]
epics = ["E-08"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_unit_get_pos"
module = "generational.c"
restype = "int"
params = [{ name = "w", ctype = "const om_world*" }, { name = "unit", ctype = "uint32_t" }, { name = "out_x", ctype = "double*" }, { name = "out_y", ctype = "double*" }]
epics = ["E-08"]
confidence = "likely"
wrapper = "out_pair"
note = ""

[[symbols]]
name = "om_tick_existing"
module = "generational.c"
restype = "uint32_t"
params = [{ name = "w", ctype = "const om_world*" }, { name = "out", ctype = "om_existing*" }, { name = "max", ctype = "uint32_t" }]
epics = ["E-08"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_render_text"
module = "generational.c"
restype = "const char*"
params = [{ name = "w", ctype = "const om_world*" }, { name = "label", ctype = "const char*" }]
epics = ["E-08"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_bad_names"
module = "generational.c"
restype = "void"
params = [{ name = "w", ctype = "om_world*" }, { name = "int", ctype = "uint64_t" }, { name = "byref", ctype = "double" }, { name = "byref", ctype = "double" }]
epics = ["E-08"]
confidence = "likely"
note = ""

[[symbols]]
name = "om_unmappable"
module = "generational.c"
restype = "om_mystery_enum"
params = [{ name = "w", ctype = "const om_world*" }]
epics = ["E-08"]
confidence = "likely"
note = ""

[[structs]]
name = "OmCharacterRecord"
source_test = "tests/csim/test_fixture.py"
fields = [
  { name = "id", ctype = "uint32_t" },
  { name = "name", ctype = "char[32]" },
  { name = "birth_tick", ctype = "uint64_t" },
  { name = "weights", ctype = "double[10]" },
]

[[structs]]
name = "om_character_record"
source_test = "tests/csim/test_fixture.py"
fields = [
  { name = "id", ctype = "uint32_t" },
  { name = "name", ctype = "char[32]" },
  { name = "birth_tick", ctype = "uint64_t" },
  { name = "weights", ctype = "double[10]" },
]

[[structs]]
name = "OmExisting"
source_test = "tests/csim/test_fixture.py"
fields = [
  { name = "a", ctype = "uint32_t" },
  { name = "b", ctype = "double" },
]
"""


def make_project(tmp_path: Path, table: str = TABLE) -> Path:
    project = tmp_path / "proj"
    (project / "csrc").mkdir(parents=True)
    (project / "tests" / "csim").mkdir(parents=True)
    (project / "docs" / "northstar" / "spec_factory").mkdir(parents=True)
    (project / "csrc" / "ouroboros_sim.h").write_text(HEADER)
    (project / "csrc" / "om_internal.h").write_text(OM_INTERNAL)
    (project / "csrc" / "diplomacy.c").write_text(EXISTING_C)
    (project / "tests" / "csim" / "conftest.py").write_text(CONFTEST)
    (project / "docs" / "northstar" / "spec_factory" / "signatures.toml").write_text(table)
    return project


def run(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SIG_TABLE), "--project", str(project), *args],
        capture_output=True, text=True,
    )


def emit(project: Path) -> dict:
    proc = run(project, "--emit", "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_header_gets_one_block_per_module_and_never_redeclares(tmp_path):
    project = make_project(tmp_path)
    emit(project)
    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    assert "/* ---- generated from signatures.toml: diplomacy.c ---- */" in header
    assert "/* ---- end generated: diplomacy.c ---- */" in header
    assert header.count("om_already(") == 1, "an existing declaration must never be duplicated"
    assert header.count("om_tick_existing(") == 1
    assert "double om_diplomacy_new_thing(const om_world *w, int32_t faction_id, om_archetype archetype);" in header
    assert "int om_character_get_record(const om_world *w, uint32_t id, om_character_record *out);" in header
    assert "int om_unit_get_pos(const om_world *w, uint32_t unit, double *out_x, double *out_y);" in header
    assert header.index("generated from signatures.toml: structs") < header.index("generated from signatures.toml: diplomacy.c")
    assert header.rindex("#ifdef __cplusplus") > header.rindex("end generated: generational.c")


def test_existing_declarations_are_byte_identical_after_generation(tmp_path):
    project = make_project(tmp_path)
    before = (project / "csrc" / "ouroboros_sim.h").read_text()
    emit(project)
    after = (project / "csrc" / "ouroboros_sim.h").read_text()
    start = after.index("/* ---- generated from signatures.toml: structs ---- */")
    end = after.index("/* ---- end generated: generational.c ---- */") + len("/* ---- end generated: generational.c ---- */\n\n")
    stripped = after[:start] + after[end:]
    assert stripped == before
    assert "int  om_already(om_world *w,\n                uint32_t idx);" in after


def test_struct_typedef_uses_c_name_field_order_and_array_types(tmp_path):
    project = make_project(tmp_path)
    emit(project)
    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    assert header.count("typedef struct om_character_record {") == 1, "class row and snake row collapse to one typedef"
    body = header[header.index("typedef struct om_character_record {"):]
    body = body[:body.index("} om_character_record;")]
    fields = [ln.strip() for ln in body.splitlines()[1:] if ln.strip()]
    assert fields == ["uint32_t id;", "char name[32];", "uint64_t birth_tick;", "double weights[10];"]
    assert header.count("typedef struct om_existing {") == 1, "a struct already typedef'd in the header is not re-emitted"


def test_conftest_mirrors_bindings_paramflags_and_wrappers(tmp_path):
    project = make_project(tmp_path)
    emit(project)
    conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    gen = conftest[conftest.index("# ---- generated from signatures.toml ----"):conftest.index("# ---- end generated ----")]
    assert "class OmCharacterRecord(ctypes.Structure):" in gen
    assert '("name", ctypes.c_char * 32)' in gen
    assert '("weights", ctypes.c_double * 10)' in gen
    assert "om_character_record = OmCharacterRecord" in gen
    assert '"OmCharacterRecord": "om_character_record"' in gen
    assert "class OmExisting(ctypes.Structure):" not in gen, "a mirror the conftest already defines is not redefined"
    assert "def _bind_e06(lib):" in gen and "def _bind_e08(lib):" in gen
    assert "def _bind_e07(lib):" not in gen, "only epics present in the table get a binder"
    e06 = gen[gen.index("def _bind_e06"):gen.index("def _bind_e08")]
    e08 = gen[gen.index("def _bind_e08"):]
    assert 'lib, "om_diplomacy_new_thing"' in e06 and 'lib, "om_diplomacy_new_thing"' not in e08, "bound once, in the lowest epic"
    assert '("w", "faction_id", "archetype"), kw=True' in e06
    assert 'lib, "om_already", [W, ctypes.c_uint32], ctypes.c_int, ("w", "idx"))' in e06
    assert '_bind(lib, "om_character_get_record", [W, ctypes.c_uint32, V], ctypes.c_int, ("w", "id", "out"))' in e08
    assert '_wrap_out_pair(lib, "om_unit_get_pos")' in e08
    assert '_bind(lib, "om_render_text", [W, ctypes.c_char_p], ctypes.c_char_p, ("w", "label"))' in e08
    assert "_GENERATED_BINDERS = (_bind_e06, _bind_e08)" in gen
    assert conftest.count("def _bind_e05(lib):") == 1
    assert "lib.om_already.argtypes = [V, ctypes.c_uint32]; lib.om_already.restype = ctypes.c_int" in conftest


def test_skeletons_new_file_and_append_to_existing(tmp_path):
    project = make_project(tmp_path)
    emit(project)
    dip = (project / "csrc" / "diplomacy.c").read_text()
    assert dip.startswith(EXISTING_C), "an existing module is extended, never overwritten"
    assert dip.count("om_already(") == 1
    assert "double om_diplomacy_new_thing(const om_world *w, int32_t faction_id, om_archetype archetype) {\n    /* STUB */\n    (void)w; (void)faction_id; (void)archetype;\n    return 0.0;\n}" in dip
    assert dip.rstrip().endswith("/* ---- end generated stubs ---- */")
    gen_c = project / "csrc" / "generational.c"
    assert gen_c.is_file()
    text = gen_c.read_text()
    assert text.startswith("/* csrc/generational.c")
    assert '#include "ouroboros_sim.h"' in text and '#include "om_internal.h"' in text
    assert "om_tick_existing(" in text and "return 0;" in text
    assert "(void)w; (void)id; (void)out;" in text
    assert 'const char *om_render_text(const om_world *w, const char *label) {\n    /* STUB */\n    (void)w; (void)label;\n    return "";\n}' in text
    assert "om_unmappable" not in text


def test_emit_is_idempotent(tmp_path):
    project = make_project(tmp_path)
    emit(project)
    snapshot = {p: p.read_text() for p in project.rglob("*") if p.is_file()}
    emit(project)
    again = {p: p.read_text() for p in project.rglob("*") if p.is_file()}
    assert snapshot == again


def test_unmappable_row_is_left_out_and_reported(tmp_path):
    project = make_project(tmp_path)
    report = emit(project)
    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    assert "om_unmappable" not in header
    assert "om_unmappable" not in conftest
    blocked = {b["name"]: b for b in report["blocked"]}
    assert "om_unmappable" in blocked
    assert "om_mystery_enum" in blocked["om_unmappable"]["reason"]
    assert report["header_added"] == 5
    assert report["bindings_added"] == 7
    assert report["structs_added"] == 1


def test_keyword_and_duplicate_param_names_are_renamed_and_reported(tmp_path):
    project = make_project(tmp_path)
    report = emit(project)
    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    assert "void om_bad_names(om_world *w, uint64_t p1, double byref, double p3);" in header
    renames = {(r["name"], r["param"], r["renamed_to"]) for r in report["renamed"]}
    assert renames == {("om_bad_names", "int", "p1"), ("om_bad_names", "byref", "p3")}
    conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    assert '("w", "p1", "byref", "p3")' in conftest


def test_check_mode_exits_nonzero_when_stale(tmp_path):
    project = make_project(tmp_path)
    stale = run(project, "--check")
    assert stale.returncode == 1, stale.stdout + stale.stderr
    emit(project)
    fresh = run(project, "--check")
    assert fresh.returncode == 0, fresh.stdout + fresh.stderr


STRUCT_WRAPPER_ROWS = """
[[symbols]]
name = "om_tick_read_things"
module = "generational.c"
restype = "uint32_t"
params = [{ name = "w", ctype = "om_world*" }, { name = "out", ctype = "om_thing*" }, { name = "max", ctype = "uint32_t" }]
epics = ["E-08"]
confidence = "likely"
wrapper = "records"
note = ""

[[symbols]]
name = "om_view_read"
module = "generational.c"
restype = "om_view*"
params = [{ name = "w", ctype = "const om_world*" }]
epics = ["E-08"]
confidence = "likely"
wrapper = "client_snapshot"
note = ""

[[symbols]]
name = "om_tick_read_unknown"
module = "generational.c"
restype = "uint32_t"
params = [{ name = "w", ctype = "om_world*" }, { name = "out", ctype = "om_only_header*" }, { name = "max", ctype = "uint32_t" }]
epics = ["E-08"]
confidence = "likely"
wrapper = "records"
note = ""

[[structs]]
name = "OMThing"
source_test = "tests/csim/test_fixture.py"
fields = [{ name = "id", ctype = "uint32_t" }]

[[structs]]
name = "om_view"
source_test = "tests/csim/test_fixture.py"
fields = [{ name = "unit_count", ctype = "uint32_t" }, { name = "units", ctype = "om_thing[4]" }]
"""


def test_struct_wrappers_pass_the_mirror_and_block_without_one(tmp_path):
    project = make_project(tmp_path, TABLE + STRUCT_WRAPPER_ROWS)
    header_path = project / "csrc" / "ouroboros_sim.h"
    header_path.write_text(HEADER.replace(
        "} om_existing;", "} om_existing;\n\ntypedef struct om_only_header {\n    uint32_t z;\n} om_only_header;"))
    report = emit(project)
    conftest = (project / "tests" / "csim" / "conftest.py").read_text()
    header = (project / "csrc" / "ouroboros_sim.h").read_text()
    assert '_wrap_records(lib, "om_tick_read_things", OMThing)' in conftest
    assert '_wrap_client_snapshot(lib, "om_view_read", OmView)' in conftest
    assert '_wrap_out_pair(lib, "om_unit_get_pos")' in conftest, "a scalar-only adapter still gets no mirror"
    assert "typedef struct om_view {\n    uint32_t unit_count;\n    om_thing units[4];\n} om_view;" in header
    assert '("units", OMThing * 4)' in conftest
    blocked = {b["name"]: b["reason"] for b in report["blocked"]}
    assert "om_tick_read_unknown" in blocked, "a records row whose struct has no table mirror is blocked, not guessed"
    assert "wrapper records" in blocked["om_tick_read_unknown"]
    assert "om_tick_read_unknown" not in conftest
