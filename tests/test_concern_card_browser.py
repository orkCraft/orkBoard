"""Spec 168 D4 (decisions §283.21): a concern at the alert's level is also a card in the hand, one stack a leader under its lane, in a real browser against the concerns' stub host (`ConcernHost` made to carry each goal's
`concerns.list`, the open concerns as realm/concerns.py `cards` says them, and to answer `ideas.concern_later`). The hand's card, the small card in the party's header and the mark on the scheme are one thing: one hovered, focused or lifted lights
the others, and it is answered once. A note stays on the scheme and in the header. Played, the card rises at the table's foot at its left (144 x 202), the leader's tab opened, its ways the hand: **Not a problem** (`not_a_problem`),
**Later** (`later`: face down in the header, out of the hand, the mark stays on the scheme) and **Make it a goal** (`make_it_a_goal`). The narrow page deals no such card. Pictures at 1366 x 768 to $ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import copy

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concerns_desktop_browser import ConcernHost, start  # noqa: E402

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






# -- Spec 168 D5 (decisions §283.25): a doubt left is a card in the hand --------------------------------------------------------------------------

import json  # noqa: E402

from tests.test_table_desktop_browser import node as board_node  # noqa: E402

DOUBT = '.hand-card[data-kind="doubt"]'
WHY = "The option is not what was asked"


class DoubtHost(CardHost):
    """The concerns' host with a goal in Talk that the leaders judged again once: its row says the Architect still doubts (`say.doubts`); `ideas.judge_again` and `ideas.to_hearing` clear the doubt as the real host's goal does."""

    def __init__(self):
        super().__init__()
        self.nodes.append(board_node("dark-mode", "tech", "Add a dark mode option", "talk", "talk", "ice", "", place="table", say={"doubts": [{"party": "tech", "verdict": "doubt", "why": WHY}], "leaders": [], "judged": 1}))

    def handle(self, name, a):
        if name in ("ideas.judge_again", "ideas.to_hearing"):
            self.log.append((name, a))
            next(n for n in self.nodes if n["slug"] == a["idea"])["say"]["doubts"] = []
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return {"ok": True, "idea": a["idea"], "parties": ["tech"]}
        return super().handle(name, a)


@pytest.fixture
def doubt(gui):
    pg, host, errors = start(gui, "wide", DoubtHost())
    pg.locator(DOUBT).first.wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def play_doubt(pg):
    pg.locator(DOUBT).first.dispatch_event("click")
    lifted = pg.locator('.hand-lifted[data-kind="doubt"]')
    lifted.wait_for(timeout=WAIT_MS)
    return lifted






def test_to_the_hearing_sends_its_command_and_the_card_leaves(doubt):
    pg, host = doubt
    play_doubt(pg)
    pg.locator('.hand-ways-cards button[data-way-kind="go_on"]').click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"doubt\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.to_hearing") == [{"idea": "dark-mode"}] and host.sent("ideas.judge_again") == []




