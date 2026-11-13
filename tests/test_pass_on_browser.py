"""Spec 128 part D.3 (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.6), in a real browser against a stub host that keeps the snapshot's `passing` as the keeper does: a question passed on is a small card
over the Orkmaster's column's foot (its goal's rune, the two heads, the question, *passing on · N s*); pressed, **Answer it myself** (`ideas.pass_take`) and **Pass it now** (`ideas.pass_now`), each with the row's id. Screenshots to $PASS_SHOTS when it is set."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.column_kit import ColumnHost, open_column  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PASS_SHOTS"]) if os.environ.get("PASS_SHOTS") else None
QUESTION = "Does the round timer count on the phones or on the server?"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def row(left_s=6, answering=False, idea="talk", to="tech", by="design", n="q1"):
    return {"id": f"{idea}~{n}", "idea": idea, "task": "", "by": by, "to": to, "q": QUESTION, "left_s": left_s, "answering": answering}


class PassHost(ColumnHost):
    """The column's host with a question or two passing: `passing` is in the snapshot; `ideas.pass_take` and `ideas.pass_now` are logged and answered as the host's are."""

    def __init__(self):
        super().__init__()
        self.passing = []

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["passing"] = self.passing
        return doc

    def put(self, rows):
        self.passing = rows
        self.ws.send(json.dumps(self.snapshot()))

    def handle(self, name, a):
        if name in ("ideas.pass_take", "ideas.pass_now"):
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)


def start(gui, rows):
    host = PassHost()
    host.passing = rows
    pg, host, log = open_column(gui, host=host)
    return pg, host, log


def flights(pg):
    return pg.evaluate("() => import('/static/js/table/passing.js').then((m) => ({ ...m.passFlights }))")


def test_a_question_passing_is_a_small_card_over_the_columns_foot_with_its_rune_two_heads_the_question_and_its_seconds(gui):
    pg, host, log = start(gui, [row()])
    try:
        card = pg.locator(".frame-column .col-pass")
        card.wait_for(timeout=WAIT_MS)
        assert card.get_attribute("data-goal") == "talk"
        assert card.locator(".ork-elem").count() == 1 and card.locator(".ork-race__head").count() == 2, "the goal's rune and the two heads: who asked, who it is passed to"
        assert QUESTION in card.inner_text()
        text = card.locator(".col-pass__left").inner_text()
        assert text.startswith("passing on · ") and text.endswith(" s") and 1 <= int(text.split("· ")[1].split(" ")[0]) <= 6, text
        c, col, hand = card.bounding_box(), pg.locator(".frame-column").bounding_box(), pg.locator(".frame-hand").bounding_box()
        assert col["x"] <= c["x"] and c["x"] + c["width"] <= col["x"] + col["width"] and c["y"] + c["height"] <= hand["y"] + 1, "inside the column, over its foot"
        assert pg.locator(".col-pass .ork-btn").count() == 0, "its choices are shown when it is pressed"
        assert abs(c["width"] - 144) <= 1 and abs(c["height"] - 202) <= 1, f"a card, 144 x 202 (spec 168 A1): {c}"
        shot(pg, "passing")
        pg.wait_for_timeout(2300)
        assert int(card.locator(".col-pass__left").get_attribute("data-left")) <= 4, "the seconds count down between snapshots"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pressed_it_offers_answer_it_myself_and_pass_it_now_with_its_id(gui):
    pg, host, log = start(gui, [row()])
    try:
        pg.locator(".col-pass__main").click()
        take, now = pg.locator("[data-pass-take]"), pg.locator("[data-pass-now]")
        assert take.inner_text() == "Answer it myself" and now.inner_text() == "Pass it now"
        shot(pg, "passing-open")
        take.click()
        assert _sent(pg, host, ("ideas.pass_take", {"id": "talk~q1"}))
        now.click()
        assert _sent(pg, host, ("ideas.pass_now", {"id": "talk~q1"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)
