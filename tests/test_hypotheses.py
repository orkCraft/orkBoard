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


# -- the bounds -----------------------------------------------------------------------------------------------------------------------

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


# -- evidence, judging ----------------------------------------------------------------------------------------------------------------

def test_held_and_refuted_end_it_with_the_decision_and_unsure_keeps_it_open_with_the_why_as_evidence(state):
    a, b, c = (hyp.add(state, w, "x") for w in ("Alpha", "Beta", "Gamma"))
    got = hyp.judge(state, a["id"], "held", "  it did \n hold", 12)
    assert got["state"] == "held" and got["verdict"] == {"state": "held", "why": "it did hold", "decision": 12, "way": "", "at": got["verdict"]["at"]} and got["verdict"]["at"]
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


# -- the file is not trusted ----------------------------------------------------------------------------------------------------------

# -- a leader's proposal, strictly ----------------------------------------------------------------------------------------------------

# -- spec 133 A: when it holds, each way it is refuted, the draft ---------------------------------------------------------------------

WAYS = [{"name": "the hook", "when": "opens rise, goals landed do not", "change": "The push is not built."}, {"name": "the noise", "when": "one in five turns it off"}]


def test_ways_and_the_draft_are_kept_and_edited_and_adding_asks_only_text_and_signal(state):
    short = hyp.add(state, "Short", "s")
    assert (short["refuted"], short["if_holds"]) == ([], "")
    full = hyp.add(state, "Full", "f", refuted=WAYS, if_holds="  The push\n becomes a setting. ")
    assert [w["name"] for w in full["refuted"]] == ["the hook", "the noise"] and full["refuted"][1]["change"] == "" and full["if_holds"] == "The push becomes a setting."
    assert kept(state)[1]["refuted"] == full["refuted"]
    got = hyp.edit(state, full["id"], refuted=[WAYS[1]], if_holds="")
    assert [w["name"] for w in got["refuted"]] == ["the noise"] and got["if_holds"] == "" and hyp.edit(state, full["id"], refuted=[])["refuted"] == []


def test_a_verdict_names_the_way_it_was_refuted_and_a_way_that_does_not_fit_is_refused(state):
    a = hyp.add(state, "Alpha", "a", refuted=WAYS)
    with pytest.raises(ValueError, match="Pick the way it is refuted: the hook, the noise"):
        hyp.judge(state, a["id"], "refuted", "why", 3, way="the cold")
    with pytest.raises(ValueError, match="Pick the way"):
        hyp.judge(state, a["id"], "refuted")
    with pytest.raises(ValueError, match="Only a refuted"):
        hyp.judge(state, a["id"], "held", way="the hook")
    assert kept(state)[0]["state"] == "open"
    got = hyp.judge(state, a["id"], "refuted", "why", 3, way="THE HOOK")
    assert got["verdict"]["way"] == "the hook" and hyp.read(state)["items"][0]["verdict"]["way"] == "the hook"
    one = hyp.add(state, "One way", "b", refuted=[WAYS[0]])
    assert hyp.judge(state, one["id"], "refuted")["verdict"]["way"] == "the hook"          # the only way is taken when none is named
    none = hyp.add(state, "No ways", "c")
    assert hyp.judge(state, none["id"], "refuted")["verdict"]["way"] == ""


def test_a_proposal_is_taken_with_its_ways_and_its_draft_and_a_bad_way_is_dropped(state):
    got = hyp.parse({"hypotheses": [{"text": "A", "signal": "s", "refuted": [{"name": "the hook", "when": "w", "change": "ignored"}, {"name": "x"}, "no", {"name": "the hook", "when": "again"}], "if_holds": " Do it. "},
                                    {"text": "B", "signal": "s", "refuted": "nope"}]})
    assert got[0]["refuted"] == [{"name": "the hook", "when": "w", "change": ""}] and got[0]["if_holds"] == "Do it." and got[1]["refuted"] == [] and got[1]["if_holds"] == ""
    kept_ = hyp.add(state, got[0]["text"], got[0]["signal"], by="leader", party="product", refuted=got[0]["refuted"], if_holds=got[0]["if_holds"])
    assert kept_["state"] == "proposed" and kept_["refuted"][0]["name"] == "the hook"
