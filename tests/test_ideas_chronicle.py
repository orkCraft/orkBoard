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
