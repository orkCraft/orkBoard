"""A way's kind (spec 168 J1): each way has one after parsing, an unknown one reads `other`, an old record reads as before with `other`, the prompts ask for it."""
from pathlib import Path

from orkboard.realm import idea_questions, idea_say, idea_talk_parse, way_kinds

PICTURES = Path(__file__).resolve().parent.parent / "docs/mockups/table-template/pictures"


def test_an_old_record_reads_as_before_with_other():
    old = {"id": "c1", "q": "Which?", "choices": ["a", "b"], "pick": 0, "why": ""}
    assert way_kinds.of_card(old) == ["other", "other"]
    assert way_kinds.with_kinds(old) == {**old, "kinds": ["other", "other"]}
    assert "kinds" not in way_kinds.with_kinds({"ask": "No choices"})
    assert idea_questions._asked(old, "waiting")["kinds"] == ["other", "other"]


def test_needs_ways_keep_their_kind():
    got = idea_talk_parse.clean_needs([{"kind": "question", "line": "Which?", "ways": [{"name": "A", "line": "x", "way_kind": "split"}, {"name": "B", "line": "y", "way_kind": "??"}, {"name": "C"}]}], "tech")
    assert [w["way_kind"] for w in got[0]["ways"]] == ["split", "other", "other"]


def test_a_legacy_need_and_an_old_need_have_kinds_in_the_rows(tmp_path):
    talk = {"waiting": [{"id": "c1", "by": "tech", "q": "Which?", "choices": ["a", "b"], "pick": 0, "kinds": ["replace", "keep"]}, {"id": "c2", "by": "tech", "q": "Old?", "choices": ["x", "y"], "pick": 1}],
            "answers": [{"id": "c3", "by": "tech", "q": "Done?", "answer": "mine"}]}
    got = {n["id"]: n for n in idea_say._legacy(talk, "tech")}
    assert [w["way_kind"] for w in got["c1"]["ways"]] == ["replace", "keep"]
    assert [w["way_kind"] for w in got["c2"]["ways"]] == ["other", "other"]
    assert [w["way_kind"] for w in got["c3"]["ways"]] == ["other"]
    row = idea_say._row({"id": "n1", "ways": [{"name": "A", "line": ""}, {"name": "B", "line": "", "way_kind": "drop"}]}, {"answers": {}})
    assert [w["way_kind"] for w in row["ways"]] == ["other", "drop"]

