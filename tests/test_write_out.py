"""Spec 126 C (docs/specs/126-read-in-and-write-out.md §C, decisions §204): write out. The decisions as MADR or Nygard files that `doc_formats` reads back the same, their README, Cline's
memory bank in six files, each journal as Markdown that a reader (the small one here) reads back equal, nothing written outside `to` and no file of the person's touched, `orkboard export`."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orkboard.gui import board_cli
from orkboard.realm import doc_formats, goal_team, ideas, journals, project_facts, write_out, write_out_bank

LOG = """# Decisions

## 1. No accounts in the first release (1 November, the person and Orkboard)

Why: People play at once.

1. Nobody signs in.
2. Scores stay on the device.

### A nested heading

More words.

## 2. Keep one theme file (2 November, the leaders, all agreed; Orkboard)

Why: One place to change the look.

1. Tech owns it.
"""


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    (root / "docs").mkdir(parents=True)
    return root


@pytest.fixture
def state(project):
    return project / ".orkcraft"


def _board(root: Path) -> Path:
    return root / "llm-wiki" / "general"


def _party(root: Path, title: str, leader: str) -> str:
    slug = ideas.add_track(_board(root), title)
    goal_team.set_team(_board(root), slug, ["grunt"], leader=leader)
    return slug


def _tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def _read_journal(text: str) -> dict:
    """A small reader of a journal file, as `read_in` reads it: the front matter and the entries `(day, kind, text, id, idea, on, ref)`."""
    meta, rest = doc_formats.front_matter(text)
    rows = []
    for line in rest.splitlines():
        m = re.fullmatch(r"- (\d{4}-\d{2}-\d{2}) · ([a-z_]+) · (.*) <!-- id=(\S*) idea=(\S*) on=(\S*) ref=(.*) -->", line)
        if m:
            day, kind, body, eid, idea, on, ref = m.groups()
            rows.append({"day": day, "kind": kind, "text": body, "id": eid, "idea": idea, "on": [p for p in on.split(",") if p], "ref": ref})
    return {"meta": meta, "entries": rows}


# -- the decisions ------------------------------------------------------------------------------------------------------------------------

def test_the_boards_decisions_are_madr_files_that_read_back_the_same_and_a_readme(project, state):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    got = write_out.write(project, state)
    out = project / ".orkcraft" / "export"
    assert got["decisions"] == 2 and got["path"] == out
    names = sorted(p.name for p in (out / "decisions").iterdir())
    assert names == ["0001-no-accounts-in-the-first-release.md", "0002-keep-one-theme-file.md", "README.md"]
    first = doc_formats.parse_record((out / "decisions" / names[0]).read_text("utf-8"), names[0])
    assert (first["number"], first["title"], first["status"], first["date"], first["deciders"], first["format"]) == (
        1, "No accounts in the first release", "accepted", "1 November", ["the person"], "madr")
    assert first["extra"] == {"ork-source": "docs/decisions.md"}
    assert first["decision"].startswith("Why: People play at once.") and "2. Scores stay on the device." in first["decision"] and "#### A nested heading" in first["decision"]
    second = doc_formats.parse_record((out / "decisions" / names[1]).read_text("utf-8"), names[1])
    assert second["deciders"] == ["the leaders"] and second["decision"].endswith("1. Tech owns it.")
    assert [r["number"] for r in doc_formats.records(out / "decisions")] == [1, 2]            # README.md is no record
    readme = (out / "decisions" / "README.md").read_text("utf-8")
    assert "Orkboard" in readme.splitlines()[0] and "- 0001 · [No accounts in the first release](0001-no-accounts-in-the-first-release.md)" in readme


def test_the_decisions_as_nygard_files(project, state, tmp_path):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    to = tmp_path / "out"
    assert write_out.write(project, state, to, "nygard")["decisions"] == 2
    name = "0002-keep-one-theme-file.md"
    text = (to / "decisions" / name).read_text("utf-8")
    assert "Orkboard" in text.splitlines()[0] and "ork-source: docs/decisions.md" in text.splitlines()[0]
    rec = doc_formats.parse_record(text, name)
    assert (rec["format"], rec["number"], rec["title"], rec["status"], rec["date"]) == ("nygard", 2, "Keep one theme file", "accepted", "2 November")
    assert rec["decision"].endswith("1. Tech owns it.")
    assert doc_formats.folder_format(to / "decisions") == "nygard"


def test_the_decisions_of_a_projects_adr_folder_are_written_out_and_the_folder_is_never_touched(project, state):
    adr = project / "docs" / "adr"
    adr.mkdir()
    (adr / "0001-use-postgres.md").write_text("---\nstatus: accepted\ndate: 2026-03-02\ndecision-makers: [Ann, Bo]\n---\n\n# Use Postgres\n\n## Context and Problem Statement\n\nWe need a store.\n\n"
                                              "## Decision Outcome\n\nPostgres.\n\n### Consequences\n\nWe run it.\n", "utf-8")
    before = _tree(adr)
    write_out.write(project, state)
    assert _tree(adr) == before
    rec = doc_formats.records(project / ".orkcraft" / "export" / "decisions")[0]
    assert (rec["title"], rec["date"], rec["deciders"], rec["context"], rec["decision"], rec["consequences"]) == (
        "Use Postgres", "2026-03-02", ["Ann", "Bo"], "We need a store.", "Postgres.", "We run it.")
    assert rec["extra"]["ork-source"] == "docs/adr/0001-use-postgres.md"


def test_nothing_is_refused_into_the_projects_own_decisions_folder(project, state):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    for bad in (project / "docs" / "adr", project / "docs", project / "docs" / "decisions", project):
        with pytest.raises(ValueError):
            write_out.write(project, state, bad)
    assert not (project / "docs" / "adr").exists()
    with pytest.raises(ValueError):
        write_out.write(project, state, None, "word")


# -- the memory bank -----------------------------------------------------------------------------------------------------------------------

def test_the_memory_bank_has_six_files_and_says_nothing_yet(project, state, tmp_path):
    to = tmp_path / "out"
    assert write_out.write(project, state, to)["memory_bank"] == 6
    assert sorted(p.name for p in (to / "memory-bank").iterdir()) == sorted(write_out_bank.FILES)
    for name in write_out_bank.FILES:
        text = (to / "memory-bank" / name).read_text("utf-8")
        assert "Written by Orkboard" in text and "Nothing yet." in text, name


def test_the_memory_bank_holds_the_brief_the_parties_the_goals_and_the_journals(project, state, tmp_path):
    tech, product = _party(project, "Tech", "architect"), _party(project, "Product", "product-manager")
    project_facts.keep(state, product, "for_whom", "Players of party games", "person")
    project_facts.keep(state, product, "hurts", "Setup takes an evening", "person")
    project_facts.keep(state, tech, "stack", "Python 3.12 and SQLite", "read")
    ideas.add_idea(_board(project), "A lobby for friends", ideas.GENERAL, state)
    gone = ideas.add_idea(_board(project), "Old thing", ideas.GENERAL, state)
    ideas.save_state(state, gone, state="done")
    for n in range(12):
        journals.add(state, tech, "stance", f"Tech line {n}")
    journals.save_digest(state, product, "Product wants it quick", "x")
    journals.save_digest(state, tech, "Tech keeps it small", "x")
    journals.add(state, journals.PROJECT, "done", "Goal “Lobby” was done")
    journals.add(state, journals.PROJECT, "dropped", "Goal “Chat” was dropped")
    journals.add(state, journals.PROJECT, "decision", "Decision 1: no accounts", ref="1")
    to = tmp_path / "out"
    write_out.write(project, state, to)
    bank = {n: (to / "memory-bank" / n).read_text("utf-8") for n in write_out_bank.FILES}
    assert "Whom it is for: Players of party games" in bank["projectbrief.md"] and "Tech, led by" in bank["projectbrief.md"] and "Product, led by" in bank["projectbrief.md"]
    assert "Players of party games" in bank["productContext.md"] and "Setup takes an evening" in bank["productContext.md"] and "Product wants it quick" in bank["productContext.md"]
    assert "Tech keeps it small" in bank["systemPatterns.md"] and "Tech line 11" in bank["systemPatterns.md"] and "Tech line 1\n" not in bank["systemPatterns.md"]
    assert bank["systemPatterns.md"].count("Tech line") == 10
    assert "Python 3.12 and SQLite" in bank["techContext.md"]
    assert "A lobby for friends (raw)" in bank["activeContext.md"] and "Old thing" not in bank["activeContext.md"] and "Decision 1: no accounts" in bank["activeContext.md"]
    progress = bank["progress.md"]
    assert progress.index("dropped · Goal “Chat”") < progress.index("done · Goal “Lobby”") and "Decision 1" not in progress


# -- the journals --------------------------------------------------------------------------------------------------------------------------

def test_a_journal_file_is_in_the_specs_format_and_reads_back_equal(project, state, tmp_path):
    tech = _party(project, "Tech", "architect")
    _party(project, "Design", "product-designer")                                           # no entry: no file
    a = journals.add(state, tech, "overruled", "You said no to “Add a lobby”: it breaks the cache.", idea="add-lobby", on=["cache", "net"], ref="12", at="2026-10-30")
    b = journals.add(state, tech, "stance", "Go on the timer")
    c = journals.add(state, tech, "stance", "Struck line")
    journals.strike(state, tech, c["id"], "no")
    journals.save_digest(state, tech, 'Tech says "small" and \\ keeps it', b["id"])
    p = journals.add(state, journals.PROJECT, "decision", "Decision 12: no accounts", idea="lobby", ref="docs/my decisions/0012-x.md#12", at="2026-11-01")
    to = tmp_path / "out"
    got = write_out.write(project, state, to)
    assert got["journals"] == 2 and sorted(f.name for f in (to / "journals").iterdir()) == ["project.md", f"{tech}.md"]
    text = (to / "journals" / f"{tech}.md").read_text("utf-8")
    lines = text.splitlines()
    assert lines[0] == "---" and lines[1] == f"orkboard-journal: {tech}" and lines[2] == "party: Tech" and lines[3].startswith("leader: ") and lines[3] != "leader: "
    assert lines[4] == "digest: \"Tech says 'small' and / keeps it\"" and re.fullmatch(r"exported: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", lines[5]) and lines[6] == "---"
    assert "# Tech's journal" in lines and f"- 2026-10-30 · overruled · You said no to “Add a lobby”: it breaks the cache. <!-- id={a['id']} idea=add-lobby on=cache,net ref=12 -->" in lines
    assert f"- {b['at'][:10]} · stance · Go on the timer <!-- id={b['id']} idea= on= ref= -->" in lines and "Struck line" not in text
    back = _read_journal(text)
    assert back["meta"]["orkboard-journal"] == tech and back["meta"]["party"] == "Tech"
    assert [(e["day"], e["kind"], e["text"], e["idea"], e["on"]) for e in back["entries"]] == [(e["at"][:10], e["kind"], e["text"], e["idea"], e["on"]) for e in journals.read(state, tech)]
    proj = _read_journal((to / "journals" / "project.md").read_text("utf-8"))
    assert proj["meta"]["orkboard-journal"] == journals.PROJECT and proj["entries"][0]["ref"] == "docs/my decisions/0012-x.md#12" and proj["entries"][0]["id"] == p["id"]


def test_a_journal_read_back_into_an_empty_state_is_the_same(project, state, tmp_path):
    tech = _party(project, "Tech", "architect")
    journals.add(state, tech, "heeded", "You made it smaller", idea="a", on=["x"], ref="r1", at="2026-09-01")
    journals.add(state, tech, "calibration", "Your no's held 3 of 4 times", at="2026-09-02")
    to = tmp_path / "out"
    write_out.write(project, state, to)
    empty = tmp_path / "empty-state"
    for e in _read_journal((to / "journals" / f"{tech}.md").read_text("utf-8"))["entries"]:
        journals.add(empty, tech, e["kind"], e["text"], idea=e["idea"], on=e["on"], ref=e["ref"], at=e["day"])
    keep = lambda rows: [(r["at"][:10], r["kind"], r["text"], r["idea"], r["on"], r["ref"]) for r in rows]
    assert keep(journals.read(empty, tech)) == keep(journals.read(state, tech))


# -- where it writes ------------------------------------------------------------------------------------------------------------------------

def test_it_writes_only_inside_to_and_never_touches_a_file_it_did_not_write(project, state, tmp_path):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    _party(project, "Tech", "architect")
    journals.add(state, "tech", "stance", "x")
    (project / "memory-bank").mkdir()
    (project / "memory-bank" / "projectbrief.md").write_text("MINE", "utf-8")
    outside = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    to = tmp_path / "out"
    (to / "memory-bank").mkdir(parents=True)
    (to / "memory-bank" / "progress.md").write_text("A PERSON'S OWN PAGE", "utf-8")
    (to / "decisions").mkdir()
    (to / "decisions" / "0099-mine.md").write_text("# mine\n", "utf-8")
    got = write_out.write(project, state, to)
    assert {p: p.read_bytes() for p in project.rglob("*") if p.is_file()} == outside                  # the project is as it was
    assert (to / "memory-bank" / "progress.md").read_text("utf-8") == "A PERSON'S OWN PAGE" and (to / "decisions" / "0099-mine.md").exists()
    assert got["memory_bank"] == 5 and got["skipped"] == [str(to / "memory-bank" / "progress.md")]


def test_a_second_export_writes_the_same_files_and_removes_those_that_no_longer_belong(project, state, tmp_path):
    log = project / "docs" / "decisions.md"
    log.write_text(LOG, "utf-8")
    to = tmp_path / "out"
    write_out.write(project, state, to)
    first = sorted(p.name for p in (to / "decisions").iterdir())
    log.write_text(LOG.replace("No accounts in the first release", "Accounts come later"), "utf-8")
    write_out.write(project, state, to)
    second = sorted(p.name for p in (to / "decisions").iterdir())
    assert "0001-no-accounts-in-the-first-release.md" in first and second == ["0001-accounts-come-later.md", "0002-keep-one-theme-file.md", "README.md"]


def test_a_project_with_no_decisions_has_a_readme_that_says_so(project, state, tmp_path):
    got = write_out.write(project, state, tmp_path / "out")
    assert got["decisions"] == 0 and "Nothing yet." in (tmp_path / "out" / "decisions" / "README.md").read_text("utf-8")


# -- orkboard export ------------------------------------------------------------------------------------------------------------------------

def test_run_cli_says_what_it_wrote(project, tmp_path):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    journals.add(project / ".orkcraft", journals.PROJECT, "done", "Goal “Lobby” was done")
    code, text = write_out.run_cli(project, tmp_path / "out", "madr")
    assert code == 0 and text == f"Wrote 2 decisions, 6 memory bank files and 1 journal to {tmp_path / 'out'}"
    code, text = write_out.run_cli(project, None, "nygard")
    assert code == 0 and text.endswith(f"to {project / '.orkcraft' / 'export'}") and (project / ".orkcraft" / "export" / "decisions").is_dir()


def test_orkboard_export_prints_it_and_a_bad_folder_or_format_is_exit_2(project, tmp_path, capsys):
    (project / "docs" / "decisions.md").write_text(LOG, "utf-8")
    assert board_cli.run(["export", str(project), "--to", str(tmp_path / "out")]) == 0
    assert capsys.readouterr().out.startswith("Wrote 2 decisions, 6 memory bank files and 1 journal to ")
    assert board_cli.run(["export", str(project), "--to", str(project / "docs" / "adr")]) == 2 and "decisions folder" in capsys.readouterr().err
    assert board_cli.run(["export", str(tmp_path / "none")]) == 2 and "no folder" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        board_cli.run(["export", str(project), "--as", "docbook"])


# -- the journals and the brief in a folder, for the Board's tree (spec 151 B.1, B.3) -------------------------------------------------------

def test_the_journals_go_into_a_folder_one_file_each_and_a_party_with_nothing_has_none(project, state):
    slug = _party(project, "Tech", "archie")
    _party(project, "Design", "dryad")
    journals.add(state, journals.PROJECT, "decision", "Decision 1: no accounts", ref="1")
    journals.add(state, slug, "stance", "Keep it small")
    out = project / "wiki" / "journals"
    parties = write_out_bank.parties(_board(project))
    assert write_out.journals_into(state, parties, out) == 2
    assert sorted(p.name for p in out.iterdir()) == ["project.md", f"{slug}.md"]
    assert "orkboard-journal: _project" in (out / "project.md").read_text() and "Keep it small" in (out / f"{slug}.md").read_text()
    assert write_out.journals_into(state, parties, out) == 0                                    # nothing changed: nothing written


def test_the_brief_is_the_memory_banks_projectbrief_written_again_when_it_changes_and_a_file_of_the_persons_is_left(project, state, tmp_path):
    _party(project, "Tech", "archie")
    board, out = _board(project), tmp_path / "wiki"
    want = lambda: write_out_bank.pages(project, state, board)["projectbrief.md"]
    assert write_out.brief_into(project, state, board, out) and (out / "project.md").read_text() == want() and "Tech" in want()
    assert not write_out.brief_into(project, state, board, out)
    _party(project, "Design", "dryad")
    assert write_out.brief_into(project, state, board, out) and "Design" in (out / "project.md").read_text()
    (out / "project.md").write_text("# my own brief\n")
    assert not write_out.brief_into(project, state, board, out) and (out / "project.md").read_text() == "# my own brief\n"
