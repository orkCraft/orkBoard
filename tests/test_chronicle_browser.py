"""Spec 134 part B, the chronicle's face (docs/specs/134-release-keeps-the-chronicle.md B; decisions §238.2–§238.4), in a real browser against a stub host (the maps' `MapsHost`, with the `ideas.chronicle*` commands answered
as the host answers them): one line *Earlier: v0.3 · 28 Oct ›* in Release's lens (none when nothing is known, a week said *The week of 3 Nov*), pressed it opens the chronicle over the pane; a chapter a version, newest first, the newest
open, an older one a line opened by a press; a decision a goal carries beside its goal's row, a decision of no goal a row of its own; the search shows its finds by chapter; a goal opened as it was (its spec marked *changed by §<n>*, its
decision, its quality, *How it works now*); a decision opened with its *Changes* and *changed by* links walked; ← back to the lens. Desktop only (§238.6). Screenshots to ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import MapsHost, Refused, go, watch  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser


def goal(idea, title, day, decision=0, element="meadow"):
    return {"idea": idea, "title": title, "party": "tech", "element": element, "hue": "", "at": f"{day}T10:00:00", "day": day, "commit": "a" * 40, "decision": decision}


NEW = {"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02", "open": True,
       "goals": [goal("timer", "Round timer shows on every phone", "2026-11-01", 238), goal("seat", "Reconnect keeps your seat", "2026-10-31", 0, "ice")],
       "decisions": [{"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "goal": ""}]}
OLD = {"id": "v:0.3", "kind": "tag", "name": "v0.3", "day": "2026-10-28", "open": False}
OLD_FULL = {**OLD, "open": True, "goals": [goal("lobby", "A lobby with a chat", "2026-10-27", 0, "dust")], "decisions": []}
DECISIONS = {
    238: {"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "changes": [{"n": 206, "point": 3, "title": "The Orkmaster's column"}], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}],
          "entry": "## 238. The past lives past the portal\n\nWhy: the owner asked.", "goal": "timer"},
    206: {"number": 206, "title": "The Orkmaster's column", "day": "2026-10-01", "changes": [], "changed_by": [{"number": 238, "title": "The past lives past the portal", "day": "2026-11-04", "points": [3]}], "entry": "## 206. The column", "goal": ""},
    240: {"number": 240, "title": "A hypothesis's verdict", "day": "2026-11-01", "changes": [], "changed_by": [], "entry": "## 240. A verdict", "goal": ""},
}


class ChronicleHost(MapsHost):
    def __init__(self, earlier="tag"):
        super().__init__()
        self.earlier = {"tag": {"kind": "tag", "name": "v0.4", "day": "2026-11-02"}, "week": {"kind": "week", "name": "", "day": "2026-11-02"}, "none": None}[earlier]

    def handle(self, name, a):
        if not name.startswith("ideas.chronicle"):
            return super().handle(name, a)
        self.log.append((name, a))
        if name == "ideas.chronicle_line":
            return {"earlier": self.earlier}
        if name == "ideas.chronicle":
            return {"kind": "tag", "earlier": self.earlier, "chapters": [NEW, OLD], "unreleased": None}
        if name == "ideas.chronicle_chapter":
            return OLD_FULL
        if name == "ideas.chronicle_find":
            return {"query": a["query"], "found": 1, "more": 0, "unreleased": None, "chapters": [{"id": "v:0.4", "kind": "tag", "name": "v0.4", "day": "2026-11-02",
                    "goals": [{"idea": "timer", "title": "Round timer shows on every phone", "day": "2026-11-01", "element": "meadow", "hue": "", "decision": 238, "in": ["title", "spec"]}], "decisions": []}]}
        if name == "ideas.chronicle_goal":
            return {**NEW["goals"][0], "spec": {"asked": "A timer on every phone.", "gist": "Ninety seconds a round.", "sections": [{"party": "tech", "title": "Tech", "parts": {"Will": "Add a timer to the lobby."}}]},
                    "decision": DECISIONS[238], "changed_by": [{"number": 241, "title": "A later word", "day": "2026-11-05", "points": [2]}], "how_now": [{"capability": "timer", "title": "The round timer"}],
                    "quality": {"findings": [{"id": "f1", "source": "lens", "what": "The bar is hard to see", "found": "", "level": "work"}]}}
        if name == "ideas.chronicle_decision":
            if a["number"] not in DECISIONS:
                raise Refused("That decision is not in the log")
            return DECISIONS[a["number"]]
        raise AssertionError(name)


def open_release(gui, host):
    server, browser = gui
    errors: list[str] = []
    pg = narrow.page(browser, "wide")
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    go(pg, "release")
    pg.locator(".mp-since").wait_for(timeout=WAIT_MS)
    return pg, errors


def finish(pg, errors):
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_lens_says_one_line_of_the_last_version_and_it_opens_the_chronicle_and_back_returns(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    line = pg.locator(".mp-earlier")
    line.wait_for(timeout=WAIT_MS)
    assert line.inner_text() == "Earlier: v0.4 · 2 Nov ›" and pg.locator(".mp-earlier").count() == 1
    assert [a for n, a in host.log if n.startswith("ideas.chronicle")] == [{}]                                              # one read, the line's; no list, no count
    shot(pg, "chronicle-lens.png")
    line.click()
    pg.locator('.table-over[data-kind="chronicle"] .chr').wait_for(timeout=WAIT_MS)
    assert pg.locator("[data-title]").text_content().endswith("· Chronicle")
    pg.keyboard.press("Escape")
    pg.locator(".mp-since").wait_for(timeout=WAIT_MS)
    assert pg.locator('.table-over[data-kind="chronicle"]').count() == 0
    finish(pg, errors)


def test_a_project_with_no_version_yet_says_the_week_and_one_with_no_past_says_nothing(gui):
    pg, errors = open_release(gui, ChronicleHost("week"))
    assert pg.locator(".mp-earlier").inner_text() == "Earlier: The week of 2 Nov ›"
    finish(pg, errors)
    pg, errors = open_release(gui, ChronicleHost("none"))
    pg.wait_for_timeout(300)
    assert pg.locator(".mp-earlier").count() == 0
    finish(pg, errors)


def test_the_newest_chapter_is_open_an_older_one_a_line_and_a_decision_stands_beside_its_goal(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    pg.locator(".mp-earlier").click()
    pg.locator(".chr-chapter").first.wait_for(timeout=WAIT_MS)
    chapters = pg.locator(".chr-chapter")
    assert [c.get_attribute("data-chapter") for c in chapters.all()] == ["v:0.4", "v:0.3"]                                    # newest first
    assert " ".join(chapters.first.locator(".chr-chapter__btn").inner_text().split()) == "v0.4 2 Nov" and chapters.first.locator(".chr-chapter__btn").get_attribute("aria-expanded") == "true"
    assert chapters.last.locator(".chr-chapter__btn").get_attribute("aria-expanded") == "false" and chapters.last.locator(".chr-row").count() == 0       # an older one is a line
    rows = chapters.first.locator(".chr-row")
    assert [r.locator(".chr-row__nm").inner_text() for r in rows.all()] == ["Round timer shows on every phone", "Reconnect keeps your seat", "A hypothesis's verdict"]
    assert rows.first.locator(".chr-row__dec").inner_text() == "§238" and rows.nth(1).locator(".chr-row__dec").count() == 0       # the carried decision beside its goal
    assert rows.last.get_attribute("data-decision-row") == "240"                                                              # a decision of no goal: a row of its own
    shot(pg, "chronicle-list.png")
    chapters.last.locator(".chr-chapter__btn").click()
    chapters.last.locator(".chr-row").first.wait_for(timeout=WAIT_MS)
    assert chapters.last.locator(".chr-row__nm").inner_text() == "A lobby with a chat"
    assert [a for n, a in host.log if n == "ideas.chronicle_chapter"] == [{"id": "v:0.3"}]
    chapters.last.locator(".chr-chapter__btn").click()                                                                        # pressed again, it folds
    assert chapters.last.locator(".chr-row").count() == 0
    finish(pg, errors)


def test_the_search_shows_its_finds_by_chapter_and_where_the_words_were(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    pg.locator(".mp-earlier").click()
    pg.get_by_role("searchbox", name="Search the chronicle").fill("timer")
    pg.locator(".chr-finds").wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-chapter").count() == 1 and pg.locator(".chr-chapter").get_attribute("data-chapter") == "v:0.4"      # the chapters with none are folded away
    assert "in its name, its spec" in pg.locator(".chr-row").inner_text()
    assert [a for n, a in host.log if n == "ideas.chronicle_find"] == [{"query": "timer"}]
    shot(pg, "chronicle-find.png")
    pg.get_by_role("searchbox", name="Search the chronicle").fill("")
    pg.locator(".chr-chapters").wait_for(timeout=WAIT_MS)
    finish(pg, errors)


def test_a_goal_opens_as_it_was_with_its_spec_marked_changed_by_its_decision_its_quality_and_how_it_works_now(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    pg.locator(".mp-earlier").click()
    pg.locator('.chr-row[data-goal="timer"] .chr-row__btn').click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    text = pg.locator(".chr-goal").inner_text()
    assert "Round timer shows on every phone" in text and "A timer on every phone." in text and "Add a timer to the lobby." in text
    assert pg.locator(".chr-changed").inner_text().startswith("changed by §241") and "A later word" in pg.locator(".chr-changed").inner_text()
    assert pg.locator(".chr-decision .chr-link").inner_text() == "§238 The past lives past the portal" and "Why: the owner asked." in pg.locator(".chr-entry").inner_text()
    assert "The bar is hard to see" in pg.locator(".chr-quality").inner_text()
    assert " ".join(pg.locator(".chr-now").text_content().split()) == "How it works nowThe round timer"
    assert [a for n, a in host.log if n == "ideas.chronicle_goal"] == [{"idea": "timer"}]
    shot(pg, "chronicle-goal.png")
    pg.get_by_role("button", name="Chronicle").click()                                                                        # back to the list, still in the chronicle
    pg.locator(".chr-chapters").wait_for(timeout=WAIT_MS)
    finish(pg, errors)


def test_a_decision_opens_its_entry_and_its_changes_and_changed_by_links_are_walked(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    pg.locator(".mp-earlier").click()
    pg.locator('.chr-row[data-goal="timer"] .chr-row__dec').click()
    pg.locator('.chr-decision-page[data-decision="238"]').wait_for(timeout=WAIT_MS)
    page = pg.locator(".chr-decision-page")
    assert "The past lives past the portal" in page.locator(".chr-title").inner_text() and "Why: the owner asked." in page.locator(".chr-entry").inner_text()
    assert page.locator('[data-links="Changes"] .chr-link').inner_text() == "§206.3 The Orkmaster's column"
    assert page.locator('[data-links="Changed by"] .chr-link').inner_text() == "§241.2 A later word"
    page.get_by_role("button", name="The goal it came from").click()
    pg.locator(".chr-goal").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Chronicle").click()
    pg.locator('.chr-row[data-decision-row="240"] .chr-row__btn').click()                                                      # a decision of no goal
    pg.locator('.chr-decision-page[data-decision="240"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".chr-decision-page").get_by_role("button", name="The goal it came from").count() == 0
    shot(pg, "chronicle-decision.png")
    finish(pg, errors)


def test_a_decision_gone_from_the_log_is_said_in_words(gui):
    host = ChronicleHost()
    pg, errors = open_release(gui, host)
    pg.evaluate("() => import('/static/js/table/chronicle.js').then((m) => m.openChronicle({ decision: 999 }))")
    pg.locator(".chr-err").wait_for(timeout=WAIT_MS)
    assert "not in the log" in pg.locator(".chr-err").inner_text()
    pg.context.close()
    assert [e for e in errors if "pageerror" in e] == []
    assert json.dumps(host.log)                                                                                               # the stub kept its log
