"""Spec 168 H3 (decisions §283.32): the morning's proposal on the page, in a real browser against the concerns' stub host. A proposal waiting is a Needs-you row of `kind: "night_proposal"` and its goal lies on Hold: the card is in the proposing
leader's stack in the hand (wide only), played at the table's foot with **Take** (`ideas.night_answer {id, take: true}`) and **Drop** (`take: false`), each carrying its `data-way-kind`; the goal lies in the Orkmaster's column's **Specs** pile marked
*proposed*. The narrow page deals no such card and no such mark. Pictures at 1366 x 768 to $ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import ConcernHost, start, system  # noqa: E402
from tests.test_maps_desktop_browser import Refused  # noqa: E402
from tests.test_table_desktop_browser import node as board_node, shot  # noqa: E402

pytestmark = pytest.mark.browser

CARD = '.hand-card[data-kind="night_proposal"]'
LIT = {"viewport": {"width": 1366, "height": 768}}
PID, SLUG = "np-2026-11-09-tech", "faster-start"


class NightHost(ConcernHost):
    """The stub host with one proposal waiting: its goal on Hold (`proposed` on its row) and the Needs-you row the real host builds (`idea_night.way_row`)."""

    def __init__(self):
        super().__init__()
        self.nodes.append(board_node(SLUG, "tech", "Faster start", "raw", "new", "ice", "", place="table", queue="hold", held_for="hold", proposed="2026-11-09", say={"doubts": [], "leaders": [], "judged": 0}))
        self.needs.append({"idea": "", "goal": SLUG, "kind": "night_proposal", "proposed": True, "id": PID, "by": "tech", "title": "Proposed: Faster start", "text": "Why: the start is slow.\nDone when: it is fast.", "blocks": False,
                           "at": "2026-11-10T03:10:00", "night": "2026-11-09", "choices": [{"label": "Take", "way": "take", "text": "x"}, {"label": "Drop", "way": "drop", "text": "y"}], "kinds": ["take", "drop"]})

    def board(self):
        return {**super().board(), "night": "01:00-07:00"}

    def handle(self, name, a):
        if name == "ideas.night_answer":
            self.log.append((name, a))
            self.needs[:] = [n for n in self.needs if n.get("id") != a["id"]]
            if a["take"]:
                next(n for n in self.nodes if n["slug"] == SLUG).pop("proposed")
            else:
                self.nodes[:] = [n for n in self.nodes if n["slug"] != SLUG]
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return {"ok": True, "status": "taken" if a["take"] else "dropped"}
        if name == "ideas.chronicle_goal":
            raise Refused("No such goal")          # a goal dropped is no past goal either
        return super().handle(name, a)


@pytest.fixture
def night(gui):
    pg, host, errors = start(gui, "wide", NightHost())
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def box(loc):
    return tuple(loc.evaluate("e => [e.offsetWidth, e.offsetHeight]"))


def play(pg):
    pg.locator(CARD).first.dispatch_event("click")
    lifted = pg.locator('.hand-lifted[data-kind="night_proposal"]')
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_the_proposal_is_a_card_in_its_leaders_stack_under_its_lane(night):
    pg, host = night
    cards = pg.locator(CARD)
    assert cards.count() == 1 and cards.first.get_attribute("data-key") == f"night/{PID}"
    assert "Proposed: Faster start" in cards.first.text_content() and box(cards.first) == (144, 202)
    lane = pg.locator(f".hand-lane:has({CARD})").get_attribute("data-lane")
    assert lane not in (None, "0"), "under the proposing leader's lane, not the project's"


def test_the_goal_lies_in_the_specs_pile_marked_proposed(night):
    pg, host = night
    system(pg)
    card = pg.locator(f'.col-card--spec[data-goal="{SLUG}"]')
    card.wait_for(timeout=WAIT_MS)
    assert card.get_attribute("data-proposed") == "1" and card.locator(".col-spec__proposed").inner_text() == "proposed"
    assert "proposed" in card.get_attribute("aria-label") and box(card) == (78, 56), "the Specs card's own size, nothing changes by what is open"
    assert pg.locator('.col-card[data-pile="analysis"][data-goal="faster-start"]').count() == 0


def test_played_it_has_take_and_drop_by_their_kinds_and_the_night_it_ran(night):
    pg, host = night
    lifted = play(pg)
    assert box(lifted) == (144, 202) and "the night of" in lifted.text_content() and "01:00-07:00" in lifted.text_content()
    ways = pg.locator(".hand-ways-cards button[data-way-kind]")
    assert [(ways.nth(i).get_attribute("data-way-kind"), ways.nth(i).locator(".hand-ans__name").inner_text()) for i in range(ways.count())] == [("take", "Take"), ("drop", "Drop")]
    pg.locator(f'.col-card--spec[data-goal="{SLUG}"][data-ringed]').wait_for(timeout=WAIT_MS)      # its goal is picked and ringed in the Specs pile while the card is up


def test_take_sends_its_command_and_the_mark_and_the_card_go(night):
    pg, host = night
    system(pg)
    play(pg)
    pg.locator('.hand-ways-cards button[data-way-kind="take"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"night_proposal\"], .hand-lifted[data-kind=\"night_proposal\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.night_answer") == [{"id": PID, "take": True}]
    pg.wait_for_function("() => !document.querySelector('.col-spec__proposed')", timeout=WAIT_MS)


def test_drop_sends_its_command_and_the_goal_leaves_the_pile(night):
    pg, host = night
    system(pg)
    play(pg)
    pg.locator('.hand-ways-cards button[data-way-kind="drop"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"night_proposal\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.night_answer") == [{"id": PID, "take": False}]
    pg.wait_for_function("() => !document.querySelector('.col-card--spec[data-goal=\"faster-start\"]')", timeout=WAIT_MS)


def test_the_narrow_page_deals_no_proposal_card(gui):
    pg, host, errors = start(gui, "narrow", NightHost())
    pg.wait_for_timeout(600)
    assert pg.locator(CARD).count() == 0 and pg.locator(".col-spec__proposed").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_pictures_at_1366_by_768(gui):
    pg, host, errors = start(gui, "wide", NightHost(), **LIT)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    system(pg)
    pg.locator(".col-spec__proposed").first.wait_for(timeout=WAIT_MS)
    pg.locator('.col-pile.is-specs').hover()                                           # the deck fans: the proposed card shows its mark
    pg.wait_for_timeout(500)
    shot(pg, "h3-column-and-hand-with-a-proposal.png")
    play(pg)
    shot(pg, "h3-proposal-played.png")
    pg.context.close()
    assert not errors, "\n".join(errors)
