"""**The leaders' tables on mocks** (goal 170, stage T; docs/mockups/frameworks/): a leader's lane has a switch in its head, *Feed* and its framework's
name; the framework is drawn in the pane in place of the lanes (Tech's Architecture, read from this repository's code (realm/code_layers.py);
Product's Jobs to be done, examples). The person never moves a card or puts a token (decisions §298.5): it turns one over, spreads a pile, and asks
the leader about a part (`ideas.ask_leader`, proposed, logged by the mock)."""
from __future__ import annotations

import json
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


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/?mock=1"
    s.shutdown()


def open_table(pg, party: str, framework: str):
    pg.locator(f'.cards-lane[data-party="{party}"] [data-value="{framework}"]').click()
    pg.wait_for_selector(f'.tb[data-framework="{framework}"]')


def box(pg, card: str):
    return pg.locator(f'[data-card="{card}"]').bounding_box()


def test_the_switch_shows_each_leaders_framework_and_feed_brings_the_lanes_back(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_selector(".cards-lane", timeout=15000)
        # only the parties with a framework have the switch; Design's lane is as it was
        assert pg.locator(".cards-lane .tb-switch").count() == 2
        assert pg.locator('.cards-lane[data-party="design"] .tb-switch').count() == 0
        assert [t.strip() for t in pg.locator('.cards-lane[data-party="tech"] .tb-switch .ork-btn').all_inner_texts()] == ["Feed", "Architecture"]
        open_table(pg, "tech", "architecture")
        assert pg.locator(".cards-lanes").evaluate("el => !!el.closest('[inert]')")           # the lanes lie under the mat, inert (goal 171 H)
        assert pg.get_by_text("Tech's table", exact=True).is_visible()
        assert [t.strip() for t in pg.locator(".tb-layer .tb-ln").all_inner_texts()][0].startswith("Outside")
        for layer in ("outside", "faces", "engine", "words"):
            assert pg.locator(f'[data-layer="{layer}"]').count() == 1
        assert "tests/test_architecture.py" in pg.locator(".tb-rules").inner_text()
        # a module that reaches up carries Tech's own risk token
        assert pg.locator('[data-card="realm/goal_route.py"] .cards-tok[data-view="risk"]').count() == 1
        pg.locator('.tb [data-value="feed"]').click()
        pg.wait_for_selector(".cards-lanes")
        assert pg.locator(".tb").count() == 0
        open_table(pg, "product", "jtbd")
        text = pg.locator(".tb-jtbd").inner_text()
        assert "When" in text and "I want" in text and "example" in text
        for force in ("push", "pull", "anxiety", "habit"):
            assert pg.locator(f'[data-force="{force}"]').count() == 1
        assert pg.locator('[data-card="orkboard"].is-hired').count() == 1 and pg.locator('[data-card="tabs"].is-fired').count() == 1
        b.close()


def test_a_pile_spreads_on_press_and_a_card_turns_over_on_press(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_selector(".cards-lane", timeout=15000)
        open_table(pg, "tech", "architecture")
        pile = pg.locator('[data-card="gui/"]')
        assert pile.get_attribute("aria-expanded") == "false" and pg.locator('[data-spread="gui/"]').count() == 0
        pile.click()
        assert pile.get_attribute("aria-expanded") == "true"
        assert pg.locator('[data-spread="gui/"] [data-card="gui/board_host.py"]').is_visible()
        pile.click()
        assert pg.locator('[data-spread="gui/"]').count() == 0
        # a card turns over, and back
        card = pg.locator('[data-card="vscode/"]')
        assert card.get_attribute("aria-pressed") == "false" and "lines" not in card.inner_text()
        card.click()
        assert card.get_attribute("aria-pressed") == "true" and "lines" in card.inner_text()
        card.click()
        assert card.get_attribute("aria-pressed") == "false"
        # Jobs to be done: the personas' pile, the smaller jobs' pile, the face-down fired card
        pg.locator('.tb [data-value="feed"]').click()
        open_table(pg, "product", "jtbd")
        assert pg.locator('[data-spread="personas"]').count() == 0
        pg.locator('[data-spread-of="personas"]').click()
        assert pg.locator('[data-spread="personas"] [data-card="lead"]').is_visible()
        pg.locator('[data-card="pile:jobs"]').click()
        assert pg.locator('[data-spread="jobs"] [data-card="waits"]').is_visible()
        assert pg.locator('[data-card="todo"]').count() == 0
        pg.locator('[data-card="face-down"]').click()
        assert pg.locator('[data-card="todo"]').is_visible()
        b.close()


def test_the_person_asks_the_leader_about_a_part_and_puts_no_token(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_selector(".cards-lane", timeout=15000)
        open_table(pg, "tech", "architecture")
        # no token in the hand, none on the table; the foot says what to do
        assert pg.locator("[data-token], .tb-takes, .tb-you").count() == 0
        assert "Press a card to turn it over; ask its leader about any part." in pg.locator(".tb-hand").inner_text()
        pg.locator('[data-card="gui/"]').click()
        card = pg.locator('[data-card="gui/board_host.py"]')
        assert pg.locator("[data-ask-part]").count() == 0
        card.click()
        assert card.get_attribute("aria-pressed") == "true"
        pg.get_by_role("button", name="Ask Tech about this part").click()
        pg.get_by_role("textbox", name="Your words to Tech about this part").fill("805 lines, past the ~600 a module may grow to. Split it?")
        pg.get_by_role("button", name="Send to Tech").click()
        assert pg.locator(".tb-asked").inner_text() == "Sent to Tech"
        pg.locator(".mock-plate__b").click()
        assert "ideas.ask_leader" in pg.locator(".mock-plate__sent").inner_text()
        got = pg.evaluate("""() => import("/static/js/mock/mocklink.js").then((m) => m.sent.value.filter((s) => s.name === "ideas.ask_leader").map((s) => s.args))""")
        assert got == [{"party": "tech", "framework": "architecture", "card": "gui/board_host.py", "text": "805 lines, past the ~600 a module may grow to. Split it?", "sealed": True}], json.dumps(got)
        # Product's table: the same, Enter sends
        pg.locator('.tb [data-value="feed"]').click()
        open_table(pg, "product", "jtbd")
        assert pg.locator("[data-token]").count() == 0
        pg.locator('[data-card="lead"], [data-card="pile:solo"]').first.click()
        pg.locator('[data-card="pile:jobs"]').click()
        pg.locator('[data-spread="jobs"] [data-card="waits"]').click()
        pg.get_by_role("button", name="Ask Product about this part").click()
        pg.get_by_role("textbox", name="Your words to Product about this part").fill("Is this a job of its own?")
        pg.keyboard.press("Enter")
        assert pg.locator(".tb-asked").count() == 1
        b.close()


def test_no_card_moves_the_person_only_turns_spreads_and_asks(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_selector(".cards-lane", timeout=15000)
        open_table(pg, "tech", "architecture")
        pg.wait_for_timeout(300)
        before = {c: box(pg, c) for c in ("core/", "design/", "vscode/", "realm/goal_route.py")}
        assert pg.locator('.tb-body [draggable="true"]').count() == 0
        # a drag from a card to another place leaves every card where it lies
        a, z = box(pg, "core/"), box(pg, "design/")
        pg.mouse.move(a["x"] + 40, a["y"] + 60); pg.mouse.down(); pg.mouse.move(z["x"] + 200, z["y"] + 80, steps=8); pg.mouse.up()
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(300)
        after = {c: box(pg, c) for c in before}
        assert after == before
        b.close()
