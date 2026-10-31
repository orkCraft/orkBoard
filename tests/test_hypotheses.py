"""Spec 116 A (docs/specs/116-hypotheses-on-products-tree.md §2; decisions §194): the hypotheses of Product's map as code keeps them, `realm/hypotheses.py`: what the project believes and has not shown,
its signal, what it rests on and the goals that test it, in `<state_dir>/hypotheses.json`; the bounds (seven open, twelve proposed, forty in all), the ids that stay, a test goal that moves, the state
as shown, what is due, the text for a leader's call in the same bytes, a leader's proposal taken strictly. No git, no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp


@pytest.fixture
def state(tmp_path: Path) -> Path:
    (tmp_path / "state").mkdir()
    return tmp_path / "state"


def many(state: Path, n: int, by: str = "person", prefix: str = "Claim") -> list[dict]:
    return [hyp.add(state, f"{prefix} {k} holds", f"people do {k}", by=by, party="product" if by == "leader" else "") for k in range(n)]


def kept(state: Path) -> list[dict]:
    return hyp.read(state)["items"]


# -- the record kept ------------------------------------------------------------------------------------------------------------------

def test_nothing_is_kept_before_a_hypothesis_and_one_is_kept_with_its_parts_in_one_file(state):
    assert hyp.read(state) == {"items": []} and hyp.text(state, {}) == "" and hyp.due(state, {}) == []
    item = hyp.add(state, "  People   want a sketch first ", "most ask for one within a minute", axis="desirable", on="see-a-sketch", rests=["dark-mode", "dark-mode", "faster-pages"])
    assert item["id"] == "people-want-a-sketch-first" and item["text"] == "People want a sketch first" and item["state"] == "open" and item["by"] == "person" and item["party"] == ""
    assert (item["axis"], item["on"], item["rests"], item["tests"], item["evidence"], item["verdict"]) == ("desirable", "see-a-sketch", ["dark-mode", "faster-pages"], [], [], {}) and item["at"]
    assert hyp.read(state) == {"items": [item]}
    assert list(json.loads((state / "hypotheses.json").read_text())) == ["items"]
    led = hyp.add(state, "Founders pay for it", "ten say so", by="leader", party="product")
    assert led["state"] == "proposed" and led["by"] == "leader" and led["party"] == "product" and led["axis"] == "" and led["on"] == ""
    assert [i["id"] for i in kept(state)] == ["people-want-a-sketch-first", "founders-pay-for-it"]


def test_the_parts_are_bounded_and_the_ids_are_unique(state):
    long = "word " * 100
    item = hyp.add(state, long, long)
    assert len(item["text"]) <= hyp.TEXT_CHARS and len(item["signal"]) <= hyp.TEXT_CHARS and len(item["id"]) <= 40
    same = [hyp.add(state, "Same words", "x") for _ in range(3)]
    assert [i["id"] for i in same] == ["same-words", "same-words-2", "same-words-3"]
    assert hyp.add(state, "!!!", "x")["id"] == "hypothesis"
    for _ in range(hyp.EVIDENCE + 5):
        hyp.evidence(state, "same-words", "a line " + "x" * 300)
    assert all(len(e["text"]) <= hyp.TEXT_CHARS for e in kept(state)[1]["evidence"])


def test_the_id_stays_when_the_words_change_and_edit_changes_only_what_it_is_given(state):
    first = hyp.add(state, "People want a sketch", "most ask", axis="desirable", on="job-a", rests=["g1"])
    got = hyp.edit(state, first["id"], text="People want a sketch in a minute", signal="most ask within a minute")
    assert got["id"] == "people-want-a-sketch" and got["text"] == "People want a sketch in a minute" and (got["axis"], got["on"], got["rests"]) == ("desirable", "job-a", ["g1"])
    got = hyp.edit(state, first["id"], axis="", on="", rests=["g2", "g3"])
    assert (got["axis"], got["on"], got["rests"]) == ("", "", ["g2", "g3"]) and got["text"] == "People want a sketch in a minute"
    assert kept(state)[0] == got
    for fields, why in (({"text": " "}, "what we believe"), ({"signal": ""}, "we'll know when"), ({"axis": "tasty"}, "desirable"), ({"on": "No Job"}, "job or an outcome"),
                        ({"rests": ["Bad Slug"]}, "rests on"), ({"rests": ["g%d" % n for n in range(13)]}, "rests on"), ({"state": "held"}, "state is not changed"), ({"tests": ["g1"]}, "tests is not changed")):
        with pytest.raises(ValueError, match=why):
            hyp.edit(state, first["id"], **fields)
    with pytest.raises(ValueError, match="gone"):
        hyp.edit(state, "no-such", text="x")
    assert kept(state)[0] == got


def test_a_hypothesis_without_words_or_with_a_part_that_is_none_is_refused_and_nothing_changes(state):
    for args, kw, why in ((("", "s"), {}, "what we believe"), (("t", " "), {}, "we'll know when"), (("t", "s"), {"axis": "tasty"}, "desirable"), (("t", "s"), {"on": "A B"}, "job or an outcome"),
                          (("t", "s"), {"rests": ["A B"]}, "rests on"), (("t", "s"), {"rests": "g1"}, "rests on"), (("t", "s"), {"by": "model"}, "person or a leader")):
        with pytest.raises(ValueError, match=why):
            hyp.add(state, *args, **kw)
    assert not (state / "hypotheses.json").exists()


# -- the bounds -----------------------------------------------------------------------------------------------------------------------

def test_seven_open_at_most_and_a_person_who_adds_past_them_is_told_so(state):
    many(state, hyp.MAX_OPEN)
    with pytest.raises(ValueError, match="7 hypotheses are open or being tested"):
        hyp.add(state, "One too many", "x")
    assert len(kept(state)) == 7
    hyp.drop(state, "claim-0-holds")
    assert hyp.add(state, "One more", "x")["state"] == "open"


def test_a_proposal_is_refused_past_seven_open_and_past_twelve_proposed_and_keeping_is_bounded_too(state):
    many(state, hyp.MAX_PROPOSED, by="leader", prefix="Proposed")
    with pytest.raises(ValueError, match="12 hypotheses are waiting"):
        hyp.add(state, "Another", "x", by="leader", party="product")
    assert hyp.add(state, "A person's own", "x")["state"] == "open"                                   # twelve proposed do not stop a person
    for k in range(hyp.MAX_OPEN - 1):
        hyp.keep(state, kept(state)[k]["id"])
    with pytest.raises(ValueError, match="open or being tested already"):
        hyp.add(state, "Another", "x", by="leader", party="product")
    with pytest.raises(ValueError, match="7 hypotheses are open"):
        hyp.keep(state, "proposed-7-holds")
    assert hyp.keep(state, "proposed-0-holds")["state"] == "open"                                     # one already kept stays as it is
    hyp.drop(state, "proposed-0-holds")
    assert hyp.keep(state, "proposed-7-holds")["state"] == "open"


def test_forty_in_all_and_the_oldest_judged_goes_first(state):
    for k in range(hyp.MAX_ALL):
        item = hyp.add(state, f"Old {k}", "x")
        hyp.judge(state, item["id"], "held" if k % 2 else "refuted", "because")
    assert len(kept(state)) == hyp.MAX_ALL
    hyp.add(state, "New one", "x")
    ids = [i["id"] for i in kept(state)]
    assert len(ids) == hyp.MAX_ALL and "old-0" not in ids and "old-1" in ids and ids[-1] == "new-one"
    hyp.add(state, "Newer one", "x")
    assert "old-1" not in [i["id"] for i in kept(state)] and len(kept(state)) == hyp.MAX_ALL


def test_forty_none_judged_refuses_instead_of_losing_one(state):
    (state / "hypotheses.json").write_text(json.dumps({"items": [{"id": f"p-{n}", "text": f"P {n}", "signal": "s", "state": "proposed", "by": "leader"} for n in range(hyp.MAX_ALL)]}))
    assert len(kept(state)) == hyp.MAX_ALL
    with pytest.raises(ValueError, match="12 hypotheses are waiting"):
        hyp.add(state, "Past forty", "x", by="leader", party="product")                              # twelve proposed are past already
    with pytest.raises(ValueError, match="40 hypotheses are kept"):
        hyp.add(state, "Past forty", "x")
    (state / "hypotheses.json").write_text(json.dumps({"items": [{"id": f"p-{n}", "text": f"P {n}", "signal": "s", "state": "proposed" if n < 11 else "refuted", "by": "leader"} for n in range(hyp.MAX_ALL)]}))
    assert hyp.add(state, "Past forty", "x")["state"] == "open" and len(kept(state)) == hyp.MAX_ALL   # a judged one went


# -- keep, drop -----------------------------------------------------------------------------------------------------------------------

def test_keep_opens_a_proposed_one_and_drop_removes_it_whatever_its_state(state):
    prop = hyp.add(state, "Leader thinks so", "x", by="leader", party="product")
    assert hyp.keep(state, prop["id"])["state"] == "open"
    hyp.judge(state, prop["id"], "held")
    assert hyp.keep(state, prop["id"])["state"] == "held"
    hyp.drop(state, prop["id"])
    assert kept(state) == []
    for call in (hyp.keep, hyp.drop):
        with pytest.raises(ValueError, match="That hypothesis is gone"):
            call(state, prop["id"])


# -- the goals that rest on it and test it --------------------------------------------------------------------------------------------

def test_a_goal_may_rest_on_several_and_a_goal_tests_one_hypothesis_at_most_it_moves(state):
    a, b = hyp.add(state, "Alpha", "x"), hyp.add(state, "Beta", "y")
    assert hyp.attach(state, a["id"], goal="dark-mode")["rests"] == ["dark-mode"]
    assert hyp.attach(state, b["id"], goal="dark-mode")["rests"] == ["dark-mode"] and kept(state)[0]["rests"] == ["dark-mode"]      # resting is not a move
    assert hyp.attach(state, a["id"], test="try-dark")["tests"] == ["try-dark"]
    assert hyp.attach(state, a["id"], goal="dark-mode", test="try-dark")["rests"] == ["dark-mode"]                                  # again: once
    assert hyp.attach(state, b["id"], test="try-dark")["tests"] == ["try-dark"]
    assert [i["tests"] for i in kept(state)] == [[], ["try-dark"]]                                                                   # it moved
    hyp.attach(state, b["id"], test="try-more")
    assert hyp.attach(state, "", test="try-dark") is None and [i["tests"] for i in kept(state)] == [[], ["try-more"]]
    assert hyp.attach(state, "", goal="dark-mode") is None and [i["rests"] for i in kept(state)] == [[], []]


def test_attaching_refuses_what_is_none_and_past_twelve(state):
    a = hyp.add(state, "Alpha", "x")
    for kw, why in (({}, "Say which goal"), ({"goal": "Bad Slug"}, "goal's name"), ({"test": "Bad Slug"}, "goal's name")):
        with pytest.raises(ValueError, match=why):
            hyp.attach(state, a["id"], **kw)
    with pytest.raises(ValueError, match="gone"):
        hyp.attach(state, "no-such", goal="g")
    for n in range(hyp.GOALS):
        hyp.attach(state, a["id"], goal=f"g{n}", test=f"t{n}")
    for kw, why in (({"goal": "one-more"}, "rests on 12 goals"), ({"test": "one-more"}, "tested by 12 goals")):
        with pytest.raises(ValueError, match=why):
            hyp.attach(state, a["id"], **kw)
    assert len(kept(state)[0]["rests"]) == 12 and len(kept(state)[0]["tests"]) == 12


# -- evidence, judging ----------------------------------------------------------------------------------------------------------------

def test_evidence_is_a_line_with_where_from_twelve_at_most_the_newest_kept(state):
    a = hyp.add(state, "Alpha", "x")
    got = hyp.evidence(state, a["id"], "  three  of five\nasked ", "try-dark")
    assert got["evidence"][0]["text"] == "three of five asked" and got["evidence"][0]["ref"] == "try-dark" and got["evidence"][0]["at"]
    for n in range(15):
        hyp.evidence(state, a["id"], f"line {n}")
    lines = [e["text"] for e in kept(state)[0]["evidence"]]
    assert len(lines) == hyp.EVIDENCE and lines[-1] == "line 14" and lines[0] == "line 3" and "three of five asked" not in lines
    for args, why in ((("no-such", "x"), "gone"), ((a["id"], " "), "line on what was found")):
        with pytest.raises(ValueError, match=why):
            hyp.evidence(state, *args)


def test_held_and_refuted_end_it_with_the_decision_and_unsure_keeps_it_open_with_the_why_as_evidence(state):
    a, b, c = (hyp.add(state, w, "x") for w in ("Alpha", "Beta", "Gamma"))
    got = hyp.judge(state, a["id"], "held", "  it did \n hold", 12)
    assert got["state"] == "held" and got["verdict"] == {"state": "held", "why": "it did hold", "decision": 12, "at": got["verdict"]["at"]} and got["verdict"]["at"]
    got = hyp.judge(state, b["id"], "refuted")
    assert got["state"] == "refuted" and got["verdict"]["decision"] == 0 and got["verdict"]["why"] == ""
    got = hyp.judge(state, c["id"], "unsure", "need more people")
    assert got["state"] == "open" and got["verdict"] == {} and [e["text"] for e in got["evidence"]] == ["need more people"]
    assert hyp.judge(state, c["id"], "unsure")["evidence"] == got["evidence"]                        # no why, nothing added
    assert [i["state"] for i in kept(state)] == ["held", "refuted", "open"] and kept(state)[0]["verdict"]["decision"] == 12
    with pytest.raises(ValueError, match="judged already"):
        hyp.judge(state, a["id"], "refuted")
    with pytest.raises(ValueError, match="judged already"):
        hyp.judge(state, a["id"], "unsure")
    with pytest.raises(ValueError, match="held, was refuted"):
        hyp.judge(state, c["id"], "maybe")
    with pytest.raises(ValueError, match="gone"):
        hyp.judge(state, "no-such", "held")
    prop = hyp.add(state, "Proposed", "x", by="leader", party="product")
    with pytest.raises(ValueError, match="Keep the hypothesis"):
        hyp.judge(state, prop["id"], "held")
    assert hyp.judge(state, c["id"], "held", "x", True)["verdict"]["decision"] == 0                  # a number is a number, not a flag


# -- as shown, what is due ------------------------------------------------------------------------------------------------------------

def test_state_of_is_testing_while_an_open_ones_test_is_in_line_or_at_work(state):
    item = hyp.add(state, "Alpha", "x")
    assert hyp.state_of(item, {}) == "open"
    hyp.attach(state, item["id"], test="t1")
    hyp.attach(state, item["id"], test="t2")
    item = kept(state)[0]
    for places, shown in (({"t1": "line"}, "testing"), ({"t1": "work", "t2": "done"}, "testing"), ({"t1": "done", "t2": "done"}, "open"), ({}, "open"), ({"other": "work"}, "open")):
        assert hyp.state_of(item, places) == shown
    assert hyp.state_of({**item, "state": "held"}, {"t1": "work"}) == "held" and hyp.state_of({**item, "state": "proposed"}, {"t1": "work"}) == "proposed"
    assert kept(state)[0]["state"] == "open"                                                         # "testing" is never kept


def test_due_are_the_open_ones_with_a_test_every_test_done_and_not_judged(state):
    none, running, finished, mixed, judged, proposed, gone = (hyp.add(state, w, "x") for w in ("None", "Running", "Finished", "Mixed", "Judged", "Proposed", "Gone"))
    hyp.attach(state, running["id"], test="t-run")
    hyp.attach(state, finished["id"], test="t-done")
    hyp.attach(state, mixed["id"], test="t-done-2")
    hyp.attach(state, mixed["id"], test="t-line")
    hyp.attach(state, judged["id"], test="t-done-3")
    hyp.attach(state, gone["id"], test="t-gone")
    places = {"t-run": "work", "t-done": "done", "t-done-2": "done", "t-line": "line", "t-done-3": "done"}
    assert [i["id"] for i in hyp.due(state, places)] == ["finished", "judged"]
    hyp.judge(state, judged["id"], "held")
    assert [i["id"] for i in hyp.due(state, places)] == ["finished"]
    hyp.judge(state, finished["id"], "unsure", "not enough")
    assert [i["id"] for i in hyp.due(state, places)] == ["finished"]                                  # unsure: asked again when more is done
    (state / "hypotheses.json").write_text(json.dumps({"items": [{**i, "state": "proposed", "tests": ["t-done"]} for i in kept(state)[:1]]}))
    assert hyp.due(state, places) == [] and none["id"] and proposed["id"]


# -- its text -------------------------------------------------------------------------------------------------------------------------

def test_the_text_is_the_open_and_testing_ones_a_line_each_in_the_same_bytes(state):
    a = hyp.add(state, "People want a sketch", "most ask within a minute")
    b = hyp.add(state, "Founders pay", "ten say so")
    c = hyp.add(state, "Held already", "x")
    hyp.add(state, "Only proposed", "x", by="leader", party="product")
    hyp.judge(state, c["id"], "held")
    hyp.attach(state, b["id"], test="t1")
    places = {"t1": "work"}
    want = "Hypothesis (open): People want a sketch — we'll know when most ask within a minute\nHypothesis (testing): Founders pay — we'll know when ten say so"
    assert hyp.text(state, places) == want == hyp.text(state, places)
    assert hyp.text(state, {}).splitlines()[1] == "Hypothesis (open): Founders pay — we'll know when ten say so"
    assert hyp.text(state, {}).encode() == hyp.text(state, {}).encode() and a["id"]
    only = state.parent / "only-judged"
    only.mkdir()
    hyp.add(only, "Done", "x")
    hyp.judge(only, "done", "refuted")
    assert hyp.text(only, {}) == ""


def test_the_text_is_bounded_its_words_cut_before_a_line_goes(state):
    words = "word " * 40
    for n in range(hyp.MAX_OPEN):
        hyp.add(state, f"Claim number {n} {words}", f"signal {words}")
    got = hyp.text(state, {})
    assert 0 < len(got) <= hyp.LIMIT and got == hyp.text(state, {})
    assert len(got.splitlines()) == hyp.MAX_OPEN and got.splitlines()[0].startswith("Hypothesis (open): Claim number 0")             # every line named, the words cut
    assert len(hyp.text(state, {})) <= hyp.LIMIT
    one = state.parent / "one"
    one.mkdir()
    hyp.add(one, "Short", "clear")
    assert hyp.text(one, {}) == "Hypothesis (open): Short — we'll know when clear"                                                       # nothing cut that fits


# -- the file is not trusted ----------------------------------------------------------------------------------------------------------

def test_a_file_that_is_not_of_the_shape_reads_as_absent(state):
    ok = {"id": "fine", "text": "Fine", "signal": "s", "state": "open"}
    (state / "hypotheses.json").write_text(json.dumps({"items": [
        {**ok, "axis": "tasty", "on": "A B", "rests": ["a", "a", "Bad Slug", 3], "tests": "no", "by": "robot", "party": "Bad Party", "evidence": [{"text": "e"}, {"text": ""}, "no", {"text": "x", "ref": 3}],
         "verdict": {"state": "maybe"}, "at": 5},
        {**ok}, {**ok, "id": "Bad Id"}, {**ok, "id": "no-text", "text": ""}, {**ok, "id": "no-signal", "signal": " "}, {**ok, "id": "bad-state", "state": "testing"}, {**ok, "id": 3}, "no",
        {**ok, "id": "judged", "state": "held", "verdict": {"state": "held", "why": "w", "decision": "7", "at": "t"}}]}))
    got = kept(state)
    assert [i["id"] for i in got] == ["fine", "judged"]
    assert (got[0]["axis"], got[0]["on"], got[0]["rests"], got[0]["tests"], got[0]["by"], got[0]["party"], got[0]["verdict"], got[0]["at"]) == ("", "", ["a"], [], "person", "", {}, "5")
    assert [(e["text"], e["ref"]) for e in got[0]["evidence"]] == [("e", ""), ("x", "")]
    assert got[1]["verdict"] == {"state": "held", "why": "w", "decision": 0, "at": "t"}
    (state / "hypotheses.json").write_text("[1]")
    assert kept(state) == []
    (state / "hypotheses.json").write_text(json.dumps({"items": "no"}))
    assert kept(state) == []
    over = [{**ok, "id": f"i-{n}", "state": "proposed", "evidence": [{"text": f"e{k}"} for k in range(30)], "rests": [f"g{k}" for k in range(30)]} for n in range(50)]
    (state / "hypotheses.json").write_text(json.dumps({"items": over}))
    got = kept(state)
    assert len(got) == hyp.MAX_ALL and len(got[0]["evidence"]) == hyp.EVIDENCE and got[0]["evidence"][-1]["text"] == "e29" and len(got[0]["rests"]) == hyp.GOALS


def test_writes_from_two_threads_lose_nothing(state):
    import threading
    threads = [threading.Thread(target=lambda n=n: hyp.add(state, f"Claim {n}", "x", by="leader", party="product")) for n in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(kept(state)) == 10 and len({i["id"] for i in kept(state)}) == 10


# -- a leader's proposal, strictly ----------------------------------------------------------------------------------------------------

def test_the_leaders_proposal_is_taken_strictly(state):
    good = {"hypotheses": [{"text": "  People want a sketch ", "signal": "most ask", "axis": "desirable", "on": "see-a-sketch", "rests": ["dark-mode"]}, {"text": "Founders pay", "signal": "ten say so"}]}
    got = hyp.parse(good)
    assert got == [{"text": "People want a sketch", "signal": "most ask", "axis": "desirable", "on": "see-a-sketch", "rests": ["dark-mode"]},
                   {"text": "Founders pay", "signal": "ten say so", "axis": "", "on": "", "rests": []}]
    added = [hyp.add(state, h["text"], h["signal"], axis=h["axis"], on=h["on"], rests=h["rests"], by="leader", party="product") for h in got]
    assert [a["state"] for a in added] == ["proposed", "proposed"]
    four = {"hypotheses": [{"text": f"Claim {n}", "signal": "s"} for n in range(5)]}
    assert [h["text"] for h in hyp.parse(four)] == ["Claim 0", "Claim 1", "Claim 2"]                  # three at most, the riskiest first
    for bad in (None, "no", [], {}, {"hypotheses": "no"}, {"hypotheses": []}, {"hypotheses": ["no", 3, None]}, {"hypotheses": [{"text": "x"}]}, {"hypotheses": [{"text": "", "signal": "s"}]},
                {"hypotheses": [{"text": "x", "signal": 3}]}, {"hypotheses": [{"text": ["x"], "signal": "s"}]}):
        assert hyp.parse(bad) is None
    shapes = {"hypotheses": [{"text": "bad axis", "signal": "s", "axis": "tasty"}, {"text": "bad on", "signal": "s", "on": "A B"}, {"text": "bad rests", "signal": "s", "rests": "g"},
                             {"text": "bad rest", "signal": "s", "rests": ["A B"]}, {"text": "too many", "signal": "s", "rests": [f"g{n}" for n in range(13)]}, "no", {"signal": "s"},
                             {"text": "Fine", "signal": "s", "axis": "viable"}, {"text": "fine", "signal": "again"}, {"text": "Second", "signal": "s", "axis": ""}]}
    assert [h["text"] for h in hyp.parse(shapes)] == ["Fine", "Second"]                               # what is not of the shape dropped, the same text once
