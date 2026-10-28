"""The route card and the start card (docs/specs/100-a-goals-way-as-cards.md §1, part A; docs/specs/99-a-goals-way.md §4), in a real browser against a stub host that answers spec 99's `route` and `start` rows and
their commands, at the two widths of `tests/narrow.py`: the card's face (the goal's element and name, the route's sign, the Orkmaster's crowned head, the cost's gem), the lifted card (the leaders' heads in order with
a × each, a head's popover and its Esc, the + with no Release and the offered parties first, the route in words, the cost in gem and words said again from the answer of an edit, its place in line, **Talk**,
**Later, by itself** only when the limits run low), a bug's two cards (*finding the cause* + **Talk**; *the report has a failing test*, **Start** and *The long way*), the start card's two costs. No sideways scroll.
Screenshots to $ROUTE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import PARTIES, HandHost, head, need, node  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["ROUTE_SHOTS"]) if os.environ.get("ROUTE_SHOTS") else None
RACES = {p[0]: (p[2], p[3]) for p in PARTIES}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


SHORT = ("cause", "report", "legacy", "legacy-report", "tidy", "balance")                    # the scenarios of a route of Tech alone, the short way
TYPES = {"cause": "bug", "report": "bug", "tidy": "tidy", "balance": "balance"}               # the goal type the row carries


def steps(parties):
    return [{"party": p, "leader": f"{p}-lead", "head": head(RACES[p][0], RACES[p][1])} for p in parties]


def cost_of(n):
    return {"calls": 2 * n, "usd_low": 0.5 * n, "usd_high": 1.5 * n}


class RouteHost(HandHost):
    """A project of four parties (Release led by the release manager) and one goal with a route card: `scenario` "route" (Product, Design, Tech; 3rd in line), "cause" (a bug, Tech alone, no failing test),
    "report" (a bug whose report holds a failing test), "tidy" and "balance" (a short goal that is no bug: the row's `type`), "legacy" (a short bug of a host that sends no `type`) or "start" (a step was added
    after Talk). `low`: the limits run low."""

    def __init__(self, scenario="route", low=False):
        super().__init__(empty=True)
        self.parties[3]["leader"]["slug"] = "release-manager"
        self.scenario, self.low = scenario, low
        title = "Players can't rejoin a room" if scenario in ("cause", "report", "legacy", "legacy-report") else "Clean up the lobby code" if scenario == "tidy" else "A team-vs-team round"
        self.nodes = [node("fresh", "tech", title, "hand", state="routed", element="ice")]
        self.route = ["tech"] if scenario in SHORT else ["product", "design", "tech"]
        self.needs = [self.row()]

    def row(self):
        if self.scenario == "start":
            return need("start", "tech", "fresh", self.nodes[0]["title"], "A step was added to the route", cost=cost_of(4), was=cost_of(3))
        short, more = self.scenario in SHORT, {}
        if self.scenario != "legacy":
            more["type"] = TYPES.get(self.scenario, "feature")
        return need("route", "tech", "fresh", self.nodes[0]["title"], "Route: " + ", then ".join(self.route), route=steps(self.route), cost=cost_of(len(self.route)), place=3, short=short,
                    reproduces=self.scenario in ("report", "legacy-report"), low=self.low, offer=["product"], **more)

    def handle(self, name, a):
        if name == "ideas.route_set":
            self.log.append((name, a))
            self.route = list(a["route"])
            self.needs = [self.row()]
            row = self.needs[0]
            return self.bump({"ok": True, "route": row["route"], "cost": row["cost"], "short": row["short"], "reproduces": row["reproduces"], "offer": row["offer"], "changed": False})
        if name in ("ideas.talk", "ideas.route_start", "ideas.route_later", "ideas.start"):
            self.log.append((name, a))
            self.needs = []
            return self.bump({"ok": True})
        return super().handle(name, a)

    def map_doc(self):
        return {**super().map_doc(), "project": {"orkmaster": {"race": "peon", "tier": "crown"}}}


def open_route(gui, host, width):
    server, browser = gui
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand-card[data-kind]", timeout=WAIT_MS)
    return pg, log


def lift(pg, kind="route"):
    pg.locator(f'.hand-card[data-kind="{kind}"]').click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def fits(pg):
    narrow.no_sideways(pg)
    box, size = pg.locator(".hand-lifted").bounding_box(), pg.viewport_size
    assert box["x"] >= -1 and box["x"] + box["width"] <= size["width"] + 1 and box["y"] >= -1, "the lifted card lies within the window"
    assert pg.locator(".hand-lifted").evaluate("e => e.scrollWidth <= e.clientWidth + 1"), "nothing sideways inside it"


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_route_cards_face_is_the_goals_element_and_name_the_route_sign_the_orkmasters_head_and_the_costs_gem(gui, width):
    host = RouteHost()
    pg, log = open_route(gui, host, width)
    try:
        card = pg.locator('.hand-card[data-kind="route"]')
        assert card.get_attribute("data-goal") == "fresh" and pg.locator('.hand-lane[data-lane="0"] .hand-card[data-kind="route"]').count() == 1, "under the first lane: it is the whole goal's"
        assert "el-ice" in card.get_attribute("class") and card.locator(".hand-card__head .ork-elem.ice").count() == 1
        assert card.locator(".hand-card__name").inner_text() == "A team-vs-team round"
        assert card.locator(".hand-card__window .ork-sign.after").count() == 1, "the route's sign in its window"
        img = card.locator(".hand-card__asker img")
        assert img.count() == 1 and "/races/peon-crown" in img.get_attribute("src"), "the Orkmaster's crowned head over its corner"
        assert card.locator(".hand-card__gem .ork-gem").inner_text() == "3–9%", "the gem of its cost in the label row"
        if width == "wide":
            pg.mouse.move(640, 300)
            pg.wait_for_timeout(700)
        shot(pg, f"{width}-route-face")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_lifted_route_card_has_the_heads_the_words_the_cost_its_place_and_talk(gui, width):
    host = RouteHost()
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        assert lifted.locator(".hand-route__step:not(.is-add)").count() == 3 and lifted.locator(".hand-route__step .ork-race__head").count() == 3, "the leaders' heads in order"
        assert lifted.locator(".hand-route__off").count() == 3, "a × at each"
        assert lifted.locator(".hand-way__words").inner_text() == "Product, then Design, then Tech"
        assert lifted.locator(".hand-way__cost .hand-spend__words").inner_text() == "about 6 calls, about 3–9% of Claude's week" and lifted.locator(".hand-way__cost .ork-gem.share").inner_text() == "3–9%"
        assert pg.locator(".hand-lifted .hand-spend:visible").count() == 1, "the cost is said once"
        assert lifted.locator(".hand-way__place").inner_text() == "3rd in line"
        assert lifted.get_by_role("button", name="Talk").count() == 1 and lifted.get_by_role("button", name="Later, by itself").count() == 0, "Later only when the limits run low"
        assert lifted.get_by_role("button", name="Put it back").count() == 1
        assert lifted.locator("img[src*='/races/peon-crown']").count() >= 1
        fits(pg)
        shot(pg, f"{width}-route-lifted")
        lifted.get_by_role("button", name="Talk").click()
        assert _sent(pg, host, ("ideas.talk", {"idea": "fresh"}))
        pg.locator(".hand-lifted").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_an_edit_sends_route_set_and_says_the_cost_again_from_the_answer_and_the_plus_never_offers_release(gui, width):
    host = RouteHost()
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        lifted.get_by_role("button", name="Take Design off the route").click()
        assert _calls(pg, host, "ideas.route_set")[-1] == {"idea": "fresh", "route": ["product", "tech"]}
        pg.wait_for_function("() => document.querySelector('.hand-way__words')?.textContent === 'Product, then Tech'", timeout=WAIT_MS)
        assert lifted.locator(".hand-way__cost .hand-spend__words").inner_text() == "about 4 calls, about 2–6% of Claude's week", "the cost said again"
        assert pg.locator(".hand-lifted").count() == 1 and lifted.locator(".hand-route__step:not(.is-add)").count() == 2, "the card stays lifted"
        lifted.get_by_role("button", name="Take Product off the route").click()
        pg.wait_for_function("() => document.querySelector('.hand-way__words')?.textContent === 'Tech'", timeout=WAIT_MS)
        assert lifted.get_by_role("button", name="Take Tech off the route").is_disabled(), "a route needs a party"
        lifted.get_by_role("button", name="Add a party to the route").click()
        menu = lifted.locator(".hand-route__menu [role=menuitem]")
        assert [m.get_attribute("data-party") for m in menu.all()] == ["product", "design"], "the offered party first (it touches its map), Release never"
        assert menu.first.inner_text().endswith("touches its map") and "touches" not in menu.last.inner_text()
        fits(pg)
        shot(pg, f"{width}-route-plus")
        menu.last.click()
        assert _calls(pg, host, "ideas.route_set", at_least=3)[-1] == {"idea": "fresh", "route": ["tech", "design"]}
        pg.wait_for_function("() => document.querySelector('.hand-way__words')?.textContent === 'Tech, then Design'", timeout=WAIT_MS)
        assert lifted.locator(".hand-route__menu").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_head_pressed_opens_its_popover_and_esc_closes_it_before_the_card(gui, width):
    host = RouteHost()
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        lifted.get_by_role("button", name="Tech’s leader").click()
        pop = lifted.locator(".table-seatpop")
        pop.wait_for(timeout=WAIT_MS)
        assert pop.get_attribute("data-seat") == "tech-lead" and pop.bounding_box()["x"] >= lifted.bounding_box()["x"] - 1, "the table's seat popover, in the card"
        assert _calls(pg, host, "ideas.route_set", ms=300) == [], "a press on a head takes no party off"
        fits(pg)
        shot(pg, f"{width}-route-popover")
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-lifted .table-seatpop')", timeout=WAIT_MS)
        assert pg.locator(".hand-lifted").count() == 1, "the first Esc closes the popover only"
        lifted.get_by_role("button", name="Tech’s leader").click()                       # pressed again, it opens again; a third press closes
        pop.wait_for(timeout=WAIT_MS)
        lifted.get_by_role("button", name="Tech’s leader").click()
        pg.wait_for_function("() => !document.querySelector('.hand-lifted .table-seatpop')", timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_later_by_itself_is_offered_only_when_the_limits_run_low(gui, width):
    host = RouteHost(low=True)
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        later = lifted.get_by_role("button", name="Later, by itself")
        assert later.count() == 1 and lifted.get_by_role("button", name="Talk").count() == 1
        fits(pg)
        shot(pg, f"{width}-route-low")
        later.click()
        assert _sent(pg, host, ("ideas.route_later", {"idea": "fresh"}))
        pg.locator(".hand-lifted").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_bug_alone_is_talk_to_find_the_cause_or_start_with_the_long_way_beside_it(gui, width):
    host = RouteHost("cause")
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        assert lifted.locator(".hand-way__words").inner_text() == "Tech alone: finding the cause"
        assert lifted.get_by_role("button", name="Talk").count() == 1 and lifted.get_by_role("button", name="Start").count() == 0 and lifted.get_by_role("button", name="The long way").count() == 0
        assert lifted.locator(".hand-way__place").inner_text() == "3rd in line"
        fits(pg)
        shot(pg, f"{width}-bug-cause")
        lifted.get_by_role("button", name="Talk").click()
        assert _sent(pg, host, ("ideas.talk", {"idea": "fresh"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)

    host = RouteHost("report")
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        assert lifted.locator(".hand-way__words").inner_text() == "Tech alone: the report has a failing test"
        assert lifted.get_by_role("button", name="Talk", exact=True).count() == 0 and lifted.get_by_role("button", name="Start", exact=True).count() == 1
        long = lifted.get_by_role("button", name="The long way")
        assert long.count() == 1 and "quiet" in long.get_attribute("class"), "a quiet link"
        fits(pg)
        shot(pg, f"{width}-bug-report")
        long.click()
        assert _sent(pg, host, ("ideas.talk", {"idea": "fresh"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)

    host = RouteHost("report")
    pg, log = open_route(gui, host, width)
    try:
        lift(pg).get_by_role("button", name="Start", exact=True).click()
        assert _sent(pg, host, ("ideas.route_start", {"idea": "fresh"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_start_card_says_the_new_cost_with_the_old_one_struck_and_starts(gui, width):
    host = RouteHost("start")
    pg, log = open_route(gui, host, width)
    try:
        card = pg.locator('.hand-card[data-kind="start"]')
        assert card.locator(".hand-card__window .ork-sign.after").count() == 1 and "/races/peon-crown" in card.locator(".hand-card__asker img").get_attribute("src")
        assert card.locator(".hand-card__gem .ork-gem").inner_text() == "4–12%", "the new cost's gem"
        lifted = lift(pg, "start")
        now, old = lifted.locator(".hand-way__cost").first, lifted.locator("del .hand-spend")
        assert now.locator(".hand-spend__words").inner_text() == "about 8 calls, about 4–12% of Claude's week"
        assert old.locator(".hand-spend__words").inner_text() == "about 6 calls, about 3–9% of Claude's week"
        assert old.locator(".hand-spend__words").evaluate("e => getComputedStyle(e).textDecorationLine") == "line-through", "the old cost struck"
        assert now.locator(".hand-spend__words").evaluate("e => getComputedStyle(e).textDecorationLine") == "none"
        assert pg.locator(".hand-lifted .hand-spend:visible").count() == 2
        fits(pg)
        shot(pg, f"{width}-start-card")
        lifted.get_by_role("button", name="Start").click()
        assert _sent(pg, host, ("ideas.start", {"idea": "fresh"}))
        pg.locator(".hand-lifted").wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
@pytest.mark.parametrize("scenario,words", [("tidy", "Tech alone: a small clean-up"), ("balance", "Tech alone: a small change to the numbers")])
def test_a_short_goal_that_is_no_bug_says_its_own_line_and_has_talk_alone(gui, width, scenario, words):
    host = RouteHost(scenario)
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        assert lifted.locator(".hand-way__words").inner_text() == words
        assert lifted.get_by_role("button", name="Talk", exact=True).count() == 1 and lifted.get_by_role("button", name="Start", exact=True).count() == 0 and lifted.get_by_role("button", name="The long way").count() == 0
        assert "cause" not in lifted.inner_text() and "failing test" not in lifted.inner_text(), "the bug's words are the bug's"
        fits(pg)
        shot(pg, f"{width}-short-{scenario}")
        lifted.get_by_role("button", name="Talk", exact=True).click()
        assert _sent(pg, host, ("ideas.talk", {"idea": "fresh"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_route_row_of_a_host_that_sends_no_type_is_read_as_before(gui, width):
    host = RouteHost("legacy")
    pg, log = open_route(gui, host, width)
    try:
        assert lift(pg).locator(".hand-way__words").inner_text() == "Tech alone: finding the cause"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_cards_kind_is_said_in_plain_words(gui, width):
    for scenario, word in (("route", "Route"), ("start", "Start")):
        host = RouteHost(scenario)
        pg, log = open_route(gui, host, width)
        try:
            lifted = lift(pg, scenario)
            assert " ".join(lifted.locator(".hand-lifted__kind").text_content().split()) == word and lifted.get_attribute("aria-label").startswith(f"Lifted: {word}:")
        finally:
            pg.close()
        assert not log, "\n".join(log)
