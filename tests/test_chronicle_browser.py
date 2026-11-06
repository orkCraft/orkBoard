"""The past through the open tab (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.2, decisions §254.7; docs/specs/134-release-keeps-the-chronicle.md B, decisions §238.3–§238.4; mockup docs/mockups/table-edge/ section 5), in a real
browser at the wide width against a stub host (the road's `RoadHost`, its ring with the lich at six, with the `ideas.chronicle*` commands answered as the host answers them): the lich's line in the edge says whose past it holds (*Design's past ›*, *The project's
past ›*) and changes with the tab; the lich pressed opens the past over the pane with `party` the open tab's (none on the Orkmaster's), its title both axes (*The past · through Design · every version*, *· v0.3*), its search *Search Design's past…*;
at its left a deck a version, *Unreleased* on top: none picked, every version dealt newest first with each card's version at its bottom right; a deck picked deals its own; a search dims the decks with no find and lights the cards found; a goal lifted
as it was with **Show on Design's table** (that tab, the goal picked); a decision with its *Changes* and *changed by* walked; ← back to the tab's table. Release's lens has no line *Earlier* any more. Screenshots to ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, call, open_hand, sig  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser


def goal(idea, title, day, decision=0, element="meadow"):
    return {"idea": idea, "title": title, "party": "design", "element": element, "hue": "", "at": f"{day}T10:00:00", "day": day, "commit": "a" * 40, "decision": decision}


UNRELEASED = {"goals": [goal("words", "Words on the sign-in screen", "2026-11-04", 0, "ice")], "decisions": []}
NEW = {"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02", "open": True,
       "goals": [goal("phones", "The timer resets after a reconnect", "2026-11-01", 238), goal("seat", "Reconnect keeps your seat", "2026-10-31", 0, "dust")],
       "decisions": [{"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "goal": ""}]}
OLD = {"id": "v:0.3", "kind": "tag", "name": "v0.3", "day": "2026-10-28", "open": False}
OLD_FULL = {**OLD, "open": True, "goals": [goal("lobby", "A lobby with a chat", "2026-10-27", 0, "dust")], "decisions": [{"number": 212, "title": "The server owns every clock", "day": "2026-10-20", "changes": [], "changed_by": [], "goal": ""}]}
DECISIONS = {
    238: {"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "changes": [{"n": 206, "point": 3, "title": "The Orkmaster's column"}], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}],
          "entry": "## 238. The past lives past the portal\n\nWhy: the owner asked.", "goal": "phones"},
    206: {"number": 206, "title": "The Orkmaster's column", "day": "2026-10-01", "changes": [], "changed_by": [{"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "points": [3]}], "entry": "## 206. The column", "goal": ""},
    240: {"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "entry": "## 240. A verdict", "goal": ""},
}


class PastHost(RoadHost):
    def __init__(self):
        super().__init__(bare=True)

    def handle(self, name, a):
        if not name.startswith("ideas.chronicle"):
            return super().handle(name, a)
        self.log.append((name, a))
        if name == "ideas.chronicle_last":
            return {"decisions": []}
        if name == "ideas.chronicle":
            return {"kind": "tag", "earlier": {"kind": "tag", "name": "v0.4", "day": "2026-11-02"}, "chapters": [NEW, OLD], "unreleased": UNRELEASED}
        if name == "ideas.chronicle_chapter":
            return OLD_FULL
        if name == "ideas.chronicle_find":
            return {"query": a["query"], "found": 1, "more": 0, "unreleased": None, "chapters": [{"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02",
                    "goals": [{"idea": "phones", "title": "The timer resets after a reconnect", "day": "2026-11-01", "element": "meadow", "hue": "", "decision": 238, "in": ["title", "spec"]}], "decisions": []}]}
        if name == "ideas.chronicle_goal":
            return {**NEW["goals"][0], "spec": {"asked": "A timer that resets.", "gist": "Ninety seconds a round.", "sections": [{"party": "design", "title": "Design", "parts": {"Will": "Show the timer big."}}]},
                    "decision": DECISIONS[238], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}], "how_now": [{"capability": "timer", "title": "The round timer"}],
                    "quality": {"findings": [{"id": "f1", "source": "lens", "what": "The bar is hard to see", "found": "", "level": "work"}]}}
        if name == "ideas.chronicle_decision":
            if a["number"] not in DECISIONS:
                return {"error": "That decision is not in the log"}
            return DECISIONS[a["number"]]
        raise AssertionError(name)


def asked(host, name):
    return [a for n, a in host.log if n == name]


def open_past(gui, tab="design"):
    pg, host, log = open_hand(gui, host=PastHost())
    pg.locator(".ork-portal-ring__before").wait_for(timeout=WAIT_MS)
    if tab != "orkmaster":
        call(pg, "frame/state.js", "openTab", tab)
    pg.locator(".portal__past").wait_for(timeout=WAIT_MS)
    return pg, host, log


def lich(pg):
    pg.locator(".ork-portal-ring__before").click()
    pg.locator('.table-over[data-kind="chronicle"] .chr-deal').wait_for(timeout=WAIT_MS)


def title(pg):
    return pg.locator("[data-title]").text_content().strip()


def finish(pg, log):
    pg.close()
    assert not log, "\n".join(log)


def test_the_lichs_line_says_whose_past_and_the_lich_opens_it_through_the_open_tab_and_back_returns_to_its_table(gui):
    pg, host, log = open_past(gui)
    assert pg.locator(".portal__past").inner_text() == "Design's past ›"
    lich(pg)
    assert title(pg) == "Design's table · The past · through Design · every version"
    assert asked(host, "ideas.chronicle") == [{"party": "design"}]
    assert pg.get_by_role("searchbox", name="Search Design's past…").get_attribute("placeholder") == "Search Design's past…"
    shot(pg, "past-design.png")
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"chronicle\"]')", timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "tab") == "design", "back to the tab's table"
    call(pg, "frame/state.js", "openTab", "orkmaster")
    pg.wait_for_function("() => document.querySelector('.portal__past')?.textContent === \"The project's past ›\"", timeout=WAIT_MS)
    pg.locator(".portal__past").click()                                                                    # the line opens it too
    pg.locator('.table-over[data-kind="chronicle"] .chr-deal').wait_for(timeout=WAIT_MS)
    assert title(pg).endswith("The past · through the Orkmaster · every version") and asked(host, "ideas.chronicle")[-1] == {}
    assert pg.get_by_role("searchbox").get_attribute("placeholder") == "Search the past…"
    finish(pg, log)


def test_a_deck_a_version_unreleased_on_top_none_picked_every_version_and_a_deck_picked_deals_its_own(gui):
    pg, host, log = open_past(gui)
    lich(pg)
    decks = pg.locator(".chr-deck")
    assert [d.get_attribute("data-deck") for d in decks.all()] == ["unreleased", "v:0.4", "v:0.3"]
    assert decks.first.locator(".chr-deck__nm").inner_text().lower() == "unreleased"
    pg.locator('.chr-card-wrap[data-decision-row="212"]').wait_for(timeout=WAIT_MS)                       # every version: the older chapter is read for the deal
    assert asked(host, "ideas.chronicle_chapter") == [{"id": "v:0.3", "party": "design"}]
    cards = pg.locator(".chr-deal > .chr-card-wrap")
    assert [c.get_attribute("data-goal") or c.get_attribute("data-decision-row") for c in cards.all()] == ["words", "phones", "seat", "240", "lobby", "212"], "newest first"
    assert [c.locator('[data-much="version"]').inner_text() for c in cards.all()] == ["Unreleased", "v0.4", "v0.4", "v0.4", "v0.3", "v0.3"], "each card's version at its bottom right"
    assert pg.locator('.chr-card-wrap[data-goal="phones"] .chr-card__dec').inner_text() == "§238", "the decision a goal carries beside its card"
    pg.locator('.chr-deck[data-deck="v:0.3"]').click()
    pg.wait_for_function("() => document.querySelectorAll('.chr-deal > .chr-card-wrap').length === 2", timeout=WAIT_MS)
    assert pg.locator('.chr-deck[data-deck="v:0.3"]').get_attribute("aria-pressed") == "true"
    pg.wait_for_function("() => document.querySelector('[data-title]').textContent.trim().endsWith('· v0.3')", timeout=WAIT_MS)
    assert title(pg) == "Design's table · The past · through Design · v0.3"
    shot(pg, "past-design-v03.png")
    pg.locator('.chr-deck[data-deck="v:0.3"]').click()                                                     # pressed again: every version
    pg.wait_for_function("() => document.querySelectorAll('.chr-deal > .chr-card-wrap').length === 6", timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('[data-title]').textContent.trim().endsWith('every version')", timeout=WAIT_MS)
    finish(pg, log)


def test_the_search_dims_the_decks_with_no_find_and_lights_the_cards_found(gui):
    pg, host, log = open_past(gui)
    lich(pg)
    pg.get_by_role("searchbox", name="Search Design's past…").fill("timer")
    pg.locator(".chr-deal[data-finds]").wait_for(timeout=WAIT_MS)
    assert [d.get_attribute("data-deck") for d in pg.locator(".chr-deck.is-dim").all()] == ["unreleased", "v:0.3"]
    found = pg.locator(".chr-deal > .chr-card-wrap")
    assert found.count() == 1 and "is-lit" in found.get_attribute("class") and "in its name, its spec" in found.inner_text()
    assert asked(host, "ideas.chronicle_find") == [{"query": "timer", "party": "design"}]
    pg.get_by_role("searchbox").fill("")
    pg.locator(".chr-deal[data-deck]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-deck.is-dim").count() == 0
    finish(pg, log)


def test_a_goal_lifted_is_as_it_was_and_show_on_designs_table_opens_that_table_with_it_picked(gui):
    pg, host, log = open_past(gui)
    lich(pg)
    pg.locator('.chr-card-wrap[data-goal="phones"] .chr-card').click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    text = pg.locator(".chr-goal").inner_text()
    assert "The timer resets after a reconnect" in text and "A timer that resets." in text and "Show the timer big." in text
    assert pg.locator(".chr-changed").inner_text().startswith("changed by §241")
    assert pg.locator(".chr-decision .chr-link").inner_text() == "§238 The past lives past the portal" and "The bar is hard to see" in pg.locator(".chr-quality").inner_text()
    shot(pg, "past-goal.png")
    pg.get_by_role("button", name="The past", exact=True).click()                                                      # back to the deal, the deck as it was
    pg.locator(".chr-deal").wait_for(timeout=WAIT_MS)
    pg.locator('.chr-card-wrap[data-goal="phones"] .chr-card').click()
    pg.get_by_role("button", name="Show on Design's table").click()
    pg.wait_for_function("() => !document.querySelector('.table-over[data-kind=\"chronicle\"]')", timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "picked") == "phones" and sig(pg, "frame/state.js", "tab") == "orkmaster", "Design's route does not pass the goal (spec 155 B.5): the pick opens the Orkmaster's tab"
    finish(pg, log)


def test_a_decision_opens_its_entry_and_its_links_are_walked_and_one_gone_is_said_in_words(gui):
    pg, host, log = open_past(gui)
    lich(pg)
    pg.locator('.chr-card-wrap[data-goal="phones"] .chr-card__dec').click()
    page = pg.locator('.chr-decision-page[data-decision="238"]')
    page.wait_for(timeout=WAIT_MS)
    assert "Why: the owner asked." in page.locator(".chr-entry").inner_text()
    assert page.locator('[data-links="Changes"] .chr-link').inner_text() == "§206.3 The Orkmaster's column"
    assert page.locator('[data-links="Changed by"] .chr-link').inner_text() == "§241.2 A later word"
    page.get_by_role("button", name="The goal it came from").click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="The past", exact=True).click()
    pg.locator('.chr-card-wrap[data-decision-row="240"] .chr-card').click()                                 # a decision of no goal
    pg.locator('.chr-decision-page[data-decision="240"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-decision-page").get_by_role("button", name="The goal it came from").count() == 0
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 999 }))")
    pg.locator(".chr-err").first.wait_for(timeout=WAIT_MS)
    assert "not in the log" in pg.locator(".chr-err").first.inner_text()
    finish(pg, log)


def test_a_decision_named_to_be_lit_deals_its_deck_with_its_card_lit_and_releases_lens_has_no_earlier_line(gui):
    pg, host, log = open_past(gui)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ lit: 212 }))")
    pg.wait_for_function("() => document.querySelector('.chr-deck[data-deck=\"v:0.3\"]')?.getAttribute('aria-pressed') === 'true'", timeout=WAIT_MS)
    assert pg.locator(".chr-card-wrap.is-lit").get_attribute("data-decision-row") == "212"
    pg.wait_for_function("() => document.querySelector('[data-title]').textContent.trim().endsWith('· v0.3')", timeout=WAIT_MS)
    assert pg.locator(".mp-earlier").count() == 0 and asked(host, "ideas.chronicle_line") == []
    finish(pg, log)
