"""H-079 one-workflow-per-landing: land_story.js with a stub agent().

Story H-079: "A story goes from Ready to landed on one launch; the runner hears
about it once."
Rules proved (story Change/Tests sections): `meta` is a pure literal with name
`land-story` and phases Build, Land, Review; "`blocked` or `test_defect` returns
at once with the stage's fields: `{landed: false, blocked: true, stage: "build",
reason}`"; a good builder and clerk give `{landed: true, sha}`; "`args.skip` holds
stage names already done" so skip ["build"] calls no builder.

The Workflow runtime cannot run offline, so node loads the script text: `export`
is stripped, the body is wrapped in an async function with injected agent, phase,
log, pipeline, parallel and args stubs (the vg-wave scripts use top-level await
and return). The stub classifies a call as builder when opts.phase or opts.label
is Build/build, as clerk when Land/land.
Story point 6 (a launch record line in the story file) is a doc line, not tested.
Story point 1 says `node --check`; the script has top-level return like every
workflow script, so syntax is checked by compiling the wrapper instead.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "scripts" / "specfactory" / "workflows"
LAND = WF / "land_story.js"
PREV = WF / "vg-wave16-harness-pregate-pins.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")

RUNNER = r"""
const fs = require('fs'), vm = require('vm');
const [file, mode, scen] = process.argv.slice(2);
const src = fs.readFileSync(file, 'utf8');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
function metaLiteral() {
  const i = src.indexOf('export const meta');
  if (i < 0) throw new Error('no export const meta');
  const s = src.indexOf('{', i);
  let d = 0, q = null;
  for (let j = s; j < src.length; j++) {
    const c = src[j];
    if (q) { if (c === '\\') j++; else if (c === q) q = null; continue; }
    if (c === "'" || c === '"' || c === '`') { q = c; continue; }
    if (c === '{') d++;
    if (c === '}' && --d === 0) return src.slice(s, j + 1);
  }
  throw new Error('unbalanced meta');
}
const body = src.replace(/^export\s+/mg, '');
if (mode === 'meta') {
  // pure literal: evaluates in an empty context with no identifiers in scope
  const meta = vm.runInNewContext('(' + metaLiteral() + ')', Object.create(null));
  console.log(JSON.stringify(meta));
} else if (mode === 'compile') {
  new AsyncFunction('agent', 'phase', 'log', 'pipeline', 'parallel', 'args', body);
  console.log('{"compiled":true}');
} else {
  const sc = JSON.parse(scen);
  const calls = [];
  const kind = (o) => {
    const t = ((o && o.phase) || '') + ' ' + ((o && o.label) || '');
    if (/build/i.test(t)) return 'build';
    if (/land/i.test(t)) return 'land';
    return 'other';
  };
  const agent = async (prompt, opts) => {
    const k = kind(opts);
    calls.push({ kind: k, prompt: String(prompt), opts: opts || {} });
    if (k === 'build' && sc.builder) return sc.builder;
    if (k === 'land' && sc.clerk) return sc.clerk;
    throw new Error('unexpected ' + k + ' agent call');
  };
  const fn = new AsyncFunction('agent', 'phase', 'log', 'pipeline', 'parallel', 'args', body);
  const phases = [];
  fn(agent, (p) => phases.push(p), () => {},
     async (...a) => { throw new Error('pipeline unexpected'); },
     async (...a) => { throw new Error('parallel unexpected'); }, sc.args)
    .then((r) => console.log(JSON.stringify({ result: r, calls, phases })))
    .catch((e) => { console.log(JSON.stringify({ error: String(e), calls, phases })); });
}
"""


@pytest.fixture(scope="module")
def runner(tmp_path_factory):
    p = tmp_path_factory.mktemp("node") / "runner.js"
    p.write_text(RUNNER)
    return p


def node(runner, file, mode, scen=None):
    argv = [NODE, str(runner), str(file), mode] + ([json.dumps(scen)] if scen is not None else [])
    r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


BUILD_OK = {"ok": True, "pushed_sha": "b" * 40, "blocked": False, "reason": "", "test_defect": ""}
CLERK_OK = {"ok": True, "landed": "a" * 40, "summary": "landed", "played": "Played: ok", "worktrees": ""}
ARGS = {"id": "H-099", "channel": "lab"}


def test_control_previous_wave_meta_parses(runner):
    """Positive control (S-H079 pt 5): the loader parses the previous wave script's meta."""
    meta = node(runner, PREV, "meta")
    assert meta["name"] == "vg-wave16-harness-pregate-pins"
    assert [p["title"] for p in meta["phases"]][0] == "Preflight"


def test_control_loader_runs_an_existing_script_body(runner):
    """Control: the wrapper compiles an existing workflow script, so a red below is the missing script."""
    assert node(runner, PREV, "compile") == {"compiled": True}


def test_meta_is_pure_literal_with_three_phases(runner):
    """H-079 pt 1: `meta`: name `land-story`, phases Build, Land, Review."""
    assert LAND.exists(), f"{LAND} missing"
    meta = node(runner, LAND, "meta")
    assert meta["name"] == "land-story"
    assert [p["title"] for p in meta["phases"]] == ["Build", "Land", "Review"]


def test_script_compiles(runner):
    """H-079 pt 1: the file parses as JavaScript."""
    assert LAND.exists(), f"{LAND} missing"
    assert node(runner, LAND, "compile") == {"compiled": True}


@pytest.mark.parametrize("builder", [
    {**BUILD_OK, "ok": False, "blocked": True, "reason": "needs ruling"},
    {**BUILD_OK, "ok": False, "test_defect": "test_x line 4 contradicts R-001-01"},
])
def test_blocked_builder_returns_at_once(runner, builder):
    """H-079 pt 2: "`blocked` or `test_defect` returns at once with the stage's fields:
    `{landed: false, blocked: true, stage: "build", reason}`"; the clerk is never called."""
    assert LAND.exists(), f"{LAND} missing"
    out = node(runner, LAND, "run", {"args": ARGS, "builder": builder})
    assert "error" not in out, out
    r = out["result"]
    assert r["landed"] is False
    assert r["blocked"] is True
    assert r["stage"] == "build"
    assert r["reason"]
    assert [c["kind"] for c in out["calls"]] == ["build"]


def test_good_build_and_clerk_land(runner):
    """H-079 pt 3: builder ok and clerk ok with `landed: "<sha>"` yields `{landed: true, sha}`."""
    assert LAND.exists(), f"{LAND} missing"
    out = node(runner, LAND, "run", {"args": ARGS, "builder": BUILD_OK, "clerk": CLERK_OK})
    assert "error" not in out, out
    r = out["result"]
    assert r["landed"] is True
    assert r["sha"] == CLERK_OK["landed"]
    assert not r.get("blocked")
    assert [c["kind"] for c in out["calls"]] == ["build", "land"]
    assert all(c["opts"].get("schema") for c in out["calls"] if c["kind"] != "other")


def test_skip_build_calls_no_builder(runner):
    """H-079 pt 4: `args.skip = ["build"]` calls no builder and goes to the clerk."""
    assert LAND.exists(), f"{LAND} missing"
    out = node(runner, LAND, "run", {"args": {**ARGS, "skip": ["build"]}, "clerk": CLERK_OK})
    assert "error" not in out, out
    assert [c["kind"] for c in out["calls"]] == ["land"]
    assert out["result"]["landed"] is True
    assert out["result"]["sha"] == CLERK_OK["landed"]
