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


