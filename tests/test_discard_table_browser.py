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
        done = pg.locator(":is(.frame-edge, .table-end) .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        assert pg.locator(".hand .hand-done, .hand .table-discard, .hand .table-end").count() == 0, "none in the hand"
        assert pg.locator(".hand-end > :not(.hand-mana):not(.hand-die)").count() == 0, "`.hand-end` holds the Play die and the mana alone (spec 112 §3.3, decisions §190.6)"
        if width == "wide":
            assert pg.locator(".hand-end").count() == 0 and pg.locator(".frame-edge > .edge-discard .table-discard").count() == 1, "at the wide width the pile lies in the table's edge, the hand has no end (spec 150 D.2)"
        pile, label = box(pg, ".table-discard"), box(pg, ".table-end__label")
        assert pg.locator(".table-end__label").text_content() == "Discard" and label["y"] + label["height"] <= pile["y"] + 1, "the word above the pile"
        assert (round(pile["width"]), round(pile["height"])) == CARD[width], "the hand card's size"
        hand_card = pg.locator(".hand .hand-card").first.bounding_box()
        assert round(hand_card["width"]) == round(pile["width"]), "the same width as a card of the hand"
        body, hand = box(pg, ".table-body"), box(pg, ".hand")
        if width == "wide":
            edge, ring, die = box(pg, ".frame-edge"), box(pg, ".ork-portal-ring"), box(pg, ".frame-edge > .hand-die")
            assert edge["x"] <= pile["x"] and pile["x"] + pile["width"] <= edge["x"] + edge["width"] and pile["y"] >= edge["y"] and pile["y"] + pile["height"] <= edge["y"] + edge["height"], "in the table's edge"
            assert abs((pile["x"] + pile["width"] / 2) - (ring["x"] + ring["width"] / 2)) <= 1, "centred under the portal's ring (spec 110 §3.2)"
            assert ring["y"] + ring["height"] <= label["y"] + 1 and pile["y"] + pile["height"] <= die["y"] + 1, "under the ring, over the die"
            assert pile["x"] >= body["x"] + body["width"] - 1, "none of the table lies under it: the table ends where the edge begins"
        else:
            assert pile["y"] + pile["height"] <= body["y"] + body["height"] and body["y"] + body["height"] - (pile["y"] + pile["height"]) <= 40, "at the column's foot, above the hand"
            assert pile["y"] + pile["height"] <= hand["y"] + 1
            last = box(pg, ".table-lane--free")
            assert pile["x"] >= last["x"] - 1 and pile["x"] + pile["width"] <= last["x"] + last["width"] + 1, "in the last column, right of the lanes"
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
        pg.locator(":is(.frame-edge, .table-end) .hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        pile, pane, head = box(pg, ".table-discard"), box(pg, ".table-body"), box(pg, ".table-head")
        mp = pg.locator(".mp").first
        m = mp.bounding_box()
        assert abs((head["x"] + head["width"]) - (pane["x"] + pane["width"])) <= 2, "the party's header keeps the pane's whole width"
        if width == "wide":
            assert pile["x"] >= pane["x"] + pane["width"] - 1 and m["x"] + m["width"] <= pile["x"] + 1, "the map ends before the pile's column: the edge's"
        else:
            assert pile["y"] + pile["height"] <= pane["y"] + pane["height"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40, "the pile at the foot"
            assert m["y"] + m["height"] <= pile["y"] - 10, "the map ends above the pile"
        assert pg.locator(".mp-scroll").first.evaluate("e => getComputedStyle(e).overflowY") == "auto", "the map scrolls as it did"
        assert pg.locator(".frame-edge" if width == "wide" else ".table-end").count() == 1
        narrow.no_sideways(pg)
        shot(pg, f"{width}-party-map")
        call(pg, "frame/state.js", "openTab", "orkmaster")                                                                 # the project's tab again: the pile is still there
        pg.wait_for_selector(".table-board", timeout=WAIT_MS)
        assert pg.locator(":is(.frame-edge, .table-end) .hand-done").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_the_system_map_of_tech_the_pile_lies_at_the_foot_too(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(":is(.frame-edge, .table-end) .hand-done").wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")
        pg.wait_for_selector(".table-head", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        pile, pane = box(pg, ".table-discard"), box(pg, ".table-body")
        edge = box(pg, ".frame-edge")
        assert pg.locator(":is(.frame-edge, .table-end) .hand-done").count() == 1 and pile["x"] >= pane["x"] + pane["width"] - 1 and pile["x"] + pile["width"] <= edge["x"] + edge["width"] and pile["y"] + pile["height"] <= edge["y"] + edge["height"], "the pile lies in the edge, at the table's right"
        shot(pg, "wide-tech")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_piles_press_opens_the_face_over_the_pane_and_a_second_press_closes_it(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(":is(.frame-edge, .table-end) .hand-done")
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
def test_nothing_done_and_nothing_ready_for_main_lays_no_end_at_either_width_and_the_table_gains_the_width(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".table-discard, .hand-done").count() == 0
        assert pg.locator(".table-end, .table-end__label, .edge-discard, .ork-card-place").count() == 0, "no pile, no frame, no word (decisions §247.1)"
        assert pg.locator(".portal-host, .ork-portal-ring").count() == (2 if width == "wide" else 0), "the ring (and its host) is always drawn from Start at the wide width (spec 150 D.3), asleep; the narrow width has none"
        assert pg.locator(".portal__label, .ork-portal-ring.is-open").count() == 0, "asleep: no word, not open"
        call(pg, "frame/state.js", "openTab", "tech")
        pg.locator('.table-tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-body").evaluate("e => getComputedStyle(e).paddingRight") == "0px", "the room kept for the end is given back to the party's map"
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
        back = pg.locator(":is(.frame-edge, .table-end) .hand-done.ork-card-back")
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


def test_the_ring_is_drawn_when_the_first_goal_becomes_ready_and_goes_when_none_is_left(gui):
    host = HandHost()
    ready = host.gate_doc["ideas"]
    host.gate_doc = {**host.gate_doc, "ideas": [], "commits": 0, "files": 0, "same": False}
    pg, host, log = open_hand(gui, host=host)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".ork-portal-ring").count() == 1 and pg.locator(".portal__label, .ork-portal-ring.is-open").count() == 0 and "is-asleep" in pg.locator(".portal-host").get_attribute("class"), "nothing ready: the ring asleep, no word (spec 150 D.3)"
        host.gate_doc = {**host.gate_doc, "ideas": ready, "commits": 5, "files": 9, "same": False}
        host.bump({})
        pg.locator(".ork-portal-ring.is-open > .ork-portal").wait_for(timeout=WAIT_MS)
        assert "is-waking" in pg.locator(".ork-portal-ring").get_attribute("class") and pg.locator(".portal__label").text_content() == "Main"
        host.gate_doc = {**host.gate_doc, "ideas": [], "commits": 0, "files": 0, "same": False}
        host.bump({})
        pg.wait_for_function("() => !document.querySelector('.ork-portal-ring.is-open')", timeout=WAIT_MS)
        assert pg.locator(".portal__label").count() == 0 and pg.locator(".ork-portal-ring").count() == 1 and "is-asleep" in pg.locator(".portal-host").get_attribute("class"), "none left: the ring goes back to sleep and stays"
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


def test_the_discard_is_drawn_from_its_first_goal_done_and_not_before(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True))
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-end, .edge-discard, .ork-card-place, .table-end__label").count() == 0, "empty: nothing lies there"
        host.nodes.append(hand_node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00"))
        host.bump({})
        pg.locator(":is(.frame-edge, .table-end) .hand-done").wait_for(timeout=WAIT_MS)
        assert pg.locator(".ork-card-place").count() == 0 and pg.locator(".table-discard").count() == 1 and pg.locator(".table-end__label").text_content() == "Discard"
        pile = box(pg, ".table-discard")
        assert (round(pile["width"]), round(pile["height"])) == CARD["wide"] and pg.locator(".ork-portal-ring.is-open").count() == 0, "nothing ready for main: the pile, the ring asleep"
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
        end, hand, body, ring = box(pg, ".frame-edge"), box(pg, ".hand"), box(pg, ".table-body"), box(pg, ".frame-edge > .portal-host")
        assert end["x"] >= hand["x"] + hand["width"] - 1, "the edge lies beside the hand, not over it"
        assert ring["y"] >= end["y"] - 1 and ring["y"] + ring["height"] <= end["y"] + end["height"] + 1, "the line and the reason lie inside the edge"
        assert end["x"] >= body["x"] + body["width"] - 1 and end["x"] + end["width"] <= size[0] + 1
        assert pg.evaluate("() => { const e = document.querySelector('.frame-edge'); return e.scrollHeight <= e.clientHeight; }"), "nothing of the edge scrolls"
        shot(pg, f"{size[0]}x{size[1]}-end-sealed")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_pile_leans_and_rises_on_hover_like_a_card(gui):
    pg, host, log = open_hand(gui)
    try:
        done = pg.locator(":is(.frame-edge, .table-end) .hand-done")
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


def test_ready_for_main_and_its_to_main_lie_above_done_not_yet_seen(gui):
    """Spec 155 G.4: with goals done and goals ready, the discard's face shows *Ready for main* with its **To main** first, *Done, not yet seen* under it."""
    pg, host, log = open_hand(gui)
    try:
        pg.locator(":is(.frame-edge, .table-end) .hand-done").click()
        pane = pg.locator("#table-pane")
        ready, done = pane.get_by_role("region", name="Ready for main"), pane.get_by_role("region", name="Done, not yet seen")
        ready.wait_for(timeout=WAIT_MS)
        done.wait_for(timeout=WAIT_MS)
        assert ready.locator("[data-to-main]").bounding_box()["y"] < done.bounding_box()["y"]
        assert ready.bounding_box()["y"] < done.bounding_box()["y"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discard_is_seen_through_the_result_and_leaves_the_pile(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(":is(.frame-edge, .table-end) .hand-done").click()
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
        pg.locator(":is(.frame-edge, .table-end) .hand-done").wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="failed"]').first.click(position={"x": 10, "y": 20})
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        z = pg.evaluate("() => [getComputedStyle(document.querySelector('.hand')).zIndex, getComputedStyle(document.querySelector('.frame-edge, .table-end')).zIndex].map(Number)")
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


def test_the_piles_words_stay_inside_its_card_and_the_whole_sentence_is_its_title(gui):
    """Spec 143 F.5 (decisions §250.7): what is ready for main, said on the back of the pile (no goal done to show), wraps inside the card's art and is cut with its whole sentence in `title`, however long the branch's name."""
    server, browser = gui
    host = HandHost()
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    host.gate_doc = {"into": "dev", "main": "release-candidate-2026", "same": False, "commits": 12, "files": 9, "ideas": []}
    pg = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.wait_for_selector(".table-discard .hand-back__ready .cap", timeout=WAIT_MS)
        cap, card = pg.locator(".table-discard .hand-back__ready .cap"), pg.locator(".table-discard .hand-done").first
        c, k = cap.bounding_box(), card.bounding_box()
        assert c["x"] >= k["x"] + 12 and c["x"] + c["width"] <= k["x"] + k["width"] - 12, f"the words lie inside the frame of the art: {c} in {k}"
        assert cap.evaluate("e => e.scrollWidth <= e.clientWidth + 1"), "no word runs past its line"
        assert cap.get_attribute("title") == "12 commits ready for release-candidate-2026", "the whole sentence is its title"
        shot(pg, "wide-discard-words")
    finally:
        pg.context.close()


def test_at_the_narrow_width_the_piles_words_wrap_inside_its_window_not_cut(gui):
    """Spec 149 G.5 (decisions §250.7, §253.8): at the narrow width (a pile 80 px wide) *12 commits ready for main* was cut at the card's edge (*1 commi*, *ready for*): every word lies whole inside the card, wrapped, and no line is cut."""
    server, browser = gui
    host = HandHost()
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    host.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 12, "files": 9, "ideas": []}
    pg = narrow.page(browser, "narrow")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.wait_for_selector(".table-discard .hand-back__ready .cap", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        cap, card = pg.locator(".table-discard .hand-back__ready .cap"), pg.locator(".table-discard .hand-done").first
        c, k = cap.bounding_box(), card.bounding_box()
        shot(pg, "narrow-discard-words")
        assert cap.text_content() == "12 commits ready for main" and cap.get_attribute("title") == "12 commits ready for main"
        assert c["x"] >= k["x"] - 1 and c["x"] + c["width"] <= k["x"] + k["width"] + 1, f"the words lie inside the card: {c} in {k}"
        assert cap.evaluate("e => e.scrollWidth <= e.clientWidth + 1 && e.scrollHeight <= e.clientHeight + 1"), f"no word is cut: {cap.evaluate('e => [e.scrollWidth, e.clientWidth, e.scrollHeight, e.clientHeight]')}"
        inside = """() => { const r = document.createRange(), n = document.querySelector('.table-discard .hand-back__ready .cap'), k = document.querySelector('.table-discard .hand-done').getBoundingClientRect();
            r.selectNodeContents(n); return [...r.getClientRects()].every((q) => q.left >= k.left + 10 && q.right <= k.right - 10 && q.top >= k.top + 8 && q.bottom <= k.bottom - 8); }"""
        assert pg.evaluate(inside), "every line of the words is drawn inside the art's window (10 px in from the card's sides, 8 px from its top and foot)"
    finally:
        pg.context.close()
