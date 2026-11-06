"""Spec 152 B.5 / D: while a goal's step is being accepted, its Map node says so in a field of its own (`busy: "accepting"`), its `state` staying `working` (a new state would go
through every `state == "working"` check); before and after the run the node has no such field. The words (`arenawords.js`) say *<leader> is accepting* for it."""
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


@pytest.mark.browser
def test_the_words_say_the_leader_is_accepting_for_a_working_node_with_that_busy_field(gui):
    pytest.importorskip("playwright.sync_api")
    from tests.test_shell_browser import StubHost
    from tests.test_sign_in_browser import _page
    pg, errors = _page(gui, StubHost())
    try:
        got = pg.evaluate("""async () => {
          const base = document.querySelector('link[href$="shell.css"]').href.replace('shell/shell.css', 'arena/');
          const m = await import(base + 'arenawords.js');
          const node = (more) => ({ slug: "a", title: "A", state: "working", stage: "implementation", tasks: [], ...more });
          return m.planningOf({ slug: "tech" }, [node({ busy: "accepting" }), node({ slug: "b" })], "Taskmaster").rows.map((r) => [r.slug, r.words, r.busy, r.doing || ""]); }""")
        assert got == [["a", "Taskmaster is accepting", True, "accepting"]]
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
