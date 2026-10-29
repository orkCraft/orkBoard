"""A leader's no on the window (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §4.3; decisions §183.3), in a real browser against a stub host answering the rows `objection` and the command
`ideas.objection`, at the two widths of `tests/narrow.py`: one card for each leader that said no, in the route's order, under the first lane (the whole goal's), the question sign and the leader's own head, *<Leader> says no*
at its foot; lifted the leader's why, the smaller goal it would do when it named one, and only the answers that apply — *Drop the goal* (a danger button), *Do the smaller one* (when there is one), *Not now* (when the no names
a goal in line) and *Go on anyway* — each sending `ideas.objection {idea, party, answer}`; a refusal keeps the card. Screenshots to $OBJECTION_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["OBJECTION_SHOTS"]) if os.environ.get("OBJECTION_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def no(party, leader, why, instead="", after="", after_title="", answers=("drop", "go")):
    return need("objection", "tech", "night", "Night mode for the lobby", why, party=party, leader=leader, why=why, instead=instead, after=after, after_title=after_title, answers=list(answers))


ROWS = [no("design", "product-designer", "It adds a screen nobody leads to", instead="Only a dark theme file, no new screen", answers=("drop", "smaller", "go")),
        no("tech", "architect", "It adds a third caller to server/ws"),
        no("product", "product-manager", "The lobby comes first", after="kick", after_title="Kick a player from the room", answers=("drop", "later", "go"))]


class ObjectionHost(HandHost):
    """A project of four parties and a goal `night` of Tech's at Talk, three leaders having said no (Design with a smaller goal, Tech with none, Product naming a goal in line)."""

    def __init__(self):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.nodes.append(node("night", "tech", "Night mode for the lobby", "table", state="talk", element="ice", asks_you=True, needs_you="objection"))
        self.needs = [dict(r) for r in ROWS]
        self.refuse = False

    def handle(self, name, a):
        if name == "ideas.objection":
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The keeper is busy with this goal: a moment"}
            self.needs = [n for n in self.needs if not (n["kind"] == "objection" and n["party"] == a["party"])]
            return self.bump({"ok": True})
        return super().handle(name, a)


def open_objections(gui, width="wide"):
    pg, host, log = open_hand(gui, host=ObjectionHost(), width=width)
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg):
    return pg.locator('.hand-card[data-goal="night"][data-top="1"]')


def press(pg):
    front(pg).click(position={"x": 10, "y": 24})


def lifted(pg):
    return pg.locator(".hand-lifted")


def waiting(pg):
    """How many cards the goal's stack holds (only its top is a card in the page; the rest are backs)."""
    return int(pg.locator('.hand-stack[data-goal="night"]').get_attribute("data-cards"))


def labels(card):
    return [b.inner_text().strip() for b in card.locator(".hand-answers .ork-btn").all()]


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_no_is_a_card_saying_who_says_it_with_the_leaders_own_head_under_the_first_lane(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        assert waiting(pg) == 3, "one card a leader that said no, in one stack"
        c = front(pg)
        assert c.get_attribute("data-kind") == "objection"
        assert c.get_attribute("data-key") == "objection/night/design", "the route's order: Design said no first"
        assert c.locator(".hand-card__name").text_content().strip() == "Night mode for the lobby" and c.locator(".hand-card__head .ork-elem.ice").count() == 1
        assert c.locator(".hand-card__window .ork-sign.question").count() == 1 and c.locator(".hand-card__asker .ork-race__head").count() == 1
        assert "dryad" in c.locator(".hand-card__asker .ork-race__head").get_attribute("src"), "the leader of the party that said no, not the goal's"
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Design lead says no"
        assert c.locator(".ork-gem").count() == 0, "it spends nothing"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="night"]').count() == 1, "the whole goal's: under the first lane"
        shot(pg, f"{width}-objection-face")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_the_no_says_why_the_smaller_goal_and_only_the_answers_that_apply_with_drop_a_danger_button(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        press(pg)
        lifted(pg).wait_for(timeout=WAIT_MS)
        card = lifted(pg)
        assert card.locator(".hand-way__no").text_content().strip() == "Design lead says no"
        assert card.locator(".hand-way__words").inner_text() == "It adds a screen nobody leads to"
        assert "Only a dark theme file, no new screen" in card.locator(".hand-way__instead").inner_text()
        assert labels(card) == ["Drop the goal", "Do the smaller one", "Go on anyway"]
        assert card.get_by_role("button", name="Drop the goal").get_attribute("class").split().count("danger") == 1
        assert card.get_by_role("button", name="Do the smaller one").get_attribute("title") == "The goal becomes: Only a dark theme file, no new screen"
        assert card.locator(".hand-spend").count() == 0, "no cost line"
        shot(pg, f"{width}-objection-lifted")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_no_with_no_smaller_goal_and_no_goal_in_line_offers_only_drop_and_go_on_anyway(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        host.needs = [r for r in host.needs if r["party"] == "tech"]
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-stack[data-goal=\"night\"]')?.dataset.cards === '1'", timeout=WAIT_MS)
        press(pg)
        card = lifted(pg)
        card.wait_for(timeout=WAIT_MS)
        assert card.locator(".hand-way__no").text_content().strip() == "Tech lead says no" and card.locator(".hand-way__instead").count() == 0
        assert labels(card) == ["Drop the goal", "Go on anyway"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_not_now_is_for_the_no_that_names_a_goal_in_line_and_says_which(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        host.needs = [r for r in host.needs if r["party"] == "product"]
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-stack[data-goal=\"night\"]')?.dataset.cards === '1'", timeout=WAIT_MS)
        press(pg)
        card = lifted(pg)
        card.wait_for(timeout=WAIT_MS)
        assert labels(card) == ["Drop the goal", "Not now", "Go on anyway"]
        assert card.get_by_role("button", name="Not now").get_attribute("title") == "The goal waits for Kick a player from the room"
        card.get_by_role("button", name="Not now").click()
        assert _calls(pg, host, "ideas.objection") == [{"idea": "night", "party": "product", "answer": "later"}]
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_each_answer_sends_the_command_with_the_leader_and_the_answered_card_goes_and_the_next_comes_on_top(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        press(pg)
        lifted(pg).get_by_role("button", name="Do the smaller one").click()
        assert _calls(pg, host, "ideas.objection") == [{"idea": "night", "party": "design", "answer": "smaller"}]
        pg.wait_for_function("() => document.querySelector('.hand-stack[data-goal=\"night\"]')?.dataset.cards === '2'", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
        assert front(pg).get_attribute("data-key") == "objection/night/tech"
        press(pg)
        lifted(pg).get_by_role("button", name="Go on anyway").click()
        assert _calls(pg, host, "ideas.objection")[-1] == {"idea": "night", "party": "tech", "answer": "go"}
        pg.wait_for_function("() => document.querySelector('.hand-stack[data-goal=\"night\"]')?.dataset.cards === '1'", timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
        press(pg)
        lifted(pg).get_by_role("button", name="Drop the goal").click()
        assert _calls(pg, host, "ideas.objection")[-1] == {"idea": "night", "party": "product", "answer": "drop"}
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"night\"]:not(.is-gone)')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_refused_answer_keeps_the_card_lifted(gui, width):
    pg, host, log = open_objections(gui, width)
    try:
        host.refuse = True
        press(pg)
        lifted(pg).get_by_role("button", name="Go on anyway").click()
        assert _calls(pg, host, "ideas.objection") == [{"idea": "night", "party": "design", "answer": "go"}]
        pg.wait_for_timeout(300)
        assert lifted(pg).count() == 1 and waiting(pg) == 3, "refused: nothing changed"
    finally:
        pg.close()
    assert not [m for m in log if "pageerror" in m], "\n".join(log)
