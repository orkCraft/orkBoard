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


def cards(n, first_day=20):
    """n cards, one a day from the 20th of November down: goals g1, g3.. and decisions 302, 304.. on their own days, the newest first."""
    return ([goal(f"g{i}", f"Goal {i}", f"2026-11-{first_day - i:02d}") for i in range(1, n + 1, 2)],
            [{"number": 300 + i, "title": f"Decision {i}", "day": f"2026-11-{first_day - i:02d}", "changes": [], "changed_by": [], "goal": ""} for i in range(2, n + 1, 2)])


class PastHost(RoadHost):
    def __init__(self, newest=0, deck=None):
        super().__init__(bare=True)
        self.newest = newest
        self.deck = deck                                                                                      # (goals, decisions) of v0.4 when a test wants a different deck

    def handle(self, name, a):
        if not name.startswith("ideas.chronicle"):
            return super().handle(name, a)
        self.log.append((name, a))
        if name == "ideas.chronicle_last":
            return {"decisions": [{"number": self.newest, "title": "A decision", "element": "", "kind": "decision", "parties": ["design"], "version": "", "at": "2026-11-05T10:00:00"}] if self.newest else []}
        if name == "ideas.chronicle":
            new = {**NEW, "goals": self.deck[0], "decisions": self.deck[1]} if self.deck else NEW
            return {"kind": "tag", "earlier": {"kind": "tag", "name": "v0.4", "day": "2026-11-02"}, "chapters": [new, OLD], "unreleased": UNRELEASED}
        if name == "ideas.chronicle_chapter":
            return {**NEW, "goals": self.deck[0], "decisions": self.deck[1]} if self.deck and a["id"] == "v:0.4" else OLD_FULL
        if name == "ideas.chronicle_find":
            want = a["query"].lower().split()
            gs, ds = (self.deck or (NEW["goals"], NEW["decisions"]))
            hit = lambda s: all(w in s.lower() for w in want)  # noqa: E731
            mine = {"id": a["id"], "kind": "tag", "name": "v0.4", "day": "2026-11-02",
                    "goals": [{"idea": g["idea"], "title": g["title"], "in": ["title"]} for g in gs if hit(g["title"])],
                    "decisions": [{"number": d["number"], "title": d["title"], "day": d["day"], "in": ["decision"]} for d in ds if hit(d["title"])]}
            return {"query": a["query"], "found": 0, "more": 0, "chapters": [mine] if mine["goals"] or mine["decisions"] else [], "unreleased": None}
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
    assert [c.get_attribute("data-goal") or c.get_attribute("data-decision-row") for c in deal.all()] == ["240", "seat"], "newest day first across goals and decisions"
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
    pg.set_viewport_size({"width": 1440, "height": 900})                                                       # the discard is a column beside the table: five tracks keep their names (not compact) from this width
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


def dealt(pg, id_):
    return [c.get_attribute("data-goal") or "d" + c.get_attribute("data-decision-row") for c in pg.locator(f'.release-lane__deal[data-deck="{id_}"] > .chr-card-wrap').all()]


def test_a_deck_of_more_than_seven_deals_its_newest_seven_by_day_then_all_search_in_the_lines_face_with_no_count(gui):
    pg, host, log = open_past(gui, host=PastHost(deck=cards(9)))
    deck(pg, "v:0.4").click()
    pg.locator('.release-lane__deal[data-deck="v:0.4"] .chr-card-wrap').first.wait_for(timeout=WAIT_MS)
    assert dealt(pg, "v:0.4") == ["g1", "d302", "g3", "d304", "g5", "d306", "g7"], "the newest seven by day across goals and decisions; g9 and d308 are left for All"
    all_ = pg.locator('.release-lane__deal[data-deck="v:0.4"] .table-lstrip--all')
    assert all_.count() == 1 and all_.inner_text() == "All · search" and all_.get_attribute("aria-label") == "All of v0.4, with a search"
    assert all_.locator(".ork-icon").count() == 1 and "table-gstrip" in all_.get_attribute("class"), "the line's face: the sign search and the words"
    assert pg.locator('.release-lane__deal[data-deck="v:0.4"] > li').last.locator(".table-lstrip--all").count() == 1, "the eighth card, after the seven"
    box, lane = all_.bounding_box(), pg.locator(".release-lane").bounding_box()
    assert lane["x"] <= box["x"] and box["x"] + box["width"] <= lane["x"] + lane["width"], "in the lane"
    text = pg.locator(".release-lane__past").inner_text().lower()
    assert "of 9" not in text and "more" not in text and "cards" not in text, "no count of the deck"
    shot(pg, "past-lane-seven-all.png")
    all_.focus()                                                                                               # a button: Tab reaches it, Enter presses it
    pg.keyboard.press("Enter")
    assert sig(pg, "frame/state.js", "over")["kind"] == "chronicle", "stage I: the deck opens over the pane"
    finish(pg, log)


def open_all(pg, id_="v:0.4"):
    if deck(pg, id_).get_attribute("aria-pressed") != "true":
        deck(pg, id_).click()
    all_ = pg.locator(f'.release-lane__deal[data-deck="{id_}"] [data-deck-all]')
    all_.wait_for(timeout=WAIT_MS)
    all_.focus()
    pg.keyboard.press("Enter")
    pg.locator(".chr-deck-all .chr-search input").wait_for(timeout=WAIT_MS)
    return all_


def shown(pg):
    return [c.get_attribute("data-goal") or "d" + c.get_attribute("data-decision-row") for c in pg.locator(".chr-deck-all .chr-deal > .chr-card-wrap").all()]


def test_all_search_opens_the_whole_deck_over_the_pane_under_its_name_with_its_search_focused_words_narrow_it_and_esc_gives_the_lane_back(gui):
    pg, host, log = open_past(gui, host=PastHost(deck=cards(9)))
    open_all(pg)
    o = sig(pg, "frame/state.js", "over")
    assert o["kind"] == "chronicle" and o["props"]["deck"]["id"] == "v:0.4" and pg.locator("[data-title]").text_content().strip().endswith("v0.4 · through Design")
    assert pg.evaluate("() => document.activeElement.matches('.chr-search input')"), "its search field focused"
    pg.wait_for_function("() => document.querySelectorAll('.chr-deck-all .chr-card-wrap').length === 9", timeout=WAIT_MS)
    assert shown(pg) == ["g1", "d302", "g3", "d304", "g5", "d306", "g7", "d308", "g9"], "the whole deck by day, newest first"
    assert {"id": "v:0.4", "party": "design"} in asked(host, "ideas.chronicle_chapter")
    shot(pg, "past-deck-over-pane.png")
    pg.keyboard.type("goal 5")
    pg.wait_for_function("() => document.querySelectorAll('.chr-deck-all .chr-card-wrap').length === 1", timeout=WAIT_MS)
    assert shown(pg) == ["g5"] and asked(host, "ideas.chronicle_find")[-1] == {"query": "goal 5", "id": "v:0.4", "party": "design"}
    assert "in its name" in pg.locator(".chr-deck-all .chr-card__day").inner_text()
    pg.keyboard.press("Control+a")
    pg.keyboard.type("zzz")
    pg.locator(".chr-none").wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-none").inner_text() == "Nothing in v0.4 has those words." and shown(pg) == []
    pg.keyboard.press("Escape")                                                                             # typing in the field: Esc gives the lane back
    pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)
    pg.wait_for_function("() => document.activeElement?.matches('[data-deck-all=\"v:0.4\"]')", timeout=WAIT_MS)
    assert pg.locator('.release-lane__deal[data-deck="v:0.4"]').count() == 1, "the lane as it was"
    finish(pg, log)


def test_the_deck_over_the_pane_goes_back_by_the_arrow_too_and_a_goal_card_picks_the_goal_a_decision_card_opens_its_entry(gui):
    pg, host, log = open_past(gui, host=PastHost(deck=cards(9)))
    open_all(pg)
    pg.locator('.chr-deck-all .chr-card-wrap[data-goal="g9"]').wait_for(timeout=WAIT_MS)
    pg.locator(".table-title__back").click()
    pg.wait_for_function("() => document.activeElement?.matches('[data-deck-all=\"v:0.4\"]')", timeout=WAIT_MS)
    assert sig(pg, "frame/state.js", "over") is None
    all_ = open_all(pg)
    pg.locator('.chr-deck-all .chr-card-wrap[data-goal="g9"] .chr-card').click()
    assert sig(pg, "frame/state.js", "picked") == "g9" and sig(pg, "frame/state.js", "over") is None, "closed, and the goal picked"
    pg.keyboard.press("Escape")
    open_all(pg)
    pg.locator('.chr-deck-all .chr-card-wrap[data-decision-row="308"] .chr-card').click()
    assert sig(pg, "frame/state.js", "over")["props"] == {"decision": 308}, "a decision opens its entry"
    pg.locator(".chr-err, .chr-decision-page").first.wait_for(timeout=WAIT_MS)
    del all_
    finish(pg, log)


def test_a_week_deck_dealt_on_the_orkmasters_tab_at_1366_by_768_for_the_eye(gui):
    pg, host, log = open_past(gui, tab="orkmaster", host=PastHost(deck=cards(9)))
    pg.set_viewport_size({"width": 1366, "height": 768})
    pg.wait_for_timeout(300)
    deck(pg, "v:0.4").click()
    pg.locator('.release-lane__deal[data-deck="v:0.4"] .table-lstrip--all').wait_for(timeout=WAIT_MS)
    shot(pg, "past-orkmaster-week-deck-1366.png")
    pg.locator('.release-lane__deal[data-deck="v:0.4"] .table-lstrip--all').click()
    pg.locator(".chr-deck-all .chr-card-wrap").first.wait_for(timeout=WAIT_MS)
    shot(pg, "past-orkmaster-deck-over-pane-1366.png")
    finish(pg, log)


def test_a_deck_of_seven_or_fewer_deals_whole_with_no_all_search_and_on_one_day_goals_come_first(gui):
    pg, host, log = open_past(gui, host=PastHost(deck=cards(7)))
    deck(pg, "v:0.4").click()
    pg.locator('.release-lane__deal[data-deck="v:0.4"] .chr-card-wrap').first.wait_for(timeout=WAIT_MS)
    assert len(dealt(pg, "v:0.4")) == 7 and pg.locator(".table-lstrip--all").count() == 0, "seven deal whole, none after them"
    finish(pg, log)
    same = ([goal("g1", "Goal", "2026-11-20")], [{"number": 301, "title": "Decision", "day": "2026-11-20", "changes": [], "changed_by": [], "goal": ""}])
    pg, host, log = open_past(gui, host=PastHost(deck=same))
    deck(pg, "v:0.4").click()
    pg.locator('.release-lane__deal[data-deck="v:0.4"] .chr-card-wrap').first.wait_for(timeout=WAIT_MS)
    assert dealt(pg, "v:0.4") == ["g1", "d301"] and pg.locator(".table-lstrip--all").count() == 0, "on one day the goal first"
    finish(pg, log)


# -- a first open over the real host (spec 162 J; decisions §277): the past from history lies once ---------------------------------------------------

import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402


HERE = Path(__file__).resolve().parents[1]
HISTORY = [("201-first-sign", "201"), ("202-then-seat", "202"), ("203-the-lobby", "203"), ("204-no-decision", "")]


def _page(slug, decisions):
    return (f"---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nsize:\npriority: normal\nshort: {slug}\nphase: done\nroute: design, tech\nspec: docs/specs/{slug}.md\n"
            f"decisions: {decisions}\nby: person\nlaid: history\nschema: 3\n---\n# {slug}\n\n## Gist\n{slug}.\n")


@pytest.fixture(scope="module")
def first_open(tmp_path_factory, gui):
    """The real host and server over a git project whose goal pages are laid done as history, with decisions: in a log: `(server, browser)`, the browser the gui fixture's, the state its own."""
    tmp = tmp_path_factory.mktemp("first_open")
    browser = gui[1]
    mp = pytest.MonkeyPatch()
    mp.setenv("ORKCRAFT_STATE_DIR", str(tmp / "state"))
    repo = tmp / "project"
    wiki = repo / "llm-wiki/general/pages"
    (wiki / "ideas").mkdir(parents=True)
    (wiki / "tracks").mkdir()
    (repo / "docs").mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    for t in ("design", "product", "tech", "general"):
        shutil.copy(HERE / f"llm-wiki/general/pages/tracks/{t}.md", wiki / "tracks" / f"{t}.md")
    log = ["# Decisions\n"]
    for n, day in ((201, "26 October 2026"), (202, "27 October 2026"), (203, "3 November 2026")):
        log.append(f"## {n}. Decision {n} ({day}, the owner)\n\nWhy: a reason.\n")
    (repo / "docs/decisions.md").write_text("\n".join(log), encoding="utf-8")
    for slug, dec in HISTORY:
        (wiki / "ideas" / f"{slug}.md").write_text(_page(slug, dec), encoding="utf-8")
    git = ["git", "-c", "user.email=test@orkcraft.local", "-c", "user.name=Test Runner"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "init"], cwd=repo, check=True)
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    from orkboard.realm import project_kind
    host = Orkboard(repo)
    project_kind.keep(host.ideas.state_dir, "code")
    host.first_open.tools_skipped = True
    server = Server(host)
    thread = server.start_thread()
    yield server, browser
    server.stop()
    thread.join(10)
    mp.undo()


def test_a_first_open_lays_each_history_goal_once_in_its_weeks_deck_never_in_the_discard_and_no_tab_wears_the_dot(first_open):
    server, browser = first_open
    ctx = browser.new_context(viewport={"width": 1366, "height": 768})
    pg = ctx.new_page()
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.goto(server.url)
    pg.locator(".table-tab[data-tab]").first.wait_for(timeout=WAIT_MS)
    call(pg, "frame/state.js", "openTab", "design")
    pg.locator('.release-lane__past .chr-deck[data-deck="w:2026-10-26"]').wait_for(timeout=WAIT_MS)       # the lane draws although the flags were raised while it first asked
    assert [d.get_attribute("data-deck") for d in pg.locator(".release-lane__past .chr-deck").all()] == ["w:2026-11-02", "w:2026-10-26"], "the weeks, newest first"
    for id_ in ("w:2026-11-02", "w:2026-10-26"):
        deck(pg, id_).click()
        pg.locator(f'.release-lane__deal[data-deck="{id_}"] .chr-card-wrap').first.wait_for(timeout=WAIT_MS)

    def goals(id_):
        return sorted(c.get_attribute("data-goal") for c in pg.locator(f'.release-lane__deal[data-deck="{id_}"] .chr-card-wrap[data-goal]').all())
    assert goals("w:2026-10-26") == ["201-first-sign", "202-then-seat"] and goals("w:2026-11-02") == ["203-the-lobby", "204-no-decision"], "each in the week of its day"
    assert sorted(c.get_attribute("data-goal") for c in pg.locator(".release-lane [data-goal].chr-card-wrap, .release-lane .chr-card-wrap[data-goal]").all()) == sorted(h[0] for h in HISTORY), "each card lies once"
    assert pg.locator(".release-lane__done").count() == 0, "none among the goals done and not yet seen"
    pg.wait_for_timeout(500)
    assert pg.locator(".table-tab__new").count() == 0, "no party's tab wears the past's dot"
    pg.evaluate("() => document.querySelectorAll('[class*=toast]').forEach((e) => { e.style.display = 'none'; })")      # the shot is of the lane
    shot(pg, "past-first-open-design-1366.png")
    for tab in ("tech", "product", "design"):                                                           # the dot is not lit by a look at another tab either
        call(pg, "frame/state.js", "openTab", tab)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-tab__new").count() == 0, tab
    assert not errors, errors
    ctx.close()
