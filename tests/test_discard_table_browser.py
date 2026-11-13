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

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand, sig  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["DISCARD_SHOTS"]) if os.environ.get("DISCARD_SHOTS") else None
CARD = {"wide": (144, 202), "narrow": (80, 112)}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def box(pg, selector):
    return pg.locator(selector).first.bounding_box()




NARROW = ("narrow",)


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








# -- Release's lane at the wide width (spec 156 D.3) ------------------------------------------------------------------------------------------


class LaneHost(HandHost):
    """HandHost with Release a party of the release craft and one goal ready for main (Lobby music loop, Tech's): Room codes (Design's) is done and not yet seen."""

    def __init__(self, **more):
        super().__init__(**more)
        for p in self.parties:
            if p["slug"] == "release":
                p["party_craft"] = "release"
        self.gate_doc["ideas"] = [g for g in self.gate_doc["ideas"] if g["slug"] == "music"]


def open_lane(gui, host=None):
    pg, host, log = open_hand(gui, host=host or LaneHost(), width="wide")
    pg.locator(".release-lane .post-card").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(400)
    return pg, host, log


def picked(pg, slug):
    pg.wait_for_function("(s) => import('/static/js/frame/state.js').then((m) => m.picked.value === s)", arg=slug, timeout=WAIT_MS)
