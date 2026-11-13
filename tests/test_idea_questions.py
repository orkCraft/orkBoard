"""realm/idea_questions.py (docs/specs/41-phone-round-3.md §9): a question's choices, the Taskmaster's pick and why."""
from __future__ import annotations

from orkboard.realm import idea_questions as iq


def test_a_question_from_the_model_is_taken_strictly():
    q = iq.of({"ask": " Which store  first? ", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first"})
    assert q == {"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first", "kinds": ["other", "other"]}
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": "Y"})["pick"] == 1               # a pick by its words
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": 2})["pick"] is None              # out of range
    assert iq.of({"ask": "A?", "choices": ["x", "y"], "pick": True})["pick"] is None
    for bad in (["only one"], ["a", "b", "c", "d", "e"], ["a/b", "c"], ["x" * 41, "y"], ["same", "Same"], "a / b"):
        assert iq.of({"ask": "A?", "choices": bad, "pick": 0, "why": "w"}) == {"ask": "A?", "choices": [], "pick": None, "why": ""}
    assert iq.of({"ask": "", "choices": ["x", "y"]}) is None and iq.of(3) is None and iq.of(None) is None
    assert len(iq.of({"ask": "A?", "choices": ["x", "y"], "why": "w " * 200})["why"]) <= iq.WHY_CHARS
    assert iq.of("Which week? (this / next)") == {"ask": "Which week?", "choices": ["this", "next"], "pick": None, "why": "", "kinds": ["other", "other"]}
    assert iq.all_of([{"ask": "A?"}, 5, "B?", "C?"], 2) == [{"ask": "A?", "choices": [], "pick": None, "why": ""},
                                                          {"ask": "B?", "choices": [], "pick": None, "why": ""}]
    assert iq.all_of("not a list", 3) == []




def test_a_card_is_a_question_of_two_to_four_real_choices_with_a_pick_and_its_why():
    """Spec 99 §5.2: `{id, by, leader, q, choices, pick, why, project}`, parsed strictly; a card with a choice that is none is no card (never padded)."""
    c = iq.card({"ask": " Where does it  run? ", "choices": ["A VPS", "server/lobby.ts", "A phone (iOS)"], "pick": "a vps", "why": "its README says so"},
                id="p-tech-runs_on", by="tech", leader="architect", project=True)
    assert c == {"id": "p-tech-runs_on", "by": "tech", "leader": "architect", "q": "Where does it run?", "choices": ["A VPS", "server/lobby.ts", "A phone (iOS)"],
                 "pick": 0, "why": "its README says so", "project": True, "kinds": ["other"] * 3}
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




def test_an_answers_line_is_written_under_its_question_and_read_back():
    """Spec 151 A.6: `  - Answered: <answer> (the person, YYYY-MM-DD)` under the question's line."""
    assert iq.answer_line("Google Play", "2026-11-06") == "  - Answered: Google Play (the person, 2026-11-06)"
    text = iq.with_answer("- Which store first? (**App Store** / Google Play)\n- Which week?", 0, "Google Play", "2026-11-06")
    assert text.splitlines()[1] == "  - Answered: Google Play (the person, 2026-11-06)"
    assert iq.answers(text) == ["Google Play", ""] and iq.answers(text.splitlines()) == ["Google Play", ""]
    assert iq.answers("") == [] and iq.open_of(text) == [(1, "Which week?")]


def test_a_ways_own_line_is_kept_after_the_why_and_read_back():
    """Spec 159 A: `lines`, one per way in the ways' order, at most 80 characters; kept only when every way has one."""
    raw = {"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone first",
           "lines": ["Ships in a week", "Ships in a month"]}
    q = iq.of(raw)
    assert q["lines"] == ["Ships in a week", "Ships in a month"]
    text = iq.line(q)
    assert text == "Which store first? (**App Store** / Google Play) — iPhone first · App Store: Ships in a week · Google Play: Ships in a month"
    assert iq.parse(text) == q and iq.of(text) == q                                     # the round trip
    assert iq.of({**raw, "lines": {"google play": "Ships in a month", "App Store": "Ships in a week"}})["lines"] == q["lines"]
    no_why = iq.of({**raw, "why": ""})
    assert iq.parse(iq.line(no_why)) == no_why and no_why["lines"] == q["lines"]








def test_a_card_and_its_talk_read_keep_the_lines_and_a_card_without_lines_is_as_before(tmp_path):
    """Spec 159 B: `lines` travel with the card into talk.json and the Talk read; the page line of a card is whole only with lines."""
    raw = {"q": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone", "lines": ["Ships in a week", "Ships in a month"]}
    c = iq.card(raw, id="c1", by="tech", leader="ork")
    assert c["lines"] == ["Ships in a week", "Ships in a month"]
    assert "lines" not in iq.card({**raw, "lines": ["only one"]}, id="c1", by="tech", leader="ork")
    plain = iq.card({k: v for k, v in raw.items() if k != "lines"}, id="c2", by="tech", leader="ork")
    assert "lines" not in plain and iq.card_line(plain) == "Which store first?"
    assert iq.parse(iq.card_line(c))["lines"] == c["lines"] and iq.card_line(c).startswith("Which store first? (**App Store** / Google Play) — iPhone · App Store: Ships")
    iq.save_record(tmp_path, "g", {"mode": "talk", "round": 1, "waiting": [c, plain], "stances": []})
    qs = iq.talk_of(tmp_path, "g")["stances"][0]["questions"]
    assert qs[0]["lines"] == c["lines"] and "lines" not in qs[1]


