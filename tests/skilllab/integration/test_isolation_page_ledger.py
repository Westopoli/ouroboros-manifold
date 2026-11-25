# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 6 (standing page; "updated after each arm lands"), piece LI5 part 1; ledger form: docs/northstar/story_reviews/westley/artifacts.md
"""The ledger fragment, determinism, errors and the CLI. The ledger (artifacts.md, branch s/artifact-ledger) has ten columns: id, url and version, date, title, shows, why, code, his response, done,
status; "A field that cannot be recovered says `not recorded`, never a guess". Interface: docs/reports/2026-11-24-li5-interface.md.
Red today: `scripts/skilllab/arena/isolation_page.py` does not exist."""
import filecmp
import json
import re
import subprocess

import pytest

import isolation_page_fixtures as pf

LEDGER_HEAD = ["id", "url and version", "date", "title", "shows", "why", "code", "his response", "done", "status"]


def cells(line):
    """The cells of one markdown table row; `\\|` is a pipe inside a cell."""
    body = line.strip()
    assert body.startswith("| ") and body.endswith(" |")
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", body[1:-1])]


def build(tmp_path, **kw):
    manifest = pf.clip_dir(tmp_path / "src", [("l0084-changed", "L-0084", "changed", ["then", "now"])])
    out, res = pf.build(tmp_path, pf.synthetic_rows() + pf.synthetic_f_rows(), m=[pf.m_summary()], v=[pf.v_row()], clips=manifest, **kw)
    return out, res, manifest


def test_fragment_is_one_row_of_ten_columns(tmp_path):
    out, res, _ = build(tmp_path)
    text = (out / "artifacts-row.md").read_text()
    assert text.endswith("\n") and text.count("\n") == 1
    c = cells(text)
    assert len(c) == 10 == len(LEDGER_HEAD)


def test_fragment_columns_in_ledger_order_with_the_passed_in_values(tmp_path):
    out, _, _ = build(tmp_path, ledger=dict(pf.LEDGER, url="https://claude.ai/artifact/XYZ"))
    c = cells((out / "artifacts-row.md").read_text())
    assert c[0] == "A-005" and "https://claude.ai/artifact/XYZ" in c[1] and c[2] == "2026-11-24" and c[3] == "Lab isolation, stage 3"
    assert c[5] == pf.LEDGER["why"]                                    # his words, with the pipe escaped on the line and restored here
    assert "\\|" in (out / "artifacts-row.md").read_text()


def test_shows_and_code_trace_to_the_page(tmp_path):
    out, _, _ = build(tmp_path)
    c = cells((out / "artifacts-row.md").read_text())
    assert "layouts L-0055, L-0084" in c[4] and "arms M, V, F, W" in c[4] and "1 clip set" in c[4]
    for sha in pf.SHA.values():
        assert sha in c[6]
    clip = json.loads((tmp_path / "src" / "src" / "l0084-changed-now.facts.json").read_text())
    assert clip["video"]["sha256"] in c[6] and "page.html" in c[6]


def test_unrecoverable_fields_say_so_never_a_guess(tmp_path):
    out, _, _ = build(tmp_path, ledger={"id": "A-006", "date": "2026-11-24", "title": "t"})
    c = cells((out / "artifacts-row.md").read_text())
    assert c[1] == "not published yet" and c[5] == "not recorded" and c[7] == "none yet" and c[8] == "none yet" and c[9] == "current"


def test_ledger_missing_id_date_or_title_is_an_error_and_nothing_is_written(tmp_path):
    for bad in ({"date": "2026-11-24", "title": "t"}, {"id": "A-1", "title": "t"}, {"id": "A-1", "date": "2026-11-24"}, {"id": "A-1", "date": "yesterday", "title": "t"}):
        with pytest.raises(pf.page().PageError):
            pf.build(tmp_path, pf.synthetic_rows(), ledger=bad)
        assert not (tmp_path / "out" / "index.html").exists() and not (tmp_path / "out" / "artifacts-row.md").exists()


def test_same_inputs_give_byte_identical_output_from_two_dirs(tmp_path):
    """Determinism is a contract: no clock, no path, no hash order in the page or the fragment."""
    a, _, _ = build(tmp_path / "a")
    b, _, _ = build(tmp_path / "b")
    assert sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file()) == sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file())
    for p in a.rglob("*"):
        if p.is_file():
            assert filecmp.cmp(p, b / p.relative_to(a), shallow=False), p
    html = (a / "index.html").read_text()
    assert str(tmp_path) not in html and "/scratch/" not in html and not re.search(r"\b20\d\d-\d\d-\d\dT\d\d:", html)


def test_rebuilding_into_the_same_dir_is_idempotent(tmp_path):
    out, _, manifest = build(tmp_path)
    first = {p.name: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    out2, _ = pf.build(tmp_path, pf.synthetic_rows() + pf.synthetic_f_rows(), m=[pf.m_summary()], v=[pf.v_row()], clips=manifest)
    assert first == {p.name: p.read_bytes() for p in out2.rglob("*") if p.is_file()}


def test_unreadable_rows_are_an_error_that_names_the_file_and_line(tmp_path):
    mod = pf.page()
    rows = tmp_path / "rows.jsonl"
    rows.write_text(json.dumps(pf.synthetic_rows()[0]) + "\n{not json\n")
    with pytest.raises(mod.PageError) as e:
        mod.read_inputs(rows=[rows], repo=pf.ROOT)
    assert "rows.jsonl" in str(e.value) and "2" in str(e.value)
    with pytest.raises(mod.PageError):
        mod.read_inputs(rows=[tmp_path / "missing.jsonl"], repo=pf.ROOT)


def test_inputs_are_read_as_the_arms_wrote_them(tmp_path):
    mod = pf.page()
    rows = pf.write_rows(pf.synthetic_rows() + pf.synthetic_f_rows(), tmp_path / "r.jsonl")
    got = mod.read_inputs(rows=[rows], repo=pf.ROOT)
    assert got["comparison"] == pf.fw().comparison_rows(pf.synthetic_rows() + pf.synthetic_f_rows(), repo=pf.ROOT) and got["m_summaries"] == [] and got["v_rows"] == []


def test_cli_writes_the_same_bytes_as_the_api_and_exits_2_on_bad_input(tmp_path):
    rows = pf.write_rows(pf.synthetic_rows(), tmp_path / "in" / "rows.jsonl")
    api, _ = pf.build(tmp_path / "api", pf.synthetic_rows())

    def cli(out, rows_file):
        cmd = [pf.fx.PY, "-m", "scripts.skilllab.arena.isolation_page", "--out", str(out), "--banner", pf.BANNER, "--rows", str(rows_file), "--id", "A-005", "--date", "2026-11-24",
               "--title", pf.LEDGER["title"], "--why", pf.LEDGER["why"], "--repo", str(pf.ROOT)]
        return subprocess.run(cmd, cwd=pf.ROOT, capture_output=True, text=True)

    ok = cli(tmp_path / "cli", rows)
    assert ok.returncode == 0, ok.stderr
    for name in ("index.html", "artifacts-row.md"):
        assert (tmp_path / "cli" / name).read_bytes() == (api / name).read_bytes()
    bad = cli(tmp_path / "cli2", tmp_path / "nope.jsonl")
    assert bad.returncode == 2 and "nope.jsonl" in bad.stderr and not (tmp_path / "cli2" / "index.html").exists()
