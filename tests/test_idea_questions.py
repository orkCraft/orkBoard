"""realm/idea_questions.py (docs/specs/41-phone-round-3.md §9): a question's choices, the Taskmaster's pick and why."""
from __future__ import annotations

from orkboard.realm import idea_questions as iq


def test_a_question_from_the_model_is_taken_strictly():
    q = iq.of({"ask": " Which store  first? ", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first"})
    assert q == {"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first"}
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": "Y"})["pick"] == 1               # a pick by its words
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": 2})["pick"] is None              # out of range
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": True})["pick"] is None
    for bad in (["only one"], ["a", "b", "c", "d", "e"], ["a/b", "c"], ["x" * 41, "y"], ["same", "Same"], "a / b"):
        assert iq.of({"ask": "A?", "choices": bad, "pick": 0, "why": "w"}) == {"ask": "A?", "choices": [], "pick": None, "why": ""}
    assert iq.of({"ask": "", "choices": ["x", "y"]}) is None and iq.of(3) is None and iq.of(None) is None
    assert len(iq.of({"ask": "A?", "choices": ["x", "y"], "why": "w " * 200})["why"]) <= iq.WHY_CHARS
    assert iq.of("Which week? (this / next)") == {"ask": "Which week?", "choices": ["this", "next"], "pick": None, "why": ""}
    assert iq.all_of([{"ask": "A?"}, 5, "B?", "C?"], 2) == [{"ask": "A?", "choices": [], "pick": None, "why": ""},
                                                          {"ask": "B?", "choices": [], "pick": None, "why": ""}]
    assert iq.all_of("not a list", 3) == []


def test_the_pages_line_says_the_pick_in_bold_and_reads_back():
    q = {"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first"}
    line = iq.line(q)
    assert line == "Which store first? (**App Store** / Google Play) — iPhone first"
    assert iq.parse(line) == q
    assert iq.line({"ask": "Why?", "choices": [], "pick": None, "why": ""}) == "Why?"
    assert iq.parse("Which store first (App Store / Google Play)?") == {
        "ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": None, "why": ""}   # a line of before
    assert iq.parse("Pick one (a / b / c / d / e)")["choices"] == []
    assert iq.parse("Both bold (**a** / **b**)")["pick"] is None
    assert iq.parse("") == {"ask": "", "choices": [], "pick": None, "why": ""}


def test_a_card_is_a_question_of_two_to_four_real_choices_with_a_pick_and_its_why():
    """Spec 99 §5.2: `{id, by, leader, q, choices, pick, why, project}`, parsed strictly; a card with a choice that is none is no card (never padded)."""
    c = iq.card({"ask": " Where does it  run? ", "choices": ["A VPS", "server/lobby.ts", "A phone (iOS)"], "pick": "a vps", "why": "its README says so"},
                id="p-tech-runs_on", by="tech", leader="architect", project=True)
    assert c == {"id": "p-tech-runs_on", "by": "tech", "leader": "architect", "q": "Where does it run?", "choices": ["A VPS", "server/lobby.ts", "A phone (iOS)"],
                 "pick": 0, "why": "its README says so", "project": True}
    assert iq.card({"q": "Which?", "choices": ["a", "b"], "pick": 1}, id="x", by="t", leader="l")["q"] == "Which?"           # `q` or `ask`
    assert iq.CHOICES == (2, 4) and iq.card({"ask": "A?", "choices": ["x" * 61, "y"], "pick": 0}, id="x", by="t", leader="l") is None
    assert iq.card({"ask": "A?", "choices": ["x", "y"], "pick": 0, "why": "w " * 200}, id="x", by="t", leader="l")["why"].endswith("…")
    assert len(iq.card({"ask": "A?", "choices": ["x", "y"], "pick": 0, "why": "w " * 200}, id="x", by="t", leader="l")["why"]) <= iq.WHY_CHARS
    assert iq.card({"ask": "A?", "choices": ["x", "y"], "pick": 0}, id="x", by="t", leader="l")["why"] == ""


def test_a_card_takes_its_leaders_pick_when_nobody_answers_and_a_persons_answer_is_a_pick_or_words():
    c = iq.card({"ask": "A?", "choices": ["x", "y", "z"], "pick": 2}, id="x", by="t", leader="l")
    assert iq.default_of(c) == "z"
    assert iq.answer_of(c, {"id": "x", "pick": 1}) == ("y", "pick") and iq.answer_of(c, {"id": "x", "text": "  my  words "}) == ("my words", "text")
    assert iq.answer_of(c, {"id": "x", "pick": 0, "text": "words win"}) == ("words win", "text")            # *Other…* opens with the pick in it: what is written wins
    for none in ({"id": "x"}, {"id": "x", "pick": 3}, {"id": "x", "pick": -1}, {"id": "x", "pick": True}, {"id": "x", "text": "   "}, "y", None):
        assert iq.answer_of(c, none) is None


def test_a_talks_record_is_kept_beside_the_goals_state(tmp_path):
    assert iq.record(tmp_path, "a-goal") == {}
    iq.save_record(tmp_path, "a-goal", {"mode": "talk", "waiting": [{"id": "x"}]})
    assert iq.record(tmp_path, "a-goal") == {"mode": "talk", "waiting": [{"id": "x"}]} and iq.record(tmp_path, "other") == {}
    assert (tmp_path / "ideas" / "a-goal" / iq.TALK_FILE).is_file()
