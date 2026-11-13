"""**The phone in cards** (goal 170, stage P; docs/mockups/table-cards/ ?face=phone): the phone's page (`/app/`, gui/pwa.py) on mocks (`?mock=1`),
served by tools/serve_mock.py at the path the phone listener serves it, at 390 x 844 with touch. Its link asks no computer (js/mock/mocklink.js,
reached as `./page/js/mock/mocklink.js`); the feed is drawn in cards (js/cards/phone.js): the leaders' heads in rings, the leaders' M cards full width (what asks lies in
the hand only, decisions §296.5), what is at work a shelf of S cards, and a card pressed opens as an L that fills the screen, Close puts it
away. Without `?mock=1` the phone loads no mock module. Set `ORK_SHOTS` to a folder to leave screenshots there."""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests import narrow  # noqa: E402
from tests import mock_kit  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
SHOTS = os.environ.get("ORK_SHOTS", "")


@pytest.fixture(scope="module")
def base():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown()


def phone(p, url):
    b = launch(p)
    pg = b.new_context(**narrow.NARROW).new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url)
    return b, pg, errors


def test_the_phone_on_mocks_draws_its_feed_in_cards(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        pg.locator(".up-ct .cards-m").first.wait_for(timeout=20000)
        # the leaders' heads in rings, the Orkmaster's first
        heads = pg.locator(".up-fh__head")
        assert heads.count() >= 3 and heads.first.get_attribute("data-leader") == "orkmaster"
        # the feed: M cards full width; no section of what asks (decisions §296.5: the person's move lies in the hand)
        feed = pg.locator(".up-ct")
        ms = feed.locator(".cards-m")
        first = ms.first.bounding_box()
        assert first["width"] >= 390 - 40, first
        assert feed.get_by_role("button", name="Answer in hand").count() == 0
        assert "asks you" not in [t.strip().lower() for t in feed.locator(".cards-lab").all_inner_texts()]
        # what is at work: a shelf of S cards
        shelf = pg.locator(".up-ct__shelf")
        assert shelf.locator(".cards-s").count() >= 2
        shelf.scroll_into_view_if_needed()
        if SHOTS:
            pg.screenshot(path=str(Path(SHOTS) / "phone-shelf.png"))
        pg.evaluate("document.querySelector('.up-look').scrollTo(0, 0)")
        # the bottom: the + card and the round die button stay
        assert pg.locator(".hand-up").count() == 1 and pg.locator(".up-row").is_visible()
        if SHOTS:
            pg.screenshot(path=str(Path(SHOTS) / "phone-feed.png"))
        narrow.no_sideways(pg)
        assert not errors, errors
        b.close()


def test_a_card_pressed_opens_as_an_l_over_the_whole_screen_and_close_puts_it_away(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        m = pg.locator(".up-ct .cards-m:not([data-mat])").first      # a word, no mat (decisions §297.1)
        m.wait_for(timeout=20000)
        m.click(position={"x": 24, "y": 14})                      # its head: the goal's own link in its body is another press
        card = pg.locator(".cards-l")
        card.wait_for(timeout=5000)
        pg.wait_for_timeout(500)
        box = card.bounding_box()
        assert box["x"] <= 1 and box["width"] >= 388 and box["height"] >= 840, box
        assert card.get_by_role("button", name="Close").is_visible()
        if SHOTS:
            pg.screenshot(path=str(Path(SHOTS) / "phone-open.png"))
        card.get_by_role("button", name="Close").click()
        assert pg.locator(".cards-l").count() == 0
        assert not errors, errors
        b.close()


def test_a_goal_of_the_shelf_opens_as_an_l_too(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        s = pg.locator(".up-ct__shelf .cards-s").first
        s.wait_for(timeout=20000)
        s.scroll_into_view_if_needed()
        s.click()
        pg.locator(".cards-l").wait_for(timeout=5000)
        assert pg.locator(".cards-l .cards-l__title").inner_text().strip()
        pg.locator(".cards-l").get_by_role("button", name="Close").click()
        assert pg.locator(".cards-l").count() == 0
        assert not errors, errors
        b.close()


def test_without_mock_the_phone_loads_no_mock_module(base):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_context(**narrow.NARROW).new_page()
        asked = []
        pg.on("request", lambda r: asked.append(r.url))
        pg.goto(base + "/app/")
        pg.locator("#phone .phone-card").wait_for(timeout=15000)     # unpaired: the frame's own card, no page
        pg.wait_for_timeout(500)
        assert not [u for u in asked if "/mock/" in u and "plate.css" not in u], asked
        assert pg.locator(".mock-plate").count() == 0
        b.close()


@pytest.fixture(scope="module")
def turned_base():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown()


SENT = "() => import('/app/page/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => [x.name, x.args]))"


def test_a_move_played_on_the_mat_its_phone_card_opened_is_sent_from_the_hand(turned_base):
    """H7 counts how the person reached a move (goal 171 O2): on the phone a move's card opened, *Open it* lays its mat, and Drop played there is sent `from: "hand"`, as on the desk."""
    with sync_playwright() as p:
        b, pg, errors = phone(p, turned_base + "/app/?mock=1")
        pg.locator(".up-card[data-key='card:turn/173-example-2/talk']").wait_for(timeout=20000)
        pg.locator(".up-card[data-key='card:turn/173-example-2/talk']").click()
        pg.locator(".up-look .hand-lifted[data-kind=turn]").get_by_role("button", name="Open it").click()
        pg.wait_for_selector("[data-spread=track] .mf-foot", timeout=5000)
        drop = pg.locator("[data-spread=track] [data-way=drop]")
        drop.first.click()
        pg.wait_for_timeout(600)
        got = [a for n, a in pg.evaluate(SENT) if n == "ideas.drop"]
        assert got == [{"slug": "173-example-2", "from": "hand"}], got
        assert not errors, errors
        b.close()


# -- goal "The battle and the gate", stage M: the battle and the gate on the phone (decisions §303; goal 171 I) -----------------------------------------------------------
# On the `gui` fixture's host (`?table=cards`, no ?mock=1) at 390 x 844 with touch: each mat opened from its address after a reload is the whole screen with *Back*, upright in the desktop's
# order, its ways a row at the screen's foot that scrolls within itself, the seal after them in the screen's order and Tab's; no sideways scroll, no card cut, no text under 12 px as drawn.
from tests import test_cards_battle_browser as battle_kit  # noqa: E402
from tests import test_cards_gate_browser as gate_kit  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

TOUCH = dict(has_touch=True, is_mobile=True)
NO_CUT = """(k) => { const sp = document.querySelector(`[data-spread=${k}]`), f = sp.querySelector('.mf-field'), fr = f.getBoundingClientRect(), bad = [];
  if (f.scrollHeight - f.clientHeight > 1 || f.scrollWidth - f.clientWidth > 1) bad.push('the field scrolls');
  for (const e of f.querySelectorAll('.mf-zone, .mf-zl, .sp-card, .bt-one, .bt-line, .gt-line, .gt-agree')) { const r = e.getBoundingClientRect();
    if (r.width && (r.top < fr.top - 1 || r.bottom > fr.bottom + 1 || r.left < fr.left - 1 || r.right > fr.right + 1)) bad.push(e.className.toString().slice(0, 30)); }
  const small = [...sp.querySelectorAll('*')].filter((n) => n.children.length === 0 && n.textContent.trim() && !n.closest('[aria-hidden=true]') && parseFloat(getComputedStyle(n).fontSize) < 12).map((n) => n.textContent.trim().slice(0, 20));
  const ways = sp.querySelector('.sp-cards'), row = ways ? getComputedStyle(ways).overflowX : '';
  return { bad, small, row, sideways: document.documentElement.scrollWidth > innerWidth }; }"""
STOP = """(k) => { const a = document.activeElement, sp = document.querySelector(`[data-spread=${k}]`); if (!sp || !sp.contains(a)) return ['outside', true];
  const f = a.closest('.bt-line, .gt-line') ? 'line' : a.closest('.bt-yours, .gt-yours') ? 'yours' : a.closest('.gt-guards') ? 'guards' : a.closest('[data-old]') ? a.closest('[data-old]').dataset.old : '';
  return [f || a.dataset.way || (a.classList.contains('mf-seal') ? 'seal' : a.classList.contains('sp-shut') ? 'back' : a.tagName), a.matches(':focus-visible')]; }"""


def mat_page(gui, address):
    server, browser = gui
    pg = browser.new_page(viewport={"width": 390, "height": 844}, **TOUCH)
    seen = []
    pg.on("pageerror", lambda e: seen.append(str(e)))
    pg.goto(server.url + ("&table=cards" if "?" in server.url else "?table=cards") + address)
    return pg, seen


def tab_order(pg, kind):
    """What Tab reaches in the mat, in order, from its first stop until it comes round; each with a visible focus."""
    names = []
    for _ in range(40):
        pg.keyboard.press("Tab")
        got = pg.evaluate(STOP, kind)
        assert got[1], got
        if names and got[0] == names[0]:
            break
        if not names or names[-1] != got[0]:
            names.append(got[0])
    return names


def test_the_battle_opened_from_its_address_after_a_reload_is_the_whole_screen_upright_with_back_and_its_ways_a_row_that_scrolls(gui):
    pg, _host = battle_kit.opened(gui, 390, 844, **TOUCH)
    pg.evaluate("() => import('/static/js/cards/spreads/open.js').then((m) => m.openSpread({ kind: 'battle', slug: 'timer' }))")
    pg.reload()                                                                                          # its address opens it again
    sp = pg.locator("[data-spread=battle]")
    sp.locator("[data-old]").first.wait_for(timeout=WAIT_MS)
    assert sp.locator(".mf").bounding_box()["width"] >= 388 and sp.locator(".sp-shut").inner_text().strip() == "Back"
    ys = [sp.locator(sel).first.bounding_box()["y"] for sel in (".bt-against", ".bt-line", ".bt-yours", ".sp-cards", ".mf-seal")]
    assert ys == sorted(ys)                                                                              # the desktop's order, the ways, then the seal
    got = pg.evaluate(NO_CUT, "battle")
    assert got["bad"] == [] and got["small"] == [] and got["row"] == "auto" and not got["sideways"], got
    names = tab_order(pg, "battle")
    assert [n for n in names if n in ("§212", "§213", "line", "new", "old", "words", "seal", "back")] == ["§212", "§213", "line", "new", "old", "words", "seal", "back"], names
    pg.keyboard.press("Escape")
    pg.wait_for_selector("[data-spread=battle]", state="detached", timeout=WAIT_MS)
    pg.close()


def test_the_phones_battle_card_opens_it_and_new_wins_from_it_is_sent_from_the_hand(gui):
    pg, host = battle_kit.opened(gui, 390, 844, **TOUCH)
    spy = battle_kit.Spy(host, [0])
    try:
        card = pg.locator("[data-key='card:battle/timer']")                                             # its card in the phone's row
        card.wait_for(state="attached", timeout=WAIT_MS)
        card.click()
        pg.locator("[data-spread=battle] [data-old]").first.wait_for(timeout=WAIT_MS)
        pg.locator("[data-spread=battle] .sp-cards [data-way=new]").click()
        pg.locator("[data-spread=battle]").wait_for(state="detached", timeout=WAIT_MS)
        assert spy.sent("ideas.conflict") == [{"idea": "timer", "number": 212, "choice": "replace", "from": "hand"}]
    finally:
        spy.close()
        pg.close()


@pytest.mark.parametrize("red", [True, False])
def test_the_gate_opened_from_its_address_after_a_reload_is_the_whole_screen_upright_with_back_the_ways_then_the_seal(gui, red):
    server, _b = gui
    slug = "phone-red" if red else "phone-green"
    gate_kit.lay(server, slug, red=red)
    pg, seen = mat_page(gui, f"#mat=gate:{slug}")
    pg.reload()
    gate = pg.locator("[data-spread=gate]")
    gate.locator(".gt[data-way]:not([data-way=''])").wait_for(timeout=WAIT_MS)
    assert gate.locator(".mf").bounding_box()["width"] >= 388 and gate.locator(".sp-shut").inner_text().strip() == "Back"
    sels = [".gt-guards", ".gt-line", ".gt-yours", *([".sp-cards"] if red else []), ".mf-seal"]
    ys = [gate.locator(sel).first.bounding_box()["y"] for sel in sels]
    assert ys == sorted(ys)
    got = pg.evaluate(NO_CUT, "gate")
    assert got["bad"] == [] and got["small"] == [] and not got["sideways"], got
    assert gate.locator(".mf-phase.is-on").inner_text().strip().lower() == "work"                       # the goal's own phase, as the desk reads it
    names = tab_order(pg, "gate")
    assert names.index("guards") < names.index("seal") < names.index("back"), names                      # the cards of Yours and the line are no act: Tab goes guards, the ways, the seal, Back
    if red:
        assert got["row"] == "auto" and names.index("guards") < names.index("fix") < names.index("stale") < names.index("seal"), names
    gate.locator(".sp-shut").click()                                                                     # Back puts it away
    pg.wait_for_selector("[data-spread=gate]", state="detached", timeout=WAIT_MS)
    assert "#mat=" not in pg.url and not seen
    pg.close()
