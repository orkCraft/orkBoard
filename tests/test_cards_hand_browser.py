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
    return { w: r.width, h: r.height, top: r.top, bottom: r.bottom, asks: c.classList.contains('is-asks') && c.dataset.kind !== 'battle', bang: !!c.querySelector('.hands-asks'), goal: c.dataset.goal }; }) }; }"""
ALERT = """() => { const d = document.createElement('i'); d.style.color = 'var(--ork-alert)'; document.body.append(d);
  const c = getComputedStyle(d).color; d.remove(); return c; }"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()






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
    pg.goto(url + "?mock=1")
    pg.locator(f"{HAND}[data-kind=turn]").first.wait_for(timeout=15000)
    pg.wait_for_timeout(600)


def sent(pg, name):
    return [a for n, a in pg.evaluate(SENT) if n == name]


def keys(pg):
    return pg.evaluate("(sel) => [...document.querySelectorAll(sel)].map((c) => c.dataset.key)", HAND)




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
        assert sent(pg, "ideas.answer_way") == [{"slug": ASKS, "answers": ["Move it"], "from": "hand"}]
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
        assert sent(pg, "ideas.answer_way") == []                                                                      # one question answered: nothing is sent yet
        pg.wait_for_function("() => document.querySelector('.hand-lifted')?.innerText.includes('(2 of 2)')", timeout=5000)
        pg.locator(".hand-ways-row [data-way=way-1]").click()
        assert sent(pg, "ideas.answer_way") == [{"slug": TWO, "answers": ["Gold", "Ten"], "from": "hand"}]
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




def test_drop_on_the_mat_its_hand_card_opened_sends_from_hand_and_undo_puts_the_page_back(turned_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        before = keys(pg)
        pg.locator(f"{HAND}[data-kind=turn][data-goal='{TALK}']").click()
        pg.locator(".mathand [data-way=drop]").click()
        assert sent(pg, "ideas.drop") == [{"slug": TALK, "from": "hand"}]
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


def test_a_mat_opened_from_the_table_sends_from_mat(turned_url):
    """`from` says how the person reached the move: a mat opened from the table (no hand card) sends "mat", the hand card's mat "hand"."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        turned(pg, turned_url)
        pg.evaluate("""async (slug) => { const sp = await import("/static/js/cards/spreads/open.js"); sp.openSpread({ kind: "track", slug }); }""", TALK)
        pg.locator("[data-spread=track]").wait_for(timeout=5000)
        pg.locator(".mathand [data-way=drop]").click()
        assert sent(pg, "ideas.drop") == [{"slug": TALK, "from": "mat"}]
        b.close()




TITLES = """() => [...document.querySelectorAll('.frame-hand button.hand-card--stop')].map((c) => {
  const t = c.querySelector('.hands-name'), r = t.getBoundingClientRect(), range = document.createRange(); range.selectNodeContents(t);
  const first = range.getClientRects()[0] || r, x = first.left + 1, y = first.top + first.height / 2, hit = document.elementFromPoint(x, y);
  return { title: t.textContent.slice(0, 30), x, y, ok: !!hit && c.contains(hit) }; })"""




