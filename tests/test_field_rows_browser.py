"""Spec 82 A (docs/specs/82-the-field-at-a-glance.md §2, §3): the field's rows, in a real browser at 1 440 × 900 against a stub host that answers `ideas.map` as the town does,
each task with its `row` (`map_stage.row_of`, the real function): the members' columns and the rows across them in one grid, a row's label at the table's left edge, an empty row not
drawn, a row from the host before a goal's own waves, and the line over the table that says why nothing is at work."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import map_stage  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost, pip  # noqa: E402
from tests.test_shell_browser import _open, box  # noqa: E402

pytestmark = pytest.mark.browser


class RowsHost(ArenaHost):
    """The arena's stub, its tasks carrying the row the town gives them."""

    def map_doc(self):
        doc = super().map_doc()
        for n in doc["nodes"]:
            rows = map_stage.row_of(n["tasks"])
            for t in n["tasks"]:
                t["row"] = rows[t["id"]]
        return doc


def alone(host, tasks, **node):
    """The register goal with only these tasks, no other goal's, no result."""
    for n in host.nodes:
        n["tasks"], n["results"] = [], []
    host.node_of("register")["tasks"] = tasks
    host.node_of("register").update(node)
    host.bump({})


@pytest.fixture
def field(gui):
    pg, host, errors = _open(gui, host=RowsHost(), ready=".arena-phead")
    pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
    pg.locator(".arena-task[data-key='register/k3']").wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def y(pg, key):
    return pg.locator(f".arena-task[data-key='{key}']").bounding_box()["y"]


def test_what_runs_at_once_lies_on_one_line_across_every_members_column(field):
    pg, host = field
    now = [y(pg, k) for k in ("register/k3", "cookie/f2", "signin/v1", "signin/c2", "cookie/f1")]      # screens, screens, reviewer, words (two goals), backend: one row
    assert max(now) - min(now) <= 0.5
    xs = [pg.locator(f".arena-task[data-key='{k}']").bounding_box()["x"] for k in ("register/k3", "signin/v1", "signin/c2")]
    assert xs == sorted(xs) and len(set(xs)) == 3                                                       # in three members' columns, left to right
    assert abs(y(pg, "register/k4") - y(pg, "register/c1")) <= 0.5                                      # Later: the screens' and the reviewer's, one line
    assert y(pg, "register/k5") > max(now) + 100 and y(pg, "register/k4") > y(pg, "register/k5") + 100  # Next under Now, Later under Next
    for agent in ("backend", "screens", "reviewer", "words"):                                           # a column is as wide as the member over it
        assert abs(box(pg, f".arena-stack[data-agent={agent}]")["x"] - box(pg, f".arena-member[data-agent={agent}]")["x"]) <= 1
    assert [c.get_attribute("data-row") for c in pg.locator(".arena-stack[data-agent=screens] .arena-phase").all()] == ["now", "later"]      # a cell for the rows it has stacks in


def test_a_rows_label_is_at_the_tables_left_edge_and_an_empty_row_is_not_drawn(field):
    pg, host = field
    labels = pg.locator(".arena-row__lbl")
    assert [l.text_content() for l in labels.all()] == ["Now", "Next", "Later"]
    grid = box(pg, ".arena-cols__grid")
    assert all(abs(l.bounding_box()["x"] - grid["x"]) <= 6 for l in labels.all())                       # at the left edge, over the first column
    assert "pixel" in labels.first.evaluate("e => getComputedStyle(e).fontFamily").lower()
    assert [l.evaluate("e => getComputedStyle(e).color") for l in labels.all()][0] != labels.nth(1).evaluate("e => getComputedStyle(e).color")      # Next and Later are muted, Now is not
    assert labels.nth(1).evaluate("e => getComputedStyle(e).color") == labels.nth(2).evaluate("e => getComputedStyle(e).color")
    ys = [l.bounding_box()["y"] for l in labels.all()]
    assert ys == sorted(ys) and ys[0] < y(pg, "register/k3") and y(pg, "register/k3") < ys[1] < y(pg, "register/k5") < ys[2] < y(pg, "register/k4")      # each over its row's cards
    node, cards = host.node_of("register"), pg.locator(".arena-task").count()
    for t in node["tasks"]:
        t["state"] = "ready" if t["state"] == "waiting" else t["state"]                                 # nothing waits any more: the rows under Now are empty
    host.bump({})
    pg.wait_for_function("() => document.querySelectorAll('.arena-row__lbl').length === 1", timeout=WAIT_MS)
    assert pg.locator(".arena-row__lbl").text_content() == "Now" and pg.locator(".arena-phase[data-row=next], .arena-phase[data-row=later]").count() == 0
    assert box(pg, ".arena-cols__grid")["height"] > 0 and pg.locator(".arena-task").count() == cards - 2         # the three that waited went to Now, k5 into its goal's stack of the backend, k4 into the screens', so two cards fewer in sight


def test_the_hosts_row_comes_before_the_goals_own_wave_and_rows_past_three_are_later(field):
    pg, host = field
    chain = [pip("a", "First", "running", wave=1), pip("b", "Second", "waiting", ["a"], 2, "screens"), pip("c", "Third", "waiting", ["b"], 3), pip("d", "Fourth", "waiting", ["c"], 4, "screens"),
             pip("e", "Fifth", "waiting", ["d"], 5, "reviewer", "check")]
    alone(host, chain)
    pg.locator(".arena-task[data-task=e]").wait_for(timeout=WAIT_MS)
    rows = {k: pg.locator(f".arena-task[data-task={k}]").locator("xpath=ancestor::*[contains(@class,'arena-phase')]").get_attribute("data-row") for k in "abcde"}
    assert rows == {"a": "now", "b": "next", "c": "later", "d": "later", "e": "later"}
    assert [l.text_content() for l in pg.locator(".arena-row__lbl").all()] == ["Now", "Next", "Later"]
    chain[1]["wave"] = 1                                                                                 # a wave of its own says Now; the host's row says Next, and it wins
    host.bump({})
    pg.wait_for_timeout(300)
    assert pg.locator(".arena-task[data-task=b]").locator("xpath=ancestor::*[contains(@class,'arena-phase')]").get_attribute("data-row") == "next"


def test_a_host_with_no_row_still_lays_the_rows_by_the_goals_waves(gui):
    pg, host, errors = _open(gui, host=ArenaHost(), ready=".arena-phead")                                  # the plain stub sends no `row`
    pg.locator(".arena-task[data-key='register/k5']").wait_for(timeout=WAIT_MS)
    assert [l.text_content() for l in pg.locator(".arena-row__lbl").all()] == ["Now", "Next", "Later"]
    assert abs(y(pg, "register/k3") - y(pg, "signin/v1")) <= 0.5 and y(pg, "register/k5") > y(pg, "register/k3") and y(pg, "register/k4") > y(pg, "register/k5")
    pg.close()
    assert not errors, "\n".join(errors)


# -- why nothing is at work (§3) ----------------------------------------------------------------------------------------------------------

def idle(pg):
    line = pg.locator(".arena-idle")
    return line.inner_text().strip() if line.count() else ""


def say(pg, host, tasks, words, **node):
    alone(host, tasks, **node)
    pg.wait_for_function("(w) => (document.querySelector('.arena-idle')?.textContent.trim() || '') === w", arg=words, timeout=WAIT_MS)
    return idle(pg)


def test_nothing_at_work_the_results_at_review_wait_for_a_look(field):
    pg, host = field
    assert idle(pg) == ""                                                                                # tasks at work: no line
    reviews = [pip("k1", "Challenge store", "review"), pip("k2", "Credential table", "review", by="screens"), pip("k3", "Register endpoint", "waiting", ["k1"], 2)]
    assert say(pg, host, reviews, "Nothing at work: 2 results wait for your look") == "Nothing at work: 2 results wait for your look"
    assert say(pg, host, reviews[1:], "Nothing at work: 1 result waits for your look") == "Nothing at work: 1 result waits for your look"
    box_ = pg.locator(".arena-idle").bounding_box()
    assert box_["y"] + box_["height"] <= box(pg, ".arena-cols__head")["y"] + 1                          # over the table's head
    assert pg.locator(".arena-idle").evaluate("e => getComputedStyle(e).color") == pg.locator(".arena-cap").first.evaluate("e => getComputedStyle(e).color")      # quiet


def test_nothing_at_work_the_tools_window_and_a_sign_in(field):
    pg, host = field
    host.limits[0]["left"] = 0.05
    host.limits[0]["rows"][0]["reset"] = "2099-01-01T14:20"
    held = lambda note="", **more: [pip("k1", "Challenge store", "held") | {"note": note, **more}, pip("k2", "Credential table", "waiting", ["k1"], 2)]      # noqa: E731
    window = {"kind": "limits", "ref": "", "title": "", "until": "2099-01-01T14:20"}
    assert say(pg, host, held("after 14:20"), "Nothing at work: Claude’s window is at 95 %, back at 14:20", waits=window)
    sign = {"kind": "sign_in", "ref": "codex", "title": "Codex", "tool": "Codex", "until": ""}
    assert say(pg, host, held(held_for="sign_in"), "Nothing at work: Codex waits for its sign-in", waits=sign)
    a_week = {"kind": "week", "ref": "", "title": "", "until": "2099-01-05T09:00"}
    assert say(pg, host, held("week · after 09:00"), "", waits=a_week) == ""                             # not one of the three: no line
    assert say(pg, host, [pip("k1", "Challenge store", "ready"), pip("k2", "Credential table", "waiting", ["k1"], 2)], "", waits=None) == ""        # nothing known: no line
    assert say(pg, host, held(held_for="sign_in") + [pip("k3", "Register endpoint", "running", by="screens")], "", waits=sign) == ""              # something runs: no line
