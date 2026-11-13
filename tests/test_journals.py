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


def test_a_struck_entry_is_never_read_into_a_call_but_is_kept_marked(sd):
    a = journals.add(sd, "tech", "came_back", "The lobby came back at Review", idea="add-lobby")
    b = journals.add(sd, "tech", "stance", "Go on the timer", idea="timer")
    got = journals.strike(sd, "tech", a["id"], "It came back for another reason")
    assert got["struck"]["why"] == "It came back for another reason"
    assert journals.read(sd, "tech") == [b] and journals.read(sd, "tech", struck=True)[0]["struck"]["why"].startswith("It came back")
    assert "lobby" not in journals.text(sd, "tech", idea="add-lobby")
    assert journals.strike(sd, "tech", a["id"]) is None and journals.strike(sd, "tech", "../x") is None and journals.strike(sd, "tech", "nope") is None


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


# -- the Markdown in any folder (spec 151 B.1) ---------------------------------------------------------------------------------------------


def test_a_leaders_journal_keeps_what_it_accepted_sent_back_and_learned_of_a_step_spec_152_b(tmp_path):
    from orkboard.realm import journal_notes
    sd, root = tmp_path / "state", tmp_path / "wiki"
    assert {"accepted", "sent_back", "learned"} <= set(journals.LEADER_KINDS) and not {"accepted", "sent_back", "learned"} & set(journals.PROJECT_KINDS)
    journal_notes.accepted(sd, root, "lobby", "tech", 3, 3, ["The cache is one file", "Tests live beside it", "a third"])
    journal_notes.sent_back(sd, root, "lobby", "tech", 2)
    journal_notes.sent_back(sd, root, "lobby", "tech", 1)
    got = [(e["kind"], e["text"]) for e in journals.of_goal(sd, "tech", "lobby")]
    assert got[0][0] == "accepted" and got[0][1].startswith("You accepted tech's step of “lobby”: 3 of 3 Done when met")
    assert [k for k, _t in got] == ["accepted", "learned", "learned", "sent_back", "sent_back"] and got[1][1] == "The cache is one file"      # two lines learned at most
    assert got[3][1].startswith("You sent back 2 things of tech's step of") and got[4][1].startswith("You sent back 1 thing of tech's step of")
    journal_notes.accepted(sd, root, "lobby", "No Such Party", 1, 1)                                  # a journal never fails what it records
    assert journals.read(sd, "tech")[0]["kind"] == "accepted"


