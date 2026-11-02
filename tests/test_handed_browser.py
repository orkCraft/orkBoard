"""The cards handed from where they were played (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.9–§6.10, decisions §198.9), in a real browser against a stub host: the origin found in its order (the goal's own card on the table, the leader's tab, on a phone
the goal in the middle or the crown, none); orkUI's `--ork-deal-x/-y` set from it; *From <Leader>* on the card and said once, politely; three flights at most, a deal gap apart; none while a pointer is down in the hand (they come when it is up), none for what came while
the page was hidden, none under reduced motion; an answered card played back to its origin (orkUI's `.ork-play`) and a dropped one crumbling where it lay. Screenshots to $HANDED_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_card_life_browser import LifeHost, back, back_of, open_life  # noqa: E402
from tests.test_hand_desktop_browser import need, node, open_hand  # noqa: E402
from tests.test_talk_desktop_browser import C1, C2, C3, STANCES  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["HANDED_SHOTS"]) if os.environ.get("HANDED_SHOTS") else None


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def asks_goal(host, slug, title, party="design", element="dust"):
    """A goal at the Orkmaster's lane with a question of its party waiting in the hand (its own stack)."""
    host.nodes = [n for n in host.nodes if n["slug"] != slug]
    asked = [{"ask": f"Which way for {title}?", "choices": ["This", "That"], "pick": None, "why": "", "by": None, "look": False}]
    host.nodes.append(node(slug, party, title, "hand", state="asks", element=element, asked=asked))
    host.needs.append(need("asks", party, slug, title, asked[0]["ask"], at="2026-10-20T09:30:00", asked=asked))


def talk_questions(host, slug="dark", cards=(C1, C2, C3)):
    host.needs = [n for n in host.needs if n["idea"] != slug]
    host.needs.append(need("talk", "design", slug, "Players see who answered first", cards[0]["q"], round=1, stances=STANCES, questions=list(cards)))


FROM_JS = """([who]) => import('/static/js/hand/motion.js').then((m) => { const w = m.fromWhere(who); return w ? { at: w.at, tag: w.el.className, goal: w.el.dataset.goal || '', tab: w.el.dataset.tab || '' } : null; })"""
DEAL_X = "() => [...document.querySelectorAll('.hand-card')].filter((e) => e.style.getPropertyValue('--ork-deal-x')).map((e) => [e.dataset.key, e.style.getPropertyValue('--ork-deal-x'), e.style.getPropertyValue('--ork-deal-y'), e.style.getPropertyValue('--ork-deal-i')])"

GAVE = "() => { window.__gave = []; document.addEventListener('animationstart', (e) => { if (e.animationName === 'ork-give') window.__gave.push(e.target.closest('.table-back-head, .table-tab, .col-head__tab, .up-crown')?.className || '?'); }, true); }"


def talking(host):
    host.put("dark", "Players see who answered first", "talk", "dust", back=back(route=("design", "tech")))


def test_the_origin_is_the_goals_own_card_then_the_leaders_tab_then_none(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        got = pg.evaluate(FROM_JS, [{"goal": "dark", "party": "design"}])
        assert got["at"] == "goal" and got["goal"] == "dark" and "col-card--down" in got["tag"], "the goal's own card: its back in the Orkmaster's column (spec 128 B.3)"
        got = pg.evaluate(FROM_JS, [{"goal": "gone", "party": "design"}])
        assert got["at"] == "tab" and got["tab"] == "design" and "table-tab" in got["tag"], "else the leader's tab"
        got = pg.evaluate(FROM_JS, [{"party": "tech"}])
        assert got["at"] == "tab" and got["tab"] == "tech"
        got = pg.evaluate(FROM_JS, [{"ork": True}])
        assert got["at"] == "tab" and got["tab"] == "orkmaster", "the Orkmaster's tab for what the Orkmaster plays"
        assert pg.evaluate(FROM_JS, [{}]) is None and pg.evaluate(FROM_JS, [{"goal": "gone"}]) is None, "a card of no goal and no party is dealt from under its place"
        pg.locator('.table-tab[data-tab="design"]').evaluate("e => { e.style.display = 'none'; }")
        assert pg.evaluate(FROM_JS, [{"goal": "gone", "party": "design"}]) is None, "an origin out of view is none"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_the_origin_is_the_goal_in_the_middle_when_it_is_the_cards_goal_else_the_crown(gui):
    pg, host, log = open_life(gui, width="phone")
    try:
        pg.locator(".up-crown").wait_for(timeout=WAIT_MS)
        assert pg.evaluate(FROM_JS, [{"goal": "nothing", "party": "design"}])["at"] == "crown", "no lanes on a phone: the crown, where the menu of the leaders lives"
        host.put("dark", "Players see who answered first", "talk", "dust", back=back(route=("design", "tech")))
        talk_questions(host)
        host.bump({})
        pg.locator(".up-look[data-goal='dark']").wait_for(timeout=WAIT_MS)
        got = pg.evaluate(FROM_JS, [{"goal": "dark", "party": "design"}])
        assert got["at"] == "goal" and got["goal"] == "dark", "the goal picked in the middle, when it is the card's goal"
        assert pg.evaluate(FROM_JS, [{"goal": "other", "party": "design"}])["at"] == "crown"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_that_comes_flies_from_the_goals_card_says_from_its_leader_and_is_said_once_politely(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        pg.evaluate(GAVE)
        talk_questions(host)
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card[data-kind=\"talk\"]')", timeout=WAIT_MS)
        pg.wait_for_function("() => window.__gave.length > 0", timeout=WAIT_MS)
        assert ["table-tab" in c.split() for c in pg.evaluate("() => window.__gave")] == [True], "the head of who plays it, on its leader's tab (the face-down card of the column has no heads under it), gives it: one beat of orkUI's `.ork-gives`"
        pg.wait_for_function("() => !document.querySelector('.ork-gives')", timeout=WAIT_MS)
        assert pg.evaluate("() => window.__gave.length") == 1, "once, and the class is taken off at the animationend"
        pg.wait_for_function(DEAL_X, timeout=WAIT_MS)
        got = pg.evaluate(DEAL_X)
        assert len(got) == 1, "a goal's questions are one stack: its top card flies"
        key, x, y, i = got[0]
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        origin = back_of(pg, "dark").bounding_box()
        card = pg.locator('.hand-card[data-kind="talk"]').first.bounding_box()
        want = (origin["x"] + origin["width"] / 2 - (card["x"] + card["width"] / 2), origin["y"] + origin["height"] / 2 - (card["y"] + card["height"] / 2))
        assert abs(float(x.removesuffix("px")) - want[0]) <= 3 and abs(float(y.removesuffix("px")) - want[1]) <= 3, f"--ork-deal-x/-y are the origin less the place: {(x, y)} vs {want}"
        label = pg.locator('.hand-card[data-kind="talk"] .hand-card__party').first
        assert label.text_content() == "From Design lead" and pg.locator('.hand-card[data-kind="talk"]').first.get_attribute("data-from") == "Design lead", "its label row says who handed it, and keeps saying it"
        pg.wait_for_function("() => document.querySelector('.hand-live').innerText.includes('hands you')", timeout=WAIT_MS)
        said = pg.locator(".hand-live")
        assert said.get_attribute("aria-live") == "polite" and said.inner_text() == "Design lead hands you a question: Where does the timer run?"
        shot(pg, "handed")
        pg.wait_for_timeout(700)
        assert pg.locator('.hand-card[data-kind="talk"] .hand-card__party').first.text_content() == "From Design lead", "it keeps saying it"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_of_the_orkmaster_says_from_the_orkmaster_and_a_card_of_no_goal_is_dealt_from_under_its_place(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        host.needs.append(need("decision", "design", "dark", "Players see who answered first", "Why: One clock.\n\n1. Tech counts.", number=201, confirmed=False, error=""))
        host.put("dark", "Players see who answered first", "decided", "dust")
        pg.wait_for_function("() => document.querySelector('.hand-card[data-kind=\"decision\"] .hand-card__party')", timeout=WAIT_MS)
        assert pg.locator('.hand-card[data-kind="decision"] .hand-card__party').text_content() == "From the Orkmaster"
        host.needs.append({"kind": "paid", "title": "Go on paid?", "text": "Every tool is out of room", "idea": "", "goal": "", "at": "2026-10-20T10:00:00", "priority": "normal", "blocks": True})
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card[data-kind=\"paid\"]')", timeout=WAIT_MS)
        paid = pg.evaluate("() => { const e = document.querySelector('.hand-card[data-kind=\"paid\"]'); return [e.classList.contains('ork-deal'), e.style.getPropertyValue('--ork-deal-x')]; }")
        assert paid in ([True, ""], [False, ""]), f"dealt from under its place, as it was: no origin set ({paid})"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_three_flights_at_most_a_deal_gap_apart_in_order_the_others_dealt_from_under_their_place(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        for k in range(5):
            asks_goal(host, f"g{k}", f"Goal number {k}")
        host.bump({})
        pg.wait_for_function("() => document.querySelectorAll('.hand-card.ork-deal').length >= 5", timeout=WAIT_MS)
        flying = pg.evaluate(DEAL_X)
        assert len(flying) == 3, f"three fly: {flying}"
        every = pg.evaluate("() => [...document.querySelectorAll('.hand-card.ork-deal, .hand-card[style*=ork-deal-i]')].map((e) => [e.dataset.goal, e.style.getPropertyValue('--ork-deal-i'), !!e.style.getPropertyValue('--ork-deal-x')])")
        assert sorted(i for _g, i, _x in every) == ["0", "1", "2", "3", "4"], "a deal gap apart, one after another"
        assert sorted(g for g, _i, x in every if not x) and len([1 for _g, _i, x in every if not x]) == 2, "the other two are dealt from under their place"
        assert [i for _g, i, x in sorted(every, key=lambda t: int(t[1])) if x] == ["0", "1", "2"], "the first three, in their order"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_none_while_a_pointer_is_down_in_the_hand_they_come_when_it_is_up(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        pg.mouse.move(640, 790)
        pg.mouse.down()
        asks_goal(host, "g0", "Goal number 0")
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card[data-goal=\"g0\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(400)
        held = pg.evaluate("() => { const e = document.querySelector('.hand-card[data-goal=\"g0\"]'); return [e.hasAttribute('data-handing'), e.classList.contains('ork-deal'), getComputedStyle(e).visibility]; }")
        assert held == [True, False, "hidden"], f"held back while the pointer is down: {held}"
        pg.mouse.up()
        pg.wait_for_function("() => document.querySelector('.hand-card[data-goal=\"g0\"]') && !document.querySelector('.hand-card[data-goal=\"g0\"]').hasAttribute('data-handing')", timeout=WAIT_MS)
        assert pg.evaluate(DEAL_X), "it flies when the pointer is up"
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.hand-card[data-goal=\"g0\"]')).visibility") == "visible"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_none_for_what_came_while_the_page_was_hidden_the_cards_are_there_each_saying_from_its_leader_and_none_under_reduced_motion(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        pg.evaluate("() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); }")
        talk_questions(host)
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card[data-kind=\"talk\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        hidden = pg.evaluate("() => { const e = document.querySelector('.hand-card[data-kind=\"talk\"]'); return [e.classList.contains('ork-deal'), e.style.getPropertyValue('--ork-deal-x'), e.querySelector('.hand-card__party').textContent]; }")
        assert hidden == [False, "", "From Design lead"], f"there, saying whose it is, with no flight: {hidden}"
        pg.evaluate("() => { delete document.hidden; }")
        pg.emulate_media(reduced_motion="reduce")
        pg.evaluate(GAVE)
        asks_goal(host, "g0", "Goal number 0")
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card[data-goal=\"g0\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert pg.evaluate("() => { const e = document.querySelector('.hand-card[data-goal=\"g0\"]'); return [e.classList.contains('ork-deal'), e.style.getPropertyValue('--ork-deal-x'), e.querySelector('.hand-card__party').textContent]; }") == [False, "", "From Design lead"]
        assert pg.evaluate("() => [window.__gave.length, document.querySelectorAll('.ork-gives').length]") == [0, 0], "no give under reduced motion"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_head_that_gives_is_the_leaders_under_the_card_else_the_tab_head_else_the_crown(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        back_of(pg, "dark").wait_for(timeout=WAIT_MS)
        head = "([who]) => import('/static/js/hand/motion.js').then((m) => { const h = m.headAt(m.fromWhere(who), who); return h ? h.closest('.table-back-head, .table-tab, .col-head__tab, .table-tabcell, .up-crown')?.className + ' ' + (h.closest('[data-party],[data-tab]')?.dataset.party || h.closest('[data-party],[data-tab]')?.dataset.tab) : null; })"
        assert "table-tab" in pg.evaluate(head, [{"goal": "dark", "party": "design"}]), "the leader's tab head: the column's face-down card has no heads under it"
        assert pg.evaluate(head, [{"goal": "gone", "party": "tech"}]).endswith("tech") and "table-tab" in pg.evaluate(head, [{"goal": "gone", "party": "tech"}]), "the leader's tab head"
        assert "col-head__tab" in pg.evaluate(head, [{"ork": True}]), "the Orkmaster's: its tab, the column's head"
        assert pg.evaluate(head, [{}]) is None
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_answered_card_is_played_back_to_its_origin_and_a_dropped_one_crumbles_where_it_lay(gui):
    pg, host, log = open_life(gui)
    try:
        talking(host)
        talk_questions(host)
        host.bump({})
        pg.locator('.hand-card[data-kind="talk"]').first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(1200)
        host.needs = [n for n in host.needs if n["kind"] != "talk"]                                    # answered: the goal stays, its card goes
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card.is-gone.ork-play')", timeout=WAIT_MS)
        got = pg.evaluate("() => { const e = document.querySelector('.hand-card.is-gone'); e.getAnimations().forEach((a) => a.cancel()); const r = e.getBoundingClientRect(); const o = document.querySelector('.col-card[data-goal=\"dark\"]').getBoundingClientRect();"
                          " return { x: e.style.getPropertyValue('--ork-play-x'), y: e.style.getPropertyValue('--ork-play-y'), shards: e.querySelectorAll('.ork-crumble').length, dx: o.left + o.width / 2 - (r.left + r.width / 2), dy: o.top + o.height / 2 - (r.top + r.height / 2) }; }")
        assert got["shards"] == 0, "flying back means answered, not gone"
        assert abs(float(got["x"].removesuffix("px")) - got["dx"]) <= 4 and abs(float(got["y"].removesuffix("px")) - got["dy"]) <= 4, f"toward its origin: {got}"
        pg.wait_for_function("() => !document.querySelector('.hand-card.is-gone')", timeout=WAIT_MS)
        asks_goal(host, "g0", "Goal number 0")
        host.bump({})
        pg.locator('.hand-card[data-goal="g0"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(1200)
        host.nodes = [n for n in host.nodes if n["slug"] != "g0"]                                      # dropped: the goal is gone with its card
        host.needs = [n for n in host.needs if n["idea"] != "g0"]
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-card.is-gone .ork-crumble')", timeout=WAIT_MS)
        assert pg.evaluate("() => document.querySelector('.hand-card.is-gone').classList.contains('ork-play')") is False, "crumbling where it lay"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_a_card_handed_flies_from_the_crown_as_a_copy_over_the_row_and_says_from_its_leader(gui):
    pg, host, log = open_life(gui, width="phone")
    try:
        pg.locator(".up-crown").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        pg.evaluate(GAVE)
        asks_goal(host, "g0", "Goal number 0")
        host.bump({})
        card = pg.locator(".up-card")
        card.first.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => window.__gave.length > 0", timeout=WAIT_MS)
        assert pg.evaluate("() => window.__gave") == ["up-crown"], "the crown's head gives it"
        pg.wait_for_function("() => document.querySelector('body > .hand-ghost--handed') || document.querySelector('.up-card[data-from]')", timeout=WAIT_MS)
        assert card.first.get_attribute("data-from") == "Design lead" and card.first.get_attribute("aria-label").endswith(", from Design lead")
        pg.wait_for_function("() => document.querySelector('.hand-live').textContent.includes('Design lead hands you')", timeout=WAIT_MS)
        assert pg.locator(".hand-live").get_attribute("aria-live") == "polite"
        pg.wait_for_function("() => !document.querySelector('body > .hand-ghost--handed')", timeout=WAIT_MS)
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.up-card')).visibility") == "visible", "the real card is there when the copy has landed"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)
