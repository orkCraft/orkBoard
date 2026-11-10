"""Spec 168 G3 (docs/specs/168-the-window-played-as-a-card-games-table.md; decisions §283.16.14–15, §283.28, §285.3): the book opens the history over the pane, in a real browser at 1366 × 768 against a stub host (`ideas.history` and `ideas.chronicle_find` answered
as the host answers them). A grid of goal cards that scrolls, a row a day, a day's many cards lying across each other; the cards are the small face-up card, 56 × 78 (a row of the pane holds about a dozen side by side at this width, a cascade past them); dated by
*agreed* (the default), *done* or *in main*, a switch in the header, a goal without the chosen day in the last row; a version's plate on its day; a search lights the cards found and dims the rest; through the open tab (a leader's tab the goals its party worked on);
a card pressed picks the goal and the history is put away; and the discard holds no past deck. Pictures to the scratchpad when ORKBOARD_G3_SHOTS is set."""
from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_chronicle_browser import PastHost, asked  # noqa: E402
from tests.test_hand_desktop_browser import call, open_hand, sig  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = os.environ.get("ORKBOARD_G3_SHOTS", "")


def g(idea, title, party, agreed="", done="", main="", element="meadow", gist=""):
    return {"idea": idea, "title": title, "gist": gist or title, "party": party, "element": element, "hue": "", "decision": 0, "dates": {"agreed": agreed, "done": done, "main": main}}


GOALS = [
    g("seat", "Reconnect keeps your seat", "design", "2026-10-28", "2026-10-30", "2026-11-02", "dust", gist="Hold a seat for a minute after a drop."),
    g("lobby", "A lobby with a chat", "tech", "2026-10-28", "2026-11-01", "2026-11-03"),
    g("words", "Words on the sign-in screen", "design", "2026-10-29", "", "2026-11-04", "ice"),
    g("lamp", "The lamp's chain", "tech", "", "2026-11-01", "2026-11-04"),
    *[g(f"batch-{i}", f"Batch goal {i}", "tech" if i % 2 else "design", "2026-10-30", "2026-11-02", "2026-11-05", "meadow") for i in range(1, 21)],     # twenty on one day
    *[g(f"old-{i}", f"Older goal {i}", "design", f"2026-10-{i:02d}", f"2026-10-{i:02d}", f"2026-10-{i + 1:02d}", "dust") for i in range(1, 25)],       # a row a day, to scroll
]
VERSIONS = [{"id": "v:v0.2", "name": "v0.2", "day": "2026-10-29"}, {"id": "v:v0.1", "name": "v0.1", "day": "2026-10-10"}]


class HistoryHost(PastHost):
    def handle(self, name, a):
        if name == "ideas.history":
            self.log.append((name, a))
            mine = [x for x in GOALS if not a.get("party") or x["party"] == a["party"]]
            return {"kind": "tag", "versions": VERSIONS, "goals": mine}
        if name == "ideas.chronicle_find":
            self.log.append((name, a))
            want = a["query"].lower().split()
            hits = [x for x in GOALS if (not a.get("party") or x["party"] == a["party"]) and all(w in (x["title"] + " " + x["gist"]).lower() for w in want)]
            return {"query": a["query"], "found": len(hits), "more": 0, "chapters": [{"id": "v:v0.2", "kind": "tag", "name": "v0.2", "day": "2026-10-29", "goals": [{"idea": x["idea"], "title": x["title"], "in": ["title"]} for x in hits], "decisions": []}] if hits else [], "unreleased": None}
        return super().handle(name, a)


def open_history(gui, tab="orkmaster"):
    pg, host, log = open_hand(gui, host=HistoryHost())
    pg.set_viewport_size({"width": 1366, "height": 768})
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    if tab != "orkmaster":
        call(pg, "frame/state.js", "openTab", tab)
    pg.locator("[data-book]").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    pg.locator("[data-book]").click()
    pg.locator(".hist-card").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def finish(pg, log):
    pg.close()
    assert not log, "\n".join(log)


def shot(pg, name):
    if SHOTS:
        pg.screenshot(path=os.path.join(SHOTS, f"g3-{name}.png"))


def row(pg, day):
    return pg.locator(f'.hist-row[data-day="{day}"]')


def ids(pg, day):
    return [c.get_attribute("data-goal") for c in row(pg, day).locator(".hist-card [data-goal]").all()]


def test_the_grid_is_a_row_a_day_newest_first_with_a_versions_plate_on_its_day_the_cards_56_by_78_and_it_scrolls(gui):
    pg, host, log = open_history(gui)
    assert asked(host, "ideas.history") == [{}], "through the Orkmaster's tab: the whole project"
    days = [r.get_attribute("data-day") for r in pg.locator(".hist-row").all()]
    assert days[-1] == "none" and days[:-1] == sorted(days[:-1], reverse=True), "newest day first, the goals with no such day last"
    assert days[0] == "2026-10-30" and days.index("2026-10-29") < days.index("2026-10-28") < days.index("2026-10-24"), "newest day first"
    assert len(days) == len(set(days)), "one row a day"
    assert ids(pg, "2026-10-28") == ["seat", "lobby"] and ids(pg, "2026-10-29") == ["words"]
    assert row(pg, "2026-10-29").locator('.hist-plate[data-version="v:v0.2"]').inner_text().lower() == "v0.2", "the version's plate on the day it was released"
    assert row(pg, "2026-10-10").locator('.hist-plate[data-version="v:v0.1"]').count() == 1 and row(pg, "2026-10-10").locator(".hist-card").count() == 1
    boxes = pg.locator(".hist-row[data-day='2026-10-28'] .hist-card .ork-card.sm").evaluate_all("els => els.map((e) => { const b = e.getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height), Math.round(b.x)]; })")
    assert [b[:2] for b in boxes] == [[56, 78], [56, 78]], boxes
    assert boxes[1][2] - boxes[0][2] >= 56, "two cards of a day lie side by side"
    big = pg.locator(".hist-row[data-day='2026-10-30'] .hist-card .ork-card.sm").evaluate_all("els => els.map((e) => { const b = e.getBoundingClientRect(); return [Math.round(b.width), Math.round(b.height), b.x]; })")
    assert len(big) == 20 and all(b[:2] == [56, 78] for b in big), "twenty on one day: still 56 × 78 each"
    assert big[1][2] - big[0][2] < 56 and big[-1][2] > big[0][2], "a day's many lie across each other, the last whole to the right"
    row_ = pg.locator(".hist-row[data-day='2026-10-30'] .hist-cards").bounding_box()
    last = pg.locator(".hist-row[data-day='2026-10-30'] .hist-card").last.bounding_box()
    assert last["x"] + last["width"] <= row_["x"] + row_["width"] + 1, "the cascade stays inside its row"
    box = pg.locator("[data-scroll]").evaluate("e => ({sh: e.scrollHeight, ch: e.clientHeight})")
    assert box["sh"] > box["ch"], "the grid scrolls"
    assert pg.evaluate("() => document.documentElement.scrollWidth <= innerWidth"), "no sideways scroll"
    shot(pg, "orkmaster")
    finish(pg, log)


def test_one_card_size_a_row_of_the_pane_holds_a_dozen_side_by_side_at_1366(gui):
    pg, host, log = open_history(gui)
    pane = pg.locator(".hist-cards").first.bounding_box()
    assert pane["width"] >= 12 * 56, f"the pane's row holds at least a dozen 56-wide cards ({pane['width']} px)"
    finish(pg, log)


def test_the_switch_dates_the_grid_by_agreed_done_or_in_main_and_a_goal_missing_the_day_lies_in_the_last_row(gui):
    pg, host, log = open_history(gui)
    assert pg.locator(".hist-by__b").all_inner_texts() == ["agreed", "done", "in main"] and pg.locator('.hist-by [data-by="agreed"]').get_attribute("aria-pressed") == "true", "agreed is the default"
    assert row(pg, "none").locator('[data-goal="lamp"]').count() == 1 and row(pg, "none").locator(".hist-day__nm").inner_text() == "No date", "the lamp's chain was never agreed in the window: the last row"
    assert pg.locator(".hist-row").last.get_attribute("data-day") == "none"
    pg.locator('.hist-by [data-by="done"]').click()
    row(pg, "2026-11-01").wait_for(timeout=WAIT_MS)
    assert ids(pg, "2026-11-01") == ["lobby", "lamp"] and pg.locator('.hist-by [data-by="done"]').get_attribute("aria-pressed") == "true" and pg.locator('.hist-by [data-by="agreed"]').get_attribute("aria-pressed") == "false"
    assert row(pg, "none").locator('[data-goal="words"]').count() == 1 and row(pg, "none").locator('[data-goal="lamp"]').count() == 0, "now the one without a done day is the last row"
    pg.locator('.hist-by [data-by="main"]').click()
    row(pg, "2026-11-05").wait_for(timeout=WAIT_MS)
    assert ids(pg, "2026-11-04") == ["words", "lamp"] and row(pg, "none").count() == 0, "every goal has its day in main"
    assert pg.locator(".hist-row").first.get_attribute("data-day") == "2026-11-05"
    assert pg.locator(".hist-by").get_attribute("aria-label") == "Dated by"
    shot(pg, "in-main")
    finish(pg, log)


def test_a_search_lights_the_cards_found_and_dims_the_rest(gui):
    pg, host, log = open_history(gui)
    assert pg.locator(".hist-card.is-lit, .hist-card.is-dim").count() == 0, "nothing lit before a search"
    pg.locator(".hist-search").fill("seat")
    pg.wait_for_function("() => document.querySelectorAll('.hist-card.is-lit').length === 1", timeout=WAIT_MS)
    assert asked(host, "ideas.chronicle_find") == [{"query": "seat"}]
    assert pg.locator(".hist-card.is-lit [data-goal]").get_attribute("data-goal") == "seat"
    assert pg.locator(".hist-card.is-dim").count() == pg.locator(".hist-card").count() - 1, "the rest dim"
    pg.wait_for_timeout(400)
    assert pg.locator(".hist-card.is-dim").first.evaluate("e => getComputedStyle(e).opacity") == "0.3" and pg.locator(".hist-card.is-lit").evaluate("e => getComputedStyle(e).opacity") == "1"
    shot(pg, "search")
    pg.locator(".hist-search").fill("")
    pg.wait_for_function("() => document.querySelectorAll('.hist-card.is-dim').length === 0", timeout=WAIT_MS)
    pg.locator(".hist-search").fill("zzzz")
    pg.locator(".hist-scroll .chr-none").first.wait_for(timeout=WAIT_MS)
    assert "Nothing in the history has those words" in pg.locator(".hist-scroll").inner_text() and pg.locator(".hist-card.is-lit").count() == 0
    finish(pg, log)


def test_through_a_leaders_tab_the_history_holds_only_the_goals_its_party_worked_on(gui):
    pg, host, log = open_history(gui, tab="design")
    assert asked(host, "ideas.history") == [{"party": "design"}]
    parties = {c.get_attribute("data-party") for c in pg.locator(".hist-card .sm-dot").all()}
    assert parties == {"design"}, parties
    assert pg.locator(".hist-card [data-goal='lobby']").count() == 0 and pg.locator(".hist-card [data-goal='seat']").count() == 1, "Tech's goal is not on Design's tab"
    assert pg.locator("[data-title]").inner_text().lower().endswith("history · through design")
    pg.locator(".hist-search").fill("batch")
    pg.wait_for_function("() => document.querySelectorAll('.hist-card.is-lit').length > 0", timeout=WAIT_MS)
    assert asked(host, "ideas.chronicle_find")[-1] == {"query": "batch", "party": "design"}
    assert pg.locator(".hist-card.is-lit").count() == 10, "ten of the twenty batch goals are Design's"
    shot(pg, "leader")
    finish(pg, log)


def test_a_card_pressed_puts_the_history_away_and_opens_the_goals_result(gui):
    pg, host, log = open_history(gui)
    pg.locator(".hist-card [data-goal='seat']").click()
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "picked") == "seat", "the goal is picked: the table shows its result"
    pg.locator(".chr-goal, .gv-result, [data-result]").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".ork-book.is-open").count() == 0
    finish(pg, log)


def test_the_discard_holds_no_past_deck_and_the_card_hovered_shows_at_144_by_202(gui):
    pg, host, log = open_history(gui)
    pg.locator("[data-book]").click()                                                                      # shut: the table with the discard
    pg.locator(".table-over[data-kind='history']").wait_for(state="detached", timeout=WAIT_MS)
    pg.locator(".release-lane").wait_for(timeout=WAIT_MS)
    assert pg.locator(".release-lane__past, .release-lane__deck, .release-lane__deal, .release-lane [data-deck], .release-lane [data-version]").count() == 0
    assert asked(host, "ideas.chronicle") == [], "the discard no longer reads the past"
    pg.locator("[data-book]").click()
    pg.locator(".hist-card [data-goal='seat']").hover()
    pg.locator(".pv-host .ork-card, .pv-host [class*=pv]").first.wait_for(timeout=WAIT_MS)
    big = pg.locator(".pv-host .ork-card").first.bounding_box()
    assert (round(big["width"]), round(big["height"])) == (144, 202)
    finish(pg, log)
