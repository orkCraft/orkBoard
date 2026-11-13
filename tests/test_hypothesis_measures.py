"""Spec 133 B (docs/specs/133-a-hypothesis-its-two-conditions-its-test-its-file.md; decisions §235.2, §235.3): a hypothesis's measures, `realm/hypothesis_measures.py`, and what they do in
`realm/hypotheses.py`: the date, the due at the later of the goals and the date, the values kept, the conditions code says they meet. No model, no git."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp, hypothesis_measures as hm


@pytest.fixture
def state(tmp_path: Path) -> Path:
    (tmp_path / "state").mkdir()
    return tmp_path / "state"


def measure(**more):
    return {"what": "the cost of an install, the Camp clip", "from": "the ads' platforms", "bars": {"holds": {"op": "<=", "n": 70, "unit": "% of the Work clip's"},
                                                                                              "refuted": [{"way": "the look", "op": ">", "n": 100, "unit": "%"}]}, **more}


# -- the measure ----------------------------------------------------------------------------------------------------------------------------

def test_a_measure_is_cleaned_strictly_and_given_an_id_a_span_and_no_value():
    (m,) = hm.clean([measure()])
    assert m == {"id": "m1", "what": "the cost of an install, the Camp clip", "from": "the ads' platforms", "by": "", "span_days": 28, "date": "", "value": None,
                 "bars": {"holds": {"op": "<=", "n": 70.0, "unit": "% of the Work clip's"}, "refuted": [{"op": ">", "n": 100.0, "unit": "%", "way": "the look"}]}}
    assert [x["id"] for x in hm.clean([measure(), measure(id="m1"), measure(id="mine")])] == ["m2", "m1", "mine"]
    assert hm.clean(None) == [] and hm.clean("") == []
    for bad, why in (([{"what": "x"}], "its bar"), ([{"bars": {"holds": {"op": ">=", "n": 1}}}], "its bar"), ([measure(bars={"holds": {"op": "~", "n": 1}})], "A bar is one of"),
                     ([measure(bars={"holds": {"op": ">=", "n": "lots"}})], "A bar is one of"), ("nope", "list"), ([measure()] * 5, "4 measures at most"), ([3], "says what")):
        with pytest.raises(ValueError, match=why):
            hm.clean(bad)


def test_a_condition_is_met_when_every_value_that_bears_on_it_meets_its_bar_and_none_is_missing():
    def item(*ms):
        return {"measures": hm.lenient(list(ms))}
    one = measure(value={"n": 60})
    assert hm.met(item(one)) == {"holds": True, "refuted": []}
    assert hm.met(item(measure(value={"n": 120}))) == {"holds": False, "refuted": ["the look"]}
    assert hm.met(item(measure())) == {"holds": None, "refuted": []}                                       # no value yet: nothing is met
    two = measure(what="coming back", bars={"holds": {"op": ">=", "n": 40}}, value={"n": 30})
    assert hm.met(item(one, two)) == {"holds": False, "refuted": []}                                       # one bar missed
    assert hm.met(item(one, measure(what="coming back", bars={"holds": {"op": ">=", "n": 40}}))) == {"holds": None, "refuted": []}      # one value still to come
    assert hm.met({"measures": []}) == {"holds": None, "refuted": []}
    eq = measure(bars={"holds": {"op": "=", "n": 5}, "refuted": []}, value={"n": 5})
    assert hm.met(item(eq))["holds"] is True


# -- in the record: the date, the due, the values ---------------------------------------------------------------------------------------------



def test_measures_are_set_changed_and_dropped_and_a_day_given_makes_the_span(state):
    item = hyp.add(state, "Camp brings more", "installs cost less")
    got = hyp.measure_set(state, item["id"], **measure(span_days=14))
    (m,) = got["measures"]
    assert m["id"] == "m1" and m["span_days"] == 14 and m["date"] == hm.date_of(item["started"], 14)
    changed = hyp.measure_set(state, item["id"], "m1", what="installs per euro", bars={"holds": {"op": ">=", "n": 3}})["measures"][0]
    assert changed["what"] == "installs per euro" and changed["bars"]["holds"]["n"] == 3 and changed["bars"]["refuted"][0]["way"] == "the look" and changed["date"] == m["date"]       # a bar changes that bar only
    day = hm.date_of(item["started"], 100)
    dated = hyp.measure_set(state, item["id"], "m1", date=day)["measures"][0]
    assert dated["date"] == day and dated["span_days"] == 100
    assert len(hyp.measure_set(state, item["id"], **measure(what="second"))["measures"]) == 2
    assert [x["id"] for x in hyp.measure_drop(state, item["id"], "m1")["measures"]] == ["m2"]
    with pytest.raises(ValueError, match="That measure is gone"):
        hyp.measure_drop(state, item["id"], "m1")
    for _ in range(3):
        hyp.measure_set(state, item["id"], **measure(what="more"))
    with pytest.raises(ValueError, match="4 measures at most"):
        hyp.measure_set(state, item["id"], **measure(what="one too many"))
    hyp.judge(state, item["id"], "held")
    with pytest.raises(ValueError, match="judged already"):
        hyp.measure_set(state, item["id"], **measure())


def test_the_row_is_due_at_the_later_of_the_goals_and_the_measures_date_and_a_measure_alone_is_a_test(state):
    item = hyp.add(state, "Camp brings more", "installs cost less")
    assert hyp.due(state, {}, "2030-01-01") == []                                                           # no test at all: never due
    hyp.measure_set(state, item["id"], **measure(span_days=14))
    date = hyp.read(state)["items"][0]["measures"][0]["date"]
    assert hyp.due(state, {}, hm.date_of(date, -1)) == [] and [i["id"] for i in hyp.due(state, {}, date)] == [item["id"]]                         # a measure alone: its date
    hyp.attach(state, item["id"], test="interview")
    assert hyp.due(state, {"interview": "work"}, "2099-01-01") == [] and hyp.due(state, {"interview": "done"}, hm.date_of(date, -1)) == []      # a goal at work, or a date not reached
    assert len(hyp.due(state, {"interview": "done"}, date)) == 1                                              # both: the later of the two
    only_goal = hyp.add(state, "Goal only", "x")
    hyp.attach(state, only_goal["id"], test="playtest")
    assert [i["id"] for i in hyp.due(state, {"interview": "done", "playtest": "done"}, "2000-01-01")] == [only_goal["id"]]            # as before


def test_not_sure_yet_puts_it_off_to_a_day_after_today_and_moves_the_measures_date(state):
    item = hyp.add(state, "Camp brings more", "installs cost less", measures=[measure(date="2026-01-01")])
    hyp.attach(state, item["id"], test="interview")
    places = {"interview": "done"}
    assert len(hyp.due(state, places, "2026-06-01")) == 1
    for bad in ("2020-01-01", "soon", hm.day(hyp.ideas._now())):
        with pytest.raises(ValueError, match="Pick a day to look again"):
            hyp.judge(state, item["id"], "unsure", "", 0, "", bad)
    got = hyp.judge(state, item["id"], "unsure", "need more", 0, "", "2099-02-01")
    assert got["state"] == "open" and got["look_on"] == "2099-02-01" and got["measures"][0]["date"] == "2099-02-01" and got["evidence"][-1]["text"] == "need more"
    assert hyp.due(state, places, "2099-01-31") == [] and len(hyp.due(state, places, "2099-02-01")) == 1




def test_a_measure_kept_on_a_hypothesis_has_the_day_it_is_read_on_and_a_person_s_hypothesis_starts_today(state):
    item = hyp.add(state, "Camp brings more", "installs cost less", measures=[measure()])
    today = hm.day(hyp.ideas._now())
    assert item["started"] == today and item["measures"][0]["date"] == hm.date_of(today, 28)
    back = hyp.read(state)["items"][0]
    assert back["measures"] == item["measures"] and back["started"] == today
    prop = hyp.add(state, "A leader's", "x", by="leader", party="product", measures=[measure()])
    assert prop["started"] == "" and prop["measures"][0]["date"] == hm.date_of(today, 28)               # worked out from today until it is kept
    assert hyp.keep(state, prop["id"])["started"] == today


def test_a_value_is_kept_with_who_gave_it_and_a_number_that_is_none_is_refused(state):
    item = hyp.add(state, "Camp brings more", "installs cost less", measures=[measure()])
    got = hyp.value(state, item["id"], "m1", "64.5", "person", "the ads dashboard")
    assert got["measures"][0]["value"]["n"] == 64.5 and got["measures"][0]["value"]["by"] == "person" and got["measures"][0]["value"]["from"] == "the ads dashboard" and got["measures"][0]["value"]["at"]
    assert hm.met(hyp.read(state)["items"][0])["holds"] is True
    for bad in ("lots", None, True, float("nan")):
        with pytest.raises(ValueError, match="is a number"):
            hyp.value(state, item["id"], "m1", bad)
    with pytest.raises(ValueError, match="That measure is gone"):
        hyp.value(state, item["id"], "m9", 1)
