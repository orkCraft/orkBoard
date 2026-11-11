"""**The discard as cards** (goal 170): on mocks the right column draws its goals as S cards: under the plate *main* the goal ready for
main ringed with its act *To main* as a button beside it, under the plate *dev* the goals waiting for dev. No count. The recording holds
no goal done, so the test lays some into the page's own signals (the Board's map, the gate, the Board's rows)."""
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

LAY = """async () => {
  const { mapData, gateData } = await import("/static/js/shell/store.js");
  const { board } = await import("/static/js/board/store.js");
  const m = mapData.value, goal = m.goals[0].slug;
  const node = (slug, title, extra) => ({ ...m.nodes[0], slug, title, short: title, goal, place: "discard", state: "done", ...extra });
  mapData.value = { ...m, nodes: [...m.nodes,
    node("g-ready", "Sign-in", {}), node("g-more", "Combo scoring", {}),
    node("g-seen", "The timer's rules", {}), node("g-wait", "A sound at the round's end", {})] };
  gateData.value = { same: false, into: "dev", main: "main", commits: 3, files: 4, off: false, ideas: [{ slug: "g-ready", title: "Sign-in", goal }, { slug: "g-more", title: "Combo scoring", goal }] };
  board.value = { ...(board.value || {}), review: true, ideas: [...(board.value?.ideas || []), { slug: "g-wait", waits_for_dev: true }] };
}"""


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def test_the_discard_draws_s_cards_under_both_plates_and_to_main_is_a_button(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        pg.locator(".mock-plate__b").wait_for(timeout=15000)
        pg.evaluate(LAY)
        lane = pg.locator(".release-lane")
        lane.locator("[data-plate=main]").wait_for(timeout=5000)
        assert lane.locator("[data-plate=dev]").count() == 1
        cards = lane.locator("button.ork-card.cards-s")
        assert cards.count() >= 4
        ready = lane.locator("[data-goal=g-ready]")
        assert ready.get_attribute("data-portal-card") == "g-ready"
        assert "is-ready" in ready.get_attribute("class")
        assert lane.locator(".ork-portal-ring").count() == 1
        # the ratio of an S card is 2.5 : 3.5
        box = ready.bounding_box()
        assert abs(box["width"] / box["height"] - 2.5 / 3.5) < 0.03
        # the goals waiting for dev are cards under the dev plate, none of them post cards
        assert lane.locator("[data-pile=lower] button.ork-card.cards-s[data-goal=g-wait]").count() == 1
        assert lane.locator(".post-card").count() == 0
        # To main is a button with its word, beside the ready card
        btn = lane.locator("button[data-act=to_main]")
        assert btn.count() == 1 and btn.inner_text().strip() == "To main"
        assert btn.bounding_box()["x"] > box["x"] + box["width"] - 1
        # two to a row: the goals that are not the ready one lie side by side
        a, c = lane.locator("[data-goal=g-more]").bounding_box(), lane.locator("[data-goal=g-seen]").bounding_box()
        assert abs(a["y"] - c["y"]) < 4 and a["x"] != c["x"]
        # no count anywhere in the column
        assert "goals ready" not in lane.inner_text()
        b.close()
