"""Spec 168 D4 (decisions §283.21): a concern at the alert's level is also a card in the hand, one stack a leader under its lane, in a real browser against the concerns' stub host (`ConcernHost` made to carry each goal's
`concerns.list`, the open concerns as realm/concerns.py `cards` says them, and to answer `ideas.concern_later`). The hand's card, the small card in the party's header and the mark on the scheme are one thing: one hovered, focused or lifted lights
the others, and it is answered once. A note stays on the scheme and in the header. Played, the card rises at the table's foot at its left (144 x 202), the leader's tab opened, its ways the hand: **Not a problem** (`not_a_problem`),
**Later** (`later`: face down in the header, out of the hand, the mark stays on the scheme) and **Make it a goal** (`make_it_a_goal`). The narrow page deals no such card. Pictures at 1366 x 768 to $ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import ConcernHost, LOBBY, ROOMS, go, ready, start, system  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser

CARD = '.hand-card[data-kind="concern"]'
LIT = {"viewport": {"width": 1366, "height": 768}}
KINDS = ["not_a_problem", "later", "make_it_a_goal"]


class CardHost(ConcernHost):
    """The concerns' host whose snapshot carries each party's `concerns.list` and that lays a concern *Later* (`ideas.concern_later`)."""

    def counts(self, slug):
        out = super().counts(slug)
        rec = self.records.get(slug)
        out["list"] = [{"id": c["id"], "on": c["on"], "name": c["name"], "level": c["level"], "what": c["what"], "why": c["why"], "fix": c["fix"], "aspect": c["aspect"], "later": bool(c.get("later")),
                        "in_hand": c["level"] == "alert" and not c.get("later")} for c in (rec["concerns"] if rec else []) if not c.get("idea")]
        return out

    def concerns(self, name, a):
        if name == "ideas.concern_later":
            rec = self.records[a["party"]]
            next(x for x in rec["concerns"] if x["id"] == a["id"])["later"] = True
            self.rev += 1
            return copy.deepcopy(rec)
        return super().concerns(name, a)


@pytest.fixture
def hand(gui):
    pg, host, errors = start(gui, "wide", CardHost())
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def box(loc):
    return tuple(loc.evaluate("e => [e.offsetWidth, e.offsetHeight]"))      # layout size: a hovered card leans, its bounding box is wider


def play(pg, party="tech"):
    pg.locator(f'{CARD}[data-key="concern/{party}/{"c1" if party == "tech" else "g1"}"]').dispatch_event("click")       # the hand's cards overlap: pressed as a key would
    lifted = pg.locator('.hand-lifted[data-kind="concern"]')
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_an_alert_is_a_card_in_the_hand_one_stack_a_leader_under_its_lane_and_a_note_is_none(hand):
    pg, host = hand
    cards = pg.locator(CARD)
    assert sorted(cards.nth(i).get_attribute("data-key") for i in range(cards.count())) == ["concern/game/g1", "concern/tech/c1"], "the alerts only: a note stays on the scheme and in the header"
    stacks = pg.locator('.hand-stack[data-stack^="concerns:"]')
    assert sorted(stacks.nth(i).get_attribute("data-stack").split("@")[0] for i in range(stacks.count())) == ["concerns:game", "concerns:tech"]
    lanes = [pg.locator(f'.hand-lane:has({CARD}[data-key="concern/{p}/{c}"])').get_attribute("data-lane") for p, c in (("tech", "c1"), ("game", "g1"))]
    assert len(set(lanes)) == 2 and "0" not in lanes, "each under its own leader's lane, not the project's"
    assert box(cards.first) == (144, 202)
    assert pg.locator(f'{CARD} .hand-card__name').first.inner_text()


def test_the_header_holds_a_small_card_for_each_concern_and_the_hand_for_the_alert_only(hand):
    pg, host = hand
    go(pg, "tech")
    row = pg.locator('.table-head .cn-cards[data-party="tech"] .cn-card')
    row.first.wait_for(timeout=WAIT_MS)
    assert [row.nth(i).get_attribute("data-concern-id") for i in range(row.count())] == ["tech/c1", "tech/c2", "tech/c3"]
    assert [row.nth(i).get_attribute("data-in-hand") for i in range(row.count())] == ["1", "0", "0"]
    assert {row.nth(i).get_attribute("data-face") for i in range(row.count())} == {"up"}
    assert box(row.first) == (28, 39)


def test_one_hovered_lights_the_others_the_hand_the_header_and_the_mark_on_the_scheme(hand):
    pg, host = hand
    system(pg)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    mark = pg.locator(f'.cn-mark[data-level="alert"]').first
    mark.wait_for(timeout=WAIT_MS)
    assert pg.locator("[data-lit]").count() == 0
    pg.locator(f'{CARD}[data-key="concern/tech/c1"]').hover(position={"x": 6, "y": 40}, force=True)      # the tech lane has a failure in front: the concern lies behind it, its left edge shows
    pg.locator('.cn-card[data-concern-id="tech/c1"].is-lit').wait_for(timeout=WAIT_MS)
    pg.locator(".cn-mark[data-lit]").first.wait_for(timeout=WAIT_MS)
    assert pg.locator('.cn-card.is-lit').count() == 1, "only its own"
    pg.mouse.move(700, 300)
    pg.wait_for_function("() => !document.querySelector('.cn-card.is-lit, .cn-mark[data-lit]')", timeout=WAIT_MS)
    pg.locator('.cn-card[data-concern-id="tech/c1"]').hover()                      # the header's card lights the hand's and the scheme's
    pg.locator(f'{CARD}[data-key="concern/tech/c1"][data-lit]').wait_for(timeout=WAIT_MS)
    pg.locator(".cn-mark[data-lit]").first.wait_for(timeout=WAIT_MS)


def test_played_it_rises_at_the_tables_foot_its_leaders_tab_open_its_ways_the_hand_by_their_kinds(hand):
    pg, host = hand
    lifted = play(pg)
    assert box(lifted) == (144, 202)
    pg.locator('.table-tab[data-tab="tech"][aria-selected="true"], .col-head__tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    ways = pg.locator(".hand-ways-cards button[data-way-kind]")
    assert [(ways.nth(i).get_attribute("data-way-kind"), ways.nth(i).locator(".hand-ans__name").inner_text()) for i in range(ways.count())] == list(zip(KINDS, ["Not a problem", "Later", "Make it a goal"]))
    assert pg.locator(".hand-lifted[data-lit], .cn-card.is-lit").count() >= 1, "the lifted one is lit with the others"
    assert pg.locator(".hand-lifted").bounding_box()["x"] < 300, "at the table's foot, at its left"
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    assert pg.locator(CARD).count() == 2, "put back: still in the hand"


def test_later_lays_it_face_down_in_the_header_out_of_the_hand_and_its_mark_stays_on_the_scheme(hand):
    pg, host = hand
    system(pg)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    pg.wait_for_selector(".table-head")
    before = box(pg.locator(".table-head"))
    play(pg).wait_for(timeout=WAIT_MS)
    pg.locator('.hand-ways-cards button[data-way-kind="later"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-key=\"concern/tech/c1\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.concern_later") == [{"party": "tech", "id": "c1"}]
    down = pg.locator('.cn-card[data-concern-id="tech/c1"][data-face="down"]')
    down.wait_for(timeout=WAIT_MS)
    assert down.get_attribute("data-in-hand") == "0" and pg.locator(CARD).count() == 1 and pg.locator(".hand-lifted").count() == 0
    assert pg.locator(".cn-mark[data-level='alert']").count() >= 1, "it is still on the scheme"
    assert box(pg.locator(".table-head")) == before, "the header does not change size"


def test_not_a_problem_and_make_it_a_goal_answer_it_once_and_it_leaves_the_hand_and_the_header(hand):
    pg, host = hand
    play(pg, "game")
    pg.locator('.hand-ways-cards button[data-way-kind="not_a_problem"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-key=\"concern/game/g1\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.concern_dismiss") == [{"party": "game", "id": "g1"}]
    play(pg, "tech")
    pg.locator('.hand-ways-cards button[data-way-kind="make_it_a_goal"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"concern\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.concern_goal") == [{"party": "tech", "id": "c1"}] and host.sent("ideas.concern_later") == []


def test_the_narrow_page_deals_no_concern_card(gui):
    pg, host, errors = start(gui, "narrow", CardHost())
    pg.wait_for_timeout(600)
    assert pg.locator(CARD).count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_pictures_at_1366_by_768(gui):
    pg, host, errors = start(gui, "wide", CardHost(), **LIT)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    system(pg)
    shot(pg, "d4-lane-with-its-concern-stack.png")
    pg.locator(f'{CARD}[data-key="concern/tech/c1"]').hover(position={"x": 6, "y": 40}, force=True)      # the tech lane has a failure in front: the concern lies behind it, its left edge shows
    play(pg)
    shot(pg, "d4-concern-played.png")
    pg.locator('.hand-ways-cards button[data-way-kind="later"]').click()
    pg.locator('.cn-card[data-face="down"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(1200)                                                          # the played card has flown back
    shot(pg, "d4-concern-laid-later.png")
    pg.context.close()
    assert not errors, "\n".join(errors)
