"""**The phone's header, round button and turns on the table of cards** (goal 170, decisions §298.7, §298.9), on mocks (`/app/?mock=1`) at 390 x 844 with touch: the header holds two bottles at most (the default and the one
that runs out first) and *+n* for the rest, then the chain and **Yours**, a menu of *Inventory* and *History* (*Settings* when the header gave way); the round button's fan is *New goal* and *Play* only, the button showing a cross
while it is open; a card at its turns lies in the foot's hand and opens its ways, a battle's card opens the battle spread. Set `ORK_SHOTS` to a folder to leave screenshots there."""
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
LIMITS = """() => import('/app/page/js/link.js').then(({ town }) => {
  const row = (name, left) => ({ provider: name.toLowerCase(), name, left, rows: [{ window: "5h", left, reset: "" }] });
  town.value = { ...town.value, limits: [row("Claude", 0.7), row("Codex", 0.4), row("Gemini", 0.1), row("Qwen", 0.9)], mana: { main: "claude", now: "claude", until: null, moved: null, paid: null } };
})"""


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
    pg.locator(".up-row").wait_for(timeout=20000)
    pg.locator(".up-card").first.wait_for(timeout=20000)
    return b, pg, errors


def test_the_header_holds_two_bottles_the_default_and_the_one_that_runs_out_first_then_plus_n(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        pg.evaluate(LIMITS)
        pots = pg.locator(".up-pots .up-pot:not(.up-pot--more)")
        pots.first.wait_for(timeout=5000)
        assert pots.count() == 2
        assert pots.nth(0).get_attribute("data-provider") == "claude" and pots.nth(0).get_attribute("data-default") == "1"      # the default first
        assert pots.nth(1).get_attribute("data-provider") == "gemini"                                                           # then the one with the least left
        more = pg.locator(".up-pot--more")
        assert more.count() == 1 and "+2" in more.inner_text()
        pg.wait_for_function("() => document.querySelector('.up-top').dataset.fit === 'none'", timeout=5000)             # the name and Settings gave way: the menu keeps Settings
        for el in pg.locator(".up-top button").all():
            if el.is_visible():
                box = el.bounding_box()
                assert box["width"] >= 43.5 and box["height"] >= 43.5, (el.get_attribute("aria-label"), box)
        more.click()                                                                                                            # the whole row of bottles over the pane
        pg.locator("[data-kind=limits], .over, .frame-table").first.wait_for(timeout=5000)
        narrow.no_sideways(pg)
        assert not errors, errors
        b.close()


def test_yours_opens_its_menu_of_inventory_and_history_and_esc_closes_it(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        yours = pg.get_by_role("button", name="Yours")
        assert yours.get_attribute("aria-haspopup") == "menu" and yours.get_attribute("aria-expanded") == "false"
        box = yours.bounding_box()
        assert box["width"] >= 43.5 and box["height"] >= 43.5
        yours.click()
        menu = pg.get_by_role("menu", name="Yours")
        menu.wait_for(timeout=3000)
        assert yours.get_attribute("aria-expanded") == "true"
        assert menu.get_by_role("menuitem", name="Inventory").is_visible() and "your tools, agents and skills" in menu.inner_text()
        assert menu.get_by_role("menuitem", name="History").is_visible() and "what was decided, what came of it" in menu.inner_text()
        pg.keyboard.press("Escape")
        pg.get_by_role("menu").wait_for(state="detached", timeout=3000)
        assert pg.evaluate("document.activeElement.getAttribute('aria-label')") == "Yours"
        yours.click()                                                                                       # a press outside closes it too
        menu.wait_for(timeout=3000)
        pg.mouse.click(200, 600)
        pg.get_by_role("menu").wait_for(state="detached", timeout=3000)
        yours.click()
        pg.get_by_role("menuitem", name="History").click()                                                  # a pick closes it and opens what it opens today
        pg.get_by_role("menu").wait_for(state="detached", timeout=3000)
        pg.locator(".frame-table, [data-over]").first.wait_for(timeout=5000)
        assert not errors, errors
        b.close()


def test_the_round_buttons_fan_is_new_goal_and_play_only_and_new_goal_opens_the_field(base):
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        assert pg.locator(".up-plus").count() == 0                                                          # the + card is the fan's New goal while there are goals
        fan = pg.locator("button.up-round")
        fan.click()
        opts = pg.locator(".up-fan__opt")
        opts.first.wait_for(timeout=3000)
        assert [t.strip() for t in pg.locator(".up-fan__lab").all_inner_texts()] == ["New goal", "Play"]
        assert pg.get_by_role("button", name="Inventory", exact=True).count() == 0 and pg.get_by_role("button", name="History", exact=True).count() == 0
        assert "is-open" in fan.get_attribute("class") and fan.locator(".ork-icon").count() == 1                 # the cross
        for el in opts.all():
            box = el.bounding_box()
            assert box["height"] >= 43.5, box
        pg.get_by_role("button", name="New goal", exact=True).click()
        pg.locator(".up-field .hand-field, .up-field textarea").first.wait_for(timeout=5000)
        assert pg.locator(".up-fan").count() == 0
        assert not errors, errors
        b.close()


def test_the_phones_hand_deals_no_turn_card_and_no_battle_card_until_stage_k_reads_ideas_turns(base):
    """Was: a turn card in the foot opens its ways, a battle card opens the battle spread: three cards (an idea rated, a spec rated, a battle) laid by the mock's
    `proposed.turns` and `proposed.battles`. The host lays no battle and the hand deals no turn from `ideas.turns` yet (goal 171 stage K), so the row holds none."""
    with sync_playwright() as p:
        b, pg, errors = phone(p, base + "/app/?mock=1")
        assert pg.locator(".up-card[data-key^='card:turn/']").count() == 0 and pg.locator(".up-card[data-kind=stops][data-key$='/battle']").count() == 0
        assert pg.locator("[data-spread=battle]").count() == 0
        narrow.no_sideways(pg)
        assert not errors, errors
        b.close()
