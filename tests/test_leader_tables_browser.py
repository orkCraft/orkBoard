"""Spec 168 C4 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.16.4, .6, .8, §284.1), in a real browser at 1366 × 768 against a stub host: a goal picked through a leader's tab.

An idea (Talk): one row of three groups, *Its verdict*, *Needs your answer*, *Could be better*, cards of 144 x 202 only, three a group at most; a better taken and a way taken through the commands (`ideas.take_better`, `ideas.take_way`),
*Undo* on the rewrite, the open fork's card. A spec: the header of its steps' small cards (56 x 78) with their seats' heads and tools, the seat whose tool cannot do its step marked **!**, the parts now and as they will be. The implementation: lanes by
its seats with arrows, the tasks sent back after. Pictures to the directory ORKCRAFT_SHOTS_DIR names when it is set (`c4-<table>.png`)."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import step_needs  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import WayHost, open_tab, pick, task, watch  # noqa: E402

pytestmark = pytest.mark.browser

VIEW = {"viewport": {"width": 1366, "height": 768}}
SAY = {
    "leaders": [{"party": "tech", "leader": "Architect", "craft": "engineering", "weigher": False, "verdict": "doubt", "why": "one clock on the server", "instead": "", "after": "", "priority": "", "risk": "",
                 "needs": [{"id": "n1", "kind": "conflict", "line": "Goes against §208: the round's state lives on the server", "title": "", "rests_on": "§208", "legacy": False, "state": "open", "way": None, "written": False,
                            "ways": [{"name": "The new one replaces §208", "line": "write a decision that replaces it"}, {"name": "Keep §208", "line": "the goal changes"}]},
                           {"id": "n2", "kind": "risk", "line": "Every answer is kept until the round ends", "title": "", "rests_on": "", "legacy": False, "state": "open", "way": None, "written": False,
                            "ways": [{"name": "Keep the last answer only", "line": ""}, {"name": "Accept the risk", "line": ""}]}],
                 "better": [{"id": "b1", "line": "Show the best answer after the vote", "weight": "lighter", "state": "open", "written": False},
                            {"id": "b2", "line": "Keep the last five rounds' best", "weight": "heavier", "state": "open", "written": False}]}],
    "rewrite": None, "fork": None, "judged": 0, "judge_left": 2, "answered": False, "waiting": [], "to_judge": []}


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(Path(d) / name))


class LeaderHost(WayHost):
    """The table's host with the goal `seat` at a state, a say on it, a route of three parties with tools (Tech on Claude Code and its tester on Codex, Art on Codex) and tasks in three bands; the say's commands answer and change the say."""

    def __init__(self, state):
        super().__init__(state=state, route=[{"step": "party", "party": p, "goal": "seat"} for p in ("game", "tech", "art")])
        by = {p["slug"]: p for p in self.parties}
        by["tech"].update(tool="claude", tools={"tester": "codex"})
        by["art"].update(tool="codex")
        self.seat = next(n for n in self.nodes if n["slug"] == "seat")
        self.seat["say"] = copy.deepcopy(SAY)
        self.seat["tasks"] = [task("s1", "Keep the seat when a socket reconnects", "running", party="tech"), task("s3", "Check the seat", "running", "reviewer", "check", tag="Review of a change", party="tech"),
                              task("s4", "Test the seat", "waiting", "tester", tag="Tests", party="tech"), task("s2", "Reset the round timer when a player rejoins", "failed", "tester", party="tech", round=2, error="3 checks failed")]

    def handle(self, name, a):
        if name == "ideas.map":
            got = super().handle(name, a)
            for n in got["nodes"]:
                n["steps"] = step_needs.steps(n, got["goals"])
            return got
        if name in ("ideas.take_better", "ideas.take_way", "ideas.leave_say", "ideas.undo_rewrite", "ideas.say_fork"):
            self.log.append((name, a))
            say = self.seat["say"]
            item = next((x for l in say["leaders"] for x in [*l["needs"], *l["better"]] if x["id"] == a.get("id")), None)
            if name in ("ideas.take_better", "ideas.take_way") and item:
                item.update(state="taken", way=a.get("way"))
                if name == "ideas.take_better":
                    say["rewrite"] = {"id": "w-1", "at": "", "ids": [item["id"]], "parties": ["tech"], "before": "a", "after": "b", "undoable": True}
            elif name == "ideas.leave_say" and item:
                item["state"] = "left"
            elif name == "ideas.undo_rewrite":
                say["rewrite"] = None
            elif name == "ideas.say_fork":
                say["fork"] = None
            self.rev += 1
            self.push()
            return {"ok": True}
        return super().handle(name, a)


def start(gui, state):
    server, browser = gui
    errors: list[str] = []
    host = LeaderHost(state)
    pg = browser.new_context(**VIEW).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    open_tab(pg, "tech")
    pick(pg, "seat")
    pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
    return pg, host, errors


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def size(loc):
    b = loc.bounding_box()
    return round(b["width"]), round(b["height"])


# -- an idea ------------------------------------------------------------------------------------------------------------------------------------------

def test_an_idea_through_a_leader_is_one_row_of_three_groups_of_big_cards_that_fit_the_window(gui):
    pg, host, errors = start(gui, "talk")
    pg.locator('[data-view="say"] .say-group').first.wait_for(timeout=WAIT_MS)
    groups = pg.locator(".say-group")
    assert [g.get_attribute("data-group") for g in groups.all()] == ["verdict", "needs", "better"]
    assert [g.locator(".ork-label").first.inner_text().strip().lower() for g in groups.all()] == ["its verdict", "needs your answer", "could be better"]
    assert len({round(g.bounding_box()["y"]) for g in groups.all()}) == 1, "one row"
    assert [pg.locator(f'.say-group[data-group="{k}"] .say-card').count() for k in ("verdict", "needs", "better")] == [1, 2, 2]
    for c in pg.locator(".say-card").all():
        assert size(c) == (144, 202), "the big card, no other size"
    assert pg.locator('.say-card[data-group="needs"].is-alert').count() == 2, "an open need asks you"
    assert pg.locator('.say-card[data-group="verdict"] [data-verdict="doubt"]').count() == 1
    assert [c.get_attribute("data-weight") for c in pg.locator('.say-card[data-group="better"]').all()] == ["lighter", "heavier"]
    assert "lighter" in pg.locator('.say-card[data-weight="lighter"]').inner_text() and "§208" in pg.locator('.say-card[data-kind="conflict"]').inner_text()
    last = max(c.bounding_box()["y"] + c.bounding_box()["height"] for c in pg.locator(".say-card").all())
    assert last < 768 - 140, "the row ends above the hand"
    assert pg.locator(".table-over").count() == 0
    shot(pg, "c4-idea.png")
    finish(pg, errors)


def test_a_better_is_taken_and_a_way_is_taken_through_the_commands_and_the_rewrite_is_undone(gui):
    pg, host, errors = start(gui, "talk")
    pg.locator('.say-card[data-say="b1"]').click()
    pg.locator('.q-choose [data-choice="take"]').click()
    pg.locator('.say-card[data-say="b1"][data-state="answered"]').wait_for(timeout=WAIT_MS)
    assert ("ideas.take_better", {"idea": "seat", "id": "b1"}) in host.log
    assert "taken" in pg.locator('.say-card[data-say="b1"]').inner_text() and pg.locator(".table-over").count() == 0
    pg.locator('[data-act="undo-rewrite"]').click()
    pg.locator('[data-act="undo-rewrite"]').wait_for(state="detached", timeout=WAIT_MS)
    assert ("ideas.undo_rewrite", {"idea": "seat"}) in host.log
    pg.locator('.say-card[data-say="n1"]').click()
    pg.locator('.q-choose [data-choice="1"]').click()
    pg.locator('.say-card[data-say="n1"][data-state="answered"]').wait_for(timeout=WAIT_MS)
    assert ("ideas.take_way", {"idea": "seat", "id": "n1", "way": 1}) in host.log
    pg.locator('.say-card[data-say="n2"]').click()
    pg.get_by_role("button", name="Leave it").click()
    pg.locator('.say-card[data-say="n2"][data-state="answered"]').wait_for(timeout=WAIT_MS)
    assert ("ideas.leave_say", {"idea": "seat", "id": "n2"}) in host.log
    finish(pg, errors)


def test_an_open_fork_lies_first_among_the_needs_and_its_choice_answers_it(gui):
    pg, host, errors = start(gui, "talk")
    host.seat["say"]["fork"] = {"id": "fork-1", "at": "", "ids": ["b1", "b2"], "card": {"q": "Lighter or heavier?", "choices": ["Lighter", "Heavier"], "pick": 0, "why": "", "lines": []}}
    host.rev += 1
    host.push()
    pg.locator('.say-card[data-say="fork-1"]').wait_for(timeout=WAIT_MS)
    assert pg.locator('.say-group[data-group="needs"] .say-card').first.get_attribute("data-say") == "fork-1"
    assert pg.locator('.say-group[data-group="needs"] .say-card').count() == 3, "three a group at most"
    pg.locator('.say-card[data-say="fork-1"]').click()
    pg.locator('.q-choose [data-choice="1"]').click()
    pg.locator('.say-card[data-say="fork-1"]').wait_for(state="detached", timeout=WAIT_MS)
    assert ("ideas.say_fork", {"idea": "seat", "pick": 1}) in host.log
    finish(pg, errors)


# -- a spec -------------------------------------------------------------------------------------------------------------------------------------------

def test_a_spec_through_a_leader_has_the_steps_header_with_the_seat_that_cannot_marked_and_the_parts_now_and_as_they_will_be(gui):
    pg, host, errors = start(gui, "sections")
    pg.locator(".spec-steps .spec-step").first.wait_for(timeout=WAIT_MS)
    assert [s.get_attribute("data-step") for s in pg.locator(".spec-step").all()] == ["game", "tech", "art"]
    for c in pg.locator(".spec-step .ork-card.sm").all():
        assert size(c) == (56, 78), "the small card"
    tester = pg.locator('.spec-step[data-step="tech"] .spec-seat[data-seat="tester"]')
    assert tester.get_attribute("data-tool") == "codex" and tester.get_attribute("data-lacks") == "git browser"
    assert tester.locator(".spec-seat__lack").count() == 1 and "Codex" in tester.inner_text()
    assert pg.locator('.spec-step[data-step="tech"] .spec-seat[data-seat="grunt"] .spec-seat__lack').count() == 0, "Claude Code has git"
    assert pg.locator('.spec-step[data-step="art"][data-marked="1"]').count() == 1
    pg.locator('.spec-parts .spec-part').first.wait_for(timeout=WAIT_MS)
    part = pg.locator('.spec-part[data-kind="changed"]')
    assert part.locator('[data-side="now"]').count() == 1 and part.locator('[data-side="will"]').count() == 1
    assert "lobby.ts" in part.inner_text()
    assert "The seat is kept" in pg.locator('[data-view="spec"]').inner_text(), "its section as written stays under them"
    shot(pg, "c4-spec.png")
    finish(pg, errors)


# -- the implementation -------------------------------------------------------------------------------------------------------------------------------

def test_the_implementation_through_a_leader_is_lanes_by_its_seats_with_arrows_and_the_tasks_sent_back_after(gui):
    pg, host, errors = start(gui, "working")
    pg.locator('[data-view="seats"] .seat-lane').first.wait_for(timeout=WAIT_MS)
    assert [l.get_attribute("data-lane") for l in pg.locator(".seat-lane").all()] == ["make", "check", "accept", "back"]
    assert pg.locator('.seat-lane[data-lane="make"] [data-task]').count() == 2 and pg.locator('.seat-lane[data-lane="check"] [data-task="s3"]').count() == 1
    assert pg.locator('.seat-lane[data-lane="back"] [data-task="s2"]').count() == 1, "a task of round 2 runs again after the acceptance"
    assert pg.locator('.seat-lane[data-lane="make"] [data-task="s2"]').count() == 0
    assert pg.locator(".seat-arrow").count() == 3
    xs = [l.bounding_box()["x"] for l in pg.locator(".seat-lane").all()]
    assert xs == sorted(xs), "left to right as the work goes"
    assert pg.locator('.seat-lane[data-lane="check"] .seat-lane__seat[data-seat="reviewer"]').count() == 1
    assert pg.locator(".gv").count() == 1, "what it will change stays under the lanes"
    shot(pg, "c4-implementation.png")
    finish(pg, errors)
