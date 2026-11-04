"""Spec 130 E.4 (decisions §239.4), in a real browser against a stub host: under *In analysis*, while goals put off wait for the reset, the pile's line says *waits for the reset · <day> <time>*: the earliest of them, a state and never a count;
no line when none waits; a held goal is not named (it has no reset), and its row says *Held* with **Talk**."""
from __future__ import annotations

import datetime as dt

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import open_column  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, node  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser
UNDER = '.col-under[data-under="analysis"]'


def iso(**later):
    return (dt.datetime.now() + dt.timedelta(**later)).isoformat(timespec="seconds")


class Host(HandHost):
    def __init__(self, nodes):
        super().__init__(bare=True)
        self.nodes = nodes

    def handle(self, name, a):
        if name == "ideas.talk":
            self.log.append((name, a))
            return self.bump({"ok": True})
        return super().handle(name, a)


def routed(slug, **more):
    return node(slug, "tech", f"Goal {slug}", "deck", state="routed", element="ice", **more)


def test_the_line_says_the_earliest_reset_and_its_time(gui):
    soon, later = dt.datetime.now().replace(second=0, microsecond=0) + dt.timedelta(days=2), dt.datetime.now() + dt.timedelta(days=4)
    pg, host, log = open_column(gui, host=Host([routed("a", held_until=later.isoformat(timespec="seconds")), routed("b", held_until=soon.isoformat(timespec="seconds"))]))
    try:
        got = pg.locator(UNDER).inner_text()
        assert got == f"waits for the reset · {soon.strftime('%a %H:%M')}", got
        box = pg.locator(UNDER).bounding_box()
        assert box["x"] + box["width"] <= pg.locator(".frame-column").bounding_box()["width"], "whole in the column, not cut"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_today_it_says_the_time_alone(gui):
    at = dt.datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
    pg, host, log = open_column(gui, host=Host([routed("a", held_until=at.isoformat(timespec="seconds"))]))
    try:
        assert pg.locator(UNDER).inner_text() == "waits for the reset · 23:59"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_no_line_with_none_waiting_nor_for_a_reset_passed(gui):
    pg, host, log = open_column(gui, host=Host([routed("a"), routed("b", held_until=iso(minutes=-5))]))
    try:
        assert pg.locator(UNDER).inner_text() == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_held_goal_is_not_named_and_its_row_says_held_with_talk(gui):
    pg, host, log = open_column(gui, host=Host([routed("a", held_for="hold")]))
    try:
        assert pg.locator(UNDER).inner_text() == ""
        card = pg.locator('.col-card--down[data-goal="a"]')
        assert "Held" in card.inner_text() and "held: nothing starts it until you press Talk" in card.get_attribute("aria-label")
        card.click(position={"x": 100, "y": 50})
        row = pg.locator('.col-list__row[data-goal="a"]')
        row.wait_for(timeout=WAIT_MS)
        assert "Held" in row.inner_text()
        row.locator("[data-talk]").click()
        assert _sent(pg, host, ("ideas.talk", {"idea": "a"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)
