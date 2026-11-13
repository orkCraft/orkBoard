"""Spec 152 B.5 / D: while a goal's step is being accepted, its Map node says so in a field of its own (`busy: "accepting"`), its `state` staying `working` (a new state would go
through every `state == "working"` check); before and after the run the node has no such field."""
from __future__ import annotations

import pytest

from orkboard.realm import ideas
from tests.browser_kit import gui  # noqa: F401  (fixture, for the browser test)
from tests.test_idea_accept import OK, _work, host, model, parties  # noqa: F401  (the fixtures of the acceptance's tests)



def _node(h, slug):
    return next(n for n in h.command("ideas.map", {})["nodes"] if n["slug"] == slug)


@pytest.mark.accepts
def test_a_node_whose_step_is_being_accepted_has_busy_accepting_and_its_state_stays_working(host, parties, model):    # noqa: F811
    w = _work(host, parties, model)
    seen = []

    def accept(row):
        seen.append(_node(host, w.slug))
        return OK
    model.said[("accept_step", "")] = accept
    assert "busy" not in _node(host, w.slug)
    w.merge("k1")
    w.runner.tick()
    w.tick()
    assert len(seen) == 1 and seen[0]["busy"] == "accepting" and seen[0]["state"] == "working"
    after = _node(host, w.slug)
    assert "busy" not in after and ideas.state(host.ideas.state_dir, w.slug)["state"] in ("working", "done")
