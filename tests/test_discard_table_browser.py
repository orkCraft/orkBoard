"""The discard on the table (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §4, §7; decisions §176.3), in a real browser at the two widths of `tests/narrow.py`: the pile lies in the table's last column (right of the
lanes) at its foot, the hand card's size, with the word *Discard* above it, on the project's tab and on a party's tab (where the party's map ends beside it and scrolls as it did), and not in the hand; its press opens the `discard` face over the pane and
a second press closes it; at the narrow width it lies at the lanes' end (80 px wide), none with nothing done and nothing ready for main, and a card lifted from the hand stands over it.
The table's end at the wide width (docs/specs/110-runes-on-the-table.md §3.2, §3.4, decisions §185): always laid, the portal's ring (asleep with no goal ready for main, open with the portal inside while one is, waking the first time on a device) over the
word *Discard* and the pile, or a dashed place where the pile will lie, which gives way to the pile when a goal is done; the ring's column holds the pile centred under it and nothing overlaps the hand.
Screenshots to $DISCARD_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, node as hand_node, open_hand, sig  # noqa: E402
from tests.test_portal_browser import PortalHost  # noqa: E402
from tests.test_maps_desktop_browser import MapsHost  # noqa: E402
from tests.test_table_desktop_browser import node  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["DISCARD_SHOTS"]) if os.environ.get("DISCARD_SHOTS") else None
CARD = {"wide": (144, 202), "narrow": (80, 112)}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def box(pg, selector):
    return pg.locator(selector).first.bounding_box()


def open_maps(gui, width, done=True):
    """The window against the maps' host (a party of each craft) with goals done, at `width`, on the Orkmaster's tab."""
    server, browser = gui
    host = MapsHost()
    if done:
        host.nodes.append(node("music", "tech", "Lobby music loop", "done", element="void", place="discard", updated="2026-10-20T12:00:00"))
        host.nodes.append(node("codes", "game", "Room codes are four letters", "done", element="dust", place="discard", updated="2026-10-19T12:00:00"))
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_discard_lies_at_the_foot_of_the_projects_last_column_not_in_the_hand(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        assert pg.locator(".hand .hand-done, .hand .table-discard, .hand .table-end").count() == 0, "none in the hand"
        assert pg.locator(".hand-end > :not(.hand-mana):not(.hand-die)").count() == 0, "`.hand-end` holds the Play die and the mana alone (spec 112 §3.3, decisions §190.6)"
        pile, label = box(pg, ".table-discard"), box(pg, ".table-end__label")
        assert pg.locator(".table-end__label").text_content() == "Discard" and label["y"] + label["height"] <= pile["y"] + 1, "the word above the pile"
        assert (round(pile["width"]), round(pile["height"])) == CARD[width], "the hand card's size"
        hand_card = pg.locator(".hand .hand-card").first.bounding_box()
        assert round(hand_card["width"]) == round(pile["width"]), "the same width as a card of the hand"
        body, hand = box(pg, ".table-body"), box(pg, ".hand")
        assert pile["y"] + pile["height"] <= body["y"] + body["height"] and body["y"] + body["height"] - (pile["y"] + pile["height"]) <= 40, "at the column's foot, above the hand"
        assert pile["y"] + pile["height"] <= hand["y"] + 1
        last = box(pg, ".table-lane--free")
        assert pile["x"] >= last["x"] - 1 and pile["x"] + pile["width"] <= last["x"] + last["width"] + 1, "in the last column, right of the lanes"
        if width == "wide":
            ring = box(pg, ".ork-portal-ring")
            assert abs((pile["x"] + pile["width"] / 2) - (ring["x"] + ring["width"] / 2)) <= 1, "centred under the portal's ring (spec 110 §3.2)"
            assert ring["x"] + ring["width"] >= last["x"] + last["width"] - 40, "the ring's column aligned right"
        else:
            assert pile["x"] + pile["width"] >= last["x"] + last["width"] - 40, "aligned right"
        lanes = pg.locator(".table-board .table-lane:not(.table-lane--free)").evaluate_all("els => els.map((e) => e.getBoundingClientRect().right)")
        assert pile["x"] >= max(lanes) - 1, "none of the lanes lies under it"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-project")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_on_a_partys_tab_the_map_ends_beside_the_pile_and_still_scrolls(gui, width):
    pg, host, log = open_maps(gui, width)
    try:
        call(pg, "frame/state.js", "openTab", "art")
        pg.locator(".mp").first.wait_for(timeout=WAIT_MS)
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        pile, pane, head = box(pg, ".table-discard"), box(pg, ".table-body"), box(pg, ".table-head")
        mp = pg.locator(".mp").first
        m = mp.bounding_box()
        assert abs((head["x"] + head["width"]) - (pane["x"] + pane["width"])) <= 2, "the party's header keeps the pane's whole width"
        assert pile["y"] + pile["height"] <= pane["y"] + pane["height"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40, "the pile at the foot"
        if width == "wide":
            assert m["x"] + m["width"] <= pile["x"] + 1, "the map ends before the pile's column"
        else:
            assert m["y"] + m["height"] <= pile["y"] - 10, "the map ends above the pile"
        assert pg.locator(".mp-scroll").first.evaluate("e => getComputedStyle(e).overflowY") == "auto", "the map scrolls as it did"
        assert pg.locator(".table-end").count() == 1
        narrow.no_sideways(pg)
        shot(pg, f"{width}-party-map")
        call(pg, "frame/state.js", "openTab", "orkmaster")                                                                 # the project's tab again: the pile is still there
        pg.wait_for_selector(".table-board", timeout=WAIT_MS)
        assert pg.locator(".table-end .hand-done").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_system_map_of_tech_the_pile_lies_at_the_foot_too(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")
        pg.wait_for_selector(".table-head", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        pile, pane = box(pg, ".table-discard"), box(pg, ".table-body")
        assert pg.locator(".table-end .hand-done").count() == 1 and pile["x"] + pile["width"] <= pane["x"] + pane["width"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40
        shot(pg, "wide-tech")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_piles_press_opens_the_face_over_the_pane_and_a_second_press_closes_it(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert done.get_attribute("aria-expanded") == "false"
        done.click()
        pg.locator("#table-pane .hand-discardview").wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["kind"] == "discard" and "is-on" in done.get_attribute("class") and done.get_attribute("aria-expanded") == "true"
        assert pg.locator("#table-pane .hand-discardview").evaluate("e => e.closest('.table-body') !== null"), "the face lies over the pane"
        shot(pg, f"{width}-discard-open")
        done.click()
        assert sig(pg, "frame/state.js", "over") is None and pg.locator("#table-pane .hand-discardview").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_nothing_done_and_nothing_ready_for_main_is_the_asleep_ring_and_the_place_at_the_wide_width_and_nothing_at_the_narrow(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".table-discard, .hand-done").count() == 0
        if width == "narrow":
            assert pg.locator(".table-end, .table-end__label, .portal-host, .ork-portal-ring, .ork-card-place").count() == 0
        else:
            ring, place, label = pg.locator(".table-end .ork-portal-ring"), pg.locator(".table-end .ork-card-place"), pg.locator(".table-end__label")
            assert ring.count() == 1 and place.count() == 1 and label.text_content() == "Discard"
            r, p, end = ring.bounding_box(), place.bounding_box(), box(pg, ".table-end")
            assert (round(r["width"]), round(r["height"])) == (192, 192), "orkUI's ring"
            assert (round(p["width"]), round(p["height"])) == CARD["wide"], "the place is a card's size"
            assert r["y"] + r["height"] <= label.bounding_box()["y"] + 1 <= p["y"] + 1, "the ring, then the word, then the place"
            assert abs((p["x"] + p["width"] / 2) - (r["x"] + r["width"] / 2)) <= 1 and p["x"] + p["width"] <= end["x"] + end["width"] + 1
            assert "is-open" not in ring.get_attribute("class") and "is-sealed" not in ring.get_attribute("class") and ring.get_attribute("aria-hidden") == "true", "asleep"
            assert pg.locator(".table-end .ork-portal").count() == 0 and pg.locator(".table-end button, .table-end [tabindex]").count() == 0, "nothing to press: no portal inside, the place is no button"
            assert pg.locator(".portal-host").get_attribute("data-portal") == "asleep" and "is-asleep" in pg.locator(".portal-host").get_attribute("class")
            assert pg.locator(".portal__label").text_content() == "Main" and pg.locator(".portal__line, .portal__hint").count() == 0
            assert pg.locator(".ork-portal-ring__seal > *").count() == 0, "no goal's rune in the seal"
            assert pg.evaluate("() => getComputedStyle(document.querySelector('.portal__label')).color") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-ink-faint)'; document.body.append(s); const c = getComputedStyle(s).color; s.remove(); return c; }"), "*Main* in the faint ink"
            assert p["y"] + p["height"] <= box(pg, ".hand")["y"] + 1, "nothing overlaps the hand"
            shot(pg, "wide-asleep-and-place")
            place.click(force=True)
            pg.wait_for_timeout(200)
            assert sig(pg, "frame/state.js", "over") is None, "pressed, the place does nothing"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_ready_for_main_alone_is_a_back_and_at_the_wide_width_the_ring_is_open(gui, width):
    host = HandHost()                                                                                                       # two goals ready for main, none done to see: that line alone on a back
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    pg, host, log = open_hand(gui, host=host, width=width)
    try:
        back = pg.locator(".table-end .hand-done.ork-card-back")
        back.wait_for(timeout=WAIT_MS)
        assert back.get_attribute("aria-label") == "Done. 2 goals ready for main" and pg.locator(".table-end__label").text_content() == "Discard"
        assert pg.locator(".ork-card-place").count() == 0, "a pile is there: no place"
        if width == "wide":
            assert "is-open" in pg.locator(".ork-portal-ring").get_attribute("class")
        else:
            assert pg.locator(".ork-portal-ring, .portal-host").count() == 0, "the narrow width opens the portal when a goal is chosen"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_ready_for_main_opens_the_ring_with_the_portal_inside_and_it_wakes_the_first_time_on_a_device_only(gui):
    pg, host, log = open_hand(gui)
    try:
        ring, door = pg.locator(".ork-portal-ring"), pg.locator(".ork-portal-ring > .ork-portal")
        door.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        klass = ring.get_attribute("class").split()
        assert "is-open" in klass and "is-waking" in klass and "is-sealed" not in klass, "open, and waking: the first time on this device"
        assert door.evaluate("e => e.tagName") == "BUTTON" and "is-new" in door.get_attribute("class") and "small" not in door.get_attribute("class")
        assert door.get_attribute("aria-label") == "Choose a goal done to send it to main"
        assert pg.locator(".portal-host").get_attribute("data-portal") == "ready" and pg.locator(".portal__line").count() == 0, "no goal chosen: no line"
        assert pg.locator(".ork-portal-ring__seal > *").count() == 0, "no goal chosen: nothing in the seal"
        r, d = ring.bounding_box(), door.bounding_box()
        assert r["x"] <= d["x"] and d["x"] + d["width"] <= r["x"] + r["width"] and r["y"] <= d["y"] and d["y"] + d["height"] <= r["y"] + r["height"], "the portal lies inside the ring"
        assert pg.locator(".portal__hint").text_content() == "Drag a goal done into the portal to send it to main"
        assert pg.evaluate("() => localStorage.getItem('orkboard.portal.seen')") == "1", "the device has seen it"
        pg.wait_for_timeout(1600)                                                                                           # the runes and the eye have opened
        shot(pg, "wide-ring-open")
        pg.reload()                                                                                                          # the second time on this device: open, not waking
        pg.locator(".ork-portal-ring > .ork-portal").wait_for(timeout=WAIT_MS)
        klass = ring.get_attribute("class").split()
        assert "is-open" in klass and "is-waking" not in klass and "is-new" not in pg.locator(".ork-portal-ring > .ork-portal").get_attribute("class")
        assert pg.locator(".portal__hint").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_ring_wakes_when_the_first_goal_becomes_ready_and_sleeps_when_none_is_left(gui):
    host = HandHost()
    ready = host.gate_doc["ideas"]
    host.gate_doc = {**host.gate_doc, "ideas": [], "commits": 0, "files": 0, "same": False}
    pg, host, log = open_hand(gui, host=host)
    try:
        pg.locator(".ork-portal-ring").wait_for(timeout=WAIT_MS)
        assert "is-open" not in pg.locator(".ork-portal-ring").get_attribute("class") and pg.locator(".ork-portal-ring > .ork-portal").count() == 0, "asleep with nothing ready"
        host.gate_doc = {**host.gate_doc, "ideas": ready, "commits": 5, "files": 9, "same": False}
        host.bump({})
        pg.locator(".ork-portal-ring.is-open > .ork-portal").wait_for(timeout=WAIT_MS)
        assert "is-waking" in pg.locator(".ork-portal-ring").get_attribute("class")
        host.gate_doc = {**host.gate_doc, "ideas": [], "commits": 0, "files": 0, "same": False}
        host.bump({})
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring > .ork-portal')", timeout=WAIT_MS)
        assert "is-open" not in pg.locator(".ork-portal-ring").get_attribute("class") and pg.locator(".portal-host").get_attribute("data-portal") == "asleep"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pressing_the_open_portal_with_no_goal_chosen_opens_the_discards_view(gui):
    pg, host, log = open_hand(gui)
    try:
        door = pg.locator(".ork-portal-ring > .ork-portal")
        door.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert sig(pg, "frame/state.js", "over") is None
        door.click()
        pg.locator("#table-pane .hand-discardview").wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "over")["kind"] == "discard" and pg.locator(".portal-cards [data-portal-card]").count() == 2
        assert [n for n, _ in host.log if n == "ideas.to_main"] == [], "nothing was sent: no goal was chosen"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_place_gives_way_to_the_pile_when_a_goal_is_done(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True))
    try:
        pg.locator(".table-end .ork-card-place").wait_for(timeout=WAIT_MS)
        host.nodes.append(hand_node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00"))
        host.bump({})
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        assert pg.locator(".ork-card-place").count() == 0 and pg.locator(".table-discard").count() == 1
        pile, ring = box(pg, ".table-discard"), box(pg, ".ork-portal-ring")
        assert (round(pile["width"]), round(pile["height"])) == CARD["wide"] and ring["y"] + ring["height"] <= pile["y"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("size", [(1280, 800), (1024, 768)])
def test_nothing_of_the_end_overlaps_the_hand_or_leaves_the_table_with_a_goal_chosen_and_a_card_lifted(gui, size):
    server, browser = gui
    host = PortalHost()
    pg = browser.new_context(viewport={"width": size[0], "height": size[1]}).new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        door = pg.locator(".ork-portal-ring > .ork-portal")
        door.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        door.click()                                                                                                        # no goal chosen: the discard's view, where one is
        pg.locator(".portal-cards").wait_for(timeout=WAIT_MS)
        pg.locator('[data-portal-card="menu"]').click()                                                                     # the sealed one: the line, the ring sealed, the reason under it
        pg.wait_for_function("() => document.querySelector('.portal-host')?.dataset.portal === 'sealed'", timeout=WAIT_MS)
        pg.locator(".hand .hand-slot").last.hover()                                                                         # a card of the hand risen
        pg.wait_for_timeout(500)
        end, hand, body = box(pg, ".table-end"), box(pg, ".hand"), box(pg, ".table-body")
        assert end["y"] + end["height"] <= hand["y"] + 1, "above the hand"
        assert end["y"] >= body["y"] - 1, "the line and the reason lie inside the table's body"
        assert end["x"] + end["width"] <= body["x"] + body["width"] + 1
        shot(pg, f"{size[0]}x{size[1]}-end-sealed")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_pile_leans_and_rises_on_hover_like_a_card(gui):
    pg, host, log = open_hand(gui)
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(500)
        assert "ork-leans" in done.get_attribute("class")
        y0 = done.bounding_box()["y"]
        done.hover()
        pg.wait_for_timeout(500)
        assert done.bounding_box()["y"] < y0, "it rises under the pointer"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discard_is_seen_through_the_result_and_leaves_the_pile(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".table-end .hand-done").click()
        pane = pg.locator("#table-pane")
        pane.get_by_role("region", name="Done, not yet seen").locator('.hand-drow[data-slug="codes"]').click()
        assert sig(pg, "frame/state.js", "over")["kind"] == "result"
        assert host.seen_log == ["codes"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_card_lifted_from_the_hand_stands_over_the_pile(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="failed"]').first.click(position={"x": 10, "y": 20})
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        z = pg.evaluate("() => [getComputedStyle(document.querySelector('.hand')).zIndex, getComputedStyle(document.querySelector('.table-end')).zIndex].map(Number)")
        assert z[0] > z[1], "the hand's layer is above the pile's"
        l, p = lifted.bounding_box(), pg.locator(".table-discard").bounding_box()
        x0, x1 = max(l["x"], p["x"]), min(l["x"] + l["width"], p["x"] + p["width"])
        y0, y1 = max(l["y"], p["y"]), min(l["y"] + l["height"], p["y"] + p["height"])
        if x1 > x0 and y1 > y0:                                                                                              # where they meet, the card is on top
            assert pg.evaluate("([x, y]) => document.elementFromPoint(x, y)?.closest('.hand-lifted') !== null", [(x0 + x1) / 2, (y0 + y1) / 2])
        elif width == "narrow":
            pytest.fail("at the narrow width the lifted card spans the screen and meets the pile")
        shot(pg, f"{width}-lifted-over-the-pile")
    finally:
        pg.close()
    assert not log, "\n".join(log)
