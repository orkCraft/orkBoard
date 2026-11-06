"""Spec 155 part B (docs/specs/155-one-pick-and-the-release-column.md, decisions §260.1-3, §260.5-6, §261.4), in a real browser against a stub host: one goal picked at most, from the Orkmaster's column (a face-down card too) or by a hand's card lifted; the pick put
away by the same card again, Esc, an empty press of the column and the browser's back; the pick in the address (`#goal=<slug>`, written and read by frame/state.js alone); no × in the pane's title; the tabs of the parties the picked goal's route does not pass grey, pressed
they put the pick away and open that tab; a pick whose route lacks the open tab opens the Orkmaster's; at 390 px a file over a pick closes on the first back, the pick on the second."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, back, open_column, ripe  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, call, node, open_hand, sig, task  # noqa: E402

pytestmark = pytest.mark.browser

STATE = "frame/state.js"


def picked(pg):
    return sig(pg, STATE, "picked")


def hash_of(pg):
    return pg.evaluate("() => location.hash")


def press(pg, slug):
    """A press on a goal's card; the backs of the hand overlap, so one is pressed at its left edge."""
    card = pg.locator(f'.col-card[data-goal="{slug}"]')
    if "col-card--fan" in card.get_attribute("class"):
        card.click(position={"x": 6, "y": 40})
    else:
        card.click()


def wait_picked(pg, slug):
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)


class RoutedHost(ColumnHost):
    """The column's goals, and two at work with routes: `both` to Tech and Design, `techonly` to Tech alone."""

    def __init__(self):
        super().__init__()
        route = lambda *parties: [{"party": p, "leader": f"{p}-lead", "head": {"race": "orc", "tier": "elder"}} for p in parties]      # noqa: E731
        self.nodes = [n for n in self.nodes if n["slug"] not in ("music", "held", "late", "timer", "scoring")] + [
            node("both", "tech", "Tech and Design goal", "table", state="working", element="ice", stage="implementation", route=route("tech", "design"), tasks=[task("b1", "Do it", "running")]),
            node("techonly", "tech", "Tech's own goal", "table", state="working", element="dust", stage="implementation", route=route("tech"), tasks=[task("c1", "Do it", "running")]),
        ]
        self.nodes[-1].update(state="ready", agreed=True, stage="planning", tasks=[], back=back(ripe=ripe(120)))      # Tech's alone waits in To review, the front of the deck


def test_a_face_down_card_is_picked_by_a_press_and_the_address_holds_it_and_the_same_card_again_puts_it_away(gui):
    pg, host, log = open_column(gui)
    try:
        card = pg.locator('.col-card[data-goal="raw3"]')
        press(pg, "raw3")
        wait_picked(pg, "raw3")
        assert hash_of(pg) == "#goal=raw3" and "ork-picked" in card.get_attribute("class").split() and card.get_attribute("aria-pressed") == "true"
        assert pg.locator(".col-card.ork-picked").count() == 1, "one pick at most"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card.ork-picked')).borderTopColor") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-ink)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }"), "its edge is in the ink"
        assert pg.locator(".col-card.is-dim").count() == 0, "nothing else is dimmed"
        press(pg, "raw2")
        wait_picked(pg, "raw2")
        assert hash_of(pg) == "#goal=raw2" and pg.locator(".col-card.ork-picked").count() == 1, "another card: the pick moves, still one"
        press(pg, "raw2")
        wait_picked(pg, "")
        pg.wait_for_function("() => location.hash === ''", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_esc_an_empty_press_of_the_column_and_the_browsers_back_each_put_the_pick_away(gui):
    pg, host, log = open_column(gui)
    try:
        press(pg, "raw3")
        wait_picked(pg, "raw3")
        pg.keyboard.press("Escape")                                                    # the card's choices beside the column take the first
        if picked(pg):
            pg.keyboard.press("Escape")
        wait_picked(pg, "")
        pg.wait_for_function("() => location.hash === ''", timeout=WAIT_MS)
        press(pg, "timer")
        wait_picked(pg, "timer")
        pg.locator('.col-sec[data-pile="review"] .col-plab').click(position={"x": 140, "y": 3})
        wait_picked(pg, "")
        press(pg, "music")
        wait_picked(pg, "music")
        assert hash_of(pg) == "#goal=music"
        pg.go_back()
        wait_picked(pg, "")
        assert hash_of(pg) == ""
        pg.go_forward()
        wait_picked(pg, "music")
        assert pg.locator(".col-card[data-goal=music].ork-picked").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_address_is_read_on_load_and_a_goal_the_snapshot_has_not_reads_as_none(gui):
    server, browser = gui
    for slug, want in (("raw2", "raw2"), ("nowhere", "")):
        pg = narrow.page(browser, "wide")
        host = ColumnHost()
        pg.route_web_socket("**/ws*", host.on_socket)
        pg.goto(f"{server.url}#goal={slug}")
        pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
        try:
            wait_picked(pg, want)
            pg.wait_for_function("(h) => location.hash === h", arg=f"#goal={want}" if want else "", timeout=WAIT_MS)
        finally:
            pg.close()


def test_the_pane_title_has_no_cross_to_leave_the_pick(gui):
    pg, host, log = open_column(gui, host=RoutedHost())
    try:
        press(pg, "both")
        wait_picked(pg, "both")
        assert pg.locator("[data-unpick], .table-title__unpick").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_tabs_the_picked_goals_route_does_not_pass_are_grey_and_pressed_they_put_the_pick_away_and_open_that_tab(gui):
    pg, host, log = open_column(gui, host=RoutedHost())
    try:
        tab = lambda slug: pg.locator(f'.table-tab[data-tab="{slug}"]')      # noqa: E731
        assert pg.locator(".table-tab.is-off").count() == 0, "nothing picked: no tab is grey"
        press(pg, "both")
        wait_picked(pg, "both")
        assert tab("tech").get_attribute("class").count("is-off") == 0 and tab("design").get_attribute("class").count("is-off") == 0
        assert "is-off" in tab("product").get_attribute("class").split()
        want = f"Product {lexicon.term('tab_off_is')}. {lexicon.term('tab_off_press')} Product's table."
        assert want == "Product is not on this goal. Press to leave it and look at Product's table." and tab("product").get_attribute("title") == want
        assert pg.locator('.col-head__tab').get_attribute("class").count("is-off") == 0, "the Orkmaster's tab is never grey"
        assert pg.locator(".table-tab__dot").count() == 0, "grey says it: the dot of the route is gone"
        tab("product").click()
        wait_picked(pg, "")
        assert tab("product").get_attribute("aria-selected") == "true" and pg.locator(".table-tab.is-off").count() == 0
        press(pg, "techonly")
        wait_picked(pg, "techonly")
        assert "is-off" in tab("design").get_attribute("class").split() and "is-off" in tab("product").get_attribute("class").split()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_pick_from_a_tab_the_goals_route_lacks_opens_the_orkmasters_tab(gui):
    pg, host, log = open_column(gui, host=RoutedHost())
    try:
        pg.locator('.table-tab[data-tab="design"]').click()
        assert sig(pg, STATE, "tab") == "design"
        press(pg, "both")
        wait_picked(pg, "both")
        assert sig(pg, STATE, "tab") == "design", "its route has Design: the tab stays"
        pg.keyboard.press("Escape")
        pg.keyboard.press("Escape")
        wait_picked(pg, "")
        press(pg, "techonly")
        wait_picked(pg, "techonly")
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.tab.value === 'orkmaster')", timeout=WAIT_MS)
        assert pg.locator(".col-head__tab").get_attribute("aria-selected") == "true"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_hands_card_lifted_picks_its_goal_and_its_lowering_leaves_the_pick_and_the_goals_cards_wear_the_ink_edge(gui):
    pg, host, log = open_hand(gui, host=HandHost(), width="wide")
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.locator('.table-tab[data-tab="design"]').click()
        stack = pg.locator('.hand-stack[data-goal="timer"]')
        stack.locator(".hand-card").first.click()
        wait_picked(pg, "timer")
        assert hash_of(pg) == "#goal=timer"
        assert sig(pg, STATE, "tab") == "orkmaster", "Design is not on its route: the Orkmaster's tab"
        card = stack.locator(".hand-card").first
        assert "ork-picked" in card.get_attribute("class").split(), "the picked goal's cards in the hand wear the ink edge"
        assert card.evaluate("e => getComputedStyle(e).borderTopColor") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-ink)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }")
        stack.locator(".hand-card").first.click()                                       # lowered
        assert picked(pg) == "timer", "its lowering leaves the pick"
        assert pg.locator(".hand-stack.is-picked").count() >= 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_at_390_px_a_file_over_a_pick_closes_on_the_first_back_and_the_pick_on_the_second(gui):
    pg, host, log = open_hand(gui, host=ColumnHost(), width="narrow")
    try:
        pg.locator(".hand").first.wait_for(timeout=WAIT_MS)
        call(pg, STATE, "pick", "raw1")
        wait_picked(pg, "raw1")
        assert hash_of(pg) == "#goal=raw1"
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openOver('file', {path: 'README.md'}, {title: 'Board', key: ''}, 'README.md'))")
        pg.locator(".table-over").wait_for(timeout=WAIT_MS)
        pg.go_back()
        pg.wait_for_function("() => !document.querySelector('.table-over')", timeout=WAIT_MS)
        assert picked(pg) == "raw1" and hash_of(pg) == "#goal=raw1", "the first back closes the file only"
        pg.go_back()
        wait_picked(pg, "")
        assert hash_of(pg) == "", "the second back puts the pick away"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_grey_tabs_words_are_the_lexicons(gui):
    pg, host, log = open_column(gui)
    try:
        got = pg.evaluate("() => import('/static/js/table/tabs.js').then((m) => ({OFF_IS: m.OFF_IS, OFF_PRESS: m.OFF_PRESS}))")
        assert got == {"OFF_IS": lexicon.term("tab_off_is"), "OFF_PRESS": lexicon.term("tab_off_press")}
    finally:
        pg.close()
    assert not log, "\n".join(log)
