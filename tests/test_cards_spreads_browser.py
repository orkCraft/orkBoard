"""**The first three spreads** (goal 170, docs/mockups/spreads/): the stages of a goal, a goal at the gate and a post's words before and
after, drawn over the table of cards on mocks (`?mock=1`). Each opens from its act in a card's L, shows its parts, closes with Esc and
gives the focus back; the current faces are unchanged without cards."""
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
THREE = "163-products-tree-on-the-board"     # a goal of the recording whose route has three stages


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


def test_the_stages_open_from_a_goals_act_and_close_with_esc(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        card = pg.locator(".cards-dealer .cards-row .cards-s[data-goal]").first
        card.click()
        pg.get_by_role("button", name="Its stages").click()
        spread = pg.locator("[data-spread=track]")
        spread.wait_for()
        assert pg.locator(".cards-l").count() == 0                              # the L went when the spread came
        assert spread.locator(".sp-meeple").count() == 1 and "at work" in spread.inner_text()
        assert pg.get_by_role("button", name="Close").is_visible()
        assert pg.evaluate("document.activeElement.classList.contains('sp-shut')")
        pg.keyboard.press("Escape")
        assert pg.locator(".sp-veil").count() == 0
        assert pg.evaluate("document.activeElement === document.querySelector('.cards-dealer .cards-row .cards-s[data-goal]')")
        b.close()




def test_the_gate_opens_from_a_goal_to_review_upright_with_what_its_tests_guard_and_its_seal_dim_while_a_check_disagrees(page_url):
    """The gate is a battle nobody disputes (goal "The battle and the gate" L): no ring, the host's `ideas.gate_guards` laid as zones, the seal dim with its why."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.evaluate("""async () => { const st = await import("/static/js/shell/store.js"); const m = st.mapData.value;
          st.mapData.value = { ...m, nodes: m.nodes.map((n) => n.state === "ready" ? { ...n, state: "review" } : n) }; }""")
        pg.locator(".cards-dealer .cards-row .cards-s[data-goal]").first.click()
        pg.get_by_role("button", name="At the gate").click()
        gate = pg.locator("[data-spread=gate]")
        gate.locator(".gt-line").wait_for()
        assert gate.locator(".sp-ring, .sp-gate, .sp-gk").count() == 0
        assert gate.locator(".mf-zl").all_text_contents() == ["What its tests guard", "Yours"]
        assert gate.locator(".gt-guards .sp-card[data-cardkind=decision]").count() == 1 and gate.locator(".gt-guards .sp-card[data-cardkind=part]").count() == 1
        seal = gate.locator(".mf-seal")
        assert seal.get_attribute("aria-disabled") == "true" and "2 checks disagree" in seal.inner_text()
        pg.keyboard.press("Escape")
        assert pg.locator(".sp-veil").count() == 0
        b.close()






