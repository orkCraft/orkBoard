"""Spec 108 part B, concerns on the maps (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §3, decisions §183.4–§183.5), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844),
against the maps' stub host (`MapsHost`: Game design with its loop, Tech led by the Architect with its System, Art, Release, Marketing) that also answers part A's commands as the contract says —
`ideas.concerns {party}` the record `{at, map_hash, by, status, error, concerns: [{id, on, name, level, what, why, fix, signal}], dismissed}`, `ideas.concerns_again`, `ideas.concern_dismiss` (both the record),
`ideas.concern_goal` (`{ok, idea}`) — and carrying each goal's `concerns: {alerts, notes, status}` in the snapshot.

A card with an alert wears orkUI's alert sign and the leader's small head, a note a dot; the highest level of several, their count only in the label; on a part of the System (inside its scaled box) and on a step of the loop;
the strip in each state (*The Architect: 1 alert, 1 note*, *sees nothing wrong*, *is looking at the map…* with the busy mark, a failure in its words), **Ask again**, a press on the counts stepping through the marked cards;
a marked card pressed lifts and its back lists each concern with **Make it a goal** and **Not a problem**, the mark then a link to the goal in its element's colour; the party's tab shows **!** with no count; nothing moves under
reduced motion; every target 44 px at the narrow width; picking wins on a marked card; a host without the commands shows no strip and no error. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import MapsHost, Refused  # noqa: E402
from tests.test_picking_desktop_browser import open_field, part  # noqa: E402
from tests.test_table_desktop_browser import node, party, shot, tab, title, watch  # noqa: E402

pytestmark = pytest.mark.browser

LOBBY, ROOMS, INDEX = "server/lobby.ts", "server/rooms.ts", "server/index.ts"


def concern(cid, on, level, what, why="", fix="", signal=""):
    return {"id": cid, "on": on, "name": on.rsplit("/", 1)[-1], "level": level, "what": what, "why": why or f"Why: {what}", "fix": fix or f"Fix: {what}", "signal": signal}


def record(*concerns, status="ready", error="", by="architect"):
    return {"at": "2026-10-29T08:00:00", "map_hash": "h1", "by": by, "status": status, "error": error, "measure": None, "concerns": list(concerns), "dismissed": []}


TECH = [concern("c1", LOBBY, "alert", "Every room goes through lobby.ts", "Eleven parts use it and it holds the sockets too.", "Split the sockets out of it.", "fan_in"),
        concern("c2", LOBBY, "note", "lobby.ts changed six times this month with no test", "", "", "churn"),
        concern("c3", ROOMS, "note", "rooms.ts grows", "It is four hundred lines.", "Watch it.")]
GAME = [concern("g1", "hold-the-tower", "alert", "Nothing in the loop pays for holding the tower", "Gems are only earned.", "Let gems buy a skin.", "finding"),
        concern("g2", "join-a-match", "note", "Joining takes four steps", "", ""), concern("g3", "cur:coins", "note", "Coins have no sink", "", "")]


class ConcernHost(MapsHost):
    """The maps' host that also keeps a record for each party and answers part A's commands; `older`: a host that does not know them."""

    def __init__(self):
        super().__init__()
        self.parties[0]["leader"]["name"] = "Game design lead"
        self.records = {"tech": record(*copy.deepcopy(TECH)), "game": record(*copy.deepcopy(GAME))}
        self.older = False
        self.looks = 0

    def counts(self, slug):
        r = self.records.get(slug)
        if not r:
            return {"alerts": 0, "notes": 0, "status": "ready"}
        return {"alerts": sum(c["level"] == "alert" for c in r["concerns"]), "notes": sum(c["level"] == "note" for c in r["concerns"]), "status": r["status"]}

    def handle(self, name, a):
        if name == "ideas.map" and not self.older:
            got = super().handle(name, a)
            for g in got["goals"]:
                g["concerns"] = self.counts(g["slug"])
            return got
        if name.startswith("ideas.concern"):
            self.log.append((name, a))
            if self.older:
                raise Refused(f"unknown command {name}")
            return self.concerns(name, a)
        return super().handle(name, a)

    def concerns(self, name, a):
        rec = self.records.setdefault(a["party"], record())
        if name == "ideas.concerns":
            if rec["status"] == "looking":                                                     # a look under way ends the second time it is asked about
                self.looks += 1
                if self.looks >= 2:
                    rec["status"] = "ready"
                    self.looks = 0
                    self.rev += 1
            return copy.deepcopy(rec)
        if name == "ideas.concerns_again":
            rec["status"] = "looking"
            self.looks = 0
            return copy.deepcopy(rec)
        c = next(x for x in rec["concerns"] if x["id"] == a["id"])
        if name == "ideas.concern_dismiss":
            rec["concerns"].remove(c)
            rec["dismissed"].append({"on": c["on"], "what": c["what"], "at": "2026-10-29T09:00:00", "map_hash": rec["map_hash"]})
            self.rev += 1
            return copy.deepcopy(rec)
        c["idea"] = "split-sockets"                                                              # ideas.concern_goal: a goal made of it
        self.nodes.append(node("split-sockets", a["party"], c["what"], "ready", element="ice", sign="restructure", place="deck"))
        self.rev += 1
        return {"ok": True, "idea": "split-sockets"}

    def sent(self, name):
        return [a for n, a in self.log if n == name]


def start(gui, width, host=None, **context):
    errors: list[str] = []
    server, browser = gui
    host = host or ConcernHost()
    pg = browser.new_context(**{**(narrow.WIDE if width == "wide" else narrow.FINE), **context}).new_page()
    watch(pg, errors)
    pg.add_init_script("window.__scrolls = []; const into = Element.prototype.scrollIntoView; Element.prototype.scrollIntoView = function (o) { window.__scrolls.push(o && o.behavior); return into.call(this, o); };")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, errors


@pytest.fixture(params=narrow.WIDTHS)
def desk(gui, request):
    """The window at one of the two widths against a ConcernHost: `(page, host, width)`; the page's errors are asserted at the end."""
    pg, host, errors = start(gui, request.param)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def go(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def system(pg):
    go(pg, "tech")
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
    pg.locator(".cn-strip").wait_for(timeout=WAIT_MS)


def loop(pg):
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    pg.locator(".cn-strip").wait_for(timeout=WAIT_MS)


def strip(pg):
    return pg.locator(".cn-strip")


def say(pg):
    return " ".join(strip(pg).inner_text().split())


def marks(pg):
    return pg.locator(".cn-slot .cn-mark")


def back(pg):
    return pg.locator(".table-back")


def wide(w):
    return w == "wide"


# -- the marks -----------------------------------------------------------------------------------------------------------------------------------------

def test_an_alert_wears_the_alert_sign_and_the_leaders_head_a_note_a_dot_on_a_part_of_the_system_inside_its_scaled_box(desk):
    pg, host, w = desk
    system(pg)
    lobby, rooms = marks(pg).locator("xpath=.").filter(has=pg.locator(".ork-sign.alert")), marks(pg).filter(has=pg.locator(".cn-dot"))
    pg.locator('.cn-mark[data-level="alert"]').first.wait_for(timeout=WAIT_MS)
    assert lobby.count() == 1 and rooms.count() == 1, "an alert on lobby.ts, a note on rooms.ts"
    alert = pg.locator('.cn-mark[data-level="alert"]')
    assert "peon-elder" in alert.locator(".ork-race__head").get_attribute("src"), "the leader's small head beside the sign"
    assert alert.get_attribute("aria-label") == "2 concerns of the Architect", "two on one card: the highest level, the count in the label only"
    assert alert.inner_text().strip() == "" and rooms.get_attribute("aria-label") == "1 concern of the Architect"
    assert rooms.locator(".ork-race__head").count() == 0 and rooms.locator(".ork-sign").count() == 0, "a note is a dot, no head"
    assert pg.locator(".arch .cn-slot").count() == 2, "the marks lie inside the System's scaled box, so they scale with it"
    card, mark = part(pg, LOBBY).bounding_box(), alert.bounding_box()
    assert card["x"] + card["width"] / 2 < mark["x"] and mark["x"] + mark["width"] <= card["x"] + card["width"] + 1, "at the card's top right"
    assert card["y"] - 1 <= mark["y"] <= card["y"] + card["height"] / 3
    assert part(pg, LOBBY).get_attribute("data-concern") == "alert" and part(pg, ROOMS).get_attribute("data-concern") == "note" and part(pg, INDEX).get_attribute("data-concern") is None
    assert pg.locator(".cn-slot button, button .cn-slot").count() == 0, "a button holds no button"
    shot(pg, f"concerns-system-{w}.png")


def test_a_step_of_the_loop_and_a_currency_wear_theirs(desk):
    pg, host, w = desk
    loop(pg)
    hold, join, coins = (pg.locator(f'.mp-card[data-id="{i}"]') for i in ("hold-the-tower", "join-a-match", "cur:coins"))
    hold.locator('.cn-mark[data-level="alert"]').wait_for(timeout=WAIT_MS)
    assert hold.locator(".ork-sign.alert").count() == 1 and "knight-elder" in hold.locator(".ork-race__head").get_attribute("src")
    assert hold.locator(".cn-mark").get_attribute("aria-label") == "1 concern of the Game design lead"
    assert join.locator('.cn-mark[data-level="note"] .cn-dot').count() == 1 and coins.locator('.cn-mark[data-level="note"] .cn-dot').count() == 1
    assert pg.locator(".mp-card:not([data-concern])").count() > 0 and pg.locator(".mp-card[data-concern]").count() == 3
    assert hold.locator(".mp-card__nm").bounding_box()["width"] > 0
    shot(pg, f"concerns-loop-{w}.png")


def test_a_map_marked_by_one_record_loses_the_marks_when_the_record_changes(desk):
    pg, host, w = desk
    loop(pg)
    pg.locator(".cn-mark").first.wait_for(timeout=WAIT_MS)
    host.records["game"] = record(copy.deepcopy(GAME[1]))
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.locator('.cn-mark[data-level="alert"]').wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator(".cn-slot").count() == 1 and pg.locator(".mp-card[data-concern]").count() == 1


# -- the strip -----------------------------------------------------------------------------------------------------------------------------------------

def test_the_strip_says_the_counts_with_the_leaders_head_and_the_busy_none_and_failed_states_in_words(desk):
    pg, host, w = desk
    system(pg)
    assert say(pg) == "The Architect: 1 alert, 2 notes Ask again" and "peon-elder" in strip(pg).locator(".ork-race__head").get_attribute("src")
    assert strip(pg).locator(".ork-busy").count() == 0 and strip(pg).get_by_role("button", name="Ask again").is_enabled()
    host.records["tech"] = record(*[concern(f"a{i}", INDEX, "alert", f"alert {i}") for i in range(2)], *[concern(f"n{i}", ROOMS, "note", f"note {i}") for i in range(3)])
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    strip(pg).filter(has_text="2 alerts, 3 notes").wait_for(timeout=WAIT_MS)
    assert say(pg) == "The Architect: 2 alerts, 3 notes Ask again"
    host.records["tech"] = record()
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    strip(pg).filter(has_text="sees nothing wrong").wait_for(timeout=WAIT_MS)
    assert say(pg) == "The Architect sees nothing wrong Ask again" and marks(pg).count() == 0 and pg.locator("[data-concern]").count() == 0
    host.records["tech"] = record(status="looking")
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    strip(pg).filter(has_text="is looking at the map").wait_for(timeout=WAIT_MS)
    assert strip(pg).locator(".ork-busy").count() == 1 and strip(pg).get_by_role("button", name="Ask again").is_disabled()
    assert say(pg).startswith("The Architect is looking at the map…")
    host.records["tech"] = record(status="failed", error="The window of Claude is spent: it will look again after the reset.")
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    strip(pg).filter(has_text="could not look").wait_for(timeout=WAIT_MS)
    assert "The window of Claude is spent: it will look again after the reset." in say(pg) and strip(pg).locator(".ork-busy").count() == 0
    assert strip(pg).get_by_role("button", name="Ask again").is_enabled(), "a failed look can be asked for again"
    shot(pg, f"concerns-strip-failed-{w}.png")


def test_ask_again_sends_the_command_and_the_strip_waits_for_the_look(desk):
    pg, host, w = desk
    system(pg)
    strip(pg).get_by_role("button", name="Ask again").click()
    strip(pg).filter(has_text="is looking at the map").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.concerns_again") == [{"party": "tech"}]
    assert strip(pg).locator(".ork-busy").count() == 1 and strip(pg).get_by_role("button", name="Ask again").is_disabled()
    strip(pg).locator(".ork-busy").wait_for(state="detached", timeout=WAIT_MS * 2)           # the look ends: the page asked again while it was under way
    assert say(pg) == "The Architect: 1 alert, 2 notes Ask again" and len(host.sent("ideas.concerns")) >= 3


def test_a_press_on_the_counts_steps_through_the_marked_cards_the_alerts_first(desk):
    pg, host, w = desk
    system(pg)
    counts = strip(pg).locator(".cn-strip__counts")
    counts.click()
    back(pg).wait_for(timeout=WAIT_MS)
    lower = lambda: pg.keyboard.press("Escape") if wide(w) else back(pg).get_by_role("button", name="Back").click()  # noqa: E731  (narrow: the back is a screen over the strip)
    assert part(pg, LOBBY).get_attribute("aria-pressed") == "true" and back(pg).get_attribute("data-lifted") == f"t:part:tech:{LOBBY}"
    assert pg.evaluate("() => window.__scrolls.at(-1)") == "smooth"
    if not wide(w):
        lower()
        back(pg).wait_for(state="detached", timeout=WAIT_MS)
    counts.click()
    pg.locator(f'.table-back[data-lifted="t:part:tech:{ROOMS}"]').wait_for(timeout=WAIT_MS)                # then the note
    if not wide(w):
        lower()
        back(pg).wait_for(state="detached", timeout=WAIT_MS)
    counts.click()
    pg.locator(f'.table-back[data-lifted="t:part:tech:{LOBBY}"]').wait_for(timeout=WAIT_MS)                # and round again


# -- the card's back -----------------------------------------------------------------------------------------------------------------------------------

def test_a_marked_part_pressed_lifts_and_its_back_lists_each_concern(desk):
    pg, host, w = desk
    system(pg)
    part(pg, LOBBY).click()
    back(pg).locator("[data-concerns-back]").wait_for(timeout=WAIT_MS)
    items = back(pg).locator(".cn-item")
    assert items.count() == 2 and items.nth(0).get_attribute("data-level") == "alert" and items.nth(1).get_attribute("data-level") == "note"
    assert "Every room goes through lobby.ts" in items.nth(0).locator(".cn-item__what").inner_text()
    assert "Eleven parts use it and it holds the sockets too." in items.nth(0).locator(".cn-item__why").inner_text()
    assert "Split the sockets out of it." in items.nth(0).locator(".cn-item__fix").inner_text()
    assert back(pg).locator(".cn-back > .ork-label").inner_text().lower() == "2 concerns of the architect"
    assert items.nth(0).get_by_role("button", name="Make it a goal").get_attribute("class").split().count("primary") == 1
    assert items.nth(0).get_by_role("button", name="Not a problem").count() == 1
    assert back(pg).locator(".table-back__part").count() == 1, "the part's own back is kept"
    shot(pg, f"concerns-back-{w}.png")
    pg.keyboard.press("Escape")
    back(pg).wait_for(state="detached", timeout=WAIT_MS)
    part(pg, INDEX).click()                                                                                 # a part with no concern: today's back alone
    pg.locator(f'.table-back[data-lifted="t:part:tech:{INDEX}"]').wait_for(timeout=WAIT_MS)
    assert back(pg).locator("[data-concerns-back]").count() == 0


def test_a_marked_step_of_the_loop_lifted_lists_its_concern_and_not_a_problem_sends_the_command(desk):
    pg, host, w = desk
    loop(pg)
    pg.locator('.mp-card[data-id="hold-the-tower"] .mp-card__nm').click()
    back(pg).locator("[data-concerns-back]").wait_for(timeout=WAIT_MS)
    assert "Nothing in the loop pays for holding the tower" in back(pg).locator(".cn-item__what").inner_text()
    back(pg).get_by_role("button", name="Not a problem").click()
    back(pg).locator("[data-concerns-back]").wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.concern_dismiss") == [{"party": "game", "id": "g1"}]
    assert pg.locator('.mp-card[data-id="hold-the-tower"][data-concern]').count() == 0 and pg.locator('.mp-card[data-id="hold-the-tower"] .cn-mark').count() == 0
    assert say(pg) == "The Game design lead: 2 notes Ask again"


def test_make_it_a_goal_sends_the_command_and_the_mark_becomes_a_link_to_the_goal_in_its_element(desk):
    pg, host, w = desk
    system(pg)
    part(pg, ROOMS).click()
    back(pg).get_by_role("button", name="Make it a goal").click()
    pg.locator(".cn-mark.is-made").wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.concern_goal") == [{"party": "tech", "id": "c3"}]
    link = pg.locator(".cn-mark.is-made")
    assert link.evaluate("e => e.tagName") == "BUTTON" and link.get_attribute("data-elem") == "ice" and "rooms.ts grows" in link.get_attribute("aria-label")
    ice = pg.evaluate("""() => { const s = document.createElement('i'); s.style.color = 'var(--ork-elem-ice)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }""")
    assert link.evaluate("e => getComputedStyle(e).color") == ice, "the goal's element's colour"
    assert back(pg).locator(".cn-item__goal").count() == 1 and back(pg).get_by_role("button", name="Make it a goal").count() == 0
    pg.keyboard.press("Escape")                                                                             # the back lies over the card: lowered, the mark is pressed
    back(pg).wait_for(state="detached", timeout=WAIT_MS)
    link.click()
    assert "rooms.ts grows" in title(pg), "the goal is picked"
    assert pg.locator(".cn-mark.is-made").count() == 1


# -- the tab -------------------------------------------------------------------------------------------------------------------------------------------

def test_a_party_tab_shows_a_bang_when_its_map_has_an_alert_and_no_count(desk):
    pg, host, w = desk
    pg.locator('.table-tab[data-tab="tech"] .table-tab__alert').wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-tab__alert").count() == 2, "Tech's and Game design's"
    bang = tab(pg, "tech").locator(".table-tab__alert")
    assert bang.locator(".ork-sign.alert").count() == 1 and bang.get_attribute("aria-label") == "The Architect has an alert on the map"
    assert not any(ch.isdigit() for ch in bang.inner_text()) and bang.inner_text().strip() == "", "no count on a tab (decisions §145.3)"
    assert tab(pg, "art").locator(".table-tab__alert").count() == 0 and tab(pg, "orkmaster").locator(".table-tab__alert").count() == 0
    host.records["game"] = record(copy.deepcopy(GAME[1]))                                                      # only a note: no mark
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_function("() => document.querySelectorAll('.table-tab__alert').length === 1", timeout=WAIT_MS)
    assert tab(pg, "game").locator(".table-tab__alert").count() == 0
    shot(pg, f"concerns-tabs-{w}.png")


# -- reduced motion, touch, picking, an older host ----------------------------------------------------------------------------------------------------

def test_nothing_moves_under_reduced_motion(gui):
    pg, host, errors = start(gui, "wide", reduced_motion="reduce")
    try:
        system(pg)
        host.records["tech"]["status"] = "looking"
        host.rev += 1
        host.ws.send(json.dumps(host.snapshot()))
        strip(pg).locator(".ork-busy").wait_for(timeout=WAIT_MS)
        moves = pg.evaluate("""() => [...document.querySelectorAll('.cn-strip, .cn-strip *, .cn-slot, .cn-slot *, .table-tab__alert, .ork-busy')].filter((e) => {
            const s = getComputedStyle(e); const parts = (a) => a.split(',').map((x) => x.trim());
            return s.animationName !== 'none' || parts(s.transitionDuration).some((d) => d !== '0s');
          }).map((e) => e.className)""")
        assert moves == [], moves
        strip(pg).locator(".cn-strip__counts").click()
        assert pg.evaluate("() => window.__scrolls.at(-1)") == "auto", "stepping jumps, it does not glide"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_every_target_is_44_px_at_the_narrow_width(gui):
    pg, host, errors = start(gui, "narrow")
    try:
        loop(pg)                                                                                            # the loop is drawn at its own size (the System's fit scales what it holds)
        for b in strip(pg).locator("button").all():
            assert b.bounding_box()["height"] >= 44, b.inner_text()
        pg.locator('.mp-card[data-id="hold-the-tower"] .mp-card__nm').click()
        back(pg).get_by_role("button", name="Make it a goal").wait_for(timeout=WAIT_MS)
        for b in back(pg).locator(".cn-item .ork-btn").all():
            assert b.bounding_box()["height"] >= 44 and b.bounding_box()["width"] >= 44, b.inner_text()
        back(pg).get_by_role("button", name="Make it a goal").click()
        back(pg).get_by_role("button", name="Back").click()
        back(pg).wait_for(state="detached", timeout=WAIT_MS)
        link = pg.locator(".cn-mark.is-made")
        link.wait_for(timeout=WAIT_MS)
        box = link.bounding_box()
        assert box["width"] >= 43.9 and box["height"] >= 43.9
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_picking_still_works_on_a_marked_card_and_wins_over_the_back(desk):
    pg, host, w = desk
    system(pg)
    open_field(pg)
    pg.locator(".pick-strip").wait_for(timeout=WAIT_MS)
    part(pg, LOBBY).click()
    assert part(pg, LOBBY).get_attribute("data-picked") == "true" and "ork-picked" in part(pg, LOBBY).get_attribute("class")
    assert back(pg).count() == 0, "a press in picking is a pick: the card does not lift"
    assert part(pg, LOBBY).get_attribute("data-concern") == "alert" and pg.locator('.cn-mark[data-level="alert"]').count() == 1
    assert pg.locator('.cn-mark[data-level="alert"]').evaluate("e => getComputedStyle(e).pointerEvents") == "none"
    part(pg, LOBBY).click()
    assert part(pg, LOBBY).get_attribute("data-picked") is None


def test_an_older_host_without_the_commands_shows_no_strip_and_no_mark_and_throws_nothing(gui):
    host = ConcernHost()
    host.older = True
    pg, host, errors = start(gui, "wide", host)
    try:
        go(pg, "tech")
        pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert pg.locator(".cn-strip").count() == 0 and pg.locator(".cn-slot").count() == 0 and pg.locator("[data-concern]").count() == 0
        assert pg.locator(".table-tab__alert").count() == 0 and pg.locator(".ork-toast, .gui-toast").count() == 0
        part(pg, LOBBY).click()
        back(pg).wait_for(timeout=WAIT_MS)
        assert back(pg).locator("[data-concerns-back]").count() == 0
        go(pg, "game")
        pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".cn-strip").count() == 0 and pg.locator(".mp-card[data-concern]").count() == 0
        assert [n for n, _ in host.log if n == "ideas.concerns"], "it asked, and was refused quietly"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_orkmasters_tab_and_a_party_with_no_map_have_no_strip(gui):
    host = ConcernHost()
    host.parties.append(party("ops", len(host.parties)))                                                      # no craft, not led by the Architect: no map
    pg, host, errors = start(gui, "wide", host)
    try:
        go(pg, "game")
        pg.locator(".cn-strip").wait_for(timeout=WAIT_MS)
        go(pg, "ops")
        pg.locator(".table-head").wait_for(timeout=WAIT_MS)
        assert pg.locator(".cn-strip").count() == 0 and not [a for n, a in host.log if n == "ideas.concerns" and a["party"] == "ops"]
        go(pg, "orkmaster")
        assert pg.locator(".cn-strip").count() == 0
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)
