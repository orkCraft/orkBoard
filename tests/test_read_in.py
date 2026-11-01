"""Spec 126 B (docs/specs/126-read-in-and-write-out.md, decisions §204): a project's own decisions, specs and notes found by their shapes and read into the journals, once.
Each framework's files are built in `tmp_path`; the host tests compose the host as `tests/test_idea_project_q.py` does. An Orkboard export is read back by the format spec 126 C
sets (`orkboard-journal: <scope>` front matter; `- YYYY-MM-DD · kind · text` lines, each followed by `<!-- id=… idea=… on=a,b ref=… -->`)."""
from __future__ import annotations

import sys

import pytest

from orkboard.gui import board_cli
from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_read_in import ReadInMixin, read_in_commands
from orkboard.realm import goal_team, ideas, journals, library, project_facts, read_in

MADR = """---
status: accepted
date: 2026-03-04
decision-makers: [Ann, Bob]
---

# Use PostgreSQL for the data

## Context and Problem Statement

We need a database.

## Decision Outcome

Chosen option: "PostgreSQL", because it is boring and good.

### Consequences

We run a server.
"""
MADR_OLD = MADR.replace("status: accepted", "status: superseded by ADR-0003").replace("PostgreSQL for the data", "SQLite for the data").replace("2026-03-04", "2026-01-10")
NYGARD = """# 2. Record architecture decisions

Date: 2016-02-12

## Status

Accepted

## Context

We need to record them.

## Decision

We will use Architecture Decision Records.

## Consequences

Files grow.
"""
UI_ADR = "---\nstatus: proposed\ndate: 2026-05-05\ntags: [ui]\n---\n\n# Round buttons\n\n## Decision Outcome\n\nButtons are round.\n"


def w(root, rel, text="x\n"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "project"
    r.mkdir()
    return r


@pytest.fixture
def sd(tmp_path):
    return tmp_path / "state"


def lines(sd, scope=journals.PROJECT):
    return [(e["kind"], e["text"], e["at"][:10], e["ref"]) for e in journals.read(sd, scope)]


# -- the shapes ----------------------------------------------------------------------------------------------------------------------------

def test_a_project_with_each_shape_is_found_by_scan(root):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    w(root, "docs/decisions/README.md", "# Decisions\n\nIndex.\n")                                    # an index is no record
    w(root, "doc/adr/0002-record.md", NYGARD)
    w(root, ".specify/memory/constitution.md", "# Constitution\n\nTests first.\n")
    w(root, "specs/001-lobby/spec.md", "# Lobby\n")
    w(root, ".kiro/steering/product.md", "Product steering\n")
    w(root, ".kiro/specs/auth/requirements.md", "# Auth\n")
    w(root, "openspec/project.md", "OpenSpec project\n")
    w(root, "openspec/specs/cart/spec.md", "# Cart\n")
    w(root, "openspec/changes/archive/old/proposal.md", "# Old\n")
    w(root, "openspec/changes/new/proposal.md", "# New\n")
    w(root, "docs/prd.md", "# PRD\n")
    w(root, "docs/stories/1.1.story.md", "# Story\n\nStatus: Done\n")
    w(root, "memory-bank/projectbrief.md", "Brief\n")
    w(root, "AGENTS.md", "Agents\n")
    w(root, "CLAUDE.md", "Claude\n")
    w(root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-02-01\n\n- First\n")
    w(root, "docs/export/journals/project.md", "---\norkboard-journal: _project\n---\n\n# Journal\n\n- 2026-04-01 · decision · Decision 1: x\n<!-- id=abc idea= on= ref=1 -->\n")
    got = read_in.scan(root)
    assert set(got) >= {"found", "decisions", "specs", "context", "releases"}
    frameworks = {(f["framework"], f["kind"]) for f in got["found"]}
    assert {("ADRs (MADR)", "decisions"), ("ADRs (Nygard)", "decisions"), ("GitHub Spec Kit", "specs"), ("GitHub Spec Kit", "context"), ("Kiro", "specs"), ("Kiro", "context"),
            ("OpenSpec", "specs"), ("OpenSpec", "context"), ("BMAD", "specs"), ("BMAD", "context"), ("Cline's memory bank", "context"), ("agents' files", "context"),
            ("Keep a Changelog", "releases"), ("An Orkboard export", "journals")} <= frameworks
    adr = next(f for f in got["found"] if f["framework"] == "ADRs (MADR)")
    assert adr == {"framework": "ADRs (MADR)", "kind": "decisions", "path": "docs/decisions", "n": 1}
    assert [d["path"] for d in got["decisions"]] == ["docs/decisions/0001-use-postgres.md", "doc/adr/0002-record.md"]
    assert [c["path"] for c in got["context"]] == [".specify/memory/constitution.md", ".kiro/steering/product.md", "openspec/project.md", "docs/prd.md",
                                                   "memory-bank/projectbrief.md", "AGENTS.md", "CLAUDE.md"]                    # the table's order
    assert {s["name"] for s in got["specs"]} == {"001-lobby", "auth", "cart", "old", "new", "1.1"}
    assert [r["version"] for r in got["releases"]] == ["1.0.0"]


def test_a_decision_belongs_to_tech_unless_its_tags_or_its_title_name_another_craft(root):
    w(root, "docs/adr/0001-pg.md", MADR)
    w(root, "docs/adr/0002-buttons.md", UI_ADR)
    w(root, "docs/adr/0003-pricing-page.md", "---\nstatus: accepted\n---\n\n# Pricing for the first year\n\n## Decision Outcome\n\nFree.\n")
    w(root, "docs/adr/0004-ship.md", "---\nstatus: accepted\ntags: marketing, launch\n---\n\n# Ship on Friday\n\n## Decision Outcome\n\nFriday.\n")
    w(root, "docs/adr/0005-level.md", "---\nstatus: accepted\n---\n\n# Level generation\n\n## Decision Outcome\n\nSeeded.\n")
    assert [d["craft"] for d in read_in.scan(root)["decisions"]] == ["tech", "design", "product", "marketing", "game-design"]


def test_secrets_links_and_large_files_are_never_read(root, tmp_path):
    w(root, "docs/decisions/0001-ok.md", MADR)
    w(root, "docs/decisions/0002-big.md", MADR + "x" * (read_in.MAX_BYTES + 1))
    outside = tmp_path / "outside.md"
    outside.write_text(MADR, encoding="utf-8")
    (root / "docs" / "decisions" / "0003-link.md").symlink_to(outside)
    w(root, ".env", "KEY=1\n")
    (root / "AGENTS.md").symlink_to(outside)
    w(root, "real/decisions/0004-in-a-linked-folder.md", MADR)
    (root / "adr").symlink_to(root / "real" / "decisions", target_is_directory=True)
    (root / "CHANGELOG.md").write_text("## [9.9.9] - 2026-01-01\n", encoding="utf-8")
    w(root, "memory-bank/projectbrief.md", "s" * 10)
    big = w(root, "docs/prd.md", "p" * (read_in.MAX_BYTES + 1))
    got = read_in.scan(root)
    assert [d["path"] for d in got["decisions"]] == ["docs/decisions/0001-ok.md"]
    assert [c["path"] for c in got["context"]] == ["memory-bank/projectbrief.md"] and big.is_file()
    assert got["releases"][0]["version"] == "9.9.9"                                                                    # a plain file, read
    (root / "CHANGELOG.md").unlink()
    (root / "CHANGELOG.md").symlink_to(outside)
    assert read_in.scan(root)["releases"] == []


def test_a_secret_among_the_context_files_is_left_out(root, monkeypatch):
    w(root, "AGENTS.md", "Agents\n")
    monkeypatch.setattr(read_in, "is_secret", lambda p: p == "AGENTS.md")
    assert read_in.scan(root)["context"] == []


# -- taking decisions ----------------------------------------------------------------------------------------------------------------------

def test_madr_and_nygard_decisions_go_into_the_projects_journal_on_their_day_with_their_status(root, sd):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    w(root, "docs/decisions/0002-sqlite.md", MADR_OLD)
    w(root, "docs/decisions/0003-buttons.md", UI_ADR)
    w(root, "doc/adr/0002-record.md", NYGARD)
    got = read_in.take(root, sd)
    assert got == {"decisions": 4, "leaders": 0, "done": 0, "releases": 0, "journals": 0}
    assert lines(sd) == [
        ("decision", "Decision 1: Use PostgreSQL for the data: Chosen option: \"PostgreSQL\", because it is boring and good.", "2026-03-04", "docs/decisions/0001-use-postgres.md"),
        ("decision", "Decision 2: Use SQLite for the data (superseded): Chosen option: \"PostgreSQL\", because it is boring and good.", "2026-01-10", "docs/decisions/0002-sqlite.md"),
        ("decision", "Decision 3: Round buttons (proposed): Buttons are round.", "2026-05-05", "docs/decisions/0003-buttons.md"),
        ("decision", "Decision 2: Record architecture decisions: We will use Architecture Decision Records.", "2016-02-12", "doc/adr/0002-record.md")]


def test_a_long_decision_line_is_cut_to_the_journals_line(root, sd):
    w(root, "docs/adr/0001-long.md", "---\nstatus: accepted\ndate: 2026-01-01\n---\n\n# Long\n\n## Decision Outcome\n\n" + "word " * 200 + "\n")
    read_in.take(root, sd)
    text = journals.read(sd, journals.PROJECT)[0]["text"]
    assert len(text) <= journals.TEXT_CHARS and text.endswith("…") and text.startswith("Decision 1: Long: word")


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def parties(host):
    return {"tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering"), "design": _party(host, "Design", "product-designer", ["ui-kit"], "design")}


def test_a_decision_also_goes_into_the_journal_of_the_projects_party_of_its_craft_and_none_where_there_is_none(host, parties):
    repo, sd, board = host.ideas.host.repo_root, host.ideas.state_dir, host.ideas.root(False)
    w(repo, "docs/decisions/0001-use-postgres.md", MADR)
    w(repo, "docs/decisions/0002-buttons.md", UI_ADR)
    w(repo, "docs/decisions/0003-pricing.md", "---\nstatus: accepted\n---\n\n# Pricing\n\n## Decision Outcome\n\nFree.\n")        # product: this project has no such party
    got = read_in.take(repo, sd, board=board)
    assert got == {"decisions": 3, "leaders": 2, "done": 0, "releases": 0, "journals": 0}
    assert [e["ref"] for e in journals.read(sd, parties["tech"])] == ["docs/decisions/0001-use-postgres.md"]
    assert [e["ref"] for e in journals.read(sd, parties["design"])] == ["docs/decisions/0002-buttons.md"]
    assert journals.read(sd, parties["tech"])[0]["kind"] == "decision" and journals.read(sd, parties["tech"])[0]["at"].startswith("2026-03-04")
    assert journals.read(sd, parties["tech"])[0]["text"] == journals.read(sd, journals.PROJECT)[0]["text"]


def test_the_boards_own_file_is_read_only_while_the_journal_holds_no_decision(root, sd):
    w(root, "docs/decisions.md", "# Decisions\n\n## 1. No accounts (2026-02-03, the person and Orkboard)\n\nNo sign-in in the first release.\n\n## 2. Pay once (2026-02-04, the leaders, all agreed)\n\nOne price.\n")
    assert [f["framework"] for f in read_in.scan(root, sd)["found"]] == ["The Board's decisions file"]
    assert read_in.take(root, sd)["decisions"] == 2
    assert lines(sd)[0] == ("decision", "Decision 1: No accounts: No sign-in in the first release.", "2026-02-03", "docs/decisions.md#1")
    journals.add(sd, journals.PROJECT, "decision", "Decision 3: made here", ref="3")
    assert read_in.scan(root, sd)["decisions"] == []                                                                    # a journal with a decision: the file is the Board's own


def test_the_boards_file_is_not_read_into_a_project_that_kept_decisions_already(root, sd):
    journals.add(sd, journals.PROJECT, "decision", "Decision 1: made here", ref="1")
    w(root, "docs/decisions.md", "## 1. No accounts (2026-02-03, the person)\n\nx\n")
    assert read_in.take(root, sd)["decisions"] == 0 and len(journals.read(sd, journals.PROJECT)) == 1


# -- specs and releases --------------------------------------------------------------------------------------------------------------------

def test_a_spec_done_is_kept_and_a_spec_in_work_is_not(root, sd):
    w(root, "specs/001-lobby/spec.md", "# Feature: Lobby\n")
    w(root, "specs/001-lobby/tasks.md", "- [x] one\n- [X] two\n")
    w(root, "specs/002-chat/spec.md", "# Chat\n")
    w(root, "specs/002-chat/tasks.md", "- [x] one\n- [ ] two\n")
    w(root, "specs/003-none/spec.md", "# None\n")                                                                        # no tasks: not done
    w(root, ".kiro/specs/auth/requirements.md", "No heading here\n")
    w(root, ".kiro/specs/auth/tasks.md", "- [x] login\n")
    w(root, "openspec/specs/cart/spec.md", "# Cart\n")
    w(root, "openspec/changes/archive/2025-old/proposal.md", "# Old change\n")
    w(root, "openspec/changes/new/proposal.md", "# New change\n")
    w(root, "docs/stories/1.1.story.md", "# Story 1.1\n\n## Status\n\nDone\n")
    w(root, "docs/stories/1.2.story.md", "# Story 1.2\n\nStatus: In Progress\n")
    specs = {s["name"]: s for s in read_in.scan(root)["specs"]}
    assert {n: s["done"] for n, s in specs.items()} == {"001-lobby": True, "002-chat": False, "003-none": False, "auth": True, "cart": True, "2025-old": True, "new": False,
                                                       "1.1": True, "1.2": False}
    assert specs["auth"]["title"] == "auth" and specs["001-lobby"]["title"] == "Feature: Lobby" and specs["cart"]["date"] == "" and specs["cart"]["framework"] == "OpenSpec"
    assert read_in.take(root, sd)["done"] == 5
    assert sorted(e["text"] for e in journals.read(sd, journals.PROJECT) if e["kind"] == "done") == sorted([
        "Spec “Feature: Lobby” (GitHub Spec Kit) was done", "Spec “auth” (Kiro) was done", "Spec “Cart” (OpenSpec) was done", "Spec “Old change” (OpenSpec) was done",
        "Spec “Story 1.1” (BMAD) was done"])


def test_a_spec_has_the_day_of_its_files_last_commit(fake_repo, sd):
    w(fake_repo, "specs/001-lobby/spec.md", "# Lobby\n")
    import subprocess
    subprocess.run(["git", "add", "."], cwd=str(fake_repo), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "spec", "--date=2026-06-07T12:00:00", "-q"], cwd=str(fake_repo), check=True, capture_output=True,
                   env={**__import__("os").environ, "GIT_COMMITTER_DATE": "2026-06-07T12:00:00"})
    assert read_in.scan(fake_repo)["specs"][0]["date"] == "2026-06-07"


def test_a_changelogs_releases_are_kept_and_unreleased_is_not(root, sd):
    w(root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n- Not yet\n\n## [1.2.0] - 2026-03-03\n\n### Added\n\n- Rounds that end by themselves\n- Another\n\n"
                            "## [1.1.0] - 2026-02-02\n\n### Fixed\n\n## 1.0.0 - 2026-01-01\n\n* The first\n")
    assert [(r["version"], r["date"], r["bullet"]) for r in read_in.scan(root)["releases"]] == [
        ("1.2.0", "2026-03-03", "Rounds that end by themselves"), ("1.1.0", "2026-02-02", ""), ("1.0.0", "2026-01-01", "The first")]
    assert read_in.take(root, sd)["releases"] == 3
    assert lines(sd) == [("done", "Version 1.2.0 was released: Rounds that end by themselves", "2026-03-03", "CHANGELOG.md#1.2.0"),
                         ("done", "Version 1.1.0 was released", "2026-02-02", "CHANGELOG.md#1.1.0"), ("done", "Version 1.0.0 was released: The first", "2026-01-01", "CHANGELOG.md#1.0.0")]


# -- an Orkboard export read back ----------------------------------------------------------------------------------------------------------

EXPORT_PROJECT = """---
orkboard-journal: _project
party: Project
exported: 2026-11-01T10:00:00
---

# The project's journal

- 2026-04-01 · decision · Decision 1: No accounts · in the first release
<!-- id=aaa111 idea=add-lobby on= ref=1 -->
- 2026-04-02 · done · Spec “Lobby” (Kiro) was done
<!-- id=bbb222 idea= on= ref= -->
- 2026-04-03 · nonsense · A kind the project's journal has not
<!-- id=ccc333 idea= on= ref= -->
"""
EXPORT_TECH = """---
orkboard-journal: tech
party: Tech
leader: Ada
digest: "Postgres, boring"
exported: 2026-11-01T10:00:00
---

# Tech's journal

- 2026-04-05 · overruled · You said no to “Add a lobby”: it breaks the cache.
<!-- id=ddd444 idea=add-lobby on=cache,auth ref=abc1234 -->
"""


def test_an_orkboard_export_is_read_back_entry_by_entry_as_it_was(root, sd):
    w(root, "docs/export/journals/project.md", EXPORT_PROJECT)
    w(root, ".orkcraft/export/journals/tech.md", EXPORT_TECH)
    w(root, "docs/export/journals/notes.md", "# Not a journal\n\n- 2026-04-01 · decision · x\n")
    got = read_in.scan(root)
    assert sorted((f["path"], f["n"]) for f in got["found"] if f["kind"] == "journals") == [(".orkcraft/export/journals", 1), ("docs/export/journals", 3)]
    assert read_in.take(root, sd)["journals"] == 3
    project = journals.read(sd, journals.PROJECT)
    assert [(e["kind"], e["text"], e["at"], e["idea"], e["on"], e["ref"]) for e in project] == [
        ("decision", "Decision 1: No accounts · in the first release", "2026-04-01", "add-lobby", [], "aaa111"),
        ("done", "Spec “Lobby” (Kiro) was done", "2026-04-02", "", [], "bbb222")]
    tech = journals.read(sd, "tech")
    assert [(e["kind"], e["text"], e["at"], e["idea"], e["on"], e["ref"]) for e in tech] == [
        ("overruled", "You said no to “Add a lobby”: it breaks the cache.", "2026-04-05", "add-lobby", ["cache", "auth"], "ddd444")]


def test_an_export_of_this_projects_own_journal_adds_nothing_twice(root, sd):
    e = journals.add(sd, journals.PROJECT, "decision", "Decision 1: No accounts", ref="1", at="2026-04-01")
    w(root, ".orkcraft/export/journals/project.md", f"---\norkboard-journal: _project\n---\n\n- 2026-04-01 · decision · Decision 1: No accounts\n<!-- id={e['id']} idea= on= ref=1 -->\n")
    assert read_in.take(root, sd)["journals"] == 0 and len(journals.read(sd, journals.PROJECT)) == 1


# -- once ----------------------------------------------------------------------------------------------------------------------------------

def test_take_twice_reads_nothing_twice_and_a_struck_entry_is_not_read_again(root, sd):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    w(root, "specs/001/spec.md", "# One\n")
    w(root, "specs/001/tasks.md", "- [x] a\n")
    w(root, "CHANGELOG.md", "## [1.0.0] - 2026-01-01\n")
    first = read_in.take(root, sd)
    assert first == {"decisions": 1, "leaders": 0, "done": 1, "releases": 1, "journals": 0}
    assert read_in.take(root, sd) == {"decisions": 0, "leaders": 0, "done": 0, "releases": 0, "journals": 0}
    mine = journals.read(sd, journals.PROJECT)
    assert len(mine) == 3
    assert journals.strike(sd, journals.PROJECT, mine[0]["id"], "not so") is not None
    assert read_in.take(root, sd)["decisions"] == 0 and len(journals.read(sd, journals.PROJECT)) == 2                  # struck: still not read in again
    w(root, "docs/decisions/0002-new.md", NYGARD)
    assert read_in.take(root, sd)["decisions"] == 1


def test_take_uses_the_scan_it_is_given(root, sd):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    got = read_in.scan(root)
    (root / "docs" / "decisions" / "0001-use-postgres.md").unlink()
    assert read_in.take(root, sd, got)["decisions"] == 1


def test_first_start_reads_in_once_and_never_again_by_itself(root, sd):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    assert read_in.first_start(root, sd)["decisions"] == 1
    w(root, "docs/decisions/0002-new.md", NYGARD)
    assert read_in.first_start(root, sd) is None and len(journals.read(sd, journals.PROJECT)) == 1


# -- the brief's sources -------------------------------------------------------------------------------------------------------------------

def test_the_start_files_are_the_context_files_first_then_the_readme_and_the_top_of_docs(root):
    w(root, "README.md", "# Party\n")
    w(root, "docs/a-vision.md", "Vision\n")
    w(root, "docs/prd.md", "# PRD\n" + "p" * 5000)
    w(root, ".specify/memory/constitution.md", "# Constitution\n")
    w(root, ".kiro/steering/product.md", "Product steering\n")
    w(root, ".kiro/steering/tech.md", "Tech steering\n")                                     # the code's, not the product's
    w(root, "memory-bank/projectbrief.md", "Brief\n")
    w(root, "memory-bank/progress.md", "Progress\n")
    w(root, "AGENTS.md", "Agents\n")
    w(root, "CLAUDE.md", "Claude, to agents\n")                                              # speaks to agents, not of the product
    got = project_facts.start_files(root)
    assert [f["path"] for f in got] == [".specify/memory/constitution.md", ".kiro/steering/product.md", "docs/prd.md", "memory-bank/projectbrief.md", "AGENTS.md", "README.md",
                                       "docs/a-vision.md"]
    assert len(next(f for f in got if f["path"] == "docs/prd.md")["text"]) == project_facts.START_CHARS


def test_the_start_files_are_six_of_context_and_docs_in_all_with_the_readme_beside(root):
    w(root, "README.md", "# Party\n")
    for p in (".specify/memory/constitution.md", ".kiro/steering/product.md", "openspec/project.md", "docs/prd.md", "memory-bank/projectbrief.md", "memory-bank/productContext.md",
              "AGENTS.md"):
        w(root, p, f"{p}\n")
    w(root, "docs/z-doc.md", "z\n")
    got = [f["path"] for f in project_facts.start_files(root)]
    assert got == [".specify/memory/constitution.md", ".kiro/steering/product.md", "openspec/project.md", "docs/prd.md", "memory-bank/projectbrief.md",
                   "memory-bank/productContext.md", "README.md"] and len(got) - 1 == project_facts.START_DOCS


# -- the host ------------------------------------------------------------------------------------------------------------------------------

def test_the_first_start_reads_in_once_quietly_before_the_questions(host, parties, monkeypatch):
    repo, sd = host.ideas.host.repo_root, host.ideas.state_dir
    asked = []
    monkeypatch.setattr(host.ideas.keeper, "project_ask", lambda: asked.append(journals.read(sd, journals.PROJECT)) or True, raising=False)
    w(repo, "docs/decisions/0001-use-postgres.md", MADR)
    assert host.ideas.project_start() == {"asked": True} and len(asked[0]) == 1                # the journal holds the history when the questions begin
    assert [e["ref"] for e in journals.read(sd, journals.PROJECT)] == ["docs/decisions/0001-use-postgres.md"]
    assert [e["ref"] for e in journals.read(sd, parties["tech"])] == ["docs/decisions/0001-use-postgres.md"]
    w(repo, "docs/decisions/0002-new.md", NYGARD)
    host.ideas.project_start()
    assert len(journals.read(sd, journals.PROJECT)) == 1                                      # never again by itself


def test_the_first_start_is_not_failed_by_a_reading_that_fails(host, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no")
    monkeypatch.setattr(read_in, "first_start", boom)
    monkeypatch.setattr(host.ideas.keeper, "project_ask", lambda: True, raising=False)
    assert host.ideas.project_start() == {"asked": True}                                      # the questions are asked all the same


def test_the_commands_scan_and_take(host, parties):
    repo, sd = host.ideas.host.repo_root, host.ideas.state_dir
    assert isinstance(host.ideas, ReadInMixin) and set(read_in_commands(host.ideas)) <= set(host.commands)
    w(repo, "docs/decisions/0001-use-postgres.md", MADR)
    got = host.commands["ideas.read_in_scan"]({})
    assert got == {"found": [{"framework": "ADRs (MADR)", "kind": "decisions", "path": "docs/decisions", "n": 1}]}
    assert host.commands["ideas.read_in_take"]({}) == {"decisions": 1, "leaders": 1, "done": 0, "releases": 0, "journals": 0}
    assert host.commands["ideas.read_in_take"]({}) == {"decisions": 0, "leaders": 0, "done": 0, "releases": 0, "journals": 0}
    assert len(journals.read(sd, journals.PROJECT)) == 1


# -- orkboard import -----------------------------------------------------------------------------------------------------------------------

def test_orkboard_import_says_what_it_found_and_what_it_read_in_and_dry_run_writes_nothing(root, capsys):
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    w(root, "docs/decisions/0002-sqlite.md", MADR_OLD)
    w(root, "specs/001/spec.md", "# One\n")
    w(root, "specs/001/tasks.md", "- [x] a\n")
    w(root, "CHANGELOG.md", "## [1.0.0] - 2026-01-01\n\n## [0.9.0] - 2025-12-01\n")
    assert board_cli.run(["import", str(root), "--dry-run"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[:3] == ["ADRs (MADR) · docs/decisions · 2 decisions", "GitHub Spec Kit · specs · 1 spec", "Keep a Changelog · CHANGELOG.md · 2 releases"]
    assert out[-1] == "Would read in: 2 decisions, 1 spec done, 2 releases"
    assert not (root / ".orkcraft").exists()
    assert board_cli.run(["import", str(root)]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "Read in: 2 decisions, 1 spec done, 2 releases"
    assert len(journals.read(root / ".orkcraft", journals.PROJECT)) == 5
    assert board_cli.run(["import", str(root)]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "Read in: 0 decisions, 0 specs done, 0 releases"


def test_orkboard_import_with_nothing_to_read_in_names_the_shapes_it_looked_for(root, capsys):
    w(root, "README.md", "# Nothing\n")
    code, text = read_in.run_cli(root)
    assert code == 0 and text.startswith("Nothing to read in:") and "MADR or Nygard" in text and "Spec Kit" in text and "OpenSpec" in text
    assert board_cli.run(["import", str(root)]) == 0
    assert "Nothing to read in" in capsys.readouterr().out
    assert board_cli.run(["import", str(root / "none")]) == 2


def test_the_cli_counts_the_leaders_copies_where_the_boards_pages_are_in_the_wiki(root):
    wiki = root / "llm-wiki" / "general"
    slug, _new = ideas.save_goal(wiki, None, "Tech", "About Tech", None, "normal", craft="engineering")
    goal_team.set_team(wiki, slug, ["grunt"], leader="architect")
    w(root, "docs/decisions/0001-use-postgres.md", MADR)
    code, text = read_in.run_cli(root, dry=True)
    assert code == 0 and text.splitlines()[-1] == "Would read in: 1 decision (1 also into leaders' journals), 0 specs done, 0 releases"
    assert read_in.run_cli(root)[1].splitlines()[-1] == "Read in: 1 decision (1 also into leaders' journals), 0 specs done, 0 releases"
    assert [e["ref"] for e in journals.read(root / ".orkcraft", slug)] == ["docs/decisions/0001-use-postgres.md"]


def test_the_architecture_keeps_orkboards_rule():
    import ast
    from pathlib import Path
    src = Path(read_in.__file__).read_text(encoding="utf-8")
    mods = {n.module for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}
    assert not any(m.startswith(("orkcraft", "textual", "rich", "orkboard.gui")) for m in mods)
