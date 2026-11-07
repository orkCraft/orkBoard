"""The past deeper in the discard (docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9; before it the chronicle over the pane, docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.2, decisions §254.7;
docs/specs/134-release-keeps-the-chronicle.md B, decisions §238.3–§238.4), in a real browser at the wide width against a stub host (the road's `RoadHost` with the `ideas.chronicle*` commands answered as the host answers them): under the goals not yet seen,
in Release's lane, *Unreleased* and a deck a version, newest first, through the open tab's eyes (`party` of every `ideas.chronicle*` command: the open tab's, none on the Orkmaster's); a deck pressed deals its cards in the lane, pressed again gathers them
(an older version is read when it is first dealt); a goal's card is picked and the table shows it as it was; a decision's card opens its entry over the pane, its *Changes* and *changed by* walked, a decision gone said in words; a decision newer than a
party's last look is a muted dot on its tab, gone once that tab's lane is scrolled to the past. The pyramid, the lich's line and the chronicle over the pane are gone. Screenshots to ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import RoadHost, call, open_hand, sig  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser


def goal(idea, title, day, decision=0, element="meadow"):
    return {"idea": idea, "title": title, "party": "design", "element": element, "hue": "", "at": f"{day}T10:00:00", "day": day, "commit": "a" * 40, "decision": decision}


UNRELEASED = {"goals": [goal("words-then", "Words on the sign-in screen", "2026-11-04", 0, "ice")], "decisions": []}
NEW = {"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02", "open": True,
       "goals": [goal("seat", "Reconnect keeps your seat", "2026-10-31", 238, "dust")],
       "decisions": [{"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "goal": ""}]}
OLD = {"id": "v:0.3", "kind": "tag", "name": "v0.3", "day": "2026-10-28", "open": False}
OLD_FULL = {**OLD, "open": True, "goals": [goal("lobby", "A lobby with a chat", "2026-10-27", 0, "dust")], "decisions": [{"number": 212, "title": "The server owns every clock", "day": "2026-10-20", "changes": [], "changed_by": [], "goal": ""}]}
DECISIONS = {
    238: {"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "changes": [{"n": 206, "point": 3, "title": "The Orkmaster's column"}], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}],
          "entry": "## 238. The past lives past the portal\n\nWhy: the owner asked.", "goal": "seat"},
    206: {"number": 206, "title": "The Orkmaster's column", "day": "2026-10-01", "changes": [], "changed_by": [{"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "points": [3]}], "entry": "## 206. The column", "goal": ""},
    240: {"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "entry": "## 240. A verdict", "goal": ""},
    212: {"number": 212, "title": "The server owns every clock", "day": "2026-10-20", "changes": [], "changed_by": [], "entry": "## 212. The clocks", "goal": ""},
}


class PastHost(RoadHost):
    def __init__(self, newest=0):
        super().__init__(bare=True)
        self.newest = newest

    def handle(self, name, a):
        if not name.startswith("ideas.chronicle"):
            return super().handle(name, a)
        self.log.append((name, a))
        if name == "ideas.chronicle_last":
            return {"decisions": [{"number": self.newest, "title": "A decision", "element": "", "kind": "decision", "parties": ["design"], "version": "", "at": "2026-11-05T10:00:00"}] if self.newest else []}
        if name == "ideas.chronicle":
            return {"kind": "tag", "earlier": {"kind": "tag", "name": "v0.4", "day": "2026-11-02"}, "chapters": [NEW, OLD], "unreleased": UNRELEASED}
        if name == "ideas.chronicle_chapter":
            return OLD_FULL
        if name == "ideas.chronicle_goal":
            return {**NEW["goals"][0], "spec": {"asked": "A seat that stays.", "gist": "Keep the seat for a minute.", "sections": [{"party": "design", "title": "Design", "parts": {"Will": "Show the seat held."}}]},
                    "decision": DECISIONS[238], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}], "how_now": [{"capability": "seat", "title": "The kept seat"}],
                    "quality": {"findings": [{"id": "f1", "source": "lens", "what": "The bar is hard to see", "found": "", "level": "work"}]}}
        if name == "ideas.chronicle_decision":
            if a["number"] not in DECISIONS:
                return {"error": "That decision is not in the log"}
            return DECISIONS[a["number"]]
        raise AssertionError(name)


def asked(host, name):
    return [a for n, a in host.log if n == name]


def open_past(gui, tab="design", host=None, seen=None):
    pg, host, log = open_hand(gui, host=host or PastHost())
    if seen is not None:
        pg.evaluate("(n) => localStorage.setItem('orkboard.past.seen.design', String(n))", seen)
        pg.reload()
        pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    if tab != "orkmaster":
        call(pg, "frame/state.js", "openTab", tab)
    pg.locator(".release-lane__past .chr-deck").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def deck(pg, id_):
    return pg.locator(f'.release-lane__past .chr-deck[data-deck="{id_}"]')


def finish(pg, log):
    pg.close()
    assert not log, "\n".join(log)


def test_the_past_lies_deeper_in_the_lane_a_deck_a_version_unreleased_on_top_through_the_open_tabs_eyes_and_nothing_else_of_it_is_left(gui):
    pg, host, log = open_past(gui)
    assert {"party": "design"} in asked(host, "ideas.chronicle")
    assert [d.get_attribute("data-deck") for d in pg.locator(".release-lane__past .chr-deck").all()] == ["unreleased", "v:0.4", "v:0.3"], "Unreleased, then the versions, newest first"
    assert deck(pg, "unreleased").locator(".chr-deck__nm").inner_text().lower() == "unreleased"
    assert pg.locator(".portal__past, .pyramid, .ork-portal-ring__before, .ork-portal-ring__after, .chr-search").count() == 0 and sig(pg, "frame/state.js", "over") is None, "no lich's line, no pyramid, no chronicle over the pane"
    call(pg, "frame/state.js", "openTab", "orkmaster")
    pg.wait_for_function("() => document.querySelector('.release-lane__label')?.textContent === 'Discard'", timeout=WAIT_MS)
    pg.wait_for_function("() => true")
    assert asked(host, "ideas.chronicle")[-1] == {}, "the Orkmaster's tab reads the whole project's past"
    finish(pg, log)


def test_a_deck_pressed_deals_its_cards_in_the_lane_and_pressed_again_gathers_them_an_older_version_is_read_when_first_dealt(gui):
    pg, host, log = open_past(gui)
    assert pg.locator(".release-lane__deal").count() == 0, "none dealt at rest"
    deck(pg, "v:0.4").click()
    deal = pg.locator('.release-lane__deal[data-deck="v:0.4"] > .chr-card-wrap')
    deal.first.wait_for(timeout=WAIT_MS)
    assert [c.get_attribute("data-goal") or c.get_attribute("data-decision-row") for c in deal.all()] == ["seat", "240"]
    assert [c.locator('[data-much="version"]').inner_text() for c in deal.all()] == ["v0.4", "v0.4"], "each card's version at its bottom right"
    assert pg.locator('.chr-card-wrap[data-goal="seat"] .chr-card__dec').inner_text() == "§238", "the decision a goal carries beside its card"
    box, lane = deal.first.bounding_box(), pg.locator(".release-lane").bounding_box()
    assert (round(box["width"]), round(box["height"])) == (144, 202) and lane["x"] <= box["x"] and box["x"] + box["width"] <= lane["x"] + lane["width"], "whole cards, in the lane"
    assert asked(host, "ideas.chronicle_chapter") == [], "the newest version came with the list"
    deck(pg, "v:0.3").click()
    pg.locator('.chr-card-wrap[data-decision-row="212"]').wait_for(timeout=WAIT_MS)
    assert asked(host, "ideas.chronicle_chapter") == [{"id": "v:0.3", "party": "design"}], "read when it is first dealt"
    shot(pg, "past-lane-dealt.png")
    deck(pg, "v:0.3").click()                                                                              # pressed again: gathered
    pg.wait_for_function("() => document.querySelectorAll('.release-lane__deal[data-deck=\"v:0.3\"]').length === 0", timeout=WAIT_MS)
    assert deck(pg, "v:0.3").get_attribute("aria-pressed") == "false" and pg.locator('.release-lane__deal[data-deck="v:0.4"]').count() == 1
    deck(pg, "unreleased").click()
    pg.locator('.release-lane__deal[data-deck="unreleased"] .chr-card-wrap[data-goal="words-then"]').wait_for(timeout=WAIT_MS)
    finish(pg, log)


def test_a_goal_card_of_the_past_is_picked_and_the_table_shows_it_as_it_was(gui):
    pg, host, log = open_past(gui)
    deck(pg, "v:0.4").click()
    pg.locator('.chr-card-wrap[data-goal="seat"] .chr-card').click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "picked") == "seat" and sig(pg, "frame/state.js", "over") is None, "picked, nothing over the pane"
    assert pg.locator("#table-pane .chr-goal").count() == 1, "the table shows it"
    text = pg.locator(".chr-goal").inner_text()
    assert "Reconnect keeps your seat" in text and "A seat that stays." in text and "Show the seat held." in text
    assert pg.locator(".chr-changed").inner_text().startswith("changed by §241")
    assert pg.locator(".chr-decision .chr-link").inner_text() == "§238 The past lives past the portal" and "The bar is hard to see" in pg.locator(".chr-quality").inner_text()
    assert "is-lit" in pg.locator('.chr-card-wrap[data-goal="seat"]').get_attribute("class"), "the card stays marked in the lane"
    shot(pg, "past-goal.png")
    pg.keyboard.press("Escape")                                                                             # put away as any pick
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.picked.value === '')", timeout=WAIT_MS)
    finish(pg, log)


def test_a_decision_opens_its_entry_over_the_pane_its_links_are_walked_and_one_gone_is_said_in_words(gui):
    pg, host, log = open_past(gui)
    deck(pg, "v:0.4").click()
    pg.locator('.chr-card-wrap[data-goal="seat"] .chr-card__dec').click()
    page = pg.locator('.chr-decision-page[data-decision="238"]')
    page.wait_for(timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "over")["kind"] == "chronicle" and "Why: the owner asked." in page.locator(".chr-entry").inner_text()
    assert page.locator('[data-links="Changes"] .chr-link').inner_text() == "§206.3 The Orkmaster's column"
    assert page.locator('[data-links="Changed by"] .chr-link').inner_text() == "§241.2 A later word"
    page.get_by_role("button", name="The goal it came from").click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    pg.locator(".chr-back button").click()
    page.wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                             # ← leaves for the tab's table
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)
    pg.locator('.chr-card-wrap[data-decision-row="240"] .chr-card').click()                                 # a decision of no goal
    pg.locator('.chr-decision-page[data-decision="240"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-decision-page").get_by_role("button", name="The goal it came from").count() == 0
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 999 }))")
    pg.locator(".chr-err").first.wait_for(timeout=WAIT_MS)
    assert "not in the log" in pg.locator(".chr-err").first.inner_text()
    finish(pg, log)


def test_a_decision_named_by_the_conflict_or_the_bubble_opens_its_entry(gui):
    pg, host, log = open_past(gui)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 212 }))")
    pg.locator('.chr-decision-page[data-decision="212"]').wait_for(timeout=WAIT_MS)
    assert pg.locator("[data-title]").text_content().strip().endswith("Decision §212 · through Design")
    finish(pg, log)


def test_a_decision_newer_than_the_partys_last_look_is_a_muted_dot_on_its_tab_gone_once_the_lane_is_scrolled_to_the_past(gui):
    pg, host, log = open_past(gui, tab="orkmaster", host=PastHost(newest=241), seen=240)
    pg.locator('.table-tab[data-tab="design"] .table-tab__new').wait_for(timeout=WAIT_MS)
    dot = pg.locator('.table-tab[data-tab="design"] .table-tab__new')
    assert dot.get_attribute("aria-label") == "A decision is newer than your last look at this party's past" and pg.locator('.table-tab[data-tab="tech"] .table-tab__new').count() == 0, "Design's tab only"
    assert dot.evaluate("e => getComputedStyle(e).backgroundColor") == pg.evaluate("() => { const s = document.createElement('i'); s.style.backgroundColor = 'var(--ork-ink-muted)'; document.body.append(s); const c = getComputedStyle(s).backgroundColor; s.remove(); return c; }"), "muted"
    shot(pg, "past-dot.png")
    call(pg, "frame/state.js", "openTab", "design")                                                          # its lane: the past is in view, the newest decision is seen
    pg.wait_for_function("() => localStorage.getItem('orkboard.past.seen.design') === '241'", timeout=WAIT_MS)
    call(pg, "frame/state.js", "openTab", "orkmaster")
    pg.wait_for_function("() => !document.querySelector('.table-tab .table-tab__new')", timeout=WAIT_MS)
    finish(pg, log)


def test_never_looked_at_nothing_is_new_the_first_read_is_taken_as_seen(gui):
    pg, host, log = open_past(gui, tab="orkmaster", host=PastHost(newest=241))
    pg.wait_for_function("() => localStorage.getItem('orkboard.past.seen.design') === '241'", timeout=WAIT_MS)
    assert pg.locator(".table-tab__new").count() == 0
    finish(pg, log)
