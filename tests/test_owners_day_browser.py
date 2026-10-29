"""Spec 107 parts D, E and G (docs/specs/107-what-the-owners-day-said.md §4, §5, §7; decisions §182.3, §182.4, §182.7), in a real browser against stub hosts, at the two widths of `tests/narrow.py`:

D, a goal dropped from its card: **…** on the Orkmaster's lane's card (its back at the narrow width), on the line's cards, on the route card lifted and on a goal's face over the pane, its one item *Drop this goal…*,
the question asked in place (*Drop this goal?*, *Keep it* · *Drop it*, *Its work stops first.* while tasks run), `ideas.stop` then `ideas.drop`, the host's refusal said in the card, a 44 px target under touch;
E, a goal sent lies in the Orkmaster's lane at once and its route card stays in the hand;
G, what works moves: a task card at work steps its drawing and marches a dotted line, says the time it has worked and ticks it, a card whose state changed flashes its frame once, all of it off under reduced motion
(the time still ticks)."""
from __future__ import annotations

import datetime as dt
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand, pane  # noqa: E402
from tests.test_route_card_desktop_browser import RouteHost, lift, open_route  # noqa: E402
from tests.test_shell_browser import _calls, _sent  # noqa: E402
from tests.test_table_desktop_browser import TableHost, node, start, task  # noqa: E402

pytestmark = pytest.mark.browser

REFUSED = "The keeper is busy with this goal: a moment"
SAID = "The Orkmaster is reading it: drop it when it is done"


class Dropping:
    """What a host does with `ideas.drop` and `ideas.stop`: the goal goes (its node and rows), or the host refuses (`refuse`); `on_socket` answers a refusal as the page's socket does (`ok: false`)."""
    refuse = ""

    def handle(self, name, a):
        if name == "ideas.drop":
            self.log.append((name, a))
            if self.refuse:
                raise ValueError(self.refuse)
            self.nodes = [n for n in self.nodes if n["slug"] != a["slug"]]
            self.needs = [n for n in self.needs if n.get("idea") != a["slug"]]
            self.rev += 1
            return {"ok": True}
        if name == "ideas.stop":
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            try:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
            except ValueError as e:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": str(e)}))
        ws.on_message(on_message)


def ago(seconds):
    return (dt.datetime.now() - dt.timedelta(seconds=seconds)).isoformat(timespec="seconds")


class DayHost(Dropping, TableHost):
    """The table's stub with a goal just sent (routed, on the table, asking), a task at work for 72 seconds, and the commands of a drop."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.nodes.append(node("fresh", "tech", "A goal just sent", "routed", element="ice", sign="feature", asks_you=True))
        for n in self.nodes:
            for t in n["tasks"]:
                if t["state"] in ("running", "testing"):
                    t["started"] = ago(72)

    def push(self):
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))


class DayRoute(Dropping, RouteHost):
    """The route card's stub (the goal just sent lies on the table, asking; its route row is in the hand) with the commands of a drop."""


@pytest.fixture(params=narrow.WIDTHS)
def day(gui, request):
    errors: list[str] = []
    server, browser = gui
    host = DayHost()
    pg = narrow.page(browser, request.param)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def first(pg):
    return pg.locator('.table-lane[data-lane="first"]')


def ask_drop(box):
    """Press the **…** in `box` and its one item; the question it asks in place."""
    box.locator(".table-dropper .table-menu__btn").first.click()
    items = box.get_by_role("menuitem")
    assert [i.inner_text().strip() for i in items.all()] == ["Drop this goal…"] and items.first.locator(".ork-icon").count() == 1
    items.first.click()
    ask = box.get_by_role("alertdialog")
    ask.wait_for(timeout=WAIT_MS)
    return ask


# -- E: a goal sent lies on the table ------------------------------------------------------------------------------------------------------------

def test_a_goal_sent_lies_in_the_orkmasters_lane_at_once_and_in_no_partys(day):
    pg, host, w = day
    keys = [e.get_attribute("data-lkey") for e in first(pg).locator("[data-lkey]").all()]
    assert "t:orc:fresh" in keys, keys
    assert pg.locator('.table-lane[data-party] [data-goal="fresh"]').count() == 0, "not drawn in a party's lane too"
    if wide(w):
        card = first(pg).locator('.table-goal[data-goal="fresh"] .table-card--own')
        assert card.get_attribute("data-stage") == "routed" and card.locator(".table-stage").inner_text().strip().lower() == "routed"
    pg.locator('[data-lkey="t:orc:fresh"]').click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    assert "waits for your Talk" in back.inner_text()


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_goal_sent_stays_a_route_card_in_the_hand_while_it_lies_in_the_orkmasters_lane(gui, width):
    host = DayRoute()
    pg, log = open_route(gui, host, width)
    try:
        pg.locator('[data-lkey="t:orc:fresh"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.table-lane[data-lane="first"] [data-lkey="t:orc:fresh"]').count() == 1
        assert pg.locator('.hand-lane[data-lane="0"] .hand-card[data-kind="route"][data-goal="fresh"]').count() == 1, "its route card is in the hand too"
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- D: drop a goal from its card ----------------------------------------------------------------------------------------------------------------

def test_drop_this_goal_asks_in_place_keep_it_changes_nothing_and_drop_it_sends_ideas_drop(day):
    pg, host, w = day
    if not wide(w):                                                                                                       # a lane a token wide: the card's back holds the **…**
        pg.locator('[data-lkey="t:orc:fresh"]').click()
        box = pg.locator(".table-back")
        box.wait_for(timeout=WAIT_MS)
    else:
        box = first(pg).locator('.table-goal[data-goal="fresh"]')
    ask = ask_drop(box)
    text = ask.locator(".table-drop__text").text_content()
    assert ask.locator(".table-drop__title").text_content() == "Drop this goal?" and text == "Its page and its plan go; what it spent stays counted."
    assert ask.get_by_role("button", name="Keep it").count() == 1 and "danger" in ask.get_by_role("button", name="Drop it").get_attribute("class")
    ask.get_by_role("button", name="Keep it").click()
    box.get_by_role("alertdialog").wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_timeout(200)
    assert not [n for n, _ in host.log if n in ("ideas.drop", "ideas.stop")]
    ask = ask_drop(box)
    ask.get_by_role("button", name="Drop it").click()
    assert _calls(pg, host, "ideas.drop") == [{"slug": "fresh"}] and not [n for n, _ in host.log if n == "ideas.stop"]
    pg.locator('[data-lkey="t:orc:fresh"]').wait_for(state="detached", timeout=WAIT_MS)


def test_a_goal_with_tasks_running_stops_its_work_first_and_says_so(day):
    pg, host, w = day
    assert any(t["state"] == "running" for n in host.nodes if n["slug"] == "bar" for t in n["tasks"])
    if not wide(w):
        pg.locator('[data-lkey="t:orc:bar"]').click()
        box = pg.locator(".table-back")
        box.wait_for(timeout=WAIT_MS)
    else:
        box = first(pg).locator('.table-goal[data-goal="bar"]')
    ask = ask_drop(box)
    assert ask.locator(".table-drop__text").text_content() == "Its page and its plan go; what it spent stays counted. Its work stops first."
    ask.get_by_role("button", name="Drop it").click()
    _calls(pg, host, "ideas.drop")
    sent = [(n, a) for n, a in host.log if n in ("ideas.stop", "ideas.drop")]
    assert sent == [("ideas.stop", {"slug": "bar"}), ("ideas.drop", {"slug": "bar"})], sent


def test_a_refusal_is_said_in_the_card_the_orkmaster_reading_it_in_its_own_words(day):
    pg, host, w = day
    host.refuse = REFUSED
    if not wide(w):
        pg.locator('[data-lkey="t:orc:fresh"]').click()
        box = pg.locator(".table-back")
        box.wait_for(timeout=WAIT_MS)
    else:
        box = first(pg).locator('.table-goal[data-goal="fresh"]')
    ask = ask_drop(box)
    ask.get_by_role("button", name="Drop it").click()
    ask.get_by_role("alert").wait_for(timeout=WAIT_MS)
    assert ask.get_by_role("alert").inner_text() == SAID, "the host's words are said in the person's"
    assert ask.get_by_role("button", name="Drop it").is_enabled() and box.get_by_role("alertdialog").count() == 1, "the question stays; the goal is still there"
    assert pg.locator('[data-lkey="t:orc:fresh"]').count() == 1
    host.refuse = "Nothing to drop here"
    ask.get_by_role("button", name="Drop it").click()
    pg.get_by_text("Nothing to drop here").wait_for(timeout=WAIT_MS)                                                      # any other refusal is said as it came
    ask.get_by_role("button", name="Keep it").click()
    box.get_by_role("alertdialog").wait_for(state="detached", timeout=WAIT_MS)


def test_esc_closes_the_question_and_gives_the_focus_back_to_the_menu_button(day):
    pg, host, w = day
    if not wide(w):
        pg.locator('[data-lkey="t:orc:fresh"]').click()
        box = pg.locator(".table-back")
    else:
        box = first(pg).locator('.table-goal[data-goal="fresh"]')
    ask_drop(box)
    assert pg.evaluate("() => document.activeElement.textContent.trim()") == "Keep it", "the safe answer has the focus"
    pg.keyboard.press("Escape")
    box.get_by_role("alertdialog").wait_for(state="detached", timeout=WAIT_MS)
    assert "table-menu__btn" in pg.evaluate("() => document.activeElement.className")
    assert not [n for n, _ in host.log if n == "ideas.drop"]


def test_the_line_cards_have_the_menu_too_the_front_one_and_the_edges_behind_it(gui):
    errors: list[str] = []
    pg, host = start(gui, "wide", errors, line=4)
    try:
        front = first(pg).locator(".table-line-item:not(.table-fan__slot)")
        assert front.locator(".table-dropper").count() == 1
        edges = first(pg).locator(".table-line-item.table-fan__slot")
        assert edges.count() == 3 and edges.locator(".table-dropper").count() >= 1, "an edge behind the front one has it (a hint, the farthest, has not)"
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_line_goal_is_dropped_from_its_front_card(gui):
    errors: list[str] = []
    server, browser = gui
    host = DayHost(line=4)
    pg = narrow.page(browser, "wide")
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        front = first(pg).locator(".table-line-item:not(.table-fan__slot)")
        front.wait_for(timeout=WAIT_MS)
        slug = front.locator("[data-slug]").first.get_attribute("data-slug")
        ask = ask_drop(front)
        ask.get_by_role("button", name="Drop it").click()
        assert _calls(pg, host, "ideas.drop") == [{"slug": slug}]
        pg.locator(f'[data-line-item][data-slug="{slug}"]').wait_for(state="detached", timeout=WAIT_MS)
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_route_card_lifted_has_the_menu_and_asks_inside_the_card(gui, width):
    host = DayRoute()
    pg, log = open_route(gui, host, width)
    try:
        lifted = lift(pg)
        ask = ask_drop(lifted)
        assert ask.bounding_box()["x"] >= lifted.bounding_box()["x"] - 1 and ask.bounding_box()["x"] + ask.bounding_box()["width"] <= lifted.bounding_box()["x"] + lifted.bounding_box()["width"] + 1, "asked in the card"
        ask.get_by_role("button", name="Keep it").click()
        assert not [n for n, _ in host.log if n == "ideas.drop"]
        ask = ask_drop(lifted)
        ask.get_by_role("button", name="Drop it").click()
        assert _calls(pg, host, "ideas.drop") == [{"slug": "fresh"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goals_face_over_the_pane_has_the_menu_in_its_head(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator('.hand-card[data-goal="timer"][data-top="1"]').click(position={"x": 10, "y": 24})
        pg.locator(".hand-lifted").get_by_role("button", name="Open…").click()
        box = pane(pg)
        box.locator(".hand-stopface").wait_for(timeout=WAIT_MS)
        head = box.locator(".hand-stopface__head")
        assert head.locator(".table-dropper").count() == 1
        ask = ask_drop(head)
        ask.get_by_role("button", name="Drop it").click()
        assert _calls(pg, host, "ideas.drop") == [{"slug": "timer"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_touch_the_menu_button_and_the_answers_are_44_by_44(gui):
    """A touch screen wide enough for the table (1280 px); the **…** of a card and of a line edge, the item and the two answers are each a 44 px target (spec 94 §1.3)."""
    server, browser = gui
    errors: list[str] = []
    host = DayHost(line=4)
    pg = browser.new_context(viewport={"width": 1280, "height": 800}, has_touch=True).new_page()
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
        for el in pg.locator(".table-dropper .table-menu__btn").all():
            box = el.bounding_box()
            assert box["width"] >= 43.5 and box["height"] >= 43.5, box
        assert pg.locator(".table-dropper .table-menu__btn").count() >= 2
        box = first(pg).locator('.table-goal[data-goal="fresh"]')
        ask = ask_drop(box)
        for el in ask.get_by_role("button").all():
            b = el.bounding_box()
            assert b["height"] >= 43.5, b
        assert box.get_by_role("alertdialog").count() == 1
    finally:
        pg.context.close()
    assert not errors, "\n".join(errors)


# -- G: what works moves --------------------------------------------------------------------------------------------------------------------------

WORKING = '.table-card[data-state="running"], .table-card[data-state="testing"]'
DRAWING = ".table-card__win > *"


def anim(el, pseudo=""):
    return el.evaluate("(e, p) => { const s = getComputedStyle(e, p || null); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }", pseudo)


def test_a_task_card_at_work_steps_its_drawing_marches_a_dotted_line_and_says_the_time_it_has_worked(day):
    pg, host, w = day
    if not wide(w):
        pytest.skip("a lane a token wide has no stage word: its token steps its drawing, tested below")
    card = pg.locator('.table-card[data-task="r1"]')
    assert card.get_attribute("data-state") == "running"
    name, duration, timing = anim(card.locator(DRAWING).first)
    assert name == "table-step" and duration == "1.2s" and timing.startswith("steps(2"), (name, duration, timing)
    name, duration, timing = anim(card, "::after")
    assert name == "table-march" and timing.startswith("steps("), (name, duration, timing)
    assert card.evaluate("e => getComputedStyle(e, '::after').backgroundImage").startswith("repeating-linear-gradient")
    words = card.locator(".table-stage").inner_text().strip()
    assert words.lower().startswith("doing · 1 m "), words
    ticked = card.locator(".table-stage").inner_text()
    pg.wait_for_function("([sel, was]) => document.querySelector(sel + ' .table-stage').innerText !== was", arg=['.table-card[data-task="r1"]', ticked], timeout=3000)   # it ticks
    waiting = pg.locator('.table-card[data-state="failed"]').first
    assert anim(waiting.locator(DRAWING).first)[0] == "none" and anim(waiting, "::after")[0] == "none", "what does not work does not move"
    assert "·" not in waiting.locator(".table-stage").inner_text(), "and counts no time"


def test_a_token_at_work_steps_its_drawing_at_the_narrow_width(day):
    pg, host, w = day
    if wide(w):
        pytest.skip("the narrow width's")
    token = pg.locator('.table-token[data-state="running"]').first
    token.wait_for(timeout=WAIT_MS)
    assert anim(token.locator(DRAWING).first)[0] == "table-step"


def test_a_card_whose_state_changed_flashes_its_frame_twice_once_and_then_is_still(day):
    pg, host, w = day
    if not wide(w):
        pytest.skip("the flash is the card's")
    card = pg.locator('.table-card[data-task="r1"]')
    assert card.count() == 1 and "is-changed" not in card.get_attribute("class"), "none on the first read"
    for n in host.nodes:
        for t in n["tasks"]:
            if t["id"] == "r1":
                t["state"] = "testing"
    host.push()
    card = pg.locator('.table-card[data-task="r1"][data-state="testing"]')
    card.wait_for(timeout=WAIT_MS)
    got = pg.evaluate_handle("""() => new Promise((resolve) => {              // read in the one frame the class appears in: it lasts 0.65 s, and a busy machine is slow
        const el = document.querySelector('.table-card[data-task="r1"]');
        const read = () => { if (!el.classList.contains('is-changed')) return requestAnimationFrame(read);
          const s = getComputedStyle(el); resolve([s.animationName, s.animationDuration, s.animationTimingFunction, s.animationIterationCount]); };
        read();
    })""").json_value()
    name, duration, timing, count = got
    assert name == "table-flash" and duration == "0.3s" and timing.startswith("steps(2") and count == "2", got           # twice: 2 x 0.3 s
    pg.wait_for_function("() => !document.querySelector('.table-card[data-task=\"r1\"]').classList.contains('is-changed')", timeout=3000)
    assert anim(card)[0] == "none"
    host.push()                                                                                                         # a redraw with the same state flashes nothing
    pg.wait_for_timeout(300)
    assert "is-changed" not in card.get_attribute("class")


def test_under_reduced_motion_nothing_moves_and_the_time_still_ticks(day):
    pg, host, w = day
    if not wide(w):
        pytest.skip("the card's")
    pg.emulate_media(reduced_motion="reduce")
    card = pg.locator('.table-card[data-task="r1"]')
    assert anim(card.locator(DRAWING).first)[0] == "none" and anim(card, "::after")[0] == "none"
    was = card.locator(".table-stage").inner_text()
    assert "·" in was
    for n in host.nodes:
        for t in n["tasks"]:
            if t["id"] == "r1":
                t["state"] = "testing"
    host.push()
    pg.locator('.table-card[data-task="r1"][data-state="testing"]').wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert anim(pg.locator('.table-card[data-task="r1"]'))[0] == "none", "no flash either"
    pg.wait_for_function("([sel, was]) => document.querySelector(sel + ' .table-stage').innerText !== was", arg=['.table-card[data-task="r1"]', pg.locator('.table-card[data-task="r1"] .table-stage').inner_text()], timeout=3000)
    pg.emulate_media(reduced_motion="no-preference")
