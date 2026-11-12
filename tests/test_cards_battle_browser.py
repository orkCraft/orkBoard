"""**A battle** (goal 170, decisions §298.6; goal 171 G), on mocks (`?mock=1`): the host lays no battle (gui/ideas_mats.py holds none: *Out* of spec 171, the battles' own goal), so
the page deals no battle card into the hand and the Orkmaster's spread of one, opened for a goal, draws nothing, never an example. What stays true of a battle is its words, which are pure:
the old cards it goes against said by kind, and its four ways with their lines. The cases that pressed a battle card (its emblem, *vs <what>*, *Settle it*; the spread with the new card, the old
ones, three axes and the cost to undo; a way sending `ideas.battle_settle`; the phone's stack) laid a battle only the mock's `proposed.battles` held; they come back with the battles' goal,
which lays a battle in the host's answer."""
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
CARD = ".frame-hand button.hand-card[data-kind=battle]"


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(pg, url):
    pg.goto(url + "?mock=1")
    pg.locator(".mock-plate__b").wait_for(timeout=15000)
    pg.locator(".cards-s[data-goal]").first.wait_for(timeout=15000)


def test_the_page_deals_no_battle_card_and_the_spread_of_a_goal_with_none_draws_nothing(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        assert pg.locator(CARD).count() == 0 and pg.locator("[data-kind=battle]").count() == 0
        slug = pg.locator(".cards-s[data-goal]").first.get_attribute("data-goal")
        pg.evaluate("(slug) => import('/static/js/cards/spreads/open.js').then((m) => m.openSpread({ kind: 'battle', slug }))", slug)
        pg.wait_for_timeout(300)
        assert pg.locator("[data-spread=battle]").count() == 0
        b.close()


def test_a_battle_says_what_it_goes_against_by_kind_and_has_four_ways_each_with_its_line(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        got = pg.evaluate("""() => import('/static/js/cards/spreads/battle.js').then((m) => {
            const d = { kind: 'decision' }, g = { kind: 'goal' };
            return { words: [[d, g], [d], [g, g], [d, d, g]].map((a) => m.againstWords(a)), ways: m.waysOf([d, g]).map((w) => [w.id, w.name, w.line]), only: m.waysOf([g]).map((w) => w.line)[0] };
        })""")
        assert got["words"] == ["a decision and a goal", "a decision", "two goals", "two decisions and a goal"]
        assert [w[:2] for w in got["ways"]] == [["new_wins", "New wins"], ["old_wins", "Old wins"], ["merge", "Merge"], ["not_a_battle", "Not a battle"]]
        assert got["ways"][0][2] == "the old goal reopens as a change; the old decision is replaced by a new one, never edited"
        assert [w[2] for w in got["ways"][1:]] == ["the new card is dropped, or changed to fit", "the leaders write one card of both", "the Orkmaster read it wrong"]
        assert got["only"] == "the old goal reopens as a change"
        b.close()
