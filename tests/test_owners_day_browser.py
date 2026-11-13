"""Spec 107 parts D, E and G (docs/specs/107-what-the-owners-day-said.md §4, §5, §7; decisions §182.3, §182.4, §182.7), in a real browser against stub hosts, at the two widths of `tests/narrow.py`:

D, a goal dropped from its card: **…** on the Orkmaster's lane's card at the narrow width (its back), on the route card lifted and on a goal's face over the pane, its one item *Drop this goal…*; at the wide width the Orkmaster's goals are the
column's (spec 128 B) and a goal in analysis is dropped with **Remove** in its list, one of To review or put off from the choices its card lifts (tests/test_column_browser.py),
the question asked in place (*Drop this goal?*, *Keep it* · *Drop it*, *Its work stops first.* while tasks run), `ideas.stop` then `ideas.drop`, the host's refusal said in the card, a 44 px target under touch;
E, a goal sent lies in the Orkmaster's lane (the column's In analysis at the wide width) at once and its route card stays in the hand;
G, what works shows: a task card at work shows the flame (its goal's rune glowing, spec 111 §3.1; it replaced the stepping drawing and the dotted line of before), says the time it has worked and ticks it, a card whose state changed
flashes its frame once, the flash off and the flame still under reduced motion (the time still ticks)."""
from __future__ import annotations

import datetime as dt
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand, pane  # noqa: E402
from tests.test_route_card_desktop_browser import RouteHost, lift, open_route  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402
from tests.test_table_desktop_browser import TableHost, node, start, task  # noqa: E402

pytestmark = pytest.mark.browser

REFUSED = "The keeper is busy with this goal: a moment"
SAID = "The Orkmaster is reading it: drop it when it is done"


class Dropping:
    """What a host does with `ideas.drop` and `ideas.stop`: the goal goes (its node and rows), or the host refuses (`refuse`); `on_socket` answers a refusal as the page's socket does (`ok: false`)."""
    refuse = ""

    def handle(self, name, a):
        if name == "ideas.drop":
            self.log.append((name, a))
            if self.refuse:
                raise ValueError(self.refuse)
            self.nodes = [n for n in self.nodes if n["slug"] != a["slug"]]
            self.needs = [n for n in self.needs if n.get("idea") != a["slug"]]
            self.rev += 1
            return {"ok": True}
        if name == "ideas.stop":
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            try:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
            except ValueError as e:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": str(e)}))
        ws.on_message(on_message)


def ago(seconds):
    return (dt.datetime.now() - dt.timedelta(seconds=seconds)).isoformat(timespec="seconds")


class DayHost(Dropping, TableHost):
    """The table's stub with a goal just sent (routed, on the table, asking), a task at work for 72 seconds, and the commands of a drop."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.nodes.append(node("fresh", "tech", "A goal just sent", "routed", element="ice", sign="feature", asks_you=True))
        for n in self.nodes:
            for t in n["tasks"]:
                if t["state"] in ("running", "testing"):
                    t["started"] = ago(72)

    def push(self):
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))


class DayRoute(Dropping, RouteHost):
    """The route card's stub (the goal just sent lies on the table, asking; its route row is in the hand) with the commands of a drop."""


@pytest.fixture(params=narrow.WIDTHS)
def day(gui, request):
    errors: list[str] = []
    server, browser = gui
    host = DayHost()
    pg = narrow.page(browser, request.param)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def first(pg):
    return pg.locator('.table-lane[data-lane="first"]')


def ask_drop(box):
    """Press the **…** in `box` and its one item; the question it asks in place."""
    box.locator(".table-dropper .table-menu__btn").first.click()
    items = box.get_by_role("menuitem")
    assert [i.inner_text().strip() for i in items.all()] == ["Drop this goal…"] and items.first.locator(".ork-icon").count() == 1
    items.first.click()
    ask = box.get_by_role("alertdialog")
    ask.wait_for(timeout=WAIT_MS)
    return ask


# -- E: a goal sent lies on the table ------------------------------------------------------------------------------------------------------------


# -- D: drop a goal from its card ----------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_route_card_lifted_has_the_menu_and_asks_inside_the_card(gui, width):
    host = DayRoute()
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        ask = ask_drop(lifted)
        card = lifted.locator(".hand-body") if lifted.locator(".hand-body").count() else lifted               # wide: the body in the hand's place is the card's inside (spec 168 D1)
        assert ask.bounding_box()["x"] >= card.bounding_box()["x"] - 1 and ask.bounding_box()["x"] + ask.bounding_box()["width"] <= card.bounding_box()["x"] + card.bounding_box()["width"] + 1, "asked in the card"
        ask.get_by_role("button", name="Keep it").click()
        assert not [n for n, _ in host.log if n == "ideas.drop"]
        ask = ask_drop(lifted)
        ask.get_by_role("button", name="Drop it").click()
        assert _calls(pg, host, "ideas.drop") == [{"slug": "fresh"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goals_face_over_the_pane_has_the_menu_in_its_head(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator('.hand-card[data-goal="timer"][data-top="1"]').click(position={"x": 10, "y": 24})
        pg.locator(".hand-ways-row, .hand-lifted").get_by_role("button", name="Open…").click()
        box = pane(pg)
        box.locator(".hand-stopface").wait_for(timeout=WAIT_MS)
        head = box.locator(".hand-stopface__head")
        assert head.locator(".table-dropper").count() == 1
        ask = ask_drop(head)
        ask.get_by_role("button", name="Drop it").click()
        assert _calls(pg, host, "ideas.drop") == [{"slug": "timer"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- G: what works shows the flame (spec 111 §3.1, decisions §187.2; the steps and the dotted line of spec 107 §7 are gone) --------------------------------------------------------------------------------------------------------------------------

WORKING = '.table-card[data-state="running"], .table-card[data-state="testing"]'


def anim(el, pseudo=""):
    return el.evaluate("(e, p) => { const s = getComputedStyle(e, p || null); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }", pseudo)
