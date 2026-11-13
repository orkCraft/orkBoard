"""Spec 35 §4, §5: an idea's risk by rules (a case per trigger row), whole words in any case, the repository's own paths,
the max with the model's, the Risks line; who passes a plan (the nine cells)."""
from __future__ import annotations

import pytest

from orkboard.realm import idea_risk
from orkboard.realm.idea_risk import assess


@pytest.mark.parametrize("touches,texts,trigger,level", [
    (["src/auth/session.py"], [], idea_risk.SECRETS, "medium"),
    ([], ["Keep the API Token out of the logs"], idea_risk.SECRETS, "medium"),
    (["db/migrations/0002_add.py"], [], idea_risk.DATA, "medium"),
    (["schema/users.sql"], [], idea_risk.DATA, "medium"),
    ([], ["Delete the old user data at start"], idea_risk.DATA, "medium"),
    ([".github/workflows/ci.yml"], [], idea_risk.CI, "medium"),
    (["Dockerfile"], [], idea_risk.CI, "medium"),
    ([], ["then RELEASE it"], idea_risk.CI, "medium"),
    ([], ["this is a Breaking Change for callers"], idea_risk.API, "medium"),
    ([f"d{n}/x.py" for n in range(6)], [], idea_risk.WIDE, "medium"),
    ([], ["We send an email to every user"], idea_risk.OUTWARD, "high"),
    ([], ["push to main when green"], idea_risk.OUTWARD, "high"),
])
def test_each_trigger_raises_the_risk(touches, texts, trigger, level):
    got = assess(touches, texts)
    assert trigger in got.triggers and got.risk == level


@pytest.mark.parametrize("risk,priority,what", [
    ("low", "high", "start"), ("low", "normal", "start"), ("low", "low", "night"),
    ("medium", "high", "start"), ("medium", "normal", "wait"), ("medium", "low", "wait"),
    ("high", "high", "wait"), ("high", "normal", "wait"), ("high", "low", "wait")])
def test_the_nine_cells_of_autostart(risk, priority, what):
    assert idea_risk.decide(risk, priority, night=True) == what


@pytest.mark.parametrize("risk,priority,what", [
    ("low", "high", "night"), ("low", "normal", "night"), ("low", "low", "night"),
    ("medium", "high", "night"), ("medium", "normal", "wait"), ("medium", "low", "wait"),
    ("high", "high", "wait"), ("high", "normal", "wait"), ("high", "low", "wait")])
def test_work_at_night_holds_what_would_start_by_itself_and_what_waits_for_the_person_still_waits(risk, priority, what):
    """Spec 121 §4.2: `held_for_night`: `start` and `night` are "night" (held for the window); `wait` stays `wait`."""
    assert idea_risk.decide(risk, priority, held_for_night=True) == what == idea_risk.decide(risk, priority, night=True, held_for_night=True)
    assert (idea_risk.decide(risk, priority) == "wait") == (what == "wait")                    # the table's own rules are unchanged
    assert idea_risk.decide(risk, priority, held_for_night=False) == idea_risk.decide(risk, priority)
