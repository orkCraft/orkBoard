"""**A leader's mat** (goal 170; decisions §297): on mocks (`?mock=1`) a leader's M that is a change in its framework or a spread of it
shows its spread's shape and one line at its foot, and opens as that table or spread, the leader's words at its head; a word with
neither opens as an L of words. The closed list: a change in a framework → its table at the part; a change → *What changed*; a concern,
a question or views that differ → *Who says what*."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from tests import mock_kit, narrow  # noqa: E402
from tests.browser_kit import launch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import serve_mock  # noqa: E402

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def page_url():
    s = serve_mock.serve(0, mock_kit.lay_standard)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/"
    s.shutdown()


def opened(p, page_url):
    b = launch(p)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto(page_url + "?mock=1")
    pg.locator(".cards-m[data-mat='table']").first.wait_for(timeout=15000)
    return b, pg


def test_a_mat_shows_its_line_and_its_slots_behind_its_words_never_a_picture_of_its_spread(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        mats = pg.evaluate("[...document.querySelectorAll('.cards-m[data-mat]')].map(m => [m.dataset.mat, m.querySelector('.cards-mat').innerText.trim()])")
        assert {"table", "diff"} == {m[0] for m in mats}, mats
        assert ["table", "Architecture: gui/"] in mats and ["diff", "What changed"] in mats
        assert pg.locator(".cards-m .tb-card, .cards-m .sp-card").count() == 0      # no table drawn in a mat
        b.close()


# -- goal 171 stage J: the closed mats' slots and the three kinds of card (js/cards/slots.js, kind.js; decisions §299.5, §300.1, §300.4) ----------

FACTS = """() => [...document.querySelectorAll('.cards-m')].map((m) => {
  const s = m.querySelector('.cards-slots'), box = m.getBoundingClientRect();
  const shown = s ? [...s.querySelectorAll('i')].filter((i) => i.getClientRects().length > 0) : [];
  const words = [...m.querySelectorAll('.cards-m__body, .cards-mat')];
  return { mat: m.dataset.mat || '', layout: s?.dataset.layout || '', hidden: s?.getAttribute('aria-hidden'), fit: m.dataset.fit || '', n: shown.length,
    dashed: shown.length ? getComputedStyle(shown[0]).borderTopStyle : '', behind: words.every((w) => getComputedStyle(w).position === 'relative'),
    left: shown.length ? Math.min(...shown.map((i) => i.getBoundingClientRect().left)) - box.left : 0, w: box.width, shape: m.querySelectorAll('.cards-mat__shape').length }; })"""


def test_a_closed_mat_lays_its_layouts_slots_faint_behind_its_words_aria_hidden_and_a_word_has_none(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        facts = pg.evaluate(FACTS)
        mats = [f for f in facts if f["mat"]]
        words = [f for f in facts if not f["mat"]]
        assert mats and words
        assert {f["layout"] for f in mats} >= {"two", "layers"}, mats
        for f in mats:
            assert f["hidden"] == "true" and f["n"] >= 2 and f["dashed"] == "dashed" and f["behind"] and f["shape"] == 0, f
            if f["fit"] == "small":
                assert f["n"] == 3 and f["left"] >= f["w"] / 2 - 2, f               # three, at its right
        for f in words:
            assert f["layout"] == "" and f["n"] == 0, f                               # a word has none
        b.close()


def test_where_little_is_left_under_the_words_a_mat_lays_three_slots_at_its_right(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        m = pg.locator(".cards-m[data-mat='diff']").first
        m.evaluate("e => { e.querySelector('.cards-m__body').style.minHeight = (e.clientHeight * 0.6) + 'px'; e.style.width = (e.clientWidth - 1) + 'px'; }")
        pg.wait_for_function("document.querySelector(\".cards-m[data-mat='diff']\").dataset.fit === 'small'", timeout=5000)
        shown = m.evaluate("e => [...e.querySelectorAll('.cards-slots i')].filter((i) => i.getClientRects().length).map((i) => i.getBoundingClientRect().left - e.getBoundingClientRect().left)")
        assert len(shown) == 3 and min(shown) >= m.bounding_box()["width"] / 2 - 2, shown
        b.close()


def test_every_card_a_mat_draws_is_a_goal_a_decision_or_a_part_its_kind_in_its_top_right_corner_and_its_name(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        pg.locator(".tb-card").first.wait_for(timeout=5000)
        cards = pg.evaluate("() => [...document.querySelectorAll('.tb-card')].map((c) => [c.dataset.cardkind, c.getAttribute('aria-label'), !!c.querySelector('.tb-ix .ork-sign')])")
        assert cards and all(k == "part" and ", a part" in n and sign for k, n, sign in cards), cards
        pg.keyboard.press("Escape")
        pg.locator(".tb").wait_for(state="detached", timeout=5000)
        pg.evaluate(RED, THREE)
        pg.locator(".sp-gate").wait_for(timeout=5000)
        gate = pg.evaluate("() => [...document.querySelectorAll('.sp-card')].map((c) => [c.dataset.cardkind, c.getAttribute('aria-label'), !!c.querySelector('.cards-c--tr .ork-sign')])")
        assert gate and all(k in ("goal", "decision", "part") and n.endswith(", a " + k) and sign for k, n, sign in gate), gate
        assert {k for k, _, _ in gate} == {"goal", "decision"}, gate                 # the gate's checks are the decisions they guard
        b.close()


def test_a_framework_mat_lays_its_table_at_its_part_with_the_leaders_words_at_its_head(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        tb = pg.locator(".tb[data-framework='architecture']")
        tb.wait_for(timeout=5000)
        assert tb.get_attribute("data-at") == "gui/"
        assert "is-at" in tb.locator(".tb-card[data-card='gui/']").get_attribute("class")
        assert "gui/ is past its line" in tb.locator(".cards-said").inner_text()
        tb.locator(".tb-switch button", has_text="Feed").click()
        pg.locator(".cards-lanes").wait_for(timeout=5000)
        pg.locator(".tb-switch button", has_text="Architecture").first.click()       # laid by its switch: no words at its head
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=5000)
        assert pg.locator(".tb .cards-said").count() == 0 and pg.locator(".tb-card.is-at").count() == 0
        b.close()


def test_a_change_opens_what_changed_and_a_concern_is_an_l_of_words(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='diff']").first.click(position={"x": 30, "y": 20})
        pg.locator(".sp-veil[data-spread='diff']").wait_for(timeout=5000)
        assert pg.locator(".cards-l").count() == 0
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        assert pg.locator(".cards-m[data-mat='dispute']").count() == 0
        pg.locator("article.cards-m", has_text="Doubts Product").first.focus()
        pg.keyboard.press("Enter")
        pg.locator(".cards-l").wait_for(timeout=5000)
        assert pg.locator(".sp-veil").count() == 0
        b.close()


# -- goal 171 stage H: the frame every mat lies in (js/cards/matframe.js, matframe.css; decisions §300.15) ---------------------------------

THREE = "163-products-tree-on-the-board"
RED = """async (slug) => { const link = await import("/static/js/link.js"), sp = await import("/static/js/cards/spreads/open.js");
  const names = ["Critical tests", "Tests of what it touched"];
  link.town.value = { ...link.town.value, main_checks: { [slug]: names.map((name, i) => ({ name, state: i ? "failed" : "passed", words: i ? "2 tests fail" : "312 passed" })) } };
  sp.openSpread({ kind: "gate", slug, from: document.querySelector(".cards-m, .cards-s") }); }"""


def test_a_mat_lies_on_its_owners_felt_with_its_words_on_plates_and_the_table_under_it_inert_and_dimmed(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.evaluate(RED, THREE)
        mat = pg.locator(".sp.mf.ork-table[data-party='orkmaster']")
        mat.wait_for(timeout=5000)
        assert mat.locator(".mf-t.ork-plate").count() == 1 and mat.locator(".sp-say.ork-plate").count() == 1       # the head's words on plates
        assert mat.locator(".sp-note.ork-plate").count() == 1
        assert pg.locator(".mf-phase.is-on").count() == 1                                     # the phases lie along the foot of a mat about one goal
        assert pg.locator(".frame-table").evaluate("e => e.hasAttribute('inert')")
        assert not pg.locator(".frame-hand").evaluate("e => e.hasAttribute('inert')")                               # the hand stays live
        assert pg.evaluate("getComputedStyle(document.querySelector('.mf-veil')).backgroundColor") != "rgba(0, 0, 0, 0)"     # the scrim dims the table
        assert pg.evaluate("document.activeElement.classList.contains('sp-shut')")
        b.close()


def test_the_seal_is_dim_with_its_why_told_by_its_rim_never_by_opacity(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.evaluate(RED, THREE)
        seal = pg.locator(".mf-foot .mf-seal")
        seal.wait_for(timeout=5000)
        assert seal.get_attribute("aria-disabled") == "true" and "sealed" in seal.inner_text()
        look = seal.evaluate("e => [e, ...e.querySelectorAll('*')].map((x) => getComputedStyle(x).opacity).join()")
        assert set(look.split(",")) == {"1"}, look                                                                  # told by its rim, not faded
        assert seal.evaluate("e => getComputedStyle(e).outlineStyle") == "dashed"
        box = seal.bounding_box()
        acts = pg.locator(".mf-foot").bounding_box()
        assert box["x"] + box["width"] >= acts["x"] + acts["width"] - 12                                            # at the foot's right
        b.close()


def test_tab_goes_through_the_mat_only_and_esc_gives_the_focus_back_to_the_card_that_opened_it(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m").first.focus()
        pg.evaluate(RED, THREE)
        pg.locator(".sp-veil[data-spread='gate']").wait_for(timeout=5000)
        seen = []
        for _ in range(8):
            pg.keyboard.press("Tab")
            seen.append(pg.evaluate("() => !!document.activeElement.closest('.sp-veil, .mathand')"))
        assert all(seen), seen
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        assert pg.evaluate("() => !document.querySelector('[inert]')")
        assert pg.evaluate("() => document.activeElement.matches('.cards-m, .cards-s')")
        b.close()


def test_a_leaders_table_lies_on_its_leaders_felt_and_on_a_phone_a_mat_is_the_whole_screen_with_back(page_url):
    with sync_playwright() as p:
        b, pg = opened(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        tb = pg.locator(".tb.sp.mf.ork-table[data-framework='architecture']")
        tb.wait_for(timeout=5000)
        assert tb.get_attribute("data-party") == "ork" and tb.get_attribute("data-race") == "ork" and tb.locator(".mf-t.ork-plate").inner_text().startswith("Tech's table")
        pg.keyboard.press("Escape")
        pg.locator(".tb").wait_for(state="detached", timeout=5000)
        assert pg.evaluate("() => document.activeElement.matches('.cards-m')")
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.evaluate(RED, THREE)
        mat = pg.locator(".sp.mf")
        mat.wait_for(timeout=5000)
        box = mat.bounding_box()
        assert box["x"] <= 1 and box["y"] <= 1 and box["width"] >= 388 and box["height"] >= 842, box
        assert pg.locator(".sp-shut").inner_text().strip() == "Back"
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        b.close()


# -- goal 171 stage I: a mat's address, and on the phone the whole screen (js/cards/address.js; decisions §299.3, §300.3) -------------------------

def at_phone(p, page_url, hash_=""):
    b = launch(p)
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.goto(page_url + "?mock=1" + hash_)
    return b, pg


def test_a_mat_opened_has_its_address_and_a_reload_opens_it_again_on_the_phone(page_url):
    with sync_playwright() as p:
        b, pg = at_phone(p, page_url)
        pg.locator(".cards-m[data-mat='table']").first.wait_for(timeout=15000)
        pg.locator(".cards-m[data-mat='table']").first.click(position={"x": 30, "y": 20})
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=5000)
        assert pg.evaluate("location.hash").startswith("#mat=table:") and ":architecture" in pg.evaluate("location.hash")
        box = pg.locator(".mf-veil > .sp.mf").bounding_box()
        assert box["x"] <= 1 and box["width"] >= 388 and box["y"] <= 1 and box["height"] >= 840             # the whole screen
        assert pg.locator(".sp-shut").inner_text().strip() == "Back"
        narrow.no_sideways(pg)
        pg.reload()                                                                                         # the address opens it again
        pg.locator(".tb[data-framework='architecture']").wait_for(timeout=15000)
        assert pg.locator(".sp-shut").inner_text().strip() == "Back"
        pg.go_back()                                                                                        # the phone's Back puts it away
        pg.locator(".tb").wait_for(state="detached", timeout=5000)
        assert pg.evaluate("location.hash") == ""
        b.close()


def test_a_spread_has_its_address_esc_takes_it_off_and_the_card_opened_shows_one_line_not_a_row_of_mats(page_url):
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(page_url + "?mock=1")
        card = pg.locator(".cards-dealer .cards-row .cards-s[data-goal]").first
        card.wait_for(timeout=15000)
        slug = card.get_attribute("data-goal")
        card.click()
        assert pg.locator(".cards-l__acts button[data-lies]").count() == 1 and pg.locator(".cards-l__acts button", has_text="At the gate").count() <= 1       # one line, no row of mats
        assert pg.locator(".cards-l__lies").inner_text().startswith("Lies now at")
        pg.locator(".cards-l__lies button").click()
        pg.locator("[data-spread=track], [data-spread=gate]").wait_for(timeout=5000)
        assert pg.evaluate("location.hash").startswith("#mat=") and pg.evaluate("location.hash").endswith(":" + slug)
        pg.reload()
        pg.locator("[data-spread=track], [data-spread=gate]").wait_for(timeout=15000)
        pg.keyboard.press("Escape")
        pg.locator(".sp-veil").wait_for(state="detached", timeout=5000)
        pg.wait_for_function("location.hash === ''")
        b.close()


def test_an_address_of_a_goal_the_board_does_not_have_opens_nothing(page_url):
    with sync_playwright() as p:
        b, pg = at_phone(p, page_url, "#mat=gate:no-such-goal")
        pg.locator(".cards-m").first.wait_for(timeout=15000)
        pg.wait_for_function("location.hash === ''")
        assert pg.locator(".sp-veil").count() == 0
        b.close()


@pytest.fixture(scope="module")
def turned_url():
    s = serve_mock.serve(0, mock_kit.lay_turned)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}/?mock=1"
    s.shutdown()


def test_the_track_mat_lays_its_stages_as_zones_with_their_labels_on_their_frame_and_its_phases_on_a_plate(turned_url):
    """Goal 171 stage N2: the done, now and to come are `Zone`s of matframe.js, each label (`.mf-zl`) on its frame; the phases' row lies on a plate."""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(turned_url)
        pg.wait_for_selector(".cards-m", timeout=15000)
        pg.wait_for_timeout(800)
        pg.locator(".frame-hand button.hand-card[data-kind=turn][data-goal='174-example-3']").click()
        pg.wait_for_selector("[data-spread=track] .mf")
        labels = pg.locator("[data-spread=track] .mf-zone > .mf-zl")
        assert labels.count() >= 1 and all(labels.nth(i).is_visible() for i in range(labels.count()))
        assert labels.first.evaluate("(e) => { const r = e.getBoundingClientRect(), z = e.parentElement.getBoundingClientRect(); return r.top < z.top + 12 && r.bottom > z.top - 12; }")     # on the zone's frame
        assert pg.locator("[data-spread=track] .mf-zone .sp-card").count() >= 1
        phases = pg.locator("[data-spread=track] .mf-phases")
        assert phases.is_visible() and phases.locator(".mf-phase").count() == 5
        assert phases.evaluate("(e) => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)"
        b.close()
