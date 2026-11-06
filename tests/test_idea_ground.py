"""Spec 155 D (decisions §260.5, §260.6): in Talk a doubt that reading the code would settle is looked up (`ground`), and the person's questions that a decision or a spec settles
are closed by their reference (`settle`). The keeper's call is stubbed (tests/test_idea_talk.py `Model`)."""
from __future__ import annotations

from orkboard.core.idea_ground import clean_ground, clean_settle
from orkboard.realm import event_log, idea_questions, ideas
from orkboard.realm.idea_talk_parse import clean_verdict
from tests.test_idea_talk import _noes, _round_one, _talk, host, model, parties  # noqa: F401  (the fixtures and the helpers of Talk's tests)

DOUBT = {"verdict": "doubt", "why": "It may need a third caller", "check": "who calls server/ws"}
WHO = ["product", "design", "tech"]


def _record(host, slug):
    return idea_questions.record(host.ideas.state_dir, slug)


def _stance(host, slug, who):
    return next(s for s in _record(host, slug)["stances"] if s["party"] == who)


def _doubt(model, parties, **more):
    _noes(model, parties, tech={**DOUBT, **more})


def _project_files(host):
    root = host.ideas.keeper.repo_root
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "decisions.md").write_text("# Decisions\n\n## 258. A thing\n\nIt is so.\n", encoding="utf-8")
    (root / "docs" / "specs" / "154-a-spec.md").write_text("# 154. A spec\n", encoding="utf-8")


# -- clean_verdict keeps `check` ---------------------------------------------------------------------------------------------------

def test_a_check_is_kept_with_a_doubt_only_and_at_most_two_hundred_characters():
    assert clean_verdict({"verdict": "doubt", "why": "w", "check": " who calls it "})["check"] == "who calls it"
    assert len(clean_verdict({"verdict": "doubt", "why": "w", "check": "x " * 300})["check"]) <= 200
    assert clean_verdict({"verdict": "no", "why": "w", "check": "who calls it"})["check"] == ""
    assert clean_verdict({"verdict": "go", "check": "who calls it"})["check"] == ""
    assert clean_verdict({"verdict": "doubt", "why": "", "check": "who calls it"})["check"] == ""             # a doubt with no why reads as go


def test_the_ground_answer_is_strict():
    assert clean_ground({"settled": True, "found": " it is there "}) == {"settled": True, "found": "it is there"}
    assert clean_ground({"settled": "yes", "found": "x"}) is None and clean_ground({"settled": True}) is None and clean_ground("x") is None


def test_a_settled_card_is_kept_only_with_a_reference_that_exists_and_a_choice_of_its_own():
    cards = {1: {"choices": ["A", "B"]}, 2: {"choices": ["A", "B"]}, 3: {"choices": ["A", "B"]}}
    got = clean_settle({"settled": [{"n": 1, "pick": 1, "ref": "§258", "why": "w"}, {"n": 2, "pick": 2, "ref": "§258", "why": "w"}, {"n": 3, "pick": 0, "ref": "§999", "why": "w"},
                                    {"n": 9, "pick": 0, "ref": "§258", "why": "w"}, {"n": 1, "pick": 0, "ref": "§258", "why": "w"}]}, cards, lambda r: r == "§258")
    assert [(g["n"], g["pick"], g["ref"]) for g in got] == [(1, 1, "§258")]


# -- ground ------------------------------------------------------------------------------------------------------------------------

def test_a_doubt_with_a_check_that_the_code_settles_becomes_a_go_with_what_was_found(host, parties, model):
    _doubt(model, parties, instead="Only the setting")
    model.said[("ground", "")] = {"settled": True, "found": "server/ws has one caller"}
    slug = _talk(host, parties, WHO)
    s = _stance(host, slug, parties["tech"])
    assert (s["verdict"], s["why"], s["instead"]) == ("go", "checked: server/ws has one caller", "")
    (look,) = model.looked
    assert "who calls server/ws" in look["prompt"] and "It may need a third caller" in look["prompt"] and look["tools"] is True and "Read at most 4 files" in look["prompt"]
    assert not _record(host, slug).get("hearing")                                                              # a settled doubt opens no hearing


def test_a_doubt_the_code_does_not_settle_stands_with_what_was_found(host, parties, model):
    _doubt(model, parties)
    model.said[("ground", "")] = {"settled": False, "found": "two callers, one of them new"}
    slug = _talk(host, parties, WHO)
    s = _stance(host, slug, parties["tech"])
    assert s["verdict"] == "doubt" and s["why"] == "It may need a third caller — checked: two callers, one of them new"
    assert _record(host, slug).get("hearing") is True


def test_a_failed_or_unreadable_ground_call_leaves_the_doubt_as_it_was(host, parties, model):
    _doubt(model, parties)
    for n, answer in enumerate(("not json at all", {"settled": "maybe"})):
        model.said[("ground", "")] = answer
        slug = _talk(host, parties, WHO, f"add a dark mode option {n}")
        s = _stance(host, slug, parties["tech"])
        assert (s["verdict"], s["why"]) == ("doubt", "It may need a third caller")

    def boom(row):
        raise RuntimeError("the tool is gone")

    model.said[("ground", "")] = boom
    slug = _talk(host, parties, WHO, "add a light mode option")
    s = _stance(host, slug, parties["tech"])
    assert (s["verdict"], s["why"]) == ("doubt", "It may need a third caller")


def test_a_doubt_with_no_check_calls_nothing(host, parties, model):
    _noes(model, parties, tech={"verdict": "doubt", "why": "It may need a third caller"})
    slug = _talk(host, parties, WHO)
    assert model.looked == [] and _stance(host, slug, parties["tech"])["verdict"] == "doubt"


def test_each_check_is_logged(host, parties, model):
    seen = []
    host.ideas.keeper._ev = lambda event, **f: seen.append((event, f))
    _doubt(model, parties)
    model.said[("ground", "")] = {"settled": True, "found": "fine"}
    slug = _talk(host, parties, WHO)
    assert (event_log.TALK_GROUND, {"idea": slug, "party": parties["tech"], "settled": True}) in seen


# -- settle ------------------------------------------------------------------------------------------------------------------------

def test_a_question_a_decision_settles_is_closed_by_its_reference_and_the_rest_reach_the_hand(host, parties, model):
    _project_files(host)
    _round_one(model, parties, per=2)
    model.said[("settle", "")] = {"settled": [{"n": 1, "pick": 1, "ref": "§258", "why": "it says B"}, {"n": 2, "pick": 0, "ref": "spec 154 C.1", "why": "it says A"}]}
    slug = _talk(host, parties, WHO)
    rec = _record(host, slug)
    by = {d["q"]: d for d in rec["defaults"] if d["by"] in ("§258", "spec 154 C.1")}
    assert (by["product question 0"]["answer"], by["product question 0"]["by"]) == ("B", "§258")
    assert (by["product question 1"]["answer"], by["product question 1"]["by"]) == ("A", "spec 154 C.1")
    assert "product question 0" not in [c["q"] for c in rec["waiting"]] and len(rec["waiting"]) == 3        # the three that remain are asked
    (look,) = model.looked
    assert "product question 0" in look["prompt"] and "docs/decisions.md" in look["prompt"]
    text = "\n".join(t["text"] for t in ideas.talk(host.ideas.state_dir, slug))
    assert "Answered by §258: product question 0 — B" in text and "Answered by spec 154 C.1: product question 1 — A" in text


def test_a_reference_that_does_not_exist_or_a_pick_that_is_no_choice_keeps_the_question(host, parties, model):
    _project_files(host)
    _round_one(model, parties, per=1)
    model.said[("settle", "")] = {"settled": [{"n": 1, "pick": 0, "ref": "§999", "why": "w"}, {"n": 2, "pick": 7, "ref": "§258", "why": "w"}]}
    slug = _talk(host, parties, WHO)
    rec = _record(host, slug)
    assert len(rec["waiting"]) == 3 and rec["defaults"] == []


def test_a_failed_settle_call_changes_nothing(host, parties, model):
    _project_files(host)
    _round_one(model, parties, per=1)
    model.said[("settle", "")] = "no json here"
    slug = _talk(host, parties, WHO)
    rec = _record(host, slug)
    assert len(rec["waiting"]) == 3 and rec["defaults"] == []


def test_no_card_for_the_person_no_settle_call(host, parties, model):
    _round_one(model, parties, per=0)
    _talk(host, parties, WHO)
    assert model.looked == []
