"""Spec 125 A (docs/specs/125-the-journals.md, decisions §203): the project's journal and each leader's, kept append only by code, struck by the person, digested
by the leader, and given to a call: the digest, this goal's and these parts' entries, then the latest."""
from __future__ import annotations

import pytest

from orkboard.realm import journals


@pytest.fixture
def sd(tmp_path):
    return tmp_path / "state"


def test_an_entry_is_kept_in_its_scope_with_its_goal_its_parts_and_its_ref(sd):
    e = journals.add(sd, "tech", "overruled", "  You said no to “Add a lobby”:\n it breaks the cache. ", idea="add-lobby", on=["cache", "", 3], ref="12")
    assert e["text"] == "You said no to “Add a lobby”: it breaks the cache." and e["on"] == ["cache"] and e["ref"] == "12" and len(e["id"]) == 12
    assert journals.read(sd, "tech") == [e] and journals.read(sd, journals.PROJECT) == [] and journals.read(sd, "design") == []
    assert (sd / "journals" / "tech.jsonl").is_file()
    assert journals.add(sd, "tech", "stance", "   ") is None                                     # nothing to keep
    assert len(journals.add(sd, "tech", "stance", "x" * 900)["text"]) == journals.TEXT_CHARS


def test_a_scope_and_a_kind_must_be_ones_and_a_project_kind_is_not_a_leaders(sd):
    with pytest.raises(ValueError):
        journals.add(sd, "Tech!", "stance", "x")
    with pytest.raises(ValueError):
        journals.add(sd, "tech", "done", "x")                                                     # a project's kind
    assert journals.add(sd, "tech", "decision", "ADR 3: Postgres")["kind"] == "decision"             # a decision of its craft, read in (spec 126 B)
    with pytest.raises(ValueError):
        journals.add(sd, journals.PROJECT, "overruled", "x")
    assert journals.add(sd, journals.PROJECT, "decision", "Decision 4: no accounts", ref="4")["kind"] == "decision"
    assert journals.kind_of(journals.PROJECT) == "project" and journals.kind_of("game-design") == "leader"


def test_a_line_that_is_not_an_entry_is_skipped(sd):
    journals.add(sd, "tech", "stance", "One")
    with (sd / "journals" / "tech.jsonl").open("a") as f:
        f.write("not json\n{\"id\": \"x\", \"kind\": \"nope\", \"text\": \"t\"}\n[1]\n")
    journals.add(sd, "tech", "stance", "Two")
    assert [e["text"] for e in journals.read(sd, "tech")] == ["One", "Two"]


def test_a_struck_entry_is_never_read_into_a_call_but_is_kept_marked(sd):
    a = journals.add(sd, "tech", "came_back", "The lobby came back at Review", idea="add-lobby")
    b = journals.add(sd, "tech", "stance", "Go on the timer", idea="timer")
    got = journals.strike(sd, "tech", a["id"], "It came back for another reason")
    assert got["struck"]["why"] == "It came back for another reason"
    assert journals.read(sd, "tech") == [b] and journals.read(sd, "tech", struck=True)[0]["struck"]["why"].startswith("It came back")
    assert "lobby" not in journals.text(sd, "tech", idea="add-lobby")
    assert journals.strike(sd, "tech", a["id"]) is None and journals.strike(sd, "tech", "../x") is None and journals.strike(sd, "tech", "nope") is None


def test_the_digest_and_what_came_after_it(sd):
    a = journals.add(sd, "design", "stance", "One")
    b = journals.add(sd, "design", "stance", "Two")
    assert journals.digest(sd, "design") == {} and journals.since_digest(sd, "design") == [a, b]
    journals.save_digest(sd, "design", "Screens grow; the person keeps the menu flat.", a["id"])
    assert journals.digest(sd, "design")["text"] == "Screens grow; the person keeps the menu flat." and journals.since_digest(sd, "design") == [b]
    with pytest.raises(ValueError):
        journals.save_digest(sd, "design", "  ", b["id"])
    journals.save_digest(sd, "design", "y" * 2000, "gone")
    assert len(journals.digest(sd, "design")["text"]) == journals.DIGEST_CHARS and journals.since_digest(sd, "design") == [a, b]


def test_a_call_is_given_the_digest_then_this_goals_and_these_parts_entries_then_the_latest_within_its_chars(sd):
    assert journals.text(sd, "tech") == ""
    old = journals.add(sd, "tech", "overruled", "Lobby: went on against my no", idea="add-lobby")
    part = journals.add(sd, "tech", "concern_dismissed", "Cache fan-in: not a problem, said the person", on=["cache"])
    for i in range(40):
        journals.add(sd, "tech", "stance", f"Go on goal {i}: small and safe", idea=f"g{i}")
    journals.save_digest(sd, "tech", "The person takes risks on speed, not on data.", part["id"])
    got = journals.text(sd, "tech", idea="add-lobby", on=["cache"], chars=600)
    lines = got.splitlines()
    assert lines[0].startswith("What you said before and what came of it") and lines[1] == "In short: The person takes risks on speed, not on data."
    assert old["text"] in got and part["text"] in got and "goal 39" in got and "goal 0:" not in got        # this goal's and this part's, then the newest
    assert len(got) <= 600
    assert got.index("Lobby") < got.index("Cache") < got.index("goal 39")                                 # oldest first
    assert journals.text(sd, journals.PROJECT) == ""
    journals.add(sd, journals.PROJECT, "decision", "Decision 3: no accounts", ref="3")
    assert journals.text(sd, journals.PROJECT).startswith("What the project decided and what came of it")


def test_an_entry_read_in_keeps_the_day_it_happened_and_its_ref_is_known(sd):
    e = journals.add(sd, journals.PROJECT, "decision", "Decision 3: Postgres", ref="docs/adr/0003-postgres.md", at="2024-05-02")
    assert e["at"] == "2024-05-02"
    assert journals.add(sd, journals.PROJECT, "decision", "x", at="last spring")["at"] != "last spring"      # not a day: now
    journals.strike(sd, journals.PROJECT, e["id"])
    assert "docs/adr/0003-postgres.md" in journals.refs(sd, journals.PROJECT)                                   # struck, still known: never read in twice


def test_each_journal_has_its_markdown_mirror_written_again_after_each_change(sd):
    from orkboard.realm import read_in
    a = journals.add(sd, "tech", "stance", "On “Lobby” you said no: the cache", idea="lobby", on=["cache"])
    md = sd / "journals" / "tech.md"
    assert md.is_file() and "orkboard-journal: tech" in md.read_text() and "On “Lobby” you said no: the cache" in md.read_text()
    journals.strike(sd, "tech", a["id"])
    assert "Lobby" not in md.read_text()                                                     # struck: gone from the mirror too
    journals.add(sd, journals.PROJECT, "decision", "Decision 3: Postgres", ref="3")
    journals.save_digest(sd, journals.PROJECT, "The project keeps its data in Postgres.", "x")
    got = read_in.parse_export((sd / "journals" / "_project.md").read_text())
    assert got["scope"] == journals.PROJECT and [e["text"] for e in got["entries"]] == ["Decision 3: Postgres"]
    assert "digest:" in (sd / "journals" / "_project.md").read_text()
