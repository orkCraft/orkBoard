"""Spec 99 B §2.2–§2.3 (docs/specs/99-a-goals-way.md, decisions §153.4, §156.7, §156.10): the project's facts by party, kept in
`facts.json`: an answer or a fact read from the files with its party and who gave it; the common core (whom it is for, what hurts them, what it
leaves out, and the brief's other half: why this, what it must always be, how it earns; spec 124 A) in about 1,000 characters; what a leader's call is given (the core, its own party's, another party's only when the route has it, a member
none); a reading never replacing a person's answer; and the start's files, chosen by code. No model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import project_facts


@pytest.fixture
def sd(tmp_path: Path) -> Path:
    return tmp_path / "state"


def route(*parties: str) -> list[dict]:
    return [{"party": p, "leader": f"{p}-lead"} for p in parties]


# -- §2.2 the facts by party -----------------------------------------------------------------------------------------------------------

def test_an_answer_is_kept_with_its_party_who_gave_it_and_when(sd):
    project_facts.keep(sd, "tech", "stack_choice", "Plain Python, no framework", "person")
    project_facts.keep(sd, "design", "look", "Dark, monochrome", "read")
    tech, = project_facts.of(sd, "tech")
    assert (tech["key"], tech["text"], tech["by"]) == ("stack_choice", "Plain Python, no framework", "person") and tech["at"]
    assert [f["key"] for f in project_facts.of(sd, "design")] == ["look"] and project_facts.of(sd, "release") == []
    kept = json.loads((sd / "facts.json").read_text())
    assert set(kept) == {"common", "common_by", "party"} and set(kept["party"]) == {"tech", "design"} and kept["common"] == {}


def test_the_common_core_is_whom_it_is_for_what_hurts_and_what_it_leaves_out(sd):
    assert project_facts.common(sd) == ""
    project_facts.keep(sd, "product", "hurts", "Rounds drag on when one player is slow", "person")
    project_facts.keep(sd, "product", "for_whom", "Friends playing together at one TV", "read")
    assert project_facts.common(sd) == ("Whom it is for: Friends playing together at one TV\n"
                                        "What hurts them: Rounds drag on when one player is slow")
    project_facts.keep(sd, "product", "leaves_out", "Accounts and online matchmaking", "person")
    assert project_facts.common(sd).splitlines()[-1] == "What it leaves out: Accounts and online matchmaking"
    assert project_facts.answered(sd) == {"for_whom", "hurts", "leaves_out"}


# -- §2.2 what a call is given ---------------------------------------------------------------------------------------------------------

def test_a_leader_is_given_the_core_its_own_partys_facts_and_another_partys_only_when_the_route_has_it(sd):
    project_facts.keep(sd, "product", "for_whom", "Friends at one TV", "person")
    project_facts.keep(sd, "tech", "runs_on", "Node 22", "person")
    project_facts.keep(sd, "design", "look", "Dark and flat", "person")
    project_facts.keep(sd, "release", "channel", "A static site", "read")
    alone = project_facts.for_call(sd, "tech", route("tech"))
    assert alone == "What the project is:\nWhom it is for: Friends at one TV\n\nWhat is known for tech:\n- Node 22"
    both = project_facts.for_call(sd, "tech", route("design", "tech"))
    assert both.endswith("What is known for tech:\n- Node 22\n\nWhat is known for design:\n- Dark and flat") and "release" not in both
    assert project_facts.for_call(sd, "design", route("design")).splitlines()[-1] == "- Dark and flat"
    assert project_facts.for_call(sd, "tech", ["design"]).count("What is known for") == 2                     # a route of names too
    assert project_facts.for_call(sd, "tech", None) == alone and project_facts.for_call(sd, "tech") == alone
    assert project_facts.for_call(sd, "tech", route("tech", "tech", "tech")) == alone                       # a party once


# -- §2.3 the start's files ------------------------------------------------------------------------------------------------------------

def test_the_start_files_are_the_readme_and_the_top_of_docs_by_name_the_first_2000_characters_each(tmp_path):
    (tmp_path / "docs" / "deep").mkdir(parents=True)
    (tmp_path / "README.md").write_text("# Party\n" + "a" * 5000)
    for name in ("b-flow.md", "A-vision.md", "notes.txt", "c.md"):
        (tmp_path / "docs" / name).write_text(f"{name} text\n")
    (tmp_path / "docs" / "deep" / "d.md").write_text("not at the top\n")
    (tmp_path / "CHANGELOG.md").write_text("not asked\n")
    got = project_facts.start_files(tmp_path)
    assert [f["path"] for f in got] == ["README.md", "docs/A-vision.md", "docs/b-flow.md", "docs/c.md"]
    assert len(got[0]["text"]) == 2000 and got[0]["text"].startswith("# Party") and got[1]["text"] == "A-vision.md text"


def test_the_start_files_are_six_docs_at_most_none_secret_none_linked_and_none_when_there_is_nothing(tmp_path):
    assert project_facts.start_files(tmp_path) == []
    (tmp_path / "docs").mkdir()
    for n in range(9):
        (tmp_path / "docs" / f"d{n}.md").write_text(f"doc {n}\n")
    (tmp_path / "docs" / "empty.md").write_text("   \n")
    (tmp_path / "docs" / ".env.md").write_text("KEY=1\n")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("secret place\n")
    (tmp_path / "docs" / "aaa-link.md").symlink_to(outside)
    (tmp_path / "readme").write_text("plain readme\n")
    got = project_facts.start_files(tmp_path)
    assert got[0] == {"path": "readme", "text": "plain readme"}
    assert [f["path"] for f in got[1:]] == [f"docs/d{n}.md" for n in range(6)]          # a file left out does not take a slot


# -- §8 what the project's questions keep (spec 99 G: gui/ideas_project_q.py) ----------------------------------------------------------

def test_the_projects_answers_are_in_every_leaders_call_whatever_party_asked_and_a_left_to_the_leader_pick_is_read(sd):
    project_facts.keep(sd, "product", "for_whom", "Friends at one TV", "person")
    project_facts.keep(sd, "product", "hurts", "Slow rounds", "read")                      # *Let … decide*: the leader's pick, kept `read`
    project_facts.keep(sd, "product", "leaves_out", "Accounts", "person")
    for party in ("tech", "design", "release"):                                            # the core reaches a party that is not on the asker's route
        text = project_facts.for_call(sd, party, route(party))
        assert text == "What the project is:\nWhom it is for: Friends at one TV\nWhat hurts them: Slow rounds\nWhat it leaves out: Accounts"
    assert [(f["key"], f["by"]) for f in project_facts.of(sd, "product")] == [("for_whom", "person"), ("hurts", "read"), ("leaves_out", "person")]
    assert project_facts.answered(sd) == {"for_whom", "hurts", "leaves_out"}                # a question answered is never asked again
    project_facts.keep(sd, "product", "hurts", "Another reading", "read")                  # a reading replaces a reading …
    assert project_facts.common(sd).splitlines()[1] == "What hurts them: Another reading"
    project_facts.keep(sd, "product", "hurts", "Players waiting", "person")
    project_facts.keep(sd, "product", "hurts", "A third reading", "read")                  # … never the person's answer
    assert project_facts.common(sd).splitlines()[1] == "What hurts them: Players waiting"


def test_the_orkmasters_one_answer_with_neither_party_is_the_common_core_and_is_asked_no_more(sd):
    project_facts.keep(sd, "orkmaster", "for_whom", "a mobile app for tennis clubs", "person")
    assert project_facts.for_call(sd, "tech", route("tech")) == "What the project is:\nWhom it is for: a mobile app for tennis clubs"
    assert "for_whom" in project_facts.answered(sd) and project_facts.of(sd, "orkmaster")[0]["by"] == "person"


# -- spec 100 F: a fact dropped (the person's empty text) ------------------------------------------------------------------------------


