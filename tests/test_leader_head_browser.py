"""Spec 168 E1 (decisions §283.16.2, §283.20, §283.21): a leader's tab with no goal picked shows its project under a header **held while the table scrolls**, in three groups of small cards, every card 56 x 78, in a real browser at
1366 x 768 against the concerns' stub host (`ConcernHost`, with Tech's goals in Talk, in its spec and at work): **at work** (its idea and its spec face down with the goal's rune, its implementation face up; pressed, the goal is picked and this leader's
table of its stage opens), **concerns** (face down with a + for a concern on no goal; pressed, lifted and played with *Not a problem*, *Later*, *Make it a goal*), **ask** (the ? card; pressed, the quick question to this leader opens; with it open a press on a part
of the scheme names the part in the question). No element of 28 x 39 is left. The leader's seats and tools are not in the header: they lie in its inventory (the … menu's *Seats and tools*), the party's menu is the pane title's. The narrow page keeps its header.
Pictures at 1366 x 768 to $ORKCRAFT_SHOTS_DIR when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_concern_card_browser import CARD, LIT, CardHost  # noqa: E402
from tests.test_concerns_desktop_browser import LOBBY, go, ready, start, system  # noqa: E402
from tests.test_table_desktop_browser import node as board_node, shot  # noqa: E402

pytestmark = pytest.mark.browser

HEAD = '.table-head.hd[data-party="tech"]'


class HeadHost(CardHost):
    """Concerns' host with Tech's goals in flight: an idea in Talk, a spec being written, an implementation at work."""

    def __init__(self):
        super().__init__()
        self.nodes += [board_node("talk-goal", "tech", "Add a dark mode option", "talk", "talk", "ice", "", place="table"),
                       board_node("spec-goal", "tech", "Keep the seat when a player drops", "sections", "planning", "dust", "", place="table"),
                       board_node("work-goal", "tech", "Tidy the lobby code", "working", "doing", "meadow", "restructure", place="table")]


@pytest.fixture
def page(gui):
    pg, host, errors = start(gui, "wide", HeadHost(), **LIT)
    system(pg)
    pg.locator(HEAD).wait_for(timeout=WAIT_MS)
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def size(loc):
    return tuple(loc.evaluate("e => [e.offsetWidth, e.offsetHeight]"))


def test_the_header_holds_three_groups_of_small_cards_all_56_by_78_and_nothing_of_28_by_39(page):
    pg, host = page
    shot(pg, "e1-leader-project.png")
    groups = pg.locator(f"{HEAD} .hd-group")
    assert [groups.nth(i).get_attribute("data-group") for i in range(groups.count())] == ["work", "concerns", "ask"]
    assert [groups.nth(i).locator(".ork-label").inner_text().lower() for i in range(groups.count())] == ["at work", "concerns", "ask"]
    work = pg.locator(f'{HEAD} [data-group="work"] [data-goal]')
    mine = [(work.nth(i).get_attribute("data-goal"), work.nth(i).get_attribute("data-stage")) for i in range(work.count())]
    assert [m for m in mine if m[0] in ("talk-goal", "spec-goal", "work-goal")] == [("talk-goal", "idea"), ("spec-goal", "spec"), ("work-goal", "work")] and {m[1] for m in mine} == {"idea", "spec", "work"}
    assert pg.locator(f'{HEAD} [data-goal="talk-goal"] .ork-card-back, {HEAD} [data-goal="spec-goal"] .ork-card-back').count() == 2, "ideas and specs face down"
    assert pg.locator(f'{HEAD} [data-goal="work-goal"].ork-card.sm').count() == 1, "the implementation face up"
    cards = pg.locator(f"{HEAD} .hd-group__cards .ork-card")
    assert cards.count() >= 5
    assert {size(cards.nth(i)) for i in range(cards.count())} == {(56, 78)}, "every card 56 x 78"
    assert pg.evaluate("() => [...document.querySelectorAll('.table-head *')].filter((e) => e.offsetWidth === 28 && e.offsetHeight === 39).length") == 0
    assert pg.locator(".cn-card").count() == 0
    asks = pg.locator(f'{HEAD} [data-group="concerns"] .hd-concern')
    assert [asks.nth(i).get_attribute("data-concern-id") for i in range(asks.count())] == ["tech/c1", "tech/c2", "tech/c3"]
    assert {asks.nth(i).get_attribute("data-face") for i in range(asks.count())} == {"down"} and asks.first.locator(".ork-icon").count() == 1, "a + for a concern on no goal"


def test_a_press_on_at_work_picks_the_goal_and_opens_this_leaders_table_of_its_stage(page):
    pg, host = page
    pg.locator(f'{HEAD} [data-goal="talk-goal"]').click()
    pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-phases [aria-current=step]").get_attribute("data-phase") == "talk"
    assert pg.locator('.table-tab[data-tab="tech"][aria-selected="true"], .col-head__tab[data-tab="tech"][aria-selected="true"]').count() == 1, "at this leader's tab"
    assert pg.locator(HEAD).count() == 0, "the table of its stage lies in the pane's place"


def test_a_press_on_a_concern_lifts_it_and_plays_it_with_its_three_ways(page):
    pg, host = page
    pg.locator(f'{HEAD} .hd-concern[data-concern-id="tech/c1"]').click()
    pg.locator('.hand-lifted[data-kind="concern"]').wait_for(timeout=WAIT_MS)
    ways = pg.locator(".hand-ways-cards button[data-way-kind]")
    assert [ways.nth(i).get_attribute("data-way-kind") for i in range(ways.count())] == ["not_a_problem", "later", "make_it_a_goal"]
    pg.locator('.hand-ways-cards button[data-way-kind="later"]').click()
    pg.locator('.hd-concern[data-concern-id="tech/c1"][data-later]').wait_for(timeout=WAIT_MS)
    assert pg.locator('.hd-concern[data-concern-id="tech/c1"]').get_attribute("data-face") == "down", "laid Later it lies face down here too"
    assert host.sent("ideas.concern_later") == [{"party": "tech", "id": "c1"}]


def test_the_ask_card_opens_the_quick_question_to_this_leader_and_a_part_pressed_is_named_in_it(page):
    pg, host = page
    ask = pg.locator(f"{HEAD} [data-ask-card]")
    assert size(ask) == (56, 78) and ask.get_attribute("aria-pressed") == "false"
    ask.click()
    pg.locator(".table-ask__bubble").wait_for(timeout=WAIT_MS)
    assert ask.get_attribute("aria-pressed") == "true"
    pg.locator(f'.sys-part[data-part="{LOBBY}"]').click()
    pg.locator(".table-ask__bubble .pick-chip, .table-ask__bubble [data-part-chip], .table-ask__bubble").first.wait_for(timeout=WAIT_MS)
    assert pg.evaluate("() => import('/static/js/table/ask.js').then((m) => m.askPart.value && m.askPart.value.id)") == LOBBY, "the part is named in the question"
    assert pg.locator(".table-back").count() == 0, "a press on a part took it in: it was not lifted"
    ask.dispatch_event("click")                                                                    # the bubble may lie over the card: pressed as a key would
    pg.wait_for_selector(".table-ask__bubble", state="detached", timeout=WAIT_MS)


def test_the_header_is_held_while_the_table_scrolls(page):
    pg, host = page
    before = pg.locator(HEAD).bounding_box()
    pg.evaluate("""() => { const body = document.querySelector('.table-body'), pad = document.createElement('div'); pad.id = 'pad'; pad.style.cssText = 'height:2400px;flex:none'; body.append(pad);
      body.style.overflow = 'auto'; body.scrollTop = 260; }""")
    pg.wait_for_timeout(100)
    now = pg.locator(HEAD).bounding_box()
    assert pg.evaluate("() => document.querySelector('.table-body').scrollTop") > 100 and abs(now["y"] - before["y"]) < 2, "held in its place"
    assert getattr(pg, "viewport_size")["height"] == 768
    shot(pg, "e1-leader-project-scrolled.png")


def test_its_seats_and_tools_are_in_the_inventory_and_the_menu_and_not_in_the_header(page):
    pg, host = page
    assert pg.locator(f"{HEAD} .table-seat, {HEAD} .table-group, {HEAD} .table-size").count() == 0
    pg.get_by_role("button", name="Tech's menu").click()
    assert [i.inner_text().strip() for i in pg.get_by_role("menuitem").all()][:2] == ["Edit", "Seats and tools"]
    pg.get_by_role("menuitem", name="Seats and tools").click()
    seats = pg.locator('.stall-seats[data-seats="tech"]')
    seats.wait_for(timeout=WAIT_MS)
    assert seats.locator(".table-seat").count() == 3 and seats.locator(".table-group").count() == 2 and seats.locator(".table-size").inner_text().strip() == "Standard"
    assert seats.locator(".table-side .ork-mark").count() >= 1, "its AI tool's mark"
    seats.locator('.table-seat[data-seat="grunt"]').click()
    pg.locator(".table-seatpop").wait_for(timeout=WAIT_MS)
    shot(pg, "e1-leader-seats-in-the-inventory.png")


def test_the_narrow_page_keeps_its_header(gui):
    pg, host, errors = start(gui, "narrow", HeadHost())
    go(pg, "tech")
    pg.locator(".table-head .table-seat").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-head.hd").count() == 0 and pg.locator(".table-head .table-menu__btn").count() == 1
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)
