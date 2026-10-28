"""Spec 99 B §2.2–§2.3 (docs/specs/99-a-goals-way.md, decisions §153.4, §156.7, §156.10): the project's facts by party, kept in
`facts.json`: an answer or a fact read from the files with its party and who gave it; the common core (whom it is for, what hurts them, what it
leaves out) in about 600 characters; what a leader's call is given (the core, its own party's, another party's only when the route has it, a member
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


def test_the_same_key_kept_again_is_replaced_and_a_reading_never_replaces_the_persons_answer(sd):
    project_facts.keep(sd, "tech", "runs_on", "Node 18", "read")
    project_facts.keep(sd, "tech", "runs_on", "Node 20", "person")
    project_facts.keep(sd, "tech", "runs_on", "Node 16", "read")
    project_facts.keep(sd, "tech", "runs_on", "Node 22", "person")
    got = project_facts.of(sd, "tech")
    assert len(got) == 1 and (got[0]["text"], got[0]["by"]) == ("Node 22", "person")
    project_facts.keep(sd, "tech", "second", "x", "read")
    assert [f["key"] for f in project_facts.of(sd, "tech")] == ["runs_on", "second"]                    # the order they were first kept


def test_a_fact_with_no_words_a_bad_key_a_bad_party_or_a_bad_giver_is_refused_and_nothing_is_written(sd):
    for args in (("tech", "k", "   ", "person"), ("tech", "Bad Key", "x", "person"), ("Tech Lead", "k", "x", "person"), ("tech", "k", "x", "model")):
        with pytest.raises(ValueError):
            project_facts.keep(sd, *args)
    assert not (sd / "facts.json").exists()


def test_a_file_that_is_not_of_the_shape_reads_as_empty(sd):
    sd.mkdir(parents=True)
    (sd / "facts.json").write_text(json.dumps({"common": "x", "party": {"tech": "no", "bad name": [{"key": "k", "text": "t"}],
                                                                       "design": [{"key": "ok", "text": "fine"}, {"key": "!", "text": "no"}, 5]}}))
    assert project_facts.common(sd) == "" and project_facts.of(sd, "tech") == []
    assert [(f["key"], f["by"]) for f in project_facts.of(sd, "design")] == [("ok", "read")]
    (sd / "facts.json").write_text("not json")
    assert project_facts.for_call(sd, "tech", route("tech")) == ""


def test_the_common_core_is_whom_it_is_for_what_hurts_and_what_it_leaves_out(sd):
    assert project_facts.common(sd) == ""
    project_facts.keep(sd, "product", "hurts", "Rounds drag on when one player is slow", "person")
    project_facts.keep(sd, "product", "for_whom", "Friends playing together at one TV", "read")
    assert project_facts.common(sd) == ("Whom it is for: Friends playing together at one TV\n"
                                        "What hurts them: Rounds drag on when one player is slow")
    project_facts.keep(sd, "product", "leaves_out", "Accounts and online matchmaking", "person")
    assert project_facts.common(sd).splitlines()[-1] == "What it leaves out: Accounts and online matchmaking"
    assert project_facts.answered(sd) == {"for_whom", "hurts", "leaves_out"}


def test_the_common_core_is_about_600_characters_at_most_each_share_cut_with_a_mark(sd):
    for key in project_facts.COMMON_KEYS:
        project_facts.keep(sd, "product", key, "word " * 200, "person")
    core = project_facts.common(sd)
    assert 0 < len(core) <= project_facts.COMMON_CHARS and core.count("…") == 3
    project_facts.keep(sd, "product", "for_whom", "Short", "person")
    assert project_facts.common(sd).splitlines()[0] == "Whom it is for: Short"


def test_a_reading_does_not_replace_the_persons_common_answer_but_the_person_replaces_a_reading(sd):
    project_facts.keep(sd, "product", "for_whom", "Read from the README", "read")
    project_facts.keep(sd, "product", "for_whom", "Families", "person")
    project_facts.keep(sd, "game-design", "for_whom", "Read again", "read")
    assert project_facts.common(sd) == "Whom it is for: Families"
    assert json.loads((sd / "facts.json").read_text())["common_by"]["for_whom"]["by"] == "person"


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


def test_a_call_is_the_same_bytes_for_the_same_facts_and_a_member_is_given_none(sd):
    project_facts.keep(sd, "product", "hurts", "Slow rounds", "person")
    project_facts.keep(sd, "tech", "runs_on", "Node 22", "person")
    one = project_facts.for_call(sd, "tech", route("tech", "product"))
    assert one == project_facts.for_call(sd, "tech", route("tech", "product")) and one
    assert project_facts.for_call(sd, "tech", route("tech"), member=True) == ""


def test_a_partys_facts_in_a_call_are_bounded_and_the_common_keys_are_not_repeated(sd):
    project_facts.keep(sd, "tech", "for_whom", "Everyone", "person")
    for n in range(30):
        project_facts.keep(sd, "tech", f"fact_{n:02d}", f"fact number {n} " + "x" * 280, "read")
    text = project_facts.for_call(sd, "tech", route("tech")).split("What is known for tech:\n", 1)[1]
    assert 0 < len(text) <= project_facts.PARTY_CHARS and "Everyone" not in text and text.startswith("- fact number 0 ")
    assert text.count("\n") + 1 <= project_facts.PARTY_FACTS


def test_an_empty_project_has_nothing_to_give(sd):
    assert project_facts.for_call(sd, "tech", route("tech", "design")) == "" and project_facts.answered(sd) == set()


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


def test_the_start_never_reads_the_decisions_file(tmp_path):
    (tmp_path / "README.md").write_text("A party game.", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "decisions.md").write_text("## 1. A decision", encoding="utf-8")
    (tmp_path / "docs" / "game.md").write_text("Rounds.", encoding="utf-8")
    assert [f["path"] for f in project_facts.start_files(tmp_path)] == ["README.md", "docs/game.md"]


# -- §8 what the project's questions keep (spec 99 G: gui/ideas_project_q.py) ----------------------------------------------------------

def test_the_projects_answers_are_in_every_leaders_call_whatever_party_asked_and_a_left_to_the_leader_pick_is_read(sd):
    project_facts.keep(sd, "product", "for_whom", "Friends at one TV", "person")
    project_facts.keep(sd, "product", "hurts", "Slow rounds", "read")                      # *Let … decide*: the leader's pick, kept `read`
    project_facts.keep(sd, "product", "leaves_out", "Accounts", "person")
    for party in ("tech", "design", "release"):                                            # the core reaches a party that is not on the asker's route
        text = project_facts.for_call(sd, party, route(party))
        assert text == "What the project is:\nWhom it is for: Friends at one TV\nWhat hurts them: Slow rounds\nWhat it leaves out: Accounts"
    assert [(f["key"], f["by"]) for f in project_facts.of(sd, "product")] == [("for_whom", "person"), ("hurts", "read"), ("leaves_out", "person")]
    assert project_facts.answered(sd) == set(project_facts.COMMON_KEYS)                    # a question answered is never asked again
    project_facts.keep(sd, "product", "hurts", "Another reading", "read")                  # a reading replaces a reading …
    assert project_facts.common(sd).splitlines()[1] == "What hurts them: Another reading"
    project_facts.keep(sd, "product", "hurts", "Players waiting", "person")
    project_facts.keep(sd, "product", "hurts", "A third reading", "read")                  # … never the person's answer
    assert project_facts.common(sd).splitlines()[1] == "What hurts them: Players waiting"


def test_the_orkmasters_one_answer_with_neither_party_is_the_common_core_and_is_asked_no_more(sd):
    project_facts.keep(sd, "orkmaster", "for_whom", "a mobile app for tennis clubs", "person")
    assert project_facts.for_call(sd, "tech", route("tech")) == "What the project is:\nWhom it is for: a mobile app for tennis clubs"
    assert "for_whom" in project_facts.answered(sd) and project_facts.of(sd, "orkmaster")[0]["by"] == "person"


def test_the_start_files_leave_the_decisions_file_out_in_any_case_of_its_name(tmp_path):
    (tmp_path / "README.markdown").write_text("Readme in markdown.", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "Decisions.MD").write_text("## 1. x", encoding="utf-8")
    assert project_facts.start_files(tmp_path) == [{"path": "README.markdown", "text": "Readme in markdown."}]
