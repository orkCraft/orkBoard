"""**Craft tokens and slips** (goal 170, decisions §298.3 to §298.5), drawn over the table of cards on mocks (`?mock=1`): a feature's S has the tokens of
Product, Tech and Design, a bug's Tech's alone (the leaders' words are the host's `ideas.verdicts`, laid in the recording by tests/mock_kit.py); a token's squares are its checks (ok, question, risk, risk that blocks); a card with a blocking risk is
ringed, says *blocked* and holds its act; a token pressed lays its slip, Esc puts it away; an opened card lies on its slips, with a reply under each and
*Ask <leader>…* under it. What is sent is only kept by the mock."""
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
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => ({name: x.name, args: x.args})))"
# what the host answered to `ideas.verdicts` (the leaders' words, laid by mock_kit.lay_verdicts), as the cards read them: {goal: [{leader, checks}]}
VERDICTS = """() => import('/static/js/cards/verdict.js').then((m) => Object.fromEntries(Object.keys(m.verdicts.value || {}).map((s) => [s, m.verdictsOf(s)])))"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal] .cards-ct").first.wait_for(timeout=15000)


def lane_card(pg, slug):
    return pg.locator(f".cards-lanes .cards-s[data-goal='{slug}']").first










def test_an_opened_goal_lies_on_its_slips_reply_and_ask_send_their_commands(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        verdicts = pg.evaluate(VERDICTS)
        slug = next(s for s, v in verdicts.items() if len(v) == 3 and pg.locator(f".cards-lanes .cards-s[data-goal='{s}']").count())
        lane_card(pg, slug).click(position={"x": 30, "y": 60})
        pg.locator(".cards-stage").wait_for()
        assert pg.locator(".cards-stage .cards-slip").count() == 3
        assert pg.locator(".cards-l .cards-ct").count() == 0 and pg.locator(".cards-l .cards-mark").count() == 3
        assert pg.locator(".cards-stage .cards-slip .cards-ct").count() == 3
        slip = pg.locator("[data-slip='tech']")
        assert pg.locator(".cards-stage textarea").count() == 0                       # every reply is closed until its button is pressed
        slip.get_by_role("button", name="Reply to Tech").click()
        assert pg.locator(".cards-stage textarea").count() == 1 and pg.evaluate("() => document.activeElement.tagName") == "TEXTAREA"
        pg.keyboard.press("Escape")                                                    # closes the field only, the card stays, the focus is back on the button
        assert pg.locator(".cards-stage textarea").count() == 0 and pg.locator(".cards-stage").count() == 1
        pg.wait_for_function("() => document.activeElement?.dataset?.reply === 'tech'", timeout=3000)
        slip.get_by_role("button", name="Reply to Tech").click()
        slip.locator("[data-ask-cost]").filter(has_text="A paid pass: one call, up to $0.06").wait_for(timeout=3000)      # its cost, the host's `ideas.ask_cost` (recorded), is said before Send
        slip.locator("textarea").fill("Does the phone keep its own order?")
        slip.get_by_role("button", name="Send to Tech").click()
        pg.wait_for_function("() => document.body.innerText.includes('Sent to Tech')")
        sent = pg.evaluate(SENT)
        assert {"name": "ideas.reply", "args": {"slug": slug, "leader": "tech", "text": "Does the phone keep its own order?", "sealed": True}} in sent      # a paid pass goes on its seal (stage E)
        assert pg.locator(".cards-l .cards-ask").count() == 1
        assert pg.locator(".cards-ask textarea").count() == 0
        heads = pg.locator(".cards-ask__b")
        assert heads.count() >= 4 and pg.locator(".cards-ask__one small").count() >= 1 and "not on its route" in pg.locator(".cards-ask__one small").first.inner_text()
        pg.locator(".cards-ask__b[data-ask='design']").click()
        pg.locator(".cards-ask [data-field='design'] textarea").fill("Which size first?")
        pg.locator(".cards-ask").get_by_role("button", name="Send to Design").click()
        pg.wait_for_function("() => document.body.innerText.includes('Sent to Design')")
        assert {"name": "ideas.ask_leader", "args": {"slug": slug, "leader": "design", "text": "Which size first?", "sealed": True}} in pg.evaluate(SENT)
        pg.keyboard.press("Escape")
        assert pg.locator(".cards-stage").count() == 0
        b.close()




