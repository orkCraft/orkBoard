"""Spec 168 H4 (decisions §283.22, §283.33): what a Silent leader decided, as a card that can be overruled, in a real browser against the concerns' stub host. The goal's row says `decided` (`[{id, party, leader, q, answer, why, round}]`);
each decision is a card of its leader's stack in the hand (wide only): muted (no alert's ring), its leader's head, the sign of *decided*, played at the table's foot with **Accepted** (`ideas.decided_accept`) and **Replay** (`ideas.decided_replay`),
each carrying its `data-way-kind`; the card leaves by itself when the goal moves to its next stage. The narrow page deals none. Pictures at 1366 x 768 to $ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import ConcernHost, start  # noqa: E402
from tests.test_maps_desktop_browser import Refused  # noqa: E402
from tests.test_table_desktop_browser import node as board_node, shot  # noqa: E402

pytestmark = pytest.mark.browser

CARD = '.hand-card[data-kind="decided"]'
LIT = {"viewport": {"width": 1366, "height": 768}}
SLUG = "dark-mode"
ONE = {"id": "q1", "party": "tech", "leader": "architect", "q": "Where do the rooms live?", "answer": "a new file", "why": "the map shows rooms.ts is full", "round": 1}
TWO = {"id": "q2", "party": "tech", "leader": "architect", "q": "Which store keeps them?", "answer": "the table", "why": "it is the one the code reads", "round": 1}


class DecidedHost(ConcernHost):
    """The stub host with one goal at Talk whose leader decided two questions by itself; Replay can be refused as the keeper does once the goal has gone on."""

    def __init__(self):
        super().__init__()
        self.nodes.append(board_node(SLUG, "tech", "Dark mode", "talk", "talk", "ice", "", decided=[dict(ONE), dict(TWO)], say={"doubts": [], "leaders": [], "judged": 0}))
        self.gone_on = False

    def node(self):
        return next(n for n in self.nodes if n["slug"] == SLUG)

    def drop(self, qid):
        self.node()["decided"] = [d for d in self.node()["decided"] if d["id"] != qid]
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))

    def advance(self):
        """The goal moves to its next stage: the decisions' phase is past, the row's `decided` is empty (realm/answer_ways.py `decided_of`)."""
        self.node().update(state="decided", stage="spec", decided=[])
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))

    def handle(self, name, a):
        if name in ("ideas.decided_accept", "ideas.decided_replay"):
            self.log.append((name, a))
            if name == "ideas.decided_replay" and self.gone_on:
                raise Refused("The goal has gone on: this decision can no longer be replayed")
            self.drop(a["id"])
            return {"ok": True, "idea": a["idea"]}
        return super().handle(name, a)


@pytest.fixture
def decided(gui):
    pg, host, errors = start(gui, "wide", DecidedHost())
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def box(loc):
    return tuple(loc.evaluate("e => [e.offsetWidth, e.offsetHeight]"))


def play(pg, key):
    pg.locator(f'{CARD}[data-key="{key}"]').dispatch_event("click")
    lifted = pg.locator('.hand-lifted[data-kind="decided"]')
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_each_decision_is_a_muted_card_of_its_leaders_stack_with_its_head_and_a_sign_of_decided(decided):
    pg, host = decided
    cards = pg.locator(CARD)
    assert cards.count() == 1 and cards.first.get_attribute("data-key") == f"decided/{SLUG}/q1"          # two decisions of one goal and one leader are one stack: its top card shows
    first = cards.first
    assert "Where do the rooms live?" in first.text_content() and box(first) == (144, 202)
    assert first.locator(".ork-race__head").count() == 1 and first.locator(".corner__kind .ork-sign.check").count() == 1       # its leader's head and the sign of *decided*
    assert first.locator(".ork-sign.alert").count() == 0 and "alert" not in (first.get_attribute("class") or "").split()      # no alert's ring
    assert float(first.evaluate("e => getComputedStyle(e).opacity")) < 1.0, "muted at rest"
    lane = pg.locator(f".hand-lane:has({CARD})").get_attribute("data-lane")
    assert lane not in (None, "0"), "under the deciding leader's lane, not the project's"


def test_played_it_says_what_was_decided_and_why_and_has_accepted_and_replay_by_their_kinds(decided):
    pg, host = decided
    lifted = play(pg, f"decided/{SLUG}/q1")
    assert box(lifted) == (144, 202) and "a new file" in lifted.text_content() and "rooms.ts is full" in lifted.text_content()
    ways = pg.locator(".hand-ways-cards button[data-way-kind]")
    assert [(ways.nth(i).get_attribute("data-way-kind"), ways.nth(i).locator(".hand-ans__name").inner_text()) for i in range(ways.count())] == [("go_on", "Accepted"), ("ask_more", "Replay")]


def test_accepted_sends_its_command_and_only_that_card_goes(decided):
    pg, host = decided
    play(pg, f"decided/{SLUG}/q1")
    pg.locator('.hand-ways-cards button[data-way-kind="go_on"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-lifted[data-kind=\"decided\"]') && document.querySelector('.hand-card[data-kind=\"decided\"]')?.dataset.key === 'decided/dark-mode/q2'", timeout=WAIT_MS)
    assert host.sent("ideas.decided_accept") == [{"idea": SLUG, "id": "q1"}]                                  # the next decision of the stack is on top


def test_replay_sends_its_command_and_the_card_goes_back_as_a_question(decided):
    pg, host = decided
    play(pg, f"decided/{SLUG}/q1")
    pg.locator('.hand-ways-cards button[data-way-kind="ask_more"]').click()
    pg.wait_for_function("() => document.querySelector('.hand-card[data-kind=\"decided\"]')?.dataset.key === 'decided/dark-mode/q2'", timeout=WAIT_MS)
    assert host.sent("ideas.decided_replay") == [{"idea": SLUG, "id": "q1"}]


def test_a_replay_the_keeper_refuses_leaves_the_card_where_it_is(decided):
    pg, host = decided
    host.gone_on = True
    play(pg, f"decided/{SLUG}/q1")
    pg.locator('.hand-ways-cards button[data-way-kind="ask_more"]').click()
    pg.wait_for_timeout(600)
    assert host.sent("ideas.decided_replay") == [{"idea": SLUG, "id": "q1"}] and pg.locator('.hand-lifted[data-kind="decided"]').count() == 1
    assert pg.locator(CARD).count() >= 1


def test_the_cards_leave_by_themselves_when_the_goal_moves_to_its_next_stage(decided):
    pg, host = decided
    assert pg.locator(CARD).count() == 1
    host.advance()
    pg.wait_for_function("() => document.querySelectorAll('.hand-card[data-kind=\"decided\"]').length === 0", timeout=WAIT_MS)
    assert host.sent("ideas.decided_accept") == [] and host.sent("ideas.decided_replay") == []                  # nobody pressed anything


def test_the_narrow_page_deals_no_decision_card(gui):
    pg, host, errors = start(gui, "narrow", DecidedHost())
    pg.wait_for_timeout(600)
    assert pg.locator(CARD).count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_pictures_at_1366_by_768(gui):
    pg, host, errors = start(gui, "wide", DecidedHost(), **LIT)
    pg.locator(CARD).first.wait_for(timeout=WAIT_MS)
    shot(pg, "h4-veto-cards-in-the-hand.png")
    play(pg, f"decided/{SLUG}/q1")
    shot(pg, "h4-veto-card-played.png")
    pg.context.close()
    assert not errors, "\n".join(errors)
