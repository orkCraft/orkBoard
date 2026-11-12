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


def test_the_stages_of_a_route_are_a_pile_the_one_now_and_the_ones_to_come_face_down(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.evaluate("""async (slug) => { const st = await import("/static/js/shell/store.js"), sp = await import("/static/js/cards/spreads/open.js");
          const m = st.mapData.value; const route = ["tech", "design", "product", "release"].map((party, i) => ({ step: "party", party, goal: slug, at: "", state: i === 0 ? "done" : i === 1 ? "running" : "waiting", done: 1, total: 2 }));
          st.mapData.value = { ...m, nodes: m.nodes.map((n) => n.slug === slug ? { ...n, state: "running", route } : n) }; sp.openSpread({ kind: "track", slug }); }""", THREE)
        spread = pg.locator("[data-spread=track]")
        spread.wait_for()
        assert spread.locator(".sp-pile .sp-card").count() == 1 and spread.locator(".sp-pile .sp-chk").count() == 1
        assert spread.locator(".sp-now .sp-card.is-xl").count() == 1
        assert spread.locator("button.sp-back").count() == 2                     # two to come, face down, each pressed to turn
        spread.locator("button.sp-back").first.click()
        assert spread.locator("button.sp-back").count() == 1 and spread.locator(".sp-ahead .sp-card").count() == 1
        pg.get_by_role("button", name="Show what comes").click()
        assert spread.locator(".sp-back").count() == 0
        pg.keyboard.press("Escape")
        assert pg.locator(".sp-veil").count() == 0
        b.close()


def test_the_gate_opens_from_a_goal_to_review_and_to_main_waits_for_its_checks(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.evaluate("""async () => { const st = await import("/static/js/shell/store.js"); const m = st.mapData.value;
          st.mapData.value = { ...m, nodes: m.nodes.map((n) => n.state === "ready" ? { ...n, state: "review" } : n) }; }""")
        pg.locator(".cards-dealer .cards-row .cards-s[data-goal]").first.click()
        pg.get_by_role("button", name="At the gate").click()
        gate = pg.locator("[data-spread=gate]")
        gate.wait_for()
        assert gate.locator(".sp-gate__mid .sp-card.is-portal").count() == 1 and gate.locator(".sp-ring").count() == 1
        assert gate.locator(".sp-gk").count() >= 3 and gate.locator(".sp-gk[data-check=waiting] .sp-back").count() >= 2
        main = gate.get_by_role("button", name="To main opens after", exact=False)
        assert main.is_disabled()
        pg.keyboard.press("Escape")
        assert pg.locator(".sp-veil").count() == 0
        b.close()


def test_the_gate_turns_a_check_green_and_opens_to_main_when_all_are_green(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.evaluate("""async (slug) => { const link = await import("/static/js/link.js"), sp = await import("/static/js/cards/spreads/open.js");
          const names = ["Critical tests", "Tests of what it touched"];
          link.town.value = { ...link.town.value, main_checks: { [slug]: names.map((name, i) => ({ name, state: i ? "failed" : "passed", words: i ? "2 tests fail" : "312 passed" })) } };
          sp.openSpread({ kind: "gate", slug }); }""", THREE)
        gate = pg.locator("[data-spread=gate]")
        gate.wait_for()
        assert gate.locator(".sp-gk[data-check=passed] .sp-chk").count() >= 1
        assert gate.locator(".sp-gk[data-check=failed] .sp-chk.is-no").count() == 1       # red stays face up, with what failed
        assert "2 tests fail" in gate.inner_text()
        assert "sealed" in gate.get_by_role("button", name="To main is sealed", exact=False).inner_text()
        b.close()


def test_a_posts_words_open_before_and_after_from_its_act_and_close_with_esc(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.locator("article.cards-m:not([data-mat]) .post-card__text").first.click()       # a word, no mat: its L's act
        pg.get_by_role("button", name="What changed").click()
        diff = pg.locator("[data-spread=diff]")
        diff.wait_for()
        assert diff.locator(".sp-l").count() == 2
        assert "Before: not recorded" in diff.locator(".sp-l.is-before").inner_text()       # the recording holds no words before
        assert diff.locator(".sp-l.is-before").get_attribute("class").count("is-lit") == 0
        pg.keyboard.press("ArrowLeft")
        assert "is-lit" in diff.locator(".sp-l.is-before").get_attribute("class")
        pg.keyboard.press("Escape")
        assert pg.locator(".sp-veil").count() == 0
        assert pg.evaluate("document.activeElement.classList.contains('cards-m')")
        b.close()


def test_a_post_that_carries_its_words_before_marks_what_was_taken_out_and_put_in(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        opened(pg, page_url)
        pg.evaluate("""async () => { const sp = await import("/static/js/cards/spreads/open.js");
          sp.openSpread({ kind: "diff", p: { leader: "tech", at: "2026-11-11T11:42:51+00:00", kind: "change", goal: "163-products-tree-on-the-board",
            text: "It jumps again, half as high, once.", before: "It jumps again, as high as the first, any number of times." } }); }""")
        diff = pg.locator("[data-spread=diff]")
        diff.wait_for()
        assert diff.locator(".sp-l.is-before del").count() >= 1 and diff.locator(".sp-l:not(.is-before) ins").count() >= 1
        assert "Before: not recorded" not in diff.inner_text()
        b.close()


def test_the_page_without_cards_has_no_spread_and_no_new_act(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url)
        pg.wait_for_timeout(1500)
        assert pg.locator(".sp-veil, .cards-s").count() == 0
        b.close()
