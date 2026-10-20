# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (piece LAB-REV3-B); Architect ruling 2026-10-20 (implementation; Westley may veto): every layer placement is a design number
"""LAB-REV3-B-SMOKE, the layer-stack plays name their layers.

The five layer-stack plays (s3_raider_bombard, s3_interceptor_bombard, s3_interceptor_raider, s3_bombard_bastion, s3_bombard_bastion_level)
registered with `numbers = {}`, and the B ruler exempted them from the named-number rule of test_plays_space.py. The Architect rejects the
exemption: every layer placement is a design number. The rule stands for every play (`len(p.numbers) >= 1`), and the builder names them.

BUILDER CONTRACT (this file and the restored rule in test_plays_space.py::test_play_has_words_skill_status_and_a_named_number):
  - Each of the five plays has, in `plays_space.PLAYS[play].numbers`, exactly one key starting "DRAFT-layer-stack-", the key
    "DRAFT-layer-stack-<play>" (play name with its s3_ prefix, e.g. "DRAFT-layer-stack-s3_raider_bombard"). Its value is a dict
    {unit type: tuple of the layers it stands on, ascending ints}, for every unit type of side 0 of the play's placed Setup, derived
    from the placed groups (a type on two layers lists both: s3_bombard_bastion gives (3, 4) for Bombard and for Bastion). The
    value is computed from the placement, not a second literal, so it cannot drift from it.
  - `plays_space.render_drafts_page()` still renders (its line `"- %s = %g" % (k, p.numbers[k])` raises TypeError on a dict value:
    the builder prints the layer dict some other way) and names every DRAFT-layer-stack-<play> once; the page file on disk is regenerated
    (test_plays_space.py::test_the_committed_page_is_current-style tests read it).
  - `report.DRAFT_TEXT` has a key for each of the five names with non-empty text; the artifact header DRAFT list (always listed, with or
    without rows) shows each once as <li data-draft=...>, none inside a diagram legend.
Tests that move with this ruling (named here so nobody reads them as a surprise; the ruler's TD row TD-LAB-REV3-B-smoke carries them):
  - test_report.py::test_l5_artifact_header_lists_every_draft_number_in_force_once (exact sorted-list pin, lines ~1247-1290:
    `sorted(names) == sorted([... *SCENE_MIX_DRAFTS])`) goes red when the builder adds the five names to DRAFT_TEXT; the ruler adds the five
    names to SCENE_MIX_DRAFTS (seventeen names; it is also read by the once-each test and the no-rows test) under the same row. NOT edited here.
  - test_plays_space.py render-page tests (lines ~509, ~517 and the page-currency check at ~131) go red on a dict value until the
    builder fixes the renderer and regenerates the page; they are the builder's, not changed here."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.skilllab import plays_space, report  # noqa: E402
from test_report import _page, _sec, _tree  # noqa: E402

PREFIX = "DRAFT-layer-stack-"
PLAYS = ("s3_raider_bombard", "s3_interceptor_bombard", "s3_interceptor_raider", "s3_bombard_bastion", "s3_bombard_bastion_level")
NAMES = tuple(PREFIX + p for p in PLAYS)


def placed_layers(setup):
    """{unit type of side 0: ascending tuple of the layers its groups stand on}, read from the placed Setup."""
    out = {}
    for g in setup.groups:
        if g.side == 0:
            out.setdefault(g.unit, set()).add(g.layer)
    return {unit: tuple(sorted(layers)) for unit, layers in out.items()}


# ---- the derivation (positive control) --------------------------------------------------------------------------------------------

def test_the_derivation_reads_the_placement_positive_control():
    """The helper on the five placed plays: values as the plays' placement lines give them today (plays_space._stack calls); a play
    that splits a type over two layers lists both, one layer lists one."""
    got = {p: placed_layers(plays_space.PLAYS[p].setup_fn()) for p in PLAYS}
    assert got == {
        "s3_raider_bombard": {"Raider": (1,), "Bombard": (3,)},
        "s3_interceptor_bombard": {"Interceptor": (1,), "Bombard": (4,)},
        "s3_interceptor_raider": {"Interceptor": (2,), "Raider": (3,)},
        "s3_bombard_bastion": {"Bombard": (3, 4), "Bastion": (3, 4)},
        "s3_bombard_bastion_level": {"Bombard": (4,), "Bastion": (4,)}}


# ---- the numbers ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("play", PLAYS)
def test_t1_the_play_has_exactly_one_layer_stack_number_named_for_it(play):
    numbers = plays_space.PLAYS[play].numbers
    assert len(numbers) >= 1, "the named-number rule stands for every play"
    assert [k for k in numbers if k.startswith(PREFIX)] == [PREFIX + play], list(numbers)


@pytest.mark.parametrize("play", PLAYS)
def test_t1_the_number_maps_every_side_0_type_to_its_placed_layers(play):
    value = plays_space.PLAYS[play].numbers[PREFIX + play]
    expected = placed_layers(plays_space.PLAYS[play].setup_fn())
    assert expected and isinstance(value, dict)
    assert value == expected, (value, expected)
    assert all(isinstance(layers, tuple) and layers == tuple(sorted(layers)) and all(isinstance(l, int) for l in layers)
               for layers in value.values()), value


@pytest.mark.parametrize("play", PLAYS)
@pytest.mark.parametrize("heads", (8, 16, 48))
def test_t1_the_number_agrees_with_the_scan_build_at_every_headcount(play, heads):
    """The sweep builds the play through scan_build; the named layers are the ones it places at every headcount (side 0 does not scale)."""
    value = plays_space.PLAYS[play].numbers[PREFIX + play]
    assert placed_layers(plays_space.scan_build(play)(None, heads, False)) == value


def test_t1_the_other_plays_are_unchanged_and_carry_no_layer_stack_number():
    """Negative control: only the five name a layer stack; every other play keeps scalar numbers and none of the prefix."""
    others = [n for n in plays_space.PLAYS if n not in PLAYS]
    assert others and not [n for n in others if any(k.startswith(PREFIX) for k in plays_space.PLAYS[n].numbers)]
    assert all(isinstance(v, (int, float)) for n in others for v in plays_space.PLAYS[n].numbers.values())


def test_t1_the_drafts_page_renders_and_names_each_layer_stack_number_once():
    page = plays_space.render_drafts_page()
    for name in NAMES:      # not followed by a name character: "...s3_bombard_bastion" is the start of "...s3_bombard_bastion_level"
        found = re.findall(re.escape(name) + r"(?![\w-])", page)
        assert len(found) == 1, (name, len(found))


# ---- the draft list ------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NAMES)
def test_t2_draft_text_has_a_non_empty_line_for_the_name(name):
    assert isinstance(report.DRAFT_TEXT.get(name), str) and report.DRAFT_TEXT[name].strip(), name


@pytest.mark.parametrize("sub,kw", [("rows", {}), ("norows", {"rows": []})], ids=["with-rows", "no-rows"])
def test_t2_the_artifact_header_lists_each_layer_stack_draft_once(tmp_path, sub, kw):
    root = _tree(_page(tmp_path / sub, **kw)[2])
    listed = [li.attrs["data-draft"] for li in _sec(root, "drafts").find("li") if "data-draft" in li.attrs]
    assert "DRAFT-mix-M5" in listed, "positive control: the header has the neighbouring draft names"
    for name in NAMES:
        assert listed.count(name) == 1, (sub, name, listed.count(name))


def test_t2_no_diagram_legend_carries_the_layer_stack_drafts(tmp_path):
    """As for the mix drafts: a legend lists the numbers its arrows touch; these touch none."""
    root = _tree(_page(tmp_path)[2])
    svgs = root.find("svg")
    assert svgs, "positive control: the page with rows has diagrams to look in"
    assert not [n for svg in svgs for n in svg.iter() if n.attrs.get("data-draft") in NAMES]
