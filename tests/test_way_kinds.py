"""A way's kind (spec 168 J1): each way has one after parsing, an unknown one reads `other`, an old record reads as before with `other`, the prompts ask for it."""
from pathlib import Path

from orkboard.core import idea_talk
from orkboard.realm import idea_hearing, idea_questions, idea_say, idea_talk_parse, lexicon, way_kinds

PICTURES = Path(__file__).resolve().parent.parent / "docs/mockups/table-template/pictures"


def test_kinds_match_the_owners_pictures_one_to_one():
    files = {p.stem for p in PICTURES.glob("*.png")}
    assert {way_kinds.PICTURE[k] for k in way_kinds.KINDS} == files
    assert len(set(way_kinds.PICTURE.values())) == len(way_kinds.KINDS)


def test_every_kind_has_its_words():
    for k in way_kinds.KINDS:
        assert lexicon.term(f"way_kind.{k}")


def test_clean_reads_unknown_and_missing_as_other():
    assert way_kinds.clean("Go on") == "go_on" and way_kinds.clean("accept-risk") == "accept_risk" and way_kinds.clean("replace") == "replace"
    for bad in ("sideways", "", None, 3, ["keep"]):
        assert way_kinds.clean(bad) == "other"
    assert way_kinds.of(["keep", "nope"], 3) == ["keep", "other", "other"]
    assert way_kinds.of(None, 2) == ["other", "other"]


def test_a_card_has_a_kind_for_each_way():
    raw = {"q": "Which store first?", "choices": ["App Store", "Google Play", "Both"], "pick": 0, "why": "iPhone", "kinds": ["keep", "bogus"]}
    c = idea_questions.card(raw, id="c1", by="tech", leader="tech-leader")
    assert c["kinds"] == ["keep", "other", "other"]
    assert idea_questions.card({k: v for k, v in raw.items() if k != "kinds"}, id="c1", by="tech", leader="l")["kinds"] == ["other"] * 3
    q = idea_questions.of({"ask": "Which?", "choices": ["a", "b"], "pick": 0, "kinds": ["later", "drop"]})
    assert q["kinds"] == ["later", "drop"]


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


def test_a_hearings_sides_are_kinds():
    assert [way_kinds.of_side(s) for s in ("go", "drop", "smaller", "later", "side", None)] == ["go_on", "drop", "smaller", "later", "other", "other"]
    side = idea_hearing._side("go", [{"party": "tech", "leader": "tech-leader"}], lambda x: x, "line", "out")
    assert side["way_kind"] == "go_on"


def test_the_prompts_ask_for_the_kind():
    assert "kinds" in idea_questions.LINES_RULE and "go_on" in idea_questions.LINES_RULE
    prompt = (Path(__file__).parent / "prompts_151/talk_tech.txt").read_text()
    assert '"kinds": ["…", "…"]' in prompt and '"way_kind": "…"' in prompt and "leader_decides" in prompt
