"""Spec 134 A.7 (docs/specs/134-release-keeps-the-chronicle.md; decisions §238): the chronicle's commands as the host has them: each one's shape, only the newest chapter open, a chapter that is gone, a goal as it was
with its quality record, and that they read and write nothing. No model."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import findings, idea_flag, ideas, spec_sections

LOG = """# Decisions

## 1. First (1 October 2026, the owner)

Why: one says purple.

## 2. Second (12 October 2026, the owner)

Changes: 1.

Why: two.

## 3. Third (24 October 2026, the owner)

Why: three.
"""


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.root()                                                                  # the Board's own tree stands, as it does in use: the log is read in it
    base, rel = h.ideas.keeper._decisions()
    (base / rel).parent.mkdir(parents=True, exist_ok=True)
    (base / rel).write_text(LOG, encoding="utf-8")
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def tag(repo: Path, name: str, day: str) -> None:
    env = {**os.environ, "GIT_COMMITTER_DATE": f"{day}T12:00:00", "GIT_AUTHOR_DATE": f"{day}T12:00:00"}
    subprocess.run(["git", "tag", "-a", name, "-m", name], cwd=repo, check=True, capture_output=True, env=env)


def through(host, title: str, day: str, decision: int = 0) -> str:
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, title, "general", st)
    ideas._write_json(idea_flag.flag_path(st, slug), {"at": f"{day}T10:00:00", "by": "gate", "commit": "abc"})
    if decision:
        spec_sections.save_record(st, slug, {"decision": {"title": f"D{decision}", "number": decision}})
    return slug


def tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_the_chronicle_has_the_newest_chapter_open_and_the_others_as_a_line(host, fake_repo):
    tag(fake_repo, "v0.1", "2026-10-10")
    tag(fake_repo, "v0.2", "2026-10-20")
    a = through(host, "Purple buttons", "2026-10-05", 1)
    b = through(host, "Faster pages", "2026-10-15", 2)
    c = through(host, "Next one", "2026-10-25")
    got = host.command("ideas.chronicle", {})
    assert got["kind"] == "tag" and got["earlier"] == {"kind": "tag", "name": "v0.2", "day": "2026-10-20"}
    new, old = got["chapters"]
    assert (new["name"], new["open"]) == ("v0.2", True) and [g["idea"] for g in new["goals"]] == [b] and new["decisions"] == []
    assert old == {"id": "v:v0.1", "kind": "tag", "name": "v0.1", "day": "2026-10-10", "open": False}
    assert [g["idea"] for g in got["unreleased"]["goals"]] == [c] and [d["number"] for d in got["unreleased"]["decisions"]] == [3]
    one = host.command("ideas.chronicle_chapter", {"id": "v:v0.1"})
    assert one["open"] is True and [g["idea"] for g in one["goals"]] == [a] and one["name"] == "v0.1"
    with pytest.raises(CommandError, match="That chapter is gone"):
        host.command("ideas.chronicle_chapter", {"id": "v:v9"})


def test_the_line_is_the_last_version_alone_and_none_for_a_project_with_no_past(host, fake_repo):
    assert host.command("ideas.chronicle_line", {}) == {"earlier": None}
    tag(fake_repo, "v0.1", "2026-10-10")
    assert host.command("ideas.chronicle_line", {}) == {"earlier": {"kind": "tag", "name": "v0.1", "day": "2026-10-10"}}


def test_find_goal_and_decision(host, fake_repo):
    tag(fake_repo, "v0.1", "2026-10-10")
    a = through(host, "Purple buttons", "2026-10-05", 1)
    got = host.command("ideas.chronicle_find", {"query": "purple"})
    assert got["found"] == 1 and got["chapters"][0]["goals"][0]["idea"] == a
    assert host.command("ideas.chronicle_find", {"query": ""})["chapters"] == []
    findings.add(host.ideas.state_dir, {"source": "verdict", "idea": a, "party": "general", "on": "src", "found": "Not quite: changed src"})
    goal = host.command("ideas.chronicle_goal", {"idea": a})
    assert goal["idea"] == a and goal["decision"]["number"] == 1 and "purple" in goal["decision"]["entry"]
    assert [c["number"] for c in goal["changed_by"]] == [2] and [f["on"] for f in goal["quality"]["findings"]] == ["src"]
    with pytest.raises(CommandError, match="not in the chronicle"):
        host.command("ideas.chronicle_goal", {"idea": ideas.add_idea(host.ideas.root(), "Not through", "general", host.ideas.state_dir)})
    dec = host.command("ideas.chronicle_decision", {"number": 1})
    assert dec["goal"] == a and dec["changed_by"][0]["number"] == 2 and "purple" in dec["entry"]
    for bad in ({"number": 99}, {"number": "1"}, {}):
        with pytest.raises(CommandError, match="not in the log"):
            host.command("ideas.chronicle_decision", bad)


def test_the_commands_read_and_write_nothing(host, fake_repo):
    tag(fake_repo, "v0.1", "2026-10-10")
    a = through(host, "Purple buttons", "2026-10-05", 1)
    before = tree(fake_repo / ".orkcraft") if (fake_repo / ".orkcraft").is_dir() else {}
    pages_before = tree(host.ideas.root())
    for name, args in (("ideas.chronicle", {}), ("ideas.chronicle_line", {}), ("ideas.chronicle_chapter", {"id": "v:v0.1"}), ("ideas.chronicle_find", {"query": "purple"}),
                       ("ideas.chronicle_goal", {"idea": a}), ("ideas.chronicle_decision", {"number": 1})):
        host.command(name, args)
    assert (tree(fake_repo / ".orkcraft") if (fake_repo / ".orkcraft").is_dir() else {}) == before and tree(host.ideas.root()) == pages_before
    assert not (fake_repo / ".orkcraft" / "usage" / "events.jsonl").exists() or "chronicle" not in (fake_repo / ".orkcraft" / "usage" / "events.jsonl").read_text()


# -- by party (spec 150 E1.4, decisions §254.7) ---------------------------------------------------------------------------------------------

def _by_party(host, fake_repo):
    """Three goals through the portal (decisions 1, 2, 3) between two versions; Design's route held A and C, Tech's C; decision 2 is cut for Tech and Design, though its goal B is neither's."""
    from orkboard.realm import slices
    tag(fake_repo, "v0.1", "2026-10-10")
    tag(fake_repo, "v0.2", "2026-10-20")
    a = through(host, "Purple buttons", "2026-10-05", 1)
    b = through(host, "Faster pages", "2026-10-15", 2)
    c = through(host, "Next one", "2026-10-25", 3)
    st = host.ideas.state_dir
    ideas.save_state(st, a, route=[{"party": "design"}])
    ideas.save_state(st, c, route=[{"party": "design"}, {"party": "tech"}])
    (old,) = slices.add_cut(st, 1, {"design": {"says": "Buttons are purple.", "points": ["1"]}})
    slices.add_cut(st, 2, {"tech": {"says": "Pages are fast.", "points": ["2"]}, "design": {"says": "Pages load behind a skeleton.", "points": ["2"]}})
    slices.add_cut(st, 3, {"tech": {"says": "One build.", "points": ["3"]}, "design": {"says": "Buttons are green now.", "points": ["3"], "replaces": [old["id"]]}})
    return a, b, c


def test_the_chronicle_read_by_party_holds_the_goals_its_route_held_and_the_decisions_it_keeps_a_slice_of(host, fake_repo):
    a, b, c = _by_party(host, fake_repo)
    whole = host.command("ideas.chronicle", {})
    assert [g["idea"] for g in whole["unreleased"]["goals"]] == [c] and [g["idea"] for g in whole["chapters"][0]["goals"]] == [b]
    got = host.command("ideas.chronicle", {"party": "design"})
    new, old = got["chapters"]
    assert new["goals"] == [] and [d["number"] for d in new["decisions"]] == [2]                       # B is not Design's, its decision 2 is: a row of its own
    assert [g["idea"] for g in got["unreleased"]["goals"]] == [c] and got["unreleased"]["decisions"] == []
    one = host.command("ideas.chronicle_chapter", {"id": "v:v0.1", "party": "design"})
    assert [g["idea"] for g in one["goals"]] == [a] and one["decisions"] == []                          # decision 1 stands under its goal A (its slice was replaced by 3's: still Design's)
    tech = host.command("ideas.chronicle", {"party": "tech"})
    assert [g["idea"] for g in tech["unreleased"]["goals"]] == [c] and [d["number"] for d in tech["chapters"][0]["decisions"]] == [2]
    assert host.command("ideas.chronicle_chapter", {"id": "v:v0.1", "party": "tech"})["goals"] == []
    nobody = host.command("ideas.chronicle", {"party": "nobody"})
    assert nobody["unreleased"] == {"goals": [], "decisions": []} and nobody["chapters"][0]["goals"] == [] and nobody["chapters"][0]["decisions"] == []


def test_the_search_and_the_line_read_by_party_too(host, fake_repo):
    a, _b, _c = _by_party(host, fake_repo)
    found = host.command("ideas.chronicle_find", {"query": "purple", "party": "design"})
    assert found["found"] == 1 and found["chapters"][0]["goals"][0]["idea"] == a
    assert host.command("ideas.chronicle_find", {"query": "purple", "party": "tech"})["found"] == 0
    assert host.command("ideas.chronicle_find", {"query": "purple"})["found"] == 1
    assert host.command("ideas.chronicle_line", {"party": "design"})["earlier"]["name"] == "v0.2"


def test_chronicle_last_is_the_partys_last_decisions_newest_first_by_code(host, fake_repo):
    _by_party(host, fake_repo)
    got = host.command("ideas.chronicle_last", {"party": "design"})["decisions"]
    assert [d["number"] for d in got] == [3, 2, 1]
    assert set(got[0]) == {"number", "title", "element", "kind", "parties", "version", "at"} and got[0]["kind"] == "decision"
    assert (got[0]["title"], got[0]["parties"], got[0]["version"]) == ("Third", ["tech", "design"], "")                 # not out yet: no version
    assert (got[1]["version"], got[1]["parties"]) == ("v0.2", ["tech", "design"]) and got[2]["version"] == "v0.1" and got[2]["parties"] == ["design"]
    assert [d["number"] for d in host.command("ideas.chronicle_last", {"party": "design", "n": 2})["decisions"]] == [3, 2]
    assert [d["number"] for d in host.command("ideas.chronicle_last", {"party": "tech"})["decisions"]] == [3, 2]
    assert [d["number"] for d in host.command("ideas.chronicle_last", {})["decisions"]] == [3, 2, 1]                     # no party: the whole project
    assert host.command("ideas.chronicle_last", {"party": "nobody"})["decisions"] == []
    assert len(host.command("ideas.chronicle_last", {"n": 99})["decisions"]) == 3 and len(host.command("ideas.chronicle_last", {"n": 0})["decisions"]) == 3
    with pytest.raises(CommandError, match="n is not a number"):
        host.command("ideas.chronicle_last", {"n": "2"})


def test_the_party_reads_write_nothing(host, fake_repo):
    _by_party(host, fake_repo)
    before = tree(host.ideas.root())
    host.command("ideas.chronicle_last", {"party": "design"})
    host.command("ideas.chronicle", {"party": "design"})
    assert tree(host.ideas.root()) == before
