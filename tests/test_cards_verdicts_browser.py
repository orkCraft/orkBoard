"""**Craft tokens and slips** (goal 170, decisions §298.3 to §298.5), drawn over the table of cards on mocks (`?mock=1`): a feature's S has the tokens of
Product, Tech and Design, a bug's Tech's alone; a token's squares are its checks (ok, question, risk, risk that blocks); a card with a blocking risk is
ringed, says *blocked* and holds its act; a token pressed lays its slip, Esc puts it away; an opened card lies on its slips, with a reply under each and
*Ask <leader>…* under it. What is sent is only kept by the mock."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser
SENT = "() => import('/static/js/mock/mocklink.js').then((m) => m.sent.value.map((x) => ({name: x.name, args: x.args})))"
VERDICTS = "() => import('/static/js/link.js').then((l) => l.proposed('verdicts'))"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal] .cards-ct").first.wait_for(timeout=15000)


def lane_card(pg, slug):
    return pg.locator(f".cards-lanes .cards-s[data-goal='{slug}']").first


def test_a_feature_has_three_tokens_with_their_squares_and_a_bug_tech_alone(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        verdicts = pg.evaluate(VERDICTS)
        feature = next(s for s, v in verdicts.items() if len(v) == 3 and pg.locator(f".cards-lanes .cards-s[data-goal='{s}']").count())
        card = lane_card(pg, feature)
        toks = card.locator(".cards-ct")
        assert toks.count() == 3
        for i, v in enumerate(verdicts[feature]):
            for kind in ("ok", "q", "r", "b"):
                want = sum(1 for c in v["checks"] if c["kind"] == kind)
                assert toks.nth(i).locator(f".cards-sq[data-kind='{kind}']").count() == min(want, 5)
            assert toks.nth(i).get_attribute("aria-label").startswith(("Tech", "Design", "Product"))
            assert toks.nth(i).locator(".ork-tool").count() == 1
        bug = next(s for s, v in verdicts.items() if len(v) == 1 and v[0]["leader"] == "tech" and pg.locator(f".cards-lanes .cards-s[data-goal='{s}']").count())
        assert lane_card(pg, bug).locator(".cards-ct").count() == 1
        assert lane_card(pg, bug).locator(".cards-ct").first.get_attribute("data-leader") == "tech"
        b.close()


def test_the_aria_label_says_the_counts_in_words(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        verdicts = pg.evaluate(VERDICTS)
        slug, v = next((s, v[0]) for s, v in verdicts.items() if pg.locator(f".cards-lanes .cards-s[data-goal='{s}']").count() and v[0]["leader"] == "tech")
        label = lane_card(pg, slug).locator(".cards-ct[data-leader='tech']").get_attribute("aria-label")
        oks = sum(1 for c in v["checks"] if c["kind"] == "ok")
        assert label.startswith("Tech: ") and f"{oks} approved" in label
        b.close()


def test_a_blocked_card_is_ringed_says_blocked_and_holds_its_act(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        verdicts = pg.evaluate(VERDICTS)
        slug = next(s for s, v in verdicts.items() if any(c["kind"] == "b" for x in v for c in x["checks"]))
        card = pg.locator(f".cards-s[data-goal='{slug}']").first
        assert "is-blocked" in card.get_attribute("class")
        assert card.locator(".cards-c--bl").inner_text().strip() == "blocked"
        assert card.locator(".cards-sq[data-kind='b']").count() == 1
        assert pg.evaluate(f"() => import('/static/js/cards/verdict.js').then((m) => m.blocked('{slug}'))") is True
        held = card.locator(".cards-act")
        assert held.count() == 0 or (held.first.is_disabled() and "blocks" in held.first.get_attribute("title"))
        b.close()


def test_a_token_pressed_lays_its_slip_with_its_checks_and_esc_puts_it_away(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        verdicts = pg.evaluate(VERDICTS)
        slug = next(s for s, v in verdicts.items() if len(v) == 3 and pg.locator(f".cards-lanes .cards-s[data-goal='{s}']").count())
        tok = lane_card(pg, slug).locator(".cards-ct").first
        want = verdicts[slug][0]["checks"]
        tok.click()
        slip = pg.locator(".cards-beside .cards-slip")
        slip.wait_for()
        assert slip.locator("li").count() == len(want)
        assert slip.locator(".cards-sq").count() == len(want)
        assert tok.get_attribute("aria-expanded") == "true"
        assert pg.locator(".cards-thread").count() == 1
        pg.keyboard.press("Escape")
        assert pg.locator(".cards-beside").count() == 0
        assert pg.evaluate("() => document.activeElement.classList.contains('cards-ct')")
        tok.click()
        slip.wait_for()
        tok.click()
        assert pg.locator(".cards-beside").count() == 0
        b.close()


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
        assert pg.evaluate("() => document.activeElement.dataset.reply") == "tech"
        slip.get_by_role("button", name="Reply to Tech").click()
        slip.locator("textarea").fill("Does the phone keep its own order?")
        slip.get_by_role("button", name="Send to Tech").click()
        pg.wait_for_function("() => document.body.innerText.includes('Sent to Tech')")
        sent = pg.evaluate(SENT)
        assert {"name": "ideas.reply", "args": {"slug": slug, "leader": "tech", "text": "Does the phone keep its own order?"}} in sent
        card, ask = pg.locator(".cards-l").bounding_box(), pg.locator(".cards-ask").bounding_box()
        assert pg.locator(".cards-l .cards-ask").count() == 1 and ask["y"] + ask["height"] <= card["y"] + card["height"] + 1      # inside the card, never over the hand
        assert pg.locator(".cards-ask textarea").count() == 0
        heads = pg.locator(".cards-ask__b")
        assert heads.count() >= 4 and pg.locator(".cards-ask__one small").count() >= 1 and "not on its route" in pg.locator(".cards-ask__one small").first.inner_text()
        pg.locator(".cards-ask__b[data-ask='design']").click()
        pg.locator(".cards-ask [data-field='design'] textarea").fill("Which size first?")
        pg.locator(".cards-ask").get_by_role("button", name="Send to Design").click()
        pg.wait_for_function("() => document.body.innerText.includes('Sent to Design')")
        assert {"name": "ideas.ask_leader", "args": {"slug": slug, "leader": "design", "text": "Which size first?"}} in pg.evaluate(SENT)
        pg.keyboard.press("Escape")
        assert pg.locator(".cards-stage").count() == 0
        b.close()


def test_on_a_phone_the_slips_stand_in_a_column_under_the_card(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 390, "height": 844})
        pg.goto(page_url + "?mock=1")
        pg.wait_for_timeout(1500)
        verdicts = pg.evaluate(VERDICTS)
        pg.evaluate("""(slug) => import('/static/js/cards/card.js').then((m) => m.openCard({ kind: 'goal', n: { slug, title: 'A goal', leader: 'tech' }, line: 'at work', from: null, acts: [] }))""",
                    next(s for s, v in verdicts.items() if len(v) == 3))
        pg.locator(".cards-stage").wait_for()
        card, slip = pg.locator(".cards-l").bounding_box(), pg.locator(".cards-slip").first.bounding_box()
        assert slip["y"] >= card["y"] + card["height"] - 2
        b.close()


def test_every_party_has_its_races_tool_and_colour(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        got = pg.evaluate("""() => Promise.all([import('/static/js/cards/verdict.js'), import('/static/js/table/post.js')]).then(([v]) =>
            ['tech', 'design', 'product', 'release'].map((s) => [s, v.raceIn(s), v.TOOLS[v.raceIn(s)]]))""")
        assert got == [["tech", "ork", "drum-gear"], ["design", "elf", "bow-drip"], ["product", "knight", "map-cross"], ["release", "undead", "hourglass-candle"]]
        b.close()
