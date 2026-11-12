"""**The hand as whole cards** (goal 170, stage M): on mocks (`?mock=1`) the hand's cards are S cards, upright 2.5:3.5, each wholly
inside the hand (no half-hidden rise), the card that asks lifted and ringed with its "!"; pressing a question card opens its ways
(the hand's own answer UI). The cards of the hand as it was (cut by the hand's rim) are not drawn on the table of cards."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests import mock_kit  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
BOXES = """() => { const h = document.querySelector('.frame-hand').getBoundingClientRect();
  return { hand: [h.top, h.bottom], old: !!document.querySelector('.hand-card--face'),
    cards: [...document.querySelectorAll('.frame-hand button.hand-card--stop')].map((c) => { const r = c.getBoundingClientRect();
    return { w: r.width, h: r.height, top: r.top, bottom: r.bottom, asks: c.classList.contains('is-asks') && !['turn', 'battle'].includes(c.dataset.kind), bang: !!c.querySelector('.hands-asks'), goal: c.dataset.goal }; }) }; }"""
ALERT = """() => { const d = document.createElement('i'); d.style.color = 'var(--ork-alert)'; document.body.append(d);
  const c = getComputedStyle(d).color; d.remove(); return c; }"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def test_the_hands_cards_are_whole_s_cards_and_the_asking_one_is_ringed(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        pg.locator(".frame-hand button.hand-card--stop").first.wait_for(timeout=15000)
        pg.wait_for_timeout(800)
        got = pg.evaluate(BOXES)
        assert len(got["cards"]) >= 3 and not got["old"]
        assert got["hand"][1] - got["hand"][0] < 230                      # a row for whole cards, not the whole window
        for c in got["cards"]:
            assert abs(c["w"] / c["h"] - 2.5 / 3.5) < 0.03, c
            assert 100 <= c["w"] <= 140, c
            assert c["top"] >= got["hand"][0] - 12 and c["bottom"] <= got["hand"][1] + 1, (c, got["hand"])      # wholly in the hand's row (a lifted one by a few px)
        asking = [c for c in got["cards"] if c["asks"]]
        assert asking and all(c["bang"] for c in asking)
        ring = pg.locator(".frame-hand button.hand-card--stop.is-asks").first.evaluate("(e) => getComputedStyle(e).borderTopColor")
        assert ring == pg.evaluate(ALERT)
        b.close()


def test_pressing_a_question_card_opens_no_l_and_its_ways_are_cards(page_url):
    """Decisions §296.2: no L over the table for a question; its ways are cards (a talk question's lie by its question today, q-choose)."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        card = pg.locator(".frame-hand button.hand-card--stop.is-asks").first
        card.wait_for(timeout=15000)
        card.click()
        pg.locator(".q-choose__row").first.wait_for(timeout=5000)
        assert pg.locator(".cards-l").count() == 0
        b.close()


# ---- goal 171 stage K: a card for each move that waits (ideas.turns), the open mat's ways -------------------------------------------------------------------

SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => [x.name, x.args]))"
HAND = ".frame-hand button.hand-card"
ASKS, TALK, SPEC, TWO, COVERED = "172-example-1", "173-example-2", "174-example-3", "175-example-4", "166-the-orkmaster-reads-the-decisions"


@pytest.fixture(scope="module")
def turned_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def turned(pg, url):
    pg.goto(url + "?mock=1&table=cards")
    pg.locator(f"{HAND}[data-kind=turn]").first.wait_for(timeout=15000)
    pg.wait_for_timeout(600)


def sent(pg, name):
    return [a for n, a in pg.evaluate(SENT) if n == name]


def keys(pg):
    return pg.evaluate("(sel) => [...document.querySelectorAll(sel)].map((c) => c.dataset.key)", HAND)


def test_each_goal_that_waits_is_one_card_in_the_hand_grouped_by_goal_and_a_goal_waiting_for_nobody_has_none(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        waits = pg.evaluate("() => import('/static/js/link.js').then((l) => l.command('ideas.turns', {}))")["turns"]
        for t in waits:
            assert pg.locator(f"{HAND}[data-goal='{t['goal']}']").count() >= 1, t                                  # every goal the host says waits has a card
        for goal in (ASKS, TALK, SPEC, TWO):
            assert pg.locator(f"{HAND}[data-kind=turn][data-goal='{goal}']").count() == 1, goal                   # one card a goal
            assert pg.locator(f"[data-stack*='{goal}']").count() == 1                                              # in the goal's stack
        assert pg.locator(f"{HAND}[data-kind=turn][data-goal='{COVERED}']").count() == 0                          # its question is its card already: no second
        assert pg.locator(f"{HAND}[data-goal='{COVERED}']").count() == 1
        assert pg.locator(f"{HAND}[data-goal^='150-']").count() == 0                                                 # a goal at work waits for nobody: no card
        card = pg.locator(f"{HAND}[data-kind=turn][data-goal='{ASKS}']")
        assert card.evaluate("(el) => getComputedStyle(el).borderTopColor") == pg.evaluate(ALERT)                  # ringed as a card that asks is
        assert card.locator(".hands-toks .cards-ct").count() >= 1 and "waits for you" in card.inner_text()         # with its craft tokens
        assert pg.evaluate("() => document.body.innerText.match(/\\d+ (moves?|cards?) (wait|waits)/)") is None        # no count of what waits
        b.close()


def test_a_goal_that_asks_lifts_its_ways_and_one_press_answers_with_from_hand_and_an_undo(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        before = pg.locator(f"{HAND}[data-kind=turn]").count()
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{ASKS}']").click()
        ways = pg.locator(".hand-ways-row [data-way]")
        ways.first.wait_for(timeout=5000)
        assert [t.strip().split("\n")[0] for t in ways.all_inner_texts()] == ["Keep it", "Move it", "Drop it", "In your own words"]
        pg.locator(".hand-ways-row [data-way=way-1]").click()
        assert sent(pg, "ideas.answer") == [{"slug": ASKS, "answers": ["Move it"], "from": "hand"}]
        pg.wait_for_function("(sel) => ![...document.querySelectorAll(sel)].some((c) => c.dataset.goal === '172-example-1' && c.dataset.kind === 'turn' && !c.classList.contains('is-gone'))", arg=HAND, timeout=5000)
        toast = pg.locator(".gui-toast", has_text="Sent: Move it").first
        toast.wait_for(timeout=5000)
        toast.get_by_role("button", name="Undo").click()                                                           # Undo: the host's own, ideas.undo with the goal
        assert sent(pg, "ideas.undo") == [{"idea": ASKS}]
        pg.wait_for_function("([sel, n]) => document.querySelectorAll(sel).length === n", arg=[f"{HAND}[data-kind=turn]:not(.is-gone)", before], timeout=5000)      # the page as before
        b.close()


def test_a_goal_that_asks_two_questions_walks_them_and_sends_the_answers_together(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{TWO}']").click()
        assert "(1 of 2)" in pg.locator(".hand-lifted").inner_text()
        pg.locator(".hand-ways-row [data-way=way-0]").click()
        assert sent(pg, "ideas.answer") == []                                                                      # one question answered: nothing is sent yet
        pg.wait_for_function("() => document.querySelector('.hand-lifted')?.innerText.includes('(2 of 2)')", timeout=5000)
        pg.locator(".hand-ways-row [data-way=way-1]").click()
        assert sent(pg, "ideas.answer") == [{"slug": TWO, "answers": ["Gold", "Ten"], "from": "hand"}]
        b.close()


def test_a_goal_whose_talk_is_said_opens_its_mat_and_the_hand_is_that_mats_ways_with_the_moves_that_wait_a_pile(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        before = keys(pg)
        assert len(before) >= 5
        card = pg.locator(f"{HAND}[data-kind=turn][data-goal='{TALK}']")
        card.click()
        pg.locator("[data-spread=track]").wait_for(timeout=5000)
        hand = pg.locator(".frame-hand .mathand")
        hand.wait_for(timeout=5000)
        assert [t.strip().split("\n")[0] for t in hand.locator("[data-way]").all_inner_texts()] == ["Hold", "Drop"]      # the mat's ways, a fan in the hand
        assert pg.locator(f"{HAND}, [data-spread] .sp-cards").count() == 0                                         # no card of the moves that wait, and no ways in the mat's foot
        pile = hand.locator("[data-act=pile]")
        assert pile.count() == 1 and not pile.inner_text().strip().isdigit() and pile.locator(".mathand__backs span").count() == 6      # a pile by its thickness, no number
        box = hand.bounding_box()
        mat = pg.locator("[data-spread=track] .mf").bounding_box()
        assert mat["y"] + mat["height"] <= box["y"] + 1                                                           # the mat leaves the hand its room: nothing lies over it
        seen = []
        for _ in range(12):                                                                                          # the focus goes through the mat and the hand's ways only
            pg.keyboard.press("Tab")
            seen.append(pg.evaluate("() => { const e = document.activeElement; return e.closest('.mathand') ? 'hand:' + (e.dataset.way || e.dataset.act) : e.closest('[data-spread]') ? 'mat' : 'outside'; }"))
        assert "outside" not in seen and "hand:drop" in seen and "hand:hold" in seen and "hand:pile" in seen, seen
        pg.keyboard.press("Escape")                                                                                  # closed: every card is back, none lost
        pg.locator("[data-spread=track]").wait_for(state="detached", timeout=5000)
        pg.wait_for_function("([sel, n]) => document.querySelectorAll(sel).length === n", arg=[HAND, len(before)], timeout=5000)
        assert keys(pg) == before and pg.locator(".mathand").count() == 0
        card.click()                                                                                                 # and the pile pressed brings them back as well
        pg.locator(".frame-hand [data-act=pile]").click()
        pg.locator("[data-spread=track]").wait_for(state="detached", timeout=5000)
        pg.wait_for_function("([sel, n]) => document.querySelectorAll(sel).length === n", arg=[HAND, len(before)], timeout=5000)
        b.close()


def test_drop_on_the_mat_sends_from_mat_and_undo_puts_the_page_back(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        before = keys(pg)
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{TALK}']").click()
        pg.locator(".mathand [data-way=drop]").click()
        assert sent(pg, "ideas.drop") == [{"slug": TALK, "from": "mat"}]
        pg.locator("[data-spread=track]").wait_for(state="detached", timeout=5000)
        assert pg.locator(f"{HAND}[data-goal='{TALK}']").count() == 0 and pg.locator("[data-pile=dropped]").count() == 1      # it lies face down in the Dropped pile
        toast = pg.locator(".gui-toast", has_text="Dropped:").first
        toast.wait_for(timeout=5000)
        toast.get_by_role("button", name="Undo").click()
        assert sent(pg, "ideas.undo") == [{"idea": TALK}]
        pg.wait_for_function("(sel) => !!document.querySelector(sel)", arg=f"{HAND}[data-kind=turn][data-goal='{TALK}']", timeout=5000)
        assert pg.locator("[data-pile=dropped]").count() == 0
        assert sorted(keys(pg)) == sorted(before)
        b.close()
