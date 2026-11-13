"""The Orkmaster's question about the Board in the code on the window (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md F.1, F.3; decisions §255.10), in a real browser against a stub host answering the
goal-free row `in_code` and the command `ideas.in_code`, at the two widths of `tests/narrow.py`: the card's face (the alert sign, the Orkmaster's head, the question as its name, under the first lane), lifted its words
(the sentence, how many pages are in the history, what waits when the repository was found public since) and its two answers, **Publish the Board** and **Keep the Board off the repository**, each sent as
`ideas.in_code {answer}`; and for a remote Orkboard cannot read *Is this repository private?* first, **Private** sent, **Public** only going on to the publish question. Screenshots to $INCODE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["INCODE_SHOTS"]) if os.environ.get("INCODE_SHOTS") else None
SAY = "Your goals, their specs, the leaders' words and the decisions will be public, in the repository's history: a later No does not take them back."
HELD = "This repository is public: the Board waits for your answer before anything is pushed."
WORDS = {"private": "Private", "public": "Public", "publish": "Publish the Board", "off": "Keep the Board off the repository"}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def in_code_row(step="publish", pages=0, held=HELD):
    text = SAY + ("" if not pages else f" {pages} pages of the Board are already in its history.")
    title = "Is this repository private?" if step == "private" else "Publish the Board?"
    return need("in_code", "", "", title, text, step=step, visibility="unknown" if step == "private" else "public", public=step != "private", pages_in_history=pages, ask="Is this repository private?",
                held=held if step != "private" else "", words=WORDS, blocks=True, priority="high")


class InCodeHost(HandHost):
    """A project of four parties with nothing to ask but the Orkmaster's row `in_code`."""

    def __init__(self, **more):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.needs = [in_code_row(**more)]

    def handle(self, name, a):
        if name == "ideas.in_code":
            self.log.append((name, a))
            self.needs = []
            return self.bump({"ok": True, "answer": a["answer"], "in_code": a["answer"] != "off", "visibility": "public"})
        return super().handle(name, a)


def open_card(gui, width="wide", **more):
    pg, host, log = open_hand(gui, host=InCodeHost(**more), width=width)
    pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg):
    return pg.locator('.hand-card[data-kind="in_code"]')


def lifted(pg):
    return pg.locator(".hand-lifted")


def lift(pg):
    front(pg).click(position={"x": 10, "y": 24})
    lifted(pg).wait_for(timeout=WAIT_MS)
    return lifted(pg)


def buttons(card):
    return [b.inner_text().strip() for b in card.locator(".hand-answers .ork-btn").all()]






@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_publish_sends_the_yes_and_the_card_goes(gui, width):
    pg, host, log = open_card(gui, width)
    try:
        lift(pg).get_by_role("button", name="Publish the Board").click()
        assert _calls(pg, host, "ideas.in_code") == [{"answer": "publish"}]
        pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"in_code\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_keep_the_board_off_sends_the_no_and_the_card_goes(gui, width):
    pg, host, log = open_card(gui, width)
    try:
        lift(pg).get_by_role("button", name="Keep the Board off the repository").click()
        assert _calls(pg, host, "ideas.in_code") == [{"answer": "off"}]
        pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"in_code\"]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)




