# spec: docs/northstar/plans/2026-10-21-tool-split-spec.md section 3 (the .claude-swarm.toml block), sections 4 and 6 (piece HARNESS-swarm-config)
"""Tests for the repo-root .claude-swarm.toml rewrite (HARNESS-swarm-config).

No R-/S- id applies to this tooling test, so none is cited (the Architect's script
vg-wave15-harness-swarmconfig.js, "no rule id applies").

UNSTATED INTERFACE choices:
- The section 3 block is read at test time from the tool split spec: the first fenced
  toml block between the heading line starting "## 3." and the next line starting "## ".
- The key check compares top-level keys and invariants.<key>; a block value with no
  angle-bracket placeholder must equal the config value, a placeholder key must be a string.
- The README test (cascades/README.md) is not in the script's case list, so it is not
  written here (gap, reported).
"""
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/northstar/plans/2026-10-21-tool-split-spec.md"
CONFIG = ROOT / ".claude-swarm.toml"

# Byte for byte `git show f3f85548:.claude-swarm.toml` (the old skilllab-harness config).
OLD_SKILLLAB_TOML = '''# claude-swarm — Ouroboros project config
# Cascade: skilllab-harness (Cascade A of docs/northstar/plans/2026-10-02-skill-lab-cascade.md)

spec_dir          = "docs/northstar/plans/"
briefs_dir        = ".swarm/skilllab-harness/briefs/"
type_contract_path = "scripts/skilllab/contract.py"

umbrella_test_cmd = "python3 -m pytest tests/skilllab/test_umbrella.py -p no:cacheprovider -q"
apex_test_cmd     = "python3 -m pytest tests/skilllab/integration -p no:cacheprovider -q"
graphify_cmd      = ""

worktree_link = []

parent_owned = [
  "docs/northstar/plans/2026-10-02-skill-lab-cascade.md",
  "docs/northstar/plans/skilllab-harness-spec.md",
  "docs/bible/**",
  "scripts/skilllab/contract.py",
  "tests/skilllab/test_umbrella.py",
  "tests/skilllab/integration/**",
  "tests/skilllab/golden_hashes.json",
  "csrc/**",
  "Makefile",
  "tests/csim/**",
  "tests/specfactory/**",
  "scripts/specfactory/**",
  "toys/**",
]

[invariants]
max_impl_lines      = 300
max_test_assertions = 40
ambiguous_verbs = [
  "decide", "choose", "design", "determine",
  "figure out", "resolve", "as appropriate",
  "use your judgment", "pick", "select an approach",
]

[gates]
extra_spec_gate_cmds = []
'''


def spec_block():
    lines = SPEC.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## 3."))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    body = "\n".join(lines[start:end])
    m = re.search(r"```toml\n(.*?)\n```", body, re.S)
    assert m, "no fenced toml block under section 3"
    return tomllib.loads(m.group(1))


def flat(cfg):
    out = {k: v for k, v in cfg.items() if not isinstance(v, dict)}
    out.update({"invariants." + k: v for k, v in cfg.get("invariants", {}).items()})
    return out


def is_placeholder(v):
    return isinstance(v, str) and "<" in v and ">" in v


def key_check(cfg, block):
    findings = []
    have = flat(cfg)
    for k, bv in flat(block).items():
        if k not in have:
            findings.append(f"{k}: missing")
        elif is_placeholder(bv):
            if not isinstance(have[k], str):
                findings.append(f"{k}: placeholder key must be a string")
        elif have[k] != bv:
            findings.append(f"{k}: {have[k]!r} != {bv!r}")
    return findings


def load_repo():
    return tomllib.loads(CONFIG.read_text())


def test_block_parses_and_lists_keys():  # C1 control
    flat_block = flat(spec_block())
    for k in ("spec_dir", "type_contract_path", "umbrella_test_cmd", "apex_test_cmd",
              "briefs_dir", "parent_owned", "invariants.max_impl_lines",
              "invariants.max_test_assertions"):
        assert k in flat_block, k


def test_key_check_clean_on_block_itself():  # C2 control
    block = spec_block()
    assert key_check(block, block) == []


def test_positive_control_old_toml_fails_key_check():  # C3 control
    old = tomllib.loads(OLD_SKILLLAB_TOML)
    git = subprocess.run(["git", "show", "f3f85548:.claude-swarm.toml"], cwd=ROOT,
                         capture_output=True, text=True)
    if git.returncode == 0:
        assert git.stdout == OLD_SKILLLAB_TOML
    text = "\n".join(key_check(old, spec_block()))
    assert "parent_owned" in text
    assert "invariants.max_impl_lines" in text


def test_repo_toml_parses():  # 1
    assert isinstance(load_repo(), dict)


def test_repo_toml_matches_section3_block():  # 2 RED (a)
    assert key_check(load_repo(), spec_block()) == []


def test_parent_owned_holds_frozen_contract_and_tests():  # 3 RED (a)
    po = load_repo()["parent_owned"]
    for entry in ("tests/**", "csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml"):
        assert entry in po, entry


def test_max_impl_lines_is_100():  # 4 RED (a)
    assert load_repo()["invariants"]["max_impl_lines"] == 100


def _before_first_table(key):
    lines = CONFIG.read_text().splitlines()
    first_table = next(i for i, l in enumerate(lines) if l.startswith("["))
    idx = next(i for i, l in enumerate(lines) if re.match(rf"{key}\s*=", l))
    return idx < first_table


def test_worktree_link_kept_top_level():  # 5 guard
    assert load_repo()["worktree_link"] == []
    assert _before_first_table("worktree_link")


def test_graphify_cmd_kept_top_level():  # 6 guard
    assert load_repo()["graphify_cmd"] == ""
    assert _before_first_table("graphify_cmd")


def test_ambiguous_verbs_kept_under_invariants():  # 7 guard
    cfg = load_repo()
    old = tomllib.loads(OLD_SKILLLAB_TOML)["invariants"]["ambiguous_verbs"]
    assert "ambiguous_verbs" not in cfg
    assert cfg["invariants"]["ambiguous_verbs"] == old


def test_extra_spec_gate_cmds_kept_under_gates():  # 8 guard
    assert load_repo()["gates"]["extra_spec_gate_cmds"] == []
