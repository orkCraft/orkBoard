"""**At 760 px and up the discard is Release's lane** (docs/specs/156-one-pick-and-the-release-column.md D.3, decisions §261.7): beside the pane on every tab, its label *Discard* or *<party>'s discard*, the goals done through the open tab's eyes (Tech's
tab holds Tech's goals only), each card whole and **picked** (no `discard` view over the pane; `ideas.seen` sent when a card not yet seen is picked), the goal ready for main on top. The tests of the lane are at the end of this file; the pile before them is the narrow width's.
The discard on the table (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §4, §7; decisions §176.3), in a real browser at the two widths of `tests/narrow.py`: the pile lies in the table's last column (right of the
lanes) at its foot, the hand card's size, with the word *Discard* above it, on the project's tab and on a party's tab (where the party's map ends beside it and scrolls as it did), and not in the hand; its press opens the `discard` face over the pane and
a second press closes it; at the narrow width it lies at the lanes' end (80 px wide), none with nothing done and nothing ready for main, and a card lifted from the hand stands over it.
The table's end at the wide width (docs/specs/110-runes-on-the-table.md §3.2, §3.4, decisions §185): always laid, the portal's ring (asleep with no goal ready for main, open with the portal inside while one is, waking the first time on a device) over the
word *Discard* and the pile, or a dashed place where the pile will lie, which gives way to the pile when a goal is done; the ring's column holds the pile centred under it and nothing overlaps the hand.
Screenshots to $DISCARD_SHOTS when it is set.

Goal 170 B (decisions §293.4): in the lane every goal is a post drawn by table/post.js (`.post-card`), its goal's name a button that picks it, the ready one ringed by the portal with *To main*. Removed or changed for the posts: test_the_pile_leans_and_rises_on_hover_like_a_card
had the lane's cards lean (`.ork-leans`, a hand card's move); a post does not lean, its act (the card is told apart under the pointer and reached) is held by test_a_post_of_the_lane_is_a_post_with_a_visible_focus_and_its_goal_reached_by_tab; the 144 x 202 card size of the lane
is now one post of the lane's width, held by test_the_goal_ready_for_main_lies_on_top_...; every press of a card is the press of the post's goal name, held by the two tests of picking at the head of the lane's part."""
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


NARROW = ("narrow",)


@pytest.mark.parametrize("width", NARROW)
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
        assert pile["x"] + pile["width"] >= last["x"] + last["width"] - 40, "aligned right"
        lanes = pg.locator(".table-board .table-lane:not(.table-lane--free)").evaluate_all("els => els.map((e) => e.getBoundingClientRect().right)")
        assert pile["x"] >= max(lanes) - 1, "none of the lanes lies under it"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-project")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", NARROW)
def test_on_a_partys_tab_the_map_ends_beside_the_pile_and_still_scrolls(gui, width):
    pg, host, log = open_maps(gui, width)
    try:
        call(pg, "frame/state.js", "openTab", "art")
        pg.locator(".mp").first.wait_for(timeout=WAIT_MS)
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(600)
        pile, pane, head = box(pg, ".table-discard"), box(pg, ".table-body"), box(pg, ".table-head")
        m = pg.locator(".mp").first.bounding_box()
        assert abs((head["x"] + head["width"]) - (pane["x"] + pane["width"])) <= 2, "the party's header keeps the pane's whole width"
        assert pile["y"] + pile["height"] <= pane["y"] + pane["height"] and pane["y"] + pane["height"] - (pile["y"] + pile["height"]) <= 40, "the pile at the foot"
        assert m["y"] + m["height"] <= pile["y"] - 10, "the map ends above the pile"
        assert pg.locator(".mp-scroll").first.evaluate("e => getComputedStyle(e).overflowY") == "auto", "the map scrolls as it did"
        narrow.no_sideways(pg)
        shot(pg, f"{width}-party-map")
        call(pg, "frame/state.js", "openTab", "orkmaster")                                                                 # the project's tab again: the pile is still there
        pg.wait_for_selector(".table-board", timeout=WAIT_MS)
        assert pg.locator(".table-end .hand-done").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", NARROW)
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


def test_nothing_done_and_nothing_ready_for_main_lays_no_end_at_the_narrow_width_and_the_wide_lane_is_empty_with_no_ring(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width="narrow")
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".table-discard, .hand-done, .table-end, .table-end__label, .ork-card-place, .portal-host, .ork-portal-ring").count() == 0, "no pile, no frame, no word (decisions §247.1)"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width="wide")
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        assert pg.locator(".release-lane").count() == 1 and pg.locator(".release-lane .post-card, .release-lane .ork-portal-ring, .release-lane [data-portal-card]").count() == 0, "the lane is there and holds no post and no ring"
        assert pg.locator(".table-end, .frame-edge").count() == 0
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_ready_for_main_alone_is_a_back_at_the_narrow_width(gui):
    host = HandHost()                                                                                                       # two goals ready for main, none done to see: that line alone on a back
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    pg, host, log = open_hand(gui, host=host, width="narrow")
    try:
        back = pg.locator(".table-end .hand-done.ork-card-back")
        back.wait_for(timeout=WAIT_MS)
        assert back.get_attribute("aria-label") == "Done. 2 goals ready for main" and pg.locator(".table-end__label").text_content() == "Discard"
        assert pg.locator(".ork-card-place").count() == 0, "a pile is there: no place"
        assert pg.locator(".ork-portal-ring, .portal-host").count() == 0, "the narrow width opens the portal when a goal is chosen"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_discard_is_drawn_from_its_first_goal_done_and_not_before_at_the_narrow_width(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width="narrow")
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.locator(".table-end, .ork-card-place, .table-end__label").count() == 0, "empty: nothing lies there"
        host.nodes.append(hand_node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00"))
        host.bump({})
        pg.locator(".table-end .hand-done").wait_for(timeout=WAIT_MS)
        assert pg.locator(".ork-card-place").count() == 0 and pg.locator(".table-discard").count() == 1 and pg.locator(".table-end__label").text_content() == "Discard"
        pile = box(pg, ".table-discard")
        assert (round(pile["width"]), round(pile["height"])) == CARD["narrow"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_post_of_the_lane_is_a_post_with_a_visible_focus_and_its_goal_reached_by_tab(gui):
    """Holds the act of the former test of a card leaning under the pointer: the lane's card is told apart and reached (a post, not a hand card)."""
    pg, host, log = open_lane_wide(gui)
    try:
        first = pg.locator(".release-lane .post-card").first
        assert "ork-card" in first.get_attribute("class") and first.get_attribute("data-race"), "orkUI's card, its party's colour its top edge"
        assert pg.locator(".release-lane .ork-leans, .release-lane .hand-done").count() == 0, "no hand card in the lane"
        first.focus()
        assert first.evaluate("e => getComputedStyle(e).boxShadow") != "none", "a focus shows"
        button = first.locator(".post-card__goal")
        button.focus()
        assert button.evaluate("e => e === document.activeElement") and button.inner_text().strip(), "the goal's name is a button with its word"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_lifted_from_the_hand_stands_over_the_pile(gui):
    pg, host, log = open_hand(gui, width="narrow")
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
        else:
            pytest.fail("at the narrow width the lifted card spans the screen and meets the pile")
        shot(pg, "narrow-lifted-over-the-pile")
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


# -- Release's lane at the wide width (spec 156 D.3) ------------------------------------------------------------------------------------------


class LaneHost(HandHost):
    """HandHost with Release a party of the release craft and one goal ready for main (Lobby music loop, Tech's): Room codes (Design's) is done and not yet seen."""

    def __init__(self, **more):
        super().__init__(**more)
        for p in self.parties:
            if p["slug"] == "release":
                p["party_craft"] = "release"
        self.gate_doc["ideas"] = [g for g in self.gate_doc["ideas"] if g["slug"] == "music"]


def open_lane_wide(gui):
    return open_lane(gui)


def open_lane(gui, host=None):
    pg, host, log = open_hand(gui, host=host or LaneHost(), width="wide")
    pg.locator(".release-lane .post-card").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(400)
    return pg, host, log


def picked(pg, slug):
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)


def test_on_techs_tab_the_lane_holds_techs_goals_only_its_label_is_techs_discard_and_a_card_pressed_is_picked_with_no_discard_over(gui):
    pg, host, log = open_lane(gui)
    try:
        call(pg, "frame/state.js", "openTab", "tech")
        pg.locator('.table-tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".release-lane__label").text_content() == "Tech's discard"
        assert pg.locator(".release-lane .post-card[data-slug]").evaluate_all("els => els.map((e) => e.dataset.slug)") == ["music"], "Tech's goal only (Design's Room codes is not here)"
        pg.locator('.release-lane .post-card[data-slug="music"] .post-card__goal').click()
        picked(pg, "music")
        assert sig(pg, "frame/state.js", "over") is None and pg.locator('[data-kind="discard"], .hand-discardview').count() == 0, "no discard view over the pane"
        assert pg.locator('.release-lane .post-card[data-slug="music"]').get_attribute("data-picked") == "true"
        assert sig(pg, "frame/state.js", "tab") == "tech", "Tech's tab is on the goal's route"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_done_and_not_seen_pressed_is_picked_and_told_to_the_host_as_seen_and_put_away_by_esc(gui):
    pg, host, log = open_lane(gui)
    try:
        pg.locator('.release-lane__done [data-slug="codes"] .post-card__goal').click()
        picked(pg, "codes")
        pg.wait_for_function("() => true")
        assert host.seen_log == ["codes"], "`ideas.seen` is sent when the card is picked"
        assert sig(pg, "frame/state.js", "over") is None and pg.locator(".hand-discardview").count() == 0
        pg.wait_for_selector('.release-lane__done [data-slug="codes"]', state="detached", timeout=WAIT_MS)       # a goal seen leaves *not yet seen*
        pg.keyboard.press("Escape")
        picked(pg, "")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_goal_ready_for_main_lies_on_top_of_the_goals_not_seen_in_the_hands_card_size(gui):
    pg, host, log = open_lane(gui)
    try:
        ready, seen = box(pg, '.release-lane [data-portal-card="music"]'), box(pg, '.release-lane__done [data-slug="codes"]')
        assert ready["y"] < seen["y"] and round(ready["width"]) == round(seen["width"]) and ready["width"] > CARD["wide"][0], "top to bottom, whole posts of the lane's width"
        assert pg.locator(".release-lane .portal-host.is-ring .ork-portal-ring").count() == 1 and pg.locator(".release-lane__done .ork-portal-ring").count() == 0, "the ring lies round the top post alone"
        assert pg.locator('.release-lane .post-card[data-portal-card="music"]').get_attribute("data-portal") == "1" and pg.locator(".release-lane .post-card[data-portal]").count() == 1, "the portal's colour rings the top ready post alone"
        assert pg.locator('.release-lane [data-portal-card="music"] [data-act="to_main"]').inner_text().strip() == "To main"
        shot(pg, "wide-lane")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_lane_ends_over_the_hand_and_the_pane_ends_where_the_lane_begins(gui):
    pg, host, log = open_lane(gui)
    try:
        lane, hand, pane = box(pg, ".release-lane"), box(pg, ".hand"), box(pg, "#table-pane")
        assert lane["y"] + lane["height"] <= hand["y"] + 1, "the lane ends over the hand"
        assert round(pane["x"] + pane["width"]) == round(lane["x"])
        assert pg.evaluate("() => { const e = document.querySelector('.release-lane__scroll'); return e.scrollWidth <= e.clientWidth; }"), "nothing of the lane scrolls sideways"
    finally:
        pg.close()
    assert not log, "\n".join(log)
